"""Native chart styling and companion text helpers."""

from __future__ import annotations

import math
from typing import Any
from xml.etree import ElementTree as ET

from .marker_attributes import native_import_source

from ..drawingml.context import ConvertContext
from ..drawingml.utils import detect_text_lang, parse_font_family, px_to_emu, _xml_escape
from .chart_data import _DEFAULT_CHART_COLORS
from .marker_common import (
    _bool_attr,
    _bounds,
    _chart_bool,
    _clean_hex,
    _compact_key,
    _fallback_fill_candidates,
    _fallback_stroke_colors,
    _fallback_text_colors,
    _first_present,
    _font_size_hpt,
    _hex_or_none,
    _inferred_chart_background,
    _local_tag,
    _maybe_number,
    _most_common_color,
    _number,
    _normalized_fallback_text,
    _powerpoint_emu,
    _powerpoint_emu_value,
    _relative_luminance,
    _style_attr,
    _visible_fallback_texts,
)


def _chart_style_value(payload: dict[str, Any], *keys: str) -> Any:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    for source in (payload, style):
        for key in keys:
            if source.get(key) is not None:
                return source.get(key)
    return None


def _chart_style_color(
    payload: dict[str, Any],
    keys: tuple[str, ...],
    default: str | None,
) -> str | None:
    raw = _chart_style_value(payload, *keys)
    if raw is None:
        return default
    if str(raw).strip().lower() in {"none", "transparent"}:
        return None
    return _hex_or_none(raw) or default


def _fallback_text_attr_values(
    elem: ET.Element,
    attr: str,
    inherited_value: str | None = None,
) -> list[str]:
    tag = _local_tag(elem)
    if tag == "metadata" or tag in {"defs", "clipPath", "mask", "filter", "style"}:
        return []
    if elem.get("display") == "none" or elem.get("visibility") == "hidden":
        return []

    own_value = _style_attr(elem, attr)
    next_value = own_value if own_value is not None else inherited_value
    values: list[str] = []
    if tag in {"text", "tspan"} and next_value:
        values.append(str(next_value).strip())
    for child in elem:
        values.extend(_fallback_text_attr_values(child, attr, next_value))
    return values


def _most_common_value(values: list[str]) -> str | None:
    if not values:
        return None
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def _most_common_font_size(values: list[str]) -> str | None:
    if not values:
        return None
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    max_count = max(counts.values())
    candidates = [value for value, count in counts.items() if count == max_count]
    numeric_candidates = [
        (float(value), value)
        for value in candidates
        if _maybe_number(value) is not None
    ]
    if numeric_candidates:
        return min(numeric_candidates, key=lambda item: item[0])[1]
    return candidates[0]


def _classic_chart_style(
    payload: dict[str, Any],
    elem: ET.Element,
    inherited_styles: dict[str, str] | None = None,
) -> dict[str, str | None]:
    inherited_styles = inherited_styles or {}
    fallback_background = _inferred_chart_background(elem)
    text_color = _most_common_color(
        _fallback_text_colors(elem, inherited_styles.get("fill"))
    ) or "404040"
    stroke_colors = _fallback_stroke_colors(elem, inherited_styles.get("stroke"))
    darkest_stroke = min(stroke_colors, key=_relative_luminance) if stroke_colors else None
    lightest_stroke = max(stroke_colors, key=_relative_luminance) if stroke_colors else None
    raw_font_face = _chart_style_value(payload, "font_family", "fontFamily", "font_face", "fontFace")
    fallback_font_face = _most_common_value(
        _fallback_text_attr_values(
            elem,
            "font-family",
            inherited_styles.get("font-family"),
        )
    )
    font_face = str(raw_font_face).strip() if raw_font_face is not None else fallback_font_face
    axis_color = darkest_stroke or text_color
    grid_color = (
        lightest_stroke
        if lightest_stroke and _relative_luminance(lightest_stroke) > _relative_luminance(axis_color)
        else "D9DED8"
    )
    chart_fill = _chart_style_color(
        payload,
        (
            "chart_area_fill",
            "chartAreaFill",
            "chart_fill",
            "chartFill",
            "background",
            "background_color",
            "backgroundColor",
            "fill",
        ),
        fallback_background,
    )
    return {
        "axis_color": _chart_style_color(
            payload,
            ("axis_color", "axisColor", "axis_line_color", "axisLineColor"),
            axis_color,
        ),
        "chart_fill": chart_fill,
        "grid_color": _chart_style_color(
            payload,
            ("grid_color", "gridColor", "gridline_color", "gridlineColor"),
            grid_color,
        ),
        "plot_fill": _chart_style_color(
            payload,
            ("plot_area_fill", "plotAreaFill", "plot_background", "plotBackground"),
            None,
        ),
        "text_color": _chart_style_color(
            payload,
            ("text_color", "textColor", "label_color", "labelColor", "font_color", "fontColor"),
            text_color,
        ),
        "font_face": font_face or None,
    }


def _chart_text_sizes(
    payload: dict[str, Any],
    elem: ET.Element | None = None,
    inherited_styles: dict[str, str] | None = None,
) -> dict[str, int]:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    inherited_styles = inherited_styles or {}
    fallback_font_size = (
        _most_common_font_size(
            _fallback_text_attr_values(
                elem,
                "font-size",
                inherited_styles.get("font-size"),
            )
        )
        if elem is not None else None
    )
    base_raw = _first_present(
        payload.get("font_size"),
        payload.get("chart_font_size"),
        payload.get("chartFontSize"),
        style.get("font_size"),
        style.get("chart_font_size"),
        style.get("chartFontSize"),
        fallback_font_size,
    )
    axis_raw = _first_present(
        payload.get("axis_font_size"),
        payload.get("axisFontSize"),
        payload.get("tick_font_size"),
        payload.get("tickFontSize"),
        style.get("axis_font_size"),
        style.get("axisFontSize"),
        style.get("tick_font_size"),
        style.get("tickFontSize"),
        base_raw,
    )
    axis_title_raw = _first_present(
        payload.get("axis_title_font_size"),
        payload.get("axisTitleFontSize"),
        style.get("axis_title_font_size"),
        style.get("axisTitleFontSize"),
        axis_raw,
    )
    legend_raw = _first_present(
        payload.get("legend_font_size"),
        payload.get("legendFontSize"),
        style.get("legend_font_size"),
        style.get("legendFontSize"),
        axis_raw,
    )
    title_raw = _first_present(
        payload.get("title_font_size"),
        payload.get("titleFontSize"),
        style.get("title_font_size"),
        style.get("titleFontSize"),
    )
    subtitle_raw = _first_present(
        payload.get("subtitle_font_size"),
        payload.get("subtitleFontSize"),
        style.get("subtitle_font_size"),
        style.get("subtitleFontSize"),
        base_raw,
    )
    note_raw = _first_present(
        payload.get("note_font_size"),
        payload.get("noteFontSize"),
        style.get("note_font_size"),
        style.get("noteFontSize"),
        style.get("caption_font_size"),
        style.get("captionFontSize"),
        base_raw,
    )
    return {
        "axis": _font_size_hpt(axis_raw, 12),
        "axis_title": _font_size_hpt(axis_title_raw, 12),
        "base": _font_size_hpt(base_raw, 12),
        "legend": _font_size_hpt(legend_raw, 12),
        "note": _font_size_hpt(note_raw, 12),
        "subtitle": _font_size_hpt(subtitle_raw, 12),
        "title": _font_size_hpt(title_raw, 16),
    }


def _solid_fill_xml(color: str | None) -> str:
    if not color:
        return "<a:noFill/>"
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def _chart_area_sp_pr_xml(fill_color: str | None) -> str:
    return f"<c:spPr>{_solid_fill_xml(fill_color)}<a:ln><a:noFill/></a:ln></c:spPr>"


def _chart_line_sp_pr_xml(color: str | None, *, width: int = 9525) -> str:
    if not color:
        line_xml = "<a:ln><a:noFill/></a:ln>"
    else:
        line_xml = (
            f'<a:ln w="{width}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            "<a:round/></a:ln>"
        )
    return f"<c:spPr>{line_xml}</c:spPr>"


def _major_gridlines_xml(color: str | None) -> str:
    return f'<c:majorGridlines>{_chart_line_sp_pr_xml(color, width=6350)}</c:majorGridlines>'


def _font_face_xml(font_face: str | None) -> str:
    if not font_face:
        return ""
    fonts = parse_font_family(font_face)
    latin_font = _xml_escape(fonts["latin"])
    ea_font = _xml_escape(fonts["ea"])
    return f'<a:latin typeface="{latin_font}"/><a:ea typeface="{ea_font}"/>'


def _chart_tx_pr_xml(
    font_size: int,
    color: str | None = None,
    *,
    bold: bool = False,
    font_face: str | None = None,
) -> str:
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    bold_attr = ' b="1"' if bold else ""
    return (
        "<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr>"
        f'<a:defRPr sz="{font_size}"{bold_attr}>{fill_xml}{_font_face_xml(font_face)}</a:defRPr>'
        '</a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>'
    )


def _chart_text_entry(value: Any) -> tuple[str, dict[str, Any]] | None:
    if isinstance(value, dict):
        text = _first_present(value.get("text"), value.get("value"), value.get("content"))
        if text is None or not str(text).strip():
            return None
        return str(text).strip(), value
    if value is None or not str(value).strip():
        return None
    return str(value).strip(), {}


def _chart_text_entry_font_size(item: dict[str, Any], fallback: int) -> int:
    raw = _first_present(item.get("font_size"), item.get("fontSize"))
    if raw is None:
        return fallback
    return _font_size_hpt(raw, 12)


def _chart_text_entry_color(item: dict[str, Any], fallback: str | None) -> str | None:
    return _hex_or_none(_first_present(
        item.get("color"),
        item.get("font_color"),
        item.get("fontColor"),
    )) or fallback


def _chart_text_entry_font_face(item: dict[str, Any], fallback: str | None) -> str | None:
    raw = _first_present(
        item.get("font_family"),
        item.get("fontFamily"),
        item.get("font_face"),
        item.get("fontFace"),
    )
    if raw is None:
        return fallback
    font_face = str(raw).strip()
    return font_face or fallback


def _alpha_xml(value: Any, field_name: str = "fill_opacity") -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        raise RuntimeError(f"Native PPTX chart {field_name} must be numeric")
    try:
        alpha = float(value)
    except (TypeError, ValueError, OverflowError):
        raise RuntimeError(f"Native PPTX chart {field_name} must be numeric") from None
    if not math.isfinite(alpha):
        raise RuntimeError(f"Native PPTX chart {field_name} must be finite")
    if alpha < 0 or alpha > 1:
        raise RuntimeError(f"Native PPTX chart {field_name} must be between 0 and 1")
    return f'<a:alpha val="{int(round(alpha * 100000))}"/>'


def _axis_title_xml(
    title: Any,
    *,
    font_size: int,
    color: str | None = None,
    font_face: str | None = None,
) -> str:
    entry = _chart_text_entry(title)
    if entry is None:
        return ""
    text, item = entry
    text_color = _chart_text_entry_color(item, color)
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{text_color}"/></a:solidFill>'
        if text_color else ""
    )
    lang = detect_text_lang(text)
    return (
        "<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:r><a:rPr lang="{lang}" sz="{_chart_text_entry_font_size(item, font_size)}">'
        f"{fill_xml}{_font_face_xml(_chart_text_entry_font_face(item, font_face))}</a:rPr>"
        f"<a:t>{_xml_escape(text)}</a:t></a:r></a:p>"
        "</c:rich></c:tx><c:layout/><c:overlay val=\"0\"/></c:title>"
    )


_AXIS_TITLE_KEY_GROUPS = {
    "category": (
        ("category",),
        ("category_axis_title", "categoryAxisTitle"),
    ),
    "value": (
        ("value",),
        ("value_axis_title", "valueAxisTitle"),
    ),
    "x": (
        ("x",),
        ("x_axis_title", "xAxisTitle"),
    ),
    "y": (
        ("y",),
        ("y_axis_title", "yAxisTitle"),
    ),
    "secondary_value": (
        ("secondary_value", "secondaryValue"),
        ("secondary_value_axis_title", "secondaryValueAxisTitle"),
    ),
}


def _axis_titles(payload: dict[str, Any]) -> dict[str, Any]:
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    raw = payload.get("axis_titles", payload.get("axisTitles"))
    style_raw = style.get("axis_titles", style.get("axisTitles"))
    axis_map = raw if isinstance(raw, dict) else {}
    style_axis_map = style_raw if isinstance(style_raw, dict) else {}

    def pick(axis_keys: tuple[str, ...], root_keys: tuple[str, ...]) -> Any:
        values: list[Any] = []
        for key in root_keys:
            values.extend((
                payload.get(key),
                style.get(key),
            ))
        for key in axis_keys + root_keys:
            values.extend((
                axis_map.get(key),
                style_axis_map.get(key),
            ))
        return _first_present(*values)

    return {
        field_name: pick(axis_keys, root_keys)
        for field_name, (axis_keys, root_keys) in _AXIS_TITLE_KEY_GROUPS.items()
    }


def _metadata_text(value: Any) -> str | None:
    entry = _chart_text_entry(value)
    if entry is None:
        return None
    text, _ = entry
    return _normalized_fallback_text(text)


def _native_chart_chrome_errors(elem: ET.Element, payload: dict[str, Any]) -> list[str]:
    fallback_texts = set(_visible_fallback_texts(elem))
    missing: list[str] = []

    for field_name in ("title", "subtitle"):
        text = _metadata_text(payload.get(field_name))
        if text and text not in fallback_texts:
            missing.append(f"{field_name}={text!r}")

    for field_name, value in _axis_titles(payload).items():
        text = _metadata_text(value)
        if text and text not in fallback_texts:
            missing.append(f"axis_titles.{field_name}={text!r}")

    if not missing:
        return []

    sample = ", ".join(missing[:5])
    suffix = "" if len(missing) <= 5 else f", and {len(missing) - 5} more"
    return [
        "Native PPTX chart metadata contains title/axis text that is not visible "
        "inside the fallback marker and would appear only after "
        f"--native-charts-and-tables: {sample}{suffix}. "
        "Use `name` for object naming, or draw the same text in the chart fallback."
    ]


def _native_chart_export_payload(
    elem: ET.Element,
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    if native_import_source(elem) == "pptx":
        return payload, []
    fallback_texts = set(_visible_fallback_texts(elem))
    output = payload
    messages: list[str] = []

    def mutable_payload() -> dict[str, Any]:
        nonlocal output
        if output is payload:
            output = dict(payload)
        return output

    def mutable_style(target: dict[str, Any]) -> dict[str, Any] | None:
        style = target.get("style")
        if not isinstance(style, dict):
            return None
        if target.get("style") is payload.get("style"):
            style = dict(style)
            target["style"] = style
        return style

    def drop_map_keys(source: dict[str, Any], map_key: str, keys: tuple[str, ...]) -> None:
        raw_map = source.get(map_key)
        if not isinstance(raw_map, dict):
            return
        next_map = dict(raw_map)
        for key in keys:
            next_map.pop(key, None)
        if next_map:
            source[map_key] = next_map
        else:
            source.pop(map_key, None)

    for key in ("title", "subtitle"):
        text = _metadata_text(payload.get(key))
        if text and text not in fallback_texts:
            mutable_payload().pop(key, None)
            messages.append(
                f"omitted native chart {key} {text!r} because it is not visible in the fallback"
            )

    for field_name, value in _axis_titles(payload).items():
        text = _metadata_text(value)
        if not text or text in fallback_texts:
            continue
        axis_keys, root_keys = _AXIS_TITLE_KEY_GROUPS[field_name]
        target = mutable_payload()
        for key in root_keys:
            target.pop(key, None)
        for map_key in ("axis_titles", "axisTitles"):
            drop_map_keys(target, map_key, axis_keys + root_keys)
        style = mutable_style(target)
        if style is not None:
            for key in root_keys:
                style.pop(key, None)
            for map_key in ("axis_titles", "axisTitles"):
                drop_map_keys(style, map_key, axis_keys + root_keys)
        messages.append(
            f"omitted native chart axis_titles.{field_name} {text!r} "
            "because it is not visible in the fallback"
        )

    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    show_legend = payload.get("show_legend", style.get("show_legend", False))
    if show_legend:
        legend_texts = _legend_candidate_texts(payload)
        if legend_texts and not any(text in fallback_texts for text in legend_texts):
            mutable_payload()["show_legend"] = False
            messages.append(
                "omitted native chart legend because show_legend=true has no "
                "visible fallback legend text"
            )

    return output, messages


def _legend_candidate_texts(payload: dict[str, Any]) -> list[str]:
    series_values: list[str] = []
    category_values: list[str] = []
    categories = payload.get("categories")
    if isinstance(categories, list):
        category_values.extend(str(item) for item in categories if str(item).strip())
    series = payload.get("series")
    if isinstance(series, list):
        for item in series:
            if isinstance(item, dict) and item.get("name") is not None:
                series_values.append(str(item.get("name")))
    plots = payload.get("plots")
    if isinstance(plots, list):
        for plot in plots:
            if not isinstance(plot, dict):
                continue
            plot_series = plot.get("series")
            if not isinstance(plot_series, list):
                continue
            for item in plot_series:
                if isinstance(item, dict) and item.get("name") is not None:
                    series_values.append(str(item.get("name")))
    chart_type = _compact_key(payload.get("type") or payload.get("chart_type") or "")
    category_legend_types = {"pie", "doughnut", "donut", "ofpie", "pieofpie", "barofpie"}
    values = category_values if chart_type in category_legend_types else series_values
    normalized: list[str] = []
    for value in values:
        text = _normalized_fallback_text(value)
        if text:
            normalized.append(text)
    return normalized


def _native_chart_chrome_warnings(elem: ET.Element, payload: dict[str, Any]) -> list[str]:
    fallback_texts = set(_visible_fallback_texts(elem))
    warnings: list[str] = []
    style = payload.get("style") if isinstance(payload.get("style"), dict) else {}
    show_legend = payload.get("show_legend", style.get("show_legend", False))
    if show_legend:
        legend_texts = _legend_candidate_texts(payload)
        if legend_texts and not any(text in fallback_texts for text in legend_texts):
            warnings.append(
                "Native PPTX chart has show_legend=true, but no series/category "
                "legend text is visible inside the fallback marker. Add the "
                "fallback legend or remove show_legend."
            )

    companion_entries = _chart_companion_entries(
        payload,
        include_title=False,
        include_subtitle_as_caption=False,
    )
    missing_companion: list[str] = []
    for item in companion_entries:
        text = _normalized_fallback_text(item.get("text"))
        if text and text not in fallback_texts:
            missing_companion.append(text)
    if missing_companion:
        sample = ", ".join(repr(text) for text in missing_companion[:5])
        suffix = "" if len(missing_companion) <= 5 else f", and {len(missing_companion) - 5} more"
        warnings.append(
            "Native PPTX chart companion text is not visible inside the fallback "
            "marker and may appear only after --native-charts-and-tables: "
            f"{sample}{suffix}. "
            "Keep companion metadata aligned with visible chart annotations."
        )
    return warnings


def _text_box_xml(
    ctx: ConvertContext,
    *,
    text: str,
    role: str,
    off_x: int,
    off_y: int,
    ext_cx: int,
    ext_cy: int,
    font_size: int,
    color: str | None,
    align: str = "l",
    bold: bool = False,
    font_face: str | None = None,
) -> str:
    shape_id = ctx.next_id()
    align_key = _compact_key(align)
    algn = {
        "center": "ctr",
        "centre": "ctr",
        "ctr": "ctr",
        "middle": "ctr",
        "right": "r",
        "r": "r",
        "left": "l",
        "l": "l",
    }.get(align_key, "l")
    fill_xml = (
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        if color else ""
    )
    bold_attr = ' b="1"' if bold else ""
    lang = detect_text_lang(text)
    name = _xml_escape(f"Chart {role.title()} {shape_id}")
    return f'''<p:sp>
<p:nvSpPr>
<p:cNvPr id="{shape_id}" name="{name}"/>
<p:cNvSpPr txBox="1"/><p:nvPr/>
</p:nvSpPr>
<p:spPr>
<a:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{ext_cx}" cy="{ext_cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
<a:noFill/>
<a:ln><a:noFill/></a:ln>
</p:spPr>
<p:txBody>
<a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" anchorCtr="0"/>
<a:lstStyle/>
<a:p><a:pPr algn="{algn}"/>
<a:r><a:rPr lang="{lang}" sz="{font_size}"{bold_attr}>{fill_xml}{_font_face_xml(font_face)}</a:rPr><a:t>{_xml_escape(text)}</a:t></a:r>
</a:p>
</p:txBody>
</p:sp>'''


def _chart_companion_entries(
    payload: dict[str, Any],
    *,
    include_title: bool,
    include_subtitle_as_caption: bool,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def add(role: str, value: Any) -> None:
        if value is None:
            return
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict):
                text = _first_present(item.get("text"), item.get("value"), item.get("content"))
                if text:
                    entries.append({"role": role, **item, "text": str(text)})
            elif str(item).strip():
                entries.append({"role": role, "text": str(item)})

    if include_title:
        add("title", payload.get("title"))
    caption_value = payload.get("caption")
    if caption_value is None and include_subtitle_as_caption:
        caption_value = payload.get("subtitle")
    add("caption", caption_value)
    add("source", payload.get("source"))
    for key in ("note", "notes", "footnote", "footnotes"):
        add("note", payload.get(key))
    return entries


def _chart_companion_box(item: dict[str, Any]) -> tuple[int, int, int, int] | None:
    """Validate and resolve an optional explicit companion text box."""
    box_keys = ("x", "y", "width", "height")
    provided_box_keys = [key for key in box_keys if key in item]
    if provided_box_keys and len(provided_box_keys) != len(box_keys):
        raise RuntimeError(
            "Native PPTX chart companion text boxes require x/y/width/height together"
        )
    if not provided_box_keys:
        return None
    return (
        _powerpoint_emu(item["x"], "companion text x"),
        _powerpoint_emu(item["y"], "companion text y"),
        _powerpoint_emu(item["width"], "companion text width", positive=True),
        _powerpoint_emu(item["height"], "companion text height", positive=True),
    )


def _validate_chart_companion_boxes(
    payload: dict[str, Any],
    *,
    chart_bounds: tuple[int, int, int, int],
    include_title: bool,
    include_subtitle_as_caption: bool,
) -> None:
    """Validate companion boxes without allocating shapes or relationships."""
    _, chart_off_y, _, chart_ext_cy = chart_bounds
    below_index = 0
    for item in _chart_companion_entries(
        payload,
        include_title=include_title,
        include_subtitle_as_caption=include_subtitle_as_caption,
    ):
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        if _chart_companion_box(item) is not None:
            continue
        if str(item.get("role") or "note") != "title":
            _powerpoint_emu_value(
                chart_off_y + chart_ext_cy + px_to_emu(4 + below_index * 18),
                "companion text y",
            )
            below_index += 1


def _chart_companion_text_xml(
    ctx: ConvertContext,
    payload: dict[str, Any],
    *,
    chart_bounds: tuple[int, int, int, int],
    chart_style: dict[str, str | None],
    note_font_size: int,
    title_font_size: int,
    include_title: bool,
    include_subtitle_as_caption: bool,
) -> str:
    entries = _chart_companion_entries(
        payload,
        include_title=include_title,
        include_subtitle_as_caption=include_subtitle_as_caption,
    )
    if not entries:
        return ""

    chart_off_x, chart_off_y, chart_ext_cx, chart_ext_cy = chart_bounds
    parts: list[str] = []
    below_index = 0
    for item in entries:
        role = str(item.get("role") or "note")
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        font_size = _font_size_hpt(item.get("font_size", item.get("fontSize")), 16 if role == "title" else 12)
        if role == "title" and item.get("font_size") is None and item.get("fontSize") is None:
            font_size = title_font_size
        elif item.get("font_size") is None and item.get("fontSize") is None:
            font_size = note_font_size

        color = _hex_or_none(item.get("color")) or chart_style.get("text_color")
        font_face = _chart_text_entry_font_face(item, chart_style.get("font_face"))
        align = str(item.get("align") or ("ctr" if role == "title" else "l"))
        bold = bool(item.get("bold", role == "title"))
        explicit_box = _chart_companion_box(item)
        if explicit_box is not None:
            off_x, off_y, ext_cx, ext_cy = explicit_box
        elif role == "title":
            off_x = chart_off_x
            off_y = chart_off_y
            ext_cx = chart_ext_cx
            ext_cy = px_to_emu(28)
        else:
            off_x = chart_off_x
            off_y = _powerpoint_emu_value(
                chart_off_y + chart_ext_cy + px_to_emu(4 + below_index * 18),
                "companion text y",
            )
            ext_cx = chart_ext_cx
            ext_cy = px_to_emu(16)
            below_index += 1
        parts.append(_text_box_xml(
            ctx,
            text=text,
            role=role,
            off_x=off_x,
            off_y=off_y,
            ext_cx=ext_cx,
            ext_cy=ext_cy,
            font_size=font_size,
            color=color,
            align=align,
            bold=bold,
            font_face=font_face,
        ))
    return "".join(parts)
