"""Convert a DrawingML <a:tbl> into SVG.

Tables in PowerPoint are stored under <p:graphicFrame> with
graphicData uri="...drawingml/2006/table" wrapping a single <a:tbl>:

    <p:graphicFrame>
      <p:xfrm>...</p:xfrm>
      <a:graphic><a:graphicData uri="...table">
        <a:tbl>
          <a:tblPr/>
          <a:tblGrid>
            <a:gridCol w="..."/>...
          </a:tblGrid>
          <a:tr h="...">
            <a:tc [gridSpan=N] [rowSpan=N] [hMerge=1] [vMerge=1]>
              <a:txBody>...</a:txBody>
              <a:tcPr>
                <a:lnL/><a:lnR/><a:lnT/><a:lnB/>
                <a:solidFill/>... or <a:gradFill/> ...
              </a:tcPr>
            </a:tc>
          </a:tr>
        </a:tbl>
      </a:graphicData></a:graphic>
    </p:graphicFrame>

The graphicFrame's <p:xfrm> gives the table's slide-space position and total
size; <a:tblGrid> + <a:tr> heights distribute that size across columns/rows.

Cell painting order:
1. background fill (rect at cell box)
2. text body (re-uses convert_txbody)
3. cell borders (lnT / lnR / lnB / lnL — stroked as separate <line>s so
   neighbouring cells with different border styles render correctly)
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

from pptx_effects import txbody_has_run_effects

from .color_resolver import ColorPalette, find_color_elem, resolve_color
from .emu_units import (
    NS,
    Xfrm,
    emu_to_px,
    fmt_num,
    hundredths_pt_to_px,
    ooxml_bool,
)
from .fill_to_svg import FillResult, resolve_fill
from .ln_to_svg import resolve_stroke
from .txbody_to_svg import _resolve_theme_typeface, convert_txbody


BUILTIN_MEDIUM_STYLE_2_ACCENT_1 = "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"
_POWERPOINT_COORD_MIN = -(2**31)
_POWERPOINT_COORD_MAX = 2**31 - 1

_BUILTIN_MEDIUM_STYLE_2_ACCENT_1_XML = ET.fromstring(
    f'''<a:tblStyle xmlns:a="{NS["a"]}"
        styleId="{BUILTIN_MEDIUM_STYLE_2_ACCENT_1}">
      <a:wholeTbl>
        <a:tcTxStyle>
          <a:fontRef idx="minor"><a:prstClr val="black"/></a:fontRef>
          <a:schemeClr val="dk1"/>
        </a:tcTxStyle>
        <a:tcStyle>
          <a:tcBdr>
            <a:left><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:left>
            <a:right><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:right>
            <a:top><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:top>
            <a:bottom><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:bottom>
            <a:insideH><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:insideH>
            <a:insideV><a:ln w="12700"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:insideV>
          </a:tcBdr>
          <a:fill><a:solidFill><a:schemeClr val="accent1"><a:tint val="20000"/></a:schemeClr></a:solidFill></a:fill>
        </a:tcStyle>
      </a:wholeTbl>
      <a:band1H>
        <a:tcStyle><a:fill><a:solidFill><a:schemeClr val="accent1"><a:tint val="40000"/></a:schemeClr></a:solidFill></a:fill></a:tcStyle>
      </a:band1H>
      <a:band2H><a:tcStyle/></a:band2H>
      <a:firstRow>
        <a:tcTxStyle b="on">
          <a:fontRef idx="minor"><a:prstClr val="black"/></a:fontRef>
          <a:schemeClr val="lt1"/>
        </a:tcTxStyle>
        <a:tcStyle>
          <a:tcBdr><a:bottom><a:ln w="38100"><a:solidFill><a:schemeClr val="lt1"/></a:solidFill></a:ln></a:bottom></a:tcBdr>
          <a:fill><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:fill>
        </a:tcStyle>
      </a:firstRow>
    </a:tblStyle>'''
)


@dataclass
class TableResult:
    """Composite render output, replacement metadata, and effect diagnostics."""

    svg: str = ""
    defs: list[str] = None
    native_payload: dict[str, Any] | None = None
    native_status: str | None = None
    effect_reason: str | None = None

    def __post_init__(self) -> None:
        if self.defs is None:
            self.defs = []


@dataclass(frozen=True)
class _TableStyleContext:
    """Small, best-effort view of the table style regions we render."""

    style: ET.Element | None
    table_properties: ET.Element | None

    def regions_for_row(self, row_index: int) -> tuple[tuple[str, ET.Element], ...]:
        if self.style is None:
            return ()

        names: list[str] = []
        first_row = bool(
            self.table_properties is not None
            and ooxml_bool(self.table_properties.get("firstRow"))
        )
        if first_row and row_index == 0:
            names.append("firstRow")
        elif (
            self.table_properties is not None
            and ooxml_bool(self.table_properties.get("bandRow"))
        ):
            band_index = row_index - (1 if first_row else 0)
            names.append("band1H" if band_index % 2 == 0 else "band2H")
        names.append("wholeTbl")

        regions: list[tuple[str, ET.Element]] = []
        for name in names:
            region = self.style.find(f"a:{name}", NS)
            if region is not None:
                regions.append((name, region))
        return tuple(regions)


def _normalize_table_style_id(value: str | None) -> str:
    return (value or "").strip().strip("{}").upper()


def _resolve_table_style(
    tbl: ET.Element,
    table_styles: ET.Element | None,
) -> _TableStyleContext:
    tbl_pr = tbl.find("a:tblPr", NS)
    style_id = (
        tbl_pr.findtext("a:tableStyleId", default="", namespaces=NS).strip()
        if tbl_pr is not None else ""
    )
    if not style_id and table_styles is not None:
        style_id = table_styles.get("def", "").strip()
    normalized_id = _normalize_table_style_id(style_id)
    supported_id = _normalize_table_style_id(BUILTIN_MEDIUM_STYLE_2_ACCENT_1)

    # P1 deliberately supports one built-in family.  Consuming an arbitrary
    # custom definition here would be asymmetric: native reconstruction keeps
    # only the style id and does not copy custom tableStyles.xml definitions.
    if normalized_id != supported_id:
        return _TableStyleContext(None, tbl_pr)

    if table_styles is not None and normalized_id:
        for candidate in table_styles.findall("a:tblStyle", NS):
            if _normalize_table_style_id(candidate.get("styleId")) == normalized_id:
                return _TableStyleContext(candidate, tbl_pr)

    return _TableStyleContext(_BUILTIN_MEDIUM_STYLE_2_ACCENT_1_XML, tbl_pr)


def _effective_cell_fill(
    tc_pr: ET.Element | None,
    table_style: _TableStyleContext,
    row_index: int,
    palette: ColorPalette | None,
    *,
    id_prefix: str,
    id_seq: list[int],
) -> FillResult:
    """Resolve direct cell fill before row-region and whole-table defaults."""
    direct = resolve_fill(
        tc_pr, palette, id_prefix=id_prefix, id_seq=id_seq,
    )
    if direct.attrs or direct.defs:
        return direct

    for _name, region in table_style.regions_for_row(row_index):
        fill_parent = region.find("a:tcStyle/a:fill", NS)
        if fill_parent is None:
            continue
        inherited = resolve_fill(
            fill_parent, palette, id_prefix=id_prefix, id_seq=id_seq,
        )
        if inherited.attrs or inherited.defs:
            return inherited
    return direct


def _table_text_run_props(
    table_style: _TableStyleContext,
    row_index: int,
    theme_fonts: dict[str, str],
) -> tuple[ET.Element, ...]:
    """Materialize table text-style regions as lowest-priority run defaults."""
    props: list[ET.Element] = []
    for _name, region in table_style.regions_for_row(row_index):
        tx_style = region.find("a:tcTxStyle", NS)
        if tx_style is None:
            continue
        run_props = _table_tx_style_run_props(tx_style, theme_fonts)
        if run_props is not None:
            props.append(run_props)
    return tuple(props)


def _table_tx_style_run_props(
    tx_style: ET.Element,
    theme_fonts: dict[str, str],
) -> ET.Element | None:
    run_props = ET.Element(f"{{{NS['a']}}}rPr")
    for attr in ("b", "i"):
        value = tx_style.get(attr)
        if value is not None:
            run_props.set(attr, "1" if ooxml_bool(value) else "0")

    font_ref = tx_style.find("a:fontRef", NS)
    font_role = font_ref.get("idx") if font_ref is not None else None
    if font_role in {"major", "minor"}:
        prefix = "major" if font_role == "major" else "minor"
        latin = theme_fonts.get(f"{prefix}Latin")
        east_asia = theme_fonts.get(f"{prefix}EastAsia") or latin
        complex_script = theme_fonts.get(f"{prefix}ComplexScript") or latin
        for tag, typeface in (
            ("latin", latin),
            ("ea", east_asia),
            ("cs", complex_script),
        ):
            if typeface:
                ET.SubElement(
                    run_props, f"{{{NS['a']}}}{tag}",
                    {"typeface": typeface},
                )

    color = find_color_elem(tx_style)
    if color is not None:
        solid_fill = ET.SubElement(run_props, f"{{{NS['a']}}}solidFill")
        solid_fill.append(copy.deepcopy(color))

    if not run_props.attrib and not list(run_props):
        return None
    return run_props


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def convert_tbl(
    tbl: ET.Element,
    xfrm: Xfrm,
    palette: ColorPalette | None,
    *,
    table_styles: ET.Element | None = None,
    theme_fonts: dict[str, str] | None = None,
    slide_number: int | None = None,
    id_prefix: str = "tbl",
    grad_seq: list[int] | None = None,
    marker_seq: list[int] | None = None,
) -> TableResult:
    """Render an <a:tbl> at the given absolute xfrm into SVG markup."""
    grad_seq = grad_seq if grad_seq is not None else [0]
    marker_seq = marker_seq if marker_seq is not None else [0]

    col_widths_px = _column_widths_px(tbl)
    if not col_widths_px:
        return TableResult()
    rows = tbl.findall("a:tr", NS)
    if not rows:
        return TableResult()
    table_style = _resolve_table_style(tbl, table_styles)
    row_heights_px = [_row_height_px(r) for r in rows]
    grid_topology_invalid = any(
        len(row.findall("a:tc", NS)) != len(col_widths_px)
        for row in rows
    )
    source_geometry_invalid = (
        grid_topology_invalid
        or any(width <= 0 for width in col_widths_px)
        or any(height <= 0 for height in row_heights_px)
        or sum(col_widths_px) <= 0
        or sum(row_heights_px) <= 0
    )

    # PowerPoint's tblGrid widths and tr heights together describe the
    # *intrinsic* table size. The graphicFrame xfrm width/height may differ;
    # if it does, scale rows/columns proportionally so the table fills the
    # frame the way PowerPoint renders it.
    intrinsic_w = sum(col_widths_px) or xfrm.w
    intrinsic_h = sum(row_heights_px) or xfrm.h
    sx = (xfrm.w / intrinsic_w) if intrinsic_w else 1.0
    sy = (xfrm.h / intrinsic_h) if intrinsic_h else 1.0
    col_widths = [w * sx for w in col_widths_px]
    row_heights = [h * sy for h in row_heights_px]

    col_lefts = _cumulative_starts(xfrm.x, col_widths)
    row_tops = _cumulative_starts(xfrm.y, row_heights)

    # First pass: resolve merge state so spanned cells get the union geometry
    # and dropped cells don't render anything. PowerPoint expresses merges via
    # gridSpan/rowSpan on the anchor cell + hMerge/vMerge on the dropped cells.
    cells = _build_cell_grid(rows, len(col_widths))
    merge_status = _canonical_native_merge_status(rows, len(col_widths))
    effect_reason = (
        "unsupported-run-effect-route:table-cell-text"
        if any(
            txbody_has_run_effects(tc.find("a:txBody", NS))
            for tc in tbl.findall(".//a:tc", NS)
        )
        else None
    )
    if xfrm.rot or xfrm.flip_h or xfrm.flip_v:
        native_status = "unsupported-native-transform"
    elif merge_status:
        native_status = merge_status
    elif len(rows) > 1000 or len(col_widths) > 1000:
        native_status = "unsupported-table-size"
    elif source_geometry_invalid or (
        any(width <= 0 for width in col_widths)
        or any(height <= 0 for height in row_heights)
        or sum(col_widths) <= 0
        or sum(row_heights) <= 0
    ):
        native_status = "unsupported-table-geometry"
    elif _table_has_unsupported_style(tbl):
        native_status = "unsupported-table-style"
    elif (
        effect_reason
        or _table_has_unsupported_direct_formatting(tbl, palette)
    ):
        native_status = "unsupported-table-direct-formatting"
    else:
        native_status = None
    native_payload = (
        None if native_status else _native_table_payload(
            tbl,
            xfrm,
            col_widths,
            row_heights,
            cells,
            palette,
            theme_fonts or {},
        )
    )

    body_parts: list[str] = []
    defs: list[str] = []

    # Pass A: cell backgrounds.
    for r, row_cells in enumerate(cells):
        for c, cell in enumerate(row_cells):
            if cell is None or cell.is_dropped:
                continue
            rect_x = col_lefts[c]
            rect_y = row_tops[r]
            rect_w = sum(col_widths[c:c + cell.col_span])
            rect_h = sum(row_heights[r:r + cell.row_span])
            tcPr = cell.element.find("a:tcPr", NS)
            fill = _effective_cell_fill(
                tcPr, table_style, r, palette,
                id_prefix=f"{id_prefix}fill",
                id_seq=grad_seq,
            )
            defs.extend(fill.defs)
            attrs = fill.attrs or {"fill": "none"}
            attr_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
            body_parts.append(
                f'<rect x="{fmt_num(rect_x)}" y="{fmt_num(rect_y)}" '
                f'width="{fmt_num(rect_w)}" height="{fmt_num(rect_h)}"'
                f'{attr_str}/>'
            )

    # Pass B: cell text. Cell xfrm uses default tcPr insets if none specified.
    for r, row_cells in enumerate(cells):
        for c, cell in enumerate(row_cells):
            if cell is None or cell.is_dropped:
                continue
            tx_body = cell.element.find("a:txBody", NS)
            if tx_body is None:
                continue
            tcPr = cell.element.find("a:tcPr", NS)
            cell_x = col_lefts[c]
            cell_y = row_tops[r]
            cell_w = sum(col_widths[c:c + cell.col_span])
            cell_h = sum(row_heights[r:r + cell.row_span])
            cell_xfrm = Xfrm(x=cell_x, y=cell_y, w=cell_w, h=cell_h)
            text_result = _convert_cell_text(
                tx_body, tcPr, cell_xfrm, palette, theme_fonts,
                fallback_run_props=_table_text_run_props(
                    table_style, r, theme_fonts or {},
                ),
                slide_number=slide_number,
                id_prefix=f"{id_prefix}txt",
                id_seq=grad_seq,
            )
            defs.extend(text_result.defs)
            if text_result.svg:
                body_parts.append(text_result.svg)

    # Pass C: cell borders. Drawn last so they appear on top of fills/text.
    for r, row_cells in enumerate(cells):
        for c, cell in enumerate(row_cells):
            if cell is None or cell.is_dropped:
                continue
            cell_x = col_lefts[c]
            cell_y = row_tops[r]
            cell_w = sum(col_widths[c:c + cell.col_span])
            cell_h = sum(row_heights[r:r + cell.row_span])
            tcPr = cell.element.find("a:tcPr", NS)
            for tag, x1, y1, x2, y2 in (
                ("a:lnT", cell_x, cell_y, cell_x + cell_w, cell_y),
                ("a:lnR", cell_x + cell_w, cell_y, cell_x + cell_w, cell_y + cell_h),
                ("a:lnB", cell_x, cell_y + cell_h, cell_x + cell_w, cell_y + cell_h),
                ("a:lnL", cell_x, cell_y, cell_x, cell_y + cell_h),
            ):
                line_xml = _border_line(
                    tcPr, table_style, r, c, len(rows), len(col_widths), tag,
                    x1, y1, x2, y2, palette,
                    id_prefix=f"{id_prefix}stk", id_seq=marker_seq, defs=defs,
                )
                if line_xml:
                    body_parts.append(line_xml)

    return TableResult(
        svg="\n".join(body_parts),
        defs=defs,
        native_payload=native_payload,
        native_status=native_status,
        effect_reason=effect_reason,
    )


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _column_widths_px(tbl: ET.Element) -> list[float]:
    grid = tbl.find("a:tblGrid", NS)
    if grid is None:
        return []
    widths: list[float] = []
    for col in grid.findall("a:gridCol", NS):
        w_emu = col.attrib.get("w")
        if w_emu is None:
            widths.append(0.0)
            continue
        value = _safe_emu_integer(w_emu)
        widths.append(emu_to_px(value) if value is not None else 0.0)
    return widths


def _row_height_px(row: ET.Element) -> float:
    h_emu = row.attrib.get("h")
    if h_emu is None:
        return 0.0
    value = _safe_emu_integer(h_emu)
    return emu_to_px(value) if value is not None else 0.0


def _safe_emu_integer(raw_value: str) -> int | None:
    """Return a bounded ASCII DrawingML coordinate without float overflow."""
    token = raw_value.strip(" \t\r\n")
    digits = token[1:] if token.startswith("-") else token
    if (
        not digits
        or not digits.isascii()
        or not digits.isdigit()
        or len(digits) > 10
    ):
        return None
    value = int(token)
    if not _POWERPOINT_COORD_MIN <= value <= _POWERPOINT_COORD_MAX:
        return None
    return value


def _cumulative_starts(origin: float, sizes: list[float]) -> list[float]:
    out = [origin]
    acc = origin
    for size in sizes[:-1]:
        acc += size
        out.append(acc)
    return out


# ---------------------------------------------------------------------------
# Cell grid
# ---------------------------------------------------------------------------

@dataclass
class _CellSlot:
    """Per-grid-position resolution of <a:tc> attributes."""

    element: ET.Element
    col_span: int = 1
    row_span: int = 1
    is_dropped: bool = False  # True for h/vMerge slaves: don't paint anything


@dataclass(frozen=True)
class _CanonicalMergeRegion:
    row: int
    col: int
    row_span: int
    col_span: int


def _build_cell_grid(rows: list[ET.Element], col_count: int) -> list[list[_CellSlot | None]]:
    """Map each (row, col) to the <a:tc> that owns it.

    Anchor cells (the top-left of a merge) carry col_span/row_span; merged
    slaves are marked is_dropped so the renderer skips them. Cells not part
    of any merge get span 1×1.
    """
    grid: list[list[_CellSlot | None]] = [[None] * col_count for _ in rows]

    for r, row in enumerate(rows):
        row_cells = row.findall("a:tc", NS)
        # PowerPoint writes one physical <a:tc> for every grid column, including
        # explicit hMerge/vMerge continuation cells. In that canonical form the
        # physical index is the grid column; advancing by gridSpan would consume
        # the continuation cell twice and shift every following cell left.
        explicit_grid = len(row_cells) >= col_count
        c = 0
        for physical_col, tc in enumerate(row_cells):
            if explicit_grid:
                c = physical_col
            else:
                # Retain best-effort support for compact/non-canonical rows that
                # omit explicit merge continuation cells.
                while c < col_count and grid[r][c] is not None:
                    c += 1
            if c >= col_count:
                break

            grid_span = _safe_int(tc.attrib.get("gridSpan"), 1)
            row_span = _safe_int(tc.attrib.get("rowSpan"), 1)
            h_merge = ooxml_bool(tc.attrib.get("hMerge"))
            v_merge = ooxml_bool(tc.attrib.get("vMerge"))

            if h_merge or v_merge:
                # Merge slaves are physical cells but have no independent paint.
                grid[r][c] = _CellSlot(element=tc, is_dropped=True)
                c += 1
                continue

            slot = _CellSlot(
                element=tc,
                col_span=max(grid_span, 1),
                row_span=max(row_span, 1),
            )
            for dr in range(slot.row_span):
                for dc in range(slot.col_span):
                    rr = r + dr
                    cc = c + dc
                    if rr >= len(rows) or cc >= col_count:
                        continue
                    if dr == 0 and dc == 0:
                        grid[rr][cc] = slot
                    else:
                        grid[rr][cc] = _CellSlot(
                            element=tc, is_dropped=True,
                        )
            c += 1 if explicit_grid else slot.col_span

    return grid


def _safe_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _strict_merge_bool(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"1", "on", "true"}:
        return True
    if normalized in {"0", "false", "off"}:
        return False
    raise ValueError("invalid OOXML boolean")


def _strict_merge_span(value: str | None) -> int:
    if value is None:
        return 1
    normalized = value.strip()
    if not normalized.isdigit():
        raise ValueError("invalid OOXML span")
    span = int(normalized)
    if span <= 0:
        raise ValueError("invalid OOXML span")
    return span


def _canonical_merge_slave_is_empty(tc: ET.Element) -> bool:
    tc_pr = tc.find("a:tcPr", NS)
    if tc_pr is None or tc_pr.attrib or list(tc_pr):
        return False
    tx_body = tc.find("a:txBody", NS)
    if tx_body is None:
        return False
    paragraph_count = 0
    for child in tx_body:
        name = child.tag.rsplit("}", 1)[-1]
        if name in {"bodyPr", "lstStyle"}:
            if child.attrib or list(child):
                return False
            continue
        if name == "p" and not child.attrib and not list(child):
            paragraph_count += 1
            continue
        return False
    return paragraph_count > 0 and not (tx_body.text or "").strip()


def _canonical_native_merge_status(
    rows: list[ET.Element],
    col_count: int,
) -> str | None:
    """Accept only explicit rectangular merge topology safe for regeneration."""
    physical_rows = [row.findall("a:tc", NS) for row in rows]
    merge_attrs = {"gridSpan", "rowSpan", "hMerge", "vMerge"}
    if not any(
        any(name in tc.attrib for name in merge_attrs)
        for row_cells in physical_rows
        for tc in row_cells
    ):
        return None
    if col_count <= 0 or any(
        len(row_cells) != col_count for row_cells in physical_rows
    ):
        return "unsupported-merge-topology"

    states: dict[tuple[int, int], tuple[ET.Element, int, int, bool, bool]] = {}
    try:
        for row_idx, row_cells in enumerate(physical_rows):
            for col_idx, tc in enumerate(row_cells):
                states[(row_idx, col_idx)] = (
                    tc,
                    _strict_merge_span(tc.get("rowSpan")),
                    _strict_merge_span(tc.get("gridSpan")),
                    _strict_merge_bool(tc.get("hMerge")),
                    _strict_merge_bool(tc.get("vMerge")),
                )
    except ValueError:
        return "unsupported-merge-topology"

    anchors: list[_CanonicalMergeRegion] = []
    for (
        (row_idx, col_idx),
        (_tc, row_span, col_span, h_merge, v_merge),
    ) in states.items():
        if not h_merge and not v_merge and (row_span > 1 or col_span > 1):
            anchors.append(
                _CanonicalMergeRegion(row_idx, col_idx, row_span, col_span)
            )

    owners: dict[tuple[int, int], _CanonicalMergeRegion] = {}
    for region in anchors:
        if (
            region.row + region.row_span > len(rows)
            or region.col + region.col_span > col_count
        ):
            return "unsupported-merge-topology"
        for covered_row in range(region.row, region.row + region.row_span):
            for covered_col in range(region.col, region.col + region.col_span):
                position = (covered_row, covered_col)
                if position in owners:
                    return "unsupported-merge-topology"
                owners[position] = region

    for (
        (row_idx, col_idx),
        (tc, row_span, col_span, h_merge, v_merge),
    ) in states.items():
        region = owners.get((row_idx, col_idx))
        if region is None:
            if h_merge or v_merge or row_span != 1 or col_span != 1:
                return "unsupported-merge-topology"
            continue

        is_anchor = row_idx == region.row and col_idx == region.col
        expected_row_span = region.row_span if row_idx == region.row else 1
        expected_col_span = region.col_span if col_idx == region.col else 1
        if (
            row_span != expected_row_span
            or col_span != expected_col_span
            or h_merge != (col_idx > region.col)
            or v_merge != (row_idx > region.row)
        ):
            return "unsupported-merge-topology"
        if not is_anchor and not _canonical_merge_slave_is_empty(tc):
            return "unsupported-merge-topology"

    return None


def _table_has_unsupported_style(tbl: ET.Element) -> bool:
    tbl_pr = tbl.find("a:tblPr", NS)
    if tbl_pr is None:
        return False
    allowed_attrs = {
        "firstRow", "bandRow", "firstCol", "lastCol", "lastRow",
        "bandCol", "rtl",
    }
    if any(name not in allowed_attrs for name in tbl_pr.attrib):
        return True
    if any(
        ooxml_bool(tbl_pr.attrib.get(name))
        for name in ("firstCol", "lastCol", "lastRow", "bandCol", "rtl")
    ):
        return True
    return any(
        child.tag.rsplit("}", 1)[-1] != "tableStyleId"
        for child in tbl_pr
    )


_DIRECT_BORDER_TAGS = {
    "lnL": "left",
    "lnR": "right",
    "lnT": "top",
    "lnB": "bottom",
}
_DIRECT_BORDER_WIDTH_MAX = 20116800
_OPAQUE_COLOR_MODIFIERS = {
    "tint",
    "shade",
    "lumMod",
    "lumOff",
    "satMod",
    "satOff",
}


def _validate_opaque_border_color(color_elem: ET.Element | None) -> None:
    if color_elem is None:
        raise ValueError("missing border color")
    name = color_elem.tag.rsplit("}", 1)[-1]
    if name not in {"srgbClr", "schemeClr"} or set(color_elem.attrib) != {"val"}:
        raise ValueError("unsupported border color")
    for modifier in color_elem:
        modifier_name = modifier.tag.rsplit("}", 1)[-1]
        if (
            modifier_name not in _OPAQUE_COLOR_MODIFIERS
            or set(modifier.attrib) != {"val"}
            or list(modifier)
        ):
            raise ValueError("unsupported border color modifier")
        value = modifier.get("val", "")
        if not value.isdigit() or not 0 <= int(value) <= 100000:
            raise ValueError("invalid border color modifier")


def _direct_border_payload(
    ln: ET.Element,
    palette: ColorPalette | None,
) -> dict[str, Any]:
    if set(ln.attrib) - {"w", "cap", "cmpd", "algn"}:
        raise ValueError("unsupported border line attribute")
    if ln.get("cap") not in {None, "flat"}:
        raise ValueError("unsupported border cap")
    if ln.get("cmpd") not in {None, "sng"}:
        raise ValueError("unsupported border compound style")
    if ln.get("algn") not in {None, "ctr"}:
        raise ValueError("unsupported border alignment")
    width_emu: int | None = None
    if "w" in ln.attrib:
        raw_width = ln.get("w", "")
        if not raw_width.isdigit():
            raise ValueError("invalid border width")
        width_emu = int(raw_width)
        if not 0 < width_emu <= _DIRECT_BORDER_WIDTH_MAX:
            raise ValueError("invalid border width")

    children = list(ln)
    child_names = [child.tag.rsplit("}", 1)[-1] for child in children]
    if child_names == ["noFill"]:
        no_fill = children[0]
        if no_fill.attrib or list(no_fill):
            raise ValueError("invalid noFill border")
        return {"style": "none"}

    decoration_names = {"round", "headEnd", "tailEnd"}
    if child_names.count("solidFill") != 1 or any(
        name not in {"solidFill", "prstDash", *decoration_names}
        for name in child_names
    ):
        raise ValueError("unsupported border paint")
    if (
        child_names.count("prstDash") > 1
        or any(child_names.count(name) > 1 for name in decoration_names)
        or width_emu is None
    ):
        raise ValueError("invalid solid border")
    dash = next(
        (child for child in children if child.tag.rsplit("}", 1)[-1] == "prstDash"),
        None,
    )
    if dash is not None and (
        dash.attrib != {"val": "solid"} or list(dash)
    ):
        raise ValueError("unsupported border dash")
    line_join = next(
        (child for child in children if child.tag.rsplit("}", 1)[-1] == "round"),
        None,
    )
    if line_join is not None and (line_join.attrib or list(line_join)):
        raise ValueError("unsupported border line join")
    for endpoint_name in ("headEnd", "tailEnd"):
        endpoint = next(
            (
                child for child in children
                if child.tag.rsplit("}", 1)[-1] == endpoint_name
            ),
            None,
        )
        if endpoint is None:
            continue
        if (
            set(endpoint.attrib) - {"type", "w", "len"}
            or endpoint.get("type") not in {None, "none"}
            or endpoint.get("w") not in {None, "med"}
            or endpoint.get("len") not in {None, "med"}
            or list(endpoint)
        ):
            raise ValueError("unsupported border endpoint")

    solid_fill = next(
        child for child in children
        if child.tag.rsplit("}", 1)[-1] == "solidFill"
    )
    if solid_fill.attrib or len(list(solid_fill)) != 1:
        raise ValueError("invalid solid border fill")
    color_elem = find_color_elem(solid_fill)
    _validate_opaque_border_color(color_elem)
    try:
        color, alpha = resolve_color(color_elem, palette)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid solid border color") from exc
    if color is None or alpha != 1.0:
        raise ValueError("border color must resolve to opaque RGB")

    width = _round_payload_number(emu_to_px(str(width_emu)))
    if width <= 0:
        raise ValueError("border width is too small")
    return {
        "style": "solid",
        "color": color,
        "width": width,
    }


def _table_has_unsupported_direct_formatting(
    tbl: ET.Element,
    palette: ColorPalette | None,
) -> bool:
    """Reject direct cell features the compact native schema cannot retain."""
    for tc in tbl.findall(".//a:tc", NS):
        if _table_cell_has_unsupported_topology(tc):
            return True
        tc_pr = tc.find("a:tcPr", NS)
        if tc_pr is not None:
            allowed_attrs = {"marL", "marR", "marT", "marB", "anchor"}
            if any(name not in allowed_attrs for name in tc_pr.attrib):
                return True
            if tc_pr.get("anchor") not in {None, "t", "ctr", "b"}:
                return True
            if any(
                child.tag.rsplit("}", 1)[-1]
                not in {"solidFill", "noFill", *_DIRECT_BORDER_TAGS}
                for child in tc_pr
            ):
                return True
            fills = [
                child for child in tc_pr
                if child.tag.rsplit("}", 1)[-1] in {"solidFill", "noFill"}
            ]
            if len(fills) > 1:
                return True
            no_fill = tc_pr.find("a:noFill", NS)
            if no_fill is not None and (no_fill.attrib or list(no_fill)):
                return True
            for border_tag in _DIRECT_BORDER_TAGS:
                borders = tc_pr.findall(f"a:{border_tag}", NS)
                if len(borders) > 1:
                    return True
                if borders:
                    try:
                        _direct_border_payload(borders[0], palette)
                    except ValueError:
                        return True
            solid_fill = tc_pr.find("a:solidFill", NS)
            if solid_fill is not None:
                if solid_fill.find(".//a:alpha", NS) is not None:
                    return True
                if _cell_fill_hex(tc_pr, palette) is None:
                    return True
        tx_body = tc.find("a:txBody", NS)
        if _text_body_has_unsupported_formatting(tx_body):
            return True
    return False


def _table_cell_has_unsupported_topology(tc: ET.Element) -> bool:
    """Accept only the closed optional txBody -> optional tcPr cell sequence."""
    if any(
        name not in {"gridSpan", "rowSpan", "hMerge", "vMerge"}
        for name in tc.attrib
    ):
        return True
    tx_body_tag = f"{{{NS['a']}}}txBody"
    tc_pr_tag = f"{{{NS['a']}}}tcPr"
    child_tags = [child.tag for child in tc]
    child_index = 0
    if child_tags[:1] == [tx_body_tag]:
        child_index += 1
    if child_tags[child_index:child_index + 1] == [tc_pr_tag]:
        child_index += 1
    return child_index != len(child_tags)


def _text_body_has_unsupported_formatting(tx_body: ET.Element | None) -> bool:
    if tx_body is None:
        return False
    if tx_body.attrib:
        return True

    body_pr_tag = f"{{{NS['a']}}}bodyPr"
    list_style_tag = f"{{{NS['a']}}}lstStyle"
    paragraph_tag = f"{{{NS['a']}}}p"
    body_tags = [child.tag for child in tx_body]
    body_index = 0
    if not body_tags or body_tags[0] != body_pr_tag:
        return True
    body_index += 1
    if body_index < len(body_tags) and body_tags[body_index] == list_style_tag:
        body_index += 1
    if body_index == len(body_tags) or any(
        tag != paragraph_tag for tag in body_tags[body_index:]
    ):
        return True

    relationship_prefix = f"{{{NS['r']}}}"
    forbidden_run_children = {
        f"{{{NS['a']}}}extLst",
        f"{{{NS['a']}}}hlinkClick",
        f"{{{NS['a']}}}hlinkMouseOver",
    }
    if any(
        node.tag in forbidden_run_children
        or any(name.startswith(relationship_prefix) for name in node.attrib)
        for node in tx_body.iter()
    ):
        return True

    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is None or body_pr.attrib or list(body_pr):
        return True
    list_style = tx_body.find("a:lstStyle", NS)
    if list_style is not None and (list_style.attrib or list(list_style)):
        return True
    for paragraph in tx_body.findall("a:p", NS):
        if paragraph.attrib:
            return True
        p_pr_tag = f"{{{NS['a']}}}pPr"
        run_tag = f"{{{NS['a']}}}r"
        end_r_pr_tag = f"{{{NS['a']}}}endParaRPr"
        direct_tags = [child.tag for child in paragraph]
        paragraph_index = 0
        if direct_tags[:1] == [p_pr_tag]:
            paragraph_index += 1
        while (
            paragraph_index < len(direct_tags)
            and direct_tags[paragraph_index] == run_tag
        ):
            paragraph_index += 1
        if (
            paragraph_index < len(direct_tags)
            and direct_tags[paragraph_index] == end_r_pr_tag
        ):
            paragraph_index += 1
        if paragraph_index != len(direct_tags):
            return True

        p_pr = paragraph.find("a:pPr", NS)
        if p_pr is not None:
            p_pr_tags = [child.tag.rsplit("}", 1)[-1] for child in p_pr]
            if p_pr_tags.count("defRPr") > 1 or p_pr_tags.count("buNone") > 1:
                return True
            if any(tag.startswith("bu") and tag != "buNone" for tag in p_pr_tags):
                return True

        for run in paragraph.findall("a:r", NS):
            if run.attrib:
                return True
            r_pr_tag = f"{{{NS['a']}}}rPr"
            text_tag = f"{{{NS['a']}}}t"
            run_tags = [child.tag for child in run]
            if run_tags not in ([text_tag], [r_pr_tag, text_tag]):
                return True
            text_node = run.find("a:t", NS)
            if text_node is None or list(text_node):
                return True
            allowed_text_attrs = {"{http://www.w3.org/XML/1998/namespace}space"}
            if any(name not in allowed_text_attrs for name in text_node.attrib):
                return True
    return False


def _legacy_text_body_has_unsupported_formatting(
    tx_body: ET.Element | None,
) -> bool:
    """Return the pre-P2-T4 gate so active plain payloads stay unchanged."""
    if tx_body is None:
        return False
    body_pr = tx_body.find("a:bodyPr", NS)
    if body_pr is not None and (body_pr.attrib or list(body_pr)):
        return True
    list_style = tx_body.find("a:lstStyle", NS)
    if list_style is not None and (list_style.attrib or list(list_style)):
        return True
    if (
        tx_body.find(".//a:br", NS) is not None
        or tx_body.find(".//a:fld", NS) is not None
        or tx_body.find(".//a:tab", NS) is not None
    ):
        return True

    run_signatures: set[tuple[str | None, str | None, bytes | None]] = set()
    for paragraph in tx_body.findall("a:p", NS):
        p_pr = paragraph.find("a:pPr", NS)
        alignment = p_pr.get("algn") if p_pr is not None else None
        if alignment not in {None, "l", "ctr", "r"}:
            return True
        if p_pr is not None:
            if any(name != "algn" for name in p_pr.attrib):
                return True
            if any(
                child.tag.rsplit("}", 1)[-1] not in {"defRPr", "buNone"}
                for child in p_pr
            ):
                return True

        default_r_pr = p_pr.find("a:defRPr", NS) if p_pr is not None else None
        if _legacy_run_props_have_unsupported_formatting(default_r_pr):
            return True
        for run in paragraph.findall("a:r", NS):
            r_pr = run.find("a:rPr", NS)
            if _legacy_run_props_have_unsupported_formatting(r_pr):
                return True
            run_signatures.add(
                _legacy_effective_run_signature(r_pr, default_r_pr)
            )
        end_r_pr = paragraph.find("a:endParaRPr", NS)
        if _legacy_run_props_have_unsupported_formatting(end_r_pr):
            return True
        if not paragraph.findall("a:r", NS) and end_r_pr is not None:
            run_signatures.add(
                _legacy_effective_run_signature(end_r_pr, default_r_pr)
            )

    return len(run_signatures) > 1


def _legacy_run_props_have_unsupported_formatting(
    r_pr: ET.Element | None,
) -> bool:
    if r_pr is None:
        return False
    if ooxml_bool(r_pr.get("i")):
        return True
    if r_pr.get("u") not in {None, "none"}:
        return True
    if r_pr.get("strike") not in {None, "noStrike"}:
        return True
    if r_pr.get("baseline") not in {None, "0"}:
        return True
    if r_pr.get("cap") not in {None, "none"}:
        return True
    if r_pr.get("spc") not in {None, "0"}:
        return True
    allowed_attrs = {
        "lang", "altLang", "sz", "b", "i", "u", "strike", "dirty",
        "baseline", "cap", "spc",
    }
    if any(name not in allowed_attrs for name in r_pr.attrib):
        return True
    solid_fill = r_pr.find("a:solidFill", NS)
    if solid_fill is not None and solid_fill.find(".//a:alpha", NS) is not None:
        return True
    return any(
        child.tag.rsplit("}", 1)[-1] != "solidFill"
        for child in r_pr
    )


def _legacy_effective_run_signature(
    r_pr: ET.Element | None,
    default_r_pr: ET.Element | None,
) -> tuple[str | None, str | None, bytes | None]:
    def attr(name: str) -> str | None:
        if r_pr is not None and r_pr.get(name) is not None:
            return r_pr.get(name)
        return default_r_pr.get(name) if default_r_pr is not None else None

    solid_fill = r_pr.find("a:solidFill", NS) if r_pr is not None else None
    if solid_fill is None and default_r_pr is not None:
        solid_fill = default_r_pr.find("a:solidFill", NS)
    fill_xml = (
        ET.tostring(solid_fill, encoding="utf-8")
        if solid_fill is not None else None
    )
    return attr("b"), attr("sz"), fill_xml


def _round_payload_number(value: float) -> int | float:
    rounded = round(float(value), 3)
    return int(rounded) if rounded.is_integer() else rounded


def _native_table_payload(
    tbl: ET.Element,
    xfrm: Xfrm,
    column_widths: list[float],
    row_heights: list[float],
    cells: list[list[_CellSlot | None]],
    palette: ColorPalette | None,
    theme_fonts: dict[str, str],
) -> dict[str, Any]:
    """Build the SVG native Table replacement payload for an unmerged table."""
    tbl_pr = tbl.find("a:tblPr", NS)
    payload: dict[str, Any] = {
        "x": _round_payload_number(xfrm.x),
        "y": _round_payload_number(xfrm.y),
        "width": _round_payload_number(xfrm.w),
        "height": _round_payload_number(xfrm.h),
        "strict_grid": True,
        "header_rows": (
            1 if tbl_pr is not None and ooxml_bool(tbl_pr.get("firstRow")) else 0
        ),
        "column_widths": [_round_payload_number(width) for width in column_widths],
        "row_heights": [_round_payload_number(height) for height in row_heights],
        "rows": [],
    }
    style: dict[str, Any] = {
        "band_row": bool(tbl_pr is not None and ooxml_bool(tbl_pr.get("bandRow"))),
    }
    if tbl_pr is not None:
        table_style_id = tbl_pr.findtext("a:tableStyleId", default="", namespaces=NS).strip()
        if table_style_id:
            style["table_style_id"] = table_style_id
    payload["style"] = style

    rows_payload: list[list[Any]] = []
    for row_cells in cells:
        row_payload: list[Any] = []
        for slot in row_cells:
            if slot is None or slot.is_dropped:
                row_payload.append("")
                continue
            cell_payload = _native_cell_payload(
                slot.element,
                palette,
                theme_fonts,
            )
            if slot.row_span > 1:
                cell_payload["row_span"] = slot.row_span
            if slot.col_span > 1:
                cell_payload["col_span"] = slot.col_span
            row_payload.append(cell_payload)
        rows_payload.append(row_payload)
    payload["rows"] = rows_payload
    return payload


def _native_cell_payload(
    tc: ET.Element,
    palette: ColorPalette | None,
    theme_fonts: dict[str, str],
) -> dict[str, Any]:
    tx_body = tc.find("a:txBody", NS)
    tc_pr = tc.find("a:tcPr", NS)
    paragraph_payloads = _cell_paragraph_payloads(tx_body)
    rich_paragraphs = _cell_rich_paragraph_payloads(
        tx_body,
        palette,
        theme_fonts,
    )
    if rich_paragraphs is not None:
        cell: dict[str, Any] = {"paragraphs": rich_paragraphs}
    elif len(paragraph_payloads) > 1:
        cell: dict[str, Any] = {"paragraphs": paragraph_payloads}
    else:
        cell = {"text": _cell_plain_text(tx_body)}

    fill = _cell_fill_hex(tc_pr, palette)
    if fill:
        cell["fill"] = fill
    if rich_paragraphs is None:
        color = _cell_text_color(tx_body, palette)
        if color:
            cell["color"] = color
        font_size = _cell_font_size_px(tx_body)
        if font_size:
            cell["font_size"] = font_size
    if len(paragraph_payloads) <= 1:
        align = _cell_align(tx_body)
        if align:
            cell["align"] = align
    valign = _cell_valign(tc_pr)
    if valign:
        cell["valign"] = valign
    if rich_paragraphs is None:
        bold = _cell_bold(tx_body)
        if bold is not None:
            cell["bold"] = bold
    borders = _cell_borders_payload(tc_pr, palette)
    if borders:
        cell["borders"] = borders
    _copy_cell_margins(tc_pr, cell)
    return cell


def _cell_plain_text(tx_body: ET.Element | None) -> str:
    if tx_body is None:
        return ""
    paragraphs: list[str] = []
    for paragraph in tx_body.findall("a:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _cell_paragraph_payloads(
    tx_body: ET.Element | None,
) -> list[str | dict[str, str]]:
    if tx_body is None:
        return []
    payloads: list[str | dict[str, str]] = []
    for paragraph in tx_body.findall("a:p", NS):
        text = "".join(node.text or "" for node in paragraph.findall(".//a:t", NS))
        p_pr = paragraph.find("a:pPr", NS)
        align = p_pr.get("algn") if p_pr is not None else None
        if align in {"l", "ctr", "r"}:
            payloads.append({"text": text, "align": align})
        else:
            payloads.append(text)
    return payloads


def _effective_run_attr(
    r_pr: ET.Element | None,
    default_r_pr: ET.Element | None,
    name: str,
) -> str | None:
    if r_pr is not None and r_pr.get(name) is not None:
        return r_pr.get(name)
    return default_r_pr.get(name) if default_r_pr is not None else None


def _effective_run_child(
    r_pr: ET.Element | None,
    default_r_pr: ET.Element | None,
    name: str,
) -> ET.Element | None:
    child = r_pr.find(f"a:{name}", NS) if r_pr is not None else None
    if child is not None:
        return child
    return default_r_pr.find(f"a:{name}", NS) if default_r_pr is not None else None


def _native_run_font_family(
    r_pr: ET.Element | None,
    default_r_pr: ET.Element | None,
    theme_fonts: dict[str, str],
) -> str | None:
    faces: list[str] = []
    for tag in ("latin", "ea"):
        node = _effective_run_child(r_pr, default_r_pr, tag)
        raw_face = node.get("typeface") if node is not None else None
        face = _resolve_theme_typeface(raw_face, theme_fonts)
        if face and face not in faces:
            faces.append(face)
    if len(faces) != 1:
        return None
    face = faces[0].strip()
    return face if face and "," not in face else None


def _native_run_payload(
    run: ET.Element,
    default_r_pr: ET.Element | None,
    palette: ColorPalette | None,
    theme_fonts: dict[str, str],
) -> dict[str, Any]:
    r_pr = run.find("a:rPr", NS)
    text = run.findtext("a:t", default="", namespaces=NS)
    payload: dict[str, Any] = {"text": text}

    for source, target in (("b", "bold"), ("i", "italic")):
        raw = _effective_run_attr(r_pr, default_r_pr, source)
        if raw is not None:
            payload[target] = ooxml_bool(raw)

    underline = _effective_run_attr(r_pr, default_r_pr, "u")
    if underline is not None:
        payload["underline"] = underline != "none"
    strike = _effective_run_attr(r_pr, default_r_pr, "strike")
    if strike is not None:
        payload["strike"] = strike != "noStrike"

    font_size = _canonical_source_font_size_px(
        _effective_run_attr(r_pr, default_r_pr, "sz")
    )
    if font_size is not None:
        payload["font_size"] = font_size

    solid_fill = _effective_run_child(r_pr, default_r_pr, "solidFill")
    if solid_fill is not None and not _solid_fill_is_unsafe(solid_fill, palette):
        try:
            color, _alpha = resolve_color(find_color_elem(solid_fill), palette)
        except (AttributeError, OverflowError, TypeError, ValueError):
            color = None
        if color:
            payload["color"] = color

    font_family = _native_run_font_family(
        r_pr,
        default_r_pr,
        theme_fonts,
    )
    if font_family:
        payload["font_family"] = font_family

    for source, target in (("lang", "lang"), ("altLang", "alt_lang")):
        language = _effective_run_attr(r_pr, default_r_pr, source)
        if language and language.strip():
            payload[target] = language.strip()
    return payload


def _cell_rich_paragraph_payloads(
    tx_body: ET.Element | None,
    palette: ColorPalette | None,
    theme_fonts: dict[str, str],
) -> list[dict[str, Any]] | None:
    """Materialize runs only when the legacy plain contract was insufficient."""
    if tx_body is None or not _legacy_text_body_has_unsupported_formatting(tx_body):
        return None

    paragraphs: list[tuple[str | None, list[dict[str, Any]]]] = []
    style_signatures: set[tuple[tuple[str, Any], ...]] = set()
    needs_runs = False
    run_only_fields = {
        "italic", "underline", "strike", "font_family", "lang", "alt_lang",
    }
    for paragraph in tx_body.findall("a:p", NS):
        p_pr = paragraph.find("a:pPr", NS)
        align = p_pr.get("algn") if p_pr is not None else None
        if align not in {"l", "ctr", "r"}:
            align = None
        default_r_pr = p_pr.find("a:defRPr", NS) if p_pr is not None else None
        runs = [
            _native_run_payload(run, default_r_pr, palette, theme_fonts)
            for run in paragraph.findall("a:r", NS)
        ]
        paragraphs.append((align, runs))
        for run in runs:
            style = tuple(sorted((key, value) for key, value in run.items() if key != "text"))
            style_signatures.add(style)
            if run_only_fields.intersection(run):
                needs_runs = True

    if len(style_signatures) > 1:
        needs_runs = True
    if not needs_runs:
        return None

    payloads: list[dict[str, Any]] = []
    for align, runs in paragraphs:
        paragraph_payload: dict[str, Any]
        if runs:
            paragraph_payload = {"runs": runs}
        else:
            paragraph_payload = {"text": ""}
        if align is not None:
            paragraph_payload["align"] = align
        payloads.append(paragraph_payload)
    return payloads


def _cell_fill_hex(tc_pr: ET.Element | None, palette: ColorPalette | None) -> str | None:
    fill = resolve_fill(tc_pr, palette)
    color = fill.attrs.get("fill") if fill.attrs else None
    if color and color.startswith("#"):
        return color
    return None


def _cell_text_color(tx_body: ET.Element | None, palette: ColorPalette | None) -> str | None:
    for r_pr in _text_run_props_in_priority(tx_body):
        solid_fill = r_pr.find("a:solidFill", NS)
        if solid_fill is not None and not _solid_fill_is_unsafe(solid_fill, palette):
            try:
                color, _alpha = resolve_color(find_color_elem(solid_fill), palette)
            except (AttributeError, OverflowError, TypeError, ValueError):
                continue
            if color:
                return color
    return None


def _cell_font_size_px(tx_body: ET.Element | None) -> int | float | None:
    for r_pr in _text_run_props_in_priority(tx_body):
        size = _canonical_source_font_size_px(r_pr.get("sz"))
        if size is not None:
            return size
    return None


def _canonical_source_font_size_px(raw_size: str | None) -> int | float | None:
    """Return a writer-stable font size for one bounded DrawingML token."""
    if (
        raw_size is None
        or not raw_size.isascii()
        or not raw_size.isdigit()
        or len(raw_size) > 6
    ):
        return None
    size_hpt = int(raw_size)
    if not 100 <= size_hpt <= 400000:
        return None
    # The writer emits sizes at 0.1pt precision; canonicalize on first import
    # so source and native reimport payloads stay stable.
    canonical_hpt = round(size_hpt / 10) * 10
    return _round_payload_number(hundredths_pt_to_px(canonical_hpt))


def _cell_align(tx_body: ET.Element | None) -> str | None:
    if tx_body is None:
        return None
    p_pr = tx_body.find("a:p/a:pPr", NS)
    align = p_pr.get("algn") if p_pr is not None else None
    if align in {"l", "ctr", "r"}:
        return align
    return None


def _cell_valign(tc_pr: ET.Element | None) -> str | None:
    anchor = tc_pr.get("anchor") if tc_pr is not None else None
    return {
        "t": "top",
        "ctr": "middle",
        "b": "bottom",
    }.get(anchor)


def _cell_bold(tx_body: ET.Element | None) -> bool | None:
    for r_pr in _text_run_props_in_priority(tx_body):
        if r_pr.get("b") is not None:
            return ooxml_bool(r_pr.get("b"))
    return None


def _cell_borders_payload(
    tc_pr: ET.Element | None,
    palette: ColorPalette | None,
) -> dict[str, dict[str, Any]]:
    if tc_pr is None:
        return {}
    borders: dict[str, dict[str, Any]] = {}
    for border_tag, side in _DIRECT_BORDER_TAGS.items():
        ln = tc_pr.find(f"a:{border_tag}", NS)
        if ln is not None:
            borders[side] = _direct_border_payload(ln, palette)
    return borders


def _text_run_props_in_priority(tx_body: ET.Element | None) -> list[ET.Element]:
    if tx_body is None:
        return []
    props: list[ET.Element] = []
    for path in (".//a:r/a:rPr", ".//a:pPr/a:defRPr", ".//a:endParaRPr"):
        r_pr = tx_body.find(path, NS)
        if r_pr is not None:
            props.append(r_pr)
    return props


def _copy_cell_margins(tc_pr: ET.Element | None, cell: dict[str, Any]) -> None:
    if tc_pr is None:
        return
    for source, target in (
        ("marL", "padding_left"),
        ("marR", "padding_right"),
        ("marT", "padding_top"),
        ("marB", "padding_bottom"),
    ):
        if source not in tc_pr.attrib:
            continue
        value = _safe_emu_integer(tc_pr.attrib[source])
        if value is None or value < 0:
            continue
        cell[target] = _round_payload_number(emu_to_px(value))


# ---------------------------------------------------------------------------
# Cell text & borders
# ---------------------------------------------------------------------------

def _convert_cell_text(
    tx_body: ET.Element,
    tcPr: ET.Element | None,
    cell_xfrm: Xfrm,
    palette: ColorPalette | None,
    theme_fonts: dict[str, str] | None,
    *,
    fallback_run_props: tuple[ET.Element, ...],
    slide_number: int | None,
    id_prefix: str,
    id_seq: list[int] | None,
):
    """Render cell text. PowerPoint's <a:tcPr> can override txBody insets via
    its own marL/marR/marT/marB attrs; convert_txbody reads from <a:bodyPr>,
    so we materialise a synthetic bodyPr when tcPr has its own insets. Invalid
    malformed source font-size and run-color values are removed from a private
    render copy; they have already been omitted from the native payload and
    must not crash fallback SVG generation."""
    render_tx_body = tx_body
    run_props = [
        node
        for node in tx_body.iter()
        if node.tag in {
            f"{{{NS['a']}}}defRPr",
            f"{{{NS['a']}}}endParaRPr",
            f"{{{NS['a']}}}rPr",
        }
    ]
    if any(
        _run_props_need_render_normalization(node, palette)
        for node in run_props
    ):
        render_tx_body = copy.deepcopy(tx_body)
        for node in render_tx_body.iter():
            if node.tag not in {
                f"{{{NS['a']}}}defRPr",
                f"{{{NS['a']}}}endParaRPr",
                f"{{{NS['a']}}}rPr",
            }:
                continue
            if (
                node.get("sz") is not None
                and _canonical_source_font_size_px(node.get("sz")) is None
            ):
                node.attrib.pop("sz", None)
            solid_fill = node.find("a:solidFill", NS)
            if solid_fill is not None and _solid_fill_is_unsafe(solid_fill, palette):
                node.remove(solid_fill)

    body_pr = render_tx_body.find("a:bodyPr", NS)
    overrides = _tcPr_inset_overrides(tcPr)
    saved: dict[str, str | None] = {}
    if overrides and body_pr is not None:
        for key, val in overrides.items():
            saved[key] = body_pr.attrib.get(key)
            body_pr.set(key, val)
    try:
        try:
            return convert_txbody(
                render_tx_body, cell_xfrm, palette, theme_fonts=theme_fonts,
                fallback_run_props=fallback_run_props,
                slide_number=slide_number,
                id_prefix=id_prefix,
                id_seq=id_seq,
            )
        except (AttributeError, OverflowError, TypeError, ValueError):
            plain_tx_body = _plain_table_text_body(render_tx_body, overrides)
            return convert_txbody(
                plain_tx_body, cell_xfrm, palette, theme_fonts=theme_fonts,
                fallback_run_props=(),
                slide_number=slide_number,
                id_prefix=id_prefix,
                id_seq=id_seq,
            )
    finally:
        if overrides and body_pr is not None:
            for key, prior in saved.items():
                if prior is None:
                    body_pr.attrib.pop(key, None)
                else:
                    body_pr.set(key, prior)


def _run_props_need_render_normalization(
    run_props: ET.Element,
    palette: ColorPalette | None,
) -> bool:
    size = run_props.get("sz")
    if size is not None and _canonical_source_font_size_px(size) is None:
        return True
    solid_fill = run_props.find("a:solidFill", NS)
    return solid_fill is not None and _solid_fill_is_unsafe(solid_fill, palette)


def _solid_fill_is_unsafe(
    solid_fill: ET.Element,
    palette: ColorPalette | None,
) -> bool:
    color = find_color_elem(solid_fill)
    if color is not None and not _color_numeric_tokens_are_finite(color):
        return True
    try:
        resolve_color(color, palette)
    except (AttributeError, OverflowError, TypeError, ValueError):
        return True
    return False


def _color_numeric_tokens_are_finite(color: ET.Element) -> bool:
    """Reject non-finite numeric tokens before the resolver can clamp them."""
    base_numeric_attrs = {
        "hslClr": ("hue", "sat", "lum"),
        "scrgbClr": ("r", "g", "b"),
    }
    modifier_tags = {
        "alpha", "alphaMod", "alphaOff", "hueMod", "hueOff",
        "lumMod", "lumOff", "satMod", "satOff", "shade", "tint",
    }
    for node in color.iter():
        name = node.tag.rsplit("}", 1)[-1]
        attrs = base_numeric_attrs.get(name, ())
        if name in modifier_tags:
            attrs = ("val",)
        for attr in attrs:
            raw = node.get(attr)
            if raw is None:
                return False
            try:
                value = float(raw)
            except (OverflowError, TypeError, ValueError):
                return False
            if not math.isfinite(value):
                return False
    return True


def _plain_table_text_body(
    tx_body: ET.Element,
    overrides: dict[str, str],
) -> ET.Element:
    """Return a text-preserving style-free fallback after malformed styling."""
    plain = copy.deepcopy(tx_body)
    body_pr = plain.find("a:bodyPr", NS)
    if body_pr is None:
        body_pr = ET.Element(f"{{{NS['a']}}}bodyPr")
        plain.insert(0, body_pr)
    body_pr.clear()
    for key, value in overrides.items():
        body_pr.set(key, value)
    list_style = plain.find("a:lstStyle", NS)
    if list_style is not None:
        list_style.clear()
    for paragraph in plain.findall("a:p", NS):
        p_pr = paragraph.find("a:pPr", NS)
        if p_pr is not None:
            align = p_pr.get("algn")
            p_pr.clear()
            if align in {"l", "ctr", "r"}:
                p_pr.set("algn", align)
    for path in (".//a:rPr", ".//a:defRPr", ".//a:endParaRPr"):
        for run_props in plain.findall(path, NS):
            run_props.clear()
    return plain


def _tcPr_inset_overrides(tcPr: ET.Element | None) -> dict[str, str]:
    if tcPr is None:
        return {}
    out: dict[str, str] = {}
    for src, dst in (("marL", "lIns"), ("marR", "rIns"),
                     ("marT", "tIns"), ("marB", "bIns")):
        if src not in tcPr.attrib:
            continue
        value = _safe_emu_integer(tcPr.attrib[src])
        if value is not None and value >= 0:
            out[dst] = str(value)
    return out


def _border_line(
    tcPr: ET.Element | None,
    table_style: _TableStyleContext,
    row_index: int,
    col_index: int,
    row_count: int,
    col_count: int,
    tag: str,
    x1: float, y1: float, x2: float, y2: float,
    palette: ColorPalette | None,
    *,
    id_prefix: str,
    id_seq: list[int],
    defs: list[str],
) -> str:
    """Emit a single border <line> for a given cell side, or empty string when
    that side is explicitly noFill / not specified."""
    ln = tcPr.find(tag, NS) if tcPr is not None else None
    if ln is not None:
        return _line_element_to_svg(
            ln, x1, y1, x2, y2, palette,
            id_prefix=id_prefix, id_seq=id_seq, defs=defs,
        )

    # Draw inherited shared edges once, from the upper/left cell.  This keeps
    # a specific firstRow bottom border from being painted over by the next
    # row's whole-table top border.  A direct border above still wins because
    # it is handled before this de-duplication gate.
    if (tag == "a:lnT" and row_index > 0) or (
        tag == "a:lnL" and col_index > 0
    ):
        return ""

    for region_name, region in table_style.regions_for_row(row_index):
        for border_name in _table_style_border_names(
            region_name, row_index, col_index, row_count, col_count, tag,
        ):
            ln = region.find(
                f"a:tcStyle/a:tcBdr/a:{border_name}/a:ln", NS,
            )
            if ln is not None:
                return _line_element_to_svg(
                    ln, x1, y1, x2, y2, palette,
                    id_prefix=id_prefix, id_seq=id_seq, defs=defs,
                )
    return ""


def _table_style_border_names(
    region_name: str,
    row_index: int,
    col_index: int,
    row_count: int,
    col_count: int,
    tag: str,
) -> tuple[str, ...]:
    side_names = {
        "a:lnT": ("top", "insideH", row_index > 0),
        "a:lnR": ("right", "insideV", col_index < col_count - 1),
        "a:lnB": ("bottom", "insideH", row_index < row_count - 1),
        "a:lnL": ("left", "insideV", col_index > 0),
    }
    side, inside, is_internal = side_names[tag]
    if region_name == "wholeTbl" and is_internal:
        return inside, side
    return side, inside


def _line_element_to_svg(
    ln: ET.Element,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    palette: ColorPalette | None,
    *,
    id_prefix: str,
    id_seq: list[int],
    defs: list[str],
) -> str:
    # Skip explicit no-line.
    if ln.find("a:noFill", NS) is not None:
        return ""

    stroke = resolve_stroke(
        # resolve_stroke expects a parent that contains <a:ln>; wrap so it
        # finds our tag's own children as the line spec.
        _make_ln_wrapper(ln),
        palette,
        id_prefix=id_prefix,
        id_seq=id_seq,
    )
    defs.extend(stroke.defs)
    attrs = stroke.attrs
    if not attrs.get("stroke"):
        return ""
    attr_str = "".join(f' {k}="{v}"' for k, v in attrs.items())
    return (
        f'<line x1="{fmt_num(x1)}" y1="{fmt_num(y1)}" '
        f'x2="{fmt_num(x2)}" y2="{fmt_num(y2)}"{attr_str}/>'
    )


def _make_ln_wrapper(ln: ET.Element) -> ET.Element:
    """resolve_stroke walks for ``parent.find('a:ln')``; tcPr borders ARE the
    <a:ln> already, so wrap them in a synthetic parent that points back at
    the original element under the expected tag.
    """
    wrapper = ET.Element(f"{{{NS['a']}}}wrapper")
    proxy = ET.SubElement(wrapper, f"{{{NS['a']}}}ln")
    # Carry attributes (e.g. w="...") and children (solidFill, prstDash, ...).
    for k, v in ln.attrib.items():
        proxy.set(k, v)
    for child in list(ln):
        proxy.append(child)
    return wrapper
