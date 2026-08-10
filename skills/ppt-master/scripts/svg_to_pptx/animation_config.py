"""Motion sidecar loading, SVG target scanning, and validation."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any
from xml.etree import ElementTree as ET

from pptx_animations import (
    ANIMATIONS,
    ANIMATION_AFTER_EFFECTS,
    ANIMATION_MODES,
    ANIMATION_RESTARTS,
    ANIMATION_TIMING_OPTION_FIELDS,
    ANIMATION_TRIGGERS,
    animation_effect_supports_bounce_end,
    animation_seconds_to_milliseconds,
    normalize_animation_effect,
    normalize_animation_effect_options,
    normalize_animation_effect_request,
    normalize_animation_trigger,
)
from pptx_transitions import (
    normalize_transition_effect,
    normalize_transition_effect_request,
    validate_seconds,
)
from slide_roster import discover_slide_svgs

from .drawingml.utils import SVG_NS
from .pptx_package.narration import AUDIO_CONTENT_TYPES
from .semantic_markers import is_static_page_frame


_NON_VISUAL_TAGS = frozenset(('defs', 'title', 'desc', 'metadata', 'style'))
_INHERITANCE_SENSITIVE_ANIMATION_FIELDS = frozenset({
    'effect',
    'effect_options',
    'repeat_count',
    'repeat_duration',
    'accelerate',
    'decelerate',
    'bounce_end',
})
_GROUP_EFFECT_FIELDS = frozenset({
    'effect',
    'effect_options',
    'duration',
    'delay',
    'order',
    'trigger',
    'trigger_shape',
    *ANIMATION_TIMING_OPTION_FIELDS,
    'after_effect',
    'sound',
})
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


@dataclass(frozen=True)
class MorphPair:
    """One explicit PowerPoint Morph identity across adjacent slides."""

    source_slide: str
    destination_slide: str
    key: str
    source_group_id: str
    destination_group_id: str

    @property
    def shape_name(self) -> str:
        """Return the Selection Pane name PowerPoint uses for forced matching."""
        return f'!!{self.key}'


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


def scan_project_targets(
    project_path: Path,
    *,
    svg_files: list[Path] | None = None,
) -> tuple[dict[str, list[GroupTarget]], list[str]]:
    """Scan selected SVG files, defaulting to ``svg_output/*.svg``."""
    targets_by_slide: dict[str, list[GroupTarget]] = {}
    anonymous_groups: list[str] = []
    if svg_files is None:
        svg_dir = project_path / 'svg_output'
        if not svg_dir.is_dir():
            return targets_by_slide, [f'svg_output directory not found: {svg_dir}']
        svg_files = discover_slide_svgs(svg_dir)

    for svg_path in svg_files:
        targets, anonymous = scan_svg_targets(svg_path)
        targets_by_slide[svg_path.stem] = targets
        anonymous_groups.extend(anonymous)

    return targets_by_slide, anonymous_groups


def default_config_path(project_path: Path) -> Path:
    return project_path / 'animations.json'


def load_animation_config(project_path: Path, config_path: str | None = None) -> dict[str, Any] | None:
    """Load animation config; only an absent default sidecar is optional."""
    if config_path is not None:
        if not config_path.strip():
            raise ValueError('Animation config path must be non-empty')
        path = Path(config_path)
    else:
        path = default_config_path(project_path)
    if config_path is not None and not path.is_absolute():
        path = project_path / path
    if not path.exists():
        if config_path is not None:
            raise FileNotFoundError(f'Animation config does not exist: {path}')
        return None

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f'Animation config must be a JSON object: {path}')
    if data.get('version', 1) != 1:
        raise ValueError(f'Unsupported animation config version: {data.get("version")}')
    return data


def _valid_transition_effect(effect: str) -> bool:
    try:
        normalize_transition_effect(effect)
    except ValueError:
        return False
    return True


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


def resolve_slide_animation_config(
    default_animation: dict[str, Any],
    slide_animation: dict[str, Any],
) -> dict[str, Any]:
    """Merge one slide animation over defaults using writer inheritance rules."""
    resolved = dict(default_animation)
    if 'effect' in slide_animation and 'effect_options' not in slide_animation:
        resolved.pop('effect_options', None)
    resolved.update(slide_animation)
    return resolved


def animation_group_effect_entries(
    group_cfg: dict[str, Any],
    *,
    path: str,
) -> tuple[tuple[str, dict[str, Any]], ...]:
    """Expand one legacy group block or one ordered multi-effect envelope."""
    if 'effects' not in group_cfg:
        return ((path, group_cfg),)

    extra_fields = sorted(set(group_cfg) - {'effects'})
    if extra_fields:
        rendered = ', '.join(repr(field) for field in extra_fields)
        raise ValueError(
            f'animations.json {path} cannot combine "effects" with '
            f'other group-level field(s): {rendered}'
        )
    effects = group_cfg['effects']
    if not isinstance(effects, list):
        raise ValueError(f'animations.json {path}.effects must be an array')
    if not effects:
        raise ValueError(
            f'animations.json {path}.effects must contain at least one effect'
        )

    entries: list[tuple[str, dict[str, Any]]] = []
    for index, effect_cfg in enumerate(effects):
        effect_path = f'{path}.effects[{index}]'
        if not isinstance(effect_cfg, dict):
            raise ValueError(
                f'animations.json {effect_path} must be an object'
            )
        if 'effect' not in effect_cfg:
            raise ValueError(
                f'animations.json {effect_path}.effect is required'
            )
        entries.append((effect_path, effect_cfg))
    return tuple(entries)


def _animation_parameter_errors(
    value: dict[str, Any],
    label: str,
    *,
    inherited_effect: object,
    sound_is_path: bool = True,
) -> list[str]:
    """Validate PowerPoint effect/timing parameters shared by all scopes."""
    errors: list[str] = []
    effect = value.get('effect', inherited_effect)
    effect_options = value.get('effect_options')
    if effect_options is not None and 'effect' not in value:
        errors.append(
            f'animations.json {label} effect_options requires an explicit effect'
        )
    else:
        try:
            normalize_animation_effect_request(
                effect,
                effect_options,
                allow_none=True,
                allow_modes=True,
            )
        except ValueError as exc:
            errors.append(f'animations.json {label}: {exc}')

    repeat_count = value.get('repeat_count')
    repeat_duration = value.get('repeat_duration')
    if repeat_count is not None:
        if (
            isinstance(repeat_count, bool)
            or not isinstance(repeat_count, (int, float))
            or not math.isfinite(float(repeat_count))
            or float(repeat_count) <= 0
            or float(repeat_count) * 1000 > 4_294_967_295
        ):
            errors.append(
                f'animations.json {label} repeat_count must be a positive number: '
                f'{repeat_count!r}'
            )
    if repeat_duration is not None:
        try:
            animation_seconds_to_milliseconds(
                repeat_duration,
                f'animations.json {label} repeat_duration',
                allow_zero=False,
            )
        except ValueError as exc:
            errors.append(str(exc))
    if repeat_count is not None and repeat_duration is not None:
        errors.append(
            f'animations.json {label} repeat_count and repeat_duration '
            'are mutually exclusive'
        )

    for field in ('auto_reverse', 'rewind'):
        if field in value and not isinstance(value[field], bool):
            errors.append(
                f'animations.json {label} {field} must be a boolean: '
                f'{value[field]!r}'
            )
    ratios: dict[str, float] = {}
    for field in ('accelerate', 'decelerate', 'bounce_end'):
        if field not in value:
            continue
        raw_ratio = value[field]
        if (
            isinstance(raw_ratio, bool)
            or not isinstance(raw_ratio, (int, float))
            or not math.isfinite(float(raw_ratio))
            or not 0 <= float(raw_ratio) <= 1
        ):
            errors.append(
                f'animations.json {label} {field} must be between 0 and 1: '
                f'{raw_ratio!r}'
            )
        else:
            ratios[field] = float(raw_ratio)
    if ratios.get('accelerate', 0) + ratios.get('decelerate', 0) > 1:
        errors.append(
            f'animations.json {label} accelerate + decelerate must not exceed 1'
        )
    if ratios.get('bounce_end', 0) and ratios.get('decelerate', 0):
        errors.append(
            f'animations.json {label} bounce_end and decelerate are '
            'mutually exclusive in PowerPoint'
        )

    if 'restart' in value and value['restart'] not in ANIMATION_RESTARTS:
        errors.append(
            f'animations.json {label} restart must be one of '
            f'{", ".join(ANIMATION_RESTARTS)}: {value["restart"]!r}'
        )

    if 'after_effect' in value:
        after_effect = value['after_effect']
        if isinstance(after_effect, str):
            after_type = after_effect
            after_color = None
        elif isinstance(after_effect, dict):
            unknown = set(after_effect) - {'type', 'color'}
            for field in sorted(unknown):
                errors.append(
                    f'animations.json {label} after_effect has unknown field: {field}'
                )
            after_type = after_effect.get('type', 'none')
            after_color = after_effect.get('color')
        else:
            after_type = None
            after_color = None
            errors.append(
                f'animations.json {label} after_effect must be a string or object'
            )
        if after_type is not None and after_type not in ANIMATION_AFTER_EFFECTS:
            errors.append(
                f'animations.json {label} after_effect.type must be one of '
                f'{", ".join(ANIMATION_AFTER_EFFECTS)}: {after_type!r}'
            )
        elif after_type == 'dim':
            if after_color is None:
                errors.append(
                    f'animations.json {label} dim after_effect requires color'
                )
            else:
                try:
                    normalize_animation_effect_options(
                        'emphasis_change_fill_color',
                        {'color': after_color},
                    )
                except ValueError as exc:
                    errors.append(f'animations.json {label}: {exc}')
        elif after_color is not None:
            errors.append(
                f'animations.json {label} after_effect.color is valid only '
                'with type "dim"'
            )

    if 'sound' in value:
        sound = value['sound']
        if sound_is_path and (
            not isinstance(sound, str) or not sound.strip()
        ):
            errors.append(
                f'animations.json {label} sound must be a non-empty path string'
            )
        elif sound_is_path and Path(sound).suffix.lower() not in AUDIO_CONTENT_TYPES:
            errors.append(
                f'animations.json {label} sound must use .m4a, .mp3, or .wav'
            )
    return errors


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
        errors.extend(_morph_scope_errors(slide_name, slide_cfg))
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
        frozenset({
            'effect',
            'effect_options',
            'duration',
            'auto_advance',
            'sound',
        }),
        f'{label} transition',
    )
    effect = transition.get('effect', inherited_effect)
    effect_options = transition.get('effect_options')
    if effect_options is not None and 'effect' not in transition:
        errors.append(
            f'animations.json {label} transition effect_options requires '
            'an explicit effect'
        )
    else:
        try:
            normalize_transition_effect_request(effect, effect_options)
        except ValueError as exc:
            errors.append(f'animations.json {label} transition: {exc}')
    try:
        duration_allows_zero = (
            normalize_transition_effect(effect) is None
        )
    except ValueError:
        duration_allows_zero = False
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
    if 'sound' in transition:
        sound = transition['sound']
        if sound is None:
            return errors
        if not isinstance(sound, str) or not sound.strip():
            errors.append(
                f'animations.json {label} transition sound must be a '
                'non-empty project-relative .wav path or null'
            )
        elif Path(sound).is_absolute() or PureWindowsPath(sound).drive:
            errors.append(
                f'animations.json {label} transition sound must be '
                f'project-relative: {sound!r}'
            )
        elif Path(sound).suffix.lower() != '.wav':
            errors.append(
                f'animations.json {label} transition sound must use .wav'
            )
    return errors


def _morph_scope_errors(
    slide_name: object,
    slide_cfg: dict[str, Any],
) -> list[str]:
    """Validate one destination slide's deterministic Morph declaration."""
    if 'morph' not in slide_cfg:
        return []
    label = f'slide "{slide_name}" morph'
    morph = slide_cfg['morph']
    if not isinstance(morph, dict):
        return [f'animations.json {label} must be an object']

    errors = _unknown_field_errors(
        morph,
        frozenset({'from', 'pairs'}),
        label,
    )
    source_slide = morph.get('from')
    if not isinstance(source_slide, str) or not source_slide.strip():
        errors.append(
            f'animations.json {label} field "from" must be a non-empty slide stem'
        )

    pairs = morph.get('pairs')
    if not isinstance(pairs, dict) or not pairs:
        errors.append(
            f'animations.json {label} field "pairs" must be a non-empty object'
        )
    else:
        source_groups: dict[str, str] = {}
        destination_groups: dict[str, str] = {}
        for key, pair in pairs.items():
            pair_label = f'{label} pair "{key}"'
            if (
                not isinstance(key, str)
                or not key.strip()
                or key != key.strip()
                or key.startswith('!!')
                or any(ord(char) < 32 for char in key)
            ):
                errors.append(
                    f'animations.json {pair_label} key must be a trimmed, '
                    'non-empty name without the !! prefix or control characters'
                )
            if not isinstance(pair, dict):
                errors.append(f'animations.json {pair_label} must be an object')
                continue
            errors.extend(
                _unknown_field_errors(
                    pair,
                    frozenset({'from', 'to'}),
                    pair_label,
                )
            )
            for field in ('from', 'to'):
                value = pair.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(
                        f'animations.json {pair_label} field "{field}" must '
                        'be a non-empty top-level group id'
                    )
            source_group = pair.get('from')
            if isinstance(source_group, str) and source_group.strip():
                previous = source_groups.setdefault(source_group, str(key))
                if previous != str(key):
                    errors.append(
                        f'animations.json {label} source group '
                        f'"{source_group}" is assigned to both "{previous}" '
                        f'and "{key}"'
                    )
            destination_group = pair.get('to')
            if isinstance(destination_group, str) and destination_group.strip():
                previous = destination_groups.setdefault(
                    destination_group,
                    str(key),
                )
                if previous != str(key):
                    errors.append(
                        f'animations.json {label} destination group '
                        f'"{destination_group}" is assigned to both "{previous}" '
                        f'and "{key}"'
                    )

    transition = slide_cfg.get('transition')
    if not isinstance(transition, dict) or 'effect' not in transition:
        errors.append(
            f'animations.json {label} requires an explicit slide transition '
            'effect "morph"'
        )
    else:
        try:
            effect, options = normalize_transition_effect_request(
                transition.get('effect'),
                transition.get('effect_options'),
            )
        except ValueError:
            pass
        else:
            if effect != 'morph':
                errors.append(
                    f'animations.json {label} requires transition effect "morph"'
                )
            elif options.get('morph_by', 'object') != 'object':
                errors.append(
                    f'animations.json {label} requires Morph by object'
                )
    return errors


def _resolve_morph_pairs(
    slide_order: list[str],
    config: dict[str, Any],
) -> tuple[list[MorphPair], list[str]]:
    """Resolve sidecar Morph declarations against the actual slide order."""
    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return [], ['animations.json field "slides" must be an object']

    order_by_slide = {slide_name: index for index, slide_name in enumerate(slide_order)}
    pairs: list[MorphPair] = []
    errors: list[str] = []
    assignments: dict[str, dict[str, str]] = {}
    keys: dict[str, dict[str, str]] = {}
    declared_keys_by_destination: dict[str, set[str]] = {}

    for destination_slide, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict) or 'morph' not in slide_cfg:
            continue
        scope_errors = _morph_scope_errors(destination_slide, slide_cfg)
        if scope_errors:
            errors.extend(scope_errors)
            continue
        destination_index = order_by_slide.get(str(destination_slide))
        if destination_index is None:
            errors.append(
                'animations.json morph destination slide is missing: '
                f'{destination_slide}'
            )
            continue
        if destination_index == 0:
            errors.append(
                'animations.json first slide cannot declare an incoming Morph: '
                f'{destination_slide}'
            )
            continue

        morph = slide_cfg['morph']
        source_slide = str(morph['from'])
        expected_source = slide_order[destination_index - 1]
        if source_slide != expected_source:
            errors.append(
                f'animations.json slide "{destination_slide}" morph.from must '
                f'reference the immediately preceding slide "{expected_source}", '
                f'not "{source_slide}"'
            )
            continue

        declared_keys_by_destination[str(destination_slide)] = set(
            morph['pairs']
        )
        for key, pair in morph['pairs'].items():
            resolved = MorphPair(
                source_slide=source_slide,
                destination_slide=str(destination_slide),
                key=str(key),
                source_group_id=str(pair['from']),
                destination_group_id=str(pair['to']),
            )
            pair_conflict = False
            for slide_name, group_id in (
                (resolved.source_slide, resolved.source_group_id),
                (resolved.destination_slide, resolved.destination_group_id),
            ):
                slide_assignments = assignments.setdefault(slide_name, {})
                previous_key = slide_assignments.setdefault(group_id, resolved.key)
                if previous_key != resolved.key:
                    errors.append(
                        f'animations.json Morph group "{slide_name}/{group_id}" '
                        f'is assigned to both "{previous_key}" and "{resolved.key}"'
                    )
                    pair_conflict = True
                slide_keys = keys.setdefault(slide_name, {})
                previous_group = slide_keys.setdefault(resolved.key, group_id)
                if previous_group != group_id:
                    errors.append(
                        f'animations.json Morph key "{resolved.key}" maps to both '
                        f'"{slide_name}/{previous_group}" and '
                        f'"{slide_name}/{group_id}"'
                    )
                    pair_conflict = True
            if not pair_conflict:
                pairs.append(resolved)

    for destination_slide, declared_keys in declared_keys_by_destination.items():
        destination_index = order_by_slide[destination_slide]
        source_slide = slide_order[destination_index - 1]
        shared_keys = (
            set(keys.get(source_slide, {}))
            & set(keys.get(destination_slide, {}))
        )
        unexpected_keys = sorted(shared_keys - declared_keys)
        if unexpected_keys:
            errors.append(
                f'animations.json slide "{destination_slide}" Morph would '
                'force undeclared adjacent key(s): '
                + ', '.join(f'"{key}"' for key in unexpected_keys)
            )
    return pairs, list(dict.fromkeys(errors))


def resolve_morph_pairs(
    slide_order: list[str],
    config: dict[str, Any] | None,
) -> tuple[MorphPair, ...]:
    """Return validated deterministic Morph pairs in authored order."""
    if not config:
        return ()
    pairs, errors = _resolve_morph_pairs(slide_order, config)
    if errors:
        raise ValueError('; '.join(errors))
    return tuple(pairs)


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
                frozenset({'transition', 'animation', 'groups', 'morph'}),
                f'slide "{slide_name}"',
            )
        )
        errors.extend(
            _animation_scope_errors(slide_cfg, f'slide "{slide_name}"')
        )
        errors.extend(_animation_group_errors(slide_name, slide_cfg))
    errors.extend(_resolved_animation_parameter_errors(config))
    return list(dict.fromkeys(errors))


def _animation_scope_errors(scope: dict[str, Any], label: str) -> list[str]:
    if 'animation' not in scope:
        return []
    animation = scope['animation']
    if not isinstance(animation, dict):
        return [f'animations.json {label} field "animation" must be an object']

    errors = _unknown_field_errors(
        animation,
        frozenset({
            'effect',
            'effect_options',
            'duration',
            'stagger',
            'trigger',
            *ANIMATION_TIMING_OPTION_FIELDS,
            'after_effect',
            'sound',
        }),
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
    errors.extend(
        _animation_parameter_errors(
            animation,
            f'{label} animation',
            inherited_effect='auto',
        )
    )
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
        path = (
            f'slides[{json.dumps(str(slide_name), ensure_ascii=False)}]'
            f'.groups[{json.dumps(str(group_id), ensure_ascii=False)}]'
        )
        if not isinstance(group_cfg, dict):
            errors.append(f'animations.json {path} must be an object')
            continue

        if 'effects' not in group_cfg:
            errors.extend(
                _animation_effect_entry_errors(
                    group_cfg,
                    path,
                    require_effect=False,
                    target_group_id=str(group_id),
                )
            )
            continue

        extra_fields = sorted(set(group_cfg) - {'effects'})
        if extra_fields:
            rendered = ', '.join(repr(field) for field in extra_fields)
            errors.append(
                f'animations.json {path} cannot combine "effects" with '
                f'other group-level field(s): {rendered}'
            )
        effects = group_cfg['effects']
        if not isinstance(effects, list):
            errors.append(f'animations.json {path}.effects must be an array')
            continue
        if not effects:
            errors.append(
                f'animations.json {path}.effects must contain at least one effect'
            )
            continue
        for index, effect_cfg in enumerate(effects):
            effect_path = f'{path}.effects[{index}]'
            if not isinstance(effect_cfg, dict):
                errors.append(
                    f'animations.json {effect_path} must be an object'
                )
                continue
            errors.extend(
                _animation_effect_entry_errors(
                    effect_cfg,
                    effect_path,
                    require_effect=True,
                    target_group_id=str(group_id),
                )
            )
    return errors


def _animation_effect_entry_errors(
    effect_cfg: dict[str, Any],
    path: str,
    *,
    require_effect: bool,
    target_group_id: str,
) -> list[str]:
    """Validate one legacy group block or one ``effects[]`` row."""
    errors = _unknown_field_errors(
        effect_cfg,
        _GROUP_EFFECT_FIELDS,
        path,
    )
    if require_effect and 'effect' not in effect_cfg:
        errors.append(f'animations.json {path}.effect is required')
    elif 'effect' in effect_cfg:
        effect_error = _animation_effect_error(effect_cfg['effect'], path)
        if effect_error:
            errors.append(effect_error)

    for field, allow_zero in (('duration', False), ('delay', True)):
        if field not in effect_cfg:
            continue
        try:
            animation_seconds_to_milliseconds(
                effect_cfg[field],
                f'animations.json {path}.{field}',
                allow_zero=allow_zero,
            )
        except ValueError as exc:
            errors.append(str(exc))

    if 'order' in effect_cfg:
        order = effect_cfg['order']
        if isinstance(order, bool) or not isinstance(order, int) or order <= 0:
            errors.append(
                f'animations.json {path}.order must be a positive integer: '
                f'{order!r}'
            )

    if 'trigger' in effect_cfg:
        trigger_error = _animation_trigger_error(effect_cfg['trigger'], path)
        if trigger_error:
            errors.append(trigger_error)

    if 'trigger_shape' in effect_cfg:
        trigger_shape = effect_cfg['trigger_shape']
        if not isinstance(trigger_shape, str) or not trigger_shape.strip():
            errors.append(
                f'animations.json {path}.trigger_shape must be a '
                f'non-empty group id: {trigger_shape!r}'
            )
        elif trigger_shape == target_group_id:
            errors.append(
                f'animations.json {path}.trigger_shape must reference '
                'a different group'
            )
        if effect_cfg.get('effect') == 'none':
            errors.append(
                f'animations.json {path}.trigger_shape cannot be used '
                'with effect "none"'
            )
        if (
            'trigger' in effect_cfg
            and effect_cfg.get('trigger') != 'on-click'
        ):
            errors.append(
                f'animations.json {path}.trigger_shape requires '
                'trigger "on-click" when trigger is explicit'
            )

    errors.extend(
        _animation_parameter_errors(
            effect_cfg,
            path,
            inherited_effect='auto',
        )
    )
    return errors


def _bounce_support_error(
    animation: dict[str, Any],
    label: str,
) -> str | None:
    """Return a writer-equivalent bounce support error for one resolved scope."""
    bounce_end = animation.get('bounce_end')
    if (
        isinstance(bounce_end, bool)
        or not isinstance(bounce_end, (int, float))
        or not math.isfinite(float(bounce_end))
        or float(bounce_end) <= 0
    ):
        return None
    try:
        effect, options = normalize_animation_effect_request(
            animation.get('effect', 'auto'),
            animation.get('effect_options'),
            allow_none=True,
            allow_modes=True,
        )
    except ValueError:
        return None
    if effect is None or effect in ANIMATION_MODES:
        return None
    if animation_effect_supports_bounce_end(effect, options):
        return None
    return (
        f'animations.json {label} effect {effect!r} has no behavior that '
        'supports bounce_end'
    )


def _resolved_animation_parameter_errors(config: dict[str, Any]) -> list[str]:
    """Validate effective animation parameters after sidecar inheritance."""
    defaults = config.get('defaults', {})
    default_animation: dict[str, Any] = {'effect': 'none'}
    if isinstance(defaults, dict):
        value = defaults.get('animation', {})
        if isinstance(value, dict):
            default_animation = resolve_slide_animation_config(
                default_animation,
                value,
            )

    errors: list[str] = []
    default_error = _bounce_support_error(default_animation, 'defaults animation')
    if default_error:
        errors.append(default_error)

    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return errors
    for slide_name, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict):
            continue
        slide_value = slide_cfg.get('animation', {})
        if not isinstance(slide_value, dict):
            continue
        slide_animation = resolve_slide_animation_config(
            default_animation,
            slide_value,
        )
        if _INHERITANCE_SENSITIVE_ANIMATION_FIELDS & set(slide_value):
            errors.extend(
                _animation_parameter_errors(
                    slide_animation,
                    f'slide "{slide_name}" animation',
                    inherited_effect='auto',
                )
            )
            error = _bounce_support_error(
                slide_animation,
                f'slide "{slide_name}" animation',
            )
            if error:
                errors.append(error)

        groups = slide_cfg.get('groups', {})
        if not isinstance(groups, dict):
            continue
        for group_id, group_cfg in groups.items():
            if not isinstance(group_cfg, dict):
                continue
            path = (
                f'slides[{json.dumps(str(slide_name), ensure_ascii=False)}]'
                f'.groups[{json.dumps(str(group_id), ensure_ascii=False)}]'
            )
            try:
                effect_entries = animation_group_effect_entries(
                    group_cfg,
                    path=path,
                )
            except ValueError:
                continue
            for effect_path, effect_cfg in effect_entries:
                if not (
                    _INHERITANCE_SENSITIVE_ANIMATION_FIELDS
                    & set(effect_cfg)
                ):
                    continue
                inherited_group_animation = {
                    field: slide_animation[field]
                    for field in (
                        'effect',
                        'effect_options',
                        'duration',
                        *ANIMATION_TIMING_OPTION_FIELDS,
                        'after_effect',
                        'sound',
                    )
                    if field in slide_animation
                }
                group_animation = resolve_slide_animation_config(
                    inherited_group_animation,
                    effect_cfg,
                )
                errors.extend(
                    _animation_parameter_errors(
                        group_animation,
                        effect_path,
                        inherited_effect='none',
                    )
                )
                error = _bounce_support_error(
                    group_animation,
                    effect_path,
                )
                if error:
                    errors.append(error)
    return errors


def _declared_animation_sounds(
    config: dict[str, Any],
) -> tuple[tuple[str, object], ...]:
    """Return explicitly declared sidecar sound values with scope labels."""
    sounds: list[tuple[str, object]] = []
    defaults = config.get('defaults', {})
    if isinstance(defaults, dict):
        animation = defaults.get('animation', {})
        if isinstance(animation, dict) and 'sound' in animation:
            sounds.append(('defaults animation', animation['sound']))

    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return tuple(sounds)
    for slide_name, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict):
            continue
        animation = slide_cfg.get('animation', {})
        if isinstance(animation, dict) and 'sound' in animation:
            sounds.append((f'slide "{slide_name}" animation', animation['sound']))
        groups = slide_cfg.get('groups', {})
        if not isinstance(groups, dict):
            continue
        for group_id, group_cfg in groups.items():
            if not isinstance(group_cfg, dict):
                continue
            path = (
                f'slides[{json.dumps(str(slide_name), ensure_ascii=False)}]'
                f'.groups[{json.dumps(str(group_id), ensure_ascii=False)}]'
            )
            try:
                effect_entries = animation_group_effect_entries(
                    group_cfg,
                    path=path,
                )
            except ValueError:
                continue
            for effect_path, effect_cfg in effect_entries:
                if 'sound' in effect_cfg:
                    sounds.append((effect_path, effect_cfg['sound']))
    return tuple(sounds)


def _animation_sound_path_errors(
    project_path: Path,
    config: dict[str, Any],
) -> list[str]:
    """Validate declared animation sound files against the project root."""
    errors: list[str] = []
    project_root = project_path.resolve()
    for label, raw_sound in _declared_animation_sounds(config):
        if not isinstance(raw_sound, str) or not raw_sound.strip():
            continue
        sound_path = Path(raw_sound)
        if sound_path.suffix.lower() not in AUDIO_CONTENT_TYPES:
            errors.append(
                f'animations.json {label} sound must use .m4a, .mp3, or .wav'
            )
            continue
        if not sound_path.is_absolute():
            sound_path = project_root / sound_path
        sound_path = sound_path.resolve()
        if not sound_path.exists():
            errors.append(
                f'animations.json {label} sound file not found: {sound_path}'
            )
        elif not sound_path.is_file():
            errors.append(
                f'animations.json {label} sound path is not a regular file: '
                f'{sound_path}'
            )
    return errors


def _declared_transition_sounds(
    config: dict[str, Any],
) -> tuple[tuple[str, object], ...]:
    """Return explicitly declared non-null transition sound values."""
    sounds: list[tuple[str, object]] = []
    defaults = config.get('defaults', {})
    if isinstance(defaults, dict):
        transition = defaults.get('transition', {})
        if (
            isinstance(transition, dict)
            and transition.get('sound') is not None
        ):
            sounds.append(('defaults transition', transition['sound']))

    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return tuple(sounds)
    for slide_name, slide_cfg in slides.items():
        if not isinstance(slide_cfg, dict):
            continue
        transition = slide_cfg.get('transition', {})
        if (
            isinstance(transition, dict)
            and transition.get('sound') is not None
        ):
            sounds.append(
                (f'slide "{slide_name}" transition', transition['sound'])
            )
    return tuple(sounds)


def _transition_sound_path_errors(
    project_path: Path,
    config: dict[str, Any],
) -> list[str]:
    """Validate transition sounds as project-contained WAV files."""
    errors: list[str] = []
    project_root = project_path.resolve()
    for label, raw_sound in _declared_transition_sounds(config):
        if not isinstance(raw_sound, str) or not raw_sound.strip():
            continue
        sound_path = Path(raw_sound)
        if sound_path.is_absolute() or PureWindowsPath(raw_sound).drive:
            errors.append(
                f'animations.json {label} sound must be project-relative: '
                f'{raw_sound!r}'
            )
            continue
        if sound_path.suffix.lower() != '.wav':
            continue
        resolved_path = (project_root / sound_path).resolve()
        try:
            resolved_path.relative_to(project_root)
        except ValueError:
            errors.append(
                f'animations.json {label} sound escapes the project root: '
                f'{raw_sound!r}'
            )
            continue
        if not resolved_path.exists():
            errors.append(
                f'animations.json {label} sound file not found: {resolved_path}'
            )
        elif not resolved_path.is_file():
            errors.append(
                f'animations.json {label} sound path is not a regular file: '
                f'{resolved_path}'
            )
    return errors


def validate_animation_config(
    project_path: Path,
    config: dict[str, Any] | None = None,
    config_path: str | None = None,
    *,
    svg_files: list[Path] | None = None,
) -> list[str]:
    """Return sidecar-reference diagnostics for the selected SVG slides.

    Fatal field/type/value checks are owned by
    :func:`validate_animation_config_errors`. Anonymous groups are warnings;
    references to invalid sound files, missing slides/groups, and structural
    targets are fatal at export call sites. Slides omitted from a sparse
    sidecar inherit defaults.
    """
    if config is None:
        config = load_animation_config(project_path, config_path)
    if not config:
        return []

    warnings = _animation_sound_path_errors(project_path, config)
    warnings.extend(_transition_sound_path_errors(project_path, config))
    targets_by_slide, anonymous_groups = scan_project_targets(
        project_path,
        svg_files=svg_files,
    )
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
    known_groups_by_slide: dict[str, dict[str, GroupTarget]] = {}
    for slide_name, slide_targets in targets_by_slide.items():
        ambiguous_ids = set(duplicates_by_slide.get(slide_name, ()))
        known_groups_by_slide[slide_name] = {
            target.group_id: target
            for target in slide_targets
            if target.group_id not in ambiguous_ids
        }
    default_animation: dict[str, Any] = {'effect': 'none'}
    defaults = config.get('defaults', {})
    if isinstance(defaults, dict):
        animation_value = defaults.get('animation', {})
        if isinstance(animation_value, dict):
            default_animation = resolve_slide_animation_config(
                default_animation,
                animation_value,
            )
    slides = config.get('slides', {})
    if not isinstance(slides, dict):
        return list(dict.fromkeys(warnings))
    for slide_name, slide_cfg in slides.items():
        if slide_name not in known_slides:
            warnings.append(f'animations.json references missing slide: {slide_name}')
            continue
        if not isinstance(slide_cfg, dict):
            continue

        slide_animation = default_animation
        animation_value = slide_cfg.get('animation', {})
        if isinstance(animation_value, dict):
            slide_animation = resolve_slide_animation_config(
                default_animation,
                animation_value,
            )
        slide_targets = targets_by_slide.get(slide_name, [])
        duplicate_ids = duplicates_by_slide.get(slide_name, ())
        ambiguous_ids = set(duplicate_ids)
        known_groups = known_groups_by_slide.get(slide_name, {})
        groups = slide_cfg.get('groups', {})
        if not isinstance(groups, dict):
            continue
        for group_id, group_cfg in groups.items():
            path = (
                f'slides[{json.dumps(str(slide_name), ensure_ascii=False)}]'
                f'.groups[{json.dumps(str(group_id), ensure_ascii=False)}]'
            )
            if group_id in ambiguous_ids:
                continue
            if group_id not in known_groups:
                warnings.append(
                    f'animations.json {path} references a missing group'
                )
                continue
            target = known_groups[group_id]
            if not isinstance(group_cfg, dict):
                continue
            try:
                effect_entries = animation_group_effect_entries(
                    group_cfg,
                    path=path,
                )
            except ValueError:
                continue
            if (
                target.structurally_static
                and any(
                    normalize_animation_effect(
                        effect_cfg.get(
                            'effect',
                            slide_animation.get('effect', 'none'),
                        ),
                        allow_none=True,
                        allow_modes=True,
                    )
                    is not None
                    for _effect_path, effect_cfg in effect_entries
                )
            ):
                warnings.append(
                    f'animations.json {path} references a non-animatable '
                    'structural group'
                )
            for effect_path, effect_cfg in effect_entries:
                trigger_shape = effect_cfg.get('trigger_shape')
                if (
                    not isinstance(trigger_shape, str)
                    or not trigger_shape.strip()
                ):
                    continue
                if trigger_shape in ambiguous_ids:
                    warnings.append(
                        f'animations.json {effect_path}.trigger_shape '
                        f'references ambiguous group {trigger_shape!r}'
                    )
                    continue
                trigger_target = known_groups.get(trigger_shape)
                if trigger_target is None:
                    warnings.append(
                        f'animations.json {effect_path}.trigger_shape '
                        f'references missing group {trigger_shape!r}'
                    )
                elif trigger_target.structurally_static:
                    warnings.append(
                        f'animations.json {effect_path}.trigger_shape '
                        f'references non-triggerable structural group '
                        f'{trigger_shape!r}'
                    )

    morph_pairs, morph_errors = _resolve_morph_pairs(
        list(targets_by_slide),
        config,
    )
    warnings.extend(morph_errors)
    for pair in morph_pairs:
        for slide_name, group_id in (
            (pair.source_slide, pair.source_group_id),
            (pair.destination_slide, pair.destination_group_id),
        ):
            target = known_groups_by_slide.get(slide_name, {}).get(group_id)
            if target is None:
                warnings.append(
                    'animations.json Morph references missing or ambiguous group: '
                    f'{slide_name}/{group_id}'
                )
            elif target.structurally_static:
                warnings.append(
                    'animations.json Morph references structural group: '
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
    transition_defaults = {
        'effect': 'fade',
        'duration': 0.4,
        'sound': None,
    }
    animation_defaults = {
        'effect': 'none',
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
            'transition': {
                'effect': transition_defaults['effect'],
                'duration': transition_defaults['duration'],
            },
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
