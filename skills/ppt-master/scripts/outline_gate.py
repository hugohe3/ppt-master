#!/usr/bin/env python3
"""Validate and confirm the editable page-by-page outline contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from console_encoding import configure_utf8_stdio


configure_utf8_stdio()

DRAFT_NAME = "outline_draft.json"
CONFIRMED_NAME = "outline_confirmed.json"
SELECTION_NAME = "workflow_selection.json"
CONTENT_INVENTORY_PATH = Path("analysis") / "content_inventory.json"
IMAGE_MANIFEST_PATH = Path("images") / "image_prompts.json"
WORKFLOW_VERSION_NAME = "workflow_version.json"


def _read_json(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analysis_selection_hash(selection: dict[str, Any]) -> str:
    """Hash every choice that can change a professional analysis image."""
    payload = {
        "analysis_required": selection.get("analysis_required"),
        "analysis_pack_id": str(selection.get("analysis_pack_id") or ""),
        "analysis_library_id": str(selection.get("analysis_library_id") or ""),
        "analysis_style_id": str(selection.get("analysis_style_id") or ""),
        "analysis_domain_id": str(selection.get("analysis_domain_id") or ""),
        "analysis_item_ids": sorted({
            str(value) for value in selection.get("analysis_item_ids", []) if str(value).strip()
        }),
        "reference_images": sorted({
            str(value) for value in selection.get("reference_images", []) if str(value).strip()
        }),
        "provider_profile": str(selection.get("provider_profile") or ""),
    }
    return _json_hash(payload)


def normalize_workflow_selection(data: dict[str, Any] | None) -> dict[str, Any]:
    """Expose schema-v3 projects through the v4 state model without rewriting them."""
    selection = dict(data or {})
    schema_version = int(selection.get("schema_version") or 0)
    if schema_version < 4 and selection:
        has_analysis = bool(selection.get("analysis_item_ids") or selection.get("analysis_pack_id"))
        selection["analysis_required"] = has_analysis
        selection["analysis_selection_confirmed"] = True
        selection["analysis_requirement_legacy_inferred"] = not has_analysis
        selection.setdefault(
            "visual_style_source",
            "user" if selection.get("visual_style") else "auto",
        )
    if selection:
        selection.setdefault("analysis_selection_hash", analysis_selection_hash(selection))
    return selection


def load_workflow_selection(project_path: str | Path) -> dict[str, Any]:
    project = Path(project_path).resolve()
    return normalize_workflow_selection(_read_json(project / SELECTION_NAME, {}) or {})


def is_schema_v4_project(project_path: str | Path) -> bool:
    project = Path(project_path).resolve()
    selection = _read_json(project / SELECTION_NAME, {}) or {}
    marker = _read_json(project / WORKFLOW_VERSION_NAME, {}) or {}
    return int(selection.get("schema_version") or 0) >= 4 or int(marker.get("schema_version") or 0) >= 4


def image_manifest_ready(
    project_path: str | Path,
    selection: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """Check the explicit analysis decision and every selected generated file."""
    project = Path(project_path).resolve()
    raw_selection = _read_json(project / SELECTION_NAME, {}) or {}
    selection = selection or normalize_workflow_selection(raw_selection)
    manifest = _read_json(project / IMAGE_MANIFEST_PATH)
    schema_version = 4 if is_schema_v4_project(project) else int(raw_selection.get("schema_version") or 0)
    required = selection.get("analysis_required")
    if schema_version >= 4 and not isinstance(required, bool):
        return False, manifest
    if required is False:
        return True, manifest
    selected_item_ids = [
        str(value) for value in selection.get("analysis_item_ids", []) if str(value).strip()
    ]
    if selected_item_ids:
        if not isinstance(manifest, dict):
            return False, None
        if manifest.get("analysis_style_id") != selection.get("analysis_style_id"):
            return False, manifest
        if schema_version >= 4 and manifest.get("analysis_selection_hash") != selection.get(
            "analysis_selection_hash"
        ):
            return False, manifest
        manifest_items = {
            str(item.get("analysis_item_id") or ""): item
            for item in manifest.get("items") or []
        }
        ready = all(
            item_id in manifest_items
            and manifest_items[item_id].get("status") == "Generated"
            and (
                project
                / "images"
                / Path(str(manifest_items[item_id].get("filename") or "")).name
            ).is_file()
            for item_id in selected_item_ids
        )
        return ready, manifest
    if selection.get("analysis_pack_id"):
        if not isinstance(manifest, dict):
            return False, None
        items = manifest.get("items") or []
        return bool(items) and all(
            item.get("status") == "Generated"
            and (project / "images" / Path(str(item.get("filename") or "")).name).is_file()
            for item in items
        ), manifest
    return (schema_version < 4), manifest


def planning_input_hash(project_path: str | Path) -> str:
    """Fingerprint sources, planning decisions, and generated analysis image bytes."""
    project = Path(project_path).resolve()
    selection = load_workflow_selection(project)
    image_facts = []
    image_dir = project / "images"
    if image_dir.is_dir():
        for image_path in sorted(image_dir.iterdir()):
            if image_path.is_file() and image_path.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff",
            }:
                image_facts.append({
                    "filename": image_path.name,
                    "sha256": _file_hash(image_path),
                })
    payload = {
        "source_manifest": _read_json(project / "source_manifest.json"),
        "workflow_brief": _read_json(project / "workflow_brief.json"),
        "selection": {
            key: selection.get(key)
            for key in (
                "visual_style",
                "visual_style_source",
                "template_id",
                "custom_style_description",
                "analysis_required",
                "analysis_selection_confirmed",
                "analysis_selection_hash",
            )
        },
        "image_pool": image_facts,
    }
    return _json_hash(payload)


def content_inventory_state(project_path: str | Path) -> tuple[bool, dict[str, Any] | None, str]:
    project = Path(project_path).resolve()
    inventory = _read_json(project / CONTENT_INVENTORY_PATH)
    if not isinstance(inventory, dict):
        return False, None, "content inventory is not ready"
    expected = planning_input_hash(project)
    if inventory.get("planning_input_hash") != expected:
        return False, inventory, "content inventory is stale after upstream changes"
    if not isinstance(inventory.get("recommended_page_count"), int):
        return False, inventory, "content inventory must include recommended_page_count"
    if not inventory.get("page_count_rationale"):
        return False, inventory, "content inventory must include page_count_rationale"
    return True, inventory, "content inventory ready"


def content_inventory_hash(project_path: str | Path) -> str:
    project = Path(project_path).resolve()
    inventory = _read_json(project / CONTENT_INVENTORY_PATH)
    if not isinstance(inventory, dict):
        return ""
    return _json_hash(inventory)


def _outline_hash(pages: list[dict[str, Any]]) -> str:
    payload = json.dumps(pages, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_outline(data: dict[str, Any]) -> list[str]:
    """Return validation errors for an outline payload."""
    errors: list[str] = []
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        return ["pages must be a non-empty array"]
    seen_ids: set[str] = set()
    require_sources = int(data.get("schema_version") or 0) >= 3
    for index, page in enumerate(pages, start=1):
        prefix = f"pages[{index - 1}]"
        if not isinstance(page, dict):
            errors.append(f"{prefix} must be an object")
            continue
        page_id = str(page.get("page_id") or "").strip()
        if not page_id:
            errors.append(f"{prefix}.page_id is required")
        elif page_id in seen_ids:
            errors.append(f"{prefix}.page_id duplicates '{page_id}'")
        seen_ids.add(page_id)
        if not str(page.get("title") or "").strip():
            errors.append(f"{prefix}.title is required")
        if not str(page.get("core_message") or "").strip():
            errors.append(f"{prefix}.core_message is required")
        if "body" not in page:
            errors.append(f"{prefix}.body is required")
        if require_sources:
            source_refs = page.get("source_refs")
            if not isinstance(source_refs, list) or not any(str(value).strip() for value in source_refs):
                errors.append(f"{prefix}.source_refs must contain at least one source reference")
        images = page.get("images")
        if not isinstance(images, list):
            errors.append(f"{prefix}.images must be an array")
        elif require_sources:
            for image_index, image in enumerate(images):
                if not isinstance(image, dict) or not str(image.get("source") or "").strip():
                    errors.append(f"{prefix}.images[{image_index}].source is required")
    return errors


def load_draft(project_path: str | Path) -> tuple[Path, dict[str, Any]]:
    project = Path(project_path).resolve()
    draft_path = project / DRAFT_NAME
    if not draft_path.is_file():
        raise ValueError(f"Outline draft not found: {draft_path}")
    try:
        data = json.loads(draft_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid outline JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Outline draft must be a JSON object")
    errors = validate_outline(data)
    if errors:
        raise ValueError("; ".join(errors))
    return draft_path, data


def confirm_outline(project_path: str | Path) -> Path:
    """Write a confirmation artifact bound to the current draft content."""
    project = Path(project_path).resolve()
    draft_path, data = load_draft(project)
    selection = load_workflow_selection(project)
    if is_schema_v4_project(project):
        gates, message = workflow_gates(project)
        required = (
            "style_confirmed",
            "analysis_decided",
            "analysis_selection_confirmed",
            "analysis_ready",
            "content_inventory_ready",
            "outline_ready",
        )
        if not all(gates.get(key) for key in required):
            raise ValueError(message)
    pages = data["pages"]
    confirmed = dict(data)
    confirmed.update(
        {
            "schema_version": max(1, int(data.get("schema_version") or 1)),
            "status": "confirmed",
            "confirmed_at": datetime.now().isoformat(timespec="seconds"),
            "outline_hash": _outline_hash(pages),
            "planning_input_hash": planning_input_hash(project),
            "content_inventory_hash": content_inventory_hash(project),
            "draft_file": draft_path.name,
        }
    )
    destination = project / CONFIRMED_NAME
    destination.write_text(
        json.dumps(confirmed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def check_outline_confirmation(project_path: str | Path, *, optional: bool = False) -> tuple[bool, str]:
    """Verify that the confirmed outline matches the current editable draft."""
    project = Path(project_path).resolve()
    draft_path = project / DRAFT_NAME
    if optional and not draft_path.exists():
        return True, "legacy project: no outline draft present"
    try:
        _, draft = load_draft(project)
    except (OSError, ValueError) as exc:
        return False, str(exc)
    confirmed_path = project / CONFIRMED_NAME
    if not confirmed_path.is_file():
        return False, f"Outline is not confirmed: {confirmed_path}"
    try:
        confirmed = json.loads(confirmed_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"Invalid confirmation artifact: {exc}"
    if confirmed.get("status") != "confirmed":
        return False, "outline_confirmed.json status must be 'confirmed'"
    expected = _outline_hash(draft["pages"])
    if confirmed.get("outline_hash") != expected:
        return False, "Outline draft changed after confirmation; confirm it again"
    selection = load_workflow_selection(project)
    if is_schema_v4_project(project):
        if confirmed.get("planning_input_hash") != planning_input_hash(project):
            return False, "Planning inputs changed after outline confirmation"
        if confirmed.get("content_inventory_hash") != content_inventory_hash(project):
            return False, "Content inventory changed after outline confirmation"
    return True, "outline confirmed"


def workflow_gates(project_path: str | Path) -> tuple[dict[str, bool], str]:
    """Return the schema-v4 planning gates and the first actionable blocker."""
    project = Path(project_path).resolve()
    raw_selection = _read_json(project / SELECTION_NAME, {}) or {}
    selection = normalize_workflow_selection(raw_selection)
    schema_version = 4 if is_schema_v4_project(project) else int(raw_selection.get("schema_version") or 0)
    style_confirmed = bool(selection.get("visual_style"))
    analysis_decided = isinstance(selection.get("analysis_required"), bool)
    analysis_selection_confirmed = bool(selection.get("analysis_selection_confirmed"))
    if selection.get("analysis_required") is True:
        analysis_selection_confirmed = analysis_selection_confirmed and bool(
            selection.get("analysis_style_id")
            and selection.get("analysis_item_ids")
            and selection.get("analysis_library_id")
        )
    analysis_ready, _ = image_manifest_ready(project, selection)
    inventory_ready, _, inventory_message = content_inventory_state(project)
    draft_ready = False
    try:
        _, draft = load_draft(project)
        draft_ready = (
            schema_version < 4
            or (
                draft.get("planning_input_hash") == planning_input_hash(project)
                and draft.get("content_inventory_hash") == content_inventory_hash(project)
            )
        )
    except (OSError, ValueError):
        pass
    confirmed, confirm_message = check_outline_confirmation(
        project,
        optional=schema_version < 4,
    )
    gates = {
        "style_confirmed": style_confirmed if schema_version >= 4 else True,
        "analysis_decided": analysis_decided if schema_version >= 4 else True,
        "analysis_selection_confirmed": analysis_selection_confirmed if schema_version >= 4 else True,
        "analysis_ready": analysis_ready if schema_version >= 4 else True,
        "content_inventory_ready": inventory_ready if schema_version >= 4 else True,
        "outline_ready": draft_ready if schema_version >= 4 else confirmed,
        "outline_confirmed": confirmed,
    }
    gates["generation_unlocked"] = all(gates.values())
    blockers = (
        ("style_confirmed", "select or accept a presentation visual style"),
        ("analysis_decided", "confirm whether professional analysis images are required"),
        ("analysis_selection_confirmed", "confirm the analysis style and domain"),
        ("analysis_ready", "generate every selected analysis image"),
        ("content_inventory_ready", inventory_message),
        ("outline_ready", "create an outline from the current content inventory"),
        ("outline_confirmed", confirm_message),
    )
    message = "generation unlocked"
    for key, blocker in blockers:
        if not gates[key]:
            message = blocker
            break
    return gates, message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the PPT Master outline confirmation gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "confirm", "check"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("project", help="PPT Master project path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            load_draft(args.project)
            message = "outline draft is valid"
        elif args.command == "confirm":
            message = str(confirm_outline(args.project))
        else:
            selection = load_workflow_selection(args.project)
            if is_schema_v4_project(args.project):
                gates, message = workflow_gates(args.project)
                valid = gates["generation_unlocked"]
            else:
                valid, message = check_outline_confirmation(args.project)
            if not valid:
                print(f"Error: {message}", file=sys.stderr)
                return 1
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
