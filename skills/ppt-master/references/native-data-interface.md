> See [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation.

# Native Data Interface

Conditional interface for preset pattern fills and PowerPoint-native chart/table replacement metadata. Load when either feature appears in the authored SVG.

## 1. Pattern Fill — `<pattern>` with PPTX preset annotation

`<pattern>` requests one fixed DrawingML preset; the converter does not render
the tile's arbitrary geometry. Use this interface only when that preset mapping
is intended.

`data-pptx-pattern="<preset>"` is the generated default for selecting the
intended preset from the enum below. The converter retains an `ltUpDiag`
fallback when the annotation is absent; the checker reports that fallback as a
non-blocking fidelity warning. Invalid explicit preset names remain errors
because they violate the closed OOXML enum.

Pattern colors may come from importer metadata (`data-pptx-fg` /
`data-pptx-bg`) or from the pattern's child paint. Without metadata, the first
child `<rect>` fill becomes the background and the first stroke (or other fill)
becomes the foreground. A missing background defaults to white; a missing
foreground means no native pattern fill can be emitted. The child geometry
itself is never used as a repeatable tile.

**Valid `data-pptx-pattern` values** (OOXML `ST_PresetPatternVal` — closed enum, anything outside makes PowerPoint open with "needs to be repaired"):

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid` — common typo)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

`svg_quality_checker.py` warns when a referenced pattern lacks the annotation;
it errors when the pattern uses `patternTransform` or names a preset outside
this enum.

## 2. PowerPoint-Native Chart / Table Replacement Markers (Opt-in)

Native PowerPoint tables and Excel-backed charts activate at export time only. Generated pages prepare dormant replacement metadata for independently planned native-ready objects while keeping hand-authored SVG geometry pixel-stable across PowerPoint / Keynote / LibreOffice / WPS.

**Hard rule — planned-object authoring**: Executor writes the marker and JSON metadata in the same edit only for a supported chart or pure text-grid table whose `design_spec.md §VII` row says `Native-ready: yes` ([`executor-chart.md`](./executor-chart.md) §2.2). `no`, `n/a`, and microvisuals outside §VII stay on the SVG fallback route. Canonical rectangular merged text cells may use the narrow `row_span` / `col_span` contract below; graphical cells stay unmarked. The marker group supplies visible SVG fallback children for browser/live-preview rendering and JSON metadata for `svg_to_pptx` native export.

**Hard rule — activation is the opt-in, dormant unless exported with `--native-charts-and-tables`**: A marker only declares that a group is eligible for PowerPoint-native Chart/Table replacement. Normal `svg_to_pptx.py` runs keep the fallback SVG children and convert them into independently editable DrawingML shapes. Pass `--native-charts-and-tables` only when the data source and chart/table-specific object model matter more than cross-renderer layout fidelity: it emits the PowerPoint Chart/Table object and skips the fallback children to avoid duplicates. Native styling preserves the core palette, text, axis, grid, and background colors where possible, but it is still a PowerPoint Chart/Table object rather than a pixel-identical SVG drawing.

The native route is deliberately data-object-first and may be lossy: marker-local labels, callouts, KPIs, guide lines, custom split/bin semantics, or styling that is absent from the payload may disappear or normalize. Export warns about this route-level risk and any narrower issue it can detect. Loss of visual parity is not grounds to remove an active marker that the emitter can otherwise convert; use the default SVG-fallback export when exact authored artwork matters more than a native data source and object-specific controls.

| Replacement marker | Native output | Required metadata |
|---|---|---|
| `<g data-pptx-replace-with="table">` | `<p:graphicFrame>` with `<a:tbl>` | bounds + `columns` or `rows` |
| `<g data-pptx-replace-with="chart">` | `<p:graphicFrame>` with `c:chart` / `cx:chart` + chart part + embedded workbook | bounds + `type`, plus chart data |

**Metadata placement**: Put JSON in one child
`<metadata type="application/json">`. The parent group's
`data-pptx-replace-with` value selects the table or chart schema, so the
metadata child does not repeat an object-kind attribute. Attribute JSON
(`data-pptx-json="..."`) remains read-compatible but is harder to XML-escape
correctly and is not canonical authoring.

**Bounds**: Provide `x`, `y`, `width`, and `height` in metadata, or as
`data-pptx-x` / `data-pptx-y` / `data-pptx-width` / `data-pptx-height` on the
marker group. If any bound is omitted, the exporter infers the object frame
from the visible fallback geometry; this keeps SVG fallback and native object
placement aligned. Complete explicit bounds are absolute slide coordinates;
marker/ancestor `translate` and `scale` transforms apply only when at least one
bound is inferred. `x`, `y`, `width`, and `height` must be finite and resolve
inside PowerPoint's 32-bit DrawingML coordinate range; `width` and `height`
must resolve to at least one EMU. Native table frames must additionally resolve
to at least one EMU per resolved row and column.

**Validation**: `svg_quality_checker.py` validates replacement marker kind, JSON
metadata, bounds/fallback availability, table rows/columns, supported chart
type, chart data shape, and any imported fallback baseline before export.

Imported marker freshness, fallback classification, provenance, and legacy
read compatibility are operational import concerns. Keep generated authoring
free of those attributes; use the exact behavior and field index in
[`conversion.md`](../scripts/docs/conversion.md#native-table-and-chart-import-claims).

```xml
<g id="p03-revenue-chart" data-pptx-replace-with="chart">
  <metadata type="application/json">
    {
      "x": 120, "y": 150, "width": 520, "height": 320,
      "type": "column",
      "title": "Revenue by Segment",
      "categories": ["Q1", "Q2", "Q3"],
      "series": [
        {"name": "Cloud", "values": [12, 15, 19]},
        {"name": "Services", "values": [8, 9, 11]}
      ]
    }
  </metadata>
  <!-- Visible SVG fallback for live preview / non-native export goes here. -->
</g>
```

**Table schema**: Native tables are rectangular DrawingML grids. Use `columns`
for the optional header row and `rows` for body rows; shorter rows are padded
with blank cells unless `strict_grid: true` is set. Tables may contain at most
1000 resolved rows and 1000 resolved columns. Use `column_widths` and
`row_heights` as relative weights. Weight lists must match the resolved grid,
contain finite non-negative numbers, and include at least one positive value.
If present, `header_rows` must be an integer from `0` through the resolved row
count. Write `strict_grid`, `style.band_row`, and cell `bold` as JSON booleans.
Cell objects accept `text`, `fill`, `color`,
`align`, `valign`, `bold`, `font_size`, `padding`, `border_color`, and
`border_width`, plus optional `lang`; the same `padding`, `border_color`,
`border_width`, and `lang` keys may also live under `style` as table defaults.
For multi-paragraph text, replace cell `text` with a non-empty `paragraphs`
list. Each entry is either a string or an object containing optional
`align: "l|ctr|r"` and exactly one of `text` or non-empty `runs`; empty
paragraph strings are preserved, and cell `text` / `paragraphs` are mutually
exclusive. Each run is an object with required string `text` and optional JSON
boolean `bold`, `italic`, `underline`, and `strike`, plus optional `color`,
`font_size`, one-typeface `font_family`, `lang`, and `alt_lang`. Unknown fields,
wrong types, empty run lists, multi-typeface `font_family`, and unsupported
colors fail fast. PPTX import requires exact physical row/grid topology and
normalizes source presentation-only run XML outside this closed schema only
when it contains no non-empty `rPr` / `defRPr` / `endParaRPr` `effectLst` or
`effectDag`. A table-cell run effect follows the blocking effect contract above
instead of entering either the native payload or an effect-free fallback.
Relationship-bearing text, extensions, structural line breaks, fields, tabs,
bullets, malformed run topology, and unsupported text-body structure remain
fallback-only.
Per-side cell borders use `borders.left|right|top|bottom`, where each value is
either `{ "style": "none" }` or
`{ "style": "solid", "color": "#RRGGBB", "width": <positive-px> }`.
Per-side borders are cell-only; legacy uniform `border_color` / `border_width`
remain supported as defaults that an individual side may override.
When `lang` is absent, export derives `zh-CN` for CJK text and `en-US`
otherwise. `style.band_row: false` disables both `<a:tblPr bandRow>` and
materialized alternating row fills. Native table typography mirrors the
visible SVG fallback: put `style.font_family` and `style.font_size` on the
marker from the table text already drawn, then use `style.header_font_size` or
per-cell `font_size` only when the fallback visibly differs. If the fallback
has no explicit table font, use the deck body family and locked body size from
`spec_lock.md`.

**Hard rule — table metadata is the native source of truth**: Every row,
summary line, value, and cell-level style that must survive
`--native-charts-and-tables` must be present in `columns` / `rows`. SVG fallback text is
discarded during native export. `svg_quality_checker.py` warns when visible
fallback `<text>` inside a native table marker does not appear in metadata.
For numeric or currency columns, use cell objects with `align: "r"`; SVG
`text-anchor="end"` does not carry into the native table.

**Merged table cells — canonical rectangular contract only**: Put positive JSON
integer `row_span` / `col_span` values on the merge anchor and keep every
covered grid cell blank. Spans must stay within the resolved rectangular grid
and may not overlap. The exporter emits the canonical DrawingML topology
(`rowSpan` on the top edge, `gridSpan` on the left edge, `hMerge` / `vMerge` on
covered cells). CamelCase aliases, raw OOXML merge fields, top-level merge lists,
nonblank covered cells, invalid spans, and overlaps fail fast. The PPTX importer
activates native reconstruction only for that same explicit rectangular topology
with empty merge-slave text bodies; other merge encodings remain fallback-only
with `unsupported-merge-topology`.

**Category chart schema**: `column`, `bar`, `line`, `area`, `pie`,
`doughnut`, `pieOfPie`, `barOfPie`, and `radar` use `categories` plus
`series[].values`. Pie-family charts (`pie`, `doughnut`, `pieOfPie`, and
`barOfPie`) must have exactly one series; the exporter assigns per-category
slice colors so single-series charts do not collapse into one solid color.
Column and bar charts may set per-point colors with `series[].point_colors`
or `series[].pointColors`; the list must match `series[].values` length.
Classic category charts may set native PowerPoint data labels with
`data_labels`. Use `data_labels: true` for default value labels, or an object
with `show_value`, `position`, `number_format`, `font_size`, `font_family`,
`bold`, `color`, and optional per-point `colors`. Supported label positions
depend on chart type: clustered column/bar labels may use `outside_end`,
`inside_end`, `inside_base`, or `center`; stacked / percent-stacked column/bar
labels may use `inside_end`, `inside_base`, or `center`; line labels may use
`above`, `center`, or `best_fit`; area labels do not emit a native label
position. To label only selected data points, use `data_labels.points` with
zero-based `idx` plus optional per-point `position`, `number_format`,
`font_size`, `font_family`, `bold`, and `color`.

**Combo chart schema**: `combo` uses shared `categories` plus either `plots[]`
or typed `series[]`. Each plot supports `type: "column" | "line" | "area"`,
its own `series`, and optional `axis: "secondary"` for a right-side value axis.
When primary and secondary plots genuinely use different category caches,
`plots[]` may also carry its own `categories` and `category_numeric`; the
workbook writer allocates independent category/value ranges. Typed `series[]`
continues to require the shared top-level categories.
Imported `plots[]` may carry `series_indices` so the verified source identity
where each `c:idx` equals its `c:order` survives when physical plot order differs
from legend order. If one plot supplies it, every plot must supply a same-length
list of unique non-negative JSON integers, and the combined values must form one
contiguous `0..N-1` range. Sources whose `idx` and `order` differ stay
fallback-only; typed `series[]` does not accept this plot-scoped field.
Typed `series[]` accepts the same `type` and `axis` fields per series, and
adjacent compatible series are grouped into the same PowerPoint plot. Area
series may set `fill_opacity` / `fillOpacity` as a `0..1` SVG opacity value
when the SVG fallback uses a transparent area fill under an opaque line. A line plot with `area_fill: true`
is exported as a PowerPoint area chart under the hood; `fill_opacity` only sets
the fill style and does not trigger conversion by itself. Combo export layers
area plots below columns and lines while preserving the original series indices.
Line and area series may set `line_width` / `lineWidth` in SVG px units to
match fallback `stroke-width`.

**Narrow classic-axis schema**: `axes` is a closed object with the roles
`category`, `value`, `secondary_category`, and `secondary_value`. Each role may
set only `kind` (`text`, `date`, or `value`, as appropriate), `position`,
`visible`, `label_position` (`next_to`, `none`, `low`, or `high`),
`number_format`, `minimum`, `maximum`, `major_unit`, `reverse`, and
`major_gridlines`. `major_unit` applies to value axes only. PPTX date-axis
**import** is deliberately narrow: numeric Excel date serials are accepted for
area charts and OHLC stock charts; arbitrary date-axis source families are not.
This contract is not a full `AxisSpec`: logarithmic scales, minor units/gridlines,
crossing values, display units, tick skipping, and other unlisted OOXML semantics
remain unsupported and fail closed on import.

**Narrow XY-axis schema**: `scatter` and `bubble` may use a closed `axes` object
with only `x` and `y` roles. Both roles have `kind: "value"`; `x.position`
is `bottom` or `top`, while `y.position` is `left` or `right`. Each accepts the
same closed fields above, and `major_unit` is valid on both value axes. PPTX
import requires the plot to reference exactly two mutually cross-linked
`c:valAx` nodes and separately enforces the closed field/topology gates. The
native writer emits and the importer reads back every field in this closed
contract. Scatter import derives the effective `scatter_style` from a uniform
per-series line/marker/smooth state; unsupported or nonuniform states remain
fallback-only. The normalized SVG fallback newly consumes only
`axes.x.major_gridlines` and `axes.y.major_gridlines`; the other fields do not
imply full visual-axis parity.

**XY chart schema**: `scatter` and `bubble` use `series[].x` + `series[].y`;
`bubble` also requires one `series[].size` / `series[].sizes` value per point.
`series[].points` is also accepted as `[x, y]` / `[x, y, size]` tuples or
`{x, y, size}` objects.

**Chart typography**: Metadata sizes use the same px-style unit as SVG text
(`1px = 0.75pt`). `style.font_family` and the role-specific
`title_font_size`, `subtitle_font_size`, `axis_font_size`,
`axis_title_font_size`, `legend_font_size`, and `note_font_size` fields are
required only when the native object must preserve typography that cannot be
inferred unambiguously from the visible fallback.

**Chart chrome metadata**: Text that is visually part of the chart must be in
metadata, not only in SVG fallback children; metadata MUST still match visible
fallback chrome. `title` becomes the native chart title on classic charts; it
is not an object name, so use `name` for semantic object naming. `subtitle`
becomes the second rich-text line of that classic chart title. `title`,
`subtitle`, and axis-title values may be strings or objects with `text`,
`font_size`, `font_family`, and `color` when the fallback uses local role
typography. `svg_quality_checker.py` rejects `title`, `subtitle`, or axis-title
metadata whose text is not visible inside the replacement marker's fallback. Direct
`--native-charts-and-tables` export keeps the chart native but omits that inconsistent
chrome with a warning. chartEx keeps PowerPoint's empty `<cx:title>` and emits
the title / subtitle as companion editable text boxes until chartEx rich titles
are validated. Axis
titles are optional and explicit: use `axis_titles` with
`category`, `value`, `x`, `y`, or `secondary_value` keys, or the root aliases
`category_axis_title`, `value_axis_title`, `x_axis_title`, `y_axis_title`, and
`secondary_value_axis_title`; do not add semantic axis titles that are not
visible in the fallback. Set `show_value_axis_labels: false` when the fallback
keeps category labels but omits numeric value-axis tick labels, such as a radar
chart without radial coordinates. Native legends are metadata-controlled: use
`show_legend: true` and `legend_position` only when the fallback's legend is
meant to be replaced by PowerPoint's native legend.
Companion text such as `caption`, `source`, `note`, `notes`, `footnote`, and
`footnotes` is exported as editable PPT text boxes next to the native chart. A
companion entry may be a string or an object with `text`, `x`, `y`, `width`,
`height`, `font_size`, `color`, `align`, and `bold`; explicit bounds are
recommended so the native export matches the SVG fallback placement. Explicit
companion bounds are slide coordinates, not local coordinates inside a
transformed marker group. Use companion text for chart captions, source notes,
center labels, and freeform annotations; use `data_labels` for values that
belong to chart points.

**Chart color styling**: For classic native charts, `style.colors` sets series
colors. The exporter also writes explicit chart-area fill, plot-area fill,
axis line, gridline, and label text colors so PowerPoint does not substitute a
white/default-theme chart. If omitted, the exporter infers these colors from
the visible SVG fallback: the largest panel-like `<rect>` becomes the chart
background, fallback text supplies label color, and fallback strokes supply
axis/grid colors. Override any of them explicitly under `style` with
`chart_area_fill`, `plot_area_fill`, `text_color`, `axis_color`, and
`grid_color`; use `"none"` for transparent chart or plot area fill. Generated
payloads default to uppercase `#RRGGBB`. The exporter retains compatibility for
`#RGB`, `rgb(...)` / `rgba(...)`, and common CSS names, normalizing them to
6-digit OOXML RGB. Bar and column series also disable PowerPoint's negative-value
inversion so negative bars keep the same series fill instead of turning into
white/theme fill.

For ChartEx native charts, valid payload `style.colors` (or root `colors`)
populate the ChartEx color-style part instead of being replaced by a fixed
accent1–accent6 list. Other ChartEx style semantics remain normalized.

**PowerPoint chartEx schema**: `treemap`, `sunburst`, `histogram`, `pareto`,
`boxWhisker`, `waterfall`, and `funnel` use Office 2016+ chartEx parts. Use
these input shapes:

| Type | Required data |
|---|---|
| `treemap`, `sunburst` | `values` plus either `levels` (`levels[level][point]`) or path-style `categories` (`[["Region", "Group", "Leaf"], ...]`) |
| `treemap` display note | Top-level group labels default to `overlapping`; override with `parent_label_layout: "banner" \| "overlapping" \| "none"`. PowerPoint labels only the top level and leaves — intermediate levels group tiles spatially without labels (sunburst shows every ring). |
| `histogram` | `values` |
| `pareto`, `waterfall`, `funnel` | `categories` + `values`; `waterfall` also accepts `subtotals` / `subtotal_indices` point indexes |
| `boxWhisker` | `series[].values`; optional `series[].categories` per value |

> Note: chartEx files are valid PPTX and editable in PowerPoint; non-Microsoft
> renderers can display a limited subset.

**Stock chart schema**: `stock` uses numeric Excel date serials in
`categories` or `dates`, plus exactly four series in open / high / low / close
order. Use either `series` with four entries, or top-level `open`, `high`,
`low`, and `close` arrays. PPTX import currently recognizes only canonical OHLC
stock charts with shared numeric date caches, `hiLowLines`, and `upDownBars`.
Safe stock series style may pass the structural gate, but stock series,
`hiLowLines`, and up-down bar local styling can still normalize under the
data-object-first contract. HLC, volume, noncanonical structure, and style XML
outside the safe parsing boundary stay fallback-only.

**PPTX chart-import boundary**: The importer recognizes conservative classic
single-plot charts plus the verified scatter/bubble XY-axis, column/line/area
combo, area date-axis, canonical OHLC stock, radar, safe `of_pie` `serLines`,
axis/title/legend normalization, and bar/column gap/overlap subsets. Imported
`gapWidth` must be one canonical integer in `0..500`; imported `overlap` must be
one canonical integer in `-100..100`. Both values intentionally normalize to
the native writer contract rather than claiming exact source-style retention.
Malformed, duplicate, or out-of-range values fail closed.

ChartEx import is closed to seven validated data models: `treemap`, `sunburst`,
`histogram`, `pareto`, `box_whisker`, `waterfall`, and `funnel`. The importer
retains their supported hierarchy/category/value/series/subtotal topology for
native read-back. Numeric cache values must be non-empty and finite, and cache
counts/indexes must be canonical non-negative decimal integers with exact,
contiguous topology; malformed, non-numeric, `NaN`, infinite, sparse, duplicate,
or mismatched caches fail closed. ChartEx style, axis, label, and binning details
outside the payload normalize. Full `AxisSpec`, arbitrary ChartEx families or
presentation fidelity, arbitrary stock variants, and axis/combo/date-axis
semantics outside the closed fields above remain fallback-only. The C4/C5
import work does not expand the normalized SVG renderer and does not reduce
existing SVG-marker-to-native writer support.

**Deferred chart types**: Exploded pie / doughnut variants, `map`, `heatmap`,
`bullet`, and `gantt` are intentionally outside the current native-object
support boundary. The exporter fails fast for these types until each mapping is
implemented and validated one by one.

**Supported chart types**:

- `column`, `bar`: `clustered`, `stacked`, or `percentStacked` (`grouping`)
- `line`: `standard`, `stacked`, or `percentStacked` (`grouping`); `line` or `lineMarker` (`line_style`, default `line` / no markers)
- `area`: `standard`, `stacked`, or `percentStacked` (`grouping`)
- `pie`: exactly one series, per-slice colors
- `doughnut`: exactly one series, per-slice colors
- `pieOfPie`, `barOfPie`: exactly one series, per-slice colors
- `radar`, `radarMarkers`, `radarFilled`
- `scatter`: `marker` (default), `lineMarker`, `line`, `smoothMarker`, or `smooth` (`scatter_style`)
- `bubble`: x/y/size series
- `combo`: `column`, `line`, and `area` plots, optional secondary value axis
- `treemap`, `sunburst`: hierarchical chartEx charts
- `histogram`, `pareto`
- `boxWhisker`
- `waterfall`, `funnel`
- `stock`: open / high / low / close series

3D chart aliases (`3DColumn`, `3DBar`, `3DLine`, `3DArea`, `3DPie`, cone,
cylinder, pyramid variants, and `surface`) are unsupported.

Native legends are opt-in through `show_legend: true`; `legend_position`
defaults to `bottom` and accepts `top`, `left`, or `right`.

**Forbidden — replacement marker transforms**: Do not rotate, skew, or matrix-transform table/chart replacement groups. Translate / scale is accepted; complex transforms fail export because PowerPoint-native table/chart frames do not preserve arbitrary SVG transforms.
