# PPT Master Toolset

This directory contains user-facing scripts for conversion, project setup, direct PPTX template filling, SVG processing, export, recorded narration, and image generation.

## Directory Layout

- Top-level `scripts/`: runnable entry scripts
- `scripts/source_to_md.py`: unified source-document → Markdown dispatcher
- `scripts/source_to_md/`: source-document → Markdown routing/batch helpers and backend converters (`_dispatcher.py`, `_batch.py`, `pdf_to_md.py`, `doc_to_md.py`, `excel_to_md.py`, `ppt_to_md.py`, `web_to_md.py`)
- `scripts/image_backends/`: internal provider implementations used by `image_gen.py`
- `scripts/tts_backends/`: internal TTS provider implementations used by `notes_to_audio.py`
- `scripts/template_import/`: internal PPTX reference-preparation helpers used by `pptx_template_import.py`
- `scripts/svg_finalize/`: internal post-processing helpers used by `finalize_svg.py`
- `scripts/docs/`: topic-focused script documentation
- `scripts/assets/`: static assets consumed by scripts

## Quick Start

Typical end-to-end workflow:

```bash
python3 scripts/source_to_md.py <file-or-url-or-dir> [<file-or-url-or-dir> ...]
# or direct backend calls:
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
# or
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...> --move
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/animation_config.py scaffold <project_path>  # optional object-level animation overrides
python3 scripts/svg_to_pptx.py <project_path>
```

Repository update:

```bash
python3 scripts/update_repo.py
```

## Script Index

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
| Conversion | `source_to_md.py`, `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py`, `pptx_to_svg.py` | [docs/conversion.md](./docs/conversion.md) |
| Project management | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py`, `template_fill_pptx.py`, `native_enhance_pptx.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `preset_shape_svg.py`, `svg_authoring_view.py`, `mirror_template_materialize.py`, `finalize_svg.py`, `svg_to_pptx.py`, `template_preview_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `extract_svg_pictures.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md); [native preset authoring](../references/native-shape-authoring.md) |
| PPTX transitions | `pptx_transitions.py` | [docs/pptx-transitions.md](./docs/pptx-transitions.md) |
| PPTX animations | `pptx_animations.py`, `animation_config.py` | [docs/pptx-animations.md](./docs/pptx-animations.md) |
| Spec maintenance | `update_spec.py` | [docs/update_spec.md](./docs/update_spec.md) |
| Image tools | `image_gen.py`, `latex_render.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## High-Frequency Commands

Conversion:

```bash
python3 scripts/source_to_md.py <file-or-url-or-dir> [<file-or-url-or-dir> ...]
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/doc_to_md.py <file.docx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/source_to_md/web_to_md.py <url>
python3 scripts/pptx_to_svg.py <deck.pptx> -o <output_dir>  # reconstruction/reference SVG import
```

Project setup:

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...> --move
python3 scripts/project_manager.py validate <project_path>
```

Template source import:

```bash
python3 scripts/pptx_template_import.py <template.pptx>
python3 scripts/pptx_template_import.py <template.pptx> --manifest-only
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode both
python3 scripts/svg_authoring_view.py <imported-svg-or-dir> -o <output-dir> --projection-kind layered
python3 scripts/mirror_template_materialize.py <import_workspace> <empty_template_workspace>
python3 scripts/template_preview_pptx.py <template_workspace>
python3 scripts/template_preview_pptx.py <legacy_template_workspace> --visual-only
```

Template import defaults to the canonical layered `svg/` tree. Use
`--inheritance-mode both` only when a separate self-contained `svg-flat/`
verification tree is required. No derived narrative digest is generated
because `manifest.json` already owns those facts.

`svg_authoring_view.py` creates a lightweight, non-destructive editable IR
bundle from PPTX-imported SVGs. It removes embedded `txbody` payloads,
duplicate hidden geometry carriers, and import-identity attributes from the
copy while retaining visible fallback geometry, text, images, stable element
ids, root Master/Layout markers, selected native-shape intent, and
document-local `data-pptx-source-ref` values.
Relative local image references are rewritten so the projected copy still
renders from its new location. The bundle's `authoring_manifest.json` records
source/authoring hashes and object paths without duplicating opaque payload.
The full imported SVG remains unchanged as native-payload backing. Template
creation edits the IR and materializes validated `templates/*.svg`; the IR
directory itself is not a final template or direct release export source.

`mirror_template_materialize.py` is the deterministic Type A mirror compiler.
It consumes only the layered `authoring-svg/` IR as editable input, validates
its manifest against immutable `svg/`, `native_structure.json`,
`svg/inheritance.json`, `source_template.pptx`, and any extracted-vector
inventory, then publishes a complete structured template roster atomically.
Unchanged supported Slide-local/slot refs may recover native payload; edited
refs keep their current SVG fallback. Fixed Master/Layout wrappers are expanded
mechanically into direct atoms, source visibility flags become canonical root
metadata, and imported vectors are copied once to `icons/imported/`. Bitmap
assets go to `images/`; other referenced source assets go to
`templates/assets/`. The destination must be empty, and the command does not
write `templates/design_spec.md`; Template_Designer owns that authored brief.

`template_preview_pptx.py` reads a template workspace, exports every public `templates/*.svg` prototype as one structured review slide, and verifies the resulting Master/Layout package. Canonical definition-only `layout_<layout_key>.svg` prototypes are registered as reusable Layouts through internal carrier slides that are removed before publication; they never increase the review deck's visible slide count. This is an on-demand review action: its default output is `exports/<template_id>_template_preview.pptx`, and that directory need not exist before the command runs. It refuses an existing output unless an intentional re-export passes `--force`. `--visual-only` is an explicit migration aid for legacy SVG rosters: it creates a slide-local visual review deck without validating or claiming a reusable Master/Layout contract. This diagnostic path does not require a project `spec_lock.md`; it may retain generic theme/text defaults inside its clean one-Master/one-Layout shell. New structured templates use the default mode when a review deck is requested.

Template fill (direct PPTX, no SVG conversion):

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source.pptx> <material...>
# Manual fallback when import-sources did not produce analysis/<stem>.slide_library.json:
python3 scripts/template_fill_pptx.py analyze <project_path>/sources/<source.pptx> -o <project_path>/analysis/<stem>.slide_library.json
python3 scripts/template_fill_pptx.py scaffold <project_path>/analysis/<stem>.slide_library.json -o <project_path>/analysis/fill_plan.json --slides "1,3,4"
python3 scripts/template_fill_pptx.py check-plan <project_path>/analysis/<stem>.slide_library.json <project_path>/analysis/fill_plan.json -o <project_path>/analysis/check_report.json
python3 scripts/template_fill_pptx.py apply <project_path>/sources/<source.pptx> <project_path>/analysis/fill_plan.json -o <project_path>/exports/filled.pptx
python3 scripts/template_fill_pptx.py validate <project_path>
```

`apply` requires `fill_plan.json` to have top-level `"status": "confirmed"` unless `--force` is passed. It automatically writes `filled_YYYYMMDD_HHMMSS.pptx` unless the output stem already ends with a timestamp. It applies a `fade` page transition by default; `--transition <effect>` (fade/push/wipe/split/strips/cover/random, `--transition-duration` in seconds) changes it, `--transition none` removes it, `--transition keep` preserves the source transitions, and a per-slide `transition` field in the plan overrides whatever the CLI selects.

Native existing-PPTX enhancement (direct PPTX, no SVG conversion):

```bash
python3 scripts/native_enhance_pptx.py init <source.pptx> --name <project_slug>
python3 scripts/native_enhance_pptx.py plan <project_path>
python3 scripts/native_enhance_pptx.py validate <project_path>
python3 scripts/native_enhance_pptx.py apply <project_path>
```

Native preset shape authoring (one registry-backed fragment on stdout):

```bash
python3 scripts/preset_shape_svg.py list --search arrow
python3 scripts/preset_shape_svg.py describe rightArrow
python3 scripts/preset_shape_svg.py render rightArrow --id process-arrow --frame 120 180 240 96 --fill '#2563EB'
```

The helper never writes a page or project file. Select one exact semantic
stock-shape match, inspect the emitted fragment, and insert it into the
hand-authored SVG with the normal patch workflow. Its project-authored output
is one compact atomic `<g>` with direct registry-generated visible paths;
quality check and export rerender the registry instead of relying on a hidden
carrier, preview wrapper, or stored preview fingerprint. PPTX import and
round-trip SVGs deliberately keep their expanded carrier/preview evidence and
are not rewritten into this authored form. Keep ordinary rectangles, ellipses,
freeform geometry, charts, icons, and ambiguous silhouettes as regular SVG.
See [`references/shared-standards.md`](../references/shared-standards.md) for
the normative contract and
[`references/native-shape-authoring.md`](../references/native-shape-authoring.md)
for selection and authoring guidance.

Create-template/source normalization (optional; never part of automatic export):

```bash
python3 scripts/extract_svg_assets.py <layered_svg_dir> --icons-dir <icons_dir> --icon-namespace imported --inplace --id-prefix layered
python3 scripts/extract_svg_assets.py <flat_svg_dir> --icons-dir <icons_dir> --icon-namespace imported --reuse-inventory <layered_inventory.json> --inplace --id-prefix flat
python3 scripts/extract_svg_pictures.py "<svg_file>" --select "<group_id>" --resource-root "<workspace>" --images-dir "<picture_assets_dir>" --inplace  # optional create-template normalization: one selected group -> one SVG picture
python3 scripts/mirror_template_materialize.py <import_workspace> <empty_template_workspace>  # Type A mirror only
```

`extract_svg_assets.py` fingerprints each extracted subtree before generated-ID
namespacing. Process the layered authoring view first, then pass its inventory to
the flat view with `--reuse-inventory`; matching flat subtrees reference the
existing layered asset instead of creating a duplicate file. Only unmatched
flat-only vectors create new assets. Create-template stores these assets once in
`<workspace>/icons/imported/` and writes `data-icon="imported/<name>"` references.
Inventories retain any `data-pptx-source-ref` values carried by the extracted
subtree, so re-inlining preserves authoring-manifest object identity.
Rerunning a namespaced pass against an already rewritten projection inventories
the existing references without progressively wrapping more parent geometry.

Post-processing and export:

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

`finalize_svg.py` optimizes raster images by default using `2x` display pixels and max `2560px`. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: only oversized full source images are reduced to max `2560px`, so later PowerPoint resizing keeps more image detail. Use `svg_to_pptx.py --image-sizing display --image-scale 2` only for aggressive size reduction, or `--no-image-optimize` when the native PPTX must embed original image bytes.

`finalize_svg.py` remains mandatory because it creates the self-contained `svg_final/` visual preview. Those SVGs may be opened directly or inserted into PowerPoint as SVG pictures. The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter; `-s final` is diagnostic-only, and PowerPoint's manual Convert-to-Shape operation is unsupported.

For SVG-authoring routes, `svg_output/` is the complete visible page-design source: every exported text, image, shape, background, and template-derived layout element is present in the page SVG or explicitly referenced by it. Export may translate represented content into Master/Layout/Slide parts or native objects, but it does not retrieve missing visible content from templates or planning files. Speaker notes, animation, narration, transitions, `template-fill-pptx`, and `native-enhance-pptx` remain separately owned capabilities.

Native `svg_to_pptx.py` release export reads the project's explicit structure mode. Free-design and brand-only projects use `flat`, omit Master/Layout mappings and SVG structure metadata, keep every represented object Slide-local, and materialize one clean project-owned Master plus one Blank Layout from the current color/typography lock. Stock content placeholders and unused built-in Layouts are removed; only the standard date/footer/slide-number capability hooks remain. Deck/layout template projects use `structured`: each project supplies unique Master/Layout definitions and one Layout assignment per generated page before SVG generation, and every SVG root repeats its assigned identity. A template-backed definition may remain unused and still register without a published carrier slide. Fixed Master/Layout visuals are direct semantic atoms; ordinary groups are invalid there, while one validated compact authored-preset `<g>` is the sole group exception because it compiles to one native shape. Reusable slots are top-level groups with positive design-zone bounds plus one compatible carrier. Composite `object` regions use explicit proxy binding, and zero-slot Layouts are valid.

Structured template export compiles only the declared structure, maps locked typography/colors into PowerPoint defaults, creates the named Master/Layout parts, and reads the package back before publication. It never clusters pages, promotes repeated chrome heuristically, or invents placeholders. Flat export is the normal free-design/brand-only route: it creates only the clean project-owned shell and performs no promotion or deduplication of Slide content.

Template `page_layouts` records authoring-input provenance, `pptx_masters` / `pptx_layouts` own unique reusable definitions, and `page_pptx_layouts` owns page assignment. Strict preserves its Master/Layout/slot contract; adaptive retains its Master and may use a new Layout key only when fixed Layout atoms or slot topology/bounds change. `standard` / `fidelity` author new SVGs and a new Master/Layout/slot contract. `mirror` restores the complete source identity graph—including unused Layout definitions—without semantic synthesis, while mechanically expanding fixed-layer group wrappers into the direct atoms required by the structured contract.

Legacy structured/template contracts using `baseline`, `template`, `preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled`/`utility`, direct atomic placeholders, or incomplete root Master identity must run [`restore-pptx-structure`](../workflows/restore-pptx-structure.md) before release export. Explicit flat free-design/brand-only projects intentionally omit root Master identity.

`pptx_to_svg.py` annotates verified text-grid tables and conservative chart data with `data-pptx-replace-with` beside the visible SVG fallback and places the payload in `<metadata type="application/json">`; the parent claim selects the chart or table schema. Imported table/chart groups under this contract carry `data-pptx-import-source="pptx"`, whether active or fallback-only. Table import covers exact physical row/grid topology, canonical rectangular merges, safe solid/no-fill per-side borders, plain multi-paragraph cells, and a closed run-rich paragraph schema. Each rich run requires `text` and may use only `bold`, `italic`, `underline`, `strike`, `color`, `font_size`, one `font_family`, `lang`, and `alt_lang`. A merge must use the exact `rowSpan` / `gridSpan` / `hMerge` / `vMerge` physical topology with empty merge slaves. Presentation-only source run XML without a non-empty `effectLst` / `effectDag` normalizes; a table-cell run effect disables native replacement and adds a blocking effect diagnostic. Relationship-bearing text, extensions, line breaks, fields, tabs, bullets, broken text topology, unsafe border XML, non-solid fills, and other merge encodings remain fallback-only. For table style `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}`, the normalized SVG fallback resolves `wholeTbl`, `firstRow`, horizontal banding, theme colors/fonts, and direct cell/run overrides; other built-in/custom style families are not implied.

Supported parsed column/bar/line/area, pie/doughnut, scatter, and bubble charts without a baked preview receive a deterministic readable fallback marked `data-pptx-fallback-kind="normalized"`. The importer additionally activates verified column/line/area combo charts, canonical OHLC stock charts, area charts with numeric date axes, verified scatter/bubble charts whose two value axes fit the closed `axes.x` / `axes.y` contract, radar charts, safe `of_pie` `serLines`, axis/title/legend normalization, and validated bar/column gap/overlap cases. Combo plots may retain independent primary/secondary category caches and workbook ranges. Both the category/value and XY contracts retain kind/position/visibility/label position/number format/min/max/major unit/reverse/major gridlines for native read-back. Scatter import derives effective `scatter_style` from uniform per-series line/marker/smooth state. The normalized XY fallback consumes only the two major-gridline flags; the C4/C5 additions do not expand the normalized renderer. `gapWidth` is accepted only as an integer in `0..500` and `overlap` only as an integer in `-100..100`; both normalize in native output, while malformed or out-of-range values fail closed. Safe common series paint forms and theme scheme colors are resolved; unknown series paint/style XML outside the explicit normalization boundaries still fails closed. Safe stock series style may pass the structural gate, but stock series, `hiLowLines`, and up-down bar local styling can still normalize under the data-object-first contract. The PowerPoint-native replacement remains allowed to normalize unmodeled no-fill/alpha/line/marker details and reports the route-level loss risk. Chart title/legend/axis titles and supported data-label flags are retained when the current schema can represent them. Fallback-only objects keep rendered SVG content or a baked chart preview and carry `data-pptx-replacement-status`, which validation and `--native-charts-and-tables` export report as a warning. An active marker without a renderer keeps `data-pptx-fallback-kind="placeholder"`; default export keeps the reconstruction-only placeholder and the native Chart/Table opt-in may still reconstruct it.

The ChartEx importer accepts exactly the validated treemap, sunburst, histogram, pareto, box-whisker, waterfall, and funnel data models. Supported hierarchy/category/value/series/subtotal data round-trips to native output; source style, axes, labels, and binning may normalize. Numeric caches must be non-empty and finite with exact contiguous point topology. This is not arbitrary ChartEx import or presentation fidelity, and the ChartEx native writer still only promises valid payload palette entries rather than full source styling.

Active imported table/chart markers carry `data-pptx-fallback-sha256`. Visible fallback edits, reachable SVG fragment-definition changes, marker-local reference-target changes, and marker transforms make the baseline stale: the mandatory quality checker warns, default export remains available, and `--native-charts-and-tables` fails instead of discarding the SVG edit. Generated authoring and reusable templates omit import provenance and a static baseline without warning. Hashless legacy imported markers that still carry PPTX import provenance remain convertible with a checker/replacement-route warning. Legacy `data-pptx-native*`, `data-pptx-visual-status`, and `data-pptx-route-status` spellings and the `--native-objects` option remain read-compatible; generated output and canonical commands use the replacement/fallback names and `--native-charts-and-tables`.

Exporter-canonical classic charts also recover canonical solid series/slice
colors and exact one- or two-paragraph title styling; two paragraphs retain
their `title` / `subtitle` roles. Slide-number fields resolve to the display
number defined by `firstSlideNum`; standalone master/layout SVGs retain their
literal field fallback because they are shared by multiple slides.

Image generation:

```bash
python3 scripts/latex_render.py <project_path>
python3 scripts/latex_render.py <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py --list-backends
python3 scripts/analyze_images.py <project_path>/images
```

Repository update:

```bash
python3 scripts/update_repo.py
python3 scripts/update_repo.py --skip-pip
```

## Recommendations

- Keep one user-facing entry point per workflow at the top level of `scripts/`
- Move provider-specific or helper internals into subdirectories
- Prefer the unified entry points `project_manager.py`, `finalize_svg.py`, and `image_gen.py`
- Use `svg_output/` for the only supported native PPTX export and `svg_final/` for self-contained SVG visual preview / picture insertion

## Related Docs

- [Conversion Tools](./docs/conversion.md)
- [Project Tools](./docs/project.md)
- [SVG Pipeline Tools](./docs/svg-pipeline.md)
- [PPTX Transition Core](./docs/pptx-transitions.md)
- [Image Tools](./docs/image.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Skill Entry](../SKILL.md)

_Last updated: 2026-07-11_
