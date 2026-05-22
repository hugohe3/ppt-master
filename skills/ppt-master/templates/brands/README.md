# Brand Identity Presets

This directory holds **brand-only templates**: identity bundles (color / typography / logo / voice / icon style) without an SVG page roster. Strategist locks the brand's identity segment as truth; Executor designs pages freely under those constraints.

Brand is one of three template kinds in the library — alongside [`layouts/`](../layouts/) (structure-only) and [`decks/`](../decks/) (full-PPT replica). Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

## How brands are consumed

Brand application follows the **same explicit-path rule as all template kinds** at SKILL.md Step 3, and lands in the **same project directory** (`<project_path>/templates/`):

| User input at SKILL.md Step 3 | Behavior |
|---|---|
| An explicit brand directory path (e.g. `templates/brands/anthropic/`) | Copy `design_spec.md` + logo files + asset subdirectories into `<project_path>/templates/`; Strategist locks identity segment |
| Bare brand name only ("use anthropic brand"), brand mention without path, or silence | Skip — same mechanical rule as all template kinds: bare names never trigger |
| Brand path + layout path | Fuse into one `design_spec.md` — brand owns identity segment (color / typography / logo / voice / icon style); layout owns structure segment (canvas / page roster). See `SKILL.md` Step 3. |
| Brand path + deck path | Fuse — brand identity overrides deck identity; structure + middle segments come from deck |
| Brand path + layout path + deck path | Three-way fuse — brand=identity, layout=structure, deck=middle |
| Two brand paths | Conflict resolution prompt before fusion — user picks per-segment source |

`brands_index.json` is discovery-only; listing brands never advances the pipeline.

## Creating a new brand

Run the standalone workflow:

```
Read skills/ppt-master/workflows/create-brand.md
```

Three input paths are supported: brand asset (logo / brand site URL / branded PPTX / brand PDF), verbal spec dictated in chat, or empty skeleton for the user to fill in later.

## Package structure

Every brand directory is self-contained:

```
templates/brands/<brand_id>/
├── design_spec.md            # required — brand identity spec (7 sections)
├── logo.<ext>                # optional — primary brand logo (single-lockup brands)
│   …or…
├── <brand>_wordmark.<ext>    # optional — wordmark variant (dual-lockup brands)
├── <brand>_mark.<ext>        # optional — symbol / icon variant (dual-lockup brands)
├── images/                   # optional — branded photos
├── illustrations/            # optional — branded illustrations
└── icons/                    # optional — branded icon overrides
```

Logo filenames are descriptive, not contractual — `design_spec.md` §IV lists the exact files and the contexts in which each is used. Single-lockup brands typically ship one `logo.<ext>`; dual-lockup brands (e.g. Google's wordmark + G mark) ship separately named files.

`design_spec.md` carries a YAML frontmatter block with `kind: brand` and is the single source of truth for the brand identity. The six required sections are: I Brand Overview / II Color Scheme / III Typography / IV Logo / V Voice & Tone / VI Icon Style.

## Discovery index

[brands_index.json](./brands_index.json) is a slim machine-readable map (`brand_id → { summary, primary_color }`). It is refreshed by `register_template.py --kind brand <brand_id>` after a brand is created or edited.

Listing the index does not trigger any pipeline action — Step 3 triggers only on an explicit directory path supplied by the user, regardless of whether the brand appears in the index.
