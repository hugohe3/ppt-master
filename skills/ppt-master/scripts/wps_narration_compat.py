#!/usr/bin/env python3
"""
PPT Master - WPS Narration Compatibility Post-Processor

Convert an already-exported narrated PPTX (PowerPoint-recorded-narration
serialization) into a WPS-compatible copy whose narration auto-plays on
slide entry, before all other effects.

PowerPoint plays a narration stored only as a trailing ``p:audio`` media node
plus the ``ppaction://media`` shape action. WPS does not recognize that
implicit trigger; it needs an explicit ``mediacall`` playFrom(0.0) effect as
the FIRST row inside the main sequence's delay=0 container par. This tool
rewrites each narrated slide's ``p:timing`` into exactly that verified shape
and leaves every other package part byte-identical.

Usage:
    python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx>
    python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx> -o out.pptx
    python3 skills/ppt-master/scripts/wps_narration_compat.py <narrated.pptx> --overwrite

Examples:
    python3 skills/ppt-master/scripts/wps_narration_compat.py \
        projects/example/exports/deck_20260807_120000_narrated.pptx
    # writes projects/example/exports/deck_20260807_120000_narrated-wps.pptx

Dependencies:
    None (standard library only). ffprobe is not required; audio durations
    and slide auto-advance timings are already baked into the input file.

See workflows/generate-pptx.md Stage 1 (WPS compatibility outcome) and
scripts/docs/wps-narration-compat.md.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWINGML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = f"{{{PML_NS}}}"

DEFAULT_SUFFIX = "-wps"

for _prefix, _uri in (
    ("p", PML_NS),
    ("a", DRAWINGML_NS),
):
    try:
        ET.register_namespace(_prefix, _uri)
    except (AttributeError, ValueError):
        pass


def _qn(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def _first_child(parent: ET.Element, tag: str) -> ET.Element | None:
    for child in parent:
        if child.tag == tag:
            return child
    return None


def _direct_children(parent: ET.Element, tag: str) -> list[ET.Element]:
    return [child for child in parent if child.tag == tag]


def _plain_zero_delay(time_node: ET.Element) -> bool:
    """True when a time node starts at delay=0 without a begin event."""
    conditions = _first_child(time_node, _qn(PML_NS, "stCondLst"))
    if conditions is None:
        return False
    return any(
        cond.get("delay") == "0" and cond.get("evt") is None
        for cond in conditions
        if cond.tag == _qn(PML_NS, "cond")
    )


def _row_container(
    mainseq: ET.Element,
) -> tuple[ET.Element | None, list[ET.Element], ET.Element | None]:
    """Locate the main sequence's effect-row container and the sibling pars
    that must move inside it for the WPS-autoplay tree shape.

    Walks wrapper pars (the onBegin anchor, then each plain delay=0 wrapper)
    and returns the ``p:childTnLst`` that directly holds the effect rows, the
    sibling row pars found at the same level as a reusable delay=0 container,
    and the ``p:childTnLst`` that currently owns those siblings. Returns
    ``(None, [], None)`` when the sequence has no rows.
    """
    current = _first_child(mainseq, _qn(PML_NS, "childTnLst"))
    for _ in range(4):
        if current is None:
            return None, [], None
        pars = _direct_children(current, _qn(PML_NS, "par"))
        if not pars:
            return None, [], None
        first_ctn = _first_child(pars[0], _qn(PML_NS, "cTn"))
        if first_ctn is None:
            return None, [], None
        if first_ctn.get("presetClass") is not None:
            return current, pars, None
        inner = _direct_children(first_ctn, _qn(PML_NS, "childTnLst"))
        if _plain_zero_delay(first_ctn) and len(inner) == 1:
            return inner[0], pars[1:], current
        if len(inner) == 1 and _direct_children(inner[0], _qn(PML_NS, "par")):
            current = inner[0]
            continue
        return current, pars, None
    return None, [], None


def _media_call_row(shape_id: str, media_id: int, cmd_id: int) -> ET.Element:
    """WPS-compatible narration autoplay row: mediacall playFrom(0.0)."""
    row = ET.Element(_qn(PML_NS, "par"))
    time_node = ET.SubElement(
        row,
        _qn(PML_NS, "cTn"),
        {
            "id": str(media_id),
            "presetID": "1",
            "presetClass": "mediacall",
            "presetSubtype": "0",
            "fill": "hold",
            "nodeType": "afterEffect",
        },
    )
    start_conditions = ET.SubElement(time_node, _qn(PML_NS, "stCondLst"))
    ET.SubElement(start_conditions, _qn(PML_NS, "cond"), {"delay": "0"})
    child_nodes = ET.SubElement(time_node, _qn(PML_NS, "childTnLst"))
    command = ET.SubElement(
        child_nodes,
        _qn(PML_NS, "cmd"),
        {"type": "call", "cmd": "playFrom(0.0)"},
    )
    behavior = ET.SubElement(command, _qn(PML_NS, "cBhvr"), {"additive": "base"})
    ET.SubElement(
        behavior,
        _qn(PML_NS, "cTn"),
        {"id": str(cmd_id), "dur": "indefinite", "fill": "hold"},
    )
    target = ET.SubElement(behavior, _qn(PML_NS, "tgtEl"))
    ET.SubElement(target, _qn(PML_NS, "spTgt"), {"spid": shape_id})
    return row


def _audio_shape_id(timing: ET.Element) -> str | None:
    audio = timing.find(f".//{P}audio")
    if audio is None:
        return None
    spid = audio.find(f"{P}cMediaNode/{P}tgtEl/{P}spTgt")
    return spid.get("spid") if spid is not None else None


def _timing_max_id(timing: ET.Element) -> int:
    ids = [
        int(node.get("id"))
        for node in timing.iter(_qn(PML_NS, "cTn"))
        if node.get("id")
    ]
    return max(ids, default=0)


def _already_patched(mainseq: ET.Element) -> bool:
    container, _, _ = _row_container(mainseq)
    if container is None:
        return False
    for row in _direct_children(container, _qn(PML_NS, "par")):
        ctn = _first_child(row, _qn(PML_NS, "cTn"))
        if ctn is not None and ctn.get("presetClass") == "mediacall":
            return True
    return False


def _insert_wps_autoplay(mainseq: ET.Element, shape_id: str, next_id: int) -> int:
    """Restructure the main sequence into the WPS narration shape and insert
    the mediacall row as its first row. ``next_id`` must exceed every cTn id
    in the slide's whole timing tree. Returns the number of new timing nodes
    added (0 when the tree already carries the mediacall row)."""
    container, moved_pars, source = _row_container(mainseq)
    if container is None:
        return 0
    if _already_patched(mainseq):
        return 0
    if source is not None:
        for row in moved_pars:
            source.remove(row)
            container.append(row)
    container.insert(
        0,
        _media_call_row(shape_id, next_id, next_id + 1),
    )
    return 2


def _synthesize_main_sequence(
    timing: ET.Element,
    shape_id: str,
) -> int:
    """Build a main sequence (seq + mainSeq + delay=0 container + mediacall
    row) into a timing tree that only holds the trailing audio node."""
    root_ctn = next(
        (
            node
            for node in timing.iter(_qn(PML_NS, "cTn"))
            if node.get("nodeType") == "tmRoot"
        ),
        None,
    )
    if root_ctn is None:
        return 0
    root_id = _timing_max_id(timing)
    mainseq_id = root_id + 1
    container_id = root_id + 2
    media_id = root_id + 3
    cmd_id = root_id + 4

    child_nodes = _first_child(root_ctn, _qn(PML_NS, "childTnLst"))
    if child_nodes is None:
        return 0
    sequence = ET.SubElement(
        child_nodes,
        _qn(PML_NS, "seq"),
        {"concurrent": "1", "nextAc": "seek"},
    )
    mainseq = ET.SubElement(
        sequence,
        _qn(PML_NS, "cTn"),
        {"id": str(mainseq_id), "dur": "indefinite", "nodeType": "mainSeq"},
    )
    main_rows = ET.SubElement(mainseq, _qn(PML_NS, "childTnLst"))
    container = ET.SubElement(main_rows, _qn(PML_NS, "par"))
    container_ctn = ET.SubElement(
        container,
        _qn(PML_NS, "cTn"),
        {"id": str(container_id), "fill": "hold"},
    )
    container_conditions = ET.SubElement(container_ctn, _qn(PML_NS, "stCondLst"))
    ET.SubElement(container_conditions, _qn(PML_NS, "cond"), {"delay": "0"})
    container_rows = ET.SubElement(container_ctn, _qn(PML_NS, "childTnLst"))
    container_rows.append(_media_call_row(shape_id, media_id, cmd_id))
    for cond_name, event in (("prevCondLst", "onPrev"), ("nextCondLst", "onNext")):
        conds = ET.SubElement(sequence, _qn(PML_NS, cond_name))
        condition = ET.SubElement(
            conds,
            _qn(PML_NS, "cond"),
            {"evt": event, "delay": "0"},
        )
        target = ET.SubElement(condition, _qn(PML_NS, "tgtEl"))
        ET.SubElement(target, _qn(PML_NS, "sldTgt"))
    # keep the trailing audio node last, after the new sequence
    audio = timing.find(f".//{P}audio")
    if audio is not None:
        child_nodes.remove(audio)
        child_nodes.append(audio)
    return 4


def _patch_slide(xml_bytes: bytes) -> tuple[bytes | None, str]:
    root = ET.fromstring(xml_bytes)
    for key, value in root.attrib.items():
        if key.startswith("xmlns"):
            prefix = key.split(":", 1)[1] if ":" in key else ""
            ET.register_namespace(prefix, value)
    timing = root.find(f".//{P}timing")
    if timing is None:
        return None, "no-timing"
    shape_id = _audio_shape_id(timing)
    if shape_id is None:
        return None, "no-narration"
    mainseq = next(
        (
            node
            for node in timing.iter(_qn(PML_NS, "cTn"))
            if node.get("nodeType") == "mainSeq"
        ),
        None,
    )
    if mainseq is None:
        added = _synthesize_main_sequence(timing, shape_id)
        status = f"synthesized ({added} nodes)" if added else "skip-no-mainseq"
    else:
        added = _insert_wps_autoplay(
            mainseq,
            shape_id,
            _timing_max_id(timing) + 1,
        )
        status = (
            "already-patched"
            if added == 0
            else f"patched ({added} nodes, spid={shape_id})"
        )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), status


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(input_path.stem + DEFAULT_SUFFIX + input_path.suffix)


def convert(input_path: Path, output_path: Path) -> dict[int, str]:
    """Rewrite every narrated slide of ``input_path`` into ``output_path``.

    Returns a mapping of slide number to per-slide status. Package parts
    without narration are copied byte-identically.
    """
    with zipfile.ZipFile(input_path) as source:
        names = source.namelist()
        items = {name: source.read(name) for name in names}
    changed: dict[str, bytes] = {}
    slide_status: dict[int, str] = {}
    for index in range(1, len(names) + 1):
        name = f"ppt/slides/slide{index}.xml"
        if name not in items:
            continue
        new_xml, status = _patch_slide(items[name])
        if new_xml is not None:
            changed[name] = new_xml
            slide_status[index] = status
    if not changed:
        raise ValueError(
            f"no narrated slide found in {input_path}; the deck has no "
            "embedded narration audio"
        )
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as target:
        for name in names:
            target.writestr(name, changed.get(name, items[name]))
    return slide_status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wps_narration_compat.py",
        description=(
            "Convert an exported narrated PPTX into a WPS-compatible copy "
            "whose narration auto-plays first on every narrated slide."
        ),
    )
    parser.add_argument("pptx", type=Path, help="Exported narrated PPTX file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            f"Output path; defaults to the input name with a "
            f'"{DEFAULT_SUFFIX}" suffix in the same directory'
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output file",
    )
    args = parser.parse_args(argv)

    if not args.pptx.is_file():
        print(f"Error: input file not found: {args.pptx}", file=sys.stderr)
        return 1
    if args.pptx.suffix.lower() != ".pptx":
        print(
            f"Error: input must be a .pptx file: {args.pptx}",
            file=sys.stderr,
        )
        return 1
    output_path = args.output or _default_output_path(args.pptx)
    if output_path == args.pptx:
        print(
            "Error: output path must differ from the input file",
            file=sys.stderr,
        )
        return 1
    if output_path.exists() and not args.overwrite:
        print(
            f"Error: output file already exists: {output_path} "
            f"(use --overwrite to replace)",
            file=sys.stderr,
        )
        return 1

    try:
        statuses = convert(args.pptx, output_path)
    except (ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for slide_num, status in sorted(statuses.items()):
        print(f"  slide{slide_num}: {status}")
    print(
        f"wrote {output_path} "
        f"({len(statuses)} narrated slide(s) processed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
