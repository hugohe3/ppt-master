---
description: Registry of PPT Master's top-level routes and supporting child workflows, profiles, stages, and governance documents.
---

# Workflow Registry

Registry for the route authorities and supporting runbooks referenced by [`SKILL.md`](../SKILL.md) and [`routing.md`](./routing.md).

**Hard rule — four entry routes only**: User requests enter exactly one top-level route. Create Template child workflows, generation profiles, stages, and governance documents refine an active route; they are never presented as competing top-level routes.

---

## 1. Top-Level Routes

| Route | Authority | Trigger | Mutation model | Output |
|---|---|---|---|---|
| Generate PPTX | [`SKILL.md`](../SKILL.md) | Create or visually regenerate a presentation from source material, a topic, or an existing deck | Author new SVG pages, then export a new PPTX | Project workspace with `design_spec.md`, `spec_lock.md`, `svg_output/`, and `exports/` |
| Create Template | [`create-template.md`](./create-template.md) | Create a reusable `brand`, `layout`, or `deck` workspace | Read reference facts and author a new template workspace; never add Master/Layout structure to the reference file in place | Portable template workspace with required `templates/` and optional assets/review export |
| Fill Native PPTX | [`template-fill-pptx.md`](./template-fill-pptx.md) | Reuse native slides from a raw PPTX and replace/fill their content | Clone and patch PPTX through OOXML; no SVG generation | New filled PPTX under the project `exports/` |
| Enhance Native PPTX | [`native-enhance-pptx.md`](./native-enhance-pptx.md) | Add notes, narration audio, timings, or transitions while preserving finished slides | Append/update scoped OOXML parts; no slide regeneration | New enhanced PPTX under the project `exports/` |

---

## 2. Supporting Documents

| Class | ID | Path | Owner / trigger |
|---|---|---|---|
| Generation profile | `beautify-pptx` | [`profiles/beautify-pptx.md`](./profiles/beautify-pptx.md) | Generate PPTX route when wording, page count, and page order are frozen 1:1 |
| Template child workflow | `create-brand` | [`create-template/create-brand.md`](./create-template/create-brand.md) | Create Template after identity-only intent is selected |
| Template child workflow | `create-layout` | [`create-template/create-layout.md`](./create-template/create-layout.md) | Create Template after brand-neutral structure-only intent is selected |
| Template child workflow | `create-deck` | [`create-template/create-deck.md`](./create-template/create-deck.md) | Create Template after integrated identity-and-structure intent is selected or defaulted |
| Intake stage | `topic-research` | [`stages/topic-research.md`](./stages/topic-research.md) | Generate PPTX route before Step 1 for topic-only requests |
| Control stage | `resume-execute` | [`stages/resume-execute.md`](./stages/resume-execute.md) | Generate PPTX route when a planned project resumes in a fresh chat |
| Planning stage | `refine-spec` | [`stages/refine-spec.md`](./stages/refine-spec.md) | Generate PPTX route after confirmation when the user explicitly requests spec review |
| Quality gate | `verify-charts` | [`stages/verify-charts.md`](./stages/verify-charts.md) | Generate PPTX route when data charts exist |
| Quality gate | `visual-review` | [`stages/visual-review.md`](./stages/visual-review.md) | Generate PPTX route only on explicit visual-review request |
| Editor stage | `live-preview` | [`stages/live-preview.md`](./stages/live-preview.md) | Generate PPTX route for preview, element selection, or applying annotations |
| Post-processing stage | `customize-animations` | [`stages/customize-animations.md`](./stages/customize-animations.md) | Generate PPTX route on explicit object-animation request |
| Shared audio stage | `generate-audio` | [`stages/generate-audio.md`](./stages/generate-audio.md) | Generate PPTX post-processing or Enhance Native PPTX narration module |
| Governance | `failure-recovery` | [`governance/failure-recovery.md`](./governance/failure-recovery.md) | Stop/continue decisions across generation stages |

---

## 3. Update Rules

1. Add a row to §1 only when a request requires a genuinely distinct artifact lifecycle or mutation model.
2. Add child workflows, profiles, stages, and governance documents only to §2; do not add them to the top-level route matrix in [`routing.md`](./routing.md).
3. Update [`routing.md`](./routing.md) whenever a top-level trigger or route boundary changes.
4. Keep execution commands in the owning route or supporting document, not in this registry.

**Forbidden — duplicated route matrices**: Do not copy the full route matrix from [`routing.md`](./routing.md) into `SKILL.md` or stage documents.
