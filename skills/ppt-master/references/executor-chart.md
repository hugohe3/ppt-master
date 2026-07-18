> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core and [`native-data-interface.md`](./native-data-interface.md) for native chart/table metadata schemas.

# Executor Chart and Table Branch

Conditional Executor authority for data charts, chart-catalog adaptations, chart verification markers, and eligible native chart/table replacement metadata.

**Trigger**: load when `design_spec.md §VII` contains a chart/table visualization, `spec_lock.md page_charts` contains any row, or the page carries an eligible data chart or text-grid table.

## 1. Reference Loading and Per-page Selection

Read each selected chart SVG once before its first use. If a later page introduces a chart absent from the initial selection, read that file once and continue.

**Per-page chart reference — `page_charts` section**:

Before drawing each page, look up its entry in `page_charts` to decide which chart structure applies (the SVG itself was loaded in §1):

- Entry present (e.g., `P09: timeline_horizontal`) → adapt the corresponding chart SVG already in context. Apply project colors/typography/density; do not copy verbatim. Use the selected §VII row and SVG; do not load the full chart catalog during execution.
- No entry for this page → either no chart on this page, or a chart that didn't match any catalog template (Strategist's `no-template-match` fallback). Design the visualization from scratch using `design_spec.md §VII` for guidance.
- Whole section absent → no chart pages in this deck.

---

## 2. Chart and Native-data Authoring

### 2.1 Chart Plot-Area Marker (MANDATORY on every chart page)

> The [`verify-charts`](../workflows/stages/verify-charts.md) stage enumerates chart pages from `design_spec.md §VII`, then reads each page's plot-area marker to feed `svg_position_calculator.py`. A missing marker invokes that stage's declared fallback and adds avoidable derivation work.

**Hard rule**: every SVG page that contains a data visualization chart includes a plot-area marker inside `<g id="chartArea">`, placed **after axis lines** and **before the first data element** (bar, line, area, point).

**Rectangular plot area** (bar / horizontal_bar / grouped_bar / stacked_bar / line / area / stacked_area / scatter / waterfall / pareto / butterfly):

```xml
<!-- chart-plot-area: x_min,y_min,x_max,y_max -->
```

**Radial charts** (pie / donut / radar):

```xml
<!-- chart-plot-area: pie | center: cx,cy | radius: r -->
<!-- chart-plot-area: donut | center: cx,cy | outer-radius: r1 | inner-radius: r2 -->
<!-- chart-plot-area: radar | center: cx,cy | radius: r -->
```

**How to determine coordinate values**:

| Value | Derivation |
|-------|------------|
| `x_min` | X coordinate of the Y-axis line (leftmost data boundary) |
| `y_min` | Y coordinate of the topmost grid line (highest data boundary) |
| `x_max` | X coordinate of the rightmost axis endpoint or grid line |
| `y_max` | Y coordinate of the X-axis baseline |
| `cx, cy` | Center point of pie/donut/radar (accounting for `transform="translate()"`) |
| `r` | Outer radius of the chart |

**Per-page verification** — after writing each chart SVG, confirm the marker exists:

```bash
grep "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

> Calculator-supported data-chart templates in `templates/charts/` include this
> marker as a reference. If a data chart covered by §2.1 lacks it, that is a
> bug. Conceptual diagrams, frameworks, and other non-data visualizations in
> the same library do not use a plot-area marker.
Technical SVG/PPT constraints remain in [`shared-standards-core.md`](./shared-standards-core.md).

### 2.2 PowerPoint-Native Chart/Table Replacement Marker (MANDATORY on eligible data-chart and text-grid table pages)

> `svg_to_pptx.py --native-charts-and-tables` replaces marked groups with PowerPoint-native Chart/Table objects (charts get an embedded Excel workbook). Markers stay dormant in the default export, whose SVG children become independently editable DrawingML shapes, but a deck without markers can never form data-backed native Chart/Table objects. Write the marker at draw time: the data is already in hand, and recovering it later costs a full re-read pass.

**Hard rule**: before deciding whether a chart or table is eligible for native replacement, load [`native-data-interface.md`](./native-data-interface.md). Every data chart whose type appears in that authority's **Supported chart types** list gets `data-pptx-replace-with="chart"` plus one `<metadata type="application/json">` JSON child on its top-level `<g>`, transcribing the same data just plotted. Every pure text-grid data table gets `data-pptx-replace-with="table"` the same way, transcribing all visible cell text into `columns` / `rows`. The parent marker determines the JSON schema; do not duplicate a chart/table kind on the metadata child.

Generated authoring MUST omit `data-pptx-import-source` and
`data-pptx-fallback-sha256`: those attributes record imported-PPTX provenance
and its sealed fallback baseline. Never copy a static baseline from a chart
catalog or reusable template; normal content edits would make it stale.

`data-pptx-replace-with` is a **data-backed replacement claim**, not a generic label for a group that contains numbers and not a marker for ordinary PowerPoint shapes or connectors. Add it only when the matching JSON payload can be written in the same edit; if the object is meant to remain SVG geometry, do not add the marker.

- Chart types absent from that list and conceptual/diagrammatic graphics (process flows, cycles, quadrant cards, timelines, KPI cards) get **no marker** — `svg_quality_checker.py` rejects unsupported marker types.
- Canonical rectangular merged text cells may carry a table marker by putting anchor-only `row_span` / `col_span` in metadata and leaving covered cells blank. Nonrectangular/overlapping merges, nonblank covered cells, and graphical cells (icons, harvey balls, rating dots) get **no table marker** and stay on the SVG fallback route.
- Transcribe, don't restyle: `categories` / `series[].values` are the numbers just plotted; `style.colors` carries the series HEX values already used on the page (from `spec_lock.colors`).
- Data-point color: when a single column/bar series uses data-point colors in the fallback, copy those fills into `series[].point_colors` in category order.
- Data labels: when visible point values are part of the fallback chart, write `data_labels` instead of companion text; use `data_labels.points` for selected labels, and use `number_format`, `font_size`, `font_family`, and per-point `colors` / `color` when the fallback labels carry suffixes or color-coded text.
- Line markers: when the fallback line chart draws visible point nodes, set `line_style: "lineMarker"`; leave the default `line` only for line charts without nodes.
- Area-under-line: when a combo plot is drawn as a filled area under a line, keep `type: "line"`, add `area_fill: true`, and copy the area transparency into `series[].fill_opacity`; copy visible line `stroke-width` into `series[].line_width` for line/area series.
- Native chrome: write `title`, `subtitle`, axis titles, or `show_legend: true` only when the fallback visibly renders the same chrome inside the native chart's replacement scope. `title` is the PowerPoint chart title, not an object name; use `name` for page-semantic object naming (e.g. `p03-revenue-chart`). Write explicit `x`/`y`/`width`/`height` read from the drawn plot area; omission is the fallback — the exporter then infers the frame from the drawn fallback geometry.
- Value-axis labels: when the fallback keeps category labels but intentionally omits numeric value-axis tick labels, set `show_value_axis_labels: false`.
- Freeform chart text: transcribe center labels, source notes, and other in-chart annotations as companion `caption` / `note` / `notes` entries with explicit slide-coordinate bounds; do not rely on fallback `<text>` children to survive native export.
- Native chart typography mirrors the SVG fallback. Copy the fallback's shared chart font into `style.font_family` and visible chart text sizes into the matching metadata fields (`title_font_size`, `subtitle_font_size`, `axis_font_size`, `note_font_size`, etc.) only when role sizes differ; otherwise let the exporter infer them from visible fallback text. When a visible chart title, subtitle, or axis title needs its own size/color/font, write that field as an object with `text`, `font_size`, `font_family`, and `color`. Use `axis_title_font_size`, `legend_font_size`, or companion per-entry `font_size` only when the fallback visibly uses a separate size.
- Native table typography mirrors the SVG fallback. Write `style.font_family` and `style.font_size` from the visible table text; use `header_font_size` or per-cell `font_size` only when the fallback visibly does so. If the fallback has no explicit table font, fall back to the deck body family and locked body size from `spec_lock.md typography`.
- The marker group's transform stays translate/scale only (no rotate / matrix / skew).
- Visual parity is not a goal: the SVG drawing remains the designed visual and exports as editable DrawingML shapes; the native object is the data-backed counterpart with PowerPoint's chart/table-specific model. Never simplify the SVG design to match what a native object could show.

**Per-page verification** — after writing each eligible data-chart or text-grid table page, confirm the marker exists:

```bash
grep "data-pptx-replace-with" <project_path>/svg_output/<current_page>.svg
```


---

## 3. Visualization Reference

Chart SVGs referenced in **VII. Visualization Reference List** are loaded once through §1. This section governs adaptation only.

**Hard rule**: adapt the loaded chart SVG; do not improvise from memory and do not replicate verbatim. Apply project colors, typography, content; preserve visualization type.

**Adaptation rules**:
- **Preserve**: visualization type (bar/line/pie/timeline/process/framework…) as specified
- **Adapt**: data, labels, colors (project scheme), dimensions
- **Freely adjust**: composition, axis ranges, grid, legend, spacing, decoration — as long as the chart stays accurate and readable
- **Forbidden**: changing visualization type without spec justification; omitting data points or structural elements from the outline

> Templates: `templates/charts/`. The Strategist's selected key is already locked in `page_charts`; execution opens only that key's SVG.

### 3.1 Chart Coordinate Calibration

Coordinate calibration runs as a **conditional post-generation stage**, not inside the Executor authoring loop. After SVG generation completes, if the deck contains data charts, run [`verify-charts`](../workflows/stages/verify-charts.md) before post-processing.

The executor's only obligation here is upstream: embed the `<!-- chart-plot-area ... -->` marker on every chart page during initial draft (§2.1). Verify-charts enumerates chart pages from `design_spec.md §VII` (authoritative deck plan) and uses the marker to feed `svg_position_calculator.py`.

> Do NOT run `svg_position_calculator.py` during the initial draft. The calculator calibrates already-generated SVGs against their declared plot areas; running it before the SVG exists has nothing to compare against.
