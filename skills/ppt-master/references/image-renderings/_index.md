# Renderings — Index

A **rendering** is a visual style family: line quality, texture, depth, material, mood. Lock one rendering per deck — every AI image in the deck shares it.

> **HEX values are not in renderings**. The deck's HEX triplet comes from `design_spec.colors`. Rendering describes *how* the image is drawn; palette describes *how* the HEX values are distributed. See [`image-generator.md`](../image-generator.md) §2.

---

## 1. Catalog (20 renderings)

Each rendering has its own file with: style paragraph, line / texture / depth notes, deck HEX usage, and a fewshot prompt snippet. **Read only the file for the rendering you pick** — never glob the directory.

### 1.1 Modern / commercial (the corporate-PPT main field)

| Rendering | One-liner | Best for |
|---|---|---|
| [`vector-illustration`](./vector-illustration.md) | Clean flat vector with bold shapes, no gradients | Consulting / SaaS / general professional decks |
| [`flat`](./flat.md) | Modern geometric blocks, slightly more design-forward than vector | Brand / product showcase decks |
| [`minimalist-swiss`](./minimalist-swiss.md) | Swiss-grid Bauhaus austerity, aggressive whitespace | High-end consulting / architecture / luxury / type foundries |
| [`glassmorphism`](./glassmorphism.md) | Frosted-glass translucent panels, soft shadows | Modern SaaS / fintech / health-tech / premium apps |
| [`3d-isometric`](./3d-isometric.md) | Isometric 3D forms with subtle shadows | Tech architecture / product structure |
| [`digital-dashboard`](./digital-dashboard.md) | Polished UI / data-viz aesthetic | SaaS demos / data products |
| [`corporate-photo`](./corporate-photo.md) | Editorial photography, real subjects | Team / lifestyle / product shots |
| [`blueprint`](./blueprint.md) | Technical schematic with grid, monospace cues | Architecture / engineering / AI systems |
| [`editorial`](./editorial.md) | Magazine-style infographic look | Finance / journalism / explainers |

### 1.2 Hand-drawn / educational

| Rendering | One-liner | Best for |
|---|---|---|
| [`sketch-notes`](./sketch-notes.md) | Warm cream paper, black hand-drawn lines, pastel fills | Education / training / onboarding |
| [`ink-notes`](./ink-notes.md) | Pure white, black ink, sparse semantic color | Methodology / Before-After / manifestos |
| [`chalkboard`](./chalkboard.md) | Chalk on board, classroom feel | Teaching / tutorials / classroom decks |
| [`paper-cut`](./paper-cut.md) | Layered paper craft, scissor-cut edges, soft shadows | Education / children / cultural / festival / sustainability |

### 1.3 Narrative / atmospheric

| Rendering | One-liner | Best for |
|---|---|---|
| [`watercolor`](./watercolor.md) | Painterly soft edges, color bleeding | Lifestyle / travel / brand story |
| [`warm-scene`](./warm-scene.md) | Golden-hour cinematic warmth | Personal growth / origin story |
| [`screen-print`](./screen-print.md) | Halftone poster art, 2-5 flat colors | Cultural / media / cinematic covers |
| [`vintage-poster`](./vintage-poster.md) | Mid-century modern poster, halftone + paper grain | Cultural / brand heritage / hospitality / anniversaries |

### 1.4 Specialty

| Rendering | One-liner | Best for |
|---|---|---|
| [`fantasy-animation`](./fantasy-animation.md) | Ghibli/Disney hand-drawn warmth | Children / storybook / brand fable |
| [`pixel-art`](./pixel-art.md) | 8-bit retro game aesthetic | Gaming / retro tech / nostalgic |
| [`nature`](./nature.md) | Organic earthy illustration | Environment / wellness / sustainability |

---

## 2. Auto-selection table — `design_spec` → rendering

Match `design_spec.md d. Style` (mode + descriptor) against this table. First match wins. If no row matches, default to `vector-illustration`.

| `d. Style` signal | Recommended rendering | Alternates |
|---|---|---|
| Top Consulting / strategic / MBB | `editorial` or `vector-illustration` | `blueprint`, `minimalist-swiss` |
| General Consulting / corporate report | `vector-illustration` | `flat`, `digital-dashboard` |
| High-end consulting / luxury / 高端 / design-firm | `minimalist-swiss` | `editorial`, `vector-illustration` |
| Tech / SaaS / AI / system / architecture | `3d-isometric`, `blueprint`, or `digital-dashboard` | `flat`, `vector-illustration` |
| Modern SaaS / fintech / health-tech / premium app | `glassmorphism` | `digital-dashboard`, `flat` |
| Product launch / brand / marketing | `flat`, `3d-isometric`, or `corporate-photo` | `vector-illustration` |
| Education / training / onboarding / 教学 | `sketch-notes` | `vector-illustration` (if school is corporate), `paper-cut` |
| Children / story / storybook / 儿童 | `fantasy-animation` | `paper-cut`, `watercolor`, `sketch-notes` |
| Cultural / folk / festival / 文化 / 节日 | `paper-cut` | `vintage-poster`, `screen-print` |
| Methodology / Before-After / manifesto / 方法论 | `ink-notes` | `editorial` |
| Government / formal / official report | `editorial` or `corporate-photo` | `vector-illustration` |
| Finance / data journalism / 财经 | `editorial` or `digital-dashboard` | `vector-illustration` |
| Personal story / 个人成长 / lifestyle | `watercolor`, `warm-scene` | `corporate-photo`, `paper-cut` |
| Cultural / media / opinion / cinematic | `screen-print`, `vintage-poster` | `editorial`, `warm-scene` |
| Brand heritage / hospitality / 老字号 / 周年 | `vintage-poster` | `screen-print`, `editorial` |
| Gaming / retro / 8-bit / 复古 | `pixel-art` | `vintage-poster` |
| Environment / wellness / 环保 / 户外 | `nature` | `watercolor`, `paper-cut` |
| Classroom / blackboard / 课堂 | `chalkboard` | `sketch-notes` |
| Team / company / product photo | `corporate-photo` | — |

---

## 3. How to use

1. From `design_spec.md` extract `d. Style` mode + descriptor.
2. Find the matching row above; pick the primary recommendation.
3. `read_file image-renderings/<chosen>.md`.
4. Apply its style paragraph when assembling each prompt per [`image-generator.md`](../image-generator.md) §4.

**Lock for the whole deck.** Don't change rendering between images in the same deck.
