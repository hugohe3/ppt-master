#!/usr/bin/env python3
"""
PPT Master - 项目管理工具

提供项目初始化、验证等功能。

用法:
    python3 tools/project_manager.py init <project_name> [--format ppt169|ppt43|wechat|...]
    python3 tools/project_manager.py validate <project_path>
    python3 tools/project_manager.py info <project_path>
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 导入公共工具模块（必须成功）
try:
    from project_utils import (
        CANVAS_FORMATS,
        get_project_info,
        validate_project_structure,
        validate_svg_viewbox
    )
except ImportError:
    # 如果直接运行，尝试从当前目录导入
    import os
    import sys
    # 将 tools 目录添加到路径
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        from project_utils import (
            CANVAS_FORMATS,
            get_project_info,
            validate_project_structure,
            validate_svg_viewbox
        )
    except ImportError as e:
        print(f"错误: 无法导入 project_utils 模块")
        print(f"请确保在 tools/ 目录下运行，或将 tools/ 添加到 PYTHONPATH")
        print(f"详细信息: {e}")
        sys.exit(1)


class ProjectManager:
    """项目管理器"""

    # 使用公共模块的画布格式定义（统一来源）
    CANVAS_FORMATS = CANVAS_FORMATS

    def __init__(self, base_dir: str = 'projects'):
        """初始化项目管理器

        Args:
            base_dir: 项目基础目录，默认为 projects
        """
        self.base_dir = Path(base_dir)

    def init_project(self, project_name: str, canvas_format: str = 'ppt169',
                     design_style: str = '通用灵活', base_dir: Optional[str] = None) -> str:
        """初始化新项目

        Args:
            project_name: 项目名称
            canvas_format: 画布格式 (ppt169, ppt43, wechat, 等)
            design_style: 设计风格 (通用灵活, 一般咨询, 顶级咨询)
            base_dir: 项目基础目录，默认使用实例的 base_dir

        Returns:
            创建的项目路径
        """
        if base_dir:
            base_path = Path(base_dir)
        else:
            base_path = self.base_dir

        # 创建项目目录名: {project_name}_{format}_{YYYYMMDD}
        date_str = datetime.now().strftime('%Y%m%d')
        project_dir_name = f"{project_name}_{canvas_format}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"项目目录已存在: {project_path}")

        # 创建目录结构
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / 'svg_output').mkdir(exist_ok=True)   # 原始版本（带占位符）
        (project_path / 'svg_final').mkdir(exist_ok=True)    # 最终版本（后处理完成）
        (project_path / 'images').mkdir(exist_ok=True)       # 图片资源
        (project_path / 'notes').mkdir(exist_ok=True)        # 演讲备注

        # 获取画布格式信息
        canvas_info = self.CANVAS_FORMATS.get(
            canvas_format, self.CANVAS_FORMATS['ppt169'])

        # 获取画布格式信息
        canvas_info = self.CANVAS_FORMATS.get(
            canvas_format, self.CANVAS_FORMATS['ppt169'])

        # 提示用户下一步操作 (不再自动创建空的设计规范文件)
        print(f"项目目录已创建: {project_path}")
        print(f"画布格式: {canvas_info['name']} ({canvas_info['dimensions']})")
        
        return str(project_path)

    def validate_project(self, project_path: str) -> Tuple[bool, List[str], List[str]]:
        """验证项目完整性

        Args:
            project_path: 项目目录路径

        Returns:
            (是否有效, 错误列表, 警告列表)
        """
        project_path = Path(project_path)
        errors = []
        warnings = []

        # 检查目录是否存在
        if not project_path.exists():
            errors.append(f"项目目录不存在: {project_path}")
            return False, errors, warnings

        if not project_path.is_dir():
            errors.append(f"不是有效的目录: {project_path}")
            return False, errors, warnings

        # 检查设计规范文件（核心必需文件）
        spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
        has_spec = any((project_path / f).exists() for f in spec_files)
        if not has_spec:
            errors.append("缺少设计规范文件（建议文件名: 设计规范与内容大纲.md）")

        # 检查 svg_output 目录
        svg_output = project_path / 'svg_output'
        if not svg_output.exists():
            errors.append("缺少 svg_output 目录")
        else:
            # 检查 SVG 文件
            svg_files = list(svg_output.glob('*.svg'))
            if len(svg_files) == 0:
                warnings.append("svg_output 目录为空")
            else:
                # 验证 SVG 文件命名（支持两种格式）
                # 格式1: slide_01_name.svg（英文项目）
                # 格式2: 01_封面.svg 或 P01_封面.svg（中文项目）
                for svg_file in svg_files:
                    if not re.match(r'^(slide_\d+_\w+|P?\d+_.+)\.svg$', svg_file.name):
                        warnings.append(
                            f"SVG 文件命名不规范: {svg_file.name} (建议: 01_名称.svg 或 slide_01_name.svg)")

                # 检查 viewBox
                self._validate_svg_viewbox(svg_files, warnings)

        # 检查项目命名格式（支持所有画布格式）
        dir_name = project_path.name
        canvas_formats = '|'.join(self.CANVAS_FORMATS.keys())
        pattern = rf'^.+_({canvas_formats})_\d{{8}}$'
        if not re.match(pattern, dir_name, re.IGNORECASE):
            warnings.append(
                f"项目目录命名不规范: {dir_name} (建议: name_format_YYYYMMDD)")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def _validate_svg_viewbox(self, svg_files: List[Path], warnings: List[str]):
        """验证 SVG 文件的 viewBox 设置

        Args:
            svg_files: SVG 文件列表
            warnings: 警告列表（会被修改）
        """
        viewbox_pattern = re.compile(r'viewBox="([^"]+)"')
        viewboxes = set()

        for svg_file in svg_files[:5]:  # 只检查前5个文件
            try:
                with open(svg_file, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 只读取前1000字符
                    match = viewbox_pattern.search(content)
                    if match:
                        viewboxes.add(match.group(1))
                    else:
                        warnings.append(f"{svg_file.name}: 未找到 viewBox 属性")
            except Exception as e:
                warnings.append(f"{svg_file.name}: 读取失败 - {e}")

        if len(viewboxes) > 1:
            warnings.append(f"检测到多个不同的 viewBox 设置: {viewboxes}")

    def get_project_info(self, project_path: str) -> Dict:
        """获取项目信息

        Args:
            project_path: 项目目录路径

        Returns:
            项目信息字典
        """
        project_path = Path(project_path)
        info = {
            'name': project_path.name,
            'path': str(project_path),
            'exists': project_path.exists(),
            'svg_count': 0,
            'has_spec': False,
            'canvas_format': 'unknown',
            'create_date': 'unknown'
        }

        if not project_path.exists():
            return info

        # 统计 SVG 文件
        svg_output = project_path / 'svg_output'
        if svg_output.exists():
            info['svg_count'] = len(list(svg_output.glob('*.svg')))

        # 检查设计规范
        spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
        info['has_spec'] = any((project_path / f).exists() for f in spec_files)

        # 从目录名提取信息
        dir_name = project_path.name

        # 提取画布格式
        for fmt in self.CANVAS_FORMATS.keys():
            if fmt in dir_name.lower():
                info['canvas_format'] = self.CANVAS_FORMATS[fmt]['name']
                break

        # 提取日期
        date_match = re.search(r'_(\d{8})$', dir_name)
        if date_match:
            date_str = date_match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                info['create_date'] = date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass

        return info


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    manager = ProjectManager()

    if command == 'init':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目名称")
            print(
                "用法: python3 tools/project_manager.py init <project_name> [--format ppt169]")
            sys.exit(1)

        project_name = sys.argv[2]
        canvas_format = 'ppt169'
        base_dir = 'projects'

        # 解析可选参数
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == '--format' and i + 1 < len(sys.argv):
                canvas_format = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--dir' and i + 1 < len(sys.argv):
                base_dir = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        try:
            project_path = manager.init_project(
                project_name, canvas_format, base_dir=base_dir)
            print(f"[OK] 项目已创建: {project_path}")
            print("\n下一步:")
            print("1. 生成并保存 设计规范与内容大纲.md (请参考 templates/design_spec_reference.md)")
            print("2. 将 SVG 文件放入 svg_output/ 目录")
        except Exception as e:
            print(f"[ERROR] 创建失败: {e}")
            sys.exit(1)

    elif command == 'validate':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目路径")
            print("用法: python3 tools/project_manager.py validate <project_path>")
            sys.exit(1)

        project_path = sys.argv[2]
        is_valid, errors, warnings = manager.validate_project(project_path)

        print(f"\n项目验证: {project_path}")
        print("=" * 60)

        if errors:
            print("\n[ERROR] 错误:")
            for error in errors:
                print(f"  - {error}")

        if warnings:
            print("\n[WARN] 警告:")
            for warning in warnings:
                print(f"  - {warning}")

        if is_valid and not warnings:
            print("\n[OK] 项目结构完整，没有问题")
        elif is_valid:
            print("\n[OK] 项目结构有效，但有一些建议")
        else:
            print("\n[ERROR] 项目结构无效，请修复错误")
            sys.exit(1)

    elif command == 'info':
        if len(sys.argv) < 3:
            print("错误: 需要提供项目路径")
            print("用法: python3 tools/project_manager.py info <project_path>")
            sys.exit(1)

        project_path = sys.argv[2]
        info = manager.get_project_info(project_path)

        print(f"\n项目信息: {info['name']}")
        print("=" * 60)
        print(f"路径: {info['path']}")
        print(f"存在: {'是' if info['exists'] else '否'}")
        print(f"SVG 文件数: {info['svg_count']}")
        print(f"设计规范: {'存在' if info['has_spec'] else '缺失'}")
        print(f"画布格式: {info['canvas_format']}")
        print(f"创建日期: {info['create_date']}")

    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
