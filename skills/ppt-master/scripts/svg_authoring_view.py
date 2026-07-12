#!/usr/bin/env python3
"""
PPT Master - SVG Authoring View

Create a lightweight, non-destructive view of PPTX-imported SVG files for
human or model inspection. The source SVG remains the round-trip authority;
the output copy keeps visible SVG content and compact shape intent while
hiding bulky import-only payloads and duplicate hidden geometry carriers.

Usage:
    python3 scripts/svg_authoring_view.py <svg-file-or-directory> -o <output-dir>

Examples:
    python3 scripts/svg_authoring_view.py analysis/source_svg_import/svg-flat -o analysis/authoring-svg
    python3 scripts/svg_authoring_view.py imported/slide_06.svg -o /tmp/slide-authoring-view

Dependencies:
    None (standard library only).

This tool produces an inspection/authoring projection, not a final template or
release export source. Keep the complete imported SVG for native restoration.
Directory runs prepare and stage the complete batch before publishing it, so a
failed page leaves the existing destination set unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

# These fields identify the source OOXML object or guard its exact imported
# fallback. They belong in the complete import SVG, not its lightweight view.
IMPORT_SOURCE_ATTRIBUTES = {
    "data-name",
    "data-pptx-preview-sha256",
    "data-pptx-shape-id",
    "data-pptx-shape-name",
    "data-pptx-shape-scope",
    "data-pptx-shape-style",
}

# Compact native-shape intent is intentionally not in the removal set:
# data-pptx-object, data-pptx-prst, and data-pptx-frame remain useful while
# reviewing the visible fallback. Structural markers also pass through
# unchanged; this projection never defines restoration policy.


def _local_name(name: object) -> str:
    return name.rsplit("}", 1)[-1] if isinstance(name, str) else ""


@dataclass
class ProjectionStats:
    txbody_metadata: int = 0
    text_carrier_metadata: int = 0
    hidden_geometry_carriers: int = 0
    geometry_preview_wrappers: int = 0
    geometry_detail_markers: int = 0
    asset_references_rewritten: int = 0
    source_attributes: Counter[str] = field(default_factory=Counter)

    def as_dict(self) -> dict[str, object]:
        return {
            "txbody_metadata": self.txbody_metadata,
            "text_carrier_metadata": self.text_carrier_metadata,
            "hidden_geometry_carriers": self.hidden_geometry_carriers,
            "geometry_preview_wrappers": self.geometry_preview_wrappers,
            "geometry_detail_markers": self.geometry_detail_markers,
            "source_attributes": dict(sorted(self.source_attributes.items())),
            "asset_references_rewritten": self.asset_references_rewritten,
        }

    def merge(self, other: "ProjectionStats") -> None:
        self.txbody_metadata += other.txbody_metadata
        self.text_carrier_metadata += other.text_carrier_metadata
        self.hidden_geometry_carriers += other.hidden_geometry_carriers
        self.geometry_preview_wrappers += other.geometry_preview_wrappers
        self.geometry_detail_markers += other.geometry_detail_markers
        self.asset_references_rewritten += other.asset_references_rewritten
        self.source_attributes.update(other.source_attributes)


@dataclass
class ProjectionReport:
    source: Path
    output: Path
    original_bytes: int
    projected_bytes: int
    stats: ProjectionStats

    def as_dict(self) -> dict[str, object]:
        saved = self.original_bytes - self.projected_bytes
        reduction = (saved / self.original_bytes * 100) if self.original_bytes else 0.0
        return {
            "source": str(self.source),
            "output": str(self.output),
            "original_bytes": self.original_bytes,
            "projected_bytes": self.projected_bytes,
            "bytes_saved": saved,
            "reduction_percent": round(reduction, 2),
            "removed": self.stats.as_dict(),
        }


def _is_hidden_geometry_carrier(element: ET.Element) -> bool:
    if element.get("data-pptx-part") != "geometry":
        return False
    visibility = (element.get("visibility") or "").strip().lower()
    display = (element.get("display") or "").strip().lower()
    style = (element.get("style") or "").replace(" ", "").lower()
    return (
        visibility == "hidden"
        or display == "none"
        or "visibility:hidden" in style
        or "display:none" in style
    )


def _append_tail(parent: ET.Element, index: int, tail: str | None) -> None:
    if not tail:
        return
    if index > 0:
        previous = list(parent)[index - 1]
        previous.tail = (previous.tail or "") + tail
    else:
        parent.text = (parent.text or "") + tail


def _remove_child(parent: ET.Element, child: ET.Element) -> None:
    children = list(parent)
    index = children.index(child)
    tail = child.tail
    parent.remove(child)
    _append_tail(parent, index, tail)


def _unwrap_preview(parent: ET.Element, wrapper: ET.Element) -> bool:
    """Promote a marker-only preview wrapper without changing its geometry."""
    if wrapper.attrib or (wrapper.text and wrapper.text.strip()):
        return False

    siblings = list(parent)
    index = siblings.index(wrapper)
    promoted = list(wrapper)
    wrapper_tail = wrapper.tail
    for child in promoted:
        wrapper.remove(child)
    parent.remove(wrapper)

    for offset, child in enumerate(promoted):
        parent.insert(index + offset, child)

    if promoted:
        promoted[-1].tail = (promoted[-1].tail or "") + (wrapper_tail or "")
    else:
        _append_tail(parent, index, wrapper_tail)
    return True


def _strip_import_attributes(element: ET.Element, stats: ProjectionStats) -> None:
    for name in list(element.attrib):
        if name not in IMPORT_SOURCE_ATTRIBUTES:
            continue
        stats.source_attributes[name] += 1
        del element.attrib[name]


def _project_subtree(parent: ET.Element, stats: ProjectionStats) -> None:
    for child in list(parent):
        part = child.get("data-pptx-part")
        tag = _local_name(child.tag)

        if tag == "metadata" and part in {"txbody", "text-carrier"}:
            if part == "txbody":
                stats.txbody_metadata += 1
            else:
                stats.text_carrier_metadata += 1
            _remove_child(parent, child)
            continue

        if _is_hidden_geometry_carrier(child):
            stats.hidden_geometry_carriers += 1
            _remove_child(parent, child)
            continue

        _project_subtree(child, stats)
        _strip_import_attributes(child, stats)

        if part == "geometry-preview":
            child.attrib.pop("data-pptx-part", None)
            if _unwrap_preview(parent, child):
                stats.geometry_preview_wrappers += 1
        elif part == "geometry-detail":
            child.attrib.pop("data-pptx-part", None)
            stats.geometry_detail_markers += 1


def _rewrite_asset_reference(value: str, source_dir: Path, output_dir: Path) -> str:
    if not value or value.startswith("#"):
        return value
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return value

    resolved = (source_dir / parsed.path).resolve()
    try:
        relative = os.path.relpath(resolved, output_dir).replace(os.sep, "/")
    except ValueError:
        relative = resolved.as_uri()
    return urlunsplit(("", "", relative, parsed.query, parsed.fragment))


def _rewrite_asset_references(
    root: ET.Element,
    source_dir: Path,
    output_dir: Path,
    stats: ProjectionStats,
) -> None:
    for element in root.iter():
        for name in ("href", f"{{{XLINK_NS}}}href"):
            current = element.get(name)
            if current is None:
                continue
            rewritten = _rewrite_asset_reference(current, source_dir, output_dir)
            if rewritten != current:
                element.set(name, rewritten)
                stats.asset_references_rewritten += 1


def _render_projection(source: Path, output: Path) -> tuple[ProjectionReport, bytes]:
    """Build one projection in memory without changing source or destination."""
    original = source.read_bytes()
    parser = ET.XMLParser(
        target=ET.TreeBuilder(insert_comments=True, insert_pis=True),
    )
    root = ET.fromstring(original, parser=parser)
    if _local_name(root.tag) != "svg":
        raise ValueError(f"Root element is not <svg>: {source}")

    stats = ProjectionStats()
    _project_subtree(root, stats)
    _strip_import_attributes(root, stats)
    _rewrite_asset_references(root, source.parent, output.parent, stats)

    projected = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    if not projected.endswith(b"\n"):
        projected += b"\n"

    report = ProjectionReport(
        source=source,
        output=output,
        original_bytes=len(original),
        projected_bytes=len(projected),
        stats=stats,
    )
    return report, projected


def project_svg(source: Path, output: Path) -> ProjectionReport:
    """Write one lightweight authoring projection without changing the source."""
    report, projected = _render_projection(source, output)
    output.parent.mkdir(parents=True, exist_ok=True)

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(projected)
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return report


def _nearest_existing_directory(path: Path) -> Path:
    candidate = path
    while not os.path.lexists(candidate):
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    if not candidate.is_dir():
        raise NotADirectoryError(f"Output parent is not a directory: {candidate}")
    return candidate


def _ensure_directory(path: Path, created: list[Path]) -> None:
    missing: list[Path] = []
    candidate = path
    while not candidate.exists():
        if os.path.lexists(candidate):
            raise NotADirectoryError(f"Output parent is not a directory: {candidate}")
        missing.append(candidate)
        parent = candidate.parent
        if parent == candidate:
            raise NotADirectoryError(f"Cannot resolve output parent: {path}")
        candidate = parent
    if not candidate.is_dir():
        raise NotADirectoryError(f"Output parent is not a directory: {candidate}")

    for directory in reversed(missing):
        directory.mkdir()
        created.append(directory)


def _remove_created_directories(created: list[Path]) -> list[str]:
    errors: list[str] = []
    for directory in reversed(created):
        try:
            directory.rmdir()
        except FileNotFoundError:
            continue
        except OSError as exc:
            errors.append(f"could not remove {directory}: {exc}")
    return errors


def _rollback_published_files(
    published: list[tuple[Path, Path | None]],
    created: list[Path],
) -> list[str]:
    errors: list[str] = []
    for target, backup in reversed(published):
        try:
            if backup is None:
                target.unlink(missing_ok=True)
            else:
                backup.replace(target)
        except OSError as exc:
            errors.append(f"could not restore {target}: {exc}")
    errors.extend(_remove_created_directories(created))
    return errors


def _publish_existing_directory(
    staged: list[tuple[ProjectionReport, Path]],
    staging_root: Path,
    *,
    force: bool,
) -> None:
    backup_root = staging_root / "previous"
    backups: dict[Path, Path | None] = {}

    for index, (report, _) in enumerate(staged):
        target = report.output
        if not os.path.lexists(target):
            backups[target] = None
            continue
        if not force:
            raise FileExistsError(f"Output file already exists: {target}")
        if target.is_dir() and not target.is_symlink():
            raise IsADirectoryError(f"Output target is a directory: {target}")

        backup = backup_root / f"{index:06d}.svg"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup, follow_symlinks=False)
        backups[target] = backup

    created: list[Path] = []
    published: list[tuple[Path, Path | None]] = []
    try:
        for report, _ in staged:
            _ensure_directory(report.output.parent, created)

        staging_device = staging_root.stat().st_dev
        for report, _ in staged:
            if report.output.parent.stat().st_dev != staging_device:
                raise OSError(
                    f"Cannot atomically publish across filesystems: {report.output}"
                )
            if backups[report.output] is None and os.path.lexists(report.output):
                raise FileExistsError(
                    f"Output appeared while projections were staged: {report.output}"
                )

        for report, staged_file in staged:
            target = report.output
            staged_file.replace(target)
            published.append((target, backups[target]))
    except OSError as exc:
        rollback_errors = _rollback_published_files(published, created)
        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise RuntimeError(
                f"Batch publish failed ({exc}); rollback was incomplete: {details}"
            ) from exc
        raise


def project_svg_batch(
    mapping: list[tuple[Path, Path]],
    output_dir: Path,
    *,
    force: bool,
) -> list[ProjectionReport]:
    """Project and publish a directory mapping as one recoverable transaction."""
    rendered = [_render_projection(source, output) for source, output in mapping]
    staging_parent = _nearest_existing_directory(output_dir.parent)

    with tempfile.TemporaryDirectory(
        prefix=".svg-authoring-view-",
        dir=staging_parent,
    ) as temporary:
        staging_root = Path(temporary)
        new_root = staging_root / "projected"
        staged: list[tuple[ProjectionReport, Path]] = []

        for report, projected in rendered:
            relative = report.output.relative_to(output_dir)
            staged_file = new_root / relative
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            staged_file.write_bytes(projected)
            staged.append((report, staged_file))

        if not output_dir.exists():
            created: list[Path] = []
            try:
                _ensure_directory(output_dir.parent, created)
                if os.path.lexists(output_dir):
                    raise FileExistsError(
                        f"Output directory appeared while projections were staged: {output_dir}"
                    )
                if output_dir.parent.stat().st_dev != staging_root.stat().st_dev:
                    raise OSError(
                        f"Cannot atomically publish across filesystems: {output_dir}"
                    )
                new_root.replace(output_dir)
            except OSError as exc:
                cleanup_errors = _remove_created_directories(created)
                if cleanup_errors:
                    details = "; ".join(cleanup_errors)
                    raise RuntimeError(
                        f"Batch publish failed ({exc}); cleanup was incomplete: {details}"
                    ) from exc
                raise
        else:
            _publish_existing_directory(
                staged,
                staging_root,
                force=force,
            )

    return [report for report, _ in rendered]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _source_mapping(input_path: Path, output_dir: Path) -> list[tuple[Path, Path]]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".svg":
            raise ValueError(f"Input file must use the .svg extension: {input_path}")
        return [(input_path, output_dir / input_path.name)]

    sources = sorted(
        path for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() == ".svg"
    )
    if not sources:
        raise ValueError(f"No SVG files found under: {input_path}")
    return [(source, output_dir / source.relative_to(input_path)) for source in sources]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create lightweight, non-destructive authoring views of PPTX-imported SVG files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="SVG file or directory to project")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit destination directory for projected SVG copies",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace projected files that already exist (never changes source files)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()

    if not input_path.exists():
        print(f"Error: input does not exist: {input_path}", file=sys.stderr)
        return 1
    if output_dir.exists() and not output_dir.is_dir():
        print(f"Error: output path is not a directory: {output_dir}", file=sys.stderr)
        return 1
    if input_path.is_dir() and _is_within(output_dir, input_path):
        print("Error: output directory must not be inside the input directory", file=sys.stderr)
        return 1

    try:
        mapping = _source_mapping(input_path, output_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    same_file = [source for source, target in mapping if source.resolve() == target.resolve()]
    if same_file:
        print(f"Error: output would overwrite source SVG: {same_file[0]}", file=sys.stderr)
        return 1

    collisions = [target for _, target in mapping if os.path.lexists(target)]
    if collisions and not args.force:
        print(
            f"Error: {len(collisions)} output file(s) already exist; use --force to replace projections. "
            f"First collision: {collisions[0]}",
            file=sys.stderr,
        )
        return 1

    reports: list[ProjectionReport] = []
    try:
        if input_path.is_file():
            source, output = mapping[0]
            reports.append(project_svg(source, output))
        else:
            reports = project_svg_batch(
                mapping,
                output_dir,
                force=args.force,
            )
    except (ET.ParseError, OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    total_stats = ProjectionStats()
    original_bytes = 0
    projected_bytes = 0
    for report in reports:
        original_bytes += report.original_bytes
        projected_bytes += report.projected_bytes
        total_stats.merge(report.stats)

    bytes_saved = original_bytes - projected_bytes
    reduction = (bytes_saved / original_bytes * 100) if original_bytes else 0.0
    result = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "file_count": len(reports),
        "files": [report.as_dict() for report in reports],
        "totals": {
            "original_bytes": original_bytes,
            "projected_bytes": projected_bytes,
            "bytes_saved": bytes_saved,
            "reduction_percent": round(reduction, 2),
            "removed": total_stats.as_dict(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
