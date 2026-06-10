#!/usr/bin/env python3
"""Batch-extract every slide of a .pptx into the native-diagram library.

Use this to bulk-import a whole diagram pack ("extract all now, curate later").
Each slide becomes a ``templates/native_diagrams/<prefix>_<NNN>/`` component and
gets an entry in ``diagrams_index.json`` whose ``summary`` seeds from the slide's
largest-font text. The run is resilient: a slide that fails to lift is recorded
and skipped, never aborting the batch.

Usage::

    python3 scripts/scan_pack.py <source.pptx> \
        [-o skills/ppt-master/templates/native_diagrams] [--prefix <slug>] [--limit N]

Curate afterwards by deleting unwanted ``<key>/`` dirs and their index entries
(or re-run ``register`` style by hand). A preview per slide can be rendered
separately; this tool only does the lift + index.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from native_diagrams import extract_diagram


def _slug(text: str) -> str:
    s = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower()
    return s or "deck"


def _slide_numbers(zf: zipfile.ZipFile) -> list[int]:
    nums = []
    for name in zf.namelist():
        m = re.match(r"ppt/slides/slide(\d+)\.xml$", name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch-extract a .pptx into the native-diagram library.")
    ap.add_argument("source", help="Source .pptx pack")
    ap.add_argument("-o", "--output", default="skills/ppt-master/templates/native_diagrams",
                    help="Library root (default: skills/ppt-master/templates/native_diagrams)")
    ap.add_argument("--prefix", help="Key prefix (default: slug of the .pptx stem)")
    ap.add_argument("--limit", type=int, help="Only the first N slides (debug)")
    args = ap.parse_args()

    src = Path(args.source)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or _slug(src.stem)

    with zipfile.ZipFile(src) as zf:
        slide_nums = _slide_numbers(zf)
    if args.limit:
        slide_nums = slide_nums[: args.limit]

    index_path = out_root / "diagrams_index.json"
    raw = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    # Read/write the new {meta, diagrams} shape; tolerate (and upgrade) a legacy
    # flat index. Writing flat here would corrupt a curated {meta, diagrams} file.
    meta_block = raw.get("meta") if isinstance(raw, dict) else None
    index = raw.get("diagrams", raw) if isinstance(raw, dict) else {}

    ok = fail = with_media = with_charts = 0
    failures: list[tuple[int, str]] = []
    for n in slide_nums:
        key = f"{prefix}_{n:03d}"
        try:
            meta = extract_diagram(src, n, out_root / key, key=key)
        except Exception as exc:  # keep the batch going
            fail += 1
            failures.append((n, f"{type(exc).__name__}: {exc}"))
            continue
        index[key] = {
            "summary": meta.get("title") or f"(slide {n})",
            "source": meta["source"],
            "slide": n,
            "shapes": meta["shape_count"],
            "media": len(meta["media"]),
            "charts": len(meta["charts_unsupported"]),
        }
        ok += 1
        with_media += bool(meta["media"])
        with_charts += bool(meta["charts_unsupported"])

    index = {k: index[k] for k in sorted(index)}
    out: dict = {}
    if meta_block is not None:
        out["meta"] = meta_block
    out["diagrams"] = index
    index_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print()
    print("## Pack Scan Complete")
    print()
    print(f"**Source**: {src.name}  ({len(slide_nums)} slides)")
    print(f"**Extracted**: {ok}   **Failed**: {fail}")
    print(f"**With media**: {with_media}   **With charts (partial lift)**: {with_charts}")
    print(f"**Library**: {out_root}  ({len(index)} total entries)")
    if failures:
        print()
        print("### Failures")
        for n, msg in failures[:30]:
            print(f"- slide {n}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
