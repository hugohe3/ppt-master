# Deck Templates

**Deck = full-PPT replica.** Each deck reverse-engineers a specific organization's branded presentation and bundles its **identity + structure + middle** segments into one atomic asset. Use a deck when you want the complete look of a particular institution (color, typography, logo, page structure, voice) preserved as a whole.

Single source of truth for what decks exist: [`decks_index.json`](./decks_index.json) (`deck_id → { summary, canvas_format, page_count, primary_color }`). This README explains the kind; it does **not** enumerate decks.

Full data model: [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md).

---

## Trigger rule

Deck selection is **opt-in by explicit path**. The main workflow defaults to free design. A deck is only used when the user gives an explicit directory path in their initial message (e.g. `skills/ppt-master/templates/decks/招商银行/`). Bare names do not trigger. See [`SKILL.md`](../../SKILL.md) Step 3.

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

Decks may include additional supporting sections (Voice & Tone, Icon Style, Layout Modes, Spacing Specification, SVG Technical Constraints, Placeholder Specification, Asset Specification, Usage Notes). Use them when meaningful for the replica.

---

## Fusion behavior at Step 3

When the user gives a deck path **alone**, Strategist locks all segments; Eight Confirmations narrows to deck-content fields (target audience / page count / outline / tone tweaks).

When the user gives a deck path **with** a brand path or layout path, identity / structure segments are overridden by the higher-priority source (brand wins on identity, layout wins on structure). See [`SKILL.md`](../../SKILL.md) Step 3 fusion table.

---

## Creating a new deck

1. Run [`workflows/create-template.md`](../../workflows/create-template.md) (default kind is `deck`)
2. Resulting directory lands under `templates/decks/<id>/`
3. Validate: `python3 skills/ppt-master/scripts/svg_quality_checker.py templates/decks/<id> --template-mode --format ppt169`
4. Register: `python3 skills/ppt-master/scripts/register_template.py <id> --kind deck`

The register step updates [`decks_index.json`](./decks_index.json) — the single source of truth for deck discovery.

---

## See also

- [`templates/layouts/`](../layouts/) — structure-only templates without identity
- [`templates/brands/`](../brands/) — identity-only presets without page rosters
- [`docs/zh/templates-architecture.md`](../../../../docs/zh/templates-architecture.md) — three-class data model + fusion rules
