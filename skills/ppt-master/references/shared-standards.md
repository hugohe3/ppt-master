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
- **Icon placeholders**: `<use data-icon="icon-name" x="" y="" width="48" height="48" fill="#HEX"/>` (auto-embedded during post-processing)

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
- After Optimizer optimization, re-run all three steps

---

## 6. Project Directory Structure

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
