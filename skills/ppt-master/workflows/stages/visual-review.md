---
description: Optional quality-gate stage for per-page rubric-based visual review.
---

# Visual Review Stage

> Optional, opt-in Generate-PPTX quality stage: AI subagents visually self-check each rendered slide against the fixed rubric in [`references/visual-review.md`](../../references/visual-review.md) and apply atomic position/spacing fixes or flag `needs_human`. When an installed Style exists, its `Review Focus` is supplemental acceptance context. Never touches brand decisions, layout structure, or other files. Context-independent — invokable in a fresh chat with only `<project_path>`.

## When to Run

Only when the user explicitly requests visual review — never auto-invoked from model capability or deck size — after Executor has finished all pages and `svg_quality_checker.py` has passed, before `finalize_svg.py` / `svg_to_pptx.py`. Run [`verify-charts`](./verify-charts.md) first for decks with data charts; this stage covers rhythm, collision, and alignment, not coordinate math. Do not run when `svg_output/` is incomplete, the static checker has not passed, or the user is already in a `live-preview` annotation loop.

**Token cost**: each batch subagent re-reads the rubric + `design_spec.md` + `spec_lock.md` (+ Style Review Focus) and processes K SVG+PNG pairs — on the order of 100–150K additional input tokens for a 20-page deck at K=5.

---

## Prerequisites

```bash
pip install playwright && python3 -m playwright install chromium          # PNG renderer
python3 skills/ppt-master/scripts/svg_editor/server.py <project_path> --no-browser   # live-preview server (skip if already running)
```

The renderer does not auto-start the server; it discovers the port from `live_preview/lock.json` (or an explicit `--server-url`) and validates `/api/health` against the target project. Playwright, not cairosvg, because cairo has no font-fallback chain and renders CJK as tofu; chromium output matches the live-preview browser.

---

## Step 1 — Pre-render all PNGs

```bash
python3 skills/ppt-master/scripts/visual_review.py <project_path>
```

Writes one PNG per page to `<project_path>/.preview/<page>.png`, sized from the root `viewBox` with icons inlined and images resolved; each successful record carries the exact canvas and raster dimensions (contract and exit codes in [`svg-pipeline.md`](../../scripts/docs/svg-pipeline.md#visual_reviewpy)).

**Mandatory — normalize partial renders before dispatch**: dispatch only records with `"ok": true`, `"all_background": false`, and a complete `canvas`. For every other page the main agent adds a `render_failed` row to the aggregate with the renderer error or blank-surface reason (a blank surface usually means a broken `<use>` reference or missing image asset). Exit `2` or `3` stops dispatch; exit `4` may review the successful subset, but the stage cannot finish until every failed page is retried or handed off per Step 4.

---

## Step 2 — Spawn the review team

Before dispatch, look for `<project>/templates/design_spec.style.*.md`; for each, read only its `## VII. Review Focus` once and include those checks in every batch prompt — this lookup never triggers the stage and cannot weaken the rubric or widen edit permissions.

```text
TeamCreate(team_name="visual-review-<project>", agent_type="orchestrator")
Agent(team_name="visual-review-<project>", subagent_type="general-purpose", name="orchestrator", prompt=<orchestrator-prompt>)
```

The orchestrator partitions N pages into batches of ≤ K (default 5) and spawns one subagent per batch in parallel; each subagent reads the fixed inputs once, then iterates its pages. The orchestrator prompt is self-contained and the single place stating dispatch shape, batch size, and forbid lists; it carries (absolute paths): `<project_path>`; the full page list with `page_role` and each successful renderer record's `canvas` (parse `design_spec.md` §IX — **fixed compatibility default**: a `design_spec.md` without §IX uses `content` for every page and flags it in the report; a missing `design_spec.md` is restored through [`failure-recovery.md`](../governance/failure-recovery.md) §3 first); batch size K (10 for token-sensitive large decks, 3 for high-fidelity short decks — rubric §6.1); iteration budget (default 1; 2 only for final-cut runs — see the appendix); the rubric path; the Style Review Focus excerpt with its wording and source path when found; the dispatch contract reference (rubric §6); and the subagent forbid list (no edits to other pages, `design_spec.md`, `spec_lock.md`, `templates/`, `animations.json`, `image_prompts.json`, `images/`).

**Host compatibility**: `TeamCreate` and `SendMessage` are Claude-Code primitives; on other hosts the main agent processes the same batches sequentially with the same prompts — token savings persist, wall-clock grows roughly N/K-fold.

---

## Step 3 — Aggregate findings

The orchestrator returns `| page | role | status | hard_hits | soft_hits | fixes_applied | needs_human_reason |`, where `ok` = clean, `fixed` = fixes applied and Hard rules pass, `needs_human` = a fix was rolled back (rubric §4.2) or the violation needs a brand/structure decision, `render_failed` = iteration-0 sanity failed, `prereq_failed` = static checker not run — plus `<project>/.review/brand_review.json` when §1.1 escalations occurred, reviewed once at the end.

---

## Step 4 — Decide next move

`ok` / `fixed` — nothing to do; the SVG was updated in place with originals at `<project>/.review/backup/<page>.iter<N>.svg`. `needs_human` — read `needs_human_items[].suggested_fix_summary` and decide with the user. `render_failed` — re-run `visual_review.py --pages <token>`; if it persists, hand off to manual review. `prereq_failed` — run `svg_quality_checker.py`. A non-empty `brand_review.json` is one deck-wide decision (e.g. bump a footer token deck-wide); apply it once, then optionally re-review the affected pages. When the table is clean, continue to [`generate-pptx`](../generate-pptx.md) Step 7.

---

## Notes & invariants

- The rubric is the single source of rules; this file is orchestration only and never restates them.
- Don't-touch (rubric §3) is hard-enforced: a brand color change is out of scope — make it manually, then re-render and re-review.
- The rubric catches collisions, drift, and rhythm errors, not a fundamentally weak layout; if 80%+ of pages come back `needs_human`, the root cause is the Design Spec's pattern selection or Executor geometry.
- Direct playwright MCP `browser_take_screenshot` resolves `filename` against the CWD (usually the repo root): always pass an absolute path — `/tmp/probe-<topic>-<n>.png` for ad-hoc probes, `<project_path>/.preview/<page>.png` for project artifacts; never write under the repository. `visual_review.py` handles its own paths.

---

## Appendix: Iteration loop (opt-in)

Default is one iteration. With budget 2 in the orchestrator prompt (a prompt-level instruction; neither the script nor the harness enforces it): iteration 1 scan + fix → re-render via `visual_review.py --pages <token>` → iteration 2 re-verify changed elements and scan for new Hard hits, rolling back any fix that introduced one (rubric §4.1–§4.2). Each added iteration roughly doubles render cost and triples token cost; reserve for final-cut runs.
