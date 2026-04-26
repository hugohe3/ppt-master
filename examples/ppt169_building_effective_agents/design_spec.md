# Building Effective Agents - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | building_effective_agents |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 12 |
| **Design Style** | General Versatile |
| **Target Audience** | Software engineers, AI/ML practitioners, technical leaders building LLM-based applications |
| **Use Case** | Technical talks, team knowledge sharing, developer workshops |
| **Created Date** | 2026-04-24 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 |

---

## III. Visual Theme

### Theme Style

- **Style**: General Versatile
- **Theme**: Dark theme
- **Tone**: Technical, precise, modern engineering — warm-on-dark with Anthropic-inspired coral accents

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#0F1117` | Deep dark canvas |
| **Secondary bg** | `#1A1D27` | Card background, section background |
| **Primary** | `#D4845A` | Anthropic-inspired warm coral — titles, key decorative elements |
| **Accent** | `#5B9BD5` | Cool blue — workflow highlights, links, interactive elements |
| **Secondary accent** | `#E8B87D` | Warm gold — secondary emphasis, gradient transitions |
| **Body text** | `#E8E8EC` | Main body text (light on dark) |
| **Secondary text** | `#9CA3AF` | Captions, annotations |
| **Tertiary text** | `#6B7280` | Supplementary info, footers |
| **Border/divider** | `#2D3348` | Card borders, divider lines |
| **Success** | `#4ADE80` | Positive indicators |
| **Warning** | `#F87171` | Cautions, blockers |

### Gradient Scheme

```xml
<!-- Title accent gradient -->
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#D4845A"/>
  <stop offset="100%" stop-color="#E8B87D"/>
</linearGradient>

<!-- Background decorative gradient -->
<radialGradient id="bgDecor" cx="85%" cy="15%" r="45%">
  <stop offset="0%" stop-color="#D4845A" stop-opacity="0.08"/>
  <stop offset="100%" stop-color="#D4845A" stop-opacity="0"/>
</radialGradient>

<!-- Card subtle glow -->
<radialGradient id="cardGlow" cx="50%" cy="0%" r="80%">
  <stop offset="0%" stop-color="#5B9BD5" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#5B9BD5" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: Tech / developer — clean, modern, Latin-primary for English engineering content.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | — | `"Helvetica Neue", Arial` | `sans-serif` |
| **Body** | — | `"Helvetica Neue", Arial` | `sans-serif` |
| **Emphasis** | — | `"Helvetica Neue", Arial` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Helvetica Neue", Arial, sans-serif`
- Body: `"Helvetica Neue", Arial, sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 18px (dense — multiple technical points per page, architectural diagrams)

| Purpose | Ratio to body | Actual Size | Weight |
| ------- | ------------- | ----------- | ------ |
| Cover title | 3.3x | 60px | Bold |
| Page title | 1.78x | 32px | Bold |
| Subtitle | 1.33x | 24px | SemiBold |
| **Body content** | **1x** | **18px** | Regular |
| Annotation / caption | 0.78x | 14px | Regular |
| Page number / footnote | 0.56x | 10px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: 50px top margin; page title zone with coral accent bar (4px wide, 40px tall, left-aligned)
- **Content area**: ~560px height; flexible layout per page rhythm
- **Footer area**: 40px bottom zone; page number right-aligned, subtle source attribution left-aligned

### Layout Pattern Library

The deck uses a variety of patterns to avoid the "every page is a card grid" monotony:

- **Cover**: Full-bleed dark background + centered title with gradient accent
- **Concept pages** (breathing): Asymmetric split with hero diagram + key text; generous whitespace
- **Pattern pages** (dense): Top-bottom split — ultra-wide workflow diagram above, structured content below
- **Summary pages** (anchor): Single column centered with key principles

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin from canvas edge | 60px left/right, 50px top/bottom |
| Content block gap | 30px |
| Icon-text gap | 12px |

**Card-based layouts** (dense pages):

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 12px |
| Card border | 1px solid #2D3348 |
| Card background | #1A1D27 |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `chunk` — sharp, rectilinear geometry matching the precise engineering tone
- **Usage method**: Placeholder format `{{icon:chunk/icon-name}}`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Agent/Robot | `{{icon:chunk/robot}}` | P01, P10 |
| Code | `{{icon:chunk/code}}` | P03, P11 |
| Lightbulb / Idea | `{{icon:chunk/lightbulb}}` | P02, P12 |
| Layers / Building blocks | `{{icon:chunk/layers}}` | P04 |
| Arrow chain | `{{icon:chunk/arrow-right}}` | P05 |
| Route / Routing | `{{icon:chunk/route}}` | P06 |
| Grid / Parallelization | `{{icon:chunk/grid}}` | P07 |
| Cube / Orchestrator | `{{icon:chunk/cube}}` | P08 |
| Loop / Evaluator | `{{icon:chunk/arrows-repeat}}` | P09 |
| Shield / Safety | `{{icon:chunk/shield-check}}` | P10 |
| Toolbox / Tools | `{{icon:chunk/toolbox}}` | P11 |
| Target | `{{icon:chunk/target}}` | P12 |
| Badge check | `{{icon:chunk/badge-check}}` | P12 |
| Terminal | `{{icon:chunk/terminal}}` | P03 |
| Cog / Settings | `{{icon:chunk/cog}}` | P08 |
| Share/Network | `{{icon:chunk/share-nodes}}` | P04 |
| Eye | `{{icon:chunk/eye}}` | P09 |
| Book | `{{icon:chunk/book-open}}` | P11 |
| Microchip | `{{icon:chunk/microchip}}` | P04 |
| Server | `{{icon:chunk/server}}` | P08 |
| Star | `{{icon:chunk/star}}` | P12 |
| Checkmark | `{{icon:chunk/checkmark}}` | P12 |
| Link | `{{icon:chunk/link}}` | P05 |

---

## VII. Visualization Reference List

No additional chart templates needed — the article's 8 architectural diagrams (provided as existing images) serve as the primary visualizations. Each workflow pattern page features its corresponding diagram.

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Status | Narrative Intent |
| -------- | ---------- | ----- | ------- | ---- | ------ | ---------------- |
| image.png | 2401×1000 | 2.40 | The augmented LLM — foundational building block diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_1.png | 2401×1000 | 2.40 | Prompt chaining workflow diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_2.png | 2401×1000 | 2.40 | Routing workflow diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_3.png | 2401×1000 | 2.40 | Parallelization workflow diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_4.png | 2401×1000 | 2.40 | Orchestrator-workers workflow diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_5.png | 2401×1000 | 2.40 | Evaluator-optimizer workflow diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_6.png | 2401×1000 | 2.40 | Autonomous agent loop diagram | Diagram | Existing | Side-by-side (top-bottom split, ultra-wide) |
| image_7.png | 2400×1666 | 1.44 | High-level coding agent flow | Diagram | Existing | Side-by-side (left-right split, standard landscape) |

---

## IX. Content Outline

### Part 1: Introduction

#### Slide 01 — Cover (P01)

- **Layout**: Full-bleed dark background, centered title block, coral accent line, subtle radial glow
- **Title**: Building Effective Agents
- **Subtitle**: Simple, composable patterns for LLM-based agentic systems
- **Info**: Anthropic Engineering · December 2024

#### Slide 02 — What Are Agents? (P02)

- **Layout**: Breathing — asymmetric split, left text block (60%) with key distinction, right visual accent
- **Title**: What Are Agents?
- **Content**:
  - **Workflows**: LLMs + tools orchestrated through predefined code paths
  - **Agents**: LLMs dynamically direct their own processes and tool usage
  - The key architectural distinction: orchestration vs. autonomy
  - All variations are "agentic systems" — the spectrum matters more than the label

### Part 2: Foundations

#### Slide 03 — When to Use Agents (P03)

- **Layout**: Dense — two-column with decision guidance
- **Title**: When (and When Not) to Use Agents
- **Content**:
  - Start with the simplest solution — single LLM calls with retrieval often suffice
  - Agentic systems trade latency and cost for better task performance
  - **Workflows**: Predictability and consistency for well-defined tasks
  - **Agents**: Flexibility and model-driven decisions at scale
  - Framework advice: start with LLM APIs directly; understand what's under the hood

#### Slide 04 — The Augmented LLM (P04)

- **Layout**: Breathing — top-bottom split; ultra-wide diagram above, key text below
- **Title**: Building Block: The Augmented LLM
- **Image**: image.png (top, full-width)
- **Content**:
  - The foundational building block: LLM + retrieval + tools + memory
  - Models actively generate search queries, select tools, determine what to retain
  - Two key implementation aspects: tailor capabilities to your use case; ensure well-documented interfaces
  - Model Context Protocol (MCP) for third-party tool integration

### Part 3: Workflow Patterns

#### Slide 05 — Prompt Chaining (P05)

- **Layout**: Dense — top-bottom split; diagram above, structured content below
- **Title**: Workflow: Prompt Chaining
- **Image**: image_1.png (top, full-width)
- **Content**:
  - Decompose task into sequential steps; each LLM call processes previous output
  - Add programmatic "gate" checks at intermediate steps
  - **When to use**: Tasks cleanly decomposed into fixed subtasks; trade latency for accuracy
  - **Examples**: Generate copy → translate; Write outline → check criteria → write document

#### Slide 06 — Routing (P06)

- **Layout**: Dense — top-bottom split; diagram above, structured content below
- **Title**: Workflow: Routing
- **Image**: image_2.png (top, full-width)
- **Content**:
  - Classify input → direct to specialized followup task
  - Separation of concerns; more specialized prompts
  - **When to use**: Distinct categories better handled separately; accurate classification possible
  - **Examples**: Customer service query routing; Model selection by difficulty (Haiku vs Sonnet)

#### Slide 07 — Parallelization (P07)

- **Layout**: Dense — top-bottom split; diagram above, two-column content below (Sectioning | Voting)
- **Title**: Workflow: Parallelization
- **Image**: image_3.png (top, full-width)
- **Content**:
  - **Sectioning**: Break task into independent subtasks run simultaneously
  - **Voting**: Run same task multiple times for diverse outputs
  - **When to use**: Subtasks parallelizable for speed; multiple perspectives needed
  - **Examples**: Guardrails + response in parallel; Code vulnerability multi-prompt review

#### Slide 08 — Orchestrator-Workers (P08)

- **Layout**: Dense — top-bottom split; diagram above, structured content below
- **Title**: Workflow: Orchestrator-Workers
- **Image**: image_4.png (top, full-width)
- **Content**:
  - Central LLM dynamically breaks down tasks, delegates to workers, synthesizes results
  - Key difference from parallelization: subtasks are not pre-defined but determined dynamically
  - **When to use**: Complex tasks with unpredictable subtasks
  - **Examples**: Multi-file code changes; Multi-source search and analysis

#### Slide 09 — Evaluator-Optimizer (P09)

- **Layout**: Dense — top-bottom split; diagram above, structured content below
- **Title**: Workflow: Evaluator-Optimizer
- **Image**: image_5.png (top, full-width)
- **Content**:
  - One LLM generates; another evaluates and provides feedback in a loop
  - **When to use**: Clear evaluation criteria; iterative refinement adds measurable value
  - Two signs of good fit: human feedback demonstrably improves responses; LLM can provide such feedback
  - **Examples**: Literary translation refinement; Multi-round search with evaluator-driven decisions

### Part 4: Autonomous Agents

#### Slide 10 — Agents (P10)

- **Layout**: Breathing — hero concept; diagram centered, key capabilities floating
- **Title**: Agents: Autonomous LLM Systems
- **Image**: image_6.png (centered, prominent)
- **Content**:
  - Emerging as LLMs mature: complex inputs, reasoning, reliable tool use, error recovery
  - Plan and operate independently; return to human for judgement at checkpoints
  - Ground truth from environment at each step (tool results, code execution)
  - Implementation is often straightforward: LLMs using tools in a loop
  - Higher costs + compounding errors → extensive testing + guardrails required

#### Slide 11 — Agents in Practice (P11)

- **Layout**: Dense — left-right split; coding agent diagram on right, two application areas on left
- **Title**: Agents in Practice
- **Image**: image_7.png (right side, standard landscape)
- **Content**:
  - **Customer Support**: Natural conversation + tool access + programmatic actions; measurable success via resolutions
  - **Coding Agents**: Verifiable via automated tests; iterate using test feedback; well-defined problem space
  - SWE-bench Verified: solving real GitHub issues from PR descriptions alone
  - Tool engineering insight: spent more time optimizing tools than prompts

### Part 5: Conclusion

#### Slide 12 — Summary & Key Principles (P12)

- **Layout**: Anchor — single column centered; three principle cards with icons
- **Title**: Three Core Principles
- **Content**:
  - ① **Simplicity** — Maintain simplicity in your agent's design
  - ② **Transparency** — Explicitly show the agent's planning steps
  - ③ **ACI Design** — Craft your agent-computer interface through thorough tool documentation and testing
  - Start simple → optimize with evaluation → add agentic systems only when simpler solutions fall short
  - Build the *right* system, not the most sophisticated one

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Content structure**: Each note includes key talking points, transition phrases, and timing guidance
- **Style**: Conversational technical — accessible but authoritative
- **Purpose**: Inform and educate
- **Duration**: ~20 minutes total (roughly 1.5-2 min per slide)

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. `marker-start` / `marker-end` conditionally allowed per shared-standards.md §1.1
8. `clipPath` conditionally allowed only on `<image>` elements per shared-standards.md §1.2

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN (group opacity); set on each child element individually
- Image transparency uses overlay mask layer
- Inline styles only; external CSS and `@font-face` FORBIDDEN
