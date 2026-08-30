---
description: Create Brand workflow for an identity-only reusable workspace without an SVG page roster.
---

# Create Brand Workflow

Enter only after [`Create Template`](../create-template.md) dispatches `kind: brand`. Create Template owns dispatch, scope, the confirmation gate, collision preflight, registration, completion, and the Generate handoff; Create Brand owns brand analysis, the identity brief, the identity-only spec, adopted assets, and brand validation.

**Hard rule — child workflow, not a top-level route**: executes only inside Create Template under its single shared gate; never a competing entry or second confirmation.

**Hard rule — identity only**: a brand owns color, typography, logo, voice, and icon style — no canvas, spacing system, page roster, SVG prototype, Master/Layout graph, placeholder contract, or preview PPTX.

**Invocation**: §1–2 feed Create Template Steps 2–3; after Step 4 resolves and preflights `<template_workspace>` / `<design_spec_path>`, §3 materializes; §4 returns evidence to Steps 5, 7, and 8; Step 6 is always skipped.

## 1. Brand Input Analysis

| Input | Read path | Facts it may support |
|---|---|---|
| SVG logo | Inspect literal `fill` / `stroke` | Logo asset and literal colors |
| PNG/JPG logo | Inspect visually | Logo asset and approximate colors |
| Official brand site or manual | Convert/read | Published colors, fonts, voice, usage restrictions |
| Branded PPTX/PDF | Source converters and theme/package facts | Observed colors, typography, logo assets, tone |
| Pasted text, Markdown, or document | Direct text or the parent's converted output | Explicit identity values, usage rules, voice, restrictions |
| Verbal brief | The user's words | Any explicitly supplied field |
| Mixed bundle | Every applicable row with per-source provenance | Combined evidence; conflicts go to the shared gate |
| No reference | None | Empty skeleton only when explicitly requested |

Provenance labels for the proposal and the Color Scheme table: `fact` (literal value from an official asset or manual), `user` (explicitly authored by the user in any carrier), `approx` (visual estimate or observed pattern). **Hard rule — no inferred brand truth**: never promote an estimate, presentation convention, or observed neutral into an official fact, and never invent semantic success/warning/error colors.

## 2. Identity Brief Fields

Surface through Create Template's Step 2–3 gate: brand display name and use cases (required); primary color (required, `#RRGGBB` plus provenance); secondary/accent/text/background colors (only when confirmed or evidenced, each with provenance); title/body typography (required, provenance in prose when unofficial); logo (optional: default presenting entity, file, usage rule, trademark restriction); voice and tone (required: formality, person, emoji policy, abbreviation policy); icon style (required: `linear`, `filled`, `duotone`, or a confirmed custom description); adopted assets (optional, with included/excluded reasons). An explicitly requested empty skeleton leaves every value as a TODO comment, stops after writing the file, and is reported as incomplete and unregistered.

## 3. Materialize the Confirmed Brand

Write only `templates/design_spec.md` (project: `design_spec.brand.<brand_id>.md`), plus optional `images/` (logo/photos when adopted) and `icons/` (branded icon overrides when adopted); never create optional directories or `exports/` to keep empty paths, and leave pre-existing project scaffolding untouched. References use `../images/<name>` and `../icons/<name>`.

```markdown
---
brand_id: <confirmed slug>
kind: brand
summary: <one-line use case>
primary_color: "#XXXXXX"
---

# <Display Name> Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview
| Property | Value |
|---|---|
| Brand Name | <display name> |
| Use Cases | <summary> |
| Tone | <one-line tone summary> |
| Sources | <official URL or bundled asset paths; version/retrieval date when known> |

## II. Color Scheme
| Role | HEX | Provenance |
|---|---|---|
| primary | #XXXXXX | fact \| approx \| user |
| secondary | #XXXXXX | fact \| approx \| user |
| accent | #XXXXXX | fact \| approx \| user |

## III. Typography
| Role | Family | Weight |
|---|---|---|
| title | <family> | <weight> |
| body | <family> | <weight> |

## IV. Logo
- File: `../images/logo.<ext>` or `none`
- Usage: cover-only \| every-page \| never

## V. Voice & Tone
- Formality: formal \| neutral \| casual
- Person: informal-you \| formal-you \| we \| none
- Emoji: allowed \| forbidden
- Abbreviations: spell-out-first \| common-abbrev-allowed

## VI. Icon Style
- Preference: linear \| filled \| duotone \| <custom>

## VII. Visual Assets
- Only when real `images/` or `icons/` assets exist.
```

Keep a supplied logo's extension; with several lockups use descriptive filenames and name exactly one default presenting entity; create another workspace when a subsidiary/campaign identity differs materially.

## 4. Brand Validation

Return to Create Template: the spec exists with `brand_id`, `kind: brand`, `summary`, `primary_color`; `brand_id` matches the library workspace ID; sections I–VI exist and Page Roster / Signature Design Elements do not; no `*.svg`, `native_structure_mode`, Master/Layout, placeholder, canvas, or page-count field; every color is `#RRGGBB` with the primary row matching frontmatter and provenance `fact` / `approx` / `user`; every referenced asset exists in the workspace and no empty optional directory was created.

Both scopes run `svg_quality_checker.py "<template_workspace>/templates" --template-mode --canonical-authoring`; library adds `register_template.py <brand_id> --kind brand --dry-run` and, after the gate, Step 7 registers with `register_template.py <brand_id> --kind brand`. Project scope skips both registrar commands and reports `Not registered (project workspace)`. Downstream consumption always uses the explicit root through Generate Step 3; a bare brand name never activates it.
