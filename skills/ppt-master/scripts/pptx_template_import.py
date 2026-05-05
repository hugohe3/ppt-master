#!/usr/bin/env python3
"""Unified PPTX preparation entry point for the /create-template workflow.

This command prepares a reusable reference workspace from a PPTX source. It can:

1. extract lightweight PPTX metadata and reusable assets
2. export every slide to SVG with PowerPoint on Windows
3. export PPTX to PDF on macOS with Keynote as a fallback bridge
4. replace inline Base64 images inside exported SVG files with external assets
5. optimize cleaned reference SVG files for downstream inspection
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import tempfile
from pathlib import Path

from template_import.externalize_images import discover_svg_files, externalize_svg_batch
from template_import.manifest import build_manifest
from template_import.optimize_reference import optimize_reference_batch

PPT_PDF_TO_SVG_SCALE = 96.0 / 72.0


POWERSHELL_EXPORT_SCRIPT = r"""
param(
    [Parameter(Mandatory = $true)][string]$PptxPath,
    [Parameter(Mandatory = $true)][string]$OutputDir
)

$ErrorActionPreference = 'Stop'
$powerpoint = $null
$presentation = $null

try {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $powerpoint = New-Object -ComObject PowerPoint.Application
    $powerpoint.Visible = -1
    $presentation = $powerpoint.Presentations.Open($PptxPath, $false, $false, $false)

    foreach ($slide in $presentation.Slides) {
        $fileName = ('slide_{0:D2}.svg' -f $slide.SlideIndex)
        $target = Join-Path $OutputDir $fileName
        $slide.Export($target, 'SVG')
    }
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
    }
    if ($powerpoint -ne $null) {
        $powerpoint.Quit()
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
"""


POWERSHELL_PDF_EXPORT_SCRIPT = r"""
param(
    [Parameter(Mandatory = $true)][string]$PptxPath,
    [Parameter(Mandatory = $true)][string]$PdfPath
)

$ErrorActionPreference = 'Stop'
$powerpoint = $null
$presentation = $null

try {
    $pdfDir = Split-Path -Parent $PdfPath
    New-Item -ItemType Directory -Force -Path $pdfDir | Out-Null
    $powerpoint = New-Object -ComObject PowerPoint.Application
    $powerpoint.Visible = -1
    $presentation = $powerpoint.Presentations.Open($PptxPath, $false, $false, $false)
    $presentation.SaveAs($PdfPath, 32)
}
finally {
    if ($presentation -ne $null) {
        $presentation.Close()
    }
    if ($powerpoint -ne $null) {
        $powerpoint.Quit()
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
"""


def run_powershell_script(script_body: str, *script_args: str) -> subprocess.CompletedProcess[bytes]:
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as handle:
        handle.write(script_body)
        script_path = Path(handle.name)

    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                *script_args,
            ],
            capture_output=True,
            text=False,
            check=False,
        )
    finally:
        script_path.unlink(missing_ok=True)
    return completed


def run_osascript_lines(*script_lines: str) -> subprocess.CompletedProcess[bytes]:
    command = ["osascript"]
    for line in script_lines:
        command.extend(["-e", line])
    return subprocess.run(
        command,
        capture_output=True,
        text=False,
        check=False,
    )

def decode_process_output(completed: subprocess.CompletedProcess[bytes]) -> str:
    stderr = (completed.stderr or b"").decode("utf-8", errors="replace").strip()
    stdout = (completed.stdout or b"").decode("utf-8", errors="replace").strip()
    return stderr or stdout or "PowerPoint export failed"


def export_pptx_slides_to_svg(pptx_path: Path, output_dir: Path) -> list[Path]:
    if platform.system() != "Windows":
        raise RuntimeError("pptx_template_import.py currently requires Windows PowerPoint")

    output_dir.mkdir(parents=True, exist_ok=True)
    completed = run_powershell_script(
        POWERSHELL_EXPORT_SCRIPT,
        "-PptxPath",
        str(pptx_path),
        "-OutputDir",
        str(output_dir),
    )

    if completed.returncode != 0:
        raise RuntimeError(decode_process_output(completed))

    svg_files = discover_svg_files([str(output_dir)])
    if not svg_files:
        raise RuntimeError("PowerPoint export completed but no SVG files were found")
    return svg_files


def export_pptx_to_pdf(pptx_path: Path, pdf_path: Path) -> Path:
    system = platform.system()

    if system == "Windows":
        completed = run_powershell_script(
            POWERSHELL_PDF_EXPORT_SCRIPT,
            "-PptxPath",
            str(pptx_path),
            "-PdfPath",
            str(pdf_path),
        )
    elif system == "Darwin":
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        completed = run_osascript_lines(
            'tell application "Keynote"',
            "activate",
            f'set pptxFile to POSIX file "{pptx_path}"',
            f'set pdfFile to POSIX file "{pdf_path}"',
            "with timeout of 600 seconds",
            "set docRef to open pptxFile",
            "export docRef to pdfFile as PDF",
            "close docRef saving no",
            "end timeout",
            "end tell",
        )
    else:
        raise RuntimeError(
            "PPTX to PDF export is supported on Windows (PowerPoint) and macOS (Keynote)"
        )

    if completed.returncode != 0:
        raise RuntimeError(decode_process_output(completed))
    if not pdf_path.exists():
        raise RuntimeError("PPTX PDF export completed but no PDF file was found")
    return pdf_path


def export_pdf_pages_to_svg(pdf_path: Path, output_dir: Path) -> list[Path]:
    import fitz

    output_dir.mkdir(parents=True, exist_ok=True)
    svg_files: list[Path] = []
    matrix = fitz.Matrix(PPT_PDF_TO_SVG_SCALE, PPT_PDF_TO_SVG_SCALE)
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document, 1):
            target = output_dir / f"slide_{index:02d}.svg"
            target.write_text(
                page.get_svg_image(matrix=matrix, text_as_path=False),
                encoding="utf-8",
            )
            svg_files.append(target)
    return svg_files


def export_pptx_slides_to_svg_with_fallback(pptx_path: Path, output_dir: Path) -> tuple[list[Path], str]:
    try:
        return export_pptx_slides_to_svg(pptx_path, output_dir), "powerpoint-svg"
    except Exception:
        pdf_path = output_dir.parent / f"{pptx_path.stem}_slides.pdf"
        export_pptx_to_pdf(pptx_path, pdf_path)
        svg_files = export_pdf_pages_to_svg(pdf_path, output_dir)
        return svg_files, "powerpoint-pdf-fallback"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a PPTX reference workspace for /create-template."
    )
    parser.add_argument("pptx_file", help="Path to the source .pptx file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <pptx_stem>_template_import beside the source file)",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help="Skip PPTX metadata extraction and asset inventory generation",
    )
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only extract manifest.json, analysis.md, and reusable assets without exporting slides to SVG",
    )
    parser.add_argument(
        "--legacy-render",
        action="store_true",
        help=(
            "Use the legacy renderer (PowerPoint COM on Windows, Keynote -> PDF "
            "on macOS). Lossy: text becomes <path>, every cropped picture spawns "
            "a new inline_*.png slice. The default semantic converter "
            "(pptx_to_svg) reads OOXML directly and preserves shape primitives."
        ),
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="(--legacy-render only) Keep raw PowerPoint-exported SVG files in svg_raw/",
    )
    parser.add_argument(
        "--no-externalize",
        action="store_true",
        help="(--legacy-render only) Skip inline image externalization",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="(--legacy-render only) Skip structural optimization of the cleaned reference SVGs",
    )
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="(default renderer only) Inline images as data: URIs instead of writing files to assets/",
    )
    return parser.parse_args()


def build_reference_svg_selection(manifest: dict, svg_files: list[Path]) -> dict:
    slides = manifest.get("slides", [])
    total = len(slides) or len(svg_files)
    svg_by_index = {
        index: f"svg/slide_{index:02d}.svg"
        for index in range(1, len(svg_files) + 1)
    }

    mandatory: list[int] = []
    for index in (1, 2, total):
        if 1 <= index <= total and index not in mandatory:
            mandatory.append(index)

    selected = list(mandatory)
    selected_set = set(selected)

    # Prefer page-type diversity first.
    by_page_type: dict[str, list[int]] = {}
    for slide in slides:
        by_page_type.setdefault(slide.get("pageType", "unknown"), []).append(slide["index"])

    preferred_types = [
        "cover_candidate",
        "chapter_candidate",
        "toc_candidate",
        "content_candidate",
        "ending_candidate",
    ]
    for page_type in preferred_types:
        for index in by_page_type.get(page_type, []):
            if index not in selected_set and index not in mandatory:
                selected.append(index)
                selected_set.add(index)
                break

    # Then fill with evenly distributed content/reference pages until
    # there are at least 7 pages beyond 1/2/last when possible.
    target_total = min(total, len(mandatory) + 7)
    remaining = [index for index in range(1, total + 1) if index not in selected_set]
    while len(selected) < target_total and remaining:
        needed = target_total - len(selected)
        picks: list[int] = []
        for slot in range(needed):
            pos = round((slot + 1) * (len(remaining) + 1) / (needed + 1)) - 1
            pos = max(0, min(pos, len(remaining) - 1))
            candidate = remaining[pos]
            if candidate not in picks:
                picks.append(candidate)
        for candidate in picks:
            if candidate not in selected_set:
                selected.append(candidate)
                selected_set.add(candidate)
        remaining = [index for index in remaining if index not in selected_set]

    selected.sort()
    recommended = [
        {
            "index": index,
            "svg": svg_by_index.get(index, f"svg/slide_{index:02d}.svg"),
            "pageType": next(
                (slide.get("pageType", "unknown") for slide in slides if slide["index"] == index),
                "unknown",
            ),
            "reason": (
                "mandatory"
                if index in mandatory
                else "representative_reference"
            ),
        }
        for index in selected
    ]

    return {
        "totalSlides": total,
        "mandatoryIndexes": mandatory,
        "minimumAdditionalReferenceCount": 7,
        "recommendedIndexes": selected,
        "recommendedSvgRefs": recommended,
        "guidance": (
            "Always reference slides 1, 2, and the last slide. "
            "Beyond those mandatory pages, use at least 7 additional representative SVG pages "
            "instead of consuming every exported SVG by default."
        ),
    }


def main() -> int:
    args = parse_args()
    pptx_path = Path(args.pptx_file).expanduser().resolve()
    if not pptx_path.exists():
        print(f"Error: file does not exist: {pptx_path}")
        return 1
    if pptx_path.suffix.lower() != ".pptx":
        print(f"Error: expected a .pptx file, got: {pptx_path.name}")
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pptx_path.with_name(f"{pptx_path.stem}_template_import")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.skip_manifest and args.manifest_only:
        print("Error: --skip-manifest and --manifest-only cannot be used together")
        return 1

    if not args.skip_manifest:
        try:
            manifest = build_manifest(pptx_path, output_dir)
        except Exception as exc:
            print(f"Error: failed to extract PPTX metadata: {exc}")
            return 1

        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        manifest = {"slides": []}

    if args.manifest_only:
        print(f"Imported PPTX template source: {pptx_path.name}")
        print(f"Output directory: {output_dir}")
        if not args.skip_manifest:
            print(f"Manifest: {manifest_path.name}")
            print(f"Assets exported: {len(manifest['assets']['allAssets'])}")
            print(f"Common assets: {len(manifest['assets']['commonAssets'])}")
            print(f"Slides analyzed: {len(manifest['slides'])}")
        return 0

    # ---------- Slide rendering ----------
    if args.legacy_render:
        export_mode, slide_count, total_in, total_out = _render_slides_legacy(
            pptx_path, output_dir, args,
        )
    else:
        export_mode, slide_count, total_in, total_out = _render_slides_native(
            pptx_path, output_dir, args,
        )

    # reference_svg_selection.json (shared between both paths)
    cleaned_dir = output_dir / "svg"
    reference_selection = build_reference_svg_selection(
        manifest, sorted(cleaned_dir.glob("*.svg")),
    )
    (output_dir / "reference_svg_selection.json").write_text(
        json.dumps(reference_selection, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Export mode: {export_mode}")
    print(f"Exported SVG slides: {slide_count}")
    if total_in is not None and total_out is not None:
        print(f"SVG bytes: {total_in} -> {total_out}")
    print(f"Reference SVG selection: {output_dir / 'reference_svg_selection.json'}")
    print(f"Output directory: {output_dir}")
    return 0


# ---------------------------------------------------------------------------
# Slide rendering — default (native, semantic) path
# ---------------------------------------------------------------------------

def _render_slides_native(
    pptx_path: Path,
    output_dir: Path,
    args: argparse.Namespace,
) -> tuple[str, int, int | None, int | None]:
    """Read OOXML directly via pptx_to_svg and emit shape-level SVGs.

    This path preserves text as <text>, picture primitives as <image>, and
    doesn't spawn inline_*.png crop slices. Default since stage G integration.
    """
    from pptx_to_svg import convert_pptx_to_svg
    from pptx_to_svg.converter import ConvertOptions

    options = ConvertOptions(
        media_subdir="assets",
        embed_images=args.embed_images,
        keep_hidden=False,
    )
    result = convert_pptx_to_svg(pptx_path, output_dir, options)
    total_bytes = sum(len(art.svg.encode("utf-8")) for art in result.slides)
    return "pptx_to_svg-native", len(result.slides), total_bytes, total_bytes


# ---------------------------------------------------------------------------
# Slide rendering — legacy (PowerPoint COM / Keynote PDF) path
# ---------------------------------------------------------------------------

def _render_slides_legacy(
    pptx_path: Path,
    output_dir: Path,
    args: argparse.Namespace,
) -> tuple[str, int, int | None, int | None]:
    """Original lossy renderer: rasterize via PowerPoint or Keynote->PDF, then
    externalize/optimize. Preserved for cases where the new semantic converter
    misbehaves; intentionally opt-in (--legacy-render).
    """
    raw_dir = output_dir / "svg_raw"
    raw_svg_files, export_mode = export_pptx_slides_to_svg_with_fallback(
        pptx_path, raw_dir,
    )

    if args.no_externalize:
        return export_mode, len(raw_svg_files), None, None

    cleaned_dir = output_dir / "svg"
    results = externalize_svg_batch(
        svg_files=raw_svg_files,
        output_dir=cleaned_dir,
        assets_dir=output_dir / "assets",
    )
    final_svg_bytes = sum(item.output_svg_bytes for item in results)

    if not args.no_optimize:
        optimize_results, optimize_output_dir = optimize_reference_batch(
            [str(cleaned_dir)], precision=2,
        )
        before_opt = sum(item.original_bytes for item in optimize_results)
        after_opt = sum(item.optimized_bytes for item in optimize_results)
        final_svg_bytes = after_opt
        print(f"Optimized SVG files: {len(optimize_results)}")
        print(f"SVG bytes after structural optimization: {before_opt} -> {after_opt}")
        print(f"Icon candidate report: {optimize_output_dir / 'icon_candidates.json'}")

    if not args.keep_raw:
        for svg_file in raw_dir.glob("*.svg"):
            svg_file.unlink(missing_ok=True)
        if raw_dir.exists():
            raw_dir.rmdir()

    total_before = sum(item.original_svg_bytes for item in results)
    total_images = sum(item.images_externalized for item in results)
    print(f"Inline images externalized: {total_images}")
    return export_mode, len(results), total_before, final_svg_bytes


if __name__ == "__main__":
    raise SystemExit(main())
