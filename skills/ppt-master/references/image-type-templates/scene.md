# Type: scene

Atmospheric environment with narrative — a moment, a place, a situation rendered as a small story. Used for case studies, brand storytelling, lifestyle pages, personal narrative slides.

> **What scene means inside a PPT block**: the image internally is **a moment in a place** — environment, figures (if any), atmosphere, mood. Unlike `hero` (single dominant subject), scene has **context and narrative**. Unlike `background` (no subject), scene has **inhabitants**.

## Composition skeleton

```
   ┌────────────────────────────────────┐
   │  sky / atmosphere (foreground      │
   │                    or upper area)  │
   │                                     │
   │    figure / subject in environment  │
   │           ↑ foreground              │
   │  ────────────────────────────       │
   │   middle ground (context, objects)  │
   │  ────────────────────────────       │
   │   background (atmospheric depth)    │
   └────────────────────────────────────┘
```

| LAYOUT | Three-layer composition: foreground (subject + immediate context), middle ground (supporting environment), background (atmospheric depth). The viewer reads the scene like a small story |
| ELEMENTS | One or more figures (simplified silhouettes unless `corporate-photo`) in an environment. Environmental elements (sun, lamp, tree, desk) support the narrative |
| NEGATIVE SPACE | Atmospheric perspective creates breathing room — background paler than foreground |
| ATMOSPHERE | Lighting direction, color temperature, and mood are deliberate (golden-hour, evening light, morning haze, etc.) |

## Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Hero scene banner | 1200×600 | 2:1 | 10% (scenes fill the frame) |
| Half-page narrative | 600×800 | 3:4 | 10% |
| Wide scenic | 1200×500 | 2.4:1 | 10% |
| Square scene | 700×700 | 1:1 | 10% |

## Text-policy variants

### `text_policy: none` (essentially always)

Scenes are visual narratives — text would interrupt. Use `text_policy: none`.

### `text_policy: embedded` (very rare)

Only when the scene includes a tiny diegetic text (a sign in the scene, a label on a book) — these often fail to render correctly. Usually better as `text_policy: none`.

## Fewshot prompt snippets

**Snippet A — warm-scene + warm-earth personal story, text_policy: none, 1200×600**

> Atmospheric scene illustration with golden-hour cinematic lighting. The composition is a three-layer narrative: foreground left — a softly rendered simplified figure silhouette walking along a path with warm long shadows cast toward the right; middle ground — the warm path winds into a stylized hillside with a few suggested trees; background — atmospheric perspective creates pale warm distance, sky transitioning from amber `#D97706` at the horizon to soft cream `#FEF3C7` at the top. Lighting is warm golden-hour from the upper right. Foreground in deeper warm primary `#9A3412`; small accent gold `#D4AF37` highlights on sunlit surfaces. No hard outlines — forms emerge from light and shadow. Subtle film grain at 8% opacity. Composed as a 1200×600 hero scene with 10% inner padding. Simplified silhouette figure only — no realistic face. NO text or labels. Color values are rendering guidance only.

**Snippet B — corporate-photo + warm-earth team scene, text_policy: none, 1200×600**

> Editorial photography of a small modern team collaborating around a workspace. Foreground: three diverse, professionally attired adults engaged in genuine conversation over a laptop and notebooks on a wooden desk. Middle ground: a colleague visible in the background, slightly out of focus, working on their own laptop. Background: large window with soft natural light streaming in, contemporary office context. Soft window light from the left creates warm-amber highlights on subjects' faces and equipment; deeper warm shadows in the desk area. Color grading warm-editorial — primary terracotta `#9A3412` in shadow tones, secondary cream `#FEF3C7` in highlights, accent gold `#D4AF37` on wood and a small warm desk-lamp glow. Shallow depth of field — foreground subjects sharp, middle/background gently blurred. Composed as a 1200×600 hero scene with 10% inner padding. Diverse, professionally attired subjects rendered photorealistically. NO text. Color values are rendering guidance only.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| No foreground/midground/background depth | Layer rule omitted | "Three-layer composition: foreground, middle ground, background — atmospheric perspective creates depth" |
| Realistic faces in non-photo rendering | §3.2 omitted | Reaffirm "simplified silhouette figures only, no realistic faces" (exception: corporate-photo rendering) |
| Too many subjects competing | Narrative focus weak | "Clear narrative focus — one primary scene moment, supporting elements contextual not competing" |
| Mood inconsistent | Lighting direction not specified | "Single deliberate light source — direction explicit (e.g. upper right, warm golden-hour)" |
| Cluttered with detail | Scene too busy | "Atmospheric — scenes suggest rather than describe; restrained detail" |

## When to switch away from scene

- If pure atmosphere with no subject → `background`
- If single dominant subject without environment → `hero`
- If structured information with zones → `infographic`
- If conceptual relationships → `framework`
- If chronological progression → `timeline`
