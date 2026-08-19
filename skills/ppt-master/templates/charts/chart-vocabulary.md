# Chart Expression Vocabulary

This is the complete planning-side map of the 33 canonical Chart references.
Choose from the page's actual information relationship, then retain the exact
`chart/<key>` identifier. This file deliberately contains no SVG construction,
data-binding, coordinate, label-placement, styling, or export instructions;
those decisions belong to Executor after selection.

**Reference — not a constraint**: each description states what the visual
encoding represents. It is not a ranking, recommendation, threshold, quota, or
substitute for judgment from the current data and communication goal. Zero
Chart selections remains valid.

## 1. Change over time

| Canonical reference | Encoded relationship |
|---|---|
| `chart/line_chart` | Values positioned along a continuous axis, with connected marks showing change or direction. |
| `chart/area_chart` | A continuous series whose filled area emphasizes magnitude across the axis. |
| `chart/stacked_area_chart` | Multiple filled series whose layers encode both total magnitude and changing composition. |
| `chart/dual_axis_line_chart` | Two continuous series measured on separate value scales. |
| `chart/stock_chart` | Open, high, low, and close values across ordered dates. |
| `chart/waterfall_chart` | Sequential positive and negative contributions connecting a starting value to an ending value. |

## 2. Category comparison and rank

| Canonical reference | Encoded relationship |
|---|---|
| `chart/column_chart` | Category values encoded by vertical length from a shared baseline. |
| `chart/horizontal_bar_chart` | Category values encoded by horizontal length from a shared baseline. |
| `chart/grouped_bar_chart` | Multiple series placed side by side within shared categories. |
| `chart/stacked_bar_chart` | Category totals divided into value-driven component lengths. |
| `chart/butterfly_chart` | Two datasets mirrored around one shared category axis. |
| `chart/dumbbell_chart` | Two values per item joined to expose their gap and direction. |
| `chart/pareto_chart` | Descending category contributions paired with their cumulative share. |

## 3. Target and progress

| Canonical reference | Encoded relationship |
|---|---|
| `chart/bullet_chart` | Actual values, targets, and optional performance bands on compact linear scales. |
| `chart/progress_bar_chart` | Bounded completion values encoded as filled portions of linear tracks. |
| `chart/gauge_chart` | One bounded value positioned against a circular or semicircular domain and reference marks. |

## 4. Distribution and multivariable relationship

| Canonical reference | Encoded relationship |
|---|---|
| `chart/histogram_chart` | Observation frequency encoded across contiguous numeric bins. |
| `chart/box_plot_chart` | Median, quartiles, spread, and outliers summarized for one or more groups. |
| `chart/scatter_chart` | Two numeric variables encoded by x/y position. |
| `chart/bubble_chart` | Two variables encoded by x/y position and a third by mark size. |
| `chart/heatmap_chart` | Values at row-column intersections encoded by color intensity. |
| `chart/radar_chart` | Multiple measures positioned on radial axes for one or more entities. |
| `chart/matrix_2x2` | Items positioned by two numeric dimensions, with optional magnitude encoded by radius. |

## 5. Part-to-whole and hierarchy

| Canonical reference | Encoded relationship |
|---|---|
| `chart/pie_chart` | Flat parts of one whole encoded by sector angle and area. |
| `chart/donut_chart` | Flat parts of one whole encoded around an open center. |
| `chart/pie_of_pie_chart` | One composition with selected parts expanded into a secondary pie. |
| `chart/bar_of_pie_chart` | One composition with selected parts expanded into a secondary stacked bar. |
| `chart/treemap_chart` | Hierarchical or grouped parts encoded as nested rectangular areas. |
| `chart/sunburst_chart` | Hierarchical parts encoded as concentric radial levels and angular spans. |

## 6. Flow, schedule, and weighted text

| Canonical reference | Encoded relationship |
|---|---|
| `chart/funnel_chart` | Ordered stage values encoded as changing widths through a conversion sequence. |
| `chart/sankey_chart` | Magnitude moving between nodes encoded by connection width. |
| `chart/gantt_chart` | Tasks positioned and sized by dates or durations along a time axis. |
| `chart/word_cloud` | Term weight or frequency encoded by type size. |
