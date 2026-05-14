# Palette: duotone

Two-color limited, poster-like. The constrained palette — only two colors plus a background, used for cultural / cover hero / cinematic poster decks where chromatic discipline carries the page.

> This file describes **color behavior**, not HEX values.

## Temperament

| Trait | Setting |
|---|---|
| Saturation | Variable — both colors are deliberate, neither competes |
| Brightness contrast | Strong between the two colors |
| Color count visible | 2 (+ optional neutral background) |
| Mood | Poster, cinematic, editorial-bold, chromatically disciplined |
| Material | Flat or screen-print textured |

## Proportion rule (60-40 or 50-50, two-color)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Color A (figure / dominant) | **40-60%** | Often `primary` | One of the two duotone colors. Carries the main subject or dominant zone. |
| Color B (ground / secondary) | **40-60%** | Often `accent` (or whatever pairs well with primary) | The complementary color. Carries the rest of the composition. |
| Optional neutral | **0-20%** | Off-white / cream / near-black | Used as separator or small neutral zone. |

**Hard rule**: only 2 colors appear; if the deck's HEX is a triplet, drop secondary or use it as the neutral background only.

## Role semantics

- **Color A** is the figure — the silhouette, the dominant block, the foreground.
- **Color B** is the ground — the background field, the contrasting zone, where Color A lives.
- The choice of pairing matters more than role assignment — pick the two HEX values from the deck that have the strongest duotone tension.

## How to phrase it in a prompt

> "Color behavior is duotone: Color A — deep teal `#0F766E` (the deck's primary) — carries the main subject silhouette and dominant zone (about 50%). Color B — vivid amber `#D97706` (the deck's accent) — carries the background and secondary zone (about 48%). The two colors are the entire palette — no third hue beyond a barely-perceptible neutral 2% in transitional textures."

## Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ screen-print | Direct alignment — duotone is screen-print's signature |
| ✓✓ flat | Bold two-color flat |
| ✓ vector-illustration | Two-color vector |
| ✓ editorial | Two-color editorial spread |
| ✓ blueprint | Two-color schematic |
| ✓ pixel-art | Limited-color retro |
| ✓ chalkboard | Pastel two-color chalk |
| ✗ corporate-photo | Photography can't be duotone (unless duotone-graded) |
| ✗ sketch-notes / fantasy-animation / nature / watercolor | Wrong temperament |
| ✗ digital-dashboard / 3d-isometric | Need more chromatic depth |

## Fewshot prompt snippets

**Snippet A — applied to a screen-print cover poster**

> [...rendering paragraph...] Color behavior is duotone: deep navy `#1E3A5F` carries the lower 55% as a confident block including the silhouette of a stylized mountain. Burnt orange `#C2410C` carries the upper 45% as the sky, with one small near-white circular sun (under 3%). Only these two colors appear in the composition — no third hue. Halftone dot texture at the horizon between the two color zones. Slight color misregistration adds silkscreen authenticity. [...container guidance...]

**Snippet B — applied to a flat editorial two-color spread**

> [...rendering paragraph...] Color behavior is duotone: deep teal `#0F766E` (the deck's primary) carries the left 50% as a flat block with a stylized geometric form. Warm amber `#D97706` (the deck's accent) carries the right 50% as a complementary flat block with a different stylized form. The two colors meet at a clean vertical edge down the center. No third color, no gradients. Editorial poster balance. [...container guidance...]

## What to avoid

- A third color creeping in (defeats duotone discipline)
- Gradients within either color (duotone is flat)
- Too-similar colors with no chromatic tension
- Photo-realistic content (duotone is intentionally stylized)

## When to switch away

- For more color flexibility → any other palette
- For monochrome (one color) → `mono-ink`
- For tech vivid → `tech-neon`
