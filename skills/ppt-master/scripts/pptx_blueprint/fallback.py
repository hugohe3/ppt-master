"""Fallback engine — delegate to the legacy pptx_template_import.py when the
native blueprint pipeline can't handle a source PPTX.

Use cases:
    - Blueprint parsing raised an unrecoverable error.
    - Extracted shape count was below the viability threshold.
    - User explicitly selected `--engine legacy`.

Flow:
    1. Call export_pptx_slides_to_svg_with_fallback() — tries PowerPoint COM
       on Windows, else Keynote via osascript + PDF->SVG via PyMuPDF.
    2. Run template_import/externalize_images to pull inline base64 images out.
    3. Run template_import/optimize_reference for numeric rounding and clipPath
       dedup.
    4. Scan each cleaned SVG with our own linter (svg_emitter.lint_svg).
       Violations are reported — NOT raised — because fallback output is
       inherently best-effort and may legitimately contain clipPath on images
       (which the linter doesn't flag) plus some residual quirks.
    5. Copy cleaned SVGs into <output_dir>/ with a simple slide_NN.svg naming
       (no clustering / fingerprinting applied — this branch is a last resort).

Prerequisites:
    - macOS: Keynote installed (for PPTX -> PDF -> SVG path).
    - Windows: PowerPoint installed.
    - Linux: NOT supported — users should stick with the blueprint engine.
"""

from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FallbackResult:
    """Outcome of the fallback pipeline run."""
    is_available: bool
    svg_files: list[Path] = field(default_factory=list)
    export_method: str = ''  # 'powerpoint-svg' / 'powerpoint-pdf-fallback' / 'keynote-pdf'
    warnings: list[str] = field(default_factory=list)
    unavailable_reason: str = ''


# ---------------------------------------------------------------------------
# Lazy imports of the legacy helpers — they have heavy transitive dependencies
# (PyMuPDF on some paths) that we only want to load when fallback is actually used.
# ---------------------------------------------------------------------------

def _load_legacy_modules():
    """Dynamically import pptx_template_import and template_import helpers.

    Placed in the same scripts/ parent on sys.path so `import
    pptx_template_import` works regardless of invocation method.
    """
    scripts_dir = Path(__file__).resolve().parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    pti = importlib.import_module('pptx_template_import')
    ext = importlib.import_module('template_import.externalize_images')
    opt = importlib.import_module('template_import.optimize_reference')
    return pti, ext, opt


# ---------------------------------------------------------------------------
# Availability probe
# ---------------------------------------------------------------------------

def probe_availability() -> tuple[bool, str]:
    """Check whether fallback prerequisites are met on this host.

    Returns (is_available, reason). `reason` is empty when available.
    """
    system = platform.system()
    if system == 'Windows':
        # PowerShell + PowerPoint COM; we can't easily pre-probe without running.
        return True, ''
    if system == 'Darwin':
        # Need Keynote for PPTX -> PDF, then PyMuPDF for PDF -> SVG.
        try:
            importlib.import_module('fitz')  # PyMuPDF
        except ImportError:
            return False, (
                "PyMuPDF (fitz) is required for the macOS fallback. "
                "Install with: pip install PyMuPDF"
            )
        # Keynote presence check: use mdfind / osascript
        import subprocess
        check = subprocess.run(
            ['osascript', '-e', 'tell application "Finder" to exists POSIX file '
             '"/System/Applications/Keynote.app" or exists POSIX file '
             '"/Applications/Keynote.app"'],
            capture_output=True, text=True, check=False,
        )
        if 'true' not in check.stdout.lower():
            return False, (
                "Keynote is required for macOS fallback (used to convert PPTX -> PDF). "
                "Install Keynote from the Mac App Store, or use --engine blueprint."
            )
        return True, ''

    # Linux / others: not supported
    return False, (
        f"Fallback engine requires Windows (PowerPoint) or macOS (Keynote); "
        f"detected {system}. Use --engine blueprint on this platform."
    )


# ---------------------------------------------------------------------------
# Main fallback runner
# ---------------------------------------------------------------------------

def run_fallback(
    pptx_path: Path,
    output_dir: Path,
    externalize_images: bool = True,
    optimize_svgs: bool = True,
) -> FallbackResult:
    """Execute the full fallback pipeline.

    Args:
        pptx_path: Source .pptx file.
        output_dir: Destination directory for the cleaned SVGs and assets.
        externalize_images: Replace inline Base64 images with external files.
        optimize_svgs: Apply optimize_reference cleanup (dedup clipPaths,
            round numerics, flatten tspans).

    Returns:
        FallbackResult. When is_available is False, svg_files is empty and
        unavailable_reason explains the failure.
    """
    result = FallbackResult(is_available=False)

    available, reason = probe_availability()
    if not available:
        result.unavailable_reason = reason
        return result

    try:
        pti, ext, opt = _load_legacy_modules()
    except ImportError as exc:
        result.unavailable_reason = f"Failed to import legacy modules: {exc}"
        return result

    output_dir.mkdir(parents=True, exist_ok=True)
    svg_raw_dir = output_dir / 'svg_raw'
    svg_raw_dir.mkdir(exist_ok=True)

    # Step 1: export PPTX -> SVG using external app
    try:
        svg_files, method = pti.export_pptx_slides_to_svg_with_fallback(
            pptx_path, svg_raw_dir,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        result.unavailable_reason = f"External app export failed: {exc}"
        return result

    result.is_available = True
    result.export_method = method

    # Step 2: externalize inline base64 images (reduce bloat)
    if externalize_images:
        assets_dir = output_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        try:
            ext.externalize_svg_batch(
                svg_paths=svg_files,
                output_svg_dir=output_dir,
                assets_dir=assets_dir,
            )
            # After externalization, the cleaned svgs live in output_dir directly
            svg_files = sorted(output_dir.glob('slide_*.svg'))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            result.warnings.append(f"Image externalization failed: {exc}")

    # Step 3: optimize (deduplicate clipPaths, round numerics)
    if optimize_svgs and svg_files:
        try:
            opt.optimize_reference_batch(svg_files)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            result.warnings.append(f"SVG optimization failed: {exc}")

    # Step 4: compliance scan (non-fatal — report only)
    from .svg_emitter import lint_svg
    total_violations = 0
    for svg_path in svg_files:
        try:
            content = svg_path.read_text(encoding='utf-8')
        except OSError:
            continue
        vios = lint_svg(content)
        if vios:
            total_violations += len(vios)

    if total_violations > 0:
        result.warnings.append(
            f"Fallback SVG output has {total_violations} linter violations. "
            "Manual cleanup may be needed before consuming with svg_to_pptx."
        )

    result.svg_files = list(svg_files)
    return result
