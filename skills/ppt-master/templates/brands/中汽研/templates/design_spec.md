---
brand_id: 中汽研
kind: brand
summary: CATARC brand identity for product certification, evaluation reports, automotive technology promotion, and business visits
primary_color: "#004098"
---

# CATARC (中汽研) Brand Specification

> Identity-only preset. No SVG page roster; pages are composed freely under these brand constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | CATARC / 中汽研 |
| Use Cases | Product certification display, evaluation presentations, automotive technology promotion, business visits, high-end technical reporting |
| Tone | Professional, authoritative, trustworthy, technical-consulting style |
| Sources | Bundled CATARC logo assets and the validated CATARC deck identity, reviewed 2026-07-13 |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#004098` | approx | Working primary blue aligned with the validated CATARC deck template |
| secondary | `#003B82` | approx | Dark blue for chapter pages, headers, and restrained depth |
| text | `#333333` | approx | Primary body text on light backgrounds |
| muted-text | `#666666` | approx | Secondary descriptions and notes |
| bg | `#FFFFFF` | approx | Standard light presentation background |
| surface | `#F8FAFC` | approx | Secondary content blocks and cards |
| border | `#E0E0E0` | approx | Dividers, table borders, and technical grids |

This compact palette intentionally matches the retained CATARC deck identity. It is an internal presentation approximation, not a claim about official CATARC design tokens. Derive success, warning, and error colors from the content context rather than treating them as brand colors.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"Microsoft YaHei", "微软雅黑", "SimHei", Arial, Calibri, sans-serif` | 700 |
| body | `"Microsoft YaHei", "微软雅黑", Arial, Calibri, sans-serif` | 400 |
| data | `Arial, "Microsoft YaHei", sans-serif` | 600-700 |

Use clear PowerPoint-safe CJK fonts. Keep numbers, certification codes, and technical abbreviations in Arial for legibility.

## IV. Logo

CATARC uses separate large and header lockups. Choose the large logo for brand moments and the compact logo for page chrome.

| File | Form | Usage |
|---|---|---|
| `../images/大型 logo.png` | Large CATARC lockup (592x238) | Cover hero, chapter/ending brand moments, and dark page lockups |
| `../images/右上角 logo.png` | Compact header logo (113x50) | Upper-right page header, title bar, and navigation areas |

- Cover / ending: use `大型 logo.png` where the brand must read strongly.
- Content pages: use `右上角 logo.png` only when the layout has enough title-bar space.
- Watermarks: large logo may be used as a very faint watermark on content pages.
- Clearspace: leave at least 0.5x logo height around the mark or lockup.

## V. Voice & Tone

- Formality: formal-neutral
- Person: organization-first, "we / 我们" only when speaking as CATARC
- Emoji: avoid
- Abbreviations: CATARC is acceptable; spell out Chinese entity names on first use
- Style: emphasize certification credibility, testing rigor, technical evidence, automotive industry insight, and trusted advisory authority

## VI. Icon Style

- Preference: filled or clean stroke icons
- Recommended libraries: `tabler-filled`, `chunk-filled`, or `tabler-outline`
- Prefer automotive, certification, testing, dashboard, data, process, and compliance metaphors. Avoid playful or consumer-app icon styling.
- This icon guidance is a presentation convention, not an official CATARC icon token set.
