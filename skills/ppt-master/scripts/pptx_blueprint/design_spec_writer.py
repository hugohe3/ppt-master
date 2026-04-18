"""design_spec.md generator — composes the human-readable design spec for a
layouts/<name>/ template pack from a Blueprint + cluster results + tag report.

The output follows the section structure of design_spec_reference.md, but
fills every knowable field automatically:

    I.   Template overview          (auto: name + source pptx + date)
    II.  Canvas spec                (auto: viewBox + dimensions)
    III. Color scheme               (auto: theme.colors mapped to named roles)
    IV.  Typography                 (auto: theme.fonts + detected size samples)
    V.   Page structure             (auto: list of cluster results with hints)
    VI.  Placeholder catalog        (auto: unique tags from the TagRecord list)
    VII. Technical constraints      (fixed: shared-standards text)
    VIII.Content outline            (left empty for Strategist)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from .ir import Blueprint, Shape, SlideBlueprint
from .page_classifier import ClusterResult, LayoutFingerprint
from .placeholder_tagger import TagRecord


# ---------------------------------------------------------------------------
# Color scheme: classify accent1..6 into semantic roles by luminance
# ---------------------------------------------------------------------------

def _color_role_rows(theme_colors: dict[str, str]) -> list[tuple[str, str, str]]:
    """Return [(role, hex, notes), ...] rows for the color scheme table.

    Heuristic mapping: lt1 is background, dk1 is body text, accents roll
    into primary/accent/secondary roles by order.
    """
    rows: list[tuple[str, str, str]] = []

    if 'lt1' in theme_colors:
        rows.append(('Background', theme_colors['lt1'], 'Page background (light)'))
    if 'lt2' in theme_colors:
        rows.append(('Secondary bg', theme_colors['lt2'], 'Card / panel background'))
    if 'dk1' in theme_colors:
        rows.append(('Body text', theme_colors['dk1'], 'Primary body copy'))
    if 'dk2' in theme_colors:
        rows.append(('Secondary text', theme_colors['dk2'], 'Captions, annotations'))

    accent_labels = ['Primary', 'Accent', 'Secondary accent', 'Success',
                     'Warning', 'Neutral']
    for i in range(1, 7):
        key = f'accent{i}'
        if key in theme_colors:
            label = accent_labels[i - 1] if i - 1 < len(accent_labels) else f'Accent {i}'
            rows.append((label, theme_colors[key], f'Theme {key}'))

    if 'hlink' in theme_colors:
        rows.append(('Link', theme_colors['hlink'], 'Hyperlink color'))

    return rows


# ---------------------------------------------------------------------------
# Typography: collect observed font sizes from representatives
# ---------------------------------------------------------------------------

def _collect_font_sizes(slides: list[SlideBlueprint]) -> list[float]:
    """Gather unique font sizes observed across slides (rounded to 0.5pt)."""
    seen: set[float] = set()
    for s in slides:
        _walk_runs_collect(s.shapes, seen)
    return sorted(seen, reverse=True)


def _walk_runs_collect(shapes: list[Shape], seen: set[float]) -> None:
    for s in shapes:
        if s.text is not None:
            for p in s.text.paragraphs:
                for r in p.runs:
                    if r.font_size:
                        seen.add(round(r.font_size * 2) / 2.0)
        if s.children:
            _walk_runs_collect(s.children, seen)


def _infer_size_hierarchy(sizes: list[float]) -> list[tuple[str, float]]:
    """Pick representative levels from the observed sizes.

    Keeps at most 5 buckets: cover title / chapter / content title /
    subtitle / body. Empty input yields a sensible default set.
    """
    if not sizes:
        return [
            ('Cover title', 56.0),
            ('Chapter title', 40.0),
            ('Content title', 28.0),
            ('Body', 18.0),
            ('Footnote', 12.0),
        ]
    # Take distinct ordered sizes, collapse near-duplicates (< 2pt apart)
    sorted_desc = sorted(sizes, reverse=True)
    kept: list[float] = []
    for s in sorted_desc:
        if not kept or abs(kept[-1] - s) >= 2.0:
            kept.append(s)

    labels = ['Cover / hero title', 'Chapter / page title',
              'Subtitle / section header', 'Body copy', 'Footnote / caption']
    return list(zip(labels, kept[: len(labels)]))


# ---------------------------------------------------------------------------
# Page structure: human-readable hints per cluster
# ---------------------------------------------------------------------------

def _page_description(fp: LayoutFingerprint) -> str:
    parts: list[str] = []
    if fp.page_type == 'cover':
        parts.append('Cover page with hero title.')
    elif fp.page_type == 'toc':
        parts.append('Table of contents / agenda listing.')
    elif fp.page_type == 'chapter':
        parts.append('Chapter or section divider.')
    elif fp.page_type == 'ending':
        parts.append('Closing / thank-you / contact page.')
    elif fp.page_type == 'content':
        if fp.column_count == 1:
            parts.append('Single-column content layout.')
        elif fp.column_count == 2:
            parts.append('Two-column comparison or image+text layout.')
        elif fp.column_count == 3:
            parts.append('Three-column card layout.')
        elif fp.column_count >= 4:
            parts.append('Grid layout (4+ columns).')
        else:
            parts.append('Flexible content layout.')
    else:
        parts.append('Mixed / uncategorized layout.')

    if fp.brightness == 'dark':
        parts.append('Dark theme background.')
    if fp.has_large_title:
        parts.append('Large top title emphasis.')
    if fp.image_count >= 2:
        parts.append(f'Typically includes {fp.image_count}+ images.')

    return ' '.join(parts)


# ---------------------------------------------------------------------------
# Placeholder catalog
# ---------------------------------------------------------------------------

def _catalog_placeholders(tag_report: list[TagRecord]) -> list[tuple[str, int, str]]:
    """Return [(tag, count, sample_original)], sorted by tag."""
    from collections import Counter

    tag_counts: Counter[str] = Counter()
    samples: dict[str, str] = {}
    for tr in tag_report:
        tag_counts[tr.tag] += 1
        samples.setdefault(tr.tag, tr.original_text or '(empty)')

    return [
        (tag, tag_counts[tag], samples[tag])
        for tag in sorted(tag_counts.keys())
    ]


# ---------------------------------------------------------------------------
# Full document writer
# ---------------------------------------------------------------------------

_TECHNICAL_CONSTRAINTS_MD = """\
### SVG Generation Must Follow

1. viewBox: `{viewbox_attr}`
2. Background rendered as a `<rect>` covering the canvas.
3. Text wrapping uses `<tspan>` — `<foreignObject>` is **forbidden**.
4. Transparency uses `fill-opacity` / `stroke-opacity`; `rgba()` is forbidden.
5. Forbidden elements: `clipPath` (except on `<image>`), `mask`, `<style>`, `class`,
   `foreignObject`, `textPath`, `animate*`, `<script>`, `<iframe>`.
6. `marker-start` / `marker-end` conditionally allowed — see
   `references/shared-standards.md` §1.1.

### PPT Compatibility Rules

- `<g opacity="...">` is forbidden; set `fill-opacity` / `stroke-opacity` on each
  child element individually.
- Image transparency uses an overlay mask layer (`<rect fill="bg" opacity="0.x"/>`).
- Inline styles only; external CSS and `@font-face` are forbidden.
"""


def write_design_spec(
    template_name: str,
    bp: Blueprint,
    clusters: list[ClusterResult],
    tag_report: list[TagRecord],
) -> str:
    """Render the design_spec.md body as a string."""
    vw, vh = bp.viewbox
    viewbox_attr = f"0 0 {vw} {vh}"
    today = date.today().isoformat()

    lines: list[str] = []

    # Header
    lines.append(f"# {template_name} — Design Specification")
    lines.append("")
    lines.append(
        f"> Auto-generated from `{bp.source_pptx.name}` on {today} by `pptx_blueprint`. "
        "Fill in the outline in Section VIII before handing off to the Executor."
    )
    lines.append("")

    # I. Template Overview
    lines.append("## I. Template Overview")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Template Name** | {template_name} |")
    lines.append(f"| **Source PPTX** | `{bp.source_pptx.name}` |")
    lines.append(f"| **Source Slides** | {len(bp.slides)} |")
    lines.append(f"| **Layout Variants** | {len(clusters)} |")
    lines.append(f"| **Generated** | {today} |")
    lines.append("")

    # II. Canvas Spec
    lines.append("## II. Canvas Specification")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| **Dimensions** | {vw} × {vh} px |")
    lines.append(f"| **viewBox** | `{viewbox_attr}` |")
    ratio = "16:9" if abs(vw / vh - 16 / 9) < 0.05 else "4:3" if abs(vw / vh - 4 / 3) < 0.05 else "custom"
    lines.append(f"| **Aspect Ratio** | {ratio} |")
    lines.append("")

    # III. Color Scheme
    lines.append("## III. Color Scheme")
    lines.append("")
    rows = _color_role_rows(bp.theme.colors)
    if rows:
        lines.append("| Role | HEX | Purpose |")
        lines.append("| --- | --- | --- |")
        for role, hex_color, notes in rows:
            lines.append(f"| **{role}** | `#{hex_color}` | {notes} |")
    else:
        lines.append("> No theme colors detected — fill in manually.")
    lines.append("")

    # IV. Typography
    lines.append("## IV. Typography System")
    lines.append("")
    lines.append("### Font Stack")
    lines.append("")
    fonts = bp.theme.fonts
    if fonts:
        for role, typeface in fonts.items():
            label = {
                'majorLatin': 'Major (titles, Latin)',
                'majorEastAsia': 'Major (titles, East Asian)',
                'minorLatin': 'Minor (body, Latin)',
                'minorEastAsia': 'Minor (body, East Asian)',
            }.get(role, role)
            lines.append(f"- **{label}**: `{typeface or '(default)'}`")
    else:
        lines.append("> Theme fonts use OS defaults. Pick typefaces in the project config.")
    lines.append("")
    lines.append("### Observed Size Hierarchy")
    lines.append("")
    lines.append("| Level | Size (pt) |")
    lines.append("| --- | --- |")
    for label, size in _infer_size_hierarchy(_collect_font_sizes(
            [r.slide for r in clusters])):
        size_str = f"{size:.1f}".rstrip('0').rstrip('.')
        lines.append(f"| {label} | {size_str} |")
    lines.append("")

    # V. Page Structure (one row per cluster)
    lines.append("## V. Page Structure")
    lines.append("")
    lines.append("Variants produced by the blueprint pipeline:")
    lines.append("")
    lines.append("| File | Page Type | Layout Hint | Represents Slides |")
    lines.append("| --- | --- | --- | --- |")
    for r in clusters:
        members = ", ".join(str(i) for i in r.member_indices)
        desc = _page_description(r.fingerprint)
        lines.append(f"| `{r.filename}` | {r.fingerprint.page_type} | {desc} | {members} |")
    lines.append("")

    # VI. Placeholder Catalog
    lines.append("## VI. Placeholder Catalog")
    lines.append("")
    catalog = _catalog_placeholders(tag_report)
    if catalog:
        lines.append("| Placeholder | Occurrences | Sample content |")
        lines.append("| --- | --- | --- |")
        for tag, count, sample in catalog:
            sample_escaped = sample.replace("|", "\\|")
            lines.append(f"| `{tag}` | {count} | {sample_escaped} |")
    else:
        lines.append("> No placeholders emitted (source template had no detectable text anchors).")
    lines.append("")

    # Provenance (tier A vs B breakdown)
    tier_a = sum(1 for t in tag_report if t.tier == 'A')
    tier_b = sum(1 for t in tag_report if t.tier == 'B')
    lines.append(f"*Provenance: {tier_a} canonical (p:ph) tags, {tier_b} heuristic inferences. "
                 "Review heuristic tags before handing to production — they may need manual tuning.*")
    lines.append("")

    # VII. Technical Constraints
    lines.append("## VII. Technical Constraints")
    lines.append("")
    lines.append(_TECHNICAL_CONSTRAINTS_MD.format(viewbox_attr=viewbox_attr))
    lines.append("")

    # VIII. Content Outline (placeholder)
    lines.append("## VIII. Content Outline")
    lines.append("")
    lines.append("> *To be filled in by the Strategist based on the project brief.*")
    lines.append("")
    lines.append("<!-- Strategist fills in the slide-by-slide content plan here -->")
    lines.append("")

    return "\n".join(lines)


def write_design_spec_file(
    output_path: Path,
    template_name: str,
    bp: Blueprint,
    clusters: list[ClusterResult],
    tag_report: list[TagRecord],
) -> None:
    """Write design_spec.md to disk."""
    body = write_design_spec(template_name, bp, clusters, tag_report)
    output_path.write_text(body, encoding='utf-8')
