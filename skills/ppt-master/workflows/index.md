---
description: Registry of standalone PPT Master workflows
---

# Workflow Registry

Registry for standalone workflows referenced by `SKILL.md` and [`routing.md`](./routing.md).

**Hard rule**: When adding a standalone workflow, update this registry and [`routing.md`](./routing.md) in the same change. The workflow file owns step-by-step execution; this registry owns discoverability and trigger boundaries.

---

## 1. Registry

| ID | Path | Trigger | Preconditions | Route exclusion | Entry step | Output contract | Blocking points |
|---|---|---|---|---|---|---|---|
| `topic-research` | [`topic-research.md`](./topic-research.md) | Topic-only request with no substantive source material | Topic or requirements exist | Do not invent facts in the main pipeline | Before `SKILL.md` Step 1 | Source material suitable for Step 1 | Stops if usable source facts cannot be gathered |
| `template-fill-pptx` | [`template-fill-pptx.md`](./template-fill-pptx.md) | Raw PPTX template plus new material/topic; clone/fill native slides | Source PPTX plus content material or topic brief | No SVG generation; no `create-template` unless reusable package is requested | Workflow Step 1 | Native PPTX in project `exports/` | Stops if no PPTX or no fill material |
| `beautify-pptx` | [`beautify-pptx.md`](./beautify-pptx.md) | Existing PPTX should be re-laid out while preserving slide count/order and wording 1:1 | Single source PPTX | Not for merge/split/drop/reorder or re-outline | Workflow Step 1 | Regenerated 1:1 deck through SVG pipeline | Blocks on source-slide mapping and final confirmation gates defined in the workflow |
| `create-template` | [`create-template.md`](./create-template.md) | Build a reusable layout/deck template from a PPTX or design reference, globally or for one initialized project | Design source or explicit template-creation request; project scope also requires an initialized target project | Does not fill final content; an optional PPTX is only an on-demand review artifact | Workflow Step 1 | Both scopes produce one workspace with required `templates/`, optional `images/` / `icons/`, and optional `exports/<id>_template_preview.pptx`; library root is `skills/ppt-master/templates/<kind>/<id>/`, project root is `projects/<name>/`; only library scope is registered | Return the exact workspace root to main Step 3; the target project's own root may continue in place after validation |
| `create-brand` | [`create-brand.md`](./create-brand.md) | Build/extract a reusable brand identity preset | Logo/site/branded deck/PDF or explicit brand setup request | Not a layout/deck template roster | Workflow Step 1 | Complete identity-only workspace under `templates/brands/<id>/` | Blocks on brand evidence and validation defined in the workflow |
| `resume-execute` | [`resume-execute.md`](./resume-execute.md) | Continue an existing split-mode project | Planning-session artifacts exist | Do not re-run planning | Execution-session entry | SVG generation, post-processing, export | Stops if `design_spec.md` or `spec_lock.md` is missing |
| `refine-spec` | [`refine-spec.md`](./refine-spec.md) | User explicitly opts into spec refinement before generation | Strategist confirmation stage completed | Do not enter by default | After Step 4, before Step 5/6 | Revised `design_spec.md` and `spec_lock.md` | Blocks for user review/approval before generation |
| `restore-pptx-structure` | [`restore-pptx-structure.md`](./restore-pptx-structure.md) | Existing structured project or template uses a legacy/unmapped PowerPoint structure contract | Legacy structured SVG project/package exists; original PPTX/native facts are preferred when available; explicit `mode: flat` free-design/brand-only projects and legacy-flat packaging are not triggers | Not part of normal new-project generation; exporter never migrates implicitly | Before Step 3 template use, structured SVG generation, or structured export | Current structured SVGs plus complete Master/Layout lock mapping | Blocks only when restoration requires an unresolved design decision |
| `verify-charts` | [`verify-charts.md`](./verify-charts.md) | Deck contains data charts that require coordinate calibration | SVG pages exist | Not needed for decks without data charts | Between Step 6 and Step 7 | Verified/fixed chart geometry | Blocks on chart coordinate errors |
| `customize-animations` | [`customize-animations.md`](./customize-animations.md) | User asks for object-level animation order/effect/timing | Target deck/SVG groups exist | Do not add per-element builds by default | Before or during export configuration | `animations.json` or equivalent validated config | Blocks if target objects cannot be identified |
| `native-enhance-pptx` | [`native-enhance-pptx.md`](./native-enhance-pptx.md) | Finished PPTX should keep content/layout stable while adding notes/audio/timing/transitions | Source PPTX exists | No SVG regeneration | Workflow Step 1 | Patched PPTX through OOXML | Blocks on source archive/validation failures |
| `native-narration-pptx` | [`native-narration-pptx.md`](./native-narration-pptx.md) | Compatibility reference for the narration subset of native enhancement | Existing PPTX exists | Prefer `native-enhance-pptx` for new requests | Compatibility entry | Narration-enhanced PPTX | Follow compatibility doc |
| `live-preview` | [`live-preview.md`](./live-preview.md) | User asks for preview, element selection, browser annotations, or re-entry to the editor | Project exists; SVGs required only for annotation apply/export | Do not apply annotations during active generation | Step 6 auto-start or workflow Step 1/2 | Running preview or applied browser edits/annotations | Blocks only when project/SVG target is missing |
| `visual-review` | [`visual-review.md`](./visual-review.md) | User explicitly asks for per-page visual review or visual rubric | Generated SVG pages exist | Never inferred from deck size/model identity | Between Step 6 and Step 7 | Findings and fixed SVGs | Blocks on selected severe findings if the workflow says to fix |
| `generate-audio` | [`generate-audio.md`](./generate-audio.md) | User asks for recorded narration, voiceover, audio, or video-style export | Post-processing/export context exists; notes available | Do not call `notes_to_audio.py` directly | After Step 7 | Audio files and optional narration-embedded PPTX | Single backend/voice/settings confirmation |

---

## 2. Update Checklist

When adding or changing a standalone workflow:

1. Update the row in §1.
2. Update route selection in [`routing.md`](./routing.md).
3. Add a short pointer in `SKILL.md` only if the workflow is part of the main pipeline's normal control flow.
4. Keep detailed commands and recovery behavior in the workflow file, not in this registry.

**Forbidden - duplicated matrices**: Do not copy the full route matrix from [`routing.md`](./routing.md) into `SKILL.md`. Link to the authority instead.
