# Template Creation Tools

Tool behavior behind [`create-template.md`](../../workflows/create-template.md) and [`template-designer.md`](../../references/template-designer.md): the PPTX import workspace, the authoring IR, template-mode validation, the review deck, and registration. `mirror_template_materialize.py`, `extract_svg_assets.py`, `extract_svg_pictures.py`, and `svg_authoring_view.py` are documented in [`svg-pipeline.md`](svg-pipeline.md).

## `pptx_template_import.py`

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>" [--inheritance-mode layered|both|flat]
```

Produces one import workspace (typically under `/tmp/pptx_template_import/`; an analysis intermediate, never a final template):

| Output | Content |
|---|---|
| `analysis/manifest.json` | Source facts: slide size, theme colors, fonts, per-master theme summaries, resource inventory and asset-name map, placeholder metadata, SVG file paths, per-slide / per-layout / per-master metadata (including source-owned inherited-shape visibility), `pageTypeCandidates` |
| `analysis/native_structure.json` | Stable Master/Layout keys, picker names, placeholder type/index/geometry, inherited-shape visibility, source hash, source-graph quality facts |
| `sources/source.pptx` | Byte-preserved backing package for cross-checking and identity validation; never copied into a template |
| `images/` | PowerPoint image media including SVG/EMF/WMF; SVG `href` values reuse the manifest asset map |
| `sounds/`, `audio/`, `video/`, `native-payloads/` | Conditional semantic resource directories, created only when populated |
| `validation/conversion-report.json` | Source-recovery and fidelity diagnostics not duplicated in the structural manifests |
| `svg/master_*.svg`, `svg/layout_*.svg`, `svg/slide_NN.svg`, `svg/inheritance.json` | Immutable layered lossless view: every master and layout rendered once (including ones no sample slide uses), each slide's own shapes only, and the Slide → Layout → Master consumption map with `showInheritedShapes` / `showMasterShapes` (Layout shapes follow the Slide flag; Master shapes need both; backgrounds are independent) |
| `svg-flat/slide_NN.svg` | Optional (`--inheritance-mode both`) self-contained verification view of each complete page |
| `authoring-svg/` (+ `authoring-svg-flat/` with `both`) | Canonical compact editable SVG projected from parsed evidence, with model-readable `authoring_summary.json` and tool-only `authoring_manifest.json` |

- `layered` (default) emits only the canonical layered view; `both` adds the flat verification tree; `flat` emits a projection-only self-contained `svg/` tree without master/layout/inheritance files. Imported-deck round-trip uses the separate `authoring-svg-flat/` contract of `pptx_to_svg.py --roundtrip`.
- Placeholder metadata lives in the manifest; master/layout SVGs show lightweight dashed guides with labels only in `svg/`. Charts, SmartArt, diagrams, and OLE objects are typed placeholders in `svg/` and preview images with a badge in `svg-flat/`; tables are converted to real SVG. Missing media and external linked images fail the import; EMF/WMF convert to PNG previews when the local toolchain supports it, otherwise the import fails.
- The import transaction publishes `authoring-svg/` already normalized and decoration-factored: large non-semantic decorative vector groups become one canonical asset under `<import_workspace>/icons/imported/` referenced as `<use data-icon="imported/..." data-pptx-asset-role="decoration"/>`; do not run a second readability or compaction pass. `--inheritance-mode both` reuses the layered inventory (`--reuse-inventory`) so only genuinely flat-only vectors create another asset under the `flat` prefix; `--clean-stale` removes obsolete `flat_*` duplicates. Every asset root, placeholder, and v2 inventory record declares the `decoration` role; any subtree with a semantic marker, text, table, chart, or relationship stays inline, and extraction and both consumers fail closed if that boundary is crossed. Eligible records may retain `data-pptx-source-ref` so re-inlining re-establishes their object mapping; referenced defs (`gradient` / `pattern` / `filter` / `clipPath` / `marker`) are copied into each asset and namespaced.
- The projection removes opaque/duplicate/import-only carriers while retaining visible intent, compact frame/preset and structure markers, ids, assets, inline Chart/Table JSON, and per-object source refs. Model-facing page coordinates use at most two decimals; crop/path/matrix values keep required precision. The summary indexes roster and counts; the manifest owns source paths/hashes and initial subtree hashes and never enters model context. After any direct IR edit, refresh the summary: `svg_authoring_view.py "<import_workspace>/authoring-svg" --refresh-summary` (in-place vector/picture normalization refreshes it automatically).
- The importer generates no narrative summary or SVG-size CSV.

**Artifact roles**: `analysis/manifest.json` is the truth for source-deck facts (slide size, theme, fonts, background inheritance, resource inventory, declared structure, reuse relationships); `analysis/native_structure.json` for source PowerPoint identity (keys, picker names, parents, placeholder types/indices, package hash); `svg/inheritance.json` for consumption and visibility. The three overlap only at contract boundaries so materialization can cross-check identity, ownership, and visibility — never collapse or substitute them. `authoring_summary.json` is the model-facing roster index; `authoring_manifest.json` is machine-only provenance validated by the mirror compiler. Exported `images/` is the canonical reusable image pool; `icons/imported/*.svg` is the canonical decoration pool but not part of the default read set — use `authoring_summary.json` `icon_refs` and cleaned SVGs first, query `*_vector_asset_inventory.json` by exact asset id only when source-ref or fingerprint detail is needed, and open an individual asset only when it affects a design decision.

## Type B source bundles

```bash
python3 skills/ppt-master/scripts/svg_authoring_view.py "<normalized_svg_source>" -o "<svg_analysis_workspace>/authoring-svg" --projection-kind generic
python3 skills/ppt-master/scripts/extract_svg_assets.py "<svg_analysis_workspace>/authoring-svg" --icons-dir "<svg_analysis_workspace>/icons" --icon-namespace imported --inplace --id-prefix source --min-decoration-bytes 3000 --clean-stale
```

Creates a non-destructive authoring IR bundle in a throwaway analysis workspace and runs the vector readability pass only on that IR; the user's source directory is never rewritten. For an explicitly selected complex subtree that should stay one SVG picture, apply `extract_svg_pictures.py` to the analysis IR with `--resource-root` set to the narrowest directory containing the IR and every local dependency.

## `svg_quality_checker.py --template-mode`

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_source>" --template-mode --canonical-authoring [--format <canvas_format>]
```

Globs `*.svg` in the template directory; skips `spec_lock.md` drift checks; enforces roster ↔ resolved Design Spec consistency as errors (orphan or missing files break the contract and, in library scope, the index); emits advisory warnings when a page lacks a conventional placeholder (silence them with a `placeholders:` frontmatter map); requires every SVG root to declare one output Master and Layout (zero-slot Layouts are valid); rejects ordinary Master/Layout `<g>` elements, nested structure markers, missing slot bounds, and carrier-bound slots without exactly one compatible carrier (a validated compact authored-preset `<g>` is the sole fixed-layer group exception and may be one `object` carrier); validates cross-page Master equality and same-key Layout atom/slot equality; warns when distinct Layout keys have identical static framing/slot contracts. For `kind: brand` it validates the identity-only frontmatter/sections/colors/provenance/asset references; for `kind: style` the frontmatter, section/field shape, conditional custom and fallback values, portable ID, and one-file roster-free boundary. It validates the authoring contract, not the compiled OOXML package.

## `template_preview_pptx.py`

```bash
python3 skills/ppt-master/scripts/template_preview_pptx.py "<authoring_workspace>" [--force] [--native-charts-and-tables -o <distinct_path>]
```

Consumes `templates/*.svg` directly, compiles the declared structured Master/Layout contract into `<authoring_workspace>/exports/<template_id>_template_preview.pptx` (creating `exports/` on demand), and reopens the result to verify one slide per prototype, the expected Master/Layout counts, exact Presentation → Master → Layout → Slide registration, distinct Theme parts per Master, valid unique `p14:creationId` and registration IDs, and — for `standard` / `fidelity` — that every carrier-bound placeholder on each review Slide has the same type, effective index, and full frame as its registered Layout placeholder. Authored modes use ephemeral SVG copies with concise preview-only sample text so long `{{...}}` markers stay readable; source SVGs, carrier typography, slot metadata, and Layout frames are unchanged. The default review keeps visible Chart/Table fallbacks; `--native-charts-and-tables -o <distinct_path>` writes a separately named JSON-first review. The first export refuses an existing output; `--force` replaces it intentionally. It needs no project `spec_lock.md`, creates no persistent project, and never infers structure.

## `register_template.py`

```bash
python3 skills/ppt-master/scripts/register_template.py <template_id> --kind brand|style|layout|deck [--dry-run]
python3 skills/ppt-master/scripts/register_template.py --kind style|deck|layout --rebuild-all
```

Derives the index entry from `templates/design_spec.md` (frontmatter preferred; prose fallback) plus the actual `templates/*.svg` roster and updates `templates/brands/brands_index.json`, `styles/styles_index.json`, `layouts/layouts_index.json`, or `decks/decks_index.json`. The JSON index is the single discovery source for Default Stage-1 template controls and chat listing; READMEs describe kinds in prose and are never edited. `--dry-run` checks the directory/index identity without writing.
