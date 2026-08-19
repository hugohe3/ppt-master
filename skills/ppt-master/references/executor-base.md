# Executor Flat and Shared Core

Always-loaded Executor authority for flat SVG page authoring and behavior shared by every Generate route. Load conditional branches only when their trigger is present.

**Conditional branch routing**:

| Trigger | Load |
|---|---|
| `pptx_structure.mode: structured` | [`executor-structured.md`](./executor-structured.md) |
| Any selected Chart/Table `family/key` reference, or a legacy `page_charts` row that resolves to a live Chart/Table SVG | [`executor-visualization.md`](./executor-visualization.md), then the resolver-returned Chart/Table branch |
| Any value-driven geometry, including a chart-family reference, mini chart, sparkline, inset, or small multiple | [`executor-chart.md`](./executor-chart.md) |
| Any semantic cell grid, including a table-family reference | [`executor-table.md`](./executor-table.md) |
| A page will use a preset pattern fill or an independent object is explicitly selected as native-ready | [`native-data-interface.md`](./native-data-interface.md) before emitting the pattern or replacement metadata |
| Any image | [`executor-image.md`](./executor-image.md) + [`image-layout-spec.md`](./image-layout-spec.md) + [`image-layout-patterns.md`](./image-layout-patterns.md) + [`svg-image-embedding.md`](./svg-image-embedding.md) |
| Any nontrivial mathematical expression | [`native-formula.md`](./native-formula.md) |
| Any external or same-deck click hyperlink | [`native-hyperlinks.md`](./native-hyperlinks.md) |
| Any placed image is `Status: Sourced` or its filename has an `image_sources.json` record | [`executor-web-image.md`](./executor-web-image.md), after `executor-image.md` |
| Effective Speaker Notes outcome is enabled after all SVG pages pass | [`executor-notes.md`](./executor-notes.md) |

Evaluate branches from each object's actual information model, not only from a Chart/Table reference. A catalog family selects construction guidance but never native readiness; `Native-ready` is an independent object-level decision. Page-local qualitative geometry also never implies package-level `pptx_structure.mode: structured`.

> Narrative skeleton and visual aesthetic come from the locked values selected through the [`modes/`](./modes/_index.md) and [`visual-styles/`](./visual-styles/_index.md) planning indexes. Executor does not reopen those indexes: it reads one locked preset file or only the exact `*_references` of a custom synthesis; an unreferenced novel custom reads none. [`shared-standards-core.md`](./shared-standards-core.md) supplies the technical boundary plus the fallback visual-quality and leading defaults when those authorities are silent.

**Hard rule — Shape-first page authority**: Every visible object intended for the exported slide MUST exist in the final page SVG or be explicitly referenced by it. Templates and `spec_lock.md` guide construction; they are not export-time overlays for missing visible content. Optional native Chart/Table metadata belongs to an independently selected object and never replaces this visible fallback during authoring; [`native-data-interface.md`](./native-data-interface.md) alone defines that metadata and its export activation. Native formula markers require a matching SVG preview; export replaces only it under [`native-formula.md`](./native-formula.md).

**Hard rule — flat PowerPoint structure**: Free-design, brand-only, Style-only, and every `template_reuse_scope: style` project use `pptx_structure.mode: flat`: write no root Master/Layout identity, `data-pptx-layer`, or `data-pptx-placeholder`; every visible object remains Slide-local, and the root declares exactly one canonical `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`). A Style workspace supplies reusable communication/design direction, composition rhythm, and information-expression defaults without page prototypes. Its identity-adjacent color, typography, icon, and image defaults yield to the final Brand/Deck identity and confirmed project lock. When a Style is installed alongside Layout/Deck, it changes only Direction / method and follows the resolved non-Style structure route. Export materializes one clean project-owned Master plus one Blank Layout from the current lock. Add `data-pptx-role` only to structural page-frame objects whose package, page-number, or animation behavior is not already expressed by specialized metadata; the marked element uses a stable unique `id`. See [`semantic-svg.md`](./semantic-svg.md).

**Hard rule — supported PPTX route**: The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter. Step 7.2 still generates `svg_final/` as a mandatory self-contained visual preview that may be inserted as an SVG picture. Do not treat PowerPoint's manual Convert-to-Shape operation as an authoring target or compatibility requirement.

> Note: this rule covers page design only. Speaker notes, animations, transitions, narration, and direct native-PPTX workflows retain their separate artifacts and package-level processing.

---

## 1. Effect Capability Discovery

**Mandatory — select by visual job**: establish each page's semantic skeleton,
then run the already-loaded [`svg-effects.md`](./svg-effects.md) §6.1 procedure
and Visual Job Router before finalizing; use §6.13 for a coordinated page
recipe when useful. The catalog expands construction vocabulary; it creates no
effect quota. Active cross-page continuous action additionally loads
[`animations.md`](./animations.md) §3.1 before authoring both endpoints.

**Hard rule — discovery does not expand compatibility**: Follow
`svg-effects.md` syntax and fallbacks; unsupported source/backdrop blur, blend
mode, SVG `<mask>` / per-pixel masking, dense texture, or skew remains
baked/alternative-only.

**Default — resolve active cross-page geometry here, while pages are still being authored (may override when the deck has no continuous action to express)**: object effects, page transitions, and Morph pair keys are post-processing decisions, but the two visible endpoint states are not. Apply this preparation only when an explicit user motion instruction, an enabled effective Custom Animations outcome, or an existing `animations.json` activates motion; a §IX Motion suggestion alone remains non-operative advice. An active sequence that should read as one continuous action (slide-in, flip, camera push-in, progressive reveal, camera pan) must be authored as consecutive pages in `svg_output/` now. Give each continuing endpoint a compatible direct-root group; source and destination ids or geometry may differ because the later motion stage can bind them explicitly through `animations.json`. A deck that reaches export without both states cannot gain the motion by adding a flag. Adding pages is a §IX roster change and returns to Strategist for Design Spec repair first.

---

## 2. Design Parameter Confirmation (Mandatory Step)

Before the first SVG page, output a confirmation listing: the compact communication objective, canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan, and the live-preview URL reported by the launcher. If the preview launch failed, state that failure before generating SVGs instead of silently proceeding. Prevents purpose/spec/execution drift.

### 2.1 Execution context validity (Mandatory)

- **Valid**: if the exact complete Design Spec and lock remain in the unchanged, uncompacted active context, reuse both for every page. Do not reread or poll them. The one scheduled exception is the five-page lightweight lock re-read defined below.
- **Invalid**: fresh/resumed/restarted execution, compaction/summary-only recovery, or an external/unknown change requires one complete read of `design_spec.md`, then `spec_lock.md`, plus triggered references/template inputs. Mid-deck recovery also reads the latest completed SVG and, when images are used, current image metadata.
- **Uncertain**: consult the retained lock first, then only the owning Design Spec fragment; use sources only for facts. Design Spec remains upstream on conflict.

**On-demand page-context diagnostic**: only for explicit telemetry/debugging or an unresolved page/template/visualization path-SHA question; never as a pre-page gate:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py page-context <project_path> P<NN> [--record-usage]
```

Consume stdout directly; stop on non-zero exit. The projection is derived, not authoritative. Use `--record-usage` only for measurement.

**Same-context repair**: in a valid uncompacted context, a bounded repair that preserves roster/order/identity/communication needs only affected Design Spec/lock fragment readback plus `project_manager.py validate`. Any broader or invalid-context repair requires the complete reads above.

**Hard rule — exact page roster**: `design_spec.md §IX` is the ordered queue: one final slide per entry, with the same id/order. The UI range no longer applies. Never add, drop, merge, split, or reorder; repair/reconfirm the Design Spec first.

**Hard rule — binding selection vs realization**: use Strategist-selected semantic content, resources/paths, structured-template Master/Layout routing keys, core fonts, palette anchors, icon-library/stroke anchors, and crop boundaries. Adapt realization—including which prepared project-local icon, if any, best serves each page—without changing those binding selections, except sparse local font/color garnish allowed below. Missing or unresolved material stops execution and returns to Strategist-owned acquisition/failure recovery; never search, generate, download, sync, invent, or substitute it. Binding selection changes require upstream repair.

**Reference — planning advice, not a layout lock**: treat §V/§IX `Layout`, cover/closing composition, capability recommendations, §III motif direction, Chart/Table `family/key` construction references, and §VIII image-layout patterns as non-binding inputs. Consider each, then adopt, adapt, or decline it without upstream repair when the same semantic job and every binding user/template/resource constraint remain satisfied. Executor owns final carrier choice, page-scale composition, information-preserving visualization realization, geometry, spacing, coordinates, native preset/Boolean/freeform construction, and effects.

**Hard rule — content vs expression**: `design_spec.md §IX` owns each page's semantic content and supplies complete preferred wording and block texture; those expression choices are not verbatim requirements unless explicitly literal. Executor may paraphrase, condense repetition, regroup or reorder material within the same page, and switch among prose, bullets, keywords, labels, or visual annotation when fit or readability benefits. The result must remain information-equivalent: preserve the `Core message`, `Audience move`, and every substantive claim, fact, data value, proper name, qualifier or caveat, relationship, key argument or evidence, and literal requirement. Never add a claim, move content across pages, or drop information to make the layout fit; return an unfit or underspecified block for Design Spec repair.

Use named lock roles literally when that role applies, and use optional `Template Application` from the retained Design Spec. Choose contextual page-local values from the Design Spec, style, content, and current composition rather than forcing every object into a lock row. A page-context delta overrides neither facts nor constraints. Deprecated `page-context --bundle` is a compatibility no-op.

**Source verification**: §IX owns the complete page brief; the page delta does not carry the source corpus. Read sources only to resolve listed `Fact IDs` or verify required claims, quotes, names, or data. Do not add facts, claims, or selected content. Return underspecified blocks for Design Spec repair.

**Per-page communication trace**: Read `communication.objective`, `communication.core_message`, and the current §IX `Core message` + `Audience move` before choosing composition. The page must advance the compact objective and move the audience as authored in §IX; the global core message remains the deck-wide north star. A page that cannot state this movement is an upstream outline defect — surface `warning: P<NN> has no communication move` instead of compensating with decorative layout. Do not invent a new purpose, ask, or outcome at execution time. Structural pages may advance the contract by establishing relevance / tension / decision frame or by completing the final commitment; they are not exempt from having a reason to exist.

**Mandatory — per-page Structure decision**: Before drawing, read the current §IX `Layout`, `Visualization`, and `Content` and decide whether geometry must carry any qualitative `order`, `link`, `parent`, `membership`, `contrast`, or `overlap` relationship. Derive the result from that semantic relationship with the already-loaded [`executor-structure.md`](./executor-structure.md); a suggested carrier, topology, or macro composition does not decide it. If none applies, continue on this shared base path. If any applies, use that grammar and retain the relationship statement in active page context; do not create a catalog reference, lock row, or new artifact. A Chart/Table reference never substitutes for this decision.

**Per-page reading-mode check**: Read `communication.consumption_mode` before choosing the page's composition. Apply it together with the authored §IX block texture and `page_rhythm`:

| `consumption_mode` | Page execution |
|---|---|
| `text` | Make the visible page independently understandable. Preserve complete prose, explicit labels / captions / sources, tables, and necessary detail; use bullets only for genuinely parallel or ordered items. |
| `balanced` | Keep the primary claim and its evidence on the page; when notes are enabled, let them add interpretation and transitions. Mix prose, structured evidence, and necessary lists according to their semantic relationship. |
| `presentation` | Make one claim and one dominant visual expression legible at projection distance. Keep visible copy concise; when notes are enabled, put explanation and transitions there instead of creating paragraph dumps or compressed bullet prose. When notes are disabled, rely only on the confirmed presenter/page channels and never omit required content on the assumption that notes will carry it. |

Apply the content-vs-expression contract above within the selected reading mode. Never drop or invent facts to force a mode. When the authored texture materially conflicts with the lock, render the least-destructive faithful composition and surface `warning: P<NN> content texture conflicts with consumption_mode <value>` as an upstream outline issue; do not encode this subjective judgment in the checker.

**Default — authored texture (may override when information-equivalent)**: start from each `design_spec.md §IX Content` block's written texture because it is the Strategist's recommended expression. Keep prose when its continuity carries causal, argumentative, narrative, qualification, or emphasis relationships; use bullets or keywords when the material is genuinely parallel or ordered, or another information-equivalent structure is clearer. Never convert solely because a list is easier to lay out or an inherited template exposes a list slot.

- **Hard rule — one paragraph, one text frame**: use one `<text>` per prose paragraph, never sibling `<text>` elements for its visual lines. Keep the first authored line as direct text; later lines use direct `<tspan>` children that repeat parent `x`, retain effective font size, and use positive relative `dy`. An all-`<tspan>` form may start at `dy="0"`. Default retains these breaks without PowerPoint wrapping; `--reflow-text` enables reflow. Start from the shared leading ranges in [`shared-standards-core.md`](./shared-standards-core.md) §4.2, then adjust for the typeface, reading distance, explicit user/template requirements, and locked style.
- **Template precedence**: an inherited slot never overrides the content relationship. If faithful expression needs prose, widen or reflow the container, or drop that card; never convert solely to fill a list slot.
- **Mode precedence**: the locked mode shapes voice / register, not §IX's authored titles or page order. When a `§IX` title is a user-authored topic label, keep it — do not upgrade it to an assertion just because the mode (e.g. `pyramid`) favors them; mode title-tendencies apply only to AI-drafted titles.

> Note: block-level phrasing, applied *within* the page's `page_rhythm` density (below), not against it.

**Missing `spec_lock.md` or `design_spec.md`** → stop before drawing and report the missing gate artifact. Recover through [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §3; do not silently downgrade. A failed on-demand `page-context` diagnostic is also not evidence that a required planning artifact may be bypassed.

**Missing field in an existing lock**: follow [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2.

**Execution anchors and contextual values**:

- Base icons may use any SVG already prepared under `<project_path>/icons/`. `icons.library` records the Strategist's primary bundled style choice and `icons.inventory` indexes its curated synced pool; neither assigns icons to pages or limits other project-local assets. `simple-icons` brand marks appear there only when the content actually needs that real brand; they are not a separately confirmed library.
- Illustrated icons are prepared transparent slice files under `images/` and follow [`executor-image.md`](./executor-image.md), even when they perform the same compact semantic job as an SVG icon. Never move them into `icons/`, add them to `icons.inventory`, or render them through `<use data-icon>`. Use or combine them with prepared SVG icons when the page benefits, keeping the result visually coherent and applying no coverage quota.
- Core color roles retain their meaning. Derive tints, shades, alpha, gradients, and effects; preserve natural asset colors; and use sparse page-local accents for differentiation/ornament. They must not become a competing or recurring palette.
- Resolve structural families by role: exact `<role>_family` first, then `title_family` for title roles or `body_family` for other unoverridden roles, then legacy `font_family`. Never flatten declared role overrides. A sparse export-safe accent family may style short non-structural display/ornament only—never title/body/data/annotation. Recurrence requires upstream selection.
- Font sizes use the named `typography` role values as deck-wide anchors. Map every structural text item to a declared role before drawing; never inherit a template placeholder size. Start from the anchor, then use composition and content fit to adjust that occurrence by at most `±2`px. Keep same-page peers consistent and preserve the role hierarchy; bounded adjustment does not create a new role.
- **Core message ≥ `body`**: map the page's primary claim to declared `lead` / `subtitle`, never below the current body treatment. Footnotes, page numbers, and credits use declared `footnote` / `annotation`; do not invent a smaller role.
- **Write unitless px, with at most two decimals.** Structural and mapped-role text uses only its anchor or a value within its `±2`px band; the sparse display-size exception is defined separately below. Do not substitute familiar pt-style numbers or emit long precision tails.
- **Sparse display-size exception**: a short non-structural Hero/Display element may use one undeclared size outside all anchor bands at most twice across the deck without a lock row. The third occurrence makes that size recurring: stop and return to Strategist to name the role in the Design Spec and `spec_lock.md`, then read back and validate the affected fragments before reuse. This exception never applies to titles, body copy, subtitles, annotations, footnotes, captions, data labels, or card copy, and nearby sizes must not be introduced to imitate one recurring treatment.
- **Prepared decorative lettering**: When the approved plan selects stable artistic lettering as part of the visual, place its prepared AI/slice file as an image asset and keep the ordinary editable title/subtitle in separate native text frames. Do not recreate the asset with layered glyph copies or native WordArt; when the plan keeps that wording as native text and prepares no lettering asset, use ordinary `<text>` without inventing a missing image.
- **Outside-band recovery**: for structural text, reflow geometry and use the declared role band locally. For a sparse display occurrence, keep the unitless value and verify that its deck-wide count remains at most two. Never flatten a justified distinction or add a role merely to silence the checker. Mirror pages preserve exact source typography as inherited input.
- Images MUST reference files listed under `images`; no invented filenames
- For math, load [`native-formula.md`](./native-formula.md): simple notation stays text; one-line structural prose uses inline; matrices, multiline derivations, or standalone high structure use block. Keep exact LaTeX plus preview; never use an image.

Return upstream before any derived/accent identity becomes recurring or structural, or when an undeclared display size reaches its third occurrence, then update the retained context under §2.1. Local garnish, same-role `±2`px adjustments, and at most two sparse display-size occurrences need no lock row. Never expand the lock to silence a comparison. New icon acquisition, images, structural fonts, role anchors, and resources keep their preparation/role rules.

**Five-page lightweight lock re-read (Default Generate only)**: after
completing P05, P10, P15, … and only when another page follows, read
`spec_lock.md` in full once before starting the next page. This is a pure
context re-anchor for the locked palette, typography, icon style, and
`page_rhythm` values under long context. No checker runs, no per-page
self-check output, no pause, and no mid-deck repair loop. If the re-read
reveals an external/unknown change, follow the Invalid recovery branch above;
otherwise continue directly. Compaction, resume, or restart still follows the
full recovery reads above. Quick Generate does not read a project-root
`spec_lock.md` and does not use this rule.

**Per-page layout rhythm — `page_rhythm` section**:

Before drawing each page, look up its entry in `page_rhythm` (key format `P<NN>` matching the page index in §IX of `design_spec.md`) and apply the corresponding layout discipline:

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). `mirror` follows its prototype; `layout` retains its structure system. `style` / free design preserves the §IX cover hook or closing takeaway but may adopt, adapt, or decline the recommended composition. Avoid an information-empty generic cover/sign-off unless content, user direction, or template requires it. |
| `dense` | Information-heavy. Card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. This is the baseline behavior. |
| `breathing` | Low-density impact page. Avoid **multi-card grid layouts** — do not organize content as multiple parallel rounded containers (3-card row, 4-card KPI grid, 2×2 matrix rendered as cards). Use naked text blocks, dividers, whitespace, or full-bleed imagery as the content structure. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine — the rule is about grid structure, not about the `rx` attribute. Proportions follow information weight (not a preset ratio). Typical forms: hero quote, single large number with one-line interpretation, full-bleed image with floating caption, section transition. |

> Mechanical repetition comes from reusing the same carrier and topology without a page job—not from semantic cards themselves. Cards remain appropriate when they express real peer grouping, comparison, hierarchy, or capacity; vary rhythm when the content relationship changes. Context recovery follows §2.1.

**Missing or empty `page_rhythm` section — fixed compatibility default** → emit `warning: spec_lock.md missing/empty page_rhythm — defaulting all pages to dense` once, fall back to `dense` for all pages.

**Tag not found for current page — fixed compatibility default** → emit `warning: spec_lock.md page_rhythm tag not found for P<NN> — falling back to dense` once per deck (aggregate; do not repeat per page), fall back to `dense`. Do not invent a tag.


---

## 3. Execution Guidelines

- **Element grouping (Mandatory)**: wrap each logical Slide-local body unit in a descriptive, page-unique top-level `<g id>`. Every visible direct root `<g>` declares root-coordinate `data-pptx-bounds="x y width height"`; frame/native coordinates do not replace it, and placeholder bounds also supply the slot frame. Nested groups need no bounds and any such values are ignored. Checker compares root bounds with the `viewBox`, recursively checks estimable text against its root module with DrawingML wrapping headroom, and independently checks every estimable visible text carrier against the page without that headroom: through `1px` is ignored; module overflow warns through `5%` and fails above it, while larger page overflow always fails. Unestimable visible text receives an advisory warning. Only a wholly off-canvas direct-root Morph endpoint may set `data-pptx-morph-staging="true"`; keep its text inside its own module bounds, use an explicit pair when Morph remains enabled, and never use the marker for partial overflow. Images, shapes, paths, `<use>`, effects, and object frames remain geometrically free. Flat pages use ordinary groups; structured slots already qualify, while titles, direct Master/Layout atoms, and canvas-level static framing may remain root primitives. On flat pages, give a root background image or full-canvas scrim/decoration rectangle a stable `id` plus `data-pptx-role="background"` / `"decoration"`; never wrap it only to silence the advisory.
- **Reference — not a constraint**: top-level groups set semantic and automatic-animation granularity, but they may contain descriptive nested `<g>` edit groups when the page has meaningful internal subunits. Nested groups need no bounds and create no automatic animation step; use or omit them from the page's actual editing semantics, with no default pattern, depth, or quota.
- **Default — size `data-pptx-bounds` as the intended module zone, not a glyph box (may skip when no text is estimable)**: make the zone as generous as the canvas and sibling layout allow, without overlapping another module zone. An untransformed line spans `y - 0.85 × font_size` to `y + 0.35 × font_size`; width uses the shared SVG-to-PPTX per-run estimate and safety headroom. If text does not fit, first expand a zone that has unused non-overlapping space; otherwise reflow or adapt. Larger bounds do not repair off-canvas text.
- **Spec adherence**: follow binding color, canvas, typography, identity, resource, and template anchors; apply layout and other Reference directions under §2.1 without turning them into locks
- **Template structure**: inherit the native visual framework only for `template_reuse_scope: mirror|layout`; `style` uses the flat route
- **Main-agent ownership**: SVG generation must run in the main agent (not sub-agents) — pages share upstream context for cross-page visual continuity
- **Generation rhythm**: P01 → first-page gate → uninterrupted remaining pages → final gate, in one context without batches or mid-run checker calls.
- **Fact provenance**: when a §IX page lists `Fact IDs`, resolve each ID from `sources/*.facts.json` and keep the claim/value unchanged. Render a compact source footnote using the source name and a short URL/domain when space permits; when speaker notes are enabled, state the attribution naturally there too. When §IX says `Data class: scenario`, place a visible localized `Scenario data` / `情景数据` label adjacent to the affected KPI/chart and, when notes are enabled, state naturally there that the number is illustrative. Never attach an external fact ID to scenario data or let an unlabeled invented KPI look factual.
- **Mandatory — resolve the page carrier mix before coordinates**: decide background paint/field, editable text and optional lettering, native geometry/lines, prepared photos/scenes/illustration/icon assets, and applicable visualizations in one page-level composition decision. Use any suitable subset; omitting a carrier remains valid. Do not finish a text/container layout and then treat the other families as optional decoration. Use only prepared external resources, preserve every binding resource job and constraint, and choose the actual combination, visual weight, z-order, and local native construction from the page message and hierarchy. The resolved style controls treatment and emphasis, never carrier eligibility, image source, or the complete native construction vocabulary.
- **Default — stage each page with the style's composition geometry (may override when another page-fit move is stronger)**: an SVG page is a canvas, not a DOM. Resolve the page-scale move from `spec_lock.md`: a preset uses that selected style's §1 `Composition geometry`; `custom` executes `visual_style_behavior` first, then uses §1 geometry only from exact `visual_style_references` that the behavior assigns a shape or composition job. Other bases contribute only their assigned job, and an unreferenced novel custom follows its behavior alone. Treat every listed move as generative vocabulary rather than a finite menu, then apply [`native-shape-authoring.md`](./native-shape-authoring.md) §2.1's shared exact-fit geometry gate.
- **Default — consider the planned motif direction (may override when another coherent expression better serves the deck)**: when §III `Theme` recommends a cross-page motif or element family, decide whether it earns a continuity job. If adopted, keep its reuse coherent while varying scale, crop, density, position, and content interaction by page role; otherwise adapt or decline it and establish a more fitting style-consistent expression. An explicit user/template motif remains binding.
- **Inherited containers**: preserve meaningful template frames; restyle radius, fill, stroke, and depth from the active Design Spec and `spec_lock.md`. Selected Chart/Table reference adaptation is owned by [`executor-visualization.md`](./executor-visualization.md); preview effects never override project styling or structural roles.
- **Reference — prefer semantic geometry over preset stacks**: for relationships such as ascending, converging, breaking through, or stacking, first compose faithful primitives and exact presets as one page geometry system; use a Boolean only when the contour itself must merge, open, or fragment. Only when neither construction works should one page-specific polygon/path replace a stack of generic arrows.
- **Reference — create depth with restraint**: use rhythm, spacing, typography, accent bars, and subtle tints before shadows. Reserve lift for a few genuinely floating elements; keep peer grids, dividers, and ordinary body containers flat. When material layering itself is part of the resolved visual style, follow that style's hierarchy instead of flattening its body planes.
- **Phased generation** (recommended):
  1. **Visual Construction Phase**: generate all SVG pages sequentially for visual consistency. Apply every triggered information-model branch while drawing. **MUST embed one object-scoped plot-area marker** per §IX-named or Quick-promoted value-driven chart object under [`executor-chart.md`](./executor-chart.md) §2; coordinate calibration is a post-generation step (see [`verify-charts`](../workflows/stages/verify-charts.md)). Write every `<object-key>=yes` native marker plus JSON metadata atomically under [`native-data-interface.md`](./native-data-interface.md) §2. **Reach for native presets** per §3.0 as you draw each page: a block arrow, chevron, banner/ribbon, callout, standard flowchart node, or star is authored through `preset_shape_svg.py` at draw time — decided by the object's intent as you create it, never by scanning finished paths, and never committed to a bare `<path>`/`<polygon>` when a preset expresses it (a gradient fill/stroke or a pattern fill is the one paint exception — keep those ordinary SVG; when justified, one registered [`svg-effects.md`](./svg-effects.md) §6.4 shadow/glow stays on the helper-authored shape). **First-page gate (Mandatory)**: after completing the first page, run `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage first-page --json` directly without output filtering. Review the whole P01 issue set, make one consolidated edit pass for every error and any selected warnings, then perform one verification rerun. If it still fails, treat that complete output as the next batch; never check between individual fixes. After it passes, draw P02 through the last page without checker calls.
  2. **Quality Check Gate**: only after every planned SVG exists, run `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage final --json` directly on `svg_output/` without `tail` / `head` / `grep` filtering. One run already reports all pages. Review its complete issue set, fix every `error` plus any selected advisory warnings in one consolidated edit pass, then perform one verification rerun. If it still fails, its complete output begins the next batch cycle; never use checker calls to discover or fix one next issue at a time. Every `warning` is advisory: it never sends the page back for required modification, never authorizes automatic rewriting of compatible user syntax, and needs no acknowledgement/disposition line. Recommendation warnings describe the generated-SVG default; fidelity/quality warnings may be surfaced when material, while the existing input remains releasable. Prototype-identical diagnostics are recorded as `inherited`, source conversion losses as `source-import`, changed/new advisories as `introduced`, and release failures as `blocking` in `validation/svg_quality_report.json`. If release truly depends on a condition, it belongs in `errors`. On success, use the exit status and terminal summary; do not open or `cat` the complete JSON into model context. If terminal output is truncated on failure, read only the relevant issue arrays from the report written by that same run. Do NOT defer error handling to after `finalize_svg.py` — finalize rewrites SVG and masks some violations.
  3. **Logic Construction Phase (conditional)**: after SVGs pass the quality check, batch-generate speaker notes for narrative continuity only when the effective Speaker Notes outcome is enabled.

**Mandatory — final carrier-receipt review**: The final checker prints one
factual `[CARRIERS]` summary and stores per-page detail under
`files[].info.carrier_receipt`. Compare the summary with the retained page jobs,
chosen resource roles, and running geometry signatures before export. Counts
and diversity never create a quota or prove quality; zero use remains valid.
When the facts contradict an active decision—such as an adopted preset absent
from output, a primary image reduced to a minor frame, or unrelated jobs
collapsing to one neutral construction—read only the affected receipt rows,
repair those pages in one consolidated pass, and rerun the final checker.

### 3.0 Native Shape Selection

**Hard rule — contour before encoding**: choose the page-fit contour from the
full native vocabulary before its authoring form. Rectangle, rounded-rectangle,
circle, and ellipse are preset contours even when authored with short SVG
primitive syntax; never select them because that syntax is easier. After
selection, use [`native-shape-authoring.md`](./native-shape-authoring.md) §1's
simplest exact form, keep atoms independent unless one contour is required,
materialize that contour with Boolean semantics, and use freeform last. Block
arrows, chevrons, banners / ribbons, callouts, flowchart nodes, stars, and other
Office symbols use `preset_shape_svg.py`, not plain paths or fake rectangles.

Before the first page, read
[`preset-shape-vocabulary.md`](./preset-shape-vocabulary.md) completely. Decide
every page-fit contour and its simplest exact authoring form directly from the
page content and visual system; no Design Spec construction selection, scorer,
or material inventory gates this choice.

**Mandatory — independent per-page geometry move**: after the Structure result
and any applicable topology resolve, apply
[`native-shape-authoring.md`](./native-shape-authoring.md) §2.1 before writing
coordinates. It owns the exact-fit geometry comparison, composition lenses,
independent relationship / carrier fit, contour-family / exact-result choice,
reader effect for a generic or undrawn result, running geometry signature, and
materialization boundary for both `Structure=no` and `Structure=yes`. Keep the
current decision in active context and never change the Structure result.

| Selected result | Authoring form |
|---|---|
| Selected exact non-Connector stock contour | Use ordinary SVG only when the exporter maps it to that same contour; otherwise call `preset_shape_svg.py render` and paste its complete stdout fragment. |
| Straight relationship / divider / leader | Use `<line>`; add a registered marker under [`shared-standards-core.md`](./shared-standards-core.md) §1.1 only when direction is meaningful. |
| Bent / curved relationship exactly expressed by a stock Connector contour, with no required endpoint attachment | Use the matching `bentConnector*` / `curvedConnector*` preset through the helper as an unconnected native Connector shape. |
| Selected text/content boundary needs no filled surface | Use its exact authoring form with `fill="none"` and a visible stroke; keep text and other content independent. |
| Two or more native shapes should form one page-level geometry system | Follow [`native-shape-authoring.md`](./native-shape-authoring.md) §2.1: compose faithful primitives and presets as independent siblings first, then materialize only contours that require Boolean semantics. |
| Supported closed-shape / resolvable-text operands need union, cutout, overlap, symmetric difference, or fragmentation | Use `shape_boolean_svg.py` when Boolean materialization is the clearest faithful construction; follow [`native-shape-authoring.md`](./native-shape-authoring.md) §6. |
| Stock shape that needs a gradient fill/stroke or a pattern fill | Keep ordinary SVG — the helper paints `none` or a solid HEX on both fill and stroke only ([`native-shape-authoring.md`](./native-shape-authoring.md) §5). |
| Page-specific freeform, organic, branded, icon, data geometry, or relationship contour that primitives, exact presets, their independent composition, and Boolean materialization cannot faithfully express | Keep ordinary SVG path/polygon geometry. |
| Similar-looking contour only | Never infer a preset; continue to the Boolean gate, then use freeform only if no faithful construction exists. |

**Hard rule — freeform is the last construction tier**: before hand-authoring a
stock-looking `<path>` / `<polygon>`, complete contour selection, simplest exact
materialization, independent composition, and the required Boolean-result gate.
A freeform is permitted only when those routes cannot faithfully express the
object; avoiding a helper or drawing the browser-visible contour faster is not
a valid exception. Data-defined geometry and a genuinely locked organic /
hand-drawn contour satisfy the exception by semantics, not by convenience.

This decision applies only while drawing a new object. A suggestion never
triggers retrospective scanning, contour classification, or automatic
upgrading of ordinary SVG during export.

**Hard rule**: do not hand-write `data-pptx-authoring`, `data-pptx-prst`,
`data-pptx-frame`, adjustment metadata, or registry paths. The preset helper
generates one compact atomic `<g>` from the shared 187-shape registry, with
semantic metadata and base paint written once. Rerun that helper when geometry
or paint changes; never edit one of its direct paths.

**Default — relationship geometry**: use `<line>` for a straight relationship.
When a relationship genuinely needs a bend or curve and a stock Connector
contour fits, prefer the matching `bentConnector*` / `curvedConnector*` preset
over a hand-authored SVG Bézier. Use an open freeform path only when a straight
line and the native Connector families cannot faithfully express the required
route, data geometry, or locked hand-drawn / organic style. A directional solid
object remains an ordinary `shape` preset such as `rightArrow` or `chevron`.

Authored Connector presets export as unconnected `p:cxnSp` objects: they do not
bind to node sites or follow moved nodes. Never hand-add endpoint/site metadata
or claim attachment semantics. Imported Connector topology stays under the
preserve/mirror contract. `actionButton*` presets provide visual geometry only,
not actions or hyperlinks.

**Hard rule — narrow helper scope**: Both helpers print only their documented
stdout fragment(s); neither writes a page or chooses layout. Read every returned
fragment and insert it through the normal `apply_patch` page edit; never
redirect, loop, or batch helper output into `svg_output/`.


### SVG File Naming Convention

Format: `<index>_<page_name>.svg`. Use one roster-wide zero-padded index width sized for the Design Spec §IX roster, such as `01_cover.svg` through `12_end.svg` or `001_cover.svg` through `120_end.svg`; match the deck language and page title.

---

## 4. Icon Usage

Strategist chooses at most one primary bundled stylistic library and may select `simple-icons` alone or alongside it; Executor implements from the complete prepared project-local pool. Library details and selection rules: [`../templates/icons/README.md`](../templates/icons/README.md). This section defines placeholder syntax.

> **Prepared-project boundary.** Any SVG already under `<project_path>/icons/<lib>/` is valid execution material, whether selected from a bundled library or supplied by the user, a template, or an import workflow. New authoring must resolve there. The global fallback in `finalize_svg.py embed-icons` is legacy compatibility, not permission for Executor to discover or use an unprepared global icon.

> **Icon identifiers are case-sensitive filenames.** Every `data-icon` value must use the exact project-local relative basename (`tabler-outline/award`, never `tabler-outline/Award`). Strategist records its curated bundled pool in `spec_lock.md`; Executor need not add other already-prepared project-local icons to that inventory. Custom identifiers preserve the custom file's exact case; the pipeline never silently lowercases names.

**Built-in icons — Placeholder method (recommended)**:

```xml
<!-- chunk-filled (straight-line geometry, sharp corners, structured) -->
<use data-icon="chunk-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-filled (bezier-curve forms, smooth & rounded contours) -->
<use data-icon="tabler-filled/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- tabler-outline (light, line-art style — screen-only decks) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- phosphor-duotone (single color + 20% backplate — soft depth without solid weight) -->
<use data-icon="phosphor-duotone/house" x="100" y="200" width="48" height="48" fill="#005587"/>

<!-- simple-icons (brand logos — used alongside the deck's primary library, only for real company/product marks) -->
<use data-icon="simple-icons/github" x="100" y="200" width="48" height="48" fill="#181717"/>

<!-- tabler-outline with thin / bold stroke (stroke-style libraries only) -->
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="1.5"/>
<use data-icon="tabler-outline/home" x="100" y="200" width="48" height="48" fill="#005587" stroke-width="3"/>
```

> ⚠️ **Color**: ALWAYS use `fill="#HEX"` on `<use data-icon="...">`. NEVER use `stroke` or `fill="none"`, even for stroke-style libraries.
>
> **stroke-width** (stroke-style libraries only, currently `tabler-outline`): allowed values `{1.5, 2, 3}`. If `spec_lock.md icons.stroke_width` is declared, all placeholders MUST use that value deck-wide. Ignored on non-stroke libraries.
>
> **Missing `icons.stroke_width` in an existing stroke-library lock — fixed compatibility default**: use `2`, emit one warning, and continue. New authoring must still declare the field.
>
> Icons are auto-embedded by `finalize_svg.py` — no need to run `embed_icons.py` manually.

**Project-local verification**: verify the exact prepared file before use:
```bash
test -f "<project_path>/icons/<lib>/<name>.svg"
```

**Default — purposeful icon use**: choose prepared icons per page when they compress a label, distinguish parallel categories, clarify a process / KPI / state, or improve navigation and visual rhythm. Omit them when imagery, charts, or typography already carry the meaning. There is no coverage quota, and the prepared pool need not be exhausted.

**Missing project-local icon** → return to Strategist's preparation / `icon_sync.py` gate. Do not search the global library, select an alternative, or copy a candidate in Executor.

**Hard rule — prepared assets**: Executor may freely combine project-local icons, regardless of namespace or style. It may not acquire a new icon or treat a globally resolvable file as prepared material.

---

## 5. Font Usage

Read typography from `spec_lock.md`: `<role>_family` → `title_family` / `body_family` → legacy `font_family`; sparse accents follow §2.1. Under [`native-formula.md`](./native-formula.md), blocks use marker style; inline math inherits size / visible solid fill and exports with the project text language in Cambria Math.

**Default — locked-stack realization (may vary treatment)**: Express the Design Spec Character Reference through scale, weight, spacing, color, and composition; keep the locked family. Put the common stack on root `<svg>`, omit matching descendants, and override at the nearest clear `<g>`, `<text>`, or `<tspan>`.

**Missing required field — `typography.font_family`** → stop and return to Generate Step 4 / [`strategist.md`](strategist.md) §6.2 to repair `spec_lock.md`; do not infer a stack from `design_spec.md`.

**Hard rule**: every SVG `font-family` stack MUST resolve to target-installed/approved Latin and EA faces. PPTX writes one face per script; CSS tails affect preview only, and fonts are not embedded. Missing-face substitution is viewer-selected—not guaranteed Calibri or a later stack entry.

---

## 6. Completion Routing

After every SVG page passes the final quality check, load
[`executor-notes.md`](./executor-notes.md) and complete its notes contract only
when the effective Speaker Notes outcome in `design_spec.md §I` is enabled.
When disabled, proceed directly to the route's conditional motion handling and
Step 7.

## 7. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase and any enabled Logic Construction Phase are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export**: Follow [`generate-pptx.md`](../workflows/generate-pptx.md)
Step 7. That workflow owns the serial commands, gates, success criteria, and
published artifacts; [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md) owns
tool-specific flags and behavior.

`svg_final/` may be opened directly or manually inserted into PowerPoint as an SVG picture. It is not a second PPTX route. Use `-s final` only for converter diagnostics; release exports use the default `svg_output/` source. Manual Convert-to-Shape behavior is unsupported.
