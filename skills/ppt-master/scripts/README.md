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
| SVG pipeline | `preset_shape_svg.py`, `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md); [native preset authoring](../references/native-shape-authoring.md) |
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
```

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

The helper never writes a page or project file. Select one exact semantic stock-shape match, inspect the emitted fragment, and insert it into the hand-authored SVG with the normal patch workflow. Keep ordinary rectangles, ellipses, freeform geometry, charts, icons, and ambiguous silhouettes as regular SVG. See [`references/native-shape-authoring.md`](../references/native-shape-authoring.md) for the selection and metadata contract.

Post-processing and export:

```bash
python3 scripts/extract_svg_assets.py <svg_dir> --icons-dir <icons_dir> --inplace --id-prefix <prefix>  # optional: shrink imported/reference SVGs before AI review
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

`finalize_svg.py` optimizes raster images by default using `2x` display pixels and max `2560px`. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: only oversized full source images are reduced to max `2560px`, so later PowerPoint resizing keeps more image detail. Use `svg_to_pptx.py --image-sizing display --image-scale 2` only for aggressive size reduction, or `--no-image-optimize` when the native PPTX must embed original image bytes.

`finalize_svg.py` remains mandatory because it creates the self-contained `svg_final/` visual preview. Those SVGs may be opened directly or inserted into PowerPoint as SVG pictures. The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter; `-s final` is diagnostic-only, and PowerPoint's manual Convert-to-Shape operation is unsupported.

For SVG-authoring routes, `svg_output/` is the complete visible page-design source: every exported text, image, shape, background, and template-derived layout element is present in the page SVG or explicitly referenced by it. Export may translate represented content into Master/Layout/Slide parts or native objects, but it does not retrieve missing visible content from templates or planning files. Speaker notes, animation, narration, transitions, `template-fill-pptx`, and `native-enhance-pptx` remain separately owned capabilities.

When `spec_lock.md` has no `pptx_structure` section, native `svg_to_pptx.py` falls back to `baseline`: the generated deck keeps a standard Master/Layout relationship and promotes only exact, z-order-safe shared backgrounds/chrome. Root `data-pptx-page-role` selects `Cover`, `Agenda`, `Section`, `Closing`, or `Content`; filenames are a fallback for marker-free legacy SVGs. A family-wide exact background and an exact leading structurally marked chrome prefix may move into that Layout; ids are consulted only when the structural role is absent. Actual titles, body content, pictures, charts, tables, page numbers, and page-specific shapes remain on Slide. No visual-similarity or placeholder inference is performed. Baseline also prunes unused layouts and maps locked typography/colors into the PowerPoint theme. Use `--pptx-structure flat` for slide-local diagnostics.

Deck/layout template routes use explicit template structure. Each complete SVG names its output Layout, repeats inherited Master/Layout preview layers, and marks supported content placeholders. Strict keeps the selected Layout contract; adaptive may create a new Layout while retaining the Master. The exporter validates cross-slide equality, creates one reusable Layout per key, removes repeated inherited copies, and keeps actual content Slide-local. The complete contract lives in [`references/shared-standards.md`](../references/shared-standards.md#explicit-pptx-master--layout--placeholder-metadata-template-export).

Current `create-template` output always rebuilds explicit SVG structure and does not package `native_structure.json` or `source_template.pptx`. `preserve` remains available only for existing projects that already carry the legacy pair.

`pptx_to_svg.py` annotates verified text-grid tables and conservative classic-chart caches with `data-pptx-native` metadata. Table import now covers unmerged grids plus canonical rectangular merges, safe solid/no-fill per-side borders, and plain multi-paragraph cells. A merge must use the exact `rowSpan` / `gridSpan` / `hMerge` / `vMerge` physical topology with empty merge slaves; unsafe border XML, mixed run formatting, non-solid fills, and other merge encodings remain fallback-only. For table style `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}`, the normalized SVG fallback resolves `wholeTbl`, `firstRow`, horizontal banding, theme colors/fonts, and direct cell/run overrides; other built-in/custom style families are not implied.

Supported parsed column/bar/line/area, pie/doughnut, scatter, and bubble charts without a baked preview receive a deterministic readable fallback marked `data-pptx-visual-status="normalized"`. The importer additionally activates verified column/line/area combo charts, canonical OHLC stock charts, area charts with numeric date axes, and verified scatter/bubble charts whose two value axes fit the closed `axes.x` / `axes.y` contract. Combo plots may retain independent primary/secondary category caches and workbook ranges. Both the category/value and XY contracts retain kind/position/visibility/label position/number format/min/max/major unit/reverse/major gridlines for native read-back. Scatter import derives effective `scatter_style` from uniform per-series line/marker/smooth state. The normalized XY fallback newly consumes only the two major-gridline flags; other XY fields do not imply complete visual-axis parity. These contracts are not a full `AxisSpec`: ChartEx import, arbitrary stock variants, other date-axis families, and other unlisted axis semantics remain fallback-only. Safe common series paint forms and theme scheme colors are resolved; unknown series paint/style XML outside the explicit normalization boundaries still fails closed. Safe stock series style may pass the structural gate, but stock series, `hiLowLines`, and up-down bar local styling can still normalize under the editable-first contract. The editable native replacement remains allowed to normalize unmodeled no-fill/alpha/line/marker details and reports the route-level loss risk. Chart title/legend/axis titles and supported data-label flags are retained when the current schema can represent them. Fallback-only objects keep rendered SVG content or a baked chart preview and carry `data-pptx-native-status`, which validation and `--native-objects` export report as a warning. A supported active marker without a renderer, such as current `of_pie`, keeps `data-pptx-visual-status="placeholder"` plus `data-pptx-route-status="reconstruction-only"`; default export keeps the placeholder and native opt-in may still reconstruct it.

Active imported table/chart markers carry `data-pptx-fallback-sha256`. Visible fallback edits, reachable SVG fragment-definition changes, marker-local reference-target changes, and marker transforms make the baseline stale: the mandatory quality checker warns, default export remains available, and `--native-objects` fails instead of discarding the SVG edit. Legacy markers without a baseline remain convertible with a checker/native-route warning. ChartEx export now writes valid payload palette entries into its color-style part; it still does not promise full source ChartEx styling.

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
