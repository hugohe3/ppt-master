#!/usr/bin/env python3
"""
PPT Master - Image Layer Tool

Layer helpers for the Image to PPTX profile. `check` tests whether an extracted
layer (RGBA, or a flat #FF00FF / #00FF00 key) is registered to its source page:
its opaque pixels must match the page at their own position better than at any
nearby shift. `diff-matte` derives a registered layer without a generator by
keeping the page's own pixels wherever the page differs from a base image that
had those objects removed.

Usage:
    python3 scripts/image_layers.py check <project_path> --page-image <png> --layer <png>
    python3 scripts/image_layers.py diff-matte <project_path> --page-image <png> --base <png> --out <png>

Examples:
    python3 scripts/image_layers.py check projects/demo --page-image images/source-pages/01.png \\
        --layer images/01_plate.png
    python3 scripts/image_layers.py diff-matte projects/demo --page-image images/source-pages/01.png \\
        --base images/01_base.png --out images/01_subject.png --ocr analysis/ocr/01.json

Dependencies:
    Pillow, numpy

See workflows/profiles/image-to-pptx.md for when each command runs and
scripts/docs/image.md for thresholds and outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

CHECK_WIDTH = 640
SHIFTS = (-10, -5, 0, 5, 10)
KEYS = ((255, 0, 255), (0, 255, 0))


def layer_alpha(image: Image.Image) -> np.ndarray:
    """Return a boolean opacity mask from real alpha, else from a flat magenta or green key."""
    rgba = np.asarray(image.convert("RGBA")).astype(int)
    if (rgba[..., 3] < 20).mean() > 0.05:
        return rgba[..., 3] > 200
    for key in KEYS:
        keyed = np.all(np.abs(rgba[..., :3] - np.array(key)) < 60, axis=2)
        if keyed.mean() > 0.05:
            return ~keyed
    return np.ones(rgba.shape[:2], bool)


def cmd_check(args: argparse.Namespace) -> int:
    project = Path(args.project_path).resolve()
    page = Image.open(project / args.page_image).convert("RGB")
    layer = Image.open(project / args.layer)
    height = round(CHECK_WIDTH * page.size[1] / page.size[0])
    src = np.asarray(page.resize((CHECK_WIDTH, height)), float)
    resized = layer.resize((CHECK_WIDTH, height))
    rgb = np.asarray(resized.convert("RGB"), float)
    alpha = layer_alpha(resized)
    if not alpha.any():
        print("Layer has no opaque pixels.", file=sys.stderr)
        return 1
    diffs = {}
    for dx in SHIFTS:
        for dy in SHIFTS:
            mask = np.roll(np.roll(alpha, dx, 1), dy, 0)
            moved = np.roll(np.roll(rgb, dx, 1), dy, 0)
            diffs[(dx, dy)] = float(np.abs(moved[mask] - src[mask]).mean())
    origin = diffs[(0, 0)]
    nearest = min(value for shift, value in diffs.items() if shift != (0, 0))
    best = min(diffs, key=diffs.get)
    registered = origin <= args.ratio * nearest
    scale = page.size[0] / CHECK_WIDTH
    print(f"{args.layer}: diff at origin {origin:.1f}, best shifted {nearest:.1f}, "
          f"best offset ({best[0] * scale:+.0f}, {best[1] * scale:+.0f}) page px")
    print("Registered" if registered else "NOT registered")
    return 0 if registered else 3


def text_mask(ocr_path: Path, size: tuple[int, int], pad: float) -> np.ndarray:
    data = json.loads(ocr_path.read_text(encoding="utf-8"))
    scale = size[0] / data["canvas"][0]
    mask = np.zeros((size[1], size[0]), bool)
    for block in data["blocks"]:
        if block.get("skip"):
            continue
        for line in block["lines"]:
            x0 = max(int((line["x"] - pad) * scale), 0)
            y0 = max(int((line["y"] - pad) * scale), 0)
            x1 = int((line["x"] + line["w"] + pad) * scale)
            y1 = int((line["y"] + line["h"] + pad) * scale)
            mask[y0:y1, x0:x1] = True
    return mask


def cmd_diff_matte(args: argparse.Namespace) -> int:
    project = Path(args.project_path).resolve()
    page = Image.open(project / args.page_image).convert("RGB")
    base = Image.open(project / args.base).convert("RGB").resize(page.size, Image.LANCZOS)
    distance = np.sqrt(((np.asarray(page, float) - np.asarray(base, float)) ** 2).sum(axis=2))
    keep = distance > args.threshold
    if args.ocr:
        keep &= ~text_mask(project / args.ocr, page.size, 6)
    mask = Image.fromarray((keep * 255).astype("uint8"))
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = np.asarray(page.convert("RGBA")).copy()
    rgba[..., 3] = np.asarray(mask)
    out = project / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(out)
    print(f"{out.relative_to(project)}: {np.asarray(mask).astype(bool).mean() * 100:.1f}% of the page kept "
          f"from source pixels at {page.size[0]}x{page.size[1]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check layer registration and derive registered layers for Image to PPTX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Exit 0 when a layer is registered to its page, 3 when not.")
    check.add_argument("project_path")
    check.add_argument("--page-image", required=True, help="Canonical page image, relative to the project.")
    check.add_argument("--layer", required=True, help="Extracted layer (RGBA or flat magenta/green key).")
    check.add_argument("--ratio", type=float, default=0.8,
                       help="Origin difference must be at most this fraction of the best shifted one (default 0.8).")
    check.set_defaults(func=cmd_check)

    matte = sub.add_parser("diff-matte", help="Keep page pixels where the page differs from an object-removed base.")
    matte.add_argument("project_path")
    matte.add_argument("--page-image", required=True, help="Canonical page image, relative to the project.")
    matte.add_argument("--base", required=True, help="Base image with the objects removed.")
    matte.add_argument("--out", required=True, help="Output RGBA layer, relative to the project.")
    matte.add_argument("--ocr", help="Reviewed analysis/ocr/<page>.json; its text boxes are excluded.")
    matte.add_argument("--threshold", type=float, default=60.0,
                       help="RGB distance above which a pixel belongs to the layer (default 60).")
    matte.set_defaults(func=cmd_diff_matte)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
