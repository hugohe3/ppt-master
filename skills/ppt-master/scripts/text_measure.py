#!/usr/bin/env python3
"""PPT Master - Text Measurement

Measure, wrap, or calculate bounds with the SVG checker's width estimator.

Usage:
    python3 scripts/text_measure.py <measure|wrap|box> [options]
Examples:
    python3 scripts/text_measure.py measure "Editable text" --size 22
Dependencies:
    Standard library and PPT Master sibling modules
"""

from __future__ import annotations

import argparse
import html
import json
import math
import sys
from functools import partial
from pathlib import Path


_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from svg_to_pptx.drawingml.elements import estimate_single_line_text_frame_width  # noqa: E402
from svg_to_pptx.drawingml.utils import is_cjk_char, split_project_text_clusters  # noqa: E402


_CLOSING_PUNCTUATION = frozenset(',.;:!?)]」』】》，。；：！？')
_OPENING_PUNCTUATION = frozenset('([「『【《（')
_WEIGHTS = ('normal', 'bold', '100', '200', '300', '400', '500', '600', '700', '800', '900')


def _bounded_float(value: str, *, minimum: float | None = None, strict: bool = False) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError('must be a finite number')
    if minimum is not None and (number < minimum or strict and number == minimum):
        relation = 'greater than' if strict else 'at least'
        raise argparse.ArgumentTypeError(f'must be {relation} {minimum:g}')
    return number


_positive_float = partial(_bounded_float, minimum=0.0, strict=True)
_nonnegative_float = partial(_bounded_float, minimum=0.0)


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be at least 1')
    return number


def _format_number(value: float) -> str:
    rounded = round(value, 2)
    return '0' if rounded == 0 else f'{rounded:.2f}'.rstrip('0').rstrip('.')


def measure_text(
    text: str, *, size: float, family: str = 'Calibri',
    weight: str = 'normal', letter_spacing: float = 0.0,
) -> float:
    """Measure one line with the checker-owned DrawingML estimator."""
    run = dict(
        text=text, font_size=size, font_family=family,
        font_weight=weight, letter_spacing=letter_spacing,
    )
    return estimate_single_line_text_frame_width([run])


def _protected_units(text: str) -> tuple[list[str], str]:
    cjk_clusters = ' ' not in text and any(is_cjk_char(ch) for ch in text)
    separator = '' if cjk_clusters else ' '
    units = split_project_text_clusters(text) if cjk_clusters else [token for token in text.split(' ') if token]
    protected: list[str] = []
    for unit in units:
        if protected and (unit[0] in _CLOSING_PUNCTUATION or protected[-1][-1] in _OPENING_PUNCTUATION):
            protected[-1] += separator + unit
        else:
            protected.append(unit)
    return protected, separator


def wrap_text(
    text: str, *, size: float, max_width: float, family: str = 'Calibri',
    weight: str = 'normal', letter_spacing: float = 0.0,
) -> tuple[list[str], list[float], list[tuple[str, float]]]:
    """Greedily wrap text and return lines, widths, and oversized units."""
    style = dict(size=size, family=family, weight=weight, letter_spacing=letter_spacing)
    units, separator = _protected_units(text)
    if not units:
        return [''], [0.0], []

    lines: list[str] = []
    widths: list[float] = []
    oversized: list[tuple[str, float]] = []
    current, current_width = '', 0.0
    for unit in units:
        unit_width = measure_text(unit, **style)
        if unit_width > max_width:
            if current:
                lines.append(current)
                widths.append(current_width)
                current = ''
            lines.append(unit)
            widths.append(unit_width)
            oversized.append((unit, unit_width))
            continue
        candidate = unit if not current else current + separator + unit
        candidate_width = measure_text(candidate, **style)
        if current and candidate_width > max_width:
            lines.append(current)
            widths.append(current_width)
            current = unit
            current_width = unit_width
        else:
            current = candidate
            current_width = candidate_width
    if current:
        lines.append(current)
        widths.append(current_width)
    return lines, widths, oversized


def _render_wrapped_svg(lines: list[str], *, x: float, dy: float, y: float | None) -> str:
    escaped = [html.escape(line, quote=False) for line in lines]
    tspan = f'<tspan x="{_format_number(x)}" dy="{_format_number(dy)}">'
    inner = escaped[0] + ''.join(f'{tspan}{line}</tspan>' for line in escaped[1:])
    return inner if y is None else (
        f'<text x="{_format_number(x)}" y="{_format_number(y)}">{inner}</text>'
    )


def text_box(
    *, x: float, baseline_y: float, size: float, lines: int, dy: float,
    width: float, anchor: str,
) -> dict[str, float]:
    """Calculate the module bounds for a positioned text block."""
    left = x - width / 2 if anchor == 'middle' else x - width if anchor == 'end' else x
    top = baseline_y - 0.85 * size
    bottom = baseline_y + (lines - 1) * dy + 0.35 * size
    return dict(x=left, y=top, width=width, height=bottom - top, top=top, bottom=bottom)


def _add_style_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--size', type=_positive_float, required=True)
    parser.add_argument('--family', default='Calibri')
    parser.add_argument('--weight', choices=_WEIGHTS, default='normal')
    parser.add_argument('--letter-spacing', type=_bounded_float, default=0.0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Measure and wrap SVG authoring text.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    measure = subparsers.add_parser('measure', help='Measure single-line text.')
    measure.add_argument('text', metavar='TEXT', nargs='*')
    measure.add_argument('--stdin', action='store_true')

    wrap = subparsers.add_parser('wrap', help='Wrap one paragraph.')
    wrap.add_argument('text', metavar='TEXT', nargs='?')
    wrap.add_argument('--stdin', action='store_true')
    wrap.add_argument('--max-width', type=_positive_float, required=True)
    wrap.add_argument('--x', type=_bounded_float, required=True)
    wrap.add_argument('--dy', type=_positive_float, required=True)
    wrap.add_argument('--y', type=_bounded_float)

    box = subparsers.add_parser('box', help='Calculate text-block bounds.')
    box.add_argument('text', metavar='TEXT', nargs='*')
    box.add_argument('--x', type=_bounded_float, required=True)
    box.add_argument('--y', type=_bounded_float, required=True)
    box.add_argument('--lines', type=_positive_int, required=True)
    box.add_argument('--dy', type=_positive_float)
    box.add_argument('--width', type=_nonnegative_float)
    box.add_argument('--anchor', choices=('start', 'middle', 'end'), default='start')
    for command in (measure, wrap, box):
        command.add_argument('--json', action='store_true')
        _add_style_arguments(command)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    style = dict(size=args.size, family=args.family, weight=args.weight, letter_spacing=args.letter_spacing)

    if args.command == 'measure':
        if args.stdin and args.text:
            parser.error('measure accepts positional TEXT or --stdin, not both')
        if not args.stdin and not args.text:
            parser.error('measure requires positional TEXT or --stdin')
        texts = sys.stdin.read().splitlines() if args.stdin else args.text
        results = [{'text': text, 'width': measure_text(text, **style)} for text in texts]
        if args.json:
            print(json.dumps(results, ensure_ascii=False))
        else:
            sys.stdout.write(''.join(f'{item["width"]:.1f}\t{item["text"]}\n' for item in results))
        return 0

    if args.command == 'wrap':
        if args.stdin and args.text is not None:
            parser.error('wrap accepts positional TEXT or --stdin, not both')
        if not args.stdin and args.text is None:
            parser.error('wrap requires positional TEXT or --stdin')
        text = sys.stdin.read().rstrip('\r\n') if args.stdin else args.text
        lines, widths, oversized = wrap_text(text, max_width=args.max_width, **style)
        for token, width in oversized:
            warning = f'Warning: token exceeds max width ({width:.1f} > {args.max_width:.1f}): {token}'
            print(warning, file=sys.stderr)
        if args.json:
            height = (len(lines) - 1) * args.dy + 1.2 * args.size
            payload = dict(lines=lines, widths=widths, max_width=args.max_width, height=height)
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(_render_wrapped_svg(lines, x=args.x, dy=args.dy, y=args.y))
        return 0

    if args.lines > 1 and args.dy is None:
        parser.error('box requires --dy when --lines is greater than 1')
    if args.width is None and len(args.text) != args.lines:
        parser.error('box without --width requires one positional TEXT per line')
    if args.width is not None and args.text:
        parser.error('box accepts positional TEXT only when --width is omitted')
    width = args.width
    if width is None:
        width = max(measure_text(text, **style) for text in args.text)
    bounds = text_box(
        x=args.x, baseline_y=args.y, size=args.size, lines=args.lines, dy=args.dy or 0.0,
        width=width, anchor=args.anchor,
    )
    rounded = {key: round(value, 2) for key, value in bounds.items()}
    if args.json:
        print(json.dumps(rounded, ensure_ascii=False))
    else:
        values = ' '.join(_format_number(bounds[key]) for key in ('x', 'y', 'width', 'height'))
        top, bottom = _format_number(bounds['top']), _format_number(bounds['bottom'])
        print(f'data-pptx-bounds="{values}"\ttop={top}\tbottom={bottom}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
