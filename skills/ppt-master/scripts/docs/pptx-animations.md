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

One resolved animation-pane row contains these fields:

| Field | Meaning |
|---|---|
| Target | Positive PowerPoint shape id written to `p:spTgt@spid` |
| Effect | One canonical PowerPoint-authored preset class / id / subtype / behavior-tree signature |
| Trigger | `on-click`, `with-previous`, or `after-previous` |
| Duration | Finite positive schedule duration; scalable native behavior trees preserve their internal timing ratios |
| Delay | Finite non-negative offset used by `after-previous` |
| Order | Positive integer sidecar order; ties retain stable SVG order |

Modes resolve before XML writing:

| Mode | Resolution |
|---|---|
| `auto` | Deterministic semantic mapping from the SVG group id |
| `mixed` | Deterministic cycle over canonical PowerPoint entrance presets |
| `random` | Stable seeded choice from the same canonical preset pool |
| `none` | No object-animation sequence |

The same effective input produces the same `random` choices. When enabled,
`--conversion-trace` records each resolved row and effect, so a generated deck
can be audited without replaying the resolver.

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
Cut object-animation preset. The old directional Fly/Wipe names remain accepted
as interface aliases, but direction is not part of the canonical key and is not
preserved: they normalize to PowerPoint's base `entrance_fly` or
`entrance_wipe` preset.

Together with the 29 accepted compatibility names, the public input surface
contains 232 keys. New selections, generated sidecars, conversion traces,
writers, and documentation examples use canonical keys; short names exist only
at compatibility input boundaries.

The shipped `pptx_animation_presets.json` contains the PowerPoint-authored
`p:cTn` row for every native effect. Complex effects use combinations of
`p:set`, `p:anim`, `p:animClr`, `p:animEffect`, `p:animMotion`, `p:animRot`,
and `p:animScale`; reducing them to one filter would silently change the
effect. `pptx_animations.py --list` prints the full categorized public
registry.

Native presets map to the object-capable `MsoAnimEffect` values. Media play,
pause, stop, and play-from-bookmark are excluded because they require a
media/bookmark target rather than an SVG-derived shape. Exit effects use the
same entrance-capable `MsoAnimEffect` identity with PowerPoint's exit flag and
serialize as `presetClass="exit"`.

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
| Ordinary content group | Animatable |
| Legacy chrome-like id | Skipped unless explicitly named in `animations.json` |
| Explicit sidecar group override | May override only the legacy chrome-name heuristic |
| `data-pptx-layer` or explicit static role/placeholder | Structural and never animatable |

An explicit sidecar entry cannot turn a Master/Layout/Slide structural layer or
an explicitly marked static page-frame role/placeholder into an animation
target. This boundary preserves PPTX structure even when a legacy id resembles
content.

---

## 5. OOXML Rules

The writer emits one root-level `p:timing` after `p:transition` and before
`p:extLst`. Its animation tree contains a `tmRoot`, one `mainSeq`, unique
`p:cTn@id` values, and `p:spTgt` references to shapes on the same slide.

Trigger mapping:

| Public trigger | Object row `p:cTn@nodeType` |
|---|---|
| `on-click` | `clickEffect` |
| `with-previous` | `withEffect` |
| `after-previous` | `afterEffect` |

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

Generated export reads every slide back before packaging and compares each
requested row with the serialized result:

- row count and row order;
- trigger and shape target;
- resolved effect key, preset class, filter, `presetID`, and `presetSubtype`;
- native behavior-tree signature, serialized behavior duration, and computed
  timeline offset (`entrance_appear` and instantaneous native presets use the
  exceptions above).

After packaging, validation scans every slide part for root timing placement,
duplicate or malformed `p:cTn` ids, missing `p:spTgt` shapes, invalid build
targets, and unsupported generated effect tuples. A mismatch fails export
before the requested output file replaces an existing deck.

Narration injection parses and merges the slide DOM. It adds audio timing under
the existing `tmRoot` child list, allocates fresh time-node ids, and preserves
the object-animation sequence. It does not replace an existing `p:timing` tree.
The merge accepts only a direct `p:sld/p:timing` source tree; a timing tree
wrapped in `mc:AlternateContent` or another non-root container fails safely
instead of being rewritten or duplicated.

Direct-PPTX routes run the structural package validator with generated-effect
enforcement disabled. This permits preservation of source/extension effects and
legacy group build rows while still rejecting corrupt timing IDs or missing
targets. Template fill and native enhancement fingerprint the source
object-animation tree before and after their allowed edits; any semantic change
fails. These routes have no object-animation write ownership.

The conversion trace is also the authoritative input for downstream video
motion. `video_motion_plan.py` preserves the resolved effect tuple, direction,
row order, duration, absolute offset, object bounds, and narration-derived slide
advance while adding only renderer-specific enhancement parameters. Video
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
