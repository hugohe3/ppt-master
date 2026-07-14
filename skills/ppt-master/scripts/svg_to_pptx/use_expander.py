"""In-memory expansion of project icons and static local ``<use>`` elements.

The icon placeholder ``<use data-icon="...">`` is a project-internal SVG
extension; standard renderers (browsers, PowerPoint's SVG parser) and our
own DrawingML dispatcher do not understand it. ``finalize_svg`` already
expands it on disk into ``svg_final/``; this module provides the same
expansion in memory so ``svg_to_pptx`` can consume ``svg_output/`` directly
without first running the on-disk finalize step.

Public API:
    expand_use_data_icons(root, icons_dir, fallback_dir=None) -> int
        Walk the SVG element tree, replace every ``<use data-icon="...">``
        with its expanded ``<g>`` group of primitive shapes, and return
        the number of replacements made.
    expand_local_use_references(root) -> int
        Materialize same-document ``href="#id"`` references, including
        ``<symbol>`` viewBox mapping, and return the number of instances.
    expand_local_use_references_in_file(svg_path) -> int
        Apply the same expansion to an SVG file in place.

The heavy lifting (icon resolution, color application, scaling) is
delegated to ``svg_finalize.embed_icons`` so the two pipelines stay
behaviourally aligned.
"""

from __future__ import annotations

import copy
import math
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

_LOCAL_HREF_RE = re.compile(r'^#([^#\s]+)$')
_LENGTH_RE = re.compile(
    r'^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(?:px)?\s*$'
)
_VIEWBOX_SPLIT_RE = re.compile(r'[\s,]+')
_URL_REF_RE = re.compile(r'''url\(#([^#\s()'"\\]+)\)''')
_URL_FUNCTION_RE = re.compile(r'\burl\s*\([^)]*\)', re.IGNORECASE)
_URL_FUNCTION_START_RE = re.compile(r'\burl\s*\(', re.IGNORECASE)
_MAX_LOCAL_USE_DEPTH = 64
_MAX_LOCAL_USE_INSTANCES = 10_000
_NON_REUSABLE_METADATA_PREFIXES = (
    'data-pptx-layer',
    'data-pptx-replace-with',
    'data-pptx-replacement-',
    'data-pptx-import-source',
    'data-pptx-fallback-',
    'data-pptx-native',
    'data-pptx-visual-status',
    'data-pptx-route-status',
    'data-pptx-placeholder',
)
_REFERENCE_TAGS = frozenset({
    'symbol', 'g', 'use',
    'rect', 'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline',
    'text', 'image',
})


class UseExpansionError(ValueError):
    """Raised when a static local ``<use>`` cannot be expanded safely."""


def _local_tag(elem: ET.Element) -> str:
    """Return an ElementTree node's local tag name."""
    return elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)


def _qualified_tag(elem: ET.Element, local: str) -> str:
    """Return ``local`` in the same namespace as ``elem``."""
    tag = str(elem.tag)
    if tag.startswith('{') and '}' in tag:
        return f'{tag.split("}", 1)[0]}}}{local}'
    return local


def _fmt_number(value: float) -> str:
    """Format a finite SVG transform number without negative zero."""
    if abs(value) < 1e-12:
        value = 0.0
    return f'{value:.12g}'


def _numeric_length(
    elem: ET.Element,
    name: str,
    default: float | None = None,
) -> float | None:
    """Parse a unitless/px local-use geometry value."""
    raw = elem.get(name)
    if raw is None:
        return default
    match = _LENGTH_RE.fullmatch(raw)
    if match is None:
        raise UseExpansionError(
            f'<use> {name} must be a finite unitless or px value, got {raw!r}'
        )
    value = float(match.group(1))
    if not math.isfinite(value):
        raise UseExpansionError(f'<use> {name} must be finite, got {raw!r}')
    return value


def _parse_viewbox(symbol: ET.Element) -> tuple[float, float, float, float]:
    """Parse a positive four-number symbol viewBox."""
    raw = symbol.get('viewBox', '')
    parts = [part for part in _VIEWBOX_SPLIT_RE.split(raw.strip()) if part]
    if len(parts) != 4:
        raise UseExpansionError(
            '<symbol> referenced by <use> must define a four-number viewBox'
        )
    try:
        values = tuple(float(part) for part in parts)
    except ValueError as exc:
        raise UseExpansionError(
            f'<symbol> viewBox contains a non-numeric value: {raw!r}'
        ) from exc
    if not all(math.isfinite(value) for value in values):
        raise UseExpansionError(f'<symbol> viewBox must be finite, got {raw!r}')
    min_x, min_y, width, height = values
    if width <= 0 or height <= 0:
        raise UseExpansionError(
            f'<symbol> viewBox width/height must be positive, got {raw!r}'
        )
    return min_x, min_y, width, height


def _symbol_viewport_transform(symbol: ET.Element, use_elem: ET.Element) -> str:
    """Map one symbol viewBox into the use element's explicit viewport."""
    for attr in ('refX', 'refY'):
        if symbol.get(attr) is not None:
            raise UseExpansionError(
                f'<symbol> {attr} is not supported by local <use> expansion'
            )

    min_x, min_y, view_width, view_height = _parse_viewbox(symbol)
    width = _numeric_length(use_elem, 'width')
    height = _numeric_length(use_elem, 'height')
    if width is None or height is None or width <= 0 or height <= 0:
        raise UseExpansionError(
            '<use> referencing <symbol> requires positive numeric width and height'
        )

    raw_aspect = symbol.get('preserveAspectRatio', 'xMidYMid meet').strip()
    parts = raw_aspect.split()
    if parts and parts[0] == 'defer':
        parts.pop(0)
    align = parts[0] if parts else 'xMidYMid'
    mode = parts[1] if len(parts) > 1 else 'meet'
    if len(parts) > 2 or mode not in {'meet', 'slice'}:
        raise UseExpansionError(
            f'Unsupported symbol preserveAspectRatio: {raw_aspect!r}'
        )

    if align == 'none':
        if len(parts) > 1:
            raise UseExpansionError(
                f'Unsupported symbol preserveAspectRatio: {raw_aspect!r}'
            )
        scale_x = width / view_width
        scale_y = height / view_height
        translate_x = -min_x * scale_x
        translate_y = -min_y * scale_y
    else:
        alignments = {
            'xMinYMin': (0.0, 0.0), 'xMidYMin': (0.5, 0.0), 'xMaxYMin': (1.0, 0.0),
            'xMinYMid': (0.0, 0.5), 'xMidYMid': (0.5, 0.5), 'xMaxYMid': (1.0, 0.5),
            'xMinYMax': (0.0, 1.0), 'xMidYMax': (0.5, 1.0), 'xMaxYMax': (1.0, 1.0),
        }
        if align not in alignments:
            raise UseExpansionError(
                f'Unsupported symbol preserveAspectRatio: {raw_aspect!r}'
            )
        if mode == 'slice':
            raise UseExpansionError(
                'symbol preserveAspectRatio="... slice" requires viewport clipping, '
                'which local <use> expansion does not approximate'
            )
        scale = min(width / view_width, height / view_height)
        scale_x = scale_y = scale
        align_x, align_y = alignments[align]
        translate_x = (width - view_width * scale) * align_x - min_x * scale
        translate_y = (height - view_height * scale) * align_y - min_y * scale

    return (
        f'matrix({_fmt_number(scale_x)} 0 0 {_fmt_number(scale_y)} '
        f'{_fmt_number(translate_x)} {_fmt_number(translate_y)})'
    )


class _LocalUseExpander:
    """Materialize static same-document SVG use references."""

    def __init__(self, root: ET.Element):
        self.root = root
        self.targets: dict[str, ET.Element] = {}
        self.duplicate_ids: set[str] = set()
        self.used_ids: set[str] = set()
        self.instance_index = 0
        self.instances_started = 0
        self.expanded = 0
        for elem in root.iter():
            elem_id = elem.get('id')
            if not elem_id:
                continue
            self.used_ids.add(elem_id)
            if elem_id in self.targets:
                self.duplicate_ids.add(elem_id)
            else:
                self.targets[elem_id] = elem

    def expand(self) -> int:
        """Expand every visible non-data-icon use node in the document."""
        self._expand_children(self.root, ())
        return self.expanded

    def _expand_children(self, parent: ET.Element, stack: tuple[str, ...]) -> None:
        for index, child in enumerate(list(parent)):
            if _local_tag(child) == 'defs':
                continue
            if _local_tag(child) == 'use' and not child.get('data-icon'):
                replacement = self._materialize_use(child, stack)
                parent.remove(child)
                parent.insert(index, replacement)
                continue
            self._expand_children(child, stack)

    def _materialize_use(
        self,
        use_elem: ET.Element,
        stack: tuple[str, ...],
    ) -> ET.Element:
        self.instances_started += 1
        if self.instances_started > _MAX_LOCAL_USE_INSTANCES:
            raise UseExpansionError(
                'Local <use> expansion exceeds the 10000-instance safety limit'
            )

        href = use_elem.get('href')
        xlink_href = use_elem.get(f'{{{XLINK_NS}}}href')
        if href is not None and xlink_href is not None:
            if href != xlink_href:
                raise UseExpansionError(
                    'Conflicting href and xlink:href values on local <use>'
                )
        if href is None:
            href = xlink_href
        match = _LOCAL_HREF_RE.fullmatch(href or '')
        if match is None:
            raise UseExpansionError(
                '<use> must reference a same-document fragment with href="#id"; '
                f'got {href!r}'
            )
        ref_id = match.group(1)
        if len(stack) >= _MAX_LOCAL_USE_DEPTH:
            chain = ' -> '.join((*stack, ref_id))
            raise UseExpansionError(
                f'Local <use> expansion exceeds the 64-reference depth limit: {chain}'
            )
        if ref_id in self.duplicate_ids:
            raise UseExpansionError(
                f'<use href="#{ref_id}"> is ambiguous because the id is duplicated'
            )
        use_id = use_elem.get('id')
        if use_id and use_id in self.duplicate_ids:
            raise UseExpansionError(
                f'Local <use> instance id {use_id!r} is duplicated in this SVG'
            )
        target = self.targets.get(ref_id)
        if target is None:
            raise UseExpansionError(
                f'<use href="#{ref_id}"> has no matching element in this SVG'
            )
        if ref_id in stack:
            chain = ' -> '.join((*stack, ref_id))
            raise UseExpansionError(f'Circular local <use> reference: {chain}')

        target_tag = _local_tag(target)
        if target_tag not in _REFERENCE_TAGS:
            raise UseExpansionError(
                f'<use href="#{ref_id}"> references unsupported <{target_tag}>'
            )

        self._reject_structural_metadata(use_elem, 'instance')
        self._reject_structural_metadata(target, f'target #{ref_id}')
        self._validate_fragment_reference_syntax(use_elem, 'instance')
        self._validate_fragment_reference_syntax(target, f'target #{ref_id}')

        target_ids = {
            elem_id
            for elem in target.iter()
            if (elem_id := elem.get('id'))
        }
        ambiguous_ids = sorted(target_ids & self.duplicate_ids)
        if ambiguous_ids:
            joined = ', '.join(ambiguous_ids)
            raise UseExpansionError(
                f'<use href="#{ref_id}"> references a subtree with duplicate id(s): '
                f'{joined}'
            )

        next_stack = (*stack, ref_id)
        target_clone = copy.deepcopy(target)
        if target_tag == 'use':
            clone = self._materialize_use(target_clone, next_stack)
        else:
            clone = target_clone
            if target_tag == 'symbol':
                clone.tag = _qualified_tag(clone, 'g')
                viewport_transform = _symbol_viewport_transform(target, use_elem)
                existing_transform = clone.get('transform', '').strip()
                clone.set(
                    'transform',
                    f'{existing_transform} {viewport_transform}'.strip(),
                )
                for attr in ('viewBox', 'preserveAspectRatio', 'x', 'y', 'width', 'height'):
                    clone.attrib.pop(attr, None)
            self._expand_children(clone, next_stack)

        self._rewrite_clone_ids(clone, self._next_instance_prefix(clone))
        wrapper = self._build_wrapper(use_elem)
        wrapper.append(clone)
        self.expanded += 1
        return wrapper

    @staticmethod
    def _reject_structural_metadata(elem: ET.Element, label: str) -> None:
        """Reject reusable template/native markers parsed before expansion."""
        for candidate in elem.iter():
            for attr in candidate.attrib:
                if attr.startswith(_NON_REUSABLE_METADATA_PREFIXES):
                    raise UseExpansionError(
                        f'Local <use> {label} cannot carry structural {attr} metadata'
                    )

    def _validate_fragment_reference_syntax(
        self,
        elem: ET.Element,
        label: str,
    ) -> None:
        """Reject URL fragment forms the clone rewriter cannot preserve."""
        for candidate in elem.iter():
            for value in candidate.attrib.values():
                starts = list(_URL_FUNCTION_START_RE.finditer(value))
                if not starts:
                    continue
                functions = list(_URL_FUNCTION_RE.finditer(value))
                if len(functions) != len(starts):
                    raise UseExpansionError(
                        f'Local <use> {label} has malformed url(...) reference {value!r}'
                    )
                for function in functions:
                    raw = function.group(0)
                    match = _URL_REF_RE.fullmatch(raw)
                    if match is None:
                        raise UseExpansionError(
                            f'Local <use> {label} requires exact url(#id) fragments; '
                            f'got {raw!r}'
                        )
                    ref_id = match.group(1)
                    if ref_id in self.duplicate_ids:
                        raise UseExpansionError(
                            f'Local <use> {label} has ambiguous url(#{ref_id}); '
                            'the referenced id is duplicated'
                        )
                    if ref_id not in self.targets:
                        raise UseExpansionError(
                            f'Local <use> {label} has unresolved url(#{ref_id})'
                        )

    def _next_instance_prefix(self, clone: ET.Element) -> str:
        """Reserve a deterministic clone prefix that cannot collide."""
        clone_ids = {
            elem_id
            for elem in clone.iter()
            if (elem_id := elem.get('id'))
        }
        while True:
            self.instance_index += 1
            prefix = f'use-instance-{self.instance_index}-'
            generated_ids = {f'{prefix}{elem_id}' for elem_id in clone_ids}
            if not generated_ids & self.used_ids:
                self.used_ids.update(generated_ids)
                return prefix

    @staticmethod
    def _rewrite_clone_ids(clone: ET.Element, prefix: str) -> None:
        """Make materialized IDs instance-local and rewrite fragment refs."""
        id_map: dict[str, str] = {}
        for elem in clone.iter():
            elem_id = elem.get('id')
            if elem_id:
                id_map[elem_id] = f'{prefix}{elem_id}'
        if not id_map:
            return
        for elem in clone.iter():
            elem_id = elem.get('id')
            if elem_id in id_map:
                elem.set('id', id_map[elem_id])
            for attr, value in list(elem.attrib.items()):
                if attr in {'href', f'{{{XLINK_NS}}}href'} and value.startswith('#'):
                    ref_id = value[1:]
                    if ref_id in id_map:
                        elem.set(attr, f'#{id_map[ref_id]}')
                    continue
                rewritten = _URL_REF_RE.sub(
                    lambda match: f'url(#{id_map.get(match.group(1), match.group(1))})',
                    value,
                )
                if rewritten != value:
                    elem.set(attr, rewritten)

    @staticmethod
    def _build_wrapper(use_elem: ET.Element) -> ET.Element:
        """Create an inheriting group for use styles and instance geometry."""
        wrapper = ET.Element(_qualified_tag(use_elem, 'g'))
        skipped = {
            'href', f'{{{XLINK_NS}}}href',
            'x', 'y', 'width', 'height', 'preserveAspectRatio', 'transform',
        }
        for attr, value in use_elem.attrib.items():
            if attr not in skipped:
                wrapper.set(attr, value)

        x = _numeric_length(use_elem, 'x', 0.0) or 0.0
        y = _numeric_length(use_elem, 'y', 0.0) or 0.0
        transforms = []
        use_transform = use_elem.get('transform', '').strip()
        if use_transform:
            transforms.append(use_transform)
        if x or y:
            transforms.append(f'translate({_fmt_number(x)} {_fmt_number(y)})')
        if transforms:
            wrapper.set('transform', ' '.join(transforms))
        return wrapper


def expand_local_use_references(root: ET.Element) -> int:
    """Expand static same-document ``<use href="#id">`` references."""
    return _LocalUseExpander(root).expand()


def validate_local_use_references(root: ET.Element) -> list[str]:
    """Return expansion errors without mutating the caller's SVG tree."""
    try:
        expand_local_use_references(copy.deepcopy(root))
    except UseExpansionError as exc:
        return [str(exc)]
    return []


def expand_local_use_references_in_file(svg_path: Path) -> int:
    """Expand local use references in one SVG file in place."""
    tree = ET.parse(str(svg_path))
    count = expand_local_use_references(tree.getroot())
    if count:
        ET.register_namespace('', SVG_NS)
        ET.register_namespace('xlink', XLINK_NS)
        tree.write(str(svg_path), encoding='unicode', xml_declaration=False)
    return count


def _import_embed_icons():
    """Lazy import so svg_to_pptx doesn't hard-require svg_finalize at import time."""
    scripts_dir = Path(__file__).resolve().parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from svg_finalize import embed_icons  # type: ignore
    return embed_icons


def _build_replacement_g(
    use_elem: ET.Element,
    icons_dir: Path,
    fallback_dir: Path | None,
    embed_icons_mod,
) -> ET.Element | None:
    """Resolve a single ``<use data-icon="...">`` into an expanded ``<g>``.

    Returns None when the icon name is missing, unresolved, or the icon
    file cannot be parsed. Callers should leave the original ``<use>`` in
    place in that case (matching the on-disk finalize_svg behaviour, which
    also leaves unresolvable placeholders untouched).
    """
    use_str = ET.tostring(use_elem, encoding='unicode')
    attrs = embed_icons_mod.parse_use_element(use_str)
    if 'icon' not in attrs:
        return None

    icon_path, _base_size = embed_icons_mod.resolve_icon_path(
        attrs['icon'], icons_dir, fallback_dir,
    )
    if not icon_path.exists():
        return None

    color = attrs.get('fill', '#000000')
    elements, style, base_size = embed_icons_mod.extract_paths_from_icon(
        icon_path, color,
    )
    if not elements:
        return None

    g_xml = embed_icons_mod.generate_icon_group(attrs, elements, style, base_size)

    # Wrap with a namespaced root so the parsed subtree carries the SVG
    # namespace through to every primitive (path/circle/...).
    wrapped = f'<svg xmlns="{SVG_NS}">{g_xml}</svg>'
    try:
        parsed_root = ET.fromstring(wrapped)
    except ET.ParseError:
        return None

    for child in parsed_root:
        local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if local == 'g':
            return child
    return None


def expand_use_data_icons(
    root: ET.Element,
    icons_dir: Path,
    fallback_dir: Path | None = None,
) -> int:
    """Replace every ``<use data-icon="...">`` in *root* with its expansion.

    Walks the tree, finds use elements that carry a ``data-icon`` attribute,
    builds a new ``<g>`` subtree from the project icon library (falling back to
    the global library when supplied), and swaps it into the parent element at
    the same position.

    Returns the number of placeholders successfully expanded. Unresolvable
    placeholders are left in place so callers can decide whether to warn.
    """
    if not icons_dir.exists():
        return 0

    embed_icons_mod = _import_embed_icons()

    # ElementTree elements don't carry a parent reference, so build a map.
    parent_of: dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in parent:
            parent_of[child] = parent

    targets: list[ET.Element] = []
    for elem in root.iter():
        local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if local == 'use' and elem.get('data-icon'):
            targets.append(elem)

    expanded = 0
    for use_elem in targets:
        parent = parent_of.get(use_elem)
        if parent is None:
            continue
        replacement = _build_replacement_g(use_elem, icons_dir, fallback_dir, embed_icons_mod)
        if replacement is None:
            continue
        idx = list(parent).index(use_elem)
        parent.remove(use_elem)
        parent.insert(idx, replacement)
        expanded += 1

    return expanded
