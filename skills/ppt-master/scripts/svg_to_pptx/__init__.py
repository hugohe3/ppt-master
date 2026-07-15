"""svg_to_pptx — SVG to PPTX conversion package.

Public API:
    - main(): CLI entry point
    - convert_svg_to_slide_shapes(): SVG -> DrawingML slide XML
    - create_pptx_with_native_svg(): Build PPTX from SVG files
"""

from __future__ import annotations

from typing import Any

__all__ = [
    'main',
    'convert_svg_to_slide_shapes',
    'create_pptx_with_native_svg',
]


def __getattr__(name: str) -> Any:
    """Load public entry points lazily to keep low-level imports acyclic."""
    if name == 'main':
        from .pptx_package.cli import main

        value = main
    elif name == 'convert_svg_to_slide_shapes':
        from .drawingml.converter import convert_svg_to_slide_shapes

        value = convert_svg_to_slide_shapes
    elif name == 'create_pptx_with_native_svg':
        from .pptx_package.builder import create_pptx_with_native_svg

        value = create_pptx_with_native_svg
    else:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value
