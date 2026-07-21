> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# SVG Image Embedding Guide

Technical spec and workflow for adding images to SVG files.

---

## Image Resource List Format

Defined in the Design Specification & Content Outline; each image carries an `Acquire Via` field plus a status annotation. This file is authoritative for status names and SVG embedding behavior. If image approach includes "B) User-provided": run `analyze_images.py` right after the Strategist confirmation stage and complete the list before outputting the design spec.

```markdown
| Filename | Dimensions | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference |
|----------|------------|---------|------|----------------|-------------|-------------|--------|-----------|
| team.jpg | 800x600 | Team photo | Photography | `#2 left-third` | adaptive | web | Pending | Diverse engineering team in modern office |
| formula_001.png | 736x168 | Page 3 block equation | Latex Formula | formula | no-crop | formula | Rendered | `E = mc^2` |
```

### Image Status Enum

| Status | Meaning | Executor Handling |
|--------|---------|-------------------|
| **Pending** | Acquisition needed (`Acquire Via: ai` / `web`) or derivation needed (`Acquire Via: slice`); not yet attempted | Image Acquisition Phase (Step 5) consumes this; must not remain after Step 5 |
| **Generated** | AI-generated file exists at expected path, or sliced element file exists at expected path | Reference from `../images/`; no on-slide credit needed. **Exception**: an `Illustration Sheet` row is only a slice source — it lives in §VIII but never in `spec_lock.md images`, so the Executor never places it |
| **Sourced** | Web-sourced file exists at expected path | Reference from `../images/`; check `image_sources.json` for `license_tier` — if `attribution-required`, render an inline credit element on the slide (see [`executor-web-image.md`](./executor-web-image.md) §1 and [`image-searcher.md`](./image-searcher.md) §7 for the visual spec) |
| **Rendered** | Deterministic formula PNG exists at expected path (`Acquire Via: formula`) | Reference from `../images/`; use `preserveAspectRatio="xMidYMid meet"` and do not crop |
| **Needs-Manual** | Acquisition attempted once + one retry, failed; for `slice`, parent sheet is unavailable | Dashed placeholder unless user has manually supplied the file. For `slice` rows, place the parent sheet and rerun `slice_images.py`; do not hand-place individual element files |
| **Existing** | User already has image (`Acquire Via: user`) | Place in `images/`, reference with `<image>` |
| **Placeholder** | Intentionally not prepared yet (`Acquire Via: placeholder`) | Dashed border placeholder; replace later |

---

## Workflow

```
1. Strategist defines image needs → Add image resource list with Acquire Via + Status per row
2. Image Acquisition (Step 5):
   - Pending + ai  → Image_Generator runs image_gen.py     → Generated
   - Pending + web → Image_Searcher runs image_search.py   → Sourced
   - Pending + slice → after parent AI sheet is Generated, slice_images.py cuts element files → Generated
   - formula / user / placeholder rows are skipped
3. Executor generates SVGs (svg_output/)
   ├── Existing / Generated → <image href="../images/xxx.png" .../>
   ├── Sourced + license_tier=no-attribution → <image href=...> only
   ├── Sourced + license_tier=attribution-required → <image href=...> + small <text> credit element on the slide
   ├── Sourced + license_tier=manual → <image href=...> only (user-supplied --from-url; rights/credit are user responsibility)
   ├── Rendered formula → <image href="../images/formula_001.png" preserveAspectRatio="xMidYMid meet" .../>
   └── Placeholder / Needs-Manual without file → Dashed border + description text
4. Preview: python3 -m http.server -d <project_path> 8000 → /svg_output/<filename>.svg
5. Post-processing & Export → follow [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7
```

> Keep external references in `svg_output/` during generation. `finalize_svg.py` auto-embeds images into the mandatory `svg_final/` visual preview; native PPTX export independently reads `svg_output/`.

**Hard rule — export boundary**: `svg_final/` is a self-contained SVG preview for embeddable raster/SVG assets and may be manually inserted into PowerPoint as an SVG picture. EMF/WMF assets retain the documented external-reference exception for lossless native passthrough. The only supported generated-PPTX route is `svg_output/` through the project SVG-to-DrawingML converter. PowerPoint's manual Convert-to-Shape operation is unsupported.

---

## External Reference vs Base64 Embedding

| Method | Pros | Cons | Suitable For |
|--------|------|------|-------------|
| **External reference** | Small file size, fast iteration, easy to replace | Preview requires HTTP server from project root | `svg_output/` development phase |
| **Base64 embedding** | Self-contained file, stable direct preview / SVG-picture insertion | Large file size | `svg_final/` preview phase |

---

## Method 1: External Reference (Recommended for Generation Phase)

### Syntax

```xml
<image href="../images/image.png" x="0" y="0" width="1280" height="720"
       preserveAspectRatio="xMidYMid slice"/>
```

### Key Attributes

| Attribute | Description | Example |
|-----------|-------------|---------|
| `href` | Image path (relative or absolute) | `"../images/cover.png"` |
| `x`, `y` | Image top-left corner position | `x="0" y="0"` |
| `width`, `height` | Image display dimensions | `width="1280" height="720"` |
| `preserveAspectRatio` | Scaling mode | `"xMidYMid slice"` |

### preserveAspectRatio Common Values

| Value | Effect |
|-------|--------|
| `xMidYMid slice` | Center crop (similar to CSS `cover`) |
| `xMidYMid meet` | Complete display (similar to CSS `contain`) |
| `none` | Stretch to fill, no aspect ratio preservation |

### Preview Method

Browser security blocks external images on directly opened SVGs. Serve via HTTP from the project root:

```bash
python3 -m http.server -d <project_path> 8000
# Visit http://localhost:8000/svg_output/your_file.svg
```

---

## Method 2: Base64 Embedding (Recommended for Preview Phase)

### Syntax

```xml
<image href="data:image/png;base64,iVBORw0KGgo..." x="0" y="0" width="1280" height="720"/>
```

### MIME Types

| MIME Type | File Format |
|-----------|-------------|
| `image/png` | PNG |
| `image/jpeg` | JPG/JPEG |
| `image/gif` | GIF |
| `image/webp` | WebP |
| `image/svg+xml` | SVG |

---

## Conversion Process

Follow [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7; it owns the
serial post-processing and export commands. Its mandatory finalization step
embeds image references into the self-contained `svg_final/` preview, while the
supported native PPTX release still reads `svg_output/` and maps it directly to
DrawingML.

### Standalone: align_embed_images.py (advanced)

For processing specific SVGs without the full pipeline:

```bash
python3 scripts/svg_finalize/align_embed_images.py <svg_file>
python3 scripts/svg_finalize/align_embed_images.py --dry-run <svg_file>
```

Use `finalize_svg.py --only align-images` for project-level batches. The old
`crop-images`, `fix-aspect`, and `embed-images` step names are compatibility
aliases only when invoked through `finalize_svg.py --only`.

---

## Best Practices

### Image Optimization

Compress before embedding to reduce file size:

```bash
convert input.png -quality 85 -resize 1920x1080\> output.png  # ImageMagick
pngquant --quality=65-80 input.png -o output.png               # pngquant (recommended)
```

### File Organization

```
project/
├── images/            # Image assets
├── sources/           # Source files and their accompanying images
│   └── article_files/
├── svg_output/        # Raw version (external references)
└── svg_final/         # Derived self-contained visual preview (images embedded)
```

### Rounded Corner / Non-rectangular Image Cropping

`clipPath` **on `<image>` elements** is conditionally allowed — authoritative constraints in [`shared-standards-core.md`](./shared-standards-core.md) §1.2; do not restate or relax here.

Fallback when `clipPath` doesn't fit: bake rounded corners into the source image (PNG with alpha) before embedding.

---

## FAQ

**Q: Can't see images when opening SVG directly?**
Browser security blocks cross-directory requests. Serve via HTTP from project root, or run `finalize_svg.py` first and view from `svg_final/`.

**Q: Base64 file too large?**
Compress the source, use JPEG, reduce resolution to match actual display dimensions.

**Q: How to reverse-extract a Base64 image?**
```bash
base64 -d image.b64 > image.png
```
