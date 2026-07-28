#!/usr/bin/env python3
"""
Image Size Analysis Tool
========================
Reports objective parameters (width, height, aspect ratio, category) for all
images in a folder. Intentionally does NOT prescribe a layout — the Strategist
decides narrative intent (hero / atmosphere / side-by-side / accent) per
references/strategist-image.md; this tool only supplies the numbers.

After resolving the canvas from the project, an explicit override, or the
ppt169 fallback, also reports the reference image/text area sizes that would
apply *if* an image is placed side-by-side with body text. Those numbers are
conditional on the Strategist picking the side-by-side intent.

Usage:
    python scripts/analyze_images.py <images_folder_path>
    python scripts/analyze_images.py projects/xxx/images
    python scripts/analyze_images.py projects/xxx/images --canvas ppt43

Output:
    - Analysis report displayed in console
    - Generates image_analysis.csv under the project's analysis/ directory
      (sibling of the images folder), alongside the PPTX intake bundle
"""

import argparse
import csv
import json
import os
import sys
import tempfile
from pathlib import Path

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Error: PIL/Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

try:
    from config import CANVAS_FORMATS, LAYOUT_MARGINS
except ImportError:
    CANVAS_FORMATS = {
        'ppt169': {
            'name': 'PPT 16:9',
            'width': 1280,
            'height': 720,
        },
    }
    LAYOUT_MARGINS = {
        'ppt169': {
            'top': 60, 'right': 60, 'bottom': 60, 'left': 60,
            'content_width': 1160, 'content_height': 600
        },
    }

from project_utils import get_project_info, normalize_canvas_format

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
OFFICE_VECTOR_EXTENSIONS = {".emf", ".wmf"}
REPORT_WIDTH = 100
CATEGORY_WIDTH = 50

# Title area height and gap between image/text areas (px)
TITLE_HEIGHT = 60
LAYOUT_GAP = 20
# Minimum text area dimensions (px)
MIN_TEXT_HEIGHT = 150
MIN_TEXT_WIDTH = 280

ImageAnalysis = dict[str, object]


def _load_image_manifest(images_dir: str) -> dict[str, dict]:
    """Load optional DOCX image metadata keyed by generated filename."""
    manifest_path = Path(images_dir) / "image_manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[WARN] Cannot read image manifest: {exc}")
        return {}
    if not isinstance(data, list):
        return {}

    manifest: dict[str, dict] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        if isinstance(filename, str):
            manifest[filename] = item
    return manifest


def _manifest_ratio(meta: dict | None) -> float | None:
    """Return a positive display ratio from manifest metadata."""
    if not meta:
        return None
    value = meta.get("display_ratio")
    if not isinstance(value, (int, float)):
        return None
    ratio = float(value)
    return ratio if ratio > 0 else None


def _manifest_display_size(meta: dict, ratio: float) -> tuple[int, int]:
    """Return a display-sized stand-in for vector media dimensions."""
    width_in = meta.get("display_width_in")
    height_in = meta.get("display_height_in")
    if isinstance(width_in, (int, float)) and isinstance(height_in, (int, float)):
        width = max(1, int(round(float(width_in) * 96)))
        height = max(1, int(round(float(height_in) * 96)))
        return width, height

    width_emu = meta.get("display_width_emu")
    height_emu = meta.get("display_height_emu")
    if isinstance(width_emu, int) and isinstance(height_emu, int):
        width = max(1, int(round(width_emu / 914400 * 96)))
        height = max(1, int(round(height_emu / 914400 * 96)))
        return width, height

    width = 960
    height = max(1, int(round(width / ratio)))
    return width, height


def _manifest_usage_count(meta: dict | None) -> int:
    """Return how many source occurrences point to one asset."""
    if not meta:
        return 1
    usage_count = meta.get("usage_count")
    if isinstance(usage_count, int) and usage_count > 0:
        return usage_count
    occurrences = meta.get("occurrences")
    if isinstance(occurrences, list) and occurrences:
        return len(occurrences)
    return 1


def _manifest_ratio_variants(meta: dict | None) -> str:
    """Return a compact list of display ratio variants from manifest metadata."""
    if not meta:
        return ""
    variants = meta.get("display_ratio_variants")
    if not isinstance(variants, list):
        return ""
    ratios = [
        f"{float(value):.2f}"
        for value in variants
        if isinstance(value, (int, float)) and value > 0
    ]
    return ";".join(ratios)


def _apply_manifest_metadata(result: ImageAnalysis, meta: dict | None) -> None:
    """Copy optional manifest fields into an image analysis row."""
    result["usage_count"] = _manifest_usage_count(meta)
    result["display_ratio_variants"] = _manifest_ratio_variants(meta)
    if not meta:
        return

    source_ext = meta.get("source_ext")
    original_filename = meta.get("original_filename")
    if isinstance(source_ext, str):
        result["source_ext"] = source_ext
    if isinstance(original_filename, str):
        result["original_filename"] = original_filename
    result["asset_kind"] = meta.get("asset_kind", "bitmap")
    result["svg_renderable"] = meta.get("svg_renderable", True)
    result["pptx_native_supported"] = meta.get("pptx_native_supported", True)


def _has_transparent_pixels(image: Image.Image) -> bool:
    """Return whether any frame contains a pixel with alpha below 255."""
    original_frame = image.tell()
    frame_count = int(getattr(image, "n_frames", 1))
    try:
        for frame_index in range(frame_count):
            image.seek(frame_index)
            if "A" not in image.getbands() and "transparency" not in image.info:
                continue
            rgba = image.convert("RGBA")
            alpha = rgba.getchannel("A")
            try:
                extrema = alpha.getextrema()
            finally:
                alpha.close()
                rgba.close()
            if extrema and extrema[0] < 255:
                return True
    finally:
        image.seek(original_frame)
    return False


def _result_from_manifest(
    filename: str,
    filepath: str,
    meta: dict,
) -> ImageAnalysis | None:
    """Build an analysis row for vector media Pillow cannot decode."""
    ratio = _manifest_ratio(meta)
    if ratio is None:
        return None
    width, height = _manifest_display_size(meta, ratio)
    result: ImageAnalysis = {
        'filename': filename,
        'width': width,
        'height': height,
        'aspect_ratio': ratio,
        'pixel_aspect_ratio': None,
        'source_display_ratio': ratio,
        'ratio_source': 'manifest',
        'format': Path(filename).suffix.lstrip('.').upper(),
        'has_transparent_pixels': None,
        'layout_hint': classify_ratio(ratio),
        'filesize_kb': os.path.getsize(filepath) / 1024,
    }
    _apply_manifest_metadata(result, meta)
    suffix = Path(filename).suffix.lower()
    is_office_vector = suffix in OFFICE_VECTOR_EXTENSIONS
    result["asset_kind"] = meta.get(
        "asset_kind",
        "office_vector" if is_office_vector else "vector",
    )
    result["svg_renderable"] = meta.get("svg_renderable", suffix == ".svg")
    result["pptx_native_supported"] = meta.get(
        "pptx_native_supported",
        is_office_vector or suffix == ".svg",
    )
    return result


def classify_ratio(aspect_ratio: float) -> str:
    """Classify image aspect ratio into layout category.

    Thresholds aligned with image-layout-spec.md:
      >2.0 ultra-wide, 1.5-2.0 wide, 1.2-1.5 standard landscape,
      0.8-1.2 square, <0.8 portrait.
    """
    if aspect_ratio > 2.0:
        return "Ultra-wide"
    elif aspect_ratio > 1.5:
        return "Wide landscape"
    elif aspect_ratio > 1.2:
        return "Standard landscape"
    elif aspect_ratio > 0.8:
        return "Near square"
    else:
        return "Portrait"


def compute_layout_dimensions(
    ratio: float,
    content_w: int,
    content_h: int,
    gap: int = LAYOUT_GAP,
) -> dict:
    """Compute image and text area dimensions following image-layout-spec.md.

    Returns dict with layout_type, image_w, image_h, text_w, text_h.
    """
    # Effective content height (below title)
    H = content_h
    W = content_w

    def _try_top_bottom() -> dict | None:
        img_w = W
        img_h = int(round(W / ratio))
        text_h = H - img_h - gap
        if text_h >= MIN_TEXT_HEIGHT:
            return {
                'layout_type': 'top-bottom',
                'image_w': img_w,
                'image_h': img_h,
                'text_w': W,
                'text_h': text_h,
            }
        return None

    def _try_left_right_height_first() -> dict | None:
        img_h = H
        img_w = int(round(H * ratio))
        text_w = W - img_w - gap
        if text_w >= MIN_TEXT_WIDTH:
            return {
                'layout_type': 'left-right',
                'image_w': img_w,
                'image_h': img_h,
                'text_w': text_w,
                'text_h': H,
            }
        return None

    def _try_left_right_width_constrained() -> dict:
        img_w = int(round(W * 0.7))
        img_h = int(round(img_w / ratio))
        text_w = W - img_w - gap
        return {
            'layout_type': 'left-right',
            'image_w': img_w,
            'image_h': min(img_h, H),
            'text_w': max(text_w, MIN_TEXT_WIDTH),
            'text_h': H,
        }

    # Decision tree per image-layout-spec.md
    if ratio > 1.5:
        # Ultra-wide or wide → try top-bottom first
        result = _try_top_bottom()
        if result:
            return result
        # Fallback to left-right (wide-constrained)
        return _try_left_right_width_constrained()
    else:
        # Standard landscape, square, portrait → try left-right (height-first)
        result = _try_left_right_height_first()
        if result:
            return result
        # Fallback to left-right (width-constrained)
        return _try_left_right_width_constrained()


def _analyze_images(images_dir: str) -> tuple[list[ImageAnalysis], list[str]]:
    """Analyze all image files in a directory.

    Args:
        images_dir: Directory that contains image files.

    Returns:
        Sorted image analysis records and supported files that could not be read.
    """

    results: list[ImageAnalysis] = []
    errors: list[str] = []
    manifest = _load_image_manifest(images_dir)

    for filename in sorted(os.listdir(images_dir)):
        filepath = os.path.join(images_dir, filename)
        if not os.path.isfile(filepath):
            continue

        suffix = Path(filename).suffix.lower()
        meta = manifest.get(filename)

        if suffix in IMAGE_EXTENSIONS:
            try:
                with Image.open(filepath) as img:
                    image_format = img.format or suffix.lstrip(".").upper()
                    has_transparent_pixels = _has_transparent_pixels(img)
                    oriented = ImageOps.exif_transpose(img)
                    try:
                        width, height = oriented.size
                    finally:
                        if oriented is not img:
                            oriented.close()

                    aspect_ratio = width / height

                    result: ImageAnalysis = {
                        'filename': filename,
                        'width': width,
                        'height': height,
                        'aspect_ratio': aspect_ratio,
                        'pixel_aspect_ratio': aspect_ratio,
                        'source_display_ratio': _manifest_ratio(meta),
                        'ratio_source': 'native',
                        'format': image_format,
                        'has_transparent_pixels': has_transparent_pixels,
                        'layout_hint': classify_ratio(aspect_ratio),
                        'filesize_kb': os.path.getsize(filepath) / 1024
                    }
                    _apply_manifest_metadata(result, meta)
                    results.append(result)
            except (
                EOFError,
                OSError,
                SyntaxError,
                ValueError,
                ZeroDivisionError,
                Image.DecompressionBombError,
            ) as exc:
                message = f"{filename}: {exc}"
                errors.append(message)
                print(f"[WARN] Cannot read {message}")
        elif meta:
            result = _result_from_manifest(filename, filepath, meta)
            if result:
                results.append(result)
            else:
                message = f"{filename}: manifest has no valid display_ratio"
                errors.append(message)
                print(f"[WARN] Cannot analyze {message}")
        elif suffix in OFFICE_VECTOR_EXTENSIONS:
            message = f"{filename}: image_manifest.json metadata is required"
            errors.append(message)
            print(f"[WARN] Cannot analyze {message}")

    return results, errors


def analyze_images(images_dir: str) -> list[ImageAnalysis]:
    """Analyze readable image files while preserving the existing public API."""
    results, _ = _analyze_images(images_dir)
    return results


def enrich_with_layout(
    results: list[ImageAnalysis],
    canvas_key: str,
) -> None:
    """Add computed layout dimensions to each result in-place."""
    margins = LAYOUT_MARGINS.get(canvas_key)

    if not margins:
        print(f"[WARN] No layout margins for canvas '{canvas_key}', skipping dimension calculation")
        return

    content_w = margins['content_width']
    content_h = margins['content_height']

    for img in results:
        dims = compute_layout_dimensions(img['aspect_ratio'], content_w, content_h)
        img.update(dims)


def print_results(results: list[ImageAnalysis]) -> None:
    """Print the analysis report to stdout."""

    print("\n" + "=" * REPORT_WIDTH)
    print("Image Size Analysis Report")
    print("=" * REPORT_WIDTH)

    has_layout = 'layout_type' in results[0] if results else False

    if has_layout:
        print("\nNote: 'Img (SxS)' shows the image area *if* the Strategist chooses the")
        print("side-by-side intent for this image. Decide narrative intent first — see")
        print("references/strategist-image.md. Hero / atmosphere / accent intents ignore it.\n")
        print(f"{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} {'Source':<8} {'Refs':<5} {'Size':<10} {'Category':<20} {'Img (SxS)':<14} {'Filename'}")
    else:
        print(f"\n{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} {'Source':<8} {'Refs':<5} {'Size':<10} {'Category':<20} {'Filename'}")
    print("-" * REPORT_WIDTH)

    for i, img in enumerate(results, 1):
        ratio_source = str(img.get('ratio_source', 'native'))
        usage_count = int(img.get('usage_count', 1))
        base = f"{i:<4} {img['width']:<7} {img['height']:<7} {img['aspect_ratio']:<7.2f} {ratio_source:<8} {usage_count:<5} {img['filesize_kb']:<10.1f}KB {img['layout_hint']:<20}"
        if has_layout:
            img_area = f"{img['image_w']}x{img['image_h']}"
            print(f"{base} {img_area:<14} {img['filename'][:35]}")
        else:
            print(f"{base} {img['filename'][:40]}")

    print("-" * REPORT_WIDTH)
    print(f"Total: {len(results)} images\n")

    # Group statistics by aspect ratio (aligned with image-layout-spec.md thresholds)
    print("\nGroup by Aspect Ratio:")
    print("-" * CATEGORY_WIDTH)

    categories = {
        "Ultra-wide (>2.0)": [],
        "Wide (1.5-2.0)": [],
        "Standard (1.2-1.5)": [],
        "Square (0.8-1.2)": [],
        "Portrait (<0.8)": [],
    }

    for img in results:
        ar = img['aspect_ratio']
        if ar > 2.0:
            categories["Ultra-wide (>2.0)"].append(img)
        elif ar > 1.5:
            categories["Wide (1.5-2.0)"].append(img)
        elif ar > 1.2:
            categories["Standard (1.2-1.5)"].append(img)
        elif ar > 0.8:
            categories["Square (0.8-1.2)"].append(img)
        else:
            categories["Portrait (<0.8)"].append(img)

    for cat, imgs in categories.items():
        if imgs:
            print(f"\n{cat}: {len(imgs)} images")
            for img in imgs[:5]:  # Show only the first 5
                print(f"  - {img['width']}x{img['height']} (ratio {img['aspect_ratio']:.2f}) - {img['filename'][:35]}...")
            if len(imgs) > 5:
                print(f"  ... and {len(imgs) - 5} more")

    native_only = [
        img for img in results
        if img.get('asset_kind') == 'office_vector'
        and not img.get('svg_renderable', True)
    ]
    if native_only:
        print("\nOffice vector assets for PPTX native passthrough:")
        for img in native_only[:10]:
            original = img.get('original_filename', img['filename'])
            print(f"  - {original} (display ratio {img['aspect_ratio']:.2f}; SVG preview not supported)")
        if len(native_only) > 10:
            print(f"  ... and {len(native_only) - 10} more")


def generate_markdown(results: list[ImageAnalysis], canvas_key: str) -> None:
    """Print a Markdown-ready image inventory section."""
    print("\n" + "=" * REPORT_WIDTH)
    print("Markdown Snippet for Strategist (Copy & Paste)")
    print("=" * REPORT_WIDTH)

    has_layout = 'layout_type' in results[0] if results else False
    fmt_name = CANVAS_FORMATS.get(canvas_key, {}).get('name', canvas_key)

    print(f"\n## Image Resource Inventory (Auto-scan Results — {fmt_name})\n")

    print("> Decide narrative intent per image (hero / atmosphere / side-by-side /")
    print("> accent) per `references/strategist-image.md` before filling the table. The")
    print("> `Img Area (SxS)` / `Text Area (SxS)` columns only apply if the chosen")
    print("> intent is side-by-side; ignore them for hero / atmosphere / accent intents.\n")

    if has_layout:
        print("| Filename | Size | Ratio | Category | Img Area (SxS) | Text Area (SxS) | Intent | Usage | Type | Status | Generation Description |")
        print("|----------|------|-------|----------|----------------|-----------------|--------|-------|------|--------|-----------------------|")
    else:
        print("| Filename | Size | Ratio | Category | Intent | Usage | Type | Status | Generation Description |")
        print("|----------|------|-------|----------|--------|-------|------|--------|-----------------------|")

    for img in results:
        ratio_str = f"{img['aspect_ratio']:.2f}"
        asset_kind = str(img.get('asset_kind', 'bitmap'))
        image_type = "Office Vector" if asset_kind == "office_vector" else ""
        status = (
            "PPTX Native Only"
            if asset_kind == "office_vector" and not img.get('svg_renderable', True)
            else "Existing"
        )

        if has_layout:
            img_area = f"{img['image_w']}x{img['image_h']}"
            text_area = f"{img['text_w']}x{img['text_h']}"
            print(f"| {img['filename']} | {img['width']}x{img['height']} | {ratio_str} | {img['layout_hint']} | {img_area} | {text_area} | (to be filled) | {img.get('usage_count', 1)} refs | {image_type} | {status} | - |")
        else:
            print(f"| {img['filename']} | {img['width']}x{img['height']} | {ratio_str} | {img['layout_hint']} | (to be filled) | {img.get('usage_count', 1)} refs | {image_type} | {status} | - |")

    print("\n" + "=" * REPORT_WIDTH + "\n")


def _format_optional_number(value: object, digits: int = 2) -> str:
    """Format a numeric value for CSV, leaving unavailable facts blank."""
    if not isinstance(value, (int, float)):
        return ""
    return f"{float(value):.{digits}f}"


def save_csv(
    results: list[ImageAnalysis],
    csv_path: str | Path,
    include_layout: bool | None = None,
) -> None:
    """Atomically save analysis results to a standards-compliant CSV file."""
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if include_layout is None:
        include_layout = bool(results and "layout_type" in results[0])
    header = [
        "No",
        "Filename",
        "Width",
        "Height",
        "AspectRatio",
        "PixelAspectRatio",
        "SourceDisplayRatio",
        "RatioSource",
        "Format",
        "HasTransparentPixels",
        "UsageCount",
        "DisplayRatioVariants",
        "AssetKind",
        "SvgRenderable",
        "PptxNativeSupported",
        "SizeKB",
        "Category",
    ]
    if include_layout:
        header.extend(["ImageArea_SxS", "TextArea_SxS"])

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(header)
            for index, image in enumerate(results, 1):
                row = [
                    index,
                    image["filename"],
                    image["width"],
                    image["height"],
                    _format_optional_number(image["aspect_ratio"]),
                    _format_optional_number(image.get("pixel_aspect_ratio")),
                    _format_optional_number(image.get("source_display_ratio")),
                    image.get("ratio_source", "native"),
                    image.get("format", ""),
                    image.get("has_transparent_pixels", ""),
                    image.get("usage_count", 1),
                    image.get("display_ratio_variants", ""),
                    image.get("asset_kind", "bitmap"),
                    image.get("svg_renderable", True),
                    image.get("pptx_native_supported", True),
                    _format_optional_number(image["filesize_kb"], digits=1),
                    image["layout_hint"],
                ]
                if include_layout:
                    image_area = (
                        f"{image['image_w']}x{image['image_h']}"
                        if "image_w" in image
                        else ""
                    )
                    text_area = (
                        f"{image['text_w']}x{image['text_h']}"
                        if "text_w" in image
                        else ""
                    )
                    row.extend([image_area, text_area])
                writer.writerow(row)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"\nCSV saved to: {target}")


def _resolve_canvas_key(images_dir: Path, override: str | None) -> tuple[str, str]:
    """Resolve canvas from an explicit override, project context, or fallback."""
    if override:
        return normalize_canvas_format(override), "--canvas"

    project_dir = images_dir.parent if images_dir.name == "images" else images_dir
    project_info = get_project_info(str(project_dir))
    project_canvas = normalize_canvas_format(str(project_info.get("format", "")))
    if project_canvas in CANVAS_FORMATS:
        return project_canvas, "project"
    return "ppt169", "fallback"


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze image sizes and compute PPT layout dimensions"
    )
    parser.add_argument(
        "images_dir",
        help="Path to the images directory"
    )
    parser.add_argument(
        "--canvas",
        help=(
            "Canvas format override. By default, infer it from the project "
            f"directory and fall back to ppt169. Available: "
            f"{', '.join(sorted(CANVAS_FORMATS.keys()))}"
        ),
    )

    args = parser.parse_args(argv)
    images_dir = Path(args.images_dir).resolve()

    if not images_dir.exists():
        print(f"Error: Directory not found: {images_dir}")
        return 1

    if not images_dir.is_dir():
        print(f"Error: Not a directory: {images_dir}")
        return 1

    canvas_key, canvas_source = _resolve_canvas_key(images_dir, args.canvas)
    if canvas_key not in CANVAS_FORMATS:
        available = ", ".join(sorted(CANVAS_FORMATS.keys()))
        print(f"Error: Unknown canvas format '{canvas_key}'. Available: {available}")
        return 1

    fmt = CANVAS_FORMATS[canvas_key]
    print(f"Analyzing: {images_dir}")
    print(
        f"Canvas: {fmt.get('name', canvas_key)} "
        f"({fmt.get('width', '?')}x{fmt.get('height', '?')}; {canvas_source})"
    )

    results, errors = _analyze_images(str(images_dir))
    enrich_with_layout(results, canvas_key)

    if results:
        print_results(results)
        generate_markdown(results, canvas_key)
    else:
        print("No readable supported image files found in the directory.")

    analysis_dir = images_dir.parent / "analysis"
    csv_path = analysis_dir / "image_analysis.csv"
    save_csv(results, csv_path, include_layout=canvas_key in LAYOUT_MARGINS)

    if errors:
        print(
            f"[ERROR] {len(errors)} supported image file(s) could not be analyzed; "
            "the current report was still written.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
