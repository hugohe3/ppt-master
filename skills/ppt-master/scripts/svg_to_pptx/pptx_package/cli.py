"""CLI entry point for svg_to_pptx."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from attribution_guard import require_skill_integrity  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402
from language_tags import (  # noqa: E402
    LanguageTagError,
    normalize_language_tag,
)
from native_payloads import PAYLOAD_STORE_RELATIVE_PATH  # noqa: E402
from pptx_animations import (  # noqa: E402
    ANIMATIONS,
    animation_seconds_to_milliseconds,
    normalize_animation_effect,
    normalize_animation_trigger,
)
from pptx_transitions import (  # noqa: E402
    LEGACY_TRANSITION_KEYS,
    NATIVE_TRANSITION_KEYS,
    normalize_transition_effect_request,
    validate_seconds,
)

configure_utf8_stdio()

if __package__ in {None, ''}:
    import types

    package = types.ModuleType('svg_to_pptx')
    package.__path__ = [str(Path(__file__).resolve().parent)]  # type: ignore[attr-defined]
    sys.modules.setdefault('svg_to_pptx', package)
    __package__ = 'svg_to_pptx'

from .dimensions import CANVAS_FORMATS, get_project_info
from .discovery import NotesFileReadError, find_notes_files, find_svg_files
from .builder import create_pptx_with_native_svg
from ..native_objects import (
    native_fallback_kind,
    native_replacement_kind,
    native_replacement_status,
)
from ..native_objects.marker_status import native_marker_release_block_reason
from ..drawingml.theme_colors import ThemeColorError, load_theme_color_spec
from ..drawingml.context import (
    TEXT_FLOW_PRESERVE,
    TEXT_FLOW_REFLOW,
    TEXT_FLOW_SPLIT,
)
from ..drawingml.theme_fonts import (
    ThemeFontError,
    load_master_text_style_spec,
    load_theme_font_spec,
)
from ..drawingml.utils import unsafe_exported_font_faces
from .narration import (
    DEFAULT_NARRATION_START_FLOOR,
    NARRATION_EXTENSIONS,
    find_narration_files,
    probe_audio_duration,
)
from .template_structure import (
    TemplateStructureError,
    load_pptx_structure_lock,
    parse_template_slides,
    structured_layout_definition_files,
    template_lock_errors,
    template_prototype_errors,
)
from ..animation_config import (
    animation_group_effect_entries,
    load_animation_config,
    validate_animation_config,
    validate_animation_config_errors,
    validate_transition_config,
)


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


_PPTX_STRUCTURE_SECTION_RE = re.compile(
    r"(?ms)^##[ \t]+pptx_structure[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)"
)
_PPTX_STRUCTURE_MODE_RE = re.compile(
    r"(?m)^-[ \t]+mode[ \t]*:[ \t]*([^#\r\n]*?)[ \t]*(?:#.*)?$"
)
_LEGACY_PPTX_STRUCTURE_MODES = frozenset({
    'baseline',
    'generated',
    'preserve',
    'template',
})
_RELEASE_PPTX_STRUCTURE_MODES = frozenset({'flat', 'structured'})
_CSS_GENERIC_FONT_FAMILIES = frozenset({
    'cursive',
    'emoji',
    'fangsong',
    'fantasy',
    'math',
    'monospace',
    'sans-serif',
    'serif',
    'system-ui',
    'ui-monospace',
    'ui-rounded',
    'ui-sans-serif',
    'ui-serif',
})


class PptxPostflightValidationError(RuntimeError):
    """Reject a generated PPTX that fails package postflight validation."""


@dataclass
class _PostflightReceipt:
    """Carry the compact export result printed after the audit is written."""

    output_path: Path
    report_path: Path
    status: str
    quality_gate: str
    slide_count: int
    warnings: tuple[str, ...]


def _font_stack_is_generic_only(stack: str) -> bool:
    """Return whether a CSS font stack contains no concrete family name."""
    families = [
        family.strip().strip('"\'').strip().lower()
        for family in stack.split(',')
        if family.strip().strip('"\'').strip()
    ]
    return bool(families) and all(
        family in _CSS_GENERIC_FONT_FAMILIES
        for family in families
    )


def _package_part_counts(pptx_path: Path) -> dict[str, object]:
    """Count public and structural OOXML parts in a completed PPTX package."""
    with zipfile.ZipFile(pptx_path) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()

    def count(pattern: str) -> int:
        matcher = re.compile(pattern)
        return sum(bool(matcher.fullmatch(name)) for name in names)

    return {
        'zip_integrity': 'passed' if bad_member is None else 'failed',
        'corrupt_member': bad_member,
        'slides': count(r'ppt/slides/slide\d+\.xml'),
        'notes': count(r'ppt/notesSlides/notesSlide\d+\.xml'),
        'masters': count(r'ppt/slideMasters/slideMaster\d+\.xml'),
        'layouts': count(r'ppt/slideLayouts/slideLayout\d+\.xml'),
    }


def _source_resource_audit(svg_files: list[Path]) -> dict[str, object]:
    """Collect unresolved tokens and portability-oriented source inventories."""
    placeholder_re = re.compile(r'\{\{[^{}]+\}\}')
    placeholders: list[dict[str, str]] = []
    font_stacks: set[str] = set()
    image_counts = {
        'data_uri': 0,
        'local': 0,
        'external': 0,
    }
    external_images: list[dict[str, str]] = []
    for svg_path in svg_files:
        try:
            content = svg_path.read_text(encoding='utf-8')
            root = ET.fromstring(content)
        except (OSError, ET.ParseError):
            continue
        for token in sorted(set(placeholder_re.findall(content))):
            placeholders.append({'file': svg_path.name, 'token': token})
        for element in root.iter():
            font_family = element.get('font-family')
            if font_family:
                font_stacks.add(font_family.strip())
            style = element.get('style') or ''
            for declaration in style.split(';'):
                if ':' not in declaration:
                    continue
                name, value = declaration.split(':', 1)
                if name.strip().lower() == 'font-family' and value.strip():
                    font_stacks.add(value.strip())
            if element.tag.rsplit('}', 1)[-1] != 'image':
                continue
            href = (
                element.get('href')
                or element.get('{http://www.w3.org/1999/xlink}href')
                or ''
            ).strip()
            if href.startswith('data:'):
                image_counts['data_uri'] += 1
            elif re.match(r'^[a-z][a-z0-9+.-]*://', href, re.IGNORECASE):
                image_counts['external'] += 1
                external_images.append({
                    'file': svg_path.name,
                    'href': href,
                })
            elif href:
                image_counts['local'] += 1
    generic_only_font_stacks = sorted({
        stack
        for stack in font_stacks
        if _font_stack_is_generic_only(stack)
    })
    unsafe_font_faces = [
        {
            'stack': stack,
            'role': role,
            'typeface': typeface,
        }
        for stack in sorted(font_stacks)
        for role, typeface in unsafe_exported_font_faces(stack).items()
    ]
    return {
        'unresolved_template_tokens': placeholders,
        'fonts': {
            'stacks': sorted(font_stacks),
            'generic_only_stacks': generic_only_font_stacks,
            'unsafe_exported_faces': unsafe_font_faces,
        },
        'images': {
            **image_counts,
            'external_references': external_images,
        },
    }


def _svg_source_fingerprint(svg_files: list[Path]) -> dict[str, object]:
    """Return one deterministic digest for the exact SVG export inputs."""
    files: list[dict[str, object]] = []
    aggregate = hashlib.sha256()
    for path in sorted(svg_files, key=lambda item: item.name):
        file_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({'file': path.name, 'sha256': file_sha256})
        aggregate.update(path.name.encode('utf-8'))
        aggregate.update(b'\0')
        aggregate.update(file_sha256.encode('ascii'))
        aggregate.update(b'\n')
    return {
        'algorithm': 'sha256',
        'digest': aggregate.hexdigest(),
        'file_count': len(files),
        'files': files,
    }


def _quality_report_context(
    project_path: Path,
    source_fingerprint: dict[str, object],
) -> dict[str, object]:
    """Load the final SVG quality report when the preceding gate wrote one."""
    quality_path = project_path / 'validation' / 'svg_quality_report.json'
    try:
        quality = json.loads(quality_path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {'status': 'not-provided', 'path': str(quality_path)}
    except (OSError, json.JSONDecodeError) as exc:
        return {
            'status': 'unreadable',
            'path': str(quality_path),
            'error': str(exc),
        }
    schema = quality.get('schema')
    if schema != 'ppt-master.svg-quality-report.v1':
        return {
            'status': 'unsupported-schema',
            'path': str(quality_path),
            'schema': schema,
        }
    categories = quality.get('categories')
    quality_fingerprint = quality.get('source_fingerprint')
    if not isinstance(quality_fingerprint, dict):
        source_match = 'unavailable'
    elif (
        quality_fingerprint.get('algorithm') == 'sha256'
        and quality_fingerprint.get('digest') == source_fingerprint.get('digest')
        and quality_fingerprint.get('file_count')
        == source_fingerprint.get('file_count')
    ):
        source_match = 'passed'
    else:
        source_match = 'mismatch'
    return {
        'status': 'loaded',
        'path': str(quality_path),
        'schema': schema,
        'stage': quality.get('stage'),
        'source_match': source_match,
        'source_fingerprint': quality_fingerprint,
        'summary': quality.get('summary'),
        'categories': categories if isinstance(categories, dict) else {},
    }


def _quality_gate_status(
    quality: dict[str, object],
) -> tuple[str, int]:
    """Return final-gate status and introduced-warning count."""
    categories = quality.get('categories')
    blocking_count = None
    introduced_warning_count = 0
    if isinstance(categories, dict):
        blocking = categories.get('blocking')
        if isinstance(blocking, dict):
            blocking_count = blocking.get('count')
        introduced = categories.get('introduced')
        if (
            isinstance(introduced, dict)
            and isinstance(introduced.get('count'), int)
        ):
            introduced_warning_count = int(introduced['count'])
    if quality.get('status') != 'loaded':
        return str(quality.get('status') or 'not-provided'), introduced_warning_count
    if quality.get('stage') != 'final':
        return 'non-final', introduced_warning_count
    if not isinstance(blocking_count, int):
        return 'unverified', introduced_warning_count
    if blocking_count > 0:
        return 'failed', introduced_warning_count
    if quality.get('source_match') == 'mismatch':
        return 'stale', introduced_warning_count
    if quality.get('source_match') != 'passed':
        return 'unverified', introduced_warning_count
    return 'passed', introduced_warning_count


def _postflight_warning_summaries(
    *,
    quality_gate: str,
    introduced_warning_count: int,
    unresolved_token_count: int,
    external_image_count: int,
    generic_font_stack_count: int,
    unsafe_font_face_count: int,
) -> tuple[str, ...]:
    """Return stable warning summaries for the terminal receipt."""
    warnings: list[str] = []
    if quality_gate != 'passed':
        warnings.append(f'quality_gate={quality_gate}')
    if introduced_warning_count:
        warnings.append(f'quality_introduced_warnings={introduced_warning_count}')
    if unresolved_token_count:
        warnings.append(f'unresolved_template_tokens={unresolved_token_count}')
    if external_image_count:
        warnings.append(f'external_images={external_image_count}')
    if generic_font_stack_count:
        warnings.append(f'generic_only_font_stacks={generic_font_stack_count}')
    if unsafe_font_face_count:
        warnings.append(f'unsafe_exported_font_faces={unsafe_font_face_count}')
    return tuple(warnings)


def _write_postflight_report(
    *,
    output_path: Path,
    project_path: Path,
    svg_files: list[Path],
    layout_definition_files: list[Path],
    pptx_structure: str,
    backup_path: Path | None,
    conversion_trace_path: Path | None,
    deck_motion: dict[str, object],
) -> _PostflightReceipt:
    """Write the unified package/resource audit for a successful PPTX."""
    try:
        package = _package_part_counts(output_path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise PptxPostflightValidationError(
            f"generated PPTX is not a readable ZIP package: {exc}"
        ) from exc
    if package['zip_integrity'] != 'passed':
        raise PptxPostflightValidationError(
            f"PPTX ZIP integrity failed at {package['corrupt_member']}"
        )
    if package['slides'] != len(svg_files):
        raise PptxPostflightValidationError(
            "Published Slide count does not match authored SVG count: "
            f"{package['slides']} != {len(svg_files)}"
        )
    source_audit = _source_resource_audit(svg_files)
    source_fingerprint = _svg_source_fingerprint(svg_files)
    quality = _quality_report_context(project_path, source_fingerprint)
    quality_gate, introduced_warning_count = _quality_gate_status(quality)
    unresolved_tokens = source_audit['unresolved_template_tokens']
    external_image_count = source_audit['images']['external']
    generic_only_font_stacks = source_audit['fonts']['generic_only_stacks']
    unsafe_font_faces = source_audit['fonts']['unsafe_exported_faces']
    if quality_gate == 'failed':
        report_status = 'failed'
    elif (
        not unresolved_tokens
        and not external_image_count
        and not generic_only_font_stacks
        and not unsafe_font_faces
        and not introduced_warning_count
        and quality_gate == 'passed'
    ):
        report_status = 'passed'
    else:
        report_status = 'passed-with-warnings'
    report_path = (
        project_path / 'validation' / f'{output_path.stem}.report.json'
    )
    report = {
        'schema': 'ppt-master.pptx-postflight-report.v1',
        'status': report_status,
        'output': {
            'path': str(output_path.resolve()),
            'bytes': output_path.stat().st_size,
        },
        'source': {
            'svg_slide_count': len(svg_files),
            'layout_definition_count': len(layout_definition_files),
            'fingerprint': source_fingerprint,
        },
        'package': package,
        'checks': {
            'zip_integrity': 'passed',
            'slide_count': 'passed',
            'internal_relationships': 'enforced-at-build',
            'structured_package': (
                'enforced-at-build'
                if pptx_structure == 'structured'
                else 'not-applicable'
            ),
            'transitions': 'enforced-at-build',
            'animations': 'enforced-at-build',
            'quality_gate': quality_gate,
            'quality_warnings': (
                'passed' if not introduced_warning_count else 'warning'
            ),
            'template_tokens': (
                'passed' if not unresolved_tokens else 'warning'
            ),
            'external_images': (
                'passed' if not external_image_count else 'warning'
            ),
            'font_portability': (
                'passed'
                if not generic_only_font_stacks and not unsafe_font_faces
                else 'warning'
            ),
        },
        'quality': quality,
        'resources': source_audit,
        'deck_motion': deck_motion,
        'backup_path': str(backup_path.resolve()) if backup_path else None,
        'conversion_trace_path': (
            str(conversion_trace_path.resolve())
            if conversion_trace_path and conversion_trace_path.is_file()
            else None
        ),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    warnings = _postflight_warning_summaries(
        quality_gate=quality_gate,
        introduced_warning_count=introduced_warning_count,
        unresolved_token_count=len(unresolved_tokens),
        external_image_count=external_image_count,
        generic_font_stack_count=len(generic_only_font_stacks),
        unsafe_font_face_count=len(unsafe_font_faces),
    )
    return _PostflightReceipt(
        output_path=output_path,
        report_path=report_path,
        status=report_status,
        quality_gate=quality_gate,
        slide_count=int(package['slides']),
        warnings=warnings,
    )


def _load_deck_motion_handoff(
    project_path: Path,
    report_arg: str,
    svg_files: list[Path],
) -> dict[str, object]:
    """Load source-bound deck motion from a successful base export report."""
    report_path = Path(report_arg).expanduser()
    if not report_path.is_absolute() and not report_path.is_file():
        report_path = project_path / report_path
    try:
        report = json.loads(report_path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ValueError(
            f'deck-motion handoff report does not exist: {report_path}'
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f'deck-motion handoff report is unreadable: {report_path}: {exc}'
        ) from exc
    if not isinstance(report, dict):
        raise ValueError('deck-motion handoff report must be a JSON object')
    if report.get('schema') != 'ppt-master.pptx-postflight-report.v1':
        raise ValueError(
            'deck-motion handoff requires a ppt-master postflight report'
        )
    if report.get('status') not in {'passed', 'passed-with-warnings'}:
        raise ValueError('deck-motion handoff report is not a successful export')
    source = _as_dict(report.get('source'))
    if source.get('fingerprint') != _svg_source_fingerprint(svg_files):
        raise ValueError(
            'deck-motion handoff does not match the current svg_output; '
            'run the base export again'
        )
    motion = report.get('deck_motion')
    if not isinstance(motion, dict):
        raise ValueError(
            'deck-motion handoff is missing from the base export report; '
            'run the base export again'
        )
    if motion.get('narration_timings') is True:
        raise ValueError(
            'deck-motion handoff must reference a base non-narrated export report'
        )
    if not isinstance(motion.get('transition'), dict):
        raise ValueError('deck-motion handoff transition must be an object')
    if not isinstance(motion.get('animation'), dict):
        raise ValueError('deck-motion handoff animation must be an object')
    if not isinstance(motion.get('cli_overrides'), dict):
        raise ValueError('deck-motion handoff cli_overrides must be an object')
    return motion


def _print_postflight_receipt(receipt: _PostflightReceipt) -> None:
    """Print the compact completion evidence; keep the full JSON on disk."""
    print(
        '  [POSTFLIGHT] '
        f'status={receipt.status} '
        f'quality_gate={receipt.quality_gate} '
        f'slides={receipt.slide_count} '
        f'warning_categories={len(receipt.warnings)}'
    )
    for warning in receipt.warnings:
        print(f'  [POSTFLIGHT][WARNING] {warning}')
    print(f'  [PPTX] {receipt.output_path}')
    print(f'  [REPORT] {receipt.report_path}')


def _declared_pptx_structure_mode(project_path: Path) -> str | None:
    """Return the explicitly locked SVG export mode, if the lock declares one."""
    lock_path = project_path / 'spec_lock.md'
    try:
        content = lock_path.read_text(encoding='utf-8')
    except OSError:
        return None
    section_match = _PPTX_STRUCTURE_SECTION_RE.search(content)
    if section_match is None:
        return None
    mode_match = _PPTX_STRUCTURE_MODE_RE.search(section_match.group(1))
    return mode_match.group(1).strip().lower() if mode_match else None


def _declared_canvas_viewbox(project_path: Path) -> str | None:
    """Return the project-lock root canvas without inferring from its name."""
    lock_path = project_path / 'spec_lock.md'
    try:
        from update_spec import parse_lock

        lock = parse_lock(lock_path)
    except (OSError, ValueError):
        return None
    canvas = lock.get('canvas', {})
    value = canvas.get('viewBox')
    return value.strip() if isinstance(value, str) and value.strip() else None


def _declared_primary_language(project_path: Path) -> str | None:
    """Return the canonical content language declared by the execution lock."""
    lock_path = project_path / 'spec_lock.md'
    try:
        from update_spec import parse_lock

        lock = parse_lock(lock_path)
    except (OSError, ValueError):
        return None
    communication = lock.get('communication', {})
    value = communication.get('primary_language')
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return normalize_language_tag(value)
    except LanguageTagError as exc:
        raise LanguageTagError(
            'spec_lock.md communication.primary_language '
            f'is invalid: {exc}'
        ) from exc


def _print_structure_contract_error(
    mode: str | None,
    *,
    requested_mode: str | None = None,
) -> None:
    """Explain an unsupported mode or a structured-export lock mismatch."""
    label = repr(mode) if mode is not None else 'missing'
    if requested_mode == 'structured':
        print(
            "Error: --pptx-structure structured requires an explicit "
            "spec_lock.md pptx_structure.mode: structured contract; found "
            + label + ".",
            file=sys.stderr,
        )
        print(
            "  A legacy lock without pptx_structure.mode defaults only to flat. "
            "Mirror/layout reuse must first create a current template workspace "
            "through skills/ppt-master/workflows/create-template.md, then generate "
            "new structured SVG pages.",
            file=sys.stderr,
        )
        return
    print(
        "Error: unsupported spec_lock.md pptx_structure.mode " + label + ". "
        "Current release modes are flat (style reference / free design / "
        "brand-only) and structured (mirror/layout reuse).",
        file=sys.stderr,
    )
    print(
        "  A legacy lock with no pptx_structure.mode defaults to flat. "
        "Explicit legacy or unknown values are not inferred. Mirror/layout reuse "
        "must first create a current template workspace "
        "through skills/ppt-master/workflows/create-template.md, then generate "
        "new structured SVG pages.",
        file=sys.stderr,
    )


def _native_object_fallbacks(svg_files: list[Path]) -> list[tuple[str, str, str]]:
    """Return fallback-only chart/table replacement statuses from SVG inputs."""
    fallbacks: list[tuple[str, str, str]] = []
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError):
            continue
        for elem in root.iter():
            status = native_replacement_status(elem)
            if not status or elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            fallbacks.append((svg_path.name, marker_id, status))
    return fallbacks


def _release_blocked_graphics(
    svg_files: list[Path],
) -> list[tuple[str, str, str]]:
    """Return graphics whose status metadata is invalid."""
    blocked: list[tuple[str, str, str]] = []
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError):
            continue
        for elem in root.iter():
            if elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            reason = native_marker_release_block_reason(elem)
            if reason is None:
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            blocked.append((svg_path.name, marker_id, reason))
    return blocked


def _reconstruction_only_graphics(
    svg_files: list[Path],
) -> list[tuple[str, str, bool]]:
    """Return valid placeholder routes for non-blocking diagnostics."""
    diagnostics: list[tuple[str, str, bool]] = []
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError):
            continue
        for elem in root.iter():
            if elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            if native_fallback_kind(elem) != 'placeholder':
                continue
            if native_marker_release_block_reason(elem) is not None:
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            active_native = bool(native_replacement_kind(elem))
            diagnostics.append((svg_path.name, marker_id, active_native))
    return diagnostics


def _recorded_narration_on_click_slides(
    ref_files: list[Path],
    animation_config: dict | None,
    animation: str | None,
    animation_trigger: str,
    animation_cli_overrides: dict[str, bool],
) -> list[str]:
    """Return slides whose effective recorded-video animation trigger is on-click."""
    if animation_cli_overrides.get('animation') and animation is None:
        return []
    slides_cfg = _as_dict(_as_dict(animation_config).get('slides'))
    blocked: list[str] = []
    for svg_path in ref_files:
        slide_cfg = _as_dict(slides_cfg.get(svg_path.stem))
        anim_cfg = _as_dict(slide_cfg.get('animation'))

        slide_animation = animation
        if not animation_cli_overrides.get('animation') and 'effect' in anim_cfg:
            slide_animation = normalize_animation_effect(anim_cfg.get('effect'))
        slide_trigger = animation_trigger
        if (
            not animation_cli_overrides.get('animation_trigger')
            and anim_cfg.get('trigger')
        ):
            slide_trigger = normalize_animation_trigger(anim_cfg.get('trigger'))

        groups_cfg = _as_dict(slide_cfg.get('groups'))
        has_interactive_animation = False
        for group_id, group_cfg in groups_cfg.items():
            if not isinstance(group_cfg, dict):
                continue
            group_path = (
                f'slides[{json.dumps(svg_path.stem, ensure_ascii=False)}]'
                f'.groups[{json.dumps(str(group_id), ensure_ascii=False)}]'
            )
            for _effect_path, effect_cfg in animation_group_effect_entries(
                group_cfg,
                path=group_path,
            ):
                row_effect = (
                    normalize_animation_effect(effect_cfg.get('effect'))
                    if 'effect' in effect_cfg
                    else slide_animation
                )
                if row_effect is None:
                    continue
                row_trigger = (
                    normalize_animation_trigger(effect_cfg.get('trigger'))
                    if effect_cfg.get('trigger')
                    else slide_trigger
                )
                if effect_cfg.get('trigger_shape') is not None:
                    has_interactive_animation = True
                    break
                if row_trigger == 'on-click':
                    has_interactive_animation = True
                    break
            if has_interactive_animation:
                break

        if has_interactive_animation or (
            slide_animation is not None and slide_trigger == 'on-click'
        ):
            blocked.append(svg_path.stem)
    return blocked


def _resolve_animation_config_source(
    project_path: Path,
    requested_config: str | None,
    *,
    recorded_narration: bool,
    no_animations: bool,
) -> str | None:
    """Resolve the animation sidecar selected for this export."""
    if requested_config is not None or not recorded_narration or no_animations:
        return requested_config

    canonical_exists = (project_path / 'animations.json').is_file()
    narration_exists = (project_path / 'narration_animations.json').is_file()
    if canonical_exists or narration_exists:
        return 'narration_animations.json'
    return None


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the SVG to PPTX conversion tool."""
    require_skill_integrity()
    transition_choices = [
        'none',
        *NATIVE_TRANSITION_KEYS,
        *LEGACY_TRANSITION_KEYS,
    ]

    animation_choices = ['none', *ANIMATIONS, 'auto', 'mixed', 'random']

    parser = argparse.ArgumentParser(
        description='PPT Master - SVG to native DrawingML PPTX Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
    %(prog)s examples/ppt169_demo                         # Default: native pptx -> exports/, svg_output -> backup/<ts>/
    %(prog)s examples/ppt169_demo -o out.pptx            # Explicit path (no backup/)
    %(prog)s projects/quick_generate_demo --quick-generate # Lockless flat export with normal postflight

    # Disable transition / change transition effect
    %(prog)s examples/ppt169_demo -t none
    %(prog)s examples/ppt169_demo -t push --transition-duration 1.0

SVG source directory (-s):
    output   - svg_output (hand-authored source; native default)
    final    - svg_final (post-processed preview; diagnostic native input only)
    <any>    - Specify a subdirectory name directly
    Omit -s to use the default: native export reads svg_output.

Transition effects (-t/--transition):
    New selections use the 48 PowerPoint-native gallery keys. The 8 old
    names remain accepted only as compatibility inputs. Run
    scripts/pptx_animations.py --list for the categorized registry and
    --describe-transition <effect> for its Effect Options.

Per-element object animation (-a/--animation, native shapes mode):
    Use PowerPoint-native entrance_*, emphasis_*, path_*, and exit_* keys for
    new animation choices. The 29 old short names remain accepted only as
    compatibility inputs. Run scripts/pptx_animations.py --list for the
    complete categorized 232-key input registry.
    Notes: applied to top-level <g id="..."> SVG groups in z-order. Default is
           "none" (no auto element builds; page transitions still apply). Use
           "-a auto" to map effects from group id: chart→entrance_wipe,
           card-/step-/pillar-→entrance_fly,
           title/takeaway→entrance_fade; image-like ids
           hero/figure-/image/img-/kpi cycle canonical entrance presets;
           unmatched ids cycle entrance_fade/entrance_wipe/entrance_fly/
           entrance_zoom. Start mode set by --animation-trigger, matching
           PowerPoint's Start dropdown:
             on-click              one presenter click per group
             with-previous         all groups start together on slide entry
             after-previous (default)  cascade on slide entry;
                                       gap = --animation-stagger seconds
           mixed (compatible mode name) cycles a larger 16-preset canonical
           PowerPoint entrance pool by group order; random samples from the
           same entrance pool. Use explicit canonical keys for emphasis,
           motion-path, or exit duties. Use "-a none" to disable element
           builds explicitly.

Speaker notes:
    - Automatically reads Markdown notes files from the notes/ directory
    - Supports two naming conventions:
      1. Match by filename (recommended): 01_cover.md corresponds to 01_cover.svg
      2. Match by index: slide01.md corresponds to the 1st SVG (backward compatible)
    - Enabled by default outside Quick Generate; use --no-notes to disable
    - Disabled by default in Quick Generate; use --with-notes to enable

Recorded narration:
    %(prog)s examples/ppt169_demo --recorded-narration audio \\
      --inherit-motion-from validation/<base>.report.json
    - Keeps speaker notes when enabled
    - Prepares PowerPoint recorded timings and narrations
    - Requires one m4a/mp3/wav file per slide
    - Uses narration_animations.json when animation sidecars exist
    - Inherits source-bound deck motion from the base postflight report
    - Use --animation-config animations.json for the canonical animation
    - Use --no-animations for narration and timings without animation motion
    - Embeds per-slide audio matched by SVG filename / slide number
    - Sets slide auto-advance from audio duration so video export can use
      "recorded timings and narrations"
    - Rejects on-click object animations; use after-previous or with-previous
    %(prog)s examples/ppt169_demo --narration-audio-dir audio
    - Lower-level audio embedding: embeds matched files but allows partial matches
    - Use only when you do not need a complete recorded-timings export
''',
    )

    parser.add_argument('project_path', type=str, help='Project directory path')
    parser.add_argument('-o', '--output', type=str, default=None, help='Output file path')
    parser.add_argument('-s', '--source', type=str, default=None,
                        help='Native SVG source directory. Default: svg_output/. '
                             'Pass output/final/<name> only for diagnostics.')
    parser.add_argument('-f', '--format', type=str,
                        choices=list(CANVAS_FORMATS.keys()), default=None,
                        help='Require SVG canvases to match this registered format')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    parser.add_argument(
        '--quick-generate',
        action='store_true',
        help=(
            'Export a Quick Generate SVG roster from svg_output/ without '
            'spec_lock.md. Require a matching final quality report, infer one '
            'consistent canvas, use a flat package with converter defaults, '
            'and support normal export capabilities.'
        ),
    )

    text_flow_group = parser.add_mutually_exclusive_group()
    text_flow_group.add_argument(
        '--reflow-text',
        action='store_const',
        const=TEXT_FLOW_REFLOW,
        dest='text_flow',
        help=(
            'Let PowerPoint automatically reflow conservative dy-stacked text '
            'inside one editable text frame.'
        ),
    )
    text_flow_group.add_argument(
        '--merge-paragraphs',
        action='store_const',
        const=TEXT_FLOW_REFLOW,
        dest='text_flow',
        help='Compatibility alias for --reflow-text.',
    )
    text_flow_group.add_argument(
        '--no-merge',
        action='store_const',
        const=TEXT_FLOW_SPLIT,
        dest='text_flow',
        help=(
            'Emit every positioned visual line as its own text frame for '
            'strict per-line SVG positioning.'
        ),
    )
    parser.set_defaults(text_flow=TEXT_FLOW_PRESERVE)
    parser.add_argument(
        '--conversion-trace',
        nargs='?',
        const='',
        default=None,
        metavar='PATH',
        help='Write per-slide SVG conversion diagnostics. Without PATH, write '
             '<project>/validation/<output_stem>.trace.json; relative PATHs '
             'are resolved from the project root.',
    )
    parser.add_argument(
        '--native-charts-and-tables',
        dest='native_objects',
        action='store_true',
        default=False,
        help=(
            'Replace explicit data-pptx-replace-with chart/table groups with '
            'PowerPoint native Chart/Table objects. This data-object route may '
            'normalize styling or omit fallback-only visuals. Default off: groups '
            'export as editable SVG-derived DrawingML shapes. The default-flow '
            'output uses <project>_<ts>_native_charts_tables.pptx.'
        ),
    )
    parser.add_argument(
        '--native-objects',
        dest='native_objects',
        action='store_true',
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--pptx-structure',
        choices=[
            'structured',
            'flat',
            'baseline',
            'template',
            'preserve',
            'generated',
        ],
        default=None,
        help=(
            'PPTX structure strategy for native export. Omitting this flag reads '
            'spec_lock.md; a legacy lock without pptx_structure.mode defaults to '
            'flat. Flat is the style-reference/free-design/brand-only release mode and '
            'builds one clean project-owned Master plus Blank Layout while keeping '
            'all SVG objects slide-local; structured is the mirror/layout reuse '
            'mode and requires complete explicit metadata. baseline, template, '
            'preserve, and generated are accepted only to report a migration error.'
        ),
    )
    parser.add_argument('--no-image-optimize', action='store_true',
                        help='Disable native PPTX raster image optimization and always embed '
                             'the original image bytes.')
    parser.add_argument('--image-max-dimension', type=int, default=2560,
                        help='Preferred raster cap in pixels. Cap mode re-encodes only images '
                             'that require resizing or EXIF geometry normalization, and may '
                             'retain more pixels for cropped/stretched visible resolution '
                             '(default: 2560).')
    parser.add_argument('--image-sizing', choices=['cap', 'display'], default='cap',
                        help='Raster sizing mode: cap preserves original bytes unless resizing '
                             'or EXIF geometry normalization is required; display targets the '
                             'SVG rendered box for explicit compaction (default: cap).')
    parser.add_argument('--image-scale', type=float, default=2.0,
                        help='Target optimized image pixels per SVG display pixel '
                             'when --image-sizing=display (default: 2.0).')
    parser.add_argument('--image-quality', type=int, default=85,
                        help='JPEG quality for raster images re-encoded during optimization, '
                             '1-100 (default: 85).')

    def non_negative_float(value: str) -> float:
        try:
            number = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"must be a number: {value}") from exc
        if not math.isfinite(number):
            raise argparse.ArgumentTypeError("must be finite")
        if number < 0:
            raise argparse.ArgumentTypeError("must be non-negative")
        return number

    def positive_float(value: str) -> float:
        number = non_negative_float(value)
        if number <= 0:
            raise argparse.ArgumentTypeError("must be greater than zero")
        return number

    parser.add_argument('-t', '--transition', type=str, choices=transition_choices, default=None,
                        help='Page transition effect (default: fade; "none" removes visual motion)')
    parser.add_argument('--transition-duration', type=non_negative_float, default=None,
                        help='Transition duration in seconds (default: 0.4)')
    parser.add_argument('--auto-advance', type=non_negative_float, default=None,
                        help='Auto-advance interval in seconds (default: manual advance)')

    parser.add_argument('-a', '--animation', type=str, choices=animation_choices,
                        default=None,
                        help='Per-element object animation (native shapes mode '
                             'only). Default "none" (no auto element builds; page '
                             'transitions still apply). Pick a native entrance_*/'
                             'emphasis_*/path_*/exit_* key or "auto" '
                             '(map effect from group id — image-like ids cycle a '
                             'richer canonical pool for visual variation, fallback '
                             'cycles entrance_fade/entrance_wipe/entrance_fly/'
                             'entrance_zoom), "mixed" (canonical 16-preset entrance '
                             'pool), or "random" (the same entrance pool). Use '
                             'explicit keys for emphasis/path/exit. Legacy short '
                             'names remain accepted only for compatibility.')
    parser.add_argument('--animation-duration', type=positive_float, default=None,
                        help='Per-element object-animation duration in seconds '
                             '(default: 0.4; instantaneous native presets keep their '
                             'PowerPoint-authored duration)')
    parser.add_argument('--animation-trigger', type=str,
                        choices=['on-click', 'with-previous', 'after-previous'],
                        default=None,
                        help='Per-element Start mode (matches PowerPoint Start dropdown): '
                             '"on-click" (one click per element), '
                             '"with-previous" (all start together on slide entry), '
                             '"after-previous" (default, cascade after the previous element).')
    parser.add_argument('--animation-stagger', type=non_negative_float, default=None,
                        help='Delay between elements in --animation-trigger=after-previous '
                             '(seconds, default 0.5). Ignored in other modes.')
    animation_source = parser.add_mutually_exclusive_group()
    animation_source.add_argument(
        '--animation-config',
        type=str,
        default=None,
        help=(
            'Per-slide/per-object animation config. Recorded narration uses '
            '<project>/narration_animations.json when an animation sidecar exists, '
            'or may inherit base postflight motion with --inherit-motion-from. '
            'Other exports default to <project>/animations.json when present.'
        ),
    )
    animation_source.add_argument(
        '--no-animations',
        action='store_true',
        help=(
            'Export without object animations or page-transition motion. '
            'Narration audio and slide advance timings are preserved.'
        ),
    )

    notes_mode = parser.add_mutually_exclusive_group()
    notes_mode.add_argument(
        '--with-notes',
        action='store_true',
        help='Embed speaker notes. Required to opt in during Quick Generate.',
    )
    notes_mode.add_argument(
        '--no-notes',
        action='store_true',
        help='Disable speaker notes embedding (enabled by default outside Quick Generate)',
    )
    parser.add_argument('--narration-audio-dir', type=str, default=None,
                        help='Low-level audio embedding from this directory; allows partial matches. '
                             'Default-flow exports get the _narrated name suffix.')
    parser.add_argument('--use-narration-timings', action='store_true',
                        help='Set slide auto-advance timings from narration audio durations')
    parser.add_argument('--recorded-narration', type=str, default=None,
                        help='Prepare PowerPoint recorded timings and narrations from a complete audio '
                             'directory. Default-flow exports get the _narrated name suffix '
                             '(<project>_<ts>_narrated.pptx) to tell them apart from silent exports.')
    parser.add_argument('--narration-padding', type=non_negative_float, default=0.5,
                        help='Seconds to add after each narration before auto-advance (default: 0.5)')
    parser.add_argument(
        '--narration-start-floor',
        type=non_negative_float,
        default=DEFAULT_NARRATION_START_FLOOR,
        help=(
            'Minimum seconds from slide-transition start to narration start; '
            'set 0 to start immediately after the transition '
            f'(default: {DEFAULT_NARRATION_START_FLOOR})'
        ),
    )
    parser.add_argument(
        '--inherit-motion-from',
        type=str,
        default=None,
        metavar='BASE_POSTFLIGHT_REPORT',
        help=(
            'For recorded narration, inherit source-bound deck-wide transition, '
            'animation, and advance settings from a successful base export report'
        ),
    )

    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    legacy_native_objects = '--native-objects' in raw_argv
    args = parser.parse_args(raw_argv)
    if legacy_native_objects:
        print(
            'Warning: --native-objects is deprecated; use '
            '--native-charts-and-tables.',
            file=sys.stderr,
        )
    if args.animation_config is not None and not args.animation_config.strip():
        print(
            'Error: --animation-config must be a non-empty file path',
            file=sys.stderr,
        )
        return 1
    if args.inherit_motion_from and not args.recorded_narration:
        print(
            'Error: --inherit-motion-from requires --recorded-narration',
            file=sys.stderr,
        )
        return 1
    if args.inherit_motion_from and args.no_animations:
        print(
            'Error: --inherit-motion-from cannot be combined with --no-animations',
            file=sys.stderr,
        )
        return 1

    if args.quick_generate:
        conflicts: list[str] = []
        if args.source not in {None, 'output'}:
            conflicts.append('--source must be omitted or output')
        if args.pptx_structure not in {None, 'flat'}:
            conflicts.append('--pptx-structure must be omitted or flat')
        if conflicts:
            print(
                "Error: --quick-generate cannot be combined with: "
                + ", ".join(conflicts),
                file=sys.stderr,
            )
            return 1
        if not args.with_notes:
            args.no_notes = True
        args.pptx_structure = 'flat'

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        return 1

    structure_lock = None
    native_structure_contract = None
    pptx_structure = args.pptx_structure
    lock_path = project_path / 'spec_lock.md'
    if not args.quick_generate and not lock_path.is_file():
        print(
            "Error: spec_lock.md is required for release SVG export",
            file=sys.stderr,
        )
        return 1
    declared_structure_mode = (
        None
        if args.quick_generate
        else _declared_pptx_structure_mode(project_path)
    )
    primary_language = None
    if not args.quick_generate:
        try:
            primary_language = _declared_primary_language(project_path)
        except LanguageTagError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if primary_language is None:
            print(
                "Warning: spec_lock.md has no "
                "communication.primary_language; using legacy per-run "
                "language detection.",
                file=sys.stderr,
            )
    if pptx_structure in _LEGACY_PPTX_STRUCTURE_MODES:
        _print_structure_contract_error(pptx_structure)
        return 1
    if (
        declared_structure_mode is not None
        and declared_structure_mode not in _RELEASE_PPTX_STRUCTURE_MODES
    ):
        _print_structure_contract_error(declared_structure_mode)
        return 1
    if pptx_structure is None:
        if declared_structure_mode is None:
            pptx_structure = 'flat'
            print(
                "Warning: spec_lock.md has no pptx_structure.mode; using flat "
                "compatibility mode.",
                file=sys.stderr,
            )
        else:
            pptx_structure = declared_structure_mode
    elif pptx_structure == 'structured' and declared_structure_mode != 'structured':
        _print_structure_contract_error(
            declared_structure_mode,
            requested_mode='structured',
        )
        return 1

    if (
        pptx_structure in _RELEASE_PPTX_STRUCTURE_MODES
        and declared_structure_mode == pptx_structure
    ):
        try:
            structure_lock = load_pptx_structure_lock(project_path)
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if structure_lock is None or structure_lock.mode != pptx_structure:
            print(
                "Error: spec_lock.md must contain one complete "
                f"pptx_structure.mode: {pptx_structure} contract",
                file=sys.stderr,
            )
            return 1

    theme_font_spec = None
    master_text_style_spec = None
    theme_color_spec = None
    if pptx_structure in {'flat', 'structured'} and not args.quick_generate:
        try:
            theme_font_spec = load_theme_font_spec(project_path)
            master_text_style_spec = load_master_text_style_spec(project_path)
            theme_color_spec = load_theme_color_spec(project_path)
        except (ThemeFontError, ThemeColorError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        missing_theme_fields = []
        if theme_font_spec is None:
            missing_theme_fields.append(
                'typography font_family/title_family/body_family'
            )
        if theme_color_spec is None:
            missing_theme_fields.append('colors')
        if missing_theme_fields:
            print(
                f"Error: {pptx_structure} export requires a current-project "
                "theme contract in spec_lock.md; missing: "
                + ", ".join(missing_theme_fields),
                file=sys.stderr,
            )
            return 1
    if args.image_max_dimension < 1:
        print("Error: --image-max-dimension must be >= 1", file=sys.stderr)
        return 1
    if args.image_scale < 1:
        print("Error: --image-scale must be >= 1", file=sys.stderr)
        return 1
    if not 1 <= args.image_quality <= 100:
        print("Error: --image-quality must be between 1 and 100", file=sys.stderr)
        return 1

    try:
        project_info = get_project_info(str(project_path))
        project_name = project_info.get('name', project_path.name)
    except Exception:
        project_name = project_path.name

    canvas_format = args.format
    expected_viewbox = (
        None
        if args.quick_generate
        else _declared_canvas_viewbox(project_path)
    )
    if expected_viewbox is None and not args.quick_generate:
        print(
            "Error: spec_lock.md must contain canvas.viewBox for release export",
            file=sys.stderr,
        )
        return 1

    # Native DrawingML is the only PPTX product. A non-output ``-s`` remains a
    # diagnostic source override; default and explicit output use release rules.
    native_source = args.source or 'output'
    native_files, native_source_dir = find_svg_files(
        project_path,
        native_source,
        allow_fallback=args.source is None and not args.quick_generate,
    )
    ref_files = native_files
    if not native_files:
        if args.quick_generate:
            print(
                "Error: No SVG files found for --quick-generate in: "
                f"{project_path / 'svg_output'}",
                file=sys.stderr,
            )
        elif args.source is not None:
            requested_dir = project_path / native_source_dir
            print(
                "Error: No SVG files found in explicitly requested source: "
                f"{requested_dir}",
                file=sys.stderr,
            )
        else:
            print("Error: No SVG files found", file=sys.stderr)
        return 1

    release_quality_gate = args.quick_generate or args.source in {None, 'output'}
    if release_quality_gate:
        source_fingerprint = _svg_source_fingerprint(native_files)
        quality = _quality_report_context(project_path, source_fingerprint)
        quality_gate, _ = _quality_gate_status(quality)
        if quality_gate != 'passed':
            export_mode = (
                '--quick-generate'
                if args.quick_generate
                else 'default release export'
            )
            print(
                f"Error: {export_mode} requires a passing final SVG quality "
                f"report for the current {native_source_dir}/; found "
                f"{quality_gate}.",
                file=sys.stderr,
            )
            quick_flag = ' --quick-generate' if args.quick_generate else ''
            print(
                "Run: python3 skills/ppt-master/scripts/svg_quality_checker.py "
                f'"{project_path}"{quick_flag} --stage final --json',
                file=sys.stderr,
            )
            return 1

    # Compatibility kwargs remain until the builder's old baseline-specific
    # parameters are removed. Structured export never activates either path.
    structured_baseline = False
    baseline_layout_specs = None
    layout_definition_files: list[Path] = []
    if pptx_structure == 'structured' and structure_lock is not None:
        try:
            template_specs = parse_template_slides(native_files)
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        lock_errors = template_lock_errors(template_specs, structure_lock)
        if lock_errors:
            print("Error: PPTX structure does not match spec_lock.md:", file=sys.stderr)
            for message in lock_errors:
                print(f"  {message}", file=sys.stderr)
            return 1
        try:
            layout_definition_files = structured_layout_definition_files(
                template_specs,
                structure_lock,
            )
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        prototype_errors = template_prototype_errors(
            template_specs,
            structure_lock,
        )
        if prototype_errors:
            print(
                "Error: structured template output does not match page_layouts "
                "prototypes:",
                file=sys.stderr,
            )
            for message in prototype_errors:
                print(f"  {message}", file=sys.stderr)
            return 1

    release_blocked = _release_blocked_graphics(native_files)
    if release_blocked:
        print(
            "Error: invalid PPTX graphic status metadata cannot enter an export. "
            "Correct the reported replacement/fallback/import-source attributes first.",
            file=sys.stderr,
        )
        for filename, marker_id, status in release_blocked[:20]:
            print(f"  {filename}: {marker_id} ({status})", file=sys.stderr)
        if len(release_blocked) > 20:
            print(
                f"  ... and {len(release_blocked) - 20} more",
                file=sys.stderr,
            )
        return 1

    reconstruction_only = _reconstruction_only_graphics(native_files)
    if reconstruction_only:
        print(
            "Warning: reconstruction-only PPTX chart placeholder(s) have no baked "
            "preview. Default export keeps the placeholder; "
            "--native-charts-and-tables "
            "reconstructs entries that carry a valid active replacement marker.",
            file=sys.stderr,
        )
        for filename, marker_id, active_native in reconstruction_only[:20]:
            route = (
                "active native Chart/Table replacement"
                if active_native else "placeholder fallback"
            )
            print(f"  {filename}: {marker_id} ({route})", file=sys.stderr)
        if len(reconstruction_only) > 20:
            print(
                f"  ... and {len(reconstruction_only) - 20} more",
                file=sys.stderr,
            )

    if args.native_objects:
        print(
            "Warning: --native-charts-and-tables replaces shape-based SVG fallbacks "
            "with PowerPoint Chart/Table objects. The native objects may normalize "
            "styling or omit SVG details that are not represented by marker metadata; "
            "use the default shape-based export when exact fallback artwork is required.",
            file=sys.stderr,
        )
        fallbacks = _native_object_fallbacks(native_files)
        if fallbacks:
            print(
                "Warning: --native-charts-and-tables found fallback-only PPTX objects; "
                "they will export through their SVG-derived DrawingML shapes instead "
                "of native Chart/Table objects.",
                file=sys.stderr,
            )
            for filename, marker_id, status in fallbacks[:20]:
                print(f"  {filename}: {marker_id} ({status})", file=sys.stderr)
            if len(fallbacks) > 20:
                print(f"  ... and {len(fallbacks) - 20} more", file=sys.stderr)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir: Path | None = None
    if args.output:
        native_path = Path(args.output)
    else:
        exports_dir = project_path / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        # --native-charts-and-tables yields a materially different file (PowerPoint
        # Chart/Table objects instead of SVG-derived DrawingML shapes), so mark it
        # in the default-flow name to distinguish the two editable object models.
        # Narration flags likewise mark _narrated (audio embedded per slide +
        # auto-advance timings). Flag-driven (not content-sniffed) so the name
        # is predictable; an explicit -o keeps the caller's exact name untouched.
        native_tag = "_native_charts_tables" if args.native_objects else ""
        narrated_tag = "_narrated" if (args.recorded_narration or args.narration_audio_dir) else ""
        native_path = exports_dir / f"{project_name}_{timestamp}{native_tag}{narrated_tag}.pptx"
        # Preserve the authored svg_output/ beside every default-path export.
        backup_dir = project_path / "backup" / timestamp

    native_path.parent.mkdir(parents=True, exist_ok=True)

    verbose = not args.quiet

    enable_notes = not args.no_notes
    notes: dict[str, str] = {}
    if enable_notes:
        try:
            notes = find_notes_files(project_path, ref_files)
        except NotesFileReadError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    narration_audio: dict[str, Path] = {}
    narration_audio_dir_arg = args.recorded_narration or args.narration_audio_dir
    use_narration_timings = args.use_narration_timings or bool(args.recorded_narration)
    if narration_audio_dir_arg:
        narration_audio_dir = Path(narration_audio_dir_arg)
        if not narration_audio_dir.is_absolute():
            narration_audio_dir = project_path / narration_audio_dir
        if args.recorded_narration and not narration_audio_dir.is_dir():
            print(
                f"Error: Recorded narration directory does not exist: {narration_audio_dir}",
                file=sys.stderr,
            )
            return 1
        try:
            narration_audio = find_narration_files(
                narration_audio_dir,
                ref_files,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if verbose:
            print(f"  Narration audio directory: {narration_audio_dir}")
            print(f"  Narration audio matched: {len(narration_audio)}/{len(ref_files)} slide(s)")
        if args.recorded_narration:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    "Error: Recorded narration requires one supported audio file per slide. "
                    f"Matched {len(narration_audio)}/{len(ref_files)} slide(s). "
                    f"Supported extensions: {', '.join(NARRATION_EXTENSIONS)}",
                    file=sys.stderr,
                )
                for stem in missing[:20]:
                    print(f"  Missing audio for: {stem}", file=sys.stderr)
                if len(missing) > 20:
                    print(f"  ... and {len(missing) - 20} more", file=sys.stderr)
                return 1
            unreadable = [
                f"{stem}: {audio_path}"
                for stem, audio_path in sorted(narration_audio.items())
                if probe_audio_duration(audio_path) is None
            ]
            if unreadable:
                print(
                    "Error: Recorded narration requires readable audio durations. "
                    "Install ffprobe/ffmpeg or replace the listed audio files.",
                    file=sys.stderr,
                )
                for item in unreadable[:20]:
                    print(f"  {item}", file=sys.stderr)
                if len(unreadable) > 20:
                    print(f"  ... and {len(unreadable) - 20} more", file=sys.stderr)
                return 1
        elif narration_audio_dir_arg and verbose:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    f"  [warn] Narration audio matched {len(narration_audio)}/{len(ref_files)} slide(s); "
                    "unmatched slides will export without audio."
                )

    if args.no_animations and any(
        value is not None
        for value in (
            args.transition,
            args.transition_duration,
            args.animation,
            args.animation_duration,
            args.animation_trigger,
            args.animation_stagger,
        )
    ):
        print(
            "Error: --no-animations cannot be combined with transition or "
            "object-animation overrides.",
            file=sys.stderr,
        )
        return 1

    effective_animation_config = _resolve_animation_config_source(
        project_path,
        args.animation_config,
        recorded_narration=bool(args.recorded_narration),
        no_animations=args.no_animations,
    )

    if effective_animation_config:
        config_path = Path(effective_animation_config)
        if not config_path.is_absolute():
            config_path = project_path / config_path
        if not config_path.exists():
            print(
                f"Error: Animation config does not exist: {config_path}",
                file=sys.stderr,
            )
            if (
                args.recorded_narration
                and args.animation_config is None
                and config_path.name == 'narration_animations.json'
            ):
                print(
                    "Generate it with narration_sync.py animations, select the "
                    "canonical config with --animation-config animations.json, "
                    "or disable animations with --no-animations.",
                    file=sys.stderr,
                )
            return 1

    try:
        animation_config = (
            None
            if args.no_animations
            else load_animation_config(
                project_path,
                effective_animation_config,
            )
        )
    except Exception as exc:
        print(f"Error: Failed to load animation config: {exc}", file=sys.stderr)
        return 1
    config_errors: list[str] = []
    if animation_config:
        config_errors.extend(validate_transition_config(animation_config))
        config_errors.extend(validate_animation_config_errors(animation_config))
    config_errors = list(dict.fromkeys(config_errors))
    if config_errors:
        for error in config_errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    config_warnings: list[str] = []
    if animation_config:
        reference_messages = validate_animation_config(
            project_path,
            animation_config,
            svg_files=native_files,
        )
        config_warnings = [
            message for message in reference_messages
            if ' has no id and cannot be customized in animations.json' in message
        ]
        reference_errors = [
            message for message in reference_messages
            if message not in config_warnings
        ]
        if reference_errors:
            for error in reference_errors:
                print(f"Error: {error}", file=sys.stderr)
            return 1

    if animation_config and verbose:
        config_label = (
            effective_animation_config
            or str(project_path / 'animations.json')
        )
        print(f"  Animation config: {config_label}")
        for warning in config_warnings:
            print(f"  [warn] {warning}")
    elif args.no_animations and verbose:
        print("  Animations: disabled")

    inherited_motion: dict[str, object] = {}
    if args.inherit_motion_from:
        try:
            inherited_motion = _load_deck_motion_handoff(
                project_path,
                args.inherit_motion_from,
                native_files,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if verbose:
            print(f"  Deck motion handoff: {args.inherit_motion_from}")

    defaults = animation_config.get('defaults', {}) if animation_config else {}
    transition_defaults = _as_dict(defaults.get('transition')) if isinstance(defaults, dict) else {}
    animation_defaults = _as_dict(defaults.get('animation')) if isinstance(defaults, dict) else {}
    inherited_transition = _as_dict(inherited_motion.get('transition'))
    inherited_animation = _as_dict(inherited_motion.get('animation'))
    inherited_overrides = _as_dict(inherited_motion.get('cli_overrides'))

    transition_arg = args.transition
    transition_effect = (
        'none'
        if args.no_animations
        else (
            transition_arg
            if transition_arg is not None
            else (
                inherited_transition['effect']
                if 'effect' in inherited_transition
                else transition_defaults.get('effect', 'fade')
            )
        )
    )
    try:
        transition, transition_effect_options = (
            normalize_transition_effect_request(
                transition_effect,
                (
                    None
                    if transition_arg is not None or args.no_animations
                    else (
                        inherited_transition.get('effect_options')
                        if 'effect' in inherited_transition
                        else transition_defaults.get('effect_options')
                    )
                ),
            )
        )
        transition_duration = validate_seconds(
            (
                args.transition_duration
                if args.transition_duration is not None
                else (
                    inherited_transition['duration']
                    if 'duration' in inherited_transition
                    else transition_defaults.get('duration', 0.4)
                )
            ),
            "transition duration",
            allow_zero=transition is None,
        )
        auto_advance = (
            args.auto_advance
            if args.auto_advance is not None
            else (
                inherited_transition['auto_advance']
                if 'auto_advance' in inherited_transition
                else transition_defaults.get('auto_advance')
            )
        )
        if auto_advance is not None:
            auto_advance = validate_seconds(
                auto_advance,
                "transition auto_advance",
                allow_zero=True,
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        animation_effect = (
            'none'
            if args.no_animations
            else (
                args.animation
                if args.animation is not None
                # Per-element object motion is opt-in by default: unsolicited
                # auto-firing builds read as the "AI deck" tell. Page transitions
                # stay on; enable objects with -a or animations.json.
                else (
                    inherited_animation['effect_request']
                    if 'effect_request' in inherited_animation
                    else animation_defaults.get('effect', 'none')
                )
            )
        )
        normalized_animation = normalize_animation_effect(animation_effect)
        # Keep the raw request for the builder so legacy directional aliases
        # can desugar into canonical effect_options instead of losing their
        # direction during early CLI normalization.
        animation = (
            None
            if normalized_animation is None
            else str(animation_effect)
        )
        animation_duration = validate_seconds(
            (
                args.animation_duration
                if args.animation_duration is not None
                else (
                    inherited_animation['duration']
                    if 'duration' in inherited_animation
                    else animation_defaults.get('duration', 0.4)
                )
            ),
            "animation duration",
            allow_zero=False,
        )
        animation_seconds_to_milliseconds(
            animation_duration,
            "animation duration",
            allow_zero=False,
        )
        animation_stagger = validate_seconds(
            (
                args.animation_stagger
                if args.animation_stagger is not None
                else (
                    inherited_animation['stagger']
                    if 'stagger' in inherited_animation
                    else animation_defaults.get('stagger', 0.5)
                )
            ),
            "animation stagger",
            allow_zero=True,
        )
        animation_seconds_to_milliseconds(
            animation_stagger,
            "animation stagger",
            allow_zero=True,
        )
        animation_trigger = normalize_animation_trigger(
            args.animation_trigger
            if args.animation_trigger is not None
            else (
                inherited_animation['trigger']
                if 'trigger' in inherited_animation
                else animation_defaults.get('trigger', 'after-previous')
            )
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    animation_cli_overrides = {
        'transition': (
            args.transition is not None
            or inherited_overrides.get('transition') is True
        ),
        'transition_duration': (
            args.transition_duration is not None
            or inherited_overrides.get('transition_duration') is True
        ),
        'auto_advance': (
            args.auto_advance is not None
            or inherited_overrides.get('auto_advance') is True
        ),
        'animation': (
            args.animation is not None
            or inherited_overrides.get('animation') is True
        ),
        'animation_duration': (
            args.animation_duration is not None
            or inherited_overrides.get('animation_duration') is True
        ),
        'animation_stagger': (
            args.animation_stagger is not None
            or inherited_overrides.get('animation_stagger') is True
        ),
        'animation_trigger': (
            args.animation_trigger is not None
            or inherited_overrides.get('animation_trigger') is True
        ),
    }

    deck_motion: dict[str, object] = {
        'transition': {
            'effect': transition,
            'effect_options': transition_effect_options,
            'duration': transition_duration,
            'auto_advance': auto_advance,
        },
        'animation': {
            'effect': normalized_animation or 'none',
            'effect_request': animation,
            'duration': animation_duration,
            'stagger': animation_stagger,
            'trigger': animation_trigger,
        },
        'cli_overrides': animation_cli_overrides,
        'narration_timings': use_narration_timings,
    }

    if args.recorded_narration:
        on_click_slides = _recorded_narration_on_click_slides(
            ref_files,
            animation_config,
            animation,
            animation_trigger,
            animation_cli_overrides,
        )
        if on_click_slides:
            print(
                "Error: --recorded-narration cannot be used with on-click object animations. "
                "Use --animation-trigger after-previous or --animation-trigger with-previous.",
                file=sys.stderr,
            )
            for slide in on_click_slides[:20]:
                print(f"  on-click trigger: {slide}", file=sys.stderr)
            if len(on_click_slides) > 20:
                print(f"  ... and {len(on_click_slides) - 20} more", file=sys.stderr)
            return 1

    # Optional per-project document properties. Absent file → factual fields
    # are still stamped at export; only the authored fields stay blank.
    doc_metadata = None
    metadata_path = project_path / 'metadata.json'
    if metadata_path.is_file():
        try:
            loaded = json.loads(metadata_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [warn] metadata.json ignored ({exc})", file=sys.stderr)
        else:
            if isinstance(loaded, dict):
                doc_metadata = loaded
                if verbose:
                    print(f"  Document properties: metadata.json ({len(loaded)} field(s))")
            else:
                print("  [warn] metadata.json ignored (top level is not an object)", file=sys.stderr)

    structure_name = project_name
    if isinstance(doc_metadata, dict):
        metadata_title = doc_metadata.get('title')
        if isinstance(metadata_title, str) and metadata_title.strip():
            structure_name = metadata_title

    shared_kwargs = dict(
        canvas_format=canvas_format,
        expected_viewbox=expected_viewbox,
        doc_metadata=doc_metadata,
        structure_name=structure_name,
        verbose=verbose,
        transition=transition,
        transition_effect_options=transition_effect_options,
        transition_duration=transition_duration,
        auto_advance=auto_advance,
        notes=notes,
        enable_notes=enable_notes,
        animation=animation,
        animation_duration=animation_duration,
        animation_stagger=animation_stagger,
        animation_trigger=animation_trigger,
        animation_config=animation_config,
        animation_resource_root=project_path,
        animation_cli_overrides=animation_cli_overrides,
        narration_audio=narration_audio,
        use_narration_timings=use_narration_timings,
        narration_padding=args.narration_padding,
        narration_start_floor=args.narration_start_floor,
        text_flow=args.text_flow,
        image_optimize=not args.no_image_optimize,
        image_max_dimension=args.image_max_dimension,
        image_sizing=args.image_sizing,
        image_scale=args.image_scale,
        image_quality=args.image_quality,
        native_objects=args.native_objects,
        pptx_structure=pptx_structure,
        structured_baseline=structured_baseline,
        baseline_layout_specs=baseline_layout_specs,
        layout_definition_files=layout_definition_files,
        native_structure_contract=native_structure_contract,
        theme_font_spec=theme_font_spec,
        master_text_style_spec=master_text_style_spec,
        theme_color_spec=theme_color_spec,
        primary_language=primary_language,
    )

    if verbose:
        print("PPT Master - SVG to native DrawingML PPTX Tool")
        print("=" * 50)
        print(f"  Project path: {project_path}")
        print(f"  SVG directory: {native_source_dir}")
        print(f"  Output file: {native_path}")
        print()

    conversion_trace_path: Path | None = None
    if args.conversion_trace is not None:
        if args.conversion_trace:
            requested_trace_path = Path(args.conversion_trace).expanduser()
            conversion_trace_path = (
                requested_trace_path
                if requested_trace_path.is_absolute()
                else project_path / requested_trace_path
            )
        else:
            conversion_trace_path = (
                project_path / 'validation' / f'{native_path.stem}.trace.json'
            )
    try:
        success = create_pptx_with_native_svg(
            output_path=native_path,
            use_native_shapes=True,
            svg_files=native_files,
            conversion_trace_path=conversion_trace_path,
            **shared_kwargs,
        )
    except (TemplateStructureError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Archive svg_output/ once per default-flow export. This preserves the
    # authored SVG sources under backup/<ts>/svg_output/ for inspection and
    # deterministic re-export.
    backup_path: Path | None = None
    if success and backup_dir is not None:
        svg_output_src = project_path / "svg_output"
        if svg_output_src.is_dir():
            backup_dir.mkdir(parents=True, exist_ok=True)
            svg_output_dst = backup_dir / "svg_output"
            try:
                shutil.copytree(svg_output_src, svg_output_dst)
            except Exception as exc:
                if verbose:
                    print(f"  [warn] svg_output backup skipped: {exc}")
            else:
                backup_path = svg_output_dst
                if verbose:
                    print(f"  svg_output backup: {svg_output_dst}")
                payload_store_src = project_path / PAYLOAD_STORE_RELATIVE_PATH
                if payload_store_src.is_file():
                    try:
                        payload_store_dst = backup_dir / PAYLOAD_STORE_RELATIVE_PATH
                        payload_store_dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(payload_store_src, payload_store_dst)
                        if verbose:
                            print(f"  native payload backup: {payload_store_dst}")
                    except Exception as exc:
                        if verbose:
                            print(f"  [warn] native payload backup skipped: {exc}")
        elif verbose:
            print(f"  [info] svg_output/ not found, backup skipped")

    if success:
        try:
            receipt = _write_postflight_report(
                output_path=native_path,
                project_path=project_path,
                svg_files=native_files,
                layout_definition_files=layout_definition_files,
                pptx_structure=pptx_structure,
                backup_path=backup_path,
                conversion_trace_path=conversion_trace_path,
                deck_motion=deck_motion,
            )
        except PptxPostflightValidationError as exc:
            print(
                "Error: generated PPTX failed postflight validation and must "
                f"not be used: {exc}",
                file=sys.stderr,
            )
            print(
                f"  Invalid output remains at: {native_path}",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(
                "Error: PPTX generation succeeded, but its postflight report "
                f"could not be written: {exc}",
                file=sys.stderr,
            )
            print(f"  PPTX output remains at: {native_path}", file=sys.stderr)
            return 1
        if verbose:
            _print_postflight_receipt(receipt)

    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
