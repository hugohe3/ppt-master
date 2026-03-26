#!/usr/bin/env python3
"""
SVG Icon Embedding Tool

Replaces icon placeholders in SVG files with actual icon code.

Placeholder syntax:
    <use data-icon="rocket" x="100" y="200" width="48" height="48" fill="#0076A8"/>

After replacement:
    <g transform="translate(100, 200) scale(3)" fill="#0076A8">
      <path d="..."/>
    </g>

Usage:
    python3 scripts/svg_finalize/embed_icons.py <svg_file> [svg_file2] ...
    python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg

Options:
    --icons-dir <path>    Icon directory path (default: templates/icons/)
    --dry-run             Only show what would be replaced, without modifying files
    --verbose             Show detailed information
"""

import os
import re
import sys
import argparse
from pathlib import Path


# Default icon directory
DEFAULT_ICONS_DIR = Path(__file__).parent.parent.parent / 'templates' / 'icons'

# Icon base size
ICON_BASE_SIZE = 16


def extract_paths_from_icon(icon_path: Path) -> list[str]:
    """
    Extract all path elements from an icon SVG file.

    Args:
        icon_path: Icon file path

    Returns:
        List of path elements (without fill attribute)
    """
    if not icon_path.exists():
        return []
    
    content = icon_path.read_text(encoding='utf-8')
    
    # Match all <path ... /> elements
    path_pattern = r'<path\s+([^>]*)/>'
    matches = re.findall(path_pattern, content, re.DOTALL)
    
    paths = []
    for attrs in matches:
        # Remove fill attribute (will be set uniformly on the outer <g>)
        attrs_clean = re.sub(r'\s*fill="[^"]*"', '', attrs)
        paths.append(f'<path {attrs_clean.strip()}/>')
    
    return paths


def parse_use_element(use_match: str) -> dict:
    """
    Parse attributes of a use element.

    Args:
        use_match: Complete string of the use element

    Returns:
        Attribute dictionary
    """
    attrs = {}
    
    # Extract data-icon
    icon_match = re.search(r'data-icon="([^"]+)"', use_match)
    if icon_match:
        attrs['icon'] = icon_match.group(1)
    
    # Extract numeric attributes
    for attr in ['x', 'y', 'width', 'height']:
        match = re.search(rf'{attr}="([^"]+)"', use_match)
        if match:
            attrs[attr] = float(match.group(1))
    
    # Extract fill color
    fill_match = re.search(r'fill="([^"]+)"', use_match)
    if fill_match:
        attrs['fill'] = fill_match.group(1)
    
    return attrs


def generate_icon_group(attrs: dict, paths: list[str]) -> str:
    """
    Generate the icon's <g> element.

    Args:
        attrs: Attributes of the use element
        paths: List of icon path elements

    Returns:
        Complete <g> element string
    """
    x = attrs.get('x', 0)
    y = attrs.get('y', 0)
    width = attrs.get('width', ICON_BASE_SIZE)
    height = attrs.get('height', ICON_BASE_SIZE)
    fill = attrs.get('fill', '#000000')
    icon_name = attrs.get('icon', 'unknown')
    
    # Calculate scale factor (based on width, assuming uniform scaling)
    scale = width / ICON_BASE_SIZE
    
    # Build transform
    if scale == 1:
        transform = f'translate({x}, {y})'
    else:
        transform = f'translate({x}, {y}) scale({scale})'
    
    # Generate <g> element
    paths_str = '\n    '.join(paths)
    
    return f'''<!-- icon: {icon_name} -->
  <g transform="{transform}" fill="{fill}">
    {paths_str}
  </g>'''


def process_svg_file(svg_path: Path, icons_dir: Path, dry_run: bool = False, verbose: bool = False) -> int:
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
    
    # Match <use data-icon="xxx" ... /> elements
    use_pattern = r'<use\s+[^>]*data-icon="[^"]*"[^>]*/>'
    matches = list(re.finditer(use_pattern, content))
    
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
        
        icon_path = icons_dir / f'{icon_name}.svg'
        paths = extract_paths_from_icon(icon_path)
        
        if not paths:
            print(f"[WARN] Icon not found: {icon_name} (in {svg_path.name})")
            continue
        
        replacement = generate_icon_group(attrs, paths)
        
        if verbose or dry_run:
            print(f"  [*] {icon_name}: x={attrs.get('x', 0)}, y={attrs.get('y', 0)}, "
                  f"size={attrs.get('width', 16)}, fill={attrs.get('fill', '#000000')}")
        
        new_content = new_content[:match.start()] + replacement + new_content[match.end():]
        replaced_count += 1
    
    if not dry_run and replaced_count > 0:
        svg_path.write_text(new_content, encoding='utf-8')
    
    status = "[PREVIEW]" if dry_run else "[OK]"
    print(f"{status} {svg_path.name} ({replaced_count} icons)")
    
    return replaced_count


def main():
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
