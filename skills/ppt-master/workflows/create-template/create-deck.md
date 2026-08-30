---
description: Create Deck child workflow for a recurring presentation application with integrated identity and structure.
---

# Create Deck Workflow

Enter only after [`Create Template`](../create-template.md) dispatches `kind: deck`. Create Template owns dispatch, the source taxonomy, scope, the confirmation gate, collision preflight, the structured authoring contract, validation commands, registration, completion, and the Generate handoff; Create Deck owns recurring-application interpretation, integrated identity/structure, the complete spec, the SVG roster, and deck validation.

**Hard rule — child workflow, not a top-level route**: executes only inside Create Template Steps 1–8.

**Hard rule — recurring application**: a deck owns descriptive application context (recurring presentation family, intended audiences/outcomes, delivery/reading assumptions, representative narrative/page roles) together with integrated identity and structure. The context helps later planning understand the resource; it never prescribes which prototypes or content a future project must keep, and the workspace is a reusable template, not the user's finished deck.

**Invocation**: §1–2 during Create Template Steps 1–3; after Step 4 preflights the workspace, §3 authors or materializes under the shared structured contract; §4 adds to Step 5, then shared Steps 6–8.

## 1. Deck Input Interpretation

Use Create Template Step 1 for ingestion and strategy feasibility across three segments: identity (color, typography, logo, visual voice, icon style, with provenance); structure (canvas, page grammar, Master/Layout families, slot geometry, text roles, alignment/wrapping/capacity, page types, image behavior, density rhythm); application (recurring situations, audiences/outcomes, delivery assumptions, representative roles, the actual source-page vocabulary — never assigned required/optional/repeatable status or fixed/replaceable/example-only policy). `standard` / `fidelity` author a new complete system (source topology is not output topology); `mirror` preserves only validated package/contract facts in a new workspace; the AI derives the implementation from intent. Direct text, converted documents, images, and assets are first-class evidence; user-authored instructions are decisions in any carrier, vague prose stays suggested until the gate.

Select Create Deck when identity and structure must travel together, the source is one organization's branded presentation system, or reusable scenario/content semantics are requested. A complete PPTX alone does not make a Deck: identity-only → Create Brand; brand-neutral structure with downstream-defined application → Create Layout; return to dispatch before the marker when the evidence supports another kind.

## 2. Deck Brief and Schema

Add to Create Template Step 2 (required unless noted): Deck ID (ASCII slug) and display name; recurring presentation family (repeatable situations, not every plausible use); intended audiences and outcomes; delivery and reading assumptions (presented, closely read, handed off, mixed); representative narrative/page roles (without future inclusion rules); identity (primary color plus palette, typography, logo policy, visual voice, icon style); canvas and page grammar (exact canvas, page types, variants, grids, zones, density, image behavior); native structure (Master families, Layout ownership, slot vocabulary, intentional zero-slot Layouts); creation intent as prose (what stays recognizable, what is rebuilt, whether the source page set is preserved broadly or distilled — `replication_mode` derived internally); adopted assets (optional, with included/excluded reasons).

```markdown
---
deck_id: <confirmed slug>
kind: deck
category: brand | general | scenario | government | special
summary: <one-line recurring presentation family and intended outcome>
keywords: [<three-to-five tags>]
primary_color: "#XXXXXX"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
replication_mode: standard | fidelity | mirror
native_structure_mode: structured
page_count: <N>
---

# <Deck Name> — Design Specification

## I. Template Overview
## II. Color Scheme
## III. Typography
## IV. Signature Design Elements
## V. Page Roster
## VI. Assets
## VII. Placeholder Overrides
```

`replication_mode` is machine provenance. Omit Typography only when the shared default is intentional; omit Assets and Placeholder Overrides when none exist; restate no generic SVG constraints, layout libraries, font-ratio bands, or the canonical placeholder table. Template Overview is descriptive application context; Page Roster describes each prototype's role, visual character, reusable slots, and capacity without status or content policy — downstream Strategist decides what to use.

## 3. Author or Materialize the Deck

Follow Create Template Step 4 and the Template_Designer contract with `kind: deck`, `kind_dir: decks`, `id_key: deck_id` fixed; never ask for the kind again. Output: `templates/` (spec plus prototypes), optional `images/` and `icons/imported/`, conditional `exports/`. Every SVG is a complete preview declaring one root Master and Layout; paint, typography, and adopted assets agree with the identity segment; every additional authored Master is a distinct reusable design family, never one Layout or an organizational duplicate.

## 4. Deck Validation

In addition to Create Template Steps 5–6: the spec contains `deck_id`, `kind: deck`, `summary` (naming the family/outcome, not only visual tone), `primary_color`, canvas fields, `replication_mode`, `native_structure_mode: structured`, `page_count`; `deck_id` matches the library workspace ID; Template Overview, Color Scheme, Signature Design Elements, and Page Roster exist with the Overview descriptive, every roster row factual, and conditional sections matching real choices; every identity color is `#RRGGBB` with the primary row matching frontmatter and SVG paint following the identity; every SVG satisfies the shared Master/Layout/slot contract with a bidirectionally complete roster; every referenced image/icon exists and no empty optional directory was created (pre-existing project scaffolding stays untouched).

Library scope validates with `register_template.py <deck_id> --kind deck --dry-run` and, after Step 5 and any triggered Step 6, registers with `register_template.py <deck_id> --kind deck`; project scope skips both. The exact root becomes the next Generate Step 3 input; a separately supplied Brand, Style, or Layout workspace overrides its complete segment downstream without mutating this deck.
