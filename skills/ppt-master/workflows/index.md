---
description: Maintainer-only registry of PPT Master's route and supporting-workflow inventory.
---

# Workflow Registry

Maintainer-only inventory for adding, moving, or removing workflow documents. Runtime task execution does not consume this file.

## 1. Route Authorities

| ID | Class | Authority path |
|---|---|---|
| `generate-pptx` | Top-level route | [`generate-pptx.md`](./generate-pptx.md) |
| `create-template` | Top-level route | [`create-template.md`](./create-template.md) |
| `template-fill-pptx` | Top-level route | [`template-fill-pptx.md`](./template-fill-pptx.md) |
| `native-enhance-pptx` | Top-level route | [`native-enhance-pptx.md`](./native-enhance-pptx.md) |

## 2. Supporting Documents

| ID | Class | Path | Parent / lifecycle slot |
|---|---|---|---|
| `beautify-pptx` | Generation profile | [`profiles/beautify-pptx.md`](./profiles/beautify-pptx.md) | Generate PPTX |
| `apply-template-workspace` | Template-input stage | [`stages/apply-template-workspace.md`](./stages/apply-template-workspace.md) | Generate Step 3 |
| `create-brand` | Template child workflow | [`create-template/create-brand.md`](./create-template/create-brand.md) | Create Template |
| `create-layout` | Template child workflow | [`create-template/create-layout.md`](./create-template/create-layout.md) | Create Template |
| `create-deck` | Template child workflow | [`create-template/create-deck.md`](./create-template/create-deck.md) | Create Template |
| `topic-research` | Factual-preparation stage | [`stages/topic-research.md`](./stages/topic-research.md) | Inside Generate Step 1 |
| `resume-execute` | Control stage | [`stages/resume-execute.md`](./stages/resume-execute.md) | Generate Step 6 resume |
| `refine-spec` | Planning stage | [`stages/refine-spec.md`](./stages/refine-spec.md) | After Generate confirmation |
| `verify-charts` | Quality gate | [`stages/verify-charts.md`](./stages/verify-charts.md) | Before Generate Step 7 |
| `visual-review` | Quality gate | [`stages/visual-review.md`](./stages/visual-review.md) | Before Generate Step 7 |
| `live-preview` | Editor stage | [`stages/live-preview.md`](./stages/live-preview.md) | Generate preview / post-export |
| `customize-animations` | Post-processing stage | [`stages/customize-animations.md`](./stages/customize-animations.md) | Generate conditional export |
| `generate-audio` | Shared audio stage | [`stages/generate-audio.md`](./stages/generate-audio.md) | Generate / Enhance Native |
| `failure-recovery` | Governance | [`governance/failure-recovery.md`](./governance/failure-recovery.md) | All routes |

## 3. Maintenance Rules

1. Add a top-level route only for a distinct artifact lifecycle and mutation model; synchronize [`routing.md`](./routing.md).
2. Register profiles, stages, governance files, and Create Template children only in §2.
3. Keep commands and trigger procedures in the owning authority, not in this registry.
4. Update `scripts/prompt_audit_manifest.json` load sets and coverage in the same change.
5. Keep this registry out of runtime load sets.
