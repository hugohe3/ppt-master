# Type: cycle

A **closed-loop process** — 3-6 steps arranged in a circle (or rounded loop), connected by directional arrows that return the flow to its starting point. The structural backbone for PDCA, growth flywheel, design-thinking cycle, continuous-improvement loops, lifecycle diagrams.

> **What cycle means inside a PPT block**: a **closed circular flow** — every step leads to the next, and the last step leads back to the first. Unlike `flowchart` (linear, one-way), cycle has no terminal end. Unlike `framework` (centered hub with passive satellites), cycle has directional motion around the perimeter.

---

## 1. Composition skeleton

```
             ┌─────────┐
       ┌────▶│ Step 1  │────┐
       │     └─────────┘     │
       │                     ▼
   ┌───┴───┐             ┌─────────┐
   │ Step 4│             │ Step 2  │
   └───────┘             └────┬────┘
       ▲                      │
       │     ┌─────────┐      │
       └─────│ Step 3  │◀─────┘
             └─────────┘
```

| LAYOUT | 3-6 step nodes arranged on a circular (or rounded square) perimeter; arrows connect each node to the next, closing back to the first |
| ELEMENTS | One simple iconic symbol per step + curved or straight directional arrows between them. Optional central anchor (a label, a small icon representing the cycle's name) |
| NEGATIVE SPACE | Center of the circle is calm — either empty or holds a small anchor element only |
| BALANCE | Step nodes spaced evenly around the perimeter; arrow weights uniform |

---

## 2. Container sizing for local PPT inserts

| Use | Canvas | Aspect | Padding |
|---|---|---|---|
| Full-bleed cycle diagram | 1280×720 | 16:9 | 15% (cycle reads best with breathing room) |
| Half-page cycle block | 700×700 | 1:1 | 15% |
| Square cycle reference | 800×800 | 1:1 | 12% |
| Hero cycle band | 1200×600 | 2:1 | 15% |

---

## 3. Text-policy variants

### 3.1 `text_policy: none` (default)

Step labels are added later as SVG overlay. Each step shows an icon only; the SVG positions the label adjacent to its step. This is the recommended path.

Sample fragment:

> NO text, letters, numbers, or step labels in the image. Each step node contains only one simple iconic symbol; SVG text overlay will add step names externally.

### 3.2 `text_policy: embedded` (occasional)

Use when the user wants a fully self-contained cycle diagram. Keep step names to single English words ("PLAN", "DO", "CHECK", "ACT").

---

## 4. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate PDCA cycle, text_policy: none, 700×700**

> Clean flat vector illustration of a closed-loop process cycle. Four step nodes arranged in a perfect circle on the canvas perimeter — at 12 o'clock, 3 o'clock, 6 o'clock, and 9 o'clock positions. Each node is a rounded square (about 130×130px equivalent) filled with primary deep navy `#1E3A5F`, with one simple white iconic symbol centered inside — a clipboard (plan), a hand (do), a magnifying glass (check), a gear (act). Curved directional arrows in accent gold `#D4AF37` connect each node to the next going clockwise, closing the loop. The center of the circle is calm — secondary light gray `#F8F9FA` field with one small accent gold dot at the exact center as the cycle's anchor. Crisp 2px outlines, soft 8% drop shadow under each node. Composed as a 700×700 half-page cycle block with 15% padding. NO text, letters, or step labels anywhere — SVG will overlay all step names. Color values are rendering guidance only.

**Snippet B — flat + tech-neon growth flywheel, text_policy: none, 800×800**

> Modern flat geometric flywheel composition. Six step nodes arranged evenly around a circular perimeter, each rotated slightly toward the cycle's rotation direction to suggest motion. Each node is a hexagonal shape filled with primary electric blue `#0EA5E9`, containing one simple white iconic symbol — a user, a heart, a star, a megaphone, an upward arrow, a refresh icon. Between each pair of nodes, a curved arrow in accent vivid cyan `#06B6D4` flows clockwise, the arrows getting slightly thicker as they progress (suggesting acceleration). The center holds a small flat circle in accent cyan with a single white spark icon — the flywheel's anchor. Background secondary deep navy `#0A0E27`. Composed as an 800×800 cycle block with 12% padding. NO text or labels anywhere. Color values are rendering guidance only.

---

## 5. Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Cycle reads as flowchart (linear, with end) | "Closed loop" rule weak | Strengthen with "last step's arrow returns to the first step, closing the loop — no terminal endpoint" |
| Nodes unevenly spaced | Position rule omitted | "N nodes spaced at perfectly equal intervals around the perimeter (clock positions: 12, 4, 8 for 3 nodes; 12, 3, 6, 9 for 4; etc.)" |
| Center too busy | Anchor element overgrown | "Center holds at most one small anchor element occupying under 10% of canvas area" |
| Arrows ambiguous direction | Direction not stated | "Curved directional arrows clearly point clockwise (or counterclockwise — specify one), arrowhead visible at each arrival point" |
| Too many or too few steps | Step count drifted | Explicitly state "exactly N step nodes" |

---

## 6. When to switch away from cycle

- If process is **linear with a defined end** → `flowchart`
- If structure is **central hub with passive satellites** (no motion around perimeter) → `framework`
- If two states compared (before/after) → `comparison`
- If chronological progression along an axis → `timeline`
- If tiered / layered → `pyramid`
