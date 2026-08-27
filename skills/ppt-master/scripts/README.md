# PPT Master Toolset

This directory contains user-facing scripts for conversion, project setup, SVG processing, source-preserving PPTX editing, export, recorded narration, and image generation.

## Directory Layout

- Top-level `scripts/`: runnable entry scripts
- `scripts/project_management/`: internals behind `project_manager.py`
- `scripts/source_to_md.py`: unified source-document → Markdown dispatcher
- `scripts/source_to_md/`: source-document → Markdown routing/batch helpers and backend converters (`_dispatcher.py`, `_batch.py`, `pdf_to_md.py`, `doc_to_md.py`, `excel_to_md.py`, `ppt_to_md.py`, `web_to_md.py`)
- `scripts/image_backends/`: internal provider implementations used by `image_gen.py`
- `scripts/tts_backends/`: internal TTS provider implementations used by `notes_to_audio.py`
- `scripts/template_import/`: internal PPTX reference-preparation helpers used by `pptx_template_import.py`
- `scripts/pptx_ooxml/`: shared OOXML intake, cloning, and package primitives
- `scripts/svg_finalize/`: internal post-processing helpers used by `finalize_svg.py`
- `scripts/docs/`: topic-focused script documentation
- `scripts/prompt_audit.py` + `scripts/prompt_audit_manifest.json`: maintainer-only prompt budget/governance lint (see [`docs/prompt_audit.md`](docs/prompt_audit.md)); the manifest is audit-only and never loaded as prompt context
- `scripts/assets/`: static assets consumed by scripts

## Quick Start

Typical end-to-end workflow:

```bash
python3 scripts/source_to_md.py <file-or-url-or-dir> [<file-or-url-or-dir> ...]
# or direct backend calls:
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
# or
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/project_manager.py init <project_name>
python3 scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...>
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/animation_config.py scaffold <project_path>  # optional object-level animation overrides
python3 scripts/svg_to_pptx.py <project_path>
```

After `init`, project-scoped Python CLIs automatically record their command
envelopes and bounded material outcomes in
`<project_path>/validation/workflow.log`; invoke them directly, without a
logging wrapper. The log does not copy the full console stream.

Repository update:

```bash
python3 scripts/update_repo.py
```

## Script Index

| Area | Primary scripts | Documentation |
|------|-----------------|---------------|
| Conversion | `source_to_md.py`, `source_to_md/pdf_to_md.py`, `source_to_md/doc_to_md.py`, `source_to_md/excel_to_md.py`, `source_to_md/ppt_to_md.py`, `source_to_md/web_to_md.py`, `pptx_intake.py`, `pptx_to_svg.py` | [docs/conversion.md](./docs/conversion.md) |
| Project management | `project_manager.py`, `workflow_log.py`, `workflow_transcript.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py`, `pptx_template_import.py`, `pptx_delivery_check.py` | [docs/project.md](./docs/project.md) |
| SVG pipeline | `preset_shape_svg.py`, `shape_boolean_svg.py`, `svg_authoring_view.py`, `authoring_roundtrip.py`, `compact_svg_coordinates.py`, `compact_svg_styles.py`, `stamp_native_fallbacks.py`, `mirror_template_materialize.py`, `finalize_svg.py`, `svg_to_pptx.py`, `template_preview_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `extract_svg_assets.py`, `extract_svg_pictures.py`, `animation_config.py`, `notes_to_audio.py`, `narration_sync.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md); [native shape authoring](../references/native-shape-authoring.md) |
| PPTX transitions | `pptx_transitions.py` | [docs/pptx-transitions.md](./docs/pptx-transitions.md) |
| PPTX animations | `pptx_animations.py`, `animation_config.py` | [docs/pptx-animations.md](./docs/pptx-animations.md) |
| Animation resources | `sound_sync.py` | [sound vocabulary and sync](../templates/sounds/README.md); [docs/pptx-animations.md](./docs/pptx-animations.md) |
| Spec maintenance | `update_spec.py`, `visualization_recall.py`; legacy `chart_recall.py` | [docs/update_spec.md](./docs/update_spec.md); [docs/visualization-recall.md](./docs/visualization-recall.md) |
| Image tools | `image_gen.py`, `image_treat.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| Maintenance smokes | Inline temporary-project commands | [advanced image and motion](./docs/advanced-image-motion-smoke.md); [mask and gradient](./docs/mask-gradient-smoke.md); [multilingual text](./docs/multilingual-text-smoke.md) |
| Repo maintenance | `update_repo.py` | README install/update section |
| Troubleshooting | validation, preview, export, dependency issues | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## High-Frequency Commands

Conversion:

```bash
python3 scripts/source_to_md.py <file-or-url-or-dir> [<file-or-url-or-dir> ...]
python3 scripts/source_to_md/pdf_to_md.py <file.pdf>
python3 scripts/source_to_md/ppt_to_md.py <deck.pptx>
python3 scripts/source_to_md/doc_to_md.py <file.docx>
python3 scripts/source_to_md/excel_to_md.py <workbook.xlsx>
python3 scripts/source_to_md/web_to_md.py <url>
python3 scripts/pptx_to_svg.py <deck.pptx> -o <output_dir>  # reconstruction/reference SVG import
```

Project setup:

```bash
python3 scripts/project_manager.py init <project_name> [--format <registered_format>]
python3 scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...>
python3 scripts/project_manager.py scaffold-spec <project_path>  # optional manual helper
python3 scripts/project_manager.py scaffold-lock <project_path>  # optional manual helper
python3 scripts/project_manager.py validate <project_path>
python3 scripts/project_manager.py page-context <project_path> P07 --record-usage
python3 scripts/project_manager.py page-context-report <project_path>
```

`--format` is optional and accepts registered canvas keys only. Pass it when
the actual canvas exactly matches one of those keys; otherwise omit it. Without
the flag, `init` creates `<name>_<YYYYMMDD>`, and authoring records the canvas
in `spec_lock.md` for Default Generate or the first SVG for Quick Generate.

`page-context` is an on-demand read-only current-page projection for diagnostics,
routing checks, or context measurement; normal generation retains the complete
Design Spec and lock once per valid execution context. Each invocation includes
the global lock projection as a continuity anchor set, not a color/font allowlist; large Design Specs,
prototype, and selected family visualization references are emitted only as scoped
path/SHA fingerprints and are read once per execution context. `--bundle` is a
deprecated compatibility no-op. `--record-usage` writes one derived snapshot
under `analysis/page-context/`; exact `o200k_base` token counts are optional and
degrade to `tokens: null` when `tiktoken` is absent. Telemetry may be partial.

Optional visualization-recall diagnostics and canonical validation:

```bash
python3 scripts/visualization_recall.py recall --page P03 --tag "time series" --tag "three metrics" --tag "direction over time"
python3 scripts/visualization_recall.py validate chart/line_chart
```

Template source import:

```bash
python3 scripts/pptx_template_import.py <template.pptx>
python3 scripts/pptx_template_import.py <template.pptx> --manifest-only
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode both
python3 scripts/svg_authoring_view.py <imported-svg-or-dir> -o <output-dir> --projection-kind layered
python3 scripts/svg_authoring_view.py <authoring-dir> --refresh-summary
python3 scripts/svg_authoring_view.py <authoring-dir> --adopt-object <from.svg>:<element-id> --into <target.svg>
python3 scripts/stamp_native_fallbacks.py <svg-file-or-directory> --write
python3 scripts/svg_quality_checker.py <template_workspace>/templates --template-mode --canonical-authoring
python3 scripts/mirror_template_materialize.py <import_workspace> <template_workspace>
python3 scripts/svg_to_pptx.py <import_workspace> --roundtrip
python3 scripts/template_preview_pptx.py <template_workspace>
```

Template import defaults to the canonical layered `svg/` backing tree and
creates compact `authoring-svg/` in the same transaction. Use
`--inheritance-mode both` only when a separate self-contained `svg-flat/`
verification tree plus `authoring-svg-flat/` is required. No derived narrative
digest is generated because `analysis/manifest.json` already owns those facts.

`pptx_template_import.py` creates the lightweight authoring bundle in the same
transaction as its immutable backing. `svg_authoring_view.py` remains the
standalone projection entry point for external SVG and migrations. Before the
transaction publishes, it also factors eligible non-semantic decoration into
`icons/imported/`. Recognized native shapes become one visible geometry carrier
plus at most one structured text body; recognized tables keep
one compact semantic JSON payload plus a preview cache. The projection removes
duplicate render geometry and import-only identity/payload attributes while
retaining text, images, stable ids, root Master/Layout markers, native-shape
intent, and document-local `data-pptx-source-ref` values. It also promotes a
common page font to the root and removes inherited presentation declarations
that merely repeat the root/group value.
Relative local image references are rewritten so the projected copy still
renders from its new location. The bundle's `authoring_summary.json` is the
model-readable current-file index; `authoring_manifest.json` records
source/authoring hashes and object paths for tools without duplicating opaque
payload and does not enter model context. Only unsupported, text-free,
schema-free source ornaments may become compact `native-restore` image proxies whose
hashed SVG previews live under `images/source-object-previews/`. Unchanged
proxies restore the original native PowerPoint objects; complete removal deletes
a Slide-local source object, while inherited-proxy removal and any proxy or
preview edit fail export. Imported
model-facing frames and safe
transform page coordinates use at most two decimals; immutable lossless SVGs
retain the original precision. In-place vector/picture extraction
refreshes the summary automatically; use `--refresh-summary` after other direct
IR edits. The full imported SVG remains unchanged as native-payload backing.
Template creation edits the IR and materializes validated `templates/*.svg`;
the layered IR directory itself is not a final template or direct release
export source. A complete-page flat IR may be selected with
`--roundtrip`: `authoring_roundtrip.py` reads `authoring-svg-flat/`, regenerates its
deterministic extraction baseline, restores unchanged refs from the immutable
layered backing, and sends the temporary result through preserve export while
leaving edited/deleted/new authoring content in place.

An imported round-trip workspace may optionally add root `page_plan.json` to
select, reorder, repeat, or omit source slides during export. The v1 shape is
minimal: top-level `schema: "ppt-master.roundtrip-page-plan.v1"` plus a
non-empty ordered `pages` array; every entry requires one-based
`source_slide` and may name a unique `authoring-svg-flat/` filename in `svg`.
A copied SVG is diffed against the baseline for its declared source slide.
Move a cross-page object with
`svg_authoring_view.py <authoring-dir> --adopt-object <from.svg>:<element-id>
--into <target.svg>` rather than pasting raw SVG. The helper rebuilds the copy
without source identity, inlines source-owned imported vectors, refuses source
proxies, resolves id collisions, and refreshes `authoring_summary.json`.
`notes/<svg-stem>.md` implicitly overrides notes for that output page; when it
is absent, source notes travel with the cloned page. Unchanged repeats clone
their private notes/chart/diagram/embedding parts, while media may stay shared;
slide-jump targets must map to exactly one output page. Without the file, the
identity round trip is unchanged. See
[`docs/svg-pipeline.md`](docs/svg-pipeline.md#round-trip-deck-page-plans) for
the schema, sidecar keying, fail-closed rules, and export receipt.

Run `python3 scripts/svg_quality_checker.py <workspace> --roundtrip` before a
round-trip export. The mode resolves the same identity or `page_plan.json`
output roster as the exporter and checks only new or changed text for supported
font stacks and sizes, estimated canvas containment, and horizontal capacity
against its owning `data-pptx-frame` or nearest rect fallback. Capacity is the
single-line width of each positioned line; the gate does not model vertical
wrapping. Explicit frame-width or canvas overflow is blocking, warnings are
advisory, and unchanged source refs, source proxies, plus
generated-project/template-only contracts are skipped.

`mirror_template_materialize.py` is the deterministic Type A mirror
validator/publisher. Template_Designer first reviews and authors the compact
layered `authoring-svg/` tree. The command loads its tool-only manifest and
validates it against immutable `svg/`,
`analysis/native_structure.json`,
`svg/inheritance.json`, `sources/source.pptx`, and any extracted-vector
inventory, then publishes the current visible authoring tree atomically. It
never replaces an unchanged visible subtree with lossless source XML; that
backing supplies provenance and supported non-visible semantics only. Mirror retains
only the Layout/Master chain reachable from each source Slide. Every output SVG
resolves Master + Layout + Slide context while keeping layer ownership explicit;
source identities unused by every Slide produce no SVG.
For a PPTX-backed mirror, `templates/source_themes.json` carries the exact Theme
bytes for each retained Master; it is validated tool input, not an SVG prototype
or model-editing surface.
Unchanged supported Slide-local/slot refs may recover native payload; edited
refs keep their current SVG fallback. Fixed Master/Layout wrappers are expanded
mechanically into direct atoms, source visibility flags become canonical root
metadata, and decoration-only imported vectors are copied once to
`icons/imported/`. Semantic objects remain inline. Large
opaque `txBody`, shape-style, and custom-geometry payloads are deduplicated into
`templates/native_payloads.json.gz`; repeated native restoration attributes
are stored there as short `data-pptx-native-ref` records. Structural metadata
stays inline, while checker, template-structure validation, and export hydrate
both layers in memory. Legacy inline payload and v1 payload-only stores remain
readable. The v1 execution manifest points to per-prototype
`ppt-master.template-text-slots.v2-min` diagnostic sidecars. They are derived
tool metadata and are not injected into model context. Checker and export
validate output attributes, topology, and resource hashes against the complete
prototype internally. Bitmap assets
and Office vector image media go to `images/`; audio, video, and opaque source
payloads go to their semantic workspace directories.
The destination must be empty, and the command does not write
`templates/design_spec.md`; Template_Designer owns that authored brief.

`template_preview_pptx.py` reads a template workspace, exports every complete `templates/*.svg` Slide prototype as one structured review slide, and verifies the resulting Master/Layout package. In a project root containing Layout and Deck specs, it previews the active Layout roster. Standalone `layout_<layout_key>.svg` definition files are rejected; every reusable Layout must be represented by a complete Slide prototype. This is an on-demand review action: its default output is `exports/<template_id>_template_preview.pptx`, and that directory need not exist before the command runs. It refuses an existing output unless an intentional re-export passes `--force`.

Native preset shape authoring (one or more registry-backed fragments on stdout):

```bash
python3 scripts/preset_shape_svg.py list --search arrow
python3 scripts/preset_shape_svg.py describe rightArrow --compact
python3 scripts/preset_shape_svg.py render rightArrow --id process-arrow --frame 120 180 240 96 --fill '#2563EB'
python3 scripts/preset_shape_svg.py render-batch --input - <<'JSON'
[
  {"preset":"chevron","id":"step-1","frame":[120,180,220,96],
   "fill":"#2563EB","stroke":"none","adjustments":{"adj":"val 42000"}},
  {"preset":"leftBrace","id":"group-brace","frame":[380,170,48,240],"fill":"none","stroke":"#111827","stroke_width":3}
]
JSON
```

Runtime capability discovery reads
[`preset-shape-vocabulary.md`](../references/preset-shape-vocabulary.md), which
lists all 187 exact names by Office category and objective contour family.
`list [--search QUERY]` and `list --grouped [--search QUERY]` remain optional
location views; they do not replace the complete vocabulary.
`describe --compact` returns the selected preset's objective identity, Office
category, family, scope, literal boundary, adjustments, connector/path facts,
connection sites, and text-rectangle availability. Plain `describe` preserves
the full nested semantics payload. A zero-match `list --search` remains
a failed lookup with exit code 1.

The helper never writes a page or project file. Select one exact semantic
stock-shape match, inspect the emitted fragment, and insert it into the
hand-authored SVG with the normal patch workflow. Semantic discovery does not
force ordinary rectangles, ellipses, or lines through `render`; use the
simplest exact authoring form from the native-shape reference. A rendered
project-owned preset is one compact atomic `<g>` with direct registry-generated
visible paths. When one effect is justified, optional `--filter-id softShadow`
references one existing direct page-level filter under the shared shadow/glow
contract and applies it once to a shape preset. Connector presets do not accept
that option. The helper does not create the filter definition. `render-batch`
accepts a non-empty JSON array using the snake_case forms of the single-render
options; it validates every item and duplicate id before printing, so one
invalid item produces no partial fragment output. The batch remains
fragment-only input for one current construction, not a page generator or
project manifest. `adjustments` is a JSON object keyed by guide name, unlike
the repeatable single-render `--adjust NAME=FORMULA` option.
Quality check and export rerender the registry instead of relying on a hidden
carrier, preview wrapper, or stored preview fingerprint. PPTX import and
round-trip SVGs deliberately keep their expanded carrier/preview evidence and
are not rewritten into this authored form. Keep ordinary rectangles, ellipses,
freeform geometry, charts, icons, and ambiguous silhouettes as regular SVG.
See [`references/shared-standards-core.md`](../references/shared-standards-core.md) §1.5 for
the normative contract and
[`references/native-shape-authoring.md`](../references/native-shape-authoring.md)
for selection and authoring guidance.

PowerPoint-style Merge Shapes materialization (source read-only; result paths
on stdout):

```bash
python3 scripts/shape_boolean_svg.py render slide.svg \
  --operation intersect \
  --source circle \
  --source card \
  --id overlap
```

The first source owns result paint and is the primary geometry for `subtract`.
Local and ancestor transforms are baked into SVG-root coordinates. Replace the
operands with every returned path at the root in the primary operand's z-order;
`fragment` returns multiple stable sibling paths. Operands may be supported
closed geometry or supported horizontal implicit-LTR direct `<text>` whose exact
OpenType weight/style can be resolved; repeat `--font-dir PATH` for additional
font roots. Text is shaped to glyph outlines before the operation, so the
result remains editable freeform geometry but is no longer editable text. See
[`references/native-shape-authoring.md`](../references/native-shape-authoring.md)
§6 for the closed operand and failure contract.

External-source migration and explicit picture normalization:

```bash
python3 scripts/extract_svg_assets.py <layered_svg_dir> --icons-dir <icons_dir> --icon-namespace imported --inplace --id-prefix layered
python3 scripts/extract_svg_assets.py <flat_svg_dir> --icons-dir <icons_dir> --icon-namespace imported --reuse-inventory <layered_inventory.json> --inplace --id-prefix flat
python3 scripts/extract_svg_pictures.py "<svg_file>" --select "<group_id>" --resource-root "<workspace>" --images-dir "<picture_assets_dir>" --inplace  # optional create-template normalization: one selected group -> one SVG picture
python3 scripts/svg_quality_checker.py <template_workspace>/templates --template-mode --canonical-authoring
python3 scripts/mirror_template_materialize.py <import_workspace> <template_workspace>  # Type A mirror only; destination owns no roster
```

PPTX template import and round-trip import run vector readability extraction in
their staging transaction before the first authoring bundle is published. The
manual extraction commands above are only for external SVG/migration input.

`extract_svg_assets.py` extracts only non-semantic decoration. Any subtree that
contains a semantic object, text, table, chart, relationship, or other
meaning-bearing authoring content stays inline. Each imported asset and its
placeholder declare `data-pptx-asset-role="decoration"`; the v2 inventory
records the same role, and round-trip/template consumers reject missing or
different roles. The extractor fingerprints each eligible subtree before
generated-ID namespacing. Process the layered authoring view first, then pass its inventory to
the flat view with `--reuse-inventory`; matching flat subtrees reference the
existing layered asset instead of creating a duplicate file. Only unmatched
flat-only vectors create new assets. Create-template stores these assets once in
`<workspace>/icons/imported/` and writes decoration-marked
`data-icon="imported/<name>"` references.
Inventories retain any `data-pptx-source-ref` values carried by the extracted
subtree, so re-inlining preserves authoring-manifest object identity.
Rerunning a namespaced pass against an already rewritten projection inventories
the existing references without progressively wrapping more parent geometry.

Post-processing and export:

```bash
# Run only when the Design Spec's effective Speaker Notes outcome is enabled.
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

When Speaker Notes is disabled, skip `total_md_split.py` and append
`--no-notes` to `svg_to_pptx.py` so stale files under `notes/` cannot be
embedded.

`finalize_svg.py` optimizes ordinary raster images by default using `2x` display pixels and max `2560px`; validated nested crop transports retain source pixel dimensions because their inner `1×1` image is source-unit geometry rather than a rendered-pixel budget. Native `svg_to_pptx.py` defaults to `--image-sizing cap`: images that need neither resizing nor EXIF geometry normalization retain their original bytes, while oversized single-frame raster sources are re-encoded after resizing toward `2560px`. Cropped or stretched placements (including imported picture crops) retain enough source pixels to avoid undersupplying the visible frame. Use `svg_to_pptx.py --image-sizing display --image-scale 2 --image-quality 85` for an explicit compact export, or `--no-image-optimize` to force original image bytes.

`finalize_svg.py` remains mandatory because it creates the self-contained `svg_final/` visual preview. Those SVGs may be opened directly or inserted into PowerPoint as SVG pictures. The only supported generated-PPTX path is `svg_output/` through the project SVG-to-DrawingML converter; `-s final` is diagnostic-only, and PowerPoint's manual Convert-to-Shape operation is unsupported.

For SVG-authoring routes, `svg_output/` is the complete visible page-design source: every exported text, image, shape, background, and template-derived layout element is present in the page SVG or explicitly referenced by it. Export may translate represented content into Master/Layout/Slide parts or native objects, but it does not retrieve missing visible content from templates or planning files. Speaker notes, animation, narration, and transitions use dedicated sidecars or assets; Edit Native PPTX owns source-preserving existing-deck edits.

Native `svg_to_pptx.py` release export reads the project's explicit structure mode. Free-design, Brand-only, Style-only, and other `template_reuse_scope: style` projects use `flat`, omit Master/Layout mappings and SVG structure metadata, keep every represented object Slide-local, and materialize one clean project-owned Master plus one Blank Layout from the current color/typography lock. Stock content placeholders and unused built-in Layouts are removed; only the standard date/footer/slide-number capability hooks remain. A Deck/Layout application uses `structured` in Default when Strategist derives `template_reuse_scope: mirror|layout` with complete lock rosters, or in Quick when every page of the installed Layout/Deck roster declares the complete lockless Master/Layout/slot contract: each project supplies unique Master/Layout definitions and one Layout assignment per generated page before SVG generation, and every SVG root repeats its assigned identity. An unselected complete template Slide may still supply a reusable Layout definition without becoming a published page. Fixed Master/Layout visuals are direct semantic atoms; ordinary groups are invalid there, while one validated compact authored-preset `<g>` is the sole group exception because it compiles to one native shape. Reusable slots are top-level groups with positive design-zone bounds plus one compatible carrier. Composite `object` regions use explicit proxy binding, and zero-slot Layouts are valid.

Structured template export compiles only the declared structure, maps locked typography/colors into PowerPoint defaults, creates the named Master/Layout parts, and reads the package back before publication. It never clusters pages, promotes repeated chrome heuristically, or invents placeholders. Flat export is the normal free-design/Brand-only/Style-only/style-scope route: it creates only the clean project-owned shell and performs no promotion or deduplication of Slide content.

Template `page_layouts` records authoring-input provenance, `pptx_masters` / `pptx_layouts` own unique reusable definitions, and `page_pptx_layouts` owns page assignment. Strict preserves its Master/Layout/slot contract; adaptive retains its Master and may use a new Layout key only when fixed Layout atoms or slot topology/bounds change. `standard` / `fidelity` inspect complete source structure evidence and author compact or broader useful Slide rosters. `mirror` materializes source Slides and their reachable identity graph without semantic synthesis or gap filling, while completing inherited context and mechanically expanding fixed-layer group wrappers into direct atoms.

Legacy structured/template contracts using `baseline`, `template`, `preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled`/`utility`, direct atomic placeholders, or incomplete root Master identity must be replaced by a new workspace created through [`create-template`](../workflows/create-template.md). Generate new structured SVG pages from that workspace; do not upgrade the existing PPTX/SVG in place. Explicit flat free-design/Brand-only/Style-only projects intentionally omit root Master identity.

`pptx_to_svg.py` also writes a canonical `animations.json` whose default
transition is `none`. Page transitions produced by the current native
transition registry are read back with their effective options, exact duration,
automatic advance, and optional embedded WAV sound. Source transition XML
outside that closed writer/read-back contract remains diagnosed rather than
being normalized by guesswork.
Finite object-animation rows from the current writer are also projected when
their registry effect, effective options, pane order, trigger, exact duration,
relative delay, and top-level SVG group target all read back exactly. Advanced
timing, build/media trees, duration-less native rows, and unmapped targets stay
diagnosed/direct-preserve.

`pptx_to_svg.py` annotates verified text-grid tables and conservative chart data with `data-pptx-replace-with` beside the visible SVG fallback and places the payload in `<metadata type="application/json">`; the parent claim selects the chart or table schema. Imported table/chart groups under this contract carry `data-pptx-import-source="pptx"`, whether active or fallback-only. Table import covers exact physical row/grid topology, canonical rectangular merges, safe solid/no-fill per-side borders, plain multi-paragraph cells, and a closed run-rich paragraph schema. Each rich run requires `text` and may use only `bold`, `italic`, `underline`, `strike`, `color`, `font_size`, one `font_family`, `lang`, and `alt_lang`. A merge must use the exact `rowSpan` / `gridSpan` / `hMerge` / `vMerge` physical topology with empty merge slaves. Presentation-only source run XML without a non-empty `effectLst` / `effectDag` normalizes; a table-cell run effect disables native replacement and adds a blocking effect diagnostic. Relationship-bearing text, extensions, line breaks, fields, tabs, bullets, broken text topology, unsafe border XML, non-solid fills, and other merge encodings remain fallback-only. For table style `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}`, the normalized SVG fallback resolves `wholeTbl`, `firstRow`, horizontal banding, theme colors/fonts, and direct cell/run overrides; other built-in/custom style families are not implied.

Supported parsed column/bar/line/area, pie/doughnut, scatter, and bubble charts without a baked preview receive a deterministic readable fallback marked `data-pptx-fallback-kind="normalized"`. The importer additionally activates verified column/line/area combo charts, canonical OHLC stock charts, area charts with numeric date axes, verified scatter/bubble charts whose two value axes fit the closed `axes.x` / `axes.y` contract, radar charts, safe `of_pie` `serLines`, axis/title/legend normalization, and validated bar/column gap/overlap cases. Combo plots may retain independent primary/secondary category caches and workbook ranges. Both the category/value and XY contracts retain kind/position/visibility/label position/number format/min/max/major unit/reverse/major gridlines for native read-back. Scatter import derives effective `scatter_style` from uniform per-series line/marker/smooth state. The normalized XY fallback consumes only the two major-gridline flags; the C4/C5 additions do not expand the normalized renderer. `gapWidth` is accepted only as an integer in `0..500` and `overlap` only as an integer in `-100..100`; both normalize in native output, while malformed or out-of-range values fail closed. Safe common series paint forms and theme scheme colors are resolved; unknown series paint/style XML outside the explicit normalization boundaries still fails closed. Safe stock series style may pass the structural gate, but stock series, `hiLowLines`, and up-down bar local styling can still normalize under the data-object-first contract. The PowerPoint-native replacement remains allowed to normalize unmodeled no-fill/alpha/line/marker details and reports the route-level loss risk. Chart title/legend/axis titles and supported data-label flags are retained when the current schema can represent them. Fallback-only objects keep rendered SVG content or a baked chart preview and carry `data-pptx-replacement-status`, which validation and `--native-charts-and-tables` export report as a warning. An active marker without a renderer keeps `data-pptx-fallback-kind="placeholder"`; default export keeps the reconstruction-only placeholder and the native Chart/Table opt-in may still reconstruct it.

The ChartEx importer accepts exactly the validated treemap, sunburst, histogram, pareto, box-whisker, waterfall, and funnel data models. Supported hierarchy/category/value/series/subtotal data round-trips to native output; source style, axes, labels, and binning may normalize. Numeric caches must be non-empty and finite with exact contiguous point topology. This is not arbitrary ChartEx import or presentation fidelity, and the ChartEx native writer still only promises valid payload palette entries rather than full source styling.

Imported/template-owned table/chart markers carry
`data-pptx-native-authority="json"`; their inline JSON is authoritative and the
visible fallback is a derived preview, so fallback freshness does not veto
native export. Free-designed markers omit the authority attribute and are
SVG-first. After their visible fallback and JSON are synchronized, run
`stamp_native_fallbacks.py ... --write`; missing, invalid, or stale baselines
leave default fallback export available but make `--native-charts-and-tables`
fail closed. Only that explicit flag activates Chart/Table replacement; marker
presence, semantic tables, and imported chart packages do not. Legacy marker
spellings and `--native-objects` remain read-compatible.

Exporter-canonical classic charts also recover canonical solid series/slice
colors and exact one- or two-paragraph title styling; two paragraphs retain
their `title` / `subtitle` roles. Slide-number fields resolve to the display
number defined by `firstSlideNum`; standalone master/layout SVGs retain their
literal field fallback because they are shared by multiple slides.

Image generation:

```bash
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py --list-backends
python3 scripts/analyze_images.py <project_path>/images
```

Generated-deck formulas do not use an image command. Author a native formula
marker in the page SVG; `svg_to_pptx.py` compiles its LaTeX metadata to editable
PowerPoint OMML. Forward compilation covers the explicitly documented Microsoft
365 LaTeX and mhchem input profiles and fails closed outside them.
`pptx_to_svg.py` also reconstructs PPT Master-owned, validator-clean OMML into
canonical block/inline formula markers with visible linear SVG previews. This
is a closed-vocabulary reverse import, not arbitrary third-party
OMML-to-LaTeX conversion; unknown OMML is reported and kept opaque in tolerant
mode. The retained `latex_render.py` utility is
standalone legacy rasterization only and is not connected to either Generate
profile.

Repository update:

```bash
python3 scripts/update_repo.py
python3 scripts/update_repo.py --skip-pip
```

## Recommendations

- Keep one user-facing entry point per workflow at the top level of `scripts/`
- Move provider-specific or helper internals into subdirectories
- Prefer the unified entry points `project_manager.py`, `finalize_svg.py`, and `image_gen.py`
- Use `svg_output/` for the only supported native PPTX export and `svg_final/` for self-contained SVG visual preview / picture insertion

## Related Docs

- [Conversion Tools](./docs/conversion.md)
- [Project Tools](./docs/project.md)
- [SVG Pipeline Tools](./docs/svg-pipeline.md)
- [PPTX Transition Core](./docs/pptx-transitions.md)
- [Image Tools](./docs/image.md)
- [Troubleshooting](./docs/troubleshooting.md)
- [Skill Entry](../SKILL.md)

_Last updated: 2026-07-11_
