---
description: Deterministic route selection rules for PPT Master requests
---

# Routing Rules

Route selection authority for PPT Master. Use this file before entering the main pipeline or any standalone workflow.

**Hard rule**: If this file conflicts with a route summary in `SKILL.md`, `AGENTS.md`, or a user-facing doc, this file wins for route selection. After a route is selected, the target workflow file or `SKILL.md` owns execution details.

---

## 1. Routing Discipline

| Rule | Behavior |
|---|---|
| Deterministic routes | Do not ask the user to choose when a request matches a defined route. Enter the route directly. |
| Missing prerequisite | State the missing prerequisite and stop that route. Do not route around the prerequisite with an invented alternative. |
| Ambiguous deck optimization | Ask exactly one discriminator question: preserve original page count/order and slide wording, or treat the deck as source material and restructure it? |
| Explicit user override | Honor explicit route instructions only when the route preconditions are satisfied. |
| Summary conflict | Use this file for route choice, then read the route's own workflow file before executing it. |

**Forbidden - route-choice prompts**: Do not present multiple implementation paths when this file already defines the route. Ordinary style choices and finite options belong at the next existing confirmation gate.

### 1.1 SVG Page-Design Scope

| Route family | SVG contract |
|---|---|
| Main SVG pipeline and `beautify-pptx` | Every visible output-page object is authored in the completed page SVG; templates and locks guide authoring but are not export-time visual overlays. |
| `create-template` | Each reusable template SVG is a complete visual reference plus explicit PowerPoint structure metadata. Library and project outputs use the same routing: required `templates/`, optional `images/` / `icons/`, and optional on-demand review output under `exports/`. |
| `template-fill-pptx` and `native-enhance-pptx` | Native PPTX editing routes. They retain their OOXML contracts and are not forced through SVG. |
| Animation, transition, speaker-note, and narration workflows | Presentation behavior/content outside the visible page-design layer; keep their dedicated sidecars and package post-processing. |

**Hard rule**: Apply SVG page-design closure only after selecting an SVG-authoring route. Do not reroute a native PPTX operation merely to make every package-level capability pass through SVG.

---

## 2. Main Route Matrix

| Request shape | Trigger | Route | Forbidden route | Preconditions | Output contract | Stop condition |
|---|---|---|---|---|---|---|
| Topic only, no source facts | User supplies only a topic name or requirement and no substantive source material | [`topic-research`](./topic-research.md), then main `SKILL.md` pipeline | Direct main pipeline with invented facts | Web/source gathering is allowed or user supplies facts | Research material becomes source input for Step 1 | Stop if facts cannot be gathered and the user supplies no source |
| Source material can be reworked into a new story | PDF/DOCX/URL/Markdown/text/conversation content, or PPTX treated as content | Main `SKILL.md` pipeline | Direct PPTX edit workflows | Source content exists or is available in conversation | `design_spec.md`, `spec_lock.md`, `svg_output/`, exported PPTX | Stop at Step gates when required artifacts are missing |
| PPTX as re-architectable source | User allows page count/order/outline to change, or asks to split/merge/drop/reorder slides | Main `SKILL.md` pipeline with `ppt_to_md.py` plus PPTX intake | [`beautify-pptx`](./beautify-pptx.md) | PPTX source exists | Markdown content plus `analysis/source_profile.json`; Strategist may re-outline | Stop if user requires exact 1:1 page preservation |
| Explicit template workspace path | User provides a current brand/layout/deck workspace root containing `templates/design_spec.md`, or a compatible legacy-flat root containing `design_spec.md` | Main `SKILL.md` Step 3 | Fuzzy template lookup by bare name; passing a current workspace's inner `templates/` directory instead of its root | Path resolves, frontmatter kind is valid, and every deck/layout SVG satisfies the current structured Master/Layout/slot contract | Stage `templates/` plus any existing `images/` and `icons/` into the target project peers; consume the target project's own root in place; never consume the review-only `exports/` directory | Route only a structurally legacy SVG contract to [`restore-pptx-structure`](./restore-pptx-structure.md) before Step 3; a legacy-flat directory shape alone remains compatible and does not trigger restoration |

---

## 3. PPTX-Specific Routes

| Request shape | Trigger | Route | Forbidden route | Preconditions | Output contract | Stop condition |
|---|---|---|---|---|---|---|
| Raw PPTX template plus new material/topic | "Use this PPT template to generate a PPTX", "fill this deck", "replace copy", native slide shell reuse | [`template-fill-pptx`](./template-fill-pptx.md) | Main SVG pipeline directly from raw PPTX template | Source PPTX plus content material or topic brief | New native PPTX in `exports/`, cloned/patched by OOXML | Stop if user instead wants a reusable template package |
| Existing PPTX, preserve page split and wording | "Beautify", "re-layout", "make more professional" with same slide count/order and verbatim text | [`beautify-pptx`](./beautify-pptx.md) | Main pipeline if page count/order changes | Single source PPTX | Regenerated deck through SVG pipeline, one source slide to one output slide | Stop if user asks to split/merge/drop/reorder |
| Finished PPTX, native enhancement only | Add notes, recorded narration, auto-advance, transitions, or stable-layout metadata | [`native-enhance-pptx`](./native-enhance-pptx.md) | SVG regeneration | Finished PPTX exists; content/layout should stay stable | Patched PPTX through direct OOXML | Stop if user asks for visual redesign |
| PPTX/reference design should become a reusable template | "Create a template", "make reusable", "build template from this deck/design", including a template for one named initialized project | [`create-template`](./create-template.md) | `template-fill-pptx` one-off fill | PPTX/design reference exists, or the user gives an explicit template-creation brief; project output additionally requires an initialized target project | Both scopes produce one workspace with required `templates/`, optional `images/` / `icons/`, and optional on-demand `exports/<id>_template_preview.pptx`; library root is `skills/ppt-master/templates/<kind>/<id>/`, project root is `projects/<name>/`; only library scope is registered | Return the exact workspace root for main Step 3; the target project's own root may resume in place after validation |

**Hard rule**: Raw PPTX template plus "generate PPTX" routes to `template-fill-pptx` by default. A raw PPTX is not a Step 3 template until `create-template` has produced a reusable template directory.

**Hard rule**: Beautify is strictly 1:1. Any page count or page order change is re-architecture and therefore the main pipeline, not beautify.

---

## 4. Optional and Post-Route Workflows

| Request shape | Trigger | Route | Preconditions | Output contract | Stop condition |
|---|---|---|---|---|---|
| Brand identity setup | Brand asset, brand site URL, branded PPTX/PDF, or explicit brand setup request | [`create-brand`](./create-brand.md) | Brand source exists or can be inspected | Complete identity-only workspace under `templates/brands/<id>/` | Stop if no brand source or brand intent exists |
| Continue a split-mode project | "Continue generating `projects/<name>`" after the planning session | [`resume-execute`](./resume-execute.md) | Project has planning-session artifacts | Execution-session SVG generation and export | Stop if required planning artifacts are missing |
| Refine spec before generation | User explicitly asks to refine/review/revise the spec before SVG work, or confirms `refine_spec: true` | [`refine-spec`](./refine-spec.md) | Strategist confirmation stage completed | Revised `design_spec.md` and `spec_lock.md` before Step 5/6 | Stop until user approves the refined spec |
| Restore legacy PowerPoint structure | Existing structured/template SVGs use unmapped `baseline`, `preserve`, `layout_strategy: distill`, `data-pptx-layout-kind`, `distilled`/`utility`, direct atomic placeholders, or an incomplete root Master identity | [`restore-pptx-structure`](./restore-pptx-structure.md) before generation/export or before Step 3 template consumption | Legacy structured SVG project/package exists; original PPTX/native facts are used when available; an explicit `mode: flat` free-design/brand-only project and a flat package directory are not triggers | Current structured SVG contract plus unique `pptx_masters` / `pptx_layouts` definitions and complete `page_pptx_layouts` assignments | Stop if structure cannot be restored without an explicit design decision |
| Data chart calibration | Generated deck contains data charts | [`verify-charts`](./verify-charts.md) between Step 6 and Step 7 | SVG pages exist | Calibrated chart coordinates before export | Stop on chart geometry errors until fixed |
| Object-level animation tuning | User asks for animation order, timing, effects, or object reveal behavior | [`customize-animations`](./customize-animations.md) | SVG groups / exported context exist | `animations.json` or validated animation config | Stop if requested target objects cannot be identified |
| Live preview / element selection / annotations | User mentions live preview, preview, visual check in browser, clicking/selecting an element, or applying browser annotations | [`live-preview`](./live-preview.md) | Project exists; for annotation apply, generated SVGs exist | Running preview service or applied annotations plus re-export | Stop only if project path or SVGs are missing |
| Visual review | User explicitly asks for per-page visual self-check or visual rubric | [`visual-review`](./visual-review.md) between Step 6 and Step 7 | SVG pages exist | Visual review findings and fixes before post-processing | Do not run without explicit user request |
| Recorded narration / video export | User asks for narration, voiceover, or video-style export | [`generate-audio`](./generate-audio.md) after post-processing | Notes and exported deck exist | Audio files and optional narration-embedded PPTX | Stop for the workflow's single backend/voice confirmation |

---

## 5. Template Name Boundary

| User input | Route behavior |
|---|---|
| Explicit current brand/layout/deck workspace root containing `templates/design_spec.md` | Enter main Step 3 template option; use the workspace root, not its inner `templates/` directory |
| Explicit legacy-flat root containing `design_spec.md` | Enter main Step 3 through the compatibility reader; flat packaging alone does not require structure restoration |
| Bare template name, brand name, style label, or vague "use a template" | Do not trigger Step 3; treat as style input for Strategist confirmation stage |
| User asks "what templates exist?" | Answer as Q&A by listing indexed paths; do not advance the pipeline |
| Raw `.pptx` called a template | Route by §3, usually `template-fill-pptx`; never treat it as a Step 3 template path |

**Forbidden - fuzzy resolution**: Do not resolve bare names to local template directories on the user's behalf. The user must provide the path that enters Step 3. For every current template kind, that path is the workspace root.
