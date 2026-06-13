"""Resolve ``data-native-diagram`` placeholders into spliced DrawingML.

This makes native-diagram components a first-class peer of ``<use data-icon>``
and ``<image>`` in the SVG -> DrawingML pipeline. The Executor draws a placeholder
rect in the SVG::

    <rect data-native-diagram="combo_product_system"
          x="140" y="120" width="1000" height="480" fill="none"/>

and at conversion time the named component's shapes (already DrawingML) are
spliced in, scaled to the placeholder rect.

Splicing is string-based (not ElementTree) so the component's namespace prefixes
(``a`` / ``p`` / ``r`` / ``a14`` / ``a16`` / …) stay byte-exact: the stored
``<a:diagram ...>`` wrapper — which carries every ``xmlns`` declaration — is
rewritten into a ``<p:grpSp ...>`` wrapper, keeping those declarations intact.

This module owns the core splice path (scale + media-remap + id-renumber). The
recolor / text-substitution / font-normalisation transforms layer on top via the
``data-recolor`` / ``data-text`` / ``data-font`` attributes.

See ``references/native-diagrams.md`` for the placeholder attribute contract.
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from pathlib import Path

from .drawingml_context import ConvertContext, ShapeResult
from .drawingml_utils import ctx_x, ctx_y, ctx_w, ctx_h, px_to_emu

LIB_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "native_diagrams"
IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"


def _f(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _renumber_cnvpr(xml: str, ctx: ConvertContext) -> str:
    """Reassign every ``<p:cNvPr id>`` from the slide's id allocator (unique)."""
    return re.sub(
        r'(<p:cNvPr id=")\d+(")',
        lambda m: f"{m.group(1)}{ctx.next_id()}{m.group(2)}",
        xml,
    )


def _remap_media(xml: str, comp_dir: Path, media_map: dict, ctx: ConvertContext) -> str:
    """Register each referenced bitmap on the slide and remap its ``r:embed``."""
    for old_rid, rel_path in media_map.items():
        fpath = comp_dir / rel_path
        if not fpath.exists():
            continue
        ext = fpath.suffix.lstrip(".").lower()
        if ext == "jpeg":
            ext = "jpg"
        fname = f"s{ctx.slide_num}_nd{len(ctx.media_files) + 1}.{ext}"
        ctx.media_files[fname] = fpath.read_bytes()
        new_rid = ctx.next_rel_id()
        ctx.rel_entries.append(
            {"id": new_rid, "type": IMAGE_REL, "target": f"../media/{fname}"}
        )
        xml = re.sub(r'(r:(?:embed|link)=")' + re.escape(old_rid) + r'(")',
                     r"\g<1>" + new_rid + r"\g<2>", xml)
    return xml


def resolve_native_diagram(elem, ctx: ConvertContext) -> ShapeResult | None:
    """Splice the referenced component, scaled into the placeholder rect."""
    from .drawingml_converter import SvgNativeConversionError

    key = elem.get("data-native-diagram")
    comp_dir = LIB_DIR / key
    # A key is authored, not user input — but a malformed value that escapes the
    # library directory must fail loudly, never read an arbitrary file.
    if not comp_dir.resolve().is_relative_to(LIB_DIR.resolve()):
        raise SvgNativeConversionError(
            f"data-native-diagram key escapes the library: {key!r} "
            f"(use a bare component name)"
        )
    gz, plain = comp_dir / "shapes.xml.gz", comp_dir / "shapes.xml"
    if gz.exists():
        xml = gzip.decompress(gz.read_bytes()).decode("utf-8")
    elif plain.exists():
        xml = plain.read_text(encoding="utf-8")
    else:
        raise SvgNativeConversionError(f"data-native-diagram: component not found: {key}")
    meta = json.loads((comp_dir / "meta.json").read_text(encoding="utf-8"))

    # Placeholder geometry -> EMU target rect (honours the context transform).
    x = ctx_x(_f(elem.get("x")), ctx)
    y = ctx_y(_f(elem.get("y")), ctx)
    w = ctx_w(_f(elem.get("width")), ctx)
    h = ctx_h(_f(elem.get("height")), ctx)
    if w <= 0 or h <= 0:
        print(
            f"Warning: data-native-diagram={key!r} skipped — zero placeholder size "
            f"(w={w}, h={h}); check the rect's width/height.",
            file=sys.stderr,
        )
        return None
    off_x, off_y = px_to_emu(x), px_to_emu(y)
    ext_cx, ext_cy = px_to_emu(w), px_to_emu(h)
    ch_cx, ch_cy = meta["canvas_emu"]

    xml = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", xml, count=1)
    if meta.get("media"):
        xml = _remap_media(xml, comp_dir, meta["media"], ctx)
    xml = _renumber_cnvpr(xml, ctx)

    # Rewrite <a:diagram ...> -> <p:grpSp ...> (keep its xmlns decls) + group props.
    m = re.match(r"<a:diagram\b([^>]*)>", xml)
    if not m:
        raise SvgNativeConversionError(f"data-native-diagram: malformed component {key}")
    ns_attrs = m.group(1)
    gid = ctx.next_id()
    props = (
        f'<p:nvGrpSpPr><p:cNvPr id="{gid}" name="NativeDiagram {gid}"/>'
        f"<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
        f'<p:grpSpPr><a:xfrm><a:off x="{off_x}" y="{off_y}"/>'
        f'<a:ext cx="{ext_cx}" cy="{ext_cy}"/>'
        f'<a:chOff x="0" y="0"/><a:chExt cx="{ch_cx}" cy="{ch_cy}"/></a:xfrm></p:grpSpPr>'
    )
    body = xml[m.end():].replace("</a:diagram>", "</p:grpSp>")
    return ShapeResult(
        xml=f"<p:grpSp{ns_attrs}>{props}{body}",
        bounds_emu=(off_x, off_y, off_x + ext_cx, off_y + ext_cy),
    )
