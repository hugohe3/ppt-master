# Structure Visualization Templates

This directory contains page-local qualitative topology references. A
structure belongs here when sequence, hierarchy, role, region, comparison, or
relationship determines its nodes and connections, while numeric values do not
drive mark geometry.

Value-driven graphics belong in [`charts/`](../charts/). Cell-grid semantics
belong in [`tables/`](../tables/). Reusable PowerPoint Master/Layout systems
belong in [`layouts/`](../layouts/).

## Source of truth

[`structures_index.json`](./structures_index.json) is the sole structure
registry. Its `structures` object maps each canonical key to one selection-rule
`summary`; keys match `<key>.svg`, and `meta.total` matches the canonical SVG
roster.

Use [`visualization_recall.py`](../../scripts/visualization_recall.py) for
bounded all-family or structure-only recall. New Default planning writes
`structure/<key>` to `page_visualizations`; Quick keeps the selected reference
in active context.

## Authoring contract

[`VISUALIZATION_TEMPLATE_AUTHORING.md`](../VISUALIZATION_TEMPLATE_AUTHORING.md)
owns the shared standalone-SVG, neutral-preview, root-boundary, Shape-first,
family, and catalog rules. Structure-specific requirements are:

- Preserve qualitative order, hierarchy, containment, direction, comparison,
  and reading flow.
- Keep every object Slide-local. Structure SVGs never own
  `data-pptx-master`, `data-pptx-layout`, `data-pptx-layer`, or
  `data-pptx-placeholder`.
- Treat a full-canvas preview as one-page composition guidance, not as a
  reusable PowerPoint Layout.
- Never add native Chart/Table replacement markers to conceptual diagrams,
  frameworks, processes, timelines, or topology.

`quadrant_text_cards` is a structure: it provides four fixed named regions,
each with a title and text items, and has no value-mapped bubbles.
`layered_pyramid` is a qualitative hierarchy; `pyramid_isometric` remains the
separate dramatic four-tier structure. `pros_cons_comparison` is the canonical
bilateral argument structure.

## Layout workspace boundary

A Layout workspace is selected as a reusable package and owns Master/Layout
atoms, page types, slot geometry, placeholder roles, and structured export
mapping. A structure reference applies only to one mapped page and remains
adaptable under §IX. When a Layout workspace is active, use a structure only
inside compatible open or object content regions; never let it overwrite the
Layout's fixed atoms or slot topology.
