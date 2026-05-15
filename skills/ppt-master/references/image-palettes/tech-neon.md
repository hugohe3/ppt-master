# Palette: tech-neon

Energetic, futuristic, high-contrast. The signature look for AI / SaaS / product launch / cyber / cutting-edge tech decks. Distinguished by saturated brand color on a darker or contrasted field, with a glow / luminance quality.

> This file describes **color behavior**, not HEX values. HEX comes from `design_spec.colors`.

## 1. Temperament

| Trait | Setting |
|---|---|
| Saturation | High — colors are intentionally vivid |
| Brightness contrast | Strong — vivid foreground on darker or neutral background |
| Color count visible | 3 (primary + secondary + accent) — restraint despite vividness |
| Mood | Energetic, futuristic, confident, edge |
| Material | Smooth digital, often with implied glow or luminance |

---

## 2. Proportion rule (50-35-15, with intentional luminance)

| Role | Share | HEX from `design_spec` | Behavior |
|---|---|---|---|
| Background / digital field | **45-55%** | `secondary` | Either a near-white digital field (light mode tech) OR a deep dark field like `#0A0E27` (dark mode tech). The choice depends on deck's overall mood. |
| Main subject / vivid brand | **30-40%** | `primary` | The saturated brand color — electric blue, vibrant teal, neon green. Renders confidently against the background. |
| Emphasis / accent glow | **10-15%** | `accent` | The "this is the future" pop — neon cyan, hot magenta, bright orange. Often rendered with implied glow / soft halo. |

> tech-neon is the rendering palette most likely to suggest **glow or luminance** in the prompt — primary forms often have a soft outer glow at 8% opacity in the same color.

---

## 3. Role semantics

- **Primary** is the brand signature — vivid, confident, the visual lead. Use it for: dominant chart elements, hero shape fills, primary geometric forms.
- **Secondary** sets the technological tone — clean digital surface or deep digital void. Should feel "screen-like" or "interface-like".
- **Accent** is the future-pop — small, glowing, attention-grabbing. Often rendered with implied luminance.

---

## 4. How to phrase it in a prompt

> "Color behavior is tech-neon: secondary deep digital navy `#0A0E27` covers about 50% of the canvas as the dark field; primary electric blue `#0EA5E9` carries the main subject in confident saturated tones (about 35%) with a soft 8%-opacity glow halo around it; accent vivid cyan `#06B6D4` appears in 10-15% as small bright pops, also with implied glow. High contrast between vivid foreground and dark digital background."

---

## 5. Compatible renderings

| Rendering | Notes |
|---|---|
| ✓✓ 3d-isometric | Tech architecture with glowing edges |
| ✓✓ digital-dashboard | Product UI with neon highlights |
| ✓✓ flat | Bold flat blocks with neon accent |
| ✓ vector-illustration | Works but feels more muted than expected |
| ✓✓ blueprint | Technical schematic with luminance |
| ✓ pixel-art | Retro neon gaming |
| ✗ sketch-notes / watercolor / fantasy-animation / nature | Temperament conflict — warm vs cyber |
| ✗ corporate-photo | Photography wants natural color, not neon |

---

## 6. Fewshot prompt snippets

**Snippet A — applied to a 3d-isometric architecture**

> [...rendering paragraph...] Color behavior is tech-neon: secondary deep navy `#0A0E27` covers the background plane and shadowed faces (about 50% of canvas); primary electric blue `#0EA5E9` carries the lit faces of the stacked blocks in saturated solid fills (about 35%) with a subtle 8%-opacity outer glow around each block's edge; accent vivid cyan `#06B6D4` appears on connecting lines and one highlighted block's lit face (about 12% area total) with stronger implied glow. High contrast throughout. [...container guidance...]
