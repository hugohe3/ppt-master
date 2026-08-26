"""Top-level orchestrator for PPTX -> SVG conversion.

Public API: convert_pptx_to_svg(pptx_path, output_dir, options).

Composes the per-slide pipeline:
    OoxmlPackage -> shape_walker.walk_sp_tree
                 -> per-shape dispatch (prstgeom / txbody / pic / ...)
                 -> assembled SVG text + extracted media files

Stages B-F will fill in the per-shape dispatch. For Stage A this entry just
loads the package and reports basic per-slide structure to verify wiring.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from html import unescape
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit
from xml.etree import ElementTree as ET
from xml.sax.saxutils import quoteattr

from extract_svg_assets import extract_directory
from pptx_embedded_fonts import (
    FONT_BUNDLE_DIR,
    EmbeddedFontBundle,
    EmbeddedFontError,
    capture_embedded_fonts,
    write_embedded_font_bundle,
)
from pptx_workspace import (
    AUTHORING_SVG_DIR,
    AUTHORING_SVG_FLAT_DIR,
    CONVERSION_REPORT_PATH,
    NATIVE_STRUCTURE_PATH,
    ROUNDTRIP_FLAT_SVG_DIR,
    ROUNDTRIP_LAYERED_SVG_DIR,
    ROUNDTRIP_MANIFEST_PATH,
    SOURCE_PPTX_PATH,
    PackageResourceInventory,
    conversion_report_path,
    inventory_package_resources,
    reject_removed_workspace_layout,
    slide_animation_config_sha256,
    write_workspace_resources,
)
from svg_authoring_view import project_svg_batch
from svg_to_pptx.animation_config import (
    validate_animation_config_errors,
    validate_transition_config,
)
from template_import.manifest import (
    count_drawable_shapes,
    extract_placeholders,
    part_display_name,
)
from template_import.native_structure import (
    CONTRACT_NAME as NATIVE_STRUCTURE_NAME,
    SOURCE_TEMPLATE_NAME,
    build_native_structure,
)

from .animation_import import (
    AnimationImportError,
    import_slide_animation,
)
from .color_resolver import ColorPalette
from .emu_units import NS
from .import_diagnostics import ImportDiagnostic, append_diagnostic
from .ooxml_loader import (
    OoxmlPackage,
    PartRef,
    SlideRef,
    part_show_master_sp,
)
from .notes_import import ImportedSpeakerNote, import_speaker_notes
from .slide_to_svg import assemble_part_solo, assemble_slide
from .transition_import import (
    TransitionImportError,
    import_slide_transition,
)


_CJK_THEME_SCRIPTS = frozenset({"Hans", "Hant", "Jpan", "Hang"})
_MANAGED_PRIMARY_SVG_RE = re.compile(
    r"(?:slide_\d+|master_\d+_[A-Za-z0-9_-]+|layout_\d+_[A-Za-z0-9_-]+)\.svg"
)
_MANAGED_FLAT_SVG_RE = re.compile(r"slide_\d+\.svg")
_MANAGED_TRANSITION_SOUND_RE = re.compile(
    r"transition_sound_[0-9a-f]{16}\.wav"
)
_ROUNDTRIP_VECTOR_MIN_DRAWABLES = 2
_ROUNDTRIP_VECTOR_MIN_BYTES = 512
_ROUNDTRIP_VECTOR_MIN_DECORATION_BYTES = 512
_SVG_HREF_RE = re.compile(
    r"\b(?:href|xlink:href)\s*=\s*[\"']([^\"']+)[\"']"
)
_SVG_HREF_ATTRIBUTE_RE = re.compile(
    r"(?P<prefix>\b(?:href|xlink:href)\s*=\s*)"
    r"(?P<quote>[\"'])(?P<value>[^\"']+)(?P=quote)"
)


def _validate_resource_subdir(value: str) -> None:
    """Reject media output paths that can escape the conversion workspace."""
    path = Path(value)
    if path.drive or path.anchor or path.is_absolute() or ".." in path.parts:
        raise ValueError(
            f"resource subdirectory must stay within the output workspace: {value!r}"
        )


def _validate_media_filename(filename: str) -> None:
    """Require one media basename so asset maps cannot redirect writes."""
    path = Path(filename)
    if (
        not filename
        or filename in {".", ".."}
        or path.drive
        or path.anchor
        or path.name != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise ValueError(f"Media filename must be a basename: {filename!r}")


def _extract_theme_info(
    theme: PartRef,
    palette: ColorPalette,
) -> tuple[dict[str, str], dict[str, str]]:
    from .color_resolver import find_color_elem, resolve_color

    colors: dict[str, str] = {}
    fonts: dict[str, str] = {}

    scheme = theme.xml.find(".//a:clrScheme", NS)
    if scheme is not None:
        for child in list(scheme):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}", 1)[-1]
            try:
                color_elem = find_color_elem(child)
                hex_, _ = resolve_color(color_elem, palette)
            except ValueError as exc:
                if palette.strict:
                    raise
                palette._diagnose(
                    "theme-summary-color-omitted",
                    str(exc),
                    "omit only this malformed theme-summary color",
                )
                continue
            if hex_:
                colors[name] = hex_

    font_scheme = theme.xml.find(".//a:fontScheme", NS)
    if font_scheme is not None:
        for slot in ("majorFont", "minorFont"):
            fnt = font_scheme.find(f"a:{slot}", NS)
            if fnt is None:
                continue
            role_prefix = "major" if slot == "majorFont" else "minor"
            latin = fnt.find("a:latin", NS)
            if latin is not None and latin.attrib.get("typeface"):
                fonts[f"{role_prefix}Latin"] = latin.attrib["typeface"]
            ea = fnt.find("a:ea", NS)
            if ea is not None and ea.attrib.get("typeface"):
                fonts[f"{role_prefix}EastAsia"] = ea.attrib["typeface"]
            cs = fnt.find("a:cs", NS)
            if cs is not None and cs.attrib.get("typeface"):
                fonts[f"{role_prefix}ComplexScript"] = cs.attrib["typeface"]
            for supplemental in fnt.findall("a:font", NS):
                script = supplemental.attrib.get("script", "")
                typeface = supplemental.attrib.get("typeface", "")
                if script in _CJK_THEME_SCRIPTS and typeface:
                    fonts[f"{role_prefix}Script{script}"] = typeface

    return colors, fonts


@dataclass
class ConvertOptions:
    """Convert behavior knobs.

    images_subdir: where to write image files relative to output_dir. SVG image
        href will use './<images_subdir>/<filename>'.
    sound_subdir: where to write transition/object cue audio relative to
        output_dir. New workspaces use ``sounds``.
    embed_images: when True, base64-encode images inline instead of writing
        files. Default False (matches svg_to_pptx default of external images).
    keep_hidden: include shapes marked hidden="1". Default False.
    inheritance_mode: how to render master/layout shapes per slide SVG.
        - "both" (default): emit both views — layered under svg/ for template
          designers (master/layout/slide as separate files) and flat under
          svg-flat/ for previewers (each slide self-contained). Costs roughly
          1.3-1.5× converter time and ~1.6-2× disk vs. either single mode.
        - "layered": skip inherited shapes inside the slide. The orchestrator
          renders every master and layout to its own SVG, plus
          svg/inheritance.json describing the reuse graph. Optimised for
          template authors who need to see "what is shared vs. unique".
        - "flat": inline the inherited shapes visible under the source
          ``showMasterSp`` flags for preview pages and screenshot pipelines.
    strict: stop on the first unsupported or malformed source construct.
        Default False keeps usable content and records structured diagnostics.
    roundtrip: create the fixed semantic workspace and source-preserving
        package contracts used by the editable ``authoring-svg-flat/`` route.
    """

    images_subdir: str = "images"
    sound_subdir: str = "sounds"
    embed_images: bool = False
    keep_hidden: bool = False
    inheritance_mode: str = "both"
    asset_name_map: dict[str, str] = field(default_factory=dict)
    strict: bool = False
    roundtrip: bool = False


@dataclass
class PartArtifact:
    """Result of converting a master or layout part to SVG (layered mode only)."""

    role: str  # "master" | "layout"
    part_path: str  # OOXML part path, e.g. "ppt/slideLayouts/slideLayout3.xml"
    filename: str  # output svg filename, e.g. "layout_03_title.xml.svg"
    svg: str
    media_files: dict[str, bytes] = field(default_factory=dict)
    parent_master_part_path: str | None = None
    theme_part_path: str | None = None
    show_master_shapes: bool = True


@dataclass
class SlideArtifact:
    """Result of converting a single slide."""

    index: int  # 1-based
    svg: str
    media_files: dict[str, bytes] = field(default_factory=dict)
    layout_part_path: str | None = None
    master_part_path: str | None = None
    show_inherited_shapes: bool = True


@dataclass
class ConvertResult:
    """Result of converting an entire .pptx.

    ``slides`` holds the layered/primary view (or, in pure flat mode, the flat
    view). ``flat_slides`` is populated only in ``"both"`` mode and contains
    self-contained renderings of every slide; callers that don't care about
    the flat view can ignore it.
    """

    slides: list[SlideArtifact] = field(default_factory=list)
    canvas_px: tuple[float, float] = (1280.0, 720.0)
    theme_colors: dict[str, str] = field(default_factory=dict)
    theme_fonts: dict[str, str] = field(default_factory=dict)
    theme_xml: bytes | None = None
    embedded_fonts: EmbeddedFontBundle | None = None
    resource_inventory: PackageResourceInventory = field(
        default_factory=PackageResourceInventory
    )
    speaker_notes: tuple[ImportedSpeakerNote, ...] = ()
    native_structure: dict[str, object] | None = None
    source_pptx_path: Path | None = None
    layouts: list[PartArtifact] = field(default_factory=list)
    masters: list[PartArtifact] = field(default_factory=list)
    flat_slides: list[SlideArtifact] = field(default_factory=list)
    master_themes: dict[str, dict[str, object]] = field(default_factory=dict)
    diagnostics: list[ImportDiagnostic] = field(default_factory=list)
    animation_config: dict[str, object] = field(
        default_factory=lambda: {
            "version": 1,
            "defaults": {
                "transition": {
                    "effect": "none",
                    "duration": 0.0,
                },
            },
            "slides": {},
        }
    )
    animation_media_files: dict[str, bytes] = field(default_factory=dict)
    source_file: str = ""
    strict: bool = False


def _palette_diagnostic_sink(
    result: ConvertResult,
    *,
    part_path: str,
    slide_index: int | None = None,
) -> Callable[[str, str, str], None]:
    """Build a package-level diagnostic sink for palette initialization."""
    def _record(code: str, message: str, fallback: str) -> None:
        append_diagnostic(
            result.diagnostics,
            ImportDiagnostic(
                code=code,
                message=message,
                fallback=fallback,
                part_path=part_path,
                slide_index=slide_index,
            ),
        )

    return _record


def _roundtrip_native_structure(
    pkg: OoxmlPackage,
    pptx_path: Path,
) -> dict[str, object]:
    """Build the existing validated source-structure contract without assets."""
    masters = list(pkg.iter_all_masters())
    layouts_with_parents = list(pkg.iter_all_layouts_with_parent())
    slides = list(pkg.iter_slides())
    used_layouts: dict[str, list[int]] = {}
    used_masters: dict[str, list[int]] = {}
    for slide in slides:
        if slide.layout is not None:
            used_layouts.setdefault(slide.layout.path, []).append(slide.index)
        if slide.master is not None:
            used_masters.setdefault(slide.master.path, []).append(slide.index)

    manifest: dict[str, object] = {
        "slideSize": {
            "width_emu": pkg.slide_size_emu[0],
            "height_emu": pkg.slide_size_emu[1],
            "width_px": pkg.slide_size_px[0],
            "height_px": pkg.slide_size_px[1],
        },
        "masters": [
            {
                "path": master.path,
                "displayName": part_display_name(master.xml, master.path),
                "drawableShapeCount": count_drawable_shapes(master.xml),
                "usedBySlides": used_masters.get(master.path, []),
            }
            for master in masters
        ],
        "layouts": [
            {
                "path": layout.path,
                "displayName": part_display_name(layout.xml, layout.path),
                "parentPath": master.path,
                "showMasterShapes": part_show_master_sp(layout),
                "drawableShapeCount": count_drawable_shapes(layout.xml),
                "placeholders": extract_placeholders(layout.xml),
                "usedBySlides": used_layouts.get(layout.path, []),
            }
            for layout, master in layouts_with_parents
        ],
        "slides": [
            {
                "index": slide.index,
                "slidePath": slide.part.path,
                "layoutPath": slide.layout.path if slide.layout else None,
                "masterPath": slide.master.path if slide.master else None,
                "showInheritedShapes": part_show_master_sp(slide.part),
                "placeholders": extract_placeholders(slide.part.xml),
                "svgFile": f"slide_{slide.index:02d}.svg",
            }
            for slide in slides
        ],
    }
    contract = build_native_structure(pptx_path, manifest)
    if not contract["strategy"]["preservationEligible"]:
        raise RuntimeError(
            "Round-trip mode requires a complete source master/layout graph"
        )
    return contract


def _annotate_roundtrip_slide_roots(
    slides: list[SlideArtifact],
    contract: dict[str, object],
) -> None:
    """Attach exact Layout identity to layered SVG roots for reverse export."""
    raw_layouts = contract.get("layouts")
    raw_masters = contract.get("masters")
    raw_slides = contract.get("slides")
    if not all(isinstance(value, list) for value in (
        raw_layouts,
        raw_masters,
        raw_slides,
    )):
        raise RuntimeError("Generated round-trip source structure is incomplete")
    layouts = {
        str(item.get("key")): item
        for item in raw_layouts
        if isinstance(item, dict)
    }
    masters = {
        str(item.get("key")): item
        for item in raw_masters
        if isinstance(item, dict)
    }
    slide_rows = {
        int(item["index"]): item
        for item in raw_slides
        if isinstance(item, dict) and isinstance(item.get("index"), int)
    }
    for slide in slides:
        row = slide_rows.get(slide.index)
        if row is None:
            raise RuntimeError(
                f"Round-trip source structure has no slide {slide.index}"
            )
        layout_key = str(row.get("layoutKey") or "")
        master_key = str(row.get("masterKey") or "")
        layout = layouts.get(layout_key)
        master = masters.get(master_key)
        if layout is None or master is None:
            raise RuntimeError(
                f"Round-trip slide {slide.index} has an unresolved Layout/Master"
            )
        attrs = {
            "data-pptx-layout": layout_key,
            "data-pptx-layout-name": str(layout.get("name") or layout_key),
            "data-pptx-master": master_key,
            "data-pptx-master-name": str(master.get("name") or master_key),
            "data-pptx-show-master-shapes": (
                "true" if layout.get("showMasterShapes", True) else "false"
            ),
            "data-pptx-show-inherited-shapes": (
                "true" if row.get("showInheritedShapes", True) else "false"
            ),
        }
        marker = slide.svg.find(">")
        if not slide.svg.startswith("<svg ") or marker < 0:
            raise RuntimeError(
                f"Round-trip slide {slide.index} does not have a canonical SVG root"
            )
        serialized = "".join(
            f" {name}={quoteattr(value)}"
            for name, value in attrs.items()
        )
        slide.svg = slide.svg[:marker] + serialized + slide.svg[marker:]


def _make_palette(
    master: PartRef | None,
    theme: PartRef | None,
    options: ConvertOptions,
    result: ConvertResult,
    *,
    part_path: str,
    slide_index: int | None = None,
) -> ColorPalette:
    """Create one strict or tolerant palette with structured diagnostics."""
    return ColorPalette(
        master,
        theme,
        strict=options.strict,
        diagnostic_sink=_palette_diagnostic_sink(
            result,
            part_path=part_path,
            slide_index=slide_index,
        ),
    )


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def convert_pptx_to_svg(
    pptx_path: Path,
    output_dir: Path | None = None,
    options: ConvertOptions | None = None,
) -> ConvertResult:
    """Convert a .pptx file to one SVG per slide.

    Args:
        pptx_path: Source .pptx file.
        output_dir: When given, write svg/<slide_NN>.svg + media files there.
            When None, files are not written; callers can read SlideArtifact.svg.
        options: ConvertOptions; defaults to ConvertOptions().

    Returns:
        ConvertResult with per-slide SVG strings and resolved theme info.
    """
    options = options or ConvertOptions()
    if options.inheritance_mode not in {"flat", "layered", "both"}:
        raise ValueError(
            f"inheritance_mode must be 'flat', 'layered', or 'both', "
            f"got {options.inheritance_mode!r}"
        )
    if options.roundtrip and options.inheritance_mode != "both":
        raise ValueError(
            "roundtrip requires inheritance_mode 'both' so the editable flat "
            "authoring view and layered source backing are both complete"
        )
    if options.roundtrip and (
        options.images_subdir != "images"
        or options.sound_subdir != "sounds"
        or options.embed_images
    ):
        raise ValueError(
            "roundtrip uses fixed images/ and sounds/ resource directories "
            "and does not support inline images"
        )
    if not options.embed_images:
        _validate_resource_subdir(options.images_subdir)
    _validate_resource_subdir(options.sound_subdir)
    emit_layered = options.inheritance_mode in {"layered", "both"}
    emit_flat = options.inheritance_mode in {"flat", "both"}
    result = ConvertResult(
        source_file=pptx_path.name,
        strict=options.strict,
    )

    with OoxmlPackage(pptx_path) as pkg:
        if pkg.zip is not None:
            result.resource_inventory = inventory_package_resources(pkg.zip)
            image_name_map = result.resource_inventory.image_name_map()
            image_name_map.update(options.asset_name_map)
            options = replace(options, asset_name_map=image_name_map)
        result.speaker_notes = import_speaker_notes(pkg)
        result.canvas_px = pkg.slide_size_px

        # Default theme summary is kept for compatibility; conversion itself
        # resolves palette/fonts per slide master.
        first_slide = pkg.get_slide(1)
        default_master = first_slide.master if first_slide else None
        default_theme = pkg.resolve_theme(default_master)
        palette = _make_palette(
            default_master,
            default_theme,
            options,
            result,
            part_path=default_theme.path if default_theme is not None else "",
        )
        if default_theme is not None:
            result.theme_colors, result.theme_fonts = _extract_theme_info(default_theme, palette)
            result.theme_xml = ET.tostring(default_theme.xml, encoding="utf-8")
        if pkg.presentation is not None and pkg.zip is not None:
            try:
                result.embedded_fonts = capture_embedded_fonts(
                    pkg.presentation.xml,
                    pkg.presentation.rels,
                    pkg.zip.read,
                )
            except EmbeddedFontError as exc:
                if options.strict:
                    raise
                append_diagnostic(
                    result.diagnostics,
                    ImportDiagnostic(
                        code="embedded-fonts-omitted",
                        message=str(exc),
                        fallback=(
                            "keep editable text and rely on an installed or "
                            "substitute font"
                        ),
                        part_path=pkg.presentation.path,
                    ),
                )

        for master in pkg.iter_all_masters():
            theme = pkg.resolve_theme(master) or default_theme
            pal = _make_palette(
                master,
                theme,
                options,
                result,
                part_path=master.path,
            )
            colors, fonts = _extract_theme_info(theme, pal) if theme is not None else ({}, {})
            result.master_themes[master.path] = {
                "themePath": theme.path if theme is not None else None,
                "colors": colors,
                "fonts": fonts,
            }

        # Per-slide conversion. The primary view is layered when emitted
        # (template designers care most about that one); the flat view is
        # rendered alongside when needed.
        primary_mode = "layered" if emit_layered else "flat"
        for slide in pkg.iter_slides():
            _read_back_slide_transition(
                pkg,
                slide,
                result,
                options,
            )
            slide_theme = pkg.resolve_theme(slide.master) or default_theme
            slide_palette = _make_palette(
                slide.master,
                slide_theme,
                options,
                result,
                part_path=slide.part.path,
                slide_index=slide.index,
            )
            _colors, slide_fonts = (
                _extract_theme_info(slide_theme, slide_palette)
                if slide_theme is not None
                else ({}, result.theme_fonts)
            )
            artifact = _convert_slide(
                pkg,
                slide,
                slide_palette,
                options,
                result.diagnostics,
                slide_fonts,
                inheritance_mode=primary_mode,
            )
            result.slides.append(artifact)
            _read_back_slide_animation(
                pkg,
                slide,
                artifact,
                result,
                options,
            )
        if emit_layered and emit_flat:
            for slide in pkg.iter_slides():
                slide_theme = pkg.resolve_theme(slide.master) or default_theme
                slide_palette = _make_palette(
                    slide.master,
                    slide_theme,
                    options,
                    result,
                    part_path=slide.part.path,
                    slide_index=slide.index,
                )
                _colors, slide_fonts = (
                    _extract_theme_info(slide_theme, slide_palette)
                    if slide_theme is not None
                    else ({}, result.theme_fonts)
                )
                artifact = _convert_slide(
                    pkg,
                    slide,
                    slide_palette,
                    options,
                    result.diagnostics,
                    slide_fonts,
                    inheritance_mode="flat",
                )
                result.flat_slides.append(artifact)

        # Layered mode: also render each master / layout once.
        if emit_layered:
            _convert_inheritance_parts(pkg, default_theme, options, result)
        if options.roundtrip:
            result.native_structure = _roundtrip_native_structure(pkg, pptx_path)
            result.source_pptx_path = pptx_path
            _annotate_roundtrip_slide_roots(
                result.slides,
                result.native_structure,
            )

    if output_dir is not None:
        _write_artifacts(output_dir, result, options)

    return result


def _read_back_slide_transition(
    pkg: OoxmlPackage,
    slide: SlideRef,
    result: ConvertResult,
    options: ConvertOptions,
) -> None:
    """Recover one supported slide transition into the sidecar."""
    try:
        transition = import_slide_transition(
            pkg,
            slide,
            media_subdir=options.sound_subdir,
            resource_path_map=result.resource_inventory.path_map(),
        )
    except TransitionImportError as exc:
        message = f"Slide transition was not reconstructed: {exc}"
        if options.strict:
            raise ValueError(message) from exc
        append_diagnostic(
            result.diagnostics,
            ImportDiagnostic(
                code="transition-not-reconstructed",
                message=message,
                fallback=(
                    "keep this transition in the source PPTX through direct "
                    "native preservation"
                ),
                part_path=slide.part.path,
                slide_index=slide.index,
            ),
        )
    else:
        if transition is not None:
            slides = result.animation_config["slides"]
            if not isinstance(slides, dict):
                raise RuntimeError("internal animations.json slides must be an object")
            slides[f"slide_{slide.index:02d}"] = {
                "transition": transition.config,
            }
            for filename, payload in transition.media_files.items():
                existing = result.animation_media_files.get(filename)
                if existing is not None and existing != payload:
                    raise RuntimeError(
                        "Transition sound filename collision with different bytes: "
                        f"{filename}"
                    )
                result.animation_media_files[filename] = payload



def _read_back_slide_animation(
    pkg: OoxmlPackage,
    slide: SlideRef,
    artifact: SlideArtifact,
    result: ConvertResult,
    options: ConvertOptions,
) -> None:
    """Recover one finite object-animation sequence into the sidecar."""
    try:
        animation = import_slide_animation(
            pkg,
            slide,
            slide_svg=artifact.svg,
        )
    except AnimationImportError as exc:
        message = f"Object animation timing was not reconstructed: {exc}"
        if options.strict:
            raise ValueError(message) from exc
        append_diagnostic(
            result.diagnostics,
            ImportDiagnostic(
                code="animation-not-reconstructed",
                message=message,
                fallback=(
                    "keep this timing in the source PPTX through direct "
                    "native preservation"
                ),
                part_path=slide.part.path,
                slide_index=slide.index,
            ),
        )
        return
    if animation is None:
        return

    slides = result.animation_config["slides"]
    if not isinstance(slides, dict):
        raise RuntimeError("internal animations.json slides must be an object")
    slide_config = slides.setdefault(f"slide_{slide.index:02d}", {})
    if not isinstance(slide_config, dict):
        raise RuntimeError("internal animations.json slide row must be an object")
    slide_config["groups"] = animation.groups


def _convert_slide(
    pkg: OoxmlPackage,
    slide: SlideRef,
    palette: ColorPalette,
    options: ConvertOptions,
    diagnostics: list[ImportDiagnostic],
    theme_fonts: dict[str, str] | None = None,
    *,
    inheritance_mode: str | None = None,
) -> SlideArtifact:
    """Convert a single slide via the full shape pipeline.

    ``inheritance_mode`` overrides ``options.inheritance_mode`` so the
    orchestrator can render the same slide twice (once layered, once flat)
    when the user asked for ``"both"``. Pass ``"flat"`` or ``"layered"``;
    ``None`` falls back to ``options.inheritance_mode`` (used by direct
    callers that want a single mode).
    """
    mode = inheritance_mode or options.inheritance_mode
    if mode == "both":
        mode = "layered"  # primary view in both-mode
    show_inherited_shapes = part_show_master_sp(slide.part)
    svg, media = assemble_slide(
        pkg, slide, palette,
        theme_fonts=theme_fonts,
        media_subdir=options.images_subdir,
        embed_images=options.embed_images,
        keep_hidden=options.keep_hidden,
        inheritance_mode=mode,
        asset_name_map=options.asset_name_map,
        strict=options.strict,
        diagnostics=diagnostics,
        preserve_placeholder_inheritance=(
            options.roundtrip and mode == "layered"
        ),
    )
    return SlideArtifact(
        index=slide.index,
        svg=svg,
        media_files=media,
        layout_part_path=slide.layout.path if slide.layout else None,
        master_part_path=slide.master.path if slide.master else None,
        show_inherited_shapes=show_inherited_shapes,
    )


def _convert_inheritance_parts(
    pkg: OoxmlPackage,
    default_theme: PartRef | None,
    options: ConvertOptions,
    result: ConvertResult,
) -> None:
    """Render every master and layout in the deck to its own SVG (layered mode).

    We deliberately render *all* masters / layouts, not only the ones a slide
    references. Multi-style template packages routinely ship more design
    surfaces than the embedded sample slides exercise, and dropping unused
    ones discards the bulk of the template's design intent.
    """
    # Collect unique parts in document order so output filenames are
    # deterministic for a given .pptx.
    seen_masters: dict[str, PartRef] = {}
    for master in pkg.iter_all_masters():
        if master.path not in seen_masters:
            seen_masters[master.path] = master

    layouts_with_parent: list[tuple[PartRef, PartRef]] = []
    seen_layout_paths: set[str] = set()
    for layout, parent_master in pkg.iter_all_layouts_with_parent():
        if layout.path in seen_layout_paths:
            continue
        seen_layout_paths.add(layout.path)
        layouts_with_parent.append((layout, parent_master))

    for seq, part in enumerate(seen_masters.values(), start=1):
        theme = pkg.resolve_theme(part) or default_theme
        palette = _make_palette(
            part,
            theme,
            options,
            result,
            part_path=part.path,
        )
        _colors, fonts = _extract_theme_info(theme, palette) if theme is not None else ({}, result.theme_fonts)
        result.masters.append(_render_part(
            pkg, part, palette, options, result.diagnostics, fonts,
            role="master", seq=seq, theme_part=theme,
        ))
    for seq, (layout, parent_master) in enumerate(layouts_with_parent, start=1):
        theme = pkg.resolve_theme(parent_master) or default_theme
        palette = _make_palette(
            parent_master,
            theme,
            options,
            result,
            part_path=layout.path,
        )
        _colors, fonts = _extract_theme_info(theme, palette) if theme is not None else ({}, result.theme_fonts)
        result.layouts.append(_render_part(
            pkg, layout, palette, options, result.diagnostics, fonts,
            role="layout", seq=seq, parent_master=parent_master,
            theme_part=theme,
        ))


def _render_part(
    pkg: OoxmlPackage,
    part: PartRef,
    palette: ColorPalette,
    options: ConvertOptions,
    diagnostics: list[ImportDiagnostic],
    theme_fonts: dict[str, str],
    *,
    role: str,
    seq: int,
    parent_master: PartRef | None = None,
    theme_part: PartRef | None = None,
) -> PartArtifact:
    """Render a master/layout part, returning a PartArtifact with output filename."""
    svg, media = assemble_part_solo(
        pkg, part, palette,
        role=role,
        parent_master=parent_master,
        theme_fonts=theme_fonts,
        media_subdir=options.images_subdir,
        embed_images=options.embed_images,
        keep_hidden=options.keep_hidden,
        asset_name_map=options.asset_name_map,
        strict=options.strict,
        diagnostics=diagnostics,
    )
    stem = PurePosixPath(part.path).stem  # e.g. "slideLayout3"
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_") or role
    filename = f"{role}_{seq:02d}_{safe_stem}.svg"
    return PartArtifact(
        role=role,
        part_path=part.path,
        filename=filename,
        svg=svg,
        media_files=media,
        parent_master_part_path=parent_master.path if parent_master is not None else None,
        theme_part_path=theme_part.path if theme_part is not None else None,
        show_master_shapes=(
            part_show_master_sp(part) if role == "layout" else True
        ),
    )


def _path_lexists(path: Path) -> bool:
    """Return whether a path or symlink exists without following the symlink."""
    return path.exists() or path.is_symlink()


def _managed_svg_paths(output_dir: Path) -> list[Path]:
    """Return converter-owned SVG files without traversing user directories."""
    managed: list[Path] = []
    for relative_dir, filename_re, carries_inheritance in (
        (Path("svg"), _MANAGED_PRIMARY_SVG_RE, True),
        (Path("svg-flat"), _MANAGED_FLAT_SVG_RE, False),
        (ROUNDTRIP_LAYERED_SVG_DIR, _MANAGED_PRIMARY_SVG_RE, True),
        (ROUNDTRIP_FLAT_SVG_DIR, _MANAGED_FLAT_SVG_RE, False),
        (AUTHORING_SVG_DIR, _MANAGED_PRIMARY_SVG_RE, False),
        (AUTHORING_SVG_FLAT_DIR, _MANAGED_FLAT_SVG_RE, False),
    ):
        svg_dir = output_dir / relative_dir
        if svg_dir.is_symlink():
            managed.append(svg_dir)
            continue
        if not svg_dir.is_dir():
            continue
        managed.extend(
            path
            for path in svg_dir.iterdir()
            if filename_re.fullmatch(path.name)
            and (path.is_file() or path.is_symlink())
        )
        inheritance = svg_dir / "inheritance.json"
        if carries_inheritance and _path_lexists(inheritance):
            managed.append(inheritance)
        if relative_dir in {AUTHORING_SVG_DIR, AUTHORING_SVG_FLAT_DIR}:
            for filename in (
                "authoring_manifest.json",
                "authoring_summary.json",
            ):
                sidecar = svg_dir / filename
                if _path_lexists(sidecar):
                    managed.append(sidecar)
    return managed


def _managed_vector_asset_paths(output_dir: Path) -> set[Path]:
    """Return the previous converter-owned decoration inventory and assets."""
    managed: set[Path] = set()
    for authoring_dir in (AUTHORING_SVG_DIR, AUTHORING_SVG_FLAT_DIR):
        inventory_path = (
            output_dir / f"{authoring_dir.name}_vector_asset_inventory.json"
        )
        if not _path_lexists(inventory_path):
            continue
        managed.add(inventory_path)
        if inventory_path.is_symlink() or not inventory_path.is_file():
            continue
        try:
            payload = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        icons_dir_value = (
            payload.get("icons_dir") if isinstance(payload, dict) else None
        )
        icons_dir = (
            Path(icons_dir_value)
            if isinstance(icons_dir_value, str) and icons_dir_value
            else Path("icons")
        )
        if (
            icons_dir.drive
            or icons_dir.anchor
            or icons_dir.is_absolute()
            or ".." in icons_dir.parts
        ):
            continue
        assets = payload.get("assets") if isinstance(payload, dict) else None
        if not isinstance(assets, list):
            continue
        for item in assets:
            value = item.get("asset") if isinstance(item, dict) else None
            if not isinstance(value, str):
                continue
            asset_path = Path(value)
            if (
                asset_path.drive
                or asset_path.anchor
                or asset_path.is_absolute()
                or ".." in asset_path.parts
                or not asset_path.parts
            ):
                continue
            path = (
                asset_path
                if asset_path.parts[0] == "icons"
                else icons_dir / asset_path
            )
            if not path.parts or path.parts[0] != "icons":
                continue
            target = output_dir / path
            if _path_lexists(target):
                managed.add(target)
    return managed


def _managed_report_artifact_paths(output_dir: Path) -> set[Path]:
    """Return optional artifacts owned by the previous conversion report."""
    report_path = conversion_report_path(output_dir)
    if report_path.is_symlink() or not report_path.is_file():
        return set()
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, dict):
        return set()
    if artifacts.get("animationConfig") != "animations.json":
        return set()

    managed = {Path("animations.json")}
    source_template = artifacts.get("sourceTemplate")
    if source_template == SOURCE_TEMPLATE_NAME:
        managed.add(Path(str(source_template)))
    native_structure = artifacts.get("nativeStructure")
    if native_structure == NATIVE_STRUCTURE_NAME:
        managed.add(Path(str(native_structure)))
    if artifacts.get("roundtripManifest") == ROUNDTRIP_MANIFEST_PATH.as_posix():
        managed.add(ROUNDTRIP_MANIFEST_PATH)
    embedded_font_paths = [artifacts.get("embeddedFontManifest")]
    raw_font_parts = artifacts.get("embeddedFontParts")
    if isinstance(raw_font_parts, list):
        embedded_font_paths.extend(raw_font_parts)
    font_prefix = FONT_BUNDLE_DIR.parts
    for value in embedded_font_paths:
        if not isinstance(value, str):
            continue
        path = Path(value)
        if (
            path.drive
            or path.anchor
            or path.is_absolute()
            or ".." in path.parts
            or path.parts[:len(font_prefix)] != font_prefix
            or path.suffix.lower() not in {".json", ".fntdata"}
        ):
            continue
        managed.add(path)
    animation_media = artifacts.get("animationMedia")
    managed_lists = [animation_media, artifacts.get("resources"), artifacts.get("notes")]
    managed_resource_roots = {
        "audio",
        "images",
        "native-payloads",
        "notes",
        "sounds",
        "video",
    }
    for values in managed_lists:
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, str):
                continue
            path = Path(value)
            if (
                path.drive
                or path.anchor
                or path.is_absolute()
                or not path.parts
                or ".." in path.parts
                or path.parts[0] not in managed_resource_roots
            ):
                continue
            managed.add(path)
    if not isinstance(animation_media, list):
        return managed
    for value in animation_media:
        if not isinstance(value, str):
            continue
        path = Path(value)
        if (
            path.drive
            or path.anchor
            or path.is_absolute()
            or not path.parts
            or ".." in path.parts
            or not _MANAGED_TRANSITION_SOUND_RE.fullmatch(path.name)
        ):
            continue
        managed.add(path)
    return managed


def _referenced_local_paths(
    output_dir: Path,
    svg_paths: list[Path],
) -> set[Path]:
    """Resolve local media referenced by converter-owned SVGs."""
    referenced: set[Path] = set()
    output_abs = output_dir.absolute()
    for svg_path in svg_paths:
        if svg_path.is_symlink() or not svg_path.is_file():
            continue
        try:
            svg_text = svg_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for raw_href in _SVG_HREF_RE.findall(svg_text):
            href = unescape(raw_href)
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            href_path = unquote(parsed.path)
            if Path(href_path).is_absolute():
                continue
            target = Path(os.path.normpath(str(svg_path.parent / href_path)))
            try:
                relative = target.absolute().relative_to(output_abs)
            except ValueError:
                continue
            if relative.parts:
                referenced.add(relative)
    return referenced


def _validated_relative_paths(paths: set[str | Path]) -> set[Path]:
    """Normalize caller-supplied managed paths and reject output escapes."""
    normalized: set[Path] = set()
    for value in paths:
        path = Path(value)
        if (
            path.drive
            or path.anchor
            or path.is_absolute()
            or not path.parts
            or ".." in path.parts
        ):
            raise ValueError(f"Managed artifact path must stay relative: {value}")
        normalized.add(path)
    return normalized


def _reject_symlink_ancestors(
    root: Path,
    relative_paths: set[Path],
) -> None:
    """Reject managed paths that would traverse a preserved user symlink."""
    for relative in relative_paths:
        current = root
        for component in relative.parts[:-1]:
            current /= component
            if current.is_symlink():
                raise RuntimeError(
                    "Managed artifact path crosses an unmanaged symlink: "
                    f"{relative}"
                )


def _remove_managed_paths(candidate_dir: Path, relative_paths: set[Path]) -> None:
    """Remove only the previous converter roster from a candidate workspace."""
    _reject_symlink_ancestors(candidate_dir, relative_paths)
    parents: set[Path] = set()
    for relative in sorted(
        relative_paths,
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        target = candidate_dir / relative
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            raise RuntimeError(
                "Managed artifact path collides with a preserved directory: "
                f"{relative}"
            )
        parent = target.parent
        while parent != candidate_dir:
            parents.add(parent)
            parent = parent.parent

    for parent in sorted(parents, key=lambda item: len(item.parts), reverse=True):
        if parent.is_symlink() or not parent.is_dir():
            continue
        try:
            parent.rmdir()
        except OSError:
            pass


def _overlay_staged_tree(staged_dir: Path, candidate_dir: Path) -> None:
    """Overlay generated artifacts without overwriting unmanaged user files."""
    for source in sorted(staged_dir.rglob("*")):
        relative = source.relative_to(staged_dir)
        target = candidate_dir / relative
        _reject_symlink_ancestors(candidate_dir, {relative})
        if source.is_symlink():
            raise RuntimeError(
                f"Generated artifact must not be a symlink: {relative}"
            )
        if source.is_dir():
            if (
                target.is_symlink()
                or (_path_lexists(target) and not target.is_dir())
            ):
                raise RuntimeError(
                    f"Generated artifact collides with unmanaged path: {relative}"
                )
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if _path_lexists(target):
            if target.is_dir() or target.is_symlink():
                raise RuntimeError(
                    f"Generated artifact collides with unmanaged path: {relative}"
                )
            if target.read_bytes() != source.read_bytes():
                raise RuntimeError(
                    f"Generated artifact collides with unmanaged file: {relative}"
                )
        shutil.copy2(source, target)


def publish_staged_workspace(
    output_dir: Path,
    staged_dir: Path,
    *,
    managed_root_files: set[str | Path] | None = None,
    managed_relative_paths: set[str | Path] | None = None,
) -> None:
    """Atomically publish generated artifacts while preserving user files.

    Converter-owned SVGs, their local media references, and the named managed
    artifacts are replaced as one roster. Everything else already present in
    the output directory is copied into the candidate unchanged.
    """
    output_dir = output_dir.absolute()
    staged_dir = staged_dir.absolute()
    if (
        output_dir == staged_dir
        or output_dir in staged_dir.parents
        or staged_dir in output_dir.parents
    ):
        raise ValueError(
            "Staged and output workspaces must not contain one another"
        )
    output_resolved = output_dir.resolve(strict=False)
    try:
        Path.cwd().resolve().relative_to(output_resolved)
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Output workspace must not contain the current working directory"
        )
    if not staged_dir.is_dir():
        raise ValueError(f"Staged workspace does not exist: {staged_dir}")
    if (
        output_dir.is_symlink()
        or (_path_lexists(output_dir) and not output_dir.is_dir())
    ):
        raise RuntimeError(f"Output path must be a real directory: {output_dir}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    transaction_dir = Path(tempfile.mkdtemp(
        prefix=f".{output_dir.name}.publish-",
        dir=output_dir.parent,
    ))
    candidate_dir = transaction_dir / "candidate"
    backup_dir = transaction_dir / "previous"
    preserve_backup = False

    try:
        if output_dir.is_dir():
            shutil.copytree(output_dir, candidate_dir, symlinks=True)
        else:
            candidate_dir.mkdir()

        managed_svg = _managed_svg_paths(output_dir)
        relative_paths = {
            path.relative_to(output_dir)
            for path in managed_svg
        }
        relative_paths.update(
            path.relative_to(output_dir)
            for path in _managed_vector_asset_paths(output_dir)
        )
        relative_paths.update(_referenced_local_paths(output_dir, managed_svg))
        relative_paths.add(CONVERSION_REPORT_PATH)
        relative_paths.update(_managed_report_artifact_paths(output_dir))
        relative_paths.update(_validated_relative_paths(managed_root_files or set()))
        relative_paths.update(_validated_relative_paths(managed_relative_paths or set()))
        _remove_managed_paths(candidate_dir, relative_paths)
        _overlay_staged_tree(staged_dir, candidate_dir)

        if output_dir.is_dir():
            try:
                os.replace(output_dir, backup_dir)
                os.replace(candidate_dir, output_dir)
            except BaseException as publish_error:
                try:
                    if _path_lexists(backup_dir):
                        if _path_lexists(output_dir):
                            failed_output = transaction_dir / "failed-publish"
                            os.replace(output_dir, failed_output)
                        os.replace(backup_dir, output_dir)
                except BaseException as restore_error:
                    if (
                        not _path_lexists(backup_dir)
                        and _path_lexists(output_dir)
                    ):
                        raise publish_error
                    preserve_backup = _path_lexists(backup_dir)
                    raise RuntimeError(
                        "Failed to publish the new workspace and restore the "
                        "previous workspace; recovery directory: "
                        f"{transaction_dir}"
                    ) from restore_error
                raise
        else:
            os.replace(candidate_dir, output_dir)
    finally:
        if not preserve_backup:
            shutil.rmtree(transaction_dir, ignore_errors=True)


def _write_artifact_tree(
    output_dir: Path,
    result: ConvertResult,
    options: ConvertOptions,
) -> None:
    """Write a complete converter roster into an empty staging directory.

    Layout:
      - normal conversion uses ``svg/`` and optional ``svg-flat/``
      - round-trip conversion keeps immutable SVG backing under ``analysis/``
        and publishes only ``authoring-svg-flat/`` as the editable page source
      - ``images/``     shared image assets, referenced by both views
      - semantic resource directories for sounds, audio, video, and opaque
        native payloads when the source package contains them
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_dir = output_dir / (
        ROUNDTRIP_LAYERED_SVG_DIR if options.roundtrip else Path("svg")
    )
    svg_dir.mkdir(parents=True, exist_ok=True)
    media_dir = output_dir / options.images_subdir
    sound_dir = output_dir / options.sound_subdir
    media_written: dict[str, bytes] = {}
    sounds_written: dict[str, bytes] = {}

    def _svg_for_target(svg: str, target_dir: Path) -> str:
        """Rebase generated local hrefs from the normal one-level SVG root."""
        source_dir = output_dir / "svg"
        project_root = output_dir.resolve()

        def replace_href(match: re.Match[str]) -> str:
            raw = unescape(match.group("value"))
            parsed = urlsplit(raw)
            if (
                not raw
                or raw.startswith("#")
                or parsed.scheme
                or parsed.netloc
                or not parsed.path
            ):
                return match.group(0)
            resolved = (source_dir / unquote(parsed.path)).resolve()
            try:
                resolved.relative_to(project_root)
            except ValueError as exc:
                raise RuntimeError(
                    f"Generated SVG resource escapes the workspace: {raw!r}"
                ) from exc
            relative = os.path.relpath(resolved, target_dir).replace(os.sep, "/")
            rebased = urlunsplit(("", "", relative, parsed.query, parsed.fragment))
            return f"{match.group('prefix')}{quoteattr(rebased)}"

        return _SVG_HREF_ATTRIBUTE_RE.sub(replace_href, svg)

    def _collect_media(media: dict[str, bytes]) -> None:
        for filename, blob in media.items():
            _validate_media_filename(filename)
            if filename in media_written:
                if media_written[filename] != blob:
                    raise RuntimeError(
                        f"Asset filename collision with different bytes: {filename}"
                    )
                continue
            media_written[filename] = blob

    # Layered mode: write masters and layouts first so they sort ahead of slides.
    for art in result.masters:
        (svg_dir / art.filename).write_text(
            _svg_for_target(art.svg, svg_dir),
            encoding="utf-8",
        )
        _collect_media(art.media_files)
    for art in result.layouts:
        (svg_dir / art.filename).write_text(
            _svg_for_target(art.svg, svg_dir),
            encoding="utf-8",
        )
        _collect_media(art.media_files)

    # Slides (primary view).
    for art in result.slides:
        target = svg_dir / f"slide_{art.index:02d}.svg"
        target.write_text(
            _svg_for_target(art.svg, target.parent),
            encoding="utf-8",
        )
        _collect_media(art.media_files)
    for filename, blob in result.animation_media_files.items():
        _validate_media_filename(filename)
        existing = sounds_written.get(filename)
        if existing is not None and existing != blob:
            raise RuntimeError(
                f"Sound filename collision with different bytes: {filename}"
            )
        sounds_written[filename] = blob

    # Inheritance graph alongside the layered SVGs (only meaningful when we
    # actually emitted a layered view).
    if options.inheritance_mode in {"layered", "both"}:
        _write_inheritance_json(svg_dir, result)

    # Flat companion view (only when result.flat_slides is populated).
    if result.flat_slides:
        flat_dir = output_dir / (
            ROUNDTRIP_FLAT_SVG_DIR if options.roundtrip else Path("svg-flat")
        )
        flat_dir.mkdir(parents=True, exist_ok=True)
        for art in result.flat_slides:
            target = flat_dir / f"slide_{art.index:02d}.svg"
            target.write_text(
                _svg_for_target(art.svg, target.parent),
                encoding="utf-8",
            )
            _collect_media(art.media_files)

    _write_animation_config(output_dir, result)
    _write_speaker_notes(output_dir, result)
    if result.native_structure is not None:
        if result.source_pptx_path is None:
            raise RuntimeError(
                "Round-trip source structure is missing its source PPTX path"
            )
        source_target = output_dir / SOURCE_TEMPLATE_NAME
        source_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(result.source_pptx_path, source_target)
        structure_target = output_dir / NATIVE_STRUCTURE_NAME
        structure_target.parent.mkdir(parents=True, exist_ok=True)
        structure_target.write_text(
            json.dumps(
                result.native_structure,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    embedded_fonts_descriptor: dict[str, object] | None = None
    embedded_font_paths: tuple[str, ...] = ()
    if result.embedded_fonts is not None:
        (
            embedded_fonts_descriptor,
            embedded_font_paths,
        ) = write_embedded_font_bundle(output_dir, result.embedded_fonts)
    _write_conversion_report(
        output_dir,
        result,
        options,
        embedded_fonts_descriptor=embedded_fonts_descriptor,
        embedded_font_paths=embedded_font_paths,
    )
    write_workspace_resources(
        output_dir,
        result.resource_inventory,
        include_images=not options.embed_images,
    )
    if media_written:
        media_dir.mkdir(parents=True, exist_ok=True)
    for filename, blob in media_written.items():
        target = media_dir / filename
        if _path_lexists(target):
            if (
                target.is_symlink()
                or not target.is_file()
                or target.read_bytes() != blob
            ):
                raise RuntimeError(
                    f"Asset filename collision with different bytes: {filename}"
                )
            continue
        target.write_bytes(blob)
    if sounds_written:
        sound_dir.mkdir(parents=True, exist_ok=True)
    for filename, blob in sounds_written.items():
        target = sound_dir / filename
        if _path_lexists(target):
            if (
                target.is_symlink()
                or not target.is_file()
                or target.read_bytes() != blob
            ):
                raise RuntimeError(
                    f"Sound filename collision with different bytes: {filename}"
                )
            continue
        target.write_bytes(blob)
    if result.native_structure is not None:
        flat_dir = output_dir / ROUNDTRIP_FLAT_SVG_DIR
        authoring_dir = output_dir / AUTHORING_SVG_FLAT_DIR
        source_proxy_dir = media_dir / "source-object-previews"
        mapping = [
            (source, authoring_dir / source.name)
            for source in sorted(flat_dir.glob("slide_*.svg"))
        ]
        if len(mapping) != len(result.slides):
            raise RuntimeError(
                "Round-trip flat backing roster does not match the slide roster"
            )
        project_svg_batch(
            mapping,
            flat_dir,
            authoring_dir,
            force=False,
            projection_kind="flat",
            source_proxy_dir=source_proxy_dir,
        )
        extract_directory(
            authoring_dir,
            output_dir / "icons",
            "imported",
            min_drawables=_ROUNDTRIP_VECTOR_MIN_DRAWABLES,
            min_bytes=_ROUNDTRIP_VECTOR_MIN_BYTES,
            min_decoration_bytes=_ROUNDTRIP_VECTOR_MIN_DECORATION_BYTES,
            inplace=True,
            id_prefix="flat",
            inventory_path=(
                output_dir
                / f"{authoring_dir.name}_vector_asset_inventory.json"
            ),
        )
        _write_roundtrip_manifest(output_dir, result, options)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_speaker_notes(output_dir: Path, result: ConvertResult) -> None:
    """Write imported notes into the standard per-slide Markdown contract."""
    if not result.speaker_notes:
        return
    notes_dir = output_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    combined = ["# Speaker Notes"]
    for note in result.speaker_notes:
        content = note.markdown.strip() + "\n"
        (notes_dir / note.filename).write_text(content, encoding="utf-8")
        combined.extend([
            "",
            f"## Slide {note.slide_index:02d}",
            "",
            note.markdown.strip(),
        ])
    (notes_dir / "total.md").write_text(
        "\n".join(combined).rstrip() + "\n",
        encoding="utf-8",
    )


def _write_roundtrip_manifest(
    output_dir: Path,
    result: ConvertResult,
    options: ConvertOptions,
) -> None:
    """Record immutable source, editable sidecars, and semantic resources."""
    source_path = output_dir / SOURCE_PPTX_PATH
    animation_path = output_dir / "animations.json"
    resource_manifest = result.resource_inventory.manifest(
        include_images=not options.embed_images,
    )
    materialized_resource_paths = {
        Path(str(item["workspacePath"]))
        for item in resource_manifest["items"]
        if isinstance(item, dict)
        and item.get("materialized") is True
        and isinstance(item.get("workspacePath"), str)
    }
    notes_by_index = {
        note.slide_index: note
        for note in result.speaker_notes
    }
    flat_by_index = {
        slide.index: slide
        for slide in result.flat_slides
    }
    native_slides = []
    if isinstance(result.native_structure, dict):
        raw_slides = result.native_structure.get("slides")
        if isinstance(raw_slides, list):
            native_slides = raw_slides
    native_by_index = {
        int(item.get("index")): item
        for item in native_slides
        if isinstance(item, dict) and isinstance(item.get("index"), int)
    }
    native_masters = (
        result.native_structure.get("masters")
        if isinstance(result.native_structure, dict)
        else None
    )
    master_parts = {
        str(item.get("key")): str(item.get("packagePart"))
        for item in native_masters or []
        if isinstance(item, dict)
        and item.get("key")
        and item.get("packagePart")
    }
    native_layouts = (
        result.native_structure.get("layouts")
        if isinstance(result.native_structure, dict)
        else None
    )
    layout_parts = {
        str(item.get("key")): str(item.get("packagePart"))
        for item in native_layouts or []
        if isinstance(item, dict)
        and item.get("key")
        and item.get("packagePart")
    }
    slides: list[dict[str, object]] = []
    for slide in result.slides:
        layered_path = ROUNDTRIP_LAYERED_SVG_DIR / f"slide_{slide.index:02d}.svg"
        native_slide = native_by_index.get(slide.index, {})
        row: dict[str, object] = {
            "index": slide.index,
            "sourcePart": native_slide.get("packagePart"),
            "layoutPart": layout_parts.get(str(native_slide.get("layoutKey"))),
            "masterPart": master_parts.get(str(native_slide.get("masterKey"))),
            "layeredSvg": layered_path.as_posix(),
            "layeredSvgSha256": _sha256_file(output_dir / layered_path),
            "animationSha256": slide_animation_config_sha256(
                result.animation_config,
                f"slide_{slide.index:02d}",
            ),
        }
        referenced_svg_paths = [output_dir / layered_path]
        if slide.index in flat_by_index:
            flat_path = ROUNDTRIP_FLAT_SVG_DIR / f"slide_{slide.index:02d}.svg"
            row["flatSvg"] = flat_path.as_posix()
            row["flatSvgSha256"] = _sha256_file(output_dir / flat_path)
            referenced_svg_paths.append(output_dir / flat_path)
        authoring_path = AUTHORING_SVG_FLAT_DIR / f"slide_{slide.index:02d}.svg"
        if (output_dir / authoring_path).is_file():
            referenced_svg_paths.append(output_dir / authoring_path)
        derived_paths = sorted(
            _referenced_local_paths(output_dir, referenced_svg_paths)
            - materialized_resource_paths,
            key=lambda path: path.as_posix(),
        )
        derived_resources: list[dict[str, str]] = []
        for relative in derived_paths:
            target = output_dir / relative
            if not target.is_file():
                raise RuntimeError(
                    "Round-trip SVG references a missing derived resource: "
                    f"{relative.as_posix()}"
                )
            derived_resources.append({
                "file": relative.as_posix(),
                "sha256": _sha256_file(target),
            })
        row["derivedResources"] = derived_resources
        note = notes_by_index.get(slide.index)
        if note is not None:
            note_path = Path("notes") / note.filename
            row["notes"] = {
                "file": note_path.as_posix(),
                "sha256": _sha256_file(output_dir / note_path),
                "sourcePart": note.source_part,
                "sourceSha256": note.source_sha256,
            }
        slides.append(row)
    payload = {
        "schema": "ppt-master.roundtrip-workspace.v1",
        "source": {
            "file": SOURCE_PPTX_PATH.as_posix(),
            "sha256": _sha256_file(source_path),
        },
        "structure": NATIVE_STRUCTURE_PATH.as_posix(),
        "conversionReport": CONVERSION_REPORT_PATH.as_posix(),
        "sidecars": {
            "animations": {
                "file": "animations.json",
                "sha256": _sha256_file(animation_path),
            },
            "notesTotal": (
                {
                    "file": "notes/total.md",
                    "sha256": _sha256_file(output_dir / "notes/total.md"),
                }
                if result.speaker_notes
                else None
            ),
        },
        "directories": {
            "authoringSvg": AUTHORING_SVG_FLAT_DIR.as_posix(),
            "layeredSvg": ROUNDTRIP_LAYERED_SVG_DIR.as_posix(),
            "flatSvg": (
                ROUNDTRIP_FLAT_SVG_DIR.as_posix()
                if result.flat_slides
                else None
            ),
            "images": options.images_subdir,
            "sourceObjectPreviews": (
                Path(options.images_subdir) / "source-object-previews"
            ).as_posix(),
            "sounds": options.sound_subdir,
            "audio": "audio",
            "video": "video",
            "notes": "notes",
            "nativePayloads": "native-payloads",
        },
        "slides": slides,
        "resources": resource_manifest,
    }
    target = output_dir / ROUNDTRIP_MANIFEST_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_artifacts(
    output_dir: Path,
    result: ConvertResult,
    options: ConvertOptions,
) -> None:
    """Stage a complete conversion, then atomically publish its exact roster."""
    output_dir = output_dir.absolute()
    reject_removed_workspace_layout(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(
        prefix=f".{output_dir.name}.convert-",
        dir=output_dir.parent,
    ))
    staged_dir = staging_root / "generated"
    try:
        _write_artifact_tree(staged_dir, result, options)
        publish_staged_workspace(output_dir, staged_dir)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def _write_conversion_report(
    output_dir: Path,
    result: ConvertResult,
    options: ConvertOptions,
    *,
    embedded_fonts_descriptor: dict[str, object] | None = None,
    embedded_font_paths: tuple[str, ...] = (),
) -> None:
    """Write the user-visible tolerant-import report."""
    animation_media = [
        (PurePosixPath(options.sound_subdir) / filename).as_posix()
        for filename in sorted(result.animation_media_files)
    ]
    source_theme: dict[str, object] = {
        "colors": result.theme_colors,
        "fonts": result.theme_fonts,
    }
    if result.theme_xml is not None:
        source_theme["ooxml"] = {
            "encoding": "base64",
            "sha256": hashlib.sha256(result.theme_xml).hexdigest(),
            "payload": base64.b64encode(result.theme_xml).decode("ascii"),
        }
    source_document: dict[str, object] = {
        "canvasPx": {
            "width": result.canvas_px[0],
            "height": result.canvas_px[1],
        },
        "theme": source_theme,
    }
    if embedded_fonts_descriptor is not None:
        source_document["embeddedFonts"] = embedded_fonts_descriptor
    artifacts: dict[str, object] = {
        "animationConfig": "animations.json",
        "animationMedia": animation_media,
        "resources": [
            resource.workspace_path
            for resource in result.resource_inventory.resources
            if not (options.embed_images and resource.kind == "image")
        ],
        "notes": [
            (Path("notes") / note.filename).as_posix()
            for note in result.speaker_notes
        ] + (["notes/total.md"] if result.speaker_notes else []),
    }
    if embedded_font_paths:
        artifacts["embeddedFontManifest"] = embedded_font_paths[-1]
        artifacts["embeddedFontParts"] = list(embedded_font_paths[:-1])
    if result.native_structure is not None:
        artifacts["sourceTemplate"] = SOURCE_TEMPLATE_NAME
        artifacts["nativeStructure"] = NATIVE_STRUCTURE_NAME
        artifacts["roundtripManifest"] = ROUNDTRIP_MANIFEST_PATH.as_posix()
    report = {
        "schemaVersion": 1,
        "source": result.source_file,
        "mode": "strict" if result.strict else "tolerant",
        "summary": {
            "slides": len(result.slides),
            "warnings": len(result.diagnostics),
        },
        "artifacts": artifacts,
        "sourceDocument": source_document,
        "diagnostics": [item.to_dict() for item in result.diagnostics],
    }
    report_path = output_dir / CONVERSION_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_animation_config(output_dir: Path, result: ConvertResult) -> None:
    """Write the canonical transition/object-motion sidecar."""
    errors = list(
        dict.fromkeys(
            validate_transition_config(result.animation_config)
            + validate_animation_config_errors(result.animation_config)
        )
    )
    if errors:
        raise RuntimeError(
            "Generated animations.json is invalid: " + "; ".join(errors)
        )
    (output_dir / "animations.json").write_text(
        json.dumps(
            result.animation_config,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def _write_inheritance_json(svg_dir: Path, result: ConvertResult) -> None:
    """Record layered parentage plus source-owned shape-visibility booleans."""
    layout_by_path = {art.part_path: art.filename for art in result.layouts}
    master_by_path = {art.part_path: art.filename for art in result.masters}

    inheritance = {
        "masters": [
            {
                "file": art.filename,
                "partPath": art.part_path,
                "themePath": art.theme_part_path,
            }
            for art in result.masters
        ],
        "layouts": [
            {
                "file": art.filename,
                "partPath": art.part_path,
                "master": master_by_path.get(art.parent_master_part_path or ""),
                "parentPartPath": art.parent_master_part_path,
                "themePath": art.theme_part_path,
                "showMasterShapes": art.show_master_shapes,
            }
            for art in result.layouts
        ],
        "slides": [
            {
                "file": f"slide_{slide.index:02d}.svg",
                "index": slide.index,
                "layout": layout_by_path.get(slide.layout_part_path or ""),
                "master": master_by_path.get(slide.master_part_path or ""),
                "showInheritedShapes": slide.show_inherited_shapes,
            }
            for slide in result.slides
        ],
    }
    (svg_dir / "inheritance.json").write_text(
        json.dumps(inheritance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
