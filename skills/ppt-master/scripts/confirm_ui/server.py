#!/usr/bin/env python3
"""
PPT Master - Template and Strategist confirmation UI Server (Steps 3-4)

Lightweight Flask backend for the Default template choice and interactive
Strategist confirmation page. Stage 1 combines template selection with the
communication contract; its submit writes ``template_selection.json`` and the
stage1-confirmed ``result.json`` in one request. After the agent applies the
choice and completes ``template_handoff.json``, final Stage 2 confirms the deck
solution and production plan.

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
    python3 scripts/confirm_ui/server.py projects/my-project --daemon
    python3 scripts/confirm_ui/server.py projects/my-project --wait-only --wait-stage stage1
    python3 scripts/confirm_ui/server.py projects/my-project --complete-template-selection
    python3 scripts/confirm_ui/server.py projects/my-project --reset-template-selection

Dependencies:
    flask>=3.0.0
"""

import argparse
import atexit
import hashlib
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
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

# Local — sys.path injection for sibling module (code-style.md §3)
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from language_tags import (  # noqa: E402
    LanguageTagError,
    language_base,
    normalize_language_tag,
)
from server_common import (  # noqa: E402
    claim_lock as _claim_lock,
    clear_lock as _clear_lock,
    find_free_port as _find_free_port,
    lock_pid as _lock_pid,
    popen_detached as _popen_detached,
    process_alive as _process_alive,
    read_lock as _read_lock,
    release_lock as _release_lock,
    validate_port as _validate_port,
)

configure_utf8_stdio()

logger = logging.getLogger('confirm_ui')

# Per-project lock file. Lives at <project_path>/.confirm_ui.lock and matches
# the *.lock entry already in the repo .gitignore. Independent of the live
# preview lock so the two surfaces never collide.
LOCK_FILE_NAME = '.confirm_ui.lock'

# Round-trip/session files, all under <project_path>/confirm_ui/.
CONFIRM_DIR_NAME = 'confirm_ui'
RECOMMENDATION_STAGE_NAMES = {
    1: 'recommendations.stage1.json',
    2: 'recommendations.stage2.json',
}
RESULT_NAME = 'result.json'
SESSION_NAME = 'session.json'
TEMPLATE_OPTIONS_NAME = 'template_options.json'
TEMPLATE_SELECTION_NAME = 'template_selection.json'
TEMPLATE_HANDOFF_NAME = 'template_handoff.json'
TEMPLATE_SCHEMA_VERSION = 1

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
_SKILL_DIR = Path(__file__).resolve().parents[2]
_TEMPLATES_DIR = _SKILL_DIR / 'templates'
_CATALOGS_PATH = Path(__file__).resolve().parent / 'static' / 'catalogs.json'
_ICON_LIBRARY_DIR = _TEMPLATES_DIR / 'icons'
_AI_IMAGE_COMPARISON_DIR = _SKILL_DIR / 'references' / 'ai-image-comparison'
_TEMPLATE_LIBRARY_CONFIG = {
    'brand': ('brands', 'brands_index.json'),
    'style': ('styles', 'styles_index.json'),
    'layout': ('layouts', 'layouts_index.json'),
    'deck': ('decks', 'decks_index.json'),
}
_TEMPLATE_KIND_LINE_RE = re.compile(
    r'''kind\s*:\s*(?:'([^']*)'|"([^"]*)"|([A-Za-z][A-Za-z0-9_-]*))'''
    r'''\s*(?:#.*)?\Z'''
)
_ICON_PREVIEW_SAMPLES = {
    'chunk-filled': ('home', 'chart-line', 'users', 'target'),
    'tabler-filled': ('home', 'chart-dots', 'user', 'bulb'),
    'tabler-outline': ('home', 'chart-line', 'users', 'bulb'),
    'phosphor-duotone': ('house', 'chart-line', 'users', 'target'),
}

# Keep the long-standing Confirm UI entry port. Live preview uses a separate
# base range so stale preview tabs cannot address a later Confirm UI process.
# Concurrent Confirm UI sessions advance while explicit ``--port`` remains exact.
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


def _json_sha256(data: object) -> str:
    """Return a stable SHA-256 over one JSON-compatible value."""
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    )
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _safe_template_id(template_id: object) -> bool:
    """Return whether an index key is one safe directory-segment id."""
    return (
        isinstance(template_id, str)
        and re.fullmatch(r'\w[\w.-]*', template_id) is not None
    )


_TEMPLATE_SPEC_NAME_RE = re.compile(
    r'design_spec\.(?P<kind>brand|style|layout|deck)\.(?P<id>[^/\\]+)\.md'
)


def _template_design_specs(workspace_root: Path) -> list[Path]:
    """Return every Design Spec one template workspace root exposes.

    A single-kind workspace keeps the exact ``templates/design_spec.md``, and a
    compatible legacy-flat root keeps ``design_spec.md`` beside its pages. A
    multi-kind workspace keeps one ``templates/design_spec.<kind>.<id>.md`` per
    kind — the same shape the apply stage installs into a consuming project — so
    one root can carry, for example, a Brand plus a Style. Order is stable so
    candidate keys and the options digest do not depend on directory listing
    order.
    """
    templates_dir = workspace_root / 'templates'
    current = templates_dir / 'design_spec.md'
    multi = sorted(
        path
        for path in templates_dir.glob('design_spec.*.md')
        if _TEMPLATE_SPEC_NAME_RE.fullmatch(path.name)
    ) if templates_dir.is_dir() else []
    if current.is_file() and multi:
        raise ValueError(
            'template workspace mixes design_spec.md with kind-qualified specs '
            f'({", ".join(path.name for path in multi)}): {workspace_root}; '
            'rename the bare spec to design_spec.<kind>.<id>.md'
        )
    if current.is_file():
        return [current]
    if multi:
        return multi
    legacy = workspace_root / 'design_spec.md'
    if legacy.is_file():
        return [legacy]
    raise ValueError(
        'template workspace is missing templates/design_spec.md, '
        'templates/design_spec.<kind>.<id>.md, or legacy design_spec.md: '
        f'{workspace_root}'
    )


def _template_kind_from_spec(spec_path: Path) -> str:
    """Read one supported top-level ``kind`` from Design Spec frontmatter.

    Frontmatter stays the single truth. When the filename also carries a kind,
    both its kind and id must agree; a mismatch is a corrupt workspace rather
    than a precedence question.
    """
    name_match = _TEMPLATE_SPEC_NAME_RE.fullmatch(spec_path.name)
    if name_match is not None:
        try:
            from register_template import (
                SpecParseError,
                validate_qualified_spec_identity,
            )
            declared_kind, _filename_id, _frontmatter, _body = (
                validate_qualified_spec_identity(spec_path)
            )
        except ImportError as exc:
            raise ValueError(
                f'Qualified Design Spec validator could not be imported: {exc}'
            ) from exc
        except (OSError, SpecParseError) as exc:
            raise ValueError(str(exc)) from exc
        return declared_kind

    try:
        lines = spec_path.read_text(encoding='utf-8-sig').splitlines()
    except OSError as exc:
        raise ValueError(f'cannot read template Design Spec {spec_path}: {exc}') from exc
    if not lines or lines[0] != '---':
        raise ValueError(f'{spec_path} must start with YAML frontmatter')
    try:
        frontmatter_end = lines.index('---', 1)
    except ValueError as exc:
        raise ValueError(f'{spec_path} has unterminated YAML frontmatter') from exc

    declared_kind = None
    for line_number, line in enumerate(lines[1:frontmatter_end], start=2):
        if re.match(r'^\s*kind\s*:', line) is None:
            continue
        if line != line.lstrip():
            raise ValueError(
                f'{spec_path}:{line_number} kind must be a top-level frontmatter field'
            )
        match = _TEMPLATE_KIND_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(
                f'{spec_path}:{line_number} has an invalid kind declaration'
            )
        if declared_kind is not None:
            raise ValueError(f'{spec_path} frontmatter declares kind more than once')
        declared_kind = next(value for value in match.groups() if value is not None)

    if declared_kind is None:
        raise ValueError(f'{spec_path} frontmatter must declare kind')
    if declared_kind not in _TEMPLATE_LIBRARY_CONFIG:
        supported = ', '.join(_TEMPLATE_LIBRARY_CONFIG)
        raise ValueError(
            f'{spec_path} frontmatter kind must be one of {supported}; '
            f'got {declared_kind!r}'
        )
    return declared_kind


def _read_template_options_input(confirm_dir: Path) -> tuple[dict, list[Path]]:
    """Read and validate the agent-authored Step-3 template input."""
    options_file = confirm_dir / TEMPLATE_OPTIONS_NAME
    data = _read_json_object(options_file)
    if type(data.get('schema_version')) is not int or data['schema_version'] != TEMPLATE_SCHEMA_VERSION:
        raise ValueError(
            f'{TEMPLATE_OPTIONS_NAME} schema_version must be {TEMPLATE_SCHEMA_VERSION}'
        )
    if data.get('phase') != 'template':
        raise ValueError(f'{TEMPLATE_OPTIONS_NAME} phase must be template')
    if data.get('default_mode') not in {'free_design', 'templates'}:
        raise ValueError(
            f'{TEMPLATE_OPTIONS_NAME} default_mode must be free_design or templates'
        )
    if 'lang' in data and (
        not isinstance(data['lang'], str) or not data['lang'].strip()
    ):
        raise ValueError(f'{TEMPLATE_OPTIONS_NAME} lang must be a non-empty string')
    if 'explicit_workspace_roots' not in data:
        raise ValueError(
            f'{TEMPLATE_OPTIONS_NAME} must include explicit_workspace_roots'
        )
    raw_roots = data['explicit_workspace_roots']
    if not isinstance(raw_roots, list):
        raise ValueError(
            f'{TEMPLATE_OPTIONS_NAME} explicit_workspace_roots must be an array'
        )
    if raw_roots and data['default_mode'] != 'templates':
        raise ValueError(
            f'{TEMPLATE_OPTIONS_NAME} default_mode must be templates when '
            'explicit_workspace_roots is non-empty'
        )

    roots = []
    seen = set()
    for index, raw_root in enumerate(raw_roots):
        if not isinstance(raw_root, str) or not raw_root.strip():
            raise ValueError(
                f'{TEMPLATE_OPTIONS_NAME} explicit_workspace_roots[{index}] '
                'must be a non-empty string'
            )
        candidate = Path(raw_root)
        if not candidate.is_absolute():
            raise ValueError(
                f'{TEMPLATE_OPTIONS_NAME} explicit_workspace_roots[{index}] '
                'must be an absolute path'
            )
        try:
            root = candidate.resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError(
                f'cannot resolve explicit workspace root {raw_root}: {exc}'
            ) from exc
        canonical = str(root)
        if canonical in seen:
            raise ValueError(
                f'{TEMPLATE_OPTIONS_NAME} contains duplicate workspace root: {canonical}'
            )
        if not root.is_dir():
            raise ValueError(f'explicit workspace root is not a directory: {canonical}')
        _template_design_specs(root)
        seen.add(canonical)
        roots.append(root)
    return data, roots


def _build_template_library() -> tuple[dict, dict[str, dict], dict[str, dict], dict]:
    """Build indexed library groups without scanning template directories."""
    library = {}
    candidates = {}
    registered_roots = {}
    index_contracts = {}
    for kind, (directory_name, index_name) in _TEMPLATE_LIBRARY_CONFIG.items():
        kind_dir = (_TEMPLATES_DIR / directory_name).resolve()
        index_path = kind_dir / index_name
        index_data = _read_json_object(index_path)
        index_contracts[kind] = index_data
        group = []
        for template_id, metadata in index_data.items():
            if not _safe_template_id(template_id):
                raise ValueError(
                    f'{index_path} contains unsafe template id: {template_id!r}'
                )
            if not isinstance(metadata, dict):
                raise ValueError(
                    f'{index_path} entry {template_id!r} must be an object'
                )
            workspace_root = (kind_dir / template_id).resolve()
            if workspace_root.parent != kind_dir:
                raise ValueError(
                    f'{index_path} entry {template_id!r} does not resolve to a '
                    f'direct child of {kind_dir}'
                )
            if not workspace_root.is_dir():
                raise ValueError(
                    f'{index_path} entry {template_id!r} workspace does not exist: '
                    f'{workspace_root}'
                )
            spec_path = workspace_root / 'templates' / 'design_spec.md'
            if not spec_path.is_file():
                raise ValueError(
                    f'{index_path} entry {template_id!r} is missing {spec_path}'
                )
            declared_kind = _template_kind_from_spec(spec_path)
            if declared_kind != kind:
                raise ValueError(
                    f'{index_path} entry {template_id!r} declares kind '
                    f'{declared_kind!r}, expected {kind!r}'
                )
            summary = metadata.get('summary', '')
            if not isinstance(summary, str):
                raise ValueError(
                    f'{index_path} entry {template_id!r} summary must be a string'
                )
            key = f'library:{kind}:{template_id}'
            if key in candidates:
                raise ValueError(f'duplicate template candidate key: {key}')
            candidate = {
                'key': key,
                'source': 'library',
                'kind': kind,
                'id': template_id,
                'label': template_id,
                'summary': summary,
                'workspace_root': str(workspace_root),
            }
            canonical_root = candidate['workspace_root']
            if canonical_root in registered_roots:
                raise ValueError(
                    f'duplicate registered workspace root: {canonical_root}'
                )
            group.append(candidate)
            candidates[key] = candidate
            registered_roots[canonical_root] = candidate
        library[kind] = group
    return library, candidates, registered_roots, index_contracts


def _build_template_options(confirm_dir: Path) -> tuple[dict, dict[str, dict]]:
    """Return the browser contract and its server-owned candidate whitelist."""
    source, explicit_roots = _read_template_options_input(confirm_dir)
    library, candidates, registered_roots, index_contracts = _build_template_library()
    explicit = []
    suggested_keys = []
    for root in explicit_roots:
        canonical_root = str(root)
        registered = registered_roots.get(canonical_root)
        if registered is not None:
            suggested_keys.append(registered['key'])
            continue
        digest = hashlib.sha256(canonical_root.encode('utf-8')).hexdigest()
        root_specs = [
            (spec, _template_kind_from_spec(spec))
            for spec in _template_design_specs(root)
        ]
        root_kinds = [kind for _spec, kind in root_specs]
        duplicate_kinds = sorted({
            kind for kind in root_kinds if root_kinds.count(kind) > 1
        })
        if duplicate_kinds:
            raise ValueError(
                'workspace root exposes the same kind more than once '
                f'({", ".join(duplicate_kinds)}): {canonical_root}'
            )
        for spec, kind in root_specs:
            key = f'explicit:{digest}:{kind}'
            if key in candidates:
                raise ValueError(f'duplicate template candidate key: {key}')
            candidate = {
                'key': key,
                'source': 'explicit',
                'kind': kind,
                'label': root.name or canonical_root,
                'workspace_root': canonical_root,
            }
            explicit.append(candidate)
            candidates[key] = candidate
            suggested_keys.append(key)

    # One supplied exact root is an unambiguous convenience default, including
    # a multi-kind root whose kinds compose rather than compete. Several roots
    # are candidates for the single-select controls, not an instruction to
    # select all of them.
    preselected_keys = suggested_keys if len(explicit_roots) == 1 else []

    response = {
        'schema_version': TEMPLATE_SCHEMA_VERSION,
        'phase': 'template',
        'default_mode': source['default_mode'],
        'library': library,
        'explicit': explicit,
        'preselected_keys': preselected_keys,
    }
    if 'lang' in source:
        response['lang'] = source['lang'].strip()
    response['options_sha256'] = _json_sha256({
        'schema_version': TEMPLATE_SCHEMA_VERSION,
        'phase': 'template',
        'default_mode': response['default_mode'],
        'lang': response.get('lang'),
        'explicit_workspace_roots': [str(root) for root in explicit_roots],
        'library_indexes': index_contracts,
        'library': library,
        'explicit': explicit,
        'preselected_keys': preselected_keys,
    })
    return response, candidates


def _template_selection_from_candidate(candidate: dict) -> dict:
    """Project one trusted browser candidate into the persisted selection."""
    selection = {
        'source': candidate['source'],
        'kind': candidate['kind'],
    }
    if candidate['source'] == 'library':
        selection['id'] = candidate['id']
    selection['workspace_root'] = candidate['workspace_root']
    return selection


def _template_selection_sha256(
    mode: str,
    selections: list[dict],
    options_sha256: str,
) -> str:
    """Bind one resolved choice to the candidate/options contract it used."""
    return _json_sha256({
        'mode': mode,
        'selections': selections,
        'options_sha256': options_sha256,
    })


def _validate_template_selection(data: dict) -> None:
    """Validate the server-owned template-selection receipt shape."""
    expected_fields = {
        'schema_version',
        'phase',
        'status',
        'mode',
        'selections',
        'options_sha256',
        'selection_sha256',
        'confirmed_at',
    }
    if set(data) != expected_fields:
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} has invalid fields')
    if type(data.get('schema_version')) is not int or data['schema_version'] != TEMPLATE_SCHEMA_VERSION:
        raise ValueError(
            f'{TEMPLATE_SELECTION_NAME} schema_version must be {TEMPLATE_SCHEMA_VERSION}'
        )
    if data.get('phase') != 'template':
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} phase must be template')
    if data.get('status') != 'confirmed':
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} status must be confirmed')
    mode = data.get('mode')
    if mode not in {'free_design', 'templates'}:
        raise ValueError(
            f'{TEMPLATE_SELECTION_NAME} mode must be free_design or templates'
        )
    selections = data.get('selections')
    if not isinstance(selections, list):
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} selections must be an array')
    if mode == 'free_design' and selections:
        raise ValueError('free_design cannot carry template selections')
    if mode == 'templates' and not selections:
        raise ValueError('templates mode requires at least one selection')

    options_sha256 = data.get('options_sha256')
    selection_sha256 = data.get('selection_sha256')
    if not isinstance(options_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', options_sha256):
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} options_sha256 is invalid')
    if not isinstance(selection_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', selection_sha256):
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} selection_sha256 is invalid')

    seen_root_kinds = set()
    seen_kinds: set[str] = set()
    explicit_roots_seen: dict[str, set[str]] = {}
    for index, selection in enumerate(selections):
        if not isinstance(selection, dict):
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] must be an object'
            )
        source = selection.get('source')
        if source not in {'library', 'explicit'}:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] has invalid source'
            )
        kind = selection.get('kind')
        if kind not in _TEMPLATE_LIBRARY_CONFIG:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] has invalid kind'
            )
        expected_keys = {'source', 'kind', 'workspace_root'}
        if source == 'library':
            expected_keys.add('id')
            if not _safe_template_id(selection.get('id')):
                raise ValueError(
                    f'{TEMPLATE_SELECTION_NAME} selections[{index}] has invalid id'
                )
        if kind in seen_kinds:
            raise ValueError(
                'template selection allows at most one workspace for kind '
                f'{kind!r}'
            )
        seen_kinds.add(kind)
        if set(selection) != expected_keys:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] has invalid fields'
            )
        workspace_root = selection.get('workspace_root')
        if not isinstance(workspace_root, str) or not workspace_root:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] '
                'workspace_root must be a non-empty string'
            )
        root = Path(workspace_root)
        if not root.is_absolute() or str(root.resolve()) != workspace_root:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selections[{index}] '
                'workspace_root must be a canonical absolute path'
            )
        if source == 'explicit':
            # One explicit workspace root may contribute several kinds, so the
            # cap counts roots rather than selections.
            explicit_roots_seen.setdefault(workspace_root, set()).add(kind)
            if len(explicit_roots_seen) > 1:
                raise ValueError(
                    'template selection allows at most one explicit workspace'
                )
        if (workspace_root, kind) in seen_root_kinds:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} contains duplicate workspace root '
                f'for kind {kind!r}: {workspace_root}'
            )
        seen_root_kinds.add((workspace_root, kind))
    if not isinstance(data.get('confirmed_at'), str) or not data['confirmed_at']:
        raise ValueError(
            f'{TEMPLATE_SELECTION_NAME} confirmed_at must be a non-empty string'
        )
    expected_selection_sha256 = _template_selection_sha256(
        mode,
        selections,
        options_sha256,
    )
    if selection_sha256 != expected_selection_sha256:
        raise ValueError(f'{TEMPLATE_SELECTION_NAME} selection_sha256 does not match')


def _validate_explicit_root_closure(
    selections: list[dict],
    candidates: dict[str, dict],
) -> None:
    """Require every selected explicit root to contribute all exposed kinds."""
    exposed: dict[str, set[str]] = {}
    for candidate in candidates.values():
        if candidate['source'] == 'explicit':
            exposed.setdefault(candidate['workspace_root'], set()).add(
                candidate['kind']
            )
    chosen: dict[str, set[str]] = {}
    for selection in selections:
        if selection['source'] == 'explicit':
            chosen.setdefault(selection['workspace_root'], set()).add(
                selection['kind']
            )
    for root, kinds in chosen.items():
        missing = sorted(exposed.get(root, set()) - kinds)
        if missing:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} selects workspace root {root} '
                f'without every kind it exposes; missing: {", ".join(missing)}'
            )


def _read_template_selection(selection_file: Path) -> dict:
    """Read a selection and revalidate it against current indexed options."""
    data = _read_json_object(selection_file)
    _validate_template_selection(data)
    options_file = selection_file.parent / TEMPLATE_OPTIONS_NAME
    if not _is_newer(selection_file, options_file):
        raise ValueError(
            f'{TEMPLATE_SELECTION_NAME} must be confirmed after the current '
            f'{TEMPLATE_OPTIONS_NAME}'
        )
    options, candidates = _build_template_options(selection_file.parent)
    if data['options_sha256'] != options['options_sha256']:
        raise ValueError(
            f'{TEMPLATE_SELECTION_NAME} options_sha256 no longer matches current options'
        )
    available_selections = {
        _json_sha256(_template_selection_from_candidate(candidate))
        for candidate in candidates.values()
    }
    for selection in data['selections']:
        if _json_sha256(selection) not in available_selections:
            raise ValueError(
                f'{TEMPLATE_SELECTION_NAME} references an unavailable candidate'
            )

    _validate_explicit_root_closure(data['selections'], candidates)
    return data


def _validate_template_handoff(data: dict) -> None:
    """Validate the agent-owned Step-3 completion receipt shape."""
    expected_fields = {
        'schema_version',
        'phase',
        'status',
        'mode',
        'selection_sha256',
        'completed_at',
    }
    if set(data) != expected_fields:
        raise ValueError(f'{TEMPLATE_HANDOFF_NAME} has invalid fields')
    if type(data.get('schema_version')) is not int or data['schema_version'] != TEMPLATE_SCHEMA_VERSION:
        raise ValueError(
            f'{TEMPLATE_HANDOFF_NAME} schema_version must be {TEMPLATE_SCHEMA_VERSION}'
        )
    if data.get('phase') != 'template':
        raise ValueError(f'{TEMPLATE_HANDOFF_NAME} phase must be template')
    if data.get('status') != 'ready':
        raise ValueError(f'{TEMPLATE_HANDOFF_NAME} status must be ready')
    if data.get('mode') not in {'free_design', 'templates'}:
        raise ValueError(
            f'{TEMPLATE_HANDOFF_NAME} mode must be free_design or templates'
        )
    selection_sha256 = data.get('selection_sha256')
    if not isinstance(selection_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', selection_sha256):
        raise ValueError(f'{TEMPLATE_HANDOFF_NAME} selection_sha256 is invalid')
    if not isinstance(data.get('completed_at'), str) or not data['completed_at']:
        raise ValueError(
            f'{TEMPLATE_HANDOFF_NAME} completed_at must be a non-empty string'
        )


def _read_template_handoff(project_path: Path, handoff_file: Path) -> dict:
    """Read a handoff and bind it to the current selection and installed state."""
    data = _read_json_object(handoff_file)
    _validate_template_handoff(data)
    selection_file = handoff_file.parent / TEMPLATE_SELECTION_NAME
    selection = _read_template_selection(selection_file)
    if not _is_newer(handoff_file, selection_file):
        raise ValueError(
            f'{TEMPLATE_HANDOFF_NAME} must be completed after the current '
            f'{TEMPLATE_SELECTION_NAME}'
        )
    if data['mode'] != selection['mode']:
        raise ValueError(f'{TEMPLATE_HANDOFF_NAME} mode does not match selection')
    if data['selection_sha256'] != selection['selection_sha256']:
        raise ValueError(
            f'{TEMPLATE_HANDOFF_NAME} selection_sha256 does not match selection'
        )
    if data['mode'] == 'templates':
        if not _installed_template_specs(project_path):
            raise ValueError(
                f'{TEMPLATE_HANDOFF_NAME} requires at least one installed '
                f'template spec: {project_path / "templates"}/'
                'design_spec.<kind>.<id>.md'
            )
    return data


def _installed_template_specs(project_path: Path) -> list[Path]:
    """Return every template spec installed into the project by the apply stage.

    The apply stage installs one file per selected workspace, named
    ``design_spec.<kind>.<id>.md``. A bare ``design_spec.md`` under
    ``templates/`` means the project is itself a Create Template workspace and
    is deliberately excluded here.
    """
    return sorted(
        path
        for path in (project_path / 'templates').glob('design_spec.*.md')
        if path.is_file() and _TEMPLATE_SPEC_NAME_RE.fullmatch(path.name)
    )


def _complete_template_selection(project_path: Path) -> int:
    """Write the agent-owned handoff after Stage 1 and template application."""
    confirm_dir = project_path / CONFIRM_DIR_NAME
    selection_file = confirm_dir / TEMPLATE_SELECTION_NAME
    if not selection_file.exists():
        logger.error('%s not found — the user must confirm Stage 1 first', selection_file)
        return 1
    try:
        selection = _read_template_selection(selection_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        logger.error('cannot complete template selection: %s', exc)
        return 1

    result_file = confirm_dir / RESULT_NAME
    if _result_stage(result_file) != 'stage1':
        logger.error(
            'cannot complete template selection before Stage 1 writes a '
            'stage1-confirmed result'
        )
        return 1
    if selection['mode'] == 'templates':
        if not _installed_template_specs(project_path):
            logger.error(
                'cannot complete template selection before template apply '
                'writes %s/design_spec.<kind>.<id>.md',
                project_path / 'templates',
            )
            return 1

    handoff_file = confirm_dir / TEMPLATE_HANDOFF_NAME
    if handoff_file.exists():
        try:
            existing = _read_template_handoff(project_path, handoff_file)
        except (OSError, json.JSONDecodeError, ValueError):
            existing = None
        if (
            existing is not None
            and existing['selection_sha256'] == selection['selection_sha256']
            and _is_newer(handoff_file, result_file)
        ):
            logger.info('template selection already complete: %s', handoff_file)
            return 0

    handoff = {
        'schema_version': TEMPLATE_SCHEMA_VERSION,
        'phase': 'template',
        'status': 'ready',
        'mode': selection['mode'],
        'selection_sha256': selection['selection_sha256'],
        'completed_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    }
    _validate_template_handoff(handoff)
    _write_json_atomic(handoff_file, handoff)
    logger.info('template selection handoff written to %s', handoff_file)
    return 0


def _reset_template_selection(confirm_dir: Path) -> int:
    """Remove one-run template-selection artifacts before a fresh UI lifecycle."""
    removed = []
    for filename in (
        TEMPLATE_HANDOFF_NAME,
        TEMPLATE_SELECTION_NAME,
        TEMPLATE_OPTIONS_NAME,
    ):
        path = confirm_dir / filename
        try:
            path.unlink()
            removed.append(str(path))
        except FileNotFoundError:
            continue
        except OSError as exc:
            logger.error('cannot remove %s: %s', path, exc)
            return 1
    if removed:
        logger.info('reset template selection artifacts: %s', ', '.join(removed))
    else:
        logger.info('template selection artifacts already absent')
    return 0


def _stage1_ready_error(confirm_dir: Path) -> Optional[str]:
    """Return why the combined template/Stage-1 page cannot be exposed."""
    options_file = confirm_dir / TEMPLATE_OPTIONS_NAME
    if not options_file.exists():
        return f'{TEMPLATE_OPTIONS_NAME} not found'
    try:
        _build_template_options(confirm_dir)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f'invalid template options: {exc}'

    stage1_file = confirm_dir / RECOMMENDATION_STAGE_NAMES[1]
    if not stage1_file.exists():
        return f'{stage1_file.name} not found'
    try:
        stage1_data = _read_json_object(stage1_file)
        if _recommendation_stage(stage1_data) != 1:
            return f'{stage1_file.name} does not declare stage1'
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f'cannot validate Stage 1 recommendations: {exc}'

    result_file = confirm_dir / RESULT_NAME
    if result_file.exists():
        if not _is_newer(options_file, result_file):
            return f'{TEMPLATE_OPTIONS_NAME} must be newer than the prior {RESULT_NAME}'
        if not _is_newer(stage1_file, result_file):
            return f'{stage1_file.name} must be newer than the prior {RESULT_NAME}'
    return None


def _stage2_ready_error(
    project_path: Path,
    confirm_dir: Path,
    recommendations_file: Optional[Path] = None,
) -> Optional[str]:
    """Return why final Stage 2 cannot follow the confirmed template choice."""
    selection_file = confirm_dir / TEMPLATE_SELECTION_NAME
    if not selection_file.exists():
        return f'{TEMPLATE_SELECTION_NAME} not found after Stage 1 confirmation'
    try:
        _read_template_selection(selection_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f'invalid template selection: {exc}'

    result_file = confirm_dir / RESULT_NAME
    if _result_stage(result_file) != 'stage1':
        return f'{RESULT_NAME} does not contain a stage1-confirmed result'

    handoff_file = confirm_dir / TEMPLATE_HANDOFF_NAME
    if not handoff_file.exists():
        return f'{TEMPLATE_HANDOFF_NAME} not found after template application'
    try:
        _read_template_handoff(project_path, handoff_file)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return f'invalid template handoff: {exc}'
    if not _is_newer(handoff_file, result_file):
        return f'{TEMPLATE_HANDOFF_NAME} must be newer than the Stage 1 {RESULT_NAME}'

    if recommendations_file is not None and not _is_newer(
        recommendations_file,
        handoff_file,
    ):
        return f'{recommendations_file.name} must be newer than {TEMPLATE_HANDOFF_NAME}'
    return None


def _resolve_template_confirmation(
    payload: dict,
    candidates: dict[str, dict],
    options_sha256: str,
) -> dict:
    """Resolve browser keys against the current server-owned candidate set."""
    required_fields = {'mode', 'selection_keys'}
    if set(payload) != required_fields:
        raise ValueError('template confirmation accepts only mode and selection_keys')
    mode = payload.get('mode')
    if mode not in {'free_design', 'templates'}:
        raise ValueError('mode must be free_design or templates')
    selection_keys = payload.get('selection_keys')
    if not isinstance(selection_keys, list):
        raise ValueError('selection_keys must be an array')
    if any(not isinstance(key, str) or not key for key in selection_keys):
        raise ValueError('selection_keys must contain non-empty strings')
    if len(selection_keys) != len(set(selection_keys)):
        raise ValueError('selection_keys must not contain duplicates')
    if mode == 'free_design' and selection_keys:
        raise ValueError('free_design cannot carry selection_keys')
    if mode == 'templates' and not selection_keys:
        raise ValueError('templates mode requires at least one selection key')

    unknown_keys = [key for key in selection_keys if key not in candidates]
    if unknown_keys:
        raise ValueError(
            'selection_keys contains unavailable candidate keys: '
            + ', '.join(unknown_keys)
        )
    selections = sorted([
        _template_selection_from_candidate(candidates[key])
        for key in selection_keys
    ], key=lambda item: (
        item['source'],
        item.get('kind', ''),
        item.get('id', ''),
        item['workspace_root'],
    ))
    selection_sha256 = _template_selection_sha256(
        mode,
        selections,
        options_sha256,
    )
    receipt = {
        'schema_version': TEMPLATE_SCHEMA_VERSION,
        'phase': 'template',
        'status': 'confirmed',
        'mode': mode,
        'selections': selections,
        'options_sha256': options_sha256,
        'selection_sha256': selection_sha256,
        'confirmed_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    }
    _validate_template_selection(receipt)
    _validate_explicit_root_closure(selections, candidates)
    return receipt


def _confirmation_launch_error(confirm_dir: Path) -> Optional[str]:
    """Return why the current Default UI lifecycle cannot launch."""
    options_file = confirm_dir / TEMPLATE_OPTIONS_NAME
    result_file = confirm_dir / RESULT_NAME
    result_stage = _result_stage(result_file)
    fresh_template_options = _fresh_template_restart(confirm_dir)
    if (
        result_file.exists()
        and result_stage is None
        and not fresh_template_options
    ):
        return (
            f'{RESULT_NAME} is not a current stage1/final receipt — reset the '
            f'template selection and write fresh {TEMPLATE_OPTIONS_NAME} before '
            'starting a new run'
        )
    if (
        result_stage == 'final'
        and not fresh_template_options
    ):
        return (
            'the previous Confirm UI run is complete — reset the template '
            f'selection and write fresh {TEMPLATE_OPTIONS_NAME} before starting a new one'
        )
    if options_file.exists():
        try:
            _build_template_options(confirm_dir)
            selection_file = confirm_dir / TEMPLATE_SELECTION_NAME
            if result_stage == 'stage1' and not selection_file.exists():
                return (
                    f'{TEMPLATE_SELECTION_NAME} not found for the confirmed '
                    'Stage 1 result'
                )
            if selection_file.exists():
                _read_template_selection(selection_file)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return f'invalid template selection input: {exc}'
        if result_stage is None or fresh_template_options:
            stage1_error = _stage1_ready_error(confirm_dir)
            if stage1_error:
                return f'Stage 1 is not ready: {stage1_error}'
        return None
    return f'{options_file} not found — write template options before launch'


def _server_url(port: int, path: str = '') -> str:
    """Return the loopback URL shown to users and used by readiness probes."""
    suffix = path if path.startswith('/') or not path else f'/{path}'
    return f'http://{PUBLIC_HOST}:{port}{suffix}'


def _wait_for_server_ready(
    port: int,
    proc: subprocess.Popen,
    project_path: Path,
    timeout: int = STARTUP_TIMEOUT,
) -> bool:
    """Wait until this project's detached confirm server is accepting requests."""
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
                data = json.load(resp)
                if (
                    resp.status == 200
                    and isinstance(data, dict)
                    and data.get('service') == 'confirm_ui'
                    and data.get('project') == str(project_path)
                    and data.get('pid') == proc.pid
                ):
                    return True
                last_error = 'health response belongs to another service or project'
        except (OSError, ValueError, urllib.error.URLError) as exc:
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
    exact_port: bool,
    idle_timeout: int,
    open_browser: bool,
) -> tuple[subprocess.Popen, int, Path]:
    """Start the confirm server child and wait until it is reachable."""
    confirm_dir = project_path / CONFIRM_DIR_NAME
    confirm_dir.mkdir(parents=True, exist_ok=True)
    log_path = confirm_dir / 'server.log'
    port = preferred_port if exact_port else _find_free_port(preferred_port)
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
    if not _wait_for_server_ready(port, proc, project_path):
        if proc.poll() is None:
            proc.terminate()
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
        return _validate_port(port) if port else fallback
    except (TypeError, ValueError):
        return fallback


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
    """Return the current result stage (Stage 1 or final), or None."""
    if not result_file.is_file():
        return None
    try:
        data = _read_json_object(result_file)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    stage = _stage_key(data.get('stage'))
    status = data.get('status')
    if stage == 'stage1' and status == 'stage1-confirmed':
        return stage
    if stage == 'final' and status == 'confirmed':
        return stage
    return None


def _stage_key(value: object) -> Optional[str]:
    """Normalize the two current recommendation/result stage names."""
    if value is None:
        return None
    raw = str(value).strip().lower()
    if raw == 'stage1':
        return 'stage1'
    if raw == 'stage2':
        return 'stage2'
    if raw == 'final':
        return 'final'
    return None


def _recommendation_stage(data: dict) -> int:
    """Return a recommendation payload's declared stage."""
    stage = _stage_key(data.get('stage'))
    if stage == 'stage1':
        return 1
    if stage == 'stage2':
        return 2
    return 0


def _stage_name(number: Optional[int]) -> Optional[str]:
    """Return the canonical stage key for a stage number."""
    if number == 1:
        return 'stage1'
    if number == 2:
        return 'stage2'
    return None


def _result_stage_number(stage: Optional[str]) -> int:
    """Return result progression: stage1=1, final=2."""
    if stage == 'stage1':
        return 1
    if stage == 'final':
        return 2
    return 0


def _expected_recommendation_stage(result_stage: Optional[str]) -> int:
    """Return the recommendation stage that follows the current result."""
    if result_stage in {'stage1', 'final'}:
        return 2
    return 1


def _stage_recommendations_path(confirm_dir: Path, stage_number: int) -> Path:
    """Return the stage-specific recommendation path for one handoff."""
    return confirm_dir / RECOMMENDATION_STAGE_NAMES[stage_number]


def _is_newer(path: Path, baseline: Path) -> bool:
    """Return whether ``path`` was authored after ``baseline``."""
    try:
        return path.stat().st_mtime_ns > baseline.stat().st_mtime_ns
    except OSError:
        return False


def _fresh_template_restart(confirm_dir: Path) -> bool:
    """Return whether fresh template options start a new UI session."""
    return _is_newer(
        confirm_dir / TEMPLATE_OPTIONS_NAME,
        confirm_dir / RESULT_NAME,
    )


def _active_recommendations_path(confirm_dir: Path) -> Path:
    """Resolve the recommendation file for the current two-stage session."""
    if _fresh_template_restart(confirm_dir):
        return _stage_recommendations_path(confirm_dir, 1)
    result_stage = _result_stage(confirm_dir / RESULT_NAME)
    expected_stage = _expected_recommendation_stage(result_stage)
    return _stage_recommendations_path(confirm_dir, expected_stage)


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
        if stage_number == 2:
            result_file = confirm_dir / RESULT_NAME
            if _result_stage(result_file) == 'stage1':
                if not _is_newer(rec_file, result_file):
                    raise ValueError(
                        f'{filename} must be authored after the current '
                        'Stage-1 confirmation'
                    )
            production_error = _stage2_production_recommendations_error(data)
            if production_error:
                raise ValueError(production_error)
        break
    return rec_file, data


def _template_confirmation_required(project_path: Path) -> bool:
    """Return whether the confirmed project state has an active template."""
    confirm_dir = project_path / CONFIRM_DIR_NAME
    handoff = _read_template_handoff(
        project_path,
        confirm_dir / TEMPLATE_HANDOFF_NAME,
    )
    return handoff['mode'] == 'templates'


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
        for key in (field, f'{field}_zh', f'{field}_zh_tw', f'{field}_en', f'{field}_ja')
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


def _stage2_production_recommendations_error(
    recommendations: dict,
) -> Optional[str]:
    """Require every production control in current Stage 2 recommendations."""
    recommend = recommendations.get('recommend')
    if not isinstance(recommend, dict):
        recommend = {}
    generation_mode = recommend.get('generation_mode')
    if not isinstance(generation_mode, str) or not generation_mode.strip():
        return (
            'Stage 2 recommendations must include non-empty '
            'recommend.generation_mode'
        )
    refine_spec = recommendations.get('refine_spec')
    if (
        not isinstance(refine_spec, dict)
        or not isinstance(refine_spec.get('value'), bool)
    ):
        return 'Stage 2 recommendations must include refine_spec.value as a boolean'
    if _uses_ai_images(recommendations):
        image_ai_path = recommend.get('image_ai_path')
        if not isinstance(image_ai_path, str) or not image_ai_path.strip():
            return (
                'Stage 2 recommendations must include non-empty '
                'recommend.image_ai_path when image_usage includes ai'
            )
    return None


def _stage2_production_result_error(result: dict) -> Optional[str]:
    """Require every user-confirmed production control in the final payload."""
    generation_mode = result.get('generation_mode')
    if not isinstance(generation_mode, str) or not generation_mode.strip():
        return 'final Stage 2 payload must include non-empty generation_mode'
    if not isinstance(result.get('refine_spec'), bool):
        return 'final Stage 2 payload must include refine_spec as a boolean'
    if _uses_ai_images(result):
        image_ai_path = result.get('image_ai_path')
        if not isinstance(image_ai_path, str) or not image_ai_path.strip():
            return (
                'final Stage 2 payload must include non-empty image_ai_path '
                'when image_usage includes ai'
            )
    return None


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


def _is_english_language(language: object) -> bool:
    """Return whether a recommendation language is an English locale."""
    if not isinstance(language, str):
        return False
    try:
        return language_base(language) == 'en'
    except LanguageTagError:
        return False


def _recommendation_language(recommendations: dict) -> object:
    """Return the deck's main language without conflating it with UI ``lang``."""
    value = (
        recommendations.get('primary_language')
        or recommendations.get('content_language')
        or recommendations.get('language')
    )
    if isinstance(value, dict):
        return value.get('value') or value.get('id') or value.get('code') or ''
    return value


def _primary_language_error(recommendations: dict) -> Optional[str]:
    """Require and canonicalize the staged content-language source of truth."""
    return _canonicalize_primary_language(recommendations, required=True)


def _canonicalize_primary_language(
    recommendations: dict,
    *,
    required: bool,
) -> Optional[str]:
    """Write a canonical primary language into one recommendation/result object."""
    value = _recommendation_language(recommendations)
    if not isinstance(value, str) or not value.strip():
        if required:
            return (
                'Stage 1 recommendations must declare a valid primary_language '
                'BCP-47 tag; lang controls only the Confirm UI language'
            )
        return None
    try:
        recommendations['primary_language'] = normalize_language_tag(value)
    except LanguageTagError as exc:
        return f'invalid primary_language: {exc}'
    return None


def _typography_font_value(
    font: dict,
    field: str,
    *,
    english_primary: bool,
) -> object:
    """Return a canonical typography font value, accepting its language-aware alias."""
    legacy_field = 'latin' if field == 'english' or english_primary else 'cjk'
    value = font.get(field)
    if not isinstance(value, str) or not value.strip():
        value = font.get(legacy_field)
    return value


def _typography_error(
    typography: object,
    label: str,
    *,
    require_sizes: bool,
    main_language: object = '',
) -> Optional[str]:
    """Validate one complete user-facing typography recommendation or choice."""
    if not isinstance(typography, dict):
        return f'{label} must be an object'
    english_primary = _is_english_language(main_language)
    for role in ('heading', 'body'):
        font = typography.get(role)
        if not isinstance(font, dict):
            return f'{label}.{role} must be an object'
        fields = (('primary', 'latin' if english_primary else 'cjk'),)
        if not english_primary:
            fields += (('english', 'latin'),)
        for field, legacy_field in fields:
            value = _typography_font_value(
                font,
                field,
                english_primary=english_primary,
            )
            if not isinstance(value, str) or not value.strip():
                return (
                    f'{label}.{role}.{field} '
                    f'(or legacy {legacy_field}) must be non-empty'
                )
        if not isinstance(font.get('css'), str) or not font['css'].strip():
            return f'{label}.{role}.css must be non-empty'
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


def _typography_signature(
    typography: dict,
    *,
    main_language: object,
) -> tuple[str, ...]:
    """Return the language-relevant font choices that distinguish one candidate."""
    english_primary = _is_english_language(main_language)
    fields = ('primary',) if english_primary else ('primary', 'english')
    values = []
    for role in ('heading', 'body'):
        font = typography[role]
        for field in fields:
            value = _typography_font_value(
                font,
                field,
                english_primary=english_primary,
            )
            values.append(str(value).strip().casefold())
    return tuple(values)


def _typography_candidates_fixed_error(
    candidates: list,
    *,
    main_language: object,
) -> Optional[str]:
    """Reject contradictions in an explicitly fixed typography contract."""
    fixed = [
        isinstance(candidate, dict) and candidate.get('fixed') is True
        for candidate in candidates
    ]
    if any(fixed):
        if not all(fixed):
            return 'typography.fixed must be true on every candidate or omitted'
        signatures = [
            _typography_signature(
                candidate,
                main_language=main_language,
            )
            for candidate in candidates
        ]
        if any(signature != signatures[0] for signature in signatures[1:]):
            return 'fixed typography candidates must repeat the same font combination'
        return None
    return None


def _candidate_list(spec: object) -> list:
    """Return candidates from the current or legacy recommendation shape."""
    if not isinstance(spec, dict):
        return []
    candidates = spec.get('candidates')
    if not isinstance(candidates, list):
        candidates = spec.get('options')
    return candidates if isinstance(candidates, list) else []


def _stage2_design_directions_error(
    recommendations: dict,
    *,
    main_language: object = '',
) -> Optional[str]:
    """Require three complete custom systems and a valid preferred direction."""
    main_language = main_language or _recommendation_language(recommendations)
    directions = recommendations.get('design_directions')
    if isinstance(directions, dict):
        candidates = _candidate_list(directions)
        if len(candidates) != 3:
            return 'Stage 2 design_directions must include exactly 3 candidates'
        selected = directions.get('selected', 0)
        if type(selected) is not int or not 0 <= selected < len(candidates):
            return 'Stage 2 design_directions.selected must be an integer from 0 to 2'
        typography_candidates = []
        direction_ids = set()
        for index, candidate in enumerate(candidates, start=1):
            label = f'design_directions.candidates[{index - 1}]'
            if not isinstance(candidate, dict):
                return f'{label} must be an object'
            direction_id = str(candidate.get('id') or '').strip()
            if not direction_id:
                return f'{label}.id must be non-empty'
            if direction_id in direction_ids:
                return f'{label}.id must be unique'
            direction_ids.add(direction_id)
            if not _localized_text_present(candidate, 'name'):
                return f'{label} requires a non-empty localized name'
            for field in ('mode', 'visual_style', 'icons'):
                if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                    return f'{label}.{field} must be non-empty'
            if candidate['mode'] != 'custom':
                return f'{label}.mode must be custom'
            if not _localized_text_present(candidate, 'mode_behavior'):
                return f'{label}.mode=custom requires non-empty localized mode_behavior'
            if candidate['visual_style'] != 'custom':
                return f'{label}.visual_style must be custom'
            if not _localized_text_present(candidate, 'visual_style_behavior'):
                return (
                    f'{label}.visual_style=custom requires non-empty localized '
                    'visual_style_behavior'
                )
            error = _palette_error(candidate.get('color'), f'{label}.color')
            if error:
                return error
            error = _typography_error(
                candidate.get('typography'),
                f'{label}.typography',
                require_sizes=False,
                main_language=main_language,
            )
            if error:
                return error
            typography_candidates.append(candidate['typography'])
            image_strategy = candidate.get('image_strategy')
            if not isinstance(image_strategy, dict):
                return f'{label}.image_strategy must be an object'
            rendering = str(image_strategy.get('rendering') or '').strip()
            if not rendering:
                return f'{label}.image_strategy.rendering must be non-empty'
            if rendering != 'custom':
                return f'{label}.image_strategy.rendering must be custom'
            for prose_field in ('name', 'visual', 'mood'):
                if not _localized_text_present(image_strategy, prose_field):
                    return (
                        f'{label}.image_strategy requires non-empty localized '
                        f'{prose_field}'
                    )
            if not _localized_text_present(image_strategy, 'behavior'):
                return (
                    f'{label}.image_strategy.rendering=custom requires non-empty '
                    'localized behavior'
                )
        return _typography_candidates_fixed_error(
            typography_candidates,
            main_language=main_language,
        )

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
    if main_language and len(typography) < 3:
        return 'Stage 2 recommendations must include 3 typography candidates'
    for index, candidate in enumerate(typography):
        error = _typography_error(
            candidate,
            f'typography.candidates[{index}]',
            require_sizes=False,
            main_language=main_language,
        )
        if error:
            return error
    if main_language:
        return _typography_candidates_fixed_error(
            typography,
            main_language=main_language,
        )
    return None


def _stage2_custom_candidates_error(recommendations: dict) -> Optional[str]:
    """Validate optional legacy standalone custom alternatives."""
    candidates = recommendations.get('custom_candidates')
    if candidates is None:
        return None
    if not isinstance(candidates, dict):
        return 'custom_candidates must be an object when present'

    for field in ('mode', 'visual_style'):
        candidate = candidates.get(field)
        if candidate is None:
            continue
        if not isinstance(candidate, dict):
            return f'custom_candidates.{field} must be an object'
        for prose_field in ('name', 'behavior'):
            if not _localized_text_present(candidate, prose_field):
                return (
                    f'custom_candidates.{field} requires non-empty localized '
                    f'{prose_field}'
                )

    image_candidate = candidates.get('image_strategy')
    if image_candidate is None:
        return None
    if not isinstance(image_candidate, dict):
        return 'custom_candidates.image_strategy must be an object'
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
    confirm_dir: Path,
    submitted_stage: Optional[str],
    *,
    recommendations_file: Path,
    recommendations: dict,
    template_required: bool,
) -> Optional[str]:
    """Reject a confirmation that does not match the staged recommendation."""
    rec_stage_number = _recommendation_stage(recommendations)
    if rec_stage_number == 0:
        return 'recommendations must declare stage1 or stage2'

    if rec_stage_number == 1:
        language_error = _primary_language_error(recommendations)
        if language_error:
            return language_error

    if rec_stage_number == 2:
        try:
            previous_result = _read_json_object(confirm_dir / RESULT_NAME)
        except (OSError, json.JSONDecodeError, ValueError):
            previous_result = {}
        language_source = (
            previous_result
            if _recommendation_language(previous_result)
            else recommendations
        )
        language_error = _canonicalize_primary_language(
            language_source,
            required=True,
        )
        if language_error:
            return language_error
        main_language = _recommendation_language(language_source)
        recommendation_error = _template_stage2_error(
            recommendations,
            template_required=template_required,
        )
        if recommendation_error:
            return recommendation_error
        recommendation_error = _stage2_custom_candidates_error(recommendations)
        if recommendation_error:
            return recommendation_error
        recommendation_error = _stage2_design_directions_error(
            recommendations,
            main_language=main_language,
        )
        if recommendation_error:
            return recommendation_error

    allowed_submissions = {
        1: {'stage1'},
        2: {'final'},
    }
    if submitted_stage not in allowed_submissions[rec_stage_number]:
        expected = 'final' if rec_stage_number == 2 else 'stage1'
        return (
            f'confirmation stage mismatch: {recommendations_file.name} is '
            f'{_stage_name(rec_stage_number)}, so the submitted stage must be '
            f'{expected}'
        )

    previous_stage = (
        None
        if _fresh_template_restart(confirm_dir)
        else _result_stage(confirm_dir / RESULT_NAME)
    )
    allowed_predecessors = {
        1: {None},
        2: {'stage1'},
    }
    if previous_stage not in allowed_predecessors[rec_stage_number]:
        expected_previous = 'stage1' if rec_stage_number == 2 else 'no prior result'
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


def _stage2_solution_error(
    result: dict,
    *,
    main_language: object = '',
) -> Optional[str]:
    """Reject a Stage 2/final payload with an incomplete design system."""
    production_error = _stage2_production_result_error(result)
    if production_error:
        return production_error

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
        main_language=main_language,
    )
    if typography_error:
        return typography_error

    if _uses_ai_images(result):
        image_strategy = result.get('image_strategy')
        if not isinstance(image_strategy, dict) or not str(
            image_strategy.get('rendering') or ''
        ).strip():
            return 'image_usage includes ai, so image_strategy.rendering must be non-empty'
        rendering = image_strategy['rendering'].strip()
        if rendering != 'custom' and rendering not in _ai_rendering_ids():
            return f'image_strategy.rendering is not a known preset: {rendering}'
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
        2: 'final',
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

    fresh_restart = _fresh_template_restart(confirm_dir)
    result_stage = None if fresh_restart else _result_stage(result_file)
    result_stage_number = _result_stage_number(result_stage)

    if result_stage == 'final':
        expected_stage_number = None
        status = 'done'
        current_stage = 'final'
    elif result_stage == 'stage1':
        expected_stage_number = 2
        ready = rec_stage_number == 2
        status = 'ready_user' if ready else 'waiting_agent'
        current_stage = 'stage2' if ready else 'stage1'
    else:
        expected_stage_number = 1
        ready = rec_stage_number == 1
        status = 'ready_user' if ready else 'waiting_agent'
        current_stage = 'stage1'

    session = {
        'phase': 'strategist',
        'status': status,
        'current_stage': current_stage,
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

    options_file = confirm_dir / TEMPLATE_OPTIONS_NAME
    selection_file = confirm_dir / TEMPLATE_SELECTION_NAME
    handoff_file = confirm_dir / TEMPLATE_HANDOFF_NAME
    session.update({
        'template_options_file': TEMPLATE_OPTIONS_NAME,
        'template_options_version': _file_version(options_file),
        'template_selection_file': TEMPLATE_SELECTION_NAME,
        'template_selection_version': _file_version(selection_file),
        'template_handoff_file': TEMPLATE_HANDOFF_NAME,
        'template_handoff_version': _file_version(handoff_file),
    })

    if result_stage == 'final':
        session.update({
            'template_status': 'ready',
            'template_error': None,
        })
        return session

    if result_stage is None:
        ready_error = _stage1_ready_error(confirm_dir)
        if ready_error:
            session.update({
                'status': 'error',
                'template_status': 'error',
                'template_error': ready_error,
            })
            if not session.get('recommendation_error'):
                session['recommendation_error'] = ready_error
            return session
        session.update({
            'template_status': 'ready_user',
            'template_error': None,
        })
        return session

    ready_error = _stage2_ready_error(
        confirm_dir.parent,
        confirm_dir,
        rec_file if rec_stage_number == 2 else None,
    )
    if ready_error:
        session.update({
            'status': 'waiting_agent',
            'current_stage': 'stage1',
            'expected_stage': 'stage2',
            'expected_stage_number': 2,
            'template_status': 'waiting_agent',
            'template_error': ready_error,
        })
        return session
    session.update({
        'template_status': 'ready',
        'template_error': None,
    })
    return session


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
# only in browser STATE and would be lost on an in-run refresh. Fold them from
# result.json into Stage-2 recommendations so the same live run resumes from the
# user's actual communication contract and complete deck-solution choices.
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
_PROACTIVE_EXECUTION_DEFAULTS = {
    'proactive_speaker_notes': True,
    'proactive_custom_animations': False,
    'proactive_narration_audio': False,
}
_LOCKED_RECOMMENDATIONS_KEY = '_locked_recommendations'


def _resolve_proactive_execution_values(
    source: dict,
) -> tuple[dict[str, bool], Optional[str]]:
    """Resolve proactive-execution booleans with backward-compatible defaults."""
    values = {}
    for key, default in _PROACTIVE_EXECUTION_DEFAULTS.items():
        if key not in source:
            values[key] = default
            continue
        raw_value = source[key]
        if isinstance(raw_value, dict):
            if 'value' not in raw_value or not isinstance(raw_value['value'], bool):
                return {}, f'{key}.value must be a boolean'
            raw_value = raw_value['value']
        elif not isinstance(raw_value, bool):
            return {}, f'{key} must be a boolean'
        values[key] = raw_value
    return values, None


def _normalize_proactive_execution_result(
    result: dict,
    defaults: dict[str, bool],
) -> Optional[str]:
    """Write the independent raw confirmation booleans to the final result."""
    values = {}
    for key, default in defaults.items():
        value = result.get(key, default)
        if not isinstance(value, bool):
            return f'{key} must be a boolean'
        values[key] = value
    result.update(values)
    return None


def _merge_confirmed_choices(data: dict, result_file: Path) -> None:
    """Fold already-confirmed choices into later-stage recommendations."""
    try:
        res = _read_json_object(result_file)
    except (OSError, json.JSONDecodeError, ValueError):
        return
    if _result_stage(result_file) != 'stage1':
        return
    recommend = data.setdefault('recommend', {})
    if not isinstance(recommend, dict):
        recommend = data['recommend'] = {}
    main_language = _recommendation_language(res)
    if main_language:
        try:
            data['primary_language'] = normalize_language_tag(main_language)
        except LanguageTagError:
            # Keep the invalid legacy value visible to the API boundary below,
            # which returns a user-facing contract error instead of hiding it.
            data['primary_language'] = main_language
    for key in _CONTRACT_RECOMMEND_KEYS:
        if res.get(key) not in (None, ''):
            recommend[key] = res[key]
    for key in _CONTRACT_VALUE_KEYS:
        if key in res:
            data[key] = {'value': res.get(key) or ''}


def _apply_locked_recommendations(
    result: dict,
    recommendations_file: Path,
    previous_result_file: Path,
    *,
    carry_previous: bool,
) -> dict:
    """Restore profile-locked fields and return locks for staged carry-over."""
    # This marker is server-owned; never accept a client-supplied carry-over map.
    result.pop(_LOCKED_RECOMMENDATIONS_KEY, None)
    locked_values = {}
    previous = {}
    if carry_previous:
        try:
            previous = _read_json_object(previous_result_file)
        except (OSError, json.JSONDecodeError, ValueError):
            previous = {}
    previous_locks = previous.get(_LOCKED_RECOMMENDATIONS_KEY)
    if isinstance(previous_locks, dict):
        locked_values.update(previous_locks)
    for key in _PROACTIVE_EXECUTION_DEFAULTS:
        locked_values.pop(key, None)

    try:
        recommendations = _read_json_object(recommendations_file)
        recommendations_loaded = True
    except (OSError, json.JSONDecodeError, ValueError):
        recommendations = {}
        recommendations_loaded = False

    # Stage 1 starts a new contract and therefore replaces any stale locks left
    # by an earlier run. Later stages inherit those locks across server restarts.
    if recommendations_loaded and _recommendation_stage(recommendations) == 1:
        locked_values = {}
    for key, field in recommendations.items():
        if key in _PROACTIVE_EXECUTION_DEFAULTS:
            continue
        if not isinstance(field, dict) or field.get('locked') is not True:
            continue
        if 'value' in field:
            locked_values[key] = field['value']
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

    No child is launched here: the page is open from the preceding ``--daemon``
    launch, so liveness is tracked via the recorded pid, not a ``proc`` handle.
    Only the stage guard is used (no mtime gate), because intermediate submits
    may happen before this wait command is issued.
    """
    logger.info('waiting for browser confirmation stage=%s...', target_stage)
    deadline = None if timeout <= 0 else time.time() + timeout
    while True:
        result_status = _wait_result_status(result_file, target_stage)
        if result_status is not None:
            return result_status

        confirm_dir = result_file.parent
        if target_stage == 'stage1':
            readiness_error = _stage1_ready_error(confirm_dir)
        else:
            recommendations_file = _active_recommendations_path(confirm_dir)
            readiness_error = _stage2_ready_error(
                confirm_dir.parent,
                confirm_dir,
                recommendations_file,
            )
        if readiness_error:
            logger.error(
                'confirmation stage=%s is not ready: %s',
                target_stage,
                readiness_error,
            )
            return 1

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


def _wait_result_status(
    result_file: Path,
    target_stage: str,
) -> Optional[int]:
    """Return a terminal wait status when the persisted result resolves the target."""
    if _fresh_template_restart(result_file.parent):
        return None
    current_stage = _result_stage(result_file)
    if current_stage == target_stage:
        if target_stage == 'stage1':
            try:
                _read_template_selection(
                    result_file.parent / TEMPLATE_SELECTION_NAME,
                )
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                logger.error(
                    'Stage 1 result has no valid template selection: %s',
                    exc,
                )
                return 2
        logger.info('confirmation stage=%s received: %s', target_stage, result_file)
        if target_stage == 'stage1':
            logger.info(
                '[NEXT] Stage 1 is intermediate: complete the template handoff, '
                'author fresh Stage 2, then wait for final confirmation.'
            )
        return 0
    if _result_stage_number(current_stage) > _result_stage_number(target_stage):
        logger.error(
            'confirmation skipped expected stage=%s and advanced to %s',
            target_stage,
            current_stage,
        )
        return 2
    return None


def _shutdown_existing(lock_file: Path) -> int:
    """Stop a confirm server left running for this project (idempotent).

    Step 4 always calls this on exit so the page never lingers on its selected
    port. Tries a graceful ``/api/shutdown`` first, falls back to killing the
    recorded pid, then clears the lock. A no-op when nothing is running.
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
    set of formats and their dimensions come from config; four-language labels
    and use text are kept from catalogs.json (with a plain fallback for new ids).
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


def _ai_rendering_ids() -> set[str]:
    """Return the rendering presets exposed by the confirmation UI."""
    return {item['id'] for item in _ai_comparison_items('rendering')}


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
            'service': 'confirm_ui',
            'pid': os.getpid(),
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
        """Expose the derived template/Strategist wizard state for polling."""
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
        result_file = confirm_dir / RESULT_NAME
        if (
            _result_stage(result_file) == 'final'
            and not _fresh_template_restart(confirm_dir)
        ):
            return jsonify({
                'error': (
                    'the current Confirm UI run is complete; reset the template '
                    f'selection and write fresh {TEMPLATE_OPTIONS_NAME} before '
                    'starting another'
                ),
            }), 409
        rec_file = _active_recommendations_path(confirm_dir)
        if not rec_file.exists():
            return jsonify({'error': f'{rec_file.name} not found'}), 404
        try:
            rec_file, data = _read_active_recommendations(confirm_dir)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return jsonify({
                'error': f'invalid current recommendation file: {exc}',
            }), 400
        rec_stage_number = _recommendation_stage(data)
        if rec_stage_number == 1:
            stage1_error = _stage1_ready_error(confirm_dir)
            if stage1_error:
                return jsonify({
                    'error': f'Stage 1 is not ready: {stage1_error}',
                }), 409
            try:
                template_options, _ = _build_template_options(confirm_dir)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                return jsonify({
                    'error': f'invalid template options: {exc}',
                }), 409
            data['template_options'] = template_options
            template_required = False
        else:
            stage2_error = _stage2_ready_error(
                project_path,
                confirm_dir,
                rec_file,
            )
            if stage2_error:
                return jsonify({
                    'error': f'Stage 2 is waiting for template handoff: {stage2_error}',
                }), 409
            try:
                template_required = _template_confirmation_required(project_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                return jsonify({
                    'error': f'cannot determine active template mode: {exc}',
                }), 409
        # Later stages render only downstream sections, so fold earlier confirmed
        # choices from result.json back in. An in-run refresh then re-inits from
        # the user's choices instead of catalog defaults.
        if rec_stage_number >= 2 and result_file.exists():
            _merge_confirmed_choices(data, result_file)
        language_error = _canonicalize_primary_language(
            data,
            required=True,
        )
        if language_error:
            return jsonify({'error': language_error}), 409
        if not template_required:
            data.pop('template_application', None)
        if rec_stage_number == 2:
            recommendation_error = _template_stage2_error(
                data,
                template_required=template_required,
            )
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
            recommendation_error = _stage2_custom_candidates_error(data)
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
            recommendation_error = _stage2_design_directions_error(data)
            if recommendation_error:
                return jsonify({'error': recommendation_error}), 409
        if rec_stage_number == 2:
            proactive_values, proactive_error = (
                _resolve_proactive_execution_values(data)
            )
            if proactive_error:
                return jsonify({'error': proactive_error}), 409
            for key, value in proactive_values.items():
                data[key] = {'value': value}
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
        template_selection_payload = result.pop('template_selection', None)
        result_file = confirm_dir / RESULT_NAME
        raw_stage = result.get('stage')
        stage = _stage_key(raw_stage)
        if raw_stage is not None and stage is None:
            return jsonify({'error': 'invalid confirmation stage'}), 400
        try:
            rec_file, current_recommendations = _read_active_recommendations(
                confirm_dir,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            return jsonify({
                'error': (
                    'cannot confirm without valid current recommendations: '
                    f'{exc}'
                ),
            }), 409
        rec_stage_number = _recommendation_stage(current_recommendations)
        selection_receipt = None
        selection_file = confirm_dir / TEMPLATE_SELECTION_NAME
        write_selection = False
        if rec_stage_number == 1:
            stage1_error = _stage1_ready_error(confirm_dir)
            if stage1_error:
                return jsonify({
                    'error': f'Stage 1 is not ready: {stage1_error}',
                }), 409
            if not isinstance(template_selection_payload, dict):
                return jsonify({
                    'error': (
                        'Stage 1 payload must include template_selection with '
                        'mode and selection_keys'
                    ),
                }), 400
            try:
                template_options, template_candidates = _build_template_options(
                    confirm_dir,
                )
                selection_receipt = _resolve_template_confirmation(
                    template_selection_payload,
                    template_candidates,
                    template_options['options_sha256'],
                )
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                return jsonify({
                    'error': f'invalid Stage 1 template selection: {exc}',
                }), 400
            template_required = selection_receipt['mode'] == 'templates'
            if selection_file.exists():
                try:
                    existing_selection = _read_template_selection(selection_file)
                except (OSError, json.JSONDecodeError, ValueError) as exc:
                    return jsonify({
                        'error': (
                            f'existing template selection is invalid: {exc}; '
                            'the agent must run --reset-template-selection'
                        ),
                    }), 409
                if (
                    existing_selection['selection_sha256']
                    != selection_receipt['selection_sha256']
                ):
                    return jsonify({
                        'error': (
                            'Stage 1 already has a different template selection; '
                            'the agent must run --reset-template-selection'
                        ),
                    }), 409
            else:
                write_selection = True
        else:
            if template_selection_payload is not None:
                return jsonify({
                    'error': 'template_selection is accepted only in Stage 1',
                }), 400
            stage2_error = _stage2_ready_error(
                project_path,
                confirm_dir,
                rec_file,
            )
            if stage2_error:
                return jsonify({
                    'error': f'Stage 2 is waiting for template handoff: {stage2_error}',
                }), 409
            try:
                template_required = _template_confirmation_required(project_path)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                return jsonify({
                    'error': f'cannot determine active template mode: {exc}',
                }), 409
        stage_error = _submission_stage_error(
            confirm_dir,
            stage,
            recommendations_file=rec_file,
            recommendations=current_recommendations,
            template_required=template_required,
        )
        if stage_error:
            return jsonify({'error': stage_error}), 409
        custom_error = _custom_selection_error(result)
        if custom_error:
            return jsonify({'error': custom_error}), 400
        previous_result = {}
        if rec_stage_number >= 2:
            try:
                previous_result = _read_json_object(result_file)
            except (OSError, json.JSONDecodeError, ValueError):
                pass
        main_language = None
        if rec_stage_number > 0:
            language_source = (
                previous_result
                if _recommendation_language(previous_result)
                else current_recommendations
            )
            if not _recommendation_language(language_source):
                language_source = result
            language_error = _canonicalize_primary_language(
                language_source,
                required=True,
            )
            if language_error:
                return jsonify({'error': language_error}), 409
            main_language = _recommendation_language(language_source)
            if main_language:
                result['primary_language'] = main_language
            else:
                result.pop('primary_language', None)
        if rec_stage_number == 2:
            solution_error = _stage2_solution_error(
                result,
                main_language=main_language,
            )
            if solution_error:
                return jsonify({'error': solution_error}), 400
        if rec_stage_number == 2:
            proactive_defaults, proactive_recommendation_error = (
                _resolve_proactive_execution_values(current_recommendations)
            )
            if proactive_recommendation_error:
                return jsonify({
                    'error': proactive_recommendation_error,
                }), 409
            proactive_result_error = _normalize_proactive_execution_result(
                result,
                proactive_defaults,
            )
            if proactive_result_error:
                return jsonify({'error': proactive_result_error}), 400
        _normalize_custom_selections(result)
        locked_values = _apply_locked_recommendations(
            result,
            rec_file,
            result_file,
            carry_previous=rec_stage_number > 1,
        )
        # Formula realization is Executor-owned. Accept the retired field from
        # older recommendations/clients, but never persist it in a new receipt.
        result.pop('formula_policy', None)
        locked_values.pop('formula_policy', None)
        if rec_stage_number == 1 or not template_required:
            result.pop('template_application', None)
            locked_values.pop('template_application', None)
        result.pop('template_reuse_scope', None)
        result.pop('template_adherence', None)
        if stage == 'stage1':
            result['stage'] = 'stage1'
            result['status'] = 'stage1-confirmed'
            if locked_values:
                result[_LOCKED_RECOMMENDATIONS_KEY] = locked_values
        else:
            result.pop(_LOCKED_RECOMMENDATIONS_KEY, None)
            result['stage'] = 'final'
            result['status'] = 'confirmed'
        result['confirmed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        if write_selection and selection_receipt is not None:
            _write_json_atomic(selection_file, selection_receipt)
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
        description='PPT Master template and Strategist confirmation UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('project_dir', help='Path to project directory')
    parser.add_argument(
        '--port', type=int, default=None,
        help=f'Exact port to listen on (default: first free port from {DEFAULT_PORT})',
    )
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    parser.add_argument(
        '--daemon', action='store_true',
        help='Start the server in the background; combine with --wait to block until confirmation',
    )
    parser.add_argument(
        '--wait', action='store_true',
        help='With --daemon, wait until the active result.json stage is written',
    )
    parser.add_argument(
        '--wait-only', action='store_true',
        help='Attach to the confirm server for this project and wait for an '
             'already-open page to write the requested receipt. If it is '
             'already persisted, return without recovery; otherwise recover a '
             'dead server on the recorded/default port so browser polling can resume.',
    )
    parser.add_argument(
        '--wait-stage', default='final', metavar='{stage1,final}',
        help='Wait for this result.json stage (default: final). Use stage1 '
             'after opening the combined template/communication page.',
    )
    parser.add_argument(
        '--wait-timeout', type=int, default=WAIT_TIMEOUT_DEFAULT,
        help=f'Seconds the wait caller blocks before returning (default: {WAIT_TIMEOUT_DEFAULT}; '
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
             'on its selected port before live preview starts.',
    )
    parser.add_argument(
        '--complete-template-selection', action='store_true',
        help='Agent-only: after Stage 1, bind its template selection to a ready '
             'handoff. Template mode requires at least one '
             '<project>/templates/design_spec.<kind>.<id>.md.',
    )
    parser.add_argument(
        '--reset-template-selection', action='store_true',
        help='Agent-only: remove exactly template_options.json, '
             'template_selection.json, and template_handoff.json before a '
             'fresh one-run UI lifecycle.',
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

    if args.port is not None:
        try:
            args.port = _validate_port(args.port)
        except ValueError as exc:
            logger.error('%s', exc)
            return 2

    project_path = Path(args.project_dir).resolve()
    if not project_path.is_dir():
        logger.error('%s is not a directory', project_path)
        return 1
    wait_stage = _stage_key(str(args.wait_stage).strip().lower())
    if wait_stage not in {'stage1', 'final'}:
        logger.error('--wait-stage must be stage1 or final')
        return 2

    template_control = (
        args.complete_template_selection
        or args.reset_template_selection
    )
    if template_control and (
        args.daemon or args.wait or args.wait_only or args.shutdown
    ):
        logger.error(
            '--complete-template-selection/--reset-template-selection cannot be combined '
            'with server, wait, or shutdown actions'
        )
        return 2
    if args.complete_template_selection and args.reset_template_selection:
        logger.error(
            '--complete-template-selection and --reset-template-selection are '
            'mutually exclusive'
        )
        return 2
    if args.complete_template_selection:
        return _complete_template_selection(project_path)
    if args.reset_template_selection:
        return _reset_template_selection(project_path / CONFIRM_DIR_NAME)

    # Step 4 cleanup: stop any lingering confirm server and exit. Independent of
    # recommendation files (the page may never have been confirmed).
    if args.shutdown:
        return _shutdown_existing(project_path / LOCK_FILE_NAME)

    # Staged wait: attach to the server launched by --daemon and block until
    # the page writes the requested Strategist receipt.
    if args.wait_only:
        lock_file = project_path / LOCK_FILE_NAME
        confirm_dir = project_path / CONFIRM_DIR_NAME
        result_file = confirm_dir / RESULT_NAME
        wait_status = _wait_result_status(result_file, wait_stage)
        if wait_status is not None:
            return wait_status
        if wait_stage == 'stage1':
            readiness_error = _stage1_ready_error(confirm_dir)
        else:
            recommendations_file = _active_recommendations_path(confirm_dir)
            readiness_error = _stage2_ready_error(
                project_path,
                confirm_dir,
                recommendations_file,
            )
        if readiness_error:
            logger.error(
                'confirmation stage=%s is not ready: %s',
                wait_stage,
                readiness_error,
            )
            return 1
        if not _live_lock(lock_file):
            launch_error = _confirmation_launch_error(confirm_dir)
            if launch_error:
                logger.error('%s', launch_error)
                return 1
            exact_port = args.port is not None
            recovery_port = (
                args.port
                if exact_port
                else _preferred_recovery_port(lock_file, DEFAULT_PORT)
            )
            try:
                _, actual_port, _ = _launch_background_server(
                    project_path,
                    preferred_port=recovery_port,
                    exact_port=exact_port,
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
            result_file,
            lock_file,
            args.wait_timeout,
            wait_stage,
        )

    confirm_dir = project_path / CONFIRM_DIR_NAME
    launch_error = _confirmation_launch_error(confirm_dir)
    if launch_error:
        logger.error('%s', launch_error)
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
                preferred_port=args.port if args.port is not None else DEFAULT_PORT,
                exact_port=args.port is not None,
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

    try:
        port = args.port if args.port is not None else _find_free_port(DEFAULT_PORT)
    except RuntimeError as exc:
        logger.error('%s', exc)
        return 1

    # Per-project mutual exclusion: refuse duplicate launches. Stale locks
    # (dead pid) are overwritten by _claim_lock.
    lock_file = project_path / LOCK_FILE_NAME
    existing = _claim_lock(lock_file, port)
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
        server_port=port,
    )

    url = _server_url(port)
    if not args.no_browser:
        _open_browser_async(url)

    logger.info('running at %s', url)
    logger.info('project: %s', project_path)
    logger.info('idle timeout: %ds (0 = disabled)', args.timeout)
    app.run(host=PUBLIC_HOST, port=port, debug=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
