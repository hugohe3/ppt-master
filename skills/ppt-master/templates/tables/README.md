# Table Visualization Templates

This directory contains six canonical cell-grid references. A table belongs
here only when a row header and column header jointly address each body fact;
headers, cells, rectangular merges, alignment, and boundaries preserve that
intersection model. Numeric values inside cells do not by themselves turn the
grid into a chart.

Value-driven mark geometry belongs in [`charts/`](../charts/). Qualitative page
topology is built as a page-specific Structure by Executor. Reusable PowerPoint
Master/Layout systems belong in [`layouts/`](../layouts/).

## Source of truth

[`tables_index.json`](./tables_index.json) is the sole table registry. Its
`tables` object maps each canonical key to one selection-rule `summary`; keys
match `<key>.svg`, and `meta.total` matches the canonical SVG roster.

Use [`visualization_recall.py`](../../scripts/visualization_recall.py) for
bounded Chart/Table or table-only recall. New Default planning writes
`table/<key>` to `page_visualizations`; Quick keeps the selected reference in
active context.

## Authoring contract

[`VISUALIZATION_TEMPLATE_AUTHORING.md`](../VISUALIZATION_TEMPLATE_AUTHORING.md)
owns the shared standalone-SVG, neutral-preview, root-boundary, Shape-first,
family, and catalog rules. Table-specific requirements are:

- Preserve the complete row/column topology, headers, values, units, ordering,
  merges, alignment, totals, status, and source notes.
- Default output remains independently editable DrawingML shapes.
- Add native Table replacement metadata only for a supported pure text grid
  selected as an independent native-ready object. The fallback and metadata
  contain the same cells.
- Keep graphical cells such as rating dots, icons, status marks, avatars, or
  embedded bars on the Shape fallback route unless the active native-data
  contract explicitly supports them.

| Canonical key | Grid contract |
|---|---|
| `record_table` | One flat record per row and one stable heterogeneous field per column |
| `metric_table` | Operating metrics by entity with current values, changes, statuses, or target progress inside cells |
| `comparison_matrix` | Criteria × alternatives with exact, prose, or heterogeneous facts at intersections |
| `feature_matrix` | Capabilities × offerings with supported, unsupported, partial, or exception states |
| `rating_matrix` | Criteria × alternatives using one repeated ordinal scale |
| `hierarchical_table` | Grouped or indented rows with detail and subtotal/total hierarchy |

**Hard rule — physical table is not semantic Table**: A PowerPoint table used
as a drawing grid does not enter this family automatically. Exact dates or
durations that drive horizontal task positions and lengths belong to
`chart/gantt_chart`; qualitative stage/lane placement belongs to
a page-specific Structure.

Selecting a table reference does not itself select native output. Design Spec
§IX/Quick names independent objects separately and decides
`<object-key>=yes|no`; explicit `--native-charts-and-tables` export is a second
opt-in.
