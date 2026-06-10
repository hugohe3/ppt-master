# Native Diagram Library

Reusable, **natively editable** DrawingML diagrams lifted verbatim from existing
`.pptx` decks. This library is the answer to "I have a beautiful diagram in a
PowerPoint file — keep it pixel-identical AND keep it editable in new decks."

## Why this is not the SVG path

The SVG import path (`pptx_to_svg.py` → `svg_to_pptx.py`) re-renders a diagram as
SVG and back. That works for clean structural diagrams but **degrades elaborate
flourishes** — bezier flow arrows, halftone dot patterns, multi-stop gradient 3D
shading can simplify or drop, because they round-trip through a different format.

A *native diagram* skips SVG entirely. The original `<p:sp>` / `<p:grpSp>` XML is
kept byte-for-byte, so it renders **exactly** like the source and stays a set of
native PowerPoint shapes you can click, recolor, and restyle. The only transform
is **theme flattening** (see below) so it survives moving to a deck with a
different theme.

## Source of truth & selection schema

[`diagrams_index.json`](./diagrams_index.json) is `{ meta, diagrams }` (like
`charts_index.json`), for AI selection in a single pass (regenerate with
`scripts/build_diagram_index.py`).

**`meta`** holds pack-level facts, the most important being: the diagrams' **3D
depth is a content-presentation choice (it conveys layers / hierarchy /
convergence), NOT a deck-wide style requirement** — recolored, a diagram drops
into any deck as one element. It also states they work **full-slide OR as an
in-page region** (via `data-native-diagram` x/y/w/h), and the two `recolor_base`
hexes to remap onto the deck palette.

**`diagrams`** — one entry per component:

| Field | The question it answers |
|---|---|
| `type` | relationship/form — primary selector (`framework`/`funnel`/`pyramid`/`layered-platform`/`isometric-stack`/`matrix`/`cycle`/`list-row`/`timeline`) |
| `subform` | the specific variant within a type (e.g. `convergence vortex hub` vs `central sphere + orbiting satellites`) — what discriminates same-type entries |
| `scenario` | **content-first** — the business content it serves (capability map / maturity model / platform stack / roadmap / two-sided platform …); the entry point a PPT expert selects by |
| `use` | the underlying relationship (hierarchy / convergence / comparison / composition / relationship / cycle / process) |
| `slots` / `slot_of` | capacity + the parallel grain: `slot_of` = `columns` (N-栏) / `tiers` / `layers` / `spokes` / `cells` — i.e. "几栏/几层/几辐" is read off `slot_of` |
| `holds` | content form per slot: `short-label` / `label+short-desc` / `label+desc` / `label+items` |
| `footprint` | region shape it needs (visual pass): `wide-band` / `tall-center` / `centered-compact` / `full-bleed` — answers *where on the slide* it can go |
| `density` | how small it can shrink and stay legible (from real shape count): `low` = small in-page element · `medium` = half-slide · `high` = needs most of the slide |
| `text_load` | overall copy it carries: `light` / `medium` / `heavy` — page-rhythm fit (breathing vs dense) |
| `motif` | node vocabulary: `sphere` / `card` / `cube` / `ring` / `tower` / `pyramid` / `mixed` — for element cohesion with the deck |
| `aspect` | source aspect (16:9) |
| `distinct` / `pick` | `distinct` = one-line visual description; `pick` = selection rule that **differentiates within the type** and cross-references siblings |
| `conf` | `refined` (hand-verified, trust) · `high` (studied) · `approx` (contact-sheet read — refine on curation) |

> `footprint` / `text_load` / `motif` and the precise `slots` / `subform` / `distinct`
> are **visual properties** — populated only on entries that have been looked at
> (`conf: refined`). The bulk `approx` entries carry type-level defaults until
> curated. See `references/native-diagrams.md` §2 for how they drive selection.

There is **no style gate** — fit is a soft aesthetic call, not a hard deck
requirement. Selection = content relationship (`type`/`use`) × item count
(`slots`) × content-per-slot (`holds`), placed full-slide or as a region within
the `density` limit. Non-diagram slides (cover / notice / pure table) are
`selectable: false`. `type` is a visual-pass classification and `slots` is
coarse; both are refined during curation.

## Component format

Each component is a directory `native_diagrams/<key>/`:

| File | Purpose |
|------|---------|
| `shapes.xml` | flattened top-level shapes wrapped in `<a:diagram>` — theme-independent, editable |
| `media/` | bitmaps the diagram references (only when present) |
| `meta.json` | provenance, canvas size, media rId map, flatten counts, and **`text_slots`** — every `<a:t>` run as `{id, text}` (document order; original text = the fill-in hint) for the `data-text` content-replacement mechanism |

**Theme flattening** resolves every `<a:schemeClr>` → `<a:srgbClr>` (through the
source master's `clrMap` + theme color scheme) and every `+mj-ea` / `+mn-lt` font
token → its concrete typeface. Gradient/3D modifier children (`lumMod` / `shade`
/ `tint` / …) are preserved, so the look is identical with zero theme dependency.

## Building the library

```bash
# 1) Extract a valuable diagram from a source deck (1-based slide number)
python3 scripts/extract_diagram.py <source.pptx> <slide_num> \
    -o templates/native_diagrams/<key> --key <key> \
    --summary "Pick for X. Skip if Y (use other_key)."

# 2) Register it (hand-edit diagrams_index.json — add a "<key>": { "summary": ... } entry)
```

## Using a diagram in a new deck

```bash
# Drop onto a new blank slide in a fresh deck
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx

# Append onto an existing deck (new blank slide)
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx --target deck.pptx

# Place into an existing slide, reframed into a rectangle (EMU; 914400 = 1 inch)
python3 scripts/inject_diagram.py templates/native_diagrams/<key> -o out.pptx \
    --target deck.pptx --slide 2 --into-existing --pos 914400,914400,10363200,5029200
```

## Using a diagram inside a generated deck (SVG placeholder)

Native diagrams are a first-class peer of `<use data-icon>` and `<image>` in the
SVG → DrawingML pipeline. The Executor draws a placeholder in the page SVG and
`svg_to_pptx` splices the named component in at conversion time — scaled to the
placeholder rect and optionally recolored to the deck palette:

```xml
<!-- the component is scaled into x/y/width/height; resolved to native shapes -->
<rect data-native-diagram="combo_product_system"
      data-recolor="558C5A=1E3A5F,122B87=D4AF37"
      x="140" y="120" width="1000" height="480" fill="none"/>
```

- `data-native-diagram` — the library `<key>`.
- `data-recolor` (optional) — `OLD=NEW,…` base-hex map (see "color" below); maps
  the diagram's accents onto the deck's `spec_lock` palette, 3D shading re-derived.
- The rect itself never renders — it is replaced by the spliced DrawingML. Give it
  `fill="none"` (optionally a dashed stroke) so the SVG preview shows the reserved
  region; the real diagram only materializes in the PPTX.

> Resolved by `svg_to_pptx/native_diagram_resolver.py`; string-spliced so the
> component's namespaces (`a`/`p`/`r`/`a14`/`a16`) stay byte-exact.

## Limits (v1)

- **Charts** (`graphicFrame` → chart part) are recorded in `meta['charts_unsupported']`
  and NOT lifted — chart parts carry their own data/embedding sub-parts. Use the
  SVG chart templates (`templates/charts/`) for data charts instead.
- A native diagram is a **frozen component**: place / recolor / relabel it, but the
  LLM does not redraw it. Decks needing free-form generated layouts use the SVG
  pipeline; this library is for reusing exact pre-designed diagrams.
- SVG-blip images (`<asvg:svgBlip>`) are uncommon in diagram packs; PNG/JPEG media
  are fully supported.

---

## 扁平政企/商务版式素材（flat collection · style=flat）

> 补 `solid3d_*`（3D）之外的**扁平商务版式**，适用更多 PPT 场景。均原生可编辑：`data-recolor` 把 `meta.recolor_base` 主色映射到本 deck 主/辅色，`data-text` 按 `meta.text_slots` 换内容。

| key | 类型 | 来源 | 用途 |
|-----|------|------|------|
| `tpl_model_spheres` | 多节点模型 | 紫模板 s96 | N 大渐变球 + 标签 + 要点列（阶段/能力模型）|
| `tpl_concentric_nodes` | 同心环节点 | 紫模板 s89 | N 个同心环圆 + 图标 + 描述（并列引擎/支柱）|
| `tpl_radial_ecosystem` | 中心辐射生态 | 紫模板 s62 | 中心主体 + N 放射节点 + 同心底盘（生态/覆盖）|
| `tpl_timeline_arrow` | 箭头时间轴 | 紫模板 s120 | 横向箭头 + 上下年节点（历程/路线图）|
| `tpl_snake_flow` | 蜿蜒长流程 | 紫模板 s73 | 6-10 步节点气泡连线 + 注释 |
| `tpl_dual_circle_radiate` | 双圆放射对比 | 蓝模板 s148 | 双大圆 + 01-N 放射要点 + 中心位（双主体目标/对比）|
| `tpl_beforeafter_flow` | 前后/问题-改进流 | 蓝模板 s21 | 横向大箭头 现状→改进 + 双侧 pill 要点 |
| `tpl_plan_circles` | 计划列表 + 支持圆 | 蓝模板 s24 | 编号计划列表 + 右侧 chip + 4 圆要素（工作计划页）|

> 含 `media:true` 的素材（dualpole / step / 双圆 / 前后流 / plan）带少量位图图标，已随组件复制到各自 `media/`。

### 第二批补充（矩阵 / 漏斗 / 进度 / 数据墙）

| key | 类型 | 来源 | 用途 |
|-----|------|------|------|
| `tpl_swot_quadrant` | SWOT 四象限 | 蓝模板 s111 | 优势/劣势/机会/威胁 + 中心 SWOT 圆（命名四象限）|
| `tpl_matrix_2x2` | 2×2 坐标矩阵 | 蓝模板 s118 | 双轴象限（重要/紧急等）+ 每格要点（优先级/定位）|
| `tpl_funnel_bowtie` | 蝴蝶结漏斗 | 蓝模板 s107 | 多段全流程漏斗（获客→转化→复利）+ chip |
| `tpl_gantt_schedule` | 甘特进度表 | 紫模板 s71 | 任务 × 月份 渐变进度条（项目排期）|
| `tpl_kpi_podium` | 大数字数据墙 | 紫模板 s110 | N 个 图标+大数字+标签 立体卡（数据概览）|
| `tpl_venn_3circle` | 3 圆交叠框架 | 蓝模板 s125 | 3C/三要素交叠 + 侧解读卡 |

> 未收（两份模板无干净版式，且易手画/图表模板已覆盖）：定价对比列（用 charts `comparison_columns`）、扁平金字塔（用 charts `pyramid_chart` 或 3D 库）、纯目录/章节封面（deck 专属，手画）。
