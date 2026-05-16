---
description: Verify chart coordinates against the design spec using svg_position_calculator.py
---

# Verify Charts Workflow

> Standalone post-generation step. Run after a deck containing data charts has finished SVG generation, before post-processing & export. Catches the 10–50 px coordinate errors AI models routinely introduce when mapping data to pixel positions.

This workflow is **independent**: it reads `design_spec.md` and the generated SVGs, then runs the calculator script — no upstream conversation context required. Safe to invoke in a fresh session.

## When to Run

- The deck contains one or more data visualization charts where source values determine SVG geometry: bar lengths/heights, point positions, arc angles, polygon vertices, connector endpoints, bubble centers/radii, or flow widths/paths.
- SVGs are generated to `<project_path>/svg_output/` and `svg_quality_checker.py` has passed.
- Post-processing (`finalize_svg.py`, `svg_to_pptx.py`) has **not yet** run.

The calculator has direct CLI models for simple bars, lines/scatter, pie/donut, radar, and grid layouts. Composite/derived charts are **not automatically out of scope**: if their geometry reduces to repeated direct calculations, include them as `decomposable-calc`; if the calculator has no layout model but the SVG geometry is still data-driven, include them as `manual-verify` so they are not silently skipped.

---

## Step 1: Build the page list from the design spec

Read `<project_path>/design_spec.md` §VII Visualization Reference List (authoritative deck plan; cross-check against §IX page outline) and include every page whose SVG geometry is driven by data values. Classify each included page into exactly one mode:

| Mode | `charts_index.json` keys | Notes |
|------|--------------------------|-------|
| `direct-calc` | `bar_chart`, `horizontal_bar_chart` | Use `calc bar`; add `--horizontal` for horizontal bars. |
| `direct-calc` | `line_chart`, `area_chart`, `scatter_chart` | Use `calc line`; area uses line output as the top boundary, then closes to `y_max`. |
| `direct-calc` | `pie_chart`, `donut_chart` | Use `calc pie`; donut passes `--inner-radius`. |
| `direct-calc` | `radar_chart` | Use `calc radar`; separate subcommand, not under `calc pie`. |
| `decomposable-calc` | `stacked_bar_chart`, `stacked_area_chart`, `grouped_bar_chart`, `dumbbell_chart`, `pareto_chart`, `dual_axis_line_chart`, `bullet_chart`, `butterfly_chart`, `waterfall_chart`, `box_plot_chart`, `gantt_chart` | Verify by repeated direct calculations; see recipes below. |
| `partial-calc` | `bubble_chart` | Use `calc line` for `cx/cy`; verify radius only when a size scale is explicit. |
| `formula-verify` | `progress_bar_chart`, `gauge_chart`, `funnel_chart` | One-line math; record the formula and resulting length/angle/width in the receipt, no calculator call needed. |
| `manual-verify` | `sankey_chart`, `heatmap_chart`, `treemap_chart` | Data-driven geometry exists, but the current calculator has no complete layout model. Inspect and report; do not silently skip. |

**Out of scope** (do not include in the receipt unless the page uses a data-driven sub-chart inside the layout):

- Pure text/number dashboards: `kpi_cards`.
- Tables: `comparison_table`, `basic_table`, `consulting_table`, `project_schedule_table`, `financial_statement_table`, `feature_matrix_table`, `harvey_balls_table`.
- Information graphics / frameworks / diagrams whose positions are layout-driven rather than value-driven: e.g. `hub_spoke`, `hub_inward_arrows`, `quadrant_text_bullets`, `quadrant_bubble_scatter` (BCG-style four-quadrant text grid — the visual bubbles are decoration, not value-mapped points), `matrix_2x2` (fixed quadrant cells with text cards), `mind_map`, `process_flow`, `numbered_steps`, `timeline`, `roadmap_vertical`, `layered_architecture`, `module_composition`, `pipeline_with_stages`, `client_server_flow`, `top_down_tree`, `journey_map`, `agenda_list`. If a deck genuinely uses these as data-driven scatter (rare — values mapped to actual `cx/cy`), promote to `partial-calc` and explain in the receipt.

Resulting list:

```
P03 03_market_share.svg  type=bar        mode=direct-calc
P07 07_growth.svg        type=line       mode=direct-calc
P11 11_share_split.svg   type=pie        mode=direct-calc
P15 15_pareto.svg        type=pareto     mode=decomposable-calc
```

If §VII is absent (legacy project / free-structure deck), skip this workflow and report: "design_spec.md has no §VII — chart pages cannot be enumerated authoritatively, verify-charts skipped". Do NOT fall back to guessing from SVG content; that reintroduces the silent-skip failure this workflow was built to eliminate.

If the filtered list is empty, output `verify-charts: spec declares no data-driven chart geometry, nothing to verify` and stop.

---

## Step 2: Per page — read SVG, run calculator, compare, update

For each page in the Step 1 list:

1. Read `<project_path>/svg_output/<page>.svg`.
2. Locate the plot-area definition:
   - Preferred: `<!-- chart-plot-area: ... -->` marker placed by Executor (see [executor-base.md §3.1](../references/executor-base.md)). Read coordinates directly.
   - If missing: derive the plot area from the SVG's axis lines (rectangular charts) or center/radius elements (radial charts). Then **add the marker back to the SVG** so future runs are not paying this cost again.
3. Read the data series from the SVG's `<text>` label/value elements.
4. **Read axis tick labels for every axis-based chart.** Locate the `<text>` elements along the value axis — X-axis labels for horizontal bars, Y-axis labels for vertical bars, and Y-axis labels for line-like charts. Extract the first and last tick values to determine the axis range (e.g. `0%` to `120%` → range `0,120`). Pass this range as `--value-range`, `--y-range`, or `--x-range` as appropriate. Radar uses `--max-value` instead of a range: read the outermost ring's tick value and pass it as `--max-value`. If the SVG has no explicit tick labels (data labels only, no grid), omit the range and let the calculator auto-normalize — but flag the receipt as `scale=auto (no ticks)`.

   **Local vs absolute coordinates.** Many chart templates wrap chart content in `<g transform="translate(cx, cy)">` or similar, so child `<circle>`/`<polygon>`/`<rect>` coords are relative to that origin (e.g. radar polygon at `0,-198`, donut paths starting from `0,0` inside a translated `<g>`, dumbbell circles at `cy="0"` inside a per-row translated `<g>`). The calculator outputs **absolute** SVG coordinates. Before comparing, either add the wrapping translate's offset to the SVG coords or subtract it from the calculator's output — pick one direction and apply it consistently.
5. Run the matching calculator command:

   ```bash
   # bar_chart / horizontal_bar_chart (add --horizontal for the latter)
   # IMPORTANT: always pass --value-range from axis tick labels (step 4)
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc bar \
     --data "Label1:Value1,Label2:Value2" --area "x_min,y_min,x_max,y_max" \
     --bar-width 120 --value-range "0,axis_max"

   # line_chart / area_chart / scatter_chart — area uses line output as the top boundary, then closes to y_max
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc line \
     --data "x1:y1,x2:y2,..." --area "x_min,y_min,x_max,y_max" --y-range "0,max"

   # pie_chart — default start angle is -90 (12 o'clock); pass --start-angle only if the SVG starts elsewhere
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc pie \
     --data "Slice1:Value1,Slice2:Value2" --center "cx,cy" --radius 200 --start-angle -90

   # donut_chart (pie with inner-radius)
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc pie \
     --data "Slice1:Value1,Slice2:Value2" --center "cx,cy" --radius 200 --inner-radius 120 --start-angle -90

   # radar_chart (separate subcommand) — pass --max-value from the outermost ring tick
   python3 skills/ppt-master/scripts/svg_position_calculator.py calc radar \
     --data "Dim1:Value1,Dim2:Value2,Dim3:Value3" --center "cx,cy" --radius 200 --max-value 100
   ```

   Area chart fill path closes to the bottom edge of the plot area:

   ```svg
   M first_x,first_y ... L last_x,last_y L last_x,y_max L first_x,y_max Z
   ```

6. **Scale-aware comparison.** Compare calculator output against the SVG's existing coordinates. Before declaring a mismatch, verify that every calculator invocation used the same axis range, plot area, center/radius, start angle, or size scale that the SVG visually declares. For `calc bar`, the output header must show `Value scale: axis ticks (...)` when the SVG has explicit ticks; if it shows `auto (max*1.1)`, go back to step 4 and re-run with the correct `--value-range`. **Do NOT update the SVG with mismatched-scale output.** Only update SVG attributes when the scale is confirmed to match and coordinates genuinely differ. Update by hand (do NOT use regex / bulk replacement — coordinates are positional and easy to swap incorrectly).

After updating any page, re-run the quality checker on the project to confirm nothing broke:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
```

---

## Stacked recipe

`stacked_bar_chart` and `stacked_area_chart` are not single-call but reduce cleanly to repeated calls on existing primitives. The operator already had to compute cumulative values to draw the SVG — verify-charts reuses them.

**Stacked bar** — for N stacked series on the same x categories, run `calc bar` N times. Pass each segment's **height** as the data value, and shift `--area`'s `y_max` down by the sum of all lower segments for that category. Compare each segment's `(x, y, width, height)` against the SVG.

```bash
# Example: two-series stack at category "Q1" with bottom=30, top=20, plot area y from 100 to 500
# Run 1 — bottom segment (origin = baseline)
python3 skills/ppt-master/scripts/svg_position_calculator.py calc bar \
  --data "Q1:30,Q2:..." --area "x_min,100,x_max,500" \
  --bar-width 80 --value-range "0,axis_max"
# Run 2 — top segment (origin shifted up by bottom segment's height in pixels)
python3 skills/ppt-master/scripts/svg_position_calculator.py calc bar \
  --data "Q1:20,Q2:..." --area "x_min,100,x_max,<500 - bottom_height_px>" \
  --bar-width 80 --value-range "0,axis_max"
```

**Stacked area** — for N stacked series, run `calc line` N times on **cumulative** y-values (series 1 raw; series 2 = series1+series2; …). Each call yields the top boundary of one band. Each band's SVG path closes to the **previous** band's top boundary (not to `y_max`).

If a stack page's segment positions don't reduce to this recipe (e.g., negative segments, percent-stacked with non-100 totals), mark it `manual-verify` in the receipt and inspect by hand — do not silently pass.

---

## Decomposable recipes

Use these recipes for `decomposable-calc` and `partial-calc` pages. Each recipe must produce a receipt line; if a page cannot be reduced cleanly, mark `manual-verify` with the reason instead of dropping it.

**Dumbbell chart** — for before/after or two-state values across categories. The two endpoints are **points**, not bar ends — `calc bar --horizontal` always anchors at `x_min`, which only matches the right endpoint. Use `calc line` × 2 instead, treating category index as the y axis:

1. Number categories `0.5, 1.5, …, N-0.5` so each row's y lands on its band center; set `--y-range "0,N"`. The same convention applies to vertical dumbbells with the axes swapped.
2. Set `--x-range` to the shared value-axis range read from ticks.
3. Run `calc line` once per endpoint series with identical `--area`, `--x-range`, `--y-range`. Each output `(SVG_X, SVG_Y)` is the matching endpoint circle's `(cx, cy)`.
4. Compare both endpoint circles and the connector line (`x1=cx_left, x2=cx_right, y1=y2=cy`) against the two calculated point sets.

```bash
# Horizontal dumbbell, 3 categories, value axis 0–100, plot area (100,100)–(700,460).
# Encode category index as the y value: row 1 → 0.5, row 2 → 1.5, row 3 → 2.5.
python3 skills/ppt-master/scripts/svg_position_calculator.py calc line \
  --data "42:0.5,55:1.5,37:2.5" --area "100,100,700,460" \
  --x-range "0,100" --y-range "0,3"
python3 skills/ppt-master/scripts/svg_position_calculator.py calc line \
  --data "68:0.5,71:1.5,49:2.5" --area "100,100,700,460" \
  --x-range "0,100" --y-range "0,3"
```

**Pareto chart** — split into descending bars plus cumulative line:

1. Run `calc bar` on the descending category values with the bar axis range from ticks.
2. Precompute cumulative percentages in category order.
3. Run `calc line` on `0.5:cum1,1.5:cum2,...,N-0.5:cumN` with `--x-range "0,N"`, the right-side percentage axis as `--y-range` (usually `0,100`), and the same `--area` as the bars. The `n - 0.5` offset puts each cumulative point on the matching bar's center; using `1,2,…,N` shifts the polyline left by half a bar width.
4. Compare bar rects, cumulative line path, and cumulative markers separately.

**Dual-axis line chart** — split by axis:

1. Read the left and right Y-axis tick ranges independently.
2. Run `calc line` once per series using its own `--y-range`; use the same `--x-range` and plot area for both.
3. Compare each series' polyline/path points against the matching axis scale. Never use the left-axis scale for the right-axis series or vice versa.

**Bullet chart** — performance bands + actual bar + target marker, all anchored at the same `x_min`. The bands occupy the **same** y row (they stack visually by overlapping, not by category), so run `calc bar --horizontal` once **per band** with a single data point — multi-category calls would spread y across rows:

1. Read the value-axis range from the band edges (the widest band's right edge = axis max).
2. For each band, run `calc bar --horizontal --data "<band_name>:<right_edge_value>" --area "<x_min>,<band_y>,<x_max>,<band_y+band_height>" --bar-width <band_height>`. Each call returns one rect at the shared `(x_min, band_y)` with the value-mapped width. Compare against the band rect.
3. Run `calc bar --horizontal` with a single data point for the actual value, using the actual bar's inset area (`y` and `bar-width` shrunk so the bands are visible). Compare against the actual rect.
4. The target marker is a `<line>` at `x = x_min + target/axis_max × area_width`, spanning the full band height. Compute by hand and compare.

**Butterfly chart** — mirrored horizontal bars around a vertical center line at `cx`:

1. Read the value-axis range and the center-line `cx` from the SVG.
2. Run `calc bar --horizontal` once per side using a plot area whose `x_min = cx` and `x_max = cx + side_width`. The right-side bars' `x` and `width` map directly.
3. For the left side, reuse the same calc output and mirror: each left bar's `x = cx - width`, `width` unchanged. Compare against the left rects.
4. Category `y` is shared across both sides — verify left and right rows align on the same `y + height/2`.

**Grouped bar chart** — N series sharing the same x categories, side-by-side instead of stacked:

1. Read the value-axis range and the plot area.
2. Compute the inner-group spacing: if there are `N` series and the visual group spans width `W` per category, each series-bar's width is `W/N` and its x offset within the group is `(i - 1) × W/N`. Read these from the SVG (the first category's bars give you both).
3. Run `calc bar` once per series with the **same** `--area` and `--value-range` but with each call's `--bar-width` set to the inner width. The calc's per-category center X gives the **group** center; each series-bar's actual `x = group_center - W/2 + (i-1) × W/N`. Compare against the SVG.

**Box plot chart** — Q1/Q3 box + median line + whiskers. All five quantities are y-values on the same axis:

1. Read the y-axis range and plot area. For each category, the five values are min / Q1 / median / Q3 / max.
2. Run `calc bar` once treating each category's box (Q3 − Q1) as a synthetic "stacked" segment with the area's `y_max` shifted to `y_axis_top - Q1 × pixels_per_unit` (the Q1 baseline). The output's `y, height` should match the box rect.
3. Median y = `y_axis_top + (axis_max - median) × pixels_per_unit`. Whisker endpoints (min, max) follow the same formula. Compare each against the SVG's `<line>` y1/y2 and `<rect>` y/height.

**Gantt chart** — task bars where each bar's `x` and `x + width` are the start and end positions on a timeline axis:

1. Read the timeline tick positions (the header row's x coordinates per date unit). Pixels-per-unit = `(x_unit_n - x_unit_1) / (n - 1)`.
2. Run `calc line` once over `start_index:row_y` per task — output `SVG_X` gives the bar's `x`. Run it again over `end_index:row_y` — output `SVG_X` gives `x + width`. Subtract for width.
3. Compare each task rect's `(x, width)` against the calculated start and end. Row y can be read directly (categories are not value-driven).

**Waterfall chart** — floating bars connected by running totals. Each bar's top and bottom edge correspond to two points on the same value axis (`cum_before`, `cum_after`):

1. Read the y-axis tick range and the plot area; compute running totals in category order (start with `cum[0] = base_value`, then `cum[i] = cum[i-1] + delta[i]` for increase, `cum[i-1] - delta[i]` for decrease, reset to delta for totals).
2. Build two virtual series: `top[i] = max(cum_before, cum_after)`, `bot[i] = min(cum_before, cum_after)`. Run `calc bar` twice on these with identical `--area`, `--bar-width`, `--value-range`. The `top` run's `Y` is the bar's `y`; `height = bot.Y - top.Y` for that index.
3. Compare each waterfall rect's `(x, y, width, height)` against the calculated pair. Connector lines should run from `(x + width, top_or_bot[i].Y)` to `(x_next, top_or_bot[i+1].Y)` at the matching shared cumulative value.
4. Total bars (full-height start/end) use `bot = 0` and the calc reduces to the standard `calc bar` recipe.

**Bubble chart / quadrant bubble scatter** — partial calculator support:

1. Use `calc line` to verify bubble centers (`cx/cy`) from the X/Y values and axis ticks.
2. Verify radius only if `design_spec.md`, `spec_lock.md`, or SVG comments declare a size scale such as `radius = sqrt(value) * k` or explicit min/max radius mapping.
3. If the size scale is missing, record `radius=manual (scale missing)` and inspect relative ordering by hand.

**Progress bar / gauge / funnel — formula-verify** (no calc call needed):

- Progress bar: `fill_width = value / max × track_width`. Read `value`, `max`, and `track_width` from the SVG; compute and compare against the fill rect's `width`.
- Gauge: `needle_angle = start_angle + value / max × sweep_angle`. Read `start_angle` and `sweep_angle` from the SVG's arc path (e.g. half-circle `start_angle=-180`, `sweep_angle=180`). Compare against the needle's `transform="rotate(α ...)"` value (the most common form), or against endpoint `(cx + L·cos α, cy + L·sin α)` when the needle is drawn as an explicit line/path.
- Funnel: each trapezoid's `top_width = prev.bottom_width`, `bottom_width = top_width × next_value / curr_value`. Verify by walking the segments: for segment `i`, `(top_left_x, top_right_x) → bottom_x_inset = (top_width - bottom_width) / 2`. The first segment's top width comes from the design's outer frame.
- Receipt should quote the formula and resulting value (e.g. `formula=value/max×track_width=0.92×700=644px`, or `formula=600×850/1000=510 bottom width`).

**Sankey / heatmap / treemap — manual verification:**

- Sankey: no layout model for node stacking, link routing, or flow-width normalization. Verify that link widths are proportional to flow values and that node-side totals match (in = out).
- Heatmap: cell positions are a fixed grid (not value-driven); the value-to-color binning is what's data-driven. Verify that the color of each cell falls in the bin matching the cell's number, and that high/low extremes use the legend's high/low colors.
- Treemap: rectangle areas reflect value proportions but the recursive squarify layout has no calculator equivalent. Verify each rect's `width × height ≈ total_area × value / sum(values)` for top-level cells, and that nested cells sum to their parent.

---

## Step 3: Per-page receipt

Output one line per page from the Step 1 list. Receipt count MUST equal Step 1 list length — that is the gate-closing artifact.

```
verify-charts: 03_market_share.svg | type=bar | mode=direct-calc | scale=0-100 (from ticks) | calc=ran | svg=updated
verify-charts: 07_growth.svg | type=line | mode=direct-calc | scale=0-120 (from ticks) | calc=ran | svg=unchanged (already accurate)
verify-charts: 11_share_split.svg | type=pie | mode=direct-calc | scale=N/A | calc=ran | svg=updated | marker=added (was missing)
verify-charts: 14_revenue_mix.svg | type=stacked-bar | mode=decomposable-calc | scale=0-200 (from ticks) | calc=ran×3 | svg=updated (per stacked recipe)
verify-charts: 15_unit_economics.svg | type=stacked-area | mode=manual-verify | scale=N/A | reason=percent-stacked, recipe does not apply
verify-charts: 16_before_after.svg | type=dumbbell | mode=decomposable-calc | scale=0-100 (from ticks) | calc=ran×2 | svg=unchanged
verify-charts: 17_drivers_pareto.svg | type=pareto | mode=decomposable-calc | scale=left 0-80 / right 0-100 | calc=ran×2 | svg=updated
verify-charts: 18_market_bubbles.svg | type=bubble | mode=partial-calc | xy=ran | radius=manual (scale missing) | svg=unchanged
verify-charts: 20_quota_attainment.svg | type=bullet | mode=decomposable-calc | scale=0-120 (from ticks) | calc=ran×3 (bands+actual+target) | svg=updated
verify-charts: 21_inflow_outflow.svg | type=butterfly | mode=decomposable-calc | scale=0-500 (from ticks) | calc=ran×2 + mirror | svg=unchanged
verify-charts: 22_profit_bridge.svg | type=waterfall | mode=decomposable-calc | scale=0-500 (from ticks) | calc=ran×2 (top/bot) | svg=updated
verify-charts: 23_quarterly_progress.svg | type=progress | mode=formula-verify | formula=68/100×800=544px | svg=unchanged
verify-charts: 24_capacity_gauge.svg | type=gauge | mode=formula-verify | formula=-180+72/100×180=-50.4° | svg=updated
verify-charts: 25_conversion_funnel.svg | type=funnel | mode=formula-verify | formula=600×850/1000=510 (seg2 bottom width) | svg=unchanged
verify-charts: 26_regional_compare.svg | type=grouped-bar | mode=decomposable-calc | scale=0-500 (from ticks) | calc=ran×3 | svg=updated
verify-charts: 27_release_plan.svg | type=gantt | mode=decomposable-calc | scale=Week1-Week24 (24 ticks, 40px/unit) | calc=ran×2 (start/end) | svg=unchanged
verify-charts: 28_score_distribution.svg | type=boxplot | mode=decomposable-calc | scale=0-100 (from ticks) | calc=ran×4 (Q1/Q3/whiskers) | svg=updated
verify-charts: 19_flow.svg | type=sankey | mode=manual-verify | link widths consistent with values | svg=unchanged
```

---

## After verification

Continue with post-processing & export ([SKILL.md Step 7](../SKILL.md)):

```bash
python3 skills/ppt-master/scripts/total_md_split.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```
