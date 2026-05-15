# Palette: dark-cinematic

Premium, atmospheric, low-light. The "dark mode" palette — used for premium product launches, film / entertainment decks, evening / nightlife themes, sophisticated tech that wants cinema mood. Distinguished by **deep dark background** with carefully placed bright accents.

> This file describes **color behavior**, not HEX values.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | Mid to high on accents; dark background provides contrast |
| Brightness contrast | Maximum — bright element on deep dark field |
| Color count visible | 2-3 (dark background + 1-2 bright accents) |
| Mood | Premium, cinematic, sophisticated, slightly mysterious |
| Material | Deep matte or subtle metallic, with implied light source |

---

## 2. Proportion rule (65-25-10, dark-dominant)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Dark background | **60-70%** | Deep dark — `#0A0E27` / `#1A1A1A` / dark brand neutral | The cinema field. May override deck's secondary if it isn't dark. |
| Primary bright element | **20-30%** | `primary` (brightness-boosted if originally muted) | The lit subject — confident vivid against the dark field. |
| Accent glow / highlight | **5-15%** | `accent` | Small concentrated bright pop — often with implied glow / luminance. |

---

## 3. Special: dark-cinematic may override deck background

dark-cinematic, like mono-ink, may **override `design_spec.colors.secondary`** if the deck's secondary is light. The dark background is essential to the palette identity. Note this in the prompt:

> "dark-cinematic palette uses a deep dark background `#0A0E27` regardless of deck's secondary HEX — the dark cinema field is the identity. The deck's primary `#XXX` is used as the bright lit subject; the deck's accent `#XXX` carries the glow accent."

---

## 4. Role semantics

- **Primary** is the lit subject — confident and bright against the dark, often with implied luminance.
- **Background** is the cinema void — deep dark, atmospheric, sometimes with subtle gradient toward even darker corners.
- **Accent** is the glow pop — small, bright, luminous.

---

## 5. How to phrase it in a prompt

> "Color behavior is dark-cinematic: deep dark background `#0A0E27` covers about 65% of the canvas with subtle gradient toward darker edges. Primary brand teal `#14B8A6` carries the main subject as a bright lit element (about 25%) with implied luminance glow at 8% opacity. Accent vivid gold `#D4AF37` appears as a small concentrated glow point near the focal area (about 10%). The bright primary and accent feel like light sources within the cinematic dark."

---

## 6. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ 3d-isometric | Premium dark-mode architecture |
| ✓✓ digital-dashboard | Dark-mode SaaS product |
| ✓✓ corporate-photo | Low-light photography |
| ✓✓ warm-scene | Evening / nightlight scenes |
| ✓✓ screen-print | Cinematic poster |
| ✓ blueprint | Dark-mode schematic |
| ✓ vector-illustration | Acceptable |
| ✗ sketch-notes / fantasy-animation / nature / chalkboard | Wrong temperament |
| ✗ macaron / warm-earth | Wrong brightness identity |

---

## 7. Fewshot prompt snippets

**Snippet A — applied to a digital-dashboard premium product**

> [...rendering paragraph...] Color behavior is dark-cinematic dashboard: deep dark `#0A0E27` covers about 65% of the surface as the cinema background. Primary bright teal `#14B8A6` carries the main chart bars with implied 8%-opacity glow halo (about 25%). Accent gold `#D4AF37` reserved for one highlighted KPI with stronger glow (about 10%). Card backgrounds are slightly lighter dark `#1E293B` separating cards from the deeper void. Premium, cinematic, sophisticated. [...container guidance...]
