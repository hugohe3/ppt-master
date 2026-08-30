---
description: One-pass Generate profile for agent-decided preparation, direct SVG authoring, and final PPTX delivery without durable planning or confirmation artifacts.
---

# Quick Generate Profile

> Generate-PPTX profile, not a top-level route: the current main agent completes one uninterrupted run without a Strategist/confirmation handoff or a resumable design record. It removes interaction and traceability, not the facts, resources, or authoring capabilities the deck needs.

**Trigger**: the user explicitly requests quick/fast generation, asks to skip strategy/confirmation, or directs the agent to proceed to SVG and export. Page count alone never activates or blocks it.

**Hard rule — Quick paths**: expand every linked or abbreviated package path from the entry-time `SKILL_DIR` anchor inside each tool call; never change CWD or inherit a prior working directory.

---

## 1. Profile Boundary

| Concern | Quick Generate contract |
|---|---|
| Authority | Follow every explicit user requirement; decide every unspecified choice directly without asking |
| Interaction | The main agent decides content, design, resources, and implementation without Strategist, Confirm UI, or approval stops; pause only for user interruption or an unresolved hard prerequisite |
| Execution memory | Routine page, visual, and resource decisions live only in the active context; losing it restarts Quick rather than reconstructing a plan from files |
| Inputs | Any supported Generate input; convert/import sources and run bounded research when needed |
| Templates | Validate and install at most one exact workspace root per kind supplied for this run; before P01 inspect the complete installed SVG roster and freeze one Template Application paragraph in context; with no root, free design without catalog selection |
| Resources | Prepare every project-local image, icon, and provenance/manifest artifact before its SVG; author formula markers and hyperlink anchors directly in the SVG; sound waits for §4 |
| Planning artifacts | No root `design_spec.md`, `spec_lock.md`, confirmation payload, or substitute plan; installed `templates/design_spec.<kind>.<id>.md` files stay template input |
| Traceability | Resource manifests, checker reports, postflight, and the bounded command audit may remain; none records design reasoning or forms a resumable history |
| Delivery | Hand-author the roster, run one lockless final checker, skip `finalize_svg.py`, export with `--quick-generate` |

Artifact roles follow [`artifact-ownership.md`](../../references/artifact-ownership.md); Quick changes the planning handoff, not those roles.

**Hard rule — speed removes interaction and durable planning, not capability**: every ordinary source, research, carrier, resource, analysis, authoring, and export capability stays available when it serves the deck — availability, not a requirement to use every carrier. Explicit user facts, wording, choices, exclusions, and permission boundaries still win.

**Default — optional production behavior (may override when useful)**: Speaker Notes, Custom Animations, and narration start off; enable any of them when the request or deck benefits, with their normal inputs and flags and without asking. Quick never creates or reads a root Design Spec or lock to do so.

**Mandatory — discover motion before deciding whether to load it** (once, during §2's pre-P01 planning; keep the defaults when no row supplies a concrete communication job; when several apply, use the earliest load point — a before-authoring signal beats before-export):

| Signal | Action |
|---|---|
| Adjacent beats may share one mental map | Evaluate visible states (repetition alone needs no Morph); if continuity clarifies orientation, enable Custom Animations, load [`animations.md`](../../references/animations.md) before SVG, and author compatible Morph endpoints |
| A page- or object-specific reveal, emphasis, movement, or removal clarifies the message | Load `animations.md` before authoring, preserve the required units/states, run [`customize-animations`](../stages/customize-animations.md) after the final checker |
| One deck-wide entrance policy supplies all staged reveal | Load `animations.md` before export and use an exporter flag such as `-a auto`; no custom stage |
| A directional/section boundary benefits from a non-default transition | Load `animations.md` before export and choose from its §3 playbook |
| No signal | Keep `fade` transitions and object animation `none`; load nothing |

**Hard rule — Quick video Custom Animations**: when [`video-design.md`](../../references/video-design.md) is active (recorded, self-running, or video-directed delivery), enable Custom Animations, load `animations.md` before SVG authoring, preserve the semantic motion units, and run `customize-animations` after the final checker — the table above chooses the choreography, not whether Custom Animations exists, and pages may stay static. A Quick video run without a validated `animations.json` fails unless the user explicitly asked for static or transition-only playback. Narration-governed motion also activates cue synchronization.

---

## 2. Source and Resource Preparation

| Input | Action |
|---|---|
| Topic or requirements without supporting facts | Run [`topic-research`](../stages/topic-research.md) and retain its Markdown supplement plus facts JSON; adopted URLs stay inside the pair and are never import inputs |
| PNG / JPEG / WebP page frames under Image to PPTX | Do not call `source_to_md.py`; normalize single pages and contact sheets into the ordered frame roster through that profile, then import the originals |
| PDF / DOCX / Office / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [...]` (`-t <type>` only when detection is ambiguous; `-o` only for a required output path) |
| CSV / TSV | Read directly as a plain-text table |
| Markdown or conversation text | Read directly |

Apply [`conversion.md`](../../scripts/docs/conversion.md) § Image Orientation Review before import when correction is requested, converted text asks for rotated viewing, or an asset is visibly sideways (skip the legacy HTML tool). After reading every source, research only the gaps where the requested outcome would otherwise require inventing, omitting, or leaving unsupported an externally verifiable claim; an Image to PPTX surface is a closed corpus whose unreadable regions become `manual_required`, and a closed/source-only brief stays within its material. When delivery is recorded, self-running, or video-directed — or a final/literal script will become notes/audio — read `video-design.md` now and retain it through roster, SVG, notes, and motion decisions.

**Template branch** (resolve exactly one before initialization; Image to PPTX always takes free design and installs nothing):

- **Direct template application** — exact workspace roots were supplied, or Create Template returned one in this conversation: at most one root per kind; load [`apply-template-workspace`](../stages/apply-template-workspace.md), normalize each root, read only the frontmatter needed for kind/canvas, and run its read-only preflight. Never scan the library, fuzzy-match a name, or open a selector. Explicit user canvas wins; otherwise the structure owner's canvas (Layout before Deck), passed to `init --format` only when it exactly matches a registered canvas.
- **Free design** — no exact root: continue with the requested canvas, or decide the viewBox during authoring. A bare template name, brand mention, style phrase, or vague request to pick a template is brief input, not a workspace reference.

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --quick-generate
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources \
  <project_path> <source_files_or_dirs...> [<converted_outputs...>] \
  [projects/<research_slug>.md projects/<research_slug>.facts.json]
```

**Hard rule — truthful canvas token**: `--format <registered_format>` only for an exactly resolved registered canvas; otherwise the first SVG's viewBox is the canvas authority, and custom dimensions are never encoded as a token. Neither branch touches `confirm_ui/`. `init` creates `svg_output/` and the cold `validation/workflow.log` (auto-recorded by later tools; one manual note only for a material handoff, rework reason, approved exception, or manual recovery; never read during a run and never a resume source). Use a new path or one whose `svg_output/` is empty; Quick ignores any existing Design Spec or lock and never scaffolds one.

**✅ Checkpoint — every named input landed**: `import-sources` exits 0 when one input succeeds; read the printed `skipped` reasons — "equivalent content exists" is benign, `path not found`, failed conversion, or no usable Markdown means the source is absent: re-import, supply a converted equivalent, or state why the deck proceeds without it. Pass a source once when Markdown sits beside it, both locations when `-o` wrote elsewhere; `projects/`-local inputs move (`--copy` keeps them), external paths are copied. Bitmaps are archived under `sources/` and copied into `images/`; EMF/WMF stay vector references (never PNG; blank in browser preview is expected); each PPTX yields `analysis/<stem>.identity.json`, `<stem>.slide_library.json`, and the `source_profile.json` index — source facts, not replica constraints. The facts JSON is the sole URL authority: only after web-image search is exhausted may a webpage package be fetched under [`topic-research`](../stages/topic-research.md) § Hand-off and its accepted images copied in. Under Image to PPTX, the normalized frame roster is canonical input and the agent writes `analysis/reconstruction_inventory.json` before deciding layers.

**Installed templates**: run `apply-template-workspace` against the preflighted roots only; the request is the selection authority, with no receipt or handoff, and every later read uses the installed state. Before P01 read each installed spec once and, for Layout/Deck, every SVG prototype; apply Brand identity, Style direction, the structure owner's prototype geometry, and Deck context under the stage's §5 segment precedence — an owner's instruction on how a value dominates, recedes, or stays rare binds as strongly as the value, and a Style tendency never demotes a Brand's dominant color. Freeze one **Template Application** paragraph in context: explicit user instructions first, otherwise the fit of the content to the complete roster, defaulting to reference-led use (redesign after full-roster study; other readings such as augment-only or replacement-only are examples, not a menu). It names which prototypes may be used, skipped, repeated, reordered, or adapted, what stays fixed, and any exception by exact SVG basename; when a detail is later uncertain, reread the installed SVG.

Read the planning-capability batch in one pass — a capability map, not a usage checklist:

```
Read ${SKILL_DIR}/references/canvas-formats.md
Read ${SKILL_DIR}/references/modes/_index.md
Read ${SKILL_DIR}/references/visual-styles/_index.md
Read ${SKILL_DIR}/references/image-renderings/_index.md
Read ${SKILL_DIR}/templates/icons/README.md
Read ${SKILL_DIR}/templates/charts/chart-vocabulary.md
Read ${SKILL_DIR}/templates/tables/table-vocabulary.md
```

Resolve one whole solution directly (never Default's three candidates): the strongest fit to the brief, or with a template the solution that most fully expresses the installed context and frozen Template Application. Freeze its mode/style/rendering ids, read only those detail files or exact custom bases (a novel custom reads none; never open unselected siblings), decide AI-image usefulness as a separate source judgment while keeping the rendering direction for coherence, and keep everything in active context only — no strategy summary, checkpoint, or persisted plan.

**Pre-P01 resolution** (apply the §1 motion gate here; freeze the roster after the rhythm check):

- Narrative beats, mental-map arcs, candidate visible states and their deltas, and enabled notes segments; adopt continuity only when it clarifies, and never alter profile-fixed count/order/content to manufacture endpoints.
- Effective Speaker Notes, Custom Animations, and Narration Audio: narration requires notes; later recording alone forces neither audio nor object animation; recorded/self-running/video delivery follows `video-design.md` and enables Custom Animations before authoring; direct narrated video also decides before audio whether narration governs group timing.
- The exact slide roster with one compact core message per page.
- Canvas, visual direction, wording, viewing distance, and reading mode (`presentation` for distance-first projected or recorded viewing, `balanced` for mixed, `text` for close content-heavy reading). Take the initial body anchor and sanity band from [`canvas-formats.md`](../../references/canvas-formats.md) § Typography Scale Start, then resolve one typography plan for the delivery target of [`shared-standards-core.md`](../../references/shared-standards-core.md) §4.1 — never the authoring host's fonts — with stable anchors for title, body, annotation, and every recurring role. When content does not fit, restructure, shorten, or split within the invariants; if none is permitted, surface the fit rather than shrinking a recurring role.
- The semantic color roles the roster needs (background/surface, primary/secondary text, dominant/accent, status), each with a concrete anchor: honor user, template/brand, fidelity, and resolved-style semantics before deriving the missing roles; decide which dominate, support, or stay rare; keep meaning-bearing text legible; pair any newly authored color-coded distinction with a label, symbol, line, or geometry cue.
- A body-content frame and a density judgment per page (`anchor`, `dense`, `breathing`) rather than one uniform fill.
- For each page, its semantic units and their source-stated relationship (`order` / `link` / `parent` / `membership` / `contrast` / `overlap`, or none), entry, and outcome — the input to §3's Structure decision; zones, geometry, and carriers are §3 authoring decisions.
- The deck-level shape language under [`visual-styles/_index.md`](../../references/visual-styles/_index.md) §2, and, when it earns a continuity job, one transient motif system with an invariant and a reuse mode (fixed chrome, adaptive variation, or both); restraint governs weight and recurrence, never the omission of an evidenced identity or communication motif.
- Resource decisions for immediate preparation: manifests may carry filenames, page relationship, status, and generation/crop/focal cues (plus subject/quiet zones, boundary, seam, and share when composition depends on them); no general roster or icon-to-page assignment; each formula's LaTeX and each hyperlink's exact target kept in context, with no manifest. An explicit user implementation path wins; otherwise the registered default.

**Mandatory — whole-roster rhythm check**: compare neighbors and section arcs — chapter entries visibly reset, same-density, same-resource, or same-relationship runs are intentional page-job arcs, a repeated motif carries a continuity job, each section follows a mode-fitting progression (including framework → explanation/evidence → judgment/action when it serves), and the final arc resolves the objective before a genuine ending lowers load. Same section, equal density, one style, and precedent establish no arc. Repair the transient roster in place; preserve intentional continuity, legitimately all-`dense` material, and 1:1 order; add no filler — a `breathing` page marks a real pause. No artifact or second pass.

**Prepared final narration**: an explicit final/literal script for notes or audio is segmented by scene while resolving the roster, every word preserved, and written once before P01 to `notes/total.md` (`# Slide <number>` headings, `---` separators) as production input, split only after the roster exists. Draft narration stays source material for the ordinary notes branch.

**Default — resource need per page (may stay implicit when a page's need is obvious)**: before resources, decide which pages need a prepared image, lettering, or illustrated-icon resource — the jobs only a prepared file can serve; SVG/emoji icons keep their curated-pool boundary. The page's carrier mix itself — background, text, native geometry, imagery, icons, visualizations and their weights — is §3's authoring decision, not a preparation decision. The resolved style controls treatment and recurrence but never eligibility, source, or the native vocabulary, and a compact icon cue does not discharge a scene, subject, or visual-weight job a photo or illustration family would serve.

| Communication job | Prepared resource or information model |
|---|---|
| Real subject, place, product, evidence, atmosphere, or scene benefits from visual grounding | Supplied/extracted, web, AI, or sliced image |
| Reusable title/corner decoration, a dominant illustrated anchor, supporting figure, or accent strengthens compositions | A coherent AI illustration family as transparent `slice` assets, combined freely with other carriers |
| A compact semantic cue clarifies a category, process, KPI, state, or navigation item | Prepared project-local SVG/emoji icon, an illustrated-icon `slice`, or both |
| A real company, product, service, or social brand must appear as itself | The exact mark from `simple-icons` or supplied assets; not a user-facing library choice |
| Values, categories, time, weights, or duration determine mark geometry | Value-driven chart |
| Sequence, hierarchy, role, region, or relationship determines topology | Qualitative structure |
| Rows, columns, cells, headers, merges, alignment form the model | Cell-grid table |
| A stable display string reads better with a material, dimensional, hand-rendered, or illustrative treatment | Decorative lettering per the rule below, as an image beside a native title |

This menu never satisfies the per-page Structure decision in §3.

**Hard rule — credentials never decide image need**: plan carriers without inspecting backend configuration or probing a provider; web search keeps zero-config providers, and AI capability is resolved during preparation, where the no-AI replan owns exhaustion.

**Default — visual grounding before a zero-image deck (may override when the full-roster review finds no image job)**: honor an explicit no-image requirement; otherwise, when the audience must recognize, experience, compare, or choose an externally verifiable subject, plan supplied/extracted or web images, and prepare AI imagery — a complete image or transparent elements — where invented or stylized expression materially improves a visual job. A semantic decision, not a quota.

**Mandatory — illustration families and illustrated icons**: when the resource-need review selects a composable family, resolve it before authoring — elements may repeat as title/corner chrome or vary as anchors, figures, and accents on any page — batching compatible elements through Illustration Sheets under [`image-generator.md`](../../references/image-generator.md) §4.3 and splitting only for geometry, detail, or quality conflicts. When it selects illustrated-icon cues and AI is not forbidden, prepare them as transparent slices under `images/`; grouping, count, and coexistence with SVG icons follow page fit, with no quota and never as SVG inventory.

**Reference — decorative-lettering candidates**: when AI is not forbidden, any display string in the frozen roster is a candidate on two questions — is the wording stable, and could an artistic treatment communicate better than native type? Page role, length, line count, kind of noun, and resolved style never pre-filter: a cover hook, chapter word, place or product name, dish or exhibit name, year, hero number, pull quote, or motif word all qualify, a two-character mark and a two-line lockup equally, and a phrase is never trimmed to feel more "wordmark-like"; type over photography or a busy field is often exactly where native text reads pasted-on. Compare candidates inside the whole page and deck mix and select any coherent set whose treatment wins; selecting none is valid without explanation. For each selected mark keep a native title wherever the page needs a searchable, selectable, or outline-visible heading — the lettering is the display layer, the editable wish is answered by the native layer. Prepare the set without a separate request: exact approved strings, one ordinary AI item or grouped Illustration Sheets with transparent slices, grouped by character and treatment, with role, placement/background relationship, weight, and energy given to the model under `image-generator.md` §5.3's controlled-default/high-expression boundary; chrome and body stay native. Never invent or alter copy or create lettering to justify AI.

**Mandatory — per-image source decision**: outside Image to PPTX, decide each page image's source separately — supplied/extracted when it carries authority, web when an externally verifiable subject must appear as itself, AI when invented or stylized expression matters more than documentary identity; mixed sources are normal. A visual style, `Illus.` propensity, or rendering resolves how imagery looks, never its source: a named place, building, product, artwork, or person stays a web/supplied candidate however illustrative the deck, and a subject deliberately not shown as itself is stated with its reason in the final report.

**Mandatory — image treatment and subject layers**: choose per image: `none`; a native SVG treatment (crop viewport, opacity, frame, scrim, shadow); or a prepared derivative. A subject that crosses native content requires a clean full-canvas base plus a registered RGBA cutout (`#A2-03`). A prepared derivative never overwrites its source, never becomes another derivative's parent, never has its output equal its input, and is derived only after that source is itself final. Where fidelity forbids adding a label, symbol, line, or geometry cue to a new color encoding, preserve the source encoding instead.

**Reference — Chart/Table vocabularies**: the loaded vocabularies list what exists; they rank nothing and are neither quota nor whitelist. Choose at most one primary `family/key` per page (never for qualitative composition), validate it with `visualization_recall.py validate`, keep its purpose in context — the reference stays flexible and locks neither final type, geometry, style, nor native output — and retain `no-template-match` when none fits; describe embedded children and qualitative relationships in the page decision. Give every independent Chart/Table a page-local `kebab-case` key with its `<object-key>=yes|no` native-ready decision and any promoted chart-verification status in context; qualitative relationships create no key or reusable structure.

**Resource preparation** (only what the decided pages need):

| Resource | Preparation |
|---|---|
| Supplied/extracted image | Copy the selected file into `images/`; keep its provenance; use the measured file |
| Image-to-PPTX reconstruction asset | In Codex, preserve identity graphics through an exact vector, deterministic redraw, sufficient source asset, or reference-based high-resolution reconstruction; keep data graphics native-and-verified or exact; build the minimum registered clean-base/midground/subject/foreground group for scene imagery, batching padded-bbox-disjoint objects into one shared plate split by grid slicing or nested-SVG crops |
| Bundled/custom/brand SVG icon | [Icon library contract](../../templates/icons/README.md): one primary generic library per pool (`icon_sync.py` rejects mixed batches), synced without page assignment; `simple-icons` for named brands |
| Formula | No resource file; keep the LaTeX and choose text, inline marker, or block marker in §3 |
| AI image | `image-base.md` + `image-generator.md`; only the chosen rendering preset or exact custom bases; `image_prompts.json` plus its readable sidecar |
| Web image | `image-base.md` + `image-searcher.md`; query/status data and `image_sources.json` with any required on-slide attribution |
| Illustration / illustrated-icon / lettering slice | Obtain the parent sheet, run `slice_images.py --trim --alpha --bg KEY_HEX_FROM_PROMPT --strict-alpha`, place only outputs of a successful strict cut; slices stay under `images/` and may serve several pages; a lettering sheet names every exact string |
| Registered reconstruction group | `image-generator.md` §4.4: full-canvas members `crop=no-crop`, every shared-plate member an independent picture |
| Visualization | Keep values, cell topology, and treatment in context; load the Chart/Table authority in §3 and write native replacement metadata for every supported chart and pure text grid (native-ready by default) |

**Hard rule — planned slice closure**: every sheet carries `slice_grid` and `slice_names` in `image_prompts.json`; every `images/<name>.png` must exist after an exit-0 `--strict-alpha` run before authoring — a `Generated` parent never satisfies its outputs. A nonzero slice run returns the parent to preparation: correct only an evidenced key/tolerance mismatch, otherwise enlarge cells or split incompatible families and regenerate; repeating the same failing grid is not recovery. An explicit manual path sets the item `Needs-Manual` with `last_error` and blocks SVG/export until every output is supplied and validated; exhausted automation follows the no-AI replan instead.

**Quick exhausted-automation no-AI replan** ([`image-generator.md`](../../references/image-generator.md) §7): when an automated AI path or its dependent slicing is exhausted, ask no path question and enter no manual fallback — remove the affected AI jobs and stale manifest entries, carry their communication content with native text/SVG or prepared non-AI assets, and continue; retaining AI imagery means repairing capability and starting a new Quick run.

**Validation before §3**: every file-backed resource is terminal — `Existing`, `Generated`, or `Sourced` under [`svg-image-embedding.md`](../../references/svg-image-embedding.md) — and every `slice_names` basename resolves to its PNG; a missing name resumes its owning step and is never deferred to the checker. Web `Needs-Selection` blocks until a thumbnail is promoted or the bounded ranked pages and materially different variants are exhausted, after which a vision-capable owner may fetch one adopted-page package; `Needs-Manual` blocks even with an unverified file; without vision only the strict metadata-ranked path reaches `Sourced`, and its provenance says so. Never bypass status by preview or presence, never substitute unrelated material. Acquisition-time review follows the owning reference; authoring inspects only one ambiguous `Existing`/`Sourced` asset under `executor-image.md` and never reopens `Generated` outputs (Image to PPTX inspects every normalized page and generated layer once, then the final recomposition). After resources change, run `analyze_images.py`; manifests and provenance are resource truth, not a design strategy.

---

## 3. Direct SVG Authoring

Read the execution core together, never file by file: [`shared-standards-core.md`](../../references/shared-standards-core.md), [`executor-base.md`](../../references/executor-base.md), [`semantic-svg.md`](../../references/semantic-svg.md), and [`preset-shape-vocabulary.md`](../../references/preset-shape-vocabulary.md) (complete, before P01); then evaluate `executor-base.md`'s routing triggers once over the frozen roster before P01 and read every triggered module in the same batch — [`executor-structure.md`](../../references/executor-structure.md) + [`topology-assembly.md`](../../references/topology-assembly.md) for any `Structure = yes` page, [`native-shape-authoring.md`](../../references/native-shape-authoring.md) for any contour beyond basic primitives, [`svg-effects.md`](../../references/svg-effects.md) for any visual job beyond the everyday block — each recorded in the module line of the pages that use it; a page that reaches a capability the sweep did not foresee reads its module at that moment, before its first SVG line; installed Layout/Deck structure adds [`pptx-structure-interface.md`](../../references/pptx-structure-interface.md). Keep the selected mode/style files: a custom applies one basis under its behavior, synthesizes several by their contributions, or follows the behavior alone. When any image exists, read the complete `Any image` row of `executor-base.md`'s routing table — [`executor-image.md`](../../references/executor-image.md), [`image-layout-spec.md`](../../references/image-layout-spec.md), [`image-layout-patterns.md`](../../references/image-layout-patterns.md), and [`svg-image-embedding.md`](../../references/svg-image-embedding.md) — once before the first affected page (plus [`executor-web-image.md`](../../references/executor-web-image.md) for a `Sourced` image); reread anything only after a known file change or context invalidation.

`executor-base.md` binds Quick exactly as it binds Default except its `Default only` items — the persisted-plan handoff in §2 / §2.1 and the export hand-off in §6 — which Quick's transient §2 anchors, single final checker, and export below own; the Default gate cadence lives in `generate-pptx.md` Step 6 and does not apply. Conditional authorities load on its routing table (Chart/Table branches, native data, formula, hyperlink); Chart/Table reference and final information model are independent signals, and selection never makes an object native-ready. Explicit user/template requirements and the resolved style override compatible aesthetic defaults, never technical boundaries, carrier eligibility, or native capability discovery.

**Mandatory — per-image-page composition**: for every page with images, after content and communication move but before geometry, apply `executor-image.md`'s image-integration decision once, keeping role, direction source, parent contour, slot/rhythm system, image/shape action, and continuity in context only; a deliberate plain or equal-grid result is valid when it communicates better. Image to PPTX replaces this and the page-geometry decision for its canonical frame: preserve source geometry, restore text natively, keep source-graphic identity through the prepared asset, and use the registered layer/plate stack; run the ordinary decisions only for additional non-source content.

**Mandatory — native formulas and hyperlinks**: no resource or manifest for either. Keep the exact LaTeX and choose ordinary text, same-paragraph inline math, or a standalone block with its SVG preview under [`native-formula.md`](../../references/native-formula.md); keep each link's exact target, choose an inline or whole-object carrier, and author canonical `<a href>` under [`native-hyperlinks.md`](../../references/native-hyperlinks.md), never guessing a destination.

**Mandatory — per-page Structure decision and geometry move**: after the page's content and communication move, before any geometry, decide whether geometry must carry `order`, `link`, `parent`, `membership`, `contrast`, or `overlap` (`executor-base.md` §2.1) — `no` stays on the base path, `yes` loads and applies the Shape Composition Grammar and topology assembly. Then, when the page's geometry reaches beyond basic primitives, load and apply [`native-shape-authoring.md`](../../references/native-shape-authoring.md) §2.1 to the transient geometry job, content, deck shape language, resolved style, and full vocabulary before coordinates (`describe --compact` only when objective facts could change a serious candidate). Both decisions stay in context, and the capability menu, visualization recall, and template geometry never stand in for them. Quick runs [`verify-charts.md`](../stages/verify-charts.md) after the roster and before the final checker whenever data-driven chart geometry exists.

**Per-page anchors**: apply the core-message, typography-role, color, body-frame, density, and composition anchors from §2 while authoring; when `notes/total.md` was frozen, keep each page's segment in view so its visible state and direct-root groups support the spoken words without copying the script into body text.

**Canvas**: the §2 canvas — explicit user choice, otherwise the Layout/Deck owner's, otherwise `ppt169` `viewBox="0 0 1280 720"`; another registered format takes its exact viewBox from `canvas-formats.md`. Template canvas is a default, not a gate. The first SVG fixes the export canvas; every page matches it exactly. Filenames use one zero-padded width for the roster (`01_cover.svg` … `12_end.svg`, or three digits); never leave pages from another run in `svg_output/` — the exporter publishes everything it finds.

**PPTX structure**: speed never flattens template structure. Free design and Brand/Style-only author flat Slide-local SVG with one root `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`) and no Master/Layout/layer/placeholder metadata. When Layout or Deck owns structure, every page is a complete structured Slide SVG that preserves or deliberately adapts the prototype's root identity, fixed layers, and slots with current content on top — all-or-none across the roster, every reused Layout repeating an identical fixed-layer/slot contract, a new Layout allowed under the selected Master when the application paragraph calls for adaptation, ownership never inferred from repeated geometry, and `data-pptx-page-role` omitted. A Style never strips structure; only an explicit instruction to use the workspace as visual language permits flat output.

**Typography**: name a concrete target-installed/approved family under `shared-standards-core.md` §4.1, never a lock or the host's fonts. Before P01 run `python3 ${SKILL_DIR}/scripts/text_measure.py calibrate <project_path> --role <name>:<family>:<size>` for every recurring role (one command, repeatable `--role`) and keep its table — CJK and Latin ≈ chars per 100 px per role, the checker's own estimator with wrapping headroom — in context; every later page sizes zones from that per-font arithmetic — write the sentence first, fit the zone to it, and never trim wording to satisfy an estimate; calibrate again only for a role or size never calibrated, and `wrap` only a genuinely long paragraph.

**Generation pacing**: hand-write the roster in order — P01 calibrates visual identity and cover expression, the first ordinary content page calibrates content geometry and carrier integration, neither becomes a reusable template — with no first-page checker or confirmation stop. A resolved motif follows its reuse mode (exact repetition for deliberate chrome, adaptive variation of scale, crop, density, position, or interaction otherwise). After every page exists, run the one final checker below; use other stages only when their capability is needed.

**Hard rule — direct page authoring stays with the main agent**: write every page SVG in the active context; never delegate page generation or run a generator that writes slide files (fragment-only helpers remain allowed after the agent chooses role, operands, paint, and z-order). Resource, inspection, checker, verification, and export tools are unrestricted. This is not a resume protocol: if the context is lost before delivery, start a clean Quick run.

---

## 4. Export

After every page and referenced resource exists, run the Quick branch of [`verify-charts`](../stages/verify-charts.md) when any data-driven chart was authored and complete its repairs, then prove canonical compact authoring with the one lockless final check; fix every blocking error and rerun the same command:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --quick-generate --canonical-authoring --stage final --json
```

**Mandatory — final carrier-receipt review**: compare the `[CARRIERS]` summary with the retained page jobs, deck shape language, motif, resource roles, and geometry signatures. Counts are not quotas; when the facts contradict an active decision — an adopted preset absent, a directional / step / flowchart relationship drawn as a hand path or polygon where `executor-base.md` §3.0 names a preset, a primary image reduced to a minor frame — read only the affected `files[].info.carrier_receipt` rows, repair those pages in one pass, and rerun the checker. **Absence needs a reason**: when the receipt shows a deck-wide zero — `Presets: (none)`, or `inline emphasis 0`, `gradients 0`, or `filters 0` on the `Effects:` line — or fewer pages carrying a preset or connector than pages whose transient relationship statement names `order` / `link` / `parent` / `membership`, answer one line per absent family or per such page: what carries that job instead, and why it serves the reader better — for presets, one line per job the family serves, not for arrows alone: direction and sequence (arrows, chevrons, flow nodes), grouping and ownership (brackets, braces, frames, plaques), emphasis and annotation (callouts, badges, banners, stars). The style, speed, restraint, "text was enough", or "it is editable anyway" are not answers; a family or page without one is repaired where the page job calls for it, then the checker reruns. Choosing not to use a device is valid — only an unstated reason is not.

**Notes** (when enabled): load [`executor-notes.md`](../../references/executor-notes.md) after the passing check, validate a frozen script or pre-SVG narration without regenerating it or otherwise generate `notes/total.md` from the final roster, then split:

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Success criterion**: per-slide files under `notes/` cover every published slide; the command exits non-zero on a missing slide or failed write — repair and rerun, and never let leftover files satisfy it.

**Motion and sound**: run [`customize-animations`](../stages/customize-animations.md) after the notes pass when the §1 outcome or an existing sidecar triggers it; deck-wide-only motion uses exporter flags. Quick video delivery completes the Custom Animations stage and validates `animations.json` before export unless the user asked for static or transition-only playback; direct narrated video derives cue timing only when narration governs groups. After motion is final, sync a selected cue per [`animations.md`](../../references/animations.md) §2.2 (no cue → no `sounds/`; never `templates/sounds/`); `generate-audio` completes narrated MP4 delivery through the verified native mix or an explicit slideshow capture, never both.

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate --with-notes   # Speaker Notes enabled
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate --no-notes     # Speaker Notes disabled
```

`--quick-generate` reads `svg_output/`, resolves project-local assets, infers one canvas and one all-page structure mode (no metadata → flat; complete Master/Layout/slot metadata → structured), and needs no lock. Notes, Custom Animations, and narration stay off unless the agent enabled them or the video rule requires them; append `--native-charts-and-tables` only for an explicit native Chart/Table delivery decision. Never run `finalize_svg.py`. The exporter requires a passing `final` report whose fingerprint matches the current `svg_output/`; the default output path keeps backup and postflight, an explicit `-o <path>.pptx` skips backup. On failure repair the owning SVG, resource, or capability input, rerun the checker, and export again — never create a Design Spec or lock. When Narration Audio is enabled, run [`generate-audio`](../stages/generate-audio.md) after the validated export (page audio/SRT, narrated PPTX, optional raw MP4, final mixed or captured MP4, or the capture-ready handoff).

```markdown
## ✅ Quick Generate Complete

- [x] Source/resource preparation complete; the planning-capability batch and every selected detail source were read before the roster
- [x] The complete preset vocabulary was read before P01; each page resolved its Structure decision, geometry move, and carrier mix without a quota and compared its geometry signature before the next page
- [x] Image need was decided independently of credentials; every image decided its own source, every `slice_names` output exists after an exit-0 strict-alpha run, and every exhausted AI job was replanned under the no-AI rule with its disclosure retained
- [x] Every selected formula and hyperlink uses its checker-valid native form
- [x] The frozen Template Application paragraph was applied, every installed Layout/Deck SVG was read, and structure matches the installed capability (flat vs explicit all-page structured)
- [x] The carrier receipt was compared with the retained page jobs and contradictions repaired; the lockless final report passes and matches the current SVGs
- [x] Enabled notes were validated/generated and split; enabled custom motion ran through its owning stage
- [x] One native PPTX exists under `exports/` or the explicit output path; no Strategist, confirmation, root Design Spec, or lock artifact was created
- [ ] **Next**: report the base PPTX and any narrated PPTX, MP4, or capture-ready handoff, plus the resolved mode, visual style, and image sources actually used; for every no-AI replan, report the affected job, attempted path, concrete error, replacement carrier, and that retaining AI imagery requires repairing generation capability and a new Quick run
```
