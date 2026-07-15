#!/usr/bin/env python3
"""Build deterministic source inventory and an AI-synthesis scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from console_encoding import configure_utf8_stdio


configure_utf8_stdio()

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
PRESENTATION_SUFFIXES = {".pptx", ".pptm", ".ppsx", ".ppsm", ".potx", ".potm"}
DOCUMENT_SUFFIXES = {".pdf", ".doc", ".docx", ".odt", ".rtf", ".epub", ".html", ".htm"}
TABLE_SUFFIXES = {".xlsx", ".xlsm", ".csv", ".tsv"}
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _kind(path: Path) -> str:
    if path.name.endswith(".conversion_profile.json") or path.name == "image_manifest.json":
        return "pipeline-metadata"
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in PRESENTATION_SUFFIXES:
        return "presentation"
    if suffix in DOCUMENT_SUFFIXES:
        return "document"
    if suffix in TABLE_SUFFIXES:
        return "table"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return "other"


def _role(path: Path) -> str:
    if _kind(path) == "pipeline-metadata":
        return "pipeline-sidecar"
    name = path.stem.lower()
    role_words = (
        (("outline", "大纲"), "existing-outline"),
        (("task", "任务书"), "design-task"),
        (("brief", "说明", "design"), "design-brief"),
        (("template", "模板"), "style-reference"),
        (("render", "效果图"), "project-render"),
    )
    for words, role in role_words:
        if any(word in name for word in words):
            return role
    return "source-material"


def _entry(path: Path, project: Path) -> dict[str, Any]:
    relative = path.relative_to(project).as_posix()
    return {
        "source_id": hashlib.sha1(relative.encode("utf-8")).hexdigest()[:12],
        "path": relative,
        "name": path.name,
        "kind": _kind(path),
        "role": _role(path),
        "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def build_source_manifest(project_path: str | Path) -> tuple[Path, Path]:
    """Scan project sources/images and write inventory plus synthesis scaffold."""
    project = Path(project_path).resolve()
    if not project.is_dir():
        raise ValueError(f"Project not found: {project}")
    source_files = []
    for dirname in ("sources", "images"):
        directory = project / dirname
        if directory.is_dir():
            source_files.extend(path for path in directory.rglob("*") if path.is_file())
    source_files = sorted(set(source_files), key=lambda path: path.as_posix().lower())
    entries = [_entry(path, project) for path in source_files]

    hashes: dict[str, list[str]] = {}
    stems: dict[str, list[str]] = {}
    for entry in entries:
        hashes.setdefault(entry["sha256"], []).append(entry["source_id"])
        stems.setdefault(Path(entry["name"]).stem.lower(), []).append(entry["source_id"])
    duplicate_groups = [group for group in hashes.values() if len(group) > 1]
    related_groups = [group for group in stems.values() if len(group) > 1]

    manifest = {
        "schema_version": 1,
        "project": project.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_count": len(entries),
        "sources": entries,
        "duplicate_groups": duplicate_groups,
        "related_name_groups": related_groups,
    }
    manifest_path = project / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    synthesis_path = project / "source_synthesis.json"
    if not synthesis_path.exists():
        synthesis = {
            "schema_version": 1,
            "status": "pending-ai",
            "source_manifest": manifest_path.name,
            "summary": "",
            "relationships": [],
            "shared_facts": [],
            "conflicts": [],
            "existing_structure": [],
            "available_images": [
                entry["path"] for entry in entries if entry["kind"] == "image"
            ],
            "outline_inputs": [
                entry["source_id"] for entry in entries if entry["role"] == "existing-outline"
            ],
            "agent_instructions": (
                "Read source_manifest.json and the normalized source content. "
                "Replace pending fields with a sourced synthesis before style selection."
            ),
        }
        synthesis_path.write_text(
            json.dumps(synthesis, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return manifest_path, synthesis_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build PPT Master source intake artifacts.")
    parser.add_argument("project", help="PPT Master project path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest, synthesis = build_source_manifest(args.project)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(manifest)
    print(synthesis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
