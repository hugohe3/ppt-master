# Visual style: photo-editorial

Photo-led editorial — large full-bleed photography dominates the page, text points and captions. The big image speaks; words title it. Magazine photo-essay rhythm. For architecture, design, fashion, culture, photography-forward long-reads.

---

## 1. Shape & decoration

- Shape language: large full-bleed / edge-to-edge image fields are the page's spine; text sits in restrained columns, caption blocks, kickers, or overlay headlines. Minimal chrome — the photograph carries the page.
- Composition geometry: an L-shaped text zone carved out of the full bleed; a headline straddling the photo edge; a diptych / triptych panel split; one floating caption card breaking the image boundary — moves that serve the photograph, never bury it.
- Decoration: thin rules, section numbering, small figure notes; nothing competes with the image.
- Whitespace: generous around text; the photo fills, the type breathes beside it. Asymmetric magazine composition.

> **No usable image → fall back to `editorial`.** This style's spine is the photograph; when a page has no suitable image available, render it in the `editorial` text-led layout (magazine columns) rather than a full-bleed placeholder — an empty / dashed image frame contradicts the style's whole premise. A deterministic, observable condition, not a judgment call.

## 2. Typography character

- Editorial serif / CJK title × clean sans body; magazine-column cadence; small precise captions and figure notes. Words are concise — they point, they don't fill.

> Families are chosen at confirmation `g`; this style asks for an editorial serif-title × clean-sans-body *character*.

## 3. Using the deck's colors

- The photograph carries the color; the text-side field stays a quiet neutral so imagery dominates; one restrained accent marks numbering, rules, or a key word.
- Deliberately understated on the type side — the image is the loudest element, by design.

> HEX values come from confirmation `e`; this style only governs the image-dominant, understated-type discipline — it names no colors.

## 4. Texture / elevation

- Flat — no decorative shadows. The one practical exception: a scrim gradient over an image where overlay text needs legibility. Photography supplies the texture.

## 5. Paired image-rendering

`corporate-photo` — real editorial photography as the hero imagery the layout is built around.

## 6. Illustration propensity

**sparse** — photography *is* the visual; illustration competes with the hero image. With no user steer, default to none. If the user explicitly asks, keep them to tiny captional marks that never rival the photo. `image_usage: none` writes no illustration rows.
