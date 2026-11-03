#!/usr/bin/env python3
"""
PPT Master - Image OCR Tool

OCR helper for the Image to PPTX profile. `scan` reads normalized page images
and writes one reviewable JSON per page with text blocks in canvas pixels
(wording, line boxes, estimated font size, sampled ink color). `merge-base`
keeps source pixels outside the OCR text boxes of a text-removed image.
`text-layer` writes the quick-restore page SVG: the text-free base image as a
background plus one native text group per reviewed block.

Usage:
    python3 scripts/image_ocr.py scan <project_path> <page_image> [<page_image> ...] [--canvas WxH]
    python3 scripts/image_ocr.py merge-base <project_path> --page <stem> --inpainted <png> --out <png>
    python3 scripts/image_ocr.py text-layer <project_path> --page <stem> --base <png> --out <svg>

Examples:
    python3 scripts/image_ocr.py scan projects/demo images/source-pages/01.png --canvas 1280x720
    python3 scripts/image_ocr.py text-layer projects/demo --page 01 \\
        --base images/01_base.png --out svg_output/01_cover.svg --font "Microsoft YaHei, Arial"

Dependencies:
    Pillow; rapidocr + onnxruntime (optional, scan only: pip install rapidocr onnxruntime)

See workflows/profiles/image-to-pptx.md for when each command runs and
scripts/docs/image-ocr.md for the JSON layout and placement rules.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape, quoteattr

from PIL import Image, ImageDraw, ImageFilter

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

OCR_DIR = "analysis/ocr"
LOW_CONFIDENCE = 0.9
RESIDUE_MIN_SCORE = 0.6
INSTALL_HINT = "image_ocr.py scan needs rapidocr: pip install rapidocr onnxruntime"


@dataclass
class Line:
    text: str
    score: float
    x: float
    y: float
    w: float
    h: float


@dataclass
class Block:
    id: str
    text: str
    lines: list[Line] = field(default_factory=list)
    font_size: float = 0.0
    color: str = "#000000"
    min_score: float = 1.0


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def text_units(text: str) -> float:
    """Approximate advance width in em: CJK/full-width 1.0, capitals 0.68, other glyphs 0.36-0.56."""
    total = 0.0
    for char in text:
        if char.isspace():
            total += 0.3
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            total += 1.0
        elif char.isupper():
            total += 0.68
        elif char.isalnum():
            total += 0.54
        else:
            total += 0.36
    return total


MONO_HINTS = ("mono", "consolas", "courier", "menlo")


def is_monospace(stack: str) -> bool:
    first = stack.split(",")[0].strip().lower()
    return any(hint in first for hint in MONO_HINTS)


def mono_units(text: str) -> float:
    """Advance width in em for a monospace face: CJK/full-width 1.0, everything else 0.55."""
    return sum(1.0 if unicodedata.east_asian_width(c) in {"W", "F"} else 0.55 for c in text)


def estimate_font_size(lines: list[Line], units=None) -> float:
    units = units or text_units
    by_width = [line.w / units(line.text) for line in lines if units(line.text) >= 4]
    if by_width:
        return float(int(statistics.median(by_width) * 0.97))
    return float(round(statistics.median(line.h / 1.4 for line in lines)))


def sample_ink(image: Image.Image, scale: float, line: Line) -> str:
    """Return the text color inside one line box as #RRGGBB (contrast to the box border)."""
    box = (int(line.x * scale), int(line.y * scale),
           max(int((line.x + line.w) * scale), int(line.x * scale) + 2),
           max(int((line.y + line.h) * scale), int(line.y * scale) + 2))
    crop = image.crop(box).convert("RGB")
    width, height = crop.size
    border = [crop.getpixel((x, y)) for x in range(width) for y in (0, height - 1)]
    border += [crop.getpixel((x, y)) for y in range(height) for x in (0, width - 1)]
    background = tuple(statistics.median(channel) for channel in zip(*border))

    def distance(pixel: tuple[int, ...]) -> float:
        return sum((a - b) ** 2 for a, b in zip(pixel, background)) ** 0.5

    pixels = list(crop.getdata())
    far = max(distance(pixel) for pixel in pixels) or 1.0
    ink = [pixel for pixel in pixels if distance(pixel) > 0.6 * far]
    return "#" + "".join(f"{round(statistics.fmean(channel)):02X}" for channel in zip(*ink))


def color_distance(first: str, second: str) -> float:
    a = [int(first[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(second[i:i + 2], 16) for i in (1, 3, 5)]
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def group_blocks(lines: list[Line], inks: dict[int, str]) -> list[list[Line]]:
    """Merge vertically adjacent lines sharing a left edge, size, and ink color into paragraphs."""
    remaining = sorted(lines, key=lambda line: (line.y, line.x))
    blocks: list[list[Line]] = []
    while remaining:
        block = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            last = block[-1]
            for candidate in remaining:
                same_edge = abs(candidate.x - block[0].x) <= 0.6 * last.h
                same_size = abs(candidate.h - last.h) <= 0.25 * last.h
                same_ink = color_distance(inks[id(candidate)], inks[id(last)]) < 64
                gap = candidate.y - (last.y + last.h)
                if same_edge and same_size and same_ink and -0.3 * last.h <= gap <= 0.9 * last.h:
                    block.append(candidate)
                    remaining.remove(candidate)
                    changed = True
                    break
        blocks.append(block)
    return blocks


def join_lines(lines: list[Line]) -> str:
    """Join wrapped lines: no separator between CJK neighbors, one space otherwise."""
    text = lines[0].text
    for line in lines[1:]:
        tail, head = text[-1:], line.text[:1]
        wide = any(unicodedata.east_asian_width(c) in {"W", "F"} for c in tail + head)
        text += ("" if wide else " ") + line.text
    return text


# ---------------------------------------------------------------------------
# scan
# ---------------------------------------------------------------------------

def parse_canvas(value: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in value.lower().split("x"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("canvas must look like 1280x720") from exc
    return width, height


def cmd_scan(args: argparse.Namespace) -> int:
    try:
        from rapidocr import RapidOCR
    except ImportError:
        print(INSTALL_HINT, file=sys.stderr)
        return 2
    project = Path(args.project_path).resolve()
    canvas_w, canvas_h = args.canvas
    engine = RapidOCR()
    out_dir = project / OCR_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    for page_arg in args.pages:
        page = (project / page_arg) if not Path(page_arg).is_absolute() else Path(page_arg)
        if not page.is_file():
            print(f"Missing page image: {page}", file=sys.stderr)
            return 1
        image = Image.open(page)
        scale = canvas_w / image.size[0]
        result = engine(str(page))
        lines = []
        empty = result.boxes is None
        for box, text, score in zip([] if empty else result.boxes, result.txts or (), result.scores or ()):
            xs = [float(point[0]) * scale for point in box]
            ys = [float(point[1]) * scale for point in box]
            lines.append(Line(text=str(text), score=round(float(score), 3),
                              x=round(min(xs), 1), y=round(min(ys), 1),
                              w=round(max(xs) - min(xs), 1), h=round(max(ys) - min(ys), 1)))
        inks = {id(line): sample_ink(image, 1 / scale, line) for line in lines}
        blocks = []
        for number, group in enumerate(group_blocks(lines, inks), start=1):
            blocks.append(Block(
                id=f"t{number:02d}",
                text=join_lines(group),
                lines=group,
                font_size=estimate_font_size(group),
                color=inks[id(group[0])],
                min_score=min(line.score for line in group),
            ))
        payload = {
            "page_image": str(page.relative_to(project)) if page.is_relative_to(project) else str(page),
            "canvas": [canvas_w, canvas_h],
            "page_pixels": list(image.size),
            "blocks": [asdict(block) for block in blocks],
        }
        out = out_dir / f"{page.stem}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        low = [block for block in blocks if block.min_score < LOW_CONFIDENCE]
        print(f"{out.relative_to(project)}: {len(blocks)} block(s), {len(low)} low-confidence")
        for block in blocks:
            flag = "?" if block.min_score < LOW_CONFIDENCE else " "
            first = block.lines[0]
            print(f"  {flag} {block.id} x={first.x} y={first.y} size={block.font_size} "
                  f"{block.color} lines={len(block.lines)} | {block.text}")
    return 0


# ---------------------------------------------------------------------------
# text-layer
# ---------------------------------------------------------------------------

def family_stack(value: str, generic: str = "sans-serif") -> str:
    families = [part.strip() for part in value.split(",") if part.strip()]
    if generic not in families:
        families.append(generic)
    return ", ".join(families)


def cmd_merge_base(args: argparse.Namespace) -> int:
    """Keep source pixels except inside text boxes and removed-layer areas; low-res pages keep the generated image."""
    project = Path(args.project_path).resolve()
    ocr_path = project / OCR_DIR / f"{args.page}.json"
    inpainted_path = project / args.inpainted
    for required in [ocr_path, inpainted_path] + [project / layer for layer in args.layer]:
        if not required.is_file():
            print(f"Missing {required.relative_to(project)}", file=sys.stderr)
            return 1
    data = json.loads(ocr_path.read_text(encoding="utf-8"))
    source = Image.open(project / data["page_image"]).convert("RGB")
    canvas_w = data["canvas"][0]
    low_res = source.size[0] < canvas_w
    target = Image.open(inpainted_path).convert("RGB") if low_res else source
    size = target.size
    scale = size[0] / canvas_w
    pad = args.pad * scale
    boxes = []
    for block in data["blocks"]:
        if block.get("skip"):
            continue
        for line in block["lines"]:
            boxes.append((line["x"] * scale - pad, line["y"] * scale - pad,
                          (line["x"] + line["w"]) * scale + pad, (line["y"] + line["h"]) * scale + pad))
    out = project / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    if low_res:
        target.save(out)
        print(f"{out.relative_to(project)}: page image is {source.size[0]} px wide for a {canvas_w} px canvas, "
              f"so the generated image is kept whole at {size[0]}x{size[1]} instead of merging upscaled source pixels")
    else:
        from image_layers import layer_alpha

        inpainted = Image.open(inpainted_path).convert("RGB").resize(size, Image.LANCZOS)
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        for box in boxes:
            draw.rectangle(box, fill=255)
        for layer in args.layer:
            alpha = layer_alpha(Image.open(project / layer).resize(size, Image.LANCZOS))
            grown = Image.fromarray((alpha * 255).astype("uint8")).filter(ImageFilter.MaxFilter(2 * int(pad) + 1))
            mask.paste(255, mask=grown)
        mask = mask.filter(ImageFilter.GaussianBlur(2 * scale))
        Image.composite(inpainted, source, mask).save(out)
        print(f"{out.relative_to(project)}: {len(boxes)} text box(es) and {len(args.layer)} removed layer(s) "
              "from the inpainted image, source pixels elsewhere")
    residue = find_residue(out, boxes)
    if residue is None:
        print("Residue check skipped: OCR is not installed; inspect the base for leftover text.", file=sys.stderr)
        return 0
    if residue:
        print(f"Residue: {len(residue)} text line(s) left inside the removal boxes:")
        for text in residue:
            print(f"  {text}")
        return 3
    print("Residue: none")
    return 0


def find_residue(image_path: Path, boxes: list[tuple[float, float, float, float]]) -> Optional[list[str]]:
    """OCR the merged base; return text whose center lies in a removal box, or None without OCR."""
    try:
        from rapidocr import RapidOCR
    except ImportError:
        return None
    result = RapidOCR()(str(image_path))
    if result.boxes is None:
        return []
    found = []
    for box, text, score in zip(result.boxes, result.txts, result.scores):
        if float(score) < RESIDUE_MIN_SCORE or not any(char.isalnum() for char in str(text)):
            continue
        cx = sum(float(point[0]) for point in box) / len(box)
        cy = sum(float(point[1]) for point in box) / len(box)
        if any(left <= cx <= right and top <= cy <= bottom for left, top, right, bottom in boxes):
            found.append(str(text))
    return found


def num(value: float) -> str:
    """Compact decimal: one place at most, no trailing zero."""
    return f"{round(value, 1):g}"


def widen_zones(boxes: list[list[float]], canvas_w: float) -> None:
    """Extend each zone's right edge to its nearest right-hand neighbor, or near the canvas edge."""
    for box in boxes:
        limit = canvas_w - 8
        for other in boxes:
            if other is box or other[0] <= box[0] or other[1] >= box[3] or box[1] >= other[3]:
                continue
            limit = min(limit, other[0] - 2)
        box[2] = max(box[2], limit)


def separate_zones(boxes: list[list[float]]) -> None:
    """Split overlapping [left, top, right, bottom] zones at the midpoint of their overlap."""
    for _ in range(3):
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if a[0] >= b[2] or b[0] >= a[2] or a[1] >= b[3] or b[1] >= a[3]:
                    continue
                overlap_w = min(a[2], b[2]) - max(a[0], b[0])
                overlap_h = min(a[3], b[3]) - max(a[1], b[1])
                stacked = (a[1] < b[1] and a[3] < b[3]) or (b[1] < a[1] and b[3] < a[3])
                if stacked and overlap_h <= overlap_w:
                    upper, lower = (a, b) if a[1] <= b[1] else (b, a)
                    middle = (min(upper[3], lower[3]) + max(upper[1], lower[1])) / 2
                    upper[3], lower[1] = middle, middle
                else:
                    first, second = (a, b) if a[0] <= b[0] else (b, a)
                    middle = (min(first[2], second[2]) + max(first[0], second[0])) / 2
                    first[2], second[0] = middle, middle


def cmd_text_layer(args: argparse.Namespace) -> int:
    project = Path(args.project_path).resolve()
    ocr_path = project / OCR_DIR / f"{args.page}.json"
    base = project / args.base
    if not ocr_path.is_file():
        print(f"Missing {OCR_DIR}/{args.page}.json; run scan first.", file=sys.stderr)
        return 1
    if not base.is_file():
        print(f"Missing base image: {args.base}", file=sys.stderr)
        return 1
    data = json.loads(ocr_path.read_text(encoding="utf-8"))
    canvas_w, canvas_h = data["canvas"]
    blocks = [block for block in data["blocks"] if not block.get("skip")]
    body = family_stack(args.font)
    title = family_stack(args.title_font or args.font)
    largest = max((block["font_size"] for block in blocks), default=0)

    out = project / args.out
    href = Path("..", base.relative_to(project)).as_posix() if out.parent.name == "svg_output" else base.as_posix()
    root = f'viewBox="0 0 {canvas_w} {canvas_h}" font-family={quoteattr(body)}'
    if args.lang:
        root += f" lang={quoteattr(args.lang)}"
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" {root} data-pptx-page-role="{args.page_role}">',
        f'  <image id="page-base" data-pptx-role="background" href={quoteattr(href)} '
        f'x="0" y="0" width="{canvas_w}" height="{canvas_h}" preserveAspectRatio="none"/>',
    ]
    placed = []
    title_done = False
    for block in blocks:
        size = block["font_size"]
        is_title = not title_done and size >= 0.85 * largest
        title_done = title_done or is_title
        lines = block["lines"]
        texts = [line["text"] for line in lines]
        if is_monospace(title if is_title else body):
            size = estimate_font_size([Line(text=l["text"], score=1, x=l["x"], y=l["y"], w=l["w"], h=l["h"])
                                       for l in lines], mono_units)
        x = round(min(line["x"] for line in lines), 1)
        baselines = [round(line["y"] + line["h"] / 2 + 0.36 * size, 1) for line in lines]
        units = mono_units if is_monospace(title if is_title else body) else text_units
        width = max(max(line["w"] for line in lines), max(units(t) for t in texts) * size * 1.1)
        left = max(x - 4, 0)
        placed.append({
            "id": "title" if is_title else block["id"],
            "is_title": is_title,
            "x": x, "size": size, "color": block["color"], "texts": texts, "baselines": baselines,
            "box": [left, max(baselines[0] - 0.85 * size - 4, 0),
                    min(left + width + 8, canvas_w), min(baselines[-1] + 0.35 * size + 4, canvas_h)],
        })
    widen_zones([item["box"] for item in placed], canvas_w)
    separate_zones([item["box"] for item in placed])
    for item in placed:
        x, baselines, texts = item["x"], item["baselines"], item["texts"]
        content = escape(texts[0])
        for previous, current, text in zip(baselines, baselines[1:], texts[1:]):
            content += f'<tspan x="{num(x)}" dy="{num(current - previous)}">{escape(text)}</tspan>'
        left, top, right, bottom = item["box"]
        family = f" font-family={quoteattr(title)}" if item["is_title"] and title != body else ""
        svg.append(f'  <g id="{item["id"]}" data-pptx-bounds="{num(left)} {num(top)} '
                   f'{num(right - left)} {num(bottom - top)}">')
        svg.append(f'    <text x="{num(x)}" y="{num(baselines[0])}"{family} font-size="{num(item["size"])}" '
                   f'fill="{item["color"]}">{content}</text>')
        svg.append("  </g>")
    svg.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(out.relative_to(project))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OCR page images and write quick-restore text layers for Image to PPTX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="OCR page images into analysis/ocr/<stem>.json.")
    scan.add_argument("project_path")
    scan.add_argument("pages", nargs="+", help="Page images, absolute or relative to the project.")
    scan.add_argument("--canvas", type=parse_canvas, default=(1280, 720),
                      help="Canvas size in px the coordinates map to (default 1280x720).")
    scan.set_defaults(func=cmd_scan)

    merge = sub.add_parser("merge-base", help="Composite an inpainted image into the source inside text boxes only.")
    merge.add_argument("project_path")
    merge.add_argument("--page", required=True, help="Page image stem used by scan.")
    merge.add_argument("--inpainted", required=True, help="Text-removed image, relative to the project.")
    merge.add_argument("--out", required=True, help="Merged base PNG, relative to the project.")
    merge.add_argument("--pad", type=float, default=6.0, help="Canvas px added around each OCR line box (default 6).")
    merge.add_argument("--layer", action="append", default=[],
                       help="Extracted layer whose area also takes inpainted pixels (repeatable; RGBA or flat key).")
    merge.set_defaults(func=cmd_merge_base)

    layer = sub.add_parser("text-layer", help="Write a quick-restore page SVG from a base image and reviewed OCR.")
    layer.add_argument("project_path")
    layer.add_argument("--page", required=True, help="Page image stem used by scan.")
    layer.add_argument("--base", required=True, help="Text-free base image, relative to the project.")
    layer.add_argument("--out", required=True, help="Output SVG, relative to the project (svg_output/<name>.svg).")
    layer.add_argument("--font", required=True, help="Body font stack, e.g. 'Microsoft YaHei, Arial'.")
    layer.add_argument("--title-font", help="Font stack for the largest block (default: --font).")
    layer.add_argument("--lang", help="BCP-47 deck language for the root lang attribute.")
    layer.add_argument("--page-role", default="content",
                       choices=["cover", "toc", "section", "content", "ending"])
    layer.set_defaults(func=cmd_text_layer)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
