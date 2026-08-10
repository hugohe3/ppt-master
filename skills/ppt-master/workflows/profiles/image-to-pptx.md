---
description: Quick-only Generate profile for reconstructing one or more source images into layered, editable PPTX slides.
---

# Image to PPTX Profile

> Quick-only Generate profile, not a top-level route. Normalize one or more
> supplied images into the represented page roster, then rebuild each page as
> native text, identity-faithful source graphics, and independently placeable
> image layers.

Reconstructs approved mockups, rendered slide images, contact sheets, or
flattened page visuals into a new PPTX. It does not redesign the deck and does
not run Strategist or confirmation. The visible result is the reference truth,
but the output is not a screenshot skin: image content is rebuilt into the
smallest useful background / foreground / subject stack, visible text is
restored as native text, and source graphics remain visually exact.

**Trigger**: the user supplies one or more raster visuals and explicitly asks
to restore the represented pages as a PPTX. Ordinary photos, illustrations, and
moodboards used only as resources for a new story do not activate this profile.

**Support boundary — Codex required**: this profile is currently documented
and validated for Codex because it depends on Codex's native reference-image
generation/editing capability and direct inspection of every derived layer.
Other hosts are not adapted or supported by this workflow; they may happen to
work, but the repository makes no compatibility claim and defines no alternate
host or generic image-backend fallback for this profile.

**Hard rule — Quick only**: this profile always loads
[`quick-generate.md`](./quick-generate.md) and never
[`generate-pptx.md`](../generate-pptx.md). The user does not need to say
"Quick" separately. Skip Strategist, Confirm UI, template selection,
`design_spec.md`, `spec_lock.md`, and the Default first-page gate. The current
main agent decides the reconstruction directly, prepares all resources, hand-
authors SVG pages, runs the lockless final checker, and exports.

**Hard rule — source surface, not template application**: stay in Quick free
design and do not install or apply a Brand/Style/Layout/Deck workspace for this
profile. A template would compete with the canonical page geometry and visual
identity. A reusable-system request routes to Create Template instead.

---

## 1. Routing and Output Boundary

| Request shape | Behavior |
|---|---|
| One or more image files represent pages that must become a final editable PPTX | Activate this profile and Quick Generate |
| One file contains several clearly separated slide frames | Split it into the ordered page roster first, then reconstruct each frame |
| Images are ordinary content assets or inspiration for a new deck | Use ordinary Generate |
| Images should define a reusable Brand/Style/Layout/Deck workspace | Use [`create-template.md`](../create-template.md) |
| A semantic source PPTX exists and only its layout should improve | Use [`beautify-pptx.md`](./beautify-pptx.md) |

**Hard rule — mutually exclusive fidelity profiles**: Image to PPTX and
Beautify never compose. Beautify preserves semantic PPTX content while
redesigning layout; Image to PPTX preserves a rendered page surface while
rebuilding its object and image-layer boundaries.

**Hard rule — flat final deck**: output stays `pptx_structure.mode: flat`. Page
pixels do not prove Master/Layout identity, placeholders, theme ancestry,
hidden objects, notes, animations, chart data sources, or authoring history.
Do not infer them. A reusable-system request routes to Create Template instead.

---

## 2. Normalize Source Images into Pages

🚧 **GATE**: an ordered canonical page-image roster exists before image-layer
decisions or SVG authoring.

| Source form | Normalization |
|---|---|
| One file containing one complete page | Keep it as one canonical page image |
| Several files containing one page each | Preserve the explicit or filename-natural order |
| One or more regular contact sheets | Split row-major with `slice_images.py --grid`, without alpha removal |
| A file containing several non-grid page frames | Record each visibly bounded page bbox and crop it into a separate lossless canonical page image |
| Boundaries or order are genuinely ambiguous | Mark the roster blocked instead of silently merging, dropping, or reordering pages |

Archive original files under `sources/`; keep normalized page images under
`images/source-pages/` or another project-local source-page folder. Never
overwrite an original file.

**Hard rule — one normalized frame, one slide**: frame count, not input-file
count, owns slide count. Every normalized page frame maps to one output slide
in the same order. Preserve the frame's aspect ratio. Mixed aspect ratios are
blocked until the current agent resolves one explicit whole-deck treatment.

**Mandatory — inspect every canonical page**: ordinary image-resource
inspection limits do not apply to this page roster. Inspect each normalized
page once to identify text, source graphics, scene-image regions, overlap,
region-level source sufficiency, boundary completeness, occlusion, and the
minimum useful layer stack. Reopen only the current page or a specifically
unresolved region afterward.

---

## 3. Reconstruct by Content Family

Classify visible regions by what they are, not by how easy they are to crop.

| Content family | Default realization | Non-negotiable boundary |
|---|---|---|
| Editable text | `native_text` | Restore exact visible wording, line grouping, alignment, emphasis, and approximate font metrics; do not bake ordinary slide text into generated images |
| Source graphic | `source_graphic` | Logos, icons, badges, vector-like ornaments, and decorative marks preserve visible identity. Use an exact vector, deterministic redraw, sufficient source pixels, or Codex reference reconstruction according to the quality ladder below; never substitute a merely similar graphic |
| Data graphic | `native_chart`, `native_table`, or exact `source_graphic` | Preserve every visible value, label, relationship, and geometry. Rebuild natively only when the source is legible enough to verify; otherwise use an exact crop/vector or mark `manual_required`. Never ask a generative model to recreate chart/table/data content |
| Simple exact geometry | `native_shape` | Use a native shape only when fill, stroke, geometry, and layering can be matched faithfully; otherwise prepare an identity-faithful source-graphic asset |
| Scene image | `image_layer` | Photos, people, characters, products, environmental backgrounds, textures, and complex illustrations may be reference-edited or regenerated as registered layers |
| Unreadable or unsafe region | `manual_required` | Block rather than invent wording, identity, values, or a visually different replacement |

**Hard rule — separate layer need from realization**: source clarity never
decides whether a required editable, movable, or overlapping object becomes a
separate layer; it decides only how that layer is prepared.

**Mandatory — assess source sufficiency per region**: judge each region at final
display size without a page-wide score or threshold. Inspect detail,
contamination/occlusion, and whether identity, geometry, lettering, or data
remain verifiable.

| Source evidence for a required independent image layer | Realization |
|---|---|
| Complete, cleanly separable, and sufficient at final display size | Prepare a source-derived crop or RGBA layer at the recorded geometry |
| Contaminated, occluded, incomplete, or too low-resolution; identity and geometry remain verifiable | Reference-edit or reconstruct the layer and exposed background from that evidence |
| Required identity, wording, values, or geometry cannot be verified | Mark `manual_required`; do not invent authoritative content |

**Graphic identity is authoritative; source pixel bytes are not**: use an exact
known vector when available. Deterministically redraw a simple, fully legible
graphic as SVG/native geometry. Reuse source pixels only when they are complete
and sufficient at final display size. When a complex logo, icon, badge,
ornament, or wordmark is visibly identifiable but too low-resolution, use its
source crop as the Codex reference and reconstruct a higher-resolution asset
that preserves the same silhouette, proportions, colors, lettering, bbox, and
z-order. Never merely interpolate low-resolution pixels, redesign the brand,
replace it with a similar library icon, or invent unreadable identity. If those
properties cannot be verified, mark the graphic `manual_required`.

**Visible-surface authority**: preserve every legible string, number, label,
relative position, crop, z-order, color relationship, and emphasis visible in
the source. Do not improve the layout, rewrite copy, correct claims through
research, reveal invented semantics, or silently replace branded graphics.

---

## 4. Build the Minimum Useful Layer Stack

For each page, decide the smallest stack that makes the intended objects
independent. Do not split a page merely to maximize layer count.

Typical bottom-to-top order:

1. `base` — clean full-canvas background with all planned removable subjects,
   foreground objects, and editable text removed; hidden background pixels are
   reconstructed where necessary.
2. `midground-*` — optional scene layers that must sit between the base and
   primary subject.
3. `subject-*` — people, characters, products, props, or other independently
   movable cutouts.
4. `foreground-*` — effects, foliage, particles, framing objects, or other
   scene elements that cross the subject or native slide objects.
5. `source-graphic-*` — exact or identity-faithfully reconstructed logos,
   icons, badges, and ornamental marks, plus exact/native data graphics at
   their visible z-order.
6. `native-text-*` and exact native shapes.

**Registered-group rule**: every base/midground/subject/foreground layer in a
group stays registered to the same canonical page or scene bbox. A
source-derived member retains recorded geometry; every Codex-derived member
starts from that canonical source. Preserve canvas, position, scale,
pose, lighting, and style. Do not trim registered full-canvas layers;
transparent pixels retain alignment.

When one or more scene layers require reference editing or reconstruction, use
[`image-generator.md`](../../references/image-generator.md) §4.4's registered
reconstruction group as the primitive:

- create one clean base by removing **all** scene subjects/foreground objects,
  source/data graphics, and editable text planned for separate realization,
  then reconstruct only the newly exposed background;
- create at least one independent subject/foreground output from the same
  canonical source whenever the page contains scene content that must be
  independently editable; the base plus that output are the minimum two
  independently prepared image layers, while §3 decides whether each layer
  retains sufficient source pixels or requires reference reconstruction;
- derive every additional layer independently from the canonical source, never
  from the base or another generated layer;
- preserve the original pose, scale, and coordinates on RGBA transparency;
- repeat only for additional layers that genuinely need independent movement,
  overlap, or animation.

**Batch non-overlapping objects**: one object does not imply one generation.
When several subjects, props, effects, or source-graphic reconstructions have
pairwise-disjoint padded bboxes—including visible shadows and effects—and can
share one isolation treatment, ask Codex for one `layer-plate` containing all
of them with clear separation. Use either:

- a full-canvas registered plate that keeps the source positions, then create
  one nested-SVG picture crop per recorded bbox; or
- a regular isolated-cell sheet when source coordinates are unnecessary, then
  use `slice_images.py --grid ... --names ... --trim --alpha` and place the
  resulting assets at their recorded source bboxes.

Both paths yield independent PPT picture objects from one generated output.
If transparency is unavailable, use one exact flat key color for the whole
plate and remove it once; never regenerate a separate green-background image
for each object. Objects that overlap one another or require different z-order
must use separate plates/layers.

The reference-image CLI does not inherit source dimensions automatically. Pass
an explicit matching aspect ratio/size, then verify that every member of one
registration group has the same final pixel canvas. In SVG, place the base and
all full-canvas layers at identical `x`, `y`, `width`, and `height` with
`no-crop` behavior.

**Reconstruct for final resolution**: apply the §3 source-sufficiency decision
per region. Retaining complete source pixels is valid only when they remain
sharp enough at final display size; a clear source may still require reference
reconstruction when separation needs hidden or uncontaminated pixels. When
detail is insufficient, use Codex reference reconstruction; interpolation alone
does not recover detail.

**Reference-edit, not reinterpretation**: reconstruction prompts name the
canonical source page/region and ask to preserve the visible composition and
style. They may inpaint hidden scene pixels or complete an occluded subject,
but must not redesign the scene, change a character/person, introduce text,
substitute or alter a logo, or invent extra decorative graphics.

When Codex cannot return transparency, generate the isolated layer or shared
plate on one exact flat key color and use `slice_images.py` as a `1x1` sheet
with `--alpha` and **without** `--trim`, preserving full-canvas registration.
Several plate members share this single keyed output.

---

## 5. Source Evidence without a Quick Plan

Before deciding layers, write source evidence to:

```text
<project_path>/analysis/reconstruction_inventory.json
```

The inventory records what is visibly present, not a resumable implementation
plan. Keep it limited to:

- original file and normalized page path;
- page order, source-frame bbox, SHA-256, and pixel dimensions;
- visible regions with stable ids, source bboxes, observed family
  (`text`, `graphic`, `image`, or `unknown`), verbatim text when applicable,
  and confidence;
- observed source sufficiency, boundary completeness, occlusion/contamination,
  and identity/data verifiability at final placement;
- overlap/z-order observations and unresolved evidence.

Do **not** put final layer choices, generation prompts, output filenames, or SVG
bindings into this inventory. The current main agent keeps those decisions in
active context and writes only required operational image manifests/evidence.
Context loss restarts the Quick run; the inventory is not a resume artifact.

Low-confidence visible text, an uncertain page boundary, or an unidentified
branded/data graphic is unresolved evidence and blocks successful delivery.

---

## 6. Image Preparation

When any `image_layer` or low-resolution `source_graphic` requires reference
editing or generation, load
[`image-base.md`](../../references/image-base.md) and
[`image-generator.md`](../../references/image-generator.md). The current Codex
main agent resolves the layer stack directly, uses Codex's native
reference-image capability, and finishes every required layer before SVG
authoring. Do not adapt `image_gen.py`, its generic manifest, or provider
backends for this profile.

- Use `text_policy: none` for scene reconstruction layers. Use `embedded` only
  when an exact visible wordmark/letterform is integral to a reconstructed
  source graphic; ordinary slide text always remains native.
- Exhaust the available Codex image path automatically; block before export if a
  required layer remains `Needs-Manual`.
- Preserve each prepared image layer's source page/region, source hash,
  realization method, operation, output path/hash, registration group, and
  z-order in the applicable operational evidence; include prompt and
  backend/model when the layer was reference-edited or reconstructed.
- Re-run `analyze_images.py` after assets change.
- A generated candidate is not usable until its expected file exists, it has
  been inspected once, and its registration group or plate has been checked
  against the canonical page.
- Inspect the recomposed page once after all generated layers, plate crops,
  source graphics, native shapes, and native text are in place. This narrow
  readback is mandatory fidelity validation, not resource reselection.

---

## 7. SVG Authoring and Release Gate

Follow Quick Generate after source normalization and resource preparation.
Hand-author pages serially from the prepared base, registered scene layers,
identity-faithful source graphics, native shapes, and native text. Give independently
movable layers stable direct-root group ids so later animation can target them.

**Forbidden — screenshot skin**: do not use the complete source page as the
sole full-slide picture and add token editable text above it. The source page
is a comparison reference, not a hidden backing layer in the delivered slide.

Verify each page against its canonical image:

| Final check | Required evidence |
|---|---|
| Page roster | Every normalized frame becomes one slide in the same order and canvas treatment |
| Native text | Every legible string/number is present verbatim and remains editable |
| Source graphics | Logos, icons, and decorative graphics preserve the original identity and geometry at adequate final resolution; no similar substitute or unverified redesign appears |
| Data graphics | Every chart/table/data value and relationship is native-and-verified or retained from an exact source asset; none is generatively recreated |
| Layer registration | Base, subject, foreground, and other generated layers share the expected canvas/placement and show no jumps, seams, halos, or independent-crop drift |
| Visible image fidelity | The recomposed scene preserves the source's visible subject identity, pose, crop, lighting, color relationships, and z-order |
| Honest reconstruction | AI-recovered hidden pixels are identified as reconstruction, not claimed as original source detail |
| Independent objects | Every layer requested for editing or animation is a distinct SVG/PPT picture object; non-overlapping members may originate from one shared generated plate |
| Reference exclusion | Canonical full-page source images remain comparison evidence and are not referenced or packaged as delivered slide media |
| Package quality | Quick's lockless final SVG checker and PPTX postflight pass |

If a generated layer drifts, retry from the canonical reference with a narrower
edit instruction. Do not compensate by changing native text/graphics or by
flattening the full page. If the Codex image path is exhausted,
mark the affected layer `Needs-Manual` and block successful export.

```markdown
## ✅ Image to PPTX Complete

- [x] Source files were normalized into the complete ordered page roster
- [x] Visible text is native and verbatim
- [x] Source graphics preserve identity and are sharp enough at final size
- [x] Required background / foreground / subject layers are independent and registered
- [x] Shared plates were split/cropped into the required independent objects
- [x] Recombined pages match the supplied visual references
- [x] Canonical full-page source images are absent from delivered slide media
- [x] Quick's SVG quality gate and PPTX postflight pass
- [ ] **Next**: Report the PPTX and identify native, exact-source, and AI-reconstructed objects
```
