"""Placeholder tagger — assign `{{PLACEHOLDER}}` tags to text-bearing shapes.

Two-tier strategy (per plan):

  Tier A (canonical): when a shape carries a PPT placeholder marker (<p:ph>),
      map by (ph_type, ph_idx) + page_type context. These tags are high-confidence
      because the source PPT author explicitly marked them.

  Tier B (heuristic): when no p:ph is present (common in 'finished document'
      PPTXs), infer tags from font-size ordering, y-position, and text content.
      These tags are lower-confidence and are logged for user review.

Each tagged shape gets:
    shape.placeholder_tag = '{{TITLE}}'  (etc.)

Untagged shapes keep their original text — downstream consumers may choose to
preserve them as visual hints or replace them with generic filler.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from .ir import Shape, SlideBlueprint


PageType = Literal['cover', 'toc', 'chapter', 'content', 'ending', 'unknown']


# ---------------------------------------------------------------------------
# Regex patterns for heuristic detection
# ---------------------------------------------------------------------------

_DATE_PATTERNS = [
    re.compile(r'\b\d{4}[-./年]\d{1,2}[-./月]?\d{0,2}日?'),
    re.compile(r'\b(19|20|21)\d{2}\b'),                      # lone year (e.g., "2026")
    re.compile(r'\b\d{1,2}[-./]\d{1,2}[-./]\d{2,4}\b'),
]

_EMAIL_PATTERN = re.compile(r'[\w.-]+@[\w.-]+\.\w+')
_PHONE_PATTERN = re.compile(r'(\+?\d[\d\s\-]{7,}\d)')
_URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)

_CHAPTER_NUM_PATTERN = re.compile(
    r'(?:第\s*[一二三四五六七八九十\d]+\s*[章节篇部分]|'
    r'(?:chapter|part|section)\s*[\dIVXLCMivxlcm]+)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Tagging report (for user review / design_spec metadata)
# ---------------------------------------------------------------------------

@dataclass
class TagRecord:
    """Provenance record for one placeholder assignment."""
    slide_index: int
    shape_source_name: str | None
    tag: str
    tier: Literal['A', 'B']  # A = canonical p:ph, B = heuristic
    rule: str  # e.g. 'ph_type=title', 'largest_font_cover', 'regex_date'
    original_text: str


# ---------------------------------------------------------------------------
# Tier A: canonical p:ph -> placeholder
# ---------------------------------------------------------------------------

def _tier_a_tag(shape: Shape, page_type: PageType) -> str | None:
    """Map a shape's <p:ph> metadata to a placeholder tag, or None if not applicable."""
    if shape.ph_type is None:
        return None

    pt = shape.ph_type

    if pt == 'ctrTitle':
        return '{{TITLE}}' if page_type in ('cover', 'ending') else '{{PAGE_TITLE}}'

    if pt == 'title':
        if page_type == 'cover':
            return '{{TITLE}}'
        if page_type == 'chapter':
            return '{{CHAPTER_TITLE}}'
        if page_type == 'ending':
            return '{{THANK_YOU}}'
        return '{{PAGE_TITLE}}'

    if pt == 'subTitle':
        return '{{SUBTITLE}}'

    if pt == 'body':
        idx = shape.ph_idx or 0
        return f'{{{{BODY_{idx + 1}}}}}'

    if pt == 'pic':
        idx = shape.ph_idx or 0
        return f'{{{{IMAGE_{idx + 1}}}}}'

    if pt == 'dt':
        return '{{DATE}}'
    if pt == 'sldNum':
        return '{{PAGE_NUM}}'
    if pt == 'ftr':
        return '{{FOOTER}}'
    if pt == 'hdr':
        return '{{HEADER}}'

    return None


# ---------------------------------------------------------------------------
# Tier B: heuristic inference
# ---------------------------------------------------------------------------

def _shape_dominant_font_size(shape: Shape) -> float:
    """Return the largest font_size among the shape's runs (0 if none)."""
    if shape.text is None:
        return 0.0
    best = 0.0
    for p in shape.text.paragraphs:
        for r in p.runs:
            if r.font_size and r.font_size > best:
                best = r.font_size
    return best


def _shape_full_text(shape: Shape) -> str:
    """Concatenate all run texts with single spaces between runs."""
    if shape.text is None:
        return ''
    parts: list[str] = []
    for p in shape.text.paragraphs:
        line = ''.join(r.text for r in p.runs)
        if line.strip():
            parts.append(line)
    return ' '.join(parts)


def _collect_text_shapes(shapes: list[Shape]) -> list[Shape]:
    """Flat list of every shape in the tree that carries a non-empty text body."""
    out: list[Shape] = []
    for s in shapes:
        if s.text is not None and _shape_full_text(s).strip():
            out.append(s)
        if s.children:
            out.extend(_collect_text_shapes(s.children))
    return out


def _tier_b_cover(
    slide_bp: SlideBlueprint,
    report: list[TagRecord],
) -> None:
    """Cover slide: largest font -> TITLE, second -> SUBTITLE, date regex -> DATE."""
    text_shapes = _collect_text_shapes(slide_bp.shapes)
    if not text_shapes:
        return

    # Sort by dominant font size (descending)
    ordered = sorted(text_shapes, key=_shape_dominant_font_size, reverse=True)

    title_shape: Shape | None = None
    subtitle_shape: Shape | None = None

    for s in ordered:
        fs = _shape_dominant_font_size(s)
        if fs <= 0:
            continue
        if title_shape is None:
            title_shape = s
        elif subtitle_shape is None and fs < _shape_dominant_font_size(title_shape):
            subtitle_shape = s
            break

    if title_shape is not None and title_shape.placeholder_tag is None:
        title_shape.placeholder_tag = '{{TITLE}}'
        report.append(TagRecord(
            slide_index=slide_bp.index,
            shape_source_name=title_shape.source_name,
            tag='{{TITLE}}', tier='B', rule='largest_font_cover',
            original_text=_shape_full_text(title_shape)[:60],
        ))

    if subtitle_shape is not None and subtitle_shape.placeholder_tag is None:
        subtitle_shape.placeholder_tag = '{{SUBTITLE}}'
        report.append(TagRecord(
            slide_index=slide_bp.index,
            shape_source_name=subtitle_shape.source_name,
            tag='{{SUBTITLE}}', tier='B', rule='second_largest_font',
            original_text=_shape_full_text(subtitle_shape)[:60],
        ))

    # Date detection
    for s in text_shapes:
        if s.placeholder_tag is not None:
            continue
        text = _shape_full_text(s)
        if any(p.search(text) for p in _DATE_PATTERNS):
            s.placeholder_tag = '{{DATE}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=s.source_name,
                tag='{{DATE}}', tier='B', rule='regex_date',
                original_text=text[:60],
            ))
            break


def _tier_b_chapter(
    slide_bp: SlideBlueprint,
    report: list[TagRecord],
) -> None:
    """Chapter page: 'Part N / 第N章' -> CHAPTER_NUM, largest centered text -> CHAPTER_TITLE."""
    text_shapes = _collect_text_shapes(slide_bp.shapes)
    if not text_shapes:
        return

    # Chapter number regex first (higher confidence)
    for s in text_shapes:
        if s.placeholder_tag is not None:
            continue
        text = _shape_full_text(s)
        if _CHAPTER_NUM_PATTERN.search(text):
            s.placeholder_tag = '{{CHAPTER_NUM}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=s.source_name,
                tag='{{CHAPTER_NUM}}', tier='B', rule='regex_chapter_num',
                original_text=text[:60],
            ))

    # Chapter title: largest remaining text
    ordered = sorted(text_shapes, key=_shape_dominant_font_size, reverse=True)
    for s in ordered:
        if s.placeholder_tag is None and _shape_dominant_font_size(s) > 0:
            s.placeholder_tag = '{{CHAPTER_TITLE}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=s.source_name,
                tag='{{CHAPTER_TITLE}}', tier='B', rule='largest_font_chapter',
                original_text=_shape_full_text(s)[:60],
            ))
            break


def _tier_b_toc(
    slide_bp: SlideBlueprint,
    report: list[TagRecord],
) -> None:
    """TOC page: list-like items (similar bbox width, vertically stacked) -> TOC_ITEM_N."""
    text_shapes = _collect_text_shapes(slide_bp.shapes)
    if not text_shapes:
        return

    # Heading (largest or containing keyword)
    ordered = sorted(text_shapes, key=_shape_dominant_font_size, reverse=True)
    if ordered and ordered[0].placeholder_tag is None:
        first = ordered[0]
        first.placeholder_tag = '{{PAGE_TITLE}}'
        report.append(TagRecord(
            slide_index=slide_bp.index,
            shape_source_name=first.source_name,
            tag='{{PAGE_TITLE}}', tier='B', rule='toc_heading',
            original_text=_shape_full_text(first)[:60],
        ))

    # Remaining ordered by y (top to bottom) become TOC items
    remaining = [s for s in text_shapes if s.placeholder_tag is None]
    remaining.sort(key=lambda s: s.bbox[1])
    for i, s in enumerate(remaining, 1):
        s.placeholder_tag = f'{{{{TOC_ITEM_{i}_TITLE}}}}'
        report.append(TagRecord(
            slide_index=slide_bp.index,
            shape_source_name=s.source_name,
            tag=s.placeholder_tag, tier='B', rule='toc_item_by_y',
            original_text=_shape_full_text(s)[:60],
        ))


def _tier_b_content(
    slide_bp: SlideBlueprint,
    report: list[TagRecord],
) -> None:
    """Content page: top-most large text -> PAGE_TITLE; columnar groups -> CARD_N_*."""
    _, vh = slide_bp.viewbox
    top_zone = vh * 0.25  # top quarter

    text_shapes = _collect_text_shapes(slide_bp.shapes)
    if not text_shapes:
        return

    # PAGE_TITLE: largest font in the top quarter
    in_top = [s for s in text_shapes if s.bbox[1] < top_zone]
    if in_top:
        title = max(in_top, key=_shape_dominant_font_size)
        if _shape_dominant_font_size(title) >= 20.0 and title.placeholder_tag is None:
            title.placeholder_tag = '{{PAGE_TITLE}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=title.source_name,
                tag='{{PAGE_TITLE}}', tier='B', rule='top_zone_largest',
                original_text=_shape_full_text(title)[:60],
            ))

    # CARD_N_*: group remaining text by column (3 bands: left/center/right)
    vw, _ = slide_bp.viewbox
    band_w = vw / 3.0
    bands: list[list[Shape]] = [[], [], []]
    for s in text_shapes:
        if s.placeholder_tag is not None:
            continue
        cx = s.bbox[0] + s.bbox[2] / 2.0
        idx = min(int(cx / band_w), 2)
        bands[idx].append(s)

    # Only treat as cards if all three bands are populated (>=1 each)
    if all(len(b) >= 1 for b in bands):
        for col_idx, band in enumerate(bands, 1):
            band.sort(key=lambda s: s.bbox[1])
            # First in each column -> CARD_N_TITLE, subsequent -> CARD_N_LINE_M
            for row_idx, s in enumerate(band):
                if row_idx == 0:
                    tag = f'{{{{CARD_{col_idx}_TITLE}}}}'
                else:
                    tag = f'{{{{CARD_{col_idx}_LINE_{row_idx}}}}}'
                s.placeholder_tag = tag
                report.append(TagRecord(
                    slide_index=slide_bp.index,
                    shape_source_name=s.source_name,
                    tag=tag, tier='B', rule='three_column_card',
                    original_text=_shape_full_text(s)[:60],
                ))


def _tier_b_ending(
    slide_bp: SlideBlueprint,
    report: list[TagRecord],
) -> None:
    """Ending page: 谢谢/Thank -> THANK_YOU; email/phone -> CONTACT_INFO."""
    text_shapes = _collect_text_shapes(slide_bp.shapes)
    thanks_keywords = ('谢谢', '感谢', '致谢', 'thank', 'thanks', 'q&a', 'qa')

    for s in text_shapes:
        if s.placeholder_tag is not None:
            continue
        text = _shape_full_text(s)
        lower = text.lower()
        if any(k in lower for k in thanks_keywords):
            s.placeholder_tag = '{{THANK_YOU}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=s.source_name,
                tag='{{THANK_YOU}}', tier='B', rule='ending_keyword',
                original_text=text[:60],
            ))
            continue
        if (_EMAIL_PATTERN.search(text) or _PHONE_PATTERN.search(text)
                or _URL_PATTERN.search(text)):
            s.placeholder_tag = '{{CONTACT_INFO}}'
            report.append(TagRecord(
                slide_index=slide_bp.index,
                shape_source_name=s.source_name,
                tag='{{CONTACT_INFO}}', tier='B', rule='regex_contact',
                original_text=text[:60],
            ))


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

_TIER_B_DISPATCH = {
    'cover': _tier_b_cover,
    'chapter': _tier_b_chapter,
    'toc': _tier_b_toc,
    'content': _tier_b_content,
    'ending': _tier_b_ending,
}


def tag_slide(
    slide_bp: SlideBlueprint,
    report: list[TagRecord] | None = None,
) -> list[TagRecord]:
    """Tag every text-bearing shape in a slide with a placeholder, in place.

    Uses the slide's page_type (set by page_classifier.compute_fingerprint)
    to pick the right Tier B heuristic bundle.
    """
    if report is None:
        report = []

    def _walk_tier_a(shapes: list[Shape]) -> None:
        for s in shapes:
            if s.placeholder_tag is None:
                tag = _tier_a_tag(s, slide_bp.page_type)
                if tag:
                    s.placeholder_tag = tag
                    report.append(TagRecord(
                        slide_index=slide_bp.index,
                        shape_source_name=s.source_name,
                        tag=tag, tier='A',
                        rule=f'ph_type={s.ph_type}_idx={s.ph_idx}',
                        original_text=_shape_full_text(s)[:60],
                    ))
            if s.children:
                _walk_tier_a(s.children)

    _walk_tier_a(slide_bp.shapes)

    # Tier B for shapes still unlabelled
    heuristic = _TIER_B_DISPATCH.get(slide_bp.page_type)
    if heuristic is not None:
        heuristic(slide_bp, report)

    return report


def tag_representative_slides(
    representatives,  # list[ClusterResult] from page_classifier
) -> list[TagRecord]:
    """Tag all representatives emitted by cluster_and_select().

    Returns a flat tag report aggregated across all representatives.
    """
    full_report: list[TagRecord] = []
    for r in representatives:
        tag_slide(r.slide, full_report)
    return full_report
