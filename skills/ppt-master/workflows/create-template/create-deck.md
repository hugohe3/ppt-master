---
description: Create Deck child workflow for a recurring presentation application with integrated identity and structure.
---

# Create Deck Workflow

Enter this child workflow only after [`Create Template`](../create-template.md) dispatches `kind: deck`.

## Responsibility Boundary

| Owner | Responsibilities |
|---|---|
| Create Template | Child-workflow dispatch plus the shared source taxonomy, `library` / `project` scope, confirmation gate, collision preflight, structured authoring contract, validation commands, registration, completion, and Generate PPTX handoff |
| Create Deck | Recurring-application interpretation, integrated identity/structure, complete `design_spec.md`, SVG roster, and deck-specific validation |

**Hard rule — child workflow, not a top-level route**: Create Deck executes only inside Create Template. It reuses the parent workflow's Steps 1–8 and never creates a competing entry route or second confirmation gate.

**Hard rule — recurring application**: A deck owns an application contract together with integrated identity and structure. The contract states the recurring presentation family, intended audiences/outcomes, delivery/reading assumptions, stable narrative/page roles, and content reuse boundary. It is a reusable template workspace, not the user's finished content deck.

## Invocation Points

1. Use §1–2 below while executing Create Template Steps 1–3.
2. After Create Template Step 4 preflights `<template_workspace>`, use §3 to author or materialize the deck workspace under the shared structured contract.
3. Apply §4 in addition to Create Template Step 5, then continue through shared Steps 6–8.

## 1. Deck Input Interpretation

Use Create Template Step 1 for source ingestion and replication-mode eligibility. Interpret source evidence across all three segments:

- Identity: color, typography, logo, visual voice, and icon style, with fact/suggestion provenance preserved in the brief.
- Structure: canvas, page grammar, Master/Layout families, slot geometry, semantic text roles, alignment/wrapping/capacity behavior, page types, image behavior, and density rhythm.
- Application: recurring situations, intended audiences/outcomes, delivery or reading assumptions, stable narrative/page roles, and the boundary between fixed, replaceable, optional, and example-only content.
- `standard` and `fidelity` author a new complete system; source topology is not output topology. `mirror` preserves only validated package/contract facts in a new workspace and never modifies the source.

Direct conversation text, pasted requirements, converted documents/websites, images, and supplied assets are first-class evidence under Create Template Step 1. In a mixed bundle, combine the applicable identity, structure, and application evidence without erasing provenance. Exact user-authored instructions remain decisions whether they arrive in chat or a user-written brief file; vague prose remains suggested interpretation until the shared confirmation gate.

Create Deck is selected when identity and structure must travel together, when the source is a specific organization's branded presentation system, or when reusable scenario/content semantics are requested. A complete PPTX source alone does not make the output a Deck. If only identity is stable, use Create Brand; if the reusable structure is brand-neutral and the communication application remains downstream-defined, use Create Layout. Return to Create Template dispatch before the shared confirmation marker is emitted when the evidence supports a different kind.

## 2. Deck Brief and Schema

Add these child-owned requirements to Create Template Step 2:

| Field | Requirement |
|---|---|
| Deck ID and display name | Required; `deck_id` is a filesystem-safe ASCII slug |
| Recurring presentation family | Required; identify the repeatable situations this Deck serves rather than listing every plausible use |
| Intended audiences and outcomes | Required; state who the recurring users/recipients are and what the presentation should enable |
| Delivery and reading assumptions | Required; state whether the family is usually presented, closely read, handed off, or used in a mixed way |
| Stable narrative/page roles | Required; identify roles that must or may recur without forcing one page count/order |
| Content reuse boundary | Required; distinguish fixed, replaceable, optional, and example-only starting content |
| Identity | Required; primary color plus supported palette, typography, logo policy, visual voice, and icon style |
| Canvas and page grammar | Required; exact canvas, page types, variants, grids, zones, density rhythm, and image behavior |
| Native structure | Required; Master families, Layout ownership, slot vocabulary, and zero-slot Layouts where intentional |
| Replication mode | Required; `standard`, eligible `fidelity`, or eligible `mirror` under Create Template Step 1 |
| Adopted assets | Optional; list included and excluded candidates with reasons |

Write this complete schema:

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

Omit Typography only when the shared default is intentionally used. Omit Assets and Placeholder Overrides when none exist. Do not restate generic SVG constraints, layout libraries, font-ratio bands, or the canonical placeholder table.

Write Template Overview as the application contract. In Page Roster, add one
content-policy statement per prototype: supported narrative role,
required/optional/repeatable status, and which visible content is fixed,
replaceable, or example-only. These policies guide downstream selection but do
not force future decks to retain the template page count or order.

## 3. Author or Materialize the Deck

Follow Create Template Step 4 and the shared Template_Designer contract with `kind: deck`, `kind_dir: decks`, and `id_key: deck_id` fixed. Do not ask the user to choose the kind again.

The output is:

```text
<template_workspace>/
├── templates/        # design_spec.md + SVG prototypes
├── images/           # optional adopted bitmaps
├── icons/
│   └── imported/     # optional imported vectors
└── exports/          # conditional review evidence
```

Every SVG is a complete preview and declares one root Master and Layout under the shared structured contract. The deck's SVG paint, typography, and adopted assets must agree with its identity segment. Every additional authored Master represents a distinct reusable design family, not one Layout or an organizational duplicate.

## 4. Deck Validation

In addition to Create Template Steps 5–6, verify:

- `templates/design_spec.md` contains `deck_id`, `kind: deck`, `summary`, `primary_color`, canvas fields, `replication_mode`, `native_structure_mode: structured`, and `page_count`; `summary` names the recurring presentation family/outcome rather than only visual tone.
- `deck_id` matches the confirmed workspace ID in library scope.
- Template Overview, Color Scheme, Signature Design Elements, and Page Roster exist; Template Overview covers every application-contract field, every roster row states its content policy, and conditional sections match real choices/assets.
- Every identity color is `#RRGGBB`; the primary table row matches frontmatter, and SVG paint follows the confirmed identity.
- Every SVG in the roster satisfies the shared Master/Layout/slot contract and the roster is bidirectionally complete.
- Every referenced image/icon exists under the same workspace; this workflow created no optional directory solely to leave it empty. Pre-existing initialized-project scaffolding is allowed and remains untouched.

For library scope, Create Template validates and registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <deck_id> --kind deck --dry-run
python3 skills/ppt-master/scripts/register_template.py <deck_id> --kind deck
```

For project scope, skip both commands. The exact workspace root becomes the next Generate PPTX Step 3 input; any separately supplied Brand or Layout workspace overrides the corresponding complete segment downstream without mutating this deck workspace.
