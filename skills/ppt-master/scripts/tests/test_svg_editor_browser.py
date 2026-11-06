#!/usr/bin/env python3
"""Exercise editor JavaScript handlers with a small Node VM DOM adapter.

Run with: python3 -m unittest tests.test_svg_editor_browser
Dependencies: Python standard library, Node.js for executing the shipped JavaScript.
Real DOM rendering and caret behavior require a separate browser smoke test.
"""

import json
import subprocess
import unittest
from pathlib import Path


APP = Path(__file__).resolve().parents[1] / 'svg_editor' / 'static' / 'app.js'


class EditorKeyboardTests(unittest.TestCase):
    def _key(self, focus, key, *, selected=True, ctrl=False, meta=False, shift=False):
        program = r'''
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(input.app, 'utf8');
const start = source.indexOf('    function initKeyboardShortcuts()');
const end = source.indexOf('    function initSlideNav()', start);
const actions = [];
const annotation = {tagName: 'TEXTAREA'};
const focus = input.focus === 'annotation' ? annotation : {
    tagName: input.focus, isContentEditable: input.focus === 'editable'
};
let handler;
const context = {
    document: {activeElement: focus, addEventListener: (name, fn) => {handler = fn;}},
    annotationText: annotation,
    selectedElementIds: new Set(input.selected ? ['heading'] : []),
    svgContent: {querySelector: () => ({querySelectorAll: () => [{
        id: 'other', classList: {add: () => actions.push('select')}
    }]})},
    runUndo: () => actions.push('undo'),
    updateSelectionPanel: () => actions.push('panel'),
    overlapPickerEl: null,
    closeOverlapPicker: () => actions.push('close'),
    clearSelection: () => actions.push('clear'),
    nudgeSelection: (x, y) => actions.push(['nudge', x, y]),
    slideNames: ['01.svg', '02.svg'],
    currentSlideIndex: () => 1,
    gotoSlideIndex: i => actions.push(['navigate', i])
};
vm.createContext(context);
vm.runInContext(source.slice(start, end) + '\ninitKeyboardShortcuts();', context);
let prevented = false;
handler({key: input.key, ctrlKey: input.ctrl, metaKey: input.meta,
    shiftKey: input.shift, target: focus, preventDefault: () => {prevented = true;}});
process.stdout.write(JSON.stringify({prevented, actions}));
'''
        result = subprocess.run(
            ['node', '-e', program],
            input=json.dumps(dict(app=str(APP), focus=focus, key=key, selected=selected,
                                  ctrl=ctrl, meta=meta, shift=shift)),
            text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def test_editable_controls_keep_native_keyboard_behavior(self) -> None:
        for focus in ('TEXTAREA', 'INPUT', 'SELECT', 'editable', 'annotation'):
            for key, ctrl in (('ArrowLeft', False), ('Home', False), ('Escape', False),
                              ('a', True), ('z', True)):
                with self.subTest(focus=focus, key=key):
                    self.assertEqual(self._key(focus, key, ctrl=ctrl),
                                     {'prevented': False, 'actions': []})

    def test_editable_controls_do_not_navigate_without_selection(self) -> None:
        self.assertEqual(self._key('TEXTAREA', 'ArrowRight', selected=False),
                         {'prevented': False, 'actions': []})

    def test_canvas_shortcuts_still_work(self) -> None:
        self.assertEqual(self._key('BODY', 'ArrowLeft'),
                         {'prevented': True, 'actions': [['nudge', -1, 0]]})
        self.assertEqual(self._key('BODY', 'ArrowDown', shift=True),
                         {'prevented': True, 'actions': [['nudge', 0, 10]]})
        self.assertEqual(self._key('BODY', 'a', meta=True),
                         {'prevented': True, 'actions': ['select', 'panel']})
        self.assertEqual(self._key('BODY', 'z', ctrl=True),
                         {'prevented': True, 'actions': ['undo']})
        self.assertEqual(self._key('BODY', 'ArrowLeft', selected=False),
                         {'prevented': True, 'actions': [['navigate', 0]]})


class EditorSanitizerTests(unittest.TestCase):
    def _sanitize(self, tag, value, attr_name='href'):
        program = r'''
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const source = fs.readFileSync(input.app, 'utf8');
const start = source.indexOf('    var SVG_NS =');
const end = source.indexOf('    function showError(', start);
const ns = 'http://www.w3.org/2000/svg';
const attr = {name: input.attr, localName: input.attr.split(':').pop(), value: input.value};
const node = {localName: input.tag, namespaceURI: ns, attributes: [attr],
    removeAttributeNode: a => {node.attributes = node.attributes.filter(x => x !== a);},
    remove: () => {node.removed = true;}};
const root = {localName: 'svg', namespaceURI: ns};
const doc = {documentElement: root, getElementsByTagName: () => [], querySelectorAll: () => [node]};
const context = {
    DOMParser: function () {this.parseFromString = () => doc;},
    XMLSerializer: function () {this.serializeToString = () => JSON.stringify(node);},
    t: key => key
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
process.stdout.write(context.sanitizeSvg('<svg/>'));
'''
        result = subprocess.run(
            ['node', '-e', program],
            input=json.dumps(dict(app=str(APP), tag=tag, value=value, attr=attr_name)),
            text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)['attributes']

    def test_raster_data_uri_survives_for_image_elements(self) -> None:
        for tag in ('image', 'feImage'):
            for attr in ('href', 'xlink:href'):
                with self.subTest(tag=tag, attr=attr):
                    uri = 'data:image/png;base64,iVBORw0KGgo='
                    self.assertEqual(self._sanitize(tag, uri, attr)[0]['value'], uri)

    def test_local_image_control_survives(self) -> None:
        uri = '../images/control.png'
        self.assertEqual(self._sanitize('image', uri)[0]['value'], uri)

    def test_active_or_malformed_data_uris_stay_blocked(self) -> None:
        for uri in ('data:text/html;base64,PHNjcmlwdD4=',
                    'data:image/svg+xml;base64,PHN2Zz4=',
                    'data:image/png,<script/>',
                    'data:image/png;base64,AAAA<script/>',
                    'java\tscript:alert(1)', 'VBScript:msgbox(1)'):
            for attr in ('href', 'xlink:href'):
                with self.subTest(uri=uri, attr=attr):
                    self.assertEqual(self._sanitize('image', uri, attr), [])

    def test_data_uri_is_not_allowed_on_links_or_use(self) -> None:
        for tag in ('a', 'use'):
            with self.subTest(tag=tag):
                self.assertEqual(self._sanitize(tag, 'data:image/png;base64,iVBORw0KGgo='), [])

    def test_event_attributes_stay_blocked(self) -> None:
        self.assertEqual(self._sanitize('image', 'alert(1)', 'ONERROR'), [])
