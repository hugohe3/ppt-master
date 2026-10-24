#!/usr/bin/env python3
"""
PPT Master - Imported Chart Data Patching

Patch classic-chart caches and their embedded workbook without serializing the
surrounding chart XML. See scripts/docs/conversion.md for the round-trip rule.

Usage:
    Import patch_chart_package from the round-trip materializer.

Examples:
    package = patch_chart_package(source_package, baseline, edited)

Dependencies:
    Standard library and sibling native chart helpers.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import math
import posixpath
import re
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET
from xml.parsers import expat
from xml.sax.saxutils import escape
from zipfile import BadZipFile, ZipFile

from .chart_data import validate_chart_payload


NS = {
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
_START_TAG_RE = re.compile(rb'''<([^\s/>]+)(?:[^>"']|"[^"]*"|'[^']*')*>''')
_RANGE_RE = re.compile(r"(?:'((?:[^']|'')+)'|([^!]+))!\$?([A-Z]+)\$?([1-9][0-9]*)"
                       r"(?::\$?([A-Z]+)\$?([1-9][0-9]*))?")


@dataclass
class _Span:
    start: int
    start_end: int
    close: int
    end: int
    name: bytes
    empty: bool


class _XmlPatch:
    """Address parsed elements while retaining all untouched source bytes."""

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.root = ET.fromstring(data)
        self.edits: list[tuple[int, int, bytes]] = []
        spans: list[_Span] = []
        stack: list[_Span] = []
        parser = expat.ParserCreate()

        def start(_name, _attributes):
            offset = parser.CurrentByteIndex
            match = _START_TAG_RE.match(data, offset)
            if match is None:
                raise RuntimeError("Cannot locate source XML start tag")
            empty = match.group().endswith(b"/>")
            span = _Span(offset, match.end(), match.end() - 2, match.end(), match[1], empty)
            spans.append(span)
            stack.append(span)

        def end(_name):
            span = stack.pop()
            if not span.empty:
                span.close = parser.CurrentByteIndex
                span.end = data.index(b">", span.close) + 1

        parser.StartElementHandler = start
        parser.EndElementHandler = end
        parser.Parse(data, True)
        self.spans = dict(zip(self.root.iter(), spans))

    def replace(self, node: ET.Element, data: bytes) -> None:
        span = self.spans[node]
        self.edits.append((span.start, span.end, data))

    def text(self, node: ET.Element, value: Any) -> None:
        data = escape(str(value), {"\r": "&#13;"}).encode("utf-8")
        span = self.spans[node]
        if span.empty:
            self.replace(node, self.data[span.start:span.close] + b">" + data + b"</" + span.name + b">")
        else:
            self.edits.append((span.start_end, span.close, data))

    def attributes(self, node: ET.Element, values: dict[str, str | None]) -> None:
        span = self.spans[node]
        start = self.data[span.start:span.start_end]
        for key, value in values.items():
            pattern = re.compile(rb"\s+" + re.escape(key.encode()) + rb'''\s*=\s*(?:"[^"]*"|'[^']*')''')
            replacement = b"" if value is None else (
                b" " + key.encode() + b'="' + escape(value, {'"': "&quot;"}).encode("utf-8") + b'"'
            )
            if pattern.search(start):
                start = pattern.sub(lambda _match: replacement, start, count=1)
            elif value is not None:
                offset = -2 if span.empty else -1
                start = start[:offset] + replacement + start[offset:]
        self.edits.append((span.start, span.start_end, start))

    def append(self, node: ET.Element, data: bytes) -> None:
        span = self.spans[node]
        if span.empty:
            self.replace(node, self.data[span.start:span.close] + b">" + data + b"</" + span.name + b">")
        else:
            self.edits.append((span.close, span.close, data))

    def render(self) -> bytes:
        result: list[bytes] = []
        cursor = 0
        for start, end, data in sorted(self.edits, key=lambda edit: (edit[0], edit[1])):
            if start < cursor:
                raise RuntimeError("Overlapping chart XML data edits")
            result.extend((self.data[cursor:start], data))
            cursor = end
        result.append(self.data[cursor:])
        patched = b"".join(result)
        ET.fromstring(patched)
        return patched


def _data_shape(payload: dict[str, Any]) -> dict[str, Any]:
    """Mask only data leaves, retaining field presence, counts and all options."""
    result = copy.deepcopy(payload)
    for plot in [result, *result.get("plots", [])]:
        if isinstance(plot.get("categories"), list):
            plot["categories"] = [None] * len(plot["categories"])
        for series in plot.get("series", []):
            if "name" in series:
                series["name"] = None
            for key in ("values", "x", "y", "sizes"):
                if isinstance(series.get(key), list):
                    series[key] = [None] * len(series[key])
    return result


def chart_edit_is_data_only(baseline: dict[str, Any], edited: dict[str, Any]) -> bool:
    """Require the same plot/series topology and every non-data JSON field."""
    for plot in [edited, *edited.get("plots", [])]:
        for series in plot.get("series", []):
            if not isinstance(series.get("name", ""), str):
                return False
            for key in ("values", "x", "y", "sizes"):
                if any(value is not None and (type(value) not in {int, float} or not math.isfinite(value))
                       for value in series.get(key, [])):
                    return False
    return baseline != edited and _data_shape(baseline) == _data_shape(edited)


def _range_cells(formula: str) -> tuple[str, list[str]]:
    match = _RANGE_RE.fullmatch(formula)
    if match is None:
        raise RuntimeError(f"Cannot patch chart workbook range {formula!r}; use a single A1 row or column range")
    quoted, plain, col, row, last_col, last_row = match.groups()
    sheet = quoted.replace("''", "'") if quoted is not None else plain
    last_col, last_row = last_col or col, last_row or row

    def number(label):
        value = 0
        for char in label:
            value = value * 26 + ord(char) - ord("A") + 1
        return value

    def label(value):
        result = ""
        while value:
            value, digit = divmod(value - 1, 26)
            result = chr(ord("A") + digit) + result
        return result

    c1, c2, r1, r2 = number(col), number(last_col), int(row), int(last_row)
    if c2 < c1 or r2 < r1 or (c1 != c2 and r1 != r2):
        raise RuntimeError(f"Cannot patch non-linear chart workbook range {formula!r}")
    if c2 > 16384 or r2 > 1048576 or max(c2 - c1, r2 - r1) > 1_000_000:
        raise RuntimeError(f"Chart workbook range exceeds worksheet bounds: {formula!r}")
    return sheet, [f"{label(c)}{r}" for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]


def _patch_cache(
    xml: _XmlPatch, owner: ET.Element, before: list, after: list,
    cells: dict[tuple[str, str], Any],
) -> None:
    cache = next((node for node in owner.iter() if node.tag in {
        f'{{{NS["c"]}}}{name}' for name in ("strCache", "numCache", "strLit", "numLit")
    }), None)
    if cache is None:
        raise RuntimeError("Imported chart has no patchable data cache; reimport a chart with cached values")
    formula = owner.find(".//c:f", NS)
    if formula is not None:
        sheet, addresses = _range_cells(formula.text or "")
        if len(addresses) != len(after):
            raise RuntimeError("Chart cache count differs from its workbook range; repair the source chart")
        for address, old, value in zip(addresses, before, after):
            key = (sheet, address)
            if key in cells and cells[key][1] != value:
                raise RuntimeError(f"Conflicting chart data for workbook cell {sheet}!{address}")
            cells[key] = (old, value)
    if before == after:
        return
    if cache.tag in {f'{{{NS["c"]}}}numCache', f'{{{NS["c"]}}}numLit'}:
        try:
            valid = all(value is None or math.isfinite(float(value)) for value in after)
        except (ValueError, TypeError, OverflowError):
            valid = False
        if not valid:
            raise RuntimeError("Source chart uses a numeric cache; retain numeric category labels")
    count = cache.find("c:ptCount", NS)
    if count is None:
        raise RuntimeError("Imported chart cache has no ptCount; repair the source chart")
    if count.get("val") != str(len(after)):
        xml.attributes(count, {"val": str(len(after))})
    points = {int(node.get("idx", "-1")): node for node in cache.findall("c:pt", NS)}
    prefix = xml.spans[cache].name.rsplit(b":", 1)[0] + b":" if b":" in xml.spans[cache].name else b""
    additions: dict[int, list[bytes]] = {}
    for index, (old, value) in enumerate(zip(before, after)):
        if old == value:
            continue
        point = points.get(index)
        if value is None:
            if point is not None:
                xml.replace(point, b"")
        elif point is not None:
            leaf = point.find("c:v", NS)
            if leaf is None:
                raise RuntimeError("Imported chart point has no value; repair the source chart")
            xml.text(leaf, value)
        else:
            tag = prefix.decode()
            following = [xml.spans[node].start for idx, node in points.items() if idx > index]
            anchor = min(following) if following else max(
                (xml.spans[node].end for node in points.values()), default=xml.spans[count].end,
            )
            additions.setdefault(anchor, []).append(
                f'<{tag}pt idx="{index}"><{tag}v>{escape(str(value))}</{tag}v></{tag}pt>'.encode("utf-8")
            )
    for anchor, fragments in additions.items():
        xml.edits.append((anchor, anchor, b"".join(fragments)))


def _patch_chart(data: bytes, baseline: dict, edited: dict) -> tuple[bytes, dict]:
    xml = _XmlPatch(data)
    plot_area = xml.root.find("c:chart/c:plotArea", NS)
    plots = [node for node in plot_area if node.find("c:ser", NS) is not None] if plot_area is not None else []
    old_plots, new_plots = baseline.get("plots", [baseline]), edited.get("plots", [edited])
    if len(plots) != len(new_plots):
        raise RuntimeError("Source chart plots do not match the import baseline; reimport the source deck")
    cells: dict[tuple[str, str], Any] = {}
    for plot, old_plot, new_plot in zip(plots, old_plots, new_plots):
        series = plot.findall("c:ser", NS)
        if len(series) != len(new_plot["series"]):
            raise RuntimeError("Source chart series do not match the import baseline; reimport the source deck")
        for node, old, new in zip(series, old_plot["series"], new_plot["series"]):
            for key, tag in (("values", "val"), ("x", "xVal"), ("y", "yVal"), ("sizes", "bubbleSize")):
                if key in new:
                    owner = node.find(f"c:{tag}", NS)
                    if owner is None:
                        raise RuntimeError(f"Source chart lacks c:{tag}; reimport the source deck")
                    _patch_cache(xml, owner, old[key], new[key], cells)
            if "categories" in edited:
                owner = node.find("c:cat", NS)
                if owner is None:
                    raise RuntimeError("Source chart lacks categories; reimport the source deck")
                _patch_cache(xml, owner, old_plot.get("categories", baseline["categories"]),
                             new_plot.get("categories", edited["categories"]), cells)
            tx = node.find("c:tx", NS)
            if tx is not None and tx.find("c:strRef", NS) is not None:
                _patch_cache(xml, tx, [old["name"]], [new["name"]], cells)
            elif old.get("name") != new.get("name"):
                leaf = tx.find("c:v", NS) if tx is not None else None
                if leaf is None:
                    name = xml.spans[node].name.decode()
                    prefix = name.rsplit(":", 1)[0] + ":" if ":" in name else ""
                    value = escape(new["name"], {"\r": "&#13;"})
                    content = f"<{prefix}v>{value}</{prefix}v>".encode("utf-8")
                    if tx is not None:
                        xml.append(tx, content)
                    else:
                        order = node.find("c:order", NS)
                        if order is None:
                            raise RuntimeError("Source chart series has no order; repair the source chart")
                        anchor = xml.spans[order].end
                        content = f"<{prefix}tx>".encode() + content + f"</{prefix}tx>".encode()
                        xml.edits.append((anchor, anchor, content))
                else:
                    xml.text(leaf, new["name"])
    return xml.render(), cells


def _resolve(owner: str, target: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(owner), target)).lstrip("/")


def _patch_workbook(data: bytes, assignments: dict[tuple[str, str], Any]) -> bytes:
    with ZipFile(io.BytesIO(data)) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
        workbook = ET.fromstring(parts["xl/workbook.xml"])
        relationships = ET.fromstring(parts["xl/_rels/workbook.xml.rels"])
        targets = {rel.get("Id"): _resolve("xl/workbook.xml", rel.get("Target", "")) for rel in relationships}
        sheets = {sheet.get("name"): targets[sheet.get(f'{{{NS["r"]}}}id')]
                  for sheet in workbook.findall("s:sheets/s:sheet", NS)}
        strings_part = next((targets[rel.get("Id")] for rel in relationships
                             if rel.get("Type", "").endswith("/sharedStrings")), None)
        strings = _XmlPatch(parts[strings_part]) if strings_part else None
        string_values = ["".join(text.text or "" for text in node.findall("s:t", NS) + node.findall("s:r/s:t", NS))
                         for node in strings.root.findall("s:si", NS)] if strings else []
        string_indices = {value: index for index, value in enumerate(string_values)}
        additions: list[bytes] = []
        sheets_xml = {name: _XmlPatch(parts[part]) for name, part in sheets.items()}
        shared_count = sum(node.get("t") == "s" for xml in sheets_xml.values() for node in xml.root.iter())
        old_shared_count = shared_count
        for (sheet, address), (before, value) in assignments.items():
            if before == value:
                continue
            if sheet not in sheets_xml:
                raise RuntimeError(f"Chart workbook sheet {sheet!r} is missing")
            xml = sheets_xml[sheet]
            node = next((cell for cell in xml.root.findall("s:sheetData/s:row/s:c", NS)
                         if cell.get("r") == address), None)
            leaf = node.find("s:v", NS) if node is not None else None
            kind = node.get("t") if node is not None else None
            old_value = leaf.text if leaf is not None else None
            if kind == "s" and old_value is not None:
                old_value = string_values[int(old_value)]
            elif kind == "inlineStr":
                old_value = "".join(node.find("s:is", NS).itertext())
            if old_value == value or (kind in {None, "n"} and old_value is not None
                                     and isinstance(value, (int, float)) and float(old_value) == value):
                continue
            if node is not None and node.find("s:f", NS) is not None:
                raise RuntimeError(f"Chart workbook cell {sheet}!{address} is a formula; edit its source inputs")
            # A fresh cell body preserves style/extension attributes and avoids shared-string alias edits.
            cell = copy.deepcopy(node) if node is not None else ET.Element(f'{{{NS["s"]}}}c', {"r": address})
            cell.tail = None
            for child in list(cell):
                if child.tag in {f'{{{NS["s"]}}}{tag}' for tag in ("v", "is")}:
                    cell.remove(child)
            cell.attrib.pop("t", None)
            if isinstance(value, str):
                if strings is not None:
                    if value not in string_indices:
                        string_indices[value] = len(string_values) + len(additions)
                        tag = strings.spans[strings.root].name.decode().rsplit(":", 1)
                        prefix = tag[0] + ":" if len(tag) == 2 else ""
                        text_value = escape(value, {"\r": "&#13;"})
                        additions.append((f'<{prefix}si><{prefix}t xml:space="preserve">'
                                          f'{text_value}</{prefix}t></{prefix}si>').encode("utf-8"))
                    cell.set("t", "s")
                    content = ET.Element(f'{{{NS["s"]}}}v')
                    content.text = str(string_indices[value])
                    cell.insert(0, content)
                else:
                    cell.set("t", "inlineStr")
                    content = ET.Element(f'{{{NS["s"]}}}is')
                    text = ET.SubElement(content, f'{{{NS["s"]}}}t')
                    text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    text.text = value
                    cell.insert(0, content)
            elif value is not None:
                content = ET.Element(f'{{{NS["s"]}}}v')
                content.text = str(value)
                cell.insert(0, content)
            shared_count += int(cell.get("t") == "s") - int(kind == "s")
            replacement = ET.tostring(cell, encoding="utf-8")
            if node is not None:
                xml.replace(node, replacement)
            else:
                row_num = re.search(r"[0-9]+$", address).group()
                row = next((row for row in xml.root.findall("s:sheetData/s:row", NS)
                            if row.get("r") == row_num), None)
                if row is None:
                    raise RuntimeError(f"Chart workbook row {sheet}!{row_num} is missing; repair the source workbook")
                column = re.match(r"[A-Z]+", address).group()
                following = [cell for cell in row.findall("s:c", NS)
                             if (len(re.match(r"[A-Z]+", cell.get("r")).group()),
                                 re.match(r"[A-Z]+", cell.get("r")).group()) > (len(column), column)]
                if following:
                    anchor = xml.spans[following[0]].start
                    xml.edits.append((anchor, anchor, replacement))
                else:
                    xml.append(row, replacement)
        if not any(xml.edits for xml in sheets_xml.values()):
            return data
        for sheet, xml in sheets_xml.items():
            if xml.edits:
                parts[sheets[sheet]] = xml.render()
        if strings is not None and (additions or shared_count != old_shared_count):
            strings.attributes(strings.root, {"count": str(shared_count),
                                              "uniqueCount": str(len(string_values) + len(additions))})
            if additions:
                strings.append(strings.root, b"".join(additions))
            parts[strings_part] = strings.render()
        output = io.BytesIO()
        with ZipFile(output, "w") as result:
            for info in archive.infolist():
                result.writestr(info, parts[info.filename])
            result.comment = archive.comment
        return output.getvalue()


def patch_chart_package(source: dict, baseline: dict, edited: dict) -> dict:
    """Clone a validated source graph and patch only data in its chart/workbook."""
    from . import _decode_source_chart_package

    validate_chart_payload(edited)
    decoded = _decode_source_chart_package({"source_package": source})
    if decoded is None:
        raise RuntimeError("Imported chart has no source package; reimport the source deck")
    chart_part, _frame, parts, _types = decoded
    parts[chart_part], cells = _patch_chart(parts[chart_part], baseline, edited)
    chart_root = ET.fromstring(parts[chart_part])
    external = chart_root.find("c:externalData", NS)
    if cells and external is not None:
        rels_name = posixpath.join(posixpath.dirname(chart_part), "_rels", posixpath.basename(chart_part) + ".rels")
        rels = ET.fromstring(parts[rels_name])
        rel = next((rel for rel in rels if rel.get("Id") == external.get(f'{{{NS["r"]}}}id')), None)
        if rel is None:
            raise RuntimeError("Chart workbook relationship is missing; repair the source chart")
        workbook_part = _resolve(chart_part, rel.get("Target", ""))
        try:
            parts[workbook_part] = _patch_workbook(parts[workbook_part], cells)
        except (BadZipFile, KeyError, ValueError, ET.ParseError) as exc:
            raise RuntimeError(f"Cannot patch embedded chart workbook: {exc}; repair the source workbook") from exc

    # Content-addressed copies keep other pages sharing the source graph immutable.
    digest = hashlib.sha256()
    for name, data in sorted(parts.items()):
        digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    suffix = "_data_" + digest.hexdigest()[:20]
    names = {name: posixpath.splitext(name)[0] + suffix + posixpath.splitext(name)[1]
             for name in parts if not name.endswith(".rels")}
    for name in parts:
        if not name.endswith(".rels"):
            continue
        parent, leaf = name.split("/_rels/", 1)
        owner = parent + "/" + leaf[:-5]
        new_owner = names[owner]
        names[name] = posixpath.join(posixpath.dirname(new_owner), "_rels", posixpath.basename(new_owner) + ".rels")
        rels = _XmlPatch(parts[name])
        for rel in rels.root:
            target = names[_resolve(owner, rel.get("Target", ""))]
            rels.attributes(rel, {"Target": posixpath.relpath(target, posixpath.dirname(new_owner))})
        parts[name] = rels.render()
    result = copy.deepcopy(source)
    result["chart_part"] = names[chart_part]
    for item in result["parts"]:
        data = parts[item["name"]]
        item.update(name=names[item["name"]], payload=base64.b64encode(data).decode("ascii"),
                    sha256=hashlib.sha256(data).hexdigest())
    return result
