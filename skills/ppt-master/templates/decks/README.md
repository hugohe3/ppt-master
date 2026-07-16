# Deck Templates

**Deck = a complete reusable template bundle.** It owns both presentation
identity and reusable page structure. A deck template is not a finished content
deck, and `kind: deck` does not mean “mirror the source PPT”. Its construction
mode decides whether the system is newly authored or materialized from validated source facts.

| Axis | Deck behavior |
|---|---|
| Template kind | `deck`: identity + structure + deck-specific overview |
| Creation mode | `standard` / `fidelity` author a new system; `mirror` materializes validated source-package facts into a new workspace |
| Downstream adherence | Strategist selects `strict` or `adaptive` when the package is used |
| PPTX structure | Always `structured`; `flat` is reserved for free design and brand-only routes |

The discovery source of truth is [`decks_index.json`](./decks_index.json)
(`deck_id → { summary, canvas_format, page_count, primary_color }`). This README
defines the kind and intentionally does not enumerate installed decks. See
[`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md)
for the complete data model.

---

## Trigger and fusion

Selection is opt-in through an explicit workspace-root path such as
`skills/ppt-master/templates/decks/<deck_id>/`. Supplying a bare ID or reading
the discovery index does not trigger template use. Current packages resolve
`templates/design_spec.md`; a compatible flat-directory current-contract root
may resolve `design_spec.md` directly. Semantic-legacy packages must be replaced
through Create Template rather than upgraded in place. See [`SKILL.md`](../../SKILL.md) Step 3.

A deck path alone supplies the complete reference. When combined with a brand
or layout path, brand replaces the identity segment and layout replaces the
structure segment; the deck remains the source of deck-specific overview
context. Fusion never changes the package's stored SVGs in place.

---

## `design_spec.md` contract

The spec stores portable metadata plus template-specific personality. It does
not repeat generic SVG rules, spacing libraries, font-ratio bands, or the
canonical placeholder table.

```markdown
---
deck_id: <slug>
kind: deck
category: brand | general | scenario | government | special
summary: <one-line use case and tone>
primary_color: "#XXXXXX"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
---

# [Template Name] — Design Specification

## I. Template Overview
## II. Color Scheme
## III. Typography                 # omit only when the shared default is used
## IV. Signature Design Elements
## V. Page Roster
## VI. Assets                      # omit when none
## VII. Placeholder Overrides      # omit when none
```

`Page Roster` must list every SVG and its declared Master/Layout identity.
Every additional authored Master represents a distinct reusable design family,
not one Layout or an organizational duplicate.

---

## Structured SVG contract

Every SVG is a complete preview and declares one root Master and Layout.
Master/Layout fixed visuals are direct atoms. Reusable content regions are
top-level slot groups with positive bounds and exactly one compatible carrier;
zero-slot Layouts are valid. `{{...}}` is the authoring vocabulary, while
`data-pptx-placeholder*` is the native reconstruction contract.

`standard` and `fidelity` author new SVGs and a new Master/Layout/slot system.
`mirror` preserves existing source identities, parentage, assignments,
placeholder facts, and supported visuals in a new workspace without semantic
synthesis. Legacy semantic contracts are not upgraded in place; create a new
workspace through [`create-template`](../../workflows/create-template.md). A
flat directory shape alone is not a legacy signal.

---

## Workspace and creation

```text
<template_workspace>/
├── templates/                # design_spec.md + SVG prototypes
├── images/                   # optional bitmaps; SVG href is ../images/<name>
├── icons/
│   └── imported/             # optional canonical imported vectors
└── exports/                  # review evidence; ignored during template use
    └── <deck_id>_template_preview.pptx
```

Library scope writes `skills/ppt-master/templates/decks/<deck_id>/` and updates
the index. Project scope uses an initialized `projects/<name>/` workspace and
does not register globally. Empty optional directories are omitted.

1. Enter [`workflows/create-template.md`](../../workflows/create-template.md), which dispatches integrated identity-and-structure output to [`create-deck.md`](../../workflows/create-template/create-deck.md).
2. Validate with `svg_quality_checker.py --template-mode`.
3. Run `template_preview_pptx.py` when review is requested and always when the roster declares multiple Masters.
4. In library scope, register with `register_template.py <id> --kind deck`.

See also [`layouts/`](../layouts/) for structure-only packages and
[`brands/`](../brands/) for identity-only packages.
