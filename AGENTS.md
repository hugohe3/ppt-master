# AGENTS.md

This file is the project entry point for general AI agents.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** It owns global execution discipline and points to the route selector; after routing, the selected route authority owns its steps, gates, and commands. The rest of this file only points to where related material lives.

## Project Overview

PPT Master is an AI-driven presentation generation system. Multi-role collaboration (Strategist → Image_Generator → Executor) converts source documents (PDF/DOCX/URL/Markdown) into natively editable PPTX with real PowerPoint shapes (DrawingML). The Generate route owns its pipeline sequence.

**Route selection authority**: [`skills/ppt-master/workflows/routing.md`](skills/ppt-master/workflows/routing.md) owns the four top-level artifact routes: Generate PPTX, Create Template, Fill Native PPTX, and Enhance Native PPTX. Child workflows, profiles, stages, and governance documents refine one selected route; they are not competing top-level routes.

- Topic-only or fact-insufficient inputs run [`topic-research`](skills/ppt-master/workflows/stages/topic-research.md) in Generate Step 1; facts only, no images.
- Raw PPTX template plus new material/topic routes to [`template-fill-pptx`](skills/ppt-master/workflows/template-fill-pptx.md), not the SVG pipeline.
- Raw PPTX cannot be consumed as a Generate Step 3 SVG template; run [`create-template`](skills/ppt-master/workflows/create-template.md) first and return with the generated template workspace root. Never add Master/Layout structure directly to an existing PPTX/SVG; generate new structured SVG pages from the workspace.
- PPTX beautify is a strict 1:1 main-generation [`profile`](skills/ppt-master/workflows/profiles/beautify-pptx.md), not a separate route; any split/merge/drop/reorder uses the default main-pipeline policy.
- Finished PPTX native enhancement uses [`native-enhance-pptx`](skills/ppt-master/workflows/native-enhance-pptx.md) and must not enter SVG regeneration.
- [`visual-review`](skills/ppt-master/workflows/stages/visual-review.md), [`customize-animations`](skills/ppt-master/workflows/stages/customize-animations.md), and [`generate-audio`](skills/ppt-master/workflows/stages/generate-audio.md) are supporting stages; their trigger rules remain explicit/conditional.

## Execution Requirements

- For any `brand`, `layout`, or `deck` workspace creation from PPTX/SVG, images/PDFs, documents/websites, brand assets, direct text, or mixed references, enter [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md); it keeps the fixed Create Template name and dispatches exactly one of [`create-brand`](skills/ppt-master/workflows/create-template/create-brand.md), [`create-layout`](skills/ppt-master/workflows/create-template/create-layout.md), or [`create-deck`](skills/ppt-master/workflows/create-template/create-deck.md).
- Always-on SVG constraints live in [`skills/ppt-master/references/shared-standards-core.md`](skills/ppt-master/references/shared-standards-core.md). Load [`svg-effects.md`](skills/ppt-master/references/svg-effects.md), [`native-data-interface.md`](skills/ppt-master/references/native-data-interface.md), and [`pptx-structure-interface.md`](skills/ppt-master/references/pptx-structure-interface.md) only when their documented execution triggers apply.
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Prompt decision ownership** — follow [`docs/rules/prompt-style.md`](docs/rules/prompt-style.md) §4.1: Strategist readies every selected resource; Executor uses only that inventory and owns realization. Never move acquisition or reselection downstream.
- **Markdown language consistency** — Markdown files under `skills/ppt-master/workflows/`, `skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) inside this repository.

## Command Quick Reference

Convenience summary only — route selection starts in [`SKILL.md`](skills/ppt-master/SKILL.md); the full SVG-generation workflow is [`generate-pptx.md`](skills/ppt-master/workflows/generate-pptx.md).

```bash
# Source content conversion
uvx ppt-master source-to-md <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]

# Project management
uvx ppt-master project init <project_name> --format ppt169
uvx ppt-master project import-sources <project_path> <source_files_or_dirs_or_URLs...> --move
uvx ppt-master project scaffold-spec <project_path>  # optional manual helper
uvx ppt-master project scaffold-lock <project_path>  # optional manual helper
uvx ppt-master project validate <project_path>

# Icon selection — copy chosen library icons into <project>/icons/ (missing names reported + non-zero = re-pick)
uvx ppt-master icon-sync <project_path> <lib/name> [<lib/name>...]

# Step 4 Strategist confirmation stage — interactive visual page (default auto-launch; chat fallback)
uvx ppt-master confirm-ui <project_path> --daemon --wait

# Image tools and SVG quality check
uvx ppt-master analyze-images <project_path>/images
# Formula rendering — manifest written by Strategist after typography confirmation:
uvx ppt-master latex-render <project_path>
uvx ppt-master latex-render <project_path> --dry-run
uvx ppt-master latex-render <project_path> --providers codecogs,quicklatex,mathpad,wikimedia
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
uvx ppt-master image-gen --manifest <project_path>/images/image_prompts.json
uvx ppt-master image-gen --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
uvx ppt-master image-gen "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
# Spot illustrations — slice one AI grid sheet into individual elements (see image-generator.md §4.3):
uvx ppt-master slice-images <project_path>/images/<sheet>.png --grid RxC --names a,b,c --trim --alpha
uvx ppt-master confirm-ui <project_path> --live --daemon
uvx ppt-master svg-quality-check <project_path>
# Shared create-template coordinate compaction before template validation
uvx ppt-master compact-svg-coordinates "<template_workspace>/templates" --inplace --keep-native-frames
# Explicit create-template normalization: selected complex <g> -> one SVG picture asset / <image>
uvx ppt-master extract-svg-pictures "<svg_file>" --select "<group_id>" --resource-root "<workspace>" --images-dir "<workspace>/picture-assets" --inplace
# Type A create-template mirror: validated authoring IR -> deterministic structured template workspace
uvx ppt-master mirror-template-materialize "<import_workspace>" "<empty_template_workspace>"
# create-template review deck (workspace root may be global or project-scoped)
uvx ppt-master template-preview-pptx <template_workspace>
uvx ppt-master animation-config scaffold <project_path>  # optional, only for custom object-level animation
uvx ppt-master animation-config validate <project_path>  # optional, before re-export

# Existing PPTX native enhancement workflow — direct OOXML patch, no SVG conversion
uvx ppt-master native-enhance-pptx init <PPTX_file> --name <project_slug>
uvx ppt-master native-enhance-pptx validate <project_path>
uvx ppt-master native-enhance-pptx apply <project_path>
```

For serial post-processing and export, follow [`generate-pptx.md`](skills/ppt-master/workflows/generate-pptx.md) Step 7 exactly. See [`svg-pipeline.md`](skills/ppt-master/scripts/docs/svg-pipeline.md) for tool flags and behavior.

## Core Directories

- `skills/ppt-master/SKILL.md` — global discipline and route-entry authority.
- `skills/ppt-master/workflows/generate-pptx.md` — Generate PPTX Step 1–7 authority.
- `skills/ppt-master/references/` — role cores plus conditionally loaded role and technical modules.
- `skills/ppt-master/scripts/` — runnable tool scripts.
- `skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `skills/ppt-master/templates/` — layout templates, chart templates, icon library, brand presets.
- `skills/ppt-master/workflows/` — top-level route authorities plus supporting child workflows, profiles, stages, and governance runbooks.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `examples/` — example projects.
- `projects/` — user project workspace.
