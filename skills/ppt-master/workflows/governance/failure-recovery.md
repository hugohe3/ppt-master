---
description: Cross-route stop/continue governance with a concrete recovery matrix and resume map for Generate PPTX.
---

# Failure Recovery Governance

Global stop/continue rules for all four top-level routes, plus concrete failure handling for Generate PPTX. Section 2 applies across routes; Sections 1 and 3 apply only to Generate PPTX. Owning route and stage documents may add narrower handling, but must not weaken the global rules or duplicate this matrix.

**Hard rule**: A failed required artifact blocks the next gate. A failed convenience surface falls back to the canonical channel and does not block the active route.

---

## 1. Generate PPTX Recovery Matrix

| Failure point | Blocking | Automatic recovery | User intervention | Resume entry |
|---|---:|---|---|---|
| Confirm UI launch failure | No | Re-check `confirm_ui/result.json` once, then use chat fallback | No | [`generate-pptx`](../generate-pptx.md) Step 4 chat confirmation |
| Confirm UI wait timeout | No, if no final result yet | Re-check `result.json` once; keep server cleanup mandatory | Only if user still wants the page | Step 4 same stage or chat fallback |
| Confirm UI Stage 1 completed then interrupted | Yes until Stage 2 is written/confirmed | Read existing Stage 1 `result.json`, write Stage 2 recommendations, then `--wait-only --wait-stage stage2` | Usually no | Step 4 Stage 2 write/wait |
| Missing final confirmation | Yes | None | User must confirm or change the values | Step 4 final confirmation |
| Step 3 rejects a legacy or incomplete template contract | Yes | Stop template consumption; create a new current workspace through Create Template from the original PPTX/reference, then return with its exact workspace root | Only when required source evidence or template choices are unavailable | Create Template → Generate PPTX Step 3 |
| Formula rendering provider failure | No until the Step 7 readiness gate | Exhaust the provider chain; if unresolved, mark only the affected formula rows `Needs-Manual` and continue | Supply the exact target PNG or change formula policy | Step 4 / Step 7 image readiness gate |
| AI image generation failure | No | `auto`: follow A → B → Offline Manual. Explicit `api` / `host-native`: retry only that path, then mark the row `Needs-Manual` without switching automated providers | Only when missing files are required before export | Step 5 / Step 7 image readiness gate |
| Web image search/download failure | No | Adjust query/source per image-searcher rules, then mark `Needs-Manual` if unresolved | Only if the resource is required and no acceptable substitute exists | Step 5 |
| Slice sheet missing | Yes for derived slice rows | Wait for parent sheet; run `slice_images.py`; rerun image analysis | Yes when sheet was manual/offline | Step 5 slice handling / Step 7 image readiness gate |
| Residual `Pending` or `Failed` image row before Executor | Yes | Re-run path or mark `Needs-Manual` | Only if file must be supplied manually | Step 5 terminal-state check |
| User replaces/adds images after analysis | No | Re-run `analyze_images.py` before reading image facts | No | Step 4/5/6 image-fact read |
| Live preview fails to start | No | Continue generation; report that preview is unavailable | Only if user requires browser preview | Step 6 or `live-preview` Step 1 |
| Live preview closed by user | No | Continue generation | No | Restart through `live-preview` only if requested |
| Browser annotations submitted during generation | No | Defer application until after Step 7 | User asks to apply annotations | `live-preview` Step 2 |
| `svg_quality_checker.py` error | Yes | Fix the affected SVG, then rerun checker | No unless required asset is missing | Step 6 Visual Construction |
| `svg_quality_checker.py` warning | No | Continue without mandatory modification or acknowledgement; preserve compatible user syntax, and report material fidelity/quality advice when useful | No | Step 6 advisory warning handling |
| Missing `notes/total.md` | Yes | Generate speaker notes before Step 7 | No | Step 6 Logic Construction |
| Step 7 image readiness missing manual files | Yes | None for manual assets; list required filenames and prompts | Yes | Step 7 image readiness gate |
| `total_md_split.py` failure | Yes | Fix notes format/path, rerun only Step 7.1 | Usually no | Step 7.1 |
| `finalize_svg.py` failure | Yes | Fix SVG/assets, rerun Step 7.2 | Only if source asset is missing | Step 7.2 |
| `svg_to_pptx.py` failure | Yes | Fix conversion issue, rerun Step 7.3 | Only if required artifact is missing | Step 7.3 |
| Export succeeds but user wants direct browser edits re-exported | No | Rerun Step 7.2 and Step 7.3 after applied edits | No | Post-export live-preview handling |

---

## 2. Global Stop/Continue Rules

| Condition | Action |
|---|---|
| Required gate artifact missing | Stop at that gate and name the missing artifact. |
| Optional stage not explicitly requested | Do not run it as recovery. |
| Convenience UI/server failure | Fall back to chat or continue without the surface. |
| Derived artifact stale | Regenerate it from its owning source. |
| Required manual artifact missing | Pause and name the exact required artifacts; resume only after they exist. |
| Validation or export failure | Fix the owning source artifact, then rerun the failed operation and affected downstream operations only. |
| Confirmed execution choice cannot be honored | Retry the confirmed provider, mode, voice, effect, or path only as its owning workflow allows; if it remains unavailable, stop, request a new decision, or hand off through the owning workflow's declared manual fallback (e.g. `Needs-Manual` with a user summary). Never switch to another automated value or path silently. |

**Missing values**: For a field in an existing artifact, follow only the exact requiredness, inference procedure, or fixed default declared by its owning schema or workflow; an active omission with no such rule stops at the owning boundary. Empty values, inactive conditional fields, whole artifacts, derived artifacts, and file-format attributes keep their own declared semantics—do not extend a fallback by analogy. Owning rules label their fallbacks with two terms used across this repository: a **declared-inference / declared-procedure fallback** states its missing condition and a bounded procedure that needs no new user decision; a **fixed compatibility default** states the exact fallback value, applied with one warning.

**Forbidden — silent downgrade**: Do not skip a required gate because a downstream command might tolerate the missing file, and do not change a confirmed execution value merely to keep the route moving. Fix, pause, or request a new decision at the owning boundary.

---

## 3. Generate PPTX Resume Pointers

Here, **final confirmation evidence** means either the explicit final confirmation in the current chat or `<project>/confirm_ui/result.json` with `status: confirmed` and `stage: final`. Planning artifacts alone do not prove that the user confirmed their values.

| Last good state | Resume from |
|---|---|
| Stage 1 confirmation exists, Stage 2 missing | Write Stage 2 recommendations, then `confirm_ui/server.py <project> --wait-only --wait-stage stage2` |
| Stage 2 confirmation exists, final confirmation missing | Resume [`generate-pptx`](../generate-pptx.md) Step 4 substep 4, "Derive Stage 3 once from the confirmed solution, then wait for the final confirmation." |
| Final confirmation evidence exists; `design_spec.md` is missing, with or without a surviving `spec_lock.md` | Return to [`strategist.md`](../../references/strategist.md) §6 steps 1–4 and regenerate `design_spec.md` and `spec_lock.md` together from the source material and confirmed state; do not reconstruct the outline from an orphan lock. |
| Final confirmation evidence exists; `design_spec.md` exists and `spec_lock.md` missing | Return to [`strategist.md`](../../references/strategist.md) §6 step 4 and regenerate `spec_lock.md`. |
| No final confirmation evidence is available | Resume Step 4 from the latest stage evidenced by `confirm_ui/result.json`; if no stage is persisted, restart Step 4 at Stage 1. Do not infer confirmed choices from partial planning artifacts. |
| `design_spec.md` and `spec_lock.md` complete, split mode selected | [`resume-execute`](../stages/resume-execute.md) |
| Images acquired but SVGs not started | [`generate-pptx`](../generate-pptx.md) Step 6 |
| SVGs complete and checker passed, notes missing | Step 6 Logic Construction |
| SVGs and notes complete | Step 7.1 |
| Step 7.1 complete, export not complete | Step 7.2 |
| Step 7.2 complete, PPTX not complete | Step 7.3 |
| Browser annotations saved after export | [`live-preview`](../stages/live-preview.md) Step 2 |

**Default - resume at the owning failed step**: Do not restart the planning session or regenerate prior artifacts unless the owning source has changed.
