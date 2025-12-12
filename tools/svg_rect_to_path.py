#!/usr/bin/env python3
"""
PPT Master - SVG 圆角矩形转 Path 工具

解决 SVG 在 PowerPoint 中「转换为形状」时圆角丢失的问题：
将带 rx/ry 的 <rect> 转换为等效的 <path>

用法:
    python3 tools/svg_rect_to_path.py <SVG文件或目录>
    python3 tools/svg_rect_to_path.py <项目路径> -s output
    python3 tools/svg_rect_to_path.py <项目路径> -s final -o svg_rounded

示例:
    python3 tools/svg_rect_to_path.py examples/ppt169_demo
    python3 tools/svg_rect_to_path.py examples/ppt169_demo/svg_output/01_cover.svg

输出:
    - 目录模式：输出到 svg_rounded/ 子目录
    - 文件模式：输出到 <文件名>_rounded.svg
"""

import sys
import re
import argparse
from pathlib import Path
from typing import Tuple, Dict, List
from xml.etree import ElementTree as ET


def rect_to_rounded_path(x: float, y: float, width: float, height: float, 
                          rx: float, ry: float) -> str:
    """
    将圆角矩形转换为 SVG path 字符串
    使用椭圆弧命令绘制圆角
    """
    # 限制圆角半径不超过宽高的一半
    rx = min(rx, width / 2)
    ry = min(ry, height / 2)
    
    # 计算关键点
    x1 = x + rx
    x2 = x + width - rx
    y1 = y + ry
    y2 = y + height - ry
    
    # 构建 path
    path = (
        f"M{x1:.2f},{y:.2f} "
        f"H{x2:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x + width:.2f},{y1:.2f} "
        f"V{y2:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x2:.2f},{y + height:.2f} "
        f"H{x1:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x:.2f},{y2:.2f} "
        f"V{y1:.2f} "
        f"A{rx:.2f},{ry:.2f} 0 0 1 {x1:.2f},{y:.2f} "
        f"Z"
    )
    
    # 清理多余的小数
    path = re.sub(r'\.00(?=\s|,|[A-Za-z]|$)', '', path)
    
    return path


def parse_float(val: str, default: float = 0.0) -> float:
    """安全解析浮点数"""
    if not val:
        return default
    try:
        # 移除单位
        val = re.sub(r'(px|pt|em|%|rem)$', '', val.strip())
        return float(val)
    except ValueError:
        return default


def process_svg(content: str, verbose: bool = False) -> Tuple[str, int]:
    """
    处理 SVG 内容，将圆角矩形转换为 path
    返回 (处理后的内容, 转换数量)
    """
    converted_count = 0
    
    # 保存原始 XML 声明
    xml_declaration = ''
    if content.strip().startswith('<?xml'):
        match = re.match(r'(<\?xml[^?]*\?>)', content)
        if match:
            xml_declaration = match.group(1) + '\n'
    
    # 注册 SVG 命名空间
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        if verbose:
            print(f"    XML 解析错误: {e}")
        return content, 0
    
    # 获取默认命名空间
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'
    
    def get_tag_name(tag):
        """获取不带命名空间的标签名"""
        if tag.startswith('{'):
            return tag.split('}')[1]
        return tag
    
    def process_element(elem):
        """处理单个元素"""
        nonlocal converted_count
        tag_name = get_tag_name(elem.tag)
        
        # 处理圆角矩形
        if tag_name == 'rect':
            rx = parse_float(elem.get('rx', '0'))
            ry = parse_float(elem.get('ry', '0'))
            
            # 如果只指定了一个，另一个取相同值
            if rx == 0 and ry > 0:
                rx = ry
            elif ry == 0 and rx > 0:
                ry = rx
            
            if rx > 0 or ry > 0:
                x = parse_float(elem.get('x', '0'))
                y = parse_float(elem.get('y', '0'))
                width = parse_float(elem.get('width', '0'))
                height = parse_float(elem.get('height', '0'))
                
                if width > 0 and height > 0:
                    # 生成 path
                    path_d = rect_to_rounded_path(x, y, width, height, rx, ry)
                    
                    # rect 特有属性
                    rect_attrs = {'x', 'y', 'width', 'height', 'rx', 'ry'}
                    
                    # 修改元素为 path
                    elem.tag = ns + 'path' if ns else 'path'
                    elem.set('d', path_d)
                    
                    # 移除 rect 特有属性
                    for attr in rect_attrs:
                        if attr in elem.attrib:
                            del elem.attrib[attr]
                    
                    converted_count += 1
                    if verbose:
                        print(f"    转换圆角矩形: rx={rx}, ry={ry}")
        
        # 递归处理子元素
        for child in elem:
            process_element(child)
    
    # 处理所有元素
    process_element(root)
    
    # 转换回字符串
    result = ET.tostring(root, encoding='unicode')
    
    # 添加 XML 声明（如果原来有的话）
    if xml_declaration:
        result = xml_declaration + result
    
    return result, converted_count


def process_svg_file(input_path: Path, output_path: Path, verbose: bool = False) -> Tuple[bool, int]:
    """处理单个 SVG 文件"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        processed, count = process_svg(content, verbose)
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed)
        
        return True, count
        
    except Exception as e:
        if verbose:
            print(f"  错误: {e}")
        return False, 0


def find_svg_files(project_path: Path, source: str = 'output') -> Tuple[List[Path], str]:
    """查找项目中的 SVG 文件"""
    dir_map = {
        'output': 'svg_output',
        'final': 'svg_final',
        'flat': 'svg_output_flattext',
        'final_flat': 'svg_final_flattext',
    }
    
    dir_name = dir_map.get(source, source)
    svg_dir = project_path / dir_name
    
    if not svg_dir.exists():
        if (project_path / 'svg_output').exists():
            dir_name = 'svg_output'
            svg_dir = project_path / dir_name
        elif project_path.is_dir():
            svg_dir = project_path
            dir_name = project_path.name
    
    if not svg_dir.exists():
        return [], ''
    
    return sorted(svg_dir.glob('*.svg')), dir_name


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master - SVG 圆角矩形转 Path 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    %(prog)s examples/ppt169_demo
    %(prog)s examples/ppt169_demo -s final
    %(prog)s examples/ppt169_demo/svg_output/01_cover.svg

处理内容:
    将带 rx/ry 的 <rect> 转换为等效的 <path>
    处理后的 SVG 在 PowerPoint 中「转换为形状」时能保留圆角
'''
    )
    
    parser.add_argument('path', type=str, help='SVG 文件或项目目录路径')
    parser.add_argument('-s', '--source', type=str, default='output',
                        help='SVG 来源: output/final/flat/final_flat 或子目录名 (默认: output)')
    parser.add_argument('-o', '--output', type=str, default='svg_rounded',
                        help='输出目录名 (默认: svg_rounded)')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')
    
    args = parser.parse_args()
    
    input_path = Path(args.path)
    
    if not input_path.exists():
        print(f"错误: 路径不存在: {input_path}")
        sys.exit(1)
    
    verbose = args.verbose and not args.quiet
    quiet = args.quiet
    
    if not quiet:
        print("PPT Master - SVG 圆角矩形转 Path 工具")
        print("=" * 50)
    
    total_converted = 0
    
    if input_path.is_file() and input_path.suffix.lower() == '.svg':
        # 单文件模式
        output_path = input_path.with_stem(input_path.stem + '_rounded')
        
        if not quiet:
            print(f"  输入: {input_path}")
            print(f"  输出: {output_path}")
            print()
        
        success, count = process_svg_file(input_path, output_path, verbose)
        total_converted = count
        
        if success:
            if not quiet:
                print(f"[完成] 已保存: {output_path}")
        else:
            print(f"[失败] 处理失败")
            sys.exit(1)
    
    else:
        # 目录/项目模式
        svg_files, source_dir = find_svg_files(input_path, args.source)
        
        if not svg_files:
            print("错误: 未找到 SVG 文件")
            sys.exit(1)
        
        output_dir = input_path / args.output
        
        if not quiet:
            print(f"  项目路径: {input_path}")
            print(f"  SVG 来源: {source_dir}")
            print(f"  输出目录: {args.output}")
            print(f"  文件数量: {len(svg_files)}")
            print()
        
        success_count = 0
        for i, svg_file in enumerate(svg_files, 1):
            output_path = output_dir / svg_file.name
            
            if verbose:
                print(f"  [{i}/{len(svg_files)}] {svg_file.name}")
            
            success, count = process_svg_file(svg_file, output_path, verbose)
            
            if success:
                success_count += 1
                total_converted += count
                if not verbose and not quiet:
                    print(f"  [{i}/{len(svg_files)}] {svg_file.name} OK")
            else:
                if not quiet:
                    print(f"  [{i}/{len(svg_files)}] {svg_file.name} FAILED")
        
        if not quiet:
            print()
            print(f"[完成] 成功: {success_count}/{len(svg_files)}")
            print(f"  输出目录: {output_dir}")
    
    # 显示统计
    if not quiet:
        print()
        print(f"转换统计: 圆角矩形 -> path: {total_converted} 个")
    
    sys.exit(0)


if __name__ == '__main__':
    main()

