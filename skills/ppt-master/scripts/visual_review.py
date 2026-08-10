#!/usr/bin/env python3
"""
PPT Master - Visual Review Renderer

Renders project SVGs at their root viewBox dimensions to PNGs that match the
live-preview browser view (inlined <use data-icon>, resolved <image href>, full
font fallback including CJK). The pure renderer for the visual-review stage —
does not edit SVGs, does not interpret the rubric.

Backend: Playwright (Chromium). The cairosvg backend was evaluated and rejected
because cairo's text API has no font-fallback chain — CJK characters render as
tofu boxes for any deck whose font-family list relies on system fallback.

Usage:
    python3 scripts/visual_review.py <project_path>
    python3 scripts/visual_review.py <project_path> --pages 02 03
    python3 scripts/visual_review.py <project_path> --server-url http://localhost:5050

Exit codes (per references/visual-review.md §7):
    0 — all requested pages rendered
    2 — live-preview server not reachable for this project
    3 — rendering backend (playwright + chromium) missing or unable to launch
    4 — one or more page-level render failures (details in stderr)

Output: JSON summary printed to stdout, PNGs written to <project>/.preview/.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET

from console_encoding import configure_utf8_stdio
from server_common import lock_pid, process_alive, read_lock
from slide_roster import discover_slide_svgs
from svg_to_pptx.canvas_contract import parse_project_svg_root

configure_utf8_stdio()


# Histogram threshold: PNG counts as "all background" if a single quantized
# color bucket holds >= ALL_BG_THRESHOLD of pixels. Guards against blank
# renders without false-firing on legitimate sparse dark layouts.
ALL_BG_THRESHOLD = 0.99


def _safe_print(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


@contextmanager
def file_lock(lock_path: Path, timeout: float = 30.0):
    """POSIX advisory lock via fcntl. Falls back to lockless on Windows."""
    try:
        import fcntl
    except ImportError:
        yield
        return

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(lock_path, 'w')
    deadline = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fp.close()
                raise TimeoutError(f"render lock contended for {timeout}s at {lock_path}")
            time.sleep(0.1)
    try:
        fp.write(str(os.getpid()))
        fp.flush()
        yield
    finally:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
        fp.close()
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def is_all_background(png_bytes: bytes) -> bool:
    """Histogram check: quantize each channel to 4 bits, count dominant bucket.
    Returns True only when the PNG is essentially monochrome (blank render)."""
    try:
        from PIL import Image
    except ImportError:
        # PIL not installed — skip this check, the rubric subagent will
        # re-validate visually.
        return False

    img = Image.open(io.BytesIO(png_bytes)).convert('RGB')
    pixels = img.getdata()
    total = img.width * img.height
    if total == 0:
        return True
    counts: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        key = (r >> 4, g >> 4, b >> 4)
        counts[key] = counts.get(key, 0) + 1
    dominant = max(counts.values())
    return dominant / total >= ALL_BG_THRESHOLD


def fetch_slide_content(server_url: str, page_name: str, timeout: float = 5.0) -> str:
    """Return the live-preview server's inlined SVG content for one slide."""
    url = f"{server_url.rstrip('/')}/api/slide/{urllib.parse.quote(page_name)}"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    content = payload.get('content') if isinstance(payload, dict) else None
    if not isinstance(content, str):
        raise RuntimeError(f'unexpected response shape from {url}: {payload!r}')
    return content


def _json_number(value: Decimal) -> int | float:
    """Keep integral canvas values compact while preserving fractional input."""
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def parse_slide_canvas(svg_content: str, page_name: str) -> dict:
    """Read the authoritative canvas from one inlined SVG root viewBox."""
    try:
        root = ET.fromstring(svg_content)
    except ET.ParseError as exc:
        raise ValueError(f'{page_name}: unable to parse root SVG: {exc}') from exc

    viewbox = parse_project_svg_root(root, context=page_name)
    width = _json_number(viewbox.width)
    height = _json_number(viewbox.height)
    return {
        'view_box': [_json_number(value) for value in viewbox.values],
        'width': width,
        'height': height,
        'png_width': math.ceil(float(viewbox.width)),
        'png_height': math.ceil(float(viewbox.height)),
    }


def render_pages(server_url: str, pages: list[str], preview_dir: Path) -> list[dict]:
    """Render all requested pages in a single browser session.

    Each render: page.goto(server_url) anchors the base URL so the SVG's
    relative <image href="../images/..."> resolves against the server.
    Then fetch the slide via the server's /api/slide endpoint (which inlines
    <use data-icon> references) and inject it as the document body.
    """
    from playwright.sync_api import sync_playwright

    preview_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []

    inject_js = """
({svgContent, width, height}) => {
    document.documentElement.innerHTML =
        '<head><style>html,body{margin:0;padding:0;background:#0E1116;overflow:hidden}'
        + ' svg{display:block;width:' + width + 'px;height:' + height + 'px}</style></head>'
        + '<body>' + svgContent + '</body>';
    return { len: svgContent.length };
}
"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context()
            for page_name in pages:
                rec: dict = {'page': page_name, 'ok': False}
                try:
                    svg_content = fetch_slide_content(server_url, page_name)
                    canvas = parse_slide_canvas(svg_content, page_name)
                    rec['canvas'] = canvas
                except urllib.error.URLError as e:
                    rec['error'] = f'server_unreachable: {e!r}'
                    records.append(rec)
                    continue
                except Exception as e:  # noqa: BLE001
                    rec['error'] = f'{type(e).__name__}: {e}'
                    records.append(rec)
                    continue

                stem = page_name[:-4] if page_name.endswith('.svg') else page_name
                out_path = preview_dir / f'{stem}.png'

                pg = None
                try:
                    pg = context.new_page()
                    pg.set_viewport_size({
                        'width': canvas['png_width'],
                        'height': canvas['png_height'],
                    })
                    pg.goto(server_url, wait_until='domcontentloaded')
                    pg.evaluate(inject_js, {
                        'svgContent': svg_content,
                        'width': canvas['width'],
                        'height': canvas['height'],
                    })
                    # Wait one frame so font/text shaping settles before capture.
                    pg.wait_for_timeout(100)
                    png_bytes = pg.screenshot(type='png', full_page=False)

                    out_path.write_bytes(png_bytes)
                    rec['path'] = str(out_path)
                    rec['bytes'] = len(png_bytes)
                    rec['all_background'] = is_all_background(png_bytes)
                    rec['ok'] = True
                except Exception as e:  # noqa: BLE001 — best-effort per-page
                    rec['error'] = f'{type(e).__name__}: {e}'
                finally:
                    if pg is not None:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001 — cleanup is best-effort
                            pass
                records.append(rec)
        finally:
            browser.close()

    return records


def discover_pages(project_path: Path, requested: list[str] | None) -> list[str]:
    svg_dir = project_path / 'svg_output'
    if not svg_dir.is_dir():
        raise FileNotFoundError(f'no svg_output/ in {project_path}')
    all_svgs = [path.name for path in discover_slide_svgs(svg_dir)]
    if not requested:
        return all_svgs
    selected: list[str] = []
    for token in requested:
        match = next((n for n in all_svgs if n.startswith(token) or n == token), None)
        if match is None:
            raise ValueError(f'no SVG matches token {token!r} in {svg_dir}')
        selected.append(match)
    return selected


def discover_server_url(project_path: Path) -> str:
    """Return the live-preview URL recorded for one project."""
    lock_paths = (
        project_path / 'live_preview' / 'lock.json',
        project_path / '.live_preview.lock',
    )
    for lock_path in lock_paths:
        lock = read_lock(lock_path)
        if not lock or not process_alive(lock_pid(lock)):
            continue
        try:
            port = int(lock.get('port', 0) or 0)
        except (TypeError, ValueError):
            port = 0
        if 1 <= port <= 65535:
            return f'http://127.0.0.1:{port}'
    raise RuntimeError(
        f'no running live-preview server recorded for project: {project_path}'
    )


def check_server(server_url: str, project_path: Path) -> None:
    """Require a live-preview server that belongs to the target project."""
    url = f"{server_url.rstrip('/')}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            if resp.status != 200:
                raise RuntimeError(f'{url} returned HTTP {resp.status}')
            data = json.load(resp)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise RuntimeError(f'live-preview server not reachable at {server_url}: {e}')
    expected_project = str(project_path)
    expected_svg_output = str((project_path / 'svg_output').resolve())
    service = data.get('service') if isinstance(data, dict) else None
    legacy_live_preview = (
        service is None
        and isinstance(data, dict)
        and data.get('svg_output') == expected_svg_output
    )
    if (
        not isinstance(data, dict)
        or data.get('project') != expected_project
        or (service != 'live_preview' and not legacy_live_preview)
    ):
        raise RuntimeError(
            f'URL does not belong to this project live preview: {server_url}'
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Render project SVGs to PNGs for visual review.',
    )
    parser.add_argument('project_path', help='Path to project directory (contains svg_output/)')
    parser.add_argument(
        '--pages', nargs='+', default=None,
        help='Page tokens to render (default: all SVGs in svg_output/). '
             "Accepts '02', '02_three_steps', or '02_three_steps.svg'.",
    )
    parser.add_argument(
        '--server-url', default=None,
        help='Explicit live-preview URL (default: discover it from the project lock)',
    )
    parser.add_argument(
        '--lock-timeout', type=float, default=30.0,
        help='Seconds to wait for render lock (default: 30)',
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        _safe_print(f'project path not found: {project_path}')
        return 2

    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        _safe_print(
            'playwright not installed. Install with:\n'
            '    pip install playwright\n'
            '    python3 -m playwright install chromium\n'
            '(see skills/ppt-master/requirements.txt)'
        )
        return 3

    try:
        server_url = args.server_url or discover_server_url(project_path)
        check_server(server_url, project_path)
    except RuntimeError as e:
        _safe_print(str(e))
        _safe_print(
            'start it with:\n'
            f'    python3 skills/ppt-master/scripts/svg_editor/server.py {project_path}'
        )
        return 2

    try:
        pages = discover_pages(project_path, args.pages)
    except (FileNotFoundError, ValueError) as e:
        _safe_print(str(e))
        return 2

    preview_dir = project_path / '.preview'
    lock_path = preview_dir / '.render.lock'

    with file_lock(lock_path, timeout=args.lock_timeout):
        try:
            records = render_pages(server_url, pages, preview_dir)
        except Exception as e:  # noqa: BLE001 — browser launch failure
            _safe_print(f'browser session failed: {type(e).__name__}: {e}')
            _safe_print(
                'try:  python3 -m playwright install chromium'
            )
            return 3

    for rec in records:
        if not rec['ok']:
            _safe_print(f"[FAIL] {rec['page']}: {rec.get('error')}")
        elif rec.get('all_background'):
            _safe_print(f"[WARN] {rec['page']}: PNG rendered but is all-background")

    summary = {
        'project': str(project_path),
        'server_url': server_url,
        'rendered': sum(1 for r in records if r['ok']),
        'failed': sum(1 for r in records if not r['ok']),
        'all_background': sum(1 for r in records if r.get('all_background')),
        'pages': records,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if summary['failed']:
        return 4
    return 0


if __name__ == '__main__':
    sys.exit(main())
