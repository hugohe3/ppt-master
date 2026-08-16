# AGENTS.md

This file is the project entry point for general AI agents.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** It owns global execution discipline and points to the route selector; after routing, the selected runtime authority owns its steps, gates, and commands. The rest of this file only points to where related material lives.

## Project Overview

PPT Master turns source material into natively editable DrawingML PPTX. Generate has two mutually exclusive runtimes: Default Strategist → Image_Generator → Executor, and self-contained Quick without separate strategy/confirmation. Beautify selects from explicit Quick intent; Image to PPTX always uses Quick.

**Route selection authority**: [`skills/ppt-master/workflows/routing.md`](skills/ppt-master/workflows/routing.md) owns the four top-level artifact routes: Generate PPTX, Create Template, Fill Native PPTX, and Enhance Native PPTX. Child workflows, profiles, stages, and governance documents refine one selected route; they are not competing top-level routes.

- Topic-only or fact-insufficient inputs run [`topic-research`](skills/ppt-master/workflows/stages/topic-research.md) inside the selected Generate profile's source intake; its facts URLs are not auto-expanded. After normal image search fails, one relevant webpage may be fetched as a source package and only reviewed selections enter the runtime image pool.
- Default Generate prepares template candidates internally in Step 3, then confirms the communication contract and free-design/template choice together in Stage 1. Template content stays unread until that confirmation; selected roots are installed before template-aware Stage 2. Quick skips this interaction.
- Raw PPTX template plus new material/topic routes to [`template-fill-pptx`](skills/ppt-master/workflows/template-fill-pptx.md), not the SVG pipeline.
- Raw PPTX cannot be consumed as a Generate template workspace; run [`create-template`](skills/ppt-master/workflows/create-template.md) first and return with the generated workspace root as a Stage-1 candidate. Never add Master/Layout structure directly to an existing PPTX/SVG; generate new structured SVG pages from the workspace.
- Explicit quick/fast or skip-strategy generation may use [`quick-generate`](skills/ppt-master/workflows/profiles/quick-generate.md): prepare sources/resources as needed, decide without interaction, omit Strategist/confirmation/spec/lock, hand-author `svg_output/`, pass its lockless final checker, and export.
- Recorded, self-running, or video-directed Generate work conditionally loads [`video-design`](skills/ppt-master/references/video-design.md) inside the selected Default or explicit Quick runtime before page planning. It changes scene, script, and motion design—not the runtime/profile or artifact route.
- PPTX beautify is a strict 1:1 Generate [`profile`](skills/ppt-master/workflows/profiles/beautify-pptx.md), not a separate route. Explicit Quick intent uses the Quick runtime; otherwise it uses Default. Any split/merge/drop/reorder disables Beautify and returns to ordinary Generate in the selected runtime.
- Page-image reconstruction uses the Codex-supported, Quick-only [`image-to-pptx`](skills/ppt-master/workflows/profiles/image-to-pptx.md) profile. Normalize input page frames; one frame becomes one slide. Restore text natively, reconstruct low-resolution graphics without changing identity, and derive registered clean-base/scene layers. Padded-bbox-disjoint objects may share a generated plate and become independent crops. Never use a full-slide screenshot skin. Other hosts are unsupported.
- Finished PPTX native enhancement uses [`native-enhance-pptx`](skills/ppt-master/workflows/native-enhance-pptx.md) and must not enter SVG regeneration.
- [`visual-review`](skills/ppt-master/workflows/stages/visual-review.md), [`customize-animations`](skills/ppt-master/workflows/stages/customize-animations.md), and [`generate-audio`](skills/ppt-master/workflows/stages/generate-audio.md) are supporting stages; their trigger rules remain explicit/conditional.

## Execution Requirements

- For any `brand`, `style`, `layout`, or `deck` workspace creation from PPTX/SVG, images/PDFs, documents/websites, brand assets, direct text, or mixed references, enter [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md); it keeps the fixed Create Template name and dispatches exactly one of [`create-brand`](skills/ppt-master/workflows/create-template/create-brand.md), [`create-style`](skills/ppt-master/workflows/create-template/create-style.md), [`create-layout`](skills/ppt-master/workflows/create-template/create-layout.md), or [`create-deck`](skills/ppt-master/workflows/create-template/create-deck.md).
- Always-on SVG constraints and shared visual-quality defaults live in [`skills/ppt-master/references/shared-standards-core.md`](skills/ppt-master/references/shared-standards-core.md). Default and Quick Generate always load [`svg-effects.md`](skills/ppt-master/references/svg-effects.md); other routes load it, [`native-data-interface.md`](skills/ppt-master/references/native-data-interface.md), and [`pptx-structure-interface.md`](skills/ppt-master/references/pptx-structure-interface.md) only when their documented execution triggers apply.
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Prompt decision ownership** — follow [`docs/rules/prompt-style.md`](docs/rules/prompt-style.md) §4.1. Default Strategist prepares project-local resources and Executor realizes them; Quick's current agent decides and prepares before SVG authoring. This is not downstream acquisition. Every project icon is prepared material; `icons.inventory` indexes the default plan's curated bundled pool, not page usage or an execution whitelist. Sounds follow [`animations.md`](skills/ppt-master/references/animations.md) §2.2.
- **Markdown language consistency** — follow [`docs/rules/language.md`](docs/rules/language.md): one language per file, mirroring the siblings in that directory; a non-English string may appear in an English file only as quoted content (user trigger text, sample values, rendered labels, proper nouns), never as the wording of a rule; never hard-code which language the model replies in. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) inside this repository.

## Command Quick Reference

Convenience summary only — route selection starts in [`SKILL.md`](skills/ppt-master/SKILL.md). Image to PPTX always uses [`quick-generate.md`](skills/ppt-master/workflows/profiles/quick-generate.md); Beautify uses it only when Quick is explicit, otherwise [`generate-pptx.md`](skills/ppt-master/workflows/generate-pptx.md).

```bash
# Source content conversion
python3 skills/ppt-master/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]

# Project management
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs_or_URLs...>
python3 skills/ppt-master/scripts/project_manager.py scaffold-spec <project_path>  # optional manual helper
python3 skills/ppt-master/scripts/project_manager.py scaffold-lock <project_path>  # optional manual helper
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>

# Icon selection — copy chosen library icons into <project>/icons/ (missing names reported + non-zero = re-pick)
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [<lib/name>...]

# Sounds
python3 skills/ppt-master/scripts/sound_sync.py list [--query term]
python3 skills/ppt-master/scripts/sound_sync.py <project_path> <namespace>/<id>...

python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --daemon
python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage1

# Image tools and SVG quality check
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
python3 skills/ppt-master/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
python3 skills/ppt-master/scripts/image_gen.py --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
python3 skills/ppt-master/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
# Spot illustrations — slice one AI grid sheet into individual elements (see image-generator.md §4.3):
python3 skills/ppt-master/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names a,b,c --trim --alpha
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live --daemon
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
# Shared create-template coordinate compaction before template validation
python3 skills/ppt-master/scripts/compact_svg_coordinates.py "<template_workspace>/templates" --inplace --keep-native-frames
# Explicit create-template normalization: selected complex <g> -> one SVG picture asset / <image>
python3 skills/ppt-master/scripts/extract_svg_pictures.py "<svg_file>" --select "<group_id>" --resource-root "<workspace>" --images-dir "<workspace>/picture-assets" --inplace
# Type A create-template mirror: validated authoring IR -> deterministic structured template workspace
python3 skills/ppt-master/scripts/mirror_template_materialize.py "<import_workspace>" "<empty_template_workspace>"
# create-template review deck (workspace root may be global or project-scoped)
python3 skills/ppt-master/scripts/template_preview_pptx.py <template_workspace>
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>  # optional, only for custom object-level animation
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>  # optional, before re-export

# Existing PPTX native enhancement workflow — direct OOXML patch, no SVG conversion
python3 skills/ppt-master/scripts/native_enhance_pptx.py init <PPTX_file> --name <project_slug>
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate <project_path>
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply <project_path>
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
