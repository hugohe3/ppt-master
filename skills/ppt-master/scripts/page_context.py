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

from project_specs import (
    default_spec_lock_forbidden,
    parse_markdown_artifact,
    validate_project_artifacts,
)
from svg_to_pptx.pptx_package.template_structure import (
    PptxStructureLock,
    TemplateStructureError,
    load_pptx_structure_lock,
)


PAGE_CONTEXT_SCHEMA = "ppt-master.page-context.v2"
PAGE_CONTEXT_USAGE_SCHEMA = "ppt-master.page-context-usage.v2"
PAGE_CONTEXT_REPORT_SCHEMA = "ppt-master.page-context-usage-report.v2"
TOKEN_ENCODING = "o200k_base"
PAGE_CONTEXT_TOKEN_TARGET = 2000
LOCK_PROJECTION_TOKEN_TARGET = 1000

_SKILL_DIR = Path(__file__).resolve().parent.parent
_CHARTS_DIR = _SKILL_DIR / "templates" / "charts"

_PAGE_RE = re.compile(r"^(?:P)?([0-9]+)$", re.IGNORECASE)
_SLIDE_HEADING_RE = re.compile(
    r"^#{3,6}[ \t]+Slide[ \t]+0*([0-9]+)(?:[ \t]*(?:[-:–—]).*)?$",
    re.IGNORECASE | re.MULTILINE,
)
_BLOCK_BOUNDARY_RE = re.compile(r"^#{2,6}[ \t]+", re.MULTILINE)
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


@dataclass(frozen=True)
class PageContextResult:
    """One projected page view plus the files that make it current."""

    project_path: Path
    page: str
    context: dict[str, object]
    inputs: tuple[Path, ...]


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


def _reference_payload(
    kind: str,
    path: Path,
    *,
    scope: str,
    display_path: str,
    same_context_edit_policy: str | None = None,
) -> dict[str, str]:
    """Describe one large reference without injecting its contents per page."""
    payload = {
        "kind": kind,
        "scope": scope,
        "path": display_path,
        "sha256": _file_sha256(path),
        "load_policy": "once-per-execution-context",
    }
    if same_context_edit_policy is not None:
        payload["same_context_edit_policy"] = same_context_edit_policy
    return payload


def _chart_reference(chart_key: str) -> tuple[dict[str, str], Path]:
    """Resolve one locked chart key to the shared Skill catalog."""
    if Path(chart_key).name != chart_key or not chart_key:
        raise PageContextError(f"invalid page_charts key: {chart_key!r}")
    chart_path = (_CHARTS_DIR / f"{chart_key}.svg").resolve()
    if not chart_path.is_file():
        raise PageContextError(
            f"page_charts key {chart_key!r} has no shared SVG reference"
        )
    return (
        _reference_payload(
            "chart-svg",
            chart_path,
            scope="skill",
            display_path=f"templates/charts/{chart_path.name}",
        ),
        chart_path,
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
    preflight_errors, _preflight_warnings = validate_project_artifacts(
        project_path,
        include_design=False,
    )
    if preflight_errors:
        preview = "; ".join(preflight_errors[:8])
        suffix = (
            ""
            if len(preflight_errors) <= 8
            else f"; +{len(preflight_errors) - 8} more"
        )
        raise PageContextError(
            "spec_lock/template preflight failed before page generation: "
            f"{preview}{suffix}"
        )
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
    chart_key = _section_fields(lock_sections, "page_charts").get(page)
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
    reference_set: list[dict[str, str]] = [
        _reference_payload(
            "design-spec",
            design_path,
            scope="project",
            display_path="design_spec.md",
            same_context_edit_policy="targeted-readback-and-rebind",
        ),
    ]
    template_design_path = project_path / "templates" / "design_spec.md"
    if template_design_path.is_file():
        inputs.append(template_design_path)
        reference_set.append(
            _reference_payload(
                "template-design-spec",
                template_design_path,
                scope="project",
                display_path="templates/design_spec.md",
            )
        )
    if prototype_path is not None:
        inputs.append(prototype_path)
        reference_set.append(
            _reference_payload(
                "prototype-svg",
                prototype_path,
                scope="project",
                display_path=_relative_project_path(project_path, prototype_path),
            )
        )
    if chart_key is not None:
        chart_reference, chart_path = _chart_reference(chart_key)
        inputs.append(chart_path)
        reference_set.append(chart_reference)
    mode_fields = _section_fields(lock_sections, "mode")
    visual_style_fields = _section_fields(lock_sections, "visual_style")
    # Repeat this bounded projection per page intentionally: stable lock roles
    # are continuity anchors, while large reference payloads use reference_set.
    global_context = {
        "communication": _section_fields(lock_sections, "communication"),
        "canvas": _section_fields(lock_sections, "canvas"),
        "mode": mode_fields.get("mode"),
        "mode_behavior": mode_fields.get("mode_behavior"),
        "visual_style": visual_style_fields.get("visual_style"),
        "visual_style_behavior": visual_style_fields.get(
            "visual_style_behavior"
        ),
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
    current_page: dict[str, object] = {
        "part": part,
        "brief_markdown": brief,
        "rhythm": rhythm,
        "image_selection": image_selection,
    }
    if chart_key is not None:
        current_page["chart"] = chart_key
    if selected_images:
        current_page["images"] = selected_images
    if template is not None:
        current_page["template"] = template
    context: dict[str, object] = {
        "schema": PAGE_CONTEXT_SCHEMA,
        "page": page,
        "lock_source": {
            "path": "spec_lock.md",
            "sha256": _file_sha256(lock_path),
            "load_policy": "per-page-context-anchors",
        },
        "global": global_context,
        "page_context": current_page,
        "reference_set": reference_set,
    }
    if warnings:
        context["warnings"] = warnings
    unique_inputs = tuple(dict.fromkeys(path.resolve() for path in inputs))
    return PageContextResult(
        project_path=project_path,
        page=page,
        context=context,
        inputs=unique_inputs,
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
    """Render compact stdout; ``bundle`` remains a compatibility no-op."""
    context_payload = (
        _pretty_json(result.context) if pretty else _compact_json(result.context)
    )
    context_read = PageRead(
        kind="page-context",
        path="stdout:page-context",
        payload=context_payload,
    )
    return context_payload, (context_read,)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _input_location(project_path: Path, path: Path) -> tuple[str, str]:
    """Return a stable project- or Skill-relative locator for telemetry."""
    resolved = path.resolve()
    for scope, root in (("project", project_path), ("skill", _SKILL_DIR)):
        try:
            return scope, resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
    raise PageContextError(f"input escapes project and Skill roots: {path}")


def _resolve_input_location(
    project_path: Path,
    scope: str,
    relative_path: str,
) -> Path | None:
    """Resolve one recorded input without accepting arbitrary filesystem roots."""
    roots = {"project": project_path, "skill": _SKILL_DIR}
    root = roots.get(scope)
    if root is None:
        return None
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


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
        "scope": "component" if read.kind == "lock-projection" else "page",
        "path": read.path,
        "sha256": _sha256_bytes(payload),
        "utf8_bytes": len(payload),
        "characters": len(read.payload),
        "tokens": count_tokens(read.payload) if count_tokens else None,
    }
    return measurement


def record_page_context_usage(
    result: PageContextResult,
    output: str,
    measured_reads: tuple[PageRead, ...],
) -> tuple[Path, str]:
    """Write one deterministic, derived token snapshot for the current page."""
    count_tokens, token_status = _token_counter()
    lock_read = PageRead(
        kind="lock-projection",
        path="stdout:global",
        payload=_compact_json(result.context["global"]),
    )
    documents = [
        _payload_measurement(read, count_tokens)
        for read in (*measured_reads, lock_read)
    ]
    output_bytes = output.encode("utf-8")
    input_records: list[dict[str, object]] = []
    for path in result.inputs:
        scope, relative_path = _input_location(result.project_path, path)
        input_records.append(
            {
                "scope": scope,
                "path": relative_path,
                "exists": True,
                "sha256": _file_sha256(path),
            }
        )
    by_kind = {
        str(item["kind"]): item.get("tokens")
        for item in documents
    }
    route = dict(result.context["global"].get("pptx_structure", {}))
    template = result.context["page_context"].get("template")
    if isinstance(template, dict):
        if isinstance(value := template.get("reuse_scope"), str):
            route["template_reuse_scope"] = value
    usage = {
        "schema": PAGE_CONTEXT_USAGE_SCHEMA,
        "page": result.page,
        "output_mode": "compact",
        "route": route,
        "encoding": TOKEN_ENCODING,
        "token_status": token_status,
        "image_selection": result.context["page_context"]["image_selection"],
        "inputs": input_records,
        "references": result.context.get("reference_set", []),
        "documents": documents,
        "controlled_output": {
            "sha256": _sha256_bytes(output_bytes),
            "utf8_bytes": len(output_bytes),
            "characters": len(output),
            "tokens": count_tokens(output) if count_tokens else None,
        },
        "totals": {
            "page_context": by_kind.get("page-context"),
            "lock_projection": by_kind.get("lock-projection"),
        },
        "targets": {
            "page_context_max_tokens": PAGE_CONTEXT_TOKEN_TARGET,
            "lock_projection_max_tokens": LOCK_PROJECTION_TOKEN_TARGET,
        },
        "untracked": [
            "source-material reads",
            "once-per-execution-context reference payloads",
            "other session-level prompt references",
        ],
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
            if record.get("output_mode") != "compact":
                stale_pages.append(page)
                continue
            stale = False
            for item in record.get("inputs", []):
                if not isinstance(item, dict):
                    stale = True
                    break
                source_path = _resolve_input_location(
                    project_path,
                    str(item.get("scope", "project")),
                    str(item.get("path", "")),
                )
                if source_path is None:
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
    unique_references = sorted({
        f"{reference.get('scope', 'project')}:{reference.get('path', '')}"
        for record in records
        for reference in record.get("references", [])
        if isinstance(reference, dict) and reference.get("path")
    })
    return {
        "schema": PAGE_CONTEXT_REPORT_SCHEMA,
        "project": project_path.name,
        "record_count": len(records),
        "pages": sorted(str(record["page"]) for record in records),
        "stale_pages": sorted(set(stale_pages)),
        "token_unavailable_pages": sorted(set(unavailable_pages)),
        "unique_reference_count": len(unique_references),
        "unique_references": unique_references,
        "metrics": {
            "page_context": _metric(
                tokens_for("page-context"),
                target=PAGE_CONTEXT_TOKEN_TARGET,
            ),
            "lock_projection": _metric(
                tokens_for("lock-projection"),
                target=LOCK_PROJECTION_TOKEN_TARGET,
            ),
            "controlled_output": _metric(controlled),
        },
    }
