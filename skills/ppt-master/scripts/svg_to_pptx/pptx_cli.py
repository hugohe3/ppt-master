"""CLI entry point for svg_to_pptx."""

from __future__ import annotations

import sys
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __package__ in {None, ''}:
    import types

    package = types.ModuleType('svg_to_pptx')
    package.__path__ = [str(Path(__file__).resolve().parent)]  # type: ignore[attr-defined]
    sys.modules.setdefault('svg_to_pptx', package)
    __package__ = 'svg_to_pptx'

from .pptx_dimensions import CANVAS_FORMATS, get_project_info, get_viewbox_dimensions
from .pptx_discovery import find_svg_files, find_notes_files
from .pptx_builder import create_pptx_with_native_svg
from .pptx_narration import NARRATION_EXTENSIONS, find_narration_files, probe_audio_duration
from .pptx_slide_xml import TRANSITIONS
from .animation_config import load_animation_config, validate_animation_config

try:
    from pptx_animations import ANIMATIONS as _ANIMATIONS
except ImportError:
    _ANIMATIONS = {}


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _recorded_narration_on_click_slides(
    ref_files: list[Path],
    animation_config: dict | None,
    animation: str | None,
    animation_trigger: str,
    animation_cli_overrides: dict[str, bool],
) -> list[str]:
    """Return slides whose effective recorded-video animation trigger is on-click."""
    slides_cfg = _as_dict(_as_dict(animation_config).get('slides'))
    blocked: list[str] = []
    for svg_path in ref_files:
        slide_cfg = _as_dict(slides_cfg.get(svg_path.stem))
        anim_cfg = _as_dict(slide_cfg.get('animation'))

        slide_animation = animation
        if not animation_cli_overrides.get('animation') and 'effect' in anim_cfg:
            cfg_effect = str(anim_cfg.get('effect'))
            slide_animation = None if cfg_effect == 'none' else cfg_effect
        if slide_animation is None:
            continue

        slide_trigger = animation_trigger
        if not animation_cli_overrides.get('animation_trigger') and anim_cfg.get('trigger'):
            slide_trigger = str(anim_cfg.get('trigger'))
        if slide_trigger == 'on-click':
            blocked.append(svg_path.stem)
    return blocked


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the SVG to PPTX conversion tool."""
    transition_choices = (
        ['none'] + (list(TRANSITIONS.keys()) if TRANSITIONS
                    else ['fade', 'push', 'wipe', 'split', 'strips', 'cover', 'random'])
    )

    animation_choices = (
        ['none'] + (list(_ANIMATIONS.keys()) if _ANIMATIONS
                    else ['fade', 'fly', 'zoom', 'appear'])
        + ['auto', 'mixed', 'random']
    )

    parser = argparse.ArgumentParser(
        description='PPT Master - SVG to PPTX Tool (Office Compatibility Mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
    %(prog)s examples/ppt169_demo                         # Default: native pptx -> exports/, svg_output -> backup/<ts>/
    %(prog)s examples/ppt169_demo --svg-snapshot         # Also emit SVG-rendered snapshot pptx
    %(prog)s examples/ppt169_demo --only legacy          # Only SVG image version (skips native)
    %(prog)s examples/ppt169_demo -o out.pptx            # Explicit path (no backup/)

    # Disable transition / change transition effect
    %(prog)s examples/ppt169_demo -t none
    %(prog)s examples/ppt169_demo -t push --transition-duration 1.0

SVG source directory (-s):
    output   - svg_output (hand-authored source; native default)
    final    - svg_final (post-processed; legacy SVG-image path source)
    <any>    - Specify a subdirectory name directly
    Omit -s to use the default: native reads svg_output, legacy reads svg_final.

Transition effects (-t/--transition):
    {', '.join(transition_choices)}

Per-element entrance animation (-a/--animation, native shapes mode):
    {', '.join(animation_choices)}
    Notes: applied to top-level <g id="..."> SVG groups in z-order. Default is
           "auto" (map effect from group id: chart→wipe, card-/step-/pillar-→fly,
           title/takeaway→fade; image-like ids hero/figure-/image/img-/kpi cycle
           zoom/dissolve/circle/box/diamond/wheel so multiple images vary across
           the deck; unmatched ids cycle fade/wipe/fly/zoom). Start mode set by
           --animation-trigger, matching PowerPoint's Start dropdown:
             on-click              one presenter click per group
             with-previous         all groups start together on slide entry
             after-previous (default)  cascade on slide entry;
                                       gap = --animation-stagger seconds
           mixed (legacy) cycles a larger 16-effect pool by group order;
           random samples from the same legacy pool. Use "-a none" to disable.

Compatibility mode (enabled by default):
    - Automatically generates PNG fallback images, SVG embedded as extension
    - Compatible with all Office versions (including Office LTSC 2021)
    - Newer Office still displays SVG (editable), older versions display PNG
    - Requires svglib: pip install svglib reportlab
    - Use --no-compat to disable (only Office 2019+ supported)

Speaker notes (enabled by default):
    - Automatically reads Markdown notes files from the notes/ directory
    - Supports two naming conventions:
      1. Match by filename (recommended): 01_cover.md corresponds to 01_cover.svg
      2. Match by index: slide01.md corresponds to the 1st SVG (backward compatible)
    - Use --no-notes to disable

Recorded narration:
    %(prog)s examples/ppt169_demo --recorded-narration audio
    - Keeps speaker notes when enabled
    - Prepares PowerPoint recorded timings and narrations
    - Requires one m4a/mp3/wav file per slide
    - Embeds per-slide audio matched by SVG filename / slide number
    - Sets slide auto-advance from audio duration so video export can use
      "recorded timings and narrations"
    - Rejects on-click object animations; use after-previous or with-previous
    %(prog)s examples/ppt169_demo --narration-audio-dir audio
    - Lower-level audio embedding: embeds matched files but allows partial matches
    - Use only when you do not need a complete recorded-timings export
''',
    )

    parser.add_argument('project_path', type=str, help='Project directory path')
    parser.add_argument('-o', '--output', type=str, default=None, help='Output file path')
    parser.add_argument('-s', '--source', type=str, default=None,
                        help='SVG source directory. Default: native reads '
                             'svg_output/ (high-fidelity, preserves icons / '
                             'preserveAspectRatio / rx-ry); legacy reads '
                             'svg_final/ (PPT-internal SVG parser fallback). '
                             'Pass output/final/<name> to force one source.')
    parser.add_argument('-f', '--format', type=str,
                        choices=list(CANVAS_FORMATS.keys()), default=None,
                        help='Specify canvas format')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')

    parser.add_argument('--no-compat', action='store_true',
                        help='Disable Office compatibility mode (pure SVG only, requires Office 2019+)')

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--only', type=str, choices=['native', 'legacy'], default=None,
                            help='Only generate one version: native (editable shapes) or legacy (SVG image)')
    mode_group.add_argument('--native', action='store_true', default=False,
                            help='(Deprecated, now default) Convert SVG to native DrawingML shapes')
    merge_group = parser.add_mutually_exclusive_group()
    merge_group.add_argument('--merge-paragraphs', action='store_true', dest='merge_paragraphs',
                             help='Compatibility no-op: mergeable paragraph blocks are merged '
                                  'by default.')
    merge_group.add_argument('--no-merge', action='store_false', dest='merge_paragraphs',
                             help='Disable paragraph merging. Every dy-stacked line becomes '
                                  'its own text frame for strict SVG line-layout fidelity.')
    parser.set_defaults(merge_paragraphs=True)
    parser.add_argument('--conversion-trace', action='store_true', default=False,
                        help='Write a JSON diagnostics report next to the native PPTX '
                             '(<output>.trace.json). Records per-slide SVG element '
                             'conversion decisions for debugging.')
    parser.add_argument('--native-objects', action='store_true', default=False,
                        help='Opt in to converting explicit data-pptx-native table/chart '
                             'markers into native PowerPoint objects. Default off: marked '
                             'groups export through their SVG fallback children.')
    parser.add_argument('--svg-snapshot', action='store_true', default=False,
                        help='Also emit the SVG-rendered snapshot pptx alongside '
                             'the native pptx in exports/ (named '
                             '<project>_<ts>_svg.pptx). Off by default — the '
                             'native pptx is the canonical output; live preview '
                             'already provides the SVG visual reference. '
                             'Note: the svg_output/ source snapshot is always written to backup/<ts>/ '
                             'regardless of this flag.')
    parser.add_argument('--no-image-optimize', action='store_true',
                        help='Disable native PPTX raster image optimization; embeds original image bytes.')
    parser.add_argument('--image-max-dimension', type=int, default=2560,
                        help='Maximum optimized raster image dimension in pixels (default: 2560).')
    parser.add_argument('--image-sizing', choices=['cap', 'display'], default='cap',
                        help='Raster sizing mode: cap only limits source dimensions; '
                             'display sizes from the SVG rendered box (default: cap).')
    parser.add_argument('--image-scale', type=float, default=2.0,
                        help='Target optimized image pixels per SVG display pixel '
                             'when --image-sizing=display (default: 2.0).')
    parser.add_argument('--image-quality', type=int, default=85,
                        help='JPEG quality for optimized opaque raster images, 1-100 (default: 85).')

    def non_negative_float(value: str) -> float:
        try:
            number = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"must be a number: {value}") from exc
        if number < 0:
            raise argparse.ArgumentTypeError("must be non-negative")
        return number

    parser.add_argument('-t', '--transition', type=str, choices=transition_choices, default=None,
                        help='Page transition effect (default: fade, use "none" to disable)')
    parser.add_argument('--transition-duration', type=non_negative_float, default=None,
                        help='Transition duration in seconds (default: 0.4)')
    parser.add_argument('--auto-advance', type=non_negative_float, default=None,
                        help='Auto-advance interval in seconds (default: manual advance)')

    parser.add_argument('-a', '--animation', type=str, choices=animation_choices,
                        default=None,
                        help='Per-element entrance animation (native shapes mode '
                             'only). Default "none" (no auto element builds; page '
                             'transitions still apply). Pick a single effect, "auto" '
                             '(map effect from group id — image-like ids cycle a '
                             'richer pool for visual variation, fallback cycles fade/'
                             'wipe/fly/zoom), "mixed" (legacy 16-effect pool), or '
                             '"random".')
    parser.add_argument('--animation-duration', type=non_negative_float, default=None,
                        help='Per-element entrance duration in seconds (default: 0.4)')
    parser.add_argument('--animation-trigger', type=str,
                        choices=['on-click', 'with-previous', 'after-previous'],
                        default=None,
                        help='Per-element Start mode (matches PowerPoint Start dropdown): '
                             '"on-click" (one click per element), '
                             '"with-previous" (all start together on slide entry), '
                             '"after-previous" (default, cascade after the previous element).')
    parser.add_argument('--animation-stagger', type=non_negative_float, default=None,
                        help='Delay between elements in --animation-trigger=after-previous '
                             '(seconds, default 0.5). Ignored in other modes.')
    parser.add_argument('--animation-config', type=str, default=None,
                        help='Optional per-slide/per-object animation config. '
                             'Default: <project>/animations.json when present.')

    parser.add_argument('--no-notes', action='store_true',
                        help='Disable speaker notes embedding (enabled by default)')
    parser.add_argument('--narration-audio-dir', type=str, default=None,
                        help='Low-level audio embedding from this directory; allows partial matches')
    parser.add_argument('--use-narration-timings', action='store_true',
                        help='Set slide auto-advance timings from narration audio durations')
    parser.add_argument('--recorded-narration', type=str, default=None,
                        help='Prepare PowerPoint recorded timings and narrations from a complete audio directory')
    parser.add_argument('--narration-padding', type=float, default=0.5,
                        help='Seconds to add after each narration before auto-advance (default: 0.5)')

    parser.add_argument('--cache-dir', type=str, default=None,
                        help='Cache directory for SVG→PNG renders (default: '
                             '<project>/.cache/svg_png). Cache key uses SVG content '
                             'hash + size + renderer; safe across renderer switches. '
                             'Removed automatically after a successful export.')
    parser.add_argument('--no-cache', action='store_true',
                        help='Disable the SVG→PNG cache for this run (still parallel).')
    parser.add_argument('--keep-cache', action='store_true',
                        help='Keep the SVG→PNG cache directory after export '
                             '(default: removed on success to keep project clean).')
    parser.add_argument('--workers', type=int, default=None,
                        help='Parallel workers for SVG→PNG pre-rendering. '
                             'Default: min(cpu, pages, 8). Set 1 for sequential.')

    args = parser.parse_args(argv)

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        return 1
    if args.image_max_dimension < 1:
        print("Error: --image-max-dimension must be >= 1", file=sys.stderr)
        return 1
    if args.image_scale < 1:
        print("Error: --image-scale must be >= 1", file=sys.stderr)
        return 1
    if not 1 <= args.image_quality <= 100:
        print("Error: --image-quality must be between 1 and 100", file=sys.stderr)
        return 1

    try:
        project_info = get_project_info(str(project_path))
        project_name = project_info.get('name', project_path.name)
        detected_format = project_info.get('format')
    except Exception:
        project_name = project_path.name
        detected_format = None

    canvas_format = args.format
    if canvas_format is None and detected_format and detected_format != 'unknown':
        canvas_format = detected_format

    # Determine which versions to generate.
    # Default is native-only; SVG snapshot is opt-in via --svg-snapshot.
    # --only native / --only legacy still force a single version explicitly.
    only_mode = args.only
    if only_mode == 'native':
        gen_native, gen_legacy = True, False
    elif only_mode == 'legacy':
        gen_native, gen_legacy = False, True
    else:
        gen_native = True
        gen_legacy = args.svg_snapshot

    # Pipeline split: native pptx gets the high-fidelity svg_output/ source
    # (icons, preserveAspectRatio, rounded-rect rx/ry are all preserved by the
    # converter); legacy pptx still needs svg_final/ because PowerPoint's
    # internal SVG parser cannot handle <use data-icon> or honour
    # preserveAspectRatio. An explicit -s overrides both branches so callers
    # can keep the previous single-source behaviour for unusual workflows.
    explicit_source = args.source is not None
    native_source = args.source if explicit_source else 'output'
    legacy_source = args.source if explicit_source else 'final'

    native_files: list[Path] = []
    legacy_files: list[Path] = []
    native_source_dir = ''
    legacy_source_dir = ''

    if gen_native:
        native_files, native_source_dir = find_svg_files(project_path, native_source)
    if gen_legacy:
        legacy_files, legacy_source_dir = find_svg_files(project_path, legacy_source)

    # Reference list for cross-product lookups (notes / narration matching).
    # native_files and legacy_files share filenames because svg_final/ is
    # copytree'd from svg_output/, so either list works for matching.
    ref_files = native_files or legacy_files
    if not ref_files:
        print("Error: No SVG files found")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir: Path | None = None
    legacy_path: Path | None = None
    if args.output:
        output_base = Path(args.output)
        native_path = output_base
        if gen_legacy:
            stem = output_base.stem
            legacy_path = output_base.parent / f"{stem}_svg{output_base.suffix}"
    else:
        exports_dir = project_path / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        native_path = exports_dir / f"{project_name}_{timestamp}.pptx"
        # svg_output/ snapshot always goes under backup/<ts>/ in default-flow
        # mode (no -o). --svg-snapshot only controls the optional legacy
        # SVG-rendered pptx, which now sits alongside the native pptx in
        # exports/ rather than nested inside backup/.
        backup_dir = project_path / "backup" / timestamp
        if gen_legacy:
            legacy_path = exports_dir / f"{project_name}_{timestamp}_svg.pptx"

    native_path.parent.mkdir(parents=True, exist_ok=True)
    if legacy_path is not None:
        legacy_path.parent.mkdir(parents=True, exist_ok=True)

    verbose = not args.quiet

    # Honor the actual SVG pixels over a stale project-recorded format. The
    # canvas_format read from project init can disagree with what the Executor
    # actually drew — e.g. a mirror template imported at 2560×1440 while the
    # project was initialized as ppt169 (1280×720). When the first SVG's real
    # viewBox doesn't match the recorded format's dimensions, drop the format
    # so the builder sizes the slide by pixels (custom_pixels path). Standard
    # decks match exactly, so this only changes behavior on the conflict case.
    # An explicit --format always wins and is never second-guessed.
    if args.format is None and canvas_format:
        fmt_info = CANVAS_FORMATS.get(canvas_format)
        actual_dims = get_viewbox_dimensions(ref_files[0])
        if fmt_info and actual_dims:
            fmt_dims = (fmt_info.get('width'), fmt_info.get('height'))
            if fmt_dims != actual_dims:
                if verbose:
                    print(
                        f"  Recorded format '{canvas_format}' "
                        f"({fmt_dims[0]}×{fmt_dims[1]}) differs from SVG viewBox "
                        f"({actual_dims[0]}×{actual_dims[1]}); exporting by SVG pixels"
                    )
                canvas_format = None

    enable_notes = not args.no_notes
    notes: dict[str, str] = {}
    if enable_notes:
        notes = find_notes_files(project_path, ref_files)

    narration_audio: dict[str, Path] = {}
    narration_audio_dir_arg = args.recorded_narration or args.narration_audio_dir
    use_narration_timings = args.use_narration_timings or bool(args.recorded_narration)
    if narration_audio_dir_arg:
        narration_audio_dir = Path(narration_audio_dir_arg)
        if not narration_audio_dir.is_absolute():
            narration_audio_dir = project_path / narration_audio_dir
        if args.recorded_narration and not narration_audio_dir.is_dir():
            print(
                f"Error: Recorded narration directory does not exist: {narration_audio_dir}",
                file=sys.stderr,
            )
            return 1
        narration_audio = find_narration_files(narration_audio_dir, ref_files)
        if verbose:
            print(f"  Narration audio directory: {narration_audio_dir}")
            print(f"  Narration audio matched: {len(narration_audio)}/{len(ref_files)} slide(s)")
        if args.recorded_narration:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    "Error: Recorded narration requires one supported audio file per slide. "
                    f"Matched {len(narration_audio)}/{len(ref_files)} slide(s). "
                    f"Supported extensions: {', '.join(NARRATION_EXTENSIONS)}",
                    file=sys.stderr,
                )
                for stem in missing[:20]:
                    print(f"  Missing audio for: {stem}", file=sys.stderr)
                if len(missing) > 20:
                    print(f"  ... and {len(missing) - 20} more", file=sys.stderr)
                return 1
            unreadable = [
                f"{stem}: {audio_path}"
                for stem, audio_path in sorted(narration_audio.items())
                if probe_audio_duration(audio_path) is None
            ]
            if unreadable:
                print(
                    "Error: Recorded narration requires readable audio durations. "
                    "Install ffprobe/ffmpeg or replace the listed audio files.",
                    file=sys.stderr,
                )
                for item in unreadable[:20]:
                    print(f"  {item}", file=sys.stderr)
                if len(unreadable) > 20:
                    print(f"  ... and {len(unreadable) - 20} more", file=sys.stderr)
                return 1
        elif narration_audio_dir_arg and verbose:
            missing = [path.stem for path in ref_files if path.stem not in narration_audio]
            if missing:
                print(
                    f"  [warn] Narration audio matched {len(narration_audio)}/{len(ref_files)} slide(s); "
                    "unmatched slides will export without audio."
                )

    if args.animation_config:
        config_path = Path(args.animation_config)
        if not config_path.is_absolute():
            config_path = project_path / config_path
        if not config_path.exists():
            print(f"Error: Animation config does not exist: {config_path}")
            return 1

    try:
        animation_config = load_animation_config(project_path, args.animation_config)
    except Exception as exc:
        print(f"Error: Failed to load animation config: {exc}")
        return 1
    if animation_config and verbose:
        config_label = args.animation_config or str(project_path / 'animations.json')
        print(f"  Animation config: {config_label}")
        for warning in validate_animation_config(project_path, animation_config):
            print(f"  [warn] {warning}")

    defaults = animation_config.get('defaults', {}) if animation_config else {}
    transition_defaults = defaults.get('transition', {}) if isinstance(defaults, dict) else {}
    animation_defaults = defaults.get('animation', {}) if isinstance(defaults, dict) else {}

    transition_arg = args.transition
    transition_effect = (
        transition_arg
        if transition_arg is not None
        else transition_defaults.get('effect', 'fade')
    )
    transition = None if transition_effect == 'none' else transition_effect
    transition_duration = (
        args.transition_duration
        if args.transition_duration is not None
        else float(transition_defaults.get('duration', 0.4))
    )

    animation_arg = args.animation
    animation_effect = (
        animation_arg
        if animation_arg is not None
        # Per-element entrance is opt-in by default: auto-firing element builds
        # read as the "AI deck" tell and were unsolicited. Page transitions stay
        # on (see transition default above). Re-enable with -a auto / animations.json.
        else animation_defaults.get('effect', 'none')
    )
    animation = None if animation_effect == 'none' else animation_effect
    animation_duration = (
        args.animation_duration
        if args.animation_duration is not None
        else float(animation_defaults.get('duration', 0.4))
    )
    animation_stagger = (
        args.animation_stagger
        if args.animation_stagger is not None
        else float(animation_defaults.get('stagger', 0.5))
    )
    animation_trigger = (
        args.animation_trigger
        if args.animation_trigger is not None
        else animation_defaults.get('trigger', 'after-previous')
    )

    animation_cli_overrides = {
        'transition': args.transition is not None,
        'transition_duration': args.transition_duration is not None,
        'auto_advance': args.auto_advance is not None,
        'animation': args.animation is not None,
        'animation_duration': args.animation_duration is not None,
        'animation_stagger': args.animation_stagger is not None,
        'animation_trigger': args.animation_trigger is not None,
    }

    if args.recorded_narration and gen_native:
        on_click_slides = _recorded_narration_on_click_slides(
            ref_files,
            animation_config,
            animation,
            animation_trigger,
            animation_cli_overrides,
        )
        if on_click_slides:
            print(
                "Error: --recorded-narration cannot be used with on-click object animations. "
                "Use --animation-trigger after-previous or --animation-trigger with-previous.",
                file=sys.stderr,
            )
            for slide in on_click_slides[:20]:
                print(f"  on-click trigger: {slide}", file=sys.stderr)
            if len(on_click_slides) > 20:
                print(f"  ... and {len(on_click_slides) - 20} more", file=sys.stderr)
            return 1

    if args.no_cache:
        cache_dir: Path | None = None
    elif args.cache_dir:
        cache_dir = Path(args.cache_dir)
        if not cache_dir.is_absolute():
            cache_dir = project_path / cache_dir
    else:
        cache_dir = project_path / '.cache' / 'svg_png'

    # svg_files is per-product (native vs legacy may now read different
    # directories); everything else is shared.
    # Optional per-project document properties. Absent file → factual fields
    # are still stamped at export; only the authored fields stay blank.
    doc_metadata = None
    metadata_path = project_path / 'metadata.json'
    if metadata_path.is_file():
        try:
            loaded = json.loads(metadata_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [warn] metadata.json ignored ({exc})", file=sys.stderr)
        else:
            if isinstance(loaded, dict):
                doc_metadata = loaded
                if verbose:
                    print(f"  Document properties: metadata.json ({len(loaded)} field(s))")
            else:
                print("  [warn] metadata.json ignored (top level is not an object)", file=sys.stderr)

    shared_kwargs = dict(
        canvas_format=canvas_format,
        doc_metadata=doc_metadata,
        verbose=verbose,
        transition=transition,
        transition_duration=transition_duration,
        auto_advance=args.auto_advance,
        use_compat_mode=not args.no_compat,
        notes=notes,
        enable_notes=enable_notes,
        animation=animation,
        animation_duration=animation_duration,
        animation_stagger=animation_stagger,
        animation_trigger=animation_trigger,
        animation_config=animation_config,
        animation_cli_overrides=animation_cli_overrides,
        narration_audio=narration_audio,
        use_narration_timings=use_narration_timings,
        narration_padding=args.narration_padding,
        cache_dir=cache_dir,
        workers=args.workers,
        merge_paragraphs=args.merge_paragraphs,
        image_optimize=not args.no_image_optimize,
        image_max_dimension=args.image_max_dimension,
        image_sizing=args.image_sizing,
        image_scale=args.image_scale,
        image_quality=args.image_quality,
        native_objects=args.native_objects,
    )

    success = True

    # --- Native shapes version (primary) ---
    if gen_native:
        if verbose:
            print("PPT Master - SVG to PPTX Tool")
            print("=" * 50)
            print(f"  Project path: {project_path}")
            print(f"  SVG directory: {native_source_dir}")
            print(f"  Output file: {native_path}")
            print()

        ok = create_pptx_with_native_svg(
            output_path=native_path,
            use_native_shapes=True,
            svg_files=native_files,
            conversion_trace_path=(
                native_path.with_name(native_path.name + '.trace.json')
                if args.conversion_trace else None
            ),
            **shared_kwargs,
        )
        success = success and ok

    # --- SVG image reference version ---
    if gen_legacy:
        if verbose:
            if gen_native:
                print()
                print("-" * 50)
            print("PPT Master - SVG to PPTX Tool (SVG Reference)")
            print("=" * 50)
            print(f"  Project path: {project_path}")
            print(f"  SVG directory: {legacy_source_dir}")
            print(f"  Output file: {legacy_path}")
            print()

        ok = create_pptx_with_native_svg(
            output_path=legacy_path,
            use_native_shapes=False,
            svg_files=legacy_files,
            **shared_kwargs,
        )
        success = success and ok

    # svg_output/ snapshot — runs once per export in default-flow mode,
    # decoupled from --svg-snapshot. Preserves the AI-generated SVG sources
    # under backup/<ts>/svg_output/ for later inspection / re-export.
    if success and backup_dir is not None:
        svg_output_src = project_path / "svg_output"
        if svg_output_src.is_dir():
            backup_dir.mkdir(parents=True, exist_ok=True)
            svg_output_dst = backup_dir / "svg_output"
            try:
                shutil.copytree(svg_output_src, svg_output_dst)
                if verbose:
                    print(f"  svg_output backup: {svg_output_dst}")
            except Exception as exc:
                if verbose:
                    print(f"  [warn] svg_output backup skipped: {exc}")
        elif verbose:
            print(f"  [info] svg_output/ not found, backup skipped")

    if success and cache_dir is not None and cache_dir.is_dir() and not args.keep_cache:
        try:
            shutil.rmtree(cache_dir)
            cache_parent = cache_dir.parent
            if cache_parent.is_dir() and cache_parent.name == '.cache' and not any(cache_parent.iterdir()):
                cache_parent.rmdir()
        except Exception as exc:
            if verbose:
                print(f"  [warn] cache cleanup skipped: {exc}")

    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
