#!/usr/bin/env python3
"""
PPT Master - PPTX Intake Enrichment

Extract reusable PPTX intake facts into a standard analysis bundle. This is a
read-only companion to `ppt_to_md.py`: Markdown remains the content source,
while this bundle provides canvas, visual identity, slide geometry, tables,
native chart data, and SmartArt structure for downstream workflows.

Usage:
    python3 scripts/pptx_intake.py <source.pptx> -o <output_dir>

Examples:
    python3 scripts/pptx_intake.py deck.pptx -o projects/demo/analysis

Dependencies:
    None beyond the repository scripts used for PPTX parsing.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from beautify_identity import extract_identity  # noqa: E402
from pptx_ooxml.analyzer import analyze_pptx  # noqa: E402

configure_utf8_stdio()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _chart_summary(slide_library: dict[str, Any]) -> dict[str, Any]:
    charts: list[dict[str, Any]] = []
    total_series = 0
    multi_plot_count = 0
    for slide in slide_library.get("slides", []):
        for chart in slide.get("charts", []):
            series_count = int(chart.get("series_count") or 0)
            plot_types = chart.get("plot_types") or []
            if len(plot_types) > 1:
                multi_plot_count += 1
            total_series += series_count
            charts.append(
                {
                    "slide_index": slide.get("slide_index"),
                    "chart_id": chart.get("chart_id"),
                    "chart_type": chart.get("chart_type"),
                    "plot_types": plot_types,
                    "category_count": chart.get("category_count", 0),
                    "series_count": series_count,
                    "series_names": [
                        series.get("name")
                        for series in chart.get("series", [])
                        if series.get("name")
                    ],
                }
            )
    return {
        "chart_count": len(charts),
        "series_count": total_series,
        "multi_plot_chart_count": multi_plot_count,
        "charts": charts,
    }


def _table_summary(slide_library: dict[str, Any]) -> dict[str, Any]:
    tables: list[dict[str, Any]] = []
    for slide in slide_library.get("slides", []):
        for table in slide.get("tables", []):
            tables.append(
                {
                    "slide_index": slide.get("slide_index"),
                    "table_id": table.get("table_id"),
                    "row_count": table.get("row_count", 0),
                    "column_count": table.get("column_count", 0),
                }
            )
    return {"table_count": len(tables), "tables": tables}


def _diagram_summary(slide_library: dict[str, Any]) -> dict[str, Any]:
    diagrams: list[dict[str, Any]] = []
    text_item_count = 0
    unreadable_count = 0
    warning_count = 0
    slides_with_diagrams: set[int] = set()
    for slide in slide_library.get("slides", []):
        slide_index = slide.get("slide_index")
        for diagram in slide.get("diagrams", []):
            node_count = int(diagram.get("node_count") or 0)
            text_count = int(diagram.get("text_count") or 0)
            text_item_count += text_count
            if not diagram.get("text_extracted"):
                unreadable_count += 1
            if diagram.get("status") != "ok" or diagram.get("warnings"):
                warning_count += 1
            if isinstance(slide_index, int):
                slides_with_diagrams.add(slide_index)
            diagrams.append(
                {
                    "slide_index": slide_index,
                    "diagram_id": diagram.get("diagram_id"),
                    "layout": diagram.get("layout", {}),
                    "node_count": node_count,
                    "text_count": text_count,
                    "connection_count": int(diagram.get("connection_count") or 0),
                    "max_depth": int(diagram.get("max_depth") or 0),
                    "text_extracted": bool(diagram.get("text_extracted")),
                    "has_persisted_drawing": bool(diagram.get("has_persisted_drawing")),
                    "status": diagram.get("status"),
                    "warnings": diagram.get("warnings", []),
                }
            )
    return {
        "diagram_count": len(diagrams),
        "text_item_count": text_item_count,
        "unreadable_count": unreadable_count,
        "warning_count": warning_count,
        "slides_with_diagrams": sorted(slides_with_diagrams),
        "diagrams": diagrams,
    }


def build_source_profile(
    pptx_path: Path,
    identity: dict[str, Any],
    slide_library: dict[str, Any],
    stem: str | None = None,
) -> dict[str, Any]:
    """Build the Strategist-facing per-deck digest over the raw intake artifacts.

    `stem` is the source-file stem used to prefix the per-deck artifact files so
    several decks can coexist in one `analysis/` folder. Defaults to the pptx stem.
    """
    stem = stem or pptx_path.stem
    return {
        "schema": "pptx_intake_profile.v1",
        "stem": stem,
        "source_pptx": str(pptx_path),
        "slide_count": slide_library.get("slide_count", identity.get("slide_count", 0)),
        "usage_contract": {
            "standard_generation": (
                "Use identity and slide-library fields as source facts and recommendation "
                "candidates only; do not preserve original page count, order, or coordinates "
                "unless the user selected the beautify profile."
            ),
            "beautify": (
                "Promote source text, page order, page count, colors, fonts, and font sizes "
                "into locked constraints after user confirmation."
            ),
        },
        "artifacts": {
            "identity": f"{stem}.identity.json",
            "slide_library": f"{stem}.slide_library.json",
        },
        "canvas": identity.get("canvas", {}),
        "identity": {
            "theme_palette": (identity.get("theme") or {}).get("palette", {}),
            "theme_fonts": (identity.get("theme") or {}).get("fonts", {}),
            "theme_sizes": (identity.get("theme") or {}).get("sizes", {}),
            "observed_colors": (identity.get("observed") or {}).get("colors", []),
            "observed_fonts": (identity.get("observed") or {}).get("fonts", {}),
            "observed_sizes_pt": (identity.get("observed") or {}).get("sizes_pt", []),
            "layout_sizes_pt": identity.get("layout_sizes_pt", []),
        },
        "structure": {
            "canvas_px": slide_library.get("canvas_px", {}),
            "page_types": [
                {
                    "slide_index": slide.get("slide_index"),
                    "page_type": slide.get("page_type"),
                    "slot_count": len(slide.get("slots", [])),
                    "diagram_count": len(slide.get("diagrams", [])),
                }
                for slide in slide_library.get("slides", [])
            ],
        },
        "tables": _table_summary(slide_library),
        "charts": _chart_summary(slide_library),
        "diagrams": _diagram_summary(slide_library),
    }


SOURCE_INDEX_NAME = "source_profile.json"


@contextmanager
def _source_index_lock(output_dir: Path):
    """Serialize source-index bundle publication with a persistent lock file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / f"{SOURCE_INDEX_NAME}.lock"
    with lock_path.open("a+b") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            return

        if msvcrt is not None:
            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            return

        raise RuntimeError(
            "Cannot safely update source_profile.json: no supported file-lock API"
        )


def _load_source_index(index_path: Path) -> dict[str, Any]:
    """Load and validate an existing multi-deck source index."""
    if not index_path.exists():
        return {}
    if not index_path.is_file():
        raise RuntimeError(f"Source index is not a file: {index_path}")

    try:
        loaded = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise RuntimeError(
            f"Source index contains invalid JSON and was left unchanged: {index_path}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"Cannot read source index: {index_path}: {exc}") from exc

    if not isinstance(loaded, dict) or not isinstance(loaded.get("decks"), list):
        raise RuntimeError(
            f"Source index must be a JSON object with a decks array and was left unchanged: "
            f"{index_path}"
        )
    for index, deck in enumerate(loaded["decks"]):
        if not isinstance(deck, dict):
            raise RuntimeError(
                f"Source index decks[{index}] must be an object and was left unchanged: "
                f"{index_path}"
            )
    return loaded


def _upsert_source_index_unlocked(
    output_dir: Path,
    digest: dict[str, Any],
) -> Path:
    index_path = output_dir / SOURCE_INDEX_NAME
    index = _load_source_index(index_path)
    stem = digest.get("stem")
    decks = [d for d in index.get("decks", []) if d.get("stem") != stem]
    decks.append(digest)
    decks.sort(key=lambda d: str(d.get("stem", "")))
    index = {
        "schema": "pptx_intake_index.v1",
        "deck_count": len(decks),
        "decks": decks,
    }
    _write_json(index_path, index)
    return index_path


def upsert_source_index(output_dir: Path, digest: dict[str, Any]) -> Path:
    """Merge one deck digest into the serialized multi-deck source index.

    The index stays the single must-read entry for the Strategist: it inlines every
    deck's digest under `decks[]`, so a one-deck project is a one-entry index and a
    multi-deck project lists each source deck self-containedly. Re-importing a deck
    with the same stem replaces its entry in place.
    """
    with _source_index_lock(output_dir):
        return _upsert_source_index_unlocked(output_dir, digest)


def run_intake(pptx_path: Path, output_dir: Path) -> dict[str, Path]:
    """Write `<stem>.identity.json`, `<stem>.slide_library.json`, and merge the
    deck's digest into the single multi-deck index `source_profile.json`."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pptx_path.stem
    identity = extract_identity(pptx_path)
    slide_library = analyze_pptx(pptx_path)
    digest = build_source_profile(pptx_path, identity, slide_library, stem)

    identity_path = output_dir / f"{stem}.identity.json"
    slide_library_path = output_dir / f"{stem}.slide_library.json"
    with _source_index_lock(output_dir):
        _write_json(identity_path, identity)
        _write_json(slide_library_path, slide_library)
        profile_path = _upsert_source_index_unlocked(output_dir, digest)
    return {
        "identity": identity_path,
        "slide_library": slide_library_path,
        "source_profile": profile_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract standard PPTX intake analysis artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", help="Source PPTX / PPTM / PPSX / PPSM / POTX / POTM file")
    parser.add_argument("-o", "--output-dir", required=True, help="Output project analysis directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    if not source.is_file():
        print(f"Error: source not found: {source}", file=sys.stderr)
        return 1
    try:
        outputs = run_intake(source, Path(args.output_dir).expanduser().resolve())
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"Error: PPTX intake failed: {exc}", file=sys.stderr)
        return 1
    print(f"PPTX intake -> {Path(args.output_dir).expanduser().resolve()}", file=sys.stderr)
    for name, path in outputs.items():
        print(f"  {name}: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
