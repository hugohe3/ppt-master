# Page Transitions & Per-Element Animations

PPT Master's exported PPTX supports **page transitions** (slide-to-slide) and **per-element entrance animations** (within a slide). Both are controlled by `svg_to_pptx.py` CLI flags and ship as real OOXML — they animate inside PowerPoint and Keynote, no embedded video.

## Defaults

| Layer | Default | Why |
|---|---|---|
| Page transition | `fade`, 0.4s | Calm baseline that suits most decks |
| Per-element animation | off | Existing users see no behavior change |

To regenerate a deck with different settings, rerun `svg_to_pptx.py` against the same `svg_output/` (or `svg_final/`) — no need to rerun the LLM.

## Page Transitions

```bash
# Pick a different effect
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push --transition-duration 0.6

# Disable
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none

# Auto-advance every 5 seconds (kiosk-style playback)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5
```

Available effects: `fade`, `push`, `wipe`, `split`, `strips`, `cover`, `random`.

Flags:

- `-t/--transition` — effect name, or `none` to disable. Default: `fade`.
- `--transition-duration` — seconds, default `0.4`.
- `--auto-advance` — seconds; omit for presenter-controlled advance.

## Per-Element Animations

Off by default. When enabled, entering a slide → first click reveals the first semantic group; each subsequent click reveals the next group in z-order.

```bash
# Cascade every group with fade (recommended starting point)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# Auto-vary effects within a slide (title fades; later groups cycle a curated pool)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed

# Slow each reveal down to 0.5s
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade --animation-duration 0.5
```

22 single effects: `appear`, `fade`, `fly`, `cut`, `zoom`, `wipe`, `split`, `blinds`, `checkerboard`, `dissolve`, `random_bars`, `peek`, `wheel`, `box`, `circle`, `diamond`, `plus`, `strips`, `wedge`, `stretch`, `expand`, `swivel`. Plus two auto-vary modes:

- `mixed` — deterministic. The first animated group on each slide uses `fade`; later groups cycle through a curated visible-effect pool across the deck.
- `random` — samples from the same pool.

The pool excludes `appear` because it has no visible motion.

Flags:

- `-a/--animation` — effect name, `mixed`, `random`, or `none`. Default: `none`.
- `--animation-duration` — per-element seconds, default `0.3`.
- `--animation-stagger` — kept for backward compatibility; ignored by click-by-click timing.

## Anchor Logic — Top-Level `<g id="...">`

Per-element animations are anchored on **top-level `<g id="...">` groups** in the SVG (e.g. `<g id="cover-title">`, `<g id="card-1">`). One group = one click reveal.

Aim for **3–8 semantic groups per slide**. This is also the granularity PowerPoint uses for group-select / group-move, so it improves editing ergonomics regardless of animation.

**Fallback for flat SVGs** (no top-level `<g>` wrappers, only raw `<rect>` / `<text>` / `<path>` at the root):

- ≤ 8 visible top-level primitives → each becomes one anchor (capped to avoid 70+ atom cascades on dense pages).
- > 8 → animation is skipped on that slide. The slide still renders, just without entrance animation.

Executors should wrap logical sections in `<g id>` regardless of whether you plan to animate. The Executor reference (`skills/ppt-master/references/shared-standards.md`) requires it.

## Limitations

- **Native shapes mode only.** Per-element animation needs editable shape anchors. `--only legacy` produces one image per slide and has no element granularity to animate; that mode is unaffected by `-a/--animation` and only honors `-t/--transition`.
- **Office version drift on element animations.** Effects use the `<p:animEffect filter=...>` path (vs. `presetID` lookup tables) to stay stable across Office versions. Most filters render identically in PowerPoint 2016+; older Office may downgrade some filters to plain Appear.
- **PNG fallback (compat mode) is for visual rendering only.** Transitions and animations live in the slide XML, not in the PNG, so disabling compat mode does not affect either layer.

## Quick Reference

| Goal | Command |
|---|---|
| Disable transitions | `-t none` |
| Change transition effect | `-t push` (or any from the list above) |
| Slower transition | `--transition-duration 0.8` |
| Auto-play | `--auto-advance 5` |
| Enable element animation | `--animation fade` |
| Auto-vary element animation | `--animation mixed` |
| Slower per-element reveal | `--animation-duration 0.5` |

See also: [`scripts/docs/svg-pipeline.md`](../skills/ppt-master/scripts/docs/svg-pipeline.md) for the full `svg_to_pptx.py` reference.
