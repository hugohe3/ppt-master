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
| User explicitly switches from Confirm UI to chat during any stage | Yes until the unresolved current stage is confirmed | Follow [`confirm_ui.md`](../../scripts/docs/confirm_ui.md)'s in-run switch, retain persisted confirmed stages, then continue the current and remaining stages in chat; never relaunch UI | Confirm in chat unless explicitly delegated | Step 4 current chat stage |
| Confirm UI Stage 1 completed then unexpectedly interrupted while UI remains selected | Yes until final Stage 2 is written/confirmed | Read existing Stage 1 `result.json`, derive a fresh `recommendations.stage2.json` without changing Stage 1, then `--wait-only` for final confirmation | Usually no | Step 4 final Stage 2 write/wait |
| Missing final confirmation | Yes | None | User must confirm or change the values | Step 4 final confirmation |
| Final confirmed value or a later explicit user override is missing, changed, substituted, or weakened in `design_spec.md` | Yes | Repair from the retained final-confirmation object plus any newer explicit instruction; only a fresh recovery turn with no retained state reads persisted final evidence once | Only when the effective value genuinely cannot be honored | Step 4 Gate 1 — confirmation fidelity |
| `spec_lock.md` changes confirmed identity or omits a required execution anchor/routing decision | Yes | Re-author the affected lock rows from the completed Design Spec and current context; do not enumerate page-local literals | No unless the Design Spec itself is incomplete | Step 4 Gate 2 — lock context fidelity |
| Execution exposes a missing Strategist-owned role/plan detail | Yes for the affected page | Repair affected Design Spec/lock fragments under [`executor-base.md`](../../references/executor-base.md) §2.1 | Only if confirmed intent changes | Step 4 Gate 1/2 → Step 6 current page |
| Execution context is fresh, resumed, restarted, compacted/summary-only, external, or unknown | Yes until rebuilt | Read complete Design Spec, then lock, once; reload triggered inputs and latest completed SVG when mid-deck | No | Step 6 current page |
| Step 3 rejects a legacy or incomplete template contract | Yes | Stop template consumption; create a new current workspace through Create Template from the original PPTX/reference, then return with its exact workspace root | Only when required source evidence or template choices are unavailable | Create Template → Generate PPTX Step 3 |
| Native formula marker validation or LaTeX compilation failure | Yes for the affected page | Repair the marker metadata or source LaTeX and rerun the SVG checker; there is no formula-image fallback | Clarify the intended equation only when the source is ambiguous | Active SVG authoring step |
| AI image generation failure | Default blocks at the recovery decision; Quick does not | Default `auto`: try A → B, then ask once to repair/retry, generate manually, or cancel/replan affected AI images; explicit `api` / `host-native`: retry only that path, then ask the same question. Quick removes the exhausted AI/dependent-slice jobs, replans them with native editable text/SVG or already prepared non-AI assets, and continues | Default chooses one outcome; manual files are still required before export | Default: Step 5 decision → same path, Step 4 affected-plan repair, or Step 7 image readiness gate; Quick: current resource plan |
| Web image search/download failure | No | Adjust query/source per image-searcher rules, then mark `Needs-Manual` if unresolved | Only if the resource is required and no acceptable substitute exists | Step 5 |
| Slice sheet missing | Yes for derived slice rows | Wait for parent sheet; run `slice_images.py`; rerun image analysis | Yes when sheet was manual/offline | Step 5 slice handling / Step 7 image readiness gate |
| Strict-alpha slice failure | Yes for every named output | Return the parent to image preparation; correct an evidenced key/tolerance mismatch, then enlarge cells or split incompatible shape families and regenerate when content reaches an edge. A generated parent never substitutes for its missing slices | Only after the selected automated recovery is exhausted | Quick §2 resource closure / Default Step 5 slice handling |
| Residual `Pending` or `Failed` image row before Executor | Yes | Re-run the owning path; Default AI follows its three-outcome decision and reaches `Needs-Manual` only after manual confirmation; Quick automated AI follows its declared no-AI replan | Only when the owning rule requires a new choice or manual file | Step 5 terminal-state check |
| User replaces/adds images after analysis | No | Re-run `analyze_images.py` before reading image facts | No | Step 4/5/6 image-fact read |
| Live preview fails to start | No | Continue generation; report that preview is unavailable | Only if user requires browser preview | Step 6 or `live-preview` Step 1 |
| Live preview closed by user | No | Continue generation | No | Restart through `live-preview` only if requested |
| Browser annotations submitted during generation | No | Defer application until after Step 7 | User asks to apply annotations | `live-preview` Step 2 |
| `svg_quality_checker.py` error | Yes | Review the complete issue set from one unfiltered run; fix all errors and selected warnings in one consolidated edit pass, then perform one verification rerun. If it still fails, use that complete result as the next batch; never check between individual fixes | No unless required asset is missing | Step 6 Visual Construction |
| `svg_quality_checker.py` warning | No | Continue without mandatory modification or acknowledgement; preserve compatible user syntax, and report material fidelity/quality advice when useful | No | Step 6 advisory warning handling |
| Missing `notes/total.md` while the effective Speaker Notes outcome is enabled | Yes | Generate speaker notes before Step 7 | No | Step 6 Logic Construction |
| Step 7 image readiness missing manual files | Yes | None for manual assets; list required filenames and prompts | Yes | Step 7 image readiness gate |
| `total_md_split.py` failure while speaker notes are enabled | Yes | Fix notes format/path, rerun only Step 7.1 | Usually no | Step 7.1 |
| `finalize_svg.py` failure | Yes | Fix SVG/assets, rerun Step 7.2 | Only if source asset is missing | Step 7.2 |
| `svg_to_pptx.py` failure | Yes | If no current matching passing final SVG quality report exists, obtain the complete blocking issue set from the final checker as needed, fix it, rerun the checker against the updated `svg_output/`, and proceed to Step 7.3 only after it reports `passed`; otherwise fix the conversion issue and rerun Step 7.3 | Only if a required artifact is missing | Step 6 final quality gate or Step 7.3 |
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
| Confirmed execution choice cannot be honored | Keep the confirmed requirement visible. Retry the confirmed provider, mode, voice, effect, or path only as its owning workflow allows; if it remains unavailable, stop, request a new decision, or use the owning workflow's declared recovery. Quick's AI-generation exception is an explicit no-AI replan that preserves the communication job; it never substitutes another image source. |

**Missing values**: For a field in an existing artifact, follow only the exact requiredness, inference procedure, or fixed default declared by its owning schema or workflow; an active omission with no such rule stops at the owning boundary. Empty values, inactive conditional fields, whole artifacts, derived artifacts, and file-format attributes keep their own declared semantics—do not extend a fallback by analogy. Owning rules label their fallbacks with two terms used across this repository: a **declared-inference / declared-procedure fallback** states its missing condition and a bounded procedure that needs no new user decision; a **fixed compatibility default** states the exact fallback value, applied with one warning.

**Forbidden — silent downgrade**: Do not skip a required gate because a downstream command might tolerate the missing file, and do not change a confirmed execution value merely to keep the route moving. Fix, pause, request a new decision, or apply an explicit profile-owned recovery at the owning boundary; Quick's documented AI-to-no-AI replan is the narrow exception.

**Proactive production resolution**: Keep final Stage-2 raw fields as evidence.
Resolve durable outcomes as explicit instruction → final Stage 2 → workflow defaults
`enabled` / `disabled` / `disabled`. Audio raises Notes only when Notes is not
explicitly disabled; an explicit notes-off/audio-on conflict stops at
Generate's one-question dependency gate. Keep raw values unchanged and record
outcomes/provenance only in Design Spec §I, never the lock.

---

## 3. Generate PPTX Resume Pointers

Here, **final confirmation evidence** means either the explicit final confirmation in the current chat or `<project>/confirm_ui/result.json` with `status: confirmed` and `stage: final`. Planning artifacts alone do not prove that the user confirmed their values. After that gate, a newer explicit user instruction may update only its effective production outcome and provenance in the durable Design Spec; resume from the owning step without reopening Confirm UI.

The UI wait resume entries below apply only while UI remains the selected
surface. A newer explicit chat-surface instruction follows `confirm_ui.md`'s
in-run switch and resumes the unresolved stage in chat without relaunching UI.

| Last good state | Resume from |
|---|---|
| Stage 1 confirmation exists, final Stage 2 is missing or unconfirmed, and UI remains selected | Derive a fresh `recommendations.stage2.json` from confirmed Stage 1 and current inputs without changing Stage 1, then run `confirm_ui/server.py <project> --wait-only` for final confirmation. |
| Final confirmation evidence exists; `design_spec.md` is missing, with or without a surviving `spec_lock.md` | Return to Generate Step 4 and [`strategist.md`](../../references/strategist.md) §6.2; read final evidence once into the fresh context, read [`design_spec_reference.md`](../../templates/design_spec_reference.md), author the complete `design_spec.md` from scratch using that state plus source analysis, and pass Gate 1. Then read [`spec_lock_reference.md`](../../templates/spec_lock_reference.md) and re-author the complete `spec_lock.md` from the audited Design Spec plus current context, replacing any orphan lock. Never reconstruct the Design Spec from an orphan lock or retain orphan-lock choices as authority. |
| Final confirmation evidence exists; `design_spec.md` exists and `spec_lock.md` missing | Return to Generate Step 4; in this fresh recovery context read final evidence once to audit the existing Design Spec, then read [`spec_lock_reference.md`](../../templates/spec_lock_reference.md) and author the complete lock from the audited Design Spec plus current context. |
| Final confirmation evidence and both planning artifacts exist, but Gate 1 fails | In a fresh recovery context read final evidence once, repair `design_spec.md`, then re-author every affected lock row. Do not reopen recommendations or infer a replacement from the current lock. |
| Gate 1 passes but Gate 2 fails | Keep the Design Spec unchanged and re-author only the mismatched lock anchors/routing rows from it plus current context. |
| No final confirmation evidence is available | If `confirm_ui/result.json` proves Stage 1 confirmation, resume at final Stage 2; otherwise restart Step 4 at Stage 1. Do not infer confirmed choices from partial planning artifacts. |
| `design_spec.md` and `spec_lock.md` complete, split mode selected | [`resume-execute`](../stages/resume-execute.md) |
| Images acquired but SVGs not started | [`generate-pptx`](../generate-pptx.md) Step 6 |
| SVGs complete and checker passed; effective Speaker Notes outcome enabled and notes missing | Step 6 Logic Construction |
| SVGs complete; effective Speaker Notes outcome disabled | Run any applicable conditional motion handling, then Step 7.2 and export with `--no-notes` |
| SVGs and enabled notes complete | Step 7.1 |
| Step 7.1 complete, export not complete | Step 7.2 |
| Step 7.2 complete, PPTX not complete | Step 7.3 |
| Browser annotations saved after export | [`live-preview`](../stages/live-preview.md) Step 2 |

**Default - resume at the owning failed step**: Do not restart the planning session or regenerate prior artifacts unless the owning source has changed.
