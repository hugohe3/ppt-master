"""DrawingML color resolution.

Resolves any of the 6 OOXML color types (srgbClr, schemeClr, sysClr, prstClr,
hslClr, scrgbClr) plus the registered luminance, saturation, hue, alpha,
grayscale, complement, and inverse modifiers into an (#RRGGBB, alpha) pair.

Theme palette is resolved from the slide master's a:clrMap and theme1.xml's
a:clrScheme.
"""

from __future__ import annotations

import colorsys
import re
from xml.etree import ElementTree as ET

from .emu_units import NS
from .ooxml_loader import PartRef


# ---------------------------------------------------------------------------
# Preset color names (DrawingML <a:prstClr val="...">)
# ---------------------------------------------------------------------------

# Source: complete ECMA-376 ST_PresetColorVal enumeration (190 values).
PRST_COLORS = {
    "aliceBlue": "F0F8FF", "antiqueWhite": "FAEBD7", "aqua": "00FFFF",
    "aquamarine": "7FFFD4", "azure": "F0FFFF", "beige": "F5F5DC",
    "bisque": "FFE4C4", "black": "000000", "blanchedAlmond": "FFEBCD",
    "blue": "0000FF", "blueViolet": "8A2BE2", "brown": "A52A2A",
    "burlyWood": "DEB887", "cadetBlue": "5F9EA0", "chartreuse": "7FFF00",
    "chocolate": "D2691E", "coral": "FF7F50", "cornflowerBlue": "6495ED",
    "cornsilk": "FFF8DC", "crimson": "DC143C", "cyan": "00FFFF",
    "darkBlue": "00008B", "darkCyan": "008B8B", "darkGoldenrod": "B8860B",
    "darkGray": "A9A9A9", "darkGrey": "A9A9A9", "darkGreen": "006400",
    "darkKhaki": "BDB76B", "darkMagenta": "8B008B", "darkOliveGreen": "556B2F",
    "darkOrange": "FF8C00", "darkOrchid": "9932CC", "darkRed": "8B0000",
    "darkSalmon": "E9967A", "darkSeaGreen": "8FBC8F", "darkSlateBlue": "483D8B",
    "darkSlateGray": "2F4F4F", "darkSlateGrey": "2F4F4F",
    "darkTurquoise": "00CED1", "darkViolet": "9400D3", "deepPink": "FF1493",
    "deepSkyBlue": "00BFFF", "dimGray": "696969", "dimGrey": "696969",
    "dkBlue": "00008B", "dkCyan": "008B8B", "dkGoldenrod": "B8860B",
    "dkGray": "A9A9A9", "dkGrey": "A9A9A9", "dkGreen": "006400",
    "dkKhaki": "BDB76B", "dkMagenta": "8B008B", "dkOliveGreen": "556B2F",
    "dkOrange": "FF8C00", "dkOrchid": "9932CC", "dkRed": "8B0000",
    "dkSalmon": "E9967A", "dkSeaGreen": "8FBC8F", "dkSlateBlue": "483D8B",
    "dkSlateGray": "2F4F4F", "dkSlateGrey": "2F4F4F",
    "dkTurquoise": "00CED1", "dkViolet": "9400D3",
    "dodgerBlue": "1E90FF", "firebrick": "B22222", "floralWhite": "FFFAF0",
    "forestGreen": "228B22", "fuchsia": "FF00FF", "gainsboro": "DCDCDC",
    "ghostWhite": "F8F8FF", "gold": "FFD700", "goldenrod": "DAA520",
    "gray": "808080", "grey": "808080", "green": "008000",
    "greenYellow": "ADFF2F", "honeydew": "F0FFF0", "hotPink": "FF69B4",
    "indianRed": "CD5C5C", "indigo": "4B0082", "ivory": "FFFFF0",
    "khaki": "F0E68C", "lavender": "E6E6FA", "lavenderBlush": "FFF0F5",
    "lawnGreen": "7CFC00", "lemonChiffon": "FFFACD",
    "lightBlue": "ADD8E6", "lightCoral": "F08080", "lightCyan": "E0FFFF",
    "lightGoldenrodYellow": "FAFAD2", "lightGray": "D3D3D3",
    "lightGrey": "D3D3D3", "lightGreen": "90EE90", "lightPink": "FFB6C1",
    "lightSalmon": "FFA07A", "lightSeaGreen": "20B2AA",
    "lightSkyBlue": "87CEFA", "lightSlateGray": "778899",
    "lightSlateGrey": "778899", "lightSteelBlue": "B0C4DE",
    "lightYellow": "FFFFE0", "ltBlue": "ADD8E6", "ltCoral": "F08080",
    "ltCyan": "E0FFFF", "ltGoldenrodYellow": "FAFAD2", "ltGray": "D3D3D3",
    "ltGrey": "D3D3D3", "ltGreen": "90EE90", "ltPink": "FFB6C1",
    "ltSalmon": "FFA07A", "ltSeaGreen": "20B2AA", "ltSkyBlue": "87CEFA",
    "ltSlateGray": "778899", "ltSlateGrey": "778899",
    "ltSteelBlue": "B0C4DE", "ltYellow": "FFFFE0",
    "lime": "00FF00", "limeGreen": "32CD32", "linen": "FAF0E6",
    "magenta": "FF00FF", "maroon": "800000", "medAquamarine": "66CDAA",
    "medBlue": "0000CD", "medOrchid": "BA55D3", "medPurple": "9370DB",
    "medSeaGreen": "3CB371", "medSlateBlue": "7B68EE",
    "medSpringGreen": "00FA9A", "medTurquoise": "48D1CC",
    "medVioletRed": "C71585", "mediumAquamarine": "66CDAA",
    "mediumBlue": "0000CD", "mediumOrchid": "BA55D3", "mediumPurple": "9370DB",
    "mediumSeaGreen": "3CB371", "mediumSlateBlue": "7B68EE",
    "mediumSpringGreen": "00FA9A", "mediumTurquoise": "48D1CC",
    "mediumVioletRed": "C71585",
    "midnightBlue": "191970", "mintCream": "F5FFFA", "mistyRose": "FFE4E1",
    "moccasin": "FFE4B5", "navajoWhite": "FFDEAD", "navy": "000080",
    "oldLace": "FDF5E6", "olive": "808000", "oliveDrab": "6B8E23",
    "orange": "FFA500", "orangeRed": "FF4500", "orchid": "DA70D6",
    "paleGoldenrod": "EEE8AA", "paleGreen": "98FB98", "paleTurquoise": "AFEEEE",
    "paleVioletRed": "DB7093", "papayaWhip": "FFEFD5", "peachPuff": "FFDAB9",
    "peru": "CD853F", "pink": "FFC0CB", "plum": "DDA0DD",
    "powderBlue": "B0E0E6", "purple": "800080", "red": "FF0000",
    "rosyBrown": "BC8F8F", "royalBlue": "4169E1", "saddleBrown": "8B4513",
    "salmon": "FA8072", "sandyBrown": "F4A460", "seaGreen": "2E8B57",
    "seaShell": "FFF5EE", "sienna": "A0522D", "silver": "C0C0C0",
    "skyBlue": "87CEEB", "slateBlue": "6A5ACD", "slateGray": "708090",
    "slateGrey": "708090", "snow": "FFFAFA", "springGreen": "00FF7F",
    "steelBlue": "4682B4", "tan": "D2B48C", "teal": "008080",
    "thistle": "D8BFD8", "tomato": "FF6347", "turquoise": "40E0D0",
    "violet": "EE82EE", "wheat": "F5DEB3", "white": "FFFFFF",
    "whiteSmoke": "F5F5F5", "yellow": "FFFF00", "yellowGreen": "9ACD32",
}


# Scheme color name normalization
SCHEME_ALIASES = {
    "bg1": "lt1", "bg2": "lt2",
    "tx1": "dk1", "tx2": "dk2",
}
_THEME_SCHEME_SLOTS = (
    "dk1",
    "lt1",
    "dk2",
    "lt2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)
_COLOR_MAP_SOURCES = (
    "bg1",
    "tx1",
    "bg2",
    "tx2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
)
_THEME_COLOR_TAGS = frozenset({
    f"{{{NS['a']}}}{name}"
    for name in ("srgbClr", "sysClr", "prstClr", "hslClr", "scrgbClr")
})
_SRGB_HEX_RE = re.compile(r"[0-9A-Fa-f]{6}")
_OOXML_INTEGER_RE = re.compile(r"[+-]?[0-9]+")
_OOXML_INT_MIN = -(2**31)
_OOXML_INT_MAX = 2**31 - 1
_COLOR_MODIFIER_PERCENT_RANGES = {
    "alpha": (0, 100000),
    "alphaMod": (0, _OOXML_INT_MAX),
    "alphaOff": (-100000, 100000),
    "hueMod": (0, _OOXML_INT_MAX),
    "lumMod": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "lumOff": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "satMod": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "satOff": (_OOXML_INT_MIN, _OOXML_INT_MAX),
    "shade": (0, 100000),
    "tint": (0, 100000),
}
_COLOR_MODIFIER_FLAG_NAMES = frozenset({"comp", "gray", "inv"})
_SCHEME_COLOR_VALUES = {
    "bg1",
    "tx1",
    "bg2",
    "tx2",
    "accent1",
    "accent2",
    "accent3",
    "accent4",
    "accent5",
    "accent6",
    "hlink",
    "folHlink",
    "phClr",
    "dk1",
    "lt1",
    "dk2",
    "lt2",
}
_SYSTEM_COLOR_VALUES = {
    "scrollBar",
    "background",
    "activeCaption",
    "inactiveCaption",
    "menu",
    "window",
    "windowFrame",
    "menuText",
    "windowText",
    "captionText",
    "activeBorder",
    "inactiveBorder",
    "appWorkspace",
    "highlight",
    "highlightText",
    "btnFace",
    "btnShadow",
    "grayText",
    "btnText",
    "inactiveCaptionText",
    "btnHighlight",
    "3dDkShadow",
    "3dLight",
    "infoText",
    "infoBk",
    "hotLight",
    "gradientActiveCaption",
    "gradientInactiveCaption",
    "menuHighlight",
    "menuBar",
}


# ---------------------------------------------------------------------------
# ColorPalette
# ---------------------------------------------------------------------------

class ColorPalette:
    """Resolves scheme colors via the master's a:clrMap + theme1's a:clrScheme.

    a:clrMap remaps presentation-level scheme names (bg1/tx1) to theme-level
    names (lt1/dk1) — this is rarely overridden but must be honored.
    """

    def __init__(self, master: PartRef | None, theme: PartRef | None) -> None:
        self.scheme: dict[str, str] = {}
        self.clr_map: dict[str, str] = {}
        if theme is not None:
            self._load_scheme(theme)
        if master is not None:
            self._load_clr_map(master)

    def _load_scheme(self, theme: PartRef) -> None:
        theme_root = theme.xml
        if theme_root.tag != f"{{{NS['a']}}}theme":
            raise ValueError(f"{theme.path}: expected a:theme root")

        theme_elements = theme_root.findall("a:themeElements", NS)
        if len(theme_elements) != 1:
            raise ValueError(
                f"{theme.path}: expected exactly one direct a:themeElements"
            )
        clr_schemes = theme_elements[0].findall("a:clrScheme", NS)
        if len(clr_schemes) != 1:
            raise ValueError(
                f"{theme.path}: expected exactly one direct a:clrScheme"
            )
        clr_scheme = clr_schemes[0]
        children = list(clr_scheme)
        expected_tags = [
            f"{{{NS['a']}}}{name}" for name in _THEME_SCHEME_SLOTS
        ]
        if (
            set(clr_scheme.attrib) != {"name"}
            or (clr_scheme.text or "").strip()
            or [child.tag for child in children] != expected_tags
            or any((child.tail or "").strip() for child in children)
        ):
            raise ValueError(
                f"{theme.path}: invalid DrawingML color scheme structure"
            )

        for name, slot in zip(_THEME_SCHEME_SLOTS, children):
            color_children = list(slot)
            if (
                slot.attrib
                or (slot.text or "").strip()
                or len(color_children) != 1
                or color_children[0].tag not in _THEME_COLOR_TAGS
                or (color_children[0].tail or "").strip()
            ):
                raise ValueError(
                    f"{theme.path}: invalid DrawingML theme color slot {name!r}"
                )
            try:
                hex_, alpha = resolve_color(color_children[0], None)
            except ValueError as exc:
                raise ValueError(
                    f"{theme.path}: invalid DrawingML theme color slot "
                    f"{name!r}: {exc}"
                ) from exc
            if hex_ is None:
                raise ValueError(
                    f"{theme.path}: unresolved DrawingML theme color slot {name!r}"
                )
            if alpha != 1.0:
                raise ValueError(
                    f"{theme.path}: non-opaque DrawingML theme color slot {name!r}"
                )
            self.scheme[name] = hex_[1:]

    def _load_clr_map(self, master: PartRef) -> None:
        master_root = master.xml
        if master_root.tag != f"{{{NS['p']}}}sldMaster":
            raise ValueError(f"{master.path}: expected p:sldMaster root")
        clr_maps = master_root.findall("p:clrMap", NS)
        if len(clr_maps) != 1:
            raise ValueError(
                f"{master.path}: expected exactly one direct p:clrMap"
            )
        clr_map = clr_maps[0]
        children = list(clr_map)
        if (
            set(clr_map.attrib) != set(_COLOR_MAP_SOURCES)
            or children
            or (clr_map.text or "").strip()
        ):
            raise ValueError(
                f"{master.path}: invalid DrawingML color map structure"
            )
        for source in _COLOR_MAP_SOURCES:
            target = clr_map.attrib[source]
            if target not in _THEME_SCHEME_SLOTS:
                raise ValueError(
                    f"{master.path}: invalid DrawingML color map target "
                    f"{source}={target!r}"
                )
            self.clr_map[source] = target

    def resolve_scheme(self, name: str) -> str | None:
        """scheme name (e.g. 'accent1', 'bg1') -> 'RRGGBB'. None on miss."""
        # apply clrMap remap (bg1 -> lt1, tx1 -> dk1, etc.)
        mapped = self.clr_map.get(name, name)
        # canonical alias (bg1 -> lt1)
        mapped = SCHEME_ALIASES.get(mapped, mapped)
        return self.scheme.get(mapped)


# ---------------------------------------------------------------------------
# Color resolution
# ---------------------------------------------------------------------------

# All concrete color element names under the a: namespace.
COLOR_TAGS = ("srgbClr", "schemeClr", "sysClr", "prstClr",
              "hslClr", "scrgbClr")


def validate_no_fill(elem: ET.Element) -> None:
    """Require the empty DrawingML a:noFill leaf contract."""
    if elem.attrib or list(elem) or (elem.text or "").strip():
        raise ValueError("Invalid DrawingML noFill structure")


def resolve_solid_fill_color(
    elem: ET.Element,
    palette: ColorPalette | None,
    *,
    placeholder_hex: str | None = None,
) -> tuple[str, float]:
    """Resolve one explicit color from a closed DrawingML solid fill."""
    children = list(elem)
    color_tags = {f"{{{NS['a']}}}{name}" for name in COLOR_TAGS}
    if not elem.attrib and not children and not (elem.text or "").strip():
        raise ValueError(
            "DrawingML solid fill requires one explicit color"
        )
    if (
        elem.attrib
        or len(children) != 1
        or children[0].tag not in color_tags
        or (elem.text or "").strip()
        or (children[0].tail or "").strip()
    ):
        raise ValueError("Invalid DrawingML solid fill structure")
    hex_, alpha = resolve_color(
        children[0],
        palette,
        placeholder_hex=placeholder_hex,
    )
    if hex_ is None:
        raise ValueError("DrawingML solid fill color cannot be resolved")
    return hex_, alpha


def find_color_elem(parent: ET.Element | None) -> ET.Element | None:
    """Return the first child color element (any of the 6 OOXML color tags)."""
    if parent is None:
        return None
    for tag in COLOR_TAGS:
        elem = parent.find(f"a:{tag}", NS)
        if elem is not None:
            return elem
    return None


def resolve_color(
    color_elem: ET.Element | None,
    palette: ColorPalette | None,
    *,
    placeholder_hex: str | None = None,
) -> tuple[str | None, float]:
    """Resolve a color element to (#RRGGBB, alpha).

    Args:
        color_elem: a:srgbClr / a:schemeClr / etc. May be None.
        palette: ColorPalette for resolving schemeClr.
        placeholder_hex: when a child uses schemeClr val="phClr" (placeholder
            color used inside theme styles), substitute this hex.

    Returns:
        (hex string with leading '#', alpha in [0,1]) or (None, 1.0) on failure.
    """
    if color_elem is None:
        return None, 1.0

    tag = color_elem.tag.split("}", 1)[-1]
    base_hex: str | None = None
    alpha: float = 1.0

    if tag == "srgbClr":
        base_hex = _srgb_hex_value(color_elem)
    elif tag == "schemeClr":
        name = _scheme_color_name(color_elem)
        if name == "phClr":
            base_hex = _normalize_hex(placeholder_hex) if placeholder_hex else None
        elif palette is not None:
            base_hex = palette.resolve_scheme(name)
    elif tag == "sysClr":
        base_hex = _system_color_fallback(color_elem)
    elif tag == "prstClr":
        base_hex = _preset_color_hex(color_elem)
    elif tag == "hslClr":
        base_hex = _hsl_color_hex(color_elem)
    elif tag == "scrgbClr":
        base_hex = _scrgb_color_hex(color_elem)

    if base_hex is None:
        return None, 1.0

    # Apply modifiers (children of the color element).
    base_hex, alpha = _apply_modifiers(base_hex, color_elem)
    return f"#{base_hex}", alpha


def _srgb_hex_value(color_elem: ET.Element) -> str:
    """Parse the closed six-digit DrawingML sRGB base token."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}srgbClr"
        or set(color_elem.attrib) != {"val"}
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML sRGB color structure")
    raw = color_elem.attrib["val"]
    if _SRGB_HEX_RE.fullmatch(raw) is None:
        raise ValueError(f"Invalid DrawingML sRGB color value: {raw!r}")
    return raw.upper()


def _scheme_color_name(color_elem: ET.Element) -> str:
    """Parse one closed DrawingML scheme-color reference."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}schemeClr"
        or set(color_elem.attrib) != {"val"}
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML scheme color structure")
    name = color_elem.attrib["val"]
    if name not in _SCHEME_COLOR_VALUES:
        raise ValueError(f"Invalid DrawingML scheme color value: {name!r}")
    return name


def _system_color_fallback(color_elem: ET.Element) -> str:
    """Parse a registered system color with a portable six-digit fallback."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}sysClr"
        or set(color_elem.attrib) - {"val", "lastClr"}
        or "val" not in color_elem.attrib
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML system color structure")
    name = color_elem.attrib["val"]
    if name not in _SYSTEM_COLOR_VALUES:
        raise ValueError(f"Invalid DrawingML system color value: {name!r}")
    fallback = color_elem.get("lastClr")
    if fallback is None:
        raise ValueError(
            "DrawingML system color requires a lastClr fallback"
        )
    if _SRGB_HEX_RE.fullmatch(fallback) is None:
        raise ValueError(
            f"Invalid DrawingML system color fallback: {fallback!r}"
        )
    return fallback.upper()


def _preset_color_hex(color_elem: ET.Element) -> str:
    """Resolve one exact value from the complete DrawingML preset enum."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}prstClr"
        or set(color_elem.attrib) != {"val"}
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML preset color structure")
    name = color_elem.attrib["val"]
    hex_ = PRST_COLORS.get(name)
    if hex_ is None:
        raise ValueError(f"Invalid DrawingML preset color value: {name!r}")
    return hex_


def _hsl_color_hex(color_elem: ET.Element) -> str:
    """Resolve one closed DrawingML HSL base color."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}hslClr"
        or set(color_elem.attrib) != {"hue", "sat", "lum"}
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML HSL color structure")
    hue = _bounded_integer_attribute(
        color_elem,
        "hue",
        minimum=0,
        maximum=21_599_999,
        label="HSL color",
    )
    saturation = _bounded_integer_attribute(
        color_elem,
        "sat",
        minimum=0,
        maximum=100000,
        label="HSL color",
    )
    luminance = _bounded_integer_attribute(
        color_elem,
        "lum",
        minimum=0,
        maximum=100000,
        label="HSL color",
    )
    return _hsl_to_hex(
        hue / 21_600_000.0,
        saturation / 100000.0,
        luminance / 100000.0,
    )


def _scrgb_color_hex(color_elem: ET.Element) -> str:
    """Resolve one closed linear-light DrawingML scRGB base color."""
    children = list(color_elem)
    if (
        color_elem.tag != f"{{{NS['a']}}}scrgbClr"
        or set(color_elem.attrib) != {"r", "g", "b"}
        or (color_elem.text or "").strip()
        or any((child.tail or "").strip() for child in children)
    ):
        raise ValueError("Invalid DrawingML scRGB color structure")
    channels = [
        _bounded_integer_attribute(
            color_elem,
            attr,
            minimum=0,
            maximum=100000,
            label="scRGB color",
        )
        / 100000.0
        for attr in ("r", "g", "b")
    ]
    return _linear_rgb01_to_hex(*channels)


def _bounded_integer_attribute(
    elem: ET.Element,
    attr: str,
    *,
    minimum: int,
    maximum: int,
    label: str,
) -> int:
    """Parse one required bounded DrawingML integer attribute."""
    raw = elem.attrib[attr]
    token = raw.strip()
    if _OOXML_INTEGER_RE.fullmatch(token) is None:
        raise ValueError(f"Invalid DrawingML {label} {attr}: {raw!r}")
    value = int(token)
    if not minimum <= value <= maximum:
        raise ValueError(f"Invalid DrawingML {label} {attr}: {raw!r}")
    return value


def _parse_color_modifier(child: ET.Element) -> tuple[str, int | None]:
    """Parse one modifier from the closed DrawingML color subset."""
    tag = child.tag.split("}", 1)[-1]
    if child.tag != f"{{{NS['a']}}}{tag}":
        raise ValueError(f"invalid-color-modifier-namespace:{tag}")
    if tag in _COLOR_MODIFIER_FLAG_NAMES:
        if child.attrib or list(child) or (child.text or "").strip():
            raise ValueError(f"invalid-color-modifier-structure:{tag}")
        return tag, None

    bounds = _COLOR_MODIFIER_PERCENT_RANGES.get(tag)
    if tag == "hueOff":
        bounds = (_OOXML_INT_MIN, _OOXML_INT_MAX)
    elif bounds is None:
        raise ValueError(f"unsupported-color-modifier:{tag}")
    if (
        set(child.attrib) != {"val"}
        or list(child)
        or (child.text or "").strip()
    ):
        raise ValueError(f"invalid-color-modifier-structure:{tag}")
    try:
        value = _bounded_integer_attribute(
            child,
            "val",
            minimum=bounds[0],
            maximum=bounds[1],
            label=f"{tag} color modifier",
        )
    except ValueError:
        raise ValueError(f"invalid-{tag}-val:{child.attrib['val']!r}") from None
    return tag, value


def _apply_modifiers(hex_color: str, color_elem: ET.Element) -> tuple[str, float]:
    """Apply the registered DrawingML color modifiers in document order."""
    r, g, b = _hex_to_rgb01(hex_color)
    # Convert to HSL for luminance/saturation ops; convert back when emitting.
    h, lum, sat = colorsys.rgb_to_hls(r, g, b)
    alpha = 1.0

    for child in list(color_elem):
        if not isinstance(child.tag, str):
            continue
        tag, value = _parse_color_modifier(child)

        if tag == "tint":
            # Tint blends toward white. r' = r + (1-r)*(1-val) is the common
            # interpretation; OOXML actually defines tint on luminance.
            # Use luminance-based tint per ECMA-376.
            ratio = value / 100000.0
            lum = lum * ratio + (1.0 - ratio)
        elif tag == "shade":
            # Shade blends toward black on luminance.
            lum = lum * (value / 100000.0)
        elif tag == "lumMod":
            lum = lum * (value / 100000.0)
        elif tag == "lumOff":
            lum = lum + (value / 100000.0)
        elif tag == "satMod":
            sat = sat * (value / 100000.0)
        elif tag == "satOff":
            sat = sat + (value / 100000.0)
        elif tag == "hueMod":
            h = (h * (value / 100000.0)) % 1.0
        elif tag == "hueOff":
            h = (h + value / 21_600_000.0) % 1.0
        elif tag == "alpha":
            alpha = value / 100000.0
        elif tag == "alphaMod":
            alpha = max(0.0, min(1.0, alpha * (value / 100000.0)))
        elif tag == "alphaOff":
            alpha = max(0.0, min(1.0, alpha + (value / 100000.0)))
        elif tag == "gray":
            # Convert to grayscale based on luminance.
            sat = 0.0
        elif tag == "comp":
            # Complement: hue rotated 180°
            h = (h + 0.5) % 1.0
        elif tag == "inv":
            # RGB invert
            rr, gg, bb = colorsys.hls_to_rgb(h, lum, sat)
            rr, gg, bb = 1.0 - rr, 1.0 - gg, 1.0 - bb
            h, lum, sat = colorsys.rgb_to_hls(rr, gg, bb)

        # Clamp luminance / saturation to [0,1]
        lum = max(0.0, min(1.0, lum))
        sat = max(0.0, min(1.0, sat))

    rr, gg, bb = colorsys.hls_to_rgb(h, lum, sat)
    return _rgb01_to_hex(rr, gg, bb), alpha


# ---------------------------------------------------------------------------
# Hex / RGB / HSL helpers
# ---------------------------------------------------------------------------

def _normalize_hex(value: str | None) -> str | None:
    """Strip '#' and validate 6-digit hex. Return uppercase or None on failure."""
    if value is None:
        return None
    v = value.strip()
    if v.startswith("#"):
        v = v[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    if len(v) != 6:
        return None
    try:
        int(v, 16)
    except ValueError:
        return None
    return v.upper()


def _hex_to_rgb01(hex_color: str) -> tuple[float, float, float]:
    h = _normalize_hex(hex_color) or "000000"
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b


def _rgb01_to_hex(r: float, g: float, b: float) -> str:
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    return f"{int(round(r * 255)):02X}{int(round(g * 255)):02X}{int(round(b * 255)):02X}"


def _linear_rgb01_to_hex(r: float, g: float, b: float) -> str:
    """Encode linear-light RGB channels as an SVG sRGB hex color."""
    encoded = (
        12.92 * channel
        if channel <= 0.0031308
        else 1.055 * channel ** (1.0 / 2.4) - 0.055
        for channel in (r, g, b)
    )
    return _rgb01_to_hex(*encoded)


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    h = h % 1.0 if h != 1.0 else 1.0
    s = max(0.0, min(1.0, s))
    l = max(0.0, min(1.0, l))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return _rgb01_to_hex(r, g, b)
