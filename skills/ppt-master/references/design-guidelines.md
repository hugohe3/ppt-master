> See shared-standards.md for common technical constraints.

# Design Guidelines

Detailed design guidelines and best practices for the PPT Master system.

---

## Color System

### Primary Color Selection

#### Consulting Style

```
Deloitte Blue:   #0076A8  - Professional, reliable
McKinsey Blue:   #005587  - Authoritative, deep
BCG Dark Blue:   #003F6C  - Stable, trustworthy
PwC Orange:      #D04A02  - Energetic, innovative
EY Yellow:       #FFE600  - Optimistic, clear
```

#### General Versatile Style

```
Tech Blue:       #2196F3  - Modern, innovative
Vibrant Orange:  #FF9800  - Passionate, positive
Growth Green:    #4CAF50  - Healthy, growth
Professional Purple: #9C27B0  - Creative, premium
Alert Red:       #F44336  - Urgent, important
```

### Secondary Colors

#### Data Visualization Colors

```
Positive trend (green):
  Dark: #2E7D32 | Medium: #4CAF50 | Light: #81C784

Warning trend (yellow):
  Dark: #F57C00 | Medium: #FFA726 | Light: #FFD54F

Negative trend (red):
  Dark: #C62828 | Medium: #EF5350 | Light: #E57373
```

#### Neutral Colors

```
Text hierarchy:
  Primary text:   #212121  (black, 87% opacity)
  Secondary text: #757575  (gray, 60% opacity)
  Tertiary text:  #9E9E9E  (light gray, 38% opacity)

Background hierarchy:
  Primary bg:     #FFFFFF
  Secondary bg:   #F5F5F5
  Card bg:        #FAFAFA
  Border:         #E0E0E0
```

### Contrast Requirements

Following WCAG 2.1 AA standards:
- Body text: at least 4.5:1
- Large text (24px+): at least 3:1
- Important data: at least 7:1 (AAA level)

---

## Typography Specification

### Font Hierarchy

> Use body font size as 1x baseline; derive other levels proportionally. Font size selection depends on content density, not design style.

#### Relaxed Content (body baseline 24px)

Suitable for: Keynote-style PPTs, training materials, few points per page (3-5)

```
H1 - Cover title:      60-72px, Bold     (2.5-3x)
H2 - Page title:       42-48px, Bold     (1.75-2x)
H3 - Section title:    32-36px, SemiBold (1.3-1.5x)
Body - Main content:   24px, Regular     (1x baseline)
Small - Annotations:   18-20px, Regular  (0.75-0.85x)
```

#### Dense Content (body baseline 18px)

Suitable for: Data reports, consulting analysis, many points per page (6+)

```
H1 - Cover title:      45-54px, Bold     (2.5-3x)
H2 - Page title:       27-36px, Bold     (1.5-2x)
H3 - Section title:    22-27px, SemiBold (1.2-1.5x)
Body - Main content:   18px, Regular     (1x baseline)
Small - Annotations:   14-15px, Regular  (0.75-0.85x)
```

### Font Selection

#### Chinese Fonts

| Category | Code | Options | Suitable Scenarios |
|----------|:----:|---------|-------------------|
| Sans-serif | A | Microsoft YaHei, SimHei, YouYuan, STXihei | Modern business, body text (default) |
| Serif | B | SimSun, NSimSun, FangSong, STSong | Government docs, formal reports |
| Calligraphic | C | KaiTi, STKaiti, STXingkai | Culture, arts, humanities |
| Display | D | SimHei, STZhongsong, Source Han Sans Bold | Large titles, emphasis |
| Handwritten | E | STXingkai, STXinwei, LiSu | Creative, personalized |

#### English Fonts

| Category | Code | Options | Suitable Scenarios |
|----------|:----:|---------|-------------------|
| Sans-serif modern | F | Arial, Calibri, Segoe UI, Helvetica | Modern business (default) |
| Serif classic | G | Times New Roman, Georgia, Cambria | Formal documents, academic |
| Display | H | Impact, Arial Black, Bebas Neue | Large titles, posters |
| Handwritten | I | Comic Sans MS, Segoe Script, Ink Free | Casual, playful |
| Monospace | J | Consolas, Cascadia Code, Courier New | Data, code |

#### Recommended font-family

```css
/* Chinese fonts */
"Microsoft YaHei", sans-serif               /* A: Microsoft YaHei */
"SimHei", sans-serif                        /* A/D: SimHei */
"SimSun", serif                             /* B: SimSun */
"FangSong", serif                           /* B: FangSong */
"KaiTi", serif                              /* C: KaiTi */
"STXingkai", cursive                        /* C/E: STXingkai */

/* English fonts */
"Arial", sans-serif                         /* F: Arial */
"Calibri", sans-serif                       /* F: Calibri */
"Times New Roman", serif                    /* G: Times */
"Georgia", serif                            /* G: Georgia */
"Impact", sans-serif                        /* H: Impact */
"Consolas", monospace                       /* J: Monospace */
```

#### Chinese-English Mixed Typesetting Recommendations

| Scenario | Chinese Font | English Font |
|----------|-------------|-------------|
| Modern business | Microsoft YaHei (A) | Calibri / Arial (F) |
| Government docs | SimSun (B) | Times New Roman (G) |
| Culture & arts | KaiTi (C) | Georgia (G) |
| Tech / Internet | SimHei (D) | Segoe UI (F) |

#### Font Roles

| Role | Purpose | Chinese Recommended | English Recommended |
|------|---------|--------------------|--------------------|
| Title font | H1/H2 large titles | A/C/D/E | F/G/H |
| Body font | Paragraphs, bullet points | A/B | F/G |
| Emphasis font | KPIs, keywords | D | H/J |
| Annotation font | Footnotes, captions | A/B | F/G |

### Line Height and Spacing

```
Title line height: 1.2-1.3
Body line height: 1.5-1.6
Paragraph spacing: 1.5-2em
List spacing: 0.5-1em
```

### Text Wrapping & Flattening

- Generation phase: Use `<tspan>` for manual line breaks, control line start and spacing via `x`/`dy`
- Post-processing: Use `python3 scripts/finalize_svg.py <project_path>`, includes text flattening
- Verification: Compare `svg_output` with `svg_final`; check line order, styles, and positioning match; target files should not contain residual `<tspan>`

---

## Layout Principles

### 16:9 Canvas Specification

```
Canvas size: 1280x720px
Safe area: 1200x640px (40px margins)
Title area:    1200x100px
Content area:  1200x500px
Footer area:   1200x40px
```

### Grid System

#### Single Column Layout
```
Suitable for: Covers, ending pages, single topics
Content width: 800-1000px, horizontally centered
```

#### Two-Column Layout
```
Suitable for: Comparative analysis, left-image right-text
Column ratio: 1:1 or 3:2, column gap: 40-60px
```

#### Three-Column Layout
```
Suitable for: Parallel points, process steps
Column ratio: 1:1:1, column gap: 30-40px
```

#### Four-Quadrant Layout
```
Suitable for: Matrix analysis, classification display
Quadrant size: 560x250px (including gap), gap: 20-30px
```

### Card Design

#### Dimension Specifications (Mandatory)

```
Single-row card: height 530-600px
Double-row card: each row 265-295px
Three-column card: each column width 360-380px
```

#### Internal Padding

```
Title area: 20-30px
Content area: 30-40px
Chart area: 20-30px
```

#### Border Radius

```
Small cards: 8-12px
Large cards: 12-16px
Charts: 8px
Buttons: 6-8px
```

---

## Image Layout Specification

Pages with images need dynamic layout calculation based on image ratio. See image-layout-spec.md for details.

**Quick rules**:
- Ratio > 2.0 (ultra-wide) → Top-bottom layout
- Ratio 1.5-2.0 (wide) → Prefer top-bottom; switch to left-right if text area insufficient
- Ratio 1.2-1.5 (standard landscape) → Left-right layout
- Ratio 0.8-1.2 (square) → Left-right layout
- Ratio < 0.8 (portrait) → Left-right layout

---

## Chart Design

### Common Chart Types

#### KPI Cards
```
Layout: 2x2 or 1x4
Elements: Large number (48-56px) + metric name (18-20px) + trend icon/percentage + YoY/MoM note
```

#### Bar Charts
```
Bar count: 3-8, bar width: 40-60px, gap: 50-80% of bar width, show data labels
```

#### Line Charts
```
Line: 2-3px, data points: circle radius 4-6px, grid lines: 1px light gray, legend: top-right or bottom
```

#### Pie/Donut Charts
```
Segments: 3-6, start angle: -90° (12 o'clock), ring width: 40-60px, show percentage labels
```

#### Matrix Charts
```
2x2 layout, axis lines: 2px solid, quadrant labels clear, data point sizes uniform
```

### Chart Colors

| Scheme | Suitable Scenarios | Example |
|--------|-------------------|---------|
| Monochromatic gradient | Same-category data comparison | #1976D2 → #42A5F5 → #90CAF9 |
| Contrasting set | Different category data | #2196F3 / #FF9800 / #4CAF50 |
| Sequential | Level/intensity display | #4CAF50 → #FFC107 → #F44336 |

---

## Icon Usage

### Built-in Icon Library (Recommended)

Located in `templates/icons/`, containing 640+ SVG icons.

```
Full index: templates/icons/FULL_INDEX.md
Programmatic query: templates/icons/icons_index.json
Usage guide: templates/icons/README.md
```

**Category overview**:
- General: home, settings, search, user, calendar, mail...
- Data: trending-up, chart-bar, database, file-text...
- Business: rocket, target, lightbulb, trophy, star...
- Arrows: arrow-right/left/up/down, chevron-right...
- Status: check, check-circle, x-circle, alert-circle...
- Tools: edit, trash, download, upload, share...

### Icon Specifications

```
Size: Small 16-20px | Regular 24-32px | Large 40-48px
Stroke width: 2px (uniform)
Color: Coordinate with primary color
Spacing: 50% of icon size
```

---

## Common Patterns

### Cover Page
- Top: Company logo (optional), Center: Presentation title (H1), subtitle, Bottom: Date, presenter
- Clean and impressive; primary color background or image; text centered or left-aligned

### Content Page
- Standard structure: Page title (H2) → Main content → Page number / notes
- Variants: Left-title right-content, top-bottom split, multi-column layout

### Data Page
- Data visualization as primary; highlight key numbers; provide data sources; add trend notes
- Layouts: Large chart + key points, multiple small chart combinations, KPI dashboard

### Summary Page
- 3-5 core takeaways + Call to Action (CTA) + Next steps
- Lists or numbering, icon-assisted, clean and clear

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Too much content to fit | Split across pages, use smaller font (>=16px), condense text, use charts instead |
| Colors don't match | Limit primary colors to <=3, increase neutral color proportion, reference successful cases |
| Unbalanced layout | Check alignment, adjust spacing, use grid system, balance visual weight |
