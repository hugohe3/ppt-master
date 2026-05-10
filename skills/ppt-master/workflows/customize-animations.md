---
description: Customize default PPTX animations with per-slide and per-object timing/effect overrides
---

# Customize Animations Workflow

> Standalone post-generation step. Run when the user asks to tune animation order, effects, timing, or object-level reveals. Default PPTX export already has global animations; this workflow only creates `animations.json` overrides when the user wants finer control.

## When to Run

| Condition | Action |
|---|---|
| User asks for object-level animation, reveal order, timing, or effect changes | Run this workflow |
| User only wants the default animated deck | Do not run; normal `svg_to_pptx.py` export is enough |
| `svg_output/*.svg` is missing | Complete the main Executor phase first |
| Existing `animations.json` is present | Validate and edit it; do not overwrite unless the user asks |

---

## 1. Build or Validate the Scaffold

**Mandatory**: use real SVG group ids. Do not invent slide or group keys.

If `animations.json` does not exist:

```bash
python3 skills/ppt-master/scripts/animation_config.py scaffold <project_path>
```

If it already exists:

```bash
python3 skills/ppt-master/scripts/animation_config.py validate <project_path>
```

---

## 2. Read Semantic Context

**Mandatory**: before editing `animations.json`, read the deck's semantic planning files.

| File | Use |
|---|---|
| `<project_path>/design_spec.md` | Understand each slide's content intent, narrative role, and visual emphasis |
| `<project_path>/spec_lock.md` | Confirm page rhythm, layout role, chart/template constraints, and execution contract |
| `<project_path>/notes/total.md` or `<project_path>/notes/*.md` | Use speaker flow to tune reveal order, delays, and emphasis |

**Hard rule**: semantic files determine animation intent; `svg_output/*.svg` determines valid animation targets. Never reference a slide or group id that is absent from the scaffold / SVG scan.

**Missing context**: if one semantic file is absent, state what is missing and proceed with the remaining files plus real SVG group ids. If both `design_spec.md` and `spec_lock.md` are absent, do not infer detailed object choreography; use only conservative defaults and explicit user instructions.

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
| `none` | Disable page transition |
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
| `effect` | One supported page transition effect |
| `duration` | Transition duration in seconds |
| `auto_advance` | Optional seconds before automatic slide advance |

### 3.2 Supported In-Slide Animations

| Effect | Behavior |
|---|---|
| `none` | Exclude the object or slide from in-slide animation |
| `appear` | Visibility flip without motion |
| `fade` | Neutral entrance |
| `fly` | Fly in from bottom |
| `cut` | Cut in from left |
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
| `mixed` | Deterministic varied effects across animated groups |
| `random` | Random effect per animated group |

**Start modes**:

| Trigger | Behavior |
|---|---|
| `after-previous` | Cascade automatically on slide entry |
| `with-previous` | Start together on slide entry |
| `on-click` | One presenter click per animated group |

---

## 4. Edit `animations.json`

**Hard rule**: write only overrides that differ from the default global animation. Unmentioned groups keep the normal export behavior.

| Field | Behavior |
|---|---|
| `transition.effect` | Slide-specific page transition effect |
| `transition.duration` | Slide-specific page transition duration |
| `animation.effect` | Slide-specific default object entrance effect |
| `animation.duration` | Slide-specific default object entrance duration |
| `animation.stagger` | Slide-specific delay between object entrances |
| `animation.trigger` | Slide-specific start mode |
| `groups.<id>.effect` | Object-specific entrance effect, `mixed`, `random`, or `none` |
| `order` | Animation order only; does not change SVG layer order |
| `delay` | Extra seconds before this group starts in `after-previous` mode |
| `duration` | Per-group entrance duration in seconds; vary when semantic weight or pacing calls for it |

Example:

```json
{
  "version": 1,
  "defaults": {
    "transition": { "effect": "fade", "duration": 0.25 },
    "animation": { "effect": "fade", "duration": 0.4, "stagger": 0.2, "trigger": "after-previous" }
  },
  "slides": {
    "03_market": {
      "transition": { "effect": "wipe", "duration": 0.35 },
      "groups": {
        "title": { "effect": "fade", "order": 1 },
        "chart": { "effect": "wipe", "order": 2, "duration": 0.6 },
        "insight": { "effect": "fly", "order": 3, "delay": 0.2 },
        "footer": { "effect": "none" }
      }
    }
  }
}
```

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

**Validation**: the exported native PPTX should reflect the object-level overrides. `--animation none` still disables all per-element animation and overrides `animations.json`.

---

## ✅ Customize Animations Complete

- [x] `animations.json` exists only because object-level customization was requested
- [x] `design_spec.md`, `spec_lock.md`, and available speaker notes were checked before editing animation overrides
- [x] Page transitions and in-slide object animations were planned together
- [x] Transition and object durations were chosen intentionally for the deck's pacing
- [x] `animation_config.py validate` passed
- [x] PPTX re-export completed with custom animation overrides
