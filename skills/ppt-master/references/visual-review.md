# Visual Review Rubric

> Per-page visual self-check rubric for slide SVGs, read by the subagents spawned during the [`visual-review` stage](../workflows/stages/visual-review.md). The renderer contract lives in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md#visual_reviewpy).

## §0 Prerequisites

Required order: Executor finishes page → `svg_quality_checker.py` passes → `visual_review.py` renders PNG → this rubric runs. If the static checker has not run or failed, abort with status `prereq_failed`. Do not re-check what it already enforces: font-size anchor drift (`2px` from every declared role anchor), id uniqueness and XML well-formedness, canvas/structural typography and informational spec-lock comparison, `animation_config` compliance.

## §0.1 Subagent inputs

Each subagent processes a batch of pages (§6.1) with these inputs: (1) the page batch — `(svg_path, png_path, page_role, canvas)` records, `svg_path` under `<project>/svg_output/`, `png_path` under `<project>/.preview/`, `page_role` one of `cover` / `chapter` / `tldr` / `content` / `data` / `closing` / `breathing` parsed from `design_spec.md §IX` by the orchestrator (never guessed), `canvas` copied verbatim from the renderer record (`view_box`, `width` / `height`, `png_width` / `png_height`; never assumed or recomputed); (2) this rubric's path; (3) `<project>/design_spec.md` read-only — §IX is the truth for what the page should deliver; (4) `<project>/spec_lock.md` read-only; (5) a Style Review Focus excerpt, only when an installed `templates/design_spec.style.<id>.md` exists, with its source path and exact §VII wording; (6) writable `<project>/.review/`.

Read inputs 2–5 once at the start, then iterate the batch sequentially: apply the rubric → apply any Style supplement → write `<project>/.review/<page>.json` → next page. Style Review Focus is supplemental acceptance context, not a second rubric: it cannot add Hard rules, weaken §§1–3, or authorize content, identity, or structural edits. Record a clearly unmet focus item as `rule: "STYLE"`; fix it only when the rubric already permits that atomic edit, otherwise add a `needs_human_items` entry with a suggested fix.

## §1 Hard rules (fix every hit)

| # | Category | Trigger | Permitted fix |
|---|----------|---------|---------------|
| H1 | Out-of-bounds | element bbox outside `canvas.view_box` | shrink or reposition into canvas |
| H2 | Text overflow | text bbox extends past its visual container | reduce font-size or line-break |
| H3 | Text overlap | two `<text>` bboxes intersect (tspans within one text excluded) | reposition or resize |
| H4 | Readability | contrast < 4.5 (small text) / < 3.0 (font-size ≥ 24px), or text directly atop a complex image with no scrim | when neither color is a brand token: position-only escape — add a `<rect>` scrim under the text, or raise the text to ≥ 24px so the 3.0 threshold applies; when either color is a brand token: do not edit → §1.1 |
| ~~H5~~ | Font-ramp drift | covered by `svg_quality_checker.py` (§0) | n/a |
| H6 | Element collision | rect/circle/path bboxes overlap with z-order violating semantics | open spacing |
| H7 | Declared page chrome displaced | page number / header / footer explicitly declared by `design_spec §IX`, `spec_lock.md`, or the installed template with a concrete anchor is covered, missing, or outside `canvas.view_box` | restore only that declared chrome; never invent undeclared chrome |
| H8 | Image rendering broken | `<image>` empty / broken / severely distorted | fix `href`; for `adaptive`, choose `meet` or a safer crop; a new complete-display requirement returns to §VIII `Crop Policy` and lock projection |
| H9 | Missing key element | element required by `design_spec §IX` absent from the render | recreate from spec |

Detection order, sequential within one subagent: H1 → H2 → H7 (structure), H3 → H6 (collisions), H4 (readability), H8 → H9 (content).

### §1.1 Brand-token contrast escalation

If H4 fires and the foreground or background is a brand token from `spec_lock.md`, the violation repeats on every page using that token, so do not touch the SVG — even a scrim or size escalation is a brand-level decision. Record the finding under `needs_human_items` with `rule: "H4"`, the element selector, and a `suggested_fix_summary` naming brand-level options (e.g. "raise body-text token from `#6E7681` to `#8B949E` deck-wide"), and append it to `<project>/.review/brand_review.json` (append-only, one entry per distinct token+context pair). The page's `status` is `needs_human` when H4 is its only Hard hit; otherwise it finishes `fixed` with the H4 entry alongside. The orchestrator aggregates brand findings at the end of the run.

## §2 Soft rules (act only when clearly bad)

When in doubt, leave it — under-fixing beats oscillation.

| # | Category | Trigger | Fix direction |
|---|----------|---------|---------------|
| S1 | Vertical rhythm tight | within one logical text block, consecutive baselines gap < 1.05× the larger font-size | open to 1.15–1.3× |
| S2 | Vertical rhythm hollow | within one block, > 150 px non-decorative whitespace; `breathing` pages exempt | tighten |
| S3 | Intended anchor missed | hero/title block clearly displaced from a concrete anchor explicitly declared by §IX, the lock, or the template; canvas center counts only when the plan calls for centering — intentional asymmetry, negative space, and image-focal placement are exempt | restore toward the declared anchor |
| S4 | Alignment drift | same-column `x` or same-row baselines differ by > 4 px and are meant to share a grid line | snap to grid |
| S5 | Grid non-uniform | N-card row: neighbor `x`-spacing differs by > 5% of the average | re-distribute |
| S6 | CJK letter-spacing | CJK `letter-spacing / font-size > 5%` | reduce to ≤ 2% |
| S7 | Decorative accents compete | several unlocked colors with no semantic role visibly compete with each other and the intended primary emphasis; brand, natural-media, data-series, status, and other semantic colors are exempt | consolidate only the competing decorative colors into existing accents; never recolor locked or semantic elements |
| S8 | Emphasis mismatch | most prominent element ≠ the element §IX declares as the page's primary | rescale to match intent |
| S9 | Image-text relationship | caption > 60 px from its image; text on a busy image without scrim; image clearly purposeless | tighten / add scrim / remove |
| S10 | Breathing violation | `page_role = breathing` with a ≥ 3 rounded-card grid | replace with naked text / single hero |

## §3 Don't-touch

Equal weight to §1: brand decisions (color tokens, font families, geometry style from `spec_lock.md` / brand directory); layout restructure (column counts, chart types, sections); content (no added or removed copy — only position, font-size within the role anchor `±2px`, spacing, letter-spacing, alignment, scrim); other files (`design_spec.md`, `spec_lock.md`, `animations.json`, `image_prompts.json`, `images/`, other pages' SVGs); atomicity (one edit per fix, no bulk multi-element replacement). A "violation" that requires reinterpreting `design_spec.md` → `needs_human` with a one-line `suggested_fix_summary`.

## §4 Iteration protocol

### §4.0 Iteration 0 — PNG sanity check

Before any rule: the PNG exists and is non-empty; its dimensions equal the record's `canvas.png_width` × `canvas.png_height`; it is not all-background (background-color pixels < 99% — guards blank renders only, not sparse dark layouts). Any failure → `render_failed`, abort.

### §4.1 Iteration loop

Default budget is **1 iteration**; more requires explicit opt-in in the orchestrator prompt and roughly doubles render cost per iteration. Iteration 1: scan all Hard + Soft → fix → re-render only if budget ≥ 2. Iteration 2 (opt-in): re-verify changed elements + scan for new Hard hits → fix → re-render. Iteration 3 (opt-in): report only. Hard rules have no per-round cap; Soft rules ≤ 2 fixes per iteration, remainder to `untouched_concerns`.

### §4.2 Termination conditions

Rollback: a fix introduces a new Hard hit → `cp` the backup back, status `needs_human`, record "rolled back fix X — created Hard Y". Soft thrash (budget ≥ 2): iteration 2 introduces a new Soft hit → stop, `needs_human`, "fixes are competing". Clean exit: zero Hard hits and ≤ 1 Soft hit remaining → `ok` if nothing was applied, `fixed` otherwise.

### §4.3 Backup discipline

Before the first edit on a page in iteration `N`: `cp <project>/svg_output/<page>.svg <project>/.review/backup/<page>.iter<N>.svg`; record the path in every finding's `backup_path`.

## §5 Output schema

One file per page at `<project>/.review/<page>.json`; every `needs_human_items` entry carries a `suggested_fix_summary`, never a bare problem description.

```json
{
  "page": "02_three_steps.svg",
  "page_role": "content",
  "canvas": {"view_box": [0, 0, 1242, 1660], "width": 1242, "height": 1660, "png_width": 1242, "png_height": 1660},
  "status": "ok" | "fixed" | "needs_human" | "render_failed" | "prereq_failed",
  "iterations_run": 1,
  "screenshot_paths": [".preview/02_three_steps.png", ".preview/02_three_steps.iter1.png"],
  "findings": [{
    "iter": 1, "rule": "S6", "severity": "soft",
    "evidence": "letter-spacing=10 on font-size=84, ratio=11.9% > 5%",
    "fix_applied": {"element": "#hero-statement text[font-size='84']", "before": "letter-spacing=\"10\"", "after": "letter-spacing=\"2\""},
    "verified_in_iter": 2,
    "backup_path": ".review/backup/02_three_steps.iter1.svg"
  }],
  "untouched_concerns": [{"rule": "S1", "evidence": "...", "reason": "soft-cap reached" | "ambiguous_design_intent"}],
  "needs_human_items": [{"rule": "H9", "suggested_fix_summary": "Hero subtitle declared in spec §IX.4 missing; add a <text> at (80,496) per design language"}],
  "design_intent_check": {"spec_says": "TL;DR — emphasize 意图 as the core abstraction", "render_delivers": true, "note": "..."}
}
```

## §6 Dispatch & messaging contract

### §6.1 Orchestrator → subagent (batched dispatch)

The orchestrator partitions N pages into `ceil(N/K)` batches of ≤ K pages (default **K = 5**, configurable per run) and spawns one subagent per batch, all in one assistant message (parallel `Agent` calls). Each prompt is self-contained — absolute paths for inputs 1–5 plus the full batch records; no prior context assumed. `subagent_type: general-purpose`; tools Read, Edit, Bash (`cp` backups), Write (JSON); no playwright — the orchestrator pre-renders. Dispatch must work with anonymous subagents when `name` / `team_name` are unavailable.

Batched dispatch exists because the rubric (~2.5K tokens), `design_spec.md` (~4–5K), and `spec_lock.md` (~1K) are identical across pages and do not share a prompt cache between siblings: K=5 cuts fixed-document re-reads by ~75% on a 20-page deck and bounds failure blast radius. Guidance: K=5 default (decks to ~50 pages), K=3 for high-fidelity short decks, K=10 for token-sensitive large decks; beyond ~10 pages subagent context compression starts dropping early findings, so keep `K × (avg_svg_size + image_token_cost + report_size)` well under the subagent budget.

### §6.2 Subagent → orchestrator

The subagent's final action before idling is `SendMessage(to=<lead>)` listing one JSON path per processed page and a ≤150-word summary of the batch; idling without messaging or with a partial batch is a violation. A mid-batch abort still sends the report with aborted pages marked `needs_human` or `render_failed`.

### §6.3 Orchestrator → main agent

The orchestrator's final action is `SendMessage(to=<lead>)` with the aggregate table (page × status × hard_hits × soft_hits × fixes_applied × needs_human_reason), one ≤150-word plumbing verdict, and the `brand_review.json` path if any §1.1 aggregation occurred.

### §6.4 Concurrency

Rendering is serialized by `visual_review.py`'s lock at `<project>/.preview/.render.lock`; subagents never call the renderer concurrently, and iteration re-renders go through the same lock.

## §7 Renderer expectations

`visual_review.py` is a pure render-and-validate tool: it never edits SVGs and reads no rule from this rubric. Its output, canvas, lock, and exit-code contract is documented in [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md#visual_reviewpy).
