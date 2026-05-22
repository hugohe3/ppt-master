> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: convert each `Acquire Via: ai` row into an optimized prompt, generate the image, and save it to `project/images/`.

**Trigger**: resource list rows with `Acquire Via: ai`. The role is loaded only when at least one such row exists.

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

- Same `deck_rendering` + same `deck_palette` for every image in the deck
- HEX codes and color names are rendering guidance — never visible text in the image
- Long body copy / data points / bulleted lists / long quotes stay in SVG (improving them later means regenerating the image, which is expensive)
- **In-image text is only for words that will not need editing later** — visual keywords, decorative lettering, mood words. Editable text (titles that may be reworded, subtitles, dates, authors, captions, body) belongs in SVG. Changing one in-image word costs an image regeneration; one SVG word costs a keystroke.
- Prompts are one coherent prose paragraph, not tag soup (a model-output reality, not an aesthetic choice)

Everything else is the AI's judgment per page. No mandated padding, no type-locked text_policy, no scenario whitelists for hero_page.

---

## 2. Three Dimensions

Every AI image is described by three orthogonal dimensions. Lock them in this order: **Rendering** (deck-wide) → **Palette** (deck-wide) → **Type** (per image).

| Dimension | Decides | When fixed |
|---|---|---|
| **Rendering** | Visual style family (vector / sketch-notes / 3d-isometric / corporate-photo / …) | Once per deck — every AI image in the deck shares one rendering |
| **Palette** | How the deck's HEX colors are *used* (proportion + role + temperament). HEX values come from `design_spec.colors`, not from the palette | Once per deck |
| **Type** | What the image's internal composition skeleton looks like — geometric layout of a local infographic block (infographic / flowchart / framework / matrix / cycle / funnel / pyramid / comparison / timeline / map / scene). Only applies to `page_role: local`; for `page_role: hero_page`, describe composition with §4.1 primitives instead of picking a type. | Per image |

> **What rendering vs palette means**: rendering is *how the image is drawn* (line quality, texture, depth). Palette is *how colors are distributed and behave* (which color dominates, which is accent, what proportion). The HEX values come from Strategist; palette is the **usage contract** for those HEX values.

### 2.1 Where to find each dimension

| Reference | Loaded |
|---|---|
| [`image-renderings/_index.md`](./image-renderings/_index.md) — rendering catalog + auto-selection table | Always (Step 1 below) |
| [`image-palettes/_index.md`](./image-palettes/_index.md) — palette catalog + auto-selection table | Always (Step 1 below) |
| [`image-type-templates/_index.md`](./image-type-templates/_index.md) — type catalog + auto-selection table | Always (Step 1 below) |
| `image-renderings/<chosen>.md` | After Step 2 picks the rendering — only the chosen one |
| `image-palettes/<chosen>.md` | After Step 2 picks the palette — only the chosen one |
| `image-type-templates/<chosen>.md` | After Step 3 picks the type per image — only the types actually used |

**Hard rule — on-demand loading**:

- Read the three `_index.md` files once at role entry.
- After locking dimensions, read **only** the specific rendering / palette / type files you selected.
- **Never** glob-read an entire subdirectory (`image-renderings/*.md` is forbidden). Token cost balloons and the AI loses focus.

---

## 3. Workflow

### Step 1 — Load the dimension indices

Read all three index files. They are short (~50 lines each) and contain auto-selection tables that let you map `design_spec` signals → dimension values without reading every detail file.

```
read_file references/image-renderings/_index.md
read_file references/image-palettes/_index.md
read_file references/image-type-templates/_index.md
```

### Step 2 — Resolve deck-wide rendering + palette

**Primary path — Strategist already locked these in `spec_lock.md colors`**:

```
image_rendering: vector-illustration
image_palette: cool-corporate
```

If both fields are present, use them directly — Strategist made the decision in h.5 with full d-e-f-g-h linkage context. Do NOT re-decide.

**Hard rule — `custom` escape hatch**: when either value is the literal string `custom`, do NOT `read_file` the preset library for that dimension. Read the sibling `*_behavior` line from `spec_lock.md colors` and splice that prose into the prompt in place of the preset's fewshot snippet. The behavior prose owns the style paragraph (for `custom` rendering) or the proportion/role rules (for `custom` palette). See [`image-renderings/_index.md`](./image-renderings/_index.md) §1.5 / [`image-palettes/_index.md`](./image-palettes/_index.md) §2 for the invocation rules.

**Fallback path — when `spec_lock.md` lacks both fields** (legacy decks or pipelines that skipped h.5):

| Signal | Maps to |
|---|---|
| `design_spec.md d. Style` mode + descriptor | Rendering (consult renderings `_index.md` auto-selection table) |
| `design_spec.md e. Color Scheme` (HEX) + content vibe | Palette (consult palettes `_index.md` auto-selection table) |
| `design_spec.md f. Icon library` | Sanity check: chosen rendering should be compatible with the icon library's visual weight |

If the auto-selection table surfaces multiple candidates, pick the first; do not present a choice to the user.

> **Tell the user**: when falling back, print one line "spec_lock.md missing `image_rendering`/`image_palette` — inferring `<X>` / `<Y>` from design_spec. For optimal deck consistency, lock these in Strategist h.5." Then proceed.

Then `read_file` the **single resolved** rendering file and the **single resolved** palette file. These two files give you:

- The 80-120 word style paragraph (rendering)
- The proportion / role / temperament rules for the deck's three HEX values (palette)
- Two ready-to-paste prompt snippets per file (fewshot)

### Step 3 — Per-image type + assembly

For each `Acquire Via: ai` row in `design_spec.md §VIII`:

1. **Determine type** — only when `page_role: local` (the image sits as a region block on an SVG page). Match the row's `Purpose` against the `_index.md` auto-selection table (methodology visualization → `framework`; process steps → `flowchart`; SWOT/Eisenhower → `matrix`; PDCA / flywheel → `cycle`; etc.). `Purpose` is authoritative for picking among the 11 internal-composition types. **When `page_role: hero_page`, skip type selection** and describe composition directly using §4.1 primitives (single-subject / portrait / typographic / atmospheric).
2. **Determine `text_policy`** — Strategist's value wins when set. Otherwise pick `none` or `embedded` based on whether in-image text serves the page. Long body / data / lists stay in SVG.
3. **Determine `page_role`** — Strategist's value wins when set. Otherwise pick `local` or `hero_page` based on whether the image carries the page or sits inside one.
4. `read_file references/image-type-templates/<type>.md` (only if not already read — types are commonly reused across images in one deck)
5. **Assemble the prompt** by combining:
   - The rendering's style paragraph (from Step 2)
   - The palette's proportion + role rules applied to the deck's HEX values (from Step 2)
   - The type's structural layout (from Step 3)
   - The image's specific `Reference` intent (from `design_spec.md §VIII`)
   - The container sizing guidance from the type file (so the model knows it's painting a local block, not a full canvas)
   - The hard rules from §5 below (HEX-not-as-text, simplified figures, text policy)

The assembled prompt is **one cohesive paragraph**, not a bulleted list of tags. See §4 for the assembly template.

### Step 4 — Write the manifest and generate

Write `project/images/image_prompts.json` per §6. Then run `image_gen.py --manifest` (§7 Path A). The CLI iterates `items[]`, writes status back, and re-renders the Markdown sidecar.

---

## 4. Prompt Assembly Template

Every assembled prompt follows this paragraph structure. **Write prose, not tag soup**.

```
[Rendering style paragraph — 80-120 words from the chosen rendering file].
[Palette behavior — apply the chosen palette's proportion + role rules to the deck's HEX values, e.g. "primary #1E3A5F dominates as the main shape, secondary #F8F9FA provides 60% breathing space, accent #D4AF37 appears in one or two emphasis points only"].
[Type-specific composition — from the chosen type file, e.g. "central hub node with four radiating satellite nodes connected by clean lines"].
[Image-specific subject — translated from the row's Reference intent into concrete visual nouns].
[Container note — "composed as a {W}x{H}px image for {page_role} use"; add composition cues only when the page actually needs them (e.g. "leave the lower band relatively calm — SVG title overlays it")].
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

Use with `text_policy: embedded`. Must obey the §5.3 text-accuracy rules (English short-text and simple numbers reliable; CJK and long sentences fail — for those, switch to Primitive D + SVG overlay).

**Primitive D — atmospheric backdrop (no subject)**

> Atmospheric field with no dominant subject — gradients, subtle patterns, or restrained color blocks. Small geometric anchor optional, placed in a corner or along an edge, never centered. The center 60-70% of the canvas must stay calm to receive SVG title/text overlay.

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

### 5.3 Text policy — none vs embedded

| `text_policy` | Prompt cue |
|---|---|
| `none` | "NO text of any kind anywhere in the image — no letters, numbers, signs, watermarks, labels, or written symbols." |
| `embedded` | Describe the text directly inside the visual scene: the word(s), how they're rendered (decorative lettering / designed title / hand-lettered keyword), and the artistic treatment. Examples below. |

**When to pick `embedded` — the edit-stability test**

Before adding any word to the image, ask: *will this word ever need to be changed?* If yes, it belongs in SVG, not the image. The bar is high — in-image text is for words that are part of the visual itself.

| Page situation | Recommended approach |
|---|---|
| **hero_page** — cover, chapter divider, section opener | **Two-layer**: 1-3 high-impact visual keywords go *in* the image (`embedded`); subtitle, date, author, organization, edition, body intro stay on the SVG overlay. **Do not** put the full title block (main + subtitle + author + date) into the image — any later wording change forces an image regen. |
| **local image — infographic / framework / flowchart / matrix / cycle / comparison** | `none` — labels live as SVG text so they stay editable. The image carries the structure; SVG carries the words. |
| **local image — decorative background / scene / portrait** | `none` by default. Use `embedded` only if a decorative word *is* the visual (e.g. a giant "GROWTH" lettering as wall art). |
| **Poster / standalone marketing-style page** | `embedded` allowed for the visual core word; auxiliary copy still SVG. |

The principle in one line: **the image gets the unchanging visual keywords; SVG gets everything readable that might be reworded**.

**Prompt phrasing examples for embedded text** (not an exhaustive list):

- Decorative: "large 'GROWTH' lettering as a background element, 3D extruded retro chrome style"
- Designed title: "main title 'Q3 STRATEGY' typeset in clean geometric sans-serif, centered"
- Hand-lettered set: "small hand-lettered annotations 'fast', 'cheap', 'good' woven into the sketch"

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
- Any case where rendering + palette already imply a font character (e.g. `vintage-poster` rendering implies period display lettering) → trust the rendering, no need to echo SVG body

**When to use the table**: a designed title (cover main title, chapter heading) on a deck whose visual identity is grounded in the SVG body typography, and where a surprise font choice would feel out of place.

**In-image text accuracy — what image models can and cannot render reliably**

Image models have **variable accuracy on text rendering**. Pick the in-image text content with this in mind, especially for §4.1 Primitive C (typographic hero) where the word *is* the image:

| Content | Reliability |
|---|---|
| English short text (1-5 characters, one short word) | High — most modern models render correctly most of the time |
| English longer text (full sentences) | Low — typos, glyph errors, dropped letters |
| Simple numbers / symbols (`100`, `5x`, `$50M`, `∞`, `?`) | Variable — verify after generation, often fail at large display scale |
| Chinese / Japanese / Korean characters | Very low — most models fail consistently |

**Prefer in-image**: a short English word (1-2 words max), a simple number, a single symbol or letter.

**Push to SVG overlay instead**: long quotes / sentences, CJK headlines, complex composite text. When the desired headline is long or CJK, switch to **Primitive D (atmospheric backdrop)** and overlay the headline as SVG text.

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
  "deck_palette": "cool-corporate",
  "color_scheme": {
    "primary": "#1E3A5F",
    "secondary": "#F8F9FA",
    "accent": "#D4AF37"
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
| `deck_palette` | yes | Step 2 lock | Single palette name shared by all items |
| `color_scheme` | yes | `design_spec.md §III` | HEX triplet from Strategist |
| `items[].filename` | yes | `§VIII` resource list | Output filename with extension |
| `items[].type` | conditional | Step 3 per-image (only when `page_role: local`) | One of 11 internal-composition types: `infographic`, `flowchart`, `framework`, `matrix`, `cycle`, `funnel`, `pyramid`, `comparison`, `timeline`, `map`, `scene`. **Omit `type` entirely when `page_role: hero_page`** — the composition comes from §4.1 primitives written directly into the prompt, not from a type file. |
| `items[].page_role` | yes | Step 3 per-image | `local` (default — region block on SVG page) or `hero_page` (image is page's main voice; SVG overlay minimal or empty) |
| `items[].text_policy` | yes | Step 3 per-image | `none` (default — no text in image) or `embedded` (image contains decorative lettering, designed title, or hand-lettered keywords) |
| `items[].aspect_ratio` | yes | Container sizing | Passed to `image_gen.py --aspect_ratio` |
| `items[].prompt` | yes | §4 assembly | The full assembled paragraph |
| `items[].image_size` | no | Container sizing | `512px` / `1K` / `2K` / `4K` |
| `items[].alt_text` | no | Accessibility | Short caption |
| `items[].status` | yes | CLI manages | `Pending` initially; CLI updates to `Generated` / `Failed` / `Needs-Manual` |

> **Back-compat for legacy `type` values**: existing manifests using `background` / `hero` / `portrait` / `typography` (the four removed pseudo-types) remain readable. Read them as: `background` → `page_role: hero_page` + no type; `hero` → `page_role: hero_page` + no type (use §4.1 Primitive A in prompt); `portrait` → `page_role: local` + no type (use §4.1 Primitive B); `typography` → `page_role: hero_page` + `text_policy: embedded` + no type (use §4.1 Primitive C). New manifests should follow the rule above (omit `type` when `page_role: hero_page`).
>
> Existing manifests without `deck_rendering` / `deck_palette` / `type` / `page_role` / `text_policy` remain valid — older items default to `page_role: local`, `text_policy: none`. Legacy `page_role: full_page` (pre-2026-05-15) is read as `hero_page`.

---

## 7. Generation Execution

> Prerequisite: §3 Steps 1-3 complete; `images/image_prompts.json` exists and validates.

### Path Selection (Deterministic)

C (AI-generated) supports three implementation modes sharing one `image_prompts.json` source:

| Trigger | Mode | Mechanism |
|---|---|---|
| **Default** — `IMAGE_BACKEND` configured | **Path A**: `image_gen.py --manifest` | One command runs the whole manifest with concurrency; status writes back per item |
| `IMAGE_BACKEND` not configured (or Path A fails) AND host has a native image tool | **Path B**: Host-native tool | Agent invokes the host's image capability; outputs land at `project/images/<filename>` |
| **Both Path A and Path B fail/unavailable** | **Offline Manual Mode** | Manifest stays on disk; user generates externally from `items[].prompt` and places files at `project/images/<filename>` |

**Selection logic** — monotonic A → B → C fallback chain (automatic, no user prompting):

1. **Try Path A** — if `IMAGE_BACKEND` is configured (env or `.env`), run `image_gen.py --manifest`. If it fails twice in a row, fall to Path B.
2. **Try Path B** — if `IMAGE_BACKEND` was not configured (A skipped), or A failed, and the host has a native image tool (Codex / Antigravity / Claude Code / similar), the agent invokes the host's image capability directly.
3. **Fall to C (Offline Manual)** — if B is also unavailable (no host-native tool) or fails, write prompts to `images/image_prompts.json` and hand off to the user.

**User override**: If the user explicitly names Path B ("use Codex's image tool"), skip A and start at B. Explicit naming is the only way to bypass an earlier path in the chain; otherwise the chain is monotonic.

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
- First `.env` found in this order: current working directory, clone repo root, `~/.ppt-master/.env`

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

> Use provider-specific names only (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). See `.env.example` in clone mode or `${SKILL_DIR}/.env.example` in skill-install mode for the full set per backend.

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
- Outputs **must** land at `project/images/<filename-from-resource-list>` with dimensions matching the Image Resource List
- After each placement, set the corresponding item's `status` to `Generated` in the manifest
- Executor downstream is path-agnostic — no spec change required between Path A and Path B

### Offline Manual Mode (C's third implementation mode)

**Trigger**: Both Path A and Path B fail or are unavailable.

**Workflow** (no user prompting; system enters this mode automatically):

1. Verify `images/image_prompts.json` was written
2. Set `status: "Needs-Manual"` on every affected item per [`image-base.md`](./image-base.md) §6
3. Continue to Step 6 — SVG references `images/<filename>` optimistically; Step 7 entry verifies presence
4. Print one consolidated handoff to the user:
   - Filenames awaiting manual generation
   - Pointer to `images/image_prompts.md` (paste-ready `### Image N:` block per item) or `image_prompts.json` (`items[].prompt`)
   - Target placement: `project/images/<filename>` matching the resource list exactly
   - Resume command: re-run Step 7 once all expected files exist

**User-initiated**: When Strategist Step 4 captured "user wants manual generation" up front, Path A is skipped from the start; the workflow above runs as a planned mode.

> The pipeline tolerates `Needs-Manual` rows end-to-end. The user can leave the project, generate offline at their own pace, then resume Step 7.

#### AI-specific Failure Handling (extends image-base.md §6)

If Path A's backend fails twice in a row:

1. Do not halt. Automatically attempt to fall back to **Path B (Host-Native Tool)**.
2. If Path B also fails or is unavailable, mark the row `Needs-Manual`.
3. Report to user: filename, prompt used, error message.
4. Fall through to **Offline Manual Mode** above.

> If the alternate platform watermarks outputs (e.g. Gemini web), the repository includes `scripts/gemini_watermark_remover.py`.

#### Guardrails (All Modes)

**Hard rule**:

- Do not claim an image is generated without an actual file at the expected path
- `Needs-Manual` is set after a failed attempt OR on entering Offline Manual Mode — not as a way to skip work that automation could have done
- Status transitions are evidence-driven: `Pending` → `Generated` (file exists) or `Pending` → `Needs-Manual` (no automation, or attempt failed once)

---

## 8. Common Issues & Variant Workflow

### Reference field is blank — quick examples

When the Resource List row has no `Reference`, infer a reasonable image from `Purpose`. Examples (not prescriptions):

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
| Colors don't match deck | HEX not echoed in prompt, or palette proportion rule omitted | Repeat HEX values 2-3 times in the prompt; restate palette proportion rule |
| Hex code or color name visible as text in image | Missing §5.1 closing sentence | Append the §5.1 hard rule verbatim |
| Garbled letters in supposedly text-free image | `text_policy: none` rule too weak | Strengthen with explicit list: "no letters, no numbers, no words, no signs, no labels, no captions, no watermarks" |
| SVG text overlay clashes with busy image area | Page design needs negative space the prompt didn't request | Add a composition cue like "leave the {center / left third / lower band} relatively calm for text overlay" — only when the page actually overlays text on top of the image |
| Subject vague | Reference field too abstract | Rewrite reference with concrete nouns (verbs + objects) |
| Faces too realistic / uncanny | §5.2 rule omitted, or rendering is photo-incompatible | Either append §5.2, or switch rendering to a non-photo family |

**Variant workflow**:

1. Set the unsatisfactory item's `status` back to `Pending` and update its `prompt` in place
2. Re-run `image_gen.py --manifest` — only that item is re-processed
3. To try multiple stylistic approaches, append additional items with distinct filenames (e.g. `cover_bg_v2.png`) rather than overwriting

---

## 9. Forbidden

- Generating prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description (degrades output)
- Mixing renderings or palettes across images in the same deck
- Tag-soup prompts (keyword lists separated by commas without a coherent visual scene)
- Globbing `image-renderings/*.md` or any subdirectory — read only the chosen file
- Placing an image without updating its `image_prompts.json` `status` and the resource list status
- Switching rendering or palette for a single image — `hero_page` is not an exception to deck-wide coherence
- Embedding body copy, data points, bullet lists, or long quotes inside an image — those route to SVG
