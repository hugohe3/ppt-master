# Palettes — Index

A **palette** is the deck's **color behavior** — proportion, role, temperament. It does **not** supply HEX values; those come from `design_spec.colors`. The palette tells the model how to use the HEX values: which dominates, which carries accent, what proportion the background occupies, what the overall temperament feels like.

> Why this split: SVG renders the HEX precisely from `design_spec`. The AI image must use the **same HEX values** so the image visually belongs in the deck — but the image needs more than a HEX list; it needs a **usage rule**. That's the palette.

---

## 1. Catalog (14 palettes)

Each palette has its own file with: rendering compatibility matrix and a fewshot prompt snippet.

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
| [`jewel-tone`](./jewel-tone.md) | Deep saturated gemstone — emerald/sapphire/ruby + gold | Luxury / fashion / premium product / heritage |
| [`frost-ice`](./frost-ice.md) | Near-white field with pale cool accents | Health / medical / beauty / premium SaaS |
| [`sunset-gradient`](./sunset-gradient.md) | Warm gradient flow (pink → orange → purple) | Lifestyle / creative / travel / event |
| [`earthy-dusty`](./earthy-dusty.md) | Muted desaturated earth tones, Morandi-adjacent | Interior / wellness / mindfulness / slow living |

---

## 2. Auto-selection table — `design_spec` → palette

Match `design_spec.md d. Style` + `e. Color Scheme` content vibe. First match wins. If no row matches, default to `cool-corporate`.

| Content vibe / industry | Recommended palette | Alternates |
|---|---|---|
| Consulting / finance / B2B / corporate | `cool-corporate` | `editorial-classic`, `frost-ice` |
| Tech / SaaS / AI | `tech-neon` | `cool-corporate`, `dark-cinematic` |
| Modern SaaS / fintech / health-tech | `frost-ice` | `cool-corporate`, `tech-neon` |
| Health / medical / beauty / skincare | `frost-ice` | `nature-organic`, `earthy-dusty` |
| Education / training / onboarding | `macaron` | `warm-earth` |
| Methodology / Before-After / mindset shift | `mono-ink` | `editorial-classic` |
| Personal / lifestyle / brand story | `warm-earth` | `nature-organic`, `earthy-dusty` |
| Interior / wellness / mindfulness / slow living | `earthy-dusty` | `warm-earth`, `nature-organic` |
| Product launch / marketing / event | `vivid-launch` | `tech-neon`, `sunset-gradient` |
| Creative agency / travel / music / lifestyle | `sunset-gradient` | `vivid-launch`, `warm-earth` |
| Luxury / fashion / jewelry / premium / heritage | `jewel-tone` | `dark-cinematic`, `editorial-classic` |
| Children / storybook | `macaron` | `warm-earth` |
| Premium / entertainment / film | `dark-cinematic` | `jewel-tone`, `duotone` |
| Cultural / media / cover-art | `duotone` | `editorial-classic` |
| Environment / wellness / outdoor | `nature-organic` | `warm-earth`, `earthy-dusty` |
| Finance / journalism / explainer | `editorial-classic` | `cool-corporate` |
| Government / formal | `cool-corporate` | `editorial-classic` |

---

## 3. Rendering × Palette compatibility

Some combinations clash. Use this matrix as a sanity check after auto-selection.

| | cool-corp | warm-earth | tech-neon | editorial | macaron | mono-ink | vivid-launch | dark-cinem | duotone | nature-org | jewel-tone | frost-ice | sunset-grad | earthy-dusty |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| vector-illustration | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ |
| flat | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓✓ | ✓✓ |
| minimalist-swiss | ✓✓ | ✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✗ | ✓ |
| glassmorphism | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✓✓ | ✓ | ✓ |
| 3d-isometric | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✗ | ✓✓ | ✓✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| digital-dashboard | ✓✓ | ✗ | ✓✓ | ✓✓ | ✗ | ✓ | ✓ | ✓✓ | ✗ | ✗ | ✗ | ✓✓ | ✗ | ✗ |
| corporate-photo | ✓✓ | ✓✓ | ✓ | ✓✓ | ✗ | ✗ | ✓ | ✓✓ | ✗ | ✓✓ | ✓✓ | ✓ | ✗ | ✓✓ |
| blueprint | ✓✓ | ✗ | ✓✓ | ✓ | ✗ | ✓✓ | ✗ | ✓✓ | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ |
| editorial | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ |
| sketch-notes | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✓ | ✓ | ✗ | ✗ | ✓✓ | ✗ | ✗ | ✗ | ✓ |
| ink-notes | ✓ | ✓ | ✗ | ✓✓ | ✗ | ✓✓ | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ | ✗ | ✓ |
| chalkboard | ✗ | ✓ | ✗ | ✗ | ✓ | ✓ | ✗ | ✓✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| paper-cut | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✗ | ✓✓ |
| watercolor | ✓ | ✓✓ | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓✓ |
| warm-scene | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓✓ | ✓ | ✓✓ | ✓ | ✗ | ✓✓ | ✓ |
| screen-print | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | ✓✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| vintage-poster | ✓ | ✓✓ | ✗ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✗ | ✗ | ✓ | ✓✓ |
| fantasy-animation | ✗ | ✓✓ | ✗ | ✗ | ✓✓ | ✗ | ✓ | ✗ | ✗ | ✓✓ | ✗ | ✗ | ✓ | ✗ |
| pixel-art | ✗ | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| nature | ✓ | ✓✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | ✓✓ | ✓ | ✓ | ✓ | ✓✓ |

✓✓ recommended | ✓ acceptable | ✗ avoid

---

## 4. How to use

1. After picking rendering, look up your candidate palette in the auto-selection table.
2. Cross-check the compatibility matrix — if `✗`, pick the alternate.
3. `read_file image-palettes/<chosen>.md`.
4. Apply its proportion + role rules to the deck's HEX values when assembling prompts.

**Lock for the whole deck.**
