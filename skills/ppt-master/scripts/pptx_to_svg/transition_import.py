"""Import PPT Master-owned slide transitions into animations.json rows.

The reverse contract accepts only source XML that passes the existing
generated-transition read-back validator. Unknown third-party carriers remain
outside the reconstruction claim and are handled by the caller's diagnostics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath

from pptx_transitions import (
    TransitionSummary,
    read_slide_transition_xml,
    validate_generated_transition_xml,
)

from .ooxml_loader import OoxmlPackage, SlideRef


_AUDIO_RELATIONSHIP_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
)


class TransitionImportError(ValueError):
    """Raised when a source transition is outside the reversible contract."""


@dataclass(frozen=True)
class TransitionImport:
    """One canonical sidecar row plus any extracted transition sound."""

    config: dict[str, object]
    media_files: dict[str, bytes]


@dataclass(frozen=True)
class TransitionReadback:
    """One validated transition before its sound relationship is resolved."""

    config: dict[str, object]
    summary: TransitionSummary


def read_transition_config(
    slide_xml: str | bytes,
) -> TransitionReadback | None:
    """Read one exact generated-transition contract from slide XML."""
    summary = read_slide_transition_xml(slide_xml)
    if summary.logical_count == 0:
        return None
    if summary.speed is not None:
        raise TransitionImportError(
            "legacy p:transition@spd cannot be represented exactly by "
            "animations.json duration"
        )
    if summary.effect is not None and summary.canonical_effect is None:
        raise TransitionImportError(
            "transition effect is outside the canonical native registry"
        )
    if summary.canonical_effect is not None and summary.duration_ms is None:
        raise TransitionImportError(
            "visual transition is missing the exact p14:dur duration"
        )

    sound = _sound_expectation(summary)
    duration = (
        summary.duration_ms / 1000.0
        if summary.duration_ms is not None
        else 0.0
    )
    advance_after = (
        summary.advance_after_ms / 1000.0
        if summary.advance_after_ms is not None
        else None
    )
    try:
        validate_generated_transition_xml(
            slide_xml,
            effect=summary.canonical_effect,
            effect_options=summary.effect_options,
            duration=duration,
            advance_on_click=summary.advance_on_click,
            advance_after=advance_after,
            sound=sound,
        )
    except ValueError as exc:
        raise TransitionImportError(str(exc)) from exc
    if summary.advance_on_click is not True:
        raise TransitionImportError(
            "advance_on_click=false is outside the animations.json "
            "transition contract"
        )

    config: dict[str, object] = {
        "effect": summary.canonical_effect or "none",
    }
    if summary.effect_options:
        config["effect_options"] = dict(summary.effect_options)
    if summary.canonical_effect is not None:
        config["duration"] = duration
    if advance_after is not None:
        config["auto_advance"] = advance_after
    return TransitionReadback(config=config, summary=summary)


def import_slide_transition(
    pkg: OoxmlPackage,
    slide: SlideRef,
    *,
    media_subdir: str,
    resource_path_map: dict[str, str] | None = None,
) -> TransitionImport | None:
    """Read one slide transition and resolve its optional WAV relationship."""
    slide_xml = pkg.read_part_bytes(slide.part.path)
    if slide_xml is None:
        raise TransitionImportError(
            f"source slide part is missing: {slide.part.path}"
        )
    readback = read_transition_config(slide_xml)
    if readback is None:
        return None

    config = dict(readback.config)
    media_files: dict[str, bytes] = {}
    relationship_id = readback.summary.sound_relationship_id
    if relationship_id is not None:
        source_part, sound_path, sound_bytes = _resolve_transition_sound(
            pkg,
            slide,
            relationship_id,
        )
        mapped_path = (resource_path_map or {}).get(source_part)
        if mapped_path is not None:
            config["sound"] = mapped_path
        else:
            media_files[sound_path] = sound_bytes
            config["sound"] = (
                PurePosixPath(media_subdir) / sound_path
            ).as_posix()
    return TransitionImport(config=config, media_files=media_files)


def _sound_expectation(
    summary: TransitionSummary,
) -> dict[str, str] | None:
    relationship_id = summary.sound_relationship_id
    name = summary.sound_name
    if relationship_id is None and name is None:
        return None
    if not relationship_id or not name:
        raise TransitionImportError(
            "transition sound requires both relationship id and display name"
        )
    return {
        "relationship_id": relationship_id,
        "name": name,
    }


def _resolve_transition_sound(
    pkg: OoxmlPackage,
    slide: SlideRef,
    relationship_id: str,
) -> tuple[str, str, bytes]:
    relationship = slide.part.rels.get(relationship_id)
    if relationship is None:
        raise TransitionImportError(
            f"transition sound relationship is missing: {relationship_id}"
        )
    if relationship.get("external"):
        raise TransitionImportError("transition sound relationship must be internal")
    if relationship.get("type") != _AUDIO_RELATIONSHIP_TYPE:
        raise TransitionImportError(
            "transition sound relationship must use the OOXML audio type"
        )
    target = relationship.get("target") or ""
    if PurePosixPath(target).suffix.lower() != ".wav":
        raise TransitionImportError("transition sound part must use .wav")
    payload = pkg.read_part_bytes(target)
    if payload is None:
        raise TransitionImportError(
            f"transition sound part is missing: {target}"
        )
    if not (
        len(payload) >= 12
        and payload[:4] in {b"RIFF", b"RF64"}
        and payload[8:12] == b"WAVE"
    ):
        raise TransitionImportError(
            f"transition sound part is not a valid WAV file: {target}"
        )
    digest = hashlib.sha256(payload).hexdigest()[:16]
    return target, f"transition_sound_{digest}.wav", payload


__all__ = [
    "TransitionImport",
    "TransitionImportError",
    "TransitionReadback",
    "import_slide_transition",
    "read_transition_config",
]
