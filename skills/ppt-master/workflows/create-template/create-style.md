---
description: Create Style child workflow for a reusable communication method and visual-default workspace without page prototypes.
---

# Create Style Workflow

Enter this child workflow only after [`Create Template`](../create-template.md) dispatches `kind: style`.

## Responsibility Boundary

| Owner | Responsibilities |
|---|---|
| Create Template | Child-workflow dispatch plus the shared `library` / `project` scope, confirmation gate, collision preflight, registration, completion, and Generate PPTX handoff contract |
| Create Style | Reusable communication method, page-role vocabulary, evidence discipline, visual-system defaults, image/icon direction, review focus, and the roster-free `design_spec.md` |

**Hard rule — child workflow, not a top-level route**: Create Style executes only inside Create Template. It uses the parent workflow's single shared confirmation/preflight/registration contract and never creates a competing entry route or second confirmation gate.

**Hard rule — method and defaults only**: A Style owns a reusable way to argue, express evidence, and coordinate non-binding design defaults. It owns no current-project communication contract, reusable brand identity, page geometry, canvas, SVG prototype, Master/Layout graph, placeholder contract, application contract, visible asset inventory, carrier eligibility, image source, or local authoring-capability whitelist.

**Hard rule — no page prototypes**: Style contributes only its own Design Spec. Do not create page SVGs, a review PPTX, or empty `images/`, `icons/`, or `exports/` directories. In a project workspace shared with another kind, files that kind owns are not Style output and are left untouched.

## Invocation Points

1. Use §1–2 below for Style analysis and brief fields, then execute Create Template Steps 2–3 with those child-owned fields.
2. After Create Template Step 4 resolves and preflights `<template_workspace>` and `<design_spec_path>`, use §3 to materialize the confirmed Style.
3. Run §4, then return its evidence to Create Template Steps 5, 7, and 8. Create Style always skips the shared structured-preview step.

## 1. Style Input Interpretation

Use every supplied reference only as evidence for reusable method and design defaults:

| Evidence | May inform | Must not become |
|---|---|---|
| Direct brief, text, document, or website | Argument flow, claim discipline, page-role vocabulary, data-expression rules, and review focus | The current project's audience, objective, outline, page count, or source claims |
| PPTX, PDF, image, or SVG reference | Visual-system tendencies, density, decoration, image treatment, and icon treatment | A copied page roster, canvas contract, Master/Layout graph, or fixed geometry |
| Brand or organization material | A lower-priority fallback direction when the user explicitly wants it generalized | Official identity truth, logos, proprietary palettes, brand voice, or trademarked presentation rules |
| Existing mode, visual-style, or image-rendering catalog entry | A preferred catalog seed plus a concise Style-owned overlay | A duplicated copy of the catalog file |

**Mandatory — series-aware PPTX analysis**: Before inferring cross-page cadence from a composite PPTX reference, distinguish coherent finished-deck series from page/layout libraries. Infer cadence only within each coherent series; treat library pages as independent composition evidence, never as one ordered narrative run.

Preserve source provenance in `Style Overview`. Keep exact user-authored method decisions distinct from AI-derived defaults. Reject organization-confidential examples and do not generalize proprietary frameworks into a reusable Style.

**Reference — not a constraint**: A Style may prefer a catalog mode, visual style, image rendering, fallback palette, or fallback font stack. These values seed the normal Stage-2 solution; they are not execution locks and never bypass user confirmation.

## 2. Style Brief and Schema

Add these child-owned requirements to Create Template Step 2:

| Field | Requirement |
|---|---|
| Style ID and display name | Required; `style_id` is a filesystem-safe portable slug (prefer ASCII for interoperability) |
| Best fit | Required; describe reusable decision, explanation, or expression situations without binding a target audience or outcome |
| Reusable intent | Required; state what the method and design defaults should consistently achieve |
| Communication method | Required; argument flow, page-message discipline, and claim/evidence treatment; a preferred mode is optional |
| Page-role vocabulary | Required; reusable semantic roles and their jobs, evidence obligations, and composition tendencies; no order or inclusion policy |
| Evidence and data expression | Required; chart, table, source, and editability guidance without numeric content quotas |
| Visual-system defaults | Required; composition, density, decoration, color behavior, and native-text character; catalog seeds and literal fallbacks are optional, while carrier and native-construction eligibility remain downstream |
| Image and icon direction | Required; rendering, centrality, recurrence, and treatment defaults without source restrictions, asset inventory, or page mapping |
| Review focus | Required; extra checks to apply only if the user explicitly activates visual review |

Write this roster-free schema:

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
| Sources | <source URLs, bundled references, or user brief; include date/version when known> |

## II. Communication Method
- **Preferred Mode**: <catalog id or custom; omit when none>
- **Mode References**: <catalog ids actually used by a custom seed; omit when none>
- **Mode Behavior**: <required for custom; omit for a preset>
- **Argument Flow**: <reusable reasoning progression>
- **Page Message Discipline**: <relationship among question, title, message, and proof>
- **Claim Discipline**: <treatment of facts, assumptions, implications, and recommendations>

## III. Page Role Vocabulary
| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| <semantic role> | <job> | <proof requirement> | <non-geometric tendency> |

## IV. Evidence & Data Expression
- **Argument Trace**: <claim-to-evidence relationship>
- **Charts**: <selection, labeling, annotation, and decoration behavior>
- **Tables**: <comparison, hierarchy, and emphasis behavior>
- **Sources**: <citation and uncertainty treatment>
- **Native Editability**: <when editable data/native shapes are preferred>

## V. Visual System Defaults
- **Preferred Visual Style**: <catalog id or custom; omit when none>
- **Visual Style References**: <catalog ids actually used by a custom seed; omit when none>
- **Visual Style Behavior**: <required for custom; omit for a preset>
- **Composition**: <page-scale relationships without fixed geometry>
- **Density**: <information and whitespace rhythm>
- **Decoration**: <shape, rule, elevation, and ornament behavior>
- **Color Behavior**: <role and contrast behavior; no identity claim>
- **Typography Character**: <hierarchy and register; no identity claim>

### Fallback Color Scheme
| Role | HEX | Purpose |
|---|---|---|
| <role> | #RRGGBB | <fallback use> |

### Fallback Typography
| Role | Primary | Fallback Tail | Character |
|---|---|---|---|
| <role> | <family> | <ordered fallbacks> | <typographic job> |

## VI. Image & Icon Direction
- **Preferred Image Rendering**: <catalog id or custom; omit when none>
- **Image Rendering References**: <catalog ids actually used by a custom seed; omit when none>
- **Image Rendering Behavior**: <required for custom; omit for a preset>
- **Image Usage**: <semantic role and frequency tendency>
- **Image Treatment**: <crop, framing, overlay, and caption behavior>
- **Icon Treatment**: <shape/stroke/fill behavior; actual library and inventory remain Stage-2 decisions>

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->
> Apply this section only after the user explicitly activates visual review. It never triggers that stage.

- <style-specific answer, evidence, hierarchy, legibility, or scan-path check>
```

`Fallback Color Scheme` and `Fallback Typography` are conditional; omit either subsection when the Style has no literal fallback values. Exact fallback colors use `#RRGGBB`. A supplied Brand or Deck identity replaces overlapping fallback colors, font families, voice, and icon identity as one identity decision; it does not erase the Style's communication method or evidence discipline.

`Preferred Mode`, `Preferred Visual Style`, and `Preferred Image Rendering` are recommendation seeds. The current project's confirmed Stage-2 values remain authoritative. A preset value must be a real ID in its matching catalog. For `custom`, retain only real catalog references actually used as a comma-separated ID list and include the matching behavior prose.

**Hard rule — Style never becomes a capability policy**: Style prose may tune
treatment, visual weight, density, recurrence, and coherence. It never bans a
carrier or requires carrier coverage, never selects image source, and never
narrows primitives, Office presets, independent composition, Boolean, or
necessary freeform. Explicit current-project requirements remain upstream.

`Page Role Vocabulary` is a semantic vocabulary, not a Page Roster. Do not assign order, required/optional/repeatable status, page count, filenames, Master/Layout identities, slots, or fixed/replaceable/example-only content policy.

## 3. Materialize the Confirmed Style

Create Template supplies an already resolved and collision-checked `<template_workspace>` and `<design_spec_path>`. Write only:

```text
<template_workspace>/
└── templates/
    └── design_spec.md          # project scope: design_spec.style.<style_id>.md
```

Do not create or adopt images, icons, SVGs, native payloads, or review exports. References remain textual provenance; they are not portable Style assets.

## 4. Style Validation

Return these facts to Create Template:

- The Design Spec contains non-empty `style_id`, `kind: style`, `summary`, and three-to-five `keywords`; no other frontmatter field exists.
- `style_id` matches the confirmed workspace ID in library scope.
- Required sections I–VII exist; preset seeds resolve to real catalog IDs, while custom seeds include behavior prose and only real comma-separated catalog references.
- No `*.svg`, optional asset directory, review export, or native payload was created.
- No `primary_color`, canvas, page-count, page-type, replication, native-structure, Master/Layout, placeholder, Page Roster, or Signature Design Elements field exists.
- No current-project target audience, communication objective/outcome, delivery context, artifact afterlife, content outline, page assignment, icon inventory, or image-resource mapping exists.
- Brand-only identity sections (`Brand Overview`, `Color Scheme`, `Typography`, `Logo`, `Voice & Tone`, and `Icon Style`) and Deck-only `Template Overview` are absent. Conditional fallback subsections remain explicitly named `Fallback Color Scheme` and `Fallback Typography`.
- `Review Focus` contains exactly one `<!-- visual-review-trigger: explicit-user-only -->` marker; its localized prose explains the same boundary, and the section cannot activate visual review by itself.

For both scopes, Create Template Step 5 validates the portable Style contract without registration:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_workspace>/templates" --template-mode
```

For `library` scope, additionally validate the directory/index identity with:

```bash
python3 skills/ppt-master/scripts/register_template.py <style_id> --kind style --dry-run
```

After that gate passes, Create Template Step 7 registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <style_id> --kind style
```

For `project` scope, run only the shared validator, skip both registrar commands, and report `Not registered (project workspace)`. Downstream consumption always uses the explicit workspace root through Generate PPTX Step 3; a bare Style name or ordinary style description never activates it.
