import os
import sys
import re
import argparse
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
NSMAP = {"svg": SVG_NS}

# Ensure pretty element names without ns0 prefix on write
ET.register_namespace("", SVG_NS)


TEXT_STYLE_ATTRS = {
    # common text styling
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "font-variant",
    "font-stretch",
    "letter-spacing",
    "word-spacing",
    "kerning",
    "text-anchor",
    "text-decoration",
    "dominant-baseline",
    "writing-mode",
    "direction",
    # color/paint
    "fill",
    "fill-opacity",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "opacity",
    "paint-order",
    # transforms/filters
    "transform",
    "clip-path",
    "filter",
}


num_re = re.compile(r"^[\s,]*([+-]?(?:\d+\.?\d*|\d*\.\d+))")


def parse_first_number(val: str):
    if val is None:
        return None
    m = num_re.match(val)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def format_number(n: float) -> str:
    if n is None:
        return None
    if abs(n - round(n)) < 1e-6:
        return str(int(round(n)))
    # Trim trailing zeros
    s = f"{n:.6f}".rstrip("0").rstrip(".")
    return s


def parse_style(style_str: str) -> dict:
    out = {}
    if not style_str:
        return out
    # split by ; and then :
    for chunk in style_str.split(";"):
        if not chunk.strip():
            continue
        if ":" in chunk:
            k, v = chunk.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def style_to_string(style_map: dict) -> str:
    if not style_map:
        return ""
    return ";".join(f"{k}:{v}" for k, v in style_map.items())


def merge_styles(parent_style: str, child_style: str) -> str:
    p = parse_style(parent_style)
    c = parse_style(child_style)
    p.update(c)  # child overrides
    return style_to_string(p)


def get_attr(elem, name, default=None):
    return elem.get(name) if elem is not None and name in elem.attrib else default


def compute_line_positions(text_el, tspan_el, cur_x, cur_y):
    """
    Compute absolute x,y for a tspan based on parent <text> current baseline and tspan's x/y/dx/dy.
    Returns (new_x, new_y).
    """
    # Prefer explicit x/y on tspan
    t_x_attr = get_attr(tspan_el, "x")
    t_y_attr = get_attr(tspan_el, "y")
    t_dx_attr = get_attr(tspan_el, "dx")
    t_dy_attr = get_attr(tspan_el, "dy")

    if t_x_attr is not None:
        nx = parse_first_number(t_x_attr)
    elif t_dx_attr is not None:
        dx = parse_first_number(t_dx_attr) or 0.0
        nx = (cur_x or 0.0) + dx
    else:
        nx = cur_x

    if t_y_attr is not None:
        ny = parse_first_number(t_y_attr)
    elif t_dy_attr is not None:
        dy = parse_first_number(t_dy_attr) or 0.0
        ny = (cur_y or 0.0) + dy
    else:
        ny = cur_y

    return nx, ny


def collect_text_content(el) -> str:
    # Gather all text within the element (flatten nested tspans if any)
    parts = []
    for s in el.itertext():
        if s:
            parts.append(s)
    return "".join(parts)


def copy_text_attrs(src_el, dst_el, exclude=None):
    exclude = exclude or set()
    # Copy style string first
    if "style" in src_el.attrib and "style" not in exclude:
        dst_el.set("style", src_el.attrib["style"])
    for k in TEXT_STYLE_ATTRS:
        if k in exclude:
            continue
        v = src_el.get(k)
        if v is not None:
            dst_el.set(k, v)
    # xml:space preservation
    xml_space = src_el.get("{http://www.w3.org/XML/1998/namespace}space")
    if xml_space is not None and "{http://www.w3.org/XML/1998/namespace}space" not in exclude:
        dst_el.set("{http://www.w3.org/XML/1998/namespace}space", xml_space)


def flatten_text_with_tspans(tree: ET.ElementTree) -> bool:
    root = tree.getroot()
    parent_map = {c: p for p in root.iter() for c in p}
    changed = False

    def is_svg_tag(el, name):
        return el.tag == f"{{{SVG_NS}}}{name}"

    # Collect candidates first to avoid modifying while iterating
    candidates = []
    for el in root.iter():
        if is_svg_tag(el, "text"):
            has_tspan_child = any(is_svg_tag(c, "tspan") for c in list(el))
            if has_tspan_child:
                candidates.append(el)

    for text_el in candidates:
        parent = parent_map.get(text_el)
        if parent is None:
            continue

        base_x = parse_first_number(get_attr(text_el, "x")) or 0.0
        base_y = parse_first_number(get_attr(text_el, "y")) or 0.0
        cur_x, cur_y = base_x, base_y

        new_texts = []

        # Leading text directly under <text>
        lead_text = (text_el.text or "").strip("\n")
        if lead_text:
            ne = ET.Element(f"{{{SVG_NS}}}text")
            # Copy attrs from parent <text>
            copy_text_attrs(text_el, ne, exclude={"x", "y"})
            ne.set("x", format_number(cur_x))
            ne.set("y", format_number(cur_y))
            ne.text = lead_text
            new_texts.append(ne)

        for child in list(text_el):
            if not is_svg_tag(child, "tspan"):
                # We do not attempt to convert other child types
                continue

            content = collect_text_content(child)
            if content.strip() == "":
                # skip empty lines but still update position if dy present
                nx, ny = compute_line_positions(text_el, child, cur_x, cur_y)
                cur_x, cur_y = nx, ny
                continue

            nx, ny = compute_line_positions(text_el, child, cur_x, cur_y)

            ne = ET.Element(f"{{{SVG_NS}}}text")

            # Start by copying parent's attributes
            copy_text_attrs(text_el, ne, exclude={"x", "y"})

            # Merge style with tspan's style
            merged_style = merge_styles(text_el.get("style"), child.get("style"))
            if merged_style:
                ne.set("style", merged_style)

            # Override specific attributes from tspan if present
            for attr in TEXT_STYLE_ATTRS:
                cv = child.get(attr)
                if cv is not None:
                    ne.set(attr, cv)

            # Positioning
            if nx is not None:
                ne.set("x", format_number(nx))
            if ny is not None:
                ne.set("y", format_number(ny))

            # Transform: combine if child also has it
            p_tf = text_el.get("transform")
            c_tf = child.get("transform")
            if p_tf and c_tf:
                ne.set("transform", f"{p_tf} {c_tf}")
            elif p_tf:
                ne.set("transform", p_tf)
            elif c_tf:
                ne.set("transform", c_tf)

            ne.text = content
            new_texts.append(ne)

            # Update current baseline for subsequent tspans
            cur_x, cur_y = nx, ny

        if new_texts:
            # Replace original <text> with the list of new <text> nodes
            try:
                idx = list(parent).index(text_el)
            except ValueError:
                # Shouldn't happen, but guard anyway
                idx = None

            # Insert in place to preserve drawing order
            for i, ne in enumerate(new_texts):
                if idx is not None:
                    parent.insert(idx + i, ne)
                else:
                    parent.append(ne)

            # Remove the original <text>
            parent.remove(text_el)
            changed = True

    return changed


def process_svg_file(src_path: str, dst_path: str) -> bool:
    try:
        tree = ET.parse(src_path)
    except ET.ParseError as e:
        print(f"[WARN] Failed to parse {src_path}: {e}")
        return False

    changed = flatten_text_with_tspans(tree)

    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    # Write out XML without XML declaration to mimic input style
    tree.write(dst_path, encoding="utf-8", xml_declaration=False, method="xml")
    return changed


def _compute_default_out_base(inp: str) -> str:
    """Compute default output path for directory or file input."""
    if os.path.isdir(inp):
        # Default: if input ends with svg_output, use sibling svg_output_flattext;
        # otherwise append _flattext to the directory name at the same level.
        head, tail = os.path.split(os.path.normpath(inp))
        if tail == "svg_output":
            return os.path.join(head, "svg_output_flattext")
        return inp.rstrip("/\\") + "_flattext"
    else:
        base, ext = os.path.splitext(inp)
        return base + "_flattext" + ext


def _interactive_get_paths():
    """
    Interactive mode: prompt the user for input path (SVG file or directory)
    and optional output path. Returns (inp, out_base) or (None, None) if cancelled.
    """
    print("[交互模式] 未提供参数，将以交互方式运行。")
    print("请输入需要处理的路径（SVG 文件或包含 SVG 的目录）。")
    print("输入 q 回车可退出。\n")

    while True:
        raw = input("输入路径 (file/dir): ").strip()
        if raw.lower() in {"q", "quit", "exit"} or raw == "":
            return None, None
        inp = os.path.expanduser(raw)
        if os.path.exists(inp):
            break
        print("路径不存在，请重新输入或输入 q 退出。")

    default_out = _compute_default_out_base(inp)
    if os.path.isdir(inp):
        prompt = f"输出目录 [默认: {default_out}]: "
    else:
        prompt = f"输出文件 [默认: {default_out}]: "

    raw_out = input(prompt).strip()
    out_base = os.path.expanduser(raw_out) if raw_out else default_out

    return inp, out_base


def main():
    # CLI parsing with optional interactive mode
    parser = argparse.ArgumentParser(
        description="Flatten <tspan> lines into multiple <text> nodes for better compatibility.",
        add_help=True,
    )
    parser.add_argument("input", nargs="?", help="Input path: SVG file or directory")
    parser.add_argument("output", nargs="?", help="Optional output file/dir")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run in interactive prompt mode to input paths",
    )

    args = parser.parse_args()

    if args.interactive or not args.input:
        inp, out_base = _interactive_get_paths()
        if not inp:
            print("已取消。用法: python tools/flatten_tspan.py <input_dir_or_svg> [output_dir]")
            sys.exit(0)
    else:
        inp = args.input
        out_base = args.output

    if os.path.isdir(inp):
        # If output base not provided, create a sibling folder named svg_output_flattext for svg_output
        if out_base is None:
            out_base = _compute_default_out_base(inp)

        total = 0
        changed_count = 0
        out_base_abs = os.path.abspath(out_base)
        for root, dirs, files in os.walk(inp):
            # Avoid recursing into the output directory when it lives under input
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != out_base_abs]
            rel_root = os.path.relpath(root, inp)
            for f in files:
                if not f.lower().endswith(".svg"):
                    continue
                src = os.path.join(root, f)
                dst = os.path.join(out_base, rel_root, f) if rel_root != "." else os.path.join(out_base, f)
                total += 1
                changed = process_svg_file(src, dst)
                if changed:
                    changed_count += 1
        print(f"Processed {total} SVG(s). With <tspan> flattened: {changed_count}.")
        print(f"Output written to: {out_base}")
    else:
        src = inp
        if out_base is None:
            out_base = _compute_default_out_base(src)
        changed = process_svg_file(src, out_base)
        print(f"Written: {out_base} (flattened: {changed})")


if __name__ == "__main__":
    main()
