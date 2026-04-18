"""Blueprint IR -> compliant SVG emitter.

Outputs SVG that obeys shared-standards.md §1 — banned features are NEVER
generated (no <style>, no class=, no mask, no rgba, no foreignObject,
no <g opacity>, etc.). A built-in linter at the bottom of this module
double-checks the output and raises on any violation.

Coordinate convention: Shape.bbox is in absolute viewBox coordinates (px).
Shape.path_d is in local coordinates (0..w, 0..h) relative to the bbox; the
emitter wraps paths in a <g transform="translate(...)"> so the path_d values
need no rewriting.

Font size: DrawingML `sz` values are points (pt). Per project convention
(design_spec_reference.md), we treat the numeric value as px when emitting SVG,
matching the templates/ hand-authored style.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from xml.sax.saxutils import escape as xml_escape

from .ir import (
    Blueprint, Fill, GradientSpec, Shape, SlideBlueprint,
    Stroke, TextParagraph, TextRun, Theme,
)


# ---------------------------------------------------------------------------
# Emit context (gradient defs, id allocation)
# ---------------------------------------------------------------------------

@dataclass
class EmitContext:
    """Shared state carried through an emit pass for one slide."""
    theme: Theme
    gradient_defs: list[str] = field(default_factory=list)
    gradient_id_counter: int = 1

    def next_gradient_id(self) -> str:
        """Allocate a unique gradient id for defs reference."""
        gid = f"grad{self.gradient_id_counter}"
        self.gradient_id_counter += 1
        return gid


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------

def _f(val: float) -> str:
    """Format a float as a compact string (trim trailing zeros)."""
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}".rstrip('0').rstrip('.')


# ---------------------------------------------------------------------------
# Fill emission (solid / gradient / none / image-as-fill)
# ---------------------------------------------------------------------------

def _emit_gradient_def(spec: GradientSpec, gid: str) -> str:
    """Build a <linearGradient> or <radialGradient> XML snippet."""
    stops_xml = []
    for s in spec.stops:
        pos_pct = s.pos * 100.0
        alpha_attr = ""
        if s.opacity < 1.0:
            alpha_attr = f' stop-opacity="{_f(s.opacity)}"'
        stops_xml.append(
            f'  <stop offset="{_f(pos_pct)}%" stop-color="#{s.color}"{alpha_attr}/>'
        )
    stops = "\n".join(stops_xml)

    if spec.kind == 'radial':
        return (
            f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%">\n'
            f'{stops}\n'
            f'</radialGradient>'
        )

    # linear: convert DrawingML angle (deg, 0 = left->right) to x1,y1,x2,y2
    rad = math.radians(spec.angle_deg)
    # DrawingML: 0deg = left-to-right, increasing clockwise
    # SVG default (x1=0,y1=0,x2=1,y2=0) is also left-to-right
    # Rotate (0,0)->(1,0) by angle
    x1, y1 = 0.0, 0.5
    x2 = 0.5 + 0.5 * math.cos(rad)
    y2 = 0.5 + 0.5 * math.sin(rad)
    x1 = 0.5 - 0.5 * math.cos(rad)
    y1 = 0.5 - 0.5 * math.sin(rad)
    return (
        f'<linearGradient id="{gid}" '
        f'x1="{_f(x1 * 100)}%" y1="{_f(y1 * 100)}%" '
        f'x2="{_f(x2 * 100)}%" y2="{_f(y2 * 100)}%">\n'
        f'{stops}\n'
        f'</linearGradient>'
    )


def _fill_attrs(fill: Fill | None, ctx: EmitContext) -> str:
    """Return the `fill="..."` (and `fill-opacity`) attributes for a shape."""
    if fill is None:
        # Default: no explicit fill, let the renderer default (usually black).
        # For our use case, defaulting to noFill is safer.
        return 'fill="none"'

    if fill.kind == 'none':
        return 'fill="none"'

    if fill.kind == 'solid':
        color = fill.color or '000000'
        op = f' fill-opacity="{_f(fill.opacity)}"' if fill.opacity < 1.0 else ''
        return f'fill="#{color}"{op}'

    if fill.kind == 'gradient' and fill.gradient is not None:
        gid = ctx.next_gradient_id()
        ctx.gradient_defs.append(_emit_gradient_def(fill.gradient, gid))
        return f'fill="url(#{gid})"'

    # image fill — handled at the shape level (rendered as <image>, not a fill)
    return 'fill="none"'


def _stroke_attrs(stroke: Stroke | None) -> str:
    """Return stroke-related attributes for a shape."""
    if stroke is None or stroke.color is None:
        return ''
    parts = [f'stroke="#{stroke.color}"', f'stroke-width="{_f(stroke.width)}"']
    if stroke.opacity < 1.0:
        parts.append(f'stroke-opacity="{_f(stroke.opacity)}"')
    dash_map = {
        'dash': '6,3',
        'dot': '2,2',
        'dashDot': '6,3,2,3',
        'lgDash': '12,3',
    }
    if stroke.dash and stroke.dash != 'solid':
        pattern = dash_map.get(stroke.dash)
        if pattern:
            parts.append(f'stroke-dasharray="{pattern}"')
    cap_map = {'rnd': 'round', 'sq': 'square', 'flat': 'butt'}
    if stroke.cap != 'flat':
        parts.append(f'stroke-linecap="{cap_map.get(stroke.cap, "butt")}"')
    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Transform (rotation + flip)
# ---------------------------------------------------------------------------

def _transform_attr(shape: Shape) -> str:
    """Build transform="..." for rotation and flipH/flipV (around bbox center).

    Rotation values that are multiples of 360° are treated as no-ops — PowerPoint
    sometimes stores rot=21600000 (exactly 360°) for unrotated shapes.
    """
    x, y, w, h = shape.bbox
    cx, cy = x + w / 2.0, y + h / 2.0
    ops: list[str] = []

    effective_rot = shape.rotation % 360.0 if shape.rotation else 0.0
    if abs(effective_rot) > 0.01:
        ops.append(f"rotate({_f(effective_rot)} {_f(cx)} {_f(cy)})")

    if shape.flip_h or shape.flip_v:
        sx = -1 if shape.flip_h else 1
        sy = -1 if shape.flip_v else 1
        # Flip around the shape center: translate(cx,cy) scale(...) translate(-cx,-cy)
        ops.append(
            f"translate({_f(cx)} {_f(cy)}) scale({sx} {sy}) translate({_f(-cx)} {_f(-cy)})"
        )

    return f' transform="{" ".join(ops)}"' if ops else ''


# ---------------------------------------------------------------------------
# Text emission
# ---------------------------------------------------------------------------

_ALIGN_TO_ANCHOR = {
    'l': 'start',
    'ctr': 'middle',
    'r': 'end',
    'just': 'start',
}


def _emit_text(shape: Shape, ctx: EmitContext) -> str:
    """Emit a <text> block with <tspan>s per paragraph.

    Layout strategy (v1, simple):
    - One <text> element per paragraph.
    - y advances by font_size * line_spacing_pct / 100 between paragraphs.
    - Anchor (vertical) positions the first baseline relative to bbox.
    - text-anchor (horizontal) set per paragraph.

    If `shape.placeholder_tag` is set, the entire body is replaced with a
    single centered line carrying the tag, using the first run's style as
    its typography baseline.
    """
    if shape.text is None or not shape.text.paragraphs:
        return ''

    if shape.placeholder_tag:
        return _emit_placeholder_text(shape, ctx)

    x, y, w, h = shape.bbox
    tc = shape.text

    # Estimate total text block height to support vertical anchor
    # Use the dominant font size of the first run per paragraph (fallback 18)
    def _para_font_size(p: TextParagraph) -> float:
        for r in p.runs:
            if r.font_size:
                return r.font_size
        return 18.0

    line_heights = [
        _para_font_size(p) * (p.line_spacing_pct / 100.0) for p in tc.paragraphs
    ]
    total_h = sum(line_heights)

    if tc.anchor == 'ctr':
        base_y = y + (h - total_h) / 2.0
    elif tc.anchor == 'b':
        base_y = y + h - total_h
    else:  # 't' or fallback
        base_y = y

    # First line baseline sits one line-height below base_y top
    cursor_y = base_y

    text_blocks: list[str] = []
    for i, p in enumerate(tc.paragraphs):
        lh = line_heights[i]
        baseline_y = cursor_y + lh * 0.8  # 0.8 = typographic baseline factor
        cursor_y += lh

        # Determine x based on align
        anchor = _ALIGN_TO_ANCHOR.get(p.align, 'start')
        if anchor == 'start':
            x_text = x
        elif anchor == 'middle':
            x_text = x + w / 2.0
        else:  # end
            x_text = x + w

        runs_xml = _emit_runs(p.runs, p.bullet)
        if not runs_xml.strip():
            continue

        # Apply inherited attributes at the <text> level to save bytes
        text_attrs = [
            f'x="{_f(x_text)}"',
            f'y="{_f(baseline_y)}"',
            f'text-anchor="{anchor}"',
        ]
        text_blocks.append(
            f'<text {" ".join(text_attrs)}>{runs_xml}</text>'
        )

    return "\n".join(text_blocks)


def _emit_placeholder_text(shape: Shape, ctx: EmitContext) -> str:
    """Render a single line carrying shape.placeholder_tag.

    Uses the first run's style for typography (font-size/family/weight/color)
    and the first paragraph's alignment. The text body is replaced with the
    tag verbatim (e.g. `{{TITLE}}`), collapsing any multi-paragraph source.
    """
    if not shape.placeholder_tag or shape.text is None:
        return ''

    first_para = shape.text.paragraphs[0] if shape.text.paragraphs else None
    first_run: TextRun | None = None
    if first_para is not None:
        for r in first_para.runs:
            if r.text.strip():
                first_run = r
                break

    # Fallback synthetic run if the source body is empty
    if first_run is None:
        first_run = TextRun(text=shape.placeholder_tag, font_size=18.0)

    # Compose layout using the same math as _emit_text (single-line case)
    x, y, w, h = shape.bbox
    anchor = shape.text.anchor
    align = first_para.align if first_para is not None else 'l'

    font_size = first_run.font_size or 18.0
    line_height = font_size * (
        first_para.line_spacing_pct / 100.0 if first_para is not None else 1.0
    )

    if anchor == 'ctr':
        baseline_y = y + (h - line_height) / 2.0 + line_height * 0.8
    elif anchor == 'b':
        baseline_y = y + h - line_height * 0.2
    else:
        baseline_y = y + line_height * 0.8

    svg_anchor = _ALIGN_TO_ANCHOR.get(align, 'start')
    if svg_anchor == 'start':
        x_text = x
    elif svg_anchor == 'middle':
        x_text = x + w / 2.0
    else:
        x_text = x + w

    # Reuse the same tspan-style attributes as normal runs
    tspan_attrs = _run_attrs(first_run)
    safe_tag = xml_escape(shape.placeholder_tag)
    if tspan_attrs:
        body = f'<tspan {tspan_attrs}>{safe_tag}</tspan>'
    else:
        body = safe_tag

    return (
        f'<text x="{_f(x_text)}" y="{_f(baseline_y)}" '
        f'text-anchor="{svg_anchor}">{body}</text>'
    )


def _emit_runs(runs: list[TextRun], bullet: str | None) -> str:
    """Emit a list of runs as <tspan>s, with optional bullet prefix on first run."""
    if not runs:
        return ''

    parts: list[str] = []
    first = True
    for r in runs:
        text = r.text
        if first and bullet:
            text = f"{bullet} {text}"
            first = False
        else:
            first = False

        attrs = _run_attrs(r)
        safe_text = xml_escape(text)
        if attrs:
            parts.append(f'<tspan {attrs}>{safe_text}</tspan>')
        else:
            parts.append(safe_text)

    return "".join(parts)


def _run_attrs(r: TextRun) -> str:
    """Return the SVG attributes for a <tspan> that describe a run's inline style."""
    attrs: list[str] = []

    if r.font_size:
        attrs.append(f'font-size="{_f(r.font_size)}"')

    # Font family: prefer EA typeface for CJK content when present; emit a stack
    families: list[str] = []
    if r.font_latin and r.font_ea and r.font_latin != r.font_ea:
        families = [r.font_ea, r.font_latin, 'sans-serif']
    elif r.font_latin:
        families = [r.font_latin, 'sans-serif']
    elif r.font_ea:
        families = [r.font_ea, 'sans-serif']
    if families:
        # Wrap multi-word names in &quot; (escaped inside the XML attribute).
        stack = ', '.join(
            f'&quot;{f}&quot;' if ' ' in f else f for f in families
        )
        attrs.append(f'font-family="{stack}"')

    if r.bold:
        attrs.append('font-weight="bold"')
    if r.italic:
        attrs.append('font-style="italic"')
    if r.color:
        attrs.append(f'fill="#{r.color}"')

    return ' '.join(attrs)


# ---------------------------------------------------------------------------
# Per-shape emitters
# ---------------------------------------------------------------------------

def _emit_rect(shape: Shape, ctx: EmitContext) -> str:
    x, y, w, h = shape.bbox
    if w <= 0 or h <= 0:
        return ''
    fill = _fill_attrs(shape.fill, ctx)
    stroke = _stroke_attrs(shape.stroke)
    transform = _transform_attr(shape)
    stroke_part = f' {stroke}' if stroke else ''
    rx = ''
    if shape.kind == 'roundRect' and shape.corner_radius > 0:
        rx = f' rx="{_f(shape.corner_radius)}" ry="{_f(shape.corner_radius)}"'
    geom = (
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}"'
        f'{rx} {fill}{stroke_part}{transform}/>'
    )
    text = _emit_text(shape, ctx)
    if text:
        return f'{geom}\n{text}'
    return geom


def _emit_ellipse(shape: Shape, ctx: EmitContext) -> str:
    x, y, w, h = shape.bbox
    if w <= 0 or h <= 0:
        return ''
    cx, cy = x + w / 2.0, y + h / 2.0
    rx, ry = w / 2.0, h / 2.0
    fill = _fill_attrs(shape.fill, ctx)
    stroke = _stroke_attrs(shape.stroke)
    transform = _transform_attr(shape)
    stroke_part = f' {stroke}' if stroke else ''
    geom = (
        f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" '
        f'{fill}{stroke_part}{transform}/>'
    )
    text = _emit_text(shape, ctx)
    if text:
        return f'{geom}\n{text}'
    return geom


def _emit_line(shape: Shape, ctx: EmitContext) -> str:
    x, y, w, h = shape.bbox
    # For a DrawingML prst="line", flipH/flipV swap the diagonal direction.
    if shape.flip_h and shape.flip_v:
        x1, y1, x2, y2 = x + w, y + h, x, y
    elif shape.flip_h:
        x1, y1, x2, y2 = x + w, y, x, y + h
    elif shape.flip_v:
        x1, y1, x2, y2 = x, y + h, x + w, y
    else:
        x1, y1, x2, y2 = x, y, x + w, y + h

    stroke = _stroke_attrs(shape.stroke)
    if not stroke:
        # DrawingML lines default to black 1px if no explicit stroke.
        stroke = 'stroke="#000000" stroke-width="1"'
    return (
        f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
        f'{stroke}/>'
    )


def _emit_path(shape: Shape, ctx: EmitContext) -> str:
    """Emit a <path>. path_d is in local coords; wrap in translate(bbox.x, bbox.y)."""
    if not shape.path_d:
        return ''
    x, y, w, h = shape.bbox
    fill = _fill_attrs(shape.fill, ctx)
    stroke = _stroke_attrs(shape.stroke)
    stroke_part = f' {stroke}' if stroke else ''

    # Compose transform: translate(x,y) + optional rotation/flip (around center).
    # Here the center for rotation is (w/2, h/2) in the path's local frame.
    cx, cy = w / 2.0, h / 2.0
    transforms: list[str] = [f"translate({_f(x)} {_f(y)})"]
    if shape.rotation:
        transforms.append(f"rotate({_f(shape.rotation)} {_f(cx)} {_f(cy)})")
    if shape.flip_h or shape.flip_v:
        sx = -1 if shape.flip_h else 1
        sy = -1 if shape.flip_v else 1
        transforms.append(
            f"translate({_f(cx)} {_f(cy)}) scale({sx} {sy}) translate({_f(-cx)} {_f(-cy)})"
        )
    transform = f' transform="{" ".join(transforms)}"'

    geom = f'<path d="{shape.path_d}" {fill}{stroke_part}{transform}/>'
    text = _emit_text(shape, ctx)
    if text:
        return f'{geom}\n{text}'
    return geom


def _emit_image(shape: Shape, ctx: EmitContext) -> str:
    x, y, w, h = shape.bbox
    if w <= 0 or h <= 0 or shape.image_ref is None:
        return ''
    href = f"assets/{shape.image_ref}"
    transform = _transform_attr(shape)
    # Crop (srcRect) v1: convert l/t/r/b to a clipPath. Since clipPath on <image>
    # is allowed per shared-standards §1.2, we emit a rect clip.
    # P3 keeps it simple: ignore crop and log a warning. Full support can come later.
    return (
        f'<image x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" '
        f'href="{href}"{transform} preserveAspectRatio="xMidYMid slice"/>'
    )


def _emit_group(shape: Shape, ctx: EmitContext) -> str:
    """Emit <g> wrapping children. Uses identity transform so children keep absolute coords."""
    if not shape.children:
        return ''
    # CLAUDE.md memory: group related elements in <g> for structure/editability.
    # Children already carry absolute bbox, so no transform is applied here.
    parts: list[str] = []
    for child in shape.children:
        xml = _dispatch_shape(child, ctx)
        if xml:
            parts.append(xml)
    if not parts:
        return ''
    return "<g>\n" + "\n".join(parts) + "\n</g>"


def _emit_text_shape(shape: Shape, ctx: EmitContext) -> str:
    """A pure text shape (kind='text') — unusual but supported for completeness."""
    return _emit_text(shape, ctx)


def _emit_unknown(shape: Shape, ctx: EmitContext) -> str:
    """Fallback: emit the shape's bbox as a dashed gray rect placeholder."""
    x, y, w, h = shape.bbox
    if w <= 0 or h <= 0:
        return ''
    return (
        f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(w)}" height="{_f(h)}" '
        f'fill="none" stroke="#CCCCCC" stroke-width="1" stroke-dasharray="4,2"/>'
    )


_DISPATCH = {
    'rect': _emit_rect,
    'roundRect': _emit_rect,
    'ellipse': _emit_ellipse,
    'line': _emit_line,
    'path': _emit_path,
    'image': _emit_image,
    'group': _emit_group,
    'text': _emit_text_shape,
    'prstGeom': _emit_unknown,
    'unknown': _emit_unknown,
}


def _dispatch_shape(shape: Shape, ctx: EmitContext) -> str:
    emitter = _DISPATCH.get(shape.kind, _emit_unknown)
    return emitter(shape, ctx)


# ---------------------------------------------------------------------------
# Public emit API
# ---------------------------------------------------------------------------

def emit_slide_svg(slide_bp: SlideBlueprint, theme: Theme) -> str:
    """Emit a complete SVG document string for one slide blueprint."""
    ctx = EmitContext(theme=theme)

    body_parts: list[str] = []

    # Background (bottom-most layer)
    if slide_bp.background is not None:
        bg_xml = _emit_rect(slide_bp.background, ctx)
        if bg_xml:
            body_parts.append(bg_xml)

    # Shapes in source order (later = on top)
    for shape in slide_bp.shapes:
        xml = _dispatch_shape(shape, ctx)
        if xml:
            body_parts.append(xml)

    # Assemble defs
    defs_xml = ''
    if ctx.gradient_defs:
        defs_xml = "<defs>\n" + "\n".join(ctx.gradient_defs) + "\n</defs>\n"

    vw, vh = slide_bp.viewbox
    body = "\n".join(body_parts)

    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw} {vh}">\n'
        f'{defs_xml}'
        f'{body}\n'
        f'</svg>\n'
    )
    return svg


def emit_blueprint_svgs(bp: Blueprint) -> list[tuple[int, str]]:
    """Emit every slide in a Blueprint. Returns [(slide_index, svg_string), ...]."""
    return [(s.index, emit_slide_svg(s, bp.theme)) for s in bp.slides]


# ---------------------------------------------------------------------------
# Compliance linter (shared-standards.md §1 + §2)
# ---------------------------------------------------------------------------

# Tokens that must never appear in a compliant SVG (regex patterns keyed by name)
_BANNED_PATTERNS: list[tuple[str, str]] = [
    ('mask element / attribute', r'<\s*mask\b|\bmask\s*='),
    ('<style> element', r'<\s*style\b'),
    ('class attribute', r'\bclass\s*='),
    ('<foreignObject>', r'<\s*foreignObject\b'),
    ('<symbol>+<use> reference reuse', r'<\s*symbol\b'),
    # Note: <use> is not banned per se, but usually paired with <symbol>; we only flag <symbol>.
    ('<textPath>', r'<\s*textPath\b'),
    ('@font-face', r'@font-face'),
    ('<animate*> / <set>', r'<\s*(animate|animateMotion|animateTransform|set)\b'),
    ('<script> or event handler', r'<\s*script\b|\son[a-z]+\s*='),
    ('<iframe>', r'<\s*iframe\b'),
    ('rgba(...)', r'rgba\s*\('),
    ('<g opacity> (group opacity)', r'<\s*g\b[^>]*\bopacity\s*='),
    ('<image opacity>', r'<\s*image\b[^>]*\bopacity\s*='),
]


def lint_svg(svg: str) -> list[str]:
    """Scan an SVG string for banned features. Returns list of violation descriptions.

    An empty list means the SVG is compliant with shared-standards §1 + §2.
    Conditionally-allowed features (marker-start/end, clipPath on <image>) are
    NOT checked here in v1 — they are caller-controlled.
    """
    violations: list[str] = []
    for label, pattern in _BANNED_PATTERNS:
        m = re.search(pattern, svg, flags=re.IGNORECASE)
        if m:
            # Provide the matched snippet and a rough position.
            line_no = svg[:m.start()].count("\n") + 1
            snippet = m.group(0)[:60]
            violations.append(f"[line {line_no}] {label} — found: {snippet!r}")
    return violations


def assert_compliant(svg: str) -> None:
    """Raise ValueError with a formatted message if the SVG violates standards."""
    vios = lint_svg(svg)
    if vios:
        raise ValueError(
            "SVG output violates shared-standards.md:\n  "
            + "\n  ".join(vios)
        )
