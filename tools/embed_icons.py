#!/usr/bin/env python3
"""
SVG 图标嵌入工具

将 SVG 文件中的图标占位符替换为实际的图标代码。

占位符语法：
    <use data-icon="rocket" x="100" y="200" width="48" height="48" fill="#0076A8"/>

替换后：
    <g transform="translate(100, 200) scale(3)" fill="#0076A8">
      <path d="..."/>
    </g>

用法：
    python3 tools/embed_icons.py <svg_file> [svg_file2] ...
    python3 tools/embed_icons.py svg_output/*.svg

选项：
    --icons-dir <path>    图标目录路径（默认：templates/icons/）
    --dry-run             仅显示将要替换的内容，不修改文件
    --verbose             显示详细信息
"""

import os
import re
import sys
import argparse
from pathlib import Path


# 默认图标目录
DEFAULT_ICONS_DIR = Path(__file__).parent.parent / 'templates' / 'icons'

# 图标基础尺寸
ICON_BASE_SIZE = 16


def extract_paths_from_icon(icon_path: Path) -> list[str]:
    """
    从图标 SVG 文件中提取所有 path 元素
    
    Args:
        icon_path: 图标文件路径
        
    Returns:
        path 元素列表（不含 fill 属性）
    """
    if not icon_path.exists():
        return []
    
    content = icon_path.read_text(encoding='utf-8')
    
    # 匹配所有 <path ... /> 元素
    path_pattern = r'<path\s+([^>]*)/>'
    matches = re.findall(path_pattern, content, re.DOTALL)
    
    paths = []
    for attrs in matches:
        # 移除 fill 属性（将在外层 <g> 上统一设置）
        attrs_clean = re.sub(r'\s*fill="[^"]*"', '', attrs)
        paths.append(f'<path {attrs_clean.strip()}/>')
    
    return paths


def parse_use_element(use_match: str) -> dict:
    """
    解析 use 元素的属性
    
    Args:
        use_match: use 元素的完整字符串
        
    Returns:
        属性字典
    """
    attrs = {}
    
    # 提取 data-icon
    icon_match = re.search(r'data-icon="([^"]+)"', use_match)
    if icon_match:
        attrs['icon'] = icon_match.group(1)
    
    # 提取数值属性
    for attr in ['x', 'y', 'width', 'height']:
        match = re.search(rf'{attr}="([^"]+)"', use_match)
        if match:
            attrs[attr] = float(match.group(1))
    
    # 提取 fill 颜色
    fill_match = re.search(r'fill="([^"]+)"', use_match)
    if fill_match:
        attrs['fill'] = fill_match.group(1)
    
    return attrs


def generate_icon_group(attrs: dict, paths: list[str]) -> str:
    """
    生成图标的 <g> 元素
    
    Args:
        attrs: use 元素的属性
        paths: 图标的 path 元素列表
        
    Returns:
        完整的 <g> 元素字符串
    """
    x = attrs.get('x', 0)
    y = attrs.get('y', 0)
    width = attrs.get('width', ICON_BASE_SIZE)
    height = attrs.get('height', ICON_BASE_SIZE)
    fill = attrs.get('fill', '#000000')
    icon_name = attrs.get('icon', 'unknown')
    
    # 计算缩放比例（基于 width，假设等比缩放）
    scale = width / ICON_BASE_SIZE
    
    # 构建 transform
    if scale == 1:
        transform = f'translate({x}, {y})'
    else:
        transform = f'translate({x}, {y}) scale({scale})'
    
    # 生成 <g> 元素
    paths_str = '\n    '.join(paths)
    
    return f'''<!-- icon: {icon_name} -->
  <g transform="{transform}" fill="{fill}">
    {paths_str}
  </g>'''


def process_svg_file(svg_path: Path, icons_dir: Path, dry_run: bool = False, verbose: bool = False) -> int:
    """
    处理单个 SVG 文件，替换所有图标占位符
    
    Args:
        svg_path: SVG 文件路径
        icons_dir: 图标目录路径
        dry_run: 是否仅预览不修改
        verbose: 是否显示详细信息
        
    Returns:
        替换的图标数量
    """
    if not svg_path.exists():
        print(f"❌ 文件不存在: {svg_path}")
        return 0
    
    content = svg_path.read_text(encoding='utf-8')
    
    # 匹配 <use data-icon="xxx" ... /> 元素
    use_pattern = r'<use\s+[^>]*data-icon="[^"]*"[^>]*/>'
    matches = list(re.finditer(use_pattern, content))
    
    if not matches:
        if verbose:
            print(f"⏭️  无图标占位符: {svg_path}")
        return 0
    
    replaced_count = 0
    new_content = content
    
    # 从后向前替换，避免位置偏移
    for match in reversed(matches):
        use_str = match.group(0)
        attrs = parse_use_element(use_str)
        
        icon_name = attrs.get('icon')
        if not icon_name:
            continue
        
        icon_path = icons_dir / f'{icon_name}.svg'
        paths = extract_paths_from_icon(icon_path)
        
        if not paths:
            print(f"⚠️  图标不存在: {icon_name} (in {svg_path.name})")
            continue
        
        replacement = generate_icon_group(attrs, paths)
        
        if verbose or dry_run:
            print(f"  📍 {icon_name}: x={attrs.get('x', 0)}, y={attrs.get('y', 0)}, "
                  f"size={attrs.get('width', 16)}, fill={attrs.get('fill', '#000000')}")
        
        new_content = new_content[:match.start()] + replacement + new_content[match.end():]
        replaced_count += 1
    
    if not dry_run and replaced_count > 0:
        svg_path.write_text(new_content, encoding='utf-8')
    
    status = "🔍 预览" if dry_run else "✅ 已处理"
    print(f"{status}: {svg_path.name} ({replaced_count} 个图标)")
    
    return replaced_count


def main():
    parser = argparse.ArgumentParser(
        description='将 SVG 文件中的图标占位符替换为实际图标代码',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python3 tools/embed_icons.py svg_output/01_cover.svg
  python3 tools/embed_icons.py svg_output/*.svg
  python3 tools/embed_icons.py --dry-run svg_output/*.svg
  python3 tools/embed_icons.py --icons-dir my_icons/ output.svg
        '''
    )
    
    parser.add_argument('files', nargs='+', help='要处理的 SVG 文件')
    parser.add_argument('--icons-dir', type=Path, default=DEFAULT_ICONS_DIR,
                        help=f'图标目录路径（默认：{DEFAULT_ICONS_DIR}）')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅显示将要替换的内容，不修改文件')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细信息')
    
    args = parser.parse_args()
    
    # 验证图标目录
    if not args.icons_dir.exists():
        print(f"❌ 图标目录不存在: {args.icons_dir}")
        sys.exit(1)
    
    print(f"📁 图标目录: {args.icons_dir}")
    if args.dry_run:
        print("🔍 预览模式（不修改文件）")
    print()
    
    total_replaced = 0
    total_files = 0
    
    for file_pattern in args.files:
        svg_path = Path(file_pattern)
        if svg_path.exists():
            count = process_svg_file(svg_path, args.icons_dir, args.dry_run, args.verbose)
            total_replaced += count
            if count > 0:
                total_files += 1
    
    print()
    print(f"📊 总计: {total_files} 个文件, {total_replaced} 个图标" + 
          (" (预览)" if args.dry_run else " 已替换"))


if __name__ == '__main__':
    main()

