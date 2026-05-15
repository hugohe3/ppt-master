# Rendering: blueprint

Technical schematic aesthetic — clean lines on a grid, monospace cues, restrained color. Conveys engineering precision and analytical depth. Used for architecture diagrams, AI systems, engineering decks, technical deep-dives.

## 1. Style paragraph (paste-ready, 95 words)

> Technical blueprint schematic style. Clean precise lines on an implied or subtle grid, with deliberate geometric rigor — right angles, parallel rules, measured spacing. Elements are simplified to essential schematic forms — boxes, rounded rectangles, connector lines, anchor dots, callout markers. Color is restrained, often near-monochrome with one or two semantic accents (one color for "primary path", one for "alternate" or "warning"). Optional subtle grid background at very low opacity (5-8%) reinforces the schematic feel. No textures, no shading, no painterly artifacts. Overall feel is engineering-precise, analytical, intentional — common in system design and architecture briefings.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Crisp uniform stroke, often 1-1.5px feel; perfectly straight or precisely curved |
| Texture | None; optional very-low-opacity grid background |
| Depth | Flat — schematic, not perspectival |
| Material | None — abstract schematic |
| Mood | Analytical, engineering-precise, restrained |

---

## 3. Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page architecture | 600×500 | ~1.2 | 12-15% |
| Hero system diagram | 1200×500 | 2.4:1 | 12% |
| Square component | 700×700 | 1:1 | 15% |
| Spot schematic | 400×400 | 1:1 | 12% |

---

## 4. Using the deck's HEX values

- Primary HEX: main schematic lines and primary boxes
- Secondary HEX: background (often near-white, or very pale blue if a blueprint mood is wanted)
- Accent HEX: highlighted path / warning / focus element
- Optional grid: secondary HEX at 5-8% opacity

---

## 5. Fewshot prompt snippets

**Snippet A — half-page system architecture, text_policy: none**

> Technical blueprint schematic. Six rounded rectangles arranged in a clean two-row layout, connected by precise straight lines with small arrow heads. All rectangles use crisp 1.5px uniform stroke in primary deep blue `#1E40AF` on a near-white secondary background `#FAFAFA`. A subtle grid pattern in primary blue at 6% opacity provides a schematic feel. One rectangle is highlighted by replacing its stroke with accent orange `#F97316` — the focus component. Each rectangle contains a single simple iconic symbol — a database cylinder, a gear, a chat bubble, an upward arrow, a lock, a network node — rendered in the same primary blue, no fill. Connector lines route at right angles, with small dot anchors at junctions. Composed as a 600×500 half-page block with 14% inner padding. NO text, no labels, no numbers — pure schematic structure. Color values are rendering guidance only.

**Snippet B — hero pipeline diagram, text_policy: none**

> Technical blueprint pipeline schematic, banner format. Five rounded rectangle stages arranged horizontally across the canvas, connected by precise arrow-headed lines. All stages use 1.5px primary teal `#0F766E` stroke on a near-white background `#FAFAFA`. The third stage (center) is rendered with accent gold `#D4AF37` stroke as the focal stage. A subtle 6%-opacity grid background reinforces the schematic feel. Small anchor dots at every line junction. Each stage contains one iconic symbol — input arrow, gear, magnifier, transform symbol, output arrow — in monoline schematic style. Composed for a 1200×500 hero band with 12% inner padding. NO text or labels anywhere. Color values are rendering guidance only.

---

## 6. Forbidden

- Realistic textures or materials
- Decorative flourishes — blueprint is intentionally austere
- More than 2 accent colors — restraint is the aesthetic
- Cluttered diagrams (>8 components)

---

## 7. When to switch away

- For 3D depth on technical visuals → `3d-isometric`
- For product UI / dashboard surfaces → `digital-dashboard`
- For brand-aware design rather than technical schematic → `flat` or `vector-illustration`
