#!/usr/bin/env python3
"""PPT Master - Concurrent Source Import Tests

Overlapping import-sources runs on one project must serialize cleanly:
same-named Markdown files land under distinct names with intact asset
links, every companion image and manifest entry is preserved, invalid
calls fail before waiting for a lock, and Windows lock errors distinguish
contention from permanent failures.

Usage:
    cd skills/ppt-master/scripts && python3 -m unittest tests.test_concurrent_source_import

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import contextlib
import errno
import io
import json
import re
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from project_management import cli as project_cli  # noqa: E402

CLI = SCRIPTS_DIR / "project_manager.py"
_IMAGE_LINK_RE = re.compile(r"!\[\]\(([^)]+)\)")


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _make_png_1x1(rgb: tuple[int, int, int]) -> bytes:
    """Build a valid 1x1 RGB PNG using only the standard library."""
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    raw_scanline = bytes([0, *rgb])
    idat = zlib.compress(raw_scanline)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def _make_markdown_source(root: Path, tag: str, png_bytes: bytes) -> Path:
    """Build <tag>/report.md with a report_files/ image and manifest."""
    assets = root / tag / "report_files"
    assets.mkdir(parents=True)
    (assets / f"chart_{tag}.png").write_bytes(png_bytes)
    (assets / "image_manifest.json").write_text(
        json.dumps([{"filename": f"chart_{tag}.png"}]), encoding="utf-8"
    )
    markdown = root / tag / "report.md"
    markdown.write_text(
        f"# Report {tag}\n\n![](report_files/chart_{tag}.png)\n", encoding="utf-8"
    )
    return markdown


def _import_command(project: Path, source: Path) -> list[str]:
    return [sys.executable, str(CLI), "import-sources", str(project), str(source), "--copy"]


class ConcurrentSourceImportTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.project = self.root / "demo"
        (self.project / "sources").mkdir(parents=True)

    def _spawn(self, command: list[str]) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.addCleanup(self._reap_process, process)
        return process

    @staticmethod
    def _reap_process(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()

    def test_overlapping_imports_serialize_through_public_api(self) -> None:
        png_a = _make_png_1x1((220, 40, 40))
        png_b = _make_png_1x1((40, 120, 220))
        source_a = _make_markdown_source(self.root / "in", "A", png_a)
        source_b = _make_markdown_source(self.root / "in", "B", png_b)

        first_entered = threading.Event()
        release_first = threading.Event()
        second_entered = threading.Event()
        errors: list[BaseException] = []

        original_unlocked = project_cli.ProjectManager._import_sources_unlocked

        def gated_unlocked(manager, project_dir, source_items, **kwargs):
            if str(source_a) in source_items:
                first_entered.set()
                if not release_first.wait(timeout=15):
                    raise TimeoutError("timed out waiting to release first import")
            else:
                second_entered.set()
            return original_unlocked(manager, project_dir, source_items, **kwargs)

        def run_import(source: Path) -> None:
            try:
                project_cli.ProjectManager().import_sources(
                    str(self.project), [str(source)], copy=True
                )
            except BaseException as exc:
                errors.append(exc)

        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()), \
                patch.object(
                    project_cli.ProjectManager,
                    "_import_sources_unlocked",
                    gated_unlocked,
                ):
            thread_a = threading.Thread(target=run_import, args=(source_a,))
            thread_b = threading.Thread(target=run_import, args=(source_b,))
            thread_a.start()
            try:
                self.assertTrue(first_entered.wait(timeout=10), "first import did not acquire lock")
                thread_b.start()
                self.assertFalse(
                    second_entered.wait(timeout=0.3),
                    "second import entered critical section while first held the lock",
                )
                self.assertFalse((self.project / "sources" / "report.md").exists())
            finally:
                release_first.set()
                thread_a.join(timeout=15)
                if thread_b.is_alive() or second_entered.is_set():
                    thread_b.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertTrue(second_entered.is_set())
        md_files = sorted((self.project / "sources").glob("*.md"))
        self.assertEqual(len(md_files), 2)
        manifest = json.loads(
            (self.project / "images" / "image_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(item["filename"] for item in manifest),
            ["chart_A.png", "chart_B.png"],
        )

    def test_parallel_cli_imports_keep_every_source_and_manifest_entry(self) -> None:
        tags = [chr(ord("A") + index) for index in range(6)]
        png_by_tag = {
            tag: _make_png_1x1((30 * index + 10, 80, 220 - 20 * index))
            for index, tag in enumerate(tags)
        }
        sources = [
            _make_markdown_source(self.root / "in", tag, png_by_tag[tag])
            for tag in tags
        ]
        processes = [
            self._spawn(_import_command(self.project, source))
            for source in sources
        ]
        for process in processes:
            _, stderr = process.communicate(timeout=120)
            self.assertEqual(process.returncode, 0, stderr.decode("utf-8", "replace"))

        md_files = sorted((self.project / "sources").glob("*.md"))
        self.assertEqual(len(md_files), len(tags))

        matched_tags: set[str] = set()
        for md_path in md_files:
            text = md_path.read_text(encoding="utf-8")
            hits = [tag for tag in tags if f"# Report {tag}" in text]
            self.assertEqual(len(hits), 1, md_path.name)
            tag = hits[0]
            matched_tags.add(tag)
            link_match = _IMAGE_LINK_RE.search(text)
            self.assertIsNotNone(link_match, md_path.name)
            linked_image = self.project / "sources" / link_match.group(1)
            self.assertTrue(linked_image.is_file(), linked_image)
            self.assertEqual(linked_image.read_bytes(), png_by_tag[tag])
        self.assertEqual(matched_tags, set(tags))

        manifest = json.loads(
            (self.project / "images" / "image_manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(item["filename"] for item in manifest),
            sorted(f"chart_{tag}.png" for tag in tags),
        )
        for tag in tags:
            image_path = self.project / "images" / f"chart_{tag}.png"
            self.assertTrue(image_path.is_file(), image_path)
            self.assertEqual(image_path.read_bytes(), png_by_tag[tag])

    def test_validation_order_and_invalid_calls_skip_lock(self) -> None:
        manager = project_cli.ProjectManager()
        missing_project = self.root / "does_not_exist"

        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            manager.import_sources(
                str(missing_project), ["report.md"], move=True, copy=True
            )

        source = _make_markdown_source(self.root / "in", "A", _make_png_1x1((10, 20, 30)))
        entered = threading.Event()
        release = threading.Event()
        errors: list[BaseException] = []
        original_unlocked = project_cli.ProjectManager._import_sources_unlocked

        def hold_lock(mgr, project_dir, source_items, **kwargs):
            entered.set()
            release.wait(timeout=15)
            return original_unlocked(mgr, project_dir, source_items, **kwargs)

        def run_valid() -> None:
            try:
                manager.import_sources(str(self.project), [str(source)], copy=True)
            except BaseException as exc:
                errors.append(exc)

        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()), \
                patch.object(project_cli.ProjectManager, "_import_sources_unlocked", hold_lock):
            worker = threading.Thread(target=run_valid)
            worker.start()
            try:
                self.assertTrue(entered.wait(timeout=10))
                with self.assertRaisesRegex(ValueError, "At least one source"):
                    manager.import_sources(str(self.project), [], copy=True)
                with self.assertRaisesRegex(ValueError, "mutually exclusive"):
                    manager.import_sources(
                        str(self.project), [str(source)], move=True, copy=True
                    )
            finally:
                release.set()
                worker.join(timeout=15)

        self.assertEqual(errors, [])

    def test_windows_lock_retries_contention_raises_permanent_errors_and_skips_lock_file(
        self,
    ) -> None:
        source_dir = self.root / "win_in"
        source_dir.mkdir()
        (source_dir / "note.md").write_text("# Note\n", encoding="utf-8")
        (source_dir / ".import-sources.lock").write_bytes(b"")

        calls: list[int] = []
        attempts = {"count": 0}

        def fake_locking(_fd: int, mode: int, _nbytes: int) -> None:
            calls.append(mode)
            if mode == 2:  # LK_NBLCK
                attempts["count"] += 1
                if attempts["count"] == 1:
                    raise PermissionError(errno.EACCES, "locked")

        fake_msvcrt = SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, locking=fake_locking)

        with patch.object(project_cli, "_IS_WINDOWS", True), \
                patch.dict(sys.modules, {"msvcrt": fake_msvcrt}), \
                patch.object(project_cli.time, "sleep") as sleep_mock, \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            summary = project_cli.ProjectManager().import_sources(
                str(self.project), [str(source_dir)], copy=True
            )

        self.assertEqual(calls, [2, 2, 0])
        sleep_mock.assert_called_once()
        self.assertEqual([Path(p).name for p in summary["markdown"]], ["note.md"])
        self.assertFalse((self.project / "sources" / ".import-sources.lock").exists())

        def permanent_failure(_fd: int, _mode: int, _nbytes: int) -> None:
            raise OSError(errno.EINVAL, "locking unsupported")

        failing_msvcrt = SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, locking=permanent_failure)
        with patch.object(project_cli, "_IS_WINDOWS", True), \
                patch.dict(sys.modules, {"msvcrt": failing_msvcrt}), \
                patch.object(project_cli.time, "sleep") as sleep_mock:
            with self.assertRaises(OSError) as ctx:
                project_cli.ProjectManager().import_sources(
                    str(self.project), [str(source_dir / "note.md")], copy=True
                )
        self.assertEqual(ctx.exception.errno, errno.EINVAL)
        sleep_mock.assert_not_called()
