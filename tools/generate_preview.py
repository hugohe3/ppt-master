#!/usr/bin/env python3
"""
PPT Master - 预览文件生成工具

自动为项目生成统一格式的 preview.html 文件。
支持交互模式和命令行参数模式。

用法:
    python3 tools/generate_preview.py                          # 交互模式
    python3 tools/generate_preview.py <project_path>           # 为指定项目生成
    python3 tools/generate_preview.py --all                    # 为所有项目生成
    python3 tools/generate_preview.py --batch <dir1> <dir2>    # 批量生成
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class PreviewGenerator:
    """预览文件生成器"""
    
    # 默认配色方案
    COLOR_SCHEMES = {
        'default': {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'bg_start': '#667eea',
            'bg_end': '#764ba2'
        },
        'google': {
            'primary': '#4285F4',
            'secondary': '#34A853',
            'bg_start': '#f8f9fa',
            'bg_end': '#e9ecef'
        },
        'consulting': {
            'primary': '#0076A8',
            'secondary': '#005587',
            'bg_start': '#f5f7fa',
            'bg_end': '#e8eef5'
        },
        'elegant': {
            'primary': '#2C3E50',
            'secondary': '#34495E',
            'bg_start': '#ECF0F1',
            'bg_end': '#BDC3C7'
        }
    }
    
    def __init__(self, template_path: Optional[str] = None):
        """初始化生成器
        
        Args:
            template_path: 模板文件路径，默认使用 templates/preview_template.html
        """
        if template_path is None:
            # 获取脚本所在目录的父目录
            script_dir = Path(__file__).parent.parent
            template_path = script_dir / 'templates' / 'preview_template.html'
        
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
    
    def detect_project_info(self, project_path: Path) -> Dict[str, any]:
        """自动检测项目信息
        
        Args:
            project_path: 项目目录路径
            
        Returns:
            包含项目信息的字典
        """
        info = {
            'title': '',
            'subtitle': '',
            'create_date': '',
            'canvas_format': '',
            'design_style': '',
            'spec_file': '',
            'slides': []
        }
        
        # 从目录名提取信息
        dir_name = project_path.name
        
        # 提取日期 (YYYYMMDD)
        date_match = re.search(r'_(\d{8})$', dir_name)
        if date_match:
            date_str = date_match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                info['create_date'] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                info['create_date'] = date_str
        
        # 提取画布格式
        if 'ppt169' in dir_name.lower():
            info['canvas_format'] = 'PPT 16:9 (1280×720)'
        elif 'ppt43' in dir_name.lower() or 'ppt_43' in dir_name.lower():
            info['canvas_format'] = 'PPT 4:3 (1024×768)'
        elif 'wechat' in dir_name.lower():
            info['canvas_format'] = '微信公众号 (900×383)'
        elif 'xiaohongshu' in dir_name.lower():
            info['canvas_format'] = '小红书 3:4 (1242×1660)'
        elif 'story' in dir_name.lower():
            info['canvas_format'] = 'Story 9:16 (1080×1920)'
        else:
            info['canvas_format'] = 'PPT 16:9 (1280×720)'  # 默认
        
        # 读取 README.md 获取标题
        readme_path = project_path / 'README.md'
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取第一个标题
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    info['title'] = title_match.group(1).strip()
                
                # 提取副标题（第二行或第一个段落）
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                if len(lines) > 1:
                    subtitle_candidate = lines[1]
                    if not subtitle_candidate.startswith('#'):
                        info['subtitle'] = subtitle_candidate[:100]  # 限制长度
        
        # 如果 README 没有标题，从目录名提取
        if not info['title']:
            # 移除日期和格式后缀
            title = re.sub(r'_(ppt169|ppt43|wechat|xiaohongshu|story)_\d{8}$', '', dir_name, flags=re.IGNORECASE)
            title = title.replace('_', ' ')
            info['title'] = title
        
        # 查找设计规范文件
        spec_files = [
            '设计规范与内容大纲.md',
            'design_specification.md',
            '设计规范.md'
        ]
        for spec_file in spec_files:
            if (project_path / spec_file).exists():
                info['spec_file'] = spec_file
                # 从设计规范中提取风格信息
                with open(project_path / spec_file, 'r', encoding='utf-8') as f:
                    spec_content = f.read()
                    if '通用灵活' in spec_content or '通用风格' in spec_content:
                        info['design_style'] = '通用灵活'
                    elif '高端咨询' in spec_content or '咨询风格' in spec_content:
                        info['design_style'] = '高端咨询'
                break
        
        if not info['spec_file']:
            info['spec_file'] = '设计规范与内容大纲.md'  # 默认
        
        if not info['design_style']:
            info['design_style'] = '通用灵活'  # 默认
        
        # 扫描 SVG 文件
        svg_output = project_path / 'svg_output'
        if svg_output.exists():
            svg_files = sorted(svg_output.glob('*.svg'))
            for svg_file in svg_files:
                # 提取文件名中的标题
                filename = svg_file.stem
                # 移除 slide_XX_ 前缀
                title = re.sub(r'^slide_\d+_', '', filename)
                # 将下划线替换为空格，首字母大写
                title = title.replace('_', ' ').title()
                
                info['slides'].append({
                    'path': f'svg_output/{svg_file.name}',
                    'title': title,
                    'filename': svg_file.name
                })
        
        return info
    
    def select_color_scheme(self, project_info: Dict) -> Dict[str, str]:
        """根据项目信息选择配色方案
        
        Args:
            project_info: 项目信息字典
            
        Returns:
            配色方案字典
        """
        # 根据设计风格选择
        if project_info.get('design_style') == '高端咨询':
            return self.COLOR_SCHEMES['consulting']
        
        # 根据标题关键词选择
        title = project_info.get('title', '').lower()
        if 'google' in title or 'gemini' in title:
            return self.COLOR_SCHEMES['google']
        
        # 默认配色
        return self.COLOR_SCHEMES['default']
    
    def generate(self, project_path: str, output_path: Optional[str] = None,
                 config: Optional[Dict] = None) -> str:
        """生成预览文件
        
        Args:
            project_path: 项目目录路径
            output_path: 输出文件路径，默认为项目目录下的 preview.html
            config: 自定义配置，覆盖自动检测的信息
            
        Returns:
            生成的文件路径
        """
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"项目目录不存在: {project_path}")
        
        # 自动检测项目信息
        info = self.detect_project_info(project_path)
        
        # 应用自定义配置
        if config:
            info.update(config)
        
        # 选择配色方案
        colors = self.select_color_scheme(info)
        
        # 准备替换数据
        replacements = {
            'PROJECT_TITLE': info.get('title', '项目预览'),
            'PROJECT_SUBTITLE': info.get('subtitle', ''),
            'CREATE_DATE': info.get('create_date', datetime.now().strftime('%Y-%m-%d')),
            'CANVAS_FORMAT': info.get('canvas_format', 'PPT 16:9'),
            'DESIGN_STYLE': info.get('design_style', '通用灵活'),
            'SLIDE_COUNT': str(len(info['slides'])),
            'SPEC_FILE': info.get('spec_file', '设计规范与内容大纲.md'),
            'PRIMARY_COLOR': colors['primary'],
            'SECONDARY_COLOR': colors['secondary'],
            'BG_GRADIENT_START': colors['bg_start'],
            'BG_GRADIENT_END': colors['bg_end'],
            'SLIDES_JSON': json.dumps(info['slides'], ensure_ascii=False, indent=2),
            'FOOTER_TEXT': f"© {datetime.now().year} | 所有 SVG 文件遵循 {info.get('canvas_format', 'PPT 16:9')} 标准"
        }
        
        # 替换模板中的占位符
        output = self.template
        for key, value in replacements.items():
            output = output.replace('{{' + key + '}}', value)
        
        # 确定输出路径
        if output_path is None:
            output_path = project_path / 'preview.html'
        else:
            output_path = Path(output_path)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        return str(output_path)
    
    def generate_for_all_projects(self, base_dir: str = 'examples') -> List[Tuple[str, bool, str]]:
        """为所有项目生成预览文件
        
        Args:
            base_dir: 项目基础目录
            
        Returns:
            结果列表，每项为 (项目路径, 是否成功, 消息)
        """
        base_path = Path(base_dir)
        if not base_path.exists():
            return [(base_dir, False, "目录不存在")]
        
        results = []
        for project_dir in base_path.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith('.'):
                continue
            
            # 检查是否有 svg_output 目录
            if not (project_dir / 'svg_output').exists():
                results.append((str(project_dir), False, "没有 svg_output 目录"))
                continue
            
            try:
                output_path = self.generate(project_dir)
                results.append((str(project_dir), True, f"已生成: {output_path}"))
            except Exception as e:
                results.append((str(project_dir), False, f"错误: {str(e)}"))
        
        return results


def interactive_mode():
    """交互模式"""
    print("=" * 60)
    print("PPT Master - 预览文件生成工具 (交互模式)")
    print("=" * 60)
    print()
    
    generator = PreviewGenerator()
    
    while True:
        print("\n请选择操作:")
        print("1. 为单个项目生成预览")
        print("2. 为所有项目生成预览")
        print("3. 批量生成（指定多个项目）")
        print("4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            project_path = input("请输入项目路径: ").strip()
            if not project_path:
                print("❌ 路径不能为空")
                continue
            
            try:
                output_path = generator.generate(project_path)
                print(f"✅ 成功生成预览文件: {output_path}")
            except Exception as e:
                print(f"❌ 生成失败: {e}")
        
        elif choice == '2':
            base_dir = input("请输入项目基础目录 (默认: examples): ").strip()
            if not base_dir:
                base_dir = 'examples'
            
            print(f"\n正在扫描 {base_dir} 目录...")
            results = generator.generate_for_all_projects(base_dir)
            
            print(f"\n处理完成，共 {len(results)} 个项目:")
            success_count = 0
            for project, success, message in results:
                status = "✅" if success else "❌"
                print(f"{status} {Path(project).name}: {message}")
                if success:
                    success_count += 1
            
            print(f"\n成功: {success_count}/{len(results)}")
        
        elif choice == '3':
            print("请输入项目路径（每行一个，输入空行结束）:")
            paths = []
            while True:
                path = input().strip()
                if not path:
                    break
                paths.append(path)
            
            if not paths:
                print("❌ 没有输入任何路径")
                continue
            
            print(f"\n正在处理 {len(paths)} 个项目...")
            success_count = 0
            for path in paths:
                try:
                    output_path = generator.generate(path)
                    print(f"✅ {Path(path).name}: {output_path}")
                    success_count += 1
                except Exception as e:
                    print(f"❌ {Path(path).name}: {e}")
            
            print(f"\n成功: {success_count}/{len(paths)}")
        
        elif choice == '4':
            print("\n再见！")
            break
        
        else:
            print("❌ 无效选项，请重新选择")


def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 无参数，进入交互模式
        interactive_mode()
    elif sys.argv[1] in ['-h', '--help']:
        print(__doc__)
    elif sys.argv[1] == '--all':
        # 为所有项目生成
        base_dir = sys.argv[2] if len(sys.argv) > 2 else 'examples'
        generator = PreviewGenerator()
        print(f"正在为 {base_dir} 下的所有项目生成预览文件...")
        results = generator.generate_for_all_projects(base_dir)
        
        success_count = 0
        for project, success, message in results:
            status = "✅" if success else "❌"
            print(f"{status} {Path(project).name}: {message}")
            if success:
                success_count += 1
        
        print(f"\n完成！成功: {success_count}/{len(results)}")
    elif sys.argv[1] == '--batch':
        # 批量生成
        if len(sys.argv) < 3:
            print("错误: --batch 需要至少一个项目路径")
            sys.exit(1)
        
        generator = PreviewGenerator()
        paths = sys.argv[2:]
        success_count = 0
        
        for path in paths:
            try:
                output_path = generator.generate(path)
                print(f"✅ {Path(path).name}: {output_path}")
                success_count += 1
            except Exception as e:
                print(f"❌ {Path(path).name}: {e}")
        
        print(f"\n完成！成功: {success_count}/{len(paths)}")
    else:
        # 为单个项目生成
        project_path = sys.argv[1]
        generator = PreviewGenerator()
        
        try:
            output_path = generator.generate(project_path)
            print(f"✅ 成功生成预览文件: {output_path}")
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()

