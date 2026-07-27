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
| Use one native emphasis effect | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation emphasis_spin` |
| Use one native motion path | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation path_circle` |
| Use one native exit effect | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation exit_fade` |
| Reveal elements on click | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| Animate all elements together | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| Slow the reveal sequence | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

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

## Choose an Effect

| Choice | Use it when |
|---|---|
| `auto` | You want PPT Master to choose suitable effects from each content group's role; this is the recommended opt-in |
| A native `entrance_*` key | You want one of PowerPoint's 53 native entrance presets |
| A native `emphasis_*` key | An already visible object should draw attention or change appearance |
| A native `path_*` key | An object should follow one of PowerPoint's 64 motion paths |
| A native `exit_*` key | An object should leave the slide during the sequence |
| `mixed` | You need the compatible deterministic mode over canonical PowerPoint presets |
| `random` | You want deterministic variation from the same canonical preset pool |
| `none` | You want to disable element animation |

The canonical registry contains 203 PowerPoint-native keys: 53 entrance, 33
emphasis, 64 motion path, and 53 exit presets. New selections, sidecars,
automatic choices, traces, and examples use these category-qualified keys.
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

Use `animations.json` only when deck-wide settings are not enough—for example, title first, chart second, conclusion last. The easiest path is to generate a complete scaffold from the actual slide groups, edit it, validate it, and export:

```bash
python3 skills/ppt-master/scripts/animation_config.py scaffold <project>
python3 skills/ppt-master/scripts/animation_config.py validate <project>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

The generated sidecar targets stable top-level `<g id="...">` content groups. Common per-object fields are:

| Field | Purpose |
|---|---|
| `effect` | Override the object effect; use `none` to keep that object static |
| `order` | Change reveal order without changing slide layer order |
| `delay` | Add a pause in `after-previous`, or after clicking `trigger_shape` |
| `duration` | Override that object's scheduled animation duration |
| `effect_options` | Set effect-specific `direction`, `amount`, `color`, `font_name`, `relative`, or `size` |
| `trigger_shape` | Trigger this row when another top-level group is clicked (PowerPoint **On Click of**) |
| Timing modifiers | `repeat_count`/`repeat_duration`, `auto_reverse`, `rewind`, `accelerate`, `decelerate`, `bounce_end`, and `restart` |
| Completion | `after_effect` (dim/hide) and a `.m4a`/`.mp3`/`.wav` `sound` path |

Use `python3 skills/ppt-master/scripts/pptx_animations.py --describe
<canonical_effect>` to see exactly which options that effect accepts. Speed is
controlled by `duration`; smooth start/end are controlled by
`accelerate`/`decelerate`.

`trigger_shape` is group-only and points to a different group id on the same
slide. It affects only that row; the slide Start mode still controls all other
rows. Recorded narration rejects interactive trigger-shape animations.

When a user asks the AI to tune individual objects, use the [`customize-animations`](../skills/ppt-master/workflows/stages/customize-animations.md) stage. The full sidecar schema and target-validation rules remain in the [animation execution reference](../skills/ppt-master/references/animations.md).

## Validation & Compatibility

PPT Master validates animation settings strictly: unknown effects or Start modes, invalid timing values, missing slide/group references, and attempts to animate structural objects fail instead of silently changing behavior. Export also reads the candidate PPTX back before replacing an existing output.

| Boundary | User-facing consequence |
|---|---|
| Animation target | Element animation operates on logical top-level content groups, not every SVG atom |
| Static structure | Backgrounds, Master/Layout content, placeholders, and page chrome remain static |
| Output route | Animation exists in the native PPTX generated from `svg_output/`; `svg_final/` is a static preview |
| Existing PPTX routes | Template Fill and Native Enhance preserve source object animation rather than translating it into this generated-deck model |
| Playback compatibility | Microsoft PowerPoint desktop is the primary validation target; Keynote, WPS, LibreOffice, and older Office versions may remap or omit individual effects |

For the full CLI reference, see [`svg-pipeline.md`](../skills/ppt-master/scripts/docs/svg-pipeline.md). For exact effect definitions, sidecar requirements, anchor fallback logic, and OOXML read-back rules, see the [animation execution reference](../skills/ppt-master/references/animations.md).
