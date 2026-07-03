# SVG Visualization Template Library

This directory contains the standardized SVG visualization templates used by PPT Master — charts, infographics, process diagrams, relationship diagrams, and strategic frameworks. The directory name `charts/` is kept for backward compatibility; the library scope is broader than charts.

## Source of truth

[`charts_index.json`](./charts_index.json) is the single source of truth for the library: total count + one selection-rule `summary` per template (format: `"Pick for X. Skip if Y (use other_key)."`). Both human readers and AI roles read it in full — there is no category/keyword sub-index. Selection is done by semantic match against the summary list in one pass.

To browse the library, open `charts_index.json` and scan the `charts` block top-to-bottom; each entry's `summary` answers "when do I pick this, when do I skip" directly.

## Style rules

See [`CHART_STYLE_GUIDE.md`](./CHART_STYLE_GUIDE.md) for color palette, typography, and SVG authoring conventions all templates must follow.

## Native editable export markers

Some chart templates include a `<g data-pptx-native="chart">` marker. The default SVG export path is unchanged: the fallback vector artwork is exported exactly as drawn. When `svg_to_pptx.py --native-objects` is enabled, that marked fallback group is replaced with an editable PowerPoint chart using the JSON metadata inside the child `<metadata data-pptx-native="chart">` node.

Native chart markers are opt-in and must include explicit `name`, `x`, `y`, `width`, and `height` fields so the editable chart frame aligns with the fallback drawing. Keep legends, explanatory cards, and source notes outside the marker when they should remain as separate editable shapes.

| Family | Native-marker templates | Use when |
|---|---|---|
| Category comparison | `column_chart`, `horizontal_bar_chart`, `grouped_bar_chart`, `stacked_bar_chart` | Comparing named categories, rankings, or stacked totals |
| Time trend | `line_chart`, `area_chart`, `stacked_area_chart`, `dual_axis_line_chart` | Showing direction, volume, cumulative share, or two-axis trends |
| Part-to-whole | `pie_chart`, `donut_chart`, `pie_of_pie_chart`, `bar_of_pie_chart`, `treemap_chart`, `sunburst_chart` | Showing share, long-tail split, or hierarchy composition |
| Distribution and relationship | `scatter_chart`, `bubble_chart`, `histogram_chart`, `pareto_chart`, `box_plot_chart` | Showing correlation, spread, frequency, defects, or statistical ranges |
| Specialty business charts | `waterfall_chart`, `funnel_chart`, `stock_chart`, `radar_chart` | Showing bridges, conversion stages, OHLC movement, or multi-axis capability profiles |

## Usage

Before generating a chart page, open the corresponding `<key>.svg` file to read its structure and layout. Files are named after the `key` field in `charts_index.json` (e.g. `column_chart.svg`, `quadrant_bubble_scatter.svg`). Templates are named by visual structure, not by business-model name — keywords like SWOT, BCG, PEST, OKR, Porter's Five Forces, Value Chain are matched via each template's `summary` field.
