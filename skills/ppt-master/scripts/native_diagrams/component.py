"""Shared helpers for the native-diagram library: theme flattening + rel resolution.

A **native diagram** is a self-contained, theme-independent DrawingML shape group
lifted verbatim out of a source ``.pptx`` slide. Unlike the SVG round-trip
(``pptx_to_svg`` -> ``svg_to_pptx``), nothing is re-rendered: the original
``<p:sp>`` / ``<p:grpSp>`` XML is kept byte-for-byte, so decorative flourishes
(bezier flow arrows, halftone dot patterns, gradient 3D shading) survive intact
while the shapes stay natively editable in PowerPoint.

The single transform applied is **theme flattening**. Source decks express most
colors as ``<a:schemeClr>`` (theme references) and fonts as ``+mj-ea`` / ``+mn-lt``
tokens. Pasted into a deck with a different theme those would recolor / re-font.
Flattening resolves every ``schemeClr`` -> ``srgbClr`` (through the slide master's
``clrMap`` and the theme's color scheme) and every theme-font token -> its concrete
typeface, so the component renders identically in ANY deck.

Modifier children of ``schemeClr`` (``lumMod`` / ``lumOff`` / ``shade`` / ``tint``
/ ``alpha`` / ``satMod`` …) are preserved untouched — they carry the gradient and
3D-shading math, and DrawingML accepts them on ``srgbClr`` just as on ``schemeClr``.
"""
from __future__ import annotations

import posixpath
from dataclasses import dataclass
from lxml import etree

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"a": A, "p": P, "r": R}

# Top-level slide-shape kinds we lift. Everything else under spTree (the group's
# own nvGrpSpPr / grpSpPr props) is slide scaffolding, not diagram content.
SHAPE_TAGS = frozenset(
    {"sp", "grpSp", "pic", "graphicFrame", "cxnSp", "contentPart"}
)

REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
IMAGE_REL = REL_BASE + "image"
CHART_REL = REL_BASE + "chart"
LAYOUT_REL = REL_BASE + "slideLayout"
MASTER_REL = REL_BASE + "slideMaster"
THEME_REL = REL_BASE + "theme"


def local(elem) -> str:
    """Local tag name without the namespace brace."""
    return etree.QName(elem).localname


# ---------------------------------------------------------------------------
# Relationship resolution (walk slide -> layout -> master -> theme)
# ---------------------------------------------------------------------------

def rels_path(part: str) -> str:
    """``ppt/slides/slide1.xml`` -> ``ppt/slides/_rels/slide1.xml.rels``."""
    d = posixpath.dirname(part)
    return posixpath.join(d, "_rels", posixpath.basename(part) + ".rels")


def read_rels(zf, part: str) -> list[dict]:
    """Return the relationship records for *part* (empty list if it has none)."""
    try:
        data = zf.read(rels_path(part))
    except KeyError:
        return []
    root = etree.fromstring(data)
    out = []
    for rel in root:
        out.append(
            {
                "id": rel.get("Id"),
                "type": rel.get("Type"),
                "target": rel.get("Target"),
                "mode": rel.get("TargetMode"),
            }
        )
    return out


def resolve_target(part: str, target: str) -> str:
    """Resolve a (possibly ``../``-relative) rel target to an absolute zip path."""
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def first_target(zf, part: str, rel_type: str) -> str | None:
    for rel in read_rels(zf, part):
        if rel["type"] == rel_type:
            return resolve_target(part, rel["target"])
    return None


def resolve_master_and_theme(zf, slide_part: str) -> tuple[str, str]:
    """Walk slide -> layout -> master -> theme. Falls back to ``*1`` parts."""
    layout = first_target(zf, slide_part, LAYOUT_REL) or "ppt/slideLayouts/slideLayout1.xml"
    master = first_target(zf, layout, MASTER_REL) or "ppt/slideMasters/slideMaster1.xml"
    theme = first_target(zf, master, THEME_REL) or "ppt/theme/theme1.xml"
    return master, theme


# ---------------------------------------------------------------------------
# Theme flattening
# ---------------------------------------------------------------------------

@dataclass
class ThemeMaps:
    colors: dict   # theme slot -> hex  (dk1 / lt1 / dk2 / lt2 / accent1..6 / hlink / folHlink)
    clrmap: dict   # bg1 / tx1 / bg2 / tx2 / accent1.. -> theme slot (per the slide master)
    fonts: dict    # +mj-ea / +mn-lt / … -> concrete typeface

    def resolve_color(self, val: str) -> str | None:
        """``schemeClr`` val -> hex. Honors the (sometimes inverted) clrMap."""
        if val in self.clrmap:          # bg1 / tx1 / bg2 / tx2 indirect through clrMap
            return self.colors.get(self.clrmap[val])
        return self.colors.get(val)     # accent1..6 / dk1 / lt1 … used directly


def load_theme_maps(theme_xml: bytes, master_xml: bytes) -> ThemeMaps:
    theme = etree.fromstring(theme_xml)
    master = etree.fromstring(master_xml)

    colors: dict[str, str] = {}
    for c in theme.find(".//a:clrScheme", NS):
        srgb = c.find("a:srgbClr", NS)
        sysc = c.find("a:sysClr", NS)
        if srgb is not None:
            colors[local(c)] = srgb.get("val")
        elif sysc is not None:
            colors[local(c)] = sysc.get("lastClr")

    clrmap_el = master.find("p:clrMap", NS)
    clrmap = dict(clrmap_el.attrib) if clrmap_el is not None else {}

    fs = theme.find(".//a:fontScheme", NS)
    mj = fs.find("a:majorFont", NS)
    mn = fs.find("a:minorFont", NS)

    def typeface(font_el, script: str) -> str | None:
        e = font_el.find("a:" + script, NS)
        return e.get("typeface") if (e is not None and e.get("typeface")) else None

    fonts = {
        "+mj-lt": typeface(mj, "latin"),
        "+mn-lt": typeface(mn, "latin"),
        "+mj-ea": typeface(mj, "ea") or typeface(mj, "latin"),
        "+mn-ea": typeface(mn, "ea") or typeface(mn, "latin"),
        "+mj-cs": typeface(mj, "cs"),
        "+mn-cs": typeface(mn, "cs"),
    }
    return ThemeMaps(colors=colors, clrmap=clrmap, fonts=fonts)


def strip_foreign_rels(sp_tree, keep_rids: set) -> int:
    """Remove relationship references the component does not carry.

    Lifted shapes routinely point at parts that don't travel with a diagram:
    ``<p:custDataLst><p:tags r:id>`` (vendor tag parts), hyperlinks, sounds.
    Left in place, those ``r:id`` / ``r:embed`` values dangle in the target deck
    and PowerPoint rejects the file as corrupt. *keep_rids* are the media rIds
    that ``inject`` will remap; everything else is stripped. Returns the count
    of removed refs/elements.
    """
    removed = 0
    # custDataLst holds <p:tags r:id="..."> pointing at tag parts we don't carry.
    for cd in list(sp_tree.iter("{%s}custDataLst" % P)):
        parent = cd.getparent()
        if parent is not None:
            parent.remove(cd)
            removed += 1

    rid_attrs = ("{%s}embed" % R, "{%s}link" % R, "{%s}id" % R)
    drop_elems = {"hlinkClick", "hlinkHover", "tags", "snd"}
    for el in list(sp_tree.iter()):
        for attr in rid_attrs:
            v = el.get(attr)
            if v is not None and v not in keep_rids:
                if local(el) in drop_elems:
                    parent = el.getparent()
                    if parent is not None:
                        parent.remove(el)
                        removed += 1
                else:
                    del el.attrib[attr]
                    removed += 1
                break
    return removed


def flatten_theme(sp_tree, maps: ThemeMaps) -> dict:
    """In-place: ``schemeClr`` -> ``srgbClr`` and theme-font tokens -> typeface.

    Returns a counts dict for reporting / verification.
    """
    n_clr = n_skip = 0
    for sc in list(sp_tree.iter("{%s}schemeClr" % A)):
        hexv = maps.resolve_color(sc.get("val"))
        if hexv:
            sc.tag = "{%s}srgbClr" % A   # children (lumMod/shade/…) are kept verbatim
            sc.set("val", hexv)
            n_clr += 1
        else:
            n_skip += 1  # e.g. phClr — leave untouched

    n_font = 0
    for el in sp_tree.iter():
        tf = el.get("typeface")
        if tf in maps.fonts and maps.fonts[tf]:
            el.set("typeface", maps.fonts[tf])
            n_font += 1

    return {"colors": n_clr, "colors_unresolved": n_skip, "fonts": n_font}
