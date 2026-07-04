> See [`image-generator.md`](./image-generator.md) and [`image-searcher.md`](./image-searcher.md) for path-specific behavior.

# Image Acquisition Common Reference

Shared baseline for both acquisition paths. Path-specific behavior lives in the path's own reference.

---

## 1. Trigger Condition

Active when at least one resource list row has `Acquire Via: ai` / `web` / `slice`. Rows with `user` / `formula` / `placeholder` are skipped.

| Mode | Trigger |
|---|---|
| In-pipeline | `generate-ppt` workflow, image rows present |
| Standalone | Direct request against an existing project |

---

## 2. Image Resource List Format

Defined in `design_spec.md §VIII`. Status enum: see [`svg-image-embedding.md`](svg-image-embedding.md).

| Filename | Dimensions | Purpose | Type | Acquire Via | Status | Reference |
|---|---|---|---|---|---|---|
| cover.png | 1280x720 | Cover background | Background | `ai` | Pending | Modern tech abstract, deep blue gradient #0A2540 |
| team.jpg | 800x600 | Team photo | Photography | `web` | Pending | Diverse engineering team in modern office |
| formula_001.png | 736x168 | Block equation on P03 | Latex Formula | `formula` | Rendered | `E = mc^2` |
| spot_team.png | TBD after slicing | Team spot illustration | Illustration | `slice` | Pending | From `spot_sheet.png` cell 1,1 |

**Required per non-skipped row**: `Acquire Via`, `Status`, `Reference`.

---

## 3. Path Dispatch

For each row with `Status: Pending`:

| Acquire Via | Load reference | Run | Success status |
|---|---|---|---|
| `ai` | [`image-generator.md`](./image-generator.md) | `image_gen.py` | `Generated` |
| `web` | [`image-searcher.md`](./image-searcher.md) | `image_search.py` | `Sourced` |
| `slice` | [`image-generator.md`](./image-generator.md) §4.3 | `slice_images.py` after parent AI sheet is `Generated` | `Generated` |
| `user` | — | — | (already `Existing`) |
| `formula` | — | — | (already `Rendered`) |
| `placeholder` | — | — | (already `Placeholder`) |

> Lazy load: an all-`web` deck never reads `image-generator.md`, and vice versa.

---

## 4. Analysis Phase

Before processing any row:

1. `read_file <project_path>/design_spec.md` — extract color scheme, canvas format, target audience
2. Group resource list rows by `Acquire Via`
3. Confirm `project/images/` exists

---

## 5. Verification Phase

After all rows reach terminal status:

- Every non-skipped row has a file at `project/images/<filename>`, or is marked `Needs-Manual`
- Every `slice` row has a generated element file, or is marked `Needs-Manual` because its parent sheet is not available
- No `Pending` or `Failed` rows remain
- `image_prompts.json` exists when ≥1 ai row processed; its top level is an object with `items[]` (never a raw array), and every entry has `status ∈ {Generated, Needs-Manual}` (no `Pending` or `Failed` remaining)
- `image_sources.json` exists when ≥1 web row processed; every entry has `license_tier ∈ {no-attribution, attribution-required, manual}` (`manual` = a user-supplied `--from-url` replacement)

> `Needs-Manual` is a legitimate terminal state for ai rows — Step 7 entry waits for the user to place the file. See [`image-generator.md`](./image-generator.md) §7 Offline Manual Mode.

---

## 6. Failure Handling

**Hard rule**: acquisition failures MUST NOT halt the pipeline.

1. Try once
2. On recoverable failure (network, no candidates, license rejection, rate limit), retry once with broadened parameters
3. On second failure, set `Status: Needs-Manual`, log the reason in conversation, continue
4. After the phase completes, summarize all `Needs-Manual` rows for the user — list filenames, where prompts live (`images/image_prompts.md` paste-ready blocks for ai rows; refresh via `image_gen.py --render-md` if stale), and where to place generated files (`project/images/<filename>`). For `slice` rows, list the parent sheet filename and target element names; the user places the sheet, then the agent reruns `slice_images.py`.

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

Executor reads the manifest per slide and renders inline credits when needed — see [`executor-base.md`](./executor-base.md) §6.1 and [`image-searcher.md`](./image-searcher.md) §7.

---

## 8. Handoff with Strategist

The `Reference` field is **intent**, not a query. Strategist writes free-form intent; the receiving role translates.

| ✅ Intent | ❌ Pre-processed |
|---|---|
| `"Diverse engineering team in modern office, natural light"` | `"team office light"` |
| `"Abstract digital waves, deep navy gradient #0A2540"` | `"use openverse, search 'waves'"` |

---

## 9. Handoff with Executor

Executor consumes the resource list plus:

| Artifact | Path | Purpose |
|---|---|---|
| Image files | `project/images/*.{jpg,png,webp}` | `<image>` references |
| Manifest | `project/images/image_sources.json` | `license_tier` per Sourced image |

Executor does NOT invoke `image_gen.py` / `image_search.py` / `slice_images.py`.

---

## 10. Task Completion Checkpoint

```markdown
## ✅ Image Acquisition Phase Complete
- [x] {N} rows processed (`ai`: {a} / `web`: {b} / `slice`: {s})
- [x] {a} `Generated`, {b} `Sourced`, {s} sliced `Generated`, {c} `Needs-Manual`
- [x] image_prompts.json / image_sources.json written
- [ ] **Next**: Auto-proceed to Executor phase
```
