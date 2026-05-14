# Palette: editorial-classic

Refined, magazine-style, balanced. The premium-restrained palette — used in finance journalism, opinion pieces, sophisticated B2B content, longform commentary. Distinguished from cool-corporate by slightly richer primary tones and more deliberate accent rules.

> This file describes **color behavior**, not HEX values.

## Temperament

| Trait | Setting |
|---|---|
| Saturation | Moderate — colors are rich but not loud |
| Brightness contrast | Medium-strong — supports editorial readability |
| Color count visible | 3 |
| Mood | Refined, intelligent, magazine, slightly serious |
| Material | Flat with subtle paper texture |

## Proportion rule (55-30-15, with magazine pacing)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / page field | **50-60%** | `secondary` | Warm cream, off-white, or very pale neutral — feels like magazine paper. |
| Main feature / column block | **25-35%** | `primary` | The rich brand tone — deep navy, deep teal, deep burgundy. Used in confident solid blocks or hero subjects. |
| Editorial accent / rule | **10-15%** | `accent` | A small concentrated accent — often a thin horizontal rule, a single highlight, a callout marker. Slightly more visible than cool-corporate's accent. |

## Role semantics

- **Primary** is the editorial voice — confident, anchoring, the column lead. Use it for: dominant text blocks (visually, not literally), hero subjects, the "lead story" element.
- **Secondary** is the magazine paper — warm or cool neutral, slightly textured. Should feel like physical print, not digital.
- **Accent** is the editorial rule — a thin line, a callout dot, a marker. Editorial restraint says: "one accent, used decisively."

## How to phrase it in a prompt

> "Color behavior is editorial-classic: secondary warm cream `#FAF7F2` carries the magazine-paper field across about 55% of the canvas with subtle paper-grain texture at 8% opacity; primary deep navy `#0F2C4C` anchors the dominant column block and hero subject in confident solid tone (about 30%); accent burnt orange `#C2410C` appears as a single thin horizontal rule and one small highlight marker (totaling under 14%). Magazine-considered composition, deliberate breathing room."

## Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ editorial | Perfect alignment |
| ✓✓ vector-illustration | Restrained vector with magazine pacing |
| ✓✓ ink-notes | Editorial restraint + ink-notes formality |
| ✓✓ corporate-photo | Magazine photography |
| ✓ flat | Acceptable — flat is slightly more decorative |
| ✓ blueprint | Works for technical magazine content |
| ✓ screen-print | Editorial poster style |
| ✗ sketch-notes / fantasy-animation / pixel-art | Too playful for editorial restraint |

## Fewshot prompt snippets

**Snippet A — applied to an editorial finance explainer**

> [...rendering paragraph...] Color behavior is editorial-classic: secondary warm cream `#FAF7F2` covers about 55% of the canvas with subtle paper-grain at 8% opacity; primary deep navy `#0F2C4C` carries the dominant data block on the left (about 32%); accent burnt orange `#C2410C` appears as one thin horizontal rule and a single small data marker at the highlighted point (about 12% total). Magazine-spread composition with deliberate gutters. [...container guidance...]

**Snippet B — applied to a corporate-photo magazine hero**

> [...rendering paragraph...] Color behavior is editorial-classic: image is graded toward magazine warmth — cream highlights, deep navy shadows. The subject is graded with primary `#0F2C4C` as dominant shadow tone (about 30%), secondary `#FAF7F2` as soft highlight tone (about 55%), and accent `#C2410C` appearing only as a small contextual detail in the environment (about 13%). Editorial restraint throughout. [...container guidance...]

## What to avoid

- Vibrant / loud accent (editorial-classic is restrained)
- Equal-share triplet (creates carnival, not magazine)
- Too much accent area (defeats editorial restraint)
- Cold sterile background (paper warmth matters)

## When to switch away

- For business consulting / B2B → `cool-corporate`
- For warm storytelling → `warm-earth`
- For methodology / Before-After → `mono-ink`
- For premium / cinematic dark → `dark-cinematic`
