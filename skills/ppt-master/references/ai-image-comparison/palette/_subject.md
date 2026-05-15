# Palette Comparison Set

## Controlled variables

| Dimension | Value | Status |
|---|---|---|
| Palette | **varies (10 palettes)** | under comparison |
| Rendering | `vector-illustration` | fixed baseline |
| Type | `hero` | fixed baseline |

## Subject

> A confident professional standing beside an upward growth chart, looking forward — single dominant subject occupying 60-70% of the canvas (hero composition).

## On HEX values

**Important**: this set does **not** fix HEX values across all 10 palettes. Each palette uses its own typical HEX triplet.

Reason: a palette is a *color behavior* (saturation, contrast, temperament, proportion), and the HEX it expects is part of that behavior. Forcing cool-corporate's deep navy through a vivid-launch palette would produce a strange "restrained navy mimicking promotional energy" image — losing the semantic representativeness of the palette.

This also matches real production: a user who picks vivid-launch will have vivid HEX values in their `design_spec`, not navy. This set simulates each palette's typical production scenario.

| Palette | Primary | Secondary | Accent |
|---|---|---|---|
| cool-corporate | `#1E3A5F` deep navy | `#F8F9FA` off-white | `#D4AF37` gold |
| warm-earth | `#9A3412` terracotta | `#FEF3C7` cream | `#D4AF37` gold |
| tech-neon | `#0EA5E9` electric blue | `#0A0E27` deep navy | `#06B6D4` cyan |
| editorial-classic | `#0F2C4C` deep navy | `#FAF7F2` warm cream | `#C2410C` burnt orange |
| macaron | (pastel tints) | `#F5F0E8` cream | `#F97316` coral |
| mono-ink | `#1A1A1A` near-black | `#FFFFFF` white | `#E8655A` coral red |
| vivid-launch | `#E11D48` magenta | `#FAFAFA` near-white | `#F97316` orange |
| dark-cinematic | `#14B8A6` teal | `#0A0E27` deep dark | `#D4AF37` amber |
| duotone | `#0F766E` deep teal | `#D97706` amber | (only 2 colors) |
| nature-organic | `#166534` forest green | `#FEF3C7` cream | `#D4AF37` honey |

## Naming convention

Each filename is `<palette>.png`, matching the corresponding file under `references/image-palettes/`.

## How to read this set

Scan all 10 images side by side. Focus on:

- **Color temperature** — cool-professional vs warm-human vs neutral-editorial
- **Saturation** — restrained vs vivid vs monochrome
- **The 60-30-10 proportional feel** — how dominant the secondary really is
- **Accent weight** — how much visual presence the small accent commands
