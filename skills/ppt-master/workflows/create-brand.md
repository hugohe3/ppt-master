---
description: Generate a brand-only workspace under `templates/brands/<id>/` that captures colors, typography, logos, voice, and icon style without an SVG page roster.
---

# Create Brand Workflow

> Standalone preset-creation workflow. Output is a complete brand workspace at `skills/ppt-master/templates/brands/<brand_id>/`. A brand keeps the common workspace shape but omits the SVG page roster: Strategist locks identity while Executor designs pages freely.

This workflow edits the global brand library, not any specific `projects/<x>/`. Consumption follows the same explicit-path rule as layout templates (see [Downstream consumption](#downstream-consumption-informational) at the end).

> Companion: [`create-template.md`](./create-template.md) generates full templates with SVG pages. Use `create-brand.md` when the user wants identity-only locking with free page layout.

## When to Run

| User signal | Action |
|---|---|
| "set up brand" / "extract brand from this logo" | Run this workflow |
| User provides a brand asset (logo / brand site URL / branded PPTX / brand PDF) and wants it locked across future projects | Run this workflow |
| User mentions brand color or font once for a single deck only | Skip — handle inline via Strategist h.5 |
| `templates/brands/<requested_id>/` already exists | Ask: update / replace / use a new id — never silently overwrite |

⛔ Never auto-trigger. Brand creation is a user-invoked identity setup; an empty `templates/brands/` is not an invitation to create one.

---

## Step 1: Detect input type

| Type | User-supplied input | Path |
|---|---|---|
| **A** Brand asset | Logo (SVG/PNG/JPG), brand site URL, branded PPTX, brand PDF | Step 2A — Asset extraction |
| **B** Verbal spec | User dictates HEX / font / tone directly in chat | Step 2B — Verbal capture |
| **C** Nothing | User wants to set up a brand but provides no asset and no spec | Step 2C — Empty skeleton |

---

## Step 2A: Asset extraction

Read assets directly using existing converters — no dedicated extraction script.

| Asset format | Read method | Extractable fields |
|---|---|---|
| SVG logo | `Read` the SVG; grep `fill=` / `stroke=` for HEX | colors (literal), logo file |
| PNG/JPG logo | `Read` (multimodal); AI vision identifies dominant colors | colors (approximate HEX, label `[approx]`), logo file |
| Brand site URL | `python3 skills/ppt-master/scripts/source_to_md/web_to_md.py <URL>`, then `Read` the result | color references, font references, voice/tone |
| Branded PPTX | `python3 skills/ppt-master/scripts/source_to_md/ppt_to_md.py <file>`, then read theme XML | colors, typography (literal) |
| Brand PDF | `python3 skills/ppt-master/scripts/source_to_md/pdf_to_md.py <file>` | voice/tone; sometimes color/font references |

Identify which of (colors / typography / logo / voice / icon style) the asset did NOT cover, then proceed to Step 3 for the rest. Most single assets cover 1–2 categories well.

**Provenance labels** for each field in the draft `design_spec.md`:
- `[fact]` — extracted directly (SVG fill HEX, PPTX theme XML)
- `[approx]` — visual estimate (PNG/JPG color picking)
- `[user]` — supplied via chat fill-in in Step 3

**Hard rule — brand truth boundary**: Use `fact` only for a literal value extracted from an official asset/manual. Use `user` for values dictated in chat. Values inferred from an existing deck, website appearance, raster sampling, or presentation convention remain `approx`. Keep approximate presentation neutrals minimal; do not invent a semantic info/success/alert palette and lock it as brand identity.

---

## Step 2B: Verbal spec capture

Ask once, bundled (do NOT itemize each field). Match the user's language. Example bundled prompt:

> "I'll record: primary / secondary / accent HEX, title font, body font, logo path (optional), tone (formal / neutral / casual), emoji allowed or not. Which do you want to lock now?"

Whatever the user gives is `[user]`-labelled. Skip Step 3 unless the user explicitly invites more fields.

---

## Step 2C: Empty skeleton

Write `templates/brands/<brand_id>/templates/design_spec.md` with the full schema, every value as a TODO comment. Tell the user where the file is. Do not register the incomplete skeleton; registration requires concrete identity values. No further prompting — the user owns it from here.

---

## Step 3: Chat fill-in (Type A only)

For fields not covered by the asset, ask the user in a single bundled message. Skip fields irrelevant to the user's intent.

| Field | When to ask |
|---|---|
| primary / secondary / accent HEX | always |
| text / bg HEX | only if dark-mode or inverted scheme mentioned |
| title / body font | when the asset gave no font reference |
| logo usage | when a logo file was provided |
| brand scope | when assets mix a company, product, subsidiary, or campaign identity |
| voice & tone | when audience or formality was mentioned |
| icon style preference | when icon consistency was mentioned |

---

## Step 4: Materialize the brand workspace

Create the required template source directory. Create `images/`, `icons/`, or `exports/` only when writing a real asset or derived artifact; never add placeholder files for empty directories.

```bash
mkdir -p "skills/ppt-master/templates/brands/<brand_id>/templates"
```

### Mandatory: `templates/design_spec.md`

```markdown
---
brand_id: <slug>
kind: brand
summary: <one-line use case, e.g. "ACME Corp marketing decks">
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
| Sources | <official URL or bundled asset paths; include retrieval/version date when known> |

## II. Color Scheme
| Role | HEX | Provenance |
|---|---|---|
| primary | #XXXXXX | fact \| approx \| user |
| secondary | #XXXXXX | fact \| approx \| user |
| accent | #XXXXXX | fact \| approx \| user |
| text | #XXXXXX | fact \| approx \| user; optional, default `#1A1A1A` |
| bg | #XXXXXX | fact \| approx \| user; optional, default `#FFFFFF` |

## III. Typography
| Role | Family | Weight |
|---|---|---|
| title | <family> | <weight> |
| body | <family> | <weight> |
| mono | <family> | optional |

## IV. Logo
- File: `../images/logo.<ext>` (relative to this design_spec.md)
- Usage: cover-only \| every-page \| never

## V. Voice & Tone
- Formality: formal \| neutral \| casual
- Person: informal-you \| formal-you \| we \| none
- Emoji: allowed \| forbidden
- Abbreviations: spell-out-first \| common-abbrev-allowed

## VI. Icon Style
- Preference: linear \| filled \| duotone   # optional, drives icon library search

## VII. Visual Assets (optional)
- Images and illustrations: `../images/` # brand visual assets
- Icons: `../icons/`                     # branded icon overrides
```

**Section scope rules**:
- Layout / canvas / spacing / radius / shadow / page roster / signature design elements are OUT of brand scope. Those live in layout / deck workspaces (`templates/layouts/<id>/templates/design_spec.md` or `templates/decks/<id>/templates/design_spec.md`) or `shared-standards.md`. Do NOT add those sections here.
- HEX must be `#RRGGBB`
- Font names are free strings; not validated against locally installed fonts
- §VII is fully optional — list only directories that actually exist
- A company/product family may share one preset when the user explicitly wants that scope. Name the combined scope in §I and identify the owner of every logo/lockup in §IV; never relabel a product mark as the company mark.
- One preset has one default presenting entity. Subsidiary/campaign assets may remain as explicit alternates, but they never silently replace the default identity; create a separate brand workspace when their colors, typography, or voice differ.
- Record official usage or trademark restrictions next to the affected asset. Do not turn an observed public logo into permission to imply affiliation, sponsorship, or endorsement.

### Optional: logo file

If the user provided a logo, copy it to `templates/brands/<brand_id>/images/logo.<ext>` and preserve its source extension. Use descriptive filenames when several lockups exist.

### Optional: visual asset directories

Copy brand photos and illustrations into the workspace `images/` directory. Copy branded icon overrides into `icons/`. Reference only directories and assets that actually exist in §VII of `templates/design_spec.md`.

### NOT created here

No SVG page roster, canvas spec, signature design elements, or preview PPTX. Do not create an empty `exports/` directory. If the user later wants brand-anchored page templates, run `create-template.md` with this brand as a style reference.

---

## Step 5: Validate, register, and hand off

Run the registrar in dry-run mode first. It validates the mandatory frontmatter, brand ID, required sections, roster-free scope, `#RRGGBB` colors and primary-color consistency, color provenance, and every referenced `images/` / `icons/` asset:

```bash
python3 skills/ppt-master/scripts/register_template.py --kind brand <brand_id> --dry-run
```

Fix every reported error, then register the same workspace:

```bash
python3 skills/ppt-master/scripts/register_template.py --kind brand <brand_id>
```

Emit the confirmation card:

```markdown
## ✅ Brand Saved
- Path: `skills/ppt-master/templates/brands/<brand_id>/`
- Files: templates/design_spec.md{, images/logo.<ext>}{, images/*}{, icons/*}
- Fields locked: <list>
- Provenance: <fact / approx / user counts>

How to use in a project:
- Include the brand workspace path in the initial Step 3 input, for example: "Create a Q4 summary using skills/ppt-master/templates/brands/<brand_id>/"
- Same explicit-path rule as layout templates: bare brand names never trigger
- May be supplied together with a layout template path; Step 3 fuses both into a single `design_spec.md` (brand wins on identity tokens, layout wins on page structure) — see `SKILL.md` Step 3
- To list available brands: open `templates/brands/brands_index.json`
- To edit: modify `templates/brands/<brand_id>/templates/design_spec.md`, then re-run `python3 skills/ppt-master/scripts/register_template.py --kind brand <brand_id>`
```

---

## Downstream consumption (informational)

Brand application happens in [`SKILL.md` Step 3](../SKILL.md) under the **same explicit-path rule as layout templates**:

| User input at SKILL.md Step 3 | Behavior |
|---|---|
| Explicit brand workspace path supplied | Step 3 resolves `templates/design_spec.md`, stages `templates/`, `images/`, and `icons/` into their project peers, and locks color / typography / logo / voice as truth at Step 4 |
| Bare brand name, brand mention without path, or silence | Skip — no auto-application based on directory count or any other implicit signal |
| Both a brand path and a layout template path supplied in the same message | Step 3 fuses both into a single `design_spec.md` inside `<project_path>/templates/` (brand wins on identity tokens, layout wins on page structure). See `SKILL.md` Step 3 for the field-precedence table and the two conflict gates that may surface a clarifying question |

`brands_index.json` is discovery-only (mirrors `layouts_index.json` semantics); listing brands never advances the pipeline.

---

## Notes

1. **Brand is identity, not layout** — colors / typography / logo / voice / icon style only. Page roster, canvas spec, and signature design elements belong to layout templates; do not duplicate them here.
2. **Common workspace routing** — brand assets use the same `templates/`, `images/`, `icons/`, and `exports/` routes as other template kinds; empty optional directories are omitted.
3. **No script dependency** — Step 2A reuses existing converters plus AI inline reading. A dedicated `brand_extract.py` is not introduced unless future user feedback demands batch processing or precise color picking from raster logos.
4. **Multi-brand support** — `templates/brands/` accepts any number of brands; agency / freelancer / multi-client workflows are natural.
5. **Precedence rule** — when a brand and a layout template both apply, Step 3 fuses them into one `design_spec.md`: brand wins on color / typography / logo / voice / icon style; layout wins on canvas / page roster / spacing / font-size hierarchy / signature visual elements. See `SKILL.md` Step 3 for the full precedence table.
