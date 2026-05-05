"""Per-slide composition: dispatches every ShapeNode through the right
converter, accumulates <defs>, and produces one final SVG string.

The output structure mirrors what svg_to_pptx expects so the deck can be
round-tripped:
    <svg viewBox="0 0 W H">
        <defs>
            <linearGradient id=.../>
            <marker id=.../>
            <filter id=.../>
        </defs>
        <!-- background -->
        <rect ... />        (slide background, if any)
        <g id="shape-1">...</g>
        <g id="shape-2">...</g>
        ...
    </svg>

Each top-level <g> wraps one shape and is treated by svg_to_pptx as an
animation anchor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from .color_resolver import ColorPalette
from .custgeom_to_svg import convert_custom_geom
from .effect_to_svg import convert_effects
from .emu_units import NS, fmt_num
from .fill_to_svg import resolve_fill
from .ln_to_svg import resolve_stroke
from .ooxml_loader import OoxmlPackage, PartRef, SlideRef
from .pic_to_svg import convert_picture
from .prstgeom_to_svg import GeomResult, convert_prst_geom
from .shape_walker import (
    CONNECTOR, GRAPHIC, GROUP, PICTURE, SHAPE,
    ShapeNode, get_background, walk_sp_tree,
)
from .txbody_to_svg import TextResult, convert_txbody


# ---------------------------------------------------------------------------
# AssemblyContext
# ---------------------------------------------------------------------------

@dataclass
class AssemblyContext:
    """Per-slide accumulator for unique IDs + media + defs."""

    palette: ColorPalette | None
    pkg: OoxmlPackage
    slide_part: PartRef
    theme_fonts: dict[str, str] = field(default_factory=dict)
    media_subdir: str = "assets"
    embed_images: bool = False
    keep_hidden: bool = False

    # Sequence counters (single-element lists so handlers can mutate)
    grad_seq: list[int] = field(default_factory=lambda: [0])
    marker_seq: list[int] = field(default_factory=lambda: [0])
    filter_seq: list[int] = field(default_factory=lambda: [0])
    shape_seq: list[int] = field(default_factory=lambda: [0])

    # Accumulated outputs
    defs: list[str] = field(default_factory=list)
    media: dict[str, bytes] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def assemble_slide(
    pkg: OoxmlPackage,
    slide: SlideRef,
    palette: ColorPalette | None,
    *,
    theme_fonts: dict[str, str] | None = None,
    media_subdir: str = "assets",
    embed_images: bool = False,
    keep_hidden: bool = False,
) -> tuple[str, dict[str, bytes]]:
    """Convert one slide to a complete SVG string + media files map."""
    ctx = AssemblyContext(
        palette=palette,
        pkg=pkg,
        slide_part=slide.part,
        theme_fonts=theme_fonts or {},
        media_subdir=media_subdir,
        embed_images=embed_images,
        keep_hidden=keep_hidden,
    )

    canvas_w, canvas_h = pkg.slide_size_px

    # Background (cSld/bg) — emit as the first body element.
    body_parts: list[str] = []
    bg_xml = _emit_background(slide, ctx, canvas_w, canvas_h)
    if bg_xml:
        body_parts.append(bg_xml)

    # Walk shapes
    nodes = walk_sp_tree(slide.part.xml)
    for node in nodes:
        chunk = _convert_node(node, ctx, top_level=True)
        if chunk:
            body_parts.append(chunk)

    # Compose final SVG
    defs_xml = "".join(ctx.defs) if ctx.defs else ""
    defs_block = f"<defs>{defs_xml}</defs>" if defs_xml else ""

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
        f'width="{fmt_num(canvas_w)}" height="{fmt_num(canvas_h)}" '
        f'viewBox="0 0 {fmt_num(canvas_w)} {fmt_num(canvas_h)}">'
        f"{defs_block}"
        + "\n".join(body_parts)
        + "</svg>"
    )
    return svg, ctx.media


# ---------------------------------------------------------------------------
# Per-node dispatch
# ---------------------------------------------------------------------------

def _convert_node(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    if node.hidden and not ctx.keep_hidden:
        return ""
    if node.kind == SHAPE:
        return _convert_shape(node, ctx, top_level=top_level)
    if node.kind == PICTURE:
        return _convert_picture(node, ctx, top_level=top_level)
    if node.kind == CONNECTOR:
        return _convert_connector(node, ctx, top_level=top_level)
    if node.kind == GROUP:
        return _convert_group(node, ctx, top_level=top_level)
    if node.kind == GRAPHIC:
        return _convert_graphic_fallback(node, ctx, top_level=top_level)
    return ""


# ---------------------------------------------------------------------------
# Shape (<p:sp>)
# ---------------------------------------------------------------------------

def _convert_shape(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    sp_pr = node.xml.find("p:spPr", NS)

    # Geometry
    geom_xml = _build_geometry_xml(node, sp_pr, ctx)

    # Text body (a:txBody)
    tx_body = node.xml.find("p:txBody", NS)
    text_result = convert_txbody(
        tx_body, node.xfrm, ctx.palette,
        theme_fonts=ctx.theme_fonts,
    ) if tx_body is not None else TextResult()

    inner = (geom_xml + ("\n" + text_result.svg if text_result.svg else ""))
    return _wrap_shape_group(inner, node, ctx, top_level=top_level)


def _build_geometry_xml(node: ShapeNode, sp_pr: ET.Element | None,
                        ctx: AssemblyContext) -> str:
    """Build the SVG geometry element with fill/stroke/effect attributes."""
    # Resolve geometry
    prst_geom = sp_pr.find("a:prstGeom", NS) if sp_pr is not None else None
    cust_geom = sp_pr.find("a:custGeom", NS) if sp_pr is not None else None

    geom: GeomResult | None = None
    if prst_geom is not None:
        prst = prst_geom.attrib.get("prst", "rect")
        geom = convert_prst_geom(prst, node.xfrm, prst_geom)
        if geom is None:
            # Unknown prst — fall back to rect bounding box
            geom = convert_prst_geom("rect", node.xfrm, None)
    elif cust_geom is not None:
        d = convert_custom_geom(cust_geom, node.xfrm)
        if d:
            geom = GeomResult(tag="path", path_d=d)
    else:
        # No geometry hint at all — render bounding rect
        geom = convert_prst_geom("rect", node.xfrm, None)

    if geom is None or node.xfrm.w <= 0 or node.xfrm.h <= 0:
        return ""

    # Fill / stroke / effect
    fill = resolve_fill(sp_pr, ctx.palette,
                        id_prefix="g", id_seq=ctx.grad_seq)
    stroke = resolve_stroke(sp_pr, ctx.palette,
                            id_prefix="m", id_seq=ctx.marker_seq)
    filter_id, effect_defs = convert_effects(sp_pr, ctx.palette,
                                             id_prefix="fx",
                                             id_seq=ctx.filter_seq)

    ctx.defs.extend(fill.defs)
    ctx.defs.extend(stroke.defs)
    ctx.defs.extend(effect_defs)

    attrs = {**fill.attrs, **stroke.attrs}
    if filter_id is not None:
        attrs["filter"] = f"url(#{filter_id})"

    # Default fill / stroke when not specified by spPr (matches PowerPoint
    # behavior: a:noFill on shape-level fill if there's a txBody, else any
    # explicit fill present in spPr should already have been captured).
    if "fill" not in attrs:
        # Default: transparent so the shape doesn't paint over text/images.
        # PowerPoint's actual default is theme accent + style, but mimicking
        # that requires reading slideMaster styles which is out of v1 scope.
        attrs["fill"] = "none"
    if "stroke" not in attrs:
        # Spec default for shapes is no stroke unless ln says otherwise.
        # Skip emitting stroke="none" to keep markup tight.
        pass

    geom_attrs_xml = _attrs_to_xml({**geom.attrs, **attrs})

    if geom.tag == "path":
        return f'<path d="{geom.path_d}"{geom_attrs_xml}/>'
    if geom.tag in ("polygon", "polyline"):
        return f'<{geom.tag} points="{geom.points}"{geom_attrs_xml}/>'
    return f"<{geom.tag}{geom_attrs_xml}/>"


# ---------------------------------------------------------------------------
# Picture (<p:pic>)
# ---------------------------------------------------------------------------

def _convert_picture(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    result = convert_picture(
        node.xml, node.xfrm, ctx.slide_part, ctx.pkg,
        media_subdir=ctx.media_subdir,
        embed_inline=ctx.embed_images,
    )
    if not result.svg:
        return ""
    ctx.media.update(result.media)
    return _wrap_shape_group(result.svg, node, ctx, top_level=top_level)


# ---------------------------------------------------------------------------
# Connector (<p:cxnSp>)
# ---------------------------------------------------------------------------

def _convert_connector(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    sp_pr = node.xml.find("p:spPr", NS)
    geom_xml = _build_geometry_xml(node, sp_pr, ctx)
    return _wrap_shape_group(geom_xml, node, ctx, top_level=top_level)


# ---------------------------------------------------------------------------
# Group (<p:grpSp>)
# ---------------------------------------------------------------------------

def _convert_group(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    """Render group contents flat (children already remapped to slide space)."""
    inner_parts: list[str] = []
    for child in node.children:
        chunk = _convert_node(child, ctx, top_level=False)
        if chunk:
            inner_parts.append(chunk)
    if not inner_parts:
        return ""
    inner = "\n".join(inner_parts)
    return _wrap_shape_group(inner, node, ctx, top_level=top_level)


# ---------------------------------------------------------------------------
# Graphic frame fallback (<p:graphicFrame>)
# ---------------------------------------------------------------------------

def _convert_graphic_fallback(node: ShapeNode, ctx: AssemblyContext,
                              *, top_level: bool) -> str:
    """v1 fallback: render the bounding box with a dashed outline + label."""
    # Detect what's inside (chart / table / smartArt) for the comment.
    graphic_data = node.xml.find("a:graphic/a:graphicData", NS)
    uri = graphic_data.attrib.get("uri", "graphicFrame") if graphic_data is not None else "graphicFrame"
    label = uri.rsplit("/", 1)[-1]
    placeholder = (
        f'<rect x="{fmt_num(node.xfrm.x)}" y="{fmt_num(node.xfrm.y)}" '
        f'width="{fmt_num(node.xfrm.w)}" height="{fmt_num(node.xfrm.h)}" '
        f'fill="none" stroke="#999999" stroke-dasharray="4 4"/>'
        f'<text x="{fmt_num(node.xfrm.x + node.xfrm.w / 2)}" '
        f'y="{fmt_num(node.xfrm.y + node.xfrm.h / 2)}" '
        f'text-anchor="middle" font-size="14" fill="#999999">'
        f"[{_xml_escape(label)}]</text>"
    )
    return _wrap_shape_group(placeholder, node, ctx, top_level=top_level)


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def _emit_background(slide: SlideRef, ctx: AssemblyContext,
                     w: float, h: float) -> str:
    """Inspect <p:bg> on slide / layout / master in inheritance order."""
    for part in (slide.part, slide.layout, slide.master):
        if part is None:
            continue
        bg = get_background(part.xml)
        if bg is None:
            continue
        bg_pr = bg.find("p:bgPr", NS)
        if bg_pr is None:
            continue
        fill = resolve_fill(bg_pr, ctx.palette,
                            id_prefix="bg", id_seq=ctx.grad_seq)
        ctx.defs.extend(fill.defs)
        if not fill.attrs:
            return ""
        # Convert dict to attributes
        attrs_xml = _attrs_to_xml(fill.attrs)
        return (f'<rect x="0" y="0" width="{fmt_num(w)}" height="{fmt_num(h)}"'
                f"{attrs_xml}/>")
    return ""


# ---------------------------------------------------------------------------
# Wrap / utilities
# ---------------------------------------------------------------------------

def _wrap_shape_group(inner: str, node: ShapeNode, ctx: AssemblyContext,
                      *, top_level: bool) -> str:
    """Wrap a shape's body in a <g> that carries the transform (rotation /
    flip) and an id for animation anchoring."""
    if not inner.strip():
        return ""

    transform = node.xfrm.to_svg_transform()
    ctx.shape_seq[0] += 1
    seq = ctx.shape_seq[0]
    sid = node.spid or str(seq)
    g_id = f"shape-{sid}"

    attrs: list[str] = [f'id="{g_id}"']
    if node.name:
        attrs.append(f'data-name="{_xml_escape(node.name)}"')
    if node.placeholder is not None and node.placeholder.type:
        attrs.append(f'data-ph-type="{_xml_escape(node.placeholder.type)}"')
    if transform:
        attrs.append(f'transform="{transform}"')
    return f"<g {' '.join(attrs)}>\n{inner}\n</g>"


def _attrs_to_xml(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    return "".join(f' {k}="{v}"' for k, v in attrs.items())


def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
