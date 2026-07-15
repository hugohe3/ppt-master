# Template Resources

## Design Specification & Outline Reference

`design_spec_reference.md` is an all-in-one reference template for defining:
1.  **Visual Specifications**: Canvas dimensions, color scheme, typography, layout principles
2.  **Content Outline**: Slide-by-slide page structure planning
3.  **Technical Constraints**: Hard requirements for SVG generation and PPT compatibility

[View Design Spec Reference](./design_spec_reference.md)

## Page Layout Templates

The `layouts/` directory contains pre-built page layout templates organized by design style:

- **General**: Versatile modern style, clean and flexible
- **Consultant**: Consulting style, professional and structured
- **Consultant Top**: Top-tier consulting style (MBB-level)
- **Academic Defense**: Academic defense style, research-oriented

- **Human browsing**: [layouts/README.md](./layouts/README.md)
- **Slim lookup (discovery only)**: [layouts/layouts_index.json](./layouts/layouts_index.json) — used to answer "what templates exist?". Step 3 triggers on an explicit directory path supplied by the user, not on names from this index.

Every brand/layout/deck package uses one workspace routing contract. Whether created under this library or under `projects/`, source files live in `templates/`, bitmaps in `images/`, imported vectors live once in `icons/imported/`, and on-demand review files live in `exports/`. Other icon-library namespaces remain under `icons/` only when explicitly adopted. Empty optional directories are omitted, so a normal checked-in workspace has no `exports/`. Library `exports/` directories are Git-ignored, and Step 3 never copies them. Existing flat packages remain readable; flat placement alone does not imply legacy Master/Layout metadata.

## Brand Identity Presets

The `brands/` directory holds brand-only templates: identity bundles (color / typography / logo / voice / icon style) without an SVG page roster. Brands follow the **same explicit-path trigger and workspace routing as layout templates** — at SKILL.md Step 3 the user supplies the workspace root; bare brand names never trigger. `templates/`, `images/`, and `icons/` map to their matching project peers. When supplied together, Step 3 fuses them into one `design_spec.md` (brand wins on identity tokens, layout wins on page structure) — see `SKILL.md` Step 3 for the precedence table.

A brand is structurally a layout template minus its page roster. Use a brand when the user wants identity locking with free page layout; use a layout template when fixed page structures are also required.

- **Human browsing**: [brands/README.md](./brands/README.md)
- **Discovery index (no trigger)**: [brands/brands_index.json](./brands/brands_index.json) — answers "what brands exist?"; Step 3 still requires an explicit directory path from the user
- **Creation workflow**: [`../workflows/create-brand.md`](../workflows/create-brand.md)

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
- **Search icons**: `ls skills/ppt-master/templates/icons/<library>/ | grep <keyword>`
