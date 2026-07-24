#!/usr/bin/env python3
"""
PPT Master - Strategist confirmation stage UI Server (Step 4)

Lightweight Flask backend for the interactive, visual Strategist confirmation
stage page. Strategist writes each stage to
``<project>/confirm_ui/recommendations.stageN.json``; this server selects the
current stage from ``result.json`` and renders it as a clickable page (color
swatches, live font previews, candidate picks). On submit it writes the user's
choices to ``<project>/confirm_ui/result.json`` for the AI to read back.

This is the default confirmation surface. The chat fallback is used only when
the user explicitly requests chat-only confirmation or the browser launch
fails; it preserves the same staged semantics.

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
import urllib.error
import urllib.request
import uuid
import webbrowser
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

# Local — sys.path injection for sibling module (code-style.md §3)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from server_common import (  # noqa: E402
    claim_lock as _claim_lock,
    clear_lock as _clear_lock,
    find_free_port as _find_free_port,
    lock_pid as _lock_pid,
    popen_detached as _popen_detached,
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

# Round-trip/session files, all under <project_path>/confirm_ui/.
CONFIRM_DIR_NAME = 'confirm_ui'
LEGACY_RECOMMENDATIONS_NAME = 'recommendations.json'
RECOMMENDATION_STAGE_NAMES = {
    1: 'recommendations.stage1.json',
    2: 'recommendations.stage2.json',
    3: 'recommendations.stage3.json',
}
RESULT_NAME = 'result.json'
SESSION_NAME = 'session.json'

_PALETTE_ROLES = (
    'background',
    'secondary_bg',
    'primary',
    'accent',
    'secondary_accent',
    'body_text',
)
_TYPOGRAPHY_SIZE_ROLES = ('title', 'subtitle', 'annotation')
_HEX_COLOR_RE = re.compile(r'#?(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})\Z')

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
PUBLIC_HOST = '127.0.0.1'
STARTUP_TIMEOUT = 10

# Default --wait budget, kept just under the 600s Bash-tool ceiling so the
# parent (waiting) command returns before the calling harness kills it. The
# detached child server keeps running on its own --timeout idle budget, so a
# slow user can still confirm after the wait returns; the caller re-checks
# result.json before falling back to chat.
WAIT_TIMEOUT_DEFAULT = 590

def _read_json_object(path: Path, retries: int = 2, delay: float = 0.08) -> dict:
    """Read a JSON object, retrying briefly around non-atomic external writes."""
    last_error: Exception = ValueError('unknown JSON read error')
    for attempt in range(retries + 1):
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
            if isinstance(data, dict):
                return data
            raise ValueError(f'{path} top-level JSON value must be an object')
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay)
                continue
            raise last_error
    raise last_error


def _write_json_atomic(path: Path, data: dict) -> None:
    """Write a JSON object with replace semantics so waiters never see a partial file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    try:
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        os.replace(tmp, path)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def _server_url(port: int, path: str = '') -> str:
    """Return the loopback URL shown to users and used by readiness probes."""
    suffix = path if path.startswith('/') or not path else f'/{path}'
    return f'http://{PUBLIC_HOST}:{port}{suffix}'


def _wait_for_server_ready(
    port: int,
    proc: subprocess.Popen,
    timeout: int = STARTUP_TIMEOUT,
) -> bool:
    """Wait until the detached child is accepting HTTP requests."""
    deadline = time.time() + timeout
    last_error = ''
    health_url = _server_url(port, '/api/health')
    while time.time() < deadline:
        returncode = proc.poll()
        if returncode is not None:
            logger.error('confirm UI exited during startup (code=%s)', returncode)
            return False
        try:
            with urllib.request.urlopen(health_url, timeout=1) as resp:
                if 200 <= resp.status < 500:
                    return True
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        time.sleep(0.2)
    logger.error(
        'confirm UI did not become ready at %s within %ss%s',
        health_url,
        timeout,
        f' (last error: {last_error})' if last_error else '',
    )
    return False


def _launch_background_server(
    project_path: Path,
    *,
    preferred_port: int,
    idle_timeout: int,
    open_browser: bool,
) -> tuple[subprocess.Popen, int, Path]:
    """Start the confirm server child and wait until it is reachable."""
    confirm_dir = project_path / CONFIRM_DIR_NAME
    confirm_dir.mkdir(parents=True, exist_ok=True)
    log_path = confirm_dir / 'server.log'
    port = _find_free_port(preferred_port)
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
    with log_path.open('a', encoding='utf-8') as log:
        proc = _popen_detached(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            logger=logger,
        )
    logger.info('log: %s', log_path)
    if not _wait_for_server_ready(port, proc):
        raise RuntimeError(f'confirm UI failed to become reachable: {_server_url(port)}')
    _sync_session_state(confirm_dir, server_port=port, event='server-ready')
    url = _server_url(port)
    logger.info('started confirm UI in background: %s (pid=%s)', url, proc.pid)
    if open_browser:
        webbrowser.open(url)
    return proc, port, log_path


def _live_lock(lock_file: Path) -> Optional[dict]:
    """Return a live lock; stale entries are overwritten by the recovered child."""
    existing = _read_lock(lock_file)
    if not existing:
        return None
    if _process_alive(_lock_pid(existing)):
        return existing
    return None


def _preferred_recovery_port(lock_file: Path, fallback: int) -> int:
    """Prefer a stale lock's port so an already-open browser can reconnect."""
    existing = _read_lock(lock_file)
    try:
        port = int((existing or {}).get('port', 0) or 0)
    except (TypeError, ValueError):
        port = 0
    return port or fallback


def _open_browser_async(url: str, delay: float = 0.4) -> None:
    """Open the browser after Flask has had a moment to bind its socket."""
    def _open() -> None:
        time.sleep(delay)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


def _wait_for_result(
    result_file: Path,
    proc: subprocess.Popen,
    started_at: float,
    timeout: int,
    expected_stage: str,
) -> int:
    """Wait until this launch writes a fresh result file or the server exits."""
    logger.info('waiting for browser confirmation...')
    deadline = None if timeout <= 0 else time.time() + timeout
    while True:
        if result_file.exists():
            try:
                if result_file.stat().st_mtime >= started_at:
                    actual_stage = _result_stage(result_file)
                    if actual_stage != expected_stage:
                        logger.error(
                            'confirmation stage mismatch: expected %s, found %s',
                            expected_stage,
                            actual_stage or 'invalid/absent',
                        )
                        return 2
                    logger.info('confirmation received: %s', result_file)
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        pass
                    return 0
            except OSError:
                pass

        skip_error = _stage_skip_error(result_file.parent)
        if skip_error:
            logger.error('%s', skip_error)
            return 2

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
        data = _read_json_object(result_file)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    return _stage_key(data.get('stage'))


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
    """Return a recommendation payload's stage, with legacy tier fallback."""
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


def _stage_name(number: Optional[int]) -> Optional[str]:
    """Return the canonical stage key for a stage number."""
    if number == 1:
        return 'stage1'
    if number == 2:
        return 'stage2'
    if number == 3:
        return 'stage3'
    return None


def _result_stage_number(stage: Optional[str]) -> int:
    """Return result progression: stage1=1, stage2=2, final=4."""
    if stage == 'stage1':
        return 1
    if stage == 'stage2':
        return 2
    if stage == 'final':
        return 4
    return 0


def _expected_recommendation_stage(result_stage: Optional[str]) -> int:
    """Return the recommendation stage that follows the current result."""
    if result_stage == 'stage1':
        return 2
    if result_stage in {'stage2', 'final'}:
        return 3
    return 1


def _stage_recommendations_path(confirm_dir: Path, stage_number: int) -> Path:
    """Return the stage-specific recommendation path for one handoff."""
    return confirm_dir / RECOMMENDATION_STAGE_NAMES[stage_number]


def _active_recommendations_path(confirm_dir: Path) -> Path:
    """Resolve the recommendation file for the current confirmation stage.

    Once any stage-specific file exists, the legacy single-file input is ignored.
    If the expected stage is missing but a later stage exists, return that later
    file so the existing stage-skip guard can report the ordering error.
    """
    result_stage = _result_stage(confirm_dir / RESULT_NAME)
    expected_stage = _expected_recommendation_stage(result_stage)
    expected_file = _stage_recommendations_path(confirm_dir, expected_stage)
    staged_files = {
        stage_number: _stage_recommendations_path(confirm_dir, stage_number)
        for stage_number in RECOMMENDATION_STAGE_NAMES
    }
    if any(path.exists() for path in staged_files.values()):
        if expected_file.exists():
            return expected_file
        for stage_number in range(expected_stage + 1, 4):
            candidate = staged_files[stage_number]
            if candidate.exists():
                return candidate
        return expected_file

    legacy_file = confirm_dir / LEGACY_RECOMMENDATIONS_NAME
    return legacy_file if legacy_file.exists() else expected_file


def _read_active_recommendations(
    confirm_dir: Path,
    *,
    retries: int = 2,
) -> tuple[Path, dict]:
    """Read and validate the recommendation payload active for this stage."""
    rec_file = _active_recommendations_path(confirm_dir)
    data = _read_json_object(rec_file, retries=retries)
    for stage_number, filename in RECOMMENDATION_STAGE_NAMES.items():
        if rec_file.name != filename:
            continue
        actual_stage = _recommendation_stage(data)
        if actual_stage != stage_number:
            raise ValueError(
                f'{filename} must declare stage={_stage_name(stage_number)}, '
                f'found {_stage_name(actual_stage) or "absent"}'
            )
        break
    return rec_file, data


def _stage_skip(rec_stage_number: int, result_stage: Optional[str]) -> bool:
    """Detect a staged recommendation running ahead of the confirmed progression.

    Stages confirm strictly in order (stage1 → stage2 → stage3): a
    recommendation may only run one stage past the last confirmed result, so
    e.g. a ``stage3`` file while only stage 1 is confirmed is a skip — the
    page must not render it (an active template never exempts stage 2).
    Legacy single-pass recommendations (no ``stage``) are not staged and are
    exempt, as is any state after the final confirmation.
    """
    if rec_stage_number <= 1 or result_stage == 'final':
        return False
    return rec_stage_number > _result_stage_number(result_stage) + 1


def _stage_skip_error(confirm_dir: Path) -> Optional[str]:
    """Return a directive error when the active recommendation skips a stage."""
    try:
        rec_file, rec_data = _read_active_recommendations(confirm_dir)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    rec_stage_number = _recommendation_stage(rec_data)
    result_stage = _result_stage(confirm_dir / RESULT_NAME)
    if not _stage_skip(rec_stage_number, result_stage):
        return None
    expected = _stage_name(_result_stage_number(result_stage) + 1)
    reattach = (
        '--daemon --wait' if expected == 'stage1'
        else '--wait-only --wait-stage stage2'
    )
    expected_file = RECOMMENDATION_STAGE_NAMES[
        _expected_recommendation_stage(result_stage)
    ]
    return (
        f'stage skip detected: {rec_file.name} is {_stage_name(rec_stage_number)} but the last '
        f'confirmed result is {result_stage or "absent"} — the page will not render a skipped stage. '
        f'Stages confirm in order and an active template does not exempt stage2 (generate-pptx Step 4). '
        f'Write the missing {expected_file} recommendations, then re-run with {reattach}.'
    )


def _template_confirmation_required(project_path: Path, recommendations: dict) -> bool:
    """Return whether this project must use the staged template confirmation."""
    return (
        'template_application' in recommendations
        or (project_path / 'templates' / 'design_spec.md').is_file()
    )


def _template_stage2_error(
    recommendations: dict,
    *,
    template_required: bool,
) -> Optional[str]:
    """Require the natural-language template plan in template Stage 2."""
    if template_required and 'template_application' not in recommendations:
        return (
            'template Stage 2 recommendations must include '
            'template_application.value'
        )
    return None


def _localized_text_present(candidate: dict, field: str) -> bool:
    """Return whether a candidate carries non-empty localized prose."""
    return any(
        isinstance(candidate.get(key), str) and bool(candidate[key].strip())
        for key in (field, f'{field}_zh', f'{field}_en', f'{field}_ja')
    )


def _recommended_image_usage(recommendations: dict):
    """Return the Stage 2 image-source recommendation in either schema."""
    recommend = recommendations.get('recommend')
    usage = recommend.get('image_usage') if isinstance(recommend, dict) else None
    if usage is None:
        usage = recommendations.get('image_usage')
        if isinstance(usage, dict):
            usage = usage.get('value')
    return usage


def _uses_ai_images(recommendations: dict) -> bool:
    """Return whether Stage 2 proposes AI-generated images."""
    usage = _recommended_image_usage(recommendations)
    return 'ai' in usage if isinstance(usage, list) else usage == 'ai'


def _palette_error(color: object, label: str) -> Optional[str]:
    """Validate one complete user-facing palette."""
    if not isinstance(color, dict):
        return f'{label} must be an object'
    palette = color.get('palette')
    if not isinstance(palette, dict):
        palette = color
    for role in _PALETTE_ROLES:
        value = palette.get(role)
        if role == 'body_text' and value is None:
            value = palette.get('text')
        if not isinstance(value, str) or not _HEX_COLOR_RE.fullmatch(value.strip()):
            return f'{label}.palette.{role} must be a HEX color'
    return None


def _positive_number(value: object) -> bool:
    """Return whether a JSON value is a positive finite number."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number > 0 and number != float('inf')


def _typography_error(typography: object, label: str, *, require_sizes: bool) -> Optional[str]:
    """Validate one complete user-facing typography recommendation or choice."""
    if not isinstance(typography, dict):
        return f'{label} must be an object'
    for role in ('heading', 'body'):
        font = typography.get(role)
        if not isinstance(font, dict):
            return f'{label}.{role} must be an object'
        for field in ('cjk', 'latin', 'css'):
            if not isinstance(font.get(field), str) or not font[field].strip():
                return f'{label}.{role}.{field} must be non-empty'
    if not _positive_number(typography.get('body_size')):
        return f'{label}.body_size must be a positive number'
    if not require_sizes:
        return None
    sizes = typography.get('sizes')
    if not isinstance(sizes, dict):
        return f'{label}.sizes must be an object'
    for role in _TYPOGRAPHY_SIZE_ROLES:
        if not _positive_number(sizes.get(role)):
            return f'{label}.sizes.{role} must be a positive number'
    return None


def _candidate_list(spec: object) -> list:
    """Return candidates from the current or legacy recommendation shape."""
    if not isinstance(spec, dict):
        return []
    candidates = spec.get('candidates')
    if not isinstance(candidates, list):
        candidates = spec.get('options')
    return candidates if isinstance(candidates, list) else []


def _stage2_design_directions_error(recommendations: dict) -> Optional[str]:
    """Require three complete coordinated Stage 2 design systems."""
    directions = recommendations.get('design_directions')
    if isinstance(directions, dict):
        candidates = _candidate_list(directions)
        if len(candidates) < 3:
            return 'Stage 2 design_directions must include at least 3 candidates'
        for index, candidate in enumerate(candidates, start=1):
            label = f'design_directions.candidates[{index - 1}]'
            if not isinstance(candidate, dict):
                return f'{label} must be an object'
            if not _localized_text_present(candidate, 'name'):
                return f'{label} requires a non-empty localized name'
            for field in ('visual_style', 'icons'):
                if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                    return f'{label}.{field} must be non-empty'
            error = _palette_error(candidate.get('color'), f'{label}.color')
            if error:
                return error
            error = _typography_error(
                candidate.get('typography'),
                f'{label}.typography',
                require_sizes=False,
            )
            if error:
                return error
            if _uses_ai_images(recommendations):
                image_strategy = candidate.get('image_strategy')
                if not isinstance(image_strategy, dict) or not str(
                    image_strategy.get('rendering') or ''
                ).strip():
                    return f'{label}.image_strategy.rendering must be non-empty'
        return None

    # Legacy staged files remain readable, but they must still provide three
    # complete color combinations and at least one complete typography choice.
    colors = _candidate_list(recommendations.get('color'))
    if len(colors) < 3:
        return 'Stage 2 recommendations must include 3 complete color candidates'
    for index, color in enumerate(colors):
        error = _palette_error(color, f'color.candidates[{index}]')
        if error:
            return error
    typography = _candidate_list(recommendations.get('typography'))
    if not typography:
        return 'Stage 2 recommendations must include typography candidates'
    for index, candidate in enumerate(typography):
        error = _typography_error(
            candidate,
            f'typography.candidates[{index}]',
            require_sizes=False,
        )
        if error:
            return error
    return None


def _stage2_custom_candidates_error(recommendations: dict) -> Optional[str]:
    """Require visible AI-authored custom alternatives in new Stage 2 files."""
    candidates = recommendations.get('custom_candidates')
    if not isinstance(candidates, dict):
        return 'Stage 2 recommendations must include custom_candidates'

    for field in ('mode', 'visual_style'):
        candidate = candidates.get(field)
        if not isinstance(candidate, dict):
            return f'custom_candidates.{field} must be an object'
        for prose_field in ('name', 'behavior'):
            if not _localized_text_present(candidate, prose_field):
                return (
                    f'custom_candidates.{field} requires non-empty localized '
                    f'{prose_field}'
                )

    if not _uses_ai_images(recommendations):
        return None

    image_candidate = candidates.get('image_strategy')
    if not isinstance(image_candidate, dict):
        return 'custom_candidates.image_strategy must be an object when image_usage includes ai'
    if image_candidate.get('rendering') != 'custom':
        return 'custom_candidates.image_strategy.rendering must be custom'
    for prose_field in ('name', 'visual', 'mood', 'behavior'):
        if not _localized_text_present(image_candidate, prose_field):
            return (
                'custom_candidates.image_strategy requires non-empty localized '
                f'{prose_field}'
            )
    return None


def _submission_stage_error(
    project_path: Path,
    confirm_dir: Path,
    submitted_stage: Optional[str],
) -> Optional[str]:
    """Reject a confirmation that does not match the staged recommendation."""
    try:
        rec_file, recommendations = _read_active_recommendations(confirm_dir)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f'cannot confirm without valid current recommendations: {exc}'

    rec_stage_number = _recommendation_stage(recommendations)
    template_required = _template_confirmation_required(
        project_path,
        recommendations,
    )
    if rec_stage_number == 0:
        if template_required:
            return (
                'an installed template requires the Stage 1 → Stage 2 → Stage 3 '
                'flow; legacy single-pass confirmation is not allowed'
            )
        if submitted_stage not in {None, 'stage3', 'final'}:
            return 'legacy single-pass recommendations accept only a final submission'
        return None

    if rec_stage_number == 2:
        recommendation_error = _template_stage2_error(
            recommendations,
            template_required=template_required,
        )
        if recommendation_error:
            return recommendation_error
        recommendation_error = _stage2_custom_candidates_error(recommendations)
        if recommendation_error:
            return recommendation_error
        recommendation_error = _stage2_design_directions_error(recommendations)
        if recommendation_error:
            return recommendation_error

    allowed_submissions = {
        1: {'stage1'},
        2: {'stage2'},
        3: {'stage3', 'final'},
    }
    if submitted_stage not in allowed_submissions[rec_stage_number]:
        expected = 'final' if rec_stage_number == 3 else _stage_name(rec_stage_number)
        return (
            f'confirmation stage mismatch: {rec_file.name} is '
            f'{_stage_name(rec_stage_number)}, so the submitted stage must be '
            f'{expected}'
        )

    previous_stage = _result_stage(confirm_dir / RESULT_NAME)
    allowed_predecessors = {
        1: {None, 'stage1', 'stage2', 'final'},
        2: {'stage1', 'stage2'},
        3: {'stage2', 'final'},
    }
    if previous_stage not in allowed_predecessors[rec_stage_number]:
        expected_previous = 'stage1' if rec_stage_number == 2 else 'stage2'
        return (
            f'confirmation predecessor mismatch: {_stage_name(rec_stage_number)} '
            f'requires a confirmed {expected_previous} result, found '
            f'{previous_stage or "absent"}'
        )
    return None


def _custom_selection_error(result: dict) -> Optional[str]:
    """Require behavior prose whenever a creative custom choice is selected."""
    if result.get('mode') == 'custom' and not str(
        result.get('mode_behavior') or ''
    ).strip():
        return 'mode=custom requires non-empty mode_behavior'
    if result.get('visual_style') == 'custom' and not str(
        result.get('visual_style_behavior') or ''
    ).strip():
        return 'visual_style=custom requires non-empty visual_style_behavior'
    image_strategy = result.get('image_strategy')
    if isinstance(image_strategy, dict) and image_strategy.get('rendering') == 'custom':
        behavior = image_strategy.get('behavior') or image_strategy.get('custom')
        if not str(behavior or '').strip():
            return 'image_strategy.rendering=custom requires non-empty behavior'
    return None


def _stage2_solution_error(result: dict) -> Optional[str]:
    """Reject a Stage 2/final payload with an incomplete design system."""
    color = result.get('color')
    color_error = _palette_error(color, 'color')
    color_custom = (
        isinstance(color, dict)
        and color.get('name') == 'custom'
        and str(color.get('custom') or '').strip()
    )
    if color_error and not color_custom:
        return color_error

    typography = result.get('typography')
    typography_error = _typography_error(
        typography,
        'typography',
        require_sizes=True,
    )
    typography_custom = (
        isinstance(typography, dict)
        and typography.get('name') == 'custom'
        and str(typography.get('custom') or '').strip()
        and _positive_number(typography.get('body_size'))
        and isinstance(typography.get('sizes'), dict)
        and all(
            _positive_number(typography['sizes'].get(role))
            for role in _TYPOGRAPHY_SIZE_ROLES
        )
    )
    if typography_error and not typography_custom:
        return typography_error
    return None


def _normalize_custom_selections(result: dict) -> None:
    """Keep custom prose only for the creative choices actually selected."""
    if result.get('mode') != 'custom':
        result.pop('mode_behavior', None)
    if result.get('visual_style') != 'custom':
        result.pop('visual_style_behavior', None)

    image_strategy = result.get('image_strategy')
    if not isinstance(image_strategy, dict):
        return
    legacy_behavior = image_strategy.pop('custom', None)
    if image_strategy.get('rendering') == 'custom':
        if not image_strategy.get('behavior') and legacy_behavior:
            image_strategy['behavior'] = legacy_behavior
        return
    image_strategy.pop('behavior', None)


def _expected_result_stage(confirm_dir: Path) -> str:
    """Return the result stage expected from the current recommendations."""
    try:
        _, recommendations = _read_active_recommendations(confirm_dir)
    except (OSError, json.JSONDecodeError, ValueError):
        return 'final'
    return {
        1: 'stage1',
        2: 'stage2',
        3: 'final',
    }.get(_recommendation_stage(recommendations), 'final')


def _file_version(path: Path) -> Optional[float]:
    """Return a cheap file version for polling state, or None when absent."""
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _read_session(confirm_dir: Path) -> dict:
    """Read session.json if present, returning an object."""
    session_file = confirm_dir / SESSION_NAME
    if not session_file.exists():
        return {}
    try:
        return _read_json_object(session_file)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def _build_session_state(
    confirm_dir: Path,
    *,
    server_port: Optional[int] = None,
    event: Optional[str] = None,
) -> dict:
    """Derive the resumable Confirm UI state from disk artifacts."""
    previous = _read_session(confirm_dir)
    rec_file = _active_recommendations_path(confirm_dir)
    result_file = confirm_dir / RESULT_NAME

    rec_stage_number = 0
    rec_stage = None
    rec_error = None
    if rec_file.exists():
        try:
            rec_file, rec_data = _read_active_recommendations(confirm_dir)
            rec_stage_number = _recommendation_stage(rec_data)
            rec_stage = _stage_name(rec_stage_number)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            rec_error = str(exc)

    result_stage = _result_stage(result_file)
    result_stage_number = _result_stage_number(result_stage)
    stage_skip = _stage_skip(rec_stage_number, result_stage)

    # A skipped stage is never presented: the page keeps its "deriving…" state
    # (waiting_agent) until the AI creates the missing stage file.
    if result_stage == 'final':
        expected_stage_number = None
        status = 'done'
        current_stage = 'final'
    elif result_stage == 'stage2':
        expected_stage_number = 3
        status = 'ready_user' if rec_stage_number >= 3 else 'waiting_agent'
        current_stage = _stage_name(rec_stage_number) if rec_stage_number >= 3 else 'stage2'
    elif result_stage == 'stage1':
        expected_stage_number = 2
        ready = rec_stage_number >= 2 and not stage_skip
        status = 'ready_user' if ready else 'waiting_agent'
        current_stage = _stage_name(rec_stage_number) if ready else 'stage1'
    else:
        expected_stage_number = 1 if stage_skip else (rec_stage_number or 1)
        ready = bool(rec_stage_number) and not stage_skip
        status = 'ready_user' if ready else 'waiting_agent'
        current_stage = rec_stage if ready else 'stage1'

    return {
        'session_id': previous.get('session_id') or uuid.uuid4().hex,
        'status': status,
        'current_stage': current_stage,
        'stage_skip': stage_skip,
        'expected_stage': _stage_name(expected_stage_number),
        'expected_stage_number': expected_stage_number,
        'recommendation_stage': rec_stage,
        'recommendation_stage_number': rec_stage_number,
        'recommendation_file': rec_file.name,
        'recommendation_version': _file_version(rec_file),
        'recommendation_error': rec_error,
        'result_stage': result_stage,
        'result_stage_number': result_stage_number,
        'result_version': _file_version(result_file),
        'server_port': server_port or previous.get('server_port'),
        'event': event or previous.get('event') or 'derived',
    }


def _write_session_state(confirm_dir: Path, session: dict) -> None:
    """Persist session.json only when stable state changes."""
    previous = _read_session(confirm_dir)
    comparable_previous = dict(previous)
    comparable_current = dict(session)
    comparable_previous.pop('updated_at', None)
    comparable_current.pop('updated_at', None)
    if comparable_previous == comparable_current:
        return
    session = dict(session)
    session['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    _write_json_atomic(confirm_dir / SESSION_NAME, session)


def _sync_session_state(
    confirm_dir: Path,
    *,
    server_port: Optional[int] = None,
    event: Optional[str] = None,
) -> dict:
    """Derive and persist the current session state."""
    session = _build_session_state(
        confirm_dir,
        server_port=server_port,
        event=event,
    )
    _write_session_state(confirm_dir, session)
    return session


# Earlier-stage choices are not rendered on later pages, so their values live
# only in browser STATE and would be lost on refresh. Fold them from result.json
# into the served recommendations so a refresh / reopen resumes from the user's
# actual communication contract and complete deck-solution choices.
_CONTRACT_RECOMMEND_KEYS = (
    'canvas',
)
_CONTRACT_VALUE_KEYS = (
    'audience',
    'communication_intent',
    'audience_outcome',
    'core_message',
    'delivery_context',
    'artifact_afterlife',
    'content_divergence',
)
_DECK_DIRECTION_RECOMMEND_KEYS = (
    'delivery_purpose',
    'mode',
    'visual_style',
    'icons',
    'image_usage',
)
_PRODUCTION_RECOMMEND_KEYS = (
    'formula_policy',
    'image_ai_path',
    'generation_mode',
)
_LOCKED_RECOMMENDATIONS_KEY = '_locked_recommendations'


def _merge_confirmed_choices(data: dict, result_file: Path) -> None:
    """Fold already-confirmed choices into later-stage recommendations."""
    try:
        res = _read_json_object(result_file)
    except (OSError, json.JSONDecodeError, ValueError):
        return
    recommend = data.setdefault('recommend', {})
    if not isinstance(recommend, dict):
        recommend = data['recommend'] = {}
    for key in _CONTRACT_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    for key in _CONTRACT_VALUE_KEYS:
        if key in res:
            data[key] = {'value': res.get(key) or ''}
    if _recommendation_stage(data) < 3:
        return
    for key in _DECK_DIRECTION_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    if 'page_count' in res:
        data['page_count'] = {'value': res.get('page_count') or ''}
    if 'image_notes' in res:
        data['image_notes'] = {'value': res.get('image_notes') or ''}
    if 'template_application' in res:
        data['template_application'] = {
            'value': res.get('template_application') or '',
        }
    if isinstance(res.get('color'), dict):
        data['color'] = {'selected': 0, 'candidates': [res['color']]}
    if isinstance(res.get('typography'), dict):
        data['typography'] = {'selected': 0, 'candidates': [res['typography']]}
    if isinstance(res.get('image_strategy'), dict):
        data['image_strategy'] = {
            'selected': 0,
            'candidates': [res['image_strategy']],
        }
    custom_candidates = data.get('custom_candidates')
    if not isinstance(custom_candidates, dict):
        custom_candidates = {}
        data['custom_candidates'] = custom_candidates
    for field, behavior_field in (
        ('mode', 'mode_behavior'),
        ('visual_style', 'visual_style_behavior'),
    ):
        behavior = res.get(behavior_field)
        if res.get(field) != 'custom' or not str(behavior or '').strip():
            continue
        candidate = custom_candidates.get(field)
        if not isinstance(candidate, dict):
            candidate = {}
        candidate['behavior'] = behavior
        custom_candidates[field] = candidate
    image_strategy = res.get('image_strategy')
    if isinstance(image_strategy, dict) and image_strategy.get('rendering') == 'custom':
        custom_candidates['image_strategy'] = image_strategy
    # Stage 3 must retain its own production recommendations until final
    # confirmation. A final-result reopen reflects those confirmed mechanics.
    # Legacy single-pass results have no stage but do carry status=confirmed.
    result_stage = _stage_key(res.get('stage'))
    is_final = result_stage == 'final' or (
        result_stage is None and res.get('status') == 'confirmed'
    )
    if not is_final:
        return
    for key in _PRODUCTION_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    if 'refine_spec' in res:
        data['refine_spec'] = {'value': bool(res.get('refine_spec'))}


def _apply_locked_recommendations(
    result: dict,
    recommendations_file: Path,
    previous_result_file: Path,
) -> dict:
    """Restore profile-locked fields and return locks for staged carry-over."""
    # This marker is server-owned; never accept a client-supplied carry-over map.
    result.pop(_LOCKED_RECOMMENDATIONS_KEY, None)
    locked_values = {}
    try:
        previous = _read_json_object(previous_result_file)
    except (OSError, json.JSONDecodeError, ValueError):
        previous = {}
    previous_locks = previous.get(_LOCKED_RECOMMENDATIONS_KEY)
    if isinstance(previous_locks, dict):
        locked_values.update(previous_locks)

    try:
        recommendations = _read_json_object(recommendations_file)
        recommendations_loaded = True
    except (OSError, json.JSONDecodeError, ValueError):
        recommendations = {}
        recommendations_loaded = False

    # Stage 1 starts a new contract and therefore replaces any stale locks left
    # by an earlier run. Later stages inherit those locks across server restarts.
    if (
        recommendations_loaded
        and _recommendation_stage(recommendations) in {0, 1}
    ):
        locked_values = {}
    for key, field in recommendations.items():
        if not isinstance(field, dict) or field.get('locked') is not True:
            continue
        if 'value' in field:
            locked_values[key] = field.get('value') or ''
    for key, value in locked_values.items():
        result[key] = value
    return locked_values


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
        current_stage = _result_stage(result_file)
        if current_stage == target_stage:
            logger.info('confirmation stage=%s received: %s', target_stage, result_file)
            return 0
        if _result_stage_number(current_stage) > _result_stage_number(target_stage):
            logger.error(
                'confirmation skipped expected stage=%s and advanced to %s',
                target_stage,
                current_stage,
            )
            return 2

        skip_error = _stage_skip_error(result_file.parent)
        if skip_error:
            logger.error('%s', skip_error)
            return 2

        lock = _read_lock(lock_file)
        pid = _lock_pid(lock)
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
    pid = _lock_pid(existing)
    port = existing.get('port')
    if not _process_alive(pid):
        _clear_lock(lock_file)
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
    _clear_lock(lock_file)
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
    }


# --- app --------------------------------------------------------------------

def create_app(
    project_dir: str,
    idle_timeout: int = 900,
    lock_file: Optional[Path] = None,
    server_port: Optional[int] = None,
) -> Flask:
    """Create and configure the Flask app for a given project directory."""
    project_path = Path(project_dir).resolve()
    confirm_dir = project_path / CONFIRM_DIR_NAME

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config['PROJECT_PATH'] = project_path
    app.config['CONFIRM_DIR'] = confirm_dir
    app.config['LOCK_FILE'] = lock_file
    app.config['SERVER_PORT'] = server_port
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

    @app.route('/api/health')
    def health():
        """Expose a cheap readiness probe for the daemon launcher."""
        rec_file = _active_recommendations_path(confirm_dir)
        rec_ok = False
        stage = None
        if rec_file.exists():
            try:
                rec_file, rec_data = _read_active_recommendations(
                    confirm_dir,
                    retries=0,
                )
                rec_ok = True
                stage = _recommendation_stage(rec_data)
            except (OSError, json.JSONDecodeError, ValueError):
                rec_ok = False
        resp = jsonify({
            'status': 'ok',
            'project': str(project_path),
            'recommendations': rec_ok,
            'stage': stage,
            'session': _build_session_state(
                confirm_dir,
                server_port=app.config.get('SERVER_PORT'),
            ),
        })
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.route('/api/session')
    def get_session():
        """Expose the derived three-stage wizard state for browser polling."""
        session = _sync_session_state(
            confirm_dir,
            server_port=app.config.get('SERVER_PORT'),
            event='poll',
        )
        resp = jsonify(session)
        resp.headers['Cache-Control'] = 'no-store'
        return resp

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
        """Serve generated-image rendering references for the current UI."""
        try:
            resp = jsonify(_build_ai_image_comparison())
            resp.headers['Cache-Control'] = 'no-store'
            return resp
        except (OSError, json.JSONDecodeError) as exc:
            return jsonify({'error': f'invalid ai-image-comparison manifest: {exc}'}), 500

    @app.route('/ai-image-comparison/<kind>/<filename>')
    def get_ai_image_comparison(kind: str, filename: str):
        """Serve rendering images for generated-image strategy candidates."""
        if kind != 'rendering':
            return jsonify({'error': 'invalid comparison kind'}), 404
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.png', filename or ''):
            return jsonify({'error': 'invalid comparison filename'}), 404
        return send_from_directory(_AI_IMAGE_COMPARISON_DIR / kind, filename)

    @app.route('/api/recommendations')
    def get_recommendations():
        """Serve the Strategist-authored recommendations for this project."""
        rec_file = _active_recommendations_path(confirm_dir)
        if not rec_file.exists():
            return jsonify({'error': f'{rec_file.name} not found'}), 404
        try:
            rec_file, data = _read_active_recommendations(confirm_dir)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return jsonify({
                'error': f'invalid current recommendation file: {exc}',
            }), 400
        # Report whether a result already exists (re-open after confirm).
        result_file = confirm_dir / RESULT_NAME
        if _stage_skip(
            _recommendation_stage(data),
            _result_stage(result_file),
        ):
            return jsonify({
                'error': _stage_skip_error(confirm_dir),
            }), 409
        data['_already_confirmed'] = result_file.exists()
        # Later stages render only downstream sections, so fold earlier confirmed
        # choices from result.json back in. A refresh / reopen then re-inits from
        # the user's choices instead of catalog defaults.
        rec_stage_number = _recommendation_stage(data)
        if rec_stage_number >= 2 and result_file.exists():
            _merge_confirmed_choices(data, result_file)
        if rec_stage_number == 2:
            recommendation_error = _template_stage2_error(
                data,
                template_required=_template_confirmation_required(
                    project_path,
                    data,
                ),
            )
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
            recommendation_error = _stage2_custom_candidates_error(data)
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
            recommendation_error = _stage2_design_directions_error(data)
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
        # Template application is authored by Strategist from the installed
        # workspace and current content. Never expose legacy mode fields as
        # user-facing confirmation controls.
        recommend = data.get('recommend')
        if isinstance(recommend, dict):
            recommend.pop('template_reuse_scope', None)
            recommend.pop('template_adherence', None)
        data.pop('template_reuse_scope', None)
        data.pop('template_adherence', None)
        # The page polls this endpoint after each confirmation until the AI
        # creates the next stage file, so it must never be cached.
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
        result_file = confirm_dir / RESULT_NAME
        raw_stage = result.get('stage')
        stage = _stage_key(raw_stage)
        if raw_stage is not None and stage is None:
            return jsonify({'error': 'invalid confirmation stage'}), 400
        stage_error = _submission_stage_error(
            project_path,
            confirm_dir,
            stage,
        )
        if stage_error:
            return jsonify({'error': stage_error}), 409
        custom_error = _custom_selection_error(result)
        if custom_error:
            return jsonify({'error': custom_error}), 400
        try:
            rec_file, current_recommendations = _read_active_recommendations(
                confirm_dir,
            )
        except (OSError, json.JSONDecodeError, ValueError):
            rec_file = _active_recommendations_path(confirm_dir)
            current_recommendations = {}
        if stage == 'stage2' or _recommendation_stage(current_recommendations) == 3:
            solution_error = _stage2_solution_error(result)
            if solution_error:
                return jsonify({'error': solution_error}), 400
        _normalize_custom_selections(result)
        locked_values = _apply_locked_recommendations(
            result,
            rec_file,
            result_file,
        )
        result.pop('template_reuse_scope', None)
        result.pop('template_adherence', None)
        # Staged flow: Stage 1 / Stage 2 submits record intermediate choices but do
        # NOT close the page. Only a final submit is a full confirmation. A
        # payload with no stage is a legacy free-design single-pass confirmation.
        if stage in {'stage1', 'stage2'}:
            result['stage'] = stage
            result['status'] = f'{stage}-confirmed'
            if locked_values:
                result[_LOCKED_RECOMMENDATIONS_KEY] = locked_values
        else:
            result.pop(_LOCKED_RECOMMENDATIONS_KEY, None)
            result['stage'] = 'final'
            result['status'] = 'confirmed'
        result['confirmed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        _write_json_atomic(result_file, result)
        _sync_session_state(
            confirm_dir,
            server_port=app.config.get('SERVER_PORT'),
            event=f'{result["stage"]}-submitted',
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
        '--daemon', action='store_true',
        help='Start the server in the background; combine with --wait to block until confirmation',
    )
    parser.add_argument(
        '--wait', action='store_true',
        help='With --daemon, wait until a fresh result.json is written',
    )
    parser.add_argument(
        '--wait-only', action='store_true',
        help='Attach to the confirm server for this project and wait for an '
             'already-open page to write result.json. If the server died, '
             'recover it on the recorded/default port so browser polling can resume.',
    )
    parser.add_argument(
        '--wait-stage', default='final', metavar='{stage2,final}',
        help='With --wait-only, wait for this result.json stage (default: final). '
             'Use stage2 for the direction handoff in the three-stage flow.',
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
    # recommendation files (the page may never have been confirmed).
    if args.shutdown:
        return _shutdown_existing(project_path / LOCK_FILE_NAME)

    # Staged wait: attach to the server launched by the first --wait and block
    # until the page writes the requested intermediate or final result.json.
    if args.wait_only:
        lock_file = project_path / LOCK_FILE_NAME
        if not _live_lock(lock_file):
            confirm_dir = project_path / CONFIRM_DIR_NAME
            rec_file = _active_recommendations_path(confirm_dir)
            if not rec_file.exists():
                logger.error(
                    '%s not found — cannot recover confirm UI before wait-only',
                    rec_file,
                )
                return 1
            recovery_port = _preferred_recovery_port(lock_file, args.port)
            try:
                _, actual_port, _ = _launch_background_server(
                    project_path,
                    preferred_port=recovery_port,
                    idle_timeout=args.timeout,
                    open_browser=False,
                )
            except RuntimeError as exc:
                logger.error('%s', exc)
                return 1
            if actual_port != recovery_port and not args.no_browser:
                webbrowser.open(_server_url(actual_port))
            logger.info(
                'recovered confirm UI for wait-only at %s; the browser polling should resume',
                _server_url(actual_port),
            )
        return _wait_only_for_result(
            project_path / CONFIRM_DIR_NAME / RESULT_NAME,
            lock_file,
            args.wait_timeout,
            wait_stage,
        )

    confirm_dir = project_path / CONFIRM_DIR_NAME
    rec_file = _active_recommendations_path(confirm_dir)
    if not rec_file.exists():
        logger.error(
            '%s not found — Strategist must write the current recommendation stage before launch',
            rec_file,
        )
        return 1

    if args.daemon:
        lock_file = project_path / LOCK_FILE_NAME
        existing = _read_lock(lock_file)
        if existing and _process_alive(_lock_pid(existing)):
            existing_pid = existing.get('pid', '?')
            existing_port = existing.get('port', '?')
            logger.error(
                'confirm UI is already running for this project '
                '(pid=%s, port=%s). Open http://%s:%s',
                existing_pid, existing_port, PUBLIC_HOST, existing_port,
            )
            return 1

        confirm_dir = project_path / CONFIRM_DIR_NAME
        result_file = confirm_dir / RESULT_NAME
        expected_stage = _expected_result_stage(confirm_dir)
        started_at = time.time()
        try:
            proc, port, _ = _launch_background_server(
                project_path,
                preferred_port=args.port,
                idle_timeout=args.timeout,
                open_browser=not args.no_browser,
            )
        except RuntimeError as exc:
            logger.error('%s', exc)
            return 1
        if args.wait:
            return _wait_for_result(
                result_file,
                proc,
                started_at,
                args.wait_timeout,
                expected_stage,
            )
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
            '(pid=%s, port=%s). Open http://%s:%s, or run: kill %s',
            existing_pid, existing_port, PUBLIC_HOST, existing_port, existing_pid,
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
        server_port=args.port,
    )

    url = _server_url(args.port)
    if not args.no_browser:
        _open_browser_async(url)

    logger.info('running at %s', url)
    logger.info('project: %s', project_path)
    logger.info('idle timeout: %ds (0 = disabled)', args.timeout)
    app.run(host=PUBLIC_HOST, port=args.port, debug=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
