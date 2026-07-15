#!/usr/bin/env python3
"""
SVG Icon Embedding Tool

Replaces icon placeholders in SVG files with actual icon code.

Placeholder syntax (new SVGs must include a library prefix):
    <use data-icon="chunk-filled/rocket" x="100" y="200" width="48" height="48" fill="#0076A8"/>
    <use data-icon="tabler-filled/home" x="100" y="200" width="48" height="48" fill="#0076A8"/>
    <use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#0076A8"/>
    <use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#0076A8" stroke-width="3"/>
    <use data-icon="imported/layered_slide_06_ill01"/>

Legacy compatibility accepted by the resolver:
    <use data-icon="rocket" .../> -> chunk-filled/rocket
    <use data-icon="chunk/rocket" .../> -> chunk-filled/rocket

Optional `stroke-width` (stroke-style libraries only — e.g. tabler-outline):
    Default 2 (matches the source). Pass 1.5 for thin, 3 for bold.
    Ignored on fill-style libraries.

After replacement:
    <g transform="translate(100, 200) scale(3)" fill="#0076A8">
      <path d="..."/>
    </g>

Icon libraries (subdirectories of templates/icons/):
    chunk-filled/      - 640+ fill icons, 16x16 viewBox  (use prefix: chunk-filled/name; legacy 'chunk/' also accepted)
    tabler-filled/     - 1000+ fill icons, 24x24 viewBox (use prefix: tabler-filled/name)
    tabler-outline/    - 5000+ stroke icons, 24x24 viewBox (use prefix: tabler-outline/name)
    phosphor-duotone/  - 1200+ duotone icons, 256x256 viewBox (single color + 0.2-opacity backplate)
    simple-icons/      - 3400+ brand logos, 24x24 viewBox (brand-inset library — used alongside the chosen primary library, NOT as a standalone library for generic icons)
    imported/          - project-local extracted vector illustrations with data-icon-style="preserve-color"; preserve source colors and natural viewBox aspect ratio

Usage:
    python3 scripts/svg_finalize/embed_icons.py <svg_file> [svg_file2] ...
    python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg

Options:
    --icons-dir <path>    Icon directory path (default: templates/icons/)
    --dry-run             Only show what would be replaced, without modifying files
    --verbose             Show detailed information
"""

from __future__ import annotations

import os
import re
import sys
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from svg_to_pptx.drawingml.utils import parse_project_geometry_length  # noqa: E402

configure_utf8_stdio()


# Default icon directory
DEFAULT_ICONS_DIR = Path(__file__).parent.parent.parent / 'templates' / 'icons'

# Icon base size per library
ICON_BASE_SIZES = {
    'chunk-filled': 16,
    'chunk': 16,          # backward compat alias → chunk-filled/
    'tabler-filled': 24,
    'tabler-outline': 24,
    'phosphor-duotone': 256,
    'simple-icons': 24,
}
_ICON_LIBRARY_ALIASES = {'chunk': 'chunk-filled'}
DEFAULT_ICON_BASE_SIZE = 24
BaseGeometry = float | tuple[float, float, float, float]


def _get_viewbox_size(content: str) -> float:
    """Extract the width from viewBox attribute (assumed square). Returns 0 if not found."""
    m = re.search(r'viewBox=["\']0 0 ([\d.]+)', content)
    if m:
        return float(m.group(1))
    return 0


def _get_viewbox_geometry(content: str) -> tuple[float, float, float, float] | None:
    """Extract full viewBox geometry as (min_x, min_y, width, height)."""
    match = re.search(r'viewBox=["\']([^"\']+)["\']', content)
    if not match:
        return None
    parts = re.split(r'[\s,]+', match.group(1).strip())
    if len(parts) < 4:
        return None
    try:
        min_x, min_y, width, height = [float(part) for part in parts[:4]]
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return min_x, min_y, width, height


def _format_number(value: object) -> str:
    """Format SVG numeric values compactly without losing meaningful precision."""
    if isinstance(value, float):
        return f'{value:g}'
    return str(value)


def _base_geometry(base_size: BaseGeometry) -> tuple[float, float, float, float]:
    """Normalize legacy square icon size and full viewBox geometry."""
    if isinstance(base_size, tuple):
        return base_size
    return 0.0, 0.0, float(base_size), float(base_size)


def _is_preserve_color_asset(content: str) -> bool:
    """Project illustrations are vector assets, not recolorable monochrome icons.

    The `data-icon-style="preserve-color"` marker is stamped by
    extract_svg_assets.py and is the single source of truth — hand-authored
    multi-color assets must carry it to keep their colors and aspect ratio.
    """
    return 'data-icon-style="preserve-color"' in content


def _detect_icon_style(content: str) -> str:
    """Detect whether an icon is fill-based or stroke-based."""
    # stroke="currentColor" with fill="none" → stroke style
    if 'stroke="currentColor"' in content and 'fill="none"' in content:
        return 'stroke'
    return 'fill'


def _extract_svg_body(content: str) -> list[str]:
    """Return the root SVG body for preserve-color assets without editing attrs."""
    match = re.search(r'<svg\b[^>]*>(.*)</svg>\s*$', content, re.DOTALL)
    if not match:
        return []
    body = match.group(1).strip()
    return [body] if body else []


def _extract_shape_elements(content: str, color: str) -> list[str]:
    """
    Extract all drawable shape elements from an icon SVG, replacing
    fill/stroke color references (currentColor or #xxxxxx) with the target color.

    Supports: <path>, <circle>, <rect>, <line>, <polyline>, <polygon>, <ellipse>
    """
    shape_tags = ('path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse')
    pattern = r'<(' + '|'.join(shape_tags) + r')(\s[^>]*)?(?:/>|></\1>)'
    matches = re.findall(pattern, content, re.DOTALL)

    elements = []
    for tag, attrs in matches:
        # Remove standalone fill/stroke color attrs so outer <g> controls color.
        # Also strip stroke-width so the outer <g> can override it (otherwise the
        # icon's source stroke-width="2" would shadow any caller-specified value).
        attrs_clean = re.sub(r'\s*fill="(?:currentColor|#[0-9a-fA-F]{3,6}|none)"', '', attrs)
        attrs_clean = re.sub(r'\s*stroke="(?:currentColor|#[0-9a-fA-F]{3,6}|none)"', '', attrs_clean)
        attrs_clean = re.sub(r'\s*stroke-width="[^"]*"', '', attrs_clean)
        elements.append(f'<{tag}{attrs_clean}/>')

    return elements


def _resolve_in_dir(icon_name: str, icons_dir: Path) -> tuple[Path, float]:
    """Resolve `icon_name` against a single icons dir (no fallback)."""
    if '/' in icon_name:
        lib, name = icon_name.split('/', 1)
        lib = _ICON_LIBRARY_ALIASES.get(lib, lib)  # resolve aliases
        icon_path = icons_dir / lib / f'{name}.svg'
        base_size = ICON_BASE_SIZES.get(lib, 24)
    else:
        # Backward compatibility: un-prefixed names fall back to legacy chunk-filled/ library
        icon_path = icons_dir / 'chunk-filled' / f'{icon_name}.svg'
        base_size = 16
        if not icon_path.exists():
            icon_path = icons_dir / f'{icon_name}.svg'  # legacy flat layout
            base_size = 16

    return icon_path, base_size


def _casefold_icon_name_in_dir(icon_name: str, icons_dir: Path) -> str | None:
    """Return the exact on-disk identifier when only casing differs."""
    if not icons_dir.is_dir():
        return None

    search_dirs: list[Path] = []
    expected_name = icon_name
    if '/' in icon_name:
        raw_lib, expected_name = icon_name.split('/', 1)
        requested_lib = _ICON_LIBRARY_ALIASES.get(raw_lib.casefold(), raw_lib)
        library_dir = icons_dir / requested_lib
        if not library_dir.is_dir():
            library_dir = next(
                (
                    path for path in icons_dir.iterdir()
                    if path.is_dir()
                    and path.name.casefold() == requested_lib.casefold()
                ),
                library_dir,
            )
        search_dirs.append(library_dir)
    else:
        search_dirs.extend((icons_dir / 'chunk-filled', icons_dir))

    expected_filename = f'{expected_name}.svg'.casefold()
    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        matches = sorted(
            path for path in search_dir.iterdir()
            if path.is_file()
            and path.suffix.casefold() == '.svg'
            and path.name.casefold() == expected_filename
        )
        if len(matches) != 1:
            continue
        relative = matches[0].relative_to(icons_dir).with_suffix('')
        return relative.as_posix()
    return None


def suggest_icon_name(
    icon_name: str,
    icons_dir: Path,
    fallback_dir: Path | None = None,
) -> str | None:
    """Suggest an exact project-first icon identifier without auto-correcting it."""
    suggestion = _casefold_icon_name_in_dir(icon_name, icons_dir)
    if suggestion is None and fallback_dir is not None:
        suggestion = _casefold_icon_name_in_dir(icon_name, fallback_dir)
    return suggestion


def resolve_icon_path(icon_name: str, icons_dir: Path, fallback_dir: Path | None = None) -> tuple[Path, float]:
    """
    Resolve icon name to file path and base size, e.g. "chunk-filled/home" →
    icons_dir/chunk-filled/home.svg. "chunk/" is a backward-compat alias; an
    un-prefixed name falls back to chunk-filled/ then a legacy flat layout.

    Resolution is project-first: if the icon is absent under ``icons_dir`` and a
    ``fallback_dir`` (the global library) is given, the fallback's path is
    returned instead. Returns (path, base_size); the path may not exist when
    neither dir has the icon.
    """
    icon_path, base_size = _resolve_in_dir(icon_name, icons_dir)
    if fallback_dir is not None and not icon_path.exists():
        fb_path, fb_size = _resolve_in_dir(icon_name, fallback_dir)
        if fb_path.exists():
            return fb_path, fb_size
    return icon_path, base_size


def extract_paths_from_icon(icon_path: Path, target_color: str = '#000000') -> tuple[list[str], str, BaseGeometry]:
    """
    Extract drawable elements from an icon SVG file.

    Returns:
        (elements, style, base_size)
        style: 'fill', 'stroke', or 'preserve'
        base_size: square icon size, or full viewBox geometry for preserve assets
    """
    if not icon_path.exists():
        return [], 'fill', 16

    content = icon_path.read_text(encoding='utf-8')
    if _is_preserve_color_asset(content):
        geometry = _get_viewbox_geometry(content) or (0.0, 0.0, DEFAULT_ICON_BASE_SIZE, DEFAULT_ICON_BASE_SIZE)
        elements = _extract_svg_body(content)
        return elements, 'preserve', geometry

    style = _detect_icon_style(content)
    base_size = _get_viewbox_size(content) or 16
    elements = _extract_shape_elements(content, target_color)
    return elements, style, base_size


def _attr_value(tag_text: str, attr: str) -> str | None:
    """Return an attribute value from a raw tag, accepting either quote style."""
    match = re.search(
        rf'\b{re.escape(attr)}\s*=\s*(["\'])(.*?)\1',
        tag_text,
        re.DOTALL,
    )
    return match.group(2) if match else None


def parse_use_element(use_match: str) -> dict[str, str | float]:
    """
    Parse attributes of a use element.

    Args:
        use_match: Complete string of the use element

    Returns:
        Attribute dictionary
    """
    attrs: dict[str, str | float] = {}

    # Extract data-icon
    icon_value = _attr_value(use_match, 'data-icon')
    if icon_value:
        attrs['icon'] = icon_value

    # Extract numeric attributes
    for attr in ['x', 'y', 'width', 'height']:
        value = _attr_value(use_match, attr)
        if value is not None:
            attrs[attr] = parse_project_geometry_length(value, attr)

    # Extract fill color
    fill_value = _attr_value(use_match, 'fill')
    if fill_value is not None:
        attrs['fill'] = fill_value

    # Stroke-style icons may be authored with natural SVG semantics:
    # fill="none" stroke="#HEX". Keep accepting fill as the canonical color
    # carrier, but preserve stroke so outline icons do not collapse to none.
    stroke_value = _attr_value(use_match, 'stroke')
    if stroke_value is not None:
        attrs['stroke'] = stroke_value

    # Live preview direct edits may write an absolute transform matrix back to
    # the placeholder. Preserve it so the expanded icon matches the edited
    # browser geometry instead of falling back to the original x/y placement.
    transform_value = _attr_value(use_match, 'transform')
    if transform_value is not None:
        attrs['transform'] = transform_value

    # Extract optional stroke-width override (stroke-style icons only).
    # Tabler-outline ships at stroke-width=2; passing 1.5 reads thin, 3 reads bold.
    stroke_width_value = _attr_value(use_match, 'stroke-width')
    if stroke_width_value is not None:
        attrs['stroke-width'] = stroke_width_value

    return attrs


def resolve_icon_color(attrs: dict[str, str | float], style: str) -> str:
    """Resolve the caller-provided color for fill or stroke icon libraries."""
    if style == 'preserve':
        return 'preserve'

    fill = str(attrs.get('fill', '')).strip()
    stroke = str(attrs.get('stroke', '')).strip()

    if style == 'stroke':
        if fill and fill != 'none':
            return fill
        if stroke and stroke != 'none':
            return stroke
        return '#000000'

    if fill:
        return fill
    if stroke and stroke != 'none':
        return stroke
    return '#000000'


def generate_icon_group(attrs: dict[str, str | float], elements: list[str], style: str, base_size: BaseGeometry) -> str:
    """
    Generate the icon's <g> element.

    Args:
        attrs:     Attributes of the use element
        elements:  List of drawable SVG elements
        style:     'fill', 'stroke', or 'preserve'
        base_size: Icon's natural size, or full viewBox geometry for preserve assets

    Returns:
        Complete <g> element string
    """
    min_x, min_y, base_width, base_height = _base_geometry(base_size)
    x = attrs.get('x', 0)
    y = attrs.get('y', 0)
    width = attrs.get('width', base_width)
    height = attrs.get('height', base_height)
    color = resolve_icon_color(attrs, style)
    icon_name = attrs.get('icon', 'unknown')

    scale_x = float(width) / base_width
    scale_y = float(height) / base_height

    if attrs.get('transform'):
        # This transform is authoritative: the editor computes it from the
        # expanded <g>, so composing it with x/y would apply placement twice.
        transform = str(attrs['transform'])
    elif abs(scale_x - 1) < 1e-6 and abs(scale_y - 1) < 1e-6:
        transform = f'translate({_format_number(x)}, {_format_number(y)})'
    elif abs(scale_x - scale_y) < 1e-6:
        transform = f'translate({_format_number(x)}, {_format_number(y)}) scale({_format_number(scale_x)})'
    else:
        transform = (
            f'translate({_format_number(x)}, {_format_number(y)}) '
            f'scale({_format_number(scale_x)}, {_format_number(scale_y)})'
        )

    elements_str = '\n    '.join(elements)

    if style == 'preserve':
        if min_x or min_y:
            inner_transform = f'translate({_format_number(-min_x)}, {_format_number(-min_y)})'
            elements_str = f'<g transform="{inner_transform}">\n    {elements_str}\n    </g>'
        return f'''<!-- icon: {icon_name} -->
  <g transform="{transform}">
    {elements_str}
  </g>'''

    if style == 'stroke':
        # Default to 2 — matches the source stroke-width baked into tabler-outline
        # (and any other stroke library) so omitting the attribute reproduces
        # pre-change visual output.
        stroke_width = attrs.get('stroke-width', '2')
        color_attrs = f'fill="none" stroke="{color}" stroke-width="{stroke_width}"'
    else:
        color_attrs = f'fill="{color}"'

    return f'''<!-- icon: {icon_name} -->
  <g transform="{transform}" {color_attrs}>
    {elements_str}
  </g>'''


def process_svg_file(svg_path: Path, icons_dir: Path, dry_run: bool = False, verbose: bool = False, fallback_dir: Path | None = None) -> int:
    """
    Process a single SVG file, replacing all icon placeholders.

    Args:
        svg_path: SVG file path
        icons_dir: Icon directory path
        dry_run: Whether to only preview without modifying
        verbose: Whether to show detailed information

    Returns:
        Number of icons replaced
    """
    if not svg_path.exists():
        print(f"[ERROR] File not found: {svg_path}")
        return 0
    
    content = svg_path.read_text(encoding='utf-8')
    
    # Match self-closing <use data-icon="..."/> placeholders. Attribute
    # parsing below accepts both single and double quotes.
    use_pattern = r'<use\b(?=[^>]*\bdata-icon\s*=)[^>]*/>'
    matches = list(re.finditer(use_pattern, content, re.IGNORECASE | re.DOTALL))
    
    if not matches:
        if verbose:
            print(f"[SKIP] No icon placeholders: {svg_path}")
        return 0
    
    replaced_count = 0
    new_content = content
    
    # Replace from back to front to avoid position offset
    for match in reversed(matches):
        use_str = match.group(0)
        attrs = parse_use_element(use_str)
        
        icon_name = attrs.get('icon')
        if not icon_name:
            continue

        icon_path, _ = resolve_icon_path(str(icon_name), icons_dir, fallback_dir)
        if not icon_path.exists():
            suggestion = suggest_icon_name(str(icon_name), icons_dir, fallback_dir)
            hint = (
                f"; identifiers are case-sensitive; use '{suggestion}'"
                if suggestion else ""
            )
            print(
                f"[WARN] Icon not found: {icon_name}{hint} "
                f"(in {svg_path.name})"
            )
            continue

        elements, style, base_size = extract_paths_from_icon(icon_path)
        color = resolve_icon_color(attrs, style)
        if not elements:
            print(
                f"[WARN] Icon has no embeddable shapes: {icon_name} "
                f"(in {svg_path.name})"
            )
            continue
        
        replacement = generate_icon_group(attrs, elements, style, base_size)
        
        if verbose or dry_run:
            print(f"  [*] {icon_name}: x={attrs.get('x', 0)}, y={attrs.get('y', 0)}, "
                  f"size={attrs.get('width', base_size)}, fill={color}, style={style}")
        
        new_content = new_content[:match.start()] + replacement + new_content[match.end():]
        replaced_count += 1
    
    if not dry_run and replaced_count > 0:
        svg_path.write_text(new_content, encoding='utf-8')
    
    status = "[PREVIEW]" if dry_run else "[OK]"
    print(f"{status} {svg_path.name} ({replaced_count} icons)")
    
    return replaced_count


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Replace icon placeholders in SVG files with actual icon code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 scripts/svg_finalize/embed_icons.py svg_output/01_cover.svg
  python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
  python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
  python3 scripts/svg_finalize/embed_icons.py --icons-dir my_icons/ output.svg
        '''
    )
    
    parser.add_argument('files', nargs='+', help='SVG files to process')
    parser.add_argument('--icons-dir', type=Path, default=DEFAULT_ICONS_DIR,
                        help=f'Icon directory path (default: {DEFAULT_ICONS_DIR})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Only show what would be replaced, without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed information')
    
    args = parser.parse_args()
    
    # Validate icon directory
    if not args.icons_dir.exists():
        print(f"[ERROR] Icon directory not found: {args.icons_dir}")
        sys.exit(1)

    print(f"[DIR] Icon directory: {args.icons_dir}")
    if args.dry_run:
        print("[PREVIEW] Preview mode (no files will be modified)")
    print()
    
    total_replaced = 0
    total_files = 0
    
    for file_pattern in args.files:
        svg_path = Path(file_pattern)
        if svg_path.exists():
            count = process_svg_file(svg_path, args.icons_dir, args.dry_run, args.verbose)
            total_replaced += count
            if count > 0:
                total_files += 1
    
    print()
    print(f"[Summary] Total: {total_files} file(s), {total_replaced} icon(s)" +
          (" (preview)" if args.dry_run else " replaced"))


if __name__ == '__main__':
    main()
