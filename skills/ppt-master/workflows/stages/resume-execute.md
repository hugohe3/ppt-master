---
description: Main-pipeline control stage for resuming execution in a fresh chat after planning completed.
---

# Resume Execute Stage

> Generate-PPTX control stage for a fresh execution session. Run when [`generate-pptx`](../generate-pptx.md) Step 1–5 completed in a previous chat and the user wants to continue with SVG generation + export. Loads project state from disk and runs Step 6 + Step 7 inside the already selected Generate route.

This stage is **context-independent**: it owns the execution session starting from a fresh chat — no upstream conversation context required. Persisted project artifacts replace the planning session's confirmation dialogue and image-acquisition history.

## When to Run

The user opens a new chat and gives a phrase that names a project path and signals continuation. Recognize any of:

| Pattern | Example |
|---|---|
| "继续生成 projects/<project_name>" | "继续生成 projects/ppt169_joe_hisaishi" |
| "resume execution projects/<project_name>" | "resume execution projects/ppt169_joe_hisaishi" |
| Project path + any "继续 / 恢复 / 继续做 / 接着做" semantic | "把 projects/ppt169_joe_hisaishi 继续做完" |

**Prerequisite**: the planning session must have completed in the named project. Verified by file presence in Step 1; do NOT auto-trigger planning on missing state.

---

## Step 1: Sanity check

Verify the project's planning-session artifacts before doing anything else:

| File / Directory | Required when | Reason |
|---|---|---|
| `<project_path>/spec_lock.md` | Always | Strategist's execution contract; `page-context` projects its current-page values |
| `<project_path>/design_spec.md` | Always | Section IX page outline; `page-context` projects the current page block |
| `<project_path>/images/` plus files whose row status requires existence | `spec_lock images` references any image | `Existing` / `Generated` / `Sourced` / `Rendered` files must exist; an absent `Needs-Manual` file remains allowed until the Step 7 readiness gate |
| `<project_path>/templates/` | `spec_lock page_layouts` references any | Layout / mirror prototypes required by execution |
| `skills/ppt-master/templates/charts/` | `spec_lock page_charts` references any | Shared chart SVGs selected by key |

If any required artifact is missing, report it and stop this stage. Do not enter Step 6 or invent a replacement artifact. Recover by artifact owner:

- Missing `design_spec.md` / `spec_lock.md` → use [`failure-recovery.md`](../governance/failure-recovery.md) §3.
- Missing `images/`, or a file whose status requires existence → recover by provenance: an `Acquire Via: user` / `Status: Existing` file is a required manual artifact, so use `failure-recovery.md` §2 and wait for the user to restore that exact file; a template-bundled bitmap returns to [`generate-pptx`](../generate-pptx.md) Step 3 to restore the selected workspace; an AI, web, formula, or slice output uses its matching row in `failure-recovery.md` §1 to reacquire, rerender, or derive it. An absent `Needs-Manual` file is not a Step 1 failure.
- Missing `templates/` inputs → restore the selected workspace through [`generate-pptx`](../generate-pptx.md) Step 3 and [`apply-template-workspace`](apply-template-workspace.md). If the workspace is unavailable or invalid, run Create Template again rather than reconstructing a template inside this stage.

---

## Step 2: Load the Generate authority, proceed from Step 6

```
Read skills/ppt-master/workflows/generate-pptx.md
```

Then jump to `### Step 6: Executor Phase` and run the documented pipeline:

- Read the Step 6 flat core (`executor-base`, `shared-standards-core`, and the locked preset mode / visual-style files); for custom directions, reload every optional `*_references` file from `spec_lock.md` before applying the behavior, then only the branches selected by the condition table
- Design Parameter Confirmation
- Read the project Design Spec and, when structured, the template Design Spec once; retain both in the fresh execution context
- Per-page `python3 skills/ppt-master/scripts/project_manager.py page-context <project_path> P<NN> --record-usage` load + sequential page generation; the stable anchor projection repeats intentionally without becoming a color/font allowlist, while each prototype/chart SVG is loaded only before its first use or after its SHA changes
- Quality Check Gate
- Speaker notes generation
- Step 7: Post-processing & Export (`total_md_split` → `finalize_svg` → `svg_to_pptx`)

Reload the Generate authority and required execution references; do not reconstruct or replay the earlier planning conversation.

**Source verification**: the execution session is fresh, but `design_spec.md §IX` already owns the complete approved page wording. Read only the relevant `sources/` passages needed to resolve explicit `Fact IDs` / source references or verify exact facts, quotes, names, and data already required by the current §IX block. Never turn §IX back into a skeleton, add new claims or details, or independently rewrite its content. If §IX lacks executable wording or evidence, stop and return to Generate Step 4 for Design Spec repair.

> Note: this stage does NOT duplicate Step 6 / Step 7 content. `generate-pptx.md` is the authoritative procedure; resume-execute only adds the resumption entry, sanity check, and source-verification guidance.

---

## Step 3: Hand-back

When Step 7 completes and `exports/<project_name>_<timestamp>.pptx` is produced, the stage ends. Report the export path to the user.

If the deck contains data charts, the [`verify-charts`](verify-charts.md) stage runs between Step 6 and Step 7 as documented in [`generate-pptx`](../generate-pptx.md); resume mode handles it the same way as continuous mode.
