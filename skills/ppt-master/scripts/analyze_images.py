#!/usr/bin/env python3
"""
Image Size Analysis Tool
========================
Reports objective parameters for all images in a folder. It does not resolve a
canvas, prescribe a layout, or generate Strategist recommendations.

Usage:
    python scripts/analyze_images.py <images_folder_path>
    python scripts/analyze_images.py projects/xxx/images

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

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
OFFICE_VECTOR_EXTENSIONS = {".emf", ".wmf"}
REPORT_WIDTH = 100
CATEGORY_WIDTH = 50

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
        'category': classify_ratio(ratio),
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
    """Classify an image by its objective aspect-ratio range.

    Ranges: >2.0 ultra-wide, 1.5-2.0 wide, 1.2-1.5 standard
    landscape, 0.8-1.2 near square, and <0.8 portrait.
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
                        'category': classify_ratio(aspect_ratio),
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


def print_results(results: list[ImageAnalysis]) -> None:
    """Print the analysis report to stdout."""

    print("\n" + "=" * REPORT_WIDTH)
    print("Image Size Analysis Report")
    print("=" * REPORT_WIDTH)

    print(
        f"\n{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} "
        f"{'Source':<8} {'Refs':<5} {'Size':<10} {'Category':<20} {'Filename'}"
    )
    print("-" * REPORT_WIDTH)

    for i, img in enumerate(results, 1):
        ratio_source = str(img.get('ratio_source', 'native'))
        usage_count = int(img.get('usage_count', 1))
        base = (
            f"{i:<4} {img['width']:<7} {img['height']:<7} "
            f"{img['aspect_ratio']:<7.2f} {ratio_source:<8} {usage_count:<5} "
            f"{img['filesize_kb']:<10.1f}KB {img['category']:<20}"
        )
        print(f"{base} {img['filename'][:40]}")

    print("-" * REPORT_WIDTH)
    print(f"Total: {len(results)} images\n")

    # Group statistics by objective aspect-ratio ranges.
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


def _format_optional_number(value: object, digits: int = 2) -> str:
    """Format a numeric value for CSV, leaving unavailable facts blank."""
    if not isinstance(value, (int, float)):
        return ""
    return f"{float(value):.{digits}f}"


def save_csv(results: list[ImageAnalysis], csv_path: str | Path) -> None:
    """Atomically save analysis results to a standards-compliant CSV file."""
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
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
                    image["category"],
                ]
                writer.writerow(row)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print(f"\nCSV saved to: {target}")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze objective image-file facts"
    )
    parser.add_argument(
        "images_dir",
        help="Path to the images directory"
    )
    args = parser.parse_args(argv)
    images_dir = Path(args.images_dir).resolve()

    if not images_dir.exists():
        print(f"Error: Directory not found: {images_dir}")
        return 1

    if not images_dir.is_dir():
        print(f"Error: Not a directory: {images_dir}")
        return 1

    print(f"Analyzing: {images_dir}")

    results, errors = _analyze_images(str(images_dir))

    if results:
        print_results(results)
    else:
        print("No readable supported image files found in the directory.")

    analysis_dir = images_dir.parent / "analysis"
    csv_path = analysis_dir / "image_analysis.csv"
    save_csv(results, csv_path)

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
