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
)


DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

MEDIA_REL_TYPE = "http://schemas.microsoft.com/office/2007/relationships/media"
AUDIO_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/audio"
IMAGE_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

AUDIO_CONTENT_TYPES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
}

NARRATION_EXTENSIONS = tuple(AUDIO_CONTENT_TYPES.keys())

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
    exact = {path.stem: path for path in audio_files}
    normalized: dict[str, Path] = {}
    numbered: dict[int, Path] = {}
    for path in audio_files:
        normalized.setdefault(_normalize_title(path.stem), path)
        number = _leading_number(path.stem)
        if number is not None:
            numbered.setdefault(number, path)

    matched: dict[str, Path] = {}
    for index, svg in enumerate(svg_files, 1):
        stem = svg.stem
        if stem in exact:
            matched[stem] = exact[stem]
            continue
        norm = _normalize_title(stem)
        if norm in normalized:
            matched[stem] = normalized[norm]
            continue
        if index in numbered:
            matched[stem] = numbered[index]
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


def _create_audio_timing_element(shape_id: int, ctn_id: int) -> ET.Element:
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
    ET.SubElement(start_conditions, _qn(PML_NS, "cond"), {"delay": "0"})
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


def inject_narration(
    slide_xml: str,
    *,
    shape_id: int,
    shape_name: str,
    audio_rid: str,
    media_rid: str,
    poster_rid: str,
) -> str:
    """Inject a hidden narration media shape and slide-entry autoplay timing."""
    if isinstance(shape_id, bool) or not isinstance(shape_id, int) or shape_id <= 0:
        raise ValueError("narration shape_id must be a positive integer")
    if shape_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError(
            "narration shape_id exceeds the OOXML unsigned-integer limit: "
            f"{shape_id}"
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
    timing_ids = _numeric_ids(root.iter(_qn(PML_NS, "cTn")), "timing node")
    next_timing_id = max(timing_ids, default=0) + 1
    if next_timing_id > MAX_OOXML_UNSIGNED_INT:
        raise ValueError("narration source has no available timing node identifiers")

    root_timings = [child for child in root if child.tag == _qn(PML_NS, "timing")]
    all_timings = list(root.iter(_qn(PML_NS, "timing")))
    if len(all_timings) != len(root_timings):
        raise ValueError(
            "narration source contains non-root p:timing; only direct p:sld/p:timing "
            "can be merged safely"
        )
    if len(root_timings) > 1:
        raise ValueError(
            f"narration source has multiple root p:timing elements: {len(root_timings)}"
        )
    if not root_timings and next_timing_id + 1 > MAX_OOXML_UNSIGNED_INT:
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

    if root_timings:
        _validate_root_timing_position(root, root_timings[0])
        timing_root = _existing_timing_root(root_timings[0])
        child_nodes = _direct_child(
            timing_root,
            _qn(PML_NS, "childTnLst"),
            "tmRoot/p:childTnLst",
        )
        child_nodes.append(_create_audio_timing_element(shape_id, next_timing_id))
    else:
        audio_timing = _create_audio_timing_element(shape_id, next_timing_id + 1)
        _insert_root_timing(root, _new_timing(audio_timing, next_timing_id))

    return serialize_source_xml(root, slide_xml).decode("utf-8")


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
