# PPT Master Toolset

This directory contains user-facing scripts for conversion, project setup, SVG processing, export, and image generation.

## Directory Layout

- Top-level `scripts/`: runnable entry scripts
- `scripts/source_to_md/`: source-document → Markdown converters (`pdf_to_md.py`, `doc_to_md.py`, `ppt_to_md.py`, `web_to_md.py`, `web_to_md.cjs`)
- `scripts/image_backends/`: internal provider implementations used by `image_gen.py`
- `scripts/template_import/`: internal PPTX reference-preparation helpers used by `pptx_template_import.py`
- `scripts/svg_finalize/`: internal post-processing helpers used by `finalize_svg.py`
- `scripts/docs/`: topic-focused script documentation
- `scripts/assets/`: static assets consumed by scripts

## Quick Start

Typical end-to-end workflow:

```bash
uv run scripts/source_to_md/pdf_to_md.py <file.pdf>
# or
uv run scripts/source_to_md/ppt_to_md.py <deck.pptx>
uv run scripts/project_manager.py init <project_name> --format ppt169
uv run scripts/project_manager.py import-sources <project_path> <source_files...> --move
uv run scripts/total_md_split.py <project_path>
uv run scripts/finalize_svg.py <project_path>
uv run scripts/svg_to_pptx.py <project_path> -s final
```

Repository update:

```bash
uv run scripts/update_repo.py
```

## Script Index

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
| Conversion | `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `source_to_md/web_to_md.cjs` | [docs/conversion.md](./docs/conversion.md) |
| Project management | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| Spec maintenance | `update_spec.py` | [docs/update_spec.md](./docs/update_spec.md) |
| Image tools | `image_gen.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## High-Frequency Commands

Conversion:

```bash
uv run scripts/source_to_md/pdf_to_md.py <file.pdf>
uv run scripts/source_to_md/ppt_to_md.py <deck.pptx>
uv run scripts/source_to_md/doc_to_md.py <file.docx>
uv run scripts/source_to_md/web_to_md.py <url>
```

Project setup:

```bash
uv run scripts/project_manager.py init <project_name> --format ppt169
uv run scripts/project_manager.py import-sources <project_path> <source_files...> --move
uv run scripts/project_manager.py validate <project_path>
```

Template source import:

```bash
uv run scripts/pptx_template_import.py <template.pptx>
uv run scripts/pptx_template_import.py <template.pptx> --manifest-only
```

Post-processing and export:

```bash
uv run scripts/total_md_split.py <project_path>
uv run scripts/finalize_svg.py <project_path>
uv run scripts/svg_to_pptx.py <project_path> -s final
```

Image generation:

```bash
uv run scripts/image_gen.py "A modern futuristic workspace"
uv run scripts/image_gen.py --list-backends
uv run scripts/analyze_images.py <project_path>/images
```

Repository update:

```bash
uv run scripts/update_repo.py
uv run scripts/update_repo.py --skip-pip
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
- [AGENTS Guide](../../../AGENTS.md)

_Last updated: 2026-04-09_
