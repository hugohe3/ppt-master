#!/usr/bin/env python3
"""
PPT Master - Eight Confirmations UI Server (Step 4)

Lightweight Flask backend for the interactive, visual Eight Confirmations page.
Strategist writes its recommendations to
``<project>/confirm_ui/recommendations.json``; this server renders them as a
clickable page (color swatches, live font previews, candidate picks). On
submit it writes the user's final choices to
``<project>/confirm_ui/result.json`` for the AI to read back.

This is the confirmation surface only. The chat fallback always remains valid:
if the browser cannot open (remote / headless / web host), the AI presents the
same Eight Confirmations in chat.

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

from server_common import (  # noqa: E402
    claim_lock as _claim_lock,
    find_free_port as _find_free_port,
    process_alive as _process_alive,
    read_lock as _read_lock,
    release_lock as _release_lock,
)

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
    """Return the ``stage`` field of result.json (``tier1`` / ``final``), or None."""
    try:
        data = json.loads(result_file.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get('stage') if isinstance(data, dict) else None


# Tier-1 anchors. On the Tier-2 page these sections are not rendered (they were
# confirmed in Tier 1), so their values live only in browser STATE — lost on a
# refresh. Folding them from result.json into the served Tier-2 recommendations
# lets the page re-initialize them from the user's actual choices.
_ANCHOR_RECOMMEND_KEYS = ('canvas', 'mode', 'visual_style', 'delivery_purpose')
_ANCHOR_VALUE_KEYS = ('audience', 'content_divergence')


def _merge_confirmed_anchors(data: dict, result_file: Path) -> None:
    """Fold the Tier-1 anchors confirmed in result.json into a Tier-2
    recommendations payload, so a refresh / reopen re-initializes them. The
    confirmed value is truth — it overrides any stale recommend entry."""
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


def _wait_only_for_result(
    result_file: Path,
    lock_file: Path,
    timeout: int,
) -> int:
    """Attach to an already-running confirm server and wait for the **final**
    (tier-2) result.json — the second leg of the two-tier flow. No child is
    launched here: the page is still open from the first ``--wait`` launch, so
    liveness is tracked via the recorded pid, not a ``proc`` handle. Only the
    ``stage == 'final'`` guard is used (no mtime gate): this run's tier-1 confirm
    already left result.json at stage ``tier1``, so any ``final`` is the tier-2
    submit, and a mtime gate would race-miss a user who confirms before this wait.
    """
    logger.info('waiting for tier-2 browser confirmation...')
    deadline = None if timeout <= 0 else time.time() + timeout
    while True:
        # `stage == 'final'` alone is the signal: this run's tier-1 confirm already
        # overwrote result.json to stage 'tier1', so any 'final' here is the tier-2
        # submit we are waiting for. Gating on mtime >= started_at would race-miss a
        # user who confirms tier 2 before this wait is even issued.
        if _result_stage(result_file) == 'final':
            logger.info('tier-2 confirmation received: %s', result_file)
            return 0

        lock = _read_lock(lock_file)
        pid = int((lock or {}).get('pid', 0) or 0)
        if not pid or not _process_alive(pid):
            logger.error('confirm server is no longer running before tier 2 was confirmed')
            return 1

        if deadline is not None and time.time() >= deadline:
            logger.error(
                'timed out waiting for tier-2 confirmation — the page may still '
                'be open; re-check %s before falling back to chat', result_file,
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
    set of formats and their dimensions come from config; bilingual labels and
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


# --- app --------------------------------------------------------------------

def create_app(
    project_dir: str,
    idle_timeout: int = 900,
    lock_file: Optional[Path] = None,
) -> Flask:
    """Create and configure the Flask app for a given project directory."""
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
        # Tier 2 renders only realization sections, so fold the confirmed Tier-1
        # anchors from result.json back in — a refresh / reopen then re-inits
        # canvas / audience / mode / visual_style / delivery_purpose from the
        # user's choices instead of catalog defaults.
        if data.get('tier') == 2 and result_file.exists():
            _merge_confirmed_anchors(data, result_file)
        # The page polls this endpoint after a tier-1 confirm until the AI
        # overwrites the file with the re-derived tier-2 recommendations, so it
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
        # Two-tier flow: a tier-1 submit records the anchor choices but does NOT
        # close the page (the AI re-derives tier 2, the same browser session
        # renders it). Only a final submit is a full confirmation. A payload with
        # no stage is a single-pass confirmation (chat-opt-out parity).
        stage = result.get('stage')
        result['status'] = 'tier1-confirmed' if stage == 'tier1' else 'confirmed'
        result['confirmed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        result_file = confirm_dir / RESULT_NAME
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        logger.info('%s confirmation written to %s', stage or 'final', result_file)
        return jsonify({'status': 'ok'})

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='PPT Master Eight Confirmations UI',
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
             'this project and wait for the final (tier-2) result.json. Used for '
             'the second leg of the two-tier flow after the tier-2 '
             'recommendations have been re-derived and written.',
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

    # Step 4 cleanup: stop any lingering confirm server and exit. Independent of
    # recommendations.json (the page may never have been confirmed).
    if args.shutdown:
        return _shutdown_existing(project_path / LOCK_FILE_NAME)

    # Tier-2 wait: attach to the server already serving this project (launched by
    # the first --wait) and block until the page writes the final result.json.
    if args.wait_only:
        return _wait_only_for_result(
            project_path / CONFIRM_DIR_NAME / RESULT_NAME,
            project_path / LOCK_FILE_NAME,
            args.wait_timeout,
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
