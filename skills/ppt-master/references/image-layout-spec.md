> See shared-standards.md for common technical constraints.

# Image Layout Specification (Mandatory)

Layout rules for pages containing images. Both the Strategist planning phase and Executor generation phase must follow these rules.

**Core principle: Calculate layout based on the image's original aspect ratio, ensuring the image is displayed completely without excess whitespace or cropping.**

---

## Layout Decision Flow

```
1. Get image original dimensions → Calculate ratio (width/height)
2. Select layout type based on ratio
3. Calculate maximum display size for the image
4. Allocate remaining space for text area
5. Fill results into the Design Specification's image resource list
```

**When to execute**: If the image approach includes "B) User-provided", after the Strategist completes the Eight Confirmations and before content analysis and outlining, the scan must be run and the image resource list populated.

---

## Layout Type Selection (Mandatory)

| Image Ratio | Layout Type | Image Position | Description |
|-------------|-------------|----------------|-------------|
| > 2.0 (ultra-wide) | Top-bottom split | Top full-width | Image spans canvas width, height proportional |
| 1.5-2.0 (wide) | Top-bottom split | Top | Image width = content area width, height proportional |
| 1.2-1.5 (standard) | Left-right split | Left | Image height-first fit, width proportional |
| 0.8-1.2 (square) | Left-right split | Left | Image takes content area height, width proportional |
| < 0.8 (portrait) | Left-right split | Left | Image height = content area height, width proportional |

> Edge cases: When ratio is at a boundary (e.g., 1.5), decide based on text volume. More text → left-right; less text → top-bottom.

---

## Dimension Calculation Formulas

### PPT 16:9 (1280x720) Canvas Parameters

```
Canvas: 1280 x 720 px
Content area: 1160 x 640 px (left/right margin 60px, top/bottom margin 40px)
Title area height: 60 px
Content start: y = 80 px (title + spacing)
```

### Top-Bottom Layout Calculation

```
Image width = W = 1160 px
Image height = W / R = 1160 / R px
Text area height = H - image height - gap(20px)

Validation: Text area height >= 150px (at least 3-4 lines of text)
If not satisfied → Switch to left-right layout
```

### Left-Right Layout Calculation

**Method 1 (height-first, suitable for portrait images)**:
```
Image height = H = 600 px
Image width = H x R = 600 x R px
Text area width = W - image width - gap(20px)
```

**Method 2 (width-constrained, for wide images converted to left-right)**:
```
Image width = W x 0.7 = 812 px
Image height = image width / R
Text area width = W - image width - gap(20px)
```

**Validation**: Text area width >= 280px; otherwise reduce image area width.

---

## Layout Examples

### Ultra-wide Image (ratio 2.45)

```
Original: 1960x800, R=2.45 → Top-bottom split
Image: 1160x473, Text area: 1160x147 → 7:3 top-bottom
```

### Standard Landscape (ratio 1.38)

```
Original: 1614x1171, R=1.38 → Left-right split
Image: 773x560 (left), Text area: 367x560 (right) → 7:3 left-right
```

### Wide Image Edge Case (ratio 1.75)

```
Original: 1820x1040, R=1.75
Try top-bottom: image height=663, text area=-43 ❌
Switch to left-right: image 780x446 (left), text area 360x600 (right) → 7:3 left-right
```

---

## Prohibited Practices

| Prohibited | Correct Approach |
|-----------|-----------------|
| Fixed 50:50 or arbitrary ratios | Dynamic calculation based on image ratio |
| Forcing wide image into square container | Use top-bottom layout or increase image area width |
| Placing portrait image in narrow horizontal strip | Use left-right layout, image on left |
| Image whitespace exceeding 10% | Recalculate layout or choose alternative approach |
| Cropping key image content | Use `preserveAspectRatio="xMidYMid meet"` |
| Text area too small to read | Ensure text area >= 150px (top-bottom) or >= 280px (left-right) |

---

## SVG Image Embedding Code

### Complete Display (recommended for data charts)

```xml
<image href="../images/xxx.png"
       x="60" y="80" width="780" height="446"
       preserveAspectRatio="xMidYMid meet"/>
```

### Crop-to-Fill (backgrounds only)

```xml
<image href="../images/bg.png"
       x="0" y="0" width="1280" height="720"
       preserveAspectRatio="xMidYMid slice"/>
```

---

## Image Resource List Template

In the Design Specification & Content Outline, the image resource list must include:

| Field | Description | Example |
|-------|-------------|---------|
| Filename | Image filename | `p12_0.png` |
| Original dimensions | Width x Height | 1524x968 |
| Ratio | Width / Height | 1.57 |
| Page | Usage page number | Page 5 |
| Type | Visual type | Background / Photography / Illustration / Diagram / Decorative |
| Layout plan | Top-bottom/Left-right + split ratio | Top-bottom 6:4 or Left-right 7:3 |
| Image area | Image display dimensions | 1160x420 or 780x446 |
| Text area | Remaining space dimensions | 1160x200 or 360x600 |

**The Type field is used by Image_Generator to select the appropriate prompt strategy.**

---

## Automation Tool

```bash
python3 scripts/analyze_images.py <project_path>/images
```

Output includes dimensions, ratios, and layout recommendations (Markdown table), which can be directly used to populate the image resource list.

---

## Role Responsibilities

| Role | Responsibility |
|------|---------------|
| **Strategist** | Run analyze_images.py, calculate layout per this spec, populate image resource list |
| **Executor** | Strictly follow the layout plan and dimensions in the image resource list when generating SVGs |
