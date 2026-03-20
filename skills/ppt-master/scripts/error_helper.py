#!/usr/bin/env python3
"""
PPT Master - 错误消息助手

提供友好的错误消息和具体的修复建议。
"""

from typing import Dict, List, Optional


class ErrorHelper:
    """错误消息助手"""

    # 错误类型和对应的修复建议
    ERROR_SOLUTIONS = {
        'missing_readme': {
            'message': '缺少 README.md 文件',
            'solutions': [
                '创建 README.md 文件，包含项目说明、使用方法等',
                '参考模板: examples/google_annual_report_ppt169_20251116/README.md',
                '或使用命令: cp examples/google_annual_report_ppt169_20251116/README.md <your_project>/'
            ],
            'severity': 'error'
        },
        'missing_spec': {
            'message': '缺少设计规范文件',
            'solutions': [
                '创建 设计规范与内容大纲.md 文件',
                '包含: 画布规格、配色方案、字体规范、布局规范、内容大纲',
                '参考 Strategist 角色生成的设计规范'
            ],
            'severity': 'warning'
        },
        'missing_svg_output': {
            'message': '缺少 svg_output 目录',
            'solutions': [
                '创建 svg_output 目录: mkdir svg_output',
                '将生成的 SVG 文件放入该目录',
                '确保 SVG 文件命名符合规范: slide_XX_name.svg'
            ],
            'severity': 'error'
        },
        'empty_svg_output': {
            'message': 'svg_output 目录为空',
            'solutions': [
                '使用 AI 角色（Executor）生成 SVG 文件',
                '将 SVG 文件保存到 svg_output 目录',
                '确保文件命名格式: slide_01_cover.svg, slide_02_content.svg 等'
            ],
            'severity': 'warning'
        },
        'invalid_svg_naming': {
            'message': 'SVG 文件命名不规范',
            'solutions': [
                '重命名 SVG 文件，使用格式: slide_XX_name.svg',
                'XX 为两位数字（01, 02, ...）',
                'name 使用英文或拼音，下划线分隔',
                '示例: slide_01_cover.svg, slide_02_overview.svg'
            ],
            'severity': 'warning'
        },
        'missing_project_date': {
            'message': '项目目录缺少日期后缀',
            'solutions': [
                '重命名项目目录，添加日期后缀: _YYYYMMDD',
                '格式: {项目名}_{格式}_{YYYYMMDD}',
                '示例: my_project_ppt169_20251116',
                '命令: mv old_name new_name_ppt169_20251116'
            ],
            'severity': 'warning'
        },
        'viewbox_mismatch': {
            'message': 'SVG viewBox 与画布格式不匹配',
            'solutions': [
                '检查 SVG 文件的 viewBox 属性',
                '确保与项目画布格式一致',
                'PPT 16:9 应为: viewBox="0 0 1280 720"',
                'PPT 4:3 应为: viewBox="0 0 1024 768"',
                '参考: references/canvas-formats.md'
            ],
            'severity': 'warning'
        },
        'multiple_viewboxes': {
            'message': '检测到多个不同的 viewBox 设置',
            'solutions': [
                '统一所有 SVG 文件的 viewBox',
                '同一项目的所有页面应使用相同的画布尺寸',
                '使用查找替换工具批量修正',
                '参考第一页的 viewBox 设置'
            ],
            'severity': 'warning'
        },
        'no_viewbox': {
            'message': 'SVG 文件缺少 viewBox 属性',
            'solutions': [
                '在 SVG 根元素添加 viewBox 属性',
                '格式: <svg viewBox="0 0 1280 720" ...>',
                '确保 width、height 与 viewBox 一致',
                '这是 SVG 生成的强制要求'
            ],
            'severity': 'error'
        },
        'foreignobject_detected': {
            'message': '检测到禁用的 <foreignObject> 元素',
            'solutions': [
                '移除 <foreignObject> 元素',
                '使用 <text> + <tspan> 进行手动换行',
                '这是项目的技术规范要求',
                '参考: references/design-guidelines.md'
            ],
            'severity': 'error'
        },
        'clippath_detected': {
            'message': '检测到禁用的 <clipPath> 元素',
            'solutions': [
                '移除 <clipPath> 元素',
                'PPT 不支持 SVG 裁剪路径',
                '使用基础形状组合替代裁剪效果'
            ],
            'severity': 'error'
        },
        'mask_detected': {
            'message': '检测到禁用的 <mask> 元素',
            'solutions': [
                '移除 <mask> 元素',
                'PPT 不支持 SVG 遮罩',
                '使用不透明度（opacity/fill-opacity）替代'
            ],
            'severity': 'error'
        },
        'style_element_detected': {
            'message': '检测到禁用的 <style> 元素',
            'solutions': [
                '移除 <style> 元素',
                '将 CSS 样式转换为内联属性',
                '例如: fill="#000" 而非 class="text-black"'
            ],
            'severity': 'error'
        },
        'class_attribute_detected': {
            'message': '检测到禁用的 class 属性',
            'solutions': [
                '移除所有 class 属性',
                '使用内联样式替代',
                '例如: fill="#000" stroke="#333" 直接写在元素上'
            ],
            'severity': 'error'
        },
        'id_attribute_detected': {
            'message': '检测到禁用的 id 属性',
            'solutions': [
                '移除所有 id 属性',
                '使用内联样式替代',
                '避免依赖选择器定位或样式复用'
            ],
            'severity': 'error'
        },
        'external_css_detected': {
            'message': '检测到禁用的外部 CSS 引用',
            'solutions': [
                '移除 <?xml-stylesheet?> 声明',
                '移除 <link rel="stylesheet"> 引用',
                '移除 @import 外部样式',
                '将样式改为内联属性'
            ],
            'severity': 'error'
        },
        'symbol_use_detected': {
            'message': '检测到禁用的 <symbol> + <use> 复杂用法',
            'solutions': [
                '将 <symbol> 展开为实际 SVG 代码',
                '避免 <symbol> + <use> 的复用结构',
                '需要图标时可直接嵌入 SVG 路径'
            ],
            'severity': 'error'
        },
        'marker_detected': {
            'message': '检测到禁用的 <marker> 元素',
            'solutions': [
                '移除 <marker> 定义',
                '使用 line + polygon 绘制箭头',
                '参考 AGENTS.md 的箭头绘制方案'
            ],
            'severity': 'error'
        },
        'marker_end_detected': {
            'message': '检测到禁用的 marker-end 属性',
            'solutions': [
                '移除 marker-end 属性',
                '使用 line + polygon 绘制箭头',
                '确保箭头方向与线条一致'
            ],
            'severity': 'error'
        },
        'rgba_detected': {
            'message': '检测到禁用的 rgba() 颜色',
            'solutions': [
                '将 rgba() 改为 hex + opacity 写法',
                '示例: fill="#FFFFFF" fill-opacity="0.1"',
                '描边使用 stroke-opacity'
            ],
            'severity': 'error'
        },
        'group_opacity_detected': {
            'message': '检测到禁用的 <g opacity>',
            'solutions': [
                '移除组级 opacity',
                '为每个子元素单独设置透明度',
                '使用 fill-opacity / stroke-opacity 控制'
            ],
            'severity': 'error'
        },
        'image_opacity_detected': {
            'message': '检测到禁用的 <image opacity>',
            'solutions': [
                '移除图片 opacity 属性',
                '添加遮罩层 <rect> 控制透明度',
                '确保遮罩颜色与背景一致'
            ],
            'severity': 'error'
        },
        'event_attribute_detected': {
            'message': '检测到禁用的事件属性',
            'solutions': [
                '移除 onclick/onload 等事件属性',
                'SVG 禁止脚本和事件处理',
                '交互请在 PPT 中实现'
            ],
            'severity': 'error'
        },
        'set_detected': {
            'message': '检测到禁用的 <set> 元素',
            'solutions': [
                '移除 <set> 元素',
                'SVG 动画不会导出到 PPT',
                '如需动画效果请在 PPT 中设置'
            ],
            'severity': 'error'
        },
        'iframe_detected': {
            'message': '检测到禁用的 <iframe> 元素',
            'solutions': [
                '移除 <iframe> 元素',
                'SVG 中不应嵌入外部页面'
            ],
            'severity': 'error'
        },
        'textpath_detected': {
            'message': '检测到禁用的 <textPath> 元素',
            'solutions': [
                '移除 <textPath> 元素',
                '路径文本不兼容 PPT',
                '使用普通 <text> 元素并手动调整位置'
            ],
            'severity': 'error'
        },
        'webfont_detected': {
            'message': '检测到禁用的 Web 字体 (@font-face)',
            'solutions': [
                '移除 @font-face 声明',
                '使用系统字体栈',
                'font-family: system-ui, -apple-system, sans-serif'
            ],
            'severity': 'error'
        },
        'animation_detected': {
            'message': '检测到禁用的 SMIL 动画元素',
            'solutions': [
                '移除所有 <animate>, <animateMotion>, <animateTransform> 等元素',
                'SVG 动画不会导出到 PPT',
                '如需动画效果，在 PPT 中使用 PPT 原生动画'
            ],
            'severity': 'error'
        },
        'script_detected': {
            'message': '检测到禁用的 <script> 元素',
            'solutions': [
                '移除 <script> 元素',
                '禁止脚本和事件处理',
                'SVG 中的 JavaScript 不会在 PPT 中执行'
            ],
            'severity': 'error'
        },
        'invalid_font': {
            'message': '使用了非标准字体',
            'solutions': [
                '使用系统 UI 字体栈',
                'font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
                '避免使用特定字体名称（如 Arial, Helvetica）',
                '确保跨平台兼容性'
            ],
            'severity': 'warning'
        }
    }

    @classmethod
    def get_solution(cls, error_type: str, context: Optional[Dict] = None) -> Dict:
        """
        获取错误的解决方案

        Args:
            error_type: 错误类型
            context: 上下文信息（可选）

        Returns:
            包含 message, solutions, severity 的字典
        """
        if error_type in cls.ERROR_SOLUTIONS:
            solution = cls.ERROR_SOLUTIONS[error_type].copy()

            # 根据上下文定制消息
            if context:
                solution = cls._customize_solution(solution, context)

            return solution

        # 未知错误类型
        return {
            'message': '未知错误',
            'solutions': ['请查看文档或联系维护者'],
            'severity': 'error'
        }

    @classmethod
    def _customize_solution(cls, solution: Dict, context: Dict) -> Dict:
        """
        根据上下文定制解决方案

        Args:
            solution: 原始解决方案
            context: 上下文信息

        Returns:
            定制后的解决方案
        """
        customized = solution.copy()

        # 根据项目路径定制
        if 'project_path' in context:
            project_path = context['project_path']
            customized['solutions'] = [
                s.replace('<project_path>', project_path).replace(
                    '<your_project>', project_path)
                for s in customized['solutions']
            ]

        # 根据文件名定制
        if 'file_name' in context:
            file_name = context['file_name']
            customized['message'] = f"{customized['message']}: {file_name}"

        # 根据期望值定制
        if 'expected' in context and 'actual' in context:
            customized['message'] += f" (期望: {context['expected']}, 实际: {context['actual']})"

        return customized

    @classmethod
    def format_error_message(cls, error_type: str, context: Optional[Dict] = None) -> str:
        """
        格式化错误消息（用于终端输出）

        Args:
            error_type: 错误类型
            context: 上下文信息

        Returns:
            格式化的错误消息字符串
        """
        solution = cls.get_solution(error_type, context)

        lines = []

        # 错误消息
        severity_icon = "❌" if solution['severity'] == 'error' else "⚠️ "
        lines.append(f"{severity_icon} {solution['message']}")

        # 解决方案
        if solution['solutions']:
            lines.append("\n💡 解决方案:")
            for i, sol in enumerate(solution['solutions'], 1):
                lines.append(f"   {i}. {sol}")

        return "\n".join(lines)

    @classmethod
    def print_error(cls, error_type: str, context: Optional[Dict] = None):
        """
        打印格式化的错误消息

        Args:
            error_type: 错误类型
            context: 上下文信息
        """
        print(cls.format_error_message(error_type, context))

    @classmethod
    def get_all_error_types(cls) -> List[str]:
        """获取所有支持的错误类型"""
        return list(cls.ERROR_SOLUTIONS.keys())

    @classmethod
    def print_help(cls):
        """打印所有错误类型和解决方案"""
        print("PPT Master - 错误类型和解决方案\n")
        print("=" * 80)

        for error_type, info in cls.ERROR_SOLUTIONS.items():
            print(f"\n【{error_type}】")
            print(f"消息: {info['message']}")
            print(f"严重性: {info['severity']}")
            print("解决方案:")
            for i, sol in enumerate(info['solutions'], 1):
                print(f"  {i}. {sol}")
            print("-" * 80)


def main():
    """主函数 - 用于测试"""
    import sys

    if len(sys.argv) > 1:
        error_type = sys.argv[1]
        context = {}

        # 解析上下文参数
        for arg in sys.argv[2:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                context[key] = value

        print(ErrorHelper.format_error_message(error_type, context))
    else:
        ErrorHelper.print_help()


if __name__ == '__main__':
    main()
