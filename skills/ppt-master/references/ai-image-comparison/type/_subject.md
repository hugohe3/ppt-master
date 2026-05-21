# Type Comparison Set

## Controlled variables

| Dimension | Value | Status |
|---|---|---|
| Type | **varies (11 types)** | under comparison |
| Rendering | `vector-illustration` | fixed baseline |
| Palette | `cool-corporate` | fixed baseline |

> The 11 types here are the **internal geometric skeletons** for `page_role: local` infographic blocks. `page_role: hero_page` images don't pick a type — they use the four composition primitives in [`image-generator.md`](../../image-generator.md) §4.1 instead (single-subject / portrait / typographic / atmospheric), so they don't appear in this comparison set.

## Subject theme

> "Team scaling a business — collaboration, growth, structure"

This abstract theme is chosen deliberately. Each type interprets it through a **completely different composition**, which is precisely the value of the type comparison:

| Type | How the same theme renders under this type |
|---|---|
| infographic | Four KPI zones: team / product / customer / revenue |
| flowchart | Sequential arrows: idea → team → product → customer → growth |
| framework | Central business node + 4 radiating satellites (team / product / customer / growth) |
| matrix | 2×2 quadrant grid with team / product / customer / growth icons |
| cycle | Closed-loop: build → ship → learn → scale, arrows returning to start |
| funnel | 4 narrowing bands: awareness → interest → engagement → conversion |
| pyramid | 4 narrowing-upward tiers: culture → team → product → growth |
| comparison | Split: small team vs scaled team (before / after) |
| timeline | Time axis: Year 1 → Year 2 → Year 3 → Year 5 |
| map | Stylized world map with office markers and collaboration arcs |
| scene | Narrative scene of team collaboration in a meeting room |

## Baseline HEX (cool-corporate)

- Primary `#1E3A5F` deep navy
- Secondary `#F8F9FA` off-white
- Accent `#D4AF37` gold

## Aspect ratios

Each type uses its own "natural container shape" (see the default container table in `image-type-templates/_index.md`):

| Type | Aspect ratio | Container character |
|---|---|---|
| infographic | 4:3 | Square-ish info block |
| flowchart | 21:9 | Horizontal banner |
| framework | 1:1 | Square radial |
| matrix | 1:1 | Square quadrant grid |
| cycle | 1:1 | Square closed loop |
| funnel | 3:4 | Portrait converging-down stack |
| pyramid | 3:4 | Portrait converging-up tiers |
| comparison | 21:9 | Wide split banner |
| timeline | 21:9 | Long horizontal axis |
| map | 16:9 | Wide geographic frame |
| scene | 4:3 | Scene-format frame |

## Naming convention

Each filename is `<type>.png`, matching the corresponding file under `references/image-type-templates/`.

## How to read this set

Scan all 11 images side by side. Focus on:

- **Internal composition skeleton** — central / sequential / radiating / symmetrical / tiled / axis-aligned
- **Subject density and distribution**
- **Visual relationships between elements** — connecting / parallel / nested / progressive
- **Intuitive use-case fit** — which best fits "process content", "comparison content", "data content"
