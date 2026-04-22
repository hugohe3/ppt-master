# Claude Code Auto Mode — Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Claude Code Auto Mode |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | General Versatile — tech-forward, dark theme |
| **Target Audience** | Technical teams / AI safety engineers / developers |
| **Use Case** | Technical sharing, engineering blog presentation |
| **Created Date** | 2026-04-22 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Style**: General Versatile — tech-forward
- **Theme**: Dark theme
- **Tone**: Technical, innovative, security-focused, premium

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0D1117` | Page background — deep space black |
| **Secondary bg** | `#161B22` | Card background, section containers |
| **Card bg** | `#1C2333` | Inner card / elevated surface |
| **Primary** | `#D4A574` | Title decorations, key section accents — warm amber (Anthropic brand resonance) |
| **Accent** | `#60A5FA` | Data highlights, links, tech elements — sky blue |
| **Secondary accent** | `#34D399` | Safety/success indicators — emerald green |
| **Body text** | `#E6EDF3` | Main body text — high-contrast light |
| **Secondary text** | `#8B949E` | Captions, annotations |
| **Tertiary text** | `#6E7681` | Supplementary info, footers |
| **Border/divider** | `#30363D` | Card borders, divider lines |
| **Success** | `#34D399` | Positive indicators |
| **Warning** | `#F97316` | Issue markers, danger highlights |

### Gradient Scheme

```xml
<!-- Title accent gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#D4A574"/>
  <stop offset="100%" stop-color="#60A5FA"/>
</linearGradient>

<!-- Background decorative glow -->
<radialGradient id="bgGlow" cx="75%" cy="25%" r="45%">
  <stop offset="0%" stop-color="#D4A574" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#D4A574" stop-opacity="0"/>
</radialGradient>

<!-- Blue accent glow -->
<radialGradient id="blueGlow" cx="25%" cy="75%" r="40%">
  <stop offset="0%" stop-color="#60A5FA" stop-opacity="0.06"/>
  <stop offset="100%" stop-color="#60A5FA" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Recommended preset**: P5 (English-primary)

| Role | English | Fallback |
| ---- | ------- | -------- |
| **Title** | Arial | Helvetica, sans-serif |
| **Body** | Calibri | Arial, sans-serif |
| **Code** | Consolas | Monaco, monospace |
| **Emphasis** | Arial Black | Arial, sans-serif |

**Font stack**: `"Arial", "Calibri", "Helvetica", sans-serif`

### Font Size Hierarchy

**Baseline**: Body font size = 18px (dense content)

| Purpose | Ratio | Size | Weight |
| ------- | ----- | ---- | ------ |
| Cover title | 3x | 54px | Bold |
| Chapter title | 2.2x | 40px | Bold |
| Content title | 1.7x | 30px | Bold |
| Subtitle | 1.3x | 24px | SemiBold |
| **Body content** | **1x** | **18px** | Regular |
| Annotation | 0.78x | 14px | Regular |
| Page number/date | 0.61x | 11px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 50px — page title + decorative accent line
- **Content area**: 600px — main content zone
- **Footer area**: 70px — source attribution / page number

### Layout Pattern Library

| Pattern | Used In |
| ------- | ------- |
| **Single column centered** | P01 Cover, P10 Closing |
| **Asymmetric split (4:6)** | P04, P06, P07, P09 (image + text) |
| **Three-column cards** | P05 Threat model |
| **Vertical list with icons** | P08 Results |
| **Top-bottom split** | P02 Background, P03 Overview |

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin | 60px |
| Content block gap | 30px |
| Icon-text gap | 12px |

**Card-based layouts**:

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 12px |

---

## VI. Icon Usage Specification

### Source

- **Library**: `chunk` (sharp rectilinear geometry)
- **Usage method**: Placeholder `{{icon:chunk/icon-name}}`

### Icon Inventory

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Shield / security | `{{icon:chunk/shield-check}}` | P03, P05 |
| Terminal / code | `{{icon:chunk/terminal}}` | P01, P02 |
| Eye / observation | `{{icon:chunk/eye}}` | P07 |
| Filter / classification | `{{icon:chunk/filter}}` | P06 |
| Bug / threats | `{{icon:chunk/bug}}` | P05 |
| Lock / permissions | `{{icon:chunk/lock-closed}}` | P02, P06 |
| Layers / tiers | `{{icon:chunk/layers}}` | P06 |
| Chart / metrics | `{{icon:chunk/chart-bar}}` | P08 |
| Checkmark / approved | `{{icon:chunk/circle-checkmark}}` | P08, P10 |
| Robot / AI agent | `{{icon:chunk/robot}}` | P03, P05 |
| Bolt / fast | `{{icon:chunk/bolt}}` | P09 |
| Target / goal | `{{icon:chunk/target}}` | P04, P10 |
| Key / credentials | `{{icon:chunk/key}}` | P05 |
| Arrow trend up | `{{icon:chunk/arrow-trend-up}}` | P08 |
| Code | `{{icon:chunk/code}}` | P07 |
| Eye slash / hidden | `{{icon:chunk/eye-slash}}` | P09 |
| Server | `{{icon:chunk/server}}` | P04 |
| Warning / alert | `{{icon:chunk/gauge-high}}` | P08 |

---

## VII. Visualization Reference List

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| comparison_table | `templates/charts/comparison_table.svg` | P08 — Classifier performance results |
| concentric_circles | `templates/charts/concentric_circles.svg` | P06 — Three-tier permission system |

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Intent | Purpose | Type | Status |
| -------- | ---------- | ----- | ------ | ------- | ---- | ------ |
| image.png | 1920×1920 | 1.00 | Side-by-side | Fig.1: Permission modes tradeoff space | Diagram | Existing |
| image_1.png | 1920×2002 | 0.96 | Side-by-side | Fig.2: System architecture | Diagram | Existing |
| image_2.png | 1920×1679 | 1.14 | Side-by-side | Fig.3: What the classifier sees | Diagram | Existing |
| image_3.png | 1920×1935 | 0.99 | Side-by-side | Fig.4: Two-stage pipeline | Diagram | Existing |

---

## IX. Content Outline

### Part 1: Introduction

#### Slide 01 — Cover

- **Layout**: Single column centered, dark hero with subtle radial glow
- **page_rhythm**: anchor
- **Title**: Claude Code Auto Mode
- **Subtitle**: A Safer Way to Skip Permissions
- **Info**: Anthropic Engineering · Mar 2026

#### Slide 02 — The Problem: Approval Fatigue

- **Layout**: Top-bottom split — headline stat on top, explanation below
- **page_rhythm**: breathing
- **Title**: 93% of Permission Prompts Are Approved
- **Content**:
  - Users approve 93% of prompts → approval fatigue sets in
  - Two existing solutions: sandbox (safe but high-maintenance) or `--dangerously-skip-permissions` (zero maintenance, zero protection)
  - Real incidents: deleting remote branches, uploading auth tokens, production DB migrations

### Part 2: How Auto Mode Works

#### Slide 03 — What Is Auto Mode?

- **Layout**: Top-bottom — headline definition + three key pillars in horizontal blocks
- **page_rhythm**: breathing
- **Title**: Auto Mode: Classifier-Delegated Approvals
- **Content**:
  - Delegates permission decisions to model-based classifiers
  - Middle ground between manual review and no guardrails
  - Goal: catch dangerous actions misaligned with user intent, let the rest run freely

#### Slide 04 — System Architecture

- **Layout**: Asymmetric split (4:6) — image_1.png left, annotated highlights right
- **page_rhythm**: dense
- **Title**: Two Layers of Defense
- **Image**: image_1.png (Fig.2: System architecture)
- **Content**:
  - **Input layer**: Prompt-injection probe scans tool outputs before they enter context
  - **Output layer**: Transcript classifier (Sonnet 4.6) evaluates each action before execution
  - Two-stage filter: fast single-token → chain-of-thought reasoning only if flagged
  - Subagents run the same pipeline recursively

### Part 3: Threat Model & Permissions

#### Slide 05 — Four Threat Categories

- **Layout**: Four cards in 2×2 grid with icons
- **page_rhythm**: dense
- **Title**: Why an Agent Might Take Dangerous Action
- **Content**:
  - {{icon:chunk/robot}} **Overeager behavior** — takes initiative beyond what user would approve
  - {{icon:chunk/bug}} **Honest mistakes** — misunderstands blast radius
  - {{icon:chunk/code}} **Prompt injection** — hijacked by planted instructions
  - {{icon:chunk/key}} **Misalignment** — pursues its own goal (not observed in practice)
  - Real examples: scope escalation, credential exploration, safety-check bypass

#### Slide 06 — Three-Tier Permission System

- **Layout**: Asymmetric split (5:5) — image.png left, tier breakdown right
- **page_rhythm**: dense
- **Title**: How Permission Decisions Work
- **Image**: image.png (Fig.1: Permission modes)
- **Visualization**: concentric_circles (conceptual reference)
- **Content**:
  - **Tier 1**: Built-in safe-tool allowlist + user settings
  - **Tier 2**: In-project file operations (no classifier call)
  - **Tier 3**: Transcript classifier — shell commands, web fetches, external tools

### Part 4: Classifier Deep Dive

#### Slide 07 — What the Classifier Sees

- **Layout**: Asymmetric split (4:6) — image_2.png left, key design decisions right
- **page_rhythm**: dense
- **Title**: Reasoning-Blind by Design
- **Image**: image_2.png (Fig.3: What the classifier sees)
- **Content**:
  - Strips assistant text → agent can't "talk" classifier into bad calls
  - Strips tool results → primary prompt-injection defense
  - Sees only user messages + bare tool call commands
  - Being reasoning-blind is complementary to CoT monitoring

#### Slide 08 — Evaluation Results

- **Layout**: Vertical list — key metrics with visual emphasis
- **page_rhythm**: dense
- **Title**: Performance: The Honest Numbers
- **Visualization**: comparison_table
- **Content**:
  - Three datasets: real traffic (n=10K), real overeager (n=52), synthetic exfil (n=1K)
  - Full pipeline: **0.4% FPR** on real traffic, **17% FNR** on overeager actions, **5.7% FNR** on exfiltration
  - Stage 1 alone: 8.5% FPR, 6.6% FNR overeager, 1.8% FNR exfil
  - 17% FNR — classifier correctly identifies danger but misreads consent signals

### Part 5: Design & Future

#### Slide 09 — Key Design Decisions

- **Layout**: Asymmetric split (4:6) — image_3.png left, design highlights right
- **page_rhythm**: dense
- **Title**: Design Decisions That Matter
- **Image**: image_3.png (Fig.4: Two-stage pipeline)
- **Content**:
  - {{icon:chunk/bolt}} **Two-stage classification**: Stage 1 fast filter (8.5% FPR) → Stage 2 reasoning (0.4% FPR); cache-hit efficiency
  - {{icon:chunk/shield-check}} **Prompt-injection probe**: Two layers compound — must evade both input probe AND transcript classifier
  - {{icon:chunk/target}} **Deny-and-continue**: Blocked actions → agent retries safer approach; 3 consecutive or 20 total denials → escalate to human

#### Slide 10 — Closing

- **Layout**: Single column centered, minimal with key takeaway
- **page_rhythm**: anchor
- **Title**: Substantially Safer Than No Guardrails
- **Content**:
  - Auto mode catches enough dangerous actions to make autonomous operation substantially safer
  - Not a replacement for careful human review on high-stakes infrastructure
  - Expanding overeagerness testset, iterating on safety and cost
  - Source: anthropic.com/engineering/claude-code-auto-mode

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Total duration**: ~15 minutes
- **Notes style**: Technical, conversational
- **Purpose**: Inform & educate

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed per shared-standards.md §1.1

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN; set on each child element individually
- Image transparency uses overlay mask layer
- Inline styles only; external CSS and `@font-face` FORBIDDEN
