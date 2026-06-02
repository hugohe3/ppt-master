# CLAUDE.md

This file is the project entry point for Claude Code.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** This repository exists to generate presentations; SKILL.md is the authoritative workflow that owns project creation, role switching, serial execution, quality gates, post-processing, export, and every per-step command. The rest of this file only points to where related material lives — it never substitutes for SKILL.md.

## Project Overview

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML).

**Core Pipeline**: `Source Document → Create Project → [Template] → Strategist Eight Confirmations → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

> Topic-only requests with no source material: run the standalone [`topic-research`](skills/ppt-master/workflows/topic-research.md) workflow before SKILL.md Step 1 to gather web materials.
>
> Template fill: when the user provides an existing `.pptx` template plus text materials or a topic and asks to reuse the original PPT design or fill content back into it (for example, "fill this deck with the new content", "fill this back into the template", or "reuse this deck's design"), run the standalone [`template-fill-pptx`](skills/ppt-master/workflows/template-fill-pptx.md) workflow. This route edits PPTX directly and must not enter the SVG generation pipeline.
>
> Phase B resumption (split-mode execution): when the user opens a fresh chat and says "继续生成 projects/<x>" or similar, run the standalone [`resume-execute`](skills/ppt-master/workflows/resume-execute.md) workflow to enter Phase B (SVG generation + export) without re-running Phase A.
>
> Decks containing data charts: run the standalone [`verify-charts`](skills/ppt-master/workflows/verify-charts.md) workflow between the executor and post-processing steps to calibrate chart coordinates.
>
> Recorded narration / video export: run the standalone [`generate-audio`](skills/ppt-master/workflows/generate-audio.md) workflow after post-processing.
>
> Object-level animation tuning: when the user asks to change animation order, effect, timing, or a specific object's reveal behavior, run the standalone [`customize-animations`](skills/ppt-master/workflows/customize-animations.md) workflow. Default export already has global animations; do not create `animations.json` unless customization was requested.
>
> Live preview: any time the user mentions "live preview", "preview", "看效果", or wants to click/select a slide element, run [`live-preview`](skills/ppt-master/workflows/live-preview.md). Step 6 auto-starts it during generation; the workflow covers post-export re-entry and applying submitted annotations.
>
> Brand identity setup: when the user asks to "set up brand" / "建立品牌" / "做品牌规范", provides a brand asset (logo / brand site URL / branded PPTX / brand PDF), or wants to extract a brand from existing materials, run the standalone [`create-brand`](skills/ppt-master/workflows/create-brand.md) workflow. Output goes to `skills/ppt-master/templates/brands/<id>/`. Brands apply at SKILL.md Step 3 via the same explicit-path rule as layout templates — the user supplies the brand directory path to apply it; bare brand names never trigger.
>
> Visual self-check: only when the user explicitly requests a per-page visual review on the generated SVGs (e.g., "跑一下视觉自检 / 视觉回看 / 视觉 rubric", "visual review", "check each page visually"), run the standalone [`visual-review`](skills/ppt-master/workflows/visual-review.md) workflow between the executor and post-processing steps. The main pipeline does NOT invoke it automatically; do not infer or recommend it from deck size, model identity, or any other signal — user request is the only trigger.

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
python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <PDF_file>
python3 skills/ppt-master/scripts/source_to_md/doc_to_md.py <DOCX_or_other_file>
python3 skills/ppt-master/scripts/source_to_md/excel_to_md.py <XLSX_or_XLSM_file>
python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <PPTX_file>
python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

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
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>  # optional, only for custom object-level animation
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>  # optional, before re-export

# Post-processing pipeline: run sequentially, one command at a time
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
# Add --merge-paragraphs when the user wants paragraph-level editable text frames instead of one-per-line (default off, see SKILL.md Step 7.3).
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
