> Default Generate also loads [`executor-base.md`](./executor-base.md); Default and Quick load [`native-data-interface.md`](./native-data-interface.md) when native chart/table metadata is selected.

# Executor Chart and Table Branch

Conditional Executor authority for data charts, chart-catalog adaptations, chart verification markers, and eligible native chart/table replacement metadata.

**Trigger**: load when `design_spec.md §VII` contains a selected chart/table reference, `spec_lock.md page_charts` contains any row, the current §IX page block carries any data-encoded chart or text-grid table, or Quick Generate resolves such an object in active context. Mini charts, sparklines, inset charts, and small multiples count even when they are absent from `page_charts` or the chart catalog.

**Profile authority**: Default follows the Design Spec/lock and returns missing or conflicting planning decisions upstream. Quick has no plan artifact: the current main agent resolves the data object, optional catalog key, fallback design, and native-readiness immediately in active context, writes the selected semantics into the SVG itself, and does not create a substitute roster or mapping file.

## 1. Reference Loading and Per-page Selection

For each selected `templates/charts/<key>.svg`, use its Skill-relative path and
read once before first use or after a known change, otherwise reuse it. Never
load the full catalog.

**Per-page chart reference**:

| Active profile | Selection authority |
|---|---|
| Default Generate | Look up whether `spec_lock.md page_charts` supplies a page-local key, then read its §VII Usage and SVG for that page only |
| Quick Generate | Use bounded `chart_recall.py` only when a reusable visualization reference would help; keep the selected key and purpose in active context for that page only, or retain `no-template-match` and design from scratch |

Before drawing each page, apply the matching branch:

- Selected key present (e.g., `timeline_horizontal`) → read that SVG for the current page only and realize the active page intent without copying it or loading the catalog.
- No selected key → design the declared visualization/table from scratch; do not invent a catalog reference after drawing begins.
- Quick never persists its selection into §VII, `page_charts`, or another mapping artifact.

---

## 2. Chart and Native-data Authoring

### 2.1 Chart Plot-Area Marker (MANDATORY on active data-chart pages)

> The [`verify-charts`](../workflows/stages/verify-charts.md) stage enumerates Default data-driven chart pages from `design_spec.md §IX`; Quick runs it from the still-active page decisions and cross-checks those decisions against plot-area markers. A missing marker invokes that stage's declared fallback and adds avoidable derivation work.

**Hard rule**: every Default page whose §IX `Visualization` declares
data-driven chart geometry, and every Quick page the current agent resolves as
data-driven, includes a plot-area marker inside `<g id="chartArea">`, placed
**after axis lines** and **before the first data element** (bar, line, area,
point). A legacy §VII data-chart row counts when its page block lacks that
declaration. An incidental microvisual needs no marker unless the current
profile promotes it to a coordinate-verified data object; Default repairs §IX,
while Quick resolves that decision immediately before drawing.

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

**Per-page verification** — after writing each active data-chart SVG, confirm the marker exists:

```bash
rg -n "chart-plot-area" <project_path>/svg_output/<current_page>.svg
```

> Calculator-supported data-chart templates in `templates/charts/` include this
> marker as a reference. If a data chart covered by §2.1 lacks it, that is a
> bug. Conceptual diagrams, frameworks, and other non-data visualizations in
> the same library do not use a plot-area marker.
Technical SVG/PPT constraints remain in [`shared-standards-core.md`](./shared-standards-core.md).

### 2.2 PowerPoint-Native Chart/Table Replacement Marker (MANDATORY on selected native-ready objects)

> `svg_to_pptx.py --native-charts-and-tables` replaces marked groups with PowerPoint-native Chart/Table objects (charts get an embedded Excel workbook). Markers stay dormant in the default export, whose SVG children become independently editable DrawingML shapes. Prepare this optional capability for selected independent data objects, not every numeric embellishment.

**Hard rule**: load [`native-data-interface.md`](./native-data-interface.md) for
each independent data chart or pure text-grid table selected as native-ready.
Default reads that decision from the current §IX page block (`yes`/`no`; legacy
§VII fallback only). Quick decides in active context before drawing based on
whether the PowerPoint Chart/Table object model is useful enough to accept its
normalization risk. A supported selected chart gets
`data-pptx-replace-with="chart"` plus one JSON `<metadata>` child; a selected
pure text-grid table gets the table form, transcribing all plotted data or
visible cells. An object not selected stays ordinary SVG even when a catalog
reference contains a marker. The parent marker selects the schema.

**MUST — atomic authoring**: For each native-ready object, treat the visible SVG fallback, the parent `data-pptx-replace-with` marker, and its JSON `<metadata>` child as one object. Write all three in the same SVG edit while the data is in context. Do not defer the marker or metadata to `verify-charts`, the final quality gate, or export.

**Hard rule — eligibility follows the active profile authority**: In Default, a
two-point line or small multiple gets metadata only when its §IX page block
plans it as an independent object with `Native-ready: yes`; changing eligibility
requires upstream repair. In Quick, the current agent makes that independent-
object decision before drawing and expresses it atomically through the marker,
metadata, and fallback. A sparkline, inset, KPI-card trend, or other incidental
microvisual stays ordinary SVG unless Quick deliberately promotes it before
authoring.

Generated authoring MUST omit `data-pptx-import-source` and
`data-pptx-fallback-sha256`: those attributes record imported-PPTX provenance
and its sealed fallback baseline. Never copy a static baseline from a chart
catalog or reusable template; normal content edits would make it stale.

`data-pptx-replace-with` is a **data-backed replacement claim**, not a generic label for a group that contains numbers and not a marker for ordinary PowerPoint shapes or connectors. Add it only when the matching JSON payload can be written in the same edit; if the object is meant to remain SVG geometry, do not add the marker.

- Chart types absent from that list and conceptual/diagrammatic graphics (process flows, cycles, quadrant cards, timelines, or a KPI card container) get **no marker** — `svg_quality_checker.py` rejects unsupported marker types. A supported data chart nested inside one of those compositions gets its own marker only when Default §IX or the Quick active-context decision selects that object as native-ready.
- Canonical rectangular merged text cells may carry a table marker by putting anchor-only `row_span` / `col_span` in metadata and leaving covered cells blank. Nonrectangular/overlapping merges, nonblank covered cells, and graphical cells (icons, harvey balls, rating dots) get **no table marker** and stay on the SVG fallback route.
- Transcribe, don't restyle: `categories` / `series[].values` are the numbers just plotted; `style.colors` copies the series HEX values already rendered on the page, whether they use a recurring Default `spec_lock.colors` anchor or a Quick/contextual page-local color.
- Data-point color: when a single column/bar series uses data-point colors in the fallback, copy those fills into `series[].point_colors` in category order.
- Data labels: when visible point values are part of the fallback chart, write `data_labels` instead of companion text; use `data_labels.points` for selected labels, and use `number_format`, `font_size`, `font_family`, and per-point `colors` / `color` when the fallback labels carry suffixes or color-coded text.
- Line markers: when the fallback line chart draws visible point nodes, set `line_style: "lineMarker"`; leave the default `line` only for line charts without nodes.
- Area-under-line: when a combo plot is drawn as a filled area under a line, keep `type: "line"`, add `area_fill: true`, and copy the area transparency into `series[].fill_opacity`; copy visible line `stroke-width` into `series[].line_width` for line/area series.
- Native chrome: write `title`, `subtitle`, axis titles, or `show_legend: true` only when the fallback visibly renders the same chrome inside the native chart's replacement scope. `title` is the PowerPoint chart title, not an object name; use `name` for page-semantic object naming (e.g. `p03-revenue-chart`). Write explicit `x`/`y`/`width`/`height` read from the drawn plot area; omission is the fallback — the exporter then infers the frame from the drawn fallback geometry.
- Value-axis labels: when the fallback keeps category labels but intentionally omits numeric value-axis tick labels, set `show_value_axis_labels: false`.
- Freeform chart text: transcribe center labels, source notes, and other in-chart annotations as companion `caption` / `note` / `notes` entries with explicit slide-coordinate bounds; do not rely on fallback `<text>` children to survive native export.
- Native chart typography mirrors the SVG fallback. Copy the fallback's shared chart font into `style.font_family` and visible chart text sizes into the matching metadata fields (`title_font_size`, `subtitle_font_size`, `axis_font_size`, `note_font_size`, etc.) only when role sizes differ; otherwise let the exporter infer them from visible fallback text. When a visible chart title, subtitle, or axis title needs its own size/color/font, write that field as an object with `text`, `font_size`, `font_family`, and `color`. Use `axis_title_font_size`, `legend_font_size`, or companion per-entry `font_size` only when the fallback visibly uses a separate size.
- Native table typography mirrors the SVG fallback. Write `style.font_family` and `style.font_size` from the visible table text; use `header_font_size` or per-cell `font_size` only when the fallback visibly does so. If the fallback has no explicit table font, Default uses the deck body family and declared `spec_lock.md` body anchor; Quick uses the concrete body family/size already resolved in active context.
- The marker group's transform stays translate/scale only (no rotate / matrix / skew).
- Visual parity is not a goal: the SVG drawing remains the designed visual and exports as editable DrawingML shapes; the native object is the data-backed counterpart with PowerPoint's chart/table-specific model. Never simplify the SVG design to match what a native object could show.

**Per-page verification** — after writing a page with selected native-ready objects, enumerate those objects and confirm a one-to-one match: every object has one parent marker and exactly one JSON metadata child. Finding one marker somewhere on a page is insufficient when the page contains multiple selected objects.

```bash
rg -n 'data-pptx-replace-with="(chart|table)"|<metadata type="application/json">' <project_path>/svg_output/<current_page>.svg
```


---

## 3. Visualization Reference

§1 loads only a selected page-local SVG. Default takes Usage/semantics from
§VII/§IX; Quick takes them from the current active-context page decision.

**Hard rule**: treat the loaded SVG as a page-local reference, not a required base. Default §IX or the Quick active-context page decision plus source data own the final information structure; never replicate the preview verbatim.

**Adaptation rules**:
- **Preserve**: Default-planned or Quick-resolved information relationships, data encoding, and every active content obligation
- **Page-local only**: a reference row applies only to its mapped page; never spread it across the deck
- **Flexible realization**: borrow, recombine, or depart from the preview's type and geometry when the current page is better served another way
- **Carry forward**: every authoritative label, value, unit, status, source, and explanatory block; never shorten or drop content to imitate a lighter catalog preview
- **Adapt**: project data and labels, dimensions, axes, legend, and spacing as the authored content requires
- **Project-owned**: palette, typography, container treatment, effects, background, and page chrome; catalog preview values are fallbacks, never defaults
- **Bound final body modules**: add or revise root-coordinate `data-pptx-bounds` on every visible direct root `<g>` copied into the final page; nested groups need none, chart geometry and local references are not content-boundary inputs, and catalog reference warnings never waive the final-page contract
- **Adjust with fidelity**: composition, axis ranges, grouping, and grid may change when the actual content, relationships, hierarchy, and data encoding remain complete
- **Forbidden**: treating preview structure as the page specification; omitting authoritative data points, labels, relationships, or explanatory content to fit it

> Templates: `templates/charts/`. `page_charts` maps one optional reference to one page; execution opens only that SVG.

### 3.1 Chart Coordinate Calibration

Coordinate calibration runs as a **conditional post-generation stage**, not
inside the SVG authoring loop. After SVG generation completes, if the deck
contains data-driven charts, run
[`verify-charts`](../workflows/stages/verify-charts.md). Default follows its
declared gate order; Quick runs calibration before its one lockless final
checker.

The authoring obligation is upstream: embed the
`<!-- chart-plot-area ... -->` marker on every active data-chart page during the
initial draft (§2.1). Verify-charts enumerates Default pages from the Design
Spec; Quick enumerates them from the still-active page decisions and cross-checks
the markers before feeding `svg_position_calculator.py`.

> Do NOT run `svg_position_calculator.py` during the initial draft. The calculator calibrates already-generated SVGs against their declared plot areas; running it before the SVG exists has nothing to compare against.
