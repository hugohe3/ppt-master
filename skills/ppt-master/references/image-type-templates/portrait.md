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

## 2. Text-policy variants

### 3.1 `text_policy: none`

The portrait shows the person only; names, titles, and quotes are handled in SVG.

Sample fragment:

> NO text, letters, numbers, name tags, or captions in the image. The portrait is the person only.

### 3.2 `text_policy: embedded`

If text is part of the page's visual (a name carved as a design element, a quote alongside the figure), the type is likely `hero` or `typography` rather than `portrait`.

---

## 3. Fewshot prompt snippets

**Snippet A — corporate-photo + cool-corporate executive headshot, text_policy: none, 600×800**

> Editorial corporate portrait photograph of one professional executive. The person is centered slightly left of canvas center, photographed from chest-up at eye level, looking confidently toward the camera with a relaxed natural expression — not posed-stiff, not over-smiling. Professionally attired in a contemporary business setting (a tailored blazer, neutral palette clothing). Soft natural light from the upper left, gentle shadow on the right side of the face. Diverse, professionally attired subject, photorealistically rendered, contemporary styling. Background is a softly out-of-focus office context — secondary light gray `#F8F9FA` wall with a subtle hint of primary deep navy `#1E3A5F` in a blurred architectural element. Color grading is cool-corporate — restrained, professional. Shallow depth of field — subject sharp, background gently blurred. Subject's eyes positioned at the upper-third horizontal line. Composed as a 600×800 half-page bio portrait with 10% padding. NO text, name tags, or captions in the image. Color values are rendering guidance only.