"""Semantic page-type classification + layout-fingerprint clustering.

Three-step pipeline for converting a Blueprint's slides into a set of
deduplicated representative layouts:

    1. classify_page_type(slide)  -> 'cover' | 'toc' | 'chapter' | 'content' | 'ending'
    2. compute_fingerprint(slide) -> LayoutFingerprint (structural features)
    3. cluster_and_select(slides) -> list of (filename, SlideBlueprint) for emit

The cluster step groups slides whose fingerprints are close enough that they
would produce redundant templates. Each cluster surfaces one representative
slide — the one whose shape count is nearest the cluster median.

Output count is neither fixed nor bounded to a preset 5; source PPTXs with
richer layouts yield more SVGs (capped by `max_layouts`, default 12).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Literal

from .ir import Shape, SlideBlueprint


# ---------------------------------------------------------------------------
# Page type classification (keyword-driven, mirrors template_import/manifest)
# ---------------------------------------------------------------------------

_THANKS_KEYWORDS = (
    "thank", "thanks", "q&a", "qa", "contact",
    "致谢", "谢谢", "感谢", "答疑", "联系方式",
)
_TOC_KEYWORDS = (
    "agenda", "contents", "content", "outline",
    "目录", "议程", "目录页",
)
_CHAPTER_KEYWORDS = (
    "chapter", "part", "section",
    "章节", "部分",
)

PageType = Literal['cover', 'toc', 'chapter', 'content', 'ending', 'unknown']


def classify_page_type(
    slide_bp: SlideBlueprint,
    total_slides: int,
) -> PageType:
    """Infer the semantic page role from text content and positional hints.

    Decision order (first match wins):
        ending   — keywords match (谢谢/Q&A/...)
        toc      — keywords match
        chapter  — keywords match, OR (few texts + few shapes + mid-deck)
        cover    — first slide with <= 3 images
        ending   — last slide with <= 6 text runs (fallback)
        content  — default
    """
    texts = slide_bp.text_samples
    joined = " ".join(texts).lower()

    image_count = _count_shapes_of(slide_bp.shapes, 'image')
    shape_count = _total_shape_count(slide_bp.shapes)
    text_count = len(texts)

    if any(k in joined for k in _THANKS_KEYWORDS):
        return 'ending'
    if any(k in joined for k in _TOC_KEYWORDS):
        return 'toc'
    if any(k in joined for k in _CHAPTER_KEYWORDS):
        return 'chapter'

    if slide_bp.index == 1 and image_count <= 3:
        return 'cover'
    if slide_bp.index == total_slides and text_count <= 6:
        return 'ending'
    if text_count <= 3 and shape_count <= 12:
        return 'chapter'

    return 'content'


def _count_shapes_of(shapes: list[Shape], kind: str) -> int:
    count = 0
    for s in shapes:
        if s.kind == kind:
            count += 1
        if s.children:
            count += _count_shapes_of(s.children, kind)
    return count


def _total_shape_count(shapes: list[Shape]) -> int:
    count = len(shapes)
    for s in shapes:
        if s.children:
            count += _total_shape_count(s.children)
    return count


# ---------------------------------------------------------------------------
# Layout fingerprint
# ---------------------------------------------------------------------------

ShapeCountBucket = Literal['few', 'medium', 'many']
ColumnCount = Literal[1, 2, 3, 4]  # 4 = 4+
ThemeBrightness = Literal['light', 'dark']


@dataclass
class LayoutFingerprint:
    """Compact representation of a slide's layout structure."""
    page_type: PageType
    shape_bucket: ShapeCountBucket
    text_count: int
    image_count: int
    column_count: ColumnCount
    has_large_title: bool  # any shape with font_size >= 28pt in top half
    brightness: ThemeBrightness


def _bucketize_shape_count(n: int) -> ShapeCountBucket:
    if n < 5:
        return 'few'
    if n <= 15:
        return 'medium'
    return 'many'


def _infer_column_count(slide_bp: SlideBlueprint) -> ColumnCount:
    """Estimate column count from shape x-center distribution.

    Splits the viewBox into 4 vertical bands; a column is 'significant' if at
    least 2 shapes have their x-center in it. Returns the number of
    significant bands, clamped to 1..4.
    """
    vw, _ = slide_bp.viewbox
    bands = [0, 0, 0, 0]
    band_w = vw / 4.0

    def _walk(shapes: list[Shape]) -> None:
        for s in shapes:
            x, y, w, h = s.bbox
            # Skip tiny/decorative shapes and full-width backgrounds
            if w <= 0 or h <= 0 or w >= vw * 0.8:
                _walk(s.children)
                continue
            if s.kind in ('line', 'group'):
                _walk(s.children)
                continue
            cx = x + w / 2.0
            idx = min(int(cx / band_w), 3)
            bands[idx] += 1
            _walk(s.children)

    _walk(slide_bp.shapes)

    significant = sum(1 for b in bands if b >= 2)
    return max(1, min(significant, 4))  # type: ignore[return-value]


def _has_large_title(slide_bp: SlideBlueprint) -> bool:
    """True when any shape in the top half has a run with font_size >= 28 pt."""
    _, vh = slide_bp.viewbox
    top_half = vh / 2.0

    def _walk(shapes: list[Shape]) -> bool:
        for s in shapes:
            if s.bbox[1] < top_half and s.text:
                for p in s.text.paragraphs:
                    for r in p.runs:
                        if r.font_size and r.font_size >= 28.0:
                            return True
            if s.children and _walk(s.children):
                return True
        return False

    return _walk(slide_bp.shapes)


def _infer_brightness(slide_bp: SlideBlueprint) -> ThemeBrightness:
    """Classify the slide as 'dark' or 'light' based on background fill."""
    bg = slide_bp.background
    if bg is None or bg.fill is None:
        return 'light'

    if bg.fill.kind == 'solid':
        return 'dark' if _hex_is_dark(bg.fill.color) else 'light'

    if bg.fill.kind == 'gradient' and bg.fill.gradient and bg.fill.gradient.stops:
        avg_L = 0.0
        for stop in bg.fill.gradient.stops:
            avg_L += _hex_luminance(stop.color)
        avg_L /= len(bg.fill.gradient.stops)
        return 'dark' if avg_L < 0.5 else 'light'

    return 'light'


def _hex_luminance(hex_color: str | None) -> float:
    if not hex_color or len(hex_color) < 6:
        return 1.0
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
    except ValueError:
        return 1.0
    # Standard relative luminance (simplified — no gamma)
    return 0.299 * r + 0.587 * g + 0.114 * b


def _hex_is_dark(hex_color: str | None) -> bool:
    return _hex_luminance(hex_color) < 0.5


def compute_fingerprint(
    slide_bp: SlideBlueprint,
    total_slides: int,
) -> LayoutFingerprint:
    """Compute the layout fingerprint for a slide."""
    page_type = classify_page_type(slide_bp, total_slides)
    shape_count = _total_shape_count(slide_bp.shapes)
    text_count = _count_shapes_of(slide_bp.shapes, 'text') + sum(
        1 for s in _iter_all(slide_bp.shapes) if s.text is not None
    )
    image_count = _count_shapes_of(slide_bp.shapes, 'image')
    column_count = _infer_column_count(slide_bp)
    large_title = _has_large_title(slide_bp)
    brightness = _infer_brightness(slide_bp)

    fp = LayoutFingerprint(
        page_type=page_type,
        shape_bucket=_bucketize_shape_count(shape_count),
        text_count=text_count,
        image_count=image_count,
        column_count=column_count,
        has_large_title=large_title,
        brightness=brightness,
    )
    # Attach back to slide_bp for downstream use (design_spec etc.)
    slide_bp.page_type = page_type
    slide_bp.fingerprint = {
        'page_type': page_type,
        'shape_bucket': fp.shape_bucket,
        'text_count': fp.text_count,
        'image_count': fp.image_count,
        'column_count': fp.column_count,
        'has_large_title': fp.has_large_title,
        'brightness': fp.brightness,
    }
    return fp


def _iter_all(shapes: list[Shape]):
    for s in shapes:
        yield s
        if s.children:
            yield from _iter_all(s.children)


# ---------------------------------------------------------------------------
# Clustering (distance-threshold hierarchical)
# ---------------------------------------------------------------------------

def _fingerprint_distance(a: LayoutFingerprint, b: LayoutFingerprint) -> float:
    """Weighted distance between two fingerprints.

    page_type difference hard-separates (distance >> threshold), so different
    semantic roles never merge.
    """
    if a.page_type != b.page_type:
        return 1000.0

    d = 0.0
    if a.shape_bucket != b.shape_bucket:
        d += 5.0
    if a.column_count != b.column_count:
        d += 4.0
    if a.brightness != b.brightness:
        d += 4.0
    if a.has_large_title != b.has_large_title:
        d += 2.0

    # Relative text/image count differences
    def _rel_diff(x: int, y: int) -> float:
        if x == 0 and y == 0:
            return 0.0
        m = max(x, y)
        return abs(x - y) / m

    if _rel_diff(a.text_count, b.text_count) > 0.5:
        d += 2.0
    if _rel_diff(a.image_count, b.image_count) > 0.5:
        d += 2.0

    return d


def _cluster_fingerprints(
    fingerprints: list[LayoutFingerprint],
    threshold: float = 6.0,
) -> list[int]:
    """Agglomerative single-linkage clustering with distance threshold.

    Returns a list of cluster ids (one per input).
    """
    n = len(fingerprints)
    if n == 0:
        return []

    cluster_ids: list[int] = [-1] * n
    next_id = 0

    for i, fp in enumerate(fingerprints):
        if cluster_ids[i] != -1:
            continue
        cluster_ids[i] = next_id
        # Assign every later slide within threshold to this cluster
        for j in range(i + 1, n):
            if cluster_ids[j] != -1:
                continue
            if _fingerprint_distance(fp, fingerprints[j]) < threshold:
                cluster_ids[j] = next_id
        next_id += 1

    return cluster_ids


def _enforce_max_layouts(
    cluster_ids: list[int],
    fingerprints: list[LayoutFingerprint],
    max_layouts: int,
) -> list[int]:
    """Merge smallest clusters into nearest neighbors until count <= max_layouts."""
    from collections import Counter

    while True:
        counts = Counter(cluster_ids)
        if len(counts) <= max_layouts:
            return cluster_ids

        # Pick the smallest cluster
        smallest_id, _ = min(counts.items(), key=lambda kv: (kv[1], kv[0]))

        # Pick a representative fp of the smallest cluster
        small_fp = next(
            fingerprints[i] for i, cid in enumerate(cluster_ids) if cid == smallest_id
        )

        # Find the nearest non-smallest cluster (must share page_type)
        best_target = None
        best_dist = float('inf')
        for other_id in counts:
            if other_id == smallest_id:
                continue
            other_fp = next(
                fingerprints[i] for i, cid in enumerate(cluster_ids) if cid == other_id
            )
            d = _fingerprint_distance(small_fp, other_fp)
            if d < best_dist:
                best_dist = d
                best_target = other_id

        if best_target is None:
            # No merge candidate (all different page_types) — stop
            return cluster_ids

        # Merge smallest into best_target
        cluster_ids = [best_target if cid == smallest_id else cid for cid in cluster_ids]


# ---------------------------------------------------------------------------
# Representative selection
# ---------------------------------------------------------------------------

def _select_representative(
    cluster_members: list[SlideBlueprint],
) -> SlideBlueprint:
    """From a cluster of slides, pick the one whose shape count is nearest the median.

    If the cluster has only one member, that's the pick.
    """
    if len(cluster_members) == 1:
        return cluster_members[0]

    counts = [_total_shape_count(s.shapes) for s in cluster_members]
    med = median(counts)
    best_idx = 0
    best_delta = float('inf')
    for i, c in enumerate(counts):
        delta = abs(c - med)
        if delta < best_delta:
            best_delta = delta
            best_idx = i
    return cluster_members[best_idx]


# ---------------------------------------------------------------------------
# Filename generation
# ---------------------------------------------------------------------------

def _variant_hint(fp: LayoutFingerprint) -> str:
    """Produce a short variant tag describing distinctive features."""
    hints: list[str] = []
    if fp.page_type == 'content':
        if fp.column_count == 2:
            hints.append('2col')
        elif fp.column_count == 3:
            hints.append('3col')
        elif fp.column_count >= 4:
            hints.append('grid')
        elif fp.shape_bucket == 'few':
            hints.append('simple')

    if fp.brightness == 'dark':
        hints.append('dark')

    return '_'.join(hints)


def _build_filename(
    fp: LayoutFingerprint,
    suffix_counter: dict[str, int],
) -> str:
    """Build `<semantic>[_<variant>][_v<N>].svg`, deduplicated via counter."""
    base = fp.page_type if fp.page_type != 'unknown' else 'layout'
    variant = _variant_hint(fp)

    name = f"{base}_{variant}" if variant else base
    suffix_counter[name] = suffix_counter.get(name, 0) + 1
    if suffix_counter[name] > 1:
        name = f"{name}_v{suffix_counter[name]}"
    return f"{name}.svg"


# ---------------------------------------------------------------------------
# Public entry: classify + cluster + select representatives
# ---------------------------------------------------------------------------

@dataclass
class ClusterResult:
    """Output of cluster_and_select: one row per representative slide."""
    filename: str
    slide: SlideBlueprint
    fingerprint: LayoutFingerprint
    member_count: int
    member_indices: list[int]  # 1-based slide indices in the cluster


def cluster_and_select(
    slides: list[SlideBlueprint],
    max_layouts: int = 12,
    distance_threshold: float = 6.0,
) -> list[ClusterResult]:
    """Classify -> fingerprint -> cluster -> choose representatives.

    Args:
        slides: All slides from a Blueprint, in source order.
        max_layouts: Hard upper bound on the number of representatives emitted.
        distance_threshold: Fingerprint distance below which slides merge into
            the same cluster. Lower = more clusters, finer variants.

    Returns:
        One ClusterResult per cluster (non-empty clusters only), ordered by
        a stable semantic sequence: cover, toc, chapter, content, ending, unknown.
    """
    if not slides:
        return []

    total = len(slides)
    fingerprints = [compute_fingerprint(s, total) for s in slides]

    cluster_ids = _cluster_fingerprints(fingerprints, threshold=distance_threshold)
    cluster_ids = _enforce_max_layouts(cluster_ids, fingerprints, max_layouts)

    from collections import defaultdict
    members: dict[int, list[int]] = defaultdict(list)
    for i, cid in enumerate(cluster_ids):
        members[cid].append(i)

    # Build one result per cluster
    results: list[tuple[PageType, ClusterResult]] = []
    suffix_counter: dict[str, int] = {}

    # Order cluster ids so filename assignment is stable per semantic group
    order_key = {'cover': 0, 'toc': 1, 'chapter': 2, 'content': 3, 'ending': 4, 'unknown': 5}
    ordered_cluster_ids = sorted(
        members.keys(),
        key=lambda cid: (
            order_key.get(fingerprints[members[cid][0]].page_type, 99),
            slides[members[cid][0]].index,  # earlier source slide ~ primary variant
        ),
    )

    for cid in ordered_cluster_ids:
        member_slide_idxs = members[cid]
        cluster_slides = [slides[i] for i in member_slide_idxs]
        rep = _select_representative(cluster_slides)
        # Use the representative's own fingerprint for naming
        rep_local_idx = slides.index(rep)
        rep_fp = fingerprints[rep_local_idx]

        filename = _build_filename(rep_fp, suffix_counter)
        results.append(
            (rep_fp.page_type, ClusterResult(
                filename=filename,
                slide=rep,
                fingerprint=rep_fp,
                member_count=len(cluster_slides),
                member_indices=[slides[i].index for i in member_slide_idxs],
            ))
        )

    # Final flat list, ordering already baked in by ordered_cluster_ids
    return [r for _, r in results]
