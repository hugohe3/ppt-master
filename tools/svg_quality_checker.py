#!/usr/bin/env python3
"""
PPT Master - SVG 质量检查工具

检查 SVG 文件是否符合项目技术规范。

用法:
    python3 tools/svg_quality_checker.py <svg_file>
    python3 tools/svg_quality_checker.py <directory>
    python3 tools/svg_quality_checker.py --all examples
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

try:
    from project_utils import CANVAS_FORMATS
    from error_helper import ErrorHelper
except ImportError:
    print("警告: 无法导入依赖模块")
    CANVAS_FORMATS = {}
    ErrorHelper = None


class SVGQualityChecker:
    """SVG 质量检查器"""

    def __init__(self):
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0
        }
        self.issue_types = defaultdict(int)

    def check_file(self, svg_file: str, expected_format: str = None) -> Dict:
        """
        检查单个 SVG 文件

        Args:
            svg_file: SVG 文件路径
            expected_format: 期望的画布格式（如 'ppt169'）

        Returns:
            检查结果字典
        """
        svg_path = Path(svg_file)

        if not svg_path.exists():
            return {
                'file': str(svg_file),
                'exists': False,
                'errors': ['文件不存在'],
                'warnings': [],
                'passed': False
            }

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'passed': True
        }

        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. 检查 viewBox
            self._check_viewbox(content, result, expected_format)

            # 2. 检查禁用元素
            self._check_forbidden_elements(content, result)

            # 3. 检查字体
            self._check_fonts(content, result)

            # 4. 检查 width/height 与 viewBox 一致性
            self._check_dimensions(content, result)

            # 5. 检查文本换行方式
            self._check_text_elements(content, result)

            # 判断是否通过
            result['passed'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"读取文件失败: {e}")
            result['passed'] = False

        # 更新统计
        self.summary['total'] += 1
        if result['passed']:
            if result['warnings']:
                self.summary['warnings'] += 1
            else:
                self.summary['passed'] += 1
        else:
            self.summary['errors'] += 1

        # 统计问题类型
        for error in result['errors']:
            self.issue_types[self._categorize_issue(error)] += 1

        self.results.append(result)
        return result

    def _check_viewbox(self, content: str, result: Dict, expected_format: str = None):
        """检查 viewBox 属性"""
        viewbox_match = re.search(r'viewBox="([^"]+)"', content)

        if not viewbox_match:
            result['errors'].append("缺少 viewBox 属性")
            return

        viewbox = viewbox_match.group(1)
        result['info']['viewbox'] = viewbox

        # 检查格式
        if not re.match(r'0 0 \d+ \d+', viewbox):
            result['warnings'].append(f"viewBox 格式异常: {viewbox}")

        # 检查是否与期望格式匹配
        if expected_format and expected_format in CANVAS_FORMATS:
            expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']
            if viewbox != expected_viewbox:
                result['errors'].append(
                    f"viewBox 不匹配: 期望 '{expected_viewbox}', 实际 '{viewbox}'"
                )

    def _check_forbidden_elements(self, content: str, result: Dict):
        """检查禁用元素（黑名单）"""
        content_lower = content.lower()

        # ============================================================
        # 禁用元素黑名单 - PPT 不兼容
        # ============================================================

        # 裁剪 / 遮罩
        if '<clippath' in content_lower:
            result['errors'].append("检测到禁用的 <clipPath> 元素（PPT 不支持 SVG 裁剪路径）")
        if '<mask' in content_lower and '<mask>' not in content_lower:  # 排除纯文本 "mask"
            result['errors'].append("检测到禁用的 <mask> 元素（PPT 不支持 SVG 遮罩）")

        # 样式系统
        if '<style' in content_lower:
            result['errors'].append("检测到禁用的 <style> 元素（使用内联属性替代）")
        if re.search(r'\bclass\s*=', content):
            result['errors'].append("检测到禁用的 class 属性（使用内联样式替代）")
        if re.search(r'\bid\s*=', content):
            result['errors'].append("检测到禁用的 id 属性（使用内联样式替代）")
        if re.search(r'<\?xml-stylesheet\b', content_lower):
            result['errors'].append("检测到禁用的 xml-stylesheet（禁止引用外部 CSS）")
        if re.search(r'<link[^>]*rel\s*=\s*["\']stylesheet["\']', content_lower):
            result['errors'].append("检测到禁用的 <link rel=\"stylesheet\">（禁止引用外部 CSS）")
        if re.search(r'@import\s+', content_lower):
            result['errors'].append("检测到禁用的 @import（禁止引用外部 CSS）")

        # 结构 / 嵌套
        if '<foreignobject' in content_lower:
            result['errors'].append(
                "检测到禁用的 <foreignObject> 元素（使用 <tspan> 手动换行）")
        has_symbol = '<symbol' in content_lower
        has_use = re.search(r'<use\b', content_lower) is not None
        if has_symbol and has_use:
            result['errors'].append("检测到禁用的 <symbol> + <use> 复杂用法（请改用基础形状或简单 <use>）")
        if '<marker' in content_lower:
            result['errors'].append("检测到禁用的 <marker> 元素（PPT 不支持 SVG marker）")
        if re.search(r'\bmarker-end\s*=', content_lower):
            result['errors'].append("检测到禁用的 marker-end 属性（请用 line + polygon 代替）")

        # 文本 / 字体
        if '<textpath' in content_lower:
            result['errors'].append("检测到禁用的 <textPath> 元素（路径文本不兼容 PPT）")
        if '@font-face' in content_lower:
            result['errors'].append("检测到禁用的 @font-face（使用系统字体栈）")

        # 动画 / 交互
        if re.search(r'<animate', content_lower):
            result['errors'].append("检测到禁用的 SMIL 动画元素 <animate*>（SVG 动画不导出）")
        if re.search(r'<set\b', content_lower):
            result['errors'].append("检测到禁用的 SMIL 动画元素 <set>（SVG 动画不导出）")
        if '<script' in content_lower:
            result['errors'].append("检测到禁用的 <script> 元素（禁止脚本和事件处理）")
        if re.search(r'\bon\w+\s*=', content):  # onclick, onload 等
            result['errors'].append("检测到禁用的事件属性（如 onclick, onload）")

        # 其他不推荐的元素
        if '<iframe' in content_lower:
            result['errors'].append("检测到 <iframe> 元素（不应出现在 SVG 中）")
        if re.search(r'rgba\s*\(', content_lower):
            result['errors'].append("检测到禁用的 rgba() 颜色（请用 fill-opacity/stroke-opacity）")
        if re.search(r'<g[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("检测到禁用的 <g opacity>（请为子元素单独设置透明度）")
        if re.search(r'<image[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("检测到禁用的 <image opacity>（请使用遮罩层方案）")

    def _check_fonts(self, content: str, result: Dict):
        """检查字体使用"""
        # 查找 font-family 声明
        font_matches = re.findall(
            r'font-family[:\s]*["\']([^"\']+)["\']', content, re.IGNORECASE)

        if font_matches:
            result['info']['fonts'] = list(set(font_matches))

            # 检查是否使用了系统 UI 字体栈
            recommended_fonts = [
                'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI']

            for font_family in font_matches:
                has_recommended = any(
                    rec in font_family for rec in recommended_fonts)

                if not has_recommended:
                    result['warnings'].append(
                        f"建议使用系统 UI 字体栈，当前: {font_family}"
                    )
                    break  # 只警告一次

    def _check_dimensions(self, content: str, result: Dict):
        """检查 width/height 与 viewBox 的一致性"""
        width_match = re.search(r'width="(\d+)"', content)
        height_match = re.search(r'height="(\d+)"', content)

        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            result['info']['dimensions'] = f"{width}×{height}"

            # 检查是否与 viewBox 一致
            if 'viewbox' in result['info']:
                viewbox_parts = result['info']['viewbox'].split()
                if len(viewbox_parts) == 4:
                    vb_width, vb_height = viewbox_parts[2], viewbox_parts[3]
                    if width != vb_width or height != vb_height:
                        result['warnings'].append(
                            f"width/height ({width}×{height}) 与 viewBox "
                            f"({vb_width}×{vb_height}) 不一致"
                        )

    def _check_text_elements(self, content: str, result: Dict):
        """检查文本元素和换行方式"""
        # 统计 text 和 tspan 元素
        text_count = content.count('<text')
        tspan_count = content.count('<tspan')

        result['info']['text_elements'] = text_count
        result['info']['tspan_elements'] = tspan_count

        # 检查是否有过长的单行文本（可能需要换行）
        text_matches = re.findall(r'<text[^>]*>([^<]{100,})</text>', content)
        if text_matches:
            result['warnings'].append(
                f"检测到 {len(text_matches)} 个可能过长的单行文本（建议使用 tspan 换行）"
            )

    def _categorize_issue(self, error_msg: str) -> str:
        """分类问题类型"""
        if 'viewBox' in error_msg:
            return 'viewBox 问题'
        elif 'foreignObject' in error_msg:
            return 'foreignObject'
        elif '字体' in error_msg or 'font' in error_msg:
            return '字体问题'
        else:
            return '其他'

    def check_directory(self, directory: str, expected_format: str = None) -> List[Dict]:
        """
        检查目录下的所有 SVG 文件

        Args:
            directory: 目录路径
            expected_format: 期望的画布格式

        Returns:
            检查结果列表
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"[ERROR] 目录不存在: {directory}")
            return []

        # 查找所有 SVG 文件
        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            svg_output = dir_path / \
                'svg_output' if (
                    dir_path / 'svg_output').exists() else dir_path
            svg_files = sorted(svg_output.glob('*.svg'))

        if not svg_files:
            print(f"[WARN] 未找到 SVG 文件")
            return []

        print(f"\n[SCAN] 检查 {len(svg_files)} 个 SVG 文件...\n")

        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            self._print_result(result)

        return self.results

    def _print_result(self, result: Dict):
        """打印单个文件的检查结果"""
        if result['passed']:
            if result['warnings']:
                icon = "[WARN]"
                status = "通过（有警告）"
            else:
                icon = "[OK]"
                status = "通过"
        else:
            icon = "[ERROR]"
            status = "失败"

        print(f"{icon} {result['file']} - {status}")

        # 显示基本信息
        if result['info']:
            info_items = []
            if 'viewbox' in result['info']:
                info_items.append(f"viewBox: {result['info']['viewbox']}")
            if info_items:
                print(f"   {' | '.join(info_items)}")

        # 显示错误
        if result['errors']:
            for error in result['errors']:
                print(f"   [ERROR] {error}")

        # 显示警告
        if result['warnings']:
            for warning in result['warnings'][:2]:  # 只显示前2个警告
                print(f"   [WARN] {warning}")
            if len(result['warnings']) > 2:
                print(f"   ... 还有 {len(result['warnings']) - 2} 个警告")

        print()

    def print_summary(self):
        """打印检查摘要"""
        print("=" * 80)
        print("[SUMMARY] 检查摘要")
        print("=" * 80)

        print(f"\n总文件数: {self.summary['total']}")
        print(
            f"  [OK] 完全通过: {self.summary['passed']} ({self._percentage(self.summary['passed'])}%)")
        print(
            f"  [WARN] 有警告: {self.summary['warnings']} ({self._percentage(self.summary['warnings'])}%)")
        print(
            f"  [ERROR] 有错误: {self.summary['errors']} ({self._percentage(self.summary['errors'])}%)")

        if self.issue_types:
            print(f"\n问题分类:")
            for issue_type, count in sorted(self.issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count} 个")

        # 修复建议
        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print(f"\n[TIP] 常见修复方法:")
            print(f"  1. viewBox 问题: 确保与画布格式一致（参考 docs/canvas_formats.md）")
            print(f"  2. foreignObject: 改用 <text> + <tspan> 进行手动换行")
            print(f"  3. 字体问题: 使用系统 UI 字体栈")

    def _percentage(self, count: int) -> int:
        """计算百分比"""
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'svg_quality_report.txt'):
        """导出检查报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master SVG 质量检查报告\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "[OK] 通过" if result['passed'] else "[ERROR] 失败"
                f.write(f"{status} - {result['file']}\n")
                f.write(f"路径: {result.get('path', 'N/A')}\n")

                if result['info']:
                    f.write(f"信息: {result['info']}\n")

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
            f.write("检查摘要\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"总文件数: {self.summary['total']}\n")
            f.write(f"完全通过: {self.summary['passed']}\n")
            f.write(f"有警告: {self.summary['warnings']}\n")
            f.write(f"有错误: {self.summary['errors']}\n")

        print(f"\n[REPORT] 检查报告已导出: {output_file}")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("PPT Master - SVG 质量检查工具\n")
        print("用法:")
        print("  python3 tools/svg_quality_checker.py <svg_file>")
        print("  python3 tools/svg_quality_checker.py <directory>")
        print("  python3 tools/svg_quality_checker.py --all examples")
        print("\n示例:")
        print("  python3 tools/svg_quality_checker.py examples/project/svg_output/slide_01.svg")
        print("  python3 tools/svg_quality_checker.py examples/project/svg_output")
        print("  python3 tools/svg_quality_checker.py examples/project")
        sys.exit(0)

    checker = SVGQualityChecker()

    # 解析参数
    target = sys.argv[1]
    expected_format = None

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]

    # 执行检查
    if target == '--all':
        # 检查所有示例项目
        base_dir = sys.argv[2] if len(sys.argv) > 2 else 'examples'
        from project_utils import find_all_projects
        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"检查项目: {project.name}")
            print('=' * 80)
            checker.check_directory(str(project))
    else:
        checker.check_directory(target, expected_format)

    # 打印摘要
    checker.print_summary()

    # 导出报告（如果指定）
    if '--export' in sys.argv:
        output_file = 'svg_quality_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        checker.export_report(output_file)

    # 返回退出码
    if checker.summary['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
