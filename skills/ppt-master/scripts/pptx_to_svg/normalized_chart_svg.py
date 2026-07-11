"""Deterministic normalized SVG fallback for parsed classic charts.

The renderer is intentionally independent from the native-chart OOXML
emitter.  It visualizes only data and semantics that ``chart_to_svg`` has
already accepted, so a rendering failure can never invalidate an otherwise
valid editable-chart payload.
"""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


_DEFAULT_COLORS = (
    "#4472C4",
    "#ED7D31",
    "#A5A5A5",
    "#FFC000",
    "#5B9BD5",
    "#70AD47",
    "#264478",
    "#9E480E",
)


@dataclass(frozen=True)
class SeriesVisualStyle:
    """Resolved paint used only by the normalized SVG fallback."""

    fill: str | None
    fill_opacity: float = 1.0
    stroke: str | None = None
    stroke_opacity: float = 1.0
    stroke_width: float = 1.5
    line_cap: str = "round"
    marker_fill: str | None = None
    marker_fill_opacity: float = 1.0
    marker_stroke: str | None = None
    marker_stroke_opacity: float = 1.0
    marker_stroke_width: float = 1.0
    marker_size: float = 5.0


@dataclass(frozen=True)
class _Rect:
    x: float
    y: float
    w: float
    h: float


def render_normalized_chart_svg(
    payload: dict[str, Any],
    styles: list[SeriesVisualStyle],
) -> str | None:
    """Render a readable normalized fallback for supported classic charts."""
    chart_type = str(payload.get("type") or "")
    if chart_type not in {
        "area", "bar", "column", "doughnut", "line", "pie",
        "scatter", "bubble",
    }:
        return None

    try:
        bounds = _Rect(
            float(payload["x"]),
            float(payload["y"]),
            float(payload["width"]),
            float(payload["height"]),
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if (
        bounds.w <= 0
        or bounds.h <= 0
        or not all(math.isfinite(value) for value in vars(bounds).values())
    ):
        return None

    legend_entries = _legend_entries(payload, styles)
    content, legend_rect, title_parts = _outer_layout(
        payload,
        bounds,
        len(legend_entries),
    )
    parts = [*title_parts]
    if chart_type in {"pie", "doughnut"}:
        parts.extend(_render_pie(payload, styles, content, chart_type == "doughnut"))
    elif chart_type in {"scatter", "bubble"}:
        parts.extend(_render_xy(payload, styles, content, chart_type))
    else:
        parts.extend(_render_category(payload, styles, content, chart_type))
    if legend_rect is not None:
        parts.extend(
            _render_legend(
                legend_entries,
                legend_rect,
                str(payload.get("legend_position") or "b"),
            )
        )
    return "\n".join(part for part in parts if part)


def _outer_layout(
    payload: dict[str, Any],
    bounds: _Rect,
    legend_count: int,
) -> tuple[_Rect, _Rect | None, list[str]]:
    pad = max(4.0, min(bounds.w, bounds.h) * 0.018)
    content = _Rect(
        bounds.x + pad,
        bounds.y + pad,
        max(1.0, bounds.w - 2 * pad),
        max(1.0, bounds.h - 2 * pad),
    )
    title_parts: list[str] = []
    title = _entry_text(payload.get("title"))
    subtitle = _entry_text(payload.get("subtitle"))
    if title:
        title_size = _font_size(
            _entry_value(payload.get("title"), "font_size"),
            min(18.0, max(10.0, bounds.h * 0.055)),
            bounds,
        )
        title_y = content.y + title_size
        title_parts.append(
            _text(
                content.x + content.w / 2,
                title_y,
                title,
                size=title_size,
                anchor="middle",
                weight="600",
                fill=_entry_color(payload.get("title"), "#333333"),
            )
        )
        used = title_size + max(4.0, title_size * 0.35)
        content = _Rect(content.x, content.y + used, content.w, max(1.0, content.h - used))
    if subtitle:
        subtitle_size = _font_size(
            _entry_value(payload.get("subtitle"), "font_size"),
            min(12.0, max(8.0, bounds.h * 0.035)),
            bounds,
        )
        title_parts.append(
            _text(
                content.x + content.w / 2,
                content.y + subtitle_size,
                subtitle,
                size=subtitle_size,
                anchor="middle",
                fill=_entry_color(payload.get("subtitle"), "#666666"),
            )
        )
        used = subtitle_size + max(3.0, subtitle_size * 0.3)
        content = _Rect(content.x, content.y + used, content.w, max(1.0, content.h - used))

    if not payload.get("show_legend") or legend_count <= 0:
        return content, None, title_parts
    position = str(payload.get("legend_position") or "b").lower()
    if position in {"l", "r", "left", "right"}:
        legend_w = min(max(86.0, content.w * 0.24), max(1.0, content.w * 0.38))
        if position in {"l", "left"}:
            legend = _Rect(content.x, content.y, legend_w, content.h)
            content = _Rect(
                content.x + legend_w,
                content.y,
                max(1.0, content.w - legend_w),
                content.h,
            )
        else:
            legend = _Rect(content.x + content.w - legend_w, content.y, legend_w, content.h)
            content = _Rect(content.x, content.y, max(1.0, content.w - legend_w), content.h)
        return content, legend, title_parts

    columns = max(1, min(4, int(content.w // 130) or 1))
    rows = math.ceil(legend_count / columns)
    legend_h = min(content.h * 0.32, max(20.0, rows * 17.0 + 4.0))
    if position in {"t", "top"}:
        legend = _Rect(content.x, content.y, content.w, legend_h)
        content = _Rect(
            content.x,
            content.y + legend_h,
            content.w,
            max(1.0, content.h - legend_h),
        )
    else:
        legend = _Rect(content.x, content.y + content.h - legend_h, content.w, legend_h)
        content = _Rect(content.x, content.y, content.w, max(1.0, content.h - legend_h))
    return content, legend, title_parts


def _render_category(
    payload: dict[str, Any],
    styles: list[SeriesVisualStyle],
    content: _Rect,
    chart_type: str,
) -> list[str]:
    categories = _category_labels(payload)
    series = payload.get("series") or []
    if categories is None or not categories or not series:
        return []
    styles = _complete_styles(styles, len(series))
    axis_titles = payload.get("axis_titles") if isinstance(payload.get("axis_titles"), dict) else {}
    is_bar = chart_type == "bar"
    label_size = max(6.0, min(11.0, content.h * 0.037, content.w * 0.021))
    left = max(34.0, content.w * 0.075)
    bottom = max(25.0, content.h * 0.105)
    if is_bar:
        left = min(content.w * 0.34, max(66.0, content.w * 0.18))
        bottom = max(24.0, content.h * 0.085)
    if axis_titles.get("value"):
        left += 14.0 if not is_bar else 0.0
        bottom += 14.0 if is_bar else 0.0
    if axis_titles.get("category"):
        bottom += 14.0 if not is_bar else 0.0
        left += 14.0 if is_bar else 0.0
    plot = _Rect(
        content.x + left,
        content.y + 5.0,
        max(12.0, content.w - left - 10.0),
        max(12.0, content.h - bottom - 8.0),
    )

    grouping = str(payload.get("grouping") or ("clustered" if chart_type in {"bar", "column"} else "standard"))
    segments, percent = _category_segments(series, len(categories), grouping)
    scale_values = [value for row in segments for pair in row for value in pair]
    lo, hi, ticks = _nice_scale(scale_values, include_zero=True, percent=percent)
    parts: list[str] = []
    show_value_labels = payload.get("show_value_axis_labels") is not False

    if is_bar:
        parts.extend(_horizontal_grid_and_ticks(
            plot,
            ticks,
            lo,
            hi,
            label_size,
            percent,
            show_labels=show_value_labels,
        ))
        parts.extend(_bar_category_labels(plot, categories, label_size))
    else:
        parts.extend(_vertical_grid_and_ticks(
            plot,
            ticks,
            lo,
            hi,
            label_size,
            percent,
            show_labels=show_value_labels,
        ))
        parts.extend(_column_category_labels(
            plot,
            categories,
            label_size,
            point_aligned=chart_type in {"line", "area"},
        ))
    parts.extend(_axis_titles(plot, content, axis_titles, label_size, is_bar=is_bar))

    if chart_type in {"bar", "column"}:
        parts.extend(
            _render_bars(
                payload,
                categories,
                series,
                styles,
                segments,
                plot,
                lo,
                hi,
                grouping,
                horizontal=is_bar,
                label_size=label_size,
                percent=percent,
            )
        )
    else:
        parts.extend(
            _render_lines_or_areas(
                payload,
                categories,
                series,
                styles,
                segments,
                plot,
                lo,
                hi,
                chart_type,
                label_size,
                percent,
            )
        )
    return parts


def _category_labels(payload: dict[str, Any]) -> list[str] | None:
    raw_categories = payload.get("categories") or []
    axes = payload.get("axes")
    category_axis = axes.get("category") if isinstance(axes, dict) else None
    if not isinstance(category_axis, dict) or category_axis.get("kind") != "date":
        return [str(value) for value in raw_categories]

    number_format = str(category_axis.get("number_format") or "").lower()
    normalized_format = re.sub(r'\\.|"[^"]*"|\[[^]]*]', "", number_format)
    labels: list[str] = []
    for raw_value in raw_categories:
        try:
            serial = float(raw_value)
        except (TypeError, ValueError, OverflowError):
            return None
        if not math.isfinite(serial):
            return None
        date_parts = _excel_1900_date_parts(serial)
        if date_parts is None:
            return None
        year, month, day = date_parts
        if "yyyy-mm-dd" in normalized_format:
            labels.append(f"{year:04d}-{month:02d}-{day:02d}")
        elif "mm/dd/yyyy" in normalized_format:
            labels.append(f"{month:02d}/{day:02d}/{year:04d}")
        elif "m/d/yyyy" in normalized_format:
            labels.append(f"{month}/{day}/{year:04d}")
        else:
            labels.append(f"{year:04d}-{month:02d}-{day:02d}")
    return labels


def _excel_1900_date_parts(serial: float) -> tuple[int, int, int] | None:
    day_number = math.floor(serial)
    if day_number < 1:
        return None
    if day_number == 60:
        return 1900, 2, 29
    epoch = date(1899, 12, 31) if day_number < 60 else date(1899, 12, 30)
    try:
        value = epoch + timedelta(days=day_number)
    except (OverflowError, ValueError):
        return None
    return value.year, value.month, value.day


def _category_segments(
    series: list[dict[str, Any]],
    count: int,
    grouping: str,
) -> tuple[list[list[tuple[float, float]]], bool]:
    raw = [
        [float(value) for value in item.get("values", [])[:count]]
        for item in series
    ]
    percent = grouping == "percentStacked"
    if percent:
        positive = [sum(max(row[idx], 0.0) for row in raw) for idx in range(count)]
        negative = [sum(abs(min(row[idx], 0.0)) for row in raw) for idx in range(count)]
        for row in raw:
            for idx, value in enumerate(row):
                denominator = positive[idx] if value >= 0 else negative[idx]
                row[idx] = value / denominator if denominator else 0.0
    if grouping not in {"stacked", "percentStacked"}:
        return [[(0.0, value) for value in row] for row in raw], percent

    positive_base = [0.0] * count
    negative_base = [0.0] * count
    result: list[list[tuple[float, float]]] = []
    for row in raw:
        segments: list[tuple[float, float]] = []
        for idx, value in enumerate(row):
            if value >= 0:
                start = positive_base[idx]
                positive_base[idx] += value
                end = positive_base[idx]
            else:
                start = negative_base[idx]
                negative_base[idx] += value
                end = negative_base[idx]
            segments.append((start, end))
        result.append(segments)
    return result, percent


def _render_bars(
    payload: dict[str, Any],
    categories: list[str],
    series: list[dict[str, Any]],
    styles: list[SeriesVisualStyle],
    segments: list[list[tuple[float, float]]],
    plot: _Rect,
    lo: float,
    hi: float,
    grouping: str,
    *,
    horizontal: bool,
    label_size: float,
    percent: bool,
) -> list[str]:
    parts: list[str] = []
    stacked = grouping in {"stacked", "percentStacked"}
    category_span = (plot.h if horizontal else plot.w) / max(len(categories), 1)
    cluster = category_span * 0.72
    bar_span = cluster if stacked else cluster / max(len(series), 1)
    labels = payload.get("data_labels") if isinstance(payload.get("data_labels"), dict) else None
    for series_index, (item, style, row) in enumerate(zip(series, styles, segments)):
        fill = style.fill or "none"
        stroke = style.stroke or "none"
        for category_index, (start, end) in enumerate(row):
            offset = 0.0 if stacked else series_index * bar_span
            display_index = (
                len(categories) - 1 - category_index
                if horizontal else category_index
            )
            cluster_start = display_index * category_span + (category_span - cluster) / 2
            if horizontal:
                x1 = _map(end, lo, hi, plot.x, plot.x + plot.w)
                x0 = _map(start, lo, hi, plot.x, plot.x + plot.w)
                x = min(x0, x1)
                y = plot.y + cluster_start + offset
                w = max(abs(x1 - x0), 0.35)
                h = max(bar_span * 0.9, 0.5)
            else:
                y1 = _map(end, lo, hi, plot.y + plot.h, plot.y)
                y0 = _map(start, lo, hi, plot.y + plot.h, plot.y)
                x = plot.x + cluster_start + offset
                y = min(y0, y1)
                w = max(bar_span * 0.9, 0.5)
                h = max(abs(y1 - y0), 0.35)
            parts.append(
                f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" '
                f'height="{_fmt(h)}" fill="{fill}" fill-opacity="{_fmt(style.fill_opacity)}" '
                f'stroke="{stroke}" stroke-opacity="{_fmt(style.stroke_opacity)}" '
                f'stroke-width="{_fmt(max(0.4, style.stroke_width))}"/>'
            )
            if labels:
                value = float(item["values"][category_index])
                normalized_percent = end - start if percent else None
                label = _data_label(
                    labels,
                    str(item.get("name") or ""),
                    categories[category_index],
                    value,
                    percent_value=normalized_percent,
                )
                if label:
                    if horizontal:
                        tx = x1 + (4.0 if end >= start else -4.0)
                        ty = y + h / 2 + label_size * 0.32
                        anchor = "start" if end >= start else "end"
                    else:
                        tx = x + w / 2
                        ty = y1 - 4.0 if end >= start else y1 + label_size + 3.0
                        anchor = "middle"
                    parts.append(_text(tx, ty, label, size=max(6.0, label_size - 1), anchor=anchor))
    return parts


def _render_lines_or_areas(
    payload: dict[str, Any],
    categories: list[str],
    series: list[dict[str, Any]],
    styles: list[SeriesVisualStyle],
    segments: list[list[tuple[float, float]]],
    plot: _Rect,
    lo: float,
    hi: float,
    chart_type: str,
    label_size: float,
    percent: bool,
) -> list[str]:
    parts: list[str] = []
    count = len(categories)
    x_positions = [
        _category_point_x(plot, idx, count)
        for idx in range(count)
    ]
    labels = payload.get("data_labels") if isinstance(payload.get("data_labels"), dict) else None
    show_markers = chart_type == "line" and payload.get("line_style") == "lineMarker"
    for series_index, (item, style, row) in enumerate(zip(series, styles, segments)):
        fill_color = style.fill or "none"
        line_color = style.stroke
        top = [
            (x_positions[idx], _map(end, lo, hi, plot.y + plot.h, plot.y))
            for idx, (_start, end) in enumerate(row)
        ]
        if chart_type == "area":
            bottom = [
                (x_positions[idx], _map(start, lo, hi, plot.y + plot.h, plot.y))
                for idx, (start, _end) in enumerate(row)
            ]
            points = top + list(reversed(bottom))
            parts.append(
                f'<polygon points="{_points(points)}" fill="{fill_color}" '
                f'fill-opacity="{_fmt(min(style.fill_opacity, 0.58))}" '
                f'stroke="{line_color or "none"}" stroke-opacity="{_fmt(style.stroke_opacity)}" '
                f'stroke-width="{_fmt(max(0.7, style.stroke_width))}" '
                'stroke-linejoin="round"/>'
            )
        elif line_color is not None:
            parts.append(
                f'<polyline points="{_points(top)}" fill="none" stroke="{line_color}" '
                f'stroke-opacity="{_fmt(style.stroke_opacity)}" '
                f'stroke-width="{_fmt(max(1.0, style.stroke_width))}" '
                f'stroke-linecap="{style.line_cap}" stroke-linejoin="round"/>'
            )
        if show_markers:
            for x, y in top:
                radius = max(2.0, style.marker_size / 2)
                parts.append(
                    f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(radius)}" '
                    f'fill="{style.marker_fill or "none"}" '
                    f'fill-opacity="{_fmt(style.marker_fill_opacity)}" '
                    f'stroke="{style.marker_stroke or "none"}" '
                    f'stroke-opacity="{_fmt(style.marker_stroke_opacity)}" '
                    f'stroke-width="{_fmt(max(0.6, style.marker_stroke_width))}"/>'
                )
        if labels:
            for idx, (x, y) in enumerate(top):
                value = float(item["values"][idx])
                start, end = row[idx]
                normalized_percent = end - start if percent else None
                label = _data_label(
                    labels,
                    str(item.get("name") or ""),
                    categories[idx],
                    value,
                    percent_value=normalized_percent,
                )
                if label:
                    parts.append(_text(x, y - 5.0, label, size=max(6.0, label_size - 1), anchor="middle"))
    return parts


def _render_pie(
    payload: dict[str, Any],
    styles: list[SeriesVisualStyle],
    content: _Rect,
    doughnut: bool,
) -> list[str]:
    categories = [str(value) for value in payload.get("categories") or []]
    series = payload.get("series") or []
    if not categories or len(series) != 1:
        return []
    values = [abs(float(value)) for value in series[0].get("values") or []]
    total = sum(values)
    styles = _complete_styles(styles, len(categories))
    label_size = max(6.0, min(10.0, content.h * 0.035, content.w * 0.018))
    radius = max(5.0, min(content.w, content.h) * 0.34)
    cx = content.x + content.w / 2
    cy = content.y + content.h / 2
    if total <= 0:
        parts = [
            f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius)}" '
            'fill="none" stroke="#B8C0CC" stroke-width="1.2" stroke-dasharray="4 3"/>'
        ]
        if doughnut:
            parts.append(
                f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius * 0.75)}" '
                'fill="none" stroke="#D5DAE1" stroke-width="1"/>'
            )
        parts.append(
            _text(cx, cy + label_size * 0.32, "0", size=label_size, anchor="middle")
        )
        return parts
    parts: list[str] = []
    angle = -math.pi / 2
    for idx, (category, value, style) in enumerate(zip(categories, values, styles)):
        sweep = math.tau * value / total
        end = angle + sweep
        # Pie styles are completed before rendering, so ``None`` here means
        # the source explicitly used ``noFill`` rather than an absent style.
        fill = style.fill or "none"
        stroke = style.stroke or "none"
        if sweep >= math.tau - 1e-9:
            if doughnut:
                inner = radius * 0.75
                path = _full_ring_path(cx, cy, radius, inner)
                parts.append(
                    f'<path d="{path}" fill="{fill}" fill-opacity="{_fmt(style.fill_opacity)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(max(0.6, style.stroke_width))}" '
                    'fill-rule="evenodd"/>'
                )
            else:
                parts.append(
                    f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(radius)}" '
                    f'fill="{fill}" fill-opacity="{_fmt(style.fill_opacity)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(max(0.6, style.stroke_width))}"/>'
                )
        else:
            path = _sector_path(cx, cy, radius, angle, end, radius * 0.75 if doughnut else 0.0)
            parts.append(
                f'<path d="{path}" fill="{fill}" fill-opacity="{_fmt(style.fill_opacity)}" '
                f'stroke="{stroke}" stroke-opacity="{_fmt(style.stroke_opacity)}" '
                f'stroke-width="{_fmt(max(0.6, style.stroke_width))}" fill-rule="evenodd"/>'
            )
        mid = angle + sweep / 2
        label_radius = radius * (0.87 if doughnut else 0.68)
        lx = cx + math.cos(mid) * label_radius
        ly = cy + math.sin(mid) * label_radius + label_size * 0.32
        percent = value / total
        label = f"{category} {_format_percent(percent)}"
        parts.append(
            _text(
                lx,
                ly,
                label,
                size=label_size,
                anchor="middle",
                fill="#444444" if fill == "none" else _contrast_color(fill),
            )
        )
        angle = end
    return parts


def _render_xy(
    payload: dict[str, Any],
    styles: list[SeriesVisualStyle],
    content: _Rect,
    chart_type: str,
) -> list[str]:
    series = payload.get("series") or []
    if not series:
        return []
    styles = _complete_styles(styles, len(series))
    axis_titles = payload.get("axis_titles") if isinstance(payload.get("axis_titles"), dict) else {}
    label_size = max(6.0, min(11.0, content.h * 0.037, content.w * 0.021))
    left = max(40.0, content.w * 0.09) + (14.0 if axis_titles.get("y") else 0.0)
    bottom = max(26.0, content.h * 0.1) + (14.0 if axis_titles.get("x") else 0.0)
    plot = _Rect(
        content.x + left,
        content.y + 6.0,
        max(12.0, content.w - left - 10.0),
        max(12.0, content.h - bottom - 8.0),
    )
    x_values = [float(value) for item in series for value in item.get("x") or []]
    y_values = [float(value) for item in series for value in item.get("y") or []]
    x_lo, x_hi, x_ticks = _nice_scale(x_values, include_zero=False)
    y_lo, y_hi, y_ticks = _nice_scale(y_values, include_zero=False)
    parts = _xy_grid_and_ticks(plot, x_ticks, y_ticks, x_lo, x_hi, y_lo, y_hi, label_size)
    parts.extend(_xy_axis_titles(plot, content, axis_titles, label_size))
    nonnegative_bubble_sizes = [
        float(value)
        for item in series
        for value in item.get("sizes") or []
        if float(value) >= 0
    ]
    bubble_max = max(max(nonnegative_bubble_sizes or [0.0]), 1e-12)
    scatter_style = str(payload.get("scatter_style") or "marker")
    has_line = chart_type == "scatter" and scatter_style in {"line", "lineMarker", "smooth", "smoothMarker"}
    has_marker = chart_type == "bubble" or scatter_style in {"marker", "lineMarker", "smoothMarker"}
    for idx, (item, style) in enumerate(zip(series, styles)):
        color = style.stroke or style.fill or style.marker_fill or _DEFAULT_COLORS[idx % len(_DEFAULT_COLORS)]
        points = [
            (
                _map(float(x), x_lo, x_hi, plot.x, plot.x + plot.w),
                _map(float(y), y_lo, y_hi, plot.y + plot.h, plot.y),
            )
            for x, y in zip(item.get("x") or [], item.get("y") or [])
        ]
        if has_line and style.stroke is not None and len(points) >= 2:
            parts.append(
                f'<polyline points="{_points(points)}" fill="none" stroke="{color}" '
                f'stroke-opacity="{_fmt(style.stroke_opacity)}" '
                f'stroke-width="{_fmt(max(1.0, style.stroke_width))}" '
                f'stroke-linecap="{style.line_cap}" stroke-linejoin="round"/>'
            )
        if has_marker:
            sizes = item.get("sizes") or [style.marker_size * style.marker_size] * len(points)
            for point_index, (x, y) in enumerate(points):
                if chart_type == "bubble":
                    bubble_size = float(sizes[point_index])
                    if bubble_size < 0:
                        continue
                    radius = 3.0 + 13.0 * math.sqrt(bubble_size / bubble_max)
                else:
                    radius = max(2.0, style.marker_size / 2)
                fill = (
                    style.fill or "none"
                    if chart_type == "bubble"
                    else style.marker_fill or "none"
                )
                stroke = (
                    style.stroke or "none"
                    if chart_type == "bubble"
                    else style.marker_stroke or "none"
                )
                parts.append(
                    f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(radius)}" '
                    f'fill="{fill}" fill-opacity="{_fmt(style.marker_fill_opacity if chart_type == "scatter" else style.fill_opacity)}" '
                    f'stroke="{stroke}" stroke-opacity="{_fmt(style.marker_stroke_opacity)}" '
                    f'stroke-width="{_fmt(max(0.6, style.marker_stroke_width))}"/>'
                )
    return parts


def _vertical_grid_and_ticks(
    plot: _Rect,
    ticks: list[float],
    lo: float,
    hi: float,
    size: float,
    percent: bool,
    *,
    show_labels: bool,
) -> list[str]:
    parts: list[str] = []
    for tick in ticks:
        y = _map(tick, lo, hi, plot.y + plot.h, plot.y)
        parts.append(
            f'<line x1="{_fmt(plot.x)}" y1="{_fmt(y)}" x2="{_fmt(plot.x + plot.w)}" '
            f'y2="{_fmt(y)}" stroke="#D9D9D9" stroke-width="0.7"/>'
        )
        if show_labels:
            label = _format_percent(tick) if percent else _format_number(tick)
            parts.append(_text(plot.x - 5.0, y + size * 0.32, label, size=size, anchor="end", fill="#666666"))
    parts.append(
        f'<line x1="{_fmt(plot.x)}" y1="{_fmt(plot.y)}" x2="{_fmt(plot.x)}" '
        f'y2="{_fmt(plot.y + plot.h)}" stroke="#808080" stroke-width="1"/>'
    )
    return parts


def _horizontal_grid_and_ticks(
    plot: _Rect,
    ticks: list[float],
    lo: float,
    hi: float,
    size: float,
    percent: bool,
    *,
    show_labels: bool,
) -> list[str]:
    parts: list[str] = []
    for tick in ticks:
        x = _map(tick, lo, hi, plot.x, plot.x + plot.w)
        parts.append(
            f'<line x1="{_fmt(x)}" y1="{_fmt(plot.y)}" x2="{_fmt(x)}" '
            f'y2="{_fmt(plot.y + plot.h)}" stroke="#D9D9D9" stroke-width="0.7"/>'
        )
        if show_labels:
            label = _format_percent(tick) if percent else _format_number(tick)
            parts.append(_text(x, plot.y + plot.h + size + 4.0, label, size=size, anchor="middle", fill="#666666"))
    parts.append(
        f'<line x1="{_fmt(plot.x)}" y1="{_fmt(plot.y + plot.h)}" '
        f'x2="{_fmt(plot.x + plot.w)}" y2="{_fmt(plot.y + plot.h)}" '
        'stroke="#808080" stroke-width="1"/>'
    )
    return parts


def _column_category_labels(
    plot: _Rect,
    categories: list[str],
    size: float,
    *,
    point_aligned: bool,
) -> list[str]:
    parts: list[str] = []
    span = plot.w / max(len(categories), 1)
    rotate = len(categories) > 8 or any(len(value) > 10 for value in categories)
    for idx, category in enumerate(categories):
        if point_aligned:
            x = _category_point_x(plot, idx, len(categories))
        else:
            x = plot.x + span * (idx + 0.5)
        y = plot.y + plot.h + size + 5.0
        transform = f' transform="rotate(-35 {_fmt(x)} {_fmt(y)})"' if rotate else ""
        anchor = "end" if rotate else "middle"
        parts.append(
            f'<text x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="{anchor}" '
            f'font-family="Arial" font-size="{_fmt(size)}" fill="#555555"{transform}>'
            f'{html.escape(category)}</text>'
        )
    return parts


def _category_point_x(plot: _Rect, index: int, count: int) -> float:
    """Align line/area data points and their category labels."""
    if count <= 1:
        return plot.x + plot.w / 2
    return plot.x + plot.w * index / (count - 1)


def _bar_category_labels(plot: _Rect, categories: list[str], size: float) -> list[str]:
    span = plot.h / max(len(categories), 1)
    return [
        _text(
            plot.x - 6.0,
            plot.y + span * (len(categories) - idx - 0.5) + size * 0.32,
            category,
            size=size,
            anchor="end",
            fill="#555555",
        )
        for idx, category in enumerate(categories)
    ]


def _xy_grid_and_ticks(
    plot: _Rect,
    x_ticks: list[float],
    y_ticks: list[float],
    x_lo: float,
    x_hi: float,
    y_lo: float,
    y_hi: float,
    size: float,
) -> list[str]:
    parts = _vertical_grid_and_ticks(
        plot,
        y_ticks,
        y_lo,
        y_hi,
        size,
        False,
        show_labels=True,
    )
    for tick in x_ticks:
        x = _map(tick, x_lo, x_hi, plot.x, plot.x + plot.w)
        parts.append(_text(x, plot.y + plot.h + size + 4.0, _format_number(tick), size=size, anchor="middle", fill="#666666"))
    parts.append(
        f'<line x1="{_fmt(plot.x)}" y1="{_fmt(plot.y + plot.h)}" '
        f'x2="{_fmt(plot.x + plot.w)}" y2="{_fmt(plot.y + plot.h)}" '
        'stroke="#808080" stroke-width="1"/>'
    )
    return parts


def _axis_titles(
    plot: _Rect,
    content: _Rect,
    titles: dict[str, Any],
    size: float,
    *,
    is_bar: bool,
) -> list[str]:
    category = str(titles.get("category") or "")
    value = str(titles.get("value") or "")
    x_title = value if is_bar else category
    y_title = category if is_bar else value
    return _draw_axis_titles(plot, content, x_title, y_title, size)


def _xy_axis_titles(
    plot: _Rect,
    content: _Rect,
    titles: dict[str, Any],
    size: float,
) -> list[str]:
    return _draw_axis_titles(
        plot,
        content,
        str(titles.get("x") or ""),
        str(titles.get("y") or ""),
        size,
    )


def _draw_axis_titles(
    plot: _Rect,
    content: _Rect,
    x_title: str,
    y_title: str,
    size: float,
) -> list[str]:
    parts: list[str] = []
    if x_title:
        parts.append(_text(plot.x + plot.w / 2, content.y + content.h - 2.0, x_title, size=size, anchor="middle", weight="600"))
    if y_title:
        x = content.x + size
        y = plot.y + plot.h / 2
        parts.append(
            f'<text x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="middle" '
            f'font-family="Arial" font-size="{_fmt(size)}" font-weight="600" '
            f'fill="#444444" transform="rotate(-90 {_fmt(x)} {_fmt(y)})">'
            f'{html.escape(y_title)}</text>'
        )
    return parts


def _legend_entries(
    payload: dict[str, Any],
    styles: list[SeriesVisualStyle],
) -> list[tuple[str, str]]:
    chart_type = str(payload.get("type") or "")
    if chart_type in {"pie", "doughnut"}:
        labels = [str(value) for value in payload.get("categories") or []]
    else:
        labels = [str(item.get("name") or f"Series {idx + 1}") for idx, item in enumerate(payload.get("series") or [])]
    completed = _complete_styles(styles, len(labels))
    return [
        (
            label,
            style.fill or style.stroke or style.marker_fill or _DEFAULT_COLORS[idx % len(_DEFAULT_COLORS)],
        )
        for idx, (label, style) in enumerate(zip(labels, completed))
    ]


def _render_legend(
    entries: list[tuple[str, str]],
    rect: _Rect,
    position: str,
) -> list[str]:
    if not entries:
        return []
    size = max(6.0, min(10.0, rect.h * 0.18 if position.lower() in {"l", "r", "left", "right"} else 9.0))
    parts: list[str] = []
    if position.lower() in {"l", "r", "left", "right"}:
        row_h = min(18.0, rect.h / max(len(entries), 1))
        for idx, (label, color) in enumerate(entries):
            y = rect.y + row_h * (idx + 0.5)
            parts.append(
                f'<rect x="{_fmt(rect.x + 5)}" y="{_fmt(y - 4)}" width="8" height="8" fill="{color}"/>'
            )
            parts.append(_text(rect.x + 18.0, y + size * 0.32, label, size=size, anchor="start", fill="#444444"))
        return parts

    columns = max(1, min(4, int(rect.w // 130) or 1))
    rows = math.ceil(len(entries) / columns)
    row_h = rect.h / max(rows, 1)
    col_w = rect.w / columns
    for idx, (label, color) in enumerate(entries):
        row = idx // columns
        col = idx % columns
        x = rect.x + col * col_w + 5.0
        y = rect.y + row_h * (row + 0.5)
        parts.append(
            f'<rect x="{_fmt(x)}" y="{_fmt(y - 4)}" width="8" height="8" fill="{color}"/>'
        )
        parts.append(_text(x + 13.0, y + size * 0.32, label, size=size, anchor="start", fill="#444444"))
    return parts


def _data_label(
    config: dict[str, Any],
    series: str,
    category: str,
    value: float,
    *,
    percent_value: float | None,
) -> str:
    fields: list[str] = []
    if config.get("show_series"):
        fields.append(series)
    if config.get("show_category"):
        fields.append(category)
    if config.get("show_value"):
        fields.append(_format_data_label_value(
            value,
            config.get("number_format"),
        ))
    if config.get("show_percent"):
        if percent_value is None:
            raise ValueError(
                "normalized percent labels require percent-stacked segments"
            )
        number_format = config.get("number_format")
        normalized_format = str(number_format or "").strip()
        percent_format = (
            "0%"
            if not normalized_format or normalized_format.lower() == "general"
            else normalized_format
        )
        fields.append(_format_data_label_value(
            percent_value,
            percent_format,
        ))
    return " · ".join(field for field in fields if field)


def _format_data_label_value(value: float, number_format: Any) -> str:
    """Render the safe numeric subset used by normalized data labels.

    Unknown Excel format programs raise so the caller falls back to the
    reconstruction-only route instead of displaying a materially wrong label.
    """
    code = str(number_format or "").strip()
    if not code or code.lower() == "general":
        return _format_number(value)
    match = re.fullmatch(
        r"(?P<prefix>[$¥￥€£]?)(?P<group>#,##)?0"
        r"(?P<decimals>\.0+)?(?P<percent>%?)",
        code,
    )
    if match is None:
        raise ValueError(f"unsupported normalized data-label format: {code!r}")
    scaled = value * 100.0 if match.group("percent") else value
    decimals = len((match.group("decimals") or "").lstrip("."))
    grouping = "," if match.group("group") else ""
    quantum = Decimal(1).scaleb(-decimals)
    rounded = Decimal(str(abs(scaled))).quantize(
        quantum,
        rounding=ROUND_HALF_UP,
    )
    absolute = format(rounded, f"{grouping}.{decimals}f")
    sign = "-" if scaled < 0 else ""
    return (
        f"{sign}{match.group('prefix')}{absolute}{match.group('percent')}"
    )


def _nice_scale(
    values: list[float],
    *,
    include_zero: bool,
    percent: bool = False,
) -> tuple[float, float, list[float]]:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        finite = [0.0, 1.0]
    lo = min(finite)
    hi = max(finite)
    if include_zero:
        lo = min(lo, 0.0)
        hi = max(hi, 0.0)
    if percent:
        lo = min(lo, 0.0)
        hi = max(hi, 1.0)
    if math.isclose(lo, hi):
        delta = max(abs(lo) * 0.1, 1.0)
        lo -= delta
        hi += delta
    raw_step = (hi - lo) / 5.0
    magnitude = 10 ** math.floor(math.log10(raw_step))
    normalized = raw_step / magnitude
    nice = 1.0 if normalized <= 1 else 2.0 if normalized <= 2 else 2.5 if normalized <= 2.5 else 5.0 if normalized <= 5 else 10.0
    step = nice * magnitude
    nice_lo = math.floor(lo / step) * step
    nice_hi = math.ceil(hi / step) * step
    count = max(1, int(round((nice_hi - nice_lo) / step)))
    ticks = [nice_lo + idx * step for idx in range(count + 1)]
    return nice_lo, nice_hi, ticks


def _sector_path(
    cx: float,
    cy: float,
    outer: float,
    start: float,
    end: float,
    inner: float,
) -> str:
    x1 = cx + math.cos(start) * outer
    y1 = cy + math.sin(start) * outer
    x2 = cx + math.cos(end) * outer
    y2 = cy + math.sin(end) * outer
    large = 1 if end - start > math.pi else 0
    if inner <= 0:
        return (
            f"M {_fmt(cx)} {_fmt(cy)} L {_fmt(x1)} {_fmt(y1)} "
            f"A {_fmt(outer)} {_fmt(outer)} 0 {large} 1 {_fmt(x2)} {_fmt(y2)} Z"
        )
    ix2 = cx + math.cos(end) * inner
    iy2 = cy + math.sin(end) * inner
    ix1 = cx + math.cos(start) * inner
    iy1 = cy + math.sin(start) * inner
    return (
        f"M {_fmt(x1)} {_fmt(y1)} A {_fmt(outer)} {_fmt(outer)} 0 {large} 1 {_fmt(x2)} {_fmt(y2)} "
        f"L {_fmt(ix2)} {_fmt(iy2)} A {_fmt(inner)} {_fmt(inner)} 0 {large} 0 {_fmt(ix1)} {_fmt(iy1)} Z"
    )


def _full_ring_path(cx: float, cy: float, outer: float, inner: float) -> str:
    return (
        f"M {_fmt(cx + outer)} {_fmt(cy)} "
        f"A {_fmt(outer)} {_fmt(outer)} 0 1 1 {_fmt(cx - outer)} {_fmt(cy)} "
        f"A {_fmt(outer)} {_fmt(outer)} 0 1 1 {_fmt(cx + outer)} {_fmt(cy)} Z "
        f"M {_fmt(cx + inner)} {_fmt(cy)} "
        f"A {_fmt(inner)} {_fmt(inner)} 0 1 0 {_fmt(cx - inner)} {_fmt(cy)} "
        f"A {_fmt(inner)} {_fmt(inner)} 0 1 0 {_fmt(cx + inner)} {_fmt(cy)} Z"
    )


def _complete_styles(
    styles: list[SeriesVisualStyle],
    count: int,
) -> list[SeriesVisualStyle]:
    result = list(styles[:count])
    while len(result) < count:
        color = _DEFAULT_COLORS[len(result) % len(_DEFAULT_COLORS)]
        result.append(
            SeriesVisualStyle(
                fill=color,
                stroke=color,
                marker_fill=color,
                marker_stroke=color,
            )
        )
    return result


def _entry_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text") or "")
    return str(value or "")


def _entry_value(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def _entry_color(value: Any, default: str) -> str:
    color = _entry_value(value, "color")
    return str(color) if isinstance(color, str) and color.startswith("#") else default


def _font_size(value: Any, default: float, bounds: _Rect) -> float:
    try:
        size = float(value)
    except (TypeError, ValueError, OverflowError):
        size = default
    return max(6.0, min(size, max(8.0, bounds.h * 0.18)))


def _text(
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    anchor: str = "start",
    fill: str = "#444444",
    weight: str | None = None,
) -> str:
    weight_attr = f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{_fmt(x)}" y="{_fmt(y)}" text-anchor="{anchor}" '
        f'font-family="Arial" font-size="{_fmt(size)}" fill="{fill}"{weight_attr}>'
        f'{html.escape(str(value))}</text>'
    )


def _map(value: float, lo: float, hi: float, out_lo: float, out_hi: float) -> float:
    if math.isclose(lo, hi):
        return (out_lo + out_hi) / 2
    return out_lo + (value - lo) * (out_hi - out_lo) / (hi - lo)


def _points(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)


def _format_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K".replace(".0K", "K")
    if math.isclose(value, round(value)):
        return str(int(round(value)))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _format_percent(value: float) -> str:
    percent = value * 100.0
    return f"{percent:.1f}%".replace(".0%", "%")


def _contrast_color(color: str) -> str:
    token = color.lstrip("#")
    try:
        r, g, b = (int(token[idx:idx + 2], 16) for idx in (0, 2, 4))
    except (ValueError, TypeError):
        return "#FFFFFF"
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return "#222222" if luminance > 0.62 else "#FFFFFF"


def _fmt(value: float) -> str:
    if not math.isfinite(float(value)):
        return "0"
    rounded = round(float(value), 3)
    if rounded == 0:
        return "0"
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.3f}".rstrip("0").rstrip(".")
