# Brand Identity Presets

**Brand-only templates**: identity bundles (color / typography / logo / voice / icon style) without an SVG roster. Strategist locks the identity segment as truth; Executor composes pages freely under it. Brand is one of four kinds alongside [`styles/`](../styles/), [`layouts/`](../layouts/), and [`decks/`](../decks/); the shared kind and workspace model lives in the parent [`README.md`](../README.md).

## How brands are consumed

Selection follows the parent contract: Brand choices come only from `brands_index.json` (no directory scan or bare-name match); a supplied exact root joins the same selector, defaults Stage 1 to template mode, and is preselected only when it is the sole root; [`apply-template-workspace`](../../workflows/stages/apply-template-workspace.md) installs it before Stage 2; Quick applies a supplied exact root directly. This file owns only the Brand schema.

## Creating a new brand

Enter [`create-template.md`](../../workflows/create-template.md), which dispatches `kind: brand` to [`create-brand.md`](../../workflows/create-template/create-brand.md), from a brand asset (logo / site / branded PPTX / PDF), a verbal spec, or an explicitly requested empty skeleton.

```text
templates/brands/<brand_id>/
├── templates/design_spec.md   # required — identity spec with YAML frontmatter `kind: brand`
├── images/                    # optional — logo.<ext>, alternate lockups, visual assets
├── icons/                     # optional — branded icon overrides
└── exports/                   # normally absent; Git-ignored derived artifacts only
```

Logo filenames are descriptive; `design_spec.md` §IV lists the exact `../images/...` paths and usage. The six required sections are I Brand Overview / II Color Scheme / III Typography / IV Logo / V Voice & Tone / VI Icon Style; omit empty optional directories.

## Discovery index

[brands_index.json](./brands_index.json) maps `brand_id → { summary, primary_color }`; refresh with `register_template.py <brand_id> --kind brand`, which rejects incomplete frontmatter, mismatched IDs, page SVGs, missing identity sections, invalid colors/provenance, and broken asset references. Stage-1 controls and chat discovery read this index only; a bare ID never resolves implicitly.
