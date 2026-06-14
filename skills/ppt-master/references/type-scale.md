# Type Scale — Reference (not a constraint)

> A reference the model *draws on* when sizing text, not a rule it must obey.
> Part of the direction in #163: visual guidance as soft reference + personal
> feedback memory, not fixed quotas. This file is one focused slice of that —
> deliberately written in the softer register #163 proposes.

## The ladder

Anchor every size on the page's `body` size; the rest are ratios of it. These are
the sizes the model reaches for *first* — defaults that read as intentional because
they share one ratio family — **not a closed set**.

| Role | Typical px (body ≈ 18) | Ratio to body |
|------|------------------------|---------------|
| Data label / caption | 13–14 | ~0.75× |
| Body | 18 | 1× |
| Subtitle / section label | 22 | ~1.2× |
| Page title | 28 | ~1.5× |
| Slide title | 36 | ~2× |
| Cover / hero | 44 | ~2.4× |
| KPI hero number | 64–72 | ~3.5–4× |

> **Why a ladder at all** (the rationale, so the model *prefers* it — not a ban):
> when sizes drift to arbitrary values (17, 19, 24, 29 …) the implied proportion
> breaks and the page reads as "placed by hand, not designed." So lean on the
> ladder. But deviate when it genuinely reads better: a 20px caption on a
> data-dense page is fine, and a deck whose `body` is 16 or 24 shifts the whole
> ladder with it.

## Self-check (reflection, not a gate)

After drafting a page, read it back: does the size hierarchy still separate roles
clearly, and does each deviation from the ladder earn its place? Adjust if not.
There is **no score and no pass/fail threshold** — the model reflects and refines;
it does not "fail under 60 and regenerate." A rubric that forces regeneration would
be writing code where we want generative judgment.

## Personalization (where this is headed — see #163)

The strongest version of this isn't a fixed table at all: it's the sizes *this
user* has approved on past pages of the same kind, surfaced as a soft preference.
The ladder above is the cold-start default; a user's own approved exemplars
override it over time. That keeps the guidance personal and generative rather than
a universal rule imposed on every deck.
