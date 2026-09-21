#!/usr/bin/env python3
"""
PPT Master - Lossless Design Spec Blocks

Locate Markdown blocks without normalizing whitespace or line endings.

Usage:
    Import split_spec_blocks() and replace_spec_block().

Examples:
    from project_management.spec_blocks import split_spec_blocks

Dependencies:
    None (only uses the standard library)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


# Also used by the legacy page-context reader; keep its grammar unchanged.
SLIDE_HEADING_RE = re.compile(
    r"^#{3,6}[ \t]+Slide[ \t]+0*([0-9]+)(?:[ \t]*(?:[-:–—]).*)?$",
    re.IGNORECASE | re.MULTILINE,
)
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_SECTION_RE = re.compile(r"^([IVXLCDM]+)\.(?:[ \t]|$)", re.IGNORECASE)
_TRAILING_SPACE_RE = re.compile(r"[ \t\r\n]*$")


def _slide_match(line: str):
    return SLIDE_HEADING_RE.fullmatch(line.strip(" \t"))


@dataclass(frozen=True)
class SpecBlock:
    """One source range: character offsets plus equivalent UTF-8 byte offsets."""

    kind: str
    key: str
    title: str
    start: int
    end: int
    byte_start: int
    byte_end: int
    section: str


@dataclass(frozen=True)
class SpecBlocks:
    """The untouched preamble followed by contiguous, ordered source blocks."""

    preamble: str
    blocks: tuple[SpecBlock, ...]


def markdown_headings(text: str) -> Iterator[tuple[int, int, str]]:
    """Yield (character offset, level, original line) outside fenced code."""
    fence = ""
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        match = _FENCE_RE.fullmatch(line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = ""
        elif match and not (match[1][0] == "`" and "`" in match[2]):
            fence = match[1]
        else:
            heading = _HEADING_RE.fullmatch(line)
            if heading:
                yield offset, len(heading[1]), line
        offset += len(raw_line)


def split_spec_blocks(text: str) -> SpecBlocks:
    """Partition raw text; preamble + all block slices is exactly the input.

    H2 sections are blocks. In section IX each H3-H6 Slide and each non-Slide
    H3 Part heading starts a separate block. Parts are numbered by occurrence.
    Duplicate keys receive occurrence suffixes so malformed specs remain readable.
    """
    starts: list[tuple[int, str, str, str, str]] = []
    occurrences: dict[str, int] = {}
    section = ""
    part_number = 0
    for offset, level, line in markdown_headings(text):
        title = line.lstrip(" ").lstrip("#").strip()
        if level == 2:
            match = _SECTION_RE.match(title)
            section = match[1].upper() if match else title
            kind, key = ("outline", "section:IX") if section == "IX" else ("section", f"section:{section}")
        elif section == "IX" and (match := _slide_match(line)):
            kind, key = "slide", f"slide:{int(match[1]):02d}"
        elif section == "IX" and level == 3:
            part_number += 1
            kind, key = "part", f"part:{part_number:02d}"
        else:
            continue
        occurrences[key] = occurrences.get(key, 0) + 1
        if occurrences[key] > 1:
            key = f"{key}~{occurrences[key]}"
        starts.append((offset, kind, key, line, section))

    preamble = text[:starts[0][0]] if starts else text
    blocks: list[SpecBlock] = []
    byte_offset = len(preamble.encode("utf-8"))
    for index, (start, kind, key, title, section) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        byte_end = byte_offset + len(text[start:end].encode("utf-8"))
        blocks.append(SpecBlock(kind, key, title, start, end, byte_offset, byte_end, section))
        byte_offset = byte_end
    return SpecBlocks(preamble, tuple(blocks))


def replace_spec_block(text: str, key: str, replacement: str) -> str:
    """Replace one block, preserving surrounding bytes and its final whitespace.

    Browser textareas use LF. Changed text uses the block's original newline
    style; an unchanged textarea round trip preserves even mixed line endings.
    Section headings, Slide identities, and Part bodies cannot be edited here.
    """
    layout = split_spec_blocks(text)
    block = next((item for item in layout.blocks if item.key == key), None)
    if block is None:
        raise ValueError(f"Unknown block {key}; reload the spec.")
    before = text[block.start:block.end]
    normalize = lambda value: value.replace("\r\n", "\n").replace("\r", "\n")
    if normalize(before) == normalize(replacement):
        return text
    newline = re.search(r"\r\n|\r|\n", before) or re.search(r"\r\n|\r|\n", text)
    replacement = normalize(replacement).replace("\n", newline[0] if newline else "\n")
    tail = _TRAILING_SPACE_RE.search(before)[0]
    replacement = _TRAILING_SPACE_RE.sub("", replacement) + tail
    headings = list(markdown_headings(replacement))
    if not headings or headings[0][0] != 0:
        raise ValueError("Keep the block's heading on the first line.")
    first = headings[0][2]
    if block.kind == "slide":
        old = _slide_match(block.title)
        new = _slide_match(first)
        if not new or new[1] != old[1] or first[:first.index(new[0]) + new.end(1)] != (
            block.title[:block.title.index(old[0]) + old.end(1)]
        ):
            raise ValueError("Keep the Slide heading level and number; only its page name may change.")
    elif block.kind == "part":
        if headings[0][1] != 3 or _slide_match(first):
            raise ValueError("Keep the Part heading level; only its title text may change.")
        if normalize(before[len(block.title):]) != normalize(replacement[len(first):]):
            raise ValueError("Only the Part title text may change; keep its remaining content unchanged.")
    elif first != block.title:
        raise ValueError("Keep the section heading unchanged; request structural changes in an annotation.")
    for _, level, line in headings[1:]:
        if level == 2 or _slide_match(line) or (block.section == "IX" and level == 3):
            raise ValueError("Structural heading injection (##, Part, or Slide) is not allowed; use an annotation.")
    candidate = text[:block.start] + replacement + text[block.end:]
    if [(item.kind, item.key) for item in split_spec_blocks(candidate).blocks] != [
        (item.kind, item.key) for item in layout.blocks
    ]:
        raise ValueError("The edit changes block boundaries (check fenced code); use an annotation.")
    return candidate
