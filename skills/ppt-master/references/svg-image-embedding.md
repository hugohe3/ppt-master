> See shared-standards.md for common technical constraints.

# SVG Image Embedding Guide

Technical specifications and recommended workflow for adding images to SVG files.

---

## Image Resource List Format

Defined in the Design Specification & Content Outline; each image has a status annotation. If the image approach includes "B) User-provided", you must run `analyze_images.py` immediately after the Strategist completes the Eight Confirmations, and complete the list before outputting the design spec.

```markdown
| Filename | Dimensions | Purpose | Status | Generation Description |
|----------|-----------|---------|--------|----------------------|
| cover_bg.png | 1280x720 | Cover background | Pending | Modern tech abstract background, deep blue gradient |
| product.png | 600x400 | Page 3 | Existing | - |
| team.png | 600x400 | Page 5 | Placeholder | Team collaboration scene (to be added later) |
```

### Three Status Types

| Status | Meaning | Executor Handling |
|--------|---------|-------------------|
| **Pending** | Needs AI generation, has description | Generate image first into `images/`, then reference with `<image>` |
| **Existing** | User already has image | Place in `images/`, reference with `<image>` |
| **Placeholder** | Not yet processed | Use dashed border placeholder; replace later |

---

## Workflow

```
1. Strategist defines image needs → Add image resource list, annotate each status
2. Image preparation (pending/existing) → Place in project/images/
3. Executor generates SVGs (svg_output/)
   ├── Existing/Pending → <image href="../images/xxx.png" .../>
   └── Placeholder → Dashed border + description text
4. Preview: python3 -m http.server -d <project_path> 8000 → /svg_output/<filename>.svg
5. Post-processing & Export
   ├── python3 scripts/finalize_svg.py <project_path>
   └── python3 scripts/svg_to_pptx.py <project_path> -s final
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

### Recommended: Use finalize_svg.py (Unified Pipeline)

```bash
python3 scripts/finalize_svg.py <project_path>         # Icons, images, text, rounded rects — all in one pass
python3 scripts/svg_to_pptx.py <project_path> -s final  # Export PPTX from final version
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

`clipPath` **on `<image>` elements** is conditionally allowed — the converter maps qualifying clip shapes to native DrawingML picture geometry (`<a:prstGeom>` / `<a:custGeom>`), so rounded corners, circular avatars, hexagonal portraits, etc. are fully supported end-to-end.

Constraints (see [shared-standards.md §1.2](shared-standards.md) for the authoritative list):
- The `<clipPath>` must live inside `<defs>` and contain exactly **one** shape child — `circle`, `ellipse`, `rect` with `rx`/`ry`, `path`, or `polygon`.
- `clip-path` may appear **only** on `<image>` elements. Using it on shapes / groups / text is an error — draw the target geometry directly with the matching native element (`<circle>` / `<ellipse>` / `<rect rx="...">` / `<polygon>` / `<path>`). A rect clipped to a circle is just a `<circle>`.
- PowerPoint's own SVG renderer does not render `clipPath` correctly. The Native PPTX converter handles it, but the SVG reference version in the `_svg.pptx` backup will display the image uncropped.

Alternative for the rare case where `clipPath` does not fit (e.g. shape needs clipping): bake the rounded corners into the source image (PNG with alpha) before embedding.

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
