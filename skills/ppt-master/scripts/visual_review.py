#!/usr/bin/env python3
"""
PPT Master - Visual Review Renderer

Renders project SVGs to 1280x720 PNGs that match the live-preview browser view
(inlined <use data-icon>, resolved <image href>, full font fallback including CJK).
The pure renderer for the visual-review workflow — does not edit SVGs, does not
interpret the rubric.

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
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from console_encoding import configure_utf8_stdio

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
    pixels = list(img.getdata())
    total = len(pixels)
    if total == 0:
        return True
    counts: dict[tuple[int, int, int], int] = {}
    for r, g, b in pixels:
        key = (r >> 4, g >> 4, b >> 4)
        counts[key] = counts.get(key, 0) + 1
    dominant = max(counts.values())
    return dominant / total >= ALL_BG_THRESHOLD


def fetch_slide_text(server_url: str, page_name: str, timeout: float = 5.0) -> int:
    """Probe that the server can return the slide. Returns content length.
    Used only for failure detection — the actual fetch happens inside the
    browser via fetch() so the response is parsed by JS, not Python."""
    url = f"{server_url.rstrip('/')}/api/slide/{urllib.parse.quote(page_name)}"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    if 'content' not in payload:
        raise RuntimeError(f'unexpected response shape from {url}: {payload!r}')
    return len(payload['content'])


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
async (pageName) => {
    const res = await fetch('/api/slide/' + encodeURIComponent(pageName) + '?_=' + Date.now());
    if (!res.ok) throw new Error('fetch /api/slide/' + pageName + ' returned ' + res.status);
    const data = await res.json();
    document.documentElement.innerHTML =
        '<head><style>html,body{margin:0;padding:0;background:#0E1116;overflow:hidden}'
        + ' svg{display:block;width:1280px;height:720px}</style></head>'
        + '<body>' + data.content + '</body>';
    return { len: data.content.length };
}
"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            for page_name in pages:
                rec: dict = {'page': page_name, 'ok': False}
                try:
                    fetch_slide_text(server_url, page_name)
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

                try:
                    pg = context.new_page()
                    pg.goto(server_url, wait_until='domcontentloaded')
                    pg.evaluate(inject_js, page_name)
                    # Wait one frame so font/text shaping settles before capture.
                    pg.wait_for_timeout(100)
                    png_bytes = pg.screenshot(type='png', full_page=False)
                    pg.close()

                    out_path.write_bytes(png_bytes)
                    rec['ok'] = True
                    rec['path'] = str(out_path)
                    rec['bytes'] = len(png_bytes)
                    rec['all_background'] = is_all_background(png_bytes)
                except Exception as e:  # noqa: BLE001 — best-effort per-page
                    rec['error'] = f'{type(e).__name__}: {e}'
                records.append(rec)
        finally:
            browser.close()

    return records


def discover_pages(project_path: Path, requested: list[str] | None) -> list[str]:
    svg_dir = project_path / 'svg_output'
    if not svg_dir.is_dir():
        raise FileNotFoundError(f'no svg_output/ in {project_path}')
    all_svgs = sorted(p.name for p in svg_dir.glob('*.svg'))
    if not requested:
        return all_svgs
    selected: list[str] = []
    for token in requested:
        match = next((n for n in all_svgs if n.startswith(token) or n == token), None)
        if match is None:
            raise ValueError(f'no SVG matches token {token!r} in {svg_dir}')
        selected.append(match)
    return selected


def check_server(server_url: str) -> None:
    """Probe server liveness via /api/slides. Raises RuntimeError if down."""
    url = f"{server_url.rstrip('/')}/api/slides"
    try:
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            if resp.status != 200:
                raise RuntimeError(f'{url} returned HTTP {resp.status}')
    except urllib.error.URLError as e:
        raise RuntimeError(f'live-preview server not reachable at {server_url}: {e}')


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
        '--server-url', default='http://localhost:5050',
        help='Live-preview server URL (default: http://localhost:5050)',
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
        check_server(args.server_url)
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
            records = render_pages(args.server_url, pages, preview_dir)
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
        'server_url': args.server_url,
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
