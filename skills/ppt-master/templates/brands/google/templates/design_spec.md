---
brand_id: google
kind: brand
summary: Google brand identity — multi-product corporate decks, developer events (Google I/O style), education and training in the Google ecosystem
primary_color: "#4285F4"
---

# Google Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Google |
| Use Cases | Product launches, developer events (Google I/O style), corporate updates, multi-product decks, ecosystem education / training |
| Tone | Modern, friendly, optimistic, clear, multi-color expressive |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#4285F4` | fact | Google Blue — extracted from `google_g_logo.svg` |
| secondary | `#34A853` | fact | Google Green |
| accent (warm) | `#FBBC05` | fact | Google Yellow |
| accent (alert) | `#EA4335` | fact | Google Red |
| text | `#202124` | approx | Standard Material / Google product UI text |
| bg | `#FFFFFF` | fact | |

The four primary brand colors (Blue / Green / Yellow / Red) carry equal weight in Google brand usage; the `primary` / `secondary` / `accent` role split above is a slide-layout presentation hierarchy convention, not a brand prominence statement. Strategist may rotate any of the four into the dominant role per page rhythm.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Google Sans, Roboto, "Microsoft YaHei", sans-serif` | 500–700 |
| body | `Roboto, "Microsoft YaHei", sans-serif` | 400 |

> `Google Sans` is a proprietary brand font; decks rendering on machines without it installed should either embed it into the PPTX or accept the `Roboto` / `Microsoft YaHei` fallback. When locking, Strategist notes "requires install or PPTX embed".

## IV. Logo

Google uses a dual-lockup brand system — pick by context, never combine on the same page.

| File | Form | Usage |
|---|---|---|
| `../images/google_wordmark.svg` | Full "Google" wordmark (272×92) | Cover hero, ending sign-off, any moment the full brand reads at a glance |
| `../images/google_g_logo.svg` | Square multi-color "G" mark (24×24) | Header / footer corners, page-number neighbors, tight badges, any small-size moment where the wordmark would become illegible |

- Cover: prefer wordmark
- Per-page: optional — only when wordmark or G mark genuinely fits the layout; do not stamp every page
- Clearspace: leave at least 0.5× logo height of empty space on all sides; never overlap text or photographic backgrounds

## V. Voice & Tone

- Formality: neutral
- Person: we / you (English), 我们 / 你 (Chinese)
- Emoji: allowed
- Abbreviations: common-abbrev-allowed

## VI. Icon Style

- Preference: filled

> Aligns with Material Icons' default filled style. When the deck uses `templates/icons/`, prefer `tabler-filled` or `chunk-filled`; avoid stroke-only libraries to stay consistent with Google's product UI aesthetic.
