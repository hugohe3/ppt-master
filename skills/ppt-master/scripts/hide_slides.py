#!/usr/bin/env python3
"""
PPT Master - Hidden Slide Marker

Set or clear the native PowerPoint ``show`` flag on selected slides in a
finished PPTX. Hidden slides stay in the file and can be unhidden later;
``pptx_delivery_check.py`` already reports that state.

Usage:
    python3 scripts/hide_slides.py <presentation.pptx> --pages 5-6 -o out.pptx
    python3 scripts/hide_slides.py <presentation.pptx> --last 2 -o out.pptx
    python3 scripts/hide_slides.py <presentation.pptx> --project <project> --match appendix
    python3 scripts/hide_slides.py <presentation.pptx> --unhide-all -o out.pptx

Examples:
    python3 scripts/hide_slides.py exports/review.pptx --pages 5,6
    python3 scripts/hide_slides.py exports/review.pptx --project projects/review --match appendix

Dependencies:
    None beyond the repository PPTX helpers (standard library zip/xml).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_ooxml.ooxml import _parse_slide_refs  # noqa: E402
from slide_roster import discover_slide_svgs  # noqa: E402

configure_utf8_stdio()

_RANGE_TOKEN_RE = re.compile(r"^(\d+)(?:-(\d+))?$")
_SLIDE_OPEN_RE = re.compile(
    rb"<((?:[A-Za-z_][\w.-]*:)?)sld(?![A-Za-z])(\s[^>]*)?(/?>)",
)
_SHOW_ATTR_RE = re.compile(rb"""\sshow\s*=\s*("[^"]*"|'[^']*')""")


def parse_page_spec(spec: str, slide_count: int) -> list[int]:
    """Parse ``5,6,8-10`` into sorted unique 1-based page numbers."""
    if slide_count < 1:
        raise ValueError("presentation has no slides")
    pages: set[int] = set()
    for raw in spec.split(","):
        token = raw.strip()
        if not token:
            continue
        match = _RANGE_TOKEN_RE.fullmatch(token)
        if match is None:
            raise ValueError(f"invalid page spec {token!r}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start > end:
            start, end = end, start
        if start < 1 or end > slide_count:
            raise ValueError(
                f"page spec {token!r} is outside 1..{slide_count}"
            )
        pages.update(range(start, end + 1))
    if not pages:
        raise ValueError("page spec selected no slides")
    return sorted(pages)


def last_pages(slide_count: int, count: int) -> list[int]:
    """Return the last ``count`` 1-based page numbers."""
    if count < 1:
        raise ValueError("--last must be a positive integer")
    if slide_count < 1:
        raise ValueError("presentation has no slides")
    start = max(1, slide_count - count + 1)
    return list(range(start, slide_count + 1))


def pages_matching_stem(
    project_path: Path,
    token: str,
) -> list[int]:
    """Return 1-based roster indexes whose SVG stem contains ``token``."""
    svg_dir = project_path / "svg_output"
    if not svg_dir.is_dir():
        raise FileNotFoundError(f"svg_output directory not found: {svg_dir}")
    needle = token.casefold().strip()
    if not needle:
        raise ValueError("--match requires a non-empty token")
    hits = [
        index
        for index, path in enumerate(discover_slide_svgs(svg_dir), start=1)
        if needle in path.stem.casefold()
    ]
    if not hits:
        raise ValueError(
            f"no svg_output page stem contains {token!r}"
        )
    return hits


def set_slide_visibility(xml: bytes, *, visible: bool) -> bytes:
    """Set or clear ``show`` on the slide part root without rewriting the tree."""
    match = _SLIDE_OPEN_RE.search(xml)
    if match is None:
        raise RuntimeError("slide part has no sld root element")
    attrs = match.group(2) or b""
    closer = match.group(3)
    if visible:
        attrs = _SHOW_ATTR_RE.sub(b"", attrs, count=1)
    elif _SHOW_ATTR_RE.search(attrs):
        attrs = _SHOW_ATTR_RE.sub(b' show="0"', attrs, count=1)
    else:
        attrs = attrs + b' show="0"'
    return (
        xml[: match.start()]
        + b"<"
        + match.group(1)
        + b"sld"
        + attrs
        + closer
        + xml[match.end() :]
    )


def slide_is_visible(xml: bytes) -> bool:
    """Return whether a slide part is shown (default true)."""
    match = _SLIDE_OPEN_RE.search(xml)
    if match is None:
        raise RuntimeError("slide part has no sld root element")
    attrs = match.group(2) or b""
    found = _SHOW_ATTR_RE.search(attrs)
    if found is None:
        return True
    raw = found.group(1).strip(b"\"'").decode("ascii", errors="replace")
    if raw in {"0", "false"}:
        return False
    if raw in {"1", "true"}:
        return True
    raise RuntimeError(f"invalid slide show value {raw!r}")


def rewrite_pptx(
    source: Path,
    dest: Path,
    replacements: dict[str, bytes],
) -> None:
    """Copy a PPTX zip, replacing named parts."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            payload = replacements.get(info.filename, zin.read(info.filename))
            zout.writestr(info, payload)
    tmp.replace(dest)


def apply_visibility(
    source: Path,
    dest: Path,
    pages: list[int],
    *,
    visible: bool,
) -> dict[str, object]:
    """Hide or unhide ``pages`` and write ``dest``."""
    with zipfile.ZipFile(source) as zin:
        refs = _parse_slide_refs(zin)
        if not refs:
            raise RuntimeError(f"no slides found in {source}")
        by_index = {ref.index: ref for ref in refs}
        missing = [page for page in pages if page not in by_index]
        if missing:
            raise ValueError(
                f"slides not in presentation: {', '.join(str(n) for n in missing)}"
            )
        replacements: dict[str, bytes] = {}
        changed: list[int] = []
        for page in pages:
            part_name = by_index[page].part_name
            original = zin.read(part_name)
            updated = set_slide_visibility(original, visible=visible)
            if updated != original:
                replacements[part_name] = updated
                changed.append(page)
        slide_count = len(refs)
    if not replacements:
        if dest.resolve() != source.resolve():
            rewrite_pptx(source, dest, {})
        report = {
            "source": str(source),
            "output": str(dest),
            "slide_count": slide_count,
            "requested": pages,
            "changed": [],
            "visible": visible,
        }
        return report
    rewrite_pptx(source, dest, replacements)
    return {
        "source": str(source),
        "output": str(dest),
        "slide_count": slide_count,
        "requested": pages,
        "changed": changed,
        "visible": visible,
    }


def collect_pages(args: argparse.Namespace, slide_count: int) -> list[int]:
    """Union every selection flag into sorted 1-based page numbers."""
    selected: set[int] = set()
    if args.unhide_all:
        return list(range(1, slide_count + 1))
    if args.pages:
        selected.update(parse_page_spec(args.pages, slide_count))
    if args.last:
        selected.update(last_pages(slide_count, args.last))
    if args.match:
        if not args.project:
            raise ValueError("--match requires --project")
        selected.update(pages_matching_stem(Path(args.project), args.match))
        overflow = [page for page in selected if page > slide_count]
        if overflow:
            raise ValueError(
                "project roster page(s) "
                + ", ".join(str(n) for n in overflow)
                + f" are outside the PPTX (1..{slide_count})"
            )
    if not selected:
        raise ValueError("select slides with --pages, --last, --match, or --unhide-all")
    return sorted(selected)


def default_output_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_hidden{source.suffix}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hide or unhide selected slides in a finished PPTX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pptx", help="Source .pptx path")
    parser.add_argument(
        "-o",
        "--output",
        help="Destination .pptx (default: <name>_hidden.pptx beside the source)",
    )
    parser.add_argument(
        "--pages",
        help="1-based pages or ranges to change, e.g. 5,6,8-10",
    )
    parser.add_argument(
        "--last",
        type=int,
        help="Change the last N slides",
    )
    parser.add_argument(
        "--project",
        help="Project directory used with --match (reads svg_output/)",
    )
    parser.add_argument(
        "--match",
        help="Hide slides whose SVG stem contains this token (needs --project)",
    )
    parser.add_argument(
        "--unhide",
        action="store_true",
        help="Clear the hidden flag on the selected slides instead of setting it",
    )
    parser.add_argument(
        "--unhide-all",
        action="store_true",
        help="Clear the hidden flag on every slide",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write back to the source path (ignores --output)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write a machine-readable summary to stdout",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the selected pages without writing a PPTX",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.pptx).expanduser().resolve()
    if not source.is_file():
        print(f"Error: PPTX not found: {source}", file=sys.stderr)
        return 1
    dest = source if args.in_place else (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(source)
    )
    try:
        with zipfile.ZipFile(source) as zin:
            slide_count = len(_parse_slide_refs(zin))
        pages = collect_pages(args, slide_count)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    visible = bool(args.unhide or args.unhide_all)
    action = "unhide" if visible else "hide"
    if args.json and args.dry_run:
        print(json.dumps({
            "source": str(source),
            "output": str(dest),
            "slide_count": slide_count,
            "requested": pages,
            "visible": visible,
            "dry_run": True,
        }, indent=2))
    else:
        print(
            f"{action} {len(pages)} slide(s) of {slide_count}: "
            + ", ".join(str(n) for n in pages),
            file=sys.stderr,
        )
    if args.dry_run:
        return 0

    try:
        report = apply_visibility(source, dest, pages, visible=visible)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report["output"])
    print(
        f"Wrote {dest} ({len(report['changed'])} part(s) changed)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
