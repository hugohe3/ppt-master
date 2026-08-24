> See [`executor-structure.md`](./executor-structure.md) §1 for relationship → topology and [`native-shape-authoring.md`](./native-shape-authoring.md) §§1–2.1 for contour selection and materialization.

# Topology Assembly Reference

Generative material for turning one resolved qualitative topology into editable native-shape components with coherent relative registration before coordinates.

**Load**: Default and Quick read this reference once with the fixed construction
bundle before SVG authoring and reuse it for every `Structure=yes` assembly.

**Hard rule — relative constraints, never copyable geometry**: State exact
preset or primitive identities, semantic counts, inter-component relations, and
only the relative geometry required to make the assembly hold together. Never
provide coordinates, concrete sizes or ratios, adjustment values, points, path
data, SVG fragments, copy, color, styling, page composition, or full-page
frames. Materialize every adopted call fresh through
[`native-shape-authoring.md`](./native-shape-authoring.md).

**Mandatory — two-step assembly test**: Preserve the topology resolved by
[`executor-structure.md`](./executor-structure.md); do not select or rename it
here. Then decide in order:

1. Split every piece that needs independent editing, movement, paint, animation, or reuse.
2. From outline and region semantics, choose one continuous shape, one shape with dividers, stacked siblings, seamed pieces, overlapping siblings, or independently retained Boolean regions.

**Mandatory — registration closure**: After the two-step test, resolve only the
relative conditions that make the chosen pieces read as one construct: shared
datum, center, taper, or contour; aligned endpoints and seams; fitted contact or
intentional clearance; nesting margin; overlap depth; joint type; direction
continuity; and cutters that fully cross the parent silhouette. A set of valid
individual shapes is not an assembly until its required contacts and boundaries
register.

**Hard rule — no assembly lookup**: Never recall a paragraph as a named
structure, resolve a key, or match the page to the nearest mechanism. Generate
from the active atoms and the two-step test; adapt, combine, or invent calls and
relative constraints even when no paragraph resembles the result.

**Reference — not a constraint**: The mechanisms below are common generative
material rather than an exhaustive set, ranking, recommendation, or allowed
combination list. A primitive, another registered preset, necessary freeform,
or no drawn carrier may still win the current contour comparison.

**Hard rule — semantic counts, not balance**: Derive every call count from real
units, runs, turns, boundaries, junctions, owners, or retained regions. A count
never implies equal size, spacing, angle, weight, or symmetry. Closure,
mirroring, centrality, taper, interlock, and contact require the relationship
meaning already resolved upstream.

**Hard rule — information-model boundary**: Value-derived position, length,
width, area, angle, radius, or color remains Chart geometry; row-header ×
column-header facts remain Table. The assemblies below carry only qualitative
relationships.

---

## 1. `order`

For independently owned stages on one directional path, call `chevron` once per
stage and keep the calls as siblings. On a continuous handoff, register each
tip into the next notch and keep the entry / exit direction coherent through
the joint; let the tip enter far enough to close the carrier without occluding
the next stage's independently owned interior. Preserve an intentional gap when
the boundary is a pause, reset, or discontinuity. The per-stage split preserves
independent edit, paint, animation, and reuse duties; continuity versus boundary
semantics decides fitted interlock versus clearance. Stage bodies may vary with
their duties while every adopted joint still fits.

For a path that wraps and reverses, call `rightArrow` once per forward run,
`leftArrow` once per return run, `downArrow` once per turn, and `roundRect` once
per independently owned stop. Place successive runs on distinct parallel
baselines; align each turn's entry with the preceding run endpoint and its exit
with the next run entry so the path neither doubles back ambiguously nor jumps
across a gap. Attach each stop to its owning run without covering the carrier's
entry, exit, or turn joint. Stops split for independent duties; run and turn
pieces split because each owns a distinct direction / continuation duty.
Contact at a turn means continuation, while clearance means a stage break; run
lengths and offsets follow the resolved path rather than a regular wrap.

For recurrence with independently owned stages, call `blockArc` once per stage
and seam the siblings into one closed reading path. Make every segment share one
center and registered inner / outer contours; meet adjacent end faces on both
contours so the ring has neither accidental steps nor overlaps. Segment spans
may differ, but their sequence and seam direction must remain legible. Retain a
gap only for a semantic reset. When recurrence is one indivisible duty, call one
`circularArrow` instead. Stage independence decides one versus many pieces;
recurrence and direction decide closure, while shared-center registration makes
the segmented result one carrier rather than unrelated arcs.

---

## 2. `link`

For a qualitative split or merge, call `roundRect` once per semantic source or
target and `line` once per necessary edge. Call `ellipse` zero or one time for
each junction: omit it when edges merely share a meeting point, and retain it
when the junction is independently editable, reusable, or animatable. Terminate
each edge on its node boundary rather than inside the node; make converging edge
endpoints meet the same junction, preserve a collinear shared trunk when one
exists, and separate branches soon enough that they do not read as one line.
An apparent crossing must either remain visibly non-joining or receive a real
semantic junction. Nodes, edges, and retained junctions split by ownership;
junction and outline semantics decide an implied meeting, one visible node, or
separate passing paths.

For a two-way exchange owned as one relationship, call one `leftRightArrow`
between two independently owned `roundRect` nodes. Register both arrow ends to
the facing node boundaries and preserve one uninterrupted exchange corridor.
When the two directions need independent editing, paint, animation, or reuse,
call one `rightArrow` and one `leftArrow` as parallel siblings instead. Keep the
two directional corridors distinct, align each endpoint to its own node port,
and prevent either arrowhead from covering the other carrier or a node interior.
Directional responsibility decides whether the edge splits; reciprocal-single-
duty versus two owned transfers decides one contour or two, while endpoint and
corridor registration preserves the exchange.

---

## 3. `parent`

For enclosure hierarchy or nested bubbles, call `ellipse` once per unit that
owns a visible boundary and nest each child inside its immediate parent. Keep
all ellipses as independent siblings rather than unioning parent and child.
Preserve a visible containment margin around every child, keep its complete
boundary inside the parent, and prevent sibling interiors from touching unless
another active atom requires contact or overlap. Deeper levels may move,
contract, or cluster asymmetrically; they need only preserve unambiguous
containment and enough parent field to remain perceptible. Independent node
ownership requires separate edit, movement, paint, animation, and reuse;
enclosure semantics requires nesting while preserving every outline.

For an indented decomposition without explicit relationship edges, call
`roundRect` once per independently owned node and `leftBrace` once for each
parent whose child group needs a visible shared boundary. Register siblings to
one depth datum, place the child group deeper than its parent, and make the brace
span only that parent's actual children with its open side facing their shared
entry edge. Nested braces must remain distinct and must not cross a node
boundary. Nodes split for independent duties; the brace remains a separate
shared ownership mark because one outline governs several children. Depth and
group extent, not equal offsets or repeated widths, carry the hierarchy.

---

## 4. `membership`

For independently owned qualitative lanes, call `rect` once per lane and
`roundRect` once per member that needs a carrier. Keep lane fields as parallel
siblings; make adjacent long boundaries share one seam when membership is
continuous, or preserve a clear gap when the groups are separate fields. Keep
each member's complete contour inside its owning lane with a visible nesting
margin; cross a lane boundary only when the member truly has multiple ownership
or changes owner. If all lanes form one indivisible field and only boundaries
carry meaning, call one `rect` for the field and `line` once per semantic lane
boundary instead. Independent lane / member duties require siblings; one-field
semantics permits dividers. Lane width and occupancy follow responsibility, not
uniform partitioning.

For membership that needs a light grouping boundary rather than a closed field,
call `leftBrace` once per group and `roundRect` once per independently owned
member. Keep the brace separate, face its open side toward the members, span the
complete member group but no adjacent group, and maintain clearance so neither
the brace nor a nested brace touches a member contour. Members split for
independent edit, movement, paint, animation, and reuse; one brace is the shared
ownership mark because the group boundary itself is one duty. Member count does
not require repeated contours, equal spacing, or equal weight.

---

## 5. `contrast`

For opposing fields on one comparison baseline, call `rect` once per field when
the sides need independent editing, movement, paint, animation, or reuse. Align
the comparable anchors to a shared baseline and register the facing boundaries
as parallel edges separated by either a semantic gap or one explicit `line`
divider; do not let an incidental offset become a false rank. If the field is
one indivisible duty and only the state boundary matters, call one `rect` plus
one `line` at that boundary instead. Independent side responsibility decides
two siblings versus one divided field; opposing-field semantics decides the
facing joint. Shared framing and counterweight never require equal dimensions
or mirrored content.

For a tapered rank or support stack, call `trapezoid` once per independently
owned tier and stack the siblings with semantic seams. Register all tier side
edges to one shared taper, make each adjacent seam meet across the complete
current width, and vary tier width monotonically in the rank direction without
assuming equal change, height, or area. Do not substitute one `triangle` plus
divider lines when tiers need independent paint or animation. If the whole
stack is one duty, call one `triangle` plus one `line` per semantic tier
boundary; make every divider cross the interior and terminate on both outer
edges so no tier leaks into the next. If one registered outer silhouette and
independently retained tier regions are both required, call one `triangle` plus
one `rect` strip per tier region, make every strip fully cross the parent
silhouette and meet the next strip without an accidental sliver, run `fragment`,
and retain the required triangle-covered regions. Independent tier duty decides
the split; continuous-outline versus retained-region semantics decides stacked
siblings, dividers, or Boolean regions. Shared taper and complete crossings keep
all three routes registered as one stack.

---

## 6. `overlap`

When each owner must remain independently editable and the shared area needs no
separate treatment, call `ellipse` once per owner and overlap the calls as
siblings without Boolean materialization. Preserve enough of every complete
owner boundary to identify it, make each intended common area substantial
enough to read as a region rather than an accidental tangent, and avoid full
containment unless subset meaning is active. Choose overlap order and depth so
one owner does not erase another owner or create unintended micro-regions.
Owner responsibility requires the split; outline semantics preserves each
complete boundary, while the common area remains a consequence of overlap.
Paired, chained, or layered ownership does not imply equal ellipses or symmetric
intersection.

When exclusive and shared regions need independent editing, paint, animation,
or reuse, call `ellipse` once per owner, run `fragment` across the overlapping
set, and retain every required exclusive / shared result as an independent
shape. Register the owner overlaps before fragmenting so their crossings produce
only the semantic regions; eliminate accidental tangencies, hidden owners, and
unintended slivers rather than retaining them as topology. Region
responsibility—not owner count alone—requires the further split; exact retained-
region semantics requires `fragment` rather than ordinary siblings or
`intersect`, which keeps only the common region. Retain no region merely to
complete a symmetric pattern.

---

## 7. Combined atoms

**Mandatory — compose active topologies, not reference paragraphs**: Generate
each active atom's topology from its own relationship duties, then resolve how
those topologies share a field, nest, run in parallel, cross orthogonally, or
intersect. Preserve each atom's ownership and reading direction. Let one
component carry several atoms only when its edit, movement, paint, animation,
reuse, outline, and region duties never need to separate; otherwise keep the
atom systems as registered siblings. Re-run the two-step test at every contact,
crossing, shared boundary, and retained region. A shared field does not make one
atom dominant, and authoring convenience never justifies merging them.

For an actual `order` path crossing `membership` lanes, call `rect` once per
independently owned lane, `roundRect` once per process unit, `line` once per
necessary transition, and `line` once per semantic phase boundary. Keep all
lane bands parallel and register the process axis orthogonally across them.
Place each process unit fully inside its current owner's lane; let only a real
responsibility transfer cross a lane seam, and terminate every transition on
the process-unit boundaries rather than using a lane boundary as an edge.
Phase boundaries must cross the lane field coherently and remain distinguishable
from process transitions. If lane regions are one field duty, use one `rect`
plus lane dividers instead of independent lane rectangles. Lane ownership and
process-unit responsibility decide the splits; orthogonal registration keeps
the two atom systems readable without implying equal bands, phases, or steps.

For two independent `contrast` dimensions partitioning one field, call one
`rect` plus one `line` per axis when only the axes carry meaning. Make both axes
cross the complete field, keep them orthogonal, and let their intersection move
with the semantic thresholds rather than centering it. When the four resulting
regions need independent editing, movement, paint, animation, or reuse, call
four `rect` siblings instead; tile them to one shared outer field with one
continuous seam per axis, no accidental gaps or overlaps, and the same
non-central intersection when required. Axis-only semantics chooses one body
with dividers; region responsibility chooses four siblings. Orthogonality and
continuous seams create one partition while unequal region extents remain
legal.

For a radial `parent` topology whose ancestry requires explicit `link` edges,
call `ellipse` once per semantic node and `line` once per parent-child relation.
Only after radial organization is resolved upstream, register depth to
concentric bands around the actual root; the bands and sibling sectors may vary
with role and content. Start and end every edge on node boundaries, keep each
branch moving outward to the child's depth, and make shared branch junctions
coincide only when the relations truly share a trunk. Nodes split for
independent content and motion duties; edges remain separate because ancestry
is a relation rather than a shared silhouette. Concentric registration makes
depth legible, while root centrality, even fan-out, mirrored branches, and equal
radial spacing remain forbidden unless the relationship itself requires them.

