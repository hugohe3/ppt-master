# AGENTS.md

This file is the project entry point for general AI agents.

**You MUST read [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) before any PPT generation task or repo modification.** It owns global execution discipline and points to the route selector; after routing, the selected runtime authority owns its steps, gates, and commands.

**Repository execution anchor**: resolve the absolute repository root from this
file's supplied path and retain the absolute `skills/ppt-master` root before the
first command. Paths in this file are repository-relative notation only; invoke
them through those absolute roots, retain the absolute project path returned by
initialization, and never issue `cd skills/ppt-master` or `cd projects/...`.
When parsing machine-readable stdout, keep stderr separate and never place
`2>&1` upstream of a JSON or XML parser. Invoke each such command once per
concrete argument set; never encode its executable or flag list in scalar shell
strings, batch it through a shell loop, or add a downstream parser when the
command provides a compact view.

## Project Overview

PPT Master turns source material into natively editable DrawingML PPTX. Generate has two mutually exclusive runtimes: Default Strategist → Image_Generator → Executor, and self-contained Quick without separate strategy/confirmation. Beautify selects from explicit Quick intent; Image to PPTX always uses Quick.

**Route selection authority**: [`skills/ppt-master/workflows/routing.md`](skills/ppt-master/workflows/routing.md) owns the three top-level artifact routes: Generate PPTX, Create Template, and Edit Native PPTX. Child workflows, profiles, stages, and governance documents refine one selected route; they are not competing top-level routes.

- Topic-only or fact-insufficient inputs run [`topic-research`](skills/ppt-master/workflows/stages/topic-research.md) inside the selected Generate profile's source intake; its facts URLs are not auto-expanded. After normal image search fails, one relevant webpage may be fetched as a source package and only reviewed selections enter the runtime image pool.
- Default Generate prepares template candidates internally in Step 3, then confirms the communication contract and free-design/template choice together in Stage 1. Template content stays unread until that confirmation; selected roots are installed before template-aware Stage 2. Quick skips this interaction.
- Raw PPTX template plus new material/topic routes to [`edit-native-pptx`](skills/ppt-master/workflows/edit-native-pptx.md): a `pptx_to_svg.py --roundtrip` workspace where unchanged pages are referenced byte-for-byte and only planned pages are edited; it never enters Generate.
- Raw PPTX cannot be consumed as a Generate template workspace; run [`create-template`](skills/ppt-master/workflows/create-template.md) first and return with the generated workspace root as a Stage-1 candidate. Never add Master/Layout structure directly to an existing PPTX/SVG; generate new structured SVG pages from the workspace.
- Explicit quick/fast or skip-strategy generation uses [`quick-generate`](skills/ppt-master/workflows/profiles/quick-generate.md): prepare sources/resources as needed, decide without interaction, omit Strategist/confirmation/spec/lock, hand-author `svg_output/`, pass its lockless final checker, and export.
- Recorded, self-running, or video-directed Generate work conditionally loads [`video-design`](skills/ppt-master/references/video-design.md) inside the selected Default or explicit Quick runtime before page planning. It changes scene, script, and motion design—not the runtime/profile or artifact route.
- PPTX beautify is a strict 1:1 Generate [`profile`](skills/ppt-master/workflows/profiles/beautify-pptx.md), not a separate route. Explicit Quick intent uses the Quick runtime; otherwise it uses Default. Any split/merge/drop/reorder disables Beautify and returns to ordinary Generate in the selected runtime.
- Page-image reconstruction uses the Codex-supported, Quick-only [`image-to-pptx`](skills/ppt-master/workflows/profiles/image-to-pptx.md) profile. Normalize input page frames; one frame becomes one slide. Restore text natively, reconstruct low-resolution graphics without changing identity, and derive registered clean-base/scene layers. Padded-bbox-disjoint objects may share a generated plate and become independent crops. Never use a full-slide screenshot skin. Other hosts are unsupported.
- Finished PPTX notes / narration / timings / transitions with visible slides untouched also use [`edit-native-pptx`](skills/ppt-master/workflows/edit-native-pptx.md); export must report `rebuilt=0`.
- [`visual-review`](skills/ppt-master/workflows/stages/visual-review.md), [`customize-animations`](skills/ppt-master/workflows/stages/customize-animations.md), and [`generate-audio`](skills/ppt-master/workflows/stages/generate-audio.md) are supporting stages; their trigger rules remain explicit/conditional.

## Execution Requirements

- For any `brand`, `style`, `layout`, or `deck` workspace creation from PPTX/SVG, images/PDFs, documents/websites, brand assets, direct text, or mixed references, enter [`skills/ppt-master/workflows/create-template.md`](skills/ppt-master/workflows/create-template.md); it keeps the fixed Create Template name and dispatches exactly one of [`create-brand`](skills/ppt-master/workflows/create-template/create-brand.md), [`create-style`](skills/ppt-master/workflows/create-template/create-style.md), [`create-layout`](skills/ppt-master/workflows/create-template/create-layout.md), or [`create-deck`](skills/ppt-master/workflows/create-template/create-deck.md).
- Always-on SVG constraints and shared visual-quality defaults live in [`skills/ppt-master/references/shared-standards-core.md`](skills/ppt-master/references/shared-standards-core.md). Default and Quick Generate load [`svg-effects.md`](skills/ppt-master/references/svg-effects.md) on the executor-base routing trigger (the everyday effects live in the executor core); other routes load it, [`native-data-interface.md`](skills/ppt-master/references/native-data-interface.md), and [`pptx-structure-interface.md`](skills/ppt-master/references/pptx-structure-interface.md) only when their documented execution triggers apply.
- Canvas choices live in [`skills/ppt-master/references/canvas-formats.md`](skills/ppt-master/references/canvas-formats.md).
- Icon library details live in [`skills/ppt-master/templates/icons/README.md`](skills/ppt-master/templates/icons/README.md).

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`skills/ppt-master/references/`](skills/ppt-master/references/), Python under [`skills/ppt-master/scripts/`](skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Prompt content layers** — follow [`docs/rules/prompt-layers.md`](docs/rules/prompt-layers.md): a prompt file holds craft (design judgment) and the minimal contract the model writes; enforced grammar, importer behavior, and restated procedure live in [`scripts/docs/`](skills/ppt-master/scripts/docs/), one owner per rule with pointers elsewhere.
- **Prompt decision ownership** — follow [`docs/rules/ownership.md`](docs/rules/ownership.md); every cross-file rule has one owner recorded in [`docs/rules/rule-owners.md`](docs/rules/rule-owners.md). Default Strategist prepares project-local resources and Executor realizes them; Quick's current agent decides and prepares before SVG authoring. This is not downstream acquisition. Every project icon is prepared material; `icons.inventory` indexes the default plan's curated bundled pool, not page usage or an execution whitelist. Sounds follow [`animations.md`](skills/ppt-master/references/animations.md) §2.2.
- **Markdown language consistency** — follow [`docs/rules/language.md`](docs/rules/language.md): one language per file, mirroring the siblings in that directory; a non-English string may appear in an English file only as quoted content (user trigger text, sample values, rendered labels, proper nouns), never as the wording of a rule; never hard-code which language the model replies in. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize [`skills/ppt-master/SKILL.md`](skills/ppt-master/SKILL.md) inside this repository.

## Command Quick Reference

Convenience summary only — route selection starts in [`SKILL.md`](skills/ppt-master/SKILL.md). Image to PPTX always uses [`quick-generate.md`](skills/ppt-master/workflows/profiles/quick-generate.md); Beautify uses it only when Quick is explicit, otherwise [`generate-pptx.md`](skills/ppt-master/workflows/generate-pptx.md).

```bash
python3 skills/ppt-master/scripts/source_to_md.py <file_or_URL_or_dir> [...]          # source conversion
python3 skills/ppt-master/scripts/project_manager.py init <project_name>              # --format only for an exact registered canvas
python3 skills/ppt-master/scripts/project_manager.py import-sources <project_path> <sources...>
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <lib/name> [...]        # missing names -> non-zero = re-pick
python3 skills/ppt-master/scripts/confirm_ui/server.py <project_path> --daemon        # then --wait-only --wait-stage stage1
python3 skills/ppt-master/scripts/analyze_images.py <project_path>/images
python3 skills/ppt-master/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json   # in-pipeline AI images, even for 1
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --live --daemon
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path> --canonical-authoring --stage final --json   # Quick adds --quick-generate; --json writes the report the exporter reads, stdout stays the summary
python3 skills/ppt-master/scripts/pptx_to_svg.py <source.pptx> -o projects/<slug>_<YYYYMMDD> --inheritance-mode both --roundtrip   # Edit Native PPTX
python3 skills/ppt-master/scripts/svg_to_pptx.py projects/<slug>_<YYYYMMDD> --roundtrip
```

Every other command (sound sync, slicing, template materialization and preview, animation config, authoring-view refresh) is listed by the route or stage that owns it and in [`svg-pipeline.md`](skills/ppt-master/scripts/docs/svg-pipeline.md).

For Generate PPTX serial post-processing and export, follow [`generate-pptx.md`](skills/ppt-master/workflows/generate-pptx.md) Step 7 exactly; Edit Native PPTX exports through its own §7. See [`svg-pipeline.md`](skills/ppt-master/scripts/docs/svg-pipeline.md) for tool flags and behavior.

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
- `projects/` — user project workspace.
