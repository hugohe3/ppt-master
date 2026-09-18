"""Shared OOXML primitives for PPTX intake and source-preserving export.

Read-side helpers only: namespaces and content-type constants, part /
relationship resolution, EMU unit conversion, slide-shape discovery, and small
JSON readers / writers. Write-side package plumbing lives in ``package.py``.
"""

from __future__ import annotations

import json
import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
C14_NS = "http://schemas.microsoft.com/office/drawing/2007/8/2/chart"
C16_NS = "http://schemas.microsoft.com/office/drawing/2014/chart"
C16R2_NS = "http://schemas.microsoft.com/office/drawing/2015/06/chart"

SLIDE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
NOTES_SLIDE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
CHART_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"
PACKAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/package"
SLIDE_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
NOTES_SLIDE_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
CHART_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EMU_PER_INCH = 914400
PX_PER_INCH = 96


for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
ET.register_namespace("", REL_NS)
ET.register_namespace("mc", MC_NS)
ET.register_namespace("c14", C14_NS)
ET.register_namespace("c16", C16_NS)
ET.register_namespace("c16r2", C16R2_NS)
ET.register_namespace("p14", P14_NS)


@dataclass(frozen=True)
class SlideRef:
    """Presentation slide reference resolved from presentation.xml.rels."""

    index: int
    rel_id: str
    target: str
    part_name: str
    rels_name: str


def _qn(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def _read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(zf.read(name))
    except KeyError as exc:
        raise RuntimeError(f"Missing required PPTX part: {name}") from exc


def _xml_bytes(root: ET.Element) -> bytes:
    root_namespace = root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else ""
    if root_namespace in {REL_NS, CT_NS}:
        # OPC relationship/content-type roots conventionally use the default
        # namespace. ElementTree's global prefix registry can be changed while
        # parsing source parts; restore the package-root form before writing so
        # strict consumers such as LibreOffice accept the generated package.
        ET.register_namespace("", root_namespace)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _normalize_part(target: str, base: str = "ppt/presentation.xml") -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    normalized = posixpath.normpath(posixpath.join(posixpath.dirname(base), target))
    return normalized.lstrip("/")


def _rels_name_for_part(part_name: str) -> str:
    parent = posixpath.dirname(part_name)
    basename = posixpath.basename(part_name)
    return posixpath.join(parent, "_rels", f"{basename}.rels")


def _emu_to_px(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return round(int(value) / EMU_PER_INCH * PX_PER_INCH)
    except ValueError:
        return None


def _parse_relationships(zf: zipfile.ZipFile) -> dict[str, dict[str, str]]:
    rels_name = "ppt/_rels/presentation.xml.rels"
    rels_root = _read_xml(zf, rels_name)
    relationships: dict[str, dict[str, str]] = {}
    seen_ids: set[str] = set()
    for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
        rel_id = rel.attrib.get("Id")
        if rel_id:
            if rel_id in seen_ids:
                raise RuntimeError(
                    f"Duplicate relationship Id {rel_id!r} in {rels_name}"
                )
            seen_ids.add(rel_id)
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type")
        if rel_id and target and rel_type:
            relationships[rel_id] = {"target": target, "type": rel_type}
    return relationships


def _parse_slide_refs(zf: zipfile.ZipFile) -> list[SlideRef]:
    pres_root = _read_xml(zf, "ppt/presentation.xml")
    relationships = _parse_relationships(zf)
    sld_id_lst = pres_root.find("p:sldIdLst", NS)
    if sld_id_lst is None:
        return []

    slides: list[SlideRef] = []
    for index, sld_id in enumerate(sld_id_lst.findall("p:sldId", NS), start=1):
        rel_id = sld_id.attrib.get(_qn(NS["r"], "id"))
        if not rel_id or rel_id not in relationships:
            continue
        rel = relationships[rel_id]
        if rel["type"] != SLIDE_REL_TYPE:
            continue
        part_name = _normalize_part(rel["target"])
        slides.append(
            SlideRef(
                index=index,
                rel_id=rel_id,
                target=rel["target"],
                part_name=part_name,
                rels_name=_rels_name_for_part(part_name),
            )
        )
    return slides


def _slide_relationships(zf: zipfile.ZipFile, rels_name: str) -> dict[str, dict[str, str]]:
    try:
        rels_root = _read_xml(zf, rels_name)
    except RuntimeError:
        return {}
    relationships: dict[str, dict[str, str]] = {}
    for rel in rels_root.findall(_qn(REL_NS, "Relationship")):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type")
        if rel_id and target and rel_type:
            relationships[rel_id] = {"target": target, "type": rel_type}
    return relationships


def _paragraph_texts(container: ET.Element) -> list[str]:
    paragraphs: list[str] = []
    for paragraph in container.findall(".//a:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS)).strip()
        if text:
            paragraphs.append(text)
    if paragraphs:
        return paragraphs
    text = "".join(node.text or "" for node in container.findall(".//a:t", NS)).strip()
    return [text] if text else []


def _group_chain(container: ET.Element, slide_root: ET.Element) -> list[ET.Element]:
    """Return the ``p:grpSp`` ancestors of ``container``, innermost first."""
    parents = {child: parent for parent in slide_root.iter() for child in parent}
    chain: list[ET.Element] = []
    node = parents.get(container)
    group_tag = f"{{{NS['p']}}}grpSp"
    while node is not None:
        if node.tag == group_tag:
            chain.append(node)
        node = parents.get(node)
    return chain


def _container_geometry(
    container: ET.Element,
    slide_root: ET.Element | None = None,
) -> dict[str, int | None]:
    """Return the container's slide-space box in px.

    A shape inside ``p:grpSp`` stores its ``a:xfrm`` in the group's child
    space; with ``slide_root`` every enclosing group's ``off/ext`` versus
    ``chOff/chExt`` mapping is applied so nested siblings do not all report
    the same local corner.
    """
    xfrm = container.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        xfrm = container.find("p:xfrm", NS)
    if xfrm is None:
        xfrm = container.find(".//a:xfrm", NS)
    if xfrm is None:
        return {"x": None, "y": None, "width": None, "height": None}
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    try:
        x = float(off.attrib["x"]) if off is not None else None
        y = float(off.attrib["y"]) if off is not None else None
        width = float(ext.attrib["cx"]) if ext is not None else None
        height = float(ext.attrib["cy"]) if ext is not None else None
    except (KeyError, ValueError):
        return {"x": None, "y": None, "width": None, "height": None}
    if slide_root is not None:
        for group in _group_chain(container, slide_root):
            group_xfrm = group.find("p:grpSpPr/a:xfrm", NS)
            if group_xfrm is None:
                continue
            parts = [group_xfrm.find(name, NS) for name in ("a:off", "a:ext", "a:chOff", "a:chExt")]
            if any(part is None for part in parts):
                continue
            g_off, g_ext, ch_off, ch_ext = parts
            try:
                ch_cx = float(ch_ext.attrib["cx"])
                ch_cy = float(ch_ext.attrib["cy"])
                scale_x = float(g_ext.attrib["cx"]) / ch_cx if ch_cx else 1.0
                scale_y = float(g_ext.attrib["cy"]) / ch_cy if ch_cy else 1.0
                if x is not None:
                    x = float(g_off.attrib["x"]) + (x - float(ch_off.attrib["x"])) * scale_x
                if y is not None:
                    y = float(g_off.attrib["y"]) + (y - float(ch_off.attrib["y"])) * scale_y
            except (KeyError, ValueError):
                continue
            if width is not None:
                width *= scale_x
            if height is not None:
                height *= scale_y

    def _px(value: float | None) -> int | None:
        return None if value is None else round(value / EMU_PER_INCH * PX_PER_INCH)

    return {"x": _px(x), "y": _px(y), "width": _px(width), "height": _px(height)}


def _text_containers(slide_root: ET.Element) -> list[ET.Element]:
    containers: list[ET.Element] = []
    for tag in ("p:sp", "p:graphicFrame"):
        for element in slide_root.findall(f".//{tag}", NS):
            if element.find(".//p:txBody", NS) is not None or element.findall(".//a:t", NS):
                containers.append(element)
    return containers


def _table_containers(slide_root: ET.Element) -> list[ET.Element]:
    return [
        frame
        for frame in slide_root.findall(".//p:graphicFrame", NS)
        if frame.find(".//a:tbl", NS) is not None
    ]


def _chart_containers(slide_root: ET.Element) -> list[ET.Element]:
    return [
        frame
        for frame in slide_root.findall(".//p:graphicFrame", NS)
        if frame.find(".//c:chart", NS) is not None
    ]


def _shape_identity(container: ET.Element, order: int) -> tuple[str, str]:
    c_nv_pr = container.find(".//p:cNvPr", NS)
    shape_id = c_nv_pr.attrib.get("id") if c_nv_pr is not None else str(order)
    shape_name = c_nv_pr.attrib.get("name") if c_nv_pr is not None else ""
    return shape_id, shape_name


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON: {path}: {exc}") from exc


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
