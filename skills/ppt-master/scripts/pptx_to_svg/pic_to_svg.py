"""DrawingML <p:pic> -> SVG <image> conversion.

Reverse of svg_to_pptx convert_image.

DrawingML structure:
    <p:pic>
        <p:blipFill>
            <a:blip r:embed="rIdN"/>
            <a:srcRect l/t/r/b="1/100000"/>      (optional crop)
            <a:stretch><a:fillRect/></a:stretch> (default: fill the shape)
        </p:blipFill>
        <p:spPr>
            <a:xfrm/>
            <a:prstGeom prst="rect"/>            (usually rect; can be other)
        </p:spPr>
    </p:pic>

Strategy:
- Default (no srcRect, plain stretch) -> a single <image> filling the box,
  preserveAspectRatio="none".
- With srcRect -> wrap the <image> in a nested <svg viewBox> in the unit
  rectangle [0,1] x [0,1], so cropping is expressed as the visible viewBox
  region. preserveAspectRatio="none" both inside and outside.
- Image bytes are written through the result; the slide assembler decides
  the href format (external file vs base64).
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from .emu_units import NS, Xfrm, fmt_num
from .ooxml_loader import OoxmlPackage, PartRef


@dataclass
class PictureResult:
    """Resolved picture: SVG element string + extracted media bytes."""

    svg: str = ""
    # Map of {filename: bytes} that the assembler should emit alongside
    # the SVG. Filename is the basename inside the package's media dir.
    media: dict[str, bytes] = field(default_factory=dict)


def convert_picture(
    pic_elem: ET.Element,
    xfrm: Xfrm,
    slide_part: PartRef,
    pkg: OoxmlPackage,
    *,
    media_subdir: str = "assets",
    embed_inline: bool = False,
) -> PictureResult:
    """Translate <p:pic> to SVG <image> (or nested <svg>+<image> for cropping)."""
    blip_fill = pic_elem.find("p:blipFill", NS)
    if blip_fill is None:
        return PictureResult()

    blip = blip_fill.find("a:blip", NS)
    if blip is None:
        return PictureResult()

    rid = blip.attrib.get(f"{{{NS['r']}}}embed")
    if not rid:
        return PictureResult()

    target = slide_part.resolve_rel(rid)
    if not target:
        return PictureResult()

    # Read the bytes
    img_bytes = pkg.read_media(target)
    if img_bytes is None:
        return PictureResult()

    filename = pkg.media_filename(target)
    href = _build_href(filename, img_bytes, media_subdir, embed_inline)

    # srcRect: l/t/r/b in 1/100000ths (so 50000 = 50%).
    src_rect = blip_fill.find("a:srcRect", NS)
    crop = _parse_src_rect(src_rect)

    # stretch / tile: default stretch+fillRect means "fill, ignore aspect ratio".
    has_stretch = blip_fill.find("a:stretch") is not None
    if not has_stretch:
        # tile mode is rare; for v1 fall back to plain image.
        pass

    if crop is None:
        # Plain unclipped image
        svg = (
            f'<image href="{href}" x="{fmt_num(xfrm.x)}" y="{fmt_num(xfrm.y)}" '
            f'width="{fmt_num(xfrm.w)}" height="{fmt_num(xfrm.h)}" '
            f'preserveAspectRatio="none"/>'
        )
    else:
        # Crop expressed as a unit-rectangle viewBox on a nested <svg>.
        vb_l, vb_t, vb_w, vb_h = crop
        svg = (
            f'<svg x="{fmt_num(xfrm.x)}" y="{fmt_num(xfrm.y)}" '
            f'width="{fmt_num(xfrm.w)}" height="{fmt_num(xfrm.h)}" '
            f'viewBox="{fmt_num(vb_l, 5)} {fmt_num(vb_t, 5)} '
            f'{fmt_num(vb_w, 5)} {fmt_num(vb_h, 5)}" '
            f'preserveAspectRatio="none">'
            f'<image href="{href}" x="0" y="0" width="1" height="1" '
            f'preserveAspectRatio="none"/>'
            f"</svg>"
        )

    media: dict[str, bytes] = {}
    if not embed_inline:
        media[filename] = img_bytes
    return PictureResult(svg=svg, media=media)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
