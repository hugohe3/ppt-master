# Mask and Gradient Maintenance Smoke

Run this manual smoke from the repository root after changing gradient
validation, gradient import/export, native background promotion, icon
expansion, or mask rejection. It keeps XML in memory except for temporary SVG
fixtures; do not turn it into a test framework or example deck.

```bash
python3 - <<'PY'
import math
import re
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

scripts = Path("skills/ppt-master/scripts").resolve()
sys.path.insert(0, str(scripts))

from pptx_to_svg.fill_to_svg import _angle_to_unit_endpoints
from svg_quality_checker import SVGQualityChecker
from svg_to_pptx.drawingml.converter import (
    SvgNativeConversionError,
    convert_svg_to_slide_shapes,
)
from svg_to_pptx.drawingml.styles import build_gradient_fill
from svg_to_pptx.drawingml.utils import (
    parse_project_linear_gradient_coordinate,
    project_gradient_errors,
    project_mask_errors,
)

SVG_NS = "http://www.w3.org/2000/svg"


def svg(fragment):
    return ET.fromstring(
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 1280 720" '
        f'data-pptx-page-role="content">{fragment}</svg>'
    )


valid = svg(
    """<defs>
  <linearGradient id="linear">
    <stop offset="0" stop-color="#2563EB"/>
    <stop offset="100%" stop-color="#F97316" stop-opacity="0.4"/>
  </linearGradient>
  <radialGradient id="radial" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="#FFFFFF"/>
    <stop offset="1" stop-color="#0F172A"/>
  </radialGradient>
</defs>
<rect id="bg" x="0" y="0" width="1280" height="720"
  fill="url(#linear)"/>"""
)
assert not project_gradient_errors(valid)
linear, radial = list(valid.find(f"{{{SVG_NS}}}defs"))
linear_xml = build_gradient_fill(linear)
radial_xml = build_gradient_fill(radial)
assert '<a:lin ang="0" scaled="1"/>' in linear_xml
assert '<a:alpha val="40000"/>' in linear_xml
assert '<a:path path="circle">' in radial_xml

with tempfile.TemporaryDirectory(prefix="ppt-master-gradient-smoke-") as tmp:
    source = Path(tmp) / "gradient.svg"
    source.write_text(
        ET.tostring(valid, encoding="unicode"),
        encoding="utf-8",
    )
    trace = []
    slide_xml, *_ = convert_svg_to_slide_shapes(source, trace_out=trace)
assert slide_xml.count("<p:bg>") == 1
assert "<a:gradFill>" in slide_xml
assert trace[0]["summary"]["promoted_backgrounds"] == 1
assert any(
    event.get("decision") == "native-background"
    for event in trace[0]["events"]
)

invalid_gradients = [
    (
        """<linearGradient id="single">
  <stop offset="0" stop-color="#2563EB"/>
</linearGradient>""",
        "requires at least two direct <stop> children",
    ),
    (
        """<linearGradient id="descending">
  <stop offset="1" stop-color="#2563EB"/>
  <stop offset="0" stop-color="#F97316"/>
</linearGradient>""",
        "offsets must be non-decreasing",
    ),
    (
        """<linearGradient id="zero" x1="0.5" y1="0.5" x2="0.5" y2="0.5">
  <stop offset="0" stop-color="#2563EB"/>
  <stop offset="1" stop-color="#F97316"/>
</linearGradient>""",
        "linear gradient axis must not collapse to one point",
    ),
]
for definition, expected in invalid_gradients:
    errors = project_gradient_errors(svg(f"<defs>{definition}</defs>"))
    assert any(expected in error for error in errors), errors

mask_cases = [
    """<defs><mask id="fade"><rect width="1" height="1"/></mask></defs>""",
    """<rect width="100" height="100" mask="url(#fade)"/>""",
    """<rect width="100" height="100" style="mask: url(#fade)"/>""",
]
for fragment in mask_cases:
    errors = project_mask_errors(svg(fragment))
    assert any("unsupported SVG mask" in error for error in errors), errors

checker = SVGQualityChecker()
with tempfile.TemporaryDirectory(prefix="ppt-master-mask-smoke-") as tmp:
    for index, fragment in enumerate(mask_cases, start=1):
        source = Path(tmp) / f"mask-{index}.svg"
        source.write_text(
            ET.tostring(svg(fragment), encoding="unicode"),
            encoding="utf-8",
        )
        checked = checker.check_file(str(source))
        assert any("mask" in error.lower() for error in checked["errors"])
        try:
            convert_svg_to_slide_shapes(source)
        except SvgNativeConversionError as exc:
            assert "invalid project mask" in str(exc)
        else:
            raise AssertionError(f"native export accepted {source.name}")

with tempfile.TemporaryDirectory(prefix="ppt-master-icon-mask-smoke-") as tmp:
    project = Path(tmp)
    icon_dir = project / "icons" / "imported"
    icon_dir.mkdir(parents=True)
    (icon_dir / "masked.svg").write_text(
        f"""<svg xmlns="{SVG_NS}" viewBox="0 0 24 24">
  <defs>
    <mask id="fade">
      <rect x="0" y="0" width="24" height="24" fill="#FFFFFF"/>
    </mask>
  </defs>
  <rect x="0" y="0" width="24" height="24"
    fill="#000000" mask="url(#fade)"/>
</svg>""",
        encoding="utf-8",
    )
    source = project / "icon-mask.svg"
    source.write_text(
        ET.tostring(
            svg(
                """<use data-icon="imported/masked"
  x="20" y="20" width="24" height="24"/>"""
            ),
            encoding="unicode",
        ),
        encoding="utf-8",
    )
    checked = checker.check_file(str(source))
    assert any(
        "Icon imported/masked" in error and "mask" in error.lower()
        for error in checked["errors"]
    )
    try:
        convert_svg_to_slide_shapes(source)
    except SvgNativeConversionError as exc:
        assert "invalid project mask" in str(exc)
    else:
        raise AssertionError("native export accepted a masked icon")

x1, y1, x2, y2 = _angle_to_unit_endpoints(30)
assert any(value < 0 or value > 1 for value in (x1, y1, x2, y2))
for value in (x1, y1, x2, y2):
    assert math.isclose(
        parse_project_linear_gradient_coordinate(str(value)),
        value,
        abs_tol=1e-9,
    )
roundtrip = svg(
    f"""<defs>
  <linearGradient id="roundtrip"
    x1="{x1:.9f}" y1="{y1:.9f}" x2="{x2:.9f}" y2="{y2:.9f}">
    <stop offset="0" stop-color="#2563EB"/>
    <stop offset="1" stop-color="#F97316"/>
  </linearGradient>
</defs>"""
)
assert not project_gradient_errors(roundtrip)
roundtrip_gradient = roundtrip.find(
    f"{{{SVG_NS}}}defs/{{{SVG_NS}}}linearGradient"
)
angle = int(
    re.search(
        r'<a:lin ang="(\d+)"',
        build_gradient_fill(roundtrip_gradient),
    ).group(1)
) / 60000
assert math.isclose(angle, 30, abs_tol=0.01), angle

print("Mask and gradient smoke: passed")
PY
```

The three invalid-gradient cases, all three direct mask forms, and a mask
hidden inside a `data-icon` asset must produce the named shared-validator
errors in both Checker and direct export. The legal cases must retain stop
alpha, promote the full-canvas gradient to one native `p:bg`, default an
unpositioned linear gradient to horizontal, and recover approximately 30
degrees from the importer's out-of-unit-box endpoint form.
