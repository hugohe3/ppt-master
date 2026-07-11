"""PPTX -> SVG semantic converter (reverse of svg_to_pptx).

Reads OOXML (DrawingML) directly from a .pptx zip archive and emits SVG with
shape-level fidelity: <p:sp prst="rect"> -> <rect>, <p:txBody> -> <text>, etc.

Public entry: convert_pptx_to_svg().
"""

from __future__ import annotations

__all__ = ["convert_pptx_to_svg"]


def __getattr__(name: str):
    """Load the public converter lazily so shared submodules stay lightweight."""
    if name != "convert_pptx_to_svg":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .converter import convert_pptx_to_svg

    return convert_pptx_to_svg
