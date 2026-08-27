#!/usr/bin/env python3
"""
PPT Master - Legacy SVG Inherited Style Migration

Diagnose or migrate older SVG authoring files to root/group defaults plus local
overrides. New authoring code calls the tree-level implementation before its
first write; the CLI is not a standard post-generation step.

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
import re
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
XLINK_NS = "http://www.w3.org/1999/xlink"
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
_UNSAFE_PRESENTATION_VALUE_TOKENS = (
    "!important",
    "var(",
)
_CSS_WIDE_VALUES = frozenset({
    "inherit",
    "initial",
    "revert",
    "revert-layer",
    "unset",
})
_CONTEXT_DEPENDENT_VALUES = frozenset({
    "context-fill",
    "context-stroke",
    "currentcolor",
})
_URL_FUNCTION_RE = re.compile(r"url\([^)]*\)", re.IGNORECASE)

ET.register_namespace("", SVG_NS)


@dataclass
class StyleCompactionStats:
    """Count semantics-preserving authoring-style reductions."""

    root_font_defaults: int = 0
    root_style_declarations_normalized: int = 0
    container_style_declarations_normalized: int = 0
    group_defaults_promoted: int = 0
    shadowed_attributes_removed: int = 0
    redundant_attributes_removed: int = 0
    redundant_style_declarations_removed: int = 0

    @property
    def changed_declarations(self) -> int:
        return (
            self.root_font_defaults
            + self.root_style_declarations_normalized
            + self.container_style_declarations_normalized
            + self.group_defaults_promoted
            + self.shadowed_attributes_removed
            + self.redundant_attributes_removed
            + self.redundant_style_declarations_removed
        )

    def merge(self, other: "StyleCompactionStats") -> None:
        self.root_font_defaults += other.root_font_defaults
        self.root_style_declarations_normalized += (
            other.root_style_declarations_normalized
        )
        self.container_style_declarations_normalized += (
            other.container_style_declarations_normalized
        )
        self.group_defaults_promoted += other.group_defaults_promoted
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
            "container_style_declarations_normalized": (
                self.container_style_declarations_normalized
            ),
            "group_defaults_promoted": self.group_defaults_promoted,
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


def is_canonical_presentation_value(
    value: str,
    *,
    property_name: str | None = None,
) -> bool:
    """Return whether a value can move to a presentation attribute safely."""
    normalized = value.strip().lower()
    context_dependent = False
    if property_name in {"fill", "stroke"}:
        outside_urls = _URL_FUNCTION_RE.sub(" ", normalized)
        tokens = {
            token for token in re.split(r"[\s,]+", outside_urls)
            if token
        }
        context_dependent = bool(tokens & _CONTEXT_DEPENDENT_VALUES)
    return (
        bool(normalized)
        and normalized not in _CSS_WIDE_VALUES
        and not context_dependent
        and not any(
            token in normalized
            for token in _UNSAFE_PRESENTATION_VALUE_TOKENS
        )
    )


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
        if not is_canonical_presentation_value(
            style_family,
            property_name="font-family",
        ):
            return
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

    # Include definition text conservatively. A local <use> can make it
    # visible, and promoting a font while ignoring that text could change its
    # inherited rendering. Unused definitions are pruned by import projection;
    # legacy migration prefers no promotion over a visual change.
    text_elements = [
        element
        for element in root.iter()
        if _local_name(element.tag) == "text"
        and "".join(element.itertext()).strip()
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


def _normalize_container_inherited_styles(
    root: ET.Element,
    stats: StyleCompactionStats,
) -> None:
    """Spell inherited root/group defaults as presentation attributes."""
    for element in root.iter():
        if _local_name(element.tag) not in {"svg", "g"}:
            continue
        declarations = _style_declarations(element.get("style"))
        if declarations is None:
            continue
        retained: list[_StyleDeclaration] = []
        for declaration in declarations:
            if (
                declaration.name not in INHERITABLE_ATTRIBUTES
                or not is_canonical_presentation_value(
                    declaration.value,
                    property_name=declaration.name,
                )
            ):
                retained.append(declaration)
                continue
            element.set(declaration.name, declaration.value)
            stats.container_style_declarations_normalized += 1
        _write_style(element, retained)


def _promote_common_group_defaults(
    element: ET.Element,
    stats: StyleCompactionStats,
) -> None:
    """Factor proven direct-child repetition into an existing SVG group."""
    if _local_name(element.tag) in _DEFINITION_SUBTREES:
        return
    for child in element:
        _promote_common_group_defaults(child, stats)
    if _local_name(element.tag) != "g":
        return

    children = [
        child for child in element
        if isinstance(child.tag, str)
        and _local_name(child.tag) not in {
            "desc",
            "metadata",
            "title",
        }
    ]
    if len(children) < 2:
        return

    element_styles = _style_declarations(element.get("style"))
    if element_styles is None:
        return
    element_style_values = _style_values(element_styles)
    for name in INHERITABLE_ATTRIBUTES:
        if element.get(name) is not None or name in element_style_values:
            continue
        declarations_by_child: list[list[_StyleDeclaration]] = []
        values: list[str] = []
        for child in children:
            declarations = _style_declarations(child.get("style"))
            if declarations is None:
                break
            declarations_by_child.append(declarations)
            value = _style_values(declarations).get(name)
            if value is None:
                value = child.get(name)
            if value is None or not is_canonical_presentation_value(
                value,
                property_name=name,
            ):
                break
            values.append(value)
        if len(values) != len(children) or len(set(values)) != 1:
            continue

        element.set(name, values[0])
        stats.group_defaults_promoted += 1
        for child, declarations in zip(children, declarations_by_child):
            removed_style = sum(item.name == name for item in declarations)
            if removed_style:
                _write_style(
                    child,
                    [item for item in declarations if item.name != name],
                )
                stats.redundant_style_declarations_removed += removed_style
            if child.get(name) is not None:
                child.attrib.pop(name, None)
                stats.redundant_attributes_removed += 1


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
            if (
                style_value == inherited.get(name)
                and is_canonical_presentation_value(
                    style_value,
                    property_name=name,
                )
            ):
                remove_style_names.add(name)
                stats.redundant_style_declarations_removed += sum(
                    item.name == name for item in declarations
                )
            else:
                effective[name] = style_value
            continue
        if attribute_value is None:
            continue
        if (
            attribute_value == inherited.get(name)
            and is_canonical_presentation_value(
                attribute_value,
                property_name=name,
            )
        ):
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
    _normalize_container_inherited_styles(root, stats)
    _normalize_root_font_family(root, stats)
    _promote_common_group_defaults(root, stats)
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
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
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
            "Diagnose or migrate older SVG by promoting a common page font "
            "and removing redundant inherited presentation declarations."
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
