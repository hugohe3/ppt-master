---
brand_id: anthropic
kind: brand
summary: Anthropic / Claude brand family — AI research, product talks, developer conferences, technical training, and launches
primary_color: "#D97757"
---

# Anthropic / Claude Brand Family Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Anthropic / Claude |
| Use Cases | AI / LLM research updates, Claude product talks, developer conferences, technical training, product launches |
| Tone | Tech-forward, professional, modern, conclusion-first, restrained |
| Sources | Bundled Claude SVG assets for literal logo colors; Anthropic public materials reviewed 2026-07-13 |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#D97757` | fact | Claude coral — literal fill in the bundled Claude star mark |
| neutral-dark | `#191919` | fact | Literal fill in the bundled Claude wordmark |
| bg | `#FFFFFF` | approx | Default light presentation background |
| surface | `#F8FAFC` | approx | Off-white — card background |
| border | `#E2E8F0` | approx | Light gray — card borders, dividers |
| muted-text | `#64748B` | approx | Slate gray — secondary text, chart labels |

The first two rows are literal Claude asset facts. Background and neutral rows are presentation conventions, not official company tokens. Choose semantic chart/status colors per deck; do not lock an invented info/success/alert trio as Anthropic identity.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `"Styrene A", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 600–700 |
| body | `"Anthropic Sans", "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif` | 400 |

> `Styrene A` and `Anthropic Sans` are proprietary and unlikely to be installed on viewer machines. PPT Master does not bundle or automatically embed them; use the declared fallback chain unless the user supplies an installed/approved font workflow.

## IV. Logo

This preset intentionally combines Anthropic company voice with Claude product visuals. The bundled star and wordmark belong to Claude; they are not relabeled as an Anthropic corporate mark. Pick one Claude asset by context and never combine several lockups on the same page.

| File | Form | Usage |
|---|---|---|
| `../images/anthropic_claude_lockup.svg` | Claude star + "Claude" wordmark (112×24) | Cover hero, ending sign-off, and Claude product moments |
| `../images/anthropic_mark.svg` | Claude square star mark (24×24; historical filename retained) | Header/footer corners, page-number neighbors, and compact Claude product badges |
| `../images/claude_wordmark.svg` | "Claude" wordmark alone (82×24) | When the visual context already establishes the brand and only the product name needs to be reinforced |

- Claude-facing cover: prefer the complete Claude lockup
- Anthropic-company-facing cover: use editable `Anthropic` text unless an approved corporate lockup is supplied; do not substitute the Claude wordmark
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

> This is a presentation convention, not an official brand token. Prefer `tabler` or `lucide` stroke families when they fit the deck; keep one icon family consistent.
