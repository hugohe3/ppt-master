# Conversion Tools

> Architecture rationale (why native-Python first with pandoc fallback, why curl_cffi for TLS impersonation): see [docs/technical-design.md "Source Content Conversion"](../../../../docs/technical-design.md#source-content-conversion).

Source conversion tools turn PDFs, documents, slide decks, and web pages into Markdown before project creation.

## `source_to_md/pdf_to_md.py`

Recommended first choice for native PDFs.

```bash
uv run scripts/source_to_md/pdf_to_md.py book.pdf
uv run scripts/source_to_md/pdf_to_md.py book.pdf -o output.md
uv run scripts/source_to_md/pdf_to_md.py ./pdfs
uv run scripts/source_to_md/pdf_to_md.py ./pdfs -o ./markdown

# Image extraction control (default: filtered)
uv run scripts/source_to_md/pdf_to_md.py book.pdf --images filtered  # size/quality filters applied
uv run scripts/source_to_md/pdf_to_md.py book.pdf --images all       # extract all images, no filtering
uv run scripts/source_to_md/pdf_to_md.py book.pdf --images none      # skip all images (text only)
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
- `.docx` — via `mammoth`
- `.html` / `.htm` — via `markdownify` + `beautifulsoup4`
- `.epub` — via `ebooklib` + `markdownify`
- `.ipynb` — via `nbconvert`

Pandoc fallback (only if you need these):
- `.doc`, `.odt`, `.rtf`, `.tex`/`.latex`, `.rst`, `.org`, `.typ`

```bash
uv run scripts/source_to_md/doc_to_md.py lecture.docx
uv run scripts/source_to_md/doc_to_md.py lecture.docx -o output.md
uv run scripts/source_to_md/doc_to_md.py notes.epub
uv run scripts/source_to_md/doc_to_md.py paper.tex -o paper.md  # uses pandoc
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

## `source_to_md/excel_to_md.py`

Excel workbook converter for presentation source intake.

Supported formats:
- `.xlsx`
- `.xlsm`

Unsupported by default:
- `.xls` — resave as `.xlsx` first

```bash
uv run scripts/source_to_md/excel_to_md.py report.xlsx
uv run scripts/source_to_md/excel_to_md.py report.xlsx -o output.md
uv run scripts/source_to_md/excel_to_md.py report.xlsm --max-rows 200 --max-cols 40
```

Behavior:
- preserves workbook and sheet structure in Markdown
- exports visible sheets only
- trims empty outer rows and columns
- propagates merged-cell labels for readable Markdown tables
- exports formula cells as cached values; it does not recalculate formulas

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
uv run scripts/source_to_md/ppt_to_md.py sales_deck.pptx
uv run scripts/source_to_md/ppt_to_md.py sales_deck.pptx -o output.md
uv run scripts/source_to_md/ppt_to_md.py ./decks
uv run scripts/source_to_md/ppt_to_md.py ./decks -o ./markdown
uv run scripts/source_to_md/ppt_to_md.py template.ppsx -o notes/template.md
```

Behavior:
- extracts slide text in reading order
- converts PowerPoint tables to Markdown tables
- exports embedded pictures to a sibling `_files/` directory
- appends speaker notes when present

Dependency:

```bash
pip install python-pptx
```

Legacy `.ppt` is not parsed directly. Resave it as `.pptx` or export it to PDF first.

## `source_to_md/web_to_md.py`

Convert web pages to Markdown and download images locally.

```bash
uv run scripts/source_to_md/web_to_md.py https://example.com/article
uv run scripts/source_to_md/web_to_md.py https://url1.com https://url2.com
uv run scripts/source_to_md/web_to_md.py -f urls.txt
uv run scripts/source_to_md/web_to_md.py https://example.com -o output.md
```

When `curl_cffi` is installed (included in `requirements.txt`), this script
automatically impersonates a modern Chrome TLS fingerprint, which lets it
fetch WeChat Official Accounts (`mp.weixin.qq.com`) and other sites that
block Python's default TLS fingerprint. No extra flags needed. If
`curl_cffi` is not available, it falls back to plain `requests`.


## `rotate_images.py`

Fix image EXIF orientation in downloaded or imported assets.

```bash
uv run scripts/rotate_images.py auto projects/xxx_files
uv run scripts/rotate_images.py gen projects/xxx_files
uv run scripts/rotate_images.py fix fixes.json
```

Use this when extracted photos appear sideways after conversion or import.
