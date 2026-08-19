# Template Resources

## Reusable template kinds

Brand, Style, Layout, and Deck are independent template kinds, not stages of one
inheritance hierarchy.

| Kind | Owns | Does not own | Discovery index |
|---|---|---|---|
| [`brands/`](./brands/) | Identity: color, typography, logo, voice, icon style | Page structure or SVG roster | [`brands_index.json`](./brands/brands_index.json) |
| [`styles/`](./styles/) | Direction/method: reusable communication method, visual language, composition rhythm, and information-expression defaults | Official brand identity, current-project application, page structure, or SVG roster | [`styles_index.json`](./styles/styles_index.json) |
| [`layouts/`](./layouts/) | Brand-neutral structure: canvas, Master/Layout graph, page types, slots, SVG roster | Brand identity or a recurring communication application | [`layouts_index.json`](./layouts/layouts_index.json) |
| [`decks/`](./decks/) | A recurring presentation family: application contract + integrated identity + structure | — | [`decks_index.json`](./decks/decks_index.json) |

A brand is not “a layout minus its pages”, and a Style is not a roster-free
Deck: each owns a different segment. Use a brand for identity with free page
composition, a Style for reusable direction/method without identity truth or
page prototypes, a layout for brand-neutral structure whose identity and
communication purpose remain downstream decisions, and a deck for a recurring
presentation family with an explicit application contract.

PowerPoint package objects are compilation targets, not additional template
kinds. Theme values and identity assets are projected from resolved identity
rules supplied by Brand, Deck, or the current project; Layout rules project
into Master/Layout/Placeholder topology, semantic text roles, and
spatial behavior; Deck combines both with descriptive recurring-application
context and actual prototype examples. Style rules guide communication method,
visual language, composition, and information expression; they do not create a
PowerPoint package object or override resolved Brand/Deck identity. Downstream AI planning decides which
prototypes and content to use, then records the required exporter values.
A compiled Slide Master may therefore contain both
structural geometry and brand visuals even though their source rules remain
separately owned.

New workspaces always enter [`Create Template`](../workflows/create-template.md),
which keeps the fixed route name and dispatches exactly one child workflow:
[`Create Brand`](../workflows/create-template/create-brand.md),
[`Create Style`](../workflows/create-template/create-style.md),
[`Create Layout`](../workflows/create-template/create-layout.md), or
[`Create Deck`](../workflows/create-template/create-deck.md).

The four indexes are the complete library-discovery source for Default
[`generate-pptx`](../workflows/generate-pptx.md) Stage-1 template selection.
Step 3 prepares candidate input without interaction or reading template
content. The Stage-1 page confirms the communication contract together with an
explicit free-design/template choice; only template mode expands these indexes.
Exact roots supplied for the run or handed off by Create Template appear as
specified candidates. Ordinary requests default to free design; explicit
template intent or any supplied root defaults to template mode. Exactly one root
may be preselected, while multiple roots remain unselected candidates. The user
can always switch modes. The page accepts one registered choice per kind plus
one supplied-root choice. A registered exact root is `library`; any other exact
root is `explicit`. After that combined confirmation,
[`apply-template-workspace`](../workflows/stages/apply-template-workspace.md)
validates and installs every selected workspace into the current
project as its own `design_spec.<kind>.<id>.md` before Stage 2 starts. Template-aware reading begins in final Stage 2 from
that project-local copy. Quick skips the page, applies supplied exact roots, and
otherwise uses free design.

## Orthogonal contracts

| Axis | Values | Meaning |
|---|---|---|
| Template kind | `brand` / `style` / `layout` / `deck` | Which reusable contract the package owns: identity, direction/method, brand-neutral structure, or a complete recurring application |
| Selection source | `library` / `explicit` | Step-3 discovery provenance only: exact index-derived root or exact unregistered root; it does not change template semantics |
| Internal creation strategy | `standard` / `fidelity` / `mirror` | AI-derived Create Layout/Create Deck implementation: newly author a compact or broad roster, or materialize validated source-package facts into a new workspace; persisted for tools, never presented as a required user choice |
| Internal application plan | `template_reuse_scope` plus optional `template_adherence` | Strategist derives literal, structural, or style-only use and any strict/adaptive exporter behavior after inspecting the installed template and current content |
| PPTX structure | `flat` / `structured` | Derived application plans that use template structure compile declared Masters and Layouts; Style-only, style-scope, brand-only, and free design remain Slide-local. A Style installed alongside Layout/Deck does not change the non-Style structure plan. |

These axes must not be used as synonyms or exposed as a user mode matrix. In
particular, a mirror-created deck is still an ordinary reusable `deck` package
after creation; it does not force future presentations to keep the source page
count or order.

## Workspace contract

Every package uses the same portable root under either this library or an
initialized project:

```text
<template_workspace>/
├── templates/                # design_spec.md; optional Layout/Deck SVG prototypes and native_payloads.json.gz store
├── images/                   # optional bitmaps
├── icons/
│   └── imported/             # optional imported vectors, one canonical copy
└── exports/                  # optional review evidence; never a template input
```

Empty optional directories are omitted. Template SVGs reference bitmaps through
`../images/<name>` and imported vectors through `data-icon="imported/<name>"`.
Style narrows this shared routing shape to `templates/design_spec.md` only and
does not carry asset or review payloads; initialized-project sibling scaffolding
may exist but is not Style input.
The conditional [`apply-template-workspace`](../workflows/stages/apply-template-workspace.md)
stage owns installation after a non-free Default Stage-1 selection or
on the Quick exact-root branch. Brand/Layout/Deck consume package-owned
`templates/`, `images/`, and `icons/`; Style consumes only
`templates/design_spec.md` and ignores sibling project scaffolding. Every kind
ignores `exports/`. Compatible legacy-flat Brand/Layout/Deck packages remain
readable; Style has no legacy-flat form, and directory shape alone does not
indicate legacy Master/Layout semantics. Default Strategist, Quick's current
agent, and all later consumers use the installed project-local files, never the
original library or explicit root.

## Design specification references

[`design_spec_reference.md`](./design_spec_reference.md) and
[`spec_lock_reference.md`](./spec_lock_reference.md) own normal whole-document
authoring; their schemas own machine validation. Files under `scaffolds/` are
optional overwrite-safe CLI conveniences, not Generate-route starting artifacts.
Reusable template `design_spec.md` files are
deliberately smaller: they contain portable metadata and only the identity,
direction/method, structure, or application rules owned by that package. General SVG rules live
in [`shared-standards-core.md`](../references/shared-standards-core.md), with
effects and PowerPoint interfaces loaded only when triggered.

## Visualization Templates

Page-local Shape-first references are catalog families, not reusable template
kinds:

| Family | Owns | Planning map | Machine index |
|---|---|---|---|
| Chart | Value-driven geometry (33) | [`chart-vocabulary.md`](./charts/chart-vocabulary.md) | [`charts_index.json`](./charts/charts_index.json) |
| Table | Row × column fact grid (6) | [`table-vocabulary.md`](./tables/table-vocabulary.md) | [`tables_index.json`](./tables/tables_index.json) |

[`VISUALIZATION_TEMPLATE_AUTHORING.md`](./VISUALIZATION_TEMPLATE_AUTHORING.md)
is the shared authoring contract. Each machine index owns family membership;
the Chart and Table vocabularies are their complete objective planning
projections.

Qualitative Structure is a Slide-local Executor method rather than a catalog:
Default and Quick both derive its relationship model and compose shapes for the
current page. Only [`layouts/`](./layouts/) owns reusable Master/Layout, page
types, slots, and placeholders.

## Icon Library

The `icons/` directory contains 12,027 vector icons across five libraries:

| Library | Style | Count |
|---------|-------|-------|
| `chunk-filled` | fill / compact, chunky 16px silhouettes | 641 |
| `tabler-filled` | fill / bezier-curve forms | 1,055 |
| `tabler-outline` | stroke / line | 5,138 |
| `phosphor-duotone` | duotone / single color + 0.2 opacity backplate | 1,518 |
| `simple-icons` | brand logos (company / product marks) | 3,675 |

- **Usage & style rules**: [icons/README.md](./icons/README.md)
- **Versions, licenses & attribution**: [icons/THIRD_PARTY_NOTICES.md](./icons/THIRD_PARTY_NOTICES.md)
- **Search icons**: `rg --files skills/ppt-master/templates/icons/<library>/ | rg <keyword>`

## Sound Library

[`sounds/`](./sounds/) is a post-motion selection resource, not a template or
Strategist resource. Its complete
[cue vocabulary](./sounds/sound-vocabulary.md) is read only after a concrete
auditory job exists; sync selected cues only. See [usage](./sounds/README.md).
