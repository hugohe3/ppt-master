"""Shared projection and integrity helpers for mirror-template text slots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from xml.etree import ElementTree as ET


MODEL_TEXT_SLOT_KEYS = (
    "selector",
    "role",
    "current_text",
    "text_segments",
    "tspan_count",
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _ancestor_chain(
    element: ET.Element,
    parent_by_child: dict[ET.Element, ET.Element],
) -> list[ET.Element]:
    chain = [element]
    while chain[-1] in parent_by_child:
        chain.append(parent_by_child[chain[-1]])
    return chain


def _nearest_attribute(chain: list[ET.Element], name: str) -> str | None:
    for element in chain:
        value = element.get(name)
        if value is not None:
            return value
    return None


def _text_selector(
    element: ET.Element,
    parent_by_child: dict[ET.Element, ET.Element],
    *,
    compact: bool,
) -> str:
    segments: list[str] = []
    current = element
    while True:
        element_id = (current.get("id") or "").strip()
        if element_id:
            segments.append(f"#{element_id}")
            break
        parent = parent_by_child.get(current)
        tag = _local_name(current.tag)
        if parent is None:
            segments.append(tag)
            break
        same_tag = [child for child in parent if _local_name(child.tag) == tag]
        if compact and len(same_tag) == 1:
            segments.append(tag)
        else:
            segments.append(f"{tag}:nth-of-type({same_tag.index(current) + 1})")
        current = parent
    separator = ">" if compact else " > "
    return separator.join(reversed(segments))


def _text_topology_sha256(element: ET.Element) -> str:
    """Hash text/tspan topology and attributes while excluding visible values."""
    digest = hashlib.sha256()

    def visit(node: ET.Element) -> None:
        digest.update(_local_name(node.tag).encode("utf-8"))
        for name, value in sorted(node.attrib.items()):
            digest.update(b"\0a")
            digest.update(name.encode("utf-8"))
            digest.update(b"\0")
            digest.update(value.encode("utf-8"))
        for child in node:
            digest.update(b"\0c")
            visit(child)
        digest.update(b"\0e")

    visit(element)
    return digest.hexdigest()


@dataclass(frozen=True)
class TemplateTextSlot:
    selector: str
    legacy_selector: str
    role: str
    current_text: str
    text_segments: tuple[str, ...]
    tspan_count: int
    topology_sha256: str
    editable: bool

    def model_payload(self) -> dict[str, object]:
        return {
            "selector": self.selector,
            "role": self.role,
            "current_text": self.current_text,
            "text_segments": list(self.text_segments),
            "tspan_count": self.tspan_count,
        }


def analyze_template_text_slots(root: ET.Element) -> tuple[TemplateTextSlot, ...]:
    """Derive the model projection and tool-only integrity facts from one SVG."""
    parent_by_child = {
        child: parent
        for parent in root.iter()
        for child in parent
    }
    slots: list[TemplateTextSlot] = []
    for text_element in root.iter():
        if _local_name(text_element.tag) != "text":
            continue
        chain = _ancestor_chain(text_element, parent_by_child)
        placeholder = _nearest_attribute(chain, "data-pptx-placeholder")
        editable_value = _nearest_attribute(chain, "data-pptx-editable")
        inherited_layer = _nearest_attribute(chain, "data-pptx-layer")
        tspans = [
            child
            for child in text_element.iter()
            if child is not text_element and _local_name(child.tag) == "tspan"
        ]
        segments = [
            text_element.text or "",
            *[(tspan.text or "") for tspan in tspans],
        ]
        if tspans and not segments[0].strip():
            segments = segments[1:]
        slots.append(TemplateTextSlot(
            selector=_text_selector(
                text_element,
                parent_by_child,
                compact=True,
            ),
            legacy_selector=_text_selector(
                text_element,
                parent_by_child,
                compact=False,
            ),
            role=placeholder or "text",
            current_text="".join(text_element.itertext()),
            text_segments=tuple(segments),
            tspan_count=len(tspans),
            topology_sha256=_text_topology_sha256(text_element),
            editable=editable_value != "false" and inherited_layer is None,
        ))
    selectors = [slot.selector for slot in slots]
    if len(selectors) != len(set(selectors)):
        raise ValueError("template text selectors are not unique")
    return tuple(slots)


def text_slot_integrity_sha256(slots: tuple[TemplateTextSlot, ...]) -> str:
    """Hash selectors plus immutable text/tspan topology and attributes."""
    payload = [
        {
            "selector": slot.selector,
            "topology_sha256": slot.topology_sha256,
        }
        for slot in slots
    ]
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()
