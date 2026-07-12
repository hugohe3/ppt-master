"""Post-package validation for explicit SVG text-layout contracts."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


P_NS = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'p': P_NS, 'a': A_NS}


def _shape_id(shape: ET.Element) -> int | None:
    c_nv_pr = shape.find('./p:nvSpPr/p:cNvPr', NS)
    if c_nv_pr is None:
        c_nv_pr = shape.find('./p:nvGrpSpPr/p:cNvPr', NS)
    if c_nv_pr is None:
        return None
    try:
        return int(c_nv_pr.get('id', ''))
    except ValueError:
        return None


def _shape_map(root: ET.Element) -> dict[int, ET.Element]:
    shapes: dict[int, ET.Element] = {}
    for element in root.iter():
        if element.tag not in {
            f'{{{P_NS}}}sp',
            f'{{{P_NS}}}grpSp',
        }:
            continue
        shape_id = _shape_id(element)
        if shape_id is not None:
            shapes[shape_id] = element
    return shapes


def _shape_bounds(shape: ET.Element) -> list[int]:
    off = shape.find('./p:spPr/a:xfrm/a:off', NS)
    ext = shape.find('./p:spPr/a:xfrm/a:ext', NS)
    if off is None or ext is None:
        raise ValueError('[TEXT_PACKAGE_BOUNDS] Text shape has no complete a:xfrm')
    x = int(off.get('x', '0'))
    y = int(off.get('y', '0'))
    return [x, y, x + int(ext.get('cx', '0')), y + int(ext.get('cy', '0'))]


def _content_sha256(shape: ET.Element) -> str:
    txbody = shape.find('./p:txBody', NS)
    if txbody is None:
        raise ValueError('[TEXT_PACKAGE_TXBODY] Contract output has no direct p:txBody')
    paragraphs: list[list[dict[str, str]]] = []
    for paragraph in txbody.findall('./a:p', NS):
        tokens: list[dict[str, str]] = []
        bullet = paragraph.find('./a:pPr/a:buChar', NS)
        if bullet is not None:
            tokens.append({
                'kind': 'bullet',
                'text': bullet.get('char', '•'),
            })
        for child in paragraph:
            if child.tag == f'{{{A_NS}}}br':
                tokens.append({'kind': 'break'})
                continue
            if child.tag not in {f'{{{A_NS}}}r', f'{{{A_NS}}}fld'}:
                continue
            text = child.find('./a:t', NS)
            text_value = text.text if text is not None and text.text is not None else ''
            tokens.append({'kind': 'run', 'text': text_value})
        paragraphs.append(tokens)
    payload = json.dumps(paragraphs, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _combined_content_sha256(shapes: list[ET.Element]) -> str:
    hashes = [_content_sha256(shape) for shape in shapes]
    if len(hashes) == 1:
        return hashes[0]
    payload = json.dumps(hashes, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _union_bounds(shapes: list[ET.Element]) -> list[int]:
    bounds = [_shape_bounds(shape) for shape in shapes]
    return [
        min(value[0] for value in bounds),
        min(value[1] for value in bounds),
        max(value[2] for value in bounds),
        max(value[3] for value in bounds),
    ]


def _validate_block(
    block: dict[str, Any],
    shapes_by_id: dict[int, ET.Element],
) -> None:
    source = block.get('source') or {}
    source_id = source.get('element_id') or '<unknown>'
    shape_ids = [int(value) for value in block.get('output_shape_ids') or []]
    missing = [shape_id for shape_id in shape_ids if shape_id not in shapes_by_id]
    if missing:
        raise ValueError(
            f'[TEXT_PACKAGE_SHAPE_MAP] {source_id}: missing output shape id(s) {missing}'
        )
    shapes = [shapes_by_id[shape_id] for shape_id in shape_ids]
    effective_mode = block.get('effective_mode')
    expected_shape_count = (
        1
        if effective_mode == 'paragraph'
        else int(block.get('visual_line_count') or 0)
    )
    if len(shapes) != expected_shape_count:
        raise ValueError(
            f'[TEXT_PACKAGE_SHAPE_COUNT] {source_id}: '
            f'{len(shapes)} != {expected_shape_count}'
        )
    paragraph_count = sum(
        len(shape.findall('./p:txBody/a:p', NS))
        for shape in shapes
    )
    break_count = sum(
        len(shape.findall('./p:txBody/a:p/a:br', NS))
        for shape in shapes
    )
    if paragraph_count != int(block.get('paragraph_count') or 0):
        raise ValueError(
            f'[TEXT_PACKAGE_PARAGRAPHS] {source_id}: '
            f'{paragraph_count} != {block.get("paragraph_count")}'
        )
    if break_count != int(block.get('break_count') or 0):
        raise ValueError(
            f'[TEXT_PACKAGE_BREAKS] {source_id}: '
            f'{break_count} != {block.get("break_count")}'
        )
    expected_bounds = block.get('slide_bounds_emu')
    if expected_bounds is not None and _union_bounds(shapes) != expected_bounds:
        raise ValueError(
            f'[TEXT_PACKAGE_BOUNDS] {source_id}: final package bounds changed'
        )
    actual_hash = _combined_content_sha256(shapes)
    if actual_hash != block.get('content_sha256'):
        raise ValueError(
            f'[TEXT_PACKAGE_CONTENT] {source_id}: final text content hash changed'
        )
    block['readback'] = {'status': 'passed'}


def validate_pptx_text_contracts(
    pptx_path: Path,
    conversion_traces: list[dict[str, Any]] | None,
) -> None:
    """Validate explicit text blocks in a temporary PPTX before publication."""
    if not conversion_traces:
        return
    with zipfile.ZipFile(pptx_path) as package:
        for slide_trace in conversion_traces:
            blocks = slide_trace.get('text_blocks') or []
            if not blocks:
                continue
            slide_num = int(slide_trace['slide_num'])
            slide_path = f'ppt/slides/slide{slide_num}.xml'
            try:
                root = ET.fromstring(package.read(slide_path))
            except KeyError as exc:
                raise ValueError(
                    f'[TEXT_PACKAGE_SLIDE] Missing {slide_path}'
                ) from exc
            shapes_by_id = _shape_map(root)
            for block in blocks:
                _validate_block(block, shapes_by_id)
