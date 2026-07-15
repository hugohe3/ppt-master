#!/usr/bin/env python3
"""
PPT Master - Large Vector Asset Extractor

Factor large inline vector groups (complex illustrations) out of working SVGs
into project icon assets, leaving a one-line `<use data-icon="id"/>`
placeholder behind — so the working SVG stays readable (structure, not a wall of
`<path>`). Visually lossless and reversible: the existing icon embedding path
re-inlines each asset before export, so the exported PPTX remains native shapes,
not an embedded picture.

Because re-inlining restores the extracted vector subtree, the detection
threshold is a readability convenience — it changes which blobs are factored
out, not whether the export stays editable.

Usage:
    python3 scripts/extract_svg_assets.py <svg_dir> [options]

Examples:
    python3 scripts/extract_svg_assets.py import_ws/svg \
        --icons-dir import_ws/icons --inplace --id-prefix layered --clean-stale
    python3 scripts/extract_svg_assets.py import_ws/svg-flat \
        --icons-dir import_ws/icons \
        --reuse-inventory import_ws/svg_vector_asset_inventory.json \
        --inplace --id-prefix flat --clean-stale
    python3 scripts/extract_svg_assets.py project/svg_output --inplace --min-drawables 40

Dependencies:
    None (standard library only).

See workflows/create-template.md and svg_finalize/embed_icons.py.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
DRAWABLE = {"path", "polygon", "polyline", "rect", "circle", "ellipse", "line"}
SEMANTIC_CONTENT = {"text", "tspan", "foreignObject"}
DEFAULT_MIN_DRAWABLES = 20
DEFAULT_MIN_BYTES = 3000
DEFAULT_MIN_DECORATION_BYTES = 3000
URL_REF_RE = re.compile(r"url\(\s*(['\"]?)#([^)'\"]\S*?)\1\s*\)")


def _local(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _drawable_count(elem: ET.Element) -> int:
    return sum(1 for e in elem.iter() if _local(e.tag) in DRAWABLE)


def _xml_size(elem: ET.Element) -> int:
    return len(ET.tostring(elem, encoding="utf-8"))


def _large_enough(elem: ET.Element, min_drawables: int, min_bytes: int) -> bool:
    return _drawable_count(elem) >= min_drawables or _xml_size(elem) >= min_bytes


def _has_semantic_content(elem: ET.Element) -> bool:
    """Text-bearing groups must stay readable/editable in the working SVG."""
    return any(_local(e.tag) in SEMANTIC_CONTENT for e in elem.iter())


def _is_existing_placeholder(elem: ET.Element) -> bool:
    return _local(elem.tag) == "use" and elem.get("data-icon") is not None


def _is_extractable_subtree(elem: ET.Element) -> bool:
    """Pure vector subtrees can be moved; semantic content must stay inline."""
    if _is_existing_placeholder(elem) or _is_chart_group(elem) or _has_semantic_content(elem):
        return False
    return _drawable_count(elem) > 0


def _is_chart_group(elem: ET.Element) -> bool:
    """Charts are handled separately (data + calibration) — never extract them."""
    gid = (elem.get("id") or "").lower()
    if "chart" in gid:
        return True
    return any("chart" in (e.get("id") or "").lower() for e in elem.iter())


def _tag_histogram(elem: ET.Element) -> dict[str, int]:
    hist: dict[str, int] = {}
    for e in elem.iter():
        name = _local(e.tag)
        if name in DRAWABLE:
            hist[name] = hist.get(name, 0) + 1
    return hist


def _is_descendant(container: ET.Element, candidate: ET.Element) -> bool:
    return any(elem is candidate for elem in container.iter())


def _id_index(root: ET.Element) -> dict[str, ET.Element]:
    return {elem_id: elem for elem in root.iter() if (elem_id := elem.get("id"))}


def _referenced_ids(elem: ET.Element) -> set[str]:
    refs: set[str] = set()
    for item in elem.iter():
        for attr_name, value in item.attrib.items():
            refs.update(match.group(2) for match in URL_REF_RE.finditer(value))
            if _local(attr_name) == "href" and value.startswith("#") and len(value) > 1:
                refs.add(value[1:])
    return refs


def _dependency_elements(root: ET.Element, asset_group: ET.Element) -> list[ET.Element]:
    """
    Return external definition elements referenced by the extracted subtree.

    Gradients, patterns, filters, clip paths, and markers often live in the
    source SVG root <defs>. The extracted asset must carry these dependencies
    itself; otherwise the standalone icon and later re-inline can lose styling.
    """
    by_id = _id_index(root)
    dependencies: list[ET.Element] = []
    seen: set[str] = set()
    queue = sorted(_referenced_ids(asset_group))

    while queue:
        ref_id = queue.pop(0)
        if ref_id in seen:
            continue
        seen.add(ref_id)

        target = by_id.get(ref_id)
        if target is None or _is_descendant(asset_group, target):
            continue

        dependencies.append(target)
        for nested_ref in sorted(_referenced_ids(target)):
            if nested_ref not in seen:
                queue.append(nested_ref)

    return dependencies


def _collect_id_mapping(asset_id: str, group: ET.Element, dependencies: list[ET.Element]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for root in [group, *dependencies]:
        for elem in root.iter():
            elem_id = elem.get("id")
            if elem_id and elem_id not in mapping:
                mapping[elem_id] = f"{asset_id}_{elem_id}"
    return mapping


def _rewrite_references(elem: ET.Element, id_mapping: dict[str, str]) -> None:
    def rewrite_url(match: re.Match[str]) -> str:
        quote, ref_id = match.group(1), match.group(2)
        new_id = id_mapping.get(ref_id, ref_id)
        return f"url({quote}#{new_id}{quote})"

    for item in elem.iter():
        elem_id = item.get("id")
        if elem_id in id_mapping:
            item.set("id", id_mapping[elem_id])

        for attr_name, value in list(item.attrib.items()):
            rewritten = URL_REF_RE.sub(rewrite_url, value)
            if _local(attr_name) == "href" and value.startswith("#") and value[1:] in id_mapping:
                rewritten = f"#{id_mapping[value[1:]]}"
            if rewritten != value:
                item.set(attr_name, rewritten)


def _find_extractable(root: ET.Element, min_drawables: int, min_bytes: int) -> list[ET.Element]:
    """Outermost <g> groups whose drawable count clears the threshold (no nesting)."""
    found: list[ET.Element] = []

    def walk(elem: ET.Element) -> None:
        for child in list(elem):
            if _local(child.tag) != "g":
                walk(child)
                continue
            if (
                not _is_chart_group(child)
                and not _has_semantic_content(child)
                and child.get("data-icon") is None
                and _large_enough(child, min_drawables, min_bytes)
            ):
                found.append(child)  # outermost qualifying — do not descend
            else:
                walk(child)

    walk(root)
    return found


def _find_extractable_runs(
    root: ET.Element,
    min_drawables: int,
    min_bytes: int,
    min_decoration_bytes: int,
) -> list[tuple[ET.Element, list[ET.Element]]]:
    """
    Consecutive pure-vector children inside mixed groups.

    PPT exports often flatten text and large vector decorations as siblings
    under the same parent. Whole-group extraction would hide text, so only the
    contiguous vector runs are factored out.
    """
    found: list[tuple[ET.Element, list[ET.Element]]] = []

    def flush(parent: ET.Element, run: list[ET.Element]) -> None:
        byte_threshold = min_decoration_bytes if _has_semantic_content(parent) else min_bytes
        if run and (
            sum(_drawable_count(child) for child in run) >= min_drawables
            or sum(_xml_size(child) for child in run) >= byte_threshold
        ):
            found.append((parent, list(run)))

    def walk(elem: ET.Element) -> None:
        run: list[ET.Element] = []
        for child in list(elem):
            if _is_extractable_subtree(child):
                run.append(child)
                continue
            flush(elem, run)
            run = []
            walk(child)
        flush(elem, run)

    walk(root)
    return found


def _asset_svg(
    group: ET.Element,
    dependencies: list[ET.Element],
    view_box: str | None,
    width: str | None,
    height: str | None,
) -> bytes:
    """Standalone, independently-viewable SVG carrying the group in page coords."""
    svg = ET.Element(f"{{{SVG_NS}}}svg")
    svg.set("data-icon-style", "preserve-color")
    if view_box:
        svg.set("viewBox", view_box)
    if width:
        svg.set("width", width)
    if height:
        svg.set("height", height)
    if dependencies:
        defs = ET.SubElement(svg, f"{{{SVG_NS}}}defs")
        for dependency in dependencies:
            defs.append(dependency)
    svg.append(group)
    return ET.tostring(svg, encoding="utf-8", xml_declaration=True)


def _source_sha256(
    group: ET.Element,
    dependencies: list[ET.Element],
    view_box: str | None,
    width: str | None,
    height: str | None,
) -> str:
    """Fingerprint an extracted subtree before asset-id namespacing."""
    payload = _asset_svg(
        copy.deepcopy(group),
        [copy.deepcopy(dependency) for dependency in dependencies],
        view_box,
        width,
        height,
    )
    return hashlib.sha256(payload).hexdigest()


def _asset_group(nodes: list[ET.Element]) -> ET.Element:
    group = ET.Element(f"{{{SVG_NS}}}g")
    for node in nodes:
        group.append(node)
    return group


def _asset_id(svg_path: Path, index: int, id_prefix: str) -> str:
    prefix = f"{id_prefix}_" if id_prefix else ""
    return f"{prefix}{svg_path.stem}_ill{index:02d}"


def _generated_asset_re(svg_stems: list[str], id_prefix: str) -> re.Pattern[str] | None:
    if not svg_stems:
        return None
    prefix = f"{re.escape(id_prefix)}_" if id_prefix else ""
    stems = "|".join(re.escape(stem) for stem in svg_stems)
    return re.compile(rf"^{prefix}(?:{stems})_ill\d+\.svg$")


def _clean_stale_assets(icons_dir: Path, svg_paths: list[Path], id_prefix: str, keep_assets: set[str]) -> list[str]:
    pattern = _generated_asset_re([path.stem for path in svg_paths], id_prefix)
    if pattern is None:
        return []

    removed: list[str] = []
    for asset_path in sorted(icons_dir.glob("*.svg")):
        if asset_path.name in keep_assets or not pattern.match(asset_path.name):
            continue
        asset_path.unlink()
        removed.append(asset_path.name)
    return removed


def _referenced_icon_assets(svg_paths: list[Path]) -> set[str]:
    assets: set[str] = set()
    for svg_path in svg_paths:
        try:
            root = ET.parse(svg_path).getroot()
        except ET.ParseError:
            continue
        for elem in root.iter():
            if _local(elem.tag) != "use":
                continue
            icon_name = elem.get("data-icon")
            if icon_name and "/" not in icon_name:
                assets.add(f"{icon_name}.svg")
    return assets


def _existing_placeholder_entries(
    svg_paths: list[Path],
    icons_dir: Path,
    known_assets: set[str],
) -> list[dict]:
    by_asset: dict[str, dict] = {}
    for svg_path in svg_paths:
        try:
            root = ET.parse(svg_path).getroot()
        except ET.ParseError:
            continue

        for elem in root.iter():
            if _local(elem.tag) != "use":
                continue
            icon_name = elem.get("data-icon")
            if not icon_name or "/" in icon_name:
                continue

            asset = f"{icon_name}.svg"
            if asset in known_assets:
                continue

            entry = by_asset.setdefault(
                asset,
                {
                    "svg": svg_path.name,
                    "svgs": [],
                    "id": icon_name,
                    "icon": icon_name,
                    "asset": asset,
                    "source": "existing-placeholder",
                    "asset_exists": (icons_dir / asset).exists(),
                },
            )
            if svg_path.name not in entry["svgs"]:
                entry["svgs"].append(svg_path.name)

    entries: list[dict] = []
    for asset, entry in sorted(by_asset.items()):
        asset_path = icons_dir / asset
        if asset_path.exists():
            try:
                root = ET.parse(asset_path).getroot()
            except ET.ParseError:
                pass
            else:
                entry["drawable_count"] = _drawable_count(root)
                entry["byte_count"] = _xml_size(root)
                entry["elements"] = _tag_histogram(root)
                entry["dependencies"] = sorted(
                    elem_id
                    for elem in root.iter()
                    if _local(elem.tag) == "defs"
                    for child in elem
                    if (elem_id := child.get("id"))
                )
        entries.append(entry)
    return entries


def _load_reusable_assets(inventory_path: Path, icons_dir: Path) -> dict[str, dict]:
    """Load fingerprinted assets from an earlier extraction inventory."""
    try:
        payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"reuse inventory not found: {inventory_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid reuse inventory JSON: {inventory_path}: {exc}") from exc

    entries = payload.get("assets")
    if not isinstance(entries, list):
        raise ValueError(f"reuse inventory has no assets list: {inventory_path}")

    reusable: dict[str, dict] = {}
    fingerprinted = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        source_sha256 = entry.get("source_sha256")
        asset_sha256 = entry.get("asset_sha256")
        asset = entry.get("asset")
        icon = entry.get("icon")
        if not all(
            isinstance(value, str) and value
            for value in (source_sha256, asset_sha256, asset, icon)
        ):
            continue
        fingerprinted += 1
        asset_path = icons_dir / asset
        if not asset_path.is_file():
            raise ValueError(
                f"reusable asset is missing from the target icons directory: {asset_path}"
            )
        actual_asset_sha256 = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if actual_asset_sha256 != asset_sha256:
            raise ValueError(
                f"reusable asset hash does not match its inventory: {asset_path}"
            )
        current = reusable.get(source_sha256)
        if current is None or asset < str(current["asset"]):
            reusable[source_sha256] = entry

    extracted_count = payload.get("extracted_count", 0)
    if isinstance(extracted_count, int) and extracted_count > fingerprinted:
        raise ValueError(
            "reuse inventory predates source fingerprints; rerun the source extraction "
            f"with the current tool: {inventory_path}"
        )
    return reusable


def _rewritten_path(svg_path: Path, rewritten_dir: Path | None, inplace: bool) -> Path:
    if inplace:
        return svg_path
    if rewritten_dir is None:
        return svg_path.parent.parent / f"{svg_path.parent.name}-rewritten" / svg_path.name
    return rewritten_dir / svg_path.name


def extract_file(
    svg_path: Path,
    icons_dir: Path,
    min_drawables: int,
    min_bytes: int,
    min_decoration_bytes: int,
    inplace: bool,
    id_prefix: str = "",
    rewritten_dir: Path | None = None,
    reusable_assets: dict[str, dict] | None = None,
) -> list[dict]:
    """Extract qualifying groups from one SVG. Returns inventory entries."""
    ET.register_namespace("", SVG_NS)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    view_box = root.get("viewBox")
    width = root.get("width")
    height = root.get("height")

    targets: list[tuple[ET.Element, list[ET.Element]]] = []
    parents = {child: parent for parent in root.iter() for child in parent}
    group_targets = _find_extractable(root, min_drawables, min_bytes)
    selected_groups = set(group_targets)

    def inside_selected_group(elem: ET.Element) -> bool:
        current = elem
        while current in parents:
            current = parents[current]
            if current in selected_groups:
                return True
        return False

    for group in group_targets:
        parent = parents.get(group)
        if parent is not None:
            targets.append((parent, [group]))

    for parent, run in _find_extractable_runs(root, min_drawables, min_bytes, min_decoration_bytes):
        if (
            parent not in selected_groups
            and not inside_selected_group(parent)
            and not any(child in selected_groups for child in run)
            and all(child in parent for child in run)
        ):
            targets.append((parent, run))

    if not targets:
        if not inplace:
            rewritten = _rewritten_path(svg_path, rewritten_dir, inplace)
            rewritten.parent.mkdir(parents=True, exist_ok=True)
            tree.write(rewritten, encoding="utf-8", xml_declaration=True)
        return []

    icons_dir.mkdir(parents=True, exist_ok=True)
    entries = []

    for index, (parent, nodes) in enumerate(targets, start=1):
        if not nodes or not all(node in parent for node in nodes):
            continue
        asset_id = _asset_id(svg_path, index, id_prefix)
        pos = list(parent).index(nodes[0])
        group = nodes[0] if len(nodes) == 1 and _local(nodes[0].tag) == "g" else _asset_group(nodes)

        dependencies = [copy.deepcopy(elem) for elem in _dependency_elements(root, group)]
        dependency_source_ids = sorted({
            elem_id
            for dependency in dependencies
            for elem in dependency.iter()
            if (elem_id := elem.get("id"))
        })
        source_sha256 = _source_sha256(group, dependencies, view_box, width, height)
        reusable = (reusable_assets or {}).get(source_sha256)
        if reusable is not None:
            reused_icon = str(reusable["icon"])
            reused_asset = str(reusable["asset"])
            placeholder = ET.Element(f"{{{SVG_NS}}}use")
            placeholder.set("data-icon", reused_icon)
            for node in nodes:
                if node in parent:
                    parent.remove(node)
            parent.insert(pos, placeholder)
            entries.append({
                "svg": svg_path.name,
                "id": reused_icon,
                "icon": reused_icon,
                "asset": reused_asset,
                "source": "reused-inventory",
                "source_sha256": source_sha256,
                "asset_sha256": reusable["asset_sha256"],
                "reused_from_svg": reusable.get("svg"),
                "drawable_count": _drawable_count(group),
                "byte_count": _xml_size(group),
                "dependencies": dependency_source_ids,
                "elements": _tag_histogram(group),
            })
            continue

        id_mapping = _collect_id_mapping(asset_id, group, dependencies)
        _rewrite_references(group, id_mapping)
        for dependency in dependencies:
            _rewrite_references(dependency, id_mapping)

        # Asset keeps the group in original page coordinates and carries its defs.
        asset_bytes = _asset_svg(group, dependencies, view_box, width, height)
        (icons_dir / f"{asset_id}.svg").write_bytes(asset_bytes)

        placeholder = ET.Element(f"{{{SVG_NS}}}use")
        placeholder.set("data-icon", asset_id)
        for node in nodes:
            if node in parent:
                parent.remove(node)
        parent.insert(pos, placeholder)

        entries.append({
            "svg": svg_path.name,
            "id": asset_id,
            "icon": asset_id,
            "asset": f"{asset_id}.svg",
            "source": "extracted",
            "source_sha256": source_sha256,
            "asset_sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "drawable_count": _drawable_count(group),
            "byte_count": _xml_size(group),
            "dependencies": [id_mapping.get(elem_id, elem_id) for elem_id in dependency_source_ids],
            "elements": _tag_histogram(group),
        })

    rewritten = _rewritten_path(svg_path, rewritten_dir, inplace)
    rewritten.parent.mkdir(parents=True, exist_ok=True)
    tree.write(rewritten, encoding="utf-8", xml_declaration=True)
    return entries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Factor large inline vector groups out of SVGs into reusable assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("svg_dir", help="Directory of working SVGs (e.g. import_ws/svg or project/svg_output)")
    parser.add_argument("-o", "--output", dest="icons_dir", help="Project icon dir (default: <svg_dir>/../icons)")
    parser.add_argument("--icons-dir", dest="icons_dir", help="Project icon dir (default: <svg_dir>/../icons)")
    parser.add_argument(
        "--rewritten-dir",
        help="Directory for rewritten SVGs when not using --inplace (default: <svg_dir>/../<svg_dir-name>-rewritten)",
    )
    parser.add_argument(
        "--inventory",
        help="Inventory JSON path (default: <svg_dir>/../<svg_dir-name>_vector_asset_inventory.json)",
    )
    parser.add_argument(
        "--reuse-inventory",
        help=(
            "Reuse fingerprint-matched assets from an earlier extraction inventory; "
            "only unmatched vector subtrees create new assets"
        ),
    )
    parser.add_argument(
        "--id-prefix",
        default="",
        help=(
            "Optional prefix for generated asset IDs, useful when processing "
            "layered and flat SVG dirs into one icons dir"
        ),
    )
    parser.add_argument(
        "--min-drawables", type=int, default=DEFAULT_MIN_DRAWABLES,
        help=f"Min drawable elements for a group to be extracted (default: {DEFAULT_MIN_DRAWABLES})",
    )
    parser.add_argument(
        "--min-bytes", type=int, default=DEFAULT_MIN_BYTES,
        help=f"Min XML bytes for a pure-vector group/run to be extracted (default: {DEFAULT_MIN_BYTES})",
    )
    parser.add_argument(
        "--min-decoration-bytes", type=int, default=DEFAULT_MIN_DECORATION_BYTES,
        help=(
            "Min XML bytes for pure-vector decoration runs inside text-bearing groups "
            f"(default: {DEFAULT_MIN_DECORATION_BYTES})"
        ),
    )
    parser.add_argument(
        "--inplace", action="store_true",
        help="Rewrite the source SVGs in place instead of writing to --rewritten-dir",
    )
    parser.add_argument(
        "--clean-stale",
        action="store_true",
        help=(
            "Remove stale generated assets for the current svg filenames/id prefix "
            "that are not referenced by this run's inventory"
        ),
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    svg_dir = Path(args.svg_dir)
    if not svg_dir.is_dir():
        print(f"[ERROR] svg_dir not found: {svg_dir}", file=sys.stderr)
        return 1

    icons_dir = Path(args.icons_dir) if args.icons_dir else svg_dir.parent / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    reusable_assets: dict[str, dict] = {}
    reuse_inventory_path = Path(args.reuse_inventory) if args.reuse_inventory else None
    if reuse_inventory_path is not None:
        try:
            reusable_assets = _load_reusable_assets(reuse_inventory_path, icons_dir)
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
    rewritten_dir = Path(args.rewritten_dir) if args.rewritten_dir else None
    inventory_path = (
        Path(args.inventory)
        if args.inventory
        else svg_dir.parent / f"{svg_dir.name}_vector_asset_inventory.json"
    )
    svg_paths = sorted(svg_dir.glob("*.svg"))

    inventory: list[dict] = []
    for svg_path in svg_paths:
        try:
            inventory.extend(
                extract_file(
                    svg_path,
                    icons_dir,
                    args.min_drawables,
                    args.min_bytes,
                    args.min_decoration_bytes,
                    args.inplace,
                    args.id_prefix,
                    rewritten_dir,
                    reusable_assets,
                )
            )
        except ET.ParseError as exc:
            print(f"[WARN] skip unparseable {svg_path.name}: {exc}", file=sys.stderr)

    extracted_count = sum(entry.get("source") == "extracted" for entry in inventory)
    reused_count = sum(entry.get("source") == "reused-inventory" for entry in inventory)
    known_assets = {str(entry["asset"]) for entry in inventory}
    inventory.extend(_existing_placeholder_entries(svg_paths, icons_dir, known_assets))

    stale_removed: list[str] = []
    if args.clean_stale:
        keep_assets = {str(entry["asset"]) for entry in inventory}
        keep_assets.update(_referenced_icon_assets(svg_paths))
        stale_removed = _clean_stale_assets(
            icons_dir,
            svg_paths,
            args.id_prefix,
            keep_assets,
        )

    manifest = {
        "schema": "vector_asset_inventory.v1",
        "svg_dir": str(svg_dir),
        "icons_dir": str(icons_dir),
        "rewritten_dir": (
            None
            if args.inplace
            else str(_rewritten_path(svg_dir / "_sample.svg", rewritten_dir, False).parent)
        ),
        "reuse_inventory": str(reuse_inventory_path) if reuse_inventory_path is not None else None,
        "min_drawables": args.min_drawables,
        "min_bytes": args.min_bytes,
        "min_decoration_bytes": args.min_decoration_bytes,
        "extracted_count": extracted_count,
        "reused_count": reused_count,
        "asset_count": len(inventory),
        "stale_removed": stale_removed,
        "assets": inventory,
    }
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"[OK] extracted {extracted_count} new asset(s), reused {reused_count} asset(s), "
        f"inventoried {len(inventory)} asset reference(s) -> {icons_dir}",
        file=sys.stderr,
    )
    if stale_removed:
        print(f"[OK] removed {len(stale_removed)} stale generated asset(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
