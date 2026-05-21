# Type Templates — Index

A **type** describes the **internal geometric composition skeleton** of a local infographic image block — what the layout looks like *inside the rectangle the model paints*. Type is decided **per image**, not per deck (one deck typically uses 2-4 different types).

## What Type *is* and *is not*

**Type *is*** — the geometric skeleton of a local infographic block. Each type has a non-interchangeable layout structure: a 2×2 grid is not a closed loop; an upward-narrowing pyramid is not a top-wide funnel; a linear timeline is not a sequential flowchart. The skeleton constrains where elements go.

**Type *is not***:

- *not* "what this image is for in the PPT page" — that's `page_role` (`local` vs `hero_page`, see [`image-generator.md`](../image-generator.md) §1)
- *not* "what subject occupies the image" — single subject, single person, big number, no subject: these are all expressible through §4.1 hero-page primitives or natural-language prompt description, not through types
- *not* a high-level asset category — the row's `Purpose` + `Reference` columns in `design_spec.md §VIII` already carry that, no separate vocabulary needed

**When to skip type entirely** — when `page_role: hero_page` (the image is the page's main voice: cover, chapter divider, mood transition, signature stat, closing quote), do **not** pick a type. Instead describe the composition directly using the four primitives in [`image-generator.md`](../image-generator.md) §4.1 (single-subject / portrait / typographic / atmospheric). The 11 types below are for local infographic blocks only.

---

## 1. Catalog (11 types)

Each type has its own file with: composition skeleton (LAYOUT / ELEMENTS / NEGATIVE SPACE), text-policy variants, and a fewshot prompt snippet.

| Type | Internal composition | Typical use |
|---|---|---|
| [`infographic`](./infographic.md) | 2-5 parallel ordered zones with icons + minimal labels | Data summary / step list / KPI rundown |
| [`flowchart`](./flowchart.md) | Sequential blocks connected by directional arrows | Process / workflow / pipeline |
| [`framework`](./framework.md) | Central node + radiating satellites (hub-spoke) | Methodology / model / system architecture |
| [`matrix`](./matrix.md) | 2×2 quadrant grid with two perpendicular axes | SWOT / BCG / Eisenhower / Ansoff / Porter |
| [`cycle`](./cycle.md) | Closed loop, 3-6 steps with arrows returning to start | PDCA / flywheel / design thinking / continuous improvement |
| [`funnel`](./funnel.md) | Top-wide bottom-narrow conversion stack | Marketing funnel / sales pipeline / hiring funnel |
| [`pyramid`](./pyramid.md) | Bottom-wide top-narrow hierarchical tiers | Maslow / capability stack / value hierarchy |
| [`comparison`](./comparison.md) | Symmetric split (left vs right, before vs after) | A/B / pros-cons / Before-After |
| [`timeline`](./timeline.md) | Linear axis with milestone markers | History / roadmap / evolution |
| [`map`](./map.md) | Stylized geographic outline with annotated markers | Offices / market presence / regional data / supply chain |
| [`scene`](./scene.md) | Atmospheric environment with narrative | Story / lifestyle / case study |

---

## 2. Auto-selection — per-image `Purpose` → type

For each row in `design_spec.md §VIII Image Resource List` where `page_role: local`, match `Purpose` against this table.

| `Purpose` keyword | Type |
|---|---|
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
| Team / lifestyle / story / scenario / case (group, with environment) | `scene` |
| Cover / chapter divider / mood transition / big number / hero quote / single-subject hero / single-person headshot | **No type — use `page_role: hero_page` + [`image-generator.md`](../image-generator.md) §4.1 primitives** |

`text_policy` and `page_role` are decided per image — see each type file's variants section and the page's communication goal.

---

## 3. Default container sizes (when not specified by Image Resource List)

The Resource List's `Dimensions` column is authoritative. If absent, use these defaults for prompt assembly:

| Type | Default container | Aspect ratio |
|---|---|---|
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

For `page_role: hero_page` images, default container is the slide canvas (e.g. 1280×720 for 16:9) — see §4.1 primitives in [`image-generator.md`](../image-generator.md).

---

## 4. How to use

1. For each `page_role: local` row in the Image Resource List, pick the type using the auto-selection table above.
2. For each `page_role: hero_page` row, **skip type selection** — go straight to [`image-generator.md`](../image-generator.md) §4.1 primitives.
3. `read_file image-type-templates/<type>.md` — only the types actually used in this deck. Most decks use 2-4 types; load each at most once.
4. Apply the type's composition skeleton when assembling the prompt, alongside the locked deck-wide rendering and palette.

**Multiple types per deck is normal.** Locking is at rendering + palette level, not type level.
