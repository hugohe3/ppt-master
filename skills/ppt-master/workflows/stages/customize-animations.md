---
description: Optional post-processing stage for per-slide and per-object animation overrides.
---

# Customize Animations Stage

> Optional Generate-PPTX post-processing stage for per-slide or per-object motion. Run when `<project_path>/animations.json` exists, the user explicitly asks for slide-specific motion, object order, effects, timing, or reveals, or the effective Custom Animations outcome in `design_spec.md §I` is enabled. Deck-wide transitions, auto-advance, and deck-wide per-element settings without page-specific motion or a sidecar use [`animations.md`](../../references/animations.md) directly. Quick may activate either path from the request/deck in active context without a Design Spec or interaction. The sidecar grammar is documented in [`pptx-animations.md`](../../scripts/docs/pptx-animations.md).

## When to Run

| Condition | Action |
|---|---|
| Effective Custom Animations outcome enabled | Run after the final SVG quality gate and any speaker-note pass, before Generate Step 7; §IX suggestions are advice |
| User asks for per-slide or per-object animation, reveal order, timing, or effect changes | Run |
| `animations.json` already exists | Run to resolve preserve/adjust/replace/suppress intent before export |
| §IX `Motion suggestion` only, no trigger above | Do not run; keep the suggestion as advice and normal export defaults |
| No request, outcome, or sidecar | Do not run; export keeps page transitions and no builds |
| Only deck-wide transitions, auto-advance, or one per-element policy, no sidecar | Do not run; apply `animations.md` with exporter flags such as `-a auto` or `-a emphasis_spin` |
| Only a page-transition sound, no object motion or sidecar | Do not run; resolve a sparse transition sidecar through `animations.md` §2.2 at export |
| An object-animation sound is requested | Run — the cue must bind to a resolved row and real target |
| `svg_output/*.svg` missing | Complete the Executor phase first |

**Decision precedence**: latest explicit instruction → final Stage-2 policy → workflow default `false`; provenance stays in §I, never the lock. A final Stage-2 `false` blocks creation, not an existing sidecar; explicit disables follow the table without deletion.

---

## 1. Resolve Intent and Read Semantic Context

Before editing `animations.json`, read every semantic file that exists — `design_spec.md` (content intent, narrative role, emphasis), `spec_lock.md` (page rhythm, layout role, chart/template constraints), `notes/total.md` or `notes/*.md` (speaker flow for reveal order, delays, emphasis). They inform but do not gate this stage: state what is missing and proceed with the rest plus visible SVG content; with none of them, use only explicit instructions, visible SVG, and `animations.md`'s resolution rules without inferring choreography beyond what the page expresses.

| Existing-sidecar intent | Action |
|---|---|
| Explicit Custom Animations disable | Preserve and validate the sidecar; return `-a none` |
| Explicit all-motion disable | Preserve and bypass it; return `--no-animations` |
| Explicit regeneration / rewrite / replacement | Rebuild the grouping plan and replace `animations.json`; prior choreography is not a constraint |
| Explicit adjustment / tuning / repair | Validate first; preserve valid semantic units; migrate affected references after regrouping |
| Stage activated with a sidecar and new §IX suggestions, no replacement request | Validate first; preserve valid choreography, adjust only affected units |
| Sidecar with no new instruction | Validate and preserve unchanged; repair an invalid sidecar/group reference before export |
| Ambiguous request | Default asks regenerate-or-modify; Quick decides from the request, SVG, and sidecar |

Unless an all-motion disable bypasses it, validate an existing sidecar first: `python3 skills/ppt-master/scripts/animation_config.py validate <project_path>`.

**Hard rule**: semantic files determine motion intent and unit boundaries; the current `svg_output/*.svg` supplies visible content and implementation structure, and its existing `<g>` hierarchy is never accepted as the plan merely because it exists.

**Decision ownership — understand, then design**: a §IX `Motion suggestion` states the communication job and relationship; it neither activates this stage nor locks implementation. Understand it, then develop the motion brief from the final SVG's semantic units, visible states, composition, and speaker flow — never a mechanical mapping to groups, effects, order, or timing. Executor may preserve, adapt, simplify, decline, or choose `none`; explicit user requirements bind; never change page content to justify animation.

**Hard rule — existing visible-layer boundary**: regroup only under §2 visual equivalence; never create or modify a crop, comparison layer, scrim, lens, hotspot, annotation, or other visible image state for motion. When a required state is missing and ordinary Slide-local authoring can supply it, return to Generate Step 6, rerun the final gate (and notes when enabled), then resume; when a structural boundary prevents that, simplify a non-binding suggestion to legal units, a page transition, or `none`, and let an explicit requirement follow failure recovery.

**No-op is complete**: if no sidecar exists, every page should keep the normal `fade` transition with no builds, and no explicit requirement is unmet, change no SVG, create no sidecar, and return to Step 7. Never author motion to expose a capability.

---

## 2. Rebuild Semantic Motion Units When Needed, Then List IDs

**Mandatory when object-targeted motion is in scope — content-first grouping audit**: inspect each affected slide's visible content against its communication job and speaker flow before treating any top-level `<g>` as an anchor. The affected set is the page named by an adopted suggestion or explicit request plus both endpoints of each Morph pair; untouched pages need no audit; a page-transition-only plan without Morph pairs skips regrouping and listing. Keep a group unchanged only when it already represents exactly one audience-facing motion unit or one continuing Morph object.

| Content condition | Grouping action |
|---|---|
| One group holds several independently narrated rows, cards, steps, claims, or stages | Split into descriptive direct-root siblings, one per unit |
| One unit is scattered across groups or root primitives | Merge or wrap its background, icon, label, value, and text into one direct-root group |
| A connector or arrow explains entry into a node or stage | Keep it with the relationship or target that makes it intelligible |
| A hero visual, overview graphic, takeaway, or warning has its own role | Its own group |
| The same object continues across adjacent Morph pages | Isolate each endpoint as one direct-root group of compatible kinds |
| Several atoms express one inseparable idea | Keep them together |
| Page chrome, structural layers, static framing | Preserve and exclude from ordinary targets |

**Hard rule — visual equivalence**: regrouping changes object boundaries only — preserve every visible pixel, paint order, coordinate, transform, inherited paint, opacity, clip, filter, reference, and native metadata; keep rendering-bearing wrappers nested when flattening could change appearance. **Hard rule — structural boundary**: never split or merge across `data-pptx-layer`, `data-pptx-placeholder`, native chart/table carrier, native preset, or imported logical-object boundaries; structural/static objects stay non-animatable; ordinary direct-root groups follow [`shared-standards-core.md`](../../references/shared-standards-core.md) §4.3 (descriptive unique `id`, positive root-coordinate `data-pptx-bounds`, no bounds on nested groups).

**Forbidden — group-list-first choreography**: choosing effects or order from `list-groups` before the audit; keeping a coarse wrapper because it has an `id`; splitting one idea into shapes or lines to raise the count; merging unrelated ideas to lower it; adding animation `data-*` attributes to SVG. There is no target group count.

After any regrouping, rerun the final gate (`svg_quality_checker.py <project_path> --canonical-authoring --stage final --json`; Quick inserts `--quick-generate` before `--stage`), then list the post-regroup anchors with `animation_config.py list-groups <project_path>` (one line per slide, chrome groups `bg` / `*-header` / `*-footer` / `*-decor` / `nav` / `watermark` / `logo` / `pagenumber` excluded). That list is the only source of slide and group keys for §3–§4. An explicit sidecar entry overrides only the marker-free legacy id-name heuristic; a group carrying `data-pptx-layer` or a static role/placeholder marker never animates. If a starting file is useful, `animation_config.py scaffold <project_path>` after regrouping creates a neutral scaffold (default object effect `none`, groups as empty `{}` placeholders) — creating it selects nothing, and it need not be read in full.

---

## 3. Plan Slide and Object Motion

**Mandatory**: plan the requested layers for each affected slide before editing — page transition (`defaults.transition` / `slides.<slide>.transition`), deterministic Morph pair (`slides.<destination>.morph`), page animation defaults (`defaults.animation` / `slides.<slide>.animation`), object lifecycle (`slides.<slide>.groups.<group_id>` as one legacy row or an ordered `effects[]`). A local object request needs no deck-wide transition review.

**Per-affected-page motion brief**: classify the communication job (including none) and each unit's lifecycle; choose only the required transition, effect, order, timing, and one dominant Start rhythm; mix modes or add emphasis/exit only for a distinct job with a restrained effect. **Mandatory — select from meaning, not catalog coverage**: run the page-relationship and lifecycle playbooks in `animations.md` §3–§4 before any specific effect; candidates are recall aids. **Title motion**: classify the lifecycle, then choose immediate, delayed, synchronized, post-hero, or narration-cued timing; use the sidecar override for a marker-free chrome-like id and repair an incorrect structural marker before animating it. **Default — inherit unaffected layers (may override when the page's job requires it)**: leave the transition and untouched pages on defaults; add a slide-specific `transition` only when the page needs one. **Timing**: shorter for dense/repeated scan content, longer for pivots, hero diagrams, section boundaries, and takeaways; uniform timing is valid. **Reference — motion judgment**: decide job, lifecycle, tone, audience order, and whether direction carries meaning before geometry; a unit that gains no clarity or feeling is `static` (`none`, `entrance_appear`, or `entrance_fade` only when that matches the lifecycle); layout direction alone requires no motion; variation follows content or tone, never quota.

### 3.1 Supported Page Transitions

One of the 48 canonical native effects in `animations.md` §3 (the complete Subtle, Exciting, and Dynamic Content gallery); the eight old names are compatibility inputs only and normalize to a canonical effect plus `effect_options`; `none` removes the visual effect while timed advance remains. Fields: `effect`; `effect_options` (only the selected effect's native options — run `pptx_animations.py --describe-transition <effect>` first and never infer another effect's fields); `duration` (> 0 s); `auto_advance` (non-negative seconds, click still enabled, valid with `effect: none`); `sound` (project-relative `.wav`, selected only after the transition is resolved). For a cross-slide continuation that must not depend on PowerPoint's automatic matching, put one `morph` block on the destination whose `from` is the immediately preceding SVG and whose pair keys bind one source direct-root group to one destination group (the exporter supplies `!!`); Morph by object only.

### 3.2 Supported In-Slide Animations

The 203 canonical keys — 53 `entrance_*`, 33 `emphasis_*`, 64 `path_*`, 53 `exit_*` (`pptx_animations.py --list`), each preserving PowerPoint's complete behavior tree. `auto` / `mixed` / `random` apply to generic `enter` only (`auto` maps roles to canonical entrances with a richer pool for image-like ids; `mixed` cycles 16 presets by group order; `random` selects deterministically from the same pool) and never choose emphasis, path, or exit implicitly; `none` excludes the object or slide. The 29 old short names are compatibility inputs (Fly/Wipe directions → `entrance_fly` / `entrance_wipe` with `effect_options.direction`, `cut` → `entrance_appear`, legacy `wheel` keeps its four-spoke amount). **Hard rule — explicit semantic choreography**: when a plan depends on a specific lifecycle, relationship, or order, target real groups with explicit canonical effects and order; generic modes are valid only when generic entrance treatment suffices. Start modes: `after-previous` (click-free cascade), `with-previous` (one coordinated beat), `on-click` (controlled reveal).

### 3.3 Optional Sound Pass

Only after visual transition, lifecycle, effect, order, and timing are complete; sound is post-processing state never written to or recovered from the Design Spec or lock. No resolved cue → omit every `sound` field and create no `sounds/`. A bundled cue fits one resolved row → read the complete [`sound-vocabulary.md`](../../templates/sounds/sound-vocabulary.md), choose from the auditory job, then sync only the selected ids (`sound_sync.py list --query <term>` for optional filtering; `sound_sync.py <project_path> <namespace>/<sound_id> ...`) and reference `sounds/<namespace>/<file>.wav` in `transition.sound`, `animation.sound`, or the group/effect row. User-provided audio in the project uses its own path when the format is valid. Never reference `skills/ppt-master/templates/sounds/` from `animations.json`; the global library is a selection source, not an exporter fallback. Gain, limiting, and video mixing belong to [`generate-audio`](./generate-audio.md), never this sidecar.

---

## 4. Edit `animations.json`

**Hard rule — sparse overrides reference real targets**: write only affected slides and only fields that differ from exporter or sidecar defaults; an unlisted SVG inherits deck-wide settings; a listed slide carries only the `transition`, `animation`, `groups`, or `morph` fields it overrides; `defaults` is optional and deck-wide only; chrome groups stay out (the exporter pins them to `none`), and a legacy chrome-like id is named only on explicit reviewed intent with no structural marker. **Forbidden**: a slide absent from `svg_output/`; a missing, ambiguous, or structural group; enumerating every group to restate the slide default; listing a group with `data-pptx-layer` or a static role/placeholder marker; animation `data-*` attributes in SVG.

**Hard rule — one group representation**: a populated `groups.<id>` uses either the legacy single-effect fields or `effects[]` (non-empty, every row naming `effect`), never both; an untouched scaffold `{}` is neutral; omitted row duration, Start, timing/completion controls, and sound inherit the resolved slide values. `effect_options` may hold `direction`, `amount`, `color`, `font_name`, `relative`, or `size`, but only fields the selected effect supports — run `pptx_animations.py --describe <canonical_effect>` before writing a parameterized effect; `duration` owns Speed and `accelerate` / `decelerate` own smooth start/end (no duplicate fields); Change Font's `font_name` is one target-installed face, never a CSS stack. The complete field reference — transition, morph, slide animation defaults, per-row trigger, order, delay, duration, `trigger_shape`, repeat, reverse/rewind, timing ratios, restart, after-effect, sound — is [`pptx-animations.md`](../../scripts/docs/pptx-animations.md) §8. Use the multi-category `effects[]` example in `animations.md` §2 and the two-slide Morph example in §2.1 (never copy the source group into the destination `groups` to establish identity); keep the legacy object for one-row overrides and never convert old sidecars mechanically.

---

## 5. Validate and Return to Generate Export

When `animations.json` was created or changed after §1, run `python3 skills/ppt-master/scripts/animation_config.py validate <project_path>`, then return to the owning export path — Default [`generate-pptx.md`](../generate-pptx.md) Step 7.1; Quick [`quick-generate.md`](../profiles/quick-generate.md) §4 — both of which read the sidecar automatically. If §2 changed `svg_output/`, complete the owning route's final SVG rerun before returning; never finalize or export from this stage.

**Validation**: unknown effects/modes/triggers; unsupported options; incompatible, boolean, non-finite, or out-of-range timing; non-positive durations; negative delay/stagger; invalid order; missing slides/groups; structural targets; and Morph pairs with non-adjacent sources, missing or ambiguous groups, conflicting or undeclared keys, non-object Morph, or a target that does not remain one compatible Slide-local object all fail — never replaced by a fallback or silently dropped. `--animation none` still disables all per-element animation. A passing sidecar, timing-tree read-back, and sound relationship check prove the PPTX configuration, not an exported MP4 audio track. Step 7 export reads back row order, trigger, target, effect, duration, offset, placement, IDs, and shape references; narration preserves them; direct-PPTX routes preserve source animation and never author it.

### 5.1 Optional Video Motion Handoff

When a downstream renderer will enhance the deck, have Step 7.3 append `--conversion-trace`, then derive the plan from the final resolved trace (the `--recorded-narration` trace for narrated output): `python3 skills/ppt-master/scripts/video_motion_plan.py <project_path>/validation/<output_stem>.trace.json -o <project_path>/validation/video_motion_plan.json --style adaptive --force`. The plan locks identity, effect, direction, order, bounds, and timing and may refine renderer parameters only ([`video-motion-plan.md`](../../scripts/docs/video-motion-plan.md)). With resolved sound cues on the native-export branch, the same final trace and narrated PPTX feed `video_sound_mix.py`; an explicit slideshow capture records native cue playback and uses no trace for mixing.

---

## ✅ Customize Animations Complete

- [x] Semantic context and motion intent resolved
- [x] Adopted object targets use real post-regroup SVG ids when object motion is in scope
- [x] Sparse `animations.json` overrides valid when present; a no-op path creates none
- [x] Any regrouped SVG passed the final quality gate
- [x] Control returned to Generate Step 7; any video plan waits for the final resolved trace
