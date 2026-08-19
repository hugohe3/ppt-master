# Table Expression Vocabulary

This is the complete planning-side map of the six canonical Table references.
Choose from the page's actual row-column information model, then retain the
exact `table/<key>` identifier. This file contains no SVG construction,
cell-sizing, styling, native-replacement, or export instructions; those
decisions belong to Executor after selection.

**Reference — not a constraint**: each description states what the cell grid
represents. It is not a ranking, recommendation, threshold, quota, or
substitute for judgment from the current facts and communication goal. Zero
Table selections remains valid.

| Canonical reference | Encoded relationship |
|---|---|
| `table/record_table` | Each row represents one flat record, and each column represents one stable heterogeneous field. |
| `table/metric_table` | Entities form rows while metric columns hold current values, changes, statuses, or target progress inside cells. |
| `table/comparison_matrix` | Criteria and alternatives form the two grid axes, with exact values, prose, or mixed facts at their intersections. |
| `table/feature_matrix` | Capabilities and offerings form the two grid axes, with supported, unsupported, partial, or exception states in cells. |
| `table/rating_matrix` | Criteria and alternatives form the two grid axes, with one repeated ordinal scale encoded across their intersections. |
| `table/hierarchical_table` | Grouped or indented rows preserve a detail hierarchy across stable measure columns, including subtotals and totals. |
