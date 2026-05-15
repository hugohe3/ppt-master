# Palette: earthy-dusty

Muted desaturated earth tones — dusty pink, sage green, faded terracotta, muted ochre. Calm, sophisticated, refined-minimal — Morandi-adjacent. Used for lifestyle / interior design / wellness / mindfulness / slow living / contemporary minimal brand decks where understatement is the visual signal.

> This file describes **color behavior**, not HEX values. earthy-dusty tells the model how to apply the deck's HEX values **at reduced saturation** — every color appears slightly desaturated, even when the HEX itself is more vivid.

---

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Low — all colors are dusted, faded, never vivid |
| Brightness contrast | Soft — adjacent values, no harsh jumps |
| Color count visible | 3-4 (all muted; no single color dominates loudly) |
| Mood | Calm, refined, contemplative, slow, considered |
| Material | Linen / clay / faded paint / soft fabric — natural and aged |

---

## 2. Proportion rule (50-35-15, all-muted)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Field | **45-55%** | `secondary` rendered as muted neutral (warm gray, faded cream, dusty taupe) | Calm field — never pure white |
| Primary muted | **30-40%** | `primary` desaturated 20-40% from its source HEX | The dominant tone — still recognizable but dusted |
| Accent muted | **10-15%** | `accent` desaturated similarly | The "loudest" element, but loud is relative — even the accent is dusty |

> **Hard rule**: earthy-dusty applies a **uniform desaturation** to every color in the deck. Vivid HEX values get rendered as their dusted neighbors ("vivid coral `#FF6B6B` rendered as dusty rose `#D4A5A5`"). State this transformation in the prompt.

---

## 3. Role semantics

- **Field** is the calm neutral backdrop — warm gray, oat, dusted cream
- **Primary muted** carries gentle warmth — dusty rose, sage, faded clay
- **Accent muted** is the "loudest" element but stays within dusty register — never breaks the palette discipline
- All three colors should feel like they could share a room — no chromatic competition

---

## 4. How to phrase it in a prompt

> "Color behavior is earthy-dusty Morandi-adjacent: every color appears desaturated 25-35% from its source HEX. Secondary muted oat `#E8E0D5` (slightly dusted from cream) carries about 50% of the canvas as calm field. Primary muted dusty rose `#D4A5A5` (a desaturated translation of the deck's primary) carries the main shape at about 35%. Accent muted sage `#A8B5A0` (desaturated translation of the accent) appears in one or two small dusty highlights totaling about 12%. No vivid color anywhere — even the accent is dusted. Refined, contemplative, slow."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ watercolor | Watercolor's muted material aligns naturally |
| ✓✓ editorial | Magazine restraint pairs well with muted discipline |
| ✓✓ corporate-photo | Photography graded toward dusty / Morandi palette (lifestyle, interior, wellness) |
| ✓✓ flat | Muted flat geometric blocks |
| ✓✓ vector-illustration | Dusty vector restraint |
| ✓ paper-cut | Muted paper craft |
| ✓ warm-scene | Warm scene with dusted grading |
| ✗ tech-neon / vivid-launch / pixel-art / digital-dashboard | Wrong temperament — those rely on saturation |
| ✗ chalkboard | Wrong material |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to an editorial lifestyle spread**

> [...rendering paragraph...] Color behavior is earthy-dusty Morandi-adjacent: every color appears desaturated 30% from its source HEX. Secondary muted oat `#E8E0D5` carries the upper 60% of the canvas as calm field. Primary muted dusty terracotta `#C9A38C` (desaturated translation of the deck's primary) forms a confident block across the lower 30%. Accent muted sage `#A8B5A0` appears as one thin horizontal line near the meeting point and one small dusty dot in the upper right (totaling about 10%). No vivid color anywhere. Refined, contemplative. [...container guidance...]
