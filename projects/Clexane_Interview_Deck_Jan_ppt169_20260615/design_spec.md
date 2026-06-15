# Clexane_Interview_Deck_Jan - Design Spec

> Human-readable design narrative — rationale, audience, style, color choices, content outline. Read once by downstream roles for context.
>
> Machine-readable execution contract: `spec_lock.md` (color / typography / icon / image short form). Executor re-reads `spec_lock.md` before every SVG page to resist context-compression drift. Keep both in sync; on divergence, `spec_lock.md` wins.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | Clexane_Interview_Deck_Jan |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 6 slides |
| **Design Style** | A) General Versatile + Corporate Pharma MR Pitch |
| **Target Audience** | Sales Manager at DKSH Thailand — evaluating MR candidate Rattanakorn Rattanaroj (Jan) |
| **Use Case** | Pre-interview pitch deck presented during / ahead of job interview for Clexane® Medical Representative role |
| **Created Date** | 2026-06-15 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 px |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right 60px, top 50px, bottom 40px |
| **Content Area** | 1160×630px (x=60, y=50) |

---

## III. Visual Theme

### Theme Style

- **Style**: Corporate Pharma MR Pitch — clean, high-contrast, DKSH red identity
- **Theme**: Light
- **Tone**: Professional, confident, evidence-based — similar to BI/Sanofi pre-interview materials in DKSH brand language

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | Slide background |
| **Secondary bg** | `#F5F5F5` | Card backgrounds, gray section fills |
| **Primary** | `#AE232F` | DKSH Red — title bars, accent elements, CTA bars |
| **Dark Red** | `#8A1B25` | Deep accent, dark bars, emphasis backgrounds |
| **Light Red** | `#F9E5E7` | Card tints, subtle highlight fills |
| **Body text** | `#1A1A1A` | All primary body copy |
| **Secondary text** | `#555555` | Captions, labels, annotations |
| **Tertiary text** | `#888888` | Footnotes, page numbers |
| **Border/divider** | `#E0E0E0` | Card borders, separator lines |
| **Success** | `#2E7D32` | Positive indicators (Tier A stars) |
| **Warning** | `#C62828` | Issue markers / negative trend |

---

## IV. Typography System

### Font Plan

**Typography direction**: Concord single-family — Arial throughout. User-specified. All text uses Arial, differentiating weight and size only.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | — | `Arial` | `sans-serif` |
| **Body** | — | `Arial` | `sans-serif` |
| **Emphasis** | — | `Arial` | `sans-serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Arial, sans-serif`
- Body: `Arial, sans-serif`
- Emphasis: `Arial, sans-serif` (Bold weight differentiates from body)
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body = 18px (dense content — 6-slide pitch with clinical bullet blocks)

| Purpose | Ratio to body | px |
| ------- | ------------- | -- |
| Cover/hero title | 3-4x | 54-72px |
| Page title | 1.8-2x | 32-36px |
| Subtitle / section label | 1.3-1.5x | 24-27px |
| **Body** | **1x** | **18px** |
| Annotation / caption | 0.75-0.85x | 14-15px |
| Footer / page number | 0.6x | 11-12px |

**Formula rendering policy**: `text-only` — no mathematical formulas; all content is plain clinical terminology.

---

## V. Layout Principles

### Page Structure

- **Header area**: y=0 to y=80 — slide title bar (red background `#AE232F`) with white title text
- **Content area**: y=80 to y=680 — main content (cards, tables, diagrams)
- **Footer area**: y=680 to y=720 — contact / branding strip

### Layout Pattern Library

| Pattern | Pages Used |
| ------- | ---------- |
| **Asymmetric split (4:6)** | Slide 1 (photo+contact left / content blocks right) |
| **Three-column equal** | Slide 2 (MOA / Indications / Differentiators) |
| **Top-bottom split** | Slide 3 (network diagram top / priority table bottom) |
| **Five-step horizontal chevron** | Slide 4 (ADAPT framework) |
| **Symmetric split (5:5) + full-width bar** | Slide 5 (Strengths left / Development right + Why Me bar) |
| **Single column centered** | Slide 6 (closing — breathing) |

### Spacing Specification

| Element | Value |
| ------- | ----- |
| Safe margin from canvas edge | 60px |
| Content block gap | 24px |
| Card padding | 20-24px |
| Card border radius | 10-12px |
| Icon-text gap | 10px |
| Column gap | 28px |

---

## VI. Icon Usage Specification

**Library**: `tabler-filled` — smooth, rounded, medium-weight filled icons. Professional pharma/corporate character.

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Education / academic background | `tabler-filled/school` | P01 |
| Field / clinical experience | `tabler-filled/briefcase` | P01 |
| Passion / motivation | `tabler-filled/heart` | P01 |
| Mechanism / science | `tabler-filled/flask` | P02 |
| Indications / clinical use | `tabler-filled/clipboard-check` | P02 |
| Differentiators / advantage | `tabler-filled/shield-check` | P02 |
| Hospital / institution | `tabler-filled/hospital-circle` | P03 |
| Physician / HCP contact | `tabler-filled/user` | P03 |
| Priority / tier marker | `tabler-filled/star` | P03 |
| Assess (open questions) | `tabler-filled/search` | P04 |
| Discover (surface gap) | `tabler-filled/message` | P04 |
| Activate (present solution) | `tabler-filled/medical-cross` | P04 |
| Project (paint outcomes) | `tabler-filled/eye` | P04 |
| Tie Down (commitment) | `tabler-filled/circle-check` | P04 |
| Strength / achievement | `tabler-filled/award` | P05 |
| Development / growth | `tabler-filled/book` | P05 |
| Closing / celebration | `tabler-filled/trophy` | P06 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P01 | labeled_card | `templates/charts/labeled_card.svg` | "Pick for 3-4 parallel aspects of one subject with per-aspect titles + short body (self-introduction, four-pillar overview, characteristic contrast)" | Three content blocks (Pharma Background / Field Experience / Why DKSH) in right column of intro slide |
| P02 | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST" | Three equal pillars: MOA, Key Indications, Key Differentiators |
| P03 | basic_table | `templates/charts/basic_table.svg` | "Pick for plain tabular text/number grid, 3-8 columns. Skip if cells need visual bars (use consulting_table) or qualitative scores (use harvey_balls_table)" | Physician priority table (Specialty / Role / Priority) in bottom half of slide |
| P04 | chevron_process | `templates/charts/chevron_process.svg` | "Pick for 3-6 phase methodology with chunky arrow-chain progression and deliverables per phase. Skip for <=2 phases or no deliverables." | 5-step ADAPT framework: Assess → Discover → Activate → Project → Tie Down |
| P05 | pros_cons_chart | `templates/charts/pros_cons_chart.svg` | "Pick for bilateral pros/cons list, 2-5 items per side. Skip for full feature comparison (use comparison_table) or numerical scoring (use dumbbell_chart)." | 3 Strengths (left) vs 2 Development Areas (right), bilateral layout |

**Runners-up considered**:

- `icon_grid` | rejected for P01: icon_grid emphasizes 4-9 flat feature tiles with minimal prose; P01 needs 3 substantive narrative blocks with multi-line body text for the biographical pitch — labeled_card provides title + body depth per block
- `hub_spoke` | rejected for P01: hub_spoke requires one central concept radiating to surrounding nodes; P01 is a sequential left-to-right narrative pitch, not a hub-and-spokes topology
- `icon_grid` | rejected for P02: icon_grid is a feature grid without the title + bullet depth each column needs for the clinical detail (MOA sub-bullets, specific LMWH mechanism)
- `comparison_columns` | rejected for P02: comparison_columns is a pricing/service tier marketing layout; P02 is educational clinical content in parallel columns, not a tier comparison
- `top_down_tree` | rejected for P03: top_down_tree could serve the hospital network diagram in the upper half, but the physician priority table (primary data deliverable) is tabular with Tier A/B ratings, not a tree; basic_table is the right anchor
- `feature_matrix_table` | rejected for P03: feature_matrix_table requires binary checkmarks across products — P03's physician table uses star-rating priority tiers (Tier A / Tier B), not feature checkmarks
- `numbered_steps` | rejected for P04: numbered_steps uses flat horizontal numeric labels without the chunky arrow-chain visual weight ADAPT needs; chevron_process provides the arrow-chain progression and per-phase body text depth
- `pipeline_with_stages` | rejected for P04: pipeline_with_stages requires per-stage output artifacts; ADAPT steps produce behavioral commitments, not data artifacts — chevron_process maps better to the methodology framing
- `vertical_list` | rejected for P05: vertical_list is a single numbered column of key points; P05 is explicitly bilateral (strengths left / development right) — pros_cons_chart provides the two-side structure
- `comparison_columns` | rejected for P05: comparison_columns is a marketing tier layout; P05 is a self-assessment bilateral, not pricing tiers

*Note: fewer than 3 viz pages use the same primary template, but all 5 content pages have a template match above. Runners-up drawn from real second-best matches per page.*

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference |
| -------- | ---------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- |
| photo_jan.png | 260×310 | 0.84 | Profile photo placeholder — left column of Slide 1 | Portrait | #2 left-third image + right text body | placeholder | Placeholder | Photo of Rattanakorn Rattanaroj (Jan) — rounded rectangle placeholder labeled [Photo: Jan]; user to supply actual photo |

**Image-as-canvas coverage note**: Deck has only 1 image-bearing page (P01, placeholder portrait). Fewer than 4 image-bearing pages, so the ≥1 `#38–#46` coverage requirement does not apply to this deck.

---

## IX. Content Outline

### Part 1: Introduction

#### Slide 01 — Hello, I'm Jan

- **Layout**: Asymmetric two-column (left ~38% / right ~62%). Left column: photo placeholder (rounded rect, red border) + name + contact info. Right column: red header bar + 3 labeled content blocks.
- **Title**: Hello, I'm Jan
- **Subtitle**: MR Candidate · DKSH Thailand · Clexane®
- **Core message**: Jan brings a rare combination of Pharm.D. scientific depth and real solo MR field experience — he is not a fresh graduate, he is an MR who happens to hold a doctorate.
- **Visualization**: labeled_card (see §VII P01)
- **Content**:
  - **Left column**:
    - Rounded rectangle placeholder (260×310px, `#F9E5E7` fill, `#AE232F` 2px border, rx=12), centered, labeled `[Photo: Jan]` in gray italic
    - Name: Rattanakorn Rattanaroj (Jan) — 20px Bold
    - Contact: Rattanaroj.jan@gmail.com · 080-045-0821 — 14px
  - **Right column — Block 1** (icon: school) **Pharma Background**:
    - Pharm.D. (GPA 3.50) — Srinakarinwirot University
    - Deep knowledge of drug mechanisms, pharmacokinetics, and clinical data — ready to communicate science to physicians.
  - **Right column — Block 2** (icon: briefcase) **Real Field Experience**:
    - MR Intern at Roche Thailand — solo physician visits across Ramathibodi, Bhumibol Adulyadej &amp; EENT Hospital
    - Planned call cycles and managed physician follow-ups independently.
  - **Right column — Block 3** (icon: heart) **Why DKSH / Clexane?**:
    - Clexane has strong clinical evidence in acute care settings.
    - I want to be the MR who translates that evidence into real prescribing change at PMK and beyond.
- **Footer**: Rattanakorn Rattanaroj | Rattanaroj.jan@gmail.com | 080-045-0821

---

#### Slide 02 — Clexane® Product Knowledge

- **Layout**: Three-column equal card layout. Red header bar at top with slide title. Three white cards below side by side.
- **Title**: Clexane® (Enoxaparin) — What You Need to Know
- **Core message**: Clexane is a predictable, evidence-backed LMWH that outperforms UFH on convenience and DOACs on acute/renal safety — Jan knows exactly why it belongs in every Orthopedic and Cardiology protocol.
- **Visualization**: vertical_pillars (see §VII P02)
- **Content**:
  - **Column 1** (icon: flask) **Mechanism of Action (MOA)**:
    - LMWH → Binds Antithrombin III
    - → Inhibits Factor Xa : IIa = 3.5:1
    - → Prevents Fibrin Clot formation
    - SC Bioavailability ~90%
    - No routine aPTT monitoring required
  - **Column 2** (icon: clipboard-check) **Key Indications**:
    - ① DVT Prophylaxis (post-op surgical)
    - ② DVT / PE Treatment
    - ③ ACS — Unstable Angina / NSTEMI
    - ④ Hemodialysis Circuit Protection
    - ⑤ Medical patients (immobile / high-risk)
  - **Column 3** (icon: shield-check) **Key Differentiators**:
    - vs UFH: Predictable PK · SC injection · Lower HIT risk · Longer half-life (4–5 hrs vs 1–2 hrs)
    - vs DOAC: Safe in severe CKD · Reversible with Protamine Sulfate · Ideal for acute &amp; peri-operative settings

---

### Part 2: Territory & Strategy

#### Slide 03 — Territory Plan: PMK &amp; Network

- **Layout**: Top half (~45%) = hospital network diagram (boxes with connectors); Bottom half (~45%) = physician priority table. Red header bar. Small red insight box at bottom right.
- **Title**: Territory Plan — Phramongkutklao &amp; Network Hospitals
- **Core message**: PMK's military patient mix creates concentrated Orthopedic and Cardiology volume; the ward pharmacist is the third Tier-A call that most MRs overlook.
- **Visualization**: basic_table for physician priority (see §VII P03); hospital network is custom SVG boxes with connector arrows
- **Content**:
  - **Top — Hospital Network Diagram**:
    - Center top box (red, bold): ⭐ Phramongkutklao Hospital (PMK) — Primary Anchor
    - Downward arrow → row of three gray boxes: Network Hospital 1 | Network Hospital 2 | Network Hospital 3
    - Connector arrows from PMK box down to each of the three network boxes
  - **Bottom — Physician Priority Table** (5 rows):

    | Specialty | Role in Clexane | Priority |
    |---|---|---|
    | Orthopedic Surgeon | DVT prophylaxis — post Hip/Knee Replacement | ⭐⭐⭐ Tier A |
    | Cardiologist | ACS (NSTEMI), post-PCI anticoagulation | ⭐⭐⭐ Tier A |
    | Ward Pharmacist | Formulary influence &amp; protocol setting | ⭐⭐⭐ Tier A |
    | Internal Medicine | DVT prophylaxis in medical ward patients | ⭐⭐ Tier B |
    | Nephrologist | Hemodialysis circuit anticoagulation | ⭐⭐ Tier B |

  - **Key Insight Box** (red bg, white text, bottom area):
    - PMK = Military Hospital → High volume of post-op patients
    - Orthopedic + Cardiology = Core revenue drivers
    - Ward Pharmacist = Formulary gatekeeper — always call on both MD and PharmD

---

#### Slide 04 — Selling Approach: ADAPT Framework

- **Layout**: Red header bar. Five-step horizontal chevron flow (left → right), each step = colored box. Below: key principle box (white card, red left border).
- **Title**: My Detailing Approach — ADAPT Framework
- **Core message**: Jan's detailing is physician-led, not product-led — ADAPT ensures every call starts with listening and ends with a committed next step.
- **Visualization**: chevron_process (see §VII P04)
- **Content**:
  - **Step 1 — A** (icon: search): **Assess** · Open-ended questions to understand physician's current need
  - **Step 2 — D** (icon: message): **Discover** · Surface the gap or clinical challenge the physician faces
  - **Step 3 — A** (icon: medical-cross): **Activate** · Present Clexane as the targeted solution
  - **Step 4 — P** (icon: eye): **Project** · Paint the picture of outcomes for physician and patient
  - **Step 5 — T** (icon: circle-check): **Tie Down** · Secure a commitment or clear next step
  - **Key Principle Box** (below chevrons):
    - "Ask before you tell — a great MR listens more than they speak."
    - Objection = Opportunity, not a roadblock.
    - Always: Acknowledge → Clarify → Respond → Confirm

---

### Part 3: Self-Assessment &amp; Close

#### Slide 05 — Strengths, Development &amp; Why Me

- **Layout**: Two halves side by side (left ~55% = Strengths, right ~45% = Development Areas) + full-width red bar at bottom = Why Me.
- **Title**: Strengths · Development Areas · Why Choose Me
- **Core message**: Jan's honesty about gaps is itself a strength — he knows where he is and has a plan for the rest.
- **Visualization**: pros_cons_chart adapted (see §VII P05)
- **Content**:
  - **Left — 3 Strengths** (dark card, `#1A1A1A` bg or deep red tint):
    - (icon: award) **① Scientific Communication** — Pharm.D. foundation + Roche field experience → Translate clinical data into physician language
    - (icon: award) **② Observation &amp; Relationship Building** — Quickly learn physician preferences and working styles → Approach at the right time, build long-term trust
    - (icon: award) **③ Adaptability &amp; Initiative** — Solo detailing across 3 major Bangkok hospitals → Adapt strategy to each environment from day one
  - **Right — 2 Development Areas** (neutral gray card):
    - ⚠ **Limited long-term territory experience** → Compensated by strong discipline, preparation, and fast learning curve
    - ⚠ **Developing commercial language** → Actively studying Clexane clinical data and objection handling frameworks
  - **Bottom — Why Me Bar** (full-width, `#AE232F` background, white text):
    - Pharm.D. Science  +  Real MR Field Experience  +  High Preparation  =  Ready to Drive Growth for DKSH

---

#### Slide 06 — Thank You / Closing

- **Layout**: Centered single-column. No header bar — clean breathing page. Centered content with a bottom red tagline bar.
- **Title**: (none — large centered text replaces header)
- **Core message**: Jan closes with confidence and a concrete statement of readiness — not generic gratitude but a commitment to Day 1 action.
- **Content**:
  - Large center text (72px Bold, `#AE232F`): Thank You for This Opportunity
  - Medium text (22px, `#1A1A1A`): I am ready to build physician relationships from Day 1 and drive Clexane growth across the PMK territory.
  - Contact block (18px): Rattanakorn Rattanaroj (Jan) · 📧 Rattanaroj.jan@gmail.com · 📞 080-045-0821
  - Bottom tagline bar (`#AE232F` background, white text): "Science + Field Experience + Dedication → Ready for DKSH"

---

## X. Speaker Notes Requirements

- **Filename**: match SVG name — `01_hello_jan.md`, `02_product_knowledge.md`, `03_territory_plan.md`, `04_adapt_framework.md`, `05_strengths_development.md`, `06_closing.md`
- **Duration**: ~8–12 minutes total (average 2 min per slide)
- **Notes style**: Conversational — spoken English as an MR would speak in an interview
- **Purpose**: Persuade (job interview — convince Sales Manager Jan is the right hire)
- **Structure per note**: Opening hook → Key points → Transition to next slide

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` FORBIDDEN
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`
6. FORBIDDEN: `textPath`, `animate*`, `script`
7. Text characters: write typography and symbols as raw Unicode (em dash —, en dash –, ©, ®, →, etc.); HTML named entities (`&nbsp;`, `&mdash;`, etc.) FORBIDDEN. XML reserved chars in text MUST be escaped as `&amp;` `&lt;` `&gt;` `&quot;` `&apos;`
8. `clipPath` conditionally allowed only on `<image>` elements
9. `marker-start` / `marker-end` allowed for connectors: `<marker>` in `<defs>`, `orient="auto"`, triangle shape

### PPT Compatibility Rules:

- `<g opacity="...">` FORBIDDEN — set opacity on each child element individually
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
