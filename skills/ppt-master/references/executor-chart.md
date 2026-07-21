> See [`executor-base.md`](./executor-base.md) for the always-loaded Executor core and [`native-data-interface.md`](./native-data-interface.md) for native chart/table metadata schemas.

# Executor Chart and Table Branch

Conditional Executor authority for data charts, chart-catalog adaptations, chart verification markers, and eligible native chart/table replacement metadata.

**Trigger**: load when `design_spec.md §VII` contains a chart/table visualization, `spec_lock.md page_charts` contains any row, or the current page carries any data-encoded chart or text-grid table. Mini charts, sparklines, inset charts, and small multiples count even when they are absent from `page_charts` or the chart catalog.

## 1. Reference Loading and Per-page Selection

For each selected `templates/charts/<key>.svg`, use its Skill-relative `reference_set` path + SHA: read once before first use or after change, otherwise reuse it. Never load the full catalog.

**Per-page chart reference — `page_charts` section**:

Before drawing each page, look up its entry in `page_charts` to decide which chart structure applies (the SVG itself was loaded in §1):

- Entry present (e.g., `P09: timeline_horizontal`) → adapt the corresponding chart SVG already in context under §3; do not copy it verbatim. Use the selected §VII row and SVG; do not load the full chart catalog during execution.
- No entry for this page → either no chart on this page, or a chart that didn't match any catalog template (Strategist's `no-template-match` fallback). Design the visualization from scratch using `design_spec.md §VII` for guidance.
- Whole section absent → no chart pages in this deck.

---

## 2. Chart and Native-data Authoring

### 2.1 Chart Plot-Area Marker (MANDATORY on planned data-chart pages)

> The [`verify-charts`](../workflows/stages/verify-charts.md) stage enumerates chart pages from `design_spec.md §VII`, then reads each page's plot-area marker to feed `svg_position_calculator.py`. A missing marker invokes that stage's declared fallback and adds avoidable derivation work.

**Hard rule**: every data-driven chart page enumerated in `design_spec.md §VII` includes a plot-area marker inside `<g id="chartArea">`, placed **after axis lines** and **before the first data element** (bar, line, area, point). An incidental microvisual outside §VII needs no marker; if its geometry must enter `verify-charts`, return upstream and record it in §VII first.

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

**Per-page verification** — after writing each §VII data-chart SVG, confirm the marker exists:

```bash
rg -n "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

> Calculator-supported data-chart templates in `templates/charts/` include this
> marker as a reference. If a data chart covered by §2.1 lacks it, that is a
> bug. Conceptual diagrams, frameworks, and other non-data visualizations in
> the same library do not use a plot-area marker.
Technical SVG/PPT constraints remain in [`shared-standards-core.md`](./shared-standards-core.md).

### 2.2 PowerPoint-Native Chart/Table Replacement Marker (MANDATORY on planned native-ready objects)

> `svg_to_pptx.py --native-charts-and-tables` replaces marked groups with PowerPoint-native Chart/Table objects (charts get an embedded Excel workbook). Markers stay dormant in the default export, whose SVG children become independently editable DrawingML shapes. Prepare this optional capability for planned independent data objects, not every numeric embellishment.

**Hard rule**: load [`native-data-interface.md`](./native-data-interface.md) for each §VII row whose `Native-ready` value is `yes`. A supported data chart then gets `data-pptx-replace-with="chart"` plus one JSON `<metadata>` child; a pure text-grid table gets the table form, transcribing all plotted data or visible cells. `no` / `n/a` stays ordinary SVG even when the catalog reference contains a marker. Missing or invalid values return upstream; Executor never infers eligibility. The parent marker selects the schema.

**MUST — atomic authoring**: For each native-ready object, treat the visible SVG fallback, the parent `data-pptx-replace-with` marker, and its JSON `<metadata>` child as one object. Write all three in the same SVG edit while the data is in context. Do not defer the marker or metadata to `verify-charts`, the final quality gate, or export.

**Hard rule — eligibility follows the plan**: A two-point line or small multiple gets metadata only when its §VII row says `yes`. A sparkline, inset, KPI-card trend, or other microvisual outside §VII stays ordinary SVG even when values are recoverable. Changing eligibility requires upstream repair.

Generated authoring MUST omit `data-pptx-import-source` and
`data-pptx-fallback-sha256`: those attributes record imported-PPTX provenance
and its sealed fallback baseline. Never copy a static baseline from a chart
catalog or reusable template; normal content edits would make it stale.

`data-pptx-replace-with` is a **data-backed replacement claim**, not a generic label for a group that contains numbers and not a marker for ordinary PowerPoint shapes or connectors. Add it only when the matching JSON payload can be written in the same edit; if the object is meant to remain SVG geometry, do not add the marker.

- Chart types absent from that list and conceptual/diagrammatic graphics (process flows, cycles, quadrant cards, timelines, or a KPI card container) get **no marker** — `svg_quality_checker.py` rejects unsupported marker types. A supported data chart nested inside one of those compositions gets its own marker only when its §VII row says `Native-ready: yes`.
- Canonical rectangular merged text cells may carry a table marker by putting anchor-only `row_span` / `col_span` in metadata and leaving covered cells blank. Nonrectangular/overlapping merges, nonblank covered cells, and graphical cells (icons, harvey balls, rating dots) get **no table marker** and stay on the SVG fallback route.
- Transcribe, don't restyle: `categories` / `series[].values` are the numbers just plotted; `style.colors` copies the series HEX values already rendered on the page, whether they use a recurring `spec_lock.colors` anchor or a contextual page-local color.
- Data-point color: when a single column/bar series uses data-point colors in the fallback, copy those fills into `series[].point_colors` in category order.
- Data labels: when visible point values are part of the fallback chart, write `data_labels` instead of companion text; use `data_labels.points` for selected labels, and use `number_format`, `font_size`, `font_family`, and per-point `colors` / `color` when the fallback labels carry suffixes or color-coded text.
- Line markers: when the fallback line chart draws visible point nodes, set `line_style: "lineMarker"`; leave the default `line` only for line charts without nodes.
- Area-under-line: when a combo plot is drawn as a filled area under a line, keep `type: "line"`, add `area_fill: true`, and copy the area transparency into `series[].fill_opacity`; copy visible line `stroke-width` into `series[].line_width` for line/area series.
- Native chrome: write `title`, `subtitle`, axis titles, or `show_legend: true` only when the fallback visibly renders the same chrome inside the native chart's replacement scope. `title` is the PowerPoint chart title, not an object name; use `name` for page-semantic object naming (e.g. `p03-revenue-chart`). Write explicit `x`/`y`/`width`/`height` read from the drawn plot area; omission is the fallback — the exporter then infers the frame from the drawn fallback geometry.
- Value-axis labels: when the fallback keeps category labels but intentionally omits numeric value-axis tick labels, set `show_value_axis_labels: false`.
- Freeform chart text: transcribe center labels, source notes, and other in-chart annotations as companion `caption` / `note` / `notes` entries with explicit slide-coordinate bounds; do not rely on fallback `<text>` children to survive native export.
- Native chart typography mirrors the SVG fallback. Copy the fallback's shared chart font into `style.font_family` and visible chart text sizes into the matching metadata fields (`title_font_size`, `subtitle_font_size`, `axis_font_size`, `note_font_size`, etc.) only when role sizes differ; otherwise let the exporter infer them from visible fallback text. When a visible chart title, subtitle, or axis title needs its own size/color/font, write that field as an object with `text`, `font_size`, `font_family`, and `color`. Use `axis_title_font_size`, `legend_font_size`, or companion per-entry `font_size` only when the fallback visibly uses a separate size.
- Native table typography mirrors the SVG fallback. Write `style.font_family` and `style.font_size` from the visible table text; use `header_font_size` or per-cell `font_size` only when the fallback visibly does so. If the fallback has no explicit table font, fall back to the deck body family and declared body anchor from `spec_lock.md typography`.
- The marker group's transform stays translate/scale only (no rotate / matrix / skew).
- Visual parity is not a goal: the SVG drawing remains the designed visual and exports as editable DrawingML shapes; the native object is the data-backed counterpart with PowerPoint's chart/table-specific model. Never simplify the SVG design to match what a native object could show.

**Per-page verification** — after writing a page with planned native-ready objects, enumerate those objects and confirm a one-to-one match: every object has one parent marker and exactly one JSON metadata child. Finding one marker somewhere on a page is insufficient when the page contains multiple planned objects.

```bash
rg -n 'data-pptx-replace-with="(chart|table)"|<metadata type="application/json">' <project_path>/svg_output/<current_page>.svg
```


---

## 3. Visualization Reference

Chart SVGs referenced in **VII. Visualization Reference List** are loaded once through §1. This section governs adaptation only.

**Hard rule**: adapt the loaded chart SVG; do not improvise from memory and do not replicate verbatim. Apply the active Design Spec and `spec_lock.md`; preserve the visualization type and data semantics.

**Adaptation rules**:
- **Preserve**: visualization type (bar/line/pie/timeline/process/framework…), information relationships, data encoding, and every content obligation in the active Design Spec
- **Selected key, flexible realization**: keep the Strategist-selected chart key/type; its preview grouping, frame count, item count, capacity, and geometry are adaptable to the actual authored content
- **Carry forward**: every planned label, value, unit, status, source, and explanatory block; never shorten or drop content to imitate a lighter catalog preview
- **Adapt**: project data and labels, dimensions, axes, legend, and spacing as the authored content requires
- **Project-owned**: palette, typography, container treatment, effects, background, and page chrome; catalog preview values are fallbacks, never defaults
- **Bound final body modules**: add or revise root-coordinate `data-pptx-bounds` on every visible direct root `<g>` copied into the final page; nested groups need none, chart geometry and local references are not content-boundary inputs, and catalog reference warnings never waive the final-page contract
- **Adjust with fidelity**: composition, axis ranges, grouping, and grid may change when the actual content, relationships, hierarchy, and data encoding remain complete
- **Forbidden**: changing visualization type without spec justification; omitting planned data points, labels, relationships, or explanatory content to fit the catalog preview

> Templates: `templates/charts/`. The Strategist's selected key is already locked in `page_charts`; execution opens only that key's SVG.

### 3.1 Chart Coordinate Calibration

Coordinate calibration runs as a **conditional post-generation stage**, not inside the Executor authoring loop. After SVG generation completes, if the deck contains data charts, run [`verify-charts`](../workflows/stages/verify-charts.md) before post-processing.

The executor's only obligation here is upstream: embed the `<!-- chart-plot-area ... -->` marker on each §VII data-chart page during initial draft (§2.1). Verify-charts enumerates those pages from the authoritative deck plan and uses the marker to feed `svg_position_calculator.py`.

> Do NOT run `svg_position_calculator.py` during the initial draft. The calculator calibrates already-generated SVGs against their declared plot areas; running it before the SVG exists has nothing to compare against.
