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
        images = page.get("images")
        if not isinstance(images, list):
            errors.append(f"{prefix}.images must be an array")
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
    pages = data["pages"]
    confirmed = dict(data)
    confirmed.update(
        {
            "schema_version": max(1, int(data.get("schema_version") or 1)),
            "status": "confirmed",
            "confirmed_at": datetime.now().isoformat(timespec="seconds"),
            "outline_hash": _outline_hash(pages),
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
    return True, "outline confirmed"


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
