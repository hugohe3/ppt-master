> See [`executor-base.md`](./executor-base.md) for page authoring and [`executor-visualization.md`](./executor-visualization.md) when a table-family SVG is selected.

# Executor Table Branch

Conditional Executor authority for semantic cell grids whose row/column intersections carry the information.

**Trigger**: the page contains an actual cell-grid table or its primary reference uses `table/<key>`.

---

## 1. Cell-grid Boundary

| Information model | Route |
|---|---|
| A row header and column header jointly address each body fact; summaries and optional rectangular spans preserve the same grid | This branch |
| Independent visual zones compare categories without a shared row/column grid | [`executor-structure.md`](./executor-structure.md) |
| Values determine marks, positions, lengths, areas, angles, radii, or color bins | [`executor-chart.md`](./executor-chart.md) |

**Hard rule — physical grid is insufficient**: a PowerPoint table object or rectangular drawing grid does not establish Table semantics. Dates or durations driving task-bar position and length route to `executor-chart.md`; qualitative stage/lane placement routes to `executor-structure.md`. Graphical indicators may sit inside cells while the grid still carries their meaning; a row of metric cards or two prose columns is a qualitative structure, not a table.

With a `table/<key>` primary reference, [`executor-visualization.md`](./executor-visualization.md) owns resolution and adaptation; a custom grid follows this branch without a catalog SVG. Catalog keys (`record_table` record × field, `metric_table` entity × KPI, `comparison_matrix` criterion × alternative, `feature_matrix` capability states, `rating_matrix` one repeated ordinal scale, `hierarchical_table` grouped rows with detail and totals) separate recurring cell grammars without changing this boundary.

---

## 2. Grid Construction

**Hard rule — grid before decoration**: establish the complete logical grid before fills, borders, badges, or other cell treatment: (1) resolve column/row counts, header rows, row labels, summaries, and rectangular spans from the content; (2) allocate widths and heights from semantic weight and real text/data fit — no default equal columns when labels or values differ materially; (3) place every value, unit, qualifier, status, and source note in its intersection; (4) align by content role with comparable numeric alignment and stable header/body hierarchy; (5) add rules, fills, banding, highlights, and in-cell indicators only after the grid reads correctly plain; (6) for a `<object-key>=yes` table, project the finished grid into the JSON in the same edit — `row_heights`, header fill/text/bold/alignment, whole-row or whole-column fills, first-column emphasis, padding, and per-side `borders` mirroring the drawn rules; a font size plus a uniform border is not a projection, and a graphical cell (inset badge, colored chip, mini bar) cannot be expressed by `a:tbl`, so return that object to `Native-ready=no`.

**Per-cell completeness**: never drop a row, column, summary, footnote, unit, or qualifier to imitate a lighter catalog preview; reflow text, widen the column, rebalance neighbors, or increase row height within the page's information contract and [`executor-base.md`](./executor-base.md) typography bounds.

**Spans and chrome**: merge only rectangular regions whose repeated boundaries would obscure an intended shared heading or group, with no competing visible content in covered areas; native merge fields belong exclusively to [`native-data-interface.md`](./native-data-interface.md). Distinguish header/body/summary with the lightest sufficient weight, fill, rule, and whitespace; decorative card treatment must not break row or column continuity. **Reference — table defaults (treatment follows the locked style)**: a header set apart by weight and a rule, or by a fill with reversed text where the style carries fills; zebra rows at `fill-opacity` 0.05, numbers right-aligned and text left-aligned with consistent units and precision, one highlighted row in the accent at `fill-opacity` 0.1, and horizontal rules only — avoid a full grid of lines.

---

## 3. Object Boundary

Each semantic table is one independently bounded page object even with nested cell groups; captions, source notes, and callouts may sit outside the grid when ownership is visually explicit. Native readiness is decided per table object, not by family or numeric cells: reuse its §IX/Quick semantic object key in the `Native-ready` map; only `<object-key>=yes` loads [`native-data-interface.md`](./native-data-interface.md), everything else remains Shape-first SVG geometry.
