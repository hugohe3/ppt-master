# Modes — Index

A **mode** is the deck's **narrative + persuasion skeleton** — how the argument is organized and advanced across pages. Lock **one mode per deck**; it shapes page sequencing, title voice, page-structure tendencies, and speaker-notes register.

> A mode is *not* a visual style. **Mode = how you argue; visual style = how it looks** (see [`visual-styles/_index.md`](../visual-styles/_index.md)). The two are locked independently — any mode pairs with any visual style (a `pyramid` deck can look `swiss-minimal` or `dark-tech`).

---

## 1. Catalog (5 modes)

Each mode has its own file with: narrative skeleton, page-structure tendencies, speaker-notes register, and a page skeleton example. A preset lock reads that one file. A catalog-based `custom` reads every preset named in `mode_references`; a novel `custom` may omit references. Never glob the directory.

| Mode | Narrative skeleton | Best for |
|---|---|---|
| [`pyramid`](./pyramid.md) | Conclusion first; MECE arguments; every datum carries a comparison | Decision support, analysis, strategy, board / exec reports |
| [`narrative`](./narrative.md) | Story arc — situation → tension → resolution; suspense and turns | Pitches, case studies, brand journeys, fundraising |
| [`instructional`](./instructional.md) | Concept decomposition; step-by-step; parallel exposition | Training, tutorials, explainers, knowledge sharing |
| [`showcase`](./showcase.md) | Visual-led impact; big imagery / numbers; emotional rhythm | Launches, brand reveals, event / promo decks |
| [`briefing`](./briefing.md) | Neutral, complete, scannable; topic titles, even weight, no thesis | Status updates, reference decks, catalogs, meeting packs, FAQs |

> The five are **argument strategies, not a taxonomy of communication purposes**. A presentation may inform + align + request a decision at once; that composite intent stays as open prose in the Stage-1 communication contract. Stage 2 chooses the mode that best carries the dominant body-page spine, or one concrete `custom` act sequence when no preset can serve the stated priority / sequence.
>
> **A mode is a lens, not a mandate over an explicitly preserved structure.** Apply the confirmed `content_divergence` to a user-supplied outline. An ordinary source outline is a Reference that the mode may regroup, reorder, or retitle while preserving its facts and intended relationships. Preserve page order, titles, or wording only when the user presents the outline as the final page plan or explicitly requests that boundary. When the user gives no structure, the mode does the structural lifting. To keep reshaping light, `briefing` imposes the least skeleton.

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
2. Preselect one mode from the auto-selection table + the confirmed communication contract and source structure; separately author the visible AI custom candidate required by §4.
3. Record the confirmed mode and rationale in `design_spec.md`, then project `- mode: <name>` into `spec_lock.md`.
4. Executor reads `modes/<locked-mode>.md` for a preset. For `custom`, it reads every file listed in `mode_references` before applying `mode_behavior`; with no references, it applies the novel behavior directly. Never glob this directory.

**Lock scope**: deck-wide (one mode per deck). The five are the catalog you select from; if the structure is genuinely mixed, pick the mode of the body pages and let pages vary within it, or recommend a `custom` blend (§4). Recommend the best fit; the user confirms.

---

## 4. Escape hatch — `custom`

`custom` holds **any bespoke narrative direction the five don't give as-is** — and what *kind* of thing it is doesn't matter. It might be a nameable cadence (dialectic 正反合, myth-vs-reality, countdown / Top-N, Socratic), a deliberate multi-act fusion of several modes, or the user's own feel for how the deck should carry (confrontational here, detached there). Don't try to taxonomize it.

**Always author the candidate; select it only when warranted.** Stage 2 includes one visible, non-empty AI custom proposal beside the five presets, spelling out the cadence / fusion / posture in plain language. It is initially unselected and does not replace the best-fit preset recommendation unless the user already supplied that exact custom direction; with a template, it must fit available prototype capacity. When the user selects it, the editable prose is saved as `mode: custom` plus `mode_behavior`; otherwise it remains recommendation-only. The Strategist crystallizes a selected custom direction in the Design Spec first, then projects the behavior and any actual catalog basis to `spec_lock.md`. The Executor reads every listed basis file before following that prose, or follows it directly when the direction is novel. (This records the intent so it survives 20 pages of generation — the Executor only ever reads `spec_lock.md`, never the chat.)

**Mandatory — read every catalog source actually used**: If the proposal combines or borrows an existing mode, name its exact catalog id in the visible proposal and read that mode file before writing the synthesis. A `pyramid` + `narrative` fusion therefore reads both [`pyramid.md`](./pyramid.md) and [`narrative.md`](./narrative.md), then writes `mode_references: pyramid, narrative` beside `mode_behavior`. Do not add loosely related references after the fact. A genuinely new cadence with no catalog source writes no `mode_references` and may proceed from its standalone behavior.

> **One value per deck — fusion is *one* `custom`, not several modes.** A deck always locks a single `mode`. A multi-mode blend is expressed as **one** `mode: custom` whose `mode_behavior` paragraph describes the acts — never by locking several modes.
>
> **First ask whether it's really fusion.** A locked mode is a *tendency*, not a cage: a `narrative` deck can still carry one analytical (pyramid-style) page, an `instructional` deck one showcase reveal — that is leaning within a dominant mode, and needs **no** `custom`. Reach for `custom` only when there is genuinely no single dominant spine.

**The one thing to avoid**: selecting `custom` as a *dodge* — defaulting to it because picking among the five takes judgment. The custom candidate is mandatory; a custom lock is not. When a preset genuinely fits, keep that preset selected. A user-stated direction remains authoritative the same way a user-supplied outline is — see the lens-not-mandate note in §1.
