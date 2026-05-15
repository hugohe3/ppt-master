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

## 3. Using the deck's HEX values

- Primary HEX: main schematic lines and primary boxes
- Secondary HEX: background (often near-white, or very pale blue if a blueprint mood is wanted)
- Accent HEX: highlighted path / warning / focus element
- Optional grid: secondary HEX at 5-8% opacity

---

## 4. Fewshot prompt snippets

**Snippet A — half-page system architecture, text_policy: none**

> Technical blueprint schematic. Six rounded rectangles arranged in a clean two-row layout, connected by precise straight lines with small arrow heads. All rectangles use crisp 1.5px uniform stroke in primary deep blue `#1E40AF` on a near-white secondary background `#FAFAFA`. A subtle grid pattern in primary blue at 6% opacity provides a schematic feel. One rectangle is highlighted by replacing its stroke with accent orange `#F97316` — the focus component. Each rectangle contains a single simple iconic symbol — a database cylinder, a gear, a chat bubble, an upward arrow, a lock, a network node — rendered in the same primary blue, no fill. Connector lines route at right angles, with small dot anchors at junctions. Composed as a 600×500 half-page block with 14% inner padding. NO text, no labels, no numbers — pure schematic structure. Color values are rendering guidance only.