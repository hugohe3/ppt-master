"""Tests for text width estimation and letter-spacing handling.

Covers issue #199: LibreOffice wraps text because the DrawingML text box
is too narrow when letter-spacing is used or the font is a wide serif.
"""
import sys, os

# Make svg_to_pptx package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'ppt-master', 'scripts'))

from svg_to_pptx.drawingml_utils import estimate_text_width


class TestEstimateTextWidth:
    """estimate_text_width basic behaviour."""

    def test_ascii_string(self):
        w = estimate_text_width("Hello", font_size=20)
        assert w > 0

    def test_bold_wider_than_normal(self):
        normal = estimate_text_width("PSYOPTIMAL", font_size=20, font_weight='400')
        bold = estimate_text_width("PSYOPTIMAL", font_size=20, font_weight='700')
        assert bold > normal

    def test_cjk_char_full_width(self):
        w = estimate_text_width("中", font_size=20)
        assert w == 20  # 1 CJK char = font_size


class TestLetterSpacingAware:
    """Letter-spacing must be factored into width estimation (issue #199)."""

    def test_letter_spacing_adds_width(self):
        base = estimate_text_width("MARKET OPPORTUNITY", font_size=14)
        with_ls = estimate_text_width(
            "MARKET OPPORTUNITY", font_size=14, letter_spacing=2.0
        )
        # 18 chars → 17 gaps × 2px = 34px extra
        assert with_ls >= base + 30

    def test_zero_letter_spacing_no_change(self):
        base = estimate_text_width("Hello", font_size=20)
        with_zero = estimate_text_width("Hello", font_size=20, letter_spacing=0)
        assert with_zero == base

    def test_single_char_no_letter_spacing_effect(self):
        """A single character has no inter-char gaps."""
        base = estimate_text_width("X", font_size=20)
        with_ls = estimate_text_width("X", font_size=20, letter_spacing=5)
        assert with_ls == base


class TestSerifAware:
    """Serif fonts like Georgia have wider glyphs than the 0.55em average."""

    def test_serif_wider_than_default(self):
        default_w = estimate_text_width("PSYOPTIMAL", font_size=20)
        serif_w = estimate_text_width(
            "PSYOPTIMAL", font_size=20, font_family="Georgia"
        )
        assert serif_w > default_w

    def test_times_new_roman_treated_as_serif(self):
        default_w = estimate_text_width("MARKET OPPORTUNITY", font_size=14)
        times_w = estimate_text_width(
            "MARKET OPPORTUNITY", font_size=14,
            font_family="Times New Roman"
        )
        assert times_w > default_w

    def test_generic_sans_no_extra_width(self):
        default_w = estimate_text_width("Hello", font_size=20)
        arial_w = estimate_text_width("Hello", font_size=20, font_family="Arial")
        # Arial is sans-serif — should NOT get the serif bonus
        assert arial_w == default_w


class TestCombinedSerifAndLetterSpacing:
    """Both fixes together must produce a box wide enough for LibreOffice."""

    def test_georgia_caps_with_tracking(self):
        """Simulates the exact scenario from the issue report."""
        w = estimate_text_width(
            "PSYOPTIMAL", font_size=24,
            font_weight='700', font_family='Georgia',
            letter_spacing=1.5,
        )
        bare = estimate_text_width("PSYOPTIMAL", font_size=24, font_weight='700')
        # Must be noticeably wider than the bare estimate
        assert w > bare * 1.2

    def test_eyebrow_label_scenario(self):
        """Eyebrow/kicker label with tracking: 'PROJECTED BY 2030'."""
        w = estimate_text_width(
            "PROJECTED BY 2030", font_size=12,
            font_family='Georgia', letter_spacing=2.5,
        )
        bare = estimate_text_width("PROJECTED BY 2030", font_size=12)
        assert w > bare * 1.3
