# Chart Visualization Templates

This directory contains 33 canonical value-driven references. A chart belongs here
when source values, categories, time, weights, or durations determine visual
mark position, length, area, angle, font size, or connection width.

Qualitative page topology is built as a page-specific Structure by Executor.
Cell-grid semantics belong in [`tables/`](../tables/). Reusable PowerPoint
Master/Layout, page-type, slot, and placeholder contracts belong in
[`layouts/`](../layouts/).

## Source of truth

[`charts_index.json`](./charts_index.json) is the sole chart registry. Its
`charts` object maps each canonical key to one selection-rule `summary` in the
form `Pick for ... Skip if ...`. The key matches `<key>.svg`; `meta.total`
matches the canonical SVG roster.

Use [`visualization_recall.py`](../../scripts/visualization_recall.py) for
bounded Chart/Table or chart-only recall. New Default planning writes
`chart/<key>` to `page_visualizations`; Quick keeps the selected reference in
active context. [`chart_recall.py`](../../scripts/chart_recall.py) and bare keys
remain legacy compatibility only.

## Authoring contract

[`VISUALIZATION_TEMPLATE_AUTHORING.md`](../VISUALIZATION_TEMPLATE_AUTHORING.md)
owns the shared standalone-SVG, neutral-preview, root-boundary, Shape-first,
family, and catalog rules. Chart-specific requirements are:

- Preserve the exact value-to-mark mapping, labels, units, categories, series,
  ordering, and source notes required by the information.
- Keep calculator-supported `chart-plot-area` markers accurate.
- Default output remains independently editable DrawingML shapes.
- Add native Chart replacement metadata only for a supported independent data
  object. The visible fallback and metadata describe the same data.
- Do not classify a named quadrant, process, hierarchy, or relationship diagram
  as a chart unless values actually determine its marks.

`matrix_2x2` is a chart: each item's x/y coordinates encode two values and its
radius encodes a third metric. A fixed 2×2 set of titled text regions is a
page-specific Structure. A schedule whose dates or durations determine task-bar
position and length is `chart/gantt_chart`; a qualitative stage/lane plan is a
Structure built from those relationships.

## Runtime boundary

One selected SVG is a flexible reference for one mapped page. Design Spec §IX
or the Quick active-context decision plus source data owns final semantics.
Project palette, typography, chrome, grouping, capacity, and geometry remain
adaptable. Selecting a chart reference does not itself select native output;
§IX/Quick names independent objects separately and decides
`<object-key>=yes|no`, while explicit `--native-charts-and-tables` export is a
second opt-in.
