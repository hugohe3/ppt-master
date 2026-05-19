---
brand_id: anthropic
kind: brand
summary: Anthropic brand identity — AI/LLM tech talks, developer conferences, technical training, product launches
keywords: [tech, modern, dark, conclusion-first, ai]
primary_color: "#D97757"
---

# Anthropic Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Anthropic |
| Use Cases | AI / LLM tech talks, developer conferences, technical training, product launches, research updates |
| Tone | Tech-forward, professional, modern, conclusion-first, restrained |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#D97757` | fact | Anthropic Orange — extracted from `anthropic_mark.svg` (matches the mark fill on claude.com header) |
| neutral-dark | `#191919` | fact | Anthropic near-black — body text, dark surfaces, chart base |
| bg | `#FFFFFF` | fact | Pure white page background |
| accent (info) | `#4A90D9` | approx | Tech blue — flow / process, links, interactive elements |
| accent (positive) | `#10B981` | approx | Mint green — recommended options, success states |
| accent (alert) | `#EF4444` | approx | Coral red — risks, cautions, warnings |
| surface | `#F8FAFC` | approx | Off-white — card background |
| border | `#E2E8F0` | approx | Light gray — card borders, dividers |
| muted-text | `#64748B` | approx | Slate gray — secondary text, chart labels |

The first three rows are the official triad; the accent / surface / border / muted rows are presentation conventions on top of the official identity, derived to match Anthropic's restrained product UI tone. The accent triple (info / positive / alert) differentiates content types (blue = process, green = recommended, red = risk). Strategist may rotate dominance per page.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"Styrene A", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 600–700 |
| body | `"Anthropic Sans", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 400 |

> Anthropic's official typefaces are `Styrene A` (titles) and `Anthropic Sans` (body) — both proprietary and unlikely to be installed on viewer machines. Decks should either embed the fonts into the PPTX or accept the `Helvetica Neue` → `Arial` / `Microsoft YaHei` fallback chain. When locking, Strategist notes "official Anthropic typefaces require install or PPTX embed".

## IV. Logo

Anthropic uses a six-petal star **mark** that is most commonly seen locked up with a product wordmark. The bundled lockup pairs the mark with the **Claude** wordmark, since that is the live lockup on claude.com. Pick by context, never combine on the same page.

| File | Form | Usage |
|---|---|---|
| `./anthropic_claude_lockup.svg` | Mark + "Claude" wordmark (112×24) | Cover hero, ending sign-off, any moment when the brand needs to read as Claude-the-product at a glance |
| `./anthropic_mark.svg` | Square orange six-petal mark (24×24) | Header / footer corners, page-number neighbors, tight badges, any small-size moment where the lockup would become illegible — also the recommended choice when the deck is about Anthropic the company rather than Claude the product |
| `./claude_wordmark.svg` | "Claude" wordmark alone (82×24) | When the visual context already establishes the brand and only the product name needs to be reinforced |

- Cover: prefer the lockup when the deck is Claude-facing; prefer the mark alone when the deck is Anthropic-company-facing
- Per-page: optional — only when one of these genuinely fits the layout; do not stamp every page
- Clearspace: leave at least 0.5× mark height of empty space on all sides; never overlap text or photographic backgrounds
- Mark color is fixed at `#D97757`; wordmark inherits the page text color (default `#191919` on light bg, `#FFFFFF` on dark)

## V. Voice & Tone

- Formality: professional-neutral
- Person: we / you (English), 我们 / 你 (Chinese)
- Emoji: avoid
- Abbreviations: spell-out-first-use

## VI. Icon Style

- Preference: stroke

> Outline / stroke icons read as "research / engineering" and align with Anthropic's restrained product UI aesthetic. When the deck uses `templates/icons/`, prefer `tabler` or `lucide` stroke families over filled libraries.
