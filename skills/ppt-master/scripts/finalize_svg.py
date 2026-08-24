#!/usr/bin/env python3
"""
PPT Master - SVG Post-processing Tool (Unified Entry Point)

Processes SVG files from svg_output/ and produces the visual preview in
svg_final/, embedding supported raster/SVG assets. Native PPTX export continues
to read svg_output/ by default; svg_final/ may be opened directly or inserted
as an SVG image. EMF/WMF assets retain their external-reference exception.
By default, all processing steps are executed. You can also specify individual
steps via arguments.

Architecture note: this module's outputs feed svg_final/ on disk AND its
sub-modules (svg_finalize.embed_icons, svg_finalize.flatten_tspan, ...)
are memory-reused by svg_to_pptx during native conversion. Deleting any
step here may also break native pptx output, not just svg_final/.
See scripts/docs/svg-pipeline.md before modifying the shared pipeline.

Usage:
    # Execute all processing steps (recommended)
    python3 scripts/finalize_svg.py <project_directory>

    # Execute only specific steps
    python3 scripts/finalize_svg.py <project_directory> --only embed-icons align-images

Examples:
    python3 scripts/finalize_svg.py projects/my_project
    python3 scripts/finalize_svg.py projects/ppt169_demo --only embed-icons

Processing options:
    embed-icons   - Expand project icons and static same-document <use>
    align-images  - Align (slice/meet) and Base64-embed all <image> in one pass.
                    Replaces the former crop-images + fix-aspect + embed-images
                    trio. The old names remain accepted as aliases for the
                    merged step, so existing --only invocations keep working.
    flatten-text  - Convert <tspan> to independent <text> (for special renderers)
"""

import argparse
import os
import shutil
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import TextIO
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

# Import finalize helpers from the internal package.
sys.path.insert(0, str(Path(__file__).parent))
from resource_paths import icon_search_dirs_for_project  # noqa: E402
from svg_finalize.align_embed_images import (
    align_and_embed_images_in_svg,
    count_office_vector_refs_in_svg,
)
from svg_finalize.embed_icons import process_svg_file as embed_icons_in_file
from svg_to_pptx.geometry_properties import (
    GeometryStyleError,
    materialize_inline_geometry_in_file,
)
from svg_to_pptx.use_expander import (
    UseExpansionError,
    expand_local_use_references_in_file,
)


class FlattenTextResult(Enum):
    """Describe whether flattening changed a file, skipped it, or failed."""

    CHANGED = "changed"
    UNCHANGED = "unchanged"
    ERROR = "error"


def safe_print(text: str, *, file: TextIO | None = None) -> None:
    """Print text while tolerating Windows terminal encoding limits."""
    stream = file or sys.stdout
    try:
        print(text, file=stream)
    except UnicodeEncodeError:
        replacements = {
            chr(0x23F3): "[..]",
            chr(0x2705): "[DONE]",
            chr(0x274C): "[ERROR]",
            chr(0x26A0) + chr(0xFE0F): "[WARN]",
            chr(0x1F4C1): "[DIR]",
            chr(0x1F4C4): "[FILE]",
            chr(0x1F4E6): "[OK]",
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        print(text, file=stream)


def process_flatten_text(
    svg_file: Path,
    verbose: bool = False,
) -> FlattenTextResult:
    """Flatten text in one SVG and report changed, unchanged, or error."""
    try:
        from svg_finalize.flatten_tspan import flatten_text_with_tspans

        tree = ET.parse(str(svg_file))
        changed = flatten_text_with_tspans(tree)

        if changed:
            tree.write(str(svg_file), encoding='unicode', xml_declaration=False)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: text flattened")
            return FlattenTextResult.CHANGED
        return FlattenTextResult.UNCHANGED
    except Exception as exc:
        safe_print(
            f"   [ERROR] {svg_file.name}: text flattening failed: {exc}",
            file=sys.stderr,
        )
        return FlattenTextResult.ERROR


def _path_lexists(path: Path) -> bool:
    """Return whether a path or dangling symlink occupies the target name."""
    return os.path.lexists(path)


def _publish_candidate_directory(candidate_dir: Path, output_dir: Path) -> None:
    """Publish one staged directory and restore the previous output on failure."""
    if output_dir.is_symlink() or (
        _path_lexists(output_dir) and not output_dir.is_dir()
    ):
        raise RuntimeError(f"Output path must be a real directory: {output_dir}")

    transaction_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}.publish-",
            dir=output_dir.parent,
        )
    )
    backup_dir = transaction_dir / "previous"
    preserve_backup = False

    try:
        if output_dir.is_dir():
            try:
                os.replace(output_dir, backup_dir)
                os.replace(candidate_dir, output_dir)
            except BaseException as publish_error:
                try:
                    if _path_lexists(backup_dir):
                        if _path_lexists(output_dir):
                            failed_output = transaction_dir / "failed-publish"
                            os.replace(output_dir, failed_output)
                        os.replace(backup_dir, output_dir)
                except BaseException as restore_error:
                    if (
                        not _path_lexists(backup_dir)
                        and _path_lexists(output_dir)
                    ):
                        raise publish_error
                    preserve_backup = _path_lexists(backup_dir)
                    raise RuntimeError(
                        "Failed to publish svg_final and restore the previous "
                        "directory; recovery directory: "
                        f"{transaction_dir}"
                    ) from restore_error
                raise
        else:
            os.replace(candidate_dir, output_dir)
    finally:
        if not preserve_backup:
            shutil.rmtree(transaction_dir, ignore_errors=True)


def _process_candidate_directory(
    candidate_dir: Path,
    *,
    options: dict[str, bool],
    quiet: bool,
    compress: bool,
    max_dimension: int | None,
    image_scale: float,
    icons_dir: Path,
    icons_fallback_dir: Path | None,
) -> bool:
    """Run every selected finalization pass against one unpublished candidate."""
    # Core normalization: downstream image/rect processors read XML geometry.
    geometry_count = 0
    for svg_file in candidate_dir.glob('*.svg'):
        try:
            geometry_count += materialize_inline_geometry_in_file(svg_file)
        except (OSError, ET.ParseError, GeometryStyleError) as exc:
            safe_print(
                f"[ERROR] {svg_file.name}: inline geometry materialization failed: {exc}"
            )
            return False

    # Step 1: Expand project icons, then standard same-document use references.
    if options.get('embed_icons'):
        if not quiet:
            safe_print("[1/3] Expanding icons + local use references...")
        icons_count = 0
        for svg_file in candidate_dir.glob('*.svg'):
            count = embed_icons_in_file(
                svg_file,
                icons_dir,
                dry_run=False,
                verbose=False,
                fallback_dir=icons_fallback_dir,
            )
            icons_count += count
        for svg_file in candidate_dir.glob('*.svg'):
            try:
                geometry_count += materialize_inline_geometry_in_file(svg_file)
            except (OSError, ET.ParseError, GeometryStyleError) as exc:
                safe_print(
                    f"[ERROR] {svg_file.name}: expanded icon geometry "
                    f"materialization failed: {exc}"
                )
                return False
        local_use_count = 0
        for svg_file in candidate_dir.glob('*.svg'):
            try:
                local_use_count += expand_local_use_references_in_file(svg_file)
            except (OSError, ET.ParseError, UseExpansionError) as exc:
                safe_print(
                    f"[ERROR] {svg_file.name}: local <use> expansion failed: {exc}"
                )
                return False
        if not quiet:
            if icons_count > 0:
                safe_print(f"      {icons_count} icon(s) embedded")
            else:
                safe_print("      No icons")
            if local_use_count > 0:
                safe_print(f"      {local_use_count} local use reference(s) expanded")
            else:
                safe_print("      No local use references")

    if not quiet and geometry_count:
        safe_print(
            f"[PREP] {geometry_count} inline geometry declaration(s) materialized"
        )

    # Step 2: Align (slice/meet) and Base64-embed all <image> in one pass.
    # Replaces the former crop-images / fix-aspect / embed-images trio: the
    # spatial transform (slice → crop, meet → fit-box) and the asset embed
    # are mutually exclusive branches per image, sequenced together so each
    # SVG is only parsed and serialized once and each bitmap is only read
    # from disk once.
    if options.get('align_images'):
        if not quiet:
            safe_print("[2/3] Aligning + embedding images...")
        img_count = 0
        img_errors = 0
        office_vector_count = 0
        for svg_file in candidate_dir.glob('*.svg'):
            office_vector_count += count_office_vector_refs_in_svg(svg_file)
            count, errs = align_and_embed_images_in_svg(
                svg_file,
                dry_run=False,
                verbose=False,
                compress=compress,
                max_dimension=max_dimension,
                image_scale=image_scale,
            )
            img_count += count
            img_errors += errs
        if img_errors:
            safe_print(
                f"[ERROR] Image alignment/embedding failed for "
                f"{img_errors} image(s); svg_final was not published",
                file=sys.stderr,
            )
            return False
        if not quiet:
            if img_count > 0:
                msg = f"      {img_count} image(s) aligned + embedded"
                safe_print(msg)
                if office_vector_count:
                    safe_print(
                        f"      {office_vector_count} Office vector(s) left external "
                        "for native PPTX passthrough"
                    )
            elif office_vector_count:
                safe_print(
                    f"      {office_vector_count} Office vector(s) left external "
                    "for native PPTX passthrough"
                )
            else:
                safe_print("      No images")

    # Step 3: Flatten text.
    if options.get('flatten_text'):
        if not quiet:
            safe_print("[3/3] Flattening text...")
        flatten_count = 0
        flatten_errors = 0
        for svg_file in candidate_dir.glob('*.svg'):
            result = process_flatten_text(svg_file, verbose=False)
            if result is FlattenTextResult.CHANGED:
                flatten_count += 1
            elif result is FlattenTextResult.ERROR:
                flatten_errors += 1
        if flatten_errors:
            safe_print(
                f"[ERROR] Text flattening failed for {flatten_errors} file(s); "
                "svg_final was not published",
                file=sys.stderr,
            )
            return False
        if not quiet:
            if flatten_count > 0:
                safe_print(f"      {flatten_count} file(s) processed")
            else:
                safe_print("      No processing needed")

    return True


def finalize_project(
    project_dir: Path,
    options: dict[str, bool],
    dry_run: bool = False,
    quiet: bool = False,
    compress: bool = True,
    max_dimension: int | None = 2560,
    image_scale: float = 2.0,
) -> bool:
    """
    Finalize SVG files in the project

    Args:
        project_dir: Project directory path
        options: Processing options dictionary
        dry_run: Preview only, do not execute
        quiet: Quiet mode, reduce output
        compress: Compress images before embedding
        max_dimension: Downscale images exceeding this dimension
        image_scale: Target image pixels per SVG display pixel
    """
    svg_output = project_dir / 'svg_output'
    svg_final = project_dir / 'svg_final'
    icons_dir, icons_fallback_dir = icon_search_dirs_for_project(project_dir)

    # Check if svg_output exists
    if not svg_output.exists():
        safe_print(f"[ERROR] svg_output directory not found: {svg_output}")
        return False

    # Get list of SVG files
    svg_files = list(svg_output.glob('*.svg'))
    if not svg_files:
        safe_print(f"[ERROR] No SVG files in svg_output")
        return False

    if not quiet:
        print()
        safe_print(f"[DIR] Project: {project_dir.name}")
        safe_print(f"[FILE] {len(svg_files)} SVG file(s)")

    if dry_run:
        safe_print("[PREVIEW] Preview mode, no operations will be performed")
        return True

    candidate_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{svg_final.name}.candidate-",
            dir=svg_final.parent,
        )
    )
    try:
        try:
            shutil.copytree(svg_output, candidate_dir, dirs_exist_ok=True)
            candidate_ready = _process_candidate_directory(
                candidate_dir,
                options=options,
                quiet=quiet,
                compress=compress,
                max_dimension=max_dimension,
                image_scale=image_scale,
                icons_dir=icons_dir,
                icons_fallback_dir=icons_fallback_dir,
            )
        except Exception as exc:
            safe_print(
                f"[ERROR] SVG finalization failed before publish: {exc}",
                file=sys.stderr,
            )
            return False

        if not candidate_ready:
            return False

        try:
            _publish_candidate_directory(candidate_dir, svg_final)
        except (OSError, RuntimeError) as exc:
            safe_print(
                f"[ERROR] svg_final publish failed: {exc}",
                file=sys.stderr,
            )
            return False
    finally:
        shutil.rmtree(candidate_dir, ignore_errors=True)

    # Done
    if not quiet:
        print()
        safe_print("[OK] Done!")
        print()
        print("Next steps:")
        print(f"  python scripts/svg_to_pptx.py \"{project_dir}\"")

    return True


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description='PPT Master - SVG Post-processing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s projects/my_project           # Execute all processing (default)
  %(prog)s projects/my_project --only embed-icons align-images
  %(prog)s projects/my_project -q        # Quiet mode

Processing options (for --only):
  embed-icons   Expand project icons and static same-document <use>
  align-images  Align (slice/meet) + Base64-embed all <image> (single pass)
  flatten-text  Flatten text

Aliases (still accepted):
  crop-images, fix-aspect, embed-images  → all map to align-images
        '''
    )

    parser.add_argument('project_dir', type=Path, help='Project directory path')
    parser.add_argument(
        '--only', nargs='+', metavar='OPTION',
        choices=[
            'embed-icons',
            'align-images',
            # Backwards-compatible aliases — all three map to align-images now.
            'crop-images', 'fix-aspect', 'embed-images',
            'flatten-text',
        ],
        help=('Execute only specified processing steps (default: all). '
              'crop-images / fix-aspect / embed-images are accepted as '
              'aliases for the merged align-images step.'),
    )
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview only, do not execute')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Quiet mode, reduce output')
    parser.add_argument('--compress', dest='compress', action='store_true', default=True,
                        help='Compress images before embedding (default)')
    parser.add_argument('--no-compress', dest='compress', action='store_false',
                        help='Disable image compression before embedding')
    parser.add_argument('--max-dimension', type=int, default=2560,
                        help='Downscale images exceeding this dimension on either axis (default: 2560)')
    parser.add_argument('--image-scale', type=float, default=2.0,
                        help='Target image pixels per SVG display pixel (default: 2.0)')

    args = parser.parse_args()

    if not args.project_dir.exists():
        safe_print(f"[ERROR] Project directory does not exist: {args.project_dir}")
        sys.exit(1)

    # Aliases: any of crop-images / fix-aspect / embed-images implies the
    # merged align-images step. Older invocations stay valid.
    _ALIGN_ALIASES = {'align-images', 'crop-images', 'fix-aspect', 'embed-images'}

    # Determine processing options
    if args.only:
        only = set(args.only)
        options = {
            'embed_icons': 'embed-icons' in only,
            'align_images': bool(only & _ALIGN_ALIASES),
            'flatten_text': 'flatten-text' in only,
        }
    else:
        # Execute all by default
        options = {
            'embed_icons': True,
            'align_images': True,
            'flatten_text': True,
        }

    if args.max_dimension < 1:
        safe_print("[ERROR] --max-dimension must be >= 1")
        sys.exit(1)
    if args.image_scale < 1:
        safe_print("[ERROR] --image-scale must be >= 1")
        sys.exit(1)

    success = finalize_project(args.project_dir, options, args.dry_run, args.quiet,
                               compress=args.compress,
                               max_dimension=args.max_dimension,
                               image_scale=args.image_scale)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
