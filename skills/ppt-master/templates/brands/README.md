# Brand Identity Presets

This directory holds **brand-only templates**: identity bundles (color / typography / logo / voice / icon style) without an SVG page roster. Strategist locks the brand's identity segment as truth; Executor designs pages freely under those constraints.

Brand is one of three template kinds in the library — alongside
[`layouts/`](../layouts/) (brand-neutral structure) and [`decks/`](../decks/)
(a recurring application with integrated identity and structure). The shared
kind and workspace model lives in the parent [`README.md`](../README.md).

## How brands are consumed

Brand application follows the common explicit-path trigger in
[`generate-pptx`](../../workflows/generate-pptx.md) Step 3. The conditional
[`apply-template-workspace`](../../workflows/stages/apply-template-workspace.md)
stage owns path normalization, portable-root installation, multi-kind fusion,
same-kind conflict resolution, and provenance. This file owns only the Brand
schema. `brands_index.json` is discovery-only; listing brands never advances
the pipeline.

## Creating a new brand

Enter the fixed Create Template route, which dispatches the Create Brand child workflow:

```
Read skills/ppt-master/workflows/create-template.md, which dispatches `kind: brand` to skills/ppt-master/workflows/create-template/create-brand.md
```

Three input paths are supported: brand asset (logo / brand site URL / branded PPTX / brand PDF), verbal spec dictated in chat, or empty skeleton for the user to fill in later.

## Workspace structure

Every brand uses the same workspace routing as layout and deck templates. Brand identity remains roster-free; omit empty optional directories instead of adding placeholder files.

```
templates/brands/<brand_id>/
├── templates/
│   └── design_spec.md        # required — brand identity spec
├── images/                    # optional — logos and visual assets
│   ├── logo.<ext>            # optional — primary logo
│   └── <brand>_wordmark.svg  # optional — alternate lockups and visual assets
├── icons/                     # optional — branded icon overrides
└── exports/                   # normally absent; real local derived artifacts only; Git-ignored
```

Logo filenames are descriptive, not contractual — `templates/design_spec.md` §IV lists exact `../images/...` paths and usage contexts. Single-lockup brands typically ship one logo; dual-lockup brands ship separately named files.

`templates/design_spec.md` carries a YAML frontmatter block with `kind: brand` and is the single source of truth for the brand identity. The six required sections are: I Brand Overview / II Color Scheme / III Typography / IV Logo / V Voice & Tone / VI Icon Style.

## Discovery index

[brands_index.json](./brands_index.json) is a slim machine-readable map (`brand_id → { summary, primary_color }`). Refresh it with `register_template.py --kind brand <brand_id>` after a brand is created or edited. Registration rejects incomplete frontmatter, mismatched IDs, page SVGs, missing required identity sections, invalid or inconsistent colors/provenance, and broken workspace-local asset references.

Listing the index does not trigger any pipeline action — Generate Step 3 triggers only on an explicit directory path supplied by the user or an exact validated Create Template handoff, regardless of whether the brand appears in the index.
