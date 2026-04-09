#!/usr/bin/env python3
"""Internal helper: extract inline SVG images into external asset files.

This tool is the inverse of svg_finalize/embed_images.py. It is useful when
PowerPoint exports SVG files with large inline Base64 images and those SVGs need
to be reused as lightweight template references.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import os
import re
from dataclasses import dataclass
from pathlib import Path


DATA_URI_RE = re.compile(
    r'(?P<attr>(?:xlink:)?href)="data:(?P<mime>image/[^;"]+);base64,(?P<data>[^"]+)"',
    re.IGNORECASE,
)


@dataclass
class ExternalizedImage:
    asset_path: Path
    original_bytes: int
    digest: str


@dataclass
class SvgExternalizeResult:
    svg_path: Path
    output_svg_path: Path
    original_svg_bytes: int
    output_svg_bytes: int
    images_found: int
    images_externalized: int
    assets_written: list[Path]


def detect_extension(mime_type: str, file_bytes: bytes) -> str:
    mime_type = mime_type.lower()
    if mime_type == "image/png" or file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if mime_type in {"image/jpeg", "image/jpg"} or file_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if mime_type == "image/gif" or file_bytes.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if mime_type == "image/webp" or (
        file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP"
    ):
        return ".webp"
    if mime_type == "image/svg+xml" or file_bytes.lstrip().startswith(b"<svg"):
        return ".svg"
    return ".bin"


def relpath_for_svg(target: Path, svg_path: Path) -> str:
    return os.path.relpath(target, start=svg_path.parent).replace("\\", "/")


def discover_svg_files(inputs: list[str]) -> list[Path]:
    svg_files: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if path.is_dir():
            svg_files.extend(
                sorted(
                    child
                    for child in path.iterdir()
                    if child.is_file() and child.suffix.lower() == ".svg"
                )
            )
            continue
        if path.suffix.lower() != ".svg":
            raise ValueError(f"Expected .svg input, got: {path}")
        svg_files.append(path)
    return svg_files


def externalize_svg_file(
    svg_path: Path,
    output_svg_path: Path,
    assets_dir: Path,
    digest_index: dict[str, Path] | None = None,
) -> SvgExternalizeResult:
    digest_index = digest_index if digest_index is not None else {}
    assets_dir.mkdir(parents=True, exist_ok=True)
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)

    content = svg_path.read_text(encoding="utf-8")
    original_svg_bytes = len(content.encode("utf-8"))
    assets_written: list[Path] = []
    images_found = 0
    images_externalized = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal images_found, images_externalized

        images_found += 1
        attr_name = match.group("attr")
        mime_type = match.group("mime")
        data = html.unescape(match.group("data"))

        try:
            payload = base64.b64decode(data)
        except ValueError:
            return match.group(0)

        digest = hashlib.sha1(payload).hexdigest()
        asset_path = digest_index.get(digest)
        if asset_path is None:
            extension = detect_extension(mime_type, payload)
            asset_path = assets_dir / f"inline_{digest[:12]}{extension}"
            if not asset_path.exists():
                asset_path.write_bytes(payload)
                assets_written.append(asset_path)
            digest_index[digest] = asset_path

        images_externalized += 1
        relative_ref = relpath_for_svg(asset_path, output_svg_path)
        return f'{attr_name}="{relative_ref}"'

    updated = DATA_URI_RE.sub(replace, content)
    output_svg_path.write_text(updated, encoding="utf-8")

    return SvgExternalizeResult(
        svg_path=svg_path,
        output_svg_path=output_svg_path,
        original_svg_bytes=original_svg_bytes,
        output_svg_bytes=len(updated.encode("utf-8")),
        images_found=images_found,
        images_externalized=images_externalized,
        assets_written=assets_written,
    )


def externalize_svg_batch(
    svg_files: list[Path],
    output_dir: Path | None,
    assets_dir: Path | None,
) -> list[SvgExternalizeResult]:
    digest_index: dict[str, Path] = {}
    results: list[SvgExternalizeResult] = []

    default_assets_dir = assets_dir
    if default_assets_dir is None:
        if output_dir is not None:
            default_assets_dir = output_dir / "assets"
        elif svg_files:
            default_assets_dir = svg_files[0].parent / "assets"
        else:
            default_assets_dir = Path.cwd() / "assets"

    for svg_path in svg_files:
        destination = output_dir / svg_path.name if output_dir else svg_path
        result = externalize_svg_file(
            svg_path=svg_path,
            output_svg_path=destination,
            assets_dir=default_assets_dir,
            digest_index=digest_index,
        )
        results.append(result)

    return results


def print_summary(results: list[SvgExternalizeResult]) -> None:
    total_original = sum(item.original_svg_bytes for item in results)
    total_output = sum(item.output_svg_bytes for item in results)
    total_images = sum(item.images_externalized for item in results)
    written_assets = sorted({asset for item in results for asset in item.assets_written})

    for item in results:
        print(f"[FILE] {item.svg_path.name}")
        print(
            f"  SVG size: {item.original_svg_bytes} -> {item.output_svg_bytes} bytes"
        )
        print(
            f"  Images externalized: {item.images_externalized}/{item.images_found}"
        )
        if item.assets_written:
            for asset in item.assets_written:
                print(f"  Asset written: {asset.name}")

    print("=" * 50)
    print(f"[DONE] Processed SVG files: {len(results)}")
    print(f"[DONE] Images externalized: {total_images}")
    print(f"[DONE] SVG bytes: {total_original} -> {total_output}")
    print(f"[DONE] Unique assets written: {len(written_assets)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract inline Base64 SVG images into external asset files."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="SVG files or directories containing SVG files",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Write cleaned SVG files to this directory instead of editing in place",
    )
    parser.add_argument(
        "--assets-dir",
        help="Directory for extracted image assets (default: <output>/assets or sibling assets/)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        svg_files = discover_svg_files(args.inputs)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    if not svg_files:
        print("Error: no SVG files found")
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    assets_dir = Path(args.assets_dir).expanduser().resolve() if args.assets_dir else None

    results = externalize_svg_batch(svg_files, output_dir, assets_dir)
    print_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
