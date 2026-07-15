# Conversion Tools

> Architecture rationale (why native-Python first with pandoc fallback, why curl_cffi for TLS impersonation): see [docs/technical-design.md "Source Content Conversion"](../../../../docs/technical-design.md#source-content-conversion).

Source conversion tools turn PDFs, documents, slide decks, and web pages into Markdown before project creation.

Default workflow entry: use `source_to_md.py` unless a backend-specific
diagnostic or forced route is needed.

## Shared Output Contract

All `source_to_md` converters keep their existing Markdown output behavior and
now also write a lightweight sidecar profile when conversion succeeds:

| Output | Convention |
|---|---|
| Markdown | `<stem>.md` beside the local source unless `-o` selects another path |
| Asset directory | `<stem>_files/` when the backend extracts images or media |
| Image manifest | `<stem>_files/image_manifest.json` when image metadata is available |
| Conversion profile | `<stem>.conversion_profile.json` beside the Markdown output |

The conversion profile is metadata only. It records the converter, source path,
Markdown structure counts, asset directory, image manifest path, and image
count. Downstream PPT workflows still use the Markdown and image manifest as the
content/asset contract; the profile is for inspection and debugging.

## `source_to_md.py`

Unified dispatcher for ad hoc explicit-source conversion. It auto-detects each
listed input file or URL and calls the existing backend converter, so backend
behavior remains the source of truth.

Routing is centralized in `source_to_md/_dispatcher.py` and reused by
`project_manager.py import-sources`; do not add a second type-to-backend table.

```bash
python3 scripts/source_to_md.py paper.pdf
python3 scripts/source_to_md.py paper.pdf report.docx deck.pptx
python3 scripts/source_to_md.py ./sources
python3 scripts/source_to_md.py ./pdfs/*.pdf
python3 scripts/source_to_md.py ./decks/*.pptx
python3 scripts/source_to_md.py report.docx -o report.md
python3 scripts/source_to_md.py ./sources -o ./markdown  # explicit separate output directory
python3 scripts/source_to_md.py workbook.xlsx --json
python3 scripts/source_to_md.py deck.pptx
python3 scripts/source_to_md.py https://example.com/article -o article.md
```

Useful options:
- `-t pdf|doc|excel|pptx|web|markdown|text` forces a route when extension
  detection is not enough.
- `--json` prints a compact machine-readable result after success when the
  output path is known. With multiple inputs, each successful conversion prints
  its own JSON line after that source finishes.
- `--images all|filtered|none`, `--no-images`, and `--filter-images` map to the
  existing PDF image mode. They are intentionally PDF-only until other backends
  expose the same behavior natively.
- Unknown backend-specific flags are passed through to each selected converter.
- `-o/--output` selects one Markdown file for one input, or an output directory
  for multiple inputs / directory inputs.

For multi-source project intake, use `project_manager.py import-sources` with
all source paths / URLs. For local files, the default is to keep generated
Markdown/profile outputs beside the original source. `source_to_md.py` and the
backend converters support single files, explicit multi-file inputs, and
non-recursive directory inputs.

## `source_to_md/pdf_to_md.py`

Recommended first choice for native PDFs.

```bash
python3 scripts/source_to_md/pdf_to_md.py book.pdf
python3 scripts/source_to_md/pdf_to_md.py book.pdf -o output.md
python3 scripts/source_to_md/pdf_to_md.py book.pdf appendix.pdf
python3 scripts/source_to_md/pdf_to_md.py ./pdfs
python3 scripts/source_to_md/pdf_to_md.py ./pdfs -o ./markdown  # explicit separate output directory

# Image extraction control (default: filtered)
python3 scripts/source_to_md/pdf_to_md.py book.pdf --images filtered  # size/quality filters applied
python3 scripts/source_to_md/pdf_to_md.py book.pdf --images all       # extract all images, no filtering
python3 scripts/source_to_md/pdf_to_md.py book.pdf --images none      # skip all images (text only)
```

Use cases:
- Native PDFs exported from Word, PowerPoint, LaTeX, or similar tools
- Privacy-sensitive documents that should stay local
- Fast first-pass extraction before falling back to OCR-heavy tools

Prefer MinerU or another OCR/layout tool when:
- The PDF is scanned or image-based
- Multi-column layout parsing is poor
- Encoding is garbled

Dependency:

```bash
pip install PyMuPDF
```

## `source_to_md/doc_to_md.py`

Hybrid converter: pure-Python for the common formats, pandoc fallback for the rest.

Native path (no external binary required):
- `.docx` — via `mammoth`; text-only tables are preserved as pipe Markdown, and OMML / Office Math equations (Word-native or MathType "Convert to Office Math") are rewritten to inline LaTeX. Classic MathType OLE objects carry no OMML and are kept only as their preview image.
- `.html` / `.htm` — via `markdownify` + `beautifulsoup4`
- `.epub` — via `ebooklib` + `markdownify`
- `.ipynb` — via `nbconvert`

Pandoc fallback (only if you need these):
- `.doc`, `.odt`, `.rtf`, `.tex`/`.latex`, `.rst`, `.org`, `.typ`

```bash
python3 scripts/source_to_md/doc_to_md.py lecture.docx
python3 scripts/source_to_md/doc_to_md.py lecture.docx -o output.md
python3 scripts/source_to_md/doc_to_md.py lecture.docx notes.html
python3 scripts/source_to_md/doc_to_md.py ./docs
python3 scripts/source_to_md/doc_to_md.py ./docs -o ./markdown  # explicit separate output directory
python3 scripts/source_to_md/doc_to_md.py notes.epub
python3 scripts/source_to_md/doc_to_md.py paper.tex -o paper.md  # uses pandoc
```

Dependencies:

```bash
# Native path — always required
pip install mammoth markdownify ebooklib nbconvert beautifulsoup4

# Fallback path — only for .doc/.odt/.rtf/.tex/.rst/.org/.typ
# macOS:   brew install pandoc
# Ubuntu:  sudo apt install pandoc
# Windows: https://pandoc.org/installing.html
```

All paths produce the same output convention: `<input>.md` plus a sibling `<input>_files/` directory containing extracted images with relative references.
On success, a sibling `<input>.conversion_profile.json` is also written.

## `source_to_md/excel_to_md.py`

Excel workbook converter for presentation source intake.

Supported formats:
- `.xlsx`
- `.xlsm`

Unsupported by default:
- `.xls` — resave as `.xlsx` first

```bash
python3 scripts/source_to_md/excel_to_md.py report.xlsx
python3 scripts/source_to_md/excel_to_md.py report.xlsx -o output.md
python3 scripts/source_to_md/excel_to_md.py report.xlsx budget.xlsm
python3 scripts/source_to_md/excel_to_md.py ./workbooks
python3 scripts/source_to_md/excel_to_md.py ./workbooks -o ./markdown  # explicit separate output directory
python3 scripts/source_to_md/excel_to_md.py report.xlsm --max-rows 200 --max-cols 40
```

Behavior:
- preserves workbook and sheet structure in Markdown
- exports visible sheets only
- trims empty outer rows and columns
- propagates merged-cell labels for readable Markdown tables
- exports formula cells as cached values; it does not recalculate formulas
- writes `<input>.conversion_profile.json` after successful conversion

Dependency:

```bash
pip install openpyxl
```

CSV/TSV files are already plain-text table sources and do not require this converter.

## `source_to_md/ppt_to_md.py`

Structured PowerPoint-to-Markdown converter for Open XML slide decks.

Supported formats include:
- `.pptx`, `.pptm`
- `.ppsx`, `.ppsm`
- `.potx`, `.potm`

```bash
python3 scripts/source_to_md/ppt_to_md.py sales_deck.pptx
python3 scripts/source_to_md/ppt_to_md.py sales_deck.pptx -o output.md
python3 scripts/source_to_md/ppt_to_md.py sales_deck.pptx appendix.pptx
python3 scripts/source_to_md/ppt_to_md.py ./decks
python3 scripts/source_to_md/ppt_to_md.py ./decks -o ./markdown  # explicit separate output directory
python3 scripts/source_to_md/ppt_to_md.py template.ppsx -o notes/template.md
```

Behavior:
- extracts slide text in reading order
- converts PowerPoint tables to Markdown tables; cell-internal line breaks become `<br>` so they cannot break the pipe-table row structure
- transcribes category charts as category × series tables and scatter/bubble charts as typed X/Y[/size] point tables
- preserves every readable chart dimension or series and emits `[Chart data warning: <reason>]` for missing caches/count mismatches; `[Chart data unavailable: <reason>]` is reserved for charts with no readable points (and unsupported ChartEx), so XY data is never flattened into a misleading category table
- transcribes SmartArt semantic nodes as hierarchical Markdown; unreadable diagram data emits an explicit placeholder and conversion warning
- exports embedded pictures to a sibling `_files/` directory
- appends speaker notes when present
- writes `<input>.conversion_profile.json` after successful conversion

Dependency:

```bash
pip install python-pptx
```

Legacy `.ppt` is not parsed directly. Resave it as `.pptx` or export it to PDF first.

## `pptx_intake.py`

Standard enrichment layer for PPTX sources. It complements `ppt_to_md.py` rather
than replacing it: Markdown remains the normalized content source, while intake
artifacts provide source facts for Strategist and standalone PPTX workflows.

```bash
python3 scripts/pptx_intake.py deck.pptx -o projects/demo/analysis
```

Outputs (per source deck, prefixed by file stem):
- `<stem>.identity.json` — canvas size/aspect, theme palette/fonts, observed colors/fonts
- `<stem>.slide_library.json` — text slots, geometry, native tables, native chart display caches, and SmartArt nodes/connections
- `source_profile.json` — the single multi-deck index: a compact Strategist-facing digest per deck (over identity, tables, charts, SmartArt, and page types) under `decks[]`, with prefixed artifact pointers

`project_manager.py import-sources` runs this automatically for PPTX/PPTM/PPSX/PPSM/POTX/POTM inputs and stores the bundle directly under `analysis/`. Multi-deck per project: importing several PPTX files gives each its own `<stem>.*` artifacts and a `decks[]` entry in the shared `source_profile.json` index (re-importing the same stem replaces its entry). The beautify / template-fill workflows stay single-deck and read one chosen deck's `<stem>.*` artifacts.

Usage boundary:
- Standard generation uses these fields as facts and recommendation candidates; it does not inherit source slide coordinates or page order by default.
- Beautify promotes selected identity/content fields into locked constraints after confirmation and redraws SmartArt meaning with ordinary editable shapes.
- Template-fill uses the slide library as the native PPTX fill contract; SmartArt is inventory-only and remains unchanged.

## `pptx_to_svg.py`

Reconstruct a PPTX package as editable SVG views by reading OOXML directly.

```bash
python3 scripts/pptx_to_svg.py deck.pptx --inheritance-mode both
python3 scripts/pptx_to_svg.py deck.pptx --inheritance-mode layered
python3 scripts/pptx_to_svg.py deck.pptx --inheritance-mode flat
python3 scripts/pptx_to_svg.py deck.pptx --strict
```

| Mode | Output |
|---|---|
| `both` (default) | Layered master/layout/slide SVGs under `svg/`, plus self-contained slides under `svg-flat/` |
| `layered` | Only the layered `svg/` view and inheritance metadata |
| `flat` | One self-contained slide SVG per page under `svg/` |

For Office pictures that carry both a raster compatibility preview on
`a:blip` and an editable SVG relationship in `asvg:svgBlip`, import resolves
the SVG relationship first. The raster relationship is used only when the SVG
relationship or media part cannot be read. The template manifest uses the same
relationship preference for asset identity; its existing missing-media gate
remains strict rather than silently treating the raster preview as the
template's canonical asset.

Import is tolerant by default because the source deck is user-owned or comes
from third-party authoring tools. Recovery happens at the narrowest safe
boundary: first omit only an unsupported property or feature; if that is not
possible, replace only the affected object with a visible diagnostic
placeholder; omit a background without discarding its page. Corrupt ZIP/XML or
missing required package structure remains fatal because no safe local recovery
exists. Pass `--strict` for parser development or contract verification when
the first unsupported/malformed source construct should stop conversion.

Every successful run writes `<output>/conversion-report.json`. Its stable
top-level fields are `schemaVersion`, `source`, `mode`, `summary`, and
`diagnostics`. Each diagnostic records a reason `code`, source `message`, chosen
`fallback`, package `part_path`, and—when available—`slide_index`, `shape_id`,
`shape_name`, and `shape_kind`. The command also prints a bounded warning
summary instead of a raw Python traceback.

In the detailed native-object notes below, “fails closed” or “error” describes
the native replacement claim or strict mode. Default tolerant deck import
retains the usable fallback/object and records the degradation; it does not
discard unrelated shapes, pages, or the entire deck.

Supported text-grid tables and conservative classic-chart caches carry a
`data-pptx-replace-with` claim beside their SVG fallback, with the replacement
payload in a child `<metadata type="application/json">`. The parent claim
selects the table or chart schema. Table import requires
exact physical row/grid topology and accepts canonical rectangular merges,
safe solid/no-fill per-side borders, plain multi-paragraph cells, and a closed
run-rich paragraph schema.
Each run requires `text` and may use only `bold`, `italic`, `underline`,
`strike`, `color`, `font_size`, one `font_family`, `lang`, and `alt_lang`.
Presentation-only source run XML without a non-empty `effectLst` / `effectDag`
normalizes. A table-cell run effect disables native replacement and adds a
blocking effect diagnostic. Relationship-bearing text, extensions,
noncanonical/overlapping merges, nonblank merge slaves, unsafe border XML,
non-solid fills, structural line breaks/fields/tabs/bullets, and broken text
topology remain fallback-only.
Markers remain dormant
unless a later export uses `--native-charts-and-tables`. That opt-in is
data-object-first: the default fallback still exports as editable DrawingML
shapes, while the opt-in supplies a data source and PowerPoint's
chart/table-specific object model.
The native-object route may normalize styling or omit marker-local details not represented by the
payload, and export reports that risk without disabling an otherwise supported
active marker. Unsupported tables keep their
rendered SVG table; unsupported charts keep a baked preview when one exists.
For the currently supported parsed classic families (column/bar/line/area,
pie/doughnut, scatter, and bubble), a chart without a baked preview receives a
deterministic readable fallback marked
`data-pptx-fallback-kind="normalized"`. Unknown style XML disables the native
replacement claim or falls back to a diagnostic object in tolerant mode;
common solid/no-fill/line/marker forms and scheme colors are normalized for the
SVG fallback and core payload colors, while native opt-in may still normalize
unmodeled alpha, line, marker, or no-fill details. Common General, decimal,
grouped, percent, and simple currency-prefix data-label formats render
deterministically; an unknown Excel format program keeps the active payload but
does not claim a normalized fallback. Active types outside the current renderer
continue to use an explicit placeholder marked
`data-pptx-fallback-kind="placeholder"`. Validation and export report that
reconstruction-only fallback as a warning. Default export keeps the
placeholder; when the same group has a valid active chart replacement payload,
`--native-charts-and-tables` may still reconstruct the PowerPoint-native chart.
Invalid or contradictory fallback declarations remain errors. Fallback-only
replacement capability uses `data-pptx-replacement-status` and remains a
warning when the SVG fallback itself is complete. Imported table/chart groups
under this contract carry `data-pptx-import-source="pptx"`, whether active or
fallback-only; generated authoring omits this provenance attribute.

Active imported markers also carry `data-pptx-fallback-sha256`, computed over
their canonical fallback plus reachable document-level SVG fragment definitions.
A later visible edit, reachable definition change, local reference-target
change, or marker transform makes the replacement metadata stale. The mandatory
quality checker reports the mismatch; default export keeps the edited fallback,
while `--native-charts-and-tables` fails before replacement so it cannot discard that edit.
`visibility:hidden` content, marker-local unused definitions, and explicitly
referenced document-level target roots (even when hidden) are included
conservatively; marker-local `display:none` subtrees are excluded, and external
file bytes are not read.
Generated authoring and reusable templates omit import provenance and do not
preseed a static fallback hash; that state is normal and does not warn. A legacy
imported marker that still carries PPTX import provenance but lacks the hash
remains native-compatible and warns in the checker/native route that stale
detection is unavailable.

Legacy `data-pptx-native*`, `data-pptx-visual-status`, and
`data-pptx-route-status` spellings remain read-compatible. New importer output
and generated SVG use the replacement/fallback names above. The old
`--native-objects` option remains a compatibility alias for
`--native-charts-and-tables`.

For table style `{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}`, the importer resolves
the normalized `wholeTbl`, `firstRow`, `band1H`/`band2H`, theme color/font, and
direct-format override subset. Other built-in/custom style families remain
outside this guarantee.

The chart importer also accepts the verified column/line/area combo subset,
canonical four-series OHLC stock charts with shared numeric date caches, area
charts with numeric date axes, and verified scatter/bubble charts with a closed
pair of `axes.x` / `axes.y` value axes. Combo primary/secondary plots may retain
independent category caches and workbook ranges. Both the category/value and XY
contracts read back the supported kind/position/visibility, label-position,
number-format, min/max/major-unit, reverse, and major-gridline fields; the native
writer emits every field in those closed contracts. Scatter style is derived
from uniform effective series line/marker/smooth state. The normalized XY
fallback newly consumes only the two major-gridline flags, not the remaining
axis fields. The importer also accepts radar, safe `of_pie` `serLines`, the
closed axis/title/legend normalization cases, and bar/column `gapWidth` /
`overlap`. `gapWidth` must be one integer in `0..500` and `overlap` one integer
in `-100..100`; both normalize in native output, while malformed, duplicate, or
out-of-range values disable the native replacement claim in tolerant mode and
stop strict import. These additions do not expand the normalized
renderer.
Safe stock series style may pass the structural gate, while stock series,
`hiLowLines`, and up-down bar local styling can still normalize under the
data-object-first contract.
ChartEx import accepts exactly the validated treemap, sunburst, histogram,
pareto, box-whisker, waterfall, and funnel data models. Their supported
hierarchy/category/value/series/subtotal topology round-trips to native output.
Numeric caches must be non-empty and finite, with canonical non-negative counts
and indexes and exact contiguous point topology. Source style, axes, labels,
and binning details may normalize. This is not full `AxisSpec`, arbitrary
ChartEx import or presentation fidelity, arbitrary stock variants, other
date-axis chart families, or unlisted axis semantics. ChartEx native output
still consumes valid payload colors in its color-style part.

Exporter-canonical charts recover canonical solid series/slice colors and exact
one- or two-paragraph title styling; two paragraphs retain their `title` /
`subtitle` roles. This is not a general source-chart style round-trip guarantee.

Concrete slide SVGs resolve `<a:fld type="slidenum">` using the presentation's
`firstSlideNum` display numbering. Standalone master/layout SVGs keep the
literal field fallback because one shared part can serve multiple slides.

### Maintenance smoke checks

Run these checks from the repository root after changing `pptx_to_svg/` or its
CLI. They use a shipped deck and generated adversarial input; do not replace
them with a committed `test_*.py` suite.

#### Healthy generated deck

```bash
python3 "skills/ppt-master/scripts/pptx_to_svg.py" \
  "examples/ppt169_kubernetes_blueprint_2026/exports/kubernetes_blueprint_2026.pptx" \
  --inheritance-mode flat \
  -o "/tmp/ppt-master-smoke-kubernetes"
python3 -c "import json; from pathlib import Path; report = json.loads(Path('/tmp/ppt-master-smoke-kubernetes/conversion-report.json').read_text()); assert report['summary'] == {'slides': 10, 'warnings': 0}, report['summary']; print('OK: 10 slides, 0 warnings')"
```

Expected: both commands exit `0`; the assertion prints
`OK: 10 slides, 0 warnings`.

#### Tolerant/strict color-structure probe

Generate a two-shape PPTX, then add one foreign attribute to the first shape's
valid `a:srgbClr` node:

```bash
python3 -c '
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches

base = Path("/tmp/ppt-master-color-smoke-base.pptx")
target = Path("/tmp/ppt-master-color-smoke.pptx")
presentation = Presentation()
slide = presentation.slides.add_slide(presentation.slide_layouts[6])
for left, color in ((1, (0x44, 0x72, 0xC4)), (4, (0xED, 0x7D, 0x31))):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left),
        Inches(1),
        Inches(2),
        Inches(1),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(*color)
presentation.save(base)

with ZipFile(base) as source, ZipFile(target, "w", ZIP_DEFLATED) as destination:
    patched = False
    for member in source.infolist():
        payload = source.read(member)
        if member.filename == "ppt/slides/slide1.xml":
            old = b"<a:srgbClr val=\"4472C4\"/>"
            new = b"<a:srgbClr val=\"4472C4\" legacy=\"1\"/>"
            if old not in payload:
                raise RuntimeError("probe color node was not generated")
            payload = payload.replace(old, new, 1)
            patched = True
        destination.writestr(member, payload)
if not patched:
    raise RuntimeError("slide XML was not patched")
print(target)
'
```

Run tolerant import and verify both the recovery report and the visible SVG:

```bash
python3 "skills/ppt-master/scripts/pptx_to_svg.py" \
  "/tmp/ppt-master-color-smoke.pptx" \
  --inheritance-mode flat \
  -o "/tmp/ppt-master-smoke-color-tolerant"
python3 -c '
import json
from pathlib import Path

output = Path("/tmp/ppt-master-smoke-color-tolerant")
report = json.loads((output / "conversion-report.json").read_text())
diagnostics = report["diagnostics"]
svg = (output / "svg" / "slide_01.svg").read_text()
assert report["summary"] == {"slides": 1, "warnings": 1}, report["summary"]
assert len(diagnostics) == 1, diagnostics
assert diagnostics[0]["code"] == "color-structure-normalized", diagnostics[0]
assert diagnostics[0]["fallback"] == "retain recognized color attributes and modifiers", diagnostics[0]
assert diagnostics[0]["slide_index"] == 1, diagnostics[0]
assert diagnostics[0]["shape_name"] == "Rectangle 1", diagnostics[0]
assert "#4472C4" in svg and "#ED7D31" in svg
print("OK: tolerant import recovered #4472C4 and preserved #ED7D31")
'
```

Expected: both commands exit `0`; the importer reports one
`color-structure-normalized` warning and the assertion prints
`OK: tolerant import recovered #4472C4 and preserved #ED7D31`.

Run the same probe in strict mode:

```bash
python3 "skills/ppt-master/scripts/pptx_to_svg.py" \
  "/tmp/ppt-master-color-smoke.pptx" \
  --inheritance-mode flat \
  --strict \
  -o "/tmp/ppt-master-smoke-color-strict"
```

Expected: exit `1`, no traceback, and one error line:

```text
Error: PPTX-to-SVG conversion failed: Invalid DrawingML sRGB color structure
```

## `source_to_md/web_to_md.py`

Convert web pages to Markdown and download images locally.

```bash
python3 scripts/source_to_md/web_to_md.py https://example.com/article
python3 scripts/source_to_md/web_to_md.py https://url1.com https://url2.com
python3 scripts/source_to_md/web_to_md.py -f urls.txt
python3 scripts/source_to_md/web_to_md.py https://example.com -o output.md
python3 scripts/source_to_md/web_to_md.py https://example.com --emit-result /tmp/result.json
```

When `curl_cffi` is installed (included in `requirements.txt`), this script
automatically impersonates a modern Chrome TLS fingerprint, which lets it
fetch WeChat Official Accounts (`mp.weixin.qq.com`) and other sites that
block Python's default TLS fingerprint. No extra flags needed. If
`curl_cffi` is not available, it falls back to plain `requests`.

On success, the converter writes `<output>.conversion_profile.json` beside the
Markdown output.
`--emit-result` is for wrapper scripts that need the actual saved Markdown path
when the converter derives a title-based filename.


## `rotate_images.py`

Fix image EXIF orientation in downloaded or imported assets.

```bash
python3 scripts/rotate_images.py auto projects/xxx_files
python3 scripts/rotate_images.py gen projects/xxx_files
python3 scripts/rotate_images.py fix fixes.json
```

Use this when extracted photos appear sideways after conversion or import.
