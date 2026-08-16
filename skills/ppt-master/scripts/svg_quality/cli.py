#!/usr/bin/env python3
"""PPT Master SVG quality-check CLI implementation.

Parses the legacy command-line contract and delegates validation to the checker.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file_or_project> [options]

Examples:
    python3 scripts/svg_quality_checker.py projects/demo --stage final --json

Dependencies:
    Standard library plus local PPT Master validation modules.
"""

import sys
from pathlib import Path

from attribution_guard import require_skill_integrity
from slide_roster import discover_slide_svgs

from .checker import SVGQualityChecker


def _first_page_target(target: str) -> str:
    """Resolve a project/directory target to its first authored SVG page."""
    path = Path(target)
    if path.is_file():
        return str(path)
    svg_root = path / "svg_output" if (path / "svg_output").is_dir() else path
    svg_files = discover_slide_svgs(svg_root) if svg_root.is_dir() else []
    return str(svg_files[0]) if svg_files else target


def _default_json_report_path(
    checker: SVGQualityChecker,
    target: str,
    stage: str,
) -> Path:
    """Choose a stage-specific report path without overwriting the final gate."""
    target_path = Path(target)
    project_path = checker._resolve_project_path(target_path)
    report_name = (
        "svg_quality_report.json"
        if stage == "final"
        else "svg_quality_first_page_report.json"
    )
    if (
        (project_path / "svg_output").is_dir()
        or (project_path / "design_spec.md").is_file()
    ):
        return project_path / "validation" / report_name
    base = target_path if target_path.is_dir() else target_path.parent
    return base / report_name


def print_usage() -> None:
    """Print CLI usage information."""
    print("PPT Master - SVG Quality Check Tool\n")
    print("Usage:")
    print("  python3 scripts/svg_quality_checker.py <svg_file>")
    print("  python3 scripts/svg_quality_checker.py <directory>")
    print("  python3 scripts/svg_quality_checker.py <workspace>/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py --all examples")
    print("\nExamples:")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output/slide_01.svg")
    print("  python3 scripts/svg_quality_checker.py examples/project/svg_output")
    print("  python3 scripts/svg_quality_checker.py examples/project")
    print("  python3 scripts/svg_quality_checker.py templates/layouts/presentation_core/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py templates/decks/中国电信/templates --template-mode")
    print("\nOptions:")
    print("  --format <ppt169|ppt43|...>   Expected canvas format")
    print("  --stage <first-page|final>     first-page checks only the first authored SVG")
    print("                                  with a partial structure roster; final (default)")
    print("                                  requires the complete declared page roster.")
    print("  --json                         Write a machine-readable quality report")
    print("  --json-output <path>           Override the JSON report path")
    print("  --export                       Write a plain-text quality report")
    print("  --output <path>                Override the plain-text report path")
    print("  --quick-generate               Validate lockless flat Quick Generate SVGs;")
    print("                                  ignore design_spec.md and spec_lock.md.")
    print("  --template-mode               Validate a template workspace's templates/ directory:")
    print("                                  Brand/Style validate their portable workspace contracts;")
    print("                                  Layout/Deck glob *.svg directly, skip spec_lock checks,")
    print("                                  enforce roster consistency, and emit placeholder hints.")
    print("                                  native_structure_mode: structured also enables complete")
    print("                                  per-file and cross-page structure validation. Legacy")
    print("                                  native_structure_mode: template fails and must be")
    print("                                  re-created through create-template before validation.")
    print("  Warnings are advisory: they require no modification and do not affect exit status;")
    print("  only errors make the command exit with status 1.")


def main() -> None:
    """Run the CLI entry point."""
    require_skill_integrity()
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)

    if sys.argv[1] in {"-h", "--help", "help"}:
        print_usage()
        sys.exit(0)

    if sys.argv[1].startswith("--") and sys.argv[1] not in {"--all"}:
        print(f"[ERROR] Missing target before option: {sys.argv[1]}")
        print_usage()
        sys.exit(1)

    template_mode = "--template-mode" in sys.argv
    quick_generate = "--quick-generate" in sys.argv
    if template_mode and quick_generate:
        print("[ERROR] --template-mode cannot be combined with --quick-generate")
        sys.exit(1)
    checker = SVGQualityChecker(
        template_mode=template_mode,
        quick_generate=quick_generate,
    )

    target = sys.argv[1]
    expected_format = None
    stage = "final"

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]
    if "--stage" in sys.argv:
        idx = sys.argv.index("--stage")
        if idx + 1 >= len(sys.argv):
            print("[ERROR] --stage requires first-page or final")
            sys.exit(1)
        stage = sys.argv[idx + 1]
        if stage not in {"first-page", "final"}:
            print(f"[ERROR] Unsupported quality-check stage: {stage}")
            sys.exit(1)

    if target == "--all":
        if quick_generate:
            print("[ERROR] --quick-generate does not support --all")
            sys.exit(1)
        if stage != "final":
            print("[ERROR] --stage first-page does not support --all")
            sys.exit(1)
        base_dir = sys.argv[2] if len(sys.argv) > 2 else "examples"
        from project_utils import find_all_projects

        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"Checking project: {project.name}")
            print("=" * 80)
            checker.check_directory(str(project))
    else:
        check_target = _first_page_target(target) if stage == "first-page" else target
        checker.check_directory(check_target, expected_format)

    if stage == "final" and Path(target).is_dir():
        if checker._has_incomplete_page_roster:
            print(
                "[TIP] This final-stage run found an incomplete page roster. "
                "During serial authoring, use --stage first-page for the first-page "
                "gate; keep --stage final for the complete deck."
            )

    checker.print_summary()

    if "--export" in sys.argv:
        output_file = "svg_quality_report.txt"
        if "--output" in sys.argv:
            idx = sys.argv.index("--output")
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        checker.export_report(output_file)

    if "--json" in sys.argv or "--json-output" in sys.argv:
        if "--json-output" in sys.argv:
            idx = sys.argv.index("--json-output")
            if idx + 1 >= len(sys.argv):
                print("[ERROR] --json-output requires a path")
                sys.exit(1)
            json_output = Path(sys.argv[idx + 1])
        else:
            json_output = _default_json_report_path(checker, target, stage)
        checker.export_json_report(
            str(json_output),
            target=target,
            stage=stage,
        )

    if checker.summary["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
