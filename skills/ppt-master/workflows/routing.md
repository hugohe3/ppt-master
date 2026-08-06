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
| Generate PPTX | Create a new presentation; regenerate an existing deck visually; use source material or a topic; optionally select a registered library template or supply an explicit workspace | [`generate-pptx`](./generate-pptx.md) | Source facts exist or research can gather them; explicit quick intent activates its profile | Author new SVG pages and export a new PPTX | Default: spec, lock, SVG, validation, and PPTX; Quick: optional source/resource artifacts, no spec/lock, SVG, and one PPTX |
| Create Template | Create a reusable brand/style/layout/deck template from one or more PPTX/SVG files, images/PDFs, direct or file-based text, documents/websites, brand assets, or a mixed reference bundle | [`create-template`](./create-template.md) | A reusable-template request exists; reference material is optional, and project scope additionally requires an initialized target project | Author a new portable workspace; never modify any reference file in place | Workspace with required `templates/`, optional `images/` / `icons/`, and optional review `exports/` |
| Fill Native PPTX | Use a raw PPTX's native slide shells and replace/fill content | [`template-fill-pptx`](./template-fill-pptx.md) | Source PPTX plus new material/topic | Clone and patch PPTX through OOXML; no SVG pipeline | New filled PPTX in project `exports/` |
| Enhance Native PPTX | Keep a finished PPTX's visible slides stable while adding notes, audio, timings, or transitions | [`native-enhance-pptx`](./native-enhance-pptx.md) | Finished source PPTX exists | Append/update scoped OOXML parts; no slide regeneration | New enhanced PPTX in project `exports/` |

---

## 3. Generate PPTX Profiles and Stages

| Request condition | Generate-route behavior |
|---|---|
| Explicit quick/fast, skip-strategy, or direct SVG-to-PPTX intent | Activate [`quick-generate`](./profiles/quick-generate.md): prepare sources/resources as needed, let the current agent decide without interaction, directly apply at most one exact workspace root per kind supplied for this run, otherwise use free design, omit Strategist/Confirm UI/spec/lock, hand-author SVG, run the lockless final checker, and export the final PPTX |
| Topic only, or supplied sources leave planning-critical factual gaps | Run [`topic-research`](./stages/topic-research.md) inside the selected Generate profile's source preparation: immediately for topic-only input, or after conversion and reading for source-backed input; research only the identified gaps |
| Existing PPTX may be split, merged, dropped, reordered, or re-outlined | Treat the PPTX as source content through [`generate-pptx`](./generate-pptx.md) Step 1 and its PPTX intake; continue the default pipeline unless explicit Quick Generate intent selected that profile |
| Existing PPTX must preserve wording, page count, and page order 1:1 | Activate the [`beautify-pptx`](./profiles/beautify-pptx.md) profile inside the main pipeline |
| Default Generate has no explicit template-discovery/selection request, exact workspace root, or current Create Template handoff | Use free design and proceed directly to Stage 1; do not read template indexes or create template-selection artifacts |
| Default Generate explicitly requests template discovery/selection, supplies an exact current workspace root, or receives a current Create Template handoff | Run the conditional Step-3 template-selection phase before Stage 1. The UI offers only index-registered library roots plus supplied explicit roots; confirmed non-free selections run [`apply-template-workspace`](./stages/apply-template-workspace.md) |
| Explicit current brand/style/layout/deck workspace root | Default Generate preserves the exact-path path through Step 3; Quick Generate validates and installs it directly without Step 3 or Confirm UI. Classify it as `library` only when its normalized root exactly matches a registered index entry; otherwise retain `explicit`. Consume the workspace root, never only its inner `templates/` directory |
| Split-mode project resumes in a fresh chat | Run [`resume-execute`](./stages/resume-execute.md) inside the active Generate route |
| Existing generated project needs a deck-wide `colors.*` or universal `typography.font_family` substitution | Stay in Generate; load [`update_spec.py`](../scripts/docs/update_spec.md), honor its supported-key boundary, then rerun the final quality gate and Step 7 export |
| User explicitly requests spec refinement | Run [`refine-spec`](./stages/refine-spec.md) after Design Spec Gate 1 and before lock Gate 2 |
| Data charts exist | Run [`verify-charts`](./stages/verify-charts.md) before export |
| User explicitly requests visual review | Run [`visual-review`](./stages/visual-review.md) before post-processing |
| User requests preview, selection, or annotation application | Use the default Generate pipeline and run [`live-preview`](./stages/live-preview.md) at the stage defined there; explicit Quick + preview intent falls back to default rather than dropping preview |
| User requests page transitions, auto-advance, or deck-wide animation settings without page-specific motion planning or an existing `animations.json` | Load [`animations`](../references/animations.md) and apply its export-level contract |
| `<project_path>/animations.json` already exists, the user explicitly requests per-slide/object-level animation control, or the effective Custom Animations outcome in `design_spec.md §I` is enabled | Run [`customize-animations`](./stages/customize-animations.md) after the final SVG quality gate and any enabled speaker-note pass, before Generate Step 7. A §IX `Motion suggestion` informs an active pass but never triggers it alone |
| Generate PPTX receives an explicit narration request or has effective Narration Audio enabled in `design_spec.md §I`; Enhance Native PPTX has a confirmed `audio.enabled: true` module | Run [`generate-audio`](./stages/generate-audio.md) after the owning route's notes/export readiness; Generate audio implies effective Speaker Notes enabled |

**Hard rule — profile, not fifth route**: The 1:1 beautify behavior uses the same Strategist → Executor → SVG export lifecycle as Generate PPTX. It changes content/page invariants; it does not define a separate artifact lifecycle.

**Hard rule — direct-generation profile, not a fifth route**: `quick-generate`
stays inside Generate PPTX but owns an explicit SVG → PPTX short circuit. Page
count alone never activates or blocks it. Conversion, bounded research, and
project-local resources remain available. Package capabilities may be requested
or agent-selected. Quick may consume exact Brand/Style/Layout/Deck workspaces as
flat authoring inputs; compiling reusable Master/Layout/placeholder structure
still requires the default lock-backed Generate pipeline.

---

## 4. Template and Master/Layout Boundary

**Hard rule — no direct structure grafting**: An existing PPTX or SVG is never upgraded in place by adding Master/Layout/placeholder structure. If reusable native structure is required:

1. Run [`create-template`](./create-template.md) to produce a separate validated workspace.
2. Pass that workspace root to [`generate-pptx`](./generate-pptx.md) Step 3.
3. Author new structured SVG pages whose Master/Layout contract exists from their first generated draft.
4. Export a new PPTX from those pages.

When a PPTX already contains native Master/Layout parts, `create-template` mirror may read and preserve those existing package facts in the new workspace. It does not infer missing historical intent. An incomplete or legacy SVG package may guide `standard` / `fidelity` visually, but it is not mutated into a structured template and cannot claim source-topology recovery.

**Hard rule — no automatic structure upgrade**: Free-design, brand-only, and style-only generation remains `pptx_structure.mode: flat`. Repeated Slide-local objects never trigger `structured`, Master/Layout promotion, placeholder inference, or deduplication. The minimal Master plus Blank Layout emitted by flat export is package scaffolding, not an inferred reusable design master.

| Input | Route behavior |
|---|---|
| Raw PPTX called a template + new content | Fill Native PPTX unless the user explicitly asks for a reusable template workspace |
| Any supported reference bundle or direct-text brief + reusable template request | Create Template |
| Current template workspace root + content | [`generate-pptx`](./generate-pptx.md) Step 3 |
| Legacy-flat Brand/Layout/Deck root satisfying its current kind contract; Layout/Deck also require current structured SVGs | [`apply-template-workspace`](./stages/apply-template-workspace.md) compatibility reader; Style has no flat form |
| Semantic-legacy or incomplete structured package | Create a new workspace through Create Template; do not migrate in place |
| Request to add a master directly to an existing PPTX/SVG | Unsupported; explain the Create Template → Generate PPTX lifecycle |

---

## 5. Create Template Child Workflows

| Selected kind | Behavior |
|---|---|
| `brand` | Dispatch to [`create-brand`](./create-template/create-brand.md); write identity only and no SVG roster |
| `style` | Dispatch to [`create-style`](./create-template/create-style.md); write reusable communication method and design direction only, with no SVG roster or native structure |
| `layout` | Dispatch to [`create-layout`](./create-template/create-layout.md); author brand-neutral, application-neutral structure and an SVG roster |
| `deck` | Dispatch to [`create-deck`](./create-template/create-deck.md); author descriptive recurring-application context with integrated identity, structure, and an SVG roster |

Create Template remains the fixed route name and owns the shared contract. These four documents are mutually exclusive child workflows, not additional top-level routes.

**Hard rule — classify reusable rules, not source completeness**: A complete
PPTX does not automatically select Deck. Use Brand when only identity is
stable; use Style when reusable communication method and design direction
should travel without identity truth, page prototypes, or native
structure; use Layout when structure is brand-neutral and the communication
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

## 7. Template Selection Boundary

| User input | Behavior |
|---|---|
| No explicit template intent/root/handoff | Skip Step 3, use free design, and open Stage 1 directly without reading indexes |
| Explicit template discovery or selection request | Enter Step 3; offer free design plus registered library workspaces from the four indexes below, then confirm and install before Stage 1 |
| Explicit current workspace root containing `templates/design_spec.md` | Preserve it as an `explicit` Step-3 candidate; an exact registered-root match may be displayed as `library` |
| Bare template/brand name or style label | Do not resolve it to a local path; treat it as a style brief |
| “What templates exist?” in chat | List indexed workspace paths; selection still requires the user to return an exact root |

The default UI and chat discovery read only these indexes. Never scan the
corresponding directories to construct or supplement the catalog:

| Kind | Discovery index |
|---|---|
| Brand | [`brands_index.json`](../templates/brands/brands_index.json) |
| Style | [`styles_index.json`](../templates/styles/styles_index.json) |
| Layout | [`layouts_index.json`](../templates/layouts/layouts_index.json) |
| Deck | [`decks_index.json`](../templates/decks/decks_index.json) |

**Hard rule — triggered selection precedes communication confirmation**: When
Step 3 is triggered, confirm free design or selected roots and complete
workspace validation/installation before Stage 1. In an ordinary free-design
run, no selection phase exists and Stage 1 starts directly. Stage 2
`template_application` decides how an already installed template is used; it
never selects a template.

**Forbidden — fuzzy resolution**: Never resolve a bare name to a local template
directory on the user's behalf. A library choice comes from an index-derived
root; an unregistered workspace requires an explicit root, including the exact
validated workspace handed off by Create Template in the current conversation.
