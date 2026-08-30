---
description: Create Layout child workflow for a brand-neutral reusable page-structure workspace.
---

# Create Layout Workflow

Enter only after [`Create Template`](../create-template.md) dispatches `kind: layout`. Create Template owns dispatch, the source taxonomy, scope, the confirmation gate, collision preflight, the structured authoring contract, validation commands, registration, completion, and the Generate handoff; Create Layout owns structure-only interpretation, layout brief fields, the brand-neutral spec, the SVG roster, and layout validation.

**Hard rule — child workflow, not a top-level route**: executes only inside Create Template Steps 1–8.

**Hard rule — brand-neutral structure only**: a layout owns canvas, page grammar, Master/Layout families, slot geometry, semantic text roles, alignment/wrapping/capacity behavior, page types, image behavior, density rhythm, and the prototype roster — no palette, typeface/weight identity, final type scale, logo, voice, icon identity, communication objective, audience outcome, narrative sequence, scenario copy, or example content downstream must preserve. Neutral colors, safe fonts, and provisional sizes may appear in prototypes for review; they are preview values, never identity or a locked scale. Downstream `layout` scope resolves appearance from Brand, reading mode, and project typography; `mirror` scope preserves literal source formatting.

**Invocation**: §1–2 during Create Template Steps 1–3; after Step 4 preflights the workspace, §3 authors or materializes under the shared structured contract; §4 adds to Step 5, then shared Steps 6–8.

## 1. Layout Input Interpretation

Use Create Template Step 1 for ingestion and strategy feasibility, reading evidence only for reusable structure: canvas, grid, zones, page taxonomy, repeated chrome, image placement, density rhythm, placeholder geometry, semantic text roles, alignment, wrapping, and capacity may become facts or suggestions; colors, font families, weights, absolute sizes, logos, voice, and icon style stay context only. A source scenario may inform supported content shapes and delivery conditions but never becomes an application contract — if the artifact prescribes objective, outcome, sequence, boilerplate, or content policy, return to dispatch and select Create Deck. When the source is branded, state plainly that identity will be omitted (so an authored strategy is derived); if the user wants identity retained, return to dispatch for Create Deck before the marker. `standard` / `fidelity` inspect the complete inventory and author a new system; `mirror` is derived only when the source-Slide-reachable contract is complete, brand-neutral, and application-neutral. Direct text, converted documents, images, and assets may define structure; identity-only evidence never grants ownership; user-authored instructions are decisions in any carrier, vague prose stays suggested until the gate.

## 2. Layout Brief and Schema

Add to Create Template Step 2 (all required unless noted): Layout ID (ASCII slug) and display name; structural use cases (content shapes and delivery settings, not objectives, outcomes, sequence, or tone); canvas (exact format, dimensions, `viewBox`); page grammar (types, variants, grids, zones, text roles, alignment/wrapping/capacity, density, image behavior); native structure (Master families, Layout ownership, slot vocabulary, intentional zero-slot Layouts); creation intent as prose (what stays recognizable, what becomes reusable, how broad the vocabulary is — `replication_mode` is derived from it); identity stripping (required for branded references: the identity facts excluded).

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

`replication_mode` is machine provenance, never a user choice. Omit `Placeholder Overrides` without overrides; omit Template Overview, Color Scheme, Typography, Logo, Voice, and every identity section; never write `primary_color`. `Signature Design Elements` describes reusable structure including text-role hierarchy and spatial behavior without locking font identity or scale; `Page Roster` lists every SVG with Master/Layout identity, picker name, content shape, and slot behavior. `category: scenario` is a discovery label and authorizes no Overview or scenario content policy.

## 3. Author or Materialize the Layout

Follow Create Template Step 4 and the Template_Designer contract with `kind: layout`, `kind_dir: layouts`, `id_key: layout_id` fixed; never ask for the kind again. Output: `templates/` (spec plus prototypes), optional `images/` and `icons/imported/`, conditional `exports/`. Every SVG is a complete preview declaring one root Master and Layout; authored neutral paint stays replaceable downstream; for mirror, first prove the source contract satisfies the complete Layout boundary, then preserve its structure and supported visuals exactly as Create Template allows — removing or replacing identity or application rules is never "mirror".

## 4. Layout Validation

In addition to Create Template Steps 5–6: the spec contains `layout_id`, `kind: layout`, `summary`, canvas fields, `replication_mode`, `native_structure_mode: structured`, `page_count`, `page_types`; `layout_id` matches the library workspace ID; Signature Design Elements and Page Roster exist while Template Overview, application language, and identity sections do not; no `primary_color`, palette, typeface/weight, type-scale, logo, voice, or icon-identity claim (structural text roles and capacity rules may remain); every SVG satisfies the shared Master/Layout/slot contract with a bidirectionally complete roster; neutral paint is not described as identity; `replication_mode: mirror` is rejected for any source retaining organization identity or application rules.

Library scope validates with `register_template.py <layout_id> --kind layout --dry-run` and, after Step 5 and any triggered Step 6, registers with `register_template.py <layout_id> --kind layout`; project scope skips both. The exact root becomes the next Generate Step 3 input; identity remains a Strategist decision unless an explicit Brand or Deck workspace is also supplied.
