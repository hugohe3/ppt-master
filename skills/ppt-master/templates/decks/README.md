# Deck Templates

**Deck = a reusable solution for a recurring presentation family**: descriptive application context (which situations it serves, which outcomes it supports, which narrative/page roles commonly appear) together with presentation identity and reusable structure. It describes the resource without deciding which pages or content a future presentation must keep; a deck template is not a finished content deck, and `kind: deck` does not mean "mirror the source PPT" — the creation strategy decides whether the system is newly authored or materialized from validated facts. The shared kind and workspace model lives in the parent [`README.md`](../README.md).

| Axis | Deck behavior |
|---|---|
| Template kind | `deck`: application context + integrated identity + structure |
| Internal creation strategy | AI-derived `standard` / `fidelity` for a new system or `mirror` for validated source materialization; tool provenance, not a user choice |
| Application planning | Strategist decides which prototypes to select, repeat, skip, or reorganize and derives the exporter behavior |
| PPTX structure | The workspace is `structured`; the plan decides whether pages compile its structure or use it as visual reference |

[`decks_index.json`](./decks_index.json) (`deck_id → { summary, canvas_format, page_count, primary_color }`) is the discovery source of truth; this README enumerates no decks. Index summaries lead with the presentation family and outcome — visual tone alone never selects a Deck; open its Template Overview to judge fit.

## Selection and installation

Selection follows the parent contract: Deck choices come only from the index (no directory scan or bare-ID/style-phrase match); a supplied exact root joins the selector and is preselected only when sole; [`apply-template-workspace`](../../workflows/stages/apply-template-workspace.md) installs it before Stage 2; Quick applies a supplied exact root directly and authors the installed Master/Layout/slot contract as lockless structured Slides unless the user explicitly requests visual-only flat use.

## `design_spec.md` contract

Portable metadata plus package-owned application, identity, and structure rules; no generic SVG rules, spacing libraries, font-ratio bands, or the canonical placeholder table.

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

`replication_mode` records how the workspace was produced. `Template Overview` is descriptive application context — family, intended audiences/outcomes, delivery/reading assumptions, representative roles — broad when the source supports related uses yet specific enough to help Strategist understand the resource. `Page Roster` lists every SVG with its Master/Layout identity, role, visual character, reusable slots, and capacity, never marking pages required/optional/repeatable or content fixed/replaceable/example-only. Every additional authored Master is a distinct reusable design family.

## Structured SVG contract

Every SVG is a complete preview declaring one root Master and Layout; fixed visuals are direct atoms; reusable regions are top-level slot groups with positive bounds and exactly one compatible carrier; zero-slot Layouts are valid; `{{...}}` is the authoring vocabulary and `data-pptx-placeholder*` the native contract. `standard` / `fidelity` author new SVGs and structure; `mirror` preserves source identities, parentage, assignments, placeholder facts, and supported visuals without synthesis; legacy contracts are never upgraded in place, and a flat directory shape alone is not a legacy signal.

## Workspace and creation

`templates/` (spec + prototypes), optional `images/` (`../images/<name>`), optional `icons/imported/`, and `exports/<deck_id>_template_preview.pptx` as review evidence. Library scope writes `skills/ppt-master/templates/decks/<deck_id>/` and updates the index; project scope uses an initialized `projects/<name>/` root without registration. Enter [`create-template.md`](../../workflows/create-template.md) (dispatching to [`create-deck.md`](../../workflows/create-template/create-deck.md)), validate with `svg_quality_checker.py --template-mode`, run `template_preview_pptx.py` on request and always for multiple Masters, and in library scope register with `register_template.py <id> --kind deck`. See [`styles/`](../styles/), [`layouts/`](../layouts/), and [`brands/`](../brands/) for the other kinds.
