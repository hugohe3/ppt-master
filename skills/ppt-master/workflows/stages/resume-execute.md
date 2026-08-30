---
description: Main-pipeline control stage for resuming execution in a fresh chat after planning completed.
---

# Resume Execute Stage

> Generate-PPTX control stage for a fresh execution session: [`generate-pptx`](../generate-pptx.md) Steps 1–5 completed in a previous chat and the user wants SVG generation + export. Loads project state from disk and runs Steps 6–7 inside the already selected Generate route.

Context-independent: persisted project artifacts replace the planning session's confirmation dialogue and image-acquisition history. `validation/workflow.log` is a cold audit log, not planning state — never open or replay it while resuming; inspect it only when the user asks to review the prior run.

## When to Run

The user opens a new chat naming a project path with continuation intent — "继续生成 projects/<name>", "resume execution projects/<name>", or a project path plus any 继续 / 恢复 / 接着做 semantic. **Prerequisite**: planning completed in that project, verified by file presence in Step 1; never auto-trigger planning on missing state.

---

## Step 1: Sanity check

`<project_path>/design_spec.md` (approved narrative and §IX outline) and `<project_path>/spec_lock.md` (execution anchors and routing contract) must both exist; their complete reads happen after the Executor role core loads. If either is missing, stop and recover through [`failure-recovery.md`](../governance/failure-recovery.md) §3 — never enter Step 6, treat an orphan lock as authority, or invent a replacement.

---

## Step 2: Load the Generate authority, proceed from Step 6

Read `skills/ppt-master/workflows/generate-pptx.md` and jump to `### Step 6: Executor Phase`, which loads `executor-base.md` and applies its context policy: read the complete Design Spec, then the complete lock, once; resolve the effective Speaker Notes / Custom Animations / Narration Audio outcomes from `design_spec.md §I` (missing outcomes default `enabled` / `disabled` / `disabled`; never from the lock).

Before the first SVG, verify every conditional dependency discoverable from that pair:

| File / Directory | Required when | Recovery when missing |
|---|---|---|
| `notes/total.md` | §X records a supplied final/literal narration script | Return to Step 4's prepared final narration branch; never rewrite the script from memory |
| `images/` plus files whose row status requires existence (`Existing` / `Generated` / `Sourced`; an absent `Needs-Manual` file is allowed until the Step 7 gate) | `spec_lock images` references any image | By provenance: `Acquire Via: user` / `Existing` is a required manual artifact (`failure-recovery.md` §2, wait for the exact file); a template-bundled bitmap returns to Step 3 to restore the workspace; AI, web, or slice output uses its `failure-recovery.md` §1 row. Formula markers never create a required image file |
| `templates/` | `spec_lock page_layouts` references any prototype | Restore the workspace through Step 3 and [`apply-template-workspace`](apply-template-workspace.md); if unavailable or invalid, run Create Template again rather than reconstructing a template here |
| Resolver-returned Chart/Table SVG | `page_visualizations` or legacy `page_charts` references a live key | Failed, missing, or ambiguous resolution is a missing planning dependency and stops this stage |

Resolve every live Chart/Table value through the shared resolver — canonical `family/key` directly, `--legacy-bare` only for a value read from legacy `page_charts` — and require every returned SVG to exist; never construct a path from the key. A retired Structure bare key is semantic intent only: recover it from §IX or return to Step 4 when §IX is insufficient.

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate <family/key> [<family/key> ...]
python3 skills/ppt-master/scripts/visualization_recall.py validate --legacy-bare <legacy-key> [...]
```

Then continue the documented Step 6–7 pipeline exactly as `generate-pptx.md` lists it: read the frozen `notes/total.md` once when §X declares a final/literal script; when mid-deck, read the latest completed SVG and current image metadata after their paths are verified; read the Step 6 construction core and one locked preset file or only the exact `*_references` of a custom, never reopening the mode or visual-style catalogs; load only the branches the condition table selects; make the per-page Structure decision from retained §IX before any geometry; when structured, read the template Design Spec and each selected prototype once. Use `page-context` only for explicit diagnostics or an unresolved path-SHA question ([`artifact-ownership.md`](../../references/artifact-ownership.md) §1), never as a routine pre-page load. Then the quality gate, conditional notes, conditional custom animation, Step 7 (`total_md_split` → `finalize_svg` → `svg_to_pptx`; disabled notes use `--no-notes`), and `generate-audio` when Narration Audio is enabled.

A newer explicit instruction after final Stage 2 updates only its effective outcome and provenance in `design_spec.md §I`, then resumes at the owning step — no Confirm UI, no lock entry; apply Generate's notes/audio dependency gate before writing and its sidecar suppression rules at export.

**Source verification**: read only the `sources/` passages needed to resolve explicit `Fact IDs` / source references or verify facts, quotes, names, and data required by the current §IX block, under [`executor-base.md`](../../references/executor-base.md) §2.1's content-vs-expression contract; verification never authorizes a second outline. If §IX lacks executable content, stop and return to Step 4 for Design Spec repair.

> This stage does not duplicate Steps 6–7; `generate-pptx.md` is the authoritative procedure. Resume adds only the entry, sanity check, and source-verification guidance.

---

## Step 3: Hand-back

When Step 7 produces `exports/<project_name>_<timestamp>.pptx`, the stage ends; report the export path. [`verify-charts`](verify-charts.md) runs between Steps 6 and 7 exactly as in continuous mode.
