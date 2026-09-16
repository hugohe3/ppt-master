#!/usr/bin/env python3
"""Regress Edit Native links, inheritance, text, shows, payloads, and proxies.

Usage: python3 -m unittest tests.test_edit_native_batch_b
Examples: Run the command from the scripts directory.
Dependencies: python-pptx and the sibling importer, exporter, and checker.
"""

from __future__ import annotations

import copy
import io
import json
import posixpath
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

from authoring_roundtrip import materialize_flat_authoring_roundtrip
from pptx_delivery_check import audit_pptx_delivery
from pptx_ooxml.clone import clone_presentation_slides
from pptx_to_svg.converter import ConvertOptions, convert_pptx_to_svg
from svg_authoring_view import adopt_authoring_object
from svg_quality.checker import SVGQualityChecker
from svg_to_pptx.pptx_package.cli import main as export_main


NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    's': 'http://www.w3.org/2000/svg',
    'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
}
REL_BASE = NS['r'] + '/'


def _xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def _rewrite_package(path: Path, mutate) -> None:
    with zipfile.ZipFile(path) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    mutate(entries)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def _add_relationship(entries: dict, part: str, rid: str, kind: str, target: str) -> None:
    rels = posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part) + '.rels')
    root = ET.fromstring(entries[rels])
    ET.SubElement(root, '{%s}Relationship' % NS['rel'], {
        'Id': rid, 'Type': REL_BASE + kind, 'Target': target,
    })
    entries[rels] = _xml(root)


def _source(path: Path, *, chart: bool = False, placeholder: bool = False, mutate=None) -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(10), Inches(5.625)
    for _ in range(3):
        slide = prs.slides.add_slide(prs.slide_layouts[1 if placeholder else 6])
        shape = (slide.shapes.title if placeholder else
                 slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(4), Inches(1)))
        shape.text = 'Bonjour'
        shape.text_frame.paragraphs[0].runs[0].font.size = Pt(18)
    if chart:
        data = CategoryChartData()
        data.categories = ['Old A', 'Old B']
        data.add_series('Original', [8, 2])
        prs.slides[0].shapes.add_chart(
            XL_CHART_TYPE.AREA, Inches(1), Inches(2.5), Inches(4), Inches(2), data,
        )
    prs.save(path)
    if mutate:
        _rewrite_package(path, mutate)


def _link_fixture(entries: dict, *, text: bool = False, target: int = 3) -> None:
    part = 'ppt/slides/slide1.xml'
    root = ET.fromstring(entries[part])
    parent = root.find('.//a:rPr' if text else './/p:sp/p:nvSpPr/p:cNvPr', NS)
    ET.SubElement(parent, '{%s}hlinkClick' % NS['a'], {
        '{%s}id' % NS['r']: 'rIdJump', 'action': 'ppaction://hlinksldjump',
    })
    entries[part] = _xml(root)
    _add_relationship(entries, part, 'rIdJump', 'slide', f'slide{target}.xml')


def _show_fixture(entries: dict, *, action: bool = False) -> None:
    root = ET.fromstring(entries['ppt/presentation.xml'])
    shows = ET.SubElement(root, '{%s}custShowLst' % NS['p'])
    show = ET.SubElement(shows, '{%s}custShow' % NS['p'], {'name': 'Demo', 'id': '42'})
    slides = ET.SubElement(show, '{%s}sldLst' % NS['p'])
    ET.SubElement(slides, '{%s}sld' % NS['p'], {
        '{%s}id' % NS['r']: root.find('p:sldIdLst/p:sldId', NS).get('{%s}id' % NS['r']),
    })
    entries['ppt/presentation.xml'] = _xml(root)
    props = ET.fromstring(entries['ppt/presProps.xml'])
    show_pr = ET.SubElement(props, '{%s}showPr' % NS['p'])
    ET.SubElement(show_pr, '{%s}custShow' % NS['p'], {'id': '42'})
    entries['ppt/presProps.xml'] = _xml(props)
    if action:
        root = ET.fromstring(entries['ppt/slides/slide1.xml'])
        ET.SubElement(root.find('.//p:sp/p:nvSpPr/p:cNvPr', NS), '{%s}hlinkClick' % NS['a'], {
            'action': 'ppaction://customshow?id=42&return=true',
        })
        entries['ppt/slides/slide1.xml'] = _xml(root)


def _diagram_fixture(entries: dict) -> None:
    root = ET.fromstring(entries['ppt/slides/slide1.xml'])
    frame = ET.fromstring(
        f'<p:graphicFrame xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}" xmlns:r="{NS["r"]}" '
        'xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram">'
        '<p:nvGraphicFramePr><p:cNvPr id="90" name="Diagram"/><p:cNvGraphicFramePr/>'
        '<p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="6000000" y="1000000"/>'
        '<a:ext cx="2000000" cy="1000000"/></p:xfrm><a:graphic>'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram">'
        '<dgm:relIds r:dm="rIdDiagram"/></a:graphicData></a:graphic></p:graphicFrame>'
    )
    root.find('p:cSld/p:spTree', NS).append(frame)
    entries['ppt/slides/slide1.xml'] = _xml(root)
    entries['ppt/diagrams/data1.xml'] = (
        '<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
        'xmlns:dsp="http://schemas.microsoft.com/office/drawing/2008/diagram">'
        '<dgm:extLst><dsp:dataModelExt relId="rIdDrawing"/></dgm:extLst></dgm:dataModel>'
    ).encode()
    entries['ppt/diagrams/drawing1.xml'] = b'<drawing xmlns="urn:test">Native drawing</drawing>'
    _add_relationship(entries, 'ppt/slides/slide1.xml', 'rIdDiagram', 'diagramData', '../diagrams/data1.xml')
    _add_relationship(entries, 'ppt/slides/slide1.xml', 'rIdDrawing', 'diagramDrawing', '../diagrams/drawing1.xml')


class EditNativeBatchBTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source.pptx'
        self.workspace = self.root / 'workspace'
        self.serial = 0

    def import_source(self, **kwargs) -> None:
        _source(self.source, **kwargs)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            convert_pptx_to_svg(self.source, self.workspace, ConvertOptions(inheritance_mode='both', roundtrip=True))

    def page(self, index: int = 1) -> tuple[Path, ET.Element]:
        path = self.workspace / 'authoring-svg-flat' / f'slide_{index:02d}.svg'
        return path, ET.parse(path).getroot()

    def plan(self, sources: list[int]) -> None:
        pages = []
        for index, source in enumerate(sources):
            row = {'source_slide': source}
            if source in sources[:index]:
                name = f'copy_{index}.svg'
                original, _ = self.page(source)
                original.with_name(name).write_bytes(original.read_bytes())
                row['svg'] = name
            pages.append(row)
        (self.workspace / 'page_plan.json').write_text(json.dumps({
            'schema': 'ppt-master.roundtrip-page-plan.v1', 'pages': pages,
        }), encoding='utf-8')

    def materialize(self):
        self.serial += 1
        return materialize_flat_authoring_roundtrip(
            self.workspace, self.workspace / 'authoring-svg-flat', self.workspace / f'materialized{self.serial}',
        )

    def export(self, *, native: bool = False) -> Path:
        self.serial += 1
        path = self.root / f'output{self.serial}.pptx'
        log = io.StringIO()
        args = [str(self.workspace), '--roundtrip', '-o', str(path)]
        if native:
            args.append('--native-charts-and-tables')
        with redirect_stdout(log), redirect_stderr(log):
            status = export_main(args)
        self.assertEqual(status, 0, log.getvalue())
        self.assertTrue(path.is_file(), log.getvalue())
        return path

    def edit_text(self) -> None:
        path, root = self.page()
        node = next(node for node in root.iter() if node.text and 'Bonjour' in node.text)
        node.text = node.text.replace('Bonjour', 'Bonsoir')
        path.write_bytes(_xml(root))

    def assert_jump(self, path: Path, slide: int, expected: str, count: int = 1) -> None:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read(f'ppt/slides/slide{slide}.xml'))
            rels = ET.fromstring(archive.read(f'ppt/slides/_rels/slide{slide}.xml.rels'))
            targets = {node.get('Id'): node.get('Target') for node in rels}
            jumps = [targets[node.get('{%s}id' % NS['r'])] for node in root.iter()
                     if node.get('action') == 'ppaction://hlinksldjump']
            self.assertEqual(jumps, [expected] * count)

    def test_b1_inherited_shape_jump_reorders_after_text_edit(self) -> None:
        self.import_source(mutate=_link_fixture)
        self.edit_text()
        self.plan([1, 3, 2])
        self.assert_jump(self.export(), 1, 'slide2.xml')

    def test_b1_inherited_text_jump_allows_subset(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, text=True))
        self.edit_text()
        self.plan([1, 3])
        self.assert_jump(self.export(), 1, 'slide2.xml')

    def test_b1_text_link_provenance_survives_new_sibling_run(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, text=True))
        path, root = self.page()
        text = root.find('.//s:text', NS)
        prefix = ET.Element('{%s}tspan' % NS['s'])
        prefix.text = 'New '
        text.insert(0, prefix)
        path.write_bytes(_xml(root))
        self.plan([1, 3])
        self.assert_jump(self.export(), 1, 'slide2.xml')

    def test_b1_deleted_link_allows_omitted_target(self) -> None:
        self.import_source(mutate=_link_fixture)
        path, root = self.page()
        for node in root.iter():
            node.attrib.pop('data-pptx-shape-hyperlink', None)
        for parent in list(root.iter()):
            for node in list(parent):
                if node.tag == '{%s}a' % NS['s']:
                    index = list(parent).index(node)
                    parent.remove(node)
                    for child in reversed(list(node)):
                        parent.insert(index, child)
        path.write_bytes(_xml(root))
        self.plan([1])
        with zipfile.ZipFile(self.export()) as archive:
            self.assertNotIn(b'hlinksldjump', archive.read('ppt/slides/slide1.xml'))

    def test_b1_shape_hyperlink_and_text_link_both_remap(self) -> None:
        def links(entries):
            _link_fixture(entries, text=True)
            root = ET.fromstring(entries['ppt/slides/slide1.xml'])
            ET.SubElement(root.find('.//p:sp/p:nvSpPr/p:cNvPr', NS), '{%s}hlinkClick' % NS['a'], {
                '{%s}id' % NS['r']: 'rIdJump', 'action': 'ppaction://hlinksldjump',
            })
            entries['ppt/slides/slide1.xml'] = _xml(root)
        self.import_source(mutate=links)
        _, root = self.page()
        self.assertTrue(any(node.get('data-pptx-shape-hyperlink') for node in root.iter()))
        self.edit_text()
        self.plan([1, 3])
        self.assert_jump(self.export(), 1, 'slide2.xml', 2)

    def test_b1_repeated_destination_is_rejected(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, text=True))
        self.edit_text()
        self.plan([1, 3, 3])
        with self.assertRaisesRegex(RuntimeError, 'repeated source slide 3'):
            self.materialize()

    def test_b1_repeated_self_jump_follows_each_copy(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, target=1))
        self.edit_text()
        self.plan([1, 1])
        output = self.export()
        self.assert_jump(output, 1, 'slide1.xml')
        self.assert_jump(output, 2, 'slide2.xml')

    def test_b1_new_and_changed_links_use_output_page_numbers(self) -> None:
        for imported in (False, True):
            with self.subTest(imported=imported):
                self.workspace = self.root / f'workspace-{imported}'
                self.import_source(mutate=_link_fixture if imported else None)
                path, root = self.page()
                if imported:
                    root.find('s:a', NS).set('href', '#slide-2')
                else:
                    obj = next(node for node in root if node.get('data-pptx-source-ref') == 'slide:2')
                    root.remove(obj)
                    ET.SubElement(root, '{%s}a' % NS['s'], {'href': '#slide-2'}).append(obj)
                path.write_bytes(_xml(root))
                self.plan([1, 3])
                self.assert_jump(self.export(), 1, 'slide2.xml')

    def test_b1_replacing_source_link_with_new_output_link(self) -> None:
        self.import_source(mutate=_link_fixture)
        path, root = self.page()
        anchor = root.find('s:a', NS)
        anchor.attrib.pop('data-pptx-source-href', None)
        path.write_bytes(_xml(root))
        self.plan([1, 3, 2])
        self.assert_jump(self.export(), 1, 'slide3.xml')

    def test_b1_retained_link_survives_edit_to_another_shape(self) -> None:
        def source_with_second_shape(entries):
            _link_fixture(entries)
            root = ET.fromstring(entries['ppt/slides/slide1.xml'])
            second = copy.deepcopy(root.find('.//p:sp', NS))
            props = second.find('p:nvSpPr/p:cNvPr', NS)
            props.set('id', '33')
            props.remove(props.find('a:hlinkClick', NS))
            second.find('.//a:t', NS).text = 'Second'
            root.find('p:cSld/p:spTree', NS).append(second)
            entries['ppt/slides/slide1.xml'] = _xml(root)
        self.import_source(mutate=source_with_second_shape)
        path, root = self.page()
        obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:33')
        next(node for node in obj.iter() if node.text and 'Second' in node.text).text = 'Changed'
        path.write_bytes(_xml(root))
        self.plan([1, 3, 2])
        self.assert_jump(self.export(), 1, 'slide2.xml')

    def test_b1_adopt_preserves_source_target_after_source_page_is_omitted(self) -> None:
        self.import_source(mutate=_link_fixture)
        adopt_authoring_object(self.workspace / 'authoring-svg-flat', 'slide_01.svg:shape-2', 'slide_02.svg')
        self.plan([2, 3])
        self.assert_jump(self.export(), 1, 'slide2.xml', 2)

    def test_b1_adopted_self_jump_still_targets_original_source(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, target=1))
        adopt_authoring_object(self.workspace / 'authoring-svg-flat', 'slide_01.svg:shape-2', 'slide_02.svg')
        self.plan([2, 1])
        output = self.export()
        self.assert_jump(output, 1, 'slide2.xml', 2)
        self.assert_jump(output, 2, 'slide2.xml')

    def test_b2_inherited_deletion_and_edit_fail(self) -> None:
        def inherited(entries):
            slide = ET.fromstring(entries['ppt/slides/slide1.xml'])
            shape = slide.find('.//p:sp', NS)
            shape.find('p:nvSpPr/p:cNvPr', NS).set('id', '77')
            for part in ('ppt/slideMasters/slideMaster1.xml', 'ppt/slideLayouts/slideLayout7.xml'):
                root = ET.fromstring(entries[part])
                root.find('p:cSld/p:spTree', NS).append(copy.deepcopy(shape))
                entries[part] = _xml(root)
        self.import_source(mutate=inherited)
        path, original = self.page()
        for scope in ('master', 'layout'):
            for operation in ('delete', 'edit'):
                with self.subTest(scope=scope, operation=operation):
                    root = copy.deepcopy(original)
                    obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == f'{scope}:77')
                    if operation == 'delete':
                        next(parent for parent in root.iter() if obj in list(parent)).remove(obj)
                    else:
                        obj.set('opacity', '0.5')
                    path.write_bytes(_xml(root))
                    with self.assertRaisesRegex(RuntimeError, f'{scope}:77.*shared structure'):
                        self.materialize()

    def test_b3_ancestor_translation_changes_native_position(self) -> None:
        self.import_source()
        path, root = self.page()
        obj = next(node for node in root if node.get('data-pptx-source-ref') == 'slide:2')
        root.remove(obj)
        wrapper = ET.SubElement(root, '{%s}g' % NS['s'], {'transform': 'translate(30 0)'})
        wrapper.append(obj)
        path.write_bytes(_xml(root))
        result = self.materialize()
        self.assertIn('slide:2', result.report['documents'][0]['edited_ref_ids'])
        with zipfile.ZipFile(self.export()) as archive:
            slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            self.assertEqual(slide.find('.//p:sp/p:spPr/a:xfrm/a:off', NS).get('x'), str((96 + 30) * 9525))

    def test_b3_root_opacity_and_inherited_font_share_checker_diff(self) -> None:
        self.import_source()
        path, baseline = self.page()
        root = copy.deepcopy(baseline)
        root.set('opacity', '0.25')
        root.set('font-family', 'Arial')
        path.write_bytes(_xml(root))
        record = SimpleNamespace(source_refs={'slide:2': SimpleNamespace(representation='inline')})
        edited, unchanged = SVGQualityChecker._roundtrip_text_diff_ids(root, record, baseline, {}, {})
        self.assertEqual(edited, {id(node) for node in root.iter('{%s}text' % NS['s'])})
        self.assertEqual(unchanged, set())
        with zipfile.ZipFile(self.export()) as archive:
            slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            self.assertIsNotNone(slide.find('.//a:alpha[@val="25000"]', NS))
            self.assertIsNotNone(slide.find('.//a:latin[@typeface="Arial"]', NS))

    def test_b3_proxy_ancestor_change_is_rejected(self) -> None:
        self.import_source(mutate=_diagram_fixture)
        path, root = self.page()
        root.set('opacity', '0.25')
        path.write_bytes(_xml(root))
        with self.assertRaisesRegex(RuntimeError, 'edits source-backed proxy.*slide:90'):
            self.materialize()

    def test_b3_root_transform_fails_instead_of_disappearing(self) -> None:
        self.import_source()
        path, root = self.page()
        root.set('transform', 'translate(30 0)')
        path.write_bytes(_xml(root))
        with self.assertRaisesRegex(RuntimeError, 'Root <svg> transform is unsupported'):
            self.export()

    def test_b3_context_wrapper_preserves_multiple_source_owners(self) -> None:
        def second_shape(entries):
            root = ET.fromstring(entries['ppt/slides/slide1.xml'])
            second = copy.deepcopy(root.find('.//p:sp', NS))
            second.find('p:nvSpPr/p:cNvPr', NS).set('id', '33')
            root.find('p:cSld/p:spTree', NS).append(second)
            entries['ppt/slides/slide1.xml'] = _xml(root)
        self.import_source(mutate=second_shape)
        path, root = self.page()
        wrapper = ET.Element('{%s}g' % NS['s'], {'transform': 'translate(30 0)'})
        for node in list(root):
            if node.get('data-pptx-source-ref', '').startswith('slide:'):
                root.remove(node)
                wrapper.append(node)
        root.append(wrapper)
        path.write_bytes(_xml(root))
        with zipfile.ZipFile(self.export()) as archive:
            slide = ET.fromstring(archive.read('ppt/slides/slide1.xml'))
            offsets = [node.get('x') for node in slide.findall('.//p:sp/p:spPr/a:xfrm/a:off', NS)]
            self.assertEqual(offsets, [str(126 * 9525)] * 2)

    def test_b4_fill_edit_preserves_unchanged_native_text(self) -> None:
        def rich_text(entries):
            part = 'ppt/slides/slide1.xml'
            root = ET.fromstring(entries[part])
            tx = root.find('.//p:sp/p:txBody', NS)
            body = tx.find('a:bodyPr', NS)
            for child in list(body):
                body.remove(child)
            ET.SubElement(body, '{%s}normAutofit' % NS['a'], {'fontScale': '80000'})
            para = tx.find('a:p', NS)
            props = ET.Element('{%s}pPr' % NS['a'])
            ET.SubElement(props, '{%s}buAutoNum' % NS['a'], {'type': 'arabicPeriod'})
            para.insert(0, props)
            para.find('a:r/a:rPr', NS).set('lang', 'fr-FR')
            fld = ET.SubElement(para, '{%s}fld' % NS['a'], {
                'id': '{11111111-1111-1111-1111-111111111111}', 'type': 'datetime1',
            })
            ET.SubElement(fld, '{%s}rPr' % NS['a'], {'lang': 'fr-FR'})
            ET.SubElement(fld, '{%s}t' % NS['a']).text = '2026'
            entries[part] = _xml(root)
        self.import_source(mutate=rich_text)
        path, root = self.page()
        obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:2')
        obj.find('*[@data-pptx-part="geometry"]').set('fill', '#FF0000')
        path.write_bytes(_xml(root))
        with zipfile.ZipFile(self.source) as source, zipfile.ZipFile(self.export()) as output:
            expected = ET.fromstring(source.read('ppt/slides/slide1.xml')).find('.//p:sp/p:txBody', NS)
            result = ET.fromstring(output.read('ppt/slides/slide1.xml'))
            actual = result.find('.//p:sp/p:txBody', NS)
            actual.tail = expected.tail = None
            self.assertEqual(ET.tostring(actual), ET.tostring(expected))
            self.assertIsNotNone(result.find('.//a:srgbClr[@val="FF0000"]', NS))

    def test_b5_page_plan_resets_custom_show_selection(self) -> None:
        _source(self.source, mutate=_show_fixture)
        output = self.root / 'clone.pptx'
        clone_presentation_slides(self.source, (1,), output)
        with zipfile.ZipFile(output) as archive:
            props = ET.fromstring(archive.read('ppt/presProps.xml'))
            self.assertIsNone(props.find('p:showPr/p:custShow', NS))

    def test_b4_fill_edit_keeps_placeholder_and_text_effects(self) -> None:
        def effects(entries):
            part = 'ppt/slides/slide1.xml'
            root = ET.fromstring(entries[part])
            rpr = root.find('.//p:sp/p:txBody/a:p/a:r/a:rPr', NS)
            effects = ET.SubElement(rpr, '{%s}effectLst' % NS['a'])
            glow = ET.SubElement(effects, '{%s}glow' % NS['a'], {'rad': '63500'})
            ET.SubElement(glow, '{%s}srgbClr' % NS['a'], {'val': 'FFFF00'})
            shape_effect = ET.SubElement(root.find('.//p:sp/p:spPr', NS), '{%s}effectLst' % NS['a'])
            shadow = ET.SubElement(shape_effect, '{%s}outerShdw' % NS['a'], {
                'blurRad': '38100', 'dist': '19050', 'dir': '5400000', 'algn': 'ctr', 'rotWithShape': '0',
            })
            ET.SubElement(shadow, '{%s}srgbClr' % NS['a'], {'val': '000000'})
            entries[part] = _xml(root)
        self.import_source(placeholder=True, mutate=effects)
        path, root = self.page()
        obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:2')
        obj.find('*[@data-pptx-part="geometry"]').set('fill', '#FF0000')
        path.write_bytes(_xml(root))
        with zipfile.ZipFile(self.source) as source, zipfile.ZipFile(self.export()) as output:
            original = ET.fromstring(source.read('ppt/slides/slide1.xml')).find('.//p:sp', NS)
            result = ET.fromstring(output.read('ppt/slides/slide1.xml')).find('.//p:sp', NS)
            old_body, new_body = original.find('p:txBody', NS), result.find('p:txBody', NS)
            old_body.tail = new_body.tail = None
            self.assertEqual(ET.tostring(new_body), ET.tostring(old_body))
            self.assertEqual(result.find('p:nvSpPr/p:nvPr/p:ph', NS).attrib,
                             original.find('p:nvSpPr/p:nvPr/p:ph', NS).attrib)
            self.assertIsNotNone(result.find('p:spPr/a:effectLst/a:outerShdw', NS))

    def test_b4_relationship_text_keeps_links_without_unsafe_payload_copy(self) -> None:
        self.import_source(mutate=lambda entries: _link_fixture(entries, text=True))
        path, root = self.page()
        obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:2')
        obj.find('*[@data-pptx-part="geometry"]').set('fill', '#FF0000')
        path.write_bytes(_xml(root))
        result = self.materialize()
        materialized = ET.parse(result.svg_files[0]).getroot()
        self.assertIsNone(materialized.find('.//s:metadata[@data-pptx-part="txbody"]', NS))
        self.assert_jump(self.export(), 1, 'slide3.xml')

    def test_b4_edited_text_is_not_overwritten_by_source_body(self) -> None:
        self.import_source()
        self.edit_text()
        with zipfile.ZipFile(self.export()) as archive:
            xml = archive.read('ppt/slides/slide1.xml')
            self.assertIn(b'Bonsoir', xml)
            self.assertNotIn(b'Bonjour', xml)

    def test_b5_page_plan_resets_source_slide_range(self) -> None:
        def range_selection(entries):
            root = ET.fromstring(entries['ppt/presProps.xml'])
            show = ET.SubElement(root, '{%s}showPr' % NS['p'], {'loop': '1'})
            ET.SubElement(show, '{%s}sldRg' % NS['p'], {'st': '2', 'end': '3'})
            entries['ppt/presProps.xml'] = _xml(root)
        _source(self.source, mutate=range_selection)
        output = self.root / 'clone.pptx'
        clone_presentation_slides(self.source, (1,), output)
        with zipfile.ZipFile(output) as archive:
            show = ET.fromstring(archive.read('ppt/presProps.xml')).find('p:showPr', NS)
            self.assertIsNotNone(show.find('p:sldAll', NS))
            self.assertIsNone(show.find('p:sldRg', NS))
            self.assertEqual(show.get('loop'), '1')

    def test_b5_delivery_checks_custom_show_semantic_closure(self) -> None:
        _source(self.source, mutate=lambda entries: _show_fixture(entries, action=True))
        valid = audit_pptx_delivery(self.source)
        self.assertFalse(any(item['code'] == 'dangling_custom_show_reference' for item in valid['errors']))

        def remove_show(entries):
            root = ET.fromstring(entries['ppt/presentation.xml'])
            root.remove(root.find('p:custShowLst', NS))
            entries['ppt/presentation.xml'] = _xml(root)
        _rewrite_package(self.source, remove_show)
        broken = audit_pptx_delivery(self.source)
        issues = [item for item in broken['errors'] if item['code'] == 'dangling_custom_show_reference']
        self.assertEqual(len(issues), 2, broken)
        self.assertTrue(all('42' in item['message'] for item in issues))

    def test_b5_page_plan_rejects_retained_custom_show_action(self) -> None:
        _source(self.source, mutate=lambda entries: _show_fixture(entries, action=True))
        with self.assertRaisesRegex(RuntimeError, '[Ss]lide 1.*42'):
            clone_presentation_slides(self.source, (1,), self.root / 'clone.pptx')

    def test_b5_deleted_custom_show_action_no_longer_blocks_plan(self) -> None:
        self.import_source(mutate=lambda entries: _show_fixture(entries, action=True))
        path, root = self.page()
        for parent in root.iter():
            for child in list(parent):
                if child.get('data-pptx-source-ref') == 'slide:2':
                    parent.remove(child)
        path.write_bytes(_xml(root))
        self.plan([1])
        self.export()

    def test_b6_native_chart_replacement_prunes_old_payloads(self) -> None:
        self.import_source(chart=True)
        path, root = self.page()
        marker = next(node for node in root.iter() if node.get('data-pptx-replace-with') == 'chart')
        metadata = marker.find('s:metadata[@type="application/json"]', NS)
        payload = json.loads(metadata.text)
        payload['series'][0]['values'] = [70, 30]
        metadata.text = json.dumps(payload)
        path.write_bytes(_xml(root))
        self.plan([1])
        with zipfile.ZipFile(self.export(native=True)) as archive:
            charts = [name for name in archive.namelist() if name.startswith('ppt/charts/')
                      and name.endswith('.xml') and '/_rels/' not in name]
            self.assertEqual(len(charts), 1, charts)
            self.assertIn(b'70', archive.read(charts[0]))
            books = [name for name in archive.namelist() if name.startswith('ppt/embeddings/')]
            self.assertEqual(len(books), 1, books)

    def test_b6_delivery_reports_xml_unused_relationships(self) -> None:
        self.import_source(chart=True)
        valid = audit_pptx_delivery(self.source)
        self.assertFalse(any(item['code'] == 'unreferenced_slide_relationship' for item in valid['errors']))
        _rewrite_package(self.source, lambda entries: _add_relationship(
            entries, 'ppt/slides/slide1.xml', 'rIdUnused', 'chart', '../charts/chart1.xml',
        ))
        report = audit_pptx_delivery(self.source)
        issues = [item for item in report['advisories'] if item['code'] == 'unreferenced_slide_relationship']
        self.assertEqual(len(issues), 1, report)
        self.assertIn('rIdUnused', issues[0]['message'])

    def test_b6_deleted_graphic_frame_prunes_diagram_without_page_plan(self) -> None:
        self.import_source(mutate=_diagram_fixture)
        path, root = self.page()
        for parent in root.iter():
            for child in list(parent):
                if child.get('data-pptx-source-ref') == 'slide:90':
                    parent.remove(child)
        path.write_bytes(_xml(root))
        with zipfile.ZipFile(self.export()) as archive:
            self.assertFalse(any(name.startswith('ppt/diagrams/') for name in archive.namelist()))
            self.assertNotIn(b'rIdDiagram', archive.read('ppt/slides/_rels/slide1.xml.rels'))

    def test_b6_diagram_drawing_relationship_ids_are_part_local(self) -> None:
        def modern_diagram(entries):
            _diagram_fixture(entries)
            entries['ppt/diagrams/_rels/data1.xml.rels'] = _xml(ET.Element('{%s}Relationships' % NS['rel']))
            entries['ppt/diagrams/modern.xml'] = entries['ppt/diagrams/drawing1.xml']
            _add_relationship(entries, 'ppt/diagrams/data1.xml', 'rIdDrawing', 'diagramDrawing', 'modern.xml')
        self.import_source(mutate=modern_diagram)
        report = audit_pptx_delivery(self.source)
        unused = [item for item in report['advisories'] if item['code'] == 'unreferenced_slide_relationship']
        self.assertEqual(len(unused), 1, report)
        self.assertIn('rIdDrawing', unused[0]['message'])
        self.edit_text()
        output = self.export()
        with zipfile.ZipFile(output) as archive:
            self.assertIn('ppt/diagrams/modern.xml', archive.namelist())
            self.assertNotIn('ppt/diagrams/drawing1.xml', archive.namelist())
        self.assertFalse(any(item['code'] == 'unreferenced_slide_relationship'
                             for item in audit_pptx_delivery(output)['errors']))

    def test_b7_retained_diagram_and_replaced_chart_coexist(self) -> None:
        self.import_source(chart=True, mutate=_diagram_fixture)
        path, root = self.page()
        summary = json.loads((path.parent / 'authoring_summary.json').read_text())
        self.assertIn('"source_proxies": 1', json.dumps(summary))
        marker = next(node for node in root.iter() if node.get('data-pptx-replace-with') == 'chart')
        metadata = marker.find('s:metadata[@type="application/json"]', NS)
        payload = json.loads(metadata.text)
        payload['series'][0]['values'][0] = 98765
        metadata.text = json.dumps(payload)
        path.write_bytes(_xml(root))
        with zipfile.ZipFile(self.source) as source, zipfile.ZipFile(self.export(native=True)) as output:
            self.assertEqual(output.read('ppt/diagrams/data1.xml'), source.read('ppt/diagrams/data1.xml'))
            self.assertEqual(output.read('ppt/diagrams/drawing1.xml'), source.read('ppt/diagrams/drawing1.xml'))
            charts = [name for name in output.namelist() if name.startswith('ppt/charts/') and name.endswith('.xml')]
            self.assertEqual(len(charts), 1, charts)
            self.assertIn(b'98765', output.read(charts[0]))

    def test_b7_diagram_is_atomic_proxy(self) -> None:
        self.import_source(mutate=_diagram_fixture)
        path, root = self.page()
        obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:90')
        self.assertEqual(obj.get('data-pptx-source-proxy'), 'native-restore')
        with self.assertRaisesRegex(ValueError, 'Cannot adopt source proxy'):
            adopt_authoring_object(path.parent, f'{path.name}:{obj.get("id")}', 'slide_02.svg')
        obj.set('opacity', '0.5')
        path.write_bytes(_xml(root))
        with self.assertRaisesRegex(RuntimeError, 'edits source-backed proxy'):
            self.materialize()

    def test_b7_nested_diagram_is_proxy_and_rejects_adopting_its_parent(self) -> None:
        def nested_diagram(entries):
            _diagram_fixture(entries)
            root = ET.fromstring(entries['ppt/slides/slide1.xml'])
            tree = root.find('p:cSld/p:spTree', NS)
            diagram = tree.find('p:graphicFrame', NS)
            tree.remove(diagram)
            group = ET.fromstring(
                f'<p:grpSp xmlns:p="{NS["p"]}" xmlns:a="{NS["a"]}">'
                '<p:nvGrpSpPr><p:cNvPr id="91" name="Container"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="9000000" cy="5000000"/>'
                '<a:chOff x="0" y="0"/><a:chExt cx="9000000" cy="5000000"/></a:xfrm></p:grpSpPr></p:grpSp>'
            )
            group.append(diagram)
            tree.append(group)
            entries['ppt/slides/slide1.xml'] = _xml(root)
        self.import_source(mutate=nested_diagram)
        path, root = self.page()
        self.assertTrue(any(node.get('data-pptx-source-proxy') == 'native-restore' for node in root.iter()))
        self.materialize()
        with self.assertRaisesRegex(ValueError, 'Cannot adopt source proxy'):
            adopt_authoring_object(path.parent, 'slide_01.svg:shape-91', 'slide_02.svg')

    def test_b7_ole_and_unknown_graphic_frames_are_proxies(self) -> None:
        for kind in ('ole', 'unknown'):
            with self.subTest(kind=kind):
                self.workspace = self.root / f'workspace-{kind}'
                def unsupported(entries):
                    _diagram_fixture(entries)
                    root = ET.fromstring(entries['ppt/slides/slide1.xml'])
                    root.find('.//a:graphicData', NS).set('uri', f'{NS["p"]}/{kind}')
                    entries['ppt/slides/slide1.xml'] = _xml(root)
                self.import_source(mutate=unsupported)
                _, root = self.page()
                obj = next(node for node in root.iter() if node.get('data-pptx-source-ref') == 'slide:90')
                self.assertEqual(obj.get('data-pptx-source-proxy'), 'native-restore')
