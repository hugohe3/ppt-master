#!/usr/bin/env python3
"""
PPT Master - SVG Inherited Style Compactor

Normalize generated SVG authoring files to root/group defaults plus local
overrides. The compactor promotes one common page font to the SVG root and
removes presentation declarations that repeat an inherited value.

Usage:
    python3 scripts/compact_svg_styles.py <svg-file-or-directory> [--inplace]

Examples:
    python3 scripts/compact_svg_styles.py projects/example/svg_output --inplace
    python3 scripts/compact_svg_styles.py imported/authoring-svg-flat

Dependencies:
    None (standard library only).
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from svg_to_pptx.drawingml.utils import INHERITABLE_ATTRS

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
INHERITABLE_ATTRIBUTES = tuple(INHERITABLE_ATTRS)
_DEFINITION_SUBTREES = frozenset({
    "clipPath",
    "defs",
    "filter",
    "linearGradient",
    "marker",
    "mask",
    "pattern",
    "radialGradient",
    "symbol",
})

ET.register_namespace("", SVG_NS)


@dataclass
class StyleCompactionStats:
    """Count semantics-preserving authoring-style reductions."""

    root_font_defaults: int = 0
    root_style_declarations_normalized: int = 0
    shadowed_attributes_removed: int = 0
    redundant_attributes_removed: int = 0
    redundant_style_declarations_removed: int = 0

    @property
    def changed_declarations(self) -> int:
        return (
            self.root_font_defaults
            + self.root_style_declarations_normalized
            + self.shadowed_attributes_removed
            + self.redundant_attributes_removed
            + self.redundant_style_declarations_removed
        )

    def merge(self, other: "StyleCompactionStats") -> None:
        self.root_font_defaults += other.root_font_defaults
        self.root_style_declarations_normalized += (
            other.root_style_declarations_normalized
        )
        self.shadowed_attributes_removed += other.shadowed_attributes_removed
        self.redundant_attributes_removed += other.redundant_attributes_removed
        self.redundant_style_declarations_removed += (
            other.redundant_style_declarations_removed
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "root_font_defaults": self.root_font_defaults,
            "root_style_declarations_normalized": (
                self.root_style_declarations_normalized
            ),
            "shadowed_attributes_removed": self.shadowed_attributes_removed,
            "redundant_attributes_removed": self.redundant_attributes_removed,
            "redundant_style_declarations_removed": (
                self.redundant_style_declarations_removed
            ),
            "changed_declarations": self.changed_declarations,
        }


@dataclass(frozen=True)
class _StyleDeclaration:
    raw: str
    name: str
    value: str


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


def _style_declarations(value: str | None) -> list[_StyleDeclaration] | None:
    if value is None:
        return []
    declarations: list[_StyleDeclaration] = []
    for raw in value.split(";"):
        stripped = raw.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            return None
        raw_name, raw_value = stripped.split(":", 1)
        name = raw_name.strip().lower()
        normalized_value = raw_value.strip()
        if not name or not normalized_value:
            return None
        declarations.append(
            _StyleDeclaration(
                raw=stripped,
                name=name,
                value=normalized_value,
            )
        )
    return declarations


def _style_values(
    declarations: list[_StyleDeclaration],
) -> dict[str, str]:
    return {
        declaration.name: declaration.value
        for declaration in declarations
    }


def _write_style(
    element: ET.Element,
    declarations: list[_StyleDeclaration],
) -> None:
    if declarations:
        element.set("style", ";".join(item.raw for item in declarations))
    else:
        element.attrib.pop("style", None)


def _effective_value(
    element: ET.Element,
    name: str,
    parents: dict[ET.Element, ET.Element],
    cache: dict[tuple[int, str], str | None],
) -> str | None:
    key = (id(element), name)
    if key in cache:
        return cache[key]
    declarations = _style_declarations(element.get("style"))
    if declarations is None:
        cache[key] = None
        return None
    style_value = _style_values(declarations).get(name)
    if style_value is not None:
        cache[key] = style_value
        return style_value
    attribute_value = element.get(name)
    if attribute_value is not None:
        cache[key] = attribute_value
        return attribute_value
    parent = parents.get(element)
    resolved = (
        _effective_value(parent, name, parents, cache)
        if parent is not None
        else None
    )
    cache[key] = resolved
    return resolved


def _normalize_root_font_family(
    root: ET.Element,
    stats: StyleCompactionStats,
) -> None:
    declarations = _style_declarations(root.get("style"))
    if declarations is None:
        return
    style_values = _style_values(declarations)
    style_family = style_values.get("font-family")
    if style_family is not None:
        root.set("font-family", style_family)
        retained = [
            item for item in declarations
            if item.name != "font-family"
        ]
        _write_style(root, retained)
        stats.root_style_declarations_normalized += 1
        return
    if root.get("font-family") is not None:
        return

    parents = {
        child: parent
        for parent in root.iter()
        for child in parent
    }

    def inside_definition(element: ET.Element) -> bool:
        current = parents.get(element)
        while current is not None:
            if _local_name(current.tag) in _DEFINITION_SUBTREES:
                return True
            current = parents.get(current)
        return False

    text_elements = [
        element
        for element in root.iter()
        if _local_name(element.tag) == "text"
        and "".join(element.itertext()).strip()
        and not inside_definition(element)
    ]
    if not text_elements:
        return
    cache: dict[tuple[int, str], str | None] = {}
    families = [
        _effective_value(
            element,
            "font-family",
            parents,
            cache,
        )
        for element in text_elements
    ]
    if any(family is None or not family.strip() for family in families):
        return
    counts = Counter(str(family) for family in families)
    common = min(
        counts,
        key=lambda family: (-counts[family], len(family), family),
    )
    root.set("font-family", common)
    stats.root_font_defaults += 1


def _remove_redundant_inherited_styles(
    element: ET.Element,
    inherited: dict[str, str],
    stats: StyleCompactionStats,
) -> None:
    if _local_name(element.tag) in _DEFINITION_SUBTREES:
        return
    declarations = _style_declarations(element.get("style"))
    if declarations is None:
        return
    style_values = _style_values(declarations)
    remove_style_names: set[str] = set()
    effective = dict(inherited)

    for name in INHERITABLE_ATTRIBUTES:
        style_value = style_values.get(name)
        attribute_value = element.get(name)
        if style_value is not None:
            if attribute_value is not None:
                element.attrib.pop(name, None)
                stats.shadowed_attributes_removed += 1
            if style_value == inherited.get(name):
                remove_style_names.add(name)
                stats.redundant_style_declarations_removed += sum(
                    item.name == name for item in declarations
                )
            else:
                effective[name] = style_value
            continue
        if attribute_value is None:
            continue
        if attribute_value == inherited.get(name):
            element.attrib.pop(name, None)
            stats.redundant_attributes_removed += 1
        else:
            effective[name] = attribute_value

    if remove_style_names:
        _write_style(
            element,
            [
                item for item in declarations
                if item.name not in remove_style_names
            ],
        )
    for child in element:
        _remove_redundant_inherited_styles(child, effective, stats)


def compact_svg_style_tree(root: ET.Element) -> StyleCompactionStats:
    """Compact inherited declarations without changing effective SVG styles."""
    if _local_name(root.tag) != "svg":
        raise ValueError("Style compaction requires an SVG root element")
    stats = StyleCompactionStats()
    _normalize_root_font_family(root, stats)
    _remove_redundant_inherited_styles(root, {}, stats)
    return stats


def _svg_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".svg" else []
    return sorted(
        path for path in input_path.rglob("*.svg")
        if path.is_file()
    )


def _compact_svg_bytes(
    path: Path,
) -> tuple[bytes, StyleCompactionStats]:
    original = path.read_bytes()
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    root = ET.fromstring(original, parser=parser)
    stats = compact_svg_style_tree(root)
    if stats.changed_declarations == 0:
        return original, stats
    payload = ET.tostring(
        root,
        encoding="utf-8",
        xml_declaration=original.lstrip().startswith(b"<?xml"),
    )
    if not payload.endswith(b"\n"):
        payload += b"\n"
    return payload, stats


def _write_atomic(path: Path, payload: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(payload)
    try:
        temporary_path.chmod(mode)
        os.replace(temporary_path, path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Promote a common page font and remove redundant inherited SVG "
            "presentation declarations."
        ),
    )
    parser.add_argument("input", type=Path, help="SVG file or directory")
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Atomically replace changed SVG files",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.resolve()
    svg_files = _svg_files(input_path)
    if not svg_files:
        print(f"[ERROR] No SVG files found: {input_path}", file=sys.stderr)
        return 1

    prepared: list[tuple[Path, bytes, StyleCompactionStats]] = []
    total = StyleCompactionStats()
    try:
        for path in svg_files:
            payload, stats = _compact_svg_bytes(path)
            prepared.append((path, payload, stats))
            total.merge(stats)
    except (OSError, ET.ParseError, ValueError) as exc:
        print(f"[ERROR] SVG style compaction failed: {exc}", file=sys.stderr)
        return 1

    changed_files = 0
    if args.inplace:
        for path, payload, _stats in prepared:
            if payload == path.read_bytes():
                continue
            _write_atomic(path, payload)
            changed_files += 1
    else:
        changed_files = sum(
            payload != path.read_bytes()
            for path, payload, _stats in prepared
        )

    print(json.dumps({
        "input": str(input_path),
        "inplace": bool(args.inplace),
        "file_count": len(prepared),
        "changed_files": changed_files,
        "styles": total.as_dict(),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
