"""SVG path parsing, normalization, and DrawingML path command generation.

See references/svg-effects.md §6.9 for the project freeform grammar.
"""

from __future__ import annotations

import math
import re
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from .utils import (
    SVG_NS,
    parse_inline_style,
    parse_project_geometry_length,
    project_definition_index,
    px_to_emu,
    resolve_url_id,
)


@dataclass
class PathCommand:
    """A single SVG path command with its arguments."""
    cmd: str  # M, L, C, Z, etc. (uppercase = absolute)
    args: list[float] = field(default_factory=list)


# Argument counts per SVG path command
_ARG_COUNTS = {
    'M': 2, 'm': 2, 'L': 2, 'l': 2,
    'H': 1, 'h': 1, 'V': 1, 'v': 1,
    'C': 6, 'c': 6, 'S': 4, 's': 4,
    'Q': 4, 'q': 4, 'T': 2, 't': 2,
    'A': 7, 'a': 7, 'Z': 0, 'z': 0,
}

_PATH_COMMAND_CHARS = 'MmLlHhVvCcSsQqTtAaZz'
_PATH_NUMBER_PATTERN = (
    r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
)
_PATH_TOKEN_RE = re.compile(
    rf'(?P<command>[{_PATH_COMMAND_CHARS}])|(?P<number>{_PATH_NUMBER_PATTERN})'
)
_POINT_TOKEN_RE = re.compile(_PATH_NUMBER_PATTERN)
_TOKEN_SEPARATOR_RE = re.compile(r'[ \t\r\n]*(?:,[ \t\r\n]*)?')
_TRAILING_WHITESPACE_RE = re.compile(r'[ \t\r\n]*')
_CANONICAL_FREEFORM_NUMBER_RE = re.compile(
    r'-?(?:\d+(?:\.\d+)?|\.\d+)$'
)


@dataclass(frozen=True)
class _GeometryToken:
    kind: str
    raw: str
    offset: int


def _tokenize_path_data(d: str) -> list[_GeometryToken]:
    """Tokenize one complete path-data value without skipping input."""
    if not d or not d.strip():
        raise ValueError('path d must not be empty')

    tokens: list[_GeometryToken] = []
    cursor = 0
    previous_kind: str | None = None
    for match in _PATH_TOKEN_RE.finditer(d):
        kind = 'command' if match.lastgroup == 'command' else 'number'
        gap = d[cursor:match.start()]
        if _TOKEN_SEPARATOR_RE.fullmatch(gap) is None:
            raise ValueError(
                f'path d contains unsupported syntax at offset {cursor}: {gap!r}'
            )
        if ',' in gap and (
            previous_kind is None
            or previous_kind == 'command'
            or kind == 'command'
        ):
            raise ValueError(
                f'path d has a misplaced comma at offset {cursor}'
            )
        tokens.append(_GeometryToken(kind, match.group(), match.start()))
        previous_kind = kind
        cursor = match.end()

    trailing = d[cursor:]
    if _TRAILING_WHITESPACE_RE.fullmatch(trailing) is None:
        raise ValueError(
            f'path d contains unsupported trailing syntax at offset '
            f'{cursor}: {trailing!r}'
        )
    if not tokens:
        raise ValueError('path d must contain a supported command')
    return tokens


def _finite_token_value(token: _GeometryToken, context: str) -> float:
    value = float(token.raw)
    if not math.isfinite(value):
        raise ValueError(
            f'{context} contains a non-finite number {token.raw!r} at '
            f'offset {token.offset}'
        )
    return value


def _expand_arc_argument_tokens(
    argument_tokens: list[_GeometryToken],
    command_token: _GeometryToken,
) -> list[_GeometryToken]:
    """Split compact SVG arc flags without weakening the numeric grammar."""
    pending = deque(argument_tokens)
    expanded: list[_GeometryToken] = []
    argument_index = 0
    while pending:
        token = pending.popleft()
        position = argument_index % _ARG_COUNTS[command_token.raw]
        if position in {3, 4}:
            if not token.raw or token.raw[0] not in {'0', '1'}:
                raise ValueError(
                    f'path arc flag at offset {token.offset} must be exactly '
                    f'0 or 1; got {token.raw!r}'
                )
            expanded.append(
                _GeometryToken('number', token.raw[0], token.offset)
            )
            remainder = token.raw[1:]
            if remainder:
                next_position = (position + 1) % _ARG_COUNTS[command_token.raw]
                if (
                    next_position in {3, 4}
                    and remainder[0] not in {'0', '1'}
                ) or (
                    next_position not in {3, 4}
                    and re.fullmatch(_PATH_NUMBER_PATTERN, remainder) is None
                ):
                    raise ValueError(
                        f'path arc flag at offset {token.offset} must be '
                        f'exactly 0 or 1; got {token.raw!r}'
                    )
                pending.appendleft(
                    _GeometryToken('number', remainder, token.offset + 1)
                )
        else:
            expanded.append(token)
        argument_index += 1

    return expanded


def _tokenize_points(points: str) -> list[_GeometryToken]:
    """Tokenize one complete polygon/polyline points value."""
    if not points or not points.strip():
        raise ValueError('points must not be empty')

    tokens: list[_GeometryToken] = []
    cursor = 0
    for match in _POINT_TOKEN_RE.finditer(points):
        gap = points[cursor:match.start()]
        if _TOKEN_SEPARATOR_RE.fullmatch(gap) is None:
            raise ValueError(
                f'points contains unsupported syntax at offset {cursor}: {gap!r}'
            )
        if not tokens and ',' in gap:
            raise ValueError('points cannot start with a comma')
        tokens.append(_GeometryToken('number', match.group(), match.start()))
        cursor = match.end()

    trailing = points[cursor:]
    if _TRAILING_WHITESPACE_RE.fullmatch(trailing) is None:
        raise ValueError(
            f'points contains unsupported trailing syntax at offset '
            f'{cursor}: {trailing!r}'
        )
    if not tokens:
        raise ValueError('points must contain coordinate pairs')
    return tokens


def _parse_svg_path_tokens(
    d: str,
) -> tuple[list[PathCommand], list[_GeometryToken]]:
    """Parse path data and retain its semantic numeric tokens."""
    tokens = _tokenize_path_data(d)
    if tokens[0].kind != 'command' or tokens[0].raw not in {'M', 'm'}:
        raise ValueError('path d must begin with M or m')

    commands: list[PathCommand] = []
    number_tokens: list[_GeometryToken] = []
    token_index = 0
    while token_index < len(tokens):
        command_token = tokens[token_index]
        if command_token.kind != 'command':
            raise ValueError(
                f'path d requires a command at offset {command_token.offset}'
            )
        command = command_token.raw
        token_index += 1
        if command in {'Z', 'z'}:
            commands.append(PathCommand(command, []))
            continue

        argument_tokens: list[_GeometryToken] = []
        while token_index < len(tokens) and tokens[token_index].kind == 'number':
            argument_tokens.append(tokens[token_index])
            token_index += 1

        argument_count = _ARG_COUNTS[command]
        if command in {'A', 'a'}:
            argument_tokens = _expand_arc_argument_tokens(
                argument_tokens,
                command_token,
            )
        if not argument_tokens:
            raise ValueError(
                f'path command {command!r} at offset {command_token.offset} '
                f'requires {argument_count} argument(s)'
            )
        if len(argument_tokens) % argument_count:
            raise ValueError(
                f'path command {command!r} at offset {command_token.offset} '
                f'has {len(argument_tokens)} argument(s); expected a multiple '
                f'of {argument_count}'
            )

        for group_index in range(0, len(argument_tokens), argument_count):
            group = argument_tokens[group_index:group_index + argument_count]
            values = [_finite_token_value(token, 'path d') for token in group]
            if command in {'A', 'a'}:
                if values[0] < 0 or values[1] < 0:
                    raise ValueError('path arc radii must be non-negative')

            emitted_command = command
            if command == 'M' and group_index > 0:
                emitted_command = 'L'
            elif command == 'm' and group_index > 0:
                emitted_command = 'l'
            commands.append(PathCommand(emitted_command, values))
            number_tokens.extend(group)
    return commands, number_tokens


def parse_svg_path(d: str) -> list[PathCommand]:
    """Parse one complete supported SVG path value or fail closed."""
    commands, _ = _parse_svg_path_tokens(d)
    return commands


def parse_svg_points(
    points: str,
    *,
    min_points: int = 2,
) -> list[tuple[float, float]]:
    """Parse complete polygon/polyline points into finite coordinate pairs."""
    tokens = _tokenize_points(points)
    if len(tokens) % 2:
        raise ValueError(
            f'points has {len(tokens)} numeric value(s); expected coordinate pairs'
        )
    point_count = len(tokens) // 2
    if point_count < min_points:
        raise ValueError(
            f'points requires at least {min_points} coordinate pair(s); '
            f'found {point_count}'
        )
    values = [_finite_token_value(token, 'points') for token in tokens]
    return [
        (values[index], values[index + 1])
        for index in range(0, len(values), 2)
    ]


def noncanonical_path_numbers(d: str) -> tuple[str, ...]:
    """Return compatible path numbers that generated SVG should normalize."""
    _, number_tokens = _parse_svg_path_tokens(d)
    return tuple(
        token.raw
        for token in number_tokens
        if _CANONICAL_FREEFORM_NUMBER_RE.fullmatch(token.raw) is None
    )


def noncanonical_points_numbers(points: str, *, min_points: int) -> tuple[str, ...]:
    """Return compatible point numbers that generated SVG should normalize."""
    parse_svg_points(points, min_points=min_points)
    return tuple(
        token.raw
        for token in _tokenize_points(points)
        if _CANONICAL_FREEFORM_NUMBER_RE.fullmatch(token.raw) is None
    )


def iter_project_freeform_geometry(
    root: ET.Element,
) -> Iterator[tuple[ET.Element, str, str | None, int | None]]:
    """Yield path/points values and their minimum point-count contract."""
    for elem in root.iter():
        raw_tag = str(elem.tag)
        if raw_tag.startswith('{'):
            namespace, tag = raw_tag[1:].split('}', 1)
            if namespace != SVG_NS:
                continue
        else:
            tag = raw_tag
        if tag == 'path':
            yield elem, 'd', elem.get('d'), None
        elif tag == 'polygon':
            yield elem, 'points', elem.get('points'), 3
        elif tag == 'polyline':
            yield elem, 'points', elem.get('points'), 2


def project_freeform_geometry_errors(root: ET.Element) -> list[str]:
    """Return blocking path/points grammar errors for converter preflight."""
    errors: list[str] = []
    for elem, attribute, raw, min_points in iter_project_freeform_geometry(root):
        tag = elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)
        elem_id = elem.get('id')
        label = f'<{tag} id={elem_id!r}>' if elem_id else f'<{tag}>'
        try:
            if raw is None:
                raise ValueError(f'<{tag}> requires {attribute}')
            if attribute == 'd':
                parse_svg_path(raw)
            else:
                parse_svg_points(raw, min_points=min_points or 2)
        except ValueError as exc:
            errors.append(f'{label} {attribute}: {exc}')
    return errors


def _project_path_like_bounds(
    elem: ET.Element,
) -> tuple[float, float, float, float] | None:
    """Return intrinsic bounds for line-like SVG geometry."""
    tag = elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)
    points: list[tuple[float, float]] = []

    if tag == 'line':
        points = [
            (
                parse_project_geometry_length(elem.get('x1', '0'), 'x1'),
                parse_project_geometry_length(elem.get('y1', '0'), 'y1'),
            ),
            (
                parse_project_geometry_length(elem.get('x2', '0'), 'x2'),
                parse_project_geometry_length(elem.get('y2', '0'), 'y2'),
            ),
        ]
    elif tag in {'polygon', 'polyline'}:
        min_points = 3 if tag == 'polygon' else 2
        points = parse_svg_points(elem.get('points', ''), min_points=min_points)
    elif tag == 'path':
        commands = normalize_path_commands(
            svg_path_to_absolute(parse_svg_path(elem.get('d', '')))
        )
        current_point: tuple[float, float] | None = None
        subpath_start: tuple[float, float] | None = None
        for command in commands:
            if command.cmd == 'M':
                current_point = (command.args[0], command.args[1])
                subpath_start = current_point
            elif command.cmd == 'L':
                end_point = (command.args[0], command.args[1])
                if current_point is not None:
                    points.extend((current_point, end_point))
                current_point = end_point
            elif command.cmd == 'C':
                if current_point is not None:
                    points.append(current_point)
                points.extend(
                    (command.args[index], command.args[index + 1])
                    for index in range(0, 6, 2)
                )
                current_point = (command.args[4], command.args[5])
            elif command.cmd == 'Z' and current_point is not None:
                if subpath_start is not None:
                    points.extend((current_point, subpath_start))
                    current_point = subpath_start

    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def project_gradient_geometry_errors(root: ET.Element) -> list[str]:
    """Reject object-bounding-box gradient strokes on degenerate geometry."""
    definitions, _duplicates = project_definition_index(root)
    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    errors: set[str] = set()

    for elem in root.iter():
        tag = elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)
        if tag not in {'line', 'path', 'polygon', 'polyline'}:
            continue

        current: ET.Element | None = elem
        stroke: str | None = None
        while current is not None:
            style_values = parse_inline_style(current.get('style'))
            if 'stroke' in style_values:
                stroke = style_values['stroke']
                break
            if current.get('stroke') is not None:
                stroke = current.get('stroke')
                break
            current = parent_by_id.get(id(current))

        gradient_id = resolve_url_id(stroke)
        gradient = definitions.get(gradient_id) if gradient_id else None
        if gradient is None:
            continue
        gradient_tag = (
            gradient.tag.rsplit('}', 1)[-1]
            if '}' in str(gradient.tag)
            else str(gradient.tag)
        )
        if gradient_tag not in {'linearGradient', 'radialGradient'}:
            continue
        if gradient.get('gradientUnits') not in {None, 'objectBoundingBox'}:
            continue

        try:
            bounds = _project_path_like_bounds(elem)
        except ValueError:
            # The existing geometry preflight owns malformed geometry errors.
            continue
        if bounds is None:
            continue
        min_x, min_y, max_x, max_y = bounds
        zero_width = math.isclose(
            min_x, max_x, rel_tol=0.0, abs_tol=1e-9
        )
        zero_height = math.isclose(
            min_y, max_y, rel_tol=0.0, abs_tol=1e-9
        )
        if not zero_width and not zero_height:
            continue

        dimension = 'width and height' if zero_width and zero_height else (
            'width' if zero_width else 'height'
        )
        elem_id = elem.get('id')
        label = f'<{tag} id={elem_id!r}>' if elem_id else f'<{tag}>'
        errors.add(
            f'{label} stroke=url(#{gradient_id}) has zero intrinsic {dimension}; '
            'objectBoundingBox gradients do not include stroke width and will '
            'not render. Use a non-degenerate path or a closed filled shape'
        )

    return sorted(errors)


def svg_path_to_absolute(commands: list[PathCommand]) -> list[PathCommand]:
    """Convert all relative path commands to absolute."""
    result: list[PathCommand] = []
    cx, cy = 0.0, 0.0  # current point
    sx, sy = 0.0, 0.0  # subpath start

    for cmd in commands:
        a = cmd.args
        if cmd.cmd == 'M':
            cx, cy = a[0], a[1]
            sx, sy = cx, cy
            result.append(PathCommand('M', [cx, cy]))
        elif cmd.cmd == 'm':
            cx += a[0]; cy += a[1]
            sx, sy = cx, cy
            result.append(PathCommand('M', [cx, cy]))
        elif cmd.cmd == 'L':
            cx, cy = a[0], a[1]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'l':
            cx += a[0]; cy += a[1]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'H':
            cx = a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'h':
            cx += a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'V':
            cy = a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'v':
            cy += a[0]
            result.append(PathCommand('L', [cx, cy]))
        elif cmd.cmd == 'C':
            result.append(PathCommand('C', list(a)))
            cx, cy = a[4], a[5]
        elif cmd.cmd == 'c':
            abs_args = [
                cx + a[0], cy + a[1],
                cx + a[2], cy + a[3],
                cx + a[4], cy + a[5],
            ]
            result.append(PathCommand('C', abs_args))
            cx, cy = abs_args[4], abs_args[5]
        elif cmd.cmd == 'S':
            result.append(PathCommand('S', list(a)))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 's':
            abs_args = [cx + a[0], cy + a[1], cx + a[2], cy + a[3]]
            result.append(PathCommand('S', abs_args))
            cx, cy = abs_args[2], abs_args[3]
        elif cmd.cmd == 'Q':
            result.append(PathCommand('Q', list(a)))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 'q':
            abs_args = [cx + a[0], cy + a[1], cx + a[2], cy + a[3]]
            result.append(PathCommand('Q', abs_args))
            cx, cy = abs_args[2], abs_args[3]
        elif cmd.cmd == 'T':
            result.append(PathCommand('T', list(a)))
            cx, cy = a[0], a[1]
        elif cmd.cmd == 't':
            abs_args = [cx + a[0], cy + a[1]]
            result.append(PathCommand('T', abs_args))
            cx, cy = abs_args[0], abs_args[1]
        elif cmd.cmd == 'A':
            result.append(PathCommand('A', list(a)))
            cx, cy = a[5], a[6]
        elif cmd.cmd == 'a':
            abs_args = [a[0], a[1], a[2], a[3], a[4], cx + a[5], cy + a[6]]
            result.append(PathCommand('A', abs_args))
            cx, cy = abs_args[5], abs_args[6]
        elif cmd.cmd in ('Z', 'z'):
            result.append(PathCommand('Z', []))
            cx, cy = sx, sy

    return result


def _reflect_control_point(
    cp_x: float, cp_y: float,
    cx: float, cy: float,
) -> tuple[float, float]:
    """Reflect a control point through the current point."""
    return 2 * cx - cp_x, 2 * cy - cp_y


def _quad_to_cubic(
    qp_x: float, qp_y: float,
    p0_x: float, p0_y: float,
    p3_x: float, p3_y: float,
) -> list[float]:
    """Convert quadratic bezier control point to cubic bezier control points."""
    cp1_x = p0_x + 2.0 / 3.0 * (qp_x - p0_x)
    cp1_y = p0_y + 2.0 / 3.0 * (qp_y - p0_y)
    cp2_x = p3_x + 2.0 / 3.0 * (qp_x - p3_x)
    cp2_y = p3_y + 2.0 / 3.0 * (qp_y - p3_y)
    return [cp1_x, cp1_y, cp2_x, cp2_y, p3_x, p3_y]


def _arc_to_cubic_beziers(
    cx_: float, cy_: float,
    rx: float, ry: float,
    phi: float,
    large_arc: int, sweep: int,
    x2: float, y2: float,
) -> list[PathCommand]:
    """Convert SVG arc (endpoint parameterization) to cubic bezier curves.

    Uses the algorithm from the SVG spec (F.6.5) to convert endpoint to center
    parameterization, then approximates each arc segment with cubic beziers.
    """
    x1, y1 = cx_, cy_

    if abs(x1 - x2) < 1e-10 and abs(y1 - y2) < 1e-10:
        return []

    rx = abs(rx)
    ry = abs(ry)
    if rx < 1e-10 or ry < 1e-10:
        return [PathCommand('L', [x2, y2])]

    phi_rad = math.radians(phi)
    cos_phi = math.cos(phi_rad)
    sin_phi = math.sin(phi_rad)

    # Step 1: Compute (x1', y1')
    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    # Step 2: Compute (cx', cy')
    x1p2 = x1p * x1p
    y1p2 = y1p * y1p
    rx2 = rx * rx
    ry2 = ry * ry

    # Ensure radii are large enough
    lam = x1p2 / rx2 + y1p2 / ry2
    if lam > 1:
        lam_sqrt = math.sqrt(lam)
        rx *= lam_sqrt
        ry *= lam_sqrt
        rx2 = rx * rx
        ry2 = ry * ry

    num = max(rx2 * ry2 - rx2 * y1p2 - ry2 * x1p2, 0)
    den = rx2 * y1p2 + ry2 * x1p2
    sq = math.sqrt(num / den) if den > 1e-10 else 0.0

    if large_arc == sweep:
        sq = -sq

    cxp = sq * rx * y1p / ry
    cyp = -sq * ry * x1p / rx

    # Step 3: Compute (cx, cy)
    arc_cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    arc_cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    # Step 4: Compute theta1 and dtheta
    def angle_between(ux: float, uy: float, vx: float, vy: float) -> float:
        n = math.sqrt((ux * ux + uy * uy) * (vx * vx + vy * vy))
        if n < 1e-10:
            return 0
        c = max(-1, min(1, (ux * vx + uy * vy) / n))
        a = math.acos(c)
        if ux * vy - uy * vx < 0:
            a = -a
        return a

    theta1 = angle_between(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dtheta = angle_between(
        (x1p - cxp) / rx, (y1p - cyp) / ry,
        (-x1p - cxp) / rx, (-y1p - cyp) / ry,
    )

    if sweep == 0 and dtheta > 0:
        dtheta -= 2 * math.pi
    elif sweep == 1 and dtheta < 0:
        dtheta += 2 * math.pi

    # Split arc into segments of at most 90 degrees
    n_segs = max(1, int(math.ceil(abs(dtheta) / (math.pi / 2))))
    d_per_seg = dtheta / n_segs

    result: list[PathCommand] = []
    alpha = 4.0 / 3.0 * math.tan(d_per_seg / 4.0)

    for i in range(n_segs):
        t1 = theta1 + i * d_per_seg
        t2 = theta1 + (i + 1) * d_per_seg

        cos_t1 = math.cos(t1)
        sin_t1 = math.sin(t1)
        cos_t2 = math.cos(t2)
        sin_t2 = math.sin(t2)

        ep1_x = cos_t1 - alpha * sin_t1
        ep1_y = sin_t1 + alpha * cos_t1
        ep2_x = cos_t2 + alpha * sin_t2
        ep2_y = sin_t2 - alpha * cos_t2
        ep_x = cos_t2
        ep_y = sin_t2

        def transform_pt(px: float, py: float) -> tuple[float, float]:
            x = rx * px
            y = ry * py
            xr = cos_phi * x - sin_phi * y + arc_cx
            yr = sin_phi * x + cos_phi * y + arc_cy
            return xr, yr

        cp1 = transform_pt(ep1_x, ep1_y)
        cp2 = transform_pt(ep2_x, ep2_y)
        ep = transform_pt(ep_x, ep_y)

        result.append(PathCommand('C', [cp1[0], cp1[1], cp2[0], cp2[1], ep[0], ep[1]]))

    return result


def normalize_path_commands(commands: list[PathCommand]) -> list[PathCommand]:
    """Normalize path commands to M/L/C/Z only.

    Converts S -> C, Q -> C, T -> C, A -> C sequences.
    """
    result: list[PathCommand] = []
    cx, cy = 0.0, 0.0
    last_cp_x, last_cp_y = 0.0, 0.0
    last_cmd = ''

    for cmd in commands:
        a = cmd.args

        if cmd.cmd == 'M':
            cx, cy = a[0], a[1]
            last_cp_x, last_cp_y = cx, cy
            result.append(cmd)
        elif cmd.cmd == 'L':
            cx, cy = a[0], a[1]
            last_cp_x, last_cp_y = cx, cy
            result.append(cmd)
        elif cmd.cmd == 'C':
            last_cp_x, last_cp_y = a[2], a[3]
            cx, cy = a[4], a[5]
            result.append(cmd)
        elif cmd.cmd == 'S':
            if last_cmd in ('C', 'S'):
                rcp_x, rcp_y = _reflect_control_point(last_cp_x, last_cp_y, cx, cy)
            else:
                rcp_x, rcp_y = cx, cy
            last_cp_x, last_cp_y = a[0], a[1]
            new_cx, new_cy = a[2], a[3]
            result.append(PathCommand('C', [rcp_x, rcp_y, a[0], a[1], new_cx, new_cy]))
            cx, cy = new_cx, new_cy
        elif cmd.cmd == 'Q':
            cubic = _quad_to_cubic(a[0], a[1], cx, cy, a[2], a[3])
            last_cp_x, last_cp_y = a[0], a[1]
            result.append(PathCommand('C', cubic))
            cx, cy = a[2], a[3]
        elif cmd.cmd == 'T':
            if last_cmd in ('Q', 'T'):
                qp_x, qp_y = _reflect_control_point(last_cp_x, last_cp_y, cx, cy)
            else:
                qp_x, qp_y = cx, cy
            last_cp_x, last_cp_y = qp_x, qp_y
            cubic = _quad_to_cubic(qp_x, qp_y, cx, cy, a[0], a[1])
            result.append(PathCommand('C', cubic))
            cx, cy = a[0], a[1]
        elif cmd.cmd == 'A':
            arc_beziers = _arc_to_cubic_beziers(
                cx, cy, a[0], a[1], a[2], int(a[3]), int(a[4]), a[5], a[6],
            )
            for bc in arc_beziers:
                result.append(bc)
            cx, cy = a[5], a[6]
            last_cp_x, last_cp_y = cx, cy
        elif cmd.cmd == 'Z':
            result.append(cmd)
        else:
            result.append(cmd)

        last_cmd = cmd.cmd

    return result


def path_commands_to_drawingml(
    commands: list[PathCommand],
    offset_x: float = 0,
    offset_y: float = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> tuple[str, float, float, float, float]:
    """Convert normalized path commands to DrawingML <a:path> inner XML.

    Returns:
        (path_xml, min_x, min_y, width, height) in scaled+offset coordinates.
    """
    if not commands:
        return '', 0, 0, 0, 0

    # First pass: calculate bounding box
    points: list[tuple[float, float]] = []
    for cmd in commands:
        if cmd.cmd in ('M', 'L'):
            points.append((
                cmd.args[0] * scale_x + offset_x,
                cmd.args[1] * scale_y + offset_y,
            ))
        elif cmd.cmd == 'C':
            for i in range(0, 6, 2):
                points.append((
                    cmd.args[i] * scale_x + offset_x,
                    cmd.args[i + 1] * scale_y + offset_y,
                ))

    if not points:
        return '', 0, 0, 0, 0

    min_x = min(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_x = max(p[0] for p in points)
    max_y = max(p[1] for p in points)

    width = max(max_x - min_x, 1)
    height = max(max_y - min_y, 1)

    # Second pass: generate DrawingML path commands (EMU, relative to shape)
    parts: list[str] = []
    for cmd in commands:
        if cmd.cmd == 'M':
            x_emu = px_to_emu(cmd.args[0] * scale_x + offset_x - min_x)
            y_emu = px_to_emu(cmd.args[1] * scale_y + offset_y - min_y)
            parts.append(f'<a:moveTo><a:pt x="{x_emu}" y="{y_emu}"/></a:moveTo>')
        elif cmd.cmd == 'L':
            x_emu = px_to_emu(cmd.args[0] * scale_x + offset_x - min_x)
            y_emu = px_to_emu(cmd.args[1] * scale_y + offset_y - min_y)
            parts.append(f'<a:lnTo><a:pt x="{x_emu}" y="{y_emu}"/></a:lnTo>')
        elif cmd.cmd == 'C':
            pts = []
            for i in range(0, 6, 2):
                x_emu = px_to_emu(cmd.args[i] * scale_x + offset_x - min_x)
                y_emu = px_to_emu(cmd.args[i + 1] * scale_y + offset_y - min_y)
                pts.append(f'<a:pt x="{x_emu}" y="{y_emu}"/>')
            parts.append(f'<a:cubicBezTo>{"".join(pts)}</a:cubicBezTo>')
        elif cmd.cmd == 'Z':
            parts.append('<a:close/>')

    path_inner = '\n'.join(parts)
    return path_inner, min_x, min_y, width, height
