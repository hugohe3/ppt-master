---
brand_id: ibm
kind: brand
summary: IBM-style enterprise identity — Carbon blue on a disciplined gray scale for hybrid cloud, AI, and enterprise consulting decks
primary_color: "#0F62FE"
---

# IBM Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | IBM |
| Use Cases | Hybrid cloud and AI solution decks, enterprise consulting deliverables, technical architecture reviews, and industry point-of-view papers |
| Tone | Formal, engineered, systematic, evidence-led |
| Sources | IBM's Carbon Design System — the company's own open design system — reviewed 2026-08-07 for Blue 60. Neutral and surface rows are presentation conventions, not published brand tokens |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#0F62FE` | fact | Blue 60, the primary interactive color published in the company's own Carbon Design System |
| accent | `#002D9C` | approx | Deeper blue from the same family for chapter grounds and depth |
| bg | `#FFFFFF` | approx | Default light presentation background |
| surface | `#F4F4F4` | approx | Neutral gray — card and module surfaces |
| border | `#E0E0E0` | approx | Hairline rules, dividers, and table borders |
| muted-text | `#525252` | approx | Secondary text, annotations, and chart labels |

The primary is `fact` — it is the published token in the company's own open design system. Every other row is `approx` and represents presentation convention, not an official token. Blue 60 is defined there as an *interactive* color for buttons, links, and focus states rather than a decorative brand fill; on a slide, keep that spirit by using it for the decisive mark and structural emphasis instead of tinting large areas. Because it reads as a link color, avoid setting non-interactive body text in it. Choose semantic chart and status colors per deck; do not lock an invented success/warning/error trio as identity.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Arial, "Microsoft YaHei", sans-serif` | 600–700 |
| body | `Arial, "Microsoft YaHei", sans-serif` | 400 |

> The company maintains its own open typeface family, which this preset neither bundles nor assumes is installed. PPT Master does not auto-embed fonts or follow CSS tails in PowerPoint. The rows above are the default Windows/Office export; replace them only with a user-confirmed target-installed face.

## IV. Logo

- File: `none`
- Usage: never

No logo asset is bundled. The company's marks are protected trademarks, and the striped wordmark in particular degrades badly when redrawn or rescaled without official artwork. Where a presenting entity must appear, set it as editable text in the deck's own typography, or install an officially supplied asset into this workspace's `images/` directory and add its usage rules here. The bundled icon library contains a single-color `simple-icons/ibm` symbol for genuine brand-recognition contexts such as a partner or ecosystem listing; it is a symbol only, not the official lockup. Never imply affiliation, sponsorship, endorsement, or certification.

## V. Voice & Tone

- Formality: formal
- Person: we / you (English), 我们 / 您 (Chinese)
- Emoji: forbidden
- Abbreviations: spell-out-first-use

> Presentation convention derived from the register these decks are normally written in, not an official brand token. Keep architecture claims tied to named components and versions, and separate available capability from roadmap.

## VI. Icon Style

- Preference: stroke

> Presentation convention, not an official brand token. Prefer a consistent stroke family such as `tabler-outline`, keep one family across the deck, and use an icon only where it clarifies a role, state, or relationship.
