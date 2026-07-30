# Page Transitions & Element Animations

[English](./animations.md) | [Chinese](./zh/animations.md)

---

PPT Master writes **page transitions** and optional **element object
animations** as real PowerPoint OOXML, not embedded video. Object animation
includes entrance, emphasis, motion-path, and exit effects. This guide covers
the choices and commands users need; exact effect mappings, the complete
sidecar schema, anchor rules, and package validation live in the
[animation execution reference](../skills/ppt-master/references/animations.md).

## Default Behavior

| Layer | Default | What it means |
|---|---|---|
| Page transition | `fade`, 0.4 seconds | Slides change with a restrained visual transition |
| Element object animation | **`none` (off)** | Each slide appears as a complete page; opt in only when motion helps the presentation |

Changing animation settings does not require regenerating the slides. Rerun `svg_to_pptx.py` against the same `svg_output/`.

## Common Recipes

| Goal | Command |
|---|---|
| Keep the defaults | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project>` |
| Change the page transition | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push` |
| Remove the visual transition | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none` |
| Auto-advance every 5 seconds | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5` |
| Enable automatic element reveals | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto` |
| Use one entrance effect throughout | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade` |
| Reveal elements on click | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| Animate all elements together | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| Slow the reveal sequence | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

## Choose a Page Transition

| Relationship between adjacent slides | Start with |
|---|---|
| Ordinary continuation within one section | `fade` |
| Immediate change with no continuity to preserve | `none` or `cut` |
| Directional steps, timeline, or visible layer progression | `push`, `wipe`, `cover`, or `uncover` with a meaningful direction |
| The same object or scene changes position, size, crop, or appearance | `morph` |
| Section opening, key reveal, or marked state boundary | A selective `split`, `reveal`, `shape`, `flash`, or `random_bars` |
| A repeated collection advances through one spatial frame | `pan`, `conveyor`, or `ferris_wheel`; use Morph when individual objects must retain identity |
| The viewpoint travels around or through a continuous space | `rotate`, `window`, `orbit`, or `fly_through` |
| The theme supports a stage, paper, or physical-page metaphor | A selective `fall_over`, `drape`, `curtains`, `wind`, `prestige`, `peel_off`, `page_curl`, `airplane`, `origami`, or `doors` |
| A disruptive beat represents breakage, collapse, or dispersal | A selective `fracture`, `crush`, `dissolve`, `vortex`, or `shred` |
| A marked reveal benefits from a geometric, timed, or textured pattern | A selective `checkerboard`, `blinds`, `clock`, `ripple`, `honeycomb`, `glitter`, or `comb` |
| A card, panel, gallery, or viewpoint visibly turns or changes face | A selective `switch`, `flip`, `gallery`, `cube`, `box`, or `zoom` |

Keep `fade` or `none` when no other transition adds meaning. Do not change
effects merely to create variety; `random` is appropriate only when
unpredictability is itself intentional.

The 48 canonical transition keys cover all three sections in the current
PowerPoint gallery:

- Subtle: `morph`, `fade`, `push`, `wipe`, `split`, `reveal`, `cut`,
  `random_bars`, `shape`, `uncover`, `cover`, `flash`.
- Exciting: `fall_over`, `drape`, `curtains`, `wind`, `prestige`, `fracture`,
  `crush`, `peel_off`, `page_curl`, `airplane`, `origami`, `dissolve`,
  `checkerboard`, `blinds`, `clock`, `ripple`, `honeycomb`, `glitter`,
  `vortex`, `shred`, `switch`, `flip`, `gallery`, `cube`, `doors`, `box`,
  `comb`, `zoom`, `random`.
- Dynamic Content: `pan`, `ferris_wheel`, `conveyor`, `rotate`, `window`,
  `orbit`, `fly_through`.

The old names `strips`, `circle`, `diamond`, `newsflash`, `plus`, `pull`,
`wedge`, and `wheel` remain accepted only as compatibility inputs. New
sidecars, plans, traces, and output use canonical keys. Compatibility inputs
desugar into a native effect plus its Effect Options—for example, `diamond`
becomes `shape` with `shape: diamond`, and `wedge` becomes `clock` with
`style: wedge`.

Set effect-specific PowerPoint options in
`transition.effect_options`. Direction, shape, pattern, Morph scope, black
screen, page count, and bounce are validated against the selected effect.
Run
`python3 skills/ppt-master/scripts/pptx_animations.py --describe-transition <effect>`
for the exact values. `-t none` removes the visual effect but does not remove
an explicitly configured auto-advance timer.

## Choose a Start Mode

| Start mode | Behavior | Best fit |
|---|---|---|
| `on-click` | One content group appears per click | Live presentations where the speaker controls pacing |
| `with-previous` | All content groups animate together when the slide appears | A single coordinated entrance |
| `after-previous` (default) | Groups appear sequentially without clicks | Kiosk playback, walkthroughs, and narrated decks |

`--recorded-narration` does not support `on-click`; use `after-previous` or `with-previous` for narrated or video-ready output.

## Choose an Object Animation

Start with `none`. When object motion has a communication job, choose its
lifecycle before its visual effect:

| Communication job | Choice | Boundary |
|---|---|---|
| Reveal information in reading or narration order | `auto` or a native `entrance_*` key | This is the usual object-animation case |
| Redirect attention to an already visible object | An explicit `emphasis_*` key | Do not use it as the object's first reveal |
| Show meaningful spatial or causal movement | An explicit `path_*` key, or Morph across adjacent slides | The path itself should carry meaning; deliberate background ambience is an advanced exception |
| Remove, replace, or make room for content on the same slide | An explicit `exit_*` key | A normal slide change already removes the old page |
| Add deterministic or seeded variation to generic entrances | `mixed` or `random` | These modes still select entrance effects only |
| No clear motion task | `none` | Keep the slide static |

The canonical registry contains 203 PowerPoint-native keys: 53 entrance, 33
emphasis, 64 motion path, and 53 exit presets. New selections, sidecars,
automatic choices, traces, and examples use these category-qualified keys.
`auto`, `mixed`, and `random` select entrances only. Use an explicit canonical
key for emphasis, motion-path, or exit behavior.
The 29 established short names remain accepted only as compatibility inputs;
they normalize before writing and do not retain a second behavior engine.
Old Fly direction names all normalize to `entrance_fly`, and old Wipe
direction names all normalize to `entrance_wipe`; their direction is preserved
as an option rather than another canonical preset. Legacy `wheel` keeps four
spokes. Run
`python3 skills/ppt-master/scripts/pptx_animations.py --list` for the complete
categorized list. The four media playback commands are handled by the
audio/video workflows because they require media or bookmark targets.

## Customize Specific Objects

Use `animations.json` only when deck-wide settings are not enough—for example,
one object entering, moving, drawing attention, and then leaving. List the real
groups, write sparse overrides for only the affected slides and objects,
validate, and export. `scaffold` is an optional neutral editing starter: it
sets the default object effect to `none`, and untouched `{}` group entries do
not enable animation.

```bash
python3 skills/ppt-master/scripts/animation_config.py list-groups <project>
python3 skills/ppt-master/scripts/animation_config.py validate <project>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

The sidecar targets stable top-level `<g id="...">` content groups. A group ID
is a PowerPoint shape-target anchor, not an Animation Pane row. The compatible
single-effect object still creates one row; an `effects[]` array can create
several ordered rows that all target the same shape:

```json
{
  "version": 1,
  "slides": {
    "03_threshold": {
      "animation": { "trigger": "after-previous" },
      "groups": {
        "risk-marker": {
          "effects": [
            { "effect": "entrance_fade", "order": 1, "duration": 0.25 },
            { "effect": "path_right", "order": 2, "delay": 0.1, "duration": 0.7 },
            { "effect": "emphasis_teeter", "order": 3, "trigger": "with-previous", "duration": 0.45 },
            { "effect": "exit_fade", "order": 4, "trigger_shape": "details-button", "duration": 0.3 }
          ]
        }
      }
    }
  }
}
```

A populated group uses either the legacy single-effect fields or the
`{ "effects": [...] }` form, never both. `effects` must be non-empty, and every
row names an explicit `effect`. Existing single-effect sidecars remain fully
compatible.

Common row fields are:

| Field | Purpose |
|---|---|
| `effect` | Select one explicit effect; the legacy form may use `none` to keep that object static |
| `trigger` | Override this row's Start mode; otherwise inherit the slide animation trigger |
| `order` | Order ordinary rows across the slide without changing slide layers; trigger-shape rows remain in separate interactive sequences |
| `delay` | Add a pause to this row's resolved Start behavior |
| `duration` | Override this row's scheduled animation duration |
| `effect_options` | Set effect-specific `direction`, `amount`, `color`, `font_name`, `relative`, or `size` |
| `trigger_shape` | Trigger this row when another top-level group is clicked (PowerPoint **On Click of**) |
| Timing modifiers | `repeat_count`/`repeat_duration`, `auto_reverse`, `rewind`, `accelerate`, `decelerate`, `bounce_end`, and `restart` |
| Completion | `after_effect` (dim/hide) and a `.m4a`/`.mp3`/`.wav` `sound` path |

`order`, `delay`, `duration`, `trigger`, and `trigger_shape` are resolved per
row. The slide-level animation trigger is inheritance only. `trigger_shape`
implies `on-click`; if the row also declares `trigger`, it must be
`on-click`.

Use `python3 skills/ppt-master/scripts/pptx_animations.py --describe
<canonical_effect>` to see exactly which options that effect accepts. Speed is
controlled by `duration`; smooth start/end are controlled by
`accelerate`/`decelerate`. Change Font's `font_name` is one concrete
target-installed PowerPoint face, never a CSS font stack.

`trigger_shape` points to a different group id on the same slide and affects
only its row. Recorded narration rejects any row that resolves to `on-click`,
including trigger-shape rows.

When a user asks the AI to tune individual objects, use the [`customize-animations`](../skills/ppt-master/workflows/stages/customize-animations.md) stage. The full sidecar schema and target-validation rules remain in the [animation execution reference](../skills/ppt-master/references/animations.md).

## Validation & Compatibility

PPT Master validates animation settings strictly: unknown effects or Start modes, invalid timing values, missing slide/group references, and attempts to animate structural objects fail instead of silently changing behavior. Export also reads the candidate PPTX back before replacing an existing output.

| Boundary | User-facing consequence |
|---|---|
| Animation target | Element animation operates on logical top-level content-group anchors; one anchor may own several Animation Pane rows |
| Static structure | Backgrounds, Master/Layout content, placeholders, and page chrome remain static |
| Unsupported object builds | No paragraph/text-range builds, custom freeform motion-path authoring, native Chart/SmartArt build sequencing, or media playback commands are inferred from grouped SVG content |
| Output route | Animation exists in the native PPTX generated from `svg_output/`; `svg_final/` is a static preview |
| Existing PPTX routes | Template Fill and Native Enhance preserve source object animation rather than translating it into this generated-deck model |
| Playback compatibility | Microsoft PowerPoint desktop is the primary validation target; Keynote, WPS, LibreOffice, and older Office versions may remap or omit individual effects |

For the full CLI reference, see [`svg-pipeline.md`](../skills/ppt-master/scripts/docs/svg-pipeline.md). For exact effect definitions, sidecar requirements, anchor fallback logic, and OOXML read-back rules, see the [animation execution reference](../skills/ppt-master/references/animations.md).
