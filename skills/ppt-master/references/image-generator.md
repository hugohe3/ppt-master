# Image_Generator Reference Manual

> This file is the streamlined reference for the Image_Generator role. Common standards (SVG technical constraints, canvas formats, post-processing pipeline, etc.) are in [shared-standards.md](./shared-standards.md).

## Core Mission

Receive the "Image Resource List" from the Design Specification & Content Outline output by the Strategist, acquire every non-user image asset required by the deck, and save the resulting files to the project's `images/` directory.

**Trigger condition**: When non-user image acquisition is needed (AI generation and/or web sourcing), whether standalone or invoked within the pipeline.

| Mode | Trigger | Description |
|------|---------|-------------|
| **Standalone** | Directly describe image needs | Acquire single or multiple non-user image assets |
| **In-pipeline** | `generate-ppt` with AI generation or web sourcing selected | Batch-acquire image assets for a project |

> Next step in pipeline: Executor generates SVGs

---

## 1. Input & Output

### Input

- **Design Specification & Content Outline** (from Strategist): project theme, target audience, design style, color scheme, canvas format
- **Image Resource List** (key input):

  | Filename | Dimensions | Purpose | Type | Acquire Via | Status | Reference | Attribution |
  |----------|-----------|---------|------|-------------|--------|-----------|-------------|
  | cover_bg.png | 1920x1080 | Cover background | Background | ai | Pending | Modern tech abstract background, deep blue gradient | N/A |

  Status values are defined in [`svg-image-embedding.md`](svg-image-embedding.md). Image_Generator consumes only `Pending` rows whose `Acquire Via` is `ai` or `web`, and changes them to `Generated`, `Sourced`, or `Needs-Manual`.

### Output

| Deliverable | Path / Description | Requirements |
|------------|-------------------|--------------|
| Prompt document | `project/images/image_prompts.md` | Required for `ai` rows; **must** be saved using file write tool — cannot just be output in conversation |
| Source manifest | `project/images/image_sources.json` | Required for `web` rows; records queries, chosen source, output filename, and attribution |
| Optimized prompts | Individual prompt per AI image | Directly usable with AI image generation tools; doubles as alt text |
| Image files | `project/images/` directory | Named per the resource list filenames |
| Updated list | Status changes | `Pending` -> `Generated` (AI success), `Pending` -> `Sourced` (web success), or `Pending` -> `Needs-Manual` (acquisition attempted and failed) |

---

## 2. Unified Prompt Structure

### 2.1 Standard Output Format

Every AI image must be output in the following format:

```markdown
### Image N: {filename}

| Attribute | Value |
| --------- | ----- |
| Purpose   | {which page / what function} |
| Type      | {Background / Illustration / Photography / Diagram / Decorative} |
| Dimensions | {width}x{height} ({aspect ratio}) |
| Original description | {reference provided by Strategist for the `ai` row} |

**Prompt**:
{subject description}, {style directive}, {color directive}, {composition directive}, {quality directive}

**Negative Prompt**:
{elements to exclude}

**Alt Text**:
> {Description for accessibility and image captions}
```

### 2.2 Prompt Components

| Component | Description | Example |
|-----------|-------------|---------|
| Subject description | Core content | `Abstract geometric shapes`, `Team collaboration scene` |
| Style directive | Visual style | `flat design`, `3D isometric`, `watercolor style` |
| Color directive | Color scheme | `color palette: navy blue (#1E3A5F), gold (#D4AF37)` |
| Composition directive | Layout ratio | `16:9 aspect ratio`, `centered composition` |
| Quality directive | Resolution quality | `high quality`, `4K resolution`, `sharp details` |
| Negative prompt | Exclude elements | `text, watermark, blurry, low quality` |

### 2.3 Style Keywords Quick Reference

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

### 2.4 Color Integration Method

Extract colors from design spec, convert to prompt directives:

```
Primary: #1E3A5F (Deep Navy)  →  "deep navy blue (#1E3A5F)"
Secondary: #F8F9FA (Light Gray) →  "light gray (#F8F9FA)"
Accent: #D4AF37 (Gold)        →  "gold accent (#D4AF37)"

Full directive: "color palette: deep navy blue (#1E3A5F), light gray (#F8F9FA), gold accent (#D4AF37)"
```

### 2.5 Canvas Format & Aspect Ratio

| Canvas Format | Background Aspect Ratio | Recommended Resolution |
|--------------|------------------------|----------------------|
| PPT 16:9 | 16:9 | 1920x1080 or 2560x1440 |
| PPT 4:3 | 4:3 | 1600x1200 |
| Xiaohongshu (RED) | 3:4 | 1242x1660 |
| WeChat Moments | 1:1 | 1080x1080 |
| Story | 9:16 | 1080x1920 |

> Supported aspect ratios: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9` (Gemini also supports `1:4`, `1:8`, `4:1`, `8:1`)

### 2.6 Multi-Image Coherence Strategy

When generating multiple AI images for a single deck, visual coherence is critical. Use a **Deck Style Anchor** — a shared prefix of 15-25 words prepended to every image prompt.

**Construction**: Combine style keywords (Section 2.3) + color directive (Section 2.4) + quality directive into one reusable prefix.

**Example**:
```
Deck Style Anchor:
"modern flat design illustration, color palette: deep navy (#1E3A5F), light gray (#F8F9FA), gold accent (#D4AF37), clean minimalist, high quality, 4K"

Image 1 prompt: [Deck Style Anchor], abstract technology network showing connected nodes...
Image 2 prompt: [Deck Style Anchor], team of professionals collaborating at a desk...
Image 3 prompt: [Deck Style Anchor], growth chart with upward trending line...
```

**Exception**: Background images may replace style keywords with `background`, `backdrop`, `negative space for text overlay` while keeping the same color directive. This ensures color consistency without compromising background functionality.

**Rule**: Define the Deck Style Anchor once in the prompt document header (Section 5), then reference it in every individual prompt.

---

## 3. Image Type Classification & Handling

### Type Determination Flow

1. Full-page / large-area backdrop → **Background** (3.1)
2. Real scenes / people / products → **Photography** (3.2)
3. Flat / illustration / cartoon style → **Illustration** (3.3)
4. Process / architecture / relationships → **Diagram** (3.4)
5. Partial decoration / texture → **Decorative Pattern** (3.5)

### 3.1 Background

**Identifying characteristics**: Full-page background for covers or chapter pages; must support text overlay

| Key Point | Description |
|-----------|-------------|
| Emphasize background nature | Add `background`, `backdrop` |
| Reserve text area | `negative space in center for text overlay` |
| Avoid strong subjects | Use abstract, gradient, geometric elements |
| Low-contrast details | `subtle`, `soft`, `muted` |

**Template**: `Abstract {theme element} background, {style} style, {primary color} to {secondary color} gradient, subtle {decorative elements}, clean negative space in center for text overlay, {aspect ratio} aspect ratio, high resolution, professional presentation background`

**Negative prompt**: `text, letters, watermark, faces, busy patterns, high contrast details`

### 3.2 Photography

**Identifying characteristics**: Real scenes, people, products, architecture — photographic quality

| Key Point | Description |
|-----------|-------------|
| Emphasize realism | `photography`, `photorealistic`, `real photo` |
| Lighting effects | `natural lighting`, `soft shadows`, `studio lighting` |
| Background handling | `white background` / `blurred background` / `contextual setting` |
| People diversity | `diverse`, `professional attire` |

**Template**: `{subject description}, professional photography, {lighting type} lighting, {background type} background, color grading matching {color scheme}, high quality, sharp focus, 8K resolution`

**Negative prompt**: `watermark, text overlay, artificial, CGI, illustration, cartoon, distorted faces`

### 3.3 Illustration

**Identifying characteristics**: Flat design, vector style, cartoon, concept diagrams

| Key Point | Description |
|-----------|-------------|
| Specify style | `flat design`, `isometric`, `vector style`, `hand-drawn` |
| Simplify details | `simplified`, `clean lines`, `minimal details` |
| Unified palette | Strictly use design spec colors |
| Background choice | `white background` or `transparent background` |

**Template**: `{subject description}, {illustration style} illustration style, {detail level} with clean lines, color palette: {color list}, {background type} background, professional {purpose} illustration`

**Negative prompt**: `realistic, photography, 3D render, complex textures, watermark`

### 3.4 Diagram

**Identifying characteristics**: Flowcharts, architecture diagrams, concept relationship maps, data visualizations

| Key Point | Description |
|-----------|-------------|
| Clear structure | `clear structure`, `organized layout`, `logical flow` |
| Connection representation | `arrows indicating flow`, `connecting lines` |
| Academic / professional feel | `suitable for academic publication`, `professional diagram` |
| Light background | `white background` or `light gray background` |

**Template**: `{diagram type} diagram showing {content description}, {component description} connected by {connection method}, {style} style with {color scheme}, white background, clear labels, professional technical diagram`

**Negative prompt**: `cluttered, messy, overlapping elements, dark background, realistic, photography`

### 3.5 Decorative Pattern

**Identifying characteristics**: Partial decoration, textures, borders, divider elements

| Key Point | Description |
|-----------|-------------|
| Repeatability | `seamless`, `tileable`, `repeatable` (if needed) |
| Understated support | `subtle`, `understated`, `supporting element` |
| Transparency-friendly | `transparent background` or `isolated element` |
| Small-size readability | Consider legibility at small dimensions |

**Template**: `{pattern type} decorative pattern, {style} style, {color scheme}, {background type} background, subtle and elegant, suitable for {purpose}`

**Negative prompt**: `busy, cluttered, high contrast, distracting, photorealistic`

---

## 4. Image Acquisition Workflow

### 4.1 Analysis Phase

1. Read the design spec; understand overall project style
2. Extract color scheme, canvas format, target audience
3. Analyze each image in the resource list individually
4. Determine each image's type (refer to Section 3)
5. Separate rows by `Acquire Via`: `ai` rows require prompts, `web` rows require source search

### 4.2 Prompt & Source Preparation Phase

For each `Pending` row:

1. **Determine type** → Background / Photography / Illustration / Diagram / Decorative
2. **Understand purpose** → Which page? What function?
3. **Read `Reference`** → This drives either prompt writing or web search
4. **Apply type-specific handling** → Reference the corresponding type's table
5. **For `ai` rows** → Generate optimized prompt using the 2.1 standard output format
6. **For `web` rows** → Prepare a source record containing query/source target, chosen file, and attribution
7. **Save acquisition artifacts**:
   - `project/images/image_prompts.md` for `ai` rows
   - `project/images/image_sources.json` for `web` rows

### 4.3 Image Acquisition Phase

> Prerequisite: Section 4.2 must be complete. Create `images/image_prompts.md` for `ai` rows and `images/image_sources.json` for `web` rows when applicable.

#### Path Selection (Deterministic)

| Trigger | Path |
|---------|------|
| User explicitly requests web image search | `web` |
| No image-generation API key and deck benefits from imagery, after user confirmation | `web` |
| Image-generation API key present and no web request | `ai` |

Agent must follow this table exactly when deciding between `ai` and `web`.

#### AI Path — `image_gen.py`

```bash
python3 scripts/image_gen.py "your prompt" \
  --aspect_ratio 16:9 --image_size 1K \
  --output project/images --filename cover_bg
```

**Parameters**:

| Parameter | Short | Description | Default |
|-----------|-------|-------------|---------|
| `prompt` | - | Positive prompt (positional arg) | - |
| `--negative_prompt` | `-n` | Negative prompt | None |
| `--aspect_ratio` | - | Image aspect ratio | `1:1` |
| `--image_size` | - | Size (`1K`/`2K`/`4K`) | `1K` |
| `--output` | `-o` | Output directory | Current directory |
| `--filename` | `-f` | Output filename (no extension) | Auto-named |
| `--backend` | `-b` | Override backend (see `--list-backends` for options) | None |
| `--model` | `-m` | Model name | Backend default |
| `--list-backends` | - | Print support tiers and exit | `false` |

**Configuration sources**:
- Current process environment variables
- Project-root `.env` as fallback

Precedence:
- Current process environment wins
- `.env` fills missing values only

| Variable | Required | Description |
|----------|----------|-------------|
| `IMAGE_BACKEND` | Required | Backend identifier; run `image_gen.py --list-backends` for the current set |
| `{PROVIDER}_API_KEY` | Required | Provider-specific API key, e.g. `GEMINI_API_KEY`, `ZHIPU_API_KEY` |
| `{PROVIDER}_BASE_URL` | Optional | Provider-specific custom endpoint |
| `{PROVIDER}_MODEL` | Optional | Provider-specific model override |

> Use provider-specific names only (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). See `.env.example` for the full set per backend.
>
> `IMAGE_API_KEY`, `IMAGE_MODEL`, and `IMAGE_BASE_URL` are intentionally unsupported.
>
> If `.env` or the current environment contains multiple provider configs, `IMAGE_BACKEND` explicitly selects the active one.

**Support tiers (recommended usage)**: Core / Extended / Experimental. Run `image_gen.py --list-backends` for the current assignments.

**Generation pacing (mandatory)**:
- Execute only one generation command at a time; wait for file confirmation before the next
- Recommend 2-5 second intervals between images to avoid concurrency failures

#### Web Path — `image_search.py`

```bash
python3 scripts/image_search.py "query or source target" \
  --output project/images --filename office-team
```

- Use the `Reference` field as the search target or source hint
- Save source-selection details to `project/images/image_sources.json`
- Record attribution exactly as required by the chosen source
- Outputs **must** land at `project/images/<filename-from-resource-list>`

#### Failure Handling (Applies to Both Paths)

If acquisition fails for a given image:

1. **Retry once.** If the retry also fails, stop attempting that image — do not loop further.
2. **Do NOT halt the pipeline.** Report the failures to the user: list the affected filenames and the error reason, and ask the user to provide those images manually at `project/images/<filename>` with the exact filename from the resource list.
3. **Mark the affected rows** in the Image Resource List as `Needs-Manual`.
4. **Proceed to the Executor phase.** Executor consumes whatever is in `project/images/` at its runtime; missing files are handled downstream (placeholder or user prompt), not by blocking here.

If the user chooses to provide manually sourced files that need cleanup, the repository includes `scripts/gemini_watermark_remover.py` as a utility for watermark-bearing images.

#### Guardrails (Both Paths)

- Agent must NOT claim an image is acquired without producing an actual file at the expected path
- Agent must NOT mark an image as `Needs-Manual` without a real acquisition attempt having failed
- Status transitions are evidence-driven:
  - `Pending` -> `Generated` when an AI-generated file exists at the expected path
  - `Pending` -> `Sourced` when a web-sourced file exists at the expected path
  - `Pending` -> `Needs-Manual` when acquisition was attempted and failed after one retry

### 4.4 Verification Phase

- Confirm all successfully acquired images are saved to the `images/` directory
- Check filenames match the resource list
- Update image resource list:
  - `Generated` for AI files present at the expected path
  - `Sourced` for web files present at the expected path
  - `Needs-Manual` for rows whose acquisition failed after one retry
- Confirm `project/images/image_prompts.md` exists when `ai` rows were processed
- Confirm `project/images/image_sources.json` exists when `web` rows were processed
- Any `Needs-Manual` rows must have been reported to the user with filename and error reason before this phase completes

---

## 5. Prompt Document Template

Use the following structure when creating `project/images/image_prompts.md`:

```markdown
# Image Acquisition Prompts

> Project: {project_name}
> Generated: {date}
> Color scheme: Primary {#HEX} | Secondary {#HEX} | Accent {#HEX}

---

## Image List Overview

| # | Filename | Type | Dimensions | Status |
|---|----------|------|-----------|--------|
| 1 | cover_bg.png | Background | 1920x1080 | Pending |

---

## Detailed Prompts

### Image 1: cover_bg.png

| Attribute | Value |
|-----------|-------|
| Purpose | Cover background |
| Type | Background |
| Dimensions | 1920x1080 (16:9) |
| Original description | Modern tech abstract background, deep blue gradient |

**Prompt**:
Abstract futuristic background with flowing digital waves...

**Alt Text**:
> Modern tech abstract background with deep blue gradient, digital waves, and particle effects

---

## Usage Instructions

1. Copy the "Prompt" above into an AI image generation tool
2. Recommended platforms: gpt-image-2 / Midjourney / DALL-E 3 / Gemini / Stable Diffusion
3. Rename generated images to the corresponding filenames
4. Place in the `images/` directory
```

Use the following structure when creating `project/images/image_sources.json`:

```json
[
  {
    "filename": "office-team.jpg",
    "query": "modern office collaboration team photo",
    "reference": "Openverse search: modern office collaboration",
    "selected_source": "https://example.org/source-page",
    "attribution": "Photo by ...",
    "status": "Sourced"
  }
]
```

---

## 6. Negative Prompt Quick Reference

### By Image Type

| Type | Recommended Negative Prompt |
|------|---------------------------|
| Background | `text, letters, watermark, faces, busy patterns, high contrast details` |
| Photography | `watermark, text overlay, artificial, CGI, illustration, cartoon, distorted faces` |
| Illustration | `realistic, photography, 3D render, complex textures, watermark` |
| Diagram | `cluttered, messy, overlapping elements, dark background, realistic` |
| Decorative pattern | `busy, cluttered, high contrast, distracting, photorealistic` |

### Universal Negative Prompts

- **Standard**: `text, watermark, signature, blurry, distorted, low quality`
- **Extended** (people scenarios): `text, watermark, signature, blurry, low quality, distorted, extra fingers, mutated hands, poorly drawn face, bad anatomy, extra limbs, disfigured, deformed`

---

## 7. Common Issues

### Default Inference When No `Reference` Provided

| Purpose | Default Inference |
|---------|------------------|
| Cover background | Abstract gradient background, reserve central text area |
| Chapter page background | Clean geometric pattern, monochrome focus |
| Team introduction page | Team collaboration scene illustration (flat style) |
| Data display page | Clean geometric pattern or solid color background |
| Product showcase | Product photography style, white or gradient background |

### When Images Are Unsatisfactory

Diagnose the problem category and apply a targeted fix:

| Problem | Diagnosis | Adjustment |
|---------|-----------|------------|
| Wrong style | Image looks photorealistic when flat design was intended | Change style directive: replace `photography` with `flat design illustration`, or refine the web query/source target |
| Wrong colors | Colors don't match the design spec palette | Strengthen color directive for AI, or choose a better-matched web source |
| Wrong composition | Subject is off-center or layout doesn't fit the slide | Adjust composition directive or select a source with the required crop/negative space |
| Wrong subject | Image depicts something different from what was described | Rewrite the prompt/query with more specificity and concrete details |
| Low quality | Image is blurry, has artifacts, or lacks detail | Retry with higher quality prompt settings or choose a better source image |

**Variant workflow**:
1. Keep the original prompt or source choice as "Variant A"
2. Create a modified prompt or alternate source as "Variant B"
3. If needed, create "Variant C" with a different stylistic approach
4. Label all variants clearly so the user can compare results

---

## 8. Role Collaboration

### Handoff with Strategist

| Direction | Content |
|-----------|---------|
| Receives | Design Specification & Content Outline (with image resource list) |
| Trigger condition | User selected "C) AI-generated" or "D) Web-sourced" in "Image usage" |
| Key information | Color scheme, design style, canvas format, `Acquire Via`, `Reference`, `Attribution` |

### Handoff with Executor

| Direction | Content |
|-----------|---------|
| Delivers | All acquired images placed in `project/images/` directory |
| Executor reference | `<image href="../images/xxx.png" .../>` |
| Path note | SVGs in `svg_output/`, images in `images/`; use relative path `../images/` |

---

## 9. Task Completion Checkpoint

### Must-complete Items

- [ ] Created prompt document `project/images/image_prompts.md` for `ai` rows when applicable
- [ ] Created source manifest `project/images/image_sources.json` for `web` rows when applicable
- [ ] Each AI image has: type determination + optimized prompt + negative prompt + Alt Text
- [ ] Each sourced image has: query/source target + selected source + attribution record
- [ ] Updated image resource list statuses
- [ ] Phase completion confirmation output

### Image Readiness

- [ ] All acquired images saved to `project/images/` directory
- [ ] Or: User clearly informed which rows are `Needs-Manual`

### Pipeline Flow

- [ ] User prompted to proceed to next step (switch to Executor role)

> **Critical check**: If `images/image_prompts.md` was required and not created, or if `images/image_sources.json` was required and not created, or if the status outputs do not match the resource list, the task is NOT complete.

### Completion Confirmation Output Format

```markdown
## Image Acquisition Phase Complete

- [x] Created prompt document `project/images/image_prompts.md` for AI rows
- [x] Created source manifest `project/images/image_sources.json` for web rows
- [x] All acquired images saved to `images/` directory
- [x] Updated image resource list status

**Image Status Summary**:

| Filename | Type | Dimensions | Status |
|----------|------|-----------|--------|
| cover_bg.png | Background | 1920x1080 | Generated |
| office-team.jpg | Photography | 1600x900 | Sourced |

**Next step**: Switch to Executor role to begin SVG generation
```
