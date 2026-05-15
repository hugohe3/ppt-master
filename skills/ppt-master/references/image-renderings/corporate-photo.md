# Rendering: corporate-photo

Editorial photography style — real subjects, natural composition, professional grading. The only rendering where photorealism is intentional. Used for team photos, lifestyle shots, product photography, real-world scenarios.

## 1. Style paragraph (paste-ready, 100 words)

> Editorial photography style with natural composition and professional color grading. Subjects appear as real people, real products, real environments — captured with depth-of-field and intentional lighting. Composition follows photographic principles: rule of thirds, leading lines, deliberate foreground/background separation. Lighting is natural or studio-soft, never harsh. Color grading matches the deck's palette temperament — corporate decks lean cool and restrained, lifestyle decks lean warm and golden. Subjects in team or workplace contexts appear diverse and professionally attired. Background is contextual and slightly blurred to keep focus on the subject. Overall feel is authentic, premium, magazine-quality.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | N/A — photographic |
| Texture | Natural — skin, fabric, environment textures preserved |
| Depth | True depth-of-field — subject sharp, background subtly blurred |
| Material | Real-world physical materials, professionally lit |
| Mood | Authentic, premium, magazine-editorial |

---

## 3. Exception to global hard rule §5.2

corporate-photo **overrides** the global "simplified silhouettes / no realistic faces" rule (image-generator.md §5.2). For this rendering, append instead:

> Diverse, professionally attired subjects rendered photorealistically. Editorial photography composition, natural light or soft studio lighting. Subjects appear authentic and contemporary — no posed stock-photo stiffness, no exaggerated expressions, no fashion-shoot artificiality.

All other renderings keep the simplified-figure rule.

---

## 4. Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page lifestyle shot | 600×800 | 3:4 | 8% (photography fills the frame more) |
| Hero team photo | 1200×600 | 2:1 | 8% |
| Spot portrait | 400×500 | 4:5 | 8% |
| Full-bleed product hero | 1280×720 | 16:9 | 8% |

---

## 5. Using the deck's HEX values

corporate-photo's relationship to HEX is **color grading**, not color fills:

- Primary HEX: dominant tone the image is graded toward (cool grade for navy primary, warm grade for terracotta primary)
- Secondary HEX: highlight tone in the lit areas
- Accent HEX: a subtle environment color (a sweater, a wall accent, a product detail) that picks up the deck's accent
- HEX values appear as **color cues** in the description, not as literal HEX strings in the image

---

## 6. Fewshot prompt snippets

**Snippet A — team workplace photo, text_policy: none**

> Editorial photography of a small modern team collaborating around a laptop in a contemporary office. Three to four diverse, professionally attired adults — varied ethnicities, varied ages — engaged in genuine conversation, no posed stock-photo stiffness. Natural window light from the side, soft shadows. Color grading is cool-corporate — image is subtly graded toward deep blue tones echoing the deck's primary `#1E3A5F`, with the background carrying soft light gray `#F8F9FA` walls and a single accent of warm wood or amber from a desk lamp echoing the accent `#D4AF37`. Shallow depth of field — subjects sharp, background gently blurred. Composed as a 1200×600 hero band with 8% inner padding. Diverse, professionally attired subjects rendered photorealistically. Editorial photography composition. Authentic, not stock-photo artificial. Color values are rendering guidance — HEX codes themselves do not appear in the image as text.

**Snippet B — product lifestyle photo, text_policy: none**

> Editorial product photography of a sleek consumer device on a contemporary desk. Soft natural light from the upper left, gentle shadow cast to the lower right. Wood desk surface in warm beige tones, with a notebook and a cup of coffee in supporting context — slightly out of focus to keep attention on the device. Color grading is warm-editorial — image leans toward soft amber and cream, with the device itself catching a subtle highlight of accent terracotta `#C2410C`. Background wall in calm secondary cream `#FEF3C7`, gently blurred. Shallow depth of field. Composed as a 600×800 half-page block with 8% inner padding. Photorealistic, magazine-editorial quality. Color values are rendering guidance only.

---

## 7. Forbidden

- Stock-photo stiffness (forced smiles, frozen handshakes, fake-laughing meetings)
- Fashion-shoot artificiality (over-styled, over-lit, model-pose)
- Specific celebrity / public figure likenesses
- Visible brand logos on products unless explicitly intended
- Overly homogeneous casting (all same age, ethnicity, gender)

---

## 8. When to switch away

- For abstract / concept work → `vector-illustration`, `flat`, or `3d-isometric`
- For atmospheric narrative scenes (not photography) → `warm-scene` or `watercolor`
- For technical / system visuals → `blueprint` or `3d-isometric`
