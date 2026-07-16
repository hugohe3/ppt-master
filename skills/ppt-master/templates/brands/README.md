# Brand Identity Presets

This directory holds **brand-only templates**: identity bundles (color / typography / logo / voice / icon style) without an SVG page roster. Strategist locks the brand's identity segment as truth; Executor designs pages freely under those constraints.

Brand is one of three template kinds in the library — alongside [`layouts/`](../layouts/) (structure-only) and [`decks/`](../decks/) (complete identity + structure). Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

## How brands are consumed

Brand application follows the **same explicit-path rule and workspace routing as all template kinds** at SKILL.md Step 3:

| User input at SKILL.md Step 3 | Behavior |
|---|---|
| An explicit brand workspace path (e.g. `templates/brands/anthropic/`) | Resolve `templates/design_spec.md`; stage `templates/` plus any existing `images/` and `icons/` into the matching project directories; Strategist locks the identity segment |
| Bare brand name only ("use anthropic brand"), brand mention without path, or silence | Skip — same mechanical rule as all template kinds: bare names never trigger |
| Brand path + layout path | Fuse into one `design_spec.md` — brand owns identity segment (color / typography / logo / voice / icon style); layout owns structure segment (canvas / page roster). See `SKILL.md` Step 3. |
| Brand path + deck path | Fuse — brand identity overrides deck identity; structure + middle segments come from deck |
| Brand path + layout path + deck path | Three-way fuse — brand=identity, layout=structure, deck=middle |
| Two brand paths | Conflict resolution prompt before fusion — user picks per-segment source |

`brands_index.json` is discovery-only; listing brands never advances the pipeline.

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

Listing the index does not trigger any pipeline action — Step 3 triggers only on an explicit directory path supplied by the user, regardless of whether the brand appears in the index.
