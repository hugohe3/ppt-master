#!/usr/bin/env python3
"""Compact and expand the canonical semantic-table.v2 payload."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Iterable
from typing import Any


SEMANTIC_TABLE_SCHEMA = "ppt-master.semantic-table.v2"

_TOP_LEVEL_FIELDS = {
    "schema",
    "name",
    "x",
    "y",
    "width",
    "height",
    "strict_grid",
    "header_rows",
    "column_widths",
    "row_heights",
    "style",
    "defaults",
    "cell_styles",
    "columns",
    "rows",
}
_TABLE_STYLE_FIELDS = {
    "band_row",
    "font_family",
    "font_size",
    "header_font_size",
    "header_fill",
    "header_text",
    "body_fill",
    "body_text",
    "band_fill",
    "border_color",
    "border_width",
    "padding",
    "valign",
    "lang",
    "table_style_id",
}
_CELL_FORMAT_FIELDS = (
    "fill",
    "fill_opacity",
    "color",
    "font_size",
    "bold",
    "align",
    "valign",
    "borders",
    "padding",
    "padding_left",
    "padding_right",
    "padding_top",
    "padding_bottom",
    "border_color",
    "border_width",
    "lang",
    "anchor_center",
    "horizontal_overflow",
)
_CELL_FIELDS = set(_CELL_FORMAT_FIELDS) | {
    "text",
    "paragraphs",
    "row_span",
    "col_span",
    "merge_continuation",
    "cell_style",
}
_PARAGRAPH_DEFAULT_FIELDS = (
    "align",
    "line_spacing_percent",
)
_PARAGRAPH_FIELDS = set(_PARAGRAPH_DEFAULT_FIELDS) | {"text", "runs"}
_RUN_DEFAULT_FIELDS = (
    "bold",
    "italic",
    "underline",
    "strike",
    "color",
    "font_size",
    "font_family",
    "lang",
    "alt_lang",
    "baseline_percent",
    "outline",
)
_RUN_FIELDS = set(_RUN_DEFAULT_FIELDS) | {"text"}
_DEFAULT_SECTIONS = {
    "cell": set(_CELL_FORMAT_FIELDS),
    "paragraph": set(_PARAGRAPH_DEFAULT_FIELDS),
    "run": set(_RUN_DEFAULT_FIELDS),
}
_MERGED_OBJECT_FIELDS = {"padding"}
_STYLE_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _payload_size(payload: dict[str, Any], defaults: dict[str, Any]) -> int:
    return len(_canonical_json({"payload": payload, "defaults": defaults}))


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"Native PPTX table {label} must be an object")
    return value


def _reject_unknown_fields(
    value: dict[str, Any],
    allowed: set[str],
    label: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise RuntimeError(
            f"Native PPTX table {label} contains unsupported field(s): "
            + ", ".join(unknown)
        )


def _format_layers(*layers: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for layer in layers:
        for key, value in layer.items():
            if (
                key in _MERGED_OBJECT_FIELDS
                and isinstance(value, dict)
                and isinstance(result.get(key), dict)
            ):
                merged = copy.deepcopy(result[key])
                merged.update(copy.deepcopy(value))
                result[key] = merged
            else:
                result[key] = copy.deepcopy(value)
    return result


def _validated_defaults(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_defaults = payload.get("defaults", {})
    defaults = _require_object(raw_defaults, "defaults")
    _reject_unknown_fields(defaults, set(_DEFAULT_SECTIONS), "defaults")
    result: dict[str, dict[str, Any]] = {}
    for section, allowed in _DEFAULT_SECTIONS.items():
        raw_section = defaults.get(section, {})
        section_data = _require_object(raw_section, f"defaults.{section}")
        _reject_unknown_fields(
            section_data,
            allowed,
            f"defaults.{section}",
        )
        result[section] = copy.deepcopy(section_data)
    return result


def _validated_cell_styles(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_styles = payload.get("cell_styles", {})
    styles = _require_object(raw_styles, "cell_styles")
    result: dict[str, dict[str, Any]] = {}
    for name, raw_style in styles.items():
        if not isinstance(name, str) or not _STYLE_NAME_RE.fullmatch(name):
            raise RuntimeError(
                "Native PPTX table cell style names must use lower-case kebab-case"
            )
        style = _require_object(raw_style, f"cell_styles.{name}")
        _reject_unknown_fields(
            style,
            set(_CELL_FORMAT_FIELDS),
            f"cell_styles.{name}",
        )
        result[name] = copy.deepcopy(style)
    return result


def _expand_run(value: Any, run_defaults: dict[str, Any]) -> dict[str, Any]:
    run = _require_object(value, "run")
    _reject_unknown_fields(run, _RUN_FIELDS, "run")
    return _format_layers(run_defaults, run)


def _expand_paragraph(
    value: Any,
    paragraph_defaults: dict[str, Any],
    run_defaults: dict[str, Any],
) -> dict[str, Any]:
    if isinstance(value, str):
        paragraph = {"text": value}
    else:
        paragraph = _require_object(value, "paragraph")
        _reject_unknown_fields(paragraph, _PARAGRAPH_FIELDS, "paragraph")
    expanded = _format_layers(paragraph_defaults, paragraph)
    if "runs" in expanded:
        runs = expanded["runs"]
        if not isinstance(runs, list):
            raise RuntimeError("Native PPTX table paragraph runs must be a list")
        expanded["runs"] = [_expand_run(run, run_defaults) for run in runs]
    return expanded


def _expand_cell(
    value: Any,
    defaults: dict[str, dict[str, Any]],
    cell_styles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(value, dict):
        cell = copy.deepcopy(value)
        _reject_unknown_fields(cell, _CELL_FIELDS, "cell")
    else:
        cell = {"text": "" if value is None else str(value)}

    style_name = cell.pop("cell_style", None)
    if style_name is None:
        style = {}
    elif not isinstance(style_name, str) or style_name not in cell_styles:
        raise RuntimeError(
            f"Native PPTX table cell references unknown cell_style: {style_name!r}"
        )
    else:
        style = cell_styles[style_name]

    expanded = _format_layers(defaults["cell"], style, cell)
    if "paragraphs" in expanded:
        paragraphs = expanded["paragraphs"]
        if not isinstance(paragraphs, list):
            raise RuntimeError("Native PPTX table cell paragraphs must be a list")
        expanded["paragraphs"] = [
            _expand_paragraph(
                paragraph,
                defaults["paragraph"],
                defaults["run"],
            )
            for paragraph in paragraphs
        ]
    return expanded


def expand_semantic_table_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Expand semantic-table.v2 defaults and named styles into canonical cells."""
    source = _require_object(payload, "payload")
    if source.get("schema") != SEMANTIC_TABLE_SCHEMA:
        raise RuntimeError(
            "Native PPTX table metadata requires schema "
            f"{SEMANTIC_TABLE_SCHEMA!r}"
        )
    _reject_unknown_fields(source, _TOP_LEVEL_FIELDS, "payload")
    style = source.get("style", {})
    if not isinstance(style, dict):
        raise RuntimeError("Native PPTX table style must be an object")
    _reject_unknown_fields(style, _TABLE_STYLE_FIELDS, "style")

    defaults = _validated_defaults(source)
    cell_styles = _validated_cell_styles(source)
    expanded = {
        key: copy.deepcopy(value)
        for key, value in source.items()
        if key not in {"schema", "defaults", "cell_styles", "columns", "rows"}
    }
    if "columns" in source:
        columns = source["columns"]
        if not isinstance(columns, list):
            raise RuntimeError("Native PPTX table columns must be a list")
        expanded["columns"] = [
            _expand_cell(cell, defaults, cell_styles) for cell in columns
        ]
    if "rows" in source:
        rows = source["rows"]
        if not isinstance(rows, list):
            raise RuntimeError("Native PPTX table rows must be a list")
        expanded_rows: list[list[dict[str, Any]]] = []
        for row_index, row in enumerate(rows, start=1):
            if not isinstance(row, list):
                raise RuntimeError(
                    f"Native PPTX table row {row_index} must be a list"
                )
            expanded_rows.append(
                [_expand_cell(cell, defaults, cell_styles) for cell in row]
            )
        expanded["rows"] = expanded_rows
    return expanded


def _iter_cells(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    columns = payload.get("columns")
    if isinstance(columns, list):
        for cell in columns:
            if isinstance(cell, dict):
                yield cell
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, list):
                continue
            for cell in row:
                if isinstance(cell, dict):
                    yield cell


def _iter_paragraphs(cells: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for cell in cells:
        paragraphs = cell.get("paragraphs")
        if not isinstance(paragraphs, list):
            continue
        for paragraph in paragraphs:
            if isinstance(paragraph, dict):
                yield paragraph


def _iter_runs(paragraphs: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for paragraph in paragraphs:
        runs = paragraph.get("runs")
        if not isinstance(runs, list):
            continue
        for run in runs:
            if isinstance(run, dict):
                yield run


def _most_common_value(items: list[dict[str, Any]], field: str) -> Any:
    counts: dict[str, int] = {}
    values: dict[str, Any] = {}
    order: list[str] = []
    for item in items:
        signature = _canonical_json(item[field])
        if signature not in counts:
            counts[signature] = 0
            values[signature] = item[field]
            order.append(signature)
        counts[signature] += 1
    winner = max(order, key=lambda signature: counts[signature])
    return copy.deepcopy(values[winner])


def _promote_defaults(
    payload: dict[str, Any],
    defaults: dict[str, dict[str, Any]],
    section: str,
    items: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> None:
    if not items:
        return
    for field in fields:
        if any(field not in item for item in items):
            continue
        value = _most_common_value(items, field)
        before = _payload_size(payload, defaults)
        matching = [item for item in items if item[field] == value]
        defaults[section][field] = value
        for item in matching:
            del item[field]
        after = _payload_size(payload, defaults)
        if after < before:
            continue
        del defaults[section][field]
        for item in matching:
            item[field] = copy.deepcopy(value)


def _compact_plain_paragraphs(payload: dict[str, Any]) -> None:
    for cell in _iter_cells(payload):
        paragraphs = cell.get("paragraphs")
        if not isinstance(paragraphs, list):
            continue
        for index, paragraph in enumerate(paragraphs):
            if (
                isinstance(paragraph, dict)
                and set(paragraph) == {"text"}
                and isinstance(paragraph["text"], str)
            ):
                paragraphs[index] = paragraph["text"]


def _cell_style_signature(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        field: copy.deepcopy(cell[field])
        for field in _CELL_FORMAT_FIELDS
        if field in cell
    }


def _factor_cell_styles(
    payload: dict[str, Any],
    defaults: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    cells = list(_iter_cells(payload))
    signatures: dict[str, dict[str, Any]] = {}
    matching_cells: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for cell in cells:
        style = _cell_style_signature(cell)
        if not style:
            continue
        signature = _canonical_json(style)
        if signature not in signatures:
            signatures[signature] = style
            matching_cells[signature] = []
            order.append(signature)
        matching_cells[signature].append(cell)

    cell_styles: dict[str, dict[str, Any]] = {}
    for signature in order:
        matched = matching_cells[signature]
        if len(matched) < 2:
            continue
        name = f"cell-{len(cell_styles) + 1}"
        before = len(
            _canonical_json(
                {"payload": payload, "defaults": defaults, "cell_styles": cell_styles}
            )
        )
        style = signatures[signature]
        cell_styles[name] = copy.deepcopy(style)
        for cell in matched:
            for field in style:
                del cell[field]
            cell["cell_style"] = name
        after = len(
            _canonical_json(
                {"payload": payload, "defaults": defaults, "cell_styles": cell_styles}
            )
        )
        if after < before:
            continue
        del cell_styles[name]
        for cell in matched:
            del cell["cell_style"]
            cell.update(copy.deepcopy(style))
    return cell_styles


def compact_semantic_table_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic, lossless semantic-table.v2 representation."""
    source = _require_object(payload, "payload")
    if "schema" in source:
        working = expand_semantic_table_payload(source)
    else:
        working = copy.deepcopy(source)

    defaults: dict[str, dict[str, Any]] = {
        "cell": {},
        "paragraph": {},
        "run": {},
    }
    cells = list(_iter_cells(working))
    total_cells = len(working.get("columns", [])) + sum(
        len(row) for row in working.get("rows", []) if isinstance(row, list)
    )
    if cells and len(cells) == total_cells:
        _promote_defaults(
            working,
            defaults,
            "cell",
            cells,
            _CELL_FORMAT_FIELDS,
        )

    paragraphs = list(_iter_paragraphs(cells))
    paragraph_count = sum(
        len(cell["paragraphs"])
        for cell in cells
        if isinstance(cell.get("paragraphs"), list)
    )
    if paragraphs and len(paragraphs) == paragraph_count:
        _promote_defaults(
            working,
            defaults,
            "paragraph",
            paragraphs,
            _PARAGRAPH_DEFAULT_FIELDS,
        )

    runs = list(_iter_runs(paragraphs))
    run_count = sum(
        len(paragraph["runs"])
        for paragraph in paragraphs
        if isinstance(paragraph.get("runs"), list)
    )
    if runs and len(runs) == run_count:
        _promote_defaults(
            working,
            defaults,
            "run",
            runs,
            _RUN_DEFAULT_FIELDS,
        )

    _compact_plain_paragraphs(working)
    cell_styles = _factor_cell_styles(working, defaults)
    compact_defaults = {
        section: values for section, values in defaults.items() if values
    }

    result: dict[str, Any] = {"schema": SEMANTIC_TABLE_SCHEMA}
    for key, value in working.items():
        if key not in {"columns", "rows"}:
            result[key] = value
    if compact_defaults:
        result["defaults"] = compact_defaults
    if cell_styles:
        result["cell_styles"] = cell_styles
    if "columns" in working:
        result["columns"] = working["columns"]
    if "rows" in working:
        result["rows"] = working["rows"]

    expand_semantic_table_payload(result)
    return result
