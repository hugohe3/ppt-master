#!/usr/bin/env python3
"""
PPT Master - LaTeX Formula Renderer

Render Strategist-declared LaTeX formulas to transparent PNG assets.
The script reads an explicit manifest; it never scans spec_lock.md or source
content for dollar-delimited math.

Usage:
    python3 scripts/latex_render.py <project_path>
    python3 scripts/latex_render.py <project_path> --manifest images/formula_manifest.json
    python3 scripts/latex_render.py <project_path> --dry-run

Examples:
    python3 scripts/latex_render.py projects/demo_ppt169_20260523
    python3 scripts/latex_render.py projects/demo_ppt169_20260523 --providers codecogs,quicklatex,mathpad,wikimedia

Dependencies:
    Pillow (for measuring generated PNG dimensions)
    Network access to at least one configured rendering provider
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from console_encoding import configure_utf8_stdio

try:
    from PIL import Image
except ImportError:
    Image = None


configure_utf8_stdio()


DEFAULT_DPI = 300
DEFAULT_TRANSPARENT_TOLERANCE = 12
DEFAULT_MANIFEST = "images/formula_manifest.json"
DEFAULT_PROVIDERS = ["codecogs", "quicklatex", "mathpad", "wikimedia"]
CODECOGS_ENDPOINT = "https://latex.codecogs.com/png.image?"
WIKIMEDIA_CHECK_ENDPOINT = "https://wikimedia.org/api/rest_v1/media/math/check"
WIKIMEDIA_RENDER_ENDPOINT = "https://wikimedia.org/api/rest_v1/media/math/render/png"
QUICKLATEX_ENDPOINT = "https://quicklatex.com/latex3.f"
MATHPAD_ENDPOINT = "https://mathpad.ai/api/v1/latex2image"
VALID_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.png$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _project_relative(path: Path, project_path: Path) -> str:
    """Return a POSIX-style path relative to the project."""
    return path.relative_to(project_path).as_posix()


def _load_manifest(path: Path) -> dict[str, Any]:
    """Load a JSON formula manifest."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read manifest: {path} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Manifest is not valid JSON: {path} ({exc})") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Manifest root must be a JSON object.")
    items = data.get("items")
    if not isinstance(items, list):
        raise RuntimeError("Manifest must contain an `items` array.")
    return data


def _safe_filename(item: dict[str, Any], index: int) -> str:
    """Resolve and validate the output PNG filename for one formula."""
    filename = item.get("filename")
    if filename is None:
        formula_id = str(item.get("id") or f"formula_{index:03d}")
        filename = f"{formula_id}.png"
    filename = str(filename)
    if "/" in filename or "\\" in filename or not VALID_FILENAME_RE.match(filename):
        raise RuntimeError(
            f"Invalid formula filename `{filename}`. Use a simple PNG filename "
            "such as `formula_001.png`."
        )
    return filename


def _normalize_hex_color(color: str | None, field_name: str) -> str | None:
    """Normalize an optional 6-digit HEX color."""
    if not color:
        return None
    value = color.strip()
    if value.startswith("#"):
        value = value[1:]
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise RuntimeError(f"Formula {field_name} must be a 6-digit HEX value: {color}")
    return value.upper()


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert a normalized HEX color to an RGB tuple."""
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def _parse_bool(value: Any, default: bool) -> bool:
    """Parse a manifest boolean with a default."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise RuntimeError(f"Expected boolean value, got: {value!r}")


def _normalize_tolerance(value: Any) -> int:
    """Normalize the background removal tolerance."""
    if value is None:
        return DEFAULT_TRANSPARENT_TOLERANCE
    tolerance = int(value)
    if tolerance < 0 or tolerance > 255:
        raise RuntimeError("transparent_tolerance must be between 0 and 255.")
    return tolerance


def _parse_providers(value: str | list[str] | None) -> list[str]:
    """Parse and validate a provider chain."""
    if value is None:
        providers = DEFAULT_PROVIDERS
    elif isinstance(value, list):
        providers = value
    else:
        providers = [part.strip() for part in value.split(",") if part.strip()]

    valid = {"codecogs", "quicklatex", "mathpad", "wikimedia"}
    unknown = [provider for provider in providers if provider not in valid]
    if unknown:
        raise RuntimeError(
            f"Unknown formula provider(s): {', '.join(unknown)}. "
            f"Available: {', '.join(sorted(valid))}"
        )
    if not providers:
        raise RuntimeError("Provider chain must include at least one provider.")
    return providers


def _request_bytes(req: urllib.request.Request, timeout: int = 30) -> tuple[bytes, str]:
    """Fetch bytes and return the response content type."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc


def _assert_png(data: bytes, provider: str, content_type: str) -> bytes:
    """Validate PNG response bytes."""
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError(
            f"{provider} did not return PNG data (Content-Type: {content_type})"
        )
    return data


def _build_codecogs_payload(latex: str, dpi: int, color: str | None) -> str:
    """Build a CodeCogs LaTeX payload."""
    # CodeCogs documents PNG DPI in the 50-300 range.
    safe_dpi = min(max(dpi, 50), 300)
    parts = [rf"\dpi{{{safe_dpi}}}"]
    if color:
        parts.append(rf"\fg{{{color}}}")
    parts.append(latex)
    return " ".join(parts)


def _render_codecogs(
    latex: str,
    dpi: int,
    color: str | None,
    background: str | None,
    display: str,
) -> bytes:
    """Render one formula through CodeCogs."""
    payload = _build_codecogs_payload(latex, dpi, color)
    url = CODECOGS_ENDPOINT + urllib.parse.quote(payload)
    req = urllib.request.Request(url, headers={"User-Agent": "PPT-Master/1.0"})
    data, content_type = _request_bytes(req)
    return _assert_png(data, "codecogs", content_type)


def _render_wikimedia(
    latex: str,
    dpi: int,
    color: str | None,
    background: str | None,
    display: str,
) -> bytes:
    """Render one formula through Wikimedia Mathoid."""
    formula_type = "inline-tex" if display == "inline" else "tex"
    payload = urllib.parse.urlencode({"q": latex}).encode("utf-8")
    check_req = urllib.request.Request(
        f"{WIKIMEDIA_CHECK_ENDPOINT}/{formula_type}",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PPT-Master/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(check_req, timeout=30) as resp:
            resp.read()
            resource = resp.headers.get("x-resource-location")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc

    if not resource:
        raise RuntimeError("missing x-resource-location header")

    render_req = urllib.request.Request(
        f"{WIKIMEDIA_RENDER_ENDPOINT}/{resource}",
        headers={"User-Agent": "PPT-Master/1.0"},
    )
    data, content_type = _request_bytes(render_req)
    return _assert_png(data, "wikimedia", content_type)


def _render_quicklatex(
    latex: str,
    dpi: int,
    color: str | None,
    background: str | None,
    display: str,
) -> bytes:
    """Render one formula through QuickLaTeX."""
    wrapped = f"${latex}$" if display == "inline" else f"$${latex}$$"
    # QuickLaTeX uses CSS font size rather than DPI. Keep a conservative fixed
    # size; downstream placement uses measured dimensions from the PNG.
    params = {
        "formula": wrapped,
        "fsize": "24px",
        "fcolor": color or "000000",
        "mode": "0",
        "out": "1",
        "remhost": "quicklatex.com",
    }
    req = urllib.request.Request(
        QUICKLATEX_ENDPOINT,
        data=urllib.parse.urlencode(params).encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "PPT-Master/1.0",
        },
        method="POST",
    )
    data, _ = _request_bytes(req)
    text = data.decode("utf-8", errors="replace").strip()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "0":
        raise RuntimeError(text or "QuickLaTeX returned an empty response")
    if len(lines) < 2:
        raise RuntimeError(f"QuickLaTeX response missing image URL: {text}")
    image_url = lines[1].split()[0]
    image_req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "PPT-Master/1.0"},
    )
    image_data, content_type = _request_bytes(image_req)
    return _assert_png(image_data, "quicklatex", content_type)


def _render_mathpad(
    latex: str,
    dpi: int,
    color: str | None,
    background: str | None,
    display: str,
) -> bytes:
    """Render one formula through MathPad's public LaTeX image endpoint."""
    wrapped = f"${latex}$" if display == "inline" else f"$${latex}$$"
    scale = "4" if dpi >= 300 else "2"
    params = {
        "latex": wrapped,
        "format": "png",
        "scale": scale,
        "color": f"#{color or '000000'}",
        "bg": f"#{background or 'FFFFFF'}",
    }
    url = MATHPAD_ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "PPT-Master/1.0"})
    data, content_type = _request_bytes(req)
    return _assert_png(data, "mathpad", content_type)


PROVIDER_RENDERERS = {
    "codecogs": _render_codecogs,
    "quicklatex": _render_quicklatex,
    "mathpad": _render_mathpad,
    "wikimedia": _render_wikimedia,
}
COLOR_AWARE_PROVIDERS = {"codecogs", "quicklatex", "mathpad"}


def _render_with_providers(
    latex: str,
    output_path: Path,
    dpi: int,
    color: str | None,
    background: str | None,
    display: str,
    providers: list[str],
) -> tuple[str, list[str]]:
    """Try providers in order and write the first successful PNG."""
    errors: list[str] = []
    for provider in providers:
        try:
            data = PROVIDER_RENDERERS[provider](latex, dpi, color, background, display)
            output_path.write_bytes(data)
            return provider, errors
        except RuntimeError as exc:
            errors.append(f"{provider}: {exc}")
    raise RuntimeError("; ".join(errors))


def _image_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG dimensions."""
    if Image is None:
        raise RuntimeError(
            "Pillow is required to measure formula PNGs. Run: pip install Pillow"
        )
    with Image.open(path) as img:
        return img.size


def _make_png_background_transparent(
    path: Path,
    *,
    color: str | None,
    background: str | None,
    tolerance: int,
) -> None:
    """Convert the rendered formula's matte background to alpha."""
    if Image is None:
        raise RuntimeError(
            "Pillow is required to post-process transparent formula PNGs. "
            "Run: pip install Pillow"
        )

    bg_rgb = _hex_to_rgb(background or "FFFFFF")
    fg_rgb = _hex_to_rgb(color or "000000")

    with Image.open(path) as img:
        rgba = img.convert("RGBA")

    alpha = rgba.getchannel("A")
    if alpha.getextrema()[0] < 255:
        if color:
            pixels = rgba.load()
            width, height = rgba.size
            for y in range(height):
                for x in range(width):
                    _, _, _, a = pixels[x, y]
                    if a:
                        pixels[x, y] = (fg_rgb[0], fg_rgb[1], fg_rgb[2], a)
            rgba.save(path)
        return

    fg_bg_distance = max(abs(fg_rgb[i] - bg_rgb[i]) for i in range(3))
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue

            bg_distance = max(
                abs(r - bg_rgb[0]),
                abs(g - bg_rgb[1]),
                abs(b - bg_rgb[2]),
            )
            if bg_distance <= tolerance:
                pixels[x, y] = (fg_rgb[0], fg_rgb[1], fg_rgb[2], 0)
                continue

            if fg_bg_distance > tolerance:
                coverage = min(1.0, bg_distance / fg_bg_distance)
                new_alpha = max(1, min(255, round(a * coverage)))
            else:
                new_alpha = a
            pixels[x, y] = (fg_rgb[0], fg_rgb[1], fg_rgb[2], new_alpha)

    rgba.save(path)


def _process_item(
    item: dict[str, Any],
    index: int,
    project_path: Path,
    output_dir: Path,
    default_dpi: int,
    providers: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    """Render one manifest item and return its updated record."""
    latex = str(item.get("latex") or "").strip()
    if not latex:
        raise RuntimeError(f"Formula item #{index} is missing `latex`.")

    filename = _safe_filename(item, index)
    output_path = output_dir / filename
    dpi = int(item.get("dpi") or default_dpi)
    color = _normalize_hex_color(item.get("color"), "color")
    background = _normalize_hex_color(item.get("background"), "background")
    transparent = _parse_bool(item.get("transparent"), True)
    transparent_tolerance = _normalize_tolerance(item.get("transparent_tolerance"))
    display = str(item.get("display") or "block").strip().lower()
    if display not in {"inline", "block"}:
        raise RuntimeError(f"Formula item #{index} has invalid `display`: {display}")
    item_providers = _parse_providers(
        item.get("providers") or item.get("provider_chain") or providers
    )

    updated = dict(item)
    updated["filename"] = filename
    updated["file"] = _project_relative(output_path, project_path)
    updated["dpi"] = dpi
    updated["display"] = display
    updated["providers"] = item_providers
    updated["transparent"] = transparent
    if color:
        updated["color"] = f"#{color}"
    if background:
        updated["background"] = f"#{background}"
    if transparent:
        updated["transparent_tolerance"] = transparent_tolerance

    if dry_run:
        updated["status"] = item.get("status") or "Pending"
        return updated

    try:
        if not output_path.exists() or item.get("status") != "Rendered":
            provider_used, provider_errors = _render_with_providers(
                latex,
                output_path,
                dpi,
                color,
                background,
                display,
                item_providers,
            )
            updated["provider"] = provider_used
            if color and provider_used not in COLOR_AWARE_PROVIDERS:
                updated["color_warning"] = (
                    f"Provider `{provider_used}` is an availability fallback and may "
                    "not preserve the requested formula color."
                )
            if provider_errors:
                updated["provider_errors"] = provider_errors
        if transparent:
            _make_png_background_transparent(
                output_path,
                color=color,
                background=background,
                tolerance=transparent_tolerance,
            )
        width, height = _image_dimensions(output_path)
        updated["pixel_width"] = width
        updated["pixel_height"] = height
        updated["ratio"] = round(width / height, 4) if height else None
        updated["status"] = "Rendered"
        updated.pop("error", None)
    except RuntimeError as exc:
        updated["status"] = "Failed"
        updated["error"] = str(exc)

    return updated


def render_manifest(
    project_path: Path,
    manifest_path: Path,
    *,
    default_dpi: int = DEFAULT_DPI,
    providers: list[str] | None = None,
    dry_run: bool = False,
) -> int:
    """Render all formulas declared in a manifest."""
    manifest = _load_manifest(manifest_path)
    output_dir = project_path / "images"
    updated_items: list[dict[str, Any]] = []
    provider_chain = _parse_providers(providers or manifest.get("providers"))

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for index, raw_item in enumerate(manifest["items"], 1):
        if not isinstance(raw_item, dict):
            raise RuntimeError(f"Formula item #{index} must be an object.")
        updated = _process_item(
            raw_item,
            index,
            project_path,
            output_dir,
            default_dpi,
            provider_chain,
            dry_run,
        )
        updated_items.append(updated)
        status = updated.get("status")
        label = updated.get("id") or updated.get("filename")
        print(f"{status}: {label} -> {updated.get('file')}", file=sys.stderr)
        if status == "Failed":
            failures += 1
            print(f"  {updated.get('error')}", file=sys.stderr)

    if dry_run:
        print(f"Dry run: {len(updated_items)} formula item(s) parsed.", file=sys.stderr)
        return 0

    manifest["items"] = updated_items
    manifest["renderer"] = {
        "providers": provider_chain,
        "default_dpi": default_dpi,
        "output_dir": _project_relative(output_dir, project_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if failures:
        print(f"Formula rendering completed with {failures} failure(s).", file=sys.stderr)
        return 2
    print(f"Formula rendering complete: {len(updated_items)} item(s).", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Render Strategist-declared LaTeX formulas to PNG assets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_path", type=Path, help="Project directory.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"Formula manifest path. Default: <project>/{DEFAULT_MANIFEST}",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Default render DPI when an item omits `dpi` (default: {DEFAULT_DPI}).",
    )
    parser.add_argument(
        "--providers",
        default=None,
        help=(
            "Comma-separated provider fallback chain "
            f"(default: {','.join(DEFAULT_PROVIDERS)})."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and list formula items without rendering or writing files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    project_path = args.project_path.resolve()
    if not project_path.is_dir():
        print(f"Error: project directory not found: {project_path}", file=sys.stderr)
        return 1

    manifest_path = args.manifest
    if manifest_path is None:
        manifest_path = project_path / DEFAULT_MANIFEST
    elif not manifest_path.is_absolute():
        manifest_path = project_path / manifest_path
    manifest_path = manifest_path.resolve()

    try:
        return render_manifest(
            project_path,
            manifest_path,
            default_dpi=args.dpi,
            providers=_parse_providers(args.providers) if args.providers else None,
            dry_run=args.dry_run,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
