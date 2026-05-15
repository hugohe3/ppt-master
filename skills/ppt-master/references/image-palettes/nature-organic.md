# Palette: nature-organic

Earthy, natural, wellness. The palette for environment / sustainability / wellness / outdoor / food / agriculture decks. Distinguished by **earth-toned warm and cool greens**, with cream and earth-brown backgrounds.

> This file describes **color behavior**, not HEX values.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Mid — earth tones are rich but slightly desaturated |
| Brightness contrast | Soft — earth tones layer comfortably |
| Color count visible | 3-4 |
| Mood | Grounded, natural, sustainable, contemplative |
| Material | Soft natural textures permitted |

---

## 2. Proportion rule (50-35-15, earthy)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / natural field | **45-55%** | `secondary` | Cream, soft warm beige, or pale sage. The "outdoor breath" of the image. |
| Primary natural color | **30-40%** | `primary` | Deep forest green, deep earth brown, warm terracotta. Dominant natural element. |
| Accent natural pop | **10-15%** | `accent` | A small natural pop — golden honey, soft coral, deep autumn red. Often used as a fruit, flower, or warm detail. |

---

## 3. Role semantics

- **Primary** is the natural anchor — the dominant earth color (greens for forest/wellness, browns/terracottas for earth/agriculture).
- **Secondary** is the natural breath — soft cream or sage carrying outdoor warmth.
- **Accent** is a small natural detail — never artificial-bright, always feels found-in-nature.

---

## 4. How to phrase it in a prompt

> "Color behavior is nature-organic: secondary soft cream `#FEF3C7` covers the background field as gentle outdoor breath (about 50%). Primary deep forest green `#166534` carries the dominant natural forms — foliage, hills, organic shapes (about 35%). Accent warm honey `#D4AF37` appears in small natural detail pops — a flower, a fruit, a sunlit highlight (about 13%). All tones feel earthy and slightly desaturated, like a sustainable wellness palette."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ nature | Direct alignment |
| ✓✓ watercolor | Natural washes |
| ✓✓ warm-scene | Outdoor warm cinematic |
| ✓✓ fantasy-animation | Storybook nature |
| ✓✓ sketch-notes | Educational nature content |
| ✓✓ corporate-photo | Outdoor / wellness photography |
| ✓ vector-illustration | Natural vector |
| ✗ tech-neon / dark-cinematic / digital-dashboard / blueprint | Wrong temperament |
| ✗ pixel-art | Earth feel doesn't fit pixel grid |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a nature illustration**

> [...rendering paragraph...] Color behavior is nature-organic: soft cream background `#FEF3C7` (about 50%); primary deep forest green `#166534` in stylized leaves and a central tree silhouette (about 35%); accent warm honey-amber `#D4AF37` in small detail pops — a few hand-drawn flowers at the base, sunlit highlights on leaf tips (about 13%). Earth-toned and slightly desaturated. [...container guidance...]
