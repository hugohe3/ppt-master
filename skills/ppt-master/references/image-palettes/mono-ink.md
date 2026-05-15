# Palette: mono-ink

High-contrast monochrome with sparse semantic accents. The most disciplined palette — used for methodology, manifestos, Before-After essays, mindset-shift narratives, professional visual-notes. Distinguished by **black ink on white**, with the deck's accent reserved for semantic meaning only.

> This file describes **color behavior**, not HEX values. mono-ink overrides much of the deck's HEX usage — read carefully.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Extreme contrast (black + white) + low saturation for accents |
| Brightness contrast | Maximum — pure black on pure white |
| Color count visible | Ink (black) + 1-2 semantic accents, total under 10% color area |
| Mood | Professional, manifesto, disciplined, considered |
| Material | Ink on paper |

---

## 2. Proportion rule (90/10 ink + sparse accent)

| Role | Share | Source | Behavior |
|---|---|---|---|
| Background | **~50-60%** | Pure white `#FFFFFF` | Never replace with deck's secondary; the white is essential to mono-ink identity |
| Ink (lines, fills, text, figures) | **~30-40%** | Near-black `#1A1A1A` | All structural elements; never replaced by deck's primary |
| Semantic accent #1 (e.g. emphasis / risk) | **3-7%** | Maps from `design_spec.accent` if that HEX is in a warm/red family | Reserved for: risks, emphasis points, "this matters" markers. Often coral red `#E8655A` traditionally. |
| Semantic accent #2 (e.g. positive / solution) | **2-5%** | Optional second accent, often muted teal `#5FA8A8` | Reserved for: positive states, solution markers, "after" side of Before-After. |

> **Total color accent must stay under 10% of canvas** — this is what makes mono-ink "mono".

---

## 3. Special: deviates from deck HEX

mono-ink is the palette **most likely to override `design_spec.colors`**:

- The deck's `primary` HEX is typically **not used** as ink color (mono-ink ink is always near-black, not the deck's brand color)
- The deck's `secondary` HEX is typically **not used** as background (mono-ink background is always pure white)
- The deck's `accent` HEX **is used** — but only in the semantic accent role, with strict <10% area constraint

When proposing mono-ink, the assembled prompt should explicitly note: "mono-ink palette intentionally uses near-black on white as the structural language; the deck's primary `#XXX` and secondary `#XXX` are not represented as image colors. The deck's accent `#XXX` is reserved for the semantic emphasis role under 10% of canvas."

---

## 4. How to phrase it in a prompt

> "Color behavior is mono-ink: pure white background `#FFFFFF` (about 55%). All structural elements — lines, figures, hand-lettered text, arrows — in near-black ink `#1A1A1A` (about 38%). The deck's accent color `#E8655A` is reserved as the semantic emphasis accent, appearing in 1-3 small focal points totaling under 8% of canvas. No other colors. The deck's primary and secondary HEX values are intentionally not represented as image colors in this palette."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ ink-notes | Direct alignment — mono-ink is the default ink-notes palette |
| ✓✓ editorial | Magazine restraint + ink discipline |
| ✓ vector-illustration | Acceptable but loses the hand-drawn quality |
| ✓ blueprint | Schematic restraint |
| ✗ sketch-notes / watercolor / fantasy-animation / nature | Wrong temperament — those are warm |
| ✗ tech-neon / digital-dashboard | Mono-ink is intentionally non-digital |
| ✗ corporate-photo | Photography can't be mono-ink |
| ✗ chalkboard | Mono-ink is white-paper-black-ink; chalkboard is opposite |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to an ink-notes Before/After comparison**

> [...rendering paragraph...] Color behavior is mono-ink with semantic accents: pure white background `#FFFFFF` (about 55%); all line work, figures, and hand-lettered text in near-black ink `#1A1A1A` (about 38%). Left "Before" side carries coral red accent `#E8655A` on its pain-point markers only (about 4% of total canvas). Right "After" side carries muted teal `#5FA8A8` on solution markers only (about 3%). Total color accent stays under 8%. Deck's primary `#1E3A5F` and secondary `#F8F9FA` are intentionally not used here — mono-ink's discipline is the visual point. [...container guidance...]

**Snippet B — applied to an ink-notes framework diagram**

> [...rendering paragraph...] Color behavior is mono-ink: pure white background `#FFFFFF` (about 58%); central frame, sub-components, connector arrows, and stick-figure labels in near-black ink `#1A1A1A` (about 38%). The deck's accent `#D4AF37` appears only as a single thin emphasis ring around the central frame — about 4% of canvas. No other color. The deck's primary and secondary are not represented as image colors in this manifesto-style palette. [...container guidance...]

---

## 7. Forbidden

- Adding the deck's primary or secondary as image colors (defeats mono-ink discipline)
- Color accent exceeding 10% of canvas
- More than 2 semantic accent colors
- Cream or warm paper (that's `sketch-notes` / `warm-earth`, not mono-ink)
- Saturated digital feeling (mono-ink is paper-and-ink)

---

## 8. When to switch away

- For warm educational feel → `macaron` palette + `sketch-notes` rendering
- For broader color use → any other palette
- For digital aesthetic → `cool-corporate` or `tech-neon`
