#!/usr/bin/env python3
"""PPT Master - Text Measurement

Measure, wrap, calibrate, or calculate bounds with the SVG checker's width estimator.

Usage:
    python3 scripts/text_measure.py <measure|wrap|box|calibrate> [options]
Examples:
    python3 scripts/text_measure.py measure "Editable text" --size 22
    python3 scripts/text_measure.py calibrate projects/example --outline
Dependencies:
    Standard library and PPT Master sibling modules
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import unicodedata
from datetime import datetime, timezone
from functools import partial
from pathlib import Path


_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from project_specs import parse_markdown_artifact, parse_spec_lock  # noqa: E402
from svg_to_pptx.drawingml.elements import estimate_single_line_text_frame_width  # noqa: E402
from svg_to_pptx.drawingml.utils import split_project_text_clusters  # noqa: E402


_CLOSING_PUNCTUATION = frozenset(',.;:!?)]}、，。；：！？）》」』】”’')
_OPENING_PUNCTUATION = frozenset('([{（《「『【“‘')
_PREFERRED_BREAK_PUNCTUATION = frozenset('，。；：')
_LATIN_TOKEN_CONNECTORS = frozenset("'’._:/+%@#-")
_WEIGHTS = ('normal', 'bold', '100', '200', '300', '400', '500', '600', '700', '800', '900')
_CALIBRATION_CJK_SAMPLE = '天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往'
_CALIBRATION_LATIN_SAMPLE = 'Clear Slides Make Big Ideas Easy to See.'
_CORE_CALIBRATION_ROLES = ('body', 'title', 'subtitle', 'annotation')
_SLIDE_HEADING_RE = re.compile(
    r'^#{3,6}[ \t]+Slide[ \t]+([0-9]+|NN)\b.*$',
    flags=re.IGNORECASE | re.MULTILINE,
)
_OUTLINE_FIELD_RE = re.compile(
    r'^(?P<indent>[ \t]*)-[ \t]+(?:\*\*)?'
    r'(?P<label>Title|Core message|Content)(?:\*\*)?[ \t]*:[ \t]*(?P<value>.*)$',
    flags=re.IGNORECASE,
)
_OUTLINE_DATA_LINE_RE = re.compile(
    r'^(?P<indent>[ \t]*)-[ \t]+(?:\*\*)?[^:\n*]+?(?:\*\*)?[ \t]*:',
)


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


def _role_argument(value: str) -> tuple[str, str, float]:
    try:
        name_and_family, raw_size = value.rsplit(':', 1)
        name, family = name_and_family.split(':', 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('expected NAME:FAMILY:SIZE') from exc
    name, family = name.strip().casefold(), family.strip()
    if not name or not family:
        raise argparse.ArgumentTypeError('expected non-empty NAME and FAMILY')
    try:
        size = _positive_float(raw_size)
    except (argparse.ArgumentTypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError('SIZE must be a positive finite number') from exc
    return name, family, size


def _ordered_roles(roles: dict[str, tuple[str, float]]) -> list[tuple[str, str, float]]:
    names = [name for name in _CORE_CALIBRATION_ROLES if name in roles]
    names.extend(sorted(set(roles) - set(names)))
    return [(name, *roles[name]) for name in names]


def _roles_from_spec_lock(lock_path: Path) -> dict[str, tuple[str, float]]:
    lock = parse_spec_lock(lock_path, report_duplicate_fields=True)
    typography = next(
        (
            fields
            for heading, fields in lock.items()
            if heading.strip().casefold() == 'typography'
        ),
        {},
    )
    rows = {
        str(key).strip().casefold(): str(value).strip()
        for key, value in typography.items()
    }
    roles: dict[str, tuple[str, float]] = {}
    for role, raw_size in rows.items():
        if role == 'font_family' or role.endswith('_family'):
            continue
        try:
            size = _positive_float(raw_size)
        except (argparse.ArgumentTypeError, ValueError) as exc:
            raise ValueError(
                f'spec_lock.md typography role {role!r} has invalid size {raw_size!r}'
            ) from exc
        family = rows.get(f'{role}_family', '')
        if not family:
            fallback = 'title_family' if 'title' in role else 'body_family'
            family = rows.get(fallback, '') or rows.get('font_family', '')
        if not family:
            raise ValueError(
                f'spec_lock.md typography role {role!r} has no resolvable font family'
            )
        roles[role] = (family, size)
    return roles


def _clean_planned_line(raw: str) -> str:
    text = re.sub(r'^(?:[-*+]|\d+[.)])[ \t]+', '', raw.strip())
    if not text or re.fullmatch(r'[|:\- \t]+', text):
        return ''
    text = re.sub(r'!\[([^]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', text)
    text = text.replace('**', '').replace('__', '').replace('`', '')
    return ' '.join(text.split())


def _slide_id(token: str) -> str:
    return 'PNN' if token.upper() == 'NN' else f'P{int(token):02d}'


def _outline_candidates(
    design_path: Path,
    role_names: set[str],
) -> dict[str, list[tuple[str, str]]]:
    candidates = {name: [] for name in role_names}
    if not design_path.is_file():
        return candidates
    sections = parse_markdown_artifact(design_path)
    outline = next(
        (
            str(section.get('body', ''))
            for section in sections
            if re.match(
                r'^IX\.[ \t]+Content Outline\b',
                str(section.get('heading', '')),
                flags=re.IGNORECASE,
            )
        ),
        '',
    )
    slide_matches = list(_SLIDE_HEADING_RE.finditer(outline))
    for slide_index, slide_match in enumerate(slide_matches):
        block_end = (
            slide_matches[slide_index + 1].start()
            if slide_index + 1 < len(slide_matches)
            else len(outline)
        )
        slide = _slide_id(slide_match.group(1))
        lines = outline[slide_match.end():block_end].splitlines()
        field_matches = [match for line in lines if (match := _OUTLINE_FIELD_RE.match(line))]
        if not field_matches:
            continue
        base_indent = min(len(match.group('indent').expandtabs()) for match in field_matches)
        line_index = 0
        while line_index < len(lines):
            field_match = _OUTLINE_FIELD_RE.match(lines[line_index])
            if (
                field_match is None
                or len(field_match.group('indent').expandtabs()) != base_indent
            ):
                line_index += 1
                continue
            label = field_match.group('label').casefold()
            value = _clean_planned_line(field_match.group('value'))
            if label == 'title':
                if value and 'title' in candidates:
                    candidates['title'].append((slide, value))
                line_index += 1
                continue
            if label == 'core message':
                role = 'subtitle' if 'subtitle' in candidates else 'body'
                if value and role in candidates:
                    candidates[role].append((slide, value))
                line_index += 1
                continue

            content_lines = [value] if value else []
            next_index = line_index + 1
            while next_index < len(lines):
                next_field = _OUTLINE_DATA_LINE_RE.match(lines[next_index])
                if (
                    next_field is not None
                    and len(next_field.group('indent').expandtabs()) <= base_indent
                ):
                    break
                planned_line = _clean_planned_line(lines[next_index])
                if planned_line:
                    content_lines.append(planned_line)
                next_index += 1
            if 'body' in candidates:
                candidates['body'].extend((slide, text) for text in content_lines)
            line_index = next_index
    return candidates


def _truncate_planned_line(text: str, limit: int = 40) -> str:
    clusters = split_project_text_clusters(text)
    return text if len(clusters) <= limit else ''.join(clusters[:limit - 1]) + '…'


def _longest_planned_lines(
    project_path: Path,
    roles: list[tuple[str, str, float]],
) -> dict[str, dict[str, object] | None]:
    candidates = _outline_candidates(
        project_path / 'design_spec.md',
        {name for name, _family, _size in roles},
    )
    longest: dict[str, dict[str, object] | None] = {}
    for name, family, size in roles:
        best: tuple[float, str, str] | None = None
        for slide, planned_line in candidates[name]:
            width = measure_text(planned_line, size=size, family=family)
            if best is None or width > best[0]:
                best = (width, slide, planned_line)
        longest[name] = None if best is None else {
            'px': round(best[0], 1),
            'slide': best[1],
            'text': _truncate_planned_line(best[2]),
        }
    return longest


def _calibration_payload(
    roles: list[tuple[str, str, float]],
    *,
    project_path: Path,
    source: str,
    include_outline: bool,
) -> dict[str, object]:
    longest = (
        _longest_planned_lines(project_path, roles)
        if include_outline
        else {name: None for name, _family, _size in roles}
    )
    cjk_length = len(split_project_text_clusters(_CALIBRATION_CJK_SAMPLE))
    latin_length = len(split_project_text_clusters(_CALIBRATION_LATIN_SAMPLE))
    role_rows = {}
    for name, family, size in roles:
        cjk_width = measure_text(_CALIBRATION_CJK_SAMPLE, size=size, family=family)
        latin_width = measure_text(_CALIBRATION_LATIN_SAMPLE, size=size, family=family)
        role_rows[name] = {
            'family': family,
            'size': size,
            'cjk_chars_per_100px': round(100.0 * cjk_length / cjk_width, 1),
            'latin_chars_per_100px': round(100.0 * latin_length / latin_width, 1),
            'longest_planned_line': longest[name],
        }
    return {
        'roles': role_rows,
        'source': source,
        'generated_at': datetime.now(timezone.utc)
        .isoformat(timespec='seconds')
        .replace('+00:00', 'Z'),
    }


def _render_calibration_table(payload: dict[str, object], *, include_outline: bool) -> str:
    role_rows = payload['roles']
    assert isinstance(role_rows, dict)
    headers = ['role', 'family', 'size', 'CJK ≈chars/100px', 'Latin ≈chars/100px']
    if include_outline:
        headers.append('longest planned line (px, slide, text)')
    lines = [
        f'[CALIBRATION] roles: {len(role_rows)} | source: {payload["source"]}',
        ' | '.join(headers),
        ' | '.join('---' for _header in headers),
    ]
    for name, raw_row in role_rows.items():
        assert isinstance(raw_row, dict)
        row = [
            name,
            str(raw_row['family']),
            _format_number(float(raw_row['size'])),
            f'{raw_row["cjk_chars_per_100px"]:.1f}',
            f'{raw_row["latin_chars_per_100px"]:.1f}',
        ]
        if include_outline:
            planned = raw_row['longest_planned_line']
            row.append(
                '-'
                if planned is None
                else f'{planned["px"]:.1f}px, {planned["slide"]}, {planned["text"]}'
            )
        lines.append(' | '.join(row))
    return '\n'.join(lines) + '\n'


def _run_calibrate(args: argparse.Namespace) -> int:
    project_path = args.project_path.resolve()
    if not project_path.is_dir():
        print(
            f'Calibration failed: project path is not a directory: {project_path}',
            file=sys.stderr,
        )
        return 2
    lock_path = project_path / 'spec_lock.md'
    if not lock_path.is_file() and not args.role:
        print(
            'Calibration requires spec_lock.md or at least one --role NAME:FAMILY:SIZE entry.',
            file=sys.stderr,
        )
        return 2
    try:
        roles = _roles_from_spec_lock(lock_path) if lock_path.is_file() else {}
        for name, family, size in args.role:
            roles[name] = (family, size)
        ordered_roles = _ordered_roles(roles)
        if not ordered_roles:
            raise ValueError('no typography size roles were found')
        source = 'spec_lock.md' if lock_path.is_file() else '--role'
        payload = _calibration_payload(
            ordered_roles,
            project_path=project_path,
            source=source,
            include_outline=args.outline,
        )
        output_path = project_path / 'validation' / 'text_calibration.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rendered_json = json.dumps(payload, ensure_ascii=False, indent=2)
        output_path.write_text(rendered_json + '\n', encoding='utf-8')
    except (OSError, ValueError) as exc:
        message = ' '.join(str(exc).splitlines())
        print(f'Calibration failed: {message}', file=sys.stderr)
        return 2
    if args.json:
        print(rendered_json)
    else:
        sys.stdout.write(_render_calibration_table(payload, include_outline=args.outline))
    return 0


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
    parser = argparse.ArgumentParser(
        description='Measure, wrap, and calibrate SVG authoring text.'
    )
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

    calibrate = subparsers.add_parser('calibrate', help='Calibrate project typography roles.')
    calibrate.add_argument('project_path', type=Path)
    calibrate.add_argument('--outline', action='store_true')
    calibrate.add_argument('--role', action='append', type=_role_argument, default=[])
    calibrate.add_argument('--json', action='store_true')
    for command in (measure, wrap, box):
        command.add_argument('--json', action='store_true')
        _add_style_arguments(command)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == 'calibrate':
        return _run_calibrate(args)
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
