# Deck Templates

**Deck = full-PPT replica.** Each deck reverse-engineers a specific organization's branded presentation and bundles its **identity + structure + middle** segments into one atomic asset. Use a deck when you want the complete look of a particular institution (color, typography, logo, page structure, voice) preserved as a whole.

Single source of truth for what decks exist: [`decks_index.json`](./decks_index.json) (`deck_id → { summary, canvas_format, page_count, primary_color }`). This README explains the kind; it does **not** enumerate decks.

Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

---

## Trigger rule

Deck selection is **opt-in by explicit path**. The main workflow defaults to free design. For a current package, the user supplies the explicit workspace root (for example, `skills/ppt-master/templates/decks/<deck_id>/`), not its inner `templates/` directory. A legacy-flat deck root containing `design_spec.md` remains a compatible input. Bare names do not trigger. See [`SKILL.md`](../../SKILL.md) Step 3.

`decks_index.json` is a **discovery aid**, not a trigger — it lets the AI answer "what decks exist?" by listing ids and paths. Listing alone never advances the pipeline.

---

## design_spec.md schema

Decks carry the full set of segments (identity + structure + middle). Minimum schema:

```markdown
---
deck_id: <slug>
kind: deck
summary: <one-line use cases>
canvas_format: ppt169
page_count: 5
primary_color: "#XXXXXX"
---

# [Brand / Organization Name] - Design Specification

## I. Template Overview          # Middle — Use cases / Design intent
## II. Canvas Specification      # Structure
## III. Color Scheme             # Identity — role / HEX / provenance / notes
## IV. Typography                # Identity — role / family / weight
## V. Logo                       # Identity — file / form / usage rules (if logo bundled)
## VI. Page Structure            # Structure — layout grid / decorative DNA
## VII. Page Types               # Structure — per-page roles
## VIII. SVG Page Roster         # Structure — file list + per-file purpose
```

Decks may include additional supporting sections (Voice & Tone, Icon Style, Layout Modes, Spacing Specification, Placeholder Specification, Asset Specification, Usage Notes). Put a template-specific required / forbidden / conditional boundary inside the personality section it qualifies. General SVG/PPT authoring rules belong only in [`shared-standards.md`](../../references/shared-standards.md); do not add a generic technical-rules section or pointer to a deck spec.

---

## Fusion behavior at Step 3

When the user gives a deck path **alone**, Strategist locks all segments; Strategist confirmation stage narrows to deck-content fields (target audience / page count / outline / tone tweaks).

When the user gives a deck path **with** a brand path or layout path, identity / structure segments are overridden by the higher-priority source (brand wins on identity, layout wins on structure). See [`SKILL.md`](../../SKILL.md) Step 3 fusion table.

---

## Standard workspace contract

New deck creation uses the same complete workspace shape in both output scopes:

```text
<template_workspace>/
├── templates/
│   ├── design_spec.md
│   ├── 01_cover.svg
│   ├── 02_chapter.svg
│   ├── 03_content.svg
│   └── 04_ending.svg
├── images/
├── icons/
└── exports/
    └── <deck_id>_template_preview.pptx
```

| Scope | `<template_workspace>` | Difference |
|---|---|---|
| Library | `skills/ppt-master/templates/decks/<deck_id>/` | Register in `decks_index.json` |
| Project | `projects/<project_name>/` | Do not register globally |

Bitmaps belong in `images/`; extracted runtime icons belong in `icons/`; template sources and any validation icon copy belong in `templates/`. The preview PPTX is a required review artifact, not a template input. Template application consumes `templates/`, `images/`, and `icons/` from the explicit workspace root and does not copy `exports/`.

**Legacy compatibility**: Existing flat packages with `design_spec.md` and SVGs at their root remain readable. Flat placement alone does not trigger [`restore-pptx-structure`](../../workflows/restore-pptx-structure.md); restoration is required only when SVG Master/Layout/slot metadata is absent or legacy. New `create-template` outputs always use the workspace contract above.

---

## Creating a new deck

1. Run [`workflows/create-template.md`](../../workflows/create-template.md) (default kind is `deck`)
2. Choose the workspace root: library `skills/ppt-master/templates/decks/<id>/` or project `projects/<name>/`
3. Validate: `python3 skills/ppt-master/scripts/svg_quality_checker.py "<template_workspace>/templates" --template-mode --format ppt169`
4. Export the review deck: `python3 skills/ppt-master/scripts/template_preview_pptx.py "<template_workspace>"`
5. For library scope only, register: `python3 skills/ppt-master/scripts/register_template.py <id> --kind deck`

The register step updates [`decks_index.json`](./decks_index.json) — the single source of truth for deck discovery.

---

## See also

- [`templates/layouts/`](../layouts/) — structure-only templates without identity
- [`templates/brands/`](../brands/) — identity-only presets without page rosters
- [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md) — three-class data model + fusion rules
