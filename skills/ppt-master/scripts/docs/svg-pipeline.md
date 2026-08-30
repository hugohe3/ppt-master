# SVG Pipeline Tools

> **Maintenance boundary**: post-processing modules serve both the on-disk
> `svg_final/` preview and in-memory native PPTX conversion. Check both
> consumers before changing or removing a step.

These tools cover post-processing, SVG validation, speaker notes, recorded narration, and PPTX export.

The normal release contract has one PPTX path: `svg_output/` → the project
SVG-to-DrawingML converter → native PPTX. An explicit dangerous compatibility
path may apply its supported in-memory normalizations to the default
`svg_output/` or to a project-relative directory selected with `-s`, then enter
the same strict DrawingML converter.
The mandatory `finalize_svg.py` step separately creates self-contained
`svg_final/` visual previews, which may be opened directly or inserted into
PowerPoint as SVG pictures. There is no SVG-image PPTX output, and PowerPoint's
manual Convert-to-Shape operation is unsupported.

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

- translates each recognized native shape into one visible geometry carrier
  plus at most one structured text body;
- translates each recognized native table into one inline
  `ppt-master.semantic-table.v2` payload with table/cell/run defaults and named
  cell styles, plus an external authoring-preview cache;
- removes duplicate render geometry, embedded `txbody`, and import-only
  identity/style/hash payloads;
- keeps visible semantic paths, text, images, stable ids, Master/Layout root
  markers, native-shape intent, and a document-local `data-pptx-source-ref` on
  each imported logical object;
- rewrites relative local asset references for the projection's new location;
- compacts model-facing coordinates, promotes a common page font to the root,
  and removes descendant presentation declarations equal to inherited values.

PPTX authoring publication applies two object-level reductions inside its
staging transaction, before the editable bundle first appears:

- non-semantic vector decorations that cross the readability threshold may
  move to `icons/imported/*.svg`; the asset, placeholder, and v2 inventory all
  declare the fixed `decoration` role. Any subtree containing semantic
  authoring content remains inline;
- unsupported, text-free, schema-free source ornaments with no semantic marker
  may become
  `<image data-pptx-source-proxy="native-restore">` references whose hashed SVG
  previews live under `images/source-object-previews/`.

The live editor expands `data-icon` references for complete-page preview. Read
an imported vector asset only when editing that decoration. An unchanged asset
restores its native source objects; editing the asset rebuilds every slide whose
placeholder references that vector edit unit. A source proxy remains atomic: leave it unchanged
to restore the original native PowerPoint object. A complete Slide-local proxy
may be removed to delete that object; an inherited Master/Layout proxy must
remain because one flat page cannot delete shared structure. Editing the proxy
or its preview asset fails round-trip export instead of silently rasterizing or
flattening the object.

The summary stores the current SVG roster plus compact per-file canvas, size,
text, image, vector, placeholder, icon, source-ref, and source-proxy counts.
Models read the summary and editable SVGs; they do not read the machine
manifest. The manifest stores relative source/authoring filenames, source and initial authoring
hashes, source element paths, and immutable preview hashes for source proxies.
It deliberately does not copy the opaque payload.
The layered authoring bundle remains the editable source for template creation;
the complete imported SVG remains immutable native-payload backing. Final
`templates/*.svg` files are materialized and validated from that pair. A
complete-page `authoring-svg-flat/` bundle is the user's editable source for an
imported-deck round-trip. `pptx_template_import.py` publishes its compact
layered authoring bundle and decoration inventory in the same transaction as
its immutable backing. `pptx_to_svg.py --roundtrip` places image media in
`images/`, decoration-only vectors in `icons/imported/`, cues/audio/video/notes in their named
directories, opaque payloads in `native-payloads/`, the source package in
`sources/`, and tool-owned backing/contracts in `analysis/`; `assets/` is
invalid. `svg_to_pptx.py --roundtrip` always reads `authoring-svg-flat/`,
restores unchanged source refs from `analysis/roundtrip-svg/`, expands imported
vector edit units from `icons/imported/`, and retains edits/deletions/new
content without rewriting the bundle. Unchanged slides and resources pass
through byte-for-byte. A page edit rebuilds that output page; a changed
materialized or derived resource rebuilds every output page that references it.
Changed materialized bytes must still match the source package part's extension
and Content-Type. Resource hrefs resolve exactly relative to the page or
extracted asset and must remain inside the workspace.

### Round-trip deck page plans

`page_plan.json` is an optional, model-authored file at the root of a
`pptx_to_svg.py --roundtrip` workspace. Without it, export uses the existing
identity roster and preserves the no-plan package behavior. With it, the
`pages` array is the complete output order and may select, reorder, repeat, or
omit source slides:

```json
{
  "schema": "ppt-master.roundtrip-page-plan.v1",
  "pages": [
    {"source_slide": 3},
    {"source_slide": 1, "svg": "intro.svg"},
    {"source_slide": 3, "svg": "intro_b.svg"}
  ]
}
```

`source_slide` is the one-based source presentation index. `svg` defaults to
that source slide's canonical imported filename, normally `slide_03.svg`, and
must name one file directly inside `authoring-svg-flat/`. Each output entry
must use a different SVG filename. To author independent edits from one source
page, copy its SVG to a new filename and list that filename on the repeated
entry. The exporter always compares the copy with the baseline regenerated
from its declared `source_slide`, so source-ref restoration, proxy checks, and
edit detection remain source-correct. Every extra authoring SVG must appear in
the plan; an unknown, duplicate, or cross-owned canonical filename fails.

Move an object between pages before export with the authoring helper:

```bash
python3 scripts/svg_authoring_view.py <authoring-dir> \
  --adopt-object <from.svg>:<element-id> --into <target.svg>
```

The helper appends a copy to the target page, removes its source/native restore
transport, gives colliding ids fresh local names, inlines any source-owned
`icons/imported/` vector reference, and refreshes the page-plan-aware summary.
It refuses a source proxy because that atomic object cannot leave its source
page. Raw cross-page source refs remain invalid and export reports that the page
contains unknown source refs.

An unchanged planned page keeps the source slide XML and receives its own
relationship graph. Repeated pages clone notes slides, charts, diagrams,
embeddings, and other private structured parts under unique part names while
ordinary media may remain shared. An edited copy overlays only its edited
owners onto its cloned source page. Same-deck slide-jump links follow the
page-plan contract: a target must map to exactly one output page. An
omitted or repeated destination is an error; external links remain unchanged.
Omitting a source slide deliberately drops its private video, audio, or opaque
native payloads; a kept slide still fails if rebuilding it would discard such
relationships.
With a plan present, presentation-level `sectionLst` and custom-show rosters
are dropped, output `p:sldId` values are renumbered, and the slide count in
`docProps/app.xml` is updated.

Output-page sidecars are keyed by the authoring SVG stem. A repeated copy
inherits its source row from `animations.json` unless that output stem has its
own row. Canonical pages keep identity notes semantics: a manifest `notes.file`
must equal `notes/<svg-stem>.md`; deleting that file removes the source notes,
different bytes override them, and matching bytes remain unchanged. A canonical
page without source notes treats a present stem-keyed file as an addition. For
a copied SVG, a present `notes/<svg-stem>.md` overrides its inherited source
notes and an absent file keeps them. Deleting inherited source notes only on a
copy is not supported in v1. The same output-stem rule applies to narration
audio.

When a round-trip recorded-narration export omits `--animation-config`, it uses the workspace `animations.json` when present and otherwise applies no sidecar while preserving source motion.

Narration audio is keyed by the output SVG stem. A copied output page uses its
own stem-keyed notes when present and otherwise inherits the declared source
slide's canonical notes.

`-t`, `-a`, `--recorded-narration`, `--use-narration-timings`,
`--no-animations`, and `--no-notes` continue to resolve per output page.

Import and export from the repository root:

```bash
python3 skills/ppt-master/scripts/pptx_to_svg.py source.pptx \
  -o /path/to/workspace --inheritance-mode both --roundtrip
python3 skills/ppt-master/scripts/svg_to_pptx.py /path/to/workspace \
  --roundtrip -o /path/to/output.pptx
```

Successful round-trip export prints one deck receipt:
`Round-trip export summary: output_pages=N passthrough=P
cloned_passthrough=C patched=M rebuilt=R`. `patched` keeps source shape XML
while order, notes, or motion may change; `rebuilt` means visible authoring or
one of its referenced resources changed.
Without `-o`, round-trip export names the deck `<workspace-directory-name>_<timestamp>[<flavor-suffix>].pptx` under `exports/`.

Before export, run `python3 scripts/svg_quality_checker.py <workspace> --roundtrip`
as the round-trip text-capacity gate. It resolves the output roster from
`authoring-svg-flat/` and optional `page_plan.json`, then applies the shared
font-family, font-size, text-width, and canvas metrics only to new text or
changed source-ref objects. The gate asserts horizontal capacity: it estimates
single-line width for each positioned line and does not model vertical
wrapping. Width beyond an explicit ancestor `data-pptx-frame` is blocking;
overflow against the nearest-rect-sibling fallback is advisory, while bounds
leaving the page canvas remain blocking. Other advisories remain non-blocking.
Unchanged source refs, source proxies, and generated-project-only spec,
template, canonical-authoring, and resource-manifest checks are excluded.

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

## Shape Boolean maintenance smoke

Run this manual smoke from the repository root after changing
`shape_boolean_svg.py`, preset geometry, path conversion, or custom-geometry
import/export. It uses only a gitignored `projects/_smoke_*` workspace and the
inline-smoke convention from [`code-style.md`](../../../../docs/rules/code-style.md)
§11; do not turn it into a test file or example deck.

```bash
python3 - <<'PY'
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pathops

project = Path(tempfile.mkdtemp(prefix="_smoke_shape_boolean_", dir="projects"))
scripts = Path("skills/ppt-master/scripts")
svg_output = project / "svg_output"
svg_output.mkdir()
(project / "spec_lock.md").write_text(
    """<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: ppt169
## communication
- audience:
- objective:
- core_message:
## mode
- mode: briefing
## visual_style
- visual_style: Boolean maintenance smoke
## colors
- bg: #FFFFFF
- primary: #2563EB
- accent: #F97316
- text: #0F172A
## typography
- font_family: Arial, sans-serif
- title_family: Arial, sans-serif
- body_family: Arial, sans-serif
- title: 36
- body: 20
## icons
- library: none
- inventory: none
## page_rhythm
- P01: dense
## pptx_structure
- mode: flat
## forbidden
- Unsupported SVG constructs
""",
    encoding="utf-8",
)


def run_tool(script, *args):
    result = subprocess.run(
        [sys.executable, str(scripts / script), *map(str, args)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()

preset = run_tool(
    "preset_shape_svg.py", "render", "rightArrow",
    "--id", "preset-source", "--frame", "500", "120", "240", "120",
    "--fill", "#2563EB", "--stroke", "none",
)
source = project / "operands.svg"
source.write_text(
    f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <defs><clipPath id="clip"><rect width="80" height="80"/></clipPath></defs>
  <g transform="translate(100 80) scale(1.2)">
    <rect id="body" x="40" y="40" width="400" height="240" rx="20"
      fill="#2563EB" stroke="#0F172A" stroke-width="5"
      stroke-dasharray="10 4"/>
    <circle id="cutout" cx="240" cy="160" r="70" fill="#F97316"/>
    <text id="text-cutout" x="240" y="235" text-anchor="middle"
      font-family="sans-serif" font-size="180" font-weight="700">01</text>
    <text id="missing-font" x="240" y="235"
      font-family="Definitely Missing Font" font-size="80">X</text>
    <text id="nested-text" x="240" y="235"
      font-family="sans-serif" font-size="80"><tspan>X</tspan></text>
    <path id="open" d="M 40 320 L 260 320 L 260 420" fill="#2563EB"/>
    <rect id="clipped" x="40" y="320" width="160" height="100"
      clip-path="url(#clip)" fill="#2563EB"/>
    <path id="imported" d="M 240 320 H 400 V 420 H 240 Z"
      data-pptx-geometry-kind="custom" fill="#2563EB"/>
    <rect id="dashoffset" x="440" y="320" width="120" height="100"
      fill="#2563EB" stroke="#0F172A" stroke-dashoffset="2"/>
    <rect id="non-scaling" x="500" y="40" width="150" height="120"
      fill="#2563EB" stroke="#0F172A" stroke-width="5"
      stroke-dasharray="10 4" vector-effect="non-scaling-stroke"/>
    <circle id="non-scaling-cut" cx="625" cy="100" r="45" fill="#F97316"/>
    <rect id="far" x="800" y="320" width="100" height="80" fill="#2563EB"/>
  </g>
  {preset}
  <circle id="preset-cut" cx="690" cy="180" r="52" fill="#F97316"/>
</svg>
""",
    encoding="utf-8",
)

operations = [
    ("union", "union", "preset-source", "preset-cut"),
    ("combine", "combine", "body", "cutout"),
    ("fragment", "fragment", "body", "cutout"),
    ("intersect", "intersect", "body", "cutout"),
    ("subtract", "subtract", "body", "cutout"),
    ("text-subtract", "subtract", "body", "text-cutout"),
]
expected_custom_shapes = 0
for index, (name, operation, first, second) in enumerate(operations, start=1):
    fragment = run_tool(
        "shape_boolean_svg.py", "render", source, "--operation", operation,
        "--source", first, "--source", second, "--id", f"result-{name}",
    )
    paths = list(
        ET.fromstring(
            f'<svg xmlns="http://www.w3.org/2000/svg">{fragment}</svg>'
        )
    )
    assert paths and all(path.tag.endswith("}path") for path in paths)
    assert all(
        token not in fragment
        for token in ("clip-path=", "fill-rule=", "mask=", "transform=")
    )
    if operation == "fragment":
        assert len(paths) > 1
        assert [path.get("id") for path in paths] == [
            f"result-{name}-{piece}"
            for piece in range(1, len(paths) + 1)
        ]
    else:
        assert len(paths) == 1
        assert paths[0].get("id") == f"result-{name}"
    if operation == "combine":
        assert all(path.get("stroke-width") == "6" for path in paths)
        assert all(path.get("stroke-dasharray") == "12 4.8" for path in paths)
    if operation == "subtract":
        assert (paths[0].get("d") or "").count("M ") >= 2

    expected_custom_shapes += len(paths)
    (svg_output / f"{index:02d}_{name}.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" '
        'data-pptx-page-role="content">'
        '<rect x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>'
        f"{fragment}</svg>\n",
        encoding="utf-8",
    )

non_scaling = ET.fromstring(
    run_tool(
        "shape_boolean_svg.py", "render", source, "--operation", "union",
        "--source", "non-scaling", "--source", "non-scaling-cut",
        "--id", "result-non-scaling",
    )
)
assert non_scaling.get("stroke-width") == "5"
assert non_scaling.get("stroke-dasharray") == "10 4"
assert non_scaling.get("vector-effect") == "non-scaling-stroke"

rejections = [
    ("union", "body", "open", "open subpath"),
    ("union", "body", "clipped", "uses clip-path"),
    ("union", "body", "imported", "PPTX import/round-trip metadata"),
    ("union", "body", "dashoffset", "stroke-dashoffset"),
    ("intersect", "body", "far", "produced no filled area"),
    ("subtract", "body", "missing-font", "cannot resolve an installed font"),
    ("subtract", "body", "nested-text", "child content is unsupported"),
]
for operation, first, second, expected_error in rejections:
    rejected = subprocess.run(
        [
            sys.executable,
            str(scripts / "shape_boolean_svg.py"),
            "render", str(source), "--operation", operation,
            "--source", first, "--source", second,
            "--id", f"reject-{second}",
        ],
        capture_output=True, text=True,
    )
    assert rejected.returncode != 0
    assert expected_error in rejected.stderr, rejected.stderr

run_tool(
    "svg_quality_checker.py", project,
    "--quick-generate", "--format", "ppt169",
    "--stage", "final", "--json",
)
pptx = project / "boolean-smoke.pptx"
run_tool("svg_to_pptx.py", project, "--quick-generate", "-o", pptx)
with zipfile.ZipFile(pptx) as archive:
    slides = [
        name
        for name in archive.namelist()
        if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
    ]
    custom_shapes = sum(
        archive.read(name).count(b"<a:custGeom>")
        for name in slides
    )
assert len(slides) == len(operations), slides
assert custom_shapes == expected_custom_shapes

readback = project / "readback"
run_tool(
    "pptx_to_svg.py", pptx, "-o", readback,
    "--inheritance-mode", "flat", "--strict",
)
slides = sorted((readback / "svg").glob("slide_*.svg"))
readback_custom_shapes = sum(
    slide.read_text(encoding="utf-8").count('data-pptx-custgeom="')
    for slide in slides
)
assert len(slides) == len(operations), slides
assert readback_custom_shapes == expected_custom_shapes
print(
    f"Shape Boolean smoke: passed "
    f"({expected_custom_shapes} custom shapes; {project})"
)
PY
```

The seven inline negative cases must return nonzero and match their expected
errors; every other command must pass. Open the printed
`boolean-smoke.pptx` path in PowerPoint: both shape-cut and text-cut Subtract
results must have real holes, and every Fragment sibling must remain separately
selectable.

## `compact_svg_coordinates.py`

Compact safe model-facing page-space coordinates without rewriting unrelated
SVG formatting:

```bash
python3 scripts/compact_svg_coordinates.py <svg-file-or-directory>
python3 scripts/compact_svg_coordinates.py <template-directory> \
  --inplace --keep-native-frames
```

The default run is a dry-run JSON report. `--inplace` atomically replaces only
changed legacy SVG files. `--keep-native-frames` compacts `data-pptx-bounds`,
translation values, rotation centers, and matrix `e/f`, while preserving canonical
authored-preset or inline native frames. `svg_authoring_view.py` separately
compacts imported model-facing frames because the compact authoring tree owns
visible coordinates; lossless backing only validates identity and recovers
supported non-visible semantics.

The compactor never rounds path/points geometry, normalized crop or nested
`viewBox` ratios, gradient offsets, opacity, scale arguments, rotation angles,
or matrix `a/b/c/d` coefficients. Type A mirror materialization invokes the
same tree-level implementation before its first write. The CLI is a migration
and diagnostic tool; standard authoring is checked read-only.

## `compact_svg_styles.py`

Diagnose or migrate older authoring SVG to shared root/group defaults plus
local overrides:

```bash
python3 scripts/compact_svg_styles.py <svg-file-or-directory>
python3 scripts/compact_svg_styles.py <svg-file-or-directory> --inplace
```

The default run reports proposed changes without writing. `--inplace` prepares
the complete input set first and then atomically replaces changed files. When
every rendered `<text>` has a resolvable typeface, the most common page
`font-family` becomes one root declaration. Descendants retain only true
exceptions. The same pass removes any supported inheritable presentation
attribute or inline declaration that exactly repeats its effective parent
value; it never invents a paint, size, weight, or other non-font default.

PPTX import projections and mirror materialization call the same tree-level
implementation before publishing their authoring SVG. Standard workflows do
not rewrite completed SVG: they pass `--canonical-authoring` to
`svg_quality_checker.py`, which reports any remaining deterministic change as an
advisory warning (run `compact_svg_styles.py <svg_output> --inplace` on
authored project pages and rerun the final gate to normalize, or keep the
explicit form). Structured template rosters keep their explicit form: per-slide
compaction would make shared Master/Layout atoms diverge and shift native
fallback hashes, so the normalizer is not applied to them; mirror
materialization compacts its own tree before publication. SVG-to-PPTX accepts
valid explicit declarations either way; canonical compact
authoring is a generated-source contract, not a compatibility restriction on
external SVG input.

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

`pptx_template_import.py` and `pptx_to_svg.py --roundtrip` invoke the same
extractor automatically inside their staging transactions. They use the
imported namespace and record thresholds in the adjacent vector inventory so
template materialization and round-trip export can regenerate the same
baseline before comparing edits. The CLI form is for external SVG and legacy
migration input, not a standard post-generation rewrite.

The first pass records a source fingerprint before namespacing each extracted
asset's internal ids. The second pass reuses a fingerprint-matched asset and
writes no duplicate SVG file. Unmatched flat-only subtrees still extract
normally. Use `--clean-stale` on both import-workspace passes to remove stale
generated files for their respective prefixes. In create-template workspaces,
`imported` is the fixed decoration-only namespace: assets live once under
`icons/imported/`, and the working SVGs reference them as
`data-icon="imported/<name>"`. Each asset root and placeholder declares
`data-pptx-asset-role="decoration"`; the v2 inventory repeats that role. The
extractor and both consumers fail closed if a semantic marker or semantic
descendant crosses this boundary. Inventory entries may retain source refs from
eligible decoration subtrees, allowing expansion to reconnect the
authoring-manifest mapping. A rerun on an
already rewritten namespaced projection inventories those references and does
not progressively extract their remaining parent or sibling geometry. An
in-place pass over an authoring bundle refreshes `authoring_summary.json`
automatically.

## `stamp_native_fallbacks.py`

After an SVG-first Chart/Table fallback and its inline JSON projection are
updated together, validate and bind the visible subtree explicitly:

```bash
python3 scripts/stamp_native_fallbacks.py <svg-or-directory> --write
```

Omit `--write` for a read-only preview. The command prevalidates every direct
Chart/Table marker, skips JSON-first markers, and atomically adds/updates only
`data-pptx-fallback-sha256` without reformatting the document. The fingerprint
detects later visible edits; it is not a semantic-equivalence proof.

## `mirror_template_materialize.py`

Validate and publish one Type A PPTX import workspace as a deterministic
structured mirror after Template_Designer has reviewed/authored the new compact
layered SVG:

```bash
python3 scripts/mirror_template_materialize.py \
  <import_workspace> <template_workspace>
```

The command treats `<import_workspace>/authoring-svg/` as the sole visible
editable source. It reads the tool-only layered authoring manifest internally
and validates source SVG/PPTX hashes, known refs, the source Slide roster and reachable Master/Layout
graph, inheritance visibility facts, source-ref closure, and extracted-vector inventory before it
writes anything. It accepts an absent/empty destination or a project
`templates/` containing unique qualified Brand/Style specs plus, for a
Layout-over-Deck transition, one qualified Deck spec with no staged roster. A
bare spec, active structural roster, SVG, Layout spec, or other template payload blocks direct
materialization; Create Template uses its isolated transition workspace when a
new Layout or Deck must be composed with the other structural kind. It stages the whole
result before atomic publication, so a failed preflight cannot leave a partial
template.

Materialization preserves source Slide order and only the Layout/Master chains
reachable from those Slides. Each source Slide becomes one standalone prototype
with Master + Layout + Slide context resolved. Explicit layer markers preserve
ownership; source Master/Layout identities unused by every Slide produce no SVG.
The v2 report lists source counts plus retained and omitted structure keys.
For PPTX-backed mirror input, `templates/source_themes.json` stores the exact
Theme bytes keyed by retained Master. Structured export validates that sidecar
against the Master roster and installs one Theme per Master; it is not an SVG
prototype or page-authoring input.
It mechanically expands fixed Master/Layout group wrappers into direct atoms,
publishes the current compact visible authoring tree for both changed and
unchanged refs, recovers only supported non-visible semantics such as explicit
text hard breaks, and removes every IR-only source ref. It never replaces an
ordinary visible subtree with lossless source XML. Imported axis-flipped groups retain their
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
text/tspan topology and attributes. These records are deterministic tool
diagnostics, not page-authoring inputs. Page-context emits only the complete
prototype's path and SHA for that reference, so the model reads the SVG once
per execution context and reuses it until the SHA changes. The model chooses
semantics and edits only permitted visible text values; a direct JSON-first
Chart/Table may regenerate its derived preview children while keeping marker,
metadata, bounds, and structure. Checker and
structured export validate output attributes, text/tspan topology, and
referenced-resource hashes against
the prototype.

The output routes reusable decoration vectors once to `icons/imported/`, image media to
`images/`, audio and video to their semantic directories, and opaque referenced
files to `native-payloads/imported/`. The JSON report
reports payload occurrence, native-record, unique-byte, and compressed-store
counts and is written to stdout only. The command intentionally does not create
`templates/design_spec.md`; Template_Designer writes the package-specific rules
and page roster after publication. This validator/publisher is for Type A mirror,
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

When the effective Speaker Notes outcome in `design_spec.md §I` is enabled, run:

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

When Speaker Notes is disabled, skip `total_md_split.py` and use
`python3 scripts/svg_to_pptx.py <project_path> --no-notes` for the final
command. This prevents stale files under `notes/` from being embedded.

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

`svg_final/` is an optional Step 7.2 preview artifact; the native exporter reads `svg_output/` and never requires it. It is the self-contained visual reference and may be manually inserted as an SVG picture.

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

Native formulas use the two markers owned by
[`native-formula.md`](../../references/native-formula.md). A standalone block
stores delimiter-free LaTeX in the JSON metadata of
`<g data-pptx-replace-with="formula">` and exports `m:oMathPara`. A leaf
`<tspan data-pptx-inline-formula="...">preview</tspan>` inside ordinary text
exports `m:oMath` in the same DrawingML paragraph as its surrounding runs; it
inherits computed size and visible solid fill, then uses the project text
language and Cambria Math.
Matrices, multiline derivations, and other high-structure expressions remain
blocks. Formula replacement is always active, independent of
`--native-charts-and-tables`: export replaces only the registered SVG preview
and writes editable PowerPoint 2010+ Office Math. It emits no formula PNG, media
relationship, or compatibility fallback, and makes no rendering/editability
promise for Keynote, WPS, LibreOffice, or another non-PowerPoint client.

```bash
python3 scripts/svg_to_pptx.py <project_path>
# Explicit compact image export:
python3 scripts/svg_to_pptx.py <project_path> --image-sizing display --image-scale 2 --image-quality 85
# Force original image bytes:
python3 scripts/svg_to_pptx.py <project_path> --no-image-optimize
python3 scripts/svg_to_pptx.py <project_path> --native-charts-and-tables
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure structured  # deck/layout template override
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure flat  # free-design/brand-only override
# Template-import visual round-trip diagnostic only:
python3 scripts/svg_to_pptx.py <template_import_output> -s svg-flat
# Editable authoring-svg-flat/ -> source-preserving PPTX round-trip:
python3 scripts/svg_to_pptx.py <pptx_import_output> --roundtrip
# The same compatibility mode defaults to svg_output/ when -s is omitted:
python3 scripts/svg_to_pptx.py <project_path> \
  --enable-dangerous-nonconforming-svg-export
# Post-processed-source comparison diagnostic only (never a release export):
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> --no-notes
python3 scripts/svg_to_pptx.py <project_path> -t none
python3 scripts/svg_to_pptx.py <project_path> --auto-advance 3
python3 scripts/svg_to_pptx.py <project_path> --animation mixed --animation-duration 0.8
python3 scripts/svg_to_pptx.py <project_path> --reflow-text  # opt-in PowerPoint reflow
python3 scripts/svg_to_pptx.py <project_path> --no-merge    # one text frame per visual line
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio --animation-config animations.json
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio --no-animations
```

Native image export defaults to `--image-sizing cap`: it preserves source bytes
when no resize or EXIF geometry normalization is required, and re-encodes only
images that require one of those transformations. The `display` command above
is an explicit compact export; `--no-image-optimize` disables all native image
optimization and forces original bytes.

The normal command reads `pptx_structure.mode` from `spec_lock.md`. For legacy
projects whose lock exists but predates that field, export emits one compatibility
warning and uses `flat`; no SVG regeneration is required. A missing `spec_lock.md`,
an explicit legacy/unknown mode, or a requested `structured` export without an
explicit current structured contract remains blocking.

Explicit direct generation may use the
[`quick-generate`](../../workflows/profiles/quick-generate.md) profile after the
current agent has converted/read sources, researched identified factual gaps,
prepared the required images, icons, and resource manifests as needed, and
retained any source LaTeX for direct native-marker authoring. That profile skips Strategist, Confirm UI, `design_spec.md`, and
`spec_lock.md`; it does not skip the resources required by the authored pages.
After the complete SVG roster exists, run its lockless final checker, then
export:

```bash
python3 scripts/svg_quality_checker.py <project_path> \
  --quick-generate --canonical-authoring --stage final --json
python3 scripts/svg_to_pptx.py <project_path> --quick-generate
```

This direct-export flag takes `svg_output/` as its authored page source, resolves
valid project-local resources referenced by those pages, infers one consistent
canvas, and does not read or require `spec_lock.md`. It infers one all-page PPTX
structure mode from the authored SVGs: no structure metadata creates clean flat
package scaffolding; any structure metadata requires every page to satisfy the
complete Master/Layout/slot contract and creates structured output. A mixed or
partial roster fails closed. Notes, motion, narration, native objects, conversion
trace, and other ordinary exporter capabilities remain available; notes,
custom object animation, and narration start off in Quick and may be enabled
when needed. The exporter refuses a missing, blocking, non-final, or stale
Quick final report before PPTX creation. Default-path output retains the normal
postflight report and `backup/` snapshot; explicit `-o` retains the ordinary
no-backup behavior. Existing source, analysis, image/icon, and resource-manifest
artifacts remain untouched; formula source stays inside its authored SVG marker.

For generated-project narration, follow the
[`generate-audio`](../../workflows/stages/generate-audio.md) stage. It owns voice
selection, audio generation, and the narrated re-export workflow.

Behavior:
- Default output (either Generate profile, no `-o`):
  - `exports/<project_name>_<timestamp>.pptx` — native editable pptx (canonical output)
  - `validation/<project_name>_<timestamp>.report.json` — package postflight, quality-gate linkage, unresolved resource audit, and published part counts
  - `backup/<timestamp>/svg_output/` — copy of authored SVG source for re-export without re-running the LLM
- `exports/` contains only final PPTX deliverables; machine-readable quality and postflight reports belong in `validation/`.
- The default Generate flow always runs `finalize_svg.py` before export. This directory is the self-contained SVG visual preview; it is not packaged as a second PPTX. Quick-generate deliberately skips it.
- In both Generate profiles, explicit `-o/--output` changes the native PPTX destination and skips `backup/`; the postflight report still uses the output stem under the project `validation/` directory.
- A custom `-s/--source` also skips `backup/`: that directory remains the caller-owned SVG source and is never copied under a misleading `backup/<timestamp>/svg_output/` name. Default or explicit `-s output` export retains the normal SVG backup behavior.
- Postflight reruns ZIP integrity and published Slide count. Internal relationships,
  structured-package validation, transitions, and animations are enforced before the
  builder publishes the PPTX and are reported as `enforced-at-build`, not as repeated
  postflight checks.
- `font_portability` warns when a complete font stack has no concrete family or when
  the converter resolves its Latin / East Asian role to a typeface that normally
  requires a custom installation. A recommended stack such as
  `"Microsoft YaHei", Arial, sans-serif` does not warn merely because it ends with a
  generic fallback.
- Multiline text export modes:
  - Default: one editable frame retains authored breaks and disables PowerPoint wrapping. An ordinary generated frame uses PowerPoint's native resize-shape-to-fit-text behavior, so deleting a retained break expands the frame instead of leaving text outside it; imported exact frames and structured multiline placeholder carriers retain fixed-size behavior.
  - `--reflow-text`: eligible same-size lines become flowing prose that PowerPoint may rewrap; a font-size change, list marker, or accepted larger gap remains a paragraph boundary. Legacy `--merge-paragraphs` aliases this mode.
  - `--no-merge`: each dy-stacked line becomes an independent frame with its own placement.
  - Detection is conservative: mixed-layout `<text>` falls back to per-line frames. Use `--reflow-text` only for resizable body copy and `--no-merge` only for independent line objects or absolute line positions.
- Native release export reads `svg_output/`; `-s <directory>` selects another project-relative SVG source. `-s final` remains an explicit diagnostic comparison against post-processed SVGs and does not change artifact ownership. `--enable-dangerous-nonconforming-svg-export` is a separate, explicitly requested flat compatibility path for either the default or selected source; it forces flat structure, restores no imported source object, and cannot combine with `--roundtrip` or `--quick-generate`.
- `--roundtrip` accepts only `authoring-svg-flat/` and the source/contracts emitted by `pptx_to_svg.py --roundtrip`; predecessor root sidecars and alternate `-s` inputs fail. It restores unchanged refs from `analysis/roundtrip-svg/`, preserves unchanged Slide XML/relationships and source resources byte-for-byte, rebuilds a page whose authoring changed, and rebuilds every output page that references a changed resource. Closed unchanged chart packages recover exactly; editing their fallback disables stale replacement. Optional root `page_plan.json` uses the versioned deck-plan contract above; the no-plan path remains the identity export. Explicit `-t <effect>` without `--transition-duration` on a source without transitions uses the default duration.
- `svg_final/` may be opened directly or inserted into PowerPoint as an SVG picture. PowerPoint's manual Convert-to-Shape operation is outside the compatibility contract.
- On every SVG-authoring route, each file in `svg_output/` is the complete visible
  page-design source. Templates and locks may guide authoring, but finalize/export
  never use them to overlay visible content missing from the SVG. Notes, animation,
  narration, transitions, and direct native-PPTX workflows keep their separate
  inputs and package-level processing.
- For PPTX template-import workspaces, use `-s svg-flat` when you need a visual round-trip check. The layered `svg/` tree is the machine-readable template source and intentionally does not inline inherited master / layout decoration into each slide.
- Native mode is strict about unsupported visual SVG elements: if a visual element cannot be represented or safely preserved, export fails with the SVG file, element tag, and position instead of silently dropping content. Dangerous compatibility export first applies the registry in `svg_compatibility.py`; it currently lowers a filter on an otherwise attribute-free one-child group whose child is a supported native filter target. The complete strict preflight then runs normally; every remaining contract, resource, conversion, relationship, or package error still blocks export.
- Default export omitting `--pptx-structure` reads `spec_lock.md`. Free-design, brand-only, and `template_reuse_scope: style` releases declare `mode: flat`, omit Master/Layout mappings and SVG structure metadata, and materialize one clean project-owned Master plus one Blank Layout from the current lock. Deck/layout templates use `mode: structured` only for `template_reuse_scope: mirror|layout`, with complete unique `pptx_masters` / `pptx_layouts` rosters and one `page_pptx_layouts` assignment per page. A template-backed Layout definition may remain unused by pages and still register in the final package.
- On structured template routes, every page root repeats Master/Layout keys and picker names. Master/Layout fixed visuals are direct semantic atoms. Ordinary layer `<g>` elements are invalid; one validated compact authored-preset `<g>` emitted by `preset_shape_svg.py` is the sole group exception because it compiles to one native shape.
- Every visible direct root `<g>` except a compact helper-authored preset atom requires root-coordinate `data-pptx-bounds`; nested bounds are ignored. The text-free preset atom remains top-level when standalone, uses `data-pptx-frame`, and never carries bounds. Frame/native metadata never replaces bounds on any other group; placeholder bounds also define the slot frame. Checker fails ordinary direct-root module pairs whose intersection exceeds `1px` on both axes; complete structured slots, registered structural-role groups, and wholly off-canvas Morph staging groups are excluded, while ordinary Slide-local groups remain checked on structured pages. Checker compares root bounds with `viewBox`, estimable descendant text—including the canonical direct first line plus later positioned tspan form—with its module using DrawingML wrapping headroom, and every estimable visible text carrier directly with the root `viewBox` before that headroom. Images, shapes, paths, `<use>`, effects, and object frames are excluded from module containment. Per side, ≤`1px` is ignored; module overflow ≤`5%` warns and >`5%` fails, while larger page text overflow always fails. Bounds never clip/reflow; unestimable visible text warns. A wholly off-canvas direct-root Morph endpoint may opt out of page containment with `data-pptx-morph-staging="true"`; it still needs valid module bounds, retained Morph uses an explicit pair, and partial overflow remains blocking.
- Missing required root bounds fails on final pages/templates and under `--template-mode`; references warn until adapted.
- On structured template routes, each normal slot is a direct root `<g id>` with semantic type, positive design-zone bounds, and exactly one compatible carrier. Composite `object` slots use explicit proxy binding; zero-slot Layouts are valid. Flat pages keep all SVG objects Slide-local.
- Flat export maps locked typography/colors into a clean project-owned theme/Master, removes stock content placeholders and unused built-in Layouts, retains only the standard date/footer/slide-number capability hooks, and keeps one Blank Layout without promoting Slide content. Structured export additionally creates one reusable Layout per declared key and reopens the package to verify the full Presentation → Master → Layout → Slide graph, fixed-object order, placeholder identities/bounds, carrier bindings, hidden proxies, and zero-slot Layouts.
- Template `page_layouts` remains input provenance. Strict preserves the prototype contract; adaptive keeps its Master; new Layouts require Default plan/lock or Quick's frozen Template Application. Construction cannot allocate or mutate Layout identity downstream.
- Legacy structured/template contracts using `baseline`, `template`, `preserve`, `layout_strategy`, `data-pptx-layout-kind`, `distilled`/`utility`, direct atomic placeholders, or incomplete Master identity are rejected with a pointer to [`create-template`](../../workflows/create-template.md). Create a new workspace and generate new structured SVG pages; do not upgrade the existing project in place. Explicit flat free-design/brand-only projects intentionally omit Master identity.
- Native output uses content-hash media filenames, so identical images are reused and different images cannot overwrite each other by sharing a basename.
- `[Content_Types].xml` is generated from the actual media extensions written into the PPTX. Unknown media extensions fail unless Python's `mimetypes` can identify them.
- Native export writes to a temporary file first and publishes the requested PPTX only after conversion succeeds. A failed conversion does not replace the main output file.
- `--conversion-trace` without a path writes `validation/<output_stem>.trace.json`. `--conversion-trace <path>` respects the explicit destination; relative paths are resolved from the project root, so `exports/<name>.trace.json` remains available when intentionally requested.
- Formal default and `--quick-generate` release export compute the exact SVG source fingerprint and refuse a missing, unreadable, unsupported, non-final, blocking, stale, or unverifiable final quality report before PPTX creation. A project without `validation/svg_quality_report.json` exits nonzero with the `not-provided` gate status; run the final checker against its current `svg_output/` first. An explicit non-`output` `--source` remains outside this release gate. Dangerous compatibility export also stays outside it even when reading the default `svg_output/`: it automatically writes a conversion trace, marks postflight `passed-with-warnings`, and records its normalization count; it never claims that the source passed the normal authoring quality gate.
- The final quality report carries an informational `carrier_receipt` aggregate plus each page's `files[].info.carrier_receipt`: actual text/image/icon counts, SVG geometry, native preset names, marker use, native Chart/Table/Formula markers, largest image-frame share, and effect use. `effects.inline_emphasis_runs` counts `<tspan>` elements inside `<text>` with no `x`/`y`/`dx`/`dy` that set `fill`, `font-weight`, `font-size`, `font-style`, `text-decoration`, or `letter-spacing`; `effects.gradient_uses` counts visible fill/stroke references that resolve to same-document linear/radial gradients; `effects.filter_uses` counts visible filter references that resolve to same-document filters; and `effects.text_effects` counts visible `<text>`/`<tspan>` elements with gradient/pattern paint, a filter, or a non-`none` stroke. Content inside `defs`, `clipPath`, `mask`, `pattern`, `marker`, or `symbol` is excluded. The terminal prints only the compact aggregate. These facts never affect exit status, create coverage quotas, or score design; the active Generate profile compares them with its retained page decisions before export.
- After publication, native export writes `validation/<output_stem>.report.json`. The report distinguishes authored Slides from internal Layout definitions, reruns ZIP integrity and published Slide-count checks, records slide/layout/master/notes part counts, labels relationship/structured/transition/animation validation as enforced at build time, links the final SVG quality report only when its SHA-256 source fingerprint matches the exact export inputs, and surfaces stale/unverified gates, unresolved template tokens, generic-only font stacks, and external image references. A matching final quality report with introduced warnings yields `passed-with-warnings` and a `quality_introduced_warnings=<N>` receipt instead of a clean `passed` claim.
- By default, a successful command also prints a compact receipt instead of requiring a report read: `[POSTFLIGHT] status=<...> quality_gate=<...> slides=<N> warning_categories=<N>`, followed by one compact line per warning category and the `[PPTX]` / `[REPORT]` paths. Resource-warning lines carry counts; a non-passing quality gate carries its status. Routine agents use this receipt and do not load either complete validation JSON into model context. Full reports remain cold audit artifacts; failure investigation and explicit audits extract only the required fields. `--quiet` keeps suppressing successful-run output.
- Before publishing structured template output, export reopens the temporary PPTX and validates the Slide → Layout → Master graph and registrations, Layout identity, placeholder identity, reusable bounds, and prompt/level-one sizes. A mismatch aborts publication. Flat release instead validates its single referenced Master/Layout shell and exact date/footer/slide-number hook roster before packaging.
- Authored SVG clip-path restrictions remain. Crop wrappers use an
  overflow-hidden viewport; preview-safe shape clips target the inner image in
  viewBox coordinates, while legacy imported wrapper clips remain compatible.
  Both map to native picture crop/geometry when possible.
- The default Generate flow embeds speaker notes automatically unless `--no-notes` is used; Quick Generate defaults them off and enables them with `--with-notes`
- Recorded narration is opt-in:
  - `notes_to_audio.py` uses `edge-tts` by default, or a configured cloud TTS provider (`elevenlabs`, `minimax`, `qwen`, `cosyvoice`), and generates one audio file per slide into `audio/`
  - Narration text is read strictly from the matching `notes/*.md` file; the script only skips Markdown heading lines (`# ...`) and does not summarize, rewrite, or filter delivery notes
  - `--recorded-narration audio` prepares PowerPoint's "recorded timings and narrations": every slide must have matching `m4a` / `mp3` / `wav` audio, `ffprobe` must read every duration, and `--animation-trigger on-click` is rejected
  - `--recorded-narration audio` keeps speaker notes, embeds each matching audio file, and writes slide auto-advance timings from page-start lead-in + audio duration + page-tail padding. `--narration-start-floor` and `--narration-padding` are independent optional seconds; their defaults are `0.8` and `0.5`, and the post-transition lead-in is `max(0, start floor - transition duration)`
  - While motion remains enabled, narrated export without an explicit `--animation-config` selects `<project>/narration_animations.json` when either animation sidecar exists; canonical-only cue synchronization therefore blocks until the derived file exists. Narration-independent custom motion explicitly passes `--animation-config animations.json`, even when a derived sidecar also exists
  - Without animation sidecars, Generate narration may inherit base-report deck motion via `--inherit-motion-from`; direct low-level omission keeps legacy `fade` / no object builds. Use `--no-animations` to remove object/page motion while retaining narration timings
  - Non-narrated export keeps the existing optional `<project>/animations.json` default
  - Narration timing merges into the existing slide timing DOM. While motion remains enabled, object-animation rows and the resolved page transition are preserved rather than regenerated; inherited `-a none` suppresses object rows, and `--no-animations` removes both motion layers
  - `--narration-audio-dir audio` is the lower-level embedding path: it embeds whatever files match and allows partial audio coverage
  - Either narration flag names the default-flow export `<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports in the same directory
  - This is intended for direct PowerPoint video export with "Use recorded timings and narrations"
  - Long-audio import and automatic long-audio splitting are not supported; keep narration assets page-level
  - Voice choices can be listed with `python3 scripts/notes_to_audio.py --list-common-voices`, `python3 scripts/notes_to_audio.py --list-voices --locale zh-CN`, or provider-specific `--provider <name> --list-voices`
- Page transitions are controlled by `-t/--transition`; per-element object animations are controlled by `-a/--animation`
- Per-element animation applies to ordinary top-level SVG `<g id="...">` groups; each group is a PowerPoint shape-target anchor, not necessarily one Animation Pane row. Use one group per logical Slide-local content unit rather than targeting a group count. Master/Layout atoms and slot groups are structural and excluded; exact id tokens remain a fallback only when explicit structural roles are absent
- An explicit `animations.json` group entry may override the marker-free legacy chrome-name heuristic. It cannot override `data-pptx-layer` or an explicit static role/placeholder marker
- Start mode is set globally by `--animation-trigger`, mirroring PowerPoint's Start dropdown: `after-previous` (default, cascade with `--animation-stagger` spacing on slide entry), `on-click` (presenter-paced), or `with-previous` (all together on slide entry). A sidecar row may override it with `trigger`; the slide value is only the inherited Start mode
- `on-click` is for live presentations only; recorded narration rejects every row that resolves to it, including a row with `trigger_shape`, because the tool does not generate object-level click timings
- Flat SVG roots without top-level groups fall back to at most 8 visible primitives; beyond that, animation is skipped on the slide
- Per-element animation defaults to `none`. `auto` is opt-in (`-a auto`) and maps
  generic entrance effects from the group's SVG id: information-dense elements
  get a stable entrance (chart→wipe, card-/step-/pillar-→fly,
  title/takeaway→fade); image-like and unmatched ids rotate through bounded
  entrance pools.
- `mixed` (legacy) deterministically rotates through the canonical entrance pool; `random` selects from the same entrance pool with a stable seed from the effective deck input. `auto`, `mixed`, and `random` never choose emphasis, motion-path, or exit effects; select an explicit canonical `entrance_*`, `emphasis_*`, `path_*`, or `exit_*` key for those authored duties. `--conversion-trace` records each resolved effect when enabled
- `--animation-duration` controls the inherited per-row schedule length (default
  `0.4`); scalable native effects preserve internal timing ratios, while
  instantaneous presets keep their authored duration. `--animation-stagger`
  supplies the default gap between successive non-trigger-shape rows in
  `after-previous` mode (default `0.5`)
- Optional object-level overrides live in `<project>/animations.json` or a path passed via `--animation-config`; build and validate them with `animation_config.py scaffold|validate`. The scaffold is neutral (`defaults.animation.effect: none`, untouched groups `{}`). A populated group uses either the fully compatible legacy single-effect fields or a non-empty `effects[]`, never both; every `effects[]` row names an explicit effect
- Transition/object sound remains off by default. After SVG and visual motion are complete and one row has a concrete auditory job, read the complete [`sound-vocabulary.md`](../../templates/sounds/sound-vocabulary.md), then copy only selected ids with `sound_sync.py <project> <namespace>/<sound_id> [...]`; `list --query <term>` is optional exact filtering after that review. `transition.sound` references a project-relative `.wav`; object-animation `sound` accepts the existing `.m4a`/`.mp3`/`.wav` path contract, while bundled selections use the synced project-relative `.wav`. With no selected cue, do not create `<project>/sounds/`. Export never resolves ids or reads `templates/sounds/` directly
- One `effects[]` row becomes one Animation Pane record on the group's shape target. Each row may independently set sequence `order`, `delay`, `duration`, `trigger`, and `trigger_shape`; ordinary rows use page-wide order, while `trigger_shape` rows keep relative order in separate interactive sequences and imply `on-click`
- Animation configuration is strict: unknown effects/modes/triggers, invalid finite/range/order values, missing slides/groups, and structural-layer targets fail export without fallback or silent omission
- Generated export reads every slide back and verifies animation row order, including repeated rows on one shape target, trigger, shape target, resolved effect tuple and native behavior signature, duration, and offset. Package validation then checks timing placement, `p:cTn` ids, and `p:spTgt` references before publication
- The animation writer does not emit paragraph/text-range builds (`p:bldP`), custom freeform motion paths, native Chart/SmartArt build sequences, or media playback commands for grouped SVG content. Direct-PPTX routes preserve source object animation and perform structural package validation only; they do not author effects
- The full registry, OOXML rules, and compatibility boundary are documented in [`pptx-animations.md`](./pptx-animations.md)

Dependency:

```bash
pip install python-pptx
```

### Structured export mechanics

Checker and exporter behavior behind [`pptx-structure-interface.md`](../../references/pptx-structure-interface.md) §2.

**Master text styles**: the effective `title` anchor maps to every `a:defRPr@sz` in Master `p:titleStyle`. Level 1 in `p:bodyStyle` and `p:otherStyle` uses the `body` anchor; levels 2–9 descend deterministically from `15/16` through `8/16` of that size, rounded to 0.5 pt and floored at the smaller of 8 pt or the body size. Only `p:txStyles//a:defRPr@sz` changes; indentation, bullets, margins, paragraph settings, and direct run sizes on generated slides are untouched. Default reads the anchors from `spec_lock.md`; missing `title` / `body` rows fail flat or structured export. Structured Quick infers anchors from semantic slot carriers with deterministic fallbacks; flat Quick keeps stock defaults.

| Master style | Effective source | XML field changed |
|---|---|---|
| `p:titleStyle` | title anchor | every `a:defRPr@sz` |
| `p:bodyStyle` | body anchor | level 1 plus derived level 2–9 `a:defRPr@sz` |
| `p:otherStyle` | body anchor | level 1 plus derived level 2–9 `a:defRPr@sz` |

**Layout level-one text default**: for every text-bearing placeholder whose first prototype run has a direct `a:rPr@sz`, export copies that size to the generated Layout prompt run and `p:txBody/a:lstStyle/a:lvl1pPr/a:defRPr@sz`; Slide direct runs and Layout levels 2–9 are not rewritten.

**Placeholder identity**: export writes the semantic type on both the Layout and Slide carrier (except `obj`, already the OOXML default). Date, footer, and slide-number placeholders enable the matching Layout `p:hf` flags; a date placeholder also gets a `datetimeFigureOut` field in the Layout while the Slide keeps its authored date text. An omitted `p:ph@idx` has effective value `0`, so an omitted-index title reserves `0`; every other indexed placeholder on that Layout uses a unique OOXML UInt32 index. An imported title with an explicit index keeps that exact index.

**Text carriers**: a multiline text placeholder stays one native text frame under default export and `--reflow-text`; `--no-merge` cannot supply several line shapes as one placeholder. A whitespace-only marked carrier materializes one invisible U+200B run so it still becomes a native text shape. On a materialized mirror, an imported text carrier may keep the source shape's positive `data-pptx-frame="x y width height"`; that frame owns the Slide carrier `a:xfrm` and the converter reconstructs text-body insets from the visible anchor/baseline instead of shrinking to glyph bounds, while `data-pptx-bounds` remains the reusable Layout default.

**Visibility attributes**: `data-pptx-show-master-shapes` writes the Layout's `p:sldLayout@showMasterSp` and must repeat the same value on every SVG sharing that Layout key; `data-pptx-show-inherited-shapes` writes this Slide's `p:sld@showMasterSp`. Both accept only exact lowercase `true` / `false`; omission means `true`.

**Static structure consistency**: the same master element ids on every slide and the same layout element ids on every slide sharing a layout must compile to identical OOXML within that group. Static objects may carry shapes, text, or images; non-image/external relationships are rejected. Interleaved layers fail: paint order is Master background, Layout background, optional Slide background, remaining Master atoms, remaining Layout atoms, then slot groups and Slide-local content. Structured export narrows background ownership to a direct full-canvas solid `<rect>` and disables the generic conversion-level promotion; an unmarked full-canvas solid rect in the background plane is treated as Slide scope.

**Final-package read-back gate**: before publishing, export reopens the temporary structured PPTX and verifies that each Slide targets exactly one Layout, one Layout key resolves to one part, distinct keys do not collapse, and every declared Layout—including unused ones—is registered through its Master and the Presentation; that physical Slide/Layout/Master part rosters, content-type overrides, and registrations are exact; the Layout picker name, Master picker identity, placeholder type and effective index, `p:hf` flags, design-zone frame, prompt size, and level-one default size; every owned `p:bg` as an exact zero-or-one payload against the pre-promotion result (preserving the base Master background when none replaces it); the exact top-level shape-name roster and order of every Slide, Layout, and Master; carrier-bound slot bindings, ordinary composite visible carriers, hidden composite proxies, and zero-slot Layouts with no placeholder. Later Slides may keep different Slide-local geometry; only the reusable Layout frame is checked. Any mismatch fails export without replacing the requested output.

### Native formula compiler

Behind [`native-formula.md`](../../references/native-formula.md) §3. The compiler implements every explicitly named LaTeX-to-OMML input in Microsoft's documented [Microsoft 365 LaTeX profile](https://learn.microsoft.com/en-us/office/math/latex) (Windows 2606 / Mac 16.110) and [mhchem profile](https://learn.microsoft.com/en-us/office/math/latex.mhchem) (Windows 2605 / Mac 16.109): outer delimiters, listed symbols and relations, fractions and binomials, roots, right and left scripts, delimiters and `\middle`, accents, bars and group characters, limits, all 21 listed n-ary operators, standard/custom functions, matrices and equation-array environments, CD diagrams, fonts and local colors, boxes and phantoms, spacing, global 0–9 argument macros, and the documented `\ce` chemistry grammar. Microsoft's open-ended "etc." wording defines no undisclosed names; only explicitly named commands and retained project aliases are contractual. The closed command tables in `svg_to_pptx/native_objects/formula_profile.py` are the executable vocabulary; the compiler facade and OMML structure gate are `formula_compiler.py` and `formula_omml.py`, with `formula.py`, `formula_ast.py`, `formula_parser.py`, `formula_run_properties.py`, and `inline_formula.py` alongside.

**Normalization**: `\dfrac` / `\tfrac`, `\dbinom` / `\tbinom`, and continued-fraction alignment normalize to the corresponding OMML structure; explicit big-delimiter grades become auto-sizing delimiters; `\mathscr` → `\mathcal`; `smallmatrix` → `matrix`; array columns become centered; style/size commands and equation tags are accepted but not stored. Color is stored in generated formula runs and structural control properties; `\boldsymbol` / `\bm` applies bold-italic to structural control glyphs.

**Fail-closed**: unknown commands or environments, Microsoft's explicitly unsupported commands, unsupported mhchem arrows, unescaped `%` comments, invalid macros, and resource-limit overflow block conversion — stricter than Microsoft 365's literal-text passthrough and macro-limit behavior.

**Compatibility**: the package uses standard editable Office Math and keeps the PowerPoint 2010+ target; the executable profile is pinned to the documentation versions above. Repository verification covers compilation, OMML structure, and PPTX packaging, not a Microsoft 365 UI rendering/editability certification. Earlier PowerPoint versions are not the source-profile baseline; WPS, Keynote, LibreOffice, and other clients receive no embedded fallback. Reverse import is described in [`conversion.md`](conversion.md#native-formula-reverse-import).

## `visual_review.py`

Pure render-and-validate tool for the [`visual-review`](../../workflows/stages/visual-review.md) stage; it never edits SVGs and reads no rubric rule.

```bash
python3 scripts/visual_review.py <project_path> [--pages <token> ...] [--server-url http://127.0.0.1:<P>]
```

- Requires `playwright` plus chromium and a running live-preview server for the same project; without `--server-url` it discovers the port from `<project>/live_preview/lock.json`, and in either case validates `/api/health` against the target project and rejects a server for another project.
- Output PNG matches the live-preview browser (inlined `<use data-icon>`, resolved `<image href>`); the root SVG `viewBox` is the canvas source of truth, and each successful page record carries `view_box`, `width` / `height`, and raster `png_width` / `png_height`; output dimensions equal that record's raster size. A record with `"all_background": true` rendered to a blank surface.
- Renders are serialized by `<project>/.preview/.render.lock`, so concurrent invocation is safe.
- Exit codes: `0` all requested pages rendered; `2` live-preview server unreachable or serving a different project; `3` playwright/chromium missing or unable to launch; `4` page-level render failure (details on stderr, partial output on disk).

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

## Measuring, wrapping, and calibrating text before authoring

`text_measure.py` imports the same single-line DrawingML width estimator used by
the SVG quality checker.

- `measure` prints one `width<TAB>text` line per input, or a JSON array with
  `--json`.
- `wrap` prints greedy word- or CJK-cluster-wrapped SVG text content; `--y`
  includes the outer `<text>` element, and `--json` prints line metrics.
- `box` prints a `data-pptx-bounds` attribute plus numeric `top` and `bottom`, or
  a JSON bounds object with `--json`.
- `calibrate` measures fixed CJK and Latin samples for every typography role
  from `spec_lock.md` or repeatable `--role NAME:FAMILY:SIZE` overrides, writes
  `validation/text_calibration.json`, and prints a compact table or JSON. Add
  `--outline` to include the longest planned line per mapped role from Design
  Spec §IX.

```bash
python3 scripts/text_measure.py measure "Editable DrawingML text" --size 22
python3 scripts/text_measure.py wrap "Editable DrawingML text stays measurable" --size 22 --max-width 240 --x 96 --dy 30 --y 140
python3 scripts/text_measure.py box "First line" "Second line" --x 96 --y 140 --size 22 --lines 2 --dy 30
python3 scripts/text_measure.py calibrate projects/example --outline
```

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
python3 scripts/svg_quality_checker.py projects/project/svg_output/01_cover.svg
python3 scripts/svg_quality_checker.py projects/project/svg_output
python3 scripts/svg_quality_checker.py projects/project
python3 scripts/svg_quality_checker.py projects/project --stage first-page
python3 scripts/svg_quality_checker.py projects/project --stage final --json
python3 scripts/svg_quality_checker.py projects/project --canonical-authoring --stage final --json
python3 scripts/svg_quality_checker.py projects/project --format ppt169
python3 scripts/svg_quality_checker.py --all projects
python3 scripts/svg_quality_checker.py projects/project --export
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
mistake a stale report for the current export gate. On a successful run, use the
checker exit status and terminal summary; do not load the complete JSON unless a
failure investigation or explicit audit requires targeted fields.

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

### Verification recipes

Used by the [`verify-charts`](../../workflows/stages/verify-charts.md) stage for chart objects whose geometry reduces to repeated direct calculations (`decomposable-calc` / `partial-calc`), a closed formula (`formula-verify`), or inspection only (`manual-verify`). Every recipe produces one receipt line; a page that cannot be reduced cleanly is marked `manual-verify` with the reason, never dropped.

**Stacked bar** — for N stacked series on the same categories, run `calc bar` N times. Pass each segment's height as the data value and shift `--area`'s `y_max` down by the sum of all lower segments for that category; compare each segment's `(x, y, width, height)`.

```bash
# two-series stack at "Q1" with bottom=30, top=20, plot y from 100 to 500
python3 scripts/svg_position_calculator.py calc bar --data "Q1:30,Q2:..." --area "x_min,100,x_max,500" --bar-width 80 --value-range=0,axis_max
python3 scripts/svg_position_calculator.py calc bar --data "Q1:20,Q2:..." --area "x_min,100,x_max,<500 - bottom_height_px>" --bar-width 80 --value-range=0,axis_max
```

**Stacked area** — run `calc line` N times on cumulative y-values (series 1 raw; series 2 = s1+s2; …); each call yields one band's top boundary, and each band's path closes to the previous band's top, not `y_max`. Negative segments or percent-stacked totals other than 100 are `manual-verify`.

**Dumbbell** — the two endpoints are points, not bar ends (`calc bar --horizontal` anchors at `x_min`). Number categories `0.5, 1.5, …, N-0.5` with `--y-range=0,N` (swap axes for vertical dumbbells), set `--x-range` from ticks, run `calc line` once per endpoint series with identical `--area` / ranges; each `(SVG_X, SVG_Y)` is the endpoint circle's `(cx, cy)`, and the connector is `x1=cx_left, x2=cx_right, y1=y2=cy`.

```bash
python3 scripts/svg_position_calculator.py calc line --data "42:0.5,55:1.5,37:2.5" --area "100,100,700,460" --x-range=0,100 --y-range=0,3
python3 scripts/svg_position_calculator.py calc line --data "68:0.5,71:1.5,49:2.5" --area "100,100,700,460" --x-range=0,100 --y-range=0,3
```

**Pareto** — `calc bar` on the descending values with the bar-axis range; precompute cumulative percentages; `calc line` on `0.5:cum1,…,N-0.5:cumN` with `--x-range=0,N`, the right-side percentage axis as `--y-range` (usually `0,100`), and the same `--area` (the `n - 0.5` offset centers each point on its bar). Compare bars, line, and markers separately.

**Dual-axis line** — read each Y-axis tick range independently; run `calc line` once per series with its own `--y-range` and a shared `--x-range` / area; never apply the left scale to the right series.

**Bullet** — bands overlap in one y row, so run `calc bar --horizontal` once per band with a single data point: `--data "<band>:<right_edge_value>" --area "<x_min>,<band_y>,<x_max>,<band_y+band_height>" --bar-width <band_height>` (widest band's right edge = axis max). Run once more for the actual bar with its inset area; the target marker is a `<line>` at `x = x_min + target/axis_max × area_width`.

**Butterfly** — read the value range and center-line `cx`; run `calc bar --horizontal` once per side with `x_min = cx`, `x_max = cx + side_width`; right bars map directly, left bars mirror as `x = cx - width`; verify both sides share `y + height/2` per category.

**Grouped bar** — with N series and group width `W`, each series bar is `W/N` wide at offset `(i - 1) × W/N`; run `calc bar` once per series with the same `--area` / `--value-range` and `--bar-width` set to the inner width; the per-category center is the group center, so `x = group_center - W/2 + (i-1) × W/N`.

**Box plot** — five y-values per category on one axis. Run `calc bar` once treating the box (Q3 − Q1) as a synthetic segment with `y_max` shifted to the Q1 baseline; median and whisker y = `y_axis_top + (axis_max - value) × pixels_per_unit`.

**Gantt** — pixels-per-unit from the header tick positions `(x_unit_n - x_unit_1) / (n - 1)`; run `calc line` over `start_index:row_y` and again over `end_index:row_y` — the two `SVG_X` values are `x` and `x + width`; row y is read directly. A qualitative stage/lane plan not derived from dates is not a chart and never enters verification.

**Waterfall** — compute running totals (`cum[i] = cum[i-1] ± delta[i]`, reset for totals); build `top[i] = max(cum_before, cum_after)` and `bot[i] = min(...)`; run `calc bar` twice with identical parameters — the `top` run's `Y` is `y`, `height = bot.Y - top.Y`; connectors run from `(x + width, Y_i)` to `(x_next, Y_{i+1})` at the shared cumulative value; total bars use `bot = 0`.

**Bubble / plotted 2×2 matrix** — `calc line` verifies `cx/cy` from x/y values and ticks. For `matrix_2x2`, the axis midpoint must match the quadrant split; Low/High-only axes need an explicit numeric mapping from the active §IX decision or an SVG comment, otherwise record `xy=manual (scale missing)`. Verify radius only when a size scale is declared (`radius = sqrt(value) * k` or min/max mapping) — `spec_lock.md` is not a size-scale authority; otherwise record `radius=manual (scale missing)` and inspect ordering by hand.

**Bar-of-pie / pie-of-pie** — replace the expanded tail with one aggregate value and `calc pie` the main pie; `pie_of_pie` runs `calc pie` again on the tail at the secondary center/radius, `bar_of_pie` verifies each detail height as `tail_value / sum(tail) × detail_height` with no gaps or overlap; the aggregate slice equals the sum of expanded values and connectors touch both plot regions.

**Stock** — `calc line` for open, high, low, close on the shared price axis; the wick spans `high_y..low_y`, the body `min(open_y, close_y)..max(...)`; body color follows `close >= open` and stays inside its wick.

**Formula-verify** (no calc call): progress bar `fill_width = value / max × track_width`; gauge `needle_angle = start_angle + value / max × sweep_angle`, compared against `transform="rotate(α …)"` or the endpoint `(cx + L·cos α, cy + L·sin α)`; funnel `top_width = prev.bottom_width`, `bottom_width = top_width × next_value / curr_value`, inset `(top_width - bottom_width) / 2`, first top width from the outer frame; sunburst arc length `node_value / root_total × 2πr` per ring with offsets from cumulative siblings plus any declared gap, children inside the parent span, siblings summing to the parent. The receipt quotes the formula and result (`formula=0.92×700=644px`).

**Manual-verify**: sankey — link widths proportional to flow, node totals in = out; heatmap — grid positions are fixed, verify each cell's color falls in the bin matching its value and extremes use the legend's high/low colors; treemap — `width × height ≈ total_area × value / sum(values)` for top-level cells, nested cells summing to the parent; word cloud — font sizes monotonic with declared weights or bins, then inspect bounds for overlap and clipping; position is layout-driven.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
python3 scripts/svg_finalize/flatten_tspan.py projects/<project>/svg_output
python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `align_embed_images.py`

```bash
python3 scripts/svg_finalize/align_embed_images.py path/to/slide.svg
python3 scripts/svg_finalize/align_embed_images.py --dry-run path/to/slide.svg
```

Use for rare single-file diagnostics when image `slice` / `meet` alignment and
Base64 embedding must be inspected outside `finalize_svg.py`. Embedded hrefs are
`data:<mime>;base64,...` with `image/png`, `image/jpeg`, `image/gif`,
`image/webp`, or `image/svg+xml`; recover an embedded payload with
`base64 -d image.b64 > image.png`. In normal project
runs, use `python3 scripts/finalize_svg.py <project_path>`; the old
`crop-images`, `fix-aspect`, and `embed-images` names remain accepted only as
`finalize_svg.py --only` aliases for the merged `align-images` step.

### `embed_icons.py`

```bash
python3 scripts/svg_finalize/embed_icons.py output.svg
python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Replaces project-local `<use data-icon="library/name" .../>` placeholders with
SVG paths. The exact case-sensitive file must exist under the workspace
`icons/`; bare, aliased, template-source, and unsynced references fail. Use
this only for manual checks outside `finalize_svg.py`.

## SVG Compatibility Contract

The always-on SVG authoring contract lives in
[`shared-standards-core.md`](../../references/shared-standards-core.md), with
advanced effects, native data objects, and structured PPTX metadata owned by
their conditionally loaded modules. The complete closed grammar those files
rely on — mapping tables, accepted-but-warned spellings, rejection boundaries,
and imported native-shape metadata — is documented in
[`svg-contract.md`](svg-contract.md). This tool guide does not repeat it.

`svg_quality_checker.py` validates source SVG before finalization.
`finalize_svg.py` and native export apply the preprocessing required by that
contract, while native conversion fails on unsupported visual elements rather
than silently dropping them.
