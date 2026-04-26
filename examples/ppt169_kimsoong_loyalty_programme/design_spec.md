# Kimsoong Customer Loyalty Programme - Design Spec

> This document is the human-readable design narrative — rationale, audience, style, color choices, content outline. It is read once by downstream roles for context.
>
> The machine-readable execution contract lives in `spec_lock.md` (short form of color / typography / icon / image decisions). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep the two files in sync; if they diverge, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Kimsoong Customer Loyalty Programme |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 10 |
| **Design Style** | Top Consulting (MBB-level) |
| **Target Audience** | Senior management / board at Kimsoong European HQ |
| **Use Case** | Strategic proposal for customer loyalty programme investment decision |
| **Created Date** | 2026-04-24 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/Right 60px, Top 50px, Bottom 40px |
| **Content Area** | 1160×630 (x=60, y=50, w=1160, h=630) |

---

## III. Visual Theme

### Theme Style

- **Style**: Top Consulting (MBB-level strategic presentation)
- **Theme**: Light theme
- **Tone**: Authoritative, data-driven, professionally restrained, eco-conscious automotive

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | Page background |
| **Secondary bg** | `#F4F6F8` | Card backgrounds, section backgrounds |
| **Primary** | `#1A3A5C` | Titles, key sections, header bars, strategic elements |
| **Accent** | `#E8A838` | Data highlights, key numbers, critical insights |
| **Secondary accent** | `#2D8A4E` | Eco-brand elements, positive indicators, growth metrics |
| **Body text** | `#2C3E50` | Main body text |
| **Secondary text** | `#5D6D7E` | Captions, annotations, supporting text |
| **Tertiary text** | `#95A5A6` | Page numbers, footnotes |
| **Border/divider** | `#D5DDE5` | Card borders, divider lines |
| **Success** | `#27AE60` | Positive indicators, improvement metrics |
| **Warning** | `#E74C3C` | Critical issues, problem areas, negative data |

### Gradient Scheme

```xml
<!-- Header gradient bar (Top Consulting signature) -->
<linearGradient id="headerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#1A3A5C"/>
  <stop offset="100%" stop-color="#2D8A4E"/>
</linearGradient>

<!-- Subtle background accent -->
<radialGradient id="bgDecor" cx="85%" cy="15%" r="40%">
  <stop offset="0%" stop-color="#1A3A5C" stop-opacity="0.05"/>
  <stop offset="100%" stop-color="#1A3A5C" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: International English — clean, authoritative sans-serif for a European audience.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | — | `"Helvetica Neue"`, `Arial` | `sans-serif` |
| **Body** | — | `"Helvetica Neue"`, `Arial` | `sans-serif` |
| **Emphasis** | — | `Georgia`, `"Times New Roman"` | `serif` |
| **Code** | — | `Consolas`, `"Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Helvetica Neue", Arial, sans-serif`
- Body: `"Helvetica Neue", Arial, sans-serif`
- Emphasis: `Georgia, "Times New Roman", serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 18px (dense — consulting analysis with 6+ data points per page)

| Purpose | Ratio | Size @ body=18 | Weight |
| ------- | ----- | -------------- | ------ |
| Cover title | 3x | 54px | Bold |
| Page title | 1.7x | 30px | Bold |
| Hero number | 2x | 36px | Bold |
| Subtitle | 1.3x | 24px | SemiBold |
| **Body** | **1x** | **18px** | Regular |
| Annotation | 0.78x | 14px | Regular |
| Page number | 0.61x | 11px | Regular |

---

## V. Layout Principles

### Page Structure

- **Header area**: y=0 to y=90 — Primary gradient bar (8px) + page title zone
- **Content area**: y=90 to y=680 — Main content (590px height)
- **Footer area**: y=680 to y=720 — Page number, confidential marking

### Top Consulting Signature Elements

- **Gradient top bar**: 8px height, full width, primary-to-secondary-accent gradient
- **Dark takeaway box**: Bottom-left insight box with dark background (#1A3A5C) and white text
- **Conclusion-first titles**: Page titles carry the core insight, not topic labels

### Layout Pattern Library

| Pattern | Used On |
| ------- | ------- |
| Single column centered | P01 Cover, P10 Conclusion |
| Asymmetric split (4:6) | P03 Company Profile (image + text) |
| Four-quadrant dashboard | P04 Customer Demographics |
| Matrix 2×2 | P05 Priorities Gap Analysis |
| Horizontal bar ranking | P06 Root Cause |
| Center-radiating | P07 Strategic Pillars |
| Five-card evaluation | P08 Initiatives |
| Timeline horizontal | P09 Roadmap |

### Spacing Specification

**Universal**:

| Element | Value |
| ------- | ----- |
| Safe margin | 60px |
| Content block gap | 30px |
| Icon-text gap | 10px |

**Card-based layouts**:

| Element | Value |
| ------- | ----- |
| Card gap | 24px |
| Card padding | 24px |
| Card border radius | 10px |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `tabler-filled` (smooth bezier curves — warm, professional, suitable for automotive consulting)
- **Usage method**: `{{icon:tabler-filled/icon-name}}`

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Automotive | `{{icon:tabler-filled/car}}` | P01, P03 |
| Strategic target | `{{icon:tabler-filled/target}}` | P02, P07 |
| Data analysis | `{{icon:tabler-filled/chart-pie}}` | P04 |
| Customer base | `{{icon:tabler-filled/users}}` | P04 |
| After-sales / warranty | `{{icon:tabler-filled/shield-check}}` | P05, P08 |
| Loyalty discount | `{{icon:tabler-filled/discount}}` | P08 |
| Achievement | `{{icon:tabler-filled/trophy}}` | P09 |
| Timeline | `{{icon:tabler-filled/clock}}` | P09 |
| Customer loyalty | `{{icon:tabler-filled/heart}}` | P07, P10 |
| Data insights | `{{icon:tabler-filled/report-analytics}}` | P06 |
| Revenue / cost | `{{icon:tabler-filled/coin}}` | P08 |
| Incentive | `{{icon:tabler-filled/gift}}` | P08 |
| Alert / warning | `{{icon:tabler-filled/alert-triangle}}` | P02, P06 |
| Checkmark | `{{icon:tabler-filled/circle-check}}` | P10 |
| Stars / satisfaction | `{{icon:tabler-filled/star}}` | P05 |
| Sparkle / highlight | `{{icon:tabler-filled/sparkles}}` | P03 |

---

## VII. Visualization Reference List

| Visualization Type | Reference Template | Used In | Purpose |
| ------------------ | ------------------ | ------- | ------- |
| kpi_cards | `templates/charts/kpi_cards.svg` | P02 | Executive summary KPI dashboard |
| donut_chart | `templates/charts/donut_chart.svg` | P04 | Age distribution, income distribution |
| horizontal_bar_chart | `templates/charts/horizontal_bar_chart.svg` | P04 | Occupation distribution |
| matrix_2x2 | `templates/charts/matrix_2x2.svg` | P05 | Priority vs. Performance gap |
| pareto_chart | `templates/charts/pareto_chart.svg` | P06 | Root cause analysis with cumulative line |
| hub_spoke | `templates/charts/hub_spoke.svg` | P07 | Four strategic pillars radiating from core |
| comparison_columns | `templates/charts/comparison_columns.svg` | P08 | Initiative evaluation (impact vs cost) |
| timeline | `templates/charts/timeline.svg` | P09 | Implementation roadmap Q1-Q4 |

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |
| -------- | --------- | ----- | ------- | ---- | ------ | --------------------- |
| cover_bg.jpg | 1920x1080 | 1.78 | P01 Cover background | Background | Pending | Abstract automotive engineering background with flowing aerodynamic curves in deep navy (#1A3A5C) to midnight blue gradient, subtle light particle effects suggesting motion and innovation, clean center-right area for text overlay, premium corporate feel |
| company_profile.jpg | 1920x1080 | 1.78 | P03 Company profile context | Photography | Pending | Modern automotive showroom interior with sleek cars on display, clean minimalist design, natural lighting through large glass windows, European city visible outside, professional corporate atmosphere |
| customer_insight.jpg | 1920x1080 | 1.78 | P04 Customer data page accent | Illustration | Pending | Abstract data visualization illustration showing interconnected human silhouettes forming a network pattern, flat design style in deep blue and amber tones, representing customer demographics and buyer profiling analytics |
| roadmap_bg.jpg | 1920x1080 | 1.78 | P09 Roadmap section accent | Background | Pending | Subtle abstract road pathway stretching into the distance with soft gradient from deep blue (#1A3A5C) to eco green (#2D8A4E), geometric grid overlay suggesting structured planning, clean negative space for content overlay |

---

## IX. Content Outline

### Part 1: Setting the Stage

#### Slide 01 - Cover (anchor)

- **Layout**: Full-bleed background image + centered title with overlay
- **Title**: "Kimsoong Customer Loyalty Programme"
- **Subtitle**: "Strategic Framework for Customer Retention & Growth"
- **Info**: European Headquarters | Strategic Proposal | April 2026
- **Image**: `cover_bg.jpg` — hero / full-bleed intent

#### Slide 02 - The Challenge: A Critical Retention Gap (breathing)

- **Layout**: Single column — three hero KPI cards + takeaway box
- **Title**: "Only 15% of customers return — 78% rate after-sales as Fair or Poor"
- **Visualization**: kpi_cards
- **Content**:
  - KPI 1: 15% repeat buyer rate (vs. industry benchmark ~40%)
  - KPI 2: 78% Fair/Poor after-sales rating
  - KPI 3: 52% lost to competitors
  - Dark takeaway box: "The cost of acquiring a new customer is 5-7x retaining an existing one. With only 15% repeat purchases, Kimsoong is leaving significant lifetime value on the table."

### Part 2: Understanding the Customer

#### Slide 03 - Kimsoong: Market Position & Brand Assets (dense)

- **Layout**: Asymmetric split (4:6) — image left, structured text right
- **Title**: "Strong brand assets provide foundation for loyalty strategy"
- **Image**: `company_profile.jpg` — side-by-side intent
- **Content**:
  - Brand strengths: Reliability reputation, value pricing, eco-conscious image
  - Market position: Lower-end with "extras included" differentiation
  - European footprint: Franchises across most countries (sales + service + used cars)
  - R&D pipeline: Eco-car with alternative power source
  - Takeaway: "Brand equity is high — the gap is in post-purchase experience, not product appeal"

#### Slide 04 - Customer Profile: Who Buys Kimsoong? (dense)

- **Layout**: Four-quadrant dashboard
- **Title**: "Young, employed, middle-income — a segment with high lifetime value potential"
- **Visualization**: donut_chart (age), horizontal_bar_chart (occupation)
- **Image**: `customer_insight.jpg` — accent intent (small, decorative)
- **Content**:
  - Q1: Age — 48% under 30, 27% age 31-40 (75% under 40)
  - Q2: Income — 82% middle income (price-sensitive but stable)
  - Q3: Occupation — 75% employed, 15% self-employed
  - Q4: Interests — Top 3: Eating/drinking, Sport, Travel; #4 Environment (brand-aligned)
  - Gender split: 52M / 48F (near-even)

#### Slide 05 - The Gap: What Customers Want vs. What They Get (dense)

- **Layout**: Matrix 2×2 — importance vs. satisfaction
- **Title**: "After-sales service: high importance, critically low satisfaction"
- **Visualization**: matrix_2x2
- **Content**:
  - X-axis: Customer Priority Ranking (1-7)
  - Y-axis: Satisfaction Level
  - Key insight: After-sales ranks #4 in priorities but only 33% rate it Good or above
  - Economy (#1) and Price (#2) — well-served by Kimsoong's value proposition
  - Reliability (#3) — strong brand perception
  - After-sales (#4) — **critical gap** (red zone)
  - Questionnaire return rate: only 40% — data quality issue

### Part 3: Diagnosis

#### Slide 06 - Why Customers Leave: Root Cause Decomposition (dense)

- **Layout**: Horizontal bar chart (descending) + cumulative percentage line
- **Title**: "78% of customer loss is addressable — competitors and service dominate"
- **Visualization**: pareto_chart
- **Content**:
  - Bought competitor: 52% (largest bar, red)
  - Disappointed with service: 26% (orange)
  - Relocated: 8% (gray — uncontrollable)
  - No longer drive: 5% (gray — uncontrollable)
  - Don't know: 9% (gray — data gap)
  - Cumulative line showing 78% addressable
  - Takeaway box: "78% of churn is within Kimsoong's control. Service improvement and competitive positioning are the two levers."

### Part 4: Strategy & Solutions

#### Slide 07 - Four Pillars of Customer Loyalty Strategy (breathing)

- **Layout**: Center-radiating — core objective surrounded by 4 pillars
- **Title**: "A four-pillar framework to transform customer relationships"
- **Visualization**: hub_spoke
- **Content**:
  - Core: Customer Loyalty Programme
  - Pillar 1: Build long-term relationships → Increase profits
  - Pillar 2: Increase customer loyalty → Boost repeat rate (15% → 30%+)
  - Pillar 3: Accurate buyer profiling → Data-driven decisions
  - Pillar 4: Staff engagement → Service excellence
  - Cost model: 50/50 shared with head office

#### Slide 08 - Five Recommended Initiatives: Impact vs. Cost (dense)

- **Layout**: Five evaluation cards in priority order
- **Title**: "Prioritize service and data — financial incentives follow"
- **Visualization**: comparison_columns
- **Content**:
  - Initiative 1 ⭐: 3-Year Free After-sales Service — Impact: HIGH (directly addresses #1 pain point) / Cost: Medium-High
  - Initiative 2: 20% Loyalty Discount — Impact: HIGH (financial incentive) / Cost: Medium
  - Initiative 3: Enhanced Trade-in Programme — Impact: MEDIUM (reduces switching barrier) / Cost: Low-Medium
  - Initiative 4: Customer Magazine — Impact: LOW-MEDIUM (emotional connection, brand) / Cost: Low
  - Initiative 5: Questionnaire Incentive (Branded Pen) — Impact: MEDIUM (data quality improvement, 40% → 70%) / Cost: Very Low
  - Takeaway: "Lead with service; follow with incentives. The branded pen initiative has the highest ROI for data collection."

### Part 5: Execution

#### Slide 09 - Implementation Roadmap: Phased Rollout (dense)

- **Layout**: Horizontal timeline (Q1-Q4) + KPI tracker cards at bottom
- **Title**: "Quick wins first, then systematic service transformation"
- **Visualization**: timeline
- **Image**: `roadmap_bg.jpg` — atmosphere intent (low opacity background)
- **Content**:
  - Phase 1 (Q1): Quick Wins — Launch Magazine, Deploy Questionnaire Incentive
  - Phase 2 (Q2): Service Uplift — Roll out 3-Year Free After-sales across franchises
  - Phase 3 (Q3): Financial Incentives — Activate 20% Loyalty Discount, Trade-in Programme
  - Phase 4 (Q4): Evaluate & Optimize — Measure KPIs, adjust programme
  - KPI targets: Repeat rate 15% → 30% | Satisfaction (Good+) 33% → 60% | Questionnaire return 40% → 70%

#### Slide 10 - Conclusion: The Loyalty Imperative (anchor)

- **Layout**: Single column centered — key message + three takeaway bullets
- **Title**: "Customer retention is the highest-ROI growth lever for Kimsoong Europe"
- **Content**:
  - Core message: "Transforming 15% repeat buyers into 30%+ is achievable within 12 months with a phased, data-driven loyalty programme"
  - Three imperatives:
    1. Fix after-sales service first — it's the #1 reason customers leave
    2. Build data capability — 40% questionnaire return is a strategic blind spot
    3. Phase financial incentives after service foundation is in place
  - Call to action: "Approve Q1 launch of Phase 1 quick wins"

---

## X. Speaker Notes Requirements

- **File naming**: Match SVG names (e.g., `slide_01_cover.md`)
- **Style**: Formal, conclusion-first, data-referenced
- **Purpose**: Persuade — strategic proposal for investment decision
- **Total duration**: ~20 minutes (2 minutes per slide average)
- **Content**: Script key points, data citations, transition phrases

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

- `<g opacity="...">` FORBIDDEN; set on each child element individually
- Image transparency uses overlay mask layer
- Inline styles only; external CSS and `@font-face` FORBIDDEN
