# Palette: macaron

Soft pastel, gentle, approachable. The signature palette for education, onboarding, children's content, knowledge cards, and warm friendly explainers. Distinguished by **pastel-tinted** versions of the deck's HEX values on a warm cream field.

> This file describes **color behavior**, not HEX values. HEX comes from `design_spec.colors`, but rendered as pastel tints.

## Temperament

| Trait | Setting |
|---|---|
| Saturation | Low to moderate — colors are tinted toward pastel |
| Brightness contrast | Soft — gentle transitions, no harsh contrast |
| Color count visible | 3-4 pastel tints + black ink for lines (when paired with sketch-notes) |
| Mood | Gentle, approachable, educational-warm, slightly playful |
| Material | Soft block fills (often hand-painted overshoot quality) |

## Proportion rule (50-40-10, pastel-graded)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / paper field | **45-55%** | `secondary` | Warm cream `#F5F0E8` or near-cream — the "paper" the macarons sit on. May override deck's secondary if it doesn't lean cream. |
| Pastel block fills | **35-45%** | `primary` (pastel-tinted) + 2-3 supporting pastels | The block colors — soft tinted versions of primary, plus complementary pastels (light blue, mint, lavender, peach). Each block fills with its own pastel. |
| Emphasis pop | **5-10%** | `accent` | A small concentrated pop — often used sparingly as the "this is the answer" coral or warm yellow. |

## Role semantics

- **Background** carries warmth and friendliness — should feel like a thoughtful teacher's notebook page.
- **Pastel blocks** carry information zones — each block is a different soft tint, used to differentiate sections without shouting.
- **Accent** is the one warm pop — used 1-2 times max in an entire image, drawing the eye to the key takeaway.

## How to phrase it in a prompt

> "Color behavior is macaron pastel: warm cream paper background `#F5F0E8` covers about 50% of the canvas. Pastel block fills in soft tints — light blue, mint green, lavender, peach — fill the rounded info shapes (about 40% total area, divided across 3-4 blocks). Accent warm coral `#F97316` appears in one or two small emphasis points only (under 10%). All pastel fills have slight hand-painted overshoot beyond their outlines. Soft, friendly, educational temperament throughout."

## Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ sketch-notes | Direct alignment — macaron is the default sketch-notes palette |
| ✓✓ flat | Pastel flat blocks for friendly content |
| ✓✓ vector-illustration | Pastel vector for educational warmth |
| ✓✓ watercolor | Pastel washes pair naturally |
| ✓✓ fantasy-animation | Storybook pastels |
| ✓✓ chalkboard | Pastel chalk on dark slate |
| ✓ pixel-art | Pastel retro |
| ✗ tech-neon / dark-cinematic / blueprint | Wrong temperament |
| ✗ corporate-photo | Photography wants natural color |
| ✗ digital-dashboard | Dashboards want vivid not pastel |

## Fewshot prompt snippets

**Snippet A — applied to a sketch-notes infographic**

> [...rendering paragraph...] Color behavior is macaron pastel: warm cream paper background `#F5F0E8` covers about 50%. Four rounded info boxes filled with soft pastels — light blue (pastel tint of primary `#1E3A5F`), mint (pastel tint of secondary `#F8F9FA` shifted greener), lavender, peach. Each fill has slight hand-painted overshoot beyond its black ink outline. Accent warm coral `#F97316` appears only on one highlighted hand-drawn arrow connecting two boxes (about 6%). Friendly educational temperament. [...container guidance...]

**Snippet B — applied to a flat illustration knowledge card**

> [...rendering paragraph...] Color behavior is macaron pastel for a knowledge-card aesthetic. Warm cream background `#F5F0E8` (about 55%). One large rounded rectangle in pastel mint occupying the lower half (about 30%), with a smaller pastel-peach circle overlapping its upper edge (about 10%). One small accent coral `#F97316` dot at the focal point of the composition (about 5%). All shapes have soft hand-painted overshoot edges. Gentle, knowledge-card feel. [...container guidance...]

## What to avoid

- Saturated full-strength colors (defeats macaron's pastel identity)
- Cool / sterile background (cream warmth is essential)
- Hard digital edges (macaron's softness needs hand-painted feel)
- Heavy accent presence (one pop is enough)

## When to switch away

- For corporate / consulting → `cool-corporate`
- For warm-earth storytelling → `warm-earth`
- For methodology sharpness → `mono-ink`
- For premium dark → `dark-cinematic`
