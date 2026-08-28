"""Native PowerPoint object converters for explicit SVG metadata markers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import posixpath
import sys
from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, ShapeResult
from ..drawingml.utils import _xml_escape
from .chart_data import _chart_data, _chart_plot_area_layout
from .chart_style import (
    _axis_titles,
    _chart_companion_entries,
    _chart_companion_text_xml,
    _chart_text_sizes,
    _chart_title_is_bounded,
    _classic_chart_style,
    _native_chart_chrome_errors,
    _native_chart_chrome_warnings,
    _native_chart_export_payload,
    _validate_chart_companion_boxes,
)
from .chart_xml import _chart_rels_xml, _chart_xml
from .chartex import (
    _chart_ex_colors_xml,
    _chart_ex_rels_xml,
    _chart_ex_style_xml,
    _chart_ex_xml,
)
from .fallback_hash import (
    native_fallback_contract_warnings,
    require_fresh_native_fallback,
    snapshot_native_fallback_freshness,
    stamp_native_fallback_baseline,
)
from .formula import FormulaSpec, build_native_formula, validate_formula_payload
from .formula_compiler import estimate_inline_formula_vertical_extent
from .inline_formula import (
    INLINE_FORMULA_ATTR,
    inline_formula_marker_errors,
)
from .marker_common import (
    CHART_CONTENT_TYPE,
    CHARTEX_CONTENT_TYPE,
    CHARTEX_REL_TYPE,
    CHARTEX_URI,
    CHART_COLOR_STYLE_CONTENT_TYPE,
    CHART_REL_TYPE,
    CHART_STYLE_CONTENT_TYPE,
    CHART_URI,
    _NATIVE_KINDS,
    _bounds,
    _load_payload,
    _local_tag,
    _native_marker_validation_context,
    _validate_bounds_inputs,
    native_marker_transform,
)
from .marker_attributes import (
    JSON_NATIVE_AUTHORITY,
    NATIVE_AUTHORITY_ATTR,
    NativeMarkerAttributeError,
    native_fallback_kind,
    native_import_source,
    native_metadata_payload_matches,
    native_json_is_authoritative,
    native_marker_legacy_warnings,
    native_replacement_kind,
    native_replacement_status,
)
from .marker_status import native_marker_status_errors
from semantic_table import expand_semantic_table_payload
from .table import (
    _build_native_table,
    _native_table_warnings,
    _validate_table_payload,
)
from .workbook import (
    _minimal_category_chart_workbook,
    _minimal_chart_ex_workbook,
    _minimal_xy_chart_workbook,
)

__all__ = [
    "convert_native_object",
    "estimate_inline_formula_vertical_extent",
    "INLINE_FORMULA_ATTR",
    "JSON_NATIVE_AUTHORITY",
    "NATIVE_AUTHORITY_ATTR",
    "NativeMarkerAttributeError",
    "native_fallback_kind",
    "native_import_source",
    "native_metadata_payload_matches",
    "native_json_is_authoritative",
    "native_marker_legacy_warnings",
    "native_object_marker_warnings",
    "native_object_projection_warnings",
    "native_replacement_kind",
    "native_replacement_status",
    "native_marker_transform",
    "inline_formula_marker_errors",
    "require_fresh_native_fallback",
    "snapshot_native_fallback_freshness",
    "stamp_native_fallback_baseline",
    "validate_native_object_marker",
    "validate_native_object_marker_with_warnings",
]


def _decode_source_chart_blob(blob: object, field_name: str) -> bytes:
    if not isinstance(blob, dict) or blob.get("encoding") != "base64":
        raise RuntimeError(f"Native PPTX chart {field_name} must be base64 metadata")
    encoded = blob.get("payload")
    expected_sha = blob.get("sha256")
    if not isinstance(encoded, str) or not isinstance(expected_sha, str):
        raise RuntimeError(f"Native PPTX chart {field_name} is incomplete")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RuntimeError(f"Native PPTX chart {field_name} is invalid base64") from exc
    if hashlib.sha256(payload).hexdigest() != expected_sha.lower():
        raise RuntimeError(f"Native PPTX chart {field_name} checksum mismatch")
    return payload


def _source_part_owner(rels_name: str) -> str:
    marker = "/_rels/"
    if marker not in rels_name or not rels_name.endswith(".rels"):
        raise RuntimeError("Native PPTX chart source relationship part name is invalid")
    parent, filename = rels_name.split(marker, 1)
    return f"{parent}/{filename[:-5]}"


def _decode_source_chart_package(
    payload: dict[str, Any],
) -> tuple[str, ET.Element, dict[str, bytes], dict[str, str]] | None:
    source = payload.get("source_package")
    if source is None:
        return None
    if not isinstance(source, dict):
        raise RuntimeError("Native PPTX chart source_package must be an object")
    chart_part = source.get("chart_part")
    raw_parts = source.get("parts")
    if (
        not isinstance(chart_part, str)
        or not chart_part.startswith("ppt/charts/")
        or not isinstance(raw_parts, list)
        or not raw_parts
        or len(raw_parts) > 32
    ):
        raise RuntimeError("Native PPTX chart source_package inventory is invalid")

    parts: dict[str, bytes] = {}
    content_types: dict[str, str] = {}
    total_size = 0
    for index, item in enumerate(raw_parts):
        if not isinstance(item, dict):
            raise RuntimeError("Native PPTX chart source_package part must be an object")
        name = item.get("name")
        if (
            not isinstance(name, str)
            or "\\" in name
            or name.startswith("/")
            or posixpath.normpath(name) != name
            or not name.startswith(
                ("ppt/charts/", "ppt/embeddings/", "ppt/theme/")
            )
            or name in parts
        ):
            raise RuntimeError("Native PPTX chart source_package part name is invalid")
        part_payload = _decode_source_chart_blob(
            item,
            f"source_package.parts[{index}]",
        )
        total_size += len(part_payload)
        if total_size > 20_000_000:
            raise RuntimeError("Native PPTX chart source_package is too large")
        parts[name] = part_payload
        content_type = item.get("content_type")
        if content_type is not None and not isinstance(content_type, str):
            raise RuntimeError(
                "Native PPTX chart source_package content_type must be a string"
            )
        if content_type:
            content_types[name] = content_type

    chart_xml = parts.get(chart_part)
    if chart_xml is None:
        raise RuntimeError("Native PPTX chart source_package omits its chart part")
    try:
        chart_root = ET.fromstring(chart_xml)
    except ET.ParseError as exc:
        raise RuntimeError("Native PPTX chart source package chart XML is malformed") from exc
    if chart_root.tag != f"{{{CHART_URI}}}chartSpace":
        raise RuntimeError("Native PPTX chart source package root must be c:chartSpace")

    package_rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    for name, part_payload in parts.items():
        if not name.endswith(".rels"):
            continue
        try:
            rels_root = ET.fromstring(part_payload)
        except ET.ParseError as exc:
            raise RuntimeError(
                "Native PPTX chart source relationship XML is malformed"
            ) from exc
        owner = _source_part_owner(name)
        for rel in rels_root.findall(f"{{{package_rel_ns}}}Relationship"):
            if rel.attrib.get("TargetMode") == "External":
                raise RuntimeError(
                    "Native PPTX chart source_package cannot contain external relationships"
                )
            target = rel.attrib.get("Target")
            if not target:
                raise RuntimeError(
                    "Native PPTX chart source_package relationship has no target"
                )
            resolved = posixpath.normpath(
                posixpath.join(posixpath.dirname(owner), target)
            ).lstrip("/")
            if resolved not in parts:
                raise RuntimeError(
                    "Native PPTX chart source_package relationship target is missing"
                )

    frame_payload = _decode_source_chart_blob(
        source.get("frame"),
        "source_package.frame",
    )
    try:
        frame = ET.fromstring(frame_payload)
    except ET.ParseError as exc:
        raise RuntimeError("Native PPTX chart source frame is malformed") from exc
    pml_ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    if frame.tag != f"{{{pml_ns}}}graphicFrame":
        raise RuntimeError("Native PPTX chart source frame must be p:graphicFrame")
    return chart_part, frame, parts, content_types


def _source_chart_frame_xml(
    frame: ET.Element,
    *,
    shape_id: int,
    rel_id: str,
) -> str:
    pml_ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    c_nv_pr = frame.find(f"{{{pml_ns}}}nvGraphicFramePr/{{{pml_ns}}}cNvPr")
    chart_refs = list(frame.iter(f"{{{CHART_URI}}}chart"))
    if c_nv_pr is None or len(chart_refs) != 1:
        raise RuntimeError("Native PPTX chart source frame structure is invalid")
    relationship_attrs = [
        (node, name)
        for node in frame.iter()
        for name in node.attrib
        if isinstance(name, str) and name.startswith(f"{{{rel_ns}}}")
    ]
    if len(relationship_attrs) != 1 or relationship_attrs[0][0] is not chart_refs[0]:
        raise RuntimeError(
            "Native PPTX chart source frame has unsupported relationships"
        )
    c_nv_pr.set("id", str(shape_id))
    chart_refs[0].set(f"{{{rel_ns}}}id", rel_id)
    return ET.tostring(frame, encoding="unicode")


def _build_native_chart(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    source_package = _decode_source_chart_package(payload)
    chart_data = None if source_package is not None else _chart_data(payload)
    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)

    shape_id = (
        ctx.claim_shape_id(
            elem.get("data-pptx-shape-id"),
            elem.get("data-pptx-shape-scope"),
        )
        if source_package is not None
        else ctx.next_id()
    )
    rel_id = ctx.next_rel_id()
    local_index = 1 + sum(1 for part in ctx.package_files if part.startswith("ppt/charts/chart"))
    part_index = ctx.slide_num * 100 + local_index
    workbook_name = f"Microsoft_Excel_Sheet{part_index}.xlsx"
    workbook_part = f"ppt/embeddings/{workbook_name}"
    if source_package is not None:
        chart_part, source_frame, source_parts, source_content_types = source_package
        chart_name = posixpath.basename(chart_part)
        graphic_uri = CHART_URI
        chart_ref_xml = ""
        ctx.rel_entries.append({
            "id": rel_id,
            "type": CHART_REL_TYPE,
            "target": posixpath.relpath(chart_part, "ppt/slides"),
        })
        for part_name, part_payload in source_parts.items():
            existing = ctx.package_files.get(part_name)
            if existing is not None and existing != part_payload:
                raise RuntimeError(
                    f"Native PPTX chart source package part collision: {part_name}"
                )
            ctx.package_files[part_name] = part_payload
        ctx.content_type_overrides.update(source_content_types)
    elif chart_data is not None and chart_data["kind"] == "chartex":
        chart_name = f"chartEx{part_index}.xml"
        style_name = f"style{part_index}.xml"
        colors_name = f"colors{part_index}.xml"
        chart_part = f"ppt/charts/{chart_name}"
        chart_rels_part = f"ppt/charts/_rels/{chart_name}.rels"
        style_part = f"ppt/charts/{style_name}"
        colors_part = f"ppt/charts/{colors_name}"
        graphic_uri = CHARTEX_URI
        chart_ref_xml = (
            f'<cx:chart xmlns:cx="{CHARTEX_URI}" '
            f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            f'r:id="{rel_id}"/>'
        )
        ctx.rel_entries.append({
            "id": rel_id,
            "type": CHARTEX_REL_TYPE,
            "target": f"../charts/{chart_name}",
        })
        ctx.package_files[chart_part] = _chart_ex_xml(payload, chart_data, chart_rels_id="rId1")
        ctx.package_files[chart_rels_part] = _chart_ex_rels_xml(
            f"../embeddings/{workbook_name}",
            style_name,
            colors_name,
        )
        ctx.package_files[style_part] = _chart_ex_style_xml()
        ctx.package_files[colors_part] = _chart_ex_colors_xml(payload)
        ctx.package_files[workbook_part] = _minimal_chart_ex_workbook(chart_data)
        ctx.content_type_overrides[chart_part] = CHARTEX_CONTENT_TYPE
        ctx.content_type_overrides[style_part] = CHART_STYLE_CONTENT_TYPE
        ctx.content_type_overrides[colors_part] = CHART_COLOR_STYLE_CONTENT_TYPE
    else:
        chart_name = f"chart{part_index}.xml"
        chart_part = f"ppt/charts/{chart_name}"
        chart_rels_part = f"ppt/charts/_rels/{chart_name}.rels"
        graphic_uri = CHART_URI
        chart_ref_xml = (
            '<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
            f'r:id="{rel_id}"/>'
        )
        ctx.rel_entries.append({
            "id": rel_id,
            "type": CHART_REL_TYPE,
            "target": f"../charts/{chart_name}",
        })
        ctx.package_files[chart_part] = _chart_xml(
            elem,
            payload,
            chart_rels_id="rId1",
            chart_data=chart_data,
            inherited_styles=ctx.inherited_styles,
            primary_language=ctx.primary_language,
            chart_bounds=(off_x, off_y, ext_cx, ext_cy),
        )
        ctx.package_files[chart_rels_part] = _chart_rels_xml(f"../embeddings/{workbook_name}")
        assert chart_data is not None
        if chart_data["kind"] == "xy":
            ctx.package_files[workbook_part] = _minimal_xy_chart_workbook(chart_data)
        else:
            ctx.package_files[workbook_part] = _minimal_category_chart_workbook(chart_data)
        ctx.content_type_overrides[chart_part] = CHART_CONTENT_TYPE

    name = _xml_escape(str(payload.get("name") or elem.get("id") or f"Native Chart {shape_id}"))
    chart_frame_xml = (
        _source_chart_frame_xml(
            source_frame,
            shape_id=shape_id,
            rel_id=rel_id,
        )
        if source_package is not None
        else f'''<p:graphicFrame>
<p:nvGraphicFramePr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr>
<p:nvPr/>
</p:nvGraphicFramePr>
<p:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></p:xfrm>
<a:graphic>
<a:graphicData uri="{graphic_uri}">
{chart_ref_xml}
</a:graphicData>
</a:graphic>
</p:graphicFrame>'''
    )
    if source_package is not None:
        companion_xml = ""
    else:
        assert chart_data is not None
        text_sizes = _chart_text_sizes(payload, elem, ctx.inherited_styles)
        chart_style = _classic_chart_style(payload, elem, ctx.inherited_styles)
        companion_xml = _chart_companion_text_xml(
            ctx,
            payload,
            chart_bounds=(off_x, off_y, ext_cx, ext_cy),
            chart_style=chart_style,
            note_font_size=text_sizes["note"],
            title_font_size=text_sizes["title"],
            include_title=(
                chart_data["kind"] == "chartex"
                or _chart_title_is_bounded(payload)
            ),
            include_subtitle_as_caption=chart_data["kind"] == "chartex",
        )
    xml = chart_frame_xml + companion_xml
    return ShapeResult(xml=xml, bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy))


def _validate_native_object_marker_payload(
    elem: ET.Element,
    *,
    validate_chrome: bool = True,
    ctx: ConvertContext | None = None,
    ancestors: tuple[ET.Element, ...] = (),
    require_fresh_fallback: bool = False,
) -> tuple[str, dict[str, Any], list[list[Any]] | FormulaSpec | None]:
    try:
        kind = native_replacement_kind(elem)
    except NativeMarkerAttributeError as exc:
        raise RuntimeError(str(exc)) from exc
    if not kind:
        return "", {}, None
    status_errors = native_marker_status_errors(elem)
    if status_errors:
        raise RuntimeError("; ".join(status_errors))
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-replace-with value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX replacement markers must be <g> elements")
    native_marker_transform(elem.get("transform"))
    if require_fresh_fallback and kind in {"chart", "table"}:
        require_fresh_native_fallback(elem, use_runtime_snapshot=True)

    try:
        payload = _load_payload(elem, kind)
    except NativeMarkerAttributeError as exc:
        raise RuntimeError(str(exc)) from exc
    if native_json_is_authoritative(elem):
        missing_bounds = [
            key for key in ("x", "y", "width", "height")
            if payload.get(key) is None
        ]
        if missing_bounds:
            raise RuntimeError(
                "JSON-authoritative Chart/Table metadata requires explicit "
                "x/y/width/height; missing " + ", ".join(missing_bounds)
            )
    bounds_ctx = ctx or _native_marker_validation_context(elem, ancestors)
    off_x, off_y, ext_cx, ext_cy, _ = _validate_bounds_inputs(elem, payload, bounds_ctx)
    validated_data: list[list[Any]] | FormulaSpec | None = None
    if kind == "table":
        _expanded_payload, table_rows, col_count, _merge_layout = (
            _validate_table_payload(payload)
        )
        validated_data = table_rows
        if ext_cx < col_count or ext_cy < len(table_rows):
            raise RuntimeError(
                "Native PPTX table bounds must provide at least one EMU per row and column"
            )
    elif kind == "chart":
        source_package = _decode_source_chart_package(payload)
        if (
            elem.get("data-pptx-roundtrip-object")
            == "source-chart-package"
            and source_package is None
        ):
            raise RuntimeError(
                "Round-trip source-chart marker requires source_package"
            )
        if source_package is None:
            chart_data = _chart_data(payload)
            _chart_plot_area_layout(
                chart_data,
                (off_x, off_y, ext_cx, ext_cy),
            )
            _validate_chart_companion_boxes(
                payload,
                chart_bounds=(off_x, off_y, ext_cx, ext_cy),
                include_title=(
                    chart_data["kind"] == "chartex"
                    or _chart_title_is_bounded(payload)
                ),
                include_subtitle_as_caption=chart_data["kind"] == "chartex",
            )
            if validate_chrome and native_import_source(elem) != "pptx":
                chrome_errors = _native_chart_chrome_errors(elem, payload)
                if chrome_errors:
                    raise RuntimeError("; ".join(chrome_errors))
    else:
        validated_data = validate_formula_payload(payload, ctx=ctx)
    return kind, payload, validated_data


def validate_native_object_marker(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
) -> None:
    """Validate a native replacement marker without mutating the package."""
    _validate_native_object_marker_payload(elem, ancestors=ancestors)


def _projection_warnings_for_validated_marker(
    elem: ET.Element,
    kind: str,
    payload: dict[str, Any],
    validated_data: list[list[Any]] | FormulaSpec | None,
) -> list[str]:
    if (
        native_json_is_authoritative(elem)
        or native_import_source(elem) == "pptx"
    ):
        return []
    if kind == "table" and isinstance(validated_data, list):
        # Expand a copy for the parity checks; the caller keeps the original
        # payload so the table writer can expand it again itself.
        return _native_table_warnings(
            elem,
            expand_semantic_table_payload(payload),
            validated_data,
        )
    if kind == "chart" and payload.get("source_package") is None:
        return _native_chart_chrome_warnings(elem, payload)
    return []


def native_object_projection_warnings(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
) -> list[str]:
    """Return SVG-first fallback details that marker metadata does not project."""
    kind, payload, validated_data = _validate_native_object_marker_payload(
        elem,
        ancestors=ancestors,
    )
    return _projection_warnings_for_validated_marker(
        elem,
        kind,
        payload,
        validated_data,
    )


def validate_native_object_marker_with_warnings(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
    document_root: ET.Element | None = None,
) -> list[str]:
    """Validate a native replacement marker and return non-fatal warnings."""
    kind, payload, validated_data = _validate_native_object_marker_payload(
        elem,
        ancestors=ancestors,
    )
    warnings = (
        native_fallback_contract_warnings(
            elem,
            document_root=document_root,
        )
        if kind in {"chart", "table"} else []
    )
    warnings.extend(
        _projection_warnings_for_validated_marker(
            elem,
            kind,
            payload,
            validated_data,
        )
    )
    return warnings


def native_object_marker_warnings(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
    document_root: ET.Element | None = None,
) -> list[str]:
    """Return non-fatal warnings for a native replacement marker."""
    return validate_native_object_marker_with_warnings(
        elem,
        ancestors=ancestors,
        document_root=document_root,
    )


def convert_native_object(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert a marked SVG group to its native PowerPoint object."""
    try:
        kind = native_replacement_kind(elem)
    except NativeMarkerAttributeError as exc:
        raise RuntimeError(str(exc)) from exc
    if not kind:
        return None

    kind, payload, validated_data = _validate_native_object_marker_payload(
        elem,
        validate_chrome=False,
        ctx=ctx,
        require_fresh_fallback=True,
    )
    if kind == "formula":
        formula_spec = (
            validated_data if isinstance(validated_data, FormulaSpec) else None
        )
        return build_native_formula(elem, ctx, payload, formula_spec)

    marker_id = elem.get("id") or "<unnamed>"
    for warning in native_fallback_contract_warnings(
        elem,
        use_runtime_snapshot=True,
    ):
        print(
            f"  Warning: data-pptx-replace-with marker {marker_id}: {warning}",
            file=sys.stderr,
        )
    if kind == "table":
        return _build_native_table(elem, ctx, payload)
    if payload.get("source_package") is None:
        payload, warnings = _native_chart_export_payload(elem, payload)
        for warning in warnings:
            print(
                f"  Warning: data-pptx-replace-with marker {marker_id}: {warning}",
                file=sys.stderr,
            )
    return _build_native_chart(elem, ctx, payload)
