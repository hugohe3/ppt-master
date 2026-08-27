"""Read SmartArt content and structure from DrawingML diagram parts.

The reader exposes source facts only.  It does not edit DiagramML or promise
native SmartArt regeneration; generated decks continue to redraw the extracted
content through the SVG-to-DrawingML shape pipeline.
"""

from __future__ import annotations

import zipfile
from typing import Any
from xml.etree import ElementTree as ET

from .ooxml import (
    MC_NS,
    NS,
    _container_geometry,
    _normalize_part,
    _paragraph_texts,
    _qn,
    _read_xml,
    _rels_name_for_part,
    _shape_identity,
    _slide_relationships,
)


DIAGRAM_NS = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
DIAGRAM_DRAWING_NS = "http://schemas.microsoft.com/office/drawing/2008/diagram"
DIAGRAM_URI = "http://schemas.openxmlformats.org/drawingml/2006/diagram"

_DIAGRAM_REL_SUFFIXES = {
    "colors": "diagramColors",
    "data": "diagramData",
    "layout": "diagramLayout",
    "quick_style": "diagramQuickStyle",
}
_REL_ATTRS = {
    "colors": "cs",
    "data": "dm",
    "layout": "lo",
    "quick_style": "qs",
}
_CONTENT_POINT_TYPES = {"asst", "node"}

DIAGRAM_NS_MAP = {
    **NS,
    "dgm": DIAGRAM_NS,
    "dsp": DIAGRAM_DRAWING_NS,
    "mc": MC_NS,
}


def _relationship_matches(rel_type: str, suffix: str) -> bool:
    return rel_type.rsplit("/", 1)[-1] == suffix


def _read_optional_xml(
    zf: zipfile.ZipFile,
    part_name: str | None,
) -> tuple[ET.Element | None, str | None]:
    if not part_name:
        return None, "missing-part-reference"
    try:
        return _read_xml(zf, part_name), None
    except RuntimeError:
        return None, "missing-part"
    except ET.ParseError:
        return None, "invalid-xml"


def _diagram_containers(slide_root: ET.Element) -> list[ET.Element]:
    containers: list[ET.Element] = []
    for frame in slide_root.findall(".//p:graphicFrame", DIAGRAM_NS_MAP):
        graphic_data = frame.find("a:graphic/a:graphicData", DIAGRAM_NS_MAP)
        if graphic_data is not None and graphic_data.attrib.get("uri") == DIAGRAM_URI:
            containers.append(frame)
    return containers


def _fallback_preview_shape_ids(slide_root: ET.Element) -> set[str]:
    shape_ids: set[str] = set()
    for alternate in slide_root.findall(".//mc:AlternateContent", DIAGRAM_NS_MAP):
        frame = alternate.find("mc:Choice//p:graphicFrame", DIAGRAM_NS_MAP)
        if frame is None:
            continue
        graphic_data = frame.find("a:graphic/a:graphicData", DIAGRAM_NS_MAP)
        if graphic_data is None or graphic_data.attrib.get("uri") != DIAGRAM_URI:
            continue
        if alternate.find("mc:Fallback//p:pic", DIAGRAM_NS_MAP) is None:
            continue
        shape_id, _shape_name = _shape_identity(frame, len(shape_ids) + 1)
        shape_ids.add(shape_id)
    return shape_ids


def _diagram_parts(
    rel_ids: ET.Element | None,
    relationships: dict[str, dict[str, str]],
    slide_part: str,
) -> tuple[dict[str, str], str | None]:
    if rel_ids is None:
        return {}, "missing-rel-ids"

    parts: dict[str, str] = {}
    data_error: str | None = None
    for key, attr_name in _REL_ATTRS.items():
        rel_id = rel_ids.attrib.get(_qn(NS["r"], attr_name), "")
        if not rel_id:
            if key == "data":
                data_error = "missing-data-relationship"
            continue
        relationship = relationships.get(rel_id)
        if relationship is None:
            if key == "data":
                data_error = "missing-data-relationship"
            continue
        if not _relationship_matches(
            relationship.get("type", ""),
            _DIAGRAM_REL_SUFFIXES[key],
        ):
            if key == "data":
                data_error = "invalid-data-relationship"
            continue
        parts[key] = _normalize_part(relationship["target"], slide_part)
    return parts, data_error


def _persisted_drawing_part(
    zf: zipfile.ZipFile,
    data_part: str | None,
    data_root: ET.Element | None,
    slide_part: str,
    slide_relationships: dict[str, dict[str, str]],
) -> tuple[str | None, list[str]]:
    if not data_part or data_root is None:
        return None, []
    data_model_ext = data_root.find(".//dsp:dataModelExt", DIAGRAM_NS_MAP)
    rel_id = data_model_ext.attrib.get("relId", "") if data_model_ext is not None else ""
    if not rel_id:
        return None, []

    warnings: list[str] = []
    relationship = slide_relationships.get(rel_id)
    relationship_owner = slide_part
    if relationship is not None and not _relationship_matches(
        relationship.get("type", ""),
        "diagramDrawing",
    ):
        relationship = None
    if relationship is None:
        try:
            data_relationships = _slide_relationships(zf, _rels_name_for_part(data_part))
        except ET.ParseError:
            data_relationships = {}
            warnings.append("invalid-persisted-drawing-relationships")
        relationship = data_relationships.get(rel_id)
        relationship_owner = data_part
        if relationship is not None and not _relationship_matches(
            relationship.get("type", ""),
            "diagramDrawing",
        ):
            relationship = None
    if relationship is None:
        warnings.append("unresolved-persisted-drawing-relationship")
        return None, warnings

    part_name = _normalize_part(relationship["target"], relationship_owner)
    if part_name not in zf.namelist():
        warnings.append("missing-persisted-drawing-part")
        return None, warnings
    return part_name, warnings


def _layout_info(
    layout_root: ET.Element | None,
    data_root: ET.Element | None,
) -> dict[str, Any]:
    unique_id = layout_root.attrib.get("uniqueId") if layout_root is not None else None
    if not unique_id and data_root is not None:
        document_properties = data_root.find(
            ".//dgm:pt[@type='doc']/dgm:prSet",
            DIAGRAM_NS_MAP,
        )
        if document_properties is not None:
            unique_id = document_properties.attrib.get("loTypeId")
    title = layout_root.find("dgm:title", DIAGRAM_NS_MAP) if layout_root is not None else None
    name = title.attrib.get("val") if title is not None else None
    if not name and unique_id:
        name = unique_id.rstrip("/").rsplit("/", 1)[-1]
    categories = (
        [
            category.attrib["type"]
            for category in layout_root.findall("dgm:catLst/dgm:cat", DIAGRAM_NS_MAP)
            if category.attrib.get("type")
        ]
        if layout_root is not None
        else []
    )
    return {
        "name": name,
        "unique_id": unique_id,
        "categories": categories,
    }


def _integer_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _point_text(point: ET.Element) -> str:
    text_body = point.find("dgm:t", DIAGRAM_NS_MAP)
    if text_body is None:
        return ""
    return "\n".join(_paragraph_texts(text_body)).strip()


def _connections(data_root: ET.Element) -> list[dict[str, Any]]:
    connections: list[dict[str, Any]] = []
    for connection in data_root.findall(
        ".//dgm:cxnLst/dgm:cxn",
        DIAGRAM_NS_MAP,
    ):
        source_id = connection.attrib.get("srcId", "")
        destination_id = connection.attrib.get("destId", "")
        if not source_id or not destination_id:
            continue
        connections.append(
            {
                "type": connection.attrib.get("type") or "parOf",
                "source_id": source_id,
                "destination_id": destination_id,
                "source_order": _integer_or_none(connection.attrib.get("srcOrd")),
                "destination_order": _integer_or_none(connection.attrib.get("destOrd")),
            }
        )
    return connections


def _nearest_content_parent(
    node_id: str,
    parent_by_id: dict[str, str],
    content_ids: set[str],
) -> str | None:
    current = parent_by_id.get(node_id)
    visited = {node_id}
    while current:
        if current in content_ids:
            return current
        if current in visited:
            return None
        visited.add(current)
        current = parent_by_id.get(current)
    return None


def _break_parent_cycles(
    parent_by_node: dict[str, str | None],
    source_order: dict[str, int],
) -> list[str]:
    """Break cycles in the Markdown tree projection while retaining raw connections."""
    warnings: list[str] = []
    for start_id in sorted(parent_by_node, key=lambda node_id: source_order[node_id]):
        path: list[str] = []
        path_index: dict[str, int] = {}
        current_id: str | None = start_id
        while current_id is not None and current_id in parent_by_node:
            if current_id in path_index:
                cycle = path[path_index[current_id] :]
                root_id = min(cycle, key=lambda node_id: source_order[node_id])
                parent_by_node[root_id] = None
                warnings.append(f"parent-cycle-broken-at:{root_id}")
                break
            path_index[current_id] = len(path)
            path.append(current_id)
            current_id = parent_by_node.get(current_id)
    return warnings


def _ordered_nodes(
    data_root: ET.Element,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    raw_points: list[dict[str, Any]] = []
    for source_index, point in enumerate(
        data_root.findall(".//dgm:ptLst/dgm:pt", DIAGRAM_NS_MAP),
    ):
        model_id = point.attrib.get("modelId", "")
        point_type = point.attrib.get("type") or "node"
        text = _point_text(point)
        if not model_id or point_type not in _CONTENT_POINT_TYPES:
            continue
        raw_points.append(
            {
                "id": model_id,
                "type": point_type,
                "text": text,
                "source_index": source_index,
            }
        )

    all_connections = _connections(data_root)
    parent_by_id: dict[str, str] = {}
    order_by_id: dict[str, int | None] = {}
    for connection in all_connections:
        if connection["type"] != "parOf":
            continue
        destination_id = connection["destination_id"]
        parent_by_id.setdefault(destination_id, connection["source_id"])
        order_by_id.setdefault(destination_id, connection["source_order"])

    content_ids = {point["id"] for point in raw_points}
    source_order = {point["id"]: int(point["source_index"]) for point in raw_points}
    parent_by_node = {
        point["id"]: _nearest_content_parent(
            point["id"],
            parent_by_id,
            content_ids,
        )
        for point in raw_points
    }
    structure_warnings = _break_parent_cycles(parent_by_node, source_order)
    nodes_by_id: dict[str, dict[str, Any]] = {}
    for point in raw_points:
        node = {
            "id": point["id"],
            "type": point["type"],
            "text": point["text"],
            "parent_id": parent_by_node[point["id"]],
            "order": order_by_id.get(point["id"]),
            "depth": 0,
            "_source_index": point["source_index"],
        }
        nodes_by_id[point["id"]] = node

    children: dict[str | None, list[dict[str, Any]]] = {}
    for node in nodes_by_id.values():
        children.setdefault(node["parent_id"], []).append(node)

    def sort_key(node: dict[str, Any]) -> tuple[int, int]:
        order = node["order"]
        return (
            order if isinstance(order, int) else 1_000_000,
            int(node["_source_index"]),
        )

    for siblings in children.values():
        siblings.sort(key=sort_key)

    ordered: list[dict[str, Any]] = []
    visited: set[str] = set()

    def visit(node: dict[str, Any], depth: int) -> None:
        node_id = str(node["id"])
        if node_id in visited:
            return
        visited.add(node_id)
        node["depth"] = depth
        ordered.append(node)
        for child in children.get(node_id, []):
            visit(child, depth + 1)

    for root in children.get(None, []):
        visit(root, 0)
    for node in sorted(nodes_by_id.values(), key=sort_key):
        if node["id"] not in visited:
            visit(node, 0)

    for node in ordered:
        node.pop("_source_index", None)

    visible_connections = [
        connection
        for connection in all_connections
        if connection["type"] == "parOf"
        and connection["source_id"] in content_ids
        and connection["destination_id"] in content_ids
    ]
    return ordered, visible_connections, structure_warnings


def _read_diagram_container(
    zf: zipfile.ZipFile,
    container: ET.Element,
    *,
    slide_part: str,
    slide_index: int,
    order: int,
    relationships: dict[str, dict[str, str]],
    relationship_error: str | None,
    fallback_shape_ids: set[str],
) -> dict[str, Any]:
    shape_id, shape_name = _shape_identity(container, order)
    graphic_data = container.find("a:graphic/a:graphicData", DIAGRAM_NS_MAP)
    rel_ids = (
        graphic_data.find("dgm:relIds", DIAGRAM_NS_MAP)
        if graphic_data is not None
        else None
    )
    parts, diagram_relation_error = _diagram_parts(
        rel_ids,
        relationships,
        slide_part,
    )
    data_root, data_error = _read_optional_xml(zf, parts.get("data"))
    layout_root, layout_error = _read_optional_xml(zf, parts.get("layout"))
    metadata_warnings = [f"layout:{layout_error}"] if layout_error else []
    nodes: list[dict[str, Any]] = []
    connections: list[dict[str, Any]] = []
    structure_warnings: list[str] = []
    if data_root is not None:
        nodes, connections, structure_warnings = _ordered_nodes(data_root)

    status = relationship_error or diagram_relation_error or data_error
    if status is None and structure_warnings:
        status = "structure-cycle"
    persisted_drawing, drawing_warnings = _persisted_drawing_part(
        zf,
        parts.get("data"),
        data_root,
        slide_part,
        relationships,
    )
    text_items = [node["text"] for node in nodes if node["text"]]
    return {
        "diagram_id": f"s{slide_index:02d}_dgm{shape_id}",
        "kind": "smartart",
        "shape_id": shape_id,
        "shape_name": shape_name,
        "geometry": _container_geometry(container),
        "layout": _layout_info(layout_root, data_root),
        "root_ids": [node["id"] for node in nodes if node["parent_id"] is None],
        "nodes": nodes,
        "connections": connections,
        "text_items": text_items,
        "node_count": len(nodes),
        "text_count": len(text_items),
        "connection_count": len(connections),
        "max_depth": max((int(node["depth"]) for node in nodes), default=0),
        "text_extracted": data_root is not None,
        "has_persisted_drawing": persisted_drawing is not None,
        "has_fallback_preview": shape_id in fallback_shape_ids,
        "status": status or "ok",
        "warnings": metadata_warnings + structure_warnings + drawing_warnings,
    }


def _failed_diagram(
    container: ET.Element,
    *,
    slide_index: int,
    order: int,
    error: Exception,
    fallback_shape_ids: set[str],
) -> dict[str, Any]:
    shape_id, shape_name = _shape_identity(container, order)
    return {
        "diagram_id": f"s{slide_index:02d}_dgm{shape_id}",
        "kind": "smartart",
        "shape_id": shape_id,
        "shape_name": shape_name,
        "geometry": _container_geometry(container),
        "layout": {"name": None, "unique_id": None, "categories": []},
        "root_ids": [],
        "nodes": [],
        "connections": [],
        "text_items": [],
        "node_count": 0,
        "text_count": 0,
        "connection_count": 0,
        "max_depth": 0,
        "text_extracted": False,
        "has_persisted_drawing": False,
        "has_fallback_preview": shape_id in fallback_shape_ids,
        "status": "diagram-read-error",
        "warnings": [f"{type(error).__name__}:{error}"],
    }


def read_smartart_diagrams(
    zf: zipfile.ZipFile,
    slide_part: str,
    slide_index: int,
) -> list[dict[str, Any]]:
    """Return SmartArt source facts for one slide part."""
    slide_root = _read_xml(zf, slide_part)
    relationship_error: str | None = None
    try:
        relationships = _slide_relationships(zf, _rels_name_for_part(slide_part))
    except ET.ParseError:
        relationships = {}
        relationship_error = "invalid-slide-relationships"
    fallback_shape_ids = _fallback_preview_shape_ids(slide_root)
    diagrams: list[dict[str, Any]] = []

    for order, container in enumerate(_diagram_containers(slide_root), start=1):
        try:
            diagram = _read_diagram_container(
                zf,
                container,
                slide_part=slide_part,
                slide_index=slide_index,
                order=order,
                relationships=relationships,
                relationship_error=relationship_error,
                fallback_shape_ids=fallback_shape_ids,
            )
        except (OSError, RuntimeError, zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as exc:
            diagram = _failed_diagram(
                container,
                slide_index=slide_index,
                order=order,
                error=exc,
                fallback_shape_ids=fallback_shape_ids,
            )
        diagrams.append(diagram)
    return diagrams


def smartart_to_markdown(diagram: dict[str, Any]) -> str:
    """Render one extracted SmartArt diagram as hierarchical Markdown."""
    name = str(diagram.get("shape_name") or diagram.get("diagram_id") or "SmartArt")
    layout = diagram.get("layout") or {}
    layout_name = str(layout.get("name") or "") if isinstance(layout, dict) else ""
    heading = f"### SmartArt: {name}"
    if layout_name and layout_name.lower() not in name.lower():
        heading += f" — {layout_name}"
    lines = [heading, ""]
    nodes = diagram.get("nodes") or []
    text_nodes = [node for node in nodes if str(node.get("text") or "").strip()]
    if text_nodes:
        nodes_by_id = {
            str(node.get("id")): node
            for node in nodes
            if node.get("id") is not None
        }
        rendered_depths: dict[str, int] = {}

        def rendered_depth(node: dict[str, Any]) -> int:
            node_id = str(node.get("id") or "")
            if node_id in rendered_depths:
                return rendered_depths[node_id]
            parent = nodes_by_id.get(str(node.get("parent_id") or ""))
            if parent is None:
                depth = 0
            else:
                depth = rendered_depth(parent)
                if str(parent.get("text") or "").strip():
                    depth += 1
            rendered_depths[node_id] = depth
            return depth

        for node in text_nodes:
            text = " / ".join(str(node.get("text") or "").splitlines()).strip()
            indent = "  " * rendered_depth(node)
            lines.append(f"{indent}- {text}")
    elif nodes:
        lines.append(f"> [SmartArt structure has {len(nodes)} node(s), but no text]")
    else:
        status = str(diagram.get("status") or "content-unavailable")
        if diagram.get("text_extracted") and status == "ok":
            lines.append("> [SmartArt data is readable but has no semantic nodes]")
        else:
            lines.append(f"> [SmartArt content unavailable: {status}]")
    return "\n".join(lines).rstrip()
