#!/usr/bin/env python3
"""
Document to Markdown Converter (hybrid Python + Pandoc fallback)

Primary formats (pure Python, no external tools required):
    .docx   → mammoth (tables preserved; OMML equations rewritten to inline LaTeX)
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
import tempfile
import uuid
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from _batch import run_path_batch  # noqa: E402
from _conversion_profile import write_conversion_profile_best_effort  # noqa: E402

configure_utf8_stdio()

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
IMAGE_ASSET_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif",
    ".emf", ".wmf", ".svg",
}

DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "v": "urn:schemas-microsoft-com:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
EMU_PER_INCH = 914400
MATH_NS = DOCX_NS["m"]
W_NS = DOCX_NS["w"]
XML_SPACE_ATTR = "{http://www.w3.org/XML/1998/namespace}space"

# OMML n-ary operator chars (m:nary/m:naryPr/m:chr) → LaTeX command.
NARY_OPS = {
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod",
    "∫": r"\int", "∬": r"\iint", "∭": r"\iiint", "∮": r"\oint",
    "⋃": r"\bigcup", "⋂": r"\bigcap", "⋁": r"\bigvee", "⋀": r"\bigwedge",
}
# OMML accent chars (m:acc/m:accPr/m:chr) → LaTeX command.
ACCENT_CMDS = {
    "̂": r"\hat", "̃": r"\tilde", "̄": r"\bar", "→": r"\vec", "⃗": r"\vec",
    "̇": r"\dot", "̈": r"\ddot", "̌": r"\check", "́": r"\acute", "̀": r"\grave",
}


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


def _write_generic_image_manifest(
    media_dir: Path,
    rel_media_dir: str,
    markdown: str,
    source_kind: str,
) -> None:
    """Write lightweight image metadata for non-DOCX converter paths."""
    if not media_dir.exists():
        return

    ref_pattern = re.compile(rf"{re.escape(rel_media_dir)}/([^)\s]+)")
    refs = [Path(match.group(1)).name for match in ref_pattern.finditer(markdown)]
    occurrence_map: dict[str, list[dict[str, object]]] = {}
    for index, filename in enumerate(refs, 1):
        occurrence_map.setdefault(filename, []).append({
            "occurrence_index": index,
            "source_ref": f"{rel_media_dir}/{filename}",
        })

    manifest: list[dict[str, object]] = []
    for file_path in sorted(path for path in media_dir.iterdir() if path.is_file()):
        ext = _normalize_ext(file_path.suffix)
        if ext not in IMAGE_ASSET_SUFFIXES:
            continue
        width, height = _image_size(file_path)
        ratio = width / height if width and height else None
        asset_kind = "office_vector" if _is_office_vector(ext) else "bitmap"
        occurrences = occurrence_map.get(file_path.name, [])
        entry: dict[str, object] = {
            "index": len(manifest) + 1,
            "filename": file_path.name,
            "original_filename": file_path.name,
            "asset_kind": asset_kind,
            "svg_renderable": asset_kind != "office_vector",
            "pptx_native_supported": True,
            "source_kind": source_kind,
            "source_ext": ext,
            "pixel_width": width,
            "pixel_height": height,
            "pixel_ratio": round(ratio, 6) if ratio else None,
            "display_ratio": round(ratio, 6) if ratio else None,
            "occurrences": occurrences,
            "usage_count": len(occurrences) if occurrences else 1,
        }
        manifest.append(entry)

    if manifest:
        (media_dir / "image_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


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
# OMML (Office Math) → LaTeX
# ─────────────────────────────────────────────────────────────
#
# mammoth drops all math content, so Word-native equations and MathType
# formulas saved as Office Math (OMML) vanish from the output. This pure-Python
# converter rewrites each <m:oMath> into inline `$...$` LaTeX before mammoth
# runs, so formulas survive into the Markdown in document order.
#
# Scope: OMML only. Classic MathType OLE objects (Equation.DSMT4 / MTEF binary)
# carry no OMML — they expose only a WMF/EMF preview image, which mammoth still
# emits as a picture. Decoding MTEF is out of scope.

def _m_child(elem: ET.Element, name: str) -> ET.Element | None:
    """Return the first OMML child with the given local name."""
    for child in elem:
        if _local_name(child) == name:
            return child
    return None


def _m_pr_val(elem: ET.Element, prop: str) -> str | None:
    """Return m:val of a property inside the element's *Pr block (e.g. chr)."""
    for child in elem:
        if not _local_name(child).endswith("Pr"):
            continue
        for sub in child:
            if _local_name(sub) == prop:
                return sub.get(f"{{{MATH_NS}}}val")
    return None


def _brace(latex: str) -> str:
    """Wrap multi-char LaTeX in braces so it binds as one super/subscript arg."""
    return latex if len(latex) <= 1 else "{" + latex + "}"


def _omml_part(elem: ET.Element, name: str) -> str:
    """Convert a named OMML child (e/num/den/sup/sub/...) to LaTeX."""
    child = _m_child(elem, name)
    return _omml_to_latex(child) if child is not None else ""


def _omml_run(elem: ET.Element) -> str:
    """Concatenate text from an OMML run, skipping property children."""
    return "".join(
        c.text or "" for c in elem if _local_name(c) == "t"
    )


def _omml_children(elem: ET.Element) -> str:
    """Convert all non-property children in order (default/passthrough rule)."""
    return "".join(
        _omml_to_latex(c) for c in elem if not _local_name(c).endswith("Pr")
    )


def _omml_matrix(elem: ET.Element, *, environment: str) -> str:
    """Convert a matrix (m:m) or equation array (m:eqArr) to a LaTeX env."""
    rows: list[str] = []
    for row in elem:
        if _local_name(row) not in ("mr", "e"):
            continue
        if _local_name(row) == "e":  # eqArr stores rows as bare <m:e>
            rows.append(_omml_to_latex(row))
            continue
        cells = [_omml_to_latex(cell) for cell in row if _local_name(cell) == "e"]
        rows.append(" & ".join(cells))
    body = r" \\ ".join(rows)
    return rf"\begin{{{environment}}} {body} \end{{{environment}}}"


def _omml_to_latex(elem: ET.Element) -> str:
    """Recursively convert one OMML element subtree to a LaTeX string.

    Unknown elements degrade to a concatenation of their children rather than
    being dropped, so rare constructs lose markup but never lose content.
    """
    local = _local_name(elem)

    if local == "t":
        return elem.text or ""
    if local == "r":
        return _omml_run(elem)
    if local in ("oMath", "oMathPara", "e", "num", "den", "sup", "sub",
                 "deg", "fName", "lim", "box", "borderBox"):
        return _omml_children(elem)
    if local == "sSup":
        return _brace(_omml_part(elem, "e")) + "^" + _brace(_omml_part(elem, "sup"))
    if local == "sSub":
        return _brace(_omml_part(elem, "e")) + "_" + _brace(_omml_part(elem, "sub"))
    if local == "sSubSup":
        return (_brace(_omml_part(elem, "e"))
                + "_" + _brace(_omml_part(elem, "sub"))
                + "^" + _brace(_omml_part(elem, "sup")))
    if local == "sPre":
        return ("{}_" + _brace(_omml_part(elem, "sub"))
                + "^" + _brace(_omml_part(elem, "sup"))
                + _brace(_omml_part(elem, "e")))
    if local == "f":
        return r"\frac{" + _omml_part(elem, "num") + "}{" + _omml_part(elem, "den") + "}"
    if local == "rad":
        deg = _m_child(elem, "deg")
        body = _omml_part(elem, "e")
        deg_latex = _omml_to_latex(deg) if deg is not None and len(deg) else ""
        return rf"\sqrt[{deg_latex}]{{{body}}}" if deg_latex else rf"\sqrt{{{body}}}"
    if local == "d":
        beg = _m_pr_val(elem, "begChr")
        end = _m_pr_val(elem, "endChr")
        beg = "(" if beg is None else (beg or ".")
        end = ")" if end is None else (end or ".")
        inner = "".join(_omml_to_latex(c) for c in elem if _local_name(c) == "e")
        return rf"\left{beg}{inner}\right{end}"
    if local == "nary":
        chr_ = _m_pr_val(elem, "chr") or "∫"
        op = NARY_OPS.get(chr_, chr_)
        sub, sup = _m_child(elem, "sub"), _m_child(elem, "sup")
        out = op
        if sub is not None and len(sub):
            out += "_" + _brace(_omml_to_latex(sub))
        if sup is not None and len(sup):
            out += "^" + _brace(_omml_to_latex(sup))
        return out + _brace(_omml_part(elem, "e"))
    if local == "func":
        return "\\" + _omml_part(elem, "fName").strip() + _brace(_omml_part(elem, "e"))
    if local == "limLow":
        return _brace(_omml_part(elem, "e")) + "_" + _brace(_omml_part(elem, "lim"))
    if local == "limUpp":
        return _brace(_omml_part(elem, "e")) + "^" + _brace(_omml_part(elem, "lim"))
    if local == "bar":
        cmd = r"\underline" if _m_pr_val(elem, "pos") == "bot" else r"\overline"
        return cmd + "{" + _omml_part(elem, "e") + "}"
    if local == "acc":
        cmd = ACCENT_CMDS.get(_m_pr_val(elem, "chr") or "̂", r"\hat")
        return cmd + "{" + _omml_part(elem, "e") + "}"
    if local == "groupChr":
        return _omml_part(elem, "e")
    if local == "m":
        return _omml_matrix(elem, environment="matrix")
    if local == "eqArr":
        return _omml_matrix(elem, environment="aligned")

    return _omml_children(elem)


def _make_text_run(text: str) -> ET.Element:
    """Build a <w:r><w:t xml:space="preserve">text</w:t></w:r> element."""
    run = ET.Element(f"{{{W_NS}}}r")
    t = ET.SubElement(run, f"{{{W_NS}}}t")
    t.set(XML_SPACE_ATTR, "preserve")
    t.text = text
    return run


def _make_text_paragraph(text: str) -> ET.Element:
    """Build a simple Word paragraph containing text."""
    paragraph = ET.Element(f"{{{W_NS}}}p")
    paragraph.append(_make_text_run(text))
    return paragraph


def _docx_inject_math_latex(
    input_file: Path,
) -> tuple[Path, dict[str, str]] | None:
    """Replace OMML equations with alphanumeric placeholders in a temp DOCX.

    Returns ``(temp_file, {placeholder: latex})`` or None when the document has
    no OMML math. Placeholders are plain ``[A-Za-z0-9]`` tokens so mammoth never
    markdown-escapes the LaTeX; the caller swaps each token for its `$...$` value
    after mammoth has produced the Markdown.
    """
    try:
        with zipfile.ZipFile(input_file) as docx:
            document_xml = docx.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile, OSError):
        return None
    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError:
        return None

    parent_map = {child: parent for parent in root.iter() for child in parent}
    targets: list[tuple[ET.Element, bool]] = []
    for elem in root.iter():
        local = _local_name(elem)
        if local == "oMathPara":
            targets.append((elem, True))
        elif local == "oMath":
            parent = parent_map.get(elem)
            if parent is None or _local_name(parent) != "oMathPara":
                targets.append((elem, False))
    if not targets:
        return None

    token_base = uuid.uuid4().hex
    replacements: dict[str, str] = {}
    for index, (elem, display) in enumerate(targets):
        parent = parent_map.get(elem)
        if parent is None:
            continue
        latex = _omml_to_latex(elem).strip()
        position = list(parent).index(elem)
        parent.remove(elem)
        if latex:
            token = f"MATHEQ{token_base}{index:04d}"
            delim = "$$" if display else "$"
            replacements[token] = f"{delim}{latex}{delim}"
            parent.insert(position, _make_text_run(token))
    if not replacements:
        return None

    for prefix, uri in DOCX_NS.items():
        if prefix != "rel":
            ET.register_namespace(prefix, uri)
    patched_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.close()
    out_path = Path(tmp.name)
    with zipfile.ZipFile(input_file) as zin, \
            zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = patched_xml if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    return out_path, replacements


# ─────────────────────────────────────────────────────────────
# DOCX tables → pipe Markdown
# ─────────────────────────────────────────────────────────────

def _docx_paragraph_text(paragraph: ET.Element) -> str:
    """Extract readable text from one Word paragraph."""
    parts: list[str] = []
    for elem in paragraph.iter():
        local = _local_name(elem)
        if local == "t":
            parts.append(elem.text or "")
        elif local == "tab":
            parts.append("\t")
        elif local in {"br", "cr"}:
            parts.append(" ")
    return "".join(parts).strip()


def _docx_table_has_media(table: ET.Element) -> bool:
    """Return whether a table contains image-bearing nodes."""
    return any(_local_name(elem) in {"drawing", "imagedata"} for elem in table.iter())


def _docx_table_cell_text(cell: ET.Element) -> str:
    """Extract table-cell text, preserving paragraph breaks as Markdown breaks."""
    paragraphs: list[str] = []
    for child in cell:
        if _local_name(child) == "p":
            text = _docx_paragraph_text(child)
            if text:
                paragraphs.append(text)
    return "<br>".join(paragraphs)


def _markdown_table_cell(text: str) -> str:
    """Escape Markdown table delimiters in one cell."""
    text = re.sub(r"[ \t\r\n]+", " ", text).strip()
    return text.replace("|", r"\|")


def _docx_table_to_markdown(table: ET.Element) -> str:
    """Convert a Word table XML node to a pipe Markdown table."""
    rows: list[list[str]] = []
    for row in table.findall("w:tr", DOCX_NS):
        cells = [
            _markdown_table_cell(_docx_table_cell_text(cell))
            for cell in row.findall("w:tc", DOCX_NS)
        ]
        if cells:
            rows.append(cells)
    if not rows:
        return ""

    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    header, body = rows[0], rows[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def _docx_inject_tables_markdown(
    input_file: Path,
) -> tuple[Path, dict[str, str]] | None:
    """Replace text-only DOCX tables with Markdown placeholders in a temp DOCX."""
    try:
        with zipfile.ZipFile(input_file) as docx:
            document_xml = docx.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile, OSError):
        return None
    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError:
        return None

    parent_map = {child: parent for parent in root.iter() for child in parent}
    token_base = uuid.uuid4().hex
    replacements: dict[str, str] = {}
    for index, table in enumerate(root.findall(".//w:tbl", DOCX_NS)):
        if _docx_table_has_media(table):
            continue
        markdown = _docx_table_to_markdown(table)
        if not markdown:
            continue
        parent = parent_map.get(table)
        if parent is None:
            continue
        position = list(parent).index(table)
        token = f"MARKDOWNTABLE{token_base}{index:04d}"
        parent.remove(table)
        parent.insert(position, _make_text_paragraph(token))
        replacements[token] = markdown
    if not replacements:
        return None

    for prefix, uri in DOCX_NS.items():
        if prefix != "rel":
            ET.register_namespace(prefix, uri)
    patched_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    tmp.close()
    out_path = Path(tmp.name)
    with zipfile.ZipFile(input_file) as zin, \
            zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = patched_xml if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    return out_path, replacements


def _clean_mammoth_markdown(markdown: str) -> str:
    """Remove Mammoth escapes for punctuation that is safe as literal text."""
    def _repl(match: re.Match[str]) -> str:
        char = match.group(1)
        if char == ".":
            line_start = markdown.rfind("\n", 0, match.start()) + 1
            line_prefix = markdown[line_start:match.start()]
            if re.fullmatch(r"\s*\d+", line_prefix):
                return match.group(0)
        return char

    return re.sub(r"\\([.(),:])", _repl, markdown)


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

    # Rewrite OMML equations to LaTeX placeholders before mammoth (which would
    # otherwise drop them); the placeholders are swapped back below.
    math_injection = _docx_inject_math_latex(input_file)
    if math_injection is not None:
        math_file, math_replacements = math_injection
    else:
        math_file, math_replacements = None, {}
    table_file = None
    table_replacements: dict[str, str] = {}
    mammoth_source = math_file or input_file
    table_injection = _docx_inject_tables_markdown(mammoth_source)
    if table_injection is not None:
        table_file, table_replacements = table_injection
        mammoth_source = table_file
    try:
        with mammoth_source.open("rb") as f:
            result = mammoth.convert_to_markdown(
                f,
                convert_image=mammoth.images.img_element(_save_image),
            )
    finally:
        if table_file is not None:
            try:
                table_file.unlink()
            except OSError:
                pass
        if math_file is not None:
            try:
                math_file.unlink()
            except OSError:
                pass

    markdown = result.value
    for token, table_markdown in table_replacements.items():
        markdown = markdown.replace(token, table_markdown)
    for token, latex in math_replacements.items():
        markdown = markdown.replace(token, latex)
    markdown = _html_img_to_md(markdown)
    markdown = _clean_mammoth_markdown(markdown)
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
    _write_generic_image_manifest(media_dir, rel_media_dir, markdown, "html_image")

    if not any(media_dir.iterdir()):
        media_dir.rmdir()
        media_dir = None  # type: ignore[assignment]

    _report_result(out_file, media_dir)
    return markdown


# ─────────────────────────────────────────────────────────────
# EPUB → Markdown (ebooklib + markdownify)
# ─────────────────────────────────────────────────────────────

def _sanitize_epub_manifest(src: Path) -> tuple[Path, bool]:
    """Return an EPUB path that ebooklib can read.

    Some EPUBs contain OPF manifest entries pointing at files that are missing
    from the ZIP archive. ebooklib reads every manifest item eagerly, so one
    stale entry can abort the whole conversion. When broken entries are found,
    this writes a temporary EPUB with those manifest items and matching spine
    refs removed.
    """
    OPF_NS = "http://www.idpf.org/2007/opf"
    CONT_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

    try:
        with zipfile.ZipFile(src, "r") as zin:
            names = set(zin.namelist())
            if "META-INF/container.xml" not in names:
                return src, False

            container_root = ET.fromstring(zin.read("META-INF/container.xml"))
            rootfile_el = container_root.find(f".//{{{CONT_NS}}}rootfile")
            if rootfile_el is None:
                return src, False

            opf_path = rootfile_el.get("full-path")
            if not opf_path or opf_path not in names:
                return src, False

            opf_root = ET.fromstring(zin.read(opf_path))
            manifest_el = opf_root.find(f"{{{OPF_NS}}}manifest")
            if manifest_el is None:
                return src, False

            opf_dir = posixpath.dirname(opf_path)
            bad_ids: list[str] = []
            bad_hrefs: list[str] = []
            for item_el in list(manifest_el.findall(f"{{{OPF_NS}}}item")):
                href = item_el.get("href", "")
                if not href:
                    continue
                rel = unquote(href)
                zpath = posixpath.normpath(
                    posixpath.join(opf_dir, rel) if opf_dir else rel
                )
                if zpath in names:
                    continue

                item_id = item_el.get("id", "")
                if item_id:
                    bad_ids.append(item_id)
                bad_hrefs.append(href)
                manifest_el.remove(item_el)

            if not bad_hrefs:
                return src, False

            spine_el = opf_root.find(f"{{{OPF_NS}}}spine")
            if spine_el is not None and bad_ids:
                for itemref in list(spine_el.findall(f"{{{OPF_NS}}}itemref")):
                    if itemref.get("idref") in bad_ids:
                        spine_el.remove(itemref)

            ET.register_namespace("", OPF_NS)
            ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
            new_opf = ET.tostring(opf_root, encoding="utf-8", xml_declaration=True)

            tmp = tempfile.NamedTemporaryFile(suffix=".epub", delete=False)
            tmp.close()
            out_path = Path(tmp.name)

            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
                if "mimetype" in names:
                    zout.writestr(
                        zipfile.ZipInfo("mimetype"),
                        zin.read("mimetype"),
                        compress_type=zipfile.ZIP_STORED,
                    )
                for name in zin.namelist():
                    if name == "mimetype":
                        continue
                    if name == opf_path:
                        zout.writestr(name, new_opf)
                    else:
                        zout.writestr(name, zin.read(name))

            preview = ", ".join(bad_hrefs[:3])
            if len(bad_hrefs) > 3:
                preview += " ..."
            print(
                f"[INFO] EPUB manifest sanitized: removed "
                f"{len(bad_hrefs)} broken item(s) [{preview}]"
            )
            return out_path, True
    except (zipfile.BadZipFile, ET.ParseError, OSError) as exc:
        print(
            f"[WARN] EPUB sanitize skipped "
            f"({exc.__class__.__name__}: {exc}); using original file"
        )
        return src, False


def _epub_image_candidates(src: str, document_name: str) -> list[str]:
    """Build lookup candidates for an image reference inside an EPUB document."""
    parsed = urlparse(src)
    raw_path = parsed.path if parsed.scheme else src
    decoded_path = unquote(raw_path)
    normalized_path = posixpath.normpath(decoded_path).lstrip("/")
    document_dir = posixpath.dirname(document_name)
    relative_path = posixpath.normpath(
        posixpath.join(document_dir, decoded_path)
    ).lstrip("/")

    candidates = [
        src,
        raw_path,
        decoded_path,
        normalized_path,
        relative_path,
        Path(decoded_path).name,
        Path(normalized_path).name,
    ]
    return [candidate for candidate in dict.fromkeys(candidates) if candidate]


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
    sanitized_path, is_temp_copy = _sanitize_epub_manifest(input_file)
    try:
        book = epub.read_epub(str(sanitized_path))
    finally:
        if is_temp_copy:
            try:
                sanitized_path.unlink()
            except OSError:
                pass

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
            # Try exact match, basename, decoded path, and path relative to this XHTML file.
            candidates = _epub_image_candidates(src, item.file_name)
            resolved = next((img_map[c] for c in candidates if c in img_map), None)
            if resolved:
                img["src"] = f"{rel_media_dir}/{resolved}"
        body = soup.find("body") or soup
        html_parts.append(str(body))

    combined_html = "\n\n".join(html_parts)
    markdown = markdownify(combined_html, heading_style="ATX", bullets="-")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    out_file.write_text(markdown, encoding="utf-8")
    _write_generic_image_manifest(media_dir, rel_media_dir, markdown, "epub_image")

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
    _write_generic_image_manifest(media_dir, rel_media_dir, markdown, "ipynb_image")
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
    _write_generic_image_manifest(media_dir, rel_media_dir, markdown, "pandoc_image")

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
            markdown = _convert_docx(input_file, out_file)
        elif suffix in (".html", ".htm"):
            markdown = _convert_html(input_file, out_file)
        elif suffix == ".epub":
            markdown = _convert_epub(input_file, out_file)
        elif suffix == ".ipynb":
            markdown = _convert_ipynb(input_file, out_file)
        else:
            markdown = ""
        if markdown:
            profile_path = write_conversion_profile_best_effort(
                input_path=str(input_file),
                markdown_path=out_file,
                converter="doc_to_md.py",
                conversion_type=suffix.lstrip("."),
            )
            if profile_path:
                print(f"   Wrote conversion profile -> {profile_path}")
        return markdown

    _, format_desc = PANDOC_FORMATS[suffix]
    print(f"[INFO] Converting {format_desc} via pandoc: {input_file.name}")
    markdown = _convert_with_pandoc(input_file, out_file, suffix)
    if markdown:
        profile_path = write_conversion_profile_best_effort(
            input_path=str(input_file),
            markdown_path=out_file,
            converter="doc_to_md.py",
            conversion_type=suffix.lstrip("."),
        )
        if profile_path:
            print(f"   Wrote conversion profile -> {profile_path}")
    return markdown


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert documents to Markdown "
                    "(pure-Python for common formats, pandoc fallback for the rest)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python doc_to_md.py lecture.docx                # Word → Markdown (mammoth)
  python doc_to_md.py lecture.docx notes.html     # Convert multiple files
  python doc_to_md.py ./docs -o ./markdown        # Convert supported files in a directory
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
    parser.add_argument("inputs", nargs="+", help="Input document file(s) or directories")
    parser.add_argument(
        "-o",
        "--output",
        help="Output Markdown file for one input, or output directory for multiple inputs/directories",
    )
    args = parser.parse_args()

    supported_suffixes = set(NATIVE_FORMATS) | set(PANDOC_FORMATS)
    return run_path_batch(
        args.inputs,
        supported_suffixes,
        args.output,
        lambda source, output: bool(convert_to_markdown(str(source), str(output))),
    )


if __name__ == "__main__":
    raise SystemExit(main())
