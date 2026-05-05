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

from dataclasses import dataclass, field
from pathlib import Path

from .color_resolver import ColorPalette
from .emu_units import NS
from .ooxml_loader import OoxmlPackage, SlideRef
from .slide_to_svg import assemble_slide


@dataclass
class ConvertOptions:
    """Convert behavior knobs.

    media_subdir: where to write media files relative to output_dir. SVG image
        href will use './<media_subdir>/<filename>'.
    embed_images: when True, base64-encode images inline instead of writing
        files. Default False (matches svg_to_pptx default of external images).
    keep_hidden: include shapes marked hidden="1". Default False.
    """

    media_subdir: str = "assets"
    embed_images: bool = False
    keep_hidden: bool = False


@dataclass
class SlideArtifact:
    """Result of converting a single slide."""

    index: int  # 1-based
    svg: str
    media_files: dict[str, bytes] = field(default_factory=dict)


@dataclass
class ConvertResult:
    """Result of converting an entire .pptx."""

    slides: list[SlideArtifact] = field(default_factory=list)
    canvas_px: tuple[float, float] = (1280.0, 720.0)
    theme_colors: dict[str, str] = field(default_factory=dict)
    theme_fonts: dict[str, str] = field(default_factory=dict)


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
    result = ConvertResult()

    with OoxmlPackage(pptx_path) as pkg:
        result.canvas_px = pkg.slide_size_px

        # Theme + palette built once (multi-master case rarely happens in
        # template decks; if it does we re-resolve per slide).
        first_slide = pkg.get_slide(1)
        master = first_slide.master if first_slide else None
        theme = pkg.resolve_theme(master)
        palette = ColorPalette(master, theme)
        if theme is not None:
            from .color_resolver import find_color_elem, resolve_color
            # Surface theme colors / fonts onto the result (informational only).
            scheme = theme.xml.find(".//a:clrScheme", NS)
            if scheme is not None:
                for child in list(scheme):
                    if not isinstance(child.tag, str):
                        continue
                    name = child.tag.split("}", 1)[-1]
                    color_elem = find_color_elem(child)
                    hex_, _ = resolve_color(color_elem, palette)
                    if hex_:
                        result.theme_colors[name] = hex_
            font_scheme = theme.xml.find(".//a:fontScheme", NS)
            if font_scheme is not None:
                for slot in ("majorFont", "minorFont"):
                    fnt = font_scheme.find(f"a:{slot}", NS)
                    if fnt is None:
                        continue
                    role_prefix = "major" if slot == "majorFont" else "minor"
                    latin = fnt.find("a:latin", NS)
                    if latin is not None and latin.attrib.get("typeface"):
                        result.theme_fonts[f"{role_prefix}Latin"] = latin.attrib["typeface"]
                    ea = fnt.find("a:ea", NS)
                    if ea is not None and ea.attrib.get("typeface"):
                        result.theme_fonts[f"{role_prefix}EastAsia"] = ea.attrib["typeface"]
                    cs = fnt.find("a:cs", NS)
                    if cs is not None and cs.attrib.get("typeface"):
                        result.theme_fonts[f"{role_prefix}ComplexScript"] = cs.attrib["typeface"]

        # Per-slide conversion
        for slide in pkg.iter_slides():
            artifact = _convert_slide(pkg, slide, palette, options, result.theme_fonts)
            result.slides.append(artifact)

    if output_dir is not None:
        _write_artifacts(output_dir, result, options)

    return result


def _convert_slide(
    pkg: OoxmlPackage,
    slide: SlideRef,
    palette: ColorPalette,
    options: ConvertOptions,
    theme_fonts: dict[str, str] | None = None,
) -> SlideArtifact:
    """Convert a single slide via the full shape pipeline."""
    svg, media = assemble_slide(
        pkg, slide, palette,
        theme_fonts=theme_fonts,
        media_subdir=options.media_subdir,
        embed_images=options.embed_images,
        keep_hidden=options.keep_hidden,
    )
    return SlideArtifact(index=slide.index, svg=svg, media_files=media)


def _write_artifacts(output_dir: Path, result: ConvertResult,
                     options: ConvertOptions) -> None:
    """Write SVG + media files to output_dir/svg and output_dir/<media_subdir>."""
    output_dir.mkdir(parents=True, exist_ok=True)
    svg_dir = output_dir / "svg"
    svg_dir.mkdir(exist_ok=True)
    media_dir = output_dir / options.media_subdir
    media_written: set[str] = set()

    for art in result.slides:
        target = svg_dir / f"slide_{art.index:02d}.svg"
        target.write_text(art.svg, encoding="utf-8")
        for filename, blob in art.media_files.items():
            if filename in media_written:
                continue
            media_dir.mkdir(parents=True, exist_ok=True)
            (media_dir / filename).write_bytes(blob)
            media_written.add(filename)
