---
brand_id: 中国电建
kind: brand
summary: POWERCHINA brand identity for engineering project reports, technical proposals, business negotiations, and corporate promotion
primary_color: "#004EA1"
---

# POWERCHINA (中国电建) Brand Specification

> Identity-only preset. No SVG page roster; pages are composed freely under these brand constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | POWERCHINA / 中国电建 |
| Use Cases | Engineering project reports, technical proposal presentations, business negotiations, corporate promotion, annual summaries |
| Tone | Professional, composed, international, state-owned enterprise style |
| Sources | Bundled logo assets for literal colors; [POWERCHINA Brand and Visual Identity Manual (2025) release page](https://11j.powerchina.cn/col/col16780/art/2025/art_daed13ac0e294a56a31033ced7689708.html), reviewed 2026-07-13 |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#004EA1` | approx | Dominant blue sampled from the bundled raster POWERCHINA group symbol |
| secondary | `#C90A4F` | approx | Dominant magenta-red sampled from the bundled raster POWERCHINA group symbol |
| text | `#1A1A1A` | approx | Primary body text on light backgrounds |
| muted-text | `#4A5568` | approx | Secondary descriptions and annotations |
| bg | `#FFFFFF` | approx | Standard light presentation background |
| surface | `#F4F6F8` | approx | Light gray card and module surfaces |

The two symbol colors are exact pixel samples from the bundled raster asset, but remain `approx` because no authoritative token values are bundled. The neutral presentation colors are also practical approximations, not claims about official POWERCHINA design tokens.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"Microsoft YaHei", "微软雅黑", "SimHei", Arial, sans-serif` | 700 |
| body | `"Microsoft YaHei", "微软雅黑", Arial, sans-serif` | 400 |
| data | `Arial, "Microsoft YaHei", sans-serif` | 600-700 |

Use PowerPoint-safe CJK fonts by default. Keep English technical labels in Arial when they function as engineering annotations or dashboard labels.

## IV. Logo

This preset defaults to the POWERCHINA group as the presenting entity. Subsidiary marks are explicit alternates only when that subsidiary owns the presentation; pick one presenting entity per deck.

| File | Form | Usage |
|---|---|---|
| `../images/电建logo.png` | POWERCHINA group symbol / primary mark (234x236) | Cover, ending, and compact brand moments where the group identity is required |
| `../images/中国水务logo.png` | China Water logo lockup (1108x190) | Subsidiary-led water-business reports; cover or ending lockup |
| `../images/华东院logo.png` | East China Institute logo lockup (1438x300) | Institute-led technical reports and engineering proposals |
| `../images/水电三局logo.png` | Sinohydro Bureau 3 logo lockup (629x75) | Bureau-led project reports and construction updates |

- Cover / ending: use the selected primary logo at readable size.
- Per-page header: optional; use a compact logo only when it does not crowd the title bar.
- Do not mix the group mark and several subsidiary marks as routine page chrome. Use co-branding only when the presentation brief explicitly requires it.
- If a subsidiary needs materially different colors, typography, or recurring identity rules, create a separate brand workspace for that entity.
- Dark backgrounds: prefer white/inverted treatment when available; otherwise place the logo on a white backing plate.
- Clearspace: leave at least 0.5x logo height around the mark or lockup.
- External publication must follow the owner-provided trademark and visual-identity permissions; packaging these assets does not grant usage rights.

## V. Voice & Tone

- Formality: formal
- Person: organization-first, "we / 我们" when speaking as the company
- Emoji: avoid
- Abbreviations: spell out Chinese organization names on first use; POWERCHINA is acceptable after first mention
- Style: emphasize engineering reliability, delivery capability, safety, scale, and public-sector credibility

## VI. Icon Style

- Preference: filled or sturdy stroke icons
- Recommended libraries: `tabler-filled`, `chunk-filled`, or `tabler-outline` with heavier stroke
- Avoid thin decorative icons for engineering / construction content; prefer solid symbols, process arrows, infrastructure metaphors, and chart-friendly pictograms.
- This icon guidance is a presentation convention, not an official POWERCHINA icon token set.
