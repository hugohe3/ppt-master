"""Theme and color resolver for DrawingML schemeClr references.

A DrawingML <a:schemeClr val="accent1"/> reference goes through two hops:
    1. clrMap on slideMaster may remap virtual slots (bg1 -> lt1, tx1 -> dk1)
    2. clrScheme in theme1.xml defines the actual sRGB for accent1..6, lt1/2, dk1/2

This module encapsulates both hops so callers just call
    theme.resolve_scheme_color('accent1') -> 'D97757'
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .ir import Theme


# DrawingML / PresentationML XML namespaces
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

# Default clrMap if the slideMaster does not declare one.
# PowerPoint's implicit default per ISO/IEC 29500-1 §19.3.1.17.
DEFAULT_CLR_MAP = {
    "bg1": "lt1",
    "tx1": "dk1",
    "bg2": "lt2",
    "tx2": "dk2",
    "accent1": "accent1",
    "accent2": "accent2",
    "accent3": "accent3",
    "accent4": "accent4",
    "accent5": "accent5",
    "accent6": "accent6",
    "hlink": "hlink",
    "folHlink": "folHlink",
}


# ---------------------------------------------------------------------------
# theme1.xml parsing
# ---------------------------------------------------------------------------

def parse_color_scheme(theme_root: ET.Element | None) -> dict[str, str]:
    """Extract clrScheme entries as {'accent1': 'D97757', ...}.

    Returns 6-char hex colors without the leading '#'. Handles <a:srgbClr>,
    <a:sysClr> (falls back to lastClr), and <a:schemeClr> (rarely nested here
    but defensively skipped).
    """
    colors: dict[str, str] = {}
    if theme_root is None:
        return colors

    scheme = theme_root.find(".//a:clrScheme", NS)
    if scheme is None:
        return colors

    for child in list(scheme):
        if not isinstance(child.tag, str):
            continue
        slot_name = child.tag.split("}", 1)[-1]
        hex_color = _extract_hex_from_color_node(child)
        if hex_color:
            colors[slot_name] = hex_color

    return colors


def _extract_hex_from_color_node(color_parent: ET.Element) -> str | None:
    """Drill into a color-carrying parent (<a:accent1>, <a:clrMap>, ...) and return hex.

    Tries <a:srgbClr val> first, then <a:sysClr lastClr>.
    Returns 6-char uppercase hex, or None if no extractable color.
    """
    srgb = color_parent.find("a:srgbClr", NS)
    if srgb is not None:
        val = srgb.attrib.get("val")
        if val:
            return val.upper().lstrip("#")

    sys_clr = color_parent.find("a:sysClr", NS)
    if sys_clr is not None:
        last = sys_clr.attrib.get("lastClr")
        if last:
            return last.upper().lstrip("#")

    return None


def parse_font_scheme(theme_root: ET.Element | None) -> dict[str, str]:
    """Extract fontScheme typefaces.

    Returns a dict with up to these keys:
        majorLatin, majorEastAsia, majorComplexScript,
        minorLatin, minorEastAsia, minorComplexScript
    """
    fonts: dict[str, str] = {}
    if theme_root is None:
        return fonts

    scheme = theme_root.find(".//a:fontScheme", NS)
    if scheme is None:
        return fonts

    for role, tag in (("major", "a:majorFont"), ("minor", "a:minorFont")):
        group = scheme.find(tag, NS)
        if group is None:
            continue

        latin = group.find("a:latin", NS)
        if latin is not None and latin.attrib.get("typeface"):
            fonts[f"{role}Latin"] = latin.attrib["typeface"]

        ea = group.find("a:ea", NS)
        if ea is not None and ea.attrib.get("typeface"):
            fonts[f"{role}EastAsia"] = ea.attrib["typeface"]

        cs = group.find("a:cs", NS)
        if cs is not None and cs.attrib.get("typeface"):
            fonts[f"{role}ComplexScript"] = cs.attrib["typeface"]

    return fonts


# ---------------------------------------------------------------------------
# slideMaster clrMap parsing
# ---------------------------------------------------------------------------

def parse_clr_map(master_root: ET.Element | None) -> dict[str, str]:
    """Extract <p:clrMap> attributes from slideMaster.

    Falls back to DEFAULT_CLR_MAP if the element is missing or empty.
    Slide-level <p:clrMapOvr> is handled separately by callers that need it.
    """
    if master_root is None:
        return dict(DEFAULT_CLR_MAP)

    clr_map = master_root.find(".//p:clrMap", NS)
    if clr_map is None:
        return dict(DEFAULT_CLR_MAP)

    mapped = dict(DEFAULT_CLR_MAP)
    for key, val in clr_map.attrib.items():
        # ET attrib keys are plain (no namespace prefix on clrMap attrs)
        mapped[key] = val
    return mapped


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def build_theme(
    theme_root: ET.Element | None,
    master_root: ET.Element | None = None,
) -> Theme:
    """Build a resolved Theme from theme1.xml + slideMaster clrMap.

    The master_root is optional: if absent, the default clrMap is used.
    """
    return Theme(
        colors=parse_color_scheme(theme_root),
        fonts=parse_font_scheme(theme_root),
        clr_map=parse_clr_map(master_root),
    )


# ---------------------------------------------------------------------------
# Color-node resolver (schemeClr + srgbClr + sysClr, with luminance mods)
# ---------------------------------------------------------------------------

def resolve_color_element(
    color_parent: ET.Element | None,
    theme: Theme,
) -> tuple[str | None, float]:
    """Resolve a color-bearing DrawingML element to (hex, alpha).

    The color_parent is any element that may contain ONE of:
        <a:srgbClr val="RRGGBB"/>
        <a:sysClr val="..." lastClr="RRGGBB"/>
        <a:schemeClr val="accent1"/>

    Both the direct color node and its child <a:alpha val="..."/> and
    luminance modifiers (<a:lumMod>, <a:lumOff>) are read. Luminance mods
    are NOT applied in v1 — we return the base color and log unsupported
    mods via the returned alpha only. Applying lumMod/lumOff requires
    HSL conversion and is deferred to P3.

    Returns:
        (hex_without_hash, alpha in 0..1). Hex is None if unresolvable.
    """
    if color_parent is None:
        return None, 1.0

    color_hex: str | None = None
    alpha = 1.0

    for child in color_parent:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.split("}", 1)[-1]

        if tag == "srgbClr":
            val = child.attrib.get("val")
            if val:
                color_hex = val.upper().lstrip("#")
        elif tag == "sysClr":
            last = child.attrib.get("lastClr")
            if last:
                color_hex = last.upper().lstrip("#")
        elif tag == "schemeClr":
            val = child.attrib.get("val")
            if val:
                color_hex = theme.resolve_scheme_color(val)

        if color_hex is not None:
            # Nested alpha / lumMod inside the color node
            color_node = child
            alpha_node = color_node.find("a:alpha", NS)
            if alpha_node is not None:
                try:
                    alpha = int(alpha_node.attrib.get("val", "100000")) / 100000.0
                except ValueError:
                    pass
            break  # only the first color child counts

    return color_hex, alpha
