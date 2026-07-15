"""Canonical and compatible attribute access for chart/table replacements."""

from __future__ import annotations

from collections.abc import Callable
from xml.etree import ElementTree as ET


REPLACE_WITH_ATTR = "data-pptx-replace-with"
LEGACY_REPLACE_WITH_ATTR = "data-pptx-native"
REPLACEMENT_STATUS_ATTR = "data-pptx-replacement-status"
LEGACY_REPLACEMENT_STATUS_ATTR = "data-pptx-native-status"
IMPORT_SOURCE_ATTR = "data-pptx-import-source"
LEGACY_IMPORT_SOURCE_ATTR = "data-pptx-native-source"
FALLBACK_KIND_ATTR = "data-pptx-fallback-kind"
LEGACY_FALLBACK_KIND_ATTR = "data-pptx-visual-status"
LEGACY_ROUTE_STATUS_ATTR = "data-pptx-route-status"


class NativeMarkerAttributeError(ValueError):
    """Raised when canonical and compatible marker attributes conflict."""


def _normalized_token(value: str) -> str:
    return value.strip().lower()


def _resolved_alias(
    elem: ET.Element,
    canonical: str,
    legacy: str,
    *,
    normalize: Callable[[str], str] = _normalized_token,
) -> str | None:
    canonical_raw = elem.get(canonical)
    legacy_raw = elem.get(legacy)
    canonical_value = normalize(canonical_raw) if canonical_raw is not None else None
    legacy_value = normalize(legacy_raw) if legacy_raw is not None else None
    if (
        canonical_value is not None
        and legacy_value is not None
        and canonical_value != legacy_value
    ):
        raise NativeMarkerAttributeError(
            f"{canonical}={canonical_raw!r} conflicts with compatible "
            f"{legacy}={legacy_raw!r}"
        )
    return canonical_value if canonical_value is not None else legacy_value


def native_replacement_kind(elem: ET.Element) -> str:
    """Return the requested chart/table replacement kind, or an empty string."""
    return _resolved_alias(elem, REPLACE_WITH_ATTR, LEGACY_REPLACE_WITH_ATTR) or ""


def native_replacement_status(elem: ET.Element) -> str:
    """Return the fallback-only replacement status, or an empty string."""
    return (
        _resolved_alias(
            elem,
            REPLACEMENT_STATUS_ATTR,
            LEGACY_REPLACEMENT_STATUS_ATTR,
            normalize=str.strip,
        )
        or ""
    )


def native_import_source(elem: ET.Element) -> str:
    """Return replacement payload provenance, or an empty string."""
    return (
        _resolved_alias(
            elem,
            IMPORT_SOURCE_ATTR,
            LEGACY_IMPORT_SOURCE_ATTR,
            normalize=str.strip,
        )
        or ""
    )


def native_fallback_kind(elem: ET.Element) -> str | None:
    """Return the visible fallback classification when declared."""
    return _resolved_alias(
        elem,
        FALLBACK_KIND_ATTR,
        LEGACY_FALLBACK_KIND_ATTR,
        normalize=str.strip,
    )


def native_metadata_payload_matches(
    elem: ET.Element,
    parent_kind: str,
) -> bool:
    """Return whether one metadata node carries this replacement payload.

    Compatible metadata kind attributes remain readable, but any declared
    kind must agree with both its alias and the parent replacement marker.
    """
    native_kind = elem.get(LEGACY_REPLACE_WITH_ATTR)
    compatible_kind = elem.get("data-pptx-kind")
    for attr, raw in (
        (LEGACY_REPLACE_WITH_ATTR, native_kind),
        ("data-pptx-kind", compatible_kind),
    ):
        if raw is not None and raw != raw.strip():
            raise NativeMarkerAttributeError(
                f"metadata {attr} must not contain surrounding whitespace"
            )
    if native_kind is not None and compatible_kind is not None:
        if _normalized_token(native_kind) != _normalized_token(compatible_kind):
            raise NativeMarkerAttributeError(
                "metadata data-pptx-native conflicts with data-pptx-kind"
            )
    declared_raw = native_kind if native_kind is not None else compatible_kind
    declared_kind = _normalized_token(declared_raw) if declared_raw is not None else None
    if declared_kind is not None and declared_kind != parent_kind:
        raise NativeMarkerAttributeError(
            f"metadata kind {declared_kind!r} conflicts with parent "
            f"replacement kind {parent_kind!r}"
        )
    metadata_type_raw = elem.get("type")
    if metadata_type_raw is not None and metadata_type_raw != metadata_type_raw.strip():
        raise NativeMarkerAttributeError(
            "metadata type must not contain surrounding whitespace"
        )
    metadata_type = (metadata_type_raw or "").lower()
    return metadata_type == "application/json" or declared_kind == parent_kind


def native_marker_legacy_warnings(elem: ET.Element) -> list[str]:
    """Return migration advice for compatible legacy marker spellings."""
    tag = elem.tag.rsplit("}", 1)[-1]
    if tag == "metadata":
        native_kind = elem.get(LEGACY_REPLACE_WITH_ATTR)
        compatible_kind = elem.get("data-pptx-kind")
        if (
            native_kind is not None
            and compatible_kind is not None
            and _normalized_token(native_kind) != _normalized_token(compatible_kind)
        ):
            return []
        warnings = []
        for legacy in (LEGACY_REPLACE_WITH_ATTR, "data-pptx-kind"):
            if elem.get(legacy) is not None:
                warnings.append(
                    f"legacy metadata attribute {legacy} is compatible; use "
                    'type="application/json" because the parent replacement '
                    "marker determines the payload kind. No change is required "
                    "for export."
                )
        return warnings

    try:
        native_replacement_kind(elem)
        native_replacement_status(elem)
        native_import_source(elem)
        native_fallback_kind(elem)
    except NativeMarkerAttributeError:
        return []

    warnings = []
    replacements = (
        (LEGACY_REPLACE_WITH_ATTR, REPLACE_WITH_ATTR),
        (LEGACY_REPLACEMENT_STATUS_ATTR, REPLACEMENT_STATUS_ATTR),
        (LEGACY_IMPORT_SOURCE_ATTR, IMPORT_SOURCE_ATTR),
        (LEGACY_FALLBACK_KIND_ATTR, FALLBACK_KIND_ATTR),
    )
    for legacy, canonical in replacements:
        if elem.get(legacy) is not None:
            warnings.append(
                f"legacy attribute {legacy} is compatible; use {canonical} "
                "for project-canonical SVG. No change is required for export."
            )
    if elem.get(LEGACY_ROUTE_STATUS_ATTR) is not None:
        warnings.append(
            f"legacy attribute {LEGACY_ROUTE_STATUS_ATTR} is compatible; omit it "
            f"because {FALLBACK_KIND_ATTR}='placeholder' already implies the "
            "reconstruction-only route. No change is required for export."
        )
    return warnings
