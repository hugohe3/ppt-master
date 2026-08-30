# Template Resources

## Reusable template kinds

Brand, Style, Layout, and Deck are independent kinds, not stages of one inheritance hierarchy — each owns a different segment.

| Kind | Owns | Does not own | Discovery index |
|---|---|---|---|
| [`brands/`](./brands/) | Identity: color, typography, logo, voice, icon style | Page structure or SVG roster | [`brands_index.json`](./brands/brands_index.json) |
| [`styles/`](./styles/) | Direction/method: communication method, visual language, composition rhythm, information-expression defaults | Official identity, current-project application, structure, or roster | [`styles_index.json`](./styles/styles_index.json) |
| [`layouts/`](./layouts/) | Brand-neutral structure: canvas, Master/Layout graph, page types, slots, SVG roster | Identity or a recurring application | [`layouts_index.json`](./layouts/layouts_index.json) |
| [`decks/`](./decks/) | A recurring presentation family: application context + integrated identity + structure | — | [`decks_index.json`](./decks/decks_index.json) |

PowerPoint package objects are compilation targets, not kinds: Theme values and identity assets project from resolved identity rules (Brand, Deck, or the current project); Layout rules project into Master/Layout/Placeholder topology, semantic text roles, and spatial behavior; Deck combines both with descriptive application context and actual prototypes; Style guides method and expression without creating a package object or overriding resolved identity. Downstream planning decides which prototypes and content to use and records the exporter values, so one compiled Master may hold both structural geometry and brand visuals under separately owned rules.

New workspaces enter [`Create Template`](../workflows/create-template.md), which dispatches exactly one child ([`Create Brand`](../workflows/create-template/create-brand.md), [`Create Style`](../workflows/create-template/create-style.md), [`Create Layout`](../workflows/create-template/create-layout.md), [`Create Deck`](../workflows/create-template/create-deck.md)). Selection, mode defaults, preselection, `library` / `explicit` labels, cardinality, and installation are owned by [`routing.md`](../workflows/routing.md) §7 and [`apply-template-workspace`](../workflows/stages/apply-template-workspace.md): the four indexes are the complete library discovery source for Default Stage 1, every selected root is installed as `design_spec.<kind>.<id>.md` before Stage 2, and Quick applies supplied exact roots directly.

## Orthogonal contracts

| Axis | Values | Meaning |
|---|---|---|
| Template kind | `brand` / `style` / `layout` / `deck` | Which reusable contract the package owns |
| Selection source | `library` / `explicit` | Discovery provenance only (index-derived root vs exact unregistered root); no semantic effect |
| Internal creation strategy | `standard` / `fidelity` / `mirror` | AI-derived Create Layout/Deck implementation (author a compact or broad roster, or materialize validated source facts); persisted for tools, never a user choice |
| Internal application plan | `template_reuse_scope` plus optional `template_adherence` | Strategist-derived literal, structural, or style-only use and strict/adaptive exporter behavior |
| PPTX structure | `flat` / `structured` | Plans using template structure compile declared Masters and Layouts; Style-only, style-scope, brand-only, and free design stay Slide-local; a Style beside Layout/Deck never changes the structure plan |

Never use these axes as synonyms or expose them as a mode matrix; a mirror-created deck is an ordinary reusable `deck` and forces no future page count or order.

## Workspace contract

```text
<template_workspace>/
├── templates/     # the Design Spec (naming below); optional Layout/Deck SVGs and native_payloads.json.gz
├── images/        # optional bitmaps; SVG href ../images/<name>
├── icons/imported/   # optional imported vectors, one canonical copy; data-icon="imported/<name>"
└── exports/       # optional review evidence; never a template input
```

**Hard rule — the container disambiguates, the filename carries the rest**: a library root keeps `templates/design_spec.md` (its `<kind_dir>/<template_id>/` names kind and id); a project root shares one flat `templates/` and keeps one `design_spec.<kind>.<id>.md` per kind, with filename kind/id equal to frontmatter `kind` / `<kind>_id`; the shapes never mix. One `templates/` holds one active roster — Layout when present, otherwise Deck — while both specs may coexist because Layout overrides only Deck structure. Either shape is a workspace root, and selecting it takes every kind it exposes. Empty optional directories are omitted; Style contributes only its spec; every kind ignores `exports/`.

## Design specification references

[`design_spec_reference.md`](./design_spec_reference.md) and [`spec_lock_reference.md`](./spec_lock_reference.md) own project-level authoring; their schemas own validation; `scaffolds/` files are optional CLI conveniences. Template specs are deliberately smaller — portable metadata plus only the rules the package owns; general SVG rules live in [`shared-standards-core.md`](../references/shared-standards-core.md).

## Visualization Templates

Page-local Shape-first catalog families, not kinds: Chart — value-driven geometry (33), planning map [`chart-vocabulary.md`](./charts/chart-vocabulary.md), index [`charts_index.json`](./charts/charts_index.json); Table — row × column fact grid (6), [`table-vocabulary.md`](./tables/table-vocabulary.md), [`tables_index.json`](./tables/tables_index.json). [`VISUALIZATION_TEMPLATE_AUTHORING.md`](./VISUALIZATION_TEMPLATE_AUTHORING.md) is the maintainer authoring contract. Qualitative Structure is a Slide-local Executor method, not a catalog; only Layout and Deck own reusable Master/Layout, page types, slots, and placeholders.

## Icon Library

[`icons/`](./icons/) holds 12,027 vectors across five libraries (`chunk-filled` 641, `tabler-filled` 1,055, `tabler-outline` 5,138, `phosphor-duotone` 1,518, `simple-icons` 3,675 brand logos); usage and style rules in [icons/README.md](./icons/README.md), licenses in [icons/THIRD_PARTY_NOTICES.md](./icons/THIRD_PARTY_NOTICES.md).

## Sound Library

[`sounds/`](./sounds/) is a post-motion selection resource, not a template or Strategist resource: read its [cue vocabulary](./sounds/sound-vocabulary.md) only after a concrete auditory job exists and sync selected cues only ([usage](./sounds/README.md)).
