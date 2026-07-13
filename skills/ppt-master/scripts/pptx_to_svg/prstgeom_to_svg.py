"""DrawingML <a:prstGeom> -> SVG geometry conversion.

The visible SVG geometry is accompanied by the source preset name and every
explicit ``a:avLst`` guide formula. This metadata is rendering-neutral and
lets the reverse converter distinguish a native PowerPoint shape from an
arbitrary SVG path without guessing from its appearance.

The standard preset catalog is evaluated by the shared data-driven geometry
engine. Presets outside that locked catalog retain their source semantics on
an explicitly marked bounding-box fallback; they never masquerade as ``rect``.

The evaluated result carries one or more painted SVG path layers plus the
rendering-neutral metadata used by the reverse converter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from pptx_shapes import get_preset_registry

from .emu_units import NS, Xfrm, fmt_num
from .preset_registry_to_svg import SvgPresetPath, render_preset_geometry


# ---------------------------------------------------------------------------
# GeomResult
# ---------------------------------------------------------------------------

@dataclass
class GeomResult:
    """Result of converting a prst preset to SVG.

    `tag` is the SVG element tag (rect / ellipse / line / polygon / path /
    polyline). `attrs` are absolute SVG coordinates already in slide space.
    `path_d` (when tag == 'path') is the d attribute. The slide assembler
    merges fill/stroke attrs from fill_to_svg/ln_to_svg.
    """

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    # When tag == 'path' use path_d for the d attribute.
    path_d: str | None = None
    # When tag == 'polygon' / 'polyline' use points for the points attribute.
    points: str | None = None
    # Standard presets can contain multiple independently painted path layers.
    layers: tuple[SvgPresetPath, ...] = ()


# ---------------------------------------------------------------------------
# Explicit fallback for presets outside the locked standard catalog
# ---------------------------------------------------------------------------

def _rect(xfrm: Xfrm) -> GeomResult:
    return GeomResult(
        tag="rect",
        attrs={
            "x": fmt_num(xfrm.x),
            "y": fmt_num(xfrm.y),
            "width": fmt_num(xfrm.w),
            "height": fmt_num(xfrm.h),
        },
    )


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def convert_prst_geom(
    prst: str,
    xfrm: Xfrm,
    sp_pr: ET.Element | None,
) -> GeomResult | None:
    """Convert <a:prstGeom prst="..."> to a GeomResult.

    Every emitted result carries ``data-pptx-prst`` plus one
    ``data-pptx-av-<name>`` attribute per explicit adjustment guide. Unknown
    presets use a visibly neutral bounding-box fallback with diagnostic
    metadata instead of silently changing their semantic type to ``rect``.

    Returns ``None`` only when the logical frame cannot produce geometry.
    """
    metadata = _preset_metadata(prst, sp_pr)
    registry = get_preset_registry()
    if prst not in registry:
        result = _rect(xfrm)
        result.attrs.update(metadata)
        result.attrs.update({
            "data-pptx-geometry-status": "unsupported",
            "data-pptx-geometry-reason": f"unsupported-preset:{prst}",
        })
        return result
    if xfrm.w < 0 or xfrm.h < 0 or (xfrm.w == 0 and xfrm.h == 0):
        return None

    try:
        rendered = render_preset_geometry(
            prst,
            xfrm,
            _preset_adjustments(sp_pr),
        )
    except ValueError as exc:
        result = _rect(xfrm)
        result.attrs.update(metadata)
        result.attrs.update({
            "data-pptx-geometry-status": "unsupported",
            "data-pptx-geometry-reason": (
                f"preset-evaluation-error:{type(exc).__name__}"
            ),
        })
        return result
    if not rendered.paths:
        return None
    return GeomResult(
        tag="path",
        attrs=metadata,
        path_d=" ".join(path.d for path in rendered.paths),
        layers=rendered.paths,
    )


def _preset_metadata(
    prst: str,
    prst_geom: ET.Element | None,
) -> dict[str, str]:
    """Return rendering-neutral SVG attributes for native preset semantics."""
    attrs = {"data-pptx-prst": prst}
    if prst_geom is None:
        return attrs

    av_lst = prst_geom.find("a:avLst", NS)
    if av_lst is None:
        return attrs
    for guide in av_lst.findall("a:gd", NS):
        name = guide.attrib.get("name", "")
        if not name:
            continue
        attrs[f"data-pptx-av-{name}"] = guide.attrib.get("fmla", "")
    return attrs


def _preset_adjustments(
    prst_geom: ET.Element | None,
) -> dict[str, str]:
    """Return explicit instance adjustment formulas for registry evaluation."""
    if prst_geom is None:
        return {}
    av_lst = prst_geom.find("a:avLst", NS)
    if av_lst is None:
        return {}
    return {
        guide.attrib["name"]: guide.attrib.get("fmla", "")
        for guide in av_lst.findall("a:gd", NS)
        if guide.attrib.get("name")
    }


def supported_presets() -> set[str]:
    """Return the set of recognized prst values for diagnostics."""
    return set(get_preset_registry().names)
