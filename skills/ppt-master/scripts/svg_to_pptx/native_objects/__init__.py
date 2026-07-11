"""Native PowerPoint table/chart converters for explicit SVG metadata markers."""

from __future__ import annotations

import sys
from typing import Any
from xml.etree import ElementTree as ET

from ..drawingml.context import ConvertContext, ShapeResult
from ..drawingml.utils import _xml_escape
from .chart_data import _chart_data
from .chart_style import (
    _axis_titles,
    _chart_companion_entries,
    _chart_companion_text_xml,
    _chart_text_sizes,
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
from .marker_status import native_marker_status_errors
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
    "native_object_marker_warnings",
    "native_marker_transform",
    "snapshot_native_fallback_freshness",
    "stamp_native_fallback_baseline",
    "validate_native_object_marker",
    "validate_native_object_marker_with_warnings",
]


def _build_native_chart(elem: ET.Element, ctx: ConvertContext, payload: dict[str, Any]) -> ShapeResult:
    chart_data = _chart_data(payload)
    off_x, off_y, ext_cx, ext_cy = _bounds(elem, payload, ctx)

    shape_id = ctx.next_id()
    rel_id = ctx.next_rel_id()
    local_index = 1 + sum(1 for part in ctx.package_files if part.startswith("ppt/charts/chart"))
    part_index = ctx.slide_num * 100 + local_index
    workbook_name = f"Microsoft_Excel_Sheet{part_index}.xlsx"
    workbook_part = f"ppt/embeddings/{workbook_name}"

    if chart_data["kind"] == "chartex":
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
        )
        ctx.package_files[chart_rels_part] = _chart_rels_xml(f"../embeddings/{workbook_name}")
        if chart_data["kind"] == "xy":
            ctx.package_files[workbook_part] = _minimal_xy_chart_workbook(chart_data)
        else:
            ctx.package_files[workbook_part] = _minimal_category_chart_workbook(chart_data)
        ctx.content_type_overrides[chart_part] = CHART_CONTENT_TYPE

    name = _xml_escape(str(payload.get("name") or elem.get("id") or f"Native Chart {shape_id}"))
    chart_frame_xml = f'''<p:graphicFrame>
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
    text_sizes = _chart_text_sizes(payload, elem, ctx.inherited_styles)
    chart_style = _classic_chart_style(payload, elem, ctx.inherited_styles)
    companion_xml = _chart_companion_text_xml(
        ctx,
        payload,
        chart_bounds=(off_x, off_y, ext_cx, ext_cy),
        chart_style=chart_style,
        note_font_size=text_sizes["note"],
        title_font_size=text_sizes["title"],
        include_title=chart_data["kind"] == "chartex",
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
) -> tuple[str, dict[str, Any], list[list[Any]] | None]:
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return "", {}, None
    status_errors = native_marker_status_errors(elem)
    if status_errors:
        raise RuntimeError("; ".join(status_errors))
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    native_marker_transform(elem.get("transform"))
    if require_fresh_fallback:
        require_fresh_native_fallback(elem, use_runtime_snapshot=True)

    payload = _load_payload(elem, kind)
    bounds_ctx = ctx or _native_marker_validation_context(elem, ancestors)
    off_x, off_y, ext_cx, ext_cy, _ = _validate_bounds_inputs(elem, payload, bounds_ctx)
    table_rows = None
    if kind == "table":
        table_rows, col_count = _validate_table_payload(payload)
        if ext_cx < col_count or ext_cy < len(table_rows):
            raise RuntimeError(
                "Native PPTX table bounds must provide at least one EMU per row and column"
            )
    else:
        chart_data = _chart_data(payload)
        _validate_chart_companion_boxes(
            payload,
            chart_bounds=(off_x, off_y, ext_cx, ext_cy),
            include_title=chart_data["kind"] == "chartex",
            include_subtitle_as_caption=chart_data["kind"] == "chartex",
        )
        if validate_chrome and elem.get("data-pptx-native-source") != "pptx":
            chrome_errors = _native_chart_chrome_errors(elem, payload)
            if chrome_errors:
                raise RuntimeError("; ".join(chrome_errors))
    return kind, payload, table_rows


def validate_native_object_marker(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
) -> None:
    """Validate a data-pptx-native marker without mutating the PPTX package."""
    _validate_native_object_marker_payload(elem, ancestors=ancestors)


def validate_native_object_marker_with_warnings(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
    document_root: ET.Element | None = None,
) -> list[str]:
    """Validate a data-pptx-native marker and return non-fatal warnings."""
    kind, payload, table_rows = _validate_native_object_marker_payload(
        elem,
        ancestors=ancestors,
    )
    warnings = (
        native_fallback_contract_warnings(
            elem,
            document_root=document_root,
        )
        if kind else []
    )
    if kind == "table" and table_rows is not None:
        warnings.extend(_native_table_warnings(elem, table_rows))
    elif kind == "chart":
        warnings.extend(_native_chart_chrome_warnings(elem, payload))
    return warnings


def native_object_marker_warnings(
    elem: ET.Element,
    *,
    ancestors: tuple[ET.Element, ...] = (),
    document_root: ET.Element | None = None,
) -> list[str]:
    """Return non-fatal warnings for a data-pptx-native marker."""
    return validate_native_object_marker_with_warnings(
        elem,
        ancestors=ancestors,
        document_root=document_root,
    )


def convert_native_object(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert a marked SVG group to a native PowerPoint table or chart."""
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return None

    kind, payload, _ = _validate_native_object_marker_payload(
        elem,
        validate_chrome=False,
        ctx=ctx,
        require_fresh_fallback=True,
    )
    marker_id = elem.get("id") or "<unnamed>"
    for warning in native_fallback_contract_warnings(
        elem,
        use_runtime_snapshot=True,
    ):
        print(
            f"  Warning: data-pptx-native marker {marker_id}: {warning}",
            file=sys.stderr,
        )
    if kind == "table":
        return _build_native_table(elem, ctx, payload)
    payload, warnings = _native_chart_export_payload(elem, payload)
    for warning in warnings:
        print(
            f"  Warning: data-pptx-native marker {marker_id}: {warning}",
            file=sys.stderr,
        )
    return _build_native_chart(elem, ctx, payload)
