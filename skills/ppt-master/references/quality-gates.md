# Presentation Quality Gates Reference

Shared quality contract for Strategist and Executor. Use this reference to keep decks story-led, readable, editable, and accessible.

---

## 1. Evidence Base

| Source | URL | Applied rule |
|---|---|---|
| UCSD Evidence-Based Presentation Design | `https://multimedia.ucsd.edu/best-practices/presentation-design.html` | Prefer visual explanation over text volume; avoid decorative visuals that do not serve the message. |
| Harvard T.H. Chan Slide Checklist | `https://hsph.harvard.edu/research/health-communication/resources/slide-checklist/` | Use sentence headlines, 2-4 bullets, generous whitespace, readable type, and sufficient contrast. |
| Ten Simple Rules for Effective Presentation Slides | `https://pmc.ncbi.nlm.nih.gov/articles/PMC8638955/` | Make slides tell one larger story; avoid text-only slides; a slide that cannot be explained in about one minute is too complex. |
| Microsoft Accessibility Checker Rules | `https://support.microsoft.com/en-gb/office/rules-for-the-accessibility-checker-651e08f2-0fc3-4e10-aaca-74b4a67101c1` | Check contrast, alt text, reading order, and color-only meaning before release. |

> Note: These sources are decision support. The runtime contract below is authoritative inside `ppt-master`.

---

## 2. Storyline Contract

**Mandatory**: Before writing `design_spec.md`, Strategist must produce a deck storyline in working context. For long or split-mode decks, save it as `<project_path>/storyline.md`; for short decks, embed the same fields in `design_spec.md §IX` planning notes.

| Field | Requirement |
|---|---|
| `deck_thesis` | One sentence: what the whole deck proves or teaches. |
| `audience` | The real audience and their decision / behavior after the presentation. |
| `desired_decision_or_behavior` | Observable outcome, not a vague mood. |
| `chapters` | Ordered sections; each chapter has one claim. |
| `pages` | Each page has a headline, one message, evidence/example, speaker-note role, visual role, and density. |

**Schema**:

```yaml
deck_thesis:
audience:
desired_decision_or_behavior:
chapters:
  - chapter_title:
    chapter_claim:
    pages:
      - page_id:
        headline:
        one_message:
        evidence_or_example:
        speaker_note_role:
        visual_role:
        density: low | medium | high
```

**Forbidden — storyline drift**:

- Page headlines that are only noun labels, unless the page is a cover / agenda / appendix.
- Multiple independent messages on one page.
- A visual whose only role is decoration.
- Speaker notes that repeat slide text instead of carrying transitions, nuance, or explanation.

---

## 3. Page Contract

**Mandatory**: Every page in `design_spec.md §IX Content Outline` must be reducible to this contract. The exact YAML does not need to be emitted for every deck, but the fields must be represented by the outline.

| Field | Requirement |
|---|---|
| `headline` | Sentence headline; states the takeaway. |
| `audience_question` | The question this page answers for the audience. |
| `main_message` | Exactly one message. |
| `supporting_evidence` | Data, example, command, screenshot, quote, workflow, or rationale. |
| `visual_type` | Use a concrete type: table, process, matrix, journey, metric, command, checklist, screenshot, image, or custom. |
| `density_budget` | Declare rough caps before layout: text blocks, bullets, rows, columns. |
| `must_not_include` | Exclusions that prevent clutter or scope creep. |
| `speaker_note` | The narrative job of the note, not the full final script. |

**Schema**:

```yaml
page_id:
headline:
audience_question:
main_message:
supporting_evidence:
visual_type: table | process | matrix | journey | metric | command | checklist | screenshot | image | custom
density_budget:
  max_text_blocks:
  max_bullets:
  max_rows:
  max_columns:
must_not_include:
speaker_note:
```

---

## 4. Layout Budget

**Hard rule**: Strategist records layout budgets in `spec_lock.md quality` when a deck is dense, training-oriented, table-heavy, or likely to be generated across a long context. Executor treats missing values as the defaults below.

| Budget | Default | Applies to |
|---|---:|---|
| `max_cards_per_dense_page` | 6 | Dense pages with cards / panels. |
| `max_parallel_columns` | 4 | Any side-by-side layout. |
| `min_outer_margin` | 72 | Standard 16:9 / 1080p canvases; scale proportionally for smaller formats. |
| `min_card_gap` | 24 | Card and panel layouts. |
| `min_line_height_ratio` | 1.35 | Body text blocks. |
| `max_body_lines_per_text_block` | 2 | Continuous body paragraphs. |
| `max_bullets_per_block` | 4 | Bullet lists. |
| `max_table_rows_regular` | 6 | Regular readable tables. |
| `max_table_cols_regular` | 4 | Regular readable tables. |

**Density fallback**:

| Condition | Action |
|---|---|
| Content exceeds a text / table budget | Split page, convert to visual structure, or move detail to speaker notes. |
| A page needs more than one primary focus | Split page or promote one focus and demote the rest to annotations. |
| A dense page exceeds card / column caps | Use a timeline, process chain, table, or matrix instead of adding more cards. |

---

## 5. Accessibility Gate

**Mandatory**: Accessibility is a release condition, not a decoration pass.

| Gate | Requirement |
|---|---|
| Contrast | Text and meaningful labels target at least 4.5:1 contrast against background. |
| Color semantics | Never encode status or category by color alone; add labels, icons, patterns, or position. |
| Reading order | PowerPoint object order must follow the spoken / visual scan order. |
| Alt text | Meaningful images require alt text after export; decorative images may be marked decorative. |
| Font safety | Font stacks must end with PPT-safe installed families as defined in `strategist.md §g`. |

**Human release check**: Open the exported PPTX and run PowerPoint Accessibility Checker. Fix high-impact issues before delivery; record residual issues when they cannot be fixed inside SVG generation.

---

## 6. Gate Checklist

### 6.1 Pre-generation Gate

| Check | Owner |
|---|---|
| Deck thesis, audience, and desired behavior are explicit. | Strategist |
| Every page has one message and a sentence headline. | Strategist |
| Visual role is declared for every non-structural page. | Strategist |
| Density / rhythm are assigned: `anchor`, `dense`, or `breathing`. | Strategist |
| Layout budgets are recorded when the deck is dense or long. | Strategist |

### 6.2 During-generation Gate

| Check | Owner |
|---|---|
| Body text blocks stay within the line / bullet budget. | Executor |
| Each slide has one primary visual focus. | Executor |
| Visuals support the headline directly. | Executor |
| `spec_lock.md` values are used for colors, typography, icons, images, rhythm, layouts, and charts. | Executor |
| Tables beyond the regular budget are simplified, split, or moved to notes / appendix. | Executor |

### 6.3 Post-generation Gate

| Check | Owner |
|---|---|
| `svg_quality_checker.py` returns 0 errors on `svg_output/`. | Executor |
| Critical warnings are fixed or explicitly reported. | Executor |
| Final SVG count equals intended page count. | Executor |
| PPTX export succeeds with native DrawingML editable shapes. | Executor |
| Human 5-second readability check passes: audience can identify the page's main point quickly. | Reviewer |
| Human one-minute check passes: presenter can explain the page without rushing. | Reviewer |
| PowerPoint Accessibility Checker is run manually on the final PPTX. | Reviewer |

---

## 7. Automatic vs Human Checks

| Automatic / scriptable | Human judgment |
|---|---|
| SVG syntax and banned SVG features. | Whether the headline is a meaningful conclusion. |
| viewBox / canvas mismatch. | Whether the page has exactly one message. |
| `spec_lock.md` drift for colors, fonts, icons, and images. | Whether the visual genuinely supports the headline. |
| PPT-safe font tail. | Whether the story sequence feels continuous. |
| Icon library mixing. | Whether the 5-second focus and one-minute explanation checks pass. |
| Basic density counters: cards, bullets, table rows / columns. | Whether simplification removed important meaning. |
| Contrast ratio where foreground / background are programmatically knowable. | Whether complex images and screenshots need alt text or spoken explanation. |
