# Palettes — Index (Legacy / Internal Reference)

> New confirmation flows do **not** present or author `image_palette`. Image colors inherit `spec_lock.md colors` directly. This catalog remains only as legacy documentation and for maintaining the historical comparison gallery; the current generation flow ignores legacy `image_palette` rows. Never turn it into a user-facing choice or let it override deck HEX roles.

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

## 2. Legacy escape hatch — `custom`

When no preset temperament matches (brand HEX outside preset ranges, ceremonial / cultural / niche aesthetic), set `image_palette: custom` and supply a one-paragraph `image_palette_behavior`.

**Trigger** — all of:

| Condition | Check against |
|---|---|
| No preset temperament fits | `design_spec.e Color Scheme` |
| Brand / template / chat names no preset | truth-precedence inputs |
| Not expressible as "preset X + small HEX swap" | Strategist confirmation chat |

**Hard rule — `palette_behavior` prose**:

| Rule | Value |
|---|---|
| Length | One paragraph, 2-5 sentences |
| Per-HEX content | role + approximate area share (proportion follows information weight; no fixed % menu) |
| HEX source | Quote `design_spec.colors` values verbatim with backticks; never invent HEX |
| Forbidden | Naming a competing preset ("like macaron but darker") |

```yaml
- image_palette: custom
- image_palette_behavior: "Primary deep aubergine `#4C1D95` anchors the dominant ~35% of canvas; secondary warm cream `#FEF3C7` carries ~55% as breathing field; accent burnished gold `#D4AF37` appears only in 5-10% as small ceremonial accents. Restrained, ceremonial gravitas — no fourth color."
```

> Note: §4's rendering × palette matrix only covers the 14 presets. When `palette: custom`, Strategist owns the compatibility judgment in h.5.

**Hard rule**: `custom` is a tail-case, not a default. See [`strategist.md`](../strategist.md) h.5 for the one-`custom`-per-dimension limit.

---

## 3. Legacy auto-selection table — `design_spec` → palette

Match `design_spec.md d. Style` + `e. Color Scheme` content vibe. First match wins. **No row matches** → use `custom` per §2 rather than force-fitting `cool-corporate`.

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

## 4. Historical Rendering × Palette compatibility

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

## 5. Legacy interpretation only

Use this catalog only to understand a historical lock or maintain comparison assets. Do not select a palette, load a palette file, or author `image_palette` / `image_palette_behavior` in the current flow; assemble image prompts from the locked deck color roles instead.

**Lock for the whole deck.**
