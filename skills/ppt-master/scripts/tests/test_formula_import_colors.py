#!/usr/bin/env python3
"""
PPT Master - Native Formula Import Color Regression Tests

Exercise formula color normalization through the public import and SVG
converters, including native re-export and opaque text-body retention.

Usage:
    python3 -m unittest tests.test_formula_import_colors

Examples:
    Run the module from the scripts directory.

Dependencies:
    Standard library and the local PPT Master converters.
"""

from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
import zipfile
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from pptx_to_svg.color_resolver import ColorPalette, resolve_color  # noqa: E402
from pptx_to_svg.formula_import import FormulaImportError, import_formula  # noqa: E402
from pptx_to_svg.ooxml_loader import OoxmlPackage  # noqa: E402
from pptx_to_svg.slide_to_svg import assemble_slide  # noqa: E402
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes  # noqa: E402
from svg_to_pptx.drawingml.theme_colors import ThemeColorSpec  # noqa: E402
from svg_to_pptx.native_objects.formula_compiler import (  # noqa: E402
    FormulaCompileError,
    validate_omml_fragment,
)

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'a14': 'http://schemas.microsoft.com/office/drawing/2010/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    's': 'http://www.w3.org/2000/svg',
}
THEME = ThemeColorSpec(
    slots={'dk1': '173B57', 'accent2': 'C0504D'},
    roles={'text': '173B57', 'accent': 'C0504D'},
    role_slots={'text': 'dk1', 'accent': 'accent2'},
)


class FormulaImportColorTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.palette = ColorPalette(None, None, strict=False)
        self.palette.scheme.update(THEME.slots)

    def _export(self, svg: str, *, themed: bool = False) -> ET.Element:
        path = self.root / 'formula.svg'
        path.write_text(svg, encoding='utf-8')
        xml, *_ = convert_svg_to_slide_shapes(
            path, resource_root=self.root, theme_color_spec=THEME if themed else None,
        )
        return ET.fromstring(xml)

    def _source(
        self, latex: str = r'\frac{x}{y}+z', *, display: bool = False,
        themed: bool = False, style: str = '', prefix: str = 'before ',
    ) -> ET.Element:
        if display:
            payload = escape(json.dumps({
                'latex': latex, 'display': 'block', 'font_size': 28,
                'color': '#173B57', 'align': 'center',
            }))
            body = (
                '<g id="formula" data-pptx-replace-with="formula" '
                'data-pptx-x="100" data-pptx-y="100" data-pptx-width="800" '
                'data-pptx-height="100" data-pptx-bounds="100 100 800 100">'
                f'<metadata type="application/json">{payload}</metadata>'
                '<text x="100" y="150" font-size="28" fill="#173B57">x/y+z</text></g>'
            )
        else:
            body = (
                '<text x="100" y="150" font-size="28" fill="#173B57">'
                f'{prefix}<tspan data-pptx-inline-formula="{escape(latex, quote=True)}" '
                f'{style}>x/y+z</tspan> after</text>'
            )
        return self._export(f'<svg xmlns="{NS["s"]}" viewBox="0 0 1280 720">{body}</svg>', themed=themed)

    def _import(self, source: ET.Element, *, strict: bool = False):
        path = self.root / 'source.pptx'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('ppt/presentation.xml', (
                f'<p:presentation xmlns:p="{NS["p"]}" xmlns:r="{NS["r"]}">'
                '<p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst>'
                '<p:sldSz cx="12192000" cy="6858000"/></p:presentation>'
            ))
            archive.writestr('ppt/_rels/presentation.xml.rels', (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rId1" Type="{NS["r"]}/slide" Target="slides/slide1.xml"/>'
                '</Relationships>'
            ))
            archive.writestr('ppt/slides/slide1.xml', ET.tostring(source))
        diagnostics = []
        with OoxmlPackage(path) as package:
            svg, _ = assemble_slide(
                package, next(package.iter_slides()), self.palette,
                strict=strict, diagnostics=diagnostics,
            )
        return ET.fromstring(svg), diagnostics

    def _zone(self, slide: ET.Element) -> ET.Element:
        zones = slide.findall('.//a14:m', NS)
        self.assertEqual(len(zones), 1)
        return zones[0]

    def _colors(self, slide: ET.Element) -> list[tuple]:
        result = []
        for owner in self._zone(slide).iter():
            if owner.tag not in {f'{{{NS["m"]}}}r', f'{{{NS["m"]}}}ctrlPr'}:
                continue
            fill = owner.find('a:rPr/a:solidFill', NS)
            self.assertIsNotNone(fill)
            rgb, alpha = resolve_color(list(fill)[0], self.palette, strict=True)
            text = owner.find('m:t', NS)
            result.append((owner.tag, text.text if text is not None else '', rgb, alpha))
        return result

    def _assert_reexport(self, source: ET.Element, *, display: bool = False) -> ET.Element:
        imported, diagnostics = self._import(source)
        self.assertFalse(diagnostics)
        attribute = 'data-pptx-replace-with' if display else 'data-pptx-inline-formula'
        self.assertEqual(len([node for node in imported.iter() if node.get(attribute)]), 1)
        rebuilt = self._export(ET.tostring(imported, encoding='unicode'), themed=True)
        self.assertEqual(self._colors(source), self._colors(rebuilt))
        return imported

    def test_srgb_inline_and_block_roundtrip(self) -> None:
        for display in (False, True):
            with self.subTest(display=display):
                self._assert_reexport(self._source(display=display), display=display)

    def test_scheme_colors_include_control_properties(self) -> None:
        source = self._source(themed=True)
        self.assertIsNotNone(source.find('.//m:ctrlPr/a:rPr/a:solidFill/a:schemeClr', NS))
        self._assert_reexport(source)

    def test_block_scheme_color_uses_metadata_rgb(self) -> None:
        source = self._source(display=True)
        for color in self._zone(source).iter(f'{{{NS["a"]}}}srgbClr'):
            color.tag = f'{{{NS["a"]}}}schemeClr'
            color.set('val', 'dk1')
        imported = self._assert_reexport(source, display=True)
        metadata = imported.find('.//s:g[@data-pptx-replace-with="formula"]/s:metadata', NS)
        self.assertEqual(json.loads(metadata.text)['color'], '#173B57')

    def test_current_palette_color_map_is_honored(self) -> None:
        source = self._source(themed=True)
        self.palette.clr_map['tx1'] = 'accent2'
        for color in self._zone(source).iter(f'{{{NS["a"]}}}schemeClr'):
            color.set('val', 'tx1')
        imported = self._assert_reexport(source)
        marker = imported.find('.//s:tspan[@data-pptx-inline-formula]', NS)
        self.assertEqual(marker.get('fill'), '#C0504D')

    def test_uniform_alpha_and_surrounding_opaque_runs(self) -> None:
        for alpha in ('0', '0.43217', '1'):
            for prefix in ('before ', ''):
                with self.subTest(alpha=alpha, prefix=prefix):
                    source = self._source(style=f'opacity="{alpha}"', prefix=prefix)
                    imported = self._assert_reexport(source)
                    marker = imported.find('.//s:tspan[@data-pptx-inline-formula]', NS)
                    self.assertEqual(float(marker.get('fill-opacity', '1')), float(alpha))
                    rebuilt = self._export(ET.tostring(imported, encoding='unicode'))
                    for run in rebuilt.findall('.//a14:m/../a:r', NS):
                        fill = run.find('a:rPr/a:solidFill', NS)
                        self.assertEqual(resolve_color(list(fill)[0], self.palette)[1], 1.0)

    def test_formula_opacity_overrides_translucent_parent_text(self) -> None:
        source = self._source(prefix='<tspan opacity="0.25">before </tspan>')
        imported = self._assert_reexport(source)
        rebuilt = self._export(ET.tostring(imported, encoding='unicode'))
        runs = rebuilt.findall('.//a14:m/../a:r', NS)
        self.assertEqual(
            [resolve_color(list(run.find('a:rPr/a:solidFill', NS))[0], self.palette)[1] for run in runs],
            [0.25, 1.0],
        )

    def test_local_colors_full_partial_and_nested_controls(self) -> None:
        for latex in (
            r'\color{red}\frac{x}{y}',
            r'\textcolor{red}{x}+\frac{y}{z}',
            r'\color{red}\frac{x}{\textcolor{blue}{\sqrt{y}}}+\textcolor{green}{z}',
        ):
            for display, alpha in ((False, '1'), (False, '0.43217'), (True, '1')):
                with self.subTest(latex=latex, display=display, alpha=alpha):
                    self._assert_reexport(self._source(
                        latex, display=display, themed=True, style=f'fill-opacity="{alpha}"',
                    ), display=display)

    def _marker_latex(self, imported: ET.Element, *, display: bool) -> str:
        if display:
            metadata = imported.find('.//s:g[@data-pptx-replace-with="formula"]/s:metadata', NS)
            return json.loads(metadata.text)['latex']
        return imported.find('.//s:tspan[@data-pptx-inline-formula]', NS).get('data-pptx-inline-formula')

    def test_default_colors_do_not_appear_in_latex(self) -> None:
        for latex in (r'\frac{x}{y}+z', r'\int_0^1 x', r'\sum_{n=1}^N \left(x_n\right)'):
            for display in (False, True):
                for themed in (False, True):
                    with self.subTest(latex=latex, display=display, themed=themed):
                        imported = self._assert_reexport(
                            self._source(latex, display=display, themed=themed), display=display,
                        )
                        self.assertNotIn(r'\textcolor', self._marker_latex(imported, display=display))

    def test_partial_local_color_emits_only_one_scope(self) -> None:
        for local in ('x', r'\frac{x}{y}'):
            for display in (False, True):
                with self.subTest(local=local, display=display):
                    source = self._source(
                        r'a+b+c+\textcolor{red}{' + local + '}', display=display, themed=True,
                    )
                    imported = self._assert_reexport(source, display=display)
                    latex = self._marker_latex(imported, display=display)
                    self.assertEqual(latex.count(r'\textcolor'), 1)
                    self.assertIn(r'\textcolor{#FF0000}{' + local + '}', latex)
                    self.assertNotIn('#173B57', latex)

    def test_nested_controls_share_local_color_scope(self) -> None:
        for display in (False, True):
            with self.subTest(display=display):
                source = self._source(
                    r'a+b+c+d+\textcolor{red}{\frac{x}{\sqrt{y}}}', display=display, themed=True,
                )
                imported = self._assert_reexport(source, display=display)
                latex = self._marker_latex(imported, display=display)
                self.assertEqual(latex.count(r'\textcolor'), 1)
                self.assertIn(r'\textcolor{#FF0000}{\frac{x}{\sqrt{y}}}', latex)

    def test_nested_local_scope_can_restore_base_color(self) -> None:
        for display in (False, True):
            with self.subTest(display=display):
                source = self._source(
                    r'a+b+c+\textcolor{red}{\frac{x}{\textcolor{#173B57}{\sqrt{y}}}}+d',
                    display=display, themed=True,
                )
                imported = self._assert_reexport(source, display=display)
                latex = self._marker_latex(imported, display=display)
                self.assertEqual(latex.count(r'\textcolor'), 2)
                self.assertIn(r'\textcolor{#173B57}{\sqrt{y}}', latex)
                self.assertTrue(latex.endswith(r'\mathrm{+}d'))

    def test_structural_color_different_from_runs_is_preserved(self) -> None:
        for display in (False, True):
            with self.subTest(display=display):
                source = self._source(display=display)
                control = self._zone(source).find('.//m:ctrlPr/a:rPr/a:solidFill/a:srgbClr', NS)
                control.set('val', 'FF0000')
                imported = self._assert_reexport(source, display=display)
                latex = self._marker_latex(imported, display=display)
                self.assertIn(
                    r'\textcolor{#FF0000}{\frac{\textcolor{#173B57}{x}}{\textcolor{#173B57}{y}}}',
                    latex,
                )
                self.assertTrue(latex.endswith(r'\mathrm{+}z'))

    def _assert_rejected(self, source: ET.Element, *, display: bool = False) -> None:
        before = ET.tostring(source)
        with self.assertRaises(FormulaImportError):
            import_formula(self._zone(source), display=display, palette=self.palette)
        imported, diagnostics = self._import(source)
        self.assertIn('formula-not-reconstructed', [item.code for item in diagnostics])
        self.assertFalse(any(node.get('data-pptx-inline-formula') for node in imported.iter()))
        self.assertFalse(any(node.get('data-pptx-replace-with') == 'formula' for node in imported.iter()))
        metadata = imported.find('.//s:metadata[@data-pptx-part="txbody"]', NS)
        self.assertIsNotNone(metadata)
        retained = ET.fromstring(base64.b64decode(metadata.text))
        self.assertEqual(ET.tostring(retained).strip(), ET.tostring(source.find('.//p:txBody', NS)).strip())
        self.assertEqual(ET.tostring(source), before)
        with self.assertRaisesRegex(ValueError, 'Office Math was not reconstructed'):
            self._import(source, strict=True)

    def test_reject_multiple_colors(self) -> None:
        source = self._source()
        fill = self._zone(source).find('.//a:solidFill', NS)
        ET.SubElement(fill, f'{{{NS["a"]}}}schemeClr', {'val': 'accent2'})
        self._assert_rejected(source)

    def test_reject_unresolved_theme_color(self) -> None:
        source = self._source(themed=True)
        self.palette.scheme.clear()
        self._assert_rejected(source)

    def test_reject_wrong_namespaces_unknown_math_and_bad_modifiers(self) -> None:
        for invalid in ('color-namespace', 'alpha-namespace', 'unknown-math', 'bad-alpha', 'unknown-modifier'):
            with self.subTest(invalid=invalid):
                source = self._source()
                zone = self._zone(source)
                color = zone.find('.//a:srgbClr', NS)
                if invalid == 'color-namespace':
                    color.tag = '{urn:wrong}srgbClr'
                elif invalid == 'alpha-namespace':
                    ET.SubElement(color, '{urn:wrong}alphaMod', {'val': '50000'})
                elif invalid == 'unknown-math':
                    ET.SubElement(zone[0], f'{{{NS["m"]}}}unknown')
                elif invalid == 'bad-alpha':
                    ET.SubElement(color, f'{{{NS["a"]}}}alphaMod', {'val': 'no'})
                else:
                    ET.SubElement(color, f'{{{NS["a"]}}}unknown', {'val': '50000'})
                self._assert_rejected(source)

    def test_reject_mixed_run_or_control_alpha(self) -> None:
        for target in ('.//m:r/a:rPr/a:solidFill/*', './/m:ctrlPr/a:rPr/a:solidFill/*'):
            with self.subTest(target=target):
                source = self._source(style='opacity="0.5"')
                color = self._zone(source).find(target, NS)
                color[0].set('val', '25000')
                self._assert_rejected(source)

    def test_reject_block_alpha_that_metadata_cannot_reexport(self) -> None:
        source = self._source(display=True)
        for color in self._zone(source).iter(f'{{{NS["a"]}}}srgbClr'):
            ET.SubElement(color, f'{{{NS["a"]}}}alphaMod', {'val': '50000'})
        self._assert_rejected(source, display=True)

    def test_normalization_does_not_mutate_source_or_relax_compiler(self) -> None:
        for options in ({'themed': True}, {'style': 'opacity="0.5"'}):
            with self.subTest(options=options):
                zone = self._zone(self._source(**options))
                before = ET.tostring(zone)
                import_formula(zone, display=False, palette=self.palette)
                self.assertEqual(ET.tostring(zone), before)
                with self.assertRaises(FormulaCompileError):
                    validate_omml_fragment(ET.tostring(zone[0], encoding='unicode'))
