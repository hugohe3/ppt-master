# Renderings — Index

A **rendering** is a visual style family: line quality, texture, depth, material, mood. Lock one rendering per deck — every AI image in the deck shares it.

> **HEX values are not in renderings.** Rendering describes how the image is drawn. The new flow starts from the deck's core color anchors in `spec_lock.md colors` and interprets them with the Design Spec/image context; it does not ask for or author a separate image palette. See [`image-generator.md`](../image-generator.md) §2.

> **Core deck identity has precedence.** Any sample HEX inside an individual rendering file is illustrative legacy prose. Prompt assembly replaces identity roles with the current deck anchors, then may derive coherent tints, light/shadow transitions, material colors, and atmospheric hues from the rendering and image context. Do not replace the deck identity with an unrelated palette. When one derived tone becomes a reusable semantic role across images/pages, promote it to a named lock row.

---

## 1. Catalog (20 renderings)

Each rendering has its own file with: style paragraph, line / texture / depth notes, deck HEX usage, and a fewshot prompt snippet. A preset lock reads that one file. A catalog-based `custom` reads every preset named in `image_rendering_references`; a novel `custom` may omit references. Never glob the directory.

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

### 1.5 Escape hatch — `custom`

Whenever proposed image usage includes `ai`, Stage 2 authors one separate, visible custom rendering proposal in addition to the preset cards. It uses `rendering: custom` plus a complete behavior paragraph, remains initially unselected, and enters the confirmed contract only when the user chooses it. A template-backed proposal must honor inherited identity and the confirmed template-application plan.

**Hard rule — `rendering_behavior` prose**:

| Rule | Value |
|---|---|
| Length | One paragraph, 2-5 sentences |
| Axes covered | line / texture / depth / material / mood (same as preset files) |
| Catalog basis | When existing renderings are combined or borrowed, name every exact id and read every named file before synthesis |

```yaml
- image_rendering: custom
- image_rendering_behavior: "Hand-screened poster aesthetic — slightly misregistered halftone overlays, 3 flat ink colors with visible dot pattern at 12% opacity, no gradients, no anti-aliased edges; reads as silkscreen print."
```

**Hard rule**: the custom candidate is mandatory when AI images are proposed; selecting `custom` is a tail-case, not the default. See [`strategist-image.md`](../strategist-image.md) for the Stage-2 carrier and downstream lock behavior.

Write `image_rendering_references` only when the custom direction actually uses catalog material. Keep the list exact: a blend of `screen-print` and `watercolor` reads both files and lists both ids. A genuinely new rendering with no catalog source omits the field and proceeds from its standalone behavior; never invent a reference merely to legitimize `custom`.

---

## 2. Auto-selection table — `design_spec` → rendering

Match `design_spec.md d` (mode + `visual_style`) against this table. First match wins. **No row matches** → use `custom` per §1.5 rather than force-fitting `vector-illustration`. (When the locked `visual_style` names a paired rendering, prefer that for aesthetic alignment.)

| `d. Style` signal | Recommended rendering | Alternates |
|---|---|---|
| Strategic / MBB / board | `editorial` or `vector-illustration` | `blueprint`, `minimalist-swiss` |
| Corporate report / analysis | `vector-illustration` | `flat`, `digital-dashboard` |
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
3. For a preset, read `image-renderings/<chosen>.md`. For `custom`, read every file named in `image_rendering_references`, then synthesize them under the confirmed behavior; with no references, use the novel behavior directly. Apply the result when assembling prompts per [`image-generator.md`](../image-generator.md) §4.

**Lock for the whole deck.** Don't change rendering between images in the same deck.
