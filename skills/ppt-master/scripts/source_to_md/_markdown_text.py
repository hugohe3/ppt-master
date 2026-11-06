#!/usr/bin/env python3
"""Escape literal Office text before composing Markdown structures.

Usage:
    Imported by Office source converters.

Examples:
    escape_markdown_text("[literal](missing.png)")

Dependencies:
    Standard library only.
"""

from __future__ import annotations

import re
import uuid


_HTML_SYNTAX_RE = re.compile(r"<(?=[A-Za-z/!?])|&(?=(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#[xX][0-9A-Fa-f]+);)")


def escape_html_syntax(
    value: str, replacements: dict[str, str] | None = None, *, following: str = "",
) -> str:
    """Escape HTML-like prefixes, optionally protecting them through another writer."""
    def escape(match):
        if match.start() >= len(value):
            return match[0]
        escaped = "\\" + match[0]
        if replacements is None:
            return escaped
        token = f"MARKDOWNLITERAL{uuid.uuid4().hex}"
        replacements[token] = escaped
        return token

    escaped = _HTML_SYNTAX_RE.sub(escape, value + following)
    return escaped[:-len(following)] if following else escaped


def escape_markdown_text(value: str, *, block_prefix: bool = False) -> str:
    """Keep literal inline text distinct from generated links, math, and HTML."""
    value = re.sub(r"([\\`*\[\]~$])", r"\\\1", value)
    # Intraword underscores cannot open or close CommonMark emphasis.
    value = re.sub(r"(?<!\w)_+|_+(?!\w)", lambda match: r"\_" * len(match[0]), value)
    if block_prefix:
        def escape_prefix(match):
            marker = match[2]
            marker = marker[:-1] + "\\" + marker[-1] if marker[0].isdigit() else "\\" + marker
            return match[1] + marker

        value = re.sub(
            r"(?m)^([ \t]*)(#{1,6}(?=[ \t]|$)|[-+](?=[ \t]|$)|\d{1,9}[.)](?=[ \t]|$)|-{3,}(?=[ \t]*$))",
            escape_prefix,
            value,
        )
    return escape_html_syntax(value)
