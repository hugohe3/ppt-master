#!/usr/bin/env python3
"""
PPT Master - Text Outline Materialization

Resolve one supported SVG ``<text>`` operand into closed glyph-outline path
commands for the Shape Boolean geometry pipeline.

Usage:
    Import text_element_to_path_commands from svg_to_pptx.text_outline.

Dependencies:
    uharfbuzz and local PPT Master modules
"""

from __future__ import annotations

import bisect
import math
import os
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .drawingml.paths import PathCommand, normalize_path_commands
from .drawingml.text_properties import (
    normalize_project_text_segments,
    parse_project_font_style,
    parse_project_font_weight,
    parse_project_letter_spacing,
    parse_project_text_anchor,
    parse_project_text_decoration,
    resolve_project_xml_space,
)
from .drawingml.utils import (
    font_px_to_hpt,
    parse_inline_style,
    parse_project_geometry_length,
    parse_svg_length,
    split_project_text_clusters,
)


_FONT_EXTENSIONS = frozenset({".otc", ".otf", ".ttc", ".ttf"})
_FAMILY_NAME_IDS = (16, 1, 21)
_GENERIC_FAMILIES = {
    "sans-serif": (
        "Segoe UI",
        "Arial",
        "Helvetica",
        "Noto Sans",
        "Liberation Sans",
        "DejaVu Sans",
        "Nimbus Sans",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "Droid Sans Fallback",
    ),
    "system-ui": (
        "Segoe UI",
        "SF Pro",
        "Helvetica Neue",
        "Noto Sans",
        "Liberation Sans",
        "DejaVu Sans",
        "Noto Sans CJK SC",
        "Droid Sans Fallback",
    ),
    "serif": (
        "Times New Roman",
        "Noto Serif",
        "Liberation Serif",
        "DejaVu Serif",
        "Nimbus Roman",
        "Noto Serif CJK SC",
        "Source Han Serif SC",
    ),
    "monospace": (
        "Consolas",
        "Courier New",
        "Noto Sans Mono",
        "Liberation Mono",
        "DejaVu Sans Mono",
        "Nimbus Mono PS",
        "Noto Sans Mono CJK SC",
    ),
}
_GENERIC_FAMILIES["ui-sans-serif"] = _GENERIC_FAMILIES["system-ui"]
_GENERIC_FAMILIES["ui-serif"] = _GENERIC_FAMILIES["serif"]
_GENERIC_FAMILIES["ui-monospace"] = _GENERIC_FAMILIES["monospace"]
_UNSUPPORTED_TEXT_PROPERTIES = frozenset({
    "alignment-baseline",
    "baseline-shift",
    "direction",
    "dominant-baseline",
    "font-feature-settings",
    "font-kerning",
    "font-size-adjust",
    "font-stretch",
    "font-synthesis",
    "font-variant",
    "font-variation-settings",
    "font",
    "hyphens",
    "kerning",
    "line-height",
    "overflow-wrap",
    "text-align",
    "text-align-last",
    "text-indent",
    "text-orientation",
    "text-rendering",
    "text-transform",
    "unicode-bidi",
    "vertical-align",
    "white-space",
    "word-spacing",
    "word-break",
    "writing-mode",
})
_UNSUPPORTED_TEXT_ATTRIBUTES = frozenset({
    "dx",
    "dy",
    "lengthAdjust",
    "rotate",
    "textLength",
})
_UNSUPPORTED_BIDI_CLASSES = frozenset({
    "AL",
    "FSI",
    "LRE",
    "LRI",
    "LRO",
    "PDF",
    "PDI",
    "R",
    "RLE",
    "RLI",
    "RLO",
})
@dataclass(frozen=True)
class _FontFace:
    path: Path
    index: int
    families: tuple[str, ...]
    weight: int
    italic: bool
    weight_range: tuple[float, float] | None
    italic_range: tuple[float, float] | None
    coverage: frozenset[int]
    order: int


@dataclass(frozen=True)
class _TextStyle:
    families: tuple[str, ...]
    font_size: float
    font_weight: int
    italic: bool
    anchor: str
    letter_spacing: float


@dataclass(frozen=True)
class _FontRun:
    face: _FontFace
    clusters: tuple[str, ...]
    global_cluster_start: int

    @property
    def text(self) -> str:
        return "".join(self.clusters)


@dataclass
class _ShapedRun:
    run: _FontRun
    font: Any
    infos: Sequence[Any]
    positions: Sequence[Any]
    scale: float
    advance_x: float


@dataclass
class _DrawState:
    origin_x: float
    origin_y: float
    scale: float
    commands: list[PathCommand]
    segment_count: int = 0

    def point(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.origin_x + x * self.scale,
            self.origin_y - y * self.scale,
        )


def text_element_to_path_commands(
    element: ET.Element,
    parents: Mapping[ET.Element, ET.Element],
    *,
    font_dirs: Sequence[str | Path] = (),
) -> list[PathCommand]:
    """Return closed glyph outlines for one supported SVG ``<text>`` element."""
    chain = _element_chain(element, parents)
    _validate_text_structure(element, chain)
    text = _normalized_direct_text(element, chain)
    if not text:
        raise ValueError(f"{_element_label(element)} has no rendered text")
    if any(
        unicodedata.bidirectional(character)
        in _UNSUPPORTED_BIDI_CLASSES
        for character in text
    ):
        raise ValueError(
            f"{_element_label(element)} uses right-to-left or bidirectional "
            "text; materialize its glyph outlines before Shape Boolean"
        )

    style = _resolve_text_style(chain)
    x = _text_position(element, "x")
    y = _text_position(element, "y")
    explicit_roots = _normalize_explicit_font_dirs(font_dirs)
    catalog = _font_catalog(explicit_roots)
    candidates = _font_candidates(
        catalog,
        style.families,
        style.font_weight,
        style.italic,
    )
    if not candidates:
        family_list = ", ".join(style.families)
        raise ValueError(
            f"{_element_label(element)} cannot resolve an installed font from "
            f"{family_list!r}; add a usable fallback or pass --font-dir"
        )

    clusters = split_project_text_clusters(text)
    runs = _font_runs(
        element,
        clusters,
        candidates,
        style.families,
    )
    shaped_runs = _shape_runs(
        runs,
        style.font_size,
        style.font_weight,
        style.italic,
        style.letter_spacing,
    )
    natural_width = sum(run.advance_x for run in shaped_runs)
    tracked_width = (
        natural_width
        + max(0, len(clusters) - 1) * style.letter_spacing
    )
    if not math.isfinite(tracked_width) or tracked_width <= 0:
        raise ValueError(
            f"{_element_label(element)} resolves to a non-positive text width"
        )
    anchor_shift = {
        "start": 0.0,
        "middle": -tracked_width / 2.0,
        "end": -tracked_width,
    }[style.anchor]

    hb = _load_harfbuzz()
    draw_funcs = _draw_functions(hb)
    commands: list[PathCommand] = []
    natural_run_x = 0.0
    for shaped in shaped_runs:
        run_offsets = _cluster_offsets(shaped.run.clusters)
        glyph_cursor_x = 0.0
        glyph_cursor_y = 0.0
        for info, position in zip(shaped.infos, shaped.positions):
            if info.codepoint == 0:
                raise ValueError(
                    f"{_element_label(element)} shaped a missing glyph in "
                    f"{shaped.run.face.path.name}"
                )
            cluster_index = max(
                0,
                bisect.bisect_right(run_offsets, info.cluster) - 1,
            )
            cluster_index = min(
                cluster_index,
                len(shaped.run.clusters) - 1,
            )
            global_cluster = (
                shaped.run.global_cluster_start + cluster_index
            )
            spacing_shift = global_cluster * style.letter_spacing
            state = _DrawState(
                origin_x=(
                    x
                    + anchor_shift
                    + natural_run_x
                    + glyph_cursor_x
                    + position.x_offset * shaped.scale
                    + spacing_shift
                ),
                origin_y=(
                    y
                    - glyph_cursor_y
                    - position.y_offset * shaped.scale
                ),
                scale=shaped.scale,
                commands=commands,
            )
            shaped.font.draw_glyph(info.codepoint, draw_funcs, state)
            if state.segment_count == 0:
                cluster = shaped.run.clusters[cluster_index]
                if not _cluster_may_have_no_outline(cluster):
                    codepoints = " ".join(
                        f"U+{ord(character):04X}"
                        for character in cluster
                    )
                    raise ValueError(
                        f"{_element_label(element)} glyph for {codepoints} has "
                        "no vector outline; bitmap/color-only glyphs cannot be "
                        "used in Shape Boolean"
                    )
            glyph_cursor_x += position.x_advance * shaped.scale
            glyph_cursor_y += position.y_advance * shaped.scale
        natural_run_x += shaped.advance_x

    if not commands:
        raise ValueError(
            f"{_element_label(element)} has no glyph outline to materialize"
        )
    return normalize_path_commands(commands)


@lru_cache(maxsize=1)
def _load_harfbuzz() -> Any:
    try:
        import uharfbuzz
    except ImportError as exc:
        raise RuntimeError(
            "Text operands in Shape Boolean require uharfbuzz. Install the "
            "project requirements, or run: pip install uharfbuzz"
        ) from exc
    required = ("Blob", "Buffer", "DrawFuncs", "Face", "Font", "StyleTag", "shape")
    missing = [name for name in required if not hasattr(uharfbuzz, name)]
    if missing:
        raise RuntimeError(
            "Installed uharfbuzz is incompatible; missing: "
            + ", ".join(missing)
        )
    return uharfbuzz


def _element_chain(
    element: ET.Element,
    parents: Mapping[ET.Element, ET.Element],
) -> list[ET.Element]:
    chain = [element]
    current = element
    while current in parents:
        current = parents[current]
        chain.append(current)
    chain.reverse()
    return chain


def _validate_text_structure(
    element: ET.Element,
    chain: Sequence[ET.Element],
) -> None:
    if _local_name(element.tag) != "text":
        raise AssertionError("Text outline requires one <text> element")
    children = list(element)
    if children:
        child_tags = ", ".join(
            f"<{_local_name(child.tag)}>"
            for child in children
        )
        raise ValueError(
            f"{_element_label(element)} must contain direct single-line text; "
            f"child content is unsupported ({child_tags})"
        )
    unsupported_attrs = sorted(
        _local_name(name)
        for name in element.attrib
        if _local_name(name) in _UNSUPPORTED_TEXT_ATTRIBUTES
    )
    if unsupported_attrs:
        raise ValueError(
            f"{_element_label(element)} uses unsupported text attribute(s): "
            + ", ".join(unsupported_attrs)
        )

    for current in chain:
        inline = parse_inline_style(current.get("style"))
        unsupported = sorted(
            name
            for name in _UNSUPPORTED_TEXT_PROPERTIES
            if current.get(name) is not None or name in inline
        )
        if unsupported:
            raise ValueError(
                f"{_element_label(element)} inherits unsupported text "
                f"property/properties from {_element_label(current)}: "
                + ", ".join(unsupported)
            )

    decoration = _effective_property(chain, "text-decoration") or "none"
    try:
        parsed_decoration = parse_project_text_decoration(decoration)
    except ValueError as exc:
        raise ValueError(
            f"{_element_label(element)} text-decoration={decoration!r}: {exc}"
        ) from exc
    if parsed_decoration.canonical != "none":
        raise ValueError(
            f"{_element_label(element)} uses text decoration; materialize the "
            "decoration separately before Shape Boolean"
        )

    stroke = _effective_property(chain, "stroke")
    if stroke is not None and stroke.strip().lower() not in {
        "",
        "inherit",
        "none",
        "transparent",
    }:
        raise ValueError(
            f"{_element_label(element)} uses a visible text stroke; Shape "
            "Boolean materializes the filled glyph silhouette only"
        )


def _normalized_direct_text(
    element: ET.Element,
    chain: Sequence[ET.Element],
) -> str:
    xml_space = "default"
    for current in chain:
        try:
            xml_space = resolve_project_xml_space(current, xml_space)
        except ValueError as exc:
            raise ValueError(
                f"{_element_label(current)} xml:space: {exc}"
            ) from exc
    segments = normalize_project_text_segments([
        (xml_space, element.text or ""),
    ])
    return "".join(text for _owner, text in segments)


def _resolve_text_style(chain: Sequence[ET.Element]) -> _TextStyle:
    font_size = 16.0
    root_font_size = 16.0
    letter_spacing = 0.0
    family_value = "sans-serif"
    weight_value = "normal"
    style_value = "normal"
    anchor_value = "start"

    for index, current in enumerate(chain):
        inline = parse_inline_style(current.get("style"))
        raw_size = inline.get("font-size", current.get("font-size"))
        if raw_size is not None and raw_size.strip().lower() != "inherit":
            relative_base = (
                root_font_size
                if raw_size.strip().lower().endswith("rem")
                else font_size
            )
            try:
                font_size = parse_svg_length(
                    raw_size,
                    font_size,
                    font_size=relative_base,
                )
                font_px_to_hpt(font_size)
            except ValueError as exc:
                raise ValueError(
                    f"{_element_label(current)} font-size={raw_size!r}: {exc}"
                ) from exc
        if index == 0:
            root_font_size = font_size

        raw_spacing = inline.get(
            "letter-spacing",
            current.get("letter-spacing"),
        )
        if raw_spacing is not None and raw_spacing.strip().lower() != "inherit":
            try:
                letter_spacing = float(parse_project_letter_spacing(
                    raw_spacing,
                    font_size=font_size,
                ).value)
            except ValueError as exc:
                raise ValueError(
                    f"{_element_label(current)} "
                    f"letter-spacing={raw_spacing!r}: {exc}"
                ) from exc

        family_value = _updated_property(
            current,
            inline,
            "font-family",
            family_value,
        )
        weight_value = _updated_property(
            current,
            inline,
            "font-weight",
            weight_value,
        )
        style_value = _updated_property(
            current,
            inline,
            "font-style",
            style_value,
        )
        anchor_value = _updated_property(
            current,
            inline,
            "text-anchor",
            anchor_value,
        )

    families = _parse_font_family_stack(family_value)
    try:
        parsed_weight = parse_project_font_weight(weight_value)
        parsed_style = parse_project_font_style(style_value)
        parsed_anchor = parse_project_text_anchor(anchor_value)
    except ValueError as exc:
        raise ValueError(
            f"{_element_label(chain[-1])} has invalid text typography: {exc}"
        ) from exc
    weight = {
        "normal": 400,
        "bold": 700,
    }.get(parsed_weight.canonical)
    if weight is None:
        weight = int(parsed_weight.canonical)
    return _TextStyle(
        families=families,
        font_size=font_size,
        font_weight=weight,
        italic=bool(parsed_style.value),
        anchor=str(parsed_anchor.value),
        letter_spacing=letter_spacing,
    )


def _updated_property(
    element: ET.Element,
    inline: Mapping[str, str],
    name: str,
    inherited: str,
) -> str:
    raw = inline.get(name, element.get(name))
    if raw is None or raw.strip().lower() == "inherit":
        return inherited
    value = raw.strip()
    if not value:
        raise ValueError(f"{_element_label(element)} {name} must not be empty")
    return value


def _effective_property(
    chain: Sequence[ET.Element],
    name: str,
) -> str | None:
    value: str | None = None
    for current in chain:
        inline = parse_inline_style(current.get("style"))
        raw = inline.get(name, current.get(name))
        if raw is not None and raw.strip().lower() != "inherit":
            value = raw.strip()
    return value


def _text_position(element: ET.Element, name: str) -> float:
    raw = element.get(name)
    if raw is None:
        return 0.0
    try:
        return parse_project_geometry_length(raw, name)
    except ValueError as exc:
        raise ValueError(
            f"{_element_label(element)} {name}={raw!r}: {exc}"
        ) from exc


def _parse_font_family_stack(raw: str) -> tuple[str, ...]:
    families = tuple(
        value.strip().strip("'\"")
        for value in raw.split(",")
    )
    if not families or any(not family for family in families):
        raise ValueError("font-family must contain at least one family name")
    return families


def _normalize_explicit_font_dirs(
    font_dirs: Sequence[str | Path],
) -> tuple[str, ...]:
    if isinstance(font_dirs, (str, bytes)):
        raise ValueError(
            "Shape Boolean font_dirs must be a sequence of directory paths"
        )
    roots: list[str] = []
    seen: set[str] = set()
    for raw in font_dirs:
        root = Path(raw).expanduser()
        if not root.is_dir():
            raise ValueError(f"Shape Boolean font directory not found: {root}")
        resolved = str(root.resolve())
        if resolved not in seen:
            roots.append(resolved)
            seen.add(resolved)
    return tuple(roots)


@lru_cache(maxsize=8)
def _font_catalog(explicit_roots: tuple[str, ...]) -> tuple[_FontFace, ...]:
    hb = _load_harfbuzz()
    records: list[_FontFace] = []
    for path in _font_files(explicit_roots):
        try:
            data = path.read_bytes()
            first_face = hb.Face(data, 0)
            face_count = max(1, int(first_face.count))
        except (OSError, RuntimeError, ValueError):
            continue
        for index in range(face_count):
            try:
                face = hb.Face(data, index)
                families = _face_names(face, _FAMILY_NAME_IDS)
                if not families:
                    continue
                font = hb.Font(face)
                weight_value = font.get_style_value(hb.StyleTag.WEIGHT)
                italic_value = font.get_style_value(hb.StyleTag.ITALIC)
                slant_value = font.get_style_value(hb.StyleTag.SLANT_ANGLE)
                axes = {
                    axis.tag: axis
                    for axis in face.axis_infos
                }
                coverage = frozenset(int(value) for value in face.unicodes)
            except (OSError, RuntimeError, TypeError, ValueError):
                continue
            weight = int(round(weight_value)) if math.isfinite(weight_value) else 400
            weight = min(1000, max(1, weight))
            italic = (
                math.isfinite(italic_value) and italic_value >= 0.5
            ) or (
                math.isfinite(slant_value) and abs(slant_value) > 0.01
            )
            records.append(_FontFace(
                path=path,
                index=index,
                families=families,
                weight=weight,
                italic=italic,
                weight_range=_axis_range(axes.get("wght")),
                italic_range=_axis_range(axes.get("ital")),
                coverage=coverage,
                order=len(records),
            ))
    if not records:
        raise RuntimeError(
            "Text operands in Shape Boolean found no readable OpenType fonts; "
            "install fonts or pass --font-dir"
        )
    return tuple(records)


def _font_files(explicit_roots: tuple[str, ...]) -> tuple[Path, ...]:
    roots = [Path(value) for value in explicit_roots]
    roots.extend(_system_font_roots())
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        try:
            candidates = sorted(
                (
                    path
                    for path in root.rglob("*")
                    if path.is_file()
                    and path.suffix.lower() in _FONT_EXTENSIONS
                ),
                key=lambda path: str(path).casefold(),
            )
        except OSError:
            continue
        for path in candidates:
            try:
                key = str(path.resolve())
            except OSError:
                key = str(path)
            if key not in seen:
                files.append(path)
                seen.add(key)
    return tuple(files)


def _system_font_roots() -> tuple[Path, ...]:
    roots: list[Path] = []
    home = Path.home()
    if sys.platform.startswith("win"):
        windows = Path(os.environ.get("WINDIR", "C:/Windows"))
        roots.append(windows / "Fonts")
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            roots.append(Path(local_app_data) / "Microsoft/Windows/Fonts")
    elif sys.platform == "darwin":
        roots.extend((
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            home / "Library/Fonts",
        ))
    else:
        xdg_data_home = os.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            roots.append(Path(xdg_data_home) / "fonts")
        roots.extend((home / ".local/share/fonts", home / ".fonts"))
        xdg_data_dirs = os.environ.get(
            "XDG_DATA_DIRS",
            "/usr/local/share:/usr/share",
        )
        roots.extend(
            Path(value) / "fonts"
            for value in xdg_data_dirs.split(os.pathsep)
            if value
        )
    return tuple(roots)


def _face_names(face: Any, name_ids: Sequence[int]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for name_id in name_ids:
        value = face.get_name(name_id)
        if not value:
            continue
        normalized = " ".join(str(value).split())
        key = _family_key(normalized)
        if normalized and key not in seen:
            values.append(normalized)
            seen.add(key)
    return tuple(values)


def _font_candidates(
    catalog: Sequence[_FontFace],
    families: Sequence[str],
    target_weight: int,
    italic: bool,
) -> list[_FontFace]:
    by_family: dict[str, list[_FontFace]] = {}
    for face in catalog:
        for family in face.families:
            by_family.setdefault(_family_key(family), []).append(face)

    candidates: list[_FontFace] = []
    seen: set[tuple[Path, int]] = set()
    for requested in families:
        requested_key = _family_key(requested)
        generic = requested_key in _GENERIC_FAMILIES
        expanded = _GENERIC_FAMILIES.get(requested_key, (requested,))
        for family in expanded:
            available = by_family.get(_family_key(family), ())
            if generic:
                available = tuple(
                    face
                    for face in available
                    if _face_supports_style(
                        face,
                        target_weight,
                        italic,
                    )
                )
            matches = sorted(
                available,
                key=lambda face: (
                    not _face_supports_style(
                        face,
                        target_weight,
                        italic,
                    ),
                    face.italic != italic,
                    abs(face.weight - target_weight),
                    face.order,
                ),
            )
            for face in matches:
                key = (face.path, face.index)
                if key not in seen:
                    candidates.append(face)
                    seen.add(key)
    return candidates


def _face_supports_style(
    face: _FontFace,
    requested_weight: int,
    requested_italic: bool,
) -> bool:
    weight_supported = (
        face.weight == requested_weight
        or (
            face.weight_range is not None
            and face.weight_range[0]
            <= requested_weight
            <= face.weight_range[1]
        )
    )
    italic_value = 1.0 if requested_italic else 0.0
    italic_supported = (
        face.italic == requested_italic
        or (
            face.italic_range is not None
            and face.italic_range[0]
            <= italic_value
            <= face.italic_range[1]
        )
    )
    return weight_supported and italic_supported


def _axis_range(axis: Any | None) -> tuple[float, float] | None:
    if axis is None:
        return None
    return (float(axis.min_value), float(axis.max_value))


def _font_runs(
    element: ET.Element,
    clusters: Sequence[str],
    candidates: Sequence[_FontFace],
    families: Sequence[str],
) -> list[_FontRun]:
    selected: list[tuple[str, _FontFace]] = []
    previous_face: _FontFace | None = None
    for cluster in clusters:
        required = _required_codepoints(cluster)
        face = next(
            (
                candidate
                for candidate in candidates
                if required.issubset(candidate.coverage)
            ),
            None,
        )
        if face is None and not required and previous_face is not None:
            face = previous_face
        if face is None:
            codepoints = " ".join(
                f"U+{ord(character):04X}"
                for character in cluster
            )
            raise ValueError(
                f"{_element_label(element)} cannot resolve glyphs for "
                f"{codepoints} from font stack {', '.join(families)!r}"
            )
        selected.append((cluster, face))
        previous_face = face

    runs: list[_FontRun] = []
    run_clusters: list[str] = []
    run_face: _FontFace | None = None
    run_start = 0
    for index, (cluster, face) in enumerate(selected):
        if run_face is None or face is run_face:
            run_clusters.append(cluster)
            run_face = face
            continue
        runs.append(_FontRun(
            face=run_face,
            clusters=tuple(run_clusters),
            global_cluster_start=run_start,
        ))
        run_clusters = [cluster]
        run_face = face
        run_start = index
    if run_face is not None:
        runs.append(_FontRun(
            face=run_face,
            clusters=tuple(run_clusters),
            global_cluster_start=run_start,
        ))
    return runs


def _shape_runs(
    runs: Sequence[_FontRun],
    font_size: float,
    font_weight: int,
    italic: bool,
    letter_spacing: float,
) -> list[_ShapedRun]:
    hb = _load_harfbuzz()
    font_cache: dict[tuple[Path, int], tuple[Any, int]] = {}
    shaped: list[_ShapedRun] = []
    for run in runs:
        key = (run.face.path, run.face.index)
        cached = font_cache.get(key)
        if cached is None:
            data = run.face.path.read_bytes()
            face = hb.Face(data, run.face.index)
            upem = int(face.upem)
            if upem <= 0:
                raise ValueError(
                    f"Font {run.face.path} face {run.face.index} has invalid UPEM"
                )
            font = hb.Font(face)
            font.scale = (upem, upem)
            _apply_font_style(
                run.face,
                face,
                font,
                font_weight,
                italic,
            )
            cached = (font, upem)
            font_cache[key] = cached
        font, upem = cached
        buffer = hb.Buffer()
        buffer.add_str(run.text)
        buffer.guess_segment_properties()
        if str(buffer.direction) != "ltr":
            raise ValueError(
                f"Text run {run.text!r} resolves to {buffer.direction} "
                "direction; only horizontal left-to-right text is supported"
            )
        if letter_spacing:
            hb.shape(font, buffer, {"liga": False, "clig": False})
        else:
            hb.shape(font, buffer)
        infos = tuple(buffer.glyph_infos)
        positions = tuple(buffer.glyph_positions)
        if not infos or len(infos) != len(positions):
            raise ValueError(f"Font shaping produced no glyphs for {run.text!r}")
        scale = font_size / upem
        advance_x = sum(position.x_advance for position in positions) * scale
        shaped.append(_ShapedRun(
            run=run,
            font=font,
            infos=infos,
            positions=positions,
            scale=scale,
            advance_x=advance_x,
        ))
    return shaped


def _apply_font_style(
    record: _FontFace,
    face: Any,
    font: Any,
    requested_weight: int,
    requested_italic: bool,
) -> None:
    axes = {
        axis.tag: axis
        for axis in face.axis_infos
    }
    variations: dict[str, float] = {}
    weight_axis = axes.get("wght")
    if weight_axis is not None:
        if not weight_axis.min_value <= requested_weight <= weight_axis.max_value:
            raise ValueError(
                f"Font {record.path.name} cannot provide requested weight "
                f"{requested_weight}; its wght axis is "
                f"{weight_axis.min_value:g}..{weight_axis.max_value:g}"
            )
        variations["wght"] = float(requested_weight)
    elif record.weight != requested_weight:
        raise ValueError(
            f"Font {record.path.name} resolves weight {record.weight}, not "
            f"requested {requested_weight}; install the exact face, choose a "
            "matching family, or adjust the text operand"
        )

    italic_axis = axes.get("ital")
    italic_value = 1.0 if requested_italic else 0.0
    if italic_axis is not None:
        if not italic_axis.min_value <= italic_value <= italic_axis.max_value:
            style = "italic" if requested_italic else "normal"
            raise ValueError(
                f"Font {record.path.name} cannot provide requested {style} "
                "style through its ital axis"
            )
        variations["ital"] = italic_value
    elif record.italic != requested_italic:
        requested = "italic" if requested_italic else "normal"
        resolved = "italic" if record.italic else "normal"
        raise ValueError(
            f"Font {record.path.name} resolves {resolved}, not requested "
            f"{requested}; install the exact face, choose a matching family, "
            "or adjust the text operand"
        )

    if variations:
        font.set_variations(variations)


def _draw_functions(hb: Any) -> Any:
    functions = hb.DrawFuncs()

    def move_to(x: float, y: float, state: _DrawState) -> None:
        point = state.point(x, y)
        state.commands.append(PathCommand("M", [*point]))

    def line_to(x: float, y: float, state: _DrawState) -> None:
        point = state.point(x, y)
        state.commands.append(PathCommand("L", [*point]))
        state.segment_count += 1

    def quadratic_to(
        control_x: float,
        control_y: float,
        x: float,
        y: float,
        state: _DrawState,
    ) -> None:
        control = state.point(control_x, control_y)
        point = state.point(x, y)
        state.commands.append(PathCommand(
            "Q",
            [control[0], control[1], point[0], point[1]],
        ))
        state.segment_count += 1

    def cubic_to(
        control_1_x: float,
        control_1_y: float,
        control_2_x: float,
        control_2_y: float,
        x: float,
        y: float,
        state: _DrawState,
    ) -> None:
        control_1 = state.point(control_1_x, control_1_y)
        control_2 = state.point(control_2_x, control_2_y)
        point = state.point(x, y)
        state.commands.append(PathCommand(
            "C",
            [
                control_1[0],
                control_1[1],
                control_2[0],
                control_2[1],
                point[0],
                point[1],
            ],
        ))
        state.segment_count += 1

    def close_path(state: _DrawState) -> None:
        state.commands.append(PathCommand("Z", []))

    functions.set_move_to_func(move_to)
    functions.set_line_to_func(line_to)
    functions.set_quadratic_to_func(quadratic_to)
    functions.set_cubic_to_func(cubic_to)
    functions.set_close_path_func(close_path)
    return functions


def _cluster_offsets(clusters: Sequence[str]) -> list[int]:
    offsets: list[int] = []
    offset = 0
    for cluster in clusters:
        offsets.append(offset)
        offset += len(cluster)
    return offsets


def _required_codepoints(cluster: str) -> frozenset[int]:
    return frozenset(
        ord(character)
        for character in cluster
        if not _is_default_ignorable(character)
    )


def _is_default_ignorable(character: str) -> bool:
    codepoint = ord(character)
    return (
        unicodedata.category(character) == "Cf"
        or 0x180B <= codepoint <= 0x180D
        or 0x2061 <= codepoint <= 0x206F
        or 0xFE00 <= codepoint <= 0xFE0F
        or 0xE0100 <= codepoint <= 0xE01EF
    )


def _cluster_may_have_no_outline(cluster: str) -> bool:
    return all(
        character.isspace() or _is_default_ignorable(character)
        for character in cluster
    )


def _family_key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _local_name(tag: object) -> str:
    raw = str(tag)
    return raw.rsplit("}", 1)[-1] if "}" in raw else raw


def _element_label(element: ET.Element) -> str:
    tag = _local_name(element.tag)
    element_id = element.get("id")
    return f"<{tag} id={element_id!r}>" if element_id else f"<{tag}>"
