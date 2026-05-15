# Rendering: vector-illustration

The default safe rendering for general PPT decks. Clean flat vector art with bold shapes, deliberate geometry, and confident negative space. Scales reliably across 15+ slide decks without visual fatigue.

## 1. Style paragraph (paste-ready, 95 words)

> Clean flat vector illustration with bold geometric shapes and confident solid fills. Crisp outlines (1.5-2px equivalent stroke weight, consistent across all elements) define every form. No gradients within shapes — color is applied as flat blocks. Subtle shadow only where it adds depth (soft 8% opacity drop, no harsh edges). Composition is grid-aware and balanced, with deliberate negative space carrying as much weight as filled areas. Iconography is simplified to essential geometry — recognizable at small sizes. Overall feel is modern, professional, and confidently restrained — a quality often called "design-system aesthetic" in product/SaaS contexts.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Clean vector outlines, uniform stroke weight, sharp corners or consistent rounded radius |
| Texture | None — flat fills only. No noise, no paper grain, no painterly artifacts |
| Depth | Optional 8% soft drop shadow under elevated elements; no perspective rendering |
| Material | None — color is information, not material simulation |
| Mood | Neutral-positive, professional, designed |

---

## 3. Container sizing for local PPT inserts

| Embedded position | Recommended canvas | Aspect | Inner padding |
|---|---|---|---|
| Full-bleed background | 1280×720 | 16:9 | 15% all sides (the central 70% must be calm for SVG overlay) |
| Half-page illustration | 600×500 | ~1.2 | 12-15% |
| Quarter-page accent | 400×300 | 4:3 | 10-12% |
| Hero band (top) | 1200×400 | 3:1 | 15% top/bottom, 10% sides |
| Spot illustration | 320×320 | 1:1 | 8-10% |

---

## 4. Using the deck's HEX values

vector-illustration treats colors as **flat coded zones**, not as gradients or shadows. Apply HEX values exactly — no tinting, no shading, no blend modes implied.

- Primary HEX: main shape fills, dominant elements
- Secondary HEX: background or large supporting blocks
- Accent HEX: highlight, key data point, or single emphasis element
- Lines and outlines: dark neutral (#222 or near-black) unless the deck's primary is dark enough to use directly

---

## 5. Fewshot prompt snippets

**Snippet A — background block, text_policy: none**

> Clean flat vector illustration backdrop. Bold geometric shapes in flat solid fills — primary deep navy (#1E3A5F) forming a confident diagonal across the lower third, secondary light gray (#F8F9FA) occupying the upper two-thirds as calm breathing space, accent gold (#D4AF37) appearing only as one or two thin geometric lines drawing the eye toward the center. Crisp 2px outlines on all shapes. No gradients, no shadows beyond a single 8% soft drop. The central 70% of the canvas is deliberately calm and unbusy, ready to receive a slide title overlaid in SVG. Composed as a local PPT background block with 15% padding on all sides. Color values are rendering guidance only — do not display HEX codes, color names, or any labels as text in the image. NO text of any kind anywhere in the image — no letters, numbers, signs, watermarks, or written symbols.
