---
description: Optional main-pipeline stage for reviewing and revising the complete Design Spec before lock authoring and generation.
---

# Refine Spec Stage

> **Opt-in Generate-PPTX stage**. Default writes `design_spec.md` + `spec_lock.md` and proceeds. With explicit refinement, produce and audit the complete Design Spec, then **stop before the lock** for unrestricted user review/revision.

This stage is **conditional**, same shape as the split-mode choice: it never fires on its own and the default path is unchanged. The Strategist confirmation stage settles design directions up front as abstract recommendations; this pass lets the user revise the **concrete spec** the Strategist produced from them. It is most valuable for a zero-background user, who can judge a finished spec far better than the up-front recommendations — and the spec's content outline (`§IX`) is usually what they most want to adjust.

## When to Run

The user **explicitly asks** to refine / review / revise the spec before generation. Recognize any of:

| Pattern | Example |
|---|---|
| "refine the spec / review the spec first" | "produce the spec first, let me review before slides" |
| "let me revise the spec, then continue" | "send me the spec to confirm, I'll edit it" |
| Any request to inspect/iterate the design spec before generation | "draft the full plan, I want to adjust it, then generate" |

**Default is OFF.** Strategist surfaces this option as one short opt-in line inside the Strategist confirmation stage (see [`generate-pptx`](../generate-pptx.md) Step 4). No request → the spec is written in one go and the pipeline auto-proceeds as usual; this stage never starts.

**Prerequisite**: the Strategist confirmation stage is settled (mode + visual style + the rest). This pass revises the spec produced from that stage; it does not re-open the confirmation stage itself.

---

## Step 1: Produce the complete Design Spec

Run [`generate-pptx`](../generate-pptx.md) Step 4 through the complete `design_spec.md` (§I–X) and initial Gate 1 audit. Read relevant `sources/` so §IX carries facts, not skeleton points.

**Hard rule — no lock before approval**: Do not create, update, use, or validate `spec_lock.md` during review. On a resumed project, any prior lock is stale derived state until Gate 2 resynchronizes it after approval.

---

## Step 2: ⛔ HARD STOP — present, discuss, and revise

Present the Design Spec and **wait for explicit revision or approval before anything else**. Review the one project `design_spec.md` in chat; do not create a second draft, parallel summary, or fixed-field questionnaire.

The user may revise **any part of the spec** and request any number of changes per round. Discuss in **prose**; do not emit scores or force field-by-field confirmation. Let the user drive.

**Reference — review lenses, not a checklist or score**: raise these in plain language to surface what is worth discussing. They name a *direction*, never a number — never convert any into HEX values, px sizes, ratios, page quotas, or grades.

- *Outline*: logical clarity (do the points build on each other), information density (right amount per page — nothing padded or crammed), focus (each page lands one idea), register (spoken vs formal, matched to the audience), emotional resonance (a hook to open, a payoff to close), chapter balance (page budget not lopsided).
- *Color*: does the scheme fit the content's mood and audience, and is there enough hierarchy and contrast to read comfortably — not which exact HEX.
- *Typography*: do title and body form a clear contrast or a clean concord, is the size hierarchy legible, does the type character match the visual style — not which px.
- *Layout*: does structure follow each page's information weight, or does it fall back to one uniform symmetric grid (the "AI-generated" look).
- *Icon / image*: one consistent icon character throughout; images that serve the content (hero / atmosphere used on purpose) rather than decorate.
- *Page rhythm*: do `anchor` / `dense` / `breathing` track the narrative, or is everything flatly dense.

These overlap with what the confirmed `mode`, visual style, and §6.1 already shape — treat them as discussion angles to surface what is worth talking about, not permission for the Strategist to redo a decision without the user's explicit revision.

**Revise one Design Spec only**: Apply each user-requested round incrementally to `design_spec.md`; affected decisions supersede earlier values, while unaffected confirmed decisions and cross-section coherence remain intact. Do not regenerate the document for a local change or touch lock anchors. Iterate until explicit approval.

**Re-run the route/template preflight after reuse revisions.** For changed reuse/prototype decisions, repeat [`strategist-template.md`](../../references/strategist-template.md) preflight before approval. `style` later locks flat; `mirror` / `layout` require a complete structured contract. Update only human-facing Design Spec decisions during review; Gate 2 derives structure mappings. Legacy prototypes remain unselectable.

---

## Step 3: Approve and author the lock

After explicit approval, return to [`generate-pptx`](../generate-pptx.md) Step 4 Gate 2. Author or resynchronize `spec_lock.md` once from the approved Design Spec plus current context, validate, then continue to Step 5 or Step 6. Do not reopen `result.json`.

> Note: this stage does NOT duplicate Strategist content. It inserts a review-and-revise checkpoint between Design Spec Gate 1 and lock Gate 2. [`strategist.md`](../../references/strategist.md) and [`generate-pptx`](../generate-pptx.md) remain authoritative for artifact content and route sequencing.
