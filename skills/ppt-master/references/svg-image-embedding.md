> See [`shared-standards-core.md`](./shared-standards-core.md) for common technical constraints.

# SVG Image Embedding Guide

Status names, resource lifecycle, and the embedding workflow for images in SVG pages. [`svg-effects.md`](./svg-effects.md) §6.5 owns the native carrier, crop transport, and filter/clip contracts; Base64 embedding, preview serving, and image-optimization flags are tool behavior in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md).

---

## Image Resource List Format

Each image carries an `Acquire Via` field plus a status. Default Generate's authority is `design_spec.md §VIII` plus its lock projection (run `analyze_images.py` after confirmation when user images are selected and complete the list before Executor); Quick's is the main agent's active-context decisions (explicit user paths first, unspecified acquisition resolved automatically, all preparation finished before SVG authoring without confirmation or a persisted roster).

```markdown
| Filename | Dimensions | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference |
|----------|------------|---------|------|----------------|-------------|-------------|--------|-----------|
| team.jpg | 800x600 | Team photo | Photography | `Put faces behind the hiring claim; #P1-02 + #M2-08 fading the photo edge into the page so copy meets it without a frame` | adaptive | web | Pending | Diverse engineering team in modern office |
```

### Image Status Enum

| Status | Meaning | Executor Handling |
|--------|---------|-------------------|
| **Pending** | Acquisition or declared derivation needed, not yet attempted | Step 5 consumes it; must not remain afterward |
| **Failed** | Latest automatic attempt failed; retryable, non-terminal | Step 5 reruns the owning manifest or resolves the row to `Needs-Manual`; never usable content |
| **Needs-Selection** | Web search produced one bounded thumbnail page; no original or provenance yet | Step 5 promotes one candidate, advances to `next_candidate_page`, or after exhaustion changes the query and returns the row to `Pending`; never consumed |
| **Generated** | AI/slice output exists | Reference from `../images/`; manifest records govern attribution; an `Illustration Sheet` stays in §VIII only as an unplaced slice source |
| **Sourced** | Web-sourced file exists at the expected path | Reference from `../images/`; with `license_tier: attribution-required` in `image_sources.json`, render an inline credit ([`executor-web-image.md`](./executor-web-image.md) §1, [`image-searcher.md`](./image-searcher.md) §7) |
| **Needs-Manual** | The owning path requires manual fulfillment; for `slice`, the parent sheet is unavailable | Default may use a dashed placeholder until its readiness gate; Quick blocks every required row in this status even with an unverified candidate file — validate and reconcile a supplied replacement to `Existing`, `Generated`, or `Sourced` first. Quick automated AI exhaustion never creates it ([`image-generator.md`](./image-generator.md) §7's no-AI replan). A retained manual `slice` needs the parent sheet and a `slice_images.py` rerun, never hand-placed element files |
| **Existing** | User-supplied (`Acquire Via: user`) | Place in `images/`, reference with `<image>` |
| **Placeholder** | Intentionally not prepared (`Acquire Via: placeholder`) | Dashed placeholder; replace later |

---

## Workflow

1. Resolve image needs — Default: Strategist resource list + lock projection; Quick: the main agent in active context.
2. Prepare project-local resources before SVG authoring: `user` → materialize under `images/` → `Existing`; a Pending prepared derivative → [`image-base.md`](./image-base.md) §1 before ordinary dispatch; `ai` → Image_Generator → `Generated`, a Default recovery decision, or the Quick no-AI replan; `web` with vision → Image_Searcher saves at most 8 ranked previews → `Needs-Selection` → promote or next page → `Sourced` / `Needs-Manual`; `web` without vision → strict metadata-ranked best-only candidate with the method recorded → `Sourced` / `Needs-Manual`; `slice` → after the parent sheet is `Generated`, `slice_images.py` → `Generated`.
3. Authoring consumes only prepared resources: `Existing` / `Generated` → `<image href="../images/xxx.png" …/>`; `Sourced` → `<image>` plus a credit `<text>` only for `attribution-required` (`no-attribution` and `manual` place the image alone); `Placeholder` / `Needs-Manual` → dashed border plus description text until a supplied file is validated and reconciled.
4. Export — Default: [`generate-pptx.md`](../workflows/generate-pptx.md) Step 7; Quick: after every required resource has a validated file/provenance and usable status, its final checker then `--quick-generate` export.

Keep external references in `svg_output/` during generation; Default's `finalize_svg.py` embeds images into the `svg_final/` preview, Quick omits it, and both native exports read `svg_output/` directly. **Hard rule — export boundary**: `svg_final/` is a self-contained preview that may be inserted into PowerPoint as an SVG picture (EMF/WMF keep the external-reference exception for lossless passthrough); the only supported generated-PPTX route is `svg_output/` through the project converter; PowerPoint's manual Convert-to-Shape is unsupported.

---

## Canonical `<image>` form

```xml
<image href="../images/image.png" x="0" y="0" width="1280" height="720" preserveAspectRatio="xMidYMid slice"/>
```

`href` is the relative project path; `x`, `y`, `width`, `height` the display frame; `preserveAspectRatio` `xMidYMid slice` (center crop, like CSS `cover`), `xMidYMid meet` (complete display, like `contain`), or `none` (stretch — never for a `no-crop` source). A Base64 `data:` href is the `svg_final/` preview form produced by finalization, not an authoring form. `clipPath` on `<image>` is conditionally allowed under [`shared-standards-core.md`](./shared-standards-core.md) §1.2; when it does not fit, bake rounded corners into an alpha PNG before embedding.

Project layout: `images/` (assets), `sources/` (source files and their `*_files/` images), `svg_output/` (external references), `svg_final/` (Default-only embedded preview). Preview `svg_output/` through `python3 -m http.server -d <project_path> 8000` (browsers block cross-directory images on directly opened files). Native export keeps original image bytes by default (`--image-sizing cap`); explicit compact export uses `--image-sizing display --image-scale 2 --image-quality 85`, and `--no-image-optimize` forces original bytes.
