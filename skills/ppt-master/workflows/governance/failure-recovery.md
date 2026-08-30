---
description: Cross-route stop/continue governance with a concrete recovery matrix and resume map for Generate PPTX.
---

# Failure Recovery Governance

Global stop/continue rules for all three routes plus concrete Generate PPTX handling. §2 applies across routes; §1 and §3 apply only to Generate PPTX. Owning route and stage documents may add narrower handling but never weaken these rules or duplicate the matrix.

**Hard rule**: a failed required artifact blocks the next gate. A failed convenience surface falls back to the canonical channel and does not block the route.

---

## 1. Generate PPTX Recovery Matrix

| Failure point | Blocking | Automatic recovery | User intervention | Resume entry |
|---|---:|---|---|---|
| Confirm UI launch failure | No | Re-check `confirm_ui/result.json` once, then chat fallback | No | [`generate-pptx`](../generate-pptx.md) Step 4 chat confirmation |
| Confirm UI wait timeout | No, if no final result yet | Re-check `result.json` once; server cleanup stays mandatory | Only if the user still wants the page | Step 4 same stage or chat fallback |
| User switches from Confirm UI to chat mid-stage | Yes until the current stage is confirmed | Follow the in-run switch in [`confirm-surface.md`](../../references/confirm-surface.md): keep persisted confirmed stages, continue the current and remaining stages in chat, never relaunch UI | Confirm in chat unless delegated | Step 4 current chat stage |
| Stage 1 completed, then interrupted while UI remains selected | Yes until final Stage 2 is confirmed | Read Stage 1 `result.json`, derive a fresh `recommendations.stage2.json` without changing Stage 1, then `--wait-only` | Usually no | Step 4 final Stage 2 write/wait |
| Missing final confirmation | Yes | None | User confirms or changes the values | Step 4 final confirmation |
| Final confirmed value or later explicit override missing, changed, or weakened in `design_spec.md` | Yes | Repair from the retained final-confirmation object plus any newer explicit instruction; only a fresh recovery turn with no retained state reads persisted evidence once | Only when the value genuinely cannot be honored | Step 4 Gate 1 |
| `spec_lock.md` changes confirmed identity or omits a required anchor/routing decision | Yes | Re-author the affected rows from the completed Design Spec and context; do not enumerate page-local literals | No unless the Design Spec is incomplete | Step 4 Gate 2 |
| Execution exposes a missing Strategist-owned role/plan detail | Yes for the page | Repair the Design Spec/lock fragments under [`executor-base.md`](../../references/executor-base.md) §2.1 | Only if confirmed intent changes | Step 4 Gate 1/2 → Step 6 current page |
| Execution context is fresh, resumed, compacted, external, or unknown | Yes until rebuilt | Read the complete Design Spec, then lock, once; reload triggered inputs and the latest completed SVG when mid-deck | No | Step 6 current page |
| `apply-template-workspace` rejects a legacy or incomplete template | Yes | Stop template consumption; create a new workspace through Create Template from the original PPTX/reference and return with its exact root | Only when source evidence or template choices are unavailable | Create Template → Step 4 Stage 1 |
| Native formula marker validation or LaTeX compilation failure | Yes for the page | Repair the marker or LaTeX and rerun the checker; no formula-image fallback | Clarify the equation only when the source is ambiguous | Active SVG authoring step |
| AI image generation failure | Default blocks at the recovery decision; Quick does not | Default `auto`: try A → B, then ask once to repair/retry, generate manually, or cancel/replan; explicit `api` / `host-native`: retry that path, then ask. Quick removes exhausted AI/dependent-slice jobs, replans with native text/SVG or prepared non-AI assets, and continues | Default chooses one outcome; manual files still required before export | Default: Step 5 decision, Step 4 plan repair, or Step 7 image readiness gate; Quick: current resource plan |
| Web image search/download failure | No | Adjust query/source per image-searcher rules, then `Needs-Manual` if unresolved | Only if required with no substitute | Step 5 |
| Slice sheet missing | Yes for derived slice rows | Wait for the parent sheet; run `slice_images.py`; rerun image analysis | Yes when the sheet was manual/offline | Step 5 slice handling / Step 7 image readiness gate |
| Strict-alpha slice failure | Yes for every named output | Return the parent to preparation; correct an evidenced key/tolerance mismatch, then enlarge cells or split incompatible shape families and regenerate; a parent never substitutes for its slices | Only after automated recovery is exhausted | Quick §2 resource closure / Default Step 5 |
| Residual `Pending` or `Failed` image row before Executor | Yes | Re-run the owning path; Default AI follows its three-outcome decision and reaches `Needs-Manual` only after manual confirmation; Quick follows its no-AI replan | Only when the owning rule requires a new choice or file | Step 5 terminal-state check |
| User replaces/adds images after analysis | No | Re-run `analyze_images.py` before reading image facts | No | Step 4/5/6 image-fact read |
| Live preview fails to start / closed by user | No | Continue generation; report unavailability | Only if the user requires browser preview | Step 6, or `live-preview` Step 1 on request |
| Browser annotations submitted during generation | No | Defer application until after Step 7 | User asks to apply | `live-preview` Step 2 |
| `svg_quality_checker.py` error | Yes | Review the complete issue set from one unfiltered run; fix all errors and selected warnings in one consolidated pass, then one verification rerun; a remaining failure is the next batch — never check between individual fixes | No unless a required asset is missing | Step 6 Visual Construction |
| `svg_quality_checker.py` warning | No | Continue without mandatory modification; preserve compatible user syntax, report material advice when useful | No | Step 6 advisory handling |
| Missing `notes/total.md` while Speaker Notes is enabled | Yes | Generate notes before Step 7 | No | Step 6 Logic Construction |
| Step 7 image readiness missing manual files | Yes | None; list required filenames and prompts | Yes | Step 7 image readiness gate |
| `total_md_split.py` failure | Yes | Fix notes format/path, rerun Step 7.1 | Usually no | Step 7.1 |
| `finalize_svg.py` failure | Yes | Fix SVG/assets, rerun Step 7.2 | Only if a source asset is missing | Step 7.2 |
| `svg_to_pptx.py` failure | Yes | Without a current passing final report: get the complete blocking set from the final checker, fix, rerun the checker, proceed only after `passed`; otherwise fix the conversion issue and rerun Step 7.3 | Only if a required artifact is missing | Step 6 final quality gate or Step 7.3 |
| Export succeeds but the user wants browser edits re-exported | No | Rerun Step 7.2 and 7.3 after the edits | No | Post-export live-preview handling |

---

## 2. Global Stop/Continue Rules

| Condition | Action |
|---|---|
| Required gate artifact missing | Stop at that gate and name it |
| Optional stage not explicitly requested | Do not run it as recovery |
| Convenience UI/server failure | Fall back to chat or continue without the surface |
| Derived artifact stale | Regenerate from its owning source |
| Required manual artifact missing | Pause and name the exact artifacts; resume only after they exist |
| Validation or export failure | Fix the owning source artifact, then rerun only the failed and affected downstream operations |
| Confirmed execution choice cannot be honored | Keep the confirmed requirement visible; retry the confirmed provider, mode, voice, effect, or path only as its owning workflow allows; if still unavailable, stop, request a new decision, or use the owning workflow's declared recovery. Quick's AI-generation exception is an explicit no-AI replan that preserves the communication job and never substitutes another image source |

**Missing values**: for a field in an existing artifact, follow only the requiredness, inference procedure, or fixed default declared by its owning schema or workflow; an active omission with no such rule stops at the owning boundary. Do not extend a fallback by analogy to empty values, inactive conditional fields, whole or derived artifacts, or file-format attributes. Two fallback terms are used across the repository: a **declared-inference / declared-procedure fallback** states its missing condition and a bounded procedure needing no new user decision; a **fixed compatibility default** states the exact value, applied with one warning.

**Forbidden — silent downgrade**: never skip a required gate because a downstream command might tolerate the missing file, and never change a confirmed execution value to keep the route moving. Fix, pause, request a new decision, or apply an explicit profile-owned recovery at the owning boundary.

**Proactive production resolution**: keep final Stage-2 raw fields as evidence; resolve durable outcomes as explicit instruction → final Stage 2 → workflow defaults `enabled` / `disabled` / `disabled`. Audio raises Notes only when Notes is not explicitly disabled; an explicit notes-off/audio-on conflict stops at Generate's one-question dependency gate. Record outcomes/provenance only in Design Spec §I, never the lock.

---

## 3. Generate PPTX Resume Pointers

**Final confirmation evidence** means the explicit final confirmation in the current chat or `<project>/confirm_ui/result.json` with `status: confirmed` and `stage: final`; planning artifacts alone prove nothing. After that gate, a newer explicit instruction updates only its effective production outcome and provenance in the Design Spec; resume from the owning step without reopening Confirm UI. UI wait entries apply only while UI remains the selected surface; a newer chat-surface instruction follows the in-run switch and resumes in chat.

| Last good state | Resume from |
|---|---|
| Stage 1 confirmed, final Stage 2 missing or unconfirmed, UI selected | Derive a fresh `recommendations.stage2.json` from confirmed Stage 1 and current inputs, then `confirm_ui/server.py <project> --wait-only` |
| Final evidence exists; `design_spec.md` missing (with or without a surviving lock) | Step 4 and [`strategist.md`](../../references/strategist.md) §6.2: read final evidence once, read [`design_spec_reference.md`](../../templates/design_spec_reference.md), author the complete Design Spec from scratch, pass Gate 1; then read [`spec_lock_reference.md`](../../templates/spec_lock_reference.md) and re-author the complete lock, replacing any orphan. Never reconstruct the Design Spec from an orphan lock |
| Final evidence exists; Design Spec exists, lock missing | Step 4: read final evidence once to audit the Design Spec, then author the complete lock from it plus context |
| Both planning artifacts exist but Gate 1 fails | Read final evidence once, repair `design_spec.md`, re-author every affected lock row; do not reopen recommendations or infer from the lock |
| Gate 1 passes, Gate 2 fails | Keep the Design Spec; re-author only the mismatched lock rows |
| No final evidence | If `result.json` proves Stage 1, resume at final Stage 2; otherwise restart Step 4 at Stage 1. Never infer confirmed choices from partial artifacts |
| Both planning artifacts complete, split mode selected | [`resume-execute`](../stages/resume-execute.md) |
| Images acquired, SVGs not started | [`generate-pptx`](../generate-pptx.md) Step 6 |
| SVGs complete and checker passed; Speaker Notes enabled, notes missing | Step 6 Logic Construction |
| SVGs complete; Speaker Notes disabled | Conditional motion handling, then Step 7.2 and export with `--no-notes` |
| SVGs and notes complete | Step 7.1 |
| Step 7.1 complete | Step 7.2 |
| Step 7.2 complete, PPTX missing | Step 7.3 |
| Browser annotations saved after export | [`live-preview`](../stages/live-preview.md) Step 2 |

**Default — resume at the owning failed step**: do not restart planning or regenerate prior artifacts unless the owning source changed.
