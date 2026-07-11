"""CLI entry point for svg_to_pptx."""

from __future__ import annotations

import sys
import json
import math
import shutil
import argparse
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_animations import (  # noqa: E402
    ANIMATIONS,
    animation_seconds_to_milliseconds,
    normalize_animation_effect,
    normalize_animation_trigger,
)
from pptx_transitions import validate_seconds  # noqa: E402

configure_utf8_stdio()

if __package__ in {None, ''}:
    import types

    package = types.ModuleType('svg_to_pptx')
    package.__path__ = [str(Path(__file__).resolve().parent)]  # type: ignore[attr-defined]
    sys.modules.setdefault('svg_to_pptx', package)
    __package__ = 'svg_to_pptx'

from .dimensions import CANVAS_FORMATS, get_project_info, get_viewbox_dimensions
from .discovery import find_svg_files, find_notes_files
from .builder import create_pptx_with_native_svg
from ..drawingml.theme_colors import ThemeColorError, load_theme_color_spec
from ..drawingml.theme_fonts import (
    ThemeFontError,
    load_master_text_style_spec,
    load_theme_font_spec,
)
from .narration import NARRATION_EXTENSIONS, find_narration_files, probe_audio_duration
from .slide_xml import TRANSITIONS
from .template_structure import (
    TemplateStructureError,
    load_native_structure_contract,
    load_pptx_structure_lock,
    native_structure_lock_errors,
    parse_preserve_slides,
    parse_template_slides,
    template_lock_errors,
)
from ..animation_config import (
    load_animation_config,
    validate_animation_config,
    validate_animation_config_errors,
    validate_transition_config,
)


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _native_object_fallbacks(svg_files: list[Path]) -> list[tuple[str, str, str]]:
    """Return fallback-only native object statuses from SVG inputs."""
    fallbacks: list[tuple[str, str, str]] = []
    for svg_path in svg_files:
        try:
            root = ET.parse(svg_path).getroot()
        except (OSError, ET.ParseError):
            continue
        for elem in root.iter():
            status = elem.get('data-pptx-native-status')
            if not status or elem.tag.rsplit('}', 1)[-1] == 'metadata':
                continue
            marker_id = elem.get('id') or elem.get('data-name') or '<unnamed>'
            fallbacks.append((svg_path.name, marker_id, status))
    return fallbacks


def _recorded_narration_on_click_slides(
    ref_files: list[Path],
    animation_config: dict | None,
    animation: str | None,
    animation_trigger: str,
    animation_cli_overrides: dict[str, bool],
) -> list[str]:
    """Return slides whose effective recorded-video animation trigger is on-click."""
    if animation_cli_overrides.get('animation') and animation is None:
        return []
    slides_cfg = _as_dict(_as_dict(animation_config).get('slides'))
    blocked: list[str] = []
    for svg_path in ref_files:
        slide_cfg = _as_dict(slides_cfg.get(svg_path.stem))
        anim_cfg = _as_dict(slide_cfg.get('animation'))

        slide_animation = animation
        if not animation_cli_overrides.get('animation') and 'effect' in anim_cfg:
            slide_animation = normalize_animation_effect(anim_cfg.get('effect'))
        groups_cfg = _as_dict(slide_cfg.get('groups'))
        has_explicit_animation = any(
            isinstance(group_cfg, dict)
            and 'effect' in group_cfg
            and normalize_animation_effect(group_cfg.get('effect')) is not None
            for group_cfg in groups_cfg.values()
        )
        if slide_animation is None and not has_explicit_animation:
            continue

        slide_trigger = animation_trigger
        if not animation_cli_overrides.get('animation_trigger') and anim_cfg.get('trigger'):
            slide_trigger = normalize_animation_trigger(anim_cfg.get('trigger'))
        if slide_trigger == 'on-click':
            blocked.append(svg_path.stem)
    return blocked


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the SVG to PPTX conversion tool."""
    transition_choices = (
        ['none'] + (list(TRANSITIONS.keys()) if TRANSITIONS
                    else ['fade', 'push', 'wipe', 'split', 'strips', 'cover', 'random'])
    )

    animation_choices = ['none', *ANIMATIONS, 'auto', 'mixed', 'random']

    parser = argparse.ArgumentParser(
        description='PPT Master - SVG to native DrawingML PPTX Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
    %(prog)s examples/ppt169_demo                         # Default: native pptx -> exports/, svg_output -> backup/<ts>/
    %(prog)s examples/ppt169_demo -o out.pptx            # Explicit path (no backup/)

    # Disable transition / change transition effect
    %(prog)s examples/ppt169_demo -t none
    %(prog)s examples/ppt169_demo -t push --transition-duration 1.0

SVG source directory (-s):
    output   - svg_output (hand-authored source; native default)
    final    - svg_final (post-processed preview; diagnostic native input only)
    <any>    - Specify a subdirectory name directly
    Omit -s to use the default: native export reads svg_output.

Transition effects (-t/--transition):
    {', '.join(transition_choices)}

Per-element entrance animation (-a/--animation, native shapes mode):
    {', '.join(animation_choices)}
    Notes: applied to top-level <g id="..."> SVG groups in z-order. Default is
           "none" (no auto element builds; page transitions still apply). Use
           "-a auto" to map effects from group id: chart→wipe,
           card-/step-/pillar-→fly, title/takeaway→fade; image-like ids
           hero/figure-/image/img-/kpi cycle zoom/dissolve/circle/box/diamond/
           wheel so multiple images vary across the deck; unmatched ids cycle
           fade/wipe/fly/zoom. Start mode set by --animation-trigger, matching
           PowerPoint's Start dropdown:
             on-click              one presenter click per group
             with-previous         all groups start together on slide entry
             after-previous (default)  cascade on slide entry;
                                       gap = --animation-stagger seconds
           mixed (legacy) cycles a larger 16-effect pool by group order;
           random samples from the same legacy pool. Use "-a none" to disable
           element builds explicitly.

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
                        help='Native SVG source directory. Default: svg_output/. '
                             'Pass output/final/<name> only for diagnostics.')
    parser.add_argument('-f', '--format', type=str,
                        choices=list(CANVAS_FORMATS.keys()), default=None,
                        help='Specify canvas format')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')

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
                             'groups export through their SVG fallback children. When set, '
                             'the default-flow export is named <project>_<ts>_native_charts.pptx '
                             'to tell it apart from a plain shape export.')
    parser.add_argument(
        '--pptx-structure',
        choices=['baseline', 'template', 'preserve', 'flat'],
        default=None,
        help=(
            'PPTX structure strategy for native export. When omitted, read '
            'spec_lock.md pptx_structure.mode, falling back to baseline. baseline '
            'promotes safe repeated background/chrome and extracts conservative '
            'semantic page-role layout families plus exact family-wide '
            'structurally marked chrome (legacy filenames/ids remain fallbacks); '
            'template consumes explicit '
            'data-pptx-layout/layer/placeholder metadata to build reusable layouts; '
            'preserve is legacy compatibility for imported source packages; '
            'flat leaves generated structure slide-local for debugging/comparison.'
        ),
    )
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
        if not math.isfinite(number):
            raise argparse.ArgumentTypeError("must be finite")
        if number < 0:
            raise argparse.ArgumentTypeError("must be non-negative")
        return number

    def positive_float(value: str) -> float:
        number = non_negative_float(value)
        if number <= 0:
            raise argparse.ArgumentTypeError("must be greater than zero")
        return number

    parser.add_argument('-t', '--transition', type=str, choices=transition_choices, default=None,
                        help='Page transition effect (default: fade; "none" removes visual motion)')
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
    parser.add_argument('--animation-duration', type=positive_float, default=None,
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
                        help='Low-level audio embedding from this directory; allows partial matches. '
                             'Default-flow exports get the _narrated name suffix.')
    parser.add_argument('--use-narration-timings', action='store_true',
                        help='Set slide auto-advance timings from narration audio durations')
    parser.add_argument('--recorded-narration', type=str, default=None,
                        help='Prepare PowerPoint recorded timings and narrations from a complete audio '
                             'directory. Default-flow exports get the _narrated name suffix '
                             '(<project>_<ts>_narrated.pptx) to tell them apart from silent exports.')
    parser.add_argument('--narration-padding', type=non_negative_float, default=0.5,
                        help='Seconds to add after each narration before auto-advance (default: 0.5)')

    args = parser.parse_args(argv)

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        return 1
    structure_lock = None
    native_structure_contract = None
    pptx_structure = args.pptx_structure
    if pptx_structure is None:
        try:
            structure_lock = load_pptx_structure_lock(project_path)
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        pptx_structure = structure_lock.mode if structure_lock else 'baseline'
    elif pptx_structure == 'preserve':
        try:
            structure_lock = load_pptx_structure_lock(project_path)
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        if structure_lock is None or structure_lock.mode != 'preserve':
            print(
                "Error: --pptx-structure preserve requires a preserve-mode "
                "spec_lock.md with source_template/native_structure rows",
                file=sys.stderr,
            )
            return 1
    if pptx_structure == 'preserve':
        if structure_lock is None:
            print("Error: preserve mode requires spec_lock.md", file=sys.stderr)
            return 1
        try:
            native_structure_contract = load_native_structure_contract(structure_lock)
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    theme_font_spec = None
    master_text_style_spec = None
    theme_color_spec = None
    if pptx_structure in {'baseline', 'template'}:
        try:
            theme_font_spec = load_theme_font_spec(project_path)
            if pptx_structure == 'template':
                master_text_style_spec = load_master_text_style_spec(project_path)
            theme_color_spec = load_theme_color_spec(project_path)
        except (ThemeFontError, ThemeColorError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
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

    # Native DrawingML is the only PPTX product. ``-s`` remains an explicit
    # diagnostic source override; standard export always reads svg_output/.
    native_source = args.source or 'output'
    native_files, native_source_dir = find_svg_files(project_path, native_source)
    ref_files = native_files
    if not native_files:
        print("Error: No SVG files found")
        return 1

    if (
        pptx_structure in {'template', 'preserve'}
        and structure_lock is not None
    ):
        try:
            template_specs = (
                parse_preserve_slides(native_files)
                if pptx_structure == 'preserve'
                else parse_template_slides(native_files)
            )
        except TemplateStructureError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        lock_errors = template_lock_errors(template_specs, structure_lock)
        if lock_errors:
            print("Error: PPTX structure does not match spec_lock.md:", file=sys.stderr)
            for message in lock_errors:
                print(f"  {message}", file=sys.stderr)
            return 1
        if pptx_structure == 'preserve':
            if native_structure_contract is None:
                print("Error: preserve mode contract is unavailable", file=sys.stderr)
                return 1
            preserve_errors = native_structure_lock_errors(
                template_specs,
                structure_lock,
                native_structure_contract,
            )
            if preserve_errors:
                print(
                    "Error: PPTX structure does not match native_structure.json:",
                    file=sys.stderr,
                )
                for message in preserve_errors:
                    print(f"  {message}", file=sys.stderr)
                return 1

    if args.native_objects:
        fallbacks = _native_object_fallbacks(native_files)
        if fallbacks:
            print(
                "Warning: --native-objects found fallback-only PPTX objects; "
                "they will export through their SVG preview instead of editable objects.",
                file=sys.stderr,
            )
            for filename, marker_id, status in fallbacks[:20]:
                print(f"  {filename}: {marker_id} ({status})", file=sys.stderr)
            if len(fallbacks) > 20:
                print(f"  ... and {len(fallbacks) - 20} more", file=sys.stderr)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_dir: Path | None = None
    if args.output:
        native_path = Path(args.output)
    else:
        exports_dir = project_path / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        # --native-objects yields a materially different file (real editable
        # PowerPoint chart/table objects instead of flattened shapes), so mark
        # it in the default-flow name to tell it apart from a plain shape export.
        # Narration flags likewise mark _narrated (audio embedded per slide +
        # auto-advance timings). Flag-driven (not content-sniffed) so the name
        # is predictable; an explicit -o keeps the caller's exact name untouched.
        native_tag = "_native_charts" if args.native_objects else ""
        narrated_tag = "_narrated" if (args.recorded_narration or args.narration_audio_dir) else ""
        native_path = exports_dir / f"{project_name}_{timestamp}{native_tag}{narrated_tag}.pptx"
        # Preserve the authored svg_output/ beside every default-flow export.
        backup_dir = project_path / "backup" / timestamp

    native_path.parent.mkdir(parents=True, exist_ok=True)

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
    config_errors: list[str] = []
    if animation_config:
        config_errors.extend(validate_transition_config(animation_config))
        config_errors.extend(validate_animation_config_errors(animation_config))
    config_errors = list(dict.fromkeys(config_errors))
    if config_errors:
        for error in config_errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    config_warnings: list[str] = []
    if animation_config:
        reference_messages = validate_animation_config(project_path, animation_config)
        config_warnings = [
            message for message in reference_messages
            if ' has no id and cannot be customized in animations.json' in message
        ]
        reference_errors = [
            message for message in reference_messages
            if message not in config_warnings
        ]
        if reference_errors:
            for error in reference_errors:
                print(f"Error: {error}", file=sys.stderr)
            return 1

    if animation_config and verbose:
        config_label = args.animation_config or str(project_path / 'animations.json')
        print(f"  Animation config: {config_label}")
        for warning in config_warnings:
            print(f"  [warn] {warning}")

    defaults = animation_config.get('defaults', {}) if animation_config else {}
    transition_defaults = _as_dict(defaults.get('transition')) if isinstance(defaults, dict) else {}
    animation_defaults = _as_dict(defaults.get('animation')) if isinstance(defaults, dict) else {}

    transition_arg = args.transition
    transition_effect = (
        transition_arg
        if transition_arg is not None
        else transition_defaults.get('effect', 'fade')
    )
    transition = None if transition_effect == 'none' else transition_effect
    try:
        transition_duration = validate_seconds(
            (
                args.transition_duration
                if args.transition_duration is not None
                else transition_defaults.get('duration', 0.4)
            ),
            "transition duration",
            allow_zero=transition is None,
        )
        auto_advance = (
            args.auto_advance
            if args.auto_advance is not None
            else transition_defaults.get('auto_advance')
        )
        if auto_advance is not None:
            auto_advance = validate_seconds(
                auto_advance,
                "transition auto_advance",
                allow_zero=True,
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        animation_effect = (
            args.animation
            if args.animation is not None
            # Per-element entrance is opt-in by default: auto-firing element builds
            # read as the "AI deck" tell and were unsolicited. Page transitions stay
            # on (see transition default above). Re-enable with -a auto / animations.json.
            else animation_defaults.get('effect', 'none')
        )
        animation = normalize_animation_effect(animation_effect)
        animation_duration = validate_seconds(
            (
                args.animation_duration
                if args.animation_duration is not None
                else animation_defaults.get('duration', 0.4)
            ),
            "animation duration",
            allow_zero=False,
        )
        animation_seconds_to_milliseconds(
            animation_duration,
            "animation duration",
            allow_zero=False,
        )
        animation_stagger = validate_seconds(
            (
                args.animation_stagger
                if args.animation_stagger is not None
                else animation_defaults.get('stagger', 0.5)
            ),
            "animation stagger",
            allow_zero=True,
        )
        animation_seconds_to_milliseconds(
            animation_stagger,
            "animation stagger",
            allow_zero=True,
        )
        animation_trigger = normalize_animation_trigger(
            args.animation_trigger
            if args.animation_trigger is not None
            else animation_defaults.get('trigger', 'after-previous')
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    animation_cli_overrides = {
        'transition': args.transition is not None,
        'transition_duration': args.transition_duration is not None,
        'auto_advance': args.auto_advance is not None,
        'animation': args.animation is not None,
        'animation_duration': args.animation_duration is not None,
        'animation_stagger': args.animation_stagger is not None,
        'animation_trigger': args.animation_trigger is not None,
    }

    if args.recorded_narration:
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
        auto_advance=auto_advance,
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
        merge_paragraphs=args.merge_paragraphs,
        image_optimize=not args.no_image_optimize,
        image_max_dimension=args.image_max_dimension,
        image_sizing=args.image_sizing,
        image_scale=args.image_scale,
        image_quality=args.image_quality,
        native_objects=args.native_objects,
        pptx_structure=pptx_structure,
        native_structure_contract=native_structure_contract,
        theme_font_spec=theme_font_spec,
        master_text_style_spec=master_text_style_spec,
        theme_color_spec=theme_color_spec,
    )

    if verbose:
        print("PPT Master - SVG to native DrawingML PPTX Tool")
        print("=" * 50)
        print(f"  Project path: {project_path}")
        print(f"  SVG directory: {native_source_dir}")
        print(f"  Output file: {native_path}")
        print()

    try:
        success = create_pptx_with_native_svg(
            output_path=native_path,
            use_native_shapes=True,
            svg_files=native_files,
            conversion_trace_path=(
                native_path.with_name(native_path.name + '.trace.json')
                if args.conversion_trace else None
            ),
            **shared_kwargs,
        )
    except (TemplateStructureError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Archive svg_output/ once per default-flow export. This preserves the
    # authored SVG sources under backup/<ts>/svg_output/ for inspection and
    # deterministic re-export.
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
        if pptx_structure == 'preserve' and structure_lock is not None:
            try:
                preserve_sources = [
                    project_path / 'spec_lock.md',
                    structure_lock.source_template,
                    structure_lock.native_structure,
                ]
                for source in preserve_sources:
                    if source is None or not source.is_file():
                        continue
                    source_path = source.resolve()
                    relative = source_path.relative_to(project_path.resolve())
                    destination = backup_dir / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, destination)
                if verbose:
                    print(f"  preserve contract backup: {backup_dir}")
            except (OSError, ValueError) as exc:
                if verbose:
                    print(f"  [warn] preserve contract backup skipped: {exc}")

    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
