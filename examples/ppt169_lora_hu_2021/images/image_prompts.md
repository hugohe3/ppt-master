# Image Generation Prompts

> Auto-generated from `image_prompts.json` by `image_gen.py --render-md`.
> Do not hand-edit — re-run the command to refresh.

> Project: lora_hu_2021
> Generated: 2026-05-23
> Color scheme: Primary #1B3A5C | Secondary #F4F7FA | Accent #E8743B

---

### Image 1: cover_hero.png

| Attribute | Value |
|---|---|
| Purpose | Cover hero visual (Slide 01) |
| Aspect ratio | 16:9 |
| Image size | 2K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: clean precise lines on a subtle low-opacity grid, deliberate geometric rigor with right angles and measured spacing, elements simplified to essential schematic forms (boxes, rounded rectangles, connector lines, anchor dots), no textures or shading, engineering-precise and analytical. Color behavior is restrained-corporate: a near-white field #F4F7FA carries about 62% of the canvas as calm breathing space, deep navy #1B3A5C forms the main schematic structure and lines (about 30%), warm orange #E8743B appears only on the single injected low-rank branch and one small anchor dot (under 8%). Composition: one dominant concept centered with generous negative space — a large frozen pretrained weight matrix drawn as a big square grid block marked with a small padlock glyph to signal it is frozen, and a slim parallel branch beside it made of two thin rectangular matrices, a tall-narrow down-projection labelled 'A' and a wide-short up-projection labelled 'B' meeting at a narrow bottleneck labelled 'r', their connector lines summing into the block's output. Embedded designed lettering, part of the artwork: a large title reading 'LoRA' and a smaller tagline 'Low-Rank Adaptation', set as clean geometric sans-serif. Composed as a 1280x720 hero image for hero_page use; keep the lower third relatively calm and uncluttered so an SVG subtitle can overlay it. Render the HEX values only as colors, never as literal text in the image; keep every form simplified and schematic.

**Alt Text**:
> Blueprint schematic: a frozen pretrained weight block with a small low-rank A-to-B branch injected, titled LoRA

---

### Image 2: cost_explosion.png

| Attribute | Value |
|---|---|
| Purpose | Cost of full fine-tuning at 175B scale (Slide 03) |
| Type | scene |
| Aspect ratio | 16:9 |
| Image size | 1K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: clean precise lines on a subtle low-opacity grid, simplified schematic forms, no textures or shading, engineering-precise and analytical. Color behavior is restrained-corporate: near-white field #F4F7FA dominates as calm space (about 60%), deep navy #1B3A5C carries the structural forms (about 32%), warm orange #E8743B appears only on a single small cost-warning marker (under 6%). Composition for a local block whose subject bleeds off the right canvas edge: one very large model block on the left, then the same model replicated into a receding row of identical heavy server-rack stacks marching toward and off the right edge, each rack tagged with a short embedded label '175B', conveying 'one full-parameter copy stored per task'; a small multiplication motif 'x N' near the receding stacks. Keep the subject weighted to the right two-thirds and the left third calmer so SVG text can sit there. Composed as a 1280x720 image for local use. Embedded text is limited to the short stable labels '175B' and 'x N'. Render the HEX values only as colors, never as literal text; keep every form simplified and schematic.

**Alt Text**:
> A 175B model copied into many identical heavy server racks, one per task

---

### Image 3: lowrank_insight.png

| Attribute | Value |
|---|---|
| Purpose | Low intrinsic-rank insight (Slide 05) |
| Type | scene |
| Aspect ratio | 16:9 |
| Image size | 1K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: clean precise lines on a subtle low-opacity grid, simplified schematic forms, no textures or shading, engineering-precise and analytical. Color behavior is restrained-corporate: near-white field #F4F7FA carries most of the canvas as generous whitespace (about 65%), deep navy #1B3A5C draws the structure (about 28%), warm orange #E8743B highlights only the two or three principal-direction arrows (under 7%). Composition: a diffuse cloud of fine points in an implied high-dimensional space collapsing and projecting down onto a single thin low-dimensional plane sheet; on that plane, two or three bold principal-direction arrows in orange carry the main structure, while the off-plane scatter fades to faint navy. Lots of surrounding negative space, the figure floating near center. Embedded short labels, part of the diagram: 'low-rank subspace' on the plane and 'intrinsic rank r' beside the principal arrows. Composed as a 1280x720 image for local use. Render the HEX values only as colors, never as literal text; keep every form simplified and schematic.

**Alt Text**:
> A high-dimensional weight-update cloud collapsing onto a low-dimensional subspace plane

---

### Image 4: reparam_diagram_cropped.png

| Attribute | Value |
|---|---|
| Purpose | LoRA reparametrization forward-pass schematic (Slide 06) |
| Type | flowchart |
| Aspect ratio | 16:9 |
| Image size | 2K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: clean precise lines on a subtle low-opacity grid, deliberate geometric rigor, right-angle connector lines with small arrowheads and dot anchors at junctions, simplified schematic forms, no textures or shading, engineering-precise. Color behavior is restrained-corporate: near-white grid field #F4F7FA about 60%, deep navy #1B3A5C for lines and blocks about 32%, warm orange #E8743B only on the low-rank branch about 8%. Composition: a precise left-to-right signal-path schematic. An input node labelled 'x' on the left splits into two parallel paths that rejoin at a summation node drawn as a circled plus, producing an output labelled 'h' on the right. Top path: a large square block labelled 'Pretrained Weights W' with a small padlock glyph marking it frozen. Bottom path, highlighted in warm orange: a down-projection matrix labelled 'A' narrowing to a thin bottleneck labelled 'r', then an up-projection matrix labelled 'B'. Add an engineering-style dimension tick with end-caps spanning the bottleneck, annotated 'r is small'. Embedded labels are short technical identifiers, part of the schematic: 'x', 'h', 'W', 'A', 'B', 'r'. Composed as a 1280x720 image for local use; leave a calm horizontal band at the bottom so an SVG formula caption can overlay it. Render the HEX values only as colors, never as literal text; keep every form simplified and schematic.

**Alt Text**:
> Forward pass schematic: x feeds frozen W and a low-rank A-to-B branch, summed into h

---

### Image 5: attention_apply.png

| Attribute | Value |
|---|---|
| Purpose | LoRA applied to Transformer attention (Slide 08) |
| Type | flowchart |
| Aspect ratio | 16:9 |
| Image size | 1K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: clean precise lines on a subtle low-opacity grid, right-angle connectors with dot anchors, simplified schematic forms, no textures or shading, engineering-precise. Color behavior is restrained-corporate: near-white field #F4F7FA about 60%, deep navy #1B3A5C structure about 33%, warm orange #E8743B only on the two highlighted LoRA branches (under 7%). Composition: a Transformer self-attention module drawn as a clean vertical schematic stack of four projection-matrix boxes labelled 'Wq', 'Wk', 'Wv', 'Wo'; the 'Wq' and 'Wv' boxes each carry a small parallel low-rank LoRA branch highlighted in orange; below them an MLP block tagged with a small padlock and a short label 'frozen'. Connector lines route at right angles with small anchor dots. Place the schematic in the left portion of the canvas for a left-third placement, keeping the right side calmer for SVG text. Embedded labels are short stable identifiers: 'Wq', 'Wk', 'Wv', 'Wo', 'MLP', 'frozen'. Composed as a 1280x720 image for local use. Render the HEX values only as colors, never as literal text; keep every form simplified and schematic.

**Alt Text**:
> Transformer attention block with LoRA branches on Wq and Wv, MLP frozen

---

### Image 6: subspace_heatmap.png

| Attribute | Value |
|---|---|
| Purpose | Subspace similarity heatmap (Slide 14) |
| Type | scene |
| Aspect ratio | 1:1 |
| Image size | 1K |
| Status | Generated |

**Prompt**:

Technical blueprint schematic style: crisp clean lines, precise grid, simplified forms, no textures or shading, analytical and engineering-precise. Color behavior is restrained-corporate built as an intensity scale: deep navy #1B3A5C for low values, warm orange #E8743B for high values, on a near-white frame #F4F7FA. Composition: a square correlation-style heatmap grid of cells showing a normalized subspace-similarity matrix; the top-left cells corresponding to top singular directions glow at high intensity in warm orange and rapidly fade to deep navy toward larger indices, so the bright signal concentrates in one corner. Crisp thin grid lines between cells; a vertical axis labelled 'i' and a horizontal axis labelled 'j'; a slim vertical intensity scale bar on the right running from '0' at the bottom to '1' at the top. Embedded text limited to the short stable labels 'i', 'j', '0', '1'. Composed as a 1024x1024 square image for local use. Render the HEX values only as colors, never as literal text; keep every form simplified and schematic.

**Alt Text**:
> Square subspace-similarity heatmap, bright in the top-left singular directions, fading elsewhere

---
