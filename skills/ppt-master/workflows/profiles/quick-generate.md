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
| Delivery | Hand-author the roster, run the §3 early gate on rosters of seven or more pages plus one lockless final checker, skip `finalize_svg.py`, export with `--quick-generate` |

Artifact roles follow [`artifact-ownership.md`](../../references/artifact-ownership.md); Quick changes the planning handoff, not those roles.

**Hard rule — speed removes interaction and durable planning, not capability**: every ordinary source, research, carrier, resource, analysis, authoring, and export capability stays available when it serves the deck — availability, not a requirement to use every carrier. Explicit user facts, wording, choices, exclusions, and permission boundaries still win.

**Default — optional production behavior (may override when useful)**: Speaker Notes, Custom Animations, and narration start off. Enable any of them when the request or deck benefits, with their normal inputs and flags and without asking. Quick never creates or reads a root Design Spec or lock to do so.

**Mandatory — discover motion before deciding whether to load it**: once, during §2's pre-P01 planning. Keep the defaults when no row supplies a concrete communication job. When several rows apply, use the earliest load point — a before-authoring signal beats before-export.

| Signal | Action |
|---|---|
| Adjacent beats may share one mental map | Evaluate visible states (repetition alone needs no Morph); if continuity clarifies orientation, enable Custom Animations, load [`animations.md`](../../references/animations.md) before SVG, and author compatible Morph endpoints |
| A page- or object-specific reveal, emphasis, movement, or removal clarifies the message | Load `animations.md` before authoring, preserve the required units/states, run [`customize-animations`](../stages/customize-animations.md) after the final checker |
| One deck-wide entrance policy supplies all staged reveal | Load `animations.md` before export and use an exporter flag such as `-a auto`; no custom stage |
| A directional/section boundary benefits from a non-default transition | Load `animations.md` before export and choose from its §3 playbook |
| No signal | Keep `fade` transitions and object animation `none`; load nothing |

**Hard rule — Quick video Custom Animations**: when [`video-design.md`](../../references/video-design.md) is active (recorded, self-running, or video-directed delivery), enable Custom Animations, load `animations.md` before SVG authoring, preserve the semantic motion units, and run `customize-animations` after the final checker. The table above chooses the choreography, not whether Custom Animations exists; pages may stay static. A Quick video run without a validated `animations.json` fails unless the user explicitly asked for static or transition-only playback. Narration-governed motion also activates cue synchronization.

---

## 2. Source and Resource Preparation

| Input | Action |
|---|---|
| Topic or requirements without supporting facts | Run [`topic-research`](../stages/topic-research.md) and retain its Markdown supplement plus facts JSON; adopted URLs stay inside the pair and are never import inputs |
| PNG / JPEG / WebP page frames under Image to PPTX | Do not call `source_to_md.py`; normalize single pages and contact sheets into the ordered frame roster through that profile, then import the originals |
| PDF / DOCX / Office / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [...]` (`-t <type>` only when detection is ambiguous; `-o` only for a required output path) |
| CSV / TSV | Read directly as a plain-text table |
| Markdown or conversation text | Read directly |

**Orientation review**: apply [`conversion.md`](../../scripts/docs/conversion.md) § Image Orientation Review before import when correction is requested, converted text asks for rotated viewing, or an asset is visibly sideways (skip the legacy HTML tool).

**Research scope**: after reading every source, research only the gaps where the requested outcome would otherwise require inventing, omitting, or leaving unsupported an externally verifiable claim. An Image to PPTX surface is a closed corpus whose unreadable regions become `manual_required`; a closed/source-only brief stays within its material.

**Video delivery**: when delivery is recorded, self-running, or video-directed — or a final/literal script will become notes/audio — read `video-design.md` now and retain it through roster, SVG, notes, and motion decisions.

**Template branch** (resolve exactly one before initialization; Image to PPTX always takes free design and installs nothing):

| Branch | Rule |
|---|---|
| **Direct template application** — exact workspace roots were supplied, or Create Template returned one in this conversation | At most one root per kind. Load [`apply-template-workspace`](../stages/apply-template-workspace.md), normalize each root, read only the frontmatter needed for kind/canvas, and run its read-only preflight. Never scan the library, fuzzy-match a name, or open a selector. Explicit user canvas wins; otherwise the structure owner's canvas (Layout before Deck), passed to `init --format` only when it exactly matches a registered canvas. |
| **Free design** — no exact root | Continue with the requested canvas, or decide the viewBox during authoring. A bare template name, brand mention, style phrase, or vague request to pick a template is brief input, not a workspace reference. |

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --quick-generate
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources \
  <project_path> <source_files_or_dirs...> [<converted_outputs...>] \
  [projects/<research_slug>.md projects/<research_slug>.facts.json]
```

**Hard rule — truthful canvas token**: `--format <registered_format>` only for an exactly resolved registered canvas; otherwise the first SVG's viewBox is the canvas authority, and custom dimensions are never encoded as a token. Neither branch touches `confirm_ui/`.

**Project state**: `init` creates `svg_output/` and the cold `validation/workflow.log` (auto-recorded by later tools; one manual note only for a material handoff, rework reason, approved exception, or manual recovery; never read during a run and never a resume source). Use a new path or one whose `svg_output/` is empty. Quick ignores any existing Design Spec or lock and never scaffolds one.

**✅ Checkpoint — every named input landed**: `import-sources` exits 0 when one input succeeds; read the printed `skipped` reasons. "equivalent content exists" is benign; `path not found`, failed conversion, or no usable Markdown means the source is absent: re-import, supply a converted equivalent, or state why the deck proceeds without it. Pass a source once when Markdown sits beside it, both locations when `-o` wrote elsewhere. Copy/move semantics, bitmap archiving, EMF/WMF handling (never PNG), and the PPTX intake bundle under `analysis/` are [`project.md`](../../scripts/docs/project.md) — source facts, not replica constraints.

**URL authority**: the facts JSON is the sole URL authority; only after web-image search is exhausted may a webpage package be fetched under [`topic-research`](../stages/topic-research.md) § Hand-off and its accepted images copied in. Under Image to PPTX, the normalized frame roster is canonical input and the agent writes `analysis/reconstruction_inventory.json` before deciding layers.

**Installed templates**: run `apply-template-workspace` against the preflighted roots only; the request is the selection authority, with no receipt or handoff, and every later read uses the installed state. Before P01 read each installed spec once and, for Layout/Deck, every SVG prototype. Apply Brand identity, Style direction, the structure owner's prototype geometry, and Deck context under the stage's §5 segment precedence: an owner's instruction on how a value dominates, recedes, or stays rare binds as strongly as the value, and a Style tendency never demotes a Brand's dominant color.

**Template Application paragraph**: freeze one in context — explicit user instructions first, otherwise the fit of the content to the complete roster, defaulting to reference-led use (redesign after full-roster study; other readings such as augment-only or replacement-only are examples, not a menu). It names which prototypes may be used, skipped, repeated, reordered, or adapted, what stays fixed, and any exception by exact SVG basename. When a detail is later uncertain, reread the installed SVG.

Read the planning-capability batch in one pass — a capability map, not a usage checklist:

```
Read ${SKILL_DIR}/references/plan-core.md
Read ${SKILL_DIR}/references/canvas-formats.md
Read ${SKILL_DIR}/references/modes/_index.md
Read ${SKILL_DIR}/references/visual-styles/_index.md
Read ${SKILL_DIR}/references/image-renderings/_index.md
Read ${SKILL_DIR}/templates/icons/README.md
Read ${SKILL_DIR}/templates/charts/chart-vocabulary.md
Read ${SKILL_DIR}/templates/tables/table-vocabulary.md
```

**One whole solution**: resolve it directly (never Default's three candidates): the strongest fit to the brief, or with a template the solution that most fully expresses the installed context and frozen Template Application. Freeze its mode/style/rendering ids and read only those detail files or exact custom bases (a novel custom reads none; never open unselected siblings). Decide AI-image usefulness as a separate source judgment while keeping the rendering direction for coherence. Keep everything in active context only — no strategy summary, checkpoint, or persisted plan.

**Pre-P01 resolution** (apply the §1 motion gate here; freeze the roster after the rhythm check):

- **Beats and states**: narrative beats, mental-map arcs, candidate visible states and their deltas, and enabled notes segments; adopt continuity only when it clarifies, and never alter profile-fixed count/order/content to manufacture endpoints.
- **Production outcomes**: effective Speaker Notes, Custom Animations, and Narration Audio. Narration requires notes; later recording alone forces neither audio nor object animation; recorded/self-running/video delivery follows `video-design.md` and enables Custom Animations before authoring; direct narrated video also decides before audio whether narration governs group timing.
- **Roster**: the exact slide roster with one compact core message per page.
- **Reading and typography**: canvas, visual direction, wording, viewing distance, and reading mode (`presentation` for distance-first projected or recorded viewing, `balanced` for mixed, `text` for close content-heavy reading). Take the initial body anchor and sanity band from [`canvas-formats.md`](../../references/canvas-formats.md) § Typography Scale Start, then resolve one typography plan for the delivery target of [`shared-standards-core.md`](../../references/shared-standards-core.md) §4.1 — never the authoring host's fonts — with stable anchors for title, body, annotation, and every recurring role. When content does not fit, restructure, shorten, or split within the invariants; if none is permitted, surface the fit rather than shrinking a recurring role.
- **Color roles**: the semantic color roles the roster needs (background/surface, primary/secondary text, dominant/accent, status), each with a concrete anchor. Honor user, template/brand, fidelity, and resolved-style semantics before deriving the missing roles; decide which dominate, support, or stay rare; keep meaning-bearing text legible; pair any newly authored color-coded distinction with a label, symbol, line, or geometry cue.
- **Density**: a body-content frame and a density judgment per page (`anchor`, `dense`, `breathing`) rather than one uniform fill.
- **Relationships**: for each page, its semantic units and their source-stated relationship (`order` / `link` / `parent` / `membership` / `contrast` / `overlap`, or none), entry, and outcome — the input to §3's topology decision; zones, geometry, and carriers are §3 authoring decisions.
- **Shape language and motif**: the deck-level shape language under [`visual-styles/_index.md`](../../references/visual-styles/_index.md) §2, and, when it earns a continuity job, one transient motif system with an invariant and a reuse mode (fixed chrome, adaptive variation, or both). Restraint governs weight and recurrence, never the omission of an evidenced identity or communication motif.
- **Resource decisions** for immediate preparation: manifests may carry filenames, page relationship, status, and generation/crop/focal cues (plus subject/quiet zones, boundary, seam, and share when composition depends on them); no general roster or icon-to-page assignment. Each formula's LaTeX and each hyperlink's exact target stay in context, with no manifest. An explicit user implementation path wins; otherwise the registered default.

**Mandatory — whole-roster rhythm check, cover impact, closing impact**: [`plan-core.md`](../../references/plan-core.md) §4, applied to the transient roster in place; no artifact or second pass.

**Prepared final narration**: an explicit final/literal script for notes or audio is segmented by scene while resolving the roster, every word preserved, and written once before P01 to `notes/total.md` (`# Slide <number>` headings, `---` separators) as production input, split only after the roster exists. Draft narration stays source material for the ordinary notes branch.

**Resource need per page**: decide it under [`plan-core.md`](../../references/plan-core.md) §5 before resources. SVG/emoji icons keep their curated-pool boundary, and the page's carrier mix is §3's authoring decision, not a preparation decision. The resolved style controls treatment and recurrence but never eligibility, source, or the native vocabulary. A compact icon cue does not discharge a scene, subject, or visual-weight job a photo or illustration family would serve. The communication-job menu never satisfies the per-page topology decision in §3.

**Image sources, grounding, families, lettering, per-image source, and treatment**: [`plan-core.md`](../../references/plan-core.md) §5.1 owns the credentials Hard rule, visual grounding before a zero-image deck, illustration families and illustrated icons, decorative-lettering candidates, the per-image source decision, and image treatment and subject layers. In Quick, web search keeps zero-config providers, AI capability is resolved during preparation, and the no-AI replan below owns exhaustion.

**Chart/Table references**: [`plan-core.md`](../../references/plan-core.md) §5.2 — at most one flexible `family/key` per page, validated with `visualization_recall.py validate`, purpose kept in context, `no-template-match` retained when none fits. Each independent Chart/Table keeps its page-local `kebab-case` key, `<object-key>=yes|no` native-ready decision, and any promoted chart-verification status in context; qualitative relationships create no key or reusable structure.

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

**Hard rule — planned slice closure**: every sheet carries `slice_grid` and `slice_names` in `image_prompts.json`; every `images/<name>.png` must exist after an exit-0 `--strict-alpha` run before authoring — a `Generated` parent never satisfies its outputs.

| Slice outcome | Action |
|---|---|
| Nonzero slice run | The parent returns to preparation: correct only an evidenced key/tolerance mismatch, otherwise enlarge cells or split incompatible families and regenerate; repeating the same failing grid is not recovery |
| Explicit manual path | The item is `Needs-Manual` with `last_error` and blocks SVG/export until every output is supplied and validated |
| Exhausted automation | The no-AI replan below |

**Quick exhausted-automation no-AI replan** ([`image-generator.md`](../../references/image-generator.md) §7): when an automated AI path or its dependent slicing is exhausted, ask no path question and enter no manual fallback. Remove the affected AI jobs and stale manifest entries, carry their communication content with native text/SVG or prepared non-AI assets, and continue. Retaining AI imagery means repairing capability and starting a new Quick run.

**Validation before §3**: every file-backed resource is terminal — `Existing`, `Generated`, or `Sourced` under [`svg-image-embedding.md`](../../references/svg-image-embedding.md) — and every `slice_names` basename resolves to its PNG; a missing name resumes its owning step and is never deferred to the checker. Never bypass status by preview or presence, never substitute unrelated material.

| Web status | Rule |
|---|---|
| `Needs-Selection` | Blocks until a thumbnail is promoted or the bounded ranked pages and materially different variants are exhausted, after which a vision-capable owner may fetch one adopted-page package |
| `Needs-Manual` | Blocks even with an unverified file |
| No vision | Only the strict metadata-ranked path reaches `Sourced`, and its provenance says so |

**Inspection boundary**: acquisition-time review follows the owning reference; authoring inspects only one ambiguous `Existing`/`Sourced` asset under `executor-image.md` and never reopens `Generated` outputs (Image to PPTX inspects every normalized page and generated layer once, then the final recomposition). After resources change, run `analyze_images.py`; manifests and provenance are resource truth, not a design strategy.

---

## 3. Direct SVG Authoring

Read the execution core together, never file by file: [`shared-standards-core.md`](../../references/shared-standards-core.md), [`executor-base.md`](../../references/executor-base.md), [`semantic-svg.md`](../../references/semantic-svg.md), and [`preset-shape-vocabulary.md`](../../references/preset-shape-vocabulary.md) (complete, before P01). Then evaluate `executor-base.md`'s routing table once over the frozen roster and read every triggered module in the same batch (the `Any image` row loads its four files together); installed Layout/Deck structure adds [`pptx-structure-interface.md`](../../references/pptx-structure-interface.md). Keep the selected mode/style files: a custom applies one basis under its behavior, synthesizes several by their contributions, or follows the behavior alone. Reread anything only after a known file change or context invalidation.

**How executor-base binds Quick**: exactly as it binds Default except its `Default only` items — the persisted-plan handoff in §2 / §2.1 and the export hand-off in §6 — which Quick's transient §2 anchors, own checker gates, and export below replace; the Default gate cadence in `generate-pptx.md` Step 6 does not apply. Conditional authorities load on its routing table (Chart/Table branches, native data, formula, hyperlink). Chart/Table reference and final information model are independent signals, and selection never makes an object native-ready. Explicit user/template requirements and the resolved style override compatible aesthetic defaults, never technical boundaries, carrier eligibility, or native capability discovery.

**Mandatory — per-image-page composition**: for every page with images, after content and communication move but before geometry, apply `executor-image.md`'s image-integration decision once, keeping role, direction source, parent contour, slot/rhythm system, image/shape action, and continuity in context only; a deliberate plain or equal-grid result is valid when it communicates better. Image to PPTX replaces this and the page-geometry decision for its canonical frame: preserve source geometry, restore text natively, keep source-graphic identity through the prepared asset, and use the registered layer/plate stack; run the ordinary decisions only for additional non-source content.

**Mandatory — native formulas and hyperlinks**: no resource or manifest for either. Keep the exact LaTeX and choose ordinary text, same-paragraph inline math, or a standalone block with its SVG preview under [`native-formula.md`](../../references/native-formula.md). Keep each link's exact target, choose an inline or whole-object carrier, and author canonical `<a href>` under [`native-hyperlinks.md`](../../references/native-hyperlinks.md), never guessing a destination.

**Mandatory — per-page topology decision and geometry move**: after the page's content and communication move, before any geometry, decide whether geometry must carry `order`, `link`, `parent`, `membership`, `contrast`, or `overlap` (`executor-base.md` §2.2) — `no` stays on the base path, `yes` loads and applies the Shape Composition Grammar and topology assembly. Then, when the page's geometry reaches beyond basic primitives, load and apply [`native-shape-authoring.md`](../../references/native-shape-authoring.md) §2.1 to the transient geometry job, content, deck shape language, resolved style, and full vocabulary before coordinates (`describe --compact` only when objective facts could change a serious candidate). Both decisions stay in context; the capability menu, visualization recall, and template geometry never stand in for them. Quick runs [`verify-charts.md`](../stages/verify-charts.md) after the roster and before the final checker whenever data-driven chart geometry exists.

**Per-page anchors**: apply the core-message, typography-role, color, body-frame, density, and composition anchors from §2 while authoring. When `notes/total.md` was frozen, keep each page's segment in view so its visible state and direct-root groups support the spoken words without copying the script into body text.

**Canvas**: the §2 canvas — explicit user choice, otherwise the Layout/Deck owner's, otherwise `ppt169` `viewBox="0 0 1280 720"`; another registered format takes its exact viewBox from `canvas-formats.md`. Template canvas is a default, not a gate. The first SVG fixes the export canvas; every page matches it exactly. Filenames use one zero-padded width for the roster (`01_cover.svg` … `12_end.svg`, or three digits). Never leave pages from another run in `svg_output/` — the exporter publishes everything it finds.

**PPTX structure**: speed never flattens template structure.

| Structure owner | Page form |
|---|---|
| Free design, Brand/Style-only | Flat Slide-local SVG with one root `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`) and no Master/Layout/layer/placeholder metadata |
| Layout or Deck | Every page is a complete structured Slide SVG that preserves or deliberately adapts the prototype's root identity, fixed layers, and slots with current content on top — all-or-none across the roster, every reused Layout repeating an identical fixed-layer/slot contract, a new Layout allowed under the selected Master when the application paragraph calls for adaptation, ownership never inferred from repeated geometry, and `data-pptx-page-role` omitted |

A Style never strips structure; only an explicit instruction to use the workspace as visual language permits flat output.

**Typography**: name a concrete target-installed/approved family under `shared-standards-core.md` §4.1, never a lock or the host's fonts. Before P01 run `python3 ${SKILL_DIR}/scripts/text_measure.py calibrate <project_path> --role <name>:<family>:<size>` for every recurring role (one command, repeatable `--role`) and keep its table — CJK and Latin ≈ chars per 100 px per role, the checker's own estimator with wrapping headroom — in context. Every later page sizes zones from that per-font arithmetic: write the sentence first, fit the zone to it, and never trim wording to satisfy an estimate. Calibrate again only for a role or size never calibrated, and `wrap` only a genuinely long paragraph.

**Generation pacing (Mandatory)**: hand-write the roster in order with no confirmation stop. P01 calibrates visual identity and cover expression; the first ordinary content page calibrates content geometry and carrier integration; neither becomes a reusable template. A resolved motif follows its reuse mode (exact repetition for deliberate chrome, adaptive variation of scale, crop, density, position, or interaction otherwise).

**Cadence**: when the planned roster has seven or more pages, run the §4 final-check command with `--stage early` after P05 and before P06, repair under the consolidated-pass discipline of [`executor-base.md`](../../references/executor-base.md) §3, and continue; six or fewer pages skip the early gate. After every page exists, run the one final checker in §4. Every checker invocation follows a gate point (early or final, all covered pages written) or one consolidated repair pass; validating an authoring pattern early is not a reason. Use other stages only when their capability is needed.

**Hard rule — page authoring stays with the main agent** ([`executor-base.md`](../../references/executor-base.md) §3). This is not a resume protocol: if the context is lost before delivery, start a clean Quick run.

---

## 4. Export

After every page and referenced resource exists, run the Quick branch of [`verify-charts`](../stages/verify-charts.md) when any data-driven chart was authored and complete its repairs, then prove canonical compact authoring with the one lockless final check; fix every blocking error and rerun the same command:

```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> \
  --quick-generate --canonical-authoring --stage final --json
```

`--json` writes `validation/svg_quality_report.json`, the report `--quick-generate` export fingerprints against `svg_output/`; stdout stays the human-readable summary and is never parsed as JSON. Both flags above are required — omitting `--canonical-authoring` or `--json` makes the export refuse or skip the canonical check.

**Mandatory — final carrier-receipt review**: run the review in [`executor-base.md`](../../references/executor-base.md) §3 Checkpoints against the retained page jobs, deck shape language, motif, resource roles, and geometry signatures; a repair reruns this checker once.

**Notes** (when enabled): load [`executor-notes.md`](../../references/executor-notes.md) after the passing check, validate a frozen script or pre-SVG narration without regenerating it or otherwise generate `notes/total.md` from the final roster, then split:

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Success criterion**: per-slide files under `notes/` cover every published slide; the command exits non-zero on a missing slide or failed write — repair and rerun, and never let leftover files satisfy it.

**Motion and sound**: run [`customize-animations`](../stages/customize-animations.md) after the notes pass when the §1 outcome or an existing sidecar triggers it; deck-wide-only motion uses exporter flags. Quick video delivery completes the Custom Animations stage and validates `animations.json` before export unless the user asked for static or transition-only playback; direct narrated video derives cue timing only when narration governs groups. After motion is final, run the optional sound pass in [`animations.md`](../../references/animations.md) §2.2. `generate-audio` completes narrated MP4 delivery through the verified native mix or an explicit slideshow capture, never both.

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate --with-notes   # Speaker Notes enabled
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> --quick-generate --no-notes     # Speaker Notes disabled
```

**Exporter behavior**: `--quick-generate` reads `svg_output/`, resolves project-local assets, infers one canvas and one all-page structure mode (no metadata → flat; complete Master/Layout/slot metadata → structured), and needs no lock. Notes, Custom Animations, and narration stay off unless the agent enabled them or the video rule requires them; append `--native-charts-and-tables` only for an explicit native Chart/Table delivery decision. Never run `finalize_svg.py`. The exporter requires a passing `final` report whose fingerprint matches the current `svg_output/`; the default output path keeps backup and postflight, an explicit `-o <path>.pptx` skips backup.

**On failure**: repair the owning SVG, resource, or capability input, rerun the checker, and export again — never create a Design Spec or lock. When Narration Audio is enabled, run [`generate-audio`](../stages/generate-audio.md) after the validated export (page audio/SRT, narrated PPTX, optional raw MP4, final mixed or captured MP4, or the capture-ready handoff).

```markdown
## ✅ Quick Generate Complete

- [x] Source/resource preparation complete; the planning-capability batch and every selected detail source were read before the roster
- [x] The complete preset vocabulary was read before P01; each page resolved its topology decision, geometry move, and carrier mix without a quota and compared its geometry signature before the next page
- [x] Image need was decided independently of credentials; every image decided its own source, every `slice_names` output exists after an exit-0 strict-alpha run, and every exhausted AI job was replanned under the no-AI rule with its disclosure retained
- [x] Every selected formula and hyperlink uses its checker-valid native form
- [x] The frozen Template Application paragraph was applied, every installed Layout/Deck SVG was read, and structure matches the installed capability (flat vs explicit all-page structured)
- [x] The early gate ran once after P05 on a roster of seven or more pages (or a shorter roster skipped it), and every checker invocation followed a gate point or one consolidated repair pass
- [x] The carrier receipt was compared with the retained page jobs and contradictions repaired; the lockless final report passes and matches the current SVGs
- [x] The §1 motion gate was evaluated before P01 (the row hit, or none); enabled notes were validated/generated and split; enabled custom motion ran through its owning stage
- [x] One native PPTX exists under `exports/` or the explicit output path; no Strategist, confirmation, root Design Spec, or lock artifact was created
- [ ] **Next**: report the base PPTX and any narrated PPTX, MP4, or capture-ready handoff, plus the resolved mode, visual style, and image sources actually used; for every no-AI replan, report the affected job, attempted path, concrete error, replacement carrier, and that retaining AI imagery requires repairing generation capability and a new Quick run
```
