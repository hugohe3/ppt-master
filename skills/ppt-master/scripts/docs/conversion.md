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
| Markdown | `<stem>.md` unless `-o` selects another path |
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
python3 scripts/source_to_md.py ./pdfs/*.pdf
python3 scripts/source_to_md.py ./decks/*.pptx
python3 scripts/source_to_md.py report.docx -o report.md
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
- `-o/--output` is valid only with one input. Multiple explicit inputs write
  one Markdown/profile pair per source.

For multi-source project intake, use `project_manager.py import-sources` with
all source paths / URLs. `source_to_md.py` intentionally rejects directory
batching; pass explicit files/URLs or use project intake.

Backend converters are single-file tools. For ad hoc multi-file conversion,
pass explicit files or shell-expanded globs to `source_to_md.py`; for project
intake, use `project_manager.py import-sources`.

## `source_to_md/pdf_to_md.py`

Recommended first choice for native PDFs.

```bash
python3 scripts/source_to_md/pdf_to_md.py book.pdf
python3 scripts/source_to_md/pdf_to_md.py book.pdf -o output.md

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
python3 scripts/source_to_md/ppt_to_md.py template.ppsx -o notes/template.md
```

Behavior:
- extracts slide text in reading order
- converts PowerPoint tables to Markdown tables
- transcribes native chart data (type + categories × series values) into a Markdown table, so chart numbers are not lost in conversion
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
- `<stem>.slide_library.json` — text slots, geometry, native tables, native chart display caches
- `source_profile.json` — the single multi-deck index: a compact Strategist-facing digest per deck (over identity, tables, charts, and page types) under `decks[]`, with prefixed artifact pointers

`project_manager.py import-sources` runs this automatically for PPTX/PPTM/PPSX/PPSM/POTX/POTM inputs and stores the bundle directly under `analysis/`. Multi-deck per project: importing several PPTX files gives each its own `<stem>.*` artifacts and a `decks[]` entry in the shared `source_profile.json` index (re-importing the same stem replaces its entry). The beautify / template-fill workflows stay single-deck and read one chosen deck's `<stem>.*` artifacts.

Usage boundary:
- Standard generation uses these fields as facts and recommendation candidates; it does not inherit source slide coordinates or page order by default.
- Beautify promotes selected identity/content fields into locked constraints after confirmation.
- Template-fill uses the slide library as the native PPTX fill contract.

## `source_to_md/web_to_md.py`

Convert web pages to Markdown and download images locally.

```bash
python3 scripts/source_to_md/web_to_md.py https://example.com/article
python3 scripts/source_to_md/web_to_md.py https://url1.com https://url2.com
python3 scripts/source_to_md/web_to_md.py -f urls.txt
python3 scripts/source_to_md/web_to_md.py https://example.com -o output.md
```

When `curl_cffi` is installed (included in `requirements.txt`), this script
automatically impersonates a modern Chrome TLS fingerprint, which lets it
fetch WeChat Official Accounts (`mp.weixin.qq.com`) and other sites that
block Python's default TLS fingerprint. No extra flags needed. If
`curl_cffi` is not available, it falls back to plain `requests`.

On success, the converter writes `<output>.conversion_profile.json` beside the
Markdown output.


## `rotate_images.py`

Fix image EXIF orientation in downloaded or imported assets.

```bash
python3 scripts/rotate_images.py auto projects/xxx_files
python3 scripts/rotate_images.py gen projects/xxx_files
python3 scripts/rotate_images.py fix fixes.json
```

Use this when extracted photos appear sideways after conversion or import.
