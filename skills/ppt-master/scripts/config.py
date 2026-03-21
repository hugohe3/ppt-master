#!/usr/bin/env python3
"""
PPT Master - 统一配置管理模块

集中管理项目的所有配置项，确保配置的一致性和可维护性。

用法:
    from config import Config, CANVAS_FORMATS, DESIGN_COLORS
    
    # 获取画布格式
    ppt169 = Config.get_canvas_format('ppt169')
    
    # 获取配色方案
    colors = Config.get_color_scheme('consulting')
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json


# ============================================================
# 路径配置
# ============================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 核心目录
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
REFERENCES_DIR = PROJECT_ROOT / 'references'
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
WORKFLOWS_DIR = PROJECT_ROOT / 'workflows'

# 仓库根目录
REPO_ROOT = PROJECT_ROOT.parent.parent
EXAMPLES_DIR = REPO_ROOT / 'examples'
PROJECTS_DIR = REPO_ROOT / 'projects'

# 模板子目录
CHART_TEMPLATES_DIR = TEMPLATES_DIR / 'charts'


# ============================================================
# 画布格式配置
# ============================================================

CANVAS_FORMATS = {
    'ppt169': {
        'name': 'PPT 16:9',
        'dimensions': '1280×720',
        'viewbox': '0 0 1280 720',
        'width': 1280,
        'height': 720,
        'aspect_ratio': '16:9',
        'use_case': '现代投影设备、在线演示'
    },
    'ppt43': {
        'name': 'PPT 4:3',
        'dimensions': '1024×768',
        'viewbox': '0 0 1024 768',
        'width': 1024,
        'height': 768,
        'aspect_ratio': '4:3',
        'use_case': '传统投影设备'
    },
    'wechat': {
        'name': '微信公众号头图',
        'dimensions': '900×383',
        'viewbox': '0 0 900 383',
        'width': 900,
        'height': 383,
        'aspect_ratio': '2.35:1',
        'use_case': '公众号文章配图'
    },
    'xiaohongshu': {
        'name': '小红书',
        'dimensions': '1242×1660',
        'viewbox': '0 0 1242 1660',
        'width': 1242,
        'height': 1660,
        'aspect_ratio': '3:4',
        'use_case': '知识分享、产品种草'
    },
    'moments': {
        'name': '朋友圈/Instagram',
        'dimensions': '1080×1080',
        'viewbox': '0 0 1080 1080',
        'width': 1080,
        'height': 1080,
        'aspect_ratio': '1:1',
        'use_case': '社交媒体方形图片'
    },
    'story': {
        'name': 'Story/竖版',
        'dimensions': '1080×1920',
        'viewbox': '0 0 1080 1920',
        'width': 1080,
        'height': 1920,
        'aspect_ratio': '9:16',
        'use_case': '短视频封面、快拍'
    },
    'banner': {
        'name': '横版 Banner',
        'dimensions': '1920×1080',
        'viewbox': '0 0 1920 1080',
        'width': 1920,
        'height': 1080,
        'aspect_ratio': '16:9',
        'use_case': '网页横幅、大屏展示'
    },
    'a4': {
        'name': 'A4 打印',
        'dimensions': '1240×1754',
        'viewbox': '0 0 1240 1754',
        'width': 1240,
        'height': 1754,
        'aspect_ratio': '√2:1',
        'use_case': '打印文档、PDF导出'
    }
}


# ============================================================
# 设计配色配置
# ============================================================

DESIGN_COLORS = {
    'consulting': {
        'name': '咨询风格',
        'primary': '#005587',
        'secondary': '#0076A8',
        'accent': '#F5A623',
        'success': '#27AE60',
        'warning': '#E74C3C',
        'text_dark': '#1A252F',
        'text_light': '#FFFFFF',
        'text_muted': '#7F8C8D',
        'background': '#FFFFFF',
        'background_alt': '#F8F9FA'
    },
    'general': {
        'name': '通用灵活风格',
        'primary': '#2196F3',
        'secondary': '#4CAF50',
        'accent': '#FF9800',
        'purple': '#9C27B0',
        'success': '#27AE60',
        'warning': '#E74C3C',
        'text_dark': '#2C3E50',
        'text_light': '#FFFFFF',
        'text_muted': '#7F8C8D',
        'background': '#FFFFFF',
        'background_alt': '#F8F9FA'
    },
    'tech': {
        'name': '科技风格',
        'primary': '#00D1FF',
        'secondary': '#7B61FF',
        'accent': '#00FF88',
        'success': '#00FF88',
        'warning': '#FF6B6B',
        'text_dark': '#0A0E17',
        'text_light': '#FFFFFF',
        'text_muted': '#8892A0',
        'background': '#0A0E17',
        'background_alt': '#1A1F2E'
    },
    'academic': {
        'name': '学术规范风格',
        'primary': '#8B0000',
        'secondary': '#1E3A5F',
        'accent': '#C9B037',
        'success': '#2E7D32',
        'warning': '#D32F2F',
        'text_dark': '#1A1A1A',
        'text_light': '#FFFFFF',
        'text_muted': '#666666',
        'background': '#FFFFFF',
        'background_alt': '#F5F5F5'
    },
    'government': {
        'name': '政务风格',
        'primary': '#C41E3A',
        'secondary': '#1E3A5F',
        'accent': '#D4AF37',
        'success': '#2E7D32',
        'warning': '#B71C1C',
        'text_dark': '#1A1A1A',
        'text_light': '#FFFFFF',
        'text_muted': '#555555',
        'background': '#FFFFFF',
        'background_alt': '#FFF8E1'
    }
}


# ============================================================
# 行业配色模板
# ============================================================

INDUSTRY_COLORS = {
    'finance': {
        'name': '金融/银行',
        'primary': '#003366',
        'secondary': '#4A90D9',
        'accent': '#D4AF37'
    },
    'healthcare': {
        'name': '医疗/健康',
        'primary': '#00796B',
        'secondary': '#4DB6AC',
        'accent': '#FF7043'
    },
    'technology': {
        'name': '科技/互联网',
        'primary': '#1565C0',
        'secondary': '#42A5F5',
        'accent': '#00E676'
    },
    'education': {
        'name': '教育/培训',
        'primary': '#5E35B1',
        'secondary': '#7E57C2',
        'accent': '#FFD54F'
    },
    'retail': {
        'name': '零售/消费',
        'primary': '#E53935',
        'secondary': '#EF5350',
        'accent': '#FFB300'
    },
    'manufacturing': {
        'name': '制造/工业',
        'primary': '#455A64',
        'secondary': '#78909C',
        'accent': '#FF6F00'
    },
    'energy': {
        'name': '能源/环保',
        'primary': '#2E7D32',
        'secondary': '#66BB6A',
        'accent': '#FDD835'
    },
    'realestate': {
        'name': '房地产/建筑',
        'primary': '#795548',
        'secondary': '#A1887F',
        'accent': '#4CAF50'
    },
    'legal': {
        'name': '法律/合规',
        'primary': '#37474F',
        'secondary': '#546E7A',
        'accent': '#8D6E63'
    },
    'media': {
        'name': '媒体/娱乐',
        'primary': '#7B1FA2',
        'secondary': '#AB47BC',
        'accent': '#FF4081'
    },
    'logistics': {
        'name': '物流/供应链',
        'primary': '#F57C00',
        'secondary': '#FFB74D',
        'accent': '#0288D1'
    },
    'agriculture': {
        'name': '农业/食品',
        'primary': '#558B2F',
        'secondary': '#8BC34A',
        'accent': '#FFCA28'
    },
    'tourism': {
        'name': '旅游/酒店',
        'primary': '#00ACC1',
        'secondary': '#4DD0E1',
        'accent': '#FF7043'
    },
    'automotive': {
        'name': '汽车/交通',
        'primary': '#263238',
        'secondary': '#455A64',
        'accent': '#D32F2F'
    }
}


# ============================================================
# 字体配置
# ============================================================

FONTS = {
    'system_ui': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    'sans_serif': "'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
    'monospace': "'SF Mono', Monaco, Consolas, 'Liberation Mono', monospace"
}

FONT_SIZES = {
    'title_large': 48,
    'title': 36,
    'title_small': 28,
    'heading': 24,
    'subheading': 20,
    'body': 18,
    'body_small': 16,
    'caption': 14,
    'footnote': 12
}


# ============================================================
# 布局配置
# ============================================================

LAYOUT_MARGINS = {
    'ppt169': {
        'top': 60,
        'right': 60,
        'bottom': 60,
        'left': 60,
        'content_width': 1160,
        'content_height': 600
    },
    'xiaohongshu': {
        'top': 80,
        'right': 60,
        'bottom': 80,
        'left': 60,
        'content_width': 1122,
        'content_height': 1500
    },
    'moments': {
        'top': 60,
        'right': 60,
        'bottom': 60,
        'left': 60,
        'content_width': 960,
        'content_height': 960
    }
}


# ============================================================
# SVG 技术规范
# ============================================================

SVG_CONSTRAINTS = {
    # 禁用元素 - PPT 不兼容
    'forbidden_elements': [
        # 裁剪 / 遮罩
        'clipPath',
        'mask',
        # 样式系统
        'style',
        # 结构 / 嵌套
        'foreignObject',
        'marker',
        # 文本 / 字体
        'textPath',
        # 动画 / 交互
        'animate',
        'animateMotion',
        'animateTransform',
        'animateColor',
        'set',
        'script',
        # 其他
        'iframe',
    ],
    # 禁用属性
    'forbidden_attributes': [
        'class',
        'id',
        'onclick', 'onload', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange',
        'marker-end',
    ],
    # 禁用模式（正则匹配）
    'forbidden_patterns': [
        r'@font-face',  # Web 字体
        r'rgba\s*\(',   # rgba 颜色（PPT 不兼容）
        r'<\?xml-stylesheet\b',  # 外部 CSS
        r'<link[^>]*rel\s*=\s*["\']stylesheet["\']',
        r'@import\s+',  # 外部 CSS
        r'<g[^>]*\sopacity\s*=',  # 组透明度
        r'<image[^>]*\sopacity\s*=',  # 图片透明度
        r'\bon\w+\s*=',  # 事件属性
        r'(?s)(?=.*<symbol)(?=.*<use\b)',  # <symbol> + <use> 复杂用法（顺序无关）
    ],
    'recommended_fonts': [
        'system-ui',
        '-apple-system',
        'BlinkMacSystemFont',
        'Segoe UI'
    ]
}


# ============================================================
# 配置管理类
# ============================================================

class Config:
    """配置管理器"""

    @staticmethod
    def get_canvas_format(format_key: str) -> Optional[Dict]:
        """
        获取画布格式配置

        Args:
            format_key: 格式键名（如 'ppt169', 'xiaohongshu'）

        Returns:
            格式配置字典，不存在则返回 None
        """
        return CANVAS_FORMATS.get(format_key)

    @staticmethod
    def get_all_canvas_formats() -> Dict:
        """获取所有画布格式"""
        return CANVAS_FORMATS.copy()

    @staticmethod
    def get_color_scheme(style: str) -> Optional[Dict]:
        """
        获取配色方案

        Args:
            style: 风格名称（如 'consulting', 'general', 'tech'）

        Returns:
            配色方案字典
        """
        return DESIGN_COLORS.get(style)

    @staticmethod
    def get_industry_colors(industry: str) -> Optional[Dict]:
        """
        获取行业配色

        Args:
            industry: 行业名称（如 'finance', 'healthcare'）

        Returns:
            行业配色字典
        """
        return INDUSTRY_COLORS.get(industry)

    @staticmethod
    def get_all_industries() -> List[str]:
        """获取所有行业列表"""
        return list(INDUSTRY_COLORS.keys())

    @staticmethod
    def get_layout_margins(format_key: str) -> Optional[Dict]:
        """
        获取布局边距配置

        Args:
            format_key: 格式键名

        Returns:
            边距配置字典
        """
        return LAYOUT_MARGINS.get(format_key)

    @staticmethod
    def get_font(font_type: str = 'system_ui') -> str:
        """
        获取字体声明

        Args:
            font_type: 字体类型（'system_ui', 'sans_serif', 'monospace'）

        Returns:
            字体声明字符串
        """
        return FONTS.get(font_type, FONTS['system_ui'])

    @staticmethod
    def get_font_size(size_name: str) -> int:
        """
        获取字体大小

        Args:
            size_name: 大小名称（如 'title', 'body', 'caption'）

        Returns:
            字体大小（像素）
        """
        return FONT_SIZES.get(size_name, FONT_SIZES['body'])

    @staticmethod
    def validate_svg_element(element_name: str) -> bool:
        """
        验证 SVG 元素是否允许使用

        Args:
            element_name: 元素名称

        Returns:
            是否允许使用
        """
        return element_name.lower() not in [e.lower() for e in SVG_CONSTRAINTS['forbidden_elements']]

    @staticmethod
    def get_project_path(subdir: str = '') -> Path:
        """
        获取项目路径

        Args:
            subdir: 子目录名称

        Returns:
            完整路径
        """
        if subdir:
            return PROJECT_ROOT / subdir
        return PROJECT_ROOT

    @staticmethod
    def export_config(output_file: str = 'config_export.json'):
        """
        导出配置为 JSON 文件

        Args:
            output_file: 输出文件路径
        """
        config_data = {
            'canvas_formats': CANVAS_FORMATS,
            'design_colors': DESIGN_COLORS,
            'industry_colors': INDUSTRY_COLORS,
            'fonts': FONTS,
            'font_sizes': FONT_SIZES,
            'svg_constraints': SVG_CONSTRAINTS
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        print(f"配置已导出到: {output_file}")


# ============================================================
# 命令行接口
# ============================================================

def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("PPT Master - 配置管理工具\n")
        print("用法:")
        print("  python3 scripts/config.py list-formats     # 列出所有画布格式")
        print("  python3 scripts/config.py list-colors      # 列出所有配色方案")
        print("  python3 scripts/config.py list-industries  # 列出所有行业配色")
        print("  python3 scripts/config.py export           # 导出配置到 JSON")
        print("  python3 scripts/config.py format <key>     # 查看指定画布格式")
        return

    command = sys.argv[1]

    if command == 'list-formats':
        print("\n📐 画布格式列表:\n")
        for key, info in CANVAS_FORMATS.items():
            print(
                f"  {key:15} | {info['name']:15} | {info['dimensions']:12} | {info['use_case']}")

    elif command == 'list-colors':
        print("\n🎨 配色方案列表:\n")
        for key, info in DESIGN_COLORS.items():
            print(f"  {key:12} | {info['name']:15} | 主色: {info['primary']}")

    elif command == 'list-industries':
        print("\n🏢 行业配色列表:\n")
        for key, info in INDUSTRY_COLORS.items():
            print(f"  {key:15} | {info['name']:15} | 主色: {info['primary']}")

    elif command == 'export':
        output_file = sys.argv[2] if len(
            sys.argv) > 2 else 'config_export.json'
        Config.export_config(output_file)

    elif command == 'format' and len(sys.argv) > 2:
        format_key = sys.argv[2]
        info = Config.get_canvas_format(format_key)
        if info:
            print(f"\n📐 画布格式: {format_key}\n")
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ 未找到格式: {format_key}")
            print(f"   可用格式: {', '.join(CANVAS_FORMATS.keys())}")

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == '__main__':
    main()
