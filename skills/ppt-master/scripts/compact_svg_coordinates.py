#!/usr/bin/env python3
"""
PPT Master - SVG Coordinate Compactor

Compact model-facing page-space SVG coordinates to at most two decimal places
without rounding normalized crop ratios or transform linear coefficients.

Usage:
    python3 scripts/compact_svg_coordinates.py <svg-file-or-directory> [--inplace]

Examples:
    python3 scripts/compact_svg_coordinates.py projects/example/templates --inplace
    python3 scripts/compact_svg_coordinates.py imported/authoring-svg

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

COORDINATE_DECIMAL_PLACES = 2
_NUMBER_TOKEN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_NUMBER_RE = re.compile(rf"^{_NUMBER_TOKEN}$")
_TRANSFORM_FUNCTION_RE = re.compile(r"([A-Za-z]+)\s*\(([^)]*)\)")
_COMPACTABLE_ATTRIBUTE_RE = re.compile(
    r"(?<![A-Za-z0-9_.:-])"
    r"(?P<name>data-pptx-frame|data-pptx-placeholder-bounds|transform)"
    r"(?P<spacing>\s*=\s*)"
    r"(?P<quote>[\"'])"
    r"(?P<value>.*?)"
    r"(?P=quote)",
    re.DOTALL,
)


@dataclass
class CoordinateCompactionStats:
    """Count safely compacted coordinate-bearing SVG attributes."""

    native_frames: int = 0
    placeholder_bounds: int = 0
    transforms: int = 0

    @property
    def changed_attributes(self) -> int:
        return self.native_frames + self.placeholder_bounds + self.transforms

    def merge(self, other: "CoordinateCompactionStats") -> None:
        self.native_frames += other.native_frames
        self.placeholder_bounds += other.placeholder_bounds
        self.transforms += other.transforms

    def as_dict(self) -> dict[str, int]:
        return {
            "native_frames": self.native_frames,
            "placeholder_bounds": self.placeholder_bounds,
            "transforms": self.transforms,
            "changed_attributes": self.changed_attributes,
        }


def _number_tokens(value: str) -> list[str] | None:
    stripped = value.strip()
    if not stripped:
        return None
    tokens = re.split(r"[\s,]+", stripped)
    if not tokens or any(_NUMBER_RE.fullmatch(token) is None for token in tokens):
        return None
    return tokens


def format_coordinate(value: str | float) -> str:
    """Format one finite page-space coordinate with at most two decimals."""
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"Coordinate is not finite: {value!r}")
    compact = (
        f"{numeric:.{COORDINATE_DECIMAL_PLACES}f}".rstrip("0").rstrip(".")
    )
    return "0" if compact in {"", "-0"} else compact


def _compact_coordinate_quad(value: str) -> str:
    tokens = _number_tokens(value)
    if tokens is None or len(tokens) != 4:
        return value
    return " ".join(format_coordinate(token) for token in tokens)


def _compact_transform(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name, arguments = match.groups()
        tokens = _number_tokens(arguments)
        if tokens is None:
            return match.group(0)

        lowered = name.lower()
        compacted: list[str]
        if lowered == "translate" and len(tokens) in {1, 2}:
            compacted = [format_coordinate(token) for token in tokens]
        elif lowered == "rotate" and len(tokens) == 3:
            compacted = [
                tokens[0],
                format_coordinate(tokens[1]),
                format_coordinate(tokens[2]),
            ]
        elif lowered == "matrix" and len(tokens) == 6:
            compacted = [
                *tokens[:4],
                format_coordinate(tokens[4]),
                format_coordinate(tokens[5]),
            ]
        else:
            return match.group(0)
        return f"{name}({' '.join(compacted)})"

    return _TRANSFORM_FUNCTION_RE.sub(replace, value)


def _compact_attribute_value(
    name: str,
    value: str,
    *,
    compact_native_frames: bool,
) -> str:
    if name == "data-pptx-frame":
        return _compact_coordinate_quad(value) if compact_native_frames else value
    if name == "data-pptx-placeholder-bounds":
        return _compact_coordinate_quad(value)
    if name == "transform":
        return _compact_transform(value)
    return value


def _record_change(stats: CoordinateCompactionStats, name: str) -> None:
    if name == "data-pptx-frame":
        stats.native_frames += 1
    elif name == "data-pptx-placeholder-bounds":
        stats.placeholder_bounds += 1
    elif name == "transform":
        stats.transforms += 1


def compact_svg_tree(
    root: ET.Element,
    *,
    compact_native_frames: bool = True,
) -> CoordinateCompactionStats:
    """Compact safe coordinate metadata in one parsed SVG tree."""
    stats = CoordinateCompactionStats()
    for element in root.iter():
        for name in (
            "data-pptx-frame",
            "data-pptx-placeholder-bounds",
            "transform",
        ):
            current = element.get(name)
            if current is None:
                continue
            compacted = _compact_attribute_value(
                name,
                current,
                compact_native_frames=compact_native_frames,
            )
            if compacted == current:
                continue
            element.set(name, compacted)
            _record_change(stats, name)
    return stats


def compact_svg_text(
    text: str,
    *,
    compact_native_frames: bool = True,
) -> tuple[str, CoordinateCompactionStats]:
    """Compact safe coordinates while preserving unrelated SVG formatting."""
    stats = CoordinateCompactionStats()

    def replace(match: re.Match[str]) -> str:
        name = match.group("name")
        current = match.group("value")
        compacted = _compact_attribute_value(
            name,
            current,
            compact_native_frames=compact_native_frames,
        )
        if compacted == current:
            return match.group(0)
        _record_change(stats, name)
        return (
            f"{name}{match.group('spacing')}{match.group('quote')}"
            f"{compacted}{match.group('quote')}"
        )

    return _COMPACTABLE_ATTRIBUTE_RE.sub(replace, text), stats


def _svg_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".svg" else []
    return sorted(path for path in input_path.rglob("*.svg") if path.is_file())


def _write_atomic(path: Path, payload: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(payload)
    try:
        temporary_path.chmod(mode)
        temporary_path.replace(path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compact safe page-space SVG coordinates to at most two decimal "
            "places. Runs as a dry-run unless --inplace is supplied."
        ),
    )
    parser.add_argument("input", type=Path, help="SVG file or directory")
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Atomically replace changed SVG files",
    )
    parser.add_argument(
        "--keep-native-frames",
        action="store_true",
        help=(
            "Leave data-pptx-frame unchanged while compacting slot bounds and "
            "transform translations"
        ),
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.resolve()
    if not input_path.exists():
        print(
            json.dumps(
                {"error": f"Input does not exist: {input_path}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    paths = _svg_files(input_path)
    if not paths:
        print(
            json.dumps(
                {"error": f"No SVG files found under {input_path}"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    staged: list[tuple[Path, str]] = []
    totals = CoordinateCompactionStats()
    bytes_before = 0
    bytes_after = 0
    try:
        for path in paths:
            original = path.read_text(encoding="utf-8")
            ET.fromstring(original)
            compacted, stats = compact_svg_text(
                original,
                compact_native_frames=not args.keep_native_frames,
            )
            totals.merge(stats)
            before = len(original.encode("utf-8"))
            after = len(compacted.encode("utf-8"))
            bytes_before += before
            bytes_after += after
            if compacted != original:
                staged.append((path, compacted))
    except (OSError, UnicodeDecodeError, ET.ParseError, ValueError) as exc:
        print(
            json.dumps({"error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1

    if args.inplace:
        try:
            for path, payload in staged:
                _write_atomic(path, payload)
        except OSError as exc:
            print(
                json.dumps({"error": str(exc)}, ensure_ascii=False),
                file=sys.stderr,
            )
            return 1

    print(json.dumps({
        "input": str(input_path),
        "inplace": args.inplace,
        "files_scanned": len(paths),
        "files_changed": len(staged),
        "bytes_before": bytes_before,
        "bytes_after": bytes_after,
        "bytes_saved": bytes_before - bytes_after,
        "coordinates": totals.as_dict(),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
