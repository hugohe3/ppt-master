# Executor Common Guidelines

> Style-specific content is in the corresponding `executor-{style}.md`. Technical constraints are in shared-standards.md.

---

## 1. Template Adherence Rules

If `templates/` exists in the project, follow the template structure:

| Page Type | Corresponding Template | Adherence Rules |
|-----------|----------------------|-----------------|
| Cover | `01_cover.svg` | Inherit background, decorative elements, layout structure; replace placeholder content |
| Chapter | `02_chapter.svg` | Inherit numbering style, title position, decorative elements |
| Content | `03_content.svg` | Inherit header/footer styles; **content area may be freely laid out** |
| Ending | `04_ending.svg` | Inherit background, thank-you message position, contact info layout |
| TOC | `02_toc.svg` | **Optional**: Inherit TOC title, list styles |

### Page-Template Mapping Declaration (Required Output)

Before generating each page, output which template is used:

```
📝 **Template mapping**: `templates/01_cover.svg` (or "None (free design)")
🎯 **Adherence rules / layout strategy**: [specific description]
```

- **Content pages**: template defines only header/footer; content area is free
- **No template**: generate entirely per the Design Spec

---

## 2. Design Parameter Confirmation (Mandatory Step)

Before the first SVG page, output a confirmation listing: canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan. Prevents spec/execution drift.

### 2.1 Per-page spec_lock re-read (Mandatory)

> Long decks drift off the declared palette/icons mid-deck due to context compression. `spec_lock.md` is the canonical execution reference — re-read it per page to bypass model memory.

**Hard rule**: Before generating **each** SVG page, `read_file <project_path>/spec_lock.md`. Use only values from this file, not from memory. If context was auto-compacted, also `read_file <project_path>/design_spec.md` for the current page's §IX brief.

**If `spec_lock.md` is missing**: emit `warning: spec_lock.md missing — generating without execution lock` once, then proceed using `design_spec.md` values. Expected only for legacy projects; new projects MUST have it (see [strategist.md](strategist.md) §6 step 4).

**Forbidden — values outside the lock**:

- Colors (fill / stroke / stop-color) MUST come from `colors`
- Icons MUST come from `icons.inventory`; library MUST equal `icons.library`
- Font family from `typography`: use role override (`title_family` / `body_family` / `emphasis_family` / `code_family`) if declared, else fall back to `font_family`
- Font sizes follow a **ramp anchored on `typography.body`**, not a closed menu. Use the declared slots when they fit. Intermediate sizes (e.g., 40px hero number, 13px annotation) are allowed if the ratio to `body` falls within the role's band (see `design_spec.md §IV ramp table`). Sizes outside every band require extending the lock first.
- Images MUST reference files listed under `images`; no invented filenames

If a page needs a value not in `spec_lock.md`, surface it — do not silently invent one.

**Per-page layout rhythm — `page_rhythm` section**:

Before drawing each page, look up its entry in `page_rhythm` (key format `P<NN>` matching the page index in §IX of `design_spec.md`) and apply the corresponding layout discipline:

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). Follow the matching template verbatim. |
| `dense` | Information-heavy. Card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. This is the baseline behavior. |
| `breathing` | Low-density impact page. Avoid **multi-card grid layouts** — do not organize content as multiple parallel rounded containers (3-card row, 4-card KPI grid, 2×2 matrix rendered as cards). Use naked text blocks, dividers, whitespace, or full-bleed imagery as the content structure. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine — the rule is about grid structure, not about the `rx` attribute. Proportions follow information weight (not a preset ratio). Typical forms: hero quote, single large number with one-line interpretation, full-bleed image with floating caption, section transition. |

> Without rhythm variation, every page defaults to card grids (the "AI-generated" look). `page_rhythm` is the only narrative lever that survives context compression.

**Missing `page_rhythm` section** → emit `warning: spec_lock.md missing page_rhythm — defaulting all pages to dense` once, fall back to `dense` for all pages.

**Tag not found for current page** → fall back to `dense` silently. Do not invent a tag.

---

## 3. Execution Guidelines

- **Proximity**: group related elements with tight spacing; separate unrelated groups
- **Spec adherence**: follow color, layout, canvas format, and typography in the spec
- **Template structure**: if templates exist, inherit the visual framework
- **Main-agent ownership**: SVG generation must run in the main agent (not sub-agents) — pages share upstream context for cross-page visual continuity
- **Generation rhythm**: lock global design context first, then generate pages sequentially in one continuous context. No batched groups (e.g., 5 at a time).
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: generate all SVG pages sequentially for visual consistency. Do NOT run `svg_position_calculator.py` during the initial draft — use layout judgment for chart marks.
  2. **Quality Check Gate** (between phases): run `python3 scripts/svg_quality_checker.py <project_path>` on `svg_output/`. Any `error` (banned features, viewBox mismatch, spec_lock drift, non-PPT-safe font, etc.) MUST be fixed on the offending page before proceeding — regenerate and re-check. Address `warning`s when straightforward. After passing, run §5.1 chart coordinate calibration for calculator-supported chart types. Do NOT defer to after `finalize_svg.py` — finalize rewrites SVG and masks some violations.
  3. **Logic Construction Phase**: after SVGs pass, batch-generate speaker notes for narrative continuity.
- **Technical specs**: see [shared-standards.md](shared-standards.md) for SVG/PPT constraints
- **Visual depth — through restraint**: layered depth comes from rhythm (flat vs lifted, dense vs spacious), not from shadows everywhere. Apply shadow to at most 2-3 genuinely floating elements per page (cards on photos, primary CTA, overlays); keep peer-grid cards, dividers, body containers flat. Reach for typography weight, spacing, accent bars, subtle tints **before** shadow. Full rules in shared-standards.md §6.

### SVG File Naming Convention

Format: `<NN>_<page_name>.svg` (two-digit number from 01; name matches the deck's language and the page title in the Design Spec).

Examples: `01_封面.svg` / `02_目录.svg` / `03_核心优势.svg`; `01_cover.svg` / `02_agenda.svg` / `03_key_benefits.svg`.

---

## 4. Icon Usage

Strategist chooses the library and inventory; Executor only implements. Library details and one-library rule: [`../templates/icons/README.md`](../templates/icons/README.md). This section defines placeholder syntax.

**Built-in icons — Placeholder method (recommended)**:

```xml
<!-- chunk-filled (straight-line geometry, sharp corners, structured) -->
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-filled (bezier-curve forms, smooth & rounded contours) -->
<use data-icon="tabler-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-outline (light, line-art style — screen-only decks) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- phosphor-duotone (single color + 20% backplate — soft depth without solid weight) -->
<use data-icon="phosphor-duotone/house" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- simple-icons (brand logos — used alongside the deck's primary library, only for real company/product marks) -->
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>

<!-- tabler-outline with thin / bold stroke (stroke-style libraries only) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="1.5"/>
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="3"/>
```

> ⚠️ **Color**: ALWAYS use `fill="#HEX"` on `<use data-icon="...">`. NEVER use `stroke` or `fill="none"`, even for stroke-style libraries.
>
> **stroke-width** (stroke-style libraries only, currently `tabler-outline`): allowed values `{1.5, 2, 3}`. If `spec_lock.md icons.stroke_width` is declared, all placeholders MUST use that value deck-wide. Default `2` if absent (legacy). Ignored on non-stroke libraries.
>
> Icons are auto-embedded by `finalize_svg.py` — no need to run `embed_icons.py` manually.

**Searching for icons** — use terminal, zero token cost:
```bash
ls skills/ppt-master/templates/icons/chunk-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-filled/ | grep home
ls skills/ppt-master/templates/icons/tabler-outline/ | grep chart
ls skills/ppt-master/templates/icons/phosphor-duotone/ | grep house
ls skills/ppt-master/templates/icons/simple-icons/ | grep github
```

**Abstract concept → icon name** (names for `chunk-filled`; tabler libraries use their own equivalents — verify with `ls | grep`):

| Concept | chunk-filled | tabler-filled / tabler-outline |
|---------|-------|-------------------------------|
| Growth / Increase | `arrow-trend-up` | same |
| Decline / Decrease | `arrow-trend-down` | same |
| Success / Complete | `circle-checkmark` | `circle-check` |
| Warning / Risk | `triangle-exclamation` | `alert-triangle` |
| Innovation / Idea | `lightbulb` | `bulb` |
| Strategy / Goal | `target` | same |
| Efficiency / Speed | `bolt` | same |
| Collaboration / Team | `users` | same |
| Settings / Config | `cog` | `settings` |
| Security / Trust | `shield` | same |
| Money / Finance | `dollar` | `currency-dollar` |
| Time / Deadline | `clock` | same |
| Location / Region | `map-pin` | same |
| Communication | `comment` | `message` |
| Analysis / Data | `chart-bar` | same |
| Process / Flow | `arrows-rotate-clockwise` | `refresh` |
| Global / World | `globe` | `world` |
| Excellence / Award | `star` | same |
| Expand / Scale | `maximize` | same |
| Problem / Issue | `bug` | same |

> For self-evident names (home, user, file, search, arrow, etc.) — just `grep chunk-filled/` directly without consulting the table.

> ⚠️ **Icon validation**: only use icons from the Design Spec's approved inventory. Verify each via `ls | grep` before use. Mixing libraries within one deck is FORBIDDEN.

---

## 5. Visualization Reference

When the Design Spec includes **VII. Visualization Reference List**, read the referenced templates from `templates/charts/` before drawing those pages.

**Reading is mandatory; copying is not.** On first use of each visualization type listed in §VII, read `templates/charts/<chart_name>.svg`. Use as reference for layout, structure, spacing, visual logic — apply the project's colors, typography, content. Do not improvise from memory; do not replicate verbatim.

> Re-read only when the visualization type changes; reuse for subsequent pages of the same type.

**Adaptation rules**:
- **Preserve**: visualization type (bar/line/pie/timeline/process/framework…) as specified
- **Adapt**: data, labels, colors (project scheme), dimensions
- **Freely adjust**: composition, axis ranges, grid, legend, spacing, decoration — as long as the chart stays accurate and readable
- **Forbidden**: changing visualization type without spec justification; omitting data points or structural elements from the outline

> Templates: `templates/charts/` (70 types). Index: `templates/charts/charts_index.json`

### 5.1 Chart Coordinate Calibration (After SVG Quality Checker)

> For chart types supported by `svg_position_calculator.py`, run calibration **after** `svg_quality_checker.py` passes and **before** Logic Construction. Calibrates already-generated SVG against the plot area. Do NOT run during initial draft. Only applies to calculator-supported types.

**Workflow after `svg_quality_checker.py` passes:**

1. **Confirm chart type is supported** — calculator covers: `bar`, `pie`/`donut`, `radar`, `line`/`area`/`scatter`. Area has no separate mode — use `calc line` for the top boundary, then close to `y_max`. Grid layout is optional. Other visualizations (timeline, process, framework, maps, pictograms…) skip this step.

2. **Identify the plot area** — the data drawing rectangle only; excludes title, legend, axis labels, footnotes, annotations.

   Recommended SVG marker when generating chart pages:
   ```xml
   <!-- chart-plot-area: x_min,y_min,x_max,y_max -->
   ```

3. **Calculate the expected coordinates** — run the calculator for the chart type and manually compare the output with the SVG's existing mark coordinates:
   ```bash
   # Bar chart
   python3 scripts/svg_position_calculator.py calc bar \
     --data "Label1:Value1,Label2:Value2" --area "x_min,y_min,x_max,y_max" --bar-width 120

   # Line / area chart
   python3 scripts/svg_position_calculator.py calc line \
     --data "x1:y1,x2:y2,..." --area "x_min,y_min,x_max,y_max" --y-range "0,max"

   # Pie / donut chart
   python3 scripts/svg_position_calculator.py calc pie \
     --data "Slice1:Value1,Slice2:Value2" --center "cx,cy" --radius 200
   ```

   For an area chart, use the line output as the top boundary. The filled SVG path should close to the plot area's bottom edge:
   ```svg
   M first_x,first_y ... L last_x,last_y L last_x,y_max L first_x,y_max Z
   ```

4. **If coordinates differ** — manually update SVG attributes from calculator output, rerun `svg_quality_checker.py`, repeat. Do NOT use regex or bulk replacement.

> AI models routinely introduce 10-50 px errors when mapping data to pixel positions. Errors compound across bars/lines/arcs, distorting proportions. The calculator eliminates this class of error.

---

## 6. Image Handling

Handle images by their status in the Design Spec's Image Resource List. Status enum and lifecycle: [`svg-image-embedding.md`](svg-image-embedding.md).

| Status | Source | Handling |
|--------|--------|----------|
| **Existing** | User-provided | Reference images directly from `../images/` directory |
| **Generated** | Generated by Image_Generator | Reference images directly from `../images/` directory |
| **Needs-Manual** | Generation failed and file is absent | Use dashed border placeholder unless the expected file exists |
| **Placeholder** | Not yet prepared | Use dashed border placeholder |

**Reference syntax**: see [`svg-image-embedding.md`](svg-image-embedding.md).

**Placeholder**: Dashed border `<rect stroke-dasharray="8,4" .../>` + description text

---

## 7. Font Usage

Source of truth: `spec_lock.md typography`. Use `font_family` as default; override per role with `title_family` / `body_family` / `emphasis_family` / `code_family` if declared.

If `spec_lock.md` is absent, consult [`strategist.md`](strategist.md) §g — do not invent a stack.

**Hard rule**: every SVG `font-family` stack MUST end with a pre-installed family (Microsoft YaHei / SimHei / SimSun / Arial / Calibri / Segoe UI / Times New Roman / Georgia / Consolas / Courier New / Impact / Arial Black). PPTX has no runtime fallback — missing fonts degrade to Calibri.

---

## 8. Speaker Notes Generation Framework

### Task 1. Generate Complete Speaker Notes Document

After all SVG pages are finalized, enter Logic Construction Phase and write the full notes to `notes/total.md`. Batch-writing (not per-page) lets transitions plan coherently.

**Format**: Each page: `# <number>_<page_title>` heading, separated by `---`. Each contains 2-5 sentence script, `Key points: ① ② ③`, `Duration: X minutes`. Every page after the first starts with a `[Transition]` phrase.

**Basic stage direction markers** (common to all styles):

| Marker | Purpose |
|--------|---------|
| `[Pause]` | Whitespace after key content, letting the audience absorb |
| `[Transition]` | Standalone paragraph at the start of each page's text, bridging from the previous page |

> Each style may extend with additional markers (`[Interactive]`/`[Data]`/`[Scan Room]`/`[Benchmark]` etc.), see `executor-{style}.md`.

**Language consistency**: structural labels and stage direction markers MUST match the deck's content language. Localize all labels — do NOT mix English labels with non-English content.

| English | 中文 | 日本語 | 한국어 |
|---------|------|--------|--------|
| `[Transition]` | `[过渡]` | `[つなぎ]` | `[전환]` |
| `[Pause]` | `[停顿]` | `[間]` | `[멈춤]` |
| `[Interactive]` | `[互动]` | `[問いかけ]` | `[상호작용]` |
| `[Data]` | `[数据]` | `[データ]` | `[데이터]` |
| `[Scan Room]` | `[观察]` | `[観察]` | `[관찰]` |
| `[Benchmark]` | `[对标]` | `[ベンチマーク]` | `[벤치마크]` |
| `Key points:` | `要点：` | `要点：` | `핵심 포인트:` |
| `Duration:` | `时长：` | `所要時間：` | `소요 시간:` |
| `Flex:` | `弹性：` | `調整：` | `조정:` |

> For languages not listed above, translate each label to the corresponding natural term in that language.

**Requirements**: conversational tone; highlight each page's core info and key points; users may edit/override in `notes/`.

### Task 2. Split Into Per-Page Note Files

Auto-split `notes/total.md` into per-page files in `notes/`.

**Naming**: match SVG names (`01_cover.svg` → `notes/01_cover.md`); `slide01.md` also supported (legacy).

---

## 9. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (same canonical pipeline as [shared-standards.md §5](shared-standards.md)):

```bash
# 1. Split speaker notes
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons, images, etc.)
python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX
python3 scripts/svg_to_pptx.py <project_path> -s final
# Output: exports/<project_name>_<timestamp>.pptx + exports/<project_name>_<timestamp>_svg.pptx
```
