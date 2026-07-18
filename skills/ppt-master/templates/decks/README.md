# Deck Templates

**Deck = a reusable solution for a recurring presentation family.** It owns an
application context together with presentation identity and reusable page
structure. The application context states which communication situations the
template serves, which audience outcomes it supports, and which narrative/page
roles commonly appear. It describes the resource; it does not decide which
pages or visible content a future presentation must retain.
A deck template is not a finished content deck, and `kind: deck` does not mean
“mirror the source PPT”. Its construction mode decides whether the system is
newly authored or materialized from validated source facts.

| Axis | Deck behavior |
|---|---|
| Template kind | `deck`: descriptive application context + integrated identity + structure |
| Internal creation strategy | AI derives `standard` / `fidelity` for a new system or `mirror` for validated source-package materialization; the field is tool provenance, not a user choice |
| Application planning | Strategist automatically decides which prototypes to select, repeat, skip, or reorganize and derives the exporter behavior |
| PPTX structure | The workspace is `structured`; the derived application plan decides whether generated pages compile its structure or use it only as visual reference |

The discovery source of truth is [`decks_index.json`](./decks_index.json)
(`deck_id → { summary, canvas_format, page_count, primary_color }`). This README
defines the kind and intentionally does not enumerate installed decks. The
shared kind and workspace model lives in the parent
[`README.md`](../README.md).

Index `summary` values lead with the recurring presentation family and intended
outcome. Visual tone alone is not enough to select a Deck; open its Template
Overview when application fit must be judged in detail.

---

## Trigger and fusion

Selection uses the common explicit-path trigger in
[`generate-pptx`](../../workflows/generate-pptx.md) Step 3. Supplying a bare ID
or reading the discovery index does not trigger template use. The conditional
[`apply-template-workspace`](../../workflows/stages/apply-template-workspace.md)
stage owns path normalization, compatibility checks, installation, and fusion.
This file owns the Deck schema and application-context boundary.

---

## `design_spec.md` contract

The spec stores portable metadata plus package-owned application, identity,
and structure rules. It does not repeat generic SVG rules, spacing libraries,
font-ratio bands, or the canonical placeholder table.

```markdown
---
deck_id: <slug>
kind: deck
category: brand | general | scenario | government | special
summary: <one-line recurring presentation family and intended outcome>
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

`replication_mode` records how the workspace was produced. Create Template
derives it from the natural-language brief and source evidence; users do not
need to select or understand this field.

`Template Overview` is descriptive application context, not a style
description or future-use policy. It identifies the recurring presentation
family, intended audiences and outcomes, delivery/reading assumptions, and
representative narrative or page roles. These values may be broad when the
source supports a family of related uses, but they must be specific enough to
help Strategist understand the resource.

`Page Roster` must list every SVG and its declared Master/Layout identity, then
describe its observed or intended role, visual character, reusable slots, and
structural capacity. It must not mark pages required/optional/repeatable or
content fixed/replaceable/example-only. Strategist inspects the actual roster
and current material and decides what to use.

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

1. Enter [`workflows/create-template.md`](../../workflows/create-template.md), which dispatches recurring-application output with integrated identity and structure to [`create-deck.md`](../../workflows/create-template/create-deck.md).
2. Validate with `svg_quality_checker.py --template-mode`.
3. Run `template_preview_pptx.py` when review is requested and always when the roster declares multiple Masters.
4. In library scope, register with `register_template.py <id> --kind deck`.

See also [`layouts/`](../layouts/) for structure-only packages and
[`brands/`](../brands/) for identity-only packages.
