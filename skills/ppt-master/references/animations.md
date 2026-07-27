# Page Transitions & Per-Element Animations

Execution contract for generated-PPTX **page transitions** and **per-element
object animations**. This file owns defaults, sidecar semantics, anchor
selection, validation, and package read-back.

## Capability Menu — Open Here

Motion here is several separate capabilities, not one dial. Two of them are
decided **upstream, while pages are still being authored** — read this menu
before the page plan is frozen, not only when a deck is already exported.

| What the deck needs | Reach for | Decided at |
|---|---|---|
| Reveal content in step with the narration | Per-element object animation — `-a auto` deck-wide, or an `animations.json` sidecar for specific order, effects, timing, and triggers | Post-processing; §2, §4, [`customize-animations`](../workflows/stages/customize-animations.md) |
| A continuous action — slide-in, flip, camera push-in, progressive reveal, camera pan | **Morph: author the action as two static pages plus `-t morph`.** There is no keyframe timeline anywhere in this pipeline; the difference between two ordinary editable slides *is* the animation | **Page authoring (Step 6)** — §3.1 |
| A static full-bleed page that should stop looking frozen | One slow `path_*` motion on the background group only, `with-previous`, 4–10 s | Post-processing; §4.1, one sidecar entry |
| Carousel, counting numerals, parallax depth, click-to-reveal flip card | Four recurring recipes assembled from the mechanisms above | §4.2 — the carousel and odometer both need paired pages |
| Kiosk or unattended playback | `--auto-advance <seconds>`, optionally with `-t none` | Export; §3 |
| Nothing should move | `-t none`, and leave per-element animation at its default `none` | Export; §1 |

**Hard rule — morph is an authoring decision, not an export flag**: `-t morph`
tweens only objects it can match across consecutive slides, and matching is by
object identity — same image filename, same group `id`, unchanged container
dimensions. A deck that reaches export without paired pages cannot gain morph
motion by adding the flag; it degrades silently to a cross-fade. Resolve this
while `svg_output/` is still being authored, or accept that the sequence stays
static.

**Reference — not a constraint**: per-element animation stays off by default
(§1). Auto-firing element builds on every page are an unsolicited "AI deck"
tell; each capability above earns its place per page, not per deck.

---

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

**Hard rule — semantic anchors before sidecar**: derive reveal units from page
meaning and narration, then regroup coarse/fragmented Slide-local content
without changing its appearance. Only post-regroup top-level ids are valid.

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
        "chart": { "effect": "entrance_wipe", "effect_options": { "direction": "left" }, "order": 2, "duration": 0.6 },
        "details-button": { "effect": "none" },
        "insight": { "effect": "entrance_fly", "effect_options": { "direction": "up_right" }, "order": 3, "delay": 0.2, "trigger_shape": "details-button" }
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
- `trigger_shape` is a group-only reference to another unique, triggerable
  top-level group. It maps to PowerPoint **Trigger → On Click of**, makes only
  that row interactive, and uses `delay` as `TriggerDelayTime`.
- `duration` overrides the per-group schedule duration. `entrance_appear`
  remains a 1ms visibility flip, and instantaneous native emphasis presets
  retain their PowerPoint-authored duration; the configured value still spaces
  the next `after-previous` row.
- `effect_options` requires an explicit canonical `effect` in the same block
  and accepts only parameters PowerPoint exposes for that effect:

  | Option | Applies to |
  |---|---|
  | `direction` | Directional Fly/Crawl/Wipe/Peek/Strips/Split/Stretch/Zoom and related entrance/exit effects |
  | `amount` | Wheel spokes (`1`, `2`, `3`, `4`, `8`), emphasis Spin degrees, or Transparency ratio |
  | `color` | Color-capable emphasis effects; `#RRGGBB` or `theme:<scheme-color>` |
  | `font_name`, `size` | Change Font and Grow/Shrink |
  | `relative` | Motion paths (`true` = shape-relative, `false` = fixed slide path) |
- Any animation/group block may set `repeat_count` or `repeat_duration`
  (mutually exclusive), `auto_reverse`, `rewind`, `accelerate`, `decelerate`,
  `bounce_end`, `restart`, `after_effect`, and `sound`. Ratios are `0..1`;
  `bounce_end` requires an interpolated behavior and cannot combine with
  `decelerate`; `restart` is `always`, `when-not-active`, or `never`;
  `after_effect` is `none`, `dim` (with `color`), `hide`, or
  `hide-on-next-click`; `sound` is a project-relative or absolute `.m4a`,
  `.mp3`, or `.wav` path.
- `Speed` and smooth start/end are not duplicate sidecar fields: they are
  derived from `duration` and `accelerate`/`decelerate`.
- This is the complete parameter surface for the generated top-level-group
  target model. PowerPoint paragraph/text-range build fields are intentionally
  absent because grouped SVG content is not emitted as paragraph builds; media
  play/pause/stop commands remain in the audio/video workflows.
- Run `python3 skills/ppt-master/scripts/pptx_animations.py --describe
  <canonical_effect>` for that effect's exact option values and full parameter
  contract.
- `--animation none` overrides the sidecar and disables all per-element animation.
- An explicit sidecar group may override the legacy chrome-name heuristic, but it cannot override `data-pptx-layer` or an explicit static role/placeholder marker.
- Unknown effects, modes, or triggers and invalid numeric/order fields fail validation; no fallback effect is substituted.

**Inheritance**: the sidecar is optional. Sparse legacy slides inherit
`defaults.transition` / `defaults.animation`, then CLI resolution; explicit CLI
flags win. Groups inherit the resolved slide duration, timing modifiers,
after-effect, and sound. `effect_options` remains coupled to an explicit effect;
`trigger_shape` is never inherited; omitted `order`/`delay` use exporter
defaults. New authoring writes complete slide blocks.

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

The native registry covers PowerPoint's complete Subtle, Exciting, and Dynamic
Content gallery: 48 canonical keys. New selection, sidecars, plans, conversion
traces, and writers use only those keys. Run `pptx_animations.py --list` for
the categorized identifiers.

Eight old low-level names remain accepted only as compatibility inputs. They
desugar to a native key plus native `effect_options`: for example, `diamond`
becomes `shape` with `shape: diamond`, and `wedge` becomes `clock` with
`style: wedge`. They are never selected for new output.

Effects expose their real PowerPoint Effect Options through
`transition.effect_options`. Common examples include Push/Wipe direction,
Morph by object/word/character, Reveal through black, Shape geometry, Page
Curl direction/pages, Glitter pattern/direction, and Fly Through bounce. Run
`pptx_animations.py --describe-transition <effect>` for the exact
effect-specific contract; unknown or inapplicable options fail validation.
`none` removes the visual effect. Effects that require newer Office namespaces
carry a real PowerPoint effect in `mc:Choice` and a `fade` fallback for older
consumers; validation requires the requested primary effect and never accepts
the fallback as a silent substitute.

Flags:

- `-t/--transition` — native effect name, compatibility input, or `none` for no visual transition. Default: `fade`. `none` does not remove an explicitly configured automatic advance.
- `--transition-duration` — seconds, default `0.4`.
- `--auto-advance` — seconds; click remains enabled, so the slide advances on click or when the timer expires. Omit for presenter-controlled advance.

**Hard rule — no silent downgrade**: an unknown transition effect, unsupported Effect Option, or invalid/non-finite duration fails export. It is never replaced by `fade`. Recorded narration keeps the resolved visual transition; `-t none --recorded-narration ...` writes narration-driven advance timing without restoring a visual effect.

### 3.1 Morph — author an action as the difference between two pages

Morph tweens objects it can match across consecutive slides. That makes it a general mechanism, not just a transition: **any continuous action can be authored as two static pages plus `-t morph`**, with no keyframe timeline anywhere. Duplicate the page, change one property on one object, and PowerPoint interpolates the rest.

| Change between the two pages | Reads as |
|---|---|
| Object sits off-canvas, then on-canvas | Slide-in, drawer pull, card extending |
| Object rotates | Flip, turn, hinge |
| Image container scales up | Camera push-in |
| Scrim opacity drops, or a cut contour grows | Progressive reveal |
| Same wide image at two `x` offsets | Camera pan (see image-layout-patterns `#87`) |

Chain three or more pages to build a sequence — extend, hold, retract — where each page is still an ordinary editable slide.

**Hard rule — matching is by object identity**: keep the same image filename, the same group `id`, and container dimensions that do not change between the pages. Rename the file or resize the frame and morph silently degrades to a cross-fade with none of the motion. This is the most common reason a morph sequence "does nothing".

**Give text somewhere to come from.** Morph tweens objects present on both pages; text that only exists on the second page can only fade in. The standard fix, used in essentially every morph-driven deck: place the *next* page's copy on the current page just outside the canvas (below), and the *previous* page's copy just outside the opposite edge (above). Each block then slides through the frame instead of blinking, and the deck reads as one continuous surface being scrolled. Objects parked outside the canvas are not rendered but must still exist on both pages with the same identity.

**When morph refuses to match**: PowerPoint pairs objects of the same kind first, so two different shape types, or a shape and a picture, will cross-fade instead of tweening. Authored decks force the pairing by giving both objects an identical custom shape name. The exporter does read a per-object name — `data-pptx-shape-name` on the wrapper — but that attribute is currently specified as **importer metadata** for mirror/preserve packages ([`svg-effects.md`](./svg-effects.md) §6.6), not as an authoring control for generated pages. Until that contract is widened, keep morph pairs the same object kind with matching geometry and `id`, and do not introduce the attribute on generated pages to force a match.

**Not supported — Slide Zoom / Summary Zoom.** Click-to-jump navigation built on PowerPoint's Zoom objects (the "click a portrait, zoom into that section" pattern) has no exporter path. Build click-driven navigation with `trigger_shape` on ordinary object animations instead, or with plain hyperlinks.

**No 3D**: perspective rotation, extrusion, and shear are outside the SVG contract — `skewX` / `skewY` and shear matrices fail closed ([`svg-effects.md`](./svg-effects.md) §6.8). Build the same impression with 2D means — offset, scale, overlap, and per-facet lightness (image-layout-patterns `#91`) — rather than attempting a 3D tilt.

---

## 4. Per-Element Animations

Off by default — enable deck-wide with `-a auto` (or another effect). Once enabled, three Start modes are available — these mirror PowerPoint's animation-pane "Start" dropdown:

- **`on-click`** — entering a slide → first click reveals the first semantic group; each subsequent click reveals the next group in z-order. Suits live presentations where the speaker paces reveals. Forbidden with `--recorded-narration` because video-ready exports need click-free playback.
- **`with-previous`** — all groups start together on slide entry, playing their object animation in parallel. Stagger ignored.
- **`after-previous`** (default) — first group fires on slide entry, subsequent groups cascade after the previous one finishes, with `--animation-stagger` extra spacing. Suits kiosk playback, recorded walkthroughs, or anyone who wants visual flow without clicking.

Enable with `-a auto`, select a canonical effect with
`--animation entrance_fade`, and choose Start behavior with
`--animation-trigger on-click|with-previous|after-previous`.

PowerPoint's separate **Trigger → On Click of** behavior uses group-only
`trigger_shape`. It links that row to another top-level group while unlinked
rows keep the slide Start mode; it is not a fourth deck-wide Start mode.

The registry exposes two layers:

- **203 PowerPoint-native object presets**: 53 `entrance_*` presets, 33
  `emphasis_*` effects, 64 `path_*` motion paths, and 53 `exit_*` effects.
  Examples include `entrance_bounce`, `emphasis_spin`, `path_circle`, and
  `exit_faded_zoom`. Each native key carries the complete PowerPoint-authored
  behavior tree, not a generic filter approximation.
- **29 legacy compatibility inputs**, listed by `--list`; new output never
  selects them.

Run the registry command for the exact categorized key list:

```bash
python3 skills/ppt-master/scripts/pptx_animations.py --list
```

Compatibility names normalize before selection and writing: for example,
`fade` resolves to `entrance_fade`; every old Fly direction name resolves to
`entrance_fly`; every old Wipe direction name resolves to `entrance_wipe`; and
`cut` resolves to `entrance_appear` because current PowerPoint has no separate
Cut object effect. Directional aliases preserve their old direction through
`effect_options`; legacy `wheel` maps to `entrance_wheel` with four spokes.
These names are accepted only as compatibility inputs.
Automatic selection, new sidecars, conversion traces, and writers use
canonical keys.

The native keys mirror the object-capable `MsoAnimEffect` surface. The four
media commands—play, pause, stop, and play from bookmark—are not object effects
for SVG groups and remain owned by the audio/video workflows.

- `auto` maps semantic ids to canonical entrances: charts/tables/timelines use
  `entrance_wipe`; cards/steps use `entrance_fly`; titles/takeaways use
  `entrance_fade`; image-like ids cycle a richer pool; unmatched ids cycle
  fade/wipe/fly/zoom.
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

Flags: `-a/--animation` selects effect/mode; `--animation-trigger` selects Start;
`--animation-duration` and `--animation-stagger` control base timing;
`--animation-config` selects a sidecar; `--no-animations` disables page/object
motion but preserves narration audio and recorded advance timing.

> Note: `--recorded-narration` rejects `on-click` and `trigger_shape`; use its default `narration_animations.json`, pass `--animation-config animations.json` for the canonical presentation animation, or pass `--no-animations`.

### 4.1 Slow ambient motion — the page that breathes

Most object animation exists to reveal content on click. There is a second, quieter use: **one long, slow motion on the background that never waits for a click**, so a static page stops looking frozen. It is the highest-impact-per-effort motion available and it costs one sidecar entry.

The recipe: a `path_left` (or `path_right`) motion on the **background image group only**, `with-previous` so it starts unprompted, and a duration of **4–10 s** — an order of magnitude longer than the reveal default. Set the travel distance so the image is still fully covering the canvas at both ends; a background that drifts past its own edge exposes the slide beneath it.

It pairs naturally with a fixed foreground: with image-layout-patterns `#90`, the scrim and its cut contour stay locked while the world moves behind the cuts, which reads as looking through windows rather than as a sliding photo. The same logic applies to `#82` and `#12`.

**Restraint is the whole technique**: one moving object per page, background only, never body copy or data. Two ambient motions on one page cancel each other out and the page reads as unstable.

### 4.2 Recurring recipes

Four combinations that recur constantly in authored decks. Each is built from
mechanisms already defined above — none needs a new capability.

**Carousel** (morph, §3.1) — hold a fixed row of card frames and rotate the *content* through them: on each page every image advances one position, so the card at centre changes while the frames stay put. Morph then slides the images between frames and the row appears to scroll. Requires identical frame geometry and `id`s on every page; only the image assignments change. Scales to any number of images with one page each.

**Odometer / counting numerals** (morph or motion path) — build a vertical strip of digits 0–9 and show one through a fixed window: a masked opening, or a background-filled rectangle above and below ([`image-layout-patterns.md`](./image-layout-patterns.md) `#95`). Shift the strip so the target digit lands in the window, then either morph between two pages or run a `path_up` motion on the strip. Give each digit column a 0.1 s stagger so they settle in sequence rather than in lockstep.

**Parallax depth** (morph) — move a background layer a *short* distance and a foreground layer a longer one between two pages. The differing travel is read as depth. Keep both layers' z-order identical on both pages; a layer that changes stacking between pages breaks the tween and the transition jumps.

**Flip-card / click-to-reveal** (`trigger_shape`, §4) — pair a face group and a back group at the same position, give the face an exit and the back an entrance, and set the back's `trigger_shape` to the face's id. Clicking the face plays both. This is the supported route for click-driven interaction; PowerPoint's Zoom objects are not (§3.1).

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

**Chrome stays static.** `data-pptx-layer` and explicit static
role/placeholder markers are absolute. For marker-free legacy SVGs, chrome-like
ids (background, header/footer, decor, watermark, page number, nav, logo, rule)
are skipped; an explicit sidecar entry may override only this name heuristic.
Keep wrappers and use `effect: none` for static content.

**Fallback for flat SVGs** (no top-level `<g>` wrappers, only raw `<rect>` / `<text>` / `<path>` at the root):

- ≤ 8 visible top-level primitives → each becomes one anchor (capped to avoid 70+ atom cascades on dense pages).
- > 8 → animation is skipped on that slide. The slide still renders, just without object animation.

Executors should wrap logical sections in `<g id>` regardless of whether you plan to animate. [`shared-standards-core.md`](./shared-standards-core.md) requires it.

---

## 6. Validation and Read-Back

Animation configuration is strict. Export fails on an unknown effect, mode, or
trigger; invalid timing/order values; a missing slide/group/`trigger_shape`
reference; a self-trigger; or any attempt to animate or trigger from a
structural layer. These errors never downgrade or silently omit a target.

Generated export reads each slide's timing tree back and checks row count/order,
trigger, trigger shape, shape target, preset class, resolved effect tuple, native behavior
signature, duration, and timeline offset. Package validation then checks root
timing placement, unique and valid `p:cTn` ids, and every `p:spTgt` reference.
The writer does not emit `p:bldP` for groups or pictures. Direct-PPTX preserve
mode tolerates unchanged legacy group/picture `p:bldP` rows from earlier PPT
Master exports; new generated packages remain strict.

Narration injection preserves animation and updates both p14 Choice/Fallback
when bounce timing is present; unsupported nested timing fails safely.
Direct-PPTX routes fingerprint source
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
