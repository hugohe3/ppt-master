#!/usr/bin/env python3
"""PPT Master — single-pass image alignment + Base64 embedding.

Replaces the previous three independent finalize_svg steps:

    crop-images   →  for each <image preserveAspectRatio="… slice"/>, crop the
                     source bitmap to the target aspect ratio at the given
                     anchor and write to ``images/cropped/`` so the SVG
                     reference points to a pre-cropped asset.
    fix-aspect    →  for each <image>, read the source bitmap dimensions and
                     adjust x/y/width/height so the rendered box matches the
                     image aspect ratio in PowerPoint SVG rendering paths that
                     do not honor preserveAspectRatio consistently.
    embed-images  →  Base64-inline every embeddable external image reference
                     so ``svg_final/`` remains portable when opened or manually
                     inserted as an SVG image. EMF/WMF keep the documented
                     external-reference exception.

Why merge: each step independently parsed + serialized the SVG, each step
re-read the same bitmap from disk, and the two spatial transforms (crop and
fit-box) are mutually exclusive yet were sequenced one after the other.
The fix-aspect default ``preserveAspectRatio = "xMidYMid meet"`` could
also kick in on rects already cropped by crop-images (whose par was
already removed), with the only thing keeping it from corrupting the
geometry being that crop and fix-aspect happened to produce numerically
equal box dimensions — a brittle accident.

The merged pipeline:

    for image in svg:
        if href starts with data: → skip (already inline)
        if href is unresolvable / external URL → skip
        if href points to EMF/WMF → skip (native PPTX passthrough only)
        if missing preserveAspectRatio → just embed (do not assume meet)
        if align == none → just embed (no spatial transform)
        if mode == slice → crop in memory, embed cropped bytes
        if mode == meet → adjust x/y/w/h, embed original bytes
    write SVG once

Bonus: the cropped bitmap is base64-inlined directly without going through
``images/cropped/``, so that intermediate directory disappears and stale
crops can no longer accumulate across re-runs.
"""

from __future__ import annotations

import base64
import io
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote
from xml.etree import ElementTree as ET

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

if __package__ in {None, ''}:
    import types

    package = types.ModuleType('svg_finalize')
    package.__path__ = [str(Path(__file__).resolve().parent)]  # type: ignore[attr-defined]
    sys.modules.setdefault('svg_finalize', package)
    __package__ = 'svg_finalize'

# Reuse helpers from the previous standalone modules.
from .crop_images import crop_image_to_size, get_crop_anchor, parse_preserve_aspect_ratio
from .embed_images import _optimize_image_bytes, get_mime_type
from .fix_image_aspect import calculate_fitted_dimensions

if TYPE_CHECKING:  # pragma: no cover
    from PIL import Image as PILImage  # noqa: F401


SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

# PIL save format is named slightly differently from the file extension /
# MIME type set we expose elsewhere; this map covers the formats we accept.
_PIL_FORMAT_BY_MIME = {
    'image/png': 'PNG',
    'image/jpeg': 'JPEG',
    'image/gif': 'GIF',
    'image/webp': 'WEBP',
}
_OFFICE_VECTOR_EXTENSIONS = {'.emf', '.wmf'}


def _parse_float(val: str | None, default: float = 0.0) -> float:
    """Best-effort float parse, tolerating trailing ``px`` etc."""
    if val is None or val == '':
        return default
    try:
        return float(re.sub(r'(px|pt|em|%|rem)$', '', val.strip()))
    except (ValueError, AttributeError):
        return default


def _format_number(n: float) -> str:
    """Format a float for compact SVG attribute output."""
    if abs(n - round(n)) < 1e-6:
        return str(int(round(n)))
    s = f"{n:.2f}".rstrip('0').rstrip('.')
    return s or '0'


def _resolve_image_path(href: str, svg_dir: Path) -> Path | None:
    """Resolve an <image> href to a local filesystem path.

    Returns None for unresolvable references (http/https/etc.) so callers
    can leave those refs untouched.
    """
    if not href:
        return None
    decoded = unquote(href)
    if decoded.startswith(('http://', 'https://', 'file://')):
        return None
    if os.path.isabs(decoded):
        candidate = Path(decoded)
    else:
        candidate = (svg_dir / decoded).resolve()
    return candidate if candidate.exists() else None


def _is_svg_image(img_path: Path, raw_bytes: bytes) -> bool:
    """Return True when an image reference is an SVG document."""
    if img_path.suffix.lower() == '.svg':
        return True
    head = raw_bytes.lstrip()[:512].lower()
    return head.startswith(b'<svg') or (head.startswith(b'<?xml') and b'<svg' in head)


def _embed_raw_image(image: ET.Element, img_path: Path, raw_bytes: bytes) -> None:
    """Embed raw image bytes without PIL transforms."""
    mime_type = get_mime_type(img_path.name, raw_bytes)
    b64 = base64.b64encode(raw_bytes).decode('ascii')
    _set_href(image, f'data:{mime_type};base64,{b64}')


def _load_pil_image(img_path: Path) -> 'PILImage' | None:
    """Open an image with PIL, returning None on any failure."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        return Image.open(img_path)
    except (OSError, ValueError):
        return None


def _normalize_for_save(img: 'PILImage', mime_type: str) -> 'PILImage':
    """Coerce a PIL image into a mode that the target format can save.

    JPEG cannot store alpha — flatten to white background. Other formats
    keep alpha when present.
    """
    if mime_type == 'image/jpeg':
        if img.mode in ('RGBA', 'LA'):
            from PIL import Image
            background = Image.new('RGB', img.size, (255, 255, 255))
            alpha = img.getchannel('A') if img.mode == 'RGBA' else None
            background.paste(img.convert('RGB'), mask=alpha)
            return background
        if img.mode != 'RGB':
            return img.convert('RGB')
        return img
    # PNG / GIF / WEBP — preserve alpha if present
    if img.mode == 'P':
        return img.convert('RGBA' if 'A' in img.getbands() else 'RGB')
    return img


def _has_alpha(img: 'PILImage') -> bool:
    """Return whether a PIL image has transparency."""
    if img.mode in ('RGBA', 'LA'):
        return True
    if img.mode == 'P':
        return 'transparency' in getattr(img, 'info', {})
    return False


def _target_size(
    box_w: float,
    box_h: float,
    *,
    max_dimension: int | None,
    image_scale: float,
) -> tuple[int, int]:
    """Resolve the pixel budget for a rendered SVG image box."""
    target_w = max(1, int(round(box_w * max(image_scale, 1.0))))
    target_h = max(1, int(round(box_h * max(image_scale, 1.0))))
    if max_dimension and max(target_w, target_h) > max_dimension:
        ratio = max_dimension / max(target_w, target_h)
        target_w = max(1, int(round(target_w * ratio)))
        target_h = max(1, int(round(target_h * ratio)))
    return target_w, target_h


def _downscale_to_target(img: 'PILImage', target_w: int, target_h: int) -> tuple['PILImage', bool]:
    """Downscale without upsampling."""
    width, height = img.size
    ratio = min(target_w / width, target_h / height, 1.0)
    if ratio >= 1.0:
        return img, False
    from PIL import Image
    new_size = (max(1, int(round(width * ratio))), max(1, int(round(height * ratio))))
    return img.resize(new_size, Image.Resampling.LANCZOS), True


def _encode_pil_to_data_uri(
    img: 'PILImage',
    src_path: Path,
    *,
    compress: bool,
    max_dimension: int | None,
    fallback_bytes: bytes | None,
) -> tuple[str, int] | None:
    """Serialize *img* to a base64 data URI.

    If the image hasn't been transformed (slice crop or meet fit), prefer
    re-encoding the original file bytes so we don't risk mutating an
    already-optimized asset. *fallback_bytes* carries the raw on-disk
    bytes for that path.
    """
    original_mime_type = get_mime_type(src_path.name, fallback_bytes)
    mime_type = original_mime_type
    if compress and mime_type == 'image/png' and not _has_alpha(img):
        mime_type = 'image/jpeg'
    pil_format = _PIL_FORMAT_BY_MIME.get(mime_type, 'PNG')

    # Encode current PIL image
    try:
        prepared = _normalize_for_save(img, mime_type)
        buf = io.BytesIO()
        save_kwargs: dict = {'format': pil_format}
        if pil_format == 'JPEG':
            save_kwargs['quality'] = 95
            save_kwargs['optimize'] = True
        elif pil_format == 'PNG':
            save_kwargs['optimize'] = True
        prepared.save(buf, **save_kwargs)
        encoded_bytes = buf.getvalue()
    except (OSError, ValueError):
        return None

    # If caller passed the original bytes and they're smaller (because PIL
    # round-tripping an asset that was already well-compressed inflates it),
    # fall back to those.
    chosen = encoded_bytes
    if fallback_bytes and mime_type == original_mime_type and len(fallback_bytes) < len(encoded_bytes):
        chosen = fallback_bytes

    chosen = _optimize_image_bytes(
        chosen, mime_type, compress=compress, max_dimension=max_dimension,
    )

    b64 = base64.b64encode(chosen).decode('ascii')
    return f'data:{mime_type};base64,{b64}', len(chosen)


def _iter_image_elements(root: ET.Element):
    """Yield every <image> in the tree regardless of namespace prefix."""
    for image in root.iter(f'{{{SVG_NS}}}image'):
        yield image
    # Also catch namespace-stripped trees just in case
    for image in root.iter('image'):
        yield image


def _get_href(image: ET.Element) -> str | None:
    """Return the image href, supporting both ``href`` and ``xlink:href``."""
    return image.get('href') or image.get(f'{{{XLINK_NS}}}href')


def _set_href(image: ET.Element, value: str) -> None:
    """Write the data URI back to whichever href attribute the image used."""
    if image.get(f'{{{XLINK_NS}}}href') is not None:
        image.set(f'{{{XLINK_NS}}}href', value)
    else:
        image.set('href', value)


def _process_one_image(
    image: ET.Element,
    svg_dir: Path,
    *,
    compress: bool,
    max_dimension: int | None,
    image_scale: float,
    verbose: bool,
) -> tuple[bool, str | None]:
    """Align (slice/meet) and embed a single <image>.

    Returns ``(processed, error)`` where *processed* is True iff the image
    was rewritten and *error* is a short message when something went wrong
    (the image is left untouched in that case).
    """
    href = _get_href(image)
    if not href:
        return False, None
    if href.startswith('data:'):
        return False, None  # already inline

    img_path = _resolve_image_path(href, svg_dir)
    if img_path is None:
        return False, f'unresolved href: {href[:60]}'

    try:
        with open(img_path, 'rb') as fh:
            raw_bytes = fh.read()
    except OSError as exc:
        return False, f'read failed: {exc}'

    if img_path.suffix.lower() in _OFFICE_VECTOR_EXTENSIONS:
        if verbose:
            print(f'   [INFO] {img_path.name}: Office vector left external for native PPTX passthrough')
        return False, None

    if _is_svg_image(img_path, raw_bytes):
        _embed_raw_image(image, img_path, raw_bytes)
        if verbose:
            print(f'   [OK] {img_path.name} (svg, embedded as-is)')
        return True, None

    img = _load_pil_image(img_path)
    if img is None:
        return False, 'PIL open failed'

    # Multi-frame images (animated GIF / WebP / APNG): every PIL transform
    # and re-save below operates on frame 0 only, silently flattening the
    # animation — and the "original bytes are smaller" fallback never fires
    # because one frame is always smaller than all frames. Embed the raw
    # bytes untouched and keep the geometry attributes (including
    # preserveAspectRatio, which the native converter maps to srcRect
    # non-destructively). Animated assets skip re-encode, resize, and the
    # size cap.
    if getattr(img, 'is_animated', False):
        _embed_raw_image(image, img_path, raw_bytes)
        if max_dimension and max(img.size) > max_dimension:
            print(f'   [WARN] {img_path.name}: animated image kept as-is '
                  f'({img.size[0]}x{img.size[1]} exceeds max dimension '
                  f'{max_dimension}px); animations are exempt from size limits')
        if verbose:
            print(f'   [OK] {img_path.name} (animated, embedded as-is)')
        return True, None

    box_x = _parse_float(image.get('x'))
    box_y = _parse_float(image.get('y'))
    box_w = _parse_float(image.get('width'))
    box_h = _parse_float(image.get('height'))
    if box_w <= 0 or box_h <= 0:
        return False, 'zero-sized box'

    par_attr = image.get('preserveAspectRatio') or ''
    par_attr = par_attr.strip()

    # ------------------------------------------------------------------
    # Decide the spatial transform
    # ------------------------------------------------------------------
    final_img: 'PILImage' = img
    new_x, new_y, new_w, new_h = box_x, box_y, box_w, box_h
    transformed = False  # True iff bitmap content changed (crop happened)
    target_box_w, target_box_h = box_w, box_h

    if not par_attr:
        # No preserveAspectRatio at all. The previous pipeline's fix-aspect
        # step assumed "xMidYMid meet" here, which silently re-fit images
        # that crop-images had already shaped. Treat absence as "leave it
        # alone": embed bytes, keep box.
        pass
    else:
        align, mode = parse_preserve_aspect_ratio(par_attr)
        if align == 'none':
            # Author wants stretch-to-box; preserve geometry, embed bytes.
            pass
        elif mode == 'slice':
            x_anchor, y_anchor = get_crop_anchor(align)
            cropped = crop_image_to_size(img, int(box_w), int(box_h),
                                         x_anchor, y_anchor)
            final_img = cropped
            transformed = True
        else:  # meet (or any other mode → treat as meet)
            new_w_calc, new_h_calc, off_x, off_y = calculate_fitted_dimensions(
                img.size[0], img.size[1], box_w, box_h, mode='meet',
            )
            new_x = box_x + off_x
            new_y = box_y + off_y
            new_w = new_w_calc
            new_h = new_h_calc
            target_box_w, target_box_h = new_w, new_h

    target_w, target_h = _target_size(
        target_box_w,
        target_box_h,
        max_dimension=max_dimension,
        image_scale=image_scale,
    )
    final_img, resized = _downscale_to_target(final_img, target_w, target_h)
    transformed = transformed or resized

    # ------------------------------------------------------------------
    # Encode and rewrite
    # ------------------------------------------------------------------
    encoded = _encode_pil_to_data_uri(
        final_img,
        img_path,
        compress=compress,
        max_dimension=max_dimension,
        fallback_bytes=raw_bytes if not transformed else None,
    )
    if encoded is None:
        return False, 'encode failed'
    data_uri, _ = encoded

    _set_href(image, data_uri)
    image.set('x', _format_number(new_x))
    image.set('y', _format_number(new_y))
    image.set('width', _format_number(new_w))
    image.set('height', _format_number(new_h))
    if 'preserveAspectRatio' in image.attrib:
        del image.attrib['preserveAspectRatio']

    if verbose:
        suffix = ' (cropped)' if transformed else ''
        print(f'   [OK] {img_path.name}{suffix}')
    return True, None


def count_office_vector_refs_in_svg(svg_path: str | Path) -> int:
    """Count local EMF/WMF image refs that the embed pass intentionally skips."""
    svg_path = Path(svg_path)
    svg_dir = svg_path.parent.resolve()
    try:
        tree = ET.parse(svg_path)
    except ET.ParseError:
        return 0
    count = 0
    seen: set[int] = set()
    for image in _iter_image_elements(tree.getroot()):
        ident = id(image)
        if ident in seen:
            continue
        seen.add(ident)
        href = _get_href(image)
        if not href or href.startswith('data:'):
            continue
        img_path = _resolve_image_path(href, svg_dir)
        if img_path and img_path.suffix.lower() in _OFFICE_VECTOR_EXTENSIONS:
            count += 1
    return count


def align_and_embed_images_in_svg(
    svg_path: str | Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
    compress: bool = True,
    max_dimension: int | None = 2560,
    image_scale: float = 2.0,
) -> tuple[int, int]:
    """Run the merged align + embed pass on a single SVG file.

    Returns ``(processed_count, error_count)``.
    """
    svg_path = Path(svg_path)
    svg_dir = svg_path.parent.resolve()

    # Register namespaces for clean serialization
    ET.register_namespace('', SVG_NS)
    ET.register_namespace('xlink', XLINK_NS)

    try:
        tree = ET.parse(svg_path)
    except ET.ParseError as exc:
        if verbose:
            print(f'  [ERROR] {svg_path.name}: parse failed ({exc})')
        return (0, 1)
    root = tree.getroot()

    # Avoid double-iteration if an element matches both namespaced and
    # bare-tag iteration paths.
    seen: set[int] = set()
    processed = 0
    errors = 0

    for image in _iter_image_elements(root):
        ident = id(image)
        if ident in seen:
            continue
        seen.add(ident)

        if dry_run:
            processed += 1
            continue

        ok, err = _process_one_image(
            image, svg_dir,
            compress=compress, max_dimension=max_dimension,
            image_scale=image_scale, verbose=verbose,
        )
        if ok:
            processed += 1
        elif err:
            errors += 1
            if verbose:
                print(f'   [WARN] {svg_path.name}: {err}')

    if processed > 0 and not dry_run:
        tree.write(svg_path, encoding='utf-8', xml_declaration=False)

    return (processed, errors)


# ---------------------------------------------------------------------------
# Standalone CLI (rare; the main entry point is finalize_svg.py)
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the standalone diagnostic parser."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Align (slice/meet) and Base64-embed all <image> refs in an SVG.',
    )
    parser.add_argument('svg', type=Path, help='SVG file to process in place')
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--compress', dest='compress', action='store_true', default=True,
                        help='Compress images before embedding (default)')
    parser.add_argument('--no-compress', dest='compress', action='store_false',
                        help='Disable image compression')
    parser.add_argument('--max-dimension', type=int, default=2560,
                        help='Downscale images larger than this on either axis (default: 2560)')
    parser.add_argument('--image-scale', type=float, default=2.0,
                        help='Target pixels per rendered SVG pixel')
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the standalone diagnostic CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.svg.exists():
        print(f'Error: file not found: {args.svg}', file=sys.stderr)
        return 1
    if args.max_dimension < 1:
        print('Error: --max-dimension must be >= 1', file=sys.stderr)
        return 1
    if args.image_scale < 1:
        print('Error: --image-scale must be >= 1', file=sys.stderr)
        return 1

    proc, err = align_and_embed_images_in_svg(
        args.svg,
        dry_run=args.dry_run,
        verbose=args.verbose,
        compress=args.compress,
        max_dimension=args.max_dimension,
        image_scale=args.image_scale,
    )
    print(f'Processed {proc} image(s), {err} error(s)')
    return 1 if err else 0


if __name__ == '__main__':
    raise SystemExit(main())
