"""Animation sidecar loading, SVG target scanning, and validation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .drawingml_utils import SVG_NS

try:
    from pptx_animations import ANIMATIONS, TRANSITIONS
except ImportError:
    ANIMATIONS = {}
    TRANSITIONS = {}


_NON_VISUAL_TAGS = frozenset(('defs', 'title', 'desc', 'metadata', 'style'))
_CHROME_ID_TOKENS = frozenset({
    'background', 'bg',
    'decoration', 'decorations', 'decor',
    'header', 'footer',
    'chrome', 'watermark',
    'pagenumber', 'pagenum',
    'page-number',
})


@dataclass(frozen=True)
class GroupTarget:
    """Top-level SVG group available for PowerPoint animation anchoring."""

    slide: str
    group_id: str
    order: int
    chrome: bool = False


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
        group_id = child.get('id')
        if not group_id:
            anonymous_groups.append(f'{svg_path.stem}: top-level group #{visual_index}')
            continue
        targets.append(
            GroupTarget(
                slide=svg_path.stem,
                group_id=group_id,
                order=visual_index,
                chrome=is_chrome_id(group_id),
            )
        )

    return targets, anonymous_groups


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


def _valid_animation_effect(effect: str) -> bool:
    return effect == 'none' or effect in ANIMATIONS or effect in ('mixed', 'random')


def _valid_transition_effect(effect: str) -> bool:
    return effect == 'none' or effect in TRANSITIONS


def validate_animation_config(
    project_path: Path,
    config: dict[str, Any] | None = None,
    config_path: str | None = None,
) -> list[str]:
    """Validate sidecar references against current ``svg_output``."""
    if config is None:
        config = load_animation_config(project_path, config_path)
    if not config:
        return []

    warnings: list[str] = []
    targets_by_slide, anonymous_groups = scan_project_targets(project_path)
    for item in anonymous_groups:
        warnings.append(f'{item} has no id and cannot be customized in animations.json')

    known_slides = set(targets_by_slide)
    slides = config.get('slides', {})
    if slides and not isinstance(slides, dict):
        return ['animations.json field "slides" must be an object']

    defaults = config.get('defaults', {})
    if isinstance(defaults, dict):
        _validate_scope_effects(defaults, 'defaults', warnings)

    for slide_name, slide_cfg in (slides or {}).items():
        if slide_name not in known_slides:
            warnings.append(f'animations.json references missing slide: {slide_name}')
            continue
        if not isinstance(slide_cfg, dict):
            warnings.append(f'animations.json slide "{slide_name}" must be an object')
            continue
        _validate_scope_effects(slide_cfg, f'slide "{slide_name}"', warnings)

        known_groups = {target.group_id for target in targets_by_slide[slide_name]}
        groups = slide_cfg.get('groups', {})
        if groups and not isinstance(groups, dict):
            warnings.append(f'animations.json slide "{slide_name}" field "groups" must be an object')
            continue
        for group_id, group_cfg in (groups or {}).items():
            if group_id not in known_groups:
                warnings.append(
                    f'animations.json references missing group: {slide_name}/{group_id}'
                )
            if not isinstance(group_cfg, dict):
                warnings.append(f'animations.json group "{slide_name}/{group_id}" must be an object')
                continue
            effect = group_cfg.get('effect')
            if effect is not None and not _valid_animation_effect(str(effect)):
                warnings.append(
                    f'animations.json group "{slide_name}/{group_id}" has unknown effect: {effect}'
                )
    return warnings


def _validate_scope_effects(scope: dict[str, Any], label: str, warnings: list[str]) -> None:
    transition = scope.get('transition', {})
    if isinstance(transition, dict):
        effect = transition.get('effect')
        if effect is not None and not _valid_transition_effect(str(effect)):
            warnings.append(f'animations.json {label} has unknown transition effect: {effect}')
    animation = scope.get('animation', {})
    if isinstance(animation, dict):
        effect = animation.get('effect')
        if effect is not None and not _valid_animation_effect(str(effect)):
            warnings.append(f'animations.json {label} has unknown animation effect: {effect}')


def build_scaffold(project_path: Path) -> dict[str, Any]:
    """Build an editable animation override scaffold from current SVGs."""
    targets_by_slide, _anonymous = scan_project_targets(project_path)
    slides: dict[str, Any] = {}
    for slide_name, targets in targets_by_slide.items():
        groups: dict[str, Any] = {}
        for target in targets:
            if target.chrome:
                groups[target.group_id] = {'effect': 'none'}
            else:
                groups[target.group_id] = {}
        slides[slide_name] = {'groups': groups}
    return {'version': 1, 'slides': slides}


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
