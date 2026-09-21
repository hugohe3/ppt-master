---
description: Optional main-pipeline stage for reviewing and revising the complete Design Spec before lock authoring and generation.
---

# Refine Spec Stage

> **Opt-in Generate-PPTX stage.** Default writes `design_spec.md` + `spec_lock.md` and proceeds. With explicit refinement, produce and audit the complete Design Spec, then **stop before the lock** for unrestricted user review.

The confirmation stage settles design directions as abstract recommendations; this pass lets the user revise the concrete spec produced from them — most valuable for a zero-background user, who judges a finished spec far better than up-front recommendations, and usually wants to adjust the content outline (§IX).

## When to Run

Only when the user explicitly asks to refine / review / revise the spec before generation ("produce the spec first, let me review", "send me the spec to confirm, I'll edit it", "draft the full plan, I want to adjust it, then generate"). **Default is OFF**: Strategist surfaces it as one short opt-in line inside the confirmation stage ([`generate-pptx`](../generate-pptx.md) Step 4); without a request the spec is written in one go. **Prerequisite**: the confirmation stage is settled; this pass never reopens it.

---

## Step 1: Produce the complete Design Spec

Run [`generate-pptx`](../generate-pptx.md) Step 4 through the complete `design_spec.md` (§I–X) and the initial Gate 1 audit, reading relevant `sources/` so §IX carries facts, not skeleton points.

**Hard rule — no lock before approval**: do not create, update, use, or validate `spec_lock.md` during review; on a resumed project a prior lock is stale derived state until Gate 2 resynchronizes it after approval.

---

## Step 2: ⛔ HARD STOP — present, discuss, and revise

Present the one project `design_spec.md` and wait for explicit revision or approval — no second draft, parallel summary, fixed-field questionnaire, scores, or field-by-field confirmation. The user may revise any part, any number of rounds; discuss in prose and let the user drive.

**Review surface follows the confirmation surface** ([`confirm-surface.md`](../../references/confirm-surface.md) §1): on the page branch launch the review page; on the chat or delegated branch, after a switch to chat, or when the launch fails, present the file in chat. The page is a derived view of that one file — one page per `##` section and per §IX slide — never a second draft.

```bash
python3 ${SKILL_DIR}/scripts/spec_review/server.py <project_path> --daemon
```

Report the actual URL from the launch output (remote host: `--no-browser` plus port forwarding, [`spec_review.md`](../../scripts/docs/spec_review.md)) and tell the user in one short message: **Direct edit** rewrites one block of the same file on **Apply changes**; **Annotate** leaves a per-page or global comment for anything needing judgement and for every page added, dropped, or moved; return to chat to have comments applied or to approve. Then stop — never wait on the page; approval is given only in chat.

**Apply a review round** when the user returns from the page:

1. `spec_review/server.py <project_path> --hold on` — the page cannot write while the file is revised. Skip the hold when the page is no longer running (idle timeout, new session): the sidecars still carry the to-do list.
2. `python3 ${SKILL_DIR}/scripts/check_spec_annotations.py <project_path>` — the to-do list: pending comments plus blocks the user edited directly since the last round. Read those blocks from disk; the copy in context is stale.
3. A direct edit is a user revision: keep its wording and reconcile what it supersedes elsewhere. Apply each comment to the file on disk, then clear it with `--applied <id>`; a comment changed since listing stays pending — list again.
4. `check_spec_annotations.py <project_path> --ack-edits`, `--hold off`, then report what changed and what stays open.

**Reference — review lenses, not a checklist**: raise these in plain language as directions, never numbers (no HEX, px, ratios, page quotas, or grades): outline — logical build, information density, one idea per page, register matched to the audience, hook and payoff, chapter balance; color — fit to mood and audience, enough hierarchy and contrast; typography — clear contrast or clean concord between title and body, legible size hierarchy, character matched to the visual style; layout — structure following each page's information weight rather than one uniform symmetric grid; icon/image — one consistent icon character, images that serve the content; page rhythm — `anchor` / `dense` / `breathing` tracking the narrative. They overlap what the confirmed `mode`, visual style, and §6.1 already shape; they are discussion angles, not permission to redo a decision without the user's explicit revision.

**Revise one Design Spec only**: apply each round incrementally; affected decisions supersede earlier values while unaffected confirmed decisions and cross-section coherence stay intact. Do not regenerate the document for a local change, rewrite it from the copy in context, or touch lock anchors. After a changed reuse/prototype decision, repeat the [`strategist-template.md`](../../references/strategist-template.md) preflight before approval (`style` later locks flat; `mirror` / `layout` require a complete structured contract; Gate 2 derives structure mappings; legacy prototypes stay unselectable). Iterate until explicit approval.

---

## Step 3: Approve and author the lock

After explicit approval, apply any pending review round and end it with `spec_review/server.py <project_path> --shutdown` instead of `--hold off` — no edit lands between approval and the lock — then return to [`generate-pptx`](../generate-pptx.md) Step 4 Gate 2: author or resynchronize `spec_lock.md` once from the approved Design Spec plus current context, validate, then continue to Step 5 or Step 6. Do not reopen `result.json`.

> This stage inserts a review-and-revise checkpoint between Gate 1 and Gate 2; [`strategist.md`](../../references/strategist.md) and [`generate-pptx`](../generate-pptx.md) remain authoritative for content and sequencing.
