---
description: Generate a brand-only template under `templates/brands/<id>/` — a design_spec.md that captures the user's colors / typography / logo / voice / icon style without an SVG page roster, so subsequent PPT projects inherit brand identity while keeping page layout free.
---

# Create Brand Workflow

> Standalone preset-creation workflow. Output is a brand template package at `skills/ppt-master/templates/brands/<brand_id>/`. Structurally a brand is a template minus the SVG page roster — Strategist locks the brand's color / typography / logo / voice as truth; Executor designs pages freely under those constraints.

This workflow edits the global brand library, not any specific `projects/<x>/`. Consumption follows the same explicit-path rule as layout templates (see [Downstream consumption](#downstream-consumption-informational) at the end).

> Companion: [`create-template.md`](./create-template.md) generates full templates with SVG pages. Use `create-brand.md` when the user wants identity-only locking with free page layout.

## When to Run

| User signal | Action |
|---|---|
| "set up brand" / "extract brand from this logo" / 建立品牌 / 做品牌规范 | Run this workflow |
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

---

## Step 2B: Verbal spec capture

Ask once, bundled (do NOT itemize each field). Match the user's language. Example bundled prompt:

> "I'll record: primary / secondary / accent HEX, title font, body font, logo path (optional), tone (formal / neutral / casual), emoji allowed or not. Which do you want to lock now?"

Whatever the user gives is `[user]`-labelled. Skip Step 3 unless the user explicitly invites more fields.

---

## Step 2C: Empty skeleton

Write `templates/brands/<brand_id>/design_spec.md` with the full schema, every value as a TODO comment. Tell the user where the file is. No further prompting — the user owns it from here.

---

## Step 3: Chat fill-in (Type A only)

For fields not covered by the asset, ask the user in a single bundled message. Skip fields irrelevant to the user's intent.

| Field | When to ask |
|---|---|
| primary / secondary / accent HEX | always |
| text / bg HEX | only if dark-mode or inverted scheme mentioned |
| title / body font | when the asset gave no font reference |
| logo usage | when a logo file was provided |
| voice & tone | when audience or formality was mentioned |
| icon style preference | when icon consistency was mentioned |

---

## Step 4: Materialize the brand package

Create the package directory:

```bash
mkdir -p "skills/ppt-master/templates/brands/<brand_id>"
```

### Mandatory: `design_spec.md`

```markdown
---
brand_id: <slug>
kind: brand
summary: <one-line use case, e.g. "ACME Corp marketing decks">
keywords: [<3-5 short tags>]
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

## II. Color Scheme
| Role | HEX | Provenance |
|---|---|---|
| primary | #XXXXXX | fact \| approx \| user |
| secondary | #XXXXXX | |
| accent | #XXXXXX | |
| text | #XXXXXX | optional, default `#1A1A1A` |
| bg | #XXXXXX | optional, default `#FFFFFF` |

## III. Typography
| Role | Family | Weight |
|---|---|---|
| title | <family> | <weight> |
| body | <family> | <weight> |
| mono | <family> | optional |

## IV. Logo
- File: `./logo.<ext>` (relative to this design_spec.md)
- Usage: cover-only \| every-page \| never

## V. Voice & Tone
- Formality: formal \| neutral \| casual
- Person: informal-you \| formal-you \| we \| none
- Emoji: allowed \| forbidden
- Abbreviations: spell-out-first \| common-abbrev-allowed

## VI. Icon Style
- Preference: linear \| filled \| duotone   # optional, drives icon library search

## VII. Visual Assets (optional)
- Images: `./images/`               # branded photos, prioritised before AI image generation
- Illustrations: `./illustrations/` # branded illustrations, prioritised before AI generation
- Icons: `./icons/`                 # branded icon overrides; falls back to `templates/icons/`
```

**Section scope rules**:
- Layout / canvas / spacing / radius / shadow / page roster / signature design elements are OUT of brand scope. Those live in layout templates (`templates/layouts/<id>/design_spec.md`) or `shared-standards.md`. Do NOT add those sections here.
- HEX must be `#RRGGBB`
- Font names are free strings; not validated against locally installed fonts
- §VII is fully optional — list only directories that actually exist

### Optional: logo file

If the user provided a logo, copy it to `templates/brands/<brand_id>/logo.<ext>` (preserve source extension).

### Optional: visual asset directories

If the user provided brand photo / illustration / icon folders, copy them as `images/` / `illustrations/` / `icons/` under `templates/brands/<brand_id>/`. Reference each in §VII of `design_spec.md`. Skip the entire section if none exist.

### NOT created here

No SVG page roster. No canvas spec. No signature design elements. If the user later wants brand-anchored page templates, run `create-template.md` with this brand as a style reference.

---

## Step 5: Register and hand off

Update `templates/brands/brands_index.json` with the new entry (create the file if missing):

```json
{
  "<brand_id>": {
    "summary": "<from design_spec.md frontmatter>",
    "keywords": [...],
    "primary_color": "#XXXXXX"
  }
}
```

Emit the confirmation card:

```markdown
## ✅ Brand Saved
- Path: `skills/ppt-master/templates/brands/<brand_id>/`
- Files: design_spec.md{, logo.<ext>}{, images/}{, illustrations/}{, icons/}
- Fields locked: <list>
- Provenance: <fact / approx / user counts>

How to use in a project:
- Include the brand directory path in your initial Step 3 input — e.g. "做一个 Q4 总结 PPT, 用 skills/ppt-master/templates/brands/<brand_id>/ 这个品牌"
- Same explicit-path rule as layout templates: bare brand names never trigger
- May be supplied together with a layout template path; brand identity overrides layout-template defaults
- To list available brands: open `templates/brands/brands_index.json`
- To edit: modify `templates/brands/<brand_id>/design_spec.md` directly, then re-run `python3 skills/ppt-master/scripts/register_template.py --kind brand <brand_id>`
```

---

## Downstream consumption (informational)

Brand application happens in [`SKILL.md` Step 3](../SKILL.md) under the **same explicit-path rule as layout templates**:

| User input at SKILL.md Step 3 | Behavior |
|---|---|
| Explicit brand directory path supplied | Step 3 copies the brand into `<project_path>/brand/`; Strategist locks color / typography / logo / voice as truth at Step 4 |
| Bare brand name, brand mention without path, or silence | Skip — no auto-application based on directory count or any other implicit signal |
| Both a brand path and a layout template path supplied in the same message | Both apply; brand identity overrides layout-template defaults, layout template's page roster and structural design stay intact |

`brands_index.json` is discovery-only (mirrors `layouts_index.json` semantics); listing brands never advances the pipeline.

---

## Notes

1. **Brand is identity, not layout** — colors / typography / logo / voice / icon style only. Page roster, canvas spec, and signature design elements belong to layout templates; do not duplicate them here.
2. **Self-contained package** — all brand assets (logo, images, illustrations, icons) live inside `templates/brands/<brand_id>/`. Nothing leaks to workspace root or `projects/`.
3. **No script dependency** — Step 2A reuses existing converters plus AI inline reading. A dedicated `brand_extract.py` is not introduced unless future user feedback demands batch processing or precise color picking from raster logos.
4. **Multi-brand support** — `templates/brands/` accepts any number of brands; agency / freelancer / multi-client workflows are natural.
5. **Precedence rule** — when a brand and a layout template both apply, brand identity tokens (color / typography / logo / voice) override the layout template's defaults while the layout's page structure is preserved.
