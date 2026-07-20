#!/usr/bin/env python3
"""
PPT Master - Analysis Prompt Matrix

Compile a multi-sheet Excel workbook into analysis styles, grouped analysis
types, and a style-by-type prompt matrix. Build standard image manifests from
one selected style and one or more selected analysis types.

Usage:
    python3 scripts/analysis_library.py compile <workbook.xlsx> [-o output_dir]
    python3 scripts/analysis_library.py build-manifest <library_dir> <project> \
        --style <style-id> --item <analysis-id> --reference <image>

Examples:
    python3 scripts/analysis_library.py compile templates/analysis-library/diagram-prompt-building/prompts_master.xlsx
    python3 scripts/analysis_library.py build-manifest templates/analysis-library/diagram-prompt-building projects/demo --style light_fresh_ppt_detailed --item ARC-010 --reference render.png

Dependencies:
    openpyxl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from analysis_pack import DEFAULT_PROFILE, build_image_manifest
from console_encoding import configure_utf8_stdio


configure_utf8_stdio()

LIBRARY_ID = "diagram-prompt-building-v1"
SOURCE_COLUMNS = (
    "id",
    "category_l1",
    "category_l2",
    "graphic_mode",
    "style_id",
    "style_label",
    "style_tags",
    "title",
    "prompt_final",
    "template_id",
    "notes",
)
DOMAIN_IDS = {
    "建筑": "architecture",
    "室内": "interior",
    "景观": "landscape",
    "城市规划": "planning",
    "规划": "planning",
}
EDITABLE_OVERLAY_SUFFIX = (
    "\n\n「PPT 可编辑输出约束（优先级最高）」成图内不要生成标题、段落、图例文字、"
    "地名、尺寸、层数、百分比或其他数值；不得虚构测绘、性能或计算数据。"
    "使用无文字色块、线型、箭头与符号表达分析关系，并为后续 PPT/SVG 可编辑文字层保留留白。"
    "不得生成水印、签名或 AI 标识。"
)


def _require_openpyxl():
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError(
            "openpyxl is required for analysis libraries. Run: pip install openpyxl"
        ) from exc
    return openpyxl


def _text(value: Any) -> str:
    return str(value or "").strip()


def _stable_id(value: str) -> str:
    stable_id = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]+", stable_id):
        raise ValueError(f"invalid id: {value!r}")
    return stable_id


def _row_map(headers: list[str], values: tuple[Any, ...]) -> dict[str, Any]:
    return {
        name: values[headers.index(name)] if headers.index(name) < len(values) else None
        for name in SOURCE_COLUMNS
    }


def compile_library(
    workbook_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    library_id: str = LIBRARY_ID,
) -> Path:
    """Compile one-style-per-sheet Excel into three stable runtime JSON files."""
    openpyxl = _require_openpyxl()
    source = Path(workbook_path).resolve()
    if not source.is_file():
        raise ValueError(f"Workbook not found: {source}")
    destination = Path(output_dir).resolve() if output_dir else source.parent
    destination.mkdir(parents=True, exist_ok=True)

    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    styles: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []
    canonical_types: dict[str, dict[str, Any]] = {}
    canonical_ids: set[str] | None = None
    seen_style_ids: set[str] = set()

    for sheet in workbook.worksheets:
        rows = sheet.iter_rows(values_only=True)
        try:
            headers = [_text(value) for value in next(rows)]
        except StopIteration as exc:
            raise ValueError(f"Worksheet is empty: {sheet.title}") from exc
        missing = [name for name in SOURCE_COLUMNS if name not in headers]
        if missing:
            raise ValueError(
                f"Worksheet '{sheet.title}' missing column(s): {', '.join(missing)}"
            )

        sheet_rows: list[dict[str, Any]] = []
        seen_item_ids: set[str] = set()
        for row_number, values in enumerate(rows, start=2):
            row = _row_map(headers, values)
            if not any(_text(value) for value in row.values()):
                continue
            item_id = _text(row["id"])
            style_id = _stable_id(_text(row["style_id"]))
            prompt = _text(row["prompt_final"])
            if not item_id or not prompt:
                raise ValueError(
                    f"Worksheet '{sheet.title}' row {row_number}: id and prompt_final are required"
                )
            if not re.fullmatch(r"[A-Za-z0-9_-]+", item_id):
                raise ValueError(
                    f"Worksheet '{sheet.title}' row {row_number}: invalid id '{item_id}'"
                )
            if not _text(row["template_id"]):
                raise ValueError(
                    f"Worksheet '{sheet.title}' row {row_number}: template_id is required"
                )
            if item_id in seen_item_ids:
                raise ValueError(
                    f"Worksheet '{sheet.title}' row {row_number}: duplicate id '{item_id}'"
                )
            seen_item_ids.add(item_id)
            sheet_rows.append({**row, "id": item_id, "style_id": style_id})

        if not sheet_rows:
            raise ValueError(f"Worksheet has no prompt rows: {sheet.title}")
        style_ids = {row["style_id"] for row in sheet_rows}
        if len(style_ids) != 1:
            raise ValueError(
                f"Worksheet '{sheet.title}' must contain exactly one style_id"
            )
        style_id = next(iter(style_ids))
        if style_id in seen_style_ids:
            raise ValueError(f"duplicate style_id across worksheets: {style_id}")
        seen_style_ids.add(style_id)

        if canonical_ids is None:
            canonical_ids = set(seen_item_ids)
        elif seen_item_ids != canonical_ids:
            missing_ids = sorted(canonical_ids - seen_item_ids)
            extra_ids = sorted(seen_item_ids - canonical_ids)
            raise ValueError(
                f"Worksheet '{sheet.title}' type set differs; "
                f"missing={missing_ids[:5]}, extra={extra_ids[:5]}"
            )

        domain_counts: Counter[str] = Counter()
        for row in sheet_rows:
            item_id = row["id"]
            domain_name = _text(row["category_l1"])
            domain_id = DOMAIN_IDS.get(domain_name)
            if not domain_id:
                raise ValueError(
                    f"Worksheet '{sheet.title}' item {item_id}: unsupported domain '{domain_name}'"
                )
            domain_counts[domain_id] += 1
            template_id = _text(row["template_id"])
            title = _text(row["title"]) or _text(row["category_l2"]) or item_id
            type_record = {
                "id": item_id,
                "domain_id": domain_id,
                "domain_name_zh": domain_name,
                "name_zh": title,
                "category_zh": _text(row["category_l2"]),
                "template_id": template_id,
                "graphic_mode": _text(row["graphic_mode"]),
            }
            prior = canonical_types.get(item_id)
            if prior is not None and prior != type_record:
                raise ValueError(
                    f"Analysis type metadata drift for {item_id} in worksheet '{sheet.title}'"
                )
            canonical_types[item_id] = type_record
            safe_template_id = re.sub(r"[^a-z0-9_-]+", "_", template_id.lower()).strip("_")
            matrix.append(
                {
                    "style_id": style_id,
                    "analysis_item_id": item_id,
                    "domain_id": domain_id,
                    "template_id": template_id,
                    "name_zh": title,
                    "graphic_mode": _text(row["graphic_mode"]),
                    "prompt_template": _text(row["prompt_final"]),
                    "output_filename": f"{item_id}__{safe_template_id}__{style_id}.png",
                    "notes": _text(row["notes"]),
                }
            )

        first = sheet_rows[0]
        preview_dir = destination / "previews"
        preview_candidates = [
            preview_dir / f"{style_id}{suffix}"
            for suffix in (".svg", ".png", ".jpg", ".jpeg", ".webp")
        ]
        preview_path = next((path for path in preview_candidates if path.is_file()), None)
        if preview_path is None:
            raise ValueError(
                f"Analysis style '{style_id}' is missing a preview under "
                f"{preview_dir}"
            )
        styles.append(
            {
                "id": style_id,
                "name_zh": _text(first["style_label"]) or sheet.title,
                "sheet_name": sheet.title,
                "preview": preview_path.relative_to(destination).as_posix(),
                "tags": [tag for tag in _text(first["style_tags"]).split("|") if tag],
                "item_count": len(sheet_rows),
                "domain_counts": dict(domain_counts),
            }
        )

    if not styles or not canonical_types:
        raise ValueError("Workbook contains no analysis styles or types")

    domain_order = ("architecture", "interior", "landscape", "planning")
    domain_names = {
        "architecture": "建筑",
        "interior": "室内",
        "landscape": "景观",
        "planning": "规划",
    }
    domains = []
    for domain_id in domain_order:
        items = [
            canonical_types[item_id]
            for item_id in sorted(canonical_types)
            if canonical_types[item_id]["domain_id"] == domain_id
        ]
        if items:
            domains.append(
                {
                    "id": domain_id,
                    "name_zh": domain_names[domain_id],
                    "item_count": len(items),
                    "items": items,
                }
            )

    generated_at = datetime.now().isoformat(timespec="seconds")
    common = {
        "schema_version": 1,
        "library_id": _stable_id(library_id),
        "source_workbook": source.name,
        "compiled_at": generated_at,
    }
    payloads = {
        "styles.json": {
            **common,
            "default_style_id": styles[0]["id"],
            "style_count": len(styles),
            "styles": styles,
        },
        "analysis_types.json": {
            **common,
            "domain_count": len(domains),
            "type_count": len(canonical_types),
            "domains": domains,
        },
        "prompt_matrix.json": {
            **common,
            "style_count": len(styles),
            "type_count": len(canonical_types),
            "entry_count": len(matrix),
            "entries": matrix,
        },
    }
    for filename, payload in payloads.items():
        (destination / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return destination


def load_library(library_dir: str | Path) -> dict[str, Any]:
    """Load the compiled library catalog used by the wizard."""
    directory = Path(library_dir).resolve()
    styles_path = directory / "styles.json"
    types_path = directory / "analysis_types.json"
    matrix_path = directory / "prompt_matrix.json"
    missing = [path.name for path in (styles_path, types_path, matrix_path) if not path.is_file()]
    if missing:
        raise ValueError(f"Analysis library missing compiled file(s): {', '.join(missing)}")
    styles = json.loads(styles_path.read_text(encoding="utf-8"))
    types = json.loads(types_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    for style in styles.get("styles", []):
        preview = str(style.get("preview") or "")
        preview_path = (directory / preview).resolve()
        if not preview or directory not in preview_path.parents or not preview_path.is_file():
            raise ValueError(
                f"Analysis style '{style.get('id')}' has an invalid preview: {preview}"
            )
    return {
        "schema_version": 1,
        "library_id": styles["library_id"],
        "default_style_id": styles["default_style_id"],
        "styles": styles["styles"],
        "domains": types["domains"],
        "matrix": matrix,
    }


def resolve_domain_item_ids(
    library: dict[str, Any],
    domain_id: str,
    explicit_item_ids: list[str] | None = None,
) -> list[str]:
    """Resolve a user-facing domain into internal analysis type ids."""
    domain = next(
        (item for item in library.get("domains", []) if item.get("id") == domain_id),
        None,
    )
    if domain is None:
        raise ValueError(f"Unknown analysis domain: {domain_id}")
    valid_ids = {str(item.get("id") or "") for item in domain.get("items", [])}
    requested = list(
        dict.fromkeys(
            _text(item_id)
            for item_id in (explicit_item_ids or [])
            if _text(item_id)
        )
    )
    if requested:
        unknown = [item_id for item_id in requested if item_id not in valid_ids]
        if unknown:
            raise ValueError(
                f"Analysis type(s) outside domain '{domain_id}': {', '.join(unknown)}"
            )
        return requested
    return [str(item.get("id")) for item in domain.get("items", []) if item.get("id")]


def build_library_manifest(
    library_dir: str | Path,
    project_path: str | Path,
    style_id: str,
    item_ids: list[str],
    reference_images: list[str],
    *,
    provider_profile: str = DEFAULT_PROFILE,
    prompt_context: str = "",
) -> Path:
    """Build the standard image manifest from one style and selected type ids."""
    library = load_library(library_dir)
    selected_ids = list(dict.fromkeys(_text(item_id) for item_id in item_ids if _text(item_id)))
    if not selected_ids:
        raise ValueError("Select at least one analysis type")
    valid_styles = {style["id"] for style in library["styles"]}
    if style_id not in valid_styles:
        raise ValueError(f"Unknown analysis style: {style_id}")

    type_by_id = {
        item["id"]: item
        for domain in library["domains"]
        for item in domain.get("items", [])
    }
    unknown = [item_id for item_id in selected_ids if item_id not in type_by_id]
    if unknown:
        raise ValueError(f"Unknown analysis type(s): {', '.join(unknown)}")
    entries = {
        entry["analysis_item_id"]: entry
        for entry in library["matrix"]["entries"]
        if entry.get("style_id") == style_id
    }
    missing = [item_id for item_id in selected_ids if item_id not in entries]
    if missing:
        raise ValueError(
            f"Style '{style_id}' has no prompt for: {', '.join(missing)}"
        )

    pack_items = []
    for item_id in selected_ids:
        entry = entries[item_id]
        item_type = type_by_id[item_id]
        prompt = entry["prompt_template"] + EDITABLE_OVERLAY_SUFFIX
        if prompt_context.strip():
            prompt = f"{prompt_context.strip()}\n\n{prompt}"
        pack_items.append(
            {
                "item_id": item_id,
                "category": item_type["domain_name_zh"],
                "name": item_type["name_zh"],
                "prompt_template": prompt,
                "output_filename": entry["output_filename"],
                "aspect_ratio": "16:9",
                "image_size": "1K",
                "enabled": True,
                "reference_role": "project-render",
                "notes": entry.get("notes", ""),
                "analysis_library_id": library["library_id"],
                "analysis_style_id": style_id,
                "analysis_domain_id": item_type["domain_id"],
                "analysis_template_id": item_type["template_id"],
            }
        )

    project = Path(project_path).resolve()
    compiled_selection = project / "analysis" / "analysis_selection.compiled.json"
    compiled_selection.parent.mkdir(parents=True, exist_ok=True)
    compiled_selection.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pack_id": library["library_id"],
                "analysis_library_id": library["library_id"],
                "analysis_style_id": style_id,
                "item_count": len(pack_items),
                "enabled_count": len(pack_items),
                "items": pack_items,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return build_image_manifest(
        compiled_selection,
        project,
        reference_images,
        provider_profile=provider_profile,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile and use the two-level analysis prompt matrix.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile the source workbook")
    compile_parser.add_argument("workbook", help="One-style-per-sheet .xlsx workbook")
    compile_parser.add_argument("-o", "--output", help="Output directory")
    compile_parser.add_argument("--library-id", default=LIBRARY_ID, help="Stable library id")

    manifest_parser = subparsers.add_parser(
        "build-manifest", help="Build image_prompts.json from selected types"
    )
    manifest_parser.add_argument("library", help="Compiled analysis library directory")
    manifest_parser.add_argument("project", help="PPT Master project path")
    manifest_parser.add_argument("--style", required=True, help="Selected analysis style id")
    manifest_parser.add_argument("--item", action="append", default=[], help="Analysis type id")
    manifest_parser.add_argument("--reference", action="append", default=[], help="Reference image")
    manifest_parser.add_argument("--profile", default=DEFAULT_PROFILE, help="Provider profile")
    manifest_parser.add_argument("--prompt-context", default="", help="Project prompt context")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "compile":
            output = compile_library(
                args.workbook,
                args.output,
                library_id=args.library_id,
            )
        else:
            output = build_library_manifest(
                args.library,
                args.project,
                args.style,
                args.item,
                args.reference,
                provider_profile=args.profile,
                prompt_context=args.prompt_context,
            )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
