# Palette: cool-corporate

Stable, professional, restrained. The default palette for consulting / finance / B2B / corporate decks where credibility is the primary visual signal.

> This file describes **color behavior**, not HEX values. The deck's HEX triplet comes from `design_spec.colors` (set by Strategist). cool-corporate tells the model **how to use** those HEX values.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Restrained — let the primary blue feel deep but not vivid |
| Brightness contrast | Strong (deep primary against bright secondary) — supports executive readability |
| Color count visible | 3 maximum (primary + secondary + accent); no fourth color creeps in |
| Mood | Confident, calm, deliberate, slightly serious |
| Material | Flat — no glossy, no metallic, no plastic |

---

## 2. Proportion rule (60-30-10, applied to the deck's HEX)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / negative space | **60-70%** | `secondary` | Calm field. Usually pale (gray, off-white, very light blue). Carries the page's breathing room. |
| Main subject / dominant shape | **25-30%** | `primary` | The deep blue / navy / dark teal that anchors the image. Used in confident solid blocks, not as a tint. |
| Emphasis / call-attention | **3-7%** | `accent` | One or two elements only — a single highlighted node, a thin key line, an emphasized icon stroke. Never more than 5-7% of the canvas. |

> **Hard rule**: if accent exceeds ~7%, the deck loses its corporate temperament and starts to feel promotional. When in doubt, reduce accent presence.

---

## 3. Role semantics

- **Primary** carries trust, structure, the spine of the visual. Use it for: dominant forms, vertical/horizontal anchor lines, key icon fills, foundational geometry.
- **Secondary** carries breathing space. Use it for: backgrounds, gutters, secondary blocks, subtle dividers. It should feel **almost invisible** in a good cool-corporate image.
- **Accent** carries direction — it tells the viewer's eye where to land. Use it for: the single most important data point, the chosen "this is the conclusion" element, a thin accent line under a key area.

---

## 4. How to phrase it in a prompt

Combine the proportion rule + role semantics + the deck's actual HEX:

> "Color behavior is restrained-corporate: secondary `#F8F9FA` occupies 60-70% of the canvas as calm background; primary `#1E3A5F` carries the main shape and dominant elements; accent `#D4AF37` appears only in one or two emphasis points totaling under 5% of the area. No fourth color. Flat solid fills only — no gradients, no metallic, no glossy reflections."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ vector-illustration | Default pairing — flat shapes carry the restraint |
| ✓✓ flat | Similar feel, slightly more decorative |
| ✓✓ 3d-isometric | Works well — keep shadows soft and 8% opacity |
| ✓✓ digital-dashboard | Natural fit for data products |
| ✓✓ blueprint | Good for technical architecture |
| ✓✓ corporate-photo | Photography with cool color grading |
| ✓✓ editorial | Magazine restraint matches palette restraint |
| ✗ sketch-notes / fantasy-animation / pixel-art | Temperament conflict — choose `warm-earth` or `macaron` for those renderings |
| ✗ dark-cinematic combinations | Dark-cinematic is a different palette — don't try to merge |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a vector-illustration background**

> [...rendering paragraph...] Color behavior is restrained-corporate: secondary light gray `#F8F9FA` carries 65% of the canvas as calm breathing space across the upper two-thirds; primary deep navy `#1E3A5F` forms a confident diagonal block across the lower portion (about 28% area); accent gold `#D4AF37` appears only as one thin horizontal line and a single small geometric dot, together under 5% of the area. No additional colors. [...container guidance...]

**Snippet B — applied to a digital-dashboard product showcase**

> [...rendering paragraph...] Color behavior is restrained-corporate dashboard: secondary `#F8F9FA` dominates the canvas as the UI surface (about 70%); primary `#1E3A5F` carries the main data chart's bars and the dominant card header (25%); accent `#D4AF37` is reserved for one highlighted metric — a single arrow indicator or one emphasized data point — totaling under 5% of the area. Soft 8% drop shadows under cards. No gradients within fills. [...container guidance...]

---

## 7. Forbidden

- **Vibrant accent**: accent in cool-corporate is structurally a small percentage, not a bright burst. If the HEX `accent` is itself highly saturated (e.g. neon yellow), reduce its area further — never increase it.
- **Equal-share triplet**: when all three colors appear in roughly equal area, the image looks like a children's flag, not a corporate visual. Force the 60-30-10 split.
- **Fourth color**: don't let the model introduce a green, a pink, or a darker complement. Reaffirm the three HEX values 2-3 times in the prompt.
- **Bright background**: secondary should be near-white, not the primary brand color. cool-corporate's breathing room is what makes it corporate.
- **Metallic / glossy**: cool-corporate is flat. Switch palette to `dark-cinematic` if a premium glossy treatment is wanted.

---

## 8. When to switch away from cool-corporate

- If the deck is **warm / personal / brand-storytelling**, switch to `warm-earth` or `editorial-classic`
- If the deck is **AI / SaaS / energetic tech**, `tech-neon` carries more presence
- If the deck is **methodology / mindset shift**, `mono-ink` is sharper
- If the deck is **education / approachable**, `macaron` is softer
