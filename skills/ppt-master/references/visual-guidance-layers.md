# Visual Guidance Layers — Reference (not a constraint)

> A reference for *how* human-approved visual guidance is organized and drawn on —
> not a system that records or applies anything on its own.
> Part of the direction in #163: visual guidance as soft reference + human-curated
> structure. Sibling to [`type-scale.md`](./type-scale.md), which softens one
> section (hard rule → soft reference); this file describes the structure those
> references sit in.

## The gap this fills

A general model carries broad design competence but not *this* user's accumulated
PPT judgment — which scenarios want which restraint, which page patterns they have
blessed, which component treatments they reach for. This file describes the
*structural layer* that closes that gap: domain structure plus the user's
**manually approved** exemplars, organized by layer and keyed by scenario, so the
right prior surfaces at the right moment.

The organizing principle is **human curation, not automatic memory**. A flat,
equal-weight store that absorbs everything is actively harmful for slides:
scenarios are heterogeneous — government, tech, and project decks want different
things — so the more an undifferentiated store accumulates, the worse recall gets,
with preferences bleeding across scenarios and the guidance turning inconsistent.
Layering plus a human approval gate is what keeps recall precise.

## The four layers

| Layer | Retrieve by | Holds | Curated by | Drawn on | Conflict priority |
|---|---|---|---|---|---|
| **Scenario** | deck scenario (Strategist mode / style) | the scenario's baseline: palette discipline, density, restraint level, shadow / grid preferences | human-set | before the whole deck | lowest (baseline) |
| **Layout** | page role / type (cover / KPI / architecture / comparison …) | the layout pattern preferred for that page type | human-approved | when starting a page | medium |
| **Component** | the element type needed (arrow / card / native figure …) | approved element treatments (`exemplars/element_*`, approved native-diagram keys) | human-approved | when placing an element | high |
| **Single-page** | (scenario × page type) | a gold full-page exemplar (`exemplars/<type>_*.svg`) | **explicitly** human-approved | when starting a same-kind page | highest (most specific) |

## What keeps it precise

| Constraint | What it does |
|---|---|
| **Human-approval gate** | Nothing enters any layer except by explicit user approval — marked gold, or "use X for this kind from now on". No automatic accumulation. |
| **Bounded recall** | Each layer surfaces a small top-k within scenario scope, so the injected context stays small and on-point rather than diluting attention. |
| **More specific wins** | Single-page and component override the scenario default, which keeps one scenario's preferences from bleeding into another. |
| **Soft, not hard** | Layers inject as *preferences / starting points*. The model still weighs the actual page content — the same soft-reference stance as the rest of this direction. |

## Drawing on the layers

Starting page P (role R) in scenario S, the layers stack into one soft context:

```
Scenario[S]            → baseline    (palette / density / value preferences)
Layout[R]              → layout starting point
Component[P's elements] → element treatments
Single-page[R, S]      → same-kind gold exemplar (structural starting point)
```

Where layers disagree, the more specific layer wins over the more general one, and
each layer's recall stays bounded (small top-k). None of this overrides the page's
own content — it is the prior the model reaches for first, not a value it must keep.

## Where the layers already live

This is a way of reading structure the repo already has, not a new store beside it.

| Layer | Already lives in |
|---|---|
| Scenario | [`strategist.md`](./strategist.md) modes / style descriptors |
| Layout | [`design_spec_reference.md`](../templates/design_spec_reference.md) layout library |
| Component | `exemplars/element_*` plus approved native-diagram keys |
| Single-page | [`exemplars/`](../templates/exemplars/) gold pages |

So the work is to give the existing `exemplars/` and references a **layer + scenario
key**, not to build a memory system next to them.

## Where this is headed (see #163)

The smallest first cut is a scenario × page-type index over `exemplars/`, so a page
retrieves the gold exemplar matching its (scenario × page type) rather than the
generic one. Layout- and component-layer keying can follow once that proves out.
Throughout, explicit human approval stays the only way anything enters a layer — the
structure is curated, never self-populating.
