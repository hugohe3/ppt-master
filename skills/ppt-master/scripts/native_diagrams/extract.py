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
import gzip
import html
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

# Editable text runs, in document order over the serialized shapes. The resolver
# walks the SAME regex over the SAME stored string, so slot ids align exactly.
_AT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.DOTALL)


def _text_slots(shapes_xml: str) -> list[dict]:
    """Index every <a:t> run as a fillable text slot, keeping its original text
    as an authoring hint (what kind of content the slot held in the source)."""
    return [
        {"id": i, "text": html.unescape(m.group(1))}
        for i, m in enumerate(_AT_RE.finditer(shapes_xml))
    ]

from .component import (
    A, P, R, NS, SHAPE_TAGS, IMAGE_REL, CHART_REL,
    local, read_rels, resolve_target, resolve_master_and_theme,
    load_theme_maps, flatten_theme, strip_foreign_rels,
)
from .slotspec import compute_slot_spec, FIT_GUIDANCE


def _representative_title(sp_tree) -> str:
    """A short title hint for the index: the largest-font text run, else the first.

    These vendor diagrams rarely use real title placeholders, so size is a better
    signal than document order. Used only as a human-readable summary seed — the
    curator can overwrite it.
    """
    best_sz, best_text, first_text = -1, "", ""
    for run in sp_tree.iter("{%s}r" % A):
        t = run.find("{%s}t" % A)
        if t is None or not (t.text and t.text.strip()):
            continue
        txt = " ".join(t.text.split())
        if not first_text:
            first_text = txt
        rpr = run.find("{%s}rPr" % A)
        sz = int(rpr.get("sz")) if (rpr is not None and (rpr.get("sz") or "").isdigit()) else 0
        if sz > best_sz:
            best_sz, best_text = sz, txt
    return (best_text or first_text)[:40]


def extract_diagram(
    src_pptx: str | Path,
    slide_num: int,
    out_dir: str | Path,
    *,
    key: str | None = None,
    summary: str = "",
    structure: str = "",
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
        title = _representative_title(sp_tree)
        counts = flatten_theme(sp_tree, maps)

        rels = {r["id"]: r for r in read_rels(z, slide_part)}

        def _chart_rids(el) -> list[str]:
            """Chart rIds referenced under *el* (a chart uses <c:chart r:id=...>)."""
            found = []
            for sub in el.iter():
                for ak, av in sub.attrib.items():
                    if ak.endswith("}id") and rels.get(av, {}).get("type") == CHART_REL:
                        found.append(av)
            return found

        # Data charts (graphicFrame -> chart part) are NOT lifted: the chart +
        # embedded-workbook parts live separately (templates/charts/). Drop those
        # frames from the lifted set and record their rIds — shipping the frame
        # would leave an empty graphicFrame once strip_foreign_rels drops its r:id.
        shapes: list = []
        charts: list[str] = []
        for c in sp_tree:
            if local(c) not in SHAPE_TAGS:
                continue
            rids = _chart_rids(c)
            if rids:
                charts.extend(rids)
                continue
            shapes.append(c)
        if charts:
            print(
                f"Note: slide {slide_num}: {len(charts)} chart(s) not lifted "
                f"(charts stay with templates/charts/): {', '.join(charts)}",
                file=sys.stderr,
            )

        # Map embedded-image rIds -> targets among the LIFTED shapes only. Skip
        # external-linked images (TargetMode=External): their target is a URL, so
        # resolve_target + z.read would crash on a path that isn't in the package.
        media_map: dict[str, str] = {}   # rId -> "media/<file>"
        for s in shapes:
            for el in s.iter():
                for k, v in el.attrib.items():
                    if k.endswith("}embed") or k.endswith("}link"):
                        rel = rels.get(v)
                        if rel and rel["type"] == IMAGE_REL and rel.get("mode") != "External":
                            media_map[v] = rel["target"]

        # Strip non-media rel refs (tags / hyperlinks / sounds / chart leftovers)
        # so the lifted shapes carry no dangling rIds into the target deck.
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

        # shapes.xml.gz — a stable <a:diagram> wrapper holding the lifted shapes.
        # DrawingML is verbose (~1 MB/slide raw) but compresses ~18x, so the
        # library stays git-friendly. inject reads .gz, falling back to plain .xml.
        root = etree.Element("{%s}diagram" % A, nsmap={"a": A, "p": P, "r": R})
        for s in shapes:
            root.append(copy.deepcopy(s))
        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
        text_slots = _text_slots(data.decode("utf-8"))
        (out_dir / "shapes.xml.gz").write_bytes(gzip.compress(data, mtime=0))

    meta = {
        "key": key or out_dir.name,
        "title": title,
        "source": src_pptx.name,
        "slide_num": slide_num,
        "canvas_emu": canvas,
        "shape_count": len(shapes),
        "media": media_meta,
        "charts_unsupported": charts,
        "flatten": counts,
        "foreign_rels_stripped": stripped,
        "text_slots": text_slots,
        "slot_spec": compute_slot_spec(text_slots),
        "structure": structure,
        "fit_guidance": FIT_GUIDANCE,
        "summary": summary,
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return meta
