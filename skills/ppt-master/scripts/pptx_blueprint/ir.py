"""Blueprint IR — the intermediate representation between PPTX and SVG.

All coordinates in Blueprint are in viewBox pixel units (not EMU).
The parser (xml_parser.py) converts EMU -> px via EMU_PER_PX = 9525 (96 dpi).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# ---------------------------------------------------------------------------
# Theme (colors + fonts resolved once per PPTX)
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    """Resolved color scheme and font scheme from theme/theme1.xml.

    Colors are stored as 6-char hex without leading '#'.
    The clr_map records how scheme slots (bg1/tx1/...) map to actual
    accents, so schemeClr references can be resolved uniformly.
    """

    colors: dict[str, str] = field(default_factory=dict)
    # accent1..accent6, lt1, lt2, dk1, dk2, hlink, folHlink
    fonts: dict[str, str] = field(default_factory=dict)
    # majorLatin, majorEastAsia, minorLatin, minorEastAsia
    clr_map: dict[str, str] = field(default_factory=dict)
    # bg1 -> lt1, tx1 -> dk1, ...

    def resolve_scheme_color(self, scheme_name: str) -> str | None:
        """Resolve a schemeClr val (e.g. 'accent1', 'bg1') to a hex color."""
        mapped = self.clr_map.get(scheme_name, scheme_name)
        color = self.colors.get(mapped)
        if color is None and mapped != scheme_name:
            color = self.colors.get(scheme_name)
        return color


# ---------------------------------------------------------------------------
# Paint: solid fill, gradient, stroke
# ---------------------------------------------------------------------------

@dataclass
class GradientStop:
    """A single color stop in a gradient."""
    pos: float  # 0.0 - 1.0
    color: str  # 6-char hex
    opacity: float = 1.0


@dataclass
class GradientSpec:
    """Linear or radial gradient spec. Kept simple for v1."""
    kind: Literal['linear', 'radial'] = 'linear'
    stops: list[GradientStop] = field(default_factory=list)
    angle_deg: float = 0.0  # linear only; 0 = left to right


@dataclass
class Fill:
    """Shape fill paint."""
    kind: Literal['solid', 'gradient', 'none', 'image'] = 'none'
    color: str | None = None  # for solid; 6-char hex
    opacity: float = 1.0
    gradient: GradientSpec | None = None
    image_ref: str | None = None  # for kind='image'; asset filename


@dataclass
class Stroke:
    """Shape stroke paint."""
    color: str | None = None  # 6-char hex
    width: float = 1.0  # px
    opacity: float = 1.0
    dash: Literal['solid', 'dash', 'dot', 'dashDot', 'lgDash'] | None = None
    cap: Literal['flat', 'rnd', 'sq'] = 'flat'


# ---------------------------------------------------------------------------
# Text (run/paragraph model — DrawingML natively uses this)
# ---------------------------------------------------------------------------

@dataclass
class TextRun:
    """A text run with inline style."""
    text: str
    font_size: float | None = None  # pt; None = inherit from paragraph/placeholder
    font_latin: str | None = None
    font_ea: str | None = None  # East Asian (CJK) typeface
    bold: bool = False
    italic: bool = False
    color: str | None = None  # 6-char hex; None = inherit


@dataclass
class TextParagraph:
    """A paragraph within a text body."""
    runs: list[TextRun] = field(default_factory=list)
    align: Literal['l', 'ctr', 'r', 'just'] = 'l'
    bullet: str | None = None  # None = no bullet; '•' / '1.' / etc.
    indent_px: float = 0.0
    line_spacing_pct: float = 100.0  # 100 = single line


@dataclass
class TextContent:
    """Text content of a shape (corresponds to <p:txBody>)."""
    paragraphs: list[TextParagraph] = field(default_factory=list)
    anchor: Literal['t', 'ctr', 'b'] = 't'
    auto_fit: bool = False  # normAutofit — body scales font to fit


# ---------------------------------------------------------------------------
# Shape tree (Shape + recursive group)
# ---------------------------------------------------------------------------

ShapeKind = Literal[
    'rect', 'roundRect', 'ellipse', 'line', 'path',
    'text', 'image', 'group', 'prstGeom', 'unknown',
]


@dataclass
class Shape:
    """One shape in a slide. Coordinates in viewBox pixels (post-EMU conversion).

    For kind='prstGeom', `preset_name` carries the preset identifier
    (e.g. 'rect' / 'roundRect' / 'chevron'); the SVG emitter dispatches
    via prstgeom_registry. avLst parameters (if any) are stored in
    `preset_avlst` for presets that use adjust values.

    For kind='group', child shapes are in `children`.
    """
    kind: ShapeKind
    bbox: tuple[float, float, float, float]  # x, y, w, h in viewBox px
    rotation: float = 0.0  # degrees clockwise
    flip_h: bool = False
    flip_v: bool = False

    fill: Fill | None = None
    stroke: Stroke | None = None
    opacity: float = 1.0

    # geometry-dependent
    preset_name: str | None = None  # for prstGeom
    preset_avlst: dict[str, int] = field(default_factory=dict)
    path_d: str | None = None  # for kind='path' (custGeom already SVG-ified)
    corner_radius: float = 0.0  # for roundRect

    # content-dependent
    text: TextContent | None = None
    image_ref: str | None = None  # asset filename (for kind='image')
    image_crop: tuple[float, float, float, float] | None = None  # srcRect l/t/r/b (0-1)

    # grouping
    children: list['Shape'] = field(default_factory=list)

    # placeholder semantics (set by placeholder_tagger.py; None means unknown)
    ph_type: str | None = None  # title/body/subTitle/pic/dt/sldNum/ctrTitle/...
    ph_idx: int | None = None
    placeholder_tag: str | None = None  # {{TITLE}} / {{PAGE_TITLE}} / etc.

    # provenance (debug aid; filled during parsing)
    source_id: str | None = None  # PPTX <p:cNvPr id=...>
    source_name: str | None = None  # PPTX <p:cNvPr name=...>


# ---------------------------------------------------------------------------
# Slide + Blueprint (root)
# ---------------------------------------------------------------------------

PageType = Literal['cover', 'toc', 'chapter', 'content', 'ending', 'unknown']


@dataclass
class SlideBlueprint:
    """One slide's extracted layout, post-inheritance-flattening."""
    index: int  # 1-based, slide order in presentation
    viewbox: tuple[int, int]  # (width_px, height_px)
    page_type: PageType = 'unknown'

    background: Shape | None = None  # resolved background (layer behind spTree)
    shapes: list[Shape] = field(default_factory=list)

    # raw metadata preserved for downstream classification
    layout_name: str | None = None
    text_samples: list[str] = field(default_factory=list)

    # layout fingerprint (filled by page_classifier in P4)
    fingerprint: dict[str, float | int | str] = field(default_factory=dict)
    cluster_id: int | None = None


@dataclass
class Blueprint:
    """Root container: everything extracted from a single PPTX."""
    source_pptx: Path
    viewbox: tuple[int, int]  # slide size, e.g. (1280, 720)
    theme: Theme = field(default_factory=Theme)

    slides: list[SlideBlueprint] = field(default_factory=list)

    # assets copied out of ppt/media/ (maps original zip path -> on-disk path)
    assets: dict[str, Path] = field(default_factory=dict)

    # warnings accumulated during parse (non-fatal: unknown prstGeom, etc.)
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Unit conversion constants (public — shared across the package)
# ---------------------------------------------------------------------------

EMU_PER_INCH = 914400
DEFAULT_DPI = 96
EMU_PER_PX = EMU_PER_INCH // DEFAULT_DPI  # 9525

# DrawingML font size unit is 1/100 of a point (e.g. 1200 = 12pt)
DML_FONT_UNIT = 100.0

# DrawingML angle unit is 1/60000 of a degree (e.g. 5400000 = 90°)
DML_ANGLE_UNIT = 60000.0


def emu_to_px(emu: int) -> float:
    """Convert EMU to pixels at 96 dpi."""
    return emu / EMU_PER_PX


def dml_font_size_to_pt(sz: int) -> float:
    """Convert DrawingML sz attribute (1/100 pt) to points."""
    return sz / DML_FONT_UNIT


def dml_angle_to_deg(ang: int) -> float:
    """Convert DrawingML rotation (1/60000 deg) to degrees."""
    return ang / DML_ANGLE_UNIT
