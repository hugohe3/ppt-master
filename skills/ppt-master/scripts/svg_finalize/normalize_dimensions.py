#!/usr/bin/env python3
"""Backfill root ``<svg>`` ``width`` / ``height`` from ``viewBox``.

A root ``<svg>`` carrying only ``viewBox`` (no ``width`` / ``height``) is valid,
scalable SVG in browsers — which is exactly why generators omit the two
attributes. But PPT preview/export dimension detection (and the live-preview
"missing width/height" banner) keys off the explicit attributes. Rather than
rely on every model strictly following ``shared-standards.md §4``, this module
deterministically restores the attributes from ``viewBox`` wherever an
``svg_output`` consumer ingests the file (finalize → ``svg_final`` and the
live-preview serve path). The backfill is lossless: ``viewBox="0 0 W H"``
already carries the exact canvas dimensions, so ``width="W" height="H"`` is the
only correct value.

Two adapters share one rule so the ET-based server path and the string-based
finalize path cannot drift:

- :func:`backfill_root_dimensions` — mutate an ``ElementTree`` root in place.
- :func:`backfill_svg_dimensions` — rewrite raw SVG text.
"""

from __future__ import annotations

import re

__all__ = ["backfill_root_dimensions", "backfill_svg_dimensions"]


def _dims_from_viewbox(viewbox: str | None) -> tuple[str, str] | None:
    """Return ``(width, height)`` from a ``viewBox`` string, or ``None``.

    Only integer ``0 0 W H`` viewBoxes yield dimensions — the same shape the
    canvas formats emit and the quality checker compares against. Anything
    else (fractional, offset origin, malformed) is left untouched so we never
    invent a bogus size.
    """
    if not viewbox:
        return None
    parts = viewbox.split()
    if len(parts) != 4:
        return None
    min_x, min_y, width, height = parts
    if (min_x, min_y) != ("0", "0"):
        return None
    if not (width.isdigit() and height.isdigit()):
        return None
    if int(width) <= 0 or int(height) <= 0:
        return None
    return width, height


def backfill_root_dimensions(root) -> bool:
    """Set ``width`` / ``height`` on an ET ``<svg>`` root from ``viewBox``.

    Only fills an attribute that is absent — an author-supplied ``width`` /
    ``height`` (even a mismatched one) is preserved so this pass never
    overrides an explicit intent. Returns ``True`` when anything changed.
    """
    dims = _dims_from_viewbox(root.get("viewBox"))
    if dims is None:
        return False
    width, height = dims
    changed = False
    if not root.get("width"):
        root.set("width", width)
        changed = True
    if not root.get("height"):
        root.set("height", height)
        changed = True
    return changed


def backfill_svg_dimensions(content: str) -> tuple[str, bool]:
    """Inject missing ``width`` / ``height`` into raw SVG text.

    Operates only on the root ``<svg>`` open tag (child ``width`` / ``height``
    on ``<rect>``/``<image>`` are left alone). Returns ``(content, changed)``.
    """
    tag_match = re.search(r"<svg\b[^>]*>", content)
    if tag_match is None:
        return content, False
    tag = tag_match.group(0)

    vb_match = re.search(r'\bviewBox\s*=\s*"([^"]+)"', tag)
    dims = _dims_from_viewbox(vb_match.group(1) if vb_match else None)
    if dims is None:
        return content, False
    width, height = dims

    has_width = re.search(r'\bwidth\s*=\s*"', tag) is not None
    has_height = re.search(r'\bheight\s*=\s*"', tag) is not None
    if has_width and has_height:
        return content, False

    injected = ""
    if not has_width:
        injected += f' width="{width}"'
    if not has_height:
        injected += f' height="{height}"'
    new_tag = re.sub(r"^<svg\b", "<svg" + injected, tag, count=1)
    return content[: tag_match.start()] + new_tag + content[tag_match.end() :], True
