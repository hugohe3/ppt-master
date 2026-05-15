# Type Templates — Index

A **type** describes what the image's **internal composition** looks like — its layout skeleton. Type is decided **per image**, not per deck (one deck typically uses 2-5 different types).

> **Type vs PPT page layout — important**: type describes the composition *inside* the AI image block. The PPT slide's overall layout (where the image sits, how SVG text wraps around it) is a separate decision made by Strategist and Executor. Type only governs what's inside the rectangle the model paints.
>
> **Type is orthogonal to `page_role`**: every type's container guidance assumes `page_role: local` (region block on an SVG page). When promoted to `page_role: hero_page`, the same type's composition fills the slide with SVG kept minimal above. See [`image-generator.md`](../image-generator.md) §1.

---

## 1. Catalog (15 types)

Each type has its own file with: composition skeleton (LAYOUT / ELEMENTS / NEGATIVE SPACE), text-policy variants, and a fewshot prompt snippet.

| Type | Internal composition | Typical use |
|---|---|---|
| [`background`](./background.md) | Atmospheric backdrop, no central subject | Cover bg, chapter divider bg, hero overlay bg |
| [`hero`](./hero.md) | Single dominant subject (60-70% of canvas) | Product/concept reveal, chapter title bg |
| [`portrait`](./portrait.md) | One person headshot / upper body, neutral background | Team page / speaker bio / testimonial / founder profile |
| [`typography`](./typography.md) | Large headline / number / single word as visual | Big-stat pages, slogan pages, chapter openers |
| [`infographic`](./infographic.md) | 2-5 ordered zones with icons + minimal labels | Data summary / step list / KPI rundown |
| [`flowchart`](./flowchart.md) | Sequential blocks connected by arrows | Process / workflow / pipeline |
| [`framework`](./framework.md) | Central node + radiating satellites | Methodology / model / system architecture |
| [`matrix`](./matrix.md) | 2×2 quadrant grid with two perpendicular axes | SWOT / BCG / Eisenhower / Ansoff / Porter |
| [`cycle`](./cycle.md) | Closed loop, 3-6 steps with arrows returning | PDCA / flywheel / design thinking / continuous improvement |
| [`funnel`](./funnel.md) | Top-wide bottom-narrow conversion stack | Marketing funnel / sales pipeline / hiring funnel |
| [`pyramid`](./pyramid.md) | Bottom-wide top-narrow hierarchical tiers | Maslow / capability stack / value hierarchy |
| [`comparison`](./comparison.md) | Split composition (left vs right, before vs after) | A/B / pros-cons / Before-After |
| [`timeline`](./timeline.md) | Linear progression along an axis | History / roadmap / evolution |
| [`map`](./map.md) | Stylized geographic outline with annotated markers | Offices / market presence / regional data / supply chain |
| [`scene`](./scene.md) | Atmospheric environment with narrative | Story / lifestyle / case study |

---

## 2. Auto-selection — per-image `Purpose` → type

For each row in `design_spec.md §VIII Image Resource List`, match `Purpose` against this table.

| `Purpose` keyword | Type |
|---|---|
| Cover background / chapter background / divider bg | `background` |
| Product reveal / hero / headline visual | `hero` |
| Team headshot / speaker bio / founder profile / testimonial | `portrait` |
| Big number / KPI single visual / quote | `typography` |
| Data summary / metrics rundown / step list | `infographic` |
| Process / workflow / pipeline / steps with arrows | `flowchart` |
| Methodology / model / framework / architecture diagram | `framework` |
| 2×2 quadrant / SWOT / BCG / Eisenhower / Ansoff | `matrix` |
| Closed-loop process / PDCA / flywheel / continuous improvement | `cycle` |
| Conversion funnel / sales pipeline / hiring funnel | `funnel` |
| Hierarchy / Maslow / value stack / capability layer | `pyramid` |
| Comparison / Before-After / A/B / VS | `comparison` |
| History / evolution / roadmap / timeline | `timeline` |
| Offices / market presence / regions / supply chain / geography | `map` |
| Team / lifestyle / story / scenario / case | `scene` |

`text_policy` and `page_role` are decided per image — see each type file's variants section and the page's communication goal.

---

## 3. Default container sizes (when not specified by Image Resource List)

The Resource List's `Dimensions` column is authoritative. If absent, use these defaults for prompt assembly:

| Type | Default container | Aspect ratio |
|---|---|---|
| background | 1280×720 full-bleed; `page_role: local` when SVG text overlays on top, `page_role: hero_page` when image alone is the page | 16:9 |
| hero | 800×600 or 1280×720 | 4:3 / 16:9 |
| portrait | 400×500 or 600×800 | 4:5 / 3:4 |
| typography | 800×500 | 16:10 |
| infographic | 600×500 or 700×700 | ~1.2 / 1 |
| flowchart | 1200×400 (horizontal banner) | 3:1 |
| framework | 700×700 square | 1:1 |
| matrix | 800×800 or 1280×720 | 1:1 / 16:9 |
| cycle | 700×700 or 800×800 square | 1:1 |
| funnel | 600×800 portrait | 3:4 |
| pyramid | 600×800 portrait | 3:4 |
| comparison | 1200×500 split / 600×500 each | 2.4 / 1.2 |
| timeline | 1200×350 banner | 3.4:1 |
| map | 1280×720 or 1200×500 | 16:9 / 2.4:1 |
| scene | 1200×720 wide / 800×600 | 16:10 / 4:3 |

---

## 4. How to use

1. Pick the type per row in the Image Resource List using the table above.
2. `read_file image-type-templates/<type>.md` — only the types actually used in this deck. Most decks use 2-4 types; load each at most once.
3. Apply the type's composition skeleton when assembling the prompt, alongside the locked deck-wide rendering and palette.

**Multiple types per deck is normal.** Locking is at rendering + palette level, not type level.
