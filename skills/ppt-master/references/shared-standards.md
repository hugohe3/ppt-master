# Shared Technical Standards

Common technical constraints for PPT Master, eliminating cross-role file duplication.

---

## 1. SVG Banned Features Blacklist

The following features are **absolutely forbidden** when generating SVGs — PPT export will break if any are used:

| Banned Feature | Description |
|----------------|-------------|
| `clipPath` | Clipping paths |
| `mask` | Masks |
| `<style>` | Embedded stylesheets |
| `class` | CSS selector attributes (`id` inside `<defs>` is a legitimate reference and is NOT banned) |
| External CSS | External stylesheet links |
| `<foreignObject>` | Embedded external content |
| `<symbol>` + `<use>` | Symbol reference reuse |
| `textPath` | Text along a path |
| `@font-face` | Custom font declarations |
| `<animate*>` / `<set>` | SVG animations |
| `<script>` / event attributes | Scripts and interactivity |
| `marker` / `marker-end` | Line endpoint markers |
| `<iframe>` | Embedded frames |

---

## 2. PPT Compatibility Alternatives

| Banned Syntax | Correct Alternative |
|---------------|---------------------|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">...</g>` | Set `fill-opacity` / `stroke-opacity` on each child element individually |
| `<image opacity="0.3"/>` | Overlay a `<rect fill="background-color" opacity="0.7"/>` mask layer after the image |
| `marker-end` arrows | Draw triangle arrows with `<polygon>` |

**Mnemonic**: PPT does not recognize rgba, group opacity, image opacity, or markers.

---

## 3. Canvas Format Quick Reference

### Presentations

| Format | viewBox | Dimensions | Ratio |
|--------|---------|------------|-------|
| PPT 16:9 | `0 0 1280 720` | 1280x720 | 16:9 |
| PPT 4:3 | `0 0 1024 768` | 1024x768 | 4:3 |

### Social Media

| Format | viewBox | Dimensions | Ratio |
|--------|---------|------------|-------|
| Xiaohongshu (RED) | `0 0 1242 1660` | 1242x1660 | 3:4 |
| WeChat Moments / Instagram Post | `0 0 1080 1080` | 1080x1080 | 1:1 |
| Story / TikTok Vertical | `0 0 1080 1920` | 1080x1920 | 9:16 |

### Marketing Materials

| Format | viewBox | Dimensions | Ratio |
|--------|---------|------------|-------|
| WeChat Article Header | `0 0 900 383` | 900x383 | 2.35:1 |
| Landscape Banner | `0 0 1920 1080` | 1920x1080 | 16:9 |
| Portrait Poster | `0 0 1080 1920` | 1080x1920 | 9:16 |
| A4 Print (150dpi) | `0 0 1240 1754` | 1240x1754 | 1:1.414 |

---

## 4. Basic SVG Rules

- **viewBox** must match the canvas dimensions (`width`/`height` must match `viewBox`)
- **Background**: Use `<rect>` to define the page background color
- **Line breaks**: Use `<tspan>` for manual line breaks; `<foreignObject>` is FORBIDDEN
- **Fonts**: Use system fonts only (Microsoft YaHei, Arial, Calibri, etc.); `@font-face` is FORBIDDEN
- **Styles**: Use inline styles only (`fill="..."` `font-size="..."`); `<style>` / `class` are FORBIDDEN (`id` inside `<defs>` is legitimate)
- **Colors**: Use HEX values; for transparency use `fill-opacity` / `stroke-opacity`
- **Image references**: `<image href="../images/xxx.png" preserveAspectRatio="xMidYMid slice"/>`
- **Icon placeholders**: `<use data-icon="chunk/name" x="" y="" width="48" height="48" fill="#HEX"/>` (default library); or `tabler-filled/name` / `tabler-outline/name` when that library is chosen for the deck. (auto-embedded during post-processing). Always include the library prefix. **One presentation = one library — never mix libraries.**

### Element Grouping (Mandatory)

Logically related elements **MUST** be wrapped in `<g>` tags. This produces PowerPoint groups in the exported PPTX, making slides easier to select, move, and edit.

> ⚠️ **Only `<g opacity="...">` is banned** (see §2). Plain `<g>` for structural grouping is required.

**What to group**:

| Grouping Unit | Contains |
|---------------|----------|
| Card / panel | Background rect + shadow + icon + title + body text |
| Process step | Number circle + icon + label + description |
| List item | Bullet / number + icon + title + description |
| Icon-text combo | Icon element + adjacent label |
| Page header | Title + subtitle + accent decoration |
| Page footer | Page number + branding |
| Decorative cluster | Related decorative shapes (rings, orbs, dots) |

**Example**:

```xml
<g id="card-benefits-1">
  <rect x="60" y="115" width="565" height="260" rx="20" fill="#FFFFFF" filter="url(#shadow)"/>
  <use data-icon="bolt" x="108" y="163" width="44" height="44" fill="#0071E3"/>
  <text x="105" y="270" font-size="56" font-weight="bold" fill="#0071E3">10×</text>
  <text x="250" y="270" font-size="30" font-weight="bold" fill="#1D1D1F">Faster</text>
  <text x="105" y="310" font-size="18" fill="#6E6E73">Reduce production time from days to hours.</text>
</g>
```

**Naming convention**: Use descriptive `id` attributes on `<g>` tags (e.g., `card-1`, `step-discover`, `header`, `footer`). IDs are optional but recommended for readability.

---

## 5. Post-processing Pipeline (3 Steps)

Must be executed in order — skipping or adding extra flags is FORBIDDEN:

```bash
# 1. Split speaker notes into per-page note files
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (icon embedding, image crop/embed, text flattening, rounded rect to path)
python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX (from svg_final/, embeds speaker notes by default)
python3 scripts/svg_to_pptx.py <project_path> -s final
# Default: generates native shapes (.pptx) + SVG reference (_svg.pptx)
```

**Prohibited**:
- NEVER use `cp` as a substitute for `finalize_svg.py`
- NEVER export directly from `svg_output/` — MUST export from `svg_final/` (use `-s final`)
- NEVER add extra flags like `--only`

**Re-run rule**: Any modification to `svg_output/` after post-processing has completed (including page revisions, additions, or deletions) requires re-running Steps 2 and 3. Step 1 only needs re-running if `notes/total.md` was also modified.

---

## 6. Shadow & Overlay Techniques

> `<mask>` elements and `<image opacity="...">` are banned. Always use stacked `<rect>` or gradient overlays instead (see §2).

### Shadow

#### Filter Soft Shadow — Recommended

Best for: cards, floating panels, elevated elements. The `svg_to_pptx` converter automatically converts `feGaussianBlur` + `feOffset` into native PPTX `<a:outerShdw>`.

```xml
<defs>
  <filter id="softShadow" x="-15%" y="-15%" width="140%" height="140%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="12"/>
    <feOffset dx="0" dy="6" result="offsetBlur"/>
    <feFlood flood-color="#000000" flood-opacity="0.15" result="shadowColor"/>
    <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
    <feMerge>
      <feMergeNode in="shadow"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
<rect x="60" y="60" width="400" height="240" rx="12" fill="#FFFFFF" filter="url(#softShadow)"/>
```

Recommended parameters:
```
stdDeviation:   10–16    (smaller = crisper, larger = softer)
flood-opacity:  0.12–0.20  (too low will be invisible in PPTX)
dy:             4–8      (vertical > horizontal for natural top-light)
dx:             0–2
```

#### Colored Shadow

Best for: accent buttons, brand-colored cards. Use the element's own color family instead of black.

```xml
<filter id="colorShadow" x="-15%" y="-15%" width="140%" height="140%">
  <feGaussianBlur in="SourceAlpha" stdDeviation="10"/>
  <feOffset dx="0" dy="6" result="offsetBlur"/>
  <feFlood flood-color="#1A73E8" flood-opacity="0.20" result="shadowColor"/>
  <feComposite in="shadowColor" in2="offsetBlur" operator="in" result="shadow"/>
  <feMerge>
    <feMergeNode in="shadow"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

Replace `flood-color` with the element's brand color; keep `flood-opacity` between 0.15–0.25.

#### Glow Effect

Best for: title highlights, key metrics, hero text. The converter automatically converts `feGaussianBlur` without `feOffset` into native PPTX `<a:glow>`.

```xml
<defs>
  <filter id="titleGlow" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="blur"/>
    <feFlood flood-color="#1A73E8" flood-opacity="0.45" result="glowColor"/>
    <feComposite in="glowColor" in2="blur" operator="in" result="glow"/>
    <feMerge>
      <feMergeNode in="glow"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>
<text x="640" y="360" text-anchor="middle" font-size="48" fill="#1A73E8" filter="url(#titleGlow)">Key Insight</text>
```

Recommended parameters:
```
stdDeviation:   4–8      (smaller = subtle, larger = prominent)
flood-color:    brand color or accent color (NOT black)
flood-opacity:  0.35–0.55  (stronger than shadow for visibility)
```

**Key difference from shadow**: No `<feOffset>` element (or dx=0/dy=0). The converter uses this to distinguish glow from shadow.

#### Layered Rect Shadow — High-Compatibility Fallback

Best for: maximum compatibility with older PowerPoint versions. Stack 2–3 semi-transparent rectangles behind the main card:

```xml
<!-- Shadow layers (back to front, largest offset first) -->
<rect x="68" y="72" width="400" height="240" rx="16" fill="#000000" fill-opacity="0.03"/>
<rect x="65" y="69" width="400" height="240" rx="14" fill="#000000" fill-opacity="0.05"/>
<rect x="62" y="66" width="400" height="240" rx="12" fill="#1A73E8" fill-opacity="0.04"/>
<!-- Main card -->
<rect x="60" y="60" width="400" height="240" rx="12" fill="#FFFFFF"/>
```

### Image Overlay

#### Linear Gradient Overlay — Most Common

Best for: image+text pages. Gradient direction should match text position (text on left → gradient darkens toward left).

```xml
<image href="..." x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>
<defs>
  <linearGradient id="imgOverlay" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#1A1A2E" stop-opacity="0.85"/>
    <stop offset="55%"  stop-color="#1A1A2E" stop-opacity="0.30"/>
    <stop offset="100%" stop-color="#1A1A2E" stop-opacity="0"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#imgOverlay)"/>
```

#### Bottom Gradient Bar

Best for: cover slides and full-image pages with bottom title.

```xml
<defs>
  <linearGradient id="bottomBar" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%"   stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.72"/>
  </linearGradient>
</defs>
<rect x="0" y="380" width="1280" height="340" fill="url(#bottomBar)"/>
```

#### Radial Gradient Overlay — Vignette Effect

Best for: full-screen atmosphere slides; draws attention to the center.

```xml
<defs>
  <radialGradient id="vignette" cx="50%" cy="50%" r="70%">
    <stop offset="0%"   stop-color="#000000" stop-opacity="0"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.58"/>
  </radialGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#vignette)"/>
```

#### Brand Color Overlay

Best for: slides needing strong visual brand identity.

```xml
<defs>
  <linearGradient id="brandOverlay" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%"   stop-color="#005587" stop-opacity="0.80"/>
    <stop offset="100%" stop-color="#005587" stop-opacity="0.10"/>
  </linearGradient>
</defs>
<rect x="0" y="0" width="1280" height="720" fill="url(#brandOverlay)"/>
```

### Quick-Reference Table

| Scenario | Recommended Technique | Avoid |
|----------|-----------------------|-------|
| Card / panel shadow | Filter soft shadow (`flood-opacity` ≤ 0.12) | Hard black shadow |
| Accent / CTA button | Colored shadow (same hue family) | Generic gray shadow |
| Title / metric highlight | Glow filter (brand color, no offset) | Overuse on body text |
| Text over image | Linear gradient overlay (direction matches text side) | Uniform flat opacity over whole image |
| Cover / full-image slide | Bottom gradient bar + brand color | Solid black overlay |
| Atmosphere / hero slide | Radial vignette | Unprocessed raw image |
| Max PPT compatibility needed | Layered rect shadow | Filter-based shadow |

---

## 7. Stroke, Text & Shape Effects

### stroke-dasharray — Dashed / Dotted Lines

Converts to native PPTX `<a:prstDash>`. Use preset patterns for best results:

| SVG Value | PPTX Preset | Best For |
|-----------|-------------|----------|
| `4,4` | Dash | General dashed lines, separators |
| `2,2` | Dot (sysDot) | Subtle dotted borders, placeholder outlines |
| `8,4` | Long dash | Timeline connectors, flow arrows |
| `8,4,2,4` | Long dash-dot | Technical drawings, dimension lines |

```xml
<rect x="60" y="60" width="400" height="240" rx="12"
  fill="none" stroke="#999999" stroke-width="2" stroke-dasharray="4,4"/>

<line x1="100" y1="360" x2="1180" y2="360"
  stroke="#CCCCCC" stroke-width="1" stroke-dasharray="2,2"/>
```

### stroke-linejoin

Controls how line segments join at corners. Supported values convert to native PPTX line join types:

| SVG Value | PPTX Equivalent | Best For |
|-----------|-----------------|----------|
| `round` | Round join | Smooth polyline charts, organic shapes |
| `bevel` | Bevel join | Technical diagrams |
| `miter` | Miter join (default) | Sharp-cornered rectangles, arrows |

```xml
<polyline points="100,200 200,100 300,200" fill="none"
  stroke="#1A73E8" stroke-width="3" stroke-linejoin="round"/>
```

### text-decoration

Supported text decorations convert to native PPTX text formatting:

| SVG Value | PPTX Equivalent | Best For |
|-----------|-----------------|----------|
| `underline` | Single underline | Emphasis, links, key terms |
| `line-through` | Strikethrough | Removed items, before/after comparisons |

```xml
<text x="100" y="200" font-size="20" fill="#333333" text-decoration="underline">Important Term</text>

<!-- Per-tspan decoration -->
<text x="100" y="240" font-size="18" fill="#333333">
  Regular text <tspan text-decoration="line-through" fill="#999999">old value</tspan> new value
</text>
```

### Gradient Fill — linearGradient & radialGradient

Gradients defined in `<defs>` and referenced via `fill="url(#id)"` convert to native PPTX `<a:gradFill>`. Use them as shape fills (not just overlays) for polished surfaces.

**Linear gradient** — best for buttons, header bars, background panels:

```xml
<defs>
  <linearGradient id="btnGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#1A73E8"/>
    <stop offset="100%" stop-color="#0D47A1"/>
  </linearGradient>
</defs>
<rect x="540" y="600" width="200" height="48" rx="24" fill="url(#btnGrad)"/>
```

**Radial gradient** — best for spotlight backgrounds, circular accents:

```xml
<defs>
  <radialGradient id="spotBg" cx="50%" cy="50%" r="70%">
    <stop offset="0%" stop-color="#1A73E8" stop-opacity="0.15"/>
    <stop offset="100%" stop-color="#1A73E8" stop-opacity="0"/>
  </radialGradient>
</defs>
<circle cx="640" cy="360" r="300" fill="url(#spotBg)"/>
```

### transform: rotate — Element Rotation

Rotation converts to native PPTX `<a:xfrm rot="...">`. Supported on all element types: `rect`, `circle`, `ellipse`, `line`, `path`, `polygon`, `polyline`, `image`, and `text`.

```xml
<!-- Rotated decorative element -->
<rect x="100" y="100" width="60" height="60" fill="#1A73E8" fill-opacity="0.1"
  transform="rotate(45, 130, 130)"/>

<!-- Rotated text label -->
<text x="50" y="400" font-size="14" fill="#999999"
  transform="rotate(-90, 50, 400)">Y-Axis Label</text>
```

**Syntax**: `rotate(angle)` or `rotate(angle, cx, cy)` where `cx,cy` is the rotation center. Positive angles rotate clockwise.

### Arc Paths — Donut / Pie Charts

When drawing donut or pie chart sectors with `<path>`, the arc endpoint coordinates must be calculated precisely using trigonometry. **Never estimate or approximate arc endpoints** — even small errors produce wildly incorrect shapes.

**Calculation formula** (center `cx,cy`, radius `r`, angle `θ` in degrees):
```
x = cx + r × cos(θ × π / 180)
y = cy + r × sin(θ × π / 180)
```

**Key rules**:
1. Start at **-90°** (12 o'clock position) and go clockwise
2. Each sector spans `percentage × 360°`
3. Use **large-arc flag = 1** when the sector is > 180°, **0** otherwise
4. sweep-direction = 1 (clockwise) for outer arc, 0 (counter-clockwise) for inner arc returning
5. **Always verify** that the sum of all sector angles equals 360° and that the last sector's end point matches the first sector's start point

**Example — 75% donut sector** (center 400,400, outer r=180, inner r=100):
```
Start angle: -90°    → outer(400, 220), inner(400, 300)
End angle: -90+270=180° → outer(220, 400), inner(300, 400)
Large-arc flag: 1 (270° > 180°)

<path d="M 400,220 A 180,180 0 1,1 220,400 L 300,400 A 100,100 0 1,0 400,300 Z"/>
```

### Polygon Arrows on Diagonal Lines

When using `<polygon>` triangles as arrowheads (since `marker-end` is banned), arrows on **horizontal or vertical lines** can use simple point offsets. But arrows on **diagonal lines** must have their triangle vertices rotated to match the line direction.

**Method**: Calculate the triangle points using the line's direction vector:

```
Given line from (x1,y1) to (x2,y2):
1. Direction vector: dx = x2-x1, dy = y2-y1
2. Normalize: len = √(dx²+dy²), ux = dx/len, uy = dy/len
3. Perpendicular: px = -uy, py = ux
4. Arrow tip = (x2, y2)
5. Back point 1 = (x2 - ux×12 + px×5,  y2 - uy×12 + py×5)
6. Back point 2 = (x2 - ux×12 - px×5,  y2 - uy×12 - py×5)
```

**Example — diagonal line** from (260,310) to (370,430):
```
dx=110, dy=120, len≈162.8, ux=0.676, uy=0.737
px=-0.737, py=0.676
Tip: (370, 430)
Back1: (370-8.1-3.7, 430-8.8+3.4) = (358.2, 424.6)
Back2: (370-8.1+3.7, 430-8.8-3.4) = (365.6, 417.8)

<polygon points="370,430 365.6,417.8 358.2,424.6" fill="#C8A96E"/>
```

⚠️ **Never use a fixed downward/rightward triangle on a diagonal line** — the arrow will point in the wrong direction.

---

## 8. Project Directory Structure

```
project/
├── svg_output/    # Raw SVGs (Executor output, contains placeholders)
├── svg_final/     # Post-processed final SVGs (finalize_svg.py output)
├── images/        # Image assets (user-provided + AI-generated)
├── notes/         # Speaker notes (.md files matching SVG names)
│   └── total.md   # Complete speaker notes document (before splitting)
├── templates/     # Project templates (if any)
└── *.pptx         # Exported PPT file
```
