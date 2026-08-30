---
description: Conditional quality-gate stage for data-chart geometry and encoding verification.
---

# Verify Charts Stage

> Conditional Generate-PPTX quality stage. Run after a deck containing data charts has finished SVG generation and before post-processing/export; it catches coordinate and encoding errors introduced while mapping source values into SVG marks. Default runs it context-independently from `design_spec.md` plus the SVGs; the lockless Quick branch runs in the same active session from the page decisions just authored — if that context is lost, restart Quick rather than inventing a page plan from finished files.

## When to Run

- The deck contains at least one chart where source values determine SVG geometry or encoding (bar lengths, point positions, arc angles, polygon vertices, connector endpoints, bubble centers/radii, flow widths, cell colors, word sizes).
- SVGs exist in `<project_path>/svg_output/` and `finalize_svg.py` / `svg_to_pptx.py` have not run. Default enters from its quality-gate order; Quick runs it before its one lockless final checker.

The calculator has direct models for bars, lines/scatter, pie/donut, radar, and grids. Composite charts are not out of scope: geometry that reduces to repeated direct calculations is `decomposable-calc`; data-driven geometry with no layout model is `manual-verify`, never silently skipped.

---

## Step 1: Build the chart-object list from the active profile authority

| Active profile | Object-list authority |
|---|---|
| Default Generate | `design_spec.md §IX` — every semantic object key whose `Visualization` entry declares value-driven SVG geometry; §VII only resolves a selected catalog reference, and one real §VII data-chart row may supply one legacy object for a page whose §IX predates object keys |
| Quick Generate | The still-active semantic object keys and page decisions, cross-checked one-for-one against every `chart-plot-area` marker found by one search of `svg_output/`; add a missing scoped marker, investigate an unexpected one, keep the list in active context only |

Incidental microvisuals not promoted by the profile authority are not inferred into the list: Default repairs §IX first; Quick decides promotion in active context and updates the marker before verification. Never guess from SVG content when §IX declares no data-driven object.

| Mode | `charts_index.json` keys | Notes |
|------|--------------------------|-------|
| `direct-calc` | `column_chart`, `horizontal_bar_chart`, `histogram_chart` | `calc bar`; `--horizontal` for horizontal bars; histogram bins are contiguous bars on the numeric x-axis |
| `direct-calc` | `line_chart`, `area_chart`, `scatter_chart` | `calc line`; area uses the line output as the top boundary, then closes to `y_max` |
| `direct-calc` | `pie_chart`, `donut_chart` | `calc pie`; donut passes `--inner-radius` |
| `direct-calc` | `radar_chart` | `calc radar` (separate subcommand) |
| `decomposable-calc` | `stacked_bar_chart`, `stacked_area_chart`, `grouped_bar_chart`, `dumbbell_chart`, `pareto_chart`, `dual_axis_line_chart`, `bullet_chart`, `butterfly_chart`, `waterfall_chart`, `box_plot_chart`, `gantt_chart`, `bar_of_pie_chart`, `pie_of_pie_chart`, `stock_chart` | Repeated direct calculations per the [verification recipes](../../scripts/docs/svg-pipeline.md#verification-recipes) |
| `partial-calc` | `bubble_chart`, `matrix_2x2` | `calc line` for x/y-driven `cx/cy`; radius only with an explicit size scale |
| `formula-verify` | `progress_bar_chart`, `gauge_chart`, `funnel_chart`, `sunburst_chart` | Quote the formula and resulting length/angle/width in the receipt |
| `manual-verify` | `sankey_chart`, `heatmap_chart`, `treemap_chart`, `word_cloud` | Data-driven, but no layout model; inspect and report |

**Family boundary**: this table covers every canonical `charts_index.json` key exactly once. Qualitative shape composition and Table references never enter the receipt merely because they contain shapes or numbers; named quadrants are composed through [`executor-structure.md`](../../references/executor-structure.md), and `chart/matrix_2x2` is reserved for plotted x/y data. Every embedded data chart is its own keyed §IX object.

```
P03 market-share   03_market_share.svg  type=bar     mode=direct-calc
P15 pareto-causes  15_pareto.svg        type=pareto  mode=decomposable-calc
```

If the list is empty, output `verify-charts: active profile declares no data-driven chart objects, nothing to verify` and stop.

---

## Step 2: Per object — read its SVG scope, calculate, compare, update

1. Read `<project_path>/svg_output/<page>.svg`; locate `<g id="<object-key>">` and its one plot-area marker (`chart-plot-area: object=<object-key> | …` inside `<g id="<object-key>-chartArea">`). A legacy unscoped marker with `id="chartArea"` is accepted only when the page has exactly one verified chart; a multi-chart page never mixes scoped and unscoped markers. Derive and add a missing scoped marker from the axes or center/radius before continuing.
2. Read only that object's data series and label/value elements.
3. **Read axis tick labels for every axis-based chart** — X-axis labels for horizontal bars, Y-axis labels for vertical bars and line-like charts. The first and last tick values give the axis range; pass it as attached `--value-range=min,max` / `--y-range=…` / `--x-range=…` (the attached form also protects a negative minimum). Radar takes `--max-value` from the outermost ring. With no tick labels, omit the range, let the calculator auto-normalize, and flag the receipt `scale=auto (no ticks)`.
4. **Local vs absolute**: content inside `<g transform="translate(cx, cy)">` has relative coordinates; the calculator outputs absolute ones. Add the translate to the SVG values or subtract it from the calculator output — one direction, consistently.
5. Run the matching command (see the [calculator documentation](../../scripts/docs/svg-pipeline.md#svg_position_calculatorpy) and recipes for decomposable, partial, formula, and manual modes):

   ```bash
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc bar --data "L1:V1,L2:V2" --area "x_min,y_min,x_max,y_max" --bar-width 120 --value-range=0,axis_max
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc line --data "x1:y1,x2:y2" --area "x_min,y_min,x_max,y_max" --y-range=0,max
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc pie --data "S1:V1,S2:V2" --center "cx,cy" --radius 200 [--inner-radius 120] --start-angle -90
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc radar --data "D1:V1,D2:V2,D3:V3" --center "cx,cy" --radius 200 --max-value 100
   ```

6. **Scale-aware comparison**: before declaring a mismatch, confirm every invocation used the axis range, plot area, center/radius, start angle, or size scale the SVG visually declares — for `calc bar` the header must show `Value scale: axis ticks (...)` when the SVG has ticks; `auto (max*1.1)` means go back to step 3. Never update the SVG with mismatched-scale output. When the scale matches and coordinates genuinely differ, update by hand — no regex or bulk replacement.

After updating any page, follow the profile's checker order. Default reruns `svg_quality_checker.py <project_path> --canonical-authoring --stage final --json`, which writes the current `final` report Step 7.3 requires. Quick completes every chart comparison/repair first, then returns to `quick-generate.md` §4 for its one lockless final checker — no checker call between chart pages.

---

## Step 3: Per-object receipt

One line per Step 1 object, including its semantic key; receipt count MUST equal the list length — that is the gate-closing evidence. Quick does not persist these lines.

```
verify-charts: 03_market_share.svg | object=market-share | type=bar | mode=direct-calc | scale=0-100 (from ticks) | calc=ran | svg=updated
verify-charts: 11_share_split.svg | object=share-split | type=pie | mode=direct-calc | scale=N/A | calc=ran | svg=updated | marker=added
verify-charts: 14_revenue_mix.svg | object=revenue-mix | type=stacked-bar | mode=decomposable-calc | scale=0-200 (from ticks) | calc=ran×3 | svg=updated
verify-charts: 18_market_bubbles.svg | object=market-bubbles | type=bubble | mode=partial-calc | xy=ran | radius=manual (scale missing) | svg=unchanged
verify-charts: 23_quarterly_progress.svg | object=quarterly-progress | type=progress | mode=formula-verify | formula=68/100×800=544px | svg=unchanged
verify-charts: 19_flow.svg | object=flow | type=sankey | mode=manual-verify | link widths consistent with values | svg=unchanged
```

---

## After verification

Default continues with [`generate-pptx`](../generate-pptx.md) Step 7; Quick returns to [`quick-generate`](../profiles/quick-generate.md) §4 for its final checker and direct export.
