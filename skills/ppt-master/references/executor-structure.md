> See [`executor-base.md`](./executor-base.md) for shared authoring and [`executor-chart.md`](./executor-chart.md) / [`executor-table.md`](./executor-table.md) for other information models.

# Executor Shape Composition Grammar

Runtime grammar for Slide-local qualitative relationships built from editable shapes; it is not a diagram/template catalog.

**Load**: Quick reads this grammar once before all SVG authoring and reuses it for every per-page decision. Default loads it before realizing the first page whose Structure decision is yes, then reuses it in that execution context.

**Hard rule — no Structure catalog**: never recall or resolve `structure/<key>`. Compose from authoritative content, §IX relationships, the communication move, and the active visual system.

**Hard rule — not structured PPTX**: this branch owns Slide-local geometry. [`executor-structured.md`](./executor-structured.md) independently owns reusable Master/Layout/placeholders under `pptx_structure.mode: structured`; neither implies the other.

---

## 1. Relationship Atoms

| Atom | Meaning | Encode with |
|---|---|---|
| `order` | Sequence, progression, or rank | Position, numbering, direction, shared path |
| `link` | Dependency, exchange, influence, transition | Proximity/alignment when unmistakable; otherwise an edge |
| `parent` | One unit governs or decomposes into children | Branching, indentation, nesting, scale |
| `membership` | Units belong to a group, stage, lane, or region | Containment, shared field, band, repetition |
| `contrast` | Peers, states, options, or positions compare | Shared baseline, opposing regions, parallel framing |
| `overlap` | Units share a meaningful subset or duty | Intersecting regions plus a clear common area |

Combine atoms as needed; never force a named business model. Numbers used only as labels do not create a chart. Value-derived position/length/angle/area/radius/width/color routes to [`executor-chart.md`](./executor-chart.md); row-header × column-header facts route to [`executor-table.md`](./executor-table.md). Qualitative lanes use this grammar, but date/duration-driven task-bar `x`/`width` is Gantt Chart geometry.

---

## 2. Shape Roles and Operations

| Role | Job |
|---|---|
| `field` | Page/local region where a relationship operates |
| `node` | Semantic unit, state, actor, item, or group |
| `spine` | Explicit/implied scaffold establishing reading direction |
| `edge` | Necessary connection, branch, dependency, or transition |
| `label` | Text attached to a node, edge, region, or relationship |
| `garnish` | Non-semantic accent added after the relationship works |

| Operation | Job |
|---|---|
| `repeat` | Create peers from one role |
| `arrange` | Establish order, alignment, rhythm, rank, comparison |
| `transform` | Vary scale, rotation, crop, fill, or emphasis meaningfully |
| `connect` | Add an edge when layout/containment is insufficient |
| `region` | Partition, contain, intersect, band, or layer fields |
| `attach` | Bind labels, badges, annotations, or evidence to an owner |

Choose ordinary primitives → exact Office presets → Boolean results → necessary freeform under [`native-shape-authoring.md`](./native-shape-authoring.md). Shape choice follows semantic duty; decoration cannot invent a relationship.

---

## 3. Construction Order

Choose the field and map required atoms, then follow:

**Mandatory — spine → nodes → connectors → labels → garnish**:

| Layer | Completion evidence |
|---|---|
| `spine` | Entry, direction, and organizing path are clear |
| `nodes` | Every required unit has one home and intentional weight |
| `connectors` (`edge`) | Only unresolved links receive edges; route/source/target is clear |
| `labels` | Copy and caveats visibly attach to what they explain |
| `garnish` | Removing accents leaves all meaning intact |

**Hard rule — relationship before styling**: establish atoms, field, spine, nodes, and necessary edges before palette, type, effects, or containers. Prefer containment, alignment, baselines, and proximity; add lines/Connectors only for real edges, never to make a page look process-like.

---

## 4. Validation

| Check | Pass condition |
|---|---|
| Coverage | Every authoritative atom is visible; none was invented |
| Reading path | Entry, progression, hierarchy, and endpoint are unambiguous |
| Roles | Nodes/edges have one duty; garnish carries no meaning |
| Attachment | Labels/evidence belong to the correct node, edge, or region |
| Removal | Without color/effects/icons/garnish, placement still communicates |
| Fidelity | All required units, qualifiers, values, and caveats remain |

Load Chart/Table branches independently for embedded objects. Keep one dominant reading path while allowing secondary atoms whose ownership stays clear.
