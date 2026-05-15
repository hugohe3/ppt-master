# Palette: warm-earth

Friendly, grounded, human. The warm counterpart to cool-corporate — used in brand storytelling, lifestyle, education, wellness, and any deck where human warmth matters more than corporate restraint.

> This file describes **color behavior**, not HEX values. HEX comes from `design_spec.colors`.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Medium — warm tones feel rich but not vivid |
| Brightness contrast | Moderate — warm earth tones layer well without harsh contrast |
| Color count visible | 3-4 (primary + secondary + accent + optional warm neutral) |
| Mood | Friendly, grounded, approachable, slightly nostalgic |
| Material | Soft — leaves room for texture (paper grain, watercolor wash) |

---

## 2. Proportion rule (50-35-15, applied to the deck's HEX)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / supporting field | **50-60%** | `secondary` | Warm cream, soft beige, gentle off-white. Carries breathing space with warmth. |
| Main subject / dominant warm element | **30-40%** | `primary` | The earthy warm tone — terracotta, deep amber, warm rust, deep olive. The visual anchor. |
| Emphasis / warm pop | **10-15%** | `accent` | A small concentrated warm pop (golden yellow, coral, deep red). More generous than cool-corporate's 5-7%, because warm palettes tolerate more saturation visually. |

> warm-earth is more permissive than cool-corporate about color presence — warm tones layer comfortably without feeling promotional.

---

## 3. Role semantics

- **Primary** carries grounding warmth, the human anchor. Use it for: dominant warm forms, foreground subjects, body of illustration, main subject silhouette.
- **Secondary** is the warm breathing field. Use it for: soft cream background, paper field, atmospheric haze. Should feel cozy, not sterile.
- **Accent** carries small warm pops of energy. Use it for: the standout flower, the warm sunlight glow, the highlighted detail. Allowed to be slightly more visible than cool-corporate's accent.

---

## 4. How to phrase it in a prompt

> "Color behavior is warm-grounded: secondary `#FEF3C7` (warm cream) carries about 55% of the canvas as soft breathing space; primary `#9A3412` (deep terracotta) anchors the main forms in confident warm tones occupying about 32%; accent `#D4AF37` (warm gold) appears in small concentrated pops totaling under 13% — perhaps as a glow, a flower, a sunlight detail. Soft warm temperament throughout, no cool tones."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ vector-illustration | Warm vector forms work well |
| ✓✓ flat | Warm flat blocks are friendly |
| ✓✓ sketch-notes | Natural pairing — both warm-earth and sketch-notes share warmth |
| ✓✓ watercolor | Warm washes pair perfectly |
| ✓✓ warm-scene | Direct alignment |
| ✓✓ fantasy-animation | Storybook warmth |
| ✓✓ nature | Earth-tone alignment |
| ✓✓ corporate-photo | Warm-graded photography |
| ✓ editorial | Acceptable — editorial restraint sometimes prefers cool |
| ✗ tech-neon themes / dark-cinematic | Temperament conflict |
| ✗ blueprint | Blueprint wants restraint; warm-earth wants warmth |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a watercolor narrative scene**

> [...rendering paragraph...] Color behavior is warm-grounded: secondary cream `#FEF3C7` occupies the upper third as soft sky and breathing space (about 50% of canvas); primary deep terracotta `#9A3412` carries the midground hills and foreground earth in confident warm washes (about 35%); accent warm gold `#D4AF37` appears as a small concentrated glow near the horizon and a single golden bird shape in the foreground (totaling under 15%). All tones warm, no cool blues or greens beyond a barely-perceptible suggestion in the sky. [...container guidance...]

**Snippet B — applied to a sketch-notes educational block**

> [...rendering paragraph...] Color behavior is warm-grounded: cream paper background `#FEF3C7` carries about 55% of the area. Primary deep amber `#B45309` fills the rounded info boxes in a soft pastel tint (about 35% area). Accent warm coral `#F97316` appears on one highlighted arrow and a few small doodle decorations (totaling 10-13%). All hand-drawn ink in near-black. No cool tones. [...container guidance...]

---

## 7. Forbidden

- Cool color mixing (a stray blue / teal breaks the warm identity)
- Over-saturated accent (warm-earth's accent is warm-rich, not neon-loud)
- Sterile / clinical feel (defeats the warmth — switch to cool-corporate)
- Equal-share triplet (creates a flag-like balance instead of warm-grounded depth)

---

## 8. When to switch away

- For corporate / consulting → `cool-corporate`
- For premium / cinematic → `dark-cinematic`
- For methodology / sharp manifesto → `mono-ink`
- For event / launch / saturated bold → `vivid-launch`
