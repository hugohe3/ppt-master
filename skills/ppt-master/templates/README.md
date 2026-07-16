# Template Resources

## Reusable template kinds

Brand, Layout, and Deck are independent template kinds, not stages of one
inheritance hierarchy.

| Kind | Owns | Does not own | Discovery index |
|---|---|---|---|
| [`brands/`](./brands/) | Identity: color, typography, logo, voice, icon style | Page structure or SVG roster | [`brands_index.json`](./brands/brands_index.json) |
| [`layouts/`](./layouts/) | Structure: canvas, Master/Layout graph, page types, slots, SVG roster | Brand identity | [`layouts_index.json`](./layouts/layouts_index.json) |
| [`decks/`](./decks/) | Complete identity + structure reference | — | [`decks_index.json`](./decks/decks_index.json) |

A brand is not “a layout minus its pages”: it owns a different segment. Use a
brand for identity with free page composition, a layout for fixed reusable
structure with downstream identity, and a deck for a coherent complete system.

New workspaces always enter [`Create Template`](../workflows/create-template.md),
which keeps the fixed route name and dispatches exactly one child workflow:
[`Create Brand`](../workflows/create-template/create-brand.md),
[`Create Layout`](../workflows/create-template/create-layout.md), or
[`Create Deck`](../workflows/create-template/create-deck.md).

The indexes are discovery aids only. Step 3 activates a template only from an
explicit workspace-root path supplied by the user.

## Orthogonal contracts

| Axis | Values | Meaning |
|---|---|---|
| Template kind | `brand` / `layout` / `deck` | Which design segments the package owns |
| Creation mode | `standard` / `fidelity` / `mirror` | Create Layout/Create Deck only: newly author a compact or broad roster, or materialize validated source-package facts into a new workspace; Create Brand is N/A |
| Downstream adherence | `strict` / `adaptive` | Preserve the selected Layout contract, or allow explicit new Layout identities |
| PPTX structure | `flat` / `structured` | Free-design/brand-only content stays Slide-local; layout/deck routes compile declared Masters and Layouts |

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
Step 3 consumes `templates/`, `images/`, and `icons/` and ignores `exports/`.
Compatible legacy-flat packages remain readable; directory shape alone does not
indicate legacy Master/Layout semantics.

## Design specification references

[`design_spec_reference.md`](./design_spec_reference.md) is the project-level
Strategist reference for the generated presentation's full specification and
content outline. Reusable template `design_spec.md` files are deliberately
smaller: they contain portable metadata and only the personality or structure
that distinguishes that package. General SVG/PPT rules remain centralized in
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
