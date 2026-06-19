#!/usr/bin/env python3
"""
PPT Master - Beautify Identity Extractor

Extract a source deck's visual identity as JSON for the beautify-pptx workflow:
the declared `theme` (palette + major/minor fonts) plus `observed` usage
(run-level fonts incl. CJK `ea`, and frequent explicit fill colors) sampled
across slides — so the workflow can recommend theme vs actual-usage identity
and let the user confirm. Pure read: reuses the pptx_to_svg resolver, writes
no PPTX.

Usage:
    python3 scripts/beautify_identity.py <source.pptx> [-o identity.json]

Examples:
    python3 scripts/beautify_identity.py projects/x/sources/deck.pptx
    python3 scripts/beautify_identity.py deck.pptx -o projects/x/analysis/identity.json

Dependencies:
    None beyond the standard library (reuses scripts/pptx_to_svg/).

See workflows/beautify-pptx.md for how the emitted identity is consumed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from pptx_to_svg.color_resolver import ColorPalette  # noqa: E402
from pptx_to_svg.emu_units import NS  # noqa: E402
from pptx_to_svg.ooxml_loader import OoxmlPackage  # noqa: E402


def _font_pair(theme_root, font_tag: str) -> dict[str, str]:
    """Read one <a:majorFont> / <a:minorFont> into {latin, ea} (skip empties)."""
    out: dict[str, str] = {}
    font = theme_root.find(f".//a:fontScheme/a:{font_tag}", NS)
    if font is None:
        return out
    for slot, key in (("a:latin", "latin"), ("a:ea", "ea"), ("a:cs", "cs")):
        elem = font.find(slot, NS)
        if elem is not None:
            face = (elem.attrib.get("typeface") or "").strip()
            if face:
                out[key] = face
    return out


def _rank(counter: dict[str, int], limit: int) -> list[dict]:
    """Frequency-ranked [{value, count}, ...], most common first."""
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"value": v, "count": n} for v, n in ranked[:limit]]


def _sample_observed(pkg: "OoxmlPackage") -> dict:
    """Aggregate run-level fonts + explicit (non-theme) fill colors across slides.

    Theme extraction reports the *declared* identity; a hand-edited deck often
    overrides it per shape / run. This is a frequency sample of run-level usage
    (not a full style resolution — it misses schemeClr + master/layout
    inheritance, and counts chart/gradient fills), enough for the workflow to
    recommend theme vs observed.
    """
    latin: dict[str, int] = {}
    ea: dict[str, int] = {}
    colors: dict[str, int] = {}
    for slide in pkg.iter_slides():
        root = slide.part.xml
        for tag, bucket in (("a:latin", latin), ("a:ea", ea)):
            for elem in root.iterfind(f".//{tag}", NS):
                face = (elem.attrib.get("typeface") or "").strip()
                if face and not face.startswith("+"):  # skip +mj-*/+mn-* theme refs
                    bucket[face] = bucket.get(face, 0) + 1
        for elem in root.iterfind(".//a:srgbClr", NS):
            val = (elem.attrib.get("val") or "").strip().upper()
            if val:
                colors[f"#{val}"] = colors.get(f"#{val}", 0) + 1
    return {
        "fonts": {"latin": _rank(latin, 5), "ea": _rank(ea, 5)},
        "colors": _rank(colors, 8),
    }


def extract_identity(pptx_path: Path) -> dict:
    """Resolve the deck's theme + observed-usage identity, plus canvas."""
    with OoxmlPackage(pptx_path) as pkg:
        first = pkg.get_slide(1)
        master = first.master if first else None
        theme = pkg.resolve_theme(master)
        palette_resolver = ColorPalette(master, theme)

        # Presentation-level scheme names; ColorPalette applies clrMap + aliases.
        scheme = {
            "background": palette_resolver.resolve_scheme("bg1"),
            "background_alt": palette_resolver.resolve_scheme("bg2"),
            "text": palette_resolver.resolve_scheme("tx1"),
            "text_alt": palette_resolver.resolve_scheme("tx2"),
            "hyperlink": palette_resolver.resolve_scheme("hlink"),
        }
        accents = {
            f"accent{i}": palette_resolver.resolve_scheme(f"accent{i}")
            for i in range(1, 7)
        }
        palette = {
            k: (f"#{v}" if v else None)
            for k, v in {**scheme, **accents}.items()
        }
        # accent1 is the conventional primary.
        palette["primary"] = palette.get("accent1")

        fonts = {}
        if theme is not None:
            fonts = {
                "title": _font_pair(theme.xml, "majorFont"),
                "body": _font_pair(theme.xml, "minorFont"),
            }

        w, h = pkg.slide_size_px
        canvas = {
            "width_px": round(w),
            "height_px": round(h),
            "aspect": round(w / h, 4) if h else None,
        }

        return {
            "source": str(pptx_path),
            "slide_count": pkg.slide_count,
            "canvas": canvas,
            "theme": {"palette": palette, "fonts": fonts},
            "observed": _sample_observed(pkg),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a source deck's theme palette + fonts + canvas as JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", help="Source .pptx file")
    parser.add_argument(
        "-o", "--output",
        help="Write JSON here (default: stdout)",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    src = Path(args.source)
    if not src.is_file():
        print(f"[ERROR] source not found: {src}", file=sys.stderr)
        return 1

    try:
        identity = extract_identity(src)
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"[ERROR] failed to extract identity: {exc}", file=sys.stderr)
        return 1

    payload = json.dumps(identity, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(f"[OK] identity written to: {out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
