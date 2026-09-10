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
Both need a background color; it is auto-sampled from the dominant flat field
unless you pass --bg. Keying only works on a genuinely flat ground, so each
element is checked before writing. --strict-alpha turns an incomplete key into
an error with no output files. An explicit pure red, green, or blue key also
recovers clean RGB and partial alpha for antialiasing, shadows, and glows. See
references/image-generator.md section 4.3 for the sheet contract.

Usage:
    python3 scripts/slice_images.py <sheet_image> --grid RxC [options]

Examples:
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 2x3 \
        --names team,product,customer,growth,risk,vision --trim --alpha \
        --bg "#00FF00" --strict-alpha
    python3 scripts/slice_images.py projects/demo/images/illus_sheet.png --grid 1x4 \
        --prefix spot_ --bg "#F8F9FA" --alpha

Dependencies:
    Pillow
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Optional

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

from PIL import (
    Image,
    ImageChops,
    ImageFilter,
    ImageMath,
    ImageOps,
)

_GRID_RE = re.compile(r"^\s*(\d+)\s*[xX×]\s*(\d+)\s*$")
_BG_BUCKET_SIZE = 16
_BG_SAMPLE_BORDER = 2
_BG_SAMPLE_MAX_SIDE = 256
_DEFAULT_FEATHER = 4
_BOUNDARY_OPAQUE_ALPHA = 32
_SHEET_DIAGNOSTIC_BORDER_RATIO = 0.01
_SHEET_DIAGNOSTIC_BUCKET_SIZE = 4
# Isolated pixels this close to the key are compression or ringing artifacts a
# larger tolerance absorbs; farther pixels are content crossing the gutter.
_KEY_DRIFT_MAX_TOLERANCE = 48
_KEY_DRIFT_MARGIN = 4
# A key-dominant pixel whose strongest non-key channel reaches this fraction of
# the key channel is opaque foreground of a key-like hue (malachite green on a
# green key), not a semi-transparent blend with the key; color-to-alpha recovery
# and despill skip it so the element keeps its own color.
_KEY_PURITY_OPAQUE_RATIO = 0.6
# At most this many trim pixels on a touched edge count as isolated drift.
_EDGE_DRIFT_MAX_PIXELS = 8
# Strict-alpha haze gate: when this share of an element's trimmed box sits in
# the semi-transparent alpha band, the key field itself was recovered as soft
# alpha (the sheet ground is not the stated key), not an element edge.
_HAZE_ALPHA_LOW = 20
_HAZE_ALPHA_HIGH = 150
_HAZE_MAX_SHARE = 0.15
# Corner sample inset (px) and minimum cell fill for the backing-panel notice.
_PANEL_CORNER_INSET = 2
_PANEL_MIN_FILL = 0.75


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


def parse_inset(spec: str) -> tuple[float, float]:
    """Parse `--inset` as one fraction or `H,V`; both must lie in [0, 0.5)."""
    parts = [part.strip() for part in str(spec).split(",")]
    if len(parts) not in (1, 2) or not all(parts):
        raise ValueError("--inset must be one fraction or H,V")
    try:
        values = [float(part) for part in parts]
    except ValueError as exc:
        raise ValueError("--inset must be one fraction or H,V") from exc
    if not all(0.0 <= value < 0.5 for value in values):
        raise ValueError("--inset must be in [0, 0.5)")
    return (values[0], values[-1])


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


def _sample_border_bg(rgb: Image.Image) -> tuple[int, int, int]:
    """Estimate a background candidate from a cell's border ring."""
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


def _sample_pixels(rgb: Image.Image) -> list[tuple[int, int, int]]:
    """Return a bounded RGB sample for background-candidate scoring."""
    sample = rgb.copy()
    sample.thumbnail(
        (_BG_SAMPLE_MAX_SIDE, _BG_SAMPLE_MAX_SIDE),
        Image.Resampling.NEAREST,
    )
    raw = sample.tobytes()
    return list(zip(raw[0::3], raw[1::3], raw[2::3]))


def _dominant_bg_candidate(
    pixels: list[tuple[int, int, int]],
) -> tuple[int, int, int]:
    """Estimate the dominant flat field from quantized sampled pixels."""
    buckets = Counter(
        tuple(channel // _BG_BUCKET_SIZE for channel in pixel)
        for pixel in pixels
    )
    dominant_bucket = buckets.most_common(1)[0][0]
    members = [
        pixel
        for pixel in pixels
        if tuple(channel // _BG_BUCKET_SIZE for channel in pixel) == dominant_bucket
    ]
    return tuple(round(median(channel)) for channel in zip(*members))  # type: ignore[return-value]


def _background_coverage(
    pixels: list[tuple[int, int, int]],
    candidate: tuple[int, int, int],
    tolerance: int,
) -> int:
    """Count sampled pixels close enough to a background candidate."""
    return sum(
        max(abs(pixel[index] - candidate[index]) for index in range(3)) <= tolerance
        for pixel in pixels
    )


def _sample_bg(cell: Image.Image, tolerance: int) -> tuple[int, int, int]:
    """Choose the background candidate that covers most of the cell."""
    rgb = cell.convert("RGB")
    pixels = _sample_pixels(rgb)
    candidates = (
        _sample_border_bg(rgb),
        _dominant_bg_candidate(pixels),
    )
    return max(
        candidates,
        key=lambda candidate: _background_coverage(pixels, candidate, tolerance),
    )


def _sample_sheet_border(
    sheet: Image.Image,
) -> tuple[tuple[int, int, int], int]:
    """Return the dominant RGB cluster, its spread, and the ring's farthest pixel.

    The spread describes the key field itself; the outlier distance is what a
    ``--tolerance`` must reach so that isolated ringing or compression pixels
    in the gutter still key out.
    """
    rgb = sheet.convert("RGB")
    width, height = rgb.size
    border_x = max(1, round(width * _SHEET_DIAGNOSTIC_BORDER_RATIO))
    border_y = max(1, round(height * _SHEET_DIAGNOSTIC_BORDER_RATIO))
    px = rgb.load()
    pixels: list[tuple[int, int, int]] = []

    for y in range(border_y):
        pixels.extend(px[x, y] for x in range(width))
    for y in range(max(border_y, height - border_y), height):
        pixels.extend(px[x, y] for x in range(width))
    for y in range(border_y, max(border_y, height - border_y)):
        pixels.extend(px[x, y] for x in range(border_x))
        pixels.extend(
            px[x, y]
            for x in range(max(border_x, width - border_x), width)
        )

    buckets = Counter(
        tuple(channel // _SHEET_DIAGNOSTIC_BUCKET_SIZE for channel in pixel)
        for pixel in pixels
    )
    dominant_bucket = buckets.most_common(1)[0][0]
    dominant_pixels = [
        pixel
        for pixel in pixels
        if tuple(
            channel // _SHEET_DIAGNOSTIC_BUCKET_SIZE
            for channel in pixel
        ) == dominant_bucket
    ]
    dominant = tuple(
        round(median(channel))
        for channel in zip(*dominant_pixels)
    )
    channel_spreads = [
        max(pixel[index] for pixel in dominant_pixels)
        - min(pixel[index] for pixel in dominant_pixels)
        for index in range(3)
    ]
    outlier = max(
        max(abs(pixel[index] - dominant[index]) for index in range(3))
        for pixel in pixels
    )
    return dominant, max(channel_spreads), outlier  # type: ignore[return-value]


def _max_channel_difference(cell: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    """Return the maximum absolute RGB channel difference from the background."""
    diff = ImageChops.difference(cell.convert("RGB"), Image.new("RGB", cell.size, bg))
    red, green, blue = diff.split()
    return ImageChops.lighter(ImageChops.lighter(red, green), blue)


def _pure_chroma_channel(bg: tuple[int, int, int]) -> Optional[int]:
    """Return the active channel for an exact pure RGB key, if any."""
    if bg.count(255) != 1 or bg.count(0) != 2:
        return None
    return bg.index(255)


def _nearest_pure_key(
    color: tuple[int, int, int],
) -> Optional[tuple[tuple[int, int, int], int]]:
    """Return the pure RGB key a drifted gutter color came from, with its distance."""
    best: Optional[tuple[tuple[int, int, int], int]] = None
    for index in range(3):
        pure = tuple(255 if i == index else 0 for i in range(3))
        distance = max(abs(color[i] - pure[i]) for i in range(3))
        if distance <= _KEY_DRIFT_MAX_TOLERANCE and (best is None or distance < best[1]):
            best = (pure, distance)  # type: ignore[assignment]
    return best


def _channel_alpha(channel: Image.Image, bg_value: int) -> Image.Image:
    """Return the minimum alpha that can explain one channel over a key."""
    lut = []
    for value in range(256):
        if value > bg_value:
            denominator = 255 - bg_value
            alpha = 255 if denominator == 0 else round(
                (value - bg_value) * 255 / denominator
            )
        elif value < bg_value:
            alpha = 255 if bg_value == 0 else round(
                (bg_value - value) * 255 / bg_value
            )
        else:
            alpha = 0
        lut.append(alpha)
    return channel.point(lut)


def _chroma_alpha(rgb: Image.Image, bg: tuple[int, int, int]) -> Image.Image:
    """Recover foreground opacity for a pure single-channel chroma key.

    A non-key-dominant pixel is treated as opaque foreground. A key-dominant
    pixel uses color-to-alpha recovery, which preserves soft shadows, glows,
    and antialiased edges without making an ordinary solid foreground color
    unnecessarily translucent.
    """
    channels = rgb.split()
    channel_alphas = [
        _channel_alpha(channel, bg_value)
        for channel, bg_value in zip(channels, bg)
    ]
    raw_alpha = ImageChops.lighter(
        ImageChops.lighter(channel_alphas[0], channel_alphas[1]),
        channel_alphas[2],
    )
    key_index = _pure_chroma_channel(bg)
    if key_index is None:
        return raw_alpha

    other_channels = [
        channel for index, channel in enumerate(channels) if index != key_index
    ]
    key_blend = _key_blend_mask(
        channels[key_index],
        ImageChops.lighter(other_channels[0], other_channels[1]),
    )
    opaque = Image.new("L", rgb.size, 255)
    return Image.composite(raw_alpha, opaque, key_blend)


def _key_blend_mask(key_channel: Image.Image, other_max: Image.Image) -> Image.Image:
    """Mask the pixels that read as a blend of foreground with a pure key.

    A pixel qualifies only when the key channel dominates and the strongest
    non-key channel stays below `_KEY_PURITY_OPAQUE_RATIO` of it. An opaque
    foreground color that merely shares the key's hue (a malachite green under a
    green key) keeps a substantial non-key channel and is left opaque, while
    antialiased edges, soft shadows, and glows composited over the key fall
    below the ratio and still receive color-to-alpha recovery.
    """
    ratio_num = round(_KEY_PURITY_OPAQUE_RATIO * 10)
    if hasattr(ImageMath, "lambda_eval"):
        blend = ImageMath.lambda_eval(
            lambda op: op["convert"](
                (op["key"] > op["other"])
                & (op["other"] * 10 < op["key"] * ratio_num),
                "L",
            ),
            key=key_channel,
            other=other_max,
        )
    else:
        blend = ImageMath.eval(  # type: ignore[attr-defined]
            "convert((key > other) & (other * 10 < key * ratio), 'L')",
            key=key_channel,
            other=other_max,
            ratio=ratio_num,
        )
    return blend.point(lambda value: 255 if value else 0)


def _decontaminate_channel(
    channel: Image.Image,
    alpha: Image.Image,
    bg_value: int,
) -> Image.Image:
    """Remove a composited key channel while supporting Pillow 9 through 12."""
    if hasattr(ImageMath, "lambda_eval"):
        return ImageMath.lambda_eval(
            lambda op: op["convert"](
                bg_value
                + (op["channel"] - bg_value)
                * 255
                / op["max"](op["alpha"], 1),
                "L",
            ),
            channel=channel,
            alpha=alpha,
        )
    return ImageMath.eval(  # type: ignore[attr-defined]
        "convert(bg + (channel - bg) * 255 / max(alpha, 1), 'L')",
        channel=channel,
        alpha=alpha,
        bg=bg_value,
    )


def _decontaminate_rgb(
    rgb: Image.Image,
    alpha: Image.Image,
    bg: tuple[int, int, int],
) -> Image.Image:
    """Recover foreground RGB values from a composited pure chroma key."""
    return Image.merge(
        "RGB",
        tuple(
            _decontaminate_channel(channel, alpha, bg_value)
            for channel, bg_value in zip(rgb.split(), bg)
        ),
    )


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
) -> tuple[Image.Image, Image.Image, Optional[Image.Image], Image.Image]:
    """Build trim/alpha masks, optional chroma-decontaminated RGB, and the key diff."""
    rgb = cell.convert("RGB")
    diff = _max_channel_difference(rgb, bg)
    trim_mask = diff.point(lambda p: 255 if p > tolerance else 0)
    tolerance_gate = _soft_mask_from_diff(diff, tolerance)
    if _pure_chroma_channel(bg) is not None:
        chroma_alpha = _chroma_alpha(rgb, bg)
        alpha_mask = ImageChops.multiply(chroma_alpha, tolerance_gate)
        keyed_rgb = _decontaminate_rgb(rgb, chroma_alpha, bg)
        return trim_mask, alpha_mask, keyed_rgb, diff

    alpha_mask = tolerance_gate.filter(ImageFilter.MinFilter(3))
    return trim_mask, alpha_mask, None, diff


def _keying_findings(
    label: str,
    cell_size: tuple[int, int],
    bbox: tuple[int, int, int, int],
    alpha_mask: Optional[Image.Image],
    cell_bg: tuple[int, int, int],
    *,
    trim: bool,
    alpha: bool,
    trim_mask: Optional[Image.Image] = None,
    diff: Optional[Image.Image] = None,
    notices: Optional[list[str]] = None,
) -> list[str]:
    """Report objective signs that the flat-background key did not take.

    Two deterministic symptoms: a cut element whose cell boundary is still
    opaque, and content that reaches any cell edge. Both violate the clear-key
    gutter required by the sheet contract, usually because the ground is not
    flat or an element/effect crossed its cell boundary.
    """
    findings: list[str] = []
    hex_bg = "#{:02X}{:02X}{:02X}".format(*cell_bg)

    if alpha and trim and alpha_mask is not None and notices is not None:
        notice = _backing_panel_notice(label, alpha_mask, bbox, cell_size)
        if notice:
            notices.append(notice)

    if alpha and alpha_mask is not None:
        px = alpha_mask.load()
        width, height = alpha_mask.size
        border = max(1, min(_BG_SAMPLE_BORDER, width, height))
        boundary = []
        for y in range(border):
            boundary.extend(px[x, y] for x in range(width))
        for y in range(max(border, height - border), height):
            boundary.extend(px[x, y] for x in range(width))
        for y in range(border, max(border, height - border)):
            boundary.extend(px[x, y] for x in range(border))
            boundary.extend(
                px[x, y] for x in range(max(border, width - border), width)
            )
        opaque = sum(
            1 for value in boundary if value > _BOUNDARY_OPAQUE_ALPHA
        )
        if opaque:
            findings.append(
                f"{label}: {opaque}/{len(boundary)} boundary pixels stayed opaque "
                f"after --alpha "
                f"(key background {hex_bg})"
            )

    if trim:
        cell_width, cell_height = cell_size
        touched_edges = []
        if bbox[0] <= 0:
            touched_edges.append("left")
        if bbox[1] <= 0:
            touched_edges.append("top")
        if bbox[2] >= cell_width:
            touched_edges.append("right")
        if bbox[3] >= cell_height:
            touched_edges.append("bottom")
        if touched_edges:
            drift = _edge_drift(trim_mask, diff, touched_edges)
            if drift is not None:
                count, distance, isolated = drift
                if isolated:
                    findings.append(
                        f"{label}: {count} isolated pixel(s) on the "
                        f"{'/'.join(touched_edges)} cell edge(s) exceed the key "
                        f"tolerance (farthest {distance} from key {hex_bg}); this is "
                        f"key drift, not content — rerun with --tolerance "
                        f"{distance + _KEY_DRIFT_MARGIN} or higher"
                    )
                else:
                    findings.append(
                        f"{label}: {count} pixel(s) on the "
                        f"{'/'.join(touched_edges)} cell edge(s) exceed the key "
                        f"tolerance but all stay within {distance} of key {hex_bg}; "
                        f"this is key noise (JPEG compression or a slightly off "
                        f"key), not content — rerun with --tolerance "
                        f"{distance + _KEY_DRIFT_MARGIN} or higher"
                    )
            else:
                findings.append(
                    f"{label}: content reaches the {'/'.join(touched_edges)} "
                    f"cell edge(s) (key background {hex_bg})"
                )

    return findings


def _haze_finding(
    label: str,
    alpha_mask: Image.Image,
    bbox: tuple[int, int, int, int],
    bg: tuple[int, int, int],
) -> Optional[str]:
    """Report an element box that is mostly semi-transparent haze.

    Soft-alpha recovery assumes the key field lies at the stated key; when the
    real ground sits farther than the tolerance, the whole field comes back as
    faint half-foreground that reads as a glowing rectangle on a dark slide.
    `--strict-alpha` only inspects the outer gutter, so this gate looks at the
    trimmed box itself.
    """
    box = alpha_mask.crop(bbox)
    total = box.width * box.height
    if total == 0:
        return None
    histogram = box.histogram()
    hazy = sum(histogram[_HAZE_ALPHA_LOW:_HAZE_ALPHA_HIGH + 1])
    share = hazy / total
    if share <= _HAZE_MAX_SHARE:
        return None
    hex_bg = "#{:02X}{:02X}{:02X}".format(*bg)
    return (
        f"{label}: {share:.0%} of the trimmed element box is semi-transparent "
        f"(alpha {_HAZE_ALPHA_LOW}-{_HAZE_ALPHA_HIGH}): the key field itself "
        f"was recovered as soft alpha, so the sheet ground is not {hex_bg}; "
        "rerun with --bg set to the measured ground colour (see the sheet "
        "border line below) instead of the nearest pure key"
    )


def _backing_panel_notice(
    label: str,
    alpha_mask: Image.Image,
    bbox: tuple[int, int, int, int],
    cell_size: tuple[int, int],
) -> Optional[str]:
    """Flag a trimmed element whose corners are opaque: a painted backing panel.

    A cut-out silhouette almost never fills all four corners of its own
    bounding box; a rectangle behind it does. The key cannot see the panel
    (the gutters are clean), so this is advisory, never a strict failure.
    """
    left, top, right, bottom = bbox
    if right - left < 2 * _PANEL_CORNER_INSET + 1 or bottom - top < 2 * _PANEL_CORNER_INSET + 1:
        return None
    cell_width, cell_height = cell_size
    fill_w = (right - left) / cell_width if cell_width else 0.0
    fill_h = (bottom - top) / cell_height if cell_height else 0.0
    if min(fill_w, fill_h) < _PANEL_MIN_FILL:
        return None
    px = alpha_mask.load()
    corners = (
        (left + _PANEL_CORNER_INSET, top + _PANEL_CORNER_INSET),
        (right - 1 - _PANEL_CORNER_INSET, top + _PANEL_CORNER_INSET),
        (left + _PANEL_CORNER_INSET, bottom - 1 - _PANEL_CORNER_INSET),
        (right - 1 - _PANEL_CORNER_INSET, bottom - 1 - _PANEL_CORNER_INSET),
    )
    opaque = sum(1 for x, y in corners if px[x, y] > _BOUNDARY_OPAQUE_ALPHA)
    if opaque < 3:
        return None
    return (
        f"{label}: the trimmed element fills {fill_w:.0%} x {fill_h:.0%} of its "
        f"cell and is opaque in {opaque} of 4 corners; it "
        "may sit on a painted backing panel the key could not remove — look at "
        "the slice, and regenerate with the element alone on the key if so"
    )


def _edge_drift(
    trim_mask: Optional[Image.Image],
    diff: Optional[Image.Image],
    touched_edges: list[str],
) -> Optional[tuple[int, int, bool]]:
    """Return (pixel count, max key distance, isolated) when every pixel on
    the touched edges stays near the key, or None when real content reaches
    an edge. ``isolated`` is True for a handful of stray pixels; False means
    the whole edge is near-key noise (JPEG ringing, a slightly off key), which
    is still keying drift rather than content."""
    if trim_mask is None or diff is None:
        return None
    width, height = trim_mask.size
    mask_px = trim_mask.load()
    diff_px = diff.load()
    coords = set()
    if "left" in touched_edges:
        coords.update((0, y) for y in range(height))
    if "right" in touched_edges:
        coords.update((width - 1, y) for y in range(height))
    if "top" in touched_edges:
        coords.update((x, 0) for x in range(width))
    if "bottom" in touched_edges:
        coords.update((x, height - 1) for x in range(width))
    hits = [diff_px[x, y] for x, y in coords if mask_px[x, y]]
    if not hits:
        return None
    distance = max(hits)
    if distance > _KEY_DRIFT_MAX_TOLERANCE:
        return None
    return len(hits), distance, len(hits) <= _EDGE_DRIFT_MAX_PIXELS


def _log_keying_findings(
    findings: list[str],
    *,
    sheet_border: tuple[tuple[int, int, int], int, int] | None = None,
    tolerance: int,
    notices: list[str] | None = None,
) -> None:
    """Report incomplete flat-background keying."""
    _log("\n[WARN] Alpha extraction is incomplete — the key field or cell")
    _log("       isolation failed:")
    for finding in findings:
        _log(f"       - {finding}")
    # A field recovered as haze is an off-key ground, not a panel: keep the
    # measured-border rerun advice for it instead of the panel verdict.
    hazy = any("semi-transparent" in finding for finding in findings)
    panel_notices = [] if hazy else [n for n in (notices or []) if "backing panel" in n]
    for notice in panel_notices:
        _log(f"       - {notice}")
    if panel_notices:
        _log("       Cells painted as panels or cards keep their own ground "
             "inside the key gutters: no --bg/--tolerance rerun on the outer "
             "key can remove them. Regenerate with each element alone on the "
             "key, or key each cell on its measured inner ground.")
        return
    _log("       Fix: regenerate with one genuinely flat ground and keep every "
         "element/effect")
    _log("       inside its cell with a clear key-only gutter, or rerun with an "
         "explicit")
    _log("       --bg <hex> and a larger --tolerance; use --inset when a drawn "
         "outer gutter is isolated from every element, or when the model drew "
         "grid lines between cells (--inset 0.02, or H,V for wide cells).")
    if sheet_border is not None:
        dominant, drift, outlier = sheet_border
        hex_bg = "#{:02X}{:02X}{:02X}".format(*dominant)
        _log(
            "       Measured outer 1% border/gutter: "
            f"dominant {hex_bg}; key spread {drift}; farthest pixel {outlier} "
            "from the key."
        )
        if outlier > _KEY_DRIFT_MAX_TOLERANCE:
            _log(
                "       The gutter holds pixels far from the key: content or an "
                "effect crosses it. Regenerate with a clear key-only gutter; a "
                "larger --tolerance would eat into the elements."
            )
        elif (
            outlier <= tolerance
            and any("content reaches the" in finding for finding in findings)
            and not any("boundary pixels stayed opaque" in finding for finding in findings)
        ):
            # The key itself passed at this tolerance; only element tips
            # crossed a gutter. When the farthest gutter pixel exceeds the
            # tolerance the branch below still offers the rerun instead.
            _log(
                "       Content crosses a cell edge: no --bg/--tolerance rerun "
                "can separate it. Regenerate with a wider key-only gutter "
                "(each element about 65% of its cell, at least 10% key on "
                "every side, tips and effects included)."
            )
        else:
            pure = _nearest_pure_key(dominant)
            if pure is not None:
                # A pure key enables despill and soft-alpha recovery; keep it
                # and widen the tolerance by the measured drift instead.
                pure_rgb, pure_distance = pure
                hex_bg = "#{:02X}{:02X}{:02X}".format(*pure_rgb)
                drift += pure_distance
                outlier += pure_distance
            suggested_tolerance = max(
                tolerance, drift, outlier + _KEY_DRIFT_MARGIN
            )
            _log(
                "       Suggested rerun: "
                f"--bg {hex_bg} --tolerance {suggested_tolerance}"
            )


def slice_sheet(
    sheet_path: Path,
    rows: int,
    cols: int,
    output_dir: Path,
    *,
    names: Optional[list[str]] = None,
    prefix: Optional[str] = None,
    inset: float | tuple[float, float] = 0.0,
    trim: bool = False,
    alpha: bool = False,
    strict_alpha: bool = False,
    bg: Optional[tuple[int, int, int]] = None,
    tolerance: int = 18,
) -> list[Path]:
    """Slice `sheet_path` into rows*cols element PNGs under `output_dir`.

    Returns the list of written file paths (row-major order). When `names` is
    given it must hold exactly rows*cols entries — a mismatch is an error so an
    automated run never silently drops cells. Each name must be a bare filename.
    """
    total_cells = rows * cols
    inset_x, inset_y = inset if isinstance(inset, tuple) else (inset, inset)
    if strict_alpha and not alpha:
        raise ValueError("strict_alpha requires alpha=True")
    if names is not None and len(names) != total_cells:
        raise ValueError(
            f"--names has {len(names)} entries but the {rows}x{cols} grid has "
            f"{total_cells} cells; provide exactly one name per cell"
        )
    safe_names = [_safe_basename(n) for n in names] if names else None
    if safe_names:
        seen_outputs: set[str] = set()
        for name in safe_names:
            output_name = name if Path(name).suffix else f"{name}.png"
            normalized_output = output_name.casefold()
            if normalized_output in seen_outputs:
                raise ValueError(
                    f"--names repeats output filename {output_name!r} "
                    "(case-insensitive)"
                )
            seen_outputs.add(normalized_output)
    if alpha and safe_names:
        for name in safe_names:
            suffix = Path(name).suffix.lower()
            if suffix and suffix != ".png":
                raise ValueError(f"--alpha requires .png output names, got {name!r}")

    with Image.open(sheet_path) as source:
        sheet = ImageOps.exif_transpose(source).convert("RGBA")
    sw, sh = sheet.size
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = sheet_path.stem
    name_prefix = _safe_basename(prefix) if prefix else f"{stem}_"
    prepared: list[tuple[int, int, Image.Image, Path]] = []
    written: list[Path] = []
    findings: list[str] = []
    notices: list[str] = []

    idx = 0
    for r in range(rows):
        for c in range(cols):
            # Integer cell box via per-index rounding to avoid drift.
            x0, x1 = round(c * sw / cols), round((c + 1) * sw / cols)
            y0, y1 = round(r * sh / rows), round((r + 1) * sh / rows)
            if inset_x > 0 or inset_y > 0:
                dx = round((x1 - x0) * inset_x)
                dy = round((y1 - y0) * inset_y)
                x0, x1, y0, y1 = x0 + dx, x1 - dx, y0 + dy, y1 - dy
            cell = sheet.crop((x0, y0, x1, y1))

            trim_mask: Optional[Image.Image] = None
            alpha_mask: Optional[Image.Image] = None
            keyed_rgb: Optional[Image.Image] = None
            bbox = None
            if trim or alpha:
                cell_bg = bg if bg is not None else _sample_bg(cell, tolerance)
                trim_mask, alpha_mask, keyed_rgb, diff = _content_masks(
                    cell, cell_bg, tolerance
                )
                bbox = trim_mask.getbbox()
                if bbox is None:
                    raise ValueError(f"cell ({r},{c}) is all background; no element was sliced")
                findings.extend(_keying_findings(
                    f"cell ({r},{c})", cell.size, bbox, alpha_mask, cell_bg,
                    trim=trim, alpha=alpha, trim_mask=trim_mask, diff=diff,
                    notices=notices,
                ))
                if strict_alpha:
                    haze = _haze_finding(f"cell ({r},{c})", alpha_mask, bbox, cell_bg)
                    if haze:
                        findings.append(haze)

            if trim and trim_mask is not None and alpha_mask is not None and bbox is not None:
                cell = cell.crop(bbox)
                alpha_mask = alpha_mask.crop(bbox)
                if keyed_rgb is not None:
                    keyed_rgb = keyed_rgb.crop(bbox)

            if alpha and alpha_mask is not None:
                if keyed_rgb is not None:
                    cell = keyed_rgb.convert("RGBA")
                cell.putalpha(alpha_mask)

            if safe_names:
                out_name = safe_names[idx]
                if not Path(out_name).suffix:
                    out_name += ".png"
            else:
                out_name = f"{name_prefix}{idx + 1:02d}.png"
            out_path = output_dir / out_name
            prepared.append((r, c, cell, out_path))
            idx += 1

    if findings:
        sheet_border = _sample_sheet_border(sheet) if strict_alpha else None
        _log_keying_findings(
            findings,
            sheet_border=sheet_border,
            tolerance=tolerance,
            notices=notices,
        )
        if strict_alpha:
            raise ValueError(
                "strict alpha validation found incomplete background keying; "
                "no output files were written"
            )

    for notice in notices:
        _log(f"[WARN] {notice}")

    for r, c, cell, out_path in prepared:
        cell.save(out_path)
        written.append(out_path)
        _log(f"[OK] cell ({r},{c}) -> {out_path.name}  ({cell.width}x{cell.height})")

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
      --names team,product,customer,growth,risk,vision --trim --alpha \\
      --bg "#00FF00" --strict-alpha
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
        "--inset", type=str, default="0",
        help=(
            "Trim each cell inward by this fraction (0-0.49) to drop gutters: "
            "one value for every side, or H,V (e.g. 0.01,0.03) when wide cells "
            "only need the horizontal grid line trimmed"
        ),
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
        "--strict-alpha", action="store_true",
        help="Fail without writing outputs when --alpha validation finds incomplete keying",
    )
    parser.add_argument(
        "--bg", default=None,
        help="Background hex color for --trim/--alpha; an exact pure red/green/blue "
             "key enables despill and soft-alpha recovery, skipping opaque "
             "foreground pixels of a key-like hue (default: auto-sample)",
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

    try:
        inset = parse_inset(args.inset)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    if not 0 <= args.tolerance <= 255:
        print("[ERROR] --tolerance must be in [0, 255]", file=sys.stderr)
        return 1
    if args.strict_alpha and not args.alpha:
        print("[ERROR] --strict-alpha requires --alpha", file=sys.stderr)
        return 1

    names = [n.strip() for n in args.names.split(",") if n.strip()] if args.names else None
    output_dir = Path(args.output) if args.output else sheet_path.parent

    try:
        written = slice_sheet(
            sheet_path, rows, cols, output_dir,
            names=names, prefix=args.prefix, inset=inset,
            trim=args.trim, alpha=args.alpha, strict_alpha=args.strict_alpha,
            bg=bg, tolerance=args.tolerance,
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
