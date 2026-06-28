> See [`image-base.md`](./image-base.md) for the common framework. Technical SVG/PPT constraints are in [`shared-standards.md`](./shared-standards.md).

# Image_Searcher Reference Manual

Role definition for the **web image acquisition path**: translate Strategist intent into keyword queries, search openly-licensed providers, download a license-cleared image into `project/images/`, and record provenance + license metadata into `image_sources.json`.

**Trigger**: resource list rows with `Acquire Via: web`. The role is loaded only when at least one such row exists.

---

## 1. License Tier Discipline

Every **provider-sourced** image is classified into one of two tiers; anything else is rejected outright. A third tier, `manual`, exists **only** for a user-supplied [`--from-url`](#5-running-image_searchpy) replacement — it is never the result of a provider search accepting an unknown license.

| Tier | Licenses | On-slide attribution |
|---|---|---|
| `no-attribution` | CC0, Public Domain, Pexels License, Pixabay Content License | None |
| `attribution-required` | CC BY, CC BY-SA | Inline credit `<text>` on the slide |
| `manual` | User-supplied via `--from-url` (license unverified) | None — verifying rights / any credit is the user's responsibility |

**Forbidden — auto-rejected licenses**:

- CC BY-NC, CC BY-NC-SA (non-commercial)
- CC BY-ND, CC BY-NC-ND (no derivatives)
- All Rights Reserved
- Unknown / missing license

> `license_tier` is the central abstraction. Downstream consumers (Executor) read this single field and never interpret raw license strings.

---

## 2. Search Strategy

Default: quality-first across all allowed license tiers. Do not prefer CC0 / Public Domain over a better CC BY / CC BY-SA image; rely on the manifest's `license_tier` so Executor can add attribution only when needed.

```
Default: provider chain, license filter = cc0,pdm,pexels,pixabay,cc by,cc by-sa
         → rank candidates across providers; first downloadable ranked hit wins.
Strict:  provider chain, license filter = cc0,pdm,pexels,pixabay
         → fail if no no-attribution image can be downloaded.
```

`--strict-no-attribution` is opt-in. Use it only when the deck cannot tolerate any on-slide credit (corporate template, full-bleed hero).

---

## 3. Providers

| Provider | Config | Strength |
|---|---|---|
| Openverse | zero-config | fallback aggregator: Wikimedia + Flickr + museums + rawpixel |
| Wikimedia Commons | zero-config | educational, scientific, geographic, historical |
| Pexels | recommended: `PEXELS_API_KEY` (free, [signup](https://www.pexels.com/api/)) | modern stock photography, people, workplace, lifestyle |
| Pixabay | recommended: `PIXABAY_API_KEY` (free, [signup](https://pixabay.com/api/docs/)) | broad type coverage including photos and illustrations |

Default chain (when `--provider` is unset):

```
openverse → wikimedia → pexels (if PEXELS_API_KEY set) → pixabay (if PIXABAY_API_KEY set)
```

Keyed providers without an API key are silently skipped — not an error.

**Validation**: For polished visual decks, configure at least one keyed provider before using `Acquire Via: web`.

---

## 4. Intent → Query Translation

Web image APIs match keywords against image metadata, not semantic embeddings. `simplify_query` automatically:

1. Strips HEX color codes (`#1E3A5F`) and parentheticals (`(corporate vibe)`)
2. Drops hard-noise words: brand names, generic filler
3. Drops soft-noise words (`ai`, `tech`, `platform`, `professional`, `editorial`, `photo`, `background`) — only when concrete nouns remain
4. Caps at 4 words
5. **Fail-open**: if filtering empties the query, return the original

Then `build_query_progression` tries: original → simplified (4 words) → simplified (3 words). First non-empty hit wins.

**Per-row web Reference grammar**:

| Segment | Rule |
|---|---|
| Subject | Use 1-2 concrete nouns only: `offshore wind farm`, `Xiamen skyline`, `boardroom meeting` |
| Quality cues | **DO NOT ADD QUALITY CUES** like `professional editorial photography` or `clean composition`. These APIs use exact keyword matching; adding long adjectives will result in 0 matches. |
| Language | For Chinese landmarks: use precise Chinese names (e.g., `磁器口古镇`) if specifically targeting `--provider wikimedia`. For general stock providers (Pexels/Pixabay), use simple English nouns (e.g., `Chongqing Jiefangbei`); do NOT use complex Chinese sentences or overly long English descriptive strings which fail on these platforms. |

When the subject is an exact entity (landmark / person / company / product / venue), write `required_terms` at the same time you write the row's `query`. Use one required group per identity anchor and `|` for aliases / translations, e.g. `["Chongqing|重庆", "Jiefangbei|解放碑|Liberation Monument"]`. This keeps the query short for provider search while preventing metadata-ranked wrong entities from being accepted.

**Forbidden — web negative prompts**: `not tourist snapshot`, `no amateur photo`, `avoid low quality`.

> Note: Keyword APIs search negative words literally.

| ✅ Good Reference (intent) | ❌ Avoid |
|---|---|
| "Offshore wind farm at dusk, aerial view, professional editorial photography" | "professional editorial photography background" |
| "Diverse engineering team collaborating around a laptop, modern office, natural light" | "use Openverse, search 'team'" |
| "Sunlit forest path in autumn, clean composition, high-resolution photography" | "Hero image, dramatic lighting" |

---

## 5. Running `image_search.py`

```bash
python3 scripts/image_search.py "<query>" \
  --filename <name>.jpg \
  --slide <slide_id> \
  --orientation landscape \
  --purpose background \
  -o <project_path>/images
```

| Parameter | Required | Default | Description |
|---|---|---|---|
| `query` | yes | — | Positional. Pre-simplification not necessary; CLI runs `simplify_query` internally. |
| `--filename` | yes | — | Output filename matching the resource list |
| `-o / --output` | no | `.` | Output directory; manifest defaults to `<output>/image_sources.json` |
| `--slide` | no | `""` | Slide ID from resource list (recorded in manifest) |
| `--purpose` | no | `""` | `background` / `hero` / `side` / `accent` |
| `--orientation` | no | `any` | `any` / `landscape` / `portrait` / `square` |
| `--provider` | no | (chain) | Pin one provider |
| `--strict-no-attribution` | no | off | Restrict to no-attribution licenses; refuse CC BY / CC BY-SA |
| `--require-terms` | no | — | Entity-safety gate for exact subjects. Repeatable; comma separates required groups; `A|B` means aliases within one group. Example: `--require-terms Chongqing --require-terms "Jiefangbei|Liberation Monument"` |
| `--manifest` | no | (default) | Override manifest path |
| `--save-candidates` | no | off | Escalation only: also keep a review pool in `candidates/<stem>/`. Default downloads just the best match (+ a review copy) |
| `--max-candidates` | no | `4` | Pool size when `--save-candidates` is set |
| `--promote` | no | — | Promote a reviewed candidate to the target filename, e.g. `--promote candidate_03.jpg --filename team.jpg -o <dir>` |
| `--from-url` | no | — | Manual replace: download a user-supplied image URL into `--filename` (recorded `license_tier: manual`); works without a multimodal model |

### Batch mode (≥ 2 web rows) — preferred

When more than one row is `Acquire Via: web`, do **not** call the CLI once per row. Write all rows into one `image_queries.json` and run a single concurrent batch — the web sister of `image_gen.py --manifest`:

```bash
python3 scripts/image_search.py --batch <project_path>/images/image_queries.json \
  -o <project_path>/images
```

`image_queries.json` schema (one item per web row):

```json
{
  "items": [
    {
      "filename": "jiefangbei.jpg",
      "query": "Jiefangbei Chongqing downtown monument",
      "slide": "03_landmark",
      "purpose": "exact landmark photo",
      "orientation": "landscape",
      "required_terms": ["Chongqing", "Jiefangbei|Liberation Monument"],
      "status": "Pending"
    }
  ]
}
```

Required per item: `filename`, `query`, `status` (`Pending`). Optional per-item overrides: `slide`, `purpose`, `orientation`, `provider`, `strict_no_attribution`, `min_width`, `min_height`, `required_terms`.

Use `required_terms` for **exact-entity images**: landmarks, people, companies, products, venues, named artworks, and named institutions. Each list item is required; alternatives inside one item use `|`. Example for a Chongqing landmark: `["Chongqing|重庆", "Jiefangbei|解放碑|Liberation Monument"]`. This is a metadata gate: candidates whose title / author / source URL do not satisfy every group are rejected before ranking, so a visually polished but wrong Rome / Hoi An image cannot win a Chongqing landmark row. Do **not** use `required_terms` for generic mood / background rows such as "modern city skyline" or "team collaboration".

The runner searches all `Pending` / `Failed` rows concurrently, appends each success to `image_sources.json` (the credit source of truth, idempotent on `filename`), and writes status back into `image_queries.json` — `Sourced` on success, `Needs-Manual` when the full provider/stage chain is exhausted. Status is saved after each completion, so an interrupted run preserves finished rows; re-running skips terminal rows. A single `web` row may still use single-query mode above.

**Pacing**: free providers (Wikimedia/Openverse) are rate-sensitive, so batch concurrency defaults to a modest **3** (`--concurrency N`, or `IMAGE_SEARCH_CONCURRENCY` env). Use `--concurrency 1` to restore strict one-at-a-time pacing. Single-query mode is one request at a time by nature.

### Ranking model

`image_search.py` ranks provider metadata, not pixels. The order is deliberately conservative:

1. hard reject: invalid license, zero query relevance, or any missing `required_terms`;
2. identity priority: every required term group must match; candidates whose title also contains the required entity terms get an additional boost over candidates that only match via URL;
3. query relevance: concrete query tokens dominate generic visual words like "photo", "high quality", "background";
4. layout fit: requested orientation helps; mismatched orientation is a small penalty, not a hard reject;
5. license / size tie-breakers: no-attribution is a small bonus; pixel count is capped so a huge but weakly relevant image cannot outrank a smaller accurate image.

Do not tune this into a visual taste engine. The scorer prevents obvious metadata failures and produces a reviewable best match; the `.review` copy still decides whether the image is visually fit for the slide.

### Suitability review — with or without a multimodal model

A metadata-ranked top hit is *downloadable and token-relevant*, not necessarily *visually suitable* — `score_candidate` never sees pixels. So a web best match should be reviewed before it is trusted, by whichever reviewer is available:

- **Multimodal model**: each download writes a downscaled review copy to `images/.review/<stem>.jpg` (the placed asset stays full-resolution; the bounded copy just keeps a very large original safe and quick to open). Read it and judge fit — subject, mood, quality, not just topic overlap.
- **Non-multimodal model (no vision)**: do **not** pretend to confirm. Hand off to a human — surface each web image's `source_page_url` from `image_sources.json` (live preview also shows the placed result) and let the user judge.

For exact-entity rows, suitability has two gates: `required_terms` first enforces metadata identity, then the `.review` image confirms the pixels actually show the right subject well enough. A row can still be rejected after passing `required_terms` if the visual is weak, cropped badly, or only tangentially shows the subject.

**Replacement ladder when a best match is not right** (any reviewer):

1. refine the query and re-run that row once;
2. **manual URL replace (universal, model-agnostic)** — the user finds a better image anywhere and gives its URL; download and swap it in:
   ```bash
   python3 scripts/image_search.py --from-url <image-url> --filename <name>.jpg -o <project_path>/images
   ```
   Recorded with `license_tier: manual` — verifying usage rights is the user's call. Human replacement is a legitimate outcome, not a failure. It updates the image and `image_sources.json` but does **not** rewrite `image_queries.json`, so a row fixed this way may still read `Needs-Manual` in the batch manifest — harmless: the file is present, so export proceeds (executor-base §6.1);
3. (opt-in) `--save-candidates` to pull auto-alternatives with their own `source_page_url`s, then `--promote` the best (below);
4. if nothing fits, mark the row `Needs-Manual`.

Web search is far cheaper than AI generation, so this review pass is well worth it.

**This review never halts the pipeline** (image-base §6 hard rule). It runs inside Step 5 image acquisition: an image that cannot be verified or replaced right now becomes `Needs-Manual` and the deck still builds (placeholder), so generation flows straight into Step 6. Manual `--from-url` replacement is an improvement step, not a blocking gate — do it now, or later from live preview, without stopping the run.

### Manual review candidates (escalation, opt-in)

Candidate-pool saving is **off by default** — reach for it only when a best match fails confirmation, on a subjective topic, or for a prominent image (cover / chapter divider / `hero_page` / photo-led page).

```bash
python3 scripts/image_search.py "<query>" --filename <name>.jpg -o <project_path>/images \
  --save-candidates --max-candidates 4
```

Saves the top candidates to `images/candidates/<stem>/` with a `candidates.json` manifest and one downscaled review copy per candidate under `candidates/<stem>/review/`. **Read the candidate review copies**, pick the best fit, then promote it — the full-resolution original is copied to the target filename:

```bash
python3 scripts/image_search.py --promote candidate_03.jpg --filename <name>.jpg -o <project_path>/images
```

---

## 6. Manifest Format (`image_sources.json`)

Every successful download appends or replaces one entry keyed on `filename`:

```json
{
  "license_verification": "provider metadata used; manual review recommended for external delivery",
  "generated_at": "2026-05-01T12:17:59.856275Z",
  "items": [
    {
      "filename": "team.jpg",
      "slide": "03_team",
      "purpose": "Leadership photo",
      "search_query": "executive boardroom meeting",
      "orientation": "landscape",
      "provider": "openverse",
      "stage": "all",
      "title": "Untitled",
      "author": "",
      "source_page_url": "https://www.rawpixel.com/...",
      "download_url": "https://...",
      "license_name": "CC0",
      "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
      "license_tier": "no-attribution",
      "attribution_required": false,
      "width": 1024,
      "height": 683,
      "metadata_dimensions": {
        "width": 4800,
        "height": 3200,
        "note": "upstream-reported size; actual downloaded file is smaller (likely a preview)"
      },
      "attribution_text": "team.jpg — \"Untitled\" via Openverse — license: CC0 (...)",
      "status": "sourced"
    }
  ]
}
```

| Field | Notes |
|---|---|
| `width` / `height` | Measured from the file actually saved to disk. Use these for layout. |
| `metadata_dimensions` | Present only when upstream-claimed size differs from the saved file (preview vs original). Informational only. |
| `license_tier` | Drives Executor's attribution decision: `no-attribution` / `attribution-required` for provider-sourced images, or `manual` for a user-supplied `--from-url` replacement (embed only; rights/credit are the user's responsibility). |
| `attribution_required` | Boolean alias of `license_tier == "attribution-required"`. |
| `attribution_text` | Pre-rendered canonical credit string. **Use as-is; do not regenerate.** |
| `stage` | `all` by default, or `no-attribution-only` when strict mode is used. |

> Manifest is **idempotent on `filename`**. Rerunning the CLI replaces that entry; other entries are preserved.

---

## 7. On-Slide Attribution — Visual Specification

Applied by Executor when an image's `license_tier == "attribution-required"`. Three layouts depending on the page.

### 7.1 Single-image page

- **Position**: bottom-right of the image's container, hugging the image edge (within ~8 px)
- **Font size**: 6–8pt equivalent (≈ 0.7–1 % of canvas short edge)
- **Color**: `#999` on light/photo backgrounds; `rgba(255,255,255,0.6)` on dark/photo
- **Content**: `© {author} / {provider_short} / {license_short}`
  - `provider_short`: `Openverse` / `Wikimedia` / `Pexels` / `Pixabay`
  - `license_short`: `CC BY 4.0` / `CC BY-SA 4.0` / `Public Domain`
  - Drop empty fields (CC0 with no author → `via Openverse`)

**Forbidden — fields that break the visual line**: full URLs, `attribution_text` verbatim, "License:" prefix.

### 7.2 Multi-image page (≥ 2 attribution-required)

Combine into one source line at the page bottom rather than scattering credits:

```
Sources: a, b via Wikimedia (CC BY); c via Openverse (CC BY-SA)
```

Use single-letter labels (a/b/c) only when needed for disambiguation.

### 7.3 Hero / full-bleed image

- Bottom 1.5 cm gradient overlay: transparent → `rgba(0,0,0,0.5)`
- 7pt white semi-transparent text inside the overlay band, right-aligned ~24 px from edge

### 7.4 Source for the credit text

Use `attribution_text` from the manifest as the **starting point**. Compress for the small-text constraint:

| Manifest | Slide credit |
|---|---|
| `team.jpg — "Untitled" via Openverse — license: CC0 (...)` | `via Openverse / CC0` |
| `team.jpg — "Sunset" by Jane Doe via Wikimedia Commons — license: CC BY-SA 4.0 (...)` | `© Jane Doe / Wikimedia / CC BY-SA 4.0` |

---

## 8. Failure Handling (web-specific)

Extends [`image-base.md`](./image-base.md) §6.

| Situation | Behavior |
|---|---|
| No candidates from any provider in either stage | Mark row `Needs-Manual`. Suggest: shorter query, drop `--strict-no-attribution`, or set keyed provider's API key. |
| Single candidate fails to download (HTTP 403/404) | Dispatcher auto-falls through to the next ranked candidate. No user action. |
| All candidates from one provider fail | Dispatcher moves to the next provider in the chain. |
| Keyed provider has no API key | Silently skipped. Not an error. |

CLI exit: `0` on success, `1` only when no acceptable image was found across the entire dispatch matrix.

---

## 9. Handoff with Strategist

Reference field is **intent description**, not a query. See [`image-base.md`](./image-base.md) §8 for the rule.

If the description is verbose, that's fine — `simplify_query` handles it.

---

## 10. Handoff with Executor

Executor reads `image_sources.json` per slide that uses a Sourced image. For each entry:

| `license_tier` | Slide-level action |
|---|---|
| `no-attribution` | Embed `<image>` only |
| `attribution-required` | Embed `<image>` **and** an inline credit element per §7 |
| `manual` | Embed `<image>` only — user-supplied URL (`--from-url`); verifying usage rights / any required credit is the user's responsibility |

Executor does not interpret raw license strings — `license_tier` is sufficient.

`svg_quality_checker.py` verifies this handoff before post-processing: if an attribution-required image is referenced without visible `CC BY` / `CC BY-SA` credit text, the SVG fails the quality gate.

---

## 11. Task Completion Checkpoint

In addition to the shared checkpoint in [`image-base.md`](./image-base.md) §10:

- [ ] Every web row has a downloaded file at `project/images/<filename>` OR is marked `Needs-Manual`
- [ ] Each `Sourced` web image was reviewed for fit — a multimodal model via its `images/.review/<stem>.jpg` copy, otherwise handed to the user via `source_page_url`; a poor fit was re-queried, replaced with `--from-url`, escalated via `--save-candidates` + `--promote`, or marked `Needs-Manual`
- [ ] Each `Sourced` row has a manifest entry with valid `license_tier` and non-empty `attribution_text` (except `manual` `--from-url` rows, which carry no `attribution_text`)
- [ ] Any `attribution-required` image has visible inline credit text in the corresponding SVG
- [ ] `metadata_dimensions` warnings surfaced when downloaded preview is much smaller than upstream-claimed size
- [ ] `Needs-Manual` rows include the failure reason
