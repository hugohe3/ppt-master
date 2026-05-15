# Rendering: glassmorphism

Frosted-glass / soft-UI aesthetic — translucent layered panels, blurred background, soft shadows, depth via transparency. The "modern app UI" rendering — used for modern SaaS, fintech, health-tech, premium app showcases, product launches.

---

## 1. Style paragraph (paste-ready, 105 words)

> Modern glassmorphism aesthetic. Composition built on layered semi-transparent panels with frosted-glass blur — each panel reads as a sheet of polished glass floating slightly above a soft gradient background. Panel edges are subtly defined with thin 1px highlight strokes (whitespace at top/left, slight shadow at bottom/right) suggesting refraction. Background is a soft pastel-cool gradient that blurs through the panels. Drop shadows under panels are large and soft (15-25% opacity, generous spread) to create real depth. Interior content of each panel uses crisp solid color shapes and clean typography character. Overall feel is premium, futuristic-friendly, polished — the aesthetic of contemporary fintech and Apple-style product showcases.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Thin 1px highlight strokes on panel top/left edges (glass refraction cue) |
| Texture | Frosted blur on panels (gaussian blur ~10-15px over background) |
| Depth | Real layered depth — large soft drop shadows, parallax-suggesting offsets |
| Material | Translucent polished glass on soft gradient background |
| Mood | Premium, polished, futuristic-friendly, optimistic |

---

## 3. Container sizing for local PPT inserts

| Embedded position | Recommended canvas | Aspect | Inner padding |
|---|---|---|---|
| Full-bleed product hero | 1280×720 | 16:9 | 12% all sides |
| Half-page UI showcase | 600×500 | ~1.2 | 10-12% |
| Spot product card | 400×500 | 4:5 | 10% |
| Hero band | 1200×500 | 2.4:1 | 12% |

---

## 4. Using the deck's HEX values

glassmorphism treats the deck's HEX as **panel content + background gradient stops**:

- Background gradient: a soft transition from a lighter tint of `primary` toward `secondary` (e.g., pale blue → pale gray)
- Panel fills: semi-transparent (~40-60% opacity) tints of `primary` or near-white
- Panel content shapes: solid `primary`, with `accent` reserved for the single most-emphasized data point or CTA element
- Avoid heavy saturation — glassmorphism feels best with mid-light tones; if the deck's primary is very dark, use it only in interior content shapes, not in the gradient

---

## 5. Fewshot prompt snippets

**Snippet A — fintech product showcase, text_policy: none**

> Modern glassmorphism product showcase. Soft pastel-cool background gradient transitioning from light tint of primary `#1E3A5F` (about 30% opacity) in the upper-left to near-white `#F8F9FA` in the lower-right. Two layered frosted-glass panels float above — a larger main panel (about 55% of canvas, centered with slight rotation suggesting 3D depth) and a smaller card peeking from behind the main panel. Each panel has subtle 1px white highlight on its top-left edge and soft 20%-opacity drop shadow beneath (generous spread, suggesting real depth). Interior content: clean solid shapes — a stylized chart bar in primary `#1E3A5F`, a small accent gold `#D4AF37` indicator marking one data point. Crisp, polished, premium. Composed as a 600×500 half-page UI showcase with 12% padding. Color values are rendering guidance only — do not display HEX codes as text. NO text or labels anywhere; SVG will overlay copy.
