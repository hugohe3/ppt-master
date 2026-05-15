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

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed strategy matrix | 1280×720 | 16:9 | 12% all sides |
| Half-page quadrant block | 700×700 | 1:1 | 12% |
| Square reference matrix | 800×800 | 1:1 | 10% |
| Wide consulting matrix | 1200×600 | 2:1 | 12% sides, 8% top/bottom |

---

## 3. Text-policy variants

### 3.1 `text_policy: none` (default)

Quadrants carry icons only; axis labels and quadrant names are added later as SVG overlay. This is the safer choice — image models often render axis-label text inconsistently across the four positions.

Sample fragment:

> NO text, letters, numbers, axis labels, or quadrant names in the image. Each quadrant contains a simple iconic symbol only; SVG text overlay will add axis labels and quadrant names externally.

### 3.2 `text_policy: embedded` (rare)

Use only when the user explicitly wants the axis labels baked into the image. Keep labels to single English words ("HIGH", "LOW", "GROW", "HOLD") and accept higher risk of typo/glyph errors.

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate SWOT matrix, text_policy: none, 800×800**

> Clean flat vector illustration of a 2×2 strategic matrix. Two perpendicular thin lines in primary deep navy `#1E3A5F` cross at the exact canvas center, dividing the canvas into four equal quadrants. Each quadrant has a subtle background tint: upper-left in pale primary navy at 10% opacity, upper-right in pale accent gold `#D4AF37` at 15% opacity, lower-left in pale gray `#F8F9FA`, lower-right in slightly deeper pale navy at 18% opacity. Each quadrant contains one simple iconic symbol in primary navy, centered within its quadrant — a shield (strength), a lightning bolt (opportunity), a target (weakness), an alert triangle (threat). Each icon occupies about 45% of its quadrant. Small accent gold dots sit at the four outer corners. Composed as an 800×800 reference matrix block with 10% padding. NO text, letters, axis labels, or quadrant names anywhere — SVG will overlay all labels. Color values are rendering guidance only.

**Snippet B — flat + vivid-launch BCG matrix, text_policy: none, 1200×600**

> Clean flat vector matrix composition. Two thick perpendicular lines in primary deep purple `#7C3AED` divide the canvas into four equal quadrants. Each quadrant is filled with a distinct vivid flat color from the deck palette — upper-left deep purple `#7C3AED` solid, upper-right vivid orange `#F97316` solid, lower-left soft secondary cream `#FEF3C7`, lower-right vivid pink `#EC4899` solid. Inside each quadrant, one simple white iconic symbol (centered, about 50% of quadrant area) — a star, a question mark, a cow silhouette, a dog silhouette. Crisp solid fills, no gradients. Small directional arrows mark the two outer axis ends (one pointing up, one pointing right). Composed as a 1200×600 wide consulting matrix with 12% side padding. NO text or labels — SVG overlays axis names and category labels. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Quadrants unequal in size | Center-crossing rule omitted | "Axes cross at EXACT canvas center, four quadrants of equal size" |
| Icons too small or off-center | Icon sizing rule omitted | Reaffirm "each icon occupies 40-50% of its quadrant, centered within the quadrant" |
| Text rendered into the image despite `none` | Rule too weak | Strengthen with full exclusion list including "no axis labels, no quadrant names, no titles" |
| Quadrants visually compete (no clear axis structure) | Axis lines too thin or omitted | "Two perpendicular lines clearly visible — they ARE the matrix structure" |
| 3×3 grid instead of 2×2 | Model defaulted to standard grid | Explicitly state "exactly 2×2, four quadrants only" |

---

## 6. When to switch away from matrix

- If structure is **central hub + radiating** → `framework`
- If structure is **left vs right only** (one axis) → `comparison`
- If structure is **sequential / linear** → `flowchart` or `timeline`
- If structure is **closed loop** → `cycle`
- If structure is **tiered / layered** → `pyramid`
