#!/usr/bin/env python3
"""Build reusable PPT-style and analysis-style contact sheets.

The source catalogs remain authoritative. Run this script after adding or
removing a visual style, preview, analysis style, or analysis domain.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
STYLE_CATALOG = SKILL_DIR / "scripts" / "confirm_ui" / "static" / "catalogs.json"
STYLE_PREVIEWS = SKILL_DIR / "scripts" / "confirm_ui" / "static" / "style_previews"
ANALYSIS_DIR = SKILL_DIR / "templates" / "analysis-library" / "diagram-prompt-building"
ANALYSIS_STYLES = ANALYSIS_DIR / "styles.json"
ANALYSIS_TYPES = ANALYSIS_DIR / "analysis_types.json"
DEFAULT_OUTPUT = SKILL_DIR / "assets" / "contact-sheets"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def svg_data_uri(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{payload}"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_sheet(
    *,
    title: str,
    subtitle: str,
    items: list[dict],
    output: Path,
    columns: int = 3,
) -> tuple[int, int]:
    card_w, card_h = 680, 470
    gap_x, gap_y = 28, 30
    margin_x, header_h, footer_h = 36, 150, 70
    rows = (len(items) + columns - 1) // columns
    width = margin_x * 2 + columns * card_w + (columns - 1) * gap_x
    height = header_h + rows * card_h + max(0, rows - 1) * gap_y + footer_h

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F3F1EC"/>',
        f'<text x="{margin_x}" y="62" font-family="Microsoft YaHei, Arial, sans-serif" font-size="38" font-weight="700" fill="#171717">{esc(title)}</text>',
        f'<text x="{margin_x}" y="105" font-family="Microsoft YaHei, Arial, sans-serif" font-size="21" fill="#5D5A54">{esc(subtitle)}</text>',
    ]

    for index, item in enumerate(items, start=1):
        row, col = divmod(index - 1, columns)
        x = margin_x + col * (card_w + gap_x)
        y = header_h + row * (card_h + gap_y)
        preview = Path(item["preview"])
        if not preview.is_file():
            raise FileNotFoundError(f"Missing preview for {item['id']}: {preview}")
        label = item.get("label_zh") or item.get("name_zh") or item["id"]
        group = item.get("group_zh", "")
        body.extend(
            [
                f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="18" fill="#FFFFFF" stroke="#D8D3C8" stroke-width="2"/>',
                f'<rect x="{x + 20}" y="{y + 20}" width="{card_w - 40}" height="360" rx="10" fill="#E9E6DF"/>',
                f'<image x="{x + 20}" y="{y + 20}" width="{card_w - 40}" height="360" preserveAspectRatio="xMidYMid meet" href="{svg_data_uri(preview)}"/>',
                f'<circle cx="{x + 50}" cy="{y + 417}" r="25" fill="#111111"/>',
                f'<text x="{x + 50}" y="{y + 425}" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#FFFFFF">{index:02d}</text>',
                f'<text x="{x + 88}" y="{y + 414}" font-family="Microsoft YaHei, Arial, sans-serif" font-size="24" font-weight="700" fill="#171717">{esc(label)}</text>',
                f'<text x="{x + 88}" y="{y + 444}" font-family="Arial, Microsoft YaHei, sans-serif" font-size="17" fill="#6B675F">{esc(item["id"])}{(" · " + esc(group)) if group else ""}</text>',
            ]
        )

    body.extend(
        [
            f'<text x="{margin_x}" y="{height - 24}" font-family="Microsoft YaHei, Arial, sans-serif" font-size="17" fill="#77736B">选择时回复编号或 id；新增目录项后重新运行 scripts/build_contact_sheets.py 即可更新。</text>',
            "</svg>",
        ]
    )
    output.write_text("\n".join(body), encoding="utf-8")
    return width, height


def find_browser(explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate if candidate.is_file() else None
    for command in ("msedge", "chrome", "chromium", "chromium-browser"):
        found = shutil.which(command)
        if found:
            return Path(found)
    if __import__("os").name == "nt":
        candidates = [
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ]
        return next((path for path in candidates if path.is_file()), None)
    return None


def rasterize(svg_path: Path, width: int, height: int, browser: Path) -> Path:
    png_path = svg_path.with_suffix(".png")
    with tempfile.TemporaryDirectory(prefix="ppt-master-contact-sheet-") as profile:
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--screenshot={png_path}",
            svg_path.resolve().as_uri(),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    if completed.returncode != 0 or not png_path.is_file():
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"Browser PNG export failed: {detail}")
    return png_path


def write_analysis_domains(output: Path, catalog: dict) -> None:
    descriptions = {
        "architecture": "建筑体量、立面、空间与场地关系",
        "interior": "室内功能、动线、体验与环境分区",
        "landscape": "景观生态、视线、活动与场景序列",
        "planning": "城市形态、公共空间、交通与开发关系",
    }
    lines = [
        "# 专业分析图大类选择",
        "",
        "> 先选择一个大类；随后系统会完整列出该类全部分析图，默认全选，并等待用户确认全部或说明需要排除的编号。",
        "",
    ]
    for domain in catalog.get("domains", []):
        domain_id = domain["id"]
        lines.append(
            f"- `{domain_id}` {domain.get('name_zh', domain_id)}："
            f"{descriptions.get(domain_id, '由素材内容决定具体分析方向')}"
        )
    lines.extend(
        [
            "",
            "完整清单、数量和稳定编号来自 `analysis_types.json`；不得根据素材自动筛减。",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-png", action="store_true", help="Generate SVG and Markdown only")
    parser.add_argument("--browser", help="Explicit Edge/Chrome executable for PNG export")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    catalogs = read_json(STYLE_CATALOG)
    ppt_items = []
    for group in catalogs.get("visual_styles", []):
        for item in group.get("items", []):
            ppt_items.append(
                {
                    **item,
                    "group_zh": group.get("group_zh", group.get("group", "")),
                    "preview": STYLE_PREVIEWS / f"{item['id']}.svg",
                }
            )

    analysis_catalog = read_json(ANALYSIS_STYLES)
    analysis_items = [
        {**item, "preview": ANALYSIS_DIR / item["preview"]}
        for item in analysis_catalog.get("styles", [])
    ]

    ppt_svg = output_dir / "ppt_visual_styles.svg"
    analysis_svg = output_dir / "analysis_visual_styles.svg"
    ppt_size = build_sheet(
        title="PPT 视觉风格选择册",
        subtitle=f"{len(ppt_items)} 种已注册风格 · 编号按 catalogs.json 顺序自动生成",
        items=ppt_items,
        output=ppt_svg,
    )
    analysis_size = build_sheet(
        title="专业分析图风格选择册",
        subtitle=f"{len(analysis_items)} 种统一住宅体量案例预览 · 编号按 styles.json 顺序自动生成",
        items=analysis_items,
        output=analysis_svg,
    )
    write_analysis_domains(output_dir / "analysis_domains.md", read_json(ANALYSIS_TYPES))

    generated = [ppt_svg, analysis_svg, output_dir / "analysis_domains.md"]
    if not args.no_png:
        browser = find_browser(args.browser)
        if browser:
            generated.extend(
                [
                    rasterize(ppt_svg, *ppt_size, browser),
                    rasterize(analysis_svg, *analysis_size, browser),
                ]
            )
        else:
            print("[WARN] Edge/Chrome not found; SVG contact sheets were generated without PNG copies.")

    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
