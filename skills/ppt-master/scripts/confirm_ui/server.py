#!/usr/bin/env python3
"""
PPT Master - Strategist confirmation stage UI Server (Step 4)

Lightweight Flask backend for the interactive, visual Strategist confirmation stage page.
Strategist writes its recommendations to
``<project>/confirm_ui/recommendations.json``; this server renders them as a
clickable page (color swatches, live font previews, candidate picks). On
submit it writes the user's final choices to
``<project>/confirm_ui/result.json`` for the AI to read back.

This is the confirmation surface only. The chat fallback always remains valid:
if the browser cannot open (remote / headless / web host), the AI presents the
same Strategist confirmation stage in chat.

See scripts/docs/confirm_ui.md for the round-trip data contract and schema.

Usage:
    python3 scripts/confirm_ui/server.py <project_dir>

Examples:
    python3 scripts/confirm_ui/server.py projects/my-project
    python3 scripts/confirm_ui/server.py projects/my-project --port 5051
    python3 scripts/confirm_ui/server.py projects/my-project --no-browser
    python3 scripts/confirm_ui/server.py projects/my-project --daemon --wait

Dependencies:
    flask>=3.0.0
"""

import argparse
import atexit
import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

# Local — sys.path injection for sibling module (code-style.md §3)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from analysis_pack import DEFAULT_PROFILE, build_image_manifest, compile_workbook  # noqa: E402
from analysis_library import (  # noqa: E402
    build_library_manifest,
    compile_library,
    load_library,
    resolve_domain_item_ids,
)
from intake_manifest import build_source_manifest  # noqa: E402
from outline_gate import (  # noqa: E402
    CONTENT_INVENTORY_PATH,
    CONFIRMED_NAME as OUTLINE_CONFIRMED_NAME,
    DRAFT_NAME as OUTLINE_DRAFT_NAME,
    analysis_selection_hash,
    check_outline_confirmation,
    confirm_outline,
    content_inventory_hash,
    content_inventory_state,
    image_manifest_ready,
    load_workflow_selection,
    planning_input_hash,
    validate_outline,
    workflow_gates,
)
from project_manager import ProjectManager  # noqa: E402
from server_common import (  # noqa: E402
    claim_lock as _claim_lock,
    find_free_port as _find_free_port,
    process_alive as _process_alive,
    read_lock as _read_lock,
    release_lock as _release_lock,
)

configure_utf8_stdio()

logger = logging.getLogger('confirm_ui')

# Per-project lock file. Lives at <project_path>/.confirm_ui.lock and matches
# the *.lock entry already in the repo .gitignore. Independent of the live
# preview lock so the two surfaces never collide.
LOCK_FILE_NAME = '.confirm_ui.lock'

# Round-trip files, both under <project_path>/confirm_ui/.
CONFIRM_DIR_NAME = 'confirm_ui'
RECOMMENDATIONS_NAME = 'recommendations.json'
RESULT_NAME = 'result.json'

# Static option universe served at /api/catalogs (canvas synced live from config).
_CATALOGS_PATH = Path(__file__).resolve().parent / 'static' / 'catalogs.json'
_ICON_LIBRARY_DIR = Path(__file__).resolve().parents[2] / 'templates' / 'icons'
_AI_IMAGE_COMPARISON_DIR = Path(__file__).resolve().parents[2] / 'references' / 'ai-image-comparison'
_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / 'templates'
_ANALYSIS_PACKS_DIR = _TEMPLATES_DIR / 'analysis-packs'
_ANALYSIS_LIBRARY_DIR = (
    _TEMPLATES_DIR / 'analysis-library' / 'diagram-prompt-building'
)
_ICON_PREVIEW_SAMPLES = {
    'chunk-filled': ('home', 'chart-line', 'users', 'target'),
    'tabler-filled': ('home', 'chart-dots', 'user', 'bulb'),
    'tabler-outline': ('home', 'chart-line', 'users', 'bulb'),
    'phosphor-duotone': ('house', 'chart-line', 'users', 'target'),
}

# Shares port 5050 with the live preview server (svg_editor/server.py). The two
# never run at once: confirm is Step 4 and shuts down on confirm (or idle),
# freeing the port before live preview starts at Step 6. One port = one forward
# rule for the whole pipeline. They still keep separate processes and locks.
DEFAULT_PORT = 5050

# Default --wait budget, kept just under the 600s Bash-tool ceiling so the
# parent (waiting) command returns before the calling harness kills it. The
# detached child server keeps running on its own --timeout idle budget, so a
# slow user can still confirm after the wait returns; the caller re-checks
# result.json before falling back to chat.
WAIT_TIMEOUT_DEFAULT = 590


def _read_json(path: Path, default=None):
    """Read a JSON file or return a caller-provided default."""
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def _write_json(path: Path, payload: dict) -> None:
    """Write UTF-8 JSON with a final newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _safe_upload_name(name: str, fallback: str = 'upload') -> str:
    """Return a Windows-safe basename while preserving readable Unicode."""
    basename = Path(name or fallback).name
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', basename).strip(' .')
    return cleaned[:180] or fallback


def _pack_record(pack_id: str) -> tuple[Path, Path]:
    """Resolve a registered analysis pack without allowing path traversal."""
    if not re.fullmatch(r'[a-z0-9-]+', pack_id or ''):
        raise ValueError('invalid analysis pack id')
    directory = (_ANALYSIS_PACKS_DIR / pack_id).resolve()
    if _ANALYSIS_PACKS_DIR.resolve() not in directory.parents:
        raise ValueError('analysis pack path escaped the library')
    workbook = directory / 'pack.xlsx'
    compiled = directory / 'pack.json'
    if not workbook.is_file():
        raise ValueError(f'analysis pack workbook not found: {workbook}')
    if not compiled.is_file() or workbook.stat().st_mtime > compiled.stat().st_mtime:
        compile_workbook(workbook, compiled, pack_id=pack_id)
    return workbook, compiled


def _analysis_library_catalog() -> dict:
    """Compile the two-level analysis library when stale and return its UI catalog."""
    workbook = _ANALYSIS_LIBRARY_DIR / 'prompts_master.xlsx'
    outputs = [
        _ANALYSIS_LIBRARY_DIR / 'styles.json',
        _ANALYSIS_LIBRARY_DIR / 'analysis_types.json',
        _ANALYSIS_LIBRARY_DIR / 'prompt_matrix.json',
    ]
    if not workbook.is_file():
        return {}
    if any(not path.is_file() for path in outputs) or any(
        workbook.stat().st_mtime > path.stat().st_mtime for path in outputs
    ):
        compile_library(workbook, _ANALYSIS_LIBRARY_DIR)
    library = load_library(_ANALYSIS_LIBRARY_DIR)
    styles = []
    for style in library['styles']:
        item = dict(style)
        item['preview_url'] = f"/analysis-library/{item['preview']}"
        styles.append(item)
    return {
        'schema_version': library['schema_version'],
        'library_id': library['library_id'],
        'default_style_id': library['default_style_id'],
        'styles': styles,
        'domains': library['domains'],
    }


def _image_manifest_ready(project_path: Path) -> tuple[bool, dict | None]:
    """Backward-compatible alias for the shared workflow gate helper."""
    return image_manifest_ready(project_path)


def _wait_for_result(
    result_file: Path,
    proc: subprocess.Popen,
    started_at: float,
    timeout: int,
) -> int:
    """Wait until this launch writes a fresh result file or the server exits."""
    logger.info('waiting for browser confirmation...')
    deadline = None if timeout <= 0 else time.time() + timeout
    while True:
        if result_file.exists():
            try:
                if result_file.stat().st_mtime >= started_at:
                    logger.info('confirmation received: %s', result_file)
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        pass
                    return 0
            except OSError:
                pass

        returncode = proc.poll()
        if returncode is not None:
            logger.error('confirm UI exited before a fresh result was written')
            return returncode or 1

        if deadline is not None and time.time() >= deadline:
            logger.error(
                'timed out waiting for browser confirmation — the page is still '
                'open; re-check %s before falling back to chat', result_file,
            )
            return 124

        time.sleep(0.5)


def _result_stage(result_file: Path) -> Optional[str]:
    """Return the canonical ``stage`` field of result.json, or None."""
    try:
        data = json.loads(result_file.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return _stage_key(data.get('stage')) if isinstance(data, dict) else None


def _stage_key(value: object) -> Optional[str]:
    """Normalize current stage names while accepting legacy tier values."""
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw in {'1', 'stage1', 'tier1'}:
        return 'stage1'
    if raw in {'2', 'stage2', 'tier2'}:
        return 'stage2'
    if raw in {'3', 'stage3', 'tier3'}:
        return 'stage3'
    if raw == 'final':
        return 'final'
    return None


def _recommendation_stage(data: dict) -> int:
    """Return recommendations.json stage number, with legacy tier fallback."""
    stage = _stage_key(data.get('stage'))
    if not stage and 'tier' in data:
        stage = _stage_key(data.get('tier'))
    if stage == 'stage1':
        return 1
    if stage == 'stage2':
        return 2
    if stage == 'stage3':
        return 3
    return 0


# Stage-1 anchors and Stage-2 design-system choices. On later pages these sections
# are not rendered (they were already confirmed), so their values live only in
# browser STATE — lost on a refresh. Folding them from result.json into the
# served recommendations lets a refresh / reopen re-initialize from the user's
# actual choices instead of catalog defaults.
_ANCHOR_RECOMMEND_KEYS = ('canvas', 'mode', 'visual_style', 'delivery_purpose')
_ANCHOR_VALUE_KEYS = ('audience', 'content_divergence')
_DESIGN_RECOMMEND_KEYS = ('icons', 'formula_policy')


def _merge_confirmed_choices(data: dict, result_file: Path) -> None:
    """Fold already-confirmed choices into later-stage recommendations."""
    try:
        res = json.loads(result_file.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(res, dict):
        return
    recommend = data.setdefault('recommend', {})
    if not isinstance(recommend, dict):
        recommend = data['recommend'] = {}
    for key in _ANCHOR_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    for key in _ANCHOR_VALUE_KEYS:
        if key in res:
            data[key] = {'value': res.get(key) or ''}
    if _recommendation_stage(data) < 3:
        return
    for key in _DESIGN_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    if 'page_count' in res:
        data['page_count'] = {'value': res.get('page_count') or ''}
    if isinstance(res.get('color'), dict):
        data['color'] = {'selected': 0, 'candidates': [res['color']]}
    if isinstance(res.get('typography'), dict):
        typography = {'selected': 0, 'candidates': [res['typography']]}
        if res.get('formula_policy') not in (None, ''):
            typography['formula_policy'] = {'value': res['formula_policy']}
        data['typography'] = typography


def _wait_only_for_result(
    result_file: Path,
    lock_file: Path,
    timeout: int,
    target_stage: str = 'final',
) -> int:
    """Attach to an already-running confirm server and wait for a target stage.

    No child is launched here: the page is still open from the first ``--wait``
    launch, so liveness is tracked via the recorded pid, not a ``proc`` handle.
    Only the stage guard is used (no mtime gate), because intermediate submits
    may happen before this wait command is issued.
    """
    logger.info('waiting for browser confirmation stage=%s...', target_stage)
    deadline = None if timeout <= 0 else time.time() + timeout
    while True:
        if _result_stage(result_file) == target_stage:
            logger.info('confirmation stage=%s received: %s', target_stage, result_file)
            return 0

        lock = _read_lock(lock_file)
        pid = int((lock or {}).get('pid', 0) or 0)
        if not pid or not _process_alive(pid):
            logger.error('confirm server is no longer running before stage=%s was confirmed', target_stage)
            return 1

        if deadline is not None and time.time() >= deadline:
            logger.error(
                'timed out waiting for confirmation stage=%s — the page may still '
                'be open; re-check %s before falling back to chat', target_stage, result_file,
            )
            return 124

        time.sleep(0.5)


def _shutdown_existing(lock_file: Path) -> int:
    """Stop a confirm server left running for this project (idempotent).

    Step 4 always calls this on exit so the page never lingers on the shared
    port 5050 — whether the user clicked **Confirm** (the page already shut the
    server down) or replied in chat instead (the server is still up). Tries a
    graceful ``/api/shutdown`` first, falls back to killing the recorded pid,
    then clears the lock. A no-op when nothing is running.
    """
    existing = _read_lock(lock_file)
    if not existing:
        logger.info('no confirm server running — nothing to stop')
        return 0
    pid = int(existing.get('pid', 0) or 0)
    port = existing.get('port')
    if not _process_alive(pid):
        _release_lock(lock_file)
        logger.info('confirm server already stopped; cleared stale lock')
        return 0
    # Graceful first: the server flushes and releases its own lock.
    if port:
        try:
            req = urllib.request.Request(
                f'http://127.0.0.1:{port}/api/shutdown',
                data=b'{"reason": "step4-cleanup"}',
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            urllib.request.urlopen(req, timeout=3)
        except OSError:
            pass  # server may already be exiting; fall through to the kill path
    for _ in range(20):  # up to ~2s for the graceful exit to land
        if not _process_alive(pid):
            break
        time.sleep(0.1)
    if _process_alive(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    _release_lock(lock_file)
    logger.info('confirm server stopped (pid=%s)', pid)
    return 0


def _build_catalogs() -> dict:
    """Return the static catalog set with the canvas list synced live from
    ``config.CANVAS_FORMATS`` — the single source of truth for canvas formats —
    so the confirm page can never drift from the pipeline's real formats. The
    set of formats and their dimensions come from config; trilingual labels and
    use text are kept from catalogs.json (with a plain fallback for any new id).
    """
    data = json.loads(_CATALOGS_PATH.read_text(encoding='utf-8'))
    try:
        import config  # scripts/ is on sys.path (injected at import time)
        formats = config.CANVAS_FORMATS
    except (ImportError, AttributeError):  # missing module/attr → static canvas
        return data
    existing = {
        c.get('id'): c
        for c in data.get('canvas', [])
        if isinstance(c, dict) and c.get('id')
    }
    canvas = []
    for cid, fmt in formats.items():
        entry = dict(existing.get(cid, {}))
        entry['id'] = cid
        entry['dim'] = fmt.get('dimensions', entry.get('dim', ''))
        if not entry.get('label'):
            name = fmt.get('name', cid)
            entry['label'] = name
            entry.setdefault('label_zh', name)
            entry.setdefault('label_en', name)
        if not entry.get('use_en') and fmt.get('use_case'):
            entry['use_en'] = fmt['use_case']
        canvas.append(entry)
    data['canvas'] = canvas
    return data


def _icon_preview_svg(library: str, name: str) -> str:
    """Read a trusted sample SVG from the bundled icon templates."""
    icon_path = _ICON_LIBRARY_DIR / library / f'{name}.svg'
    raw = icon_path.read_text(encoding='utf-8')
    raw = re.sub(r'<\?xml[^>]*>\s*', '', raw)
    raw = re.sub(r'<!--.*?-->\s*', '', raw, flags=re.S)
    return raw.strip()


def _build_icon_previews() -> dict:
    previews = {}
    for library, names in _ICON_PREVIEW_SAMPLES.items():
        items = []
        for name in names:
            try:
                items.append({'name': name, 'svg': _icon_preview_svg(library, name)})
            except OSError as exc:
                logger.warning('icon preview sample missing: %s/%s (%s)', library, name, exc)
        previews[library] = items
    return previews


def _ai_comparison_items(kind: str) -> list[dict[str, str]]:
    manifest = _AI_IMAGE_COMPARISON_DIR / kind / '_manifest.json'
    if not manifest.exists():
        return []
    data = json.loads(manifest.read_text(encoding='utf-8'))
    items = []
    for item in data.get('items', []):
        filename = item.get('filename')
        if not isinstance(filename, str) or not filename.endswith('.png'):
            continue
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.png', filename):
            continue
        if not (_AI_IMAGE_COMPARISON_DIR / kind / filename).exists():
            continue
        item_id = Path(filename).stem
        items.append({
            'id': item_id,
            'label': item.get('type') or item_id,
            'filename': filename,
            'purpose': item.get('purpose') or '',
            'alt_text': item.get('alt_text') or '',
        })
    return items


def _build_ai_image_comparison() -> dict:
    return {
        'rendering': _ai_comparison_items('rendering'),
        'palette': _ai_comparison_items('palette'),
        'type': _ai_comparison_items('type'),
    }


# --- app --------------------------------------------------------------------

def create_app(
    project_dir: str,
    idle_timeout: int = 900,
    lock_file: Optional[Path] = None,
    wizard_mode: bool = False,
) -> Flask:
    """Create and configure the Flask app for a given project directory."""
    project_path = Path(project_dir).resolve()
    confirm_dir = project_path / CONFIRM_DIR_NAME

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PROJECT_PATH'] = project_path
    app.config['CONFIRM_DIR'] = confirm_dir
    app.config['LOCK_FILE'] = lock_file
    app.config['LAST_REQUEST_TIME'] = time.time()
    app.config['WIZARD_MODE'] = wizard_mode
    if wizard_mode:
        version_path = project_path / 'workflow_version.json'
        if not version_path.exists():
            _write_json(version_path, {
                'schema_version': 4,
                'workflow': 'airi-content-planning',
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            })

    @app.before_request
    def _update_activity():
        app.config['LAST_REQUEST_TIME'] = time.time()

    def _exit_with_lock_release(code: int = 0) -> None:
        lf = app.config.get('LOCK_FILE')
        if lf is not None:
            _release_lock(lf)
        os._exit(code)

    def _idle_watchdog():
        if idle_timeout <= 0:
            return
        while True:
            time.sleep(10)
            elapsed = time.time() - app.config['LAST_REQUEST_TIME']
            if elapsed > idle_timeout:
                logger.info('idle for %ds, shutting down', idle_timeout)
                _exit_with_lock_release(0)

    watchdog = threading.Thread(target=_idle_watchdog, daemon=True)
    watchdog.start()

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        data = request.get_json(silent=True) or {}
        reason = data.get('reason') or 'shutdown'

        def _stop():
            time.sleep(0.5)  # let HTTP response flush before killing the process
            logger.info('shutting down (%s)', reason)
            _exit_with_lock_release(0)
        threading.Thread(target=_stop, daemon=True).start()
        return jsonify({'status': 'ok'})

    @app.route('/')
    def index():
        page = 'workflow.html' if app.config['WIZARD_MODE'] else 'index.html'
        return send_from_directory(app.static_folder, page)

    @app.route('/workflow')
    def workflow_index():
        return send_from_directory(app.static_folder, 'workflow.html')

    @app.route('/confirm')
    def legacy_confirm_index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/workflow-images/<path:filename>')
    def workflow_image(filename: str):
        return send_from_directory(project_path / 'images', filename)

    @app.route('/analysis-library/<path:filename>')
    def analysis_library_preview(filename: str):
        return send_from_directory(_ANALYSIS_LIBRARY_DIR, filename)

    @app.route('/api/workflow/state')
    def workflow_state():
        """Serve the persisted v2 wizard state and discovery catalogs."""
        try:
            pack_index = _read_json(_ANALYSIS_PACKS_DIR / 'analysis_packs_index.json', {}) or {}
            analysis_library = _analysis_library_catalog()
            deck_index = _read_json(_TEMPLATES_DIR / 'decks' / 'decks_index.json', {}) or {}
            analysis_ready, image_manifest = image_manifest_ready(project_path)
            images = []
            image_dir = project_path / 'images'
            if image_dir.is_dir():
                for path in sorted(image_dir.iterdir()):
                    if path.is_file() and path.suffix.lower() in {
                        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tif', '.tiff'
                    }:
                        images.append({
                            'name': path.name,
                            'path': f'images/{path.name}',
                            'url': f'/workflow-images/{path.name}',
                        })
            gates, outline_message = workflow_gates(project_path)
            selection = load_workflow_selection(project_path)
            inventory_ready, content_inventory, inventory_message = content_inventory_state(
                project_path
            )
            recommendations = _read_json(confirm_dir / RECOMMENDATIONS_NAME, {}) or {}
            recommended_style = str(
                (recommendations.get('recommend') or {}).get('visual_style') or 'swiss-minimal'
            )
            payload = {
                'schema_version': 4,
                'project': project_path.name,
                'source_manifest': _read_json(project_path / 'source_manifest.json'),
                'source_synthesis': _read_json(project_path / 'source_synthesis.json'),
                'workflow_brief': _read_json(project_path / 'workflow_brief.json', {}) or {},
                'selection': selection,
                'visual_style_recommendation': recommended_style,
                'analysis_library': analysis_library,
                'analysis_packs': pack_index.get('packs', []),
                'templates': [
                    {
                        'id': deck_id,
                        'number': index,
                        'path': f'templates/decks/{deck_id}',
                        **info,
                    }
                    for index, (deck_id, info) in enumerate(deck_index.items(), start=1)
                ],
                'images': images,
                'image_manifest': image_manifest,
                'analysis_ready': analysis_ready,
                'content_inventory': content_inventory,
                'content_inventory_ready': inventory_ready,
                'content_inventory_message': inventory_message,
                'outline_draft': _read_json(project_path / OUTLINE_DRAFT_NAME),
                'outline_confirmed': _read_json(project_path / OUTLINE_CONFIRMED_NAME),
                'outline_ready': gates['outline_ready'],
                'outline_message': outline_message,
                'gates': gates,
            }
            response = jsonify(payload)
            response.headers['Cache-Control'] = 'no-store'
            return response
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return jsonify({'error': str(exc)}), 500

    @app.route('/api/workflow/intake', methods=['POST'])
    def workflow_intake():
        """Archive uploaded files/text through the existing project intake path."""
        upload_dir = project_path / 'workflow_uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        staged: list[str] = []

        def _save_upload(file_storage, prefix: str = '') -> None:
            if file_storage is None or not file_storage.filename:
                return
            filename = _safe_upload_name(prefix + file_storage.filename)
            destination = upload_dir / filename
            if destination.exists():
                destination = upload_dir / f'{destination.stem}_{int(time.time())}{destination.suffix}'
            file_storage.save(destination)
            staged.append(str(destination))

        for file_storage in request.files.getlist('files'):
            _save_upload(file_storage)
        _save_upload(request.files.get('template_ppt'), 'style_template_')

        pasted_fields = {
            'text': 'pasted_text.md',
            'outline_text': 'pasted_existing_outline.md',
            'design_brief': 'pasted_design_brief.md',
            'design_task': 'pasted_design_task.md',
        }
        for field, filename in pasted_fields.items():
            value = (request.form.get(field) or '').strip()
            if not value:
                continue
            destination = upload_dir / filename
            destination.write_text(value + '\n', encoding='utf-8')
            staged.append(str(destination))

        urls = [line.strip() for line in (request.form.get('urls') or '').splitlines() if line.strip()]
        source_items = staged + urls
        if not source_items:
            return jsonify({'error': 'upload at least one file, text block, or URL'}), 400
        try:
            summary = ProjectManager().import_sources(
                str(project_path),
                source_items,
                move=True,
            )
            manifest_path, synthesis_path = build_source_manifest(project_path)
            brief = {
                'schema_version': 1,
                'updated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'audience': str(request.form.get('audience') or '').strip(),
                'objective': str(request.form.get('objective') or '').strip(),
                'canvas': str(request.form.get('canvas') or 'ppt169').strip(),
                'delivery_purpose': str(request.form.get('delivery_purpose') or 'balanced').strip(),
                'content_divergence': str(request.form.get('content_divergence') or '').strip(),
                'color_notes': str(request.form.get('color_notes') or '').strip(),
                'typography_notes': str(request.form.get('typography_notes') or '').strip(),
                'presentation_image_policy': str(
                    request.form.get('presentation_image_policy') or ''
                ).strip(),
            }
            _write_json(project_path / 'workflow_brief.json', brief)
            (project_path / OUTLINE_CONFIRMED_NAME).unlink(missing_ok=True)
            style_decks = sorted((project_path / 'sources').glob('style_template_*.ppt*'))
            if style_decks:
                _write_json(
                    project_path / 'template_request.json',
                    {
                        'schema_version': 1,
                        'status': 'pending-ai',
                        'source_pptx': style_decks[-1].relative_to(project_path).as_posix(),
                        'usage': 'style-reference-restructure',
                        'replication_mode': 'standard',
                        'preserve_page_count': False,
                        'output_dir': 'templates/custom-upload',
                        'workflow': 'workflows/create-template.md',
                    },
                )
        except (OSError, ValueError, RuntimeError) as exc:
            return jsonify({'error': str(exc)}), 400
        return jsonify({
            'status': 'ok',
            'import': summary,
            'source_manifest': str(manifest_path),
            'source_synthesis': str(synthesis_path),
        })

    @app.route('/api/workflow/selection', methods=['POST'])
    def workflow_selection():
        """Persist schema-v4 style and explicit professional-analysis decisions."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'invalid payload'}), 400
        analysis_required = payload.get('analysis_required')
        if not isinstance(analysis_required, bool):
            return jsonify({'error': 'confirm whether AI analysis images are required'}), 400
        visual_style = str(payload.get('visual_style') or '').strip()
        visual_style_source = str(payload.get('visual_style_source') or '')
        if not visual_style:
            return jsonify({'error': 'select or accept a presentation visual style'}), 400
        if visual_style_source not in {'user', 'auto'}:
            return jsonify({'error': 'visual_style_source must be user or auto'}), 400
        selection = {
            'schema_version': 4,
            'status': 'selection-confirmed',
            'updated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'visual_style': visual_style,
            'visual_style_source': visual_style_source,
            'template_id': str(payload.get('template_id') or ''),
            'custom_style_description': str(payload.get('custom_style_description') or ''),
            'analysis_required': analysis_required,
            'analysis_selection_confirmed': False,
            'analysis_pack_id': str(payload.get('analysis_pack_id') or '') if analysis_required else '',
            'analysis_library_id': str(payload.get('analysis_library_id') or '') if analysis_required else '',
            'analysis_style_id': str(payload.get('analysis_style_id') or '') if analysis_required else '',
            'analysis_domain_id': str(payload.get('analysis_domain_id') or '') if analysis_required else '',
            'analysis_item_ids': list(dict.fromkeys(
                str(value)
                for value in ((payload.get('analysis_item_ids') or []) if analysis_required else [])
                if str(value).strip()
            )),
            'reference_images': [
                str(value)
                for value in ((payload.get('reference_images') or []) if analysis_required else [])
                if str(value).strip()
            ],
            'provider_profile': str(payload.get('provider_profile') or DEFAULT_PROFILE),
        }
        if selection['analysis_pack_id']:
            try:
                _pack_record(selection['analysis_pack_id'])
            except (OSError, ValueError) as exc:
                return jsonify({'error': str(exc)}), 400
        if analysis_required:
            try:
                if (
                    'analysis_selection_confirmed' in payload
                    and not bool(payload.get('analysis_selection_confirmed'))
                ):
                    raise ValueError('confirm at least one analysis type before saving')
                library = _analysis_library_catalog()
                valid_styles = {item['id'] for item in library.get('styles', [])}
                valid_items = {
                    item['id']
                    for domain in library.get('domains', [])
                    for item in domain.get('items', [])
                }
                if selection['analysis_library_id'] != library.get('library_id'):
                    raise ValueError('invalid analysis library id')
                if selection['analysis_style_id'] not in valid_styles:
                    raise ValueError('select a valid analysis style')
                selection['analysis_item_ids'] = resolve_domain_item_ids(
                    library,
                    selection['analysis_domain_id'],
                    selection['analysis_item_ids'],
                )
                unknown = [item_id for item_id in selection['analysis_item_ids'] if item_id not in valid_items]
                if unknown:
                    raise ValueError(f"unknown analysis type(s): {', '.join(unknown)}")
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                return jsonify({'error': str(exc)}), 400
        selection['analysis_selection_confirmed'] = True
        selection['analysis_selection_hash'] = analysis_selection_hash(selection)
        prior = load_workflow_selection(project_path)
        _write_json(project_path / 'workflow_selection.json', selection)
        if any(
            prior.get(key) != selection.get(key)
            for key in (
                'visual_style',
                'visual_style_source',
                'template_id',
                'custom_style_description',
                'analysis_required',
                'analysis_selection_hash',
            )
        ):
            (project_path / OUTLINE_CONFIRMED_NAME).unlink(missing_ok=True)
        return jsonify({'status': 'ok', 'selection': selection})

    @app.route('/api/workflow/generate-analysis', methods=['POST'])
    def workflow_generate_analysis():
        """Generate internally resolved analysis items for the selected domain and style."""
        payload = request.get_json(silent=True) or {}
        selection = load_workflow_selection(project_path)
        if selection.get('analysis_required') is not True:
            return jsonify({'error': 'analysis generation is available only after choosing Yes'}), 409
        if not selection.get('analysis_selection_confirmed'):
            return jsonify({'error': 'confirm the analysis style and domain first'}), 409
        style_id = str(payload.get('analysis_style_id') or selection.get('analysis_style_id') or '')
        item_ids = payload.get('analysis_item_ids') or selection.get('analysis_item_ids') or []
        references = payload.get('reference_images') or selection.get('reference_images') or []
        profile = str(
            payload.get('provider_profile')
            or selection.get('provider_profile')
            or DEFAULT_PROFILE
        )
        dry_run = bool(payload.get('dry_run'))
        if not style_id or not item_ids:
            return jsonify({'error': 'select an analysis style and analysis domain'}), 400
        try:
            manifest = build_library_manifest(
                _ANALYSIS_LIBRARY_DIR,
                project_path,
                style_id,
                [str(value) for value in item_ids],
                [str(value) for value in references],
                provider_profile=profile,
                prompt_context=str(payload.get('prompt_context') or ''),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return jsonify({'error': str(exc)}), 400
        manifest_data = _read_json(Path(manifest), {}) or {}
        manifest_data['analysis_selection_hash'] = selection['analysis_selection_hash']
        _write_json(Path(manifest), manifest_data)
        command = [
            sys.executable,
            str(_SCRIPTS_DIR / 'image_gen.py'),
            '--manifest',
            str(manifest),
        ]
        if dry_run:
            command.append('--dry-run')
        completed = subprocess.run(
            command,
            cwd=str(_SCRIPTS_DIR.parent.parent.parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=3600,
            check=False,
        )
        if completed.returncode != 0:
            return jsonify({
                'error': 'analysis image generation failed',
                'returncode': completed.returncode,
                'stdout': completed.stdout[-4000:],
                'stderr': completed.stderr[-4000:],
            }), 500
        return jsonify({
            'status': 'ok',
            'dry_run': dry_run,
            'manifest': str(manifest),
            'selected_count': len(item_ids),
            'stdout': completed.stdout[-4000:],
        })

    @app.route('/api/workflow/content-inventory', methods=['GET', 'POST'])
    def workflow_content_inventory():
        """Read or persist the post-analysis content and page-count inventory."""
        inventory_path = project_path / CONTENT_INVENTORY_PATH
        if request.method == 'GET':
            inventory = _read_json(inventory_path)
            if inventory is None:
                return jsonify({'error': 'content inventory not found'}), 404
            return jsonify(inventory)
        gates, message = workflow_gates(project_path)
        required = ('style_confirmed', 'analysis_decided', 'analysis_selection_confirmed', 'analysis_ready')
        if not all(gates.get(key) for key in required):
            return jsonify({'error': message}), 409
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'invalid payload'}), 400
        try:
            page_count = int(payload.get('recommended_page_count'))
        except (TypeError, ValueError):
            return jsonify({'error': 'recommended_page_count must be an integer'}), 400
        if page_count <= 0 or not payload.get('page_count_rationale'):
            return jsonify({'error': 'page count and rationale are required'}), 400
        inventory = dict(payload)
        inventory.update({
            'schema_version': 1,
            'status': 'ready',
            'updated_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'recommended_page_count': page_count,
            'planning_input_hash': planning_input_hash(project_path),
        })
        _write_json(inventory_path, inventory)
        (project_path / OUTLINE_CONFIRMED_NAME).unlink(missing_ok=True)
        return jsonify({'status': 'ok', 'inventory': inventory})

    @app.route('/api/workflow/generate-pack', methods=['POST'])
    def workflow_generate_pack():
        """Build and execute every enabled item in the manually selected pack."""
        payload = request.get_json(silent=True) or {}
        selection = _read_json(project_path / 'workflow_selection.json', {}) or {}
        pack_id = str(payload.get('analysis_pack_id') or selection.get('analysis_pack_id') or '')
        references = payload.get('reference_images') or selection.get('reference_images') or []
        profile = str(payload.get('provider_profile') or selection.get('provider_profile') or DEFAULT_PROFILE)
        dry_run = bool(payload.get('dry_run'))
        if not pack_id:
            return jsonify({'error': 'select an analysis pack first'}), 400
        try:
            _, compiled = _pack_record(pack_id)
            manifest = build_image_manifest(
                compiled,
                project_path,
                list(references),
                provider_profile=profile,
                prompt_context=str(payload.get('prompt_context') or ''),
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return jsonify({'error': str(exc)}), 400
        command = [
            sys.executable,
            str(_SCRIPTS_DIR / 'image_gen.py'),
            '--manifest',
            str(manifest),
        ]
        if dry_run:
            command.append('--dry-run')
        completed = subprocess.run(
            command,
            cwd=str(_SCRIPTS_DIR.parent.parent.parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=3600,
            check=False,
        )
        if completed.returncode != 0:
            return jsonify({
                'error': 'analysis pack generation failed',
                'returncode': completed.returncode,
                'stdout': completed.stdout[-4000:],
                'stderr': completed.stderr[-4000:],
            }), 500
        return jsonify({
            'status': 'ok',
            'dry_run': dry_run,
            'manifest': str(manifest),
            'stdout': completed.stdout[-4000:],
        })

    @app.route('/api/workflow/outline', methods=['GET', 'POST'])
    def workflow_outline():
        """Read or replace the editable page-card outline."""
        draft_path = project_path / OUTLINE_DRAFT_NAME
        if request.method == 'GET':
            draft = _read_json(draft_path)
            if draft is None:
                return jsonify({'error': 'outline draft not found'}), 404
            return jsonify(draft)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'invalid payload'}), 400
        gates, message = workflow_gates(project_path)
        prerequisites = (
            'style_confirmed',
            'analysis_decided',
            'analysis_selection_confirmed',
            'analysis_ready',
            'content_inventory_ready',
        )
        if not all(gates.get(key) for key in prerequisites):
            return jsonify({'error': message}), 409
        candidate = dict(payload)
        candidate['schema_version'] = 3
        errors = validate_outline(candidate)
        if errors:
            return jsonify({'error': '; '.join(errors)}), 400
        draft = candidate
        draft['status'] = 'draft'
        draft['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        draft['planning_input_hash'] = planning_input_hash(project_path)
        draft['content_inventory_hash'] = content_inventory_hash(project_path)
        _write_json(draft_path, draft)
        (project_path / OUTLINE_CONFIRMED_NAME).unlink(missing_ok=True)
        return jsonify({'status': 'ok', 'outline': draft})

    @app.route('/api/workflow/outline/confirm', methods=['POST'])
    def workflow_outline_confirm():
        """Confirm the current outline only after selected analysis images exist."""
        gates, message = workflow_gates(project_path)
        prerequisites = (
            'style_confirmed',
            'analysis_decided',
            'analysis_selection_confirmed',
            'analysis_ready',
            'content_inventory_ready',
            'outline_ready',
        )
        if not all(gates.get(key) for key in prerequisites):
            return jsonify({'error': message}), 409
        try:
            confirmed = confirm_outline(project_path)
        except (OSError, ValueError) as exc:
            return jsonify({'error': str(exc)}), 400
        return jsonify({'status': 'confirmed', 'path': str(confirmed)})

    @app.route('/api/workflow/upload-image', methods=['POST'])
    def workflow_upload_image():
        """Add a replacement image to the project's runtime image pool."""
        file_storage = request.files.get('image')
        if file_storage is None or not file_storage.filename:
            return jsonify({'error': 'image file is required'}), 400
        image_dir = project_path / 'images'
        image_dir.mkdir(parents=True, exist_ok=True)
        filename = _safe_upload_name(file_storage.filename, 'replacement.png')
        destination = image_dir / filename
        if destination.exists():
            destination = image_dir / f'{destination.stem}_{int(time.time())}{destination.suffix}'
        file_storage.save(destination)
        build_source_manifest(project_path)
        (project_path / OUTLINE_CONFIRMED_NAME).unlink(missing_ok=True)
        return jsonify({
            'status': 'ok',
            'name': destination.name,
            'path': f'images/{destination.name}',
            'url': f'/workflow-images/{destination.name}',
        })

    @app.route('/api/workflow/regenerate-image', methods=['POST'])
    def workflow_regenerate_image():
        """Re-run one edited manifest item while keeping completed siblings idempotent."""
        payload = request.get_json(silent=True) or {}
        filename = Path(str(payload.get('filename') or '')).name
        manifest_path = project_path / 'images' / 'image_prompts.json'
        manifest = _read_json(manifest_path)
        if not filename or not isinstance(manifest, dict):
            return jsonify({'error': 'valid filename and image manifest are required'}), 400
        item = next((row for row in manifest.get('items', []) if row.get('filename') == filename), None)
        if item is None:
            return jsonify({'error': f'image item not found: {filename}'}), 404
        if payload.get('prompt') is not None:
            item['prompt'] = str(payload['prompt'])
        if payload.get('reference_images') is not None:
            item['reference_images'] = [str(value) for value in payload['reference_images']]
        item['status'] = 'Pending'
        item.pop('last_error', None)
        _write_json(manifest_path, manifest)
        completed = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / 'image_gen.py'), '--manifest', str(manifest_path)],
            cwd=str(_SCRIPTS_DIR.parent.parent.parent),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=1800,
            check=False,
        )
        if completed.returncode != 0:
            return jsonify({
                'error': 'image regeneration failed',
                'stdout': completed.stdout[-3000:],
                'stderr': completed.stderr[-3000:],
            }), 500
        return jsonify({'status': 'ok', 'filename': filename, 'stdout': completed.stdout[-3000:]})

    @app.route('/api/catalogs')
    def get_catalogs():
        """Serve the option universe; canvas is synced live from config.py so
        the static catalogs.json copy can never drift from the real formats."""
        try:
            resp = jsonify(_build_catalogs())
            resp.headers['Cache-Control'] = 'no-store'
            return resp
        except (OSError, json.JSONDecodeError) as exc:
            return jsonify({'error': f'invalid catalogs.json: {exc}'}), 500

    @app.route('/api/icon-previews')
    def get_icon_previews():
        """Serve real sample icons from templates/icons for the icon chooser."""
        resp = jsonify(_build_icon_previews())
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.route('/api/ai-image-comparison')
    def get_ai_image_comparison_manifest():
        """Serve generated-image reference options from ai-image-comparison."""
        try:
            resp = jsonify(_build_ai_image_comparison())
            resp.headers['Cache-Control'] = 'no-store'
            return resp
        except (OSError, json.JSONDecodeError) as exc:
            return jsonify({'error': f'invalid ai-image-comparison manifest: {exc}'}), 500

    @app.route('/ai-image-comparison/<kind>/<filename>')
    def get_ai_image_comparison(kind: str, filename: str):
        """Serve reference images for generated-image strategy candidates."""
        if kind not in {'rendering', 'palette', 'type'}:
            return jsonify({'error': 'invalid comparison kind'}), 404
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.png', filename or ''):
            return jsonify({'error': 'invalid comparison filename'}), 404
        return send_from_directory(_AI_IMAGE_COMPARISON_DIR / kind, filename)

    @app.route('/api/recommendations')
    def get_recommendations():
        """Serve the Strategist-authored recommendations for this project."""
        rec_file = confirm_dir / RECOMMENDATIONS_NAME
        if not rec_file.exists():
            return jsonify({'error': 'recommendations not found'}), 404
        try:
            data = json.loads(rec_file.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            return jsonify({'error': f'invalid recommendations.json: {exc}'}), 400
        # Report whether a result already exists (re-open after confirm).
        result_file = confirm_dir / RESULT_NAME
        data['_already_confirmed'] = result_file.exists()
        # Later stages render only downstream sections, so fold earlier confirmed
        # choices from result.json back in. A refresh / reopen then re-inits from
        # the user's choices instead of catalog defaults.
        if _recommendation_stage(data) >= 2 and result_file.exists():
            _merge_confirmed_choices(data, result_file)
        # The page polls this endpoint after a stage-1 confirm until the AI
        # overwrites the file with the re-derived stage-2 recommendations, so it
        # must never be served from a cache.
        resp = jsonify(data)
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.route('/api/confirm', methods=['POST'])
    def confirm():
        """Persist the user's final choices to result.json for the AI to read."""
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({'error': 'invalid payload'}), 400
        confirm_dir.mkdir(parents=True, exist_ok=True)
        result = dict(payload)
        # Staged flow: stage-1 / stage-2 submits record intermediate choices but do
        # NOT close the page. Only a final submit is a full confirmation. A
        # payload with no stage is a single-pass confirmation (chat-opt-out parity).
        stage = _stage_key(result.get('stage'))
        if stage in {'stage1', 'stage2'}:
            result['stage'] = stage
            result['status'] = f'{stage}-confirmed'
        else:
            result['stage'] = 'final'
            result['status'] = 'confirmed'
        result['confirmed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        result_file = confirm_dir / RESULT_NAME
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        logger.info('%s confirmation written to %s', result['stage'], result_file)
        return jsonify({'status': 'ok'})

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='PPT Master Strategist confirmation stage UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('project_dir', help='Path to project directory')
    parser.add_argument(
        '--port', type=int, default=DEFAULT_PORT,
        help=f'Port to listen on (default: {DEFAULT_PORT})',
    )
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    parser.add_argument(
        '--wizard', action='store_true',
        help='Open the v2 intake/style/analysis-pack/outline workflow instead of the legacy confirmation page.',
    )
    parser.add_argument(
        '--daemon', action='store_true',
        help='Start the server in the background; combine with --wait to block until confirmation',
    )
    parser.add_argument(
        '--wait', action='store_true',
        help='With --daemon, wait until a fresh result.json is written',
    )
    parser.add_argument(
        '--wait-only', action='store_true',
        help='Do not launch. Attach to the already-running confirm server for '
             'this project and wait for an already-open page to write result.json.',
    )
    parser.add_argument(
        '--wait-stage', default='final', metavar='{stage2,final}',
        help='With --wait-only, wait for this result.json stage (default: final). '
             'Use stage2 for the middle handoff in the three-stage flow.',
    )
    parser.add_argument(
        '--wait-timeout', type=int, default=WAIT_TIMEOUT_DEFAULT,
        help=f'Seconds the --wait parent blocks before returning (default: {WAIT_TIMEOUT_DEFAULT}; '
             '0 = no limit). Kept under the caller\'s tool timeout; the detached server lives on.',
    )
    parser.add_argument(
        '--timeout', type=int, default=900,
        help='Server idle timeout in seconds (default: 900; 0 = disabled)',
    )
    parser.add_argument(
        '--shutdown', action='store_true',
        help='Stop a confirm server left running for this project, then exit '
             '(idempotent). Run at the end of Step 4 so the page never lingers '
             'on the shared port before live preview starts.',
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] confirm_ui: %(message)s',
        datefmt='%H:%M:%S',
    )

    project_path = Path(args.project_dir).resolve()
    if not project_path.is_dir():
        logger.error('%s is not a directory', project_path)
        return 1
    wait_stage = _stage_key(args.wait_stage)
    if wait_stage not in {'stage2', 'final'}:
        logger.error('--wait-stage must be stage2 or final')
        return 2

    # Step 4 cleanup: stop any lingering confirm server and exit. Independent of
    # recommendations.json (the page may never have been confirmed).
    if args.shutdown:
        return _shutdown_existing(project_path / LOCK_FILE_NAME)

    # Staged wait: attach to the server launched by the first --wait and block
    # until the page writes the requested intermediate or final result.json.
    if args.wait_only:
        return _wait_only_for_result(
            project_path / CONFIRM_DIR_NAME / RESULT_NAME,
            project_path / LOCK_FILE_NAME,
            args.wait_timeout,
            wait_stage,
        )

    rec_file = project_path / CONFIRM_DIR_NAME / RECOMMENDATIONS_NAME
    if not args.wizard and not rec_file.exists():
        logger.error(
            '%s not found — Strategist must write recommendations.json before launch',
            rec_file,
        )
        return 1

    if args.daemon:
        lock_file = project_path / LOCK_FILE_NAME
        existing = _read_lock(lock_file)
        if existing and _process_alive(int(existing.get('pid', 0))):
            existing_pid = existing.get('pid', '?')
            existing_port = existing.get('port', '?')
            logger.error(
                'confirm UI is already running for this project '
                '(pid=%s, port=%s). Open http://localhost:%s',
                existing_pid, existing_port, existing_port,
            )
            return 1

        confirm_dir = project_path / CONFIRM_DIR_NAME
        confirm_dir.mkdir(parents=True, exist_ok=True)
        log_path = confirm_dir / 'server.log'
        result_file = confirm_dir / RESULT_NAME
        started_at = time.time()
        # Pick a free port up front (another project may hold the default) and
        # pass the concrete port to the child so the reported URL is accurate.
        port = _find_free_port(args.port)
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            str(project_path),
            '--port',
            str(port),
            '--timeout',
            str(args.timeout),
        ]
        if args.no_browser:
            cmd.append('--no-browser')
        if args.wizard:
            cmd.append('--wizard')
        creationflags = 0
        popen_kwargs = {}
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            popen_kwargs['start_new_session'] = True
        with log_path.open('a', encoding='utf-8') as log:
            proc = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                **popen_kwargs,
            )
        url = f'http://localhost:{port}'
        logger.info('started confirm UI in background: %s (pid=%s)', url, proc.pid)
        logger.info('log: %s', log_path)
        if args.wait:
            return _wait_for_result(result_file, proc, started_at, args.wait_timeout)
        return 0

    # Per-project mutual exclusion: refuse duplicate launches. Stale locks
    # (dead pid) are overwritten by _claim_lock.
    lock_file = project_path / LOCK_FILE_NAME
    existing = _claim_lock(lock_file, args.port)
    if existing:
        existing_pid = existing.get('pid', '?')
        existing_port = existing.get('port', '?')
        logger.error(
            'confirm UI is already running for this project '
            '(pid=%s, port=%s). Open http://localhost:%s, or run: kill %s',
            existing_pid, existing_port, existing_port, existing_pid,
        )
        return 1
    atexit.register(_release_lock, lock_file)

    def _on_sigterm(signum: int, _frame) -> None:
        logger.info('received signal %s, exiting', signum)
        sys.exit(0)
    try:
        signal.signal(signal.SIGTERM, _on_sigterm)
    except (ValueError, OSError):
        pass

    app = create_app(
        str(project_path),
        idle_timeout=args.timeout,
        lock_file=lock_file,
        wizard_mode=args.wizard,
    )

    url = f'http://localhost:{args.port}'
    if not args.no_browser:
        webbrowser.open(url)

    logger.info('running at %s', url)
    logger.info('project: %s', project_path)
    logger.info('idle timeout: %ds (0 = disabled)', args.timeout)
    app.run(host='127.0.0.1', port=args.port, debug=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
