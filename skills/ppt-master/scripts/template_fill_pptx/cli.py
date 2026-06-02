"""Command-line interface: analyze / scaffold / check-plan / apply subcommands."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from .analyzer import analyze_pptx
from .applier import apply_plan
from .checker import check_plan, print_check_report
from .ooxml import _load_json, _write_json
from .scaffolder import scaffold_plan
from .transitions import (
    DEFAULT_TRANSITION,
    DEFAULT_TRANSITION_DURATION,
    KEEP_TRANSITION,
    TRANSITIONS,
)


def _parse_slide_list(value: str | None) -> list[int] | None:
    if not value:
        return None
    slides: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            slides.extend(range(int(start), int(end) + 1))
        else:
            slides.append(int(part))
    return slides


def _timestamped_pptx_path(path: Path) -> Path:
    if path.suffix.lower() != ".pptx":
        return path
    if re.search(r"_\d{8}_\d{6}$", path.stem):
        return path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.stem}_{timestamp}{path.suffix}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze and fill native PPTX templates without converting slides to SVG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Extract slide library JSON from a PPTX")
    analyze.add_argument("pptx_file", help="Source PPTX file")
    analyze.add_argument("-o", "--output", required=True, help="Output slide_library.json path")

    scaffold = subparsers.add_parser("scaffold", help="Create an editable fill plan skeleton")
    scaffold.add_argument("library_json", help="slide_library.json from analyze")
    scaffold.add_argument("-o", "--output", required=True, help="Output fill_plan.json path")
    scaffold.add_argument(
        "--slides",
        help="Comma/range source slide list, e.g. 1,3,5-7. Defaults to first six slides.",
    )
    scaffold.add_argument(
        "--include-empty",
        action="store_true",
        help="Include empty text slots in the scaffold. Defaults to text-bearing slots only.",
    )

    check = subparsers.add_parser("check-plan", help="Check a fill plan against source slot capacity")
    check.add_argument("library_json", help="slide_library.json from analyze")
    check.add_argument("plan_json", help="Fill plan JSON")
    check.add_argument("-o", "--output", help="Optional JSON report output path")

    apply = subparsers.add_parser("apply", help="Apply fill plan and write a new PPTX")
    apply.add_argument("pptx_file", help="Source PPTX file")
    apply.add_argument("plan_json", help="Fill plan JSON")
    apply.add_argument(
        "-o",
        "--output",
        required=True,
        help=(
            "Output PPTX path. A _YYYYMMDD_HHMMSS timestamp is appended "
            "automatically unless the stem already ends with one."
        ),
    )
    apply.add_argument(
        "--transition",
        choices=sorted(TRANSITIONS) + ["none", KEEP_TRANSITION],
        default=DEFAULT_TRANSITION,
        help=(
            "Page-to-page transition applied to every cloned slide "
            "(per-slide 'transition' in the plan overrides this). "
            f"Default: {DEFAULT_TRANSITION}. Use 'none' for no motion, "
            "or 'keep' to preserve each source slide's existing transition."
        ),
    )
    apply.add_argument(
        "--transition-duration",
        type=float,
        default=DEFAULT_TRANSITION_DURATION,
        help="Transition duration in seconds (default: 0.5).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            pptx_path = Path(args.pptx_file).expanduser().resolve()
            if not pptx_path.exists():
                print(f"Error: file does not exist: {pptx_path}", file=sys.stderr)
                return 1
            library = analyze_pptx(pptx_path)
            _write_json(Path(args.output).expanduser().resolve(), library)
            print(f"Analyzed {library['slide_count']} slides -> {args.output}", file=sys.stderr)
            return 0

        if args.command == "scaffold":
            library = _load_json(Path(args.library_json).expanduser().resolve())
            plan = scaffold_plan(
                library,
                _parse_slide_list(args.slides),
                include_empty=args.include_empty,
            )
            _write_json(Path(args.output).expanduser().resolve(), plan)
            print(f"Plan scaffold -> {args.output}", file=sys.stderr)
            return 0

        if args.command == "check-plan":
            library = _load_json(Path(args.library_json).expanduser().resolve())
            plan = _load_json(Path(args.plan_json).expanduser().resolve())
            report = check_plan(library, plan)
            print_check_report(report)
            if args.output:
                _write_json(Path(args.output).expanduser().resolve(), report)
                print(f"Check report -> {args.output}", file=sys.stderr)
            return 0 if report["summary"]["error"] == 0 else 1

        if args.command == "apply":
            pptx_path = Path(args.pptx_file).expanduser().resolve()
            plan = _load_json(Path(args.plan_json).expanduser().resolve())
            output_path = _timestamped_pptx_path(Path(args.output).expanduser().resolve())
            apply_plan(
                pptx_path,
                plan,
                output_path,
                transition=args.transition,
                transition_duration=args.transition_duration,
            )
            print(f"Template-filled PPTX -> {output_path}", file=sys.stderr)
            return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1
