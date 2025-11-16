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
        'missing_date_suffix': {
            'message': '目录名缺少日期后缀',
            'solutions': [
                '重命名项目目录，添加日期后缀: _YYYYMMDD',
                '格式: {项目名}_{格式}_{YYYYMMDD}',
                '示例: my_project_ppt169_20251116',
                '命令: mv old_name new_name_ppt169_20251116'
            ],
            'severity': 'warning'
        },
        'missing_preview': {
            'message': '缺少 preview.html 预览文件',
            'solutions': [
                '使用预览生成工具: python3 tools/generate_preview.py <project_path>',
                '或批量生成: python3 tools/generate_preview.py --all examples',
                '预览文件可帮助快速查看所有 SVG 页面'
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
                '参考: docs/canvas_formats.md'
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
                '参考: docs/design_guidelines.md'
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
                s.replace('<project_path>', project_path).replace('<your_project>', project_path)
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

