> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: convert each `Acquire Via: ai` row into an optimized prompt, generate the image, and save it to `project/images/`.

**Trigger**: resource list rows with `Acquire Via: ai`. The role is loaded only when at least one such row exists.

---

## 0. Core Principle — All AI Images Are Local Inserts

**HARD RULE**: AI-generated images in PPT Master are **local visual blocks** embedded inside SVG pages (left-half illustration, hero banner, background under text, accent spot). They are **not** standalone full-page outputs.

| What this means |
|---|
| Every prompt must produce art that **survives being cropped into a sub-region** of a 16:9 slide |
| Reserve 12-20% inner padding on all sides so content doesn't slam into the container edge |
| Don't ask the model to fill 100% of the canvas with content — leave breathing room |
| The surrounding SVG carries the page's headline / body / labels — your image's job is to **anchor visuals**, not to be the page |

**Escape hatch — full-page AI image (rare, ≤5% of pages)**: when the user explicitly requests "this page is one large image" (typical: cover, chapter divider), mark the item `"page_role": "full_page"` in `image_prompts.json`. Default is `"page_role": "local"`. Do not promote a page to `full_page` without an explicit user instruction.

---

## 1. Three Dimensions

Every AI image is described by three orthogonal dimensions. Lock them in this order: **Rendering** (deck-wide) → **Palette** (deck-wide) → **Type** (per image).

| Dimension | Decides | When fixed |
|---|---|---|
| **Rendering** | Visual style family (vector / sketch-notes / 3d-isometric / corporate-photo / …) | Once per deck — every AI image in the deck shares one rendering |
| **Palette** | How the deck's HEX colors are *used* (proportion + role + temperament). HEX values come from `design_spec.colors`, not from the palette | Once per deck |
| **Type** | What the image's internal composition looks like (background / hero / infographic / framework / comparison / timeline / scene / flowchart / typography) | Per image |

> **What rendering vs palette means**: rendering is *how the image is drawn* (line quality, texture, depth). Palette is *how colors are distributed and behave* (which color dominates, which is accent, what proportion). The HEX values come from Strategist; palette is the **usage contract** for those HEX values.

### 1.1 Where to find each dimension

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

## 2. Workflow

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

1. **Determine type** by matching the row's `Purpose` against types `_index.md` auto-selection table (cover background → `background`; product launch hero → `hero`; methodology visualization → `framework`; etc.) The narrative-shorthand `Type` column in §VIII (Background/Photography/Illustration/Diagram/Decorative) is a hint, not the type's final value — `Purpose` is authoritative for picking among the 9 internal-composition types.
2. **Determine `text_policy`** — read from the row directly if Strategist filled it; otherwise default by type: `background` → `none`; `typography` → `embedded`; everything else → `none` unless the deck rendering is `sketch-notes` / `ink-notes` and Purpose explicitly calls for hand-lettered keywords. The Strategist-supplied value (when present) always wins.
3. **Determine `page_role`** — read from the row directly; default `local`. Only `full_page` if explicitly set.
4. `read_file references/image-type-templates/<type>.md` (only if not already read — types are commonly reused across images in one deck)
5. **Assemble the prompt** by combining:
   - The rendering's style paragraph (from Step 2)
   - The palette's proportion + role rules applied to the deck's HEX values (from Step 2)
   - The type's structural layout (from Step 3)
   - The image's specific `Reference` intent (from `design_spec.md §VIII`)
   - The container sizing guidance from the type file (so the model knows it's painting a local block, not a full canvas)
   - The hard rules from §3 below (HEX-not-as-text, simplified figures, text policy)

The assembled prompt is **one cohesive paragraph**, not a bulleted list of tags. See §1.2 for the assembly template.

### Step 4 — Write the manifest and generate

Write `project/images/image_prompts.json` per §4. Then run `image_gen.py --manifest` (§3.2 Path A). The CLI iterates `items[]`, writes status back, and re-renders the Markdown sidecar.

---

## 1.2 Prompt Assembly Template

Every assembled prompt follows this paragraph structure. **Write prose, not tag soup**.

```
[Rendering style paragraph — 80-120 words from the chosen rendering file].
[Palette behavior — apply the chosen palette's proportion + role rules to the deck's HEX values, e.g. "primary #1E3A5F dominates as the main shape, secondary #F8F9FA provides 60% breathing space, accent #D4AF37 appears in one or two emphasis points only"].
[Type-specific composition — from the chosen type file, e.g. "central hub node with four radiating satellite nodes connected by clean lines"].
[Image-specific subject — translated from the row's Reference intent into concrete visual nouns].
[Container reminder — "composed as a local visual block with 15% padding on all sides, designed to be embedded within a slide region of roughly {W}x{H}px, leaves negative space around edges"].
[Hard rules — see §3].
```

**Word budget**: 150-250 words for `text_policy: none` images, 180-300 words for `text_policy: embedded` images.

**Forbidden — tag-soup prompts**:

```
❌ "modern, flat design, gradient, vibrant, professional, clean, 4K, high quality"
```

This produces generic, model-average output. The model is not weighting your tags — write **one coherent visual scene** instead.

---

## 3. Global Hard Rules

These rules apply to **every** prompt regardless of dimension choices. Append them as a closing sentence to every assembled prompt.

### 3.1 HEX is rendering guidance, not text

Image generation models occasionally paint color names and HEX values as **visible labels in the image** (a `#1E3A5F` swatch literally drawn as the string "#1E3A5F"). This destroys the image.

**Append to every prompt**:

> Color values (HEX codes like #1E3A5F) and color names are rendering guidance only — do NOT display HEX codes, color names, or palette labels as visible text anywhere in the image.

### 3.2 Simplified human figures, no realistic faces

When the image contains people:

> Human figures appear as simplified stylized silhouettes or symbolic representations — no photorealistic faces, no detailed anatomy, no celebrity likeness. Express role/emotion through posture, attire, and simple gestures.

Exception: when the chosen rendering is `corporate-photo`, photorealism is intentional — replace the above with: `Diverse, professionally attired subjects. Editorial photography style, natural composition`.

### 3.3 Text policy — none vs embedded

| `text_policy` | What the image contains | Append to prompt |
|---|---|---|
| `none` (default for most images) | **Zero** text, letters, numbers, labels | "NO text of any kind. No letters, numbers, signs, watermarks, labels, or written symbols anywhere in the image. Clean negative space ready for SVG text overlay." |
| `embedded` (rare — sketch-notes, ink-notes, infographic with hand-lettered keywords) | A small number of short keyword labels rendered as part of the artwork | "Minimal hand-lettered keywords only — 1-5 short words total, each ≤2 words. Use English for keywords (most models render English text reliably; CJK characters are often malformed). No long sentences, no paragraphs, no numbers." |

**CJK warning**: most image models cannot render Chinese characters correctly. For `text_policy: embedded` on a CJK-language deck, either (a) use English keywords, or (b) accept that the model will produce garbled-looking glyphs and the user must regenerate or fix manually.

### 3.4 No brand names or trademarks in the subject

> The image must not depict identifiable brand logos, trademarks, or product likenesses unless the row's Reference explicitly names a real brand asset the user owns.

### 3.5 Deck-wide visual coherence

Every AI image in one deck shares **one** rendering and **one** palette. Mixing renderings across images in the same deck destroys visual coherence. If a single image truly needs a different rendering (e.g. a corporate-photo team shot alongside otherwise vector-illustration imagery), record this as an exception in the row's `Reference` and isolate it to that one image.

---

## 4. Manifest Schema

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
      "type": "background",
      "page_role": "local",
      "text_policy": "none",
      "aspect_ratio": "16:9",
      "image_size": "2K",
      "prompt": "{fully assembled paragraph per §1.2}",
      "alt_text": "Modern tech abstract background with deep blue gradient and digital waves",
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
| `items[].type` | yes | Step 3 per-image | One of: `background`, `hero`, `typography`, `infographic`, `flowchart`, `framework`, `comparison`, `timeline`, `scene` |
| `items[].page_role` | yes | Step 3 per-image | `local` (default) or `full_page` (escape hatch only) |
| `items[].text_policy` | yes | Step 3 per-image | `none` (default for most) or `embedded` (rare) |
| `items[].aspect_ratio` | yes | Container sizing | Passed to `image_gen.py --aspect_ratio` |
| `items[].prompt` | yes | §1.2 assembly | The full assembled paragraph |
| `items[].image_size` | no | Container sizing | `512px` / `1K` / `2K` / `4K` |
| `items[].alt_text` | no | Accessibility | Short caption |
| `items[].status` | yes | CLI manages | `Pending` initially; CLI updates to `Generated` / `Failed` / `Needs-Manual` |

> Existing manifests without `deck_rendering` / `deck_palette` / `type` / `page_role` / `text_policy` remain valid — older items default to `page_role: local`, `text_policy: embedded` for backward compatibility.

---

## 3.2 Generation Execution

> Prerequisite: §2 Steps 1-3 complete; `images/image_prompts.json` exists and validates.

### Path Selection (Deterministic)

C (AI-generated) supports three implementation modes sharing one `image_prompts.json` source:

| Trigger | Mode | Mechanism |
|---|---|---|
| **Default** — `IMAGE_BACKEND` configured | **Path A**: `image_gen.py --manifest` | One command runs the whole manifest with concurrency; status writes back per item |
| **Path A unavailable/fails OR User explicitly names host tool** | **Path B**: Host-native tool | Agent invokes the host's image capability; outputs land at `project/images/<filename>` |
| **Both Path A and Path B fail/unavailable** | **Offline Manual Mode** | Manifest stays on disk; user generates externally from `items[].prompt` and places files at `project/images/<filename>` |

**Selection logic** (automatic, no user prompting):

1. User explicitly named Path B → use Path B
2. Otherwise check `IMAGE_BACKEND` (env or `.env`)
   - configured → use Path A. If Path A fails twice in a row, automatically fall back to Path B.
   - not configured → skip Path A, automatically fall back to Path B.
3. If Path B also fails or the host lacks native image generation → fall through to Offline Manual Mode.

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

### Path B — Host-Native Image Tool (On Explicit User Request)

Triggered only when the user explicitly asks the skill to use the host's built-in image generation (e.g. Codex, Antigravity, or any other host that provides a native image tool).

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

## 5. Common Issues & Variant Workflow

### Default Inference When No `Reference` Provided

| Purpose | Default Inference (assembled from rendering + palette + type) |
|---------|---------------------------------------------------------------|
| Cover background | `type: background`, `text_policy: none` — abstract atmospheric block matching deck rendering, generous center negative space |
| Chapter divider background | `type: background`, `text_policy: none` — slightly more structured than cover (geometric anchor permitted) |
| Methodology / framework illustration | `type: framework`, `text_policy: none` — central node + radiating satellites, no labels (SVG carries names) |
| Process / workflow illustration | `type: flowchart`, `text_policy: none` — sequential blocks with arrows |
| Before/After or two-option page | `type: comparison`, `text_policy: none` or `embedded` |
| Team / lifestyle photo | `type: scene`, `text_policy: none`, rendering should be `corporate-photo` or `warm-scene` |
| Big-number / hero quote block | `type: typography` or `hero`, `text_policy: embedded` (the number/keyword is the visual) |

### When Images Are Unsatisfactory

Diagnose the failure category, adjust the **one specific dimension** responsible, do not rewrite the whole prompt.

| Symptom | Most likely cause | Adjustment |
|---|---|---|
| Image looks generic, model-average | Tag-soup prompt | Rewrite as one coherent paragraph per §1.2 |
| Wrong style family (looks photorealistic when flat was intended) | Rendering mismatch or rendering paragraph diluted | Reaffirm chosen rendering's style paragraph at the top of the prompt |
| Colors don't match deck | HEX not echoed in prompt, or palette proportion rule omitted | Repeat HEX values 2-3 times in the prompt; restate palette proportion rule |
| Hex code or color name visible as text in image | Missing §3.1 closing sentence | Append the §3.1 hard rule verbatim |
| Garbled letters in supposedly text-free image | `text_policy: none` rule too weak | Strengthen with explicit list: "no letters, no numbers, no words, no signs, no labels, no captions, no watermarks" |
| Composition too busy, no room for SVG overlay | Missing container reminder | Add explicit "leaves at least 30% negative space in the {center / left third / lower band} for text overlay" |
| Subject vague | Reference field too abstract | Rewrite reference with concrete nouns (verbs + objects) |
| Faces too realistic / uncanny | §3.2 rule omitted, or rendering is photo-incompatible | Either append §3.2, or switch rendering to a non-photo family |

**Variant workflow**:

1. Set the unsatisfactory item's `status` back to `Pending` and update its `prompt` in place
2. Re-run `image_gen.py --manifest` — only that item is re-processed
3. To try multiple stylistic approaches, append additional items with distinct filenames (e.g. `cover_bg_v2.png`) rather than overwriting

---

## 6. Forbidden

- Generating prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description (degrades output)
- Mixing renderings or palettes across images in the same deck
- Tag-soup prompts (keyword lists separated by commas without a coherent visual scene)
- Globbing `image-renderings/*.md` or any subdirectory — read only the chosen file
- Placing an image without updating its `image_prompts.json` `status` and the resource list status
- Promoting a page to `page_role: full_page` without explicit user instruction
