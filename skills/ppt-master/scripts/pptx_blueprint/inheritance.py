"""Master/Layout/Slide three-tier inheritance resolution.

DrawingML placeholder shapes derive attributes via a chain:
    slide   (most specific — concrete values)
      -> slideLayout  (placeholder defaults for this layout)
      -> slideMaster  (global defaults)

Background inheritance follows the same chain.

This module uses a **lazy inheritance** strategy: instead of deep-merging XML
trees (expensive and error-prone), we build a `ResolvedShape` wrapping the
slide element plus matching layout/master elements, and callers look up
attributes by walking the chain with `find_first`. This keeps the merge logic
simple and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


# ---------------------------------------------------------------------------
# Placeholder key extraction
# ---------------------------------------------------------------------------

def read_ph(shape_elem: ET.Element) -> tuple[str | None, str | None] | None:
    """Read a shape's <p:ph> element and return (type, idx), or None if not a placeholder.

    Both type and idx may individually be None — DrawingML allows placeholders
    that have only one of them. The matching logic below handles partial keys.
    """
    ph = shape_elem.find(".//p:nvSpPr/p:nvPr/p:ph", NS)
    if ph is None:
        # <p:pic> and <p:graphicFrame> have their own nv* wrappers
        ph = shape_elem.find(".//p:nvPicPr/p:nvPr/p:ph", NS)
    if ph is None:
        ph = shape_elem.find(".//p:nvGraphicFramePr/p:nvPr/p:ph", NS)
    if ph is None:
        return None

    ph_type = ph.attrib.get("type")  # title, body, ctrTitle, subTitle, pic, ...
    ph_idx = ph.attrib.get("idx")  # "0", "1", ... (string per schema)
    return (ph_type, ph_idx)


def _iter_spTree_shapes(root: ET.Element) -> list[ET.Element]:
    """Return all <p:sp>, <p:pic>, <p:grpSp>, <p:graphicFrame> under spTree."""
    sp_tree = root.find(".//p:cSld/p:spTree", NS)
    if sp_tree is None:
        return []

    results: list[ET.Element] = []
    for child in sp_tree:
        if not isinstance(child.tag, str):
            continue
        local = child.tag.split("}", 1)[-1]
        if local in ("sp", "pic", "grpSp", "graphicFrame"):
            results.append(child)
    return results


# ---------------------------------------------------------------------------
# Inheritance context + placeholder registry
# ---------------------------------------------------------------------------

@dataclass
class InheritanceContext:
    """Per-slide inheritance chain: references plus indexed placeholder tables.

    The placeholder tables are keyed by partial keys so we can match a
    slide placeholder against layout/master even when only `type` or only
    `idx` is present.
    """

    layout_root: ET.Element | None
    master_root: ET.Element | None

    # (type, idx) -> element. Missing parts are stored as None.
    layout_phs: dict[tuple[str | None, str | None], ET.Element] = field(default_factory=dict)
    master_phs: dict[tuple[str | None, str | None], ET.Element] = field(default_factory=dict)


def _index_placeholders(root: ET.Element | None) -> dict[tuple[str | None, str | None], ET.Element]:
    """Collect (type, idx) -> shape for all placeholders in a root (layout or master)."""
    if root is None:
        return {}

    result: dict[tuple[str | None, str | None], ET.Element] = {}
    for shape in _iter_spTree_shapes(root):
        key = read_ph(shape)
        if key is None:
            continue
        # If duplicate keys appear, the first one wins (XML order).
        result.setdefault(key, shape)
    return result


def build_inheritance_context(
    layout_root: ET.Element | None,
    master_root: ET.Element | None,
) -> InheritanceContext:
    """Prepare the per-slide inheritance context with indexed placeholders."""
    return InheritanceContext(
        layout_root=layout_root,
        master_root=master_root,
        layout_phs=_index_placeholders(layout_root),
        master_phs=_index_placeholders(master_root),
    )


# ---------------------------------------------------------------------------
# Resolved shape (lazy inheritance view)
# ---------------------------------------------------------------------------

@dataclass
class ResolvedShape:
    """A slide shape with its inheritance chain for lazy attribute lookup.

    Callers use `find_first()` to traverse slide -> layout -> master and
    return the first match. This avoids the need to deep-merge XML trees.
    """

    slide_sp: ET.Element
    layout_sp: ET.Element | None = None
    master_sp: ET.Element | None = None
    ph_key: tuple[str | None, str | None] | None = None

    def find_first(self, xpath: str) -> ET.Element | None:
        """Find an element along the chain. Returns the first match."""
        for root in (self.slide_sp, self.layout_sp, self.master_sp):
            if root is None:
                continue
            found = root.find(xpath, NS)
            if found is not None:
                return found
        return None

    def findall_all(self, xpath: str) -> list[ET.Element]:
        """Collect matching elements across the chain (slide first)."""
        results: list[ET.Element] = []
        for root in (self.slide_sp, self.layout_sp, self.master_sp):
            if root is None:
                continue
            results.extend(root.findall(xpath, NS))
        return results

    def get_attr_first(self, xpath: str, attr_name: str) -> str | None:
        """Get an attribute value from the first matching element in the chain."""
        for root in (self.slide_sp, self.layout_sp, self.master_sp):
            if root is None:
                continue
            found = root.find(xpath, NS)
            if found is not None and attr_name in found.attrib:
                return found.attrib[attr_name]
        return None


# ---------------------------------------------------------------------------
# Public resolver
# ---------------------------------------------------------------------------

def _match_in_table(
    key: tuple[str | None, str | None],
    table: dict[tuple[str | None, str | None], ET.Element],
) -> ET.Element | None:
    """Match a placeholder key against a table, tolerating partial matches.

    Preference:
        1. exact (type, idx) match
        2. same idx (any type) — for body placeholders with idx but no type
        3. same type (any idx) — for singleton placeholders like title
    """
    ph_type, ph_idx = key
    # Exact match
    if key in table:
        return table[key]
    # Same idx, any type
    if ph_idx is not None:
        for k, v in table.items():
            if k[1] == ph_idx:
                return v
    # Same type, any idx
    if ph_type is not None:
        for k, v in table.items():
            if k[0] == ph_type:
                return v
    # Title/ctrTitle interchange (common in cover layouts)
    title_aliases = {"title", "ctrTitle"}
    if ph_type in title_aliases:
        for k, v in table.items():
            if k[0] in title_aliases:
                return v
    return None


def resolve_shape(
    slide_sp: ET.Element,
    ctx: InheritanceContext,
) -> ResolvedShape:
    """Build a ResolvedShape with the full inheritance chain for a slide shape.

    Non-placeholder shapes still get a ResolvedShape (with layout_sp and
    master_sp set to None) so callers have a uniform interface.
    """
    ph_key = read_ph(slide_sp)
    if ph_key is None:
        return ResolvedShape(slide_sp=slide_sp)

    layout_match = _match_in_table(ph_key, ctx.layout_phs)
    master_match = _match_in_table(ph_key, ctx.master_phs)

    return ResolvedShape(
        slide_sp=slide_sp,
        layout_sp=layout_match,
        master_sp=master_match,
        ph_key=ph_key,
    )


# ---------------------------------------------------------------------------
# Background resolution
# ---------------------------------------------------------------------------

def resolve_background(
    slide_root: ET.Element,
    ctx: InheritanceContext,
) -> ET.Element | None:
    """Find the effective <p:bg> or <p:bgRef> for a slide.

    Checks slide first, then layout, then master. Returns the raw element
    (caller decodes fill kind).
    """
    for root in (slide_root, ctx.layout_root, ctx.master_root):
        if root is None:
            continue
        bg = root.find(".//p:cSld/p:bg", NS)
        if bg is not None:
            return bg
    return None


# ---------------------------------------------------------------------------
# Placeholder shapes added by layout/master (not present on the slide)
# ---------------------------------------------------------------------------

def collect_inherited_shapes(
    slide_root: ET.Element,
    ctx: InheritanceContext,
) -> list[ET.Element]:
    """Return layout/master placeholder shapes that the slide does NOT override.

    A slide may omit a placeholder (e.g. page number, footer) which should
    still render from the layout/master. We collect those so the emitter
    can include them in the final SVG.

    Returns layout-level shapes first (closer to the slide), then master-level.
    A master placeholder is included only if neither the slide nor the layout
    carries an overriding shape with the same key.
    """
    # Collect slide's placeholder keys
    slide_keys: set[tuple[str | None, str | None]] = set()
    for sp in _iter_spTree_shapes(slide_root):
        key = read_ph(sp)
        if key is not None:
            slide_keys.add(key)

    inherited: list[ET.Element] = []
    # Layout: include placeholders not overridden by slide
    layout_keys_included: set[tuple[str | None, str | None]] = set()
    for key, elem in ctx.layout_phs.items():
        if key not in slide_keys:
            inherited.append(elem)
            layout_keys_included.add(key)

    # Master: include placeholders not overridden by slide or layout
    for key, elem in ctx.master_phs.items():
        if key not in slide_keys and key not in layout_keys_included:
            inherited.append(elem)

    return inherited
