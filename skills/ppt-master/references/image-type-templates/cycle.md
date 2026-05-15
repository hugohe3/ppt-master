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

## 2. Text-policy variants

### 3.1 `text_policy: none`

Each step shows an icon only; step labels are handled in SVG.

Sample fragment:

> NO text, letters, numbers, or step labels in the image. Each step node contains only one simple iconic symbol; SVG text overlay will add step names externally.

### 3.2 `text_policy: embedded`

Self-contained cycle diagram with step names typeset into the artwork. Keep step names to single English words ("PLAN", "DO", "CHECK", "ACT") in a font family echoing the deck's body typography.

---

## 3. Fewshot prompt snippets

**Snippet A — vector-illustration + cool-corporate PDCA cycle, text_policy: none, 700×700**

> Clean flat vector illustration of a closed-loop process cycle. Four step nodes arranged in a perfect circle on the canvas perimeter — at 12 o'clock, 3 o'clock, 6 o'clock, and 9 o'clock positions. Each node is a rounded square (about 130×130px equivalent) filled with primary deep navy `#1E3A5F`, with one simple white iconic symbol centered inside — a clipboard (plan), a hand (do), a magnifying glass (check), a gear (act). Curved directional arrows in accent gold `#D4AF37` connect each node to the next going clockwise, closing the loop. The center of the circle is calm — secondary light gray `#F8F9FA` field with one small accent gold dot at the exact center as the cycle's anchor. Crisp 2px outlines, soft 8% drop shadow under each node. Composed as a 700×700 half-page cycle block with 15% padding. NO text, letters, or step labels anywhere — SVG will overlay all step names. Color values are rendering guidance only.