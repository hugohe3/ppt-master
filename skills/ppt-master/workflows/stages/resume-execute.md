---
description: Main-pipeline control stage for resuming execution in a fresh chat after planning completed.
---

# Resume Execute Stage

> Generate-PPTX control stage for a fresh execution session. Run when [`generate-pptx`](../generate-pptx.md) Step 1–5 completed in a previous chat and the user wants to continue with SVG generation + export. Loads project state from disk and runs Step 6 + Step 7 inside the already selected Generate route.

This stage is **context-independent**: it owns the execution session starting from a fresh chat — no upstream conversation context required. Persisted project artifacts replace the planning session's confirmation dialogue and image-acquisition history.

`validation/workflow.log` is a cold command/outcome audit log with optional
important manual entries, not persisted planning state. Do not open or replay
it while resuming. Use the real artifacts in Step 1 to establish current state;
inspect the log only when the user explicitly asks to review the prior run. Run
inherited Python commands normally; their shared CLI bootstrap records a
bounded material outcome selection automatically, not the full console stream.

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

Verify the two root planning artifacts exist before loading their contents:

| File | Required when | Reason |
|---|---|---|
| `<project_path>/design_spec.md` | Always | Upstream approved design narrative and §IX page outline; its complete read occurs after the Executor role core loads |
| `<project_path>/spec_lock.md` | Always | Downstream execution anchors and routing contract; its complete read follows the Design Spec |

If either file is missing, report it and stop this stage. Recover through
[`failure-recovery.md`](../governance/failure-recovery.md) §3; do not enter Step
6, read an orphan lock as authority, or invent a replacement artifact.

---

## Step 2: Load the Generate authority, proceed from Step 6

```
Read skills/ppt-master/workflows/generate-pptx.md
```

Then jump to `### Step 6: Executor Phase`. It first loads `executor-base.md`,
then applies that role core's context policy:

- Read the complete project Design Spec, then the complete `spec_lock.md`, once to establish the fresh execution context
- Resolve the effective Speaker Notes, Custom Animations, and Narration Audio
  outcomes from `design_spec.md §I`. Missing outcomes use the workflow defaults
  `enabled` / `disabled` / `disabled`; these production decisions never come
  from `spec_lock.md`

Before the first SVG, verify every conditional dependency now discoverable
from that retained pair:

| File / Directory | Required when | Reason |
|---|---|---|
| `<project_path>/notes/total.md` | Design Spec §X records a supplied final/literal narration script | Frozen verbatim narration input; never reconstruct it from the planning chat |
| `<project_path>/images/` plus files whose row status requires existence | `spec_lock images` references any image | `Existing` / `Generated` / `Sourced` files must exist; an absent `Needs-Manual` file remains allowed until the Step 7 readiness gate |
| `<project_path>/templates/` | `spec_lock page_layouts` references any | Layout / mirror prototypes required by execution |
| Resolver-returned Chart/Table SVG | `spec_lock page_visualizations` or legacy `page_charts` references a live Chart/Table key | Shared page-local SVG selected through the two live catalogs |

Resolve every live Chart/Table value through the shared catalog resolver.
Validate canonical `family/key` from `page_visualizations` directly; opt into
bare-key resolution only for a live Chart/Table value read from legacy
`page_charts`:

```bash
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  <family/key> [<family/key> ...]
python3 skills/ppt-master/scripts/visualization_recall.py validate \
  --legacy-bare <legacy-key> [<legacy-key> ...]
```

Require every returned SVG to exist. Never construct a path from the key,
guess a family directory, or prefer one registry. Failed, missing, or ambiguous
live resolution is a missing planning dependency and stops this stage. A
retired Structure bare key carries semantic intent only and requires no SVG;
recover its relationship from §IX, or return to Step 4 when §IX is insufficient.

If a conditional dependency is missing, stop before page authoring and recover
by artifact owner:

- Missing frozen `notes/total.md` when §X declares a final/literal script → return to Generate Step 4's prepared final narration branch; never rewrite the script from memory.
- Missing `images/`, or a file whose status requires existence → recover by provenance: an `Acquire Via: user` / `Status: Existing` file is a required manual artifact, so use `failure-recovery.md` §2 and wait for the user to restore that exact file; a template-bundled bitmap returns to [`generate-pptx`](../generate-pptx.md) Step 3 to restore the selected workspace; an AI, web, or slice output uses its matching row in `failure-recovery.md` §1 to reacquire or derive it. An absent `Needs-Manual` file is not a resume failure. Formula markers are SVG authoring content and never create a required image file.
- Missing `templates/` inputs → restore the selected workspace through [`generate-pptx`](../generate-pptx.md) Step 3 and [`apply-template-workspace`](apply-template-workspace.md). If the workspace is unavailable or invalid, run Create Template again rather than reconstructing a template inside this stage.

Then continue the documented pipeline:

- When §X records a final/literal narration script, read the verified frozen `notes/total.md` once and retain its page segments through SVG authoring and the late notes validation
- If resuming mid-deck, read the latest completed SVG and current image metadata after their required paths have been verified
- Read the remaining Step 6 construction core exactly as listed in [`generate-pptx.md`](../generate-pptx.md), then read one locked preset file or only the exact `*_references` of a custom synthesis; never reopen or glob the mode or visual-style catalogs, and load only the branches selected by the condition table
- For each page, make the mandatory Structure decision from retained §IX after its content/communication move is established and before any geometry; a `yes` result loads `executor-structure.md` before realization and creates no artifact or lock row
- Design Parameter Confirmation
- When structured, read the template Design Spec and each selected prototype once; retain unchanged references in the fresh context. A later bounded repair follows [`executor-base.md`](../../references/executor-base.md) §2.1 only while that context remains valid and uncompacted
- Generate pages sequentially from the retained planning artifacts. Use `page-context` only for the on-demand diagnostic/telemetry triggers in Executor §2.1, never as a routine pre-page load
- Quality Check Gate
- Speaker notes generation only when the effective Speaker Notes outcome is enabled
- Conditional custom-animation handling under the effective outcome,
  provenance, explicit instruction, and existing-sidecar rules
- Step 7: Post-processing & Export (conditional `total_md_split` → `finalize_svg`
  → `svg_to_pptx`; disabled speaker notes use `--no-notes`)
- After the base export, run `generate-audio` when the effective Narration Audio
  outcome is enabled; narration implies speaker notes are enabled

Reload the Generate authority and required execution references; do not reconstruct or replay the earlier planning conversation.

If the user gives a newer explicit instruction after final Stage 2, update only the
affected effective outcome and provenance in `design_spec.md §I`, then resume at
its owning step. Do not reopen Confirm UI or add the decision to
`spec_lock.md`. Before writing, apply Generate's single notes/audio dependency
gate; at export, apply its sidecar suppression rules.

**Source verification**: the execution session is fresh. Read only the relevant `sources/` passages needed to resolve explicit `Fact IDs` / source references or verify facts, quotes, names, and data required by the current §IX block. Follow [`executor-base.md`](../../references/executor-base.md) §2.1's content-vs-expression contract; source verification never authorizes a second outline. If §IX lacks executable content or evidence, stop and return to Generate Step 4 for Design Spec repair.

> Note: this stage does NOT duplicate Step 6 / Step 7 content. `generate-pptx.md` is the authoritative procedure; resume-execute only adds the resumption entry, sanity check, and source-verification guidance.

---

## Step 3: Hand-back

When Step 7 completes and `exports/<project_name>_<timestamp>.pptx` is produced, the stage ends. Report the export path to the user.

If the deck contains data charts, the [`verify-charts`](verify-charts.md) stage runs between Step 6 and Step 7 as documented in [`generate-pptx`](../generate-pptx.md); resume mode handles it the same way as continuous mode.
