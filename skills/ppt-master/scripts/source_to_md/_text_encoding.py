#!/usr/bin/env python3
"""Decode text sources consistently for conversion and project import.

Usage:
    Imported by source_to_md.py and project_management.cli.
Examples:
    text, encoding = decode_text_source(raw, source)
Dependencies:
    beautifulsoup4 for HTML declarations.
"""

import codecs
from email.message import Message
from pathlib import Path


_HTML_WINDOWS_1252_LABELS = {
    "ansi_x3.4-1968", "ascii", "cp1252", "cp819", "csisolatin1", "ibm819",
    "iso-8859-1", "iso-ir-100", "iso8859-1", "iso88591", "iso_8859-1",
    "iso_8859-1:1987", "l1", "latin1", "latin-1", "us-ascii", "windows-1252",
    "x-cp1252",
}
_CP1252_C1_MAP = {
    byte: bytes([byte]).decode("cp1252")
    for byte in range(0x80, 0xA0)
    if byte not in (0x81, 0x8D, 0x8F, 0x90, 0x9D)
}


def bom_encoding(raw: bytes) -> str:
    """Return the UTF codec selected by the byte order mark, if present."""
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        return "utf-32"
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "utf-16"
    return ""


def content_type_charset(content_type: str) -> str:
    """Read the charset parameter of a Content-Type header or meta declaration."""
    message = Message()
    message["Content-Type"] = content_type
    return (message.get_content_charset() or "").strip("'")


def declared_html_charset(raw: bytes) -> str:
    """Read a charset declared by a meta element near the start of the page."""
    head = raw[:8192]
    if b"<meta" not in head.lower():
        return ""
    from bs4 import BeautifulSoup, SoupStrainer

    metas = BeautifulSoup(head.decode("latin-1"), "html.parser", parse_only=SoupStrainer("meta"))
    for meta in metas.find_all("meta"):
        charset = meta.get("charset")
        if not charset and meta.get("http-equiv", "").lower() == "content-type":
            charset = content_type_charset(meta.get("content", ""))
        if charset:
            return charset
    return ""


def normalized_charset(label: str | None, *, html: bool) -> str:
    """Resolve a charset, keeping the HTML windows-1252 decoder distinct from Python cp1252."""
    label = (label or "").strip().strip("\"'").lower()
    if html and label in _HTML_WINDOWS_1252_LABELS:
        return "windows-1252"
    try:
        return codecs.lookup(label).name if label else ""
    except LookupError:
        return ""


def decode_charset(raw: bytes, charset: str, errors: str = "strict") -> str:
    """Decode a normalized charset, preserving undefined C1 bytes in HTML windows-1252."""
    if charset == "windows-1252":
        return raw.decode("iso8859-1").translate(_CP1252_C1_MAP)
    return raw.decode(charset, errors=errors)


def decode_text_source(raw: bytes, source: Path) -> tuple[str, str]:
    """Decode supported text encodings without replacing undecodable bytes."""
    encodings = ("utf-8", "gb18030")
    if raw.startswith(codecs.BOM_UTF8):
        encodings = ("utf-8-sig",)
    elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encodings = ("utf-16",)
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(
            f"Cannot decode {source} as {' or '.join(encodings)}. "
            "Save the source as UTF-8 text and retry."
        )
    if any(ord(char) < 32 and char not in "\t\n\r\f" for char in text):
        raise ValueError(f"Binary control characters in {source}; provide a text file.")
    return text, encoding
