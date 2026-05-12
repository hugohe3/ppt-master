#!/usr/bin/env python3
"""
PowerPoint to Markdown Converter

Extracts slide text, tables, speaker notes, and embedded pictures from
Open XML PowerPoint files into Markdown.

Primary use case: PPTX source decks -> Markdown for PPT generation input.

Dependency:
    pip install python-pptx
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn


EMU_PER_INCH = 914400
OFFICE_VECTOR_EXTENSIONS = {"emf", "wmf"}
IMAGE_EXT_BY_CONTENT_TYPE = {
    "image/bmp": "bmp",
    "image/gif": "gif",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/svg+xml": "svg",
    "image/tiff": "tiff",
    "image/x-emf": "emf",
    "image/x-wmf": "wmf",
}
LEGACY_GENERATED_IMAGE_RE = re.compile(r"^slide_\d{2}_image_\d{2}\.[A-Za-z0-9]+$")


SUPPORTED_FORMATS = {
    ".pptx": "PowerPoint Presentation",
    ".pptm": "Macro-enabled PowerPoint Presentation",
    ".ppsx": "PowerPoint Slide Show",
    ".ppsm": "Macro-enabled PowerPoint Slide Show",
    ".potx": "PowerPoint Template",
    ".potm": "Macro-enabled PowerPoint Template",
}


@dataclass
class LeafShape:
    """Flattened leaf shape with stable position ordering."""

    shape: object
    top: int
    left: int


@dataclass
class SavedPicture:
    """Extracted image asset plus manifest metadata."""

    filename: str
    manifest_entry: dict[str, object]
    is_new_asset: bool


def normalize_text(value: str) -> str:
    """Collapse whitespace while preserving paragraph boundaries elsewhere."""
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.split("\n")]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def normalize_ext(ext: str | None, content_type: str | None = None) -> str:
    """Return a lowercase extension without a leading dot."""
    if ext:
        ext = ext.lower().lstrip(".")
        if ext == "jpeg":
            return "jpg"
        return ext
    if content_type:
        return IMAGE_EXT_BY_CONTENT_TYPE.get(content_type.lower(), "bin")
    return "bin"


def sanitize_filename(value: str) -> str:
    """Return a filesystem-safe basename."""
    value = re.sub(r"[^\w.\-]+", "_", value, flags=re.UNICODE)
    return value.strip("._") or "asset"


def escape_table_cell(value: str) -> str:
    """Escape Markdown table syntax inside a cell."""
    return normalize_text(value).replace("|", r"\|") or " "


def iter_leaf_shapes(shapes: object) -> list[LeafShape]:
    """Return a flattened, reading-order list of shapes."""
    items: list[LeafShape] = []
    for shape in shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            items.extend(iter_leaf_shapes(shape.shapes))
            continue
        items.append(
            LeafShape(
                shape=shape,
                top=int(getattr(shape, "top", 0) or 0),
                left=int(getattr(shape, "left", 0) or 0),
            )
        )
    items.sort(key=lambda item: (item.top, item.left))
    return items


def text_frame_to_markdown(text_frame: object) -> str:
    """Convert a PowerPoint text frame into Markdown."""
    paragraphs = []
    visible_paragraphs = [
        paragraph for paragraph in text_frame.paragraphs
        if normalize_text(paragraph.text)
    ]
    if not visible_paragraphs:
        return ""

    list_like = any(paragraph.level > 0 for paragraph in visible_paragraphs)
    if not list_like:
        list_like = len(visible_paragraphs) > 1

    for paragraph in visible_paragraphs:
        text = normalize_text(paragraph.text)
        if not text:
            continue
        if list_like:
            indent = "  " * max(paragraph.level, 0)
            paragraphs.append(f"{indent}- {text}")
        else:
            paragraphs.append(text)

    if list_like:
        return "\n".join(paragraphs)
    return "\n\n".join(paragraphs)


def table_to_markdown(table: object) -> str:
    """Convert a PowerPoint table to a Markdown table."""
    rows = []
    for row in table.rows:
        cells = [escape_table_cell(cell.text) for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ""

    column_count = max(len(row) for row in rows)
    normalized_rows = [row + [" "] * (column_count - len(row)) for row in rows]
    header = normalized_rows[0]
    separator = ["---"] * column_count
    body = normalized_rows[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _image_part_for_shape(shape: object) -> object | None:
    """Return the first embedded image part referenced by a shape."""
    element = getattr(shape, "element", None)
    part = getattr(shape, "part", None)
    if element is None or part is None:
        return None

    try:
        blips = element.xpath(".//a:blip")
    except Exception:
        return None

    for blip in blips:
        rel_id = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
        if not rel_id:
            continue
        try:
            return part.related_part(rel_id)
        except Exception:
            continue
    return None


def _image_size_from_bytes(blob: bytes) -> tuple[int | None, int | None]:
    """Return bitmap dimensions when Pillow can decode the bytes."""
    try:
        from PIL import Image
    except ImportError:
        return None, None
    try:
        with Image.open(BytesIO(blob)) as img:
            return img.width, img.height
    except (OSError, ValueError):
        return None, None


def _shape_emu(shape: object, attr: str) -> int:
    value = getattr(shape, attr, 0) or 0
    return int(value)


def _shape_occurrence(
    shape: object,
    slide_index: int,
) -> dict[str, object]:
    """Return slide-specific image placement metadata."""
    display_width_emu = _shape_emu(shape, "width")
    display_height_emu = _shape_emu(shape, "height")
    display_ratio = (
        display_width_emu / display_height_emu
        if display_width_emu > 0 and display_height_emu > 0
        else None
    )
    return {
        "slide_index": slide_index,
        "shape_name": str(getattr(shape, "name", "")),
        "display_left_emu": _shape_emu(shape, "left"),
        "display_top_emu": _shape_emu(shape, "top"),
        "display_width_emu": display_width_emu,
        "display_height_emu": display_height_emu,
        "display_width_in": round(display_width_emu / EMU_PER_INCH, 4) if display_width_emu else None,
        "display_height_in": round(display_height_emu / EMU_PER_INCH, 4) if display_height_emu else None,
        "display_ratio": round(display_ratio, 6) if display_ratio else None,
    }


def _update_manifest_usage(entry: dict[str, object]) -> None:
    """Refresh aggregate fields after adding an occurrence."""
    occurrences = entry.get("occurrences")
    if not isinstance(occurrences, list):
        occurrences = []
    entry["usage_count"] = len(occurrences)
    ratios = sorted({
        occurrence.get("display_ratio")
        for occurrence in occurrences
        if isinstance(occurrence, dict)
        and isinstance(occurrence.get("display_ratio"), (int, float))
    })
    if ratios:
        entry["display_ratio_variants"] = ratios
        if entry.get("display_ratio") is None:
            entry["display_ratio"] = ratios[0]


def _manifest_entry(
    *,
    index: int,
    filename: str,
    image_part: object,
    ext: str,
    blob: bytes,
    occurrence: dict[str, object],
) -> dict[str, object]:
    """Build image_manifest.json metadata for one unique PowerPoint media part."""
    pixel_width, pixel_height = _image_size_from_bytes(blob)
    pixel_ratio = (
        pixel_width / pixel_height
        if pixel_width and pixel_height
        else None
    )
    is_office_vector = ext in OFFICE_VECTOR_EXTENSIONS
    partname = str(getattr(image_part, "partname", ""))
    content_type = str(getattr(image_part, "content_type", ""))

    entry: dict[str, object] = {
        "index": index,
        "filename": filename,
        "original_filename": filename,
        "asset_kind": "office_vector" if is_office_vector else "bitmap",
        "svg_renderable": not is_office_vector,
        "pptx_native_supported": True,
        "source_kind": "pptx_picture",
        "source_ext": f".{ext}",
        "source_target": partname.lstrip("/"),
        "content_type": content_type,
        "display_left_emu": occurrence.get("display_left_emu"),
        "display_top_emu": occurrence.get("display_top_emu"),
        "display_width_emu": occurrence.get("display_width_emu"),
        "display_height_emu": occurrence.get("display_height_emu"),
        "display_width_in": occurrence.get("display_width_in"),
        "display_height_in": occurrence.get("display_height_in"),
        "display_ratio": occurrence.get("display_ratio"),
        "pixel_width": pixel_width,
        "pixel_height": pixel_height,
        "pixel_ratio": round(pixel_ratio, 6) if pixel_ratio else None,
        "occurrences": [occurrence],
    }
    if entry["display_ratio"] is None and pixel_ratio:
        entry["display_ratio"] = round(pixel_ratio, 6)
    _update_manifest_usage(entry)
    return entry


def _asset_cache_key(image_part: object, blob: bytes) -> str:
    """Return a stable key for deduplicating repeated PPTX media references."""
    partname = str(getattr(image_part, "partname", ""))
    if partname:
        return partname
    return hashlib.sha256(blob).hexdigest()


def _asset_filename(
    image_part: object,
    ext: str,
    asset_index: int,
    used_filenames: set[str],
) -> str:
    """Return a unique asset filename, preferring the PPTX media basename."""
    partname = str(getattr(image_part, "partname", ""))
    base = sanitize_filename(Path(partname).name) if partname else f"image_{asset_index:03d}.{ext}"
    if "." not in base:
        base = f"{base}.{ext}"
    if base not in used_filenames:
        used_filenames.add(base)
        return base

    path = Path(base)
    stem = path.stem
    suffix = path.suffix or f".{ext}"
    counter = 2
    while True:
        candidate = f"{stem}_{counter}{suffix}"
        if candidate not in used_filenames:
            used_filenames.add(candidate)
            return candidate
        counter += 1


def save_picture(
    shape: object,
    asset_dir: Path,
    slide_index: int,
    asset_index: int,
    asset_cache: dict[str, SavedPicture],
    used_filenames: set[str],
) -> SavedPicture | None:
    """Persist a shape image to the output asset directory."""
    image_part = _image_part_for_shape(shape)
    if image_part is None:
        return None

    content_type = getattr(image_part, "content_type", None)
    part_ext = getattr(getattr(image_part, "partname", None), "ext", None)
    ext = normalize_ext(part_ext, content_type)
    blob = bytes(getattr(image_part, "blob", b""))
    if not blob:
        return None

    occurrence = _shape_occurrence(shape, slide_index)
    cache_key = _asset_cache_key(image_part, blob)
    cached = asset_cache.get(cache_key)
    if cached is not None:
        occurrences = cached.manifest_entry.setdefault("occurrences", [])
        if isinstance(occurrences, list):
            occurrences.append(occurrence)
        _update_manifest_usage(cached.manifest_entry)
        return SavedPicture(
            filename=cached.filename,
            manifest_entry=cached.manifest_entry,
            is_new_asset=False,
        )

    filename = _asset_filename(image_part, ext, asset_index, used_filenames)
    output_path = asset_dir / filename
    output_path.write_bytes(blob)
    saved = SavedPicture(
        filename=filename,
        manifest_entry=_manifest_entry(
            index=asset_index,
            filename=filename,
            image_part=image_part,
            ext=ext,
            blob=blob,
            occurrence=occurrence,
        ),
        is_new_asset=True,
    )
    asset_cache[cache_key] = saved
    return saved


def _reset_generated_asset_dir(asset_dir: Path) -> None:
    """Remove a previously generated asset directory."""
    if not asset_dir.exists():
        return
    if not (asset_dir / "image_manifest.json").is_file():
        for path in asset_dir.iterdir():
            if path.is_file() and LEGACY_GENERATED_IMAGE_RE.match(path.name):
                path.unlink()
        return
    shutil.rmtree(asset_dir)


def extract_notes(slide: object) -> str:
    """Extract speaker notes text from a slide, if available."""
    try:
        notes_slide = slide.notes_slide
    except Exception:
        return ""

    blocks = []
    for item in iter_leaf_shapes(notes_slide.shapes):
        shape = item.shape
        if not getattr(shape, "has_text_frame", False):
            continue
        text = text_frame_to_markdown(shape.text_frame)
        if text:
            blocks.append(text)

    return "\n\n".join(blocks).strip()


def convert_presentation_to_markdown(
    input_path: str,
    output_path: str | None = None,
) -> str:
    """Convert a supported PowerPoint file to Markdown."""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_path}")
        return ""

    suffix = input_file.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS.keys()))
        print(f"[ERROR] Unsupported format: {suffix}")
        print(f"   Supported: {supported}")
        print("   Legacy .ppt files should be resaved as .pptx or exported to PDF first.")
        return ""

    print(f"[INFO] Converting {SUPPORTED_FORMATS[suffix]}: {input_file.name}")

    if output_path:
        out_file = Path(output_path)
    else:
        out_file = input_file.with_suffix(".md")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    asset_dir = out_file.parent / f"{out_file.stem}_files"
    _reset_generated_asset_dir(asset_dir)

    presentation = Presentation(str(input_file))
    lines = [
        f"# {input_file.stem}",
        "",
        f"- Source: `{input_file.name}`",
        f"- Total slides: {len(presentation.slides)}",
        "",
    ]

    image_count = 0
    image_ref_count = 0
    asset_dir_used = False
    image_manifest: list[dict[str, object]] = []
    asset_cache: dict[str, SavedPicture] = {}
    used_filenames: set[str] = set()

    for slide_index, slide in enumerate(presentation.slides, 1):
        lines.append(f"## Slide {slide_index}")
        lines.append("")

        blocks = []
        for item in iter_leaf_shapes(slide.shapes):
            shape = item.shape

            if getattr(shape, "has_table", False):
                table_md = table_to_markdown(shape.table)
                if table_md:
                    blocks.append(table_md)
                continue

            is_picture_shape = shape.shape_type in {
                MSO_SHAPE_TYPE.PICTURE,
                MSO_SHAPE_TYPE.LINKED_PICTURE,
            }
            has_shape_image = is_picture_shape or _image_part_for_shape(shape) is not None
            if has_shape_image:
                image_ref_count += 1
                next_image_index = image_count + 1
                asset_dir.mkdir(parents=True, exist_ok=True)
                saved_picture = save_picture(
                    shape,
                    asset_dir,
                    slide_index,
                    next_image_index,
                    asset_cache,
                    used_filenames,
                )
                if saved_picture is None:
                    if is_picture_shape:
                        blocks.append(f"> [Image] {getattr(shape, 'name', 'Picture')}")
                        continue
                else:
                    if saved_picture.is_new_asset:
                        image_count = next_image_index
                        image_manifest.append(saved_picture.manifest_entry)
                    asset_dir_used = True
                    blocks.append(
                        f"![Slide {slide_index} Image {image_ref_count}]"
                        f"({asset_dir.name}/{saved_picture.filename})"
                    )
                    if is_picture_shape:
                        continue

            if getattr(shape, "has_text_frame", False):
                text_md = text_frame_to_markdown(shape.text_frame)
                if text_md:
                    blocks.append(text_md)
                    continue

            if getattr(shape, "has_chart", False):
                blocks.append(f"> [Chart] {getattr(shape, 'name', 'Chart')}")

        if blocks:
            lines.append("\n\n".join(blocks))
            lines.append("")
        else:
            lines.append("_No extractable text content._")
            lines.append("")

        notes_md = extract_notes(slide)
        if notes_md:
            lines.append("### Speaker Notes")
            lines.append("")
            lines.append(notes_md)
            lines.append("")

    markdown_content = "\n".join(lines).strip() + "\n"
    out_file.write_text(markdown_content, encoding="utf-8")
    if image_manifest:
        (asset_dir / "image_manifest.json").write_text(
            json.dumps(image_manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"[OK] Saved Markdown to: {out_file}")
    if asset_dir_used:
        media_files = [
            path for path in asset_dir.iterdir()
            if path.is_file() and path.name != "image_manifest.json"
        ]
        print(f"   Extracted {len(media_files)} image file(s) -> {asset_dir}")
        if image_ref_count != len(media_files):
            print(
                f"   Deduplicated {image_ref_count} image reference(s) "
                f"into {len(media_files)} asset file(s)"
            )
        print(f"   Wrote image manifest -> {asset_dir / 'image_manifest.json'}")

    return markdown_content


def process_directory(input_dir: str, output_dir: str | None = None) -> None:
    """Convert all supported PowerPoint files in a directory to Markdown."""
    input_path = Path(input_dir)

    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = input_path

    presentation_files = sorted(
        path for path in input_path.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS
    )

    print(f"Found {len(presentation_files)} PowerPoint files")

    for presentation_file in presentation_files:
        output_file = output_path / f"{presentation_file.stem}.md"
        print(f"Processing: {presentation_file.name}")
        result = convert_presentation_to_markdown(str(presentation_file), str(output_file))
        if not result:
            print(f"[WARN] Skipped failed file: {presentation_file.name}")


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert PowerPoint files to Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ppt_to_md.py slides.pptx
  python ppt_to_md.py slides.pptx -o output.md
  python ppt_to_md.py ./decks
  python ppt_to_md.py ./decks -o ./markdown
  python ppt_to_md.py deck.ppsx -o notes/deck.md

Supported formats:
  .pptx  .pptm  .ppsx  .ppsm  .potx  .potm

Legacy .ppt is not parsed directly. Resave it as .pptx or export it to PDF first.
        """,
    )
    parser.add_argument("input", help="Input PowerPoint file or directory")
    parser.add_argument("-o", "--output", help="Output Markdown file or directory path")

    args = parser.parse_args()
    input_path = Path(args.input)

    if input_path.is_file():
        output = args.output or str(input_path.with_suffix(".md"))
        result = convert_presentation_to_markdown(str(input_path), output)
        sys.exit(0 if result else 1)
    if input_path.is_dir():
        process_directory(str(input_path), args.output)
        sys.exit(0)

    print(f"Error: File or directory not found: {args.input}")
    sys.exit(1)


if __name__ == "__main__":
    main()
