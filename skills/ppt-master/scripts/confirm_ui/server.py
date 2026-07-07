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

try:
    from flask import Flask, jsonify, request, send_from_directory
except ImportError:
    Flask = None
    jsonify = None
    request = None
    send_from_directory = None

# Local — sys.path injection for sibling module (code-style.md §3)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
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
        data = _read_json_lenient(result_file)
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
        res = _read_json_lenient(result_file)
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


def _build_style_previews() -> dict:
    """Inline visual-style preview SVGs for local HTML mode."""
    preview_dir = Path(__file__).resolve().parent / 'static' / 'style_previews'
    previews = {}
    for path in preview_dir.glob('*.svg'):
        try:
            previews[path.stem] = path.read_text(encoding='utf-8')
        except OSError:
            continue
    return previews


def _read_json_lenient(path: Path) -> dict:
    """Read JSON written by shells/editors that may prepend a UTF-8 BOM."""
    return json.loads(path.read_text(encoding='utf-8-sig'))


def _write_json_utf8(path: Path, data: dict) -> None:
    """Write JSON as UTF-8 without BOM."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )


def _import_local_result(project_path: Path, source: Path) -> Path:
    """Import a local-HTML downloaded result.json into the project."""
    data = _read_json_lenient(source)
    if not isinstance(data, dict):
        raise ValueError('result JSON must be an object')
    stage = _stage_key(data.get('stage'))
    if stage not in {'stage1', 'stage2', 'final'}:
        data['stage'] = 'final'
    if data.get('stage') in {'stage1', 'stage2'}:
        data['status'] = f"{data['stage']}-confirmed"
    else:
        data['stage'] = 'final'
        data['status'] = 'confirmed'
    data.setdefault('confirmed_at', time.strftime('%Y-%m-%dT%H:%M:%S'))
    result_file = project_path / CONFIRM_DIR_NAME / RESULT_NAME
    _write_json_utf8(result_file, data)
    return result_file


def _build_local_html(project_path: Path, output: Optional[Path] = None) -> Path:
    """Write a self-contained local confirmation page into the project.

    The local page is a fallback for Windows/Python environments where the
    Flask server cannot start. It embeds the current recommendations and
    catalogs directly, so users can open it with ``file://``. Because browsers
    cannot silently write local files from ``file://`` pages, confirmation
    downloads ``result.json`` and also shows the JSON on screen for saving.
    """
    confirm_dir = project_path / CONFIRM_DIR_NAME
    rec_file = confirm_dir / RECOMMENDATIONS_NAME
    if not rec_file.exists():
        raise FileNotFoundError(f'{rec_file} not found')
    confirm_dir.mkdir(parents=True, exist_ok=True)
    output_path = output or (confirm_dir / 'confirm_local.html')

    static_dir = Path(__file__).resolve().parent / 'static'
    index_html = (static_dir / 'index.html').read_text(encoding='utf-8')
    style_css = (static_dir / 'style.css').read_text(encoding='utf-8')
    app_js = (static_dir / 'app.js').read_text(encoding='utf-8')

    payload = {
        'recommendations': _read_json_lenient(rec_file),
        'catalogs': _build_catalogs(),
        'iconPreviews': _build_icon_previews(),
        'aiImageComparison': _build_ai_image_comparison(),
        'stylePreviews': _build_style_previews(),
    }
    data_script = (
        '<script>\n'
        'window.PPT_MASTER_LOCAL_DATA = '
        + json.dumps(payload, ensure_ascii=False)
        + ';\n</script>'
    )

    html = index_html
    html = re.sub(
        r'<link\s+rel="stylesheet"\s+href="/static/style\.css"\s*/?>',
        lambda _match: '<style>\n' + style_css + '\n</style>',
        html,
        count=1,
    )
    html = re.sub(
        r'<script\s+src="/static/app\.js"></script>',
        lambda _match: data_script + '\n<script>\n' + app_js + '\n</script>',
        html,
        count=1,
    )
    # Some old mojibake in the static template can leave malformed visible
    # glyphs; keep generated HTML parseable and self-contained.
    if '<script src="/static/app.js"></script>' in html:
        html += '\n' + data_script + '\n<script>\n' + app_js + '\n</script>\n'

    output_path.write_text(html, encoding='utf-8')
    return output_path


# --- app --------------------------------------------------------------------

def create_app(
    project_dir: str,
    idle_timeout: int = 900,
    lock_file: Optional[Path] = None,
) -> "Flask":
    """Create and configure the Flask app for a given project directory."""
    if Flask is None:
        raise RuntimeError("Flask is required for server mode. Use --local-html to generate an offline page.")
    project_path = Path(project_dir).resolve()
    confirm_dir = project_path / CONFIRM_DIR_NAME

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PROJECT_PATH'] = project_path
    app.config['CONFIRM_DIR'] = confirm_dir
    app.config['LOCK_FILE'] = lock_file
    app.config['LAST_REQUEST_TIME'] = time.time()

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
        return send_from_directory(app.static_folder, 'index.html')

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
            data = json.loads(rec_file.read_text(encoding='utf-8-sig'))
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
        _write_json_utf8(result_file, result)
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
    parser.add_argument(
        '--local-html', action='store_true',
        help='Write a self-contained confirm_local.html that can be opened from '
             'the filesystem without running Flask.',
    )
    parser.add_argument(
        '--local-output', default=None,
        help='Output path for --local-html. Default: <project>/confirm_ui/confirm_local.html.',
    )
    parser.add_argument(
        '--import-result', default=None,
        help='Import a result.json downloaded from --local-html into <project>/confirm_ui/result.json.',
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
    if args.import_result:
        try:
            result_file = _import_local_result(project_path, Path(args.import_result).resolve())
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.error('failed to import local result: %s', exc)
            return 1
        logger.info('local result imported: %s', result_file)
        return 0
    if args.local_html:
        try:
            output = Path(args.local_output).resolve() if args.local_output else None
            html_path = _build_local_html(project_path, output)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error('failed to write local confirm HTML: %s', exc)
            return 1
        logger.info('local confirm HTML written: %s', html_path)
        return 0
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
    if not rec_file.exists():
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
