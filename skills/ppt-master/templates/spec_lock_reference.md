# Execution Lock

> **⚠️ Skeleton for Strategist — do NOT copy verbatim into a project.** When producing `<project_path>/spec_lock.md`, emit only `##` sections with filled-in `-` data lines. Do NOT carry over any `>` blockquote guidance, HARD-rule notes, or override examples — those are author-time guidance, not runtime data. Every output line must be parseable data.
>
> Machine-readable execution contract. Executor MUST `read_file` this before every SVG page. Values not listed here must NOT appear in SVGs. For design narrative (rationale, audience, style), see `design_spec.md`.
>
> After SVG generation begins, this is the canonical source for color / font / icon / image values. Supported color/font modifications should go through `scripts/update_spec.py` to keep this file and generated SVGs in sync. Canvas changes are intentionally not bulk-rewritten by that tool.

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

> Strategist: fill viewBox and format for the chosen canvas. New authoring uses the canonical `0 0 W H` spelling with positive integer pixels. Every generated page and internal Layout prototype must match this numeric canvas. Common values: `0 0 1280 720` (PPT 16:9), `0 0 1024 768` (PPT 4:3), `0 0 1242 1660` (Xiaohongshu), `0 0 1080 1080` (WeChat Moments), `0 0 1080 1920` (Story). Changing the canvas after authoring starts requires re-authoring and re-validating affected SVGs; `update_spec.py` does not propagate canvas changes.

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
> **PowerPoint theme roles.** Flat and structured export map `bg` / `background` / `master_bg` → `lt1`, `secondary_bg` / `bg_secondary` → `lt2`, `text` / `body_text` → `dk1`, `text_secondary` → `dk2`, `primary` → `accent1`, `accent` → `accent2`, `secondary_accent` → `accent3`, and `border` → `accent4`. The first two additional non-black/non-white roles become `accent5` / `accent6`; remaining colors stay fixed. Mapping is usage-aware, so a background HEX is not automatically reused for inverse text.
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
> **Generated Master defaults**: `pptx_structure.mode: flat` and `mode: structured` require unitless `title` and `body`. Native export writes `title` into every generated Master `titleStyle` default and derives a deterministic nine-level, non-increasing size hierarchy from `body` for `bodyStyle` / `otherStyle`. It changes only each level's `a:defRPr@sz`, preserving indentation, bullets, and paragraph settings. Direct page-run sizes and role-specific structured-Layout placeholder prototype sizes remain unchanged.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** Flat and structured export map `title_family` to the PowerPoint theme major font and `body_family` (or `font_family`) to the theme minor font. Runs whose resolved face matches either role use `+mj-*` / `+mn-*` theme tokens; other role families remain concrete per-run typefaces. Every exported Latin / EA face MUST therefore resolve to cross-platform pre-installed fonts: `"Microsoft YaHei"` / `SimSun` / `Arial` / `"Times New Roman"` / `Consolas`. Stacks that resolve to non-preinstalled typefaces (Inter / Google Fonts / brand typefaces) may be used only when the Design Spec notes the font-install or embedding requirement.
>
> **Stack length discipline.** 3-4 fonts per stack is the sweet spot. Converter only writes the **first** Latin and **first** CJK font into PPTX — everything after is silently dropped. macOS-only families (`Songti SC`, `Menlo`, `Monaco`, `Helvetica`) are auto-mapped to Windows equivalents via `FONT_FALLBACK_WIN` (see `scripts/svg_to_pptx/drawingml/utils.py`); stacking both is redundant. Lead with Windows-preinstalled fonts (`Microsoft YaHei` / `SimSun` / `Arial` / `Georgia` / `Consolas`); keep at most **one** macOS-exclusive family (typically `"PingFang SC"`) as a browser-preview nicety.

## icons
- library: chunk-filled
- brand_library: simple-icons
- inventory: target, bolt, shield, users, chart-bar, lightbulb

> `library` MUST be exactly one of `chunk-filled` / `tabler-filled` / `tabler-outline` / `phosphor-duotone` — mixing is forbidden. `brand_library: simple-icons` is optional; include only when the deck uses real company / product brand marks, otherwise omit. `inventory` lists approved icon names (no library prefix); Executor may only use icons from this list. Names are case-sensitive filenames: bundled-library inventory values are the exact verified lowercase basenames (`award`, never `Award`); custom icon names preserve the custom file's exact case.
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
- mode: flat

> One deck-wide native PowerPoint structure policy. Free-design and brand-only routes use `flat`; deck/layout template routes use `structured`.
>
> `flat` keeps every SVG object Slide-local. Export materializes one clean project-owned Master plus one Blank Layout, maps the current color/typography lock into the theme and Master defaults, removes stock content placeholders and unused built-in Layouts, and retains only the standard date/footer/slide-number capability hooks. In this mode, omit `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts`, and do not add root Master/Layout identity, `data-pptx-layer`, or `data-pptx-placeholder*` metadata to generated pages.
>
> When Step 3 loaded a deck/layout template, replace the `flat` row above with exactly one of:
> ```
> - mode: structured
> - template_adherence: adaptive
> ```
> or:
> ```
> - mode: structured
> - template_adherence: strict
> ```
> Both values require complete `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts` sections. Existing legacy template SVGs that lack the current root Master identity, grouped slot/carrier contract, or positive bounds cannot be selected or upgraded in place. Create a current workspace through [`create-template`](../workflows/create-template.md), then generate new structured pages from it.

## pptx_masters
- master-default: Default Master

> Deck/layout template routes only. One row per Master: `<master_key>: <PowerPoint picker name>`. A key contains 1–64 ASCII letters, digits, dots, underscores, or hyphens; its first character is a letter or digit. Spaces belong only in the PowerPoint picker name, never in the key. Keys are deck-unique and stable. Omit this entire section when `pptx_structure.mode: flat`.

## pptx_layouts
- cover-hero-split: master-default | Cover — Hero Split | template:01_cover
- kpi-band-trio: master-default | KPI Band Trio | P02
- content-two-column: master-default | Two Column | template:03a_content_abstract
- quote-focus: master-default | Quote Focus | template:04_quote_focus

> Deck/layout template routes only. This is the unique reusable Layout roster, not a page roster. Layout keys use the same grammar as Master keys. Value format: `<master_key> | <PowerPoint layout name> | <prototype source>`. Supply all three non-empty fields separated by `|`. A prototype source is either `P<NN>` for one generated page carrying that exact Layout contract, or `template:<basename>` for an installed `templates/<basename>.svg`; the `template:` prefix is required, so a bare basename is invalid. Omit this section when `pptx_structure.mode: flat`.
>
> Every Layout key appears exactly once, belongs to exactly one declared Master, and is globally unique even when two Masters use the same picker name. Every declared Master owns at least one Layout definition. A Layout may remain unused by generated pages; such a Layout must use `template:<basename>` so export can register it without manufacturing a published slide.
>
> The definition prototype repeats its identity through root `data-pptx-master`, `data-pptx-master-name`, `data-pptx-layout`, and `data-pptx-layout-name`. Strategist plans the initial roster. If adaptive use genuinely changes reusable framing or slot topology/bounds, Executor adds a new definition and updates the page assignment immediately; never mutate a reused key silently.
>
> Reuse one `(master_key, layout_key)` only when its ordered Layout atoms and slot ids/types/indices/bounds/binding modes are identical. Current text, imagery, crop, or Slide-local geometry does not define Layout identity.
>
> **Different reusable composition → different key.** Name keys after the composition (`timeline-spine`, `kpi-band-trio`), never after PowerPoint stock roles or page topics. Distinct compositions collapsing into stock-role keys (`title-content` for eight different pages) and one shared skeleton splitting into per-topic keys (`allocation-fengqing` / `allocation-luoping` over identical framing) both produce Layout rosters that do not match the deck; the quality checker flags the second as duplicate Layouts.
>
> A Layout may have zero slots. Do not create an empty `utility` kind or a full-page fake `object` slot; the named Layout and its fixed atoms are sufficient.

## page_pptx_layouts
- P01: cover-hero-split
- P02: kpi-band-trio
- P03: content-two-column
- P04: content-two-column

> Deck/layout template routes only. Include exactly one row per generated page. The value is one key declared in `pptx_layouts`; Master and picker name come from that unique definition and are not repeated per page. The generated SVG root must match the assigned definition. Omit this section when `pptx_structure.mode: flat`.

## page_layouts
- P01: 01_cover
- P03: 02a_chapter
- P04: 03a_content_abstract

> For a deck/layout template route, include one entry per page. Key: `P<NN>` matching §IX. Value: the template SVG basename without extension. This is the authoring-input prototype mapping; `page_pptx_layouts` is the output page assignment, while `pptx_layouts` defines the unique reusable roster. Strict preserves the prototype Master/Layout/slot contract. Adaptive retains its Master contract and may explicitly define and assign a new Layout key while authoring. Non-mirror skin follows the project lock.
>
> **No entry for a page** is an error in structured template mode.
>
> **Hard rule**: Use both `page_layouts` and `page_charts` only with a compatible shell. Adaptive mode may start from a neutral content template and finalize a new explicit Layout after design; strict mode must choose an existing compatible Layout or revise the outline.
>
> **Whole section omitted** → required for free-design and brand-only `flat` routes. Template strict/adaptive routes require complete `page_layouts`. A legacy package that cannot satisfy the current structured contract must migrate before use; it never enters a compatibility branch inside normal generation.
>
> **Strategist source**: record each project-page choice in project `design_spec.md §IX Content Outline`, using the copied template package's `templates/design_spec.md §V Page Roster` descriptions as the roster authority. Basenames must match files in `templates/` exactly. A typo is a blocking contract error: stop before drawing and report it; never fall back to free design inside template mode.

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
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters

> **Execution reminder — not authoring authority**: the baseline blacklist above
> is intentionally terse. Add only deck-specific execution locks. General SVG
> required / forbidden / conditional rules are owned by
> [`shared-standards.md`](../references/shared-standards.md); do not copy its
> feature matrix or parameter contracts into `spec_lock.md`. In particular, do
> not move supported-but-non-default spellings such as `rgba()` or compatible
> `<g opacity>` into the generic forbidden list merely to enforce a generation
> preference; their checker warnings remain advisory.
