> See [`image-base.md`](./image-base.md) for the common framework. Technical SVG/PPT constraints are in [`shared-standards-core.md`](./shared-standards-core.md).

# Image_Searcher Reference Manual

Role definition for the **web image acquisition path**: translate the active resource owner's intent into keyword queries, search openly-licensed providers, download a license-cleared image into `project/images/`, and record provenance + license metadata into `image_sources.json`.

**Trigger**: the Default Generate resource list contains `Acquire Via: web`, or Quick Generate has resolved a required web image in active context. Load only when at least one such resource exists.

---

## 1. License Tier Discipline

Every **provider-sourced** image is classified into one of two tiers; anything else is rejected outright. A third tier, `manual`, exists **only** for a directly selected replacement from [`--from-url`](#5-running-image_searchpy) or an adopted-page source package — it is never the result of a provider search accepting an unknown license.

| Tier | Licenses | On-slide attribution |
|---|---|---|
| `no-attribution` | CC0, Public Domain, Pexels License, Pixabay Content License | None |
| `attribution-required` | CC BY, CC BY-SA | Inline credit `<text>` on the slide |
| `manual` | Directly selected URL or adopted-page package image (license unverified) | None — verifying rights / any credit is the user's responsibility |

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
Multimodal Generate: explicit query variants × provider chain + allowed licenses
         → aggregate/deduplicate/rank → first 8 thumbnails → visually select
         → download one original; if none passes, inspect the next 8 first.
Non-visual / standalone best-only: explicit query variants × provider chain
         → strict metadata gate → first downloadable ranked original wins.
Strict:  provider chain, license filter = cc0,pdm,pexels,pixabay
         → apply the same selected execution mode without CC BY / CC BY-SA.
```

`--strict-no-attribution` is opt-in. Use it only when the deck cannot tolerate any on-slide credit (corporate template, full-bleed hero).

---

## 3. Providers

| Provider | Config | Strength |
|---|---|---|
| Pexels | recommended: `PEXELS_API_KEY` (free, [signup](https://www.pexels.com/api/)) | modern stock photography, people, workplace, lifestyle |
| Pixabay | recommended: `PIXABAY_API_KEY` (free, [signup](https://pixabay.com/api/docs/)) | broad type coverage including photos and illustrations |
| Openverse | zero-config | fallback aggregator: Wikimedia + Flickr + museums + rawpixel |
| Wikimedia Commons | zero-config | educational, scientific, geographic, historical |

Default chain (when `--provider` is unset):

`pexels` (when keyed) → `pixabay` (when keyed) → `openverse` → `wikimedia`.

Keyed providers without an API key are silently skipped — not an error.

**Default — keyed providers for broader stock coverage (may override when zero-config sources fit)**: Configure Pexels or Pixabay when their stock-photo coverage serves the brief. Their absence is not a validation failure; Openverse and Wikimedia remain valid zero-config acquisition paths.

---

## 4. Intent → Query Translation

Keep two layers distinct:

| Layer | Owner and grammar |
|---|---|
| Default Generate `design_spec.md §VIII Reference` | Strategist's complete visual intent: exact subject, desired view/mood, focal or quiet region, and crop-safety constraints. Positive quality cues are valid here. |
| Quick Generate active `Reference` | Current main agent's active-context intent after honoring explicit user assets, URLs, subjects, and constraints; unspecified choices are resolved automatically without confirmation. |
| `image_queries.json.items[].query` / positional query | Image_Searcher's concrete entity/identity keyword string. Start with the shortest phrase that preserves identity; keep exact multi-word names and necessary disambiguators even when they exceed four words. Omit mood, quality, composition, HEX, and negative wording. |

Web APIs match metadata, not semantic intent. Providers try each explicit query first, then progressively simplified four/three/two/one-word variants. A pipeline manifest should therefore use a concise primary `query` without pre-truncating exact names, plus `query_variants` for materially different official translations, spellings, aliases, or Chinese names. The tool aggregates and deduplicates their results; do not use variants for cosmetic word-order changes. For Chinese landmarks, pair the precise Chinese name used by Wikimedia with compact English identity terms used by stock providers.

Image_Searcher consumes the active Reference and never rewrites its owner. In Default Generate, that means no rewrite of `design_spec.md` or `spec_lock.md`; in Quick Generate, the active-context Reference remains fixed for the run. A candidate either satisfies that existing subject/focal/crop intent, or the role tries materially different query/provider/permitted-license strategies until no untried strategy remains, then marks `Needs-Manual`. Never loosen `required_terms`, the license policy, or the active intent to manufacture a match.

When the subject is an exact entity (landmark / person / company / product / venue), write `required_terms` at the same time you write the row's `query` and `query_variants`. Use one required group per identity anchor and `|` for aliases / translations, e.g. `["Chongqing|重庆", "Jiefangbei|解放碑|Liberation Monument"]`. This keeps provider queries short while preventing metadata-ranked wrong entities from being accepted automatically.

Do **not** loosen `required_terms` to generic category words just to improve coverage. Terms like `canyon`, `grand canyon`, `stone pillar`, `ground fissure`, `ancient town`, `bridge`, `temple`, or `village` belong in the search query, not as the only identity gate. For small / Chinese-local attractions, the correct failure mode is `Needs-Manual` or a user-provided `--from-url`, not a visually plausible image of the wrong place.

**Forbidden — web negative prompts**: `not tourist snapshot`, `no amateur photo`, `avoid low quality`.

> Note: Keyword APIs search negative words literally.

| §VIII Reference (intent) | Provider query |
|---|---|
| "Offshore wind farm at dusk, aerial view, quiet sky on the left for safe crop" | `offshore wind farm` |
| "Diverse engineering team around a laptop, modern office, natural light" | `engineering team laptop` |
| "Chongqing Jiefangbei monument, full structure visible, landscape frame" | `Chongqing Jiefangbei monument` |

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
| `--query-variant` | no | — | Repeatable official translation, spelling, alias, or materially different entity phrase; results are aggregated and deduplicated. Batch rows use `query_variants`. |
| `--filename` | yes | — | Output filename matching the resource list |
| `-o / --output` | no | `.` | Output directory; manifest defaults to `<output>/image_sources.json` |
| `--slide` | no | `""` | Slide ID from resource list (recorded in manifest) |
| `--purpose` | no | `""` | `background` / `hero` / `side` / `accent` |
| `--orientation` | no | `any` | `any` / `landscape` / `portrait` / `square` |
| `--min-width / --min-height` | no | `1200 / 800` | Actual downloaded-pixel floors; `--from-url` honors explicit lower overrides |
| `--provider` | no | (chain) | Pin one provider |
| `--strict-no-attribution` | no | off | Restrict to no-attribution licenses; refuse CC BY / CC BY-SA |
| `--require-terms` | no | — | Entity-safety gate for exact subjects. Repeatable; comma separates required groups; `A|B` means aliases within one group. Example: `--require-terms Chongqing --require-terms "Jiefangbei|Liberation Monument"` |
| `--manifest` | no | (default) | Override manifest path |
| `--save-candidates` | no | off | Thumbnail-selection mode: save one ranked page of review-eligible previews and `review_sheet.jpg`, but no original or provenance record. Multimodal Generate enables this; standalone CLI remains best-only by default |
| `--max-candidates` | no | `8` | Thumbnail page size. `0` explicitly requests the complete pool and is reserved for debugging / exceptional review, not normal Generate |
| `--candidate-page` | no | `1` | Ranked thumbnail page to fetch. Page 2 starts at rank 9 with the default page size. Batch rows may override with `candidate_page` |
| `--promote` | no | — | Download exactly one selected candidate original, enforce the request's size/readability gates, and write provenance |
| `--from-url` | no | — | Manual replace: download a directly selected image URL into `--filename` (recorded `license_tier: manual`); works without a multimodal model |

### Batch mode (≥ 2 web rows) — preferred

When more than one row is `Acquire Via: web`, do **not** call the CLI once per row. Write all rows into one `image_queries.json` and run a single concurrent batch — the web sister of `image_gen.py --manifest`:

```bash
python3 scripts/image_search.py --batch <project_path>/images/image_queries.json \
  -o <project_path>/images \
  --save-candidates
```

The candidate flag above is the normal Generate invocation when the current
agent can inspect images. It downloads previews only and moves each successful
row to `Needs-Selection`; no target image or `image_sources.json` entry exists
yet. A non-multimodal agent omits it and follows the handoff rules under
Suitability review below: only strict metadata-verified candidates may download
automatically. Standalone CLI use remains best-only unless the caller explicitly
requests thumbnail selection.

`image_queries.json` schema (one item per web row):

```json
{
  "items": [
    {
      "filename": "jiefangbei.jpg",
      "query": "Jiefangbei Chongqing downtown monument",
      "query_variants": ["Chongqing Liberation Monument", "重庆 解放碑"],
      "slide": "03_landmark",
      "purpose": "exact landmark photo",
      "orientation": "landscape",
      "required_terms": ["Chongqing", "Jiefangbei|Liberation Monument"],
      "status": "Pending"
    }
  ]
}
```

Required per item: `filename`, `query`, `status` (`Pending`). Optional per-item overrides: `query_variants`, `candidate_page`, `slide`, `purpose`, `orientation`, `provider`, `strict_no_attribution`, `min_width`, `min_height`, `required_terms`.

Use `required_terms` for **exact-entity images**: landmarks, people, companies, products, venues, named artworks, and named institutions. Each list item is required; alternatives inside one item use `|`. Example for a Chongqing landmark: `["Chongqing|重庆", "Jiefangbei|解放碑|Liberation Monument"]`. In best-only mode, candidates whose title / author / source URL do not satisfy every group are rejected before ranking, so a visually polished but wrong Rome / Hoi An image cannot win. Thumbnail mode may show a separately labeled near match only for visual identity verification; it never promotes automatically. Do **not** use `required_terms` for generic mood / background rows such as "modern city skyline" or "team collaboration".

For less-covered local attractions, keep the strict identity gate rather than progressively deleting location anchors or replacing proper names with category words. If strict metadata cannot prove the entity, mark the row `Needs-Manual` and use the manual URL path when the user supplies a confirmed source.

The runner first revalidates every `Sourced` row against its readable file, requested dimensions, and `image_sources.json` entry; drift returns that row to `Failed`. It then searches all `Pending` / `Failed` rows concurrently. Thumbnail mode writes `Needs-Selection`, `candidate_page`, `candidate_count`, `candidate_total`, `has_more_candidates`, `next_candidate_page`, and the relative `review_sheet` path without creating a target image or provenance. To inspect the next page for one row, set its `candidate_page` to `next_candidate_page`, reset only that row to `Pending`, and rerun the batch. Promoting one candidate with the same `--batch` manifest changes that row to `Sourced`. Provider failures remain retryable `Failed`, while clean provider/stage exhaustion becomes terminal `Needs-Manual`. Status is saved after each completion. A single `web` row may still use single-query mode above.

**Pacing**: free providers (Wikimedia/Openverse) are rate-sensitive, so batch concurrency defaults to a modest **3** (`--concurrency N`, or `IMAGE_SEARCH_CONCURRENCY` env). Use `--concurrency 1` to restore strict one-at-a-time pacing. Single-query mode is one request at a time by nature.

### Ranking model

`image_search.py` ranks provider metadata, not pixels. The order is deliberately conservative:

1. common hard reject: invalid license or zero query relevance;
2. strict automatic gate: best-only mode rejects every candidate missing any `required_terms`; this is the only pool available without visual review;
3. visual-review widening: thumbnail mode keeps strict matches first, then may admit a near match only when exactly one required group is absent and the explicit query that found it still has strong metadata relevance. The sidecar marks it `identity_evidence: visual-verification-required`; visual inspection must establish the missing identity before promotion;
4. identity priority: metadata-verified candidates whose title contains the required entity terms outrank candidates that match only via URL;
5. query relevance: concrete query tokens match whole ASCII metadata tokens and dominate generic visual words like "photo", "high quality", "background"; substrings such as `office` inside `officer` do not count;
6. layout fit: requested orientation helps; mismatched orientation is a small penalty, not a hard reject;
7. license / size tie-breakers: no-attribution is a small bonus; pixel count is capped so a huge but weakly relevant image cannot outrank a smaller accurate image.

Do not tune this into a visual taste engine. The scorer removes obvious metadata failures and orders the thumbnail sheet; visual review still decides whether any candidate fits the slide.

### Suitability review — with or without a multimodal model

A metadata-ranked top hit is *downloadable and token-relevant*, not necessarily *visually suitable* — `score_candidate` never sees pixels. Review it against the active Reference and Crop Policy before it is trusted:

- **Multimodal review available**: run `--save-candidates`. The tool aggregates explicit query variants, deduplicates them, and saves at most the first **8** ranked previews under `candidates/<stem>/review/`; `review_sheet.jpg` contains only that page and no original is downloaded. Run [`web-image-review.md`](../workflows/stages/web-image-review.md): use one isolated vision reviewer for the current batch when available, otherwise review locally. Only the active image owner may use the returned candidate filename with `--promote`. If `has_more_candidates` is true and none passes, fetch `--candidate-page 2` before changing the query.
- **Non-multimodal model (no vision)**: omit `--save-candidates`; the tool excludes every `visual-verification-required` near match, downloads only the first candidate that passes all strict metadata / license / dimension gates, and records `selection_method: metadata-ranked`. Do **not** describe this as visual confirmation. If no strict candidate exists, or the active Reference requires a viewpoint, crop, expression, or fine identity detail that metadata cannot establish, mark the row `Needs-Manual`; Quick does not open an acquisition-time interaction.

The review stage owns pixel-inspection gates, bounded detail reads, and the compact decision receipt. It receives only the locked row intent plus candidate sidecars/sheets; it never receives the full planning or acquisition context.

If no thumbnail on the current page passes, download no original. When
`has_more_candidates` is true, advance to `next_candidate_page` first. Only
after the ranked pool is exhausted should you change the query materially —
identity wording, translation, alias, viewpoint, or necessary disambiguator —
reset that row to `Pending`, and generate a fresh pool. Do not promote the
least-bad candidate.

For exact-entity rows, suitability has two gates: `required_terms` first enforces metadata identity, then the `.review` image confirms the pixels actually show the right subject and satisfy the active focal/crop intent. Passing metadata never authorizes changing that intent downstream.

Never treat a generic `required_terms` pass as acceptance. For example, matching `Ground Fissure` can return an unrelated transit station named Yunlong, and matching `stone pillar` can return a different scenic area. If the proper name / geography cannot be retained, stop at `Needs-Manual`.

**Replacement ladder when the first round is not right**:

1. With vision, promote the one passing thumbnail selected under the review-stage contract; this is the first original-image request.
2. If none passes and `has_more_candidates` is true, fetch the next ranked page (8 by default). Candidate numbers continue globally, so page 2 starts at `candidate_09`; do not repeat page 1 or download an original.
3. After the current pool is exhausted, add materially different query variants for identity wording, official translation, alias, viewpoint, or disambiguation and generate a fresh pool; do not repeat a semantically exhausted query.
4. With vision only, if normal search is exhausted, select one relevant adopted `source_url` and follow [`topic-research`](../workflows/stages/topic-research.md) § Hand-off to fetch its Markdown + companion-image source package. Review that package, copy only one passing image into `<project>/images/`, and reconcile the query row plus `image_sources.json` from the selected `image_manifest.json` entry with `license_tier: manual`. Fetch another page only when the current package has no passing image; never auto-expand facts URLs or promote the whole package.
5. **manual URL replace (universal, model-agnostic)** — use a directly selected URL and swap it in:
   ```bash
   python3 scripts/image_search.py --from-url <image-url> --filename <name>.jpg -o <project_path>/images
   ```
   Recorded with `license_tier: manual` — verifying usage rights is the user's
   call. In Quick Generate, use this step only when the URL was already
   supplied; never pause to request one. The command updates the image and
   `image_sources.json` but does **not** rewrite `image_queries.json`. Validate
   the downloaded file and matching manual-provenance entry, then reconcile
   that query row and the active roster to `Sourced` before export; a stale
   `Needs-Manual` status remains blocking
   ([`executor-web-image.md`](./executor-web-image.md) §1);
6. When the query variants, ranked pages, configured provider chain, permitted license stages, and eligible adopted-page package fallback are exhausted, mark the row `Needs-Manual`.

**This review never opens an acquisition-time interaction** ([`image-base.md`](./image-base.md) §6). Default Generate may build a placeholder and continue to Step 6. Quick Generate finishes all permitted automated strategies, records `Needs-Manual`, and blocks direct export when the unresolved image is required.

### Visual selection candidates (multimodal Generate; standalone opt-in)

Candidate-thumbnail saving stays **off by default for standalone CLI use**.
Generate enables it for every web row when the current agent can inspect images,
so the first pass sees a bounded ranked page rather than trusting metadata rank
1 or flooding the reviewer with the complete pool.

```bash
python3 scripts/image_search.py "<query>" --filename <name>.jpg -o <project_path>/images \
  --save-candidates
```

Saves provider previews to `images/candidates/<stem>/review/` with a
thumbnail-only `candidates.json` manifest and an automatically generated
`candidates/<stem>/review_sheet.jpg` containing only the current round. The
default first round is ranks 1–8. The sidecar records `candidate_page`,
`page_size`, `candidate_total`, `has_more_candidates`, each candidate's matched
query, and whether identity is metadata-verified or requires visual
verification. The target filename and `image_sources.json` remain untouched.
Inspect the sheet first, open only plausible individual previews when needed,
then promote the best fit — only that full-resolution original is downloaded
to the target:

```bash
python3 scripts/image_search.py --promote candidate_03.jpg --filename <name>.jpg -o <project_path>/images

# No pass on page 1, but candidates.json says has_more_candidates: true
python3 scripts/image_search.py "<same query>" --filename <name>.jpg \
  -o <project_path>/images --save-candidates --candidate-page 2

# Batch flow: also reconcile image_queries.json from Needs-Selection to Sourced
python3 scripts/image_search.py --promote candidate_03.jpg --filename <name>.jpg \
  --batch <project_path>/images/image_queries.json -o <project_path>/images
```

For batch continuation, set only the no-pass row's `candidate_page` to its
`next_candidate_page`, reset that row to `Pending`, and rerun. Use
`--max-candidates 0` only when a complete-pool dump is explicitly useful for
debugging; it is not the Generate default.

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
      "matched_query": "leadership team boardroom",
      "selection_method": "metadata-ranked",
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
| `matched_query` | Explicit primary query or query variant that discovered the selected asset. |
| `selection_method` | `visual-thumbnail` after promotion from a reviewed preview, or `metadata-ranked` for the strict no-vision / best-only path. It never claims a visual check that did not occur. |
| `width` / `height` | Measured from the file actually saved to disk. Use these for layout. |
| `metadata_dimensions` | Present only when upstream-claimed size differs from the saved file (preview vs original). Informational only. |
| `license_tier` | Drives Executor's attribution decision: `no-attribution` / `attribution-required` for provider-sourced images, or `manual` for a directly selected URL/source-package replacement (embed only; rights/credit are the user's responsibility). |
| `attribution_required` | Boolean alias of `license_tier == "attribution-required"`. |
| `attribution_text` | Canonical credit source. Preserve its author/provider/license facts; compress only through §7's visual grammar rather than inventing or dropping identity. |
| `stage` | `all` by default, or `no-attribution-only` when strict mode is used. |

> Manifest is **idempotent on `filename`** and written atomically. Rerunning replaces that entry while preserving all others. An existing unreadable/non-object manifest blocks the write instead of being overwritten as fresh state.

---

## 7. On-Slide Attribution Contract

Applied by Executor when an image's `license_tier == "attribution-required"`.

**Hard rule — legal content and binding**: Every slide that uses the asset carries a visible, readable credit bound unambiguously to that asset. Preserve its author, source/provider, and CC BY / CC BY-SA license facts from `attribution_text`; do not invent, merge away, or drop identity.

**Reference — visual treatment is not a constraint**: Position, size, color, line structure, per-image versus combined credits, labels, and contrast treatment belong to the page composition. Use any treatment that stays readable and preserves the asset-to-credit binding; a scrim or gradient is optional, not required.

**Reference — attribution treatments, not constraints**:

| Page situation | Possible treatment |
|---|---|
| One credited image | Place a compact credit near the image edge or in a page footnote area |
| Several credited images | Use per-image credits or one combined source line with labels when needed for unambiguous mapping |
| Hero / full-bleed image | Place the credit in an available quiet region; add a scrim or gradient only when contrast otherwise fails |

Use `attribution_text` from the manifest as the **starting point**. Compress when the chosen page treatment needs a shorter line, without dropping the required facts:

| Manifest | Slide credit |
|---|---|
| `team.jpg — "Untitled" via Openverse — license: CC0 (...)` | `via Openverse / CC0` |
| `team.jpg — "Sunset" by Jane Doe via Wikimedia Commons — license: CC BY-SA 4.0 (...)` | `© Jane Doe / Wikimedia / CC BY-SA 4.0` |

---

## 8. Failure Handling (web-specific)

Extends [`image-base.md`](./image-base.md) §6.

| Situation | Behavior |
|---|---|
| No candidates from any provider in either stage | Mark row `Needs-Manual`. Suggest a more precise query or another configured provider; rerun without `--strict-no-attribution` only when the confirmed page may carry visible credit. |
| Current thumbnail page has no acceptable image and `has_more_candidates` is true | Fetch `next_candidate_page`; do not change the query or download an original yet. |
| Requested thumbnail page is past `candidate_total` | Treat the current pool as exhausted; add a materially different query variant or move to the manual boundary. |
| One or more previews fail while another qualified preview succeeds | Keep the successful thumbnail set; no original has been requested. |
| Every qualified preview fails | Mark row `Failed`; a later batch run retries it. |
| Selected original fails its download/readability/dimension gate | Leave `Needs-Selection`; select another passing thumbnail or materially change the query. Do not commit provenance. |
| Best-only candidate fails to download (HTTP 403/404) | Dispatcher auto-falls through to the next ranked candidate. |
| Provider/network failure remains after dispatch | Mark row `Failed`; a later batch run retries it. |
| Keyed provider has no API key | Silently skipped. Not an error. |

CLI exit: a successfully prepared `Needs-Selection` thumbnail set returns `0`
as an intermediate success; `Failed` or `Needs-Manual` returns `1`.

---

## 9. Handoff with the Intent Owner

Reference field is **intent description**, not a query. See [`image-base.md`](./image-base.md) §8 for the rule.

Keep it intact as the acceptance contract. In Default Generate the owner is Strategist; in Quick Generate it is the current main agent's active-context resource decision. Derive a separate concise provider query that preserves exact names and necessary disambiguation; do not pass the Reference verbatim or rewrite it after search.

---

## 10. Handoff with Executor

Executor reads `image_sources.json` per slide that uses a Sourced image. For each entry:

| `license_tier` | Slide-level action |
|---|---|
| `no-attribution` | Embed `<image>` only |
| `attribution-required` | Embed `<image>` **and** an inline credit element per §7 |
| `manual` | Embed `<image>` only — directly selected URL or adopted-page package image; verifying usage rights / any required credit is the user's responsibility |

Executor does not interpret raw license strings — `license_tier` is sufficient.

`svg_quality_checker.py` verifies this handoff before post-processing: a referenced attribution-required image needs its own visible author + CC BY / CC BY-SA credit; one generic deck-level CC token cannot satisfy several images.

---

## 11. Task Completion Checkpoint

In addition to the shared checkpoint in [`image-base.md`](./image-base.md) §10:

- [ ] Every required web row is `Sourced` with a downloaded original at `project/images/<filename>` OR is marked `Needs-Manual`; `Needs-Selection` remains incomplete
- [ ] Each multimodal `Sourced` web image was selected from a bounded ranked thumbnail page and only its winner original was downloaded; a no-pass page advanced through remaining pages before query replacement. Without vision, only strict metadata candidates may become `Sourced`, with `selection_method: metadata-ranked`; unresolved or visually unprovable intent becomes `Needs-Manual` without pretending a visual check occurred
- [ ] Each `Sourced` row has a manifest entry with valid `license_tier` and non-empty `attribution_text` (except `manual` directly selected rows, which carry no `attribution_text`)
- [ ] Any `attribution-required` image has visible author + license credit in every SVG that references it
- [ ] `metadata_dimensions` warnings surfaced when downloaded preview is much smaller than upstream-claimed size
- [ ] `Needs-Manual` rows include the failure reason
