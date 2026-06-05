"""Native-diagram library: lift editable DrawingML diagrams between decks.

Unlike the SVG pipeline (``pptx_to_svg`` -> ``svg_to_pptx``), this package never
re-renders. It lifts a slide's ``<p:sp>`` / ``<p:grpSp>`` XML verbatim and only
flattens theme dependencies (``schemeClr`` -> ``srgbClr``, theme fonts ->
typefaces) so the diagram is pixel-identical AND natively editable in any deck.

- ``extract_diagram`` — source ``.pptx`` slide -> self-contained component dir
- ``inject_diagram``  — component dir -> shapes appended into a target deck
"""
from .component import ThemeMaps, flatten_theme, load_theme_maps
from .extract import extract_diagram
from .inject import inject_diagram

__all__ = [
    "extract_diagram",
    "inject_diagram",
    "load_theme_maps",
    "flatten_theme",
    "ThemeMaps",
]
