# Canvas Format Specification

> See [`shared-standards-core.md`](./shared-standards-core.md) §4.1 for the normative root `viewBox` grammar, compatibility spellings, and fail-closed validation rules.

## Format Quick Reference

| ID | Format | Size | viewBox | Ratio | Use Case |
|----|--------|------|---------|-------|----------|
| `ppt169` | PPT 16:9 | `1280x720` | `0 0 1280 720` | 16:9 | Business presentations, meetings, modern devices |
| `ppt43` | PPT 4:3 | `1024x768` | `0 0 1024 768` | 4:3 | Traditional projectors, academic talks |
| `xiaohongshu` | Xiaohongshu (RED) | `1242x1660` | `0 0 1242 1660` | 3:4 | Image-text sharing, knowledge posts |
| `moments` | WeChat Moments / IG | `1080x1080` | `0 0 1080 1080` | 1:1 | Square posters, brand showcases |
| `story` | Story / TikTok | `1080x1920` | `0 0 1080 1920` | 9:16 | Vertical stories, short video covers |
| `wechat` | WeChat Article Header | `900x383` | `0 0 900 383` | 2.35:1 | WeChat article cover images |
| `banner` | Landscape Banner | `1920x1080` | `0 0 1920 1080` | 16:9 | Web banners, digital screens |
| `a4` | A4 Print | `1240x1754` | `0 0 1240 1754` | 1:sqrt(2) | Print posters, flyers |

Custom canvases likewise use `0 0 W H` with positive integer pixels; a fractional positive canvas is accepted only as compatible input for an imported custom PowerPoint slide size. All pages and internal Layout prototypes in one export share the same numeric canvas within PowerPoint's supported slide range (914,400–51,206,400 EMU per side, about 96–5,376 SVG px). `ppt169` is exactly `1280x720`; same-ratio canvases such as `banner` are different coordinate systems.

```xml
<svg viewBox="0 0 1280 720">   <!-- PPT 16:9 -->
<svg viewBox="0 0 1080 1920">  <!-- Story -->
```

## Platform Keep-clear

Canvas dimensions imply no title band, content topology, or recurring chrome; reserve space only for a real output obstruction. For `story`, keep meaning-bearing text, identity, and calls to action within `y=120..1740` by default because mobile story controls occupy the top and bottom; images, backgrounds, and texture may stay full bleed. An exact target-platform overlay guide or installed template overrides this advisory band.

## Typography Scale Start

**Hard rule — normative owner**: this section owns the initial body-size anchor and sanity band for every registered or custom canvas. Strategist and Quick consume it directly; Confirm UI maintains an exact executable mirror and must not infer alternate canvas classes or values. Values are unitless SVG px.

| Canvas | Reading mode | Advisory body band | Initial body |
|---|---|---:|---:|
| `ppt169` / `ppt43` | `text` | 18–21 | 20 |
| `ppt169` / `ppt43` | `balanced` | 22–25 | 24 |
| `ppt169` / `ppt43` | `presentation` | 28–32 | 32 |

Non-PPT registered and custom canvases derive one effective span from `W x H`:

```text
short = min(W, H); long = max(W, H); span = min(long, 3 * short)
low = round(span * 0.025); start = round(span * 0.029); high = round(span * 0.033)
```

| Canvas | Effective span | Advisory body band | Initial body |
|---|---:|---:|---:|
| `wechat` | 900 | 23–30 | 26 |
| `moments` | 1080 | 27–36 | 31 |
| `xiaohongshu` | 1660 | 42–55 | 48 |
| `story` / `banner` | 1920 | 48–63 | 56 |
| `a4` | 1754 | 44–58 | 51 |

**Default — starting anchor, not a floor (may override when confirmed identity, source fidelity, or target viewing conditions require it)**: start from the table or formula, then resolve the complete role ramp and page density from the content and delivery context. The band only surfaces unusual values; falling outside it is not a validation failure. Apply the viewing-distance baseline in [`shared-standards-core.md`](./shared-standards-core.md) instead of silently shrinking a recurring role to make content fit.
