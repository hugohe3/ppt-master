# Table Visualization Templates

This directory contains the cell-grid table family. A table belongs here when
rows, columns, cells, headers, merges, alignment, borders, and cell content form
the primary information model. Numeric values inside cells do not by themselves
turn the grid into a chart.

Value-driven mark geometry belongs in [`charts/`](../charts/). Qualitative
page topology belongs in [`structures/`](../structures/). Reusable PowerPoint
Master/Layout systems belong in [`layouts/`](../layouts/).

## Source of truth

[`tables_index.json`](./tables_index.json) is the sole table registry. Its
`tables` object maps each canonical key to one selection-rule `summary`; keys
match `<key>.svg`, and `meta.total` matches the canonical SVG roster.

Use [`visualization_recall.py`](../../scripts/visualization_recall.py) for
bounded all-family or table-only recall. New Default planning writes
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
- Keep graphical cells such as Harvey balls, icons, ratings, avatars, or
  embedded bars on the Shape fallback route unless the active native-data
  contract explicitly supports them.

Selecting a table reference does not itself select native output. Design Spec
§IX/Quick names independent objects separately and decides
`<object-key>=yes|no`; explicit `--native-charts-and-tables` export is a second
opt-in.
