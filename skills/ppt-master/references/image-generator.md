> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: convert each active `Acquire Via: ai` row into an optimized prompt, generate the image, and save it to `project/images/`; also defines the `slice` derivation path for AI-generated illustration, illustrated-icon, and decorative-lettering sheets.

**Trigger**: the Default Generate resource list contains `Acquire Via: ai` or `slice`, or Quick Generate has resolved a required AI/sliced image in active context. Load only when at least one such resource exists.

---

## 1. Core Principle — Maximize AI Image Capability in Service of the Deck

AI images exist to serve the deck's communication goal. Pick whatever combination of `page_role` and `text_policy` makes the page work best.

**Two page roles** (orthogonal to type):

| `page_role` | Use |
|---|---|
| `local` | Image or transparent element is composed by SVG within the page. It may be boxed, unboxed, repeated as chrome, or become the page's dominant non-full-canvas visual; SVG owns final geometry and carrier combination |
| `hero_page` | Image is the page's main voice — cover, chapter divider, mood transition, single-number hero, closing quote. SVG above may be minimal or empty |

**Two text policies** (orthogonal to page_role):

| `text_policy` | Use |
|---|---|
| `none` | No text inside the image |
| `embedded` | Image contains stable text as part of the artwork — decorative lettering, artistic wordmarks, hand-lettered words or phrases, or figure-internal labels |

**Hard rule — only what's actually hard**:

- Same `deck_rendering` + same core deck color anchors/semantic behavior for every image in the deck
- HEX codes and color names are rendering guidance — never visible text in the image
- Long body copy / data points / bulleted lists / long quotes stay in SVG (improving them later means regenerating the image, which is expensive)
- **In-image text is only for words that will not need editing later** — visual keywords, decorative lettering, mood words. Editable text (titles that may be reworded, subtitles, dates, authors, captions, body) belongs in SVG. Changing one in-image word costs an image regeneration; one SVG word costs a keystroke.
- Prompts are one coherent prose paragraph, not tag soup (a model-output reality, not an aesthetic choice)

Everything else inside the prepared bitmap is the AI's judgment per page. No mandated padding, no type-locked text_policy, no scenario whitelists for hero_page.

---

## 2. Style and Composition Inputs

Every AI image uses one deck-wide rendering, the deck's stable color anchors/semantic behavior, and a per-image type / internal composition. Only rendering is a separate image-direction decision.

| Dimension | Decides | When fixed |
|---|---|---|
| **Rendering** | Visual style family (vector / sketch-notes / 3d-isometric / corporate-photo / …) | Once per deck — every AI image in the deck shares one rendering |
| **Deck colors** | Core background / primary / accent / secondary-accent / text anchors from `spec_lock.md colors` in Default Generate, or from the active-context visual decisions in Quick Generate | Default: anchored after Stage 2; Quick: resolved before acquisition |
| **Type** | Optional recall for a local structural infographic's internal skeleton (infographic / flowchart / framework / matrix / cycle / funnel / pyramid / comparison / timeline / map / scene). Use it when one template fits; otherwise omit type and write the composition directly in §4.1 E prose. Local single-subject/portrait and `hero_page` images also omit type. | Per image |

> Rendering decides *how the image is drawn* (line quality, texture, depth). Color instructions begin from the deck roles: background / secondary background usually dominate, primary carries main forms, and accents stay scarce. Adjust proportions and derive coherent lighting/material/tint transitions for the image context; do not replace the deck's identity with an unrelated image-only palette.

### 2.1 Where to find each dimension

| Reference | Loaded |
|---|---|
| [`image-renderings/_index.md`](./image-renderings/_index.md) — rendering catalog + auto-selection table | Always (Step 1 below) |
| [`image-type-templates/_index.md`](./image-type-templates/_index.md) — type catalog + auto-selection table | Always (Step 1 below) |
| `image-renderings/<chosen>.md` | After Step 2 resolves the rendering — one preset file, or every exact reference listed for `custom` |
| `image-type-templates/<chosen>.md` | After Step 3 picks the type per image — only the types actually used |

**Hard rule — on-demand loading**:

- Read the rendering and type `_index.md` files once at role entry.
- After locking inputs, read **only** the specific preset rendering, custom rendering references, and type files selected.
- **Never** glob-read an entire subdirectory (`image-renderings/*.md` is forbidden). Token cost balloons and the AI loses focus.

---

## 3. Workflow

### Step 1 — Load the dimension indices

Read the two index files that own user-visible image direction and per-image internal composition.

```
read_file references/image-renderings/_index.md
read_file references/image-type-templates/_index.md
```

### Step 2 — Resolve deck-wide rendering + deck colors

**Default Generate path — Strategist already recorded rendering and core deck color anchors in `spec_lock.md colors`**:

```
image_rendering: vector-illustration
background: #F8F9FA
primary: #1E3A5F
accent: #D4AF37
```

Use them as identity anchors. Do not create another user-facing image-color choice. The rendering and image subject may derive coherent tonal transitions, material colors, lighting, and atmospheric hues when the context requires them, while the core roles keep their established meaning.

**Quick Generate path**: the main agent resolves one active-context rendering/color set, honoring explicit user values and deciding the rest without interaction. Write it to `image_prompts.json`; create no planning artifacts.

**Hard rule — `custom` catalog basis**: when `image_rendering` is `custom`, first inspect the optional `image_rendering_references` row. If present, read every exact `image-renderings/<id>.md` it lists and synthesize their line, texture, depth, material, and mood guidance under `image_rendering_behavior` before assembling prompts. If absent, the custom is genuinely novel: read no preset file and use `image_rendering_behavior` directly. Never infer or add adjacent references during execution. The deck color-role rows remain authoritative.

**Declared-inference fallback — when an existing `spec_lock.md` omits the `image_rendering` key** (see [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2):

This fallback covers a missing key only. An empty or invalid value stops for lock repair. Outside the active [`quick-generate`](../workflows/profiles/quick-generate.md) profile, if `spec_lock.md` itself is absent, stop at [`generate-pptx.md`](../workflows/generate-pptx.md) Step 5 before prompt assembly or image generation; do not use `design_spec.md` as a substitute.

| Signal | Maps to |
|---|---|
| `design_spec.md d. Style` mode + descriptor | Rendering (consult renderings `_index.md` auto-selection table) |
| Existing `spec_lock.md colors` rows | Deck color anchors; interpret them with the completed `design_spec.md`, never replace confirmed identity from a second palette |
| Existing `spec_lock.md icons.library` | Sanity check: chosen rendering should be compatible with the icon library's visual weight |

If rendering inference surfaces multiple candidates, pick the first; do not present another choice after confirmation.

If the table returns `custom`, stop and repair the lock: authoring `image_rendering_behavior` is a planning decision this fallback cannot make, and the deck's SVG style prose is not an image-rendering description.

> **Tell the user**: when falling back, print one line "spec_lock.md has no `image_rendering`—inferring `<X>` from design_spec; image colors still use the locked deck roles." Then proceed.

Then read the **single resolved** rendering file. It gives you:

- The 80-120 word style paragraph (rendering)
- Two ready-to-paste rendering snippets (fewshot)

Derive color behavior from the available roles and image context: background / secondary background usually carry most of the field, primary carries main forms, and accent / secondary accent remain selective. A rendering may justify a different balance and coherent derived tones; decorative text colors must remain readable. Add a new lock role only when that derived color becomes a reusable cross-image semantic token.

### Step 3 — Per-image type + assembly

For each `Acquire Via: ai` row, use Strategist-owned §VIII/lock by default or the main agent's active-context Quick resource decision. Explicit values remain binding; Quick resolves omissions automatically.

`Layout pattern` is a page-realization preference and is not copied wholesale into the bitmap prompt. Any generation-time subject direction, focal placement, quiet region, or overlay-safety requirement must therefore be present in the row's `Reference`, the matching §IX block, or Quick's active-context visual intent.

1. **Determine `page_role`** — the owning row's explicit value wins; a blank or omitted value resolves to `local`. In Default Generate, `hero_page` must be Strategist-explicit; in Quick Generate, the main agent may resolve it before acquisition in active context.
2. **Determine `text_policy`** — the owning row's value wins when set. **Declared-inference fallback for a blank or omitted value**: pick `none` or `embedded` from the row's `Purpose`, `Reference`, and page intent based on whether in-image text serves the page. Long body / data / lists stay in SVG.
3. **Determine type or free composition** — an Illustration Sheet omits manifest `type` and follows §4.3's grid composition. For another local structural infographic, use one of the 11 types only when the `_index.md` offers a real match; otherwise omit type and author the intended structure directly with §4.1 E. A local single-subject/portrait image omits type and uses §4.1 A/B inside its actual region. A `hero_page` omits type and uses §4.1 A/B/C/D/E.
4. `read_file references/image-type-templates/<type>.md` only when a type was selected (and only if not already read).
5. **Assemble the prompt** by combining:
   - The rendering's style paragraph (from Step 2)
   - Color-role instructions anchored by the deck HEX values and refined for the image context (from Step 2)
   - The selected type's structural layout, or the no-type composition prose (from Step 3)
   - The image's specific `Reference` intent (from `design_spec.md §VIII` or the Quick Generate active-context decision)
   - Container sizing from the selected type file, or the row's Dimensions for no-type prose
   - The hard rules from §5 below (HEX-not-as-text, rendering-aligned human depiction and likeness authorization, text policy)

The assembled prompt is **one cohesive paragraph**, not a bulleted list of tags. See §4 for the assembly template.

### Step 4 — Write the manifest and execute the selected path

Write `project/images/image_prompts.json` per §6, then follow §7. Default uses its confirmed path; Quick uses an explicit active-context path or `auto` without asking.

---

## 4. Prompt Assembly Template

Every assembled prompt follows this paragraph structure. **Write prose, not tag soup**.

```
[Rendering style paragraph — 80-120 words from the chosen rendering file].
[Deck color behavior — state the core anchors and any context-justified tonal treatment, e.g. "secondary background #F8F9FA provides the breathing field, primary #1E3A5F carries main forms, accent #D4AF37 marks one emphasis; subtle lighter/darker material transitions remain in the same visual family"].
[Composition — from the chosen type file or §4.1 no-type prose].
[Image-specific subject — translated from the row's Reference intent into concrete visual nouns].
[Container note — "composed as a {W}x{H}px image for {page_role} use"; add composition cues only when the page actually needs them. SVG-overlay-reservation cues ("leave the lower band calm — SVG title overlays it", "keep the right third calmer for SVG text") are valid when `page_role: hero_page`, or when §VIII `Reference` / §IX `Layout` explicitly plans native labels, hotspots, lenses, or other SVG overlays inside a `local` image region. Otherwise an opaque `local` image reserves no interior overlay space; a transparent illustration slice is generated as an isolated element and composed with other carriers by SVG].
[Hard rules — see §5].
```

**Word budget**: 150-300 words. Embedded-text prompts skew longer; pure background prompts can be shorter.

**Forbidden — tag-soup prompts**:

```
❌ "modern, flat design, gradient, vibrant, professional, clean, 4K, high quality"
```

This produces generic, model-average output. The model is not weighting your tags — write **one coherent visual scene** instead.

### 4.1 No-type composition primitives

Use these when no structural type applies. A/B can describe either a hero image or a local single-subject/portrait region; scale their framing to the actual container. C/D are hero-page compositions. E authors any custom hero or local composition, including a structural infographic that does not genuinely match one of the 11 type templates.

**Primitive A — single dominant subject (product / object / concept hero)**

> Start with one dominant subject as the clear focal point, positioned with intent (centered, rule-of-thirds offset, or slight left/right). Scale it to command the container while keeping supporting context subordinate. Leave a deliberate open side when the page composition needs breathing room or an overlay; no fixed padding is implied. No second-place subject competing.

Use for: product reveal, concept introduction, chapter-opener visual, brand statement, or a local single-object region.

**Primitive B — single human subject (portrait)**

> One person, frontal or three-quarter turn, head + upper body. Start with the face as the clear focal point, centered or rule-of-thirds offset, with eyes near the upper-third horizontal line. Background neutral, minimal, or softly blurred. Keep comfortable headroom and no competing foreground objects; adjust framing to the container rather than enforcing fixed padding.

Use for: founder profile, speaker bio, testimonial page, or executive intro, including a local bio region. Let the chosen rendering and Reference determine photographic, editorial, painterly, graphic, or other figure treatment; see §5.2.

**Primitive C — typographic hero (the text *is* the image)**

> The image's central content is one large text element — a single word, a phrase, a headline, a big number, or a short multi-line lockup — rendered as art and carrying dominant visual weight. Keep any supporting visual (small icon, geometric anchor, accent line) clearly subordinate. Give the letterforms enough breathing room for readability, adjusting scale and spacing to the actual text and container.

Use with `text_policy: embedded`. Must obey the §5.3 rule — text that is part of the artwork and stable can be embedded; copy that must stay exact or editable goes to SVG overlay (switch to Primitive D).

**Primitive D — atmospheric backdrop (no subject)**

> Atmospheric field with no dominant subject — gradients, subtle patterns, or restrained color blocks. A small geometric anchor may sit in a corner or along an edge. Arrange visual activity around the SVG overlay region named by the page plan so that region stays calm enough for its title or text; its position and extent follow the composition rather than a fixed percentage.

**Applies to `page_role: hero_page` only.** The "calm center for SVG overlay" contract defines this primitive. A `local` image uses §3 type templates or §4.1 A/B/E instead; when §VIII / §IX explicitly plans native overlays inside that region, its prompt may reserve only the named focal/quiet area without turning the whole asset into Primitive D.

Use for: cover background, chapter divider background, breathing-page background, any page where the SVG layer carries the words and the image only sets tone.

**Primitive E — custom (escape hatch)**

When none of A/B/C/D describe the page's intended layout (triptych, asymmetric multi-focal, narrative diorama, etc.), write the composition description directly into the prompt's composition sentence — same paragraph slot A/B/C/D occupy, but in your own words. No new field; the freedom is in the prose.

**Default — concise custom composition prose (may override for subject accuracy)**:

| Rule | Value |
|---|---|
| Length | One paragraph, 2-5 sentences, replacing A/B/C/D's opening paragraph |
| Content | State enough subject count and layout structure to make the composition executable; include breathing room or an SVG-overlay region only when the page composition actually needs it |
| Clarity | Describe the actual geometry; a primitive name alone is not a substitute |

Example opening for a triptych hero:

> Triptych — three equal vertical bands of canvas, each holding one symbolic object centered in its band; objects share a low horizon line; bands separated by 2px hairline rules; collectively reads as a single composed page. [...rest of prompt continues with rendering paragraph + color behavior + container note...]

**Fewshot examples per primitive** (one each, deck-context placeholders intact):

> **A — 3d-isometric + deck-color product reveal, text_policy: none, 600×600**
>
> 3D isometric illustration in true 30°/30°/30° projection. One dominant product-form subject — a stylized device or sleek tech object — commands the center of the canvas. The subject is rendered in primary electric blue `#0EA5E9` on its lit faces, with 15% darker tonal shift on shadowed faces. A subtle 8%-opacity outer glow halo surrounds the subject. Small supporting context: three thin connecting lines in accent vivid cyan `#06B6D4` arcing from the subject toward the canvas edges (suggesting connectivity), and a soft 8% drop shadow grounding the subject. Background is deep secondary navy `#0A0E27`, including the shadowed plane. The subject is clearly the singular focal element, with deliberate breathing room around it. Composed as a 600×600 hero block. NO text, letters, numbers, or labels anywhere. Color values are rendering guidance only.

> **B — corporate-photo + deck-color executive headshot, text_policy: none, 600×800**
>
> Editorial corporate portrait photograph of one professional executive. The person is centered slightly left of canvas center, photographed from chest-up at eye level, looking confidently toward the camera with a relaxed natural expression — not posed-stiff, not over-smiling. Professionally attired in a contemporary business setting (a tailored blazer, neutral palette clothing). Soft natural light from the upper left, gentle shadow on the right side of the face. Diverse, professionally attired subject, photorealistically rendered, contemporary styling. Background is a softly out-of-focus office context — secondary light gray `#F8F9FA` wall with a subtle hint of primary deep navy `#1E3A5F` in a blurred architectural element. Color grading is restrained and professional. Shallow depth of field — subject sharp, background gently blurred. Subject's eyes positioned near the upper-third horizontal line, with comfortable headroom. Composed as a 600×800 bio portrait. NO text, name tags, or captions in the image. Color values are rendering guidance only.

> **C — ink-notes + deck-color big-number stat, text_policy: embedded, 800×500**
>
> Professional hand-drawn visual-note style on pure white background. The image's central content is the hand-lettered number "100x" — rendered in bold confident ink strokes as the dominant element, centered with deliberate slight wobble characteristic of hand-lettering. Beneath the number, a thin hand-drawn underline in ink. To the side of the number, one small hand-drawn doodle decoration — a star or upward arrow — adds visual rhythm. Accent coral `#E8655A` (from the deck's accent) appears only as a tiny emphasis dot, totaling under 4% of the canvas. Background is pure white `#FFFFFF`. Composed as an 800×500 typographic hero block with enough breathing room for the letterforms to read clearly. No other text or labels in the image — just the "100x" headline and the small doodle.

> **D — vector-illustration + deck-color cover background, text_policy: none, 1280×720**
>
> Clean flat vector illustration backdrop. Atmospheric composition with no central subject — bold geometric shapes arranged along the canvas edges to leave the planned central title field calm. Primary deep navy `#1E3A5F` forms a confident diagonal block across the lower-left area; secondary light gray `#F8F9FA` provides the breathing field; accent gold `#D4AF37` appears only as one thin geometric line near the lower right corner, under 5% of the canvas. Crisp 2px outlines, no gradients, a single 8% soft drop shadow under the navy block. The intended SVG title region is deliberately calm and unbusy. Composed as a 1280×720 full-bleed PPT background. NO text, letters, numbers, signs, watermarks, or written symbols anywhere in the image. Color values are rendering guidance only — do not display HEX codes or color names as text. Simplified geometric shapes only.

### 4.2 Prompt depth — expand for subject-domain accuracy

**Hard rule**: For images whose deck purpose calls for subject-domain accuracy (scientific figures, academic paper figures, engineering schematics, medical / legal / regulated content), expand the prompt without budget ceiling — 500-1000+ words is normal. The §4 word budget (150-300) is the routine-illustration default, not a cap.

**Forbidden — pre-emptive shortening**: never trim a subject-domain prompt to fit §4's budget. Name the field's visual conventions explicitly in the prompt.

**Detail to name in the prompt** (illustrative, not an enumeration to match):

| Domain | Conventions to spell out |
|---|---|
| chemistry / materials | IUPAC atom colors, bond conventions, lattice type, Å / ps units, subplot labeling (A / B / C circles), view angle |
| biology | cell compartment colors, scale bars, organelle conventions, staining palette |
| physics | axis labels with proper symbols, signature curve shapes, unit annotations, peak labeling format |
| engineering | schematic notation, dimension callouts, section-cut conventions |

**When uncertain about field conventions**: read `sources/` before drafting the prompt.

### 4.3 Illustration sheets — one generation, many composable illustration, illustrated-icon, or lettering elements

An Illustration Sheet generates compatible transparent **illustration**,
**illustrated-icon**, or **decorative lettering** elements with shared rendering,
deck-color treatment, and finish. Subjects, silhouettes, visual weights, and page
jobs may differ; SVG authors the composition after slicing. Lettering remains
stable Layer 1 artwork, not page copy converted to an image.

**Default — batch compatible elements when a shared generation context helps consistency; split when separate generation improves the result**: Plan only useful illustrated-icon cues, normally grouping compatible ones. Group lettering by compatible letterform character and artistic treatment; font name alone does not decide. Split whenever separate generation benefits style, geometry, detail, quality, or semantic precision. A single transparent element may use a keyed `1x1` sheet; full-canvas or nontransparent images use the normal one-row path (§4.1).

**Hard rule**: a sheet is a generation source, not a slide asset. In Default Generate, keep the sheet row out of `spec_lock.md images`; in Quick Generate, retain its generation-only status in active context and the operational manifest. The sheet is never referenced from SVG. Only sliced element rows are placed.

**Sheet prompt convention** — one `page_role: local` manifest item; choose
`image_size` from final placement size. Spot sheets use `text_policy: none`;
lettering sheets use `text_policy: embedded`:

- Derive `aspect_ratio` and `--grid` from the target shape, not a universal `1:1` symmetric grid. State an invisible logical **R×C grid** and the cell shape: compact square object, tall portrait element, wide landscape vignette, or wide lettering mark. Center and isolate each element in its cell with even, clear gutters; never draw cells, panels, dividers, borders, frames, or alternate gutter colors. Do not shrink every subject into a square sticker.
- Use one flat chroma key across the sheet: pure `#00FF00`, `#0000FF`, or `#FF0000`, chosen so its active color does not dominate any element or supporting effect. State the exact HEX; keep it unchanged in all gutters and out of reflections or spill. Grain, halftone, vignette, and other texture stay inside the elements. The key is technical, not part of the deck palette.
- Shared `deck_rendering` + `color_scheme` as always.
- **Illustration / illustrated-icon sheet**: name each element and its page or recurring-reuse job. For an illustrated icon, state the compact semantic cue that must survive at placement size. Apply the §5.3 `none` cue: no text, labels, or numbers.
- **Lettering sheet**: exactly one named stable string per cell as the only text; quote each complete sequence literally. Describe the group's compatible letterform character and artistic treatment, then its communication role, placement/background relationship, relative visual weight, and energy. Follow §5.3's controlled artistic-authorship default. Keep artistry glyph-bound through silhouette, stroke structure, material, texture, depth, and contour-bound light/shadow. Add no topic motifs, scene fragments, icons, detached ribbons, particles, or surrounding illustration unless the approved treatment requests a lettering-plus-illustration lockup. Keep each mark and approved glyph-bound effect inside its cell with key-only padding; no scene, unrelated copy, labels, watermark, or mockup surface.
- **Delivery floor, not an aesthetic ceiling**: enlarge the cell, change the grid, or use a larger/separate sheet when lettering treatment or effects need more footprint. Never weaken an approved treatment to fit a crop; geometry does not raise the §5.3 expression level.

**Cell geometry is designed, not assumed.** `slice_images.py --grid RxC` cuts rows first and columns second. The cell ratio is:

```text
cell_ratio = sheet_ratio * rows / cols
```

Use that deliberately. On a wide sheet (`16:9`, `21:9`, `4:1`, `8:1`), `1xN` makes each cell tall/portrait because the width is divided by `N` while height is kept; `Nx1` makes each cell wide/landscape because height is divided by `N` while width is kept. A designed `MxN` grid is also valid when the resulting cell ratio matches the intended placements.

| Target element shape | Sheet plan | Slice grid |
|---|---|---|
| Compact objects / badges / illustrated icons | `1:1` sheet | `2x2`, `2x3`, or `3x3` |
| Tall side accents / upright objects | wide or square sheet | `1xN`, or any `MxN` whose cells are portrait |
| Wide banners / horizontal vignettes | wide sheet | `Nx1`, or any `MxN` whose cells are landscape |
| Large page anchors / dominant cutouts | dedicated sheet matching the silhouette | `1x1` |
| Decorative words, phrases, or multi-line lettering lockups | wide sheet | `Nx1`, or any `MxN` whose cells fit the planned string shapes |

Within one visual family, use separate sheets for shape families that cannot share a roomy grid. Preserve coherence through `deck_rendering` and `color_scheme`, not one forced square sheet or effect stack.

**Resource contract — sheets and elements are different row kinds.** A slice is placeable only from `spec_lock.md images` in Default Generate or the current agent's prepared-resource decision in Quick Generate. Default keeps both row kinds in §VIII under [`strategist-image.md`](./strategist-image.md); Quick keeps the distinction in active context and its operational manifest, without planning artifacts:

- **Sheet row** — `Acquire Via: ai`, `Type: Illustration Sheet`, named as the slice source with its intent prompt, cell shape, and placement purpose (`Reference: reusable title/corner illustration family`, `illustrated-icon set: cues = ...`, or `decorative lettering set: exact strings = ...`). Step 5 generates it, but it is **never placed** and stays **out of** `spec_lock.md images`. Image_Generator resolves its `aspect_ratio`, grid, and slice command.
- **Element rows** — one per used element, `Acquire Via: slice`, filename matching `--names`, and `Reference` naming the parent sheet plus cell/element. List each in the placeable-resource authority, normally with `crop=no-crop`; tight transparent slices use fit, not cover-crop. `Type: Illustrated icon` marks a compact semantic image asset, never an SVG library entry. A row may serve multiple pages. Fill dimensions after slicing by rerunning `analyze_images.py`. Each row carries an owner-resolved layout recommendation; SVG may use a direct cutout or suitable container while preserving resource identity and crop/content constraints.

For every placeable-element sheet, add `slice_grid` and `slice_names` to its `image_prompts.json` item with the geometry. The comma-separated safe PNG basenames mark the complete required output set. `image_gen.py` validates, preserves, and displays them; slicing remains a separate command.

**Slice** with [`slice_images.py`](../scripts/slice_images.py). It cuts row-major into `images/`; `--alpha` yields transparent cutouts usable directly or in containers. Use `--names` (semantic filenames matching element rows; count **must** equal `rows*cols`), `--trim`, `--alpha`, `--bg` with the prompt's exact key HEX, and `--strict-alpha`, which writes nothing when deterministic checks find an incomplete cut:

```bash
SHEET_KEY_HEX="#00FF00"  # example only; choose a key absent from every element/effect
python3 scripts/slice_images.py <project>/images/illus_sheet.png --grid 2x3 \
    --names team,product,customer,growth,risk,vision --trim --alpha \
    --bg "${SHEET_KEY_HEX}" --strict-alpha
```

**Three quality constraints**:

1. **Strict key recovery.** The pure-key path removes spill while recovering partial alpha for antialiasing, shadow, and glow. For a visually flat field with bounded pixel drift, measure it and raise `--tolerance` only enough to absorb it; `--strict-alpha` must still pass. If an effect reaches an edge, regenerate or enlarge instead of placing a non-strict slice. Use `--inset` only for an isolated outer gutter.
2. **Clean isolated cells.** `--trim` absorbs small placement variance; fused cells, scene backgrounds, or flourishes/effects crossing a cell make the sheet unusable. Do not generate alternatives merely to choose a favorite. Re-roll only after strict keying failure or user/live-preview evidence of an unusable slice, then slice the replacement.
3. **Enough source pixels.** Use the smallest sheet that keeps each cell at least **1.5-2x** intended display size. `1K` usually covers small accents, `2K` medium placements, and `4K` large, cropped, or potentially enlarged elements.

**Placement reference — one family, many page compositions.** A transparent slice may remain unboxed, enter a container, or combine with backgrounds, native shapes, text, photos, other slices, and lettering. Reuse by fit for hierarchy, rhythm, continuity, or character: stable title/corner chrome may repeat exactly; other anchors and accents may vary in scale, position, pairing, and content interaction. Editable copy remains SVG text. Owner-resolved layout text recommends expression; SVG authoring owns geometry and treatment while preserving resource identity and crop/content constraints. A large transparent anchor composed by SVG remains `local` / `slice`; use `hero_page` only when one prepared bitmap owns the page composition. Never apply a quota.

---

### 4.4 Registered reconstruction groups and shared plates

Use this preparation when a person, product, creature, effect, or other scene
element must cross native titles, panels, frames, cards, or shapes while the
original scene remains behind it. A clean base plus one subject/foreground
output is the minimum group; add layers only when overlap or independent
editing requires them:

| Output | Required content |
|---|---|
| Clean base | Full original canvas with every planned removable scene element removed and the hidden background reconstructed |
| Optional midground | Full canvas with only the scene content that must sit between the base and primary subjects |
| Subject / foreground | Full canvas with one subject or one z-order-compatible set visible on RGBA transparency |
| Shared layer plate | Several mutually non-overlapping objects isolated together in one full-canvas or regular-cell output |

**Mandatory — preserve registration**: derive every full-canvas member
independently from the same canonical source. Preserve canvas dimensions,
subject pose, scale, position, lighting, and visible style; do not trim or
independently crop registered final outputs. Record the shared source and group
relationship in the owning §VIII rows or Quick active-context resources.

**Image to PPTX override — Codex required**: when
[`image-to-pptx.md`](../workflows/profiles/image-to-pptx.md) is active, follow
its §3 per-region decision. A complete, separable, final-resolution-sufficient
region may remain source-derived. Otherwise use Codex's native reference-image
capability for required editing or reconstruction. Inspect every prepared
member plus the final recomposition. Do not adapt `image_gen.py`, its manifest,
or provider backends for this profile. Other hosts are unsupported. The
ordinary Path A / Path B procedure below applies outside this profile.

**Preparation procedure**:

1. From the canonical reference, remove every planned separate subject,
   foreground object, source/data graphic, and editable text, then inpaint one
   clean base without redesigning visible background content.
2. From that same reference, prepare the subject/foreground content as an
   exact source-derived layer or a reference reconstruction according to the
   selected profile's source-sufficiency decision. Never derive a layer from
   the generated base or another generated layer.
3. Prefer one shared plate when several objects do not overlap and use the same
   isolation treatment. Their padded bboxes, including visible shadows and
   effects, must be pairwise disjoint. One object does not imply one generation
   call.
4. For a registered plate, retain the original full-canvas positions and use
   one nested-SVG picture crop per recorded bbox under
   [`svg-effects.md`](./svg-effects.md) §6.5. For a rearranged regular-cell
   plate, follow §4.3 and run
   `slice_images.py --grid ... --names ... --trim --alpha`; place each
   resulting asset at its recorded source bbox.
5. Prefer direct RGBA. When transparency is unavailable, use one exact flat
   key color for the whole layer/plate, then run `slice_images.py` once as a
   `1x1` sheet with `--alpha` and without `--trim` so full-canvas coordinates
   remain unchanged. Do not generate one keyed image per object.
6. Save final files under `<project>/images/`. Mark registered full-canvas
   members `no-crop`; ordinary trimmed cell slices retain their own measured
   dimensions.

Objects that overlap one another or require different z-order use separate
plates/layers. A shared output is valid only when every required final object
still becomes an independent SVG/PPT picture object.

**Shared registered-plate prompt core**:

> Using the supplied canonical page as the only visual reference, isolate the
> following foreground objects together on one full-canvas extraction plate:
> {stable object ids/descriptions}. Preserve each object's visible identity,
> silhouette, pose, scale, rotation, lighting, shadow, and exact original canvas
> position. Keep the original aspect ratio and canvas registration. Retain only
> those listed objects; remove the background and every unlisted element. Do not
> rearrange, resize, merge, duplicate, or let the listed objects touch one
> another. Retain an explicitly listed source graphic or wordmark exactly when
> it is one of the requested objects; remove editable slide text and every
> unlisted logo/source graphic. Return RGBA transparency if supported;
> otherwise use one uniform exact {key HEX} matte with no gradient, texture,
> spill, or extra marks.

Outside Image to PPTX, Path A may use the existing single-image edit mode for
each registered derivative; Path B may perform the same edits with the
host-native image tool:

```bash
python3 scripts/image_gen.py "Remove the planned foreground subjects and reconstruct the hidden background; preserve the exact canvas" \
  --reference-image <project>/images/<source>.png -o <project>/images -f <group>_base
python3 scripts/image_gen.py "Isolate the planned non-overlapping foreground objects at their exact original positions on one flat #00FF00 plate" \
  --reference-image <project>/images/<source>.png -o <project>/images -f <group>_plate_key
python3 scripts/slice_images.py <project>/images/<group>_plate_key.png --grid 1x1 \
  --names <group>_plate --alpha --bg "#00FF00"
```

These positional edit commands remain the declared derivation exception for
already-planned group rows. Keep every final member in the ordinary resource
authority and operational sidecar. SVG realization follows
[`image-layout-patterns.md`](./image-layout-patterns.md) `#A2-03`.

---

## 5. Global Hard Rules

These rules apply to **every** prompt regardless of dimension choices. Append them as a closing sentence to every assembled prompt.

### 5.1 HEX is rendering guidance, not text

Image generation models occasionally paint color names and HEX values as **visible labels in the image** (a `#1E3A5F` swatch literally drawn as the string "#1E3A5F"). This destroys the image.

**Append to every prompt**:

> Color values (HEX codes like #1E3A5F) and color names are rendering guidance only — do NOT display HEX codes, color names, or palette labels as visible text anywhere in the image.

### 5.2 Human depiction follows the selected rendering

When the image contains people:

> Match facial detail, anatomy, texture, and realism to the selected rendering and the row's Reference. A silhouette, detailed illustration, painterly figure, editorial photograph, or another treatment is valid when it belongs to that rendering.

**Hard rule — likeness authorization**: Do not request an identifiable real-person or celebrity likeness unless the Reference explicitly names a user-authorized subject/source. Generic or fictional people remain free to follow the selected rendering.

### 5.3 Text policy — two-layer ownership

Every AI-image page carries text in two layers:

| Layer | Owned by | Examples |
|---|---|---|
| Layer 1 (image-owned) | the prompt — baked into the raster | figure-internal annotations (axis labels, A / B / C markers, units, scale bars, panel labels); architecture / schematic module names, node labels, signal-path identifiers; stable artistic lettering that *is* the visual |
| Layer 2 (SVG-owned) | `<text>` overlay — fully editable | authoritative deck/page/chapter titles; navigation, footer, body bullets, conclusion callout; readable copy, captions |

`text_policy` controls only Layer 1. AI judges per image; no global default bias.

**When `embedded` is the right call — positive triggers** (any one match supports `embedded`; the editability rule at the tail of §5.3 still has final say):

| Trigger | Typical Layer 1 text |
|---|---|
| Paper-figure panel comparison (A/B/C, before/after) | Panel labels — `A` / `B` / `C`, or short panel descriptors |
| Textbook math / signal figure | Curve names (`sin` / `cos`), axis labels, unit symbols |
| Architecture / schematic following discipline conventions | Module names (`Self-Attention`, `FFN`, `Add & Norm`), node ids, signal-path tags |
| Data figure with stable axes | Axis labels, units, scale bars |
| Typographic hero (§4.1 Primitive C) | The designed word / number that *is* the image |

Defaulting an entire `ai` resource list to `none` because "SVG can always overlay" is the failure mode this table exists to break. When any row matches a trigger, start at `embedded` and verify the editability filter below still holds.

| `text_policy` | Prompt cue |
|---|---|
| `none` | "NO text of any kind anywhere in the image — no letters, numbers, signs, watermarks, labels, or written symbols." |
| `embedded` | Describe the stable Layer 1 lettering directly inside the visual scene: the exact character(s), how they are rendered, and the artistic treatment. |

**Hard rule — cross-cutting**: Authoritative titles and Layer 2 chrome stay SVG regardless of `text_policy`. Bake title-like wording only when the approved plan explicitly treats those exact characters as stable artistic lettering that is part of the artwork rather than editable deck/page/chapter copy. Navigation, footer, body bullets, captions, and conclusion callouts always stay SVG.

**Forbidden — text that may be reworded**: any word that may later change belongs in Layer 2, not Layer 1. Layer 1 is for stable visual identifiers and designed lettering that is part of the image itself.

**Default — controlled, deck-aligned artistic authorship (may override when the user explicitly requests high expression or confirms a strongly expressive direction)**: For decorative lettering, give the model the exact intended string, communication role, placement/background relationship, deck identity, relative visual weight, and desired energy. The resolved rendering, semantic colors, mood, and page hierarchy define the envelope. Without the stated override, keep expression controlled and glyph-native: carry identity through the glyph silhouette, stroke construction, internal material/texture, contour-bound depth/light, and letterform composition; do not translate the topic into literal illustrations or detached decoration around the word. A lettering-plus-illustration lockup is a separate treatment and requires an explicit user request or confirmed design direction. Within the chosen treatment, let the model decide and combine—or omit—the calligraphic gesture, material, dimensionality, texture, lighting, internal hierarchy, and composition; such terms are possibility space, not an effect recipe. Do not flatten the art merely to simplify extraction: §4.3's key field, clear padding, and cell isolation protect delivery without raising the chosen intensity. When fit is uncertain, use the lower effect density; never infer high expression or external motifs from the topic, place, or wording alone. Keep a multi-line lockup as one element when its hierarchy is part of the art.

**Font choice for in-image text — free description, with the deck typography as one optional reference**

The font for in-image text is a free natural-language description, not an enum. Pick whatever serves the image: blackletter for a heritage cover, hand-brushed for a manifesto poster, retro chrome 3D for Y2K, art-deco display for a luxury hero, ribbon script for a bookstore zine — any artistic treatment the image earns.

The table below is **a reference for the one case where stable in-image lettering should read as the same typographic family as the SVG body** (e.g. an artistic cover wordmark should feel like the body Helvetica, not a surprise blackletter). Use it as a starting point, not a constraint.

| Active typography source contains | Optional descriptor if you want to echo the SVG body |
|---|---|
| `KaiTi` / `FangSong` / `Georgia` / serif families | "elegant serif lettering, refined letterforms" |
| `Microsoft YaHei` / `PingFang SC` / `Arial` / sans-serif families | "clean geometric sans-serif, modern letterforms" |
| `SimHei` / `Impact` / `Arial Black` / display families | "bold display lettering, heavy expressive strokes" |
| `Consolas` / `Courier New` / monospace families | "monospace technical lettering, fixed-width" |
| sketch-notes / ink-notes rendering, or no family specified | "hand-lettered organic strokes, natural variation" |

**When to ignore the table**:

- Decorative / background lettering, posters, large mood words → describe the artistic treatment freely
- Stable artistic cover lettering that wants its own visual identity (blackletter, retro chrome, art-deco display, brushed script) → describe freely
- Sketch-notes / ink-notes / hand-drawn renderings where the lettering is part of the rendering itself → describe freely
- Any case where rendering already implies a font character (e.g. `vintage-poster` implies period display lettering) → trust the rendering, no need to echo SVG body

**When to use the table**: stable artistic lettering on a deck whose visual identity is grounded in the SVG body typography, and where a surprise font choice would feel out of place.

**In-image text vs SVG text — decide by editability, not by model capability**

Layer 1 text is rasterized into the artwork — once generated it cannot be edited, corrected, searched, restyled, or reflowed. That is the durable reason to choose where text lives, independent of any backend's rendering ability or the script / length involved:

| Text | Layer |
|---|---|
| Part of the artwork and stable — decorative lettering, artistic wordmark, hand-lettered word or phrase, figure-internal identifiers (axis labels, panel letters, units) | Layer 1 (image) OK |
| Authoritative titles, page chrome, body copy, captions, data values — anything that must stay exact, searchable, editable, or may be reworded | Layer 2 (SVG) |

Generation is non-deterministic on every backend, but **do not pre-judge by script or length** — never push text to SVG, shorten a headline, or downgrade `embedded` to `none` on the assumption that a particular script or a long string "won't render". Decide where text lives by the editability rule above, not by guessed rendering ability. Name the exact characters to bake literally in the prompt; do not re-read the generated image to verify them.

**Prefer in-image**: text that is genuinely part of the artwork and will not be edited — a designed word or phrase, a stat lettering, a figure-internal label. String length never decides this; a multi-word phrase or two-line lockup qualifies exactly as a single word does.

**Push to SVG overlay instead**: page chrome, captions, data values, or any copy that must stay exact or editable. When the headline must remain editable, switch to **Primitive D (atmospheric backdrop)** and overlay it as SVG text.

### 5.4 No brand names or trademarks in the subject

> The image must not depict identifiable brand logos, trademarks, or product likenesses unless the row's Reference explicitly names a real brand asset the user owns.

---

## 6. Manifest Schema

Write `project/images/image_prompts.json` with this shape:

```json
{
  "project": "{project_name}",
  "generated_at": "{ISO-8601 date}",
  "deck_rendering": "vector-illustration",
  "color_scheme": {
    "background": "#FFFFFF",
    "secondary_bg": "#F8F9FA",
    "primary": "#1E3A5F",
    "accent": "#D4AF37",
    "secondary_accent": "#4A7BB5",
    "body_text": "#1D2430"
  },
  "items": [
    {
      "filename": "cover_bg.png",
      "purpose": "Cover background (Slide 01)",
      "page_role": "hero_page",
      "text_policy": "none",
      "aspect_ratio": "16:9",
      "image_size": "2K",
      "prompt": "{fully assembled paragraph per §4 — use §4.1 Primitive D for atmospheric cover}",
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

### Field reference

| Field | Required | Source | Description |
|---|---|---|---|
| `deck_rendering` | yes | Step 2 active authority | Single rendering name shared by all items in this deck |
| `color_scheme` | yes | Step 2 active authority | Core deck color anchors shared by every item; prompts may add contextual tonal behavior, but no separate image palette |
| `items[].filename` | yes | Active resource authority | Output filename with extension |
| `items[].type` | no | Step 3 per-image | Optional one-of-11 internal-composition type for a local structural infographic when a template genuinely fits. Omit it for custom §4.1 E prose, `hero_page`, an Illustration Sheet, and local single-subject/portrait prose. |
| `items[].page_role` | yes | Step 3 per-image | `local` (default — region block on SVG page) or `hero_page` (image is page's main voice; SVG overlay minimal or empty) |
| `items[].text_policy` | yes | Step 3 per-image | `none` (image carries no text — explicit visual rule) or `embedded` (image contains stable artistic lettering, hand-lettered keywords, or visual identifiers like axis labels / subplot letters / unit symbols). AI judges per image; no global default bias — see §5.3. |
| `items[].aspect_ratio` | yes | Container sizing | Passed to `image_gen.py --aspect_ratio` |
| `items[].prompt` | yes | §4 assembly | The full assembled paragraph |
| `items[].image_size` | no | Container sizing | `512px` / `1K` / `2K` / `4K` |
| `items[].model` | no | Per-item execution override | Backend model for this item; otherwise the CLI/backend default wins |
| `items[].alt_text` | no | Accessibility | Short caption |
| `items[].slice_grid` | required for a placeable-element sheet | §4.3 sheet geometry | Exact `RxC` grid to pass to `slice_images.py --grid`; requires `slice_names` |
| `items[].slice_names` | required for a placeable-element sheet | §4.3 sheet geometry | Comma-separated safe PNG basenames to pass to `slice_images.py --names`; requires exactly `rows*cols` unique outputs |
| `items[].status` | yes | CLI manages | `Pending` initially; CLI updates to `Generated` / `Failed` / `Needs-Manual` |

> **Back-compat for legacy `type` values**: existing manifests using `background` / `hero` / `portrait` / `typography` (the four removed pseudo-types) remain readable. Read them as: `background` → `page_role: hero_page` + no type; `hero` → `page_role: hero_page` + no type (use §4.1 Primitive A in prompt); `portrait` → `page_role: local` + no type (use §4.1 Primitive B); `typography` → `page_role: hero_page` + `text_policy: embedded` + no type (use §4.1 Primitive C). New manifests also omit `type` for custom §4.1 E prose, hero pages, and local single-subject/portrait prose.
>
> **Existing manifest compatibility**:
>
> - **Fixed compatibility defaults**: a missing `page_role` resolves to `local`; a missing `text_policy` resolves to `none`. Emit one aggregate legacy-compatibility warning per manifest.
> - **Declared replay procedure**: an existing manifest may lack `deck_rendering`, or an existing local item may lack `type`, because `items[].prompt` is already assembled. Leave that metadata absent, execute the existing prompt verbatim, and do not reconstruct either value. New manifests follow the field table; custom §4.1 E prose, hero pages, and local single-subject/portrait prose omit `type` intentionally.
> - A legacy non-empty `deck_style_anchor` string or object remains readable for replay and sidecar display but never overrides a current `deck_rendering`.
> - A legacy `deck_palette` field may remain but cannot override `color_scheme`. Read legacy `page_role: full_page` as `hero_page`.

---

## 7. Generation Execution

> Prerequisite: §3 Steps 1-3 complete; `images/image_prompts.json` exists and validates. The manifest is the shared audit/source contract for all modes. It does **not** imply that `image_gen.py --manifest` should run; that command is Path A only.

### Path Selection (Deterministic)

C (AI-generated) supports three implementation modes sharing one `image_prompts.json` source:

| Trigger | Mode | Mechanism |
|---|---|---|
| `api` / `auto` permits Path A and `IMAGE_BACKEND` is configured | **Path A**: `image_gen.py --manifest` | One command runs the whole manifest with concurrency; status writes back per item |
| `host-native` / `auto` permits Path B and the host has a native image tool | **Path B**: Host-native tool | Agent invokes the host's image capability; outputs land at `project/images/<filename>` |
| Default confirmed `manual`, or Quick explicitly selected `manual` | **Offline Manual Mode** | Manifest stays on disk; user generates externally from `items[].prompt` and places files at `project/images/<filename>` |

**Planning boundary**: Strategist and Quick decide AI visual jobs from communication need, not current backend configuration. Do not inspect configuration or probe a provider before planning. Resolve actual Path A/B capability only when this section executes the selected path.

**Quick Generate selection**: an explicit user instruction for `api`, `host-native`, or `manual` retained in active context wins. When the user did not specify a path, select `auto` and try Path A → Path B without asking or creating a planning artifact. If an automated path exhausts, apply the Quick no-AI replan below; Offline Manual is entered only from an explicit `manual` instruction.

**Default Generate selection — declared-procedure fallback when no path is confirmed**: the confirmed user choice wins. When neither channel confirmed a specific path, Generate Step 4 records the effective choice as `auto`; in Default, `auto` authorizes Path A → Path B only and never pre-authorizes Offline Manual. A missing/blank/unknown project value is not an implicit API or manual-generation authorization:

0. **Confirmed override (wins)** — honor `AI Image Acquisition Path` from `design_spec.md §I`. Generate Step 4 already consumed the final confirmation into that durable artifact; do not reopen `result.json` here. If the recorded choice is set and not `auto`, honor it directly, **even when it contradicts `IMAGE_BACKEND`**:
   - `api` → **Path A** (`image_gen.py --manifest`).
   - `host-native` → **Path B** (host's native image tool) — skip A and do **not** run `image_gen.py --manifest`, *even if `IMAGE_BACKEND` is configured*.
   - `manual` → **Offline Manual** (write prompts, render the Markdown sidecar, hand off; do **not** run `image_gen.py --manifest`).
   If an explicitly chosen automated path is unavailable or still fails after its retry, do not switch provider or presume manual fulfillment; enter the Default recovery decision below. Only when the Design Spec records `auto` may both automated paths be attempted. A legacy project missing this Design Spec row returns to Step 4 recovery to consume persisted confirmation once and record it; Image_Generator does not inspect the confirmation channel itself.
1. **Try Path A** — if `IMAGE_BACKEND` is configured (env or `.env`), run `image_gen.py --manifest`. If it fails twice in a row, fall to Path B.
2. **Try Path B** — if `IMAGE_BACKEND` was not configured (A skipped), or A failed, and the host has a native image tool (Codex / Antigravity / Claude Code / similar), the agent invokes the host's image capability directly.
3. **Resolve exhausted automation** — Default enters the recovery decision below; Quick applies the no-AI replan below.

**Hard rule**: normal execution does not reopen path selection. The only Default exception is the one recovery decision after the confirmed automated path or `auto`'s A → B sequence is actually unavailable/exhausted. Quick uses its explicit active-context instruction or automated path, then applies its declared no-AI replan without asking when automation exhausts.

> All three modes share one output contract: file at `project/images/<filename>`. Step 6 SVG references are mode-agnostic.

### Path A — `image_gen.py --manifest` (Default)

```bash
python3 scripts/image_gen.py \
  --manifest project/images/image_prompts.json \
  --output project/images
```

The CLI validates the file behind every `Generated` row before skipping it, iterates retryable rows with bounded adaptive concurrency, and atomically writes each status. A missing/corrupt generated file returns to `Failed`; persistent rate limits finish this run as retryable `Failed` instead of looping forever.

**Parameters**:

| Parameter | Short | Description | Default |
|---|---|---|---|
| `--manifest` | - | Path to `image_prompts.json` | — |
| `--concurrency` | - | Max concurrent requests; halves on rate-limit, min 1 | `IMAGE_CONCURRENCY` env or `3` |
| `--image_size` | - | Default size (`512px`/`1K`/`2K`/`4K`); per-item `image_size` wins | Backend default; see `--list-backends` |
| `--output` | `-o` | Output directory | Manifest's parent dir |
| `--backend` | `-b` | Override `IMAGE_BACKEND` for this run | env |
| `--model` | `-m` | Default model; per-item `model` wins | Backend default |
| `--list-backends` | - | Print support tiers and exit | — |

> The single-image form `image_gen.py "prompt" --filename ...` is preserved for ad-hoc one-offs (re-rolling a single image) but is no longer the primary path.

**Configuration sources**:
- Current process environment variables
- First `.env` found in this order: current working directory, skill directory (e.g. `~/.agents/skills/ppt-master/.env`), clone repo root, `~/.ppt-master/.env`

Precedence:
- Current process environment wins
- `.env` fills missing values only

| Variable | Required | Description |
|----------|----------|-------------|
| `IMAGE_BACKEND` | Required | Backend identifier; run `image_gen.py --list-backends` for the current set |
| `IMAGE_CONCURRENCY` | Optional | Manifest-mode default concurrency (CLI `--concurrency` wins) |
| `{PROVIDER}_API_KEY` | Required | Provider-specific API key, e.g. `GEMINI_API_KEY`, `ZHIPU_API_KEY` |
| `{PROVIDER}_BASE_URL` | Optional | Provider-specific custom endpoint |
| `{PROVIDER}_MODEL` | Optional | Provider-specific model override |
| `OPENAI_SIZE_PRESET` | Optional | OpenAI-compatible size mapping: `auto`, `legacy`, `gpt-image`, `gpt-image-2`, `dall-e-2` |
| `OPENAI_RESPONSE_FORMAT` | Optional | OpenAI-compatible response field: `auto`, `b64_json`, `url`, `omit` |
| `OPENAI_QUALITY` | Optional | OpenAI-compatible quality field: `auto`, `omit`, `low`, `medium`, `high`, `standard`, `hd` |

> Use provider-specific names only (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). See `.env.example` in clone mode or `${SKILL_DIR}/.env.example` in skill-install mode for the full set per backend.

> Note: OpenAI-compatible platforms that reject OpenAI-specific fields stay under `IMAGE_BACKEND=openai`; configure the `OPENAI_*` compatibility knobs instead of adding a provider-specific backend.

> `IMAGE_API_KEY`, `IMAGE_MODEL`, and `IMAGE_BASE_URL` are intentionally unsupported.

> If `.env` or the current environment contains multiple provider configs, `IMAGE_BACKEND` explicitly selects the active one.

**Support tiers (recommended usage)**: Core / Extended / Experimental. Run `image_gen.py --list-backends` for the current assignments.

**Concurrency (manifest mode)**:
- Default 3 concurrent requests, halves on the first rate-limit response, minimum 1 (= serial fallback)
- Rate-limited items requeue automatically; per-item failures are recorded with `last_error` and skipped
- Interrupting mid-run is safe — completed items keep `status: Generated` and are skipped on re-run
- On normal completion the Markdown sidecar is re-rendered automatically; if the run is interrupted, run `--render-md` manually to refresh the sidecar

### Path B — Host-Native Image Tool

Triggered automatically when `IMAGE_BACKEND` is not configured (or Path A fails) **and** the host provides a native image generation tool (Codex, Antigravity, Claude Code's image tool, and similar). No user prompting required — the agent detects the host capability and proceeds. The user may also explicitly name this path ("use Codex's image tool") to force it even when `IMAGE_BACKEND` is configured.

- Agent invokes the host's native image tool directly; prompts come from `items[].prompt`
- Do **not** run `image_gen.py --manifest` in Path B. That command is Path A and may use configured API/proxy backends even when the user confirmed host-native.
- Still run `python3 scripts/image_gen.py --render-md project/images/image_prompts.json` so the human-readable sidecar exists without touching any backend.
- **Batch for speed, mind the rate**: when the host can run independent tool calls in parallel (e.g. Claude Code issues independent calls concurrently), fire several generations together in modest groups — a few rows at a time (~3–4), not the whole manifest at once — so their latency overlaps without flooding the host's image quota. When the host only runs tools serially, generate one row at a time. This mirrors Path A's default concurrency of 3.
- Outputs **must** land at `project/images/<filename-from-resource-list>`. Match the Image Resource List dimensions when the host supports arbitrary sizes. Hosts with **fixed native resolutions** (common — e.g. ~1672x941 landscape / ~1086x1448 portrait) generate at the closest native size and backfill the actual pixels into the resource list `Dimensions` column, as slice rows do after slicing. Do **not** upscale the file to fake the requested size (interpolation adds no detail); minor display-side upscaling (up to ~1.3x in practice) may surface as a non-blocking quality-checker warning and requires no acknowledgement.
- Mark each item's `status` `Generated` in the manifest the moment its file lands — as each completes, not in one pass at the end (so an interrupted batch leaves accurate state)
- Executor downstream is path-agnostic — no spec change required between Path A and Path B

### Offline Manual Mode (C's third implementation mode)

**Trigger**: Default reaches this mode only after the user confirmed `manual` in final Stage 2 or at the exhausted-automation recovery decision. Quick reaches it only through an explicit `manual` instruction.

**Workflow** (manual fulfillment is already authorized; do not ask again inside acquisition):

1. Verify `images/image_prompts.json` was written
2. Set `status: "Needs-Manual"` on every affected item per [`image-base.md`](./image-base.md) §6
3. Apply the mode boundary:
   - Default Generate: continue to Step 6; Executor draws a dashed placeholder, but Step 7 blocks every export command until the supplied file is validated and the placeholder is replaced
   - Quick Generate: retain the prompt and `Needs-Manual` status, and block direct export until every required supplied file is validated and its row is reconciled to `Generated`
4. Print one consolidated handoff to the user:
   - Filenames awaiting manual generation
   - Pointer to `images/image_prompts.md` (paste-ready `### Image N:` block per item) or `image_prompts.json` (`items[].prompt`)
   - Target placement: `project/images/<filename>` matching the resource list exactly
   - Continuation: Default Generate re-runs Step 7; Quick may validate the supplied file, rerun its resource gate and final checker, then use `--quick-generate` only while the original active context remains available — otherwise start a clean Quick run

**User-initiated**: When Strategist Step 4 captured `manual` in Default Generate, or the user explicitly requested `manual` in the Quick Generate active context, Path A is skipped from the start.

#### Default Exhausted-Automation Decision

When required AI rows remain unresolved after Default's confirmed automated path or `auto`'s eligible A → B sequence, keep them `Failed` and pause once with one consolidated list of filenames, prompts, attempted paths, and concrete errors. Ask the user to choose exactly one outcome:

1. **Repair and retry** — wait for the user to repair the named key, balance, endpoint, or host capability, then rerun only the same confirmed path; for `auto`, rerun the repaired eligible path and retain the A → B permission. If it fails again, return to this same decision with the new error.
2. **Generate manually** — update `design_spec.md §I` to `AI Image Acquisition Path: manual` as the newer explicit override, mark the affected rows `Needs-Manual`, render the handoff above, and continue authoring only up to the Step 7 image-readiness gate.
3. **Cancel affected AI images** — return to Generate Step 4 as a post-confirmation override; remove the affected `ai` / dependent `slice` rows and revise their §IX page jobs plus lock rows to native editable text/SVG or already-confirmed non-AI sources. If no AI rows remain, set the path to `not applicable` and remove the AI Image Strategy subsection. Never introduce a new image source or silently drop required communication content.

Do not create `Needs-Manual` state in Default before manual fulfillment is explicitly confirmed.

> Default Generate tolerates `Needs-Manual` rows through authoring and resumes
> at Step 7. An explicitly manual Quick run preserves the same operational
> manifest and handoff but does not run `--quick-generate` while a required row still says
> `Needs-Manual`. If the original active context remains available, validate a
> later supplied file and update it to `Generated`; otherwise start a clean
> Quick run rather than treating the manifest as a resumable design record.

#### Quick Exhausted-Automation No-AI Replan

When an automated AI path or required dependent slicing remains unresolved after its allowed attempts in Quick, do not ask the user and do not enter Offline Manual. Retain the affected filename, attempted path, concrete error, and replacement carrier in active context for the final Quick completion report; remove the affected `ai` row plus dependent `slice` rows from the active resource plan and remove the corresponding manifest item. Re-render `images/image_prompts.md` when other AI items remain; when none remain, remove both `images/image_prompts.json` and `images/image_prompts.md` so no stale failed row survives the replan. Preserve the communication job with native editable text/SVG or already prepared non-AI assets and continue the same run. Do not introduce another image source merely to replace the failed AI job. If the user still wants AI imagery, they must repair the generation capability and start a new Quick run.

#### AI-specific Failure Handling (extends image-base.md §6)

When the path is `auto` and Path A's backend fails twice in a row:

1. Do not halt. Automatically attempt to fall back to **Path B (Host-Native Tool)**.
2. If Path B also fails or is unavailable, Default enters the three-outcome decision above without changing the row to `Needs-Manual`; Quick applies the no-AI replan above.
3. Report the filename, prompt used, and error message through the owning outcome.

When `api` or `host-native` was explicitly confirmed, failure or unavailability does not authorize an automated provider switch. Retry the confirmed path once; if it still fails, Default enters the decision above, while Quick applies the no-AI replan above.

> If the alternate platform watermarks outputs (e.g. Gemini web), the repository includes `scripts/gemini_watermark_remover.py`.

#### Guardrails (All Modes)

**Hard rule**:

- Do not claim an image is generated without an actual file at the expected path
- `Needs-Manual` is set only when manual fulfillment was confirmed in Default or explicitly selected in Quick — not as a way to skip work that automation could have done
- Status transitions are evidence-driven: a file at the expected path permits `Generated`; exhausted Default automation remains `Failed` until a retry succeeds or the user chooses manual or cancellation; exhausted Quick AI rows are removed only through the declared no-AI replan

---

## 8. Common Issues & Variant Workflow

### Reference field is omitted or blank — declared-inference fallback for existing AI rows

When an existing AI Resource List row omits `Reference` or contains a blank `Reference`, infer a reasonable image from its non-empty `Purpose`. If `Purpose` is also omitted or blank, stop and repair the row. Examples (not prescriptions):

| Purpose | A reasonable starting point |
|---------|-----------------------------|
| Cover | `page_role: hero_page` + §4.1 Primitive A (single-subject) or D (atmospheric); choose `text_policy` by what the cover should communicate |
| Chapter divider | `page_role: hero_page` + Primitive D (atmospheric) or A (single-subject); keep the authoritative chapter title in SVG, with `embedded` reserved for separate stable artistic lettering |
| Methodology / framework illustration | `type: framework`, `page_role: local` |
| Process / workflow illustration | `type: flowchart`, `page_role: local` |
| Before/After or two-option page | `type: comparison`, `page_role: local` |
| Team / lifestyle photo (group) | `type: scene`, `page_role: local`; rendering = `corporate-photo` or `warm-scene` |
| Single-person headshot / bio | `page_role: local` + §4.1 Primitive B (portrait); rendering = `corporate-photo` for photo realism |
| Big-number / hero quote block | `page_role: hero_page` + §4.1 Primitive C (typographic); `text_policy: embedded` |
| Mood transition / atmosphere | `page_role: hero_page` + Primitive D (atmospheric), or `type: scene` if narrative |

### When Images Are Unsatisfactory

Diagnose the failure category, adjust the **one specific dimension** responsible, do not rewrite the whole prompt.

| Symptom | Most likely cause | Adjustment |
|---|---|---|
| Image looks generic, model-average | Tag-soup prompt | Rewrite as one coherent paragraph per §4 |
| Wrong style family (looks photorealistic when flat was intended) | Rendering mismatch or rendering paragraph diluted | Reaffirm chosen rendering's style paragraph at the top of the prompt |
| Colors don't match deck | Core role anchors or their semantic/proportion instructions were diluted | Restate which deck roles own the field, main forms, and sparse accents; remove unrelated hues while preserving context-justified tonal transitions |
| Lettering feels unrelated, overdecorated, or too dominant for its role | Expression exceeded the deck identity or planned visual weight | Retain the exact string and visual family; lower effect density, ornament, contrast, or lighting energy for the affected item/family instead of shrinking it into submission |
| Lettering carries mountains, buildings, animals, icons, ribbons, or other topic decoration around the glyph | The model turned subject context into an unrequested illustration lockup | Remove every external motif and rerun the affected item/family; express the identity through glyph structure, material, texture, depth, and contour-bound light instead |
| Hex code or color name visible as text in image | Missing §5.1 closing sentence | Append the §5.1 hard rule verbatim |
| Garbled letters in supposedly text-free image | `text_policy: none` rule too weak | Strengthen with explicit list: "no letters, no numbers, no words, no signs, no labels, no captions, no watermarks" |
| SVG text overlay clashes with busy image area | Page design needs negative space the prompt didn't request | Add a composition cue like "leave the {center / left third / lower band} relatively calm for text overlay" — only when the page actually overlays text on top of the image |
| Subject vague | Reference field too abstract | Rewrite reference with concrete nouns (verbs + objects) |
| Human depiction conflicts with the selected style or intent | §5.2 rendering/Reference cues were diluted | Restate the selected rendering's facial detail, anatomy, texture, and realism cues without changing the locked rendering |

**Variant workflow**:

1. Set the unsatisfactory item's `status` back to `Pending` and update its `prompt` in place
2. Re-run the same resolved path used for the original item: Path A may re-run `image_gen.py --manifest` (only that item is re-processed); Path B uses the host-native tool again for that item; Offline Manual re-renders the sidecar and hands off
3. To try multiple stylistic approaches, append additional items with distinct filenames (e.g. `cover_bg_v2.png`) rather than overwriting

---

## 9. Forbidden

- Generating prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description (degrades output)
- Mixing renderings or introducing an unrelated image-only palette across images in the same deck
- Tag-soup prompts (keyword lists separated by commas without a coherent visual scene)
- Globbing `image-renderings/*.md` or any subdirectory — read only the chosen preset or exact custom-reference files
- Placing an image without updating its `image_prompts.json` `status` and the active resource authority's status
- Switching rendering or core deck-color semantics for a single image—`hero_page` is not an exception to deck-wide coherence
- Embedding body copy, data points, bullet lists, or long quotes inside an image — those route to SVG
