# Page Transitions & Per-Element Animations

Execution contract for generated-PPTX **page transitions** and **per-element
object animations**. This file owns defaults, sidecar semantics, anchor
selection, validation, and package read-back.

## 1. Defaults

| Layer | Default | Why |
|---|---|---|
| Page transition | CLI: `fade`, 0.4s | Calm baseline that suits most decks; the public Python builder retains its legacy 0.5s default |
| Per-element animation | **`none` (off)** | A page appears as a whole. Auto-firing element builds are an unsolicited "AI deck" tell, so object animation is opt-in. Turn on the content-aware canonical entrance policy with `-a auto`, or select one PowerPoint-native `entrance_*`, `emphasis_*`, `path_*`, or `exit_*` key explicitly |

To regenerate a deck with different settings, rerun `svg_to_pptx.py` against the same `svg_output/` — no need to rerun the LLM. `-s final` is reserved for diagnostic comparison and is not a supported release source. To turn per-element animation on for the whole deck, pass `-a auto`.

---

## 2. Custom Object-Level Animation

Per-element animation is off by default. To enable it deck-wide, pass `-a auto` at export (no config needed). When a deck instead needs specific object timing — for example title first, chart second, annotation last — use the optional `animations.json` sidecar. The SVG remains the visual source; the custom stage may rewrite its grouping hierarchy, ids, and bounds to create better semantic anchors without changing visible output, while the sidecar controls PPTX animation behavior.

Run the [`customize-animations`](../workflows/stages/customize-animations.md) post-processing stage when the user asks to tune animation order, effects, timing, or object-level reveals.

**Hard rule — semantic anchors before sidecar**: for custom object-level
animation, do not scaffold or choreograph directly from the SVG's pre-existing
`<g>` list. First derive reveal units from page meaning and narration, audit
every page, and rewrite coarse or fragmented ordinary Slide-local groups
without changing visible output. Only the post-regroup top-level ids are valid
custom-animation anchors.

```bash
# Inspect the real anchors after the semantic regrouping pass
python3 skills/ppt-master/scripts/animation_config.py list-groups <project>

# Build an editable scaffold from the post-regroup anchors when useful
python3 skills/ppt-master/scripts/animation_config.py scaffold <project>

# Validate references before export
python3 skills/ppt-master/scripts/animation_config.py validate <project>

# Export reads <project>/animations.json automatically when present
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

Single-slide sidecar excerpt (repeat the complete slide block for every SVG in `svg_output/`):

```json
{
  "version": 1,
  "defaults": {
    "transition": { "effect": "fade", "duration": 0.4 },
    "animation": { "effect": "auto", "duration": 0.4, "stagger": 0.5, "trigger": "after-previous" }
  },
  "slides": {
    "03_market": {
      "transition": { "effect": "fade", "duration": 0.4 },
      "animation": { "effect": "auto", "duration": 0.4, "stagger": 0.5, "trigger": "after-previous" },
      "groups": {
        "title": { "effect": "entrance_fade", "order": 1 },
        "chart": { "effect": "entrance_wipe", "order": 2, "duration": 0.6 },
        "insight": { "effect": "entrance_fly", "order": 3, "delay": 0.2 }
      }
    }
  }
}
```

Rules:

- `slides` keys match SVG stems (`03_market.svg` → `03_market`).
- `groups` keys match top-level `<g id="...">` anchors.
- `effect: none` removes that group from the object-animation sequence.
- `order` changes animation order only; it does not change slide layering.
- `delay` is seconds before that group starts in `after-previous` mode.
- `duration` overrides the per-group schedule duration. `entrance_appear`
  remains a 1ms visibility flip, and instantaneous native emphasis presets
  retain their PowerPoint-authored duration; the configured value still spaces
  the next `after-previous` row.
- `--animation none` overrides the sidecar and disables all per-element animation.
- An explicit sidecar group may override the legacy chrome-name heuristic, but it cannot override `data-pptx-layer` or an explicit static role/placeholder marker.
- Unknown effects, modes, or triggers and invalid numeric/order fields fail validation; no fallback effect is substituted.

**Declared inheritance for omitted sidecar fields**:

- The whole `animations.json` artifact is optional. When absent, normal exporter CLI resolution applies.
- In any existing sparse sidecar, an omitted slide transition/animation property inherits the matching `defaults.transition` / `defaults.animation` property; when that defaults property is also absent, normal exporter CLI resolution applies. Explicit CLI overrides still win. Current authoring writes each slide's complete transition and animation blocks.
- A group override inherits `effect` and `duration` from its resolved slide animation; omitted `order` and `delay` use the exporter's sidecar resolution.

---

## 3. Page Transitions

```bash
# Pick a different effect
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push --transition-duration 0.6

# Remove the visual transition
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none

# Auto-advance every 5 seconds (kiosk-style playback)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5

# Auto-advance with no visual transition
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none --auto-advance 5
```

The named effects cover the complete current PowerPoint transition gallery:

- Subtle: `morph`, `fade`, `push`, `wipe`, `split`, `reveal`, `cut`,
  `random_bars`, `shape`, `uncover`, `cover`, `flash`.
- Exciting: `fall_over`, `drape`, `curtains`, `wind`, `prestige`, `fracture`,
  `crush`, `peel_off`, `page_curl`, `airplane`, `origami`, `dissolve`,
  `checkerboard`, `blinds`, `clock`, `ripple`, `honeycomb`, `glitter`,
  `vortex`, `shred`, `switch`, `flip`, `gallery`, `cube`, `doors`, `box`,
  `comb`, `zoom`, `random`.
- Dynamic Content: `pan`, `ferris_wheel`, `conveyor`, `rotate`, `window`,
  `orbit`, `fly_through`.

Established low-level aliases remain accepted for compatibility and normalize
to current gallery effects: `strips` → `wipe`; `circle` / `diamond` / `plus`
→ `shape`; `newsflash` → `flash`; `pull` → `uncover`; and `wedge` / `wheel`
→ `clock`.
`none` removes the visual effect. Effects that require newer Office namespaces
carry a real PowerPoint effect in `mc:Choice` and a `fade` fallback for older
consumers; validation requires the requested primary effect and never accepts
the fallback as a silent substitute.

Flags:

- `-t/--transition` — effect name, or `none` for no visual transition. Default: `fade`. `none` does not remove an explicitly configured automatic advance.
- `--transition-duration` — seconds, default `0.4`.
- `--auto-advance` — seconds; click remains enabled, so the slide advances on click or when the timer expires. Omit for presenter-controlled advance.

**Hard rule — no silent downgrade**: an unknown transition effect or invalid/non-finite duration fails export. It is never replaced by `fade`. Recorded narration keeps the resolved visual transition; `-t none --recorded-narration ...` writes narration-driven advance timing without restoring a visual effect.

---

## 4. Per-Element Animations

Off by default — enable deck-wide with `-a auto` (or another effect). Once enabled, three Start modes are available — these mirror PowerPoint's animation-pane "Start" dropdown:

- **`on-click`** — entering a slide → first click reveals the first semantic group; each subsequent click reveals the next group in z-order. Suits live presentations where the speaker paces reveals. Forbidden with `--recorded-narration` because video-ready exports need click-free playback.
- **`with-previous`** — all groups start together on slide entry, playing their object animation in parallel. Stagger ignored.
- **`after-previous`** (default) — first group fires on slide entry, subsequent groups cascade after the previous one finishes, with `--animation-stagger` extra spacing. Suits kiosk playback, recorded walkthroughs, or anyone who wants visual flow without clicking.

```bash
# Default behavior (no flags): page transitions only, no per-element builds
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>

# Enable per-element animation deck-wide (auto effect + after-previous cascade)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto

# Enable with a single canonical effect (cascades via after-previous)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade

# Enable and switch to on-click for live presentations (presenter controls pacing)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click

# Custom pacing
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed \
        --animation-stagger 0.7 --animation-duration 0.5

# All groups animate in unison on slide entry
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous
```

The registry exposes two layers:

- **203 PowerPoint-native object presets**: 53 `entrance_*` presets, 33
  `emphasis_*` effects, 64 `path_*` motion paths, and 53 `exit_*` effects.
  Examples include `entrance_bounce`, `emphasis_spin`, `path_circle`, and
  `exit_faded_zoom`. Each native key carries the complete PowerPoint-authored
  behavior tree, not a generic filter approximation.
- **29 legacy compatibility inputs**: `appear`, `fade`, `fly`, `fly_left`,
  `fly_right`, `fly_top`, `cut`, `zoom`, `wipe`, `wipe_left`, `wipe_right`,
  `wipe_up`, `wipe_down`, `split`, `blinds`, `checkerboard`, `dissolve`,
  `random_bars`, `peek`, `wheel`, `box`, `circle`, `diamond`, `plus`,
  `strips`, `wedge`, `stretch`, `expand`, `swivel`.

Run the registry command for the exact categorized key list:

```bash
python3 skills/ppt-master/scripts/pptx_animations.py --list
```

Compatibility names normalize before selection and writing: for example,
`fade` resolves to `entrance_fade`; every old Fly direction name resolves to
`entrance_fly`; every old Wipe direction name resolves to `entrance_wipe`; and
`cut` resolves to `entrance_appear` because current PowerPoint has no separate
Cut object effect. These names are accepted only as compatibility inputs.
Automatic selection, new sidecars, conversion traces, and writers use
canonical keys.

The native keys mirror the object-capable `MsoAnimEffect` surface. The four
media commands—play, pause, stop, and play from bookmark—are not object effects
for SVG groups and remain owned by the audio/video workflows.

- `auto` (recommended when enabling automatic entrances) — map a canonical
  PowerPoint entrance preset from the group's SVG id. Information-dense elements get a
  single stable effect: `chart` / `table` / `legend` / `timeline` / `track` →
  `entrance_wipe`; `card-*` / `pillar-*` / `item-*` / `step-*` / `stage-*` /
  `tier-*` / `principle-*` → `entrance_fly`; `title` / `chapter-*` /
  `section-*` / `cover-*` / `tagline` / `subtitle` → `entrance_fade`;
  `takeaway` / `callout` / `quote` / `source` / `conclusion` / `note` →
  `entrance_fade`. Image-like ids `hero` / `figure-*` / `image` / `img-*` /
  `kpi` instead cycle a richer canonical entrance pool so multiple images vary
  across the deck. Unmatched ids cycle through `entrance_fade` /
  `entrance_wipe` / `entrance_fly` / `entrance_zoom`.
- `mixed` (legacy mode name) — deterministic. The first animated group on each
  slide uses `entrance_fade`; later groups cycle through a 16-effect canonical
  PowerPoint entrance pool across the deck. The mode name remains compatible;
  it no longer selects hand-authored compatibility rows.
- `random` — samples from the same canonical PowerPoint entrance pool.
  Resolution is seeded from the effective deck input, so the same input
  produces the same choices; `--conversion-trace` records every resolved effect
  when diagnostics are enabled.

`entrance_appear` is excluded from every variation pool because it has no
visible motion.

Flags:

- `-a/--animation` — compatibility alias, native `entrance_*` / `emphasis_*`
  / `path_*` / `exit_*` effect, `auto`, `mixed`, `random`, or `none`. Default:
  `none` (per-element animation off; pass `auto` to enable automatic entrances).
- `--animation-trigger` — Start mode (matches PowerPoint): `on-click`, `with-previous`, or `after-previous` (default).
- `--animation-duration` — per-element schedule duration in seconds, default
  `0.4`. Scalable native behavior trees preserve their internal timing ratios;
  instantaneous presets retain their authored duration.
- `--animation-stagger` — gap between elements in `after-previous` mode (seconds, default `0.5`). Ignored otherwise.
- `--animation-config` — explicit sidecar path. Narrated export defaults to `<project>/narration_animations.json`; other export defaults to `<project>/animations.json` when present.
- `--no-animations` — ignore animation sidecars and disable both object animations and page-transition motion. Narration audio and recorded slide-advance timing remain active.

> Note: `--recorded-narration` rejects `on-click`; use its default `narration_animations.json`, pass `--animation-config animations.json` for the canonical presentation animation, or pass `--no-animations`.

---

## 5. Anchor Logic — Top-Level `<g id="...">`

Per-element animations are anchored on **top-level `<g id="...">` content groups** in the SVG (e.g. `<g id="cover-title">`, `<g id="card-1">`). IDs must be unique within the page. One group produces one animation-pane row; whether that row needs a click depends on the selected Start mode. Nested implementation groups may remain anonymous because the sidecar does not target them.

**Hard rule — existing groups are not custom-animation intent**: the
pre-existing SVG hierarchy is implementation evidence, not an authoritative
reveal plan. During the custom-animation stage, derive one group per logical
page unit from claims, comparisons, sequence, causality, and narration beats;
split coarse wrappers and merge fragmented atoms when needed, then use
`list-groups` only after that rewrite. This is also the granularity PowerPoint
uses for group-select / group-move. Do not split or merge units to hit a target
count.

**Chrome groups skip the cascade automatically.** Explicit SVG role and placeholder semantics are authoritative. A group with `data-pptx-layer` or an explicit static role/placeholder marker can never animate. For marker-free legacy SVGs only, top-level groups whose id tokens look like page chrome (background, header/footer, decorations, watermark, page number, nav, logo, dividing rule) are excluded and appear with the slide. An explicit `animations.json` group entry may override this id-name heuristic, but never an explicit structural marker. Examples that auto-skip by legacy id: `<g id="background">`, `<g id="bg-texture">`, `<g id="cover-footer">`, `<g id="p03-header">`, `<g id="bottom-decor">`, `<g id="watermark">`, `<g id="nav">`, `<g id="logo-area">`, `<g id="column-rule">`. Examples that still animate: `<g id="card-1">`, `<g id="cover-title">`, `<g id="step-discover">`, `<g id="timeline-track">`. Do not strip the `<g>` wrapper to avoid animation — keep it for PowerPoint group selection and use `effect: none` when the content should remain static.

**Fallback for flat SVGs** (no top-level `<g>` wrappers, only raw `<rect>` / `<text>` / `<path>` at the root):

- ≤ 8 visible top-level primitives → each becomes one anchor (capped to avoid 70+ atom cascades on dense pages).
- > 8 → animation is skipped on that slide. The slide still renders, just without object animation.

Executors should wrap logical sections in `<g id>` regardless of whether you plan to animate. [`shared-standards-core.md`](./shared-standards-core.md) requires it.

---

## 6. Validation and Read-Back

Animation configuration is strict. Export fails on an unknown effect, mode, or trigger; a boolean or non-finite duration/delay/stagger; a non-positive duration; a negative delay/stagger; a non-positive or non-integer order; a missing slide/group reference; or any attempt to animate a structural layer. These errors never downgrade to another effect or silently omit a requested target.

Generated export reads each slide's timing tree back and checks row count/order,
trigger, shape target, preset class, resolved effect tuple, native behavior
signature, duration, and timeline offset. Package validation then checks root
timing placement, unique and valid `p:cTn` ids, and every `p:spTgt` reference.
The writer does not emit `p:bldP` for groups or pictures. Direct-PPTX preserve
mode tolerates unchanged legacy group/picture `p:bldP` rows from earlier PPT
Master exports; new generated packages remain strict.

Narration injection merges audio timing into an existing direct `p:sld/p:timing`
DOM and preserves object-animation rows. A source timing tree nested in
`mc:AlternateContent` or another non-root container fails safely instead of
being rewritten or duplicated. Direct-PPTX routes fingerprint source
object-animation timing before and after their allowed edits, then run
structural package validation; they do not author or normalize animation
effects.

---

## 7. Video Adaptation Contract

Video renderers consume the resolved conversion trace through
`video_motion_plan.py`, never a raw sidecar or delay-only inference. The plan
locks identity, order, effect, direction, and timing; video may refine only its
declared renderer parameters. Unsupported families fail visibly. See
[`video-motion-plan.md`](../scripts/docs/video-motion-plan.md).

---

## 8. Limitations

- Generated animation belongs to the native PPTX built from `svg_output/`.
  `svg_final/` is a static preview, and inserting it as one SVG picture does
  not create object anchors.
- PowerPoint OOXML is the compatibility target; other presentation apps may
  reinterpret individual native behavior trees.
- Direct-PPTX routes preserve unknown transition `AlternateContent`; timing
  edits keep Choice and Fallback advance attributes synchronized.

---

## 9. Implementation References

See [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md),
[`pptx-transitions.md`](../scripts/docs/pptx-transitions.md),
[`pptx-animations.md`](../scripts/docs/pptx-animations.md), and
[`video-motion-plan.md`](../scripts/docs/video-motion-plan.md).
