---
description: Create Style child workflow for a reusable communication method and visual-default workspace without page prototypes.
---

# Create Style Workflow

Enter only after [`Create Template`](../create-template.md) dispatches `kind: style`. Create Template owns dispatch, scope, the confirmation gate, collision preflight, registration, completion, and the Generate handoff; Create Style owns the reusable communication method, page-role vocabulary, evidence discipline, visual-system defaults, image/icon direction, review focus, and the roster-free spec.

**Hard rule — child workflow, not a top-level route**: executes only inside Create Template under its single shared gate.

**Hard rule — method and defaults only**: a Style owns a reusable way to argue, express evidence, and coordinate non-binding design defaults — no current-project communication contract, brand identity, page geometry, canvas, SVG prototype, Master/Layout graph, placeholder contract, application contract, asset inventory, carrier eligibility, image source, or capability whitelist.

**Hard rule — no page prototypes**: Style contributes only its Design Spec — no SVGs, review PPTX, or empty `images/` / `icons/` / `exports/`; files another kind owns in a shared project workspace are left untouched.

**Invocation**: §1–2 feed Create Template Steps 2–3; after Step 4 resolves `<template_workspace>` / `<design_spec_path>`, §3 materializes; §4 returns evidence to Steps 5, 7, and 8; the structured-preview step is always skipped.

## 1. Style Input Interpretation

| Evidence | May inform | Must not become |
|---|---|---|
| Direct brief, text, document, or website | Argument flow, claim discipline, page-role vocabulary, data-expression rules, review focus | The current project's audience, objective, outline, page count, or claims |
| PPTX, PDF, image, or SVG reference | Visual-system tendencies, density, decoration, image and icon treatment | A copied roster, canvas, Master/Layout graph, or fixed geometry |
| Brand or organization material | A lower-priority fallback direction when the user wants it generalized | Official identity truth, logos, proprietary palettes, voice, trademarked rules |
| Existing mode / visual-style / image-rendering catalog entry | A preferred seed plus a concise Style-owned overlay | A duplicated catalog file |

**Mandatory — series-aware PPTX analysis**: before inferring cross-page cadence from a composite reference, distinguish coherent finished-deck series from page/layout libraries; infer cadence only within a series and treat library pages as independent composition evidence. Preserve provenance in `Style Overview`; keep user-authored decisions distinct from AI defaults; reject organization-confidential examples and never generalize proprietary frameworks. **Reference — not a constraint**: preferred catalog mode, visual style, rendering, fallback palette, or font stack seed the Stage-2 solution; they are never execution locks and never bypass confirmation.

## 2. Style Brief and Schema

Add to Create Template Step 2 (all required): Style ID (filesystem-safe portable slug) and display name; best fit (reusable decision/explanation/expression situations without binding audience or outcome); reusable intent; communication method (argument flow, page-message discipline, claim/evidence treatment; preferred mode optional); page-role vocabulary (roles, jobs, evidence obligations, composition tendencies — no order or inclusion policy); evidence and data expression (chart, table, source, editability guidance without numeric quotas); visual-system defaults (composition, density, decoration, color behavior, native-text character; seeds and literal fallbacks optional; carrier and construction eligibility stay downstream); image and icon direction (rendering, centrality, recurrence, treatment defaults without source restrictions, inventory, or page mapping); review focus (checks applied only if the user explicitly activates visual review).

```markdown
---
style_id: <confirmed slug>
kind: style
summary: <one-line reusable method and design-default fit>
keywords: [<three-to-five discovery tags>]
---

# <Style Name> — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview
| Property | Value |
|---|---|
| Style Name | <display name> |
| Best Fit | <reusable selection context> |
| Reusable Intent | <stable method/design outcome> |
| Sources | <URLs, references, or user brief; date/version when known> |

## II. Communication Method
- **Preferred Mode**: <catalog id or custom; omit when none>
- **Mode References**: <catalog ids used by a custom seed; omit when none>
- **Mode Behavior**: <required for custom; omit for a preset>
- **Argument Flow** / **Page Message Discipline** / **Claim Discipline**: <prose>

## III. Page Role Vocabulary
| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|

## IV. Evidence & Data Expression
- **Argument Trace** / **Charts** / **Tables** / **Sources** / **Native Editability**: <prose>

## V. Visual System Defaults
- **Preferred Visual Style** / **Visual Style References** / **Visual Style Behavior**: <as for Mode>
- **Composition** / **Density** / **Decoration** / **Color Behavior** / **Typography Character**: <prose; no identity claim>

### Fallback Color Scheme (conditional)
| Role | HEX | Purpose |
|---|---|---|

### Fallback Typography (conditional)
| Role | Primary | Fallback Tail | Character |
|---|---|---|---|

## VI. Image & Icon Direction
- **Preferred Image Rendering** / **Image Rendering References** / **Image Rendering Behavior**: <as for Mode>
- **Image Usage** / **Image Treatment** / **Icon Treatment**: <prose; library and inventory stay Stage-2 decisions>

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply only after the user explicitly activates visual review. It never triggers that stage.
- <style-specific check>
```

Omit either fallback subsection without literal values; exact colors use `#RRGGBB`. A supplied Brand or Deck identity replaces overlapping fallback colors, fonts, voice, and icon identity as one decision without erasing the method. Preferred seeds are recommendations; a preset must be a real catalog ID, and `custom` keeps only real references actually used plus behavior prose. **Hard rule — Style never becomes a capability policy**: it may tune treatment, weight, density, recurrence, and coherence but never bans or requires a carrier, selects image source, or narrows primitives, presets, composition, Boolean, or freeform. `Page Role Vocabulary` is a vocabulary, not a roster: no order, status, count, filenames, identities, slots, or content policy.

## 3. Materialize the Confirmed Style

Write only `templates/design_spec.md` (project: `design_spec.style.<style_id>.md`); create or adopt no images, icons, SVGs, payloads, or exports — references stay textual provenance.

## 4. Style Validation

Return to Create Template: non-empty `style_id`, `kind: style`, `summary`, and three-to-five `keywords` with no other frontmatter field; `style_id` matches the library workspace ID; sections I–VII exist with preset seeds resolving to real IDs and custom seeds carrying behavior prose; no `*.svg`, asset directory, export, or payload; no `primary_color`, canvas, page-count/type, replication, structure, Master/Layout, placeholder, Page Roster, or Signature Design Elements; no current-project audience, objective, delivery context, afterlife, outline, page assignment, icon inventory, or image mapping; Brand-only and Deck-only sections absent, fallback subsections keeping their exact names; `Review Focus` carries exactly one `<!-- visual-review-trigger: explicit-user-only -->` marker and cannot activate the stage.

Both scopes run `svg_quality_checker.py "<template_workspace>/templates" --template-mode --canonical-authoring`; library adds `register_template.py <style_id> --kind style --dry-run` and, after the gate, Step 7 registers with `register_template.py <style_id> --kind style`. Project scope skips both and reports `Not registered (project workspace)`. Downstream consumption uses the explicit root through Generate Step 3; a bare Style name or style description never activates it.
