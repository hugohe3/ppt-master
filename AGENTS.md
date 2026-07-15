# AGENTS.md

This file is the project entry point for general AI agents.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** This repository exists to generate presentations; SKILL.md is the authoritative workflow that owns project creation, role switching, serial execution, quality gates, post-processing, export, and every per-step command. The rest of this file only points to where related material lives — it never substitutes for SKILL.md.

## Project Overview

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → [Template] → Strategist confirmation stage → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

**Route selection authority**: [`skills/ppt-master/workflows/routing.md`](skills/ppt-master/workflows/routing.md) owns the complete route matrix. The hard boundaries below stay inline because they bypass or redirect the main pipeline and are the most expensive to misroute.

- Topic-only requests run [`topic-research`](skills/ppt-master/workflows/topic-research.md) before SKILL.md Step 1.
- Raw PPTX template plus new material/topic routes to [`template-fill-pptx`](skills/ppt-master/workflows/template-fill-pptx.md), not the SVG pipeline.
- Raw PPTX cannot be consumed as a Step 3 SVG template; run [`create-template`](skills/ppt-master/workflows/create-template.md) first and return with the generated template workspace root.
- PPTX beautify is strictly 1:1 page count/order and verbatim wording via [`beautify-pptx`](skills/ppt-master/workflows/beautify-pptx.md); any split/merge/drop/reorder routes to the main pipeline.
- Finished PPTX native enhancement uses [`native-enhance-pptx`](skills/ppt-master/workflows/native-enhance-pptx.md) and must not enter SVG regeneration.
- [`visual-review`](skills/ppt-master/workflows/visual-review.md), [`customize-animations`](skills/ppt-master/workflows/customize-animations.md), and [`generate-audio`](skills/ppt-master/workflows/generate-audio.md) are explicit-request workflows.

## Execution Requirements

- For standalone template creation (no source deck), read [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md).
- Technical SVG/PPT constraints live in [`skills/ppt-master/references/shared-standards.md`](skills/ppt-master/references/shared-standards.md).
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Markdown language consistency** — Markdown files under `skills/ppt-master/workflows/`, `skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) inside this repository.

## Command Quick Reference

Convenience summary only — full workflow in [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md).

```bash
# Source content conversion
python3 skills/ppt-master/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs_or_URLs...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Icon selection — copy chosen library icons into <project>/icons/ (missing names reported + non-zero = re-pick)
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name>...]

# Step 4 Strategist confirmation stage — interactive visual page (default auto-launch; chat fallback)
python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --daemon --wait

# Image tools and SVG quality check
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
# Formula rendering — manifest written by Strategist after typography confirmation:
python3 skills/ppt-master/scripts/latex_render.py <project_path>
python3 skills/ppt-master/scripts/latex_render.py <project_path> --dry-run
python3 skills/ppt-master/scripts/latex_render.py <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
python3 skills/ppt-master/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
python3 skills/ppt-master/scripts/image_gen.py --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
# Spot illustrations — slice one AI grid sheet into individual elements (see image-generator.md §4.3):
python3 skills/ppt-master/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names a,b,c --trim --alpha
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live --daemon
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
# Explicit create-template normalization: selected complex <g> -> one SVG picture asset / <image>
python3 skills/ppt-master/scripts/extract_svg_pictures.py "<svg_file>" --select "<group_id>" --resource-root "<workspace>" --images-dir "<workspace>/picture-assets" --inplace
# create-template review deck (workspace root may be global or project-scoped)
python3 skills/ppt-master/scripts/template_preview_pptx.py <template_workspace>
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>  # optional, only for custom object-level animation
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>  # optional, before re-export

# Existing PPTX native enhancement workflow — direct OOXML patch, no SVG conversion
python3 skills/ppt-master/scripts/native_enhance_pptx.py init <PPTX_file> --name <project_slug>
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate <project_path>
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply <project_path>

# Post-processing pipeline: run sequentially, one command at a time
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
# Mergeable dy-stacked paragraph blocks collapse into one editable text frame by default; add --no-merge to keep every line as its own frame (strict line fidelity). See SKILL.md Step 7.3.
```

## Core Directories

- `skills/ppt-master/SKILL.md` — main workflow authority.
- `skills/ppt-master/references/` — role definitions and technical specifications.
- `skills/ppt-master/scripts/` — runnable tool scripts.
- `skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `skills/ppt-master/templates/` — layout templates, chart templates, icon library, brand presets.
- `skills/ppt-master/workflows/` — standalone workflow files.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `examples/` — example projects.
- `projects/` — user project workspace.
