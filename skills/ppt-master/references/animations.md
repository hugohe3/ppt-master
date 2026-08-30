# Page Transitions & Per-Element Animations

Execution contract for generated-PPTX **page transitions** and **per-element object animations**, including deterministic Morph pairing: defaults, sidecar semantics, anchor selection, validation, and package read-back.

## Capability Menu — Open Here

Motion is several separate capabilities, not one dial; two of them are decided while pages are still being authored, so read this before the page plan is frozen.

| What the deck needs | Reach for | Decided at |
|---|---|---|
| A generic deck-wide entrance build | `-a auto`; with the default `after-previous` Start, groups use fixed `--animation-stagger` timing, not narration cues | Post-processing; §2, §4 |
| Explicit object lifecycle choreography | An `animations.json` sidecar for selected enter/emphasize/move/exit/static duties, order, Start, timing | Post-processing; §2, §4, [`customize-animations`](../workflows/stages/customize-animations.md) |
| Object reveals synchronized to recorded narration | Narration-cue sync derives `narration_animations.json` from `animations.json`, page-local SRT, and `narration_timing.json`; `-a auto` alone does not | Audio stage; [`generate-audio`](../workflows/stages/generate-audio.md) |
| A continuous action — slide-in, flip, camera push-in, progressive reveal, camera pan | **Morph: author the action as two static pages**, then select Morph and add explicit pairs when identity must be deterministic; there is no keyframe timeline anywhere — the difference between two editable slides *is* the animation | **Page authoring (Step 6), then motion post-processing** — §2.1, §3.1 |
| A static full-bleed page that should stop looking frozen | Slow `path_*` motion on a visually subordinate image or atmospheric layer | Post-processing; §4.1 |
| Carousel, counting numerals, parallax depth, click-to-reveal flip card | Four recipes assembled from the mechanisms above; carousel and odometer need paired pages | §4.2 |
| Kiosk or unattended playback | `--auto-advance <seconds>`, optionally with `-t none` | Export; §3 |
| A transition or object animation needs an audible cue | Optional `transition.sound` or object `sound`, selected only after the visual solution is complete and synced from the global library; a narrated MP4 uses either the verified native-export mix or explicit slideshow capture, never both | Post-motion; §2.2 |
| Nothing should move | `-t none` and per-element `none` | Export; §1 |

**Hard rule — Morph geometry is an authoring decision; pairing is a later execution decision**: export cannot invent endpoint states. Author both consecutive pages while `svg_output/` is being built; for deterministic identity expose each endpoint as a compatible direct-root group and declare the pair in `animations.json` (§2.1) — ids and geometry may differ. `-t morph` without pairs leaves matching to PowerPoint's heuristic.

**Reference — not a constraint**: per-element animation stays off by default; auto-firing builds on every page are an unsolicited "AI deck" tell, and each capability earns its place per page.

---

## 1. Defaults

| Layer | Default | Why |
|---|---|---|
| Page transition | CLI `fade`, 0.4s (the public Python builder keeps its legacy 0.5s) | Calm baseline |
| Per-element animation | **`none` (off)** | A page appears as a whole; opt in with `-a auto` or one explicit `entrance_*` / `emphasis_*` / `path_*` / `exit_*` key |
| Sound effects | **`none` (off)** | No global sound is copied and no `<project>/sounds/` exists until a resolved cue selects one |

To regenerate with different settings, rerun the final checker when its report is absent or stale, then rerun `svg_to_pptx.py` on the same `svg_output/`; the authoring LLM reruns only for SVG repair. `-s final` is diagnostic only.

---

## 2. Custom Object-Level Animation

`-a auto` enables generic entrance reveals deck-wide with no config. A specific lifecycle — enter, move, emphasize, exit — uses the optional `animations.json` sidecar: the SVG stays the visual source, the custom stage may regroup, rename, and re-bound anchors without changing visible output, and the sidecar controls PPTX behavior. Run [`customize-animations`](../workflows/stages/customize-animations.md) when `animations.json` exists, when the user asks to tune order/effects/timing/object reveals, or when the effective Custom Animations outcome in `design_spec.md §I` is enabled; a §IX `Motion suggestion` informs an active pass but never triggers it.

**Hard rule — semantic anchors before object-targeted entries**: derive motion units and duties from page meaning and narration, regroup coarse or fragmented Slide-local content without changing appearance, and target only post-regroup top-level ids.

```bash
python3 skills/ppt-master/scripts/animation_config.py list-groups <project>   # real anchors after regrouping
python3 skills/ppt-master/scripts/animation_config.py scaffold <project>      # neutral editable scaffold (effect: none, {} placeholders)
python3 skills/ppt-master/scripts/animation_config.py validate <project>      # before export
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>                    # reads <project>/animations.json automatically
```

Sparse sidecar (unlisted slides inherit resolved defaults):

```json
{
  "version": 1,
  "slides": {
    "03_threshold": {
      "groups": {
        "risk-marker": {
          "effects": [
            { "effect": "entrance_fade", "order": 1, "duration": 0.25 },
            { "effect": "path_right", "effect_options": { "relative": true }, "order": 2, "duration": 0.7 },
            { "effect": "emphasis_teeter", "order": 3, "duration": 0.45 },
            { "effect": "exit_fade", "order": 4, "duration": 0.3 }
          ]
        }
      }
    }
  }
}
```

**Contract**:

- `slides` keys are SVG stems; `groups` keys are top-level `<g id>` anchors. A populated group is either the legacy single-effect object or `{ "effects": [row, …] }` (non-empty, each row naming `effect`, mutually exclusive with legacy fields); `{}` is a neutral placeholder; legacy `effect: none` removes the group from the sequence and overrides inherited generic animation.
- `effects[]` lets one shape carry several Animation Pane rows; `order` sorts rows across the slide (ties keep SVG group order, then array order), `trigger_shape` rows sort within their own interactive sequence, and ordering never changes layering.
- `delay` adds seconds to the resolved Start; `trigger` per row otherwise inherits the slide Start mode; `trigger_shape` references another unique triggerable top-level group (PowerPoint **Trigger → On Click of**), makes only that row interactive, uses `delay` as `TriggerDelayTime`, and implies `on-click`.
- `duration` overrides the row schedule (`entrance_appear` stays a 1 ms flip and instantaneous native emphasis keeps its authored duration, but the configured value still spaces the next `after-previous` row).
- `effect_options` requires an explicit canonical `effect` and accepts only what PowerPoint exposes: `direction` (directional entrance/exit effects), `amount` (wheel spokes `1`/`2`/`3`/`4`/`8`, spin degrees, transparency ratio), `color` (`#RRGGBB` or `theme:<scheme-color>`), `font_name` (required for `emphasis_change_font`; one installed face), `size` (grow/shrink), `relative` (motion paths). `python3 skills/ppt-master/scripts/pptx_animations.py --describe <effect>` prints each effect's exact contract.
- Any block or row may set `repeat_count` or `repeat_duration` (exclusive), `auto_reverse`, `rewind`, `accelerate`, `decelerate` (ratios `0..1`; `bounce_end` needs an interpolated behavior and excludes `decelerate`), `restart` (`always` / `when-not-active` / `never`), `after_effect` (`none` / `dim` with `color` / `hide` / `hide-on-next-click`), and `sound` (project-relative or absolute `.m4a` / `.mp3` / `.wav`; new output uses a project-relative path synced under §2.2, never `templates/sounds/`). `Speed` and smooth start/end derive from `duration` and `accelerate`/`decelerate`.
- This is the complete surface for the top-level-group model: no paragraph/text-range builds (grouped SVG is not emitted as paragraph builds), no media commands (audio/video workflows own them).
- `--animation none` overrides the sidecar and disables all per-element animation; a sidecar group may override the legacy chrome-name heuristic but never `data-pptx-layer` or an explicit static role/placeholder; unknown effects, modes, triggers, or invalid numeric/order fields fail validation with no fallback.

**Inheritance**: sidecar and `defaults` are optional; unlisted slides and omitted fields inherit `defaults.transition` / `defaults.animation`, then CLI resolution. Explicit CLI flags override the corresponding sidecar default/slide fields; explicit group overrides remain unless `-a none`. Groups inherit the resolved slide duration, Start, timing modifiers, after-effect, and sound; `effect_options` stays coupled to an explicit effect; `trigger_shape` is never inherited; omitted `order`/`delay` use exporter defaults.

### 2.1 Deterministic Morph Object Pairing

When one semantic object continues across adjacent slides, the destination slide declares forced-Morph pairs — separate from `groups` (Morph owns cross-slide identity; `groups` owns Animation Pane rows) — following Microsoft's [forced object-matching convention](https://support.microsoft.com/en-us/powerpoint/morph-transition-tips-and-tricks):

```json
{
  "version": 1,
  "slides": {
    "02_detail": {
      "transition": { "effect": "morph", "effect_options": { "morph_by": "object" }, "duration": 0.8 },
      "morph": { "from": "01_overview", "pairs": { "hero-image": { "from": "hero-overview", "to": "hero-detail" } } }
    }
  }
}
```

`morph` belongs to the destination and `morph.from` is the immediately preceding stem in export order; `scaffold` never guesses identity — add pairs from the motion plan after inspecting final direct-root ids. Each pair key is a stable identity whose `from`/`to` are unique direct-root ids on the two slides, written without `!!` (export writes the Selection Pane name `!!<key>` on both). A destination with pairs sets `effect: morph` explicitly (`morph_by` omitted or `object`; `word`/`character` rejected; a CLI override that changes the effect fails). A middle slide may continue an object into another Morph under the same key; one key never names two objects on a slide, one object never carries two keys, and every `!!` key shared by adjacent Morph pages must be declared. Pairing coexists with in-slide animation and survives `-a none`; `--no-animations` disables everything. The exporter resolves both ids to final Slide-local shapes, writes names after Master/Layout processing, then reopens the package to verify adjacency, Morph by object, one name per slide, and matching object types — missing, structural, moved, ambiguous, or mismatched targets fail rather than falling back.

### 2.2 On-Demand Sound Selection

**Hard rule — select after motion, materialize after selection**: sound is not a Strategist resource and never appears in `design_spec.md`, `spec_lock.md`, or pre-SVG preparation. After the roster and motion solution are final, and only when a specific cue is selected: read the complete [`sound-vocabulary.md`](../templates/sounds/sound-vocabulary.md), choose one exact id for the auditory job, sync only that id, and reference the project-local `sounds/<namespace>/<file>.wav`; user audio already in the project is referenced by its project-relative path (`.m4a` / `.mp3` / `.wav` for objects, `.wav` for transitions); with no concrete cue job omit `sound` and create no `sounds/`.

```bash
python3 skills/ppt-master/scripts/sound_sync.py list --query <term>                       # optional exact filtering after the vocabulary is in context
python3 skills/ppt-master/scripts/sound_sync.py <project_path> <namespace>/<sound_id> [...]  # materialize only the chosen ids
```

`sound_sync.py` is the only library materialization path; the exporter never reads `templates/sounds/`, and sidecars store paths, not ids. **Default — silence**: never add sound to demonstrate capability or for coverage; a sound supports a named transition, reveal, confirmation, warning, or gesture after that visual behavior is selected. **Hard rule — PPTX and MP4 are separate deliveries**: sound fields and read-back prove the PPTX carries the cue, not that PowerPoint's encoder put it in the MP4; a narrated MP4 with cues follows `generate-audio` — mix from the final narrated trace plus final PPTX, or capture the live Slide Show with system audio, never both — and keeps gain/limiter settings out of `animations.json`.

---

## 3. Page Transitions

**Reference — not a constraint**: choose from the relationship between adjacent pages, not gallery coverage — relate (same object or space, directional advance, new section, deliberate break), diagnose the job (continuity, cut, direction, object/state continuity, spatial movement, thematic beat), select the smallest family, coordinate direction, duration, and recurrence with reading order and narration, and keep `fade` or `none` when nothing adds meaning.

| Page relationship | Candidate family |
|---|---|
| Ordinary continuation within one section | `fade` |
| Immediate change with no continuity to preserve | `none` or `cut` |
| Directional steps, timeline, or layer progression | `push` / `wipe`; `cover` / `uncover` for a visible overlay relationship |
| The same object or scene changes across adjacent pages | `morph`; §2.1 pairs for deterministic identity |
| Section opening, key reveal, or marked state boundary | Selective `split` / `reveal` / `shape` / `flash` / `random_bars` |
| A repeated collection advances through one spatial frame | `pan` / `conveyor` / `ferris_wheel`; the §4.2 Morph carousel for deterministic cards |
| The viewpoint travels around or through a continuous space | `rotate` / `window` / `orbit` / `fly_through` |
| A stage, paper, or physical-page metaphor | Selective `fall_over` / `drape` / `curtains` / `wind` / `prestige` / `peel_off` / `page_curl` / `airplane` / `origami` / `doors` |
| Breakage, collapse, or dispersal | Selective `fracture` / `crush` / `dissolve` / `vortex` / `shred` |
| A geometric, timed, or textured reveal | Selective `checkerboard` / `blinds` / `clock` / `ripple` / `honeycomb` / `glitter` / `comb` |
| A card, panel, gallery, or viewpoint visibly turns | Selective `switch` / `flip` / `gallery` / `cube` / `box` / `zoom` |
| Unpredictability itself is requested | `random`; never for variety |

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push --transition-duration 0.6
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5            # kiosk playback
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none --auto-advance 5
```

The registry covers PowerPoint's complete Subtle, Exciting, and Dynamic Content gallery — 48 canonical keys (`pptx_animations.py --list`); eight old low-level names desugar to a native key plus options (`diamond` → `shape` + `shape: diamond`, `wedge` → `clock` + `style: wedge`) and are never selected for new output. `transition.effect_options` exposes the real Effect Options (Push/Wipe direction, Morph by object/word/character, Reveal through black, Shape geometry, Page Curl direction/pages, Glitter pattern, Fly Through bounce; `pptx_animations.py --describe-transition <effect>`); unknown options fail. Effects needing newer namespaces carry a `mc:Choice` plus a `fade` fallback that validation never accepts as a substitute. `transition.sound` (a sidecar field, `.wav`, synced under §2.2) may accompany `effect: none`; a slide-level `transition.sound: null` clears an inherited default transition sound. Flags: `-t/--transition` (native key, compatibility input, or `none`; default `fade`; `none` keeps an explicit auto-advance), `--transition-duration` (default `0.4`), `--auto-advance` (seconds; click still advances). **Hard rule — no silent downgrade**: an unknown effect, unsupported option, or invalid duration fails export and is never replaced by `fade`; `-t none --recorded-narration …` writes narration-driven advance without restoring a visual effect.

### 3.1 Morph — author an action as the difference between two pages

Morph tweens matched objects across consecutive slides, so any continuous action is two static pages plus Morph: duplicate the page, change one property, PowerPoint interpolates. Off-canvas → on-canvas reads as slide-in, drawer, card extending; rotation as flip, turn, hinge; a scaled image container as camera push-in; a dropping scrim or growing cut as progressive reveal; the same wide image at two `x` offsets as camera pan (`#C2-01`). Chain three or more pages for extend–hold–retract.

**Hard rule — matching needs compatible identity, not identical geometry**: prefer §2.1 pairs; ids and visible state may differ, but both endpoints must resolve to one compatible top-level PowerPoint object kind — a shape and a picture cross-fade instead of tweening. Automatic Morph is heuristic. **Give text somewhere to come from**: text present only on the second page can only fade in — place the next page's copy just below the canvas and the previous page's just above, so blocks slide through the frame; a wholly off-canvas endpoint is one direct-root `<g id>` with valid `data-pptx-bounds` and `data-pptx-morph-staging="true"`, explicitly paired when Morph stays enabled; the marker never excuses a partially clipped group. Declare identity through the destination's `morph` block, never `data-pptx-shape-name` (importer metadata, [`svg-effects.md`](./svg-effects.md) §6.6). **Not supported**: Slide Zoom / Summary Zoom (build click navigation with `trigger_shape` or hyperlinks) and 3D — perspective, extrusion, and shear fail closed ([`svg-effects.md`](./svg-effects.md) §6.8); build the impression with offset, scale, overlap, and per-facet lightness.

---

## 4. Per-Element Animations

Off by default; enable with `-a auto` (or another effect), select a canonical effect with `--animation entrance_fade`, and choose Start with `--animation-trigger on-click|with-previous|after-previous` — PowerPoint's Start dropdown: `on-click` (each click reveals the next group; only for a controlled semantic reveal; forbidden with `--recorded-narration`), `with-previous` (one coordinated beat; stagger ignored), `after-previous` (default click-free cascade with `--animation-stagger`). **Default — one dominant deck rhythm and normally one mode per slide (may mix for a distinct simultaneous or presenter-controlled beat)**. Row-specific `trigger_shape` is PowerPoint's separate Trigger → On Click of, not a fourth mode.

**Mandatory — lifecycle before effect**: start from `static`, classify `initial → action → end`, then choose the effect; generic staged reveals are `enter`, narrower jobs select their lifecycle.

| Duty | State contract | Use when | Effect family |
|---|---|---|---|
| `static` | present → hold → present | Motion adds no clarity or feeling | No row; legacy `effect: none` only suppresses inheritance |
| `enter` | absent → introduce → present | Information is withheld, ordered, or revealed with narration | `entrance_*`; modes only for generic reveal |
| `emphasize` | present → redirect attention → present/altered | A visible object must regain attention or show a local change; never its first reveal | Explicit `emphasis_*` |
| `move` | A → progress → B | The trajectory carries spatial or causal meaning, or §4.1 ambient motion; Morph for cross-page continuity | Explicit `path_*`, or endpoint pages + Morph |
| `exit` | present → retire → absent | The same slide must remove, replace, or make room; a page change needs no exit | Explicit `exit_*` |

**Default — restrained entrance-led choreography (may override for content, tone, or the request)**: entrances for ordinary builds; emphasis or exit only for a real duty; several `effects[]` rows only for several duties.

The registry has **203 native object presets** — 53 `entrance_*`, 33 `emphasis_*`, 64 `path_*`, 53 `exit_*` (e.g. `entrance_bounce`, `emphasis_spin`, `path_circle`, `exit_faded_zoom`), each carrying the complete PowerPoint behavior tree — plus 29 legacy compatibility inputs that normalize before selection (`fade` → `entrance_fade`, old Fly/Wipe direction names → `entrance_fly` / `entrance_wipe` with the direction in `effect_options`, `cut` → `entrance_appear`, `wheel` → `entrance_wheel` with four spokes) and are never written. `python3 skills/ppt-master/scripts/pptx_animations.py --list` prints the categorized keys; media play/pause/stop belong to the audio/video workflows. Modes handle generic `enter` only: `auto` maps semantic ids to canonical entrances (charts/tables/timelines `entrance_wipe`, cards/steps `entrance_fly`, titles/takeaways `entrance_fade`, image-like ids a richer pool, others fade/wipe/fly/zoom); `mixed` is deterministic (`entrance_fade` first, then a 16-effect canonical pool); `random` samples the same pool, seeded from the effective deck input so results repeat; `entrance_appear` is excluded from every pool; none satisfies an adopted `emphasize`, `move`, or `exit`. Flags: `-a/--animation`, `--animation-trigger`, `--animation-duration`, `--animation-stagger`, `--animation-config <sidecar>`, `--no-animations` (kills page/object motion, keeps narration audio and recorded advance). `--recorded-narration` rejects `on-click` and `trigger_shape`; narration-cue sync uses `narration_animations.json` and blocks on a bare canonical sidecar; narration-independent custom motion passes `--animation-config animations.json` explicitly; with no sidecar pass `--inherit-motion-from <base_postflight_report>`.

### 4.1 Slow ambient motion — the page that breathes

**Reference — not a constraint**: `path_left` / `path_right` on a background image, started `with-previous` and paced far slower than a content reveal, keeps a static page from feeling frozen while staying subordinate; the same applies to any non-information-bearing layer, with duration, distance, and moving-object count from the composition. A full-bleed moving image must cover the canvas at both endpoints. With a fixed foreground (`#M1-07`, also `#M1-10`, `#P1-09`) the scrim and its cuts stay locked while the world moves behind them — windows, not a sliding photo. Coordinated layers are valid for one depth or atmosphere relationship; competing paths or motion that hurts copy or data are not.

### 4.2 Recurring recipes

- **Carousel** (Morph, §2.1/§3.1): hold a fixed row of card frames and rotate the content through them one position per page, pairing each moving content unit; frames stay static and unpaired.
- **Odometer** (Morph or path): a vertical 0–9 strip shown through a window of background-filled rectangles (`#M1-08`); shift the strip so the target digit lands, then morph or `path_up`; a `0.1s` stagger settles columns in sequence, and synchronized motion is also valid when it fits the intended rhythm.
- **Parallax depth** (Morph): move the background a short distance and the foreground a longer one; keep z-order identical on both pages or the tween jumps.
- **Flip-card / click-to-reveal** (`trigger_shape`): a face group and a back group at the same position, face with an exit and back with an entrance whose `trigger_shape` is the face's id — the supported click-driven route (Zoom objects are not, §3.1).

---

## 5. Anchor Logic — Top-Level `<g id="...">`

Animations anchor on unique top-level `<g id>` content groups (`cover-title`, `card-1`); a single-effect group yields one Animation Pane row, `effects[]` several, each inheriting the slide Start unless it declares `trigger`; nested groups stay anonymous and untargeted. **Hard rule — existing groups are not custom-animation intent**: during the custom stage derive one group per logical motion unit from claims, comparisons, sequence, causality, and narration — splitting coarse wrappers and merging fragments without changing appearance, never to hit a count — and run `list-groups` only after that rewrite. **Chrome stays static**: `data-pptx-layer` and explicit static role/placeholder markers are absolute; the legacy chrome-name heuristic (background, header/footer, decor, watermark, page number, nav, logo, rule) applies only to unmarked top-level groups and only it may be overridden by a sidecar entry. Flat SVGs with no top-level `<g>`: ≤8 visible root primitives each become an anchor, more skips animation on that slide. Wrap logical sections in `<g id>` regardless ([`shared-standards-core.md`](./shared-standards-core.md)).

---

## 6. Validation and Read-Back

Export fails on an unknown effect, mode, or trigger; invalid timing or order; a missing slide, group, or `trigger_shape`; a self-trigger; or animating or triggering from a structural layer — never downgrading or omitting a target. It reads each slide's timing tree back (row count and order including repeats on one shape, trigger, trigger shape, target, preset class, effect tuple, behavior signature, duration, offset), validates root timing placement, unique `p:cTn` ids, and every `p:spTgt`, and for deterministic Morph checks the adjacent parts for the `!!` names, one-to-one uniqueness, compatible types, and a real Morph-by-object transition. The writer emits no `p:bldP` for groups or pictures (preserve mode tolerates legacy ones). Narration injection preserves animation and keeps p14 Choice/Fallback in sync; direct-PPTX routes fingerprint source timing before and after their edits and never author effects. `pptx_to_svg.py` projects supported source `p:transition` (registry effect, options, exact duration, auto-advance, WAV sound; sidecar default `none`) and only current generated `p:timing` trees (registry effect, pane order, Start, exact duration, relative delay, unique top-level targets) into `animations.json`; unknown carriers, missing durations, advanced modifiers, sounds, builds, and unmapped targets stay diagnosed/direct-preserve with no inferred value. These checks prove PPTX timing and embedded sound parts, not final-video audio: the native-export branch needs a `video_sound_mix.py` receipt and the capture branch the human acceptance owned by `generate-audio`.

---

## 7. Video Adaptation Contract

Video renderers consume the resolved conversion trace through `video_motion_plan.py` ([`video-motion-plan.md`](../scripts/docs/video-motion-plan.md)), never a raw sidecar or delay inference; the plan locks identity, order, effect, direction, and timing, video refines only its declared renderer parameters, and unsupported families fail visibly. The native-export mix uses the final trace for cue order and offsets, the final PPTX relationships for the embedded bytes, and page-level narration correlation for the clock; the slideshow-capture branch records real-time playback and does not consume the trace.

## 8. Limitations

Generated animation belongs to the native PPTX built from `svg_output/` (`svg_final/` is static and inserting it creates no anchors); PowerPoint OOXML is the compatibility target and other apps may reinterpret behavior trees; PowerPoint's MP4 encoder may drop transition and object sounds, so sound-enabled MP4 uses the post-export mix or the capture contract; direct-PPTX routes preserve unknown transition `AlternateContent` and keep Choice/Fallback advance attributes synchronized.

## 9. Implementation References

[`pptx_transitions.py`](../scripts/pptx_transitions.py), [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md), [`pptx-transitions.md`](../scripts/docs/pptx-transitions.md), [`pptx-animations.md`](../scripts/docs/pptx-animations.md), [`video-motion-plan.md`](../scripts/docs/video-motion-plan.md).
