"""Per-slot fit guidance for a native-diagram component.

``extract`` records every ``<a:t>`` run as a text slot (its original label is the
authoring hint for what that slot holds). ``slot_spec`` adds, per slot, *how much*
text fits and *what kind* — so the Strategist can map page content onto the figure
without overflowing it.

Budget is measured in **visual width**, not character count: a CJK glyph renders
roughly twice as wide as a Latin letter, so a slot designed for ``"应用层"`` (3
glyphs ≈ 6 columns) holds about 6 Latin characters, not 3. Counting characters
would let a 6-character English label overflow a slot sized for 3 Chinese ones.

See ``references/native-diagrams.md`` §3 (the ``data-text`` contract).
"""
from __future__ import annotations

import unicodedata

# Visual-width style bands (in columns; CJK glyph = 2, Latin/digit/punct = 1).
_TINY_MAX = 2          # a number / badge / single CJK glyph
_SHORT_LABEL_MAX = 8   # a node / layer name (2-4 CJK glyphs, or a short word)
_PHRASE_MAX = 18       # a short phrase / sub-label

FIT_GUIDANCE = (
    "Map content onto ALL slots (id 0..N-1). Keep each replacement within its "
    "`budget` — budget is VISUAL WIDTH, not character count: a CJK glyph counts as "
    "2, a Latin letter / digit / ASCII punct as 1 (so a budget of 6 fits ~3 Chinese "
    "characters OR ~6 Latin ones). Longer text truncates or overflows the slot. "
    "Match a slot's `style`: tiny=number/badge, short-label=node/layer name, "
    "phrase=sub-label, sentence=one short line. Adapt/condense the page content to "
    "the component's structure; do NOT leave any slot at its original text."
)


def visual_width(text: str) -> int:
    """Rendered column width of *text*: wide/fullwidth (CJK) glyphs count 2, else 1."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def style_of(width: int) -> str:
    """Classify a slot by its original visual width into a content-kind hint."""
    if width <= _TINY_MAX:
        return "tiny"
    if width <= _SHORT_LABEL_MAX:
        return "short-label"
    if width <= _PHRASE_MAX:
        return "phrase"
    return "sentence"


def budget_of(width: int) -> int:
    """Replacement budget (visual width). The slot is sized for its original width;
    allow that much, with a 2-column floor so a 1-glyph slot still takes a short word."""
    return max(width, 2)


def compute_slot_spec(text_slots: list[dict]) -> list[dict]:
    """Build the ``slot_spec`` list from ``meta.text_slots`` (CJK-aware budgets)."""
    spec = []
    for t in text_slots:
        orig = (t.get("text") or "").strip()
        w = visual_width(orig)
        spec.append({
            "id": t.get("id", len(spec)),
            "orig": orig,
            "width": w,
            "budget": budget_of(w),
            "style": style_of(w),
        })
    return spec
