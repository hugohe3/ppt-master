#!/usr/bin/env python3
"""
PPT Master - Page Context Projection

Build deterministic per-page execution views and optional token telemetry.

Usage:
    Imported by project_manager.py.

Examples:
    build_page_context(Path("projects/demo"), "P07")

Dependencies:
    None for projection; tiktoken is optional for exact usage counts.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from project_specs import default_spec_lock_forbidden, parse_markdown_artifact
from svg_to_pptx.pptx_package.template_structure import (
    PptxStructureLock,
    TemplateStructureError,
    load_pptx_structure_lock,
)
from template_text_slots import (
    MODEL_TEXT_SLOT_KEYS,
    TemplateTextSlot,
    analyze_template_text_slots,
    text_slot_integrity_sha256,
)


PAGE_CONTEXT_SCHEMA = "ppt-master.page-context.v1"
PAGE_CONTEXT_USAGE_SCHEMA = "ppt-master.page-context-usage.v1"
PAGE_CONTEXT_REPORT_SCHEMA = "ppt-master.page-context-usage-report.v1"
TEXT_SLOTS_V1_SCHEMA = "ppt-master.template-text-slots.v1"
TEXT_SLOTS_MIN_SCHEMA = "ppt-master.template-text-slots.v2-min"
EXECUTION_MANIFEST_SCHEMA = "ppt-master.template-execution-manifest.v1"
TOKEN_ENCODING = "o200k_base"
PAGE_CONTEXT_TOKEN_TARGET = 800
TEXT_SLOTS_TOKEN_TARGET = 1000

_PAGE_RE = re.compile(r"^(?:P)?([0-9]+)$", re.IGNORECASE)
_SLIDE_HEADING_RE = re.compile(
    r"^####[ \t]+Slide[ \t]+0*([0-9]+)(?:[ \t]*(?:[-:–—]).*)?$",
    re.IGNORECASE | re.MULTILINE,
)
_BLOCK_BOUNDARY_RE = re.compile(r"^#{2,4}[ \t]+", re.MULTILINE)
_PART_HEADING_RE = re.compile(r"^###[ \t]+(?!#)(.+?)[ \t]*$", re.MULTILINE)
_PAGE_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])P0*([1-9][0-9]*)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
class PageContextError(RuntimeError):
    """Reject an incomplete or ambiguous page-context request."""


@dataclass(frozen=True)
class PageRead:
    """One exact model-visible page payload."""

    kind: str
    path: str
    payload: str
    source_path: Path | None = None
    source_schema: str | None = None


@dataclass(frozen=True)
class PageContextResult:
    """One projected page view plus its conditional document payloads."""

    project_path: Path
    page: str
    context: dict[str, object]
    reads: tuple[PageRead, ...]
    inputs: tuple[Path, ...]
    absent_inputs: tuple[Path, ...]


def normalize_page_key(raw_page: str) -> tuple[str, int]:
    """Normalize a positive page identifier to the schema's P<NN> form."""
    match = _PAGE_RE.fullmatch(raw_page.strip())
    if match is None or int(match.group(1)) <= 0:
        raise PageContextError("page must be a positive P<NN> identifier")
    number = int(match.group(1))
    return f"P{number:02d}", number


def _section_index(
    sections: Iterable[dict[str, object]],
) -> dict[str, dict[str, object]]:
    return {
        str(section["heading"]).strip().casefold(): section
        for section in sections
    }


def _section_fields(
    sections: dict[str, dict[str, object]],
    heading: str,
) -> dict[str, str]:
    section = sections.get(heading.casefold())
    if section is None:
        return {}
    fields = section.get("fields", {})
    if not isinstance(fields, dict):
        return {}
    return {str(key): str(value) for key, value in fields.items()}


def _forbidden_items(
    sections: dict[str, dict[str, object]],
) -> list[str]:
    section = sections.get("forbidden")
    if section is None:
        return []
    items: list[str] = []
    default_items = default_spec_lock_forbidden()
    for raw_line in str(section.get("body", "")).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        item = re.sub(r"^-[ \t]+", "", line)
        if item not in default_items:
            items.append(item)
    return items


def _outline_section(
    sections: Iterable[dict[str, object]],
) -> dict[str, object] | None:
    for section in sections:
        heading = str(section.get("heading", "")).strip().casefold()
        if heading == "content outline" or heading.endswith(". content outline"):
            return section
    return None


def _page_image_filenames(
    design_sections: Iterable[dict[str, object]],
    page_number: int,
) -> tuple[set[str], set[str]]:
    """Read explicit P<NN> usage from the canonical image-resource table."""
    section = next(
        (
            item
            for item in design_sections
            if (
                (heading := str(item.get("heading", "")).strip().casefold())
                == "image resource list"
                or heading.startswith("viii. image resource list")
            )
        ),
        None,
    )
    if section is None:
        return set(), set()
    table_rows = [
        [
            cell.strip().replace(r"\|", "|")
            for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))
        ]
        for line in str(section.get("body", "")).splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if not table_rows:
        return set(), set()
    header = {
        name.casefold(): index
        for index, name in enumerate(table_rows[0])
    }
    filename_index = header.get("filename")
    purpose_index = header.get("purpose")
    if filename_index is None or purpose_index is None:
        return set(), set()
    assigned: set[str] = set()
    selected: set[str] = set()
    for row in table_rows[1:]:
        if len(row) <= max(filename_index, purpose_index):
            continue
        purpose = row[purpose_index]
        pages = {int(match.group(1)) for match in _PAGE_TOKEN_RE.finditer(purpose)}
        if not pages:
            continue
        filename = row[filename_index].strip().strip("`")
        if not filename:
            continue
        basename = Path(filename).name
        assigned.add(basename)
        if page_number in pages:
            selected.add(basename)
    return assigned, selected


def _locked_image_basename(value: str) -> str:
    return Path(value.split("|", 1)[0].strip()).name


def _outline_image_assignments(
    design_sections: Iterable[dict[str, object]],
    locked_images: dict[str, str],
) -> set[str]:
    outline = _outline_section(design_sections)
    if outline is None:
        return set()
    body = str(outline.get("body", ""))
    return {
        _locked_image_basename(value)
        for key, value in locked_images.items()
        if any(
            _contains_token(body, token)
            for token in (
                key,
                value.split("|", 1)[0].strip(),
                _locked_image_basename(value),
            )
        )
    }


def _slide_block(
    design_sections: Iterable[dict[str, object]],
    page_number: int,
) -> tuple[str | None, str]:
    outline = _outline_section(design_sections)
    if outline is None:
        raise PageContextError("design_spec.md has no Content Outline section")
    body = str(outline.get("body", ""))
    matches = [
        match
        for match in _SLIDE_HEADING_RE.finditer(body)
        if int(match.group(1)) == page_number
    ]
    if not matches:
        raise PageContextError(
            f"design_spec.md Content Outline has no Slide {page_number:02d} block"
        )
    if len(matches) > 1:
        raise PageContextError(
            f"design_spec.md Content Outline repeats Slide {page_number:02d}"
        )
    match = matches[0]
    next_boundary = _BLOCK_BOUNDARY_RE.search(body, match.end())
    block_end = next_boundary.start() if next_boundary else len(body)
    block = body[match.start():block_end].strip()
    part_matches = list(_PART_HEADING_RE.finditer(body, 0, match.start()))
    part = part_matches[-1].group(1).strip() if part_matches else None
    return part, block


def _relative_project_path(project_path: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_path).as_posix()
    except ValueError as exc:
        raise PageContextError(f"path escapes project: {path}") from exc


def _prototype_image_refs(svg_path: Path) -> list[str]:
    try:
        root = ET.parse(svg_path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise PageContextError(f"cannot read prototype SVG {svg_path}: {exc}") from exc
    refs: set[str] = set()
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "image":
            continue
        for name, value in element.attrib.items():
            if name.rsplit("}", 1)[-1] != "href":
                continue
            normalized = value.strip()
            if normalized and not normalized.startswith(("data:", "#")):
                refs.add(normalized)
    return sorted(refs)


def _contains_token(text: str, token: str) -> bool:
    if not token:
        return False
    if re.fullmatch(r"[A-Za-z0-9_]+", token):
        return re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])",
            text,
        ) is not None
    return token in text


def _page_images(
    locked_images: dict[str, str],
    brief: str,
    prototype_refs: list[str],
    assigned_filenames: set[str],
    resolved_filenames: set[str],
) -> tuple[str, dict[str, str]]:
    if not locked_images:
        return "none", {}
    ref_basenames = {Path(ref).name for ref in prototype_refs}
    selected: dict[str, str] = {}
    unresolved: dict[str, str] = {}
    for key, value in locked_images.items():
        basename = _locked_image_basename(value)
        if (
            _contains_token(brief, key)
            or _contains_token(brief, value)
            or _contains_token(brief, basename)
            or basename in ref_basenames
            or basename in assigned_filenames
        ):
            selected[key] = value
        elif basename not in resolved_filenames:
            unresolved[key] = value
    if selected and unresolved:
        return "explicit+unassigned", {**selected, **unresolved}
    if selected:
        return "explicit", selected
    if unresolved:
        return "unassigned", unresolved
    return "confirmed-none", {}


def _page_template(
    project_path: Path,
    structure_lock: PptxStructureLock | None,
    page_number: int,
) -> tuple[dict[str, object] | None, Path | None]:
    if structure_lock is None or structure_lock.mode != "structured":
        return None, None
    prototype = next(
        (item for item in structure_lock.prototypes if item.slide_num == page_number),
        None,
    )
    assignment = next(
        (item for item in structure_lock.layouts if item.slide_num == page_number),
        None,
    )
    if prototype is None or assignment is None:
        raise PageContextError(
            f"structured lock has no complete mapping for P{page_number:02d}"
        )
    definition = next(
        (
            item
            for item in structure_lock.layout_definitions
            if item.layout_key == assignment.layout_key
        ),
        None,
    )
    if definition is None:
        raise PageContextError(
            f"structured lock has no definition for Layout {assignment.layout_key!r}"
        )
    master = next(
        (
            item
            for item in structure_lock.masters
            if item.master_key == definition.master_key
        ),
        None,
    )
    if master is None:
        raise PageContextError(
            f"structured lock has no definition for Master {definition.master_key!r}"
        )
    template = {
        "reuse_scope": structure_lock.template_reuse_scope,
        "adherence": structure_lock.template_adherence,
        "prototype": prototype.template_basename,
        "prototype_path": _relative_project_path(project_path, prototype.svg_path),
        "layout": {
            "key": definition.layout_key,
            "name": definition.layout_name,
            "source": (
                f"P{definition.prototype_slide_num:02d}"
                if definition.prototype_slide_num is not None
                else _relative_project_path(
                    project_path,
                    definition.prototype_svg_path,
                )
            ),
        },
        "master": {
            "key": master.master_key,
            "name": master.master_name,
        },
    }
    return template, prototype.svg_path


def _project_text_slots(
    payload: object,
    expected_prototype: str,
    prototype_slots: tuple[TemplateTextSlot, ...],
) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise PageContextError("text-slot sidecar root must be an object")
    source_schema = payload.get("schema")
    if source_schema not in {TEXT_SLOTS_V1_SCHEMA, TEXT_SLOTS_MIN_SCHEMA}:
        raise PageContextError(f"unsupported text-slot schema: {source_schema!r}")
    prototype = payload.get("prototype")
    if prototype != expected_prototype:
        raise PageContextError(
            f"text-slot sidecar prototype {prototype!r} does not match "
            f"{expected_prototype!r}"
        )
    raw_slots = payload.get("text_slots")
    if not isinstance(raw_slots, list):
        raise PageContextError("text-slot sidecar requires a text_slots array")
    slots: list[dict[str, object]] = []
    for index, raw_slot in enumerate(raw_slots, start=1):
        if not isinstance(raw_slot, dict):
            raise PageContextError(f"text slot {index} must be an object")
        missing = [key for key in MODEL_TEXT_SLOT_KEYS if key not in raw_slot]
        if missing:
            raise PageContextError(
                f"text slot {index} is missing: {', '.join(missing)}"
            )
        segments = raw_slot["text_segments"]
        if not isinstance(segments, list) or not all(
            isinstance(segment, str) for segment in segments
        ):
            raise PageContextError(
                f"text slot {index} text_segments must be an array of strings"
            )
        if type(raw_slot["tspan_count"]) is not int or raw_slot["tspan_count"] < 0:
            raise PageContextError(
                f"text slot {index} tspan_count must be a non-negative integer"
            )
        if not all(
            isinstance(raw_slot[key], str)
            for key in ("selector", "role", "current_text")
        ):
            raise PageContextError(
                f"text slot {index} selector/role/current_text must be strings"
            )
        slots.append({key: raw_slot[key] for key in MODEL_TEXT_SLOT_KEYS})
    declared_count = payload.get("text_slot_count")
    if type(declared_count) is not int or declared_count != len(slots):
        raise PageContextError(
            "text-slot sidecar text_slot_count does not match text_slots"
        )
    if len(prototype_slots) != len(slots):
        raise PageContextError(
            "text-slot sidecar does not match the prototype text-slot count"
        )
    expected_slots = [slot.model_payload() for slot in prototype_slots]
    if source_schema == TEXT_SLOTS_MIN_SCHEMA:
        integrity = payload.get("tool_integrity_sha256")
        expected_integrity = text_slot_integrity_sha256(prototype_slots)
        if integrity != expected_integrity:
            raise PageContextError(
                "text-slot sidecar integrity hash does not match the prototype"
            )
        if slots != expected_slots:
            raise PageContextError(
                "text-slot sidecar values do not match the prototype"
            )
    else:
        for index, (raw_slot, actual_slot, expected_slot) in enumerate(
            zip(raw_slots, prototype_slots, expected_slots),
            start=1,
        ):
            if raw_slot["selector"] not in {
                actual_slot.selector,
                actual_slot.legacy_selector,
            }:
                raise PageContextError(
                    f"legacy text slot {index} selector does not match the prototype"
                )
            if any(
                raw_slot[key] != expected_slot[key]
                for key in MODEL_TEXT_SLOT_KEYS
                if key != "selector"
            ):
                raise PageContextError(
                    f"legacy text slot {index} values do not match the prototype"
                )
            if raw_slot.get("topology_sha256") != actual_slot.topology_sha256:
                raise PageContextError(
                    f"legacy text slot {index} topology hash does not match the prototype"
                )
    return {
        "schema": TEXT_SLOTS_MIN_SCHEMA,
        "prototype": expected_prototype,
        "text_slot_count": len(expected_slots),
        "text_slots": expected_slots,
    }


def _text_slots_read(
    project_path: Path,
    prototype_path: Path,
    inputs: list[Path],
    absent_inputs: list[Path],
    warnings: list[str],
) -> PageRead | None:
    templates_dir = project_path / "templates"
    manifest_path = templates_dir / "template_execution_manifest.json"
    candidate: Path | None = None
    if manifest_path.is_file():
        inputs.append(manifest_path)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema") != EXECUTION_MANIFEST_SCHEMA:
                raise PageContextError("unsupported template execution manifest schema")
            entries = manifest.get("templates")
            if not isinstance(entries, list):
                raise PageContextError("template execution manifest has no templates list")
            entry = next(
                (
                    item
                    for item in entries
                    if isinstance(item, dict)
                    and item.get("prototype") == prototype_path.name
                ),
                None,
            )
            if entry is not None and isinstance(entry.get("text_slots_path"), str):
                resolved = (templates_dir / str(entry["text_slots_path"])).resolve()
                if resolved.is_relative_to(templates_dir.resolve()):
                    candidate = resolved
        except (OSError, json.JSONDecodeError, PageContextError) as exc:
            warnings.append(
                f"template execution manifest unavailable; using prototype only ({exc})"
            )
    else:
        absent_inputs.append(manifest_path)
    conventional = (
        templates_dir
        / "template_execution"
        / f"{prototype_path.stem}.text-slots.json"
    )
    if candidate is None:
        candidate = conventional
    if not candidate.is_file():
        absent_inputs.append(candidate)
        warnings.append(
            f"{prototype_path.name} has no usable text-slot sidecar; "
            "use the complete prototype SVG"
        )
        return None
    inputs.append(candidate)
    try:
        prototype_root = ET.parse(prototype_path).getroot()
        prototype_slots = analyze_template_text_slots(prototype_root)
        source_payload = json.loads(candidate.read_text(encoding="utf-8"))
        projected = _project_text_slots(
            source_payload,
            prototype_path.name,
            prototype_slots,
        )
    except (OSError, ET.ParseError, ValueError, json.JSONDecodeError, PageContextError) as exc:
        warnings.append(
            f"{candidate.name} is unusable; use the complete prototype SVG ({exc})"
        )
        return None
    return PageRead(
        kind="mirror-text-slots-min",
        path=_relative_project_path(project_path, candidate),
        payload=_compact_json(projected),
        source_path=candidate,
        source_schema=str(source_payload.get("schema")),
    )


def build_page_context(project: str | Path, raw_page: str) -> PageContextResult:
    """Build one current per-page projection without writing the project."""
    project_path = Path(project).resolve()
    if not project_path.is_dir():
        raise PageContextError(f"project directory not found: {project_path}")
    page, page_number = normalize_page_key(raw_page)
    lock_path = project_path / "spec_lock.md"
    design_path = project_path / "design_spec.md"
    for required in (lock_path, design_path):
        if not required.is_file():
            raise PageContextError(f"required artifact not found: {required.name}")
    try:
        lock_sections_raw = parse_markdown_artifact(
            lock_path,
            report_duplicate_fields=True,
        )
        design_sections = parse_markdown_artifact(design_path)
    except (OSError, ValueError) as exc:
        raise PageContextError(str(exc)) from exc
    lock_sections = _section_index(lock_sections_raw)
    part, brief = _slide_block(design_sections, page_number)
    warnings: list[str] = []
    rhythm_fields = _section_fields(lock_sections, "page_rhythm")
    rhythm = rhythm_fields.get(page)
    if rhythm is None:
        rhythm = "dense"
        warnings.append(f"page_rhythm has no {page}; using compatibility default dense")
    chart = _section_fields(lock_sections, "page_charts").get(page)
    try:
        structure_lock = load_pptx_structure_lock(project_path)
    except TemplateStructureError as exc:
        raise PageContextError(str(exc)) from exc
    template, prototype_path = _page_template(
        project_path,
        structure_lock,
        page_number,
    )
    prototype_refs = (
        _prototype_image_refs(prototype_path)
        if prototype_path is not None
        else []
    )
    table_assigned_filenames, assigned_filenames = _page_image_filenames(
        design_sections,
        page_number,
    )
    locked_images = _section_fields(lock_sections, "images")
    resolved_filenames = (
        {_locked_image_basename(value) for value in locked_images.values()}
        if structure_lock is not None
        and structure_lock.template_reuse_scope == "mirror"
        else table_assigned_filenames
        | _outline_image_assignments(design_sections, locked_images)
    )
    image_selection, selected_images = _page_images(
        locked_images,
        brief,
        (
            prototype_refs
            if structure_lock is not None
            and structure_lock.template_reuse_scope == "mirror"
            else []
        ),
        assigned_filenames,
        resolved_filenames,
    )
    inputs = [lock_path, design_path]
    absent_inputs: list[Path] = []
    reads: list[PageRead] = []
    if prototype_path is not None:
        inputs.append(prototype_path)
        if (
            structure_lock is not None
            and structure_lock.template_reuse_scope == "mirror"
        ):
            text_slots = _text_slots_read(
                project_path,
                prototype_path,
                inputs,
                absent_inputs,
                warnings,
            )
            if text_slots is not None:
                reads.append(text_slots)
        reads.append(PageRead(
            kind="prototype-svg",
            path=_relative_project_path(project_path, prototype_path),
            payload=prototype_path.read_text(encoding="utf-8"),
            source_path=prototype_path,
        ))
    global_context = {
        "communication": _section_fields(lock_sections, "communication"),
        "canvas": _section_fields(lock_sections, "canvas"),
        "mode": _section_fields(lock_sections, "mode").get("mode"),
        "visual_style": _section_fields(
            lock_sections,
            "visual_style",
        ).get("visual_style"),
        "colors": _section_fields(lock_sections, "colors"),
        "typography": _section_fields(lock_sections, "typography"),
        "icons": _section_fields(lock_sections, "icons"),
        "pptx_structure": _section_fields(lock_sections, "pptx_structure"),
        "forbidden": _forbidden_items(lock_sections),
    }
    global_context = {
        key: value
        for key, value in global_context.items()
        if value not in ({}, [], None, "")
    }
    read_set = [
        {
            "kind": read.kind,
            "path": read.path,
            **(
                {"schema": TEXT_SLOTS_MIN_SCHEMA}
                if read.kind == "mirror-text-slots-min"
                else {}
            ),
        }
        for read in reads
    ]
    current_page: dict[str, object] = {
        "part": part,
        "brief_markdown": brief,
        "rhythm": rhythm,
        "image_selection": image_selection,
    }
    if chart is not None:
        current_page["chart"] = chart
    if selected_images:
        current_page["images"] = selected_images
    if template is not None:
        current_page["template"] = template
    context: dict[str, object] = {
        "schema": PAGE_CONTEXT_SCHEMA,
        "page": page,
        "global": global_context,
        "page_context": current_page,
    }
    if read_set:
        context["read_set"] = read_set
    if warnings:
        context["warnings"] = warnings
    unique_inputs = tuple(dict.fromkeys(path.resolve() for path in inputs))
    unique_absent_inputs = tuple(
        path
        for path in dict.fromkeys(path.resolve() for path in absent_inputs)
        if not path.exists()
    )
    return PageContextResult(
        project_path=project_path,
        page=page,
        context=context,
        reads=tuple(reads),
        inputs=unique_inputs,
        absent_inputs=unique_absent_inputs,
    )


def _compact_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def _pretty_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_page_context(
    result: PageContextResult,
    *,
    bundle: bool = False,
    pretty: bool = False,
) -> tuple[str, tuple[PageRead, ...]]:
    """Render the exact stdout payload and return its measured components."""
    context_payload = (
        _pretty_json(result.context) if pretty else _compact_json(result.context)
    )
    context_read = PageRead(
        kind="page-context",
        path="stdout:page-context",
        payload=context_payload,
    )
    if not bundle:
        return context_payload, (context_read,)
    reads = (context_read, *result.reads)
    parts: list[str] = []
    for read in reads:
        parts.append(f"<<<{read.kind}:{read.path}>>>\n")
        parts.append(read.payload.rstrip("\n"))
        parts.append(f"\n<<<end:{read.kind}>>>\n")
    return "".join(parts), reads


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token_counter() -> tuple[Callable[[str], int] | None, str]:
    try:
        import tiktoken
    except ImportError:
        return None, "unavailable"
    try:
        encoder = tiktoken.get_encoding(TOKEN_ENCODING)
    except Exception:
        return None, "unavailable"
    return (
        lambda text: len(encoder.encode(text, disallowed_special=())),
        "exact",
    )


def _payload_measurement(
    read: PageRead,
    count_tokens: Callable[[str], int] | None,
) -> dict[str, object]:
    payload = read.payload.encode("utf-8")
    measurement: dict[str, object] = {
        "kind": read.kind,
        "scope": "page",
        "path": read.path,
        "sha256": _sha256_bytes(payload),
        "utf8_bytes": len(payload),
        "characters": len(read.payload),
        "tokens": count_tokens(read.payload) if count_tokens else None,
    }
    if read.source_path is not None:
        measurement["source_sha256"] = _file_sha256(read.source_path)
    if read.source_schema is not None:
        measurement["source_schema"] = read.source_schema
    return measurement


def record_page_context_usage(
    result: PageContextResult,
    output: str,
    measured_reads: tuple[PageRead, ...],
) -> tuple[Path, str]:
    """Write one deterministic, derived token snapshot for the current page."""
    count_tokens, token_status = _token_counter()
    documents = [
        _payload_measurement(read, count_tokens)
        for read in measured_reads
    ]
    output_bytes = output.encode("utf-8")
    input_records = [
        {
            "path": _relative_project_path(result.project_path, path),
            "exists": True,
            "sha256": _file_sha256(path),
        }
        for path in result.inputs
    ]
    input_records.extend(
        {
            "path": _relative_project_path(result.project_path, path),
            "exists": False,
        }
        for path in result.absent_inputs
    )
    by_kind = {
        str(item["kind"]): item.get("tokens")
        for item in documents
    }
    route = dict(result.context["global"].get("pptx_structure", {}))
    template = result.context["page_context"].get("template")
    if isinstance(template, dict) and isinstance(template.get("reuse_scope"), str):
        route["template_reuse_scope"] = template["reuse_scope"]
    usage = {
        "schema": PAGE_CONTEXT_USAGE_SCHEMA,
        "page": result.page,
        "output_mode": "bundle",
        "route": route,
        "encoding": TOKEN_ENCODING,
        "token_status": token_status,
        "image_selection": result.context["page_context"]["image_selection"],
        "inputs": input_records,
        "documents": documents,
        "controlled_output": {
            "sha256": _sha256_bytes(output_bytes),
            "utf8_bytes": len(output_bytes),
            "characters": len(output),
            "tokens": count_tokens(output) if count_tokens else None,
        },
        "totals": {
            "page_context": by_kind.get("page-context"),
            "text_slots_min": by_kind.get("mirror-text-slots-min"),
            "prototype_svg": by_kind.get("prototype-svg"),
        },
        "targets": {
            "page_context_max_tokens": PAGE_CONTEXT_TOKEN_TARGET,
            "mirror_text_slots_max_tokens": TEXT_SLOTS_TOKEN_TARGET,
        },
        "untracked": ["source-material reads", "session-level prompt references"],
    }
    usage_dir = result.project_path / "analysis" / "page-context"
    usage_dir.mkdir(parents=True, exist_ok=True)
    usage_path = usage_dir / f"{result.page}.usage.json"
    temporary_path = usage_path.with_suffix(".usage.json.tmp")
    temporary_path.write_text(_pretty_json(usage), encoding="utf-8")
    temporary_path.replace(usage_path)
    return usage_path, token_status


def _nearest_rank(values: list[int], percentile: float) -> int:
    rank = max(1, math.ceil(percentile * len(values)))
    return sorted(values)[rank - 1]


def _metric(values: list[int], *, target: int | None = None) -> dict[str, object]:
    if not values:
        return {
            "count": 0,
            "sum": 0,
            "min": None,
            "p50": None,
            "p95": None,
            "max": None,
            **({"over_target_count": 0, "target": target} if target else {}),
        }
    metric: dict[str, object] = {
        "count": len(values),
        "sum": sum(values),
        "min": min(values),
        "p50": round(statistics.median(values)),
        "p95": _nearest_rank(values, 0.95),
        "max": max(values),
    }
    if target is not None:
        metric.update({
            "target": target,
            "over_target_count": sum(value > target for value in values),
        })
    return metric


def page_context_usage_report(project: str | Path) -> dict[str, object]:
    """Summarize fresh per-page telemetry without changing recorded history."""
    project_path = Path(project).resolve()
    usage_dir = project_path / "analysis" / "page-context"
    records: list[dict[str, object]] = []
    stale_pages: list[str] = []
    unavailable_pages: list[str] = []
    if usage_dir.is_dir():
        for usage_path in sorted(usage_dir.glob("P*.usage.json")):
            try:
                record = json.loads(usage_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                stale_pages.append(usage_path.stem.split(".", 1)[0])
                continue
            page = str(record.get("page", usage_path.stem.split(".", 1)[0]))
            if record.get("schema") != PAGE_CONTEXT_USAGE_SCHEMA:
                stale_pages.append(page)
                continue
            if record.get("output_mode") != "bundle":
                stale_pages.append(page)
                continue
            stale = False
            for item in record.get("inputs", []):
                if not isinstance(item, dict):
                    stale = True
                    break
                source_path = (project_path / str(item.get("path", ""))).resolve()
                try:
                    source_path.relative_to(project_path)
                except ValueError:
                    stale = True
                    break
                expected_exists = item.get("exists", True)
                if expected_exists is False:
                    if source_path.exists():
                        stale = True
                        break
                elif (
                    not source_path.is_file()
                    or _file_sha256(source_path) != item.get("sha256")
                ):
                    stale = True
                    break
            if stale:
                stale_pages.append(page)
                continue
            if record.get("token_status") != "exact":
                unavailable_pages.append(page)
            records.append(record)

    def tokens_for(kind: str) -> list[int]:
        values: list[int] = []
        for record in records:
            for document in record.get("documents", []):
                if not isinstance(document, dict) or document.get("kind") != kind:
                    continue
                value = document.get("tokens")
                if isinstance(value, int):
                    values.append(value)
        return values

    controlled = [
        value
        for record in records
        if isinstance(
            value := record.get("controlled_output", {}).get("tokens"),
            int,
        )
    ]
    prototype_values = tokens_for("prototype-svg")
    mirror_records = [
        record
        for record in records
        if isinstance(record.get("route"), dict)
        and record["route"].get("template_reuse_scope") == "mirror"
    ]
    mirror_controlled = [
        value
        for record in mirror_records
        if isinstance(
            value := record.get("controlled_output", {}).get("tokens"),
            int,
        )
    ]
    mirror_prototype_values = [
        int(document["tokens"])
        for record in mirror_records
        for document in record.get("documents", [])
        if isinstance(document, dict)
        and document.get("kind") == "prototype-svg"
        and isinstance(document.get("tokens"), int)
    ]
    prototype_share = (
        round(sum(mirror_prototype_values) / sum(mirror_controlled), 4)
        if mirror_prototype_values and sum(mirror_controlled)
        else None
    )
    return {
        "schema": PAGE_CONTEXT_REPORT_SCHEMA,
        "project": project_path.name,
        "record_count": len(records),
        "mirror_record_count": len(mirror_records),
        "pages": sorted(str(record["page"]) for record in records),
        "stale_pages": sorted(set(stale_pages)),
        "token_unavailable_pages": sorted(set(unavailable_pages)),
        "metrics": {
            "page_context": _metric(
                tokens_for("page-context"),
                target=PAGE_CONTEXT_TOKEN_TARGET,
            ),
            "mirror_text_slots_min": _metric(
                tokens_for("mirror-text-slots-min"),
                target=TEXT_SLOTS_TOKEN_TARGET,
            ),
            "prototype_svg": _metric(prototype_values),
            "controlled_output": _metric(controlled),
        },
        "mirror_prototype_share_of_controlled_output": prototype_share,
    }
