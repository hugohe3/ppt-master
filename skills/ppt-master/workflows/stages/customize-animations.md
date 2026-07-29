---
description: Optional post-processing stage for per-slide and per-object animation overrides.
---

# Customize Animations Stage

> Optional Generate-PPTX post-processing stage for per-slide or per-object
> animation control. Run when `<project_path>/animations.json` already exists,
> when the user explicitly asks to customize slide-specific motion, object
> order, effects, timing, or reveals, or when the effective Custom Animations
> outcome in `design_spec.md §I` is enabled. Deck-wide transitions,
> auto-advance, and deck-wide per-element settings without page-specific motion
> or an existing sidecar use [`animations.md`](../../references/animations.md)
> directly and do not activate this stage.

## When to Run

| Condition | Action |
|---|---|
| Effective Custom Animations outcome in `design_spec.md §I` is enabled | Run this stage after the final SVG quality gate and any enabled speaker-note pass, before Generate Step 7; use §IX suggestions as advice |
| User asks for per-slide or per-object animation, reveal order, timing, or effect changes | Run this stage |
| `<project_path>/animations.json` already exists | Run this stage to resolve preserve/adjust/replace/suppress intent before export |
| §IX contains `Motion suggestion`, but no trigger above is active | Do not run; retain the suggestion as Strategist advice and keep normal export defaults |
| No motion request, enabled outcome, or existing sidecar; user only wants the default deck | Do not run; normal export keeps page transitions and no element builds |
| No existing sidecar; user only wants deck-wide page transitions, auto-advance, or one per-element object animation policy | Do not run; apply [`animations.md`](../../references/animations.md) with exporter flags such as `-a auto` or `-a emphasis_spin` |
| `svg_output/*.svg` is missing | Complete the main Executor phase first |

**Decision precedence**: latest explicit instruction → Stage 3 policy →
compatibility default `false`; provenance stays in Design Spec §I, never the
lock. Stage 3 `false` blocks creation, not an existing sidecar. Existing
sidecars enter this stage; explicit disables follow the table without deletion.

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
| Explicit Custom Animations disable | Preserve and validate the sidecar; return `-a none` |
| Explicit all-motion disable | Preserve and bypass the sidecar; return `--no-animations` |
| Explicit regeneration / rewrite / replacement | Rebuild the semantic grouping plan and replace `animations.json`; the previous choreography is not a constraint |
| Explicit adjustment / tuning / repair | Validate first, preserve the existing choreography where its semantic units remain valid, and migrate affected group references after any required regrouping |
| Stage activated with an existing sidecar and new §IX suggestions but no user replacement request | Validate first; preserve valid existing choreography and adjust only the affected semantic units |
| Existing sidecar with no new motion instruction | Validate and preserve it unchanged; if invalid, repair the owning sidecar/group reference before export |
| Ambiguous generation request | Ask whether to regenerate from scratch or modify the current animation; do not choose on the user's behalf |

Unless explicit all-motion disable bypasses it, validate an existing sidecar
before deciding to preserve, modify, or suppress object motion:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

**Hard rule**: semantic files determine both animation intent and animation
unit boundaries. The current `svg_output/*.svg` supplies visible content and
implementation structure, but its existing `<g>` hierarchy is not accepted as
the animation plan merely because it already exists.

**Optional-context fallback**: these semantic files inform this supporting stage but are not its gate artifacts. If any are absent, state what is missing and proceed with every remaining file plus visible SVG content. If all three context inputs are absent, use only explicit user instructions, visible SVG content, and the resolution rules in [`animations.md`](../../references/animations.md); do not infer detailed choreography beyond what the page itself expresses.

**Decision ownership — advice versus requirement**: A §IX
`Motion suggestion` expresses the Strategist's recommended communication job or
reveal relationship; it neither activates this stage nor locks an effect,
Effect Options, timing, trigger, group id, or coverage. Once another trigger
activates the stage, Executor may adopt, adjust, or decline the suggestion,
including choosing `none` when motion would reduce clarity. Explicit user
motion requirements remain mandatory. Never change page content merely to
justify animation.

**Hard rule — existing visible-layer boundary**: This stage may regroup existing content only under §2 visual equivalence; it MUST NOT create or modify a crop, comparison layer, scrim, lens, hotspot, annotation, or other visible image state to satisfy motion intent. When a required state is missing and ordinary Slide-local authoring can supply it, return to Generate Step 6, rerun the final SVG gate and regenerate notes only when speaker notes are enabled, then resume here. If a structural boundary prevents that repair, simplify a non-binding suggestion to legal existing units, a page transition, or `none`; an explicit requirement follows failure recovery instead of changing structure.

**No-op is complete**: Evaluate suggestions before regrouping SVG content. If
no `animations.json` exists, every page should retain the normal `fade`
transition and no object builds, and no explicit user requirement remains
unmet, change no SVG, create no sidecar, and return to Generate Step 7. Never
author motion merely to expose a capability.

---

## 2. Rebuild Semantic Motion Groups When Needed, Then List IDs

**Mandatory when object-targeted motion is in scope — content-first grouping
audit**: inspect each affected slide's visible content against its communication
job and speaker flow before treating any top-level `<g>` as an animation
anchor. The affected set is the page named by an adopted suggestion or explicit
object-motion request, plus both endpoints of each deterministic Morph pair.
Untouched pages need no animation audit. Existing groups are implementation
evidence only. Keep a current group unchanged only after confirming that it
already represents exactly one audience-facing reveal unit or one continuing
Morph object. A page-transition-only plan without explicit Morph pairs skips
regrouping and group listing.

| Content condition | Required grouping action |
|---|---|
| One current group contains several independently narrated rows, cards, steps, claims, or stages | Split it into descriptive direct-root sibling groups, one per reveal unit |
| One reveal unit is scattered across groups or root primitives | Merge or wrap its background, icon, label, value, and supporting text into one direct-root group |
| A connector or arrow explains entry into a node or stage | Reveal it with the relationship or target unit that makes the connection intelligible |
| A hero visual, overview graphic, takeaway, or warning has its own communication role | Give it its own semantic group |
| The same semantic object continues across adjacent Morph pages | Isolate each endpoint as one direct-root group and keep both endpoints as compatible object kinds |
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

**Mandatory**: plan the requested motion layers for each affected slide before
editing `animations.json`. A local object-animation request does not require a
deck-wide transition review.

| Layer | Config path | Use |
|---|---|---|
| Page transition | `defaults.transition` or `slides.<slide>.transition` | Control how one slide enters from the previous slide |
| Deterministic Morph pair | `slides.<destination>.morph` | Bind one real source group to one real destination group when semantic identity continues across adjacent slides |
| Page animation defaults | `defaults.animation` or `slides.<slide>.animation` | Control the default object-animation behavior for animated groups on a slide |
| Object overrides | `slides.<slide>.groups.<group_id>` | Control order, effect, delay, or duration for a real SVG group |

**Per-affected-page motion brief**: decide what communication job the requested
motion should perform—or that it should perform none—then choose only the
relevant transition, reveal sequence, object effects, and timing. Use
`design_spec.md` for slide role, `spec_lock.md` for rhythm and visual style,
speaker notes for narration order, and SVG group ids for target validity.

**Title reveal decision**: when a title participates in the affected page's
motion job, choose static, immediate, delayed, synchronized, post-hero, or
narration-cued behavior from slide intent. Use the sidecar override for a
marker-free legacy chrome-like id; repair an incorrect explicit
structural/static marker before animating it.

**Default — inherit unaffected motion layers (may override when the page's
communication job requires it)**: a custom object-animation pass may leave the
page transition and every untouched page on exporter or sidecar defaults. Add a
slide-specific `transition` only when the affected page needs one; never add
variation for coverage.

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

For a cross-slide object continuation that must not depend on PowerPoint's
automatic matching, put one explicit `morph` block on the destination slide.
Its `from` slide must be the immediately preceding exported SVG; each stable
pair key binds one source direct-root group id to one destination direct-root
group id. The exporter supplies PowerPoint's `!!` prefix. Use Morph by object;
word/character Morph does not accept this object-pair contract.

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

**Hard rule — explicit semantic choreography**: When an adopted image-led plan depends on a specific reveal relationship or order, target its real groups with explicit canonical effects and order; do not delegate those material decisions to `auto`, `mixed`, or `random`. Those modes remain valid when generic entrance treatment is sufficient.

**Start modes**:

| Trigger | Behavior |
|---|---|
| `after-previous` | Cascade automatically on slide entry |
| `with-previous` | Start together on slide entry |
| `on-click` | One presenter click per animated group |

---

## 4. Edit `animations.json`

**Hard rule — sparse overrides reference real targets**: write only affected
slides and only fields that differ from exporter or sidecar defaults. An
unlisted SVG inherits the resolved deck-wide settings; a listed slide may
contain only `transition`, `animation`, `groups`, or `morph` fields that it
actually overrides. `defaults` is optional and belongs only to intentional
deck-wide settings. Group-level overrides remain opt-in. Chrome groups stay out
(the exporter pins them to `none` by default). Name a legacy chrome-like id only
when the user explicitly wants that content animated and the SVG has no
explicit structural layer, role, or placeholder marker.

**Forbidden**:

- Referencing a slide that does not exist in `svg_output/`
- Referencing a missing, ambiguous, or structural group
- Enumerating every content group in a slide just to restate the slide-level default effect
- Listing a group with `data-pptx-layer` or an explicit static role/placeholder marker
- Listing a legacy chrome-like id without an explicit, reviewed intent to override the name heuristic

| Field | Behavior |
|---|---|
| `transition.effect` | Slide-specific page transition effect |
| `transition.effect_options` | Effect-specific native PowerPoint options; requires an explicit slide-specific `transition.effect` |
| `transition.duration` | Slide-specific page transition duration |
| `morph.from` | Immediately preceding SVG stem for an explicit deterministic Morph transition |
| `morph.pairs.<key>.from` / `.to` | Unique source/destination direct-root group ids that receive the shared PowerPoint name `!!<key>` |
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
invent duplicate fields. Change Font's `font_name` is one concrete
target-installed PowerPoint face, never a CSS font stack.

**Canonical sparse example — only the affected slide and divergent fields
appear**:

```json
{
  "version": 1,
  "slides": {
    "03_market": {
      "transition": {
        "effect": "wipe",
        "effect_options": { "direction": "left" },
        "duration": 0.35
      },
      "groups": {
        "chart": { "effect": "entrance_wipe", "effect_options": { "direction": "left" }, "order": 2, "duration": 0.6 },
        "insight": { "effect": "entrance_fly", "effect_options": { "direction": "up_right" }, "order": 3, "delay": 0.2, "trigger_shape": "chart" }
      }
    }
  }
}
```

Every unlisted page inherits the resolved defaults. `03_market` changes its
transition and two real groups without restating a page animation block.
Structural chrome stays omitted unless a marker-free legacy name needs an
explicitly reviewed override.

Use the complete two-slide deterministic Morph example in
[`animations.md`](../../references/animations.md) §2.1; do not copy the source
group into the destination slide's `groups` block merely to establish identity.

**Forbidden — SVG pollution**: do not add `data-*` animation attributes to SVG files. Animation customization belongs in `animations.json`.

---

## 5. Validate and Return to Generate Export

When `animations.json` was newly created or changed after the §1 validation,
run:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

After validation succeeds, return to
[`generate-pptx.md`](../generate-pptx.md) Step 7.1. Generate owns note
splitting, `finalize_svg.py`, native export, and the published postflight
receipt; Step 7.3 reads `<project_path>/animations.json` automatically. If §2
changed `svg_output/`, complete its required final SVG quality rerun before
returning. Do not finalize or export independently from this stage.

**Validation**: The later native export must reflect the per-slide and
per-object overrides. `--animation none` still disables all per-element
animation and overrides `animations.json`. Unknown animation
effects/modes/triggers; unsupported effect options; incompatible, boolean,
non-finite, or out-of-range timing parameters; non-positive durations; negative
delay/stagger; invalid order; missing slides/groups; and structural-layer
targets fail validation. Transition validation remains strict. None of these
failures substitutes a fallback effect or silently drops a requested target.
Deterministic Morph also rejects non-adjacent source slides, missing or
ambiguous direct-root groups, conflicting or undeclared shared keys, non-object
Morph, and any target that does not remain one compatible Slide-local object
after structure processing.

Generate Step 7 export reads back row order, trigger, target, resolved effect,
duration, offset, timing placement, IDs, and shape references. Narration
preserves these rows. Direct-PPTX routes fingerprint and preserve source object
animation; they never author it. See
[`pptx-animations.md`](../../scripts/docs/pptx-animations.md).

### 5.1 Optional Video Motion Handoff

When a downstream video renderer will enhance the deck, have Generate Step 7.3
append `--conversion-trace`. After that final export succeeds, derive the motion
plan from its resolved trace:

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

- [x] Applicable semantic context and motion intent were resolved
- [x] Adopted object targets use real post-regroup SVG ids when object motion is in scope
- [x] Sparse `animations.json` overrides are valid when present; a no-op path creates none
- [x] Any regrouped SVG passed the final quality gate
- [x] Control returned to Generate Step 7 for preview, export, read-back, and package validation
- [x] Any requested video plan waits for the final resolved conversion trace
