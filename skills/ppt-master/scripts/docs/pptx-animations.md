# PPTX Animation Core

The shared animation core owns the object-effect vocabulary, trigger
semantics, OOXML timing writer, semantic read-back, and package validation for
PowerPoint OOXML. Per-element animation remains opt-in: generated PPTX export
defaults to `none`, exactly as before this validation upgrade.

## 1. Ownership

| Concern | Owner |
|---|---|
| Effect registry, timing writer, and read-back | `scripts/pptx_animations.py` |
| Sidecar parsing and SVG target discovery | `svg_to_pptx/animation_config.py` |
| SVG group-to-shape mapping | `svg_to_pptx/drawingml/converter.py` |
| Generated PPTX resolution and validation | `svg_to_pptx/pptx_package/builder.py` |
| Narration timing merge | `svg_to_pptx/pptx_package/narration.py` |
| Public authoring contract | `references/animations.md` |
| Customization stage | `workflows/stages/customize-animations.md` |

**Hard rule**: only the generated SVG-to-PPTX route writes object
animations. Direct-PPTX routes preserve source animations and run structural
package validation; they do not resolve or author animation effects.

---

## 2. Domain Model

`groups.<id>` accepts either one backward-compatible effect object or one
non-empty `effects[]` array; the forms are exclusive and every array row names
`effect`. Both expand into the same row model, so repeated shape targets are
valid. Legacy rows also accept `trigger`; omitted row settings inherit the
resolved slide animation.

One resolved row contains these fields:

| Field | Meaning |
|---|---|
| Target | Positive PowerPoint shape id written to `p:spTgt@spid` |
| Effect | One canonical PowerPoint-authored preset class / id / subtype / behavior-tree signature |
| Trigger | Row-specific `on-click`, `with-previous`, or `after-previous`; omitted values inherit the resolved slide Start mode |
| Trigger shape | Optional different top-level group; maps to PowerPoint `On Click of` |
| Duration | Finite positive schedule duration; scalable native behavior trees preserve their internal timing ratios |
| Delay | Finite non-negative row offset; shape-trigger rows use it as `TriggerDelayTime` |
| Order | Positive integer sidecar order; ties retain stable SVG group order, then `effects[]` index |
| Effect options | Effect-specific `direction`, `amount`, `color`, `font_name` (one installed PowerPoint face, required for Change Font; not a CSS list), `relative`, or `size` values from PowerPoint `EffectParameters` |
| Timing options | Repeat count/span, auto-reverse, rewind, accelerate/decelerate, bounce-end ratio, and restart policy |
| Completion / cue | Optional dim/hide behavior and packaged `.m4a`/`.mp3`/`.wav` sound |

Modes resolve before XML writing:

| Mode | Resolution |
|---|---|
| `auto` | Generic entrance only: deterministic semantic mapping from the SVG group id |
| `mixed` | Generic entrance only: deterministic cycle over canonical PowerPoint entrance presets |
| `random` | Generic entrance only: stable seeded choice from the same canonical entrance pool |
| `none` | No object-animation sequence |

The same effective input produces the same `random` choices. When enabled,
`--conversion-trace` records each resolved row and effect, so a generated deck
can be audited without replaying the resolver.

`animation_config.py scaffold` is neutral: object defaults are `none`, and
empty `{}` group placeholders inherit no motion until populated.

Bundled sound discovery/materialization is a workflow concern, not part of the
animation core. After the SVG and object-motion solution are complete,
`sound_sync.py` may copy only selected namespaced ids into
`<project>/sounds/`; new sidecars then reference those project-relative WAV
paths. Existing low-level project-relative/absolute `.m4a`, `.mp3`, and `.wav`
inputs remain compatible. The core never resolves a library id or reads
`templates/sounds/` directly; see [`animations.md`](../../references/animations.md)
§2.2.

---

## 3. Canonical Registry and Compatibility Inputs

The canonical registry contains 203 PowerPoint-authored presets:

| Category | Key prefix | Count | Example |
|---|---|---:|---|
| Entrance | `entrance_*` | 53 | `entrance_bounce` |
| Emphasis | `emphasis_*` | 33 | `emphasis_spin` |
| Motion path | `path_*` | 64 | `path_circle` |
| Exit | `exit_*` | 53 | `exit_faded_zoom` |

The 29 established short names remain valid only as compatibility inputs.
Normalization resolves them to canonical PowerPoint-authored presets before
selection, XML writing, read-back, tracing, or validation.

| Compatibility input | Canonical preset |
|---|---|
| `appear`, `cut` | `entrance_appear` |
| `fade` | `entrance_fade` |
| `fly`, `fly_left`, `fly_right`, `fly_top` | `entrance_fly` |
| `zoom` | `entrance_zoom` |
| `wipe`, `wipe_left`, `wipe_right`, `wipe_up`, `wipe_down` | `entrance_wipe` |
| `split`, `blinds`, `checkerboard`, `dissolve`, `random_bars`, `peek` | matching `entrance_*` preset |
| `wheel`, `box`, `circle`, `diamond`, `plus`, `strips`, `wedge`, `stretch`, `expand`, `swivel` | matching `entrance_*` preset |

`cut` maps to `entrance_appear` because current PowerPoint exposes no separate
Cut object-animation preset. Old Fly/Wipe names desugar to the canonical effect
plus `effect_options.direction`; legacy `wheel` desugars to
`entrance_wheel` plus `amount: 4`. New output never writes those aliases.

Together with the 29 accepted compatibility names, the public input surface
contains 232 keys. New selections, generated sidecars, conversion traces,
writers, and documentation examples use canonical keys; short names exist only
at compatibility input boundaries.

The shipped `pptx_animation_presets.json` contains the PowerPoint-authored
`p:cTn` row for every native effect. Complex effects use combinations of
`p:set`, `p:anim`, `p:animClr`, `p:animEffect`, `p:animMotion`, `p:animRot`,
and `p:animScale`; reducing them to one filter would silently change the
effect. `pptx_animations.py --list` prints the full categorized public
registry; `pptx_animations.py --describe <effect>` prints that effect's exact
option values and shared timing/completion contract.

Native presets map to the object-capable `MsoAnimEffect` values. Media play,
pause, stop, and play-from-bookmark are excluded because they require a
media/bookmark target rather than an SVG-derived shape. Exit effects use the
same entrance-capable `MsoAnimEffect` identity with PowerPoint's exit flag and
serialize as `presetClass="exit"`.

Paragraph/text-range build controls are likewise outside this writer: generated
targets are top-level SVG groups, not paragraph ranges. For that target model,
the public contract covers all PowerPoint effect parameters, timing modifiers,
completion controls, sound, and object-trigger linkage; Speed and smooth
start/end remain derived rather than duplicated.

**Hard rule — no downgrade**:

- Keep all 29 established short names accepted as compatibility inputs.
- Reject an unknown effect, mode, or trigger; never substitute another value.
- Reject booleans and non-finite, out-of-range, or invalidly ordered values.
- Reject a missing slide, missing group, or structural-layer target.
- Keep the generated-route default at `none`; validation does not opt a deck in.

---

## 4. Target Resolution

Generated object animation targets top-level SVG content groups. Explicit SVG
semantics are authoritative; the group-id chrome heuristic is only a fallback
for marker-free legacy SVGs.

| Target state | Behavior |
|---|---|
| Ordinary content group | Animatable; a legacy block resolves one row and `effects[]` may resolve several rows against the same final shape |
| Legacy chrome-like id | Skipped unless explicitly named in `animations.json` |
| Explicit sidecar group override | May override only the legacy chrome-name heuristic |
| `data-pptx-layer` or explicit static role/placeholder | Structural and never animatable |

An explicit sidecar entry cannot turn a Master/Layout/Slide structural layer or
an explicitly marked static page-frame role/placeholder into an animation
target. This boundary preserves PPTX structure even when a legacy id resembles
content.

---

## 5. OOXML Rules

The writer emits animation timing after `p:transition` and before `p:extLst`.
Normally this is one root `p:timing`; nonzero `bounce_end` uses PowerPoint's
native `mc:AlternateContent` with a p14 Choice and non-bounce Fallback. Each
branch contains a `tmRoot`, a `mainSeq` when ordinary Start rows exist, one
`interactiveSeq` per trigger-shape row, unique branch-local `p:cTn@id` values,
and same-slide `p:spTgt` references.

Trigger mapping:

| Public trigger | Object row `p:cTn@nodeType` |
|---|---|
| `on-click` | `clickEffect` |
| `with-previous` | `withEffect` |
| `after-previous` | `afterEffect` |

A row-level `trigger_shape` resolves to a different shape id and writes
PowerPoint's native `interactiveSeq` with `onClick` shape conditions. Its row
remains `clickEffect`; row `delay` becomes `TriggerDelayTime`. Ordinary rows
remain in `mainSeq` and keep the slide Start mode.

Row `trigger` overrides slide Start in both forms. `trigger_shape` implies
`on-click` and conflicts with an explicit non-`on-click` Start. Repeated
`p:spTgt@spid` values are valid distinct Animation Pane rows. Ordinary rows
retain page-wide `order`; trigger-shape rows retain their relative order in
separate `interactiveSeq` branches and do not interleave with `mainSeq`.

The writer does not emit `p:bldP` for grouped content or pictures. Microsoft
defines `p:bldP@spid` for a text-bearing `p:sp`; using it for `p:grpSp` or
`p:pic` creates an invalid build reference. Package validation still accepts a
valid source `p:bldP` that targets a text-bearing shape.

Direct-PPTX preserve mode also tolerates an unchanged legacy `p:bldP` that
targets an existing group/picture. Earlier PPT Master exports wrote this form;
the direct routes fingerprint and preserve it instead of blocking those decks.
New generated output never writes it, and generated-package validation remains
strict.

`entrance_appear` is the visibility-flip exception: its `p:set` behavior is
always 1ms. The configured positive duration remains the row's scheduling span
used when computing the next `after-previous` offset; read-back verifies the
1ms behavior and the resulting timeline offset separately. The compatibility
inputs `appear` and `cut` normalize to this canonical preset.

Other native presets with a
finite duration scale every finite behavior duration and start delay
proportionally, preserving multi-step timing such as bounce and teeter.
PowerPoint-authored instantaneous emphasis presets keep their `indefinite`
behavior duration; their configured duration remains the scheduling span for
the next `after-previous` row.

---

## 6. Validation and Read-Back

Before export, `animation_config.py validate` uses the writer's effect-behavior
test for `bounce_end` and resolves declared sound paths against the project
root. Missing paths, non-files, and unsupported audio extensions fail this
project-level preflight; field-only validation remains filesystem-independent.

Generated export reads every slide back before packaging and compares each
requested row with the serialized result:

- row count and row order, including stable repeated-target rows;
- trigger, optional trigger shape, and shape target;
- resolved effect key, preset class, filter, `presetID`, and `presetSubtype`;
- exact effect options, repeat/reverse/rewind/acceleration/bounce/restart
  semantics, completion behavior, sound relationship, and playback span;
- native behavior-tree signature, serialized behavior duration, and computed
  timeline offset (`entrance_appear` and instantaneous native presets use the
  exceptions above).

After packaging, validation scans every slide part for root timing placement,
duplicate or malformed `p:cTn` ids, missing `p:spTgt` shapes, invalid build
targets, and unsupported generated effect tuples. A mismatch fails export
before the requested output file replaces an existing deck.

`pptx_to_svg.py` reuses that semantic reader and behavior-tree validator for a
finite reverse projection. A row enters `animations.json` only when its current
registry effect/options, pane order, Start trigger, exact behavior duration,
relative delay, and target/optional trigger shape can be represented by unique
top-level slide SVG groups. Repeated targets become `effects[]`. Duration-less
native rows, advanced timing modifiers, sounds, build/media commands, unknown
trees, and unmapped targets remain explicit import diagnostics. This is not a
general PowerPoint timing-tree normalizer.

Narration injection parses and merges the slide DOM. It adds audio timing under
the existing `tmRoot`, allocates fresh ids, and preserves object animation.
For bounce timing it updates both p14 Choice and Fallback; unsupported nested
timing containers still fail safely instead of being duplicated.

Direct-PPTX routes run the structural package validator with generated-effect
enforcement disabled. This permits preservation of source/extension effects and
legacy group build rows while still rejecting corrupt timing IDs or missing
targets. Template fill and native enhancement fingerprint the source
object-animation tree before and after their allowed edits; any semantic change
fails. These routes have no object-animation write ownership.

The conversion trace is also the authoritative input for downstream video
motion. `video_motion_plan.py` preserves the resolved effect/options, direction,
row order, base and repeat-aware playback duration, absolute offset, object
bounds, and narration-derived slide advance while adding only renderer-specific enhancement parameters. Video
renderers must not bypass this read-back result and infer motion from sidecar
delay values alone.

---

## 7. Compatibility Scope

The compatibility contract covers PowerPoint OOXML and PowerPoint read-back.
Other presentation applications may interpret timing trees or filter values
differently; the exporter does not make an unconditional Keynote guarantee.

Official references:

- [Microsoft `MsoAnimEffect` enumeration](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.msoanimeffect)
- [Microsoft `Sequence.AddEffect`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.sequence.addeffect)
- [Microsoft `Effect.Exit`](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.effect.exit)
- [Microsoft animation-filter implementation notes](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/a96dab70-2e72-4319-928d-0eb4b275ce58)
- [Microsoft `p:bldP` implementation restrictions](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/40d17b6d-30c0-4c10-b042-b2597824a820)
- [Open XML SDK time-node values](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.timenodevalues?view=openxml-3.0.1)
- [Open XML SDK shape target](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.shapetarget?view=openxml-3.0.1)

See [`pptx-transitions.md`](./pptx-transitions.md) for the symmetric page-motion
core, MCE handling, and slide-advance contract.
See [`video-motion-plan.md`](./video-motion-plan.md) for the downstream
animation-to-video contract.
