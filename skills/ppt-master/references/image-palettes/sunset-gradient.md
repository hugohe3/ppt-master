# Palette: sunset-gradient

Warm gradient flow — pink → orange → purple, atmospheric and energetic. Used for lifestyle / creative agencies / travel / music / event / modern brand decks where mood and warmth carry the page. Distinguished by being the **one palette built around transitions**, not flat blocks.

> This file describes **color behavior**, not HEX values. sunset-gradient tells the model how to apply the deck's HEX values **as gradient stops**, not as discrete fills.

## 1. Compatible renderings

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

## 2. Fewshot prompt snippets

**Snippet A — applied to a flat lifestyle hero**

> [...rendering paragraph...] Color behavior is sunset-gradient: smooth diagonal gradient flowing from primary deep pink `#EC4899` in the lower-left corner, transitioning through secondary warm orange `#F97316` across the middle band, into accent purple `#9333EA` in the upper-right corner. Smooth blending — no hard color edges. Above the gradient field, one stylized flat near-black silhouette of a stylized palm tree sits at the lower right as a focal rest point (about 6% of canvas). Atmospheric, energetic, optimistic. [...container guidance...]