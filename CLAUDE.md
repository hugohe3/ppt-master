# CLAUDE.md

This file provides a project overview for Claude Code. Before executing PPT generation tasks, **you MUST first read `skills/ppt-master/SKILL.md`** for the complete workflow and rules.

## Project Overview

PPT Master is an AI-driven presentation generation system. Through multi-role collaboration (Strategist → Image_Generator → Executor), it converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → Template Option → Strategist Eight Confirmations → [Image_Generator] → Executor → Post-processing → Export PPTX`

## Common Commands

```bash
# Source content conversion
python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF_file>
python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX_or_other_file>   # Requires: pandoc (DOCX/EPUB/HTML/LaTeX/RST/etc.)
python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>
node skills/ppt-master/scripts/source_to_md/web_to_md.cjs <URL>

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Image tools
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images

# SVG quality check
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>

# Post-processing pipeline (MUST run sequentially, one at a time — NEVER batch)
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
# ✅ Confirm no errors before running the next command
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
# ✅ Confirm no errors before running the next command
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final
# Default: generates two files — native shapes (.pptx) + SVG reference (_svg.pptx)
# Use --only native  to skip SVG reference version
# Use --only legacy  to only generate SVG image version
```

## Architecture

- `skills/ppt-master/references/` — AI role definitions and technical specifications
- `skills/ppt-master/scripts/` — Runnable tool scripts
- `skills/ppt-master/scripts/docs/` — Topic-focused script docs
- `skills/ppt-master/templates/` — Layout templates, chart templates, 640+ vector icons
- `examples/` — Example projects
- `projects/` — User project workspace

## SVG Technical Constraints (Non-negotiable)

**Banned features**: `clipPath` | `mask` | `<style>` | `class` | external CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>` | `<symbol>+<use>` (`id` inside `<defs>` is a legitimate reference and is NOT banned)

**PPT compatibility alternatives**:

| Banned | Alternative |
|--------|-------------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | Set opacity on each child element individually |
| `<image opacity>` | Overlay with a mask layer |
| `marker-end` arrows | `<polygon>` triangles |

## Canvas Format Quick Reference

| Format | viewBox |
|--------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| Xiaohongshu (RED) | `0 0 1242 1660` |
| WeChat Moments | `0 0 1080 1080` |
| Story | `0 0 1080 1920` |

## Post-processing Notes

- **NEVER** use `cp` as a substitute for `finalize_svg.py`
- **NEVER** export directly from `svg_output/` — MUST export from `svg_final/` (use `-s final`)
- Do NOT add extra flags like `--only` to the post-processing commands
- **NEVER** run the three post-processing steps in a single code block or single shell invocation
