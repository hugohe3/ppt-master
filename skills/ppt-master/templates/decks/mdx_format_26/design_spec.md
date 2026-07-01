---
deck_id: mdx_format_26
template_id: mdx_format_26
kind: deck
category: brand
summary: Givery Marketing DX '26 brand deck — white canvas, soft gradient orbs, navy #1D2088 identity, Poppins/Noto Sans JP typography.
keywords: [givery, marketing-dx, deca, brand, japanese, navy]
primary_color: "#1D2088"
canvas_format: ppt169
canvas_width: 1280
canvas_height: 720
canvas_viewbox: "0 0 1280 720"
source_canvas_width: 960
source_canvas_height: 540
source_viewbox: "0 0 960 540"
page_count: 13
replication_mode: fidelity
placeholders:
  01a_cover_centered: ["{{TITLE}}", "{{UPDATE_DATE}}"]
  01b_cover_client: ["{{CLIENT_NAME}}", "{{TITLE}}", "{{DATE}}"]
  02a_toc_index: ["{{TOC_HEADING}}", "{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_2_TITLE}}", "{{TOC_ITEM_3_TITLE}}", "{{TOC_ITEM_4_TITLE}}"]
  03a_chapter_light: ["{{SECTION_TITLE}}", "{{SECTION_INDEX}}", "{{PAGE_NUM}}"]
  03b_chapter_dark: ["{{SECTION_TITLE}}", "{{SECTION_INDEX}}", "{{PAGE_NUM}}"]
  04a_content_text: ["{{TITLE}}", "{{LEAD}}", "{{NOTE}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04b_content_headed: ["{{EN_SUBTITLE}}", "{{TITLE}}", "{{BODY}}", "{{FIGURE}}", "{{PAGE_NUM}}"]
  04c_content_two_col: ["{{TITLE}}", "{{BODY}}", "{{HERO_IMAGE}}", "{{PAGE_NUM}}"]
  04d_content_grid: ["{{TITLE}}", "{{CELL_1_TITLE}}", "{{CELL_1_BODY}}", "{{CELL_2_TITLE}}", "{{CELL_2_BODY}}", "{{CELL_3_TITLE}}", "{{CELL_3_BODY}}", "{{CAPTION}}", "{{PAGE_NUM}}"]
  04e_content_process: ["{{TITLE}}", "{{STEP_1}}", "{{STEP_2}}", "{{STEP_3}}", "{{DIAGRAM}}", "{{PAGE_NUM}}"]
  04f_content_figure: ["{{TITLE}}", "{{FIGURE}}", "{{CAPTION}}", "{{PAGE_NUM}}"]
  05a_message_hero: ["{{MESSAGE}}", "{{SUBTEXT}}", "{{BOX_1}}", "{{BOX_2}}", "{{BOX_3}}", "{{PAGE_NUM}}"]
  06a_ending_thanks: ["{{THANKS}}", "{{CONTACT}}"]
---

# MDX Format '26 (Givery Marketing DX) — Design Specification

## I. Template Overview

- **Use cases**: Givery / DECA Marketing DX proposals, company & department introductions, project samples, client-facing decks. Japanese-first business collateral.
- **Design tone**: Clean, bright, corporate-modern. Generous white space, one strong navy identity color, playful gradient orbs as the only decorative motif.
- **Theme mode**: mixed — content/cover/TOC pages are light (white canvas); chapter dividers and the ending run dark (black divider, navy ending).
- **At a glance**: a near-white canvas dusted with soft pink/blue/purple gradient orbs in the corners, a faint oversized "X" watermark, and the "X DECA" or Givery mark tucked in a corner — with deep indigo `#1D2088` doing all the structural work (titles, tabs, footers, page badges).

## II. Color Scheme

Strict 11-color brand palette — **no new colors may be added** (documented brand rule). Legacy deep-red `#C60000` is tolerated only where it already appears (EN subtitles / accents).

| Role | HEX | Application |
|------|-----|-------------|
| Primary (dk1) | `#1D2088` | Titles, cover/chapter tabs, footers, page badges, index pills |
| Secondary (dk2) | `#00A0E9` | 2nd accent bar in grids/process/boxes, dark-chapter index lines |
| Light bg (lt1) | `#FFFFFF` | Page canvas, text on dark |
| Panel (lt2) | `#EDEDF3` | Grid / step card fills |
| accent1 | `#E4007F` | Figure-zone dashed frame, 3rd accent bar in grids/boxes |
| accent2 | `#F94549` | Reserved (rotational label chips) |
| accent3 | `#A81B8D` | Figure-zone placeholder captions |
| accent4 | `#FFD100` | Reserved |
| accent5 | `#6ABF4B` | Reserved |
| accent6 | `#06C755` | Reserved |
| hlink | `#0097A7` | TOC secondary (not-yet-reached) items, underlined links |
| legacy red | `#C60000` | English subtitle / accent on headed content (existing usage only) |

**Rotation rule**: multi-cell grids, process steps and hero boxes cycle their accent bar/fill navy `#1D2088` → cyan `#00A0E9` → pink `#E4007F`.

## III. Typography

Japanese-first stacks; every stack ends in a preinstalled family.

- **Body / Japanese**: `"Noto Sans JP", sans-serif`
- **Display titles / big message**: `"Poppins ExtraBold", "Noto Sans JP", sans-serif`
- **Brand lockup labels ("Marketing DX", "Index", "Page", "© 2026 Givery, Inc")**: `"Poppins", sans-serif`
- **English subtitles / dates**: `"Montserrat", Arial, sans-serif`
- **Some JP titles**: `Arial, "Noto Sans JP", sans-serif` (bold)

Poppins ExtraBold, Poppins, Noto Sans JP and Montserrat are **not preinstalled** — they lead their stacks by design intent and fall back to `sans-serif`/`Arial`. Install/embed for exact fidelity.

## IV. Signature Design Elements

- **Gradient-orb canvas**: white base with soft blurred pink/blue/purple orbs pinned to two opposite corners, plus a faint oversized `X` watermark or the small `X DECA` / Givery mark in a corner. This is baked into the bundled background PNGs — do not redraw it as vectors.
- **Navy edge tabs (cover)**: two solid `#1D2088` rectangles bleeding off the left and right edges at vertical center frame the cover title.
- **Center logo lockup**: "Marketing DX / powered by Givery" stacked and centered above a short navy underline; appears on covers.
- **Footer lockup**: "© 2026 Givery, Inc" in navy Poppins with a 2px navy underline, bottom-left; mirrored date/underline bottom-right on covers.
- **Page badge**: navy rounded pill "Page {{PAGE_NUM}}" bottom-right on content pages; bare navy page number bottom-right on chapters.
- **Chapter index pill**: centered navy rounded pill (white index text) flanked by two horizontal navy rules — the recurring "Index｜NN" divider signature.
- **Figure placeholder zone**: the source's white 25%-opacity rectangle with a **3px pink `#E4007F` dashed border** (`stroke-dasharray="4,4"`) and a centered navy picture-frame icon (`assets/figure_placeholder.png`) — used verbatim wherever an image/diagram slot is offered.
- **Grid rhythm**: 3 equal peer cards, gap 40px, `#EDEDF3` fill, 8px top (grid) or left (process) accent bar, flat (no shadows).
- **Margins**: content left/right ≈96px, header baseline ≈55–107px, footer band ≈657–700px.

## V. Page Roster

Visual fidelity: cover/chapter/ending pages are **literal** (original geometry, decoration and backgrounds reproduced at ×1.3333); content pages are **fidelity** (structure and tone kept, layout tidied). Geometry normalized from the 960×540 source to the 1280×720 canvas.

| File | Cluster source | Description |
|------|----------------|-------------|
| `01a_cover_centered.svg` | slide1 | Cover ①: full-bleed orb bg, navy edge tabs, centered title + Givery/Marketing-DX logo lockup, dated footer. |
| `01b_cover_client.svg` | slide4/58 | Cover ②: client-addressed — left-aligned client name + large title over Givery-branded bg, dated footer. |
| `02a_toc_index.svg` | slide2 | Table of contents: big "Index" heading + JP subheading, bulleted chapter list (navy reached / cyan-underlined pending). |
| `03a_chapter_light.svg` | slide7/12/45 | Chapter divider (light): centered navy title over DECA-X orb bg, navy "Index｜NN" pill between two rules. |
| `03b_chapter_dark.svg` | slide4/6/46 | Chapter divider (dark): centered white title on solid black, cyan-ruled navy index pill. |
| `04a_content_text.svg` | slide8/9 | Text-led content: navy title, bold 2-line lead, small note, wide bottom figure zone. |
| `04b_content_headed.svg` | slide28/37 | Standard headed content: red EN subtitle + bold JP title, body, figure zone. |
| `04c_content_two_col.svg` | slide37 | Two-column: left body text, right full-height hero-image placeholder. |
| `04d_content_grid.svg` | slide36/43/59 | Comparison grid: three flat `#EDEDF3` cards with navy/cyan/pink accent bars + caption. |
| `04e_content_process.svg` | slide40/53 | Process/flow: three numbered step cards joined by navy arrows, cycling accents. |
| `04f_content_figure.svg` | slide11/20/25 | Figure-led: small title over one large full-width figure zone + caption. |
| `05a_message_hero.svg` | slide13/19 | Big-message hero: right-aligned subtext, huge centered message, optional navy/cyan/pink box row. |
| `06a_ending_thanks.svg` | slide62/layout34 | Ending: navy canvas, Givery logo, thank-you line, white "DECA" search-pill mark, contact block. |

## VI. Assets

Bundled in `assets/` (extracted brand chrome, renamed semantically). Sample-specific screenshots, partner logo grids and comparison figures are **not** bundled — they are offered as `{{FIGURE}}` / `{{HERO_IMAGE}}` placeholder zones instead.

| File | Source | Dimensions | Usage |
|------|--------|-----------|-------|
| `cover_bg.png` | image21 | 2048×1152 | Cover ① background (X watermark + orbs) |
| `cover_client_bg.png` | image60 | 2048×1152 | Cover ② background (baked Givery mark + orbs) |
| `toc_bg.png` | image16 | 2048×1152 | TOC background (X watermark + X-DECA mark + orbs) |
| `chapter_light_bg.png` | image12 | 2048×1152 | Light chapter background (X-DECA mark + orbs) |
| `content_bg.png` | image24 | 2048×1152 | Standard content background (DECA mark + faint orbs) |
| `message_bg.png` | image11 | 2048×1152 | Message hero background (orbs + DECA mark) |
| `ending_bg.png` | image5 | 2048×1152 | Spare light background (orbs + DECA mark) |
| `givery_logo.png` | image1 | 2048×609 | Givery logo lockup (cover / ending) |
| `figure_placeholder.png` | image25 | 1080×1080 | Navy picture-frame icon centered in figure/image zones |

## VII. Placeholder Overrides

This brand deck uses a bespoke vocabulary declared in the `placeholders:` frontmatter above (`{{CLIENT_NAME}}`, `{{UPDATE_DATE}}`, `{{SECTION_TITLE}}`, `{{SECTION_INDEX}}`, `{{LEAD}}`, `{{NOTE}}`, `{{EN_SUBTITLE}}`, `{{HERO_IMAGE}}`, `{{CELLS}}`→`{{CELL_n_*}}`, `{{STEPS}}`→`{{STEP_n}}`, `{{DIAGRAM}}`, `{{MESSAGE}}`, `{{SUBTEXT}}`, `{{BOXES}}`→`{{BOX_n}}`, `{{THANKS}}`, `{{CONTACT}}`). Rationale: the source deck is a Japanese business-proposal system whose page semantics (client-addressed cover, "Index｜NN" chapter marker, EN-subtitle + JP-title content header, big-message hero) do not map onto the generic cover/chapter/content vocabulary. `{{TOC_ITEMS}}` and `{{CELLS}}`/`{{STEPS}}`/`{{BOXES}}` from the brief are realized as indexed per-item slots for authoring clarity. `{{PAGE_NUM}}` follows the canonical convention.
