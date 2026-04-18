"""Command-line entry point for pptx_blueprint.

Usage:
    python3 -m pptx_blueprint <pptx_path> [options]
    # or via the thin wrapper:
    python3 skills/ppt-master/scripts/pptx_blueprint/cli.py <pptx_path>

The CLI orchestrates the full pipeline:

    parse_pptx -> cluster_and_select -> tag_representative_slides
        -> emit_slide_svg (with assert_compliant)
        -> write_design_spec_file
        -> optional layouts_index.json advice

With --engine auto (default) the blueprint path is tried first; on failure
it falls back to the legacy external-app renderer (pptx_template_import.py).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from pathlib import Path

from .design_spec_writer import write_design_spec_file
from .fallback import probe_availability, run_fallback
from .ir import Blueprint
from .page_classifier import ClusterResult, cluster_and_select
from .placeholder_tagger import TagRecord, tag_representative_slides
from .svg_emitter import assert_compliant, emit_slide_svg, lint_svg
from .xml_parser import parse_pptx


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser."""
    parser = argparse.ArgumentParser(
        prog='pptx_blueprint',
        description=(
            'Distill a PPTX source into a reusable layouts/<name>/ template pack '
            '(cluster-deduplicated SVGs + design_spec.md + assets).'
        ),
    )
    parser.add_argument('pptx_path', help='Path to the source .pptx file')
    parser.add_argument(
        '-o', '--output',
        help='Output directory (default: <pptx_stem>_template next to the source)',
    )
    parser.add_argument(
        '-n', '--name',
        help='Template name written into design_spec.md (default: <pptx_stem>)',
    )
    parser.add_argument(
        '--engine', choices=['auto', 'blueprint', 'legacy'], default='auto',
        help='Engine selection. auto = blueprint then fallback on failure.',
    )
    parser.add_argument(
        '--max-layouts', type=int, default=12,
        help='Upper bound on the number of layout variants (default: 12)',
    )
    parser.add_argument(
        '--distance-threshold', type=float, default=6.0,
        help='Fingerprint distance below which slides merge into one cluster '
             '(default: 6.0). Lower = more variants, higher = fewer.',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Fail (non-zero exit) on any SVG linter violation.',
    )
    parser.add_argument(
        '--no-assets', action='store_true',
        help='Skip copying ppt/media/ assets into the output directory.',
    )
    parser.add_argument(
        '--report', action='store_true',
        help='Also write blueprint_report.json with cluster + tag provenance.',
    )
    parser.add_argument(
        '--clean', action='store_true',
        help='Wipe the output directory before writing (destructive).',
    )
    return parser


# ---------------------------------------------------------------------------
# Resolution of defaults
# ---------------------------------------------------------------------------

def _resolve_output_dir(args: argparse.Namespace, pptx_path: Path) -> Path:
    if args.output:
        return Path(args.output).expanduser().resolve()
    return pptx_path.parent / f"{pptx_path.stem}_template"


def _resolve_template_name(args: argparse.Namespace, pptx_path: Path) -> str:
    if args.name:
        return args.name
    # Sanitize: only ascii alnum, dot, dash, underscore; preserve CJK
    stem = pptx_path.stem
    return stem or 'blueprint_template'


def _prepare_output(output_dir: Path, clean: bool) -> None:
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Blueprint engine
# ---------------------------------------------------------------------------

def _emit_all(
    bp: Blueprint,
    clusters: list[ClusterResult],
    output_dir: Path,
    strict: bool,
) -> tuple[int, int]:
    """Emit every cluster's representative as an SVG file.

    Returns (emitted_count, total_violations). In strict mode, any violation
    raises instead.
    """
    emitted = 0
    total_vio = 0
    for r in clusters:
        svg = emit_slide_svg(r.slide, bp.theme)
        if strict:
            assert_compliant(svg)
        else:
            total_vio += len(lint_svg(svg))
        out_path = output_dir / r.filename
        out_path.write_text(svg, encoding='utf-8')
        emitted += 1
    return emitted, total_vio


def _write_report(
    output_dir: Path,
    bp: Blueprint,
    clusters: list[ClusterResult],
    tag_report: list[TagRecord],
) -> None:
    """Dump cluster + tag provenance as JSON for user review."""
    data = {
        'source_pptx': str(bp.source_pptx),
        'source_slide_count': len(bp.slides),
        'viewbox': list(bp.viewbox),
        'parser_warnings': bp.warnings,
        'clusters': [
            {
                'filename': r.filename,
                'page_type': r.fingerprint.page_type,
                'represents_slide': r.slide.index,
                'cluster_size': r.member_count,
                'member_slides': r.member_indices,
                'fingerprint': {
                    'shape_bucket': r.fingerprint.shape_bucket,
                    'column_count': r.fingerprint.column_count,
                    'brightness': r.fingerprint.brightness,
                    'has_large_title': r.fingerprint.has_large_title,
                    'image_count': r.fingerprint.image_count,
                    'text_count': r.fingerprint.text_count,
                },
            }
            for r in clusters
        ],
        'placeholders': [
            {
                'slide': t.slide_index,
                'source': t.shape_source_name,
                'tag': t.tag,
                'tier': t.tier,
                'rule': t.rule,
                'original_text': t.original_text,
            }
            for t in tag_report
        ],
        'tag_provenance_summary': {
            'canonical_tier_a': sum(1 for t in tag_report if t.tier == 'A'),
            'heuristic_tier_b': sum(1 for t in tag_report if t.tier == 'B'),
        },
    }
    (output_dir / 'blueprint_report.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def run_blueprint(args: argparse.Namespace, pptx_path: Path) -> int:
    """Execute the blueprint engine. Returns CLI exit code."""
    output_dir = _resolve_output_dir(args, pptx_path)
    template_name = _resolve_template_name(args, pptx_path)
    _prepare_output(output_dir, args.clean)

    print(f"[blueprint] Parsing {pptx_path.name} ...", file=sys.stderr)
    bp = parse_pptx(
        pptx_path,
        output_dir=None if args.no_assets else output_dir,
    )
    if not bp.slides:
        print('[blueprint] ERROR: no slides extracted — PPTX may be empty or corrupt',
              file=sys.stderr)
        return 2

    print(f"[blueprint] Parsed {len(bp.slides)} slides, "
          f"{len(bp.theme.colors)} theme colors, "
          f"{len(bp.assets)} assets, {len(bp.warnings)} parser warnings",
          file=sys.stderr)

    clusters = cluster_and_select(
        bp.slides,
        max_layouts=args.max_layouts,
        distance_threshold=args.distance_threshold,
    )
    if not clusters:
        print('[blueprint] ERROR: clustering produced zero representatives',
              file=sys.stderr)
        return 2

    tag_report = tag_representative_slides(clusters)

    try:
        emitted, violations = _emit_all(bp, clusters, output_dir, args.strict)
    except ValueError as exc:
        print(f"[blueprint] STRICT FAIL: {exc}", file=sys.stderr)
        return 3

    write_design_spec_file(
        output_dir / 'design_spec.md',
        template_name=template_name,
        bp=bp,
        clusters=clusters,
        tag_report=tag_report,
    )

    if args.report:
        _write_report(output_dir, bp, clusters, tag_report)

    print(f"[blueprint] Emitted {emitted} layout variants "
          f"({violations} linter violations, non-fatal)", file=sys.stderr)
    print(f"[blueprint] Output: {output_dir}", file=sys.stderr)

    _print_index_advice(template_name, clusters)
    return 0


# ---------------------------------------------------------------------------
# Legacy engine
# ---------------------------------------------------------------------------

def run_legacy(args: argparse.Namespace, pptx_path: Path) -> int:
    """Execute the legacy external-app fallback engine. Returns CLI exit code."""
    output_dir = _resolve_output_dir(args, pptx_path)
    _prepare_output(output_dir, args.clean)

    print(f"[legacy] Running external-app fallback for {pptx_path.name} ...",
          file=sys.stderr)
    result = run_fallback(pptx_path, output_dir)

    if not result.is_available:
        print(f"[legacy] UNAVAILABLE: {result.unavailable_reason}", file=sys.stderr)
        return 4

    print(f"[legacy] Export method: {result.export_method}", file=sys.stderr)
    print(f"[legacy] Emitted {len(result.svg_files)} raw SVGs to {output_dir}",
          file=sys.stderr)
    for w in result.warnings:
        print(f"[legacy] WARNING: {w}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Auto mode: blueprint first, fallback on failure
# ---------------------------------------------------------------------------

def run_auto(args: argparse.Namespace, pptx_path: Path) -> int:
    """Try the blueprint engine first; on failure, retry with the legacy fallback."""
    try:
        code = run_blueprint(args, pptx_path)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"[auto] Blueprint engine crashed: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        code = 5

    if code == 0:
        return 0

    # Try fallback if the environment supports it
    available, reason = probe_availability()
    if not available:
        print(f"[auto] Fallback unavailable ({reason}); "
              f"blueprint engine exit code was {code}.", file=sys.stderr)
        return code

    print("[auto] Retrying with legacy fallback engine ...", file=sys.stderr)
    return run_legacy(args, pptx_path)


# ---------------------------------------------------------------------------
# Helpful post-run advice
# ---------------------------------------------------------------------------

def _print_index_advice(template_name: str, clusters: list[ClusterResult]) -> None:
    """Print a manual-register snippet for layouts_index.json.

    We deliberately do NOT modify layouts_index.json automatically — it is a
    user-curated file and edits should be reviewed.
    """
    print("", file=sys.stderr)
    print("To register this template, append the following entry to "
          "skills/ppt-master/templates/layouts/layouts_index.json under "
          "`layouts`:", file=sys.stderr)
    entry = {
        template_name: {
            'label': f'{template_name} (auto-generated)',
            'summary': 'Template distilled from a source PPTX by pptx_blueprint.',
            'tone': '[Review and fill in]',
            'themeMode': '[Light theme / Dark theme]',
            'keywords': ['[Review and fill in]'],
            'files': [r.filename for r in clusters],
        }
    }
    print(json.dumps(entry, ensure_ascii=False, indent=2), file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """CLI entry point — parse argv, dispatch to the selected engine, return exit code."""
    args = build_parser().parse_args(argv)

    pptx_path = Path(args.pptx_path).expanduser().resolve()
    if not pptx_path.exists():
        print(f"ERROR: file not found: {pptx_path}", file=sys.stderr)
        return 1
    if pptx_path.suffix.lower() != '.pptx':
        print(f"ERROR: expected a .pptx file, got: {pptx_path.name}", file=sys.stderr)
        return 1

    if args.engine == 'blueprint':
        return run_blueprint(args, pptx_path)
    if args.engine == 'legacy':
        return run_legacy(args, pptx_path)
    return run_auto(args, pptx_path)


if __name__ == '__main__':
    raise SystemExit(main())
