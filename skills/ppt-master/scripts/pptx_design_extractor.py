#!/usr/bin/env python3
"""Enhanced PPTX design profile extractor.

Extracts a comprehensive design profile from a PPTX file for template creation:

- Theme colors and font scheme (from theme.xml)
- Gradient fills used across shapes
- Actual color usage frequency distribution
- Font family and size hierarchy
- Background patterns (solid, gradient, image)
- Shape style patterns (fills, outlines, effects)
- Slide composition analysis (cover, TOC, content, ending patterns)
- Optional PNG screenshots of key slides for visual analysis

Output:
    <output_dir>/design_profile.json  — comprehensive design metadata
    <output_dir>/slide_previews/      — PNG screenshots (when --screenshots)
    <output_dir>/key_slides/          — Key slide SVGs (when --key-slides)

Usage:
    python3 pptx_design_extractor.py <source.pptx> [-o <output_dir>] [--screenshots] [--key-slides]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

# ---------------------------------------------------------------------------
# XML namespaces
# ---------------------------------------------------------------------------
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_PT = 12700
EMU_PER_INCH = 914400

SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
LAYOUT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
MASTER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
THEME_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

# Page type detection keywords
THANKS_KEYWORDS = ("thank", "thanks", "q&a", "qa", "contact", "致谢", "谢谢", "感谢", "答疑", "联系方式")
TOC_KEYWORDS = ("agenda", "contents", "content", "outline", "目录", "议程")
CHAPTER_KEYWORDS = ("chapter", "part", "section", "章节", "部分", "PART")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _load_xml(zf: ZipFile, path: str) -> ET.Element | None:
    try:
        with zf.open(path) as f:
            return ET.parse(f).getroot()
    except (KeyError, ET.ParseError):
        return None


def _rels_path(part_path: str) -> str:
    from posixpath import join, dirname, basename
    return join(dirname(part_path), "_rels", basename(part_path) + ".rels")


def _parse_rels(zf: ZipFile, part_path: str) -> dict[str, dict[str, str]]:
    root = _load_xml(zf, _rels_path(part_path))
    if root is None:
        return {}
    rels = {}
    for rel in root.findall("rel:Relationship", NS):
        rid = rel.attrib.get("Id", "")
        target = rel.attrib.get("Target", "")
        rtype = rel.attrib.get("Type", "")
        if rid and target and rtype:
            # Normalize target path
            if not target.startswith("/"):
                from posixpath import normpath, dirname
                base = dirname(part_path)
                target = normpath(f"{base}/{target}")
            rels[rid] = {"type": rtype, "target": target}
    return rels


def _resolve_rel(rels: dict, rel_type: str) -> str | None:
    for rel in rels.values():
        if rel["type"] == rel_type:
            return rel["target"]
    return None


def _emu_to_pt(emu: int) -> float:
    return round(emu / EMU_PER_PT, 1)


def _emu_to_px(emu: int) -> int:
    return int(round(emu / EMU_PER_INCH * 96))


# ---------------------------------------------------------------------------
# Color extraction
# ---------------------------------------------------------------------------
def _extract_color(elem: ET.Element) -> str | None:
    """Extract a color value from an element, trying srgbClr then sysClr."""
    srgb = elem.find("a:srgbClr", NS)
    if srgb is not None and srgb.attrib.get("val"):
        return f"#{srgb.attrib['val']}"
    sys = elem.find("a:sysClr", NS)
    if sys is not None:
        last = sys.attrib.get("lastClr")
        if last:
            return f"#{last}"
    return None


def _extract_gradient(grad_elem: ET.Element) -> dict | None:
    """Extract gradient fill details."""
    gs_lst = grad_elem.find("a:gsLst", NS)
    if gs_lst is None:
        return None
    stops = []
    for gs in gs_lst:
        pos = gs.attrib.get("pos", "0")
        color = _extract_color(gs)
        if color:
            stops.append({"position": int(pos), "color": color})
    if not stops:
        return None
    result = {"type": "gradient", "stops": stops}
    lin = grad_elem.find("a:lin", NS)
    if lin is not None:
        ang = lin.attrib.get("ang")
        if ang:
            result["angle_deg"] = int(ang) / 60000
    path = grad_elem.find("a:path", NS)
    if path is not None:
        result["path_type"] = path.attrib.get("path", "rect")
    tile = grad_elem.find("a:tileRect", NS)
    if tile is not None:
        result["tiled"] = True
    return result


def _extract_fill(sp_pr: ET.Element) -> dict | None:
    """Extract fill info from shape properties."""
    if sp_pr is None:
        return None
    # Check order: noFill, solidFill, gradFill, pattFill, blipFill
    if sp_pr.find("a:noFill", NS) is not None:
        return {"type": "none"}
    solid = sp_pr.find("a:solidFill", NS)
    if solid is not None:
        color = _extract_color(solid)
        if color:
            alpha_elem = solid.find(".//a:alpha", NS)
            alpha = None
            if alpha_elem is not None:
                try:
                    alpha = int(alpha_elem.attrib.get("val", "100000")) / 1000
                except ValueError:
                    pass
            result = {"type": "solid", "color": color}
            if alpha is not None and alpha < 100:
                result["alpha_pct"] = alpha
            return result
    grad = sp_pr.find("a:gradFill", NS)
    if grad is not None:
        return _extract_gradient(grad)
    patt = sp_pr.find("a:pattFill", NS)
    if patt is not None:
        fg = patt.find("a:fgClr", NS)
        bg = patt.find("a:bgClr", NS)
        result = {"type": "pattern"}
        if fg is not None:
            result["foreground"] = _extract_color(fg)
        if bg is not None:
            result["background"] = _extract_color(bg)
        return result
    blip = sp_pr.find("a:blipFill", NS)
    if blip is not None:
        return {"type": "image"}
    return None


def _extract_outline(ln_elem: ET.Element) -> dict | None:
    """Extract line/outline style."""
    if ln_elem is None:
        return None
    w = ln_elem.attrib.get("w")
    result = {}
    if w:
        try:
            result["width_pt"] = round(int(w) / EMU_PER_PT, 1)
        except ValueError:
            pass
    solid = ln_elem.find("a:solidFill", NS)
    grad = ln_elem.find("a:gradFill", NS)
    no_fill = ln_elem.find("a:noFill", NS)
    if no_fill is not None:
        result["fill"] = {"type": "none"}
    elif solid is not None:
        color = _extract_color(solid)
        if color:
            result["fill"] = {"type": "solid", "color": color}
    elif grad is not None:
        g = _extract_gradient(grad)
        if g:
            result["fill"] = g
    dash = ln_elem.find("a:prstDash", NS)
    if dash is not None:
        result["dash"] = dash.attrib.get("val", "solid")
    return result if result else None


def _extract_effects(sp_pr: ET.Element) -> list[str]:
    """Extract effect names from shape properties."""
    effects = []
    effect_lst = sp_pr.find("a:effectLst", NS)
    if effect_lst is not None:
        for child in effect_lst:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            effects.append(tag)
    effect_dag = sp_pr.find("a:effectDag", NS)
    if effect_dag is not None:
        for child in effect_dag:
            tag = child.tag.split("}") if "}" in child.tag else child.tag
            effects.append(f"dag:{tag}")
    return effects


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------
def _extract_text_runs(sp: ET.Element) -> list[dict]:
    """Extract text runs with font/style info from a shape."""
    runs = []
    for para in sp.findall(".//a:p", NS):
        for run in para.findall("a:r", NS):
            t = run.find("a:t", NS)
            if t is None or not t.text:
                continue
            rpr = run.find("a:rPr", NS)
            info: dict = {"text": t.text.strip()}
            if rpr is not None:
                sz = rpr.attrib.get("sz")
                if sz:
                    try:
                        info["size_pt"] = int(sz) / 100
                    except ValueError:
                        pass
                if rpr.attrib.get("b") == "1":
                    info["bold"] = True
                if rpr.attrib.get("i") == "1":
                    info["italic"] = True
                latin = rpr.find("a:latin", NS)
                ea = rpr.find("a:ea", NS)
                cs = rpr.find("a:cs", NS)
                if latin is not None and latin.attrib.get("typeface"):
                    info["font_latin"] = latin.attrib["typeface"]
                if ea is not None and ea.attrib.get("typeface"):
                    info["font_ea"] = ea.attrib["typeface"]
                if cs is not None and cs.attrib.get("typeface"):
                    info["font_cs"] = cs.attrib["typeface"]
                color_elem = rpr.find("a:solidFill", NS)
                if color_elem is not None:
                    color = _extract_color(color_elem)
                    if color:
                        info["color"] = color
            runs.append(info)
    return runs


def _extract_text_style(sp: ET.Element) -> dict | None:
    """Extract representative text style from a shape's first run."""
    rpr = sp.find(".//a:rPr", NS)
    if rpr is None:
        rpr = sp.find(".//a:endParaRPr", NS)
    if rpr is None:
        return None
    style: dict = {}
    sz = rpr.attrib.get("sz")
    if sz:
        try:
            style["size_pt"] = int(sz) / 100
        except ValueError:
            pass
    if rpr.attrib.get("b") == "1":
        style["bold"] = True
    if rpr.attrib.get("i") == "1":
        style["italic"] = True
    latin = rpr.find("a:latin", NS)
    ea = rpr.find("a:ea", NS)
    if latin is not None and latin.attrib.get("typeface"):
        style["font_latin"] = latin.attrib["typeface"]
    if ea is not None and ea.attrib.get("typeface"):
        style["font_ea"] = ea.attrib["typeface"]
    color_elem = rpr.find("a:solidFill", NS)
    if color_elem is not None:
        color = _extract_color(color_elem)
        if color:
            style["color"] = color
    return style


# ---------------------------------------------------------------------------
# Shape analysis
# ---------------------------------------------------------------------------
def _analyze_shape(sp: ET.Element) -> dict:
    """Analyze a single shape's design properties."""
    tag = sp.tag.split("}")[-1] if "}" in sp.tag else sp.tag
    info: dict = {"tag": tag}

    # Name
    nvpr = sp.find(".//p:cNvPr", NS)
    if nvpr is None:
        nvpr = sp.find(".//a:cNvPr", NS)
    if nvpr is not None:
        info["name"] = nvpr.attrib.get("name", "")

    # Geometry
    xfrm = sp.find(".//a:xfrm", NS)
    if xfrm is not None:
        off = xfrm.find("a:off", NS)
        ext = xfrm.find("a:ext", NS)
        if off is not None and ext is not None:
            try:
                info["bounds"] = {
                    "x": int(off.attrib.get("x", 0)),
                    "y": int(off.attrib.get("y", 0)),
                    "w": int(ext.attrib.get("cx", 0)),
                    "h": int(ext.attrib.get("cy", 0)),
                }
            except ValueError:
                pass

    # Shape properties (fill, outline, effects)
    sp_pr = sp.find("p:spPr", NS)
    if sp_pr is None:
        sp_pr = sp.find(".//a:spPr", NS)

    if sp_pr is not None:
        fill = _extract_fill(sp_pr)
        if fill:
            info["fill"] = fill
        ln = sp_pr.find("a:ln", NS)
        if ln is not None:
            outline = _extract_outline(ln)
            if outline:
                info["outline"] = outline
        effects = _extract_effects(sp_pr)
        if effects:
            info["effects"] = effects

    # Text
    texts = _extract_text_runs(sp)
    if texts:
        info["texts"] = texts
    text_style = _extract_text_style(sp)
    if text_style:
        info["textStyle"] = text_style

    # Placeholder
    ph = sp.find(".//p:ph", NS)
    if ph is not None:
        info["placeholder"] = {
            "type": ph.attrib.get("type"),
            "idx": ph.attrib.get("idx"),
        }

    return info


# ---------------------------------------------------------------------------
# Background analysis
# ---------------------------------------------------------------------------
def _analyze_background(zf: ZipFile, part_path: str, rels: dict) -> dict | None:
    """Analyze slide/layout/master background."""
    root = _load_xml(zf, part_path)
    if root is None:
        return None

    bg = root.find("p:cSld/p:bg", NS)
    if bg is None:
        bg = root.find("p:bg", NS)
    if bg is None:
        return None

    # Check for image background
    blip = bg.find(".//a:blip", NS)
    if blip is not None:
        embed = blip.find("a:blip", NS)
        if embed is None:
            embed = blip
        for rid in [embed.attrib.get(f"{{{NS['r']}}}embed"), embed.attrib.get("r:embed")]:
            if rid and rid in rels:
                return {"type": "image", "rel_target": rels[rid]["target"]}

    # Check for gradient background
    grad = bg.find(".//a:gradFill", NS)
    if grad is not None:
        g = _extract_gradient(grad)
        if g:
            return g

    # Check for solid background
    solid = bg.find(".//a:solidFill", NS)
    if solid is not None:
        color = _extract_color(solid)
        if color:
            return {"type": "solid", "color": color}

    return None


# ---------------------------------------------------------------------------
# Theme extraction
# ---------------------------------------------------------------------------
def _parse_theme(root: ET.Element | None) -> dict:
    """Parse theme.xml for colors and font scheme."""
    if root is None:
        return {"colors": {}, "fonts": {}}

    colors: dict[str, str] = {}
    clr_scheme = root.find(".//a:clrScheme", NS)
    if clr_scheme is not None:
        for child in list(clr_scheme):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}", 1)[-1]
            color = _extract_color(child)
            if color:
                colors[name] = color

    fonts: dict[str, str] = {}
    font_scheme = root.find(".//a:fontScheme", NS)
    if font_scheme is not None:
        fonts["scheme_name"] = font_scheme.attrib.get("name", "")
        for kind in ("majorFont", "minorFont"):
            f = font_scheme.find(f"a:{kind}", NS)
            if f is not None:
                latin = f.find("a:latin", NS)
                ea = f.find("a:ea", NS)
                cs = f.find("a:cs", NS)
                if latin is not None and latin.attrib.get("typeface"):
                    fonts[f"{kind}_latin"] = latin.attrib["typeface"]
                if ea is not None and ea.attrib.get("typeface"):
                    fonts[f"{kind}_ea"] = ea.attrib["typeface"]
                if cs is not None and cs.attrib.get("typeface"):
                    fonts[f"{kind}_cs"] = cs.attrib["typeface"]

    return {"colors": colors, "fonts": fonts}


# ---------------------------------------------------------------------------
# Slide classification
# ---------------------------------------------------------------------------
def _classify_slide(index: int, total: int, texts: list[str], shape_count: int) -> str:
    joined = " ".join(texts).lower()
    if any(kw in joined for kw in THANKS_KEYWORDS):
        return "ending"
    if any(kw in joined for kw in TOC_KEYWORDS):
        return "toc"
    if any(kw in joined for kw in CHAPTER_KEYWORDS):
        return "chapter"
    if index == 1:
        return "cover"
    if index == total and len(texts) <= 8:
        return "ending"
    return "content"


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------
def extract_design_profile(
    pptx_path: Path,
    output_dir: Path,
    *,
    include_screenshots: bool = False,
    include_key_slides: bool = False,
    max_screenshot_slides: int = 10,
) -> dict:
    """Extract comprehensive design profile from a PPTX file."""
    profile: dict = {
        "source": str(pptx_path),
        "source_name": pptx_path.name,
    }

    with ZipFile(pptx_path, "r") as zf:
        # ── Slide size ──
        pres_root = _load_xml(zf, "ppt/presentation.xml")
        if pres_root is None:
            raise ValueError("Invalid PPTX: missing ppt/presentation.xml")

        sld_sz = pres_root.find("p:sldSz", NS)
        if sld_sz is not None:
            w = int(sld_sz.attrib.get("cx", "0"))
            h = int(sld_sz.attrib.get("cy", "0"))
            profile["slideSize"] = {
                "width_emu": w,
                "height_emu": h,
                "width_px": _emu_to_px(w),
                "height_px": _emu_to_px(h),
                "aspect_ratio": f"{round(w/h, 2)}:1" if h else "unknown",
            }

        # ── Parse relationships ──
        pres_rels = _parse_rels(zf, "ppt/presentation.xml")

        # ── Collect slide/master/layout/theme paths ──
        slide_parts: list[str] = []
        for sld_id in pres_root.findall("p:sldIdLst/p:sldId", NS):
            rid = sld_id.attrib.get(f"{{{NS['r']}}}id")
            rel = pres_rels.get(rid or "")
            if rel and rel["type"] == SLIDE_REL:
                slide_parts.append(rel["target"])

        master_parts: list[str] = []
        for mid in pres_root.findall("p:sldMasterIdLst/p:sldMasterId", NS):
            rid = mid.attrib.get(f"{{{NS['r']}}}id")
            rel = pres_rels.get(rid or "")
            if rel and rel["type"] == MASTER_REL and rel["target"] not in master_parts:
                master_parts.append(rel["target"])

        # ── Theme extraction ──
        themes: dict[str, dict] = {}
        for master_path in master_parts:
            master_rels = _parse_rels(zf, master_path)
            theme_path = _resolve_rel(master_rels, THEME_REL)
            if theme_path and theme_path not in themes:
                theme_root = _load_xml(zf, theme_path)
                themes[theme_path] = _parse_theme(theme_root)

        # Use first theme as primary
        primary_theme = next(iter(themes.values()), {"colors": {}, "fonts": {}})
        profile["theme"] = primary_theme

        # ── Shape analysis across slides ──
        all_fills: list[dict] = []
        all_colors: Counter[str] = Counter()
        all_text_colors: Counter[str] = Counter()
        all_fonts: Counter[str] = Counter()
        all_font_sizes: Counter[float] = Counter()
        all_gradients: list[dict] = []
        all_effects: Counter[str] = Counter()
        all_outlines: list[dict] = []

        slide_profiles: list[dict] = []

        for idx, slide_path in enumerate(slide_parts, 1):
            slide_root = _load_xml(zf, slide_path)
            slide_rels = _parse_rels(zf, slide_path)

            # Resolve layout and master
            layout_path = _resolve_rel(slide_rels, LAYOUT_REL)
            layout_rels = _parse_rels(zf, layout_path) if layout_path else {}
            master_path = _resolve_rel(layout_rels, MASTER_REL)

            sp_tree = slide_root.find(".//p:spTree", NS) if slide_root is not None else None
            shapes = []
            text_samples: list[str] = []

            if sp_tree is not None:
                visual_tags = {
                    f"{{{NS['p']}}}sp", f"{{{NS['p']}}}pic",
                    f"{{{NS['p']}}}graphicFrame", f"{{{NS['p']}}}cxnSp",
                    f"{{{NS['p']}}}grpSp",
                }
                for sp in sp_tree:
                    if sp.tag not in visual_tags:
                        continue
                    shape_info = _analyze_shape(sp)
                    shapes.append(shape_info)

                    # Aggregate stats
                    if "fill" in shape_info:
                        fill = shape_info["fill"]
                        all_fills.append(fill)
                        if fill.get("type") == "solid" and fill.get("color"):
                            all_colors[fill["color"]] += 1
                        elif fill.get("type") == "gradient":
                            all_gradients.append(fill)
                            for stop in fill.get("stops", []):
                                all_colors[stop["color"]] += 1

                    if "outline" in shape_info and shape_info["outline"].get("fill"):
                        ln_fill = shape_info["outline"]["fill"]
                        if ln_fill.get("color"):
                            all_colors[ln_fill["color"]] += 1
                        all_outlines.append(shape_info["outline"])

                    if "effects" in shape_info:
                        for eff in shape_info["effects"]:
                            all_effects[eff] += 1

                    if "texts" in shape_info:
                        for t in shape_info["texts"]:
                            text = t.get("text", "").strip()
                            if text:
                                text_samples.append(text)
                            if t.get("font_latin"):
                                all_fonts[t["font_latin"]] += 1
                            if t.get("font_ea"):
                                all_fonts[t["font_ea"]] += 1
                            if t.get("size_pt"):
                                all_font_sizes[t["size_pt"]] += 1
                            if t.get("color"):
                                all_text_colors[t["color"]] += 1

            # Background
            bg_info = _analyze_background(zf, slide_path, slide_rels)
            if bg_info and bg_info.get("type") == "solid" and bg_info.get("color"):
                all_colors[bg_info["color"]] += 1
            elif bg_info and bg_info.get("type") == "gradient":
                all_gradients.append(bg_info)
                for stop in bg_info.get("stops", []):
                    all_colors[stop["color"]] += 1

            page_type = _classify_slide(idx, len(slide_parts), text_samples, len(shapes))
            slide_profiles.append({
                "index": idx,
                "pageType": page_type,
                "layout": layout_path,
                "master": master_path,
                "background": bg_info,
                "shapeCount": len(shapes),
                "textSamples": text_samples[:5],
            })

        # ── Aggregate design patterns ──
        # Top colors by usage
        profile["colorPalette"] = {
            "themeColors": primary_theme.get("colors", {}),
            "usageFrequency": [
                {"color": c, "count": n}
                for c, n in all_colors.most_common(20)
            ],
            "textColors": [
                {"color": c, "count": n}
                for c, n in all_text_colors.most_common(10)
            ],
        }

        # Font hierarchy
        profile["typography"] = {
            "themeFonts": primary_theme.get("fonts", {}),
            "usageFrequency": [
                {"font": f, "count": n}
                for f, n in all_fonts.most_common(15)
            ],
            "fontSizeHierarchy": [
                {"size_pt": s, "count": n}
                for s, n in sorted(all_font_sizes.items(), key=lambda x: -x[1])[:15]
            ],
        }

        # Gradient patterns
        unique_gradients = []
        seen_grad_keys: set[str] = set()
        for g in all_gradients:
            key = json.dumps(g.get("stops", []), sort_keys=True)
            if key not in seen_grad_keys:
                seen_grad_keys.add(key)
                unique_gradients.append(g)
        profile["gradients"] = unique_gradients[:10]

        # Fill type distribution
        fill_types: Counter[str] = Counter()
        for f in all_fills:
            fill_types[f.get("type", "unknown")] += 1
        profile["fillTypeDistribution"] = dict(fill_types)

        # Effects
        profile["effects"] = dict(all_effects.most_common(10))

        # Outline patterns
        outline_patterns: list[dict] = []
        seen_outline_keys: set[str] = set()
        for o in all_outlines:
            key = json.dumps(o, sort_keys=True)
            if key not in seen_outline_keys:
                seen_outline_keys.add(key)
                outline_patterns.append(o)
        profile["outlinePatterns"] = outline_patterns[:10]

        # Slide composition
        profile["slideComposition"] = {
            "totalSlides": len(slide_parts),
            "pageTypes": dict(Counter(s["pageType"] for s in slide_profiles)),
            "slides": slide_profiles,
        }

        # Master/Layout structure
        layout_summary: list[dict] = []
        for lp in set(s["layout"] for s in slide_profiles if s.get("layout")):
            users = [s["index"] for s in slide_profiles if s.get("layout") == lp]
            layout_root = _load_xml(zf, lp)
            name = ""
            if layout_root is not None:
                csld = layout_root.find("p:cSld", NS)
                if csld is not None:
                    name = csld.attrib.get("name", "")
            layout_summary.append({
                "path": lp,
                "name": name,
                "usedBySlides": sorted(users),
            })

        master_summary: list[dict] = []
        for mp in master_parts:
            users = [s["index"] for s in slide_profiles if s.get("master") == mp]
            master_root = _load_xml(zf, mp)
            name = ""
            if master_root is not None:
                csld = master_root.find("p:cSld", NS)
                if csld is not None:
                    name = csld.attrib.get("name", "")
            master_summary.append({
                "path": mp,
                "name": name,
                "usedBySlides": sorted(users),
            })

        profile["structure"] = {
            "masters": master_summary,
            "layouts": sorted(layout_summary, key=lambda x: x["path"]),
        }

    # ── Generate screenshots (optional) ──
    if include_screenshots:
        profile["screenshots"] = _generate_screenshots(
            pptx_path, output_dir, max_screenshot_slides
        )

    # ── Generate key slide SVGs (optional) ──
    if include_key_slides:
        profile["keySlideSvgs"] = _generate_key_slides(
            pptx_path, output_dir, slide_profiles
        )

    return profile


# ---------------------------------------------------------------------------
# SVG conversion and rendering
# ---------------------------------------------------------------------------
def _convert_slides_to_svg(pptx_path: Path, tmp_dir: Path):
    """Convert a PPTX to a flat, self-contained SVG list."""
    scripts_dir = str(Path(__file__).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from pptx_to_svg import convert_pptx_to_svg
    from pptx_to_svg.converter import ConvertOptions

    tmp_dir.mkdir(parents=True, exist_ok=True)
    options = ConvertOptions(
        images_subdir="images",
        embed_images=True,
        keep_hidden=False,
        inheritance_mode="flat",
    )
    return convert_pptx_to_svg(pptx_path, tmp_dir, options)


def _render_svgs_to_png(
    svg_items: list[tuple[str, str]],
    preview_dir: Path,
    *,
    width: int = 1280,
    height: int = 720,
) -> tuple[list[dict], str]:
    """Render SVG strings to PNGs with a CJK-capable backend.

    Prefers Playwright/Chromium because cairo has no font-fallback chain and
    renders CJK as tofu boxes. Falls back to cairosvg (with that caveat
    reported in the returned backend name) only when Playwright is absent.

    Returns (records, backend_name). Records carry name/path/bytes when ok.
    """
    preview_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    render_dir = preview_dir / ".render_tmp"
    render_dir.mkdir(parents=True, exist_ok=True)
    sources: list[tuple[str, Path]] = []
    for name, svg in svg_items:
        svg_path = render_dir / f"{name}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        sources.append((name, svg_path))

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright

        backend = "playwright-chromium"
        png_size = None
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                canvas = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2,
                )
                for name, svg_path in sources:
                    record: dict = {"name": name, "ok": False}
                    try:
                        canvas.set_content(
                            "<!doctype html><html><head><meta charset='utf-8'>"
                            "<style>html,body{margin:0;padding:0;background:#ffffff}"
                            f"svg{{display:block;width:{width}px;height:{height}px}}</style>"
                            f"</head><body>{svg_path.read_text(encoding='utf-8')}</body></html>"
                        )
                        canvas.evaluate(
                            "document.fonts ? document.fonts.ready : Promise.resolve()"
                        )
                        canvas.wait_for_timeout(120)
                        png_bytes = canvas.screenshot(type="png")
                        png_path = preview_dir / f"{name}.png"
                        png_path.write_bytes(png_bytes)
                        record.update({
                            "path": f"{preview_dir.name}/{name}.png",
                            "bytes": len(png_bytes),
                            "ok": True,
                        })
                    except Exception as exc:  # noqa: BLE001 — per-slide best effort
                        record["error"] = f"{type(exc).__name__}: {exc}"
                    records.append(record)
                browser.close()
        except (PlaywrightError, OSError, RuntimeError) as exc:
            print(
                f"Warning: Playwright render failed ({exc}); trying cairosvg",
                file=sys.stderr,
            )
            records = []
            backend = None
    except ImportError:
        backend = None

    if backend is None:
        try:
            import cairosvg
        except (ImportError, OSError):
            print(
                "Warning: no PNG renderer available (need playwright+chromium "
                "or cairosvg); skipping screenshots",
                file=sys.stderr,
            )
            return [], "none"
        backend = "cairosvg-cjk-caveat"
        print(
            "Warning: cairosvg renders CJK glyphs as tofu boxes; install "
            "playwright + chromium for correct screenshots",
            file=sys.stderr,
        )
        for name, svg_path in sources:
            record = {"name": name, "ok": False}
            try:
                png_path = preview_dir / f"{name}.png"
                cairosvg.svg2png(
                    bytestring=svg_path.read_text(encoding="utf-8").encode("utf-8"),
                    write_to=str(png_path),
                    output_width=width,
                    output_height=height,
                )
                record.update({
                    "path": f"{preview_dir.name}/{name}.png",
                    "bytes": png_path.stat().st_size,
                    "ok": True,
                })
            except Exception as exc:  # noqa: BLE001 — per-slide best effort
                record["error"] = f"{type(exc).__name__}: {exc}"
            records.append(record)

    import shutil
    shutil.rmtree(render_dir, ignore_errors=True)
    return records, backend


def _generate_screenshots(
    pptx_path: Path, output_dir: Path, max_slides: int
) -> dict:
    """Generate PNG screenshots of slides via SVG conversion."""
    preview_dir = output_dir / "slide_previews"
    tmp_dir = output_dir / ".svg_temp"
    scanned = 0
    try:
        result = _convert_slides_to_svg(pptx_path, tmp_dir)
        scanned = len(result.slides)
        items = [
            (f"slide_{i:02d}", slide.svg)
            for i, slide in enumerate(result.slides[:max_slides], start=1)
        ]
        records, backend = _render_svgs_to_png(items, preview_dir)
    except Exception as exc:  # noqa: BLE001 — screenshots are best effort
        print(f"Warning: screenshot generation failed: {exc}", file=sys.stderr)
        return {"backend": "none", "slidesScanned": scanned, "files": []}
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    files = [
        {"slideIndex": int(r["name"].split("_")[-1]), "pngFile": r["path"], "bytes": r["bytes"]}
        for r in records
        if r.get("ok")
    ]
    failed = [r for r in records if not r.get("ok")]
    for r in failed:
        print(f"Warning: screenshot failed for {r['name']}: {r.get('error')}", file=sys.stderr)
    return {
        "backend": backend,
        "slidesScanned": scanned,
        "files": files,
        "failed": [r["name"] for r in failed],
    }


def _generate_key_slides(
    pptx_path: Path, output_dir: Path, slide_profiles: list[dict]
) -> list[dict]:
    """Generate SVGs for key slide types (cover, toc, chapter, content, ending)."""
    key_types = {"cover", "toc", "chapter", "ending"}
    key_slides: list[dict] = []

    # Select one slide per key type
    selected: dict[str, int] = {}
    for sp in slide_profiles:
        pt = sp["pageType"]
        if pt in key_types and pt not in selected:
            selected[pt] = sp["index"]

    if not selected:
        return key_slides

    try:
        svg_dir = output_dir / "key_slides"
        svg_dir.mkdir(parents=True, exist_ok=True)
        tmp_dir = output_dir / ".svg_key_temp"
        result = _convert_slides_to_svg(pptx_path, tmp_dir)

        for page_type, slide_idx in selected.items():
            if slide_idx <= len(result.slides):
                svg_name = f"{page_type}_slide_{slide_idx:02d}.svg"
                svg_path = svg_dir / svg_name
                svg_path.write_text(result.slides[slide_idx - 1].svg, encoding="utf-8")
                key_slides.append({
                    "pageType": page_type,
                    "slideIndex": slide_idx,
                    "svgFile": f"key_slides/{svg_name}",
                })

        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    except Exception as e:
        print(f"Warning: key slide SVG generation failed: {e}", file=sys.stderr)

    return key_slides


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract comprehensive design profile from a PPTX file."
    )
    parser.add_argument("pptx_file", help="Path to the source .pptx file")
    parser.add_argument(
        "-o", "--output",
        help="Output directory (default: <pptx_stem>_design_profile beside the source)",
    )
    parser.add_argument(
        "--screenshots",
        action="store_true",
        help=(
            "Render PNG screenshots of slides (Playwright/Chromium preferred for "
            "correct CJK; falls back to cairosvg)"
        ),
    )
    parser.add_argument(
        "--key-slides",
        action="store_true",
        help="Generate SVGs for key slide types (cover, toc, chapter, ending)",
    )
    parser.add_argument(
        "--max-screenshots",
        type=int,
        default=10,
        help="Maximum number of screenshot slides (default: 10)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pptx_path = Path(args.pptx_file).expanduser().resolve()
    if not pptx_path.exists():
        print(f"Error: file does not exist: {pptx_path}")
        return 1
    if pptx_path.suffix.lower() != ".pptx":
        print(f"Error: expected a .pptx file, got: {pptx_path.name}")
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pptx_path.with_name(f"{pptx_path.stem}_design_profile")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        profile = extract_design_profile(
            pptx_path,
            output_dir,
            include_screenshots=args.screenshots,
            include_key_slides=args.key_slides,
            max_screenshot_slides=args.max_screenshots,
        )
    except Exception as e:
        print(f"Error extracting design profile: {e}")
        return 1

    # Write profile JSON
    profile_path = output_dir / "design_profile.json"
    profile_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    # Summary output
    print(f"Design profile extracted: {pptx_path.name}")
    print(f"Output: {output_dir}")
    print(f"Profile: {profile_path}")

    theme = profile.get("theme", {})
    colors = theme.get("colors", {})
    fonts = theme.get("fonts", {})
    if colors:
        print(f"Theme colors: {len(colors)}")
        for name, color in list(colors.items())[:6]:
            print(f"  {name}: {color}")
    if fonts:
        major = fonts.get("majorFont_latin", "?")
        minor = fonts.get("minorFont_latin", "?")
        print(f"Theme fonts: major={major}, minor={minor}")

    comp = profile.get("slideComposition", {})
    if comp:
        print(f"Total slides: {comp.get('totalSlides', 0)}")
        types = comp.get("pageTypes", {})
        if types:
            print(f"Page types: {dict(types)}")

    gradients = profile.get("gradients", [])
    if gradients:
        print(f"Unique gradients: {len(gradients)}")

    palette = profile.get("colorPalette", {})
    usage = palette.get("usageFrequency", [])
    if usage:
        print(f"Top used colors:")
        for item in usage[:5]:
            print(f"  {item['color']} (×{item['count']})")

    typo = profile.get("typography", {})
    font_usage = typo.get("usageFrequency", [])
    if font_usage:
        print(f"Font usage:")
        for item in font_usage[:5]:
            print(f"  {item['font']} (×{item['count']})")

    screenshots = profile.get("screenshots", {})
    if screenshots and screenshots.get("files"):
        print(
            f"Screenshots: {len(screenshots['files'])} "
            f"({screenshots.get('backend', 'unknown')})"
        )

    key_svgs = profile.get("keySlideSvgs", [])
    if key_svgs:
        print(f"Key slide SVGs: {len(key_svgs)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
