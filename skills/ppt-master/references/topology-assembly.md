> See [`executor-structure.md`](./executor-structure.md) §1 for relationship → topology and [`native-shape-authoring.md`](./native-shape-authoring.md) §§1–2.1 for contour selection and materialization.

# Topology Assembly Reference

Generative material for turning one resolved qualitative topology into editable native-shape components with coherent relative registration, before coordinates. Default and Quick read it once with `executor-structure.md` at the first `Structure=yes` page and reuse it for every later assembly.

**Hard rule — relative constraints, never copyable geometry**: state exact preset or primitive identities, semantic counts, inter-component relations, and only the relative geometry that makes the assembly hold; never coordinates, points, sizes, ratios, adjustment values, path data, SVG fragments, full-page frames, copy, color, styling, or page composition. Materialize every adopted call through `native-shape-authoring.md`.

**Mandatory — two-step assembly test**: preserve the topology resolved by `executor-structure.md`, then (1) split every piece that needs independent editing, movement, paint, animation, or reuse; (2) from outline and region semantics choose one continuous shape, one shape with dividers, stacked siblings, seamed pieces, overlapping siblings, or independently retained Boolean regions.

**Mandatory — registration closure**: after the test, resolve only the relative conditions that make the pieces read as one construct — shared datum, center, taper, or contour; aligned endpoints and seams; fitted contact or intentional clearance; nesting margin; overlap depth; joint type; direction continuity; cutters that fully cross the parent silhouette. Valid individual shapes are not an assembly until their contacts and boundaries register.

**Hard rule — no assembly lookup, counts from semantics, information-model boundary**: never recall a paragraph below as a named structure or match the page to the nearest mechanism — generate from the active atoms and the two-step test, adapting or inventing calls even when no paragraph resembles the result. Derive every call count from real units, runs, turns, boundaries, junctions, owners, or regions; a count never implies equal size, spacing, angle, weight, or symmetry, and closure, mirroring, centrality, taper, interlock, and contact require meaning already resolved upstream. Value-derived position, length, width, area, angle, radius, or color stays Chart; row × column facts stay Table.

**Reference — not a constraint**: the mechanisms below are common generative material, not an exhaustive set, ranking, or allowed-combination list; a primitive, another preset, necessary freeform, or no drawn carrier may still win.

---

## 1. `order`

- **Stages on one directional path**: `chevron` once per stage, kept as siblings. On a continuous handoff register each tip into the next notch with coherent entry/exit through the joint, entering only far enough to close the carrier without occluding the next stage's interior; keep an intentional gap where the boundary is a pause, reset, or discontinuity. Bodies may vary with their duties while every joint fits.
- **A path that wraps and reverses**: `rightArrow` per forward run, `leftArrow` per return run, `downArrow` per turn, `roundRect` per independently owned stop, runs on distinct parallel baselines. Align each turn's entry to the preceding run's endpoint and its exit to the next run's entry so the path neither doubles back ambiguously nor jumps a gap; attach each stop to its run without covering an entry, exit, or turn. Contact at a turn means continuation, clearance a stage break; run lengths follow the resolved path, not a regular wrap.
- **Recurrence with independent stages**: `blockArc` once per stage, seamed into one closed path — every segment shares one center and registered inner/outer contours, adjacent end faces meet on both contours, spans may differ while sequence and seam direction stay legible, and a gap marks only a semantic reset. One indivisible recurrence is one `circularArrow` instead.

## 2. `link`

- **Split or merge**: `roundRect` per source or target, `line` per necessary edge, `ellipse` zero or once per junction — omitted when edges merely meet, retained when the junction is independently editable, reusable, or animatable. Terminate edges on node boundaries, bring converging edges to the same junction, keep a collinear shared trunk where one exists, and separate branches early enough that they never read as one line; an apparent crossing is either visibly non-joining or a real junction.
- **Two-way exchange**: one `leftRightArrow` between two `roundRect` nodes when the exchange is one relationship, both ends registered to the facing boundaries with one uninterrupted corridor; one `rightArrow` plus one `leftArrow` as parallel siblings when the directions need independent editing, paint, animation, or reuse, each end on its own port and neither head covering the other carrier or a node.

## 3. `parent`

- **Enclosure hierarchy / nested bubbles**: `ellipse` once per unit with a visible boundary, each child nested inside its immediate parent as an independent sibling (never unioned), with a visible containment margin, its complete boundary inside the parent, and sibling interiors apart unless another atom requires contact. Deeper levels may move, contract, or cluster asymmetrically while containment stays unambiguous.
- **Indented decomposition without edges**: `roundRect` per node, `leftBrace` per parent whose children need a shared boundary; siblings registered to one depth datum, the child group deeper than its parent, the brace spanning only that parent's children with its open side toward their entry edge, nested braces distinct and never crossing a node. Depth and group extent carry the hierarchy, not equal offsets.

## 4. `membership`

- **Owned lanes**: `rect` per lane, `roundRect` per member needing a carrier; lanes as parallel siblings whose long boundaries share one seam when membership is continuous or keep a clear gap when the groups are separate fields; each member's complete contour inside its lane with a nesting margin, crossing a boundary only for true multiple ownership or a transfer. One indivisible field with meaningful boundaries is one `rect` plus `line` per boundary instead. Lane width and occupancy follow responsibility, not uniform partition.
- **Light grouping boundary**: `leftBrace` per group, `roundRect` per member; the brace separate, open side toward the members, spanning the whole group and no neighbor, with clearance so no brace touches a member contour. Member count implies no repeated contours, equal spacing, or equal weight.

## 5. `contrast`

- **Opposing fields on one baseline**: `rect` per side when the sides need independent editing, paint, animation, or reuse, comparable anchors on a shared baseline, facing boundaries as parallel edges separated by a semantic gap or one `line` divider, no incidental offset that reads as rank; one `rect` plus one `line` at the state boundary when the field is one duty. Shared framing and counterweight never require equal dimensions or mirrored content.
- **Tapered rank or support stack**: `trapezoid` per independently owned tier, stacked with semantic seams — all side edges on one shared taper, each seam meeting across the full current width, tier width monotonic in the rank direction without assumed equal change, height, or area. One `triangle` plus one `line` per tier boundary when the stack is one duty (every divider crossing the interior and ending on both outer edges); one `triangle` plus one `rect` strip per region, every strip fully crossing the silhouette and meeting the next without a sliver, then `fragment`, when one outer silhouette and independently retained regions are both required. Never substitute a triangle plus dividers for tiers that need independent paint or animation.

## 6. `overlap`

- **Independently editable owners, shared area untreated**: `ellipse` per owner, overlapped as siblings without Boolean — enough of every boundary visible to identify each owner, each common area substantial enough to read as a region, no full containment unless subset meaning is active, overlap order and depth chosen so no owner erases another or creates unintended micro-regions. Paired, chained, or layered ownership never implies equal ellipses or symmetric intersection.
- **Exclusive and shared regions need independent treatment**: `ellipse` per owner, register the overlaps so their crossings produce only the semantic regions (no accidental tangencies, hidden owners, or slivers), then `fragment` and retain every required exclusive/shared result as its own shape — `fragment`, not `intersect`, which keeps only the common region. Retain no region merely to complete a pattern.

## 7. Combined atoms

**Mandatory — compose active topologies, not reference paragraphs**: generate each active atom's topology from its own duties, then resolve how those topologies share a field, nest, run in parallel, cross orthogonally, or intersect, preserving each atom's ownership and reading direction. One component may carry several atoms only when its edit, movement, paint, animation, reuse, outline, and region duties never need to separate; otherwise keep the systems as registered siblings, re-running the two-step test at every contact, crossing, shared boundary, and retained region. A shared field makes no atom dominant, and convenience never justifies merging.

- **`order` path across `membership` lanes**: `rect` per independently owned lane (or one `rect` plus lane dividers when lanes are one field duty), `roundRect` per process unit, `line` per transition and per phase boundary. Lanes parallel, the process axis orthogonal across them; each unit fully inside its owner's lane, only a real responsibility transfer crossing a seam; transitions ending on unit boundaries rather than using a lane boundary as an edge; phase boundaries crossing the whole field and distinguishable from transitions. Equal bands, phases, or steps are never implied.
- **Two independent `contrast` dimensions partitioning one field**: one `rect` plus one `line` per axis when only the axes carry meaning — both crossing the full field, orthogonal, their intersection at the semantic thresholds rather than the center; four `rect` siblings tiled to one outer field with one continuous seam per axis and the same non-central intersection when the regions need independent editing, paint, animation, or reuse. Unequal region extents remain legal.
- **Radial `parent` with explicit `link` edges**: `ellipse` per node, `line` per parent–child relation, depth registered to concentric bands around the actual root only after radial organization is resolved upstream; every edge starting and ending on node boundaries and moving outward to the child's depth, junctions coinciding only for a true shared trunk. Root centrality, even fan-out, mirrored branches, and equal radial spacing stay forbidden unless the relationship requires them.
