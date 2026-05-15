# Palette: mono-ink

High-contrast monochrome with sparse semantic accents. The most disciplined palette — used for methodology, manifestos, Before-After essays, mindset-shift narratives, professional visual-notes. Distinguished by **black ink on white**, with the deck's accent reserved for semantic meaning only.

> This file describes **color behavior**, not HEX values. mono-ink overrides much of the deck's HEX usage — read carefully.

## 1. Special: deviates from deck HEX

mono-ink is the palette **most likely to override `design_spec.colors`**:

- The deck's `primary` HEX is typically **not used** as ink color (mono-ink ink is always near-black, not the deck's brand color)
- The deck's `secondary` HEX is typically **not used** as background (mono-ink background is always pure white)
- The deck's `accent` HEX **is used** — but only in the semantic accent role, with strict <10% area constraint

When proposing mono-ink, the assembled prompt should explicitly note: "mono-ink palette intentionally uses near-black on white as the structural language; the deck's primary `#XXX` and secondary `#XXX` are not represented as image colors. The deck's accent `#XXX` is reserved for the semantic emphasis role under 10% of canvas."

## 2. Compatible renderings

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

## 3. Fewshot prompt snippets

**Snippet A — applied to an ink-notes Before/After comparison**

> [...rendering paragraph...] Color behavior is mono-ink with semantic accents: pure white background `#FFFFFF` (about 55%); all line work, figures, and hand-lettered text in near-black ink `#1A1A1A` (about 38%). Left "Before" side carries coral red accent `#E8655A` on its pain-point markers only (about 4% of total canvas). Right "After" side carries muted teal `#5FA8A8` on solution markers only (about 3%). Total color accent stays under 8%. Deck's primary `#1E3A5F` and secondary `#F8F9FA` are intentionally not used here — mono-ink's discipline is the visual point. [...container guidance...]