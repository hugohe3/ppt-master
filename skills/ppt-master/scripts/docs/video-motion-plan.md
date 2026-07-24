# Video Motion Plan

`video_motion_plan.py` converts a resolved SVG-to-PPTX conversion trace into a
renderer-neutral motion plan. It is the handoff between PPT Master's canonical
custom animation and any SVG-native or post-production video renderer.

The planner exists to prevent a video path from reducing animation to delay
values. The conversion trace is authoritative because it already contains the
resolved object target, effect, direction tuple, order, duration, offset, slide
advance, and native object bounds after sidecar inheritance and narration
synchronization.

---

## 1. Generate a Resolved Source Trace

For a narrated deck, generate the trace from the narrated export so its offsets
and slide advances include the final audio timing:

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> \
  --recorded-narration audio \
  --conversion-trace \
  -o <project_path>/validation/video_motion_source.pptx
```

Then build the motion plan:

```bash
python3 skills/ppt-master/scripts/video_motion_plan.py \
  <project_path>/validation/video_motion_source.pptx.trace.json \
  -o <project_path>/validation/video_motion_plan.json \
  --style adaptive \
  --force
```

`restrained` and `dynamic` are explicit intensity alternatives. `adaptive` is
the default and adjusts enhancement strength from page role, animated-object
count, and object area.

---

## 2. Authority and Locks

The downstream renderer must preserve:

- object identity and SVG group id;
- object order;
- source effect;
- semantic direction;
- resolved start time and slide timing anchor.

The video layer may optimize only the declared `optimizer_scope` parameters:
easing, travel distance, opacity, scale, mask feather, blur, motion blur, and
overshoot. These additions can make motion feel more cinematic without
rewriting the presentation's choreography.

Do not derive a video plan directly from raw `animations.json` or
`narration_animations.json`. Raw sidecars may still contain inheritance,
`auto`, timing modes, or narration-relative values. Always use the resolved
conversion trace.

---

## 3. Effect Mapping

Each object keeps `source_effect` and receives a compatible video family:

| Source effect | Video family |
|---|---|
| `appear` | `hard_reveal` |
| `fade` | `soft_fade` |
| `dissolve` | `grain_dissolve` |
| `fly*`, `cut` | `directional_slide` |
| `wipe*`, `peek` | `soft_mask_reveal` |
| `zoom`, `expand`, `stretch` | `focus_scale` |
| `split` | `split_mask` |
| `box`, `circle`, `diamond`, `plus` | `shape_mask` |
| `blinds`, `checkerboard`, `random_bars`, `strips`, `wedge`, `wheel` | `pattern_reveal` |
| `swivel` | `soft_swivel` |

This mapping is an enhancement contract, not permission to substitute an
unrelated effect. A directional slide remains directional; a wipe remains a
mask reveal.

---

## 4. Output Contract

The output schema is `ppt-master.video-motion-plan.v1`. Each slide records:

- SVG source and canvas size;
- page role;
- slide duration and its source;
- resolved transition;
- ordered animated objects.

Each object records:

- `group_id`, native `shape_id`, and order;
- source effect and trigger;
- absolute `start_ms` and `duration_ms`;
- native `bounds_emu` and normalized area;
- renderer parameters under `video`.

The planner rejects click-triggered animation because a rendered video has no
interactive click event. Re-export with click-free `after-previous` or
`with-previous` timing first.

---

## 5. Current Boundary

This script owns the semantic handoff and deterministic enhancement policy. It
does not encode video by itself. A renderer that consumes the plan must report
unsupported families instead of silently falling back to delay-only fades.
