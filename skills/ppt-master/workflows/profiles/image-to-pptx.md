---
description: Quick-only Generate profile for reconstructing one or more source images into layered, editable PPTX slides.
---

# Image to PPTX Profile

> Quick-only Generate profile, not a top-level route. Normalize supplied images into the represented page roster, then rebuild each page as native text, identity-faithful source graphics, and independently placeable image layers. The visible result is the reference truth, but the output is not a screenshot skin: image content becomes the smallest useful background / foreground / subject stack, visible text is restored natively, and source graphics stay visually exact. No redesign, no Strategist, no confirmation.

**Trigger**: the user supplies raster visuals (approved mockups, rendered slides, contact sheets, flattened pages) and explicitly asks to restore the represented pages as a PPTX. Photos, illustrations, or moodboards used as resources for a new story do not activate it.

**Support boundary — Codex required**: documented and validated for Codex only, because it depends on Codex's native reference-image generation/editing and direct inspection of every derived layer. Other hosts may happen to work; the repository makes no compatibility claim and defines no alternate host or generic image-backend fallback.

**Hard rule — Quick only**: always load [`quick-generate.md`](./quick-generate.md), never `generate-pptx.md`, without the user saying "Quick"; skip Strategist, Confirm UI, template selection, Design Spec, lock, and the Default first-page gate. The main agent decides the reconstruction, prepares all resources, hand-authors SVG, runs the lockless final checker, and exports.

**Hard rule — source surface, not template application**: stay in Quick free design; never install or apply a Brand/Style/Layout/Deck workspace — it would compete with the canonical page geometry. A reusable-system request routes to Create Template.

---

## 1. Routing and Output Boundary

| Request shape | Behavior |
|---|---|
| Image files represent pages that must become a final editable PPTX | This profile + Quick |
| One file contains several clearly separated slide frames | Split into the ordered roster first, then reconstruct each frame |
| Images are ordinary content assets or inspiration for a new deck | Ordinary Generate |
| Images should define a reusable workspace | [`create-template.md`](../create-template.md) |
| A semantic source PPTX exists and only its layout should improve | [`beautify-pptx.md`](./beautify-pptx.md) |

**Hard rule — mutually exclusive fidelity profiles**: Image to PPTX and Beautify never compose — Beautify preserves semantic PPTX content while redesigning layout; this profile preserves a rendered surface while rebuilding object and image-layer boundaries.

**Hard rule — flat final deck**: output stays `pptx_structure.mode: flat`. Pixels do not prove Master/Layout identity, placeholders, theme ancestry, hidden objects, notes, animations, chart data sources, or authoring history; never infer them.

---

## 2. Normalize Source Images into Pages

🚧 **GATE**: an ordered canonical page-image roster exists before any layer decision or SVG authoring.

| Source form | Normalization |
|---|---|
| One file, one complete page | One canonical page image |
| Several files, one page each | Preserve explicit or filename-natural order |
| Regular contact sheets | Split row-major with `slice_images.py --grid`, without alpha removal |
| Several non-grid page frames in one file | Record each visibly bounded bbox and crop it into a separate lossless page image |
| Ambiguous boundaries or order | Mark the roster blocked; never silently merge, drop, or reorder |

Archive originals under `sources/`; keep normalized pages under `images/source-pages/` or another project-local folder; never overwrite an original.

**Hard rule — one normalized frame, one slide**: frame count, not input-file count, owns slide count; every frame maps to one slide in order with its aspect ratio preserved; mixed aspect ratios block until one explicit whole-deck treatment is resolved.

**Mandatory — inspect every canonical page** once (ordinary image-resource inspection limits do not apply) for text, source graphics, scene regions, overlap, region-level source sufficiency, boundary completeness, occlusion, and the minimum useful layer stack; reopen only the current page or an unresolved region afterward.

---

## 3. Reconstruct by Content Family

Classify visible regions by what they are, not by how easy they are to crop.

| Content family | Default realization | Non-negotiable boundary |
|---|---|---|
| Editable text | `native_text` | Exact visible wording, line grouping, alignment, emphasis, approximate metrics; never bake slide text into generated images |
| Source graphic | `source_graphic` | Logos, icons, badges, ornaments preserve identity via exact vector, deterministic redraw, sufficient source pixels, or Codex reference reconstruction; never a merely similar graphic |
| Data graphic | `native_chart`, `native_table`, or exact `source_graphic` | Every value, label, relationship, and geometry preserved; native only when legible enough to verify, otherwise exact crop/vector or `manual_required`; never generatively recreated |
| Simple exact geometry | `native_shape` | Only when fill, stroke, geometry, and layering match faithfully |
| Scene image | `image_layer` | Photos, people, characters, products, environments, textures, complex illustrations may be reference-edited or regenerated as registered layers |
| Unreadable or unsafe region | `manual_required` | Block rather than invent wording, identity, values, or a different replacement |

**Hard rule — separate layer need from realization**: source clarity never decides whether a required editable, movable, or overlapping object becomes a separate layer, only how that layer is prepared. **Mandatory — assess source sufficiency per region** at final display size without a page-wide score: complete, cleanly separable, and sufficient → a source-derived crop or RGBA layer at the recorded geometry; contaminated, occluded, incomplete, or low-resolution with verifiable identity and geometry → reference-edit or reconstruct the layer and exposed background from that evidence; unverifiable identity, wording, values, or geometry → `manual_required`.

**Graphic identity is authoritative; source pixel bytes are not**: use an exact known vector when available; deterministically redraw a simple, fully legible graphic; reuse source pixels only when complete and sufficient at final size; when a complex logo, icon, badge, ornament, or wordmark is identifiable but too low-resolution, use its crop as the Codex reference and reconstruct a higher-resolution asset with the same silhouette, proportions, colors, lettering, bbox, and z-order — never mere interpolation, a brand redesign, a similar library icon, or invented identity. **Visible-surface authority**: preserve every legible string, number, label, relative position, crop, z-order, color relationship, and emphasis; never improve the layout, rewrite copy, correct claims through research, reveal invented semantics, or replace branded graphics.

---

## 4. Build the Minimum Useful Layer Stack

Decide per page the smallest stack that makes the intended objects independent; never split merely to maximize layer count. Typical bottom-to-top order: `base` (clean full-canvas background with every planned removable subject, foreground object, and editable text removed, hidden pixels reconstructed where necessary) → `midground-*` → `subject-*` (independently movable cutouts) → `foreground-*` (effects, foliage, particles, framing that cross the subject or native objects) → `source-graphic-*` (exact or reconstructed marks plus exact/native data graphics at their z-order) → `native-text-*` and exact native shapes.

**Registered-group rule**: every base/midground/subject/foreground layer in a group stays registered to the same canonical page or scene bbox; source-derived members keep recorded geometry, every Codex-derived member starts from that canonical source with canvas, position, scale, pose, lighting, and style preserved; never trim registered full-canvas layers. When scene layers need reference editing, use [`image-generator.md`](../../references/image-generator.md) §4.4's registered reconstruction group: one clean base with all separately realized subjects, graphics, and text removed and only the exposed background reconstructed; at least one independent subject/foreground output from the same canonical source whenever the page holds scene content that must be independently editable (base plus that output are the minimum two layers); every additional layer derived independently from the canonical source, never from the base or another generated layer; original pose, scale, and coordinates on RGBA transparency; further layers only for genuine independent movement, overlap, or animation.

**Batch non-overlapping objects**: when several subjects, props, effects, or graphic reconstructions have pairwise-disjoint padded bboxes (including shadows and effects) and share one isolation treatment, ask Codex for one `layer-plate` holding all of them with clear separation — either a full-canvas registered plate followed by one nested-SVG picture crop per recorded bbox, or a regular isolated-cell sheet sliced with `slice_images.py --grid ... --names ... --trim --alpha` and placed at the recorded bboxes. Without transparency, use one exact flat key color for the whole plate (`slice_images.py` as a `1x1` sheet with `--alpha` and without `--trim` for a registered plate) and remove it once; never a separate green-background image per object. Overlapping objects or different z-orders use separate plates.

The reference-image CLI does not inherit source dimensions: pass an explicit matching aspect ratio/size and verify every member of a registration group shares the same final pixel canvas; in SVG place the base and all full-canvas layers at identical `x`, `y`, `width`, `height` with `no-crop` behavior. **Reconstruct for final resolution**: retained source pixels must stay sharp at final size; interpolation recovers no detail. **Reference-edit, not reinterpretation**: prompts name the canonical source page/region and preserve the visible composition and style; they may inpaint hidden pixels or complete an occluded subject but never redesign the scene, change a person, introduce text, alter a logo, or add decoration.

---

## 5. Source Evidence without a Quick Plan

Before deciding layers, write `<project_path>/analysis/reconstruction_inventory.json` recording only what is visibly present: original file and normalized page path; page order, source-frame bbox, SHA-256, pixel dimensions; visible regions with stable ids, bboxes, observed family (`text` / `graphic` / `image` / `unknown`), verbatim text where applicable, and confidence; observed sufficiency, boundary completeness, occlusion/contamination, and identity/data verifiability; overlap/z-order observations and unresolved evidence. No final layer choices, prompts, output filenames, or SVG bindings — those stay in active context plus required operational image evidence; context loss restarts the run. Low-confidence text, an uncertain boundary, or an unidentified branded/data graphic is unresolved evidence and blocks delivery.

---

## 6. Image Preparation

When any `image_layer` or low-resolution `source_graphic` needs reference editing, load [`image-base.md`](../../references/image-base.md) and [`image-generator.md`](../../references/image-generator.md); the Codex main agent resolves the stack directly with Codex's native reference-image capability and finishes every layer before SVG authoring — never adapt `image_gen.py`, its manifest, or provider backends for this profile. Use `text_policy: none` for scene layers and `embedded` only when an exact wordmark/letterform is integral to a reconstructed graphic. Exhaust the Codex image path automatically and block before export if a layer stays `Needs-Manual`. Record each layer's source page/region, source hash, realization method, operation, output path/hash, registration group, and z-order (plus prompt and backend/model when reconstructed) in the operational evidence; re-run `analyze_images.py` after assets change. A candidate is usable only when its file exists, it has been inspected once, and its group or plate has been checked against the canonical page. Inspect the recomposed page once after all layers, crops, graphics, shapes, and text are in place — mandatory fidelity validation, not resource reselection.

---

## 7. SVG Authoring and Release Gate

Follow Quick after normalization and preparation: hand-author pages serially from the base, registered layers, source graphics, native shapes, and native text, giving independently movable layers stable direct-root group ids for later animation.

**Forbidden — screenshot skin**: never use the complete source page as the sole full-slide picture with token editable text above it; the source page is comparison evidence, not a hidden backing layer.

| Final check | Required evidence |
|---|---|
| Page roster | Every normalized frame is one slide in order with the same canvas treatment |
| Native text | Every legible string/number present verbatim and editable |
| Source graphics | Identity and geometry preserved at adequate resolution; no substitute or unverified redesign |
| Data graphics | Every value and relationship native-and-verified or from an exact source asset; none generatively recreated |
| Layer registration | Generated layers share canvas/placement with no jumps, seams, halos, or crop drift |
| Visible fidelity | Subject identity, pose, crop, lighting, color relationships, and z-order preserved |
| Honest reconstruction | AI-recovered hidden pixels identified as reconstruction |
| Independent objects | Every layer requested for editing or animation is a distinct picture object (shared plates allowed for disjoint members) |
| Reference exclusion | Canonical full-page source images are not referenced or packaged as slide media |
| Package quality | Quick's lockless final checker and PPTX postflight pass |

If a layer drifts, retry from the canonical reference with a narrower edit; never compensate by changing native text/graphics or flattening the page. If the Codex path is exhausted, mark the layer `Needs-Manual` and block export.

```markdown
## ✅ Image to PPTX Complete
- [x] Source files normalized into the complete ordered roster
- [x] Visible text native and verbatim; source graphics identity-faithful and sharp
- [x] Required background / foreground / subject layers independent and registered; shared plates split into independent objects
- [x] Recombined pages match the references; canonical source images absent from slide media
- [x] Quick's SVG quality gate and PPTX postflight pass
- [ ] **Next**: Report the PPTX and identify native, exact-source, and AI-reconstructed objects
```
