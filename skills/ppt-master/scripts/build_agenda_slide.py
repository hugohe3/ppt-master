#!/usr/bin/env python3
"""
PPT Master - Agenda Slide Builder

Build one clickable agenda page from the current SVG roster titles and write
it into ``svg_output/``. Each row jumps to its target slide through the
existing ``#slide-N`` hyperlink contract.

Usage:
    python3 scripts/build_agenda_slide.py <project_path>
    python3 scripts/build_agenda_slide.py <project_path> --insert-after 1
    python3 scripts/build_agenda_slide.py <project_path> --heading Agenda
    python3 scripts/build_agenda_slide.py <project_path> --dry-run

Examples:
    python3 scripts/build_agenda_slide.py projects/demo
    python3 scripts/build_agenda_slide.py projects/demo --include-roles content,section

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from slide_roster import discover_slide_svgs  # noqa: E402

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
DEFAULT_INCLUDE_ROLES = ("content", "section")
DEFAULT_CANVAS = (1280, 720)
_NUMBER_PREFIX_RE = re.compile(r"^(\d+)[_-]?")
_STYLE_SIZE_RE = re.compile(r"font-size\s*:\s*([0-9]+(?:\.[0-9]+)?)")
_WS_RE = re.compile(r"\s+")
_ROLE_SPLIT_RE = re.compile(r"[,\s]+")
_AGENDA_STEM_RE = re.compile(r"(?:^|[_-])agenda$", re.IGNORECASE)


@dataclass(frozen=True)
class RosterPage:
    """One existing SVG page in roster order."""

    index: int
    path: Path
    title: str
    role: str
    canvas: tuple[int, int]


@dataclass(frozen=True)
class AgendaItem:
    """One agenda row and the slide it should open."""

    title: str
    source: str
    role: str
    target_slide: int


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def title_from_filename(name: str) -> str:
    """Turn ``03_market_overview.svg`` into a readable title."""
    stem = Path(name).stem
    stem = _NUMBER_PREFIX_RE.sub("", stem)
    stem = stem.replace("-", " ").replace("_", " ")
    return _collapse_ws(stem).title() or Path(name).stem


def _font_size(elem: ET.Element) -> float:
    raw = elem.get("font-size")
    if raw:
        try:
            return float(raw.replace("px", "").strip())
        except ValueError:
            pass
    style = elem.get("style") or ""
    match = _STYLE_SIZE_RE.search(style)
    if match:
        return float(match.group(1))
    return 0.0


def _page_role(root: ET.Element) -> str:
    return (root.get("data-pptx-page-role") or "").strip().lower()


def read_canvas(root: ET.Element) -> tuple[int, int]:
    """Return the page canvas from viewBox or width/height."""
    view_box = (root.get("viewBox") or "").replace(",", " ").split()
    if len(view_box) == 4:
        try:
            width = int(float(view_box[2]))
            height = int(float(view_box[3]))
            if width > 0 and height > 0:
                return width, height
        except ValueError:
            pass
    try:
        width = int(float((root.get("width") or "").replace("px", "")))
        height = int(float((root.get("height") or "").replace("px", "")))
    except ValueError:
        return DEFAULT_CANVAS
    if width > 0 and height > 0:
        return width, height
    return DEFAULT_CANVAS


def extract_page_title(path: Path) -> tuple[str, str, tuple[int, int]]:
    """Return ``(title, page_role, canvas)`` for one SVG page."""
    root = ET.parse(path).getroot()
    role = _page_role(root)
    canvas = read_canvas(root)
    best = ""
    best_size = -1.0
    for elem in root.iter():
        if _local_name(elem.tag) != "text":
            continue
        structural = (elem.get("data-pptx-role") or "").strip().lower()
        if structural in {"footer", "header", "page-number", "chrome", "watermark"}:
            continue
        text = _collapse_ws("".join(elem.itertext()))
        if not text:
            continue
        size = _font_size(elem)
        if size > best_size or (size == best_size and len(text) > len(best)):
            best = text
            best_size = size
    title = best or title_from_filename(path.name)
    return title, role, canvas


def load_roster(project_path: Path) -> list[RosterPage]:
    """Load the project's SVG roster with titles and roles."""
    svg_dir = project_path / "svg_output"
    if not svg_dir.is_dir():
        raise FileNotFoundError(f"svg_output directory not found: {svg_dir}")
    pages: list[RosterPage] = []
    for index, path in enumerate(discover_slide_svgs(svg_dir), start=1):
        title, role, canvas = extract_page_title(path)
        pages.append(
            RosterPage(
                index=index,
                path=path,
                title=title,
                role=role,
                canvas=canvas,
            )
        )
    if not pages:
        raise RuntimeError(f"No SVG pages found in {svg_dir}")
    return pages


def is_agenda_page(page: RosterPage) -> bool:
    """Return whether a roster page is an agenda/toc page this tool owns."""
    if page.role == "toc":
        return True
    stem = _NUMBER_PREFIX_RE.sub("", page.path.stem)
    return bool(_AGENDA_STEM_RE.search(stem))


def parse_roles(raw: str | None) -> tuple[str, ...]:
    """Parse a comma/space role list; ``all`` keeps every non-agenda page."""
    if raw is None or not raw.strip():
        return DEFAULT_INCLUDE_ROLES
    parts = tuple(
        part.lower()
        for part in _ROLE_SPLIT_RE.split(raw.strip())
        if part
    )
    if not parts:
        return DEFAULT_INCLUDE_ROLES
    return parts


def select_source_pages(
    pages: list[RosterPage],
    include_roles: Iterable[str],
    *,
    skip: RosterPage | None = None,
) -> list[RosterPage]:
    """Choose pages that become agenda rows."""
    roles = {role.lower() for role in include_roles}
    include_all = "all" in roles
    selected: list[RosterPage] = []
    for page in pages:
        if skip is not None and page.path == skip.path:
            continue
        if include_all:
            selected.append(page)
            continue
        if is_agenda_page(page):
            continue
        if page.role in roles or (not page.role and "content" in roles):
            selected.append(page)
    return selected


def plan_agenda(
    pages: list[RosterPage],
    *,
    include_roles: Iterable[str] = DEFAULT_INCLUDE_ROLES,
    insert_after: int | None = None,
    replace_existing: bool = True,
) -> tuple[list[AgendaItem], int, RosterPage | None, tuple[int, int]]:
    """Plan agenda rows, the 1-based write slot, and any page being replaced."""
    existing = next((page for page in pages if is_agenda_page(page)), None)
    replace = replace_existing and existing is not None and insert_after is None
    if replace and existing is not None:
        write_index = existing.index
        sources = select_source_pages(pages, include_roles, skip=existing)
        items = [
            AgendaItem(
                title=page.title,
                source=page.path.name,
                role=page.role,
                target_slide=page.index,
            )
            for page in sources
        ]
        return items, write_index, existing, existing.canvas

    slot_after = 1 if insert_after is None else insert_after
    if slot_after < 0 or slot_after > len(pages):
        raise ValueError(
            f"--insert-after must be between 0 and {len(pages)}, got {slot_after}"
        )
    write_index = slot_after + 1
    sources = select_source_pages(pages, include_roles, skip=existing)
    items = []
    for page in sources:
        target = page.index if page.index < write_index else page.index + 1
        items.append(
            AgendaItem(
                title=page.title,
                source=page.path.name,
                role=page.role,
                target_slide=target,
            )
        )
    canvas = pages[0].canvas if pages else DEFAULT_CANVAS
    return items, write_index, None, canvas


def render_agenda_svg(
    items: list[AgendaItem],
    *,
    heading: str = "Agenda",
    canvas: tuple[int, int] = DEFAULT_CANVAS,
) -> str:
    """Render one clickable agenda page."""
    width, height = canvas
    scale = width / 1280
    margin = round(80 * scale)
    heading_size = max(28, round(40 * scale))
    heading_y = margin + heading_size
    top = heading_y + round(48 * scale)
    bottom = height - round(56 * scale)
    usable = max(80, bottom - top)
    count = max(1, len(items))
    row_gap = max(8, round(10 * scale))
    row_h = min(round(64 * scale), max(36, (usable - row_gap * (count - 1)) // count))
    label_size = max(16, min(24, row_h - 16))
    card_fill = "#E2E8F0"
    card_text = "#0F172A"
    index_fill = "#1D4ED8"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" data-pptx-page-role="toc" '
        'font-family="Arial">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#F8FAFC"/>',
        f'<text x="{margin}" y="{heading_y}" font-family="Arial" '
        f'font-size="{heading_size}" font-weight="bold" fill="#0F172A">'
        f"{escape(heading)}</text>",
    ]
    if not items:
        parts.append(
            f'<text x="{margin}" y="{top + 28}" font-family="Arial" '
            f'font-size="{label_size}" fill="#64748B">No matching pages</text>'
        )
    for offset, item in enumerate(items):
        y = top + offset * (row_h + row_gap)
        number = f"{offset + 1:02d}"
        href = quoteattr(f"#slide-{item.target_slide}")
        text_y = y + round(row_h * 0.68)
        parts.extend(
            [
                f'<a id="agenda-item-{offset + 1}" href={href}>',
                f'<rect x="{margin}" y="{y}" width="{width - 2 * margin}" '
                f'height="{row_h}" fill="{card_fill}"/>',
                f'<text x="{margin + 24}" y="{text_y}" font-family="Arial" '
                f'font-size="{label_size}" font-weight="bold" fill="{index_fill}">'
                f"{number}</text>",
                f'<text x="{margin + 88}" y="{text_y}" font-family="Arial" '
                f'font-size="{label_size}" fill="{card_text}">'
                f"{escape(item.title)}</text>",
                "</a>",
            ]
        )
    parts.append("</svg>\n")
    return "\n".join(parts)


def _pad_width(count: int) -> int:
    return max(2, len(str(count)))


def _rest_stem(path: Path) -> str:
    rest = _NUMBER_PREFIX_RE.sub("", path.stem)
    return rest or path.stem


def _resequence_roster(
    ordered: list[Path],
    desired: list[Path],
    staged: Path,
) -> None:
    """Rename roster files through a temp suffix, and keep matching notes."""
    moved: list[tuple[Path, Path]] = []
    for path in ordered:
        tmp = path.with_name(path.name + ".renaming")
        path.rename(tmp)
        moved.append((path, tmp))
    for (original, tmp), dest in zip(moved, desired):
        if tmp != dest:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp.rename(dest)
        if original == staged:
            continue
        notes_src = original.parent.parent / "notes" / f"{original.stem}.md"
        notes_dest = dest.parent.parent / "notes" / f"{dest.stem}.md"
        if notes_src.is_file() and notes_src != notes_dest:
            notes_dest.parent.mkdir(parents=True, exist_ok=True)
            notes_src.rename(notes_dest)


def write_agenda_page(
    project_path: Path,
    items: list[AgendaItem],
    write_index: int,
    pages: list[RosterPage],
    *,
    heading: str,
    canvas: tuple[int, int],
    replace: RosterPage | None,
) -> Path:
    """Write the agenda SVG and keep the roster numbered."""
    svg_dir = project_path / "svg_output"
    svg_dir.mkdir(parents=True, exist_ok=True)
    payload = render_agenda_svg(items, heading=heading, canvas=canvas)
    if replace is not None:
        replace.path.write_text(payload, encoding="utf-8")
        return replace.path

    final_count = len(pages) + 1
    width = _pad_width(final_count)
    new_path = svg_dir / f"{write_index:0{width}d}_agenda.svg"
    staged = svg_dir / ".__agenda_inserting.svg"
    staged.write_text(payload, encoding="utf-8")

    ordered: list[Path] = []
    insert_at = write_index - 1
    for page in pages:
        if len(ordered) == insert_at:
            ordered.append(staged)
        ordered.append(page.path)
    if len(ordered) == insert_at:
        ordered.append(staged)

    desired: list[Path] = []
    for index, path in enumerate(ordered, start=1):
        stem = "agenda" if path == staged else _rest_stem(path)
        desired.append(svg_dir / f"{index:0{width}d}_{stem}.svg")

    _resequence_roster(ordered, desired, staged)
    return new_path if new_path in desired else desired[insert_at]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a clickable agenda slide from the SVG roster titles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project directory that contains svg_output/")
    parser.add_argument(
        "--heading",
        default="Agenda",
        help="Title drawn on the agenda page (default: Agenda)",
    )
    parser.add_argument(
        "--include-roles",
        default="content,section",
        help="Page roles to list, comma-separated, or 'all' (default: content,section)",
    )
    parser.add_argument(
        "--insert-after",
        type=int,
        default=None,
        help="Insert after this 1-based page (0 = first). Default replaces an "
        "existing toc/agenda page, otherwise inserts after page 1.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned rows without writing files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write the plan as JSON on stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_path = Path(args.project_path).expanduser().resolve()
    try:
        pages = load_roster(project_path)
        items, write_index, replace, canvas = plan_agenda(
            pages,
            include_roles=parse_roles(args.include_roles),
            insert_after=args.insert_after,
            replace_existing=args.insert_after is None,
        )
    except (FileNotFoundError, RuntimeError, ValueError, ET.ParseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not items:
        print(
            "Error: no pages matched --include-roles; nothing to list on the agenda.",
            file=sys.stderr,
        )
        return 1

    plan = {
        "project": str(project_path),
        "heading": args.heading,
        "write_index": write_index,
        "replace": None if replace is None else replace.path.name,
        "items": [asdict(item) for item in items],
    }
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        action = "replace" if replace is not None else "insert"
        print(
            f"Agenda {action} at page {write_index} ({len(items)} link(s))",
            file=sys.stderr,
        )
        for item in items:
            print(
                f"  #slide-{item.target_slide}  {item.title}  ({item.source})",
                file=sys.stderr,
            )

    if args.dry_run:
        return 0

    written = write_agenda_page(
        project_path,
        items,
        write_index,
        pages,
        heading=args.heading,
        canvas=canvas,
        replace=replace,
    )
    print(f"Wrote {written}", file=sys.stderr)
    if not args.json:
        print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
