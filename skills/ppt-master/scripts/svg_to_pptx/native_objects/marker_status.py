"""Validate chart/table replacement fallback and release-route attributes."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .marker_attributes import (
    FALLBACK_KIND_ATTR,
    IMPORT_SOURCE_ATTR,
    LEGACY_FALLBACK_KIND_ATTR,
    LEGACY_IMPORT_SOURCE_ATTR,
    LEGACY_REPLACEMENT_STATUS_ATTR,
    LEGACY_REPLACE_WITH_ATTR,
    LEGACY_ROUTE_STATUS_ATTR,
    REPLACEMENT_STATUS_ATTR,
    REPLACE_WITH_ATTR,
    NativeMarkerAttributeError,
    native_fallback_kind,
    native_import_source,
    native_replacement_kind,
    native_replacement_status,
)


VISUAL_STATUSES = frozenset({"source-preview", "normalized", "placeholder"})
ROUTE_STATUSES = frozenset({"reconstruction-only"})
REPLACEMENT_KINDS = frozenset({"chart", "table"})
# Closed importer outputs from chart_to_svg, chartex_to_svg, and tbl_to_svg.
# This includes codes forwarded through their dynamic ``status`` parameters.
REPLACEMENT_STATUS_CODES = frozenset({
    "unsupported-3d-chart",
    "unsupported-chart-analysis-features",
    "unsupported-chart-axis-number-format",
    "unsupported-chart-axis-options",
    "unsupported-chart-axis-titles",
    "unsupported-chart-bar-options",
    "unsupported-chart-bubble-options",
    "unsupported-chart-cache",
    "unsupported-chart-category-format",
    "unsupported-chart-data-labels",
    "unsupported-chart-data-table",
    "unsupported-chart-doughnut-options",
    "unsupported-chart-legend-position",
    "unsupported-chart-line-style",
    "unsupported-chart-of-pie-options",
    "unsupported-chart-parse",
    "unsupported-chart-part",
    "unsupported-chart-pie-options",
    "unsupported-chart-plot",
    "unsupported-chart-point-labels",
    "unsupported-chart-radar-style",
    "unsupported-chart-reference",
    "unsupported-chart-relationship",
    "unsupported-chart-scatter-style",
    "unsupported-chart-schema",
    "unsupported-chart-series-data-labels",
    "unsupported-chart-series-order",
    "unsupported-chart-series-style",
    "unsupported-chart-type",
    "unsupported-chart-uri",
    "unsupported-chartex-cache",
    "unsupported-chartex-data-id",
    "unsupported-chartex-dimension",
    "unsupported-chartex-parse",
    "unsupported-chartex-part",
    "unsupported-chartex-schema",
    "unsupported-chartex-series",
    "unsupported-chartex-structure",
    "unsupported-chartex-type",
    "unsupported-combo-category-format",
    "unsupported-combo-category-layout",
    "unsupported-combo-chart",
    "unsupported-combo-series-order",
    "unsupported-date-axis",
    "unsupported-date-system",
    "unsupported-formatted-category-cache",
    "unsupported-merge-topology",
    "unsupported-native-transform",
    "unsupported-stock-chart",
    "unsupported-table-direct-formatting",
    "unsupported-table-geometry",
    "unsupported-table-size",
    "unsupported-table-style",
})


def native_marker_status_errors(elem: ET.Element) -> list[str]:
    """Return invalid or contradictory replacement status declarations."""
    errors: list[str] = []
    native_raw_values = {
        REPLACE_WITH_ATTR: elem.get(REPLACE_WITH_ATTR),
        LEGACY_REPLACE_WITH_ATTR: elem.get(LEGACY_REPLACE_WITH_ATTR),
    }
    fallback_status_raw_values = {
        REPLACEMENT_STATUS_ATTR: elem.get(REPLACEMENT_STATUS_ATTR),
        LEGACY_REPLACEMENT_STATUS_ATTR: elem.get(LEGACY_REPLACEMENT_STATUS_ATTR),
    }
    import_source_raw_values = {
        IMPORT_SOURCE_ATTR: elem.get(IMPORT_SOURCE_ATTR),
        LEGACY_IMPORT_SOURCE_ATTR: elem.get(LEGACY_IMPORT_SOURCE_ATTR),
    }
    visual_raw = elem.get(FALLBACK_KIND_ATTR)
    legacy_visual_raw = elem.get(LEGACY_FALLBACK_KIND_ATTR)
    route_raw = elem.get(LEGACY_ROUTE_STATUS_ATTR)
    try:
        visual = native_fallback_kind(elem)
        native = native_replacement_kind(elem)
        fallback = native_replacement_status(elem)
        native_import_source(elem)
    except NativeMarkerAttributeError as exc:
        errors.append(str(exc))
        return errors

    route = route_raw.strip() if route_raw is not None else None

    for attr, raw in (
        *native_raw_values.items(),
        *fallback_status_raw_values.items(),
        *import_source_raw_values.items(),
    ):
        if raw is not None and raw != raw.strip():
            errors.append(f"{attr} must not contain surrounding whitespace")
    canonical_kind_raw = native_raw_values[REPLACE_WITH_ATTR]
    if (
        canonical_kind_raw is not None
        and canonical_kind_raw == canonical_kind_raw.strip()
        and canonical_kind_raw != canonical_kind_raw.lower()
    ):
        errors.append(f"{REPLACE_WITH_ATTR} must use lowercase chart or table")
    if visual_raw is not None and visual_raw != visual_raw.strip():
        errors.append(f"{FALLBACK_KIND_ATTR} must not contain surrounding whitespace")
    if legacy_visual_raw is not None and legacy_visual_raw != legacy_visual_raw.strip():
        errors.append(
            f"{LEGACY_FALLBACK_KIND_ATTR} must not contain surrounding whitespace"
        )
    if route_raw is not None and route_raw != route:
        errors.append(f"{LEGACY_ROUTE_STATUS_ATTR} must not contain surrounding whitespace")
    if visual is not None and visual not in VISUAL_STATUSES:
        errors.append(f"unsupported {FALLBACK_KIND_ATTR} value: {visual!r}")
    if route is not None and route not in ROUTE_STATUSES:
        errors.append(f"unsupported {LEGACY_ROUTE_STATUS_ATTR} value: {route!r}")
    if any(raw is not None for raw in native_raw_values.values()):
        if native not in REPLACEMENT_KINDS:
            errors.append(f"unsupported {REPLACE_WITH_ATTR} value: {native!r}")
    if any(raw is not None for raw in fallback_status_raw_values.values()):
        if not fallback:
            errors.append(f"{REPLACEMENT_STATUS_ATTR} must not be empty")
        elif fallback not in REPLACEMENT_STATUS_CODES:
            errors.append(
                f"unsupported {REPLACEMENT_STATUS_ATTR} value: {fallback!r}"
            )
    if any(raw is not None for raw in import_source_raw_values.values()):
        source = native_import_source(elem)
        if source != "pptx":
            errors.append(f"unsupported {IMPORT_SOURCE_ATTR} value: {source!r}")
    if (
        visual_raw is None
        and legacy_visual_raw is not None
        and visual == "placeholder"
        and route != "reconstruction-only"
    ):
        errors.append(
            f"{LEGACY_FALLBACK_KIND_ATTR}='placeholder' requires "
            f"{LEGACY_ROUTE_STATUS_ATTR}='reconstruction-only'"
        )
    if route == "reconstruction-only" and visual != "placeholder":
        errors.append(
            f"{LEGACY_ROUTE_STATUS_ATTR}='reconstruction-only' requires "
            f"{FALLBACK_KIND_ATTR}='placeholder'"
        )
    if native and fallback:
        errors.append(
            f"data-pptx-replace-with and {REPLACEMENT_STATUS_ATTR} are mutually exclusive"
        )
    return errors


def native_marker_release_block_reason(elem: ET.Element) -> str | None:
    """Return invalid status metadata that must block an export.

    A valid ``reconstruction-only`` declaration is diagnostic rather than a
    release block: default export keeps its visible placeholder, while an
    an active replacement marker may still reconstruct a native Chart/Table.
    """
    errors = native_marker_status_errors(elem)
    if errors:
        return f"invalid-status: {errors[0]}"
    return None
