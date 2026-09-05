> See [`executor-base.md`](./executor-base.md) for page authoring and [`shared-standards-core.md`](./shared-standards-core.md) for the mandatory SVG foundation and object-local authority boundary.

# Native Data Interface

Sole conditional interface for preset pattern fills and PowerPoint-native chart/table replacement — eligibility, markers, metadata schemas, and export activation. Load only when either feature is selected for the authored SVG. Import-side normalization and the closed PPTX import boundaries live in [`conversion.md`](../scripts/docs/conversion.md#native-table-and-chart-import-claims).

## 1. Pattern Fill — `<pattern>` with PPTX preset annotation

A `<pattern>` requests one fixed DrawingML preset; the converter never renders the tile's own geometry. Write `data-pptx-pattern="<preset>"` from the closed enum below (absent annotation falls back to `ltUpDiag` with a fidelity warning; an invalid name is an error because PowerPoint opens the file as "needs to be repaired"). Colors come from `data-pptx-fg` / `data-pptx-bg` or the pattern's child paint — the first child `<rect>` fill is the background (default white) and the first stroke or other fill the foreground (required). `patternTransform` is an error.

| Category | Values |
|---|---|
| Grids | `smGrid` · `lgGrid` · `dotGrid` *(no `ltGrid`)* |
| Diagonal lines | `ltUpDiag` · `ltDnDiag` · `dkUpDiag` · `dkDnDiag` · `wdUpDiag` · `wdDnDiag` · `dashUpDiag` · `dashDnDiag` · `diagCross` |
| Horizontal / vertical lines | `horz` · `vert` · `ltHorz` · `ltVert` · `dkHorz` · `dkVert` · `narHorz` · `narVert` · `dashHorz` · `dashVert` · `cross` |
| Percent fills | `pct5` · `pct10` · `pct20` · `pct25` · `pct30` · `pct40` · `pct50` · `pct60` · `pct70` · `pct75` · `pct80` · `pct90` |
| Checks & confetti | `smCheck` · `lgCheck` · `smConfetti` · `lgConfetti` |
| Decorative | `horzBrick` · `diagBrick` · `weave` · `plaid` · `trellis` · `zigZag` · `wave` · `sphere` · `divot` · `shingle` · `solidDmnd` · `openDmnd` · `dotDmnd` |

## 2. PowerPoint-Native Chart / Table Replacement Markers (Opt-in)

The complete visible SVG fallback stays required for preview and default export; Chart/Table authority is object-local:

- **SVG-first (default)** — free-design, Brand-only, and Style-only authoring omits `data-pptx-native-authority`; the visible subtree is the design authority and JSON its derived projection. Canonical authoring records `data-pptx-fallback-sha256` only after fallback and JSON are synchronized; a later visible edit regenerates the JSON and re-stamps. A missing or stale baseline keeps fallback export available but makes `--native-charts-and-tables` fail closed.
- **JSON-first (template / native source)** — a validated PPTX import or template-owned object writes `data-pptx-native-authority="json"`; inline JSON is the authority and the visible subtree an approximate derived preview regenerated from it. Legal only on active `chart` / `table` replacement groups.

Both keep the JSON inside the SVG; `native_payloads.json.gz` is for opaque shape restoration only.

**Hard rule — selected-object authoring**: write the marker and JSON for every supported chart and pure text-grid table in the same edit — both are native-ready by default, and an unactivated marker changes no export, so never skip an eligible object. Default reads the key from §IX `Native-ready: <object-key>=yes|no; …`; Quick assigns the same page-local `kebab-case` key before drawing; the key is the marker group `id` and metadata `name`. A catalog `family/key`, §VII row, numeric content, or another ready object never implies eligibility; `=no` entries and incidental microvisuals stay on the fallback route; a legacy bare `Native-ready: yes|no` maps only to the page's sole eligible object. **MUST — atomic authoring**: one object's visible fallback, `data-pptx-replace-with` marker, and single JSON `<metadata>` child are one authoring unit written while the data is in context, never deferred to `verify-charts`, the final gate, or export. Then stamp SVG-first objects:

```bash
python3 skills/ppt-master/scripts/stamp_native_fallbacks.py "<svg-file-or-directory>" --write   # read-only without --write; skips JSON-first
```

The hash is a synchronization receipt, not proof of semantic equivalence; never stamp stale JSON to satisfy validation.

**Hard rule — activation is the opt-in**: a marker only declares eligibility. Normal `svg_to_pptx.py` converts the fallback children into editable DrawingML shapes; `--native-charts-and-tables` emits the PowerPoint Chart/Table object and discards the fallback children, so everything the fallback shows lives in the payload — data, point emphasis, line/area treatment, spacing, chrome, and companion text — and the final checker's parity findings block that export until they do. A convertible marker stays even when a detail has no native field: it becomes companion text or an unmarked sibling object, never a simpler drawing.

| Replacement marker | Native output | Required metadata |
|---|---|---|
| `<g data-pptx-replace-with="table">` | `<p:graphicFrame>` with `<a:tbl>` | bounds + `columns` or `rows` |
| `<g data-pptx-replace-with="chart">` | `<p:graphicFrame>` with `c:chart` / `cx:chart` + chart part + embedded workbook | bounds + `type`, plus chart data |

**Metadata placement and bounds**: one child `<metadata type="application/json">`; the marker's `data-pptx-replace-with` selects the schema. Provide `x`, `y`, `width`, `height` in metadata or as `data-pptx-x/y/width/height` on the group (complete explicit bounds are absolute slide coordinates; omitted bounds are inferred from the fallback geometry); JSON-first markers require all four in metadata. Classic charts accept a root `plot_area` rectangle inside the frame. Ranges, read-compatible spellings, and what the checker validates: [`native-data.md`](../scripts/docs/native-data.md).

```xml
<g id="p03-revenue-chart" data-pptx-replace-with="chart">
  <metadata type="application/json">
    {
      "x": 120, "y": 150, "width": 520, "height": 320,
      "name": "p03-revenue-chart",
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

**Hard rule — project by the selected authority**: SVG-first metadata describes the same data and visible chrome as its fallback — for a chart every category/point and series value (`null` for a break in a line), x/y/size data, visible point colors and markers (`line_style` / `point_colors`), line/area treatment (a line over a translucent fill is a `combo` of an area plot and a line plot), title/axis/legend chrome, companion text, bounds, and typography native export cannot infer; bar categories follow payload order top-down, and bar spacing, clustered overlap, and where a line starts inside `plot_area` are read from the fallback; for a table every resolved cell, header/summary line, rectangular span, cell style, alignment, bounds, and typography. JSON-first metadata is the authority and its preview may be approximate. Never simplify the artwork to fit the payload: when the closed payload cannot carry required data or topology, Default returns the native-ready decision upstream and Quick revises it before drawing; only the resolved non-native object stays unmarked, and an explicit `=yes` is never silently ignored. **Per-page verification**: every `=yes` key matches exactly one marker with one JSON child, and `=no` / unlisted objects have none — `rg -n 'data-pptx-replace-with="(chart|table)"|<metadata type="application/json">' <project_path>/svg_output/<current_page>.svg`.

### Table schema — `ppt-master.semantic-table.v2`

Every payload carries that exact `schema`; `columns` holds the optional header row and `rows` the body rows; `column_widths` / `row_heights` are relative weights. A cell is a string or an object with `text` (or `paragraphs` for rich text), `fill`, `color`, `align` (`l` / `ctr` / `r`), `valign` (`top` / `middle` / `bottom`), `bold`, `font_size`, `padding`, and per-side `borders` (each side is `{"style": "none"}` or `{"style": "solid", "color", "width"}`; a border without `style` is rejected); exact repetition may be factored into `defaults.cell` / `defaults.paragraph` / `defaults.run` (cell fields such as `align`, `valign`, `padding`, `font_size` go under `defaults.cell`, never directly under `defaults`) and named `cell_styles`. Merged cells use positive `row_span` / `col_span` on the anchor with every covered cell as `{"merge_continuation": true}`. The complete field grammar: [`native-data.md`](../scripts/docs/native-data.md).

**Hard rule — the table payload is complete**: every row, summary line, value, and cell style that must survive `--native-charts-and-tables` is in `columns` / `rows`, because fallback text is discarded on that route. A payload holding only `font_size` and a uniform border is not complete when the fallback draws a header band, row or column fills, first-column emphasis, non-uniform row heights, or sparse rules. Numeric or currency columns use cell objects with `align: "r"` (`text-anchor="end"` does not carry).

### Chart schemas

Supported `type` values: `column`, `bar`, `line`, `area` (each with `grouping`), `pie`, `doughnut`, `pieOfPie`, `barOfPie`, `radar`, `radarMarkers`, `radarFilled`, `scatter`, `bubble`, `combo`, `treemap`, `sunburst`, `histogram`, `pareto`, `boxWhisker`, `waterfall`, `funnel`, `stock`. Category charts take `categories` plus `series[].values`; XY charts take `series[].x` / `y` (bubble adds `size`); combo takes `plots[]` or typed `series[]`; ChartEx types take their own hierarchy or value fields. `data_labels` (column / bar / line / area plots only; other types show values through companion text), `axes`, `axis_titles`, `show_legend` / `legend_position`, companion text (`caption`, `source`, `note`), and `style.colors` are the chrome fields. 3D aliases and `surface` are unsupported; exploded pie, `map`, `heatmap`, `bullet`, and `gantt` fail fast. Every field, enum, and range: [`native-data.md`](../scripts/docs/native-data.md).

**Chart chrome and color**: SVG-first metadata matches the fallback chrome and reads it literally — the dominant stroke of elements named `axis` becomes `style.axis_color` and of those named `grid` becomes `style.grid_color` (unlabeled lines fall back to the marker's dominant stroke), numbers keep their written form (a payload `73.0` renders as `73` unless `number_format` says otherwise), and marker text that is not a category, data label, axis label, or legend entry needs a companion entry; JSON-first owns its chrome. Generated payloads use uppercase `#RRGGBB`. Negative bars keep the series fill. The final checker tags SVG-first parity findings `blocks --native-charts-and-tables export`; that export refuses them, so clear them before exporting the native variant.

**Forbidden — replacement marker transforms**: no rotate, skew, or matrix on table/chart groups; translate/scale only, because native frames cannot carry arbitrary SVG transforms.
