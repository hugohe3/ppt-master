> See [`image-generator.md`](./image-generator.md) and [`image-searcher.md`](./image-searcher.md) for path-specific behavior.

# Image Acquisition and Preparation Common Reference

Shared baseline for both acquisition paths and for prepared derivatives.

**Trigger**: at least one resource row has `Acquire Via: ai` / `web` / `slice`, or any §VIII / Quick active-context resource is a pending prepared derivative (`user` / `placeholder` rows are tracked but skipped) — in Default Generate from `design_spec.md §VIII`, in Quick from the main agent's active-context decisions plus required operational manifests, or standalone against an existing project.

## 1. Resource Row and Path Dispatch

Status enum: [`svg-image-embedding.md`](svg-image-embedding.md). Per non-skipped row `Acquire Via` and `Status` are required; `Reference` is required for every `web` / `slice` row, every newly authored `ai` row, and every derivative (an existing `ai` row with a blank `Reference` continues only through [`image-generator.md`](./image-generator.md) §8's declared inference). Quick: explicit user assets, URLs, and path instructions win; otherwise the agent chooses `user` / `ai` / `web` / `slice` rows and AI path `auto` without interaction.

| Filename | Dimensions | Purpose / Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference |
|---|---|---|---|---|---|---|---|
| `<planned file>` | `<planned size>` | `<planned role>` | `<owner-resolved recommendation>` | `adaptive` / `no-crop` | `ai` / `web` / `slice` | Pending | `<acquisition brief>` |

Classify `Reference: Derived from <canonical bare filename>; treatment=<operation>; …` before `Acquire Via`: the parent must be a distinct non-derived `user`, `web`, `ai`, or `slice` row (no placeholder parents, chains, cycles, or self-reference). Then for each Pending row:

| Row kind / Acquire Via | Load | Run | Success status |
|---|---|---|---|
| Deterministic prepared derivative | this reference | after the parent is usable, `image_treat.py` to a distinct `.png`; preserve the source | inherits the parent: `user → Existing`, `web → Sourced`, `ai/slice → Generated` |
| Registered-layer derivative | [`image-generator.md`](./image-generator.md) §4.4 | after the parent is usable, §4.4 | supplied final `user → Existing`; generated `ai → Generated` |
| `ai` | [`image-generator.md`](./image-generator.md) | `image_gen.py` | `Generated` |
| `web` | [`image-searcher.md`](./image-searcher.md) | `image_search.py`; with vision, bounded thumbnail pages then one selected original; without vision, strict metadata-ranked best-only | `Sourced` (`Needs-Selection` is intermediate) |
| `slice` | [`image-generator.md`](./image-generator.md) §4.3 | `slice_images.py` after the parent sheet is `Generated` | `Generated` |
| `user` / `placeholder` | — | — | already `Existing` / `Placeholder` |

An all-`web` deck never reads `image-generator.md`, and vice versa.

**Mandatory — consume the resolved treatment path**: this phase never adds or reselects a treatment. `none` uses the canonical bitmap; `native` creates no file (SVG owns crop/clip, transform, opacity, frame/shadow/scrim/vignette, overlap); `prepared derivative` is a separate file only for pixel blur, desaturation/grayscale, duotone, brightness/contrast, or existing cutout/registered-layer preparation. Never bake a native treatment into a derivative.

**Reference — pattern → preparation (an adopted id creates nothing by itself)**: `P*` / `M*` / `C*` use existing assets with native composition; `A1-02` / `A1-03` → `image_treat.py` blur / duotone; `A1-01` / `A1-04` → an existing composite or the host/AI path (`image_treat.py` does not blend); `A2-01` → an existing RGBA or flat-key AI/slice asset (with `A2-02` / `A2-03` + §4.4 when scene registration is required); `A2-02` / `A2-03` → §4.4 registered layers; `A2-04` → an existing transparent frame/device asset plus a content picture registered beneath it; `A3-01` → original/subject plus a registered `image_treat.py` derivative; `A3-02` → a registered full-canvas blur derivative with native crop panels; `A3-03` → a desaturated base plus an existing/§4.4 color subject layer.

**Intent, not query**: `Reference` is intent (`"Diverse engineering team in modern office, natural light"`, `"Abstract digital waves, deep navy gradient #0A2540"`), owned by Strategist or Quick's agent; the receiving role translates it without reopening it, and a derivative's lineage prefix is metadata, not a query.

## 2. Procedure

1. Read the Design Spec/lock or reuse Quick's active-context decisions; separate derivatives, group canonical rows by `Acquire Via`; ensure `project/images/` exists.
2. Finish `user` and triggered `ai` / `web` / `slice` canonical preparation.
3. Materialize only declared derivatives from usable parents, preserving originals, then run `analyze_images.py` once before SVG.
4. Verify: every non-skipped row has `project/images/<filename>` or is `Needs-Manual`; each derivative has its distinct file and usable parent, with web provenance copied in `image_sources.json`; every `slice` row has its element file or is `Needs-Manual` because its sheet is unavailable; no `Pending`, `Failed`, or `Needs-Selection` remains; `image_prompts.json` exists when an active `ai` row remains, every entry `Generated` or `Needs-Manual`; `image_sources.json` exists when a web row was processed, every entry with `license_tier ∈ {no-attribution, attribution-required, manual}`.

`Needs-Manual` is terminal for acquisition, not for export: a later supplied file is validated and its row reconciled to `Existing`, `Generated`, or `Sourced`. Quick blocks every required row still in `Needs-Selection` or `Needs-Manual` whatever files happen to exist.

## 3. Failure Handling

**Hard rule — automatic exhaustion before blocking**: never open an interactive choice or stop while an untried permitted strategy remains. On a recoverable failure (network, no candidates, license rejection, rate limit) continue through materially different strategies inside the path's permissions without repeating an exhausted one; when the path's variants, ranked pages, providers, license stages, backends, and retries are exhausted, follow its terminal rule — web may set `Needs-Manual`; a Default AI row stays `Failed` until [`image-generator.md`](./image-generator.md) §7's three-outcome recovery decision, and only confirmed manual fulfillment sets `Needs-Manual`; Quick removes exhausted automated AI/slice jobs through §7's no-AI replan, while an explicitly selected manual path may set `Needs-Manual`. Afterwards summarize every `Needs-Manual` row: filename, where the prompt lives (`images/image_prompts.md`, refreshed with `image_gen.py --render-md`), the target path `project/images/<filename>`, and for slices the parent sheet and element names (the user places the sheet, the agent reruns `slice_images.py`). `Needs-Manual` is also the entry to Offline Manual Mode, reached only through an explicit `manual` decision; neither profile probes a provider during planning.

## 4. Credits and Handoff

License and attribution data live only in `project/images/image_sources.json` — never in `notes/*.md` (TTS would speak them), `total.md`, SVG `<title>` / `<desc>` (stripped on export), or a credits appendix slide. Executor renders inline credits per slide under [`executor-web-image.md`](./executor-web-image.md) and [`image-searcher.md`](./image-searcher.md) §7.

SVG authoring consumes `project/images/*.{jpg,png,webp}` and `image_sources.json`. Default Executor never invokes `image_gen.py` / `image_search.py` / `slice_images.py` / `image_treat.py` — missing material returns to Strategist-owned preparation; Quick finishes acquisition and derivation before authoring and neither acquires, derives, nor reselects while drawing. Completion: every row, file, manifest, and provenance record verified; Default proceeds to Executor, Quick exports only with validated evidence and usable statuses; report only blocking recovery.
