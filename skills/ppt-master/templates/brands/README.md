# Brand Identity Presets

This directory holds **brand-only templates**: identity bundles (colors / typography / logo / voice / icon style) without an SVG page roster. Structurally a brand is a layout template minus its page roster — Strategist locks the brand's identity tokens as truth; Executor designs pages freely under those constraints.

## How brands are consumed

Brand application follows the **same explicit-path rule as layout templates** at SKILL.md Step 3:

| User input at SKILL.md Step 3 | Behavior |
|---|---|
| An explicit brand directory path (e.g. `templates/brands/acme/`) | Copy `design_spec.md` + `logo.<ext>` + any present asset subdirectories into `<project_path>/brand/`; Strategist locks color / typography / logo / voice as truth |
| Bare brand name only ("use acme brand"), brand mention without path, or silence | Skip — same mechanical rule as layout templates: bare names never trigger |
| Both a brand path and a layout template path supplied | Both apply; brand identity overrides layout-template defaults, layout template's page roster stays intact |

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

`design_spec.md` carries a YAML frontmatter block with `kind: brand` and is the single source of truth for the brand identity. The seven sections are: I Brand Overview / II Color Scheme / III Typography / IV Logo / V Voice & Tone / VI Icon Style / VII Visual Assets (optional).

## Discovery index

[brands_index.json](./brands_index.json) is a slim machine-readable map (`brand_id → { summary, keywords, primary_color }`). It is refreshed by `register_template.py --kind brand <brand_id>` after a brand is created or edited.

Listing the index does not trigger any pipeline action — Step 3 triggers only on an explicit directory path supplied by the user, regardless of whether the brand appears in the index.
