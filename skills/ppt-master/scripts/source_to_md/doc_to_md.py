#!/usr/bin/env python3
"""
Document to Markdown Converter (hybrid Python + Pandoc fallback)

Primary formats (pure Python, no external tools required):
    .docx   → mammoth
    .html   → markdownify + BeautifulSoup
    .epub   → ebooklib + markdownify
    .ipynb  → nbconvert

Fallback formats (require pandoc installed):
    .doc .odt .rtf .tex .latex .rst .org .typ

All paths produce the same output convention:
    <input>.md                     Markdown file
    <input>_files/<asset>          Extracted media (relative references in MD)
"""

import argparse
import base64
import hashlib
import json
import mimetypes
import posixpath
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

# ─────────────────────────────────────────────────────────────
# Format registry
# ─────────────────────────────────────────────────────────────

# Formats handled by pure-Python paths
NATIVE_FORMATS = {".docx", ".html", ".htm", ".epub", ".ipynb"}

# Formats handled by pandoc fallback: suffix → (pandoc input format, description)
PANDOC_FORMATS = {
    ".doc":   ("doc",    "Microsoft Word 97-2003"),
    ".odt":   ("odt",    "OpenDocument Text"),
    ".rtf":   ("rtf",    "Rich Text Format"),
    ".tex":   ("latex",  "LaTeX"),
    ".latex": ("latex",  "LaTeX"),
    ".rst":   ("rst",    "reStructuredText"),
    ".org":   ("org",    "Emacs Org-mode"),
    ".typ":   ("typst",  "Typst"),
}

# Formats pandoc should extract embedded media from
PANDOC_MEDIA_FORMATS = {".odt"}
OFFICE_VECTOR_EXTENSIONS = {".emf", ".wmf"}

DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}
EMU_PER_INCH = 914400


# ─────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────

def _format_size(size: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _ensure_media_dir(out_file: Path) -> tuple[Path, str]:
    """Return (absolute media dir, relative dir name) and create the dir."""
    rel_media_dir = f"{out_file.stem}_files"
    media_dir = out_file.parent / rel_media_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir, rel_media_dir


_HTML_IMG_PATTERNS = (
    re.compile(
        r'<img\s[^>]*?src="(?P<src>[^"]+)"[^>]*?(?:alt="(?P<alt>[^"]*)")?[^>]*/?\s*>'
    ),
    re.compile(
        r'<img\s[^>]*?alt="(?P<alt>[^"]*)"[^>]*?src="(?P<src>[^"]+)"[^>]*/?\s*>'
    ),
)


def _html_img_to_md(markdown_content: str) -> str:
    """Convert any leftover <img> HTML tags to ![alt](src) syntax."""
    def _repl(match: re.Match[str]) -> str:
        src = match.group("src")
        alt = match.group("alt") or Path(src).stem
        return f"![{alt}]({src})"

    for pattern in _HTML_IMG_PATTERNS:
        markdown_content = pattern.sub(_repl, markdown_content)
    return markdown_content


def _report_result(out_file: Path, media_dir: Path | None) -> None:
    size = out_file.stat().st_size
    print(f"[OK] Saved Markdown to: {out_file} ({_format_size(size)})")
    if media_dir and media_dir.exists():
        files = [f for f in media_dir.rglob("*") if f.is_file()]
        if files:
            print(f"   Extracted {len(files)} media file(s) → {media_dir}")


def _normalize_ext(ext: str | None) -> str:
    """Return a normalized image extension, including the leading dot."""
    if not ext:
        return ".bin"
    ext = ext.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    if ext == ".jpe":
        return ".jpg"
    return ext


def _image_size(path: Path) -> tuple[int | None, int | None]:
    """Return bitmap dimensions when Pillow can read the file."""
    try:
        from PIL import Image
    except ImportError:
        return None, None
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except (OSError, ValueError):
        return None, None


def _is_office_vector(ext: str) -> bool:
    """Return whether an extension is an Office vector preview format."""
    return ext.lower() in OFFICE_VECTOR_EXTENSIONS


def _local_name(elem: ET.Element) -> str:
    """Return an XML element local name without its namespace."""
    return elem.tag.rsplit("}", 1)[-1]


def _relationship_target_path(target: str) -> str:
    """Normalize a Word relationship target to a DOCX zip path."""
    target = unquote(target)
    if target.startswith("/"):
        normalized = posixpath.normpath(target.lstrip("/"))
    else:
        normalized = posixpath.normpath(posixpath.join("word", target))
    return normalized


def _zip_sha256_for_target(media_hashes: dict[str, str], target: str) -> str | None:
    """Return the SHA-256 digest for an embedded DOCX part target."""
    if not target:
        return None
    return media_hashes.get(_relationship_target_path(target))


def _length_to_emu(value: str) -> int | None:
    """Parse a VML CSS length into EMU."""
    match = re.match(r"^\s*([\d.]+)\s*([a-zA-Z]*)\s*$", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "pt").lower()
    factors = {
        "in": EMU_PER_INCH,
        "cm": EMU_PER_INCH / 2.54,
        "mm": EMU_PER_INCH / 25.4,
        "pt": EMU_PER_INCH / 72,
        "px": EMU_PER_INCH / 96,
    }
    factor = factors.get(unit)
    if factor is None:
        return None
    return int(round(number * factor))


def _vml_display_size_emu(shape: ET.Element | None) -> tuple[int, int]:
    """Read VML shape width/height from its style attribute."""
    if shape is None:
        return 0, 0
    style = shape.attrib.get("style", "")
    values: dict[str, str] = {}
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        values[key.strip().lower()] = value.strip()
    width = _length_to_emu(values.get("width", "")) or 0
    height = _length_to_emu(values.get("height", "")) or 0
    return width, height


def _occurrence_entry(
    *,
    rel_id: str | None,
    target: str,
    width_emu: int,
    height_emu: int,
    source_sha256: str | None,
    source_kind: str,
) -> dict[str, object]:
    """Build one image metadata occurrence row."""
    display_ratio = (
        width_emu / height_emu
        if width_emu > 0 and height_emu > 0
        else None
    )
    return {
        "relationship_id": rel_id,
        "source_target": target,
        "source_path": _relationship_target_path(target) if target else "",
        "source_ext": _normalize_ext(Path(target).suffix),
        "source_sha256": source_sha256,
        "source_kind": source_kind,
        "display_width_emu": width_emu,
        "display_height_emu": height_emu,
        "display_width_in": round(width_emu / EMU_PER_INCH, 4) if width_emu else None,
        "display_height_in": round(height_emu / EMU_PER_INCH, 4) if height_emu else None,
        "display_ratio": round(display_ratio, 6) if display_ratio else None,
    }


def _docx_image_occurrences(input_file: Path) -> list[dict[str, object]]:
    """Read DOCX drawing order and Word display dimensions."""
    try:
        with zipfile.ZipFile(input_file) as docx:
            rels_root = ET.fromstring(docx.read("word/_rels/document.xml.rels"))
            doc_root = ET.fromstring(docx.read("word/document.xml"))
            media_hashes = {
                name: hashlib.sha256(docx.read(name)).hexdigest()
                for name in docx.namelist()
                if name.startswith("word/media/")
            }
    except (KeyError, ET.ParseError, zipfile.BadZipFile, OSError):
        return []

    rels: dict[str, str] = {}
    for rel in rels_root.findall("rel:Relationship", DOCX_NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            rels[rel_id] = target

    parent_map = {child: parent for parent in doc_root.iter() for child in parent}

    def _inside_mc_choice(elem: ET.Element) -> bool:
        parent = parent_map.get(elem)
        while parent is not None:
            if _local_name(parent) == "Choice":
                return True
            parent = parent_map.get(parent)
        return False

    occurrences: list[dict[str, object]] = []
    for elem in doc_root.iter():
        if _inside_mc_choice(elem):
            continue
        local = _local_name(elem)
        if local == "drawing":
            container = elem.find(".//wp:inline", DOCX_NS)
            if container is None:
                container = elem.find(".//wp:anchor", DOCX_NS)
            if container is None:
                continue
            extent = container.find("wp:extent", DOCX_NS)
            blip = container.find(".//a:blip", DOCX_NS)
            if extent is None or blip is None:
                continue

            rel_id = blip.attrib.get(f"{{{DOCX_NS['r']}}}embed")
            if not rel_id:
                rel_id = blip.attrib.get(f"{{{DOCX_NS['r']}}}link")
            target = rels.get(rel_id or "", "")
            if not target:
                continue

            try:
                width_emu = int(extent.attrib.get("cx", "0"))
                height_emu = int(extent.attrib.get("cy", "0"))
            except ValueError:
                width_emu = 0
                height_emu = 0

            occurrences.append(_occurrence_entry(
                rel_id=rel_id,
                target=target,
                width_emu=width_emu,
                height_emu=height_emu,
                source_sha256=_zip_sha256_for_target(media_hashes, target),
                source_kind="drawing",
            ))
        elif local == "imagedata":
            rel_id = elem.attrib.get(f"{{{DOCX_NS['r']}}}id")
            if not rel_id:
                rel_id = elem.attrib.get(f"{{{DOCX_NS['r']}}}pict")
            target = rels.get(rel_id or "", "")
            if not target:
                continue
            width_emu, height_emu = _vml_display_size_emu(parent_map.get(elem))
            occurrences.append(_occurrence_entry(
                rel_id=rel_id,
                target=target,
                width_emu=width_emu,
                height_emu=height_emu,
                source_sha256=_zip_sha256_for_target(media_hashes, target),
                source_kind="vml",
            ))
    return occurrences


def _match_occurrence(
    occurrences: list[dict[str, object]],
    used_indexes: set[int],
    index: int,
    image_bytes: bytes,
) -> dict[str, object] | None:
    """Match a Mammoth image callback to DOCX metadata."""
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    for occurrence_index, occurrence in enumerate(occurrences):
        if occurrence_index in used_indexes:
            continue
        if occurrence.get("source_sha256") == image_hash:
            used_indexes.add(occurrence_index)
            return occurrence

    fallback_index = index - 1
    if fallback_index < len(occurrences) and fallback_index not in used_indexes:
        used_indexes.add(fallback_index)
        return occurrences[fallback_index]
    return None


def _manifest_entry(
    index: int,
    filename: str,
    meta: dict[str, object] | None,
    file_path: Path,
    *,
    original_filename: str | None = None,
    asset_kind: str = "bitmap",
    svg_renderable: bool = True,
    pptx_native_supported: bool = True,
) -> dict[str, object]:
    width, height = _image_size(file_path)
    pixel_ratio = width / height if width and height else None
    entry: dict[str, object] = {
        "index": index,
        "filename": filename,
        "original_filename": original_filename or filename,
        "asset_kind": asset_kind,
        "svg_renderable": svg_renderable,
        "pptx_native_supported": pptx_native_supported,
        "pixel_width": width,
        "pixel_height": height,
        "pixel_ratio": round(pixel_ratio, 6) if pixel_ratio else None,
    }
    if meta:
        entry.update(meta)
    if entry.get("display_ratio") is None and pixel_ratio:
        entry["display_ratio"] = round(pixel_ratio, 6)
    return entry


# ─────────────────────────────────────────────────────────────
# DOCX → Markdown (mammoth)
# ─────────────────────────────────────────────────────────────

def _convert_docx(input_file: Path, out_file: Path) -> str:
    try:
        import mammoth
    except ImportError:
        print("[ERROR] mammoth not installed. Run: pip install mammoth")
        return ""

    media_dir, rel_media_dir = _ensure_media_dir(out_file)
    counter = {"n": 0}
    occurrences = _docx_image_occurrences(input_file)
    used_occurrence_indexes: set[int] = set()
    manifest: list[dict[str, object]] = []

    def _save_image(image):
        counter["n"] += 1
        index = counter["n"]
        with image.open() as stream:
            image_bytes = stream.read()

        meta = _match_occurrence(
            occurrences,
            used_occurrence_indexes,
            index,
            image_bytes,
        )
        source_ext = meta.get("source_ext") if meta else None
        ext = _normalize_ext(source_ext if isinstance(source_ext, str) else None)
        if ext == ".bin":
            ext = _normalize_ext(mimetypes.guess_extension(image.content_type))

        original_filename = f"image_{index:03d}{ext}"
        original_path = media_dir / original_filename
        original_path.write_bytes(image_bytes)

        filename = original_filename
        output_path = original_path
        asset_kind = "office_vector" if _is_office_vector(ext) else "bitmap"
        svg_renderable = asset_kind != "office_vector"
        pptx_native_supported = True

        manifest.append(_manifest_entry(
            index,
            filename,
            meta,
            output_path,
            original_filename=original_filename,
            asset_kind=asset_kind,
            svg_renderable=svg_renderable,
            pptx_native_supported=pptx_native_supported,
        ))
        return {"src": f"{rel_media_dir}/{filename}"}

    with input_file.open("rb") as f:
        result = mammoth.convert_to_markdown(
            f,
            convert_image=mammoth.images.img_element(_save_image),
        )

    markdown = _html_img_to_md(result.value)
    out_file.write_text(markdown, encoding="utf-8")

    if manifest:
        (media_dir / "image_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if not any(media_dir.iterdir()):
        media_dir.rmdir()
        media_dir = None  # type: ignore[assignment]

    for msg in result.messages:
        if msg.type == "warning":
            print(f"   [warn] {msg.message}")

    _report_result(out_file, media_dir)
    return markdown


# ─────────────────────────────────────────────────────────────
# HTML → Markdown (markdownify + BeautifulSoup)
# ─────────────────────────────────────────────────────────────

def _save_data_uri(data_uri: str, media_dir: Path, index: int) -> str | None:
    """Decode data:image/...;base64,... into a file; return filename or None."""
    match = re.match(r"data:(?P<mime>[^;]+);base64,(?P<data>.+)", data_uri)
    if not match:
        return None
    mime = match.group("mime")
    ext = mimetypes.guess_extension(mime) or ".bin"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"image_{index:03d}{ext}"
    try:
        (media_dir / filename).write_bytes(base64.b64decode(match.group("data")))
    except Exception:
        return None
    return filename


def _copy_local_image(src: str, base_dir: Path, media_dir: Path, index: int) -> str | None:
    """Copy a local image (relative or file://) into media_dir."""
    parsed = urlparse(src)
    if parsed.scheme in ("http", "https"):
        return None
    path_str = unquote(parsed.path if parsed.scheme == "file" else src)
    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    if not candidate.is_file():
        return None
    ext = candidate.suffix or ".bin"
    filename = f"image_{index:03d}{ext}"
    shutil.copy2(candidate, media_dir / filename)
    return filename


def _download_remote_image(url: str, media_dir: Path, index: int) -> str | None:
    """Best-effort download of a remote image. Silent on failure."""
    try:
        import requests
    except ImportError:
        return None
    try:
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
    except Exception:
        return None
    content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
    ext = mimetypes.guess_extension(content_type) if content_type else None
    if not ext:
        ext = Path(urlparse(url).path).suffix or ".bin"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"image_{index:03d}{ext}"
    (media_dir / filename).write_bytes(resp.content)
    return filename


def _process_html_images(html: str, base_dir: Path, media_dir: Path, rel_media_dir: str) -> str:
    """Extract & rewrite all <img> srcs in an HTML string."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[ERROR] beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return html

    soup = BeautifulSoup(html, "html.parser")
    index = 0
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        index += 1
        if src.startswith("data:"):
            filename = _save_data_uri(src, media_dir, index)
        elif urlparse(src).scheme in ("http", "https"):
            filename = _download_remote_image(src, media_dir, index)
        else:
            filename = _copy_local_image(src, base_dir, media_dir, index)
        if filename:
            img["src"] = f"{rel_media_dir}/{filename}"
    return str(soup)


def _convert_html(input_file: Path, out_file: Path) -> str:
    try:
        from markdownify import markdownify
    except ImportError:
        print("[ERROR] markdownify not installed. Run: pip install markdownify")
        return ""

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[ERROR] beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return ""

    media_dir, rel_media_dir = _ensure_media_dir(out_file)
    raw_html = input_file.read_text(encoding="utf-8", errors="replace")

    # Strip non-content elements (head/style/script) so metadata doesn't leak into MD
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["head", "style", "script", "noscript"]):
        tag.decompose()
    html = str(soup)
    html = _process_html_images(html, input_file.parent, media_dir, rel_media_dir)

    markdown = markdownify(html, heading_style="ATX", bullets="-")
    # Collapse 3+ blank lines to 2 for tidier output
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    out_file.write_text(markdown, encoding="utf-8")

    if not any(media_dir.iterdir()):
        media_dir.rmdir()
        media_dir = None  # type: ignore[assignment]

    _report_result(out_file, media_dir)
    return markdown


# ─────────────────────────────────────────────────────────────
# EPUB → Markdown (ebooklib + markdownify)
# ─────────────────────────────────────────────────────────────

def _convert_epub(input_file: Path, out_file: Path) -> str:
    try:
        import ebooklib
        from ebooklib import epub
        from markdownify import markdownify
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e.name}. "
              f"Run: pip install ebooklib markdownify beautifulsoup4")
        return ""

    media_dir, rel_media_dir = _ensure_media_dir(out_file)
    book = epub.read_epub(str(input_file))

    # Extract images, remembering original path → new filename mapping
    img_map: dict[str, str] = {}
    index = 0
    for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
        index += 1
        ext = Path(item.file_name).suffix or ".bin"
        filename = f"image_{index:03d}{ext}"
        (media_dir / filename).write_bytes(item.get_content())
        # Map both full and basename for robust lookup
        img_map[item.file_name] = filename
        img_map[Path(item.file_name).name] = filename

    # Iterate document items in spine order
    html_parts: list[str] = []
    spine_ids = [sid for sid, _ in book.spine]
    id_to_item = {it.get_id(): it for it in book.get_items_of_type(ebooklib.ITEM_DOCUMENT)}
    for sid in spine_ids:
        item = id_to_item.get(sid)
        if item is None:
            continue
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not src:
                continue
            # Try exact match, then basename, then normalized path
            candidates = [src, Path(src).name, unquote(src), Path(unquote(src)).name]
            resolved = next((img_map[c] for c in candidates if c in img_map), None)
            if resolved:
                img["src"] = f"{rel_media_dir}/{resolved}"
        body = soup.find("body") or soup
        html_parts.append(str(body))

    combined_html = "\n\n".join(html_parts)
    markdown = markdownify(combined_html, heading_style="ATX", bullets="-")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    out_file.write_text(markdown, encoding="utf-8")

    if not any(media_dir.iterdir()):
        media_dir.rmdir()
        media_dir = None  # type: ignore[assignment]

    _report_result(out_file, media_dir)
    return markdown


# ─────────────────────────────────────────────────────────────
# IPYNB → Markdown (nbconvert)
# ─────────────────────────────────────────────────────────────

def _convert_ipynb(input_file: Path, out_file: Path) -> str:
    try:
        import nbformat
        from nbconvert import MarkdownExporter
        from nbconvert.writers import FilesWriter
    except ImportError:
        print("[ERROR] nbconvert not installed. Run: pip install nbconvert")
        return ""

    # Pre-process cell-level markdown attachments: nbconvert leaves
    # `attachment:<name>` references intact but doesn't write the files.
    # Extract them into our outputs dict so FilesWriter picks them up.
    nb = nbformat.read(str(input_file), as_version=4)
    extra_outputs: dict[str, bytes] = {}
    rel_media_dir = f"{out_file.stem}_files"

    attach_counter = 0
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        attachments = getattr(cell, "attachments", None) or {}
        if not attachments:
            continue
        for att_name, mime_data in attachments.items():
            for mime, b64 in mime_data.items():
                attach_counter += 1
                ext = mimetypes.guess_extension(mime) or ".bin"
                if ext == ".jpe":
                    ext = ".jpg"
                filename = f"attachment_{attach_counter:03d}{ext}"
                out_path = f"{rel_media_dir}/{filename}"
                try:
                    extra_outputs[out_path] = base64.b64decode(b64)
                except Exception:
                    continue
                # Rewrite source references: attachment:<name> → <rel_path>
                src = cell.source if isinstance(cell.source, str) else "".join(cell.source)
                src = src.replace(f"attachment:{att_name}", out_path)
                cell.source = src

    exporter = MarkdownExporter()
    body, resources = exporter.from_notebook_node(nb)

    # Merge attachment outputs with whatever nbconvert collected
    resources.setdefault("outputs", {}).update(extra_outputs)
    resources["output_extension"] = ".md"

    writer = FilesWriter(build_directory=str(out_file.parent))
    writer.write(body, resources, notebook_name=out_file.stem)

    markdown = out_file.read_text(encoding="utf-8") if out_file.exists() else body
    media_dir = out_file.parent / rel_media_dir
    _report_result(out_file, media_dir if media_dir.exists() else None)
    return markdown


# ─────────────────────────────────────────────────────────────
# Pandoc fallback
# ─────────────────────────────────────────────────────────────

def _check_pandoc() -> bool:
    return shutil.which("pandoc") is not None


def _convert_with_pandoc(input_file: Path, out_file: Path, suffix: str) -> str:
    if not _check_pandoc():
        print(f"[ERROR] Format '{suffix}' requires pandoc. Install it:")
        print("   macOS:   brew install pandoc")
        print("   Ubuntu:  sudo apt install pandoc")
        print("   Windows: https://pandoc.org/installing.html")
        return ""

    input_format, _ = PANDOC_FORMATS[suffix]
    rel_media_dir = f"{out_file.stem}_files"
    media_dir = out_file.parent / rel_media_dir

    cmd = [
        "pandoc",
        "-f", input_format,
        "-t", "gfm",
        str(input_file.resolve()),
        "-o", str(out_file.resolve()),
        "--wrap", "none",
        "--strip-comments",
    ]
    if suffix in PANDOC_MEDIA_FORMATS:
        cmd.extend(["--extract-media", rel_media_dir])

    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=str(out_file.parent))
    if result.returncode != 0:
        print(f"[ERROR] Pandoc conversion failed:\n{result.stderr}")
        return ""
    if not out_file.exists():
        print("[ERROR] Conversion completed but no output file was generated")
        return ""

    markdown = out_file.read_text(encoding="utf-8")

    # Flatten nested media/ subdir that pandoc creates
    nested_media = media_dir / "media"
    if nested_media.exists():
        for f in nested_media.iterdir():
            if f.is_file():
                shutil.move(str(f), str(media_dir / f.name))
        try:
            nested_media.rmdir()
        except OSError:
            pass
        markdown = markdown.replace(f"{rel_media_dir}/media/", f"{rel_media_dir}/")

    # Normalize absolute paths to relative
    for abs_str in (str(media_dir.resolve()).replace("\\", "/"),
                    str(media_dir.resolve())):
        if abs_str in markdown:
            markdown = markdown.replace(abs_str, rel_media_dir)

    markdown = _html_img_to_md(markdown)
    out_file.write_text(markdown, encoding="utf-8")

    _report_result(out_file, media_dir if media_dir.exists() else None)
    return markdown


# ─────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────

_FORMAT_DESC = {
    ".docx":  "Microsoft Word (mammoth)",
    ".html":  "HTML (markdownify)",
    ".htm":   "HTML (markdownify)",
    ".epub":  "EPUB (ebooklib)",
    ".ipynb": "Jupyter Notebook (nbconvert)",
}


def convert_to_markdown(input_path: str, output_path: str | None = None) -> str:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_path}")
        return ""

    suffix = input_file.suffix.lower()
    if suffix not in NATIVE_FORMATS and suffix not in PANDOC_FORMATS:
        supported = ", ".join(sorted(NATIVE_FORMATS | PANDOC_FORMATS.keys()))
        print(f"[ERROR] Unsupported format: {suffix}")
        print(f"   Supported: {supported}")
        return ""

    out_file = Path(output_path) if output_path else input_file.with_suffix(".md")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if suffix in NATIVE_FORMATS:
        desc = _FORMAT_DESC[suffix]
        print(f"[INFO] Converting {desc}: {input_file.name}")
        if suffix == ".docx":
            return _convert_docx(input_file, out_file)
        if suffix in (".html", ".htm"):
            return _convert_html(input_file, out_file)
        if suffix == ".epub":
            return _convert_epub(input_file, out_file)
        if suffix == ".ipynb":
            return _convert_ipynb(input_file, out_file)

    _, format_desc = PANDOC_FORMATS[suffix]
    print(f"[INFO] Converting {format_desc} via pandoc: {input_file.name}")
    return _convert_with_pandoc(input_file, out_file, suffix)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert documents to Markdown "
                    "(pure-Python for common formats, pandoc fallback for the rest)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python doc_to_md.py lecture.docx                # Word → Markdown (mammoth)
  python doc_to_md.py article.html                # HTML → Markdown (markdownify)
  python doc_to_md.py book.epub                   # EPUB → Markdown (ebooklib)
  python doc_to_md.py notebook.ipynb              # Jupyter → Markdown (nbconvert)
  python doc_to_md.py manuscript.tex              # LaTeX → Markdown (pandoc fallback)

Native formats (no pandoc required):
  .docx  .html/.htm  .epub  .ipynb

Pandoc fallback formats (require system pandoc):
  .doc  .odt  .rtf  .tex/.latex  .rst  .org  .typ
        """,
    )
    parser.add_argument("input", help="Input document file")
    parser.add_argument("-o", "--output", help="Output Markdown file path")
    args = parser.parse_args()

    result = convert_to_markdown(args.input, args.output)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
