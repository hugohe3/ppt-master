"""Project root-SVG canvas parsing and cross-file validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


class CanvasContractError(ValueError):
    """Raised when a root SVG canvas cannot map faithfully to one slide."""


PPTX_SLIDE_EMU_MIN = 914400
PPTX_SLIDE_EMU_MAX = 51206400


_SVG_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_VIEWBOX_RE = re.compile(
    rf"^\s*({_SVG_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_SVG_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_SVG_NUMBER})(?:\s*,\s*|\s+)"
    rf"({_SVG_NUMBER})\s*$"
)


@dataclass(frozen=True)
class ProjectViewBox:
    """One validated zero-origin project canvas."""

    width: Decimal
    height: Decimal

    @property
    def values(self) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        return Decimal(0), Decimal(0), self.width, self.height

    @property
    def pixel_dimensions(self) -> tuple[float, float]:
        return float(self.width), float(self.height)

    @property
    def emu_dimensions(self) -> tuple[int, int]:
        """Quantize the SVG canvas to DrawingML's integer EMU dimensions."""
        width_emu, height_emu = self._scaled_emu_values()
        width = int(width_emu.to_integral_value(ROUND_HALF_UP))
        height = int(height_emu.to_integral_value(ROUND_HALF_UP))
        return width, height

    def _scaled_emu_values(self) -> tuple[Decimal, Decimal]:
        precision = max(
            28,
            len(self.width.as_tuple().digits) + 8,
            len(self.height.as_tuple().digits) + 8,
        )
        with localcontext() as context:
            context.prec = precision
            return self.width * Decimal(9525), self.height * Decimal(9525)

    @property
    def canonical(self) -> str:
        return f"0 0 {_format_decimal(self.width)} {_format_decimal(self.height)}"

    @property
    def has_integer_dimensions(self) -> bool:
        return (
            self.width == self.width.to_integral_value()
            and self.height == self.height.to_integral_value()
        )


def _format_decimal(value: Decimal) -> str:
    token = format(value, "f")
    if "." in token:
        token = token.rstrip("0").rstrip(".")
    return token or "0"


def parse_project_viewbox(
    raw: str | None,
    *,
    context: str = "root viewBox",
) -> ProjectViewBox:
    """Parse the registered project root-viewBox subset.

    Equivalent SVG numeric spellings are accepted so callers can distinguish
    compatible input from canonical authoring. Semantic values stay closed:
    the origin is exactly zero and dimensions map to positive DrawingML sizes.
    Fractional dimensions remain read-compatible because imported custom PPTX
    slide sizes are not necessarily whole CSS pixels.
    """
    if raw is None or not raw.strip():
        raise CanvasContractError(f"{context} is required")

    match = _VIEWBOX_RE.fullmatch(raw)
    if match is None:
        raise CanvasContractError(
            f"{context} must contain exactly four SVG numbers; got {raw!r}"
        )

    try:
        values = tuple(Decimal(token) for token in match.groups())
    except InvalidOperation as exc:
        raise CanvasContractError(
            f"{context} contains an invalid numeric value; got {raw!r}"
        ) from exc
    if not all(value.is_finite() for value in values):
        raise CanvasContractError(
            f"{context} values must be finite; got {raw!r}"
        )

    x, y, width, height = values
    if x != 0 or y != 0:
        raise CanvasContractError(
            f'{context} origin must be "0 0"; got {raw!r}'
        )
    if width <= 0 or height <= 0:
        raise CanvasContractError(
            f"{context} width and height must be positive; got {raw!r}"
        )
    viewbox = ProjectViewBox(width=width, height=height)
    require_powerpoint_slide_size(viewbox, context=context)
    return viewbox


def read_project_viewbox(svg_path: str | Path) -> ProjectViewBox:
    """Read and validate one file's root SVG viewBox."""
    path = Path(svg_path)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise CanvasContractError(f"{path.name}: unable to parse root SVG: {exc}") from exc
    return parse_project_svg_root(
        root,
        context=path.name,
    )


def parse_project_svg_root(
    root: ET.Element,
    *,
    context: str = "document",
) -> ProjectViewBox:
    """Validate one page root element and its project viewBox."""
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise CanvasContractError(f"{context}: root element must be <svg>")
    return parse_project_viewbox(
        root.get("viewBox"),
        context=f"{context} root viewBox",
    )


def require_powerpoint_slide_size(
    viewbox: ProjectViewBox,
    *,
    context: str = "SVG canvas",
) -> tuple[int, int]:
    """Return EMU dimensions or reject values outside PowerPoint's range."""
    # Reject before converting to int so an adversarial exponent cannot force
    # construction of an enormous Python integer or fixed-point string.
    values = viewbox.width, viewbox.height
    outside_coarse_bound = any(
        value > Decimal(PPTX_SLIDE_EMU_MAX) for value in values
    )
    scaled = () if outside_coarse_bound else viewbox._scaled_emu_values()
    outside_emu_bound = outside_coarse_bound or not all(
        Decimal(PPTX_SLIDE_EMU_MIN) - Decimal("0.5")
        <= value
        < Decimal(PPTX_SLIDE_EMU_MAX) + Decimal("0.5")
        for value in scaled
    )
    if outside_emu_bound:
        dimensions = f"{viewbox.width} x {viewbox.height} px"
        raise CanvasContractError(
            f"{context} must map to PowerPoint's supported slide range "
            f"({PPTX_SLIDE_EMU_MIN}..{PPTX_SLIDE_EMU_MAX} EMU per side); "
            f"got {dimensions}"
        )
    return viewbox.emu_dimensions


def require_consistent_project_viewboxes(
    svg_paths: Iterable[str | Path],
    *,
    expected_viewbox: str | None = None,
    expected_label: str = "expected canvas",
) -> ProjectViewBox:
    """Validate every public/internal SVG and return their shared canvas."""
    paths = [Path(path) for path in svg_paths]
    if not paths:
        raise CanvasContractError("at least one SVG is required to resolve the canvas")

    errors: list[str] = []
    parsed: list[tuple[Path, ProjectViewBox]] = []
    for path in paths:
        try:
            parsed.append((path, read_project_viewbox(path)))
        except CanvasContractError as exc:
            errors.append(str(exc))
    if errors:
        details = "\n".join(f"  - {error}" for error in errors)
        raise CanvasContractError("SVG canvas validation failed:\n" + details)

    if expected_viewbox is not None:
        reference = parse_project_viewbox(
            expected_viewbox,
            context=f"{expected_label} viewBox",
        )
    else:
        reference = parsed[0][1]

    mismatches = [
        f"{path.name}: expected {reference.canonical}, got {viewbox.canonical}"
        for path, viewbox in parsed
        if viewbox != reference
    ]
    if mismatches:
        details = "\n".join(f"  - {message}" for message in mismatches)
        raise CanvasContractError(
            f"SVG canvases must all match {expected_label} "
            f"({reference.canonical}):\n{details}"
        )
    return reference
