"""Per-slide composition: dispatches every ShapeNode through the right
converter, accumulates <defs>, and produces one final SVG string.

The output structure mirrors what svg_to_pptx expects so the deck can be
round-tripped:
    <svg viewBox="0 0 W H">
        <defs>
            <linearGradient id=.../>
            <marker id=.../>
            <filter id=.../>
        </defs>
        <!-- background -->
        <rect ... />        (slide background, if any)
        <g id="shape-1">...</g>
        <g id="shape-2">...</g>
        ...
    </svg>

Each top-level <g> wraps one shape and is treated by svg_to_pptx as an
animation anchor.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import posixpath
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from pptx_shapes import (
    CONNECTOR_PRESET_TYPES,
    NATIVE_FALLBACK_SHA256_ATTR,
    has_relationship_attributes,
    svg_native_fallback_markup_fingerprint,
    svg_text_fingerprint,
)
from pptx_effects import (
    EFFECT_REASON_ATTR,
    EFFECT_STATUS_ATTR,
    NATIVE_EFFECT_ATTR,
    NATIVE_EFFECT_SHA256_ATTR,
    txbody_has_run_effects,
    unsupported_effect_metadata,
)
from hyperlink_contract import SHAPE_HYPERLINK_ATTR
from svg_to_pptx.drawingml.paths import (
    PathCommand,
    normalize_path_commands,
    parse_svg_path,
    parse_svg_points,
    svg_path_to_absolute,
    transform_path_commands,
)

from .color_resolver import ColorPalette, find_color_elem, resolve_color
from .chart_to_svg import CHART_URI, CHARTEX_URI, extract_native_chart_payload
from .custgeom_to_svg import convert_custom_geom
from .effect_to_svg import (
    EffectResult,
    convert_effects,
    unsupported_target_effect_metadata,
)
from .emu_units import NS, Xfrm, fmt_num, format_canvas_px_from_emu
from .fill_to_svg import FillResult, resolve_fill
from .formula_import import (
    A14_NS,
    FormulaImport,
    FormulaImportError,
    import_formula,
    opaque_formula_preview,
)
from .import_diagnostics import (
    ImportDiagnostic,
    append_diagnostic,
)
from .hyperlinks import resolve_click_hyperlink
from .ln_to_svg import StrokeResult, resolve_stroke
from .ooxml_loader import (
    OoxmlPackage,
    PartRef,
    SlideRef,
    inherited_shape_visibility,
)
from .pic_to_svg import (
    LinkedImageResolutionError,
    MediaResolutionError,
    PictureResult,
    convert_blip_fill,
    convert_picture,
)
from .prstgeom_to_svg import GeomResult, convert_prst_geom
from .preset_svg_markup import serialize_preset_layers
from .shape_walker import (
    CONNECTOR, GRAPHIC, GROUP, PICTURE, SHAPE,
    ShapeNode, get_background, walk_sp_tree,
)
from .tbl_to_svg import convert_tbl
from .txbody_to_svg import (
    TextResult,
    convert_txbody,
    convert_vertical_txbody,
    is_vertical_txbody,
    DEFAULT_FONT_SIZE_PX,
)


# ---------------------------------------------------------------------------
# AssemblyContext
# ---------------------------------------------------------------------------

_SOURCE_PROXY_ATTRIBUTE = "data-pptx-source-proxy"
_SOURCE_PROXY_KIND = "native-restore"
_EXTERNAL_LINKED_IMAGE_PROXY_ATTRIBUTE = (
    "data-pptx-external-linked-image-proxy"
)

@dataclass
class AssemblyContext:
    """Per-slide accumulator for unique IDs + media + defs."""

    palette: ColorPalette | None
    pkg: OoxmlPackage
    slide_part: PartRef
    slide_number: int | None = None
    theme_fonts: dict[str, str] = field(default_factory=dict)
    media_subdir: str = "images"
    embed_images: bool = False
    keep_hidden: bool = False
    strict: bool = False
    group_id_prefix: str = ""
    render_graphic_previews: bool = True
    preserve_placeholder_inheritance: bool = False
    asset_name_map: dict[str, str] = field(default_factory=dict)
    diagnostics: list[ImportDiagnostic] = field(default_factory=list)
    source_slide_index: int | None = None
    current_node: ShapeNode | None = None

    # Sequence counters (single-element lists so handlers can mutate)
    grad_seq: list[int] = field(default_factory=lambda: [0])
    marker_seq: list[int] = field(default_factory=lambda: [0])
    filter_seq: list[int] = field(default_factory=lambda: [0])
    shape_seq: list[int] = field(default_factory=lambda: [0])
    clip_seq: list[int] = field(default_factory=lambda: [0])

    # Accumulated outputs
    defs: list[str] = field(default_factory=list)
    media: dict[str, bytes] = field(default_factory=dict)
    group_fills: list[FillResult | None] = field(default_factory=list)

    def bind_palette(self) -> None:
        """Route tolerant color diagnostics through the current object context."""
        if self.palette is None:
            return
        self.palette.strict = self.strict
        self.palette.diagnostic_sink = self._diagnose_color

    def diagnose(
        self,
        code: str,
        message: str,
        fallback: str,
        *,
        node: ShapeNode | None = None,
    ) -> None:
        """Record one recoverable source-contract violation."""
        source_node = node or self.current_node
        append_diagnostic(
            self.diagnostics,
            ImportDiagnostic(
                code=code,
                message=message,
                fallback=fallback,
                part_path=self.slide_part.path,
                slide_index=self.source_slide_index,
                shape_id=source_node.spid if source_node is not None else "",
                shape_name=source_node.name if source_node is not None else "",
                shape_kind=source_node.kind if source_node is not None else "",
            ),
        )

    def _diagnose_color(self, code: str, message: str, fallback: str) -> None:
        self.diagnose(code, message, fallback)


def _diagnose_picture_result(
    ctx: AssemblyContext,
    result: PictureResult,
) -> None:
    """Project recoverable picture losses into the import report."""
    for diagnostic in result.diagnostics:
        ctx.diagnose(
            diagnostic.code,
            diagnostic.message,
            diagnostic.fallback,
        )


def _resolve_svg_hyperlink(
    ctx: AssemblyContext,
    relationship_id: str,
    action: str,
) -> str | None:
    """Resolve one source-part click link or record its explicit loss."""
    resolution = resolve_click_hyperlink(
        ctx.slide_part.rels,
        relationship_id,
        action,
        slide_index_by_part=ctx.pkg.slide_index_by_part,
    )
    if resolution.error is None:
        return resolution.href
    if ctx.strict:
        raise ValueError(resolution.error)
    ctx.diagnose(
        "hyperlink-omitted",
        resolution.error,
        "retain the object and omit only its unsupported click link",
    )
    return None


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def assemble_slide(
    pkg: OoxmlPackage,
    slide: SlideRef,
    palette: ColorPalette | None,
    *,
    theme_fonts: dict[str, str] | None = None,
    media_subdir: str = "images",
    embed_images: bool = False,
    keep_hidden: bool = False,
    inheritance_mode: str = "flat",
    asset_name_map: dict[str, str] | None = None,
    strict: bool = False,
    diagnostics: list[ImportDiagnostic] | None = None,
    preserve_placeholder_inheritance: bool = False,
) -> tuple[str, dict[str, bytes]]:
    """Convert one slide to a complete SVG string + media files map.

    inheritance_mode controls how master/layout shapes are rendered:
        - "flat" (default): emit the effective visible Master/Layout
          non-placeholder shapes inline inside the slide SVG, honoring both
          source ``showMasterSp`` flags. This view is used for round-trip
          fidelity with svg_to_pptx.
        - "layered": skip inherited shapes entirely. The slide SVG contains
          only its own shapes. Callers (e.g. /create-template's PPTX import)
          render master/layout once each as separate SVGs and record the
          inheritance graph in inheritance.json.
    """
    ctx = AssemblyContext(
        palette=palette,
        pkg=pkg,
        slide_part=slide.part,
        slide_number=pkg.first_slide_number + slide.index - 1,
        theme_fonts=theme_fonts or {},
        media_subdir=media_subdir,
        embed_images=embed_images,
        keep_hidden=keep_hidden,
        strict=strict,
        render_graphic_previews=(inheritance_mode == "flat"),
        preserve_placeholder_inheritance=preserve_placeholder_inheritance,
        asset_name_map=asset_name_map or {},
        diagnostics=diagnostics if diagnostics is not None else [],
        source_slide_index=slide.index,
    )
    ctx.bind_palette()

    canvas_w, canvas_h = pkg.slide_size_px
    canvas_w_token, canvas_h_token = (
        format_canvas_px_from_emu(value) for value in pkg.slide_size_emu
    )

    # Background (cSld/bg) — emit as the first body element.
    body_parts: list[str] = []
    try:
        bg_xml = (
            _emit_background(slide, ctx, canvas_w, canvas_h)
            if inheritance_mode == "flat"
            else _emit_part_background(
                SlideRef(index=slide.index, part=slide.part, layout=None, master=slide.master),
                ctx, canvas_w, canvas_h,
            )
        )
    except (ValueError, MediaResolutionError) as exc:
        if strict:
            raise
        ctx.diagnose(
            "background-omitted",
            str(exc),
            "omit the unsupported background and continue the slide",
        )
        bg_xml = ""
    if bg_xml:
        body_parts.append(bg_xml)

    if inheritance_mode == "flat":
        # Inherited layout/master shapes render behind slide-local shapes. Skip
        # placeholders; they define editable regions, not visible background.
        body_parts.extend(_emit_inherited_shapes(slide, ctx))
    elif inheritance_mode != "layered":
        raise ValueError(
            f"inheritance_mode must be 'flat' or 'layered', got {inheritance_mode!r}"
        )

    # Walk shapes — placeholders without their own xfrm inherit geometry from
    # layout, then master.
    nodes = walk_sp_tree(
        slide.part.xml,
        layout_xml=slide.layout.xml if slide.layout else None,
        master_xml=slide.master.xml if slide.master else None,
    )
    for node in nodes:
        chunk = _convert_node(node, ctx, top_level=True)
        if chunk:
            body_parts.append(chunk)

    # Compose final SVG
    defs_xml = "".join(ctx.defs) if ctx.defs else ""
    defs_block = f"<defs>{defs_xml}</defs>" if defs_xml else ""

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
        f'width="{canvas_w_token}" height="{canvas_h_token}" '
        f'viewBox="0 0 {canvas_w_token} {canvas_h_token}">'
        f"{defs_block}"
        + "\n".join(body_parts)
        + "</svg>"
    )
    return svg, ctx.media


def assemble_part_solo(
    pkg: OoxmlPackage,
    part: PartRef,
    palette: ColorPalette | None,
    *,
    role: str,
    parent_master: PartRef | None = None,
    theme_fonts: dict[str, str] | None = None,
    media_subdir: str = "images",
    embed_images: bool = False,
    keep_hidden: bool = False,
    asset_name_map: dict[str, str] | None = None,
    strict: bool = False,
    diagnostics: list[ImportDiagnostic] | None = None,
) -> tuple[str, dict[str, bytes]]:
    """Render a single slideMaster or slideLayout part as a standalone SVG.

    Used by the layered export path. Skips placeholders the same way
    `_emit_inherited_shapes` does, so the output represents the part's
    decorative / structural shapes only — what the part *contributes* to its
    descendants. The first ancestor's background (if any) is emitted as the
    first body element so the output reads like a real slide.

    Args:
        role: 'master' or 'layout'. Used as the group_id_prefix to keep ids
            unique when the workspace inlines multiple parts in a viewer.
        parent_master: when ``role == "layout"``, pass the parent slide
            master so theme-style background fills (``<p:bgRef idx=...>``)
            can resolve via the theme attached to that master. For
            ``role == "master"`` the master is its own parent and this
            argument is ignored.
    """
    if role not in {"master", "layout"}:
        raise ValueError(f"role must be 'master' or 'layout', got {role!r}")

    ctx = AssemblyContext(
        palette=palette,
        pkg=pkg,
        slide_part=part,
        theme_fonts=theme_fonts or {},
        media_subdir=media_subdir,
        embed_images=embed_images,
        keep_hidden=keep_hidden,
        strict=strict,
        group_id_prefix=f"{role}-",
        render_graphic_previews=False,
        asset_name_map=asset_name_map or {},
        diagnostics=diagnostics if diagnostics is not None else [],
    )
    ctx.bind_palette()

    canvas_w, canvas_h = pkg.slide_size_px
    canvas_w_token, canvas_h_token = (
        format_canvas_px_from_emu(value) for value in pkg.slide_size_emu
    )

    body_parts: list[str] = []

    # Layered semantics: each part's standalone SVG must contain only that
    # part's own contribution. The master gets its own bg, the layout gets
    # its own bg only if it overrides the master's, and consumers re-stack
    # the layers when they need a flat view. We therefore inspect <p:bg> on
    # this part alone — never inherited from above. Theme-style fills
    # (<p:bgRef idx=...>) still need the parent master's <a:fmtScheme> to
    # resolve, hence the SlideRef.master plumbing below.
    if role == "master":
        master_for_theme: PartRef | None = part
    else:
        master_for_theme = parent_master
    fake_slide = SlideRef(
        index=0,
        part=part,
        layout=None,
        master=master_for_theme,
    )
    try:
        bg_xml = _emit_part_background(fake_slide, ctx, canvas_w, canvas_h)
    except (ValueError, MediaResolutionError) as exc:
        if strict:
            raise
        ctx.diagnose(
            "background-omitted",
            str(exc),
            "omit the unsupported background and continue the part",
        )
        bg_xml = ""
    if bg_xml:
        body_parts.append(bg_xml)

    # Walk shapes. Layered master/layout SVGs retain each placeholder's source
    # appearance so mirror materialization can recover its editable decoration.
    for node in walk_sp_tree(part.xml):
        if _is_placeholder_node(node):
            chunk = _convert_placeholder_guide(node, ctx, top_level=True)
        else:
            chunk = _convert_node(node, ctx, top_level=True)
        if chunk:
            body_parts.append(chunk)

    defs_xml = "".join(ctx.defs) if ctx.defs else ""
    defs_block = f"<defs>{defs_xml}</defs>" if defs_xml else ""

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" '
        f'width="{canvas_w_token}" height="{canvas_h_token}" '
        f'viewBox="0 0 {canvas_w_token} {canvas_h_token}">'
        f"{defs_block}"
        + "\n".join(body_parts)
        + "</svg>"
    )
    return svg, ctx.media


# ---------------------------------------------------------------------------
# Per-node dispatch
# ---------------------------------------------------------------------------

def _convert_node(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    previous_node = ctx.current_node
    ctx.current_node = node
    try:
        if node.hidden and not ctx.keep_hidden:
            return ""
        if node.kind == SHAPE:
            return _convert_shape(node, ctx, top_level=top_level)
        if node.kind == PICTURE:
            return _convert_picture(node, ctx, top_level=top_level)
        if node.kind == CONNECTOR:
            return _convert_connector(node, ctx, top_level=top_level)
        if node.kind == GROUP:
            return _convert_group(node, ctx, top_level=top_level)
        if node.kind == GRAPHIC:
            return _convert_graphic_fallback(node, ctx, top_level=top_level)
        return ""
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "object-replaced",
            str(exc),
            "replace only this object with a visible placeholder",
            node=node,
        )
        return _fallback_node_svg(node, ctx, top_level=top_level)
    finally:
        ctx.current_node = previous_node


def _fallback_node_svg(
    node: ShapeNode,
    ctx: AssemblyContext,
    *,
    top_level: bool,
    source_proxy: bool = False,
) -> str:
    """Keep one unsupported source object visible without aborting its deck."""
    if node.xfrm.w <= 0 or node.xfrm.h <= 0:
        return ""
    x = fmt_num(node.xfrm.x)
    y = fmt_num(node.xfrm.y)
    width = fmt_num(node.xfrm.w)
    height = fmt_num(node.xfrm.h)
    label = _xml_escape(node.name or f"Unsupported {node.kind}")
    inner = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        'fill="#F8FAFC" fill-opacity="0.72" stroke="#DC2626" '
        'stroke-width="1" stroke-dasharray="6 4"/>'
        f'<text x="{fmt_num(node.xfrm.x + 8)}" '
        f'y="{fmt_num(node.xfrm.y + min(18, node.xfrm.h / 2))}" '
        f'font-size="12" fill="#991B1B">{label}</text>'
    )
    extra_attrs = (
        [
            f'{_SOURCE_PROXY_ATTRIBUTE}="{_SOURCE_PROXY_KIND}"',
            f'{_EXTERNAL_LINKED_IMAGE_PROXY_ATTRIBUTE}="true"',
        ]
        if source_proxy
        else None
    )
    return _wrap_shape_group(
        inner,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=extra_attrs,
    )


# ---------------------------------------------------------------------------
# Shape (<p:sp>)
# ---------------------------------------------------------------------------

def _convert_shape(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    sp_pr = node.xml.find("p:spPr", NS)

    # Check for blipFill (image-filled shape, e.g. Canva exports where images
    # are expressed as <p:sp> + <a:blipFill> rather than <p:pic>).
    geom = _resolve_geometry(node, sp_pr)

    blip_fill_elem = sp_pr.find("a:blipFill", NS) if sp_pr is not None else None
    blip_image = ""
    if blip_fill_elem is not None:
        try:
            blip_result = convert_blip_fill(
                blip_fill_elem, node.xfrm, ctx.slide_part, ctx.pkg,
                media_subdir=ctx.media_subdir,
                embed_inline=ctx.embed_images,
                asset_name_map=ctx.asset_name_map,
                strict=ctx.strict,
            )
        except LinkedImageResolutionError as exc:
            if ctx.strict:
                raise
            ctx.diagnose(
                "linked-image-proxy",
                str(exc),
                "retain the complete source object as a non-editable proxy",
            )
            return _fallback_node_svg(
                node,
                ctx,
                top_level=top_level,
                source_proxy=True,
            )
        except (ValueError, MediaResolutionError) as exc:
            if ctx.strict:
                raise
            ctx.diagnose(
                "image-fill-omitted",
                str(exc),
                "omit the image fill and retain shape geometry/text",
            )
        else:
            if blip_result.external_linked:
                ctx.diagnose(
                    "linked-image-proxy",
                    "Externally linked image fills are source-backed",
                    "retain the complete source object as a non-editable proxy",
                )
                return _fallback_node_svg(
                    node,
                    ctx,
                    top_level=top_level,
                    source_proxy=True,
                )
            _diagnose_picture_result(ctx, blip_result)
            if blip_result.svg:
                blip_image = _clip_blip_image(blip_result.svg, geom, ctx)
                ctx.media.update(blip_result.media)

    # Text body (a:txBody)
    source_tx_body = node.xml.find("p:txBody", NS)
    tx_body = _effective_placeholder_tx_body(
        source_tx_body,
        node.inherited_body_properties,
    )
    is_vertical = is_vertical_txbody(tx_body, node.xfrm)
    block_formula = _block_formula_zone(tx_body)
    block_formula_failed = False
    if block_formula is not None and not is_vertical:
        try:
            carrier_error = _block_formula_carrier_error(
                node,
                top_level=top_level,
            )
            if carrier_error is not None:
                raise FormulaImportError(carrier_error)
            imported_formula = import_formula(block_formula, display=True)
        except FormulaImportError as exc:
            _diagnose_formula_fallback(ctx, exc)
            block_formula_failed = True
        else:
            return _render_block_formula(
                node,
                ctx,
                imported_formula,
                top_level=top_level,
            )
    inline_formula_resolver = _prepare_inline_formula_resolver(
        tx_body,
        ctx,
        allow_native=not is_vertical,
        force_opaque=block_formula_failed,
    )
    local_has_run_effects = txbody_has_run_effects(source_tx_body)
    inherited_has_run_effects = txbody_has_run_effects(
        *node.inherited_lst_styles
    )
    metadata_tx_body, inherited_styles_materialized = (
        _materialize_inherited_list_styles(
            tx_body,
            node.inherited_lst_styles,
        )
    )
    export_tx_body = (
        source_tx_body
        if (
            ctx.preserve_placeholder_inheritance
            and node.placeholder is not None
            and source_tx_body is not None
        )
        else metadata_tx_body
    )
    has_run_effects = local_has_run_effects or inherited_has_run_effects
    if geom is not None and has_run_effects:
        if is_vertical:
            geom.attrs.update(unsupported_effect_metadata(
                "unsupported-run-effect-route:vertical-text"
            ))
        elif tx_body is not None and has_relationship_attributes(tx_body):
            geom.attrs.update(unsupported_effect_metadata(
                "unsupported-run-effect-route:relationship-bearing-text"
            ))
        elif inherited_has_run_effects and not inherited_styles_materialized:
            geom.attrs.update(unsupported_effect_metadata(
                "unsupported-run-effect-route:inherited-text-style"
            ))

    # Geometry (fill is "none" when blipFill is present, so only stroke draws)
    geom_xml = _build_geometry_xml(node, sp_pr, ctx, geom=geom)

    try:
        text_default_fill = _resolve_text_style_default(node, ctx)
        if tx_body is not None and is_vertical:
            text_result = convert_vertical_txbody(
                tx_body, node.xfrm, ctx.palette,
                theme_fonts=ctx.theme_fonts,
                slide_number=ctx.slide_number,
                default_fill=text_default_fill,
                default_font_size_px=DEFAULT_FONT_SIZE_PX,
                fallback_lst_styles=node.inherited_lst_styles,
                id_prefix=f"{ctx.group_id_prefix}txt",
                id_seq=ctx.grad_seq,
                hyperlink_resolver=lambda rid, action: _resolve_svg_hyperlink(
                    ctx,
                    rid,
                    action,
                ),
                inline_formula_resolver=inline_formula_resolver,
                strict=ctx.strict,
                diagnostic_sink=ctx.diagnose,
            )
        else:
            text_result = convert_txbody(
                tx_body, node.xfrm, ctx.palette,
                theme_fonts=ctx.theme_fonts,
                slide_number=ctx.slide_number,
                default_fill=text_default_fill,
                default_font_size_px=DEFAULT_FONT_SIZE_PX,
                fallback_lst_styles=node.inherited_lst_styles,
                id_prefix=f"{ctx.group_id_prefix}txt",
                id_seq=ctx.grad_seq,
                hyperlink_resolver=lambda rid, action: _resolve_svg_hyperlink(
                    ctx,
                    rid,
                    action,
                ),
                inline_formula_resolver=inline_formula_resolver,
                strict=ctx.strict,
                diagnostic_sink=ctx.diagnose,
            ) if tx_body is not None else TextResult()
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "text-omitted",
            str(exc),
            "omit this text body and retain the object's other visuals",
        )
        text_result = TextResult()
    if text_result.defs:
        ctx.defs.extend(text_result.defs)
    visible_text_svg = (
        text_result.svg
        if is_vertical
        else _counter_reflected_text_svg(text_result.svg, node.xfrm)
    )

    if is_vertical:
        # Vertical text: geometry + image in one group, text in separate group
        geom_inner = (blip_image + "\n" + geom_xml) if blip_image else geom_xml
        shape_xml = _wrap_shape_group(
            geom_inner,
            node,
            ctx,
            top_level=top_level,
            extra_attrs=_geometry_group_attrs(geom),
        )
        if not visible_text_svg:
            return shape_xml
        text_group = (
            f'<g id="{ctx.group_id_prefix}shape-{node.spid or ctx.shape_seq[0]}-text"'
            f' data-name="{_xml_escape(node.name)} text">\n'
            f"{visible_text_svg}\n</g>"
        )
        return f"{shape_xml}\n{text_group}"

    # Normal: image (behind) + geometry (stroke) + text (top)
    inner_parts = []
    if blip_image:
        inner_parts.append(blip_image)
    if geom_xml:
        inner_parts.append(geom_xml)
    if (
        export_tx_body is not None
        and geom is not None
        and not text_result.contains_inline_formula
    ):
        inner_parts.append(
            _txbody_metadata(
                export_tx_body,
                visible_text_svg,
            )
        )
    placeholder_sp_pr = _placeholder_sp_pr_metadata(node, ctx)
    if placeholder_sp_pr:
        inner_parts.append(placeholder_sp_pr)
    if visible_text_svg:
        inner_parts.append(visible_text_svg)
    inner = "\n".join(inner_parts) if inner_parts else ""
    return _wrap_shape_group(
        inner,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=_geometry_group_attrs(geom),
    )


def _effective_placeholder_tx_body(
    tx_body: ET.Element | None,
    inherited_body_properties: tuple[ET.Element, ...],
) -> ET.Element | None:
    """Merge inherited placeholder bodyPr settings into one visible text body."""
    if tx_body is None or not inherited_body_properties:
        return tx_body
    effective = copy.deepcopy(tx_body)
    body_pr = effective.find("a:bodyPr", NS)
    if body_pr is None:
        body_pr = ET.Element(f"{{{NS['a']}}}bodyPr")
        effective.insert(0, body_pr)

    child_groups = (
        {"prstTxWarp"},
        {"noAutofit", "normAutofit", "spAutoFit"},
        {"scene3d"},
        {"sp3d"},
    )
    for inherited in inherited_body_properties:
        for name, value in inherited.attrib.items():
            body_pr.attrib.setdefault(name, value)
        local_names = {
            child.tag.rsplit("}", 1)[-1]
            for child in body_pr
            if isinstance(child.tag, str)
        }
        for group in child_groups:
            if local_names & group:
                continue
            inherited_child = next(
                (
                    child
                    for child in inherited
                    if isinstance(child.tag, str)
                    and child.tag.rsplit("}", 1)[-1] in group
                ),
                None,
            )
            if inherited_child is not None:
                body_pr.append(copy.deepcopy(inherited_child))
                local_names.add(inherited_child.tag.rsplit("}", 1)[-1])
    return effective


def _materialize_inherited_list_styles(
    tx_body: ET.Element | None,
    inherited_lst_styles: tuple[ET.Element, ...],
) -> tuple[ET.Element | None, bool]:
    """Flatten placeholder list-style inheritance into the preserved txBody."""
    if not inherited_lst_styles:
        return tx_body, True
    if tx_body is None:
        return None, False

    effective = copy.deepcopy(tx_body)
    lst_style = effective.find("a:lstStyle", NS)
    if lst_style is None:
        lst_style = ET.Element(f"{{{NS['a']}}}lstStyle")
        body_pr = effective.find("a:bodyPr", NS)
        insert_at = list(effective).index(body_pr) + 1 if body_pr is not None else 0
        effective.insert(insert_at, lst_style)

    for level in range(1, 10):
        local_level = lst_style.find(f"a:lvl{level}pPr", NS)
        inherited_levels = [
            level_pr
            for inherited in inherited_lst_styles
            if (level_pr := inherited.find(f"a:lvl{level}pPr", NS)) is not None
        ]
        if local_level is None and not inherited_levels:
            continue

        merged = ET.Element(f"{{{NS['a']}}}lvl{level}pPr")
        for source in reversed(inherited_levels):
            _merge_text_property_element(merged, source)
        if local_level is not None:
            _merge_text_property_element(merged, local_level)

        if local_level is None:
            lst_style.append(merged)
        else:
            index = list(lst_style).index(local_level)
            lst_style.remove(local_level)
            lst_style.insert(index, merged)

    return effective, True


def _merge_text_property_element(
    target: ET.Element,
    source: ET.Element,
) -> None:
    """Overlay one DrawingML paragraph/run property node by choice group."""
    target.attrib.update(source.attrib)
    for source_child in source:
        key = _text_property_child_key(source_child)
        target_child = next(
            (
                child
                for child in target
                if _text_property_child_key(child) == key
            ),
            None,
        )
        if (
            source_child.tag == f"{{{NS['a']}}}defRPr"
            and target_child is not None
        ):
            _merge_text_property_element(target_child, source_child)
            continue
        if target_child is not None:
            index = list(target).index(target_child)
            target.remove(target_child)
            target.insert(index, copy.deepcopy(source_child))
        else:
            target.append(copy.deepcopy(source_child))


def _text_property_child_key(child: ET.Element) -> str:
    """Return the OOXML choice-group key for one text-property child."""
    name = child.tag.rsplit("}", 1)[-1]
    groups = (
        ("fill", {
            "noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill",
        }),
        ("effect", {"effectLst", "effectDag"}),
        ("bullet-color", {"buClrTx", "buClr"}),
        ("bullet-size", {"buSzTx", "buSzPct", "buSzPts"}),
        ("bullet-font", {"buFontTx", "buFont"}),
        ("bullet-kind", {"buNone", "buAutoNum", "buChar", "buBlip"}),
        ("underline-line", {"uLnTx", "uLn"}),
        ("underline-fill", {"uFillTx", "uFill"}),
    )
    for key, names in groups:
        if name in names:
            return key
    return name


def _counter_reflected_text_svg(text_svg: str, xfrm: Xfrm) -> str:
    """Keep text upright when DrawingML flips its owning shape geometry."""
    if not text_svg or xfrm.rot or not (xfrm.flip_h or xfrm.flip_v):
        return text_svg
    transform = xfrm.to_svg_transform()
    if not transform:
        return text_svg
    return (
        '<g data-pptx-text-flip-compensation="true" '
        f'transform="{_xml_escape(transform)}">\n{text_svg}\n</g>'
    )


def _block_formula_zone(tx_body: ET.Element | None) -> ET.Element | None:
    """Return the sole block-math zone from a canonical formula text body."""
    if tx_body is None:
        return None
    paragraphs = tx_body.findall("a:p", NS)
    if len(paragraphs) != 1:
        return None
    paragraph = paragraphs[0]
    formula_zones = [
        child
        for child in paragraph
        if child.tag == f"{{{A14_NS}}}m"
    ]
    allowed = {
        f"{{{NS['a']}}}pPr",
        f"{{{NS['a']}}}endParaRPr",
        f"{{{A14_NS}}}m",
    }
    if len(formula_zones) != 1 or any(
        child.tag not in allowed
        for child in paragraph
        if isinstance(child.tag, str)
    ):
        return None
    root_children = [
        child for child in formula_zones[0] if isinstance(child.tag, str)
    ]
    if (
        len(root_children) != 1
        or root_children[0].tag
        != "{http://schemas.openxmlformats.org/officeDocument/2006/math}oMathPara"
    ):
        return None
    return formula_zones[0]


def _block_formula_carrier_error(
    node: ShapeNode,
    *,
    top_level: bool,
) -> str | None:
    """Reject block carriers whose non-formula state would be discarded."""
    if not top_level:
        return "grouped block formula carrier is not reversible"
    if (
        node.xfrm.rot
        or node.xfrm.flip_h
        or node.xfrm.flip_v
        or node.effective_rotation
    ):
        return "block formula carrier rotation or flip is not reversible"
    if node.placeholder is not None:
        return "block formula carrier cannot retain placeholder ownership"
    if node.hyperlink_rid or node.hyperlink_action:
        return "block formula carrier hyperlink is not reversible"
    if node.xml.find("p:style", NS) is not None:
        return "block formula carrier style reference is not reversible"

    sp_pr = node.xml.find("p:spPr", NS)
    if sp_pr is None:
        return "block formula carrier is missing p:spPr"
    preset = sp_pr.find("a:prstGeom", NS)
    if preset is None or preset.get("prst") != "rect":
        return "block formula carrier must use rectangular geometry"
    if any(
        sp_pr.find(path, NS) is not None
        for path in (
            "a:solidFill",
            "a:gradFill",
            "a:pattFill",
            "a:blipFill",
            "a:grpFill",
            "a:effectLst",
            "a:effectDag",
            "a:scene3d",
            "a:sp3d",
        )
    ):
        return "block formula carrier paint or effect is not reversible"
    line = sp_pr.find("a:ln", NS)
    if line is not None and line.find("a:noFill", NS) is None:
        return "block formula carrier line is not reversible"
    return None


def _prepare_inline_formula_resolver(
    tx_body: ET.Element | None,
    ctx: AssemblyContext,
    *,
    allow_native: bool,
    force_opaque: bool = False,
):
    """Build one all-or-opaque resolver for formula runs in a text body."""
    if tx_body is None:
        return None
    zones = [
        child
        for paragraph in tx_body.findall("a:p", NS)
        for child in paragraph
        if child.tag == f"{{{A14_NS}}}m"
    ]
    if not zones:
        return None

    imported: dict[int, FormulaImport] = {}
    failed = force_opaque
    if not allow_native:
        failed = True
        _diagnose_formula_fallback(
            ctx,
            FormulaImportError(
                "formula reconstruction is not supported inside vertical text"
            ),
        )
    elif not force_opaque:
        for zone in zones:
            try:
                imported[id(zone)] = import_formula(zone, display=False)
            except FormulaImportError as exc:
                failed = True
                _diagnose_formula_fallback(ctx, exc)

    def _resolve(zone: ET.Element) -> tuple[str | None, str]:
        if failed:
            return None, opaque_formula_preview(zone)
        item = imported.get(id(zone))
        if item is None:
            return None, opaque_formula_preview(zone)
        return item.latex, item.preview

    return _resolve


def _diagnose_formula_fallback(
    ctx: AssemblyContext,
    error: FormulaImportError,
) -> None:
    message = f"Office Math was not reconstructed: {error}"
    if ctx.strict:
        raise ValueError(message) from error
    ctx.diagnose(
        "formula-not-reconstructed",
        message,
        "render a linear text preview and preserve the relationship-free source txBody",
    )


def _render_block_formula(
    node: ShapeNode,
    ctx: AssemblyContext,
    formula: FormulaImport,
    *,
    top_level: bool,
) -> str:
    """Emit one canonical block marker and a dependency-free SVG preview."""
    x = fmt_num(node.xfrm.x)
    y = fmt_num(node.xfrm.y)
    width = fmt_num(node.xfrm.w)
    height = fmt_num(node.xfrm.h)
    align = formula.align
    if align == "right":
        preview_x = node.xfrm.x + node.xfrm.w
        anchor = "end"
    elif align == "left":
        preview_x = node.xfrm.x
        anchor = "start"
    else:
        preview_x = node.xfrm.x + node.xfrm.w / 2.0
        anchor = "middle"
    preview_y = node.xfrm.y + node.xfrm.h / 2.0 + formula.font_size_px * 0.35
    payload = {
        "latex": formula.latex,
        "display": "block",
        "font_size": formula.font_size_px,
        "color": formula.color,
        "align": align,
        "language": formula.language,
        "name": node.name or f"Formula {node.spid}",
    }
    metadata = (
        '<metadata type="application/json">'
        + _xml_escape(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        + "</metadata>"
    )
    preview = (
        f'<text x="{fmt_num(preview_x)}" y="{fmt_num(preview_y)}" '
        f'text-anchor="{anchor}" font-family="Cambria Math" '
        f'font-size="{fmt_num(formula.font_size_px)}" '
        f'fill="{_xml_escape(formula.color)}">'
        f'{_xml_escape(formula.preview)}</text>'
    )
    return _wrap_shape_group(
        metadata + "\n" + preview,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=[
            'data-pptx-replace-with="formula"',
            'data-pptx-import-source="pptx"',
            f'data-pptx-x="{x}"',
            f'data-pptx-y="{y}"',
            f'data-pptx-width="{width}"',
            f'data-pptx-height="{height}"',
            f'data-pptx-bounds="{x} {y} {width} {height}"',
        ],
    )


def _txbody_metadata(
    tx_body: ET.Element,
    visible_text_svg: str,
) -> str:
    """Preserve the native text body while its visible SVG remains authoritative."""
    if has_relationship_attributes(tx_body):
        # Relationship ids are part-local and cannot be copied into a newly
        # generated slide without rebuilding the relationship target.
        return ""
    raw = ET.tostring(tx_body, encoding="utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    wrapper = ET.fromstring(
        f'<svg xmlns="http://www.w3.org/2000/svg">{visible_text_svg}</svg>'
    )
    digest = svg_text_fingerprint(wrapper)
    return (
        '<metadata data-pptx-part="txbody" data-pptx-encoding="base64" '
        f'data-pptx-text-sha256="{digest}">{encoded}</metadata>'
    )


def _placeholder_sp_pr_metadata(
    node: ShapeNode,
    ctx: AssemblyContext,
) -> str:
    """Preserve relationship-free local placeholder geometry for inheritance."""
    if (
        not ctx.preserve_placeholder_inheritance
        or node.placeholder is None
        or node.kind != SHAPE
    ):
        return ""
    sp_pr = node.xml.find("p:spPr", NS)
    if sp_pr is None or has_relationship_attributes(sp_pr):
        return ""
    raw = ET.tostring(sp_pr, encoding="utf-8")
    return (
        '<metadata data-pptx-part="placeholder-sppr" '
        'data-pptx-encoding="base64" '
        f'data-pptx-ooxml-sha256="{hashlib.sha256(raw).hexdigest()}">'
        f'{base64.b64encode(raw).decode("ascii")}</metadata>'
    )


def _resolve_geometry(node: ShapeNode, sp_pr: ET.Element | None) -> GeomResult | None:
    """Resolve a DrawingML shape geometry into an absolute SVG geometry model."""
    prst_geom = sp_pr.find("a:prstGeom", NS) if sp_pr is not None else None
    cust_geom = sp_pr.find("a:custGeom", NS) if sp_pr is not None else None
    prst = prst_geom.attrib.get("prst", "rect") if prst_geom is not None else None

    geom: GeomResult | None = None
    if prst_geom is not None:
        geom = convert_prst_geom(prst, node.xfrm, prst_geom)
    elif cust_geom is not None:
        d = convert_custom_geom(cust_geom, node.xfrm)
        if d:
            raw = ET.tostring(cust_geom, encoding="utf-8")
            geom = GeomResult(
                tag="path",
                path_d=d,
                attrs={
                    "data-pptx-part": "geometry",
                    "data-pptx-geometry-kind": "custom",
                    "data-pptx-custgeom": base64.b64encode(raw).decode("ascii"),
                    "data-pptx-geometry-sha256": hashlib.sha256(
                        d.strip().encode("utf-8")
                    ).hexdigest(),
                },
            )
    else:
        # No geometry hint at all — render bounding rect
        geom = convert_prst_geom("rect", node.xfrm, None)

    if geom is None:
        return None
    permits_degenerate_axis = (
        node.kind == CONNECTOR
        or prst in CONNECTOR_PRESET_TYPES
    )
    if (
        not permits_degenerate_axis
        and (node.xfrm.w <= 0 or node.xfrm.h <= 0)
    ):
        return None
    return geom


def _build_geometry_xml(node: ShapeNode, sp_pr: ET.Element | None,
                        ctx: AssemblyContext,
                        geom: GeomResult | None = None) -> str:
    """Build the SVG geometry element with fill/stroke/effect attributes."""
    if geom is None:
        geom = _resolve_geometry(node, sp_pr)
    if geom is None:
        return ""

    # Resolve style defaults early so markers can adopt the theme stroke color
    # when <a:ln> doesn't carry an explicit solidFill.
    try:
        style_defaults = _resolve_shape_style_defaults(node, ctx)
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "shape-style-omitted",
            str(exc),
            "omit unresolved theme style defaults",
        )
        style_defaults = {}

    # Fill / stroke / effect
    try:
        fill = resolve_fill(
            sp_pr,
            ctx.palette,
            id_prefix="g",
            id_seq=ctx.grad_seq,
            group_fill=ctx.group_fills[-1] if ctx.group_fills else None,
        )
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "fill-omitted",
            str(exc),
            "omit only the unsupported fill",
        )
        fill = FillResult.none_fill()
    try:
        stroke = resolve_stroke(
            sp_pr,
            ctx.palette,
            id_prefix="m",
            id_seq=ctx.marker_seq,
            style_stroke_default=style_defaults.get("stroke"),
            gradient_frame=(
                node.xfrm.x,
                node.xfrm.y,
                node.xfrm.w,
                node.xfrm.h,
            ),
        )
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "stroke-omitted",
            str(exc),
            "omit only the unsupported outline",
        )
        stroke = StrokeResult(attrs={"stroke": "none"})
    try:
        effect = convert_effects(
            sp_pr,
            ctx.palette,
            id_prefix="fx",
            id_seq=ctx.filter_seq,
            target_rotation_degrees=node.effective_rotation,
        )
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "effect-omitted",
            str(exc),
            "omit only the unsupported visual effect",
        )
        effect = EffectResult()

    ctx.defs.extend(fill.defs)
    ctx.defs.extend(stroke.defs)
    ctx.defs.extend(effect.defs)
    effect_attrs = dict(effect.metadata)
    effect_reason = effect_attrs.get(EFFECT_REASON_ATTR)
    existing_reason = geom.attrs.get(EFFECT_REASON_ATTR)
    if effect_reason is not None and existing_reason is not None:
        effect_attrs.update(unsupported_effect_metadata(
            existing_reason,
            effect_reason,
        ))
    geom.attrs.update(effect_attrs)
    _diagnose_unsupported_effect(ctx, geom.attrs)

    attrs = {**fill.attrs, **stroke.attrs}
    for key, value in style_defaults.items():
        attrs.setdefault(key, value)
    if effect.filter_id is not None:
        attrs["filter"] = f"url(#{effect.filter_id})"

    # Default fill / stroke when not specified by spPr (matches PowerPoint
    # behavior: a:noFill on shape-level fill if there's a txBody, else any
    # explicit fill present in spPr should already have been captured).
    if "fill" not in attrs:
        attrs["fill"] = "none"
    if "stroke" not in attrs:
        # Spec default for shapes is no stroke unless ln says otherwise.
        # Skip emitting stroke="none" to keep markup tight.
        pass

    semantic_attrs = {
        **geom.attrs,
        **_object_metadata(node, ctx),
    }
    shape_style = node.xml.find("p:style", NS)
    if shape_style is not None:
        semantic_attrs["data-pptx-shape-style"] = base64.b64encode(
            ET.tostring(shape_style, encoding="utf-8")
        ).decode("ascii")
    if geom.layers:
        return _preset_layers_to_svg(geom, semantic_attrs, attrs)
    return _geom_to_svg(
        geom,
        _attrs_to_xml({**semantic_attrs, **attrs}),
    )


def _resolve_shape_style_defaults(node: ShapeNode, ctx: AssemblyContext) -> dict[str, str]:
    """Resolve minimal p:style defaults used when spPr omits explicit style.

    Full theme style matrix reproduction is intentionally out of scope here;
    this only prevents common theme-styled placeholders/shapes from becoming
    transparent or unstroked when their visible color lives in p:style.
    """
    style = node.xml.find("p:style", NS)
    if style is None:
        return {}

    defaults: dict[str, str] = {}

    fill_ref = style.find("a:fillRef", NS)
    if fill_ref is not None and fill_ref.attrib.get("idx", "").strip() != "0":
        fill_color = _resolve_ref_color(fill_ref, ctx)
        if fill_color:
            defaults["fill"] = fill_color

    ln_ref = style.find("a:lnRef", NS)
    if ln_ref is not None and ln_ref.attrib.get("idx", "").strip() != "0":
        line_color = _resolve_ref_color(ln_ref, ctx)
        if line_color:
            defaults["stroke"] = line_color
            defaults.setdefault("stroke-width", "1")

    return defaults


def _resolve_text_style_default(node: ShapeNode, ctx: AssemblyContext) -> str:
    """Resolve p:style fontRef color used by runs without explicit fill."""
    style = node.xml.find("p:style", NS)
    if style is None:
        return "#000000"
    font_ref = style.find("a:fontRef", NS)
    font_color = _resolve_ref_color(font_ref, ctx)
    return font_color or "#000000"


def _resolve_ref_color(ref_elem: ET.Element | None, ctx: AssemblyContext) -> str | None:
    color_elem = find_color_elem(ref_elem)
    hex_, _alpha = resolve_color(color_elem, ctx.palette)
    return hex_


def _geom_to_svg(geom: GeomResult, attrs_xml: str | None = None) -> str:
    """Serialize a resolved geometry with optional SVG attributes."""
    if attrs_xml is None:
        attrs_xml = _attrs_to_xml(geom.attrs)
    if geom.tag == "path":
        return f'<path d="{geom.path_d}"{attrs_xml}/>'
    if geom.tag in ("polygon", "polyline"):
        return f'<{geom.tag} points="{geom.points}"{attrs_xml}/>'
    return f"<{geom.tag}{attrs_xml}/>"


def _preset_layers_to_svg(
    geom: GeomResult,
    semantic_attrs: dict[str, str],
    style_attrs: dict[str, str],
) -> str:
    """Serialize one semantic carrier plus every visible preset path layer.

    DrawingML applies shape-level fill/line first, then each preset path can
    override whether and how that paint is used.  A hidden carrier retains the
    unmodified shape-level style for native round-trip; visible detail paths
    reproduce the preset's independent paint behavior without being exported
    as duplicate PowerPoint shapes.
    """
    markup = serialize_preset_layers(
        geom.layers,
        semantic_attrs,
        style_attrs,
    )
    geom.attrs["data-pptx-preview-sha256"] = markup.preview_hash
    semantic_attrs["data-pptx-preview-sha256"] = markup.preview_hash
    return markup.markup


def _clip_blip_image(image_xml: str, geom: GeomResult | None,
                     ctx: AssemblyContext) -> str:
    """Clip image fills to the owning shape geometry when it is not a plain rect."""
    if geom is None or geom.tag == "line":
        return image_xml
    if geom.attrs.get("data-pptx-prst") == "rect":
        return image_xml
    if geom.tag == "rect" and not geom.attrs.get("rx") and not geom.attrs.get("ry"):
        return image_xml

    clip_geom = geom
    if image_xml.startswith("<svg"):
        flattened = None
        if (
            not ctx.strict
            and geom.attrs.get("data-pptx-geometry-kind") == "custom"
        ):
            flattened = _flatten_vector_custom_crop(image_xml)
        if flattened is not None:
            image_xml = flattened
            ctx.diagnose(
                "vector-custom-geometry-crop-normalized",
                "SVG-only picture combines srcRect with custom geometry; "
                "Office renders the complete vector as the custom-shape fill",
                "ignore srcRect and clip the complete vector to the custom geometry",
            )
        else:
            try:
                clip_geom = _project_clip_into_nested_crop(geom, image_xml)
            except ValueError as exc:
                if ctx.strict:
                    raise ValueError(
                        f"Cannot project picture geometry into its crop viewBox: {exc}"
                    ) from exc
                ctx.diagnose(
                    "nested-crop-shape-clip-omitted",
                    f"Cannot project picture geometry into its crop viewBox: {exc}",
                    "source image crop retained without the additional shape clip",
                )
                return image_xml

    ctx.clip_seq[0] += 1
    clip_id = f"{ctx.group_id_prefix}clip{ctx.clip_seq[0]}"
    clip_shape = _geom_to_svg(clip_geom, "")
    ctx.defs.append(
        f'<clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">'
        f'{clip_shape}</clipPath>'
    )
    return _inject_clip_path(image_xml, clip_id)


def _flatten_vector_custom_crop(image_xml: str) -> str | None:
    """Normalize an SVG-only custom-shape crop to a plain full-vector image."""
    wrapper = ET.fromstring(image_xml)
    if wrapper.tag != "svg" or len(wrapper) != 1 or wrapper[0].tag != "image":
        return None
    image = wrapper[0]
    href = image.attrib.get("href", "")
    href_path = href.split("#", 1)[0].split("?", 1)[0].casefold()
    if not (
        href_path.endswith(".svg")
        or href_path.startswith("data:image/svg+xml")
    ):
        return None

    attrs = {
        key: value
        for key, value in image.attrib.items()
        if key not in {"x", "y", "width", "height", "preserveAspectRatio"}
    }
    for key in ("x", "y", "width", "height"):
        value = wrapper.attrib.get(key)
        if value is None:
            return None
        attrs[key] = value
    attrs["preserveAspectRatio"] = "none"
    return f"<image{_attrs_to_xml(attrs)}/>"


def _inject_clip_path(image_xml: str, clip_id: str) -> str:
    clip_attr = f' clip-path="url(#{clip_id})"'
    if image_xml.startswith("<image"):
        return image_xml.replace("<image", f"<image{clip_attr}", 1)
    if image_xml.startswith("<svg"):
        marked = image_xml.replace("<svg", '<svg data-pptx-crop="1"', 1)
        return marked.replace("<image", f"<image{clip_attr}", 1)
    return image_xml


def _project_clip_into_nested_crop(
    geom: GeomResult,
    image_xml: str,
) -> GeomResult:
    """Map absolute slide geometry into one nested crop's viewBox space."""
    wrapper = ET.fromstring(image_xml)
    if wrapper.tag != "svg":
        raise ValueError("expected a nested <svg> crop wrapper")

    try:
        frame_x = float(wrapper.attrib["x"])
        frame_y = float(wrapper.attrib["y"])
        frame_w = float(wrapper.attrib["width"])
        frame_h = float(wrapper.attrib["height"])
        view_box = [float(token) for token in wrapper.attrib["viewBox"].split()]
    except (KeyError, ValueError) as exc:
        raise ValueError("crop wrapper has incomplete numeric geometry") from exc
    if frame_w <= 0 or frame_h <= 0 or len(view_box) != 4:
        raise ValueError(
            "crop wrapper requires positive dimensions and four viewBox values"
        )
    vb_x, vb_y, vb_w, vb_h = view_box
    if vb_w <= 0 or vb_h <= 0:
        raise ValueError("crop viewBox dimensions must be positive")

    scale_x = vb_w / frame_w
    scale_y = vb_h / frame_h
    matrix = (
        scale_x,
        0.0,
        0.0,
        scale_y,
        vb_x - frame_x * scale_x,
        vb_y - frame_y * scale_y,
    )

    if geom.tag == "path" and geom.path_d:
        commands = normalize_path_commands(
            svg_path_to_absolute(parse_svg_path(geom.path_d))
        )
        transformed = transform_path_commands(commands, matrix)
        return GeomResult(
            tag="path",
            path_d=_serialize_clip_path(transformed),
        )
    if geom.tag in {"polygon", "polyline"} and geom.points:
        points = parse_svg_points(
            geom.points,
            min_points=3 if geom.tag == "polygon" else 2,
        )
        transformed = [
            (
                x * scale_x + matrix[4],
                y * scale_y + matrix[5],
            )
            for x, y in points
        ]
        return GeomResult(
            tag=geom.tag,
            points=" ".join(
                f"{fmt_num(x, 5)},{fmt_num(y, 5)}"
                for x, y in transformed
            ),
        )
    raise ValueError(f"unsupported clip geometry <{geom.tag}>")


def _serialize_clip_path(commands: list[PathCommand]) -> str:
    """Serialize normalized M/L/C/Z commands with crop-safe precision."""
    parts: list[str] = []
    for command in commands:
        parts.append(command.cmd)
        if command.args:
            parts.append(" ".join(fmt_num(value, 5) for value in command.args))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Picture (<p:pic>)
# ---------------------------------------------------------------------------

def _convert_picture(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    sp_pr = node.xml.find("p:spPr", NS)
    geom = _resolve_geometry(node, sp_pr)
    try:
        result = convert_picture(
            node.xml, node.xfrm, ctx.slide_part, ctx.pkg,
            media_subdir=ctx.media_subdir,
            embed_inline=ctx.embed_images,
            asset_name_map=ctx.asset_name_map,
            strict=ctx.strict,
        )
    except LinkedImageResolutionError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "linked-image-proxy",
            str(exc),
            "retain the complete source picture as a non-editable proxy",
        )
        return _fallback_node_svg(
            node,
            ctx,
            top_level=top_level,
            source_proxy=True,
        )
    except MediaResolutionError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "object-replaced",
            str(exc),
            "replace only this picture with a visible placeholder",
        )
        return _fallback_node_svg(node, ctx, top_level=top_level)
    if not result.svg:
        return ""
    _diagnose_picture_result(ctx, result)
    ctx.media.update(result.media)
    effect = convert_effects(
        sp_pr,
        ctx.palette,
        id_prefix="fx",
        id_seq=ctx.filter_seq,
        target_rotation_degrees=node.effective_rotation,
    )
    ctx.defs.extend(effect.defs)
    effect_metadata = dict(effect.metadata)
    _diagnose_unsupported_effect(ctx, effect_metadata)
    clipped_svg = _clip_blip_image(result.svg, geom, ctx)
    picture_attrs = {**_object_metadata(node, ctx), **effect_metadata}
    group_attrs = _metadata_group_attrs(effect_metadata)
    if result.external_linked:
        group_attrs.append(
            f'{_SOURCE_PROXY_ATTRIBUTE}="{_SOURCE_PROXY_KIND}"'
        )
        group_attrs.append(
            f'{_EXTERNAL_LINKED_IMAGE_PROXY_ATTRIBUTE}="true"'
        )
    if effect.filter_id is not None:
        filter_attr = f"url(#{effect.filter_id})"
        if (
            clipped_svg.startswith("<svg")
            or clipped_svg.startswith("<image clip-path=")
        ):
            # Keep the effect outside the crop viewport so shadows and glows
            # remain visible beyond the picture geometry in SVG previews.
            group_attrs.append(f'filter="{filter_attr}"')
        else:
            picture_attrs["filter"] = filter_attr
    picture_svg = _inject_root_svg_attrs(
        clipped_svg,
        picture_attrs,
    )
    return _wrap_shape_group(
        picture_svg,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=group_attrs,
    )


def _inject_root_svg_attrs(markup: str, attrs: dict[str, str]) -> str:
    """Attach source-object identity to a picture's root SVG element."""
    attrs_xml = _attrs_to_xml(attrs)
    for tag in ("image", "svg"):
        prefix = f"<{tag}"
        if markup.startswith(prefix):
            return markup.replace(prefix, f"{prefix}{attrs_xml}", 1)
    return markup


# ---------------------------------------------------------------------------
# Connector (<p:cxnSp>)
# ---------------------------------------------------------------------------

def _convert_connector(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    sp_pr = node.xml.find("p:spPr", NS)
    geom = _resolve_geometry(node, sp_pr)
    geom_xml = _build_geometry_xml(node, sp_pr, ctx, geom=geom)
    return _wrap_shape_group(
        geom_xml,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=_geometry_group_attrs(geom),
    )


# ---------------------------------------------------------------------------
# Group (<p:grpSp>)
# ---------------------------------------------------------------------------

def _convert_group(node: ShapeNode, ctx: AssemblyContext, *, top_level: bool) -> str:
    """Render group contents flat (children already remapped to slide space)."""
    parent_fill = ctx.group_fills[-1] if ctx.group_fills else None
    group_properties = node.xml.find("p:grpSpPr", NS)
    try:
        resolved_fill = resolve_fill(
            group_properties,
            ctx.palette,
            id_prefix="g",
            id_seq=ctx.grad_seq,
            group_fill=parent_fill,
        )
    except ValueError as exc:
        if ctx.strict:
            raise
        ctx.diagnose(
            "group-fill-omitted",
            str(exc),
            "inherit the nearest resolved ancestor group fill when available",
        )
        group_fill = parent_fill
    else:
        ctx.defs.extend(resolved_fill.defs)
        group_fill = (
            FillResult(attrs=dict(resolved_fill.attrs))
            if resolved_fill.attrs
            else parent_fill
        )

    inner_parts: list[str] = []
    ctx.group_fills.append(group_fill)
    try:
        for child in node.children:
            chunk = _convert_node(child, ctx, top_level=False)
            if chunk:
                inner_parts.append(chunk)
    finally:
        ctx.group_fills.pop()
    if not inner_parts:
        return ""
    inner = "\n".join(inner_parts)
    effect_metadata = unsupported_target_effect_metadata(
        node.xml.find("p:grpSpPr", NS),
        "group",
    )
    _diagnose_unsupported_effect(ctx, effect_metadata)
    return _wrap_shape_group(
        inner,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=_metadata_group_attrs(effect_metadata),
    )


# ---------------------------------------------------------------------------
# Graphic frame fallback (<p:graphicFrame>)
# ---------------------------------------------------------------------------

def _convert_graphic_fallback(node: ShapeNode, ctx: AssemblyContext,
                              *, top_level: bool) -> str:
    """Render a <p:graphicFrame> by dispatching on its graphicData uri.

    Currently:
    - ``...drawingml/2006/table`` → real table renderer (`convert_tbl`)
    - ``...presentationml/2006/ole`` → render the ``mc:Fallback`` preview
      bitmap that PowerPoint bakes alongside every embedded OLE object.
      Visually identical to what PowerPoint shows for an unedited embed.
    - supported classic charts → baked preview plus native chart metadata.
    - everything else (SmartArt / diagram / unsupported chart) → labelled
      preview or bounding rectangle plus transparent unsupported metadata.
    """
    graphic_data = node.xml.find("a:graphic/a:graphicData", NS)
    uri = graphic_data.attrib.get("uri", "graphicFrame") if graphic_data is not None else "graphicFrame"

    if uri == "http://schemas.openxmlformats.org/drawingml/2006/table":
        rendered, replacement_attrs, payload_metadata = _render_graphic_table(
            node,
            ctx,
            graphic_data,
        )
        if rendered:
            inner = (
                f"{payload_metadata}\n{rendered}"
                if payload_metadata
                else rendered
            )
            roundtrip_metadata, roundtrip_attrs = (
                _roundtrip_graphic_frame_metadata(
                    node,
                    ctx,
                    inner,
                    top_level=top_level,
                )
            )
            if roundtrip_metadata:
                inner = f"{roundtrip_metadata}\n{inner}"
            return _wrap_shape_group(
                inner,
                node,
                ctx,
                top_level=top_level,
                extra_attrs=replacement_attrs + roundtrip_attrs,
            )

    preview_svg = ""
    if ctx.render_graphic_previews:
        try:
            preview_svg = _render_graphic_preview(node, ctx)
        except MediaResolutionError as exc:
            if ctx.strict:
                raise
            ctx.diagnose(
                "preview-omitted",
                str(exc),
                "omit the missing baked preview and retain the native, "
                "normalized, or placeholder fallback",
            )

    chart_replacement_attrs: list[str] = []
    chart_payload_metadata = ""
    if uri in {CHART_URI, CHARTEX_URI}:
        rendered, chart_replacement_attrs, chart_payload_metadata = (
            _render_graphic_chart(
                node,
                ctx,
                graphic_data,
                preview_svg,
            )
        )
        if rendered:
            inner = (
                f"{chart_payload_metadata}\n{rendered}"
                if chart_payload_metadata
                else rendered
            )
            return _wrap_shape_group(
                inner,
                node,
                ctx,
                top_level=top_level,
                extra_attrs=chart_replacement_attrs,
            )

    if uri == "http://schemas.openxmlformats.org/presentationml/2006/ole":
        if preview_svg:
            labelled = (
                preview_svg
                + "\n"
                + _graphic_preview_label(node, "ole preview")
            )
            return _wrap_shape_group(labelled, node, ctx, top_level=top_level)

    if preview_svg:
        labelled = (
            preview_svg
            + "\n"
            + _graphic_preview_label(
                node,
                f"{uri.rsplit('/', 1)[-1]} preview",
            )
        )
        return _wrap_shape_group(labelled, node, ctx, top_level=top_level)

    label = uri.rsplit("/", 1)[-1]
    placeholder = (
        f'<rect x="{fmt_num(node.xfrm.x)}" y="{fmt_num(node.xfrm.y)}" '
        f'width="{fmt_num(node.xfrm.w)}" height="{fmt_num(node.xfrm.h)}" '
        f'fill="none" stroke="#999999" stroke-dasharray="4 4"/>'
        f'<text x="{fmt_num(node.xfrm.x + node.xfrm.w / 2)}" '
        f'y="{fmt_num(node.xfrm.y + node.xfrm.h / 2)}" '
        f'text-anchor="middle" font-size="14" fill="#999999">'
        f"[{_xml_escape(label)}]</text>"
    )
    if chart_payload_metadata:
        placeholder = f"{chart_payload_metadata}\n{placeholder}"
    return _wrap_shape_group(
        placeholder,
        node,
        ctx,
        top_level=top_level,
        extra_attrs=chart_replacement_attrs,
    )


def _graphic_preview_label(node: ShapeNode, label: str) -> str:
    return (
        f'<rect x="{fmt_num(node.xfrm.x)}" y="{fmt_num(node.xfrm.y)}" '
        f'width="{fmt_num(node.xfrm.w)}" height="22" '
        f'fill="#FFFFFF" fill-opacity="0.82" stroke="#999999" stroke-width="0.5"/>'
        f'<text x="{fmt_num(node.xfrm.x + 6)}" y="{fmt_num(node.xfrm.y + 15)}" '
        f'font-size="11" fill="#666666">[{_xml_escape(label)}]</text>'
    )


def _replacement_payload_metadata(payload: object) -> str:
    payload_json = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        '<metadata type="application/json">'
        f'{_xml_text_escape(payload_json)}</metadata>'
    )


def _package_rels_path(part_name: str) -> str:
    parent, name = posixpath.split(part_name)
    return f"{parent}/_rels/{name}.rels" if parent else f"_rels/{name}.rels"


def _package_content_types(ctx: AssemblyContext) -> tuple[dict[str, str], dict[str, str]]:
    payload = ctx.pkg.read_part_bytes("[Content_Types].xml")
    if payload is None:
        raise RuntimeError("source package has no [Content_Types].xml")
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RuntimeError("source package content types are malformed") from exc
    defaults = {
        item.attrib.get("Extension", "").lower(): item.attrib.get("ContentType", "")
        for item in root.findall(f"{{{NS['ct']}}}Default")
    }
    overrides = {
        item.attrib.get("PartName", "").lstrip("/"): item.attrib.get("ContentType", "")
        for item in root.findall(f"{{{NS['ct']}}}Override")
    }
    return defaults, overrides


def _roundtrip_chart_package(
    node: ShapeNode,
    ctx: AssemblyContext,
    graphic_data: ET.Element | None,
) -> dict[str, Any] | None:
    """Collect the closed source chart dependency graph for exact round-trip."""
    if not ctx.preserve_placeholder_inheritance or graphic_data is None:
        return None
    chart_ref = graphic_data.find(f"{{{CHART_URI}}}chart")
    if chart_ref is None:
        return None
    rel_id = chart_ref.attrib.get(f"{{{NS['r']}}}id")
    chart_part = ctx.slide_part.resolve_rel(rel_id or "")
    if not chart_part or not chart_part.startswith("ppt/charts/"):
        return None

    try:
        defaults, overrides = _package_content_types(ctx)
        pending = [chart_part]
        seen: set[str] = set()
        parts: list[dict[str, str]] = []
        while pending:
            part_name = pending.pop()
            if part_name in seen:
                continue
            if not part_name.startswith(
                ("ppt/charts/", "ppt/embeddings/", "ppt/theme/")
            ):
                return None
            payload = ctx.pkg.read_part_bytes(part_name)
            if payload is None:
                return None
            seen.add(part_name)
            content_type = overrides.get(part_name) or defaults.get(
                posixpath.splitext(part_name)[1].lstrip(".").lower(),
                "",
            )
            parts.append({
                "content_type": content_type,
                "encoding": "base64",
                "name": part_name,
                "payload": base64.b64encode(payload).decode("ascii"),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })

            rels_name = _package_rels_path(part_name)
            rels_payload = ctx.pkg.read_part_bytes(rels_name)
            if rels_payload is None:
                continue
            try:
                rels_root = ET.fromstring(rels_payload)
            except ET.ParseError:
                return None
            for relationship in rels_root.findall(
                f"{{{NS['rel']}}}Relationship"
            ):
                if relationship.attrib.get("TargetMode") == "External":
                    return None
                target = relationship.attrib.get("Target")
                if not target:
                    return None
                resolved = posixpath.normpath(
                    posixpath.join(posixpath.dirname(part_name), target)
                ).lstrip("/")
                if resolved.startswith("../"):
                    return None
                pending.append(resolved)
            parts.append({
                "content_type": "",
                "encoding": "base64",
                "name": rels_name,
                "payload": base64.b64encode(rels_payload).decode("ascii"),
                "sha256": hashlib.sha256(rels_payload).hexdigest(),
            })
    except RuntimeError:
        return None

    frame = copy.deepcopy(node.xml)
    nv_pr = frame.find("p:nvGraphicFramePr/p:nvPr", NS)
    custom_data = nv_pr.find("p:custDataLst", NS) if nv_pr is not None else None
    if custom_data is not None:
        nv_pr.remove(custom_data)
    relationship_attrs = [
        (owner, name)
        for owner in frame.iter()
        for name in owner.attrib
        if isinstance(name, str) and name.startswith(f"{{{NS['r']}}}")
    ]
    if len(relationship_attrs) != 1 or relationship_attrs[0][0].tag != f"{{{CHART_URI}}}chart":
        return None
    frame_payload = ET.tostring(frame, encoding="utf-8")
    return {
        "chart_part": chart_part,
        "frame": {
            "encoding": "base64",
            "payload": base64.b64encode(frame_payload).decode("ascii"),
            "sha256": hashlib.sha256(frame_payload).hexdigest(),
        },
        "parts": sorted(parts, key=lambda item: item["name"]),
    }


def _roundtrip_graphic_frame_metadata(
    node: ShapeNode,
    ctx: AssemblyContext,
    visible_markup: str,
    *,
    top_level: bool,
) -> tuple[str, list[str]]:
    """Preserve one relationship-free native frame behind its SVG fallback."""
    if not ctx.preserve_placeholder_inheritance or not top_level:
        return "", []
    native_frame = copy.deepcopy(node.xml)
    nv_pr = native_frame.find("p:nvGraphicFramePr/p:nvPr", NS)
    custom_data = (
        nv_pr.find("p:custDataLst", NS)
        if nv_pr is not None else None
    )
    if custom_data is not None:
        # Office tags are non-visual, slide-relationship-bound metadata. The
        # validated source package sidecar retains them; the portable native
        # frame omits them so it stays relationship-free on a regenerated slide.
        nv_pr.remove(custom_data)
    if has_relationship_attributes(native_frame):
        return "", []
    raw = ET.tostring(native_frame, encoding="utf-8")
    transform = node.xfrm.to_svg_transform()
    fallback_hash = svg_native_fallback_markup_fingerprint(
        visible_markup,
        root_transform=transform,
        external_markup="".join(ctx.defs),
    )
    metadata = (
        '<metadata data-pptx-part="roundtrip-graphic-frame" '
        'data-pptx-encoding="base64" '
        f'data-pptx-ooxml-sha256="{hashlib.sha256(raw).hexdigest()}">'
        f'{base64.b64encode(raw).decode("ascii")}</metadata>'
    )
    return metadata, [
        'data-pptx-roundtrip-object="graphic-frame"',
        f'{NATIVE_FALLBACK_SHA256_ATTR}="{fallback_hash}"',
    ]


def _render_graphic_table(
    node: ShapeNode,
    ctx: AssemblyContext,
    graphic_data: ET.Element | None,
) -> tuple[str, list[str], str]:
    """Convert the <a:tbl> child of a graphicFrame to SVG plus metadata."""
    if graphic_data is None:
        return "", [], ""
    tbl = graphic_data.find("a:tbl", NS)
    if tbl is None:
        return "", [], ""
    table_styles_part = ctx.pkg.resolve_table_styles()
    result = convert_tbl(
        tbl, node.xfrm, ctx.palette,
        table_styles=(
            table_styles_part.xml if table_styles_part is not None else None
        ),
        theme_fonts=ctx.theme_fonts,
        slide_number=ctx.slide_number,
        id_prefix=f"tbl{ctx.shape_seq[0]}",
        grad_seq=ctx.grad_seq,
        marker_seq=ctx.marker_seq,
        hyperlink_resolver=lambda rid, action: _resolve_svg_hyperlink(
            ctx,
            rid,
            action,
        ),
        strict=ctx.strict,
        diagnostic_sink=ctx.diagnose,
    )
    if result.defs:
        ctx.defs.extend(result.defs)
    replacement_attrs: list[str] = ['data-pptx-import-source="pptx"']
    payload_metadata = ""
    if result.native_payload:
        if node.name and not result.native_payload.get("name"):
            result.native_payload["name"] = node.name
        payload_metadata = _replacement_payload_metadata(result.native_payload)
        replacement_attrs.append('data-pptx-replace-with="table"')
        replacement_attrs.append('data-pptx-native-authority="json"')
    elif result.native_status:
        replacement_attrs.append(
            'data-pptx-replacement-status="'
            f'{_xml_escape(result.native_status)}"'
        )
    if result.effect_reason:
        effect_metadata = unsupported_effect_metadata(result.effect_reason)
        _diagnose_unsupported_effect(ctx, effect_metadata)
        replacement_attrs.extend(_metadata_group_attrs(effect_metadata))
    return result.svg, replacement_attrs, payload_metadata


def _render_graphic_chart(
    node: ShapeNode,
    ctx: AssemblyContext,
    graphic_data: ET.Element | None,
    preview_svg: str,
) -> tuple[str, list[str], str]:
    """Return a chart fallback plus native Chart replacement metadata."""
    result = extract_native_chart_payload(
        graphic_data,
        node.xfrm,
        ctx.slide_part,
        ctx.pkg,
        ctx.palette,
    )
    replacement_attrs: list[str] = ['data-pptx-import-source="pptx"']
    payload_metadata = ""
    source_package = _roundtrip_chart_package(
        node,
        ctx,
        graphic_data,
    )
    if result.native_payload or source_package is not None:
        payload = result.native_payload or {
            "height": round(node.xfrm.h, 3),
            "width": round(node.xfrm.w, 3),
            "x": round(node.xfrm.x, 3),
            "y": round(node.xfrm.y, 3),
        }
        if node.name and not payload.get("name"):
            payload["name"] = node.name
        if source_package is not None:
            payload["source_package"] = source_package
            replacement_attrs.append(
                'data-pptx-roundtrip-object="source-chart-package"'
            )
        payload_metadata = _replacement_payload_metadata(payload)
        replacement_attrs.append('data-pptx-replace-with="chart"')
        replacement_attrs.append('data-pptx-native-authority="json"')
    elif result.native_status:
        replacement_attrs.append(
            'data-pptx-replacement-status="'
            f'{_xml_escape(result.native_status)}"'
        )

    rendered = preview_svg
    if rendered:
        replacement_attrs.append('data-pptx-fallback-kind="source-preview"')
    elif result.normalized_svg:
        rendered = result.normalized_svg
        replacement_attrs.append('data-pptx-fallback-kind="normalized"')
    else:
        replacement_attrs.append('data-pptx-fallback-kind="placeholder"')
    return rendered, replacement_attrs, payload_metadata


def _render_graphic_preview(node: ShapeNode, ctx: AssemblyContext) -> str:
    """Render a graphicFrame's baked fallback preview bitmap when present.

    PowerPoint stores a static raster preview for many embedded graphics
    inside ``mc:AlternateContent``. The Fallback branch is normally a plain
    ``p:pic`` (sometimes nested), so any conformant viewer that can't speak
    the richer object paints the preview. We do the same for flat preview SVGs.

    Falls back to '' when the deck has no Fallback pic (very old or
    third-party authoring tools sometimes omit it). Caller then emits the
    dashed placeholder.
    """
    ac = node.xml.find("a:graphic/a:graphicData/mc:AlternateContent", NS)
    if ac is None:
        return ""
    pic = ac.find("mc:Fallback//p:pic", NS)
    if pic is None:
        # Some authoring tools put the preview directly in mc:Choice.
        pic = ac.find("mc:Choice//p:pic", NS)
        if pic is None:
            return ""

    # The inner pic carries its own absolute xfrm in this deck (and in every
    # well-formed PPTX I've seen — PowerPoint copies the graphicFrame xfrm
    # there during save). If it's missing, fall back to the graphicFrame's
    # xfrm so the preview at least lands somewhere visible.
    inner_xfrm = node.xfrm
    pic_xfrm_elem = pic.find("p:spPr/a:xfrm", NS)
    if pic_xfrm_elem is not None:
        from .emu_units import parse_xfrm
        parsed = parse_xfrm(pic_xfrm_elem)
        if parsed.w > 0 and parsed.h > 0:
            inner_xfrm = parsed

    result = convert_picture(
        pic, inner_xfrm, ctx.slide_part, ctx.pkg,
        media_subdir=ctx.media_subdir,
        embed_inline=ctx.embed_images,
        asset_name_map=ctx.asset_name_map,
        strict=ctx.strict,
    )
    if not result.svg:
        return ""
    _diagnose_picture_result(ctx, result)
    ctx.media.update(result.media)
    return result.svg


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def _emit_background(slide: SlideRef, ctx: AssemblyContext,
                     w: float, h: float) -> str:
    """Inspect <p:bg> on slide / layout / master in inheritance order."""
    for part in (slide.part, slide.layout, slide.master):
        if part is None:
            continue
        bg = get_background(part.xml)
        if bg is None:
            continue
        bg_pr = bg.find("p:bgPr", NS)
        bg_ref = bg.find("p:bgRef", NS)
        placeholder_hex = None

        if bg_pr is None and bg_ref is not None:
            bg_pr = _theme_background_fill(slide, ctx, bg_ref)
            color_elem = find_color_elem(bg_ref)
            placeholder_hex, _ = resolve_color(color_elem, ctx.palette)
        if bg_pr is None:
            continue

        bg_image = _emit_background_image(bg_pr, part, ctx, w, h)
        if bg_image:
            return bg_image

        fill = resolve_fill(
            bg_pr, ctx.palette,
            id_prefix="bg", id_seq=ctx.grad_seq,
            placeholder_hex=placeholder_hex,
        )
        ctx.defs.extend(fill.defs)
        if not fill.attrs:
            return ""
        # Convert dict to attributes
        attrs_xml = _attrs_to_xml(fill.attrs)
        return (f'<rect x="0" y="0" width="{fmt_num(w)}" height="{fmt_num(h)}"'
                f"{attrs_xml}/>")
    return ""


def _emit_part_background(slide: SlideRef, ctx: AssemblyContext,
                          w: float, h: float) -> str:
    """Render the background declared on the part itself only.

    Distinct from `_emit_background`, which walks the slide → layout →
    master inheritance chain. Used by the layered solo renderer so each
    standalone master / layout SVG carries only its own ``<p:bg>`` — the
    inheritance is rebuilt by consumers re-stacking the layers, and we'd
    rather output nothing than have master decoration leak into a layout
    file.
    """
    bg = get_background(slide.part.xml)
    if bg is None:
        return ""
    bg_pr = bg.find("p:bgPr", NS)
    bg_ref = bg.find("p:bgRef", NS)
    placeholder_hex = None

    if bg_pr is None and bg_ref is not None:
        bg_pr = _theme_background_fill(slide, ctx, bg_ref)
        color_elem = find_color_elem(bg_ref)
        placeholder_hex, _ = resolve_color(color_elem, ctx.palette)
    if bg_pr is None:
        return ""

    bg_image = _emit_background_image(bg_pr, slide.part, ctx, w, h)
    if bg_image:
        return bg_image

    fill = resolve_fill(
        bg_pr, ctx.palette,
        id_prefix="bg", id_seq=ctx.grad_seq,
        placeholder_hex=placeholder_hex,
    )
    ctx.defs.extend(fill.defs)
    if not fill.attrs:
        return ""
    attrs_xml = _attrs_to_xml(fill.attrs)
    return (f'<rect x="0" y="0" width="{fmt_num(w)}" height="{fmt_num(h)}"'
            f"{attrs_xml}/>")


def _emit_background_image(
    bg_pr: ET.Element,
    source_part: PartRef,
    ctx: AssemblyContext,
    w: float,
    h: float,
) -> str:
    """Render a slide/layout/master background image fill as a full-canvas image."""
    blip_fill = bg_pr.find("a:blipFill", NS)
    if blip_fill is None:
        return ""

    result = convert_blip_fill(
        blip_fill,
        Xfrm(0.0, 0.0, w, h),
        source_part,
        ctx.pkg,
        media_subdir=ctx.media_subdir,
        embed_inline=ctx.embed_images,
        asset_name_map=ctx.asset_name_map,
        strict=ctx.strict,
    )
    _diagnose_picture_result(ctx, result)
    if result.media:
        ctx.media.update(result.media)
    return result.svg


def _theme_background_fill(
    slide: SlideRef,
    ctx: AssemblyContext,
    bg_ref: ET.Element,
) -> ET.Element | None:
    """Resolve p:bgRef idx into the theme background fill style list."""
    def reject_invalid_idx(message: str) -> None:
        if ctx.strict:
            raise ValueError(message)
        ctx.diagnose(
            "theme-background-reference-omitted",
            message,
            "omit this part's theme background fill",
        )

    idx_raw = bg_ref.attrib.get("idx")
    if not idx_raw:
        reject_invalid_idx(
            "Invalid p:bgRef@idx: expected a 1001-based theme fill index"
        )
        return None
    try:
        idx = int(idx_raw)
    except ValueError:
        reject_invalid_idx(
            f"Invalid p:bgRef@idx value {idx_raw!r}; expected a 1001-based "
            "theme fill index"
        )
        return None
    # ECMA style matrix background fill references are 1001-based.
    bg_fill_index = idx - 1001
    if bg_fill_index < 0:
        reject_invalid_idx(
            f"Invalid p:bgRef@idx value {idx_raw!r}; expected a value of 1001 "
            "or greater"
        )
        return None

    theme = ctx.pkg.resolve_theme(slide.master)
    if theme is None:
        return None
    fill_list = theme.xml.find(".//a:fmtScheme/a:bgFillStyleLst", NS)
    if fill_list is None:
        return None
    fills = [child for child in list(fill_list) if isinstance(child.tag, str)]
    if bg_fill_index >= len(fills):
        reject_invalid_idx(
            f"Invalid p:bgRef@idx value {idx_raw!r}; theme background fill list "
            f"contains {len(fills)} entries"
        )
        return None
    return fills[bg_fill_index]


def _emit_inherited_shapes(slide: SlideRef, ctx: AssemblyContext) -> list[str]:
    parts: list[str] = []
    show_layout_shapes, show_master_shapes = inherited_shape_visibility(slide)
    inherited_parts = (
        ("master-", slide.master, show_master_shapes),
        ("layout-", slide.layout, show_layout_shapes),
    )
    for prefix, part, visible in inherited_parts:
        if part is None or not visible:
            continue
        original_part = ctx.slide_part
        original_prefix = ctx.group_id_prefix
        ctx.slide_part = part
        ctx.group_id_prefix = prefix
        try:
            for node in walk_sp_tree(part.xml):
                if _is_placeholder_node(node):
                    continue
                chunk = _convert_node(node, ctx, top_level=True)
                if chunk:
                    parts.append(chunk)
        finally:
            ctx.slide_part = original_part
            ctx.group_id_prefix = original_prefix
    return parts


def _is_placeholder_node(node: ShapeNode) -> bool:
    if node.placeholder is not None:
        return True
    if node.kind == GROUP:
        return all(_is_placeholder_node(child) for child in node.children)
    return False


def _convert_placeholder_guide(node: ShapeNode, ctx: AssemblyContext,
                               *, top_level: bool) -> str:
    """Emit the source-authored appearance of one template placeholder."""
    return _convert_node(node, ctx, top_level=top_level)


# ---------------------------------------------------------------------------
# Wrap / utilities
# ---------------------------------------------------------------------------

def _wrap_shape_group(
    inner: str,
    node: ShapeNode,
    ctx: AssemblyContext,
    *,
    top_level: bool,
    extra_attrs: list[str] | None = None,
) -> str:
    """Wrap a shape's body in a <g> that carries the transform (rotation /
    flip) and an id for animation anchoring."""
    if not inner.strip():
        return ""

    transform = node.xfrm.to_svg_transform()
    ctx.shape_seq[0] += 1
    seq = ctx.shape_seq[0]
    sid = node.spid or str(seq)
    g_id = f"{ctx.group_id_prefix}shape-{sid}"

    attrs: list[str] = [f'id="{g_id}"']
    attrs.extend(
        f'{key}="{_xml_escape(value)}"'
        for key, value in _object_metadata(
            node,
            ctx,
            fallback_shape_id=sid,
        ).items()
    )
    if node.name:
        attrs.append(f'data-name="{_xml_escape(node.name)}"')
    if node.placeholder is not None and node.kind == SHAPE:
        sp_pr = node.xml.find("p:spPr", NS)
        if sp_pr is not None and any(
            sp_pr.find(path, NS) is not None
            for path in ("a:prstGeom", "a:custGeom")
        ):
            attrs.append('data-pptx-placeholder-local-geometry="true"')
    if extra_attrs:
        attrs.extend(extra_attrs)
        if any(
            attribute.split("=", 1)[0] == "data-pptx-replace-with"
            for attribute in extra_attrs
        ) and not any(
            attribute.split("=", 1)[0] == NATIVE_FALLBACK_SHA256_ATTR
            for attribute in extra_attrs
        ):
            fallback_hash = svg_native_fallback_markup_fingerprint(
                inner,
                root_transform=transform,
                external_markup="".join(ctx.defs),
            )
            attrs.append(
                f'{NATIVE_FALLBACK_SHA256_ATTR}="{fallback_hash}"'
            )
    if transform:
        attrs.append(f'transform="{transform}"')
    group_xml = f"<g {' '.join(attrs)}>\n{inner}\n</g>"
    if node.hyperlink_rid or node.hyperlink_action:
        href = _resolve_svg_hyperlink(
            ctx,
            node.hyperlink_rid,
            node.hyperlink_action,
        )
        if href is not None and '<a href=' in inner:
            attrs.append(
                f'{SHAPE_HYPERLINK_ATTR}="{_xml_escape(href)}"'
            )
            return f"<g {' '.join(attrs)}>\n{inner}\n</g>"
        if href is not None:
            return f'<a href="{_xml_escape(href)}">{group_xml}</a>'
    return group_xml


def _attrs_to_xml(attrs: dict[str, str]) -> str:
    if not attrs:
        return ""
    return "".join(f' {key}="{_xml_escape(value)}"' for key, value in attrs.items())


def _metadata_group_attrs(attrs: dict[str, str]) -> list[str]:
    """Serialize import metadata for a logical object wrapper."""
    return [
        f'{key}="{_xml_escape(value)}"'
        for key, value in attrs.items()
    ]


def _diagnose_unsupported_effect(
    ctx: AssemblyContext,
    metadata: dict[str, str],
) -> None:
    """Copy an import-only blocking effect marker into the conversion report."""
    reason = metadata.get(EFFECT_REASON_ATTR)
    if reason is None:
        return
    ctx.diagnose(
        "effect-unsupported",
        reason,
        "retain the base object and record blocking effect metadata",
    )


def _geometry_group_attrs(geom: GeomResult | None) -> list[str]:
    """Mirror native geometry semantics onto the logical shape container."""
    if geom is None:
        return []
    keys = (
        "data-pptx-prst",
        "data-pptx-geometry-kind",
        "data-pptx-geometry-sha256",
        "data-pptx-preview-sha256",
        "data-pptx-geometry-status",
        "data-pptx-geometry-reason",
        EFFECT_STATUS_ATTR,
        EFFECT_REASON_ATTR,
        NATIVE_EFFECT_ATTR,
        NATIVE_EFFECT_SHA256_ATTR,
    )
    attrs: list[str] = []
    for key, value in geom.attrs.items():
        if key in keys or key.startswith("data-pptx-av-"):
            attrs.append(f'{key}="{_xml_escape(value)}"')
    return attrs


def _object_metadata(
    node: ShapeNode,
    ctx: AssemblyContext,
    *,
    fallback_shape_id: str = "",
) -> dict[str, str]:
    """Describe the source object without coupling geometry to its SVG bounds."""
    object_kind = {
        SHAPE: "shape",
        PICTURE: "picture",
        CONNECTOR: "connector",
        GROUP: "group",
        GRAPHIC: "graphic-frame",
    }.get(node.kind, node.kind)
    shape_id = node.spid or fallback_shape_id
    frame = " ".join((
        fmt_num(node.xfrm.x, 8),
        fmt_num(node.xfrm.y, 8),
        fmt_num(node.xfrm.w, 8),
        fmt_num(node.xfrm.h, 8),
    ))
    attrs = {
        "data-pptx-object": object_kind,
        "data-pptx-shape-id": shape_id,
        "data-pptx-shape-scope": _shape_scope(ctx),
        "data-pptx-frame": frame,
    }
    if node.name:
        attrs["data-pptx-shape-name"] = node.name
    if node.placeholder is not None:
        if node.placeholder.type:
            attrs["data-ph-type"] = node.placeholder.type
        if node.placeholder.idx is not None:
            attrs["data-pptx-placeholder-index"] = node.placeholder.idx
        if node.placeholder.sz is not None:
            attrs["data-pptx-placeholder-size"] = node.placeholder.sz
        if node.placeholder.orient is not None:
            attrs["data-pptx-placeholder-orientation"] = node.placeholder.orient
    if node.kind == CONNECTOR:
        attrs.update(_connector_metadata(node, _shape_scope(ctx)))
    return attrs


def _shape_scope(ctx: AssemblyContext) -> str:
    if ctx.group_id_prefix.startswith("master-"):
        return "master"
    if ctx.group_id_prefix.startswith("layout-"):
        return "layout"
    return "slide"


def _connector_metadata(node: ShapeNode, scope: str) -> dict[str, str]:
    """Preserve connector endpoint references when PowerPoint declares them."""
    attrs: dict[str, str] = {}
    cnv = node.xml.find("p:nvCxnSpPr/p:cNvCxnSpPr", NS)
    if cnv is None:
        return attrs

    for endpoint, prefix in (("stCxn", "start"), ("endCxn", "end")):
        connection = cnv.find(f"a:{endpoint}", NS)
        if connection is None:
            continue
        shape_id = connection.attrib.get("id")
        site = connection.attrib.get("idx")
        if shape_id is not None:
            attrs[f"data-pptx-{prefix}-shape-id"] = shape_id
            attrs[f"data-pptx-{prefix}-shape-scope"] = scope
        if site is not None:
            attrs[f"data-pptx-{prefix}-site"] = site
    return attrs


def _xml_escape(text: str) -> str:
    return _xml_text_escape(text).replace('"', "&quot;")


def _xml_text_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))
