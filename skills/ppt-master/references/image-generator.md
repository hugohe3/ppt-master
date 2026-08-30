> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: turn each active `Acquire Via: ai` row into one prose prompt, generate the image into `project/images/`, and derive `slice` elements from illustration, illustrated-icon, and lettering sheets.

**Trigger**: the Default resource list contains `Acquire Via: ai` or `slice`, or Quick has resolved a required AI/sliced image in active context.

---

## 1. Core Principle — Maximize AI Image Capability in Service of the Deck

Pick whatever `page_role` and `text_policy` make the page work; everything else inside the bitmap is the AI's judgment — no mandated padding, no type-locked text policy, no scenario whitelist.

| `page_role` | Use |
|---|---|
| `local` | Composed by SVG within the page — boxed, unboxed, repeated as chrome, or the dominant non-full-canvas visual; SVG owns geometry and carrier combination |
| `hero_page` | The page's main voice — cover, chapter divider, mood transition, single-number hero, closing quote; SVG above may be minimal or empty |

| `text_policy` | Use |
|---|---|
| `none` | No text inside the image |
| `embedded` | Stable text as part of the artwork — decorative lettering, wordmarks, hand-lettered words, figure-internal labels |

**Hard rule — only what is actually hard**: one `deck_rendering` and the same core deck color anchors for every image in the deck; HEX codes and color names are rendering guidance, never visible text; long copy, data points, bullet lists, and quotes stay in SVG; in-image text is only for words that will never need editing (one in-image word costs a regeneration, one SVG word a keystroke); prompts are one coherent prose paragraph, not tag soup.

---

## 2. Style and Composition Inputs

| Dimension | Decides | When fixed |
|---|---|---|
| **Rendering** | Visual style family (vector / sketch-notes / 3d-isometric / corporate-photo / …) | Once per deck |
| **Deck colors** | Core background / primary / accent / secondary-accent / text anchors from `spec_lock.md colors` (Default) or the active-context decisions (Quick) | Default after Stage 2; Quick before acquisition |
| **Type** | Optional recall for a local structural infographic's skeleton (infographic / flowchart / framework / matrix / cycle / funnel / pyramid / comparison / timeline / map / scene); omit when no template fits, for single-subject/portrait, and for `hero_page` | Per image |

Rendering decides how the image is drawn; color begins from the deck roles — background / secondary background dominate the field, primary carries main forms, accents stay scarce — with context-justified lighting, material, and tint transitions but never an unrelated image-only palette.

**Hard rule — on-demand loading**: read [`image-renderings/_index.md`](./image-renderings/_index.md) and [`image-type-templates/_index.md`](./image-type-templates/_index.md) once at role entry; after resolving inputs read only the selected preset rendering file, the exact custom references, and the type files actually used. Never glob a subdirectory.

---

## 3. Workflow

1. **Load the indices** above.
2. **Resolve deck rendering + colors.** Default: `spec_lock.md colors` already carries `image_rendering` and the role HEX (`image_rendering: vector-illustration`, `background: #F8F9FA`, `primary: #1E3A5F`, `accent: #D4AF37`) — identity anchors, not a second user-facing choice. Quick: the agent resolves one rendering/color set in context and writes it to `image_prompts.json`. **`custom`**: read every `image_rendering_references` file when the row exists — apply one basis under `image_rendering_behavior`, or synthesize several by their stated line, texture, depth, material, and mood contributions; with no references use the behavior alone; never infer adjacent references. **Missing `image_rendering` key in an existing lock** ([`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2): infer the rendering from `design_spec.md d. Style` plus the intended image jobs against the complete catalog, keep the existing color rows as anchors, sanity-check against `icons.library`, choose the strongest fit without presenting a choice, print "spec_lock.md has no `image_rendering`—inferring `<X>` from design_spec; image colors still use the locked deck roles.", and stop for lock repair if the inference lands on `custom` or the value is empty/invalid; outside Quick, an absent lock stops at Generate Step 5. Then read the single resolved rendering file (an 80–120-word style paragraph plus two fewshot snippets).
3. **Per-image type + assembly.** Explicit row values bind; Quick resolves omissions. `Layout pattern` is never copied into the prompt; when page use depends on stable composition, carry the row's `Reference` / §IX / active-context contract — subject and quiet zones, boundary or direction, overlap/seam, approximate share — without inventing layout. `page_role`: the row's value, else `local` (`hero_page` is Strategist-explicit in Default; Quick may resolve it). `text_policy`: the row's value, else `none` or `embedded` from `Purpose`, `Reference`, and page intent. Type: an Illustration Sheet omits `type` and follows §4.3; another local structural infographic takes one of the 11 types only on a real index match, otherwise §4.1 E prose; a local single-subject/portrait uses §4.1 A/B; a `hero_page` uses §4.1 A–E. Read `image-type-templates/<type>.md` only when selected. Assemble one paragraph from the rendering style paragraph, the deck color behavior, the type layout or composition prose, the `Reference` intent as concrete visual nouns, the container note, and the §5 hard rules.
4. **Write the manifest (§6) and execute the selected path (§7)** — Default's confirmed path, Quick's explicit path or `auto`, without asking.

---

## 4. Prompt Assembly Template

```
[Rendering style paragraph — 80–120 words from the chosen rendering file].
[Deck color behavior — the core anchors and any context-justified tonal treatment, e.g. "secondary background #F8F9FA provides the breathing field, primary #1E3A5F carries main forms, accent #D4AF37 marks one emphasis; subtle lighter/darker material transitions stay in the same visual family"].
[Composition — from the chosen type file or §4.1 prose].
[Image-specific subject — the row's Reference intent as concrete visual nouns].
[Container note — "composed as a {W}x{H}px image for {page_role} use"; carry the owned composition contract when one exists. Reserve an SVG-overlay region for `hero_page`, or for a `local` image only when §VIII / §IX explicitly plans native labels, hotspots, lenses, or overlays there; otherwise an opaque local image reserves no interior space, and a transparent slice is an isolated element].
[Hard rules — §5].
```

Budget 150–300 words (embedded-text prompts longer, pure backgrounds shorter). **Forbidden — tag soup** (`"modern, flat design, gradient, vibrant, professional, clean, 4K"`): it produces model-average output; write one coherent visual scene.

### 4.1 No-type composition primitives

A/B describe a hero or a local single-subject region; C/D are hero-page compositions; E authors any custom composition, including a structural infographic no type template matches.

- **A — single dominant subject**: one focal subject placed with intent (centered, thirds, slight offset), scaled to command the container, supporting context subordinate, a deliberate open side only when the page needs it. Product reveal, concept introduction, chapter-opener, brand statement, local object region.
- **B — single human subject (portrait)**: one person, frontal or three-quarter, head and upper body, face as the focal point with eyes near the upper-third line, neutral or softly blurred background, comfortable headroom, framing adapted to the container. Founder, speaker, testimonial, executive, local bio; figure treatment follows the rendering (§5.2).
- **C — typographic hero**: one large text element — a word, phrase, headline, number, or short multi-line lockup — rendered as art with dominant weight, any supporting visual subordinate, breathing room scaled to the text. `text_policy: embedded`; copy that must stay exact or editable goes to SVG (switch to D).
- **D — atmospheric backdrop** (`hero_page` only): gradients, subtle patterns, or restrained color blocks with no dominant subject (a small geometric anchor may sit in a corner or along an edge), activity arranged around the planned SVG overlay region so it stays calm; a `local` image reserves only a named focal/quiet area instead. Cover and divider backgrounds, breathing pages, any page where SVG carries the words.
- **E — custom**: when none of A–D fits (triptych, asymmetric multi-focal, narrative diorama), write the composition directly in the composition sentence — one paragraph of 2–5 sentences stating subject count and layout structure concretely enough to execute, with breathing room or an overlay region only when the page needs it; a primitive name alone is not a description. Example: *Triptych — three equal vertical bands, each holding one symbolic object centered on a shared low horizon; bands separated by 2px hairline rules; reads as one composed page.*

**Fewshot per primitive** (deck-context placeholders intact):

> **A — 3d-isometric product reveal, `none`, 600×600**: 3D isometric illustration in true 30°/30°/30° projection. One dominant product-form subject — a stylized device or sleek tech object — commands the center of the canvas, rendered in primary electric blue `#0EA5E9` on its lit faces with a 15% darker tonal shift on shadowed faces and a subtle 8%-opacity outer glow. Small supporting context: three thin connecting lines in accent vivid cyan `#06B6D4` arcing from the subject toward the edges, and a soft 8% drop shadow grounding it. Background is deep secondary navy `#0A0E27`, including the shadowed plane. The subject is the singular focal element with deliberate breathing room. Composed as a 600×600 hero block. NO text, letters, numbers, or labels anywhere. Color values are rendering guidance only.

> **B — corporate-photo executive headshot, `none`, 600×800**: Editorial corporate portrait of one professional executive, centered slightly left, chest-up at eye level, looking confidently toward the camera with a relaxed natural expression. Contemporary business attire in a neutral palette. Soft natural light from the upper left, gentle shadow on the right side of the face. Background a softly out-of-focus office — secondary light gray `#F8F9FA` wall with a hint of primary deep navy `#1E3A5F` in a blurred architectural element. Restrained professional grading, shallow depth of field, eyes near the upper-third line with comfortable headroom. Composed as a 600×800 bio portrait. NO text, name tags, or captions. Color values are rendering guidance only.

> **C — ink-notes big-number stat, `embedded`, 800×500**: Professional hand-drawn visual-note style on pure white. The central content is the hand-lettered number "100x" in bold confident ink strokes, centered with the slight wobble of hand-lettering; a thin hand-drawn underline beneath; one small doodle — a star or upward arrow — beside it for rhythm. Accent coral `#E8655A` appears only as a tiny emphasis dot under 4% of the canvas. Background pure white `#FFFFFF`. Composed as an 800×500 typographic hero with enough room for the letterforms. No other text or labels — just "100x" and the doodle.

> **D — vector-illustration cover background, `none`, 1280×720**: Clean flat vector backdrop with no central subject — bold geometric shapes along the canvas edges leaving the planned central title field calm. Primary deep navy `#1E3A5F` forms a confident diagonal block across the lower left; secondary light gray `#F8F9FA` provides the breathing field; accent gold `#D4AF37` appears only as one thin geometric line near the lower right, under 5% of the canvas. Crisp 2px outlines, no gradients, a single 8% soft drop shadow under the navy block. The intended SVG title region stays calm. Composed as a 1280×720 full-bleed background. NO text, letters, numbers, signs, watermarks, or written symbols anywhere. Color values are rendering guidance only — do not display HEX codes or color names as text.

### 4.2 Prompt depth — expand for subject-domain accuracy

**Hard rule**: for scientific, academic, engineering, medical, legal, or otherwise regulated figures, expand without a ceiling — 500–1000+ words is normal, and §4's budget is a routine-illustration default, never a cap. **Forbidden — pre-emptive shortening.** Name the field's visual conventions explicitly: chemistry/materials (IUPAC atom colors, bond conventions, lattice type, Å / ps units, A/B/C subplot circles, view angle), biology (compartment colors, scale bars, organelle and staining conventions), physics (axis symbols, signature curve shapes, units, peak labeling), engineering (schematic notation, dimension callouts, section cuts) — illustrative, not an enumeration. Read `sources/` when uncertain.

### 4.3 Illustration sheets — one generation, many composable elements

A sheet generates compatible transparent **illustration**, **illustrated-icon**, or **decorative lettering** elements sharing rendering, deck-color treatment, and finish; subjects, silhouettes, weights, and jobs may differ, and SVG composes after slicing. Lettering is stable Layer 1 artwork, never page copy turned into an image.

**Default — batch compatible elements; split when separate generation improves the result**: group illustrated-icon cues normally, group lettering by compatible letterform character and treatment (not font name), and split for style, geometry, detail, quality, or semantic precision. A single element may use a keyed `1x1` sheet; full-canvas or opaque images take the normal §4.1 path.

**Hard rule — a sheet is a generation source, not a slide asset**: never referenced from SVG; out of `spec_lock.md images` in Default, generation-only in Quick's context and manifest; only sliced element rows are placed. **Hard rule — separable treatment before keying**: when the slice excludes a supporting surface, choose a treatment whose complete visible geometry stands alone against the key field; engraved, etched, debossed, inlaid, or bas-relief treatments are valid only when their carrier belongs in the slice — never define a carrier as necessary and ask the prompt to remove it.

**Sheet prompt convention** — one `page_role: local` item with `image_size` from final placement; spot sheets `text_policy: none`, lettering sheets `embedded`:

- Derive `aspect_ratio` and `--grid` from the target shape, not a universal square grid. State an invisible logical **R×C grid** and the cell shape (compact square object, tall portrait, wide vignette, wide lettering mark); center and isolate each element with even clear gutters; never draw cells, panels, dividers, borders, frames, or alternate gutter colors; never shrink every subject into a square sticker.
- One flat chroma key across the sheet — pure `#00FF00`, `#0000FF`, or `#FF0000`, chosen so its color dominates no element or effect — stated as exact HEX, unchanged in every gutter, free of reflections or spill; grain, halftone, and vignette stay inside elements. The key is technical, not deck palette.
- Shared `deck_rendering` + `color_scheme`.
- Illustration / illustrated-icon sheet: name each element and its page or reuse job; for an icon, the compact cue that must survive at placement size; the §5.3 `none` cue.
- Lettering sheet: exactly one named stable string per cell as the only text, quoted literally; the group's letterform character and treatment, then role, placement/background relationship, relative weight, and energy under §5.3's controlled-authorship default; artistry glyph-bound (silhouette, stroke structure, material, texture, depth, contour-bound light); no topic motifs, scene fragments, icons, detached ribbons, or particles unless the approved treatment is a lettering-plus-illustration lockup; key-only padding, no scene, unrelated copy, labels, watermark, or mockup surface.
- **Delivery floor, not an aesthetic ceiling**: enlarge the cell, change the grid, or use a larger or separate sheet when a treatment needs footprint; never weaken an approved treatment to fit a crop.

**Cell geometry is designed**: `slice_images.py --grid RxC` cuts rows first; `cell_ratio = sheet_ratio × rows / cols`. On a wide sheet `1xN` yields tall cells and `Nx1` wide cells; any `MxN` is valid when its cells match the placements.

| Target element shape | Sheet plan | Slice grid |
|---|---|---|
| Compact objects / badges / illustrated icons | `1:1` sheet | `2x2`, `2x3`, or `3x3` |
| Tall side accents / upright objects | wide or square sheet | `1xN`, or any `MxN` with portrait cells |
| Wide banners / horizontal vignettes | wide sheet | `Nx1`, or any `MxN` with landscape cells |
| Large page anchors / dominant cutouts | dedicated sheet matching the silhouette | `1x1` |
| Decorative words, phrases, multi-line lockups | wide sheet | `Nx1`, or any `MxN` fitting the string shapes |

Shape families that cannot share a roomy grid take separate sheets; coherence comes from rendering and colors, not one forced sheet.

**Resource contract**: a **sheet row** is `Acquire Via: ai`, `Type: Illustration Sheet`, named as the slice source with intent, cell shape, and purpose (`Reference: reusable title/corner illustration family`, `illustrated-icon set: cues = ...`, or `decorative lettering set: exact strings = ...`); Step 5 generates it, it is never placed, and Image_Generator resolves its aspect ratio, grid, and slice command. **Element rows** are one per used element, `Acquire Via: slice`, filename matching `--names`, `Reference` naming the parent and cell, listed in the placeable authority normally with `crop=no-crop` (tight slices use fit, not cover-crop), `Type: Illustrated icon` for a compact cue (never an SVG library entry), reusable across pages, each carrying an owner-resolved layout recommendation, dimensions filled after slicing by `analyze_images.py`. Add `slice_grid` and `slice_names` to the sheet's manifest item — the comma-separated basenames are the complete required output set.

```bash
SHEET_KEY_HEX="#00FF00"  # example only; choose a key absent from every element/effect
python3 scripts/slice_images.py <project>/images/illus_sheet.png --grid 2x3 \
    --names team,product,customer,growth,risk,vision --trim --alpha \
    --bg "${SHEET_KEY_HEX}" --strict-alpha
```

`--names` count equals `rows*cols`; `--strict-alpha` writes nothing on an incomplete cut. Three quality constraints: **strict key recovery** — raise `--tolerance` only enough to absorb measured flat-field drift, `--inset` only for an isolated outer gutter, and regenerate or enlarge when an effect reaches an edge; **clean isolated cells** — fused cells, scene backgrounds, or flourishes crossing a cell make the sheet unusable, and re-rolls follow only a strict keying failure or user/preview evidence, never taste; **enough source pixels** — each cell at least 1.5–2× its display size (`1K` small accents, `2K` medium, `4K` large or enlarged).

**Placement**: a slice is a decorative accessory, not a boxed picture — a spot wasted in a centered rectangle looks cheaper than none; it may stay unboxed at a margin, run off the canvas edge, sit behind or beside text with a slight rotation, vary in size and angle across pages, enter a container, or combine with backgrounds, shapes, text, photos, other slices, and lettering; stable chrome may repeat exactly while anchors and accents vary in scale, position, pairing, and interaction. Editable copy stays SVG; a large SVG-composed anchor remains `local` / `slice`, and `hero_page` applies only when one bitmap owns the page. No quota.

### 4.4 Registered reconstruction groups and shared plates

Use when a person, product, creature, effect, or scene element must cross native titles, panels, frames, cards, or shapes while the original scene stays behind it. Minimum group: a clean base plus one subject/foreground layer; add layers only for overlap or independent editing.

| Output | Required content |
|---|---|
| Clean base | Full original canvas with every planned removable element removed and the hidden background reconstructed |
| Optional midground | Full canvas with only the content that sits between base and primary subjects |
| Subject / foreground | Full canvas with one subject or one z-order-compatible set on RGBA transparency |
| Shared layer plate | Several mutually non-overlapping objects isolated together in one full-canvas or regular-cell output |

**Mandatory — preserve registration**: derive every full-canvas member independently from the same canonical source, keeping canvas dimensions, pose, scale, position, lighting, and style, never trimming or cropping a registered output; record the shared source and group in the owning rows. **Image to PPTX (Codex required)**: follow its §3 per-region decision — a complete, separable, resolution-sufficient region may stay source-derived, otherwise use Codex's native reference-image capability; inspect every member and the recomposition; do not adapt `image_gen.py` or its backends for that profile; other hosts unsupported.

Procedure: (1) from the canonical reference remove every planned subject, foreground object, source graphic, and editable text, then inpaint one clean base without redesigning the background; (2) prepare the subject/foreground as an exact source-derived layer or a reference reconstruction, never from a generated base or layer; (3) prefer one shared plate when objects do not overlap and share an isolation treatment, with padded bboxes (shadows and effects included) pairwise disjoint; (4) a registered plate keeps original positions with one nested-SVG crop per recorded bbox ([`svg-effects.md`](./svg-effects.md) §6.5), a rearranged regular-cell plate is sliced under §4.3 and each asset placed at its recorded bbox; (5) prefer direct RGBA, otherwise one exact flat key over the whole layer and one `1x1` `--alpha` slice without `--trim` so coordinates hold — never one keyed image per object; (6) save under `<project>/images/`, registered full-canvas members `no-crop`. Overlapping or differently ordered objects take separate layers; a shared output is valid only when every final object still becomes an independent picture.

> **Shared registered-plate prompt core**: Using the supplied canonical page as the only visual reference, isolate the following foreground objects together on one full-canvas extraction plate: {stable object ids/descriptions}. Preserve each object's visible identity, silhouette, pose, scale, rotation, lighting, shadow, and exact original canvas position; keep the original aspect ratio and registration; retain only the listed objects and remove the background and every unlisted element; do not rearrange, resize, merge, duplicate, or let objects touch; retain an explicitly listed source graphic or wordmark exactly and remove editable slide text and every unlisted logo. Return RGBA if supported; otherwise one uniform exact {key HEX} matte with no gradient, texture, spill, or extra marks.

Outside Image to PPTX, Path A uses single-image edit mode and Path B the host tool — the declared derivation exception for already-planned group rows, every member kept in the resource authority and sidecar; SVG realization follows [`image-layout-patterns.md`](./image-layout-patterns.md) `#A2-03`:

```bash
python3 scripts/image_gen.py "Remove the planned foreground subjects and reconstruct the hidden background; preserve the exact canvas" \
  --reference-image <project>/images/<source>.png -o <project>/images -f <group>_base
python3 scripts/image_gen.py "Isolate the planned non-overlapping foreground objects at their exact original positions on one flat #00FF00 plate" \
  --reference-image <project>/images/<source>.png -o <project>/images -f <group>_plate_key
python3 scripts/slice_images.py <project>/images/<group>_plate_key.png --grid 1x1 \
  --names <group>_plate --alpha --bg "#00FF00"
```

---

## 5. Global Hard Rules

Append these to every assembled prompt.

### 5.1 HEX is rendering guidance, not text

Models occasionally paint color names and HEX values as visible labels. Append: *Color values (HEX codes like #1E3A5F) and color names are rendering guidance only — do NOT display HEX codes, color names, or palette labels as visible text anywhere in the image.*

### 5.2 Human depiction follows the selected rendering

Match facial detail, anatomy, texture, and realism to the rendering and the row's Reference — silhouette, detailed illustration, painterly figure, or editorial photograph as that rendering allows. **Hard rule — likeness authorization**: never request an identifiable real-person or celebrity likeness unless the Reference explicitly names a user-authorized subject; generic or fictional people are free.

### 5.3 Text policy — two-layer ownership

| Layer | Owned by | Examples |
|---|---|---|
| Layer 1 (image-owned) | the prompt, baked into the raster | figure-internal annotations (axis labels, A/B/C markers, units, scale bars, panel labels); schematic module names, node labels, signal-path ids; stable artistic lettering that *is* the visual |
| Layer 2 (SVG-owned) | editable `<text>` overlay | authoritative deck/page/chapter titles; navigation, footer, body bullets, conclusion callouts; readable copy and captions |

`text_policy` controls only Layer 1, judged per image with no global bias. Positive triggers for `embedded` — a paper-figure panel comparison (panel labels), a textbook math or signal figure (curve names, axes, units), a discipline-convention schematic (`Self-Attention`, `FFN`, node ids), a data figure with stable axes, a typographic hero (§4.1 C) — start at `embedded` and then apply the editability filter; defaulting a whole `ai` list to `none` because "SVG can always overlay" is the failure mode this table breaks. Prompt cues: `none` → *"NO text of any kind anywhere in the image — no letters, numbers, signs, watermarks, labels, or written symbols."*; `embedded` → describe the exact characters, how they are rendered, and the treatment inside the scene.

**Hard rule — decide by editability, not model capability**: Layer 1 text can never be edited, corrected, searched, restyled, or reflowed. Text that is part of the artwork and stable — decorative lettering, a wordmark, a hand-lettered phrase, figure-internal identifiers — may be Layer 1; anything that must stay exact, searchable, editable, or may be reworded is Layer 2, whatever `text_policy` says: authoritative titles, chrome, navigation, footer, bullets, captions, data values. Bake title-like wording only when the approved plan treats those exact characters as stable artwork. Never pre-judge by script or length — never push text to SVG, shorten a headline, or downgrade `embedded` to `none` on the assumption that a script or long string "won't render"; a multi-word phrase or two-line lockup qualifies exactly as one word does. Name the exact characters literally; do not re-read the generated image to verify them. When the headline must stay editable, use Primitive D and overlay it.

**Reference — controlled, deck-aligned artistic authorship** (high expression on user request or a confirmed direction): give the model the exact string, communication role, placement/background relationship, deck identity, relative weight, and desired energy; the rendering, semantic colors, mood, and page hierarchy define the envelope. Glyph-native expression carries identity through silhouette, stroke construction, internal material/texture, contour-bound depth and light, and composition; literal topic illustrations or detached decoration compete with the glyph, and a lettering-plus-illustration lockup needs an explicit request or confirmed direction. Within the treatment let the model combine or omit gesture, material, dimensionality, texture, lighting, and hierarchy — possibility space, not a recipe; never flatten the art to ease extraction (§4.3's gates protect delivery); when fit is uncertain use the lower density; keep a multi-line lockup as one element when its hierarchy is part of the art.

**Font for in-image text** is a free description, not an enum — blackletter for a heritage cover, hand-brushed for a manifesto, retro chrome for Y2K, art-deco display for luxury, ribbon script for a zine. Echo the SVG body only when stable lettering should read as the same family as the deck's typography: serif families → "elegant serif lettering, refined letterforms"; sans (YaHei / PingFang / Arial) → "clean geometric sans-serif, modern letterforms"; display (SimHei / Impact / Arial Black) → "bold display lettering, heavy expressive strokes"; monospace → "monospace technical lettering, fixed-width"; sketch/ink renderings or no family → "hand-lettered organic strokes, natural variation". Ignore that echo for decorative or background lettering, posters, mood words, cover wordmarks wanting their own identity, hand-drawn renderings, or any rendering that already implies a period letterform.

### 5.4 No brand names or trademarks in the subject

The image must not depict identifiable logos, trademarks, or product likenesses unless the Reference explicitly names a real brand asset the user owns.

---

## 6. Manifest Schema

Write `project/images/image_prompts.json`:

```json
{
  "project": "{project_name}",
  "generated_at": "{ISO-8601 date}",
  "deck_rendering": "vector-illustration",
  "color_scheme": {
    "background": "#FFFFFF", "secondary_bg": "#F8F9FA",
    "primary": "#1E3A5F", "accent": "#D4AF37",
    "secondary_accent": "#4A7BB5", "body_text": "#1D2430"
  },
  "items": [
    {
      "filename": "cover_bg.png",
      "purpose": "Cover background (Slide 01)",
      "page_role": "hero_page",
      "text_policy": "none",
      "aspect_ratio": "16:9",
      "image_size": "2K",
      "prompt": "{fully assembled paragraph per §4 — Primitive D for an atmospheric cover}",
      "alt_text": "Modern tech abstract background with deep blue gradient and digital waves",
      "status": "Pending"
    },
    {
      "filename": "framework_p05.png",
      "purpose": "Methodology framework (Slide 05)",
      "type": "framework",
      "page_role": "local",
      "text_policy": "none",
      "aspect_ratio": "4:3",
      "image_size": "1K",
      "prompt": "{fully assembled paragraph per §4}",
      "status": "Pending"
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `deck_rendering`, `color_scheme` | yes | One rendering and the core color anchors shared by every item; no separate image palette |
| `items[].filename` | yes | Output filename with extension, from the resource authority |
| `items[].type` | no | One of the 11 internal-composition types for a local structural infographic when a template genuinely fits; omitted for §4.1 E prose, `hero_page`, sheets, and single-subject/portrait |
| `items[].page_role` | yes | `local` (default) or `hero_page` |
| `items[].text_policy` | yes | `none` or `embedded`, judged per image (§5.3) |
| `items[].aspect_ratio` | yes | Passed to `image_gen.py --aspect_ratio` |
| `items[].prompt` | yes | The assembled paragraph |
| `items[].image_size` | no | `512px` / `1K` / `2K` / `4K` |
| `items[].model` | no | Per-item backend model override |
| `items[].alt_text` | no | Short caption |
| `items[].slice_grid`, `items[].slice_names` | for a placeable-element sheet | Exact `RxC` and the comma-separated basenames (`rows*cols` unique outputs) for `slice_images.py` |
| `items[].status` | yes | `Pending` initially; the CLI writes `Generated` / `Failed` / `Needs-Manual` |

**Compatibility**: legacy `type` values read as `background` → `hero_page` + no type, `hero` → `hero_page` + Primitive A, `portrait` → `local` + Primitive B, `typography` → `hero_page` + `embedded` + Primitive C; a missing `page_role` is `local`, a missing `text_policy` is `none` (one aggregate warning per manifest); an existing manifest lacking `deck_rendering` or an item lacking `type` replays its assembled `prompt` verbatim without reconstruction; a legacy `deck_style_anchor` or `deck_palette` never overrides `deck_rendering` / `color_scheme`; legacy `page_role: full_page` reads as `hero_page`.

---

## 7. Generation Execution

Prerequisite: §3 complete and `images/image_prompts.json` validates. The manifest is the shared contract for every mode; it never implies that `image_gen.py --manifest` runs — that command is Path A only.

| Trigger | Mode | Mechanism |
|---|---|---|
| `api`, or `auto` with `IMAGE_BACKEND` configured | **Path A** `image_gen.py --manifest` | One command runs the manifest with concurrency and writes status per item |
| `host-native`, or `auto` with a host image tool | **Path B** host-native tool | The agent invokes the host capability; outputs land at `project/images/<filename>` |
| Default confirmed `manual`, or Quick explicitly `manual` | **Offline Manual** | Manifest stays on disk; the user generates from `items[].prompt` and places files |

**Path selection**: planning never inspects configuration or probes a provider — capability is resolved only here. Default honors `AI Image Acquisition Path` from `design_spec.md §I` (already consumed from the confirmation; never reopen `result.json`): `api` → Path A; `host-native` → Path B, skipping A even when `IMAGE_BACKEND` is configured; `manual` → Offline Manual; `auto` → Path A when `IMAGE_BACKEND` is configured (two consecutive failures fall to B), then Path B when the host has a native tool, never Offline Manual by itself; a missing row returns to Step 4 recovery. Quick honors an explicit `api` / `host-native` / `manual` instruction, otherwise `auto` A → B without asking. **Hard rule**: normal execution never reopens selection; a confirmed path that fails after its retry never switches provider — Default enters the recovery decision below, Quick applies its no-AI replan. All modes share one output contract: a file at `project/images/<filename>`.

### Path A — `image_gen.py --manifest`

```bash
python3 scripts/image_gen.py --manifest project/images/image_prompts.json --output project/images
```

Validates the file behind every `Generated` row before skipping it, iterates retryable rows with bounded adaptive concurrency, and writes each status atomically; a missing or corrupt file returns to `Failed`, and persistent rate limits end the run as retryable `Failed`. Options: `--concurrency` (default `IMAGE_CONCURRENCY` or 3; halves on rate limit, min 1), `--image_size`, `--output`/`-o`, `--backend`/`-b`, `--model`/`-m`, `--list-backends`. Interrupting is safe (completed items stay `Generated`); the Markdown sidecar re-renders on completion, or run `--render-md` after an interruption. Configuration: process environment first, then the first `.env` in cwd, the skill directory, the clone root, `~/.ppt-master/.env` — `IMAGE_BACKEND` (required; `--list-backends` shows the set and support tiers), `IMAGE_CONCURRENCY`, provider-specific `{PROVIDER}_API_KEY` / `_BASE_URL` / `_MODEL` (never `IMAGE_API_KEY` / `IMAGE_MODEL` / `IMAGE_BASE_URL`), and for OpenAI-compatible platforms `OPENAI_SIZE_PRESET` (`auto|legacy|gpt-image|gpt-image-2|dall-e-2`), `OPENAI_RESPONSE_FORMAT` (`auto|b64_json|url|omit`), `OPENAI_QUALITY` (`auto|omit|low|medium|high|standard|hd`) under `IMAGE_BACKEND=openai`; see `.env.example`. The single-image form `image_gen.py "prompt" --filename …` remains for ad-hoc re-rolls.

### Path B — host-native image tool

Automatic when `IMAGE_BACKEND` is unset or Path A failed and the host (Codex, Antigravity, Claude Code, similar) offers an image tool; the user may also name it explicitly. Prompts come from `items[].prompt`; never run `image_gen.py --manifest` here, but still run `python3 scripts/image_gen.py --render-md project/images/image_prompts.json` for the sidecar. Batch a few rows at a time (~3–4) when the host runs tools in parallel, serially otherwise. Outputs land at the resource-list filename; hosts with fixed native resolutions generate at the closest size and backfill the actual pixels into `Dimensions` — never upscale to fake a size (display-side upscaling up to ~1.3× is a non-blocking warning). Mark each item `Generated` as its file lands.

### Offline Manual Mode

Entered only after Default confirmed `manual` (Stage 2 or the recovery decision) or an explicit Quick instruction — never asked again inside acquisition. Verify the manifest, set `status: "Needs-Manual"` on every affected item ([`image-base.md`](./image-base.md) §3), and print one consolidated handoff: filenames, the `images/image_prompts.md` paste-ready blocks (or `items[].prompt`), the exact target `project/images/<filename>`, and the continuation — Default draws dashed placeholders and blocks every Step 7 export command until files are validated and placeholders replaced; Quick blocks direct export until every required row is validated and reconciled to `Generated`, and only while the original context survives (otherwise a clean run).

#### Default exhausted-automation decision

When required rows stay unresolved after the confirmed path or `auto`'s A → B, keep them `Failed`, pause once with one consolidated list (filenames, prompts, attempted paths, concrete errors), and ask for exactly one outcome: **repair and retry** (the same confirmed path; `auto` keeps A → B; a repeat failure returns here with the new error), **generate manually** (record `AI Image Acquisition Path: manual` in `design_spec.md §I`, mark rows `Needs-Manual`, hand off, author up to the Step 7 readiness gate), or **cancel the affected AI images** (return to Step 4 as a post-confirmation override, remove the `ai` and dependent `slice` rows, revise their §IX jobs and lock rows to native text/SVG or confirmed non-AI sources, set the path `not applicable` when no AI rows remain, never add a new source or drop required content). Never create `Needs-Manual` before manual fulfillment is confirmed.

#### Quick exhausted-automation no-AI replan

Do not ask and do not enter Offline Manual: retain the filename, attempted path, concrete error, and replacement carrier for the completion report; remove the `ai` row, its dependent `slice` rows, and the manifest item; re-render `image_prompts.md` when other items remain, otherwise delete both manifest files; carry the communication job with native text/SVG or prepared non-AI assets; add no other source. Retaining AI imagery means repairing capability and a new Quick run.

**Failure handling** (extends [`image-base.md`](./image-base.md) §3): on `auto`, two consecutive Path A failures fall to Path B without halting; if B also fails, Default enters the decision above and Quick the replan. A confirmed `api` or `host-native` path is retried once, never switched. If an alternate platform watermarks outputs (e.g. Gemini web), `scripts/gemini_watermark_remover.py` exists. **Guardrails**: never claim an image exists without a file at its path; `Needs-Manual` only on confirmed or explicit manual; status transitions are evidence-driven — a file permits `Generated`, exhausted Default automation stays `Failed` until a retry succeeds or the user chooses, exhausted Quick rows leave only through the replan.

---

## 8. Common Issues & Variant Workflow

**Blank `Reference` on an existing AI row — declared inference** from a non-empty `Purpose` (stop and repair when `Purpose` is blank too): cover → `hero_page` + Primitive A or D; chapter divider → `hero_page` + D or A, chapter title in SVG; methodology / framework → `type: framework`, `local`; process → `type: flowchart`, `local`; before/after → `type: comparison`, `local`; team or lifestyle group → `type: scene`, `local`, `corporate-photo` or `warm-scene`; headshot → `local` + Primitive B, `corporate-photo`; big number or hero quote → `hero_page` + Primitive C, `embedded`; mood transition → `hero_page` + D, or `type: scene` when narrative.

**Unsatisfactory images** — adjust the one dimension responsible, never rewrite the whole prompt:

| Symptom | Cause | Adjustment |
|---|---|---|
| Generic, model-average | Tag-soup prompt | One coherent paragraph per §4 |
| Wrong style family | Rendering paragraph diluted | Reaffirm the rendering paragraph at the top |
| Colors off-deck | Role anchors or proportions diluted | Restate which roles own field, forms, and accents; remove unrelated hues |
| Lettering unrelated, overdecorated, or too dominant | Expression exceeded the deck identity or planned weight | Keep the string and family; lower effect density, ornament, contrast, or lighting energy |
| Lettering surrounded by mountains, buildings, animals, icons, ribbons | The model turned topic context into an unrequested lockup | Remove every external motif; express identity through glyph structure, material, texture, depth, light |
| HEX or color name visible as text | Missing §5.1 sentence | Append it verbatim |
| Garbled letters in a text-free image | `none` cue too weak | Enumerate: no letters, numbers, words, signs, labels, captions, watermarks |
| SVG overlay clashes with a busy region | No calm-region cue | Add "leave the {center / left third / lower band} calm for text overlay" only when text really overlays |
| Subject vague | Abstract Reference | Concrete nouns (verbs + objects) |
| Human depiction off-style | §5.2 cues diluted | Restate the rendering's facial detail, anatomy, texture, realism |

**Variant workflow**: set the item's `status` back to `Pending`, update its `prompt` in place, rerun the same resolved path (Path A reprocesses only that item; Path B regenerates it; Manual re-renders the sidecar); for several stylistic tries append items with distinct filenames (`cover_bg_v2.png`).

---

## 9. Forbidden

- Prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description
- Mixing renderings or an unrelated image-only palette within one deck — `hero_page` is no exception
- Tag-soup prompts
- Globbing `image-renderings/*.md` or any subdirectory
- Placing an image without updating `image_prompts.json` `status` and the resource authority
- Embedding body copy, data points, bullet lists, or long quotes in an image
