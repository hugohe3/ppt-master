#!/usr/bin/env python3
"""
PPT Master - Beautify Identity Extractor

Extract a source deck's visual identity as JSON for the beautify-pptx profile:
the declared `theme` (palette + major/minor fonts + master placeholder sizes,
full bodyStyle ramp in `sizes.body_levels`) plus `observed` usage (run-level
fonts incl. CJK `ea`, explicit point sizes, and frequent explicit fill colors)
sampled across slides, plus `layout_sizes_pt` (in-use layout body-placeholder
level-1 sizes — a reference hint, not an auto-seed) — so the workflow can
recommend theme vs actual-usage identity, incl. a source-derived body size
(seed chain: observed → theme.sizes.body → canvas baseline) and let the user
confirm. Pure read: reuses the pptx_to_svg resolver, writes
no PPTX.

Usage:
    python3 scripts/beautify_identity.py <source.pptx> [-o identity.json]

Examples:
    python3 scripts/beautify_identity.py projects/x/sources/deck.pptx
    python3 scripts/beautify_identity.py deck.pptx -o projects/x/analysis/deck.identity.json

Dependencies:
    None beyond the standard library (reuses scripts/pptx_to_svg/).

See workflows/profiles/beautify-pptx.md for how the emitted identity is consumed.
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

from console_encoding import configure_utf8_stdio  # noqa: E402
from pptx_to_svg.color_resolver import ColorPalette  # noqa: E402
from pptx_to_svg.emu_units import NS  # noqa: E402
from pptx_to_svg.ooxml_loader import OoxmlPackage  # noqa: E402

configure_utf8_stdio()


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


def _rank(counter: dict, limit: int) -> list[dict]:
    """Frequency-ranked [{value, count}, ...], most common first."""
    ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"value": v, "count": n} for v, n in ranked[:limit]]


def _master_text_sizes(master_root) -> dict:
    """Declared title/body point sizes from the master's <p:txStyles>.

    `title` is <p:titleStyle> level-1; `body` is <p:bodyStyle> level-1 and
    `body_levels` is every declared body outline level in order (lvl1..lvl9).
    `sz` is in hundredths of a point. This is the *declared* size — the
    placeholder default a run inherits when it sets no explicit `sz` — the size
    counterpart of `theme.fonts`. Note level-1 is the coarsest/largest body
    level and commonly over-reads real density; `body_levels` exposes the full
    ramp. Returns {} when no txStyles are present.
    """
    out: dict[str, object] = {}
    title = master_root.find(".//p:txStyles/p:titleStyle//a:defRPr", NS)
    if title is not None:
        sz = (title.attrib.get("sz") or "").strip()
        if sz.isdigit():
            out["title"] = int(sz) / 100
    body = master_root.find(".//p:txStyles/p:bodyStyle", NS)
    levels: list[float] = []
    if body is not None:
        for lvl in body:  # a:lvl1pPr .. a:lvl9pPr, in document order
            defrpr = lvl.find("a:defRPr", NS)
            if defrpr is None:
                continue
            sz = (defrpr.attrib.get("sz") or "").strip()
            if sz.isdigit():
                levels.append(int(sz) / 100)
    if levels:
        out["body"] = levels[0]
        out["body_levels"] = levels
    return out


# Placeholder types that carry chrome, not body text — excluded from the layout
# body-size sample so a 9pt footer / slide-number doesn't masquerade as body.
_NON_BODY_PH = {"title", "ctrTitle", "ftr", "sldNum", "dt", "hdr"}


def _layout_text_sizes(pkg: "OoxmlPackage") -> list[dict]:
    """Frequency-ranked **body** placeholder `defRPr` sizes across the layouts in use.

    For a theme/template-driven deck whose runs set no explicit `sz` (everything
    inherits its placeholder), this is where a real body size can show: each
    layout's body placeholder may declare its own size where the master only gives
    the coarse level-1 default. Only layouts actually referenced by a slide count,
    only body-ish placeholders (title / footer / slide-number / date / header
    skipped), and only the placeholder's **level-1** `defRPr` — the primary size —
    so deeper outline levels (lvl2..lvl9) don't masquerade as body. Sizes in
    points. Often sparse: placeholders that don't override level-1 inherit the
    master default and contribute nothing here.
    """
    sizes: dict[float, int] = {}
    seen: set[str] = set()
    for slide in pkg.iter_slides():
        layout = slide.layout
        if layout is None or layout.path in seen:
            continue
        seen.add(layout.path)
        for sp in layout.xml.iterfind(".//p:sp", NS):
            ph = sp.find(".//p:nvSpPr/p:nvPr/p:ph", NS)
            ph_type = ph.attrib.get("type") if ph is not None else None
            if ph_type in _NON_BODY_PH:
                continue
            lvl1 = sp.find(".//a:lstStyle/a:lvl1pPr/a:defRPr", NS)
            if lvl1 is None:
                continue
            sz = (lvl1.attrib.get("sz") or "").strip()
            if sz.isdigit():
                pt = int(sz) / 100
                sizes[pt] = sizes.get(pt, 0) + 1
    return _rank(sizes, 10)


def _sample_observed(pkg: "OoxmlPackage") -> dict:
    """Aggregate run-level fonts, explicit point sizes, and explicit fill colors.

    Theme extraction reports the *declared* identity; a hand-edited deck often
    overrides it per shape / run. This is a frequency sample of run-level usage
    (not a full style resolution — it misses schemeClr + master/layout
    inheritance, and counts chart/gradient fills), enough for the workflow to
    recommend theme vs observed. `sizes_pt` only counts runs that set an explicit
    `sz`; runs inheriting the placeholder size are not seen here (use
    `theme.sizes` for those), so a small sample is a hint, not the full picture.
    """
    latin: dict[str, int] = {}
    ea: dict[str, int] = {}
    sizes: dict[float, int] = {}
    colors: dict[str, int] = {}
    for slide in pkg.iter_slides():
        root = slide.part.xml
        for tag, bucket in (("a:latin", latin), ("a:ea", ea)):
            for elem in root.iterfind(f".//{tag}", NS):
                face = (elem.attrib.get("typeface") or "").strip()
                if face and not face.startswith("+"):  # skip +mj-*/+mn-* theme refs
                    bucket[face] = bucket.get(face, 0) + 1
        for elem in root.iterfind(".//a:rPr", NS):
            sz = (elem.attrib.get("sz") or "").strip()
            if sz.isdigit():
                pt = int(sz) / 100
                sizes[pt] = sizes.get(pt, 0) + 1
        for elem in root.iterfind(".//a:srgbClr", NS):
            val = (elem.attrib.get("val") or "").strip().upper()
            if val:
                colors[f"#{val}"] = colors.get(f"#{val}", 0) + 1
    return {
        "fonts": {"latin": _rank(latin, 5), "ea": _rank(ea, 5)},
        "sizes_pt": _rank(sizes, 8),
        "colors": _rank(colors, 8),
    }


def extract_identity(pptx_path: Path) -> dict:
    """Resolve the deck's theme + observed-usage identity, plus canvas."""
    with OoxmlPackage(pptx_path) as pkg:
        first = pkg.get_slide(1)
        master = first.master if first else None
        theme = pkg.resolve_theme(master)
        palette_resolver = ColorPalette(master, theme, strict=False)

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
        sizes = _master_text_sizes(master.xml) if master is not None else {}

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
            "theme": {"palette": palette, "fonts": fonts, "sizes": sizes},
            "observed": _sample_observed(pkg),
            "layout_sizes_pt": _layout_text_sizes(pkg),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a source deck's theme palette + fonts + sizes + canvas as JSON.",
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
