---
description: Conditional isolated multimodal review of bounded web-image thumbnail pages.
---

# Web Image Review Stage

> Supporting Generate stage for choosing from thumbnail pages already prepared by the web-image acquisition path. It reviews pixels only: it never searches, downloads, changes the locked image intent, or writes project artifacts.

## When to Run

After `--save-candidates` has produced `Needs-Selection` rows and before any `--promote` command.

| Review capability | Action |
|---|---|
| An isolated worker can inspect the declared local images | Dispatch exactly one reviewer for all pending sheets in the current batch; reuse it for later candidate pages of the same run when the host supports follow-up messages — never one reviewer per row |
| Only the active image owner can inspect images | Read this stage and review the same batch locally |
| No available context can inspect images | Skip; use the strict metadata-only acquisition path |

---

## Execution Context

The active image owner keeps query, search, pagination, promotion, status, and provenance ownership and supplies the reviewer only this stage's absolute path plus, per row: the resource filename or stable row identifier; the exact locked `Reference` and `Crop Policy`; current page, `has_more_candidates`, and `next_candidate_page`; absolute `review_sheet.jpg` and `candidates.json` paths. The reviewer reads this file completely, inspects only the declared sidecars and images, reads no other project or prompt files, runs no network request, command, or write, and returns `blocked` with the exact reason when a path is unreadable or image inspection is unavailable.

---

## Review Contract

| Order | Gate |
|---:|---|
| 1 | Reject unless `license_tier` is `no-attribution` or `attribution-required`; reject unreadable previews or known dimensions that cannot serve the placement |
| 2 | Confirm the exact subject or identity; `visual-verification-required` passes only when the pixels establish the missing evidence |
| 3 | Check orientation, focal placement, crop safety, and usable quiet region against the locked intent |
| 4 | Check the requested view, action, and mood |
| 5 | Among passing candidates, prefer lower expected crop loss and higher usable resolution, then no-attribution |

**Mandatory — bounded detail inspection**: triage with `review_sheet.jpg`; open an individual `review/candidate_NN.jpg` only when exact identity or a fine detail cannot be resolved from the sheet, never bulk-open every candidate.

**Hard rule — no least-bad promotion**: select only a candidate that passes every gate; otherwise return `no-pass` without weakening the locked Reference or Crop Policy.

---

## Receipt and Hand-off

Return one compact table, no embedded images, under 200 words:

```markdown
| row | decision | candidate | reason | next |
|---|---|---|---|---|
| <id> | selected / no-pass / blocked | candidate_NN.jpg / — | <short evidence> | promote / next-page / pool-exhausted / repair-input |
```

`selected` names exactly one candidate from the row's current page; `no-pass` uses `next-page` when `has_more_candidates` is true, otherwise `pool-exhausted`. The image owner validates every selected filename against `candidates.json`, runs `--promote`, and verifies the downloaded original's dimensions and provenance; a no-pass row advances to the next ranked page before query replacement; an invalid receipt returns to the same reviewer and never authorizes an arbitrary promotion.
