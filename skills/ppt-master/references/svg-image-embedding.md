> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# SVG Image Embedding Guide

Technical spec and workflow for adding images to SVG files.

---

## Image Resource List Format

Each image carries an `Acquire Via` field plus a status annotation. This file
owns status names, resource lifecycle, and embedding workflow;
[`svg-effects.md`](./svg-effects.md) §6.5 owns native carrier, crop transport,
and filter/clip contracts.

| Mode | Resource authority and preparation timing |
|---|---|
| Default Generate | `design_spec.md §VIII` plus its lock projection; when user-provided images are selected, run `analyze_images.py` after Strategist confirmation and complete the list before Executor |
| Quick Generate | Current main agent's active-context resource decisions; materialize explicit user paths first, resolve unspecified acquisition decisions automatically, and finish user/ai/web/slice preparation before SVG authoring without confirmation or a persisted roster |

```markdown
| Filename | Dimensions | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference |
|----------|------------|---------|------|----------------|-------------|-------------|--------|-----------|
| team.jpg | 800x600 | Team photo | Photography | `Put faces behind the hiring claim; #P1-02 + #M2-08 fading the photo edge into the page so copy meets it without a frame` | adaptive | web | Pending | Diverse engineering team in modern office |
```

### Image Status Enum

| Status | Meaning | Executor Handling |
|--------|---------|-------------------|
| **Pending** | Acquisition or declared derivation is needed; not yet attempted | Step 5 consumes this; must not remain afterward |
| **Failed** | The latest automatic acquisition attempt failed; this is retryable and non-terminal | Step 5 reruns the owning manifest or explicitly resolves the row to `Needs-Manual`; Executor must never treat `Failed` as usable content |
| **Needs-Selection** | Web search produced one bounded thumbnail-only candidate page; no original or provenance exists yet | Step 5 reviews/promotes one candidate, advances to `next_candidate_page`, or after pool exhaustion materially changes the query and returns the row to `Pending`; Executor must never consume this intermediate state |
| **Generated** | AI/slice output exists | Reference from `../images/`; manifest records govern attribution. An `Illustration Sheet` stays in §VIII only as an unplaced slice source |
| **Sourced** | Web-sourced file exists at expected path | Reference from `../images/`; check `image_sources.json` for `license_tier` — if `attribution-required`, render an inline credit element on the slide (see [`executor-web-image.md`](./executor-web-image.md) §1 and [`image-searcher.md`](./image-searcher.md) §7 for the attribution contract) |
| **Needs-Manual** | The owning source path requires manual fulfillment; for `slice`, the parent sheet is unavailable | Default Generate may use a dashed placeholder until its readiness gate. Quick Generate blocks every required row still in this status, even if an unverified candidate file exists; validate a supplied replacement and reconcile it to `Existing`, `Generated`, or `Sourced` first. Quick automated AI exhaustion never creates this status: [`image-generator.md`](./image-generator.md) §7 removes the affected AI/dependent-slice jobs through its declared no-AI replan. For a retained manual `slice`, supply the parent sheet and rerun `slice_images.py`; do not hand-place individual element files. |
| **Existing** | User already has image (`Acquire Via: user`) | Place in `images/`, reference with `<image>` |
| **Placeholder** | Intentionally not prepared yet (`Acquire Via: placeholder`) | Dashed border placeholder; replace later |

---

## Workflow

```
1. Resolve image needs:
   - Default Generate → Strategist-owned resource list + lock projection
   - Quick Generate → current main agent resolves the required resource in active context; explicit user paths/URLs/choices win, unspecified choices use automatic resolution, no interaction or persisted roster
2. Prepare project-local resources before SVG authoring:
   - user → materialize the explicit source under project/images/ → Existing
   - Pending prepared derivative → follow [`image-base.md`](./image-base.md) §3 before ordinary `Acquire Via` dispatch
   - Pending / Failed + ai  → Image_Generator executes the selected path → Generated, Default recovery decision, or Quick no-AI replan
   - Pending / Failed + web + vision → Image_Searcher saves at most 8 ranked previews → Needs-Selection → promote one original or fetch the next page → Sourced / Needs-Manual
   - Pending / Failed + web without vision → Image_Searcher accepts only a strict metadata-ranked best-only candidate and records that method → Sourced or Needs-Manual
   - Pending + slice → after parent AI sheet is Generated, slice_images.py cuts element files → Generated
3. SVG authoring consumes only prepared resources (Executor in Default Generate; current main agent in Quick Generate)
   ├── Existing / Generated → <image href="../images/xxx.png" .../>
   ├── Sourced + license_tier=no-attribution → <image href=...> only
   ├── Sourced + license_tier=attribution-required → <image href=...> + small <text> credit element on the slide
   ├── Sourced + license_tier=manual → <image href=...> only (user-supplied --from-url; rights/credit are user responsibility)
   └── Placeholder / Needs-Manual → Dashed border + description text until a supplied file is validated and status is reconciled
4. Preview: python3 -m http.server -d <project_path> 8000 → /svg_output/<filename>.svg
5. Export:
   - Default Generate → follow [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7
   - Quick Generate → after every required resource has a validated expected file/provenance and usable status, run the profile's final checker, then its `--quick-generate` export
```

> Keep external references in `svg_output/` during generation. Default Generate uses `finalize_svg.py` to embed images into the mandatory `svg_final/` visual preview. Quick Generate omits that preview artifact. Both native PPTX exports independently read image references from `svg_output/`.

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

Default Generate follows [`generate-pptx.md`](../workflows/generate-pptx.md)
Step 7; it owns the serial post-processing and export commands. Quick Generate
follows [`quick-generate.md`](../workflows/profiles/quick-generate.md) after its
required-resource gate. The native PPTX converter reads `svg_output/` and maps
its project-local image references directly to DrawingML in both modes.

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

### Native PPTX Image Export

**Default — preserve unmodified image bytes**: `svg_to_pptx.py` uses `--image-sizing cap`. It keeps original bytes when an image needs neither resizing nor EXIF geometry normalization, and re-encodes only images that require one of those transformations. Use the explicit compact command only when a compact export is requested.

| Need | Command |
|---|---|
| Normal native export | `python3 scripts/svg_to_pptx.py <project_path>` |
| Explicit compact export | `python3 scripts/svg_to_pptx.py <project_path> --image-sizing display --image-scale 2 --image-quality 85` |
| Force original bytes | `python3 scripts/svg_to_pptx.py <project_path> --no-image-optimize` |

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
