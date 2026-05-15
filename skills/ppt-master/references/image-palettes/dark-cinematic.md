# Palette: dark-cinematic

Premium, atmospheric, low-light. The "dark mode" palette — used for premium product launches, film / entertainment decks, evening / nightlife themes, sophisticated tech that wants cinema mood. Distinguished by **deep dark background** with carefully placed bright accents.

> This file describes **color behavior**, not HEX values.

## 1. Special: dark-cinematic may override deck background

dark-cinematic, like mono-ink, may **override `design_spec.colors.secondary`** if the deck's secondary is light. The dark background is essential to the palette identity. Note this in the prompt:

> "dark-cinematic palette uses a deep dark background `#0A0E27` regardless of deck's secondary HEX — the dark cinema field is the identity. The deck's primary `#XXX` is used as the bright lit subject; the deck's accent `#XXX` carries the glow accent."

## 2. Compatible renderings

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

## 3. Fewshot prompt snippets

**Snippet A — applied to a digital-dashboard premium product**

> [...rendering paragraph...] Color behavior is dark-cinematic dashboard: deep dark `#0A0E27` covers about 65% of the surface as the cinema background. Primary bright teal `#14B8A6` carries the main chart bars with implied 8%-opacity glow halo (about 25%). Accent gold `#D4AF37` reserved for one highlighted KPI with stronger glow (about 10%). Card backgrounds are slightly lighter dark `#1E293B` separating cards from the deeper void. Premium, cinematic, sophisticated. [...container guidance...]