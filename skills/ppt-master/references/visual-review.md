# Visual Review Rubric

> Per-page visual self-check rubric for slide SVGs. Read by the subagents spawned during the `visual-review` stage. Companion to the [`visual-review` stage](../workflows/stages/visual-review.md) and the [`visual_review.py`](../scripts/visual_review.py) renderer.

## §0 Prerequisites

This rubric **does not repeat** what `svg_quality_checker.py` already covers. Required upstream order:

```
Executor finishes page → svg_quality_checker.py passes → visual_review.py renders PNG → this rubric runs
```

If the static checker has not been run or has failed, the subagent must abort with status `prereq_failed` and not start the rubric. Topics already enforced by the static checker (do **not** re-check here):

- font-size ramp drift (`RAMP_MIN_RATIO=0.5` / `MAX=5.0`)
- id uniqueness, XML well-formed
- spec_lock drift (colors / fonts / canvas)
- animation_config compliance

## §0.1 Subagent inputs

Each review subagent processes a **batch** of pages (see §6.1 for batch sizing). The inputs are:

1. **Page batch** — a list of `(svg_path, png_path, page_role)` tuples, one per assigned page. `svg_path` resolves under `<project>/svg_output/<page>.svg`, `png_path` under `<project>/.preview/<page>.png`. `page_role` is one of `cover` / `chapter` / `tldr` / `content` / `data` / `closing` / `breathing`, parsed from `design_spec.md §IX` by the orchestrator — subagents do **not** guess.
2. **Path to this rubric file**
3. **`<project>/design_spec.md`** (read-only) — §IX outline is the source of truth for "what should this page deliver"
4. **`<project>/spec_lock.md`** (read-only) — brand-locked values
5. **`<project>/.review/`** (writable) — where backups and findings JSON go

The subagent reads inputs 2–4 **once** at the start of its turn, then iterates over the page batch sequentially (one page at a time): apply the rubric → write `<project>/.review/<page>.json` → move on. This is the core token-saving move — three fixed documents are read N/K times instead of N times.

## §1 Hard rules (fix every hit)

| # | Category | Trigger | Permitted fix |
|---|----------|---------|---------------|
| H1 | Out-of-bounds | element bbox falls outside `0,0,1280,720` | shrink or reposition into canvas |
| H2 | Text overflow | text bbox extends past its visual container | reduce font-size or line-break |
| H3 | Text overlap | two `<text>` elements' bboxes intersect (tspans within one text excluded) | reposition or resize |
| H4 | Readability | contrast < 4.5 (small text) / < 3.0 (font-size ≥ 24px); OR text directly atop a complex image with no scrim | if **neither** the foreground nor the background color is a brand token: position-only escape — add a `<rect>` scrim under the text, or raise the offending text's font-size to ≥ 24px so the 3.0 threshold applies. If **either** color is a brand token: do not edit the SVG → goto §1.1 escalation. |
| ~~H5~~ | Font-ramp drift | *covered by `svg_quality_checker.py` — see §0 prerequisites* | n/a (do not re-check) |
| H6 | Element collision | rect/circle/path bboxes overlap with z-order violating semantics | open spacing |
| H7 | Anchored element displaced | page number / header / footer covered, missing, or out of canvas | restore to anchor position |
| H8 | Image rendering broken | `<image>` empty / broken-image / severe distortion | fix `href`, adjust `preserveAspectRatio`, add `no-crop` if face/data is cropped |
| H9 | Missing key element | element required by `design_spec §IX` outline is absent from rendered slide | recreate from spec |

Detection order (run sequentially, do not parallelize within a single subagent):

```
H1 → H2 → H7  (structure)
H3 → H6      (collisions)
H4           (readability)
H8 → H9      (content)
```

### §1.1 Brand-token contrast escalation

If H4 fires and the foreground or background color is a **brand token** (defined in `spec_lock.md`) — i.e., the violation will repeat on every page using that token — do **not** touch the SVG. Brand decisions are §3 Don't-Touch; even position-only escapes (scrim insertion, font-size escalation) shift the page's visual weight in ways that should be a brand-level decision, not a per-page subagent decision. Instead:

1. Record the finding in the page JSON under `needs_human_items` with `rule: "H4"`, the offending element selector, and `suggested_fix_summary` describing the brand-level options (e.g., "raise body-text token from `#6E7681` to `#8B949E` deck-wide" or "introduce a scrim style in the brand").
2. Append the finding to `<project>/.review/brand_review.json` (append-only log; one entry per distinct token+context pair). The orchestrator aggregates and surfaces this to the main agent at the end of the run so the user can make one cross-deck decision instead of N per-page ones.
3. The page's `status` is `needs_human` if H4 is the only Hard hit on the page; if other (non-brand) Hard hits were fixed, the page still finishes as `fixed` and the brand-token H4 entry sits in `needs_human_items` alongside.

The aggregated brand review is the responsibility of the orchestrator at the end of the run, not the per-page subagent.

## §2 Soft rules (act only when clearly bad)

Subagents must apply the **明显** ("clearly bad") threshold — when in doubt, leave it. Better to under-fix than to oscillate.

| # | Category | Trigger | Fix direction |
|---|----------|---------|---------------|
| S1 | Vertical rhythm tight | Within the **same logical text block**, consecutive baselines have gap < 1.05× larger font-size | open to 1.15–1.3× |
| S2 | Vertical rhythm hollow | Within one logical block, > 150 px non-decorative whitespace; `breathing` pages exempt | tighten |
| S3 | Visual centroid off | hero/title block centroid offset from canvas center exceeds threshold by `page_role`: `cover` > 35%, `chapter` > 25%, `tldr`/`closing`/`breathing` > 25%, `content`/`data` > 20% | shift toward intended anchor |
| S4 | Alignment drift | same-column elements differ in `x` by > 4 px (or same-row baselines by > 4 px) **and** are semantically meant to be on the same grid line | snap to grid |
| S5 | Grid non-uniform | N-card row: neighbor `x`-spacing differs by > 5% of the average | re-distribute |
| S6 | CJK letter-spacing | CJK characters with `letter-spacing / font-size > 5%` | reduce to ≤ 2% |
| S7 | Accent overload | > 2 accent colors across ≥ 3 distinct elements | collapse to 1 primary + 1 secondary |
| S8 | Emphasis mismatch | most visually prominent element ≠ the element `design_spec §IX` declares as the page's primary | rescale to match intent |
| S9 | Image-text relationship | caption > 60 px from its image; text on busy image without scrim; image clearly purposeless | tighten / add scrim / remove |
| S10 | Breathing violation | only when `page_role = breathing`: ≥3 rounded card grid | replace with naked text / single hero |

## §3 Don't-touch

Hard boundary, equal weight to §1.

- **Brand decisions** — color tokens, font families, geometry style (decided by `spec_lock.md` / brand directory)
- **Layout restructure** — do not change column counts, replace chart types, add/remove sections
- **Content** — do not add or remove copy; only adjust position, font-size (within ramp), spacing, letter-spacing, alignment, scrim
- **Other files** — never edit `design_spec.md` / `spec_lock.md` / `animations.json` / `image_prompts.json` / `images/` / other pages' SVGs
- **Atomicity** — one edit per fix, no bulk multi-element replacements

If a "violation" requires reinterpreting `design_spec.md` to fix → mark `needs_human` with a one-line `suggested_fix_summary`.

## §4 Iteration protocol

### §4.0 Iteration 0 — PNG sanity check

Run before applying any rule:

- PNG file exists and is non-zero bytes
- PNG dimensions = 1280 × 720
- PNG is **not** all-background (a histogram check: count of background-color pixels < 99% of total) — guards against blank/white-out renders only, **does not** filter sparse dark layouts

Any check fails → status = `render_failed`, abort without scanning rules.

### §4.1 Iteration loop

The full loop is defined here but the **default budget is 1 iteration**. Multi-iteration runs require an explicit opt-in in the orchestrator prompt and roughly double render cost per added iteration.

```
iteration 1: scan all Hard + Soft → fix → (re-render only if budget ≥ 2)
iteration 2 (opt-in): re-verify changed elements + scan for new Hard hits → fix → re-render
iteration 3 (opt-in): report only, no further fix
```

Per-iteration fix caps:

- **Hard rules**: no per-round cap — every Hard hit must be addressed in the iteration it was found in
- **Soft rules**: ≤ 2 fixes per iteration; remaining Soft hits go to `untouched_concerns`

### §4.2 Termination conditions

- **Rollback trigger**: any iteration's fix introduces a **new Hard hit** that did not exist before → immediately `cp` the backup back over the SVG, status = `needs_human`, finding records "rolled back fix X — created Hard Y"
- **Soft thrash trigger** (iteration budget ≥ 2 only): iteration 2's fix introduces a **new Soft hit** that did not exist before → stop, status = `needs_human` with note "fixes are competing"
- **Clean exit**: iteration ends with zero Hard hits and ≤ 1 Soft hit remaining → status = `ok` if no fixes were applied, `fixed` if any were applied

### §4.3 Backup discipline

Before the **first** `Edit` on a page in any iteration `N`, the subagent must:

```bash
cp <project>/svg_output/<page>.svg <project>/.review/backup/<page>.iter<N>.svg
```

The backup path is recorded in every finding's `backup_path` field. Backups are the rollback anchor for §4.2.

## §5 Output schema

Each subagent writes exactly one file to `<project>/.review/<page>.json`:

```json
{
  "page": "02_three_steps.svg",
  "page_role": "content",
  "status": "ok" | "fixed" | "needs_human" | "render_failed" | "prereq_failed",
  "iterations_run": 1,
  "screenshot_paths": [
    ".preview/02_three_steps.png",
    ".preview/02_three_steps.iter1.png"
  ],
  "findings": [
    {
      "iter": 1,
      "rule": "S6",
      "severity": "soft",
      "evidence": "letter-spacing=10 on font-size=84, ratio=11.9% > 5%",
      "fix_applied": {
        "element": "#hero-statement text[font-size='84']",
        "before": "letter-spacing=\"10\"",
        "after": "letter-spacing=\"2\""
      },
      "verified_in_iter": 2,
      "backup_path": ".review/backup/02_three_steps.iter1.svg"
    }
  ],
  "untouched_concerns": [
    {
      "rule": "S1",
      "evidence": "...",
      "reason": "soft-cap reached" | "ambiguous_design_intent"
    }
  ],
  "needs_human_items": [
    {
      "rule": "H9",
      "suggested_fix_summary": "Hero subtitle declared in spec §IX.4 missing; add a <text> at (80,496) per design language"
    }
  ],
  "design_intent_check": {
    "spec_says": "TL;DR — emphasize 意图 as the core abstraction",
    "render_delivers": true,
    "note": "..."
  }
}
```

`needs_human_items` must include a `suggested_fix_summary` for every entry — never bare problem descriptions.

## §6 Dispatch & messaging contract

This rubric is consumed by subagents spawned via the `visual-review` stage. Mandatory dispatch invariants:

### §6.1 Orchestrator → subagent (batched dispatch)

The orchestrator partitions the N pages into `ceil(N/K)` batches of ≤ K pages each (default **K = 5**; configurable per run via the orchestrator prompt) and spawns one subagent per batch.

- Spawn all batch subagents in **one assistant message** (parallel `Agent` calls). Sequential dispatch breaks pipelining.
- Each subagent prompt is **self-contained** — no prior conversation context. Inline the absolute paths for §0.1 inputs 1–5 explicitly, plus the full `(svg_path, png_path, page_role)` list for that batch. Do not assume the subagent knows the project root.
- `subagent_type: general-purpose`. Tool restrictions: Read, Edit, Bash (for `cp` backups), Write (for JSON output). MCP playwright is **not** required by subagents — orchestrator pre-renders PNGs.
- `name` / `team_name` parameters may be unavailable from nested teammate context. Dispatch must remain functional with anonymous subagents — do not require named addressing.

**Why batched, not per-page**: the rubric (~2.5K tokens), `design_spec.md` (~4–5K), and `spec_lock.md` (~1K) are identical inputs across all pages and do **not** share a prompt cache between sibling subagents. A 20-page deck with per-page dispatch re-reads ~150K tokens of fixed documents; batched dispatch with K=5 cuts that by ~75% while staying inside default parallel-subagent limits (~10). Batches also bound failure blast radius — one crashed subagent loses K pages, not the entire run.

**Batch size guidance**:
- `K = 5` (default) — balanced; safe for decks up to ~50 pages
- `K = 3` — high-fidelity / small decks (≤ 12 pages); slightly higher parallelism
- `K = 10` — token-sensitive / large decks (50+ pages); fewer subagents, larger blast radius per failure

Larger K is **not** always better: subagent context fills with prior pages' SVG / PNG / findings as the batch progresses, and beyond ~10 pages context auto-compression starts dropping early findings. Keep K such that `K × (avg_svg_size + image_token_cost + report_size)` stays well under the subagent context budget.

### §6.2 Subagent → orchestrator

- Subagent's **final action before going idle** must be `SendMessage(to=<lead>)` listing one JSON path per processed page (e.g., `<project>/.review/<page>.json`) and a ≤150-word text summary covering all pages in the batch. Going idle without messaging — or messaging with a partial batch — is a protocol violation.
- If the subagent aborts mid-batch (rule §4.2 rollback, tool error, etc.), it must still send the batch report covering both completed and aborted pages, with the aborted pages marked `needs_human` or `render_failed` as appropriate.

### §6.3 Orchestrator → main agent

- Orchestrator's **final action before going idle** must be `SendMessage(to=<lead>)` containing:
  - the aggregate Markdown table (page × status × hard_hits × soft_hits × fixes_applied × needs_human_reason)
  - one ≤150-word "plumbing verdict" paragraph
  - path to `brand_review.json` if any §1.1 aggregations occurred

### §6.4 Concurrency

- Pre-rendering is serialized by `visual_review.py`'s file lock at `<project>/.preview/.render.lock`. Subagents must **not** call the renderer concurrently. Re-renders during iteration loop go through the same lock.

## §7 Renderer expectations *(script contract)*

`visual_review.py <project> [pages...]` must guarantee:

- Output PNG matches what the user would see in the live-preview browser (inlined `<use data-icon>`, resolved `<image href>`)
- Output dimensions = 1280 × 720
- File-lock serialization at `<project>/.preview/.render.lock`
- Clean exit codes:
  - `0` — all requested pages rendered
  - `2` — live-preview server not running for this project (subagent should not retry; surfaces to the orchestrator)
  - `3` — rendering backend (playwright + chromium) missing or unable to launch (config error, surface to user)
  - `4` — page-level render failure (specific failures listed in stderr; partial output is acceptable)

The renderer never edits SVGs and never reads any rule from this rubric — it is a pure render-and-validate tool.
