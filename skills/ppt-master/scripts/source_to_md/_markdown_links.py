#!/usr/bin/env python3
"""PPT Master - Markdown Asset Link Rewriting

Rewrite local companion-directory references without reserializing Markdown.

Usage:
    Import rewrite_local_asset_links from the source-conversion helper directory.

Examples:
    rewrite_local_asset_links("![x](old_files/x.png)", "old_files", "new_files")

Dependencies:
    None (only uses standard library).
"""

from __future__ import annotations

import html
import re
import string
from urllib.parse import quote, unquote, urlsplit


_ESCAPABLE = frozenset(string.punctuation)
_BLOCK_TAGS = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    "colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|"
    "form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|"
    "menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    "table|tbody|td|tfoot|th|thead|title|tr|track|ul"
)
_BLOCK_TAG_RE = re.compile(r"</?(?:" + _BLOCK_TAGS + r")(?=[\s/>]|$)", re.I)
_TAG_RE = re.compile(
    r"</?[A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z_:][\w.:-]*"
    r"(?:\s*=\s*(?:[^\s\"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*\s*/?>"
)
_DECODE_RE = re.compile(
    r"\\[" + re.escape(string.punctuation) + r"]|&(?:#[0-9]+|#[xX][0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);"
)
_AUTOLINK_RE = re.compile(r"<(?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*|[^<>\s]+@[^<>\s]+)>")
_BLOCK_BOUNDARY_RE = re.compile(
    r" {0,3}(?:#{1,6}(?:[ \t]|$)|>|(?:[-+*]|[0-9]{1,9}[.)])[ \t]|"
    r"(?:[-*_][ \t]*){3,}$|[=-]+[ \t]*$)"
)


def _block_mask(content: str) -> str:
    """Hide code and HTML blocks while retaining source offsets."""
    masked = []
    fence = None
    html_end = None
    html_until_blank = False
    previous_blank = True
    list_indent = 0
    quote_depth = 0
    for line in content.splitlines(keepends=True):
        # Containers do not turn their enclosed code/HTML into Markdown prose.
        logical = re.sub(r"^(?: {0,3}>[ \t]?)+", "", line)
        current_quote_depth = line[:len(line) - len(logical)].count(">")
        if current_quote_depth != quote_depth:
            list_indent = 0
        quote_depth = current_quote_depth
        list_marker = re.match(r"^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])([ \t]+)", logical)
        if list_marker:
            list_indent = list_marker.end()
            if len(list_marker[1]) > 4:
                list_indent = list_marker.start(1) + 1
            logical = logical[list_indent:]
        elif list_indent and logical.startswith(" " * list_indent):
            logical = logical[list_indent:]
        elif logical.strip():
            list_indent = 0
        logical = re.sub(r"^(?: {0,3}>[ \t]?)+", "", logical)
        stripped = logical.lstrip(" ")
        indent = len(logical) - len(stripped)
        blank = not logical.strip()
        hide = False
        if fence:
            hide = True
            closing = r" {0,3}" + re.escape(fence[0]) + "{" + str(fence[1]) + r",}[ \t]*$"
            if re.match(closing, logical.rstrip("\r\n")):
                fence = None
        elif html_end:
            hide = True
            if re.search(html_end, line, re.I):
                html_end = None
        elif html_until_blank:
            hide = not blank
            html_until_blank = not blank
        elif indent >= 4 or logical.startswith("\t"):
            hide = True
        elif indent <= 3:
            opening = re.match(r"(`{3,}|~{3,})(.*)", stripped)
            if opening and (opening[1][0] != "`" or "`" not in opening[2]):
                fence = (opening[1][0], len(opening[1]))
                hide = True
            else:
                for start, end in (
                    (r"<(?:script|pre|style|textarea)(?=[\s>]|$)", r"</(?:script|pre|style|textarea)\s*>"),
                    (r"<!--", r"-->"),
                    (r"<\?", r"\?>"),
                    (r"<!\[CDATA\[", r"\]\]>"),
                    (r"<![A-Z]", r">"),
                ):
                    if re.match(start, stripped, re.I):
                        hide = True
                        if not re.search(end, stripped, re.I):
                            html_end = end
                        break
                if not hide and (_BLOCK_TAG_RE.match(stripped) or (
                    previous_blank and _TAG_RE.fullmatch(stripped.rstrip("\r\n \t"))
                )):
                    hide = True
                    html_until_blank = True
        prefix_length = len(line) - len(logical)
        masked.append(re.sub(r"[^\r\n]", " ", line) if hide else " " * prefix_length + logical)
        previous_blank = blank
    return "".join(masked)


def _destination(text: str, start: int):
    """Read an angle or balanced bare CommonMark destination span."""
    if start >= len(text):
        return None
    angle = text[start] == "<"
    pos = start + int(angle)
    begin = pos
    depth = 0
    while pos < len(text):
        char = text[pos]
        if char == "\\" and pos + 1 < len(text) and text[pos + 1] in _ESCAPABLE:
            pos += 2
            continue
        if angle:
            if char == ">":
                return begin, pos, pos + 1
            if char in "<\r\n":
                return None
        else:
            if char.isspace() or ord(char) < 32:
                break
            if char == "(":
                depth += 1
            elif char == ")":
                if not depth:
                    break
                depth -= 1
        pos += 1
    if not angle and not depth:
        return begin, pos, pos
    return None


def _title_end(text: str, pos: int):
    if pos >= len(text) or text[pos] not in "\"'(":
        return None
    delimiter = ")" if text[pos] == "(" else text[pos]
    pos += 1
    start = pos
    while pos < len(text):
        if text[pos] == "\\" and pos + 1 < len(text) and text[pos + 1] in _ESCAPABLE:
            pos += 2
        elif text[pos] == delimiter:
            return None if re.search(r"\n[ \t]*\n", text[start:pos]) else pos + 1
        elif delimiter == ")" and text[pos] == "(":
            return None
        else:
            pos += 1
    return None


def _link_end(text: str, pos: int):
    """Validate the closing parenthesis and optional inline-link title."""
    start = pos
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if re.search(r"\n[ \t]*\n", text[start:pos]):
        return None
    if pos < len(text) and text[pos] == ")":
        return pos + 1
    end = _title_end(text, pos) if pos != start else None
    if end:
        while end < len(text) and text[end].isspace():
            end += 1
        return end + 1 if end < len(text) and text[end] == ")" else None
    return None


def _definition_end(text: str, pos: int):
    """Reject trailing prose and skip the title belonging to a reference definition."""
    start = pos
    while pos < len(text) and text[pos] in " \t":
        pos += 1
    if pos == len(text):
        return pos
    if text[pos] in "\r\n":
        destination_end = pos
        next_line = pos + 1
        while next_line < len(text) and text[next_line] in " \t":
            next_line += 1
        end = _title_end(text, next_line)
        if not end:
            return pos
    elif pos != start:
        destination_end = None
        end = _title_end(text, pos)
    else:
        return None
    if end:
        while end < len(text) and text[end] in " \t":
            end += 1
        if end == len(text) or text[end] in "\r\n":
            return end
    return destination_end


def _target_spans(content: str):
    """Locate destinations in inline links/images and reference definitions."""
    text = _block_mask(content)
    spans = []
    definitions = {}
    for match in re.finditer(r"(?m)^[ \t]*\[(?:\\.|[^\]\\\n])+\]:[ \t]*(?:\n[ \t]*)?", text):
        target = _destination(text, match.end())
        if target and target[0] != target[1]:
            end = _definition_end(text, target[2])
            if end:
                definitions[match.start()] = (target, end)
    stack = []
    pos = 0
    last_definition_end = None
    while pos < len(text):
        if pos in definitions:
            target, end = definitions[pos]
            previous_lines = text[:pos].splitlines()
            previous = previous_lines[-1] if previous_lines else ""
            if not previous.strip() or _BLOCK_BOUNDARY_RE.match(previous) or (
                last_definition_end is not None and not text[last_definition_end:pos].strip()
            ):
                spans.append(target[:2])
                last_definition_end = end
                pos = end
                continue
        char = text[pos]
        if char == "\\" and pos + 1 < len(text) and text[pos + 1] in _ESCAPABLE:
            pos += 2
            continue
        if char == "`":
            run = re.match(r"`+", text[pos:])[0]
            closing = re.search(r"(?<!`)" + run + r"(?!`)", text[pos + len(run):])
            pos += len(run) + (closing.end() if closing else 0)
            continue
        if char == "<":
            tag = _AUTOLINK_RE.match(text, pos) or _TAG_RE.match(text, pos)
            if tag:
                pos = tag.end()
                continue
            if text.startswith("<!--", pos):
                end = text.find("-->", pos + 4)
                if end >= 0:
                    pos = end + 3
                    continue
        if char == "[":
            backslashes = 0
            previous = pos - 2
            while previous >= 0 and text[previous] == "\\":
                backslashes += 1
                previous -= 1
            stack.append((pos > 0 and text[pos - 1] == "!" and backslashes % 2 == 0, True))
        elif char == "\n":
            next_end = text.find("\n", pos + 1)
            next_end = len(text) if next_end < 0 else next_end
            next_line = text[pos + 1:next_end]
            if not next_line.strip() or _BLOCK_BOUNDARY_RE.match(content[pos + 1:next_end]):
                stack.clear()
        elif char == "]" and stack:
            is_image, active = stack.pop()
            if active and text[pos + 1:pos + 2] == "(":
                start = pos + 2
                while start < len(text) and text[start].isspace():
                    start += 1
                target = None if re.search(r"\n[ \t]*\n", text[pos + 2:start]) else _destination(text, start)
                end = _link_end(text, target[2]) if target else None
                if end:
                    spans.append(target[:2])
                    if not is_image:
                        stack = [(image, enabled and image) for image, enabled in stack]
                    pos = end
                    continue
        pos += 1
    return spans


def _rewrite_target(target: str, original_dir: str, imported_dir: str) -> str:
    # Decode only for comparison; everything after the first directory stays raw.
    decoded_parts = []
    offsets = []
    cursor = 0
    for match in _DECODE_RE.finditer(target):
        decoded_parts.append(target[cursor:match.start()])
        offsets.extend(range(cursor, match.start()))
        value = match[0][1:] if match[0].startswith("\\") else html.unescape(match[0])
        decoded_parts.append(value)
        offsets.extend([match.start()] * len(value))
        cursor = match.end()
    decoded_parts.append(target[cursor:])
    offsets.extend(range(cursor, len(target)))
    offsets.append(len(target))
    decoded = "".join(decoded_parts)
    if decoded != decoded.lstrip():
        return target
    if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", decoded) or decoded.startswith(("/", "\\")):
        return target
    path = urlsplit(decoded).path
    start = 0
    while path.startswith("./", start):
        start += 2
    end = path.find("/", start)
    if end < 0 or unquote(path[start:end]) != original_dir:
        return target
    return target[:offsets[start]] + quote(imported_dir, safe="-._~") + target[offsets[end]:]


def rewrite_local_asset_links(content: str, original_dir: str, imported_dir: str) -> str:
    """Rewrite local Markdown destinations rooted in a renamed companion directory."""
    if original_dir == imported_dir:
        return content
    for start, end in sorted(set(_target_spans(content)), reverse=True):
        replacement = _rewrite_target(content[start:end], original_dir, imported_dir)
        content = content[:start] + replacement + content[end:]
    return content
