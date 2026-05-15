# Palette: jewel-tone

Deep saturated gemstone colors — emerald, sapphire, ruby, amethyst, gold. Premium, luxurious, evening-elegant. Used for luxury / fashion / jewelry / premium product / evening events / heritage brands where richness is the visual signal.

> This file describes **color behavior**, not HEX values. The deck's HEX triplet comes from `design_spec.colors`. jewel-tone tells the model how to apply those HEX values with **jewel-rich saturation discipline**.

---

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | High — gemstone richness; never washed-out |
| Brightness contrast | Strong — deep jewels against dark or cream field |
| Color count visible | 2-3 (one or two jewel colors + neutral field + small gold/silver accent) |
| Mood | Premium, luxurious, sophisticated, evening-elegant |
| Material | Velvet / silk / polished gemstone — implied richness, never plastic |

---

## 2. Proportion rule (50-35-15, jewel-rich)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Field / background | **45-55%** | `secondary` (often deep cream, dark navy, or near-black) | Sets the velvet stage for the jewels |
| Primary jewel | **30-40%** | `primary` (one rich jewel — emerald, sapphire, ruby, amethyst) | The dominant gemstone color |
| Accent (gold / silver / second jewel) | **10-15%** | `accent` | A metallic gold or a small second-jewel pop |

> **Hard rule**: jewel-tone requires **high saturation** in `primary`. If the deck's primary HEX is muted, push toward its richest neighbor when describing it ("rich deep emerald `#047857`" not "muted teal").

---

## 3. Role semantics

- **Primary jewel** carries the luxury statement — used in large confident blocks, never as tints or backgrounds
- **Secondary field** is the velvet stage — cream, near-black, or deep neutral that lets the jewel sing
- **Accent** is the metallic highlight — gold leaf, silver thread, polished brass — small but bright

---

## 4. How to phrase it in a prompt

> "Color behavior is jewel-tone: rich primary deep emerald `#047857` carries the dominant gemstone block (about 35%); secondary deep cream `#FEF3C7` forms the velvet field (about 50%); accent gold `#D4AF37` appears as a thin polished metallic line or one small jewel-cut shape (about 12%). High saturation, premium feel. No muted tints. No additional colors."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ editorial | Magazine luxury — natural pairing |
| ✓✓ corporate-photo | High-end product/lifestyle photography graded toward jewel tones |
| ✓✓ dark-cinematic combinations are handled by `dark-cinematic` palette; jewel-tone is the *richer alternative* — use jewel-tone when you want saturation, dark-cinematic when you want atmospheric |
| ✓ flat | Bold flat jewel blocks |
| ✓ vector-illustration | Acceptable but loses material implication |
| ✓ screen-print | Limited-color poster luxury |
| ✗ sketch-notes / chalkboard / pixel-art / fantasy-animation | Wrong temperament |
| ✗ digital-dashboard | Data UI conflicts with luxury |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to an editorial luxury hero**

> [...rendering paragraph...] Color behavior is jewel-tone: rich primary deep emerald `#047857` forms a confident block across the lower 40% of the canvas with high saturation. Secondary deep cream `#FEF3C7` carries the upper 48% as velvet field. Accent gold `#D4AF37` appears as a single thin metallic horizontal line at the meeting point and one small polished gold dot in the upper right (totaling about 10%). No muted tints. No additional colors. Premium evening feel. [...container guidance...]

**Snippet B — applied to a corporate-photo lifestyle product**

> [...rendering paragraph...] Color grading is jewel-tone: image is graded toward rich primary ruby `#9A1B3A` as the dominant shadow tone, secondary deep cream `#FEF3C7` carries the highlight regions, and accent gold `#D4AF37` appears as warm metallic surfaces (a polished frame, a brass detail). The overall feel is high-saturation premium evening — no faded or washed-out tones. Like a contemporary luxury campaign shot. [...container guidance...]

---

## 7. Forbidden

- Muted / washed-out / pastel tints (defeats jewel saturation — switch to `editorial-classic` or `warm-earth`)
- Equal-share three-jewel palette (becomes a flag — keep one dominant jewel)
- More than one metallic accent
- Plastic or matte material feel (jewel-tone implies polished material)
- Heavy black outlines (jewel-tone is fill-based, not line-based)

---

## 8. When to switch away

- For atmospheric premium without saturation → `dark-cinematic`
- For restrained corporate luxury → `editorial-classic`
- For warm friendly brand → `warm-earth`
- For methodology / mindset → `mono-ink`
