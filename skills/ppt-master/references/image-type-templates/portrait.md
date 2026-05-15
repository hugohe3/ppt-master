# Type: portrait

A **single person headshot or upper-body shot** — frontal or three-quarter turn, neutral or minimal background, the face as the visual anchor. Used for team pages, speaker bios, founder profiles, testimonial pages, "about us" sections, executive introductions.

> **What portrait means inside a PPT block**: **one person, face-forward, isolated from environment**. Unlike `scene` (atmospheric environment with narrative), portrait strips away context to focus on the person. Unlike `hero` (any singular subject — product / object / person), portrait is specifically **human face / upper body**.

---

## 1. Composition skeleton

```
   ┌────────────────────────────────────┐
   │                                     │
   │            ┌─────────┐              │
   │            │  Head   │              │
   │            │  / Face │              │
   │            ├─────────┤              │
   │            │ Shoulders│              │
   │            │  / Torso │              │
   │            └─────────┘              │
   │                                     │
   │      Subject occupies 50-65% of     │
   │      canvas height, centered        │
   └────────────────────────────────────┘
```

| LAYOUT | Single person centered (or rule-of-thirds offset); head occupies upper third, torso/shoulders the middle. Background is neutral, minimal, or softly blurred. |
| ELEMENTS | The person (face + upper body) + minimal background context (a soft color field, a gentle gradient, an out-of-focus environment cue). No competing foreground objects. |
| NEGATIVE SPACE | Generous around the head — at least 15% padding above the crown of the head |
| BALANCE | The face is the visual anchor; eyes positioned at approximately the upper-third horizontal line (classical portrait rule) |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Team-page headshot | 400×500 | 4:5 | 10% (portrait crops tight to subject) |
| Square avatar | 600×600 | 1:1 | 10% |
| Half-page founder bio | 600×800 | 3:4 | 10% |
| Hero speaker introduction | 1200×720 | ~5:3 | 12% (more breathing on hero) |

---

## 3. Text-policy variants

### 3.1 `text_policy: none` (default)

Names, titles, and quotes are added later as SVG overlay. The portrait shows the person only.

Sample fragment:

> NO text, letters, numbers, name tags, or captions in the image. The portrait is the person only; SVG text overlay will add name, title, and any quote externally.

### 3.2 `text_policy: embedded` is essentially never used for this type — switch to `hero` or `typography` if text is required as part of the image.

---

## 4. Fewshot prompt snippets

**Snippet A — corporate-photo + cool-corporate executive headshot, text_policy: none, 600×800**

> Editorial corporate portrait photograph of one professional executive. The person is centered slightly left of canvas center, photographed from chest-up at eye level, looking confidently toward the camera with a relaxed natural expression — not posed-stiff, not over-smiling. Professionally attired in a contemporary business setting (a tailored blazer, neutral palette clothing). Soft natural light from the upper left, gentle shadow on the right side of the face. Diverse, professionally attired subject, photorealistically rendered, contemporary styling. Background is a softly out-of-focus office context — secondary light gray `#F8F9FA` wall with a subtle hint of primary deep navy `#1E3A5F` in a blurred architectural element. Color grading is cool-corporate — restrained, professional. Shallow depth of field — subject sharp, background gently blurred. Subject's eyes positioned at the upper-third horizontal line. Composed as a 600×800 half-page bio portrait with 10% padding. NO text, name tags, or captions in the image. Color values are rendering guidance only.

**Snippet B — corporate-photo + warm-earth founder portrait, text_policy: none, 400×500**

> Editorial corporate portrait of one entrepreneurial founder. Photographed from head-and-shoulders at eye level in a workspace context. Subject is centered, looking thoughtfully off-camera at a slight three-quarter turn — natural, contemplative expression suggesting reflection. Diverse, contemporary styling — casual but considered (a knit sweater, simple jewelry). Warm window light from the upper right creates golden-amber highlights on the cheek and shoulder. Color grading is warm-earth — image graded toward warm amber `#9A3412` shadows and cream `#FEF3C7` highlights, with a small detail of accent gold `#D4AF37` in the background (a hint of warm wood). Background is gently blurred contextual workspace. Shallow depth of field. Composed as a 400×500 team-page headshot with 10% padding. Diverse, professionally attired subject rendered photorealistically — no posed stock-photo stiffness. NO text or captions. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Multiple people in frame | "Single person" rule weak | Strengthen with "exactly ONE person, no other people visible in the frame" |
| Background competing with subject | Background rule omitted | "Background softly blurred or neutral solid field — no competing foreground elements" |
| Stock-photo stiffness | Naturalness rule omitted | Reaffirm "natural relaxed expression — not posed-stiff, not over-smiling, not stock-photo artificial" |
| Subject cropped at face / head touching edge | Padding rule omitted | "At least 15% padding above the crown of the head — head must not touch upper edge" |
| Subject's eyes too low in frame | Eye-position rule omitted | "Eyes positioned at approximately the upper-third horizontal line" |
| Specific celebrity / public-figure likeness | §5.4 omitted | Strengthen with "no celebrity or public-figure likeness — generic professional subject" |
| Homogeneous casting | Diversity rule omitted | Reaffirm "diverse, contemporary styling — vary age, ethnicity, gender across multiple portraits in the same deck" |

---

## 6. When to switch away from portrait

- If multiple people in environment → `scene`
- If non-human subject is the focal element → `hero`
- If subject is a product (no person) → `hero` or `infographic`
- If full-body lifestyle / case-study narrative → `scene`
- If the image is just an avatar icon (stylized, not photographic) → consider `typography` (initial-letter avatar) or a vector-illustration hero
