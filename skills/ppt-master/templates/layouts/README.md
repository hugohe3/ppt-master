# Layout Templates

**Layout = a structure-only reusable template bundle.** It owns canvas,
Master/Layout structure, page types, slot geometry, semantic text roles,
alignment/wrapping/capacity behavior, and the SVG roster. It does not own
brand color, typeface/weight identity, the final resolved type scale, logo,
voice, or icon style. Those identity decisions come from an explicit
brand/deck source or from the Strategist confirmation stage.

A layout may describe the content shapes and delivery conditions its geometry
can support. It must not own a communication objective, audience outcome,
scenario-specific narrative sequence, fixed boilerplate, or example content
that downstream generation is expected to preserve. Those application rules
belong to a Deck. A structurally useful “board update” page can remain a
Layout; a board-update sequence with required decision, risk, and action roles
is a Deck.

Neutral colors, safe fonts, and provisional sizes may appear in SVG prototypes
so the structure is reviewable. They are preview values, not a locked identity
segment or final type scale. The reusable rule is the role hierarchy and its
spatial behavior. Downstream `layout` scope resolves its appearance from the
Brand, reading mode, and confirmed project lock; explicit `mirror` scope keeps
literal source formatting.

| Axis | Layout behavior |
|---|---|
| Template kind | `layout`: structure only |
| Creation mode | `standard` / `fidelity` author a new system; `mirror` materializes validated source-package facts into a new workspace |
| Downstream adherence | Strategist selects `strict` or `adaptive` when the package is used |
| PPTX structure | Workspace is `structured`; downstream `mirror` / `layout` use it, while confirmed `style` intentionally discards structure and generates `flat` |

The discovery source of truth is [`layouts_index.json`](./layouts_index.json)
(`layout_id → { summary, canvas_format, page_count, page_types }`). This README
defines the kind and intentionally does not enumerate installed layouts. The
shared kind and workspace model lives in the parent
[`README.md`](../README.md).

Layout mirror has one additional eligibility rule: the validated source
contract must already be brand-neutral and application-neutral. A source
outside that boundary can become a Layout only through `standard` or
`fidelity`, which deliberately authors a new neutral system. If its identity or
application rules must remain literal, create a Deck instead. Removing either
kind of rule is never a mirror operation.

---

## Trigger and identity boundary

Selection is opt-in through an explicit workspace-root path such as
`skills/ppt-master/templates/layouts/<layout_id>/`. Supplying a bare ID or
reading the discovery index does not trigger template use. A layout path alone
locks structure while identity remains a downstream decision. Combined with a
brand or deck, the layout replaces the complete structure segment.

Current packages resolve `templates/design_spec.md`; compatible flat-directory
current-contract roots may resolve `design_spec.md` directly. Semantic-legacy
packages must be replaced through Create Template rather than upgraded in
place. See [`SKILL.md`](../../SKILL.md) Step 3.

---

## `design_spec.md` contract

The spec stores portable structural metadata plus rules unique to this layout.
It omits the deck-only Template Overview/application contract and every
identity section. The frontmatter `summary` carries the concise selection
context.

```markdown
---
layout_id: <slug>
kind: layout
category: general | scenario | government | special
summary: <one-line structural use case>
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
page_types: [cover, toc, chapter, content, ending]
---

# [Layout Name] — Design Specification

## IV. Signature Design Elements
## V. Page Roster
## VII. Placeholder Overrides      # omit when none
```

`Signature Design Elements` describes only reusable structure: grids, zones,
image behavior, density rhythm, semantic text roles, alignment/wrapping/
capacity behavior, and slot conventions. It must not introduce a brand
palette, typeface identity, final type scale, communication objective, or
required narrative sequence. `Page Roster` lists every SVG with its Layout
key, PowerPoint picker name, supported content shape, and slot behavior.

---

## Structured SVG and slot contract

Every SVG is a complete preview and declares one root Master and Layout.
Master/Layout fixed visuals are direct atoms. A reusable slot is a top-level
`<g id>` with positive design-zone bounds and exactly one compatible carrier;
zero-slot Layouts are valid. A typed `picture`, `chart`, or `table` slot does
not by itself promise an inserted picture or native data object: the generated
Slide supplies its content, and Chart/Table native replacement remains an
explicit export choice.

Use canonical `{{PLACEHOLDER}}` names where they fit. A layout with intentional
vocabulary overrides declares a `placeholders:` map in frontmatter. Full rules:
[`template-designer.md`](../../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template).

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
    └── <layout_id>_template_preview.pptx
```

Library scope writes `skills/ppt-master/templates/layouts/<layout_id>/` and
updates the index. Project scope uses an initialized `projects/<name>/`
workspace and does not register globally. Empty optional directories are
omitted.

1. Enter [`workflows/create-template.md`](../../workflows/create-template.md), which dispatches structure-only output to [`create-layout.md`](../../workflows/create-template/create-layout.md).
2. Validate with `svg_quality_checker.py --template-mode`.
3. Run `template_preview_pptx.py` when review is requested and always when the roster declares multiple Masters.
4. In library scope, register with `register_template.py <id> --kind layout`.

General SVG/PPT rules remain authoritative in
[`shared-standards.md`](../../references/shared-standards.md).
