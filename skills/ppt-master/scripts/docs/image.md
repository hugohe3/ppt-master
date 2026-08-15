# Image Tools

> **Design boundary**: keep provider credentials explicit, keep in-pipeline
> acquisition manifest-driven, and treat external image references as authoring
> inputs while delivery writes self-contained SVG previews and native PPTX
> media.

Image tools cover prompt-based AI generation, web image search, image inspection,
and Gemini watermark removal. Native formula authoring belongs to the SVG
pipeline, not the image pipeline.

## Legacy standalone `latex_render.py`

This retained standalone utility renders a user-authored
`images/formula_manifest.json` to PNG. Neither Default nor Quick Generate calls
it, and new projects do not create formula manifests or formula images. The
supported generated-deck path authors a native formula marker in SVG and lets
`svg_to_pptx.py` compile its LaTeX payload to editable PowerPoint OMML.

```bash
python3 scripts/latex_render.py <project_path>
python3 scripts/latex_render.py <project_path> --dry-run
```

Use it only for an explicitly requested external raster workflow. It is not a
compatibility fallback for Keynote, WPS, LibreOffice, or another client.

## `image_gen.py`

Unified image generation entry point.

This script is the **Path A** API/proxy executor for generated images. Default
Generate checks `design_spec.md §I / AI Image Acquisition Path` before manifest
mode: only `api` / `auto` permits Path A; a missing or unknown value fails
closed and returns to Step 4 recovery. Quick Generate has no Design Spec: use
the explicit active-context path when supplied, otherwise `auto` selects the
A → B → C chain defined in
[`image-generator.md`](../../references/image-generator.md) §7 without asking.
In either profile, `host-native` uses the host image tool directly and `manual`
uses the read-only Markdown sidecar.

```bash
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py "Abstract tech background" --aspect_ratio 16:9 --image_size 4K
python3 scripts/image_gen.py "Concept car" -o projects/demo/images
python3 scripts/image_gen.py --list-backends
```

Backends are grouped into Core / Extended / Experimental tiers. Run `python3 scripts/image_gen.py --list-backends` for the current list.

Backend selection:

```bash
python3 scripts/image_gen.py "A cat" --backend openai
python3 scripts/image_gen.py "A cinematic portrait" --backend minimax
python3 scripts/image_gen.py "A product launch hero image" --backend qwen
python3 scripts/image_gen.py "科技感背景图" --backend zhipu
python3 scripts/image_gen.py "A product KV in cinematic style" --backend volcengine
```

Configuration sources:

1. Current process environment variables
2. First `.env` found in this order:
   - Current working directory
   - Skill directory (e.g. `~/.agents/skills/ppt-master/.env`)
   - Clone repo root
   - `~/.ppt-master/.env`

The active backend must always be selected explicitly via `IMAGE_BACKEND`.

Example `.env`:

```env
IMAGE_BACKEND=openai
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-image-2
# Optional proxy
# OPENAI_BASE_URL=http://127.0.0.1:3000/v1
# OpenAI-compatible provider knobs:
# OPENAI_SIZE_PRESET=auto
# OPENAI_RESPONSE_FORMAT=auto
# OPENAI_QUALITY=auto
# Allowed values: png / jpeg / webp
# OPENAI_OUTPUT_FORMAT=png
# jpeg/webp only, 0-100
# OPENAI_OUTPUT_COMPRESSION=80
# gpt-image-2: auto / opaque
# OPENAI_BACKGROUND=auto
# auto / low
# OPENAI_MODERATION=auto
```

Example process environment:

```bash
export IMAGE_BACKEND=openai
export OPENAI_API_KEY=sk-xxx
export OPENAI_MODEL=gpt-image-2
export OPENAI_OUTPUT_FORMAT=png
```

Current process environment wins over `.env`.

OpenAI backend notes:
- `gpt-image-2` is the default OpenAI model.
- Requests are sent with plain `requests.post()` to improve compatibility with
  OpenAI-compatible proxies that block the OpenAI SDK's `httpx` transport.
- For `gpt-image-2`, `image_size=512px` means a low-quality draft preset, not a literal 512px edge. The model requires both edges to be multiples of 16px, a long:short ratio no greater than 3:1, and total pixels between 655,360 and 8,294,400.
- `OPENAI_BACKGROUND=transparent` is not supported by `gpt-image-2`; use `auto` or `opaque`.
- If `OPENAI_OUTPUT_FORMAT=jpeg` or `webp`, generated files use `.jpg` or `.webp` extensions instead of `.png`.
- OpenAI-compatible providers that reject OpenAI-specific fields can use `OPENAI_RESPONSE_FORMAT=omit`, `OPENAI_QUALITY=omit`, and `OPENAI_SIZE_PRESET=<preset>`. Valid response formats are `auto`, `b64_json`, `url`, and `omit`; valid size presets are `auto`, `legacy`, `gpt-image`, `gpt-image-2`, and `dall-e-2`.

Example `.env` for Agnes AI through the OpenAI-compatible backend:

```env
IMAGE_BACKEND=openai
OPENAI_API_KEY=your-agnes-key
OPENAI_MODEL=agnes-image-2.1-flash
OPENAI_BASE_URL=https://apihub.agnes-ai.com/v1
OPENAI_SIZE_PRESET=gpt-image-2
OPENAI_RESPONSE_FORMAT=omit
OPENAI_QUALITY=omit
```

Use provider-specific keys only (e.g. `GEMINI_API_KEY`, `OPENAI_API_KEY`). See `.env.example` in clone mode or `${SKILL_DIR}/.env.example` in skill-install mode for the full list per backend.

`IMAGE_API_KEY`, `IMAGE_MODEL`, and `IMAGE_BASE_URL` are intentionally unsupported.

If you keep multiple providers in one `.env` or environment, `IMAGE_BACKEND` must explicitly select the active provider.

Recommendation:
- Default to the Core tier for routine PPT work
- Use Extended only when you need a specific model style
- Treat Experimental backends as opt-in

Example `.env` for MiniMax image backend:

```env
IMAGE_BACKEND=minimax
MINIMAX_API_KEY=your-api-key
# Optional: override base URL (defaults to https://api.minimaxi.com, domestic China endpoint)
# Use https://api.minimax.io for overseas access
# MINIMAX_BASE_URL=https://api.minimax.io
# MINIMAX_MODEL=image-01
```

## `image_treat.py`

Create a non-destructive PNG derivative from one bitmap already prepared under
`<project_path>/images/`. Use this only when a slide needs a baked bitmap effect;
crop, mask, rotation, mirror, opacity, shadow, scrim, outline, and overlap remain
native SVG/PPT treatments. This tool does not perform semantic background
removal: use `slice_images.py --alpha` for flat-color keys, an already prepared
RGBA asset or the active host image editor for a standalone cutout, and
[`image-generator.md`](../../references/image-generator.md) §4.4 only for
registered subject/base layers.

```bash
python3 scripts/image_treat.py projects/demo hero.jpg \
  --output hero_soft.png --brightness 0.9 --contrast 1.1 --blur 12

python3 scripts/image_treat.py projects/demo hero.jpg \
  --output hero_duotone.png --duotone "#14213D" "#FCA311"
```

Supported operations are brightness, contrast, desaturation/grayscale,
duotone, and Gaussian blur. They compose in a fixed order: brightness →
contrast → tone treatment → blur. Desaturation, grayscale, and duotone are
mutually exclusive. At least one option must produce a real change; animated
or multi-frame sources are rejected rather than reduced to one frame.

Both input and output are bare filenames directly under `images/`; output must
be a new `.png` file. The tool keeps the EXIF-corrected display dimensions,
leaves any alpha mask unchanged, and never overwrites the source or an existing
derivative. If `images/image_sources.json` contains the source filename, the
new record inherits that legal provenance and records `derived_from` plus the
ordered `treatments`. Run `analyze_images.py` after all planned derivatives are
ready so the inventory reflects the files that SVG authoring will consume.

## `analyze_images.py`

Analyze objective image-file facts in a project directory before writing the
design spec or authoring SVG.

```bash
python3 scripts/analyze_images.py <project_path>/images
```

The tool does not resolve a canvas or recommend a left/right, top/bottom, or
other slide layout. Its atomic CSV records EXIF-corrected native dimensions and
`AspectRatio`, the objective aspect-ratio category, optional source
`SourceDisplayRatio`, format, actual transparent-pixel presence, usage count,
and bitmap/vector capability facts. An empty folder rewrites a header-only
report; unreadable supported files still refresh the report and produce a
non-zero exit.

Use this as the default factual inventory; it does not perform semantic image
understanding or choose composition. Generate planning follows the Strategist's
context-first boundary: source context, captions / alt text / titles, filenames,
user notes, and existing resource records come first. Only an already-selected
provided/web asset whose focal-safe crop, overlay contrast, or quiet region
remains materially ambiguous may be inspected for that placement; this never
reopens selection or provenance, never bulk-opens the image folder, and never
restores routine readback of AI-generated images.

## `image_search.py`

Zero-config web image search across openly-licensed providers. Sister tool to `image_gen.py` — used when the resource list row has `Acquire Via: web`.

```bash
python3 scripts/image_search.py "offshore wind farm" \
  --filename cover_bg.jpg --slide 01_cover \
  --orientation landscape -o projects/demo/images
```

For multiple web rows, `--batch images/image_queries.json` searches them concurrently (modest default, `--concurrency N` / `IMAGE_SEARCH_CONCURRENCY` to tune) instead of one call per row — the web sister of `image_gen.py --manifest`. Schema and status semantics: [`image-searcher.md`](../../references/image-searcher.md) §5.

Providers (Pexels / Pixabay are tried first when keyed; Openverse and Wikimedia are zero-config fallbacks):

| Provider | Config | Strength |
|---|---|---|
| `pexels` | recommended: `PEXELS_API_KEY` | modern stock photography, people, workplace, lifestyle |
| `pixabay` | recommended: `PIXABAY_API_KEY` | broad type coverage including photos and illustrations |
| `openverse` | zero-config | fallback aggregator: Wikimedia + Flickr + museums + rawpixel |
| `wikimedia` | zero-config | educational, scientific, geographic, historical |

Default search chain (when `--provider` is unset): configured Pexels, configured Pixabay, Openverse, then Wikimedia. Missing keyed credentials are silently skipped. Keyed providers broaden stock-photo coverage but are optional; zero-config providers remain valid.

`image_search.py` uses the same `.env` lookup order as `image_gen.py`, so skill installs can keep `PEXELS_API_KEY` / `PIXABAY_API_KEY` in `~/.ppt-master/.env`.

Query guidance:

Keep the Design Spec §VIII `Reference` as the full visual/crop intent; write a separate concise provider query for this CLI. Start with the shortest phrase that preserves identity, but retain exact multi-word names and necessary disambiguators beyond four words.

For exact entities with multiple common names, add repeatable `--query-variant`
values (batch: `query_variants`) for materially different official
translations, spellings, aliases, or Chinese names. Results are aggregated and
deduplicated before ranking.

| Case | Pattern |
|---|---|
| Generic stock concept | `boardroom meeting` |
| China-specific landmark | Precise official place/identity name plus necessary geography |
| Avoid | Negative prompt wording such as `not tourist snapshot` |

License filter:

- **Default**: search all providers with `cc0,pdm,pexels,pixabay,cc by,cc by-sa` allowed together. The chosen image may be `no-attribution` or `attribution-required`; Executor adds an inline credit only when needed.
- `--strict-no-attribution` restricts the search to `cc0,pdm,pexels,pixabay` — useful for full-bleed hero images or templates that cannot host a credit element.

Pin a provider, refuse attribution, or override the manifest path:

```bash
# Pin Wikimedia
python3 scripts/image_search.py "Olympics opening ceremony" \
  --filename event.jpg --provider wikimedia \
  --orientation landscape -o projects/demo/images

# Strict mode — refuse CC BY / CC BY-SA
python3 scripts/image_search.py "abstract gradient" \
  --filename hero.jpg --strict-no-attribution \
  -o projects/demo/images
```

Suitability & manual replacement (a web top hit is metadata-relevant, not guaranteed visually right):

- By default only the best match is downloaded, plus a downscaled review copy at `images/.review/<stem>.jpg` (the placed asset stays full-resolution).
- For exact subjects (landmarks, people, companies, products), use `--require-terms` or batch `required_terms` so visually plausible but wrong metadata is rejected before ranking. Example: `--require-terms Chongqing --require-terms "Jiefangbei|Liberation Monument"`. Keep proper-name / geography anchors; do not broaden to generic terms like `canyon`, `stone pillar`, or `ancient town` just to improve coverage.
- When the current Generate agent can inspect images, use `--save-candidates`. The tool saves only the first ranked page of review-eligible provider previews (**8 by default**), writes `candidates/<stem>/review_sheet.jpg`, and leaves the target image and `image_sources.json` untouched. Standalone CLI use remains best-only unless this flag is explicit.
- Compare the thumbnail set against the active Reference/Crop Policy. Only after one passes, run `--promote candidate_03.jpg --filename <name>.jpg`; this downloads and validates exactly that original. In batch mode, pass the same `--batch images/image_queries.json` so `Needs-Selection` becomes `Sourced`.
- If no thumbnail passes and `has_more_candidates` is true, fetch `--candidate-page 2` (or set the batch row's `candidate_page` to `next_candidate_page` and reset it to `Pending`). Candidate numbering continues at 9; no original is downloaded. Only after the pool is exhausted should you materially change the identity wording, viewpoint, translation, alias, or disambiguator and generate a fresh pool.
- Without multimodal inspection, omit `--save-candidates`. Best-only mode rejects visual-verification-required near matches, accepts only a strict metadata candidate, downloads one original, and records `selection_method: metadata-ranked`; if metadata cannot prove the entity or the active visual requirement, use `Needs-Manual` rather than claiming visual confirmation.
- `--from-url <url> --filename <name>.jpg` downloads a user-chosen image URL and replaces the target (recorded `license_tier: manual`) — the model-agnostic manual path; works even without a multimodal model.

Full review / escalation flow: [`image-searcher.md`](../../references/image-searcher.md) §5.

Output:

- `--save-candidates`: thumbnail-only `candidates/<stem>/candidates.json`, at most 8 provider previews by default, and `review_sheet.jpg`; no target image or provenance entry. `--candidate-page N` advances through the ranked pool; `--max-candidates 0` explicitly dumps all candidates for exceptional debugging
- Best-only / `--promote`: one original saved to the specified output directory (auto-converts webp → jpg via Pillow when the filename extension demands)
- Best-only / `--promote`: `image_sources.json` manifest with full provenance (provider, license, license_tier, author, source URL, dimensions, attribution_text)
- Manifest is idempotent on `filename` and written atomically; damaged existing provenance blocks replacement

Allowed licenses (default): CC0, Public Domain, Pexels License, Pixabay Content License, CC BY, CC BY-SA. Auto-rejected: CC BY-NC, CC BY-ND, CC BY-NC-SA, CC BY-NC-ND, all rights reserved, unknown.

The full role-level reference (intent → query translation, on-slide attribution contract) is in [`references/image-searcher.md`](../../references/image-searcher.md).

## `gemini_watermark_remover.py`

Remove Gemini watermark assets after manual download.

```bash
python3 scripts/gemini_watermark_remover.py <image_path>
python3 scripts/gemini_watermark_remover.py <image_path> -o output_path.png
python3 scripts/gemini_watermark_remover.py <image_path> -q
```

Notes:
- Requires `scripts/assets/bg_48.png` and `scripts/assets/bg_96.png`
- Best used after downloading “full size” Gemini images

Dependencies:

```bash
pip install Pillow numpy
```
