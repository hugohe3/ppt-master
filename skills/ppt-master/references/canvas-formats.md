# Canvas Format Specification

> See [`shared-standards-core.md`](./shared-standards-core.md) §4.1 for the normative root
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

## Platform Keep-clear

Canvas dimensions do not imply a title band, content topology, or recurring
chrome. Reserve space only for a real output obstruction. For `story`, keep
meaning-bearing text, identity, and calls to action within `y=120..1740` by
default because common mobile story controls occupy the top and bottom; images,
backgrounds, and nonessential texture may remain full bleed. An exact target-
platform overlay guide or installed template overrides this advisory band.

## Typography Scale Start

**Hard rule — normative owner**: This section owns the initial body-size anchor
and sanity band for every registered or custom canvas. Strategist and Quick
consume it directly. Confirm UI maintains an exact executable mirror and must
not infer alternate canvas classes or values. All values are unitless SVG px.

**PPT reading modes**:

| Canvas | Reading mode | Advisory body band | Initial body |
|---|---|---:|---:|
| `ppt169` / `ppt43` | `text` | 18–21 | 20 |
| `ppt169` / `ppt43` | `balanced` | 22–25 | 24 |
| `ppt169` / `ppt43` | `presentation` | 28–32 | 32 |

**Non-PPT registered and custom canvases**: derive one effective canvas span
from the canonical or custom `W x H`, then calculate the advisory band and
initial body anchor:

```text
short = min(W, H)
long = max(W, H)
span = min(long, 3 * short)
low = round(span * 0.025)
start = round(span * 0.029)
high = round(span * 0.033)
```

| Canvas | Effective span | Advisory body band | Initial body |
|---|---:|---:|---:|
| `wechat` | 900 | 23–30 | 26 |
| `moments` | 1080 | 27–36 | 31 |
| `xiaohongshu` | 1660 | 42–55 | 48 |
| `story` | 1920 | 48–63 | 56 |
| `banner` | 1920 | 48–63 | 56 |
| `a4` | 1754 | 44–58 | 51 |

**Default — starting anchor, not a floor (may override when confirmed identity,
source fidelity, or target viewing conditions require it)**: Start from the
table or formula, then resolve the complete role ramp and page density from the
active content and delivery context. The advisory band only surfaces unusual
values; falling outside it is not a validation failure. Apply the
viewing-distance baseline in
[`shared-standards-core.md`](./shared-standards-core.md) instead of silently
shrinking a recurring role to make content fit.

## ViewBox Examples

```xml
<svg width="1280" height="720" viewBox="0 0 1280 720">   <!-- PPT 16:9 -->
<svg width="1242" height="1660" viewBox="0 0 1242 1660"> <!-- Xiaohongshu -->
<svg width="1080" height="1080" viewBox="0 0 1080 1080"> <!-- WeChat Moments -->
<svg width="1080" height="1920" viewBox="0 0 1080 1920"> <!-- Story -->
<svg width="900" height="383" viewBox="0 0 900 383">     <!-- WeChat Article Header -->
```
