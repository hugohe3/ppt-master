"""Structured diagnostics for tolerant PPTX-to-SVG import."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ImportDiagnostic:
    """Describe one source-owned construct that required import recovery."""

    code: str
    message: str
    fallback: str
    part_path: str = ""
    slide_index: int | None = None
    shape_id: str = ""
    shape_name: str = ""
    shape_kind: str = ""
    severity: str = "warning"

    def to_dict(self) -> dict[str, object]:
        """Return the stable JSON representation."""
        return {
            key: value
            for key, value in asdict(self).items()
            if value not in {"", None}
        }


def append_diagnostic(
    diagnostics: list[ImportDiagnostic],
    diagnostic: ImportDiagnostic,
) -> None:
    """Append one diagnostic while suppressing duplicate layered/flat reports."""
    if diagnostic not in diagnostics:
        diagnostics.append(diagnostic)
