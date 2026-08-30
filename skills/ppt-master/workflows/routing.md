---
description: Deterministic selection among PPT Master's three top-level artifact routes.
---

# Routing Rules

Route selection authority for PPT Master. Select exactly one top-level route, then activate only the child workflows, profiles, and stages owned by that route.

**Hard rule**: when this file conflicts with a route summary elsewhere in the Skill package or a repository-level document, this file wins for route selection. After selection, the active runtime authority owns execution.

---

## 1. Routing Discipline

| Rule | Behavior |
|---|---|
| One artifact lifecycle | Every request enters Generate PPTX, Create Template, or Edit Native PPTX |
| Supporting documents are not routes | Create Template child workflows, generation profiles, stages, and governance documents refine the selected route; never offer them as competing routes |
| Missing prerequisite | State it and stop that route; do not invent an alternative |
| Ambiguous existing-deck request | Ask one discriminator question only when needed: regenerate the visible design (Generate), or preserve the native deck and edit it (Edit Native PPTX)? |
| Explicit user override | Honor explicit route instructions only when the route preconditions are satisfied |

**Forbidden — route-choice menus**: do not present multiple implementation paths when the request already matches one row in §2; ordinary design choices remain at the selected route's confirmation gate.

---

## 2. Top-Level Route Matrix

| Route | Request shape | Authority | Preconditions | Mutation model | Output contract |
|---|---|---|---|---|---|
| Generate PPTX | Create, reconstruct, or visually regenerate a presentation/video from sources or a topic; templates optional | Image to PPTX: [`image-to-pptx`](./profiles/image-to-pptx.md), always Quick; Beautify: [`beautify-pptx`](./profiles/beautify-pptx.md), Default or Quick; ordinary [`generate-pptx`](./generate-pptx.md) / [`quick-generate`](./profiles/quick-generate.md) | Facts exist or research can gather them; Image to PPTX also requires Codex and an ordered page-frame roster | Author SVG pages and export a new PPTX | Default: spec/lock/SVG/PPTX; Quick: optional source/resource artifacts, no spec/lock, SVG/PPTX; either may derive narrated PPTX/MP4 |
| Create Template | Create a reusable brand/style/layout/deck template from PPTX/SVG files, images/PDFs, direct or file-based text, documents/websites, brand assets, or a mixed bundle | [`create-template`](./create-template.md) | A reusable-template request; reference material optional; project scope also requires an initialized target project | Author a new portable workspace; never modify a reference file in place | Workspace with required `templates/`, optional `images/` / `icons/`, optional review `exports/` |
| Edit Native PPTX | Keep an existing PPTX's native design: fill with new content, edit or restructure selected pages, or add notes, narration, timings, or transitions with visible slides untouched | [`edit-native-pptx`](./edit-native-pptx.md) | Source PPTX exists; new material only when content changes | `pptx_to_svg.py --roundtrip` workspace: unchanged pages restore byte-for-byte, edited pages rebuild only edited objects, notes/motion overlay | New PPTX in workspace `exports/` |

---

## 3. Generate PPTX Profiles and Stages

| Request condition | Generate-route behavior |
|---|---|
| Raster files represent page frames to reconstruct into a layered editable PPTX | Activate the Codex-supported [`image-to-pptx`](./profiles/image-to-pptx.md); normalize the frame roster and activate `quick-generate` directly |
| Existing PPTX must preserve wording, page count, and order 1:1 | Activate [`beautify-pptx`](./profiles/beautify-pptx.md); Quick when that profile's explicit trigger also matches, otherwise `generate-pptx` |
| Effective delivery purpose is recorded, self-running, or video-directed | Inside the selected runtime, load [`video-design`](../references/video-design.md) before whole-solution/page planning; a design reference, not a profile — notes, animation, audio, and native MP4 stay with their stages |
| Explicit quick/fast, skip-strategy, or direct SVG-to-PPTX intent without an active fidelity profile | Load [`quick-generate`](./profiles/quick-generate.md) directly without `generate-pptx.md`: prepare sources/resources as needed, decide without interaction, apply at most one exact workspace root per kind supplied for this run (otherwise free design), omit Strategist/Confirm UI/spec/lock, hand-author SVG, run the lockless final checker, export |
| Topic only, or sources leave planning-critical factual gaps | Run [`topic-research`](./stages/topic-research.md) inside the selected profile's source preparation — immediately for topic-only input, after conversion and reading for source-backed input; research only the identified gaps |
| Existing PPTX must be split, merged, or re-outlined into newly designed pages | Treat the PPTX as source content through the selected Generate authority's intake; Default unless explicit Quick intent |
| Existing PPTX pages dropped, reordered, or repeated without redesign | Not Generate: Edit Native PPTX, whose `page_plan.json` owns selection, order, and repetition |
| Default Generate reaches planning | Step 3 prepares template candidates without interaction; Stage 1 confirms the communication contract and free-design/template choice together; only a confirmed non-free choice runs [`apply-template-workspace`](./stages/apply-template-workspace.md) before Stage 2 |
| Explicit current brand/style/layout/deck workspace root outside Image to PPTX | Default preserves the exact path as a Stage-1 candidate; Quick validates and installs it directly without Steps 3–4 or Confirm UI. Classify as `library` only when the normalized root exactly matches a registered index entry, otherwise `explicit`. Consume the workspace root, never only its inner `templates/` |
| Split-mode project resumes in a fresh chat | Run [`resume-execute`](./stages/resume-execute.md) inside the active Generate route |
| Generated project needs a deck-wide `colors.*` or universal `typography.font_family` substitution | Stay in Generate; load [`update_spec.py`](../scripts/docs/update_spec.md), honor its supported-key boundary, then rerun the final quality gate and Step 7 export |
| User explicitly requests spec refinement | Run [`refine-spec`](./stages/refine-spec.md) after Design Spec Gate 1 and before lock Gate 2 |
| Data charts exist | Run [`verify-charts`](./stages/verify-charts.md) before export |
| User explicitly requests visual review | Run [`visual-review`](./stages/visual-review.md) before post-processing |
| User requests preview, selection, or annotation application outside Image to PPTX | Default pipeline plus [`live-preview`](./stages/live-preview.md) at its defined stage; explicit Quick + preview intent falls back to Default rather than dropping preview. Image to PPTX stays Quick-only with its canonical-frame recomposition comparison |
| Page transitions, auto-advance, or deck-wide animation settings without page-specific motion planning or an existing `animations.json` | Load [`animations`](../references/animations.md) and apply its export-level contract |
| `<project_path>/animations.json` exists, the user explicitly requests per-slide/object-level animation control, or the effective Custom Animations outcome in `design_spec.md §I` is enabled | Run [`customize-animations`](./stages/customize-animations.md) after the final SVG quality gate and any speaker-note pass, before Step 7. A §IX `Motion suggestion` informs an active pass but never triggers it |
| Explicit narration request or effective Narration Audio enabled in `design_spec.md §I`; Edit Native PPTX narration confirmed in its plan | Run [`generate-audio`](./stages/generate-audio.md) after the owning route's notes readiness; audio implies notes on every output page |

**Hard rule — fidelity profiles, not fifth routes**: Image to PPTX and Beautify change different source/page invariants and are mutually exclusive. Image to PPTX always activates Quick; Beautify uses Quick only on explicit Quick intent. Neither defines a separate lifecycle or loads both runtimes.

**Hard rule — direct-generation profile, not a fifth route**: `quick-generate` stays inside Generate PPTX and owns an explicit SVG → PPTX short circuit; page count alone never activates or blocks it. Conversion, bounded research, project-local resources, and package capabilities remain available. Quick may consume exact Brand/Style/Layout/Deck workspaces, at most one contribution per kind; all four may combine, Layout takes structural precedence over Deck, and a multi-kind root contributes all its specs atomically. Brand/Style-only and free-design Quick pages stay flat; when Layout or Deck owns structure, Quick authors the complete explicit Master/Layout/slot metadata and its lockless checker/exporter infers structured output from the all-page SVG contract. Once selected, Quick is the complete runtime and never loads `generate-pptx.md`; Default never loads `quick-generate.md`.

---

## 4. Template and Master/Layout Boundary

**Hard rule — no direct structure grafting or automatic upgrade**: an existing PPTX or SVG is never upgraded in place by adding Master/Layout/placeholder structure — run [`create-template`](./create-template.md) for a separate validated workspace, then pass its root to Default Stage 1 or explicit Quick and author new structured pages. Free-design, brand-only, and style-only generation stays `pptx_structure.mode: flat`; repeated Slide-local objects never trigger `structured`.

| Input | Route behavior |
|---|---|
| Images containing page frames + explicit final-deck reconstruction intent | Generate PPTX with Quick-only [`image-to-pptx`](./profiles/image-to-pptx.md); normalize frames first, never infer reusable native structure from pixels |
| Raw PPTX called a template + new content | Edit Native PPTX unless the user explicitly asks for a reusable template workspace |
| Any supported reference bundle or direct-text brief + reusable template request | Create Template |
| Current template workspace root + content | Default: [`generate-pptx`](./generate-pptx.md) Stage-1 template choice; explicit Quick: direct validated application |
| Semantic-legacy or incomplete structured package | New workspace through Create Template; never migrate in place |
| Request to add a master directly to an existing PPTX/SVG | Unsupported; explain the Create Template → Generate PPTX lifecycle |

---

## 5. Create Template Child Workflows

| Selected kind | Behavior |
|---|---|
| `brand` | [`create-brand`](./create-template/create-brand.md): identity only, no SVG roster |
| `style` | [`create-style`](./create-template/create-style.md): reusable communication method and design direction only, no roster or native structure |
| `layout` | [`create-layout`](./create-template/create-layout.md): brand-neutral, application-neutral structure plus an SVG roster |
| `deck` | [`create-deck`](./create-template/create-deck.md): descriptive recurring-application context with integrated identity, structure, and an SVG roster |

Create Template remains the fixed route name and owns the shared contract; these four are mutually exclusive child workflows.

**Hard rule — classify reusable rules, not source completeness**: a complete PPTX does not automatically select Deck. Brand when only identity is stable; Style when communication method and design direction should travel without identity truth, prototypes, or native structure; Layout when structure is brand-neutral and the application stays downstream-defined; Deck when structure carries identity or reusable scenario/content semantics.

---

## 6. Native and Shared Post-Processing Boundary

A main-generated project with notes and an exported deck narrates through the shared [`generate-audio`](./stages/generate-audio.md) stage; an arbitrary finished PPTX whose visible slides must be preserved goes to Edit Native PPTX, whose narration module invokes the same stage rules against the round-trip workspace. Object animation for generated SVG projects uses the animation stage; Edit Native PPTX preserves source motion by default and writes requested motion as an overlay per [`animations.md`](../references/animations.md).

---

## 7. Template Selection Boundary

| User input | Behavior |
|---|---|
| Default Generate | Step 3 prepares candidates only; Stage 1 confirms one communication contract plus free design or template use in one interaction |
| Explicit current workspace root exposing at least one `templates/` Design Spec | Preserve it as a Stage-1 candidate and initialize template mode; preselect it only when it is the sole supplied root; an exact registered-root match may display as `library` |
| No exact root and no explicit template intent | Initialize Stage 1 to free design; the user may switch to template mode and pick an indexed workspace |
| Explicit template intent or any exact root | Initialize Stage 1 to template mode; exactly one root may be preselected, others remain unselected candidates |
| Bare template/brand name or style label without an explicit template-use request | Never resolve to a local path or preselect; treat as a style brief. An explicit request to use templates initializes template mode but leaves the candidate to the user |
| "What templates exist?" in chat | List indexed workspace paths; Stage 1 still requires an explicit free-design/template choice |

Discovery reads only [`brands_index.json`](../templates/brands/brands_index.json), [`styles_index.json`](../templates/styles/styles_index.json), [`layouts_index.json`](../templates/layouts/layouts_index.json), and [`decks_index.json`](../templates/decks/decks_index.json); never scan kind directories to construct or supplement the catalog.

**Hard rule — index-derived roots only**: never resolve a bare name to a local template directory on the user's behalf; a library choice comes from an index-derived root, and an unregistered workspace requires an explicit root (including one handed off by Create Template in the current conversation). Stage-1 ordering and delayed template reading are owned by [`generate-pptx`](./generate-pptx.md) Steps 3–4.
