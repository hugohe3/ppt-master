"""Compose several native-diagram components into one new component.

Each part is loaded, optionally recolored, and wrapped in a group whose ``xfrm``
maps its source canvas onto a target rectangle (EMU) — so parts can be resized
and positioned freely. The result is saved as a normal library component
(``shapes.xml.gz`` + ``meta.json``) and can be injected like any other.

v1 composes pure-vector parts only (no media re-embedding across parts).
"""
from __future__ import annotations

import copy
import gzip
import itertools
import json
from pathlib import Path

from lxml import etree

from .component import A, P, recolor_shapes

DEFAULT_CANVAS = (12192000, 6858000)  # 16:9 EMU


def _load_diagram_root(comp_dir: Path):
    gz = comp_dir / "shapes.xml.gz"
    data = gzip.decompress(gz.read_bytes()) if gz.exists() else (comp_dir / "shapes.xml").read_bytes()
    return etree.fromstring(data)  # <a:diagram> wrapper


def _wrap(shapes, gid: int, src_canvas, pos):
    cw, ch = src_canvas
    x, y, w, h = pos
    grp = etree.Element("{%s}grpSp" % P)
    nv = etree.SubElement(grp, "{%s}nvGrpSpPr" % P)
    etree.SubElement(nv, "{%s}cNvPr" % P, id=str(gid), name=f"part{gid}")
    etree.SubElement(nv, "{%s}cNvGrpSpPr" % P)
    etree.SubElement(nv, "{%s}nvPr" % P)
    gpr = etree.SubElement(grp, "{%s}grpSpPr" % P)
    xf = etree.SubElement(gpr, "{%s}xfrm" % A)
    etree.SubElement(xf, "{%s}off" % A, x=str(int(x)), y=str(int(y)))
    etree.SubElement(xf, "{%s}ext" % A, cx=str(int(w)), cy=str(int(h)))
    etree.SubElement(xf, "{%s}chOff" % A, x="0", y="0")
    etree.SubElement(xf, "{%s}chExt" % A, cx=str(int(cw)), cy=str(int(ch)))
    for s in shapes:
        grp.append(s)
    return grp


def _title_shape(text: str, gid: int, canvas, *, color: str = "222222", size: int = 2800):
    cw, _ = canvas
    xml = (
        f'<p:sp xmlns:a="{A}" xmlns:p="{P}">'
        f'<p:nvSpPr><p:cNvPr id="{gid}" name="title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="500000" y="240000"/><a:ext cx="{cw - 1000000}" cy="820000"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p>'
        f'<a:r><a:rPr lang="zh-CN" sz="{size}" b="1"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="微软雅黑"/><a:ea typeface="微软雅黑"/></a:rPr>'
        f'<a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'
    )
    return etree.fromstring(xml)


def compose_diagram(
    parts: list[dict],
    out_dir: str | Path,
    *,
    key: str | None = None,
    title: str = "",
    title_color: str = "222222",
    canvas=DEFAULT_CANVAS,
) -> dict:
    """Compose parts into a new component.

    Each ``parts`` entry: ``{"dir": <component_dir>, "pos": (x, y, w, h),
    "recolor": {old: new}?, "src_canvas": (cw, ch)?}``.
    """
    out_dir = Path(out_dir)
    root = etree.Element("{%s}diagram" % A, nsmap={"a": A, "p": P})
    gid = itertools.count(1)

    if title:
        root.append(_title_shape(title, next(gid), canvas, color=title_color))

    sources = []
    for part in parts:
        comp = Path(part["dir"])
        sources.append(comp.name)
        diagram = _load_diagram_root(comp)
        if part.get("recolor"):
            recolor_shapes(diagram, part["recolor"])
        shapes = [copy.deepcopy(c) for c in diagram]
        root.append(_wrap(shapes, next(gid), part.get("src_canvas", canvas), part["pos"]))

    # Unique cNvPr ids across the whole composed slide.
    for i, cnv in enumerate(root.iter("{%s}cNvPr" % P), start=100):
        cnv.set("id", str(i))

    out_dir.mkdir(parents=True, exist_ok=True)
    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    (out_dir / "shapes.xml.gz").write_bytes(gzip.compress(data, mtime=0))

    meta = {
        "key": key or out_dir.name,
        "title": title or key or out_dir.name,
        "composed_from": sources,
        "canvas_emu": list(canvas),
        "shape_count": sum(1 for _ in root),
        "media": {},
        "charts_unsupported": [],
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return meta
