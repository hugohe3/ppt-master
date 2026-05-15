# Rendering: 3d-isometric

Isometric 3D forms with controlled depth — boxes, layers, devices, stacks rendered in 30°/30°/30° projection. The dominant choice for tech architecture, product structure, and system composition visuals in modern decks.

## 1. Style paragraph (paste-ready, 105 words)

> 3D isometric illustration with clean geometric forms rendered in true 30°/30°/30° projection. All edges are crisp and uniform — no perspective distortion, no vanishing points. Surfaces use flat solid fills with subtle tonal shifts (a single darker shade for shadowed faces, ~15% darker than the light-facing face) to convey volume without painterly rendering. Edges may have thin uniform outlines or use direct color contrast. Composition emphasizes stackable, modular forms — boxes, blocks, layers, cards floating in arrangement. Soft 8% drop shadows beneath floating elements anchor them in space. Overall feel is technical, structured, contemporary — common in SaaS product diagrams, cloud architecture visuals, system component breakdowns.

---

## 2. Line, texture, depth

| Aspect | Treatment |
|---|---|
| Line quality | Thin uniform edges, or no edges relying on color contrast |
| Texture | None on surfaces — flat fills |
| Depth | True isometric projection (30°/30°/30°), tonal shading on shadowed faces, optional 8% drop shadow under floating elements |
| Material | Flat with tonal shading — not glossy, not photorealistic |
| Mood | Technical, modular, contemporary |

---

## 3. Container sizing for local PPT inserts

| Position | Canvas | Aspect | Padding |
|---|---|---|---|
| Half-page architecture visual | 600×500 | ~1.2 | 15% |
| Hero technical diagram | 1200×500 | 2.4:1 | 12% |
| Square component breakdown | 700×700 | 1:1 | 15% |
| Spot illustration | 400×400 | 1:1 | 12% |

---

## 4. Using the deck's HEX values

- Primary HEX: main block face fills (the "lit" face)
- Secondary HEX: background field
- Accent HEX: a single highlighted block or connecting line
- Shadowed faces: ~15% darker shade of the primary (automatic from prompt phrasing — no extra HEX needed)

---

## 5. Fewshot prompt snippets

**Snippet A — half-page system architecture, text_policy: none**

> 3D isometric illustration in true 30°/30°/30° projection. Three stacked blocks rise from a clean isometric plane — a wide foundation block in primary deep blue `#1E40AF`, a medium block in slightly darker blue stacked on top, and a smaller block on top of that. To the right, two floating cards in the same blue family hover above the stack, connected by thin diagonal lines. The "lit" faces of all blocks use the primary blue; the shadowed faces use a 15% darker tonal shift of the same blue. Accent gold `#D4AF37` appears as one thin line connecting the top block to a floating card. Background is calm secondary `#F8FAFC`. Soft 8% drop shadows beneath the floating cards. Composed as a 600×500 half-page block with 15% inner padding. NO text, no labels, no numbers anywhere in the image. Color values are rendering guidance only.

**Snippet B — hero technical banner, text_policy: none**

> 3D isometric illustration banner showing a modular cloud architecture. Five rounded-edge cards arranged in a horizontal flow across the canvas, each card a distinct 3D volume in true 30°/30°/30° projection. Cards alternate in primary teal `#0F766E` and a 15% darker tonal shade for shadowed faces. Thin connecting lines in accent orange `#F97316` indicate dataflow between cards. Background plane in soft secondary `#F1F5F9`. Soft 8% drop shadows ground each card. Each card contains a single simple iconic symbol on its top face — a database cylinder, a gear, an upward arrow, a cloud silhouette, a lock — rendered in white. Composed for a 1200×500 hero band with 12% inner padding. NO text, letters, numbers anywhere. Color values are rendering guidance only.

---

## 6. Forbidden

- True perspective (1-point or 2-point) — isometric is parallel projection by definition
- Realistic lighting / specular highlights — keep it flat-shaded
- More than 5-6 distinct objects in one image — isometric loses clarity with clutter
- Mixed projection angles in the same image

---

## 7. When to switch away

- For utility illustrations without depth → `vector-illustration`
- For dashboards / UI surfaces → `digital-dashboard`
- For abstract schematics rather than 3D forms → `blueprint`
