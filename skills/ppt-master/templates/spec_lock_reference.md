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

## mode
- mode: pyramid

> Strategist: the deck's narrative skeleton, locked at confirmation `d` Layer 1. One of `pyramid` / `narrative` / `instructional` / `showcase` / `briefing` — see [`references/modes/_index.md`](../references/modes/_index.md). Executor reads only the locked mode's file. Deck-wide. Or the literal `custom` for a bespoke direction no preset captures (a special cadence, a multi-mode fusion, a particular posture) — user-requested or Strategist-recommended (user confirms, like every lock). Then add a sibling `- mode_behavior:` paragraph (how the argument advances, title voice, page rhythm, register) that the Executor follows in place of a preset file. One deck locks one value; don't default to `custom` when a preset fits.

## visual_style
- visual_style: swiss-minimal

> Strategist: the deck's visual aesthetic, locked at confirmation `d` Layer 2. A preset name from [`references/visual-styles/_index.md`](../references/visual-styles/_index.md), **or** the literal `custom`. Reference intent (shape / decoration / whitespace / texture) — **not a whitelist**, and **carries no HEX** (color truth stays in `colors`). Executor reads only the locked style's file.
>
> **`custom`** — add a sibling `- visual_style_behavior:` row with a one-paragraph aesthetic description (shape language, decoration density, whitespace, typographic character, texture); no HEX, no color names. Tail-case, not a default.

## colors
- bg: #FFFFFF
- primary: #......
- accent: #......
- secondary_accent: #......
- text: #......
- text_secondary: #......
- border: #......
- image_rendering: vector-illustration
- image_palette: cool-corporate

> Strategist: fill only colors actually used. Add extra rows as needed; delete unused rows rather than leave as `#......`.
>
> **`image_rendering` and `image_palette`** — required only when `images` section below contains `ai`-sourced files. Values MUST be valid names from `references/image-renderings/_index.md` and `references/image-palettes/_index.md`, **or** the literal string `custom`. Image_Generator reads these and applies them deck-wide. Omit both rows when the deck has no AI-generated images.
>
> **`custom` escape hatch.** When set to `custom`, add a sibling `*_behavior` row carrying a one-paragraph prose description. Image_Generator splices the prose into the prompt in place of the preset file's fewshot snippet. Tail-case only — see [`image-renderings/_index.md`](../references/image-renderings/_index.md) §1.5 / [`image-palettes/_index.md`](../references/image-palettes/_index.md) §2 for invocation rules.
>
> ```
> - image_rendering: custom
> - image_rendering_behavior: "Hand-screened poster aesthetic — slightly misregistered halftone overlays, 3 flat ink colors with visible dot pattern at 12% opacity, no gradients, no anti-aliased edges; reads as silkscreen print."
> - image_palette: custom
> - image_palette_behavior: "Primary deep aubergine `#4C1D95` anchors ~35% of canvas; secondary warm cream `#FEF3C7` carries ~55% as breathing field; accent burnished gold `#D4AF37` in 5-10% as ceremonial accents. No fourth color."
> ```

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- title_family: Georgia, SimSun, serif
- body_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- emphasis_family: Georgia, SimSun, serif
- code_family: Consolas, "Courier New", monospace
- body: 24
- title: 42
- subtitle: 32
- annotation: 18
- footnote: 16

> **All five family lines are listed explicitly** so Strategist considers every role — `code_family` and `emphasis_family` are easily forgotten. In a real `spec_lock.md`:
> - Keep any `*_family` whose role genuinely differs from `font_family`.
> - **Omit** any `*_family` equal to `font_family` — Executor falls back to `font_family` for missing roles, so writing it twice is noise. (Exception: keep `code_family` even when equal — monospace is conceptually distinct.)
> - `code_family` applies to code snippets only. LaTeX formulas rendered by `latex_render.py` are PNG image assets and must be listed under `images`.
>
> `font_family` is the default fallback. Every declared family is a CSS font-stack string.
>
> **Source**: copy verbatim from the *Per-role font stacks* list in `design_spec.md §IV Font Plan`. Stack **order** encodes browser-rendering intent (Latin-led vs. CJK-led) that the breakdown table cannot — strings here must match character-for-character. See `design_spec.md §IV` for the explainer.
>
> Sizes (`body` / `title` / etc.) are **unitless px numbers** — the execution unit and the same values recorded in `design_spec.md §IV`. The system is px-only on every canvas: there is no pt layer and no conversion — the confirmed value is already px (e.g. `balanced` body `24`, title `42`, subtitle `32`, annotation `18`, footnote `16` — clean even px). Do not write `pt` / `px` / `em` or any unit. `body` is the **required baseline anchor** — all other sizes derive as clean-even ratios of it (ramp table: `design_spec_reference.md §IV`).
>
> **Size slots are anchors, not a closed menu.** Common slots (`title` / `subtitle` / `annotation`) cover frequent cases. Add role-specific slots (e.g. `cover_title: 88`, `hero_number: 56`, `subheading: 32`, `lead: 30`, `footnote: 16`, `chart_annotation: 16`) for the roles the deck actually uses — common for cover-heavy decks, consulting-style hero numbers, dense pages. **Mandatory — scan `§IX` and declare a slot for every role that recurs across pages, not just the four defaults.** A report / `text`-mode deck almost always recurs a per-page **core-message / lead line** and **page numbers / source credits / footnotes** → declare `lead` and `footnote` for them. `subheading` and `lead` sit between `subtitle` and `body` (their bands overlap `subtitle`) — pick by role, not size — and the core-message `lead` is a **primary** line, **always ≥ `body`**, never smaller. Leaving a recurring lead / footnote undeclared forces the Executor to improvise an unlocked size (and a core line improvised below `body` inverts the hierarchy). **Structural roles (title / body / subtitle / annotation / footnote) render at their locked size on every page — one role, one size, deck-wide.** Intermediate in-band sizes are for special / feature elements only (hero number, display title, one-off emphasis); declare a recurring one as its own slot so it stays consistent too.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** PPTX stores concrete exported Latin / EA typefaces per run with no runtime fallback. Every stack's exported Latin / EA typefaces MUST resolve to cross-platform pre-installed fonts: `"Microsoft YaHei"` / `SimSun` / `Arial` / `"Times New Roman"` / `Consolas`. Stacks that export non-preinstalled typefaces (Inter / Google Fonts / brand typefaces) may be used only when the Design Spec notes the font-install or embedding requirement.
>
> **Stack length discipline.** 3-4 fonts per stack is the sweet spot. Converter only writes the **first** Latin and **first** CJK font into PPTX — everything after is silently dropped. macOS-only families (`Songti SC`, `Menlo`, `Monaco`, `Helvetica`) are auto-mapped to Windows equivalents via `FONT_FALLBACK_WIN` (see `scripts/svg_to_pptx/drawingml/utils.py`); stacking both is redundant. Lead with Windows-preinstalled fonts (`Microsoft YaHei` / `SimSun` / `Arial` / `Georgia` / `Consolas`); keep at most **one** macOS-exclusive family (typically `"PingFang SC"`) as a browser-preview nicety.

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
- q3_revenue_chart: images/q3_revenue.png | no-crop
- formula_001: images/formula_001.png | no-crop

> One entry per image file used. Append ` | no-crop` only for images that must not lose pixels (data screenshots, charts, certificates, rendered LaTeX formulas) — Executor will size the container to native ratio and use `preserveAspectRatio="xMidYMid meet"`. Untagged entries default to croppable (`slice`). Remove the section entirely if no images.

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

## pptx_structure
- mode: baseline

> One deck-wide native PowerPoint structure policy. New projects always include this section.
>
> When Step 3 loaded a deck/layout template, add exactly one of:
> ```
> - template_adherence: adaptive
> - template_adherence: strict
> ```
> Omit the row for free design and brand-only templates. `adaptive` treats template SVGs as optional page references and always exports through `baseline`; `strict` requires one `page_layouts` row per page and may use `preserve` when the template carries a compatible native pair.
>
> - `baseline` — default. Preserve the conservative shared Master/background/chrome behavior; no explicit reusable placeholder layouts are authored.
> - `template` — use only when the user explicitly requests a reusable PowerPoint template/master/layout deliverable. Requires a complete `pptx_layouts` section and explicit SVG structure metadata on every generated page.
> - `preserve` — use only with `template_adherence: strict` when the selected reusable template ships `native_structure.json` + `source_template.pptx`. Add both project-relative rows below and map every page under `pptx_layouts`. `adaptive + preserve` is invalid.
> - `flat` — diagnostic escape hatch. Do not lock this in a normal project; pass it on the CLI when comparing slide-local output.
>
> Preserve example:
> ```
> - mode: preserve
> - template_adherence: strict
> - source_template: templates/source_template.pptx
> - native_structure: templates/native_structure.json
> ```

## pptx_layouts

> Emit this section only when `pptx_structure.mode` is `template` or `preserve`. Include exactly one row per generated page. Value format: `<layout_key> | <PowerPoint layout name>`. Preserve mode uses exact keys/names from `native_structure.json` and the selected template SVG root.
>
> Example:
> ```
> - P01: cover | Cover
> - P02: title-content | Title and Content
> - P03: title-content | Title and Content
> - P04: section | Section Header
> ```
>
> Reuse one key only when pages share the same static layout layer and placeholder contract. Do not generate one unique key per slide merely because every page has different content. A one-off cover/section layout is valid; content differences stay slide-local.

## page_layouts
- P01: 01_cover
- P03: 02a_chapter
- P04: 03a_content_abstract

> One entry per page **that uses a template SVG**. Key: `P<NN>` matching §IX. Value: the template's SVG basename without extension (e.g., `01_cover`, `03a_content_image_text`) — Executor resolves it to `templates/<value>.svg`. Modern templates ship many content-page variants (`03a_content_abstract`, `03b_content_image_text`, `03c_content_three_items` …); the page-type → single-file mapping in `executor-base.md §1` no longer covers them, so this section is the per-page truth.
>
> **No entry for a page** → that page is free design (no template inheritance). Mixed decks are supported: e.g., cover/chapter pages inherit a template while content pages are free.
>
> **Hard rule**: Use both `page_layouts` and `page_charts` for the same page only when the layout template is a compatible shell for the chart. Do not assign a conflicting layout just to fill every page: a waterfall chart should not inherit a timeline layout, and KPI cards should not inherit a circle-diagram layout unless that is the intended visual structure. When no compatible layout exists, omit the page from `page_layouts`.
>
> **Whole section omitted** → entire deck is free design. Equivalent to no rows but cleaner; do this when zero pages reference a template.
>
> **Strategist source**: copy the per-page SVG choices from `design_spec.md §VI Page Roster` (or §IX outline if Roster is absent). Names must match files in `templates/` exactly — typos cause silent fallback to free design.

## page_charts
- P05: column_chart
- P09: timeline_horizontal
- P12: quadrant_bubble_scatter

> One entry per page **that adapts a `templates/charts/` chart template**. Key: `P<NN>` matching §IX. Value: chart template basename without `.svg` (must match a key in `templates/charts/charts_index.json`).
>
> **No entry for a page** → no chart on that page (or a chart that did not match any catalog template — Strategist's `no-template-match` fallback). Both cases mean Executor designs the visualization from scratch per `design_spec.md §VII`.
>
> **Whole section omitted** → no data-visualization pages in this deck.
>
> **Strategist source**: copy from `design_spec.md §VII Visualization Reference List` — only the rows whose `reference template path` points to a `templates/charts/` file. Pages marked `no-template-match` in §VII MUST NOT appear here.

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- HTML named entities in text (`&nbsp;`, `&mdash;`, `&copy;`, `&ndash;`, `&reg;`, `&hellip;`, `&bull;` …) — write as raw Unicode (`—`, `©`, `→`, NBSP, etc.); XML reserved chars `& < > " '` must be escaped as `&amp; &lt; &gt; &quot; &apos;`. See shared-standards.md §1.0
