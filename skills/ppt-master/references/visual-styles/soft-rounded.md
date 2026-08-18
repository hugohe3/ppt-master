# Visual style: soft-rounded

Approachable and modern. Rounded cards, gentle elevation, friendly rhythm. For product, SaaS, training, consumer decks.

---

## 1. Shape & decoration

- Shape language: visibly rounded rectangles, pill tags, and soft containers. Keep the radius family coherent deck-wide.
- Composition geometry: a large soft disc or blob bleeding off one edge as the color field; a pill chain or exact native `arc` / `blockArc` preset replacing the boxed step row; one hero panel overlapping a full-width tinted band; an oversized rounded numeral behind the point. Use a custom arc path only when the presets cannot faithfully express the intended contour. Cards are the container language, not the composition — vary the stage they sit on.
- Decoration: cards as the primary container; icon accents; numbered circles; gentle dividers. Moderate, in service of clarity.
- Whitespace: comfortable padding inside cards; even gutters; balanced rather than austere.

## 2. Typography character

- Friendly sans (humanist or geometric); medium weights; clear but not severe hierarchy.
- Rounded, open letterforms suit; avoid condensed / industrial faces.

> Families are chosen at confirmation `g`; this style asks for an approachable sans *character*. This governs editable native text; decorative-lettering eligibility remains a separate carrier decision.

## 3. Using the deck's colors

- Theme color used confidently on covers / chapter backgrounds; same-hue tints for card backings; accent for key figures.
- Warmer, more generous color use than swiss / editorial. Assign hues by semantic role and visual hierarchy; intentional multi-hue compositions remain valid.

> HEX values come from confirmation `e`; this style governs confident, friendly color use without naming colors or imposing a ratio.

## 4. Texture / elevation

- Gentle elevation: soft shadows on floating cards, subtle tints, and optional same-hue gradients. Keep the elevation hierarchy shallow and coherent; peer-grid cards stay flat.

## 5. Paired image-rendering

`flat` — clean modern blocks for AI images. (For frosted-glass depth, see the dedicated [`glassmorphism`](./glassmorphism.md) style.)

## 6. Illustration propensity

**supportive** — friendly rounded illustration elements can carry anchors, support, rhythm, or warmth across the page system. With no user steer this is the default lean; role, scale, reuse, and placement stay Strategist judgment, an explicit user request wins either way, and `image_usage: none` writes no illustration rows.
