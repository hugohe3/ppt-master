# Executor Flat and Shared Core

Always-loaded Executor authority for flat SVG page authoring and behavior shared by every Generate route. Load conditional branches only when their trigger is present.

**Conditional branch routing**:

| Trigger | Load |
|---|---|
| `pptx_structure.mode: structured` | [`executor-structured.md`](./executor-structured.md) |
| Any data chart, chart catalog selection, or text-grid table | [`executor-chart.md`](./executor-chart.md) |
| A page will use a preset pattern fill or evaluate native chart/table replacement | [`native-data-interface.md`](./native-data-interface.md) before deciding eligibility or emitting metadata |
| Any image or formula resource, including template-bundled images | [`executor-image.md`](./executor-image.md) + [`image-layout-patterns.md`](./image-layout-patterns.md) |
| Any `Status: Sourced` web image | [`executor-web-image.md`](./executor-web-image.md), after `executor-image.md` |
| Speaker notes generation after all SVG pages pass | [`executor-notes.md`](./executor-notes.md) |

> Narrative skeleton and visual aesthetic come from this deck's locked files under [`modes/`](./modes/_index.md) and [`visual-styles/`](./visual-styles/_index.md). Technical constraints are in [`shared-standards-core.md`](./shared-standards-core.md).

**Hard rule — complete page SVG**: Every visible object intended for the exported slide MUST exist in the final page SVG or be explicitly referenced by it. Templates and `spec_lock.md` guide construction; they are not export-time overlays for missing visible content.

**Hard rule — flat PowerPoint structure**: Free-design, brand-only, and `template_reuse_scope: style` projects use `pptx_structure.mode: flat`: write no root Master/Layout identity, `data-pptx-layer`, or `data-pptx-placeholder`; every visible object remains Slide-local, and the root declares exactly one canonical `data-pptx-page-role` (`cover` / `toc` / `section` / `content` / `ending`). A `style` template supplies colors, typography, decoration, and rhythm as style input without creating per-page prototype mappings. Export materializes one clean project-owned Master plus one Blank Layout from the current lock. Add `data-pptx-role` only to structural page-frame objects whose package, page-number, or animation behavior is not already expressed by specialized metadata; the marked element uses a stable unique `id`. See [`semantic-svg.md`](./semantic-svg.md).

**Hard rule — supported PPTX route**: The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter. Step 7.2 still generates `svg_final/` as a mandatory self-contained visual preview that may be inserted as an SVG picture. Do not treat PowerPoint's manual Convert-to-Shape operation as an authoring target or compatibility requirement.

> Note: this rule covers page design only. Speaker notes, animations, transitions, narration, and direct native-PPTX workflows retain their separate artifacts and package-level processing.

---

## 1. Effect Capability Discovery

**Reference — not a constraint**: Scan this menu for treatments that support the locked style and hierarchy. After selecting one, load [`svg-effects.md`](./svg-effects.md) before authoring it.

| Visual need | Available construction |
|---|---|
| Color / material | alpha paint, gradients, translucent overlays |
| Elevation | shadow, glow, explicit highlights |
| Image integration | scrim, vignette, brand wash, clipping, faux glass |
| Line / type | dash/cap/join, markers, gradient stroke; tracking, outline, alpha/gradient text |
| Space / constructed style | transform/reuse, curves/arcs, hand-drawn, ink/Riso, halftone, isometric, paper cut |

**Hard rule — discovery does not expand compatibility**: Follow `svg-effects.md` syntax and fallbacks; unsupported blur, blend, mask, dense texture, or skew remains baked/alternative-only.

---

## 2. Design Parameter Confirmation (Mandatory Step)

Before the first SVG page, output a confirmation listing: the compact communication objective, canvas dimensions, body font size, color scheme (primary/secondary/accent HEX), font plan, and the live-preview URL reported by the launcher. If the preview launch failed, state that failure before generating SVGs instead of silently proceeding. Prevents purpose/spec/execution drift.

### 2.1 Execution context validity (Mandatory)

- **Valid**: if the exact complete Design Spec and lock remain in the unchanged, uncompacted active context, reuse both for every page. Do not reread or poll them.
- **Invalid**: fresh/resumed/restarted execution, compaction/summary-only recovery, or an external/unknown change requires one complete read of `design_spec.md`, then `spec_lock.md`, plus triggered references/template inputs. Mid-deck recovery also reads the latest completed SVG and, when images are used, current image metadata.
- **Uncertain**: consult the retained lock first, then only the owning Design Spec fragment; use sources only for facts. Design Spec remains upstream on conflict.

**On-demand page-context diagnostic**: only for explicit telemetry/debugging or an unresolved page/template/chart path-SHA question; never as a pre-page gate:

```bash
python3 skills/ppt-master/scripts/project_manager.py page-context <project_path> P<NN> [--record-usage]
```

Consume stdout directly; stop on non-zero exit. The projection is derived, not authoritative. Use `--record-usage` only for measurement.

**Same-context repair**: in a valid uncompacted context, a bounded repair that preserves roster/order/identity/communication needs only affected Design Spec/lock fragment readback plus `project_manager.py validate`. Any broader or invalid-context repair requires the complete reads above.

**Hard rule — exact page roster**: `design_spec.md §IX` is the ordered queue: one final slide per entry, with the same id/order. The UI range no longer applies. Never add, drop, merge, split, or reorder; repair/reconfirm the Design Spec first.

**Hard rule — selection vs realization**: use Strategist-selected content, resources/paths, chart/layout keys, core fonts, palette anchors, icons, and crop boundaries. Adapt realization, never selection, except sparse local font/color garnish allowed below. Missing or unresolved material stops execution and returns to Strategist-owned acquisition/failure recovery; never search, generate, download, sync, invent, or substitute it. Selection changes require upstream repair.

Use named lock roles literally when that role applies, and use optional `Template Application` from the retained Design Spec. Choose contextual page-local values from the Design Spec, style, content, and current composition rather than forcing every object into a lock row. A page-context delta overrides neither facts nor constraints. Deprecated `page-context --bundle` is a compatibility no-op.

**Source verification**: §IX owns the complete page brief; the page delta does not carry the source corpus. Read sources only to resolve listed `Fact IDs` or verify required claims, quotes, names, or data. Do not add facts, claims, or selected content. Return underspecified blocks for Design Spec repair.

**Per-page communication trace**: Read `communication.objective`, `communication.core_message`, and the current §IX `Core message` + `Audience move` before choosing composition. The page must advance the compact objective and move the audience as authored in §IX; the global core message remains the deck-wide north star. A page that cannot state this movement is an upstream outline defect — surface `warning: P<NN> has no communication move` instead of compensating with decorative layout. Do not invent a new purpose, ask, or outcome at execution time. Structural pages may advance the contract by establishing relevance / tension / decision frame or by completing the final commitment; they are not exempt from having a reason to exist.

**Per-page reading-mode check**: Read `communication.consumption_mode` before choosing the page's composition. Apply it together with the authored §IX block texture and `page_rhythm`:

| `consumption_mode` | Page execution |
|---|---|
| `text` | Make the visible page independently understandable. Preserve complete prose, explicit labels / captions / sources, tables, and necessary detail; use bullets only for genuinely parallel or ordered items. |
| `balanced` | Keep the primary claim and its evidence on the page; let notes add interpretation and transitions. Mix prose, structured evidence, and necessary lists according to their semantic relationship. |
| `presentation` | Make one claim and one dominant visual expression legible at projection distance. Keep visible copy concise; put explanation and transitions in notes instead of creating paragraph dumps or compressed bullet prose. |

§IX and sourced facts remain authoritative. Use its wording when it works; adapt it when presentation benefits while preserving intent, necessary content, and explicit literal requirements. Never drop or invent facts to force a mode. When the authored texture materially conflicts with the lock, render the least-destructive faithful composition and surface `warning: P<NN> content texture conflicts with consumption_mode <value>` as an upstream outline issue; do not encode this subjective judgment in the checker.

**Per-block expression**: render each `design_spec.md §IX Content` block in its written texture — a full-sentence block as wrapped prose, a fragment/label block as bullets/keywords. **Never split a full-sentence block into a bullet list** — splitting loses the information that the block was continuous reasoning, not a set of parallel points; not because a bullet lays out easier, and not because an inherited template slot is shaped as a list. If a block carries no clear texture, infer the mode from its wording and the page layout.

- **Hard rule — one paragraph, one text frame**: use one `<text>` per prose paragraph, never one sibling `<text>` per visual line. Keep the first line as direct text; each later wrap is a direct `<tspan>` that repeats the parent `x`, keeps its effective font size, and uses one positive relative `dy`. An all-`<tspan>` form may start with `dy="0"`. Choose consistent positive line spacing from the typeface, size, density, and reading distance; no fixed ratio overrides legibility or the selected style.
- **Template precedence**: when an inherited template slot is a bullet list but the §IX block is prose, the prose wins — widen or reflow the container to hold the paragraph, or drop that card; do not pour the sentence back into the list slot.
- **Mode precedence**: the locked mode shapes voice / register, not §IX's authored titles or page order. When a `§IX` title is a user-authored topic label, keep it — do not upgrade it to an assertion just because the mode (e.g. `pyramid`) favors them; mode title-tendencies apply only to AI-drafted titles.

> Note: block-level phrasing, applied *within* the page's `page_rhythm` density (below), not against it.

**Missing `spec_lock.md` or `design_spec.md`** → stop before drawing and report the missing gate artifact. Recover through [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §3; do not silently downgrade. A failed on-demand `page-context` diagnostic is also not evidence that a required planning artifact may be bypassed.

**Missing field in an existing lock**: follow [`failure-recovery.md`](../workflows/governance/failure-recovery.md) §2.

**Execution anchors and contextual values**:

- Icons may use any SVG already prepared under `<project_path>/icons/`. `icons.library` records the Strategist's primary bundled style choice and `icons.inventory` records its planned selection; neither is an execution whitelist over project-local assets.
- Core color roles retain their meaning. Derive tints, shades, alpha, gradients, and effects; preserve natural asset colors; and use sparse page-local accents for differentiation/ornament. They must not become a competing or recurring palette.
- Resolve structural families by role: exact `<role>_family` first, then `title_family` for title roles or `body_family` for other unoverridden roles, then legacy `font_family`. Never flatten declared role overrides. A sparse export-safe accent family may style short non-structural display/ornament only—never title/body/data/annotation. Recurrence requires upstream selection.
- Font sizes use the named `typography` role values as deck-wide anchors. Map every structural text item to a declared role before drawing; never inherit a template placeholder size. Start from the anchor, then use composition and content fit to adjust that occurrence by at most `±2`px. Keep same-page peers consistent and preserve the role hierarchy; bounded adjustment does not create a new role.
- **Core message ≥ `body`**: map the page's primary claim to declared `lead` / `subtitle`, never below the current body treatment. Footnotes, page numbers, and credits use declared `footnote` / `annotation`; do not invent a smaller role.
- **Write unitless px, with at most two decimals.** Structural and mapped-role text uses only its anchor or a value within its `±2`px band; the sparse display-size exception is defined separately below. Do not substitute familiar pt-style numbers or emit long precision tails.
- **Sparse display-size exception**: a short non-structural Hero/Display element may use one undeclared size outside all anchor bands at most twice across the deck without a lock row. The third occurrence makes that size recurring: stop and return to Strategist to name the role in the Design Spec and `spec_lock.md`, then read back and validate the affected fragments before reuse. This exception never applies to titles, body copy, subtitles, annotations, footnotes, captions, data labels, or card copy, and nearby sizes must not be introduced to imitate one recurring treatment.
- **Outside-band recovery**: for structural text, reflow geometry and use the declared role band locally. For a sparse display occurrence, keep the unitless value and verify that its deck-wide count remains at most two. Never flatten a justified distinction or add a role merely to silence the checker. Mirror pages preserve exact source typography as inherited input.
- Images MUST reference files listed under `images`; no invented filenames
- Formula PNGs are images with `Acquire Via: formula`; place a `Rendered` file only from its listed path, use the normal placeholder for `Needs-Manual`, and never recreate the formula as text.

Return upstream before any derived/accent identity becomes recurring or structural, or when an undeclared display size reaches its third occurrence, then update the retained context under §2.1. Local garnish, same-role `±2`px adjustments, and at most two sparse display-size occurrences need no lock row. Never expand the lock to silence a comparison. New icon acquisition, images, structural fonts, role anchors, and resources keep their preparation/role rules.

**Per-page layout rhythm — `page_rhythm` section**:

Before drawing each page, look up its entry in `page_rhythm` (key format `P<NN>` matching the page index in §IX of `design_spec.md`) and apply the corresponding layout discipline:

| Tag | Layout discipline |
|-----|-------------------|
| `anchor` | Structural page (cover / chapter / TOC / ending). With `template_reuse_scope: mirror`, follow the selected prototype verbatim except visible text values. With `layout`, retain the selected structure system while realizing the page's §IX intent. With `style` or free design, realize §IX directly — for the cover deliver its `Cover impact` and for a closing page its `Closing impact`, never a default centered title + subtitle or generic "Thank you" sign-off. |
| `dense` | Information-heavy. Card grids, multi-column layouts, KPI dashboards, tables, and charts are all permitted. This is the baseline behavior. |
| `breathing` | Low-density impact page. Avoid **multi-card grid layouts** — do not organize content as multiple parallel rounded containers (3-card row, 4-card KPI grid, 2×2 matrix rendered as cards). Use naked text blocks, dividers, whitespace, or full-bleed imagery as the content structure. Single rounded visual elements (hero image corners, callouts, tags, one emphasis block) are fine — the rule is about grid structure, not about the `rx` attribute. Proportions follow information weight (not a preset ratio). Typical forms: hero quote, single large number with one-line interpretation, full-bleed image with floating caption, section transition. |

> Without rhythm variation, every page defaults to card grids (the "AI-generated" look). Context recovery follows §2.1.

**Missing or empty `page_rhythm` section — fixed compatibility default** → emit `warning: spec_lock.md missing/empty page_rhythm — defaulting all pages to dense` once, fall back to `dense` for all pages.

**Tag not found for current page — fixed compatibility default** → emit `warning: spec_lock.md page_rhythm tag not found for P<NN> — falling back to dense` once per deck (aggregate; do not repeat per page), fall back to `dense`. Do not invent a tag.


---

## 3. Execution Guidelines

- **Proximity**: group related elements with tight spacing; separate unrelated groups
- **Element grouping (Mandatory)**: wrap each logical Slide-local body unit in a descriptive, page-unique top-level `<g id>`. Every visible direct root `<g>` declares root-coordinate `data-pptx-bounds="x y width height"`; frame/native coordinates do not replace it, and placeholder bounds also supply the slot frame. Nested groups need no bounds and any such values are ignored. Checker compares root bounds with the `viewBox` and recursively checks only estimable text against its root module: through `1px` is ignored, through `5%` warns, above `5%` fails per side. Images, shapes, paths, `<use>`, effects, and object frames remain geometrically free. Flat pages use ordinary groups; structured slots already qualify, while titles, direct Master/Layout atoms, and canvas-level static framing may remain root primitives. On flat pages, give a root background image or full-canvas scrim/decoration rectangle a stable `id` plus `data-pptx-role="background"` / `"decoration"`; never wrap it only to silence the advisory.
- **Spec adherence**: follow color, layout, canvas format, and typography in the spec
- **Template structure**: inherit the native visual framework only for `template_reuse_scope: mirror|layout`; `style` uses the flat route
- **Main-agent ownership**: SVG generation must run in the main agent (not sub-agents) — pages share upstream context for cross-page visual continuity
- **Generation rhythm**: P01 → first-page gate → uninterrupted remaining pages → final gate, in one context without batches or mid-run checker calls.
- **Fact provenance**: when a §IX page lists `Fact IDs`, resolve each ID from `sources/*.facts.json` and keep the claim/value unchanged. Render a compact source footnote using the source name and a short URL/domain when space permits; state the attribution naturally in speaker notes. When §IX says `Data class: scenario`, place a visible localized `Scenario data` / `情景数据` label adjacent to the affected KPI/chart and state naturally in notes that the number is illustrative. Never attach an external fact ID to scenario data or let an unlabeled invented KPI look factual.
- **Default — stage each page with the style's composition geometry (may override when the content genuinely calls for a plain grid)**: an SVG page is a canvas, not a DOM. Before defaulting to stacked rounded-rect cards or uniform equal columns, pick one page-scale move from the locked visual style's §1 `Composition geometry` (a bleed shape, diagonal split, oversized numeral, orbit rings, …) to stage the page's primary zone. Card grids are one option among many, not the house layout.
- **Containers are structural**: cards and grids express grouping, hierarchy, or capacity, not a house style. Preserve meaningful template frames; restyle radius, fill, stroke, and depth from the active Design Spec and `spec_lock.md`. Chart-catalog adaptation is owned by [`executor-chart.md`](./executor-chart.md); preview effects never override project styling or structural roles.
- **Reference — prefer semantic geometry over preset stacks**: for relationships such as ascending, converging, breaking through, or stacking, consider one page-specific polygon/path that expresses the relationship before stacking generic arrows. This does not override §3.0 when one literal stock shape is the semantic object.
- **Reference — create depth with restraint**: use rhythm, spacing, typography, accent bars, and subtle tints before shadows. Reserve lift for a few genuinely floating elements; keep peer grids, dividers, and body containers flat.
- **Phased generation** (recommended):
  1. **Visual Construction Phase**: generate all SVG pages sequentially for visual consistency. Use layout judgment for chart marks during the draft. **MUST embed plot-area markers** per [`executor-chart.md`](./executor-chart.md) §2.1 on every §IX-planned data-chart page — coordinate calibration is a post-generation step (see [`verify-charts`](../workflows/stages/verify-charts.md)) that depends on these markers — and **native object metadata** per [`executor-chart.md`](./executor-chart.md) §2.2 on every planned native-ready object. **Reach for native presets** per §3.0 as you draw each page: a block arrow, chevron, banner/ribbon, callout, standard flowchart node, or star is authored through `preset_shape_svg.py` at draw time — decided by the object's intent as you create it, never by scanning finished paths, and never committed to a bare `<path>`/`<polygon>` when a preset expresses it (a gradient fill/stroke or a pattern fill is the one paint exception — keep those ordinary SVG). **First-page gate (Mandatory)**: after completing the first page, run `python3 scripts/svg_quality_checker.py <project_path> --stage first-page --json` without output filtering. Review the whole P01 issue set, make one consolidated edit pass for every error and any selected warnings, then perform one verification rerun. If it still fails, treat that complete output as the next batch; never check between individual fixes. After it passes, draw P02 through the last page without checker calls.
  2. **Quality Check Gate**: only after every planned SVG exists, run `python3 scripts/svg_quality_checker.py <project_path> --stage final --json` on `svg_output/` without `tail` / `head` / `grep` filtering. One run already reports all pages. Review its complete issue set, fix every `error` plus any selected advisory warnings in one consolidated edit pass, then perform one verification rerun. If it still fails, its complete output begins the next batch cycle; never use checker calls to discover or fix one next issue at a time. Every `warning` is advisory: it never sends the page back for required modification, never authorizes automatic rewriting of compatible user syntax, and needs no acknowledgement/disposition line. Recommendation warnings describe the generated-SVG default; fidelity/quality warnings may be surfaced when material, while the existing input remains releasable. Prototype-identical diagnostics are recorded as `inherited`, source conversion losses as `source-import`, changed/new advisories as `introduced`, and release failures as `blocking` in `validation/svg_quality_report.json`. If release truly depends on a condition, it belongs in `errors`. On success, use the exit status and terminal summary; do not open or `cat` the complete JSON into model context. If terminal output is truncated on failure, read only the relevant issue arrays from the report written by that same run. Do NOT defer error handling to after `finalize_svg.py` — finalize rewrites SVG and masks some violations.
  3. **Logic Construction Phase**: after SVGs pass the quality check, batch-generate speaker notes for narrative continuity.

### 3.0 Native Preset Shape Selection

**Reach for a native preset whenever one expresses a complete object — this is
the default, not the exception.** Block arrows, chevrons, banners / ribbons,
callouts, flowchart nodes, stars, and other Office symbols should be **authored
as presets** via `preset_shape_svg.py`, not drawn as plain `<path>`s or faked
with rectangles: presets are what give the slide real PowerPoint shapes with
adjustment handles and the designed, non-flat-card look. When a page calls for
one of these, use the preset. Apply the decision gate in
[`native-shape-authoring.md`](./native-shape-authoring.md) to pick the right
shape and to keep only the exceptions below as ordinary SVG.

| Decision | Action |
|---|---|
| Plain rect / symmetric round rect / circle / ellipse | Keep the ordinary SVG primitive; it is already natively editable. |
| Exact single-preset match | Call `preset_shape_svg.py render` and paste its complete stdout fragment into the current hand-authored SVG. |
| Stock shape that needs a gradient fill/stroke or a pattern fill | Keep ordinary SVG — the helper paints `none` or a solid HEX on both fill and stroke only ([`native-shape-authoring.md`](./native-shape-authoring.md) §5). |
| Page-specific, compound, organic, branded, icon, or data geometry | Keep ordinary SVG path/polygon geometry. |
| Similar-looking contour only | Never guess; keep ordinary SVG. |

This automatic decision applies only before drawing a new object. Do not scan
existing SVG, classify path contours, or upgrade ordinary SVG during export.

**Hard rule**: do not hand-write `data-pptx-authoring`, `data-pptx-prst`,
`data-pptx-frame`, adjustment metadata, or registry paths. The helper generates
one compact atomic `<g>` from the shared 187-shape registry, with semantic
metadata and base paint written once. Rerun the helper when geometry or paint
changes; never edit one of its direct paths.

For chart-template and diagram authoring, thin relationships use ordinary
`<line>` / supported open `<path>` geometry with registered arrow markers;
solid directional blocks use ordinary `shape` presets such as `rightArrow` or
`chevron`. Do not select a connector-family preset merely because two nodes are
related, and never hand-add endpoint/site metadata. Connector-family presets
remain available only for an explicit request for a standalone unconnected
`p:cxnSp`; imported Connector topology stays under the preserve/mirror contract.
`actionButton*` presets provide visual geometry only, not actions or hyperlinks.

**Hard rule — narrow helper scope**: the helper prints one shape fragment to
stdout. It does not write a page or choose layout. Read the fragment and insert
it through the normal `apply_patch` page edit; never redirect, loop, or batch it
into `svg_output/`.


### SVG File Naming Convention

Format: `<NN>_<page_name>.svg` (two-digit number from 01; name matches the deck's language and the page title in the Design Spec).

Examples: `01_封面.svg` / `02_目录.svg` / `03_核心优势.svg`; `01_cover.svg` / `02_agenda.svg` / `03_key_benefits.svg`.

---

## 4. Icon Usage

Strategist chooses at most one primary bundled stylistic library and may select `simple-icons` alone or alongside it; Executor implements from the complete prepared project-local pool. Library details and selection rules: [`../templates/icons/README.md`](../templates/icons/README.md). This section defines placeholder syntax.

> **Prepared-project boundary.** Any SVG already under `<project_path>/icons/<lib>/` is valid execution material, whether selected from a bundled library or supplied by the user, a template, or an import workflow. New authoring must resolve there. The global fallback in `finalize_svg.py embed-icons` is legacy compatibility, not permission for Executor to discover or use an unprepared global icon.

> **Icon identifiers are case-sensitive filenames.** Every `data-icon` value must use the exact project-local relative basename (`tabler-outline/award`, never `tabler-outline/Award`). Strategist records its planned bundled choices in `spec_lock.md`; Executor need not add other already-prepared project-local icons to that inventory. Custom identifiers preserve the custom file's exact case; the pipeline never silently lowercases names.

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

**Missing project-local icon** → return to Strategist's preparation / `icon_sync.py` gate. Do not search the global library, select an alternative, or copy a candidate in Executor.

**Hard rule — prepared assets**: Executor may freely combine project-local icons, regardless of namespace or style. It may not acquire a new icon or treat a globally resolvable file as prepared material.

---

## 5. Font Usage

Structural typography anchors come from `spec_lock.md typography`. Use an exact `<role>_family` when declared; title roles otherwise use `title_family`, and body/support roles otherwise use `body_family`. `font_family` is the legacy/default fallback, not a reason to erase role differences. Sparse accent families follow §2.1; all structural text uses selected families. LaTeX formulas rendered by Strategist are PNG images, not a `code_family` role.

**Missing required field — `typography.font_family`** → stop and return to Generate Step 4 / [`strategist.md`](strategist.md) §6.2 to repair `spec_lock.md`; do not infer a stack from `design_spec.md`.

**Hard rule**: every SVG `font-family` stack MUST resolve to a pre-installed exported Latin / EA typeface; use the Strategist §g safe set for locked roles and §2.1 for sparse display exceptions. PPTX has no runtime fallback — missing fonts degrade to Calibri.

---

## 6. Completion Routing

After every SVG page passes the final quality check, load [`executor-notes.md`](./executor-notes.md) and complete its notes contract before entering the route's Step 7.

## 7. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export**: Follow [`generate-pptx.md`](../workflows/generate-pptx.md)
Step 7. That workflow owns the serial commands, gates, success criteria, and
published artifacts; [`svg-pipeline.md`](../scripts/docs/svg-pipeline.md) owns
tool-specific flags and behavior.

`svg_final/` may be opened directly or manually inserted into PowerPoint as an SVG picture. It is not a second PPTX route. Use `-s final` only for converter diagnostics; release exports use the default `svg_output/` source. Manual Convert-to-Shape behavior is unsupported.
