---
description: Create Layout child workflow for a brand-neutral reusable page-structure workspace.
---

# Create Layout Workflow

Enter this child workflow only after [`Create Template`](../create-template.md) dispatches `kind: layout`.

## Responsibility Boundary

| Owner | Responsibilities |
|---|---|
| Create Template | Child-workflow dispatch plus the shared source taxonomy, `library` / `project` scope, confirmation gate, collision preflight, structured authoring contract, validation commands, registration, completion, and Generate PPTX handoff |
| Create Layout | Structure-only interpretation, layout-specific brief fields, brand-neutral `design_spec.md`, SVG roster, and layout-specific validation |

**Hard rule — child workflow, not a top-level route**: Create Layout executes only inside Create Template. It reuses the parent workflow's Steps 1–8 and never creates a competing entry route or second confirmation gate.

**Hard rule — structure only**: A layout owns canvas, page grammar, Master/Layout families, slot geometry, page types, image behavior, density rhythm, and the SVG prototype roster. It owns no brand palette, typography system, logo, voice, or icon identity.

Neutral colors and safe fonts may appear in SVG prototypes so the structure is reviewable. They are preview paint, not a locked identity segment, and must not be written as brand truth in `design_spec.md`.

## Invocation Points

1. Use §1–2 below while executing Create Template Steps 1–3.
2. After Create Template Step 4 preflights `<template_workspace>`, use §3 to author or materialize the layout workspace under the shared structured contract.
3. Apply §4 in addition to Create Template Step 5, then continue through shared Steps 6–8.

## 1. Layout Input Interpretation

Use Create Template Step 1 for source ingestion and replication-mode eligibility. Interpret source evidence only for reusable structure:

- Canvas dimensions, grid, zones, page taxonomy, repeated chrome, image placement, density rhythm, and placeholder geometry may become layout facts or suggestions.
- Colors, fonts, logos, voice, and icon style remain source context only. Do not copy them into the layout identity because a layout has no identity segment.
- When the source is branded, explicitly confirm that Create Layout will strip that identity. If the user wants the identity retained with the structure, return to Create Template dispatch and select Create Deck before the shared confirmation marker is emitted.
- `standard` and `fidelity` author a new Master/Layout/slot system. `mirror` is available only when the source contains a complete current structure contract and preserves validated structure facts in a new workspace without modifying the source.

Direct conversation text, pasted requirements, converted documents/websites, images, and supplied assets may define or illustrate reusable structure. In a mixed bundle, combine those channels without treating identity-only evidence as layout ownership. Exact user-authored instructions remain decisions whether they arrive in chat or a user-written brief file; vague prose remains suggested interpretation until the shared confirmation gate.

## 2. Layout Brief and Schema

Add these child-owned requirements to Create Template Step 2:

| Field | Requirement |
|---|---|
| Layout ID and display name | Required; `layout_id` is a filesystem-safe ASCII slug |
| Structural use cases | Required; describe content shapes and presentation contexts, not brand tone |
| Canvas | Required; exact format, dimensions, and `viewBox` |
| Page grammar | Required; page types, variants, grids, zones, density rhythm, and image behavior |
| Native structure | Required; Master families, Layout ownership, slot vocabulary, and zero-slot Layouts where intentional |
| Replication mode | Required; `standard`, eligible `fidelity`, or eligible `mirror` under Create Template Step 1 |
| Identity stripping | Required when branded reference material exists; list the identity facts intentionally excluded |

Write this structure-only schema:

```markdown
---
layout_id: <confirmed slug>
kind: layout
category: general | scenario | government | special
summary: <one-line structural use case>
keywords: [<three-to-five structural tags>]
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
page_types: [cover, toc, chapter, content, ending]
---

# <Layout Name> — Design Specification

## IV. Signature Design Elements
## V. Page Roster
## VII. Placeholder Overrides
```

Omit `Placeholder Overrides` when no override exists. Omit Template Overview, Color Scheme, Typography, Logo, Voice, and every other identity section. Do not write `primary_color`.

`Signature Design Elements` describes only reusable structure. `Page Roster` lists every SVG with its Master/Layout identity, picker name, intended content shape, and slot behavior.

## 3. Author or Materialize the Layout

Follow Create Template Step 4 and the shared Template_Designer contract with `kind: layout`, `kind_dir: layouts`, and `id_key: layout_id` fixed. Do not ask the user to choose the kind again.

The output is:

```text
<template_workspace>/
├── templates/        # design_spec.md + SVG prototypes
├── images/           # optional structural/example bitmaps
├── icons/
│   └── imported/     # optional imported vectors
└── exports/          # conditional review evidence
```

Every SVG is a complete preview and declares one root Master and Layout under the shared structured contract. For authored modes, neutral preview paint must remain replaceable downstream. For mirror, preserve source structure and supported visuals exactly as allowed by Create Template, while keeping identity fields out of the layout spec.

## 4. Layout Validation

In addition to Create Template Steps 5–6, verify:

- `templates/design_spec.md` contains `layout_id`, `kind: layout`, `summary`, canvas fields, `replication_mode`, `native_structure_mode: structured`, `page_count`, and `page_types`.
- `layout_id` matches the confirmed workspace ID in library scope.
- Signature Design Elements and Page Roster exist; Template Overview and all identity sections do not.
- `primary_color`, brand palette, brand typography, logo, voice, and icon-identity claims are absent.
- Every SVG in the roster satisfies the shared Master/Layout/slot contract and the roster is bidirectionally complete.
- Neutral prototype paint is not described as a locked brand identity.

For library scope, Create Template validates and registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <layout_id> --kind layout --dry-run
python3 skills/ppt-master/scripts/register_template.py <layout_id> --kind layout
```

For project scope, skip both commands. The exact workspace root becomes the next Generate PPTX Step 3 input; downstream identity remains a Strategist decision unless an explicit Brand or Deck workspace is also supplied.
