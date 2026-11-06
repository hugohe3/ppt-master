#!/usr/bin/env python3
"""
PPT Master - Round-trip Group Restore Regression Tests

Preserve unedited native siblings and their ancestor rotation after image replacement.

Usage:
    python3 -m unittest tests.test_roundtrip_group_restore

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and local PPT Master modules.
"""

import contextlib
import hashlib
import io
import math
import posixpath
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.builder import create_pptx_with_native_svg
from svg_to_pptx.pptx_package.cli import main as export_main

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "s": "http://www.w3.org/2000/svg"}
EMU = 9525


def write_png(path: Path, color: tuple[int, int, int]) -> None:
    """Write a small RGB fixture using only the standard library."""
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 8) * 8)) + chunk(b'IEND', b''))


def make_source(root: Path, nested: bool) -> Path:
    """Create a native rotated group with one picture and an unedited label."""
    write_png(root / "original.png", (255, 0, 0))
    svg = root / "slide_01.svg"
    svg.write_text(
        f'<svg xmlns="{NS["s"]}" viewBox="0 0 960 720" font-family="Arial">'
        '<image id="photo" x="150" y="150" width="180" height="100" href="original.png"/>'
        '<text id="label" x="160" y="340" font-size="24" fill="#123456">Unchanged label</text></svg>',
        encoding="utf-8",
    )
    base = root / "base.pptx"
    assert create_pptx_with_native_svg([svg], base, resource_root=root, pptx_structure="flat",
                                     use_compat_mode=False, workers=1, transition=None, verbose=False)
    with ZipFile(base) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    slide = ET.fromstring(parts["ppt/slides/slide1.xml"])
    tree = slide.find("p:cSld/p:spTree", NS)
    shapes = [node for node in tree if node.tag in {f'{{{NS["p"]}}}pic', f'{{{NS["p"]}}}sp'}]
    group_id = max(int(n.get('id')) for n in slide.findall('.//p:cNvPr', NS)) + 1

    def group(identifier, rotation):
        return ET.fromstring(
            f'<p:grpSp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
            f'<p:nvGrpSpPr><p:cNvPr id="{identifier}" name="Group {identifier}"/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr>'
            f'<a:xfrm rot="{rotation}"><a:off x="{120 * EMU}" y="{100 * EMU}"/>'
            f'<a:ext cx="{500 * EMU}" cy="{400 * EMU}"/>'
            f'<a:chOff x="{120 * EMU}" y="{100 * EMU}"/>'
            f'<a:chExt cx="{500 * EMU}" cy="{400 * EMU}"/>'
            '</a:xfrm></p:grpSpPr></p:grpSp>'
        )
    outer = group(group_id, 600000 if nested else 1620000)
    owner = outer
    if nested:
        owner = group(group_id + 1, 1500000)
        outer.append(owner)
    for shape in shapes:
        tree.remove(shape)
        owner.append(shape)
    tree.append(outer)
    parts["ppt/slides/slide1.xml"] = ET.tostring(slide)
    source = root / "source.pptx"
    with ZipFile(source, "w") as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    return source


def replace_picture(workspace: Path, *, bytes_only: bool = False) -> None:
    """Replace just the image bytes or href in the authoring workspace."""
    path = workspace / "authoring-svg-flat/slide_01.svg"
    tree = ET.parse(path)
    picture = next(node for node in tree.getroot().iter() if node.tag == f'{{{NS["s"]}}}image')
    if bytes_only:
        write_png((path.parent / picture.get("href")).resolve(), (0, 0, 255))
    else:
        write_png(workspace / "images/replacement.png", (0, 0, 255))
        picture.set("href", "../images/replacement.png")
        tree.write(path, encoding="utf-8")


def geometry(path: Path) -> dict:
    """Read world corners by composing native group transforms independently."""
    with ZipFile(path) as archive:
        slide = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        relationships = ET.fromstring(archive.read("ppt/slides/_rels/slide1.xml.rels"))
        image_hashes = {
            rel.get("Id"): hashlib.sha256(archive.read(posixpath.normpath(
                posixpath.join("ppt/slides", rel.get("Target")),
            ))).hexdigest()
            for rel in relationships if rel.get("Type", "").endswith("/image")
        }
    result = {}

    def apply(point, xfrm, *, group=False):
        off = xfrm.find("a:off", NS)
        ext = xfrm.find("a:ext", NS)
        x, y = float(off.get('x')), float(off.get('y'))
        w, h = float(ext.get('cx')), float(ext.get('cy'))
        px, py = point
        if group:
            ch_off, ch_ext = xfrm.find('a:chOff', NS), xfrm.find('a:chExt', NS)
            px = x + (px - float(ch_off.get('x'))) * w / float(ch_ext.get('cx'))
            py = y + (py - float(ch_off.get('y'))) * h / float(ch_ext.get('cy'))
        cx, cy = x + w / 2, y + h / 2
        px, py = px - cx, py - cy
        if xfrm.get('flipH') in {'1', 'true'}:
            px = -px
        if xfrm.get('flipV') in {'1', 'true'}:
            py = -py
        angle = math.radians(float(xfrm.get('rot', '0')) / 60000)
        return (cx + px * math.cos(angle) - py * math.sin(angle),
                cy + px * math.sin(angle) + py * math.cos(angle))

    def walk(parent, ancestors):
        for node in parent:
            if node.tag == f'{{{NS["p"]}}}grpSp':
                walk(node, [node.find('p:grpSpPr/a:xfrm', NS), *ancestors])
            elif node.tag in {f'{{{NS["p"]}}}sp', f'{{{NS["p"]}}}pic'}:
                xfrm = node.find('p:spPr/a:xfrm', NS)
                off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
                x, y = float(off.get('x')), float(off.get('y'))
                w, h = float(ext.get('cx')), float(ext.get('cy'))
                corners = []
                for point in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
                    point = apply(point, xfrm)
                    for ancestor in ancestors:
                        point = apply(point, ancestor, group=True)
                    corners.append(point)
                key = 'label' if node.tag.endswith('}sp') else 'picture'
                result[key] = {'corners': corners, 'xml': ET.tostring(node).decode(),
                               'rotations': [a.get('rot', '0') for a in ancestors]}
                if key == 'picture':
                    rel_id = node.find('.//a:blip', NS).get(f'{{{NS["r"]}}}embed')
                    result[key]['media_sha256'] = image_hashes[rel_id]
    walk(slide.find('p:cSld/p:spTree', NS), [])
    return result


class RoundtripGroupRestoreTests(unittest.TestCase):
    def test_restore_placeholder_does_not_narrow_compound_transform_support(self) -> None:
        for transform in ("translate(25 15) rotate(27 360 300)",
                          "rotate(27 360 300) translate(720 0) scale(-1 1)"):
            with self.subTest(transform=transform), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "compound.svg"
                path.write_text(
                    f'<svg xmlns="{NS["s"]}" viewBox="0 0 960 720"><g transform="{transform}">'
                    '<rect x="100" y="100" width="80" height="60"/>'
                    '<g data-pptx-object="group" data-pptx-roundtrip-object="native-restore-placeholder">'
                    '<rect x="200" y="100" width="80" height="60"/></g></g></svg>',
                    encoding="utf-8",
                )
                slide, *_rest = convert_svg_to_slide_shapes(path, resource_root=path.parent)
                self.assertIn("spTree", slide)

    def test_picture_href_preserves_unedited_label_world_geometry(self) -> None:
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    source = make_source(root, nested)
                    workspace = root / "workspace"
                    convert_pptx_to_svg(source, workspace, ConvertOptions(inheritance_mode="both", roundtrip=True))
                    replace_picture(workspace)
                    output = root / "result.pptx"
                    self.assertEqual(export_main([str(workspace), '--roundtrip', '-o', str(output)]), 0)
                before, after = geometry(source), geometry(output)
                self.assertEqual(before['label']['xml'], after['label']['xml'])
                self.assertEqual(after['picture']['media_sha256'], hashlib.sha256(
                    (workspace / 'images/replacement.png').read_bytes()).hexdigest())
                for key in ('label', 'picture'):
                    for original, actual in zip(before[key]['corners'], after[key]['corners']):
                        for expected, observed in zip(original, actual):
                            self.assertAlmostEqual(expected, observed, delta=2)
