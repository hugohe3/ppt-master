#!/usr/bin/env python3
"""
PPT Master - Explicit SVG Picture Asset Extractor

Extract explicitly selected ``<g id>`` elements from one SVG into tight,
self-contained SVG picture assets. Each selected group is replaced in place by
one ``<image>`` at the same parent index, so native export produces one
PowerPoint ``p:pic`` instead of a DrawingML group.

This tool is intentionally selection-only. It does not discover repeated
objects, infer Master/Layout structure, or change the native-shape semantics of
``extract_svg_assets.py``.

Usage:
    python3 scripts/extract_svg_pictures.py page.svg --select emblem \
        --images-dir project/images -o project/svg_output/page.svg

Examples:
    python3 scripts/extract_svg_pictures.py imported/slide_01.svg \
        --select shape-15 --resource-root imported \
        --images-dir imported/images --inplace
    python3 scripts/extract_svg_pictures.py source.svg --select complex-art \
        --bounds complex-art=80,120,320,240 --images-dir work/images \
        -o work/normalized.svg

Dependencies:
    Standard library. Playwright is optional for targets without an explicit
    ``--bounds`` value or imported ``data-pptx-frame`` metadata.

See workflows/create-template.md and scripts/docs/svg-pipeline.md.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import math
import mimetypes
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio

configure_utf8_stdio()

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
GEOMETRY_ROOT_ATTRS = {"viewBox", "width", "height", "x", "y", "transform"}
PRESERVED_IMAGE_ATTRS = {
    "aria-label",
    "data-name",
    "data-pptx-layer",
    "data-pptx-role",
    "data-pptx-shape-name",
    "id",
}
SEMANTIC_MARKERS = {
    "data-icon",
    "data-pptx-authoring",
    "data-pptx-import-source",
    "data-pptx-placeholder",
    "data-pptx-replace-with",
}
SEMANTIC_PREFIXES = (
    "data-pptx-fallback-",
    "data-pptx-native",
    "data-pptx-placeholder-",
    "data-pptx-replace",
)
VISUAL_TAGS = {
    "circle",
    "ellipse",
    "image",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
    "svg",
    "text",
    "use",
}
UNSAFE_PICTURE_TAGS = {
    "animate",
    "animateMotion",
    "animateTransform",
    "foreignObject",
    "script",
    "set",
}
_URL_RE = re.compile(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)", re.IGNORECASE)
_FRAME_SPLIT_RE = re.compile(r"[\s,]+")

ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)


class SvgPictureError(RuntimeError):
    """Raised when an explicit picture extraction cannot be completed safely."""


@dataclass(frozen=True)
class Bounds:
    """One positive rectangle in source-root user coordinates."""

    x: float
    y: float
    width: float
    height: float

@dataclass
class ExtractionPlan:
    """Prepared output for one selected source group."""

    selector: str
    asset_path: Path
    href: str
    bounds: Bounds
    bounds_source: str
    asset_bytes: bytes
    dependency_ids: list[str]
    embedded_resources: list[str]


def _local(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _fmt(value: float) -> str:
    rounded = round(value, 6)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.6f}".rstrip("0").rstrip(".")


def _padded_bounds(bounds: Bounds, padding: float) -> Bounds:
    return Bounds(
        bounds.x - padding,
        bounds.y - padding,
        bounds.width + 2 * padding,
        bounds.height + 2 * padding,
    )


def _parse_svg(path: Path) -> tuple[ET.ElementTree, ET.Element]:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    try:
        tree = ET.parse(path, parser=parser)
    except (ET.ParseError, OSError) as exc:
        raise SvgPictureError(f"Cannot parse SVG {path}: {exc}") from exc
    root = tree.getroot()
    if _local(root.tag) != "svg":
        raise SvgPictureError(f"Expected an SVG root in {path}")
    return tree, root


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _index_ids(root: ET.Element) -> dict[str, ET.Element]:
    by_id: dict[str, ET.Element] = {}
    duplicates: list[str] = []
    for elem in root.iter():
        elem_id = (elem.get("id") or "").strip()
        if not elem_id:
            continue
        if elem_id in by_id:
            duplicates.append(elem_id)
        by_id[elem_id] = elem
    if duplicates:
        raise SvgPictureError("Duplicate SVG id(s): " + ", ".join(sorted(set(duplicates))))
    return by_id


def _is_descendant(container: ET.Element, candidate: ET.Element) -> bool:
    return any(elem is candidate for elem in container.iter())


def _validate_source(root: ET.Element) -> None:
    if root.get("transform"):
        raise SvgPictureError("Root-level SVG transform is unsupported; normalize it before extraction")
    if any(_local(elem.tag) == "script" for elem in root.iter()):
        raise SvgPictureError("SVG scripts are not allowed in extracted picture assets")
    for elem in root.iter():
        if _local(elem.tag) == "style" and "@import" in (elem.text or "").lower():
            raise SvgPictureError("CSS @import is not allowed in extracted picture assets")


def _validate_resource_value(value: str, *, allow_fragment: bool) -> None:
    raw = value.strip()
    if not raw or raw.startswith("data:"):
        return
    if allow_fragment and raw.startswith("#"):
        return
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        raise SvgPictureError(f"Remote or scheme-based SVG resource is not allowed: {raw}")
    if parsed.fragment and parsed.path.lower().endswith(".svg"):
        raise SvgPictureError(f"External SVG fragment references are not supported: {raw}")


def _validate_target(selector: str, target: ET.Element) -> None:
    if _local(target.tag) != "g":
        raise SvgPictureError(f"Selector {selector!r} must identify one <g> element")
    object_kind = (target.get("data-pptx-object") or "").strip()
    if object_kind and object_kind != "group":
        raise SvgPictureError(
            f"Selector {selector!r} is one imported {object_kind!r} object, not a complex group"
        )
    if not any(_local(elem.tag) in VISUAL_TAGS for elem in target.iter()):
        raise SvgPictureError(f"Selector {selector!r} has no visual SVG content")
    for elem in target.iter():
        if _local(elem.tag) in UNSAFE_PICTURE_TAGS:
            raise SvgPictureError(
                f"Selector {selector!r} contains unsupported <{_local(elem.tag)}> content"
            )
        markers = _semantic_markers(elem)
        if markers:
            raise SvgPictureError(
                f"Selector {selector!r} contains {markers[0]}; preserve its existing semantic route"
            )


def _semantic_markers(elem: ET.Element) -> list[str]:
    return sorted(
        _local(name)
        for name in elem.attrib
        if _local(name) in SEMANTIC_MARKERS
        or _local(name).startswith(SEMANTIC_PREFIXES)
    )


def _parse_bounds(raw: str, context: str) -> Bounds:
    tokens = [token for token in _FRAME_SPLIT_RE.split(raw.strip()) if token]
    if len(tokens) != 4:
        raise SvgPictureError(f"{context} must contain x,y,width,height")
    try:
        values = [float(token) for token in tokens]
    except ValueError as exc:
        raise SvgPictureError(f"{context} contains a non-numeric coordinate") from exc
    if not all(math.isfinite(value) for value in values):
        raise SvgPictureError(f"{context} must contain finite coordinates")
    bounds = Bounds(*values)
    if bounds.width <= 0 or bounds.height <= 0:
        raise SvgPictureError(f"{context} width and height must be positive")
    return bounds


def _parse_key_values(values: list[str], option: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        key, separator, value = raw.partition("=")
        key = key.strip()
        if not separator or not key or not value.strip():
            raise SvgPictureError(f"{option} expects ID=value, got {raw!r}")
        if key in parsed:
            raise SvgPictureError(f"{option} repeats selector {key!r}")
        parsed[key] = value.strip()
    return parsed


def _measure_bounds(source: Path, selectors: list[str]) -> dict[str, Bounds]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SvgPictureError(
            "Playwright is required to measure this target; install it or pass --bounds ID=x,y,w,h"
        ) from exc

    script = """
    (ids) => Object.fromEntries(ids.map((id) => {
      const element = document.getElementById(id);
      const root = element && element.ownerSVGElement;
      const rootMatrix = root && root.getScreenCTM();
      if (!element || !root || !rootMatrix) throw new Error(`Cannot measure ${id}`);
      const rect = element.getBoundingClientRect();
      const inverse = rootMatrix.inverse();
      const points = [
        new DOMPoint(rect.left, rect.top), new DOMPoint(rect.right, rect.top),
        new DOMPoint(rect.right, rect.bottom), new DOMPoint(rect.left, rect.bottom),
      ].map((point) => point.matrixTransform(inverse));
      const xs = points.map((point) => point.x);
      const ys = points.map((point) => point.y);
      return [id, {
        x: Math.min(...xs), y: Math.min(...ys),
        width: Math.max(...xs) - Math.min(...xs),
        height: Math.max(...ys) - Math.min(...ys),
      }];
    }))
    """
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.route("http://**/*", lambda route: route.abort())
            page.route("https://**/*", lambda route: route.abort())
            page.goto(source.resolve().as_uri(), wait_until="load")
            page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
            measured = page.evaluate(script, selectors)
            browser.close()
    except (PlaywrightError, OSError, RuntimeError) as exc:
        raise SvgPictureError(
            "Browser measurement failed; pass explicit --bounds ID=x,y,w,h if needed: "
            f"{exc}"
        ) from exc

    return {
        selector: _parse_bounds(
            ",".join(str(measured[selector][field]) for field in ("x", "y", "width", "height")),
            f"measured bounds for {selector}",
        )
        for selector in selectors
    }


def _resolve_bounds(
    source: Path,
    targets: dict[str, ET.Element],
    overrides: dict[str, str],
    mode: str,
    padding: float,
) -> dict[str, tuple[Bounds, str]]:
    resolved: dict[str, tuple[Bounds, str]] = {}
    measure: list[str] = []
    for selector, target in targets.items():
        if selector in overrides:
            resolved[selector] = (_parse_bounds(overrides[selector], f"--bounds {selector}"), "explicit")
            continue
        frame = target.get("data-pptx-frame")
        if mode != "measure" and frame:
            resolved[selector] = (_parse_bounds(frame, f"{selector} data-pptx-frame"), "data-pptx-frame")
            continue
        if mode == "frame":
            raise SvgPictureError(
                f"Selector {selector!r} has no data-pptx-frame; pass --bounds or use --bounds-mode measure"
            )
        measure.append(selector)

    for selector, bounds in _measure_bounds(source, measure).items() if measure else []:
        resolved[selector] = (bounds, "browser")
    return {
        selector: (_padded_bounds(bounds, padding), source_name)
        for selector, (bounds, source_name) in resolved.items()
    }


def _referenced_ids(elem: ET.Element) -> set[str]:
    refs: set[str] = set()
    for item in elem.iter():
        for attr_name, value in item.attrib.items():
            refs.update(
                match.group(2)[1:]
                for match in _URL_RE.finditer(value)
                if match.group(2).startswith("#")
            )
            if _local(attr_name) == "href" and value.startswith("#") and len(value) > 1:
                refs.add(value[1:])
        if item.text:
            refs.update(
                match.group(2)[1:]
                for match in _URL_RE.finditer(item.text)
                if match.group(2).startswith("#")
            )
    return refs


def _visual_clone(
    root: ET.Element,
    target: ET.Element,
    parents: dict[ET.Element, ET.Element],
) -> tuple[ET.Element, set[ET.Element]]:
    clone = copy.deepcopy(target)
    included = {target}
    cursor = target
    while parents.get(cursor) is not root:
        ancestor = parents.get(cursor)
        if ancestor is None or _local(ancestor.tag) != "g":
            raise SvgPictureError("Selected group is not in the visible SVG tree")
        unsafe_attrs = [
            _local(name)
            for name in ancestor.attrib
            if not (
                _local(name) == "id"
                or _local(name) == "role"
                or _local(name).startswith("data-")
                or _local(name).startswith("aria-")
            )
        ]
        semantic_attrs = _semantic_markers(ancestor)
        if unsafe_attrs or semantic_attrs:
            details = ", ".join(sorted(set(unsafe_attrs + semantic_attrs)))
            raise SvgPictureError(
                "Selected group has a non-neutral ancestor "
                f"{ancestor.get('id') or '<g>'} ({details}); select that outer group instead"
            )
        shell = ET.Element(ancestor.tag, dict(ancestor.attrib))
        shell.append(clone)
        clone = shell
        included.add(ancestor)
        cursor = ancestor
    return clone, included


def _dependency_elements(
    root: ET.Element,
    target: ET.Element,
    visual: ET.Element,
    included: set[ET.Element],
    parents: dict[ET.Element, ET.Element],
) -> list[ET.Element]:
    by_id = _index_ids(root)
    queue = sorted(_referenced_ids(visual))
    dependencies: list[ET.Element] = []
    seen: set[str] = set()
    while queue:
        ref_id = queue.pop(0)
        if ref_id in seen:
            continue
        seen.add(ref_id)
        dependency = by_id.get(ref_id)
        if dependency is None:
            raise SvgPictureError(f"Referenced SVG definition #{ref_id} does not exist")
        if dependency in included or _is_descendant(target, dependency):
            continue
        dependencies.append(dependency)
        queue.extend(sorted(_referenced_ids(dependency) - seen))

    dependency_set = set(dependencies)
    return [
        dependency
        for dependency in dependencies
        if not any(ancestor in dependency_set for ancestor in _ancestors(dependency, parents))
    ]


def _ancestors(
    elem: ET.Element,
    parents: dict[ET.Element, ET.Element],
) -> list[ET.Element]:
    found: list[ET.Element] = []
    cursor = elem
    while cursor in parents:
        cursor = parents[cursor]
        found.append(cursor)
    return found


def _data_uri(resource: Path) -> str:
    try:
        payload = resource.read_bytes()
    except OSError as exc:
        raise SvgPictureError(f"Cannot embed local SVG resource {resource}: {exc}") from exc
    mime = mimetypes.guess_type(resource.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _embed_reference(
    value: str,
    source_dir: Path,
    resource_root: Path,
    embedded: list[str],
) -> str:
    raw = value.strip()
    if not raw or raw.startswith(("#", "data:")):
        return value
    parsed = urlsplit(raw)
    _validate_resource_value(raw, allow_fragment=True)
    resource = (source_dir / unquote(parsed.path)).resolve()
    try:
        relative_resource = resource.relative_to(resource_root)
    except ValueError as exc:
        raise SvgPictureError(f"Local SVG resource escapes --resource-root: {raw}") from exc
    if not resource.is_file():
        raise SvgPictureError(f"Local SVG resource does not exist: {raw}")
    embedded.append(relative_resource.as_posix())
    return _data_uri(resource)


def _embed_css_urls(
    value: str,
    source_dir: Path,
    resource_root: Path,
    embedded: list[str],
) -> str:
    def replace(match: re.Match[str]) -> str:
        reference = match.group(2)
        if reference.startswith(("#", "data:")):
            return match.group(0)
        embedded_reference = _embed_reference(
            reference,
            source_dir,
            resource_root,
            embedded,
        )
        return f'url("{embedded_reference}")'

    return _URL_RE.sub(replace, value)


def _embed_external_resources(
    asset_root: ET.Element,
    source_dir: Path,
    resource_root: Path,
) -> list[str]:
    embedded: list[str] = []
    for elem in asset_root.iter():
        tag = _local(elem.tag)
        for attr_name, value in list(elem.attrib.items()):
            rewritten = _embed_css_urls(value, source_dir, resource_root, embedded)
            if _local(attr_name) == "href" and tag in {"image", "feImage"}:
                rewritten = _embed_reference(
                    rewritten,
                    source_dir,
                    resource_root,
                    embedded,
                )
            elif _local(attr_name) == "href" and tag == "use" and not rewritten.startswith("#"):
                raise SvgPictureError(f"External <use> is unsupported in a picture asset: {rewritten}")
            if rewritten != value:
                elem.set(attr_name, rewritten)
        if elem.text:
            elem.text = _embed_css_urls(
                elem.text,
                source_dir,
                resource_root,
                embedded,
            )
    return sorted(set(embedded))


def _rebase_reference(
    value: str,
    source_dir: Path,
    output_dir: Path,
    resource_root: Path,
) -> str:
    raw = value.strip()
    if not raw or raw.startswith(("#", "data:")):
        return value
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return value
    resource = (source_dir / unquote(parsed.path)).resolve()
    try:
        resource.relative_to(resource_root)
    except ValueError as exc:
        raise SvgPictureError(f"Local page resource escapes --resource-root: {raw}") from exc
    relative = Path(os.path.relpath(resource, output_dir)).as_posix()
    return urlunsplit(("", "", relative, parsed.query, parsed.fragment))


def _rebase_css_urls(
    value: str,
    source_dir: Path,
    output_dir: Path,
    resource_root: Path,
) -> str:
    def replace(match: re.Match[str]) -> str:
        reference = match.group(2)
        rewritten = _rebase_reference(
            reference,
            source_dir,
            output_dir,
            resource_root,
        )
        if rewritten == reference:
            return match.group(0)
        quote = match.group(1)
        return f"url({quote}{rewritten}{quote})"

    return _URL_RE.sub(replace, value)


def _rebase_page_resources(
    root: ET.Element,
    source_dir: Path,
    output_dir: Path,
    resource_root: Path,
) -> None:
    if source_dir == output_dir:
        return
    for elem in root.iter():
        tag = _local(elem.tag)
        for attr_name, value in list(elem.attrib.items()):
            rewritten = _rebase_css_urls(
                value,
                source_dir,
                output_dir,
                resource_root,
            )
            if _local(attr_name) == "href" and tag in {"image", "feImage", "use"}:
                rewritten = _rebase_reference(
                    rewritten,
                    source_dir,
                    output_dir,
                    resource_root,
                )
            if rewritten != value:
                elem.set(attr_name, rewritten)
        if elem.text:
            elem.text = _rebase_css_urls(
                elem.text,
                source_dir,
                output_dir,
                resource_root,
            )


def _asset_root_attributes(source_root: ET.Element, bounds: Bounds) -> dict[str, str]:
    attrs = {
        name: value
        for name, value in source_root.attrib.items()
        if _local(name) not in GEOMETRY_ROOT_ATTRS
    }
    attrs.update(
        {
            "viewBox": f"0 0 {_fmt(bounds.width)} {_fmt(bounds.height)}",
            "width": _fmt(bounds.width),
            "height": _fmt(bounds.height),
        }
    )
    return attrs


def _build_asset(
    source: Path,
    resource_root: Path,
    root: ET.Element,
    target: ET.Element,
    bounds: Bounds,
    parents: dict[ET.Element, ET.Element],
) -> tuple[bytes, list[str], list[str]]:
    visual, included = _visual_clone(root, target, parents)
    dependencies = _dependency_elements(root, target, visual, included, parents)
    styles = [
        elem
        for elem in root.iter()
        if _local(elem.tag) == "style"
        and not _is_descendant(target, elem)
        and not any(_is_descendant(dependency, elem) for dependency in dependencies)
    ]
    asset_root = ET.Element(root.tag, _asset_root_attributes(root, bounds))
    if styles or dependencies:
        defs = ET.SubElement(asset_root, f"{{{SVG_NS}}}defs")
        for style in styles:
            defs.append(copy.deepcopy(style))
        for dependency in dependencies:
            if _local(dependency.tag) != "style":
                defs.append(copy.deepcopy(dependency))
    translated = ET.SubElement(
        asset_root,
        f"{{{SVG_NS}}}g",
        {"transform": f"translate({_fmt(-bounds.x)} {_fmt(-bounds.y)})"},
    )
    translated.append(visual)
    embedded = _embed_external_resources(asset_root, source.parent, resource_root)
    ET.indent(asset_root, space="  ")
    payload = ET.tostring(asset_root, encoding="utf-8", xml_declaration=True)
    dependency_ids = sorted(filter(None, (elem.get("id") for elem in dependencies)))
    return payload, dependency_ids, embedded


def _safe_asset_name(source: Path, selector: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", selector).strip(".-") or "asset"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source.stem).strip(".-") or "source"
    return f"{safe_stem}__{safe_id}.svg"


def _validate_asset_name(name: str, selector: str) -> str:
    path = Path(name)
    if path.name != name or path.suffix.lower() != ".svg":
        raise SvgPictureError(f"Asset name for {selector!r} must be one .svg basename")
    return name


def _replacement_image(target: ET.Element, bounds: Bounds, href: str) -> ET.Element:
    attrs = {
        name: value
        for name, value in target.attrib.items()
        if _local(name) in PRESERVED_IMAGE_ATTRS
    }
    attrs.update(
        {
            "href": href,
            "x": _fmt(bounds.x),
            "y": _fmt(bounds.y),
            "width": _fmt(bounds.width),
            "height": _fmt(bounds.height),
            "preserveAspectRatio": "none",
        }
    )
    return ET.Element(f"{{{SVG_NS}}}image", attrs)


def _prepare_plans(
    source: Path,
    resource_root: Path,
    output: Path,
    images_dir: Path,
    root: ET.Element,
    targets: dict[str, ET.Element],
    resolved_bounds: dict[str, tuple[Bounds, str]],
    names: dict[str, str],
    parents: dict[ET.Element, ET.Element],
) -> list[ExtractionPlan]:
    plans: list[ExtractionPlan] = []
    for selector, target in targets.items():
        bounds, bounds_source = resolved_bounds[selector]
        name = _validate_asset_name(
            names.get(selector, _safe_asset_name(source, selector)),
            selector,
        )
        asset_path = images_dir / name
        href = Path(os.path.relpath(asset_path, output.parent)).as_posix()
        payload, dependency_ids, embedded = _build_asset(
            source,
            resource_root,
            root,
            target,
            bounds,
            parents,
        )
        plans.append(
            ExtractionPlan(
                selector=selector,
                asset_path=asset_path,
                href=href,
                bounds=bounds,
                bounds_source=bounds_source,
                asset_bytes=payload,
                dependency_ids=dependency_ids,
                embedded_resources=embedded,
            )
        )
    asset_paths = [plan.asset_path for plan in plans]
    if len(set(asset_paths)) != len(asset_paths):
        raise SvgPictureError("Generated or overridden asset filenames must be unique")
    return plans


def _check_outputs(
    source: Path,
    output: Path,
    inventory: Path,
    plans: list[ExtractionPlan],
    overwrite: bool,
) -> None:
    if output != source and output.exists() and not overwrite:
        raise SvgPictureError(f"Output SVG exists; pass --overwrite to replace it: {output}")
    if inventory.exists() and not overwrite:
        raise SvgPictureError(f"Inventory exists; pass --overwrite to replace it: {inventory}")
    for plan in plans:
        if not plan.asset_path.exists():
            continue
        if plan.asset_path.read_bytes() != plan.asset_bytes and not overwrite:
            raise SvgPictureError(
                f"Picture asset exists with different bytes; pass --overwrite: {plan.asset_path}"
            )


def _replace_targets(
    targets: dict[str, ET.Element],
    plans: list[ExtractionPlan],
    parents: dict[ET.Element, ET.Element],
) -> None:
    for plan in plans:
        target = targets[plan.selector]
        parent = parents[target]
        index = list(parent).index(target)
        parent.remove(target)
        parent.insert(index, _replacement_image(target, plan.bounds, plan.href))


def _inventory_payload(
    source: Path,
    resource_root: Path,
    output: Path,
    images_dir: Path,
    plans: list[ExtractionPlan],
) -> bytes:
    payload = {
        "schema": "svg_picture_asset_inventory.v1",
        "sourceSvg": str(source),
        "resourceRoot": str(resource_root),
        "rewrittenSvg": str(output),
        "imagesDir": str(images_dir),
        "items": [
            {
                "selector": plan.selector,
                "asset": str(plan.asset_path),
                "href": plan.href,
                "bounds": [
                    plan.bounds.x,
                    plan.bounds.y,
                    plan.bounds.width,
                    plan.bounds.height,
                ],
                "boundsSource": plan.bounds_source,
                "sha256": hashlib.sha256(plan.asset_bytes).hexdigest(),
                "dependencyIds": plan.dependency_ids,
                "embeddedResources": plan.embedded_resources,
            }
            for plan in plans
        ],
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _write_outputs(
    tree: ET.ElementTree,
    output: Path,
    inventory: Path,
    images_dir: Path,
    plans: list[ExtractionPlan],
    inventory_bytes: bytes,
) -> None:
    images_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    inventory.parent.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        plan.asset_path.write_bytes(plan.asset_bytes)
    ET.indent(tree, space="  ")
    output.write_bytes(ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True))
    inventory.write_bytes(inventory_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract explicitly selected SVG groups as standalone SVG picture assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("svg_file", type=Path, help="Source SVG file")
    parser.add_argument(
        "--select",
        action="append",
        required=True,
        metavar="ID",
        help="Exact <g id> to extract; repeat for multiple groups",
    )
    parser.add_argument("--images-dir", required=True, type=Path, help="Destination image asset directory")
    parser.add_argument(
        "--resource-root",
        type=Path,
        help="Allowed root for local SVG dependencies (default: source directory)",
    )
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument("-o", "--output", type=Path, help="Rewritten SVG path")
    output.add_argument("--inplace", action="store_true", help="Rewrite the source SVG")
    parser.add_argument(
        "--bounds",
        action="append",
        default=[],
        metavar="ID=X,Y,W,H",
        help="Explicit tight bounds for one selector; repeat as needed",
    )
    parser.add_argument(
        "--bounds-mode",
        choices=("auto", "frame", "measure"),
        default="auto",
        help="Bounds source when --bounds is absent (default: auto)",
    )
    parser.add_argument("--padding", type=float, default=0.0, help="Non-negative padding in SVG units")
    parser.add_argument(
        "--asset-name",
        action="append",
        default=[],
        metavar="ID=NAME.svg",
        help="Override one generated asset filename",
    )
    parser.add_argument("--inventory", type=Path, help="Explicit JSON inventory path")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing non-identical outputs")
    return parser


def _run(args: argparse.Namespace) -> dict[str, object]:
    source = args.svg_file.resolve()
    if not source.is_file():
        raise SvgPictureError(f"Source SVG does not exist: {source}")
    if args.padding < 0 or not math.isfinite(args.padding):
        raise SvgPictureError("--padding must be a finite non-negative number")
    selectors = [selector.strip() for selector in args.select]
    if any(not selector for selector in selectors) or len(set(selectors)) != len(selectors):
        raise SvgPictureError("--select values must be non-empty and unique")
    print(
        f"Preparing {len(selectors)} explicit SVG picture asset(s) from {source.name}",
        file=sys.stderr,
    )

    output = source if args.inplace else args.output.resolve()
    if not args.inplace and output == source:
        raise SvgPictureError("Use --inplace explicitly when the output is the source SVG")
    images_dir = args.images_dir.resolve()
    resource_root = args.resource_root.resolve() if args.resource_root else source.parent
    if not resource_root.is_dir():
        raise SvgPictureError(f"--resource-root is not a directory: {resource_root}")
    try:
        source.relative_to(resource_root)
    except ValueError as exc:
        raise SvgPictureError("Source SVG must be inside --resource-root") from exc
    inventory = (
        args.inventory.resolve()
        if args.inventory
        else output.with_name(f"{output.stem}_picture_asset_inventory.json")
    )
    if inventory in {source, output}:
        raise SvgPictureError("Inventory path must differ from the source and rewritten SVG")
    bounds_overrides = _parse_key_values(args.bounds, "--bounds")
    asset_names = _parse_key_values(args.asset_name, "--asset-name")
    unknown_options = (set(bounds_overrides) | set(asset_names)) - set(selectors)
    if unknown_options:
        raise SvgPictureError("Options reference unselected id(s): " + ", ".join(sorted(unknown_options)))

    tree, root = _parse_svg(source)
    _validate_source(root)
    ids = _index_ids(root)
    missing = [selector for selector in selectors if selector not in ids]
    if missing:
        raise SvgPictureError("Selected SVG id(s) do not exist: " + ", ".join(missing))
    targets = {selector: ids[selector] for selector in selectors}
    for selector, target in targets.items():
        _validate_target(selector, target)
    for outer_id, outer in targets.items():
        for inner_id, inner in targets.items():
            if outer_id != inner_id and _is_descendant(outer, inner):
                raise SvgPictureError(f"Nested selections are not allowed: {outer_id!r} contains {inner_id!r}")

    parents = _parent_map(root)
    resolved = _resolve_bounds(
        source,
        targets,
        bounds_overrides,
        args.bounds_mode,
        args.padding,
    )
    plans = _prepare_plans(
        source,
        resource_root,
        output,
        images_dir,
        root,
        targets,
        resolved,
        asset_names,
        parents,
    )
    occupied = {source, output, inventory}
    if any(plan.asset_path in occupied for plan in plans):
        raise SvgPictureError("Picture asset paths must differ from SVG and inventory paths")
    _check_outputs(source, output, inventory, plans, args.overwrite)
    _rebase_page_resources(root, source.parent, output.parent, resource_root)
    _replace_targets(targets, plans, parents)
    inventory_bytes = _inventory_payload(
        source,
        resource_root,
        output,
        images_dir,
        plans,
    )
    _write_outputs(tree, output, inventory, images_dir, plans, inventory_bytes)
    print(f"Wrote rewritten SVG and {len(plans)} picture asset(s)", file=sys.stderr)
    return {
        "source": str(source),
        "output": str(output),
        "inventory": str(inventory),
        "assets": [str(plan.asset_path) for plan in plans],
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        result = _run(parser.parse_args(argv))
    except (OSError, SvgPictureError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
