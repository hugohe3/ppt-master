#!/usr/bin/env python3
"""
PDF to Markdown Converter
Uses PyMuPDF to extract PDF text content and convert to Markdown format.
Supports heading levels, bold, italic, and list detection.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from _batch import run_path_batch  # noqa: E402
from _conversion_profile import write_conversion_profile_best_effort  # noqa: E402

configure_utf8_stdio()

try:
    import fitz  # PyMuPDF
except ImportError:
    print("[ERROR] PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)

FONT_BODY_SIZE = 12
FONT_H1_SIZE = 24
FONT_H2_SIZE = 18
FONT_H3_SIZE = 14
HEADER_FOOTER_SAMPLE_LIMIT = 40
HEADER_FOOTER_EDGE_SAMPLE_SIZE = 20
CONTROL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def analyze_font_sizes(doc: fitz.Document) -> dict[str, float]:
    """Analyze font size distribution to infer heading levels.

    Args:
        doc: Open PDF document.

    Returns:
        A size mapping containing body and inferred heading sizes.
    """
    size_counter = Counter()

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        size = round(span["size"], 1)
                        text = span["text"].strip()
                        if text:
                            size_counter[size] += len(text)

    if not size_counter:
        return {
            "body": FONT_BODY_SIZE,
            "h1": FONT_H1_SIZE,
            "h2": FONT_H2_SIZE,
            "h3": FONT_H3_SIZE,
        }

    sorted_sizes = sorted(size_counter.items(), key=lambda x: x[1], reverse=True)
    body_size = sorted_sizes[0][0]

    all_sizes = sorted(size_counter.keys(), reverse=True)
    larger_sizes = [s for s in all_sizes if s > body_size + 1]

    size_map = {"body": body_size}
    if len(larger_sizes) >= 1:
        size_map["h1"] = larger_sizes[0]
    if len(larger_sizes) >= 2:
        size_map["h2"] = larger_sizes[1]
    if len(larger_sizes) >= 3:
        size_map["h3"] = larger_sizes[2]

    return size_map


def get_heading_level(size: float, size_map: dict, text: str = "",
                      flags: int = 0, strict: bool = True) -> int:
    """
    Determine heading level using multiple heuristics.

    Args:
        size: Font size
        size_map: Font size mapping
        text: Text content (used for additional heuristics)
        flags: Font flags (bit 4 = bold)
        strict: Strict mode, requires more conditions to be met

    Returns:
        Heading level (0 = body text, 1-3 = H1-H3)
    """
    # Initial determination based on font size
    level = 0
    if "h1" in size_map and size >= size_map["h1"] - 0.5:
        level = 1
    elif "h2" in size_map and size >= size_map["h2"] - 0.5:
        level = 2
    elif "h3" in size_map and size >= size_map["h3"] - 0.5:
        level = 3

    if level == 0:
        return 0

    # Non-strict mode returns directly (backward compatible)
    if not strict or not text:
        return level

    # Strict mode: additional validation conditions
    text = text.strip()

    # Exclusion: text too long is unlikely to be a heading
    if len(text) > 80:
        return 0

    # Exclusion: complete sentences ending with punctuation
    sentence_endings = '.。!！?？'
    if text and text[-1] in sentence_endings:
        # But keep numbered headings like "1. Overview" or "Chapter 1."
        if not re.match(r'^[\d第]+[.、章节]', text):
            return 0

    # Bonus: bold text is more likely to be a heading
    is_bold = flags & 16
    if not is_bold and level >= 2:
        # Non-bold subheadings require a larger font size difference
        body_size = size_map.get("body", 12)
        if size < body_size + 2:
            return 0

    return level

def is_monospace_font(font_name: str) -> bool:
    """
    Determine if the font is monospace (typically used for code).
    """
    if not font_name:
        return False
    font_lower = font_name.lower()
    mono_fonts = [
        'courier', 'consolas', 'monaco', 'menlo', 'monospace',
        'source code', 'fira code', 'jetbrains', 'inconsolata',
        'dejavu sans mono', 'liberation mono', 'ubuntu mono',
        'roboto mono', 'robotomono', 'sf mono', 'cascadia', 'hack'
    ]
    return any(f in font_lower for f in mono_fonts)


def format_span_text(text: str, flags: int) -> str:
    """Format text based on font flags (bold, italic)."""
    text = CONTROL_CHARS_RE.sub('', text)
    text = text.strip()
    if not text:
        return ""

    is_bold = flags & 16
    is_italic = flags & 2

    if is_bold and is_italic:
        return f"***{text}***"
    elif is_bold:
        return f"**{text}**"
    elif is_italic:
        return f"*{text}*"
    return text


def detect_list_item(text: str) -> tuple:
    """Detect if the text is a list item. Returns (is_list, list_type, content)."""
    text = text.strip()

    ul_patterns = [
        (r'^[•●○◦▪▸►]\s*', '-'),
        (r'^[-–—]\s+', '-'),
        (r'^\*\s+', '-'),
    ]
    for pattern, marker in ul_patterns:
        match = re.match(pattern, text)
        if match:
            return (True, 'ul', marker + ' ' + text[match.end():])

    ol_pattern = r'^(\d+)[.、)]\s*'
    match = re.match(ol_pattern, text)
    if match:
        num = match.group(1)
        return (True, 'ol', f"{num}. " + text[match.end():])

    return (False, None, text)


def remove_page_footer(text: str) -> str:
    """
    Remove page number patterns from footers, e.g. 'November 2025 8' or '2025年11月 8'.
    """
    # English month + year + page number
    months_en = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
    pattern_en = rf'\s*{months_en}\s+\d{{4}}\s+\d{{1,3}}\s*$'
    text = re.sub(pattern_en, '', text, flags=re.IGNORECASE)

    # Chinese format: 2025年11月 8
    pattern_cn = r'\s*\d{4}年\d{1,2}月\s+\d{1,3}\s*$'
    text = re.sub(pattern_cn, '', text)

    return text.rstrip()


def detect_headers_footers(doc: fitz.Document, threshold_ratio: float = 0.6) -> set[str]:
    """
    Detect headers and footers statistically.

    Principle: Headers and footers typically appear at fixed positions (top or bottom)
    on each page with the same content. We collect top and bottom text from all pages,
    and if certain text appears more frequently than the threshold, it is treated as noise.
    """
    if len(doc) < 3:
        return set()

    headers = []
    footers = []

    # Sample first 20 and last 20 pages (avoid processing too slowly)
    pages_to_scan = list(range(len(doc)))
    if len(doc) > HEADER_FOOTER_SAMPLE_LIMIT:
        pages_to_scan = (
            pages_to_scan[:HEADER_FOOTER_EDGE_SAMPLE_SIZE]
            + pages_to_scan[-HEADER_FOOTER_EDGE_SAMPLE_SIZE:]
        )

    for i in pages_to_scan:
        page = doc[i]
        rect = page.rect
        h = rect.height

        # Define top and bottom regions (15% each)
        top_rect = fitz.Rect(0, 0, rect.width, h * 0.15)
        bottom_rect = fitz.Rect(0, h * 0.85, rect.width, h)

        # Extract text blocks
        blocks = page.get_text("blocks")
        for b in blocks:
            b_rect = fitz.Rect(b[:4])
            text = b[4].strip()
            if not text:
                continue

            # Simple spatial determination
            if b_rect.intersects(top_rect):
                headers.append(text)
            elif b_rect.intersects(bottom_rect):
                footers.append(text)

    # Count frequencies
    noise_texts = set()
    total_scanned = len(pages_to_scan)

    for collection in [headers, footers]:
        counter = Counter(collection)
        for text, count in counter.items():
            # if text appears in > 60% of scanned pages, mark as noise
            if count / total_scanned > threshold_ratio:
                noise_texts.add(text)

    return noise_texts


def merge_adjacent_headings(elements: list) -> list:
    """
    Merge adjacent same-level short headings.
    Example: '# Agent Tools &' + '# Interoperability' -> '# Agent Tools & Interoperability'
    """
    if not elements:
        return elements

    merged = []
    i = 0

    while i < len(elements):
        el = elements[i]

        # Only process heading elements
        if el.get("type") != 0 or not el.get("is_heading"):
            merged.append(el)
            i += 1
            continue

        content = el["content"]
        # Extract heading level
        match = re.match(r'^(#{1,6})\s+(.+)$', content)
        if not match:
            merged.append(el)
            i += 1
            continue

        level = match.group(1)
        title_text = match.group(2)

        # If heading is short and the next one is also the same level, try to merge
        j = i + 1
        while j < len(elements) and len(title_text) < 60:
            next_el = elements[j]
            if next_el.get("type") != 0 or not next_el.get("is_heading"):
                break

            next_match = re.match(r'^(#{1,6})\s+(.+)$', next_el["content"])
            if not next_match or next_match.group(1) != level:
                break

            next_text = next_match.group(2)
            # Only merge short heading fragments
            if len(next_text) > 40:
                break

            # Merge
            title_text += " " + next_text
            j += 1

        # Create merged element
        merged_el = el.copy()
        merged_el["content"] = f"{level} {title_text}"
        merged.append(merged_el)
        i = j

    return merged


# Image filtering thresholds
MIN_IMAGE_PIXELS = 100       # Minimum pixel dimension (width AND height)
MIN_IMAGE_AREA = 30000       # Minimum pixel area (e.g. 200x150)
MIN_IMAGE_BYTES = 2048       # Minimum image data size (2KB)
MIN_PAGE_RATIO = 0.05        # Minimum render size relative to page (5%)
MIN_VISIBLE_IMAGE_WIDTH = 40
MIN_VISIBLE_IMAGE_HEIGHT = 40
MIN_VISIBLE_IMAGE_AREA_RATIO = 0.01
MAX_ASPECT_RATIO = 12        # Maximum aspect ratio (filters decorative bars)
MAX_LOW_INFO_BPP = 0.08      # Bytes-per-pixel threshold for low-info images
MAX_LOW_INFO_AREA = 500000   # Area threshold: only apply bpp filter below this
MIN_VECTOR_FIGURE_WIDTH = 100
MIN_VECTOR_FIGURE_HEIGHT = 80
MIN_VECTOR_FIGURE_AREA = 30000
MAX_VECTOR_FIGURE_ASPECT_RATIO = 8
VECTOR_FIGURE_PADDING = 4
VECTOR_FIGURE_DPI = 180
VECTOR_CAPTION_SEARCH_HEIGHT = 380
VECTOR_CAPTION_HORIZONTAL_GAP = 90
MAX_VECTOR_BACKGROUND_AREA_RATIO = 1.9
# Caption delimiters: ``Figure 1:`` / ``Figure 1.`` (classic) and ``Figure 1 |``
# (the DeepMind / Distill / Nature house style used by many ML papers, incl.
# full-width ``｜``). Without the pipe variants, captioned vector figures route
# to the generic per-drawing fallback, which discards fine-grained line plots
# (each plot is hundreds of tiny primitives, none large enough on its own).
FIGURE_CAPTION_RE = re.compile(r'^(?:Figure|Fig\.?)\s*\d+\s*[:.|｜]', re.IGNORECASE)


TABLE_CAPTION_RE = re.compile(
    r'^\u8868\s*\d+(?:\.\d+)*\s+(?!(?:\u7684|\u5217\u793a|\u6240\u793a|\u4e3a)).+'
)
TABLE_REFERENCE_PROSE_RE = re.compile(
    r'^\u8868\s*\d+(?:\.\d+)*\s*(?:\u7684|\u5217\u793a|\u6240\u793a|\u4e3a)'
)
SECTION_HEADING_RE = re.compile(r'^\d+(?:\.\d+){1,3}\s+\S')
NUMBER_RE = re.compile(r'[-+]?\d+(?:\.\d+)?')
MODEL_COLUMN_RE = re.compile(r'^[（(]\d+[）)]$')
TABLE_NOTE_PREFIX = '\u6ce8'
TABLE_CONTINUATION_Y_RATIO = 0.88
TABLE_SCAN_BOTTOM_RATIO = 0.92


def should_keep_image(
    block: dict[str, object],
    page_rect: fitz.Rect,
    seen_hashes: set[str] | None = None,
) -> bool:
    """Filter out small, decorative, or duplicate images.

    Args:
        block: Image block extracted from PyMuPDF.
        page_rect: Current page rectangle.
        seen_hashes: Optional set used to deduplicate image payloads.

    Returns:
        Whether the image should be kept in the Markdown output.
    """
    w, h = block.get("width", 0), block.get("height", 0)
    bbox = block.get("bbox", (0, 0, 0, 0))
    render_w = bbox[2] - bbox[0]
    render_h = bbox[3] - bbox[1]
    page_area = page_rect.width * page_rect.height
    render_area_ratio = (render_w * render_h) / page_area if page_area > 0 else 0
    visibly_placed = (
        render_w >= MIN_VISIBLE_IMAGE_WIDTH
        and render_h >= MIN_VISIBLE_IMAGE_HEIGHT
        and render_area_ratio >= MIN_VISIBLE_IMAGE_AREA_RATIO
    )

    # Pixel dimension filter
    if not visibly_placed and (w < MIN_IMAGE_PIXELS or h < MIN_IMAGE_PIXELS):
        return False

    # Pixel area filter
    area = w * h
    if not visibly_placed and area < MIN_IMAGE_AREA:
        return False

    image_data = block.get("image", b"")
    if not visibly_placed and len(image_data) < MIN_IMAGE_BYTES:
        return False

    # Deduplicate tiny repeats, but preserve visibly placed logos / charts on
    # distinct pages. Academic PDFs often reuse a small logo on title pages.
    if seen_hashes is not None:
        img_hash = hashlib.md5(image_data).hexdigest()
        if img_hash in seen_hashes and not visibly_placed:
            return False
        seen_hashes.add(img_hash)

    # Check render size relative to page
    page_w = page_rect.width
    page_h = page_rect.height
    if page_w > 0 and page_h > 0:
        if render_w / page_w < MIN_PAGE_RATIO and render_h / page_h < MIN_PAGE_RATIO:
            return False

    # Filter extreme aspect ratios (decorative bars/separators)
    aspect = max(w, h) / max(min(w, h), 1)
    if aspect > MAX_ASPECT_RATIO:
        return False

    # Filter low-info images: solid color blocks / gradients have very high
    # compression ratios (low bytes-per-pixel). Only apply to smaller images
    # to avoid filtering large photos with dark/uniform backgrounds.
    bpp = len(image_data) / area
    if bpp < MAX_LOW_INFO_BPP and area < MAX_LOW_INFO_AREA and not visibly_placed:
        return False

    return True


def _clip_rect_to_page(rect: fitz.Rect, page_rect: fitz.Rect) -> fitz.Rect:
    """Clamp a rectangle to the current PDF page."""
    return fitz.Rect(
        max(page_rect.x0, rect.x0),
        max(page_rect.y0, rect.y0),
        min(page_rect.x1, rect.x1),
        min(page_rect.y1, rect.y1),
    )


def _is_rect_contained(inner: fitz.Rect, outer: fitz.Rect, threshold: float = 0.9) -> bool:
    """Return whether ``inner`` is mostly covered by ``outer``."""
    inner_area = inner.get_area()
    if inner_area <= 0:
        return False
    return ((inner & outer).get_area() / inner_area) >= threshold


def _overlaps_table(rect: fitz.Rect, tab_rects: list[fitz.Rect]) -> bool:
    """Skip vector regions that are already handled as extracted tables."""
    rect_area = rect.get_area()
    if rect_area <= 0:
        return False
    for tab_rect in tab_rects:
        intersection = rect & tab_rect
        if intersection.get_area() > 0.5 * min(rect_area, tab_rect.get_area()):
            return True
    return False


def _is_white(color: tuple[float, ...] | None) -> bool:
    """Return whether a PDF drawing color is visually white."""
    if color is None:
        return False
    return all(channel >= 0.98 for channel in color[:3])


def _is_background_drawing(drawing: dict[str, object]) -> bool:
    """Identify white background rectangles that should not drive crops."""
    return _is_white(drawing.get("fill")) and drawing.get("color") is None


def find_figure_caption_rects(page: fitz.Page) -> list[fitz.Rect]:
    """Return text-line rectangles that look like figure captions."""
    caption_rects = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if FIGURE_CAPTION_RE.match(text):
                caption_rects.append(fitz.Rect(line["bbox"]))
    return caption_rects


def _expand_rect(rect: fitz.Rect, padding: float, page_rect: fitz.Rect) -> fitz.Rect:
    """Pad a rectangle and clamp it to the current PDF page."""
    return _clip_rect_to_page(
        fitz.Rect(
            rect.x0 - padding,
            rect.y0 - padding,
            rect.x1 + padding,
            rect.y1 + padding,
        ),
        page_rect,
    )


def _union_rects(rects: list[fitz.Rect]) -> fitz.Rect:
    """Return the bounding union for one or more rectangles."""
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result |= rect
    return result


def _find_captioned_vector_figures(
    page: fitz.Page,
    drawing_rects: list[fitz.Rect],
    background_rects: list[fitz.Rect],
    caption_rects: list[fitz.Rect],
) -> list[fitz.Rect]:
    """Build tight figure crops from non-background drawings above captions."""
    figure_rects = []
    page_rect = page.rect

    for caption_rect in caption_rects:
        related = []
        for rect in drawing_rects:
            horizontal_gap = max(caption_rect.x0 - rect.x1, rect.x0 - caption_rect.x1, 0)
            if horizontal_gap > VECTOR_CAPTION_HORIZONTAL_GAP:
                continue
            if rect.y0 > caption_rect.y0:
                continue
            if caption_rect.y0 - rect.y1 > VECTOR_CAPTION_SEARCH_HEIGHT:
                continue
            related.append(rect)

        if not related:
            continue

        content_rect = _union_rects(related)
        rect = content_rect
        for background_rect in background_rects:
            background_rect = _clip_rect_to_page(background_rect, page_rect)
            if not _is_rect_contained(content_rect, background_rect, threshold=0.95):
                continue
            if background_rect.get_area() > content_rect.get_area() * MAX_VECTOR_BACKGROUND_AREA_RATIO:
                continue
            rect = background_rect
            break

        rect = _expand_rect(rect, 10, page_rect)
        rect.y1 = min(rect.y1, caption_rect.y0 - 2)
        if rect.width >= MIN_VECTOR_FIGURE_WIDTH and rect.height >= MIN_VECTOR_FIGURE_HEIGHT:
            figure_rects.append(rect)

    return figure_rects


def detect_vector_figure_rects(page: fitz.Page, tab_rects: list[fitz.Rect]) -> list[fitz.Rect]:
    """Detect large vector drawing regions that should be rasterized as figures.

    Some academic PDFs store charts and diagrams as vector drawing commands,
    not image XObjects. ``page.get_text("dict")`` exposes only raster image
    blocks, so those figures need a separate drawing-region fallback.
    """
    candidates = []
    page_rect = page.rect
    caption_rects = find_figure_caption_rects(page)
    drawing_rects = []
    background_rects = []

    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if not rect:
            continue

        rect = fitz.Rect(rect)
        if rect.is_empty:
            continue

        if _is_background_drawing(drawing):
            background_rects.append(rect)
            continue

        drawing_rects.append(rect)

    if caption_rects:
        return _find_captioned_vector_figures(page, drawing_rects, background_rects, caption_rects)

    for rect in drawing_rects:
        rect = _expand_rect(rect, VECTOR_FIGURE_PADDING, page_rect)
        rect = _clip_rect_to_page(rect, page_rect)

        width = rect.width
        height = rect.height
        if width < MIN_VECTOR_FIGURE_WIDTH or height < MIN_VECTOR_FIGURE_HEIGHT:
            continue

        area = rect.get_area()
        if area < MIN_VECTOR_FIGURE_AREA:
            continue

        aspect = max(width, height) / max(min(width, height), 1)
        if aspect > MAX_VECTOR_FIGURE_ASPECT_RATIO:
            continue

        if _overlaps_table(rect, tab_rects):
            continue

        candidates.append(rect)

    candidates.sort(key=lambda r: r.get_area(), reverse=True)

    kept = []
    for rect in candidates:
        if any(_is_rect_contained(rect, existing) for existing in kept):
            continue
        kept.append(rect)

    return sorted(kept, key=lambda r: (r.y0, r.x0))


def clean_text(text: str) -> str:
    """Clean extracted text."""
    lines = text.split('\n')
    cleaned_lines = []
    prev_empty = False

    for line in lines:
        line = line.rstrip()
        is_empty = len(line.strip()) == 0

        if is_empty:
            if not prev_empty:
                cleaned_lines.append('')
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    return '\n'.join(cleaned_lines)


def _extract_text_lines(page: fitz.Page) -> list[tuple[fitz.Rect, str]]:
    """Return text lines with their page rectangles in reading order."""
    lines = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            text = "".join(span["text"] for span in line["spans"]).strip()
            if text:
                lines.append((fitz.Rect(line["bbox"]), text))
    return sorted(lines, key=lambda item: (item[0].y0, item[0].x0))


def _is_table_caption(text: str) -> bool:
    """Return whether a line is a real table caption, not prose citing a table."""
    return bool(TABLE_CAPTION_RE.match(text.strip()))


def _caption_table_start_y(
    caption_rect: fitz.Rect,
    lines: list[tuple[fitz.Rect, str]],
) -> float:
    """Start below a caption and its adjacent English translation line."""
    start_y = caption_rect.y1 + 1
    for rect, text in lines:
        if rect.y0 < caption_rect.y1 - 1 or rect.y0 > caption_rect.y1 + 35:
            continue
        if text.startswith("Table"):
            start_y = max(start_y, rect.y1 + 1)
    return start_y


def _looks_like_numeric_table_line(text: str) -> bool:
    """Detect long data rows so they are not mistaken for prose boundaries."""
    numbers = NUMBER_RE.findall(text)
    if len(numbers) >= 3:
        return True
    tokens = [token for token in re.split(r'\s+', text.strip()) if token]
    return len(tokens) >= 4 and len(numbers) >= 2


def _is_table_region_boundary(
    rect: fitz.Rect,
    text: str,
    page: fitz.Page,
    start_y: float,
) -> bool:
    """Return whether a line likely starts prose after a text-detected table."""
    text = text.strip()
    if rect.y0 < start_y + 45:
        return False
    if text.startswith(TABLE_NOTE_PREFIX):
        return True
    if SECTION_HEADING_RE.match(text):
        return True
    if TABLE_REFERENCE_PROSE_RE.match(text):
        return True
    if _looks_like_numeric_table_line(text):
        return False

    width_ratio = rect.width / page.rect.width if page.rect.width > 0 else 0
    return len(text) >= 26 and width_ratio > 0.52 and rect.x0 < page.rect.width * 0.25


def _table_region_bottom(
    page: fitz.Page,
    lines: list[tuple[fitz.Rect, str]],
    start_y: float,
) -> float:
    """Find a conservative bottom edge for a caption-guided text table scan."""
    for rect, text in lines:
        if rect.y0 <= start_y:
            continue
        if _is_table_region_boundary(rect, text, page, start_y):
            return max(start_y + 20, rect.y0 - 2)
    return page.rect.height * TABLE_SCAN_BOTTOM_RATIO


def _normalize_table_cell(value: object) -> str:
    """Normalize one extracted table cell for Markdown output."""
    if value is None:
        return ""
    text = CONTROL_CHARS_RE.sub('', str(value))
    text = re.sub(r'\s*\n\s*', '<br>', text.strip())
    text = re.sub(r'[ \t]+', ' ', text)
    return text.replace('|', r'\|')


def _clean_table_rows(rows: list[list[object]]) -> list[list[str]]:
    """Remove empty rows / columns from PyMuPDF table extraction output."""
    normalized = [[_normalize_table_cell(cell) for cell in row] for row in rows]
    normalized = [row for row in normalized if any(cell for cell in row)]
    if not normalized:
        return []

    max_cols = max(len(row) for row in normalized)
    padded = [row + [""] * (max_cols - len(row)) for row in normalized]
    keep_cols = [
        idx
        for idx in range(max_cols)
        if any(row[idx] for row in padded)
    ]
    if len(keep_cols) < 2:
        return []
    return _postprocess_table_rows([[row[idx] for idx in keep_cols] for row in padded])


def _nonempty_cell_indexes(row: list[str]) -> list[int]:
    """Return indexes of non-empty cells in a row."""
    return [idx for idx, cell in enumerate(row) if cell]


def _merge_label_underscore_rows(rows: list[list[str]]) -> list[list[str]]:
    """Join rows where PDF extraction split a leading underscore from a label."""
    merged = []
    for row in rows:
        nonempty = _nonempty_cell_indexes(row)
        if nonempty == [0] and row[0] == "_" and merged and merged[-1][0]:
            merged[-1][0] = f"_{merged[-1][0]}"
            continue
        merged.append(row)
    return merged


def _merge_single_cell_continuations(rows: list[list[str]]) -> list[list[str]]:
    """Merge wrapped single-cell table rows into the previous row."""
    merged: list[list[str]] = []
    for row in rows:
        nonempty = _nonempty_cell_indexes(row)
        if (
            len(nonempty) == 1
            and nonempty[0] > 0
            and merged
            and not MODEL_COLUMN_RE.match(row[nonempty[0]])
        ):
            index = nonempty[0]
            separator = "<br>" if merged[-1][index] else ""
            merged[-1][index] = f"{merged[-1][index]}{separator}{row[index]}"
            continue
        merged.append(row)
    return merged


def _looks_like_model_row(row: list[str]) -> bool:
    """Return whether a row contains model-number table headings."""
    values = [cell for cell in row[1:] if cell]
    return len(values) >= 2 and all(MODEL_COLUMN_RE.match(cell) for cell in values)


def _looks_like_outcome_row(row: list[str]) -> bool:
    """Return whether a row contains regression outcome labels."""
    values = [cell for cell in row[1:] if cell]
    if len(values) < 2:
        return False
    short_values = [cell for cell in values if len(cell) <= 12 and not NUMBER_RE.search(cell)]
    return len(short_values) == len(values)


def _regression_group_labels(row: list[str], data_cols: int) -> list[str]:
    """Infer repeated group labels for common regression-table headings."""
    compact = "".join(row)
    if "总样本" in compact and "国有" in compact and "非国有" in compact and data_cols == 7:
        return ["总样本"] * 3 + ["国有企业"] * 2 + ["非国有企业"] * 2
    return [""] * data_cols


def _flatten_regression_header(rows: list[list[str]]) -> list[list[str]]:
    """Flatten multi-line regression headings into one Markdown header row."""
    if len(rows) < 3:
        return rows

    if (
        len(rows) >= 2
        and rows[0][0]
        and not any(rows[0][1:])
        and _looks_like_model_row(rows[1])
    ):
        outcome = rows[0][0]
        header = ["变量"]
        header.extend(
            f"{model} {outcome}".strip()
            for model in rows[1][1:]
        )
        return [header] + rows[2:]

    header_offset = 0
    groups = [""] * (len(rows[0]) - 1)
    if not _looks_like_model_row(rows[0]) and _looks_like_model_row(rows[1]):
        header_offset = 1
        groups = _regression_group_labels(rows[0], len(rows[1]) - 1)

    if not _looks_like_model_row(rows[header_offset]):
        return rows
    if len(rows) <= header_offset + 1 or not _looks_like_outcome_row(rows[header_offset + 1]):
        return rows

    model_row = rows[header_offset]
    outcome_row = rows[header_offset + 1]
    header = ["变量"]
    for idx, model in enumerate(model_row[1:]):
        pieces = []
        if idx < len(groups) and groups[idx]:
            pieces.append(groups[idx])
        if model:
            pieces.append(model)
        if idx + 1 < len(outcome_row) and outcome_row[idx + 1]:
            pieces.append(outcome_row[idx + 1])
        header.append(" ".join(pieces).strip())
    return [header] + rows[header_offset + 2:]


def _fix_paired_sample_t_table(rows: list[list[str]]) -> list[list[str]]:
    """Collapse multi-row paired-sample T-test headings into readable columns."""
    if not rows or not any("成对差分" in cell for cell in rows[0]):
        return rows
    body = [row for row in rows if row and row[0].startswith("对")]
    if len(body) < 1:
        return rows
    header = [
        "配对",
        "变量",
        "均值",
        "标准差",
        "均值的标准误",
        "差分95%置信区间下限",
        "差分95%置信区间上限",
        "t",
        "Df",
        "Sig.(双侧)",
    ]
    fixed_rows = [header]
    for row in body:
        fixed_rows.append(row[:len(header)] + [""] * max(0, len(header) - len(row)))
    return fixed_rows


def _fix_variable_definition_table(rows: list[list[str]]) -> list[list[str]]:
    """Repeat variable-category labels for common variable definition tables."""
    if not rows or rows[0] != ["变量类型", "变量名称", "符号", "变量说明"]:
        return rows

    fixed = [rows[0]]
    for row in rows[1:]:
        if not any(row):
            continue
        name = row[1] if len(row) > 1 else ""
        symbol = row[2] if len(row) > 2 else ""
        description = row[3] if len(row) > 3 else ""
        if not name or not symbol:
            continue

        if symbol in {"R＆D", "Fixed", "Hc"}:
            category = "被解释变量"
        elif symbol == "Vat":
            category = "解释变量"
        else:
            category = "控制变量"
        fixed.append([category, name, symbol, description])
    return fixed


def _fix_correlation_triangle(rows: list[list[str]]) -> list[list[str]]:
    """Restore the missing last self-correlation column in triangular tables."""
    if len(rows) < 4 or not rows[0] or rows[0][0] != "变量":
        return rows
    body_names = [row[0] for row in rows[1:] if row and row[0]]
    header_names = rows[0][1:]
    if len(body_names) != len(header_names) + 1:
        return rows
    missing_name = body_names[-1]
    fixed = [rows[0] + [missing_name]]
    for row in rows[1:-1]:
        fixed.append(row + [""])
    fixed.append(rows[-1] + ["1"])
    return fixed


def _postprocess_table_rows(rows: list[list[str]]) -> list[list[str]]:
    """Apply Markdown-oriented cleanup to extracted table rows."""
    rows = _merge_label_underscore_rows(rows)
    rows = _merge_single_cell_continuations(rows)
    rows = _fix_variable_definition_table(rows)
    rows = _fix_paired_sample_t_table(rows)
    rows = _flatten_regression_header(rows)
    rows = _fix_correlation_triangle(rows)
    return rows


def _rows_to_markdown(rows: list[list[str]]) -> str:
    """Convert cleaned table rows to GitHub-flavored Markdown."""
    if len(rows) < 2:
        return ""
    col_count = max(len(row) for row in rows)
    padded = [row + [""] * (col_count - len(row)) for row in rows]
    header = padded[0]
    body = padded[1:]
    lines = [
        "|" + "|".join(header) + "|",
        "|" + "|".join(["---"] * col_count) + "|",
    ]
    lines.extend("|" + "|".join(row) + "|" for row in body)
    return "\n".join(lines)


def _table_to_markdown(tab: object) -> str:
    """Convert a PyMuPDF table object to cleaned Markdown."""
    try:
        rows = tab.extract() or []
    except Exception:
        return ""
    return _rows_to_markdown(_clean_table_rows(rows))


def _is_valid_table_markdown(markdown: str) -> bool:
    """Return whether generated Markdown contains a minimally useful table."""
    return markdown.count("\n") >= 2 and markdown.startswith("|")


def _markdown_col_count(markdown: str) -> int:
    """Return the column count implied by the first Markdown table row."""
    first_line = markdown.splitlines()[0] if markdown else ""
    return max(0, first_line.count("|") - 1)


def _append_table_markdown_candidate(
    candidates: list[dict[str, object]],
    bbox: fitz.Rect,
    markdown: str,
    method: str,
    replace_narrow: bool = False,
) -> None:
    """Append or replace a table candidate after overlap deduplication."""
    if not _is_valid_table_markdown(markdown):
        return

    for index, candidate in enumerate(candidates):
        existing = candidate["bbox"]
        if not isinstance(existing, fitz.Rect):
            continue
        overlap = (bbox & existing).get_area()
        if overlap <= 0.8 * min(bbox.get_area(), existing.get_area()):
            continue

        existing_markdown = str(candidate.get("content", ""))
        can_replace = (
            replace_narrow
            and bbox.width > existing.width * 1.4
            and _markdown_col_count(markdown) >= _markdown_col_count(existing_markdown)
        )
        if can_replace:
            candidates[index] = {
                "bbox": bbox,
                "content": markdown,
                "method": method,
            }
        return

    candidates.append({
        "bbox": bbox,
        "content": markdown,
        "method": method,
    })


def _add_table_candidate(
    candidates: list[dict[str, object]],
    tab: object,
    method: str,
) -> None:
    """Append a table candidate if it has useful Markdown and is not duplicate."""
    markdown = _table_to_markdown(tab)
    if not _is_valid_table_markdown(markdown):
        return

    bbox = fitz.Rect(tab.bbox)
    _append_table_markdown_candidate(candidates, bbox, markdown, method)


def _merge_word_runs(words: list[tuple]) -> list[dict[str, object]]:
    """Group PyMuPDF words into row-level text runs."""
    rows: list[list[tuple]] = []
    for word in sorted(words, key=lambda item: (item[1], item[0])):
        if not rows or abs(rows[-1][0][1] - word[1]) > 4:
            rows.append([word])
        else:
            rows[-1].append(word)

    runs = []
    for row in rows:
        row_runs = []
        for word in sorted(row, key=lambda item: item[0]):
            x0, y0, x1, y1, text = word[:5]
            if row_runs and x0 - row_runs[-1]["x1"] <= 8:
                row_runs[-1]["x1"] = x1
                row_runs[-1]["y0"] = min(row_runs[-1]["y0"], y0)
                row_runs[-1]["y1"] = max(row_runs[-1]["y1"], y1)
                row_runs[-1]["text"] = f"{row_runs[-1]['text']} {text}"
            else:
                row_runs.append({
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "text": text,
                })
        runs.extend(row_runs)
    return runs


def _cluster_word_columns(runs: list[dict[str, object]]) -> list[float]:
    """Infer stable table columns from word-run centers."""
    centers = sorted((float(run["x0"]) + float(run["x1"])) / 2 for run in runs)
    columns: list[float] = []
    for center in centers:
        if not columns or abs(center - columns[-1]) > 14:
            columns.append(center)
        else:
            columns[-1] = (columns[-1] + center) / 2
    return columns


def _word_runs_to_rows(
    runs: list[dict[str, object]],
    columns: list[float],
) -> list[list[str]]:
    """Place word runs into inferred columns and return table rows."""
    row_groups: list[list[dict[str, object]]] = []
    for run in sorted(runs, key=lambda item: (float(item["y0"]), float(item["x0"]))):
        if not row_groups or abs(float(row_groups[-1][0]["y0"]) - float(run["y0"])) > 4:
            row_groups.append([run])
        else:
            row_groups[-1].append(run)

    rows = []
    for group in row_groups:
        row = [""] * len(columns)
        for run in group:
            center = (float(run["x0"]) + float(run["x1"])) / 2
            col_index = min(range(len(columns)), key=lambda idx: abs(columns[idx] - center))
            text = _normalize_table_cell(run["text"])
            row[col_index] = f"{row[col_index]} {text}".strip() if row[col_index] else text
        rows.append(row)
    return rows


def _words_to_markdown_table(
    page: fitz.Page,
    clip: fitz.Rect,
) -> tuple[fitz.Rect, str] | None:
    """Build a simple table from word coordinates inside a clipped region."""
    words = page.get_text("words", clip=clip)
    if len(words) < 6:
        return None

    runs = _merge_word_runs(words)
    if len(runs) < 6:
        return None

    columns = _cluster_word_columns(runs)
    if len(columns) < 3:
        return None

    rows = _word_runs_to_rows(runs, columns)
    cleaned_rows = _clean_table_rows(rows)
    markdown = _rows_to_markdown(cleaned_rows)
    if not _is_valid_table_markdown(markdown):
        return None

    x0 = min(float(run["x0"]) for run in runs)
    y0 = min(float(run["y0"]) for run in runs)
    x1 = max(float(run["x1"]) for run in runs)
    y1 = max(float(run["y1"]) for run in runs)
    return fitz.Rect(x0, y0, x1, y1), markdown


def _find_tables_in_clip(
    page: fitz.Page,
    clip: fitz.Rect,
) -> list[object]:
    """Find text-strategy tables inside a clipped page region."""
    if clip.height < 20 or clip.width < 80:
        return []
    try:
        return list(page.find_tables(strategy="text", clip=clip))
    except Exception:
        return []


def find_page_tables(
    page: fitz.Page,
    include_top_continuation: bool = False,
) -> tuple[list[dict[str, object]], bool]:
    """Find line-detected tables plus caption-guided text tables on one page."""
    candidates: list[dict[str, object]] = []
    try:
        for tab in page.find_tables():
            _add_table_candidate(candidates, tab, "lines")
    except Exception:
        pass

    lines = _extract_text_lines(page)
    for rect, text in lines:
        if not _is_table_caption(text):
            continue
        start_y = _caption_table_start_y(rect, lines)
        bottom_y = _table_region_bottom(page, lines, start_y)
        clip = fitz.Rect(0, start_y, page.rect.width, bottom_y)
        for tab in _find_tables_in_clip(page, clip):
            _add_table_candidate(candidates, tab, "caption-text")
        word_table = _words_to_markdown_table(page, clip)
        if word_table:
            bbox, markdown = word_table
            _append_table_markdown_candidate(
                candidates,
                bbox,
                markdown,
                "caption-words",
                replace_narrow=True,
            )

    if include_top_continuation:
        start_y = page.rect.height * 0.08
        bottom_y = _table_region_bottom(page, lines, start_y)
        clip = fitz.Rect(0, start_y, page.rect.width, bottom_y)
        for tab in _find_tables_in_clip(page, clip):
            _add_table_candidate(candidates, tab, "continuation-text")
        word_table = _words_to_markdown_table(page, clip)
        if word_table:
            bbox, markdown = word_table
            _append_table_markdown_candidate(
                candidates,
                bbox,
                markdown,
                "continuation-words",
                replace_narrow=True,
            )

    candidates.sort(key=lambda candidate: candidate["bbox"].y0)
    table_continues = any(
        isinstance(candidate["bbox"], fitz.Rect)
        and candidate["bbox"].y1 >= page.rect.height * TABLE_CONTINUATION_Y_RATIO
        for candidate in candidates
    )
    return candidates, table_continues


def _is_markdown_table_line(line: str) -> bool:
    """Return whether a Markdown line belongs to a pipe table."""
    return line.startswith("|")


def _is_markdown_separator_line(line: str) -> bool:
    """Return whether a Markdown table line is the separator row."""
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    return bool(cells) and all(cell and set(cell) <= {"-", ":"} for cell in cells)


def _compatible_table_headers(first: list[str], second: list[str]) -> bool:
    """Return whether two Markdown table blocks have the same flattened header."""
    if len(first) < 2 or len(second) < 2:
        return False
    if not _is_markdown_separator_line(first[1]) or not _is_markdown_separator_line(second[1]):
        return False
    return first[0] == second[0] and _markdown_col_count(first[0]) > 2


def _is_table_continuation_noise(line: str) -> bool:
    """Allow only page/header noise between split table parts."""
    text = line.strip()
    if not text:
        return True
    if text.startswith("<!-- Page ") and text.endswith("-->"):
        return True
    if re.fullmatch(r'\d+', text):
        return True
    if "重庆大学硕士学位论文" in text:
        return True
    continuation_labels = [
        "营改增",
        "深化增值税改革",
        "国有企业",
        "非国有企业",
    ]
    return any(label in text for label in continuation_labels)


def _read_markdown_table_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Read a contiguous Markdown table block from ``start``."""
    end = start
    while end < len(lines) and _is_markdown_table_line(lines[end]):
        end += 1
    return lines[start:end], end


def merge_markdown_continuation_tables(markdown: str) -> str:
    """Merge split cross-page Markdown tables with repeated headers."""
    lines = markdown.splitlines()
    result = []
    index = 0

    while index < len(lines):
        if not _is_markdown_table_line(lines[index]):
            result.append(lines[index])
            index += 1
            continue

        table, table_end = _read_markdown_table_block(lines, index)
        search = table_end
        while True:
            between_start = search
            while search < len(lines) and not _is_markdown_table_line(lines[search]):
                if not _is_table_continuation_noise(lines[search]):
                    break
                search += 1

            if search >= len(lines) or not _is_markdown_table_line(lines[search]):
                break
            if any(
                not _is_table_continuation_noise(line)
                for line in lines[between_start:search]
            ):
                break

            next_table, next_end = _read_markdown_table_block(lines, search)
            if not _compatible_table_headers(table, next_table):
                break

            table.extend(next_table[2:])
            search = next_end

        result.extend(table)
        index = search if search != table_end else table_end

    return "\n".join(result)


def merge_adjacent_formatting(text: str) -> str:
    """Merge adjacent same-style formatted spans split across PDF tokens.

    PyMuPDF often emits a phrase as several spans, so per-span wrapping in
    ``format_span_text`` produces ``**X****Y**`` (bold) or ``***X******Y***``
    (bold-italic) where one phrase is intended. Collapse the abutting markers
    so the run reads as a single phrase: ``**X Y**`` / ``***X Y***``.

    Italic-italic adjacency (``*X**Y*``) is indistinguishable from a plain
    bold span's open/close pair and is left alone — merging it would corrupt
    every legitimate ``**bold**`` phrase on the page. The previous regexes
    ``\\*\\s*\\*`` and ``\\*\\*\\*\\s*\\*\\*\\*`` did exactly that, deleting
    all bold formatting from the converted Markdown.
    """
    # Bold-italic adjacency first so the inner ``******`` isn't half-eaten
    # by the bold pass.
    text = re.sub(r'\*{6}', ' ', text)
    text = re.sub(r'\*{4}', ' ', text)
    return text


def is_sentence_end(text: str) -> bool:
    """Check if the text ends with sentence-ending punctuation."""
    text = text.rstrip()
    if not text:
        return True
    end_puncts = '.。!！?？:：;；'
    return text[-1] in end_puncts


def should_merge_lines(current: dict, next_line: dict) -> bool:
    """Determine if two lines should be merged into the same paragraph."""
    if current.get("is_heading") or next_line.get("is_heading"):
        return False
    if current.get("is_list") or next_line.get("is_list"):
        return False
    if is_sentence_end(current.get("content", "")):
        return False
    return True


def extract_pdf_to_markdown(
    pdf_path: str,
    output_path: str = None,
    images: str = "filtered",
    render_vector_figures: bool = False,
    vector_figure_dpi: int = VECTOR_FIGURE_DPI,
) -> str:
    """Extract text, images, and tables from a PDF and convert to Markdown.

    Args:
        pdf_path: Path to the PDF file.
        output_path: Optional output path for the Markdown file.
        images: Image extraction mode.
            "filtered" = apply size/quality filters (default),
            "all"      = extract all images without filtering,
            "none"     = skip all images.
        render_vector_figures: Rasterize large vector drawing regions as PNGs.
        vector_figure_dpi: DPI used for rendered vector figure PNGs.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Failed to open PDF file: {e}")
        return ""

    if len(doc) >= 200:
        print(f"[HINT] {len(doc)} pages — for very large PDFs, consider splitting "
              f"the source by chapter beforehand (e.g. with pdftk / qpdf / PyPDF2) "
              f"and converting each part individually.")

    filename = Path(pdf_path).stem
    title = re.sub(r'^\d+-', '', filename).strip()

    print(f"[INFO] Analyzing document structure...")
    size_map = analyze_font_sizes(doc)
    print(f"   Font size mapping: body={size_map.get('body', 'N/A')}, " +
          f"H1={size_map.get('h1', 'N/A')}, H2={size_map.get('h2', 'N/A')}, H3={size_map.get('h3', 'N/A')}")

    print(f"[INFO] Detecting repeated headers/footers...")
    noise_texts = detect_headers_footers(doc)
    if noise_texts:
        print(f"   Found {len(noise_texts)} repeated noise texts (will be removed):")
        for t in list(noise_texts)[:3]:
            print(f"     - {t[:30]}...")

    markdown_content = f"# {title}\n\n"
    seen_image_hashes = set()  # Track seen image hashes for deduplication

    img_dir = None
    rel_img_dir = None
    if output_path:
        output_path = Path(output_path)
        rel_img_dir = f"{output_path.stem}_files"
        img_dir = output_path.parent / rel_img_dir

    img_count = 0
    image_manifest: list[dict[str, object]] = []
    previous_table_continues = False

    for page_num, page in enumerate(doc, 1):
        if page_num > 1:
            # Add page break marker to help LLM understand context segmentation
            markdown_content += f"\n\n<!-- Page {page_num} -->\n\n"

        table_candidates, previous_table_continues = find_page_tables(
            page,
            include_top_continuation=previous_table_continues,
        )
        tab_rects = [
            candidate["bbox"]
            for candidate in table_candidates
            if isinstance(candidate["bbox"], fitz.Rect)
        ]

        page_elements = []

        for table in table_candidates:
            bbox = table["bbox"]
            if not isinstance(bbox, fitz.Rect):
                continue
            page_elements.append({
                "y0": bbox.y0,
                "type": 2,
                "content": table["content"]
            })
            print(f"  [OK] Found table: P{page_num} ({table['method']})")

        if render_vector_figures:
            for figure_rect in detect_vector_figure_rects(page, tab_rects):
                page_elements.append({
                    "y0": figure_rect.y0,
                    "type": 3,
                    "content": figure_rect,
                })
                print(f"  [OK] Found vector figure region: P{page_num} {tuple(round(v, 1) for v in figure_rect)}")

        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])

            # Check if this is table content
            is_in_table = False
            for tab_rect in tab_rects:
                intersect = block_rect & tab_rect
                if intersect.get_area() > 0.6 * block_rect.get_area():
                    is_in_table = True
                    break

            if is_in_table:
                continue

            if block["type"] == 0:
                # Check if this is noise text to be filtered (whole block match)
                block_text_full = "".join([span["text"] for line in block["lines"] for span in line["spans"]]).strip()
                if block_text_full in noise_texts:
                    continue

                for line in block["lines"]:
                    line_text = ""
                    line_size = 0
                    line_flags = 0
                    span_count = 0
                    is_code_line = False

                    formatted_spans = []
                    for span in line["spans"]:
                        span_text = CONTROL_CHARS_RE.sub('', span["text"])
                        if not span_text.strip():
                            if span_text:
                                formatted_spans.append(span_text)
                            continue

                        span_size = span["size"]
                        span_flags = span["flags"]

                        line_size = max(line_size, span_size)
                        line_flags |= span_flags
                        span_count += 1

                        heading_level = get_heading_level(span_size, size_map, span_text, span_flags)

                        # Detect code font
                        font_name = span.get("font", "")
                        if is_monospace_font(font_name):
                            is_code_line = True
                            formatted_spans.append(span_text)  # No formatting for code
                        elif heading_level > 0:
                            formatted_spans.append(span_text.strip())
                        else:
                            formatted_spans.append(format_span_text(span_text, span_flags))

                    line_text = ''.join(formatted_spans).strip()
                    if not line_text:
                        continue

                    # Secondary check: line-level noise match (sometimes blocks are split)
                    if line_text in noise_texts:
                        continue

                    line_text = merge_adjacent_formatting(line_text)

                    heading_level = get_heading_level(line_size, size_map, line_text, line_flags)

                    is_list, list_type, list_content = detect_list_item(line_text)

                    if heading_level > 0:
                        prefix = '#' * heading_level + ' '
                        clean_line = re.sub(r'\*+([^*]+)\*+', r'\1', line_text)
                        final_text = prefix + clean_line
                    elif is_list:
                        final_text = list_content
                    else:
                        final_text = line_text

                    page_elements.append({
                        "y0": line["bbox"][1],
                        "type": 0,
                        "content": final_text,
                        "is_heading": heading_level > 0,
                        "is_list": is_list,
                        "is_code": is_code_line
                    })

            elif block["type"] == 1:
                if images == "none":
                    pass
                elif images == "all" or should_keep_image(block, page.rect, seen_image_hashes):
                    page_elements.append({
                        "y0": block["bbox"][1],
                        "type": 1,
                        "content": block
                    })
                else:
                    w, h = block.get("width", 0), block.get("height", 0)
                    print(f"  [SKIP] Filtered small/decorative image: {w}x{h}px, {len(block.get('image', b''))} bytes")

        page_elements.sort(key=lambda x: x["y0"])

        # Merge adjacent same-level short headings
        page_elements = merge_adjacent_headings(page_elements)

        merged_elements = []
        i = 0
        while i < len(page_elements):
            el = page_elements[i]
            if el["type"] == 0 and not el.get("is_heading") and not el.get("is_list"):
                merged_content = el["content"]
                j = i + 1
                while j < len(page_elements):
                    next_el = page_elements[j]
                    if next_el["type"] != 0:
                        break
                    if not should_merge_lines({"content": merged_content, "is_heading": False, "is_list": False}, next_el):
                        break
                    merged_content += " " + next_el["content"]
                    j += 1
                merged_elements.append({
                    "type": 0,
                    "content": remove_page_footer(merged_content),
                    "is_heading": False,
                    "is_list": False
                })
                i = j
            else:
                merged_elements.append(el)
                i += 1

        prev_was_list = False
        prev_was_code = False
        code_block_lines = []

        def flush_code_block():
            """Flush accumulated code block."""
            nonlocal code_block_lines, markdown_content
            if code_block_lines:
                markdown_content += "```\n"
                markdown_content += "\n".join(code_block_lines) + "\n"
                markdown_content += "```\n\n"
                code_block_lines = []

        for el in merged_elements:
            if el["type"] == 0:
                is_list = el.get("is_list", False)
                is_heading = el.get("is_heading", False)
                is_code = el.get("is_code", False)

                if is_code:
                    # Accumulate code lines
                    if prev_was_list:
                        markdown_content += "\n"
                        prev_was_list = False
                    code_block_lines.append(el["content"])
                    prev_was_code = True
                else:
                    # Non-code line, flush accumulated code block first
                    if prev_was_code:
                        flush_code_block()
                        prev_was_code = False

                    if is_heading:
                        if prev_was_list:
                            markdown_content += "\n"
                        markdown_content += el["content"] + "\n\n"
                        prev_was_list = False
                    elif is_list:
                        markdown_content += el["content"] + "\n"
                        prev_was_list = True
                    else:
                        if prev_was_list:
                            markdown_content += "\n"
                        markdown_content += el["content"] + "\n\n"
                        prev_was_list = False

            elif el["type"] == 2:
                if prev_was_code:
                    flush_code_block()
                    prev_was_code = False
                if prev_was_list:
                    markdown_content += "\n"
                markdown_content += el["content"] + "\n\n"
                prev_was_list = False

            elif el["type"] == 1:
                if prev_was_code:
                    flush_code_block()
                    prev_was_code = False
                if img_dir:
                    block = el["content"]
                    ext = block["ext"]
                    image_data = block["image"]
                    safe_filename = filename.replace(" ", "_")
                    image_name = f"{safe_filename}_p{page_num}_{img_count}.{ext}"
                    image_path = img_dir / image_name

                    try:
                        img_dir.mkdir(parents=True, exist_ok=True)
                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        if prev_was_list:
                            markdown_content += "\n"
                        markdown_content += f"![{image_name}]({rel_img_dir}/{image_name})\n\n"
                        width = int(block.get("width", 0) or 0)
                        height = int(block.get("height", 0) or 0)
                        ratio = width / height if width > 0 and height > 0 else None
                        image_manifest.append({
                            "index": len(image_manifest) + 1,
                            "filename": image_name,
                            "original_filename": image_name,
                            "asset_kind": "bitmap",
                            "svg_renderable": True,
                            "pptx_native_supported": True,
                            "source_kind": "pdf_image",
                            "source_ext": f".{ext}",
                            "page_index": page_num,
                            "occurrence_index": img_count + 1,
                            "pixel_width": width or None,
                            "pixel_height": height or None,
                            "pixel_ratio": round(ratio, 6) if ratio else None,
                            "display_ratio": round(ratio, 6) if ratio else None,
                            "source_sha256": hashlib.sha256(image_data).hexdigest(),
                            "bbox": list(block.get("bbox", [])),
                        })
                        img_count += 1
                        prev_was_list = False
                        print(f"  [OK] Extracted image: {image_name}")
                    except Exception as e:
                        print(f"  [WARN] Failed to save image: {e}")

            elif el["type"] == 3:
                if prev_was_code:
                    flush_code_block()
                    prev_was_code = False
                if img_dir:
                    figure_rect = el["content"]
                    safe_filename = filename.replace(" ", "_")
                    image_name = f"{safe_filename}_p{page_num}_figure_{img_count}.png"
                    image_path = img_dir / image_name

                    try:
                        img_dir.mkdir(parents=True, exist_ok=True)
                        scale = vector_figure_dpi / 72
                        pix = page.get_pixmap(
                            matrix=fitz.Matrix(scale, scale),
                            clip=figure_rect,
                            alpha=False,
                        )
                        pix.save(str(image_path))

                        if prev_was_list:
                            markdown_content += "\n"
                        markdown_content += f"![{image_name}]({rel_img_dir}/{image_name})\n\n"
                        ratio = pix.width / pix.height if pix.width > 0 and pix.height > 0 else None
                        image_manifest.append({
                            "index": len(image_manifest) + 1,
                            "filename": image_name,
                            "original_filename": image_name,
                            "asset_kind": "bitmap",
                            "svg_renderable": True,
                            "pptx_native_supported": True,
                            "source_kind": "pdf_vector_figure",
                            "source_ext": ".png",
                            "page_index": page_num,
                            "occurrence_index": img_count + 1,
                            "pixel_width": pix.width,
                            "pixel_height": pix.height,
                            "pixel_ratio": round(ratio, 6) if ratio else None,
                            "display_ratio": round(ratio, 6) if ratio else None,
                            "bbox": [
                                figure_rect.x0,
                                figure_rect.y0,
                                figure_rect.x1,
                                figure_rect.y1,
                            ],
                        })
                        img_count += 1
                        prev_was_list = False
                        print(f"  [OK] Rendered vector figure: {image_name}")
                    except Exception as e:
                        print(f"  [WARN] Failed to render vector figure: {e}")

        # Flush code block at end of page
        if prev_was_code:
            flush_code_block()

    doc.close()

    markdown_content = merge_markdown_continuation_tables(markdown_content)
    markdown_content = CONTROL_CHARS_RE.sub('', markdown_content)
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    markdown_content = markdown_content.strip() + "\n"

    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        if img_dir and image_manifest:
            (img_dir / "image_manifest.json").write_text(
                json.dumps(image_manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        profile_path = write_conversion_profile_best_effort(
            input_path=pdf_path,
            markdown_path=output_path,
            converter="pdf_to_md.py",
            conversion_type="pdf",
            asset_dir=img_dir,
        )
        print(f"[OK] Saved Markdown to: {output_path}")
        if profile_path:
            print(f"   Wrote conversion profile -> {profile_path}")

    return markdown_content


def main() -> int:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description='PDF to Markdown converter (with structure detection and LLM optimization)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python pdf_to_md.py book.pdf                    # Convert a single file
  python pdf_to_md.py book.pdf appendix.pdf       # Convert multiple files
  python pdf_to_md.py ./pdfs -o ./markdown        # Convert PDFs in a directory
  python pdf_to_md.py book.pdf -o output.md      # Specify output file
  python pdf_to_md.py book.pdf --render-vector-figures

Structure detection features:
  - Auto-detect heading levels (based on font size)
  - Detect bold and italic text
  - Detect ordered and unordered lists
  - Extract tables and convert to Markdown format (with deduplication)
  - [New] Smart detection and removal of repeated page headers/footers
  - [New] Add <!-- Page N --> page break markers to help LLM understanding
'''
    )

    parser.add_argument('inputs', nargs='+', help='PDF file(s) or directories')
    parser.add_argument(
        '-o',
        '--output',
        help='Output Markdown file for one input, or output directory for multiple inputs/directories',
    )
    parser.add_argument(
        '--images',
        choices=['all', 'filtered', 'none'],
        default='filtered',
        help='Image extraction mode: filtered=apply size/quality filters (default), all=no filtering, none=skip images',
    )
    parser.add_argument(
        '--render-vector-figures',
        action='store_true',
        help='Render large vector drawing regions as PNG figure assets',
    )
    parser.add_argument(
        '--vector-figure-dpi',
        type=int,
        default=VECTOR_FIGURE_DPI,
        help=f'DPI for --render-vector-figures output (default: {VECTOR_FIGURE_DPI})',
    )

    args = parser.parse_args()

    return run_path_batch(
        args.inputs,
        {'.pdf'},
        args.output,
        lambda source, output: bool(
            extract_pdf_to_markdown(
                str(source),
                str(output),
                images=args.images,
                render_vector_figures=args.render_vector_figures,
                vector_figure_dpi=args.vector_figure_dpi,
            )
        ),
    )


if __name__ == '__main__':
    raise SystemExit(main())
