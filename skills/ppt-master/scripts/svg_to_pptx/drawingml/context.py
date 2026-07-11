"""ConvertContext — shared state passed through the SVG → DrawingML pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .theme_colors import ThemeColorSpec
    from .theme_fonts import ThemeFontSpec

AffineMatrix = tuple[float, float, float, float, float, float]
IDENTITY_MATRIX: AffineMatrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


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
    # Imported PPTX shape ids are reserved before conversion so newly authored
    # SVG elements cannot steal an id referenced by a native connector.
    reserved_shape_ids: frozenset[int] = frozenset()
    source_shape_id_map: dict[tuple[str, str], int] = field(default_factory=dict)
    claimed_shape_ids: set[int] = field(default_factory=set)
    referenced_shape_ids: set[int] = field(default_factory=set)
    slide_num: int = 1
    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    viewport_width: float = 1280.0
    viewport_height: float = 720.0
    transform_matrix: AffineMatrix = IDENTITY_MATRIX
    use_transform_matrix: bool = False
    filter_id: str | None = None
    media_files: dict[str, bytes] = field(default_factory=dict)
    rel_entries: list[dict[str, str]] = field(default_factory=list)
    package_files: dict[str, bytes] = field(default_factory=dict)
    content_type_overrides: dict[str, str] = field(default_factory=dict)
    rel_id_counter: int = 2  # rId1 reserved for slideLayout
    svg_dir: Path | None = None
    inherited_styles: dict[str, str] = field(default_factory=dict)
    # SVG group opacity is post-compositing, not an inherited presentation
    # property. DrawingML has no equivalent group alpha, so native export
    # approximates it by multiplying this value into each descendant object.
    opacity_multiplier: float = 1.0
    # Recursion depth — only the depth==0 (root) context records anim targets.
    depth: int = 0
    # Top-level <g id="..."> groups, recorded as (shape_id, svg_id) in z-order.
    # Used by the PPTX builder to emit per-element entrance timing.
    anim_targets: list = field(default_factory=list)
    # Explicit sidecar group ids may override the legacy chrome-name heuristic.
    # Explicit structural layer/role/placeholder markers remain non-animatable.
    animation_group_overrides: frozenset[str] = frozenset()
    # Default-on flag: merge mergeable paragraph blocks into one editable
    # text frame with multiple <a:p>. Disable it for strict line fidelity.
    merge_paragraphs: bool = True
    # Explicit opt-in: convert data-pptx-native table/chart marker groups to
    # native PowerPoint graphicFrames. Default stays off to preserve SVG output.
    native_objects_enabled: bool = False
    # Native PPTX image optimization. Keeps generated decks compact by
    # downsampling oversized raster assets to their rendered size.
    image_optimize: bool = True
    image_max_dimension: int | None = 2560
    image_sizing: str = 'cap'
    image_scale: float = 2.0
    image_quality: int = 85
    # Optional per-element conversion diagnostics. Shared by child contexts so
    # callers can inspect native / skipped / unsupported decisions per slide.
    trace_events: list[dict[str, Any]] | None = None
    # Optional project theme contract. Matching SVG title/body families emit
    # DrawingML +mj/+mn tokens instead of fixed typeface names.
    theme_font_spec: ThemeFontSpec | None = None
    # Optional project theme-color contract. Exact locked colors are promoted
    # to context-safe DrawingML scheme slots while local colors stay concrete.
    theme_color_spec: ThemeColorSpec | None = None

    def next_id(self) -> int:
        """Allocate the next shape ID."""
        cid = self.id_counter
        while cid in self.reserved_shape_ids or cid in self.claimed_shape_ids:
            cid += 1
        self.id_counter = cid + 1
        self.claimed_shape_ids.add(cid)
        return cid

    def claim_shape_id(
        self,
        source_id: str | None,
        source_scope: str | None = None,
    ) -> int:
        """Claim a pre-reserved imported shape id, or allocate a fresh one."""
        if source_id is None:
            return self.next_id()
        scope = source_scope or 'slide'
        key = (scope, source_id)
        shape_id = self.source_shape_id_map.get(key)
        if shape_id is None:
            raise ValueError(
                f'Unreserved data-pptx-shape-id {source_id!r} in scope {scope!r}'
            )
        if shape_id in self.claimed_shape_ids:
            raise ValueError(
                f'Duplicate data-pptx-shape-id {source_id!r} in scope {scope!r}'
            )
        self.claimed_shape_ids.add(shape_id)
        return shape_id

    def reference_shape_id(
        self,
        source_id: str,
        source_scope: str | None = None,
    ) -> int:
        """Resolve and record a connector target in the imported id space."""
        scope = source_scope or 'slide'
        shape_id = self.source_shape_id_map.get((scope, source_id))
        if shape_id is None:
            raise ValueError(
                f'Unknown connector shape reference {source_id!r} in scope {scope!r}'
            )
        self.referenced_shape_ids.add(shape_id)
        return shape_id

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
        transform_matrix: AffineMatrix | None = None,
        filter_id: str | None = None,
        style_overrides: dict[str, str] | None = None,
        opacity_multiplier: float = 1.0,
    ) -> ConvertContext:
        """Create a child context with accumulated translate / scale / styles.

        Args:
            dx: X translation delta.
            dy: Y translation delta.
            sx: X scale factor.
            sy: Y scale factor.
            transform_matrix: Full affine transform to accumulate for
                converters that can faithfully map it to DrawingML.
            filter_id: Override filter ID.
            style_overrides: Style attribute overrides from child element.
            opacity_multiplier: Local group opacity to multiply into descendants.
        """
        local_matrix = transform_matrix or IDENTITY_MATRIX
        # When first crossing from scalar to matrix mode, fold accumulated
        # translate_x/y and scale_x/y into the matrix base. Otherwise the
        # ancestor's scalar transform — which matrix-path readers (e.g.
        # <image>) never look at — is silently lost, and the descendant
        # lands at raw SVG coordinates (typically near (0,0)).
        if transform_matrix is not None and not self.use_transform_matrix:
            base_matrix: AffineMatrix = (
                self.scale_x, 0.0,
                0.0, self.scale_y,
                self.translate_x, self.translate_y,
            )
        else:
            base_matrix = self.transform_matrix
        a1, b1, c1, d1, e1, f1 = base_matrix
        a2, b2, c2, d2, e2, f2 = local_matrix
        combined_matrix: AffineMatrix = (
            a1 * a2 + c1 * b2,
            b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2,
            b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1,
            b1 * e2 + d1 * f2 + f1,
        )

        merged = dict(self.inherited_styles)
        if style_overrides:
            merged.update(style_overrides)

        local_opacity = max(0.0, min(1.0, opacity_multiplier))

        return ConvertContext(
            defs=self.defs,
            id_counter=self.id_counter,
            reserved_shape_ids=self.reserved_shape_ids,
            source_shape_id_map=self.source_shape_id_map,
            claimed_shape_ids=self.claimed_shape_ids,
            referenced_shape_ids=self.referenced_shape_ids,
            slide_num=self.slide_num,
            translate_x=self.translate_x + dx,
            translate_y=self.translate_y + dy,
            scale_x=self.scale_x * sx,
            scale_y=self.scale_y * sy,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            transform_matrix=combined_matrix,
            use_transform_matrix=self.use_transform_matrix or transform_matrix is not None,
            filter_id=filter_id or self.filter_id,
            media_files=self.media_files,
            rel_entries=self.rel_entries,
            package_files=self.package_files,
            content_type_overrides=self.content_type_overrides,
            rel_id_counter=self.rel_id_counter,
            svg_dir=self.svg_dir,
            inherited_styles=merged,
            opacity_multiplier=self.opacity_multiplier * local_opacity,
            depth=self.depth + 1,
            # anim_targets is intentionally a fresh list on the child;
            # only the root-level context's list is read by the builder.
            animation_group_overrides=self.animation_group_overrides,
            merge_paragraphs=self.merge_paragraphs,
            native_objects_enabled=self.native_objects_enabled,
            image_optimize=self.image_optimize,
            image_max_dimension=self.image_max_dimension,
            image_sizing=self.image_sizing,
            image_scale=self.image_scale,
            image_quality=self.image_quality,
            trace_events=self.trace_events,
            theme_font_spec=self.theme_font_spec,
            theme_color_spec=self.theme_color_spec,
        )

    def sync_from_child(self, child_ctx: ConvertContext) -> None:
        """Sync counters back from a child context."""
        self.id_counter = child_ctx.id_counter
        self.rel_id_counter = child_ctx.rel_id_counter
