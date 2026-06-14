#!/usr/bin/env python3
"""
PPT Master - Native Diagram Demo (one-command reproduction)

Builds a two-slide PPTX that shows the native-diagram pipeline end to end, using
only assets that ship in this repo (no client/vendor decks):

    slide 1  the CC0 component `demo_synthetic_platform`, placed via a
             `data-native-diagram` rect, recolored to a sample brand palette and
             re-texted onto a NEW scenario through `data-text` (object form,
             every slot covered, each within its visual-width budget);
    slide 2  the same content drawn by hand as flat SVG rects/text — the
             "without a native diagram" baseline, for an apples-to-apples
             before/after.

The point of the contrast: slide 1's SVG carries ONE placeholder rect (the
polished, gradient-shaded, still-editable figure is spliced in at conversion
time by native_diagram_resolver.py), while slide 2 needs ~40 hand-placed shapes
to approximate it and still reads flat.

Usage:
    py -3.11 skills/ppt-master/scripts/demo_native_diagram.py [-o OUT_DIR]

Examples:
    py -3.11 skills/ppt-master/scripts/demo_native_diagram.py
    py -3.11 skills/ppt-master/scripts/demo_native_diagram.py -o /tmp/nd_demo

Dependencies:
    python-pptx, lxml (same as the rest of the svg_to_pptx pipeline).

See references/native-diagrams.md for the placeholder attribute contract.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
COMPONENT = "demo_synthetic_platform"

# Sample brand palette the demo recolors INTO. The component's base hexes are the
# documented recolor bases (558C5A primary, 122B87 accent); all gradient/3D depth
# is carried by modifiers on those two, so this single remap re-themes the figure.
BRAND_PRIMARY = "0E7C7B"   # teal
BRAND_ACCENT = "E8743B"    # orange
FONT = "Microsoft YaHei"

# A NEW scenario mapped onto the component's 22 slots (smart-manufacturing), to
# prove re-texting. Each string stays within its slot's visual-width budget — a
# CJK glyph is 2 columns (see meta.json slot_spec).
TITLE = "智能制造一体化平台"                                   # slot 0  (budget 22)
LAYERS = [
    ("业务层", "BUSINESS", ["排产", "质检", "仓储", "物流", "追溯"]),       # 1,2 / 3-7
    ("平台层", "PLATFORM", ["设备互联", "数据采集", "工艺建模", "能耗优化", "质量分析"]),  # 8,9 / 10-14
    ("设施层", "INFRA", ["网络", "算力", "存储", "安全", "运维"]),          # 15,16 / 17-21
]


def _data_text() -> dict:
    """Build the slot-id -> text map (document order, matching meta.text_slots)."""
    fills = {0: TITLE}
    sid = 1
    for cn, en, cards in LAYERS:
        fills[sid] = cn
        fills[sid + 1] = en
        sid += 2
        for label in cards:
            fills[sid] = label
            sid += 1
    return fills


def native_svg() -> str:
    """Slide 1: a single data-native-diagram placeholder (figure comes from the component)."""
    data_text = json.dumps(_data_text(), ensure_ascii=False)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n'
        '  <rect width="1280" height="720" fill="#FFFFFF"/>\n'
        f'  <rect data-native-diagram="{COMPONENT}"\n'
        f'        data-recolor="558C5A={BRAND_PRIMARY},122B87={BRAND_ACCENT}"\n'
        f'        data-font="{FONT}"\n'
        f"        data-text='{data_text}'\n"
        '        x="40" y="30" width="1200" height="660" fill="none"\n'
        '        stroke="#CCCCCC" stroke-dasharray="6 6"/>\n'
        '</svg>\n'
    )


def _rect(x, y, w, h, fill, rx=10):
    return f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#{fill}"/>\n'


def _text(x, y, s, size, fill, *, bold=True, anchor="middle"):
    weight = ' font-weight="700"' if bold else ""
    return (f'  <text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}"'
            f'{weight} fill="#{fill}" text-anchor="{anchor}">{s}</text>\n')


def handdrawn_svg() -> str:
    """Slide 2: the same content drawn by hand — flat rects/text, no component."""
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">\n']
    out.append('  <rect width="1280" height="720" fill="#FFFFFF"/>\n')
    out.append(_text(640, 70, TITLE, 32, "1F2A37"))
    band_x, band_w, band_h = 80, 1120, 156
    band_ys = [126, 312, 498]
    cap_x, cap_w = 108, 196
    card_w, card_h, gap = 140, 92, 30
    cards_x0 = cap_x + cap_w + 40
    for (cn, en, cards), by in zip(LAYERS, band_ys):
        out.append(_rect(band_x, by, band_w, band_h, BRAND_PRIMARY, rx=14))
        cap_y = by + (band_h - 96) // 2
        out.append(_rect(cap_x, cap_y, cap_w, 96, "0A5C5A", rx=12))   # darker teal cap
        out.append(_text(cap_x + cap_w // 2, cap_y + 44, cn, 20, "FFFFFF"))
        out.append(_text(cap_x + cap_w // 2, cap_y + 70, en, 11, "CFE6E5", bold=False))
        card_y = by + (band_h - card_h) // 2
        for i, label in enumerate(cards):
            cx = cards_x0 + i * (card_w + gap)
            out.append(_rect(cx, card_y, card_w, card_h, BRAND_ACCENT, rx=12))
            out.append(_text(cx + card_w // 2, card_y + card_h // 2 + 6, label, 16, "FFFFFF"))
    out.append('</svg>\n')
    return "".join(out)


def _run(label, cmd):
    print(f"\n$ {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, cwd=str(SCRIPTS_DIR.parents[2]))
    if r.returncode != 0:
        print(f"[demo] {label} failed (exit {r.returncode})", file=sys.stderr)
        raise SystemExit(r.returncode)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="One-command native-diagram before/after reproduction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("-o", "--out", default="native_diagram_demo_out",
                    help="Disposable output project dir (default: ./native_diagram_demo_out)")
    args = ap.parse_args(argv)

    out = Path(args.out).resolve()
    svg_output = out / "svg_output"
    svg_output.mkdir(parents=True, exist_ok=True)
    (svg_output / "01_native.svg").write_text(native_svg(), encoding="utf-8")
    (svg_output / "02_handdrawn.svg").write_text(handdrawn_svg(), encoding="utf-8")
    print(f"[demo] wrote 2 SVGs to {svg_output}")
    print(f"[demo] recolor 558C5A->{BRAND_PRIMARY}, 122B87->{BRAND_ACCENT}; "
          f"data-text covers {len(_data_text())} slots")

    _run("finalize_svg", [sys.executable, str(SCRIPTS_DIR / "finalize_svg.py"), str(out)])
    _run("svg_to_pptx", [sys.executable, str(SCRIPTS_DIR / "svg_to_pptx.py"), str(out)])

    pptxs = sorted((out / "exports").glob("*.pptx"), key=lambda p: p.stat().st_mtime)
    print("\n[demo] done.")
    if pptxs:
        print(f"[demo] PPTX: {pptxs[-1]}")
        print("[demo] slide 1 = native component (recolored + re-texted), "
              "slide 2 = hand-drawn baseline.")
    else:
        print("[demo] WARNING: no PPTX found under exports/ — check the log above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
