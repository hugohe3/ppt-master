---
description: Deterministic selection among PPT Master's four top-level artifact routes.
---

# Routing Rules

Route selection authority for PPT Master. Select exactly one top-level route, then activate only the child workflows, profiles, and stages owned by that route.

**Hard rule**: If this file conflicts with a route summary elsewhere in the
Skill package or in a repository-level user-facing document, this file wins for
route selection. After selection, the route authority owns execution.

---

## 1. Routing Discipline

| Rule | Behavior |
|---|---|
| One artifact lifecycle | Every request enters Generate PPTX, Create Template, Fill Native PPTX, or Enhance Native PPTX |
| Supporting documents are not top-level routes | Create Template child workflows, generation profiles, stages, and governance documents refine the selected route; never offer them as competing top-level routes |
| Missing prerequisite | State the missing prerequisite and stop that route; do not invent an alternative |
| Ambiguous existing-deck request | Ask one discriminator question only when needed: regenerate visible slides, fill native slide shells with new content, or preserve slides and add native behavior? |
| Explicit user override | Honor explicit route instructions only when the route preconditions are satisfied |

**Forbidden — route-choice menus**: Do not present multiple implementation paths when the request already matches one row in §2. Ordinary design choices remain at the selected route's existing confirmation gate.

---

## 2. Top-Level Route Matrix

| Route | Request shape | Authority | Preconditions | Mutation model | Output contract |
|---|---|---|---|---|---|
| Generate PPTX | Create a new presentation; regenerate an existing deck visually; use source material or a topic; optionally apply an explicit template workspace | [`generate-pptx`](./generate-pptx.md) | Source facts exist or the topic-research stage can gather them | Author new SVG pages and export a new PPTX | New project with `design_spec.md`, `spec_lock.md`, `svg_output/`, `validation/`, and `exports/` |
| Create Template | Create a reusable brand/layout/deck template from one or more PPTX/SVG files, images/PDFs, direct or file-based text, documents/websites, brand assets, or a mixed reference bundle | [`create-template`](./create-template.md) | A reusable-template request exists; reference material is optional, and project scope additionally requires an initialized target project | Author a new portable workspace; never modify any reference file in place | Workspace with required `templates/`, optional `images/` / `icons/`, and optional review `exports/` |
| Fill Native PPTX | Use a raw PPTX's native slide shells and replace/fill content | [`template-fill-pptx`](./template-fill-pptx.md) | Source PPTX plus new material/topic | Clone and patch PPTX through OOXML; no SVG pipeline | New filled PPTX in project `exports/` |
| Enhance Native PPTX | Keep a finished PPTX's visible slides stable while adding notes, audio, timings, or transitions | [`native-enhance-pptx`](./native-enhance-pptx.md) | Finished source PPTX exists | Append/update scoped OOXML parts; no slide regeneration | New enhanced PPTX in project `exports/` |

---

## 3. Generate PPTX Profiles and Stages

| Request condition | Generate-route behavior |
|---|---|
| Topic only, or supplied sources leave planning-critical factual gaps | Run [`topic-research`](./stages/topic-research.md) inside [`generate-pptx`](./generate-pptx.md) Step 1: immediately for topic-only input, or after conversion and reading for source-backed input; research only the identified gaps, then continue Step 2 |
| Existing PPTX may be split, merged, dropped, reordered, or re-outlined | Treat the PPTX as source content through [`generate-pptx`](./generate-pptx.md) Step 1 and its PPTX intake; use the default Generate pipeline |
| Existing PPTX must preserve wording, page count, and page order 1:1 | Activate the [`beautify-pptx`](./profiles/beautify-pptx.md) profile inside the main pipeline |
| Explicit current brand/layout/deck workspace root | Enter [`generate-pptx`](./generate-pptx.md) Step 3 and conditionally load [`apply-template-workspace`](./stages/apply-template-workspace.md); consume the workspace root, never only its inner `templates/` directory |
| Split-mode project resumes in a fresh chat | Run [`resume-execute`](./stages/resume-execute.md) inside the active Generate route |
| Existing generated project needs a deck-wide `colors.*` or universal `typography.font_family` substitution | Stay in Generate; load [`update_spec.py`](../scripts/docs/update_spec.md), honor its supported-key boundary, then rerun the final quality gate and Step 7 export |
| User explicitly requests spec refinement | Run [`refine-spec`](./stages/refine-spec.md) after Strategist confirmation |
| Data charts exist | Run [`verify-charts`](./stages/verify-charts.md) before export |
| User explicitly requests visual review | Run [`visual-review`](./stages/visual-review.md) before post-processing |
| User requests preview, selection, or annotation application | Run [`live-preview`](./stages/live-preview.md) at the stage defined there |
| User requests page transitions, auto-advance, or deck-wide animation settings | Load [`animations`](../references/animations.md) and apply its export-level contract |
| User requests per-slide or object-level animation control | Run [`customize-animations`](./stages/customize-animations.md) during post-processing |
| Generated project needs narration audio | Run [`generate-audio`](./stages/generate-audio.md) after notes/export readiness |

**Hard rule — profile, not fifth route**: The 1:1 beautify behavior uses the same Strategist → Executor → SVG export lifecycle as Generate PPTX. It changes content/page invariants; it does not define a separate artifact lifecycle.

---

## 4. Template and Master/Layout Boundary

**Hard rule — no direct structure grafting**: An existing PPTX or SVG is never upgraded in place by adding Master/Layout/placeholder structure. If reusable native structure is required:

1. Run [`create-template`](./create-template.md) to produce a separate validated workspace.
2. Pass that workspace root to [`generate-pptx`](./generate-pptx.md) Step 3.
3. Author new structured SVG pages whose Master/Layout contract exists from their first generated draft.
4. Export a new PPTX from those pages.

When a PPTX already contains native Master/Layout parts, `create-template` mirror may read and preserve those existing package facts in the new workspace. It does not infer missing historical intent. An incomplete or legacy SVG package may guide `standard` / `fidelity` visually, but it is not mutated into a structured template and cannot claim source-topology recovery.

**Hard rule — no automatic structure upgrade**: Free-design and brand-only generation remains `pptx_structure.mode: flat`. Repeated Slide-local objects never trigger `structured`, Master/Layout promotion, placeholder inference, or deduplication. The minimal Master plus Blank Layout emitted by flat export is package scaffolding, not an inferred reusable design master.

| Input | Route behavior |
|---|---|
| Raw PPTX called a template + new content | Fill Native PPTX unless the user explicitly asks for a reusable template workspace |
| Any supported reference bundle or direct-text brief + reusable template request | Create Template |
| Current template workspace root + content | [`generate-pptx`](./generate-pptx.md) Step 3 |
| Legacy-flat root with current `design_spec.md` and current SVG contract | [`apply-template-workspace`](./stages/apply-template-workspace.md) compatibility reader |
| Semantic-legacy or incomplete structured package | Create a new workspace through Create Template; do not migrate in place |
| Request to add a master directly to an existing PPTX/SVG | Unsupported; explain the Create Template → Generate PPTX lifecycle |

---

## 5. Create Template Child Workflows

| Selected kind | Behavior |
|---|---|
| `brand` | Dispatch to [`create-brand`](./create-template/create-brand.md); write identity only and no SVG roster |
| `layout` | Dispatch to [`create-layout`](./create-template/create-layout.md); author brand-neutral, application-neutral structure and an SVG roster |
| `deck` | Dispatch to [`create-deck`](./create-template/create-deck.md); author descriptive recurring-application context with integrated identity, structure, and an SVG roster |

Create Template remains the fixed route name and owns the shared contract. These three documents are mutually exclusive child workflows, not additional top-level routes.

**Hard rule — classify reusable rules, not source completeness**: A complete
PPTX does not automatically select Deck. Use Brand when only identity is
stable; use Layout when structure is brand-neutral and the communication
application stays downstream-defined; use Deck when structure carries identity
or reusable scenario/content semantics.

---

## 6. Native and Shared Post-Processing Boundary

| Artifact state | Narration route |
|---|---|
| Main-generated project with notes and exported deck | Shared [`generate-audio`](./stages/generate-audio.md) stage |
| Arbitrary finished PPTX that must preserve visible slides | Enhance Native PPTX; its narration module invokes the same shared audio-stage rules |

Object animation for generated SVG projects uses the animation stage. Native PPTX routes preserve existing object-animation fingerprints and do not silently claim an animation-editing capability.

---

## 7. Template Name Boundary

| User input | Behavior |
|---|---|
| Explicit current workspace root containing `templates/design_spec.md` | Enter [`generate-pptx`](./generate-pptx.md) Step 3 |
| Bare template/brand name or style label | Do not resolve it to a local path; treat it as a style brief |
| “What templates exist?” | List indexed workspace paths as Q&A; do not advance a route |

For that Q&A only, read the matching discovery indexes:

| Kind | Discovery index |
|---|---|
| Brand | [`brands_index.json`](../templates/brands/brands_index.json) |
| Layout | [`layouts_index.json`](../templates/layouts/layouts_index.json) |
| Deck | [`decks_index.json`](../templates/decks/decks_index.json) |

**Forbidden — fuzzy resolution**: Never resolve a bare name to a local template directory on the user's behalf. The explicit workspace root is the only Step 3 template trigger, except the exact validated workspace handed off by Create Template in the current conversation.
