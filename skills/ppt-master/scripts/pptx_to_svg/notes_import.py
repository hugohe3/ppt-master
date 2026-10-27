"""Import PowerPoint speaker notes into the project notes Markdown contract."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from .emu_units import NS, ooxml_bool
from .import_diagnostics import ImportDiagnostic, append_diagnostic
from .ooxml_loader import OoxmlPackage


_NOTES_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
)
_EXCLUDED_PLACEHOLDER_TYPES = frozenset({
    "dt",
    "ftr",
    "hdr",
    "sldImg",
    "sldNum",
})


@dataclass(frozen=True)
class ImportedSpeakerNote:
    """One source notes part projected into editable Markdown."""

    slide_index: int
    source_part: str
    source_sha256: str
    markdown: str

    @property
    def filename(self) -> str:
        """Return the canonical index-based notes filename."""
        return f"slide_{self.slide_index:02d}.md"


def _paragraph_text(paragraph: ET.Element) -> str:
    pieces: list[str] = []
    for node in paragraph.iter():
        tag = node.tag.rsplit("}", 1)[-1] if isinstance(node.tag, str) else ""
        if tag == "t" and node.text:
            pieces.append(node.text)
        elif tag == "br":
            pieces.append("\n")
    text = "".join(pieces).strip()
    if not text:
        return ""
    paragraph_properties = paragraph.find("a:pPr", NS)
    if (
        paragraph_properties is not None
        and paragraph_properties.find("a:buChar", NS) is not None
    ):
        return f"- {text}"
    return text


def _notes_markdown(root: ET.Element, hidden_shapes: list[ET.Element]) -> str:
    blocks: list[str] = []
    parents = {child: parent for parent in root.iter() for child in parent}
    for shape in root.findall(".//p:sp", NS):
        placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
        placeholder_type = placeholder.get("type") if placeholder is not None else None
        if placeholder_type in _EXCLUDED_PLACEHOLDER_TYPES:
            continue
        text_body = shape.find("p:txBody", NS)
        if text_body is None:
            continue
        paragraphs = [
            text
            for paragraph in text_body.findall("a:p", NS)
            if (text := _paragraph_text(paragraph))
        ]
        if paragraphs:
            ancestor = shape
            while ancestor is not None:
                properties = ancestor.find("./*/p:cNvPr", NS)
                if properties is not None and ooxml_bool(properties.get("hidden")):
                    hidden_shapes.append(shape)
                    break
                ancestor = parents.get(ancestor)
            else:
                blocks.append("\n".join(paragraphs))
    return "\n\n".join(blocks).strip()


def import_speaker_notes(
    pkg: OoxmlPackage,
    diagnostics: list[ImportDiagnostic] | None = None,
) -> tuple[ImportedSpeakerNote, ...]:
    """Return every non-empty source speaker note in presentation order."""
    notes: list[ImportedSpeakerNote] = []
    for slide in pkg.iter_slides():
        source_part = next(
            (
                relationship.get("target", "")
                for relationship in slide.part.rels.values()
                if relationship.get("type") == _NOTES_REL_TYPE
                and not relationship.get("external")
            ),
            "",
        )
        if not source_part:
            continue
        payload = pkg.read_part_bytes(source_part)
        if payload is None:
            continue
        try:
            root = ET.fromstring(payload)
        except ET.ParseError:
            continue
        hidden_shapes: list[ET.Element] = []
        markdown = _notes_markdown(root, hidden_shapes)
        if diagnostics is not None:
            for shape in hidden_shapes:
                properties = shape.find("p:nvSpPr/p:cNvPr", NS)
                append_diagnostic(diagnostics, ImportDiagnostic(
                    code="hidden-notes-content",
                    message="Author-hidden speaker-note text was excluded from Markdown",
                    fallback="retain hidden source XML on untouched round-trip notes",
                    part_path=source_part,
                    slide_index=slide.index,
                    shape_id=properties.get("id", "") if properties is not None else "",
                    shape_name=properties.get("name", "") if properties is not None else "",
                    shape_kind="notes-shape",
                ))
        if not markdown:
            continue
        notes.append(ImportedSpeakerNote(
            slide_index=slide.index,
            source_part=source_part,
            source_sha256=hashlib.sha256(payload).hexdigest(),
            markdown=markdown,
        ))
    return tuple(notes)


__all__ = ["ImportedSpeakerNote", "import_speaker_notes"]
