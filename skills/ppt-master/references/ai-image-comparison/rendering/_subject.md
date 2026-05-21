# Rendering Comparison Set

## Controlled variables

| Dimension | Value | Status |
|---|---|---|
| Rendering | **varies (20 styles)** | under comparison |
| Palette | `cool-corporate` | fixed baseline |
| Composition | single-subject hero — see [`image-generator.md`](../../image-generator.md) §4.1 Primitive A | fixed baseline |

## Subject

> A confident professional standing beside an upward growth chart, looking forward — single dominant subject occupying 60-70% of the canvas. This is the "single-subject hero" composition described as [`image-generator.md`](../../image-generator.md) §4.1 Primitive A, used here as a stable baseline because a single dominant subject makes rendering differences read most clearly.

## Baseline HEX (canonical cool-corporate values)

- Primary `#1E3A5F` deep navy (main subject)
- Secondary `#F8F9FA` off-white (~60-70% breathing space)
- Accent `#D4AF37` gold (< 5% emphasis)

## Naming convention

Each filename is `<rendering>.png`, matching the corresponding file under `references/image-renderings/`.

## Why fix single-subject hero + cool-corporate

- The single-subject hero composition (§4.1 Primitive A) makes rendering differences read most clearly — a single dominant subject is the most visually representative shape
- `cool-corporate` has the most restrained color behavior — it does not visually overpower the rendering style being compared
- Both are the most common "origin" choices in production, making this set the most stable comparison baseline

## How to read this set

Scan all 20 images side by side. Focus on:

- **Line quality** — hand-drawn vs vector vs photographic
- **Surface material** — flat vs volumetric vs paper vs screen
- **Emotional temperament** — restrained-professional vs warm-narrative vs retro-nostalgic
