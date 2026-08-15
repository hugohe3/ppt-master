---
description: Conditional isolated multimodal review of bounded web-image thumbnail pages.
---

# Web Image Review Stage

> Supporting Generate stage for choosing from thumbnail pages already prepared
> by the web-image acquisition path. It reviews pixels only: it never searches,
> downloads, changes the locked image intent, or writes project artifacts.

## When to Run

| Review capability | Action |
|---|---|
| An isolated worker can inspect the declared local images | Dispatch exactly one reviewer for all pending sheets in the current acquisition batch |
| Only the active image owner can inspect images | Read this stage and review the same batch locally |
| No available context can inspect images | Skip this stage and use the strict metadata-only acquisition path |

Run after `--save-candidates` has produced `Needs-Selection` rows and before any
`--promote` command. When the host supports follow-up messages, reuse the same
reviewer for later candidate pages in that acquisition run; never dispatch one
reviewer per resource row.

---

## Execution Context

**Default — isolate thumbnail pixels when available**: The active image owner
retains query, search, pagination, promotion, status, and provenance ownership.
Supply the reviewer only this stage's absolute path and these per-row records:

| Input | Required value |
|---|---|
| Row identity | Resource filename or stable batch-row identifier |
| Acceptance intent | Exact locked `Reference` and `Crop Policy` |
| Candidate state | Current page, `has_more_candidates`, and `next_candidate_page` when present |
| Local evidence | Absolute `review_sheet.jpg` and `candidates.json` paths |

The isolated reviewer reads this file completely, then inspects only the
declared sidecars and review images. It does not read `image-base.md`,
`image-searcher.md`, the Design Spec, the lock, or source files. It runs no
network request, command, or project write. If any declared path is unreadable
or image inspection is unavailable, return `blocked` with the exact reason.

---

## Review Contract

Apply the gates in order for every row:

| Order | Gate |
|---:|---|
| 1 | Reject a candidate unless its `license_tier` is `no-attribution` or `attribution-required`; also reject unreadable previews or known dimensions that cannot serve the planned placement |
| 2 | Confirm the exact subject or identity; `visual-verification-required` passes only when the pixels establish the missing identity evidence |
| 3 | Check orientation, focal placement, crop safety, and usable quiet region against the locked intent |
| 4 | Check the requested view, action, and mood |
| 5 | Among passing candidates, prefer lower expected crop loss and higher usable resolution, then no-attribution |

**Mandatory — bounded detail inspection**: Triage with `review_sheet.jpg`.
Open an individual `review/candidate_NN.jpg` only when exact identity or a fine
detail cannot be resolved from the sheet; never bulk-open every candidate.

**Hard rule — no least-bad promotion**: Select only a candidate that passes all
applicable gates. When none passes, return `no-pass`; do not weaken the locked
Reference or Crop Policy.

---

## Receipt and Hand-off

Return one compact table and no embedded images:

```markdown
| row | decision | candidate | reason | next |
|---|---|---|---|---|
| <id> | selected / no-pass / blocked | candidate_NN.jpg / — | <short evidence> | promote / next-page / pool-exhausted / repair-input |
```

For `selected`, name exactly one candidate from that row's current page. For
`no-pass`, use `next-page` when `has_more_candidates` is true; otherwise use
`pool-exhausted`. Keep the entire chat receipt under 200 words.

The active image owner validates every selected filename against
`candidates.json`, runs `--promote`, and verifies the downloaded original's
readable dimensions and provenance. A no-pass row advances to the next ranked
page before query replacement. An invalid receipt returns to the same reviewer
for correction; it never authorizes an arbitrary promotion.
