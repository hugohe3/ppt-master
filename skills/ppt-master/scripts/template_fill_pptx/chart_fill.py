"""apply: edit native PowerPoint chart data on cloned slides.

Each referenced chart part is cloned, its ``<c:ser>`` caches are rewritten from
the plan's categories / series, and the embedded ``.xlsx`` workbook is rebuilt so
PowerPoint's "Edit Data" view stays consistent. Chart styling / axes / legend
layout are left untouched.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import (
    CHART_CONTENT_TYPE,
    CHART_REL_TYPE,
    NS,
    PACKAGE_REL_TYPE,
    REL_NS,
    XLSX_CONTENT_TYPE,
    _chart_containers,
    _normalize_part,
    _qn,
    _rels_name_for_part,
    _shape_identity,
    _xml_bytes,
)
from .package import _add_content_type_override, _find_relationship, _relative_target
from .selectors import _chart_selectors


def _chart_key_maps(slide_root: ET.Element, source_slide: int) -> dict[str, dict[str, str]]:
    maps: dict[str, dict[str, str]] = {}
    for order, container in enumerate(_chart_containers(slide_root), start=1):
        shape_id, shape_name = _shape_identity(container, order)
        chart = container.find(".//c:chart", NS)
        rel_id = chart.attrib.get(_qn(NS["r"], "id")) if chart is not None else ""
        info = {"shape_id": shape_id, "shape_name": shape_name, "rel_id": rel_id or ""}
        maps[f"chart_id:s{source_slide:02d}_ch{shape_id}"] = info
        maps[f"shape_id:{shape_id}"] = info
        if shape_name:
            maps[f"shape_name:{shape_name}"] = info
    return maps


def _max_chart_part_number(entries: dict[str, bytes]) -> int:
    max_number = 0
    pattern = re.compile(r"^ppt/charts/chart(\d+)\.xml$")
    for name in entries:
        match = pattern.match(name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def _max_embedding_part_number(entries: dict[str, bytes]) -> int:
    max_number = 0
    pattern = re.compile(r"^ppt/embeddings/templateFillChart(\d+)\.xlsx$")
    for name in entries:
        match = pattern.match(name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number


def _chart_part_from_relationship(slide_part: str, rel: ET.Element) -> str:
    target = rel.attrib.get("Target", "")
    if rel.attrib.get("Type") != CHART_REL_TYPE or not target:
        raise RuntimeError("Matched chart shape does not point to a chart relationship")
    return _normalize_part(target, slide_part)


def _chart_type_with_series(chart_root: ET.Element) -> ET.Element:
    plot_area = chart_root.find(".//c:plotArea", NS)
    if plot_area is None:
        raise RuntimeError("Chart XML has no plotArea")
    for child in list(plot_area):
        if child.tag.endswith("Chart") and child.findall("c:ser", NS):
            return child
    raise RuntimeError("Chart XML has no editable series")


def _ensure_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag, NS)
    if child is not None:
        return child
    return ET.SubElement(parent, _qn(NS["c"], tag.split(":", 1)[1]))


def _set_val_attr(element: ET.Element, value: str | int | float) -> None:
    element.set("val", str(value))


def _excel_col(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result or "A"


def _write_string_cache(cache: ET.Element, values: list[str]) -> None:
    for child in list(cache):
        cache.remove(child)
    pt_count = ET.SubElement(cache, _qn(NS["c"], "ptCount"))
    _set_val_attr(pt_count, len(values))
    for index, value in enumerate(values):
        pt = ET.SubElement(cache, _qn(NS["c"], "pt"), {"idx": str(index)})
        v = ET.SubElement(pt, _qn(NS["c"], "v"))
        v.text = str(value)


def _write_number_cache(cache: ET.Element, values: list[Any]) -> None:
    for child in list(cache):
        cache.remove(child)
    fmt = ET.SubElement(cache, _qn(NS["c"], "formatCode"))
    fmt.text = "General"
    pt_count = ET.SubElement(cache, _qn(NS["c"], "ptCount"))
    _set_val_attr(pt_count, len(values))
    for index, value in enumerate(values):
        pt = ET.SubElement(cache, _qn(NS["c"], "pt"), {"idx": str(index)})
        v = ET.SubElement(pt, _qn(NS["c"], "v"))
        v.text = str(value)


def _set_series_name(series: ET.Element, name: str, column_index: int) -> None:
    tx = _ensure_child(series, "c:tx")
    for child in list(tx):
        tx.remove(child)
    str_ref = ET.SubElement(tx, _qn(NS["c"], "strRef"))
    formula = ET.SubElement(str_ref, _qn(NS["c"], "f"))
    formula.text = f"Sheet1!${_excel_col(column_index)}$1"
    cache = ET.SubElement(str_ref, _qn(NS["c"], "strCache"))
    _write_string_cache(cache, [name])


def _set_category_cache(series: ET.Element, categories: list[str]) -> None:
    cat = _ensure_child(series, "c:cat")
    for child in list(cat):
        cat.remove(child)
    str_ref = ET.SubElement(cat, _qn(NS["c"], "strRef"))
    formula = ET.SubElement(str_ref, _qn(NS["c"], "f"))
    formula.text = f"Sheet1!$A$2:$A${len(categories) + 1}"
    cache = ET.SubElement(str_ref, _qn(NS["c"], "strCache"))
    _write_string_cache(cache, [str(item) for item in categories])


def _set_value_cache(series: ET.Element, values: list[Any], column_index: int) -> None:
    val = _ensure_child(series, "c:val")
    for child in list(val):
        val.remove(child)
    num_ref = ET.SubElement(val, _qn(NS["c"], "numRef"))
    formula = ET.SubElement(num_ref, _qn(NS["c"], "f"))
    formula.text = f"Sheet1!${_excel_col(column_index)}$2:${_excel_col(column_index)}${len(values) + 1}"
    cache = ET.SubElement(num_ref, _qn(NS["c"], "numCache"))
    _write_number_cache(cache, values)


def _apply_chart_edit_to_chart_xml(chart_root: ET.Element, chart_edit: dict[str, Any]) -> None:
    categories = [str(item) for item in chart_edit.get("categories", [])]
    series_payload = chart_edit.get("series", [])
    if not categories or not isinstance(series_payload, list) or not series_payload:
        raise RuntimeError("Chart edit requires non-empty categories and series")
    chart_type = _chart_type_with_series(chart_root)
    series_nodes = chart_type.findall("c:ser", NS)
    if not series_nodes:
        raise RuntimeError("Chart XML has no editable series")
    template_series = series_nodes[-1]
    while len(series_nodes) < len(series_payload):
        clone = ET.fromstring(ET.tostring(template_series, encoding="utf-8"))
        chart_type.append(clone)
        series_nodes.append(clone)
    for extra in series_nodes[len(series_payload) :]:
        chart_type.remove(extra)
    series_nodes = chart_type.findall("c:ser", NS)
    for index, (series, payload) in enumerate(zip(series_nodes, series_payload), start=0):
        values = payload.get("values", [])
        if len(values) != len(categories):
            raise RuntimeError("Chart series values must match categories length")
        idx = _ensure_child(series, "c:idx")
        order = _ensure_child(series, "c:order")
        _set_val_attr(idx, index)
        _set_val_attr(order, index)
        _set_series_name(series, str(payload.get("name", f"系列{index + 1}")), index + 2)
        _set_category_cache(series, categories)
        _set_value_cache(series, values, index + 2)


def _spreadsheet_relationships(xlsx_entries: dict[str, bytes], part_name: str) -> dict[str, str]:
    rels_name = _rels_name_for_part(part_name)
    if rels_name not in xlsx_entries:
        return {}
    root = ET.fromstring(xlsx_entries[rels_name])
    rels: dict[str, str] = {}
    for rel in root.findall(_qn(REL_NS, "Relationship")):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target")
        if rel_id and target:
            rels[rel_id] = _normalize_part(target, part_name)
    return rels


def _first_workbook_sheet(xlsx_entries: dict[str, bytes]) -> str | None:
    workbook_part = "xl/workbook.xml"
    if workbook_part not in xlsx_entries:
        return None
    root = ET.fromstring(xlsx_entries[workbook_part])
    sheets = root.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets")
    if sheets is None:
        return None
    first = next(iter(list(sheets)), None)
    if first is None:
        return None
    rel_id = first.attrib.get(_qn(NS["r"], "id"))
    if not rel_id:
        return None
    return _spreadsheet_relationships(xlsx_entries, workbook_part).get(rel_id)


def _spreadsheet_cell_ref(row: int, col: int) -> str:
    return f"{_excel_col(col)}{row}"


def _spreadsheet_cell(value: Any, row: int, col: int) -> ET.Element:
    cell = ET.Element(
        "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c",
        {"r": _spreadsheet_cell_ref(row, col)},
    )
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = ET.SubElement(cell, "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
        v.text = str(value)
        return cell
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is")
    text = ET.SubElement(inline, "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")
    text.text = str(value)
    return cell


def _rewrite_chart_workbook(xlsx_bytes: bytes, chart_edit: dict[str, Any]) -> bytes:
    categories = chart_edit.get("categories", [])
    series_payload = chart_edit.get("series", [])
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zin:
        xlsx_entries = {info.filename: zin.read(info.filename) for info in zin.infolist() if not info.is_dir()}
    sheet_part = _first_workbook_sheet(xlsx_entries) or "xl/worksheets/sheet1.xml"
    if sheet_part not in xlsx_entries:
        return xlsx_bytes
    sheet_root = ET.fromstring(xlsx_entries[sheet_part])
    sheet_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet_data = sheet_root.find(_qn(sheet_ns, "sheetData"))
    if sheet_data is None:
        sheet_data = ET.SubElement(sheet_root, _qn(sheet_ns, "sheetData"))
    for child in list(sheet_data):
        sheet_data.remove(child)

    rows = [["Category"] + [str(item.get("name", f"系列{idx + 1}")) for idx, item in enumerate(series_payload)]]
    for row_index, category in enumerate(categories):
        rows.append([category] + [item.get("values", [])[row_index] for item in series_payload])
    for row_index, values in enumerate(rows, start=1):
        row = ET.SubElement(sheet_data, _qn(sheet_ns, "row"), {"r": str(row_index)})
        for col_index, value in enumerate(values, start=1):
            row.append(_spreadsheet_cell(value, row_index, col_index))
    xlsx_entries[sheet_part] = _xml_bytes(sheet_root)

    out_buffer = io.BytesIO()
    with zipfile.ZipFile(out_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in xlsx_entries.items():
            zout.writestr(name, data)
    return out_buffer.getvalue()


def _find_chart_workbook_rel(chart_rels_root: ET.Element) -> ET.Element | None:
    for rel in chart_rels_root.findall(_qn(REL_NS, "Relationship")):
        target = rel.attrib.get("Target", "")
        if rel.attrib.get("Type") == PACKAGE_REL_TYPE or target.lower().endswith(".xlsx"):
            return rel
    return None


def _clone_and_update_chart_part(
    entries: dict[str, bytes],
    content_root: ET.Element,
    *,
    source_chart_part: str,
    new_chart_part: str,
    chart_edit: dict[str, Any],
    next_embedding_number: int,
) -> int:
    if source_chart_part not in entries:
        raise RuntimeError(f"Missing chart part: {source_chart_part}")
    chart_root = ET.fromstring(entries[source_chart_part])
    _apply_chart_edit_to_chart_xml(chart_root, chart_edit)
    entries[new_chart_part] = _xml_bytes(chart_root)
    _add_content_type_override(content_root, new_chart_part, CHART_CONTENT_TYPE)

    source_chart_rels = _rels_name_for_part(source_chart_part)
    if source_chart_rels not in entries:
        return next_embedding_number
    new_chart_rels = _rels_name_for_part(new_chart_part)
    chart_rels_root = ET.fromstring(entries[source_chart_rels])
    workbook_rel = _find_chart_workbook_rel(chart_rels_root)
    if workbook_rel is not None:
        workbook_target = workbook_rel.attrib.get("Target", "")
        workbook_part = _normalize_part(workbook_target, source_chart_part)
        if workbook_part in entries:
            next_embedding_number += 1
            new_workbook_part = f"ppt/embeddings/templateFillChart{next_embedding_number}.xlsx"
            entries[new_workbook_part] = _rewrite_chart_workbook(entries[workbook_part], chart_edit)
            workbook_rel.set("Target", _relative_target(new_chart_part, new_workbook_part))
            _add_content_type_override(content_root, new_workbook_part, XLSX_CONTENT_TYPE)
    entries[new_chart_rels] = _xml_bytes(chart_rels_root)
    return next_embedding_number


def _apply_chart_edits_to_slide_package(
    slide_root: ET.Element,
    rels_root: ET.Element,
    entries: dict[str, bytes],
    content_root: ET.Element,
    *,
    source_slide: int,
    new_slide_part: str,
    chart_edits: list[dict[str, Any]],
    next_chart_number: int,
    next_embedding_number: int,
) -> tuple[int, int]:
    maps = _chart_key_maps(slide_root, source_slide)
    cloned_by_rel_id: dict[str, str] = {}
    errors: list[str] = []
    for chart_edit in chart_edits:
        selectors = _chart_selectors(chart_edit)
        chart_info = next((maps[key] for key in selectors if key in maps), None)
        if chart_info is None:
            if chart_edit.get("optional"):
                continue
            errors.append(", ".join(selectors) or "<missing selector>")
            continue
        rel_id = chart_info.get("rel_id", "")
        rel = _find_relationship(rels_root, rel_id)
        if rel is None:
            errors.append(f"{selectors[0] if selectors else '<chart>'} relationship={rel_id}")
            continue
        if rel_id not in cloned_by_rel_id:
            next_chart_number += 1
            source_chart_part = _chart_part_from_relationship(new_slide_part, rel)
            new_chart_part = f"ppt/charts/chart{next_chart_number}.xml"
            next_embedding_number = _clone_and_update_chart_part(
                entries,
                content_root,
                source_chart_part=source_chart_part,
                new_chart_part=new_chart_part,
                chart_edit=chart_edit,
                next_embedding_number=next_embedding_number,
            )
            rel.set("Target", _relative_target(new_slide_part, new_chart_part))
            cloned_by_rel_id[rel_id] = new_chart_part
            continue
        chart_root = ET.fromstring(entries[cloned_by_rel_id[rel_id]])
        _apply_chart_edit_to_chart_xml(chart_root, chart_edit)
        entries[cloned_by_rel_id[rel_id]] = _xml_bytes(chart_root)
    if errors:
        raise RuntimeError(f"Missing chart edit target(s) on slide {source_slide}: {'; '.join(errors)}")
    return next_chart_number, next_embedding_number
