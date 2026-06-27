#!/usr/bin/env python3
"""
PPT Master - SVG Editor Server

Flask backend for the SVG annotation editor.
Serves the web UI and provides API endpoints for reading/writing SVG annotations.

Usage:
    python3 scripts/svg_editor/server.py <project_dir>

Examples:
    python3 scripts/svg_editor/server.py projects/my-project
    python3 scripts/svg_editor/server.py projects/my-project --port 8080
    python3 scripts/svg_editor/server.py projects/my-project --live

Dependencies:
    flask>=3.0.0
"""

import argparse
import atexit
import html
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

logger = logging.getLogger('svg_editor')

# Per-project runtime files live under <project_path>/live_preview/.
LIVE_PREVIEW_DIR_NAME = 'live_preview'
LOCK_FILE_NAME = 'lock.json'
LEGACY_LOCK_FILE_NAME = '.live_preview.lock'

# Local — sys.path injection for sibling module (code-style.md §3)
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_FINALIZE_DIR = _SCRIPTS_DIR.parent / 'svg_finalize'
if str(_FINALIZE_DIR) not in sys.path:
    sys.path.insert(0, str(_FINALIZE_DIR))

# scripts/ root for cross-server shared helpers
_ROOT_SCRIPTS_DIR = _SCRIPTS_DIR.parent
if str(_ROOT_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from server_common import (  # noqa: E402
    claim_lock as _claim_lock,
    find_free_port as _find_free_port,
    process_alive as _process_alive,
    read_lock as _read_lock,
    release_lock as _release_lock,
)

configure_utf8_stdio()

from annotations import (  # noqa: E402
    assign_temp_ids,
    is_editable_attr,
    parse_annotations,
    promote_tspan_to_text,
    set_annotation,
    set_attributes,
    set_text,
    strip_unused_temp_ids,
)
from embed_icons import (  # noqa: E402
    parse_use_element,
    resolve_icon_path,
    extract_paths_from_icon,
    generate_icon_group,
)

_ICONS_DIR = _SCRIPTS_DIR.parent.parent / 'templates' / 'icons'
_USE_ICON_PATTERN = re.compile(r'<use\s+[^>]*data-icon="[^"]*"[^>]*/>')

# Per-path mtime caches: key = absolute path str, value = (mtime, payload).
# Entry is evicted/replaced when the file's mtime changes, so stale data
# cannot leak. Locks guard concurrent access under Flask's threaded server.
_SLIDE_CACHE_LOCK = threading.Lock()
_SLIDE_CACHE: dict = {}  # path -> (mtime, (content, warnings))

_LIST_CACHE_LOCK = threading.Lock()
_LIST_CACHE: dict = {}  # path -> (mtime, annotation_count_on_disk)


def _xml_attr(value: object) -> str:
    """Escape a value for safe insertion into generated preview SVG markup."""
    return html.escape(str(value), quote=True)


def _cache_get(cache: dict, lock: threading.Lock, path: str, mtime: float):
    with lock:
        entry = cache.get(path)
        if entry is None or entry[0] != mtime:
            return None
        return entry[1]


def _cache_put(cache: dict, lock: threading.Lock, path: str, mtime: float, value) -> None:
    with lock:
        cache[path] = (mtime, value)


# Lock / liveness helpers are shared with confirm_ui via server_common
# (imported above as _process_alive / _read_lock / _claim_lock / _release_lock).


def _inline_icons(content: str) -> tuple[str, list[dict]]:
    """Replace <use data-icon="..."/> with rendered <g> for browser preview.

    Returns (rewritten_content, warnings). Each warning is
    ``{"icon": <name>, "reason": <str>}`` so the frontend can surface
    "icon X not found" to the user instead of silently dropping it.
    """
    warnings: list[dict] = []
    matches = list(_USE_ICON_PATTERN.finditer(content))
    if not matches:
        return content, warnings
    new_content = content
    for match in reversed(matches):
        use_str = match.group(0)
        icon_name: str = ''
        try:
            attrs = parse_use_element(use_str)
            icon_name = str(attrs.get('icon') or '')
            if not icon_name:
                warnings.append({'icon': '', 'reason': 'missing data-icon attribute'})
                continue
            icon_path, _ = resolve_icon_path(icon_name, _ICONS_DIR)
            color = str(attrs.get('fill', '#000000'))
            elements, style, base_size = extract_paths_from_icon(icon_path, color)
        except Exception as exc:
            warnings.append({'icon': icon_name, 'reason': f'{type(exc).__name__}: {exc}'})
            logger.warning('icon inline failed: name=%r reason=%s', icon_name, exc)
            continue
        if not elements:
            warnings.append({'icon': icon_name, 'reason': 'no renderable paths in icon'})
            continue
        replacement = generate_icon_group(attrs, elements, style, base_size)
        id_match = re.search(r'\bid="([^"]+)"', use_str)
        if id_match:
            preview_attrs = [
                f'id="{_xml_attr(id_match.group(1))}"',
                f'data-icon="{_xml_attr(icon_name)}"',
            ]
            for key in ('x', 'y', 'width', 'height'):
                if key in attrs:
                    preview_attrs.append(f'data-use-{key}="{_xml_attr(attrs[key])}"')
            if 'transform' in attrs:
                preview_attrs.append('data-use-has-transform="1"')
            replacement = replacement.replace(
                '<g ', f'<g {" ".join(preview_attrs)} ', 1,
            )
        new_content = new_content[:match.start()] + replacement + new_content[match.end():]
    return new_content, warnings


# ---------------------------------------------------------------------------
# Staged-edit value validation (POST /api/slide/<name>/edit).
# The browser may expose raw element attributes, so validation protects only
# invariants and dangerous value forms rather than a tiny style whitelist.
# ---------------------------------------------------------------------------

# Reject CSS-injection vectors in color-like values; mirrors frontend checks.
_UNSAFE_COLOR_RE = re.compile(r'[;:@\\]|url\s*\(', re.IGNORECASE)
# Generic SVG attribute names: namespaces, hyphenated attrs, and data-* attrs.
_SAFE_ATTR_NAME_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.:-]*$')
_MAX_ATTR_VALUE_LEN = 256
_MAX_EDIT_TEXT_LEN = 5000
_ADDABLE_BATCH_ATTRS = frozenset({
    'fill', 'stroke', 'opacity',
    'font-size', 'font-family', 'font-weight', 'text-anchor',
    'x', 'y',
})


def _is_safe_color(value: str) -> bool:
    return len(value) < _MAX_ATTR_VALUE_LEN and not _UNSAFE_COLOR_RE.search(value)


def _validate_edit_attrs(attrs: dict, existing_attrs: set[str]) -> Optional[str]:
    """Return an error string if any attr/value is disallowed, else None."""
    for key, value in attrs.items():
        if not isinstance(key, str) or not _SAFE_ATTR_NAME_RE.match(key):
            return f'invalid attribute name: {key}'
        if not is_editable_attr(key):
            return f'attribute not editable: {key}'
        if key not in existing_attrs and key != 'transform' and key not in _ADDABLE_BATCH_ATTRS:
            return f'attribute does not exist on element: {key}'
        if value is None:
            if key not in existing_attrs:
                return f'attribute does not exist on element: {key}'
            continue
        if not isinstance(value, str):
            return f'value must be a string: {key}'
        if len(value) > _MAX_ATTR_VALUE_LEN:
            return f'value too long: {key}'
        if key in ('fill', 'stroke', 'color', 'stop-color', 'flood-color', 'lighting-color'):
            if not _is_safe_color(value):
                return f'unsafe color value: {key}'
        if key == 'transform' and re.search(r'nan|inf', value, re.IGNORECASE):
            return f'invalid transform value: {key}'
        if any(c in value for c in '<>"'):
            return f'invalid value: {key}'
        if re.search(r'javascript\s*:|data\s*:|url\s*\(', value, re.IGNORECASE):
            return f'unsafe value: {key}'
    return None


EDIT_LOG_NAME = 'edits.jsonl'
ANNOTATION_LOG_NAME = 'annotations.jsonl'


def _append_live_preview_log(project_path: Path, filename: str, record: dict) -> None:
    """Append one live-preview history record under ``live_preview/``."""
    try:
        log_dir = _runtime_dir(project_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / filename, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + '\n')
    except OSError as exc:
        logger.warning('live preview log append failed: %s', exc)


def _append_edit_log(project_path: Path, record: dict) -> None:
    """Append one applied direct-edit record to the preview history."""
    _append_live_preview_log(project_path, EDIT_LOG_NAME, record)


def _append_annotation_log(project_path: Path, record: dict) -> None:
    """Append one annotation lifecycle record to the preview history."""
    _append_live_preview_log(project_path, ANNOTATION_LOG_NAME, record)


def _find_by_id(root: ET.Element, element_id: str) -> Optional[ET.Element]:
    for elem in root.iter():
        if elem.get('id') == element_id:
            return elem
    return None


def _apply_edit_record(root: ET.Element, record: dict) -> tuple[bool, Optional[str]]:
    element_id = record.get('element_id')
    if not isinstance(element_id, str):
        return False, 'invalid-record'
    promote = record.get('promote_tspan')
    if promote:
        if not isinstance(promote, dict):
            return False, 'invalid-promote'
        ok, reason = promote_tspan_to_text(
            root,
            element_id,
            str(promote.get('x') or ''),
            str(promote.get('y') or ''),
        )
        if not ok:
            return ok, reason
    if 'text' in record:
        ok, reason = set_text(root, element_id, str(record.get('text') or ''))
        if not ok:
            return ok, reason
    attrs = record.get('attrs')
    if attrs:
        ok, reason = set_attributes(root, element_id, attrs)
        if not ok:
            return ok, reason
    return True, None


def _apply_edit_records(root: ET.Element, records: list[dict]) -> tuple[bool, Optional[str]]:
    for record in records:
        ok, reason = _apply_edit_record(root, record)
        if not ok:
            return ok, reason
    return True, None


def _edit_signature(record: dict) -> tuple:
    """Identity used to coalesce consecutive staged edits.

    Two edits fold together only when they touch the exact same element and the
    exact same field set (text flag + sorted attr keys). 'Nudge fill 5×'
    collapses to one undo step; 'change fill then font-size' stays two.
    """
    attr_keys = tuple(sorted((record.get('attrs') or {}).keys()))
    promote_keys = tuple(sorted((record.get('promote_tspan') or {}).keys()))
    return (record.get('element_id'), 'text' in record, attr_keys, promote_keys)


def _coalesce_into(prev: dict, cur: dict) -> None:
    """Fold cur's new values into prev, keeping prev's original old values.

    Callers guarantee matching signatures, so prev and cur carry the same
    (kind, key) change set; only the 'new' side advances. prev's 'old' is the
    value from before the first edit in the run, which is what undo and the
    edit log should report.
    """
    if 'text' in cur:
        prev['text'] = cur['text']
    if cur.get('attrs'):
        merged = dict(prev.get('attrs') or {})
        merged.update(cur['attrs'])
        prev['attrs'] = merged
    if cur.get('promote_tspan'):
        prev['promote_tspan'] = cur['promote_tspan']
    old_by_field = {(c['kind'], c['key']): c['old'] for c in prev['changes']}
    prev['changes'] = [
        {
            'kind': c['kind'], 'key': c['key'],
            'old': old_by_field.get((c['kind'], c['key']), c['old']),
            'new': c['new'],
        }
        for c in cur['changes']
    ]


def create_app(
    project_dir: str,
    idle_timeout: int = 900,
    live: bool = False,
    lock_file: Optional[Path] = None,
) -> Flask:
    """Create and configure the Flask app for a given project directory."""
    project_path = Path(project_dir).resolve()
    svg_dir = project_path / 'svg_output'
    images_dir = project_path / 'images'
    assets_dir = project_path / 'assets'

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PROJECT_PATH'] = project_path
    app.config['SVG_DIR'] = svg_dir
    app.config['LIVE_MODE'] = live
    app.config['LOCK_FILE'] = lock_file

    # In-memory annotation store: {filename: {element_id: annotation_text}}
    app.config['ANNOTATIONS'] = {}

    # Per-file staged direct edits. They affect the browser preview immediately,
    # but are written to svg_output/ only by /api/save-all.
    app.config['PENDING_EDITS'] = {}

    # Idle timeout: auto-shutdown if no one connects within idle_timeout seconds
    app.config['LAST_REQUEST_TIME'] = time.time()

    @app.before_request
    def _update_activity():
        app.config['LAST_REQUEST_TIME'] = time.time()

    def _exit_with_lock_release(code: int = 0) -> None:
        lf = app.config.get('LOCK_FILE')
        if lf is not None:
            _release_lock(lf)
        # os._exit: atexit handlers do not run; we just released the lock
        # manually above so a clean restart still finds the slot free.
        os._exit(code)

    def _idle_watchdog():
        if idle_timeout <= 0:
            return
        while True:
            time.sleep(10)
            elapsed = time.time() - app.config['LAST_REQUEST_TIME']
            if elapsed > idle_timeout:
                logger.info('idle for %ds, shutting down', idle_timeout)
                # Flask dev server has no clean shutdown; data is safe
                # because idle timeout only fires when no requests are in flight.
                _exit_with_lock_release(0)

    watchdog = threading.Thread(target=_idle_watchdog, daemon=True)
    watchdog.start()

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        data = request.get_json(silent=True) or {}
        reason = data.get('reason') or 'shutdown'

        def _stop():
            time.sleep(0.5)  # Let HTTP response flush before killing the process
            logger.info('shutting down (%s)', reason)
            # os._exit: save-all already wrote to disk; 0.5s delay ensures response is sent.
            _exit_with_lock_release(0)
        threading.Thread(target=_stop, daemon=True).start()
        return jsonify({'status': 'ok'})

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/config')
    def get_config():
        return jsonify({
            'live': app.config['LIVE_MODE'],
        })

    @app.route('/images/<path:filename>')
    def serve_image(filename: str):
        """Serve images referenced by SVGs as `../images/*.png`.

        Resolution against an absolute images_dir + relative_to() check is the
        authoritative path-traversal guard.
        """
        if not images_dir.exists():
            return jsonify({'error': 'images directory not found'}), 404
        target = (images_dir / filename).resolve()
        try:
            target.relative_to(images_dir.resolve())
        except ValueError:
            return jsonify({'error': 'invalid path'}), 400
        if not target.exists() or not target.is_file():
            return jsonify({'error': 'not found'}), 404
        return send_from_directory(str(images_dir), filename)

    @app.route('/assets/<path:filename>')
    def serve_asset(filename: str):
        """Serve media extracted by pptx_to_svg.py as `../assets/*`."""
        if not assets_dir.exists():
            return jsonify({'error': 'assets directory not found'}), 404
        target = (assets_dir / filename).resolve()
        try:
            target.relative_to(assets_dir.resolve())
        except ValueError:
            return jsonify({'error': 'invalid path'}), 400
        if not target.exists() or not target.is_file():
            return jsonify({'error': 'not found'}), 404
        return send_from_directory(str(assets_dir), filename)

    @app.route('/<path:filename>')
    def serve_bare_asset(filename: str):
        """Resolve a template SVG's bare image href (e.g. `href="cover_bg.png"`).

        Mirror templates copy hrefs verbatim, so a bare filename reaches the
        browser as `/<filename>` (no `../images/` prefix). Resolve it against the
        project's images/ then assets/. Every real route (`/api/*`, `/images/*`,
        `/assets/*`, `/static/*`, `/`) is more specific and matches first; this
        only catches the leftover bare references and 404s otherwise.
        """
        for base in (images_dir, assets_dir):
            if not base.exists():
                continue
            target = (base / filename).resolve()
            try:
                target.relative_to(base.resolve())
            except ValueError:
                continue
            if target.exists() and target.is_file():
                return send_from_directory(str(base), filename)
        return jsonify({'error': 'not found'}), 404

    @app.route('/api/slides')
    def get_slides():
        svg_dir = app.config['SVG_DIR']
        if not svg_dir.exists():
            return jsonify({'slides': []})

        annotations = app.config['ANNOTATIONS']
        slides = []
        for svg_file in sorted(svg_dir.glob('*.svg')):
            path_str = str(svg_file)
            try:
                mtime = svg_file.stat().st_mtime
            except OSError as exc:
                logger.warning('stat failed: %s: %s', path_str, exc)
                continue

            ok = True
            error_msg: Optional[str] = None
            disk_count = _cache_get(_LIST_CACHE, _LIST_CACHE_LOCK, path_str, mtime)
            if disk_count is None:
                try:
                    tree = ET.parse(path_str)
                    disk_count = len(parse_annotations(tree.getroot()))
                except ET.ParseError as exc:
                    ok = False
                    error_msg = f'XML parse error: {exc}'
                    disk_count = 0
                    logger.warning('slide parse failed: %s: %s', svg_file.name, exc)
                _cache_put(_LIST_CACHE, _LIST_CACHE_LOCK, path_str, mtime, disk_count)

            mem_count = len(annotations.get(svg_file.name, {}))
            annotation_count = max(disk_count, mem_count)

            slides.append({
                'name': svg_file.name,
                'annotated': annotation_count > 0,
                'annotation_count': annotation_count,
                'ok': ok,
                'error': error_msg,
                'mtime': mtime,
            })

        return jsonify({'slides': slides})

    def _safe_svg_path(name: str):
        """Validate slide name and return safe path. Returns None if invalid.

        The early string checks reject obvious bad inputs; the resolve()+startswith()
        check is the authoritative path traversal guard.
        """
        if '/' in name or '\\' in name or '..' in name:
            return None
        svg_file = (svg_dir / name).resolve()
        if not str(svg_file).startswith(str(svg_dir.resolve())):
            return None
        return svg_file

    @app.route('/api/slide/<name>')
    def get_slide(name: str):
        svg_file = _safe_svg_path(name)
        if svg_file is None:
            return jsonify({'error': 'Invalid slide name'}), 400
        if not svg_file.exists():
            return jsonify({'error': 'Slide not found'}), 404

        path_str = str(svg_file)
        try:
            mtime = svg_file.stat().st_mtime
        except OSError as exc:
            logger.warning('stat failed: %s: %s', path_str, exc)
            return jsonify({'error': f'Failed to stat SVG: {exc}'}), 500

        pending_edits = app.config['PENDING_EDITS'].get(name) or []
        cached = None if pending_edits else _cache_get(
            _SLIDE_CACHE, _SLIDE_CACHE_LOCK, path_str, mtime,
        )
        if cached is not None:
            content, warnings, disk_annotations, id_to_tag = cached
        else:
            try:
                tree = ET.parse(path_str)
                root = tree.getroot()
            except ET.ParseError as exc:
                logger.warning('slide parse failed: %s: %s', name, exc)
                return jsonify({'error': f'Failed to parse SVG: {exc}'}), 500

            assign_temp_ids(root)
            if pending_edits:
                ok, reason = _apply_edit_records(root, pending_edits)
                if not ok:
                    return jsonify({'error': f'Failed to apply pending edits: {reason}'}), 500
            disk_annotations = parse_annotations(root)
            id_to_tag: dict[str, str] = {}
            for elem in root.iter():
                eid = elem.get('id')
                if eid:
                    tag = elem.tag
                    if '}' in tag:
                        tag = tag.split('}', 1)[1]
                    id_to_tag[eid] = tag
            content = ET.tostring(root, encoding='unicode', xml_declaration=False)
            content, warnings = _inline_icons(content)
            if not pending_edits:
                _cache_put(
                    _SLIDE_CACHE, _SLIDE_CACHE_LOCK, path_str, mtime,
                    (content, warnings, disk_annotations, id_to_tag),
                )

        mem_annotations = app.config['ANNOTATIONS'].get(name, {})
        merged: dict[str, str] = {}
        for ann in disk_annotations:
            merged[ann['element_id']] = ann['annotation']
        merged.update(mem_annotations)

        annotations_list = [
            {
                'element_id': eid,
                'tag': id_to_tag.get(eid, ''),
                'annotation': ann_text,
            }
            for eid, ann_text in merged.items()
        ]

        return jsonify({
            'name': name,
            'content': content,
            'annotations': annotations_list,
            'warnings': warnings,
            'mtime': mtime,
            'undo_depth': len(pending_edits),
        })

    @app.route('/api/slide/<name>/annotate', methods=['POST'])
    def post_annotate(name: str):
        data = request.get_json()
        if not data or 'element_id' not in data or 'annotation' not in data:
            return jsonify({'error': 'Missing element_id or annotation'}), 400

        element_id = data['element_id']
        annotation = data['annotation']

        if not isinstance(element_id, str) or not isinstance(annotation, str):
            return jsonify({'error': 'element_id and annotation must be strings'}), 400

        if len(element_id) > 200:
            return jsonify({'error': 'element_id too long (max 200 chars)'}), 400

        if len(annotation) > 10000:
            return jsonify({'error': 'Annotation too long (max 10000 chars)'}), 400

        if name not in app.config['ANNOTATIONS']:
            app.config['ANNOTATIONS'][name] = {}

        app.config['ANNOTATIONS'][name][element_id] = annotation

        return jsonify({
            'status': 'ok',
            'annotations_count': len(app.config['ANNOTATIONS'][name]),
        })

    @app.route('/api/slide/<name>/annotate/<element_id>', methods=['DELETE'])
    def delete_annotate(name: str, element_id: str):
        annotations = app.config['ANNOTATIONS']
        # Ensure the file key exists so save-all knows to rewrite this file
        # even if no new annotations were added (pure delete path).
        if name not in annotations:
            annotations[name] = {}
        if element_id in annotations[name]:
            del annotations[name][element_id]

        return jsonify({
            'status': 'ok',
            'annotations_count': len(annotations.get(name, {})),
        })

    @app.route('/api/slide/<name>/edit', methods=['POST'])
    def post_edit(name: str):
        """Stage a direct (AI-free) edit to one element.

        Body: ``{element_id, text?: str, attrs?: {fill, font-size, ...}}``.
        The edit is visible in preview, but disk writes happen only in
        /api/save-all alongside annotation persistence.
        """
        svg_file = _safe_svg_path(name)
        if svg_file is None:
            return jsonify({'error': 'Invalid slide name'}), 400
        if not svg_file.exists():
            return jsonify({'error': 'Slide not found'}), 404

        data = request.get_json(silent=True) or {}
        element_id = data.get('element_id')
        if not isinstance(element_id, str) or not element_id or len(element_id) > 200:
            return jsonify({'error': 'Missing or invalid element_id'}), 400

        new_text = data.get('text')
        attrs = data.get('attrs')
        promote = data.get('promote_tspan')
        if new_text is None and not attrs and not promote:
            return jsonify({'error': 'Nothing to edit (no text or attrs)'}), 400

        if new_text is not None:
            if not isinstance(new_text, str) or len(new_text) > _MAX_EDIT_TEXT_LEN:
                return jsonify({'error': 'Invalid or too-long text'}), 400
        if attrs is not None:
            if not isinstance(attrs, dict):
                return jsonify({'error': 'attrs must be an object'}), 400
        if promote is not None:
            if not isinstance(promote, dict):
                return jsonify({'error': 'promote_tspan must be an object'}), 400
            for key in ('x', 'y'):
                value = promote.get(key)
                if not isinstance(value, str) or not re.fullmatch(r'-?\d+(?:\.\d+)?', value):
                    return jsonify({'error': f'invalid promote_tspan.{key}'}), 400

        try:
            tree = ET.parse(str(svg_file))
            root = tree.getroot()
        except ET.ParseError as exc:
            return jsonify({'error': f'Failed to parse SVG: {exc}'}), 500

        assign_temp_ids(root)
        pending = app.config['PENDING_EDITS'].get(name) or []
        ok, reason = _apply_edit_records(root, pending)
        if not ok:
            return jsonify({'error': f'Failed to replay pending edits: {reason}'}), 500

        # Locate the target up front to capture old values before mutating —
        # these feed the staged record and eventual edit log.
        target = _find_by_id(root, element_id)
        if target is None:
            return jsonify({'error': 'Element not found'}), 404
        if attrs is not None:
            attr_err = _validate_edit_attrs(attrs, set(target.attrib.keys()))
            if attr_err:
                return jsonify({'error': attr_err}), 400

        changes = []
        staged: dict = {'element_id': element_id}
        if new_text is not None:
            old_text = target.text or ''
            ok, reason = set_text(root, element_id, new_text)
            if not ok:
                return jsonify({'error': f'Text edit failed: {reason}'}), (
                    404 if reason == 'not-found' else 400
                )
            changes.append({'kind': 'text', 'key': None, 'old': old_text, 'new': new_text})
            staged['text'] = new_text
        if attrs:
            old_attrs = {k: target.get(k) for k in attrs}
            ok, reason = set_attributes(root, element_id, attrs)
            if not ok:
                return jsonify({'error': f'Attribute edit failed: {reason}'}), (
                    404 if reason == 'not-found' else 400
                )
            for k, v in attrs.items():
                changes.append({'kind': 'attr', 'key': k, 'old': old_attrs[k], 'new': v})
            staged['attrs'] = attrs
        if promote:
            tag = target.tag.split('}', 1)[1] if '}' in target.tag else target.tag
            old_state = {
                'tag': tag,
                'x': target.get('x'),
                'y': target.get('y'),
                'dy': target.get('dy'),
                'transform': target.get('transform'),
            }
            ok, reason = promote_tspan_to_text(root, element_id, promote['x'], promote['y'])
            if not ok:
                return jsonify({'error': f'Tspan promotion failed: {reason}'}), (
                    404 if reason == 'not-found' else 400
                )
            changes.append({
                'kind': 'structure',
                'key': 'promote-tspan',
                'old': old_state,
                'new': {'tag': 'text', 'x': promote['x'], 'y': promote['y']},
            })
            staged['promote_tspan'] = promote

        staged['changes'] = changes
        pending = app.config['PENDING_EDITS'].setdefault(name, [])
        # Coalesce a run of edits to the same element+fields into one undo step
        # so repeated nudges/color tries don't pile up replay work or log noise.
        if pending and _edit_signature(pending[-1]) == _edit_signature(staged):
            _coalesce_into(pending[-1], staged)
        else:
            pending.append(staged)
        return jsonify({'status': 'ok', 'undo_depth': len(pending)})

    @app.route('/api/slide/<name>/undo', methods=['POST'])
    def post_undo(name: str):
        """Drop the most recent staged direct edit on this slide (LIFO)."""
        svg_file = _safe_svg_path(name)
        if svg_file is None:
            return jsonify({'error': 'Invalid slide name'}), 400
        if not svg_file.exists():
            return jsonify({'error': 'Slide not found'}), 404

        stack = app.config['PENDING_EDITS'].get(name) or []
        if not stack:
            return jsonify({'status': 'empty', 'undo_depth': 0})
        stack.pop()
        return jsonify({'status': 'ok', 'undo_depth': len(stack)})

    @app.route('/api/save-all', methods=['POST'])
    def save_all():
        annotations = app.config['ANNOTATIONS']
        pending_edits = app.config['PENDING_EDITS']
        modified = []

        filenames = sorted(set(annotations.keys()) | set(pending_edits.keys()))
        for filename in filenames:
            anns = annotations.get(filename, {})
            edits = pending_edits.get(filename, [])
            # anns may be empty when the user deleted all annotations — still
            # need to write so the on-disk data-edit-* attributes are cleared.

            svg_file = _safe_svg_path(filename)
            if svg_file is None or not svg_file.exists():
                continue

            try:
                tree = ET.parse(str(svg_file))
                root = tree.getroot()
            except ET.ParseError:
                continue

            assign_temp_ids(root)

            ok, reason = _apply_edit_records(root, edits)
            if not ok:
                return jsonify({'error': f'Failed to apply edits in {filename}: {reason}'}), 400

            old_annotations = {
                item['element_id']: item['annotation']
                for item in parse_annotations(root)
            }

            # Clear all existing annotations from the file before writing current state
            for elem in root.iter():
                elem.attrib.pop('data-edit-target', None)
                elem.attrib.pop('data-edit-annotation', None)

            for element_id, annotation_text in anns.items():
                set_annotation(root, element_id, annotation_text)

            # Strip transient _edit_N ids from elements that are NOT user-annotated.
            # Only annotated elements need to keep their id so the AI can locate them
            # via check_annotations.py; the rest are pollution.
            annotated_ids = set(anns.keys())
            strip_unused_temp_ids(root, annotated_ids)

            tree.write(str(svg_file), encoding='UTF-8', xml_declaration=True)
            ts = time.time()
            for element_id, annotation_text in anns.items():
                old_text = old_annotations.get(element_id)
                action = 'annotation_saved' if old_text is None else 'annotation_updated'
                if old_text == annotation_text:
                    action = 'annotation_saved'
                _append_annotation_log(project_path, {
                    'ts': ts, 'file': filename, 'element_id': element_id,
                    'action': action, 'old': old_text, 'new': annotation_text,
                })
            for element_id, old_text in old_annotations.items():
                if element_id not in anns:
                    _append_annotation_log(project_path, {
                        'ts': ts, 'file': filename, 'element_id': element_id,
                        'action': 'annotation_removed', 'old': old_text, 'new': None,
                    })
            for edit in edits:
                for chg in edit.get('changes', []):
                    _append_edit_log(project_path, {
                        'ts': ts, 'file': filename, 'element_id': edit.get('element_id'),
                        'action': 'edit', 'kind': chg.get('kind'), 'key': chg.get('key'),
                        'old': chg.get('old'), 'new': chg.get('new'),
                    })
            modified.append(filename)

        app.config['ANNOTATIONS'] = {}
        app.config['PENDING_EDITS'] = {}

        return jsonify({'status': 'ok', 'files_modified': modified})

    return app


def _runtime_dir(project_path: Path) -> Path:
    return project_path / LIVE_PREVIEW_DIR_NAME


def _lock_file(project_path: Path) -> Path:
    return _runtime_dir(project_path) / LOCK_FILE_NAME


def _legacy_live_lock(project_path: Path) -> Optional[dict]:
    """Return a live legacy root lock, if one exists."""
    legacy_lock = project_path / LEGACY_LOCK_FILE_NAME
    existing = _read_lock(legacy_lock)
    if existing and _process_alive(int(existing.get('pid', 0))):
        return existing
    return None


def _wait_for_ready(url: str, proc: subprocess.Popen, timeout: int = 15) -> bool:
    """Wait until the server responds or the child exits."""
    deadline = time.time() + timeout
    health_url = f'{url}/api/config'
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    return False


def _open_browser(url: str) -> bool:
    """Best-effort browser launch after the local server is reachable."""
    try:
        if os.name == 'nt':
            os.startfile(url)  # type: ignore[attr-defined]
            return True
        return bool(webbrowser.open(url))
    except OSError as exc:
        logger.warning('browser auto-open failed: %s', exc)
    except webbrowser.Error as exc:
        logger.warning('browser auto-open failed: %s', exc)
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='PPT Master SVG Editor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('project_dir', help='Path to project directory (contains svg_output/)')
    parser.add_argument('--port', type=int, default=5050, help='Port to listen on (default: 5050)')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Start the server in the background and return after it is reachable',
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run as Executor live preview: allow empty svg_output/ and keep serving after annotation submit',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='Idle timeout in seconds (default: 900; live mode default: 7200; 0 = disabled)',
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] svg_editor: %(message)s',
        datefmt='%H:%M:%S',
    )

    project_path = Path(args.project_dir).resolve()
    svg_output = project_path / 'svg_output'
    if not svg_output.exists():
        if args.live:
            svg_output.mkdir(parents=True, exist_ok=True)
        else:
            logger.error('%s does not exist', svg_output)
            return 1
    elif not svg_output.is_dir():
        logger.error('%s is not a directory', svg_output)
        return 1

    legacy_existing = _legacy_live_lock(project_path)
    if legacy_existing:
        existing_pid = legacy_existing.get('pid', '?')
        existing_port = legacy_existing.get('port', '?')
        logger.error(
            'live preview is already running for this project via legacy lock '
            '(pid=%s, port=%s). Open http://localhost:%s, click '
            'Exit preview in the browser, or stop pid %s',
            existing_pid, existing_port, existing_port, existing_pid,
        )
        return 1

    runtime_dir = _runtime_dir(project_path)
    lock_file = _lock_file(project_path)

    if args.daemon:
        existing = _read_lock(lock_file)
        if existing and _process_alive(int(existing.get('pid', 0))):
            existing_pid = existing.get('pid', '?')
            existing_port = existing.get('port', '?')
            logger.error(
                'live preview is already running for this project '
                '(pid=%s, port=%s). Open http://localhost:%s',
                existing_pid, existing_port, existing_port,
            )
            return 1

        try:
            runtime_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error('cannot create live preview runtime directory: %s (%s)', runtime_dir, exc)
            return 1
        log_path = runtime_dir / 'server.log'
        port = _find_free_port(args.port)
        idle_timeout = args.timeout
        if idle_timeout is None:
            idle_timeout = 7200 if args.live else 900
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            str(project_path),
            '--port',
            str(port),
            '--timeout',
            str(idle_timeout),
            '--no-browser',
        ]
        if args.live:
            cmd.append('--live')
        creationflags = 0
        popen_kwargs = {}
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            popen_kwargs['start_new_session'] = True
        try:
            with log_path.open('a', encoding='utf-8') as log:
                proc = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    creationflags=creationflags,
                    **popen_kwargs,
                )
        except OSError as exc:
            logger.error('cannot write live preview log: %s (%s)', log_path, exc)
            return 1
        url = f'http://localhost:{port}'
        if not _wait_for_ready(url, proc):
            logger.error('live preview failed to become reachable: %s (log: %s)', url, log_path)
            return 1
        logger.info('started live preview in background: %s (pid=%s)', url, proc.pid)
        logger.info('log: %s', log_path)
        if not args.no_browser and not _open_browser(url):
            logger.info('browser did not auto-open; open %s manually', url)
        return 0

    # Pick a free port: another project's preview/confirm server may already
    # hold the default, so bind the next free one instead of crashing — each
    # project then serves its own data on its own port (no cross-project mix-up).
    port = _find_free_port(args.port)

    # Per-project mutual exclusion. The major driver of orphaned servers is
    # --live mode (which used to disable idle timeout entirely) combined with
    # silent restarts; refusing duplicate launches catches the accumulation
    # at its source. Stale locks (dead pid) are overwritten by _claim_lock.
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.error('cannot create live preview runtime directory: %s (%s)', runtime_dir, exc)
        return 1
    existing = _claim_lock(lock_file, port)
    if existing:
        existing_pid = existing.get('pid', '?')
        existing_port = existing.get('port', '?')
        logger.error(
            'live preview is already running for this project '
            '(pid=%s, port=%s). Open http://localhost:%s, click '
            'Exit preview in the browser, or run: kill %s',
            existing_pid, existing_port, existing_port, existing_pid,
        )
        return 1
    # atexit covers normal interpreter shutdown (Ctrl+C / SystemExit);
    # /api/shutdown and idle timeout call _release_lock directly before
    # os._exit since atexit handlers do not run on os._exit.
    atexit.register(_release_lock, lock_file)

    # SIGTERM would otherwise terminate without running atexit, leaving a
    # stale lock that future launches have to recover from. Translate it
    # into SystemExit so the atexit handler above runs. SIGINT (Ctrl+C) is
    # already handled by werkzeug's reloader-free shutdown path.
    def _on_sigterm(signum: int, _frame) -> None:
        logger.info('received signal %s, exiting', signum)
        sys.exit(0)
    try:
        signal.signal(signal.SIGTERM, _on_sigterm)
    except (ValueError, OSError):
        # ValueError: not in main thread; OSError: unsupported on platform.
        pass

    idle_timeout = args.timeout
    if idle_timeout is None:
        # Long but finite default for --live so a forgotten preview eventually
        # dies. Set --timeout 0 to keep the historical never-expire behavior.
        idle_timeout = 7200 if args.live else 900

    app = create_app(
        str(project_path),
        idle_timeout=idle_timeout,
        live=args.live,
        lock_file=lock_file,
    )

    url = f'http://localhost:{port}'
    if not args.no_browser:
        _open_browser(url)

    mode = "live preview (auto-startup)" if args.live else "live preview"
    svg_count = len(list(svg_output.glob('*.svg')))
    logger.info('running at %s (%s)', url, mode)
    logger.info('project: %s', project_path)
    logger.info('svg_output: %s (%d slides)', svg_output, svg_count)
    logger.info('idle timeout: %ds (0 = disabled)', idle_timeout)
    app.run(host='127.0.0.1', port=port, debug=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
