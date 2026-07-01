#!/usr/bin/env python3
"""
PPT Master - Source Converter Batch Helpers

Share explicit multi-file and directory expansion logic across source_to_md
backend converters.

Usage:
    Imported by scripts/source_to_md/*_to_md.py

Examples:
    run_path_batch(["docs"], {".docx"}, None, convert_one)

Dependencies:
    None
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path


ConvertOne = Callable[[Path, Path], bool]
IsSupportedFile = Callable[[Path], bool]


def _print_status(message: str) -> None:
    print(message, file=sys.stderr)


def expand_directory_inputs(
    inputs: list[str],
    is_supported_file: IsSupportedFile,
    is_external_ref: Callable[[str], bool] | None = None,
) -> tuple[list[str], list[str], bool]:
    """Expand non-recursive directory inputs while preserving other items."""
    expanded: list[str] = []
    errors: list[str] = []
    saw_directory = False
    is_external = is_external_ref or (lambda _item: False)

    for item in inputs:
        if is_external(item):
            expanded.append(item)
            continue
        path = Path(item)
        if path.is_dir():
            saw_directory = True
            matches = sorted(
                child for child in path.iterdir()
                if child.is_file() and is_supported_file(child)
            )
            if matches:
                expanded.extend(str(match) for match in matches)
            else:
                errors.append(f"{item}: no supported files found")
            continue
        expanded.append(item)

    return expanded, errors, saw_directory


def _output_key(path: Path) -> Path:
    return path.resolve(strict=False)


def unique_output_path(output_dir: Path, stem: str, used_outputs: set[Path]) -> Path:
    """Return an in-run unique Markdown path without consulting the filesystem."""
    base = stem or "output"
    candidate = output_dir / f"{base}.md"
    suffix = 2
    while _output_key(candidate) in used_outputs:
        candidate = output_dir / f"{base}_{suffix}.md"
        suffix += 1
    used_outputs.add(_output_key(candidate))
    return candidate


def _output_for(
    source: Path,
    output_arg: str | None,
    batch_mode: bool,
    used_outputs: set[Path],
) -> Path:
    if output_arg and batch_mode:
        return unique_output_path(Path(output_arg), source.stem, used_outputs)
    if output_arg:
        return Path(output_arg)
    return source.with_suffix(".md")


def run_path_batch(
    inputs: list[str],
    supported_suffixes: set[str],
    output_arg: str | None,
    convert_one: ConvertOne,
) -> int:
    """Run one converter across explicit files and non-recursive directories."""
    expanded, expansion_errors, saw_directory = expand_directory_inputs(
        inputs,
        lambda path: path.suffix.lower() in supported_suffixes,
    )
    sources = [Path(item) for item in expanded]
    batch_mode = saw_directory or len(sources) > 1

    if output_arg and batch_mode:
        output_dir = Path(output_arg)
        if output_dir.exists() and not output_dir.is_dir():
            _print_status(f"[ERROR] Batch output path is not a directory: {output_arg}")
            return 1
        output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    failed: list[str] = []
    skipped: list[str] = list(expansion_errors)
    used_outputs: set[Path] = set()

    for source in sources:
        output = _output_for(source, output_arg, batch_mode, used_outputs)
        if batch_mode:
            _print_status(f"\n==> {source}")
        try:
            converted = convert_one(source, output)
            sys.stdout.flush()
            if converted:
                success_count += 1
            else:
                failed.append(str(source))
        except Exception as exc:
            sys.stdout.flush()
            failed.append(f"{source}: {exc}")
            _print_status(f"[ERROR] {source}: {exc}")

    if batch_mode:
        sys.stdout.flush()
        _print_status(f"\n[Done] Success: {success_count}/{len(sources)}, Failed: {len(failed)}")
        if skipped:
            _print_status("\n[Skipped directories]:")
            for item in skipped:
                _print_status(f"  - {item}")
        if failed:
            _print_status("\n[Failed inputs]:")
            for item in failed:
                _print_status(f"  - {item}")

    if not sources:
        return 1
    return 0 if not failed and not skipped else 1
