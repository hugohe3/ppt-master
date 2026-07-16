---
description: Create Deck child workflow for a complete reusable identity-and-structure workspace.
---

# Create Deck Workflow

Enter this child workflow only after [`Create Template`](../create-template.md) dispatches `kind: deck`.

## Responsibility Boundary

| Owner | Responsibilities |
|---|---|
| Create Template | Child-workflow dispatch plus the shared source taxonomy, `library` / `project` scope, confirmation gate, collision preflight, structured authoring contract, validation commands, registration, completion, and Generate PPTX handoff |
| Create Deck | Integrated identity-and-structure interpretation, deck-specific brief fields, complete `design_spec.md`, SVG roster, and deck-specific validation |

**Hard rule — child workflow, not a top-level route**: Create Deck executes only inside Create Template. It reuses the parent workflow's Steps 1–8 and never creates a competing entry route or second confirmation gate.

**Hard rule — complete reusable system**: A deck owns the identity segment, the structure segment, and the deck-only Template Overview. It is a reusable template workspace, not the user's finished content deck.

## Invocation Points

1. Use §1–2 below while executing Create Template Steps 1–3.
2. After Create Template Step 4 preflights `<template_workspace>`, use §3 to author or materialize the deck workspace under the shared structured contract.
3. Apply §4 in addition to Create Template Step 5, then continue through shared Steps 6–8.

## 1. Deck Input Interpretation

Use Create Template Step 1 for source ingestion and replication-mode eligibility. Interpret source evidence across both segments:

- Identity: color, typography, logo, visual voice, and icon style, with fact/suggestion provenance preserved in the brief.
- Structure: canvas, page grammar, Master/Layout families, slot geometry, page types, image behavior, and density rhythm.
- Middle: use cases, design intent, presentation rhythm, and other deck-specific overview context.
- `standard` and `fidelity` author a new complete system; source topology is not output topology. `mirror` preserves only validated package/contract facts in a new workspace and never modifies the source.

Direct conversation text, pasted requirements, converted documents/websites, images, and supplied assets are first-class evidence under Create Template Step 1. In a mixed bundle, combine the applicable identity, structure, and middle evidence without erasing provenance. Exact user instructions remain decisions; vague prose remains suggested interpretation until the shared confirmation gate.

Create Deck is the default child when identity and structure are both requested or when the source is a specific organization's branded presentation system. If the user explicitly wants identity-only or brand-neutral structure, return to Create Template dispatch before the shared confirmation marker is emitted.

## 2. Deck Brief and Schema

Add these child-owned requirements to Create Template Step 2:

| Field | Requirement |
|---|---|
| Deck ID and display name | Required; `deck_id` is a filesystem-safe ASCII slug |
| Use cases and design intent | Required; becomes the Template Overview |
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
summary: <one-line use case and tone>
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

- `templates/design_spec.md` contains `deck_id`, `kind: deck`, `summary`, `primary_color`, canvas fields, `replication_mode`, `native_structure_mode: structured`, and `page_count`.
- `deck_id` matches the confirmed workspace ID in library scope.
- Template Overview, Color Scheme, Signature Design Elements, and Page Roster exist; conditional sections match real choices/assets.
- Every identity color is `#RRGGBB`; the primary table row matches frontmatter, and SVG paint follows the confirmed identity.
- Every SVG in the roster satisfies the shared Master/Layout/slot contract and the roster is bidirectionally complete.
- Every referenced image/icon exists under the same workspace and no empty optional directory was created.

For library scope, Create Template validates and registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <deck_id> --kind deck --dry-run
python3 skills/ppt-master/scripts/register_template.py <deck_id> --kind deck
```

For project scope, skip both commands. The exact workspace root becomes the next Generate PPTX Step 3 input; any separately supplied Brand or Layout workspace overrides the corresponding complete segment downstream without mutating this deck workspace.
