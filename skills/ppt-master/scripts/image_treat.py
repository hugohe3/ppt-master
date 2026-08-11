#!/usr/bin/env python3
"""
PPT Master - Image Treatment

Create a non-destructive PNG derivative from one project-local bitmap while
preserving its display dimensions, alpha mask, and any matching web provenance.

Usage:
    python3 scripts/image_treat.py <project_path> <source> --output <filename.png> [options]

Examples:
    python3 scripts/image_treat.py projects/demo hero.jpg --output hero_soft.png --blur 12
    python3 scripts/image_treat.py projects/demo hero.jpg --output hero_duotone.png \
        --contrast 1.1 --duotone "#14213D" "#FCA311"

Dependencies:
    Pillow; project image-search dependencies when copying web provenance

Treatments run in this fixed order: brightness, contrast, tone treatment
(desaturate / grayscale / duotone), then Gaussian blur.
"""

from __future__ import annotations

import argparse
import copy
import math
import os
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import (
    Image,
    ImageCms,
    ImageEnhance,
    ImageFilter,
    ImageOps,
    UnidentifiedImageError,
)


_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()


_HEX_COLOR_RE = re.compile(r"^#?([0-9A-Fa-f]{6})$")


def _read_sources_manifest(path: Path) -> dict:
    from image_search import _read_existing_manifest

    return _read_existing_manifest(path)


def _write_sources_manifest(path: Path, item: dict) -> Path:
    from image_search import write_sources_manifest

    return write_sources_manifest(path, item)


def _finite_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a number, got {value!r}") from exc
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError("value must be finite")
    return number


def _nonnegative_float(value: str) -> float:
    number = _finite_float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be greater than or equal to 0")
    return number


def _positive_float(value: str) -> float:
    number = _finite_float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return number


def _unit_float(value: str) -> float:
    number = _finite_float(value)
    if not 0 <= number <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return number


def _hex_color(value: str) -> str:
    match = _HEX_COLOR_RE.fullmatch(value)
    if match is None:
        raise argparse.ArgumentTypeError("color must be #RRGGBB or RRGGBB")
    return f"#{match.group(1).upper()}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a project-local PNG derivative. Processing order: brightness -> "
            "contrast -> desaturate/grayscale/duotone -> blur."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", help="Project root containing an images/ directory.")
    parser.add_argument(
        "source",
        help="Existing bare bitmap filename under <project_path>/images (no path components).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="New bare .png filename under <project_path>/images; existing files are never replaced.",
    )
    parser.add_argument(
        "--brightness",
        type=_positive_float,
        help="Brightness factor greater than 0; 1 is unchanged.",
    )
    parser.add_argument(
        "--contrast",
        type=_positive_float,
        help="Contrast factor greater than 0; 1 is unchanged.",
    )
    tone_group = parser.add_mutually_exclusive_group()
    tone_group.add_argument(
        "--desaturate",
        type=_unit_float,
        help="Remove this fraction of color (0..1); 1 is grayscale.",
    )
    tone_group.add_argument(
        "--grayscale",
        action="store_true",
        help="Convert RGB content to grayscale while preserving any alpha mask.",
    )
    tone_group.add_argument(
        "--duotone",
        nargs=2,
        type=_hex_color,
        metavar=("SHADOW", "HIGHLIGHT"),
        help="Map sRGB luminance between two sRGB #RRGGBB colors.",
    )
    parser.add_argument(
        "--blur",
        type=_nonnegative_float,
        help="Gaussian blur radius greater than or equal to 0; 0 is unchanged.",
    )
    return parser


def _validate_bare_filename(value: str, *, field_name: str) -> str:
    if (
        not value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ":" in value
        or Path(value).is_absolute()
    ):
        raise ValueError(
            f"{field_name} must be a bare filename without path components: {value!r}"
        )
    return value


def _assert_output_absent(output_path: Path) -> None:
    for child in output_path.parent.iterdir():
        if child.name.casefold() == output_path.name.casefold():
            raise ValueError(f"output already exists or conflicts by casing: {child}")


def _resolve_paths(project_value: str, source_name: str, output_name: str) -> tuple[Path, Path, Path]:
    source_name = _validate_bare_filename(source_name, field_name="source")
    output_name = _validate_bare_filename(output_name, field_name="output")
    if Path(output_name).suffix.casefold() != ".png":
        raise ValueError("output must use the .png extension")
    if source_name.casefold() == output_name.casefold():
        raise ValueError("output must differ from source, including filename casing")

    project_input = Path(project_value).expanduser()
    try:
        project_path = project_input.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"project path does not resolve safely: {project_input} ({exc})") from exc
    if not project_path.is_dir():
        raise ValueError(f"project path is not a directory: {project_path}")

    images_link = project_path / "images"
    if images_link.is_symlink():
        raise ValueError(f"project images directory must not be a symlink: {images_link}")
    if not images_link.is_dir():
        raise ValueError(f"project images directory does not exist: {images_link}")
    images_path = images_link.resolve(strict=True)
    if images_path.parent != project_path:
        raise ValueError(f"project images directory escapes the project root: {images_link}")

    source_link = images_path / source_name
    if source_link.is_symlink():
        raise ValueError(f"source must not be a symlink: {source_link}")
    try:
        source_path = source_link.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"source does not resolve safely: {source_link} ({exc})") from exc
    if source_path.parent != images_path or not source_path.is_file():
        raise ValueError(f"source must be a file directly under project images/: {source_link}")

    output_path = images_path / output_name
    _assert_output_absent(output_path)
    if output_path.exists() or output_path.is_symlink():
        raise ValueError(f"output already exists: {output_path}")
    if output_path.parent.resolve() != images_path:
        raise ValueError(f"output escapes the project images directory: {output_path}")

    return images_path, source_path, output_path


def _treatment_plan(args: argparse.Namespace) -> list[dict]:
    plan: list[dict] = []
    if args.brightness is not None and args.brightness != 1:
        plan.append({"operation": "brightness", "factor": args.brightness})
    if args.contrast is not None and args.contrast != 1:
        plan.append({"operation": "contrast", "factor": args.contrast})
    if args.desaturate is not None and args.desaturate > 0:
        plan.append({"operation": "desaturate", "amount": args.desaturate})
    elif args.grayscale:
        plan.append({"operation": "grayscale"})
    elif args.duotone is not None:
        plan.append(
            {
                "operation": "duotone",
                "shadow": args.duotone[0],
                "highlight": args.duotone[1],
            }
        )
    if args.blur is not None and args.blur > 0:
        plan.append({"operation": "blur", "radius": args.blur})
    if not plan:
        raise ValueError(
            "select at least one effective treatment; identity values such as "
            "--brightness 1, --desaturate 0, or --blur 0 do not change the image"
        )
    return plan


def _validate_blur_radius(radius: Optional[float], width: int, height: int) -> None:
    if radius is None or radius <= 0:
        return
    effective_maximum = max(width, height)
    if radius > effective_maximum:
        raise ValueError(
            f"blur radius {radius:g} exceeds the effective maximum "
            f"{effective_maximum} for a {width}x{height} image; choose --blur "
            f"at or below {effective_maximum}"
        )


def _convert_duotone_source_to_srgb(image: Image.Image) -> tuple[Image.Image, bytes]:
    output_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    output_icc = output_profile.tobytes()
    source_icc = image.info.get("icc_profile")
    if not source_icc:
        return image.convert("RGB"), output_icc
    if not isinstance(source_icc, bytes):
        raise ValueError(
            "source ICC profile has an unsupported representation; convert the "
            "source to sRGB or remove the invalid profile, then retry"
        )
    try:
        input_profile = ImageCms.ImageCmsProfile(BytesIO(source_icc))
        converted = ImageCms.profileToProfile(
            image,
            input_profile,
            output_profile,
            outputMode="RGB",
        )
    except (ImageCms.PyCMSError, OSError, TypeError, ValueError) as exc:
        raise ValueError(
            "source ICC profile is invalid or incompatible with the image mode; "
            "convert the source to sRGB or remove the invalid profile, then retry"
        ) from exc
    if converted is None:
        raise RuntimeError("ICC conversion did not produce an image")
    return converted, output_icc


def _has_alpha(image: Image.Image) -> bool:
    return "A" in image.getbands() or "transparency" in image.info


def _apply_treatments(
    source_path: Path,
    temporary_path: Path,
    args: argparse.Namespace,
) -> tuple[int, int]:
    try:
        with Image.open(source_path) as source:
            if int(getattr(source, "n_frames", 1)) != 1:
                raise RuntimeError(
                    f"animated or multi-frame images are unsupported: {source_path}"
                )
            oriented = ImageOps.exif_transpose(source)
            try:
                oriented.load()
                width, height = oriented.size
                _validate_blur_radius(args.blur, width, height)
                has_alpha = _has_alpha(oriented)
                rgba = oriented.convert("RGBA") if has_alpha else None
                alpha = rgba.getchannel("A") if rgba is not None else None
                if args.duotone is not None:
                    rgb, icc_profile = _convert_duotone_source_to_srgb(oriented)
                else:
                    keep_icc = oriented.mode in {"RGB", "RGBA"}
                    icc_profile = oriented.info.get("icc_profile") if keep_icc else None
                    rgb = rgba.convert("RGB") if rgba is not None else oriented.convert("RGB")

                if args.brightness is not None and args.brightness != 1:
                    rgb = ImageEnhance.Brightness(rgb).enhance(args.brightness)
                if args.contrast is not None and args.contrast != 1:
                    rgb = ImageEnhance.Contrast(rgb).enhance(args.contrast)
                if args.desaturate is not None and args.desaturate > 0:
                    rgb = ImageEnhance.Color(rgb).enhance(1 - args.desaturate)
                elif args.grayscale:
                    rgb = ImageOps.grayscale(rgb).convert("RGB")
                elif args.duotone is not None:
                    rgb = ImageOps.colorize(
                        ImageOps.grayscale(rgb),
                        black=args.duotone[0],
                        white=args.duotone[1],
                    )
                if args.blur is not None and args.blur > 0:
                    rgb = rgb.filter(ImageFilter.GaussianBlur(radius=args.blur))

                result = rgb.convert("RGBA") if alpha is not None else rgb
                if alpha is not None:
                    result.putalpha(alpha)
                save_options = {"format": "PNG"}
                if isinstance(icc_profile, bytes) and icc_profile:
                    save_options["icc_profile"] = icc_profile
                result.save(temporary_path, **save_options)
                result.close()
                if rgba is not None:
                    rgba.close()
                if alpha is not None:
                    alpha.close()
                rgb.close()
                return width, height
            finally:
                if oriented is not source:
                    oriented.close()
    except (OSError, UnidentifiedImageError) as exc:
        raise RuntimeError(f"unable to read or treat source image {source_path}: {exc}") from exc


def _rewrite_attribution_text(item: dict, source_name: str, output_name: str) -> str:
    value = item.get("attribution_text")
    if not isinstance(value, str) or not value:
        return value if isinstance(value, str) else ""
    if not value.startswith(source_name):
        return value
    remainder = value[len(source_name) :]
    if remainder and not (remainder[0].isspace() or remainder[0] in "—–-:"):
        return value
    return output_name + remainder


def _prepare_provenance(
    manifest_path: Path,
    source_name: str,
    output_name: str,
    treatments: list[dict],
) -> Optional[dict]:
    if manifest_path.is_symlink():
        raise ValueError(f"image source manifest must not be a symlink: {manifest_path}")
    if not manifest_path.exists():
        return None

    payload = _read_sources_manifest(manifest_path)
    items = payload.get("items") or []
    source_item = None
    for item in items:
        filename = item.get("filename")
        if not isinstance(filename, str):
            continue
        if filename.casefold() == output_name.casefold():
            raise ValueError(
                f"output already has an image_sources.json record: {filename!r}"
            )
        if filename.casefold() == source_name.casefold():
            if filename != source_name:
                raise ValueError(
                    "source filename casing does not match image_sources.json: "
                    f"{source_name!r} vs {filename!r}"
                )
            source_item = item

    if source_item is None:
        return None
    derived_item = copy.deepcopy(source_item)
    derived_item["filename"] = output_name
    derived_item["attribution_text"] = _rewrite_attribution_text(
        source_item,
        source_name,
        output_name,
    )
    derived_item["derived_from"] = source_name
    derived_item["treatments"] = copy.deepcopy(treatments)
    return derived_item


def _assert_manifest_output_absent(manifest_path: Path, output_name: str) -> None:
    payload = _read_sources_manifest(manifest_path)
    for item in payload.get("items") or []:
        filename = item.get("filename")
        if isinstance(filename, str) and filename.casefold() == output_name.casefold():
            raise RuntimeError(
                f"output already has an image_sources.json record: {filename!r}"
            )


def _is_staged_output(temporary_path: Path, output_path: Path) -> bool:
    try:
        return not output_path.is_symlink() and os.path.samefile(temporary_path, output_path)
    except OSError:
        return False


def _write_derivative(
    source_path: Path,
    output_path: Path,
    manifest_path: Path,
    provenance_item: Optional[dict],
    args: argparse.Namespace,
) -> None:
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}.",
        suffix=".tmp.png",
        dir=str(output_path.parent),
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        width, height = _apply_treatments(source_path, temporary_path, args)
        if provenance_item is not None:
            provenance_item["width"] = width
            provenance_item["height"] = height
            _assert_manifest_output_absent(manifest_path, output_path.name)
        _assert_output_absent(output_path)
        try:
            os.chmod(temporary_path, 0o644)
        except OSError:
            pass
        try:
            os.link(temporary_path, output_path)
        except FileExistsError as exc:
            raise RuntimeError(
                f"output appeared during processing and will not be replaced: {output_path}"
            ) from exc
        if provenance_item is not None:
            try:
                if not _is_staged_output(temporary_path, output_path):
                    raise RuntimeError(
                        f"installed output changed before provenance commit: {output_path}"
                    )
                _assert_manifest_output_absent(manifest_path, output_path.name)
                _write_sources_manifest(manifest_path, provenance_item)
            except Exception as exc:
                try:
                    if _is_staged_output(temporary_path, output_path):
                        output_path.unlink()
                except OSError as cleanup_exc:
                    raise RuntimeError(
                        f"manifest update failed and output rollback also failed: {cleanup_exc}"
                    ) from exc
                raise RuntimeError(f"manifest update failed; output was rolled back: {exc}") from exc
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        images_path, source_path, output_path = _resolve_paths(
            args.project_path,
            args.source,
            args.output,
        )
        treatments = _treatment_plan(args)
        manifest_path = images_path / "image_sources.json"
        provenance_item = _prepare_provenance(
            manifest_path,
            args.source,
            args.output,
            treatments,
        )
        _write_derivative(
            source_path,
            output_path,
            manifest_path,
            provenance_item,
            args,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
