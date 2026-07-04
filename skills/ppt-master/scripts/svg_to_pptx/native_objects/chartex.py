"""ChartEx native chart XML emitters."""

from __future__ import annotations

from typing import Any

from ..drawingml.utils import _xml_escape
from .marker_common import (
    CHARTEX_URI,
    CHART_COLOR_STYLE_REL_TYPE,
    CHART_STYLE_REL_TYPE,
    PACKAGE_REL_TYPE,
    _compact_key,
    _excel_col,
)


def _chart_ex_legend_xml(payload: dict[str, Any]) -> str:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    show_legend = payload.get("show_legend", style.get("show_legend", False))
    if not show_legend:
        return ""
    position_key = _compact_key(payload.get("legend_position") or style.get("legend_position") or "bottom")
    positions = {
        "bottom": "b",
        "b": "b",
        "left": "l",
        "l": "l",
        "right": "r",
        "r": "r",
        "top": "t",
        "t": "t",
    }
    position = positions.get(position_key, "b")
    return f'<cx:legend pos="{position}" align="ctr" overlay="0"/>'


def _cx_points(values: list[Any]) -> str:
    return "".join(
        f'<cx:pt idx="{idx}">{_xml_escape(str(value))}</cx:pt>'
        for idx, value in enumerate(values)
    )


def _cx_col_range(start_col: int, col_count: int, row_count: int) -> str:
    start = _excel_col(start_col)
    end = _excel_col(start_col + col_count - 1)
    return f"Sheet1!${start}$2:${end}${row_count + 1}"


def _cx_str_dim(levels: list[list[str]], *, start_col: int, row_count: int) -> str:
    levels_xml = "".join(
        f'<cx:lvl ptCount="{len(level)}">{_cx_points(level)}</cx:lvl>'
        for level in reversed(levels)
    )
    return (
        '<cx:strDim type="cat">'
        f"<cx:f>{_cx_col_range(start_col, len(levels), row_count)}</cx:f>"
        f"{levels_xml}"
        "</cx:strDim>"
    )


def _cx_num_dim(
    values: list[int | float],
    *,
    dim_type: str,
    col: int,
) -> str:
    return (
        f'<cx:numDim type="{dim_type}">'
        f"<cx:f>Sheet1!${_excel_col(col)}$2:${_excel_col(col)}${len(values) + 1}</cx:f>"
        f'<cx:lvl ptCount="{len(values)}" formatCode="General">{_cx_points(values)}</cx:lvl>'
        "</cx:numDim>"
    )


def _chart_ex_data_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        values = chart_data["values"]
        levels = chart_data["levels"]
        return (
            '<cx:data id="0">'
            f'{_cx_str_dim(levels, start_col=1, row_count=len(values))}'
            f'{_cx_num_dim(values, dim_type="size", col=len(levels) + 1)}'
            "</cx:data>"
        )
    if chart_type == "histogram":
        values = chart_data["values"]
        return f'<cx:data id="0">{_cx_num_dim(values, dim_type="val", col=1)}</cx:data>'
    if chart_type in {"funnel", "pareto", "waterfall"}:
        values = chart_data["values"]
        categories = chart_data["categories"]
        return (
            '<cx:data id="0">'
            f'{_cx_str_dim([categories], start_col=1, row_count=len(values))}'
            f'{_cx_num_dim(values, dim_type="val", col=2)}'
            "</cx:data>"
        )
    if chart_type == "box_whisker":
        parts: list[str] = []
        for idx, item in enumerate(chart_data["series"]):
            start_col = idx * 2 + 1
            parts.append(
                f'<cx:data id="{idx}">'
                f'{_cx_str_dim([item["categories"]], start_col=start_col, row_count=len(item["values"]))}'
                f'{_cx_num_dim(item["values"], dim_type="val", col=start_col + 1)}'
                "</cx:data>"
            )
        return "".join(parts)
    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _chart_ex_series_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        layout_id = chart_type
        label_pos = "ctr" if chart_type == "sunburst" else "inEnd"
        layout_pr = ""
        if chart_type == "treemap":
            parent_labels = chart_data.get("parent_labels", "overlapping")
            layout_pr = (
                "<cx:layoutPr>"
                f'<cx:parentLabelLayout val="{parent_labels}"/>'
                "</cx:layoutPr>"
            )
        return (
            f'<cx:series layoutId="{layout_id}" uniqueId="{{00000000-0000-4000-8000-000000000001}}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$A$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            f'<cx:dataLabels pos="{label_pos}"><cx:visibility seriesName="0" categoryName="1" value="1"/></cx:dataLabels>'
            '<cx:dataId val="0"/>'
            f"{layout_pr}"
            "</cx:series>"
        )
    if chart_type == "histogram":
        return (
            '<cx:series layoutId="clusteredColumn" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$A$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataId val="0"/><cx:layoutPr><cx:binning intervalClosed="r"/></cx:layoutPr>'
            "</cx:series>"
        )
    if chart_type == "pareto":
        return (
            '<cx:series layoutId="clusteredColumn" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataId val="0"/><cx:layoutPr><cx:aggregation/></cx:layoutPr>'
            '<cx:axisId val="1"/></cx:series>'
            '<cx:series layoutId="paretoLine" ownerIdx="0" uniqueId="{00000000-0000-4000-8000-000000000002}">'
            '<cx:axisId val="2"/></cx:series>'
        )
    if chart_type == "waterfall":
        subtotals_xml = ""
        if chart_data.get("subtotals"):
            subtotal_items = "".join(f'<cx:idx val="{idx}"/>' for idx in chart_data["subtotals"])
            subtotals_xml = f"<cx:subtotals>{subtotal_items}</cx:subtotals>"
        return (
            '<cx:series layoutId="waterfall" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataLabels pos="outEnd"><cx:visibility seriesName="0" categoryName="0" value="1"/></cx:dataLabels>'
            f'<cx:dataId val="0"/><cx:layoutPr>{subtotals_xml}</cx:layoutPr>'
            "</cx:series>"
        )
    if chart_type == "funnel":
        return (
            '<cx:series layoutId="funnel" uniqueId="{00000000-0000-4000-8000-000000000001}">'
            '<cx:tx><cx:txData><cx:f>Sheet1!$B$1</cx:f><cx:v>Series 1</cx:v></cx:txData></cx:tx>'
            '<cx:dataLabels><cx:visibility seriesName="0" categoryName="0" value="1"/></cx:dataLabels>'
            '<cx:dataId val="0"/></cx:series>'
        )
    if chart_type == "box_whisker":
        parts: list[str] = []
        for idx, item in enumerate(chart_data["series"]):
            value_col = _excel_col(idx * 2 + 2)
            parts.append(
                f'<cx:series layoutId="boxWhisker" uniqueId="{{00000000-0000-4000-8000-{idx + 1:012d}}}">'
                f'<cx:tx><cx:txData><cx:f>Sheet1!${value_col}$1</cx:f><cx:v>{_xml_escape(str(item["name"]))}</cx:v></cx:txData></cx:tx>'
                f'<cx:dataId val="{idx}"/><cx:layoutPr>'
                '<cx:visibility meanMarker="1" outliers="1"/>'
                '<cx:statistics quartileMethod="exclusive"/>'
                '</cx:layoutPr></cx:series>'
            )
        return "".join(parts)
    raise RuntimeError(f"Native PPTX {chart_type} chart is outside current basic chart support")


def _chart_ex_axes_xml(chart_data: dict[str, Any]) -> str:
    chart_type = chart_data["type"]
    if chart_type in {"sunburst", "treemap"}:
        return ""
    if chart_type == "pareto":
        return (
            '<cx:axis id="0"><cx:catScaling gapWidth="0"/><cx:tickLabels/></cx:axis>'
            '<cx:axis id="1"><cx:valScaling/><cx:majorGridlines/><cx:tickLabels/></cx:axis>'
            '<cx:axis id="2"><cx:valScaling max="1" min="0"/><cx:units unit="percentage"/><cx:tickLabels/></cx:axis>'
        )
    if chart_type == "funnel":
        return '<cx:axis id="1"><cx:catScaling gapWidth="0.06"/><cx:tickLabels/></cx:axis>'
    gap_width = "0.5" if chart_type == "waterfall" else "0"
    if chart_type == "box_whisker":
        gap_width = "1"
    return (
        f'<cx:axis id="0"><cx:catScaling gapWidth="{gap_width}"/><cx:tickLabels/></cx:axis>'
        '<cx:axis id="1"><cx:valScaling/><cx:majorGridlines/><cx:tickLabels/></cx:axis>'
    )


def _chart_ex_xml(
    payload: dict[str, Any],
    chart_data: dict[str, Any],
    *,
    chart_rels_id: str,
) -> bytes:
    data_xml = _chart_ex_data_xml(chart_data)
    series_xml = _chart_ex_series_xml(chart_data)
    axes_xml = _chart_ex_axes_xml(chart_data)
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cx:chartSpace xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
               xmlns:cx="{CHARTEX_URI}">
<cx:chartData><cx:externalData r:id="{chart_rels_id}" cx:autoUpdate="0"/>{data_xml}</cx:chartData>
<cx:chart><cx:title pos="t" align="ctr" overlay="0"/>
<cx:plotArea><cx:plotAreaRegion>{series_xml}</cx:plotAreaRegion>{axes_xml}</cx:plotArea>
{_chart_ex_legend_xml(payload)}</cx:chart>
</cx:chartSpace>'''
    return xml.encode("utf-8")


def _chart_ex_rels_xml(workbook_target: str, style_target: str, colors_target: str) -> bytes:
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="{PACKAGE_REL_TYPE}" Target="{_xml_escape(workbook_target)}"/>
<Relationship Id="rId2" Type="{CHART_STYLE_REL_TYPE}" Target="{_xml_escape(style_target)}"/>
<Relationship Id="rId3" Type="{CHART_COLOR_STYLE_REL_TYPE}" Target="{_xml_escape(colors_target)}"/>
</Relationships>'''
    return xml.encode("utf-8")


def _chart_ex_style_xml() -> bytes:
    return b'''<cs:chartStyle xmlns:cs="http://schemas.microsoft.com/office/drawing/2012/chartStyle" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" id="410"><cs:axisTitle><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="bg1"><a:lumMod val="65000"/></a:schemeClr></a:solidFill><a:ln w="19050"><a:solidFill><a:schemeClr val="bg1"/></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:axisTitle><cs:categoryAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:categoryAxis><cs:chartArea mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="bg1"/></a:solidFill><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1330"/></cs:chartArea><cs:dataLabel><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="lt1"/></cs:fontRef><cs:defRPr sz="1197"/></cs:dataLabel><cs:dataLabelCallout><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="lt1"/></a:solidFill><a:ln><a:solidFill><a:schemeClr val="dk1"><a:lumMod val="25000"/><a:lumOff val="75000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/><cs:bodyPr rot="0" spcFirstLastPara="1" vertOverflow="clip" horzOverflow="clip" vert="horz" wrap="square" lIns="36576" tIns="18288" rIns="36576" bIns="18288" anchor="ctr" anchorCtr="1"><a:spAutoFit/></cs:bodyPr></cs:dataLabelCallout><cs:dataPoint><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:ln w="19050"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></cs:spPr></cs:dataPoint><cs:dataPoint3D><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></cs:spPr></cs:dataPoint3D><cs:dataPointLine><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="28575" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:dataPointLine><cs:dataPointMarker><cs:lnRef idx="0"/><cs:fillRef idx="0"><cs:styleClr val="auto"/></cs:fillRef><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></cs:spPr></cs:dataPointMarker><cs:dataPointMarkerLayout symbol="circle" size="5"/><cs:dataPointWireframe><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="28575" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:dataPointWireframe><cs:dataTable><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:dataTable><cs:downBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="dk1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr></cs:downBar><cs:dropLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="35000"/><a:lumOff val="65000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:dropLine><cs:errorBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:errorBar><cs:floor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:floor><cs:gridlineMajor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:gridlineMajor><cs:gridlineMinor><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:gridlineMinor><cs:hiLoLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="75000"/><a:lumOff val="25000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:hiLoLine><cs:leaderLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="35000"/><a:lumOff val="65000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr></cs:leaderLine><cs:legend><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:legend><cs:plotArea mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:plotArea><cs:plotArea3D mods="allowNoFillOverride allowNoLineOverride"><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:plotArea3D><cs:seriesAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill><a:round/></a:ln></cs:spPr><cs:defRPr sz="1197"/></cs:seriesAxis><cs:seriesLine><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="9525" cap="flat"><a:solidFill><a:srgbClr val="D9D9D9"/></a:solidFill><a:round/></a:ln></cs:spPr></cs:seriesLine><cs:title><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1862"/></cs:title><cs:trendline><cs:lnRef idx="0"><cs:styleClr val="auto"/></cs:lnRef><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef><cs:spPr><a:ln w="19050" cap="rnd"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="sysDash"/></a:ln></cs:spPr></cs:trendline><cs:trendlineLabel><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:trendlineLabel><cs:upBar><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="dk1"/></cs:fontRef><cs:spPr><a:solidFill><a:schemeClr val="lt1"/></a:solidFill><a:ln w="9525"><a:solidFill><a:schemeClr val="tx1"><a:lumMod val="15000"/><a:lumOff val="85000"/></a:schemeClr></a:solidFill></a:ln></cs:spPr></cs:upBar><cs:valueAxis><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"><a:lumMod val="65000"/><a:lumOff val="35000"/></a:schemeClr></cs:fontRef><cs:defRPr sz="1197"/></cs:valueAxis><cs:wall><cs:lnRef idx="0"/><cs:fillRef idx="0"/><cs:effectRef idx="0"/><cs:fontRef idx="minor"><a:schemeClr val="tx1"/></cs:fontRef></cs:wall></cs:chartStyle>'''


def _chart_ex_colors_xml() -> bytes:
    return b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cs:colorStyle xmlns:cs="http://schemas.microsoft.com/office/drawing/2012/chartStyle"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               meth="cycle" id="10">
<a:schemeClr val="accent1"/><a:schemeClr val="accent2"/><a:schemeClr val="accent3"/>
<a:schemeClr val="accent4"/><a:schemeClr val="accent5"/><a:schemeClr val="accent6"/>
</cs:colorStyle>'''
