#!/usr/bin/env python3
"""
PPT Master - Project Utilities Module

Provides common functions for project information parsing and validation,
reusable by other tools.
"""

import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from console_encoding import configure_utf8_stdio
from svg_to_pptx.canvas_contract import (
    CanvasContractError,
    parse_project_viewbox,
    read_project_viewbox,
)

configure_utf8_stdio()

# Canvas format definitions (unified source)
try:
    from config import CANVAS_FORMATS
except ImportError:
    # Fallback: maintain minimal usable configuration to avoid runtime crashes
    CANVAS_FORMATS = {
        'ppt169': {
            'name': 'PPT 16:9',
            'dimensions': '1280×720',
            'viewbox': '0 0 1280 720',
            'aspect_ratio': '16:9'
        },
        'ppt43': {
            'name': 'PPT 4:3',
            'dimensions': '1024×768',
            'viewbox': '0 0 1024 768',
            'aspect_ratio': '4:3'
        },
        'wechat': {
            'name': 'WeChat Article Header',
            'dimensions': '900×383',
            'viewbox': '0 0 900 383',
            'aspect_ratio': '2.35:1'
        },
        'xiaohongshu': {
            'name': '小红书',
            'dimensions': '1242×1660',
            'viewbox': '0 0 1242 1660',
            'aspect_ratio': '3:4'
        },
        'moments': {
            'name': 'Moments/Instagram',
            'dimensions': '1080×1080',
            'viewbox': '0 0 1080 1080',
            'aspect_ratio': '1:1'
        },
        'story': {
            'name': 'Story/Vertical',
            'dimensions': '1080×1920',
            'viewbox': '0 0 1080 1920',
            'aspect_ratio': '9:16'
        },
        'banner': {
            'name': 'Horizontal Banner',
            'dimensions': '1920×1080',
            'viewbox': '0 0 1920 1080',
            'aspect_ratio': '16:9'
        },
        'a4': {
            'name': 'A4 Print',
            'dimensions': '1240×1754',
            'viewbox': '0 0 1240 1754',
            'aspect_ratio': '√2:1'
        }
    }

CANVAS_FORMAT_ALIASES = {
    'xhs': 'xiaohongshu',
    'wechat_moment': 'moments',
    'wechat-moment': 'moments',
    '朋友圈': 'moments',
    '小红书': 'xiaohongshu',
}

_DESIGN_SPEC_NAMES = (
    'design_spec.md',
    '设计规范与内容大纲.md',
    'design_specification.md',
    '设计规范.md',
)
_COMMUNICATION_TRACE_KEYS = (
    'audience',
    'objective',
    'core_message',
)


def normalize_canvas_format(format_key: str) -> str:
    """Normalize canvas format key name (supports common aliases)."""
    if not format_key:
        return ''
    key = format_key.strip().lower()
    return CANVAS_FORMAT_ALIASES.get(key, key)


def parse_project_name(dir_name: str) -> Dict[str, str]:
    """
    Parse project information from the project directory name.

    Args:
        dir_name: Project directory name

    Returns:
        Dictionary containing name, format, date
    """
    result = {
        'name': dir_name,
        'format': 'unknown',
        'format_name': 'Unknown format',
        'date': 'unknown',
        'date_formatted': 'Unknown date'
    }

    dir_name_lower = dir_name.lower()

    # Extract date (format: _YYYYMMDD)
    date_match = re.search(r'_(\d{8})$', dir_name)
    if date_match:
        date_str = date_match.group(1)
        result['date'] = date_str
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            result['date_formatted'] = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Prefer parsing standard format: name_format_YYYYMMDD
    full_match = re.match(r'^(?P<name>.+)_(?P<format>[a-z0-9_-]+)_(?P<date>\d{8})$', dir_name_lower)
    if full_match:
        raw_format = full_match.group('format')
        normalized_format = normalize_canvas_format(raw_format)
        if normalized_format in CANVAS_FORMATS:
            result['format'] = normalized_format
            result['format_name'] = CANVAS_FORMATS[normalized_format]['name']
            result['name'] = dir_name[:len(full_match.group('name'))]
            return result

    # Fallback: only match trailing `_format` to avoid deleting parts of the project name
    sorted_formats = sorted(CANVAS_FORMATS.keys(), key=len, reverse=True)
    for fmt_key in sorted_formats:
        if re.search(rf'_{re.escape(fmt_key)}(?:_\d{{8}})?$', dir_name_lower):
            result['format'] = fmt_key
            result['format_name'] = CANVAS_FORMATS[fmt_key]['name']
            break

    # Extract project name (only remove trailing date and format suffix)
    name = re.sub(r'_\d{8}$', '', dir_name)
    if result['format'] != 'unknown':
        name = re.sub(rf'_{re.escape(result["format"])}$', '', name, flags=re.IGNORECASE)
    result['name'] = name

    return result


def get_project_info(project_path: str) -> Dict:
    """
    Get detailed project information.

    Args:
        project_path: Project directory path

    Returns:
        Project information dictionary
    """
    project_path = Path(project_path)

    # Parse directory name
    parsed = parse_project_name(project_path.name)

    info = {
        'path': str(project_path),
        'dir_name': project_path.name,
        'name': parsed['name'],
        'format': parsed['format'],
        'format_name': parsed['format_name'],
        'date': parsed['date'],
        'date_formatted': parsed['date_formatted'],
        'exists': project_path.exists(),
        'svg_count': 0,
        'has_spec': False,
        'has_readme': False,
        'has_source': False,
        'source_count': 0,
        'spec_file': None,
        'svg_files': []
    }

    if not project_path.exists():
        return info

    # Check README.md
    info['has_readme'] = (project_path / 'README.md').exists()

    # Check design specification files (current standard + legacy names)
    for spec_file in _DESIGN_SPEC_NAMES:
        if (project_path / spec_file).exists():
            info['has_spec'] = True
            info['spec_file'] = spec_file
            break

    # Check source documents
    legacy_source_file = project_path / '来源文档.md'
    sources_dir = project_path / 'sources'
    info['has_source'] = legacy_source_file.exists() or sources_dir.exists()

    if sources_dir.exists():
        info['source_count'] = len([p for p in sources_dir.iterdir() if p.is_file()])

    # Count SVG files
    svg_output = project_path / 'svg_output'
    if svg_output.exists():
        svg_files = sorted(svg_output.glob('*.svg'))
        info['svg_count'] = len(svg_files)
        info['svg_files'] = [f.name for f in svg_files]

    # Get canvas format details
    if info['format'] in CANVAS_FORMATS:
        info['canvas_info'] = CANVAS_FORMATS[info['format']]

    return info


def validate_communication_trace(
    project_path: str | Path,
    *,
    check_lock: bool = True,
    check_design: bool = True,
) -> List[str]:
    """Validate either or both communication-trace surfaces."""
    root = Path(project_path)
    design_spec = next(
        (root / name for name in _DESIGN_SPEC_NAMES if (root / name).is_file()),
        None,
    )
    if design_spec is None or not (check_lock or check_design):
        return []

    errors: List[str] = []
    lock_path = root / 'spec_lock.md'
    if check_lock:
        if not lock_path.is_file():
            return [
                'Communication trace: missing spec_lock.md with a '
                '## communication section.',
            ]
        try:
            lock_text = lock_path.read_text(encoding='utf-8-sig')
        except OSError as exc:
            return [f'Communication trace: unable to read specification files: {exc}']

        communication_match = re.search(
            r'^##[ \t]+communication[ \t]*$',
            lock_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if communication_match is None:
            errors.append(
                'Communication trace: spec_lock.md must contain a '
                '## communication section.',
            )
        else:
            next_section = re.search(
                r'^##[ \t]+',
                lock_text[communication_match.end():],
                flags=re.MULTILINE,
            )
            section_end = (
                communication_match.end() + next_section.start()
                if next_section
                else len(lock_text)
            )
            communication_block = lock_text[
                communication_match.end():section_end
            ]
            missing_keys = [
                key
                for key in _COMMUNICATION_TRACE_KEYS
                if re.search(
                    rf'^-[ \t]+{re.escape(key)}[ \t]*:',
                    communication_block,
                    flags=re.MULTILINE,
                ) is None
            ]
            if missing_keys:
                errors.append(
                    'Communication trace: spec_lock.md ## communication is '
                    f'missing key line(s): {", ".join(missing_keys)}.',
                )

    if not check_design:
        return errors
    try:
        design_text = design_spec.read_text(encoding='utf-8-sig')
    except OSError as exc:
        return [f'Communication trace: unable to read specification files: {exc}']

    outline_match = re.search(
        r'^##[ \t]+IX\.[ \t]+Content Outline\b.*$',
        design_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if outline_match is None:
        errors.append(
            'Communication trace: design_spec.md must contain '
            '## IX. Content Outline.',
        )
        return errors
    next_section = re.search(
        r'^##[ \t]+',
        design_text[outline_match.end():],
        flags=re.MULTILINE,
    )
    outline_end = (
        outline_match.end() + next_section.start()
        if next_section
        else len(design_text)
    )
    outline = design_text[outline_match.end():outline_end]
    slide_matches = list(re.finditer(
        r'^#{3,6}[ \t]+Slide[ \t]+([0-9]+|NN)\b.*$',
        outline,
        flags=re.IGNORECASE | re.MULTILINE,
    ))
    if not slide_matches:
        errors.append(
            'Communication trace: design_spec.md §IX contains no Slide blocks.',
        )
        return errors

    missing_moves = []
    for index, slide_match in enumerate(slide_matches):
        block_end = (
            slide_matches[index + 1].start()
            if index + 1 < len(slide_matches)
            else len(outline)
        )
        slide_block = outline[slide_match.end():block_end]
        if re.search(
            r'^[ \t]*-[ \t]+(?:\*\*)?Audience move(?:\*\*)?[ \t]*:',
            slide_block,
            flags=re.IGNORECASE | re.MULTILINE,
        ) is None:
            missing_moves.append(slide_match.group(1))
    if missing_moves:
        errors.append(
            'Communication trace: every design_spec.md §IX Slide block must '
            'contain an Audience move line; missing on Slide '
            f'{", ".join(missing_moves)}.',
        )
    return errors


def validate_project_structure(
    project_path: str,
    verbose: bool = False,
    *,
    validate_communication: bool = True,
) -> Tuple[bool, List[str], List[str]]:
    """
    Validate project structure completeness.

    Args:
        project_path: Project directory path
        verbose: Whether to show detailed fix suggestions
        validate_communication: Whether to run the communication trace check

    Returns:
        (is_valid, error_list, warning_list)
    """
    project_path = Path(project_path)
    errors = []
    warnings = []

    # Try to import error helper
    try:
        from error_helper import ErrorHelper
        use_helper = True
    except ImportError:
        use_helper = False

    # Check if directory exists
    if not project_path.exists():
        msg = f"Project directory does not exist: {project_path}"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_directory',
                                                           {'project_path': str(project_path)})
        errors.append(msg)
        return False, errors, warnings

    if not project_path.is_dir():
        errors.append(f"Not a valid directory: {project_path}")
        return False, errors, warnings

    # Check required files
    if not (project_path / 'README.md').exists():
        msg = "Missing required file: README.md"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_readme',
                                                           {'project_path': str(project_path)})
        errors.append(msg)

    # Check design specification file
    has_spec = any((project_path / name).exists() for name in _DESIGN_SPEC_NAMES)
    if not has_spec:
        msg = "Missing design specification file (suggested filename: design_spec.md)"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_spec')
        warnings.append(msg)
    elif validate_communication:
        errors.extend(validate_communication_trace(project_path))

    # Check svg_output directory
    svg_output = project_path / 'svg_output'
    if not svg_output.exists():
        msg = "Missing svg_output directory"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_svg_output')
        errors.append(msg)
    elif not svg_output.is_dir():
        errors.append("svg_output is not a directory")
    else:
        # Check for SVG files
        svg_files = list(svg_output.glob('*.svg'))
        if not svg_files:
            msg = "svg_output directory is empty, no SVG files found"
            if use_helper and verbose:
                msg += "\n" + \
                    ErrorHelper.format_error_message('empty_svg_output')
            warnings.append(msg)
        else:
            # Validate SVG file naming (consistent with project_manager.py)
            for svg_file in svg_files:
                if not re.match(r'^(slide_\d+_\w+|P?\d+_.+)\.svg$', svg_file.name):
                    msg = f"Non-standard SVG file naming: {svg_file.name}"
                    if use_helper and verbose:
                        msg += "\n" + ErrorHelper.format_error_message('invalid_svg_naming',
                                                                       {'file_name': svg_file.name})
                    warnings.append(msg)

    # Check directory naming format
    dir_name = project_path.name
    if not re.search(r'_\d{8}$', dir_name):
        msg = f"Directory name missing date suffix (_YYYYMMDD): {dir_name}"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_date_suffix')
        warnings.append(msg)

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_svg_viewbox(svg_files: List[Path], expected_format: Optional[str] = None) -> List[str]:
    """
    Validate the viewBox settings of SVG files.

    Args:
        svg_files: List of SVG files
        expected_format: Expected canvas format (e.g. 'ppt169')

    Returns:
        List of warnings
    """
    warnings = []
    viewboxes = {}

    # Determine expected viewBox
    expected_viewbox = None
    if expected_format and expected_format in CANVAS_FORMATS:
        expected_viewbox = parse_project_viewbox(
            CANVAS_FORMATS[expected_format]['viewbox'],
            context=f"canvas format {expected_format!r}",
        )

    for svg_file in svg_files:
        try:
            viewbox = read_project_viewbox(svg_file)
        except CanvasContractError as exc:
            warnings.append(str(exc))
            continue
        viewboxes[svg_file.name] = viewbox
        if expected_viewbox and viewbox != expected_viewbox:
            warnings.append(
                f"{svg_file.name}: root viewBox '{viewbox.canonical}' must match "
                f"project format '{expected_format}' ({expected_viewbox.canonical})"
            )

    # Check for multiple different viewBoxes
    distinct = {viewbox for viewbox in viewboxes.values()}
    if len(distinct) > 1:
        details = ", ".join(
            f"{name}={viewbox.canonical}"
            for name, viewbox in sorted(viewboxes.items())
        )
        warnings.append(
            "All project SVG root viewBoxes must match; found " + details
        )

    return warnings


def find_all_projects(base_dir: str) -> List[Path]:
    """
    Find all projects under the specified directory.

    Args:
        base_dir: Base directory path

    Returns:
        List of project directories
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return []

    projects = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a valid project directory (contains svg_output or design spec)
            has_svg_output = (item / 'svg_output').exists()
            has_spec = any((item / f).exists() for f in
                           ['design_spec.md', '设计规范与内容大纲.md', 'design_specification.md', '设计规范.md'])

            if has_svg_output or has_spec:
                projects.append(item)

    return sorted(projects)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_project_stats(project_path: str) -> Dict:
    """
    Get project statistics.

    Args:
        project_path: Project directory path

    Returns:
        Statistics dictionary
    """
    project_path = Path(project_path)
    stats = {
        'total_files': 0,
        'svg_files': 0,
        'md_files': 0,
        'html_files': 0,
        'total_size': 0,
        'svg_size': 0
    }

    if not project_path.exists():
        return stats

    for file in project_path.rglob('*'):
        if file.is_file():
            stats['total_files'] += 1
            file_size = file.stat().st_size
            stats['total_size'] += file_size

            if file.suffix == '.svg':
                stats['svg_files'] += 1
                stats['svg_size'] += file_size
            elif file.suffix == '.md':
                stats['md_files'] += 1
            elif file.suffix == '.html':
                stats['html_files'] += 1

    return stats


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the diagnostic entry point."""
    parser = argparse.ArgumentParser(description="Inspect and validate a PPT Master project.")
    parser.add_argument("project_path", help="Project directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the diagnostic CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = args.project_path
    info = get_project_info(project_path)

    print(f"\nProject Info: {info['dir_name']}")
    print("=" * 60)
    print(f"Project Name: {info['name']}")
    print(f"Canvas Format: {info['format_name']} ({info['format']})")
    print(f"Created: {info['date_formatted']}")
    print(f"SVG Files: {info['svg_count']}")
    print(f"README: {'Yes' if info['has_readme'] else 'No'}")
    print(f"Design Spec: {'Yes' if info['has_spec'] else 'No'}")

    print("\nValidation Results:")
    print("-" * 60)
    is_valid, errors, warnings = validate_project_structure(project_path)

    if errors:
        print("[ERROR]")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("[WARN]")
        for warning in warnings:
            print(f"  - {warning}")

    if is_valid and not warnings:
        print("[OK] Project structure is complete, no issues found")
    return 0 if is_valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
