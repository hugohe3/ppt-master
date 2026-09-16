#!/usr/bin/env python3
"""PPT Master - Custom Show Reference Validation

Check custom-show selections and actions against the presentation roster.
Usage: Imported by the page-plan cloner and delivery checker.
Examples: custom_show_problems(entries)
Dependencies: Standard library only.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

from .ooxml import NS, _normalize_part, _xml_bytes


def reset_slide_show_selection(entries: dict[str, bytes]) -> None:
    """Select all output slides after dropping source show/range rosters."""
    relationships = ET.fromstring(entries['ppt/_rels/presentation.xml.rels'])
    for rel in relationships:
        if not rel.get('Type', '').endswith('/presProps'):
            continue
        name = _normalize_part(rel.get('Target', ''), 'ppt/presentation.xml')
        root = ET.fromstring(entries[name])
        changed = False
        for show in root.findall('p:showPr', NS):
            for child in list(show):
                if child.tag in {f'{{{NS["p"]}}}custShow', f'{{{NS["p"]}}}sldRg'}:
                    show.remove(child)
                    changed = True
            if changed and show.find('p:sldAll', NS) is None:
                # CT_ShowProperties places the slide-selection choice after
                # the present/browse/kiosk choice and before pen/extLst.
                index = int(bool(list(show)) and list(show)[0].tag in {
                    f'{{{NS["p"]}}}{kind}' for kind in ('present', 'browse', 'kiosk')
                })
                show.insert(index, ET.Element(f'{{{NS["p"]}}}sldAll'))
        if changed:
            entries[name] = _xml_bytes(root)


def custom_show_problems(entries: dict[str, bytes]) -> list[str]:
    """Return dangling custom-show selections/actions, including their owner."""
    presentation = entries.get('ppt/presentation.xml')
    if presentation is None:
        return []
    try:
        root = ET.fromstring(presentation)
    except ET.ParseError:
        return []
    show_ids = {show.get('id') for show in root.findall('p:custShowLst/p:custShow', NS) if show.get('id')}
    problems = []
    for part, payload in sorted(entries.items()):
        if not part.endswith('.xml'):
            continue
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            continue
        for node in root.iter():
            action = node.get('action', '')
            if action.startswith('ppaction://customshow'):
                parsed = urlsplit(action)
                if parsed.netloc != 'customshow':
                    continue
                ids = parse_qs(parsed.query).get('id', [])
                show_id = ids[0] if len(ids) == 1 else None
                if show_id not in show_ids:
                    problems.append(f'{part}: custom-show action references missing show id {show_id!r}')
        for node in root.findall('p:showPr/p:custShow', NS):
            if node.get('id') not in show_ids:
                problems.append(f'{part}: playback selection references missing show id {node.get("id")!r}')
    return problems
