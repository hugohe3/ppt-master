> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# Image Layout Specification

Sizing reference for side-by-side or multi-image pages. Use only after Strategist selects the composition; this file never selects layout or crop policy.

**Selected pattern, flexible geometry**: Let original aspect ratio inform the container. A `no-crop` asset displays completely; an `adaptive` asset may use `meet` or a focal-safe `slice`. Rework geometry within the selected pattern when either mode produces weak hierarchy, unsafe cropping, or excessive dead space; changing the pattern requires an upstream Design Spec update.

> **Scope**: The ratio tables and formulas are calculation aids for a selected side-by-side or multi-image plan. Hero, background, accent, and other compositions stay outside this file. Layout never overrides the `no-crop` boundary owned by [`strategist-image.md`](./strategist-image.md) and [`executor-image.md`](./executor-image.md).

---

## Layout Decision Flow

```
1. Read the selected narrative intent, hierarchy, and primary/modifier ids from Strategist's plan.
2. If the selected pattern is not side-by-side or multi-image, this spec does not apply.
3. Read the asset's `no-crop` boundary and original dimensions; calculate ratio (width/height).
4. Use the tables as candidate structures, not an automatic selector.
5. Calculate the image/text rectangles, then choose `meet` or focal-safe `slice` within the crop boundary.
6. Revise geometry within the selected ids when the result weakens hierarchy, legibility, or required image content.
7. Return upstream for a different pattern, resource, role, or crop boundary; Executor never rewrites selection.
```

**When to run**: after `analyze_images.py` has produced current dimensions and a side-by-side or multi-image composition is under consideration. Skip this sizing reference for other page structures.

---

## Layout Starting Points (side-by-side intent)

| Image Ratio | Useful Starting Structure | Image Position | Description |
|-------------|-------------|----------------|-------------|
| > 2.0 (ultra-wide) | Top-bottom split | Top full-width | Image spans canvas width, height proportional |
| 1.5-2.0 (wide) | Top-bottom split | Top | Image width = content area width, height proportional |
| 1.2-1.5 (standard) | Left-right split | Left | Image height-first fit, width proportional |
| 0.8-1.2 (square) | Left-right split | Left | Image takes content area height, width proportional |
| < 0.8 (portrait) | Left-right split | Left | Image height = content area height, width proportional |

> Boundary ratios are orientation cues, not thresholds. Let text volume, focal content, page hierarchy, and crop safety decide.

---

## Dimension Calculation Formulas

### Canvas Parameters (All Formats)

| Format | Canvas | Margins (L/R, T/B) | Content Area (W x H) | Title Height | Content Start Y |
|--------|--------|--------------------|-----------------------|-------------|----------------|
| PPT 16:9 | 1280x720 | 60, 60 | 1160 x 600 | 60px | 80px |
| PPT 4:3 | 1024x768 | 50, 50 | 924 x 608 | 60px | 70px |
| Xiaohongshu | 1242x1660 | 60, 80 | 1122 x 1500 | 80px | 100px |
| WeChat Moments | 1080x1080 | 60, 60 | 960 x 960 | 60px | 80px |
| Story | 1080x1920 | 60, 120/180 | 960 x 1620 | 80px | 140px |
| WeChat Article | 900x383 | 40, 40 | 820 x 303 | 40px | 50px |

> Below, **W** = content area width, **H** = content area height (excludes title). PPT 16:9 example: W=1160, H=600.

### Top-Bottom Layout Calculation

```
Image width = W = 1160 px
Image height = W / R = 1160 / R px
Text area height = H - image height - gap(20px)

Review: if the remaining text area cannot carry the planned copy legibly,
rebalance the rectangles within the selected pattern; otherwise return upstream
for a Design Spec pattern update.
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

**Review**: if the remaining text area cannot carry the planned copy legibly, rebalance the image/text rectangles within the selected pattern; otherwise return upstream for a Design Spec pattern update.

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
Strategist compares top-bottom: image height=663, text area=-43 ❌
Strategist selects left-right: image 780x446 (left), text area 360x600 (right) → 7:3 left-right
```

---

## Portrait Canvas Override

Default selection table assumes **landscape or square canvas**. For portrait canvases (height > width), left-right splits leave both columns too narrow — use the override below.

| Canvas Orientation | Image Ratio | Useful Starting Structure | Reason |
|-------------------|-------------|-------------------|--------|
| Portrait (Xiaohongshu, Story) | > 1.5 (wide) | Top-bottom | Same as landscape canvas |
| Portrait (Xiaohongshu, Story) | 1.2-1.5 (standard) | Top-bottom | Left-right too narrow on tall canvas |
| Portrait (Xiaohongshu, Story) | 0.8-1.2 (square) | Top-bottom | Image fits well in top half |
| Portrait (Xiaohongshu, Story) | 0.5-0.8 (portrait) | Left-right | Portrait image on tall canvas works |
| Portrait (Xiaohongshu, Story) | < 0.5 (extreme portrait) | Left-right | Image takes one side, text the other |

> Square canvases (WeChat Moments 1:1): use the standard landscape rules.

---

## Multi-Image Layout

For slides with multiple images, divide the content area evenly using the formulas below.

### Grid Formulas

```
columns = number of columns
rows = number of rows
gap = 20px (PPT formats) or 30px (social formats)

cell_width  = (W - (columns - 1) * gap) / columns
cell_height = (H - (rows - 1) * gap) / rows
```

### Common Patterns

| Image Count | Layout | Grid | Description |
|-------------|--------|------|-------------|
| 2 (both landscape) | Side-by-side | 2x1 | Two equal columns |
| 2 (both portrait) | Stacked | 1x2 | Two equal rows |
| 2 (mixed) | 1 large + 1 small | Custom | Landscape top (full-width), portrait right-bottom |
| 3 | 1 large + 2 small | 1+2 | Left large (50% width), right column with 2 stacked |
| 4 | Grid | 2x2 | Equal-sized cells |

### Example: 2x2 Grid on PPT 16:9

```
W=1160, H=600, gap=20
cell_width  = (1160 - 20) / 2 = 570
cell_height = (600 - 20) / 2 = 290

Image positions:
  (60, 80)   570x290    (650, 80)  570x290
  (60, 390)  570x290    (650, 390) 570x290
```

> Multi-image slides: decide `meet` or focal-safe `slice` per asset. Keep `no-crop` images complete; do not force every image into the same scaling mode merely for grid uniformity.

---

## Composition Checks

| Check | Action |
|-----------|-----------------|
| Proportion does not reflect information weight | Rebalance image and text rectangles |
| Container conflicts with the native ratio | Change the container, choose `meet`, or use a focal-safe crop |
| Required pixels, labels, identity, or evidence would be cropped | Use `preserveAspectRatio="xMidYMid meet"` and recompose around the complete image |
| Text area cannot carry the planned copy legibly | Increase its area within the selected pattern; otherwise return upstream |

---

## Handoff Fields

This spec only defines layout calculation. Write computed fields into the Image Resource List defined in [`svg-image-embedding.md`](svg-image-embedding.md):

| Field | Meaning |
|-------|---------|
| `Ratio` | Original image width / height |
| `Layout pattern` | Strategist-selected catalog pattern; semantic composition fixed, geometry flexible |
| `Crop Policy` | `no-crop` protects complete pixels; `adaptive` lets Executor choose `meet` or focal-safe `slice` |
| `Reference` | Optional calculated image/text rectangles, focal notes, and composition intent |
| `spec_lock.md images` value | `<path> | source=<Acquire Via> | pattern=<Layout pattern> | crop=<adaptive|no-crop>` |

For SVG `<image>` syntax, path rules, `preserveAspectRatio`, external refs, and Base64 embedding: see [`svg-image-embedding.md`](svg-image-embedding.md).

### SVG Image Embedding Examples

Complete display (`no-crop` assets such as data charts):

```xml
<image href="../images/xxx.png"
       x="60" y="80" width="780" height="446"
       preserveAspectRatio="xMidYMid meet"/>
```

Crop-to-fill (an `adaptive` asset with a verified focal-safe crop):

```xml
<image href="../images/bg.png"
       x="0" y="0" width="1280" height="720"
       preserveAspectRatio="xMidYMid slice"/>
```

---

## Automation Tool

```bash
python3 scripts/analyze_images.py <project_path>/images                    # Default: PPT 16:9
python3 scripts/analyze_images.py <project_path>/images --canvas ppt43     # PPT 4:3
python3 scripts/analyze_images.py <project_path>/images --canvas xiaohongshu  # Xiaohongshu
```

`--canvas` selects target format (default `ppt169`). The tool computes a top-bottom / left-right candidate, image display area, and text area from the formulas above. Treat its output as planning input; record the composition actually selected for the page.

---

## Role Responsibilities

| Role | Responsibility |
|------|---------------|
| **Strategist** | Run `analyze_images.py`, select the catalog pattern/resources, and record the crop boundary |
| **Executor** | Realize the selected pattern for the actual asset/page while preserving its ids, role, source, must-use, and `no-crop` constraints |
