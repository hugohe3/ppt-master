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


def _page_target(target: str, page: str) -> str:
    """Resolve one requested page while keeping it inside ``svg_output/``."""
    target_path = Path(target).resolve()
    svg_root = (
        target_path
        if target_path.is_dir() and target_path.name == "svg_output"
        else target_path / "svg_output"
    )
    if not svg_root.is_dir():
        raise ValueError(
            "--stage page requires a project or svg_output directory target"
        )
    svg_root = svg_root.resolve()

    requested = Path(page)
    if requested.is_absolute():
        candidates = [requested]
    else:
        candidates = [svg_root / requested]
        if requested.parts and requested.parts[0] == "svg_output":
            candidates.append(svg_root.parent / requested)
        candidates.append(Path.cwd() / requested)

    inside_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(svg_root)
        except ValueError:
            continue
        if resolved not in inside_candidates:
            inside_candidates.append(resolved)
        if resolved.is_file() and resolved.suffix.casefold() == ".svg":
            return str(resolved)

    if not inside_candidates:
        raise ValueError("--page must resolve to a path under svg_output/")
    candidate = inside_candidates[0]
    if candidate.suffix.casefold() != ".svg":
        raise ValueError(f"--page must name an SVG file: {page}")
    raise ValueError(f"--page SVG does not exist: {page}")


def _default_json_report_path(
    checker: SVGQualityChecker,
    target: str,
    stage: str,
) -> Path:
    """Choose a stage-specific report path without overwriting the final gate."""
    target_path = Path(target)
    project_path = checker._resolve_project_path(target_path)
    report_name = {
        "final": "svg_quality_report.json",
        "first-page": "svg_quality_first_page_report.json",
        "page": "svg_quality_page_report.json",
    }[stage]
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
    print("  python3 scripts/svg_quality_checker.py <roundtrip-workspace> --roundtrip")
    print("  python3 scripts/svg_quality_checker.py <workspace>/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py --all projects")
    print("\nExamples:")
    print("  python3 scripts/svg_quality_checker.py projects/project/svg_output/slide_01.svg")
    print("  python3 scripts/svg_quality_checker.py projects/project/svg_output")
    print("  python3 scripts/svg_quality_checker.py projects/project")
    print("  python3 scripts/svg_quality_checker.py templates/layouts/presentation_core/templates --template-mode")
    print("  python3 scripts/svg_quality_checker.py templates/decks/中国电信/templates --template-mode")
    print("\nOptions:")
    print("  --format <ppt169|ppt43|...>   Expected canvas format")
    print("  --stage <first-page|page|final>")
    print("                                  first-page checks only the first authored SVG;")
    print("                                  page checks only --page with the same partial")
    print("                                  structure rules; final (default) requires the")
    print("                                  complete declared page roster.")
    print("  --page <basename|path>         Required with --stage page; must resolve under")
    print("                                  the target project's svg_output/ directory.")
    print("  --json                         Write a machine-readable quality report")
    print("  --json-output <path>           Override the JSON report path")
    print("  --export                       Write a plain-text quality report")
    print("  --output <path>                Override the plain-text report path")
    print("  --quick-generate               Validate lockless Quick SVGs; infer flat or")
    print("                                 structured output from the complete roster;")
    print("                                  ignore design_spec.md and spec_lock.md.")
    print("  --roundtrip                    Validate edited-text capacity on the resolved")
    print("                                  authoring-svg-flat/ output roster; uses")
    print("                                  page_plan.json when present and skips")
    print("                                  generated-project/template-only contracts.")
    print("  --canonical-authoring          Require compact authoring syntax as written;")
    print("                                  the checker never rewrites source SVG.")
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
    canonical_authoring = "--canonical-authoring" in sys.argv
    roundtrip = "--roundtrip" in sys.argv
    if template_mode and quick_generate:
        print("[ERROR] --template-mode cannot be combined with --quick-generate")
        sys.exit(1)
    if roundtrip and (template_mode or quick_generate or canonical_authoring):
        print(
            "[ERROR] --roundtrip cannot be combined with --template-mode, "
            "--quick-generate, or --canonical-authoring"
        )
        sys.exit(1)
    checker = SVGQualityChecker(
        template_mode=template_mode,
        quick_generate=quick_generate,
        canonical_authoring=canonical_authoring,
    )

    target = sys.argv[1]
    expected_format = None
    stage = "final"
    page = None

    if "--format" in sys.argv:
        idx = sys.argv.index("--format")
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]
    if "--stage" in sys.argv:
        idx = sys.argv.index("--stage")
        if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
            print("[ERROR] --stage requires first-page, page, or final")
            sys.exit(1)
        stage = sys.argv[idx + 1]
        if stage not in {"first-page", "page", "final"}:
            print(f"[ERROR] Unsupported quality-check stage: {stage}")
            sys.exit(1)
    if "--page" in sys.argv:
        idx = sys.argv.index("--page")
        if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
            print("[ERROR] --page requires a basename or path under svg_output/")
            sys.exit(1)
        page = sys.argv[idx + 1]
    if stage == "page" and page is None:
        print("[ERROR] --stage page requires --page <basename or path under svg_output/>")
        sys.exit(1)
    if stage != "page" and page is not None:
        print("[ERROR] --page is supported only with --stage page")
        sys.exit(1)
    if roundtrip and any(
        option in sys.argv
        for option in ("--format", "--stage", "--page")
    ):
        print("[ERROR] --roundtrip does not support --format, --stage, or --page")
        sys.exit(1)

    if target == "--all":
        if roundtrip:
            print("[ERROR] --roundtrip does not support --all")
            sys.exit(1)
        if quick_generate:
            print("[ERROR] --quick-generate does not support --all")
            sys.exit(1)
        if stage != "final":
            print(f"[ERROR] --stage {stage} does not support --all")
            sys.exit(1)
        base_dir = sys.argv[2] if len(sys.argv) > 2 else "projects"
        from project_utils import find_all_projects

        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"Checking project: {project.name}")
            print("=" * 80)
            checker.check_directory(str(project))
    else:
        if roundtrip:
            checker.check_roundtrip_workspace(target)
        elif stage == "first-page":
            check_target = _first_page_target(target)
        elif stage == "page":
            try:
                check_target = _page_target(target, page or "")
            except ValueError as exc:
                print(f"[ERROR] {exc}")
                sys.exit(1)
        else:
            check_target = target
        if not roundtrip:
            checker.check_directory(check_target, expected_format)

    if not roundtrip and stage == "final" and Path(target).is_dir():
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
