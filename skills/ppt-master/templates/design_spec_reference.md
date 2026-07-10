# {project_name} - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | {project_name} |
| **Canvas Format** | {canvas_info['name']} ({canvas_info['dimensions']}) |
| **Page Count** | [Filled by Strategist] |
| **Design Style** | {design_style} |
| **Target Audience** | [Filled by Strategist] |
| **Use Case** | [Filled by Strategist] |
| **Delivery Purpose** | [`text` read-close / `balanced` business / `presentation` — confirmed at c; a deck-wide consumption mode that drives per-page density, page-count recommendation, page_rhythm lean, and the body baseline (px). See strategist.md §6.1.] |
| **Content Strategy** | [Material divergence — the user's free-text intent on how closely to follow the source vs how freely to reshape it (or "balanced default"); facts stay sourced however free. Confirmed at c; consumed when authoring §IX. Not in spec_lock.] |
| **Template Adherence** | [`adaptive` / `strict` — include only when Step 3 loaded a deck/layout template; omit for free design and brand-only templates. Also written under `spec_lock.md pptx_structure`.] |
| **Created Date** | {date_str} |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | {canvas_info['name']} |
| **Dimensions** | {canvas_info['dimensions']} |
| **viewBox** | `{canvas_info['viewbox']}` |
| **Margins** | [Recommended by Strategist, e.g., left/right 60px, top/bottom 50px] |
| **Content Area** | [Calculated from canvas] |

---

## III. Visual Theme

### Theme Style

- **Mode**: [pyramid / narrative / instructional / showcase / briefing — narrative skeleton, locked at d Layer 1]
- **Visual style**: [preset name or custom — aesthetic, locked at d Layer 2; carries no HEX]
- **Theme**: [Light theme / Dark theme]
- **Tone**: [Filled by Strategist, e.g., tech, professional, modern, innovative]

### Color Scheme

> Strategist: determine values from project content, industry, brand colors.
> Step 4 Confirm UI: present **≥3** color candidates (creative recommendations always offer real choice — same rule as h.5; fewer only on the honest-shortfall exception, with a stated reason), each with a user-facing core `palette` (background / secondary_bg / primary / accent / secondary_accent / body_text), in `confirm_ui/recommendations.json`; the confirmed candidate from `result.json` seeds this table. Strategist derives the remaining text, border, state, and style-neutral colors when writing this full scheme. Schema: [`scripts/docs/confirm_ui.md`](../scripts/docs/confirm_ui.md).

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#......` | Page background (light theme typically white; dark theme dark gray/navy) |
| **Secondary bg** | `#......` | Card background, section background |
| **Primary** | `#......` | Title decorations, key sections, icons |
| **Accent** | `#......` | Data highlights, key information, links |
| **Secondary accent** | `#......` | Secondary emphasis, gradient transitions |
| **Body text** | `#......` | Main body text (dark theme uses light text) |
| **Secondary text** | `#......` | Captions, annotations |
| **Tertiary text** | `#......` | Supplementary info, footers |
| **Border/divider** | `#......` | Card borders, divider lines |
| **Success** | `#......` | Positive indicators (green family) |
| **Warning** | `#......` | Issue markers (red family) |

> **Reference**: Industry colors in `references/strategist.md` or `scripts/config.py` under `INDUSTRY_COLORS`

### AI Image Strategy (fill only when §VIII has `ai` rows)

- **Image Rendering**: [one of the 20 names in `references/image-renderings/_index.md` (e.g. `vector-illustration`), or `custom`]
- **Image Rendering Behavior**: [required when Rendering is `custom`; one-paragraph prose per `image-renderings/_index.md §1.5`]
- **Image Palette**: [one of the 14 names in `references/image-palettes/_index.md` (e.g. `cool-corporate`), or `custom`]
- **Image Palette Behavior**: [required when Palette is `custom`; one-paragraph prose per `image-palettes/_index.md §2`]

> Strategist: lock these once per deck in h.5; every AI image inherits them. Cross-check the rendering × palette compatibility matrix in `image-palettes/_index.md` — avoid `✗` combinations (matrix only covers presets; when either dimension is `custom`, Strategist owns the compatibility judgment). Leave the section out entirely if §VIII has no `ai` rows. Omit the `Behavior` rows whenever the corresponding dimension is a preset name.

### Gradient Scheme (if needed, using SVG syntax)

```xml
<!-- Title gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#[primary]"/>
  <stop offset="100%" stop-color="#[secondary accent]"/>
</linearGradient>

<!-- Background decorative gradient (note: rgba forbidden, use stop-opacity) -->
<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#[primary]" stop-opacity="0.15"/>
  <stop offset="100%" stop-color="#[primary]" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

> **Per-role families are expected, not optional.** Title / Body / Emphasis / Code may each use a different family (e.g., display serif title + geometric sans body). One family throughout is not required. See [strategist.md §g — Font Combinations](../references/strategist.md) for starting directions; you may propose a combination not listed.
>
> **⚠️ PPT-safe stack discipline (HARD rule).** PPTX stores concrete exported Latin / EA typefaces per run — no runtime fallback. Every stack's exported Latin / EA typefaces MUST resolve to cross-platform pre-installed fonts: `"Microsoft YaHei"` / `SimSun` / `Arial` / `"Times New Roman"` / `Consolas`. Stacks that export non-preinstalled typefaces (Inter / Google Fonts / brand typefaces) are allowed only when this spec notes the font-install or embedding requirement.

**Typography direction**: [Fill in one phrase, e.g., "modern CJK sans" / "academic serif" / "brand-specific: McKinsey Bower (requires font install)"]

> Step 4 Confirm UI: present **≥3** typography candidates (creative recommendations always offer real choice — same rule as h.5; fewer only on the honest-shortfall exception, with a stated reason), each splitting CJK + Latin for `heading` and `body` (with `css` preview stacks) and declaring `body_size` as the body baseline in **px** (the system's only unit, every canvas), in `confirm_ui/recommendations.json`; the confirmed `result.json` carries px directly — no conversion. Schema: [`scripts/docs/confirm_ui.md`](../scripts/docs/confirm_ui.md).

Two views on the same font decisions — fill both, keep them consistent:

- **Role breakdown** (table below) — lists the *pieces* per role: CJK font, Latin font, CSS generic fallback. Human-readable design language.
- **Per-role font stacks** (after the table) — the *ordered* CSS `font-family` strings that actually go into SVG `font-family=""` and `spec_lock.md`'s `*_family` lines. Order controls browser rendering (Latin-led vs. CJK-led), so this is the **actual data** — not derivable from the table alone.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | [e.g., `"Microsoft YaHei"`, or `"Microsoft YaHei", "PingFang SC"` for macOS preview nicety] | [e.g., `Georgia`] | [e.g., `serif`] |
| **Body** | [e.g., `"Microsoft YaHei", "PingFang SC"`] | [e.g., `Arial`] | [e.g., `sans-serif`] |
| **Emphasis** | [e.g., `SimSun`, or `—` for Latin-only] | [e.g., `Georgia`] | [e.g., `serif`] |
| **Code** | — | [e.g., `Consolas, "Courier New"`] | [e.g., `monospace`] |

**Per-role font stacks** (CSS `font-family` strings, one per role — arrange the table's pieces in the order your design intends):

- Title: `[Fill in stack, e.g. Georgia, "Microsoft YaHei", serif for Latin-led; or "Microsoft YaHei", "PingFang SC", Georgia, serif for CJK-led]`
- Body: `[Fill in stack — may be same as Title]`
- Emphasis: `[Fill in stack, or write "same as Body" to omit the override]`
- Code: `[Fill in monospace stack, e.g. Consolas, "Courier New", monospace]`

> **Stack ordering — why it matters**: CSS `font-family` falls back font-by-font (not char-by-char) — the browser uses the **first installed** font for everything it can render, skipping to the next only when a glyph is missing. So:
> - `Georgia, "Microsoft YaHei", serif` → Latin in Georgia (elegant serif), CJK falls through to Microsoft YaHei. **Use when Latin typography is the primary design statement** (academic / editorial / Latin-heavy covers).
> - `"Microsoft YaHei", Georgia, serif` → Everything in Microsoft YaHei (Latin uses YaHei's Latin glyphs — a different design tone). **Use when the deck is CJK-primary and Latin is incidental**.
>
> The converter (`drawingml/utils.py parse_font_family`) maps these to PPTX `<a:latin>` / `<a:ea>` regardless of order — but browser preview and SVG native rendering reflect stack order. Pick the order matching your design intent.

> **Why two views**: the breakdown shows role assignment at a glance; stacks carry the ordering info the breakdown can't encode. Keep both consistent — table cells should be exactly the fonts in the stacks (any order).

### Font Size Hierarchy

> **Ramp discipline, not a fixed menu.** `body` is the single anchor; every other size is a ratio of it. Each row below gives the role's allowed ratio band. **Structural roles (page title / body / subtitle / annotation / footnote) resolve to one size each and stay that size deck-wide** — pick the value once, lock it, reuse it on every page; same-role drift is what makes a deck look unprofessional. The in-band freedom to use an intermediate value without pre-declaring is for **special / feature elements** (hero number, cover / section display headline, one-off emphasis); if such a size recurs, declare it as its own slot so it too stays consistent.
> **Unit boundary (HARD rule).** Author this section in **unitless px** — the system's only unit, every canvas. There is no pt layer and no conversion: the confirmed value is already px. Never write `pt`, `px`, `em`, or any unit in `spec_lock.md` or SVG. Geometry (margins / gaps / card sizes) is px everywhere.
> **Baseline selection**: **delivery purpose** sets the body baseline to **one fixed value** (not a range); content density and visual style drive page treatment / rhythm / the *other* roles, **not** the body size.

**Baseline (unitless px)**: Body font size = [fill in]. For PPT 16:9, the confirmed delivery-purpose value is **one fixed px per purpose, not a range**: **`text` / read-close** `20`, **`balanced` / business** `24` (default), **`presentation`** `32`. The body baseline is purely a function of delivery purpose — density and visual style drive page treatment / rhythm / the other roles, never the body size. The user may also pin individual role sizes (`title` / `subtitle` / `annotation`) directly in the Confirm UI — a confirmed per-role value (`result.json typography.sizes`) is already px and becomes the locked slot for that role; the rest derive from the ramp. For non-PPT canvases, author px from the confirmed canvas scale (see [strategist.md §g](../references/strategist.md) per-canvas table).

| Purpose | Ratio to body | Example @ body=32 (`presentation`) | Example @ body=24 (`balanced`) | Weight |
| ------- | ------------- | --------------------------- | ------------------------- | ------ |
| Cover title (hero headline) | 2.5-5x | 80-160 | 60-120 | Bold / Heavy |
| Chapter / section opener | 2-2.5x | 64-80 | 48-60 | Bold |
| Page title | 1.5-2x | 48-64 | 36-48 | Bold |
| Hero number (consulting KPIs) | 1.5-2x | 48-64 | 36-48 | Bold |
| Subtitle | 1.2-1.5x | 38-48 | 29-36 | SemiBold |
| Lead-in / intro | 1.1-1.4x | 35-45 | 26-34 | Regular / Medium |
| Subheading | 1.1-1.3x | 35-42 | 26-31 | SemiBold |
| **Body content** | **1x** | **32** | **24** | Regular |
| Annotation / caption | 0.7-0.85x | 22-27 | 17-20 | Regular |
| Page number / footnote | 0.5-0.65x | 16-21 | 12-16 | Regular |

> **Subtitle / lead-in / subheading bands overlap by design** — choose among them by *role*, not size: `subtitle` sits under a title, `lead` is a lead-in / pull-quote in the body flow, `subheading` labels a block inside the content area. Each is its own slot, declared only when the deck uses it, and then held at one size deck-wide like any structural role. Font stays at the **family** level (no new typeface per role): `subheading` → heading / `title_family`, `lead` → `body_family` or `emphasis_family` — size + weight carry the hierarchy.
> The two px columns are illustrations for common baselines. For any other `body` value, multiply by each row's ratio. All size values here and in `spec_lock.md` are px (no pt anywhere). The checker (`svg_quality_checker._check_spec_lock_drift`) reads the live `body` (px) from `spec_lock.md` and applies the bands, so no code change is needed for a different baseline.

> Sizes outside **every** band remain forbidden — surface the need and extend `spec_lock.md typography` (e.g., `cover_title: 96`) rather than invent a one-off value.

> **Hero in single-focus / breathing pages**: when one element *is* the entire page — a large number, a headline, a key phrase — it is the visual subject, not body content. Such heroes may borrow the cover-title band (2.5–5×); for greater emphasis, declare a hero slot in `spec_lock.md` (e.g., `hero_number` / `hero_headline`) — checker exempts declared slots with no fixed upper limit. The row above "Hero number (consulting KPIs) 1.5–2×" applies only to numeric KPIs in dashboard/data layouts, not to full-page focal elements.

---

## V. Layout Principles

### Page Structure

- **Header area**: [Height and content description]
- **Content area**: [Height and content description]
- **Footer area**: [Height and content description]

### Layout Pattern Library (combine or break as content demands)

> **Principle — proportion follows information weight, not preset ratios.** The table below is a pattern library, not a menu. Combine two patterns on one page, break the grid entirely for a `breathing` page, or propose a pattern not listed when content calls for it. Defaulting every page to a symmetric grid produces the "AI-generated" look — vary intentionally.

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | Covers, conclusions, key points |
| **Symmetric split (5:5)** | Comparisons where two sides carry equal weight |
| **Asymmetric split (3:7 / 2:8)** | One side dominates — data chart vs. brief takeaway, image vs. caption |
| **Top-bottom split** | Processes, timelines, ultra-wide image + text |
| **Three/four column cards** | Feature lists, parallel points, team intros |
| **Matrix grid (2×2)** | Two-axis classifications, strategic quadrants |
| **Z-pattern / waterfall** | Storytelling, case studies — content blocks alternate left/right guiding the eye |
| **Center-radiating** | Core concept + surrounding nodes, ecosystem / stakeholder maps |
| **Full-bleed + floating text** | `breathing` / feature pages — image fills canvas, text floats with opacity overlay |
| **Figure-text overlap** | Hero moments — headline / big number sits over or against an image edge instead of beside it |
| **Negative-space-driven** | A single element in 40-60% whitespace — lets one idea land with weight |

### Spacing Specification

> Spacing defaults depend on **container type**. Cards are one option, not the universal default. Tables below split by container type; a page may consult only one set (e.g., a `breathing` page with no cards uses only universal + non-card entries).

**Universal** (any container type):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Safe margin from canvas edge | 40-60px | [fill in] |
| Content block gap | 24-40px | [fill in] |
| Icon-text gap | 8-16px | [fill in] |

**Card-based layouts** (consult only when the page uses cards — typically `dense` pages with parallel containers):

| Element | Recommended Range | Current Project |
| ------- | ---------------- | --------------- |
| Card gap | 20-32px | [fill in] |
| Card padding | 20-32px | [fill in] |
| Card border radius | 8-16px | [fill in] |
| Single-row card height | 530-600px | [fill in] |
| Double-row card height | 265-295px each | [fill in] |
| Three-column card width | 360-380px each | [fill in] |

**Non-card containers** (naked text blocks / full-bleed imagery / divider-separated content — typical for `breathing` pages or minimalist designs):

- Vertical rhythm carried by **whitespace**, not gutters — block gaps run wider than card gaps since there's no container edge to separate content.
- **Line-height**: ~1.4–1.5× for dense/small-body text (CLReq comfortable minimum); 1.6–2.0× for large-type, sparse, or `breathing` pages.
- **Full-bleed text placement**: inset text away from the image's focal points; legibility over photographic backgrounds typically needs a gradient or opacity overlay.
- **Content width** is driven by reading comfort and image composition, not a card grid slot — don't back-compute "column width" when there's no column.

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `templates/icons/` (11,600+ icons across five libraries; see `templates/icons/README.md`)
- **Usage method**: SVG placeholder `<use data-icon="library/icon-name" .../>`; Design Spec should list approved `library/icon-name` entries for Executor.

### Recommended Icon List (fill as needed)

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| [example] | `chunk-filled/circle-checkmark` | Slide XX |

---

## VII. Visualization Reference List (if needed)

> When pages map to a chart-library template (data charts OR structural patterns — team rosters, agendas, frameworks, etc.), Strategist lists them here for Executor reference. Single combined table — `summary-quote` column is the anti-fabrication audit, `path` + `usage` columns serve Executor lookup.

Catalog read: 76 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P05 | grouped_bar_chart | `templates/charts/grouped_bar_chart.svg` | "Pick for 2-4 series side-by-side across the same categories (e.g. YoY/QoQ). Skip if showing composition within each category (use stacked_bar_chart)." | YoY revenue comparison by product line |

**Runners-up considered** (3 entries minimum, drawn from real second-best matches in this deck):

- `<key_A>` | rejected for P05: `<reason citing this deck's specifics>`
- `<key_B>` | rejected for P##: `<reason>`
- `<key_C>` | rejected for P##: `<reason>`

> **Audit rule**: `Summary-quote` must be copy-pasted verbatim — paraphrasing breaks the audit. Every template name listed must `grep` cleanly inside `charts_index.json` (so misspellings/inventions fail). If fewer than 3 viz pages exist, list what exists and note "fewer than 3 viz pages"; runners-up still required for each page that does exist.

---

## VIII. Image Resource List (if needed)

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_bg.png | {canvas_info['dimensions']} | [ratio] | Atmospheric cover backdrop — SVG title overlays the calm region | Background | #1 full-bleed background with floating title + #29 two-stop scrim | ai | Pending | [subject + intent + composition, no style/HEX] | none | hero_page |
| comparison_p07.png | {canvas_info['dimensions']} | [ratio] | Three-panel approach comparison — panel labels stay inside the image | Diagram | #44 background image + native network/architecture diagram | ai | Pending | Three side-by-side schematic motifs comparing approach A / B / C, panel labels rendered inside each motif | embedded | local |
| formula_001.png | [actual dimensions from formula manifest / image_analysis] | [ratio] | Block equation on P03 | Latex Formula | formula-block | formula | Rendered | `E = mc^2` — energy-mass equation | | |

> **Layout pattern column is MANDATORY** — for non-formula rows, value is one or more `#<id> <name>` joined by ` + ` drawn verbatim from [`references/image-layout-patterns.md`](../references/image-layout-patterns.md) (Primary + optional Modifiers). Empty cells, paraphrased names, or invented ids invalidate the row. Formula rows are the only exception; use `formula-inline` or `formula-block`. See `strategist.md §h` GATE for the three-layer requirement (read → produce → image-as-canvas coverage).

**Type** (free-form category tag; common values):

- `Background` — cover / chapter / full-bleed atmosphere
- `Photography` — real-world photo
- `Illustration` — vector / flat / painterly art
- `Illustration Sheet` — a grid of several spot illustrations generated as one image to be sliced (the `ai` sheet row of a `slice` set; never placed itself)
- `Diagram` — schematic / architecture / flowchart
- `Portrait` — single-subject person
- `Latex Formula` — formula PNG rendered by `latex_render.py`

**Status**:

- **Pending** — needs AI generation or web sourcing
- **Rendered** — deterministic formula asset already exists under `images/`
- **Existing** — user-supplied, place in `images/`
- **Placeholder** — not yet processed, use dashed border in SVG

**Acquire Via**:

- `ai` — Step 5 Image_Generator
- `web` — Step 5 Image_Searcher
- `formula` — already rendered by `latex_render.py` before this spec was written
- `user` — user-supplied
- `placeholder` — intentionally deferred
- `slice` — a spot-illustration element derived in Step 5 by cutting it out of an `ai` sheet row (not generated on its own)

> **Spot-illustration sheets (`slice`).** When the deck draws several same-family spot illustrations from one generated sheet (see [`image-generator.md`](../references/image-generator.md) §4.3), write **two kinds of rows**: one **sheet row** (`Acquire Via: ai`, `Type: Illustration Sheet`, name the intended cell shape + placement purpose in `Reference`, e.g. `portrait side-accent spot set` or `landscape footer-vignette spot set`) that is generated but **never placed** — keep it out of `spec_lock.md images`; and one **element row per used element** (`Acquire Via: slice`, `Reference` naming the parent sheet + cell/element, dimensions filled after slicing) that **is** placed — list every element row in `spec_lock.md images` so the Executor may reference it. Strategist states the shape intent; Image_Generator chooses the exact sheet ratio, grid, and slice command. An element row with no sheet row, or a sliced file absent from `spec_lock.md images`, is an invalid spec. **Each element row's Layout pattern must come from the decorative-cutout family** (`#63` sticker, `#4` edge bleed, `#58` corner fragment, `#66` fade-out, `#69` rotation, `#49` cluster) — a transparent spot is an accessory placed at the margins / off-edge / behind text, never centered in a boxed tile.

**text_policy** (`ai` rows only; AI judges per row, no global default bias):

- `none` — image carries no text; SVG overlays all labels
- `embedded` — image contains in-artwork text: decorative lettering, a designed title, hand-lettered keywords, or stable visual identifiers (axis labels, subplot letters, unit symbols). Body copy / data points / long quotes never go inside the image regardless — they must stay editable. Embedded text is frozen into the raster, so the exact characters are named literally in the prompt

**page_role** (`ai` rows only; leave blank for default):

- *blank / `local`* — image is a region block on an SVG page
- `hero_page` — image is the page's main voice; SVG overlay is minimal or empty. Use on covers, chapter dividers, mood transitions, single-number data heroes, closing quotes. Same rendering and palette as the rest of the deck regardless

**Reference grammar** (`ai` rows): write **subject + intent + composition** only. Do NOT repeat style words ("flat design", "modern") or HEX values — both are already locked deck-wide by `design_spec §III AI Image Strategy` (rendering + palette) and `§III Color Scheme` (HEX triplet). Image_Generator's prompt assembler injects them.

---

## IX. Content Outline

### Part 1: [Chapter Name]

#### Slide 01 - Cover

- **Cover impact**: [MANDATORY — see strategist.md §6.2. Name one concrete hook (provocative core claim / hero number / object-scene metaphor / founder-product-audience moment / distilled conflict) + one composition strategy (full-bleed image + floating title / typographic poster / hero object / data hook / editorial scene / high-contrast abstract geometry / or a fresh one the subject suggests). This is the cover's spine — do NOT fall back to "title + subtitle + decorative background".]
- **Layout**: [realize the Cover impact above; choose the composition that delivers it — not a default centered title block]
- **Title**: [Main title]
- **Subtitle**: [Subtitle]
- **Info**: [Author / Date / Organization]

#### Slide 02 - [Page Name]

- **Layout**: [Choose a pattern from §V, combine two, or break the grid as the content demands]
- **Title**: [Page title]
- **Core message**: [the one thing this page exists to land — its spine, always phrased as one assertion sentence (prose by nature). One per page; can't name it → merge or cut the page.]
- **Visualization**: [visualization_type] (see VII. Visualization Reference List)
- **Content**: write each block in the phrasing that fits it (prose / bullet / keyword / … any phrasing the content calls for) and write it already in that mode, so the texture itself carries the intent — a prose block reads as a real sentence, not a fragment. One page may mix modes; blocks still sit under the core message, never replace it:
  - [a connected sentence or two that argues the point]
  - [parallel fragment] · [parallel fragment] · [parallel fragment]
  - [label] / [label] / [label]

> **Visualization field**: add only when the page has data visualization or structured infographic elements. Type must be listed in §VII.

---

[Strategist continues adding more pages based on source document content and page count planning...]

---

#### Slide NN - Closing  *(only if the deck genuinely lands on a conclusion / CTA / final-takeaway page — do NOT invent one to fill this slot; see strategist.md §6.2)*

- **Closing impact**: [MANDATORY for the closing page — name the one thing the audience leaves with (distilled takeaway / forward call / memorable restatement of the core claim) + one composition that lands it. Do NOT write a generic "Thank you" / contact-only / centered-title reprise of the cover.]
- **Layout**: [realize the Closing impact above — the deck's final impression, not a default sign-off]
- **Content**: [the takeaway / call-to-action itself, phrased to land]

---

## X. Speaker Notes Requirements

One speaker note file per page, saved to `notes/`:

- **Filename**: match SVG name (e.g., `01_cover.md`)
- **Content**: script key points, timing cues, transition phrases

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `{canvas_info['viewbox']}`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography & symbols as raw Unicode (em dash `—`, en dash `–`, `©`, `®`, `→`, NBSP, etc.); HTML named entities (`&nbsp;`, `&mdash;`, `&copy;`, `&reg;` …) are FORBIDDEN. XML reserved chars in text MUST be escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;` (e.g. `R&amp;D`, `error &lt; 5%`). See shared-standards.md §1.0
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` must be in `<defs>`, `orient="auto"`, shape must be triangle / diamond / circle (see shared-standards.md §1.1)
8. `clipPath` conditionally allowed **only on `<image>` elements**: `<clipPath>` in `<defs>`, single shape child (circle / ellipse / rect with rx,ry / path / polygon). Do NOT apply to shapes / groups / text — draw the target geometry directly with the matching native element (`<circle>` / `<ellipse>` / `<rect rx>` / `<polygon>` / `<path>`). See shared-standards.md §1.2

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
