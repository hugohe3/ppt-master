#!/usr/bin/env python3
"""
PPT Master - Export QA Gate

Runs final delivery checks for a project: SVG XML parse, svg_quality_checker,
optional beautify text fidelity, and optional PPTX open/page-count verification.
Writes a compact Markdown report under exports/.

Usage:
    python3 scripts/export_qa.py <project_path>
    python3 scripts/export_qa.py <project_path> --beautify
    python3 scripts/export_qa.py <project_path> --pptx exports/out.pptx --beautify

Examples:
    python3 scripts/export_qa.py projects/recruitment --beautify
    python3 scripts/export_qa.py projects/recruitment --pptx latest --beautify

Dependencies:
    python-pptx (only when --pptx is supplied)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()


def _scripts_dir() -> Path:
    return Path(__file__).resolve().parent


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout


def _xml_check(project_path: Path) -> tuple[bool, list[str]]:
    svg_dir = project_path / "svg_output"
    failures = []
    for svg_file in sorted(svg_dir.glob("*.svg")):
        try:
            ET.parse(svg_file)
        except ET.ParseError as exc:
            failures.append(f"{svg_file.name}: {exc}")
    return not failures, failures


def _latest_pptx(project_path: Path) -> Path | None:
    exports = project_path / "exports"
    files = sorted(exports.glob("*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _resolve_pptx(project_path: Path, value: str | None) -> Path | None:
    if not value:
        return None
    if value == "latest":
        return _latest_pptx(project_path)
    path = Path(value)
    if not path.is_absolute():
        path = project_path / path
    return path


def _pptx_check(path: Path | None, expected_pages: int | None) -> tuple[bool, str]:
    if path is None:
        return True, "Skipped"
    if not path.exists():
        return False, f"Missing PPTX: {path}"
    try:
        from pptx import Presentation
    except ImportError as exc:
        return False, f"python-pptx unavailable: {exc}"
    try:
        prs = Presentation(str(path))
    except Exception as exc:  # noqa: BLE001 - user-facing file validation
        return False, f"Cannot open PPTX: {exc}"
    count = len(prs.slides)
    if expected_pages is not None and count != expected_pages:
        return False, f"Slide count {count}, expected {expected_pages}"
    return True, f"Opened OK, slides={count}"


def _expected_page_count(project_path: Path) -> int | None:
    source_clean = project_path / "analysis" / "source_text_clean.json"
    if source_clean.exists():
        try:
            data = json.loads(source_clean.read_text(encoding="utf-8-sig"))
            return len(data.get("slides", []))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _write_report(project_path: Path, rows: list[tuple[str, bool, str]]) -> Path:
    exports = project_path / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    path = exports / "qa_report.md"
    lines = [
        "# Export QA Report",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for name, ok, detail in rows:
        status = "PASS" if ok else "FAIL"
        safe_detail = detail.replace("|", "\\|").replace("\n", "<br>")
        lines.append(f"| {name} | {status} | {safe_detail} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run final export QA checks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT Master project directory")
    parser.add_argument("--beautify", action="store_true", help="Run beautify text fidelity gate")
    parser.add_argument("--pptx", default=None, help="PPTX path to verify, or 'latest'")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"[ERROR] Project not found: {project_path}", file=sys.stderr)
        return 2

    rows: list[tuple[str, bool, str]] = []
    xml_ok, xml_failures = _xml_check(project_path)
    rows.append(("SVG XML parse", xml_ok, "OK" if xml_ok else "\n".join(xml_failures[:20])))

    code, output = _run(
        [sys.executable, str(_scripts_dir() / "svg_quality_checker.py"), str(project_path)],
        cwd=_scripts_dir().parents[2],
    )
    rows.append(("SVG quality checker", code == 0, "Exit 0" if code == 0 else output[-2000:]))

    code, output = _run(
        [sys.executable, str(_scripts_dir() / "svg_layout_safety.py"), str(project_path), "--write-report"],
        cwd=_scripts_dir().parents[2],
    )
    rows.append(("SVG layout safety", code == 0, "Exit 0" if code == 0 else output[-2000:]))

    if args.beautify:
        cmd = [
            sys.executable,
            str(_scripts_dir() / "verify_beautify_fidelity.py"),
            str(project_path),
            "--write-report",
        ]
        pptx_path = _resolve_pptx(project_path, args.pptx)
        if pptx_path is not None:
            cmd.extend(["--target-pptx", str(pptx_path)])
        code, output = _run(cmd, cwd=_scripts_dir().parents[2])
        rows.append(("Beautify text fidelity", code == 0, "Exit 0" if code == 0 else output[-2000:]))

    pptx_path = _resolve_pptx(project_path, args.pptx)
    pptx_ok, pptx_detail = _pptx_check(pptx_path, _expected_page_count(project_path))
    rows.append(("PPTX open/page count", pptx_ok, pptx_detail))

    report_path = _write_report(project_path, rows)
    for name, ok, detail in rows:
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail.splitlines()[0] if detail else ''}")
    print(f"Report: {report_path}")
    return 0 if all(ok for _, ok, _ in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
