# Type: scene

Atmospheric environment with narrative — a moment, a place, a situation rendered as a small story. Used for case studies, brand storytelling, lifestyle pages, personal narrative slides.

> **What scene means inside a PPT block**: the image internally is **a moment in a place** — environment, figures (if any), atmosphere, mood. Unlike `hero` (single dominant subject), scene has **context and narrative**. Unlike `background` (no subject), scene has **inhabitants**.

## 1. Composition skeleton

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

## 2. Text-policy variants

### `text_policy: none`

Scenes are visual narratives — most read better with text routed to SVG overlay.

### `text_policy: embedded` (decorative atmosphere or diegetic text)

Two valid cases:
- Decorative atmosphere lettering — a large stylized word in the bleed serving as visual mood ("WANDER", "QUIET"). Describe artistic treatment; spelling is not critical.
- Diegetic text — a sign in the scene, a label on a book. Often fails to render correctly; only use when essential to the narrative.

---

## 3. Fewshot prompt snippets

**Snippet A — warm-scene + warm-earth personal story, text_policy: none, 1200×600**

> Atmospheric scene illustration with golden-hour cinematic lighting. The composition is a three-layer narrative: foreground left — a softly rendered simplified figure silhouette walking along a path with warm long shadows cast toward the right; middle ground — the warm path winds into a stylized hillside with a few suggested trees; background — atmospheric perspective creates pale warm distance, sky transitioning from amber `#D97706` at the horizon to soft cream `#FEF3C7` at the top. Lighting is warm golden-hour from the upper right. Foreground in deeper warm primary `#9A3412`; small accent gold `#D4AF37` highlights on sunlit surfaces. No hard outlines — forms emerge from light and shadow. Subtle film grain at 8% opacity. Composed as a 1200×600 hero scene with 10% inner padding. Simplified silhouette figure only — no realistic face. NO text or labels. Color values are rendering guidance only.