---
description: Optional post-processing stage for per-slide and per-object animation overrides.
---

# Customize Animations Stage

> Optional Generate-PPTX post-processing stage for per-slide or per-object
> animation control. Run when the user asks to customize slide-specific motion,
> object order, effects, timing, or reveals. Deck-wide transitions,
> auto-advance, and per-element entrance settings use
> [`animations.md`](../../references/animations.md) directly and do not activate
> this stage.

## When to Run

| Condition | Action |
|---|---|
| User asks for per-slide or per-object animation, reveal order, timing, or effect changes | Run this stage |
| User only wants the default deck (page transitions, no element builds) | Do not run; normal `svg_to_pptx.py` export is enough |
| User only wants deck-wide page transitions, auto-advance, or per-element entrance animation | Do not run; apply [`animations.md`](../../references/animations.md) with exporter flags such as `-a auto` |
| `svg_output/*.svg` is missing | Complete the main Executor phase first |
| This stage is triggered and `animations.json` is present | Validate and edit it; do not overwrite unless the user asks |

---

## 1. Get Real Group IDs (do NOT dump the full scaffold)

**Mandatory**: use real SVG group ids. Do not invent slide or group keys.

**Default path — `list-groups`** (cheap, ~1KB of output even on a long deck):

```bash
python3 skills/ppt-master/scripts/animation_config.py list-groups <project_path>
```

Output is one line per slide: `<slide_basename>: id1, id2, id3` — default
chrome groups (`bg` / `*-header` / `*-footer` / `*-decor` / `nav` /
`watermark` / `logo` / `pagenumber`) are excluded from the ordinary target
list. Use this as the source of truth when planning §3 and editing §4
— **do not read the full scaffold file unless you need it as an editing
starting point**.

An explicit sidecar entry may override only the marker-free legacy id-name
heuristic. A group carrying `data-pptx-layer` or an explicit static
role/placeholder marker can never animate, even when it is named explicitly.

If `animations.json` does not exist and you want a starting file to edit:

```bash
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>
```

Scaffold output also excludes chrome and includes a `defaults` stub.

If it already exists:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

---

## 2. Read Semantic Context

**Context read**: before editing `animations.json`, read every semantic planning file below that exists.

| File | Use |
|---|---|
| `<project_path>/design_spec.md` | Understand each slide's content intent, narrative role, and visual emphasis |
| `<project_path>/spec_lock.md` | Confirm page rhythm, layout role, chart/template constraints, and execution contract |
| `<project_path>/notes/total.md` or `<project_path>/notes/*.md` | Use speaker flow to tune reveal order, delays, and emphasis |

**Hard rule**: semantic files determine animation intent; `svg_output/*.svg` determines valid animation targets. Never reference a slide or group id that is absent from the scaffold / SVG scan.

**Optional-context fallback**: these semantic files inform this supporting stage but are not its gate artifacts. If any are absent, state what is missing and proceed with every remaining file plus real SVG group ids. If all three context inputs are absent, use only explicit user instructions, real SVG group ids, and the resolution rules in [`animations.md`](../../references/animations.md); do not infer detailed object choreography.

---

## 3. Plan Slide and Object Motion

**Mandatory**: plan both page-level transitions and in-slide object entrances before editing `animations.json`.

| Layer | Config path | Use |
|---|---|---|
| Page transition | `defaults.transition` or `slides.<slide>.transition` | Control how one slide enters from the previous slide |
| Page animation defaults | `defaults.animation` or `slides.<slide>.animation` | Control the default entrance behavior for animated groups on a slide |
| Object overrides | `slides.<slide>.groups.<group_id>` | Control order, effect, delay, or duration for a real SVG group |

**Per-page motion brief**: for each slide, decide transition effect, transition duration, object reveal sequence, object effects, and timing. Use `design_spec.md` for slide role, `spec_lock.md` for rhythm, speaker notes for narration order, and SVG group ids for target validity.

**Hard rule**: a custom animation pass must not only edit group effects. It must also decide whether each slide should inherit the default transition or need a slide-specific `transition` override.

**Timing guidance**: prefer content-aware durations when the deck has varied slide rhythm or object importance. Uniform timing is acceptable when it matches the user's requested style or the deck's pacing.

**Duration planning**:

| Context | Transition duration | Object duration | Delay / stagger |
|---|---:|---:|---:|
| `anchor` slide / section opener / closing synthesis | 0.35-0.60s | 0.45-0.75s | 0.20-0.40s |
| `breathing` concept slide / hero diagram | 0.25-0.45s | 0.40-0.65s | 0.16-0.30s |
| `dense` technical slide / repeated pattern page | 0.18-0.35s | 0.25-0.45s | 0.10-0.24s |
| Minor supporting object | inherit or 0.20-0.35s | 0.20-0.35s | 0.08-0.18s |
| Key insight / final takeaway | 0.30-0.50s | 0.50-0.80s | 0.25-0.45s |

**Duration guidance**: use shorter timing for repeated scan content, longer timing for conceptual pivots, section transitions, hero diagrams, and final takeaways.

### 3.1 Supported Page Transitions

| Effect | Behavior |
|---|---|
| `none` | Remove visual page transition; timed advance may remain |
| `fade` | Neutral default for technical decks |
| `push` | Directional slide entry |
| `wipe` | Directional reveal |
| `split` | Split-open transition |
| `strips` | Diagonal strips transition |
| `cover` | Cover from the side |
| `random` | PowerPoint random transition |

**Transition fields**:

| Field | Behavior |
|---|---|
| `effect` | One supported page transition effect; `none` removes only the visual effect |
| `duration` | Finite transition duration in seconds; must be greater than zero |
| `auto_advance` | Optional finite non-negative seconds before automatic slide advance; click remains enabled, and this field is valid with `effect: none` |

### 3.2 Supported In-Slide Animations

| Effect | Behavior |
|---|---|
| `none` | Exclude the object or slide from in-slide animation |
| `appear` | Visibility flip without motion |
| `fade` | Neutral entrance |
| `fly` | Fly in from bottom |
| `cut` | Legacy compatibility key; preserve its registered tuple exactly |
| `zoom` | Scale/zoom entrance |
| `wipe` | Wipe entrance |
| `split` | Split/barn entrance |
| `blinds` | Horizontal blinds |
| `checkerboard` | Checkerboard reveal |
| `dissolve` | Dissolve reveal |
| `random_bars` | Random bars reveal |
| `peek` | Peek/wipe down |
| `wheel` | Wheel entrance |
| `box` | Box-in reveal |
| `circle` | Circle-in reveal |
| `diamond` | Diamond-in reveal |
| `plus` | Plus-shaped reveal |
| `strips` | Diagonal strips reveal |
| `wedge` | Wedge reveal |
| `stretch` | Stretch entrance |
| `expand` | Expand entrance |
| `swivel` | Swivel entrance |
| `auto` | Map effect from group id (chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade); image-like ids (hero/figure-/image/img-/kpi) cycle zoom/dissolve/circle/box/diamond/wheel for visual variation; unmatched ids cycle fade/wipe/fly/zoom |
| `mixed` | Legacy 16-effect cycle by group order (first group fades, rest cycle the larger pool) |
| `random` | Stable seeded effect per animated group; `--conversion-trace` records resolved effects when diagnostics are enabled |

**Start modes**:

| Trigger | Behavior |
|---|---|
| `after-previous` | Cascade automatically on slide entry |
| `with-previous` | Start together on slide entry |
| `on-click` | One presenter click per animated group |

---

## 4. Edit `animations.json`

**Hard rule — write every slide explicitly; let groups inherit**. Each
slide under `slides.<slide>` MUST carry its own complete `transition` and
`animation` block (effect + duration + stagger + trigger where applicable),
even when the values match `defaults`. This makes per-page rhythm visible
at a glance without mentally merging the inheritance chain. Group-level
overrides remain opt-in — list only the groups that genuinely diverge from
the slide's `animation` block. Chrome groups stay out (the exporter pins
them to `none` by default). Name a legacy chrome-like id only when the user
explicitly wants that content animated and the SVG has no explicit structural
layer, role, or placeholder marker.

> Note: version-1 legacy sidecars may omit fields inside a listed slide under
> the declared inheritance in [`animations.md`](../../references/animations.md) §2. This
> workflow writes complete new slide blocks, and validation still requires
> every current SVG stem to be present under `slides`.

`defaults` is still required: it supplies the legacy inheritance baseline and
the deck-wide values copied into every complete new slide block.

**Forbidden**:

- Omitting a slide that exists in `svg_output/` — every produced slide must appear under `slides`
- Writing a slide block with only `groups` and no `transition`/`animation`
- Enumerating every content group in a slide just to restate the slide-level default effect
- Listing a group with `data-pptx-layer` or an explicit static role/placeholder marker
- Listing a legacy chrome-like id without an explicit, reviewed intent to override the name heuristic

| Field | Behavior |
|---|---|
| `transition.effect` | Slide-specific page transition effect |
| `transition.duration` | Slide-specific page transition duration |
| `animation.effect` | Slide-specific default object entrance effect |
| `animation.duration` | Slide-specific default object entrance duration |
| `animation.stagger` | Slide-specific delay between object entrances |
| `animation.trigger` | Slide-specific start mode |
| `groups.<id>.effect` | Object-specific entrance effect, `auto`, `mixed`, `random`, or `none` |
| `order` | Animation order only; does not change SVG layer order |
| `delay` | Extra seconds before this group starts in `after-previous` mode |
| `duration` | Per-group schedule duration in seconds; `appear` stays a 1ms visibility flip and uses this value only for subsequent `after-previous` spacing |

**Canonical example — every slide carries explicit transition + animation;
groups appear only when they diverge**:

```json
{
  "version": 1,
  "defaults": {
    "transition": { "effect": "fade", "duration": 0.4 },
    "animation": { "effect": "fade", "duration": 0.4, "stagger": 0.5, "trigger": "after-previous" }
  },
  "slides": {
    "01_cover": {
      "transition": { "effect": "fade", "duration": 0.5 },
      "animation": { "effect": "fade", "duration": 0.5, "stagger": 0.4, "trigger": "after-previous" }
    },
    "02_agenda": {
      "transition": { "effect": "fade", "duration": 0.4 },
      "animation": { "effect": "fade", "duration": 0.4, "stagger": 0.5, "trigger": "after-previous" }
    },
    "03_market": {
      "transition": { "effect": "wipe", "duration": 0.35 },
      "animation": { "effect": "fade", "duration": 0.4, "stagger": 0.25, "trigger": "after-previous" },
      "groups": {
        "chart": { "effect": "wipe", "order": 2, "duration": 0.6 },
        "insight": { "effect": "fly", "order": 3, "delay": 0.2 }
      }
    },
    "07_hero_quote": {
      "transition": { "effect": "fade", "duration": 0.7 },
      "animation": { "effect": "fade", "duration": 0.7, "stagger": 0.3, "trigger": "after-previous" },
      "groups": {
        "quote": { "duration": 0.9, "delay": 0.3 }
      }
    }
  }
}
```

Notes:
- `02_agenda` repeats `defaults` verbatim — this is intentional under the new rule so per-page rhythm is auditable in one read.
- `03_market` and `07_hero_quote` only list the groups that diverge; `title`, `footer`, `bg`, `header` etc. are not enumerated.
- Structural chrome groups are never listed. Legacy id-only chrome groups remain omitted unless an explicit reviewed override is required.

**Forbidden — SVG pollution**: do not add `data-*` animation attributes to SVG files. Animation customization belongs in `animations.json`.

---

## 5. Validate and Export

Run sequentially:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

**Validation**: the exported native PPTX must reflect the per-slide and
per-object overrides. `--animation none` still disables all per-element
animation and overrides `animations.json`. Unknown animation
effects/modes/triggers; boolean, NaN, or Infinity numeric values; non-positive
durations; negative delay/stagger; invalid order; missing slides/groups; and
structural-layer targets fail validation. Transition validation remains strict
as well. None of these failures substitutes a fallback effect or silently drops
a requested target.

Generated export performs semantic read-back per slide, comparing row order, trigger, target, resolved effect tuple, duration, and offset. It then validates timing-tree placement, `p:cTn` ids, and `p:spTgt` references across the packaged PPTX. Stable `random` choices appear in the conversion trace when export enables `--conversion-trace`. Narration merges audio into the existing timing tree and must preserve these rows.

Direct-PPTX routes are preserve-only for object animation: they compare the source object-animation fingerprint before and after allowed edits, run structural package validation, and do not write, normalize, or claim ownership of effects. See [`pptx-animations.md`](../../scripts/docs/pptx-animations.md) for the exact compatibility and OOXML contract.

---

## ✅ Customize Animations Complete

- [x] `animations.json` exists only because per-slide or per-object customization was requested
- [x] `design_spec.md`, `spec_lock.md`, and available speaker notes were checked before editing animation overrides
- [x] Every slide in `svg_output/` appears under `slides` with explicit `transition` + `animation` blocks
- [x] Group-level entries were added only for groups that diverge from the slide's `animation` block
- [x] Page transitions and in-slide object animations were planned together
- [x] Transition and object durations were chosen intentionally for the deck's pacing
- [x] `animation_config.py validate` passed
- [x] PPTX re-export completed with custom animation overrides
- [x] Generated animation semantic read-back and package validation passed
