"""Validate native-object fallback and release-route status attributes."""

from __future__ import annotations

from xml.etree import ElementTree as ET


VISUAL_STATUSES = frozenset({"source-preview", "normalized", "placeholder"})
ROUTE_STATUSES = frozenset({"reconstruction-only"})


def native_marker_status_errors(elem: ET.Element) -> list[str]:
    """Return invalid or contradictory native-object status declarations."""
    errors: list[str] = []
    visual_raw = elem.get("data-pptx-visual-status")
    route_raw = elem.get("data-pptx-route-status")
    native_raw = elem.get("data-pptx-native")
    fallback_raw = elem.get("data-pptx-native-status")

    visual = visual_raw.strip() if visual_raw is not None else None
    route = route_raw.strip() if route_raw is not None else None
    native = native_raw.strip() if native_raw is not None else ""
    fallback = fallback_raw.strip() if fallback_raw is not None else ""

    if visual_raw is not None and visual_raw != visual:
        errors.append("data-pptx-visual-status must not contain surrounding whitespace")
    if route_raw is not None and route_raw != route:
        errors.append("data-pptx-route-status must not contain surrounding whitespace")
    if visual is not None and visual not in VISUAL_STATUSES:
        errors.append(f"unsupported data-pptx-visual-status value: {visual!r}")
    if route is not None and route not in ROUTE_STATUSES:
        errors.append(f"unsupported data-pptx-route-status value: {route!r}")
    if visual == "placeholder" and route != "reconstruction-only":
        errors.append(
            "data-pptx-visual-status='placeholder' requires "
            "data-pptx-route-status='reconstruction-only'"
        )
    if route == "reconstruction-only" and visual != "placeholder":
        errors.append(
            "data-pptx-route-status='reconstruction-only' requires "
            "data-pptx-visual-status='placeholder'"
        )
    if native and fallback:
        errors.append(
            "data-pptx-native and data-pptx-native-status are mutually exclusive"
        )
    return errors


def native_marker_release_block_reason(elem: ET.Element) -> str | None:
    """Return invalid status metadata that must block an export.

    A valid ``reconstruction-only`` declaration is diagnostic rather than a
    release block: default export keeps its visible placeholder, while an
    active native marker may still reconstruct the editable object.
    """
    errors = native_marker_status_errors(elem)
    if errors:
        return f"invalid-status: {errors[0]}"
    return None
