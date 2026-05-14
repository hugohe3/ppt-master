> See [`image-base.md`](./image-base.md) for the common framework. For the web sourcing path, see [`image-searcher.md`](./image-searcher.md).

# Image_Generator Reference Manual

Role definition for the **AI image generation path**: convert each `Acquire Via: ai` row into an optimized prompt, generate the image, and save it to `project/images/`.

**Trigger**: resource list rows with `Acquire Via: ai`. The role is loaded only when at least one such row exists.

---

## 1. Unified Prompt Structure

### 1.1 Standard Output Format

Every image becomes one entry under `items[]` in `project/images/image_prompts.json`. See §4 for the full schema and a paste-ready template.

| Field | Required | Description |
|---|---|---|
| `filename` | yes | Output filename with extension, e.g. `cover_bg.png` |
| `prompt` | yes | Subject + style + color + composition + quality, assembled per §1.2 |
| `aspect_ratio` | yes | One of §1.5; passed to `image_gen.py --aspect_ratio` |
| `status` | yes | `Pending` for new entries — CLI flips to `Generated` / `Failed` |
| `purpose` | no | Which slide / what function (audit only) |
| `type` | no | `Background` / `Photography` / `Illustration` / `Diagram` / `Decorative` |
| `image_size` | no | `512px` / `1K` / `2K` / `4K`; overrides CLI `--image_size` |
| `alt_text` | no | Caption for accessibility |
| `model` | no | Per-entry model override |

### 1.2 Prompt Components

| Component | Description | Example |
|-----------|-------------|---------|
| Subject description | Core content | `Abstract geometric shapes`, `Team collaboration scene` |
| Style directive | Visual style | `flat design`, `3D isometric`, `watercolor style` |
| Color directive | Color scheme | `color palette: navy blue (#1E3A5F), gold (#D4AF37)` |
| Composition directive | Layout ratio | `16:9 aspect ratio`, `centered composition` |
| Quality directive | Resolution quality | `high quality`, `4K resolution`, `sharp details` |

### 1.3 Style Keywords Quick Reference

| Design Style | Recommended Image Style | Core Keywords |
|-------------|------------------------|---------------|
| General Versatile | Modern illustration, flat design | `modern`, `flat design`, `gradient`, `vibrant colors` |
| General Consulting | Clean professional, corporate | `professional`, `clean`, `corporate`, `minimalist` |
| Top Consulting | Premium minimal, abstract geometric | `premium`, `sophisticated`, `geometric`, `abstract`, `elegant` |
| Technology / SaaS | Futuristic, digital | `futuristic`, `digital`, `tech grid`, `circuit pattern`, `neon accents`, `dark background` |
| Education / Training | Friendly, instructional | `friendly`, `instructional`, `whiteboard style`, `pastel colors`, `simple shapes` |
| Marketing / Branding | Bold, energetic | `bold`, `energetic`, `dynamic composition`, `vivid colors`, `action-oriented` |
| Healthcare / Medical | Clean, reassuring | `clean`, `clinical`, `soft blue-green palette`, `organic curves`, `reassuring` |
| Finance / Banking | Conservative, trustworthy | `conservative`, `trustworthy`, `blue-gray palette`, `structured`, `precise` |
| Creative / Design | Artistic, experimental | `artistic`, `experimental`, `asymmetric`, `textured`, `hand-crafted feel` |

### 1.4 Color Integration Method

Extract colors from design spec, convert to prompt directives:

```
Primary: #1E3A5F (Deep Navy)  →  "deep navy blue (#1E3A5F)"
Secondary: #F8F9FA (Light Gray) →  "light gray (#F8F9FA)"
Accent: #D4AF37 (Gold)        →  "gold accent (#D4AF37)"

Full directive: "color palette: deep navy blue (#1E3A5F), light gray (#F8F9FA), gold accent (#D4AF37)"
```

### 1.5 Canvas Format & Aspect Ratio

| Canvas Format | Background Aspect Ratio | Recommended Resolution |
|--------------|------------------------|----------------------|
| PPT 16:9 | 16:9 | 1920x1080 or 2560x1440 |
| PPT 4:3 | 4:3 | 1600x1200 |
| Xiaohongshu (RED) | 3:4 | 1242x1660 |
| WeChat Moments | 1:1 | 1080x1080 |
| Story | 9:16 | 1080x1920 |

> Supported aspect ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` (Gemini also supports `1:4`, `1:8`, `4:1`, `8:1`)

### 1.6 Multi-Image Coherence Strategy

When generating multiple images for a single deck, visual coherence is critical. Use a **Deck Style Anchor** — a shared prefix of 15-25 words prepended to every image prompt.

**Construction**: Combine style keywords (Section 1.3) + color directive (Section 1.4) + quality directive into one reusable prefix.

**Example**:
```
Deck Style Anchor:
"modern flat design illustration, color palette: deep navy (#1E3A5F), light gray (#F8F9FA), gold accent (#D4AF37), clean minimalist, high quality, 4K"

Image 1 prompt: [Deck Style Anchor], abstract technology network showing connected nodes...
Image 2 prompt: [Deck Style Anchor], team of professionals collaborating at a desk...
Image 3 prompt: [Deck Style Anchor], growth chart with upward trending line...
```

**Exception**: Background images may replace style keywords with `background`, `backdrop`, `negative space for text overlay` while keeping the same color directive. This ensures color consistency without compromising background functionality.

**Rule**: Set `deck_style_anchor` once at the manifest's top level (§4), then prepend its text to every `items[].prompt` value.

---

## 2. Image Type Classification & Handling

### Type Determination Flow

1. Full-page / large-area backdrop → **Background** (2.1)
2. Real scenes / people / products → **Photography** (2.2)
3. Flat / illustration / cartoon style → **Illustration** (2.3)
4. Process / architecture / relationships → **Diagram** (2.4)
5. Partial decoration / texture → **Decorative Pattern** (2.5)

### 2.1 Background

**Identifying characteristics**: Full-page background for covers or chapter pages; must support text overlay

| Key Point | Description |
|-----------|-------------|
| Emphasize background nature | Add `background`, `backdrop` |
| Reserve text area | `negative space in center for text overlay` |
| Avoid strong subjects | Use abstract, gradient, geometric elements |
| Low-contrast details | `subtle`, `soft`, `muted` |

**Template**: `Abstract {theme element} background, {style} style, {primary color} to {secondary color} gradient, subtle {decorative elements}, clean negative space in center for text overlay, {aspect ratio} aspect ratio, high resolution, professional presentation background`

### 2.2 Photography

**Identifying characteristics**: Real scenes, people, products, architecture — photographic quality

| Key Point | Description |
|-----------|-------------|
| Emphasize realism | `photography`, `photorealistic`, `real photo` |
| Lighting effects | `natural lighting`, `soft shadows`, `studio lighting` |
| Background handling | `white background` / `blurred background` / `contextual setting` |
| People diversity | `diverse`, `professional attire` |

**Template**: `{subject description}, professional photography, {lighting type} lighting, {background type} background, color grading matching {color scheme}, high quality, sharp focus, 8K resolution`

### 2.3 Illustration

**Identifying characteristics**: Flat design, vector style, cartoon, concept diagrams

| Key Point | Description |
|-----------|-------------|
| Specify style | `flat design`, `isometric`, `vector style`, `hand-drawn` |
| Simplify details | `simplified`, `clean lines`, `minimal details` |
| Unified palette | Strictly use design spec colors |
| Background choice | `white background` or `transparent background` |

**Template**: `{subject description}, {illustration style} illustration style, {detail level} with clean lines, color palette: {color list}, {background type} background, professional {purpose} illustration`

### 2.4 Diagram

**Identifying characteristics**: Flowcharts, architecture diagrams, concept relationship maps, data visualizations

| Key Point | Description |
|-----------|-------------|
| Clear structure | `clear structure`, `organized layout`, `logical flow` |
| Connection representation | `arrows indicating flow`, `connecting lines` |
| Academic / professional feel | `suitable for academic publication`, `professional diagram` |
| Light background | `white background` or `light gray background` |

**Template**: `{diagram type} diagram showing {content description}, {component description} connected by {connection method}, {style} style with {color scheme}, white background, clear labels, professional technical diagram`

### 2.5 Decorative Pattern

**Identifying characteristics**: Partial decoration, textures, borders, divider elements

| Key Point | Description |
|-----------|-------------|
| Repeatability | `seamless`, `tileable`, `repeatable` (if needed) |
| Understated support | `subtle`, `understated`, `supporting element` |
| Transparency-friendly | `transparent background` or `isolated element` |
| Small-size readability | Consider legibility at small dimensions |

**Template**: `{pattern type} decorative pattern, {style} style, {color scheme}, {background type} background, subtle and elegant, suitable for {purpose}`

---

## 3. Generation Workflow

### 3.1 Prompt Generation Phase

For each image with `Acquire Via: ai` and `Status: Pending`:

1. **Determine type** → Background / Photography / Illustration / Diagram / Decorative
2. **Understand purpose** → Which page? What function?
3. **Analyze the Reference field** → User's intent description
4. **Apply type-specific key points** → Reference §2's table for that type
5. **Generate optimized prompt** → §1.1 schema; prepend the §1.6 Deck Style Anchor
6. **Save manifest** → **Must** write to `project/images/image_prompts.json` with `status: "Pending"` for every new entry
7. **Render Markdown sidecar** → **Must** run `python3 scripts/image_gen.py --render-md project/images/image_prompts.json` to produce the read-only `image_prompts.md` view

**Hard rule**: `image_prompts.md` is auto-generated. Never hand-edit it — re-run `--render-md` (or `--manifest`, which re-renders on completion) to refresh.

> The JSON manifest is machine-consumed by `image_gen.py --manifest`. The Markdown sidecar is the human-readable / paste-ready fallback used in Offline Manual Mode (§3.2).

### 3.2 Image Generation Phase

> Prerequisite: §3.1 must be complete; `images/image_prompts.json` must exist and validate.

#### Path Selection (Deterministic)

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

**Hard rule**: Step 5 is execution, not re-decision. Never present an interactive choice between paths here — image strategy was locked in Strategist Step 4 h item.

> All three modes share one output contract: file at `project/images/<filename>`. Step 6 SVG references are mode-agnostic.

#### Path A — `image_gen.py --manifest` (Default)

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

#### Path B — Host-Native Image Tool (On Explicit User Request)

Triggered only when the user explicitly asks the skill to use the host's built-in image generation (e.g. Codex, Antigravity, or any other host that provides a native image tool).

- Agent invokes the host's native image tool directly; prompts come from `items[].prompt`
- Outputs **must** land at `project/images/<filename-from-resource-list>` with dimensions matching the Image Resource List
- After each placement, set the corresponding item's `status` to `Generated` in the manifest
- Executor downstream is path-agnostic — no spec change required between Path A and Path B

#### Offline Manual Mode (C's third implementation mode)

**Trigger**: Both Path A and Path B fail or are unavailable.

**Workflow** (no user prompting; system enters this mode automatically):

1. Verify `images/image_prompts.json` was written in §3.1
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

## 4. Manifest Template

Write `project/images/image_prompts.json` with this shape. Top-level fields are audit-only; `items[]` is the machine contract.

```json
{
  "project": "{project_name}",
  "generated_at": "{ISO-8601 date}",
  "color_scheme": {
    "primary": "#1A3A5C",
    "secondary": "#F8F9FA",
    "accent": "#E8A838"
  },
  "deck_style_anchor": "{15–25 word prefix per §1.6}",
  "items": [
    {
      "filename": "cover_bg.png",
      "purpose": "Cover background (Slide 01)",
      "type": "Background",
      "aspect_ratio": "16:9",
      "image_size": "2K",
      "prompt": "{deck_style_anchor}, abstract futuristic background with flowing digital waves, deep navy gradient #1A3A5C to midnight, soft particle accents, clean center for text overlay, cinematic, 4K",
      "alt_text": "Modern tech abstract background with deep blue gradient and digital waves",
      "status": "Pending"
    }
  ]
}
```

**Field reference**: see §1.1 for required vs optional. The CLI rewrites each item's `status` (and adds `last_error` on failure) — do not hand-edit those while a run is in flight.

**Paste-ready for manual mode**: each `items[].prompt` is a complete, self-contained prompt; copy it directly into ChatGPT / Gemini / Midjourney when running Offline Manual Mode (§3.2).

---

## 5. Common Issues

### Default Inference When No `Reference` Provided

| Purpose | Default Inference |
|---------|------------------|
| Cover background | Abstract gradient background, reserve central text area |
| Chapter page background | Clean geometric pattern, monochrome focus |
| Team introduction page | Team collaboration scene illustration (flat style) |
| Data display page | Clean geometric pattern or solid color background |
| Product showcase | Product photography style, white or gradient background |

### When Images Are Unsatisfactory

Diagnose the problem category and apply a targeted prompt fix:

| Problem | Diagnosis | Prompt Adjustment |
|---------|-----------|-------------------|
| Wrong style | Image looks photorealistic when flat design was intended | Change style directive: replace `photography` with `flat design illustration` |
| Wrong colors | Colors don't match the design spec palette | Strengthen color directive: add explicit HEX codes, repeat color names |
| Wrong composition | Subject is off-center or layout doesn't fit the slide | Adjust composition directive: add `centered composition`, `rule of thirds`, or `wide negative space on left` |
| Wrong subject | Image depicts something different from what was described | Rewrite subject description with more specificity and concrete details |
| Low quality | Image is blurry, has artifacts, or lacks detail | Add `highly detailed, sharp focus, professional quality, 8K resolution` |

**Variant workflow**:
1. Set the unsatisfactory item's `status` back to `Pending` and update its `prompt` in place
2. Re-run `image_gen.py --manifest` — only that item is re-processed
3. If trying multiple stylistic approaches, append additional items with distinct filenames (e.g. `cover_bg_v2.png`) rather than overwriting

---

## 6. Forbidden

- Generating prompts for `web` rows — those go through [`image-searcher.md`](./image-searcher.md)
- Brand names or HEX codes inside the subject description (degrades output)
- Mixed Deck Style Anchors across images in the same deck (breaks coherence)
- Placing an image without updating its `image_prompts.json` `status` and the resource list status
