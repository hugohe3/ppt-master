---
brand_id: nvidia
kind: brand
summary: NVIDIA-style accelerated-computing identity — signature green on near-black for AI, GPU, and data-center technical decks
primary_color: "#76B900"
---

# NVIDIA Brand Specification

> Identity-only preset. No SVG page roster — pages are composed freely under these constraints.

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | NVIDIA |
| Use Cases | AI and accelerated-computing talks, GPU and data-center architecture decks, developer sessions, and technical partner enablement |
| Tone | Technical, precise, performance-focused, evidence-led |
| Sources | NVIDIA's published trademark and logo usage guidelines, reviewed 2026-08-07, which state the green as RGB 118/185/0 and Pantone 376 C. Neutral and surface rows are presentation conventions, not published tokens |

## II. Color Scheme

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#76B900` | fact | Signature green; the published guidelines specify RGB 118/185/0, which is this hex, referenced to Pantone 376 C |
| accent | `#1A1A1A` | approx | Near-black field the green is normally presented against |
| bg | `#FFFFFF` | approx | Default light presentation background |
| surface | `#F4F6F1` | approx | Off-white with a green cast — card and module surfaces |
| border | `#DCE0D6` | approx | Hairline rules, dividers, and table borders |
| muted-text | `#5A5F55` | approx | Secondary text, annotations, and chart labels |

The primary is `fact` — it is the value published in the company's own usage guidelines. Every other row is `approx` and represents presentation convention, not an official token. This green is bright and fails contrast against white at text sizes: never set body text in it, and prefer it on the near-black field or as a mark, rule, and single decisive accent. It also collides directly with conventional "pass" and "success" semantics — where a page needs status meaning, declare that mapping explicitly and keep it distinguishable from identity use. Do not lock an invented success/warning/error trio as identity.

## III. Typography

| Role | Family | Weight |
|---|---|---|
| title | `Arial, "Microsoft YaHei", sans-serif` | 600–700 |
| body | `Arial, "Microsoft YaHei", sans-serif` | 400 |

> The company uses a proprietary licensed typeface that this preset neither bundles nor names as a claim. PPT Master does not auto-embed fonts or follow CSS tails in PowerPoint. The rows above are the default Windows/Office export; replace them only with a user-confirmed target-installed face.

## IV. Logo

- File: `none`
- Usage: never

No logo asset is bundled. The published guidelines require written approval before any use of the logo or branded elements, set a minimum size of 60 pixels on screen, mandate clear space, and prohibit unapproved color modification — conditions this preset cannot grant. Where a presenting entity must appear, set it as editable text in the deck's own typography, or install an officially approved asset into this workspace's `images/` directory and record the approval and its usage rules here. The bundled icon library contains a single-color `simple-icons/nvidia` symbol for genuine brand-recognition contexts such as a partner or ecosystem listing; it is a symbol only, not the official lockup. Never imply affiliation, sponsorship, endorsement, or certification.

## V. Voice & Tone

- Formality: neutral
- Person: we / you (English), 我们 / 你 (Chinese)
- Emoji: forbidden
- Abbreviations: spell-out-first-use

> Presentation convention derived from the register these decks are normally written in, not an official brand token. Give benchmark numbers their workload, configuration, and software version; name architectures and products exactly.

## VI. Icon Style

- Preference: stroke

> Presentation convention, not an official brand token. Prefer a consistent stroke family such as `tabler-outline`, keep one family across the deck, and use an icon only where it clarifies a role, state, or relationship.
