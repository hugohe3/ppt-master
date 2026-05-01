#!/usr/bin/env python3
"""Internal helper: optimize reference SVG files generated from PPTX/PDF exports.

This helper targets reference-quality SVGs used during template reconstruction.
It focuses on safe structural reductions:

- deduplicate identical clipPath definitions inside each SVG
- round excessive numeric precision in geometric attributes
- emit a small report with potential repeated icon/path candidates
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from .externalize_images import discover_svg_files
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from externalize_images import discover_svg_files  # type: ignore


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)
ET.register_namespace("inkscape", INKSCAPE_NS)

NS = {"svg": SVG_NS}
TAG_SUFFIX_RE = re.compile(r"\{[^}]+\}")
NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")

SAFE_ROUND_ATTRS = {
    "d",
    "transform",
    "x",
    "y",
    "x1",
    "x2",
    "y1",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "width",
    "height",
    "font-size",
    "stroke-width",
    "viewBox",
    "dx",
    "dy",
    "letter-spacing",
}


@dataclass
class OptimizeResult:
    svg_path: Path
    original_bytes: int
    optimized_bytes: int
    clip_paths_removed: int
    numeric_tokens_rounded: int
    flattened_tspans: int


def local_name(tag: str) -> str:
    return TAG_SUFFIX_RE.sub("", tag)


def format_number(value: float, precision: int) -> str:
    rounded = round(value, precision)
    if math.isclose(rounded, round(rounded), abs_tol=10 ** (-(precision + 1))):
        return str(int(round(rounded)))
    text = f"{rounded:.{precision}f}".rstrip("0").rstrip(".")
    return text if text != "-0" else "0"


def round_numbers_in_text(text: str, precision: int) -> tuple[str, int]:
    count = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal count
        raw = match.group(0)
        try:
            value = float(raw)
        except ValueError:
            return raw
        rounded = format_number(value, precision)
        if rounded != raw:
            count += 1
        return rounded

    return NUMBER_RE.sub(repl, text), count


def round_element_attributes(root: ET.Element, precision: int) -> int:
    rounded = 0
    for element in root.iter():
        for attr_name, attr_value in list(element.attrib.items()):
            if local_name(attr_name) not in SAFE_ROUND_ATTRS:
                continue
            updated, count = round_numbers_in_text(attr_value, precision)
            if count:
                element.set(attr_name, updated)
                rounded += count
    return rounded


def clip_signature(clip_element: ET.Element) -> str:
    payload = []
    for child in list(clip_element):
        payload.append(ET.tostring(child, encoding="unicode"))
    return "".join(payload)


def apply_id_remap(root: ET.Element, remap: dict[str, str]) -> None:
    if not remap:
        return
    for element in root.iter():
        for attr_name, attr_value in list(element.attrib.items()):
            updated = attr_value
            for old_id, new_id in remap.items():
                updated = updated.replace(f"url(#{old_id})", f"url(#{new_id})")
                updated = updated.replace(f"#{old_id}", f"#{new_id}")
            if updated != attr_value:
                element.set(attr_name, updated)


def deduplicate_clip_paths(root: ET.Element) -> int:
    removed = 0
    remap: dict[str, str] = {}

    for defs in root.findall(".//svg:defs", NS):
        seen: dict[str, str] = {}
        for clip in list(defs):
            if local_name(clip.tag) != "clipPath":
                continue
            clip_id = clip.attrib.get("id")
            if not clip_id:
                continue
            signature = clip_signature(clip)
            existing = seen.get(signature)
            if existing is None:
                seen[signature] = clip_id
                continue
            remap[clip_id] = existing
            defs.remove(clip)
            removed += 1

    apply_id_remap(root, remap)
    return removed


def collect_icon_candidates(root: ET.Element, svg_name: str) -> list[dict[str, str | int]]:
    candidates: list[dict[str, str | int]] = []
    for path in root.iter():
        if local_name(path.tag) != "path":
            continue
        d = path.attrib.get("d", "")
        if not d or len(d) > 220:
            continue
        if any(ancestor in d for ancestor in ("960V540", "1280V720")):
            continue
        candidates.append(
            {
                "file": svg_name,
                "d": d,
                "fill": path.attrib.get("fill", ""),
                "stroke": path.attrib.get("stroke", ""),
            }
        )
    return candidates


def flatten_single_tspan_text(root: ET.Element) -> int:
    flattened = 0
    for text_el in list(root.iter()):
        if local_name(text_el.tag) != "text":
            continue
        children = list(text_el)
        if len(children) != 1 or local_name(children[0].tag) != "tspan":
            continue
        tspan = children[0]
        if list(tspan):
            continue
        if (tspan.tail or "").strip():
            continue

        for attr_name, attr_value in list(tspan.attrib.items()):
            if attr_name not in text_el.attrib:
                text_el.set(attr_name, attr_value)
        text_el.text = tspan.text or ""
        text_el.remove(tspan)
        flattened += 1
    return flattened


def optimize_svg_file(svg_path: Path, precision: int) -> tuple[OptimizeResult, list[dict[str, str | int]]]:
    original_bytes = svg_path.stat().st_size
    root = ET.parse(svg_path).getroot()

    rounded = round_element_attributes(root, precision)
    clip_paths_removed = deduplicate_clip_paths(root)
    flattened_tspans = flatten_single_tspan_text(root)
    icon_candidates = collect_icon_candidates(root, svg_path.name)

    xml = ET.tostring(root, encoding="unicode")
    svg_path.write_text(xml, encoding="utf-8")

    return (
        OptimizeResult(
            svg_path=svg_path,
            original_bytes=original_bytes,
            optimized_bytes=svg_path.stat().st_size,
            clip_paths_removed=clip_paths_removed,
            numeric_tokens_rounded=rounded,
            flattened_tspans=flattened_tspans,
        ),
        icon_candidates,
    )


def write_component_reports(candidates: list[dict[str, str | int]], output_dir: Path) -> None:
    grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for item in candidates:
        grouped[(str(item["d"]), str(item["fill"]), str(item["stroke"]))].append(str(item["file"]))

    icon_report = []
    component_report = []
    for (d, fill, stroke), files in grouped.items():
        unique_files = sorted(set(files))
        if len(unique_files) < 2:
            continue
        record = {
            "files": unique_files,
            "fileCount": len(unique_files),
            "occurrences": len(files),
            "fill": fill,
            "stroke": stroke,
            "path": d,
        }
        icon_report.append(record)

        is_boundary = d in {"M0 540H960V0L0 0", "M0 540H960V0H0", "M0 540H960V0L00"}
        if fill and not stroke and not is_boundary and len(d) <= 120:
            component_report.append({**record, "kind": "decorative_component"})

    icon_report.sort(key=lambda item: (-item["fileCount"], -item["occurrences"], len(item["path"])))
    component_report.sort(key=lambda item: (-item["fileCount"], -item["occurrences"], len(item["path"])))
    (output_dir / "icon_candidates.json").write_text(
        json.dumps(icon_report[:200], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "template_component_candidates.json").write_text(
        json.dumps(component_report[:200], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def optimize_reference_batch(
    inputs: list[str],
    precision: int = 2,
) -> tuple[list[OptimizeResult], Path]:
    svg_files = discover_svg_files(inputs)
    if not svg_files:
        raise ValueError("no SVG files found")

    results: list[OptimizeResult] = []
    icon_candidates: list[dict[str, str | int]] = []
    for svg_file in svg_files:
        result, icons = optimize_svg_file(svg_file, precision=precision)
        results.append(result)
        icon_candidates.extend(icons)

    output_dir = svg_files[0].parent.parent if svg_files[0].parent.name == "svg" else svg_files[0].parent
    write_component_reports(icon_candidates, output_dir)
    return results, output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize reference SVG files by deduplicating clip paths and reducing numeric precision."
    )
    parser.add_argument("inputs", nargs="+", help="SVG files or directories")
    parser.add_argument(
        "--precision",
        type=int,
        default=2,
        help="Decimal precision for geometric attributes (default: 2)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results, output_dir = optimize_reference_batch(args.inputs, precision=args.precision)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    before = sum(item.original_bytes for item in results)
    after = sum(item.optimized_bytes for item in results)
    removed = sum(item.clip_paths_removed for item in results)
    rounded = sum(item.numeric_tokens_rounded for item in results)
    flattened = sum(item.flattened_tspans for item in results)

    print(f"Optimized SVG files: {len(results)}")
    print(f"SVG bytes: {before} -> {after}")
    print(f"Duplicate clipPaths removed: {removed}")
    print(f"Rounded numeric tokens: {rounded}")
    print(f"Flattened single-tspan texts: {flattened}")
    print(f"Icon candidate report: {output_dir / 'icon_candidates.json'}")
    print(f"Template component report: {output_dir / 'template_component_candidates.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
