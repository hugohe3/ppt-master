"""Visible-fallback fingerprint contract for native chart/table markers."""

from __future__ import annotations

import re
import secrets
from xml.etree import ElementTree as ET

from pptx_shapes import (
    NATIVE_FALLBACK_SHA256_ATTR,
    svg_native_fallback_fingerprint,
)

from .marker_attributes import native_import_source, native_replacement_kind


NATIVE_FALLBACK_RUNTIME_ATTR = "data-pptx-runtime-fallback-unchanged"
_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR = "data-pptx-runtime-fallback-token"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_RUNTIME_TOKEN = secrets.token_hex(16)


def stamp_native_fallback_baseline(
    elem: ET.Element,
    *,
    document_root: ET.Element | None = None,
) -> str:
    """Record the current canonical visible-subtree hash on one marker."""
    digest = svg_native_fallback_fingerprint(
        elem,
        document_root=document_root,
    )
    elem.set(NATIVE_FALLBACK_SHA256_ATTR, digest)
    elem.attrib.pop(NATIVE_FALLBACK_RUNTIME_ATTR, None)
    elem.attrib.pop(_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR, None)
    return digest


def snapshot_native_fallback_freshness(root: ET.Element) -> None:
    """Snapshot raw marker freshness before exporter preprocessing mutates SVG."""
    for elem in root.iter():
        if elem.tag.rsplit("}", 1)[-1] == "metadata":
            continue
        if not native_replacement_kind(elem):
            continue
        expected, invalid = _expected_native_fallback_hash(elem)
        if invalid:
            elem.set(NATIVE_FALLBACK_RUNTIME_ATTR, "invalid")
            elem.set(_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR, _RUNTIME_TOKEN)
        elif expected is None:
            elem.attrib.pop(NATIVE_FALLBACK_RUNTIME_ATTR, None)
            elem.attrib.pop(_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR, None)
        else:
            actual = svg_native_fallback_fingerprint(
                elem,
                document_root=root,
            )
            elem.set(
                NATIVE_FALLBACK_RUNTIME_ATTR,
                "1" if actual == expected else "0",
            )
            elem.set(_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR, _RUNTIME_TOKEN)


def native_fallback_contract_warnings(
    elem: ET.Element,
    *,
    use_runtime_snapshot: bool = False,
    document_root: ET.Element | None = None,
) -> list[str]:
    """Return non-blocking diagnostics for default/checker compatibility."""
    expected, invalid = _expected_native_fallback_hash(elem)
    if invalid:
        return [
            f"{NATIVE_FALLBACK_SHA256_ATTR} must be a 64-digit SHA-256; "
            "the shape-based SVG fallback remains available, but "
            "--native-charts-and-tables will fail"
        ]
    if expected is None:
        if native_import_source(elem) != "pptx":
            return []
        return [
            f"imported marker has no {NATIVE_FALLBACK_SHA256_ATTR} baseline; "
            "the marker remains compatible with Chart/Table replacement, but "
            "stale fallback edits cannot be detected"
        ]
    if _native_fallback_is_fresh(
        elem,
        expected,
        use_runtime_snapshot=use_runtime_snapshot,
        document_root=document_root,
    ):
        return []
    return [
        "visible SVG fallback differs from its recorded baseline; default "
        "shape-based fallback export remains available, but "
        "--native-charts-and-tables will fail"
    ]


def require_fresh_native_fallback(
    elem: ET.Element,
    *,
    use_runtime_snapshot: bool = False,
    document_root: ET.Element | None = None,
) -> None:
    """Fail Chart/Table replacement when a recorded fallback is stale."""
    expected, invalid = _expected_native_fallback_hash(elem)
    if invalid:
        raise RuntimeError(
            f"{NATIVE_FALLBACK_SHA256_ATTR} must be a 64-digit SHA-256"
        )
    if expected is None:
        return
    if _native_fallback_is_fresh(
        elem,
        expected,
        use_runtime_snapshot=use_runtime_snapshot,
        document_root=document_root,
    ):
        return
    raise RuntimeError(
        "Visible native-object SVG fallback was edited after its baseline was "
        "recorded; --native-charts-and-tables stopped to avoid discarding the "
        "SVG edit. "
        "Use the default fallback export, or deliberately update the native "
        "metadata and baseline together"
    )


def _expected_native_fallback_hash(
    elem: ET.Element,
) -> tuple[str | None, bool]:
    raw = elem.get(NATIVE_FALLBACK_SHA256_ATTR)
    if raw is None:
        return None, False
    if raw != raw.strip() or _SHA256_RE.fullmatch(raw) is None:
        return None, True
    return raw.lower(), False


def _native_fallback_is_fresh(
    elem: ET.Element,
    expected: str,
    *,
    use_runtime_snapshot: bool,
    document_root: ET.Element | None,
) -> bool:
    if (
        use_runtime_snapshot
        and elem.get(_NATIVE_FALLBACK_RUNTIME_TOKEN_ATTR) == _RUNTIME_TOKEN
    ):
        snapshot = elem.get(NATIVE_FALLBACK_RUNTIME_ATTR)
        if snapshot == "1":
            return True
        if snapshot in {"0", "invalid"}:
            return False
    return svg_native_fallback_fingerprint(
        elem,
        document_root=document_root,
    ) == expected
