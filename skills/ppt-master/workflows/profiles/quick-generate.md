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
| Resources | Prepare every project-local image, icon, and required provenance/manifest artifact before its SVG; author native formula markers and hyperlink anchors directly in the affected SVG; sound waits for §4 |
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
notes, Custom Animations, and narration start off for ordinary Quick work. The
current agent may enable any ordinary capability when the request or deck
benefits; use its normal inputs, flags, and prerequisites without asking for
approval. Quick video delivery follows the mandatory Custom Animations rule
below. Quick never creates or reads a root project Design Spec or lock to enable
an optional or mandatory capability.

**Mandatory — discover motion before deciding whether to load it**: apply this
gate once during §2's pre-P01 planning. Do not load the full reference when
the defaults fit.

| Signal | Action |
|---|---|
| Adjacent beats may share one mental map | Evaluate visible states; repetition alone does not require Morph. If continuity clarifies orientation, enable Custom Animations, load [`animations.md`](../../references/animations.md) before SVG, and author compatible Morph endpoints |
| Page- or object-specific reveal, renewed emphasis, meaningful movement, or same-page removal clarifies the message | Load [`animations.md`](../../references/animations.md) before SVG authoring; preserve the required units/states, then run [`customize-animations`](../stages/customize-animations.md) after the final checker |
| One deck-wide entrance policy supplies all required staged reveal | Load [`animations.md`](../../references/animations.md) before export and use an exporter flag such as `-a auto`; do not run the custom stage |
| A directional/section boundary benefits from a non-default transition | Load [`animations.md`](../../references/animations.md) before export and select from its §3 playbook |
| No earlier signal applies | Keep `fade` transitions and object animation `none`; do not load the motion reference |

This gate activates capability discovery, not motion coverage. Keep the
defaults when no row supplies a concrete communication job. When several
signals apply, perform every required action and use the earliest required load
point; a before-authoring signal always overrides a before-export-only timing.

**Hard rule — Quick video Custom Animations**: when
[`video-design.md`](../../references/video-design.md) is active because the
effective Quick delivery purpose is recorded, self-running, or video-directed,
enable Custom Animations, load [`animations.md`](../../references/animations.md)
before SVG authoring, preserve the required semantic motion units, and run
[`customize-animations`](../stages/customize-animations.md) after the final
checker. Use the discovery table above to choose the choreography, not whether
Custom Animations exists. Individual pages or groups may remain static, so this
is not an animation-coverage quota. A Quick video run without a validated
`animations.json` fails this requirement unless the user explicitly requests
static or page-transition-only playback. Narration-governed motion also
activates cue synchronization.

---

## 2. Source and Resource Preparation

Prepare source facts before initialization:

| Input | Action |
|---|---|
| Topic or requirements without supporting facts | Run [`topic-research`](../stages/topic-research.md) immediately and retain its Markdown supplement plus fact-provenance JSON; adopted webpage URLs remain inside that pair and are not import inputs |
| One or more PNG / JPEG / WebP files representing page frames under Image to PPTX | Do not call `source_to_md.py`; normalize single-page files and multi-frame contact sheets into the canonical ordered frame roster through that profile, then import the originals below |
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
| Image to PPTX page surface | Treat as a closed visible corpus; unreadable/occluded regions become `manual_required`, never external research |
| The requested outcome is supported | Continue |
| A required externally verifiable claim remains unsupported | Run [`topic-research`](../stages/topic-research.md) for those gaps only |
| Closed corpus / source-only / no external enrichment | Stay within the supplied material |

**Sufficiency test**: research only when the requested outcome would otherwise
require inventing, omitting, or leaving unsupported an externally verifiable
claim. File presence or length does not establish sufficiency. Research records
the needed facts and adopted webpage URLs in its research pair. Project
initialization fetches none of those pages; independent AI / web / slice
acquisition remains part of the resource preparation below.

**Conditional video-delivery context**: when the intended use is recorded,
self-running, or video-directed—or an explicit final/literal narration script
will become notes/audio—read
[`video-design.md`](../../references/video-design.md) now and retain it through
roster, SVG, notes, and motion decisions. This changes neither the Quick profile
nor its artifacts.

Before initialization, resolve exactly one template branch:

When [`image-to-pptx.md`](./image-to-pptx.md) is active, its canonical page
surface owns the design: select **Free design** directly and do not inspect,
install, or apply a supplied template workspace. The branches below apply to
ordinary Quick and other compatible profiles.

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

The facts JSON is the sole URL authority, not a download queue.
`project_manager.py` imports it as an ordinary file and never expands its
`source_url` values. If normal web-image search is exhausted, follow
[`topic-research`](../stages/topic-research.md) § Hand-off to fetch one relevant
webpage package, review it, and copy only accepted images into the runtime pool.

Only inputs already under the repository's `projects/` tree move into the
target project; every external path is copied and remains untouched. Use
`--copy` when a projects-local input must also remain in place. When conversion
wrote Markdown beside the original source, pass that source path or directory
once; when `-o` wrote it elsewhere, pass both locations. Direct supported bitmap
inputs are archived under `sources/` and copied collision-safely into `images/`.
When [`image-to-pptx.md`](./image-to-pptx.md) is active, its
normalized frame roster is canonical page-surface input and the current main
agent writes the source-evidence-only `analysis/reconstruction_inventory.json`
before deciding the layer stack in active context.

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

Before resolving the one-pass design, read the canvas authority and only these
three choice indexes:

```
Read references/canvas-formats.md
Read references/modes/_index.md
Read references/visual-styles/_index.md
Read references/image-renderings/_index.md
```

Resolve the best whole solution from the project brief and index summaries,
freeze its exact mode/style/rendering ids, then read only those selected preset
files or custom-basis files. A novel custom reads none. Never open detail files
to compare candidates, glob a catalog, or let an unselected sibling influence
the decision. Decide whether AI images are useful as a separate source judgment;
even when the answer is no, retain the chosen rendering direction for visual
coherence. Keep the chosen mode, style, rendering, and exact bases in active
context only.

**One-pass decision boundary**: resolve only what is needed to author this deck
in the current context. Do not print a strategy summary, create a planning
checkpoint, or persist a page/resource plan.

Before P01, apply the §1 gate while co-resolving these choices; freeze
the roster after the whole-roster check:

- the narrative beats, mental-map arcs, candidate visible states, their semantic deltas, and enabled notes segments. Adopt continuity only when it clarifies the message. Profile-fixed count/order/content, including 1:1/fidelity, permits only existing-neighbor evaluation; never alter those invariants to manufacture endpoints;
- the effective Speaker Notes, Custom Animations, and Narration Audio outcomes; narration requires notes, later recording alone forces neither audio nor object animation, while a Quick recorded/self-running/video delivery purpose follows [`video-design.md`](../../references/video-design.md) and enables Custom Animations before SVG authoring; direct narrated video additionally enables notes/narration/video and decides before audio whether narration governs group timing;
- the resulting exact slide roster and one compact core message for every page, used to choose its composition and hierarchy;
- the canvas, visual direction, wording, intended viewing distance, and effective reading mode: choose `presentation` for distance-first projected or recorded viewing, `balanced` for mixed viewing, or `text` for close content-heavy reading. Take the initial body anchor and sanity band from [`canvas-formats.md`](../../references/canvas-formats.md) § "Typography Scale Start" for the resolved canvas—PPT remains reading-mode-driven, while registered/custom non-PPT canvases use their canvas-derived start—then resolve one concrete typography plan for the delivery target defined by [`shared-standards-core.md`](../../references/shared-standards-core.md) §4.1, never from the authoring host's font inventory, with stable size anchors for title, body, annotation, and every other recurring role the roster uses. When content does not fit, preserve its core message and apply only fitting actions the source/profile invariants permit—restructure, shorten, or split; if none is permitted, surface the unresolved fit instead of shrinking a recurring role. Explicit user, template, fidelity-profile, or resolved-style requirements may call for a deliberate exception;
- the semantic color roles actually needed by the roster, each with a concrete active-context color anchor, including background/surface, primary/secondary text, dominant/accent, and status roles as applicable. Honor explicit user, installed template/brand, fidelity-profile source-identity, and resolved-style color semantics before deriving only the missing roles that the active profile permits; decide which roles dominate, support, or remain rare, and preserve sufficient contrast for meaning-bearing text. Pair newly authored color-coded states, categories, or relationships with a label, symbol, line, or geometry cue; when fidelity forbids adding one, preserve the source encoding;
- an ordinary body-content frame and a density judgment for every page, adapted to the canvas and any user / template / style geometry; use `anchor`, `dense`, `breathing`, or an equivalent active-context distinction instead of one uniform fill level;
- for each page not bound to literal supplied geometry, a primary visual zone and page-scale composition direction tied to its core message; use cards or equal grids when the content relationship calls for them, not as the automatic page grammar;
- for each page, preserve its semantic units, source-stated qualitative relationships, intended entry, and outcome so §3 can make the sole Structure decision before geometry;
- when useful, one transient deck-level visual motif with an identity or
  communication job, a recognizable invariant, and deliberate variation across
  applicable page roles; omit it when restraint serves the deck better;
- the resource decisions needed for immediate preparation. Required operational
  image manifests may carry filenames, page relationship, status, and
  generation/crop/focal cues, but do not create a general resource roster or an
  icon-to-page assignment. Keep each selected formula's source LaTeX in active
  context for direct marker authoring; retain each selected hyperlink's exact
  absolute URI or 1-based same-deck target; create no formula/link manifest;
- the implementation path for each resource. An explicit user path wins;
  otherwise choose the registered automatic/default path without another
  interaction.

**Prepared final narration**: when the user explicitly marks a script as
final/literal and intends it for notes or generated audio, segment it by semantic
scene while resolving the roster and preserve every spoken word. Before writing
P01, write the ordered segments once to `notes/total.md` with
`# Slide <number>` headings and `---` separators. Keep that file as exact
production input for page design; it is not a planning checkpoint. Do not split
it until the SVG roster exists. Draft narration instead remains source material
and uses the ordinary post-SVG notes branch when notes are enabled.

**Mandatory — image treatment / subject layers**: Before preparation choose per
image: `none`; native SVG crop/transform/depth; or prepared
blur/tone/cutout/registered layers. `none` is valid. A subject crossing native
content requires a clean full-canvas base plus registered RGBA cutout
(`#A2-03`; [`image-generator.md`](../../references/image-generator.md) §4.4);
a floating cutout may use `#A2-01`. Finish assets before SVG per
[`image-base.md`](../../references/image-base.md) §2–3.

**Mandatory — whole-roster rhythm check**: During the same active-context
resolution, compare neighbors and section arcs to judge whether chapter entries
visibly reset, extended same-density runs are intentional, extended same-carrier
or same-topology runs form an intentional semantic sub-arc, repeated dominant
geometry carries a continuity job, each section follows a mode-fitting
progression—including framework → explanation/evidence → judgment/action when
it serves the objective—and the final arc resolves the communication objective
before a genuine ending lowers information load. Repair
the transient roster, density, and composition choices in place. This is
judgment, not quota; preserve intentional continuity, legitimately all-`dense`
material, and 1:1/literal order. Add no filler page: a `breathing` page marks a
meaningful pause—chapter transition, standalone emphasis, or SCQA bridge—and
must stand alone. Create no artifact, checkpoint, lock, or second
authoring/review pass.

**Mandatory — capability scan, not a coverage quota**: for every page, consider
the complete carrier menu once and choose only the forms that communicate its
content best. A decision to use none of a carrier is valid; skipping the scan
because Quick is expected to be faster is not.

**Hard rule**: Credentials do not decide image need. Missing `IMAGE_BACKEND`, host generation, or Pexels/Pixabay keys never justifies a zero-image result or deletion of a web-compatible role. Web acquisition retains zero-config providers; when no generator is callable, use web for compatible real-world roles while explicit generation-only requirements follow the normal Offline Manual boundary.

**Default — visual grounding before a zero-image deck (may override when the user forbids images or charts / native SVG fully carry the visual burden)**: When the audience must recognize, experience, compare, or choose an externally verifiable subject, place, product, or setting, plan supplied/extracted or web images. When a generator is callable, prepare AI imagery proactively where invented or deliberately stylized expression materially improves a planned visual job. This is a semantic decision, not an image-count quota.

**Mandatory — proactive AI decorative lettering**: Apply
[`image-generator.md`](../../references/image-generator.md) §7's
callable-generator test before SVG authoring: a configured `IMAGE_BACKEND` is
Path A and a host-native image-generation tool is Path B; Offline Manual, web
search, or vision-only access does not qualify. When Path A/B is callable and
the user has not forbidden AI, scan the frozen roster for display strings
anywhere in the deck. Exactly two questions decide eligibility: is that wording
stable, and would an artistic treatment communicate better than native type?
Page role, string length, line count, and kind of noun never filter candidates —
a cover hook, chapter word, place or product name, dish or exhibit name, year,
hero number, pull quote, or recurring motif word all qualify when both answers
are yes. Read any such list as examples, never as the set of allowed cases; a
two-character mark, an eight-character phrase, and a two-line lockup are equally
valid, and a phrase is never trimmed toward one or two characters to feel more
"wordmark-like". Set over photography or a busy field is often exactly where
native type reads pasted-on. Eligibility is wide but use stays selective: build
one small coherent set for the deck rather than lettering every heading, and
keep a native title wherever the page needs a searchable, selectable, or
outline-visible heading, with the lettering as its display layer.
If a suitable set exists, prepare it without
a separate request: preserve the exact approved strings, use one ordinary AI
item for a single mark or group several marks by compatible visual family and
batch each family through its own Illustration Sheet and transparent slices.
Give the model the marks' role, placement/background relationship, relative
visual weight, and energy; apply `image-generator.md` §5.3's
controlled-default/high-expression boundary. Split a family
only when its cell geometry or quality needs conflict, and keep ordinary
title/chrome copy native. A prepared wordmark
and an editable title are not mutually exclusive:
one page may carry the wordmark as its display layer while its subtitle, chrome,
and body stay native text, so a wish to keep that wording editable is answered
by the native layer rather than by dropping the lettering. Skip a scanned hook
only when the user forbade AI or no generator is callable; do not add another
disqualifier. Offline Manual
alone does not trigger this proactive path; explicit user-required lettering
still follows the normal resource contract.

| Communication job | Available carrier |
|---|---|
| Real subject, place, product, evidence, atmosphere, or scene benefits from visual grounding | Supplied/extracted, web, AI, or sliced image |
| A compact semantic cue clarifies a category, process, KPI, state, navigation item, or real brand | Prepared project-local icon |
| Editable geometry can express a relationship, flow, emphasis, callout, symbol, or diagram | Basic SVG primitive, exact Office preset, Boolean result, then necessary freeform |
| Values, categories, time, weights, or duration determine mark geometry | Value-driven chart |
| Sequence, hierarchy, role, region, or relationship determines page-local topology | Qualitative structure |
| Rows, columns, cells, headers, merges, and alignment form the information model | Cell-grid table |
| Mathematical notation is clearer as typeset math than ordinary text | PowerPoint-native inline or block math |
| Any stable display string in the deck — cover hook, chapter word, place or product name, dish or exhibit name, year, hero number, pull quote, motif word — reads better with a material, dimensional, hand-rendered, or otherwise illustrative treatment than as ordinary text | Apply the proactive rule above; place prepared lettering assets as images and keep ordinary editable title/chrome in separate text frames |
| Typography, spacing, and simple geometry already carry the message | Use no additional visual carrier |

This carrier menu does not satisfy or replace the per-page Structure decision in §3.

**Mandatory — per-image source decision, never inherited from the resolved style**: Outside Image to PPTX, whose closed page surface owns its reconstruction assets, decide each page image's source separately — supplied/extracted, web, AI, or slice. Prefer a supplied/extracted asset that already carries authority; use web when an externally verifiable subject must appear as itself; use AI when invented or deliberately stylized expression matters more than documentary identity. Mixed sources across one deck are normal.

Resolving one visual style, `Illus.` propensity, or generated-image rendering resolves how imagery **looks**; it resolves the source for no page. A named place, building, product, artwork, person, or other externally verifiable subject stays a web/supplied candidate no matter how illustrative the deck looks. When such a subject is deliberately not shown as itself, state that choice and its reason in the final report rather than leaving it implicit.

**Visualization recall — optional Chart/Table reference**: When a reusable
Chart/Table reference would help, run recall with 3–8 English semantic tags.
Use its default catalog search; add `--family chart|table` only when the page's
information model is already certain. Do not run recall for qualitative shape
composition.

```bash
python3 skills/ppt-master/scripts/visualization_recall.py recall \
  --page P03 \
  --tag "time series" \
  --tag "three metrics" \
  --tag "direction over time" \
  --limit 6
```

Read the result unfiltered and apply
[`visualization-recall.md`](../../scripts/docs/visualization-recall.md)'s
low-confidence semantic fallback before retaining `no-template-match`. Choose at most one primary
Chart/Table `family/key` for a page, validate it with `visualization_recall.py validate`,
and keep its short purpose only in active context. The reference remains
flexible: it does not lock final type, geometry, style, or native output.
Describe an embedded child Chart/Table and every qualitative relationship in
the page's active decision rather than selecting another primary reference.
Actual information models determine the loaded execution branches. Give every independent
Chart/Table a page-local semantic `kebab-case` object key; keep its
`<object-key>=yes|no` native-ready decision and any promoted chart-verification
status in active context. Qualitative relationships create no catalog key or
reusable Master/Layout/placeholder contract.

Prepare only the resource paths needed by the decided pages:

| Resource | Required preparation |
|---|---|
| Supplied/extracted image | Copy the selected file into `images/`; preserve its factual/provenance context and use the measured file rather than an invented substitute |
| Image-to-PPTX reconstruction asset | In Codex, preserve identity graphics through an exact vector, deterministic redraw, sufficient source asset, or reference-based high-resolution reconstruction; keep data graphics native-and-verified or exact. For scene imagery, build the minimum registered clean-base/midground/subject/foreground group; batch padded-bbox-disjoint objects into one shared plate, then split them with grid slicing or independent nested-SVG bbox crops |
| Bundled/custom icon | Follow the [icon library contract](../../templates/icons/README.md), choose one coherent primary library, sync a useful project pool covering recurring semantics and likely page-local needs without assigning icons to pages, and choose from that prepared pool during SVG authoring |
| Formula | Create no resource file. Retain the exact source LaTeX, then choose ordinary text, an inline native marker, or a block native marker under §3; the registered SVG preview is discarded by native export |
| AI image | Follow `image-base.md` + `image-generator.md`; apply only the chosen rendering preset or exact custom bases, never blend unselected catalog identities, and keep `image_prompts.json` plus its human-readable sidecar |
| Web image | Follow `image-base.md` + `image-searcher.md`; keep query/status data and `image_sources.json`, including any required on-slide attribution |
| Illustration / lettering slice | Generate or obtain the parent sheet, run `slice_images.py --trim --alpha --bg KEY_HEX_FROM_PROMPT --strict-alpha`, and place only outputs from a successful strict cut; a lettering sheet names every exact stable string and contains no scene or page chrome |
| Registered reconstruction group | Follow `image-generator.md` §4.4; keep full-canvas members registered with `crop=no-crop`, and materialize every required shared-plate member as an independent picture object |
| Visualization | Keep Chart values, Table cell topology, and chosen treatment in active context; load the applicable Chart/Table authority in §3 and write native replacement metadata only for an independently selected native-ready object |

**Image inspection boundary**: acquisition-time suitability review follows the
owning AI/web/slice reference. Once resources reach terminal status, SVG
authoring follows `executor-image.md`'s narrow placement inspection: inspect only
one specifically ambiguous `Existing`/`Sourced` asset and never routinely reopen
`Generated` outputs. Image to PPTX is the narrow fidelity exception: inspect
every normalized page once for its inventory, inspect every generated
reconstruction layer or shared plate once, and inspect the final recomposition
against the canonical frame. Reopen only the current page or one unresolved
region after that required comparison.

After image resources change, run `analyze_images.py` so
`analysis/image_analysis.csv` reflects the files that SVG authoring will use.
Operational manifests and provenance are resource truth, not a hidden design
strategy.

Every required file-backed resource must reach a usable terminal state before
its page. Web `Needs-Selection` blocks until one thumbnail is promoted or the
bounded ranked pages and materially different query variants are exhausted;
only then may a vision-capable owner fetch one adopted-page source package,
review its companion images, and promote only accepted files; never auto-expand
facts URLs or use those packages as the initial pool.
`Needs-Manual` blocks even when an unverified file exists. With no visual
capability, only the strict metadata-ranked web path may reach `Sourced`, and
its provenance must say `selection_method: metadata-ranked` rather than imply
visual confirmation. After selection or manual supply/replacement, validate
evidence and reconcile to `Existing`, `Generated`, or `Sourced`; never bypass
status by preview/file presence or substitute unrelated material. Native
formula markers are authored page content, not file-backed resources or
terminal-status rows.

---

## 3. Direct SVG Authoring

Always read the following fixed authoring references directly in one batch; do
not route among them one file at a time:
[`shared-standards-core.md`](../../references/shared-standards-core.md),
[`svg-effects.md`](../../references/svg-effects.md),
[`native-shape-authoring.md`](../../references/native-shape-authoring.md),
[`semantic-svg.md`](../../references/semantic-svg.md),
and [`executor-structure.md`](../../references/executor-structure.md). Retain
only the mode/style detail files selected during one-pass design resolution and
realize that chosen direction. Exact `*_references` define the complete basis
of a custom synthesis; a genuinely novel custom follows its resolved behavior
without reading or inventing a nearby preset.

Do not load `executor-base.md`: it owns Default's persisted-plan handoff,
first-page gate, and completion routing. Excluding that file is not a capability
exclusion; Quick loads the shared and conditional execution authorities here
directly. When any image exists, read once before the first affected
page and reuse throughout the valid execution context:
[`executor-image.md`](../../references/executor-image.md),
[`image-layout-spec.md`](../../references/image-layout-spec.md),
[`image-layout-patterns.md`](../../references/image-layout-patterns.md), and
[`svg-image-embedding.md`](../../references/svg-image-embedding.md); add
[`executor-web-image.md`](../../references/executor-web-image.md) for a placed
`Status: Sourced` image or filename recorded in `image_sources.json`.
Reread only after a known file change or context invalidation.

`executor-structure.md` is loaded once before all SVG authoring so Quick cannot
omit shape-composition reasoning. Reuse it throughout the valid execution
context; reread only after a known file change or context invalidation.

**Mandatory — per-image-page composition decision**: For every page with one
or more images, after its content and communication move are
determined but before choosing geometry, apply
[`executor-image.md`](../../references/executor-image.md)'s active image-integration
decision once. Keep its role, direction source, parent
contour, slot/rhythm system, image/shape action, and any continuity only in
active context; create no artifact, spec, lock, manifest, or extra pass. A
deliberate plain or equal-grid result remains valid when it communicates the
relationship better.

**Mandatory — native formulas**: Quick creates no formula resource or manifest;
retain exact LaTeX in active context, then choose ordinary text, same-paragraph
native inline math, or a standalone native block and author its matching SVG
preview under [`native-formula.md`](../../references/native-formula.md).

**Mandatory — native hyperlinks**: Quick creates no hyperlink resource or
manifest. For every selected link, retain the exact target, choose an inline or
whole-object carrier, and author canonical SVG `<a href>` under
[`native-hyperlinks.md`](../../references/native-hyperlinks.md). Never guess an
unknown destination.

Image to PPTX replaces this open composition decision for its canonical page
frame: preserve the source geometry, restore text natively, preserve
source-graphic identity through the prepared exact or reconstructed asset, and
use the active-context registered layer/plate stack for scene imagery. Run the
ordinary decision only for an additional non-source image whose placement is
not already fixed by that surface.

**Mandatory — per-page Structure decision**: after the current page's content
and communication move are determined, but before choosing any geometry or
shape, decide whether geometry must carry qualitative `order`, `link`, `parent`,
`membership`, `contrast`, or `overlap`. Keep the yes/no result and, when yes,
the relationship meaning and reading path in active context only; create no
artifact, spec, lock, manifest, or extra pass.

- `no` → use Quick's shared base authoring path in this section.
- `yes` → apply the already-loaded Shape Composition Grammar before drawing.

This decision is mandatory on every page and cannot be satisfied by the
capability menu, visualization recall, template geometry, or a later check.

| Deterministic trigger | Additional authority |
|---|---|
| A selected primary Chart/Table `family/key` | [`executor-visualization.md`](../../references/executor-visualization.md), then the matching Chart/Table authority |
| Any actual value-driven geometry, including mini/inset charts and sparklines | [`executor-chart.md`](../../references/executor-chart.md) |
| Any actual row × column fact grid | [`executor-table.md`](../../references/executor-table.md) |
| Any mathematical notation that may require native math | [`native-formula.md`](../../references/native-formula.md) before choosing ordinary text, inline native math, or block native math |
| Any external or same-deck click hyperlink | [`native-hyperlinks.md`](../../references/native-hyperlinks.md) before authoring its inline or whole-object SVG anchor |
| A used preset pattern fill, or one independent Chart/Table object selected as native-ready in active context | [`native-data-interface.md`](../../references/native-data-interface.md) before drawing that object |
| Any data-driven chart geometry | [`verify-charts.md`](../stages/verify-charts.md) after the complete roster and before the one final checker |

Chart/Table reference and final information model are independent loading
signals; load every applicable authority. Selection never makes an object
native-ready or replaces the per-page Structure decision.

Keep the core's shared visual-quality / leading defaults and `svg-effects.md` §6.1 Visual Job Router active while authoring. Explicit user/template requirements and the resolved style override compatible aesthetic defaults, never technical Required / Forbidden boundaries.

**Per-page execution anchors**: apply the transient core-message, typography-role, semantic-color, body-frame, density, and composition anchors resolved in §2 while authoring; they guide the current run without creating a persisted planning artifact.

When `notes/total.md` was frozen from a final script, retain its corresponding
segment while authoring each page. The visible state and real direct-root
semantic groups must support that spoken segment without duplicating the full
script as body copy or changing its wording.

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

**PPTX structure**: author flat, Slide-local SVG only, including when a Layout or
Deck workspace is installed. In that branch, visibly realize the resolved
template rules and prototype geometry in the complete pages; do not fall back to
free design or merely explain how the template could be used. Include the
complete visible page and all resource references in each SVG; set one root
`data-pptx-page-role` from `cover`, `toc`, `section`, `content`, or `ending`,
and omit Master/Layout/layer/placeholder metadata. A request that specifically
requires reusable native Master/Layout/placeholder output is incompatible with
the lockless Quick exporter and must use the default lock-backed profile.

**Typography**: name a concrete target-installed/approved PowerPoint family
under [`shared-standards-core.md`](../../references/shared-standards-core.md)
§4.1; do not depend on a lock or generated font asset.

**Generation pacing**: the current main agent hand-writes the SVG roster in
order. Use P01 as the visual-system calibration baseline and continue
directly through the remaining pages without a first-page checker or
confirmation stop. When a motif was
resolved, reuse it selectively and vary scale, crop, density, position, or
content interaction instead of cloning one ornament. Keep this choice only in
active context; create no planning artifact or approval stop. After every page
exists, run the one final checker below. Apply other supporting tools and
stages only when their capability is actually needed.

**Hard rule — direct page authoring stays with the current main agent**: write
every page SVG directly in the active context. Do not delegate page generation
to another agent, and do not run a Python, Node, shell, or other generator that
writes slide files into `svg_output/`. Documented fragment-only helpers remain
allowed after the current main agent chooses the object's role, operands,
paint, and z-order and integrates the fragment itself. This boundary does not
restrict resource preparation, inspection, checker, verification,
post-processing, or export tools; a run fails this profile only when a delegated
agent or generator authors a page SVG on the main agent's behalf.

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

When Speaker Notes is enabled, load
[`executor-notes.md`](../../references/executor-notes.md) after the passing final
check. Validate an already frozen final script or direct-video pre-SVG narration
without regenerating it; otherwise generate `notes/total.md` from the final SVG
roster. Then run:

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

Run [`customize-animations`](../stages/customize-animations.md) after that notes
pass when the active-context outcome or an existing sidecar triggers it. Resolve
deck-wide-only motion through the selected exporter flags instead.

After visual motion is final, sync a selected cue per
[`animations.md`](../../references/animations.md) §2.2; otherwise create no
`sounds/`. Sidecars never use `templates/sounds/`. This configures the native
PPTX only; `generate-audio` completes direct narrated MP4 delivery with either
the verified native-export mix or an explicitly selected real-time PowerPoint
slideshow capture. Those sound branches are mutually exclusive.

For Quick recorded/self-running/video delivery, complete the mandatory Custom
Animations stage and validate `animations.json` before the base export unless
the user explicitly requested static or page-transition-only playback. Direct
narrated video derives cue timing only when narration governs groups; otherwise
it exports the canonical custom timing without an object-sync claim. Do not
replace this requirement with deck-wide `-a auto` or page transitions.

Choose exactly one notes mode for the base export:

```bash
# Speaker Notes enabled
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> \
  --quick-generate --with-notes

# Speaker Notes disabled
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> \
  --quick-generate --no-notes
```

`--quick-generate` reads `svg_output/` as the page source and resolves the
project-local assets referenced by those SVGs. It infers one consistent canvas,
uses a lockless flat PowerPoint package, and does not force-disable ordinary
export options. Notes, Custom Animations, and narration remain off unless
selected by the agent or required by the Quick video rule above. Do not run
`finalize_svg.py`. After the validated base export, run
[`generate-audio`](../stages/generate-audio.md) when Narration Audio is enabled;
it owns page audio/SRT, narrated PPTX, the optional raw native MP4, and the
final mixed or captured MP4. When a selected manual capture has not yet been
returned, it owns the capture-ready narrated PPTX handoff instead.

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
- [x] Image need was decided independently of credentials; any zero-image deck is backed by an explicit no-image requirement or a roster whose visual burden is fully carried by charts / native SVG
- [x] Every image-bearing page made its one pre-geometry composition decision
- [x] Every image decided its own source from that page's subject and job — not inherited from the resolved visual style — and every externally verifiable subject deliberately not shown as itself was stated with its reason
- [x] Every selected formula uses the checker-valid ordinary/inline/block form with a matching visible SVG preview and no formula image resource
- [x] Every selected hyperlink uses a checker-valid inline/whole-object anchor and an exact external or same-deck target
- [x] Resolved SVG pages and their project-local references exist
- [x] Every role declared by an installed template spec is locatable in the finished pages, or its non-use is deliberate — checked per installed spec, not from memory
- [x] Every triggered capability-specific preparation and pre-checker verification completed
- [x] The lockless final SVG quality report passes and matches the current SVGs
- [x] Enabled notes were validated/generated and split; enabled custom motion ran through its owning stage
- [x] One native PPTX exists under `exports/` or the explicit output path
- [x] No Strategist, confirmation, root project Design Spec, or lock artifact was created
- [ ] **Next**: Report the base PPTX and any enabled narrated PPTX, raw/mixed/captured MP4, or capture-ready PPTX handoff, plus the resolved mode, visual style, and the image sources actually used
```
