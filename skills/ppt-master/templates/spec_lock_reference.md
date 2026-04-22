# Execution Lock

> **⚠️ This file is a REFERENCE skeleton for Strategist — do NOT copy it verbatim into a project.** When producing `<project_path>/spec_lock.md`, emit only the structural `##` sections with their filled-in `-` data lines. Do NOT carry over any `>` blockquote guidance, callout boxes, HARD-rule notes, or `> ```code fence` override examples from this file — those are author-time guidance for Strategist, not runtime data. The output is a machine-readable contract; every line must be parseable data.
>
> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values NOT listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this file is the canonical source for color / font / icon / image values. Modifications should go through `scripts/update_spec.py` so both this file and the generated SVGs stay in sync.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

> Strategist: fill the viewBox and format for the chosen canvas. Common values: `0 0 1280 720` (PPT 16:9), `0 0 1024 768` (PPT 4:3), `0 0 1242 1660` (Xiaohongshu), `0 0 1080 1080` (WeChat Moments), `0 0 1080 1920` (Story).

## colors
- bg: #FFFFFF
- primary: #......
- accent: #......
- secondary_accent: #......
- text: #......
- text_secondary: #......
- border: #......

> Strategist: fill only the colors actually used in this deck. Extra rows may be added; unused rows should be deleted rather than left as `#......`.

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- body: 22
- title: 32
- subtitle: 24
- annotation: 14

> Sizes are in px, matching SVG native units. `body` is the **required baseline anchor** — every other size in the deck is derived as a ratio of it (see ramp table in `design_spec_reference.md §IV`). `font_family` is a CSS font-stack string — used as the default family for every text role unless overridden below.
>
> **Size slots are anchors, not a closed menu.** The common slots (`title` / `subtitle` / `annotation`) cover frequent cases. Add role-specific slots (e.g. `cover_title: 72`, `hero_number: 48`, `chart_annotation: 13`) when a deck genuinely needs them — this is expected for cover-heavy decks, consulting-style hero numbers, and information-dense pages. Executor may use intermediate sizes as long as the size's ratio to `body` sits within the corresponding role's band in the ramp table.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** PPTX stores one `typeface` per text run; there is no runtime fallback. Every stack here MUST end with a cross-platform pre-installed font: `"Microsoft YaHei", sans-serif` / `SimSun, serif` / `Arial, sans-serif` / `"Times New Roman", serif` / `Consolas, "Courier New", monospace`. Non-pre-installed fonts (Inter / Google Fonts / brand typefaces) may lead the stack only when the Design Spec explicitly notes the font-install or font-embedding requirement.
>
> **Optional per-role family overrides** — add only when a role needs a family different from the default (e.g., a display serif for titles while body stays a geometric sans). Omit any override that is not needed.
>
> ```
> - title_family: Georgia, "Times New Roman", "Songti SC", serif
> - body_family: "PingFang SC", "Microsoft YaHei", sans-serif
> - emphasis_family: same as body (omit if identical)
> - code_family: Consolas, Menlo, Monaco, "Courier New", monospace
> ```
>
> When a `*_family` override is present, Executor MUST use that family for the matching role. When absent, that role falls back to `font_family`.

## icons
- library: chunk
- inventory: target, bolt, shield, users, chart-bar, lightbulb

> `library` MUST be one of `chunk` / `tabler-filled` / `tabler-outline` (exactly one — mixing is forbidden). `inventory` lists the approved icon names (without library prefix); Executor may only use icons from this list.

## images
- cover_bg: images/cover_bg.jpg

> One entry per image file actually used. Remove the section entirely if the deck uses no images.

## page_rhythm
- P01: anchor
- P02: dense
- P03: breathing
- P04: dense
- P05: dense
- P06: breathing
- P07: anchor

> One entry per page. Key format: `P<NN>` (zero-padded two-digit page index matching `§IX Content Outline` in `design_spec.md`). Value is one of the three rhythm tags below. This field exists to break the "every page looks the same" pattern — Executor reads it per page and applies the tag's layout discipline.
>
> **Vocabulary** (exactly these three values):
> - `anchor` — Structural pages (cover / chapter opener / TOC / ending). Follow the corresponding template as-is.
> - `dense` — Information-heavy pages (data, KPIs, comparisons, multi-point lists). Card grids, multi-column layouts, tables, and charts are all permitted.
> - `breathing` — Low-density pages (single concept, hero quote, big image + caption, section transition). Avoid **multi-card grid layouts** (multiple parallel rounded containers as the primary content structure); organize with naked text, dividers, whitespace, or full-bleed imagery instead. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine. Proportions follow information weight — not a preset ratio menu.
>
> **Rhythm follows narrative** (for Strategist when filling this section): `breathing` pages appear where the narrative genuinely pauses — section transitions, a single argument worth standalone emphasis, a deliberate stop after a dense sequence. A high-density data briefing or consulting analysis may legitimately be nearly all `dense` — **do not invent filler pages** to pad the rhythm. Validation: every `breathing` page must answer "what independent thing is this page saying?".
>
> **Missing or empty section** → Executor falls back to `dense` for every page (current pre-rhythm behavior). Remove the whole section only for legacy decks; new decks authored by Strategist MUST fill it.

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
