---
description: Optional quality-gate stage for per-page rubric-based visual review.
---

# Visual Review Stage

> Optional Generate-PPTX quality stage. Goal: reduce human iteration by letting AI subagents visually self-check each rendered slide against a fixed rubric and apply atomic position/spacing fixes.
>
> Reads `<project>/svg_output/<page>.svg` and a pre-rendered PNG of each slide, then either applies a fix or flags `needs_human`. **Never touches** brand decisions, layout structure, or other files.
>
> This stage is **context-independent** — invokable in a fresh chat session with only `<project_path>` as input. No upstream conversation context required.

## Positioning

This is an **optional auxiliary loop**, opt-in only. The main pipeline (SKILL.md Step 1–7) does not invoke it; trigger only when the user explicitly asks for a visual re-pass on the generated SVGs before export.

**Token cost**: each batch subagent re-reads the rubric + `design_spec.md` + `spec_lock.md` and processes K SVG+PNG pairs. For a 20-page deck with K=5, expect on the order of 100–150K additional input tokens on top of the main generation run.

## When to Run

- Executor (SKILL.md Step 6) has finished all pages
- `svg_quality_checker.py` has passed
- Post-processing (`finalize_svg.py`, `svg_to_pptx.py`) has **not** yet run
- The user has explicitly requested visual review

For decks containing data charts, run [`verify-charts`](./verify-charts.md) first — visual-review focuses on visual rhythm / collision / alignment, not chart coordinate math.

## When NOT to Run

- The project has no `svg_output/<page>.svg` files yet — finish Executor first
- `svg_quality_checker.py` has not been run or has failed — fix static violations first
- User has already applied annotations via the `live-preview` stage and is in a fixed-edit loop — describe changes directly, do not re-trigger rubric
- The user has not asked for it — do not auto-invoke based on inferred model capability or deck size

---

## Prerequisites

```bash
# 1. playwright + chromium installed (the PNG renderer)
pip install playwright
python3 -m playwright install chromium

# 2. live-preview server running for this project (provides inlined SVG fetch)
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --no-browser
# (single instance per project — if it's already running, skip)
```

The renderer (`visual_review.py`) does **not** auto-start the live-preview server. It expects the server to be reachable at `http://localhost:5050` (override with `--server-url`).

> **Why playwright, not cairosvg**: cairo's text API has no font-fallback chain, so CJK characters render as tofu boxes for any deck whose font-family list relies on system fallback (Microsoft YaHei / PingFang SC / etc.). Playwright drives a real chromium and produces output identical to what the live-preview browser shows — the only fidelity-preserving option for bilingual decks.

---

## Step 1 — Pre-render all PNGs

```bash
python3 skills/ppt-master/scripts/visual_review.py <project_path>
```

This writes one PNG per page to `<project_path>/.preview/<page>.png` at 1280×720, with `<use data-icon>` inlined and `<image href>` resolved exactly as the live-preview browser sees them. Renders are serialized via a project-local file lock — safe to invoke concurrently.

Exit codes:

- `0` — all pages rendered
- `2` — live-preview server unreachable (start it per Prerequisites)
- `3` — playwright python / chromium not installed (or browser failed to launch)
- `4` — one or more page-level render failures (see stderr; partial output is on disk)

If any page comes back with `"all_background": true` in the JSON summary, that page rendered to a blank surface — investigate before continuing (broken `<use>` reference, missing image asset, etc.).

---

## Step 2 — Spawn the review team

Create a team and dispatch one orchestrator agent. The orchestrator partitions the N pages into batches of ≤ K pages (default **K = 5**) and spawns one subagent per batch **in parallel** (single message, `ceil(N/K)` parallel `Agent` calls). Each batch subagent reads the fixed inputs (rubric + `design_spec.md` + `spec_lock.md`) **once**, then iterates over its assigned pages sequentially.

```text
TeamCreate(team_name="visual-review-<project>", agent_type="orchestrator")
Agent(
  team_name="visual-review-<project>",
  subagent_type="general-purpose",
  name="orchestrator",
  prompt=<orchestrator-prompt>,
)
```

The orchestrator prompt must be self-contained and is the **single** place where dispatch shape, batch size, and forbid lists are stated — the rubric (`references/visual-review.md`) defines the contract those prompts must satisfy. Required fields (all absolute paths):

- `<project_path>` — project root
- Full page list with `page_role` per page (parse `<project>/design_spec.md` §IX outline; if §IX is absent, default every page to `content` and flag this in the final report)
- Batch size `K` (default 5; raise to 10 for token-sensitive runs on large decks, lower to 3 for high-fidelity short decks — see rubric §6.1)
- Iteration budget per page (default 1; 2 only for high-stakes / final-cut runs — see [Appendix: Iteration loop](#appendix-iteration-loop-opt-in))
- Path to the rubric: `skills/ppt-master/references/visual-review.md`
- Dispatch contract reference: rubric [§6](../../references/visual-review.md#6-dispatch--messaging-contract) (batched parallel spawn, self-contained prompts, mandatory `SendMessage` on idle, anonymous-name tolerance)
- Subagent forbid list: do not edit any other page, `design_spec.md`, `spec_lock.md`, `animations.json`, `image_prompts.json`, or `images/`

**Host compatibility**: `TeamCreate` and `SendMessage` are Claude-Code-specific multi-agent primitives. On hosts without those primitives (Cursor, VS Code + Copilot, Codebuddy, etc.) the main agent processes batches sequentially — same partitioning, same per-batch prompts, no parallel dispatch. Token savings from shared fixed inputs still apply; wall-clock time grows roughly N/K-fold.

---

## Step 3 — Aggregate findings

The orchestrator emits the aggregate Markdown table back to you (the main agent):

```
| page | role | status | hard_hits | soft_hits | fixes_applied | needs_human_reason |
|------|------|--------|-----------|-----------|---------------|---------------------|
```

Statuses:

- `ok` — page passed clean, no fixes applied
- `fixed` — at least one fix applied, all Hard rules now pass
- `needs_human` — fix attempted but rolled back (rule §4.2), or rule violation requires brand/structure decision outside the rubric's scope
- `render_failed` — Iteration 0 PNG sanity failed (rare; usually means renderer / server issue)
- `prereq_failed` — static checker hadn't been run

Plus a brand-token aggregate at `<project>/.review/brand_review.json` if any §1.1 escalations occurred — review this once at the end of the run, not per page.

---

## Step 4 — Decide next move

For each row in the table:

- `ok` / `fixed` — no action; the SVG has been updated in-place (originals are at `<project>/.review/backup/<page>.iter<N>.svg`)
- `needs_human` — read the page's JSON `needs_human_items[].suggested_fix_summary`, decide with the user whether to apply or defer
- `render_failed` — re-run `visual_review.py` for that page only (`--pages <token>`); if it persists, hand off to manual review
- `prereq_failed` — go back and run `svg_quality_checker.py`

If `brand_review.json` is non-empty, that's a single decision applied across the deck (e.g., bump footer text color from `#6E7681` to `#8B949E` — one change, every page benefits). Do this once, then optionally re-run visual-review for the affected pages only.

After the table is clean, continue to post-processing per [`SKILL.md`](../../SKILL.md) Step 7:

```bash
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

---

## Notes & invariants

- **Single source of truth for rules**: [`references/visual-review.md`](../../references/visual-review.md). This stage file is just the orchestration — never restate or paraphrase rules here.
- **Concurrency**: `visual_review.py` serializes renders via `<project>/.preview/.render.lock`. Subagents must never call the renderer directly without the lock.
- **Iteration budget**: default 1 iteration. Bumping to 2 doubles render cost and roughly triples token cost. Only worth it for high-stakes / final-cut decks.
- **Don't-touch (rubric §3)** is hard-enforced by subagents. If you want the subagent to e.g. change a brand color, that is **out of scope** — make the change manually first, then re-render & re-review.
- **Backups**: every modified SVG has a `.review/backup/<page>.iter<N>.svg` rollback anchor. Restore by `cp`.
- **The rubric is not the designer**: it catches collisions, drift, and rhythm errors — it does not improve a fundamentally weak layout. If 80%+ of pages come back `needs_human`, the design spec or the executor's choice of layout patterns is the root cause, not this stage.
- **Playwright output discipline**: when an agent uses the playwright MCP tool `browser_take_screenshot` directly (outside the `visual_review.py` script), the `filename` parameter is resolved against the CWD (typically the repo root) — passing a bare relative path will create stray directories inside the repository. Always pass an absolute path:
  - One-off probe / ad-hoc inspection → `/tmp/probe-<topic>-<n>.png`
  - Project artifact (replaces what the script would have produced) → `<project_path>/.preview/<page>.png` (absolute)
  - Never write to `<repo>/<anything>.png` or `<repo>/<some_dir>/...` — those are caught by `.gitignore` patterns but the cleanup burden is real

  The `visual_review.py` script handles output paths correctly on its own; this rule only applies to direct playwright MCP usage during interactive exploration or recovery.

---

## Appendix: Iteration loop (opt-in)

Default behavior is single-iteration review: one scan, fix in place, write the report. The full iteration loop in [`references/visual-review.md`](../../references/visual-review.md) §4.1 supports:

1. Iteration 1: scan + fix
2. Re-render via `visual_review.py --pages <token>`
3. Iteration 2: re-verify changed elements + scan for new Hard hits
4. Rollback on any new Hard hit introduced by a fix

To enable, set iteration budget = 2 in the orchestrator prompt (this is a prompt-level instruction to subagents; neither `visual_review.py` nor the harness enforces it). Each added iteration roughly doubles render cost and triples token cost on the affected pages — reserve for final-cut runs only.
