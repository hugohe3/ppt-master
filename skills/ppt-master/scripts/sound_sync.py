#!/usr/bin/env python3
"""
PPT Master - Sound Sync

List the bundled CC0 sound catalog or copy explicitly selected sounds into a
project-local `sounds/` directory. The global library is never copied in bulk.

Usage:
    python3 scripts/sound_sync.py list [--query TERM]
    python3 scripts/sound_sync.py <project_path> <sound_id> [<sound_id> ...]

Examples:
    python3 scripts/sound_sync.py list --query whoosh
    python3 scripts/sound_sync.py projects/deck bigsoundbank/1797 kenney-interface/click_001

Dependencies:
    None (standard library only).

See templates/sounds/README.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

_GLOBAL_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "templates" / "sounds"
_INDEX_NAME = "sounds_index.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load_sounds(global_dir: Path) -> list[dict[str, object]]:
    index_path = global_dir / _INDEX_NAME
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"sound index not found: {index_path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read sound index {index_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"sound index root is not an object: {index_path}")
    if payload.get("version") != 1:
        raise RuntimeError(f"unsupported sound index version in {index_path}")

    sounds = payload.get("sounds")
    if not isinstance(sounds, list):
        raise RuntimeError(f"sound index has no sounds list: {index_path}")
    if payload.get("asset_count") != len(sounds):
        raise RuntimeError(f"sound index count does not match its sounds list: {index_path}")

    seen_ids: set[str] = set()
    for item in sounds:
        if not isinstance(item, dict):
            raise RuntimeError(f"sound index entry is not an object: {index_path}")
        sound_id = item.get("id")
        relative_file = item.get("file")
        sha256 = item.get("sha256")
        if not all(isinstance(value, str) and value for value in (sound_id, relative_file, sha256)):
            raise RuntimeError(f"sound index entry lacks id/file/sha256: {index_path}")
        if sound_id in seen_ids:
            raise RuntimeError(f"duplicate sound id in index: {sound_id}")
        seen_ids.add(sound_id)

        relative_path = Path(relative_file)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError(f"unsafe sound path in index: {relative_file}")
        if relative_path.suffix.lower() != ".wav":
            raise RuntimeError(f"sound index entry is not WAV: {relative_file}")
        if relative_path.with_suffix("").as_posix() != sound_id:
            raise RuntimeError(f"sound id/file mismatch in index: {sound_id} != {relative_file}")

    return sounds


def list_sounds(query: str = "", global_dir: Path = _GLOBAL_SOUNDS_DIR) -> list[dict[str, object]]:
    """Return sounds whose metadata contains every case-insensitive query term."""
    sounds = _load_sounds(global_dir)
    terms = [term for term in query.casefold().split() if term]
    if not terms:
        return sounds

    matches: list[dict[str, object]] = []
    for item in sounds:
        searchable = [
            str(item.get("id", "")),
            str(item.get("label", "")),
            str(item.get("source", "")),
            *(str(tag) for tag in item.get("tags", [])),
            *(str(context) for context in item.get("contexts", [])),
        ]
        if item.get("recommended") is True:
            searchable.append("recommended")
        haystack = " ".join(searchable).casefold()
        if all(term in haystack for term in terms):
            matches.append(item)
    return matches


def sync_sounds(
    project_path: Path,
    sound_ids: list[str],
    global_dir: Path = _GLOBAL_SOUNDS_DIR,
) -> tuple[list[str], list[str]]:
    """Copy selected sound IDs into `<project>/sounds/` after validating the full batch.

    Returns `(copied_or_present, missing)`. Any missing ID is reported before
    creating the project-local directory or copying a file.
    """
    try:
        project_root = project_path.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError(f"cannot resolve project directory {project_path}: {exc}") from exc
    if not project_root.is_dir():
        raise RuntimeError(f"project is not a directory: {project_path}")

    sounds = _load_sounds(global_dir)
    catalog = {str(item["id"]): item for item in sounds}
    requested = list(dict.fromkeys(sound_ids))
    missing = [sound_id for sound_id in requested if sound_id not in catalog]
    if missing:
        return [], missing

    validated: list[tuple[str, Path, Path, bool]] = []
    for sound_id in requested:
        item = catalog[sound_id]
        relative_path = Path(str(item["file"]))
        source = global_dir / relative_path
        expected_sha256 = str(item["sha256"])
        if not source.is_file():
            raise RuntimeError(f"library file not found for {sound_id}: {source}")
        actual_sha256 = _sha256(source)
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"library checksum mismatch for {sound_id}: "
                f"expected {expected_sha256}, got {actual_sha256}"
            )
        destination = project_root / "sounds" / relative_path
        resolved_parent = destination.parent.resolve(strict=False)
        resolved_destination = destination.resolve(strict=False)
        if not _is_within(resolved_parent, project_root):
            raise RuntimeError(
                f"destination parent escapes project root for {sound_id}: {resolved_parent}"
            )
        if not _is_within(resolved_destination, project_root):
            raise RuntimeError(
                f"destination escapes project root for {sound_id}: {resolved_destination}"
            )
        if destination.is_symlink():
            raise RuntimeError(f"destination symlink is not allowed for {sound_id}: {destination}")

        already_present = False
        if destination.exists():
            if not destination.is_file():
                raise RuntimeError(f"destination is not a regular file for {sound_id}: {destination}")
            destination_sha256 = _sha256(destination)
            if destination_sha256 != expected_sha256:
                raise RuntimeError(
                    f"project sound conflicts with library id {sound_id}: {destination}; "
                    "remove or rename the existing file, then rerun"
                )
            already_present = True
        validated.append((sound_id, source, destination, already_present))

    copied: list[str] = []
    for sound_id, source, destination, already_present in validated:
        if already_present:
            copied.append(f"{sound_id} (already in project)")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(sound_id)

    return copied, []


def _build_list_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sound_sync.py list",
        description="List bundled sounds, optionally filtered by metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--query",
        default="",
        help="Case-insensitive terms matched against ID, label, source, tags, and contexts",
    )
    return parser


def _build_sync_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy explicitly selected library sounds into a project's sounds/ folder. "
            "Use `sound_sync.py list [--query TERM]` for discovery."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Existing project directory")
    parser.add_argument("sound_ids", nargs="+", help="Sound IDs such as bigsoundbank/1797")
    return parser


def _run_list(argv: list[str]) -> int:
    args = _build_list_parser().parse_args(argv)
    try:
        sounds = list_sounds(args.query)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    for item in sounds:
        marker = "*" if item.get("recommended") is True else " "
        sound_id = str(item["id"])
        duration = float(item.get("duration_seconds", 0.0))
        label = str(item.get("label", ""))
        contexts = ",".join(str(value) for value in item.get("contexts", []))
        print(f"{marker} {sound_id:<42} {duration:>7.3f}s  {label}  [{contexts}]")

    print(f"[OK] {len(sounds)} sound(s) matched", file=sys.stderr)
    return 0


def _run_sync(argv: list[str]) -> int:
    args = _build_sync_parser().parse_args(argv)
    project = Path(args.project_path)
    if not project.is_dir():
        print(f"[ERROR] project not found: {project}", file=sys.stderr)
        return 1

    try:
        copied, missing = sync_sounds(project, args.sound_ids)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if missing:
        print(
            f"[MISSING] {len(missing)} sound ID(s) not in the library; nothing was copied:",
            file=sys.stderr,
        )
        for sound_id in missing:
            print(f"     x {sound_id}", file=sys.stderr)
        print(
            "Run `python3 skills/ppt-master/scripts/sound_sync.py list --query <term>` "
            "and select a listed ID.",
            file=sys.stderr,
        )
        return 1

    print(f"[OK] {len(copied)} sound(s) in {project / 'sounds'}:", file=sys.stderr)
    for sound_id in copied:
        print(f"     + {sound_id}", file=sys.stderr)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] == "list":
        return _run_list(raw_args[1:])
    return _run_sync(raw_args)


if __name__ == "__main__":
    raise SystemExit(main())
