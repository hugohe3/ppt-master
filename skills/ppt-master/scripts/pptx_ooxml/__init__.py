"""Reusable OOXML readers and source-preserving package primitives."""

from __future__ import annotations

from .analyzer import analyze_pptx
from .chart_read import empty_chart_data, read_chart_data
from .clone import clone_presentation_slides, deep_clone_slide_private_parts
from .diagram_read import read_smartart_diagrams, smartart_to_markdown
from .package import prune_unreferenced_directory_parts

__all__ = [
    "analyze_pptx",
    "clone_presentation_slides",
    "deep_clone_slide_private_parts",
    "empty_chart_data",
    "prune_unreferenced_directory_parts",
    "read_chart_data",
    "read_smartart_diagrams",
    "smartart_to_markdown",
]
