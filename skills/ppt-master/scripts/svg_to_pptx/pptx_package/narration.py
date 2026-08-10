"""Narration audio discovery and PPTX XML helpers."""

from __future__ import annotations

import base64
import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_transitions import (
    AdvanceUpdate,
    EnterUpdate,
    MAX_OOXML_UNSIGNED_INT,
    P14_NS,
    PML_NS,
    apply_slide_motion_xml,
    parse_source_xml,
    read_slide_transition_xml,
    serialize_source_xml,
    validate_seconds,
)


DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MARKUP_COMPATIBILITY_NS = (
    "http://schemas.openxmlformats.org/markup-compatibility/2006"
)

MEDIA_REL_TYPE = "http://schemas.microsoft.com/office/2007/relationships/media"
AUDIO_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

AUDIO_CONTENT_TYPES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}

NARRATION_EXTENSIONS = tuple(AUDIO_CONTENT_TYPES.keys())
DEFAULT_NARRATION_START_FLOOR = 0.8

AUDIO_MARKER_SIZE_EMU = 457200  # 48 SVG px
AUDIO_MARKER_OFF_CANVAS_EMU = -AUDIO_MARKER_SIZE_EMU
AUDIO_MARKER_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAABsUlEQVR4nO2aQZaDIAyG"
    "cd4cQRdzgHqxeiy9mB5gFvUO7Qon0gAhJEDf+G/a92rJ9ycEqNaYS3XVSQ94uz+esWu"
    "2ZRCLKzIQBdqnXDPsL+dA+8Qx88UJpAHPHTfJsRY4Jmo1yBUoCZ8Sj2SgNHxK3KiBWv"
    "DU+EEDteGtQhxeA63AW/l4WMuolNa5zx4DNaCd/XXuWfAY15sBTXguOJTL9501GlG50"
    "Ovc/xpjzDjtP+5nqj0gkXEL7763OhmQmj4S4FZY1iGnaAUkwQMxTlWouoz65CYBq4LV"
    "0cTU6VMgw8frOO3e6273x3Nbhq7JCmCCVYDTqDkDMOuUajdnIFWXgdq6DEgLNm5oGbV"
    "qzoBPcOmES+qxkW3L0FE2s1BWJDa5cdqjm5gxf7ddmqyAC4+dQq1EDYzTTpq3mTFO56"
    "KTAam7xpJGsOxDTtUpJGEEZhw7lRb5SWlNcJs8dJx+q4DkwwcEJLsiLh86hTRNGMM3g"
    "nFVXUYlGt1rQLsKqfLxBCvQiokQR3QK1TYRi0/qgVomKHHJTVzaBDUeC0rzBnBqoljL"
    "qFY1OOP+3yf1PpX+r8TH6wW14c3/7xdFRAAAAABJRU5ErkJggg=="
)


for _prefix, _uri in (
    ("p", PML_NS),
    ("a", DRAWINGML_NS),
    ("r", RELATIONSHIPS_NS),
    ("p14", P14_NS),
):
    try:
        ET.register_namespace(_prefix, _uri)
    except (AttributeError, ValueError):
        pass


def _qn(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def _normalize_title(title: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", title.strip())
    return re.sub(r"_+", "_", text).strip("_").lower()


def _leading_number(text: str) -> int | None:
    match = re.match(r"^(\d{1,3})", text.strip())
    return int(match.group(1)) if match else None


def find_narration_files(audio_dir: Path, svg_files: list[Path]) -> dict[str, Path]:
    """Return `{svg_stem: audio_path}` matched by exact stem, normalized stem, or index."""
    if not audio_dir.exists() or not audio_dir.is_dir():
        return {}

    audio_files = [
        path for path in sorted(audio_dir.iterdir())
        if path.is_file() and path.suffix.lower() in NARRATION_EXTENSIONS
    ]
    exact: dict[str, list[Path]] = {}
    normalized: dict[str, list[Path]] = {}
    numbered: dict[int, list[Path]] = {}
    for path in audio_files:
        exact.setdefault(path.stem, []).append(path)
        normalized.setdefault(_normalize_title(path.stem), []).append(path)
        number = _leading_number(path.stem)
        if number is not None:
            numbered.setdefault(number, []).append(path)

    matched: dict[str, Path] = {}
    claimed_by: dict[Path, str] = {}
    for index, svg in enumerate(svg_files, 1):
        stem = svg.stem
        candidates = exact.get(stem)
        if not candidates:
            candidates = normalized.get(_normalize_title(stem))
        if not candidates:
            candidates = numbered.get(index)
        if not candidates:
            continue
        if len(candidates) > 1:
            names = ", ".join(path.name for path in candidates)
            raise ValueError(
                f"multiple narration audio files match slide {stem!r}: "
                f"{names}; keep exactly one supported file for this slide"
            )
        candidate = candidates[0]
        previous_stem = claimed_by.get(candidate)
        if previous_stem is not None:
            raise ValueError(
                f"narration audio file {candidate.name!r} matches multiple slides: "
                f"{previous_stem!r}, {stem!r}; provide one distinct audio file "
                "per slide"
            )
        matched[stem] = candidate
        claimed_by[candidate] = stem
    return matched


def probe_audio_duration(audio_path: Path) -> float | None:
    """Return duration in seconds using ffprobe when available."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        data = json.loads(result.stdout or "{}")
        duration = float(data.get("format", {}).get("duration", 0))
        return duration if duration > 0 else None
    except Exception:
        return None


def next_shape_id(slide_xml: str) -> int:
    """Return the next slide-local non-visual shape id."""
    root = parse_source_xml(slide_xml)
    if root.tag != _qn(PML_NS, "sld"):
        raise ValueError("narration source XML root must be p:sld")
    ids = _numeric_ids(
        root.iter(_qn(PML_NS, "cNvPr")),
        "shape",
        minimum=1,
    )
    next_id = max(ids, default=1) + 1
    if next_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError("narration source has no available shape identifiers")
    return next_id


def _create_audio_pic_element(
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
) -> ET.Element:
    pic = ET.Element(_qn(PML_NS, "pic"))
    nv_pic_pr = ET.SubElement(pic, _qn(PML_NS, "nvPicPr"))
    c_nv_pr = ET.SubElement(
        nv_pic_pr,
        _qn(PML_NS, "cNvPr"),
        {"id": str(shape_id), "name": shape_name},
    )
    ET.SubElement(
        c_nv_pr,
        _qn(DRAWINGML_NS, "hlinkClick"),
        {
            _qn(RELATIONSHIPS_NS, "id"): "",
            "action": "ppaction://media",
        },
    )
    c_nv_pic_pr = ET.SubElement(nv_pic_pr, _qn(PML_NS, "cNvPicPr"))
    ET.SubElement(
        c_nv_pic_pr,
        _qn(DRAWINGML_NS, "picLocks"),
        {"noChangeAspect": "1"},
    )
    nv_pr = ET.SubElement(nv_pic_pr, _qn(PML_NS, "nvPr"))
    ET.SubElement(
        nv_pr,
        _qn(DRAWINGML_NS, "audioFile"),
        {_qn(RELATIONSHIPS_NS, "link"): audio_rid},
    )
    ext_list = ET.SubElement(nv_pr, _qn(PML_NS, "extLst"))
    extension = ET.SubElement(
        ext_list,
        _qn(PML_NS, "ext"),
        {"uri": "{DAA4B4D4-6D71-4841-9C94-3DE7FCFB9230}"},
    )
    ET.SubElement(
        extension,
        _qn(P14_NS, "media"),
        {_qn(RELATIONSHIPS_NS, "embed"): media_rid},
    )

    blip_fill = ET.SubElement(pic, _qn(PML_NS, "blipFill"))
    ET.SubElement(
        blip_fill,
        _qn(DRAWINGML_NS, "blip"),
        {_qn(RELATIONSHIPS_NS, "embed"): poster_rid},
    )
    stretch = ET.SubElement(blip_fill, _qn(DRAWINGML_NS, "stretch"))
    ET.SubElement(stretch, _qn(DRAWINGML_NS, "fillRect"))

    shape_properties = ET.SubElement(pic, _qn(PML_NS, "spPr"))
    transform = ET.SubElement(shape_properties, _qn(DRAWINGML_NS, "xfrm"))
    ET.SubElement(
        transform,
        _qn(DRAWINGML_NS, "off"),
        {
            "x": str(AUDIO_MARKER_OFF_CANVAS_EMU),
            "y": str(AUDIO_MARKER_OFF_CANVAS_EMU),
        },
    )
    ET.SubElement(
        transform,
        _qn(DRAWINGML_NS, "ext"),
        {
            "cx": str(AUDIO_MARKER_SIZE_EMU),
            "cy": str(AUDIO_MARKER_SIZE_EMU),
        },
    )
    geometry = ET.SubElement(
        shape_properties,
        _qn(DRAWINGML_NS, "prstGeom"),
        {"prst": "rect"},
    )
    ET.SubElement(geometry, _qn(DRAWINGML_NS, "avLst"))
    return pic


def create_audio_pic_xml(
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
) -> str:
    """Create an off-canvas audio picture shape carrying narration media."""
    element = _create_audio_pic_element(
        shape_id,
        shape_name,
        audio_rid,
        media_rid,
        poster_rid,
    )
    return ET.tostring(element, encoding="unicode")


def _numeric_ids(
    elements: Iterable[ET.Element],
    label: str,
    *,
    minimum: int = 0,
    maximum: int = MAX_OOXML_UNSIGNED_INT,
) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for element in elements:
        raw_id = element.get("id")
        try:
            numeric_id = int(raw_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"narration source has invalid {label} id: {raw_id!r}") from exc
        if numeric_id < minimum:
            raise ValueError(
                f"narration source has {label} id below {minimum}: {numeric_id}"
            )
        if numeric_id > maximum:
            raise ValueError(
                f"narration source has {label} id above {maximum}: {numeric_id}"
            )
        if numeric_id in seen:
            raise ValueError(f"narration source has duplicate {label} id: {numeric_id}")
        ids.append(numeric_id)
        seen.add(numeric_id)
    return ids


def narration_lead_in_seconds(
    transition_duration: float,
    *,
    start_floor: float = DEFAULT_NARRATION_START_FLOOR,
) -> float:
    """Return silence after a slide transition before narration starts."""
    transition_seconds = validate_seconds(
        transition_duration,
        "narration transition duration",
        allow_zero=True,
    )
    floor_seconds = validate_seconds(
        start_floor,
        "narration start floor",
        allow_zero=True,
    )
    return max(0.0, floor_seconds - transition_seconds)


def _create_audio_timing_element(
    shape_id: int,
    ctn_id: int,
    start_delay_ms: int,
) -> ET.Element:
    audio = ET.Element(_qn(PML_NS, "audio"))
    media_node = ET.SubElement(
        audio,
        _qn(PML_NS, "cMediaNode"),
        {"vol": "80000"},
    )
    time_node = ET.SubElement(
        media_node,
        _qn(PML_NS, "cTn"),
        {"id": str(ctn_id), "fill": "hold", "display": "0"},
    )
    start_conditions = ET.SubElement(time_node, _qn(PML_NS, "stCondLst"))
    ET.SubElement(
        start_conditions,
        _qn(PML_NS, "cond"),
        {"delay": str(start_delay_ms)},
    )
    target = ET.SubElement(media_node, _qn(PML_NS, "tgtEl"))
    ET.SubElement(target, _qn(PML_NS, "spTgt"), {"spid": str(shape_id)})
    return audio


def _direct_child(parent: ET.Element, tag: str, label: str) -> ET.Element:
    children = [child for child in parent if child.tag == tag]
    if len(children) != 1:
        raise ValueError(
            f"narration source must contain exactly one direct {label}; found {len(children)}"
        )
    return children[0]


def _existing_timing_root(timing: ET.Element) -> ET.Element:
    children = list(timing)
    for tag, label in (
        (_qn(PML_NS, "tnLst"), "p:tnLst"),
        (_qn(PML_NS, "bldLst"), "p:bldLst"),
        (_qn(PML_NS, "extLst"), "p:extLst"),
    ):
        if sum(child.tag == tag for child in children) > 1:
            raise ValueError(f"narration source timing has multiple {label} elements")
    node_list = _direct_child(timing, _qn(PML_NS, "tnLst"), "p:timing/p:tnLst")
    node_index = children.index(node_list)
    for tag, label in (
        (_qn(PML_NS, "bldLst"), "p:bldLst"),
        (_qn(PML_NS, "extLst"), "p:extLst"),
    ):
        sibling = next((child for child in children if child.tag == tag), None)
        if sibling is not None and node_index > children.index(sibling):
            raise ValueError(f"narration source p:tnLst must precede {label}")
    timing_roots = [
        element
        for element in node_list.iter(_qn(PML_NS, "cTn"))
        if element.get("nodeType") == "tmRoot"
    ]
    if len(timing_roots) != 1:
        raise ValueError(
            "narration source timing must contain exactly one tmRoot; "
            f"found {len(timing_roots)}"
        )
    return timing_roots[0]


def _new_timing(audio_timing: ET.Element, root_id: int) -> ET.Element:
    timing = ET.Element(_qn(PML_NS, "timing"))
    node_list = ET.SubElement(timing, _qn(PML_NS, "tnLst"))
    parallel = ET.SubElement(node_list, _qn(PML_NS, "par"))
    timing_root = ET.SubElement(
        parallel,
        _qn(PML_NS, "cTn"),
        {
            "id": str(root_id),
            "dur": "indefinite",
            "restart": "never",
            "nodeType": "tmRoot",
        },
    )
    child_nodes = ET.SubElement(timing_root, _qn(PML_NS, "childTnLst"))
    child_nodes.append(audio_timing)
    return timing


def _root_extension_index(slide: ET.Element) -> int | None:
    extension_lists = [
        index
        for index, child in enumerate(slide)
        if child.tag == _qn(PML_NS, "extLst")
    ]
    if len(extension_lists) > 1:
        raise ValueError("narration source has multiple root p:extLst elements")
    if extension_lists and extension_lists[0] != len(slide) - 1:
        raise ValueError("narration source root p:extLst is not the last slide child")
    return extension_lists[0] if extension_lists else None


def _validate_root_timing_position(slide: ET.Element, timing: ET.Element) -> None:
    children = list(slide)
    timing_index = children.index(timing)
    for tag, label in (
        (_qn(PML_NS, "cSld"), "p:cSld"),
        (_qn(PML_NS, "clrMapOvr"), "p:clrMapOvr"),
    ):
        siblings = [index for index, child in enumerate(children) if child.tag == tag]
        if len(siblings) > 1:
            raise ValueError(f"narration source has multiple root {label} elements")
        if siblings and siblings[0] > timing_index:
            raise ValueError(f"narration source root p:timing must follow {label}")
    extension_index = _root_extension_index(slide)
    if extension_index is not None and timing_index > extension_index:
        raise ValueError("narration source root p:timing must precede p:extLst")


def _insert_root_timing(slide: ET.Element, timing: ET.Element) -> None:
    extension_index = _root_extension_index(slide)
    insert_at = extension_index if extension_index is not None else len(slide)
    slide.insert(insert_at, timing)


def _animation_timing_branches(
    slide: ET.Element,
) -> tuple[ET.Element | None, list[ET.Element]]:
    """Return the root timing anchor and every active/fallback timing branch."""
    direct = [
        child for child in slide
        if child.tag == _qn(PML_NS, "timing")
    ]
    alternates: list[tuple[ET.Element, list[ET.Element]]] = []
    for child in slide:
        if child.tag != _qn(MARKUP_COMPATIBILITY_NS, "AlternateContent"):
            continue
        timings = [
            timing
            for branch in list(child)
            for timing in list(branch)
            if timing.tag == _qn(PML_NS, "timing")
        ]
        if timings:
            alternates.append((child, timings))
    if direct and alternates:
        raise ValueError(
            "narration source contains both direct and AlternateContent timing"
        )
    if len(direct) > 1 or len(alternates) > 1:
        raise ValueError("narration source has multiple root animation timings")
    if direct:
        return direct[0], direct
    if alternates:
        anchor, timings = alternates[0]
        if len(timings) != 2:
            raise ValueError(
                "narration source animation AlternateContent must contain "
                "one Choice and one Fallback timing"
            )
        return anchor, timings
    nested = list(slide.iter(_qn(PML_NS, "timing")))
    if nested:
        raise ValueError(
            "narration source contains unsupported non-root p:timing"
        )
    return None, []


def inject_narration(
    slide_xml: str,
    *,
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
    start_delay: float = 0.0,
) -> str:
    """Inject a hidden narration shape and delayed slide-entry autoplay timing."""
    if isinstance(shape_id, bool) or not isinstance(shape_id, int) or shape_id <= 0:
        raise ValueError("narration shape_id must be a positive integer")
    if shape_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            "narration shape_id exceeds the OOXML unsigned-integer limit: "
            f"{shape_id}"
        )
    start_delay_seconds = validate_seconds(
        start_delay,
        "narration start delay",
        allow_zero=True,
    )
    start_delay_ms = round(start_delay_seconds * 1000)
    if start_delay_ms > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            "narration start delay exceeds the OOXML unsigned-integer limit: "
            f"{start_delay_ms} ms"
        )

    root = parse_source_xml(slide_xml)
    if root.tag != _qn(PML_NS, "sld"):
        raise ValueError("narration source XML root must be p:sld")
    common_slide_data = _direct_child(root, _qn(PML_NS, "cSld"), "p:sld/p:cSld")
    shape_tree = _direct_child(
        common_slide_data,
        _qn(PML_NS, "spTree"),
        "p:cSld/p:spTree",
    )

    shape_ids = _numeric_ids(
        root.iter(_qn(PML_NS, "cNvPr")),
        "shape",
        minimum=1,
    )
    if shape_id in shape_ids:
        raise ValueError(f"narration shape id already exists on slide: {shape_id}")
    timing_anchor, timing_branches = _animation_timing_branches(root)
    timing_id_sets = [
        _numeric_ids(timing.iter(_qn(PML_NS, "cTn")), "timing node")
        for timing in timing_branches
    ]
    timing_ids = [
        timing_id
        for timing_set in timing_id_sets
        for timing_id in timing_set
    ]
    next_timing_id = max(timing_ids, default=0) + 1
    if next_timing_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError("narration source has no available timing node identifiers")

    if not timing_branches and next_timing_id + 1 > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            "narration source has no identifiers available for a new timing root"
        )

    audio_picture = _create_audio_pic_element(
        shape_id,
        shape_name,
        audio_rid,
        media_rid,
        poster_rid,
    )
    shape_tree.append(audio_picture)

    if timing_branches:
        if timing_anchor is None:
            raise AssertionError("timing branches lost their root anchor")
        _validate_root_timing_position(root, timing_anchor)
        for timing in timing_branches:
            timing_root = _existing_timing_root(timing)
            child_nodes = _direct_child(
                timing_root,
                _qn(PML_NS, "childTnLst"),
                "tmRoot/p:childTnLst",
            )
            child_nodes.append(
                _create_audio_timing_element(
                    shape_id,
                    next_timing_id,
                    start_delay_ms,
                )
            )
    else:
        audio_timing = _create_audio_timing_element(
            shape_id,
            next_timing_id + 1,
            start_delay_ms,
        )
        _insert_root_timing(root, _new_timing(audio_timing, next_timing_id))

    return serialize_source_xml(root, slide_xml).decode("utf-8")


def read_narration_start_delay_xml(slide_xml: str) -> int:
    """Return the latest embedded narration picture's autoplay delay in ms."""
    root = parse_source_xml(slide_xml)
    if root.tag != _qn(PML_NS, "sld"):
        raise ValueError("narration source XML root must be p:sld")

    audio_shape_properties: list[ET.Element] = []
    for picture in root.iter(_qn(PML_NS, "pic")):
        if not any(
            element.tag == _qn(DRAWINGML_NS, "audioFile")
            for element in picture.iter()
        ):
            continue
        properties = list(picture.iter(_qn(PML_NS, "cNvPr")))
        if len(properties) != 1:
            raise ValueError(
                "narration audio picture must contain exactly one p:cNvPr"
            )
        audio_shape_properties.extend(properties)
    if not audio_shape_properties:
        raise ValueError("narration source has no embedded audio picture")

    narration_shape_id = max(
        _numeric_ids(
            audio_shape_properties,
            "narration audio shape",
            minimum=1,
        )
    )
    delays: list[int] = []
    for audio in root.iter(_qn(PML_NS, "audio")):
        media_node = audio.find(_qn(PML_NS, "cMediaNode"))
        if media_node is None:
            continue
        target = media_node.find(
            f"{_qn(PML_NS, 'tgtEl')}/{_qn(PML_NS, 'spTgt')}"
        )
        if target is None or target.get("spid") != str(narration_shape_id):
            continue
        time_node = _direct_child(
            media_node,
            _qn(PML_NS, "cTn"),
            "p:audio/p:cMediaNode/p:cTn",
        )
        start_conditions = _direct_child(
            time_node,
            _qn(PML_NS, "stCondLst"),
            "p:cTn/p:stCondLst",
        )
        condition = _direct_child(
            start_conditions,
            _qn(PML_NS, "cond"),
            "p:stCondLst/p:cond",
        )
        raw_delay = condition.get("delay")
        try:
            delay = int(raw_delay)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"narration timing has invalid start delay: {raw_delay!r}"
            ) from exc
        if delay < 0 or delay > MAX_OOXML_UNSIGNED_INT:
            raise ValueError(
                "narration timing start delay is outside the OOXML "
                f"unsigned-integer range: {delay}"
            )
        delays.append(delay)

    if not delays:
        raise ValueError("narration source has no autoplay timing for its audio picture")
    if len(set(delays)) != 1:
        raise ValueError(
            "narration source timing branches disagree on autoplay delay: "
            f"{sorted(set(delays))}"
        )
    return delays[0]


def apply_recorded_timing(
    slide_xml: str,
    *,
    advance_after: float,
    transition_duration: float,
    transition_effect: str | None = "fade",
) -> str:
    """Set slide auto-advance timing so exported video follows narration length."""
    summary = read_slide_transition_xml(slide_xml)
    if summary.logical_count:
        enter = EnterUpdate(policy="preserve")
    elif transition_effect is None or transition_effect == "none":
        enter = EnterUpdate(policy="none")
    else:
        enter = EnterUpdate(
            policy="replace",
            effect=transition_effect,
            duration=transition_duration,
        )
    updated, _uses_timings = apply_slide_motion_xml(
        slide_xml,
        enter=enter,
        advance=AdvanceUpdate(mode="narration", after=advance_after),
    )
    return updated
