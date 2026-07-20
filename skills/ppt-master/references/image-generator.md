> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: convert each `Acquire Via: ai` row into an optimized prompt, generate the image, and save it to `project/images/`; also defines the `slice` derivation path for AI-generated illustration sheets.

**Trigger**: resource list rows with `Acquire Via: ai` or `slice`. The role is loaded only when at least one such row exists.

---

## 1. Core Principle — Maximize AI Image Capability in Service of the Deck

AI images exist to serve the deck's communication goal. Pick whatever combination of `page_role` and `text_policy` makes the page work best.

**Two page roles** (orthogonal to type):

| `page_role` | Use |
|---|---|
| `local` | Image occupies a region of an SVG page (left half, right column, hero band, accent corner). Composition is the AI's call — fill the region as the page design wants |
| `hero_page` | Image is the page's main voice — cover, chapter divider, mood transition, single-number hero, closing quote. SVG above may be minimal or empty |

**Two text policies** (orthogonal to page_role):

| `text_policy` | Use |
|---|---|
| `none` | No text inside the image |
| `embedded` | Image contains text as part of the artwork — decorative lettering, designed title, hand-lettered keywords, infographic labels, anything the page needs |

**Hard rule — only what's actually hard**:

- Same `deck_rendering` + same core deck color anchors/semantic behavior for every image in the deck
- HEX codes and color names are rendering guidance — never visible text in the image
- Long body copy / data points / bulleted lists / long quotes stay in SVG (improving them later means regenerating the image, which is expensive)
- **In-image text is only for words that will not need editing later** — visual keywords, decorative lettering, mood words. Editable text (titles that may be reworded, subtitles, dates, authors, captions, body) belongs in SVG. Changing one in-image word costs an image regeneration; one SVG word costs a keystroke.
- Prompts are one coherent prose paragraph, not tag soup (a model-output reality, not an aesthetic choice)

Everything else is the AI's judgment per page. No mandated padding, no type-locked text_policy, no scenario whitelists for hero_page.

---

## 2. Style and Composition Inputs

Every AI image uses one deck-wide rendering, the deck's stable color anchors/semantic behavior, and a per-image type / composition. Only rendering is a separate image-direction decision.

| Dimension | Decides | When fixed |
|---|---|---|
| **Rendering** | Visual style family (vector / sketch-notes / 3d-isometric / corporate-photo / …) | Once per deck — every AI image in the deck shares one rendering |
| **Deck colors** | Core background / primary / accent / secondary-accent / text anchors from `spec_lock.md colors`, interpreted with the Design Spec and per-image context; these are not reconfirmed | Anchored after Stage 2 |
| **Type** | What the image's internal composition skeleton looks like — geometric layout of a local infographic block (infographic / flowchart / framework / matrix / cycle / funnel / pyramid / comparison / timeline / map / scene). Only applies to `page_role: local`; for `page_role: hero_page`, describe composition with §4.1 primitives instead of picking a type. | Per image |

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

Read the two index files that own user-visible image direction and per-image composition.

```
read_file references/image-renderings/_index.md
read_file references/image-type-templates/_index.md
```

### Step 2 — Resolve deck-wide rendering + deck colors

**Primary path — Strategist already recorded rendering and core deck color anchors in `spec_lock.md colors`**:

```
image_rendering: vector-illustration
background: #F8F9FA
primary: #1E3A5F
accent: #D4AF37
```

Use them as identity anchors. Do not create another user-facing image-color choice. The rendering and image subject may derive coherent tonal transitions, material colors, lighting, and atmospheric hues when the context requires them, while the core roles keep their established meaning.

**Hard rule — `custom` catalog basis**: when `image_rendering` is `custom`, first inspect the optional `image_rendering_references` row. If present, read every exact `image-renderings/<id>.md` it lists and synthesize their line, texture, depth, material, and mood guidance under `image_rendering_behavior` before assembling prompts. If absent, the custom is genuinely novel: read no preset file and use `image_rendering_behavior` directly. Never infer or add adjacent references during execution. The deck color-role rows remain authoritative.

**Declared-inference fallback — when an existing `spec_lock.md` omits the `image_rendering` key** (see [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2):

This fallback covers a missing key only. An empty or invalid value stops for lock repair. If `spec_lock.md` itself is absent, stop at [`generate-pptx.md`](../workflows/generate-pptx.md) Step 5 before prompt assembly or image generation; do not use `design_spec.md` as a substitute.

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

For each `Acquire Via: ai` row in `design_spec.md §VIII`:

1. **Determine `page_role`** — Strategist's explicit value wins; a blank or omitted value resolves to `local`. `hero_page` must be explicit.
2. **Determine `text_policy`** — Strategist's value wins when set. **Declared-inference fallback for a blank or omitted value**: pick `none` or `embedded` from the row's `Purpose`, `Reference`, and page intent based on whether in-image text serves the page. Long body / data / lists stay in SVG.
3. **Determine type** — only when the resolved `page_role` is `local` (the image sits as a region block on an SVG page). Match the row's `Purpose` against the `_index.md` auto-selection table (methodology visualization → `framework`; process steps → `flowchart`; SWOT/Eisenhower → `matrix`; PDCA / flywheel → `cycle`; etc.). `Purpose` is authoritative for picking among the 11 internal-composition types. **When the resolved `page_role` is `hero_page`, skip type selection** and describe composition directly using §4.1 primitives (single-subject / portrait / typographic / atmospheric).
4. `read_file references/image-type-templates/<type>.md` (only if not already read — types are commonly reused across images in one deck)
5. **Assemble the prompt** by combining:
   - The rendering's style paragraph (from Step 2)
   - Color-role instructions anchored by the deck HEX values and refined for the image context (from Step 2)
   - The type's structural layout (from Step 3)
   - The image's specific `Reference` intent (from `design_spec.md §VIII`)
   - The container sizing guidance from the type file (so the model knows it's painting a local block, not a full canvas)
   - The hard rules from §5 below (HEX-not-as-text, simplified figures, text policy)

The assembled prompt is **one cohesive paragraph**, not a bulleted list of tags. See §4 for the assembly template.

### Step 4 — Write the manifest and execute the confirmed path

Write `project/images/image_prompts.json` per §6. Then follow §7 Path Selection. `image_gen.py --manifest` is Path A only; confirmed `host-native` runs the host image tool directly, and confirmed `manual` renders the Markdown sidecar and hands off without API generation.

---

## 4. Prompt Assembly Template

Every assembled prompt follows this paragraph structure. **Write prose, not tag soup**.

```
[Rendering style paragraph — 80-120 words from the chosen rendering file].
[Deck color behavior — state the core anchors and any context-justified tonal treatment, e.g. "secondary background #F8F9FA provides the breathing field, primary #1E3A5F carries main forms, accent #D4AF37 marks one emphasis; subtle lighter/darker material transitions remain in the same visual family"].
[Type-specific composition — from the chosen type file, e.g. "central hub node with four radiating satellite nodes connected by clean lines"].
[Image-specific subject — translated from the row's Reference intent into concrete visual nouns].
[Container note — "composed as a {W}x{H}px image for {page_role} use"; add composition cues only when the page actually needs them. SVG-overlay-reservation cues ("leave the lower band calm — SVG title overlays it", "keep the right third calmer for SVG text") are valid **only** when `page_role: hero_page` (SVG sits on top of the image). For `page_role: local`, the image sits inside a region block and the SVG layer never overlays its interior — never reserve overlay space in a local prompt].
[Hard rules — see §5].
```

**Word budget**: 150-300 words. Embedded-text prompts skew longer; pure background prompts can be shorter.

**Forbidden — tag-soup prompts**:

```
❌ "modern, flat design, gradient, vibrant, professional, clean, 4K, high quality"
```

This produces generic, model-average output. The model is not weighting your tags — write **one coherent visual scene** instead.

### 4.1 Hero-page composition primitives

When `page_role: hero_page` (the image is the page's main voice — cover, chapter divider, mood transition, signature stat, closing quote), the image's internal composition does not need its own structural `type` (matrix / cycle / framework etc. are for *local* infographic blocks). Instead, describe the composition directly in the prompt using one of the four primitives below.

**Primitive A — single dominant subject (product / object / concept hero)**

> One dominant subject occupying 60-70% of the canvas, positioned with intent (centered, rule-of-thirds offset, or slight left/right). Supporting context <30% of canvas weight. Generous negative space — at least 15% padding on the subject's "open" side. No second-place subject competing.

Use for: product reveal, concept introduction, chapter title visual, brand statement.

**Primitive B — single human subject (portrait)**

> One person, frontal or three-quarter turn, head + upper body. Subject occupies 50-65% of canvas height, centered or rule-of-thirds offset. Eyes at the upper-third horizontal line. Background neutral, minimal, or softly blurred. No competing foreground objects. At least 15% padding above the crown.

Use for: founder profile, speaker bio, testimonial page, executive intro. Pair with `rendering: corporate-photo` for photographic realism; otherwise the §5.2 simplified-figures rule applies.

**Primitive C — typographic hero (the text *is* the image)**

> The image's central content is one large text element — a short headline, big number, or single word — rendered as art, occupying 40-60% of canvas height. Minimal supporting visual (small icon, geometric anchor, accent line) at <25% weight. At least 20% padding around the text.

Use with `text_policy: embedded`. Must obey the §5.3 rule — text that is part of the artwork and stable can be embedded; copy that must stay exact or editable goes to SVG overlay (switch to Primitive D).

**Primitive D — atmospheric backdrop (no subject)**

> Atmospheric field with no dominant subject — gradients, subtle patterns, or restrained color blocks. Small geometric anchor optional, placed in a corner or along an edge, never centered. The center 60-70% of the canvas must stay calm to receive SVG title/text overlay.

**Applies to `page_role: hero_page` only.** The "calm center for SVG overlay" contract is the defining feature of this primitive — and it only holds when SVG actually sits on top of the image. `page_role: local` images live inside a region block; the SVG layer never overlays their interior, so Primitive D is not a valid choice for local. Local schematic / scene / chart images use the §3 type templates instead.

Use for: cover background, chapter divider background, breathing-page background, any page where the SVG layer carries the words and the image only sets tone.

**Primitive E — custom (escape hatch)**

When none of A/B/C/D describe the page's intended layout (triptych, asymmetric multi-focal, narrative diorama, etc.), write the composition description directly into the prompt's composition sentence — same paragraph slot A/B/C/D occupy, but in your own words. No new field; the freedom is in the prose.

**Hard rule — custom composition prose**:

| Rule | Value |
|---|---|
| Length | One paragraph, 2-5 sentences, replacing A/B/C/D's opening paragraph |
| Required content | subject count, layout structure, where breathing room sits, where SVG overlay can claim canvas |
| Forbidden | Naming a competing primitive ("like A but two subjects") |

Example opening for a triptych hero:

> Triptych — three equal vertical bands of canvas, each holding one symbolic object centered in its band; objects share a low horizon line; bands separated by 2px hairline rules; collectively reads as a single composed page. [...rest of prompt continues with rendering paragraph + color behavior + container note...]

**Fewshot examples per primitive** (one each, deck-context placeholders intact):

> **A — 3d-isometric + tech-neon product reveal, text_policy: none, 600×600**
>
> 3D isometric illustration in true 30°/30°/30° projection. One dominant product-form subject — a stylized device or sleek tech object — occupies the center of the canvas at roughly 65% of the area. The subject is rendered in primary electric blue `#0EA5E9` on its lit faces, with 15% darker tonal shift on shadowed faces. A subtle 8%-opacity outer glow halo surrounds the subject. Small supporting context: three thin connecting lines in accent vivid cyan `#06B6D4` arcing from the subject toward the canvas edges (suggesting connectivity), and a soft 8% drop shadow grounding the subject. Background is deep secondary navy `#0A0E27` (about 30% of canvas, including shadowed plane). The subject is clearly the singular focal element. Composed as a 600×600 hero block with 15% padding around the subject. NO text, letters, numbers, or labels anywhere. Color values are rendering guidance only.

> **B — corporate-photo + cool-corporate executive headshot, text_policy: none, 600×800**
>
> Editorial corporate portrait photograph of one professional executive. The person is centered slightly left of canvas center, photographed from chest-up at eye level, looking confidently toward the camera with a relaxed natural expression — not posed-stiff, not over-smiling. Professionally attired in a contemporary business setting (a tailored blazer, neutral palette clothing). Soft natural light from the upper left, gentle shadow on the right side of the face. Diverse, professionally attired subject, photorealistically rendered, contemporary styling. Background is a softly out-of-focus office context — secondary light gray `#F8F9FA` wall with a subtle hint of primary deep navy `#1E3A5F` in a blurred architectural element. Color grading is cool-corporate — restrained, professional. Shallow depth of field — subject sharp, background gently blurred. Subject's eyes positioned at the upper-third horizontal line. Composed as a 600×800 bio portrait with 10% padding. NO text, name tags, or captions in the image. Color values are rendering guidance only.

> **C — ink-notes + mono-ink big-number stat, text_policy: embedded, 800×500**
>
> Professional hand-drawn visual-note style on pure white background. The image's central content is the hand-lettered number "100x" — rendered in bold confident ink strokes occupying about 50% of the canvas height, centered with deliberate slight wobble characteristic of hand-lettering. Text is in English/Latin characters only. Beneath the number, a thin hand-drawn underline in ink. To the side of the number, one small hand-drawn doodle decoration — a star or upward arrow — adds visual rhythm. Accent coral `#E8655A` (from the deck's accent) appears only as a tiny emphasis dot, totaling under 4% of canvas. Background is pure white `#FFFFFF`. Composed as an 800×500 typographic hero block with 20% padding around the number. No other text or labels in the image — just the "100x" headline and the small doodle.

> **D — vector-illustration + cool-corporate cover background, text_policy: none, 1280×720**
>
> Clean flat vector illustration backdrop. Atmospheric composition with no central subject — bold geometric shapes arranged along the canvas edges to leave the center calm. Primary deep navy `#1E3A5F` forms a confident diagonal block across the lower-left third; secondary light gray `#F8F9FA` occupies the upper two-thirds as breathing space; accent gold `#D4AF37` appears only as one thin geometric line near the lower right corner (under 5% of canvas). Crisp 2px outlines, no gradients, single 8% soft drop shadow under the navy block. The central 60% of the canvas is deliberately calm and unbusy — designed to receive a slide title overlaid in SVG. Composed as a 1280×720 full-bleed PPT background. NO text, letters, numbers, signs, watermarks, or written symbols anywhere in the image. Color values are rendering guidance only — do not display HEX codes or color names as text. Simplified geometric shapes only.

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

### 4.3 Illustration sheets — one generation, many spot elements

When a deck wants several small **spot illustrations** scattered as decorative accessories across pages, do **not** generate them one image per slot. Generate one sheet and slice it. One call buys identical rendering, deck-color treatment, and line quality—the same consistency protected by `deck_rendering` + `color_scheme`.

**When to use**: the §VIII image resource plan needs ≥3 small spot illustrations from the same family across the deck. For a single hero/local image, stay with the normal one-row-per-image flow (§4.1). Use sheets only where decorative illustration genuinely lifts the page; an unused element costs nothing, but a deck papered in decoration reads cheap.

**Hard rule**: a spot sheet is a generation source, not a slide asset. The sheet row is never listed in `spec_lock.md images` and never referenced from SVG. Only the sliced element rows are placed.

**Sheet prompt convention** (one manifest item, `page_role: local`, `text_policy: none`, `image_size` chosen from final placement size):

- Choose the sheet `aspect_ratio` and `--grid` from the target element shape. Do not default every sheet to `1:1` + a symmetric grid.
- Lay the elements out in an explicit **R×C grid, evenly spaced with clear gutters**, each element **centered in its own cell** and isolated (no element bleeds into a neighbor).
- State the intended cell shape in the prompt: compact square object, tall portrait element, or wide landscape vignette. Do not let the model shrink every subject into a centered square sticker.
- One **flat single-color background** across the whole sheet, set to the deck's background/secondary HEX — this is what lets the slicer key it out cleanly and lets the cut element sit on the slide without a visible box.
- Shared `deck_rendering` + `color_scheme` as always. NO text, labels, or numbers anywhere (§5.1, §5.3).

**Cell geometry is designed, not assumed.** `slice_images.py --grid RxC` cuts rows first and columns second. The cell ratio is:

```text
cell_ratio = sheet_ratio * rows / cols
```

Use that deliberately. On a wide sheet (`16:9`, `21:9`, `4:1`, `8:1`), `1xN` makes each cell tall/portrait because the width is divided by `N` while height is kept; `Nx1` makes each cell wide/landscape because height is divided by `N` while width is kept. A designed `MxN` grid is also valid when the resulting cell ratio matches the intended placements.

| Target spot shape | Sheet plan | Slice grid |
|---|---|---|
| Compact objects / badges | `1:1` sheet | `2x2`, `2x3`, or `3x3` |
| Tall side accents / upright objects | wide or square sheet | `1xN`, or any `MxN` whose cells are portrait |
| Wide banners / horizontal vignettes | wide sheet | `Nx1`, or any `MxN` whose cells are landscape |

If one deck needs mixed shapes, create separate sheets per shape family unless one carefully designed grid gives every element enough room. Keep the visual family consistent through the same `deck_rendering` and `color_scheme`, not by forcing all cells into one square sheet.

**Resource contract — the sheet and its elements are different row kinds.** A sliced element can only be placed if it exists as a resource the Executor is allowed to reference (`spec_lock.md images`). So §VIII carries two row kinds (planning authority: [`strategist-image.md`](./strategist-image.md)):

- **Sheet row** — `Acquire Via: ai`, `Type: Illustration Sheet`, the intent prompt, named as the slice source with its intended cell shape and placement purpose (`Reference: landscape footer-vignette spot set`). It is generated in Step 5 but **never placed on a slide** — keep it **out of** `spec_lock.md images`. Image_Generator resolves the exact `aspect_ratio`, grid, and slice command from this intent.
- **Element rows** — one per used element, `Acquire Via: slice`, filename matching a `--names` output, `Reference` naming the parent sheet + cell/element. These **are** placed — list every one in `spec_lock.md images`, usually with ` | no-crop` (a tight-trimmed transparent spot should be fit, not cover-cropped). Their dimensions are filled in after slicing (Step 5 re-runs `analyze_images.py`). **Set each element row's Layout pattern from the decorative-cutout family, never a boxed container** — see Placement below.

For traceability, add optional `slice_grid` and `slice_names` fields to the sheet item in `image_prompts.json` after choosing the geometry. `image_gen.py` ignores unknown item fields but preserves them in the manifest, so these fields document the exact command that must be used for slicing.

**Slice** with [`slice_images.py`](../scripts/slice_images.py) — cells are cut row-major into individual files in `images/`. With `--alpha` they are **transparent cutout stickers** (image-layout-patterns `#63`), not rectangular content images. Recommended flags: `--names` (semantic per-cell filenames matching the element rows; the count **must** equal `rows*cols`), `--trim` (tight-crop each cell so imprecise placement inside a cell doesn't leave lopsided margins), `--alpha` (knock the flat background out to transparency so an element drops onto any slide color):

```bash
python3 scripts/slice_images.py <project>/images/illus_sheet.png --grid 2x3 \
    --names team,product,customer,growth,risk,vision --trim --alpha
```

**Three constraints that decide whether it looks good**:

1. **Flat background, matched to the slide.** `image_gen.py` has no transparent-background mode, so the cut element carries whatever was behind it. A flat sheet background (= deck background HEX) is what `--alpha` keys out and what makes non-keyed pieces blend.
2. **Clean grid, or it cuts ugly.** The model will not place every element perfectly; force a clear grid with gutters, and generate **a few sheets** (re-roll the same prompt) to pick the cleanest-laid-out one before slicing. State the exact row/column structure and cell shape so the model does not invent a square matrix. `--trim` absorbs the rest.
3. **Generate only as large as needed.** Each cell is a fraction of the sheet. Pick the smallest sheet size that keeps each sliced cell at least **1.5-2x** the intended display size. `1K` is usually enough for small 80-160px decorative spots; use `2K` for medium 180-320px placements; reserve `4K` for large, cropped, or potentially enlarged elements.

**Placement — these are decorative accessories, not boxed pictures.** A transparent spot wasted in a centered rectangle looks cheaper than no spot at all. Each element row's Layout pattern comes from the decorative-cutout family in [`image-layout-patterns.md`](./image-layout-patterns.md): `#63` sticker/cutout, `#4` bleed off the canvas edge, `#58` corner fragment, `#66` fade into the background, `#69` slight editorial rotation, `#49` asymmetric cluster. Push spots to the margins, let them run off-edge or sit behind/beside text, vary size and angle across pages, and overlap the content rather than reserving a tidy tile for them. Anchor most pages on one primary element and let the rest stay small ([primary-per-page](./strategist-image.md)) — scattered same-weight tiles are exactly the generic look to avoid.

**Through-line — one family, many roles.** A spot sheet pays off more when the same motif family also drives the cover and section dividers. A large cover / divider anchor is not a giant sheet cell—generate it as its own `hero_page` image sharing the sheet's `deck_rendering`, `color_scheme`, and subject world. Plan this only when the deck leans into illustration, never as a quota.

---

## 5. Global Hard Rules

These rules apply to **every** prompt regardless of dimension choices. Append them as a closing sentence to every assembled prompt.

### 5.1 HEX is rendering guidance, not text

Image generation models occasionally paint color names and HEX values as **visible labels in the image** (a `#1E3A5F` swatch literally drawn as the string "#1E3A5F"). This destroys the image.

**Append to every prompt**:

> Color values (HEX codes like #1E3A5F) and color names are rendering guidance only — do NOT display HEX codes, color names, or palette labels as visible text anywhere in the image.

### 5.2 Simplified human figures, no realistic faces

When the image contains people:

> Human figures appear as simplified stylized silhouettes or symbolic representations — no photorealistic faces, no detailed anatomy, no celebrity likeness. Express role/emotion through posture, attire, and simple gestures.

Exception: when the chosen rendering is `corporate-photo`, photorealism is intentional — replace the above with: `Diverse, professionally attired subjects. Editorial photography style, natural composition`.

### 5.3 Text policy — two-layer ownership

Every AI-image page carries text in two layers:

| Layer | Owned by | Examples |
|---|---|---|
| Layer 1 (image-owned) | the prompt — baked into the raster | figure-internal annotations (axis labels, A / B / C markers, units, scale bars, panel labels); architecture / schematic module names, node labels, signal-path identifiers; hero typographic or decorative lettering that *is* the visual |
| Layer 2 (SVG-owned) | `<text>` overlay — fully editable | page-level chrome (title, navigation, footer, body bullets, conclusion callout); readable copy, captions |

`text_policy` controls only Layer 1. AI judges per image; no global default bias.

**When `embedded` is the right call — positive triggers** (any one match flips the row from a `none` starting point to `embedded`; the editability rule at the tail of §5.3 still has final say):

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
| `embedded` | Describe the Layer 1 text directly inside the visual scene: the word(s), how they're rendered, and the artistic treatment. |

**Hard rule — cross-cutting**: Layer 2 chrome stays SVG regardless of `text_policy`. Never bake the deck title, navigation, footer, body bullets, or conclusion callout into the image, even when `embedded`.

**Forbidden — text that may be reworded**: any word that may later change belongs in Layer 2, not Layer 1. Layer 1 is for stable visual identifiers and designed lettering that is part of the image itself.

**Font choice for in-image text — free description, with the deck typography as one optional reference**

The font for in-image text is a free natural-language description, not an enum. Pick whatever serves the image: blackletter for a heritage cover, hand-brushed for a manifesto poster, retro chrome 3D for Y2K, art-deco display for a luxury hero, ribbon script for a bookstore zine — any artistic treatment the image earns.

The table below is **a reference for the one case where you want the in-image lettering to read as the same typographic family as the SVG body** (e.g. a clean editorial deck where the cover title in the image should feel like the body Helvetica, not a surprise blackletter). Use it as a starting point, not a constraint.

| `spec_lock typography.font_family` contains | Optional descriptor if you want to echo the SVG body |
|---|---|
| `KaiTi` / `FangSong` / `Georgia` / serif families | "elegant serif lettering, refined letterforms" |
| `Microsoft YaHei` / `PingFang SC` / `Arial` / sans-serif families | "clean geometric sans-serif, modern letterforms" |
| `SimHei` / `Impact` / `Arial Black` / display families | "bold display lettering, heavy expressive strokes" |
| `Consolas` / `Courier New` / monospace families | "monospace technical lettering, fixed-width" |
| sketch-notes / ink-notes rendering, or no family specified | "hand-lettered organic strokes, natural variation" |

**When to ignore the table**:

- Decorative / background lettering, posters, large mood words → describe the artistic treatment freely
- Cover hero title that wants its own visual identity (blackletter, retro chrome, art-deco display, brushed script) → describe freely
- Sketch-notes / ink-notes / hand-drawn renderings where the lettering is part of the rendering itself → describe freely
- Any case where rendering already implies a font character (e.g. `vintage-poster` implies period display lettering) → trust the rendering, no need to echo SVG body

**When to use the table**: a designed title (cover main title, chapter heading) on a deck whose visual identity is grounded in the SVG body typography, and where a surprise font choice would feel out of place.

**In-image text vs SVG text — decide by editability, not by model capability**

Layer 1 text is rasterized into the artwork — once generated it cannot be edited, corrected, searched, restyled, or reflowed. That is the durable reason to choose where text lives, independent of any backend's rendering ability or the script / length involved:

| Text | Layer |
|---|---|
| Part of the artwork and stable — decorative lettering, designed title, hand-lettered keyword, figure-internal identifiers (axis labels, panel letters, units) | Layer 1 (image) OK |
| Page chrome, body copy, captions, data values — anything that must stay exact, searchable, or may be reworded | Layer 2 (SVG) |

Generation is non-deterministic on every backend, but **do not pre-judge by script or length** — never push text to SVG, shorten a headline, or downgrade `embedded` to `none` on the assumption that a particular script or a long string "won't render". Decide where text lives by the editability rule above, not by guessed rendering ability. Name the exact characters to bake literally in the prompt; do not re-read the generated image to verify them.

**Prefer in-image**: text that is genuinely part of the artwork and will not be edited — a designed word, a stat lettering, a figure-internal label.

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
| `deck_rendering` | yes | Step 2 lock | Single rendering name shared by all items in this deck |
| `color_scheme` | yes | `spec_lock.md colors` | Core deck color anchors shared by every item; prompts may add contextual tonal behavior, but no separate image palette |
| `items[].filename` | yes | `§VIII` resource list | Output filename with extension |
| `items[].type` | conditional | Step 3 per-image (only when `page_role: local`) | One of 11 internal-composition types: `infographic`, `flowchart`, `framework`, `matrix`, `cycle`, `funnel`, `pyramid`, `comparison`, `timeline`, `map`, `scene`. **Omit `type` entirely when `page_role: hero_page`** — the composition comes from §4.1 primitives written directly into the prompt, not from a type file. |
| `items[].page_role` | yes | Step 3 per-image | `local` (default — region block on SVG page) or `hero_page` (image is page's main voice; SVG overlay minimal or empty) |
| `items[].text_policy` | yes | Step 3 per-image | `none` (image carries no text — explicit visual rule) or `embedded` (image contains decorative lettering, designed title, hand-lettered keywords, or stable visual identifiers like axis labels / subplot letters / unit symbols). AI judges per image; no global default bias — see §5.3. |
| `items[].aspect_ratio` | yes | Container sizing | Passed to `image_gen.py --aspect_ratio` |
| `items[].prompt` | yes | §4 assembly | The full assembled paragraph |
| `items[].image_size` | no | Container sizing | `512px` / `1K` / `2K` / `4K` |
| `items[].alt_text` | no | Accessibility | Short caption |
| `items[].slice_grid` | no | §4.3 sheet geometry | Illustration sheet only; exact `RxC` grid to pass to `slice_images.py --grid` |
| `items[].slice_names` | no | §4.3 sheet geometry | Illustration sheet only; semantic filenames to pass to `slice_images.py --names` |
| `items[].status` | yes | CLI manages | `Pending` initially; CLI updates to `Generated` / `Failed` / `Needs-Manual` |

> **Back-compat for legacy `type` values**: existing manifests using `background` / `hero` / `portrait` / `typography` (the four removed pseudo-types) remain readable. Read them as: `background` → `page_role: hero_page` + no type; `hero` → `page_role: hero_page` + no type (use §4.1 Primitive A in prompt); `portrait` → `page_role: local` + no type (use §4.1 Primitive B); `typography` → `page_role: hero_page` + `text_policy: embedded` + no type (use §4.1 Primitive C). New manifests should follow the rule above (omit `type` when `page_role: hero_page`).
>
> **Existing manifest compatibility**:
>
> - **Fixed compatibility defaults**: a missing `page_role` resolves to `local`; a missing `text_policy` resolves to `none`. Emit one aggregate legacy-compatibility warning per manifest.
> - **Declared replay procedure**: an existing manifest may lack `deck_rendering`, or an existing local item may lack `type`, because `items[].prompt` is already assembled. Leave that metadata absent, execute the existing prompt verbatim, and do not reconstruct either value. This exception applies only to replaying an existing manifest; new manifests must satisfy the field table above. A `hero_page` item still omits `type` intentionally.
> - A legacy `deck_palette` field may remain but cannot override `color_scheme`. Read legacy `page_role: full_page` as `hero_page`.

---

## 7. Generation Execution

> Prerequisite: §3 Steps 1-3 complete; `images/image_prompts.json` exists and validates. The manifest is the shared audit/source contract for all modes. It does **not** imply that `image_gen.py --manifest` should run; that command is Path A only.

### Path Selection (Deterministic)

C (AI-generated) supports three implementation modes sharing one `image_prompts.json` source:

| Trigger | Mode | Mechanism |
|---|---|---|
| **Default** — `IMAGE_BACKEND` configured | **Path A**: `image_gen.py --manifest` | One command runs the whole manifest with concurrency; status writes back per item |
| `IMAGE_BACKEND` not configured (or Path A fails) AND host has a native image tool | **Path B**: Host-native tool | Agent invokes the host's image capability; outputs land at `project/images/<filename>` |
| **Both Path A and Path B fail/unavailable** | **Offline Manual Mode** | Manifest stays on disk; user generates externally from `items[].prompt` and places files at `project/images/<filename>` |

**Selection logic — declared-procedure fallback when no path is confirmed**: the confirmed user choice wins. When neither channel confirmed a specific path — the effective choice is `auto` (explicitly confirmed or defaulted) or absent — use the automatic A → B → C chain:

0. **Confirmed override (wins)** — honor `AI Image Acquisition Path` from `design_spec.md §I`. Generate Step 4 already consumed the final confirmation into that durable artifact; do not reopen `result.json` here. If the recorded choice is set and not `auto`, honor it directly, **even when it contradicts `IMAGE_BACKEND`**:
   - `api` → **Path A** (`image_gen.py --manifest`).
   - `host-native` → **Path B** (host's native image tool) — skip A and do **not** run `image_gen.py --manifest`, *even if `IMAGE_BACKEND` is configured*.
   - `manual` → **Offline Manual** (write prompts, render the Markdown sidecar, hand off; do **not** run `image_gen.py --manifest`).
   If an explicitly chosen path is unavailable or still fails after its retry, mark the affected row `Needs-Manual`; do not switch to another automated provider. Only when the Design Spec records `auto` or no specific path applies does the automatic chain decide. A legacy project missing this Design Spec row returns to Step 4 recovery to consume persisted confirmation once and record it; Image_Generator does not inspect the confirmation channel itself.
1. **Try Path A** — if `IMAGE_BACKEND` is configured (env or `.env`), run `image_gen.py --manifest`. If it fails twice in a row, fall to Path B.
2. **Try Path B** — if `IMAGE_BACKEND` was not configured (A skipped), or A failed, and the host has a native image tool (Codex / Antigravity / Claude Code / similar), the agent invokes the host's image capability directly.
3. **Fall to C (Offline Manual)** — if B is also unavailable (no host-native tool) or fails, write prompts to `images/image_prompts.json` and hand off to the user.

**Hard rule**: Step 4 is execution, not re-decision. Never present an interactive choice between paths here — image strategy was locked in Strategist Step 4 h item.

> All three modes share one output contract: file at `project/images/<filename>`. Step 6 SVG references are mode-agnostic.

### Path A — `image_gen.py --manifest` (Default)

```bash
python3 scripts/image_gen.py \
  --manifest project/images/image_prompts.json \
  --output project/images
```

The CLI iterates `items[]` with adaptive concurrency, writes `status` back per item, and is **idempotent**: re-running only re-processes entries whose status is `Pending` or `Failed`.

**Parameters**:

| Parameter | Short | Description | Default |
|---|---|---|---|
| `--manifest` | - | Path to `image_prompts.json` | — |
| `--concurrency` | - | Max concurrent requests; halves on rate-limit, min 1 | `IMAGE_CONCURRENCY` env or `3` |
| `--image_size` | - | Default size (`512px`/`1K`/`2K`/`4K`); per-item `image_size` wins | `1K` |
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
- Outputs **must** land at `project/images/<filename-from-resource-list>`. Match the Image Resource List dimensions when the host supports arbitrary sizes. Hosts with **fixed native resolutions** (common — e.g. ~1672x941 landscape / ~1086x1448 portrait) generate at the closest native size and backfill the actual pixels into the resource list `Dimensions` column — same convention as formula rows ("actual dimensions from formula manifest") and slice rows ("dimensions filled after slicing"). Do **not** upscale the file to fake the requested size (interpolation adds no detail); minor display-side upscaling (up to ~1.3x in practice) may surface as a non-blocking quality-checker warning and requires no acknowledgement.
- Mark each item's `status` `Generated` in the manifest the moment its file lands — as each completes, not in one pass at the end (so an interrupted batch leaves accurate state)
- Executor downstream is path-agnostic — no spec change required between Path A and Path B

### Offline Manual Mode (C's third implementation mode)

**Trigger**: the automatic chain reaches this point after both Path A and Path B fail or are unavailable, the user explicitly confirmed `manual`, or an explicitly confirmed automated path still fails after its own retry.

**Workflow** (no user prompting; system enters this mode automatically):

1. Verify `images/image_prompts.json` was written
2. Set `status: "Needs-Manual"` on every affected item per [`image-base.md`](./image-base.md) §6
3. Continue to Step 6 — Executor draws a dashed placeholder for each `Needs-Manual` row; the Step 7 image readiness gate verifies the supplied files and swaps them in
4. Print one consolidated handoff to the user:
   - Filenames awaiting manual generation
   - Pointer to `images/image_prompts.md` (paste-ready `### Image N:` block per item) or `image_prompts.json` (`items[].prompt`)
   - Target placement: `project/images/<filename>` matching the resource list exactly
   - Resume command: re-run Step 7 once all expected files exist

**User-initiated**: When Strategist Step 4 captured "user wants manual generation" up front, Path A is skipped from the start; the workflow above runs as a planned mode.

> The pipeline tolerates `Needs-Manual` rows end-to-end. The user can leave the project, generate offline at their own pace, then resume Step 7.

#### AI-specific Failure Handling (extends image-base.md §6)

When the path is `auto` and Path A's backend fails twice in a row:

1. Do not halt. Automatically attempt to fall back to **Path B (Host-Native Tool)**.
2. If Path B also fails or is unavailable, mark the row `Needs-Manual`.
3. Report to user: filename, prompt used, error message.
4. Fall through to **Offline Manual Mode** above.

When `api` or `host-native` was explicitly confirmed, failure or unavailability does not authorize an automated provider switch. Retry the confirmed path once; if it still fails, mark the row `Needs-Manual`, report the filename/prompt/error, and use the manual handoff above.

> If the alternate platform watermarks outputs (e.g. Gemini web), the repository includes `scripts/gemini_watermark_remover.py`.

#### Guardrails (All Modes)

**Hard rule**:

- Do not claim an image is generated without an actual file at the expected path
- `Needs-Manual` is set only when `manual` was confirmed or the selected automated recovery path was attempted and failed — not as a way to skip work that automation could have done
- Status transitions are evidence-driven: a file at the expected path permits `Generated`; an exhausted recovery path permits `Needs-Manual`

---

## 8. Common Issues & Variant Workflow

### Reference field is omitted or blank — declared-inference fallback for existing AI rows

When an existing AI Resource List row omits `Reference` or contains a blank `Reference`, infer a reasonable image from its non-empty `Purpose`. If `Purpose` is also omitted or blank, stop and repair the row. Examples (not prescriptions):

| Purpose | A reasonable starting point |
|---------|-----------------------------|
| Cover | `page_role: hero_page` + §4.1 Primitive A (single-subject) or D (atmospheric); choose `text_policy` by what the cover should communicate |
| Chapter divider | `page_role: hero_page` + Primitive D (atmospheric) or A (single-subject); often `text_policy: embedded` with a designed chapter title |
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
| Hex code or color name visible as text in image | Missing §5.1 closing sentence | Append the §5.1 hard rule verbatim |
| Garbled letters in supposedly text-free image | `text_policy: none` rule too weak | Strengthen with explicit list: "no letters, no numbers, no words, no signs, no labels, no captions, no watermarks" |
| SVG text overlay clashes with busy image area | Page design needs negative space the prompt didn't request | Add a composition cue like "leave the {center / left third / lower band} relatively calm for text overlay" — only when the page actually overlays text on top of the image |
| Subject vague | Reference field too abstract | Rewrite reference with concrete nouns (verbs + objects) |
| Faces too realistic / uncanny | §5.2 rule omitted, or rendering is photo-incompatible | Either append §5.2, or switch rendering to a non-photo family |

**Variant workflow**:

1. Set the unsatisfactory item's `status` back to `Pending` and update its `prompt` in place
2. Re-run the same confirmed path used for the original item: Path A may re-run `image_gen.py --manifest` (only that item is re-processed); Path B uses the host-native tool again for that item; Offline Manual re-renders the sidecar and hands off
3. To try multiple stylistic approaches, append additional items with distinct filenames (e.g. `cover_bg_v2.png`) rather than overwriting

---

## 9. Forbidden

- Generating prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description (degrades output)
- Mixing renderings or introducing an unrelated image-only palette across images in the same deck
- Tag-soup prompts (keyword lists separated by commas without a coherent visual scene)
- Globbing `image-renderings/*.md` or any subdirectory — read only the chosen preset or exact custom-reference files
- Placing an image without updating its `image_prompts.json` `status` and the resource list status
- Switching rendering or core deck-color semantics for a single image—`hero_page` is not an exception to deck-wide coherence
- Embedding body copy, data points, bullet lists, or long quotes inside an image — those route to SVG
