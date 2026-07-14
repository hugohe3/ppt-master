"""Coordinate, transform, color, and font helpers for DrawingML conversion.

See references/shared-standards.md §2.1 and §6.8 for project geometry and
transform authoring contracts.
"""

from __future__ import annotations

import colorsys
import math
import re
from collections.abc import Iterator
from xml.etree import ElementTree as ET

from pptx_shapes import validate_ooxml_xfrm

from .context import AffineMatrix, ConvertContext, IDENTITY_MATRIX

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

EMU_PER_PX = 9525  # 1 SVG px = 9525 EMU (96 DPI)
FONT_PX_TO_HUNDREDTHS_PT = 75  # 1px = 0.75pt -> 75 hundredths-of-a-point
DRAWINGML_TEXT_FONT_SIZE_MIN = 100
DRAWINGML_TEXT_FONT_SIZE_MAX = 400_000
ANGLE_UNIT = 60000  # DrawingML angle: 60000ths of a degree

# SVG attributes inheritable from parent <g>
INHERITABLE_ATTRS = [
    'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap',
    'stroke-linejoin', 'fill-opacity', 'stroke-opacity',
    'font-family', 'font-size', 'font-weight', 'font-style',
    'text-anchor', 'letter-spacing', 'text-decoration',
]

# Known East Asian fonts
EA_FONTS = {
    'PingFang SC', 'PingFang TC', 'PingFang HK',
    'Microsoft YaHei', 'Microsoft JhengHei',
    'SimSun', 'SimHei', 'FangSong', 'KaiTi', 'STKaiti',
    'STHeiti', 'STSong', 'STFangsong', 'STXihei', 'STZhongsong',
    'Hiragino Sans', 'Hiragino Sans GB', 'Hiragino Mincho ProN',
    'Hiragino Kaku Gothic ProN', 'Hiragino Kaku Gothic Pro',
    'Hiragino Mincho Pro',
    'Noto Sans SC', 'Noto Sans TC', 'Noto Serif SC', 'Noto Serif TC',
    'Noto Sans JP', 'Noto Serif JP', 'Noto Sans CJK JP',
    'Source Han Sans SC', 'Source Han Sans TC',
    'Source Han Serif SC', 'Source Han Serif TC',
    'Source Han Sans JP', 'Source Han Serif JP',
    'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
    'YouYuan', 'LiSu', 'HuaWenKaiTi',
    'Songti SC', 'Songti TC',
    # Windows 10/11 + Office default / common Simplified Chinese
    'DengXian', 'DengXian Light', 'DengXian Bold', 'Microsoft YaHei UI',
    # Office display Chinese (华文 / 方正) — usually title-only, not on every client
    'STXingkai', 'STLiti', 'STXinwei', 'STHupo', 'STCaiyun',
    'FZShuTi', 'FZYaoti',
    # Common Traditional Chinese (Office)
    'DFKai-SB', 'MingLiU', 'PMingLiU', 'MingLiU-ExtB', 'PMingLiU-ExtB',
    'Microsoft JhengHei UI',
    # Japanese fonts (Windows-available)
    'Yu Gothic', 'Yu Gothic UI', 'Yu Mincho',
    'Meiryo', 'Meiryo UI', 'メイリオ',
    'MS Gothic', 'MS Mincho', 'MS PGothic', 'MS PMincho', 'MS UI Gothic',
    # Korean
    'Malgun Gothic', 'Gulim', 'Dotum', 'Batang',
    'Noto Sans KR', 'Noto Serif KR',
}
SYSTEM_FONTS = {'system-ui', '-apple-system', 'BlinkMacSystemFont'}

# macOS/Linux-only fonts -> Windows equivalents
FONT_FALLBACK_WIN = {
    'PingFang SC': 'Microsoft YaHei',
    'PingFang TC': 'Microsoft JhengHei',
    'PingFang HK': 'Microsoft JhengHei',
    'Hiragino Sans': 'Microsoft YaHei',
    'Hiragino Sans GB': 'Microsoft YaHei',
    'Hiragino Mincho ProN': 'SimSun',
    'STHeiti': 'SimHei',
    'STSong': 'SimSun',
    'STKaiti': 'KaiTi',
    'STFangsong': 'FangSong',
    'STXihei': 'Microsoft YaHei',
    'STZhongsong': 'SimSun',
    'Songti SC': 'SimSun',
    'Songti TC': 'SimSun',
    'Noto Sans SC': 'Microsoft YaHei',
    'Noto Sans TC': 'Microsoft JhengHei',
    'Noto Serif SC': 'SimSun',
    'Noto Serif TC': 'SimSun',
    # Japanese: keep as-is if user specified (PowerPoint will fallback if uninstalled)
    # 'Noto Sans JP': → keep as 'Noto Sans JP' (do not map)
    # 'メイリオ': → keep as 'メイリオ' (Meiryo alias)
    'メイリオ': 'Meiryo',
    'Source Han Sans SC': 'Microsoft YaHei',
    'Source Han Sans TC': 'Microsoft JhengHei',
    'Source Han Serif SC': 'SimSun',
    'Source Han Serif TC': 'SimSun',
    'Source Han Sans JP': 'Noto Sans JP',
    'Source Han Serif JP': 'Noto Serif JP',
    'WenQuanYi Micro Hei': 'Microsoft YaHei',
    'WenQuanYi Zen Hei': 'Microsoft YaHei',
    # Latin fonts (macOS / Linux / Web -> Windows)
    'SF Pro': 'Segoe UI',
    'SF Pro Display': 'Segoe UI',
    'SF Pro Text': 'Segoe UI',
    'SF Mono': 'Consolas',
    'Menlo': 'Consolas',
    'Monaco': 'Consolas',
    'Helvetica Neue': 'Arial',
    'Helvetica': 'Arial',
    'Roboto': 'Segoe UI',
    'Ubuntu': 'Segoe UI',
    'Liberation Sans': 'Arial',
    'Liberation Serif': 'Times New Roman',
    'Liberation Mono': 'Consolas',
    'DejaVu Sans': 'Segoe UI',
    'DejaVu Serif': 'Times New Roman',
    'DejaVu Sans Mono': 'Consolas',
}

GENERIC_FONT_MAP = {
    'monospace': 'Consolas',
    'sans-serif': 'Segoe UI',
    'serif': 'Times New Roman',
}

# When the latin font is serif and no EA font is specified,
# prefer SimSun (serif CJK) over Microsoft YaHei (sans-serif CJK).
_SERIF_LATIN = {
    'Times New Roman', 'Georgia', 'Garamond', 'Palatino', 'Palatino Linotype',
    'Book Antiqua', 'Cambria', 'SimSun', 'Liberation Serif', 'DejaVu Serif',
}

# SVG stroke-dasharray -> DrawingML prstDash
DASH_PRESETS = {
    '4,4': 'dash',  '4 4': 'dash',
    '6,3': 'dash',  '6 3': 'dash',
    '2,2': 'sysDot', '2 2': 'sysDot',
    '8,4': 'lgDash', '8 4': 'lgDash',
    '8,4,2,4': 'lgDashDot', '8 4 2 4': 'lgDashDot',
}


def is_thick_circle_shorthand(
    dasharray: str | None,
    stroke: str | None,
    stroke_width: float,
    radius: float,
) -> bool:
    """Return whether one circle uses the converter's thick-arc shorthand."""
    if not dasharray or dasharray.strip().lower() == 'none':
        return False
    if not stroke or stroke.strip().lower() == 'none':
        return False
    if dasharray.strip() in DASH_PRESETS:
        return False
    if stroke_width <= 0 or radius <= 0:
        return False
    return stroke_width / radius >= 0.15


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def px_to_emu(px: float) -> int:
    """Convert SVG pixels to EMU."""
    return round(px * EMU_PER_PX)


def font_px_to_hpt(font_size_px: float) -> int:
    """Convert one legal SVG font size to DrawingML hundredths-of-a-point."""
    try:
        px = float(font_size_px)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            f"SVG font-size must be numeric, got {font_size_px!r}"
        ) from exc
    scaled = px * FONT_PX_TO_HUNDREDTHS_PT
    if not math.isfinite(scaled):
        raise ValueError(f"SVG font-size must be finite, got {font_size_px!r}")
    size = int(round(scaled / 10.0)) * 10
    if not DRAWINGML_TEXT_FONT_SIZE_MIN <= size <= DRAWINGML_TEXT_FONT_SIZE_MAX:
        raise ValueError(
            f"SVG font-size {font_size_px!r}px converts to DrawingML sz={size}; "
            f"expected {DRAWINGML_TEXT_FONT_SIZE_MIN}.."
            f"{DRAWINGML_TEXT_FONT_SIZE_MAX} (1..4000pt)"
        )
    return size


def _f(val: str | None, default: float = 0.0) -> float:
    """Parse a float attribute value, returning default if missing."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


_LENGTH_RE = re.compile(r'^\s*([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)\s*([A-Za-z%]*)\s*$')
_CANONICAL_PROJECT_GEOMETRY_LENGTH_RE = re.compile(
    r'^-?(?:\d+(?:\.\d+)?|\.\d+)$'
)
PROJECT_GEOMETRY_LENGTH_ATTRIBUTES = {
    'svg': frozenset({'x', 'y', 'width', 'height'}),
    'rect': frozenset({'x', 'y', 'width', 'height', 'rx', 'ry'}),
    'circle': frozenset({'cx', 'cy', 'r'}),
    'ellipse': frozenset({'cx', 'cy', 'rx', 'ry'}),
    'line': frozenset({'x1', 'y1', 'x2', 'y2'}),
    'text': frozenset({'x', 'y'}),
    'tspan': frozenset({'x', 'y', 'dx', 'dy'}),
    'image': frozenset({'x', 'y', 'width', 'height'}),
    'use': frozenset({'x', 'y', 'width', 'height'}),
}
PROJECT_NON_NEGATIVE_LENGTH_ATTRIBUTES = frozenset({
    'width', 'height', 'r', 'rx', 'ry', 'stroke-width',
})


def _parse_svg_length_parts(val: str) -> tuple[float, str]:
    """Parse one finite SVG length into its numeric part and lowercase unit."""
    match = _LENGTH_RE.match(str(val))
    if not match:
        raise ValueError(f'SVG length must be one finite literal, got {val!r}')
    number = float(match.group(1))
    if not math.isfinite(number):
        raise ValueError(f'SVG length must be finite, got {val!r}')
    return number, match.group(2).lower()


def parse_svg_length(
    val: str | None,
    default: float = 0.0,
    *,
    percent_base: float | None = None,
    font_size: float = 16.0,
) -> float:
    """Parse SVG/CSS length values into SVG px.

    Unitless and ``px`` values are already SVG px. Percentages need a caller
    supplied reference length because SVG uses different bases for x, y,
    width, height, and radii.

    A default applies only when the attribute is absent. Present but malformed,
    non-finite, unsupported, or context-free percentage values fail closed.
    """
    if val is None:
        return default
    number, unit = _parse_svg_length_parts(str(val))
    if unit == '%':
        if percent_base is None:
            raise ValueError(
                f'SVG percentage length requires a reference length, got {val!r}'
            )
        return percent_base * number / 100.0
    if unit in ('', 'px'):
        return number
    if unit == 'pt':
        return number * 96.0 / 72.0
    if unit in ('pc', 'pica'):
        return number * 16.0
    if unit == 'in':
        return number * 96.0
    if unit == 'cm':
        return number * 96.0 / 2.54
    if unit == 'mm':
        return number * 96.0 / 25.4
    if unit == 'q':
        return number * 96.0 / 101.6
    if unit in ('em', 'rem'):
        if not math.isfinite(font_size):
            raise ValueError(
                f'SVG relative length requires a finite font size, got {val!r}'
            )
        return number * font_size
    raise ValueError(f'Unsupported SVG length unit {unit!r} in {val!r}')


def parse_project_geometry_length(raw: str, attribute: str) -> float:
    """Parse one project geometry value without widening the authoring surface."""
    number, unit = _parse_svg_length_parts(raw)
    if unit not in {'', 'px'}:
        raise ValueError(
            f'uses unsupported unit {unit!r}; project geometry accepts only '
            'unitless values or the compatible px suffix'
        )
    numeric_literal = raw.strip()
    if unit == 'px':
        numeric_literal = numeric_literal[:-2].strip()
    if not _CANONICAL_PROJECT_GEOMETRY_LENGTH_RE.fullmatch(numeric_literal):
        raise ValueError(
            'uses an unsupported numeric spelling; use an ordinary decimal '
            'without a leading plus sign, exponent, or trailing decimal point'
        )
    if attribute in PROJECT_NON_NEGATIVE_LENGTH_ATTRIBUTES and number < 0:
        raise ValueError('must be non-negative')
    return number


def is_canonical_project_geometry_length(raw: str) -> bool:
    """Return whether a project geometry value uses the generated-SVG spelling."""
    return bool(_CANONICAL_PROJECT_GEOMETRY_LENGTH_RE.fullmatch(raw.strip()))


def format_project_geometry_length(value: float) -> str:
    """Format a parsed project geometry value as a plain unitless decimal."""
    if abs(value) < 1e-15:
        return '0'
    text = f'{value:.15f}'.rstrip('0').rstrip('.')
    return '0' if text in {'', '-0'} else text


def svg_length_x(val: str | None, ctx: ConvertContext, default: float = 0.0) -> float:
    return parse_svg_length(val, default, percent_base=ctx.viewport_width)


def svg_length_y(val: str | None, ctx: ConvertContext, default: float = 0.0) -> float:
    return parse_svg_length(val, default, percent_base=ctx.viewport_height)


def svg_length_size(val: str | None, ctx: ConvertContext, default: float = 0.0) -> float:
    base = min(ctx.viewport_width, ctx.viewport_height)
    return parse_svg_length(val, default, percent_base=base)


# ---------------------------------------------------------------------------
# SVG transform matrix helpers
# ---------------------------------------------------------------------------

_TRANSFORM_NUMBER_PATTERN = (
    r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?'
)
_TRANSFORM_NUMBER_RE = re.compile(_TRANSFORM_NUMBER_PATTERN)
_CANONICAL_TRANSFORM_NUMBER_RE = re.compile(
    r'-?(?:\d+(?:\.\d+)?|\.\d+)$'
)
_TRANSFORM_OPERATION_RE = re.compile(r'([A-Za-z]+)\(([^()]*)\)')
_TRANSFORM_WHITESPACE_RE = re.compile(r'[ \t\r\n]*')
_TRANSFORM_SEPARATOR_PATTERN = (
    r'(?:[ \t\r\n]+|[ \t\r\n]*,[ \t\r\n]*)'
)
_TRANSFORM_SEPARATOR_RE = re.compile(_TRANSFORM_SEPARATOR_PATTERN)
_TRANSFORM_ARGUMENTS_RE = re.compile(
    rf'[ \t\r\n]*{_TRANSFORM_NUMBER_PATTERN}'
    rf'(?:{_TRANSFORM_SEPARATOR_PATTERN}{_TRANSFORM_NUMBER_PATTERN})*'
    r'[ \t\r\n]*'
)
_TRANSFORM_ARITIES = {
    'matrix': frozenset({6}),
    'translate': frozenset({1, 2}),
    'scale': frozenset({1, 2}),
    'rotate': frozenset({1, 3}),
}
_FULL_TRANSFORM_TAGS = frozenset({
    'rect', 'circle', 'ellipse', 'line', 'path', 'polygon', 'polyline',
    'image',
})
_TRANSFORM_CONTAINER_TAGS = frozenset({'g', 'use'})
_TRANSFORM_DEFINITION_BOUNDARIES = frozenset({'clipPath', 'marker', 'pattern'})
_NON_VISUAL_TRANSFORM_CHILD_TAGS = frozenset({
    'defs', 'title', 'desc', 'metadata', 'style',
})


def matrix_multiply(left: AffineMatrix, right: AffineMatrix) -> AffineMatrix:
    """Compose two SVG affine matrices, applying ``right`` before ``left``."""
    a1, b1, c1, d1, e1, f1 = left
    a2, b2, c2, d2, e2, f2 = right
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _translate_matrix(tx: float, ty: float = 0.0) -> AffineMatrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def _scale_matrix(sx: float, sy: float | None = None) -> AffineMatrix:
    return (sx, 0.0, 0.0, sx if sy is None else sy, 0.0, 0.0)


def _rotate_matrix(angle_deg: float, cx: float | None = None, cy: float | None = None) -> AffineMatrix:
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    rot = (cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0)
    if cx is None or cy is None:
        return rot
    return matrix_multiply(
        matrix_multiply(_translate_matrix(cx, cy), rot),
        _translate_matrix(-cx, -cy),
    )


def _parse_transform_operations(
    transform_str: str,
) -> tuple[
    tuple[tuple[str, tuple[float, ...]], ...],
    tuple[str, ...],
]:
    """Parse a complete project transform list and retain numeric tokens."""
    if not transform_str:
        return (), ()

    operations: list[tuple[str, tuple[float, ...]]] = []
    number_tokens: list[str] = []
    cursor = 0
    matches = list(_TRANSFORM_OPERATION_RE.finditer(transform_str))
    if not matches:
        if _TRANSFORM_WHITESPACE_RE.fullmatch(transform_str):
            raise ValueError('SVG transform must not be empty')
        raise ValueError(f'Invalid SVG transform syntax {transform_str!r}')

    for index, match in enumerate(matches):
        gap = transform_str[cursor:match.start()]
        gap_pattern = (
            _TRANSFORM_WHITESPACE_RE
            if index == 0 else _TRANSFORM_SEPARATOR_RE
        )
        if gap_pattern.fullmatch(gap) is None:
            if index > 0 and not gap:
                raise ValueError(
                    f'SVG transform operations require a separator at '
                    f'offset {cursor}'
                )
            raise ValueError(
                f'Invalid SVG transform syntax at offset {cursor}: '
                f'{gap!r}'
            )
        name, raw_args = match.groups()
        if name not in _TRANSFORM_ARITIES:
            raise ValueError(
                f'Unsupported SVG transform operation {name!r}; use lowercase '
                'matrix, translate, scale, or rotate'
            )
        if raw_args.strip() and _TRANSFORM_ARGUMENTS_RE.fullmatch(raw_args) is None:
            raise ValueError(
                f'Invalid arguments for SVG transform {name!r}: {raw_args!r}'
            )
        tokens = tuple(_TRANSFORM_NUMBER_RE.findall(raw_args))
        values = tuple(float(token) for token in tokens)
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f'Non-finite arguments for SVG transform {name!r}')
        if len(values) not in _TRANSFORM_ARITIES[name]:
            expected = '/'.join(str(value) for value in sorted(_TRANSFORM_ARITIES[name]))
            raise ValueError(
                f'SVG transform {name!r} has {len(values)} argument(s); '
                f'expected {expected}'
            )
        operations.append((name, values))
        number_tokens.extend(tokens)
        cursor = match.end()

    trailing = transform_str[cursor:]
    if _TRANSFORM_WHITESPACE_RE.fullmatch(trailing) is None:
        raise ValueError(
            f'Invalid SVG transform trailing syntax at offset {cursor}: '
            f'{trailing!r}'
        )

    return tuple(operations), tuple(number_tokens)


def parse_transform_operations(
    transform_str: str,
) -> tuple[tuple[str, tuple[float, ...]], ...]:
    """Parse one complete supported SVG transform list."""
    operations, _ = _parse_transform_operations(transform_str)
    return operations


def noncanonical_transform_numbers(transform_str: str) -> tuple[str, ...]:
    """Return compatible transform numbers generated SVG should normalize."""
    _, tokens = _parse_transform_operations(transform_str)
    return tuple(
        token
        for token in tokens
        if _CANONICAL_TRANSFORM_NUMBER_RE.fullmatch(token) is None
    )


def _transform_operations_matrix(
    operations: tuple[tuple[str, tuple[float, ...]], ...],
) -> AffineMatrix:
    matrix = IDENTITY_MATRIX
    for name, args in operations:
        if name == 'matrix':
            local = (args[0], args[1], args[2], args[3], args[4], args[5])
        elif name == 'translate':
            local = _translate_matrix(
                args[0],
                args[1] if len(args) > 1 else 0.0,
            )
        elif name == 'scale':
            local = _scale_matrix(
                args[0],
                args[1] if len(args) > 1 else None,
            )
        else:
            local = _rotate_matrix(
                args[0],
                args[1] if len(args) > 2 else None,
                args[2] if len(args) > 2 else None,
            )
        matrix = matrix_multiply(matrix, local)
    return matrix


def parse_transform_matrix(transform_str: str) -> AffineMatrix:
    """Parse a complete SVG transform list into one affine matrix.

    Unsupported or malformed operations fail closed.  Treating an unknown
    operation as the identity would silently discard a visible SVG edit.
    """
    if not transform_str:
        return IDENTITY_MATRIX
    return _transform_operations_matrix(parse_transform_operations(transform_str))


def transform_point(matrix: AffineMatrix, x: float, y: float) -> tuple[float, float]:
    """Apply an SVG affine matrix to a point."""
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def validate_dml_shape_matrix(matrix: AffineMatrix) -> None:
    """Reject affine shear that a DrawingML shape transform cannot express."""
    if not all(math.isfinite(value) for value in matrix):
        raise ValueError('SVG transform produces non-finite matrix values')
    a, b, c, d, _e, _f = matrix
    x_length = math.hypot(a, b)
    y_length = math.hypot(c, d)
    if not math.isfinite(x_length) or not math.isfinite(y_length):
        raise ValueError('SVG transform produces non-finite axis lengths')
    if x_length <= 1e-12 or y_length <= 1e-12:
        raise ValueError(
            'SVG zero-scale transform cannot be represented by a visible '
            'DrawingML shape'
        )
    normalized_dot = (
        (a / x_length) * (c / y_length)
        + (b / x_length) * (d / y_length)
    )
    if not math.isfinite(normalized_dot) or abs(normalized_dot) > 1e-9:
        raise ValueError(
            'SVG shear/skew cannot be represented by a DrawingML '
            'shape transform'
        )


def _svg_element_tag(elem: ET.Element) -> str | None:
    raw_tag = str(elem.tag)
    if raw_tag.startswith('{'):
        namespace, tag = raw_tag[1:].split('}', 1)
        return tag if namespace == SVG_NS else None
    return raw_tag


def _transform_element_label(elem: ET.Element) -> str:
    tag = _svg_element_tag(elem) or str(elem.tag)
    elem_id = elem.get('id')
    return f'<{tag} id={elem_id!r}>' if elem_id else f'<{tag}>'


def _visual_transform_children(elem: ET.Element) -> list[ET.Element]:
    return [
        child
        for child in elem
        if _svg_element_tag(child) not in _NON_VISUAL_TRANSFORM_CHILD_TAGS
    ]


def _iter_visual_transform_tree(elem: ET.Element) -> Iterator[ET.Element]:
    """Yield one rendered subtree while excluding definition/metadata branches."""
    yield elem
    for child in _visual_transform_children(elem):
        yield from _iter_visual_transform_tree(child)


_TRANSFORM_ARC_STYLE_ATTRS = (
    'stroke',
    'stroke-width',
    'stroke-dasharray',
)


def _transform_arc_styles(
    elem: ET.Element,
    inherited: dict[str, str] | None = None,
) -> dict[str, str]:
    values = dict(inherited or {})
    inline_style = parse_inline_style(elem.get('style'))
    for name in _TRANSFORM_ARC_STYLE_ATTRS:
        direct = elem.get(name)
        if direct is not None:
            values[name] = direct
        if name in inline_style:
            values[name] = inline_style[name]
    return values


def _is_project_thick_circle(
    elem: ET.Element,
    arc_styles: dict[str, str],
) -> bool:
    if _svg_element_tag(elem) != 'circle':
        return False
    try:
        radius = parse_project_geometry_length(elem.get('r') or '0', 'r')
        stroke_width = parse_project_geometry_length(
            arc_styles.get('stroke-width', '0'),
            'stroke-width',
        )
    except ValueError:
        # Geometry preflight owns malformed length diagnostics.
        return False
    return is_thick_circle_shorthand(
        arc_styles.get('stroke-dasharray'),
        arc_styles.get('stroke'),
        stroke_width,
        radius,
    )


def supports_full_project_transform(
    elem: ET.Element,
    inherited_arc_styles: dict[str, str] | None = None,
) -> bool:
    """Return whether one subtree can consume an affine matrix without text loss."""
    tag = _svg_element_tag(elem)
    arc_styles = _transform_arc_styles(elem, inherited_arc_styles)
    if _is_project_thick_circle(elem, arc_styles):
        # Thick-circle arcs consume scalar context plus one local rotation;
        # treating an ancestor as a full matrix would silently drop it.
        return False
    if tag in _FULL_TRANSFORM_TAGS:
        return True
    if tag == 'use':
        # Local/data-icon use references are validated again after expansion.
        return True
    if tag == 'svg':
        children = _visual_transform_children(elem)
        return len(children) == 1 and _svg_element_tag(children[0]) == 'image'
    if tag == 'g':
        children = _visual_transform_children(elem)
        return bool(children) and all(
            supports_full_project_transform(child, arc_styles)
            for child in children
        )
    return False


def iter_project_transforms(
    root: ET.Element,
) -> Iterator[tuple[ET.Element, str]]:
    """Yield explicit SVG transform attributes from the project surface."""
    for elem in root.iter():
        if _svg_element_tag(elem) is None:
            continue
        raw = elem.get('transform')
        if raw is not None:
            yield elem, raw


def _has_positive_rounding(elem: ET.Element) -> bool:
    for attr in ('rx', 'ry'):
        raw = elem.get(attr)
        if raw is None:
            continue
        try:
            if parse_project_geometry_length(raw, attr) > 0:
                return True
        except ValueError:
            # Geometry preflight owns the malformed length diagnostic.
            continue
    return False


def _contains_rounded_rect(elem: ET.Element) -> bool:
    return any(
        _svg_element_tag(descendant) == 'rect'
        and _has_positive_rounding(descendant)
        for descendant in _iter_visual_transform_tree(elem)
    )


def _contains_native_marker(elem: ET.Element) -> bool:
    return any(
        descendant.get('data-pptx-native') in {'table', 'chart'}
        for descendant in _iter_visual_transform_tree(elem)
    )


def _project_thick_circle_ids(
    root: ET.Element,
) -> set[int]:
    thick_circle_ids: set[int] = set()

    def visit(elem: ET.Element, inherited: dict[str, str] | None = None) -> None:
        arc_styles = _transform_arc_styles(elem, inherited)
        if _is_project_thick_circle(elem, arc_styles):
            thick_circle_ids.add(id(elem))
        for child in elem:
            visit(child, arc_styles)

    visit(root)
    return thick_circle_ids


def _contains_thick_circle(elem: ET.Element, thick_circle_ids: set[int]) -> bool:
    return any(
        id(descendant) in thick_circle_ids
        for descendant in _iter_visual_transform_tree(elem)
    )


def _transform_semantic_error(
    elem: ET.Element,
    operations: tuple[tuple[str, tuple[float, ...]], ...],
    *,
    is_root: bool,
    thick_circle_ids: set[int],
) -> str | None:
    tag = _svg_element_tag(elem)
    names = tuple(name for name, _args in operations)
    label = _transform_element_label(elem)

    if is_root:
        return (
            'Root <svg> transform is unsupported; apply transforms to child '
            'elements or groups'
        )

    if tag == 'text':
        if all(name == 'translate' for name in names):
            return None
        if len(names) == 1 and names[0] == 'rotate':
            return None
        return (
            f'{label} text transform must be a translate-only list or one '
            'rotate operation; text scale, matrix, and mixed operations are '
            'not mapped'
        )

    if tag in _TRANSFORM_CONTAINER_TAGS:
        if _contains_native_marker(elem):
            if all(name in {'translate', 'scale'} for name in names):
                return None
            return (
                f'{label} native table/chart marker transforms support only '
                'translate and scale'
            )
        if _contains_thick_circle(elem, thick_circle_ids):
            if all(name == 'translate' for name in names):
                return None
            return (
                f'{label} contains a thick-circle arc shorthand; ancestor '
                'transforms must be translate-only'
            )
        if supports_full_project_transform(elem):
            if 'matrix' in names and _contains_rounded_rect(elem):
                return (
                    f'{label} matrix transform cannot target a rounded '
                    'rectangle subtree'
                )
            return None
        if all(name == 'translate' for name in names):
            return None
        if len(names) == 1 and names[0] == 'rotate':
            return None
        return (
            f'{label} contains text or another non-matrix visual; its transform '
            'must be a translate-only list or one rotate operation'
        )

    if tag in _FULL_TRANSFORM_TAGS:
        if id(elem) in thick_circle_ids:
            if len(names) == 1 and names[0] == 'rotate':
                return None
            return (
                f'{label} thick-circle arc transform must be one rotate '
                'operation'
            )
        if tag == 'rect' and 'matrix' in names and _has_positive_rounding(elem):
            return f'{label} rounded rectangles cannot use matrix transforms'
        return None

    if tag == 'svg' and supports_full_project_transform(elem):
        return None

    return f'{label} has no registered project transform mapping'


def project_transform_errors(root: ET.Element) -> list[str]:
    """Return blocking transform grammar and mapping errors for preflight."""
    parent_by_id = {
        id(child): parent
        for parent in root.iter()
        for child in list(parent)
    }
    thick_circle_ids = _project_thick_circle_ids(root)
    parsed: dict[int, tuple[AffineMatrix, bool]] = {}
    errors: set[str] = set()

    for elem, raw in iter_project_transforms(root):
        label = _transform_element_label(elem)
        restricted_ancestor = None
        current = parent_by_id.get(id(elem))
        while current is not None:
            current_tag = _svg_element_tag(current)
            if current_tag in _TRANSFORM_DEFINITION_BOUNDARIES:
                restricted_ancestor = current_tag
                break
            current = parent_by_id.get(id(current))
        if restricted_ancestor is not None:
            errors.add(
                f'{label} cannot use transform inside <{restricted_ancestor}>'
            )
            parsed[id(elem)] = (IDENTITY_MATRIX, False)
            continue

        try:
            operations = parse_transform_operations(raw)
            if not operations:
                raise ValueError('SVG transform must not be empty')
            matrix = _transform_operations_matrix(operations)
        except ValueError as exc:
            errors.add(f'{label} transform={raw!r}: {exc}')
            parsed[id(elem)] = (IDENTITY_MATRIX, False)
            continue

        semantic_error = _transform_semantic_error(
            elem,
            operations,
            is_root=elem is root,
            thick_circle_ids=thick_circle_ids,
        )
        if semantic_error is not None:
            errors.add(semantic_error)
        parsed[id(elem)] = (matrix, semantic_error is None)

    def validate_branch(elem: ET.Element, parent_matrix: AffineMatrix) -> None:
        current_matrix = parent_matrix
        entry = parsed.get(id(elem))
        if entry is not None:
            local_matrix, semantic_ok = entry
            if not semantic_ok:
                return
            current_matrix = matrix_multiply(parent_matrix, local_matrix)
            try:
                validate_dml_shape_matrix(current_matrix)
            except ValueError as exc:
                errors.add(
                    f'{_transform_element_label(elem)} has an unsupported '
                    f'cumulative transform: {exc}'
                )
                return
        for child in elem:
            validate_branch(child, current_matrix)

    validate_branch(root, IDENTITY_MATRIX)
    return sorted(errors)


def rect_to_dml_xfrm(
    x: float,
    y: float,
    w: float,
    h: float,
    matrix: AffineMatrix,
    *,
    preserve_degenerate_axes: bool = False,
) -> tuple[str, int, int, int, int, tuple[int, int, int, int]]:
    """Map a transformed SVG rectangle to DrawingML xfrm attributes.

    DrawingML can represent rotated/flipped rectangles, but not arbitrary
    shear. Template-import picture wrappers only use translate/rotate/scale,
    so decomposing the transformed local X/Y axes is sufficient here.
    """
    p0 = transform_point(matrix, x, y)
    p1 = transform_point(matrix, x + w, y)
    p2 = transform_point(matrix, x + w, y + h)
    p3 = transform_point(matrix, x, y + h)

    ux = p1[0] - p0[0]
    uy = p1[1] - p0[1]
    vx = p3[0] - p0[0]
    vy = p3[1] - p0[1]

    rect_w = math.hypot(ux, uy)
    rect_h = math.hypot(vx, vy)
    validate_dml_shape_matrix(matrix)
    if not preserve_degenerate_axes:
        rect_w = max(rect_w, 0.001)
        rect_h = max(rect_h, 0.001)
    cross = ux * vy - uy * vx

    if rect_w <= 1e-12 and rect_h > 1e-12:
        angle_deg = math.degrees(math.atan2(vy, vx)) - 90.0
        flip_attr = ''
    elif cross < 0:
        angle_deg = math.degrees(math.atan2(-uy, -ux))
        flip_attr = ' flipH="1"'
    else:
        angle_deg = math.degrees(math.atan2(uy, ux))
        flip_attr = ''

    rot = round(angle_deg * ANGLE_UNIT)
    rot_attr = f' rot="{rot}"' if rot else ''

    center_x = (p0[0] + p2[0]) / 2
    center_y = (p0[1] + p2[1]) / 2
    off_x = px_to_emu(center_x - rect_w / 2)
    off_y = px_to_emu(center_y - rect_h / 2)
    ext_cx = px_to_emu(rect_w)
    ext_cy = px_to_emu(rect_h)
    validate_ooxml_xfrm(off_x, off_y, ext_cx, ext_cy)

    xs = [p0[0], p1[0], p2[0], p3[0]]
    ys = [p0[1], p1[1], p2[1], p3[1]]
    bounds = (
        px_to_emu(min(xs)),
        px_to_emu(min(ys)),
        px_to_emu(max(xs)),
        px_to_emu(max(ys)),
    )

    return f'{flip_attr}{rot_attr}', off_x, off_y, ext_cx, ext_cy, bounds


def _extract_inheritable_styles(elem: ET.Element) -> dict[str, str]:
    """Extract all SVG-inheritable presentation attributes from an element."""
    styles: dict[str, str] = {}
    for attr in INHERITABLE_ATTRS:
        val = elem.get(attr)
        if val is not None:
            styles[attr] = val
    styles.update({
        attr: val
        for attr, val in parse_inline_style(elem.get('style')).items()
        if attr in INHERITABLE_ATTRS
    })
    return styles


def _get_attr(elem: ET.Element, attr: str, ctx: ConvertContext) -> str | None:
    """Get effective attribute: element's own value first, then inherited."""
    style_val = parse_inline_style(elem.get('style')).get(attr)
    if style_val is not None:
        return style_val
    val = elem.get(attr)
    if val is not None:
        return val
    return ctx.inherited_styles.get(attr)


def ctx_x(val: float, ctx: ConvertContext) -> float:
    """Apply context scale + translate to an X coordinate."""
    return val * ctx.scale_x + ctx.translate_x


def ctx_y(val: float, ctx: ConvertContext) -> float:
    """Apply context scale + translate to a Y coordinate."""
    return val * ctx.scale_y + ctx.translate_y


def ctx_w(val: float, ctx: ConvertContext) -> float:
    """Apply context scale to a width value."""
    return val * ctx.scale_x


def ctx_h(val: float, ctx: ConvertContext) -> float:
    """Apply context scale to a height value."""
    return val * ctx.scale_y


# ---------------------------------------------------------------------------
# Color / style parsing
# ---------------------------------------------------------------------------

_CSS_NAMED_COLORS = {
    'black': '000000',
    'silver': 'C0C0C0',
    'gray': '808080',
    'grey': '808080',
    'white': 'FFFFFF',
    'maroon': '800000',
    'red': 'FF0000',
    'purple': '800080',
    'fuchsia': 'FF00FF',
    'magenta': 'FF00FF',
    'green': '008000',
    'lime': '00FF00',
    'olive': '808000',
    'yellow': 'FFFF00',
    'navy': '000080',
    'blue': '0000FF',
    'teal': '008080',
    'aqua': '00FFFF',
    'cyan': '00FFFF',
    'orange': 'FFA500',
    'brown': 'A52A2A',
    'pink': 'FFC0CB',
    'gold': 'FFD700',
    'transparent': None,
    'lightgray': 'D3D3D3',
    'lightgrey': 'D3D3D3',
    'darkgray': 'A9A9A9',
    'darkgrey': 'A9A9A9',
}


def parse_inline_style(style_str: str | None) -> dict[str, str]:
    """Parse an SVG inline style declaration into ``property: value`` pairs."""
    styles: dict[str, str] = {}
    if not style_str:
        return styles
    for part in style_str.split(';'):
        if ':' not in part:
            continue
        name, value = part.split(':', 1)
        name = name.strip().lower()
        value = value.strip()
        if name and value:
            styles[name] = value
    return styles


def iter_project_geometry_lengths(
    root: ET.Element,
) -> Iterator[tuple[ET.Element, str, str, str]]:
    """Yield project geometry values as element, attribute, raw value, source."""
    for elem in root.iter():
        tag = elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)
        for attribute in sorted(
            PROJECT_GEOMETRY_LENGTH_ATTRIBUTES.get(tag, frozenset())
        ):
            raw = elem.get(attribute)
            if raw is not None:
                yield elem, attribute, raw, 'attribute'

        direct_stroke_width = elem.get('stroke-width')
        if direct_stroke_width is not None:
            yield elem, 'stroke-width', direct_stroke_width, 'attribute'

        style_stroke_width = parse_inline_style(elem.get('style')).get('stroke-width')
        if style_stroke_width is not None:
            yield elem, 'stroke-width', style_stroke_width, 'inline style'


def project_geometry_length_errors(root: ET.Element) -> list[str]:
    """Return blocking project geometry errors for converter preflight."""
    errors: list[str] = []
    for elem, attribute, raw, source in iter_project_geometry_lengths(root):
        tag = elem.tag.rsplit('}', 1)[-1] if '}' in str(elem.tag) else str(elem.tag)
        elem_id = elem.get('id')
        label = f'<{tag} id={elem_id!r}>' if elem_id else f'<{tag}>'
        try:
            parse_project_geometry_length(raw, attribute)
        except ValueError as exc:
            errors.append(
                f'{label} {source} {attribute}={raw!r}: {exc}'
            )
    return errors


def _finite_float(raw: str) -> float:
    """Parse a finite floating-point number."""
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f'Non-finite numeric value: {raw}')
    return value


def _parse_color_channel(raw: str) -> int:
    raw = raw.strip()
    if raw.endswith('%'):
        value = _finite_float(raw[:-1]) * 255.0 / 100.0
    else:
        value = _finite_float(raw)
    return max(0, min(255, int(round(value))))


def _parse_alpha_channel(raw: str) -> float:
    """Parse a CSS alpha channel as a clamped ``0..1`` ratio."""
    raw = raw.strip()
    value = (
        _finite_float(raw[:-1]) / 100.0
        if raw.endswith('%')
        else _finite_float(raw)
    )
    return max(0.0, min(1.0, value))


def parse_opacity(raw: str | None, default: float = 1.0) -> float:
    """Parse a number or percentage opacity, falling back to ``default``."""
    if raw is None:
        return max(0.0, min(1.0, default))
    try:
        return _parse_alpha_channel(raw)
    except ValueError:
        return max(0.0, min(1.0, default))


def _functional_color_parts(body: str) -> tuple[list[str], str | None]:
    """Split legacy comma or modern space/slash functional color syntax."""
    before, separator, after = body.partition('/')
    parts = [part for part in re.split(r'[\s,]+', before.strip()) if part]
    alpha = after.strip() if separator else None
    if alpha is None and len(parts) > 3:
        alpha = parts.pop()
    return parts, alpha


def _parse_hue_degrees(raw: str) -> float:
    """Normalize a CSS hue angle to degrees."""
    value = raw.strip().lower()
    for suffix, multiplier in (
        ('turn', 360.0),
        ('grad', 0.9),
        ('rad', 180.0 / math.pi),
        ('deg', 1.0),
    ):
        if value.endswith(suffix):
            return _finite_float(value[:-len(suffix)]) * multiplier
    return _finite_float(value)


def _parse_percentage(raw: str) -> float:
    """Parse a CSS percentage channel as a clamped ``0..1`` ratio."""
    value = raw.strip()
    ratio = (
        _finite_float(value[:-1]) / 100.0
        if value.endswith('%')
        else _finite_float(value) / 100.0
    )
    return max(0.0, min(1.0, ratio))


def parse_svg_color(color_str: str) -> tuple[str | None, float]:
    """Parse an SVG/CSS color into ``(RRGGBB, alpha)``."""
    if not color_str:
        return None, 1.0
    color_str = color_str.strip()
    named = _CSS_NAMED_COLORS.get(color_str.lower())
    if named is not None or color_str.lower() in _CSS_NAMED_COLORS:
        if color_str.lower() == 'transparent':
            return '000000', 0.0
        return named, 1.0

    rgb_match = re.match(r'rgba?\((.+)\)$', color_str, flags=re.IGNORECASE)
    if rgb_match:
        channels, alpha_raw = _functional_color_parts(rgb_match.group(1))
        if len(channels) == 3:
            try:
                r, g, b = (_parse_color_channel(ch) for ch in channels)
                alpha = _parse_alpha_channel(alpha_raw) if alpha_raw is not None else 1.0
                return f'{r:02X}{g:02X}{b:02X}', alpha
            except ValueError:
                return None, 1.0

    hsl_match = re.match(r'hsla?\((.+)\)$', color_str, flags=re.IGNORECASE)
    if hsl_match:
        channels, alpha_raw = _functional_color_parts(hsl_match.group(1))
        if len(channels) == 3:
            try:
                hue = (_parse_hue_degrees(channels[0]) % 360.0) / 360.0
                saturation = _parse_percentage(channels[1])
                lightness = _parse_percentage(channels[2])
                red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
                alpha = _parse_alpha_channel(alpha_raw) if alpha_raw is not None else 1.0
                return (
                    f'{round(red * 255):02X}{round(green * 255):02X}{round(blue * 255):02X}',
                    alpha,
                )
            except ValueError:
                return None, 1.0

    if color_str.startswith('#'):
        color_str = color_str[1:]
    if len(color_str) == 3:
        color_str = ''.join(c * 2 for c in color_str)
    elif len(color_str) == 4:
        color_str = ''.join(c * 2 for c in color_str)
    if len(color_str) == 8 and all(c in '0123456789abcdefABCDEF' for c in color_str):
        return color_str[:6].upper(), int(color_str[6:], 16) / 255.0
    if len(color_str) == 6 and all(c in '0123456789abcdefABCDEF' for c in color_str):
        return color_str.upper(), 1.0
    return None, 1.0


def parse_hex_color(color_str: str) -> str | None:
    """Parse SVG color values to ``RRGGBB``, ignoring any alpha channel."""
    if color_str and color_str.strip().lower() == 'transparent':
        return None
    color, _alpha = parse_svg_color(color_str)
    return color


def combine_opacity(*values: float | None) -> float | None:
    """Multiply opacity components, returning ``None`` when fully opaque."""
    combined = 1.0
    for value in values:
        if value is not None:
            combined *= max(0.0, min(1.0, value))
    return combined if combined < 1.0 else None


def parse_stop_style(style_str: str) -> tuple[str | None, float]:
    """Parse a gradient stop's style attribute.

    Args:
        style_str: Style string like 'stop-color:#XXX;stop-opacity:N'.

    Returns:
        (color, opacity) tuple.
    """
    color = None
    color_alpha = 1.0
    stop_opacity = 1.0
    style_values = parse_inline_style(style_str)
    if not style_values:
        return color, stop_opacity

    if 'stop-color' in style_values:
        color, color_alpha = parse_svg_color(style_values['stop-color'])
    if 'stop-opacity' in style_values:
        stop_opacity = parse_opacity(style_values['stop-opacity'])

    return color, color_alpha * stop_opacity


def resolve_url_id(url_str: str) -> str | None:
    """Extract ID from 'url(#someId)' reference."""
    if not url_str:
        return None
    m = re.match(r'url\(#([^)]+)\)', url_str.strip())
    return m.group(1) if m else None


def get_effective_filter_id(elem: ET.Element, ctx: ConvertContext) -> str | None:
    """Get the effective filter ID for an element, including inherited context."""
    filt = elem.get('filter')
    if filt:
        return resolve_url_id(filt)
    return ctx.filter_id


# ---------------------------------------------------------------------------
# Font parsing
# ---------------------------------------------------------------------------

def parse_font_family(font_family_str: str) -> dict[str, str]:
    """Parse CSS font-family into latin/ea typeface names.

    Prioritizes Windows-available fonts since PPTX is primarily opened on
    Windows. macOS/Linux-only fonts are mapped via FONT_FALLBACK_WIN.
    """
    if not font_family_str:
        return {'latin': 'Segoe UI', 'ea': 'Microsoft YaHei'}

    fonts = [f.strip().strip("'\"") for f in font_family_str.split(',')]
    latin_font = None
    ea_font = None

    for font in fonts:
        if font in SYSTEM_FONTS:
            continue
        if font in GENERIC_FONT_MAP:
            resolved = GENERIC_FONT_MAP[font]
            latin_font = latin_font or resolved
            continue

        win_font = FONT_FALLBACK_WIN.get(font, font)
        if font in EA_FONTS:
            ea_font = ea_font or win_font
        else:
            latin_font = latin_font or win_font

    # PPT renders CJK text via latin typeface when ea doesn't match
    if not latin_font and ea_font:
        latin_font = ea_font

    final_latin = latin_font or 'Segoe UI'

    # EA must always be a CJK-capable font
    if not ea_font:
        ea_font = 'SimSun' if final_latin in _SERIF_LATIN else 'Microsoft YaHei'

    return {'latin': final_latin, 'ea': ea_font}


def is_cjk_char(ch: str) -> bool:
    """Check if a character is CJK (Chinese/Japanese/Korean)."""
    cp = ord(ch)
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0x2E80 <= cp <= 0x2EFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0xF900 <= cp <= 0xFAFF or
            0x20000 <= cp <= 0x2A6DF)


def detect_text_lang(text: str) -> str:
    """Return a DrawingML language tag for a text run."""
    return 'zh-CN' if any(is_cjk_char(ch) for ch in text) else 'en-US'


def resolve_text_run_fonts(text: str, fonts: dict[str, str]) -> dict[str, str]:
    """Return DrawingML latin/ea/cs typefaces for one text run."""
    latin = fonts['latin']
    if detect_text_lang(text) == 'zh-CN':
        ea = fonts['ea']
    else:
        ea = latin
    return {'latin': latin, 'ea': ea, 'cs': latin}


def estimate_text_width(text: str, font_size: float, font_weight: str = '400') -> float:
    """Estimate text width in SVG pixels."""
    width = 0.0
    for ch in text:
        if is_cjk_char(ch):
            width += font_size
        elif ch == ' ':
            width += font_size * 0.3
        elif ch in 'mMwWOQ%':
            width += font_size * 0.75
        elif ch in 'iIlj!|':
            width += font_size * 0.3
        elif ch.isdigit():
            # digits are tabular (uniform ~0.55em) in most UI fonts, including
            # '1' — classing it with 'il|' under-sizes the box and makes
            # renderers that ignore wrap="none" (LibreOffice) wrap the line
            width += font_size * 0.55
        else:
            width += font_size * 0.55

    if font_weight in ('bold', '600', '700', '800', '900'):
        width *= 1.05

    return width


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
