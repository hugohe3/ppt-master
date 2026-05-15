# Palettes — Index

A **palette** is the deck's **color behavior** — proportion, role, temperament. It does **not** supply HEX values; those come from `design_spec.colors`. The palette tells the model how to use the HEX values: which dominates, which carries accent, what proportion the background occupies, what the overall temperament feels like.

> Why this split: SVG renders the HEX precisely from `design_spec`. The AI image must use the **same HEX values** so the image visually belongs in the deck — but the image needs more than a HEX list; it needs a **usage rule**. That's the palette.

---

## 1. Catalog (10 palettes)

Each palette has its own file with: proportion rules, role assignments, temperament, fewshot snippets, what to avoid.

| Palette | Temperament | Best for |
|---|---|---|
| [`cool-corporate`](./cool-corporate.md) | Stable, professional, restrained | Consulting / B2B / finance |
| [`warm-earth`](./warm-earth.md) | Friendly, grounded, human | Brand / lifestyle / education |
| [`tech-neon`](./tech-neon.md) | Energetic, futuristic, high-contrast | AI / SaaS / product launch |
| [`editorial-classic`](./editorial-classic.md) | Refined, magazine, balanced | Journalism / opinion / culture |
| [`macaron`](./macaron.md) | Soft pastel, gentle, approachable | Education / children / onboarding |
| [`mono-ink`](./mono-ink.md) | High-contrast monochrome with sparse accents | Methodology / Before-After / manifesto |
| [`vivid-launch`](./vivid-launch.md) | Bold, saturated, attention-grabbing | Product launch / marketing / event |
| [`dark-cinematic`](./dark-cinematic.md) | Premium, atmospheric, low-light | Premium product / film / entertainment |
| [`duotone`](./duotone.md) | Two-color limited, poster-like | Cultural / cover hero / cinematic |
| [`nature-organic`](./nature-organic.md) | Earthy, natural, wellness | Environment / wellness / outdoor |

---

## 2. Auto-selection table — `design_spec` → palette

Match `design_spec.md d. Style` + `e. Color Scheme` content vibe. First match wins. If no row matches, default to `cool-corporate`.

| Content vibe / industry | Recommended palette | Alternates |
|---|---|---|
| Consulting / finance / B2B / corporate | `cool-corporate` | `editorial-classic` |
| Tech / SaaS / AI | `tech-neon` | `cool-corporate`, `dark-cinematic` |
| Education / training / onboarding | `macaron` | `warm-earth` |
| Methodology / Before-After / mindset shift | `mono-ink` | `editorial-classic` |
| Personal / lifestyle / brand story | `warm-earth` | `nature-organic` |
| Product launch / marketing / event | `vivid-launch` | `tech-neon` |
| Children / storybook | `macaron` | `warm-earth` |
| Premium / entertainment / film | `dark-cinematic` | `duotone` |
| Cultural / media / cover-art | `duotone` | `editorial-classic` |
| Environment / wellness / outdoor | `nature-organic` | `warm-earth` |
| Finance / journalism / explainer | `editorial-classic` | `cool-corporate` |
| Government / formal | `cool-corporate` | `editorial-classic` |

---

## 3. Rendering × Palette compatibility

Some combinations clash. Use this matrix as a sanity check after auto-selection.

| | cool-corp | warm-earth | tech-neon | editorial | macaron | mono-ink | vivid-launch | dark-cinem | duotone | nature-org |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| vector-illustration | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ |
| flat | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ |
| 3d-isometric | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✗ | ✓✓ | ✓✓ | ✗ | ✓ |
| digital-dashboard | ✓✓ | ✗ | ✓✓ | ✓✓ | ✗ | ✓ | ✓ | ✓✓ | ✗ | ✗ |
| corporate-photo | ✓✓ | ✓✓ | ✓ | ✓✓ | ✗ | ✗ | ✓ | ✓✓ | ✗ | ✓✓ |
| blueprint | ✓✓ | ✗ | ✓✓ | ✓ | ✗ | ✓✓ | ✗ | ✓✓ | ✓ | ✗ |
| editorial | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ |
| sketch-notes | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✓ | ✓ | ✗ | ✗ | ✓✓ |
| ink-notes | ✓ | ✓ | ✗ | ✓✓ | ✗ | ✓✓ | ✗ | ✗ | ✓ | ✗ |
| chalkboard | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✓✓ | ✓ | ✓ |
| watercolor | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓✓ |
| warm-scene | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓✓ | ✓ | ✓✓ |
| screen-print | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓✓ | ✓✓ | ✓ |
| fantasy-animation | ✗ | ✓✓ | ✗ | ✗ | ✓✓ | ✗ | ✓ | ✗ | ✗ | ✓✓ |
| pixel-art | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✗ |
| nature | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓✓ |

✓✓ recommended | ✓ acceptable | ✗ avoid

---

## 4. How to use

1. After picking rendering, look up your candidate palette in the auto-selection table.
2. Cross-check the compatibility matrix — if `✗`, pick the alternate.
3. `read_file image-palettes/<chosen>.md`.
4. Apply its proportion + role rules to the deck's HEX values when assembling prompts.

**Lock for the whole deck.**
