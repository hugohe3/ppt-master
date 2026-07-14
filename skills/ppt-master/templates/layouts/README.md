# Layout Templates

**Layout = structure-only template.** Captures canvas, page structure, page types, and SVG roster — but **no identity segment** (color / typography / logo / voice / icon style). Layered identity comes from `templates/brands/` or is decided per-deck in Strategist's confirmation stage. For full-identity replicas of specific PPTs, see [`templates/decks/`](../decks/) instead.

Single source of truth for what layouts exist: [`layouts_index.json`](./layouts_index.json) (`layout_id → { summary, canvas_format, page_count, page_types }`). This README explains the kind; it does **not** enumerate layouts.

Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

---

## Trigger rule

Layout selection is **opt-in by explicit path**. The main workflow defaults to free design. For a current package, the user supplies the explicit workspace root (for example, `skills/ppt-master/templates/layouts/<layout_id>/`), not its inner `templates/` directory. A legacy-flat layout root containing `design_spec.md` remains a compatible input. Bare names do not trigger. See [`SKILL.md`](../../SKILL.md) Step 3.

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

Layouts may include additional supporting sections (Layout Patterns, Spacing Guidelines, Placeholder Specification, Usage Notes). Put a layout-specific required / forbidden / conditional boundary inside the personality section it qualifies. Do **not** include Color Scheme or Typography sections — those are identity-segment fields owned by `templates/brands/` and `templates/decks/`. General SVG/PPT authoring rules belong only in [`shared-standards.md`](../../references/shared-standards.md); do not add a generic technical-rules section or pointer to a layout spec.

---

## Standard workspace contract

New layout creation uses the same portable workspace routing in both output scopes:

```text
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_chapter.svg
│   ├── 03_content.svg
│   └── 04_ending.svg
├── images/                         # Optional; omit when unused
├── icons/                          # Optional; omit when unused
└── exports/                        # Optional, on-demand review output; Git-ignored
    └── <layout_id>_template_preview.pptx
```

| Scope | `<template_workspace>` | Difference |
|---|---|---|
| Library | `skills/ppt-master/templates/layouts/<layout_id>/` | Register in `layouts_index.json` |
| Project | `projects/<project_name>/` | Do not register globally |

`02_toc.svg` and other roster variants remain optional; including the TOC shifts the later types to `03_chapter.svg` / `04_content.svg` / `05_ending.svg`, keeping numbering equal to the template's own presentation order. All SVGs use `viewBox="0 0 1280 720"` for ppt169. Bitmaps belong in `images/`; extracted runtime icons belong in `icons/`; template sources and any validation icon copy belong in `templates/`.

Omit empty optional directories instead of adding placeholder files. Generate a preview PPTX only when local PowerPoint review is requested; it is derived output, library `exports/` is Git-ignored, and template application never copies it.

`standard` and `fidelity` author new SVG documents and a new Master/Layout/slot contract. `mirror` restores the source roster, Master/Layout identities and parentage, placeholder facts, and supported visuals without semantic synthesis. Fixed Master/Layout group wrappers are mechanically expanded into direct atoms because structural layers cannot be `<g>`; this normalization must preserve ownership, paint order, and appearance.

**Legacy compatibility**: Existing flat packages with `design_spec.md` and SVGs at their root remain readable. Flat placement alone does not trigger [`restore-pptx-structure`](../../workflows/restore-pptx-structure.md); restoration is required only when SVG Master/Layout/slot metadata is absent or legacy. New `create-template` outputs always use the workspace contract above.

---

## Placeholder convention

Templates use `{{PLACEHOLDER}}` to mark replaceable content. New layouts should use the canonical placeholder set documented in [`references/template-designer.md`](../../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). Templates with intentionally different vocabulary declare a `placeholders:` block in `design_spec.md` frontmatter to silence advisory warnings.

---

## Creating a new layout

1. Run [`workflows/create-template.md`](../../workflows/create-template.md) (default produces a deck; explicit "structure only / no identity" option produces a layout)
2. Choose the workspace root: library `skills/ppt-master/templates/layouts/<id>/` or project `projects/<name>/`
3. Validate: `python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_workspace>/templates" --template-mode --format ppt169`
4. Optional — when PowerPoint review is requested, export the review deck: `python3 skills/ppt-master/scripts/template_preview_pptx.py "<template_workspace>"`
5. For library scope only, register: `python3 skills/ppt-master/scripts/register_template.py <id> --kind layout`

The register step updates [`layouts_index.json`](./layouts_index.json) — the single source of truth for layout discovery.

---

## SVG technical authority

[`shared-standards.md`](../../references/shared-standards.md) is authoritative for general SVG/PPT required, forbidden, and conditional rules. Layout specs add only constraints unique to that layout.
