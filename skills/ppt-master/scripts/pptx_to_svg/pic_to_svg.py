"""DrawingML <p:pic> -> SVG <image> conversion.

Reverse of svg_to_pptx convert_image.

DrawingML structure:
    <p:pic>
        <p:blipFill>
            <a:blip r:embed="rIdRaster">
                <a:extLst>...<asvg:svgBlip r:embed="rIdSvg"/>...</a:extLst>
            </a:blip>
            <a:srcRect l/t/r/b="1/100000"/>      (optional crop)
            <a:stretch><a:fillRect/></a:stretch> (default: fill the shape)
        </p:blipFill>
        <p:spPr>
            <a:xfrm/>
            <a:prstGeom prst="rect"/>            (usually rect; can be other)
        </p:spPr>
    </p:pic>

Strategy:
- Prefer the editable SVG relationship in asvg:svgBlip when Office also stores
  a raster compatibility preview on a:blip; retain the raster as fallback.
- Default (no srcRect, plain stretch) -> a single <image> filling the box,
  preserveAspectRatio="none".
- With srcRect, or with a single oversized tile that covers the frame -> wrap
  the <image> in a nested <svg viewBox> in the unit rectangle [0,1] x [0,1],
  with overflow hidden so cropping is expressed identically in browsers and
  PowerPoint.
- Repeating tile fills still use the legacy plain-image fallback; a repeated
  pattern cannot be represented by the project's native picture-crop subset.
- Image bytes are written through the result; the slide assembler decides
  the href format (external file vs base64).
"""

from __future__ import annotations

import base64
import hashlib
import io
import math
import mimetypes
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from PIL import Image, ImageEnhance
except ImportError:  # pragma: no cover - optional visual enhancement dependency
    Image = None
    ImageEnhance = None

from .emu_units import NS, Xfrm, emu_to_px, fmt_num, format_ooxml_alpha
from .ooxml_loader import OoxmlPackage, PartRef, blip_embed_relationship_ids


@dataclass(frozen=True)
class PictureDiagnostic:
    """Recoverable loss while converting one DrawingML picture."""

    code: str
    message: str
    fallback: str


@dataclass
class PictureResult:
    """Resolved picture: SVG element string + extracted media bytes."""

    svg: str = ""
    # Map of {filename: bytes} that the assembler should emit alongside
    # the SVG. Filename is the basename inside the package's media dir.
    media: dict[str, bytes] = field(default_factory=dict)
    diagnostics: tuple[PictureDiagnostic, ...] = ()
    external_linked: bool = False


class MediaResolutionError(RuntimeError):
    """Raised when a PPTX media relationship cannot be reproduced as SVG."""


class LinkedImageResolutionError(MediaResolutionError):
    """Raised when an external linked image has no embedded preview."""


def convert_blip_fill(
    blip_fill_elem: ET.Element,
    xfrm: Xfrm,
    slide_part: PartRef,
    pkg: OoxmlPackage,
    *,
    media_subdir: str = "images",
    embed_inline: bool = False,
    asset_name_map: dict[str, str] | None = None,
    strict: bool = False,
) -> PictureResult:
    """Convert an <a:blipFill> element to SVG <image>.

    Handles image fill for both:
    - <p:pic><p:blipFill> (standard picture elements)
    - <p:sp><p:spPr><a:blipFill> (shape with image fill, e.g. Canva exports)
    """
    blip = blip_fill_elem.find("a:blip", NS)
    if blip is None:
        return PictureResult()

    relationship_ids = blip_embed_relationship_ids(blip)
    linked_rid = blip.attrib.get(f"{{{NS['r']}}}link")
    linked_relationship = slide_part.rels.get(linked_rid or "", {})
    external_linked = linked_relationship.get("external") == "1"
    if not relationship_ids:
        if external_linked:
            raise LinkedImageResolutionError(
                "Linked image relationships are not supported; embed the image in PowerPoint first"
            )
        if linked_rid:
            raise MediaResolutionError(
                "Linked image relationship cannot be resolved; embed the image in PowerPoint first"
            )
        return PictureResult()

    target: str | None = None
    img_bytes: bytes | None = None
    failures: list[str] = []
    for rel_id in relationship_ids:
        candidate = slide_part.resolve_rel(rel_id)
        if not candidate:
            failures.append(f"{rel_id}: unresolved")
            continue
        candidate_bytes = pkg.read_media(candidate)
        if candidate_bytes is None:
            failures.append(f"{rel_id}: missing {candidate}")
            continue
        if Path(candidate).suffix.lower() == ".svg" and not _is_valid_svg_media(candidate_bytes):
            failures.append(f"{rel_id}: invalid SVG media {candidate}")
            continue
        target = candidate
        img_bytes = candidate_bytes
        break
    if target is None or img_bytes is None:
        details = "; ".join(failures)
        error_type = (
            LinkedImageResolutionError
            if external_linked
            else MediaResolutionError
        )
        raise error_type(
            f"No embedded image relationship can be read in {slide_part.path}: {details}"
        )

    filename = (asset_name_map or {}).get(target, pkg.media_filename(target))
    filename, img_bytes = _normalize_office_media(filename, img_bytes)
    tile_source_bytes = img_bytes
    diagnostics = list(_unsupported_blip_effect_diagnostics(blip))
    filename, img_bytes, effect_diagnostics = _apply_blip_image_effects(
        filename,
        img_bytes,
        blip,
    )
    diagnostics.extend(effect_diagnostics)
    opacity_attr, opacity_diagnostics = _blip_opacity_attr(blip)
    diagnostics.extend(opacity_diagnostics)
    if strict and diagnostics:
        details = "; ".join(item.message for item in diagnostics)
        raise ValueError(f"Cannot reproduce DrawingML picture effects: {details}")
    href = _build_href(filename, img_bytes, media_subdir, embed_inline)

    # srcRect: l/t/r/b in 1/100000ths (so 50000 = 50%).
    src_rect = blip_fill_elem.find("a:srcRect", NS)
    crop = _parse_src_rect(src_rect)

    # A tile larger than its frame is visually a crop, not a stretch. Preserve
    # that common PowerPoint background construction through the same nested
    # SVG transport used for srcRect. True repeated patterns retain the legacy
    # plain-image fallback because native export has no registered tile subset.
    tile = blip_fill_elem.find("a:tile", NS)
    if crop is None and tile is not None:
        crop = _single_cover_tile_crop(
            tile,
            blip_fill_elem,
            xfrm,
            tile_source_bytes,
        )

    if crop is None:
        # Plain unclipped image
        svg = (
            f'<image href="{href}" x="{fmt_num(xfrm.x)}" y="{fmt_num(xfrm.y)}" '
            f'width="{fmt_num(xfrm.w)}" height="{fmt_num(xfrm.h)}" '
            f'preserveAspectRatio="none"{opacity_attr}/>'
        )
    else:
        # Crop expressed as a unit-rectangle viewBox on a nested <svg>.
        vb_l, vb_t, vb_w, vb_h = crop
        svg = (
            f'<svg x="{fmt_num(xfrm.x)}" y="{fmt_num(xfrm.y)}" '
            f'width="{fmt_num(xfrm.w)}" height="{fmt_num(xfrm.h)}" '
            f'viewBox="{fmt_num(vb_l, 5)} {fmt_num(vb_t, 5)} '
            f'{fmt_num(vb_w, 5)} {fmt_num(vb_h, 5)}" '
            f'preserveAspectRatio="none" overflow="hidden">'
            f'<image href="{href}" x="0" y="0" width="1" height="1" '
            f'preserveAspectRatio="none"{opacity_attr}/>'
            f"</svg>"
        )

    media: dict[str, bytes] = {}
    if not embed_inline:
        media[filename] = img_bytes
    return PictureResult(
        svg=svg,
        media=media,
        diagnostics=tuple(diagnostics),
        external_linked=external_linked,
    )


def convert_picture(
    pic_elem: ET.Element,
    xfrm: Xfrm,
    slide_part: PartRef,
    pkg: OoxmlPackage,
    *,
    media_subdir: str = "images",
    embed_inline: bool = False,
    asset_name_map: dict[str, str] | None = None,
    strict: bool = False,
) -> PictureResult:
    """Translate <p:pic> to SVG <image> (or nested <svg>+<image> for cropping)."""
    blip_fill = pic_elem.find("p:blipFill", NS)
    if blip_fill is None:
        return PictureResult()

    return convert_blip_fill(
        blip_fill, xfrm, slide_part, pkg,
        media_subdir=media_subdir,
        embed_inline=embed_inline,
        asset_name_map=asset_name_map,
        strict=strict,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _blip_opacity_attr(
    blip: ET.Element,
) -> tuple[str, tuple[PictureDiagnostic, ...]]:
    """Translate DrawingML fixed image alpha to an SVG opacity attribute."""
    alpha_effects = blip.findall("a:alphaModFix", NS)
    if not alpha_effects:
        return "", ()
    if len(alpha_effects) > 1:
        return "", (
            _effect_diagnostic(
                "duplicate a:alphaModFix effects cannot be reproduced safely"
            ),
        )
    alpha = alpha_effects[0]
    try:
        opacity = float(alpha.attrib.get("amt", "100000")) / 100000.0
    except ValueError:
        return "", (
            _effect_diagnostic(
                f"invalid a:alphaModFix amt={alpha.attrib.get('amt')!r}"
            ),
        )
    if not math.isfinite(opacity) or not 0.0 <= opacity <= 1.0:
        return "", (
            _effect_diagnostic(
                f"out-of-range a:alphaModFix amt={alpha.attrib.get('amt')!r}"
            ),
        )
    if opacity >= 1.0:
        return "", ()
    return f' opacity="{format_ooxml_alpha(opacity)}"', ()


def _effect_diagnostic(message: str) -> PictureDiagnostic:
    return PictureDiagnostic(
        code="image-effect-omitted",
        message=message,
        fallback="retain the source image and omit only this image effect",
    )


def _unsupported_blip_effect_diagnostics(
    blip: ET.Element,
) -> tuple[PictureDiagnostic, ...]:
    """Report direct a:blip effects outside the implemented subset."""
    supported_tags = {
        f"{{{NS['a']}}}lum",
        f"{{{NS['a']}}}alphaModFix",
        f"{{{NS['a']}}}extLst",
    }
    unsupported = sorted({
        child.tag.rsplit("}", 1)[-1]
        for child in blip
        if child.tag not in supported_tags
    })
    diagnostics = (
        [
            _effect_diagnostic(
                "unsupported direct a:blip effect(s): "
                + ", ".join(f"a:{name}" for name in unsupported)
            )
        ]
        if unsupported
        else []
    )
    if len(blip.findall("a:lum", NS)) > 1:
        diagnostics.append(
            _effect_diagnostic(
                "duplicate a:lum effects cannot be reproduced safely"
            )
        )
    return tuple(diagnostics)

_OFFICE_VECTOR_EXTS = {".emf", ".wmf"}


def _is_valid_svg_media(data: bytes) -> bool:
    """Return whether one media part is a namespaced SVG document."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return False
    return root.tag == "{http://www.w3.org/2000/svg}svg"


def _normalize_office_media(filename: str, img_bytes: bytes) -> tuple[str, bytes]:
    """Convert Office-only vector image formats to browser-renderable PNG.

    PPTX can contain EMF/WMF assets that PowerPoint renders natively but SVG
    viewers generally do not. Keep the original asset in the manifest layer;
    the SVG view uses a PNG preview when the local system can make one.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in _OFFICE_VECTOR_EXTS:
        return filename, img_bytes

    converted = _convert_office_vector_to_png(filename, img_bytes)
    if converted is None:
        return filename, img_bytes
    stem = Path(filename).stem
    return f"{stem}_preview.png", converted


def _convert_office_vector_to_png(filename: str, img_bytes: bytes) -> bytes | None:
    magick = shutil.which("magick")
    if not magick:
        return None
    suffix = Path(filename).suffix.lower() or ".bin"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src = tmp_dir / f"source{suffix}"
        dst = tmp_dir / "preview.png"
        src.write_bytes(img_bytes)
        try:
            subprocess.run(
                [magick, str(src), str(dst)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        if not dst.exists():
            return None
        return dst.read_bytes()

def _parse_src_rect(elem: ET.Element | None) -> tuple[float, float, float, float] | None:
    """Convert <a:srcRect l t r b="1/100000"/> to (x, y, w, h) in unit space."""
    if elem is None:
        return None
    if not (elem.attrib.keys() & {"l", "t", "r", "b"}):
        return None
    l = _pct_attr(elem, "l")
    t = _pct_attr(elem, "t")
    r = _pct_attr(elem, "r")
    b = _pct_attr(elem, "b")
    # All zero -> equivalent to no crop
    if l == 0 and t == 0 and r == 0 and b == 0:
        return None
    vb_x = l
    vb_y = t
    vb_w = max(0.0, 1.0 - l - r)
    vb_h = max(0.0, 1.0 - t - b)
    if vb_w <= 0 or vb_h <= 0:
        return None
    return vb_x, vb_y, vb_w, vb_h


def _single_cover_tile_crop(
    tile: ET.Element,
    blip_fill: ET.Element,
    xfrm: Xfrm,
    img_bytes: bytes,
) -> tuple[float, float, float, float] | None:
    """Map one oversized DrawingML tile to a unit-image crop window.

    The closed SVG/PPTX crop transport cannot express a repeating pattern. It
    can, however, reproduce a tile when the aligned first tile alone covers the
    complete frame. This is how PowerPoint commonly stores full-page bitmap
    backgrounds without distorting their aspect ratio.
    """
    if Image is None or xfrm.w <= 0 or xfrm.h <= 0:
        return None
    if tile.attrib.get("flip", "none") != "none":
        return None

    natural_size = _image_size_at_96_dpi(img_bytes, blip_fill)
    if natural_size is None:
        return None
    natural_w, natural_h = natural_size
    scale_x = _pct_attr_default(tile, "sx", 1.0)
    scale_y = _pct_attr_default(tile, "sy", 1.0)
    tile_w = natural_w * scale_x
    tile_h = natural_h * scale_y
    if tile_w <= 0 or tile_h <= 0:
        return None

    align_x, align_y = _tile_alignment(tile.attrib.get("algn", "tl"))
    tile_x = (
        xfrm.x
        + (xfrm.w - tile_w) * align_x
        + emu_to_px(tile.attrib.get("tx"))
    )
    tile_y = (
        xfrm.y
        + (xfrm.h - tile_h) * align_y
        + emu_to_px(tile.attrib.get("ty"))
    )

    tolerance = 1e-4
    if (
        tile_x > xfrm.x + tolerance
        or tile_y > xfrm.y + tolerance
        or tile_x + tile_w < xfrm.x + xfrm.w - tolerance
        or tile_y + tile_h < xfrm.y + xfrm.h - tolerance
    ):
        return None

    crop = (
        (xfrm.x - tile_x) / tile_w,
        (xfrm.y - tile_y) / tile_h,
        xfrm.w / tile_w,
        xfrm.h / tile_h,
    )
    if all(
        abs(actual - expected) <= 1e-7
        for actual, expected in zip(crop, (0.0, 0.0, 1.0, 1.0))
    ):
        return None
    return crop


def _image_size_at_96_dpi(
    img_bytes: bytes,
    blip_fill: ET.Element,
) -> tuple[float, float] | None:
    """Return the bitmap's physical size in the SVG canvas' 96-DPI pixels."""
    try:
        with Image.open(io.BytesIO(img_bytes)) as image:
            pixel_w, pixel_h = image.size
            embedded_dpi = image.info.get("dpi")
    except (OSError, ValueError):
        return None

    configured_dpi = _positive_float(blip_fill.attrib.get("dpi"))
    if configured_dpi is not None:
        dpi_x = dpi_y = configured_dpi
    else:
        dpi_x, dpi_y = _dpi_pair(embedded_dpi)
    return pixel_w * 96.0 / dpi_x, pixel_h * 96.0 / dpi_y


def _dpi_pair(value: object) -> tuple[float, float]:
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        dpi_x = _positive_float(value[0]) or 96.0
        dpi_y = _positive_float(value[1]) or 96.0
        return dpi_x, dpi_y
    dpi = _positive_float(value) or 96.0
    return dpi, dpi


def _positive_float(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _pct_attr_default(elem: ET.Element, name: str, default: float) -> float:
    value = elem.attrib.get(name)
    if value is None:
        return default
    try:
        return float(value) / 100000.0
    except ValueError:
        return default


def _tile_alignment(value: str) -> tuple[float, float]:
    alignments = {
        "tl": (0.0, 0.0),
        "t": (0.5, 0.0),
        "tr": (1.0, 0.0),
        "l": (0.0, 0.5),
        "ctr": (0.5, 0.5),
        "r": (1.0, 0.5),
        "bl": (0.0, 1.0),
        "b": (0.5, 1.0),
        "br": (1.0, 1.0),
    }
    return alignments.get(value, alignments["tl"])


def _apply_blip_image_effects(
    filename: str,
    img_bytes: bytes,
    blip: ET.Element,
) -> tuple[str, bytes, tuple[PictureDiagnostic, ...]]:
    """Bake supported DrawingML blip effects into extracted image bytes.

    Brightness and contrast are pixel operations, not picture-shape
    shadow/glow effects, so preserve them in the extracted bitmap.
    """
    lum_effects = blip.findall("a:lum", NS)
    if not lum_effects:
        return filename, img_bytes, ()
    if len(lum_effects) > 1:
        return filename, img_bytes, ()
    lum = lum_effects[0]

    values: dict[str, float | None] = {}
    for name in ("bright", "contrast"):
        raw_value = lum.attrib.get(name)
        if raw_value is None:
            values[name] = None
            continue
        try:
            value = float(raw_value) / 100000.0
        except ValueError:
            return filename, img_bytes, (
                _effect_diagnostic(f"invalid a:lum {name}={raw_value!r}"),
            )
        if not math.isfinite(value) or not -1.0 <= value <= 1.0:
            return filename, img_bytes, (
                _effect_diagnostic(
                    f"out-of-range a:lum {name}={raw_value!r}"
                ),
            )
        values[name] = value
    bright = values["bright"]
    contrast = values["contrast"]
    if bright is None and contrast is None:
        return filename, img_bytes, ()
    if Image is None or ImageEnhance is None:
        return filename, img_bytes, (
            _effect_diagnostic(
                "a:lum requires Pillow, but Pillow is unavailable"
            ),
        )

    try:
        with Image.open(io.BytesIO(img_bytes)) as source_image:
            if getattr(source_image, "is_animated", False):
                return filename, img_bytes, (
                    _effect_diagnostic(
                        "a:lum on an animated image would flatten its frames"
                    ),
                )
            output_format = (
                source_image.format or _pil_format_from_filename(filename)
            )
            image = source_image.copy()
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        if bright is not None:
            image = ImageEnhance.Brightness(image).enhance(max(0.0, 1.0 + bright))
        if contrast is not None:
            image = ImageEnhance.Contrast(image).enhance(max(0.0, 1.0 + contrast))

        out = io.BytesIO()
        save_format = output_format or "PNG"
        save_kwargs = {"quality": 95} if save_format.upper() in {"JPEG", "JPG"} else {}
        image.save(out, format=save_format, **save_kwargs)
        effect_key = f"lum-{bright}-{contrast}".encode("ascii")
        digest = hashlib.sha1(effect_key).hexdigest()[:8]
        return (
            _effect_filename(filename, digest, save_format),
            out.getvalue(),
            (),
        )
    except (KeyError, OSError, ValueError) as exc:
        return filename, img_bytes, (
            _effect_diagnostic(f"a:lum could not be rendered: {exc}"),
        )


def _pil_format_from_filename(filename: str) -> str | None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in {"jpg", "jpeg"}:
        return "JPEG"
    if ext == "png":
        return "PNG"
    if ext == "gif":
        return "GIF"
    if ext == "webp":
        return "WEBP"
    return None


def _effect_filename(filename: str, digest: str, image_format: str) -> str:
    stem, sep, ext = filename.rpartition(".")
    if not sep:
        ext = (image_format or "png").lower()
        stem = filename
    if ext.lower() == "jpg":
        ext = "jpeg"
    return f"{stem}_fx_{digest}.{ext}"


def _pct_attr(elem: ET.Element, name: str) -> float:
    val = elem.attrib.get(name)
    if val is None:
        return 0.0
    try:
        return float(val) / 100000.0
    except ValueError:
        return 0.0


def _build_href(filename: str, img_bytes: bytes, subdir: str, embed: bool) -> str:
    """Build an <image href=...> value (relative path or data URI).

    The path is relative to the SVG file's location. The slide assembler writes
    SVGs to <output>/svg/, so media files in <output>/<subdir>/ resolve via
    a leading "../".
    """
    if embed:
        mime = (
            mimetypes.guess_type(filename)[0]
            or _sniff_mime(img_bytes)
            or "application/octet-stream"
        )
        encoded = base64.b64encode(img_bytes).decode("ascii")
        return f"data:{mime};base64,{encoded}"
    rel = f"../{subdir}/{filename}" if subdir else f"../{filename}"
    return rel


def _sniff_mime(data: bytes) -> str | None:
    """Best-effort MIME sniffing for embedded images."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"<svg") or data.startswith(b"<?xml"):
        return "image/svg+xml"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None
