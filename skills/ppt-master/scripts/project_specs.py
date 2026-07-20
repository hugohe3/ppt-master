#!/usr/bin/env python3
"""
PPT Master - Project Specification Helpers

Scaffold and validate the Markdown planning artifacts used by project_manager.py.
The module keeps schema parsing and deterministic scaffold rendering independent
from the broader project-management command surface.

Usage:
    Import validate_project_artifacts() or scaffold_project_artifact().

Examples:
    from project_specs import validate_markdown_schema

Dependencies:
    None (only uses the standard library and local project modules)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

try:
    from project_utils import (
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        validate_communication_trace,
    )
except ImportError:
    import sys

    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from project_utils import (  # type: ignore
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        validate_communication_trace,
    )


TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
SCHEMA_DIR = SKILL_DIR / "templates" / "schemas"
SCAFFOLD_DIR = SKILL_DIR / "templates" / "scaffolds"

_CUSTOM_REFERENCE_CATALOGS = (
    ("mode", "mode", "mode_references", SKILL_DIR / "references" / "modes"),
    (
        "visual_style",
        "visual_style",
        "visual_style_references",
        SKILL_DIR / "references" / "visual-styles",
    ),
    (
        "colors",
        "image_rendering",
        "image_rendering_references",
        SKILL_DIR / "references" / "image-renderings",
    ),
)

_MARKDOWN_H2_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_MARKDOWN_SUBHEADING_RE = re.compile(r"^#{3,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_MARKDOWN_DATA_LINE_RE = re.compile(
    r"^[ \t]*-[ \t]+(?:\*\*)?([^:\n*]+?)(?:\*\*)?[ \t]*:[ \t]*(.*)$",
    re.MULTILINE,
)
_SCAFFOLD_TOKEN_RE = re.compile(r"\{\{[A-Z_]+\}\}")
_SCHEMA_MARKER_RE = re.compile(
    r"^<!--[ \t]+ppt-master-schema:[ \t]*([a-z0-9-]+/v[1-9][0-9]*)[ \t]+-->$",
    re.IGNORECASE,
)

def _normalize_schema_value(value: str) -> str:
    """Normalize a Markdown scalar before enum, pattern, and catalog checks."""
    normalized = value.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in "'\"`"
    ):
        return normalized[1:-1].strip()
    return normalized


def _extract_schema_marker(text: str) -> tuple[str | None, str | None]:
    """Read the optional version marker from the first non-empty line."""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line.startswith("<!--") or "ppt-master-schema:" not in first_line:
        return None, None
    match = _SCHEMA_MARKER_RE.fullmatch(first_line)
    if match is None:
        return None, "has a malformed ppt-master-schema marker"
    return match.group(1).casefold(), None


def _parse_markdown_sections(
    text: str,
    *,
    report_duplicate_fields: bool,
) -> tuple[list[dict[str, object]], list[str]]:
    """Parse H2 sections, data lines, and nested headings from Markdown."""
    headings = list(_MARKDOWN_H2_RE.finditer(text))
    sections: list[dict[str, object]] = []
    errors: list[str] = []

    for index, heading_match in enumerate(headings):
        body_start = heading_match.end()
        body_end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[body_start:body_end]
        fields: dict[str, str] = {}
        field_names: dict[str, str] = {}

        for field_match in _MARKDOWN_DATA_LINE_RE.finditer(body):
            field_name = field_match.group(1).strip()
            field_key = field_name
            if field_key in fields and report_duplicate_fields:
                errors.append(
                    f"section '{heading_match.group(1).strip()}' repeats data key "
                    f"'{field_name}'"
                )
                continue
            fields[field_key] = field_match.group(2).strip()
            field_names[field_key] = field_name

        sections.append(
            {
                "heading": heading_match.group(1).strip(),
                "offset": heading_match.start(),
                "body": body,
                "fields": fields,
                "field_names": field_names,
                "subheadings": [
                    match.group(1).strip()
                    for match in _MARKDOWN_SUBHEADING_RE.finditer(body)
                ],
            }
        )

    return sections, errors


def parse_markdown_artifact(
    markdown_path: Path,
    *,
    report_duplicate_fields: bool = False,
) -> list[dict[str, object]]:
    """Parse one Markdown planning artifact without changing it.

    This is the public read-only entry point for consumers that need the same
    heading/data-line grammar as schema validation.  Keeping the parser here
    prevents runtime projections from drifting into their own lock grammar.
    """
    text = markdown_path.read_text(encoding="utf-8")
    sections, errors = _parse_markdown_sections(
        text,
        report_duplicate_fields=report_duplicate_fields,
    )
    if errors:
        raise ValueError("; ".join(errors))
    return sections


def default_spec_lock_forbidden() -> frozenset[str]:
    """Return the versioned scaffold's universal forbidden-item defaults."""
    sections = parse_markdown_artifact(SCAFFOLD_DIR / "spec_lock.md")
    section = next(
        (
            item
            for item in sections
            if str(item.get("heading", "")).strip().casefold() == "forbidden"
        ),
        None,
    )
    if section is None:
        raise ValueError("spec-lock scaffold has no forbidden section")
    return frozenset(
        re.sub(r"^-[ \t]+", "", line.strip())
        for line in str(section.get("body", "")).splitlines()
        if line.strip()
    )


def _load_markdown_schema(schema_path: Path) -> dict[str, object]:
    """Load and sanity-check one versioned Markdown schema."""
    with schema_path.open("r", encoding="utf-8") as stream:
        schema = json.load(stream)
    contract = schema.get("x-markdown")
    if not isinstance(contract, dict):
        raise ValueError(f"Schema is missing x-markdown: {schema_path}")
    if contract.get("version") != 1:
        raise ValueError(f"Unsupported Markdown schema version: {schema_path}")
    return schema


def _catalog_values(
    schema_path: Path,
    value_catalog: Mapping[str, object],
) -> tuple[Path, dict[str, object]]:
    """Resolve a schema-declared JSON catalog and object pointer."""
    relative_path = value_catalog.get("path")
    pointer = value_catalog.get("pointer", [])
    if not isinstance(relative_path, str) or not isinstance(pointer, list):
        raise ValueError("value_catalog requires string path and list pointer")

    catalog_path = (schema_path.parent / relative_path).resolve()
    with catalog_path.open("r", encoding="utf-8") as stream:
        node: object = json.load(stream)
    for pointer_part in pointer:
        if not isinstance(node, dict):
            raise ValueError(f"pointer enters a non-object at '{pointer_part}'")
        node = node[str(pointer_part)]
    if not isinstance(node, dict):
        raise ValueError("catalog pointer does not resolve to an object")
    return catalog_path, node


def _validate_catalog_values(
    *,
    markdown_name: str,
    section_id: str,
    fields: Mapping[str, object],
    schema_path: Path,
    value_catalog: Mapping[str, object],
) -> list[str]:
    """Validate catalog membership and any schema-declared asset path."""
    errors: list[str] = []
    relative_path = value_catalog.get("path")
    try:
        catalog_path, catalog = _catalog_values(schema_path, value_catalog)
    except (OSError, KeyError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return [
            f"{markdown_name} schema: cannot read value catalog "
            f"'{relative_path}': {exc}"
        ]

    asset_pattern = value_catalog.get("asset_path_pattern")
    for field_value in fields.values():
        value = _normalize_schema_value(str(field_value))
        if value not in catalog:
            errors.append(
                f"{markdown_name} schema: section '{section_id}' value '{value}' "
                f"is absent from {catalog_path.name}"
            )
            continue
        if not isinstance(asset_pattern, str):
            continue
        try:
            relative_asset_path = asset_pattern.format(key=value, value=value)
        except (KeyError, ValueError) as exc:
            errors.append(
                f"{markdown_name} schema: invalid asset_path_pattern "
                f"'{asset_pattern}': {exc}"
            )
            break
        asset_path = (schema_path.parent / relative_asset_path).resolve()
        if asset_path.suffix.casefold() != ".svg" or not asset_path.is_file():
            errors.append(
                f"{markdown_name} schema: section '{section_id}' value '{value}' "
                f"does not resolve to an SVG asset at {asset_path}"
            )
    return errors


def _validate_section(
    *,
    markdown_name: str,
    section_id: str,
    section: Mapping[str, object],
    definition: Mapping[str, object],
    schema_path: Path,
) -> list[str]:
    """Apply one section definition to one matched Markdown section."""
    errors: list[str] = []
    fields = section["fields"]
    assert isinstance(fields, dict)

    required_fields = definition.get("required_fields", [])
    allow_empty = {
        str(field_name)
        for field_name in definition.get("allow_empty_fields", [])
    }
    if isinstance(required_fields, list):
        for field_name in required_fields:
            field_key = str(field_name)
            if field_key not in fields:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' is missing field "
                    f"'{field_name}'"
                )
            elif (
                field_key not in allow_empty
                and not _normalize_schema_value(str(fields[field_key]))
            ):
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' field "
                    f"'{field_name}' must not be empty"
                )

    allowed_fields = definition.get("allowed_fields")
    if isinstance(allowed_fields, list):
        allowed = {str(field_name) for field_name in allowed_fields}
        for field_name in fields:
            if field_name not in allowed:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' has unknown "
                    f"field '{field_name}'"
                )

    field_enums = definition.get("field_enums", {})
    if isinstance(field_enums, dict):
        for field_name, allowed in field_enums.items():
            field_key = str(field_name)
            if field_key not in fields or not isinstance(allowed, list):
                continue
            value = _normalize_schema_value(str(fields[field_key]))
            if value not in [str(item) for item in allowed]:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' field "
                    f"'{field_name}' has illegal value '{value}'"
                )

    field_patterns = definition.get("field_patterns", {})
    if isinstance(field_patterns, dict):
        for field_name, pattern in field_patterns.items():
            field_key = str(field_name)
            if field_key not in fields:
                continue
            value = _normalize_schema_value(str(fields[field_key]))
            if re.fullmatch(str(pattern), value) is None:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' field "
                    f"'{field_name}' does not match '{pattern}'"
                )

    minimum = definition.get("min_entries")
    if isinstance(minimum, int) and len(fields) < minimum:
        errors.append(
            f"{markdown_name} schema: section '{section_id}' needs at least "
            f"{minimum} data line(s)"
        )

    min_body_chars = definition.get("min_body_chars")
    if isinstance(min_body_chars, int) and len(str(section["body"]).strip()) < min_body_chars:
        errors.append(
            f"{markdown_name} schema: section '{section_id}' must contain content"
        )

    entry_key_pattern = definition.get("entry_key_pattern")
    if isinstance(entry_key_pattern, str):
        field_names = section["field_names"]
        assert isinstance(field_names, dict)
        for field_name in field_names.values():
            if re.fullmatch(entry_key_pattern, str(field_name)) is None:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' has malformed "
                    f"entry key '{field_name}'"
                )

    value_enum = definition.get("value_enum")
    if isinstance(value_enum, list):
        allowed_values = [str(item) for item in value_enum]
        for field_value in fields.values():
            value = _normalize_schema_value(str(field_value))
            if value not in allowed_values:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' has illegal "
                    f"value '{value}'"
                )

    value_pattern = definition.get("value_pattern")
    if isinstance(value_pattern, str):
        for field_value in fields.values():
            value = _normalize_schema_value(str(field_value))
            if re.fullmatch(value_pattern, value) is None:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' has malformed "
                    f"value '{value}'"
                )

    value_catalog = definition.get("value_catalog")
    if isinstance(value_catalog, dict):
        errors.extend(
            _validate_catalog_values(
                markdown_name=markdown_name,
                section_id=section_id,
                fields=fields,
                schema_path=schema_path,
                value_catalog=value_catalog,
            )
        )
    return errors


def _condition_applies(
    when: Mapping[str, object],
    matched: Mapping[str, dict[str, object] | None],
) -> bool:
    """Return whether a schema condition applies to the matched document."""
    section = matched.get(str(when.get("section", "")))
    if section is None:
        return False
    applies = True
    field_name = when.get("field")
    if field_name is not None:
        fields = section["fields"]
        assert isinstance(fields, dict)
        field_value = fields.get(str(field_name))
        applies = field_value is not None
        if applies and "equals" in when:
            applies = _normalize_schema_value(str(field_value)) == str(when["equals"])
    body_regex = when.get("body_regex")
    if applies and isinstance(body_regex, str):
        applies = re.search(body_regex, str(section["body"])) is not None
    return applies


def _validate_condition(
    *,
    markdown_name: str,
    condition_id: str,
    then: Mapping[str, object],
    matched: Mapping[str, dict[str, object] | None],
) -> list[str]:
    """Apply one active cross-section condition."""
    errors: list[str] = []

    required_sections = then.get("required_sections", [])
    if isinstance(required_sections, list):
        for section_id in required_sections:
            if matched.get(str(section_id)) is None:
                errors.append(
                    f"{markdown_name} schema: condition '{condition_id}' requires "
                    f"section '{section_id}'"
                )

    forbidden_sections = then.get("forbidden_sections", [])
    if isinstance(forbidden_sections, list):
        for section_id in forbidden_sections:
            if matched.get(str(section_id)) is not None:
                errors.append(
                    f"{markdown_name} schema: condition '{condition_id}' forbids "
                    f"section '{section_id}'"
                )

    field_groups = then.get("required_fields", [])
    if isinstance(field_groups, list):
        for group in field_groups:
            if not isinstance(group, dict):
                continue
            target_id = str(group.get("section", ""))
            target = matched.get(target_id)
            if target is None:
                continue
            target_fields = target["fields"]
            assert isinstance(target_fields, dict)
            for field_name in group.get("fields", []):
                field_key = str(field_name)
                if field_key not in target_fields:
                    errors.append(
                        f"{markdown_name} schema: condition '{condition_id}' requires "
                        f"field '{field_name}' in section '{target_id}'"
                    )
                elif not _normalize_schema_value(str(target_fields[field_key])):
                    errors.append(
                        f"{markdown_name} schema: condition '{condition_id}' requires "
                        f"non-empty field '{field_name}' in section '{target_id}'"
                    )

    field_values = then.get("field_values", [])
    if isinstance(field_values, list):
        for value_rule in field_values:
            if not isinstance(value_rule, dict):
                continue
            target_id = str(value_rule.get("section", ""))
            target = matched.get(target_id)
            if target is None:
                continue
            target_fields = target["fields"]
            assert isinstance(target_fields, dict)
            target_field = str(value_rule.get("field", ""))
            value = target_fields.get(target_field)
            allowed = value_rule.get("enum", [])
            if value is None or not isinstance(allowed, list):
                continue
            normalized = _normalize_schema_value(str(value))
            if normalized not in [str(item) for item in allowed]:
                errors.append(
                    f"{markdown_name} schema: condition '{condition_id}' requires "
                    f"'{target_id}.{target_field}' to be one of {allowed}"
                )

    subheading_rules = then.get("required_subheadings", [])
    if isinstance(subheading_rules, list):
        for rule in subheading_rules:
            if not isinstance(rule, dict):
                continue
            target_id = str(rule.get("section", ""))
            target = matched.get(target_id)
            if target is None:
                continue
            heading = str(rule.get("heading", ""))
            subheadings = target["subheadings"]
            assert isinstance(subheadings, list)
            if not any(
                str(item).startswith(heading)
                for item in subheadings
            ):
                errors.append(
                    f"{markdown_name} schema: condition '{condition_id}' requires "
                    f"subheading '{heading}' in section '{target_id}'"
                )
    return errors


def _validate_slides(
    *,
    markdown_name: str,
    slide_contract: Mapping[str, object],
    matched: Mapping[str, dict[str, object] | None],
) -> list[str]:
    """Validate repeated slide blocks inside the configured outline section."""
    outline = matched.get(str(slide_contract.get("section", "")))
    heading_pattern = str(slide_contract.get("heading_pattern", ""))
    if outline is None or not heading_pattern:
        return []

    body = str(outline["body"])
    heading_matches = [
        match
        for match in _MARKDOWN_SUBHEADING_RE.finditer(body)
        if re.match(heading_pattern, match.group(1))
    ]
    if not heading_matches:
        return [f"{markdown_name} schema: content outline has no Slide blocks"]

    errors: list[str] = []
    required_fields = slide_contract.get("required_fields", [])
    if not isinstance(required_fields, list):
        return errors
    for index, slide_match in enumerate(heading_matches):
        block_end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(body)
        )
        block = body[slide_match.end():block_end]
        for field_name in required_fields:
            pattern = (
                rf"^[ \t]*-[ \t]+(?:\*\*)?{re.escape(str(field_name))}"
                rf"(?:\*\*)?[ \t]*:"
            )
            if re.search(pattern, block, flags=re.MULTILINE) is None:
                errors.append(
                    f"{markdown_name} schema: '{slide_match.group(1)}' is missing "
                    f"field '{field_name}'"
                )
    return errors


def _validate_references(
    *,
    markdown_path: Path,
    markdown_name: str,
    rules: object,
    matched: Mapping[str, dict[str, object] | None],
) -> list[str]:
    """Validate schema-declared cross-section keys and project assets."""
    if not isinstance(rules, list):
        return []
    errors: list[str] = []
    project_root = markdown_path.parent.resolve()

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rule_id = str(rule.get("id", "reference"))
        source_id = str(rule.get("from_section", ""))
        source = matched.get(source_id)
        if source is None:
            continue
        source_fields = source["fields"]
        assert isinstance(source_fields, dict)

        target_id = rule.get("target_section")
        target_fields: Mapping[str, object] | None = None
        if isinstance(target_id, str):
            target = matched.get(target_id)
            if target is None:
                continue
            raw_target_fields = target["fields"]
            assert isinstance(raw_target_fields, dict)
            target_fields = raw_target_fields

        component = rule.get("value_component")
        asset_pattern = rule.get("asset_path_pattern")
        for source_key, raw_value in source_fields.items():
            value = _normalize_schema_value(str(raw_value))
            reference_value = value
            if isinstance(component, dict):
                separator = str(component.get("separator", "|"))
                index = component.get("index", 0)
                parts = [part.strip() for part in value.split(separator)]
                if not isinstance(index, int) or index >= len(parts):
                    errors.append(
                        f"{markdown_name} schema: reference '{rule_id}' cannot "
                        f"parse value '{value}' from section '{source_id}'"
                    )
                    continue
                reference_value = _normalize_schema_value(parts[index])

            if target_fields is not None:
                if reference_value not in target_fields:
                    errors.append(
                        f"{markdown_name} schema: reference '{rule_id}' value "
                        f"'{reference_value}' from '{source_id}.{source_key}' is not "
                        f"declared in section '{target_id}'"
                    )

            if isinstance(asset_pattern, str):
                asset_value = reference_value
                suffix_match = re.search(r"\{value\}(\.[A-Za-z0-9]+)$", asset_pattern)
                if (
                    suffix_match is not None
                    and asset_value.casefold().endswith(
                        suffix_match.group(1).casefold()
                    )
                ):
                    asset_value = asset_value[: -len(suffix_match.group(1))]
                try:
                    relative_asset = asset_pattern.format(value=asset_value)
                except (KeyError, ValueError) as exc:
                    errors.append(
                        f"{markdown_name} schema: reference '{rule_id}' has invalid "
                        f"asset_path_pattern '{asset_pattern}': {exc}"
                    )
                    continue
                asset_path = (project_root / relative_asset).resolve()
                try:
                    asset_path.relative_to(project_root)
                except ValueError:
                    errors.append(
                        f"{markdown_name} schema: reference '{rule_id}' escapes the "
                        f"project root for value '{reference_value}'"
                    )
                    continue
                if asset_path.suffix.casefold() != ".svg" or not asset_path.is_file():
                    errors.append(
                        f"{markdown_name} schema: reference '{rule_id}' value "
                        f"'{reference_value}' does not resolve to {asset_path}"
                    )
    return errors


def _validate_strict_data_surface(
    markdown_name: str,
    text: str,
    sections: list[dict[str, object]],
    matched: Mapping[str, dict[str, object] | None],
) -> list[str]:
    """Reject unknown lock sections and prose outside the data-line grammar."""
    errors: list[str] = []
    section_ids = {
        int(section["offset"]): section_id
        for section_id, section in matched.items()
        if section is not None
    }
    first_offset = min((int(section["offset"]) for section in sections), default=len(text))
    for line in text[:first_offset].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--") or stripped.startswith("# "):
            continue
        errors.append(f"{markdown_name} schema: unsupported preamble line '{stripped}'")

    for section in sections:
        heading = str(section["heading"])
        section_id = section_ids.get(int(section["offset"]))
        if section_id is None:
            errors.append(f"{markdown_name} schema: unknown section '{heading}'")
            continue
        for line in str(section["body"]).splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if section_id == "forbidden" and stripped.startswith("- "):
                continue
            if _MARKDOWN_DATA_LINE_RE.fullmatch(line) is not None:
                continue
            errors.append(
                f"{markdown_name} schema: section '{section_id}' has unsupported "
                f"line '{stripped}'"
            )
    return errors


def _validate_spec_lock_relations(
    markdown_path: Path,
    matched: Mapping[str, dict[str, object] | None],
) -> list[str]:
    """Validate cross-section references that JSON field rules cannot express."""
    markdown_name = markdown_path.name
    errors: list[str] = []

    def fields(section_id: str) -> dict[str, str]:
        section = matched.get(section_id)
        if section is None:
            return {}
        raw_fields = section["fields"]
        assert isinstance(raw_fields, dict)
        return {str(key): str(value) for key, value in raw_fields.items()}

    for section_id, selector_field, references_field, catalog_dir in (
        _CUSTOM_REFERENCE_CATALOGS
    ):
        section_fields = fields(section_id)
        is_custom = (
            _normalize_schema_value(section_fields.get(selector_field, "")) == "custom"
        )
        raw_references = _normalize_schema_value(
            section_fields.get(references_field, "")
        )
        if not is_custom:
            if raw_references:
                errors.append(
                    f"{markdown_name} schema: field '{references_field}' is valid "
                    f"only when '{selector_field}' is custom"
                )
            continue
        if not raw_references:
            continue
        references = [item.strip() for item in raw_references.split(",")]
        duplicates = sorted(
            reference
            for reference in set(references)
            if references.count(reference) > 1
        )
        if duplicates:
            errors.append(
                f"{markdown_name} schema: field '{references_field}' repeats "
                f"catalog id(s) {', '.join(duplicates)}"
            )
        for reference in references:
            catalog_file = catalog_dir / f"{reference}.md"
            if reference == "custom" or not catalog_file.is_file():
                errors.append(
                    f"{markdown_name} schema: field '{references_field}' references "
                    f"unknown catalog id '{reference}'"
                )

    rhythm = fields("page_rhythm")
    layouts = fields("pptx_layouts")
    page_pptx_layouts = fields("page_pptx_layouts")
    page_layouts = fields("page_layouts")
    structure = fields("pptx_structure")

    for layout_key, raw_value in layouts.items():
        parts = [part.strip() for part in raw_value.split("|")]
        if len(parts) != 3:
            continue
        _, _, source = parts
        if source.startswith("template:"):
            basename = source.removeprefix("template:").strip()
            if basename.casefold().endswith(".svg"):
                basename = basename[:-4]
            template_path = markdown_path.parent / "templates" / f"{basename}.svg"
            if not template_path.is_file():
                errors.append(
                    f"{markdown_name} schema: layout '{layout_key}' references "
                    f"missing template SVG '{basename}.svg'"
                )
        elif source not in rhythm:
            errors.append(
                f"{markdown_name} schema: layout '{layout_key}' has unknown "
                f"prototype source '{source}'"
            )

    if structure.get("mode") == "structured":
        expected_pages = set(rhythm)
        for section_id, mapping in (
            ("page_pptx_layouts", page_pptx_layouts),
            ("page_layouts", page_layouts),
        ):
            missing = sorted(expected_pages - set(mapping))
            extra = sorted(set(mapping) - expected_pages)
            if missing:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' misses pages "
                    f"{', '.join(missing)}"
                )
            if extra:
                errors.append(
                    f"{markdown_name} schema: section '{section_id}' has unknown "
                    f"pages {', '.join(extra)}"
                )

    chart_pages = set(fields("page_charts"))
    unknown_chart_pages = sorted(chart_pages - set(rhythm))
    if unknown_chart_pages:
        errors.append(
            f"{markdown_name} schema: page_charts has unknown pages "
            f"{', '.join(unknown_chart_pages)}"
        )

    info = get_project_info_common(str(markdown_path.parent))
    format_key = str(info.get("format", "unknown"))
    canvas = CANVAS_FORMATS.get(format_key)
    canvas_fields = fields("canvas")
    if canvas is not None:
        expected_format = str(canvas["name"])
        expected_viewbox = str(canvas["viewbox"])
        if (
            "format" in canvas_fields
            and _normalize_schema_value(canvas_fields["format"]) != expected_format
        ):
            errors.append(
                f"{markdown_name} schema: canvas.format must be '{expected_format}'"
            )
        if (
            "viewBox" in canvas_fields
            and _normalize_schema_value(canvas_fields["viewBox"]) != expected_viewbox
        ):
            errors.append(
                f"{markdown_name} schema: canvas.viewBox must be '{expected_viewbox}'"
            )
    return errors


def validate_markdown_schema(markdown_path: Path, schema_path: Path) -> list[str]:
    """Validate one existing Markdown artifact against a versioned schema."""
    try:
        text = markdown_path.read_text(encoding="utf-8-sig")
        schema = _load_markdown_schema(schema_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return [f"Schema validation could not read {markdown_path.name}: {exc}"]

    contract = schema["x-markdown"]
    assert isinstance(contract, dict)
    marker, marker_error = _extract_schema_marker(text)
    if marker_error is not None:
        return [f"{markdown_path.name} schema: {marker_error}"]
    expected_marker = contract.get("marker")
    if isinstance(expected_marker, str):
        if marker is None:
            return [
                f"{markdown_path.name} schema: missing ppt-master-schema marker "
                f"'{expected_marker}'"
            ]
        if marker != expected_marker.casefold():
            return [
                f"{markdown_path.name} schema: marker '{marker}' does not match "
                f"'{expected_marker}'"
            ]
    sections, parse_errors = _parse_markdown_sections(
        text,
        report_duplicate_fields=contract.get("parser") == "heading-data-lines-v1",
    )
    definitions = contract.get("sections", [])
    if not isinstance(definitions, list):
        return [f"Schema validation could not read {schema_path.name}: sections must be a list"]

    markdown_name = markdown_path.name
    errors = [f"{markdown_name} schema: {message}" for message in parse_errors]
    unresolved_patterns = contract.get("unresolved_patterns", [])
    if isinstance(unresolved_patterns, list):
        for pattern in unresolved_patterns:
            if not isinstance(pattern, str):
                continue
            matches = list(re.finditer(pattern, text))
            if matches:
                errors.append(
                    f"{markdown_name} schema: contains {len(matches)} unresolved "
                    f"placeholder(s) matching '{pattern}'"
                )

    matched: dict[str, dict[str, object] | None] = {}
    for definition in definitions:
        if not isinstance(definition, dict):
            continue
        section_id = str(definition.get("id", ""))
        pattern = str(definition.get("pattern", ""))
        if not section_id or not pattern:
            continue
        candidates = [
            section
            for section in sections
            if re.fullmatch(pattern, str(section["heading"]))
        ]
        if len(candidates) > 1:
            errors.append(
                f"{markdown_name} schema: section '{section_id}' appears more than once"
            )
        section = candidates[0] if candidates else None
        matched[section_id] = section
        if definition.get("required") is True and section is None:
            errors.append(f"{markdown_name} schema: missing section '{section_id}'")
            continue
        if section is not None:
            errors.extend(
                _validate_section(
                    markdown_name=markdown_name,
                    section_id=section_id,
                    section=section,
                    definition=definition,
                    schema_path=schema_path,
                )
            )

    section_order = contract.get("section_order", [])
    if isinstance(section_order, list):
        ordered_sections = [
            (str(section_id), matched.get(str(section_id)))
            for section_id in section_order
            if matched.get(str(section_id)) is not None
        ]
        offsets = [int(section["offset"]) for _, section in ordered_sections if section]
        if offsets != sorted(offsets):
            expected = " -> ".join(str(section_id) for section_id in section_order)
            errors.append(
                f"{markdown_name} schema: sections are out of order; expected {expected}"
            )

    conditions = contract.get("conditions", [])
    if isinstance(conditions, list):
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            when = condition.get("when", {})
            then = condition.get("then", {})
            if not isinstance(when, dict) or not isinstance(then, dict):
                continue
            if _condition_applies(when, matched):
                errors.extend(
                    _validate_condition(
                        markdown_name=markdown_name,
                        condition_id=str(condition.get("id", "conditional rule")),
                        then=then,
                        matched=matched,
                    )
                )

    errors.extend(
        _validate_references(
            markdown_path=markdown_path,
            markdown_name=markdown_name,
            rules=contract.get("references"),
            matched=matched,
        )
    )

    slide_contract = contract.get("slides")
    if isinstance(slide_contract, dict):
        errors.extend(
            _validate_slides(
                markdown_name=markdown_name,
                slide_contract=slide_contract,
                matched=matched,
            )
        )
    if contract.get("strict_lines") is True:
        errors.extend(
            _validate_strict_data_surface(markdown_name, text, sections, matched)
        )
    if schema.get("$id") == "ppt-master://schemas/spec-lock/v1":
        errors.extend(_validate_spec_lock_relations(markdown_path, matched))
    return errors


def validate_project_artifacts(
    project_path: Path,
    project_info: Mapping[str, object] | None = None,
    *,
    include_design: bool = True,
) -> tuple[list[str], list[str]]:
    """Validate the lock and, when requested, the human-facing design brief."""
    info = project_info or get_project_info_common(str(project_path))
    errors: list[str] = []
    warnings: list[str] = []
    artifacts: list[tuple[Path, Path, str]] = []
    spec_name = info.get("spec_file")
    if include_design and isinstance(spec_name, str):
        artifacts.append(
            (
                project_path / spec_name,
                SCHEMA_DIR / "design_spec.schema.json",
                "design",
            )
        )
    lock_path = project_path / "spec_lock.md"
    if lock_path.is_file():
        artifacts.append((lock_path, SCHEMA_DIR / "spec_lock.schema.json", "lock"))
    elif isinstance(spec_name, str):
        errors.append(
            "Communication trace: missing spec_lock.md with a "
            "## communication section."
        )

    legacy_design = False
    legacy_lock = False
    versioned_lock_valid = False
    for artifact_path, schema_path, artifact_kind in artifacts:
        try:
            text = artifact_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Schema validation could not read {artifact_path.name}: {exc}")
            continue
        marker, marker_error = _extract_schema_marker(text)
        if marker_error is not None:
            errors.append(f"{artifact_path.name} schema: {marker_error}")
            continue
        if marker is None:
            warnings.append(
                f"{artifact_path.name}: legacy artifact has no ppt-master-schema "
                "marker; skipped versioned schema validation"
            )
            legacy_design = legacy_design or artifact_kind == "design"
            legacy_lock = legacy_lock or artifact_kind == "lock"
            continue
        artifact_errors = validate_markdown_schema(artifact_path, schema_path)
        errors.extend(artifact_errors)
        if artifact_kind == "lock" and not artifact_errors:
            versioned_lock_valid = True
    if versioned_lock_valid:
        try:
            from svg_to_pptx.pptx_package.template_structure import (
                TemplateStructureError,
                load_pptx_structure_lock,
                template_prototype_lock_errors,
            )

            structure_lock = load_pptx_structure_lock(project_path)
            if structure_lock is not None:
                errors.extend(template_prototype_lock_errors(structure_lock))
        except (ImportError, TemplateStructureError) as exc:
            errors.append(f"spec_lock.md structure preflight failed: {exc}")
    if legacy_design or legacy_lock:
        errors.extend(
            validate_communication_trace(
                project_path,
                check_lock=legacy_lock,
                check_design=legacy_design,
            )
        )
    return errors, warnings


def scaffold_project_artifact(project_path: Path, artifact: str) -> str:
    """Render one versioned Markdown scaffold without overwriting user work."""
    assets = {
        "design_spec": (SCAFFOLD_DIR / "design_spec.md", "design_spec.md"),
        "spec_lock": (SCAFFOLD_DIR / "spec_lock.md", "spec_lock.md"),
    }
    if artifact not in assets:
        raise ValueError(f"Unsupported scaffold artifact: {artifact}")
    if not project_path.exists() or not project_path.is_dir():
        raise FileNotFoundError(f"Project directory does not exist: {project_path}")

    info = get_project_info_common(str(project_path))
    format_key = str(info.get("format", "unknown"))
    if format_key not in CANVAS_FORMATS:
        raise ValueError(
            "Cannot derive the canvas format from the project directory name. "
            "Use a standard <name>_<format>_<YYYYMMDD> project path."
        )
    canvas = CANVAS_FORMATS[format_key]
    created_date = str(info.get("date_formatted", "Unknown date"))
    if created_date == "Unknown date":
        created_date = "[fill]"
    context = {
        "PROJECT_NAME": str(info.get("name", project_path.name)),
        "CANVAS_NAME": str(canvas["name"]),
        "CANVAS_DIMENSIONS": str(canvas["dimensions"]),
        "VIEWBOX": str(canvas["viewbox"]),
        "CREATED_DATE": created_date,
    }

    scaffold_path, target_name = assets[artifact]
    target_path = project_path / target_name
    existing_spec = info.get("spec_file") if artifact == "design_spec" else None
    if isinstance(existing_spec, str):
        existing_path = project_path / existing_spec
        raise FileExistsError(
            f"Refusing to shadow existing design spec: {existing_path}"
        )
    if target_path.exists() or target_path.is_symlink():
        raise FileExistsError(f"Refusing to overwrite existing artifact: {target_path}")
    rendered = scaffold_path.read_text(encoding="utf-8")
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    unresolved = sorted(set(_SCAFFOLD_TOKEN_RE.findall(rendered)))
    if unresolved:
        raise ValueError(
            f"Unresolved scaffold token(s) in {scaffold_path}: {', '.join(unresolved)}"
        )
    with target_path.open("x", encoding="utf-8") as stream:
        stream.write(rendered)
    return str(target_path)
