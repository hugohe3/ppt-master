#!/usr/bin/env python3
"""Build a browsable HTML gallery of the native-diagram library.

Reads ``diagrams_index.json`` and per-diagram thumbnails (``<previews>/<key>.png``)
and writes a single ``gallery.html`` you open in any browser: a searchable grid of
every component with its key, title, slide number, shape count, and media/chart
badges. Thumbnails are rendered separately (e.g. via PowerPoint export of the
source slides, which are pixel-faithful to the lifted components).

Usage::

    python3 scripts/make_gallery.py [library_dir] [--previews _previews] [-o gallery.html]
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

LIB_DEFAULT = "skills/ppt-master/templates/native_diagrams"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an HTML gallery of the native-diagram library.")
    ap.add_argument("library", nargs="?", default=LIB_DEFAULT)
    ap.add_argument("--previews", default="_previews", help="thumbnail subdir relative to library")
    ap.add_argument("-o", "--output", help="output html (default: <library>/gallery.html)")
    args = ap.parse_args()

    lib = Path(args.library)
    index = json.loads((lib / "diagrams_index.json").read_text(encoding="utf-8"))
    out = Path(args.output) if args.output else lib / "gallery.html"
    prev = args.previews

    cards = []
    for key, e in sorted(index.items()):
        thumb = f"{prev}/{key}.png"
        summary = html.escape(str(e.get("summary", "")))
        media = e.get("media", 0)
        badges = ""
        if media:
            badges += f'<span class="b media">img {media}</span>'
        if e.get("charts"):
            badges += '<span class="b chart">chart</span>'
        img = (
            f'<img loading="lazy" src="{thumb}">'
            if (lib / thumb).exists()
            else '<div class="noimg">no preview</div>'
        )
        cards.append(
            f'<div class="card" data-k="{html.escape(key)}" data-t="{summary}">{img}'
            f'<div class="m"><b>{html.escape(key)}</b> · slide {e.get("slide")}<br>'
            f'{summary}<div class="s">shapes {e.get("shapes")} {badges}</div></div></div>'
        )

    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Native Diagram Library</title><style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f4f5f7;color:#222}}
header{{position:sticky;top:0;z-index:9;background:#fff;padding:10px 16px;border-bottom:1px solid #ddd;display:flex;gap:14px;align-items:center}}
input{{padding:8px;width:300px;border:1px solid #ccc;border-radius:6px;font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px;padding:16px}}
.card{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;overflow:hidden}}
.card img{{width:100%;display:block;background:#fafafa}}
.noimg{{height:160px;display:flex;align-items:center;justify-content:center;color:#bbb}}
.m{{padding:8px 10px;font-size:13px;line-height:1.45}}
.s{{margin-top:4px;color:#666;font-size:12px}}
.b{{display:inline-block;font-size:11px;padding:1px 6px;border-radius:4px;margin-left:5px;color:#5a3d00}}
.media{{background:#ffe0b2}}.chart{{background:#ffcdd2;color:#7a0000}}
</style></head><body>
<header><b>Native Diagram Library</b><span id="c">{len(index)}</span> shown
<input id="q" placeholder="filter by key / title…" oninput="f()"></header>
<div class="grid" id="g">{''.join(cards)}</div>
<script>
function f(){{var q=document.getElementById('q').value.toLowerCase(),n=0;
document.querySelectorAll('.card').forEach(function(c){{
var m=(c.dataset.k+' '+c.dataset.t).toLowerCase().indexOf(q)>=0;
c.style.display=m?'':'none';if(m)n++}});
document.getElementById('c').textContent=n}}
</script></body></html>"""
    out.write_text(doc, encoding="utf-8")
    have = sum(1 for k in index if (lib / prev / f"{k}.png").exists())
    print(f"gallery: {out}")
    print(f"cards: {len(index)}  thumbnails found: {have}/{len(index)} in {lib / prev}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
