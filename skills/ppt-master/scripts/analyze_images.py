#!/usr/bin/env python3
"""
Image Size Analysis Tool
========================
Analyzes width, height, and aspect ratio of all images in a specified folder,
and outputs PPT layout recommendations.

Usage:
    python scripts/analyze_images.py <images_folder_path>
    python scripts/analyze_images.py projects/xxx/images

Output:
    - Analysis report displayed in console
    - Generates image_analysis.csv in the parent directory of the images folder
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL/Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}
REPORT_WIDTH = 100
CATEGORY_WIDTH = 50
PPT_WIDTH = 1280
PPT_HEIGHT = 720
FULL_SCREEN_MIN_RATIO = 1.5
FULL_SCREEN_MAX_RATIO = 2.0

ImageAnalysis = dict[str, str | float | int]


def analyze_images(images_dir: str) -> list[ImageAnalysis]:
    """Analyze all image files in a directory.

    Args:
        images_dir: Directory that contains image files.

    Returns:
        A list of image analysis records sorted by filename.
    """

    results: list[ImageAnalysis] = []

    # Iterate through all files in the directory
    for filename in sorted(os.listdir(images_dir)):
        filepath = os.path.join(images_dir, filename)

        # Check if it is an image file
        if os.path.isfile(filepath) and Path(filename).suffix.lower() in IMAGE_EXTENSIONS:
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    aspect_ratio = width / height

                    # Determine PPT layout recommendation
                    if aspect_ratio > FULL_SCREEN_MIN_RATIO:
                        layout_hint = "Wide landscape"
                    elif aspect_ratio > 1.2:
                        layout_hint = "Standard landscape"
                    elif aspect_ratio > 0.8:
                        layout_hint = "Near square"
                    elif aspect_ratio > 0.6:
                        layout_hint = "Standard portrait"
                    else:
                        layout_hint = "Narrow portrait"

                    results.append({
                        'filename': filename,
                        'width': width,
                        'height': height,
                        'aspect_ratio': aspect_ratio,
                        'layout_hint': layout_hint,
                        'filesize_kb': os.path.getsize(filepath) / 1024
                    })
            except Exception as e:
                print(f"[WARN] Cannot read {filename}: {e}")

    return results


def print_results(results: list[ImageAnalysis]) -> None:
    """Print the analysis report to stdout.

    Args:
        results: Image analysis records returned by `analyze_images`.
    """

    print("\n" + "=" * REPORT_WIDTH)
    print("Image Size Analysis Report")
    print("=" * REPORT_WIDTH)

    # Table header
    print(f"\n{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} {'Size':<10} {'Layout':<15} {'Filename'}")
    print("-" * REPORT_WIDTH)

    for i, img in enumerate(results, 1):
        print(f"{i:<4} {img['width']:<7} {img['height']:<7} {img['aspect_ratio']:<7.2f} {img['filesize_kb']:<10.1f}KB {img['layout_hint']:<15} {img['filename'][:40]}")

    print("-" * REPORT_WIDTH)
    print(f"Total: {len(results)} images\n")

    # Group statistics by aspect ratio
    print("\nGroup by Aspect Ratio:")
    print("-" * CATEGORY_WIDTH)

    categories = {
        "Wide (>1.5)": [],
        "Standard (1.2-1.5)": [],
        "Square (0.8-1.2)": [],
        "Portrait (0.6-0.8)": [],
        "Narrow (<0.6)": []
    }

    for img in results:
        ar = img['aspect_ratio']
        if ar > 1.5:
            categories["Wide (>1.5)"].append(img)
        elif ar > 1.2:
            categories["Standard (1.2-1.5)"].append(img)
        elif ar > 0.8:
            categories["Square (0.8-1.2)"].append(img)
        elif ar > 0.6:
            categories["Portrait (0.6-0.8)"].append(img)
        else:
            categories["Narrow (<0.6)"].append(img)

    for cat, imgs in categories.items():
        if imgs:
            print(f"\\n{cat}: {len(imgs)} images")
            for img in imgs[:5]:  # Show only the first 5
                print(f"  - {img['width']}x{img['height']} (ratio {img['aspect_ratio']:.2f}) - {img['filename'][:35]}...")
            if len(imgs) > 5:
                print(f"  ... and {len(imgs) - 5} more")

    # PPT layout recommendations
    print("\\n" + "=" * REPORT_WIDTH)
    print("PPT Fit Suggestions (16:9 = 1280x720)")
    print("=" * REPORT_WIDTH)

    ppt_width, ppt_height = PPT_WIDTH, PPT_HEIGHT
    ppt_ratio = ppt_width / ppt_height

    print(f"\\nStandard PPT canvas: {ppt_width}x{ppt_height} (ratio {ppt_ratio:.2f})")

    fit_count = 0
    for img in results:
        if FULL_SCREEN_MIN_RATIO <= img["aspect_ratio"] <= FULL_SCREEN_MAX_RATIO:
            fit_count += 1

    print(f"\\nImages suitable for full-screen display: {fit_count}")


def generate_markdown(results: list[ImageAnalysis]) -> None:
    """Print a Markdown-ready image inventory section.

    Args:
        results: Image analysis records returned by `analyze_images`.
    """
    print("\\n" + "=" * REPORT_WIDTH)
    print("Markdown Snippet for Strategist (Copy & Paste)")
    print("=" * REPORT_WIDTH)
    print("\\n## Image Resource Inventory (Auto-scan Results)\\n")
    print("| Filename | Size | Ratio | Layout Suggestion | Usage | Status | Generation Description |")
    print("|----------|------|-------|-------------------|-------|--------|-----------------------|")

    for img in results:
        # Simplify layout suggestion description to match Strategist conventions
        layout_desc = img['layout_hint']
        if img['aspect_ratio'] > 2.0:
            layout_desc += " (suitable for full-width/split)"
        elif img['aspect_ratio'] > 1.2:
            layout_desc += " (suitable for full-screen/illustration)"
        elif img['aspect_ratio'] < 0.8:
            layout_desc += " (suitable for side-by-side columns)"

        # Usage and generation description to be filled in by the strategist; placeholders used here
        print(f"| {img['filename']} | {img['width']}x{img['height']} | {img['aspect_ratio']:.2f} | {layout_desc} | (to be filled) | Existing | - |")
    print("\\n" + "=" * REPORT_WIDTH + "\\n")


def save_csv(results: list[ImageAnalysis], csv_path: str) -> None:
    """Save analysis results to a CSV file.

    Args:
        results: Image analysis records returned by `analyze_images`.
        csv_path: Destination CSV path.
    """
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("No,Filename,Width,Height,AspectRatio,SizeKB,Layout\n")
        for i, img in enumerate(results, 1):
            f.write(f"{i},{img['filename']},{img['width']},{img['height']},{img['aspect_ratio']:.2f},{img['filesize_kb']:.1f},{img['layout_hint']}\n")
    print(f"\nCSV saved to: {csv_path}")


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_images.py <images_folder_path>")
        print("Example: python analyze_images.py projects/myproject/images")
        print("         python analyze_images.py C:/path/to/images")
        sys.exit(1)

    images_dir = sys.argv[1]

    # Convert to absolute path
    images_dir = os.path.abspath(images_dir)

    if not os.path.exists(images_dir):
        print(f"Error: Directory not found: {images_dir}")
        sys.exit(1)

    if not os.path.isdir(images_dir):
        print(f"Error: Not a directory: {images_dir}")
        sys.exit(1)

    print(f"Analyzing: {images_dir}")

    results = analyze_images(images_dir)

    if results:
        print_results(results)
        generate_markdown(results)

        # Save to CSV file (saved in the parent directory of the images folder)
        parent_dir = os.path.dirname(images_dir)
        csv_path = os.path.join(parent_dir, "image_analysis.csv")
        save_csv(results, csv_path)
    else:
        print("No image files found in the directory.")


if __name__ == "__main__":
    main()
