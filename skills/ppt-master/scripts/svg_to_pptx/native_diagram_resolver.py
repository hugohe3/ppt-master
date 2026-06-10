"""Resolve ``data-native-diagram`` placeholders into spliced DrawingML.

This makes native-diagram components a first-class peer of ``<use data-icon>``
and ``<image>`` in the SVG -> DrawingML pipeline. The Executor draws a placeholder
in the SVG::

    <rect data-native-diagram="combo_product_system"
          data-recolor="558C5A=0E7C7B,122B87=E8743B"
          data-font="Microsoft YaHei"
          x="140" y="120" width="1000" height="480" fill="none"/>

and at conversion time the named component's shapes (already DrawingML) are
spliced in, scaled to the placeholder rect, optionally recolored, and (with
``data-font``) re-fonted to the deck typeface. Always set ``data-font`` to the
deck's font: components keep the source deck's fonts, and most runs inherit the
slide theme rather than naming a typeface — so without it the figure's text
renders in a different font than the surrounding SVG-authored text.

Splicing is string-based (not ElementTree) so the component's namespace prefixes
(``a`` / ``p`` / ``r`` / ``a14`` / ``a16`` / …) stay byte-exact: the stored
``<a:diagram ...>`` wrapper — which carries every ``xmlns`` declaration — is
rewritten into a ``<p:grpSp ...>`` wrapper, keeping those declarations intact.
"""
from __future__ import annotations

import gzip
import html
import json
import re
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


def _parse_recolor(spec: str | None) -> dict:
    """``"558C5A=0E7C7B,122B87=E8743B"`` -> ``{"558C5A": "0E7C7B", ...}``."""
    out: dict[str, str] = {}
    for pair in (spec or "").split(","):
        if "=" in pair:
            old, new = pair.split("=", 1)
            out[old.strip().lstrip("#").upper()] = new.strip().lstrip("#").upper()
    return out


def _apply_recolor(xml: str, cmap: dict) -> str:
    for old, new in cmap.items():
        xml = re.sub(
            r'(<a:srgbClr val=")' + re.escape(old) + r'(")',
            lambda m: m.group(1) + new + m.group(2),
            xml, flags=re.IGNORECASE,
        )
    return xml


_AT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.DOTALL)


def _apply_text_fills(xml: str, data_text: str | None) -> str:
    """Replace the diagram's text runs with deck content.

    ``data-text`` is a JSON object ``{"<slot_id>": "<new text>"}`` where slot id
    is the run's index in document order — the same indexing ``extract`` records
    in ``meta.text_slots``. Slots not provided keep their original (source) text.
    """
    if not data_text:
        return xml
    try:
        fills = json.loads(data_text)
    except (ValueError, TypeError):
        return xml
    if not fills:
        return xml
    counter = [-1]

    def repl(m):
        counter[0] += 1
        new = fills.get(str(counter[0]))
        if new is None:
            return m.group(0)
        return "<a:t>%s</a:t>" % html.escape(str(new), quote=False)

    return _AT_RE.sub(repl, xml)


_RPR_RE = re.compile(
    r'<a:(rPr|defRPr|endParaRPr)\b((?:[^>"]|"[^"]*")*?)(?:/>|>(.*?)</a:\1>)',
    re.DOTALL,
)
_FONT_CHILD_RE = re.compile(r"<a:(?:latin|ea|cs)\b[^>]*/>")


def _apply_font(xml: str, font: str | None) -> str:
    """Force the deck font onto every run in the spliced component.

    Native-diagram components carry the source deck's fonts: a few runs name a
    typeface explicitly, but most carry none and inherit the slide theme's font
    — which is not the deck font, so the figure's text looks different from the
    surrounding SVG-authored text. ``data-font`` normalises all of them: existing
    ``latin``/``ea``/``cs`` are replaced and missing ones are injected so every run
    (and ``endParaRPr``/``defRPr``) renders in the deck's typeface.
    """
    if not font:
        return xml
    fonts = (
        f'<a:latin typeface="{font}"/>'
        f'<a:ea typeface="{font}"/>'
        f'<a:cs typeface="{font}"/>'
    )

    def repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        inner = "" if inner is None else _FONT_CHILD_RE.sub("", inner)
        return f"<a:{tag}{attrs}>{inner}{fonts}</a:{tag}>"

    xml = _RPR_RE.sub(repl, xml)
    # Runs that carry text but no run-properties at all get a fresh rPr.
    xml = re.sub(r"<a:r>(\s*)<a:t>", rf"<a:r><a:rPr>{fonts}</a:rPr>\1<a:t>", xml)
    return xml


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
        return None
    off_x, off_y = px_to_emu(x), px_to_emu(y)
    ext_cx, ext_cy = px_to_emu(w), px_to_emu(h)
    ch_cx, ch_cy = meta["canvas_emu"]

    xml = re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", xml, count=1)
    xml = _apply_recolor(xml, _parse_recolor(elem.get("data-recolor")))
    xml = _apply_text_fills(xml, elem.get("data-text"))
    xml = _apply_font(xml, elem.get("data-font"))
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
