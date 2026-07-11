# PPT Master Toolset

This directory contains user-facing scripts for conversion, project setup, direct PPTX template filling, SVG processing, export, recorded narration, and image generation.

## Directory Layout

- Top-level `scripts/`: runnable entry scripts
- `scripts/source_to_md/`: source-document → Markdown converters (`pdf_to_md.py`, `doc_to_md.py`, `excel_to_md.py`, `ppt_to_md.py`, `web_to_md.py`)
- `scripts/image_backends/`: internal provider implementations used by `image_gen.py`
- `scripts/tts_backends/`: internal TTS provider implementations used by `notes_to_audio.py`
- `scripts/template_import/`: internal PPTX reference-preparation helpers used by `pptx_template_import.py`
- `scripts/svg_finalize/`: internal post-processing helpers used by `finalize_svg.py`
- `scripts/docs/`: topic-focused script documentation
- `scripts/assets/`: static assets consumed by scripts

## Quick Start

Typical end-to-end workflow:

```bash
uvx ppt-master pdf-to-md <file.pdf>
# or
uvx ppt-master ppt-to-md <deck.pptx>
uvx ppt-master excel-to-md <workbook.xlsx>
uvx ppt-master project init <project_name> --format ppt169
uvx ppt-master project import-sources <project_path> <source_files...> --move
uvx ppt-master total-md-split <project_path>
uvx ppt-master finalize-svg <project_path>
uvx ppt-master animation-config scaffold <project_path>  # optional object-level animation overrides
uvx ppt-master svg-to-pptx <project_path>
```

Repository update:

```bash
uvx ppt-master update-repo
```

## Script Index

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
<<<<<<< HEAD
| Conversion | `source_to_md.py`, `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py`, `pptx_to_svg.py` | [docs/conversion.md](./docs/conversion.md) |
=======
| Conversion | `source_to_md.py`, `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py`, `pptx_to_svg.py` | [docs/conversion.md](./docs/conversion.md) |
>>>>>>> upstream/main
| Project management | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py`, `template_fill_pptx.py`, `native_enhance_pptx.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| PPTX transitions | `pptx_transitions.py` | [docs/pptx-transitions.md](./docs/pptx-transitions.md) |
| PPTX animations | `pptx_animations.py`, `animation_config.py` | [docs/pptx-animations.md](./docs/pptx-animations.md) |
| Spec maintenance | `update_spec.py` | [docs/update_spec.md](./docs/update_spec.md) |
| Image tools | `image_gen.py`, `latex_render.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## High-Frequency Commands

Conversion:

```bash
uvx ppt-master source-to-md <file-or-url-or-dir> [<file-or-url-or-dir> ...]
uvx ppt-master pdf-to-md <file.pdf>
uvx ppt-master ppt-to-md <deck.pptx>
uvx ppt-master doc-to-md <file.docx>
uvx ppt-master excel-to-md <workbook.xlsx>
uvx ppt-master web-to-md <url>
uvx ppt-master pptx-to-svg <deck.pptx> -o <output_dir>  # reconstruction/reference SVG import
```

Project setup:

```bash
uvx ppt-master project init <project_name> --format ppt169
uvx ppt-master project import-sources <project_path> <source_files...> --move
uvx ppt-master project validate <project_path>
```

Template source import:

```bash
uvx ppt-master pptx-template-import <template.pptx>
uvx ppt-master pptx-template-import <template.pptx> --manifest-only
uvx ppt-master pptx-template-import <template.pptx> --inheritance-mode both
```

Template fill (direct PPTX, no SVG conversion):

```bash
mkdir -p <project_path>/sources <project_path>/analysis <project_path>/exports <project_path>/validation
uvx ppt-master template-fill-pptx analyze <project_path>/sources/<source.pptx> -o <project_path>/analysis/<stem>.slide_library.json
uvx ppt-master template-fill-pptx scaffold <project_path>/analysis/<stem>.slide_library.json -o <project_path>/analysis/fill_plan.json --slides "1,3,4"
uvx ppt-master template-fill-pptx check-plan <project_path>/analysis/<stem>.slide_library.json <project_path>/analysis/fill_plan.json -o <project_path>/analysis/check_report.json
uvx ppt-master template-fill-pptx apply <project_path>/sources/<source.pptx> <project_path>/analysis/fill_plan.json -o <project_path>/exports/filled.pptx
```

`apply` requires `fill_plan.json` to have top-level `"status": "confirmed"` unless `--force` is passed. It automatically writes `filled_YYYYMMDD_HHMMSS.pptx` unless the output stem already ends with a timestamp. It applies a `fade` page transition by default; `--transition <effect>` (fade/push/wipe/split/strips/cover/random, `--transition-duration` in seconds) changes it, `--transition none` removes it, `--transition keep` preserves the source transitions, and a per-slide `transition` field in the plan overrides whatever the CLI selects.

Native existing-PPTX enhancement (direct PPTX, no SVG conversion):

```bash
uvx ppt-master native-enhance-pptx init <source.pptx> --name <project_slug>
uvx ppt-master native-enhance-pptx plan <project_path>
uvx ppt-master native-enhance-pptx validate <project_path>
uvx ppt-master native-enhance-pptx apply <project_path>
```

Post-processing and export:

```bash
uvx ppt-master extract-svg-assets <svg_dir> --icons-dir <icons_dir> --inplace --id-prefix <prefix>  # optional: shrink imported/reference SVGs before AI review
uvx ppt-master total-md-split <project_path>
uvx ppt-master finalize-svg <project_path>
uvx ppt-master svg-to-pptx <project_path>
```

`finalize_svg.py` optimizes raster images by default using `2x` display pixels and max `2560px`. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: only oversized full source images are reduced to max `2560px`, so later PowerPoint resizing keeps more image detail. Use `svg_to_pptx.py --image-sizing display --image-scale 2` only for aggressive size reduction, or `--no-image-optimize` when the native PPTX must embed original image bytes.

`finalize_svg.py` remains mandatory because it creates the self-contained `svg_final/` visual preview. Those SVGs may be opened directly or inserted into PowerPoint as SVG pictures. The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter; `-s final` is diagnostic-only, and PowerPoint's manual Convert-to-Shape operation is unsupported.

For SVG-authoring routes, `svg_output/` is the complete visible page-design source: every exported text, image, shape, background, and template-derived layout element is present in the page SVG or explicitly referenced by it. Export may translate represented content into Master/Layout/Slide parts or native objects, but it does not retrieve missing visible content from templates or planning files. Speaker notes, animation, narration, transitions, `template-fill-pptx`, and `native-enhance-pptx` remain separately owned capabilities.

When `spec_lock.md` has no `pptx_structure` section, native `svg_to_pptx.py` falls back to `baseline`: the generated deck keeps a standard Master/Layout relationship and promotes only exact, z-order-safe shared backgrounds/chrome. Root `data-pptx-page-role` selects `Cover`, `Agenda`, `Section`, `Closing`, or `Content`; filenames are a fallback for marker-free legacy SVGs. A family-wide exact background and an exact leading structurally marked chrome prefix may move into that Layout; ids are consulted only when the structural role is absent. Actual titles, body content, pictures, charts, tables, page numbers, and page-specific shapes remain on Slide. No visual-similarity or placeholder inference is performed. Baseline also prunes unused layouts and maps locked typography/colors into the PowerPoint theme. Use `--pptx-structure flat` for slide-local diagnostics.

Deck/layout template routes use explicit template structure. Each complete SVG names its output Layout, repeats inherited Master/Layout preview layers, and marks supported content placeholders. Strict keeps the selected Layout contract; adaptive may create a new Layout while retaining the Master. The exporter validates cross-slide equality, creates one reusable Layout per key, removes repeated inherited copies, and keeps actual content Slide-local. The complete contract lives in [`references/shared-standards.md`](../references/shared-standards.md#explicit-pptx-master--layout--placeholder-metadata-template-export).

Current `create-template` output always rebuilds explicit SVG structure and does not package `native_structure.json` or `source_template.pptx`. `preserve` remains available only for existing projects that already carry the legacy pair.

`pptx_to_svg.py` annotates supported unmerged tables and conservative classic-chart caches with `data-pptx-native` metadata. Source table-style inheritance, supported solid cell fills/basic text formatting, chart title/legend/axis titles, and plot-level data-label flags for area/bar/column/line charts are retained when the current schema can represent them. Tables with direct borders, non-solid fills, or mixed rich-text formatting remain fallback-only, as do charts with unsupported label scopes/types, custom axis semantics, trendlines/error bars, or subtype options. Unsupported tables keep their rendered SVG table; unsupported charts keep a baked preview or explicit placeholder. Both carry `data-pptx-native-status`, which `svg_quality_checker.py` and `svg_to_pptx.py --native-objects` report as a warning.

Exporter-canonical classic charts also recover canonical solid series/slice
colors and exact one- or two-paragraph title styling; two paragraphs retain
their `title` / `subtitle` roles. Slide-number fields resolve to the display
number defined by `firstSlideNum`; standalone master/layout SVGs retain their
literal field fallback because they are shared by multiple slides.

Image generation:

```bash
uvx ppt-master image-gen "A modern futuristic workspace"
uvx ppt-master image-gen --list-backends
uvx ppt-master analyze-images <project_path>/images
uvx ppt-master latex-render <project_path>
uvx ppt-master latex-render <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
```

Repository update:

```bash
uvx ppt-master update-repo
uvx ppt-master update-repo --skip-deps
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
