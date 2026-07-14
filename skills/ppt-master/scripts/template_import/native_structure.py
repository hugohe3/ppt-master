#!/usr/bin/env python3
"""
PPT Master - Native Template Structure Contract

Build a portable master/layout contract from the PPTX template import manifest.

Usage:
    Imported by pptx_template_import.py.

Examples:
    write_native_structure_bundle(source_pptx, output_dir, manifest)

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


SCHEMA = "ppt-master.native-structure.v1"
SOURCE_TEMPLATE_NAME = "source_template.pptx"
CONTRACT_NAME = "native_structure.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_source_template(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        return
    shutil.copy2(source, destination)


def _has_reusable_structure(manifest: dict[str, Any]) -> bool:
    layouts = manifest.get("layouts", [])
    masters = manifest.get("masters", [])
    slides = manifest.get("slides", [])
    used_layouts = [layout for layout in layouts if layout.get("usedBySlides")]
    candidate_layouts = used_layouts or layouts
    if any(
        layout.get("backgroundAsset")
        or int(layout.get("drawableShapeCount") or 0) > 0
        or any(
            placeholder.get("semanticRole")
            not in {"date", "footer", "slide-number", "other"}
            for placeholder in layout.get("placeholders", [])
        )
        for layout in candidate_layouts
    ):
        return True
    if any(
        master.get("backgroundAsset")
        or int(master.get("drawableShapeCount") or 0) > 0
        or master.get("imageAssets")
        for master in masters
    ):
        return True
    return any(slide.get("placeholders") for slide in slides)


def build_native_structure(
    source_pptx: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build the portable source-package structure contract."""
    masters = manifest.get("masters", [])
    layouts = manifest.get("layouts", [])
    slides = manifest.get("slides", [])
    master_key_by_path = {
        master["path"]: f"master_{index:02d}"
        for index, master in enumerate(masters, start=1)
    }
    layout_key_by_path = {
        layout["path"]: f"layout_{index:02d}"
        for index, layout in enumerate(layouts, start=1)
    }
    complete_graph = (
        bool(masters and layouts)
        and all(
            layout.get("parentPath") in master_key_by_path
            for layout in layouts
        )
        and all(
            slide.get("layoutPath") in layout_key_by_path
            and slide.get("masterPath") in master_key_by_path
            for slide in slides
        )
    )
    reusable_structure = _has_reusable_structure(manifest)
    recommended_mode = "preserve" if complete_graph and reusable_structure else "template"
    reasons: list[str] = []
    if not complete_graph:
        reasons.append("incomplete-master-layout-graph")
    if not reusable_structure:
        reasons.append("source-structure-is-minimal")
    if complete_graph and reusable_structure:
        reasons.append("source-master-layout-contract-is-reusable")
    if len(masters) > 1:
        reasons.append("source-uses-multiple-masters")

    master_contracts = []
    for master in masters:
        key = master_key_by_path[master["path"]]
        master_contracts.append({
            "key": key,
            "name": master.get("displayName") or master.get("name") or key,
            "packagePart": master["path"],
            "themePart": master.get("themePath"),
            "theme": master.get("theme") or {"colors": {}, "fonts": {}},
            "backgroundAsset": master.get("backgroundAsset"),
            "imageAssets": master.get("imageAssets", []),
            "shapeImageAssets": master.get("shapeImageAssets", []),
            "drawableShapeCount": master.get("drawableShapeCount", 0),
            "layoutKeys": [
                layout_key_by_path[layout["path"]]
                for layout in layouts
                if layout.get("parentPath") == master["path"]
            ],
        })

    layout_contracts = []
    for layout in layouts:
        key = layout_key_by_path[layout["path"]]
        layout_contracts.append({
            "key": key,
            "name": layout.get("displayName") or layout.get("name") or key,
            "type": layout.get("layoutType"),
            "packagePart": layout["path"],
            "masterKey": master_key_by_path.get(layout.get("parentPath")),
            "showMasterShapes": layout.get("showMasterShapes", True),
            "backgroundAsset": layout.get("backgroundAsset"),
            "imageAssets": layout.get("imageAssets", []),
            "shapeImageAssets": layout.get("shapeImageAssets", []),
            "drawableShapeCount": layout.get("drawableShapeCount", 0),
            "placeholders": layout.get("placeholders", []),
            "usedBySlides": layout.get("usedBySlides", []),
            "svgFile": layout.get("svgFile"),
        })

    slide_contracts = []
    for slide in slides:
        slide_contracts.append({
            "index": slide["index"],
            "pageType": slide.get("pageType"),
            "layoutKey": layout_key_by_path.get(slide.get("layoutPath")),
            "masterKey": master_key_by_path.get(slide.get("masterPath")),
            "showInheritedShapes": slide.get("showInheritedShapes", True),
            "placeholders": slide.get("placeholders", []),
            "layeredSvgFile": slide.get("svgFile"),
            "flatSvgFile": slide.get("flatSvgFile"),
        })

    return {
        "schema": SCHEMA,
        "source": {
            "name": source_pptx.name,
            "templateFile": SOURCE_TEMPLATE_NAME,
            "sha256": _sha256(source_pptx),
        },
        "slideSize": manifest.get("slideSize", {}),
        "strategy": {
            "preservationEligible": complete_graph,
            "reusableStructureDetected": reusable_structure,
            "recommendedMode": recommended_mode,
            "recommendationScope": "source-structure-assessment",
            "templateOutputMode": "template",
            "downstreamTemplateAdherence": "strategist-confirmed-explicit-structure",
            "hasMultipleMasters": len(masters) > 1,
            "reasonCodes": reasons,
        },
        "masters": master_contracts,
        "layouts": layout_contracts,
        "slides": slide_contracts,
    }


def write_native_structure_bundle(
    source_pptx: Path,
    output_dir: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    """Copy the source template and write its portable structure contract."""
    source_copy = output_dir / SOURCE_TEMPLATE_NAME
    _copy_source_template(source_pptx, source_copy)
    contract = build_native_structure(source_pptx, manifest)
    (output_dir / CONTRACT_NAME).write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return contract
