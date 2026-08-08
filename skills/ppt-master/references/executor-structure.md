> See [`executor-base.md`](./executor-base.md) for page authoring and [`executor-visualization.md`](./executor-visualization.md) when a structure-family SVG is selected.

# Executor Structure Branch

Conditional Executor authority for page-local qualitative topology: relationships expressed through spatial order, grouping, containment, direction, hierarchy, or named zones rather than value-mapped geometry.

**Trigger**: load when the page's actual information model is qualitative topology or its primary reference uses `structure/<key>`.

**Hard rule — not structured PPTX**: this branch constructs Slide-local information geometry. [`executor-structured.md`](./executor-structured.md) separately owns PowerPoint Master/Layout/placeholder reuse under `pptx_structure.mode: structured`. Either, both, or neither branch may be active on a page; their names do not imply each other.

---

## 1. Information-model Boundary

| Content relationship | Route |
|---|---|
| Sequence, flow, hierarchy, hub/spoke, layers, comparison zones, grouping, containment, roster, roadmap, or qualitative matrix | This branch |
| Position, length, angle, area, radius, flow width, or color bin derives from values | [`executor-chart.md`](./executor-chart.md) |
| Row/column intersections form a semantic cell grid | [`executor-table.md`](./executor-table.md) |

A structure may contain numbers as labels without becoming a chart. A named quadrant may use axes as qualitative boundaries without becoming value-driven. Conversely, actual `x`, `y`, or radius mapping remains chart geometry even when the result resembles a framework.

When a `structure/<key>` primary reference exists, [`executor-visualization.md`](./executor-visualization.md) owns resolution and flexible adaptation. No reference is required for a page-specific topology.

---

## 2. Topology Construction Order

**Mandatory — spine → nodes → connectors → labels → garnish**: complete each layer in this order so the semantic topology remains legible without decorative support.

| Layer | Construction job | Completion evidence |
|---|---|---|
| `spine` | Establish the dominant reading path or organizing frame: baseline, axis pair, hierarchy trunk, ring, hub, container, layer stack, or another explicit/implicit scaffold | The intended entry point and reading direction are unambiguous before content boxes are styled |
| `nodes` | Place every semantic unit with hierarchy and information weight reflected in size, position, repetition, or containment | Every required item has one identifiable home and peers remain visually comparable |
| `connectors` | Add only relationships the topology cannot express by adjacency, alignment, order, or containment alone | Direction, dependency, exchange, branching, or convergence is explicit without decorative arrows |
| `labels` | Attach titles, node copy, edge labels, stage names, legends, and qualifiers to the geometry they explain | No label floats ambiguously between nodes; all authoritative relationships and caveats remain readable |
| `garnish` | Add non-semantic accents, depth, icons, or motifs after the structure already communicates | Removing garnish leaves the complete topology and reading order intact |

**Hard rule — topology before styling**: do not start from a row of decorated cards and infer relationships afterward. First encode the actual information relationship; then apply project-owned palette, typography, effects, and container treatment.

**Connector economy**: use containment, alignment, shared baselines, or proximity when they already communicate the relationship. When a connector is necessary, give it a clear source/target or shared route and follow [`executor-base.md`](./executor-base.md) §3.0 for line, preset Connector, Boolean, or necessary freeform construction. Never add arrows solely to make a page look process-like.

**Label fidelity**: keep every required node, stage, branch, qualifier, status, and relationship from the active page contract. Reflow geometry around the copy; do not delete nodes, merge distinct relationships, or shorten away a caveat to preserve a preview's spacing.

---

## 3. Page-level Integration

Use one dominant topology per primary structure. Secondary annotations, KPIs, or a small data object may attach to it when their semantic ownership is clear; load the corresponding family branch for any actual chart or cell grid rather than forcing that object into the structure grammar.

Keep garnish subordinate to the page's communication move. Icons, fills, bands, shadows, and decorative paths may reinforce grouping or direction, but they never create a relationship that is absent from the spine, nodes, connectors, or labels.
