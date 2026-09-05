#!/usr/bin/env python3
"""
PPT Master - Unified Markdown Converter

Auto-detect source type and dispatch to the existing source_to_md converters.

Usage:
    python3 scripts/source_to_md.py <file_or_url_or_dir> [<file_or_url_or_dir> ...] [options]

Examples:
    python3 scripts/source_to_md.py paper.pdf
    python3 scripts/source_to_md.py paper.pdf report.docx deck.pptx
    python3 scripts/source_to_md.py ./sources -o ./markdown
    python3 scripts/source_to_md.py report.docx -o report.md
    python3 scripts/source_to_md.py deck.pptx --json

Dependencies:
    Same as the backend converter selected for the input.
"""

from __future__ import annotations

import argparse
import codecs
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

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
from _batch import expand_directory_inputs, unique_output_path  # noqa: E402
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


def _is_supported_directory_item(path: Path) -> bool:
    return detect_source_type(str(path)) in {
        "pdf", "doc", "excel", "pptx", "markdown", "text",
    }


def _output_is_directory(output_arg: str | None) -> bool:
    """True when -o names an existing directory or ends with a path separator."""
    if not output_arg:
        return False
    if output_arg.endswith(("/", os.sep)):
        return True
    return Path(output_arg).is_dir()


def _dispatch_output_arg(
    input_arg: str,
    conversion_type: str,
    output_arg: str | None,
    batch_mode: bool,
    used_outputs: set[Path],
) -> str | None:
    if output_arg and _output_is_directory(output_arg):
        # A directory is a directory even for one input: the file keeps its
        # default `<stem>.md` name inside it instead of becoming an
        # extension-less file named after the directory.
        batch_mode = True
    if output_arg and batch_mode and conversion_type == "web":
        return None
    if batch_mode and conversion_type != "web":
        default_output = default_markdown_path(input_arg)
        if output_arg:
            default_output = Path(output_arg) / default_output.name
        output = unique_output_path(default_output.parent, default_output.stem, used_outputs)
        if output != default_output:
            _print_status(
                f"[INFO] Renamed output for {input_arg}: {default_output} -> {output} "
                "(input/output collision)"
            )
        return str(output)
    if output_arg:
        # One input with an extension-less -o names the Markdown file, not a
        # directory: `-o sources_cf` writes `sources_cf.md` (a directory is
        # spelled with a trailing separator or already exists).
        if not Path(output_arg).suffix:
            return f"{output_arg}.md"
        return output_arg
    return None


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
        raw = source.read_bytes()
    except OSError as exc:
        print(f"[ERROR] Cannot read {source}: {exc}", file=sys.stderr)
        return 1

    encodings = ("utf-8", "gb18030")
    if raw.startswith(codecs.BOM_UTF8):
        encodings = ("utf-8-sig",)
    elif raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encodings = ("utf-16",)
    for encoding in encodings:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        print(
            f"[ERROR] Cannot decode {source} as {' or '.join(encodings)}. "
            "Save the source as UTF-8 text and retry.",
            file=sys.stderr,
        )
        return 1
    if any(ord(char) < 32 and char not in "\t\n\r\f" for char in text):
        print(f"[ERROR] Binary control characters in {source}; provide a text file.", file=sys.stderr)
        return 1
    if encoding != "utf-8" and output.resolve() == source.resolve():
        print(
            f"[ERROR] {source} uses {encoding}; choose a different -o path for UTF-8 output.",
            file=sys.stderr,
        )
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.resolve() != source.resolve():
        output.write_bytes(text.encode("utf-8"))
    warnings = []
    if encoding != "utf-8":
        warnings.append(f"Detected source encoding: {encoding}; converted to UTF-8.")
    profile = write_conversion_profile(
        input_path=input_arg,
        markdown_path=output,
        converter="source_to_md.py",
        conversion_type=conversion_type,
        warnings=warnings,
    )
    for warning in warnings:
        print(f"[INFO] {warning}")
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


def _read_emit_result(path: Path) -> Path | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    markdown = payload.get("markdown")
    return Path(markdown) if isinstance(markdown, str) and markdown else None


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
    web_output_dir: str | None = None,
) -> int:
    """Dispatch one source to the matching existing converter."""
    if conversion_type == "auto":
        conversion_type = detect_source_type(input_arg)

    if conversion_type == "markdown":
        output = resolve_output(output_arg, input_arg)
        return write_passthrough(input_arg, output, "markdown", args.json)
    if conversion_type == "text":
        output = resolve_output(output_arg, input_arg)
        return write_passthrough(input_arg, output, "text", args.json)

    if conversion_type == "web":
        output = Path(output_arg) if output_arg else None
        emit_result: Path | None = None
        extra_args = list(unknown_args)
        if _skips_images(args) and "--no-images" not in extra_args:
            # web_to_md keeps remote image links instead of downloading the
            # page's images into `<stem>_files/`.
            extra_args.append("--no-images")
        if output is None:
            emit_file = tempfile.NamedTemporaryFile(
                prefix="ppt-master-web-result-",
                suffix=".json",
                delete=False,
            )
            emit_file.close()
            emit_result = Path(emit_file.name)
            extra_args.extend(["--emit-result", str(emit_result)])
            if web_output_dir:
                extra_args.extend(["--dir", web_output_dir])
        try:
            route = build_conversion_command(
                input_arg,
                output,
                forced_type="web",
                extra_args=extra_args,
            )
        except ValueError as exc:
            if emit_result:
                emit_result.unlink(missing_ok=True)
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        rc = run_backend(route.command, route.script_name)
        if rc != 0:
            if emit_result:
                emit_result.unlink(missing_ok=True)
            return rc
        output_path = route.output_path
        if output_path is None and emit_result is not None:
            output_path = _read_emit_result(emit_result)
            emit_result.unlink(missing_ok=True)
        if output_path and output_path.is_file():
            profile = ensure_profile(input_arg, output_path, route.script_name, "web")
            print_output(output_path)
            if args.json:
                print_json_result(input_arg, output_path, route.script_name, "web", profile)
            return 0
        if output is not None:
            print(f"[ERROR] Expected Markdown output not found: {output}", file=sys.stderr)
        else:
            print("[ERROR] Web conversion did not report a Markdown output path", file=sys.stderr)
        return 1

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
  python3 scripts/source_to_md.py ./sources -o ./markdown
  python3 scripts/source_to_md.py report.docx -o output.md
  python3 scripts/source_to_md.py deck.pptx --json
  python3 scripts/source_to_md.py https://example.com/article -o article.md

Backend-specific flags not listed here are passed through to the selected
converter, so existing converter behavior remains the source of truth.
        """,
    )
    parser.add_argument("inputs", nargs="+", help="Input file(s), directories, or URL(s)")
    parser.add_argument(
        "-t",
        "--type",
        choices=["auto", "pdf", "doc", "excel", "pptx", "web", "markdown", "text"],
        default="auto",
        help="Force a conversion type (default: auto)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output Markdown file for one input, or output directory (an existing directory or a path ending in /) for one or more inputs",
    )
    parser.add_argument(
        "--images",
        choices=["all", "filtered", "none"],
        help="PDF image extraction mode; maps to pdf_to_md.py --images",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help=(
            "Skip images: PDF image mode none; web pages keep remote image "
            "links instead of downloading; no-op for Markdown/text"
        ),
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


def _skips_images(args: argparse.Namespace) -> bool:
    return bool(args.no_images or args.images == "none")


def _validate_pdf_image_flags(args: argparse.Namespace, conversion_types: list[str]) -> bool:
    if not _has_pdf_image_flags(args):
        return True
    skip_only = _skips_images(args) and not (
        args.filter_images or args.render_vector_figures
    )
    for conversion_type in conversion_types:
        if conversion_type == "pdf":
            continue
        # Web pages keep remote links; Markdown/text passthrough has no
        # images to skip, so the flag is accepted as a no-op there.
        if conversion_type in {"web", "markdown", "text"} and skip_only:
            continue
        print(
            "[ERROR] Image extraction flags are supported only for PDFs; "
            "--no-images (or --images none) also applies to web pages and "
            "Markdown/text passthrough",
            file=sys.stderr,
        )
        return False
    return True


def dispatch_many(
    inputs: list[str],
    args: argparse.Namespace,
    unknown_args: list[str],
    conversion_types: list[str],
    batch_mode: bool = False,
    initial_failures: list[str] | None = None,
) -> int:
    success_count = 0
    failed: list[str] = []
    skipped: list[str] = list(initial_failures or [])
    batch_mode = batch_mode or len(inputs) > 1 or _output_is_directory(args.output)
    if args.output and batch_mode:
        output_dir = Path(args.output)
        if output_dir.exists() and not output_dir.is_dir():
            print(f"[ERROR] Batch output path is not a directory: {args.output}", file=sys.stderr)
            return 1

    input_paths = {Path(item).resolve() for item in inputs if not is_url(item)}
    used_outputs = set(input_paths)
    output_args = [
        _dispatch_output_arg(
            input_arg,
            conversion_type,
            args.output,
            batch_mode,
            used_outputs,
        )
        for input_arg, conversion_type in zip(inputs, conversion_types)
    ]
    if args.output and not batch_mode and output_args:
        output = Path(output_args[0])
        own_passthrough = (
            output.resolve() in input_paths and conversion_types[0] in {"markdown", "text"}
        )
        if output.exists() and not own_passthrough:
            print(
                f"[ERROR] Refusing to overwrite existing file: {output}. Choose a different -o path.",
                file=sys.stderr,
            )
            return 1

    if args.output and batch_mode:
        Path(args.output).mkdir(parents=True, exist_ok=True)

    for input_arg, conversion_type, output_arg in zip(inputs, conversion_types, output_args):
        web_output_dir = (
            args.output
            if args.output and batch_mode and conversion_type == "web"
            else None
        )
        if batch_mode:
            _print_status(f"\n==> {input_arg}")

        rc = dispatch_single(
            input_arg,
            conversion_type,
            output_arg,
            args,
            unknown_args,
            web_output_dir=web_output_dir,
        )
        if rc == 0:
            success_count += 1
        else:
            failed.append(f"{input_arg}: exit {rc}")

    if batch_mode:
        _print_status(f"\n[Done] Success: {success_count}/{len(inputs)}, Failed: {len(failed)}")
        if skipped:
            _print_status("\n[Skipped directories]:")
            for item in skipped:
                _print_status(f"  - {item}")
        if failed:
            _print_status("\n[Failed inputs]:")
            for item in failed:
                _print_status(f"  - {item}")
    if not inputs:
        return 1
    return 0 if not failed and not skipped else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, unknown_args = parser.parse_known_args(argv)

    if not _validate_image_options(args):
        return 2

    inputs, expansion_errors, saw_directory = expand_directory_inputs(
        args.inputs,
        _is_supported_directory_item,
        is_external_ref=is_url,
    )
    batch_mode = saw_directory or len(inputs) > 1

    conversion_types = [_conversion_type_for_input(item, args.type) for item in inputs]
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

    return dispatch_many(
        inputs,
        args,
        unknown_args,
        conversion_types,
        batch_mode=batch_mode,
        initial_failures=expansion_errors,
    )


if __name__ == "__main__":
    raise SystemExit(main())
