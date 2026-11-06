#!/usr/bin/env python3
"""
PPT Master - Image Depth Normalization

Reduce 16-bit grayscale to 8-bit before Pillow RGB conversion, preserving
the encoded range instead of clipping every sample above 255 to white.

Usage:
    Import normalize_grayscale_depth from image_normalization.

Examples:
    normalized = normalize_grayscale_depth(oriented, source_format=source.format)

Dependencies:
    Pillow

See scripts/docs/image.md for the slicing and image-treatment contracts.
"""

from typing import Optional

from PIL import Image


def normalize_grayscale_depth(
    image: Image.Image, *, source_format: Optional[str] = None,
) -> Image.Image:
    """Return 8-bit grayscale for 16-bit input, otherwise return the input unchanged.

    Older Pillow versions decode 16-bit grayscale PNG as I. The original file
    format distinguishes that case from arbitrary 32-bit integer images after
    EXIF transposition has discarded the format attribute.
    """
    is_gray16 = image.mode.startswith("I;16") or (
        image.mode == "I" and (source_format or image.format) == "PNG"
    )
    if not is_gray16:
        return image
    with image.convert("I") as integer:
        normalized = integer.point(lambda value: value / 256).convert("L")
        transparent = normalized.info.pop("transparency", None)
        if transparent is not None:
            # Match the full-depth transparent sample before discarding low bits.
            alpha_table = [255] * 65536
            alpha_table[transparent] = 0
            with integer.point(alpha_table, "L") as alpha:
                normalized.putalpha(alpha)
    return normalized
