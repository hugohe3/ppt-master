# Modes — Index

A **mode** is the deck's **narrative + persuasion skeleton** — how the argument is organized and advanced across pages. Lock **one mode per deck**; it shapes page sequencing, title voice, page-structure tendencies, and speaker-notes register.

> A mode is *not* a visual style. **Mode = how you argue; visual style = how it looks** (see [`visual-styles/_index.md`](../visual-styles/_index.md)). The two are locked independently — any mode pairs with any visual style (a `pyramid` deck can look `swiss-minimal` or `dark-tech`).

---

## 1. Catalog (4 modes)

Each mode has its own file with: narrative skeleton, page-structure tendencies, speaker-notes register, and a page skeleton example. **Read only the file for the mode you lock** — never glob the directory.

| Mode | Narrative skeleton | Best for |
|---|---|---|
| [`pyramid`](./pyramid.md) | Conclusion first; MECE arguments; every datum carries a comparison | Decision support, analysis, strategy, board / exec reports |
| [`narrative`](./narrative.md) | Story arc — situation → tension → resolution; suspense and turns | Pitches, case studies, brand journeys, fundraising |
| [`instructional`](./instructional.md) | Concept decomposition; step-by-step; parallel exposition | Training, tutorials, explainers, knowledge sharing |
| [`showcase`](./showcase.md) | Visual-led impact; big imagery / numbers; emotional rhythm | Launches, brand reveals, event / promo decks |

---

## 2. Auto-selection — content / audience signal → mode

| Signal | Recommended mode | Alternates |
|---|---|---|
| Strategic decision / analysis / board / investor | `pyramid` | `narrative` |
| Pitch / case study / origin story / campaign arc | `narrative` | `showcase` |
| Course / onboarding / how-to / science explainer | `instructional` | `pyramid` |
| Product launch / brand reveal / event opener / keynote / 发布会 / TED | `showcase` | `narrative` |

> No single signal dominates — read the deck's actual purpose from `c. Key Information`. When two modes fit, follow the **primary** intent of the body pages, not the cover. A data briefing legitimately runs almost entirely `pyramid`; do not force variety.
>
> "Keynote-style" is a *mode* request, not a visual style — it means showcase pacing (one big idea per page, full-bleed hero, reveal rhythm), skinned by whatever visual style fits the brand (`swiss-minimal` clean, `dark-tech` dramatic, `glassmorphism` premium). Don't reach for a "keynote" visual style — there isn't one, by design.

---

## 3. How to use

1. Strategist reads this index at confirmation `d. Layer 1`.
2. Pick one mode from the auto-selection table + the deck's stated purpose.
3. Lock it: write `- mode: <name>` into `spec_lock.md`, record the rationale in `design_spec.md`.
4. Executor reads **only** `modes/<locked-mode>.md` at generation entry — never globs this directory.

**Lock scope**: deck-wide (one mode per deck). Modes are a closed set of narrative skeletons — there is no `custom` mode; if the argument structure is genuinely mixed, pick the mode of the body pages and let individual pages vary within it.
