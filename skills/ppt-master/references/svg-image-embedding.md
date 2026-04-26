> See shared-standards.md for common technical constraints.

# SVG Image Embedding Guide

Technical specifications and recommended workflow for adding images to SVG files.

---

## Image Resource List Format

Defined in the Design Specification & Content Outline; each image has a status annotation. This file is the authority for image status names and SVG image embedding behavior. If the image approach includes "B) User-provided", run `analyze_images.py` immediately after the Strategist completes the Eight Confirmations, and complete the list before outputting the design spec.

```markdown
| Filename | Dimensions | Purpose | Type | Status | Generation Description |
|----------|------------|---------|------|--------|------------------------|
| cover_bg.png | 1280x720 | Cover background | Background | Pending | Modern tech abstract background, deep blue gradient |
| product.png | 600x400 | Page 3 product photo | Photography | Existing | - |
| team.png | 600x400 | Page 5 team scene | Illustration | Placeholder | Team collaboration scene to be added later |
```

### Image Status Enum

| Status | Meaning | Executor Handling |
|--------|---------|-------------------|
| **Pending** | Needs AI generation, has a generation description | Image_Generator must attempt generation before Executor; should not remain in the list after Step 5 |
| **Generated** | AI-generated file exists at the expected path | Reference directly from `../images/` |
| **Needs-Manual** | Generation was attempted once plus one retry and failed | Use a dashed placeholder unless the user has manually supplied the expected file |
| **Existing** | User already has image | Place in `images/`, reference with `<image>` |
| **Placeholder** | Image intentionally not prepared yet | Use dashed border placeholder; replace later |

---

## Workflow

```
1. Strategist defines image needs → Add image resource list, annotate each status
2. Image preparation (Pending / Existing) → Place available files in project/images/
3. Executor generates SVGs (svg_output/)
   ├── Existing / Generated → <image href="../images/xxx.png" .../>
   └── Placeholder / Needs-Manual without file → Dashed border + description text
4. Preview: python3 -m http.server -d <project_path> 8000 → /svg_output/<filename>.svg
5. Post-processing & Export → follow shared-standards.md §5
```

> Recommended: During generation, keep external references in `svg_output/`. Post-processing via `finalize_svg.py` auto-embeds images into `svg_final/`, then export PPTX from `svg_final/`.

---

## External Reference vs Base64 Embedding

| Method | Pros | Cons | Suitable For |
|--------|------|------|-------------|
| **External reference** | Small file size, fast iteration, easy to replace | Preview requires HTTP server from project root | `svg_output/` development phase |
| **Base64 embedding** | Self-contained file, stable export | Large file size | `svg_final/` delivery phase |

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

Browser security restrictions prevent loading external images from directly opened SVGs. Start an HTTP server from the project root:

```bash
python3 -m http.server -d <project_path> 8000
# Visit http://localhost:8000/svg_output/your_file.svg
```

---

## Method 2: Base64 Embedding (Recommended for Delivery Phase)

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

Use the unified post-processing pipeline in [shared-standards.md §5](shared-standards.md). It runs `finalize_svg.py` before export so image references from `svg_output/` become embedded assets in `svg_final/`.

```bash
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path> -s final
```

### Standalone: embed_images.py (Advanced Usage)

For processing specific SVGs without running the full pipeline:

```bash
python3 scripts/svg_finalize/embed_images.py <svg_file>                         # Single file
python3 scripts/svg_finalize/embed_images.py <project_path>/svg_output/*.svg    # Batch
python3 scripts/svg_finalize/embed_images.py --dry-run <project_path>/svg_output/*.svg  # Preview
```

---

## Best Practices

### Image Optimization

Compress images before embedding to reduce file size:

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
└── svg_final/         # Final version (images embedded)
```

### Rounded Corner / Non-rectangular Image Cropping

`clipPath` **on `<image>` elements** is conditionally allowed. The authoritative constraints are in [shared-standards.md §1.2](shared-standards.md); do not restate or relax them here.

Alternative for the rare case where `clipPath` does not fit: bake the rounded corners into the source image (PNG with alpha) before embedding.

---

## FAQ

**Q: Can't see images when opening SVG directly?**
Browser security policy blocks cross-directory requests. Start an HTTP server from the project root, or run `finalize_svg.py` first then view from `svg_final/`.

**Q: Base64 file too large?**
Compress the original image, use JPEG format, reduce resolution (match actual display dimensions).

**Q: How to reverse-extract a Base64 image?**
```bash
base64 -d image.b64 > image.png
```
