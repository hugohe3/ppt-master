#!/usr/bin/env python3
"""Internal helper: extract lightweight template assets and style metadata from a PPTX file.

This helper is intentionally limited in scope:
- extract reusable media assets
- summarize slide size, theme colors, and fonts
- infer common background assets through slide/layout/master inheritance
- produce a compact manifest for downstream template reconstruction

It does NOT try to convert arbitrary PPTX shapes into SVG templates.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

EMU_PER_INCH = 914400

SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
LAYOUT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
MASTER_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster"
THEME_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

THANKS_KEYWORDS = ("thank", "thanks", "q&a", "qa", "contact", "致谢", "谢谢", "感谢", "答疑", "联系方式")
TOC_KEYWORDS = ("agenda", "contents", "content", "outline", "目录", "议程", "目录页")
CHAPTER_KEYWORDS = ("chapter", "part", "section", "章节", "部分")


@dataclass
class SlideRecord:
    index: int
    name: str
    slide_path: str
    layout_path: str | None
    master_path: str | None
    background_asset: str | None
    background_source: str | None
    image_assets: list[str]
    text_samples: list[str]
    text_count: int
    shape_count: int
    page_type: str


def normalize_part(path: str, base: str | None = None) -> str:
    if base:
        path = str(PurePosixPath(base).parent.joinpath(path))
    path = path.replace("\\", "/")
    normalized = posixpath.normpath(path)
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def rels_path_for(part_path: str) -> str:
    part = PurePosixPath(part_path)
    return str(part.parent / "_rels" / f"{part.name}.rels")


def load_xml_from_zip(zf: zipfile.ZipFile, part_path: str) -> ET.Element | None:
    try:
        with zf.open(part_path) as fh:
            return ET.parse(fh).getroot()
    except KeyError:
        return None
    except ET.ParseError:
        return None


def parse_relationships(zf: zipfile.ZipFile, part_path: str) -> dict[str, dict[str, str]]:
    rels_root = load_xml_from_zip(zf, rels_path_for(part_path))
    if rels_root is None:
        return {}

    rels: dict[str, dict[str, str]] = {}
    for rel in rels_root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        rel_type = rel.attrib.get("Type")
        if not rel_id or not target or not rel_type:
            continue
        rels[rel_id] = {
            "type": rel_type,
            "target": normalize_part(target, part_path),
        }
    return rels


def emu_to_pixels(value: int) -> int:
    # PowerPoint uses 96 dpi; enough for summary output.
    return int(round(value / EMU_PER_INCH * 96))


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._") or "asset"


def extract_text_samples(root: ET.Element | None, limit: int = 6) -> list[str]:
    if root is None:
        return []
    samples: list[str] = []
    for node in root.findall(".//a:t", NS):
        text = (node.text or "").strip()
        if not text:
            continue
        samples.append(text)
        if len(samples) >= limit:
            break
    return samples


def extract_image_targets(root: ET.Element | None, rels: dict[str, dict[str, str]]) -> list[str]:
    if root is None:
        return []
    targets: list[str] = []
    seen: set[str] = set()
    for blip in root.findall(".//a:blip", NS):
        rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
        if not rel_id:
            continue
        rel = rels.get(rel_id)
        if not rel or rel["type"] != IMAGE_REL:
            continue
        target = rel["target"]
        if target in seen:
            continue
        seen.add(target)
        targets.append(target)
    return targets


def detect_background_asset(root: ET.Element | None, rels: dict[str, dict[str, str]]) -> str | None:
    if root is None:
        return None

    bg = root.find("p:cSld/p:bg", NS)
    if bg is None:
        bg = root.find("p:bg", NS)
    if bg is None:
        return None

    blip = bg.find(".//a:blip", NS)
    if blip is None:
        return None

    rel_id = blip.attrib.get(f"{{{NS['r']}}}embed")
    if not rel_id:
        return None
    rel = rels.get(rel_id)
    if not rel or rel["type"] != IMAGE_REL:
        return None
    return rel["target"]


def count_slide_shapes(root: ET.Element | None) -> int:
    if root is None:
        return 0
    sp_tree = root.find("p:cSld/p:spTree", NS)
    if sp_tree is None:
        return 0
    return len(list(sp_tree))


def classify_slide(index: int, total: int, texts: list[str], image_count: int, shape_count: int) -> str:
    joined = " ".join(texts).lower()
    if any(keyword in joined for keyword in THANKS_KEYWORDS):
        return "ending_candidate"
    if any(keyword in joined for keyword in TOC_KEYWORDS):
        return "toc_candidate"
    if any(keyword in joined for keyword in CHAPTER_KEYWORDS):
        return "chapter_candidate"
    if index == 1 and image_count <= 3:
        return "cover_candidate"
    if index == total and len(texts) <= 6:
        return "ending_candidate"
    if len(texts) <= 3 and shape_count <= 12:
        return "chapter_candidate"
    return "content_candidate"


def parse_theme(root: ET.Element | None) -> dict[str, Any]:
    if root is None:
        return {"colors": {}, "fonts": {}}

    colors: dict[str, str] = {}
    clr_scheme = root.find(".//a:clrScheme", NS)
    if clr_scheme is not None:
        for child in list(clr_scheme):
            if not isinstance(child.tag, str):
                continue
            name = child.tag.split("}", 1)[-1]
            srgb = child.find("a:srgbClr", NS)
            sys_clr = child.find("a:sysClr", NS)
            if srgb is not None and "val" in srgb.attrib:
                colors[name] = f"#{srgb.attrib['val']}"
            elif sys_clr is not None:
                last = sys_clr.attrib.get("lastClr")
                if last:
                    colors[name] = f"#{last}"

    fonts: dict[str, str] = {}
    font_scheme = root.find(".//a:fontScheme", NS)
    if font_scheme is not None:
        major = font_scheme.find("a:majorFont", NS)
        minor = font_scheme.find("a:minorFont", NS)
        if major is not None:
            latin = major.find("a:latin", NS)
            if latin is not None and latin.attrib.get("typeface"):
                fonts["majorLatin"] = latin.attrib["typeface"]
        if minor is not None:
            latin = minor.find("a:latin", NS)
            if latin is not None and latin.attrib.get("typeface"):
                fonts["minorLatin"] = latin.attrib["typeface"]
            ea = minor.find("a:ea", NS)
            if ea is not None and ea.attrib.get("typeface"):
                fonts["minorEastAsia"] = ea.attrib["typeface"]

    return {"colors": colors, "fonts": fonts}


def choose_common_assets(asset_usage: Counter[str]) -> list[str]:
    common = [asset for asset, count in asset_usage.items() if count > 1]
    return sorted(common)


def write_analysis(
    output_path: Path,
    pptx_name: str,
    slide_size: dict[str, int],
    theme: dict[str, Any],
    slides: list[SlideRecord],
    common_assets: list[str],
) -> None:
    lines = [
        f"# Template Import Analysis - {pptx_name}",
        "",
        "## Summary",
        f"- Slide size: {slide_size['width_px']} x {slide_size['height_px']} px",
        f"- Theme colors: {', '.join(sorted(theme['colors'].keys())) or 'none detected'}",
        f"- Theme fonts: {', '.join(f'{k}={v}' for k, v in theme['fonts'].items()) or 'none detected'}",
        f"- Common assets: {len(common_assets)}",
        "",
        "## Slide Candidates",
    ]

    for slide in slides:
        sample = " | ".join(slide.text_samples[:3]) if slide.text_samples else "(no text sample)"
        lines.extend(
            [
                f"- Slide {slide.index}: {slide.page_type}",
                f"  - Name: {slide.name}",
                f"  - Background: {slide.background_asset or 'none'} ({slide.background_source or 'n/a'})",
                f"  - Images: {len(slide.image_assets)}",
                f"  - Text sample: {sample}",
            ]
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_manifest(pptx_path: Path, output_dir: Path) -> dict[str, Any]:
    with zipfile.ZipFile(pptx_path, "r") as zf:
        presentation_root = load_xml_from_zip(zf, "ppt/presentation.xml")
        if presentation_root is None:
            raise RuntimeError("Invalid PPTX: missing ppt/presentation.xml")

        slide_size = {"width_emu": 0, "height_emu": 0, "width_px": 0, "height_px": 0}
        sld_sz = presentation_root.find("p:sldSz", NS)
        if sld_sz is not None:
            width_emu = int(sld_sz.attrib.get("cx", "0"))
            height_emu = int(sld_sz.attrib.get("cy", "0"))
            slide_size = {
                "width_emu": width_emu,
                "height_emu": height_emu,
                "width_px": emu_to_pixels(width_emu),
                "height_px": emu_to_pixels(height_emu),
            }

        presentation_rels = parse_relationships(zf, "ppt/presentation.xml")
        slide_parts: list[str] = []
        for sld_id in presentation_root.findall("p:sldIdLst/p:sldId", NS):
            rel_id = sld_id.attrib.get(f"{{{NS['r']}}}id")
            rel = presentation_rels.get(rel_id or "")
            if rel and rel["type"] == SLIDE_REL:
                slide_parts.append(rel["target"])

        asset_dir = output_dir / "assets"
        asset_dir.mkdir(parents=True, exist_ok=True)

        copied_assets: dict[str, str] = {}
        for info in zf.infolist():
            if not info.filename.startswith("ppt/media/") or info.is_dir():
                continue
            original_name = PurePosixPath(info.filename).name
            safe_name = sanitize_filename(original_name)
            destination = asset_dir / safe_name
            stem = destination.stem
            suffix = destination.suffix
            counter = 2
            while destination.exists():
                destination = asset_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            with zf.open(info.filename) as src, open(destination, "wb") as dst:
                shutil.copyfileobj(src, dst)
            copied_assets[info.filename] = destination.name

        slide_records: list[SlideRecord] = []
        asset_usage: Counter[str] = Counter()

        theme_summary = {"colors": {}, "fonts": {}}

        for index, slide_path in enumerate(slide_parts, 1):
            slide_root = load_xml_from_zip(zf, slide_path)
            slide_rels = parse_relationships(zf, slide_path)

            layout_path = None
            for rel in slide_rels.values():
                if rel["type"] == LAYOUT_REL:
                    layout_path = rel["target"]
                    break

            layout_root = load_xml_from_zip(zf, layout_path) if layout_path else None
            layout_rels = parse_relationships(zf, layout_path) if layout_path else {}

            master_path = None
            for rel in layout_rels.values():
                if rel["type"] == MASTER_REL:
                    master_path = rel["target"]
                    break

            master_root = load_xml_from_zip(zf, master_path) if master_path else None
            master_rels = parse_relationships(zf, master_path) if master_path else {}

            theme_path = None
            for rel in master_rels.values():
                if rel["type"] == THEME_REL:
                    theme_path = rel["target"]
                    break
            if theme_path and not theme_summary["colors"] and not theme_summary["fonts"]:
                theme_summary = parse_theme(load_xml_from_zip(zf, theme_path))

            bg_asset = None
            bg_source = None
            for label, root, rels in (
                ("slide", slide_root, slide_rels),
                ("layout", layout_root, layout_rels),
                ("master", master_root, master_rels),
            ):
                candidate = detect_background_asset(root, rels)
                if candidate:
                    bg_asset = candidate
                    bg_source = label
                    break

            image_targets = extract_image_targets(slide_root, slide_rels)
            texts = extract_text_samples(slide_root)
            shape_count = count_slide_shapes(slide_root)
            page_type = classify_slide(index, len(slide_parts), texts, len(image_targets), shape_count)

            resolved_bg = copied_assets.get(bg_asset, PurePosixPath(bg_asset).name if bg_asset else None)
            resolved_images = [
                copied_assets.get(target, PurePosixPath(target).name)
                for target in image_targets
            ]

            if resolved_bg:
                asset_usage[resolved_bg] += 1
            for asset_name in resolved_images:
                asset_usage[asset_name] += 1

            slide_records.append(
                SlideRecord(
                    index=index,
                    name=PurePosixPath(slide_path).name,
                    slide_path=slide_path,
                    layout_path=layout_path,
                    master_path=master_path,
                    background_asset=resolved_bg,
                    background_source=bg_source,
                    image_assets=resolved_images,
                    text_samples=texts,
                    text_count=len(texts),
                    shape_count=shape_count,
                    page_type=page_type,
                )
            )

        common_assets = choose_common_assets(asset_usage)
        page_type_map: dict[str, list[int]] = defaultdict(list)
        for slide in slide_records:
            page_type_map[slide.page_type].append(slide.index)

        manifest = {
            "source": {
                "pptx": str(pptx_path),
                "name": pptx_path.name,
            },
            "slideSize": slide_size,
            "theme": theme_summary,
            "assets": {
                "exportDir": "assets",
                "commonAssets": common_assets,
                "allAssets": sorted(copied_assets.values()),
            },
            "pageTypeCandidates": dict(sorted(page_type_map.items())),
            "slides": [
                {
                    "index": slide.index,
                    "name": slide.name,
                    "slidePath": slide.slide_path,
                    "layoutPath": slide.layout_path,
                    "masterPath": slide.master_path,
                    "backgroundAsset": slide.background_asset,
                    "backgroundSource": slide.background_source,
                    "imageAssets": slide.image_assets,
                    "textSamples": slide.text_samples,
                    "textCount": slide.text_count,
                    "shapeCount": slide.shape_count,
                    "pageType": slide.page_type,
                }
                for slide in slide_records
            ],
        }

        write_analysis(
            output_dir / "analysis.md",
            pptx_path.name,
            slide_size,
            theme_summary,
            slide_records,
            common_assets,
        )
        return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract reusable assets and style metadata from a PPTX template source."
    )
    parser.add_argument("pptx_file", help="Path to the source .pptx file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: <pptx_stem>_template_import beside the source file)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pptx_path = Path(args.pptx_file).expanduser().resolve()
    if not pptx_path.exists():
        print(f"Error: file does not exist: {pptx_path}")
        return 1
    if pptx_path.suffix.lower() != ".pptx":
        print(f"Error: expected a .pptx file, got: {pptx_path.name}")
        return 1

    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pptx_path.with_name(f"{pptx_path.stem}_template_import")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        manifest = build_manifest(pptx_path, output_dir)
    except Exception as exc:
        print(f"Error: failed to import template source: {exc}")
        return 1

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Imported PPTX template source: {pptx_path.name}")
    print(f"Output directory: {output_dir}")
    print(f"Manifest: {manifest_path.name}")
    print(f"Assets exported: {len(manifest['assets']['allAssets'])}")
    print(f"Common assets: {len(manifest['assets']['commonAssets'])}")
    print(f"Slides analyzed: {len(manifest['slides'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
