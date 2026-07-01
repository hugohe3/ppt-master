#!/usr/bin/env python3
"""
PPT Master - Unified Markdown Converter

Auto-detect source type and dispatch to the existing source_to_md converters.

Usage:
    python3 scripts/source_to_md.py <file_or_url> [<file_or_url> ...] [options]

Examples:
    python3 scripts/source_to_md.py paper.pdf
    python3 scripts/source_to_md.py paper.pdf report.docx deck.pptx
    python3 scripts/source_to_md.py report.docx -o report.md
    python3 scripts/source_to_md.py deck.pptx --json

Dependencies:
    Same as the backend converter selected for the input.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

_SOURCE_TO_MD_DIR = _SCRIPTS_DIR / "source_to_md"
if str(_SOURCE_TO_MD_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_TO_MD_DIR))

from _conversion_profile import (  # noqa: E402
    build_result_payload,
    profile_path_for,
    write_conversion_profile,
)
from _dispatcher import (  # noqa: E402
    build_conversion_command,
    default_markdown_path,
    detect_source_type,
    is_url,
)

configure_utf8_stdio()


def resolve_output(output: str | None, input_arg: str) -> Path:
    return Path(output) if output else default_markdown_path(input_arg)


def _print_status(message: str) -> None:
    print(message, file=sys.stderr)


def _sanitize_output_stem(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    safe = safe.strip("._-")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe[:120] or "web_source"


def _default_batch_output(input_arg: str, conversion_type: str) -> str | None:
    """Return a deterministic per-source output path for batch mode."""
    if conversion_type == "web":
        parsed = urlparse(input_arg)
        parts = [parsed.netloc]
        if parsed.path and parsed.path != "/":
            parts.append(parsed.path.strip("/").replace("/", "_"))
        return str(Path(f"{_sanitize_output_stem('_'.join(parts))}.md"))
    return str(default_markdown_path(input_arg))


def run_backend(command: list[str], script_name: str) -> int:
    _print_status(f"[>>] {script_name} {' '.join(command[2:])}")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except KeyboardInterrupt:
        return 130
    if result.stdout.strip():
        print(result.stdout.strip(), file=sys.stderr)
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


def print_output(path: Path) -> None:
    print(f"OUTPUT: {path.resolve()}")


def write_passthrough(
    input_arg: str,
    output: Path,
    conversion_type: str,
    json_output: bool = False,
) -> int:
    """Copy text-like input to Markdown and write the profile sidecar."""
    source = Path(input_arg)
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"[ERROR] Cannot read {source}: {exc}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.resolve() != source.resolve():
        output.write_text(text, encoding="utf-8")
    profile = write_conversion_profile(
        input_path=input_arg,
        markdown_path=output,
        converter="source_to_md.py",
        conversion_type=conversion_type,
    )
    _print_status(f"[OK] Saved Markdown to: {output}")
    _print_status(f"   Wrote conversion profile -> {profile}")
    print_output(output)
    if json_output:
        payload = build_result_payload(
            input_path=input_arg,
            markdown_path=output,
            converter="source_to_md.py",
            conversion_type=conversion_type,
            profile_path=profile,
        )
        print(json.dumps(payload, ensure_ascii=False))
    return 0


def ensure_profile(
    input_arg: str,
    output: Path,
    converter: str,
    conversion_type: str,
) -> Path:
    """Return an existing profile path, writing one if the backend did not."""
    profile = profile_path_for(output)
    if profile.is_file():
        return profile
    return write_conversion_profile(
        input_path=input_arg,
        markdown_path=output,
        converter=converter,
        conversion_type=conversion_type,
    )


def print_json_result(
    input_arg: str,
    output: Path,
    converter: str,
    conversion_type: str,
    profile: Path,
) -> None:
    payload = build_result_payload(
        input_path=input_arg,
        markdown_path=output,
        converter=converter,
        conversion_type=conversion_type,
        profile_path=profile,
    )
    print(json.dumps(payload, ensure_ascii=False))


def _pdf_image_mode(args: argparse.Namespace) -> str | None:
    image_mode = args.images
    if args.no_images:
        image_mode = "none"
    if args.filter_images:
        image_mode = "filtered"
    return image_mode


def _validate_image_options(args: argparse.Namespace) -> bool:
    selected = sum(bool(value) for value in (args.images, args.no_images, args.filter_images))
    if selected > 1:
        print(
            "[ERROR] --images, --no-images, and --filter-images are mutually exclusive",
            file=sys.stderr,
        )
        return False
    return True


def dispatch_single(
    input_arg: str,
    conversion_type: str,
    output_arg: str | None,
    args: argparse.Namespace,
    unknown_args: list[str],
) -> int:
    """Dispatch one source to the matching existing converter."""
    if conversion_type == "auto":
        conversion_type = detect_source_type(input_arg)

    if conversion_type == "directory":
        print(
            "[ERROR] Directories are not supported by source_to_md.py; "
            "use project_manager.py import-sources for multi-source project intake.",
            file=sys.stderr,
        )
        return 1

    if conversion_type == "markdown":
        output = resolve_output(output_arg, input_arg)
        return write_passthrough(input_arg, output, "markdown", args.json)
    if conversion_type == "text":
        output = resolve_output(output_arg, input_arg)
        return write_passthrough(input_arg, output, "text", args.json)

    if conversion_type == "web":
        output = Path(output_arg) if output_arg else None
        try:
            route = build_conversion_command(
                input_arg,
                output,
                forced_type="web",
                extra_args=unknown_args,
            )
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        rc = run_backend(route.command, route.script_name)
        if rc != 0:
            return rc
        if route.output_path and route.output_path.is_file():
            profile = ensure_profile(input_arg, route.output_path, route.script_name, "web")
            print_output(route.output_path)
            if args.json:
                print_json_result(input_arg, route.output_path, route.script_name, "web", profile)
        return 0

    if conversion_type not in {"pdf", "doc", "excel", "pptx"}:
        print(
            f"[ERROR] Could not determine conversion type for {input_arg!r}. "
            "Use -t pdf|doc|excel|pptx|web|markdown|text.",
            file=sys.stderr,
        )
        return 1

    if not is_url(input_arg) and not Path(input_arg).exists():
        print(f"[ERROR] File not found: {input_arg}", file=sys.stderr)
        return 1

    output = resolve_output(output_arg, input_arg)
    try:
        route = build_conversion_command(
            input_arg,
            output,
            forced_type=conversion_type,
            extra_args=unknown_args,
            pdf_image_mode=_pdf_image_mode(args),
            render_vector_figures=args.render_vector_figures,
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    rc = run_backend(route.command, route.script_name)
    if rc != 0:
        return rc
    if not output.is_file():
        print(f"[ERROR] Expected Markdown output not found: {output}", file=sys.stderr)
        return 1

    profile = ensure_profile(input_arg, output, route.script_name, conversion_type)
    print_output(output)
    if args.json:
        print_json_result(input_arg, output, route.script_name, conversion_type, profile)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-detect source type and convert to Markdown via source_to_md backends.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/source_to_md.py paper.pdf
  python3 scripts/source_to_md.py paper.pdf report.docx deck.pptx
  python3 scripts/source_to_md.py report.docx -o output.md
  python3 scripts/source_to_md.py deck.pptx --json
  python3 scripts/source_to_md.py https://example.com/article -o article.md

Backend-specific flags not listed here are passed through to the selected
converter, so existing converter behavior remains the source of truth.
        """,
    )
    parser.add_argument("inputs", nargs="+", help="Input file(s) or URL(s)")
    parser.add_argument(
        "-t",
        "--type",
        choices=["auto", "pdf", "doc", "excel", "pptx", "web", "markdown", "text"],
        default="auto",
        help="Force a conversion type (default: auto)",
    )
    parser.add_argument("-o", "--output", help="Output Markdown file")
    parser.add_argument(
        "--images",
        choices=["all", "filtered", "none"],
        help="PDF image extraction mode; maps to pdf_to_md.py --images",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Alias for --images none on PDF inputs",
    )
    parser.add_argument(
        "--filter-images",
        action="store_true",
        help="Alias for --images filtered on PDF inputs",
    )
    parser.add_argument(
        "--render-vector-figures",
        action="store_true",
        help="Pass through to pdf_to_md.py for PDF vector figure rendering",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable result after successful conversion",
    )
    return parser


def _has_pdf_image_flags(args: argparse.Namespace) -> bool:
    return bool(args.images or args.no_images or args.filter_images or args.render_vector_figures)


def _conversion_type_for_input(input_arg: str, requested_type: str) -> str:
    if requested_type == "auto":
        return detect_source_type(input_arg)
    return requested_type


def _validate_pdf_image_flags(args: argparse.Namespace, conversion_types: list[str]) -> bool:
    if not _has_pdf_image_flags(args):
        return True
    if any(conversion_type != "pdf" for conversion_type in conversion_types):
        print("[ERROR] Image extraction flags are currently supported only for PDFs", file=sys.stderr)
        return False
    return True


def dispatch_many(
    inputs: list[str],
    args: argparse.Namespace,
    unknown_args: list[str],
    conversion_types: list[str],
) -> int:
    success_count = 0
    failed: list[tuple[str, int]] = []
    batch_mode = len(inputs) > 1

    for input_arg, conversion_type in zip(inputs, conversion_types):
        output_arg = args.output
        if batch_mode:
            output_arg = _default_batch_output(input_arg, conversion_type)
            _print_status(f"\n==> {input_arg}")

        rc = dispatch_single(input_arg, conversion_type, output_arg, args, unknown_args)
        if rc == 0:
            success_count += 1
        else:
            failed.append((input_arg, rc))

    if batch_mode:
        _print_status(f"\n[Done] Success: {success_count}/{len(inputs)}, Failed: {len(failed)}")
        if failed:
            _print_status("\n[Failed inputs]:")
            for input_arg, rc in failed:
                _print_status(f"  - {input_arg}: exit {rc}")
            return 1
    return 0 if not failed else failed[0][1]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown_args = parser.parse_known_args(argv)

    if not _validate_image_options(args):
        return 2

    if len(args.inputs) > 1 and args.output:
        print("[ERROR] -o/--output is only valid with a single input", file=sys.stderr)
        return 2

    conversion_types = [_conversion_type_for_input(item, args.type) for item in args.inputs]
    if not _validate_pdf_image_flags(args, conversion_types):
        return 2

    if unknown_args and any(
        conversion_type in {"markdown", "text"} for conversion_type in conversion_types
    ):
        print(
            "[ERROR] Backend-specific flags cannot be used with markdown/text passthrough inputs",
            file=sys.stderr,
        )
        return 2

    return dispatch_many(args.inputs, args, unknown_args, conversion_types)


if __name__ == "__main__":
    raise SystemExit(main())
