---
description: Create Brand workflow for an identity-only reusable workspace without an SVG page roster.
---

# Create Brand Workflow

Enter this child workflow only after [`Create Template`](../create-template.md) dispatches `kind: brand`.

## Responsibility Boundary

| Owner | Responsibilities |
|---|---|
| Create Template | Child-workflow dispatch plus the shared `library` / `project` scope, confirmation gate, collision preflight, registration, completion, and Generate PPTX handoff contract |
| Create Brand | End-to-end brand-specific analysis, identity brief, identity-only `design_spec.md`, adopted brand assets, and brand-specific validation |

**Hard rule — child workflow, not a top-level route**: Create Brand executes only inside Create Template. It uses the parent workflow's single shared confirmation/preflight/registration contract and never creates a competing entry route or second confirmation gate.

**Hard rule — identity only**: A brand owns color, typography, logo, voice, and icon style. It owns no canvas, spacing system, page roster, SVG prototype, Master/Layout graph, placeholder contract, or preview PPTX.

## Invocation Points

1. Use §1–2 below for brand analysis and identity fields, then execute Create Template Steps 2–3 with those child-owned fields.
2. After Create Template Step 4 resolves and preflights `<template_workspace>`, use §3 to materialize the confirmed identity.
3. Run §4, then return its evidence to Create Template Steps 5, 7, and 8. Create Brand always skips shared Step 6.

## 1. Brand Input Analysis

| Input | Read path | Facts it may support |
|---|---|---|
| SVG logo | Read the SVG and inspect literal `fill` / `stroke` values | Logo asset and literal colors |
| PNG/JPG logo | Inspect visually | Logo asset and approximate colors |
| Official brand site or manual | Convert/read the source | Published colors, fonts, voice, usage restrictions |
| Branded PPTX/PDF | Use the existing source converters and theme/package facts | Observed colors, typography, logo assets, and tone |
| Verbal brief | Use the user's words directly | Any identity field the user explicitly supplies |
| No reference | No analysis | Empty skeleton only when the user explicitly requests it |

Use these provenance labels in the proposal and final Color Scheme table:

- `fact` — literal value from an official asset or manual.
- `user` — value explicitly supplied by the user.
- `approx` — visual estimate or pattern observed in an existing deck/site.

**Hard rule — no inferred brand truth**: Do not promote a visual estimate, presentation convention, or observed neutral into an official brand fact. Do not invent semantic success/warning/error colors.

## 2. Identity Brief Fields

Surface these through Create Template's single shared Step 2–3 gate:

| Field | Requirement |
|---|---|
| Brand display name and use cases | Required |
| Primary color | Required; `#RRGGBB` plus provenance |
| Secondary/accent/text/background colors | Include only when confirmed or supported by evidence; every written color uses `#RRGGBB` plus provenance |
| Title/body typography | Required; retain provenance in surrounding prose when it is not official |
| Logo | Optional; identify the default presenting entity, file, usage rule, and any trademark restriction |
| Voice and tone | Required; formality, grammatical person, emoji policy, abbreviation policy |
| Icon style | Required; `linear`, `filled`, `duotone`, or a confirmed custom description |
| Adopted assets | Optional; list included and excluded candidates with reasons |

When the user explicitly requests an empty skeleton, all identity values remain TODO comments, materialization stops after writing the file, and Create Template reports that the workspace is incomplete and unregistered.

## 3. Materialize the Confirmed Brand

Create Template supplies an already resolved and collision-checked `<template_workspace>`. Write only:

```text
<template_workspace>/
├── templates/
│   └── design_spec.md
├── images/       # optional; logo/photos/illustrations only when adopted
└── icons/        # optional; branded icon overrides only when adopted
```

Do not create empty optional directories or `exports/`. Bitmap references from `templates/design_spec.md` use `../images/<name>`; branded icon references use `../icons/<name>`.

Write this personality-only schema:

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
| Sources | <official URL or bundled asset paths; include version/retrieval date when known> |

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
- Include this section only when real `images/` or `icons/` assets exist.
```

Preserve a supplied logo's extension. When multiple lockups exist, use descriptive filenames and name exactly one default presenting entity. Keep subsidiary/campaign alternates explicit; create another brand workspace when their identity differs materially.

## 4. Brand Validation

Return these facts to Create Template:

- `templates/design_spec.md` exists and contains `brand_id`, `kind: brand`, `summary`, and `primary_color`.
- `brand_id` matches the confirmed workspace ID in library scope.
- Required sections I–VI exist; Page Roster and Signature Design Elements do not exist.
- No `*.svg`, `native_structure_mode`, Master/Layout, placeholder, canvas, or page-count fields were written.
- Every color is `#RRGGBB`, the primary table row matches frontmatter, and provenance is `fact`, `approx`, or `user`.
- Every referenced asset exists under the same workspace; no empty optional directory or `exports/` directory was created.

For `library` scope, Create Template Step 5 validates with:

```bash
python3 skills/ppt-master/scripts/register_template.py <brand_id> --kind brand --dry-run
```

After that gate passes, Create Template Step 7 registers with:

```bash
python3 skills/ppt-master/scripts/register_template.py <brand_id> --kind brand
```

For `project` scope, skip both commands and report `Not registered (project workspace)`. Downstream consumption always uses the explicit workspace root through Generate PPTX Step 3; a bare brand name never activates it.
