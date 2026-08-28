#!/usr/bin/env python3
"""
PPT Master - Stamp Native Fallback Baselines

Validate Chart/Table replacement payloads and bind SVG-authoritative markers
to their current visible fallback without reformatting the SVG document.

Usage:
    python3 scripts/stamp_native_fallbacks.py "<svg-or-directory>" [--write]

Examples:
    python3 scripts/stamp_native_fallbacks.py "projects/example/svg_output"
    python3 scripts/stamp_native_fallbacks.py "projects/example/svg_output" --write

Dependencies:
    None (only uses standard library and PPT Master sibling modules)
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET
from xml.parsers import expat

from console_encoding import configure_utf8_stdio
from pptx_shapes import NATIVE_FALLBACK_SHA256_ATTR
from svg_to_pptx.native_objects import (
    native_json_is_authoritative,
    native_replacement_kind,
    stamp_native_fallback_baseline,
    validate_native_object_marker,
)
from svg_to_pptx.native_objects.marker_status import native_marker_status_errors


_FALLBACK_ATTR_BYTES = NATIVE_FALLBACK_SHA256_ATTR.encode("ascii")
_FALLBACK_ATTR_RE = re.compile(
    rb"(?P<prefix>\s" + re.escape(_FALLBACK_ATTR_BYTES) + rb"\s*=\s*)"
    rb"(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
    re.DOTALL,
)


class NativeFallbackStampError(RuntimeError):
    """Raised when a fallback baseline cannot be validated or patched safely."""


def _local_name(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _svg_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".svg":
            raise NativeFallbackStampError(f"Input file is not SVG: {input_path}")
        return [input_path]
    if not input_path.is_dir():
        raise NativeFallbackStampError(f"Input path does not exist: {input_path}")
    files = sorted(
        path
        for path in input_path.glob("*.svg")
        if path.is_file()
    )
    if not files:
        raise NativeFallbackStampError(
            f"Input directory contains no direct SVG files: {input_path}"
        )
    return files


def _marker_ancestors(
    marker: ET.Element,
    root: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> tuple[ET.Element, ...]:
    ancestors: list[ET.Element] = []
    parent = parent_map.get(marker)
    while parent is not None and parent is not root:
        if _local_name(parent.tag) == "g":
            ancestors.append(parent)
        parent = parent_map.get(parent)
    return tuple(reversed(ancestors))


def _start_tag_spans(source: bytes) -> list[tuple[int, int, str]]:
    starts: list[tuple[int, str]] = []
    parser = expat.ParserCreate()

    def record_start(name: str, _attrs: dict[str, str]) -> None:
        starts.append((parser.CurrentByteIndex, name.rsplit(":", 1)[-1]))

    parser.StartElementHandler = record_start
    try:
        parser.Parse(source, True)
    except expat.ExpatError as exc:
        raise NativeFallbackStampError(f"Invalid SVG XML: {exc}") from exc

    spans: list[tuple[int, int, str]] = []
    for start, name in starts:
        quote: int | None = None
        cursor = start + 1
        while cursor < len(source):
            token = source[cursor]
            if quote is not None:
                if token == quote:
                    quote = None
            elif token in {ord('"'), ord("'")}:
                quote = token
            elif token == ord(">"):
                spans.append((start, cursor + 1, name))
                break
            cursor += 1
        else:
            raise NativeFallbackStampError(
                f"Unterminated start tag at byte offset {start}"
            )
    return spans


def _patch_start_tag(tag: bytes, digest: str) -> bytes:
    encoded_digest = digest.encode("ascii")
    match = _FALLBACK_ATTR_RE.search(tag)
    if match is not None:
        return tag[:match.start("value")] + encoded_digest + tag[match.end("value"):]
    close = re.search(rb"(?P<space>\s*)(?P<slash>/?)>$", tag)
    if close is None:
        raise NativeFallbackStampError("Unable to locate SVG start-tag terminator")
    insertion = (
        b" "
        + _FALLBACK_ATTR_BYTES
        + b'="'
        + encoded_digest
        + b'"'
    )
    return tag[:close.start()] + insertion + tag[close.start():]


def _patch_document(
    source: bytes,
    root: ET.Element,
    digests: dict[ET.Element, str],
) -> tuple[bytes, int]:
    elements = list(root.iter())
    spans = _start_tag_spans(source)
    if len(elements) != len(spans):
        raise NativeFallbackStampError(
            "Parsed SVG element roster does not match raw start-tag roster"
        )

    patches: list[tuple[int, int, bytes]] = []
    for element, (start, end, raw_name) in zip(elements, spans):
        if _local_name(element.tag) != raw_name:
            raise NativeFallbackStampError(
                "Parsed SVG element order does not match raw start-tag order"
            )
        digest = digests.get(element)
        if digest is None:
            continue
        current_tag = source[start:end]
        replacement = _patch_start_tag(current_tag, digest)
        if replacement != current_tag:
            patches.append((start, end, replacement))

    patched = source
    for start, end, replacement in reversed(patches):
        patched = patched[:start] + replacement + patched[end:]
    return patched, len(patches)


def _validated_svg_first_digests(
    root: ET.Element,
    path: Path,
) -> tuple[dict[ET.Element, str], int]:
    parent_map = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    status_errors: list[str] = []
    for element in root.iter():
        if _local_name(element.tag) == "metadata":
            continue
        marker_id = element.get("id") or element.get("data-name") or "<unnamed>"
        status_errors.extend(
            f"{marker_id}: {error}"
            for error in native_marker_status_errors(element)
        )
    if status_errors:
        raise NativeFallbackStampError(
            f"{path.name}: invalid native marker status: "
            + "; ".join(status_errors)
        )

    digests: dict[ET.Element, str] = {}
    json_authoritative = 0
    for marker in root.iter():
        kind = native_replacement_kind(marker)
        if kind not in {"chart", "table"}:
            continue
        marker_id = marker.get("id") or marker.get("data-name") or "<unnamed>"
        try:
            validate_native_object_marker(
                marker,
                ancestors=_marker_ancestors(marker, root, parent_map),
            )
        except RuntimeError as exc:
            raise NativeFallbackStampError(
                f"{path.name}: invalid {kind} marker {marker_id}: {exc}"
            ) from exc
        if native_json_is_authoritative(marker):
            json_authoritative += 1
            continue
        digests[marker] = stamp_native_fallback_baseline(
            marker,
            document_root=root,
        )
    return digests, json_authoritative


def _atomic_write(path: Path, payload: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def prepare_native_fallback_baselines(
    source: bytes,
    path: Path,
) -> tuple[bytes, int, int, int]:
    """Validate and plan fallback baselines for one in-memory SVG document."""
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise NativeFallbackStampError(f"{path.name}: invalid SVG XML: {exc}") from exc
    digests, json_authoritative = _validated_svg_first_digests(root, path)
    patched, restamped = _patch_document(source, root, digests)
    return patched, len(digests), json_authoritative, restamped


def _prepare_file(path: Path) -> tuple[bytes, int, int, bool]:
    patched, svg_first, json_authoritative, restamped = (
        prepare_native_fallback_baselines(path.read_bytes(), path)
    )
    return patched, svg_first, json_authoritative, restamped > 0


def stamp_file(path: Path, *, write: bool) -> tuple[int, int, bool]:
    """Validate and optionally stamp one SVG without reformatting it."""
    patched, svg_authoritative, json_authoritative, changed = _prepare_file(path)
    if write and changed:
        _atomic_write(path, patched)
    return svg_authoritative, json_authoritative, changed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate native Chart/Table payloads and stamp current visible "
            "fallback hashes on SVG-authoritative markers."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="One SVG file or a directory whose direct *.svg files are checked",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Atomically update SVG files. Omit for a read-only preview; use only "
            "after visible fallback and embedded JSON were updated together."
        ),
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        files = _svg_files(args.input.resolve())
        prepared = [
            (path, *_prepare_file(path))
            for path in files
        ]
        if args.write:
            for path, payload, _svg_first, _json_first, changed in prepared:
                if changed:
                    _atomic_write(path, payload)
        total_svg_first = 0
        total_json_first = 0
        changed_files = 0
        for path, _payload, svg_first, json_first, changed in prepared:
            total_svg_first += svg_first
            total_json_first += json_first
            changed_files += int(changed)
            if args.write and changed:
                action = "updated"
            elif changed:
                action = "would-update"
            else:
                action = "unchanged"
            print(
                f"{path}: {action}; SVG-first={svg_first}, JSON-first={json_first}"
            )
    except (NativeFallbackStampError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    mode = "write" if args.write else "read-only"
    print(
        f"Native fallback baselines: mode={mode}, files={len(files)}, "
        f"changed={changed_files}, SVG-first={total_svg_first}, "
        f"JSON-first={total_json_first}"
    )
    if changed_files and not args.write:
        print("Re-run with --write to apply these validated baseline updates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
