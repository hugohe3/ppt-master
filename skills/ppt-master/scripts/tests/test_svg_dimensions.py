"""Root <svg> width/height backfill + quality-gate coverage.

A root ``<svg>`` carrying only ``viewBox`` is valid scalable SVG (so models
omit ``width``/``height``), but it trips PPT preview/export dimension detection
and fires the live-preview "missing width/height" banner. The pipeline now
deterministically backfills the two attributes from ``viewBox`` at every
``svg_output`` ingress (finalize → ``svg_final`` and the live-preview serve
path), independent of which model wrote the SVG.

Run: ``python -m pytest skills/ppt-master/scripts/tests/test_svg_dimensions.py``
"""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR / "svg_finalize"))

from svg_finalize.normalize_dimensions import (  # noqa: E402
    backfill_root_dimensions,
    backfill_svg_dimensions,
)
from svg_quality_checker import SVGQualityChecker  # noqa: E402


# -------------------- string adapter (finalize path) --------------------

def test_string_backfill_missing_both():
    src = '<svg viewBox="0 0 1280 720" xmlns="http://www.w3.org/2000/svg"></svg>'
    out, changed = backfill_svg_dimensions(src)
    assert changed is True
    assert 'width="1280"' in out and 'height="720"' in out


def test_string_backfill_missing_only_height():
    out, changed = backfill_svg_dimensions('<svg width="1280" viewBox="0 0 1280 720"></svg>')
    assert changed is True
    assert out.count('width="1280"') == 1
    assert 'height="720"' in out


def test_string_backfill_present_is_noop():
    src = '<svg width="1280" height="720" viewBox="0 0 1280 720"></svg>'
    out, changed = backfill_svg_dimensions(src)
    assert changed is False and out == src


def test_string_backfill_no_viewbox_is_noop():
    src = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    out, changed = backfill_svg_dimensions(src)
    assert changed is False and out == src


def test_string_backfill_offset_viewbox_is_noop():
    # Non-zero origin: cannot safely infer canvas width/height, leave as-is.
    _, changed = backfill_svg_dimensions('<svg viewBox="10 10 1280 720"></svg>')
    assert changed is False


def test_string_backfill_ignores_child_dimensions():
    src = '<svg viewBox="0 0 1280 720"><rect width="500" height="200" fill="#fff"/></svg>'
    out, changed = backfill_svg_dimensions(src)
    assert changed is True
    root_tag = out[: out.index(">") + 1]
    assert 'width="1280"' in root_tag and 'height="720"' in root_tag
    assert 'width="500" height="200"' in out  # child untouched


# -------------------- ET adapter (live-preview serve path) --------------------

def test_et_backfill_sets_missing_dims():
    root = ET.fromstring('<svg viewBox="0 0 960 540"></svg>')
    assert backfill_root_dimensions(root) is True
    assert root.get("width") == "960" and root.get("height") == "540"


def test_et_backfill_preserves_existing_dims():
    root = ET.fromstring('<svg width="800" height="600" viewBox="0 0 960 540"></svg>')
    assert backfill_root_dimensions(root) is False
    assert root.get("width") == "800"  # author intent preserved


# -------------------- quality gate --------------------

def _dim_result(content: str, *, viewbox: str | None = None):
    result = {"errors": [], "warnings": [], "info": {}}
    if viewbox is not None:
        result["info"]["viewbox"] = viewbox
    SVGQualityChecker()._check_dimensions(content, result)
    return result


def test_quality_warns_on_missing_root_dims():
    result = _dim_result('<svg viewBox="0 0 1280 720"></svg>', viewbox="0 0 1280 720")
    assert any("missing" in w for w in result["warnings"])
    assert result["errors"] == []


def test_quality_no_false_pass_on_child_width():
    # The old whole-document regex matched the child <rect> width and silently
    # passed. Scoped to the root tag, this must now warn.
    content = '<svg viewBox="0 0 1280 720"><rect width="1280" height="720"/></svg>'
    result = _dim_result(content, viewbox="0 0 1280 720")
    assert any("missing" in w for w in result["warnings"])
    assert "dimensions" not in result["info"]


def test_quality_consistent_dims_no_warning():
    content = '<svg width="1280" height="720" viewBox="0 0 1280 720"></svg>'
    result = _dim_result(content, viewbox="0 0 1280 720")
    assert result["warnings"] == [] and result["info"]["dimensions"] == "1280x720"


def test_quality_mismatch_dims_warns():
    content = '<svg width="1920" height="1080" viewBox="0 0 1280 720"></svg>'
    result = _dim_result(content, viewbox="0 0 1280 720")
    assert any("does not match viewBox" in w for w in result["warnings"])
