#!/usr/bin/env python3
"""
PPT Master - PPTX Delivery Check

Inspect a finished PPTX without modifying it and report package integrity,
delivery portability, media footprint, hidden slides, and motion presence.

Usage:
    python3 scripts/pptx_delivery_check.py <presentation.pptx>

Examples:
    python3 scripts/pptx_delivery_check.py projects/demo/exports/demo.pptx

Dependencies:
    Same repository dependencies as beautify_identity.py and svg_to_pptx.py.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import tempfile
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from beautify_identity import extract_identity  # noqa: E402
from pptx_opc_validation import (  # noqa: E402
    canonical_opc_part_path,
    resolve_internal_opc_target,
    verify_internal_relationships,
)
from pptx_animations import (  # noqa: E402
    object_animation_fingerprint,
    read_slide_animation_sequence,
    validate_pptx_animation_package,
)
from pptx_to_svg.ooxml_loader import (  # noqa: E402
    OoxmlPackage,
    parse_ooxml_boolean,
)
from pptx_transitions import (  # noqa: E402
    read_slide_transition_xml,
    validate_slide_transition_xml,
)
from svg_to_pptx.drawingml.utils import PPT_SAFE_FONTS  # noqa: E402


REPORT_SCHEMA = "ppt-master.pptx-delivery-check.v1"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PRESENTATION_NS = (
    "http://schemas.openxmlformats.org/presentationml/2006/main"
)
_SLIDE_PART_RE = re.compile(r"ppt/slides/slide[1-9]\d*\.xml")
_NOTES_PART_RE = re.compile(r"ppt/notesSlides/notesSlide[1-9]\d*\.xml")
_MASTER_PART_RE = re.compile(r"ppt/slideMasters/slideMaster[1-9]\d*\.xml")
_LAYOUT_PART_RE = re.compile(r"ppt/slideLayouts/slideLayout[1-9]\d*\.xml")
_MEDIA_REL_KINDS = frozenset({"audio", "image", "media", "video"})
_PPT_SAFE_FONT_ALIASES = {
    "等线": "DengXian",
    "等线 light": "DengXian Light",
    "宋体": "SimSun",
    "新細明體": "PMingLiU",
    "맑은 고딕": "Malgun Gothic",
    "ms pゴシック": "MS PGothic",
}
_PPT_DELIVERY_SAFE_FONTS = PPT_SAFE_FONTS | frozenset(
    {"dengxian light", "pmingliu"}
)


def _issue(code: str, message: str, **details: object) -> dict[str, object]:
    issue: dict[str, object] = {"code": code, "message": message}
    issue.update(details)
    return issue


def _empty_report(path: Path) -> dict[str, object]:
    return {
        "schema": REPORT_SCHEMA,
        "status": "failed",
        "file": {
            "path": str(path),
            "bytes": path.stat().st_size if path.is_file() else None,
        },
        "package": {
            "zip_integrity": "not-checked",
            "corrupt_member": None,
            "duplicate_parts": [],
            "canonical_part_collisions": [],
            "parts": {},
            "relationships": {"problems": []},
        },
        "slides": {
            "count": 0,
            "hidden_count": 0,
            "hidden": [],
        },
        "fonts": {
            "theme": {},
            "declared": {},
            "embedded_parts": [],
            "portability_advisory_faces": [],
        },
        "media": {
            "embedded_count": 0,
            "external_count": 0,
            "embedded": [],
            "external": [],
            "uncompressed_bytes": 0,
            "archive_compressed_bytes": 0,
            "share_of_archive": 0.0,
            "share_of_uncompressed_parts": 0.0,
            "top_contributors": [],
        },
        "motion": {
            "transitions": {
                "carrier_slide_count": 0,
                "visual_effect_slide_count": 0,
                "timed_advance_slide_count": 0,
                "carrier_slides": [],
                "visual_effect_slides": [],
                "timed_advance_slides": [],
                "effects": {},
            },
            "object_animations": {
                "timing_slide_count": 0,
                "object_animation_slide_count": 0,
                "audio_timing_slide_count": 0,
                "timing_slides": [],
                "object_animation_slides": [],
                "audio_timing_slides": [],
            },
        },
        "errors": [],
        "advisories": [],
    }


def _content_type_maps(
    archive: zipfile.ZipFile,
    errors: list[dict[str, object]],
) -> tuple[dict[str, str], dict[str, str]]:
    try:
        root = ET.fromstring(archive.read("[Content_Types].xml"))
    except KeyError:
        errors.append(
            _issue(
                "missing_content_types",
                "PPTX package is missing [Content_Types].xml.",
            )
        )
        return {}, {}
    except ET.ParseError as exc:
        errors.append(
            _issue(
                "invalid_content_types",
                f"PPTX content-types XML is invalid: {exc}.",
            )
        )
        return {}, {}
    expected_root = f"{{{CONTENT_TYPES_NS}}}Types"
    if root.tag != expected_root:
        errors.append(
            _issue(
                "invalid_content_types",
                "PPTX content-types XML uses an invalid Types namespace.",
            )
        )
        return {}, {}

    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    default_tag = f"{{{CONTENT_TYPES_NS}}}Default"
    override_tag = f"{{{CONTENT_TYPES_NS}}}Override"
    for node in root:
        if node.tag == default_tag:
            raw_extension = (node.attrib.get("Extension") or "").strip()
            content_type = (node.attrib.get("ContentType") or "").strip()
            extension = raw_extension.lower()
            if not extension or extension.startswith(".") or not content_type:
                errors.append(
                    _issue(
                        "invalid_content_types",
                        "PPTX content-types Default entry is incomplete.",
                    )
                )
                continue
            if extension in defaults:
                errors.append(
                    _issue(
                        "invalid_content_types",
                        "PPTX content-types XML has a duplicate Default extension.",
                        extension=raw_extension,
                    )
                )
                continue
            defaults[extension] = content_type
            continue
        if node.tag == override_tag:
            raw_part_name = (node.attrib.get("PartName") or "").strip()
            content_type = (node.attrib.get("ContentType") or "").strip()
            part_name = raw_part_name.lstrip("/")
            if (
                not raw_part_name.startswith("/")
                or not part_name
                or ".." in PurePosixPath(part_name).parts
                or not content_type
            ):
                errors.append(
                    _issue(
                        "invalid_content_types",
                        "PPTX content-types Override entry is incomplete or invalid.",
                        part=raw_part_name or None,
                    )
                )
                continue
            if part_name in overrides:
                errors.append(
                    _issue(
                        "invalid_content_types",
                        "PPTX content-types XML has a duplicate Override part.",
                        part=raw_part_name,
                    )
                )
                continue
            overrides[part_name] = content_type
            continue
        errors.append(
            _issue(
                "invalid_content_types",
                "PPTX content-types XML contains an unexpected child.",
                child=node.tag,
            )
        )
    return defaults, overrides


def _content_type_for_part(
    part_name: str,
    defaults: dict[str, str],
    overrides: dict[str, str],
) -> str:
    declared = _declared_content_type_for_part(
        part_name,
        defaults,
        overrides,
    )
    if declared is not None:
        return declared
    guessed, _encoding = mimetypes.guess_type(part_name)
    return guessed or "application/octet-stream"


def _declared_content_type_for_part(
    part_name: str,
    defaults: dict[str, str],
    overrides: dict[str, str],
) -> str | None:
    if part_name in overrides:
        return overrides[part_name]
    filename = PurePosixPath(part_name).name
    extension = (
        "rels"
        if filename == ".rels" or filename.endswith(".rels")
        else PurePosixPath(part_name).suffix.lstrip(".").lower()
    )
    return defaults.get(extension)


def _xml_and_font_inventory(
    archive: zipfile.ZipFile,
    part_names: set[str],
    errors: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    font_counts: dict[str, Counter[str]] = {
        "latin": Counter(),
        "ea": Counter(),
        "cs": Counter(),
    }
    for part_name in sorted(
        name
        for name in part_names
        if name.endswith(".xml") and name != "[Content_Types].xml"
    ):
        try:
            root = ET.fromstring(archive.read(part_name))
        except (KeyError, ET.ParseError) as exc:
            errors.append(
                _issue(
                    "invalid_xml_part",
                    f"Cannot parse XML part {part_name}: {exc}.",
                    part=part_name,
                )
            )
            continue
        for role in font_counts:
            for element in root.iter(
                f"{{{DRAWINGML_NS}}}{role}"
            ):
                face = (element.attrib.get("typeface") or "").strip()
                if face:
                    font_counts[role][face] += 1
    return {
        role: [
            {"value": face, "count": count}
            for face, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], item[0].casefold()),
            )
        ]
        for role, counts in font_counts.items()
    }


def _relationship_kind(relationship_type: str) -> str | None:
    kind = relationship_type.rstrip("/").rsplit("/", 1)[-1].lower()
    return kind if kind in _MEDIA_REL_KINDS else None


def _relationship_inventory(
    archive: zipfile.ZipFile,
    part_names: set[str],
    errors: list[dict[str, object]],
) -> tuple[
    Counter[str],
    dict[str, set[str]],
    list[dict[str, object]],
]:
    reference_counts: Counter[str] = Counter()
    relationship_types: dict[str, set[str]] = defaultdict(set)
    external_counts: Counter[tuple[str, str, str]] = Counter()

    for rels_name in sorted(
        name for name in part_names if name.endswith(".rels")
    ):
        try:
            root = ET.fromstring(archive.read(rels_name))
        except (KeyError, ET.ParseError) as exc:
            errors.append(
                _issue(
                    "invalid_relationship_part",
                    f"Cannot parse relationship part {rels_name}: {exc}.",
                    part=rels_name,
                )
            )
            continue
        for relationship in root.findall(
            f"{{{PACKAGE_REL_NS}}}Relationship"
        ):
            relationship_type = (
                relationship.attrib.get("Type") or ""
            ).strip()
            target = (relationship.attrib.get("Target") or "").strip()
            target_mode = (
                relationship.attrib.get("TargetMode") or ""
            ).strip().lower()
            kind = _relationship_kind(relationship_type)
            if target_mode == "external":
                if kind and target:
                    external_counts[(kind, target, relationship_type)] += 1
                continue
            resolved = resolve_internal_opc_target(rels_name, target)
            if resolved is None:
                continue
            reference_counts[resolved] += 1
            if relationship_type:
                relationship_types[resolved].add(relationship_type)

    external = [
        {
            "target": target,
            "kind": kind,
            "relationship_type": relationship_type,
            "bytes": None,
            "compressed_bytes": None,
            "reference_count": count,
        }
        for (kind, target, relationship_type), count in sorted(
            external_counts.items()
        )
    ]
    return reference_counts, relationship_types, external


def _embedded_part_record(
    info: zipfile.ZipInfo,
    *,
    content_type: str,
    reference_counts: Counter[str],
    relationship_types: dict[str, set[str]],
) -> dict[str, object]:
    kind = content_type.split("/", 1)[0]
    if kind not in {"audio", "image", "video"}:
        kind = "media"
    part_key = canonical_opc_part_path(info.filename)
    return {
        "part": info.filename,
        "kind": kind,
        "content_type": content_type,
        "bytes": info.file_size,
        "compressed_bytes": info.compress_size,
        "reference_count": (
            reference_counts.get(part_key, 0)
            if part_key is not None
            else 0
        ),
        "relationship_types": sorted(
            relationship_types.get(part_key, set())
            if part_key is not None
            else set()
        ),
    }


def _archive_member_problems(
    infos: list[zipfile.ZipInfo],
) -> list[str]:
    problems: list[str] = []
    for info in infos:
        name = info.filename
        path = PurePosixPath(name)
        if (
            name.startswith("/")
            or "\\" in name
            or ".." in path.parts
        ):
            problems.append(name)
    return sorted(set(problems))


def _relationship_problem_code(problem: str) -> str:
    if "<invalid relationships XML:" in problem:
        return "invalid_relationship_xml"
    if " -> <" in problem:
        return "invalid_internal_relationship"
    return "dangling_internal_relationship"


def _font_faces_for_advisory(
    theme_fonts: object,
    declared_fonts: object,
) -> list[str]:
    faces: set[str] = set()
    if isinstance(theme_fonts, dict):
        for role in ("title", "body"):
            value = theme_fonts.get(role)
            if not isinstance(value, dict):
                continue
            for field in ("latin", "ea", "cs"):
                face = value.get(field)
                if isinstance(face, str) and face.strip():
                    faces.add(face.strip())
            scripts = value.get("scripts")
            if isinstance(scripts, dict):
                for face in scripts.values():
                    if isinstance(face, str) and face.strip():
                        faces.add(face.strip())
    if isinstance(declared_fonts, dict):
        for role in ("latin", "ea", "cs"):
            values = declared_fonts.get(role)
            if not isinstance(values, list):
                continue
            for value in values:
                if not isinstance(value, dict):
                    continue
                face = value.get("value")
                if isinstance(face, str) and face.strip():
                    faces.add(face.strip())
    return sorted(faces, key=str.casefold)


def _unsafe_font_faces(faces: list[str]) -> list[str]:
    unsafe: list[str] = []
    for face in faces:
        normalized = unicodedata.normalize("NFKC", face).strip().casefold()
        canonical = _PPT_SAFE_FONT_ALIASES.get(normalized, normalized)
        canonical = unicodedata.normalize(
            "NFKC",
            canonical,
        ).strip().casefold()
        if canonical.startswith("+") or canonical in _PPT_DELIVERY_SAFE_FONTS:
            continue
        unsafe.append(face)
    return unsafe


def _motion_and_hidden_summary(
    path: Path,
    errors: list[dict[str, object]],
) -> tuple[int, list[dict[str, object]], dict[str, object]]:
    hidden: list[dict[str, object]] = []
    transition_carriers: list[int] = []
    visual_transitions: list[int] = []
    timed_advances: list[int] = []
    transition_effects: Counter[str] = Counter()
    timing_slides: list[int] = []
    object_animation_slides: list[int] = []
    audio_timing_slides: list[int] = []
    slide_count = 0

    try:
        validate_pptx_animation_package(
            path,
            require_supported_effects=False,
        )
    except ValueError as exc:
        errors.append(
            _issue(
                "invalid_animation_structure",
                str(exc),
            )
        )

    try:
        with OoxmlPackage(path) as package:
            if package.zip is None:
                raise RuntimeError("PPTX package closed during slide audit")
            if package.presentation is None:
                raise RuntimeError("PPTX package has no presentation part")
            slide_roster = package.presentation.xml.find(
                f"{{{PRESENTATION_NS}}}sldIdLst"
            )
            roster_count = (
                len(
                    slide_roster.findall(
                        f"{{{PRESENTATION_NS}}}sldId"
                    )
                )
                if slide_roster is not None
                else 0
            )
            loaded_count = package.slide_count
            inspected_count = 0
            slide_count = roster_count
            for slide in package.iter_slides():
                inspected_count += 1
                try:
                    visible = parse_ooxml_boolean(
                        slide.part.xml.attrib.get("show"),
                        default=True,
                        context=f"{slide.part.path} show",
                    )
                except RuntimeError as exc:
                    errors.append(
                        _issue(
                            "invalid_slide_visibility",
                            str(exc),
                            slide_index=slide.index,
                            part=slide.part.path,
                        )
                    )
                    visible = True
                if not visible:
                    hidden.append(
                        {
                            "index": slide.index,
                            "part": slide.part.path,
                        }
                    )

                slide_xml = package.zip.read(slide.part.path)
                transition_problems = validate_slide_transition_xml(slide_xml)
                for problem in transition_problems:
                    errors.append(
                        _issue(
                            "invalid_transition_structure",
                            f"{slide.part.path}: {problem}",
                            slide_index=slide.index,
                            part=slide.part.path,
                        )
                    )
                try:
                    transition = read_slide_transition_xml(slide_xml)
                except (ET.ParseError, ValueError) as exc:
                    if not transition_problems:
                        errors.append(
                            _issue(
                                "transition_readback_failed",
                                f"{slide.part.path}: {exc}",
                                slide_index=slide.index,
                                part=slide.part.path,
                            )
                        )
                else:
                    if transition.logical_count:
                        transition_carriers.append(slide.index)
                        effect = (
                            transition.canonical_effect
                            or transition.effect
                            or "timing-only"
                        )
                        transition_effects[effect] += 1
                    if transition.effect is not None:
                        visual_transitions.append(slide.index)
                    if transition.advance_after_ms is not None:
                        timed_advances.append(slide.index)

                try:
                    animation = read_slide_animation_sequence(
                        slide_xml,
                        require_supported_effects=False,
                    )
                except (ET.ParseError, ValueError):
                    animation = None

                try:
                    has_object_animation = (
                        object_animation_fingerprint(slide_xml) is not None
                    )
                except ValueError as exc:
                    errors.append(
                        _issue(
                            "animation_presence_readback_failed",
                            f"{slide.part.path}: {exc}",
                            slide_index=slide.index,
                            part=slide.part.path,
                        )
                    )
                    has_object_animation = False

                root = ET.fromstring(slide_xml)
                has_timing = any(
                    node.tag == f"{{{PRESENTATION_NS}}}timing"
                    for node in root
                )
                has_audio_timing = any(
                    node.tag == f"{{{PRESENTATION_NS}}}audio"
                    for node in root.iter()
                )
                if animation is not None:
                    has_timing = has_timing or bool(animation.timing_count)
                    has_object_animation = (
                        has_object_animation or bool(animation.rows)
                    )
                    has_audio_timing = (
                        has_audio_timing or bool(animation.audio_target_ids)
                    )
                if has_timing:
                    timing_slides.append(slide.index)
                if has_object_animation:
                    object_animation_slides.append(slide.index)
                if has_audio_timing:
                    audio_timing_slides.append(slide.index)
            if (
                roster_count != loaded_count
                or loaded_count != inspected_count
            ):
                errors.append(
                    _issue(
                        "slide_inventory_failed",
                        (
                            f"Presentation declares {roster_count} slides, "
                            f"but the loader resolved {loaded_count} and the "
                            f"delivery audit inspected {inspected_count}."
                        ),
                        roster_count=roster_count,
                        loaded_count=loaded_count,
                        inspected_count=inspected_count,
                    )
                )
    except (KeyError, OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        errors.append(
            _issue(
                "slide_inventory_failed",
                f"Cannot inspect presentation slides: {exc}.",
            )
        )

    return slide_count, hidden, {
        "transitions": {
            "carrier_slide_count": len(transition_carriers),
            "visual_effect_slide_count": len(visual_transitions),
            "timed_advance_slide_count": len(timed_advances),
            "carrier_slides": transition_carriers,
            "visual_effect_slides": visual_transitions,
            "timed_advance_slides": timed_advances,
            "effects": dict(sorted(transition_effects.items())),
        },
        "object_animations": {
            "timing_slide_count": len(timing_slides),
            "object_animation_slide_count": len(object_animation_slides),
            "audio_timing_slide_count": len(audio_timing_slides),
            "timing_slides": timing_slides,
            "object_animation_slides": object_animation_slides,
            "audio_timing_slides": audio_timing_slides,
        },
    }


def _deduplicate_issues(
    issues: list[dict[str, object]],
) -> list[dict[str, object]]:
    seen: set[str] = set()
    output: list[dict[str, object]] = []
    for issue in issues:
        key = json.dumps(issue, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        output.append(issue)
    return output


def audit_pptx_delivery(path: str | Path) -> dict[str, object]:
    """Return a JSON-safe, read-only delivery audit for one PPTX file."""
    pptx_path = Path(path).expanduser().resolve()
    report = _empty_report(pptx_path)
    errors = report["errors"]
    advisories = report["advisories"]
    if not isinstance(errors, list) or not isinstance(advisories, list):
        raise AssertionError("delivery report issue containers are invalid")

    if not pptx_path.is_file():
        errors.append(
            _issue(
                "file_not_found",
                f"PPTX file not found: {pptx_path}.",
            )
        )
        return report

    try:
        with zipfile.ZipFile(pptx_path) as archive:
            infos = archive.infolist()
            file_infos = [info for info in infos if not info.is_dir()]
            names = [info.filename for info in file_infos]
            name_counts = Counter(names)
            duplicate_parts = sorted(
                name for name, count in name_counts.items() if count > 1
            )
            info_by_name = {info.filename: info for info in file_infos}
            part_names = set(info_by_name)
            canonical_names: dict[str, set[str]] = defaultdict(set)
            invalid_part_names: list[str] = []
            for name in part_names:
                canonical = canonical_opc_part_path(name)
                if canonical is None:
                    invalid_part_names.append(name)
                else:
                    canonical_names[canonical].add(name)
            canonical_collisions = sorted(
                sorted(raw_names)
                for raw_names in canonical_names.values()
                if len(raw_names) > 1
            )

            package = report["package"]
            if not isinstance(package, dict):
                raise AssertionError("delivery report package container is invalid")
            try:
                corrupt_member = archive.testzip()
            except (NotImplementedError, RuntimeError) as exc:
                package["zip_integrity"] = "failed"
                errors.append(
                    _issue(
                        "unsupported_zip_compression",
                        f"PPTX ZIP members cannot be decoded: {exc}.",
                    )
                )
                report["errors"] = _deduplicate_issues(errors)
                return report
            package["zip_integrity"] = (
                "passed" if corrupt_member is None else "failed"
            )
            package["corrupt_member"] = corrupt_member
            package["duplicate_parts"] = duplicate_parts
            package["canonical_part_collisions"] = canonical_collisions
            package["parts"] = {
                "entries": len(file_infos),
                "unique": len(part_names),
                "slides": sum(bool(_SLIDE_PART_RE.fullmatch(name)) for name in part_names),
                "notes": sum(bool(_NOTES_PART_RE.fullmatch(name)) for name in part_names),
                "masters": sum(bool(_MASTER_PART_RE.fullmatch(name)) for name in part_names),
                "layouts": sum(bool(_LAYOUT_PART_RE.fullmatch(name)) for name in part_names),
                "media": sum(
                    (canonical_opc_part_path(name) or "").startswith(
                        "ppt/media/"
                    )
                    for name in part_names
                ),
            }
            if corrupt_member is not None:
                errors.append(
                    _issue(
                        "zip_integrity_failed",
                        f"PPTX ZIP integrity failed at {corrupt_member}.",
                        part=corrupt_member,
                    )
                )
            if duplicate_parts:
                errors.append(
                    _issue(
                        "duplicate_package_parts",
                        "PPTX package contains duplicate part names.",
                        parts=duplicate_parts,
                    )
                )
            if canonical_collisions:
                errors.append(
                    _issue(
                        "duplicate_opc_part_names",
                        (
                            "PPTX package contains case- or encoding-equivalent "
                            "part names."
                        ),
                        parts=canonical_collisions,
                    )
                )
            if invalid_part_names:
                errors.append(
                    _issue(
                        "invalid_opc_part_name",
                        "PPTX package contains invalid OPC part names.",
                        parts=sorted(invalid_part_names),
                    )
                )

            defaults, overrides = _content_type_maps(archive, errors)
            content_type_registry_valid = not any(
                issue.get("code") in {
                    "missing_content_types",
                    "invalid_content_types",
                }
                for issue in errors
                if isinstance(issue, dict)
            )
            if content_type_registry_valid:
                missing_content_types = sorted(
                    name
                    for name in part_names
                    if name != "[Content_Types].xml"
                    and _declared_content_type_for_part(
                        name,
                        defaults,
                        overrides,
                    )
                    is None
                )
                if missing_content_types:
                    errors.append(
                        _issue(
                            "missing_part_content_type",
                            (
                                "PPTX package parts are missing a declared "
                                "Default or Override content type."
                            ),
                            parts=missing_content_types,
                        )
                    )
            declared_fonts = _xml_and_font_inventory(
                archive,
                part_names,
                errors,
            )
            reference_counts, relationship_types, external_media = (
                _relationship_inventory(archive, part_names, errors)
            )

            media_infos = [
                info_by_name[name]
                for name in sorted(part_names)
                if (
                    canonical_opc_part_path(name) or ""
                ).startswith("ppt/media/")
            ]
            embedded_media = [
                _embedded_part_record(
                    info,
                    content_type=_content_type_for_part(
                        info.filename,
                        defaults,
                        overrides,
                    ),
                    reference_counts=reference_counts,
                    relationship_types=relationship_types,
                )
                for info in media_infos
            ]
            embedded_media.sort(
                key=lambda item: (
                    -int(item["bytes"]),
                    str(item["part"]),
                )
            )

            embedded_font_infos = [
                info_by_name[name]
                for name in sorted(part_names)
                if name.startswith("ppt/fonts/")
                or name.lower().endswith(".fntdata")
            ]
            embedded_fonts = [
                {
                    "part": info.filename,
                    "content_type": _content_type_for_part(
                        info.filename,
                        defaults,
                        overrides,
                    ),
                    "bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "reference_count": reference_counts.get(
                        canonical_opc_part_path(info.filename) or "",
                        0,
                    ),
                }
                for info in embedded_font_infos
            ]

            media_bytes = sum(info.file_size for info in media_infos)
            media_compressed_bytes = sum(
                info.compress_size for info in media_infos
            )
            total_uncompressed_bytes = sum(
                info.file_size for info in info_by_name.values()
            )
            file_bytes = pptx_path.stat().st_size
            media = report["media"]
            if not isinstance(media, dict):
                raise AssertionError("delivery report media container is invalid")
            media.update(
                {
                    "embedded_count": len(embedded_media),
                    "external_count": len(external_media),
                    "embedded": embedded_media,
                    "external": external_media,
                    "uncompressed_bytes": media_bytes,
                    "archive_compressed_bytes": media_compressed_bytes,
                    "share_of_archive": (
                        round(media_compressed_bytes / file_bytes, 6)
                        if file_bytes
                        else 0.0
                    ),
                    "share_of_uncompressed_parts": (
                        round(media_bytes / total_uncompressed_bytes, 6)
                        if total_uncompressed_bytes
                        else 0.0
                    ),
                    "top_contributors": embedded_media[:10],
                }
            )
            fonts = report["fonts"]
            if not isinstance(fonts, dict):
                raise AssertionError("delivery report fonts container is invalid")
            fonts["embedded_parts"] = embedded_fonts
            fonts["declared"] = declared_fonts

            unsafe_members = _archive_member_problems(infos)
            if unsafe_members:
                errors.append(
                    _issue(
                        "unsafe_package_member",
                        "PPTX package contains unsafe member paths.",
                        parts=unsafe_members,
                    )
                )
                relationship_problems: list[str] = []
            else:
                with tempfile.TemporaryDirectory(
                    prefix="pptx-delivery-check-"
                ) as tmp:
                    extract_dir = Path(tmp) / "pptx"
                    archive.extractall(extract_dir)
                    relationship_problems = verify_internal_relationships(
                        extract_dir
                    )
            relationships = package["relationships"]
            if not isinstance(relationships, dict):
                raise AssertionError(
                    "delivery report relationships container is invalid"
                )
            relationships["problems"] = relationship_problems
            for problem in relationship_problems:
                errors.append(
                    _issue(
                        _relationship_problem_code(problem),
                        problem,
                    )
                )
    except zipfile.BadZipFile as exc:
        errors.append(
            _issue(
                "invalid_zip_package",
                f"File is not a readable PPTX ZIP package: {exc}.",
            )
        )
        return report
    except (NotImplementedError, RuntimeError) as exc:
        errors.append(
            _issue(
                "unsupported_zip_compression",
                f"PPTX ZIP members cannot be decoded: {exc}.",
            )
        )
        return report
    except OSError as exc:
        errors.append(
            _issue(
                "package_read_failed",
                f"Cannot read PPTX package: {exc}.",
            )
        )
        return report

    try:
        identity = extract_identity(pptx_path)
    except (KeyError, OSError, RuntimeError, ValueError, zipfile.BadZipFile) as exc:
        advisories.append(
            _issue(
                "font_inventory_unavailable",
                f"Could not resolve theme and declared font facts: {exc}.",
            )
        )
    else:
        identity_theme = identity.get("theme")
        theme_fonts = (
            identity_theme.get("fonts", {})
            if isinstance(identity_theme, dict)
            else {}
        )
        fonts = report["fonts"]
        if not isinstance(fonts, dict):
            raise AssertionError("delivery report fonts container is invalid")
        declared_fonts = fonts.get("declared", {})
        if not isinstance(declared_fonts, dict):
            declared_fonts = {}
        fonts["theme"] = theme_fonts
        unsafe_faces = _unsafe_font_faces(
            _font_faces_for_advisory(theme_fonts, declared_fonts)
        )
        fonts["portability_advisory_faces"] = unsafe_faces
        if unsafe_faces:
            advisories.append(
                _issue(
                    "font_portability",
                    (
                        "Some fonts declared or referenced by the presentation "
                        "are outside the common Office/OS portability set; "
                        "target-system availability was not verified."
                    ),
                    faces=unsafe_faces,
                )
            )

    slide_count, hidden_slides, motion = _motion_and_hidden_summary(
        pptx_path,
        errors,
    )
    slides = report["slides"]
    if not isinstance(slides, dict):
        raise AssertionError("delivery report slides container is invalid")
    slides.update(
        {
            "count": slide_count,
            "hidden_count": len(hidden_slides),
            "hidden": hidden_slides,
        }
    )
    report["motion"] = motion
    if hidden_slides:
        advisories.append(
            _issue(
                "hidden_slides",
                "The presentation contains hidden slides; their state was not changed.",
                slides=[item["index"] for item in hidden_slides],
            )
        )

    media = report["media"]
    if isinstance(media, dict) and media.get("external_count"):
        advisories.append(
            _issue(
                "external_media",
                (
                    "The presentation contains externally linked media; "
                    "offline delivery may depend on those targets."
                ),
                targets=[
                    item["target"]
                    for item in media.get("external", [])
                    if isinstance(item, dict) and "target" in item
                ],
            )
        )

    report["errors"] = _deduplicate_issues(errors)
    report["advisories"] = _deduplicate_issues(advisories)
    report["status"] = (
        "failed"
        if report["errors"]
        else (
            "passed-with-advisories"
            if report["advisories"]
            else "passed"
        )
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a finished PPTX for delivery risks without modifying it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pptx", help="Finished .pptx file to inspect")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit_pptx_delivery(args.pptx)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
