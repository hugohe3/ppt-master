# Layout Templates

**Layout = structure-only template.** Captures canvas, page structure, page types, and SVG roster — but **no identity segment** (color / typography / logo / voice / icon style). Layered identity comes from `templates/brands/` or is decided per-deck in Strategist's Eight Confirmations. For full-identity replicas of specific PPTs, see [`templates/decks/`](../decks/) instead.

Single source of truth for what layouts exist: [`layouts_index.json`](./layouts_index.json) (`layout_id → { summary, canvas_format, page_count, page_types }`). This README explains the kind; it does **not** enumerate layouts.

Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

---

## Trigger rule

Layout selection is **opt-in by explicit path**. The main workflow defaults to free design. A layout is only used when the user gives an explicit directory path in their initial message (e.g. `skills/ppt-master/templates/layouts/academic_defense/`). Bare names do not trigger. See [`SKILL.md`](../../SKILL.md) Step 3.

`layouts_index.json` is a **discovery aid**, not a trigger — it lets the AI answer "what layouts exist?" by listing ids and paths. Listing alone never advances the pipeline.

---

## design_spec.md schema

Layouts write **structure-only segments**. Identity sections (Color Scheme / Typography / Logo / Voice / Icon Style) are forbidden — those belong to brands and decks. Minimum schema:

```markdown
---
layout_id: <slug>
kind: layout
summary: <one-line use cases>
canvas_format: ppt169
page_count: 5
page_types: [cover, toc, chapter, content, ending]
---

# [Template Name] - Design Specification

## I. Template Overview         # Use cases / Design intent
## II. Canvas Specification     # Format / Dimensions / viewBox / Margins
## III. Page Structure          # Layout grid / Decorative DNA / Navigation
## IV. Page Types               # Per-page role descriptions
## V. SVG Page Roster           # File list + per-file purpose
```

Layouts may include additional supporting sections (Layout Patterns, Spacing Guidelines, SVG Technical Constraints, Placeholder Specification, Usage Notes). Do **not** include Color Scheme or Typography sections — those are identity-segment fields owned by `templates/brands/` and `templates/decks/`.

---

## Standard file set per layout directory

| Filename | Required | Purpose |
|----------|----------|---------|
| `design_spec.md` | Yes | Layout schema spec (frontmatter + structure sections) |
| `01_cover.svg` | Yes | Cover page |
| `02_toc.svg` | Optional | Table of contents |
| `02_chapter.svg` | Yes | Chapter page |
| `03_content.svg` | Yes | Content page |
| `04_ending.svg` | Yes | Ending page |

All SVGs use `viewBox="0 0 1280 720"` for ppt169.

---

## Placeholder convention

Templates use `{{PLACEHOLDER}}` to mark replaceable content. New layouts should use the canonical placeholder set documented in [`references/template-designer.md`](../../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). Templates with intentionally different vocabulary declare a `placeholders:` block in `design_spec.md` frontmatter to silence advisory warnings.

---

## Creating a new layout

1. Run [`workflows/create-template.md`](../../workflows/create-template.md) (default produces a deck; explicit "structure only / no identity" option produces a layout)
2. Resulting directory lands under `templates/layouts/<id>/`
3. Validate: `python3 skills/ppt-master/scripts/svg_quality_checker.py templates/layouts/<id> --template-mode --format ppt169`
4. Register: `python3 skills/ppt-master/scripts/register_template.py <id> --kind layout`

The register step updates [`layouts_index.json`](./layouts_index.json) — the single source of truth for layout discovery.

---

## SVG technical constraints

See [`shared-standards.md`](../../references/shared-standards.md) for the authoritative ban list (PPT incompatibilities, raw-character rules, clipPath conditional allowance, etc.). Layouts must comply.
