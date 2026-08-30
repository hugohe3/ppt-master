> See [`executor-base.md`](./executor-base.md) for shared authoring and [`executor-chart.md`](./executor-chart.md) / [`executor-table.md`](./executor-table.md) for other information models.

# Executor Shape Composition Grammar

Runtime grammar for Slide-local qualitative relationships built from editable shapes; not a diagram catalog. Default and Quick read it once at the first page whose Structure decision is `yes` and reuse it for every later page; loading it selects no `Structure=yes` and creates no geometry quota.

**Hard rule — no Structure catalog**: never recall or resolve `structure/<key>`; compose from authoritative content, §IX relationships, the communication move, and the active visual system.

**Hard rule — not structured PPTX**: this branch owns Slide-local geometry. [`executor-structured.md`](./executor-structured.md) independently owns reusable Master/Layout/placeholders under `pptx_structure.mode: structured`.

Numbers used only as labels do not create a chart; value-derived position, length, angle, area, radius, width, or color routes to [`executor-chart.md`](./executor-chart.md), row-header × column-header facts to [`executor-table.md`](./executor-table.md). Qualitative lanes use this grammar; date/duration-driven task-bar `x` / `width` is Gantt geometry.

---

## 1. Relationship Atoms

**Mandatory — relationship → topology before contour**: for each active atom resolve only the path, junctions, enclosure, field partition, shared region, scale change, and entry/endpoint that carry meaning, adapted to the actual units, text load, page role, and visual system, before selecting contours.

| Atom | Meaning | Encode with | Generate topology from |
|---|---|---|---|
| `order` | Sequence, progression, rank | Position, numbering, direction, shared path | One reading path: open / closed; straight / bent / stepped / switchback / coiled; level / rising / falling; constant / expanding / contracting; turns, milestones, endpoint |
| `link` | Dependency, exchange, influence, transition | Proximity / alignment when unmistakable; otherwise an edge | Sources, targets, junctions: direct, hub, chain, split, merge, exchange, feedback; the fewest necessary edges |
| `parent` | One unit governs or decomposes into children | Branching, indentation, nesting, scale | Root, depth, sibling groups: branch, indent, nest, radiate, scale; child roles set fan-out and weight |
| `membership` | Units belong to a group, stage, lane, region | Containment, shared field, band, repetition | Owning fields: enclose, band, lane, cluster, repeat, nest; content sets field shape and occupancy |
| `contrast` | Peers, states, options, positions compare | Shared baseline, opposing regions, parallel framing | Shared invariants plus separation: semantic axes / baselines, opposing or parallel fields, counterweight, divergence, before / after boundary |
| `overlap` | Units share a subset or duty | Intersecting regions plus a clear common area | Exact exclusive / shared regions: paired, chained, layered intersections; every owner and common area legible |

The last column names common transform axes, not an exhaustive set: combine, deform, or invent page-fit topologies; never recall a named diagram or reproduce a listed form by default.

**Mandatory — combined-atom spatial relation before contour**: when several atoms share one construct, resolve whether their topologies share a field, nest, run in parallel, cross orthogonally, or intersect. Orthogonal overlay applies when independent dimensions occupy one field (an `order` path across `membership` lanes, two independent `contrast` dimensions); preserve each atom's ownership and reading direction. Never force a named business model; the overlay never implies equal partitions.

**Hard rule — no topology from balance alone**: node count and text fit may change spacing, route, or wrap. They never justify equal shapes, gaps, or partitions, mirroring, radial symmetry, or closure that invents peer weight, centrality, reciprocity, or recurrence.

---

## 2. Shape Roles and Operations

| Role | Job |
|---|---|
| `field` | Page/local region where a relationship operates |
| `node` | Semantic unit, state, actor, item, or group; may punctuate a drawn carrier as a stop, turn, junction, or bridge |
| `spine` | Explicit/implied scaffold or continuous carrier establishing reading direction |
| `edge` | Necessary semantic connection, branch, dependency, or transition |
| `label` | Text/evidence attached directly or by a non-relational leader/tether to its owner |
| `garnish` | Non-semantic accent added after the relationship works |

| Operation | Job |
|---|---|
| `repeat` | Peers from one visual family; clone the full contour only when structural states match |
| `arrange` | Order, alignment, rhythm, rank, comparison |
| `transform` | Vary scale, rotation, crop, fill, emphasis, or entry/continuation/turn/terminal port state meaningfully |
| `connect` | Add an edge when layout/containment is insufficient |
| `region` | Partition, contain, intersect, band, or layer fields |
| `attach` | Bind labels, badges, annotations, or evidence to an owner |

**Hard rule — realization enters the construction gate**: decide whether each role is implicit/direct content or drawn geometry. Every drawn field, spine, node carrier, or edge follows [`native-shape-authoring.md`](./native-shape-authoring.md) §§1–2.1: contour before encoding → simplest exact native form → independent compound → required Boolean → necessary freeform. Text styling cannot replace required geometry; implicit/direct roles need no container; decoration cannot invent a relationship.

---

## 3. Construction Order

**Mandatory — spine/topology → nodes → connectors → labels → garnish**, after choosing the field and mapping required atoms:

| Layer | Completion evidence |
|---|---|
| `spine` | Entry, direction, and organizing path are clear; reversal, cycle, split/merge, or stage change reshapes a continuous carrier before node placement |
| `nodes` | Every unit has one home and intentional weight as direct content or a §2-approved carrier; carrier-crossing nodes intentionally continue, stop, turn, join, or bridge its path |
| `connectors` | Only unresolved semantic links become edges; route/source/target is clear |
| `labels` | Copy and caveats visibly attach to what they explain; with several text roles on a node, cue → claim/value → support → note stays perceptibly descending and absent roles stay absent |
| `garnish` | Removing accents leaves all meaning intact |

**Hard rule — relationship before styling**: establish atoms, field, spine, nodes, and necessary edges before palette, type, effects, or containers. Containment, alignment, baselines, and proximity express relationships without edges; lines/Connectors express real edges.

**Structural carriers**: a relationship-bearing field, spine, node carrier, or directional shape can be the page-scale move; Structure `yes` by itself adds no geometry. When drawn roles interact, resolve parent contour/direction → contact → joint or intentional void → z-order/occlusion → canvas-edge behavior before labels/garnish; skip inapplicable operations.

---

## 4. Validation

| Check | Pass condition |
|---|---|
| Coverage | Every authoritative atom is visible; none invented |
| Reading path | Entry, progression, hierarchy, and endpoint unambiguous |
| Roles | Nodes/edges have one duty; garnish carries no meaning |
| Attachment | Labels/evidence belong to the correct node, edge, or region |
| Removal | Without color/effects/icons/garnish, placement still communicates |
| Fidelity | All required units, qualifiers, values, and caveats remain |
| Construction | Drawn roles pass §2; implicit/direct roles need no carrier; freeform follows failed exact-native/compound/Boolean routes |
| Composition | Every contact, void, overlap, cutout, occlusion, or canvas-edge crossing maps to an atom/role or stays removable garnish |

Load Chart/Table branches independently for embedded objects. Keep one dominant reading path while secondary atoms keep clear ownership.
