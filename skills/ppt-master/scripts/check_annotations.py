#!/usr/bin/env python3
"""
PPT Master - SVG Annotation Checker

Scans SVG files for edit annotations (data-edit-target / data-edit-annotation attributes)
and prints a human-readable summary. Used by AI agents to discover pending annotations.

Usage:
    python3 scripts/check_annotations.py <project_dir>
    python3 scripts/check_annotations.py <svg_file>

Examples:
    python3 scripts/check_annotations.py projects/my-project
    python3 scripts/check_annotations.py projects/my-project/svg_output/slide_01.svg

Dependencies:
    None (only uses standard library)
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def scan_svg_file(svg_path: Path) -> list[dict]:
    """
    Scan a single SVG file for annotations.

    Returns list of dicts: element_id, tag, annotation, content_preview.
    """
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError:
        return []

    root = tree.getroot()
    annotations = []

    for elem in root.iter():
        if elem.get('data-edit-target') == 'true':
            tag = elem.tag
            if '}' in tag:
                tag = tag.split('}', 1)[1]

            content = ''
            if tag == 'text' and elem.text:
                content = elem.text.strip()[:50]

            annotations.append({
                'element_id': elem.get('id', '(no id)'),
                'tag': tag,
                'annotation': elem.get('data-edit-annotation', ''),
                'content': content,
            })

    return annotations


def scan_directory(dir_path: Path) -> dict[str, list[dict]]:
    """
    Scan all SVG files in svg_output/ subdirectory.

    Returns dict mapping filename -> list of annotation dicts.
    """
    svg_dir = dir_path / 'svg_output'
    if not svg_dir.exists():
        return {}

    results = {}
    for svg_file in sorted(svg_dir.glob('*.svg')):
        annotations = scan_svg_file(svg_file)
        if annotations:
            results[svg_file.name] = annotations

    return results


def print_results(results: dict[str, list[dict]]) -> None:
    """Print annotation results in human-readable format."""
    if not results:
        print("✓ No annotations found.")
        return

    total = sum(len(anns) for anns in results.values())
    print(f"Found {total} annotations in {len(results)} files:\n")

    for filename, annotations in results.items():
        print(f"{filename}")
        for i, ann in enumerate(annotations, 1):
            content = f' "{ann["content"]}"' if ann['content'] else ''
            print(f"  [{i}] <{ann['tag']} id=\"{ann['element_id']}\">{content}")
            print(f"      → {ann['annotation']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Check SVG files for edit annotations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/check_annotations.py projects/my-project
    python3 scripts/check_annotations.py projects/my-project/svg_output/slide_01.svg
        """
    )
    parser.add_argument('path', help='Project directory or single SVG file path')
    args = parser.parse_args()

    target = Path(args.path).resolve()

    if not target.exists():
        print(f"Error: Path not found: {target}", file=sys.stderr)
        sys.exit(1)

    if target.is_file() and target.suffix == '.svg':
        annotations = scan_svg_file(target)
        results = {target.name: annotations} if annotations else {}
    elif target.is_dir():
        results = scan_directory(target)
    else:
        print(f"Error: Expected a project directory or .svg file, got: {target}", file=sys.stderr)
        sys.exit(1)

    print_results(results)


if __name__ == '__main__':
    main()
