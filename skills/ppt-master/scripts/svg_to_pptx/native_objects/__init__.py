"""Native PowerPoint table/chart converters for explicit SVG metadata markers."""

from __future__ import annotations

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
)
from .chart_xml import _chart_rels_xml, _chart_xml
from .chartex import (
    _chart_ex_colors_xml,
    _chart_ex_rels_xml,
    _chart_ex_style_xml,
    _chart_ex_xml,
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
    _validate_bounds_inputs,
)
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
        ctx.package_files[colors_part] = _chart_ex_colors_xml()
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
    text_sizes = _chart_text_sizes(payload)
    chart_style = _classic_chart_style(payload, elem)
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
) -> tuple[str, dict[str, Any], list[list[Any]] | None]:
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return "", {}, None
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    transform = elem.get("transform", "")
    if transform and any(token in transform for token in ("rotate", "matrix", "skew")):
        raise RuntimeError("Native PPTX table/chart markers support translate/scale transforms only")

    payload = _load_payload(elem, kind)
    _validate_bounds_inputs(elem, payload)
    table_rows = None
    if kind == "table":
        table_rows, _ = _validate_table_payload(payload)
    else:
        _chart_data(payload)
    return kind, payload, table_rows


def validate_native_object_marker(elem: ET.Element) -> None:
    """Validate a data-pptx-native marker without mutating the PPTX package."""
    _validate_native_object_marker_payload(elem)


def validate_native_object_marker_with_warnings(elem: ET.Element) -> list[str]:
    """Validate a data-pptx-native marker and return non-fatal warnings."""
    kind, _, table_rows = _validate_native_object_marker_payload(elem)
    if kind != "table" or table_rows is None:
        return []
    return _native_table_warnings(elem, table_rows)


def native_object_marker_warnings(elem: ET.Element) -> list[str]:
    """Return non-fatal warnings for a data-pptx-native marker."""
    return validate_native_object_marker_with_warnings(elem)


def convert_native_object(elem: ET.Element, ctx: ConvertContext) -> ShapeResult | None:
    """Convert a marked SVG group to a native PowerPoint table or chart."""
    kind = (elem.get("data-pptx-native") or "").strip().lower()
    if not kind:
        return None
    if kind not in _NATIVE_KINDS:
        raise RuntimeError(f"Unsupported data-pptx-native value: {kind}")
    if _local_tag(elem) != "g":
        raise RuntimeError("Native PPTX table/chart markers must be <g> elements")
    transform = elem.get("transform", "")
    if transform and any(token in transform for token in ("rotate", "matrix", "skew")):
        raise RuntimeError("Native PPTX table/chart markers support translate/scale transforms only")

    payload = _load_payload(elem, kind)
    if kind == "table":
        return _build_native_table(elem, ctx, payload)
    return _build_native_chart(elem, ctx, payload)
