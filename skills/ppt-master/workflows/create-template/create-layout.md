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

**Hard rule — brand-neutral structure only**: A layout owns canvas, page grammar, Master/Layout families, slot geometry, semantic text roles, alignment/wrapping/capacity behavior, page types, image behavior, density rhythm, and the SVG prototype roster. It owns no brand palette, typeface/weight identity, final resolved type scale, logo, voice, icon identity, communication objective, audience outcome, required narrative sequence, fixed scenario copy, or example content that downstream generation is expected to preserve.

Neutral colors, safe fonts, and provisional sizes may appear in SVG prototypes so the structure is reviewable. They are preview values, not a locked identity segment or final project type scale, and must not be written as brand truth in `design_spec.md`. The reusable rule is the text role and its spatial behavior. Downstream `layout` scope resolves actual appearance from Brand, reading mode, and confirmed project typography; explicit `mirror` scope preserves the literal source formatting instead.

## Invocation Points

1. Use §1–2 below while executing Create Template Steps 1–3.
2. After Create Template Step 4 preflights `<template_workspace>`, use §3 to author or materialize the layout workspace under the shared structured contract.
3. Apply §4 in addition to Create Template Step 5, then continue through shared Steps 6–8.

## 1. Layout Input Interpretation

Use Create Template Step 1 for source ingestion and internal creation-strategy feasibility. Interpret source evidence only for reusable structure:

- Canvas dimensions, grid, zones, page taxonomy, repeated chrome, image placement, density rhythm, placeholder geometry, semantic text roles, alignment, wrapping, and capacity may become layout facts or suggestions.
- Colors, font families, branded weight choices, final absolute sizes, logos, voice, and icon style remain source context only. Do not copy them into the layout identity because a layout has no identity segment.
- A source scenario may inform the content shapes or delivery conditions the geometry can support. Do not turn that fit into an application contract. If the reusable artifact prescribes the objective, outcome, narrative sequence, boilerplate, or content policy, return to Create Template dispatch and select Create Deck.
- When the source is branded, state in plain language that Create Layout will omit the identity. The AI therefore derives an authored internal strategy. If the user wants the identity retained with the structure, return to Create Template dispatch and select Create Deck before the shared confirmation marker is emitted.
- Internally, `standard` and `fidelity` author a new Master/Layout/slot system. `mirror` may be derived only when the complete current source contract is already brand-neutral and application-neutral; it preserves validated structure and visual facts in a new workspace without modifying the source. Never ask the user to choose among these labels.

Direct conversation text, pasted requirements, converted documents/websites, images, and supplied assets may define or illustrate reusable structure. In a mixed bundle, combine those channels without treating identity-only evidence as layout ownership. Exact user-authored instructions remain decisions whether they arrive in chat or a user-written brief file; vague prose remains suggested interpretation until the shared confirmation gate.

## 2. Layout Brief and Schema

Add these child-owned requirements to Create Template Step 2:

| Field | Requirement |
|---|---|
| Layout ID and display name | Required; `layout_id` is a filesystem-safe ASCII slug |
| Structural use cases | Required; describe content shapes and delivery settings the geometry can support, not communication objectives, audience outcomes, narrative sequence, or brand tone |
| Canvas | Required; exact format, dimensions, and `viewBox` |
| Page grammar | Required; page types, variants, grids, zones, semantic text roles, alignment/wrapping/capacity, density rhythm, and image behavior |
| Native structure | Required; Master families, Layout ownership, slot vocabulary, and zero-slot Layouts where intentional |
| Creation intent | Required as natural-language prose: what should remain recognizable, what should become reusable structure, and how broad the page vocabulary should be. The AI derives `replication_mode` internally from this intent and the evidence. |
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

`replication_mode` is required machine provenance, not a user-facing choice. Omit `Placeholder Overrides` when no override exists. Omit Template Overview, Color Scheme, Typography, Logo, Voice, and every other identity section. Do not write `primary_color`.

`Signature Design Elements` describes only reusable structure, including text-role hierarchy and spatial behavior without locking the final font identity or type scale. `Page Roster` lists every SVG with its Master/Layout identity, picker name, intended content shape, and slot behavior.

`category: scenario` is a discovery-fit label only. It does not authorize a
Template Overview or scenario-specific content policy.

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

Every SVG is a complete preview and declares one root Master and Layout under the shared structured contract. For authored modes, neutral preview paint must remain replaceable downstream. For mirror, first prove the source contract already satisfies the complete Layout boundary, then preserve its structure and supported visuals exactly as allowed by Create Template. Never call removal or replacement of source identity or application rules “mirror”.

## 4. Layout Validation

In addition to Create Template Steps 5–6, verify:

- `templates/design_spec.md` contains `layout_id`, `kind: layout`, `summary`, canvas fields, `replication_mode`, `native_structure_mode: structured`, `page_count`, and `page_types`.
- `layout_id` matches the confirmed workspace ID in library scope.
- Signature Design Elements and Page Roster exist; Template Overview, application-contract language, and all identity sections do not.
- `primary_color`, brand palette, brand typeface/weight claims, final project type-scale claims, logo, voice, and icon-identity claims are absent; structural text roles and capacity rules may remain.
- Every SVG in the roster satisfies the shared Master/Layout/slot contract and the roster is bidirectionally complete.
- Neutral prototype paint is not described as a locked brand identity.
- `replication_mode: mirror` is rejected for any source that retains organization-specific identity or reusable application rules; use authored Layout mode or Create Deck instead.

For library scope, Create Template validates and registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <layout_id> --kind layout --dry-run
python3 skills/ppt-master/scripts/register_template.py <layout_id> --kind layout
```

For project scope, skip both commands. The exact workspace root becomes the next Generate PPTX Step 3 input; downstream identity remains a Strategist decision unless an explicit Brand or Deck workspace is also supplied.
