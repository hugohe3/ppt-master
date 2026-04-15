# Conversion Tools

Source conversion tools turn PDFs, documents, slide decks, and web pages into Markdown before project creation.

## `source_to_md/pdf_to_md.py`

Recommended first choice for native PDFs.

```bash
python3 scripts/source_to_md/pdf_to_md.py book.pdf
python3 scripts/source_to_md/pdf_to_md.py book.pdf -o output.md
python3 scripts/source_to_md/pdf_to_md.py ./pdfs
python3 scripts/source_to_md/pdf_to_md.py ./pdfs -o ./markdown
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

## `source_to_md/ppt_to_md.py`

Structured PowerPoint-to-Markdown converter for Open XML slide decks.

Supported formats include:
- `.pptx`, `.pptm`
- `.ppsx`, `.ppsm`
- `.potx`, `.potm`

```bash
python3 scripts/source_to_md/ppt_to_md.py sales_deck.pptx
python3 scripts/source_to_md/ppt_to_md.py sales_deck.pptx -o output.md
python3 scripts/source_to_md/ppt_to_md.py ./decks
python3 scripts/source_to_md/ppt_to_md.py ./decks -o ./markdown
python3 scripts/source_to_md/ppt_to_md.py template.ppsx -o notes/template.md
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

## `source_to_md/web_to_md.py` / `source_to_md/web_to_md.cjs`

Convert web pages to Markdown and download images locally.

### Python version (preferred)

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

### Node.js version (fallback)

Retained as a backup for rare environments where `curl_cffi` can't be
installed (e.g., uncommon Python + OS + CPU combinations without prebuilt
wheels):

```bash
node scripts/source_to_md/web_to_md.cjs https://mp.weixin.qq.com/s/xxxx
```

For most users the Python version is sufficient — Node.js is no longer
required for WeChat coverage.

## `rotate_images.py`

Fix image EXIF orientation in downloaded or imported assets.

```bash
python3 scripts/rotate_images.py auto projects/xxx_files
python3 scripts/rotate_images.py gen projects/xxx_files
python3 scripts/rotate_images.py fix fixes.json
```

Use this when extracted photos appear sideways after conversion or import.
