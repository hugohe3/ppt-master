# Page Transitions & Element Animations

[English](./animations.md) | [Chinese](./zh/animations.md)

---

PPT Master writes **page transitions** and optional **element entrance animations** as real PowerPoint OOXML, not embedded video. This guide covers the choices and commands users need; exact effect mappings, the complete sidecar schema, anchor rules, and package validation live in the [animation execution reference](../skills/ppt-master/references/animations.md).

## Default Behavior

| Layer | Default | What it means |
|---|---|---|
| Page transition | `fade`, 0.4 seconds | Slides change with a restrained visual transition |
| Element entrance animation | **`none` (off)** | Each slide appears as a complete page; opt in only when a reveal sequence helps the presentation |

Changing animation settings does not require regenerating the slides. Rerun `svg_to_pptx.py` against the same `svg_output/`.

## Common Recipes

| Goal | Command |
|---|---|
| Keep the defaults | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project>` |
| Change the page transition | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push` |
| Remove the visual transition | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none` |
| Auto-advance every 5 seconds | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5` |
| Enable automatic element reveals | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto` |
| Use one entrance effect throughout | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade` |
| Reveal elements on click | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| Animate all elements together | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| Slow the reveal sequence | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

Available page-transition effects are `fade`, `push`, `wipe`, `split`, `strips`, `cover`, and `random`. `-t none` removes the visual effect but does not remove an explicitly configured auto-advance timer.

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
| A named effect such as `fade`, `wipe`, `fly`, or `zoom` | You want one consistent entrance style across the deck |
| `mixed` | You need the legacy deterministic effect rotation |
| `random` | You want deterministic variation from the supported legacy pool |
| `none` | You want to disable element animation |

The complete supported effect list and its exact PowerPoint mapping belong to the [animation execution reference](../skills/ppt-master/references/animations.md), so the user guide does not duplicate that contract.

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
| `effect` | Override the entrance effect; use `none` to keep that object static |
| `order` | Change reveal order without changing slide layer order |
| `delay` | Add a pause before the object in `after-previous` mode |
| `duration` | Override that object's scheduled entrance duration |

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
