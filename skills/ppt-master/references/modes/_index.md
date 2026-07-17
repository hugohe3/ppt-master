# Modes — Index

A **mode** is the deck's **narrative + persuasion skeleton** — how the argument is organized and advanced across pages. Lock **one mode per deck**; it shapes page sequencing, title voice, page-structure tendencies, and speaker-notes register.

> A mode is *not* a visual style. **Mode = how you argue; visual style = how it looks** (see [`visual-styles/_index.md`](../visual-styles/_index.md)). The two are locked independently — any mode pairs with any visual style (a `pyramid` deck can look `swiss-minimal` or `dark-tech`).

---

## 1. Catalog (5 modes)

Each mode has its own file with: narrative skeleton, page-structure tendencies, speaker-notes register, and a page skeleton example. **Read only the file for the mode you lock** — never glob the directory.

| Mode | Narrative skeleton | Best for |
|---|---|---|
| [`pyramid`](./pyramid.md) | Conclusion first; MECE arguments; every datum carries a comparison | Decision support, analysis, strategy, board / exec reports |
| [`narrative`](./narrative.md) | Story arc — situation → tension → resolution; suspense and turns | Pitches, case studies, brand journeys, fundraising |
| [`instructional`](./instructional.md) | Concept decomposition; step-by-step; parallel exposition | Training, tutorials, explainers, knowledge sharing |
| [`showcase`](./showcase.md) | Visual-led impact; big imagery / numbers; emotional rhythm | Launches, brand reveals, event / promo decks |
| [`briefing`](./briefing.md) | Neutral, complete, scannable; topic titles, even weight, no thesis | Status updates, reference decks, catalogs, meeting packs, FAQs |

> The five are **argument strategies, not a taxonomy of communication purposes**. A presentation may inform + align + request a decision at once; that composite intent stays as open prose in the Stage-1 communication contract. Stage 2 chooses the mode that best carries the dominant body-page spine, or one concrete `custom` act sequence when no preset can serve the stated priority / sequence.
>
> **A mode is a lens, not a mandate over the user's own structure.** When the user brings their own outline, it is authoritative: transcribe it into `design_spec.md §IX` as given — page order and titles preserved — and let the mode govern only voice / register and page-internal treatment. A mode never reorders a user's pages or rewrites their given titles (mode is Reference-strength; a user-authored outline is exactly the override). When the user gives no structure, the mode does the structural lifting. To lay an outline out with the least reshaping, `briefing` imposes the lightest skeleton.

---

## 2. Auto-selection — communication contract + source signal → mode

| Contract / source signal | Recommended mode | Alternates |
|---|---|---|
| Decision / recommendation outcome; analysis, board, investor; criteria and trade-offs must land | `pyramid` | `narrative` |
| Persuasion or mobilization lands through a case, tension, transformation, or origin arc | `narrative` | `showcase`, `pyramid` |
| Understanding or capability must build step by step; course, onboarding, how-to, explainer | `instructional` | `pyramid`, `briefing` |
| Attention / emotion / launch moment is primary; sparse presenter-led delivery | `showcase` | `narrative` |
| Complete reference, status, record, hand-off, FAQ, meeting pack; no thesis dominates | `briefing` | `pyramid`, `instructional` |

> No keyword decides the mode. Read `communication_intent`, `audience_outcome`, `core_message`, delivery context / afterlife, source texture, and any user-authored outline together. When several purposes coexist, follow the dominant **argument movement of the body pages**, not the cover and not the first purpose word. A data review can legitimately run almost entirely `pyramid`; a progress report whose durable hand-off matters more than persuasion may stay `briefing`.

**Close calls** — the genuinely adjacent pairs; every other pair is far enough apart that the auto-selection signal decides.

| Torn between | …the first when | …the second when |
|---|---|---|
| `pyramid` / `briefing` | it must land a recommendation — conclusion-first, every number compared | it must inform completely without arguing — topic titles, even weight |
| `narrative` / `pyramid` | the point lands through a story arc, tension → resolution | the point lands as a conclusion stated up front, then supported |
| `narrative` / `showcase` | an argument travels through the story | presence leads — minimal copy, one big visual per page |
| `instructional` / `briefing` | the goal is to build understanding step by step | the goal is to lay out a complete reference to scan |

> "Keynote-style" is a *mode* request, not a visual style — it means showcase pacing (one big idea per page, full-bleed hero, reveal rhythm), skinned by whatever visual style fits the brand (`swiss-minimal` clean, `dark-tech` dramatic, `glassmorphism` premium). Don't reach for a "keynote" visual style — there isn't one, by design.

---

## 3. How to use

1. Strategist reads this index at confirmation `d. Layer 1`.
2. Pick one mode from the auto-selection table + the confirmed communication contract and source structure.
3. Lock it: write `- mode: <name>` into `spec_lock.md`, record the rationale in `design_spec.md`.
4. Executor reads **only** `modes/<locked-mode>.md` at generation entry — never globs this directory.

**Lock scope**: deck-wide (one mode per deck). The five are the catalog you select from; if the structure is genuinely mixed, pick the mode of the body pages and let pages vary within it, or recommend a `custom` blend (§4). Recommend the best fit; the user confirms.

---

## 4. Escape hatch — `custom`

`custom` holds **any bespoke narrative direction the five don't give as-is** — and what *kind* of thing it is doesn't matter. It might be a nameable cadence (dialectic 正反合, myth-vs-reality, countdown / Top-N, Socratic), a deliberate multi-act fusion of several modes, or the user's own feel for how the deck should carry (confrontational here, detached there). Don't try to taxonomize it.

**Either side may originate it.** The user can ask for it directly; or the Strategist — as the deck's strategist — may **recommend** `custom` when a bespoke direction (often a fusion of two modes) genuinely serves the deck better than any single preset. Like every confirmation, it's a recommendation the user confirms or overrides — and the recommendation must **spell the custom out in plain language** (what the cadence / fusion / posture actually is), never present the bare token `custom`, so the user confirms something legible. Either way, the Strategist **crystallizes the intent into a `- mode_behavior:` paragraph** — concrete enough that the Executor can follow it per page (the act sequence or posture shifts, the title voice, the page rhythm, the notes register). Set `- mode: custom` in `spec_lock.md` with that sibling line; the Executor follows the prose in place of a preset file. (This records the intent so it survives 20 pages of generation — the Executor only ever reads `spec_lock.md`, never the chat.)

> **One value per deck — fusion is *one* `custom`, not several modes.** A deck always locks a single `mode`. A multi-mode blend is expressed as **one** `mode: custom` whose `mode_behavior` paragraph describes the acts — never by locking several modes.
>
> **First ask whether it's really fusion.** A locked mode is a *tendency*, not a cage: a `narrative` deck can still carry one analytical (pyramid-style) page, an `instructional` deck one showcase reveal — that is leaning within a dominant mode, and needs **no** `custom`. Reach for `custom` only when there is genuinely no single dominant spine.

**The one thing to avoid**: reaching for `custom` as a *dodge* — defaulting to it because picking among the five takes judgment. When a preset genuinely fits, lock the preset; propose `custom` when a bespoke direction earns its place, not to avoid choosing. (And a user-stated direction is authoritative the same way a user-supplied outline is — see the lens-not-mandate note in §1.)
