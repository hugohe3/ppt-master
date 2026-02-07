#!/usr/bin/env python3
"""
PPT Master - 项目管理工具

提供项目初始化、验证等功能。

用法:
    python3 tools/project_manager.py init <project_name> [--format ppt169|ppt43|wechat|...]
    python3 tools/project_manager.py validate <project_path>
    python3 tools/project_manager.py info <project_path>
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入公共工具模块（必须成功）
try:
    from project_utils import (
        CANVAS_FORMATS,
        normalize_canvas_format,
        get_project_info as get_project_info_common,
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
            normalize_canvas_format,
            get_project_info as get_project_info_common,
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
                     base_dir: Optional[str] = None) -> str:
        """初始化新项目

        Args:
            project_name: 项目名称
            canvas_format: 画布格式 (ppt169, ppt43, wechat, 等)
            base_dir: 项目基础目录，默认使用实例的 base_dir

        Returns:
            创建的项目路径
        """
        if base_dir:
            base_path = Path(base_dir)
        else:
            base_path = self.base_dir

        normalized_format = normalize_canvas_format(canvas_format)
        if normalized_format not in self.CANVAS_FORMATS:
            available = ', '.join(sorted(self.CANVAS_FORMATS.keys()))
            raise ValueError(
                f"不支持的画布格式: {canvas_format} "
                f"(可用: {available}; 常用别名: xhs -> xiaohongshu)"
            )

        # 创建项目目录名: {project_name}_{format}_{YYYYMMDD}
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        project_dir_name = f"{project_name}_{normalized_format}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"项目目录已存在: {project_path}")

        # 创建目录结构
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / 'svg_output').mkdir(exist_ok=True)   # 原始版本（带占位符）
        (project_path / 'svg_final').mkdir(exist_ok=True)    # 最终版本（后处理完成）
        (project_path / 'images').mkdir(exist_ok=True)       # 图片资源
        (project_path / 'notes').mkdir(exist_ok=True)        # 演讲备注
        (project_path / 'templates').mkdir(exist_ok=True)    # 项目页面模板（可选）
        readme_path = project_path / 'README.md'
        readme_path.write_text(
            (
                f"# {project_name}\n\n"
                f"- 画布格式: {normalized_format}\n"
                f"- 创建日期: {date_str}\n\n"
                "## 目录\n\n"
                "- `svg_output/`: 原始 SVG 输出\n"
                "- `svg_final/`: 后处理后的 SVG\n"
                "- `images/`: 图片资源\n"
                "- `notes/`: 演讲备注\n"
                "- `templates/`: 项目模板\n"
            ),
            encoding='utf-8'
        )

        # 获取画布格式信息
        canvas_info = self.CANVAS_FORMATS[normalized_format]

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
        project_path_obj = Path(project_path)
        is_valid, errors, warnings = validate_project_structure(str(project_path_obj))

        if project_path_obj.exists() and project_path_obj.is_dir():
            info = get_project_info_common(str(project_path_obj))
            if info.get('svg_files'):
                svg_files = [project_path_obj / 'svg_output' / f for f in info['svg_files']]
                expected_format = info.get('format')
                if expected_format == 'unknown':
                    expected_format = None
                warnings.extend(validate_svg_viewbox(svg_files, expected_format))

        return is_valid, errors, warnings

    def get_project_info(self, project_path: str) -> Dict:
        """获取项目信息

        Args:
            project_path: 项目目录路径

        Returns:
            项目信息字典
        """
        shared = get_project_info_common(project_path)
        return {
            'name': shared.get('name', Path(project_path).name),
            'path': shared.get('path', str(project_path)),
            'exists': shared.get('exists', False),
            'svg_count': shared.get('svg_count', 0),
            'has_spec': shared.get('has_spec', False),
            'canvas_format': shared.get('format_name', '未知格式'),
            'create_date': shared.get('date_formatted', '未知日期')
        }


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
