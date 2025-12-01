#!/usr/bin/env python3
"""
PPT Master - Examples 索引生成工具

自动扫描 examples 目录并生成 README.md 索引文件。

用法:
    python3 tools/generate_examples_index.py
    python3 tools/generate_examples_index.py examples
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from project_utils import find_all_projects, get_project_info, CANVAS_FORMATS
except ImportError:
    print("错误: 无法导入 project_utils 模块")
    print("请确保 project_utils.py 在同一目录下")
    sys.exit(1)


def generate_examples_index(examples_dir: str = 'examples') -> str:
    """
    生成 examples 目录的 README.md 索引

    Args:
        examples_dir: examples 目录路径

    Returns:
        生成的 README.md 内容
    """
    examples_path = Path(examples_dir)

    if not examples_path.exists():
        print(f"❌ 目录不存在: {examples_dir}")
        return ""

    print(f"🔍 扫描目录: {examples_dir}")

    # 查找所有项目
    projects = find_all_projects(examples_dir)

    if not projects:
        print("⚠️  未找到任何项目")
        return ""

    print(f"找到 {len(projects)} 个项目")

    # 收集项目信息
    projects_info = []
    for project_path in projects:
        info = get_project_info(str(project_path))
        projects_info.append(info)

    # 按日期排序（最新的在前）
    projects_info.sort(key=lambda x: x['date'], reverse=True)

    # 按格式分组
    by_format = defaultdict(list)
    for info in projects_info:
        by_format[info['format']].append(info)

    # 生成 README 内容
    content = []
    content.append("# PPT Master 示例项目索引\n")
    content.append("> 本文件由 `tools/generate_examples_index.py` 自动生成\n")
    content.append(f"> 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 概览统计
    content.append("## 📊 概览\n")
    content.append(f"- **项目总数**: {len(projects_info)} 个")
    content.append(f"- **画布格式**: {len(by_format)} 种")

    total_svgs = sum(info['svg_count'] for info in projects_info)
    content.append(f"- **SVG 文件**: {total_svgs} 个")

    # 按格式统计
    content.append("\n### 格式分布\n")
    for fmt_key in sorted(by_format.keys(), key=lambda x: len(by_format[x]), reverse=True):
        count = len(by_format[fmt_key])
        fmt_name = CANVAS_FORMATS.get(fmt_key, {}).get('name', fmt_key)
        content.append(f"- **{fmt_name}**: {count} 个项目")

    # 最近更新
    content.append("\n## 🆕 最近更新\n")
    for info in projects_info[:5]:
        content.append(
            f"- **{info['name']}** ({info['format_name']}) - {info['date_formatted']}")

    # 按格式分类列表
    content.append("\n## 📁 项目列表\n")

    # 定义格式显示顺序
    format_order = ['ppt169', 'ppt43', 'wechat',
                    'xiaohongshu', 'moments', 'story', 'banner', 'a4']

    for fmt_key in format_order:
        if fmt_key not in by_format:
            continue

        fmt_info = CANVAS_FORMATS.get(fmt_key, {})
        fmt_name = fmt_info.get('name', fmt_key)
        dimensions = fmt_info.get('dimensions', '')

        content.append(f"\n### {fmt_name} ({dimensions})\n")

        projects_list = by_format[fmt_key]
        # 按日期排序
        projects_list.sort(key=lambda x: x['date'], reverse=True)

        for info in projects_list:
            # 项目名称和链接
            project_link = f"./{info['dir_name']}"

            # 构建项目条目
            line = f"- **[{info['name']}]({project_link})**"

            # 添加日期
            line += f" - {info['date_formatted']}"

            # 添加 SVG 数量
            line += f" - {info['svg_count']} 页"

            content.append(line)

    # 其他未分类的格式
    other_formats = set(by_format.keys()) - set(format_order)
    if other_formats:
        content.append("\n### 其他格式\n")
        for fmt_key in sorted(other_formats):
            projects_list = by_format[fmt_key]
            for info in projects_list:
                project_link = f"./{info['dir_name']}"
                line = f"- **[{info['name']}]({project_link})**"
                line += f" ({info['format_name']}) - {info['date_formatted']}"
                line += f" - {info['svg_count']} 页"
                content.append(line)

    # 使用说明
    content.append("\n## 📖 使用说明\n")
    content.append("### 预览项目\n")
    content.append("每个项目都包含以下文件：\n")
    content.append("- `README.md` - 项目说明文档")
    content.append("- `设计规范与内容大纲.md` - 完整设计规范")
    content.append("- `svg_output/` - SVG 输出文件\n")

    content.append("**方法 1: 使用 HTTP 服务器（推荐）**\n")
    content.append("```bash")
    content.append(
        "python3 -m http.server --directory examples/<project_name>/svg_output 8000")
    content.append("# 访问 http://localhost:8000")
    content.append("```\n")

    content.append("**方法 2: 直接打开 SVG**\n")
    content.append("```bash")
    content.append(
        "open examples/<project_name>/svg_output/slide_01_cover.svg")
    content.append("```\n")

    # 创建新项目
    content.append("### 创建新项目\n")
    content.append("参考现有项目结构，或使用项目管理工具：\n")
    content.append("```bash")
    content.append(
        "python3 tools/project_manager.py init my_project --format ppt169")
    content.append("```\n")

    # 贡献指南
    content.append("## 🤝 贡献示例项目\n")
    content.append("欢迎分享你的项目到 examples 目录！\n")
    content.append("### 项目要求\n")
    content.append("1. 遵循标准项目结构")
    content.append("2. 包含完整的 README.md 和设计规范")
    content.append("3. SVG 文件符合技术规范")
    content.append("4. 目录命名格式: `{项目名}_{格式}_{YYYYMMDD}`\n")

    content.append("### 提交流程\n")
    content.append("1. 在 `examples/` 目录下创建项目")
    content.append(
        "2. 验证项目: `python3 tools/project_manager.py validate examples/<project>`")
    content.append("3. 更新索引: `python3 tools/generate_examples_index.py`")
    content.append("4. 提交 Pull Request\n")

    # 相关资源
    content.append("## 📚 相关资源\n")
    content.append("- [快速开始](../README.md)")
    content.append("- [工作流教程](../docs/workflow_tutorial.md)")
    content.append("- [设计规范](../docs/design_guidelines.md)")
    content.append("- [画布格式](../docs/canvas_formats.md)")
    content.append("- [角色定义](../roles/README.md)")
    content.append("- [图表模板](../templates/charts/README.md)\n")

    # 页脚
    content.append("---\n")
    content.append(
        f"*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by PPT Master*")

    return "\n".join(content)


def main():
    """主函数"""
    examples_dir = 'examples'

    if len(sys.argv) > 1:
        examples_dir = sys.argv[1]

    print("=" * 80)
    print("PPT Master - Examples 索引生成工具")
    print("=" * 80 + "\n")

    # 生成索引内容
    content = generate_examples_index(examples_dir)

    if not content:
        print("\n❌ 生成失败")
        sys.exit(1)

    # 写入文件
    output_file = Path(examples_dir) / 'README.md'

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n✅ 索引文件已生成: {output_file}")
        print(f"   包含 {len(content.splitlines())} 行内容")

        # 显示统计信息
        projects_count = content.count('- **[')
        print(f"   索引了 {projects_count} 个项目")

    except Exception as e:
        print(f"\n❌ 写入文件失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
