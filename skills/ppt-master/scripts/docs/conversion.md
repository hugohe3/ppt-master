# Conversion Tools

Source conversion tools turn PDFs, documents, and web pages into Markdown before project creation.

## `pdf_to_md.py`

Recommended first choice for native PDFs.

```bash
python3 scripts/pdf_to_md.py book.pdf
python3 scripts/pdf_to_md.py book.pdf -o output.md
python3 scripts/pdf_to_md.py ./pdfs
python3 scripts/pdf_to_md.py ./pdfs -o ./markdown
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

## `doc_to_md.py`

Pandoc-based converter for office and markup formats.

Supported formats include:
- `.docx`, `.doc`, `.odt`, `.rtf`
- `.epub`, `.html`, `.tex`, `.rst`, `.org`, `.ipynb`, `.typ`

```bash
python3 scripts/doc_to_md.py lecture.docx
python3 scripts/doc_to_md.py lecture.docx -o output.md
python3 scripts/doc_to_md.py notes.epub
python3 scripts/doc_to_md.py paper.tex -o paper.md
```

Dependency:

```bash
# macOS
brew install pandoc

# Ubuntu
sudo apt install pandoc
```

## `web_to_md.py` / `web_to_md.cjs`

Convert web pages to Markdown and download images locally.

Python version:

```bash
python3 scripts/web_to_md.py https://example.com/article
python3 scripts/web_to_md.py https://url1.com https://url2.com
python3 scripts/web_to_md.py -f urls.txt
python3 scripts/web_to_md.py https://example.com -o output.md
```

Node.js version for WeChat or anti-bot pages:

```bash
node scripts/web_to_md.cjs https://mp.weixin.qq.com/s/xxxx
node scripts/web_to_md.cjs https://url1.com https://url2.com
```

Use the Node.js version first for WeChat Official Accounts and similar high-security sites.

## `rotate_images.py`

Fix image EXIF orientation in downloaded or imported assets.

```bash
python3 scripts/rotate_images.py auto projects/xxx_files
python3 scripts/rotate_images.py gen projects/xxx_files
python3 scripts/rotate_images.py fix fixes.json
```

Use this when extracted photos appear sideways after conversion or import.
