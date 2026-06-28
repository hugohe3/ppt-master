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
| Conversion | `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py` | [docs/conversion.md](./docs/conversion.md) |
| Project management | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py`, `template_fill_pptx.py`, `native_enhance_pptx.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `animation_config.py`, `notes_to_audio.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| Spec maintenance | `update_spec.py` | [docs/update_spec.md](./docs/update_spec.md) |
| Image tools | `image_gen.py`, `latex_render.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## High-Frequency Commands

Conversion:

```bash
uvx ppt-master pdf-to-md <file.pdf>
uvx ppt-master ppt-to-md <deck.pptx>
uvx ppt-master doc-to-md <file.docx>
uvx ppt-master excel-to-md <workbook.xlsx>
uvx ppt-master web-to-md <url>
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
- Prefer `svg_final/` over `svg_output/` when exporting

## Related Docs

- [Conversion Tools](./docs/conversion.md)
- [Project Tools](./docs/project.md)
- [SVG Pipeline Tools](./docs/svg-pipeline.md)
- [Image Tools](./docs/image.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Skill Entry](../SKILL.md)

_Last updated: 2026-04-09_
