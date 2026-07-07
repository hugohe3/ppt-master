#!/usr/bin/env python3
"""
PPT Master - SVG Layout Safety Check

Scans generated SVG pages for obvious text/image overlaps. This is a lightweight
geometry heuristic for catching common beautify failures before export; it does
not replace visual review.

Usage:
    python3 scripts/svg_layout_safety.py <project_path>
    python3 scripts/svg_layout_safety.py <project_path> --write-report

Examples:
    python3 scripts/svg_layout_safety.py projects/recruitment --write-report

Dependencies:
    None
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

_NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?")


def _float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    match = _NUM_RE.match(str(value).strip())
    return float(match.group(0)) if match else default


def _text_content(node: ET.Element) -> str:
    pieces = []
    if node.text:
        pieces.append(node.text)
    for child in list(node):
        if child.text:
            pieces.append(child.text)
        if child.tail:
            pieces.append(child.tail)
    return "".join(pieces).strip()


def _text_box(node: ET.Element) -> tuple[float, float, float, float] | None:
    text = _text_content(node)
    if not text:
        return None
    x = _float(node.get("x"))
    y = _float(node.get("y"))
    size = _float(node.get("font-size"), 18)
    width = max(1, len(text) * size * 0.58)
    height = size * 1.25
    return x, y - size, width, height


def _image_box(node: ET.Element) -> tuple[float, float, float, float]:
    return (
        _float(node.get("x")),
        _float(node.get("y")),
        _float(node.get("width")),
        _float(node.get("height")),
    )


def _area(box: tuple[float, float, float, float]) -> float:
    return max(0, box[2]) * max(0, box[3])


def _intersection(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    w = max(0, min(ax2, bx2) - max(ax1, bx1))
    h = max(0, min(ay2, by2) - max(ay1, by1))
    return w * h


def _scan_svg(svg_file: Path) -> list[dict[str, Any]]:
    root = ET.parse(svg_file).getroot()
    images = []
    texts = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "image":
            images.append(_image_box(node))
        elif tag == "text":
            box = _text_box(node)
            if box is not None:
                texts.append((box, _text_content(node)))

    issues = []
    for text_box, content in texts:
        text_area = _area(text_box)
        if text_area <= 0:
            continue
        for image_box in images:
            overlap = _intersection(text_box, image_box)
            if overlap / text_area >= 0.25:
                issues.append(
                    {
                        "text": content[:80],
                        "text_box": [round(v, 2) for v in text_box],
                        "image_box": [round(v, 2) for v in image_box],
                        "overlap_ratio": round(overlap / text_area, 3),
                    }
                )
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan SVG pages for obvious text/image overlaps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="PPT Master project directory")
    parser.add_argument("--write-report", action="store_true", help="Write analysis/layout_safety_report.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_path = Path(args.project_path)
    svg_dir = project_path / "svg_output"
    if not svg_dir.is_dir():
        print(f"[ERROR] svg_output not found: {svg_dir}", file=sys.stderr)
        return 2

    report = {"ok": True, "pages": []}
    for svg_file in sorted(svg_dir.glob("*.svg")):
        try:
            issues = _scan_svg(svg_file)
        except ET.ParseError as exc:
            issues = [{"parse_error": str(exc)}]
        if issues:
            report["ok"] = False
        report["pages"].append({"file": svg_file.name, "issues": issues})

    for page in report["pages"]:
        if page["issues"]:
            print(f"[WARN] {page['file']}: {len(page['issues'])} possible text/image overlap(s)")
    if report["ok"]:
        print("[OK] No obvious text/image overlaps")

    if args.write_report:
        analysis = project_path / "analysis"
        analysis.mkdir(parents=True, exist_ok=True)
        path = analysis / "layout_safety_report.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report: {path}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
