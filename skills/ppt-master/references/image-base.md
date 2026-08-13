> See [`image-generator.md`](./image-generator.md) and [`image-searcher.md`](./image-searcher.md) for path-specific behavior.

# Image Acquisition and Preparation Common Reference

Shared baseline for both acquisition paths. Path-specific behavior lives in the path's own reference.

---

## 1. Trigger Condition

Active when at least one resource row has `Acquire Via: ai` / `web` / `slice`, or when any §VIII / Quick active-context resource is a pending prepared derivative. Canonical rows with `user` / `placeholder` are tracked but skipped by acquisition roles.

| Mode | Trigger |
|---|---|
| Default Generate | `generate-ppt` workflow, `design_spec.md §VIII` image rows present |
| Quick Generate | [`quick-generate`](../workflows/profiles/quick-generate.md) is active and the current main agent has resolved one or more required images in active context |
| Standalone | Direct request against an existing project |

---

## 2. Image Resource List Format

Default Generate uses Strategist-owned `design_spec.md §VIII` plus its lock projection. Quick Generate substitutes active-context resource decisions plus required operational manifests; it creates no planning artifact or general resource roster. Status enum: [`svg-image-embedding.md`](svg-image-embedding.md).

| Filename | Dimensions | Purpose / Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference |
|---|---|---|---|---|---|---|---|
| `<planned file>` | `<planned size>` | `<planned role>` | `<owner-resolved recommendation>` | `adaptive` / `no-crop` | `ai` / `web` / `slice` | Pending | `<acquisition brief>` |

**Required per non-skipped row**: `Acquire Via` and `Status`. `Reference` is required for every `web` / `slice` row, every newly authored `ai` row, and every prepared derivative regardless of source class. An existing `ai` row whose `Reference` is omitted or blank may continue only through the declared inference in [`image-generator.md`](./image-generator.md) §8; no other path may infer it.

**Quick Generate ownership**: explicit user assets, URLs, and path instructions win. Otherwise the main agent chooses required `user` / `ai` / `web` / `slice` rows and AI path `auto`, without interaction.

**Mandatory — consume the resolved path**: Default consumes Strategist-chosen §VIII rows; Quick resolves once in active context before preparation. This phase never adds or reselects a treatment:

| Path | Behavior |
|---|---|
| `none` | Use the canonical bitmap unchanged |
| `native` | No new file; SVG owns crop/clip, transform, opacity, frame/shadow/scrim/vignette, and overlap |
| `prepared derivative` | Separate file only for pixel blur, desaturation/grayscale, duotone, brightness/contrast, or existing cutout/registered-layer preparation |

Choosing `none` is valid. Never bake a native treatment into a derivative.

**Reference — exact pattern mapping, not activation**: An adopted pattern may use this mapping; its id alone creates nothing.

| Pattern | Preparation |
|---|---|
| `P*`, `M*`, `C*` | Use existing assets with native SVG/PPT composition; no automatic derivative |
| `A1-02` / `A1-03` | `image_treat.py` blur / duotone |
| `A1-01` / `A1-04` | Existing prepared composite or host/AI path; `image_treat.py` does not blend |
| `A2-01` | Existing/host-prepared RGBA or flat-key AI/slice asset; when source-scene registration is required, use `A2-02` / `A2-03` + [`image-generator.md`](./image-generator.md) §4.4 |
| `A2-02` / `A2-03` | [`image-generator.md`](./image-generator.md) §4.4 registered layers |
| `A3-01` | Original/subject plus registered `image_treat.py` blur/tone/desaturate derivative |
| `A3-02` | Registered full-canvas `image_treat.py` blur derivative; crop panels natively |
| `A3-03` | `image_treat.py` desaturated base plus existing/§4.4 color subject layer |

---

## 3. Path Dispatch

Classify `Reference: Derived from <canonical bare filename>; treatment=<operation>; ...` before `Acquire Via`. Its distinct, non-derived parent must be `user`, `web`, `ai`, or `slice`; reject placeholder parents, chains, cycles, and self-reference. For each Pending row:

| Row kind / Acquire Via | Load reference | Run | Success status |
|---|---|---|---|
| Deterministic prepared derivative | This common reference | After parent is usable, run `image_treat.py` to a distinct `.png`; preserve source | Inherit parent: `user → Existing`, `web → Sourced`, `ai/slice → Generated` |
| Registered-layer derivative | [`image-generator.md`](./image-generator.md) §4.4 | After parent is usable, run §4.4 | Supplied final: `user → Existing`; generated/reconstructed: `ai → Generated` |
| `ai` | [`image-generator.md`](./image-generator.md) | `image_gen.py` | `Generated` |
| `web` | [`image-searcher.md`](./image-searcher.md) | `image_search.py` | `Sourced` |
| `slice` | [`image-generator.md`](./image-generator.md) §4.3 | `slice_images.py` after parent AI sheet is `Generated` | `Generated` |
| `user` | — | — | (already `Existing`) |
| `placeholder` | — | — | (already `Placeholder`) |

> Lazy load: an all-`web` deck never reads `image-generator.md`, and vice versa.

---

## 4. Analysis Phase

1. Read the Default Design Spec/lock, or reuse Quick's active-context resource/page decisions.
2. Separate derivatives before grouping canonical rows by `Acquire Via`; ensure `project/images/` exists.
3. Finish user and triggered ai/web/slice canonical preparation.
4. Materialize only declared derivatives from usable parents, preserve originals, then run `analyze_images.py` once before SVG.

---

## 5. Verification Phase

After all rows reach terminal status:

- Every non-skipped row has a file at `project/images/<filename>`, or is marked `Needs-Manual`
- Each derivative has its distinct file and usable parent; web provenance is copied in `image_sources.json`
- Every `slice` row has a generated element file, or is marked `Needs-Manual` because its parent sheet is not available
- No `Pending` or `Failed` rows remain
- `image_prompts.json` exists when ≥1 ai row processed; every entry has `status ∈ {Generated, Needs-Manual}` (no `Pending` or `Failed` remaining)
- `image_sources.json` exists when ≥1 web row processed; every entry has `license_tier ∈ {no-attribution, attribution-required, manual}` (`manual` = a user-supplied `--from-url` replacement)

> `Needs-Manual` is terminal for acquisition, not export readiness. A later
> supplied/replaced file must be validated and its row reconciled to
> `Existing`, `Generated`, or `Sourced` with matching evidence.
> Quick blocks every required row that still says `Needs-Manual`, regardless of
> whether an unverified candidate file happens to exist. See
> [`image-generator.md`](./image-generator.md) §7.

---

## 6. Failure Handling

**Hard rule — automatic exhaustion before blocking**: acquisition failures MUST NOT open an interactive choice or stop while an untried permitted strategy remains.

1. Run the selected path's initial strategy
2. On recoverable failure (network, no candidates, license rejection, rate limit), continue through materially different strategies that remain inside that path's confirmed permissions; never loop an already exhausted strategy
3. When the path-specific query/provider/license-stage or backend/retry strategy is exhausted, set `Status: Needs-Manual`, log the reason in conversation, and continue
4. After the phase completes, summarize all `Needs-Manual` rows for the user — list filenames, where prompts live (`images/image_prompts.md` paste-ready blocks for ai rows; refresh via `image_gen.py --render-md` if stale), and where to place generated files (`project/images/<filename>`). After supply/replacement, validate the file and reconcile the owning row plus manifest to its usable status. For `slice` rows, list the parent sheet filename and target element names; the user places the sheet, then the agent reruns `slice_images.py`.

**Quick Generate export gate**: exhaust allowed automation without asking; stop
before `--quick-generate` when a required row is not both backed by its
validated file/provenance and in a usable status. File presence alone never
bypasses `Needs-Manual`.

`Needs-Manual` is also the entry status for **Offline Manual Mode** (no `IMAGE_BACKEND` configured, no host-native image tool in use). Affected ai rows are marked `Needs-Manual` from the start without a failed attempt — see [`image-generator.md`](./image-generator.md) §7 Offline Manual Mode.

Path-specific retry policies (provider chain, backend chain) live in the path's own reference.

---

## 7. Credits — Single Source of Truth

License / attribution data lives **only** in `project/images/image_sources.json`.

**Forbidden — credits anywhere else**:

- `notes/*.md` (TTS would speak them in the audio export)
- `total.md` (gets split, then overwritten)
- SVG `<title>` / `<desc>` (stripped by `svg_to_pptx.py`)
- A separate "Image Credits" appendix slide (lost on single-page sharing)

Executor reads the manifest per slide and renders inline credits when needed — see [`executor-web-image.md`](./executor-web-image.md) §1 and [`image-searcher.md`](./image-searcher.md) §7.

---

## 8. Intent Ownership

The `Reference` field is **intent**, not a query. Strategist owns it by default; Quick's main agent resolves it in active context. The receiving role translates without reopening it.

For derivatives, the required lineage/treatment prefix is intent metadata, not a provider query.

| ✅ Intent | ❌ Pre-processed |
|---|---|
| `"Diverse engineering team in modern office, natural light"` | `"team office light"` |
| `"Abstract digital waves, deep navy gradient #0A2540"` | `"use openverse, search 'waves'"` |

---

## 9. Handoff with SVG Authoring

SVG authoring consumes the active profile's resource authority plus:

| Artifact | Path | Purpose |
|---|---|---|
| Image files | `project/images/*.{jpg,png,webp}` | `<image>` references |
| Manifest | `project/images/image_sources.json` | License/provenance for sourced images and their derivatives |

**Default Generate boundary**: Executor does NOT invoke `image_gen.py` / `image_search.py` / `slice_images.py` / `image_treat.py`; missing material returns to Strategist-owned preparation.

**Quick Generate boundary**: the main agent finishes acquisition and planned derivation before SVG authoring, then neither acquires, derives, nor reselects while drawing.

---

## 10. Task Completion Checkpoint

Verify every row, file, triggered manifest/sidecar, and provenance record.
Default proceeds to Executor. Quick proceeds without interaction after
preparation and exports only when every required row has validated evidence and
a usable status. Report only blocking recovery.
