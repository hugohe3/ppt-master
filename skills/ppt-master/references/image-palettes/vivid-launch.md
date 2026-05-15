# Palette: vivid-launch

Bold, saturated, attention-grabbing. The palette for product launches, marketing campaigns, event keynotes, promotional decks. Distinguished from tech-neon by **richer warm-cool balance** and more confident multi-color presence.

> This file describes **color behavior**, not HEX values.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | High — colors are intentionally vivid |
| Brightness contrast | Strong — vivid colors against bright field |
| Color count visible | 3-4 |
| Mood | Energetic, confident, promotional, attention-first |
| Material | Flat saturated fills |

---

## 2. Proportion rule (40-35-25, vivid-balanced)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Bright field / background | **35-45%** | `secondary` | Often near-white, bright cream, or a saturated brand color used as background. |
| Primary brand vivid | **30-40%** | `primary` | The vivid lead — saturated brand color in confident solid blocks. |
| Accent vivid pop | **20-30%** | `accent` | More generous than other palettes — accent is a co-star, not a small detail. Can take 20-25% of canvas. |

> vivid-launch is the **most accent-generous** palette — promotional context tolerates strong color presence.

---

## 3. Role semantics

- **Primary** is the brand lead — the vivid signature of the launch.
- **Secondary** is the bright supporting field — should feel "open" and "celebrate".
- **Accent** is the co-star — bold, generous, attention-grabbing. Can take much more area than other palettes' accents.

---

## 4. How to phrase it in a prompt

> "Color behavior is vivid-launch: secondary near-white `#FAFAFA` (about 40%) carries the bright field; primary saturated brand magenta `#E11D48` carries dominant shapes in confident vivid blocks (about 35%); accent vivid orange `#F97316` is a co-star color appearing in 25% of the canvas as a major secondary subject. All colors are intentionally saturated and bold. Promotional, attention-grabbing temperament."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ flat | Vivid flat blocks for marketing |
| ✓✓ vector-illustration | Bold vector launch visuals |
| ✓✓ 3d-isometric | Vivid product 3D |
| ✓✓ screen-print | Vivid promotional poster |
| ✓✓ pixel-art | Retro vivid gaming launch |
| ✓ digital-dashboard | Acceptable if launch product is software |
| ✓ corporate-photo | Vivid-graded photography |
| ✗ sketch-notes / ink-notes / nature | Wrong temperament — those are restrained |
| ✗ watercolor / warm-scene | Wrong saturation level |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a flat marketing hero**

> [...rendering paragraph...] Color behavior is vivid-launch: secondary near-white `#FAFAFA` background (about 38%); primary saturated brand magenta `#E11D48` carries the dominant central shape — a bold geometric burst (about 35%); accent vivid orange `#F97316` is co-star — a large supporting block or burst in the upper right (about 25%). One small detail in deep neutral `#171717` for definition (about 2%). All colors confident and saturated. Promotional energy. [...container guidance...]
