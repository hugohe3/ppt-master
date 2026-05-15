# Palette: frost-ice

Near-white field with pale cool accents — icy blue, pale silver-gray, hint of crystalline. Clean, clinical, premium-minimal, calming. Used for health / medical / beauty / skincare / wellness / premium SaaS / B2B tech where serenity and clarity are the primary visual signal.

> This file describes **color behavior**, not HEX values. frost-ice tells the model how to apply the deck's HEX values with **maximum breathing room and cool restraint**.

---

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Very low — colors approach white asymptotically |
| Brightness contrast | Soft — almost all light values, with one subtle deeper accent |
| Color count visible | 2-3 (near-white field + pale cool + one slightly-deeper accent) |
| Mood | Clean, calming, clinical, premium-minimal |
| Material | Frosted glass / fresh snow / fine porcelain — never warm |

---

## 2. Proportion rule (80-15-5, near-white dominant)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Field / background | **75-85%** | `secondary` pushed toward near-white (`#F8FBFD` / `#F0F4F8` / `#FFFFFF`) | The vast calm field. Frost-ice's identity *is* this breathing room. |
| Pale cool primary | **10-15%** | `primary` rendered as a pale cool tint (icy blue, pale silver, faint mint) | Subtle structure — visible but never assertive |
| Accent / focal | **3-7%** | `accent` (often a slightly deeper cool — steel blue, polished silver) | The single moment of visual weight |

> **Hard rule**: frost-ice keeps the field over 75% of the canvas. If structural elements push the field below 70%, the palette identity breaks — switch to `cool-corporate`.

---

## 3. Role semantics

- **Field** carries serenity — it must feel vast, calm, almost empty. Frost-ice is defined by what *isn't* there.
- **Pale cool primary** carries gentle structure — used for soft shapes, subtle dividers, faint geometry
- **Accent** is the single focal moment — one small but deliberate visual anchor; never repeated

---

## 4. How to phrase it in a prompt

> "Color behavior is frost-ice: secondary near-white `#F8FBFD` occupies about 80% of the canvas as vast calm field. Pale cool primary `#DBEAFE` appears as soft restrained structure (about 12%). Accent steel blue `#3B82F6` appears as one small deliberate focal element (about 5%). No warm tones, no saturated colors. The vast field is the identity — most of the canvas is breathing room."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ digital-dashboard | Clean clinical UI — natural pairing |
| ✓✓ vector-illustration | Light vector with cool restraint |
| ✓✓ flat | Pale flat geometric |
| ✓✓ minimalist-swiss | Field-and-grid pairing |
| ✓✓ glassmorphism | Soft polished cool aesthetic |
| ✓ corporate-photo | Photography with cool clinical grading (medical, beauty, spa) |
| ✓ blueprint | Pale schematic |
| ✗ sketch-notes / chalkboard / fantasy-animation / pixel-art | Wrong temperament — those are warm |
| ✗ dark-cinematic combinations | Dark mood is opposite of frost identity |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a vector-illustration health/spa hero**

> [...rendering paragraph...] Color behavior is frost-ice: secondary near-white `#F8FBFD` occupies about 80% of the canvas as vast calm field. A single soft pale cool primary `#DBEAFE` rounded shape appears in the lower third (about 12%). Accent steel blue `#3B82F6` appears as one small deliberate dot or thin line at a rule-of-thirds intersection (about 5%). No warm tones, no saturated colors. Maximum breathing room. [...container guidance...]

**Snippet B — applied to a glassmorphism SaaS product showcase**

> [...rendering paragraph...] Color behavior is frost-ice: near-white field `#F8FBFD` dominates (about 78%). The single frosted-glass panel uses a pale cool primary `#DBEAFE` tint at 50% opacity (about 14%). One small accent steel blue `#3B82F6` indicator inside the panel marks the focal data point (about 5%). Soft cool gradient background blurs through. The vast calm field outside the panel is the identity — premium-minimal clinical clean. [...container guidance...]

---

## 7. Forbidden

- Saturated or warm colors anywhere (defeats frost identity)
- Field below 70% of canvas
- Multiple accent points (frost-ice allows exactly one focal moment)
- Heavy outlines or dark text (visible inside the image — SVG text overlay handles labels)
- Texture or noise (frost-ice is polished and clean, never tactile)

---

## 8. When to switch away

- For warmth → `warm-earth` or `macaron`
- For corporate confidence with deeper primary → `cool-corporate`
- For atmospheric premium → `dark-cinematic`
- For methodology / mindset → `mono-ink`
