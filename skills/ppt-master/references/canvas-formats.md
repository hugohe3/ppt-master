# Canvas Format Specification

> See [`shared-standards.md`](shared-standards.md) §4.1 for the normative root
> `viewBox` grammar, compatibility spellings, and fail-closed validation rules.

## Format Quick Reference

| ID | Format | Size | viewBox | Ratio | Use Case |
|----|--------|------|---------|-------|----------|
| `ppt169` | PPT 16:9 | `1280x720` | `0 0 1280 720` | 16:9 | Business presentations, meetings |
| `ppt43` | PPT 4:3 | `1024x768` | `0 0 1024 768` | 4:3 | Traditional projectors, academic talks |
| `xiaohongshu` | Xiaohongshu (RED) | `1242x1660` | `0 0 1242 1660` | 3:4 | Image-text sharing, knowledge posts |
| `moments` | WeChat Moments / IG | `1080x1080` | `0 0 1080 1080` | 1:1 | Square posters, brand showcases |
| `story` | Story / TikTok | `1080x1920` | `0 0 1080 1920` | 9:16 | Vertical stories, short video covers |
| `wechat` | WeChat Article Header | `900x383` | `0 0 900 383` | 2.35:1 | WeChat article cover images |
| `banner` | Landscape Banner | `1920x1080` | `0 0 1920 1080` | 16:9 | Web banners, digital screens |
| `a4` | A4 Print | `1240x1754` | `0 0 1240 1754` | 1:sqrt(2) | Print posters, flyers |

The table lists canonical root spellings. New custom canvases likewise use
`0 0 W H` with positive integer pixels. A fractional positive canvas is accepted
only as compatible input for an imported custom PowerPoint slide size; it is not
the default authoring form. All pages and internal Layout prototypes in one
export use the same numeric canvas and stay within PowerPoint's supported slide
range (914,400–51,206,400 EMU per side, approximately 96–5,376 SVG px).

`ppt169` is the canonical PPT wide-screen canvas in this repo: `1280x720`, not any arbitrary 16:9 size. Same-ratio canvases such as `banner` (`1920x1080`) must be treated as different coordinate systems.

## Format Selection Decision Tree

```
Content purpose?
├── Presentation
│   ├── Modern devices → PPT 16:9 (1280x720)
│   └── Traditional devices → PPT 4:3 (1024x768)
├── Social sharing
│   ├── Xiaohongshu (RED) → 1242x1660
│   ├── WeChat Moments / IG → 1080x1080
│   └── Story / TikTok → 1080x1920
└── Marketing materials
    ├── WeChat Article Header → 900x383
    ├── Banner → 1920x1080
    └── Print → 1240x1754
```

## Layout Principles

### Landscape (16:9, 4:3, 2.35:1)
- Visual flow: Z-pattern, left to right
- Margins: 40-80px
- Layouts: multi-column, left-right split, grid
- Card dimensions (16:9): single-row 530-600px, double-row 265-295px

### Portrait (3:4, 9:16)
- Visual flow: top to bottom
- Margins: 60-120px
- Layouts: single-column, top-bottom split, card stacking
- Card dimensions (3:4): height 400-600px, gap 40-60px

### Square (1:1)
- Visual flow: center-radiating
- Margins: 60-100px
- Core area: ~800x800px

## Format-specific Design

| Format | Title Area | Content Area | Special Notes |
|--------|-----------|--------------|---------------|
| PPT | 80-100px | Full width utilization | Page number bottom-right |
| Xiaohongshu (RED) | 180-240px (bold) | Generous top/bottom whitespace | Brand area at bottom 120-160px |
| WeChat Moments | 200-280px | Center 500-600px | QR code area at bottom 150-200px |
| Story | — | Middle 1500px | Top safe zone 120px, bottom 180px |
| WeChat Article Header | Center/left-aligned 48-72px | — | Image on right or as background |

> **Body font baseline scales with canvas and reading mode** — a PPT 16:9 baseline confirmed for read-close / business / projection cannot be carried onto tall canvases (Xiaohongshu / Story / A4). Pick the baseline from the confirmed canvas, not the recommended one; see the per-canvas px anchors in [`strategist.md`](strategist.md) §g "Font Size Ramp" (the system is px-only — all sizes are unitless px on every canvas).

## ViewBox Examples

```xml
<svg width="1280" height="720" viewBox="0 0 1280 720">   <!-- PPT 16:9 -->
<svg width="1242" height="1660" viewBox="0 0 1242 1660"> <!-- Xiaohongshu -->
<svg width="1080" height="1080" viewBox="0 0 1080 1080"> <!-- WeChat Moments -->
<svg width="1080" height="1920" viewBox="0 0 1080 1920"> <!-- Story -->
<svg width="900" height="383" viewBox="0 0 900 383">     <!-- WeChat Article Header -->
```
