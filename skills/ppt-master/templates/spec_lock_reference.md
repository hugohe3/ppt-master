# Execution Lock

> **⚠️ Skeleton for Strategist — do NOT copy verbatim into a project.** When producing `<project_path>/spec_lock.md`, emit only `##` sections with filled-in `-` data lines. Do NOT carry over any `>` blockquote guidance, HARD-rule notes, or override examples — those are author-time guidance, not runtime data. Every output line must be parseable data.
>
> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values not listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this is the canonical source for color / font / icon / image values. Modifications should go through `scripts/update_spec.py` to keep this file and generated SVGs in sync.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

> Strategist: fill viewBox and format for the chosen canvas. Common values: `0 0 1280 720` (PPT 16:9), `0 0 1024 768` (PPT 4:3), `0 0 1242 1660` (Xiaohongshu), `0 0 1080 1080` (WeChat Moments), `0 0 1080 1920` (Story).

## colors
- bg: #FFFFFF
- primary: #......
- accent: #......
- secondary_accent: #......
- text: #......
- text_secondary: #......
- border: #......

> Strategist: fill only colors actually used. Add extra rows as needed; delete unused rows rather than leave as `#......`.

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- title_family: Georgia, SimSun, serif
- body_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- emphasis_family: Georgia, SimSun, serif
- code_family: Consolas, "Courier New", monospace
- body: 22
- title: 32
- subtitle: 24
- annotation: 14

> **All five family lines are listed explicitly** so Strategist considers every role — `code_family` and `emphasis_family` are easily forgotten. In a real `spec_lock.md`:
> - Keep any `*_family` whose role genuinely differs from `font_family`.
> - **Omit** any `*_family` equal to `font_family` — Executor falls back to `font_family` for missing roles, so writing it twice is noise. (Exception: keep `code_family` even when equal — monospace is conceptually distinct.)
>
> `font_family` is the default fallback. Every declared family is a CSS font-stack string.
>
> **Source**: copy verbatim from the *Per-role font stacks* list in `design_spec.md §IV Font Plan`. Stack **order** encodes browser-rendering intent (Latin-led vs. CJK-led) that the breakdown table cannot — strings here must match character-for-character. See `design_spec.md §IV` for the explainer.
>
> Sizes (`body` / `title` / etc.) are in px, matching SVG units. `body` is the **required baseline anchor** — all other sizes derive as ratios of it (ramp table: `design_spec_reference.md §IV`).
>
> **Size slots are anchors, not a closed menu.** Common slots (`title` / `subtitle` / `annotation`) cover frequent cases. Add role-specific slots (e.g. `cover_title: 72`, `hero_number: 48`, `chart_annotation: 13`) when needed — common for cover-heavy decks, consulting-style hero numbers, dense pages. Executor may use intermediate sizes as long as the ratio to `body` sits in the role's ramp band.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** PPTX stores one `typeface` per run with no runtime fallback. Every stack MUST end with a cross-platform pre-installed font: `"Microsoft YaHei", sans-serif` / `SimSun, serif` / `Arial, sans-serif` / `"Times New Roman", serif` / `Consolas, "Courier New", monospace`. Non-preinstalled fonts (Inter / Google Fonts / brand typefaces) may lead the stack only when the Design Spec notes the font-install or embedding requirement.
>
> **Stack length discipline.** 3-4 fonts per stack is the sweet spot. Converter only writes the **first** Latin and **first** CJK font into PPTX — everything after is silently dropped. macOS-only families (`Songti SC`, `Menlo`, `Monaco`, `Helvetica`) are auto-mapped to Windows equivalents via `FONT_FALLBACK_WIN` (see `scripts/svg_to_pptx/drawingml_utils.py`); stacking both is redundant. Lead with Windows-preinstalled fonts (`Microsoft YaHei` / `SimSun` / `Arial` / `Georgia` / `Consolas`); keep at most **one** macOS-exclusive family (typically `"PingFang SC"`) as a browser-preview nicety.

## icons
- library: chunk-filled
- brand_library: simple-icons
- inventory: target, bolt, shield, users, chart-bar, lightbulb

> `library` MUST be exactly one of `chunk-filled` / `tabler-filled` / `tabler-outline` / `phosphor-duotone` — mixing is forbidden. `brand_library: simple-icons` is optional; include only when the deck uses real company / product brand marks, otherwise omit. `inventory` lists approved icon names (no library prefix); Executor may only use icons from this list.
>
> **`stroke_width` (stroke-style libraries only)** — required when `library` is stroke-based (currently `tabler-outline`); allowed values `1.5` / `2` / `3`. Executor MUST apply this value to every `<use data-icon="...">` placeholder via `stroke-width`, deck-wide. Omit for non-stroke libraries (`chunk-filled` / `tabler-filled` / `phosphor-duotone`) — ignored there. For heavier weight switch library; do not exceed `3` (at 24×24 strokes merge and the icon stops reading as line art).
>
> Example for stroke-style libraries:
> ```
> - library: tabler-outline
> - stroke_width: 2
> - inventory: home, chart-bar, users, bulb
> ```

## images
- cover_bg: images/cover_bg.jpg

> One entry per image file used. Remove the section entirely if no images.

## page_rhythm
- P01: anchor
- P02: dense
- P03: breathing
- P04: dense
- P05: dense
- P06: breathing
- P07: anchor

> One entry per page. Key: `P<NN>` (zero-padded, matching `§IX Content Outline` in `design_spec.md`). Value: one of the three rhythm tags. Executor reads per page and applies the tag's layout discipline — breaks the "every page looks the same" pattern.
>
> **Vocabulary** (exactly these three values):
> - `anchor` — Structural pages (cover / chapter opener / TOC / ending). Follow the template as-is.
> - `dense` — Information-heavy pages (data, KPIs, comparisons, multi-point lists). Card grids, multi-column layouts, tables, charts all permitted.
> - `breathing` — Low-density pages (single concept, hero quote, big image + caption, section transition). Avoid **multi-card grid layouts** (multiple parallel rounded containers as the primary structure); organize via naked text, dividers, whitespace, or full-bleed imagery. Single rounded elements (hero image corners, callouts, tags, one emphasis block) are fine. Proportions follow information weight — not a preset ratio menu.
>
> **Rhythm follows narrative**: `breathing` pages appear where narrative genuinely pauses — section transitions, a single argument worth standalone emphasis, a deliberate stop after a dense sequence. A data briefing or consulting analysis may legitimately be nearly all `dense` — **do not invent filler pages** to pad rhythm. Validation: every `breathing` page must answer "what independent thing is this page saying?".
>
> **Missing or empty section** → Executor falls back to `dense` for every page (legacy pre-rhythm behavior). Remove the section only for legacy decks; new decks MUST fill it.

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`. See shared-standards.md §1.0
