# Type: matrix

A **2×2 quadrant grid** (occasionally 3×3) where each cell carries its own label, color, or icon. The structural backbone of consulting frameworks — SWOT, BCG, Eisenhower, Ansoff, Porter's, Risk/Reward. Used wherever two orthogonal axes divide the page into discrete zones.

> **What matrix means inside a PPT block**: the canvas is **rigorously divided into equal quadrants** by perpendicular axes. Unlike `framework` (central hub + radiating satellites), matrix has no center — meaning lives in the four cells. Unlike `comparison` (two side-by-side zones), matrix splits **both** horizontally and vertically.

---

## 1. Composition skeleton

```
   ┌────────────────┬────────────────┐
   │                │                │
   │   Quadrant 1   │   Quadrant 2   │
   │   (icon + )    │   (icon + )    │
   │                │                │
   ├────────────────┼────────────────┤
   │                │                │
   │   Quadrant 3   │   Quadrant 4   │
   │   (icon + )    │   (icon + )    │
   │                │                │
   └────────────────┴────────────────┘
        ↑                ↑
   Two perpendicular axes split the canvas
```

| LAYOUT | Two perpendicular axes (one horizontal, one vertical) cross at canvas center, dividing into 4 equal quadrants |
| ELEMENTS | One simple iconic symbol per quadrant + optional axis-end indicators (arrows or labels). Each quadrant uses a distinct color or tint from the deck palette |
| NEGATIVE SPACE | Generous inside each quadrant — the icon should occupy 40-60% of its quadrant's area |
| BALANCE | Visual weight equal across all four quadrants — no single quadrant dominates |

## 2. Text-policy variants

### 3.1 `text_policy: none`

Quadrants carry icons only; axis labels and quadrant names are handled in SVG. Image models often render axis-label text inconsistently across the four positions, so this is the lower-risk path when label precision matters.

Sample fragment:

> NO text, letters, numbers, axis labels, or quadrant names in the image. Each quadrant contains a simple iconic symbol only; SVG text overlay will add axis labels and quadrant names externally.

### 3.2 `text_policy: embedded`

When the matrix's identity comes from its in-image lettering — a stylized SWOT poster with the four letters as visuals, a designer-matrix where axis labels are typeset into the artwork. Keep labels to single English words ("HIGH", "LOW", "GROW", "HOLD"). Specify the font family in the prompt to echo the deck's body typography.

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate SWOT matrix, text_policy: none, 800×800**

> Clean flat vector illustration of a 2×2 strategic matrix. Two perpendicular thin lines in primary deep navy `#1E3A5F` cross at the exact canvas center, dividing the canvas into four equal quadrants. Each quadrant has a subtle background tint: upper-left in pale primary navy at 10% opacity, upper-right in pale accent gold `#D4AF37` at 15% opacity, lower-left in pale gray `#F8F9FA`, lower-right in slightly deeper pale navy at 18% opacity. Each quadrant contains one simple iconic symbol in primary navy, centered within its quadrant — a shield (strength), a lightning bolt (opportunity), a target (weakness), an alert triangle (threat). Each icon occupies about 45% of its quadrant. Small accent gold dots sit at the four outer corners. Composed as an 800×800 reference matrix block with 10% padding. NO text, letters, axis labels, or quadrant names anywhere — SVG will overlay all labels. Color values are rendering guidance only.