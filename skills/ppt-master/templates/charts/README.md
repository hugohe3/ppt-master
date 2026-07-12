# SVG Visualization Template Library

This directory contains the standardized SVG visualization templates used by PPT Master — charts, infographics, process diagrams, relationship diagrams, and strategic frameworks. The directory name `charts/` is kept for backward compatibility; the library scope is broader than charts.

## Source of truth

[`charts_index.json`](./charts_index.json) is the single source of truth for the library: total count + one selection-rule `summary` per template (format: `"Pick for X. Skip if Y (use other_key)."`). Both human readers and AI roles read it in full — there is no category/keyword sub-index. Selection is done by semantic match against the summary list in one pass.

To browse the library, open `charts_index.json` and scan the `charts` block top-to-bottom; each entry's `summary` answers "when do I pick this, when do I skip" directly.

## Style rules

See [`CHART_STYLE_GUIDE.md`](./CHART_STYLE_GUIDE.md) for color palette, typography, and SVG authoring conventions all templates must follow.

## Native editable export markers

Supported data chart templates include a `<g data-pptx-native="chart">` marker by default, and pure text-grid table templates include a `<g data-pptx-native="table">` marker the same way. The default SVG export path is unchanged: the fallback vector artwork is exported exactly as drawn. When `svg_to_pptx.py --native-objects` is enabled, that marked fallback group is replaced with an editable PowerPoint chart or table using the JSON metadata inside the child `<metadata data-pptx-native="...">` node.

`--native-objects` is an explicit editable-first opt-in and may be lossy or visually normalized. Marker-local value labels, center KPIs, callouts, quadrant notes, fixed axis ranges, and custom binning/splits may not survive native replacement unless represented by the payload. ChartEx palette entries do survive when supplied through valid payload colors, but this does not preserve every ChartEx style detail. Detectable information-loss risks should be reported as warnings, not handled by disabling an otherwise supported native marker. Review those warnings and compare the native export with the default SVG export before delivery.

Native marker authoring remains active for all 23 currently supported data-chart templates:

| Family | Active native-marker templates | Native output |
|---|---|---|
| Category comparison | `column_chart`, `horizontal_bar_chart`, `grouped_bar_chart`, `stacked_bar_chart` | Classic category charts |
| Time trend | `line_chart`, `area_chart`, `stacked_area_chart`, `dual_axis_line_chart` | Classic line/area/combo charts |
| Part-to-whole | `pie_chart`, `donut_chart`, `pie_of_pie_chart`, `bar_of_pie_chart`, `treemap_chart`, `sunburst_chart` | Classic pie-family or ChartEx hierarchy charts |
| Distribution and relationship | `scatter_chart`, `bubble_chart`, `histogram_chart`, `pareto_chart`, `box_plot_chart` | Classic XY or ChartEx distribution charts |
| Specialty business charts | `waterfall_chart`, `funnel_chart`, `stock_chart`, `radar_chart` | ChartEx or classic specialty charts |
| Text-grid tables | `basic_table`, `financial_statement_table` | Native DrawingML tables |

Markers must include explicit `name`, `x`, `y`, `width`, and `height` fields so the editable frame aligns with the fallback drawing. Keep legends, explanatory cards, source notes, center KPIs, and custom callouts outside the marker when they must remain as separate editable shapes; otherwise accept and review the native-export warning. Canonical rectangular merged text cells may use anchor-only `row_span` / `col_span` metadata with blank covered cells; nonrectangular merges and graphical cells (harvey balls, rating dots, avatars) stay unmarked on the SVG fallback route. Per-side borders, plain multi-paragraph cells, and the closed run-rich paragraph schema use the contracts in [`shared-standards.md`](../../references/shared-standards.md#native-pptx-table--chart-markers-opt-in). Relationship-bearing text, structural line breaks, fields, tabs, bullets, and arbitrary rich-text OOXML stay on the SVG fallback route.

## Usage

Before generating a chart page, open the corresponding `<key>.svg` file to read its structure and layout. Files are named after the `key` field in `charts_index.json` (e.g. `column_chart.svg`, `quadrant_bubble_scatter.svg`). Templates are named by visual structure, not by business-model name — keywords like SWOT, BCG, PEST, OKR, Porter's Five Forces, Value Chain are matched via each template's `summary` field.
