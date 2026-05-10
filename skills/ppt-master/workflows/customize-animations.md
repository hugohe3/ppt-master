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

## 2. Edit `animations.json`

**Hard rule**: write only overrides that differ from the default global animation. Unmentioned groups keep the normal export behavior.

| Field | Behavior |
|---|---|
| `effect` | Any supported entrance effect, `mixed`, `random`, or `none` |
| `order` | Animation order only; does not change SVG layer order |
| `delay` | Extra seconds before this group starts in `after-previous` mode |
| `duration` | Per-group entrance duration in seconds |

Example:

```json
{
  "version": 1,
  "slides": {
    "03_market": {
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

## 3. Validate and Export

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
- [x] `animation_config.py validate` passed
- [x] PPTX re-export completed with custom animation overrides
