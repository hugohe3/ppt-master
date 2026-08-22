# Advanced Image and Motion Maintenance Smoke

Run this manual smoke from the repository root after changing nested image
crop finalization, native picture export, deterministic Morph pairing, authored
PowerPoint presets, or their planning contracts. It builds one temporary
two-slide project under the gitignored `projects/_smoke_*` namespace and follows
the inline-smoke convention from
[`code-style.md`](../../../../docs/rules/code-style.md) §11; do not turn it into
a test file or public example deck.

The fixture deliberately closes the full planning and execution chain:

- `design_spec.md` carries `Motion suggestion`, one current §VIII image row,
  and `Crop Policy`, with no native-shape planning field;
- `spec_lock.md` projects that row with optional layout pattern `#M1-11`;
- both pages reuse one raster through ordinary, ellipse-preset, and custom-path
  independent nested crops;
- `animations.json` pairs the main crop across adjacent Morph pages;
- one complete registry read plus a helper-authored `rightArrow` verifies
  Executor-local native preset discovery and export.

```bash
python3 - <<'PY'
import base64
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageDraw

project = Path(
    tempfile.mkdtemp(
        prefix="_smoke_advanced_image_motion_",
        dir="projects",
    )
)
scripts = Path("skills/ppt-master/scripts")
images = project / "images"
svg_output = project / "svg_output"
images.mkdir()
svg_output.mkdir()
(project / "README.md").write_text(
    "# Advanced image and motion maintenance smoke\n",
    encoding="utf-8",
)


def run_tool(script, *args):
    result = subprocess.run(
        [sys.executable, str(scripts / script), *map(str, args)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


scene = Image.new("RGB", (1280, 720), "#E2E8F0")
draw = ImageDraw.Draw(scene)
draw.rectangle((0, 0, 420, 720), fill="#2563EB")
draw.rectangle((420, 0, 860, 720), fill="#F97316")
draw.rectangle((860, 0, 1280, 720), fill="#0F172A")
draw.ellipse((460, 150, 820, 510), fill="#F8FAFC")
scene.save(images / "scene.png")

preset_inventory = run_tool("preset_shape_svg.py", "list").splitlines()
assert len(preset_inventory) == 187
assert "rightArrow" in preset_inventory

preset = run_tool(
    "preset_shape_svg.py",
    "render",
    "rightArrow",
    "--id",
    "native-arrow",
    "--frame",
    "500",
    "570",
    "280",
    "80",
    "--fill",
    "#2563EB",
    "--stroke",
    "none",
)
preset = (
    '<g id="native-arrow-module" data-pptx-bounds="500 570 280 80">'
    + preset
    + "</g>"
)

(project / "design_spec.md").write_text(
    """<!-- ppt-master-schema: design-spec/v1 -->
# Advanced Image and Motion Smoke - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | advanced-image-motion-smoke |
| Canvas Format | PPT 16:9 |
| Page Count | 2 |

## II. Canvas Specification

- ViewBox: `0 0 1280 720`
- Format: `ppt169`

## III. Visual Theme

- Direction: restrained technical maintenance fixture
- Colors: blue, orange, slate, and white

## IV. Typography System

- Title: Arial, sans-serif at 36px
- Body: Arial, sans-serif at 20px

## V. Layout Principles

- Reuse one source image through independently editable crop objects.
- Keep every visible crop inside the slide canvas.

## VI. Icon Usage Specification

- No icons.

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| scene.png | 1280x720 | 16:9 | Morph crop continuity | Photo | #M1-11 same-source independent crops with a shaped detail | adaptive | user | Existing | Synthetic three-band scene for crop and Morph verification | none | local |

## IX. Content Outline

### Part 1: Crop continuity

#### Slide 01 - Overview

- **Audience move**: See separate source views as one editable image system.
- **Layout**: Ordinary crop and shaped detail establish the first visual state.
- **Title**: Overview crop state
- **Core message**: One source can support independent native picture objects.
- **Content**: Show the wide crop and shaped detail together.
- **Images**: Use `scene.png` for both visible crop objects.
- **Motion suggestion**: Continue the primary crop into Slide 02 as one deterministic Morph object.

#### Slide 02 - Detail

- **Audience move**: Recognize the same image after a controlled crop and position change.
- **Layout**: Enlarged primary crop plus a second shaped detail.
- **Title**: Detail crop state
- **Core message**: Morph identity is independent from the picture crop geometry.
- **Content**: Move and zoom the primary crop while preserving the shared source.
- **Images**: Reuse `scene.png`; do not generate or replace the source.
- **Motion suggestion**: Pair the primary crop with Slide 01 and use Morph by object.

## X. Speaker Notes Requirements

- Notes are disabled for this maintenance smoke.
""",
    encoding="utf-8",
)

(project / "spec_lock.md").write_text(
    """<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: ppt169
## communication
- audience: PPT Master maintainers
- objective: Verify advanced image and motion contracts end to end.
- core_message: One raster remains editable across native crops and Morph.
## mode
- mode: showcase
## visual_style
- visual_style: swiss-minimal
## colors
- bg: #FFFFFF
- primary: #2563EB
- accent: #F97316
- text: #0F172A
## typography
- font_family: Arial, sans-serif
- title_family: Arial, sans-serif
- body_family: Arial, sans-serif
- title: 36
- body: 20
## icons
- library: none
- inventory: none
## images
- scene: images/scene.png | source=user | pattern=#M1-11 same-source independent crops with a shaped detail | crop=adaptive
## page_rhythm
- P01: dense
- P02: dense
## pptx_structure
- mode: flat
## forbidden
- Unsupported SVG constructs
""",
    encoding="utf-8",
)

slide_1 = f"""<svg xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 1280 720" data-pptx-page-role="content">
  <defs>
    <clipPath id="overview-shape" clipPathUnits="userSpaceOnUse">
      <ellipse cx="0.725" cy="0.5" rx="0.275" ry="0.5"/>
    </clipPath>
  </defs>
  <rect id="background" data-pptx-role="background"
    x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
  <g id="hero-overview" data-pptx-bounds="80 140 448 360">
    <svg id="overview-crop" x="80" y="140" width="448" height="360"
      viewBox="0 0 0.7 1" preserveAspectRatio="none" overflow="hidden">
      <image href="../images/scene.png" x="0" y="0" width="1" height="1"
        preserveAspectRatio="none"/>
    </svg>
  </g>
  <g id="shaped-overview" data-pptx-bounds="760 170 330 340">
    <svg id="overview-shaped-crop" data-pptx-crop="1"
      x="760" y="170" width="330" height="340"
      viewBox="0.45 0 0.55 1" preserveAspectRatio="none" overflow="hidden">
      <image href="../images/scene.png" x="0" y="0" width="1" height="1"
        preserveAspectRatio="none" clip-path="url(#overview-shape)"/>
    </svg>
  </g>
  {preset}
</svg>
"""

slide_2 = """<svg xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 1280 720" data-pptx-page-role="content">
  <defs>
    <clipPath id="detail-shape" clipPathUnits="userSpaceOnUse">
      <path d="M 0.5 1 L 0.75 0 L 1 1 Z"/>
    </clipPath>
  </defs>
  <rect id="background" data-pptx-role="background"
    x="0" y="0" width="1280" height="720" fill="#FFFFFF"/>
  <g id="hero-detail" data-pptx-bounds="0 0 1280 720">
    <svg id="detail-crop" x="0" y="0" width="1280" height="720"
      viewBox="0.15 0.1 0.36 0.36"
      preserveAspectRatio="none" overflow="hidden">
      <image href="../images/scene.png" x="0" y="0" width="1" height="1"
        preserveAspectRatio="none"/>
    </svg>
  </g>
  <g id="shaped-detail" data-pptx-bounds="820 160 320 360">
    <svg id="detail-shaped-crop" data-pptx-crop="1"
      x="820" y="160" width="320" height="360"
      viewBox="0.5 0 0.5 1" preserveAspectRatio="none" overflow="hidden">
      <image href="../images/scene.png" x="0" y="0" width="1" height="1"
        preserveAspectRatio="none" clip-path="url(#detail-shape)"/>
    </svg>
  </g>
</svg>
"""

(svg_output / "01_overview.svg").write_text(slide_1, encoding="utf-8")
(svg_output / "02_detail.svg").write_text(slide_2, encoding="utf-8")
(project / "animations.json").write_text(
    json.dumps(
        {
            "version": 1,
            "slides": {
                "02_detail": {
                    "transition": {
                        "effect": "morph",
                        "effect_options": {"morph_by": "object"},
                        "duration": 0.8,
                    },
                    "morph": {
                        "from": "01_overview",
                        "pairs": {
                            "hero-image": {
                                "from": "hero-overview",
                                "to": "hero-detail",
                            }
                        },
                    },
                }
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

run_tool("project_manager.py", "validate", project)
run_tool(
    "svg_quality_checker.py",
    project,
    "--format",
    "ppt169",
    "--stage",
    "final",
    "--json",
)
run_tool("animation_config.py", "validate", project)


def finalized_image_sizes():
    sizes = []
    for svg_path in sorted((project / "svg_final").glob("*.svg")):
        root = ET.parse(svg_path).getroot()
        for image in root.iter("{http://www.w3.org/2000/svg}image"):
            href = image.get("href") or image.get(
                "{http://www.w3.org/1999/xlink}href"
            )
            assert href and href.startswith("data:image/"), href
            payload = base64.b64decode(href.split(",", 1)[1], validate=True)
            with Image.open(io.BytesIO(payload)) as embedded:
                sizes.append(embedded.size)
    return sizes


finalized_sizes = []
for finalize_args in ((), ("--no-compress",)):
    run_tool("finalize_svg.py", project, *finalize_args)
    embedded_sizes = finalized_image_sizes()
    assert len(embedded_sizes) == 4, embedded_sizes
    assert all(width > 100 and height > 100 for width, height in embedded_sizes)
    finalized_sizes.append(embedded_sizes)

pptx = project / "advanced-image-motion.pptx"
run_tool("svg_to_pptx.py", project, "--no-notes", "-o", pptx)
with zipfile.ZipFile(pptx) as archive:
    slide_names = sorted(
        name
        for name in archive.namelist()
        if re.fullmatch(r"ppt/slides/slide[12]\.xml", name)
    )
    slide_xml = [archive.read(name) for name in slide_names]
assert len(slide_xml) == 2, slide_names
assert all(b'!!hero-image' in xml for xml in slide_xml)
assert b'morph' in slide_xml[1]
assert sum(xml.count(b"<a:srcRect") for xml in slide_xml) >= 4
assert b'<a:prstGeom prst="ellipse">' in slide_xml[0]
assert b'<a:prstGeom prst="rightArrow">' in slide_xml[0]
assert b"<a:custGeom>" in slide_xml[1]

readback = project / "readback"
run_tool(
    "pptx_to_svg.py",
    pptx,
    "-o",
    readback,
    "--inheritance-mode",
    "flat",
    "--strict",
)
readback_svg = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted((readback / "svg").glob("slide_*.svg"))
)
assert readback_svg.count('data-pptx-crop="1"') >= 2
assert readback_svg.count('data-pptx-shape-name="!!hero-image"') == 2

print(
    "Advanced image and motion smoke: passed "
    f"(embedded sizes={finalized_sizes}; project={project})"
)
PY
```

Every command must exit successfully. The finalized data URIs must retain
useful source pixels rather than collapsing to the nested child’s unit
coordinates; the package must contain four native picture crops, the authored
`rightArrow`, one Morph transition, and exactly one `!!hero-image` target on
each adjacent slide. The strict PPTX-to-SVG readback must restore both shaped
crop markers and both forced-Morph object names.

The printed project is intentionally retained for manual Microsoft PowerPoint
inspection. Morph must continue the primary picture without a visible
cross-fade, sharpness jump, or media re-decoding flash. That Office-only visual
check is evidence gathering; to stress differing media payloads, replace
`scene.png` with a `7680×4320` source and re-export. Do not trigger media
deduplication changes from package structure alone.
