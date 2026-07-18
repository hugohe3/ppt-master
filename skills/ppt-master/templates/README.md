# Template Resources

## Reusable template kinds

Brand, Layout, and Deck are independent template kinds, not stages of one
inheritance hierarchy.

| Kind | Owns | Does not own | Discovery index |
|---|---|---|---|
| [`brands/`](./brands/) | Identity: color, typography, logo, voice, icon style | Page structure or SVG roster | [`brands_index.json`](./brands/brands_index.json) |
| [`layouts/`](./layouts/) | Brand-neutral structure: canvas, Master/Layout graph, page types, slots, SVG roster | Brand identity or a recurring communication application | [`layouts_index.json`](./layouts/layouts_index.json) |
| [`decks/`](./decks/) | A recurring presentation family: application contract + integrated identity + structure | — | [`decks_index.json`](./decks/decks_index.json) |

A brand is not “a layout minus its pages”: it owns a different segment. Use a
brand for identity with free page composition, a layout for brand-neutral
structure whose identity and communication purpose remain downstream
decisions, and a deck for a recurring presentation family with an explicit
application contract.

PowerPoint package objects are compilation targets, not additional template
kinds. Theme values and identity assets are projected from resolved identity
rules supplied by Brand, Deck, or the current project; Layout rules project
into Master/Layout/Placeholder topology, semantic text roles, and
spatial behavior; Deck combines both with purpose-specific starting content
and usage rules. Downstream `layout` scope resolves final placeholder formatting
with the confirmed identity, reading mode, and type scale; `mirror` preserves
literal source formatting. A compiled Slide Master may therefore contain both
structural geometry and brand visuals even though their source rules remain
separately owned.

New workspaces always enter [`Create Template`](../workflows/create-template.md),
which keeps the fixed route name and dispatches exactly one child workflow:
[`Create Brand`](../workflows/create-template/create-brand.md),
[`Create Layout`](../workflows/create-template/create-layout.md), or
[`Create Deck`](../workflows/create-template/create-deck.md).

The indexes are discovery aids only. [`generate-pptx`](../workflows/generate-pptx.md)
Step 3 activates a template only from an explicit workspace-root path supplied
by the user or an exact validated Create Template handoff.

## Orthogonal contracts

| Axis | Values | Meaning |
|---|---|---|
| Template kind | `brand` / `layout` / `deck` | Which reusable contract the package owns: identity, brand-neutral structure, or a complete recurring application |
| Creation mode | `standard` / `fidelity` / `mirror` | Create Layout/Create Deck only: newly author a compact or broad roster, or materialize validated source-package facts into a new workspace; Layout mirror additionally requires a source contract already inside the brand-neutral, application-neutral Layout boundary; Create Brand is N/A |
| Downstream adherence | `strict` / `adaptive` | Preserve the selected Layout contract, or allow explicit new Layout identities |
| PPTX structure | `flat` / `structured` | Free-design, brand-only, and confirmed `style` stay Slide-local; confirmed `mirror` / `layout` compile declared Masters and Layouts |

These axes must not be used as synonyms. In particular, a mirror-created deck
is still an ordinary reusable `deck` package after creation; it does not force
future presentations to keep the source page count or order.

## Workspace contract

Every package uses the same portable root under either this library or an
initialized project:

```text
<template_workspace>/
├── templates/                # design_spec.md, SVG prototypes, optional native_payloads.json.gz store
├── images/                   # optional bitmaps
├── icons/
│   └── imported/             # optional imported vectors, one canonical copy
└── exports/                  # optional review evidence; never a template input
```

Empty optional directories are omitted. Template SVGs reference bitmaps through
`../images/<name>` and imported vectors through `data-icon="imported/<name>"`.
The conditional [`apply-template-workspace`](../workflows/stages/apply-template-workspace.md)
stage owns installation and fusion: it consumes `templates/`, `images/`, and
`icons/` and ignores `exports/`. Compatible legacy-flat packages remain
readable; directory shape alone does not indicate legacy Master/Layout semantics.

## Design specification references

[`design_spec_reference.md`](./design_spec_reference.md) is the project-level
Strategist reference for the generated presentation's full specification and
content outline. Reusable template `design_spec.md` files are deliberately
smaller: they contain portable metadata and only the identity, structure, or
application rules owned by that package. General SVG/PPT rules remain
centralized in
[`shared-standards.md`](../references/shared-standards.md).

## Visualization Templates

The `charts/` directory contains 57 standardized visualization templates. For backward compatibility, the directory name remains `charts/`, but its scope includes charts, infographics, process diagrams, relationship diagrams, strategic frameworks, and system architecture diagrams:

- KPI Cards
- Bar Chart / Stacked Bar Chart
- Line Chart / Dual-Axis Line Chart
- Donut Chart
- Radar Chart
- Funnel Chart
- Matrix (2x2)
- Timeline
- Gantt Chart
- Process Flow
- Org Chart
- Layered Architecture / Module Composition / Hub with Described Spokes / Pipeline with Stages / Client-Server Flow

- **Library index (single source of truth)**: [charts/charts_index.json](./charts/charts_index.json)
- **Directory overview**: [charts/README.md](./charts/README.md)

## Icon Library

The `icons/` directory contains 11,600+ vector icons across five libraries:

| Library | Style | Count |
|---------|-------|-------|
| `chunk-filled` | fill / straight-line geometry | 640 |
| `tabler-filled` | fill / bezier-curve forms | 1000+ |
| `tabler-outline` | stroke / line | 5000+ |
| `phosphor-duotone` | duotone / single color + 0.2 opacity backplate | 1200+ |
| `simple-icons` | brand logos (company / product marks) | 3400+ |

- **Usage & style rules**: [icons/README.md](./icons/README.md)
- **Search icons**: `rg --files skills/ppt-master/templates/icons/<library>/ | rg <keyword>`
