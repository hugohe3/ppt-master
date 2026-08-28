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
import unicodedata
from functools import partial
from pathlib import Path


_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from svg_to_pptx.drawingml.elements import estimate_single_line_text_frame_width  # noqa: E402
from svg_to_pptx.drawingml.utils import split_project_text_clusters  # noqa: E402


_CLOSING_PUNCTUATION = frozenset(',.;:!?)]}、，。；：！？）》」』】”’')
_OPENING_PUNCTUATION = frozenset('([{（《「『【“‘')
_PREFERRED_BREAK_PUNCTUATION = frozenset('，。；：')
_LATIN_TOKEN_CONNECTORS = frozenset("'’._:/+%@#-")
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
    include_headroom: bool = True,
) -> float:
    """Measure one line with the checker-owned DrawingML estimator."""
    run = dict(
        text=text, font_size=size, font_family=family,
        font_weight=weight, letter_spacing=letter_spacing,
    )
    return estimate_single_line_text_frame_width(
        [run],
        include_headroom=include_headroom,
    )


def _is_latin_or_number_cluster(cluster: str) -> bool:
    """Return whether a rendered cluster belongs to a Latin/number token."""
    bases = [
        ch
        for ch in cluster
        if unicodedata.category(ch) not in {'Mn', 'Mc', 'Me'}
    ]
    return bool(bases) and all(
        ch.isdigit() or 'LATIN' in unicodedata.name(ch, '')
        for ch in bases
    )


def _lexical_units(text: str) -> list[str]:
    """Split a paragraph while keeping Latin words and numbers atomic."""
    clusters = split_project_text_clusters(' '.join(text.split()))
    units: list[str] = []
    pending_space = False
    index = 0
    while index < len(clusters):
        cluster = clusters[index]
        if cluster.isspace():
            pending_space = bool(units)
            index += 1
            continue

        end = index + 1
        if _is_latin_or_number_cluster(cluster):
            while end < len(clusters):
                next_cluster = clusters[end]
                if _is_latin_or_number_cluster(next_cluster):
                    end += 1
                    continue
                connector = (
                    next_cluster in _LATIN_TOKEN_CONNECTORS
                    or (
                        next_cluster == ','
                        and clusters[end - 1].isdigit()
                    )
                )
                if (
                    connector
                    and end + 1 < len(clusters)
                    and _is_latin_or_number_cluster(clusters[end + 1])
                ):
                    end += 2
                    continue
                break

        prefix = ' ' if pending_space else ''
        units.append(prefix + ''.join(clusters[index:end]))
        pending_space = False
        index = end
    return units


def _protected_units(text: str) -> list[str]:
    units = _lexical_units(text)
    protected: list[str] = []
    for unit in units:
        content = unit.lstrip()
        if protected and (
            content[0] in _CLOSING_PUNCTUATION
            or protected[-1].rstrip()[-1] in _OPENING_PUNCTUATION
        ):
            protected[-1] += unit
        else:
            protected.append(unit)
    return protected


def _joined_units(units: list[str], start: int, end: int) -> str:
    return ''.join(units[start:end]).lstrip()


def _preferred_break_after(text: str) -> bool:
    tail = text.rstrip()
    while (
        tail
        and tail[-1] in _CLOSING_PUNCTUATION
        and tail[-1] not in _PREFERRED_BREAK_PUNCTUATION
    ):
        tail = tail[:-1]
    return bool(tail) and tail[-1] in _PREFERRED_BREAK_PUNCTUATION


def wrap_text(
    text: str, *, size: float, max_width: float, family: str = 'Calibri',
    weight: str = 'normal', letter_spacing: float = 0.0,
    include_headroom: bool = True,
) -> tuple[list[str], list[float], list[tuple[str, float]]]:
    """Greedily wrap text and return lines, widths, and oversized units."""
    style = dict(
        size=size,
        family=family,
        weight=weight,
        letter_spacing=letter_spacing,
        include_headroom=include_headroom,
    )
    units = _protected_units(text)
    if not units:
        return [''], [0.0], []

    lines: list[str] = []
    widths: list[float] = []
    oversized: list[tuple[str, float]] = []
    start = 0
    while start < len(units):
        fit_widths: dict[int, float] = {}
        preferred_end: int | None = None
        end = start
        while end < len(units):
            candidate_end = end + 1
            candidate = _joined_units(units, start, candidate_end)
            candidate_width = measure_text(candidate, **style)
            if candidate_width > max_width:
                break
            fit_widths[candidate_end] = candidate_width
            if _preferred_break_after(candidate):
                preferred_end = candidate_end
            end = candidate_end

        if end == len(units):
            line = _joined_units(units, start, end)
            lines.append(line)
            widths.append(fit_widths[end])
            break

        if end == start:
            unit = units[start].lstrip()
            unit_width = measure_text(unit, **style)
            lines.append(unit)
            widths.append(unit_width)
            oversized.append((unit, unit_width))
            start += 1
            continue

        line_end = preferred_end or end
        lines.append(_joined_units(units, start, line_end))
        widths.append(fit_widths[line_end])
        start = line_end
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
    parser.add_argument(
        '--no-headroom',
        action='store_true',
        help='Use the raw estimator instead of DrawingML wrapping headroom.',
    )


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
    style = dict(
        size=args.size,
        family=args.family,
        weight=args.weight,
        letter_spacing=args.letter_spacing,
        include_headroom=not args.no_headroom,
    )

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
