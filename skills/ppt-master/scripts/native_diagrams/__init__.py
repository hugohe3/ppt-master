"""Native-diagram library: lift editable DrawingML diagrams between decks.

Unlike the SVG pipeline (``pptx_to_svg`` -> ``svg_to_pptx``), this package never
re-renders. It lifts a slide's ``<p:sp>`` / ``<p:grpSp>`` XML verbatim and only
flattens theme dependencies (``schemeClr`` -> ``srgbClr``, theme fonts ->
typefaces) so the diagram is pixel-identical AND natively editable in any deck.

This module owns the shared component-format primitives (theme flattening). The
``extract_diagram`` / ``inject_diagram`` tools build on top of them (extract-inject
tooling layer).

See ``references/native-diagrams.md`` for the placeholder contract consumed by the
SVG→PPTX converter.
"""
from .component import ThemeMaps, flatten_theme, load_theme_maps

__all__ = [
    "load_theme_maps",
    "flatten_theme",
    "ThemeMaps",
]
