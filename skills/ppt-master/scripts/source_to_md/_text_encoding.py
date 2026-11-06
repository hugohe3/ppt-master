#!/usr/bin/env python3
"""Decode text sources consistently for conversion and project import.

Usage:
    Imported by source_to_md.py and project_management.cli.
Examples:
    text, encoding = decode_text_source(raw, source)
Dependencies:
    None (standard library only).
"""

import codecs
from pathlib import Path


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
