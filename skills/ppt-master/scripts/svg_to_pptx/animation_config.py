"""Animation sidecar loading, SVG target scanning, and validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pptx_animations import (
    ANIMATIONS,
    ANIMATION_MODES,
    ANIMATION_TRIGGERS,
    animation_seconds_to_milliseconds,
    normalize_animation_effect,
    normalize_animation_trigger,
)
from pptx_transitions import TRANSITIONS, validate_seconds

from .drawingml.utils import SVG_NS
from .semantic_markers import is_static_page_frame


_NON_VISUAL_TAGS = frozenset(('defs', 'title', 'desc', 'metadata', 'style'))
_CHROME_ID_TOKENS = frozenset({
    'background', 'bg',
    'decoration', 'decorations', 'decor',
    'header', 'footer',
    'chrome', 'watermark',
    'pagenumber', 'pagenum', 'slidenumber', 'slidenum',
    'logo', 'nav', 'rule',
})


@dataclass(frozen=True)
class GroupTarget:
    """Top-level SVG group available for PowerPoint animation anchoring."""

    slide: str
    group_id: str
    order: int
    chrome: bool = False
    structurally_static: bool = False


def _tag_name(elem: ET.Element) -> str:
    return elem.tag.replace(f'{{{SVG_NS}}}', '')


def is_chrome_id(elem_id: str | None) -> bool:
    """Return whether a group id represents static slide chrome."""
    if not elem_id:
        return False
    lower = elem_id.lower()
    compact = lower.replace('-', '').replace('_', '')
    if compact in _CHROME_ID_TOKENS:
        return True
    tokens = re.split(r'[-_]', lower)
    return any(t in _CHROME_ID_TOKENS for t in tokens if t)


def usable_animation_group_id(raw: str | None) -> str | None:
    """Return one nonblank SVG animation anchor verbatim, else ``None``."""
    return raw if raw and raw.strip() else None


def scan_svg_targets(svg_path: Path) -> tuple[list[GroupTarget], list[str]]:
    """Scan one SVG for top-level visible group ids and anonymous groups."""
    root = ET.parse(str(svg_path)).getroot()
    targets: list[GroupTarget] = []
    anonymous_groups: list[str] = []
    visual_index = 0

    for child in root:
        tag = _tag_name(child)
        if tag in _NON_VISUAL_TAGS:
            continue
        visual_index += 1
        if tag != 'g':
            continue
        group_id = usable_animation_group_id(child.get('id'))
        if group_id is None:
            anonymous_groups.append(f'{svg_path.stem}: top-level group #{visual_index}')
            continue
        role = child.get('data-pptx-role')
        placeholder = child.get('data-pptx-placeholder')
        has_explicit_semantics = role is not None or placeholder is not None
        has_structural_layer = child.get('data-pptx-layer') is not None
        semantic_static = (
            has_explicit_semantics
            and is_static_page_frame(role, placeholder)
        )
        structurally_static = has_structural_layer or semantic_static
        if has_structural_layer:
            chrome = True
        elif has_explicit_semantics:
            chrome = semantic_static
        else:
            chrome = is_chrome_id(group_id)
        targets.append(
            GroupTarget(
                slide=svg_path.stem,
                group_id=group_id,
                order=visual_index,
                chrome=chrome,
                structurally_static=structurally_static,
            )
        )

    return targets, anonymous_groups


def _duplicate_target_ids(targets: list[GroupTarget]) -> tuple[str, ...]:
    """Return duplicate top-level animation anchors in deterministic order."""
    counts: dict[str, int] = {}
    for target in targets:
        counts[target.group_id] = counts.get(target.group_id, 0) + 1
    return tuple(sorted(group_id for group_id, count in counts.items() if count > 1))


def _duplicate_target_error(slide_name: str, duplicates: tuple[str, ...]) -> str:
    rendered = ', '.join(repr(group_id) for group_id in duplicates)
    return (
        f'SVG slide "{slide_name}" has duplicate top-level group id(s): '
        f'{rendered}; animation target ids must be unique'
    )


def _require_unique_target_ids(
    slide_name: str,
    targets: list[GroupTarget],
) -> None:
    duplicates = _duplicate_target_ids(targets)
    if duplicates:
        raise ValueError(_duplicate_target_error(slide_name, duplicates))


def scan_project_targets(project_path: Path) -> tuple[dict[str, list[GroupTarget]], list[str]]:
    """Scan ``svg_output/*.svg`` for animation targets."""
    svg_dir = project_path / 'svg_output'
    targets_by_slide: dict[str, list[GroupTarget]] = {}
    anonymous_groups: list[str] = []
    if not svg_dir.is_dir():
        return targets_by_slide, [f'svg_output directory not found: {svg_dir}']

    for svg_path in sorted(svg_dir.glob('*.svg')):
        targets, anonymous = scan_svg_targets(svg_path)
        targets_by_slide[svg_path.stem] = targets
        anonymous_groups.extend(anonymous)

    return targets_by_slide, anonymous_groups


def default_config_path(project_path: Path) -> Path:
    return project_path / 'animations.json'


def load_animation_config(project_path: Path, config_path: str | None = None) -> dict[str, Any] | None:
    """Load optional animation config; return ``None`` when absent."""
    if config_path:
        path = Path(config_path)
    else:
        path = default_config_path(project_path)
    if config_path and not path.is_absolute():
        path = project_path / path
    if not path.exists():
        return None

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f'Animation config must be a JSON object: {path}')
    if data.get('version', 1) != 1:
        raise ValueError(f'Unsupported animation config version: {data.get("version")}')
    return data


def _valid_transition_effect(effect: str) -> bool:
    return effect == 'none' or effect in TRANSITIONS


def _animation_effect_error(effect: object, label: str) -> str | None:
    if not isinstance(effect, str):
        return f'animations.json {label} animation effect must be a string'
    try:
        normalize_animation_effect(effect)
    except ValueError:
        valid = ', '.join((*ANIMATIONS, *ANIMATION_MODES, 'none'))
        return (
            f'animations.json {label} has unknown animation effect: {effect}; '
            f'valid effects: {valid}'
        )
    return None


def _animation_trigger_error(trigger: object, label: str) -> str | None:
    if not isinstance(trigger, str):
        return f'animations.json {label} animation trigger must be a string'
    try:
        normalize_animation_trigger(trigger)
    except ValueError:
        valid = ', '.join(ANIMATION_TRIGGERS)
        return (
            f'animations.json {label} has unknown animation trigger: {trigger}; '
            f'valid triggers: {valid}'
        )
    return None


def _unknown_field_errors(
    value: dict[str, Any],
    allowed: frozenset[str],
    label: str,
) -> list[str]:
    return [
        f'animations.json {label} has unknown field: {field}'
        for field in sorted(set(value) - allowed)
    ]


def validate_transition_config(config: dict[str, Any]) -> list[str]:
    """Return fatal transition-sidecar errors that must block export."""
    errors: list[str] = []
    defaults = config.get('defaults', {})
    default_effect = 'fade'
    if not isinstance(defaults, dict):
        errors.append('animations.json field "defaults" must be an object')
    else:
        errors.extend(
            _transition_scope_errors(
                defaults,
                'defaults',
                inherited_effect='fade',
            )
        )
        transition_defaults = defaults.get('transition', {})
        if isinstance(transition_defaults, dict):
            value = transition_defaults.get('effect', default_effect)
            if isinstance(value, str) and _valid_transition_effect(value):
                default_effect = value

    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        errors.append('animations.json field "slides" must be an object')
        return errors
    for slide_name, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict):
            errors.append(f'animations.json slide "{slide_name}" must be an object')
            continue
        errors.extend(
            _transition_scope_errors(
                slide_cfg,
                f'slide "{slide_name}"',
                inherited_effect=default_effect,
            )
        )
    return errors


def _transition_scope_errors(
    scope: dict[str, Any],
    label: str,
    *,
    inherited_effect: str,
) -> list[str]:
    if 'transition' not in scope:
        return []
    transition = scope['transition']
    if not isinstance(transition, dict):
        return [f'animations.json {label} field "transition" must be an object']

    errors = _unknown_field_errors(
        transition,
        frozenset({'effect', 'duration', 'auto_advance'}),
        f'{label} transition',
    )
    if 'effect' in transition:
        effect = transition['effect']
        if not isinstance(effect, str):
            errors.append(
                f'animations.json {label} transition effect must be a string'
            )
        elif not _valid_transition_effect(effect):
            errors.append(
                f'animations.json {label} has unknown transition effect: {effect}'
            )
    duration_allows_zero = transition.get('effect', inherited_effect) == 'none'
    for field, allow_zero in (
        ('duration', duration_allows_zero),
        ('auto_advance', True),
    ):
        if field not in transition:
            continue
        try:
            validate_seconds(
                transition[field],
                f'animations.json {label} transition {field}',
                allow_zero=allow_zero,
            )
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def validate_animation_config_errors(config: dict[str, Any]) -> list[str]:
    """Return fatal object-animation errors that must block export."""
    errors = _unknown_field_errors(
        config,
        frozenset({'version', 'defaults', 'slides'}),
        'top level',
    )
    defaults = config.get('defaults', {})
    if not isinstance(defaults, dict):
        errors.append('animations.json field "defaults" must be an object')
    else:
        errors.extend(
            _unknown_field_errors(
                defaults,
                frozenset({'transition', 'animation'}),
                'defaults',
            )
        )
        errors.extend(_animation_scope_errors(defaults, 'defaults'))

    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        errors.append('animations.json field "slides" must be an object')
        return list(dict.fromkeys(errors))

    for slide_name, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict):
            errors.append(f'animations.json slide "{slide_name}" must be an object')
            continue
        errors.extend(
            _unknown_field_errors(
                slide_cfg,
                frozenset({'transition', 'animation', 'groups'}),
                f'slide "{slide_name}"',
            )
        )
        errors.extend(
            _animation_scope_errors(slide_cfg, f'slide "{slide_name}"')
        )
        errors.extend(_animation_group_errors(slide_name, slide_cfg))
    return list(dict.fromkeys(errors))


def _animation_scope_errors(scope: dict[str, Any], label: str) -> list[str]:
    if 'animation' not in scope:
        return []
    animation = scope['animation']
    if not isinstance(animation, dict):
        return [f'animations.json {label} field "animation" must be an object']

    errors = _unknown_field_errors(
        animation,
        frozenset({'effect', 'duration', 'stagger', 'trigger'}),
        f'{label} animation',
    )
    if 'effect' in animation:
        effect_error = _animation_effect_error(animation['effect'], label)
        if effect_error:
            errors.append(effect_error)

    for field, allow_zero in (('duration', False), ('stagger', True)):
        if field not in animation:
            continue
        try:
            animation_seconds_to_milliseconds(
                animation[field],
                f'animations.json {label} animation {field}',
                allow_zero=allow_zero,
            )
        except ValueError as exc:
            errors.append(str(exc))

    if 'trigger' in animation:
        trigger_error = _animation_trigger_error(animation['trigger'], label)
        if trigger_error:
            errors.append(trigger_error)
    return errors


def _animation_group_errors(
    slide_name: object,
    slide_cfg: dict[str, Any],
) -> list[str]:
    if 'groups' not in slide_cfg:
        return []
    groups = slide_cfg['groups']
    if not isinstance(groups, dict):
        return [
            f'animations.json slide "{slide_name}" field "groups" must be an object'
        ]

    errors: list[str] = []
    for group_id, group_cfg in groups.items():
        label = f'group "{slide_name}/{group_id}"'
        if not isinstance(group_cfg, dict):
            errors.append(f'animations.json {label} must be an object')
            continue

        errors.extend(
            _unknown_field_errors(
                group_cfg,
                frozenset({'effect', 'duration', 'delay', 'order'}),
                label,
            )
        )

        if 'effect' in group_cfg:
            effect_error = _animation_effect_error(group_cfg['effect'], label)
            if effect_error:
                errors.append(effect_error)

        for field, allow_zero in (('duration', False), ('delay', True)):
            if field not in group_cfg:
                continue
            try:
                animation_seconds_to_milliseconds(
                    group_cfg[field],
                    f'animations.json {label} animation {field}',
                    allow_zero=allow_zero,
                )
            except ValueError as exc:
                errors.append(str(exc))

        if 'order' in group_cfg:
            order = group_cfg['order']
            if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
                errors.append(
                    f'animations.json {label} animation order must be a positive integer: '
                    f'{order!r}'
                )
    return errors


def validate_animation_config(
    project_path: Path,
    config: dict[str, Any] | None = None,
    config_path: str | None = None,
) -> list[str]:
    """Return sidecar-reference diagnostics for ``svg_output``.

    Fatal field/type/value checks are owned by
    :func:`validate_animation_config_errors`.  Anonymous groups are warnings;
    missing slides/groups and structural targets are fatal at export call sites.
    """
    if config is None:
        config = load_animation_config(project_path, config_path)
    if not config:
        return []

    warnings: list[str] = []
    targets_by_slide, anonymous_groups = scan_project_targets(project_path)
    for item in anonymous_groups:
        warnings.append(f'{item} has no id and cannot be customized in animations.json')

    duplicates_by_slide: dict[str, tuple[str, ...]] = {}
    for slide_name, targets in targets_by_slide.items():
        duplicates = _duplicate_target_ids(targets)
        if duplicates:
            duplicates_by_slide[slide_name] = duplicates
    for slide_name, duplicates in duplicates_by_slide.items():
        warnings.append(_duplicate_target_error(slide_name, duplicates))

    known_slides = set(targets_by_slide)
    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return list(dict.fromkeys(warnings))
    for slide_name in sorted(known_slides - set(slides)):
        warnings.append(f'animations.json omits slide: {slide_name}')

    for slide_name, slide_cfg in slides.items():
        if slide_name not in known_slides:
            warnings.append(f'animations.json references missing slide: {slide_name}')
            continue
        if not isinstance(slide_cfg, dict):
            continue

        slide_targets = targets_by_slide.get(slide_name, [])
        duplicate_ids = duplicates_by_slide.get(slide_name, ())
        ambiguous_ids = set(duplicate_ids)
        known_groups = {
            target.group_id: target
            for target in slide_targets
            if target.group_id not in ambiguous_ids
        }
        groups = slide_cfg.get('groups', {})
        if not isinstance(groups, dict):
            continue
        for group_id, group_cfg in groups.items():
            if group_id in ambiguous_ids:
                continue
            if group_id not in known_groups:
                warnings.append(
                    f'animations.json references missing group: {slide_name}/{group_id}'
                )
                continue
            target = known_groups[group_id]
            effect = group_cfg.get('effect') if isinstance(group_cfg, dict) else None
            if target.structurally_static and effect != 'none':
                warnings.append(
                    'animations.json references non-animatable structural group: '
                    f'{slide_name}/{group_id}'
                )
    return list(dict.fromkeys(warnings))


def build_scaffold(project_path: Path) -> dict[str, Any]:
    """Build an editable animation override scaffold from current SVGs.

    Chrome groups are omitted — layer/slide-number placeholder semantics are
    authoritative, followed by an explicit structural role. ``is_chrome_id``
    remains only for marker-free legacy SVGs. Listing static page framing in
    the scaffold would be pure noise. A ``defaults`` stub is emitted up front
    to remind the editor that deck-wide overrides exist and most pages should
    inherit them.
    """
    transition_defaults = {'effect': 'fade', 'duration': 0.4}
    animation_defaults = {
        'effect': 'auto',
        'duration': 0.4,
        'stagger': 0.5,
        'trigger': 'after-previous',
    }
    targets_by_slide, _anonymous = scan_project_targets(project_path)
    slides: dict[str, Any] = {}
    for slide_name, targets in targets_by_slide.items():
        _require_unique_target_ids(slide_name, targets)
        groups: dict[str, Any] = {}
        for target in targets:
            if target.chrome:
                continue
            groups[target.group_id] = {}
        slides[slide_name] = {
            'transition': dict(transition_defaults),
            'animation': dict(animation_defaults),
            'groups': groups,
        }
    return {
        'version': 1,
        'defaults': {
            'transition': transition_defaults,
            'animation': animation_defaults,
        },
        'slides': slides,
    }


def build_group_listing(project_path: Path) -> tuple[list[str], list[str]]:
    """Return one compact line per slide: ``<slide>: id1, id2, id3``.

    Chrome groups are excluded — matches ``build_scaffold``'s policy so the
    listing reflects exactly what an editor can override. Returns
    ``(lines, anonymous_warnings)``.
    """
    targets_by_slide, anonymous = scan_project_targets(project_path)
    lines: list[str] = []
    for slide_name, targets in targets_by_slide.items():
        _require_unique_target_ids(slide_name, targets)
        ids = [t.group_id for t in targets if not t.chrome]
        if not ids:
            lines.append(f'{slide_name}: (no animatable groups)')
        else:
            lines.append(f'{slide_name}: {", ".join(ids)}')
    return lines, anonymous


def write_scaffold(
    project_path: Path,
    output_path: str | None = None,
    *,
    force: bool = False,
) -> Path:
    """Write ``animations.json`` scaffold and return its path."""
    if output_path:
        path = Path(output_path)
    else:
        path = default_config_path(project_path)
    if output_path and not path.is_absolute():
        path = project_path / path
    if path.exists() and not force:
        raise FileExistsError(f'Animation config already exists: {path}')

    scaffold = build_scaffold(project_path)
    path.write_text(
        json.dumps(scaffold, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    return path
