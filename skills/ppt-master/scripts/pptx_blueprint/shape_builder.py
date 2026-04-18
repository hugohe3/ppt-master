"""DrawingML shape builder — one ResolvedShape -> one complete IR Shape.

This module consolidates P2 work: fill, stroke, text, custGeom, and prstGeom
resolution. It replaces the P1 skeleton `_build_shape` in xml_parser.py (which
delegates here starting in P2-e).

Flow:
    resolve_shape(slide_sp, ctx) -> ResolvedShape
    build_shape(resolved, ...)   -> Shape (complete)

Coordinate convention: all bbox and local coordinates are in viewBox pixels
(post-EMU conversion). DrawingML custGeom path coordinates use a local unit
system defined by `<a:pathLst><a:path w=... h=...>`; we normalize them into
local px during conversion.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .inheritance import InheritanceContext, ResolvedShape, resolve_shape
from .ir import (
    Fill, GradientSpec, GradientStop, Shape, Stroke,
    TextContent, TextParagraph, TextRun, Theme,
    emu_to_px, dml_font_size_to_pt, dml_angle_to_deg,
)
from .prstgeom_registry import parse_avlst, render_preset
from .theme import resolve_color_element


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

# DrawingML line width is in EMU (1 pt = 12700 EMU); 1 px ≈ 9525 EMU at 96 dpi.
# Convention: we use the "line width in px" = width_emu / EMU_PER_PX.
from .ir import EMU_PER_PX


# ---------------------------------------------------------------------------
# Geometry: bbox, rotation
# ---------------------------------------------------------------------------

def parse_bbox(resolved: ResolvedShape) -> tuple[float, float, float, float]:
    """Extract (x, y, w, h) in viewBox px from the inheritance chain."""
    off = resolved.find_first(".//a:xfrm/a:off")
    ext = resolved.find_first(".//a:xfrm/a:ext")

    x = emu_to_px(int(off.attrib.get("x", "0"))) if off is not None else 0.0
    y = emu_to_px(int(off.attrib.get("y", "0"))) if off is not None else 0.0
    w = emu_to_px(int(ext.attrib.get("cx", "0"))) if ext is not None else 0.0
    h = emu_to_px(int(ext.attrib.get("cy", "0"))) if ext is not None else 0.0
    return (x, y, w, h)


def parse_rotation(resolved: ResolvedShape) -> tuple[float, bool, bool]:
    """Read (rotation in deg, flipH, flipV) from <a:xfrm>."""
    xfrm = resolved.find_first(".//a:xfrm")
    if xfrm is None:
        return 0.0, False, False

    rot_raw = xfrm.attrib.get("rot", "0")
    try:
        rot = dml_angle_to_deg(int(rot_raw))
    except ValueError:
        rot = 0.0
    flip_h = xfrm.attrib.get("flipH", "0") == "1"
    flip_v = xfrm.attrib.get("flipV", "0") == "1"
    return rot, flip_h, flip_v


# ---------------------------------------------------------------------------
# Fill (solid / gradient / image / none)
# ---------------------------------------------------------------------------

def build_fill(
    resolved: ResolvedShape,
    theme: Theme,
    slide_rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
) -> Fill | None:
    """Parse the first fill element in the inheritance chain.

    Returns None when no fill element is present (caller may default to 'none'
    or inherit from run/text context).
    """
    # Look in the most specific spPr first
    for root in (resolved.slide_sp, resolved.layout_sp, resolved.master_sp):
        if root is None:
            continue
        sp_pr = root.find(".//p:spPr", NS)
        if sp_pr is None:
            continue
        fill = _extract_fill_from(sp_pr, theme, slide_rels, copied_assets)
        if fill is not None:
            return fill
    return None


def _extract_fill_from(
    parent: ET.Element,
    theme: Theme,
    slide_rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
) -> Fill | None:
    """Look at the fill-bearing children of a parent element (spPr, rPr, etc.)."""
    for child in parent:
        if not isinstance(child.tag, str):
            continue
        tag = child.tag.split("}", 1)[-1]

        if tag == "noFill":
            return Fill(kind='none')

        if tag == "solidFill":
            color, alpha = resolve_color_element(child, theme)
            if color is None:
                continue
            return Fill(kind='solid', color=color, opacity=alpha)

        if tag == "gradFill":
            grad = _parse_gradient(child, theme)
            if grad is None:
                continue
            return Fill(kind='gradient', gradient=grad)

        if tag == "blipFill":
            blip = child.find("a:blip", NS)
            if blip is None:
                continue
            rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
            if not rel_id:
                continue
            rel = slide_rels.get(rel_id)
            if not rel or rel["type"] != IMAGE_REL:
                continue
            return Fill(
                kind='image',
                image_ref=copied_assets.get(rel["target"]),
            )

    return None


def _parse_gradient(grad_elem: ET.Element, theme: Theme) -> GradientSpec | None:
    """Parse <a:gradFill> into a GradientSpec."""
    stops_lst = grad_elem.find("a:gsLst", NS)
    if stops_lst is None:
        return None

    stops: list[GradientStop] = []
    for gs in stops_lst.findall("a:gs", NS):
        pos_raw = gs.attrib.get("pos", "0")
        try:
            pos = int(pos_raw) / 100000.0
        except ValueError:
            pos = 0.0
        color, alpha = resolve_color_element(gs, theme)
        if color is None:
            continue
        stops.append(GradientStop(pos=pos, color=color, opacity=alpha))

    if not stops:
        return None

    lin = grad_elem.find("a:lin", NS)
    path_elem = grad_elem.find("a:path", NS)

    if lin is not None:
        ang_raw = lin.attrib.get("ang", "0")
        try:
            angle = dml_angle_to_deg(int(ang_raw))
        except ValueError:
            angle = 0.0
        return GradientSpec(kind='linear', stops=stops, angle_deg=angle)

    if path_elem is not None:
        # radial or rectangular. Use circular default.
        return GradientSpec(kind='radial', stops=stops)

    # No direction info — default to horizontal linear
    return GradientSpec(kind='linear', stops=stops, angle_deg=0.0)


# ---------------------------------------------------------------------------
# Stroke
# ---------------------------------------------------------------------------

_DML_TO_SVG_DASH = {
    'solid': 'solid',
    'dash': 'dash',
    'dashDot': 'dashDot',
    'dot': 'dot',
    'lgDash': 'lgDash',
    'lgDashDot': 'dashDot',
    'lgDashDotDot': 'dashDot',
    'sysDash': 'dash',
    'sysDashDot': 'dashDot',
    'sysDashDotDot': 'dashDot',
    'sysDot': 'dot',
}


def build_stroke(
    resolved: ResolvedShape,
    theme: Theme,
) -> Stroke | None:
    """Parse the first <a:ln> in the inheritance chain."""
    for root in (resolved.slide_sp, resolved.layout_sp, resolved.master_sp):
        if root is None:
            continue
        ln = root.find(".//p:spPr/a:ln", NS)
        if ln is None:
            continue

        # Explicit noFill -> no stroke
        no_fill = ln.find("a:noFill", NS)
        if no_fill is not None:
            return None

        solid = ln.find("a:solidFill", NS)
        color: str | None = None
        opacity: float = 1.0
        if solid is not None:
            c, a = resolve_color_element(solid, theme)
            if c:
                color = c
                opacity = a

        # If no color was found, the line is implicitly absent in v1.
        if color is None:
            return None

        # Width: EMU -> px. Default is 9525 EMU (1 px).
        width_emu_raw = ln.attrib.get("w", "9525")
        try:
            width_px = int(width_emu_raw) / EMU_PER_PX
        except ValueError:
            width_px = 1.0

        dash_elem = ln.find("a:prstDash", NS)
        dash = None
        if dash_elem is not None:
            dash_val = dash_elem.attrib.get("val")
            dash = _DML_TO_SVG_DASH.get(dash_val) if dash_val else None

        cap = ln.attrib.get("cap", "flat")
        if cap not in ("flat", "rnd", "sq"):
            cap = "flat"

        return Stroke(
            color=color,
            width=width_px,
            opacity=opacity,
            dash=dash,
            cap=cap,
        )

    return None


# ---------------------------------------------------------------------------
# Text (txBody -> TextContent)
# ---------------------------------------------------------------------------

def build_text(
    resolved: ResolvedShape,
    theme: Theme,
) -> TextContent | None:
    """Parse <p:txBody> into a TextContent. Returns None for shapes with no text.

    P2: reads directly from the slide element's txBody. Layout/master inherited
    text styles (via p:titleStyle / p:bodyStyle on the master) are deferred.
    """
    txBody = resolved.slide_sp.find(".//p:txBody", NS)
    if txBody is None:
        # Placeholder shapes may have txBody only in the layout/master
        for fallback in (resolved.layout_sp, resolved.master_sp):
            if fallback is None:
                continue
            txBody = fallback.find(".//p:txBody", NS)
            if txBody is not None:
                break
    if txBody is None:
        return None

    body_pr = txBody.find("a:bodyPr", NS)
    anchor: str = "t"
    auto_fit = False
    if body_pr is not None:
        anchor = body_pr.attrib.get("anchor", "t")
        if anchor not in ("t", "ctr", "b"):
            anchor = "t"
        if body_pr.find("a:normAutofit", NS) is not None:
            auto_fit = True

    paragraphs: list[TextParagraph] = []
    for p in txBody.findall("a:p", NS):
        paragraph = _parse_paragraph(p, theme)
        paragraphs.append(paragraph)

    # Strip trailing empty paragraphs (common artefact of PowerPoint exports)
    while paragraphs and not _paragraph_has_text(paragraphs[-1]):
        paragraphs.pop()

    if not paragraphs:
        return None

    return TextContent(
        paragraphs=paragraphs,
        anchor=anchor,  # type: ignore[arg-type]
        auto_fit=auto_fit,
    )


def _parse_paragraph(p_elem: ET.Element, theme: Theme) -> TextParagraph:
    p_pr = p_elem.find("a:pPr", NS)
    align: str = "l"
    bullet: str | None = None
    indent_px: float = 0.0
    line_spacing_pct: float = 100.0

    if p_pr is not None:
        align_raw = p_pr.attrib.get("algn", "l")
        if align_raw in ("l", "ctr", "r", "just"):
            align = align_raw
        # indent: marL / indent are in EMU
        try:
            mar_l = int(p_pr.attrib.get("marL", "0"))
            indent_px = emu_to_px(mar_l)
        except ValueError:
            pass
        # bullets
        bu_char = p_pr.find("a:buChar", NS)
        if bu_char is not None:
            bullet = bu_char.attrib.get("char")
        elif p_pr.find("a:buAutoNum", NS) is not None:
            bullet = "1."
        elif p_pr.find("a:buNone", NS) is not None:
            bullet = None
        # line spacing
        lnSpc = p_pr.find("a:lnSpc/a:spcPct", NS)
        if lnSpc is not None:
            try:
                line_spacing_pct = int(lnSpc.attrib.get("val", "100000")) / 1000.0
            except ValueError:
                pass

    runs: list[TextRun] = []
    for r in p_elem.findall("a:r", NS):
        run = _parse_run(r, theme)
        if run is not None:
            runs.append(run)

    return TextParagraph(
        runs=runs,
        align=align,  # type: ignore[arg-type]
        bullet=bullet,
        indent_px=indent_px,
        line_spacing_pct=line_spacing_pct,
    )


def _parse_run(r_elem: ET.Element, theme: Theme) -> TextRun | None:
    t = r_elem.find("a:t", NS)
    text = t.text if t is not None and t.text is not None else ""
    if not text:
        return None

    rPr = r_elem.find("a:rPr", NS)
    font_size: float | None = None
    font_latin: str | None = None
    font_ea: str | None = None
    bold = False
    italic = False
    color: str | None = None

    if rPr is not None:
        sz_raw = rPr.attrib.get("sz")
        if sz_raw:
            try:
                font_size = dml_font_size_to_pt(int(sz_raw))
            except ValueError:
                pass
        bold = rPr.attrib.get("b", "0") in ("1", "true")
        italic = rPr.attrib.get("i", "0") in ("1", "true")

        latin = rPr.find("a:latin", NS)
        if latin is not None:
            font_latin = latin.attrib.get("typeface") or None
        ea = rPr.find("a:ea", NS)
        if ea is not None:
            font_ea = ea.attrib.get("typeface") or None

        solid_fill = rPr.find("a:solidFill", NS)
        if solid_fill is not None:
            c, _ = resolve_color_element(solid_fill, theme)
            if c:
                color = c

    return TextRun(
        text=text,
        font_size=font_size,
        font_latin=font_latin,
        font_ea=font_ea,
        bold=bold,
        italic=italic,
        color=color,
    )


def _paragraph_has_text(p: TextParagraph) -> bool:
    return any(r.text.strip() for r in p.runs)


# ---------------------------------------------------------------------------
# Geometry: prstGeom + custGeom
# ---------------------------------------------------------------------------

def build_geometry(
    resolved: ResolvedShape,
    width: float,
    height: float,
    warnings: list[str],
) -> tuple[str, str | None, str | None, float, dict[str, int]]:
    """Return (kind, preset_name, path_d, corner_radius, avlst_dict).

    kind matches Shape.kind: one of 'rect', 'roundRect', 'ellipse', 'line',
    'path', 'prstGeom' (fallback), or 'unknown'.

    For kind='rect'/'ellipse', emitter uses the bbox directly.
    For 'roundRect', corner_radius carries the rx/ry.
    For 'path', path_d has an SVG `d` value in LOCAL coordinates (0..w, 0..h).
    """
    prst = resolved.find_first(".//p:spPr/a:prstGeom")
    if prst is not None:
        preset_name = prst.attrib.get("prst", "rect")
        avlst = parse_avlst(prst.find("a:avLst", NS))
        render = render_preset(preset_name, width, height, avlst)
        if render.is_fallback:
            warnings.append(f"Unknown prstGeom preset '{preset_name}' — fallback to rect")
            return "prstGeom", preset_name, None, 0.0, avlst
        if render.kind == "path":
            return "path", preset_name, render.path_d, 0.0, avlst
        if render.kind == "roundRect":
            return "roundRect", preset_name, None, render.corner_radius, avlst
        # rect / ellipse / line
        return render.kind, preset_name, None, 0.0, avlst

    custGeom = resolved.find_first(".//p:spPr/a:custGeom")
    if custGeom is not None:
        path_d = _custgeom_to_svg_path(custGeom, width, height)
        if path_d is not None:
            return "path", None, path_d, 0.0, {}

    return "unknown", None, None, 0.0, {}


# ---------------------------------------------------------------------------
# custGeom -> SVG path
# ---------------------------------------------------------------------------

def _custgeom_to_svg_path(
    cust_elem: ET.Element,
    width: float,
    height: float,
) -> str | None:
    """Convert <a:custGeom><a:pathLst><a:path> commands into a single SVG `d`.

    DrawingML path commands:
        <a:moveTo><a:pt x=.. y=../></a:moveTo>        -> M
        <a:lnTo><a:pt x=.. y=../></a:lnTo>            -> L
        <a:cubicBezTo><a:pt/><a:pt/><a:pt/></a:cubicBezTo>  -> C
        <a:quadBezTo><a:pt/><a:pt/></a:quadBezTo>     -> Q
        <a:arcTo wR=.. hR=.. stAng=.. swAng=../>      -> A (approximated as L for v1)
        <a:close/>                                    -> Z

    The path's intrinsic coordinate system is declared on <a:path w=.. h=..>.
    We rescale to local px (0..width, 0..height) proportionally.
    """
    path_lst = cust_elem.find("a:pathLst", NS)
    if path_lst is None:
        return None

    segments: list[str] = []

    for path in path_lst.findall("a:path", NS):
        try:
            path_w = float(path.attrib.get("w", "0"))
            path_h = float(path.attrib.get("h", "0"))
        except ValueError:
            path_w = path_h = 0.0

        sx = (width / path_w) if path_w > 0 else 1.0
        sy = (height / path_h) if path_h > 0 else 1.0

        for cmd in path:
            if not isinstance(cmd.tag, str):
                continue
            local = cmd.tag.split("}", 1)[-1]

            if local == "moveTo":
                pt = cmd.find("a:pt", NS)
                if pt is None:
                    continue
                x, y = _scale_pt(pt, sx, sy)
                segments.append(f"M {x:.3f},{y:.3f}")

            elif local == "lnTo":
                pt = cmd.find("a:pt", NS)
                if pt is None:
                    continue
                x, y = _scale_pt(pt, sx, sy)
                segments.append(f"L {x:.3f},{y:.3f}")

            elif local == "cubicBezTo":
                pts = cmd.findall("a:pt", NS)
                if len(pts) < 3:
                    continue
                c1 = _scale_pt(pts[0], sx, sy)
                c2 = _scale_pt(pts[1], sx, sy)
                end = _scale_pt(pts[2], sx, sy)
                segments.append(
                    f"C {c1[0]:.3f},{c1[1]:.3f} "
                    f"{c2[0]:.3f},{c2[1]:.3f} "
                    f"{end[0]:.3f},{end[1]:.3f}"
                )

            elif local == "quadBezTo":
                pts = cmd.findall("a:pt", NS)
                if len(pts) < 2:
                    continue
                c = _scale_pt(pts[0], sx, sy)
                end = _scale_pt(pts[1], sx, sy)
                segments.append(f"Q {c[0]:.3f},{c[1]:.3f} {end[0]:.3f},{end[1]:.3f}")

            elif local == "arcTo":
                # v1: approximate arc endpoint with a line. A real implementation
                # would convert (stAng, swAng, wR, hR) to SVG arc params. Deferred.
                # stAng/swAng are in 1/60000 deg. We compute the endpoint assuming
                # the arc starts at the current pen position, then move to end.
                # Without tracking the pen, we fall back to skipping — acceptable
                # because custGeom arcs are rare in real templates.
                continue

            elif local == "close":
                segments.append("Z")

    if not segments:
        return None
    return " ".join(segments)


def _scale_pt(pt_elem: ET.Element, sx: float, sy: float) -> tuple[float, float]:
    try:
        x = float(pt_elem.attrib.get("x", "0")) * sx
        y = float(pt_elem.attrib.get("y", "0")) * sy
    except ValueError:
        x = y = 0.0
    return (x, y)


# ---------------------------------------------------------------------------
# Image reference
# ---------------------------------------------------------------------------

def _read_image_ref(
    slide_sp: ET.Element,
    slide_rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
) -> tuple[str | None, tuple[float, float, float, float] | None]:
    """Resolve <a:blip r:embed=".." /> to (asset_filename, srcRect crop) or (None, None)."""
    blip = slide_sp.find(".//p:blipFill/a:blip", NS)
    if blip is None:
        blip = slide_sp.find(".//a:blip", NS)
    if blip is None:
        return None, None

    rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
    if not rel_id:
        return None, None
    rel = slide_rels.get(rel_id)
    if not rel or rel["type"] != IMAGE_REL:
        return None, None

    asset = copied_assets.get(rel["target"])

    # srcRect crop (l/t/r/b as percent-mille fractions of original image bounds)
    crop = None
    src_rect = slide_sp.find(".//p:blipFill/a:srcRect", NS)
    if src_rect is not None:
        try:
            crop = (
                int(src_rect.attrib.get("l", "0")) / 100000.0,
                int(src_rect.attrib.get("t", "0")) / 100000.0,
                int(src_rect.attrib.get("r", "0")) / 100000.0,
                int(src_rect.attrib.get("b", "0")) / 100000.0,
            )
        except ValueError:
            crop = None

    return asset, crop


# ---------------------------------------------------------------------------
# Main entry: build_shape
# ---------------------------------------------------------------------------

def build_shape(
    slide_sp: ET.Element,
    ctx: InheritanceContext,
    slide_rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
    theme: Theme,
    warnings: list[str],
) -> Shape | None:
    """Build a complete IR Shape from a slide element (P2 full version).

    For group shapes, child <p:sp>/<p:pic>/<p:grpSp>/<p:graphicFrame> elements
    are recursively built and attached as children.
    """
    resolved = resolve_shape(slide_sp, ctx)

    cnv = slide_sp.find(".//p:cNvPr", NS)
    source_id = cnv.attrib.get("id") if cnv is not None else None
    source_name = cnv.attrib.get("name") if cnv is not None else None

    tag = slide_sp.tag.split("}", 1)[-1]
    bbox = parse_bbox(resolved)
    rot, flip_h, flip_v = parse_rotation(resolved)
    ph_key = resolved.ph_key or (None, None)

    # Dispatch by element tag
    if tag == "pic":
        kind = "image"
        preset = None
        path_d = None
        corner_radius = 0.0
        image_ref, image_crop = _read_image_ref(slide_sp, slide_rels, copied_assets)
    elif tag == "grpSp":
        kind = "group"
        preset = None
        path_d = None
        corner_radius = 0.0
        image_ref = None
        image_crop = None
    elif tag == "graphicFrame":
        warnings.append(
            f"graphicFrame (id={source_id}, name={source_name}) not supported "
            "in v1 — chart/smartArt/table will be skipped"
        )
        kind = "unknown"
        preset = None
        path_d = None
        corner_radius = 0.0
        image_ref = None
        image_crop = None
    else:
        # <p:sp>: resolve geometry
        _, _, w, h = bbox
        kind, preset, path_d, corner_radius, _avlst = build_geometry(
            resolved, w, h, warnings,
        )
        image_ref = None
        image_crop = None

    shape = Shape(
        kind=kind,  # type: ignore[arg-type]
        bbox=bbox,
        rotation=rot,
        flip_h=flip_h,
        flip_v=flip_v,
        preset_name=preset,
        path_d=path_d,
        corner_radius=corner_radius,
        source_id=source_id,
        source_name=source_name,
        ph_type=ph_key[0],
        ph_idx=int(ph_key[1]) if ph_key[1] and ph_key[1].isdigit() else None,
        image_ref=image_ref,
        image_crop=image_crop,
    )

    # Fill / stroke (skip for pure text-containers and groups)
    if kind not in ("group", "unknown"):
        shape.fill = build_fill(resolved, theme, slide_rels, copied_assets)
        shape.stroke = build_stroke(resolved, theme)

    # Text
    shape.text = build_text(resolved, theme)

    # Recurse into group children
    if kind == "group":
        for child in slide_sp:
            if not isinstance(child.tag, str):
                continue
            local = child.tag.split("}", 1)[-1]
            if local in ("sp", "pic", "grpSp", "graphicFrame"):
                child_shape = build_shape(
                    child, ctx, slide_rels, copied_assets, theme, warnings,
                )
                if child_shape is not None:
                    shape.children.append(child_shape)

    return shape
