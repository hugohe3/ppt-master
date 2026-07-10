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
| SVG pipeline | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
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

Post-processing and export:

```bash
python3 scripts/extract_svg_assets.py <svg_dir> --icons-dir <icons_dir> --inplace --id-prefix <prefix>  # optional: shrink imported/reference SVGs before AI review
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

`finalize_svg.py` optimizes raster images by default using `2x` display pixels and max `2560px`. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: only oversized full source images are reduced to max `2560px`, so later PowerPoint resizing keeps more image detail. Use `svg_to_pptx.py --image-sizing display --image-scale 2` only for aggressive size reduction, or `--no-image-optimize` when the native PPTX must embed original image bytes.

Native `svg_to_pptx.py` also defaults to `--pptx-structure baseline`: the generated deck keeps a standard master/layout relationship and promotes the strict-majority identical native slide background into the slide master (minority slides keep their own overriding background). A shared leading prefix of top-level SVG elements with exact chrome id tokens such as `logo`, `footer`, `header`, `watermark`, `chrome`, `pageNumber`, or `slideNumber` may also be promoted when its generated OOXML is identical on a strict majority of slides, it is not referenced by slide timing, and moving it behind slide-local content preserves z-order; image relationships are copied to the master. Minority slides such as covers keep every shape slide-local and are bound to a generated `Cover` layout (`showMasterSp="0"`) that hides the promoted master chrome. Baseline additionally prunes base-template slide layouts that no generated slide references, and swaps `pageNumber`/`slideNumber` chrome text for an auto-updating slide-number field when the text exactly equals the slide's display number. Use `--pptx-structure flat` when all generated backgrounds and chrome must remain slide-local for debugging or comparison.

`pptx_to_svg.py` annotates supported unmerged tables and conservative classic-chart caches with `data-pptx-native` metadata. Source table-style inheritance, supported solid cell fills/basic text formatting, chart title/legend/axis titles, and plot-level data-label flags for area/bar/column/line charts are retained when the current schema can represent them. Tables with direct borders, non-solid fills, or mixed rich-text formatting remain fallback-only, as do charts with unsupported label scopes/types, custom axis semantics, trendlines/error bars, or subtype options. Unsupported tables keep their rendered SVG table; unsupported charts keep a baked preview or explicit placeholder. Both carry `data-pptx-native-status`, which `svg_quality_checker.py` and `svg_to_pptx.py --native-objects` report as a warning.

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
- Use `svg_output/` for native export and `svg_final/` for SVG snapshot/preview export

## Related Docs

- [Conversion Tools](./docs/conversion.md)
- [Project Tools](./docs/project.md)
- [SVG Pipeline Tools](./docs/svg-pipeline.md)
- [Image Tools](./docs/image.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Skill Entry](../SKILL.md)

_Last updated: 2026-07-10_
