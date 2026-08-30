> See [`image-base.md`](./image-base.md) for the common framework. Technical SVG/PPT constraints are in [`shared-standards-core.md`](./shared-standards-core.md).

# Image_Searcher Reference Manual

Role definition for the **web image acquisition path**: translate the resource owner's intent into keyword queries, search openly-licensed providers, download one license-cleared image into `project/images/`, and record provenance and license in `image_sources.json`.

**Trigger**: the Default resource list contains `Acquire Via: web`, or Quick has resolved a required web image in active context.

---

## 1. License Tier Discipline

Every provider-sourced image lands in one of two tiers; everything else is rejected. `manual` exists only for a directly selected `--from-url` replacement or an adopted-page package image — never for a provider result with an unknown license. Downstream consumers read `license_tier` alone and never interpret raw license strings.

| Tier | Licenses | On-slide attribution |
|---|---|---|
| `no-attribution` | CC0, Public Domain, Pexels License, Pixabay Content License | None |
| `attribution-required` | CC BY, CC BY-SA | Inline credit `<text>` on the slide |
| `manual` | Directly selected URL or adopted-page image, license unverified | None — rights and any credit are the user's responsibility |

**Forbidden — auto-rejected**: CC BY-NC, CC BY-NC-SA, CC BY-ND, CC BY-NC-ND, All Rights Reserved, unknown or missing license.

---

## 2. Search Strategy

Quality first across all allowed tiers — never prefer CC0 over a better CC BY image; the manifest's `license_tier` lets Executor add credit only when needed. `--strict-no-attribution` (CC0 / PD / Pexels / Pixabay only) is opt-in for decks that cannot carry any on-slide credit.

```
Multimodal Generate: explicit query variants × provider chain + allowed licenses
         → aggregate/deduplicate/rank → first 8 thumbnails → visually select
         → download one original; if none passes, inspect the next 8 first.
Non-visual / standalone best-only: explicit query variants × provider chain
         → strict metadata gate → first downloadable ranked original wins.
```

---

## 3. Providers

| Provider | Config | Strength |
|---|---|---|
| Pexels | `PEXELS_API_KEY` (free, [signup](https://www.pexels.com/api/)) | modern stock photography, people, workplace, lifestyle |
| Pixabay | `PIXABAY_API_KEY` (free, [signup](https://pixabay.com/api/docs/)) | broad coverage including illustrations; its API serves at most a 1280 px long edge, so prefer Wikimedia or Pexels for full-bleed heroes |
| Openverse | zero-config | fallback aggregator: Wikimedia + Flickr + museums + rawpixel |
| Wikimedia Commons | zero-config | educational, scientific, geographic, historical; pin `provider: wikimedia` for murals, manuscripts, artworks, and museum objects, which stock providers tag with tourist snapshots |

Default chain: `pexels` → `pixabay` (each when keyed) → `openverse` → `wikimedia`; a keyed provider without a key is silently skipped. Configure Pexels or Pixabay when stock coverage serves the brief; their absence is never a failure.

---

## 4. Intent → Query Translation

| Layer | Owner and grammar |
|---|---|
| Default `design_spec.md §VIII Reference` / Quick active `Reference` | The owner's complete visual intent — exact subject, view/mood, focal or quiet region, crop safety, positive quality cues — fixed for the run and never rewritten by this role |
| `image_queries.json.items[].query` / positional query | This role's concrete entity keyword string: the shortest phrase that preserves identity, keeping exact multi-word names and disambiguators even beyond four words; no mood, quality, composition, HEX, or negative wording |

Web APIs match metadata, not intent: providers try each explicit query, then progressively simplified four/three/two/one-word variants, so keep a concise primary `query` plus `query_variants` for materially different official translations, spellings, aliases, or Chinese names (never cosmetic word-order changes); for Chinese landmarks pair the Wikimedia Chinese name with compact English identity terms. A candidate either satisfies the existing intent or the role tries materially different query/provider/license strategies until none remain, then marks `Needs-Manual`; never loosen `required_terms`, the license policy, or the intent to manufacture a match.

**Hard rule — `required_terms` for exact entities** (landmarks, people, companies, products, venues, named artworks and institutions): write them with the query — one group per identity anchor, `|` for aliases, e.g. `["Chongqing|重庆", "Jiefangbei|解放碑|Liberation Monument"]`. Never loosen them to category words (`canyon`, `stone pillar`, `ancient town`, `bridge`, `temple`); those belong in the query, and a small or local attraction that metadata cannot prove ends in `Needs-Manual` or a user `--from-url`, never a plausible image of the wrong place. Never use them for generic mood rows ("modern city skyline", "team collaboration"). **Forbidden — negative words** (`not tourist snapshot`, `no amateur photo`): keyword APIs search them literally.

| §VIII Reference (intent) | Provider query |
|---|---|
| "Offshore wind farm at dusk, aerial view, quiet sky on the left for safe crop" | `offshore wind farm` |
| "Diverse engineering team around a laptop, modern office, natural light" | `engineering team laptop` |
| "Chongqing Jiefangbei monument, full structure visible, landscape frame" | `Chongqing Jiefangbei monument` |

---

## 5. Running `image_search.py`

```bash
python3 scripts/image_search.py "<query>" --filename <name>.jpg --slide <slide_id> \
  --orientation landscape --purpose background -o <project_path>/images
```

| Parameter | Default | Description |
|---|---|---|
| `query` (positional, required) | — | Simplified internally |
| `--query-variant` | — | Repeatable alias/translation; batch rows use `query_variants` |
| `--filename` (required) | — | Output filename matching the resource list |
| `-o / --output` | `.` | Output directory; manifest defaults to `<output>/image_sources.json` |
| `--slide`, `--purpose`, `--orientation` | `""`, `""`, `any` | Recorded slide id; `background` / `hero` / `side` / `accent`; `landscape` / `portrait` / `square` |
| `--min-width / --min-height` | `1200 / 800` | Downloaded-pixel floors; `--from-url` honors explicit lower overrides |
| `--provider` | chain | Pin one provider |
| `--strict-no-attribution` | off | Refuse CC BY / CC BY-SA |
| `--require-terms` | — | Repeatable identity gate; comma separates groups, `A|B` aliases |
| `--save-candidates` | off | Thumbnail mode: one ranked page of previews plus `review_sheet.jpg`, no original |
| `--max-candidates` | `8` | Page size; `0` = complete pool, debugging only |
| `--candidate-page` | `1` | Ranked page; page 2 starts at rank 9 |
| `--promote <candidate>` | — | Download exactly one selected original, enforce gates, write provenance |
| `--from-url <url>` | — | Manual replacement recorded as `license_tier: manual`; works without vision |
| `--manifest <path>` | `images/image_queries.json` | Override the manifest path |

**Batch mode (≥2 web rows) — preferred**: write every row into `image_queries.json` and run one concurrent batch (the web sister of `image_gen.py --manifest`); add `--save-candidates` whenever the agent can inspect images:

```bash
python3 scripts/image_search.py --batch <project_path>/images/image_queries.json -o <project_path>/images --save-candidates
```

```json
{ "items": [ {
  "filename": "jiefangbei.jpg",
  "query": "Jiefangbei Chongqing downtown monument",
  "query_variants": ["Chongqing Liberation Monument", "重庆 解放碑"],
  "slide": "03_landmark", "purpose": "exact landmark photo", "orientation": "landscape",
  "required_terms": ["Chongqing", "Jiefangbei|Liberation Monument"],
  "status": "Pending"
} ] }
```

Required per item: `filename`, `query`, `status`; optional: `query_variants`, `candidate_page`, `slide`, `purpose`, `orientation`, `provider`, `strict_no_attribution`, `min_width`, `min_height`, `required_terms`. The runner revalidates every `Sourced` row against its file, dimensions, and manifest entry (drift → `Failed`), then searches all `Pending` / `Failed` rows concurrently (default concurrency 3, `--concurrency N` or `IMAGE_SEARCH_CONCURRENCY`; `1` for strict pacing on rate-sensitive free providers). Thumbnail mode writes `Needs-Selection` with `candidate_page`, `candidate_count`, `candidate_total`, `has_more_candidates`, `next_candidate_page`, and the `review_sheet` path, creating no image or provenance; to see the next page for one row set its `candidate_page` to `next_candidate_page`, reset only that row to `Pending`, and rerun. Promoting with the same `--batch` manifest moves the row to `Sourced`. Provider failures stay retryable `Failed`; clean exhaustion becomes `Needs-Manual`; status is saved after each completion.

**Ranking** orders provider metadata, never pixels, and must not be tuned into a taste engine: hard-reject invalid licenses and zero relevance; in best-only mode reject any candidate missing a `required_terms` group; in thumbnail mode keep strict matches first and admit a near match only when exactly one group is missing and the finding query still has strong relevance (marked `identity_evidence: visual-verification-required`, never auto-promoted); then metadata-verified identity in the title outranks a URL-only match; concrete query tokens match whole ASCII tokens (`office` ≠ `officer`) and dominate generic words; orientation is a small penalty, no-attribution a small bonus, pixel count capped so a huge weak match cannot beat a smaller accurate one.

**Suitability review** — a top hit is downloadable and token-relevant, not visually suitable (the reviewer receives only the locked row intent plus candidate sidecars/sheets, never the full planning or acquisition context):

- **With vision**: `--save-candidates` saves at most the first 8 ranked previews under `candidates/<stem>/review/` and the sheet; run [`web-image-review.md`](../workflows/stages/web-image-review.md) — one isolated reviewer for the batch when available, otherwise local review — then only the image owner promotes the returned filename. Never promote the least-bad candidate; if none passes and `has_more_candidates` is true, fetch `--candidate-page 2` before changing the query. For exact entities, `required_terms` gates metadata and the review image confirms the pixels show the subject and satisfy the focal/crop intent; a generic `required_terms` pass is not acceptance (matching `Ground Fissure` can return an unrelated station named Yunlong).
- **Without vision**: omit `--save-candidates`; the tool excludes near matches, downloads only the first candidate passing every strict metadata, license, and dimension gate, and records `selection_method: metadata-ranked` — never described as visual confirmation. With no strict candidate, or an intent that needs a viewpoint, crop, expression, or fine identity metadata cannot establish, mark `Needs-Manual`; Quick opens no interaction.

**Replacement ladder**: (1) with vision, promote the one passing thumbnail; (2) with `has_more_candidates`, fetch the next page (numbering continues globally — page 2 starts at `candidate_09`); (3) after the pool is exhausted, add materially different identity/translation/alias/viewpoint/disambiguation variants and generate a fresh pool; (4) with vision only, after normal search is exhausted, fetch one adopted `source_url` as a Markdown + companion-image package under [`topic-research`](../workflows/stages/topic-research.md) § Hand-off, copy one passing image into `images/`, and reconcile the row and `image_sources.json` from its `image_manifest.json` entry with `license_tier: manual` (never auto-expand facts URLs or promote the whole package); (5) manual URL replace — `python3 scripts/image_search.py --from-url <image-url> --filename <name>.jpg -o <project_path>/images` — recorded `manual`, only with a URL already supplied in Quick; it updates the image and `image_sources.json` but not `image_queries.json`, so validate the file and reconcile the query row and roster to `Sourced` before export ([`executor-web-image.md`](./executor-web-image.md) §1); (6) when variants, pages, providers, license stages, and the package fallback are exhausted, mark `Needs-Manual`. This review never opens an acquisition-time interaction ([`image-base.md`](./image-base.md) §3): Default may continue to Step 6 with a placeholder; Quick blocks direct export when the image is required.

**Standalone thumbnail selection** (opt-in outside Generate):

```bash
python3 scripts/image_search.py "<query>" --filename <name>.jpg -o <project_path>/images --save-candidates
python3 scripts/image_search.py --promote candidate_03.jpg --filename <name>.jpg -o <project_path>/images
python3 scripts/image_search.py "<same query>" --filename <name>.jpg -o <project_path>/images --save-candidates --candidate-page 2
python3 scripts/image_search.py --promote candidate_03.jpg --filename <name>.jpg --batch <project_path>/images/image_queries.json -o <project_path>/images
```

Previews land in `images/candidates/<stem>/review/` with a thumbnail-only `candidates.json` (page, size, total, `has_more_candidates`, matched query, identity evidence) and `review_sheet.jpg` for the current round; the target and manifest stay untouched until promotion.

---

## 6. Manifest Format (`image_sources.json`)

Each successful download appends or replaces one entry keyed on `filename`; the file is written atomically and is idempotent, and an unreadable existing manifest blocks the write.

```json
{
  "license_verification": "provider metadata used; manual review recommended for external delivery",
  "generated_at": "2026-05-01T12:17:59.856275Z",
  "items": [ {
    "filename": "team.jpg", "slide": "03_team", "purpose": "Leadership photo",
    "search_query": "executive boardroom meeting", "matched_query": "leadership team boardroom",
    "selection_method": "metadata-ranked", "orientation": "landscape",
    "provider": "openverse", "stage": "all",
    "title": "Untitled", "author": "",
    "source_page_url": "https://www.rawpixel.com/...", "download_url": "https://...",
    "license_name": "CC0", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
    "license_tier": "no-attribution", "attribution_required": false,
    "width": 1024, "height": 683,
    "metadata_dimensions": { "width": 4800, "height": 3200, "note": "upstream-reported size; actual downloaded file is smaller (likely a preview)" },
    "attribution_text": "team.jpg — \"Untitled\" via Openverse — license: CC0 (...)",
    "status": "sourced"
  } ]
}
```

`matched_query` is the query or variant that found the asset; `selection_method` is `visual-thumbnail` after a reviewed promotion or `metadata-ranked` for the strict path; `width` / `height` are measured from the saved file (use them for layout) while `metadata_dimensions` appears only when the upstream claim differs; `license_tier` drives Executor's attribution; `attribution_text` is the canonical credit source, compressed only through §7's grammar; `stage` is `all` or `no-attribution-only`.

---

## 7. On-Slide Attribution Contract

For `license_tier: attribution-required`, every slide using the asset carries a visible, readable credit bound unambiguously to it, preserving author, source/provider, and CC BY / CC BY-SA facts from `attribution_text`. Position, size, color, per-image versus combined credits, labels, and contrast treatment belong to the page — a compact credit near the image edge or footnote area for one image, per-image credits or one labeled combined line for several, a quiet region (a scrim or gradient only when contrast fails) on a hero. Compress without dropping required facts: `team.jpg — "Untitled" via Openverse — license: CC0 (...)` → `via Openverse / CC0`; `team.jpg — "Sunset" by Jane Doe via Wikimedia Commons — license: CC BY-SA 4.0 (...)` → `© Jane Doe / Wikimedia / CC BY-SA 4.0`.

---

## 8. Failure Handling (web-specific)

Extends [`image-base.md`](./image-base.md) §3. No candidates from any provider or stage → `Needs-Manual` (suggest a more precise query or another provider; rerun without `--strict-no-attribution` only when the page may carry credit). No acceptable image on the current page with `has_more_candidates` → fetch `next_candidate_page` without changing the query or downloading. A page past `candidate_total` → pool exhausted, add a variant or move to the manual boundary. Some previews fail while another qualifies → keep the set. Every preview fails, or a provider/network failure remains → `Failed`, retried by a later batch. A promoted original fails its download/readability/dimension gate → stay `Needs-Selection` and select another or change the query. A best-only download 403/404 → the dispatcher falls to the next ranked candidate. A keyed provider without a key → skipped. CLI exit: a prepared `Needs-Selection` set returns `0`; `Failed` or `Needs-Manual` returns `1`.

---

## 9. Handoff with the Intent Owner

`Reference` is intent, not a query ([`image-base.md`](./image-base.md) §1): keep it intact as the acceptance contract, derive a separate concise provider query that preserves exact names and disambiguation, and never pass it verbatim or rewrite it after search.

## 10. Handoff with Executor

Executor reads `image_sources.json` per slide and acts on `license_tier` — `no-attribution` and `manual` embed the `<image>` only, `attribution-required` adds the §7 credit — without interpreting license strings. `svg_quality_checker.py` verifies that every referenced attribution-required image has its own visible author + license credit; one deck-level CC token never covers several images.

## 11. Task Completion Checkpoint

Beyond [`image-base.md`](./image-base.md) §4: every required web row is `Sourced` with its original at `project/images/<filename>` or `Needs-Manual` with a reason (`Needs-Selection` is incomplete); each multimodal `Sourced` image came from a bounded thumbnail page whose winner alone was downloaded, with remaining pages exhausted before any query change; without vision only strict metadata candidates became `Sourced` with `selection_method: metadata-ranked`; each `Sourced` row has a valid `license_tier` and non-empty `attribution_text` (except `manual`); every attribution-required image has its credit in every referencing SVG; `metadata_dimensions` warnings were surfaced when the download was far smaller than claimed.
