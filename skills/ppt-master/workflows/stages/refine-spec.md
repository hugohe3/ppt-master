---
description: Optional main-pipeline stage for reviewing and revising the complete spec before generation.
---

# Refine Spec Stage

> **Opt-in Generate-PPTX stage** for spec review. The default pipeline writes `design_spec.md` + `spec_lock.md` and auto-proceeds. When the user explicitly asks to refine the spec, the Strategist produces the full spec first, then **stops** — the user reviews and revises any part of it (outline, color, typography, layout, image strategy, page rhythm, …) before any image generation or SVG work begins.

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

## Step 1: Produce the full spec

Run the default Strategist output exactly as [`generate-pptx`](../generate-pptx.md) Step 4 specifies: write `design_spec.md` (§I–X) and `spec_lock.md`. Read the relevant `sources/` files so the content outline (`§IX`) carries real facts, not skeleton points. Nothing special here — this is the normal spec, just produced under the knowledge that the user is about to review it.

---

## Step 2: ⛔ HARD STOP — present, discuss, and revise

Present the produced spec to the user and **wait for explicit revision or approval before doing anything else**. This is a conditional BLOCKING point that exists only on this opt-in path; the default pipeline keeps its "auto-proceed after the Strategist confirmation stage" discipline untouched.

The user may revise **any part of the spec**, not just the outline — content outline, color, typography, layout, icon plan, image strategy, page rhythm. Discuss in **prose**; do not emit a scored rubric or per-axis grades (mechanical scorecards are against project convention). When useful, point out things worth a second look — but let the user drive.

**Reference — review lenses, not a checklist or score**: raise these in plain language to surface what is worth discussing. They name a *direction*, never a number — never convert any into HEX values, px sizes, ratios, page quotas, or grades.

- *Outline*: logical clarity (do the points build on each other), information density (right amount per page — nothing padded or crammed), focus (each page lands one idea), register (spoken vs formal, matched to the audience), emotional resonance (a hook to open, a payoff to close), chapter balance (page budget not lopsided).
- *Color*: does the scheme fit the content's mood and audience, and is there enough hierarchy and contrast to read comfortably — not which exact HEX.
- *Typography*: do title and body form a clear contrast or a clean concord, is the size hierarchy legible, does the type character match the visual style — not which px.
- *Layout*: does structure follow each page's information weight, or does it fall back to one uniform symmetric grid (the "AI-generated" look).
- *Icon / image*: one consistent icon character throughout; images that serve the content (hero / atmosphere used on purpose) rather than decorate.
- *Page rhythm*: do `anchor` / `dense` / `breathing` track the narrative, or is everything flatly dense.

These overlap with what the locked `mode`, visual style, and §6.1 already shape — treat them as discussion angles to surface what is worth talking about, not a second pass to redo.

**Keep both files in sync on every change.** Any revision the user approves must land in both `design_spec.md` and `spec_lock.md`; on divergence `spec_lock.md` wins (see [`strategist.md`](../../references/strategist.md) §6.2). Iterate as many rounds as the user wants. The loop ends only when the user explicitly approves the spec.

**Re-run the route/template preflight after reuse revisions.** If the user changes `template_reuse_scope`, `template_adherence`, `page_layouts`, the Master/Layout definition roster, or any `page_pptx_layouts` assignment, repeat the preflight in [`strategist-template.md`](../../references/strategist-template.md) before approval and hand-back. Switching to `style` rewrites the route to `pptx_structure.mode: flat` and removes all structure mappings/adherence; switching to `mirror` / `layout` restores a complete structured contract. Every newly selected structured prototype must declare root Master/Layout identity, direct atomic Master/Layout visuals, and valid top-level slot groups with positive bounds plus one compatible carrier or explicit composite `object` proxy. A zero-slot Layout is valid. Update `pptx_masters`, unique `pptx_layouts` definitions, and complete `page_pptx_layouts` assignments in both artifacts immediately. A legacy prototype is not selectable; create a current workspace through [`create-template`](../create-template.md) before refinement.

---

## Step 3: Hand back

Once the user approves, `design_spec.md` and `spec_lock.md` both reflect the final, revised state. Return to [`generate-pptx`](../generate-pptx.md): Step 5 when any `ai` / `web` rows require acquisition, otherwise Step 6.

> Note: this stage does NOT duplicate Strategist content. It only inserts a review-and-revise checkpoint between spec production and the rest of the pipeline. [`strategist.md`](../../references/strategist.md) and [`generate-pptx`](../generate-pptx.md) remain authoritative for spec content and route sequencing.
