"""Extract one slide's shapes into a self-contained native-diagram component.

Output component layout (``templates/native_diagrams/<key>/``)::

    <key>/
        shapes.xml     flattened top-level shapes wrapped in <a:diagram>
        media/         only present when the diagram references bitmaps
            image1.png
        meta.json      provenance + media rId map + flatten counts + summary

The component is theme-independent: every ``schemeClr`` has been resolved to
``srgbClr`` and every theme-font token to a concrete typeface, so it renders
identically when injected into any deck. Charts (``graphicFrame`` -> chart part)
are recorded in ``meta['charts_unsupported']`` and NOT lifted — their separate
chart/embedding parts are out of scope for v1.
"""
from __future__ import annotations

import copy
import json
import posixpath
import zipfile
from pathlib import Path

from lxml import etree

from .component import (
    A, P, R, NS, SHAPE_TAGS, IMAGE_REL, CHART_REL,
    local, read_rels, resolve_target, resolve_master_and_theme,
    load_theme_maps, flatten_theme, strip_foreign_rels,
)


def extract_diagram(
    src_pptx: str | Path,
    slide_num: int,
    out_dir: str | Path,
    *,
    key: str | None = None,
    summary: str = "",
) -> dict:
    src_pptx = Path(src_pptx)
    out_dir = Path(out_dir)
    slide_part = f"ppt/slides/slide{slide_num}.xml"

    with zipfile.ZipFile(src_pptx) as z:
        if slide_part not in z.namelist():
            raise FileNotFoundError(f"{slide_part} not in {src_pptx.name}")

        slide = etree.fromstring(z.read(slide_part))
        master_part, theme_part = resolve_master_and_theme(z, slide_part)
        maps = load_theme_maps(z.read(theme_part), z.read(master_part))

        pres = etree.fromstring(z.read("ppt/presentation.xml"))
        sz = pres.find("p:sldSz", NS)
        canvas = [int(sz.get("cx")), int(sz.get("cy"))]

        sp_tree = slide.find(".//p:cSld/p:spTree", NS)
        counts = flatten_theme(sp_tree, maps)

        shapes = [c for c in sp_tree if local(c) in SHAPE_TAGS]

        # Map referenced relationship ids -> targets, split into media vs charts.
        rels = {r["id"]: r for r in read_rels(z, slide_part)}
        media_map: dict[str, str] = {}   # rId -> "media/<file>"
        charts: list[str] = []
        for el in sp_tree.iter():
            for k, v in el.attrib.items():
                if k.endswith("}embed") or k.endswith("}link"):
                    rel = rels.get(v)
                    if not rel:
                        continue
                    if rel["type"] == IMAGE_REL:
                        media_map[v] = rel["target"]
                    elif rel["type"] == CHART_REL:
                        charts.append(v)

        # Strip non-media rel refs (tags / hyperlinks / sounds) so the lifted
        # shapes carry no dangling rIds into the target deck.
        stripped = strip_foreign_rels(sp_tree, keep_rids=set(media_map))

        out_dir.mkdir(parents=True, exist_ok=True)

        # Copy media, dedup by basename, record rId -> local path.
        media_meta: dict[str, str] = {}
        if media_map:
            (out_dir / "media").mkdir(exist_ok=True)
            for rid, target in media_map.items():
                abs_path = resolve_target(slide_part, target)
                fname = posixpath.basename(abs_path)
                (out_dir / "media" / fname).write_bytes(z.read(abs_path))
                media_meta[rid] = f"media/{fname}"

        # shapes.xml — a stable <a:diagram> wrapper holding the lifted shapes.
        root = etree.Element("{%s}diagram" % A, nsmap={"a": A, "p": P, "r": R})
        for s in shapes:
            root.append(copy.deepcopy(s))
        (out_dir / "shapes.xml").write_bytes(
            etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        )

    meta = {
        "key": key or out_dir.name,
        "source": src_pptx.name,
        "slide_num": slide_num,
        "canvas_emu": canvas,
        "shape_count": len(shapes),
        "media": media_meta,
        "charts_unsupported": charts,
        "flatten": counts,
        "foreign_rels_stripped": stripped,
        "summary": summary,
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return meta
