#!/usr/bin/env python3
"""
PPT Master - 批量项目验证工具

一次性检查多个项目的结构完整性和规范性。

用法:
    python3 tools/batch_validate.py examples
    python3 tools/batch_validate.py projects
    python3 tools/batch_validate.py --all
    python3 tools/batch_validate.py examples projects
"""

import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

try:
    from project_utils import (
        find_all_projects,
        get_project_info,
        validate_project_structure,
        validate_svg_viewbox,
        CANVAS_FORMATS
    )
except ImportError:
    print("错误: 无法导入 project_utils 模块")
    print("请确保 project_utils.py 在同一目录下")
    sys.exit(1)


class BatchValidator:
    """批量验证器"""

    def __init__(self):
        self.results = []
        self.summary = {
            'total': 0,
            'valid': 0,
            'has_errors': 0,
            'has_warnings': 0,
            'missing_readme': 0,
            'missing_spec': 0,
            'svg_issues': 0
        }

    def validate_directory(self, directory: str, recursive: bool = False) -> List[Dict]:
        """
        验证目录下的所有项目

        Args:
            directory: 目录路径
            recursive: 是否递归查找子目录

        Returns:
            验证结果列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"❌ 目录不存在: {directory}")
            return []

        print(f"\n🔍 扫描目录: {directory}")
        print("=" * 80)

        projects = find_all_projects(directory)

        if not projects:
            print(f"⚠️  未找到任何项目")
            return []

        print(f"找到 {len(projects)} 个项目\n")

        for project_path in projects:
            self.validate_project(str(project_path))

        return self.results

    def validate_project(self, project_path: str) -> Dict:
        """
        验证单个项目

        Args:
            project_path: 项目路径

        Returns:
            验证结果字典
        """
        self.summary['total'] += 1

        # 获取项目信息
        info = get_project_info(project_path)

        # 验证项目结构
        is_valid, errors, warnings = validate_project_structure(project_path)

        # 验证 SVG viewBox
        svg_warnings = []
        if info['svg_files']:
            project_path_obj = Path(project_path)
            svg_files = [project_path_obj / 'svg_output' /
                         f for f in info['svg_files']]
            svg_warnings = validate_svg_viewbox(svg_files, info['format'])

        # 汇总结果
        result = {
            'path': project_path,
            'name': info['name'],
            'format': info['format_name'],
            'date': info['date_formatted'],
            'svg_count': info['svg_count'],
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings + svg_warnings,
            'has_readme': info['has_readme'],
            'has_spec': info['has_spec']
        }

        self.results.append(result)

        # 更新统计
        if is_valid and not warnings and not svg_warnings:
            self.summary['valid'] += 1
            status = "✅"
        elif errors:
            self.summary['has_errors'] += 1
            status = "❌"
        else:
            self.summary['has_warnings'] += 1
            status = "⚠️ "

        if not info['has_readme']:
            self.summary['missing_readme'] += 1
        if not info['has_spec']:
            self.summary['missing_spec'] += 1
        if svg_warnings:
            self.summary['svg_issues'] += 1

        # 打印结果
        print(f"{status} {info['name']}")
        print(f"   路径: {project_path}")
        print(
            f"   格式: {info['format_name']} | SVG: {info['svg_count']} 个 | 日期: {info['date_formatted']}")

        if errors:
            print(f"   ❌ 错误 ({len(errors)}):")
            for error in errors:
                print(f"      - {error}")

        if warnings or svg_warnings:
            all_warnings = warnings + svg_warnings
            print(f"   ⚠️  警告 ({len(all_warnings)}):")
            for warning in all_warnings[:3]:  # 只显示前3个警告
                print(f"      - {warning}")
            if len(all_warnings) > 3:
                print(f"      ... 还有 {len(all_warnings) - 3} 个警告")

        print()

        return result

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 80)
        print("📊 验证摘要")
        print("=" * 80)

        print(f"\n总项目数: {self.summary['total']}")
        print(
            f"  ✅ 完全合格: {self.summary['valid']} ({self._percentage(self.summary['valid'])}%)")
        print(
            f"  ⚠️  有警告: {self.summary['has_warnings']} ({self._percentage(self.summary['has_warnings'])}%)")
        print(
            f"  ❌ 有错误: {self.summary['has_errors']} ({self._percentage(self.summary['has_errors'])}%)")

        print(f"\n常见问题:")
        print(f"  缺少 README.md: {self.summary['missing_readme']} 个项目")
        print(f"  缺少设计规范: {self.summary['missing_spec']} 个项目")
        print(f"  SVG 格式问题: {self.summary['svg_issues']} 个项目")

        # 按格式分组统计
        format_stats = defaultdict(int)
        for result in self.results:
            format_stats[result['format']] += 1

        if format_stats:
            print(f"\n画布格式分布:")
            for fmt, count in sorted(format_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {fmt}: {count} 个项目")

        # 提供修复建议
        if self.summary['has_errors'] > 0 or self.summary['has_warnings'] > 0:
            print(f"\n💡 修复建议:")

            if self.summary['missing_readme'] > 0:
                print(f"  1. 为缺少 README 的项目创建说明文档")
                print(
                    f"     参考: examples/google_annual_report_ppt169_20251116/README.md")

            if self.summary['svg_issues'] > 0:
                print(f"  2. 检查并修复 SVG viewBox 设置")
                print(f"     确保与画布格式一致")

            if self.summary['missing_spec'] > 0:
                print(f"  3. 补充设计规范文件")
                print(f"     文件名: 设计规范与内容大纲.md")

    def _percentage(self, count: int) -> int:
        """计算百分比"""
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'validation_report.txt'):
        """
        导出验证报告到文件

        Args:
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master 项目验证报告\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "✅ 合格" if result['is_valid'] and not result['warnings'] else \
                    "❌ 错误" if result['errors'] else "⚠️  警告"

                f.write(f"{status} - {result['name']}\n")
                f.write(f"路径: {result['path']}\n")
                f.write(
                    f"格式: {result['format']} | SVG: {result['svg_count']} 个\n")

                if result['errors']:
                    f.write(f"\n错误:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")

                if result['warnings']:
                    f.write(f"\n警告:\n")
                    for warning in result['warnings']:
                        f.write(f"  - {warning}\n")

                f.write("\n" + "-" * 80 + "\n\n")

            # 写入摘要
            f.write("\n" + "=" * 80 + "\n")
            f.write("验证摘要\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"总项目数: {self.summary['total']}\n")
            f.write(f"完全合格: {self.summary['valid']}\n")
            f.write(f"有警告: {self.summary['has_warnings']}\n")
            f.write(f"有错误: {self.summary['has_errors']}\n")

        print(f"\n📄 验证报告已导出: {output_file}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("PPT Master - 批量项目验证工具\n")
        print("用法:")
        print("  python3 tools/batch_validate.py <directory>")
        print("  python3 tools/batch_validate.py <dir1> <dir2> ...")
        print("  python3 tools/batch_validate.py --all")
        print("\n示例:")
        print("  python3 tools/batch_validate.py examples")
        print("  python3 tools/batch_validate.py projects")
        print("  python3 tools/batch_validate.py examples projects")
        print("  python3 tools/batch_validate.py --all")
        sys.exit(0)

    validator = BatchValidator()

    # 处理参数
    if '--all' in sys.argv:
        directories = ['examples', 'projects']
    else:
        directories = [arg for arg in sys.argv[1:] if not arg.startswith('--')]

    # 验证每个目录
    for directory in directories:
        if Path(directory).exists():
            validator.validate_directory(directory)
        else:
            print(f"⚠️  跳过不存在的目录: {directory}\n")

    # 打印摘要
    validator.print_summary()

    # 导出报告（如果指定）
    if '--export' in sys.argv:
        output_file = 'validation_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        validator.export_report(output_file)

    # 返回退出码
    if validator.summary['has_errors'] > 0:
        sys.exit(1)
    elif validator.summary['has_warnings'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
