#!/usr/bin/env python3
"""
PPT Master - Animation Config Tool

Create and validate optional per-object PPTX animation sidecar files.

Usage:
    python3 scripts/animation_config.py scaffold <project_path>
    python3 scripts/animation_config.py list-groups <project_path>
    python3 scripts/animation_config.py validate <project_path>

Examples:
    python3 scripts/animation_config.py scaffold projects/demo --force
    python3 scripts/animation_config.py list-groups projects/demo
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

from console_encoding import configure_utf8_stdio  # noqa: E402
from svg_to_pptx.animation_config import (  # noqa: E402
    build_group_listing,
    load_animation_config,
    validate_animation_config,
    validate_animation_config_errors,
    validate_transition_config,
    write_scaffold,
)

configure_utf8_stdio()


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

    list_groups = subparsers.add_parser(
        'list-groups',
        help='print one compact line per slide listing animatable group ids '
             '(chrome groups excluded); use during planning to avoid reading '
             'the full scaffold file',
    )
    list_groups.add_argument('project_path', help='Project directory')

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

    if args.command == 'list-groups':
        lines, anonymous = build_group_listing(project_path)
        for line in lines:
            print(line)
        for warning in anonymous:
            print(f'Warning: {warning}', file=sys.stderr)
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
        errors = list(dict.fromkeys(
            validate_transition_config(config)
            + validate_animation_config_errors(config)
        ))
        if errors:
            for error in errors:
                print(f'Error: {error}', file=sys.stderr)
            return 1
        reference_messages = validate_animation_config(project_path, config)
        reference_warnings = [
            message for message in reference_messages
            if ' has no id and cannot be customized in animations.json' in message
        ]
        reference_errors = [
            message for message in reference_messages
            if message not in reference_warnings
        ]
        for warning in reference_warnings:
            print(f'Warning: {warning}', file=sys.stderr)
        if reference_errors:
            for error in reference_errors:
                print(f'Error: {error}', file=sys.stderr)
            return 1
        print('Animation config validated successfully.')
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
