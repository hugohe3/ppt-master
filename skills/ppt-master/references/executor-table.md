> See [`executor-base.md`](./executor-base.md) for page authoring and [`executor-visualization.md`](./executor-visualization.md) when a table-family SVG is selected.

# Executor Table Branch

Conditional Executor authority for semantic cell grids whose row/column intersections carry the information.

**Trigger**: load when the page contains an actual cell-grid table or its primary reference uses `table/<key>`.

---

## 1. Cell-grid Boundary

| Information model | Route |
|---|---|
| A row header and column header jointly address each body fact; summaries and optional rectangular spans preserve the same grid | This branch |
| Independent visual zones compare categories without a shared row/column grid | [`executor-structure.md`](./executor-structure.md) |
| Values determine marks, positions, lengths, areas, angles, radii, or color bins | [`executor-chart.md`](./executor-chart.md) |

Graphical indicators may appear inside cells without changing the table family, provided the row/column grid still carries their meaning. A row of metric cards or two prose columns is a qualitative structure, not a table.

**Hard rule — physical grid is insufficient**: A PowerPoint table object or a
rectangular drawing grid does not establish Table semantics. Exact dates or
durations that drive task-bar position and length route to
[`executor-chart.md`](./executor-chart.md); qualitative stage/lane placement
routes to [`executor-structure.md`](./executor-structure.md).

When a `table/<key>` primary reference exists, [`executor-visualization.md`](./executor-visualization.md) owns resolution and flexible adaptation. A custom cell grid follows this branch without loading a catalog SVG.

**Reference — not a constraint**: `record_table` covers heterogeneous record ×
field grids; `metric_table` covers entity × KPI scanning;
`comparison_matrix` covers heterogeneous criterion × alternative facts;
`feature_matrix` covers capability states; `rating_matrix` covers one repeated
ordinal scale; and `hierarchical_table` covers grouped/indented rows with detail
and totals. These keys separate recurring cell grammars without changing the
shared row/column information-model boundary.

---

## 2. Grid Construction

**Hard rule — grid before decoration**: establish the complete logical grid before drawing fills, borders, badges, or other cell treatment.

1. Resolve column count, row count, header rows, row labels, summaries, and any rectangular visual spans from the authoritative content.
2. Allocate column widths and row heights from semantic weight and real text/data fit; do not default to equal columns when labels or values differ materially.
3. Place every cell value, unit, qualifier, status, and source-bearing note in its correct intersection.
4. Apply alignment consistently by content role, including comparable numeric alignment and stable header/body hierarchy.
5. Add rules, fills, banding, highlights, and in-cell indicators only after the grid reads correctly in plain form.

**Per-cell completeness**: never drop a row, column, summary, footnote, unit, or qualifier to imitate a lighter catalog preview. Reflow text, widen the affected column, rebalance adjacent columns, or increase row height while preserving the active page's information contract and [`executor-base.md`](./executor-base.md) typography bounds.

**Visual span discipline**: merge only rectangular regions whose repeated boundaries would obscure an intended shared heading or group. Covered areas must not carry competing visible content. This branch owns the visible SVG geometry only; any native merge fields or payload topology belong exclusively to [`native-data-interface.md`](./native-data-interface.md).

**Table chrome**: make header/body/summary roles distinguishable with the lightest sufficient combination of weight, fill, rule, and whitespace. Keep comparison scanning stable across the grid; decorative card treatment must not break row or column continuity.

---

## 3. Object Boundary

Treat each semantic table as one independently bounded page object even when it contains nested cell groups. Captions, source notes, and explanatory callouts may sit outside the grid when their ownership is visually explicit.

Native readiness is decided per independent table object, not by the `table`
family or numeric cells. Reuse its §IX/Quick semantic object key in the
`Native-ready` map; only `<object-key>=yes` loads and follows
[`native-data-interface.md`](./native-data-interface.md). All others remain
ordinary Shape-first SVG geometry under [`executor-base.md`](./executor-base.md).
