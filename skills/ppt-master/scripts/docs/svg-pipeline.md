# SVG Pipeline Tools

> **Maintenance boundary**: post-processing modules serve both the on-disk
> `svg_final/` preview and in-memory native PPTX conversion. Check both
> consumers before changing or removing a step.

These tools cover post-processing, SVG validation, speaker notes, recorded narration, and PPTX export.

The supported delivery contract has one PPTX path: `svg_output/` → the project SVG-to-DrawingML converter → native PPTX. The mandatory `finalize_svg.py` step separately creates self-contained `svg_final/` visual previews, which may be opened directly or inserted into PowerPoint as SVG pictures. There is no SVG-image PPTX output, and PowerPoint's manual Convert-to-Shape operation is unsupported.

## `svg_authoring_view.py`

Create a lightweight editable authoring IR bundle from one PPTX-imported SVG or
a directory of imported SVGs:

```bash
python3 scripts/svg_authoring_view.py <svg-file-or-directory> -o <output-dir> \
  --projection-kind layered
```

The operation is non-destructive and refuses existing output files unless
`--force` is explicit. It never writes back to the source SVG. The JSON report
on stdout records original/projected byte counts and removals by category. The
output directory contains the editable SVGs, one model-readable
`authoring_summary.json`, and one tool-only `authoring_manifest.json`.

The projected copy:

- removes embedded `txbody` metadata;
- removes hidden native geometry carriers while retaining and unwrapping their
  visible preview geometry;
- removes source-object identity/style/hash attributes that are only useful to
  an exact import round trip;
- keeps visible paths, text, images, stable ids, Master/Layout root markers,
  selected native-shape intent, and a document-local `data-pptx-source-ref` on
  each imported logical object;
- rewrites relative local asset references for the projection's new location;
- compacts imported model-facing frames and safe transform page coordinates to
  at most two decimals.

The summary stores the current SVG roster plus compact per-file canvas, size,
text, image, vector, placeholder, icon, and source-ref counts. Models read the
summary and editable SVGs; they do not read the machine manifest. The manifest
stores relative source/authoring filenames, source and initial authoring hashes,
and source element paths. It deliberately does not copy the opaque payload.
The authoring bundle is the editable source for template creation; the complete
imported SVG remains immutable native-payload backing. Final
`templates/*.svg` files are materialized and validated from that pair. The IR
directory itself is not a supported direct input to `svg_to_pptx.py`.

Regenerate the summary after direct edits that do not pass through one of the
in-place normalization tools:

```bash
python3 scripts/svg_authoring_view.py <authoring-dir> --refresh-summary
```

This projection is separate from canonical preset authoring. New project SVGs
and project-owned templates use the compact authored form: one atomic
`<g data-pptx-authoring="preset">` owns the preset intent and base paint, with
the registry-generated visible `<path>` layers as direct children. Quality
check and export rerender the locked registry to validate that group, so the
compact form has no hidden carrier, preview wrapper, or serialized preview
fingerprint. `pptx_to_svg.py` continues to emit the expanded carrier/preview
evidence required for import and round-trip decisions. The normative boundary
is owned by [`shared-standards-core.md`](../../references/shared-standards-core.md) §1.5, with
authoring guidance in
[`native-shape-authoring.md`](../../references/native-shape-authoring.md).

## `compact_svg_coordinates.py`

Compact safe model-facing page-space coordinates without rewriting unrelated
SVG formatting:

```bash
python3 scripts/compact_svg_coordinates.py <svg-file-or-directory>
python3 scripts/compact_svg_coordinates.py <template-directory> \
  --inplace --keep-native-frames
```

The default run is a dry-run JSON report. `--inplace` atomically replaces only
changed SVG files. The shared create-template final pass uses
`--keep-native-frames`: it compacts `data-pptx-placeholder-bounds`, translation
values, rotation centers, and matrix `e/f`, while preserving canonical
authored-preset or inline native frames. `svg_authoring_view.py` separately
compacts imported model-facing frames because unchanged mirror refs can recover
their exact coordinates from immutable lossless backing.

The compactor never rounds path/points geometry, normalized crop or nested
`viewBox` ratios, gradient offsets, opacity, scale arguments, rotation angles,
or matrix `a/b/c/d` coefficients. Type A mirror materialization invokes the
same compactor before native-record externalization; `standard` and `fidelity`
use the shared final pass before template validation.

## `extract_svg_assets.py`

Factor large vector subtrees out of lightweight authoring IR documents and
replace them with compact `<use data-icon>` references:

```bash
python3 scripts/extract_svg_assets.py <layered_svg_dir> \
  --icons-dir <icons_dir> --icon-namespace imported \
  --inplace --id-prefix layered
python3 scripts/extract_svg_assets.py <flat_svg_dir> \
  --icons-dir <icons_dir> --icon-namespace imported \
  --reuse-inventory <layered_inventory.json> \
  --inplace --id-prefix flat
```

The first pass records a source fingerprint before namespacing each extracted
asset's internal ids. The second pass reuses a fingerprint-matched asset and
writes no duplicate SVG file. Unmatched flat-only subtrees still extract
normally. Use `--clean-stale` on both import-workspace passes to remove stale
generated files for their respective prefixes. In create-template workspaces,
`imported` is the fixed namespace: assets live once under `icons/imported/`, and
the working SVGs reference them as `data-icon="imported/<name>"`. Inventory
entries retain source refs from each extracted subtree, allowing expansion to
reconnect the authoring-manifest mapping. A rerun on an
already rewritten namespaced projection inventories those references and does
not progressively extract their remaining parent or sibling geometry. An
in-place pass over an authoring bundle refreshes `authoring_summary.json`
automatically.

## `mirror_template_materialize.py`

Compile one Type A PPTX import workspace into a deterministic structured mirror
template after the layered authoring IR has been reviewed and edited:

```bash
python3 scripts/mirror_template_materialize.py \
  <import_workspace> <empty_template_workspace>
```

The command treats `<import_workspace>/authoring-svg/` as the sole editable
source. It reads the tool-only layered authoring manifest internally and
validates it against immutable lossless SVG
hashes, source PPTX hash, complete Master/Layout/Slide graph, inheritance
visibility facts, source-ref closure, and extracted-vector inventory before it
writes anything. It refuses a non-empty destination and stages the whole result
before atomic publication, so a failed preflight cannot leave a partial
template.

Materialization preserves source page order and emits one definition-only
`layout_<layout_key>.svg` for every source Layout unused by all source Slides.
It mechanically expands fixed Master/Layout group wrappers into direct atoms,
rehydrates only unchanged converter-supported Slide-local/slot refs, keeps the
current SVG fallback for edited refs, preserves explicit text hard breaks, and
removes every IR-only source ref. Imported axis-flipped groups retain their
geometry reflection while descendant SVG text receives a matching
counter-reflection, preserving PowerPoint's upright glyph appearance in browser
previews. Supported opaque `p:txBody`,
relationship-free `p:style`, and `a:custGeom` payloads are deduplicated into
`templates/native_payloads.json.gz`. Repeated native restoration attributes
are stored there as short `data-pptx-native-ref` records; page and
imported-vector SVGs retain only those record ids and content-hash payload
references. The native record referenced by an imported text placeholder
carrier owns its authoritative source frame, so the Slide-local frame can
differ from reusable Layout bounds without restoring long exact coordinates
inline. Structural Master/Layout, placeholder, layer, and editable-object
fields remain inline. Source `p:sldLayout@showMasterSp` and
`p:sld@showMasterSp` facts become canonical root
`data-pptx-show-master-shapes` and
`data-pptx-show-inherited-shapes` booleans.

Checker, template-structure validation, and export hydrate both store layers in
memory; legacy inline payload and v1 payload-only stores remain readable.

The published `ppt-master.template-execution-manifest.v1` roster points to one
compact `ppt-master.template-text-slots.v2-min` sidecar per prototype. Each text
slot contains only `selector`, `role`, `current_text`, `text_segments`, and
`tspan_count`; a top-level tool hash covers its selectors and immutable
text/tspan topology and attributes. A current-page mirror bundle still includes
the complete prototype SVG. Page projection recomputes the hash and projected
fields against that prototype, then strips the hash from model context. The
model chooses semantics and edits only existing visible text values, while
checker and structured export validate output attributes, text/tspan topology,
and referenced-resource hashes against the prototype. Runtime page projection
accepts legacy v1 text-slot sidecars and reduces them to v2-min without
rewriting the workspace.

The output routes reusable vectors once to `icons/imported/`, bitmaps to
`images/`, and other referenced files to `templates/assets/`. The JSON report
reports payload occurrence, native-record, unique-byte, and compressed-store
counts and is written to stdout only. The command intentionally does not create
`templates/design_spec.md`; Template_Designer writes the package-specific rules
and page roster after materialization. This compiler is for Type A mirror materialization,
not `standard` / `fidelity`, loose Type B SVGs, ordinary generation, finalize,
or export.

## `extract_svg_pictures.py`

Normalize one deliberately selected complex SVG object into one PowerPoint
picture. The command accepts exact `<g id>` values only, writes each group as a
tight standalone SVG asset, embeds its local image/CSS dependencies, and
replaces the source group at the same parent index with one `<image>`. Native
export therefore emits one `p:pic` backed by SVG media.

```bash
python3 scripts/extract_svg_pictures.py \
  "<workspace>/authoring-svg/<layered_svg_file>.svg" \
  --select "<group_id>" \
  --resource-root "<workspace>" \
  --images-dir "<workspace>/picture-assets" \
  --inplace
```

Imported PowerPoint groups normally provide `data-pptx-frame`, which is used
as the picture bounds. For a large standalone SVG without frame metadata, the
tool measures the selected group with Playwright; use repeated
`--bounds ID=x,y,width,height` values when browser measurement is unavailable
or when effect overflow needs an explicit frame. `--padding` expands the
chosen bounds. The generated `*_picture_asset_inventory.json` records the
bounds source, asset hash, copied definition ids, and embedded local resources.
Nested selections are accepted only through metadata-only `<g>` ancestors.
When an ancestor carries a transform, style, clip, opacity, or other visual
attribute, select that outer group instead; this prevents applying the ancestor
effect once inside the SVG asset and again to the replacement `<image>`.
Scripts, `foreignObject`, SVG animation, remote resources, and external SVG
fragment references fail closed; local image/CSS resources must stay inside
the declared `--resource-root` and are embedded into the asset.
An in-place rewrite inside an authoring bundle refreshes
`authoring_summary.json` automatically.

This operation belongs only to an explicit `create-template` normalization
decision in `standard` or `fidelity` mode. It does not choose groups, detect
repetition, infer a Master/Layout, or run during ordinary import, free
generation, mirror materialization, finalize, or export. Placeholder, native
single-shape, table/chart, icon-placeholder, and authored-preset groups are
rejected because they already own a different semantic route.

Do not confuse this tool with `extract_svg_assets.py`:

- `extract_svg_assets.py` is a model-readability optimization. It replaces
  heuristic vector runs with `<use data-icon>`, then re-inlines them before
  export so the PPTX still contains native shapes.
- `extract_svg_pictures.py` is an explicit representation change. It replaces
  only named groups with `<image>`, so each result intentionally remains one
  editable PowerPoint picture rather than individually editable paths.

## Recommended Pipeline

Run these steps one at a time. Wait for each command to exit successfully before
starting the next command.

```bash
python3 scripts/total_md_split.py <project_path>
```

After `total_md_split.py` exits successfully, run:

```bash
python3 scripts/finalize_svg.py <project_path>
```

After `finalize_svg.py` exits successfully, run:

```bash
python3 scripts/svg_to_pptx.py <project_path>
```

Do not start another post-processing command while the current command is still
running. The canonical gates and success criteria are owned by
[`generate-pptx.md`](../../workflows/generate-pptx.md) Step 7.

## `finalize_svg.py`

Unified post-processing entry point. This is the preferred way to run SVG cleanup.

It aggregates:
- `embed_icons.py`
- static same-document `<use>` expansion from `svg_to_pptx/use_expander.py`
- `align_embed_images.py` (`crop-images` / `fix-aspect` / `embed-images` aliases route here)
- `flatten_tspan.py`

`svg_final/` remains a required Step 7.2 artifact even though the native exporter reads `svg_output/`. It is the self-contained visual reference and may be manually inserted as an SVG picture.

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

```bash
python3 scripts/svg_to_pptx.py <project_path>
python3 scripts/svg_to_pptx.py <project_path> --native-charts-and-tables
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure structured  # deck/layout template override
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure flat  # free-design/brand-only override
# Template-import visual round-trip diagnostic only:
python3 scripts/svg_to_pptx.py <template_import_output> -s svg-flat
# Post-processed-source comparison diagnostic only (never a release export):
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> --no-notes
python3 scripts/svg_to_pptx.py <project_path> -t none
python3 scripts/svg_to_pptx.py <project_path> --auto-advance 3
python3 scripts/svg_to_pptx.py <project_path> --animation mixed --animation-duration 0.8
python3 scripts/svg_to_pptx.py <project_path> --no-merge   # strict line-fidelity mode (see below)
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
```

For generated-project narration, follow the
[`generate-audio`](../../workflows/stages/generate-audio.md) stage. It owns voice
selection, audio generation, and the narrated re-export workflow.

Behavior:
- Default output (default-flow mode, no `-o`):
  - `exports/<project_name>_<timestamp>.pptx` — native editable pptx (canonical output)
  - `validation/<project_name>_<timestamp>.report.json` — package postflight, quality-gate linkage, unresolved resource audit, and published part counts
  - `backup/<timestamp>/svg_output/` — copy of Executor SVG source, always written so the pptx can be rebuilt via `finalize_svg → svg_to_pptx` without re-running the LLM
- `exports/` contains only final PPTX deliverables; machine-readable quality and postflight reports belong in `validation/`.
- `finalize_svg.py` always creates `svg_final/` before export. This directory is the self-contained SVG visual preview; it is not packaged as a second PPTX.
- Explicit `-o/--output` changes the native PPTX destination and skips `backup/`; its postflight report still uses the output stem under the project `validation/` directory.
- Postflight reruns ZIP integrity and published Slide count. Internal relationships,
  structured-package validation, transitions, and animations are enforced before the
  builder publishes the PPTX and are reported as `enforced-at-build`, not as repeated
  postflight checks.
- `font_portability` warns only when a complete font stack contains generic CSS families
  and no concrete family name. A recommended stack such as
  `"Microsoft YaHei", Arial, sans-serif` does not warn merely because it ends with a
  generic fallback.
- Paragraph merging is enabled by default and trades some SVG line-layout fidelity for PowerPoint editability:
  - Default: mergeable paragraph blocks (same x, dy clustered around one base line-height) collapse into one editable text frame. Equal effective font sizes may join as flowing prose; a font-size change, list marker, or accepted larger gap starts a new `<a:p>` with precise `<a:lnSpc>` / `<a:spcBef>`. Resizing the box reflows text inside it without erasing those paragraph boundaries.
  - With `--no-merge`: every dy-stacked `<tspan>` becomes its own text frame — exact SVG line layout is preserved but a 12-line paragraph is 12 separate textboxes
  - Side effect: PowerPoint may wrap merged paragraphs to a different line count than the SVG source. Long body text (abstracts, multi-paragraph sections, reference lists) usually benefits from the default; pages with tight typographic alignment (covers, charts, tables) usually want `--no-merge`
  - Mergeable detection is conservative: only fires when the children form a clean paragraph block; mixed-layout `<text>` falls through to the default per-line path
- Native release export reads `svg_output/`. `-s final` is an explicit diagnostic override for comparing conversion behavior against post-processed SVGs; it does not change artifact ownership or create a supported release path.
- `svg_final/` may be opened directly or inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is outside the compatibility contract.
- On every SVG-authoring route, each file in `svg_output/` is the complete visible
  page-design source. Templates and locks may guide authoring, but finalize/export
  never use them to overlay visible content missing from the SVG. Notes, animation,
  narration, transitions, and direct native-PPTX workflows keep their separate
  inputs and package-level processing.
- For PPTX template-import workspaces, use `-s svg-flat` when you need a visual round-trip check. The layered `svg/` tree is the machine-readable template source and intentionally does not inline inherited master / layout decoration into each slide.
- Native mode is strict about unsupported visual SVG elements: if a visual element cannot be represented or safely preserved, export fails with the SVG file, element tag, and position instead of silently dropping content.
- Omitting `--pptx-structure` reads `spec_lock.md`. Free-design, brand-only, and `template_reuse_scope: style` releases declare `mode: flat`, omit Master/Layout mappings and SVG structure metadata, and materialize one clean project-owned Master plus one Blank Layout from the current lock. Deck/layout templates use `mode: structured` only for `template_reuse_scope: mirror|layout`, with complete unique `pptx_masters` / `pptx_layouts` rosters and one `page_pptx_layouts` assignment per page. A template-backed Layout definition may remain unused by pages and still register in the final package.
- On structured template routes, every page root repeats Master/Layout keys and picker names. Master/Layout fixed visuals are direct semantic atoms. Ordinary layer `<g>` elements are invalid; one validated compact authored-preset `<g>` emitted by `preset_shape_svg.py` is the sole group exception because it compiles to one native shape.
- On structured template routes, each normal slot is a direct root `<g id>` with semantic type, positive design-zone bounds, and exactly one compatible carrier. Composite `object` slots use explicit proxy binding; zero-slot Layouts are valid. Flat pages keep all SVG objects Slide-local.
- Flat export maps locked typography/colors into a clean project-owned theme/Master, removes stock content placeholders and unused built-in Layouts, retains only the standard date/footer/slide-number capability hooks, and keeps one Blank Layout without promoting Slide content. Structured export additionally creates one reusable Layout per declared key and reopens the package to verify the full Presentation → Master → Layout → Slide graph, fixed-object order, placeholder identities/bounds, carrier bindings, hidden proxies, and zero-slot Layouts.
- Template `page_layouts` remains input provenance. Strict preserves the prototype contract; adaptive retains its Master and may use a new Layout identity only when fixed Layout atoms or slot topology/bounds change.
- Legacy structured/template contracts using `baseline`, `template`, `preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled`/`utility`, direct atomic placeholders, or incomplete Master identity are rejected with a pointer to [`create-template`](../../workflows/create-template.md). Create a new workspace and generate new structured SVG pages; do not upgrade the existing project in place. Explicit flat free-design/brand-only projects intentionally omit Master identity.
- Native output uses content-hash media filenames, so identical images are reused and different images cannot overwrite each other by sharing a basename.
- `[Content_Types].xml` is generated from the actual media extensions written into the PPTX. Unknown media extensions fail unless Python's `mimetypes` can identify them.
- Native export writes to a temporary file first and publishes the requested PPTX only after conversion succeeds. A failed conversion does not replace the main output file.
- After publication, native export writes `validation/<output_stem>.report.json`. The report distinguishes authored Slides from internal Layout definitions, reruns ZIP integrity and published Slide-count checks, records slide/layout/master/notes part counts, labels relationship/structured/transition/animation validation as enforced at build time, links the final SVG quality report only when its SHA-256 source fingerprint matches the exact export inputs, and surfaces stale/unverified gates, unresolved template tokens, generic-only font stacks, and external image references.
- Before publishing structured template output, export reopens the temporary PPTX and validates the Slide → Layout → Master graph and registrations, Layout identity, placeholder identity, reusable bounds, and prompt/level-one sizes. A mismatch aborts publication. Flat release instead validates its single referenced Master/Layout shell and exact date/footer/slide-number hook roster before packaging.
- SVG clip paths are still restricted for authored SVGs, but nested crop wrappers generated by PPTX import are mapped back to native picture crop / geometry when possible.
- Speaker notes are embedded automatically unless `--no-notes` is used
- Recorded narration is opt-in:
  - `notes_to_audio.py` uses `edge-tts` by default, or a configured cloud TTS provider (`elevenlabs`, `minimax`, `qwen`, `cosyvoice`), and generates one audio file per slide into `audio/`
  - Narration text is read strictly from the matching `notes/*.md` file; the script only skips Markdown heading lines (`# ...`) and does not summarize, rewrite, or filter delivery notes
  - `--recorded-narration audio` prepares PowerPoint's "recorded timings and narrations": every slide must have matching `m4a` / `mp3` / `wav` audio, `ffprobe` must read every duration, and `--animation-trigger on-click` is rejected
  - `--recorded-narration audio` keeps speaker notes, embeds each matching audio file, and writes slide auto-advance timings from audio duration
  - Narration timing is merged into the existing slide timing DOM; object entrance rows and the resolved page transition are preserved rather than regenerated
  - `--narration-audio-dir audio` is the lower-level embedding path: it embeds whatever files match and allows partial audio coverage
  - Either narration flag names the default-flow export `<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports in the same directory
  - This is intended for direct PowerPoint video export with "Use recorded timings and narrations"
  - Long-audio import and automatic long-audio splitting are not supported; keep narration assets page-level
  - Voice choices can be listed with `python3 scripts/notes_to_audio.py --list-common-voices`, `python3 scripts/notes_to_audio.py --list-voices --locale zh-CN`, or provider-specific `--provider <name> --list-voices`
- Page transitions are controlled by `-t/--transition`; per-element entrance animations are controlled by `-a/--animation`
- Per-element animation applies to ordinary top-level SVG `<g id="...">` groups in z-order; aim for 3–8 Slide-local content groups per slide. Master/Layout atoms and slot groups are structural and excluded; exact id tokens remain a fallback only when explicit structural roles are absent
- An explicit `animations.json` group entry may override the marker-free legacy chrome-name heuristic. It cannot override `data-pptx-layer` or an explicit static role/placeholder marker
- Start mode is set by `--animation-trigger`, mirroring PowerPoint's Start dropdown: `after-previous` (default, cascade with `--animation-stagger` spacing on slide entry), `on-click` (presenter-paced), `with-previous` (all together on slide entry)
- `on-click` is for live presentations only; recorded narration rejects it because the tool does not generate object-level click timings
- Flat SVG roots without top-level groups fall back to at most 8 visible primitives; beyond that, animation is skipped on the slide
- Per-element animation defaults to `none`. `auto` is opt-in (`-a auto`) and maps
  effects from the group's SVG id: information-dense elements get a stable
  effect (chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade); image-like
  ids (hero/figure-/image/img-/kpi) cycle through a richer pool
  (zoom/dissolve/circle/box/diamond/wheel), while unmatched ids cycle through
  fade/wipe/fly/zoom.
- `mixed` (legacy) is deterministic: the first animated group on each slide uses `fade`, then later groups cycle through a larger 16-effect pool across the whole deck; `random` uses a stable seed from the effective deck input, and `--conversion-trace` records each resolved effect when enabled
- `--animation-duration` controls per-element entrance length (default `0.4`); `--animation-stagger` adds gap between elements in `after-previous` mode (default `0.5`)
- Optional object-level overrides live in `<project>/animations.json` or a path passed via `--animation-config`; build and validate them with `animation_config.py scaffold|validate`
- Animation configuration is strict: unknown effects/modes/triggers, invalid finite/range/order values, missing slides/groups, and structural-layer targets fail export without fallback or silent omission
- Generated export reads every slide back and verifies animation row order, trigger, shape target, resolved effect tuple, duration, and offset. Package validation then checks timing placement, `p:cTn` ids, and `p:spTgt` references before publication
- The animation writer does not emit `p:bldP` for groups or pictures. Direct-PPTX routes preserve source object animation and perform structural package validation only; they do not author effects
- The full registry, OOXML rules, and compatibility boundary are documented in [`pptx-animations.md`](./pptx-animations.md)

Dependency:

```bash
pip install python-pptx
```

## `total_md_split.py`

Split `total.md` into per-slide note files.

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/total_md_split.py <project_path> -o <output_directory>
python3 scripts/total_md_split.py <project_path> -q
```

Requirements:
- Each section begins with `# `
- Heading text matches the SVG filename
- Sections are separated by `---`

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
python3 scripts/svg_quality_checker.py examples/project/svg_output/01_cover.svg
python3 scripts/svg_quality_checker.py examples/project/svg_output
python3 scripts/svg_quality_checker.py examples/project
python3 scripts/svg_quality_checker.py examples/project --stage first-page
python3 scripts/svg_quality_checker.py examples/project --stage final --json
python3 scripts/svg_quality_checker.py examples/project --format ppt169
python3 scripts/svg_quality_checker.py --all examples
python3 scripts/svg_quality_checker.py examples/project --export
python3 scripts/svg_quality_checker.py path/to/template/templates --template-mode
```

Checks include:
- `viewBox`
- banned elements
- paint compatibility: unsupported values error; supported non-default spellings such as `rgba()` receive non-blocking recommendations for `#RRGGBB` plus explicit alpha
- line-break structure
- explicit Master/Layout/slot structure for reusable templates
- duplicate empty Layout contracts under different keys

Warnings are advisory: they require no modification or acknowledgement and do
not affect the command's zero exit status. Only errors block the quality gate.

`--stage first-page` resolves only the first authored SVG and permits an incomplete
future page roster. `--stage final` checks the complete project. With `--json`,
the final stage writes `validation/svg_quality_report.json`, while the first-page
stage writes `validation/svg_quality_first_page_report.json` so it cannot overwrite
the release gate (or use `--json-output`). The report separates
release failures (`blocking`), changed/new advisories (`introduced`),
prototype-identical diagnostics (`inherited`), and source-conversion losses
(`source-import`). It also fingerprints every checked SVG so postflight cannot
mistake a stale report for the current export gate.

Template mode accepts the same compact canonical preset groups as generated
pages: one atomic `<g data-pptx-authoring="preset">` with direct visible paths.
It validates those paths dynamically against the locked registry and does not
require an import-style carrier, preview wrapper, fingerprint, or a separate
source-payload opt-in marker. Exact syntax remains owned by the linked
standards rather than this pipeline overview.

## `svg_position_calculator.py`

Analyze and review supported chart coordinates after SVG generation.

Use this after `svg_quality_checker.py` passes, and only for chart types supported by this script: `bar`, `pie` / `donut`, `radar`, `line` / `area` / `scatter`, and `grid`. Area charts do not have a separate calculator mode: use `calc line` for the upper boundary points, then close the filled region to the plot area's bottom baseline (`y_max`) in the SVG.

### Calculate expected coordinates

```bash
python3 scripts/svg_position_calculator.py calc bar --data "A:185,B:142" --area "130,155,1200,480" --bar-width 120
python3 scripts/svg_position_calculator.py calc line --data "0:50,10:80,20:120" --area "120,120,1200,600" --y-range "0,150"
python3 scripts/svg_position_calculator.py calc pie --data "A:35,B:25,C:20" --center "420,400" --radius 200
python3 scripts/svg_position_calculator.py calc grid --rows 2 --cols 3 --area "50,150,1230,670"
```

For an area chart, use the line output as the top boundary:

```svg
M first_x,first_y ... L last_x,last_y L last_x,y_max L first_x,y_max Z
```

Manually compare the calculator output with the coordinates already present in the generated SVG. If coordinates differ, update the SVG from the `calc` output, rerun `svg_quality_checker.py`, then repeat the coordinate review. The tool intentionally does not rewrite SVG files automatically.

### Analyze (inspect existing SVG)

```bash
python3 scripts/svg_position_calculator.py analyze <svg_file>
```

Use this after SVG generation to inspect existing SVG geometry when manual comparison needs more context.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
python3 scripts/svg_finalize/flatten_tspan.py examples/<project>/svg_output
python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `align_embed_images.py`

```bash
python3 scripts/svg_finalize/align_embed_images.py path/to/slide.svg
python3 scripts/svg_finalize/align_embed_images.py --dry-run path/to/slide.svg
```

Use for rare single-file diagnostics when image `slice` / `meet` alignment and
Base64 embedding must be inspected outside `finalize_svg.py`. In normal project
runs, use `python3 scripts/finalize_svg.py <project_path>`; the old
`crop-images`, `fix-aspect`, and `embed-images` names remain accepted only as
`finalize_svg.py --only` aliases for the merged `align-images` step.

### `embed_icons.py`

```bash
python3 scripts/svg_finalize/embed_icons.py output.svg
python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Replaces `<use data-icon="chunk-filled/name" .../>`, `<use data-icon="tabler-filled/name" .../>` and `<use data-icon="tabler-outline/name" .../>` placeholders with actual SVG path elements. Use for manual icon embedding checks outside `finalize_svg.py`.

## SVG Compatibility Contract

The always-on SVG authoring contract lives in
[`shared-standards-core.md`](../../references/shared-standards-core.md), with
advanced effects, native data objects, and structured PPTX metadata owned by
their conditionally loaded modules. This tool guide does not repeat accepted
syntax, rejected constructs, or conditional limits.

`svg_quality_checker.py` validates source SVG before finalization.
`finalize_svg.py` and native export apply the preprocessing required by that
contract, while native conversion fails on unsupported visual elements rather
than silently dropping them.
