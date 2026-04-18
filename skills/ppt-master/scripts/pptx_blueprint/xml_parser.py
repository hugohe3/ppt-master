"""PPTX ZIP + XML -> Blueprint IR.

Orchestrator: opens the .pptx ZIP, enumerates slides via presentation rels,
resolves theme, and delegates per-shape extraction to shape_builder.build_shape.
"""

from __future__ import annotations

import posixpath
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from .inheritance import (
    build_inheritance_context, collect_inherited_shapes, resolve_background,
)
from .ir import Blueprint, Shape, SlideBlueprint, Theme, emu_to_px
from .shape_builder import build_shape
from .theme import build_theme


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
LAYOUT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
MASTER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
THEME_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"


# ---------------------------------------------------------------------------
# ZIP helpers
# ---------------------------------------------------------------------------

def _normalize_part(path: str, base: str | None = None) -> str:
    if base:
        path = str(PurePosixPath(base).parent.joinpath(path))
    path = path.replace("\\", "/")
    normalized = posixpath.normpath(path)
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def _rels_path_for(part_path: str) -> str:
    part = PurePosixPath(part_path)
    return str(part.parent / "_rels" / f"{part.name}.rels")


def _load_xml(zf: zipfile.ZipFile, part_path: str) -> ET.Element | None:
    try:
        with zf.open(part_path) as fh:
            return ET.parse(fh).getroot()
    except KeyError:
        return None
    except ET.ParseError:
        return None


def _parse_rels(zf: zipfile.ZipFile, part_path: str) -> dict[str, dict[str, str]]:
    rels_root = _load_xml(zf, _rels_path_for(part_path))
    if rels_root is None:
        return {}

    rels: dict[str, dict[str, str]] = {}
    for rel in rels_root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type")
        if not rel_id or not target or not rel_type:
            continue
        rels[rel_id] = {
            "type": rel_type,
            "target": _normalize_part(target, part_path),
        }
    return rels


def _find_rel_target(rels: dict[str, dict[str, str]], rel_type: str) -> str | None:
    for rel in rels.values():
        if rel["type"] == rel_type:
            return rel["target"]
    return None


# ---------------------------------------------------------------------------
# Background shape builder (uses shape_builder for fill resolution)
# ---------------------------------------------------------------------------

def _build_background_shape(
    slide_root: ET.Element,
    ctx,
    viewbox: tuple[int, int],
    slide_rels: dict[str, dict[str, str]],
    copied_assets: dict[str, str],
    theme: Theme,
) -> Shape | None:
    """Resolve the effective <p:bg> and emit a full-canvas Shape with its fill."""
    bg = resolve_background(slide_root, ctx)
    if bg is None:
        return None

    # <p:bg> may contain <p:bgPr> (with solidFill/gradFill/blipFill) or
    # <p:bgRef idx=... schemeClr="..."> referencing the master fillStyleLst.
    # v1 handles <p:bgPr> (direct fills); bgRef is left as an uncolored shape.
    from .shape_builder import _extract_fill_from  # internal helper reuse

    fill = None
    bg_pr = bg.find("p:bgPr", NS)
    if bg_pr is not None:
        fill = _extract_fill_from(bg_pr, theme, slide_rels, copied_assets)

    return Shape(
        kind="rect",
        bbox=(0.0, 0.0, float(viewbox[0]), float(viewbox[1])),
        fill=fill,
        source_name="_background",
    )


# ---------------------------------------------------------------------------
# Per-slide builder
# ---------------------------------------------------------------------------

def _build_slide_blueprint(
    zf: zipfile.ZipFile,
    slide_path: str,
    slide_index: int,
    viewbox: tuple[int, int],
    copied_assets: dict[str, str],
    theme: Theme,
    warnings: list[str],
) -> SlideBlueprint | None:
    """Parse a single slide into a complete SlideBlueprint."""
    slide_root = _load_xml(zf, slide_path)
    if slide_root is None:
        warnings.append(f"Could not load slide {slide_path}")
        return None
    slide_rels = _parse_rels(zf, slide_path)

    layout_path = _find_rel_target(slide_rels, LAYOUT_REL)
    layout_root = _load_xml(zf, layout_path) if layout_path else None
    layout_rels = _parse_rels(zf, layout_path) if layout_path else {}

    master_path = _find_rel_target(layout_rels, MASTER_REL)
    master_root = _load_xml(zf, master_path) if master_path else None

    ctx = build_inheritance_context(layout_root, master_root)

    sp_tree = slide_root.find(".//p:cSld/p:spTree", NS)
    shapes: list[Shape] = []
    if sp_tree is not None:
        for child in sp_tree:
            if not isinstance(child.tag, str):
                continue
            local = child.tag.split("}", 1)[-1]
            if local in ("sp", "pic", "grpSp", "graphicFrame"):
                shape = build_shape(
                    child, ctx, slide_rels, copied_assets, theme, warnings,
                )
                if shape is not None:
                    shapes.append(shape)

    bg_shape = _build_background_shape(
        slide_root, ctx, viewbox, slide_rels, copied_assets, theme,
    )

    # Inherited placeholder shapes not present on the slide
    for inh_sp in collect_inherited_shapes(slide_root, ctx):
        inh_shape = build_shape(
            inh_sp, ctx, {}, copied_assets, theme, warnings,
        )
        if inh_shape is not None:
            inh_shape.source_name = (inh_shape.source_name or "") + " [inherited]"
            shapes.append(inh_shape)

    layout_name = None
    if layout_root is not None:
        cSld = layout_root.find("p:cSld", NS)
        if cSld is not None:
            layout_name = cSld.attrib.get("name")

    # Flatten text samples for downstream classification / page type inference
    flat_samples: list[str] = []
    _walk_text_samples(shapes, flat_samples, limit=20)

    return SlideBlueprint(
        index=slide_index,
        viewbox=viewbox,
        background=bg_shape,
        shapes=shapes,
        layout_name=layout_name,
        text_samples=flat_samples,
    )


def _walk_text_samples(shapes: list[Shape], out: list[str], limit: int) -> None:
    for shape in shapes:
        if len(out) >= limit:
            return
        if shape.text is not None:
            for p in shape.text.paragraphs:
                for r in p.runs:
                    if r.text.strip():
                        out.append(r.text.strip())
                        if len(out) >= limit:
                            return
        if shape.children:
            _walk_text_samples(shape.children, out, limit)


# ---------------------------------------------------------------------------
# Media asset export
# ---------------------------------------------------------------------------

def _export_assets(
    zf: zipfile.ZipFile,
    output_assets_dir: Path | None,
) -> dict[str, str]:
    """Copy ppt/media/* into <output>/assets/, returning {zip_path: basename}."""
    mapping: dict[str, str] = {}
    if output_assets_dir is not None:
        output_assets_dir.mkdir(parents=True, exist_ok=True)

    used_names: set[str] = set()
    for info in zf.infolist():
        if not info.filename.startswith("ppt/media/") or info.is_dir():
            continue
        original = PurePosixPath(info.filename).name
        safe = _sanitize_filename(original)
        base_stem = safe.rsplit(".", 1)[0]
        suffix = ("." + safe.rsplit(".", 1)[1]) if "." in safe else ""
        candidate = safe
        counter = 2
        while candidate in used_names:
            candidate = f"{base_stem}_{counter}{suffix}"
            counter += 1
        used_names.add(candidate)
        mapping[info.filename] = candidate

        if output_assets_dir is not None:
            dest = output_assets_dir / candidate
            with zf.open(info.filename) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)

    return mapping


def _sanitize_filename(name: str) -> str:
    import re
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return cleaned.strip("._") or "asset"


# ---------------------------------------------------------------------------
# Theme prefetch (before slide loop, so all slides share one Theme)
# ---------------------------------------------------------------------------

def _prefetch_theme(zf: zipfile.ZipFile, first_slide_path: str) -> Theme:
    """Follow slide -> layout -> master -> theme to build a Theme before iterating."""
    slide_rels = _parse_rels(zf, first_slide_path)
    layout_path = _find_rel_target(slide_rels, LAYOUT_REL)
    if layout_path is None:
        return Theme()
    layout_rels = _parse_rels(zf, layout_path)
    master_path = _find_rel_target(layout_rels, MASTER_REL)
    if master_path is None:
        return Theme()

    master_root = _load_xml(zf, master_path)
    master_rels = _parse_rels(zf, master_path)
    theme_path = _find_rel_target(master_rels, THEME_REL)
    theme_root = _load_xml(zf, theme_path) if theme_path else None

    return build_theme(theme_root, master_root)


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def parse_pptx(
    pptx_path: str | Path,
    output_dir: Path | None = None,
) -> Blueprint:
    """Parse a PPTX file into a Blueprint IR.

    Args:
        pptx_path: Path to the .pptx file.
        output_dir: If given, ppt/media/ assets are copied to <output_dir>/assets/.

    Returns:
        A Blueprint with slide size, theme, and per-slide complete shapes.
    """
    pptx_path = Path(pptx_path).resolve()
    warnings: list[str] = []

    with zipfile.ZipFile(pptx_path, "r") as zf:
        pres_root = _load_xml(zf, "ppt/presentation.xml")
        if pres_root is None:
            raise ValueError(f"Invalid PPTX (no ppt/presentation.xml): {pptx_path}")

        sld_sz = pres_root.find("p:sldSz", NS)
        if sld_sz is not None:
            width_emu = int(sld_sz.attrib.get("cx", "0"))
            height_emu = int(sld_sz.attrib.get("cy", "0"))
            viewbox = (int(emu_to_px(width_emu)), int(emu_to_px(height_emu)))
        else:
            viewbox = (1280, 720)

        pres_rels = _parse_rels(zf, "ppt/presentation.xml")
        slide_parts: list[str] = []
        for sld_id in pres_root.findall("p:sldIdLst/p:sldId", NS):
            rel_id = sld_id.attrib.get(f"{{{NS['r']}}}id")
            rel = pres_rels.get(rel_id or "")
            if rel and rel["type"] == SLIDE_REL:
                slide_parts.append(rel["target"])

        assets_dir = output_dir / "assets" if output_dir is not None else None
        asset_mapping = _export_assets(zf, assets_dir)
        assets_dict: dict[str, Path] = {}
        if output_dir is not None:
            for zip_path, basename in asset_mapping.items():
                assets_dict[zip_path] = (assets_dir / basename) if assets_dir else Path(basename)

        # Build Theme from first slide's inheritance chain
        theme: Theme = Theme()
        if slide_parts:
            theme = _prefetch_theme(zf, slide_parts[0])

        slides: list[SlideBlueprint] = []
        for index, slide_path in enumerate(slide_parts, start=1):
            slide_bp = _build_slide_blueprint(
                zf, slide_path, index, viewbox,
                asset_mapping, theme, warnings,
            )
            if slide_bp is not None:
                slides.append(slide_bp)

    return Blueprint(
        source_pptx=pptx_path,
        viewbox=viewbox,
        theme=theme,
        slides=slides,
        assets=assets_dict,
        warnings=warnings,
    )
