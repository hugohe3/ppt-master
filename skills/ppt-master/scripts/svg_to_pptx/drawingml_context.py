"""ConvertContext — shared state passed through the SVG → DrawingML pipeline."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class ShapeResult:
    """Internal conversion result carrying XML plus resolved EMU bounds."""

    xml: str
    bounds_emu: tuple[int, int, int, int] | None = None


@dataclass
class ConvertContext:
    """Shared context passed through the SVG → DrawingML conversion pipeline.

    Derived via child() during recursive SVG tree traversal to accumulate
    translate / scale / inherited style information.
    """

    defs: dict[str, ET.Element] = field(default_factory=dict)
    id_counter: int = 2  # 1 is reserved for spTree root
    slide_num: int = 1
    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    filter_id: str | None = None
    media_files: dict[str, bytes] = field(default_factory=dict)
    rel_entries: list[dict[str, str]] = field(default_factory=list)
    rel_id_counter: int = 2  # rId1 reserved for slideLayout
    svg_dir: Path | None = None
    inherited_styles: dict[str, str] = field(default_factory=dict)
    # Recursion depth — only the depth==0 (root) context records anim targets.
    depth: int = 0
    # Top-level <g id="..."> groups, recorded as (shape_id, svg_id) in z-order.
    # Used by the PPTX builder to emit per-element entrance timing.
    anim_targets: list = field(default_factory=list)

    def next_id(self) -> int:
        """Allocate the next shape ID."""
        cid = self.id_counter
        self.id_counter += 1
        return cid

    def next_rel_id(self) -> str:
        """Allocate the next relationship ID (rIdN)."""
        rid = f'rId{self.rel_id_counter}'
        self.rel_id_counter += 1
        return rid

    def child(
        self,
        dx: float = 0,
        dy: float = 0,
        sx: float = 1.0,
        sy: float = 1.0,
        filter_id: str | None = None,
        style_overrides: dict[str, str] | None = None,
    ) -> ConvertContext:
        """Create a child context with accumulated translate / scale / styles.

        Args:
            dx: X translation delta.
            dy: Y translation delta.
            sx: X scale factor.
            sy: Y scale factor.
            filter_id: Override filter ID.
            style_overrides: Style attribute overrides from child element.
        """
        merged = dict(self.inherited_styles)

        if style_overrides:
            # Opacity is multiplicative, not a simple override
            _OPACITY_KEYS = ('opacity', 'fill-opacity', 'stroke-opacity')
            for op_key in _OPACITY_KEYS:
                if op_key in style_overrides and op_key in merged:
                    try:
                        merged[op_key] = str(
                            float(merged[op_key]) * float(style_overrides[op_key])
                        )
                    except ValueError:
                        merged[op_key] = style_overrides[op_key]
                elif op_key in style_overrides:
                    merged[op_key] = style_overrides[op_key]

            for k, v in style_overrides.items():
                if k not in _OPACITY_KEYS:
                    merged[k] = v

        return ConvertContext(
            defs=self.defs,
            id_counter=self.id_counter,
            slide_num=self.slide_num,
            translate_x=self.translate_x + dx,
            translate_y=self.translate_y + dy,
            scale_x=self.scale_x * sx,
            scale_y=self.scale_y * sy,
            filter_id=filter_id or self.filter_id,
            media_files=self.media_files,
            rel_entries=self.rel_entries,
            rel_id_counter=self.rel_id_counter,
            svg_dir=self.svg_dir,
            inherited_styles=merged,
            depth=self.depth + 1,
            # anim_targets is intentionally a fresh list on the child;
            # only the root-level context's list is read by the builder.
        )

    def sync_from_child(self, child_ctx: ConvertContext) -> None:
        """Sync counters back from a child context."""
        self.id_counter = child_ctx.id_counter
        self.rel_id_counter = child_ctx.rel_id_counter
