---
brand_id: jpmorgan
kind: brand
summary: JPMorgan Chase-style financial-institution identity — corporate blue on navy and neutrals for research, banking, and internal governance decks
primary_color: "#117ACA"
---

# JPMorgan Chase Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | JPMorgan Chase |
| Use Cases | Market and sector research, banking and treasury client materials, investment committee and governance readouts, and internal performance reviews |
| Tone | Formal, conservative, precise, evidence-led |
| Sources | Public third-party brand-color compilations reviewed 2026-08-07, giving the blue as approximately PMS 285 C. No value was read from an official manual, so every value here is an approximation |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#117ACA` | approx | Corporate blue consistently documented across sources; commonly mapped to approximately PMS 285 C |
| accent | `#004B87` | approx | Navy documented alongside the blue for depth and chapter grounds |
| bg | `#FFFFFF` | approx | Default light presentation background |
| surface | `#F4F6F8` | approx | Cool off-white — card and module surfaces |
| border | `#DDE2E7` | approx | Hairline rules, dividers, and table borders |
| muted-text | `#54606C` | approx | Secondary text, annotations, and chart labels |

Every row is `approx`. No value was read from an official asset or manual, so nothing here may be treated as brand truth or represented as the institution's specification. Financial decks carry dense numeric tables, so keep the blue for structure, headers, and the decisive series rather than tinting data regions — a blue-filled table defeats the row scanning it exists for. Chart series in a research deck need their own declared, colorblind-safe scale that does not collide with identity blue. Distinguish the corporate parent from its consumer-facing brand: their identities differ materially and must not be mixed on one page. Do not lock an invented success/warning/error trio as identity.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Arial, "Microsoft YaHei", sans-serif` | 600–700 |
| body | `Arial, "Microsoft YaHei", sans-serif` | 400 |

> The institution uses proprietary licensed typefaces that this preset neither bundles nor names as a claim. PPT Master does not auto-embed fonts or follow CSS tails in PowerPoint. The rows above are the default Windows/Office export; replace them only with a user-confirmed target-installed face. Prefer a face with tabular figures so numeric columns align.

## IV. Logo

- File: `none`
- Usage: never

No logo asset is bundled. The institution's wordmarks and its octagon device are registered trademarks, and financial materials carry regulatory disclosure obligations that a preset cannot satisfy. Where a presenting entity must appear, set it as editable text in the deck's own typography, or install an officially supplied asset into this workspace's `images/` directory and add its usage rules and any required disclosures here. Never imply affiliation, sponsorship, endorsement, or that the material constitutes research or advice from the institution.

## V. Voice & Tone

- Formality: formal
- Person: we / you (English), 我们 / 您 (Chinese)
- Emoji: forbidden
- Abbreviations: spell-out-first-use

> Presentation convention derived from the register these decks are normally written in, not an official brand token. State the basis, period, and currency of every figure, separate historical fact from forecast, and keep any forward-looking statement explicitly labeled.

## VI. Icon Style

- Preference: stroke

> Presentation convention, not an official brand token. Prefer a restrained stroke family such as `tabler-outline`, keep one family across the deck, and use an icon only where it clarifies a role, state, or relationship.
