# Decision Ownership: Plan, Execution, and Reference

> Which role decides what in the Generate runtimes, and how strongly a written decision binds. [`prompt-layers.md`](prompt-layers.md) says what a prompt file may contain and [`prompt-style.md`](prompt-style.md) how it is written; this rule says who owns each decision. Classify a decision here before writing any rule about it, and keep each tier's rules in its own role's files.


Constraint strength and decision ownership are independent. Preserve this chain whenever writing, compressing, or reviewing the default multi-role Generate prompts:

| Layer | Owns |
|---|---|
| User / initial materials | Supplied facts/assets, desired outcome, exclusions, and permission boundaries remain authoritative |
| Strategist / plan + preparation | Assess material sufficiency; trigger permitted topic research and retain its research/provenance pair without expanding adopted webpage URLs; decide the approved content, resources, keys, identity anchors, and exact page roster; record each page's semantic units and their source-stated relationships. While composing the roster, decide which pages need a prepared image, lettering, or illustrated-icon resource and derive the external-resource rows from that need. Sketch macro composition, visual focus, and continuity as Reference when useful, without selecting a carrier mix, a local authoring capability, or element geometry; materialize the planned project-local inventory or record an explicit `Needs-Manual` dependency before execution. For icons, prepare a curated project pool with broad semantic fit rather than assigning files to pages |
| Executor / realization | Use only prepared project-local assets; preserve approved content, relationships, resources, and identity anchors; realize each page by resolving the actual carrier combination, geometry, composition, hierarchy, and treatment together before coordinates — the carrier mix has no upstream owner. Discover and invoke local deterministic authoring capabilities without an upstream capability selection. Treat every Reference as a starting sketch to adjust freely for the page's purpose; follow a `(binding)` field literally. For icons, the complete `<project>/icons/` pool is prepared material; `icons.inventory` is a curated bundled-pool index, not a page-use plan or whitelist, and Executor chooses prepared icons per page without a coverage quota. Sparse local font/color garnish is allowed only while non-structural and non-recurring |

**Hard rule — three ownership tiers**: classify a decision before writing any
rule about it, and keep each tier's rules in its own role's files.

| Tier | Test | Examples | Contract |
|---|---|---|---|
| Plan-only | Needs a prepared file before authoring; holds only across the whole roster; needs one user confirmation; or comes from source semantics | Contract, canvas, page count, roster ids/order, `page_rhythm`, identity anchors (color, type, spacing, icons, style, mode), resources, per-page content, facts, semantic units and their relationships | Execution never reopens or substitutes it; a misfit returns upstream |
| Execution-only | Judged only with the objects on the canvas | Carrier mix, geometry and native contours, composition, coordinates, spacing, hierarchy treatment, effects, per-page icon and image treatment, wrapping | Plan writes no detail here, not even as advice |
| Reference (grey zone) | Useful as a first sketch, decidable either way | Macro composition and focus, continuity and motif, cover/closing composition, Chart/Table `family/key`, image `Image pattern`, motion suggestions | Plan writes a starting sketch; Executor adjusts or replaces it freely for the page's purpose, with no upstream repair and no stated reason. It carries no binding semantics — anything that must hold is written in a plan-only field. It binds only when labeled `(binding)` because the user, a template, or a resource contract requires that property (explicit *must* / *only* / *exactly* / *verbatim*); Executor then follows it literally |

Depth test: one plan given to two competent Executors yields the same content
with different looks — converging looks mean the plan wrote execution,
diverging content means it left semantics open. `design_spec_depth` changes
only wording completeness and Reference length, never which plan-only fields
are written.

**Hard rule — capability knowledge precedes selection**: a role must know that
a capability exists before choosing among capabilities; otherwise a load trigger
circularly depends on a choice made without that capability. The always-read
core of the authoring role therefore carries the recall of every construction
capability — the everyday device menu and effects, the complete preset
vocabulary, the topology decision, and one routing row per deeper module —
while the deeper module itself (effects beyond the everyday block, native-shape
authoring, relationship grammar and topology assembly, and the rarer formula,
hyperlink, chart/table, structured-template, video, animation, and web-image
files) is loaded when its observable trigger appears — evaluated once over the
whole roster before P01, or at the page that first reaches an unforeseen
capability — read completely, and kept for the run. The owning rule is
[`prompt-layers.md`](prompt-layers.md) §2.

**Hard rule — core volume ceiling**: the always-read core of an authoring role
stays small enough that its own content is not diluted by what follows. Measured
against the v2.13.0 baseline, an Executor-phase core of roughly 1,300 lines
across a role file plus a shared technical file produced richer pages than a
4,000-line, 12-file mandatory bundle; the larger bundle flattened expression
while passing every structural gate. Treat that as the working ceiling. When a
core grows past it, shrink it by removing what is not authoring guidance or by
moving a deeper module behind a trigger whose recall stays in the core. The
enforced form of this ceiling is the `stage.generate.executor.flat` load-set
budget in `scripts/prompt_audit_manifest.json`; the line count above is the
measurement that set it. What may stay in a
prompt file at all — craft, minimal contract, tool documentation, or procedure — and the
procedure for moving content out are owned by
[`prompt-layers.md`](prompt-layers.md).

Default Strategist's planning bundle covers resource/preparation and high-level
expression options without local authoring parameters, because those choices are
persisted into artifacts other roles consume. Only post-selection mechanics whose
trigger is independently observable stay conditional: an actual `ai` / `slice`
resource row triggers Image_Generator backend, prompt-assembly, and per-image
type details after planning, and those mechanics are not a missing Strategist
capability.

**Hard rule — native shapes are authoring capabilities, not prepared
resources**: a prepared resource needs a stable project-local file/path before
realization because page authoring cannot acquire or generate it in place.
Office presets, SVG primitives, Connectors, Boolean helpers, and necessary
freeform geometry are locally callable construction capabilities. Strategist
never inventories them or promotes a concrete preset, primitive, Connector,
Boolean/freeform operation, or authoring parameter into a binding planning
selection. A macro Reference may mention a technique as optional inspiration
without prescribing or gating construction. The Design Spec / lock create no
native-shape field; Executor reads the complete current preset vocabulary and
chooses the page-fit construction during realization.

**Preparation timing**: In the default pipeline, topic research and import of
its two-artifact research pair may run before final confirmation. Facts JSON
URLs are not auto-expanded. AI / web / slice acquisition runs only from the
completed `design_spec.md §VIII` and `spec_lock.md`, after final confirmation
and before Executor. Only after normal image search fails may one relevant
adopted page become a Markdown + companion-image source package; review it and
promote accepted files individually, never the whole package. Image_Generator,
Image_Searcher, and icon-sync tooling execute Strategist-owned preparation;
they are not independent decision owners.

**Post-motion sound exception**: optional transition/object sound is not a
page-authoring ingredient and never enters Strategist planning,
`design_spec.md`, or `spec_lock.md`. After the SVG roster and visual motion
solution are complete, the active animation/export stage may discover bundled
sound ids and sync only a concretely selected cue into the project. With no
selected cue, it creates no `<project>/sounds/` directory. This exception does
not permit Executor to acquire visual resources.

**Hard rule — default pipeline**: downstream freedom exists in every dimension the plan leaves open, and every Reference is open by definition. A named binding outcome retains identity; a broad semantic request or expression recommendation permits in-class choice. Once the plan resolves a plan-only choice or a `(binding)` Reference, execution cannot reopen or substitute it. For icons, library/stroke and the prepared-project boundary bind, while per-page choice within the prepared pool is realization. Executor never searches, generates, downloads, syncs, invents, or replaces a resource; missing material returns to Strategist-owned preparation or upstream repair.

**Explicit Quick Generate exception**: [`quick-generate`](../../skills/ppt-master/workflows/profiles/quick-generate.md) removes the separate Strategist/confirmation handoff. The current main agent therefore owns both its active-context decisions and the preparation of project-local sources, images, icons, and provenance before it begins SVG realization; native formulas are authored directly from exact mathematical content rather than acquired as resources. This exception does not move acquisition into a default-pipeline Executor and does not permit resource reselection while a page is being realized. Explicit user facts, choices, exclusions, and permissions remain upstream authority; unspecified routine choices are resolved automatically without a confirmation stop.

> Mnemonic — restaurant contract: the customer supplies initial ingredients and the desired dish; Strategist plans the dish and prepares the complete mise en place; Executor cooks from that prepared inventory. “Mapo tofu” cannot become tomato-and-eggs or tofu soup, while “a tofu dish” leaves deliberate in-class freedom. Equally: the plan is the general contractor — materials, structure, and a first blueprint; Executor is the crew that builds the finished work on that structure, adapting to the site.

**Review gate**: treat any prompt refactor that erases the selected profile's ownership chain, moves acquisition into the default-pipeline Executor, turns a permission into a quota, or turns flexible realization into silent resource/identity reselection as a semantic regression even when the compressed wording is shorter.
