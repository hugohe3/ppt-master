#!/usr/bin/env python3
"""
PPT Master - Animation Config Tool

Create and validate optional per-object PPTX animation sidecar files.

Usage:
    python3 scripts/animation_config.py scaffold <project_path>
    python3 scripts/animation_config.py validate <project_path>

Examples:
    python3 scripts/animation_config.py scaffold projects/demo --force
    python3 scripts/animation_config.py validate projects/demo

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from svg_to_pptx.animation_config import (  # noqa: E402
    load_animation_config,
    validate_animation_config,
    write_scaffold,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Create or validate PPTX animation sidecar configuration.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    scaffold = subparsers.add_parser(
        'scaffold',
        help='scan svg_output/*.svg and write animations.json scaffold',
    )
    scaffold.add_argument('project_path', help='Project directory')
    scaffold.add_argument('-o', '--output', default=None, help='Output path; default: <project>/animations.json')
    scaffold.add_argument('--force', action='store_true', help='Overwrite an existing output file')

    validate = subparsers.add_parser(
        'validate',
        help='validate animations.json references against svg_output/*.svg',
    )
    validate.add_argument('project_path', help='Project directory')
    validate.add_argument('-c', '--config', default=None, help='Config path; default: <project>/animations.json')

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f'Error: Project path does not exist: {project_path}', file=sys.stderr)
        return 1

    if args.command == 'scaffold':
        try:
            output_path = write_scaffold(
                project_path,
                output_path=args.output,
                force=args.force,
            )
        except FileExistsError as exc:
            print(f'Error: {exc}', file=sys.stderr)
            print('Use --force to overwrite.', file=sys.stderr)
            return 1
        print(f'Animation config scaffold written: {output_path}')
        return 0

    if args.command == 'validate':
        try:
            config = load_animation_config(project_path, args.config)
        except Exception as exc:
            print(f'Error: {exc}', file=sys.stderr)
            return 1
        if not config:
            print('No animations.json found; default animation policy will be used.')
            return 0
        warnings = validate_animation_config(project_path, config)
        if warnings:
            for warning in warnings:
                print(f'Warning: {warning}', file=sys.stderr)
            return 1
        print('Animation config validated successfully.')
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
