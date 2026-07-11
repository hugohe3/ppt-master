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
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET

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
from .txbody_to_svg import convert_txbody


BUILTIN_MEDIUM_STYLE_2_ACCENT_1 = "{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"

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
    """Composite render output plus optional native table metadata."""

    svg: str = ""
    defs: list[str] = None
    native_payload: dict[str, Any] | None = None
    native_status: str | None = None

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
    if xfrm.rot or xfrm.flip_h or xfrm.flip_v:
        native_status = "unsupported-native-transform"
    elif _table_has_merges(rows):
        native_status = "unsupported-merge"
    elif len(rows) > 1000 or len(col_widths) > 1000:
        native_status = "unsupported-table-size"
    elif (
        any(width < 0 for width in col_widths)
        or any(height < 0 for height in row_heights)
        or sum(col_widths) <= 0
        or sum(row_heights) <= 0
    ):
        native_status = "unsupported-table-geometry"
    elif _table_has_unsupported_style(tbl):
        native_status = "unsupported-table-style"
    elif _table_has_unsupported_direct_formatting(tbl, palette):
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
            continue
        try:
            widths.append(emu_to_px(int(w_emu)))
        except ValueError:
            widths.append(0.0)
    return widths


def _row_height_px(row: ET.Element) -> float:
    h_emu = row.attrib.get("h")
    if h_emu is None:
        return 0.0
    try:
        return emu_to_px(int(h_emu))
    except ValueError:
        return 0.0


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


def _table_has_merges(rows: list[ET.Element]) -> bool:
    """Return True when the table uses merged cells."""
    for row in rows:
        for tc in row.findall("a:tc", NS):
            if ooxml_bool(tc.attrib.get("hMerge")) or ooxml_bool(tc.attrib.get("vMerge")):
                return True
            if _safe_int(tc.attrib.get("gridSpan"), 1) > 1:
                return True
            if _safe_int(tc.attrib.get("rowSpan"), 1) > 1:
                return True
    return False


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


def _table_has_unsupported_direct_formatting(
    tbl: ET.Element,
    palette: ColorPalette | None,
) -> bool:
    """Reject direct cell features the compact native schema cannot retain."""
    for tc in tbl.findall(".//a:tc", NS):
        tc_pr = tc.find("a:tcPr", NS)
        if tc_pr is not None:
            allowed_attrs = {"marL", "marR", "marT", "marB", "anchor"}
            if any(name not in allowed_attrs for name in tc_pr.attrib):
                return True
            if tc_pr.get("anchor") not in {None, "t", "ctr", "b"}:
                return True
            if any(
                child.tag.rsplit("}", 1)[-1] != "solidFill"
                for child in tc_pr
            ):
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
        if (
            tx_body is not None
            and tx_body.find(".//a:solidFill", NS) is not None
            and _cell_text_color(tx_body, palette) is None
        ):
            return True
    return False


def _text_body_has_unsupported_formatting(tx_body: ET.Element | None) -> bool:
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

    paragraphs = tx_body.findall("a:p", NS)
    if len(paragraphs) > 1:
        return True

    alignments: set[str | None] = set()
    run_signatures: set[tuple[str | None, str | None, bytes | None]] = set()
    for paragraph in paragraphs:
        p_pr = paragraph.find("a:pPr", NS)
        alignment = p_pr.get("algn") if p_pr is not None else None
        if alignment not in {None, "l", "ctr", "r"}:
            return True
        alignments.add(alignment)
        if p_pr is not None:
            if any(name != "algn" for name in p_pr.attrib):
                return True
            if any(
                child.tag.rsplit("}", 1)[-1] not in {"defRPr", "buNone"}
                for child in p_pr
            ):
                return True

        default_r_pr = p_pr.find("a:defRPr", NS) if p_pr is not None else None
        if _run_props_have_unsupported_formatting(default_r_pr):
            return True
        for run in paragraph.findall("a:r", NS):
            r_pr = run.find("a:rPr", NS)
            if _run_props_have_unsupported_formatting(r_pr):
                return True
            run_signatures.add(_effective_run_signature(r_pr, default_r_pr))
        end_r_pr = paragraph.find("a:endParaRPr", NS)
        if _run_props_have_unsupported_formatting(end_r_pr):
            return True
        if not paragraph.findall("a:r", NS) and end_r_pr is not None:
            run_signatures.add(_effective_run_signature(end_r_pr, default_r_pr))

    return len(alignments) > 1 or len(run_signatures) > 1


def _run_props_have_unsupported_formatting(r_pr: ET.Element | None) -> bool:
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


def _effective_run_signature(
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
) -> dict[str, Any]:
    """Build the SVG data-pptx-native payload for an unmerged table."""
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
            row_payload.append(_native_cell_payload(slot.element, palette))
        rows_payload.append(row_payload)
    payload["rows"] = rows_payload
    return payload


def _native_cell_payload(tc: ET.Element, palette: ColorPalette | None) -> dict[str, Any]:
    tx_body = tc.find("a:txBody", NS)
    tc_pr = tc.find("a:tcPr", NS)
    cell: dict[str, Any] = {"text": _cell_plain_text(tx_body)}

    fill = _cell_fill_hex(tc_pr, palette)
    if fill:
        cell["fill"] = fill
    color = _cell_text_color(tx_body, palette)
    if color:
        cell["color"] = color
    font_size = _cell_font_size_px(tx_body)
    if font_size:
        cell["font_size"] = font_size
    align = _cell_align(tx_body)
    if align:
        cell["align"] = align
    valign = _cell_valign(tc_pr)
    if valign:
        cell["valign"] = valign
    bold = _cell_bold(tx_body)
    if bold is not None:
        cell["bold"] = bold
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


def _cell_fill_hex(tc_pr: ET.Element | None, palette: ColorPalette | None) -> str | None:
    fill = resolve_fill(tc_pr, palette)
    color = fill.attrs.get("fill") if fill.attrs else None
    if color and color.startswith("#"):
        return color
    return None


def _cell_text_color(tx_body: ET.Element | None, palette: ColorPalette | None) -> str | None:
    for r_pr in _text_run_props_in_priority(tx_body):
        solid_fill = r_pr.find("a:solidFill", NS)
        if solid_fill is not None:
            color, _alpha = resolve_color(find_color_elem(solid_fill), palette)
            return color
    return None


def _cell_font_size_px(tx_body: ET.Element | None) -> int | float | None:
    for r_pr in _text_run_props_in_priority(tx_body):
        if not r_pr.get("sz"):
            continue
        size = hundredths_pt_to_px(r_pr.get("sz"))
        if size > 0:
            return _round_payload_number(size)
    return None


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
        cell[target] = _round_payload_number(emu_to_px(tc_pr.attrib[source]))


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
    so we materialise a synthetic bodyPr by mutating the txBody in place when
    tcPr has its own insets. (We undo the mutation afterwards to keep the
    slide tree pristine for any subsequent passes.)"""
    body_pr = tx_body.find("a:bodyPr", NS)
    overrides = _tcPr_inset_overrides(tcPr)
    saved: dict[str, str | None] = {}
    if overrides and body_pr is not None:
        for key, val in overrides.items():
            saved[key] = body_pr.attrib.get(key)
            body_pr.set(key, val)
    try:
        return convert_txbody(
            tx_body, cell_xfrm, palette, theme_fonts=theme_fonts,
            fallback_run_props=fallback_run_props,
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


def _tcPr_inset_overrides(tcPr: ET.Element | None) -> dict[str, str]:
    if tcPr is None:
        return {}
    out: dict[str, str] = {}
    for src, dst in (("marL", "lIns"), ("marR", "rIns"),
                     ("marT", "tIns"), ("marB", "bIns")):
        if src in tcPr.attrib:
            out[dst] = tcPr.attrib[src]
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
