# Palette: sunset-gradient

Warm gradient flow — pink → orange → purple, atmospheric and energetic. Used for lifestyle / creative agencies / travel / music / event / modern brand decks where mood and warmth carry the page. Distinguished by being the **one palette built around transitions**, not flat blocks.

> This file describes **color behavior**, not HEX values. sunset-gradient tells the model how to apply the deck's HEX values **as gradient stops**, not as discrete fills.

---

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Mid to high; smooth transitions, never harsh |
| Brightness contrast | Continuous gradient — no sudden value jumps |
| Color count visible | 2-3 stops blended; one optional accent break |
| Mood | Atmospheric, energetic, warm, optimistic-romantic |
| Material | Light + atmosphere — sunset sky, neon glow, soft radiance |

---

## 2. Proportion rule (gradient flow, not block proportions)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Gradient field | **80-90%** | `primary` → `secondary` → `accent` as stops | The entire canvas is a smooth blend; no hard color boundaries |
| Accent break (optional) | **5-10%** | A single small shape in `accent` (or a contrasting cool color if all three HEX are warm) | One deliberate "rest" point in the gradient |
| Negative shape (optional) | **5-10%** | Near-white or near-black silhouette cut from the gradient | Adds compositional anchor without breaking flow |

> **Hard rule**: sunset-gradient requires **smooth blending** between stops. Discrete color blocks turn the palette into a flag — switch to `vivid-launch` or `duotone` for block compositions.

---

## 3. Role semantics

- **Primary** is the warmest stop (often the deepest pink/red) — anchors the gradient's emotional core
- **Secondary** is the middle stop (orange/peach/coral) — bridges the transition
- **Accent** is the cool stop (purple/lavender/magenta) — closes the gradient at the opposite end
- The **direction** of the gradient (horizontal / vertical / diagonal / radial) is a composition choice — pick the one that supports the slide's narrative weight

---

## 4. How to phrase it in a prompt

> "Color behavior is sunset-gradient: smooth diagonal gradient flowing from primary deep pink `#EC4899` in the lower-left corner, transitioning through secondary warm orange `#F97316` across the middle band, into accent purple `#9333EA` in the upper-right corner. Smooth blending throughout — no hard color edges. Optional: one small near-white silhouette shape cuts from the gradient as a focal rest point (about 5% of canvas)."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ flat | Smooth gradient on flat geometry |
| ✓✓ watercolor | Gradient is watercolor's native language |
| ✓✓ warm-scene | Sunset-grade cinematic atmosphere |
| ✓ vector-illustration | Acceptable but requires the gradient exception (vector-illustration normally bans gradients — sunset-gradient explicitly overrides for the background) |
| ✓ glassmorphism | Soft cool gradient under glass panels (use a tame variant) |
| ✓ 3d-isometric | Gradient sky behind isometric forms |
| ✗ minimalist-swiss / blueprint / mono-ink | Wrong temperament |
| ✗ pixel-art / sketch-notes / ink-notes / chalkboard | Wrong material |
| ✗ corporate-photo | Photography uses real grading, not painted gradient |

> **Override**: sunset-gradient is the palette that **forces a gradient** into the image. When the chosen rendering normally bans gradients (e.g. vector-illustration), the gradient applies to the **background field only**, while shapes on top remain flat per the rendering's rules.

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a flat lifestyle hero**

> [...rendering paragraph...] Color behavior is sunset-gradient: smooth diagonal gradient flowing from primary deep pink `#EC4899` in the lower-left corner, transitioning through secondary warm orange `#F97316` across the middle band, into accent purple `#9333EA` in the upper-right corner. Smooth blending — no hard color edges. Above the gradient field, one stylized flat near-black silhouette of a stylized palm tree sits at the lower right as a focal rest point (about 6% of canvas). Atmospheric, energetic, optimistic. [...container guidance...]
