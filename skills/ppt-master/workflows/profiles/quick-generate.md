---
description: One-pass Generate profile for agent-decided preparation, direct SVG authoring, and final PPTX delivery without durable planning or confirmation artifacts.
---

# Quick Generate Profile

> Generate-PPTX profile, not a top-level route. The current main agent completes
> one uninterrupted run without a separate Strategist/confirmation handoff or a
> resumable design record. This removes interaction and traceability, not the
> facts, resources, or authoring capabilities needed to build the final deck.

**Trigger**: the user explicitly requests quick/fast generation, asks to skip
strategy/confirmation, or directs the agent to proceed to SVG and export.
Page count alone never activates or blocks this profile.

---

## 1. Profile Boundary

| Concern | Quick Generate contract |
|---|---|
| Authority | Follow every explicit user requirement as stated; decide every unspecified choice directly without asking |
| Interaction | The current main agent decides content, design, resources, and implementation without Strategist, Confirm UI, or approval stops |
| Execution memory | Keep routine page, visual, and resource decisions only in the current active context; losing that context restarts Quick instead of reconstructing a plan from project files |
| Inputs | Any supported Generate input; convert/import sources and run bounded factual research when the input requires them |
| Templates | Directly validate and install at most one exact workspace root per kind supplied for this run; when none are supplied, use free design without catalog selection or Confirm UI |
| Resources | Prepare every project-local image, icon, formula, and required provenance/manifest artifact before the referencing SVG is authored |
| Planning artifacts | Do not author a root project `design_spec.md`, `spec_lock.md`, confirmation payloads, or any substitute planning artifact; installed `templates/design_spec.<kind>.<id>.md` files remain template input |
| Traceability | Operational resource manifests, checker reports, postflight, and bounded Python command/outcome audit entries may remain, but they do not record the AI's design reasoning or form a resumable generation history |
| Delivery | Hand-author the resolved SVG roster, run one lockless final checker, skip `finalize_svg.py`, and export the final native PPTX through `--quick-generate` |

**Artifact ownership**: follow
[`artifact-ownership.md`](../../references/artifact-ownership.md) for source,
fact, author, derived, and regeneration boundaries. Quick changes the planning
handoff, not those artifact roles.

**Hard rule — speed removes interaction and durable planning, not capability**:
all ordinary source, research, visual-carrier, resource-preparation, analysis,
authoring, and export capabilities remain available when they serve the deck.
This is capability availability, not a requirement to use every carrier.

Explicit user facts, wording, choices, exclusions, and permission boundaries
still win. For every unspecified routine choice, decide directly and continue;
do not ask the user to approve a strategy or implementation detail.

After entry, continue through selected work, the final checker, and export.
Pause only for user interruption or an unresolved hard prerequisite.

**Default — optional production behavior (may override when useful)**: Speaker
notes, custom object animations, and narration start off. The current agent may
enable any ordinary capability when the request or deck benefits; use its
normal inputs, flags, and prerequisites without asking for approval. Quick
never creates or reads a root project Design Spec or lock to enable it.

**Mandatory — discover motion before deciding whether to load it**: scan this
compact gate once; do not load the full execution reference when the defaults
already fit.

| Signal | Action |
|---|---|
| The same semantic object or scene continues across adjacent pages | Load [`animations.md`](../../references/animations.md) before SVG authoring; prepare both visible endpoints and use its Morph contract |
| Page- or object-specific reveal, renewed emphasis, meaningful movement, or same-page removal clarifies the message | Load [`animations.md`](../../references/animations.md) before SVG authoring; preserve the required units/states, then run [`customize-animations`](../stages/customize-animations.md) after the final checker |
| One deck-wide entrance policy supplies all required staged reveal | Load [`animations.md`](../../references/animations.md) before export and use an exporter flag such as `-a auto`; do not run the custom stage |
| A directional/section boundary benefits from a non-default transition | Load [`animations.md`](../../references/animations.md) before export and select from its §3 playbook |
| No earlier signal applies | Keep `fade` transitions and object animation `none`; do not load the motion reference |

This gate activates capability discovery, not motion coverage. Keep the
defaults when no row supplies a concrete communication job. When several
signals apply, perform every required action and use the earliest required load
point; a before-authoring signal always overrides a before-export-only timing.

---

## 2. Source and Resource Preparation

Prepare source facts before initialization:

| Input | Action |
|---|---|
| Topic or requirements without supporting facts | Run [`topic-research`](../stages/topic-research.md) immediately and retain its Markdown supplement plus fact-provenance JSON for import |
| PDF / DOCX / Office document / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | Run `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]` |
| CSV / TSV | Read directly as a plain-text table source |
| Markdown or direct conversation text | Read directly |

The conversion dispatcher writes standard Markdown plus its conversion profile
beside each local source by default. Use `-t <type>` only when detection is
ambiguous and `-o` only for a required output path; with several or directory
inputs, `-o` names an output directory. A PPTX is converted to Markdown here and
receives its project analysis during the import step below.

**Source-image orientation trigger**: Before import and initialization, follow
[`conversion.md`](../../scripts/docs/conversion.md) § Image Orientation Review
when correction is requested, converted text asks for rotated viewing, or a
downloaded asset is visibly sideways. Skip the legacy HTML tool.

After reading every direct and converted source, assess factual sufficiency:

| Material state | Action |
|---|---|
| The requested outcome is supported | Continue |
| A required externally verifiable claim remains unsupported | Run [`topic-research`](../stages/topic-research.md) for those gaps only |
| Closed corpus / source-only / no external enrichment | Stay within the supplied material |

**Sufficiency test**: research only when the requested outcome would otherwise
require inventing, omitting, or leaving unsupported an externally verifiable
claim. File presence or length does not establish sufficiency. Research gathers
facts only; image acquisition remains part of the resource preparation below.

Before initialization, resolve exactly one template branch:

- **Direct template application**: one or more exact current workspace roots
  were supplied in the request, or Create Template returned an exact validated
  root in the current conversation. Accept at most one root per declared kind.
  Before initialization, load
  [`apply-template-workspace`](../stages/apply-template-workspace.md), normalize
  each supplied root, read only the matching spec frontmatter needed to resolve
  its kind/canvas, and run that stage's read-only schema/structured preflight.
  Do not scan the library, fuzzy-match a name, or open a selector. Explicit user
  canvas wins; otherwise use the selected structure owner (Layout before Deck)
  canvas when present, then fall back to `ppt169`.
- **Free design**: no exact root was supplied. Continue immediately with the
  requested canvas or `ppt169`. A bare template name, brand mention, style
  phrase, or vague request to choose a template is ordinary brief input, not a
  workspace reference.

Neither branch creates anything under `confirm_ui/` or executes
`confirm_ui/server.py`. Initialize the minimal workspace with:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> \
  --format <format> --quick-generate
```

It creates `svg_output/` plus the cold
`validation/workflow.log` command/outcome audit log, and no root README. After
this command, run project-scoped Python tools directly; their shared CLI
bootstrap records command envelopes, material tagged outcomes, bounded status
samples, and omission counts. A concise manual entry is allowed only for a
material stage handoff, rework reason, user-approved exception, or manual
recovery choice that has no owning command output; do not record routine page
progress, artifact contents, or private reasoning.
Never read the log during ordinary Quick execution; open it only for an
explicit user-requested run review. Add
capability inputs only when triggered; later tools create `exports/` and the
default-path `backup/`.

With file-based sources, import the original inputs, converted outputs, and any
research pair together:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources \
  <project_path> <source_files_or_dirs...> [<converted_outputs...>] \
  [projects/<research_slug>.md projects/<research_slug>.facts.json]
```

Only inputs already under the repository's `projects/` tree move into the
target project; every external path is copied and remains untouched. Use
`--copy` when a projects-local input must also remain in place. When conversion
wrote Markdown beside the original source, pass that source path or directory
once; when `-o` wrote it elsewhere, pass both locations. Direct supported bitmap
inputs are archived under `sources/` and copied collision-safely into `images/`.

For each imported PPTX, `import-sources` automatically writes
`analysis/<stem>.identity.json`, `analysis/<stem>.slide_library.json`, and the
multi-deck `analysis/source_profile.json` index. Read that index as source facts
and open a per-deck artifact only when the current task needs its additional
detail; these facts are recommendations, not replica constraints. Distinct PPTX
stems may coexist, and re-importing one stem replaces only that deck's entry.

Conversion companion manifests may place extracted SVG/EMF/WMF assets into the
project resource flow. Preserve EMF/WMF as vector references and never convert
them to PNG; browser preview may be blank while native PPTX export remains the
source of truth. Standalone SVG/EMF/WMF inputs remain source assets unless such
a manifest supplies their display metadata.

Never scaffold a Design Spec or lock. Use a new path, or verify that an existing
path's `svg_output/` is empty; Quick ignores any existing `design_spec.md` or
`spec_lock.md`.

The audit log is an operational tool record only. It does not capture direct
SVG authoring, active-context design choices, or private reasoning and cannot be
used to resume or reconstruct a Quick run.

For the direct-template branch, continue with
[`apply-template-workspace`](../stages/apply-template-workspace.md) after
initialization against only the preflighted roots. The user's request is the
selection authority; there is no template confirmation receipt or handoff. The
stage installs each workspace as its own spec file under `<project_path>/templates/` plus
the project-local asset pools. All later reads use that installed state, never
the original roots.

Before writing P01, read every installed
`templates/design_spec.<kind>.<id>.md` once and, for Layout/Deck, inspect the
relevant SVG prototypes. Apply Brand identity, Style direction/method, the
selected structure owner's useful prototype geometry, and Deck application
context directly in the active context under the existing segment precedence
([`apply-template-workspace`](../stages/apply-template-workspace.md) §5). A
segment owner's instruction about how a value should dominate, recede, or stay
rare binds as strongly as the value itself; a Style composition or whitespace
tendency never demotes a Brand's declared dominant color to an incidental
accent. Follow explicit instructions about literal or visual-only
use; otherwise decide which prototypes to use, skip, repeat, reorder, or adapt
while authoring. Persist no separate template-application artifact. If no
template was installed, make the same design choices freely.

**One-pass decision boundary**: resolve only what is needed to author this deck
in the current context. Do not print a strategy summary, create a planning
checkpoint, or persist a page/resource plan.

Before writing P01, resolve in active context:

- the exact slide roster and one compact core message for every page, used to choose its composition and hierarchy;
- the canvas, visual direction, palette, wording, and one concrete typography plan using installed font families, with stable size anchors for title, body, annotation, and every other recurring role the roster uses; explicit user, template, or resolved-style requirements may call for a deliberate exception;
- an ordinary body-content frame and a density judgment for every page, adapted to the canvas and any user / template / style geometry; use `anchor`, `dense`, `breathing`, or an equivalent active-context distinction instead of one uniform fill level;
- for each page not bound to literal supplied geometry, a primary visual zone and page-scale composition direction tied to its core message; use cards or equal grids when the content relationship calls for them, not as the automatic page grammar;
- when useful, one transient deck-level visual motif with an identity or
  communication job, a recognizable invariant, and deliberate variation across
  applicable page roles; omit it when restraint serves the deck better;
- the resource decisions needed for immediate preparation. Required operational
  image/formula manifests may carry filenames, page relationship, status, and
  generation/crop/focal cues, but do not create a general resource roster or an
  icon-to-page assignment;
- the implementation path for each resource. An explicit user path wins;
  otherwise choose the registered automatic/default path without another
  interaction.

**Mandatory — capability scan, not a coverage quota**: for every page, consider
the complete carrier menu once and choose only the forms that communicate its
content best. A decision to use none of a carrier is valid; skipping the scan
because Quick is expected to be faster is not.

| Communication job | Available carrier |
|---|---|
| Real subject, place, product, evidence, atmosphere, or scene benefits from visual grounding | Supplied/extracted, web, AI, or sliced image |
| A compact semantic cue clarifies a category, process, KPI, state, navigation item, or real brand | Prepared project-local icon |
| Editable geometry can express a relationship, flow, emphasis, callout, symbol, or diagram | Basic SVG primitive, exact Office preset, Boolean result, then necessary freeform |
| Values encode comparison, trend, distribution, composition, relationship, or a text grid | Data chart or table, with optional native Chart/Table metadata when its object model is useful |
| Mathematical notation is clearer as typeset math than ordinary text | Rendered formula asset |
| Typography, spacing, and simple geometry already carry the message | Use no additional visual carrier |

Prepare only the resource paths needed by the decided pages:

| Resource | Required preparation |
|---|---|
| Supplied/extracted image | Copy the selected file into `images/`; preserve its factual/provenance context and use the measured file rather than an invented substitute |
| Bundled/custom icon | Follow the [icon library contract](../../templates/icons/README.md), choose one coherent primary library, sync a useful project pool covering recurring semantics and likely page-local needs without assigning icons to pages, and choose from that prepared pool during SVG authoring |
| Formula | Follow the [`latex_render.py` contract](../../scripts/docs/image.md), write `images/formula_manifest.json`, run the renderer, and keep the rendered PNG under `images/` |
| AI image | Follow `image-base.md` + `image-generator.md`; keep `image_prompts.json` and its human-readable sidecar |
| Web image | Follow `image-base.md` + `image-searcher.md`; keep query/status data and `image_sources.json`, including any required on-slide attribution |
| Illustration slice | Generate or obtain the parent sheet, run `slice_images.py`, and place only the resulting element files |
| Data chart/table | Keep source values and the chosen page treatment in active context; load the chart/table authorities in §3 before drawing and write native replacement metadata only when selected |

**Image inspection boundary**: acquisition-time suitability review follows the
owning AI/web/slice reference. Once resources reach terminal status, SVG
authoring follows `executor-image.md`'s narrow placement inspection: inspect only
one specifically ambiguous `Existing`/`Sourced` asset and never routinely reopen
`Generated` outputs.

After image resources change, run `analyze_images.py` so
`analysis/image_analysis.csv` reflects the files that SVG authoring will use.
Operational manifests and provenance are resource truth, not a hidden design
strategy.

Every required resource must reach a usable terminal state before the
referencing page is authored. A required `Needs-Manual` resource blocks Quick
delivery even when an unverified candidate file exists. After a manual supply
or replacement, validate the file/provenance and reconcile the row to
`Generated`, `Sourced`, or `Rendered`; do not use file presence as a bypass or
silently replace it with unrelated material.

---

## 3. Direct SVG Authoring

Always read the following fixed authoring references directly in one batch; do
not route among them one file at a time:
[`shared-standards-core.md`](../../references/shared-standards-core.md),
[`svg-effects.md`](../../references/svg-effects.md),
[`native-shape-authoring.md`](../../references/native-shape-authoring.md),
[`semantic-svg.md`](../../references/semantic-svg.md),
[`modes/_index.md`](../../references/modes/_index.md), and
[`visual-styles/_index.md`](../../references/visual-styles/_index.md). Resolve
one narrative mode and one visual style from explicit user/template requirements
or the current content, keep that choice only in active context, and read every
exact preset source actually used once. A genuinely novel custom direction
follows its resolved behavior without inventing a nearby preset.

Do not load `executor-base.md`: it owns Default's persisted-plan handoff,
first-page gate, and completion routing. Excluding that file is not a capability
exclusion; Quick loads the shared and conditional execution authorities here
directly. For any image/formula, always read
[`executor-image.md`](../../references/executor-image.md),
[`image-layout-spec.md`](../../references/image-layout-spec.md),
[`image-layout-patterns.md`](../../references/image-layout-patterns.md), and
[`svg-image-embedding.md`](../../references/svg-image-embedding.md); add
[`executor-web-image.md`](../../references/executor-web-image.md) for a sourced
web image. Load [`canvas-formats.md`](../../references/canvas-formats.md) only
for a non-default canvas.

| Deterministic trigger | Additional authority |
|---|---|
| Any data chart or text-grid table, including mini/inset charts and sparklines | [`executor-chart.md`](../../references/executor-chart.md); use bounded [`chart_recall.py`](../../scripts/docs/chart-recall.md) only when a reusable visualization reference would help |
| Preset pattern or selected PowerPoint-native Chart/Table replacement | [`native-data-interface.md`](../../references/native-data-interface.md) before drawing the object |
| Any data-driven chart geometry | [`verify-charts.md`](../stages/verify-charts.md) after the complete roster and before the one final checker |

Keep the core's shared visual-quality / leading defaults and `svg-effects.md` §6.1 Visual Job Router active while authoring. Explicit user/template requirements and the resolved style override compatible aesthetic defaults, never technical Required / Forbidden boundaries.

**Per-page execution anchors**: apply the transient core-message, typography-role, body-frame, density, and composition anchors resolved in §2 while authoring; they guide the current run without creating a persisted planning artifact.

Use one zero-padded filename width sized for the resolved roster, such as
`01_cover.svg` through `12_end.svg` or `001_cover.svg` through `120_end.svg`.
Never reuse pages from another run: the exporter publishes every SVG discovered
under `svg_output/`.

**Canvas**: use the canvas resolved in §2: explicit user choice, otherwise the
selected Layout/Deck structure-owner canvas, otherwise `ppt169` with
`viewBox="0 0 1280 720"`. For another registered format, load
[`canvas-formats.md`](../../references/canvas-formats.md) and use its exact
viewBox. Template canvas is a default, not a compatibility gate; an explicit
user canvas may adapt the installed visual system. The first SVG establishes
the export canvas; every remaining page must match it exactly.

**Structure**: author flat, Slide-local SVG only, including when a Layout or
Deck workspace is installed. In that branch, visibly realize the resolved
template rules and prototype geometry in the complete pages; do not fall back to
free design or merely explain how the template could be used. Include the
complete visible page and all resource references in each SVG; set one root
`data-pptx-page-role` from `cover`, `toc`, `section`, `content`, or `ending`,
and omit Master/Layout/layer/placeholder metadata. A request that specifically
requires reusable native Master/Layout/placeholder output is incompatible with
the lockless Quick exporter and must use the default lock-backed profile.

**Typography**: name an installed concrete font family in the SVG; do not depend
on a lock or generated font asset.

**Generation pacing**: the current main agent hand-writes the SVG roster in
order. Use P01 as the visual anchor and continue directly through the remaining
pages without a first-page checker or confirmation stop. When a motif was
resolved, reuse it selectively and vary scale, crop, density, position, or
content interaction instead of cloning one ornament. Keep this choice only in
active context; create no planning artifact or approval stop. After every page
exists, run the one final checker below. Apply other supporting tools and
stages only when their capability is actually needed.

This is not a resume protocol. If the active context is lost before delivery,
start a clean Quick run rather than inferring an unfinished plan from the files
already present.

---

## 4. Export

After every page and required referenced resource exists, run the Quick branch
of [`verify-charts`](../stages/verify-charts.md) when any data-driven chart was
authored. Complete all coordinate repairs first; then run the one lockless final
SVG check:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --quick-generate --stage final --json
```

Fix every blocking error and rerun the same command. Then export:

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate
```

`--quick-generate` reads `svg_output/` as the page source and resolves the
project-local assets referenced by those SVGs. It infers one consistent canvas,
uses a lockless flat PowerPoint package, and does not force-disable ordinary
export options. Notes, custom object animation, and narration remain off unless
selected by the agent. Do not run `finalize_svg.py`.

The exporter requires a passing `final` report whose SVG fingerprint matches
the current `svg_output/`; missing, blocking, non-final, or stale reports stop
before PPTX creation. The default output path retains ordinary backup and
postflight behavior. An explicit `-o <path>.pptx` keeps the ordinary no-backup
behavior. On failure, repair the owning SVG, resource, or optional capability
input, rerun the final checker, then export again; do not create a Design Spec
or lock.

```markdown
## ✅ Quick Generate Complete

- [x] All required source/resource preparation is complete
- [x] One mode and visual style were resolved, and every catalog source actually used was read
- [x] Every page considered the complete visual-carrier menu without a coverage quota
- [x] Resolved SVG pages and their project-local references exist
- [x] Every role declared by an installed template spec is locatable in the finished pages, or its non-use is deliberate — checked per installed spec, not from memory
- [x] Every triggered capability-specific preparation and pre-checker verification completed
- [x] The lockless final SVG quality report passes and matches the current SVGs
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No Strategist, confirmation, root project Design Spec, or lock artifact was created
- [ ] **Next**: Report the PPTX path
```
