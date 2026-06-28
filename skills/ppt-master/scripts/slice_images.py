#!/usr/bin/env python3
"""
PPT Master - Illustration Sheet Slicer

Slice one AI-generated "illustration sheet" (a single image whose prompt laid
out several illustration elements in a grid) into N individual element files in
the project's `images/` folder. This is the cheap-and-consistent path for spot
illustrations: generate one multi-element sheet with `image_gen.py` (one call,
one coherent style/palette), then cut the cells out here so each element is a
normal image the Executor places like any other.

Two optional cleanups address the realities of cropping a raster sheet:
  --trim   tight-crop each cell to its content bounding box, so imprecise AI
           placement inside a cell does not leave lopsided margins.
  --alpha  knock the (flat) sheet background out to transparency, so an element
           can sit on a differently-colored slide without a visible box.
Both need a background color; it is auto-sampled from each cell's border unless
you pass --bg.

Usage:
    python3 scripts/slice_images.py <sheet_image> --grid RxC [options]

Examples:
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3 \
        --names team,product,customer,growth,risk,vision --trim --alpha
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 1x4 \
        --prefix spot_ --bg "#F8F9FA" --alpha

Dependencies:
    Pillow
"""

import argparse
import re
import sys
from pathlib import Path
from statistics import median
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

from PIL import Image, ImageChops, ImageFilter

_GRID_RE = re.compile(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$")
_BG_SAMPLE_BORDER = 2
_DEFAULT_FEATHER = 4


def _log(msg: str) -> None:
    """Print progress to stderr (stdout carries the created file paths)."""
    print(msg, file=sys.stderr)


def parse_grid(spec: str) -> tuple[int, int]:
    """Parse a 'RxC' grid spec into (rows, cols)."""
    m = _GRID_RE.match(spec)
    if not m:
        raise ValueError(f"--grid must look like '2x3' (rows x cols), got {spec!r}")
    rows, cols = int(m.group(1)), int(m.group(2))
    if rows < 1 or cols < 1:
        raise ValueError(f"--grid rows and cols must be >= 1, got {rows}x{cols}")
    return rows, cols


def parse_hex(value: str) -> tuple[int, int, int]:
    """Parse '#RRGGBB' / 'RRGGBB' into an (r, g, b) tuple."""
    h = value.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"--bg must be a 6-digit hex color, got {value!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _safe_basename(name: str) -> str:
    """Reject path components in an output name — this tool writes bare files only."""
    base = name.strip()
    if (not base or base in {".", ".."} or ".." in base
            or "/" in base or "\\" in base or Path(base).is_absolute()):
        raise ValueError(f"unsafe output name {name!r}: must be a bare filename, no path parts")
    return base


def _sample_bg(cell: Image.Image) -> tuple[int, int, int]:
    """Estimate the flat background color from a cell's border ring."""
    rgb = cell.convert("RGB")
    w, h = rgb.size
    border = max(1, min(_BG_SAMPLE_BORDER, w, h))
    px = rgb.load()
    pixels = []

    for y in range(border):
        for x in range(w):
            pixels.append(px[x, y])

    bottom_start = max(border, h - border)
    for y in range(bottom_start, h):
        for x in range(w):
            pixels.append(px[x, y])

    right_start = max(border, w - border)
    for y in range(border, bottom_start):
        for x in range(border):
            pixels.append(px[x, y])
        for x in range(right_start, w):
            pixels.append(px[x, y])

    return tuple(round(median(channel)) for channel in zip(*pixels))  # type: ignore[return-value]


def _max_channel_difference(cell: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    """Return the maximum absolute RGB channel difference from the background."""
    diff = ImageChops.difference(cell.convert("RGB"), Image.new("RGB", cell.size, bg))
    red, green, blue = diff.split()
    return ImageChops.lighter(ImageChops.lighter(red, green), blue)


def _soft_mask_from_diff(diff: Image.Image, tolerance: int) -> Image.Image:
    """Build a feathered alpha mask around the tolerance threshold."""
    low = max(0, tolerance - _DEFAULT_FEATHER)
    high = min(255, tolerance + _DEFAULT_FEATHER)
    if high <= low:
        return diff.point(lambda p: 255 if p > tolerance else 0)

    span = high - low
    lut = []
    for value in range(256):
        if value <= low:
            lut.append(0)
        elif value >= high:
            lut.append(255)
        else:
            lut.append(round((value - low) * 255 / span))
    return diff.point(lut)


def _content_masks(
    cell: Image.Image,
    bg: tuple[int, int, int],
    tolerance: int,
) -> tuple[Image.Image, Image.Image]:
    """Build binary trim and soft alpha masks from the same color distance."""
    diff = _max_channel_difference(cell, bg)
    trim_mask = diff.point(lambda p: 255 if p > tolerance else 0)
    alpha_mask = _soft_mask_from_diff(diff, tolerance)
    alpha_mask = alpha_mask.filter(ImageFilter.MinFilter(3))
    return trim_mask, alpha_mask


def slice_sheet(
    sheet_path: Path,
    rows: int,
    cols: int,
    output_dir: Path,
    *,
    names: Optional[list[str]] = None,
    prefix: Optional[str] = None,
    inset: float = 0.0,
    trim: bool = False,
    alpha: bool = False,
    bg: Optional[tuple[int, int, int]] = None,
    tolerance: int = 18,
) -> list[Path]:
    """Slice `sheet_path` into rows*cols element PNGs under `output_dir`.

    Returns the list of written file paths (row-major order). When `names` is
    given it must hold exactly rows*cols entries — a mismatch is an error so an
    automated run never silently drops cells. Each name must be a bare filename.
    """
    total_cells = rows * cols
    if names is not None and len(names) != total_cells:
        raise ValueError(
            f"--names has {len(names)} entries but the {rows}x{cols} grid has "
            f"{total_cells} cells; provide exactly one name per cell"
        )
    safe_names = [_safe_basename(n) for n in names] if names else None
    if alpha and safe_names:
        for name in safe_names:
            suffix = Path(name).suffix.lower()
            if suffix and suffix != ".png":
                raise ValueError(f"--alpha requires .png output names, got {name!r}")

    sheet = Image.open(sheet_path).convert("RGBA")
    sw, sh = sheet.size
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = sheet_path.stem
    name_prefix = _safe_basename(prefix) if prefix else f"{stem}_"
    written: list[Path] = []

    idx = 0
    for r in range(rows):
        for c in range(cols):
            # Integer cell box via per-index rounding to avoid drift.
            x0, x1 = round(c * sw / cols), round((c + 1) * sw / cols)
            y0, y1 = round(r * sh / rows), round((r + 1) * sh / rows)
            if inset > 0:
                dx = round((x1 - x0) * inset)
                dy = round((y1 - y0) * inset)
                x0, x1, y0, y1 = x0 + dx, x1 - dx, y0 + dy, y1 - dy
            cell = sheet.crop((x0, y0, x1, y1))

            trim_mask: Optional[Image.Image] = None
            alpha_mask: Optional[Image.Image] = None
            bbox = None
            if trim or alpha:
                cell_bg = bg if bg is not None else _sample_bg(cell)
                trim_mask, alpha_mask = _content_masks(cell, cell_bg, tolerance)
                bbox = trim_mask.getbbox()
                if bbox is None:
                    raise ValueError(f"cell ({r},{c}) is all background; no element was sliced")

            if trim and trim_mask is not None and alpha_mask is not None and bbox is not None:
                cell = cell.crop(bbox)
                alpha_mask = alpha_mask.crop(bbox)

            if alpha and alpha_mask is not None:
                cell.putalpha(alpha_mask)

            if safe_names:
                out_name = safe_names[idx]
                if not Path(out_name).suffix:
                    out_name += ".png"
            else:
                out_name = f"{name_prefix}{idx + 1:02d}.png"
            out_path = output_dir / out_name
            cell.save(out_path)
            written.append(out_path)
            _log(f"[OK] cell ({r},{c}) -> {out_path.name}  ({cell.width}x{cell.height})")
            idx += 1

    if len(written) != total_cells:
        raise ValueError(f"sliced {len(written)} elements but expected {total_cells}")
    return written


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Slice an AI illustration sheet into individual element images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3
  python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3 \\
      --names team,product,customer,growth,risk,vision --trim --alpha
""",
    )
    parser.add_argument("sheet", help="Path to the generated illustration sheet image")
    parser.add_argument("--grid", required=True, help="Grid as 'RxC' (rows x cols), e.g. 2x3")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output directory (default: the sheet's own directory)",
    )
    parser.add_argument(
        "--names", default=None,
        help="Comma-separated element names, row-major (extension optional). "
             "Must provide exactly rows*cols bare filenames.",
    )
    parser.add_argument(
        "--prefix", default=None,
        help="Filename prefix when --names is absent (default: '<sheet-stem>_')",
    )
    parser.add_argument(
        "--inset", type=float, default=0.0,
        help="Trim each cell inward by this fraction on every side (0-0.49) to drop gutters",
    )
    parser.add_argument(
        "--trim", action="store_true",
        help="Tight-crop each cell to its content bounding box",
    )
    parser.add_argument(
        "--alpha", action="store_true",
        help="Make the (flat) background transparent in each element",
    )
    parser.add_argument(
        "--bg", default=None,
        help="Background hex color for --trim/--alpha (default: auto-sample cell border)",
    )
    parser.add_argument(
        "--tolerance", type=int, default=18,
        help="Maximum per-channel color distance treated as background for --trim/--alpha "
             "(default: 18)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    sheet_path = Path(args.sheet)
    if not sheet_path.exists():
        print(f"[ERROR] Sheet not found: {sheet_path}", file=sys.stderr)
        return 1

    try:
        rows, cols = parse_grid(args.grid)
        bg = parse_hex(args.bg) if args.bg else None
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if not 0.0 <= args.inset < 0.5:
        print("[ERROR] --inset must be in [0, 0.5)", file=sys.stderr)
        return 1
    if not 0 <= args.tolerance <= 255:
        print("[ERROR] --tolerance must be in [0, 255]", file=sys.stderr)
        return 1

    names = [n.strip() for n in args.names.split(",") if n.strip()] if args.names else None
    output_dir = Path(args.output) if args.output else sheet_path.parent

    try:
        written = slice_sheet(
            sheet_path, rows, cols, output_dir,
            names=names, prefix=args.prefix, inset=args.inset,
            trim=args.trim, alpha=args.alpha, bg=bg, tolerance=args.tolerance,
        )
    except (OSError, ValueError) as exc:
        print(f"[ERROR] Slicing failed: {exc}", file=sys.stderr)
        return 1

    _log(f"\n[DONE] Wrote {len(written)} element(s) to {output_dir}")
    for p in written:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
