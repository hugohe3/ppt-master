# attention_is_all_you_need — Design Spec

> Paper-deep-read deck for the seminal Transformer paper (Vaswani et al., 2017). Pipeline output of PPT Master; truth-of-execution lives in `spec_lock.md`.

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | attention_is_all_you_need |
| **Canvas Format** | PPT 16:9 (1280×720) |
| **Page Count** | 16 |
| **Design Style** | B) General Consulting + academic minimalist tech (blueprint × cool-corporate) |
| **Target Audience** | AI / NLP engineers, ML graduate students, paper-reading-group members |
| **Use Case** | Paper deep-read / lab seminar / engineering onboarding to Transformer |
| **Created Date** | 2026-05-24 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280×720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | Left/right 60px, top/bottom 50px |
| **Content Area** | 1160×620 inside margins |

---

## III. Visual Theme

### Theme Style

- **Style**: General Consulting + academic minimalist tech (paper-precise, blueprint feel)
- **Theme**: Light theme
- **Tone**: Restrained, analytical, engineering-precise; reads like a Distill.pub article or Anthropic system schematic

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | Page background |
| **Secondary bg** | `#F5F7FA` | Card / region background |
| **Primary** | `#1A365D` | Title, schematic lines, primary box stroke |
| **Accent** | `#3182CE` | Key data, highlighted path, focus elements |
| **Secondary accent** | `#63B3ED` | Gradient transitions, secondary emphasis |
| **Body text** | `#1A202C` | Main body text |
| **Secondary text** | `#4A5568` | Captions, annotations |
| **Tertiary text** | `#A0AEC0` | Page numbers, footnotes |
| **Border/divider** | `#E2E8F0` | Card borders, divider lines |
| **Success** | `#2F855A` | Positive trend (BLEU improvement) |
| **Warning** | `#C53030` | Negative trend, ablation degradation |

### AI Image Strategy

- **Image Rendering**: blueprint
- **Image Palette**: cool-corporate

> Every AI image in this deck shares blueprint × cool-corporate. The rendering carries technical-schematic feel (crisp lines, near-monochrome, optional subtle grid); the palette carries restrained-corporate proportion (off-white field dominant, navy as main, accent blue under 10-15%). Cross-check: blueprint × cool-corporate is ✓✓ in the compatibility matrix.

### Gradient Scheme

```xml
<linearGradient id="titleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#1A365D"/>
  <stop offset="100%" stop-color="#3182CE"/>
</linearGradient>

<linearGradient id="scrimBottom" x1="0%" y1="0%" x2="0%" y2="100%">
  <stop offset="0%" stop-color="#1A365D" stop-opacity="0"/>
  <stop offset="100%" stop-color="#1A365D" stop-opacity="0.7"/>
</linearGradient>

<radialGradient id="bgDecor" cx="80%" cy="20%" r="50%">
  <stop offset="0%" stop-color="#3182CE" stop-opacity="0.15"/>
  <stop offset="100%" stop-color="#3182CE" stop-opacity="0"/>
</radialGradient>
```

---

## IV. Typography System

**Typography direction**: academic serif title + cross-platform sans body — Latin-led so Georgia carries the paper-essay tone in titles while Microsoft YaHei renders any CJK glyphs without fallback.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Georgia` | `serif` |
| **Body** | `"Microsoft YaHei", "PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | `"Microsoft YaHei"` | `Georgia` | `serif` |
| **Code** | — | `Consolas, "Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `Georgia, "Microsoft YaHei", serif`
- Body: `Arial, "Microsoft YaHei", "PingFang SC", sans-serif`
- Emphasis: `Georgia, "Microsoft YaHei", serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = **20**px (medium-dense — paper text + data + diagram annotations).

| Purpose | Ratio to body | This deck @ body=20 | Weight |
| ------- | ------------- | ------------------- | ------ |
| Cover title (hero headline) | 2.5-5x | 64px | Bold |
| Chapter / section opener | 2-2.5x | 44px | Bold |
| Page title | 1.5-2x | 36px | Bold |
| Hero number (KPI) | 1.5-2x | 40px | Bold |
| Subtitle | 1.2-1.5x | 26px | SemiBold |
| **Body content** | **1x** | **20px** | Regular |
| Annotation / caption | 0.7-0.85x | 14px | Regular |
| Page number / footnote | 0.5-0.65x | 11px | Regular |

### Formula Rendering Policy

- **Policy**: `mixed` — render formula-worthy block expressions to PNG; keep inline math (`d_model=512`, `O(n)`, single Greek letters) as editable text.
- **Rendered formulas** (3): Scaled Dot-Product Attention (P07), Multi-Head Attention (P08), Positional Encoding (P11). Manifest at `images/formula_manifest.json`; rendered via codecogs provider, transparent, color `#1A365D`.

---

## V. Layout Principles

### Page Structure

- **Header area**: top 60-100px — page title + thin divider rule in `#3182CE`
- **Content area**: 500-560px height — flexible per page rhythm
- **Footer area**: bottom 40px — page number + project tag in tertiary text

### Layout Pattern Library (combine or break as content demands)

| Pattern | Suitable Scenarios |
| ------- | ----------------- |
| **Single column centered** | P01 cover, P16 closing |
| **Asymmetric split (3:7 / 2:8)** | P05/P07/P08 figure-dominant pages |
| **Symmetric split (5:5)** | P06 Encoder vs Decoder |
| **Top-bottom split** | P02 KPI hero + sub-detail; P03 hero image + caption row |
| **Three/four column cards** | P04 limitations, P09 three attention uses, P13 training KPIs |
| **Full-bleed + floating text** | P01, P03, P11, P16 hero pages |
| **Figure-text overlap** | P05 annotated architecture diagram |
| **Centered formula + caption** | P07, P08, P11 formula blocks |
| **Negative-space-driven** | P11 positional encoding breathing page |

### Spacing Specification

**Universal**:

| Element | Range | This deck |
| ------- | ----- | --------- |
| Safe margin from canvas edge | 40-60px | 60px |
| Content block gap | 24-40px | 28px |
| Icon-text gap | 8-16px | 12px |

**Card-based** (P02, P04, P09, P13, P15):

| Element | Range | This deck |
| ------- | ----- | --------- |
| Card gap | 20-32px | 24px |
| Card padding | 20-32px | 24px |
| Card border radius | 8-16px | 12px |
| Three-column card width | 360-380px | 360px |
| Four-column card width | — | 268px |
| Single-row card height | 530-600px | 540px |

---

## VI. Icon Usage Specification

### Source

- **Library**: `tabler-outline` (stroke-style, weight 2px, screen-clear)
- **Stroke width**: 2 px (deck-wide lock)

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Trophy / SOTA result | `tabler-outline/trophy` | P02, P14 |
| Speed / training time | `tabler-outline/bolt` | P02, P13 |
| Layers / stack | `tabler-outline/stack-2` | P02, P06 |
| Brain / model | `tabler-outline/brain` | P02, P16 |
| Refresh / recurrence | `tabler-outline/refresh` | P03, P04 |
| Arrows-right (sequence) | `tabler-outline/arrow-right` | P03, P09 |
| Lock / constraint | `tabler-outline/lock` | P04 |
| Hourglass / sequential bottleneck | `tabler-outline/hourglass` | P04 |
| Box / module | `tabler-outline/box` | P06, P10 |
| Eye / attention | `tabler-outline/eye` | P07, P09 |
| Grid / multi-head | `tabler-outline/grid-dots` | P08 |
| Wave / sinusoid | `tabler-outline/wave-sine` | P11 |
| Chart bar | `tabler-outline/chart-bar` | P14, P15 |
| GPU / hardware | `tabler-outline/cpu` | P13 |
| Settings / hyperparams | `tabler-outline/settings` | P13, P15 |
| Tree / family of descendants | `tabler-outline/binary-tree` | P16 |

---

## VII. Visualization Reference List

Catalog read: 71 templates

| Page | Template | Path | Summary-quote (verbatim from `charts_index.json`) | Usage |
| ---- | -------- | ---- | ------------------------------------------------- | ----- |
| P02  | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline, quarterly recap, results-at-a-glance. Skip if metrics have target baselines (use bullet_chart) or single hero number (use gauge_chart)." | Four headline metrics: 28.4 BLEU EN-DE, 41.8 BLEU EN-FR, 3.5 days on 8 GPUs, no recurrence/convolution |
| P04  | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic/Social/Technological), four-pillar strategy overview, side-by-side independent categories. Skip for 2×2 quadrant (use quadrant_text_bullets), pricing tiers (use comparison_columns), or 2×2 parallel aspects (use labeled_card)." | Three RNN/CNN limitations side-by-side: sequential bottleneck / long-range path length / parallelization ceiling |
| P06  | comparison_columns | `templates/charts/comparison_columns.svg` | "Pick for 2-4 pricing/service tier cards in side-by-side columns (marketing layout). Skip for dense feature comparison (use comparison_table)." | Encoder stack vs Decoder stack — sub-layers, masking, residual+LN, output dim |
| P09  | vertical_pillars | `templates/charts/vertical_pillars.svg` | "Pick for 1×3 / 1×4 / 1×5 vertical column layout where each pillar = one independent category with title + bullets — PEST (Political/Economic/Social/Technological), four-pillar strategy overview, side-by-side independent categories. Skip for 2×2 quadrant (use quadrant_text_bullets), pricing tiers (use comparison_columns), or 2×2 parallel aspects (use labeled_card)." | Three places attention is used: encoder self-attn / decoder masked self-attn / encoder-decoder cross-attn |
| P10  | module_composition | `templates/charts/module_composition.svg` | "Pick for one parent container wrapping 3-N child module cards, each = title + 2-3 bullets — fits 'Feature X contains 3 parts, each with its own description'. Skip if source has only labels without descriptions (use numbered_steps or icon_grid)." | Sub-layer wrap: position-wise FFN + residual connection + layer normalization, all inside one Encoder/Decoder layer block |
| P12  | basic_table | `templates/charts/basic_table.svg` | "Pick for plain tabular text/number grid, 3-8 columns. Skip if cells need visual bars (use consulting_table) or qualitative scores (use harvey_balls_table)." | Table 1: Per-layer complexity / sequential ops / max path length across Self-Attn, Recurrent, Convolutional, Self-Attn(restricted) |
| P13  | kpi_cards | `templates/charts/kpi_cards.svg` | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline, quarterly recap, results-at-a-glance. Skip if metrics have target baselines (use bullet_chart) or single hero number (use gauge_chart)." | Training config dashboard: 8× P100 GPUs / 12 h base, 3.5 d big / batch 25k tokens / Adam β=(0.9, 0.98) |
| P14  | basic_table | `templates/charts/basic_table.svg` | "Pick for plain tabular text/number grid, 3-8 columns. Skip if cells need visual bars (use consulting_table) or qualitative scores (use harvey_balls_table)." | Table 2: BLEU on WMT'14 EN-DE / EN-FR vs prior SOTA, with training-cost FLOPs column |
| P15  | vertical_list | `templates/charts/vertical_list.svg` | "Pick for 3-6 numbered key points each with a short description — design principles, core tenets, action items, key takeaways, recommendations, executive summary points. Skip for icon-style cards (use icon_grid) or sequential steps (use numbered_steps)." | Table 3 ablation takeaways: head count sweet-spot, key/value dim, dropout, label smoothing |

**Runners-up considered**:

- `quadrant_text_bullets` | rejected for P04: limitations are three parallel side-by-side categories, no 2×2 framework
- `comparison_table` | rejected for P12: only 4 rows + 4 columns, no checkmark / dense matrix needed — `basic_table` is the simpler fit
- `gauge_chart` | rejected for P02: four parallel headline metrics, not one hero goal achievement
- `numbered_steps` | rejected for P15: ablation findings are independent takeaways, not sequential

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | ---------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| cover_bg.png | 1280×720 | 1.78 | P01 cover hero — abstract Transformer blueprint atmosphere | Background | #1 full-bleed background with floating title + #29 two-stop scrim + #38 background image + annotation cards with bezier leader lines | ai | Pending | Abstract technical-blueprint atmosphere suggesting a sequence-to-sequence neural network rebuilt around attention; six labeled rectangular module blocks arranged in two stacked rows on a near-white background, connected by thin precise lines with small arrow heads; a subtle grid pattern at 6% opacity reinforces the schematic feel; the left half is the deck's calm region reserved for a deep-navy title overlay; the right half holds the schematic; one rectangle is highlighted with accent stroke, suggesting the "self-attention" focal block; no embedded text, no labels, no equations, no numbers — every label will be overlaid as SVG text; reads as the title plate of a systems-design briefing document | none | hero_page |
| sequence_evolution.png | 1280×720 | 1.78 | P03 hero — RNN/CNN/Self-Attention comparison as three schematic motifs, each motif carries its panel label inside the image | Diagram | #44 background image + native network/architecture diagram + #29 two-stop scrim | ai | Pending | Three side-by-side schematic motifs reading left to right as a quiet evolution: leftmost — a horizontal chain of five linked circles flowing left-to-right, each linked to the next by a single arrow, suggesting recurrent step-by-step computation; middle — a stack of three parallel horizontal bars of small circles connected by short vertical strokes, suggesting convolutional local receptive fields; rightmost — five circles arranged as a fully-connected mesh where every node connects to every other node with thin straight lines, suggesting global self-attention; all three motifs sit on a near-white field; the rightmost mesh is rendered in the accent blue while the other two are in the primary deep navy; subtle 6% grid background underneath everything; the upper third is reserved as calm scrim region for a page title in SVG; one short panel label above each motif as stable figure-internal identifier — RNN / CNN / SELF-ATTENTION — rendered in monospace technical lettering | embedded | hero_page |
| rnn_bottleneck.png | 480×600 | 0.80 | P04 right column — sequential computation bottleneck illustration | Diagram | #3 right-third image + left text body + #21 rounded rectangle crop | ai | Pending | A vertical chain of six small rounded rectangles stacked one above the other, connected by thin arrows pointing downward; each rectangle suggests a hidden state at one time step; an hourglass-shaped marker hovers along the chain hinting at the sequential time cost; on either side of the chain, faint dashed parallel lines suggest the channels that cannot be parallelized; the background is near-white with a 6% navy grid; all linework in primary deep navy except the hourglass which is in accent blue; subtle schematic spacing between elements; no embedded text, no labels, no numbers | none | local |
| sublayer_block.png | 480×600 | 0.80 | P10 left column — encoder/decoder sub-layer composition cross-section, conventional module labels inside the image | Diagram | #2 left-third image + right text body + #21 rounded rectangle crop | ai | Pending | A vertical schematic cross-section showing one encoder/decoder layer block: an outer rounded rectangle frame containing, top-to-bottom, two inner stacked rounded rectangles labeled visually as two sub-layers (one slightly taller, one shorter); a thin arc on the right side of each inner rectangle suggests a residual skip connection that wraps around the sub-layer and rejoins below it; a small horizontal stripe below each sub-layer suggests layer normalization; all linework in primary deep navy at uniform 1.5px stroke, accent blue used only on the two residual arcs to highlight them; near-white background with 6% navy grid; reads as a precise engineering schematic of the LayerNorm(x + Sublayer(x)) pattern; conventional architecture-paper labels inside the image — Self-Attention in the upper sub-layer, Feed Forward in the lower sub-layer, Add & Norm below each LayerNorm stripe — rendered as monospace technical lettering | embedded | local |
| positional_encoding.png | 1280×720 | 1.78 | P11 hero — sinusoidal positional encoding visualization with textbook curve and axis labels inside the image | Diagram | #1 full-bleed background with floating title + #30 flat semi-transparent rectangle overlay + #45 background image + numbered hotspots with sidebar legend | ai | Pending | A full-width schematic showing two superimposed sinusoidal waveforms running horizontally across the canvas — one is the sine wave at low frequency (long wavelength, gentle undulation) in primary deep navy, the other is the cosine wave at higher frequency (shorter wavelength, tighter undulation) in accent blue; below the waveforms, a horizontal row of ten small evenly-spaced tick marks suggests discrete token positions on a position axis; thin vertical accent-blue guide-lines at three of the ticks drop from the waveforms down to the axis, suggesting that each token position carries a unique pair of (sin, cos) values; the left third of the canvas is reserved as a calm scrim region for a page title in SVG; near-white background with 6% navy grid; reads as a technical figure from a textbook chapter on Fourier features; three stable in-image labels rendered in monospace technical lettering — the word sin near the right end of the navy curve, cos near the right end of the accent-blue curve, position → just below the right end of the axis line; no other text, no axis numbers, no equations | embedded | hero_page |
| transformer_family.png | 1280×720 | 1.78 | P16 hero — Transformer descendants family tree (BERT/GPT/T5/Vision Transformer abstract motifs) | Diagram | #12 faded image as backdrop with oversized overlay text + #30 flat semi-transparent rectangle overlay | ai | Pending | A symmetric top-down tree-of-descendants schematic: at the top, one single rounded rectangle (the root Transformer) in deep navy with a brighter accent-blue outline; from it, thin lines fan downward to two intermediate rounded rectangles slightly smaller (suggesting encoder-only and decoder-only families); from each intermediate, three thinner branches drop to small abstract leaf shapes of varying size (suggesting the multitude of derived models); the entire schematic is rendered at low opacity around 35% so it reads as a faded backdrop; near-white background with 6% navy grid underneath; an oversized empty calm region across the upper middle reserved for SVG closing title; reads as a quiet "what this paper started" diagram, not a busy logo wall; no embedded text, no labels, no model names — all labels overlaid as SVG text | none | hero_page |
| attention_p3_0.png | 1520×2239 | 0.68 | P05 Transformer model architecture (Figure 1 from paper) | Diagram | #19 image floating in whitespace with thin frame and caption + #45 background image + numbered hotspots with sidebar legend | user | Existing | Original Figure 1 from the paper showing the full Encoder–Decoder Transformer architecture — Nx stacked encoder block (Multi-Head Attention → Add & Norm → Feed Forward → Add & Norm) on the left; Nx stacked decoder block (Masked Multi-Head Attention → Add & Norm → Multi-Head Attention → Add & Norm → Feed Forward → Add & Norm) on the right; positional encodings entering both stacks; final Linear + Softmax at the top right | | |
| attention_p4_1.png | 835×1282 | 0.65 | P07 Scaled Dot-Product Attention (Figure 2 left) and P08 Multi-Head Attention (Figure 2 right) | Diagram | #46 background image + bordered "lens" rectangle highlighting a sub-region + #19 image floating in whitespace with thin frame and caption + #62 same image, two references — full view + zoom-callout | user | Existing | Original Figure 2 from the paper, two sub-figures side by side: left — Scaled Dot-Product Attention with MatMul → Scale → (Mask) → SoftMax → MatMul flow taking Q, K, V; right — Multi-Head Attention with h parallel Linear → Scaled Dot-Product Attention heads → Concat → Linear, taking V, K, Q inputs | | |
| formula_001.png | 880×122 | 7.21 | P07 block formula — Scaled Dot-Product Attention equation | Latex Formula | formula-block | formula | Rendered | `Attention(Q, K, V) = softmax(QK^T / √d_k) V` — equation (1) from §3.2.1 | | |
| formula_002.png | 1168×137 | 8.53 | P08 block formula — Multi-Head Attention equation | Latex Formula | formula-block | formula | Rendered | `MultiHead(Q,K,V) = Concat(head_1, …, head_h) W^O where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)` — equations from §3.2.2 | | |
| formula_003.png | 706×201 | 3.51 | P11 block formula — Positional Encoding equation | Latex Formula | formula-block | formula | Rendered | `PE_(pos, 2i) = sin(pos / 10000^(2i/d_model)); PE_(pos, 2i+1) = cos(pos / 10000^(2i/d_model))` — equation from §3.5 | | |

> Image-as-canvas coverage check: P01 uses #38, P03 uses #44, P05 / P11 use #45. Deck has ≥4 image-bearing pages and 4 of them use the #38–#46 family — coverage rule satisfied.

---

## IX. Content Outline

### Part 1: Opening

#### Slide 01 — Cover

- **Layout**: Full-bleed AI hero image + left-half calm region for title; #38 annotation cards with bezier leader lines + #29 two-stop scrim
- **Title**: Attention Is All You Need
- **Subtitle**: A paper deep-read
- **Info**: Vaswani et al. · Google Brain / Google Research / Univ. of Toronto · NeurIPS 2017 · arXiv:1706.03762

#### Slide 02 — Why this paper matters

- **Layout**: Page title + 4-card KPI row (kpi_cards) + one-line takeaway band
- **Title**: A simpler model, better results, less training
- **Visualization**: kpi_cards (see §VII)
- **Content**:
  - **28.4 BLEU** on WMT'14 EN-DE — +2.0 over previous SOTA ensembles
  - **41.8 BLEU** on WMT'14 EN-FR — new single-model SOTA
  - **3.5 days × 8 P100 GPUs** — a small fraction of prior training cost
  - **0 recurrence · 0 convolution** — only attention + feed-forward

### Part 2: Motivation & Background

#### Slide 03 — Sequence modeling so far: RNN → CNN → Self-Attention

- **Layout**: Hero AI image full-bleed + bottom scrim + floating title (#44 + #29)
- **Title**: From recurrent chains to a fully-connected attention mesh
- **Content**:
  - RNN / LSTM / GRU — strong, but inherently sequential
  - ByteNet / ConvS2S — parallelizable, but signals between distant positions still grow with distance
  - Self-attention — relates any two positions in constant operations

#### Slide 04 — The fundamental constraint we want to lift

- **Layout**: Right-third AI image (#3 + #21) + left vertical_pillars
- **Title**: What hurts in RNN/CNN sequence models
- **Visualization**: vertical_pillars
- **Content**:
  - **Sequential bottleneck** — h_t depends on h_{t-1}; no within-example parallelism
  - **Long-range path length** — ConvS2S grows linearly, ByteNet logarithmically; distant tokens hard to relate
  - **Memory ceiling** — sequence length limits batch size, especially at long context

### Part 3: The Transformer

#### Slide 05 — Model architecture overview

- **Layout**: User-provided Figure 1 image (portrait, scaled to fit) on left + right-side numbered hotspot legend (#19 + #45)
- **Title**: Encoder–Decoder, stacked self-attention, point-wise feed-forward
- **Content** (sidebar legend):
  1. Input embeddings + positional encoding
  2. Nx encoder block — Multi-Head Self-Attention + FFN
  3. Nx decoder block — Masked Self-Attn + Encoder–Decoder Attn + FFN
  4. Add & Norm — residual then LayerNorm around every sub-layer
  5. Final Linear + Softmax — output token probabilities

#### Slide 06 — Encoder vs Decoder stacks

- **Layout**: comparison_columns — two parallel cards
- **Title**: Same skeleton, three asymmetries
- **Visualization**: comparison_columns
- **Content**:
  - **Encoder (N=6)** — Multi-Head Self-Attention → FFN; LayerNorm(x + Sublayer(x)); d_model = 512
  - **Decoder (N=6)** — Masked Multi-Head Self-Attention → Encoder-Decoder Multi-Head Attention → FFN; same residual + LN; output offset by one position; positions attend only to earlier outputs

### Part 4: Attention mechanism

#### Slide 07 — Scaled Dot-Product Attention

- **Layout**: User-provided Figure 2 cropped to left half (#46 lens crop) on right + left text body + centered formula band
- **Title**: Attention as a weighted average — keys, values, queries
- **Visualization**: Formula block (formula_001.png)
- **Content**:
  - Inputs: queries and keys of dim d_k, values of dim d_v
  - Compute QK^T, scale by √d_k, softmax → attention weights
  - Multiply by V — weighted sum is the output
  - Scaling matters: without √d_k, large d_k pushes softmax into low-gradient regions

#### Slide 08 — Multi-Head Attention

- **Layout**: User-provided Figure 2 cropped to right half (#46 lens crop) on right + left text body + centered formula band
- **Title**: h parallel projections, then concatenate
- **Visualization**: Formula block (formula_002.png)
- **Content**:
  - Project Q, K, V into h = 8 independent subspaces via learned linear projections
  - Run scaled dot-product attention in each head in parallel; d_k = d_v = d_model / h = 64
  - Concatenate the h outputs and project once more with W^O
  - Why: attend to information from different representation subspaces at different positions

#### Slide 09 — Three places attention is used

- **Layout**: vertical_pillars — three independent columns
- **Title**: One mechanism, three roles in the Transformer
- **Visualization**: vertical_pillars
- **Content**:
  - **Encoder self-attention** — Q, K, V all from the previous encoder layer; every position attends to all positions
  - **Decoder masked self-attention** — same as above but masked: position i attends only to positions ≤ i (preserve auto-regression)
  - **Encoder–decoder attention** — queries from the decoder, keys & values from the encoder output; lets every decoder position attend over the whole input sequence (the classic seq2seq attention role)

#### Slide 10 — Feed-Forward, Residual, LayerNorm

- **Layout**: Left-third AI image (#2 + #21) + right module_composition
- **Title**: The supporting cast inside every layer
- **Visualization**: module_composition
- **Content**:
  - **Position-wise FFN** — two linear layers with ReLU between, applied identically at every position; inner dim 2048
  - **Residual connection** — every sub-layer output is x + Sublayer(x), enabling deeper stacks
  - **LayerNorm** — applied around each sub-layer; stabilizes training, paired with d_model = 512

### Part 5: Position information

#### Slide 11 — Positional Encoding

- **Layout**: AI hero image full-bleed (#1 + #30 + #45) + centered formula band + minimal SVG annotation
- **Title**: Recovering order without recurrence — sinusoids of different frequencies
- **Visualization**: Formula block (formula_003.png)
- **Content**:
  - No recurrence / convolution → model has no built-in notion of token order
  - Add a deterministic sinusoidal position vector to each input embedding
  - sin / cos at geometrically increasing wavelengths from 2π to 10000·2π
  - Lets the model learn to attend by relative position via linear function of PE

### Part 6: Why and how well it works

#### Slide 12 — Complexity comparison (Table 1)

- **Layout**: Page title + basic_table (full-width)
- **Title**: Complexity per layer, sequential operations, max path length
- **Visualization**: basic_table
- **Content**:
  - Self-Attention: O(n²·d), 1 sequential op, max path length O(1)
  - Recurrent: O(n·d²), O(n) sequential ops, max path length O(n)
  - Convolutional: O(k·n·d²), 1, max path length O(log_k n)
  - Self-Attention (restricted, window r): O(r·n·d), 1, max path length O(n/r)

#### Slide 13 — Training setup

- **Layout**: Page title + kpi_cards (2×2 or 1×4)
- **Title**: How they trained it
- **Visualization**: kpi_cards
- **Content**:
  - **Hardware** — 8× NVIDIA P100 GPUs
  - **Time** — Base 12 h (100k steps) · Big 3.5 d (300k steps)
  - **Optimizer** — Adam, β₁=0.9, β₂=0.98, ε=1e-9; warm-up then 1/√step decay
  - **Regularization** — Dropout 0.1, label smoothing ε_ls = 0.1

#### Slide 14 — Results (Table 2)

- **Layout**: Page title + basic_table (full-width) + bottom takeaway band
- **Title**: New SOTA on WMT'14 — at a fraction of the training cost
- **Visualization**: basic_table
- **Content**:
  - Transformer (big): EN-DE 28.4 BLEU · EN-FR 41.8 BLEU
  - vs prior best ensembles: +2.0 EN-DE; new single-model SOTA EN-FR
  - Training FLOPs (big): ~2.3 × 10¹⁹ — well below most strong baselines

#### Slide 15 — What matters in the architecture (Table 3 ablations)

- **Layout**: vertical_list (5 numbered key points)
- **Title**: Five takeaways from the variation study
- **Visualization**: vertical_list
- **Content**:
  - **Head count has a sweet spot** — single-head loses 0.9 BLEU; too many (32) also degrade
  - **Key dim matters more than value dim** — reducing d_k hurts quality more than reducing d_v
  - **Bigger is better** — larger d_model and deeper stacks consistently improve BLEU
  - **Dropout is essential** — removing it loses ~0.5–1.0 BLEU; even small dropout (0.1) matters
  - **Label smoothing helps perplexity & BLEU** — slightly hurts perplexity but improves BLEU

### Part 7: Closing

#### Slide 16 — What this paper started

- **Layout**: AI hero image full-bleed faded (#12 + #30) + centered closing title + small caption row
- **Title**: One paper, a generation of models
- **Content**:
  - Transformer became the substrate for BERT, GPT, T5, Vision Transformer, AlphaFold, and most modern LLMs
  - The 2017 idea — **just attention** — turned out to be the right inductive bias for almost every modality
  - References: arXiv:1706.03762, code at github.com/tensorflow/tensor2tensor

---

## X. Speaker Notes Requirements

- **Filename**: one file per slide under `notes/`, matching SVG basename (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Style**: conversational-academic (paper-reading-group register — clear, technical, no marketing copy)
- **Total duration**: ~20 minutes presented (≈ 75 sec per slide on average; deeper slides P05/P07/P08/P11 ≈ 100 sec each)
- **Purpose**: instruct / inform — explain the paper to an engineer who has not read it carefully
- **Format**: master document at `notes/total.md` with `#` headings per slide; split files have no `#` heading

---

## XI. Technical Constraints Reminder

### SVG Generation Must Follow:

1. viewBox: `0 0 1280 720`
2. Background uses `<rect>` elements
3. Text wrapping uses `<tspan>` (`<foreignObject>` FORBIDDEN)
4. Transparency defaults to `fill-opacity` / `stroke-opacity`; `rgba()` remains converter-compatible
5. FORBIDDEN: `mask`, `<style>`, `class`, `foreignObject`, `textPath`, `animate*`, `script`
6. Text characters: raw Unicode (`—`, `→`, NBSP, `²`, `√`, `≤`, `·`); HTML named entities FORBIDDEN; reserved chars escaped as `&amp; &lt; &gt; &quot; &apos;`
7. `marker-start` / `marker-end` conditionally allowed: `<marker>` in `<defs>`, `orient="auto"`, triangle / diamond / circle shape only
8. `clipPath` only on `<image>` elements: `<clipPath>` in `<defs>`, single shape child

### PPT Compatibility Rules:

- Prefer opacity on each child element; `<g opacity="...">` remains converter-compatible with an approximate-fidelity warning
- Image transparency uses overlay mask layer (`<rect fill="bg-color" opacity="0.x"/>`)
- Inline styles only; external CSS and `@font-face` FORBIDDEN
