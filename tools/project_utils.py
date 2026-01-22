#!/usr/bin/env python3
"""
PPT Master - 项目工具公共模块

提供项目信息解析、验证等公共功能，供其他工具复用。
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# 画布格式定义
CANVAS_FORMATS = {
    'ppt169': {
        'name': 'PPT 16:9',
        'dimensions': '1280×720',
        'viewbox': '0 0 1280 720',
        'aspect_ratio': '16:9'
    },
    'ppt43': {
        'name': 'PPT 4:3',
        'dimensions': '1024×768',
        'viewbox': '0 0 1024 768',
        'aspect_ratio': '4:3'
    },
    'wechat': {
        'name': '微信公众号头图',
        'dimensions': '900×383',
        'viewbox': '0 0 900 383',
        'aspect_ratio': '2.35:1'
    },
    'xiaohongshu': {
        'name': '小红书',
        'dimensions': '1242×1660',
        'viewbox': '0 0 1242 1660',
        'aspect_ratio': '3:4'
    },
    'moments': {
        'name': '朋友圈/Instagram',
        'dimensions': '1080×1080',
        'viewbox': '0 0 1080 1080',
        'aspect_ratio': '1:1'
    },
    'story': {
        'name': 'Story/竖版',
        'dimensions': '1080×1920',
        'viewbox': '0 0 1080 1920',
        'aspect_ratio': '9:16'
    },
    'banner': {
        'name': '横版 Banner',
        'dimensions': '1920×1080',
        'viewbox': '0 0 1920 1080',
        'aspect_ratio': '16:9'
    },
    'a4': {
        'name': 'A4 打印',
        'dimensions': '1240×1754',
        'viewbox': '0 0 1240 1754',
        'aspect_ratio': '√2:1'
    }
}


def parse_project_name(dir_name: str) -> Dict[str, str]:
    """
    从项目目录名解析项目信息

    Args:
        dir_name: 项目目录名称

    Returns:
        包含 name, format, date 的字典
    """
    result = {
        'name': dir_name,
        'format': 'unknown',
        'format_name': '未知格式',
        'date': 'unknown',
        'date_formatted': '未知日期'
    }

    # 提取画布格式
    for fmt_key, fmt_info in CANVAS_FORMATS.items():
        if fmt_key in dir_name.lower():
            result['format'] = fmt_key
            result['format_name'] = fmt_info['name']
            break

    # 提取日期 (格式: _YYYYMMDD)
    date_match = re.search(r'_(\d{8})$', dir_name)
    if date_match:
        date_str = date_match.group(1)
        result['date'] = date_str
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            result['date_formatted'] = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # 提取项目名称（去除格式和日期后缀）
    name = dir_name
    for fmt_key in CANVAS_FORMATS.keys():
        name = re.sub(f'_{fmt_key}', '', name, flags=re.IGNORECASE)
    name = re.sub(r'_\d{8}$', '', name)
    result['name'] = name

    return result


def get_project_info(project_path: str) -> Dict:
    """
    获取项目的详细信息

    Args:
        project_path: 项目目录路径

    Returns:
        项目信息字典
    """
    project_path = Path(project_path)

    # 解析目录名
    parsed = parse_project_name(project_path.name)

    info = {
        'path': str(project_path),
        'dir_name': project_path.name,
        'name': parsed['name'],
        'format': parsed['format'],
        'format_name': parsed['format_name'],
        'date': parsed['date'],
        'date_formatted': parsed['date_formatted'],
        'exists': project_path.exists(),
        'svg_count': 0,
        'has_spec': False,
        'has_readme': False,
        'has_source': False,
        'spec_file': None,
        'svg_files': []
    }

    if not project_path.exists():
        return info

    # 检查 README.md
    info['has_readme'] = (project_path / 'README.md').exists()

    # 检查设计规范文件（多个可能的名称）
    spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
    for spec_file in spec_files:
        if (project_path / spec_file).exists():
            info['has_spec'] = True
            info['spec_file'] = spec_file
            break

    # 检查来源文档
    info['has_source'] = (project_path / '来源文档.md').exists()

    # 统计 SVG 文件
    svg_output = project_path / 'svg_output'
    if svg_output.exists():
        svg_files = sorted(svg_output.glob('*.svg'))
        info['svg_count'] = len(svg_files)
        info['svg_files'] = [f.name for f in svg_files]

    # 获取画布格式详细信息
    if info['format'] in CANVAS_FORMATS:
        info['canvas_info'] = CANVAS_FORMATS[info['format']]

    return info


def validate_project_structure(project_path: str, verbose: bool = False) -> Tuple[bool, List[str], List[str]]:
    """
    验证项目结构的完整性

    Args:
        project_path: 项目目录路径
        verbose: 是否显示详细的修复建议

    Returns:
        (是否有效, 错误列表, 警告列表)
    """
    project_path = Path(project_path)
    errors = []
    warnings = []

    # 尝试导入错误助手
    try:
        from error_helper import ErrorHelper
        use_helper = True
    except ImportError:
        use_helper = False

    # 检查目录是否存在
    if not project_path.exists():
        msg = f"项目目录不存在: {project_path}"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_directory',
                                                           {'project_path': str(project_path)})
        errors.append(msg)
        return False, errors, warnings

    if not project_path.is_dir():
        errors.append(f"不是有效的目录: {project_path}")
        return False, errors, warnings

    # 检查必需文件
    if not (project_path / 'README.md').exists():
        msg = "缺少必需文件: README.md"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_readme',
                                                           {'project_path': str(project_path)})
        errors.append(msg)

    # 检查设计规范文件
    spec_files = ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md']
    has_spec = any((project_path / f).exists() for f in spec_files)
    if not has_spec:
        msg = "缺少设计规范文件（建议文件名: 设计规范与内容大纲.md）"
        if use_helper and verbose:
            msg += "\n" + ErrorHelper.format_error_message('missing_spec')
        warnings.append(msg)

    # 检查 svg_output 目录
    svg_output = project_path / 'svg_output'
    if not svg_output.exists():
        msg = "缺少 svg_output 目录"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_svg_output')
        errors.append(msg)
    elif not svg_output.is_dir():
        errors.append("svg_output 不是目录")
    else:
        # 检查是否有 SVG 文件
        svg_files = list(svg_output.glob('*.svg'))
        if not svg_files:
            msg = "svg_output 目录为空，没有 SVG 文件"
            if use_helper and verbose:
                msg += "\n" + \
                    ErrorHelper.format_error_message('empty_svg_output')
            warnings.append(msg)
        else:
            # 验证 SVG 文件命名（与 project_manager.py 保持一致）
            for svg_file in svg_files:
                if not re.match(r'^(slide_\d+_\w+|P?\d+_.+)\.svg$', svg_file.name):
                    msg = f"SVG 文件命名不规范: {svg_file.name}"
                    if use_helper and verbose:
                        msg += "\n" + ErrorHelper.format_error_message('invalid_svg_naming',
                                                                       {'file_name': svg_file.name})
                    warnings.append(msg)

    # 检查目录命名格式
    dir_name = project_path.name
    if not re.search(r'_\d{8}$', dir_name):
        msg = f"目录名缺少日期后缀 (_YYYYMMDD): {dir_name}"
        if use_helper and verbose:
            msg += "\n" + \
                ErrorHelper.format_error_message('missing_date_suffix')
        warnings.append(msg)

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def validate_svg_viewbox(svg_files: List[Path], expected_format: Optional[str] = None) -> List[str]:
    """
    验证 SVG 文件的 viewBox 设置

    Args:
        svg_files: SVG 文件列表
        expected_format: 期望的画布格式（如 'ppt169'）

    Returns:
        警告列表
    """
    warnings = []
    viewbox_pattern = re.compile(r'viewBox="([^"]+)"')
    viewboxes = set()

    # 确定期望的 viewBox
    expected_viewbox = None
    if expected_format and expected_format in CANVAS_FORMATS:
        expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']

    for svg_file in svg_files[:10]:  # 检查前10个文件
        try:
            with open(svg_file, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # 只读取前2000字符
                match = viewbox_pattern.search(content)
                if match:
                    viewbox = match.group(1)
                    viewboxes.add(viewbox)

                    # 如果指定了期望格式，检查是否匹配
                    if expected_viewbox and viewbox != expected_viewbox:
                        warnings.append(
                            f"{svg_file.name}: viewBox '{viewbox}' 与期望格式 "
                            f"'{expected_format}' 不匹配（期望: '{expected_viewbox}'）"
                        )
                else:
                    warnings.append(f"{svg_file.name}: 未找到 viewBox 属性")
        except Exception as e:
            warnings.append(f"{svg_file.name}: 读取失败 - {e}")

    # 检查是否有多个不同的 viewBox
    if len(viewboxes) > 1:
        warnings.append(f"检测到多个不同的 viewBox 设置: {viewboxes}")

    return warnings


def find_all_projects(base_dir: str) -> List[Path]:
    """
    查找指定目录下的所有项目

    Args:
        base_dir: 基础目录路径

    Returns:
        项目目录列表
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        return []

    projects = []
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 检查是否是有效的项目目录（包含 svg_output 或设计规范）
            has_svg_output = (item / 'svg_output').exists()
            has_spec = any((item / f).exists() for f in
                           ['设计规范与内容大纲.md', 'design_specification.md', '设计规范.md'])

            if has_svg_output or has_spec:
                projects.append(item)

    return sorted(projects)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_project_stats(project_path: str) -> Dict:
    """
    获取项目的统计信息

    Args:
        project_path: 项目目录路径

    Returns:
        统计信息字典
    """
    project_path = Path(project_path)
    stats = {
        'total_files': 0,
        'svg_files': 0,
        'md_files': 0,
        'html_files': 0,
        'total_size': 0,
        'svg_size': 0
    }

    if not project_path.exists():
        return stats

    for file in project_path.rglob('*'):
        if file.is_file():
            stats['total_files'] += 1
            file_size = file.stat().st_size
            stats['total_size'] += file_size

            if file.suffix == '.svg':
                stats['svg_files'] += 1
                stats['svg_size'] += file_size
            elif file.suffix == '.md':
                stats['md_files'] += 1
            elif file.suffix == '.html':
                stats['html_files'] += 1

    return stats


if __name__ == '__main__':
    # 测试代码
    import sys

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        info = get_project_info(project_path)

        print(f"\n项目信息: {info['dir_name']}")
        print("=" * 60)
        print(f"项目名称: {info['name']}")
        print(f"画布格式: {info['format_name']} ({info['format']})")
        print(f"创建日期: {info['date_formatted']}")
        print(f"SVG 文件: {info['svg_count']} 个")
        print(f"README: {'✓' if info['has_readme'] else '✗'}")
        print(f"设计规范: {'✓' if info['has_spec'] else '✗'}")

        print("\n验证结果:")
        print("-" * 60)
        is_valid, errors, warnings = validate_project_structure(project_path)

        if errors:
            print("❌ 错误:")
            for error in errors:
                print(f"  - {error}")

        if warnings:
            print("⚠️  警告:")
            for warning in warnings:
                print(f"  - {warning}")

        if is_valid and not warnings:
            print("✅ 项目结构完整，没有问题")
    else:
        print("用法: python3 project_utils.py <project_path>")
