#!/usr/bin/env python3
"""Validate whether the project outline is execution-ready.

Usage:
    python3 tools/outline_quality_checker.py <project_path>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


SPEC_CANDIDATES = [
    "设计规范与内容大纲.md",
    "design_specification.md",
    "设计规范.md",
]

REQUIRED_SECTIONS = [
    "## 一、项目信息",
    "## 二、画布规范",
    "## 三、视觉主题",
    "## 四、排版体系",
    "## 五、布局原则",
    "## 六、图标使用规范",
    "## 七、图片资源清单",
    "## 八、内容大纲",
    "## 九、演讲备注要求",
    "## 十、技术约束提醒",
    "## 十一、设计检查清单",
    "## 十二、下一步",
]

REQUIRED_EXECUTION_MARKERS = [
    "### 执行补充（新增）",
    "#### 页面执行卡（新增，必须追加）",
    "### Executor 进入前补充检查（新增）",
]

REQUIRED_CARD_FIELDS = [
    "**页面目标**",
    "**页面结论**",
    "**必须使用的信息**",
    "**来源编号**",
    "**推荐布局**",
    "**文案结构**",
    "**备注要点**",
]

PLACEHOLDER_PATTERNS = [
    r"\[填写[^\]]*\]",
    r"\{[^{}]+\}",
    r"\[由 Strategist 根据源文档内容和页数规划继续添加更多页面，不得留空页\]",
]


def find_spec_file(project_path: Path) -> Path:
    for candidate in SPEC_CANDIDATES:
        path = project_path / candidate
        if path.exists():
            return path
    raise FileNotFoundError("未找到设计规范文件")


def find_missing_sections(content: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if section not in content]


def find_missing_markers(content: str) -> list[str]:
    return [marker for marker in REQUIRED_EXECUTION_MARKERS if marker not in content]


def extract_slide_cards(content: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"(^#### 页面执行卡（新增，必须追加）\n.*?)(?=^#### Slide\s+\d+\s*-|^\[由 Strategist|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    cards: list[tuple[str, str]] = []
    for index, match in enumerate(pattern.finditer(content), start=1):
        block = match.group(1).strip()
        cards.append((f"页面执行卡 #{index}", block))
    return cards


def contains_placeholder(text: str) -> bool:
    return any(re.search(pattern, text) for pattern in PLACEHOLDER_PATTERNS)


def validate_cards(cards: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not cards:
        errors.append("未找到任何页面执行卡（#### 页面执行卡（新增，必须追加））")
        return errors, warnings

    for title, block in cards:
        for field in REQUIRED_CARD_FIELDS:
            if field not in block:
                errors.append(f"{title} 缺少字段: {field}")

        if contains_placeholder(block):
            warnings.append(f"{title} 仍包含占位内容，请补齐")

        source_match = re.search(r"\*\*来源编号\*\*(.*?)(\n\*\*|\Z)", block, re.DOTALL)
        if source_match and "S" not in source_match.group(1):
            warnings.append(f"{title} 的来源编号未明确写出 S 编号")

    return errors, warnings


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    project_path = Path(sys.argv[1])
    if not project_path.exists():
        print(f"[ERROR] 项目路径不存在: {project_path}")
        sys.exit(1)

    try:
        spec_file = find_spec_file(project_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    content = spec_file.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend([f"缺少章节: {section}" for section in find_missing_sections(content)])
    errors.extend([f"缺少执行增强块: {marker}" for marker in find_missing_markers(content)])

    if contains_placeholder(content):
        warnings.append("文档仍包含模板占位符，请确认是否已全部替换")

    cards = extract_slide_cards(content)
    card_errors, card_warnings = validate_cards(cards)
    errors.extend(card_errors)
    warnings.extend(card_warnings)

    print(f"检查文件: {spec_file}")
    print("=" * 60)
    print(f"页面执行卡数量: {len(cards)}")

    if warnings:
        print("\n[WARN]")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\n[ERROR]")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("\n[OK] 大纲已达到可执行标准，可进入 Executor 阶段。")


if __name__ == "__main__":
    main()
