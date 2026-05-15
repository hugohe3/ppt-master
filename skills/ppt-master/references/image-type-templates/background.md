# Type: background

Atmospheric backdrop with **no central subject**. The image's job is to set tone and provide a calm field for SVG text overlay. The most common type for PPT covers, chapter dividers, and breathing pages.

> **What background means inside a PPT block**: the image is **all atmosphere, no subject**. Unlike `hero`, there is no dominant figure. Unlike `infographic`, there are no labeled zones. Background is pure ambience.

## 1. Composition skeleton

```
   ┌────────────────────────────────────┐
   │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
   │   ░ atmospheric gradients ░         │
   │  ░  + subtle geometric anchor ░     │
   │   ░  (corner / edge, not center) ░  │
   │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │
   └────────────────────────────────────┘
                  ↑
       Center 60% is intentionally calm
       (SVG title will overlay here)
```

| LAYOUT | Atmospheric field — gradient, subtle pattern, or restrained color block composition. No dominant subject |
| ELEMENTS | Optional small geometric anchor in a corner or along an edge (a line, a small shape, a subtle motif). Never centered |
| NEGATIVE SPACE | The center 60-70% must be calm — low visual weight, ready to receive SVG title/text overlay |
| TEMPERAMENT | Sets the deck's overall tone: corporate-restrained, warm-friendly, tech-energetic, etc. |

## 2. Text-policy variants

### `text_policy: none`

Backgrounds are atmospheric — for most uses, keep text out and let SVG handle overlay copy.

Sample fragment:

> NO text of any kind anywhere in the image — no letters, numbers, signs, watermarks, labels, or written symbols. The image is pure atmosphere; SVG text overlay will be added externally.

### `text_policy: embedded` (decorative or designed lettering)

When the background's mood is enhanced by lettering — large decorative word in the bleed, retro stamp, scattered alphabet texture, or a designed cover title that's part of the artwork. Name the text role explicitly in the prompt:

- Decorative lettering: "large decorative 'GROWTH' lettering in 3D extruded retro style as background element; spelling not critical"
- Designed cover title: "main title text '{exact words}' rendered in {font family echoing deck's body typography}; content must be accurate"

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate cover background, text_policy: none, 1280×720**

> Clean flat vector illustration backdrop. Atmospheric composition with no central subject — bold geometric shapes arranged along the canvas edges to leave the center calm. Primary deep navy `#1E3A5F` forms a confident diagonal block across the lower-left third; secondary light gray `#F8F9FA` occupies the upper two-thirds as breathing space; accent gold `#D4AF37` appears only as one thin geometric line near the lower right corner (under 5% of canvas). Crisp 2px outlines, no gradients, single 8% soft drop shadow under the navy block. The central 60% of the canvas is deliberately calm and unbusy — designed to receive a slide title overlaid in SVG. Composed as a 1280×720 full-bleed PPT background. NO text, letters, numbers, signs, watermarks, or written symbols anywhere in the image. Color values are rendering guidance only — do not display HEX codes or color names as text. Simplified geometric shapes only.