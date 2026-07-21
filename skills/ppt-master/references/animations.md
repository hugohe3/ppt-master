# Page Transitions & Per-Element Animations

Execution contract for generated-PPTX **page transitions** and **per-element
entrance animations**. This file owns defaults, sidecar semantics, anchor
selection, validation, and package read-back.

## 1. Defaults

| Layer | Default | Why |
|---|---|---|
| Page transition | CLI: `fade`, 0.4s | Calm baseline that suits most decks; the public Python builder retains its legacy 0.5s default |
| Per-element animation | **`none` (off)** | A page appears as a whole. Auto-firing element builds are an unsolicited "AI deck" tell, so element entrance is opt-in. Turn it on with `-a auto` (or another effect): effects map from group id (chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade); image-like ids (`hero` / `figure-` / `image` / `img-` / `kpi`) cycle a richer visual pool (zoom / dissolve / circle / box / diamond / wheel) so multiple images vary across the deck; unmatched ids cycle a small fade/wipe/fly/zoom pool |

To regenerate a deck with different settings, rerun `svg_to_pptx.py` against the same `svg_output/` — no need to rerun the LLM. `-s final` is reserved for diagnostic comparison and is not a supported release source. To turn per-element animation on for the whole deck, pass `-a auto`.

---

## 2. Custom Object-Level Animation

Per-element animation is off by default. To enable it deck-wide, pass `-a auto` at export (no config needed). When a deck instead needs specific object timing — for example title first, chart second, annotation last — use the optional `animations.json` sidecar. The SVG remains static visual source; the sidecar only controls PPTX export behavior.

Run the [`customize-animations`](../workflows/stages/customize-animations.md) post-processing stage when the user asks to tune animation order, effects, timing, or object-level reveals.

```bash
# Build an editable scaffold from real top-level <g id> anchors
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
        "title": { "effect": "fade", "order": 1 },
        "chart": { "effect": "wipe", "order": 2, "duration": 0.6 },
        "insight": { "effect": "fly", "order": 3, "delay": 0.2 }
      }
    }
  }
}
```

Rules:

- `slides` keys match SVG stems (`03_market.svg` → `03_market`).
- `groups` keys match top-level `<g id="...">` anchors.
- `effect: none` removes that group from the entrance sequence.
- `order` changes animation order only; it does not change slide layering.
- `delay` is seconds before that group starts in `after-previous` mode.
- `duration` overrides the per-group schedule duration. `appear` remains a 1ms visibility flip; its configured duration spaces the next `after-previous` row.
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

Available effects: `fade`, `push`, `wipe`, `split`, `strips`, `cover`, `random`.

Flags:

- `-t/--transition` — effect name, or `none` for no visual transition. Default: `fade`. `none` does not remove an explicitly configured automatic advance.
- `--transition-duration` — seconds, default `0.4`.
- `--auto-advance` — seconds; click remains enabled, so the slide advances on click or when the timer expires. Omit for presenter-controlled advance.

**Hard rule — no silent downgrade**: an unknown transition effect or invalid/non-finite duration fails export. It is never replaced by `fade`. Recorded narration keeps the resolved visual transition; `-t none --recorded-narration ...` writes narration-driven advance timing without restoring a visual effect.

---

## 4. Per-Element Animations

Off by default — enable deck-wide with `-a auto` (or another effect). Once enabled, three Start modes are available — these mirror PowerPoint's animation-pane "Start" dropdown:

- **`on-click`** — entering a slide → first click reveals the first semantic group; each subsequent click reveals the next group in z-order. Suits live presentations where the speaker paces reveals. Forbidden with `--recorded-narration` because video-ready exports need click-free playback.
- **`with-previous`** — all groups start together on slide entry, playing their entrance animation in parallel. Stagger ignored.
- **`after-previous`** (default) — first group fires on slide entry, subsequent groups cascade after the previous one finishes, with `--animation-stagger` extra spacing. Suits kiosk playback, recorded walkthroughs, or anyone who wants visual flow without clicking.

```bash
# Default behavior (no flags): page transitions only, no per-element builds
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>

# Enable per-element animation deck-wide (auto effect + after-previous cascade)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto

# Enable with a single effect (cascades via the after-previous trigger)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# Enable and switch to on-click for live presentations (presenter controls pacing)
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click

# Custom pacing
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed \
        --animation-stagger 0.7 --animation-duration 0.5

# All groups animate in unison on slide entry
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous
```

22 single effects: `appear`, `fade`, `fly`, `cut`, `zoom`, `wipe`, `split`, `blinds`, `checkerboard`, `dissolve`, `random_bars`, `peek`, `wheel`, `box`, `circle`, `diamond`, `plus`, `strips`, `wedge`, `stretch`, `expand`, `swivel`. Plus three auto-vary modes:

These names preserve the established filter / `presetID` / `presetSubtype` tuples documented in [`pptx-animations.md`](../scripts/docs/pptx-animations.md#3-compatibility-contract). `cut` is a legacy public key; compatibility promises its existing tuple, not a semantic interpretation inferred from an external preset-id table.

- `auto` (recommended when enabling) — map effect from the group's SVG id. Information-dense elements get a single stable effect: `chart` / `table` / `legend` / `timeline` / `track` → `wipe`; `card-*` / `pillar-*` / `item-*` / `step-*` / `stage-*` / `tier-*` / `principle-*` → `fly`; `title` / `chapter-*` / `section-*` / `cover-*` / `tagline` / `subtitle` → `fade`; `takeaway` / `callout` / `quote` / `source` / `conclusion` / `note` → `fade`. Image-like ids `hero` / `figure-*` / `image` / `img-*` / `kpi` instead cycle a richer visual pool (`zoom` / `dissolve` / `circle` / `box` / `diamond` / `wheel`) so multiple images vary across the deck. Unmatched ids cycle through `fade` / `wipe` / `fly` / `zoom`.
- `mixed` (legacy) — deterministic. The first animated group on each slide uses `fade`; later groups cycle through a 16-effect pool (`blinds` / `checkerboard` / `dissolve` / `fly` / `cut` / `random_bars` / `box` / `split` / `strips` / `wedge` / `wheel` / `wipe` / `expand` / `fade` / `swivel` / `zoom`) across the deck. Kept for backward compatibility.
- `random` — samples from the legacy 16-effect pool. Resolution is seeded from the effective deck input, so the same input produces the same choices; `--conversion-trace` records every resolved effect when diagnostics are enabled.

`appear` is excluded from every variation pool because it has no visible motion.

Flags:

- `-a/--animation` — effect name, `auto`, `mixed`, `random`, or `none`. Default: `none` (per-element animation off; pass `auto` to enable).
- `--animation-trigger` — Start mode (matches PowerPoint): `on-click`, `with-previous`, or `after-previous` (default).
- `--animation-duration` — per-element entrance seconds, default `0.4`.
- `--animation-stagger` — gap between elements in `after-previous` mode (seconds, default `0.5`). Ignored otherwise.
- `--animation-config` — sidecar path. Default: `<project>/animations.json` when present.

> Note: `--recorded-narration` rejects `on-click`; use `after-previous` or `with-previous` for video-ready narrated decks.

---

## 5. Anchor Logic — Top-Level `<g id="...">`

Per-element animations are anchored on **top-level `<g id="...">` content groups** in the SVG (e.g. `<g id="cover-title">`, `<g id="card-1">`). IDs must be unique within the page. One group produces one animation-pane entrance row; whether that row needs a click depends on the selected Start mode. Nested implementation groups may remain anonymous because the sidecar does not target them.

Use one content group per logical page unit. This is also the granularity PowerPoint uses for group-select / group-move, so semantic grouping improves editing ergonomics regardless of animation; do not split or merge units to hit a target count.

**Chrome groups skip the cascade automatically.** Explicit SVG role and placeholder semantics are authoritative. A group with `data-pptx-layer` or an explicit static role/placeholder marker can never animate. For marker-free legacy SVGs only, top-level groups whose id tokens look like page chrome (background, header/footer, decorations, watermark, page number, nav, logo, dividing rule) are excluded and appear with the slide. An explicit `animations.json` group entry may override this id-name heuristic, but never an explicit structural marker. Examples that auto-skip by legacy id: `<g id="background">`, `<g id="bg-texture">`, `<g id="cover-footer">`, `<g id="p03-header">`, `<g id="bottom-decor">`, `<g id="watermark">`, `<g id="nav">`, `<g id="logo-area">`, `<g id="column-rule">`. Examples that still animate: `<g id="card-1">`, `<g id="cover-title">`, `<g id="step-discover">`, `<g id="timeline-track">`. Do not strip the `<g>` wrapper to avoid animation — keep it for PowerPoint group selection and use `effect: none` when the content should remain static.

**Fallback for flat SVGs** (no top-level `<g>` wrappers, only raw `<rect>` / `<text>` / `<path>` at the root):

- ≤ 8 visible top-level primitives → each becomes one anchor (capped to avoid 70+ atom cascades on dense pages).
- > 8 → animation is skipped on that slide. The slide still renders, just without entrance animation.

Executors should wrap logical sections in `<g id>` regardless of whether you plan to animate. [`shared-standards-core.md`](./shared-standards-core.md) requires it.

---

## 6. Validation and Read-Back

Animation configuration is strict. Export fails on an unknown effect, mode, or trigger; a boolean or non-finite duration/delay/stagger; a non-positive duration; a negative delay/stagger; a non-positive or non-integer order; a missing slide/group reference; or any attempt to animate a structural layer. These errors never downgrade to another effect or silently omit a requested target.

Generated export reads each slide's timing tree back and checks row count/order, trigger, shape target, resolved effect tuple, duration, and timeline offset. Package validation then checks root timing placement, unique and valid `p:cTn` ids, and every `p:spTgt` reference. The writer does not emit `p:bldP` for groups or pictures. Direct-PPTX preserve mode tolerates unchanged legacy group/picture `p:bldP` rows from earlier PPT Master exports; new generated packages remain strict.

Narration injection merges audio timing into an existing direct `p:sld/p:timing` DOM and preserves entrance rows. A source timing tree nested in `mc:AlternateContent` or another non-root container fails safely instead of being rewritten or duplicated. Direct-PPTX routes fingerprint source object-animation timing before and after their allowed edits, then run structural package validation; they do not author or normalize animation effects.

---

## 7. Limitations

- **Native DrawingML output only.** Page transitions and per-element animations are authored on the PPTX produced by the project converter from `svg_output/`. `svg_final/` remains a static SVG visual preview, not an animated or alternate PPTX route.
- **PowerPoint OOXML scope.** Effects preserve their established filter / `presetID` / `presetSubtype` tuples and are validated against the serialized PowerPoint package. Rendering in Keynote, LibreOffice, WPS, or other applications is outside the unconditional compatibility guarantee.
- **Manual SVG shape conversion is unsupported.** Inserting an `svg_final/` page as an SVG picture does not establish element animation anchors; use the native PPTX when editable animated shapes are required.
- **Source extension preservation.** Direct-PPTX routes preserve unknown transition `AlternateContent` when configured to keep the source. When advance timing changes, Choice and Fallback receive the same `advClick` / `advTm` values.

---

## 8. Quick Reference

| Goal | Command |
|---|---|
| Remove visual transition | `-t none` |
| Change transition effect | `-t push` (or any from the list above) |
| Slower transition | `--transition-duration 0.8` |
| Auto-play | `--auto-advance 5` |
| Disable element animation | `-a none` |
| Switch to on-click trigger | `-a auto --animation-trigger on-click` |
| Use a single effect instead of auto | `--animation fade` |
| All groups animate together | `-a auto --animation-trigger with-previous` |
| Slower per-element reveal | `-a auto --animation-duration 0.5` |
| Wider gap in after-previous | `-a auto --animation-stagger 0.7` |

See also:

- [`scripts/docs/svg-pipeline.md`](../scripts/docs/svg-pipeline.md) for the full `svg_to_pptx.py` reference.
- [`pptx-transitions.md`](../scripts/docs/pptx-transitions.md) for the shared OOXML writer, MCE preservation, and read-back contract.
- [`pptx-animations.md`](../scripts/docs/pptx-animations.md) for the exact effect tuples, timing-tree rules, and animation package validator.
