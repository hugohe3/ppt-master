"""Slide dimensions, format detection, EMU conversion, and constants."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from ..canvas_contract import (
    CanvasContractError,
    ProjectViewBox,
    parse_project_viewbox,
    read_project_viewbox,
    require_consistent_project_viewboxes,
)

# Import project utility modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from project_utils import get_project_info
    from config import CANVAS_FORMATS
except ImportError:
    CANVAS_FORMATS = {
        'ppt169': {'name': 'PPT 16:9', 'dimensions': '1280×720', 'viewbox': '0 0 1280 720'},
    }

    def get_project_info(path: str) -> dict:
        return {'format': 'unknown', 'name': Path(path).name}

# EMU conversion constants
EMU_PER_INCH = 914400
EMU_PER_PIXEL = EMU_PER_INCH / 96

# XML namespaces
NAMESPACES = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'asvg': 'http://schemas.microsoft.com/office/drawing/2016/SVG/main',
}

# Register namespaces for ElementTree output
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


def get_slide_dimensions(
    canvas_format: str,
    custom_pixels: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Get slide dimensions in EMU units.

    Args:
        canvas_format: Canvas format key (e.g. 'ppt169').
        custom_pixels: Optional custom pixel dimensions override.

    Returns:
        (width_emu, height_emu) tuple.
    """
    if custom_pixels:
        width_px, height_px = custom_pixels
    else:
        if canvas_format not in CANVAS_FORMATS:
            canvas_format = 'ppt169'

        dimensions = CANVAS_FORMATS[canvas_format]['dimensions']
        match = re.match(r'(\d+)[×x](\d+)', dimensions)
        if match:
            width_px = int(match.group(1))
            height_px = int(match.group(2))
        else:
            width_px, height_px = 1280, 720

    return int(width_px * EMU_PER_PIXEL), int(height_px * EMU_PER_PIXEL)


def get_pixel_dimensions(
    canvas_format: str,
    custom_pixels: tuple[int, int] | None = None,
) -> tuple[int, int]:
    """Get canvas pixel dimensions.

    Args:
        canvas_format: Canvas format key.
        custom_pixels: Optional custom pixel dimensions override.

    Returns:
        (width_px, height_px) tuple.
    """
    if custom_pixels:
        return custom_pixels

    if canvas_format not in CANVAS_FORMATS:
        canvas_format = 'ppt169'

    dimensions = CANVAS_FORMATS[canvas_format]['dimensions']
    match = re.match(r'(\d+)[×x](\d+)', dimensions)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 1280, 720


def get_viewbox_dimensions(svg_path: Path) -> tuple[float, float]:
    """Extract pixel dimensions from SVG viewBox.

    Args:
        svg_path: Path to the SVG file.

    Returns:
        (width, height) in SVG pixels.

    Raises:
        CanvasContractError: The root canvas is missing or invalid.
    """
    return read_project_viewbox(svg_path).pixel_dimensions


def detect_format_from_svg(svg_path: Path) -> str | None:
    """Detect canvas format from an SVG file's viewBox.

    Args:
        svg_path: Path to the SVG file.

    Returns:
        Canvas format key (e.g. 'ppt169'), or None if not detected.
    """
    viewbox = read_project_viewbox(svg_path)
    for fmt_key, fmt_info in CANVAS_FORMATS.items():
        expected = parse_project_viewbox(
            fmt_info['viewbox'],
            context=f"registered canvas {fmt_key!r}",
        )
        if viewbox == expected:
            return fmt_key
    return None


def resolve_svg_canvas(
    svg_files: list[Path],
    *,
    canvas_format: str | None = None,
    expected_viewbox: str | None = None,
) -> tuple[ProjectViewBox, str | None]:
    """Resolve one fail-closed canvas for every public/internal SVG."""
    format_viewbox: str | None = None
    if canvas_format is not None:
        if canvas_format not in CANVAS_FORMATS:
            raise CanvasContractError(f"Unsupported canvas format: {canvas_format}")
        format_viewbox = CANVAS_FORMATS[canvas_format]['viewbox']

    if expected_viewbox is not None and format_viewbox is not None:
        locked = parse_project_viewbox(
            expected_viewbox,
            context="locked canvas viewBox",
        )
        selected = parse_project_viewbox(
            format_viewbox,
            context=f"canvas format {canvas_format!r}",
        )
        if locked != selected:
            raise CanvasContractError(
                f"canvas format {canvas_format!r} ({selected.canonical}) conflicts "
                f"with the locked canvas ({locked.canonical})"
            )

    required = expected_viewbox if expected_viewbox is not None else format_viewbox
    if expected_viewbox is not None:
        expected_label = "the locked canvas"
    elif canvas_format is not None:
        expected_label = f"canvas format {canvas_format!r}"
    else:
        expected_label = "the first SVG canvas"
    viewbox = require_consistent_project_viewboxes(
        svg_files,
        expected_viewbox=required,
        expected_label=expected_label,
    )
    detected_format = canvas_format
    if detected_format is None:
        for fmt_key, fmt_info in CANVAS_FORMATS.items():
            registered = parse_project_viewbox(
                fmt_info['viewbox'],
                context=f"registered canvas {fmt_key!r}",
            )
            if viewbox == registered:
                detected_format = fmt_key
                break
    return viewbox, detected_format
