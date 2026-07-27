---
description: Optional post-processing stage for per-slide and per-object animation overrides.
---

# Customize Animations Stage

> Optional Generate-PPTX post-processing stage for per-slide or per-object
> animation control. Run when the user asks to customize slide-specific motion,
> object order, effects, timing, or reveals. Deck-wide transitions,
> auto-advance, and deck-wide per-element object settings use
> [`animations.md`](../../references/animations.md) directly and do not activate
> this stage.

## When to Run

| Condition | Action |
|---|---|
| User asks for per-slide or per-object animation, reveal order, timing, or effect changes | Run this stage |
| User only wants the default deck (page transitions, no element builds) | Do not run; normal `svg_to_pptx.py` export is enough |
| User only wants deck-wide page transitions, auto-advance, or one per-element object animation policy | Do not run; apply [`animations.md`](../../references/animations.md) with exporter flags such as `-a auto` or `-a emphasis_spin` |
| `svg_output/*.svg` is missing | Complete the main Executor phase first |
| `animations.json` exists | Resolve regeneration versus modification through the §1 intent gate before changing it |

---

## 1. Resolve Intent and Read Semantic Context

**Context read**: before editing `animations.json`, read every semantic planning file below that exists.

| File | Use |
|---|---|
| `<project_path>/design_spec.md` | Understand each slide's content intent, narrative role, and visual emphasis |
| `<project_path>/spec_lock.md` | Confirm page rhythm, layout role, chart/template constraints, and execution contract |
| `<project_path>/notes/total.md` or `<project_path>/notes/*.md` | Use speaker flow to tune reveal order, delays, and emphasis |

**Existing sidecar intent gate**:

| User intent | Action |
|---|---|
| Explicit regeneration / rewrite / replacement | Rebuild the semantic grouping plan and replace `animations.json`; the previous choreography is not a constraint |
| Explicit adjustment / tuning / repair | Validate first, preserve the existing choreography where its semantic units remain valid, and migrate affected group references after any required regrouping |
| Ambiguous generation request | Ask whether to regenerate from scratch or modify the current animation; do not choose on the user's behalf |

When the existing sidecar will be modified:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

**Hard rule**: semantic files determine both animation intent and animation
unit boundaries. The current `svg_output/*.svg` supplies visible content and
implementation structure, but its existing `<g>` hierarchy is not accepted as
the animation plan merely because it already exists.

**Optional-context fallback**: these semantic files inform this supporting stage but are not its gate artifacts. If any are absent, state what is missing and proceed with every remaining file plus visible SVG content. If all three context inputs are absent, use only explicit user instructions, visible SVG content, and the resolution rules in [`animations.md`](../../references/animations.md); do not infer detailed choreography beyond what the page itself expresses.

---

## 2. Rebuild Semantic Animation Groups, Then List IDs

**Mandatory — content-first grouping audit**: inspect every slide's visible
content against its communication job and speaker flow before treating any
top-level `<g>` as an animation anchor. Existing groups are implementation
evidence only. Keep a current group unchanged only after confirming that it
already represents exactly one audience-facing reveal unit.

| Content condition | Required grouping action |
|---|---|
| One current group contains several independently narrated rows, cards, steps, claims, or stages | Split it into descriptive direct-root sibling groups, one per reveal unit |
| One reveal unit is scattered across groups or root primitives | Merge or wrap its background, icon, label, value, and supporting text into one direct-root group |
| A connector or arrow explains entry into a node or stage | Reveal it with the relationship or target unit that makes the connection intelligible |
| A hero visual, overview graphic, takeaway, or warning has its own communication role | Give it its own semantic group |
| Several atoms express one inseparable idea | Keep them together; do not animate the atoms separately |
| Page chrome, structural layers, or static framing | Preserve their structure and exclude them from ordinary animation targets |

**Hard rule — visual equivalence**: regrouping changes object boundaries only.
Preserve all visible content, paint order, coordinates, transforms, inherited
paint, opacity, clipping, filters, references, and native metadata. Keep
rendering-bearing implementation wrappers nested inside the new semantic group
when flattening or distributing their attributes could change appearance.

**Hard rule — structural boundary**: never split or merge across
`data-pptx-layer`, `data-pptx-placeholder`, native chart/table carrier, native
preset, or imported logical-object boundaries. Structural/static objects remain
non-animatable. Ordinary Slide-local content groups follow
[`shared-standards-core.md`](../../references/shared-standards-core.md) §4.3:
every visible direct-root group has a descriptive unique `id` and positive
root-coordinate `data-pptx-bounds`; nested implementation groups carry no
bounds.

**Forbidden — group-list-first choreography**:

- Choosing effects or order from the pre-existing `list-groups` output before the content-first audit
- Keeping a coarse wrapper only because it already has an `id`
- Splitting one semantic idea into individual shapes or text lines to increase animation count
- Merging unrelated ideas to reduce animation count
- Adding animation-specific `data-*` attributes to SVG

There is no target group count. Granularity follows the page's actual claims,
comparisons, sequence, causality, and narration beats.

After any regrouping, rerun the final SVG quality gate because `svg_output/`
changed:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path> --stage final --json
```

Then list the **post-regroup** anchors:

```bash
python3 skills/ppt-master/scripts/animation_config.py list-groups <project_path>
```

Output is one line per slide: `<slide_basename>: id1, id2, id3`. Default chrome
groups (`bg` / `*-header` / `*-footer` / `*-decor` / `nav` / `watermark` /
`logo` / `pagenumber`) are excluded. This post-regroup list is the source of
truth when planning §3 and editing §4; never invent a slide or group key.

An explicit sidecar entry may override only the marker-free legacy id-name
heuristic. A group carrying `data-pptx-layer` or an explicit static
role/placeholder marker can never animate, even when it is named explicitly.

If `animations.json` does not exist and a starting file is useful, scaffold
only after semantic regrouping:

```bash
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>
```

Do not read the full scaffold unless it is needed as an editing starting point.

---

## 3. Plan Slide and Object Motion

**Mandatory**: plan both page-level transitions and in-slide object animations before editing `animations.json`.

| Layer | Config path | Use |
|---|---|---|
| Page transition | `defaults.transition` or `slides.<slide>.transition` | Control how one slide enters from the previous slide |
| Page animation defaults | `defaults.animation` or `slides.<slide>.animation` | Control the default object-animation behavior for animated groups on a slide |
| Object overrides | `slides.<slide>.groups.<group_id>` | Control order, effect, delay, or duration for a real SVG group |

**Per-page motion brief**: for each slide, first decide what communication job motion should perform—or that it should perform none—then decide transition effect, transition duration, object reveal sequence, object effects, and timing. Use `design_spec.md` for slide role, `spec_lock.md` for rhythm and visual style, speaker notes for narration order, and SVG group ids for target validity.

**Title reveal decision**: treat each real title as a first-class plan item.
Choose static, immediate, delayed, synchronized, post-hero, or narration-cued
behavior from slide intent. Use the sidecar override for a marker-free legacy
chrome-like id; repair an incorrect explicit structural/static marker before
animating it.

**Hard rule**: a custom animation pass must not only edit group effects. It must also decide whether each slide should inherit the default transition or need a slide-specific `transition` override. Inheritance is a complete decision; do not create slide-specific transitions to satisfy a variation quota.

**Timing guidance**: use shorter motion for dense/repeated scan content and
longer motion for conceptual pivots, hero diagrams, section boundaries, and
final takeaways. Uniform timing is valid when it fits the requested style.

**Reference — not a constraint: motion judgment.** Decide the communication
job, tone, audience order, and whether direction carries meaning before using
geometry. If motion adds no clarity or intended feeling, use `none`,
`entrance_appear`, or `entrance_fade`. Layout direction alone does not require
special motion; variation follows a real content/tone change, never a quota.

### 3.1 Supported Page Transitions

Use one of the 48 canonical native effects from the complete shared registry in
[`animations.md`](../../references/animations.md) §3. It covers all current
PowerPoint Subtle, Exciting, and Dynamic Content gallery effects. The eight old
names are readable only as compatibility inputs; do not write them in new
plans or sidecars. They normalize to a canonical effect plus native
`effect_options` before writing. `none` removes the visual page transition
while allowing timed advance to remain.

**Transition fields**:

| Field | Behavior |
|---|---|
| `effect` | One supported page transition effect; `none` removes only the visual effect |
| `effect_options` | Optional object containing only the selected native effect's PowerPoint Effect Options; requires an explicit `effect` |
| `duration` | Finite transition duration in seconds; must be greater than zero |
| `auto_advance` | Optional finite non-negative seconds before automatic slide advance; click remains enabled, and this field is valid with `effect: none` |

Run
`python3 skills/ppt-master/scripts/pptx_animations.py --describe-transition <effect>`
before authoring Effect Options. Never infer that one effect accepts another
effect's direction, shape, pattern, or boolean fields.

### 3.2 Supported In-Slide Animations

Use the 203 canonical PowerPoint-native keys: 53 `entrance_*`, 33
`emphasis_*`, 64 `path_*`, and 53 `exit_*`. Run
`python3 skills/ppt-master/scripts/pptx_animations.py --list` for the exact
categorized names. Each key preserves PowerPoint's complete authored behavior
tree. Media-only commands remain in the audio/video workflows.

| Choice | Behavior |
|---|---|
| `entrance_*` / `emphasis_*` / `path_*` / `exit_*` | Select one explicit canonical PowerPoint object effect |
| `auto` | Map content roles to canonical entrances; image-like ids use a richer canonical pool |
| `mixed` | Cycle 16 canonical entrance presets by group order |
| `random` | Select deterministically from the same canonical entrance pool |
| `none` | Exclude the object or slide from in-slide animation |

The 29 old short names remain readable only as compatibility inputs; do not use
them in new plans or sidecars. All Fly direction names normalize to
`entrance_fly`, all Wipe direction names normalize to `entrance_wipe`, and the
other old names normalize to their matching `entrance_*` preset. `cut`
normalizes to `entrance_appear`. Compatibility Fly/Wipe aliases preserve their
direction as `effect_options.direction`; legacy `wheel` preserves its historical
four-spoke amount.

`auto`, `mixed`, and `random` never choose emphasis, motion-path, or exit
effects implicitly. Select an explicit canonical key when the plan calls for
one.

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
| `transition.effect_options` | Effect-specific native PowerPoint options; requires an explicit slide-specific `transition.effect` |
| `transition.duration` | Slide-specific page transition duration |
| `animation.effect` | Slide-specific default object animation effect |
| `animation.duration` | Slide-specific default object schedule duration |
| `animation.stagger` | Slide-specific delay between object animation rows |
| `animation.trigger` | Slide-specific start mode |
| `groups.<id>.effect` | Object-specific canonical native effect, `auto`, `mixed`, `random`, or `none`; old names are read-only compatibility inputs |
| `order` | Animation order only; does not change SVG layer order |
| `delay` | Extra seconds in `after-previous`, or after clicking `trigger_shape` |
| `duration` | Per-group schedule duration in seconds; scalable native behavior trees keep their internal timing ratios, while `entrance_appear` and instantaneous native presets retain their PowerPoint-authored duration and use this value for subsequent `after-previous` spacing |
| `effect_options` | Effect-specific PowerPoint parameters; requires an explicit canonical `effect` in the same block |
| `trigger_shape` | Different top-level group id for native **On Click of**; group-only and not inherited |
| `repeat_count` / `repeat_duration` | Repeat count or total repeat span; mutually exclusive |
| `auto_reverse`, `rewind` | Reverse each cycle and/or restore the pre-animation state |
| `accelerate`, `decelerate`, `bounce_end` | `0..1` timing ratios; acceleration plus deceleration must not exceed `1`; bounce requires an interpolated effect and cannot combine with deceleration |
| `restart` | `always`, `when-not-active`, or `never` |
| `after_effect` | `none`, `dim` with `color`, `hide`, or `hide-on-next-click` |
| `sound` | Project-relative or absolute `.m4a`, `.mp3`, or `.wav` path |

`effect_options` may contain `direction`, `amount`, `color`, `font_name`,
`relative`, or `size`, but validation permits only fields supported by the
selected effect. Before writing a parameterized effect, run
`python3 skills/ppt-master/scripts/pptx_animations.py --describe
<canonical_effect>` and use the returned values exactly. `duration` owns
PowerPoint Speed; `accelerate`/`decelerate` own smooth start/end, so do not
invent duplicate fields.

**Canonical example — every slide carries explicit transition + animation;
groups appear only when they diverge**:

```json
{
  "version": 1,
  "defaults": {
    "transition": { "effect": "fade", "duration": 0.4 },
    "animation": { "effect": "entrance_fade", "duration": 0.4, "stagger": 0.5, "trigger": "after-previous" }
  },
  "slides": {
    "01_cover": {
      "transition": { "effect": "fade", "duration": 0.5 },
      "animation": { "effect": "entrance_fade", "duration": 0.5, "stagger": 0.4, "trigger": "after-previous" }
    },
    "03_market": {
      "transition": {
        "effect": "wipe",
        "effect_options": { "direction": "left" },
        "duration": 0.35
      },
      "animation": { "effect": "entrance_fade", "duration": 0.4, "stagger": 0.25, "trigger": "after-previous" },
      "groups": {
        "chart": { "effect": "entrance_wipe", "effect_options": { "direction": "left" }, "order": 2, "duration": 0.6 },
        "insight": { "effect": "entrance_fly", "effect_options": { "direction": "up_right" }, "order": 3, "delay": 0.2, "trigger_shape": "chart" }
      }
    }
  }
}
```

`01_cover` shows a complete per-slide block even when values closely match
the defaults. `03_market` lists only divergent groups. Structural chrome stays
omitted unless a marker-free legacy name needs an explicitly reviewed override.

**Forbidden — SVG pollution**: do not add `data-*` animation attributes to SVG files. Animation customization belongs in `animations.json`.

---

## 5. Validate, Refresh Derived SVGs, and Export

Run sequentially:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

**Validation**: the exported native PPTX must reflect the per-slide and
per-object overrides, and `svg_final/` must reflect any semantic regrouping
performed in §2. `--animation none` still disables all per-element animation
and overrides `animations.json`. Unknown animation
effects/modes/triggers; unsupported effect options; incompatible, boolean,
non-finite, or out-of-range timing parameters; non-positive durations; negative
delay/stagger; invalid order; missing slides/groups; and structural-layer
targets fail validation. Transition validation remains strict. None of these
failures substitutes a fallback effect or silently drops a requested target.

Generated export reads back row order, trigger, target, resolved effect,
duration, offset, timing placement, IDs, and shape references. Narration
preserves these rows. Direct-PPTX routes fingerprint and preserve source object
animation; they never author it. See
[`pptx-animations.md`](../../scripts/docs/pptx-animations.md).

### 5.1 Optional Video Motion Handoff

When a downstream video renderer will enhance the deck, export with
`--conversion-trace` and derive its motion plan from that resolved trace:

```bash
python3 skills/ppt-master/scripts/video_motion_plan.py \
  <project_path>/validation/<output_stem>.trace.json \
  -o <project_path>/validation/video_motion_plan.json \
  --style adaptive \
  --force
```

For narrated output, use the final `--recorded-narration` trace. The video plan
locks identity, effect, direction, order, bounds, and timing; it may refine
renderer parameters but cannot replace the source effect. See
[`video-motion-plan.md`](../../scripts/docs/video-motion-plan.md).

---

## ✅ Customize Animations Complete

- [x] Semantic context and every slide's visible content were reviewed
- [x] Each target is one post-regroup semantic unit with a real SVG id
- [x] Regrouped SVG passed the final quality gate and refreshed `svg_final/`
- [x] Every slide has explicit motion blocks; only divergent groups are listed
- [x] Page and object motion were planned together with intentional timing
- [x] Sidecar validation, re-export, semantic read-back, and package validation passed
- [x] Any video plan came from the final resolved conversion trace
