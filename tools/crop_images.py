#!/usr/bin/env python3
"""
PPT Master - 智能图片裁剪工具

根据 SVG 中 <image> 元素的 preserveAspectRatio 属性智能裁剪图片：
- slice: 裁剪填充（类似 CSS object-fit: cover）
- meet: 完整显示，不裁剪（类似 CSS object-fit: contain）

支持9种对齐方式：
- xMinYMin / xMidYMin / xMaxYMin (顶部对齐)
- xMinYMid / xMidYMid / xMaxYMid (垂直居中)
- xMinYMax / xMidYMax / xMaxYMax (底部对齐)

用法：
    python tools/crop_images.py <SVG文件或目录> [--dry-run]
"""

import os
import re
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import unquote

try:
    from PIL import Image
except ImportError:
    print("Error: PIL (Pillow) is required. Run: pip install Pillow")
    exit(1)


def parse_preserve_aspect_ratio(attr: str) -> tuple:
    """
    解析 preserveAspectRatio 属性
    
    返回: (align, meet_or_slice)
        align: 如 'xMidYMid'
        meet_or_slice: 'meet' 或 'slice'
    """
    if not attr:
        return ('xMidYMid', 'meet')  # 默认值
    
    parts = attr.strip().split()
    align = parts[0] if parts else 'xMidYMid'
    meet_or_slice = parts[1] if len(parts) > 1 else 'meet'
    
    return (align, meet_or_slice)


def get_crop_anchor(align: str) -> tuple:
    """
    根据 align 值返回裁剪锚点
    
    返回: (x_anchor, y_anchor)
        x_anchor: 0.0 (左), 0.5 (中), 1.0 (右)
        y_anchor: 0.0 (上), 0.5 (中), 1.0 (下)
    """
    x_map = {'xMin': 0.0, 'xMid': 0.5, 'xMax': 1.0}
    y_map = {'YMin': 0.0, 'YMid': 0.5, 'YMax': 1.0}
    
    x_anchor = 0.5
    y_anchor = 0.5
    
    for key, val in x_map.items():
        if key in align:
            x_anchor = val
            break
    
    for key, val in y_map.items():
        if key in align:
            y_anchor = val
            break
    
    return (x_anchor, y_anchor)


def crop_image_to_size(img: Image.Image, target_width: int, target_height: int, 
                       x_anchor: float = 0.5, y_anchor: float = 0.5) -> Image.Image:
    """
    按目标比例裁剪图片，保持原图分辨率（不缩放）
    
    新逻辑：只按目标宽高比裁剪原图，不进行任何缩放操作，
    这样可以保持原图的分辨率和清晰度。
    
    Args:
        img: PIL Image 对象
        target_width: 目标宽度（用于计算比例）
        target_height: 目标高度（用于计算比例）
        x_anchor: 水平锚点 (0=左, 0.5=中, 1=右)
        y_anchor: 垂直锚点 (0=上, 0.5=中, 1=下)
    
    Returns:
        裁剪后的 PIL Image 对象（保持原图分辨率）
    """
    img_width, img_height = img.size
    
    # 计算目标宽高比
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height
    
    # 根据比例计算裁剪区域（在原图上裁剪，不缩放）
    if img_ratio > target_ratio:
        # 原图更宽，需要裁剪左右两侧
        crop_height = img_height
        crop_width = int(img_height * target_ratio)
    else:
        # 原图更高，需要裁剪上下两侧
        crop_width = img_width
        crop_height = int(img_width / target_ratio)
    
    # 根据锚点计算裁剪位置
    extra_width = img_width - crop_width
    extra_height = img_height - crop_height
    
    left = int(extra_width * x_anchor)
    top = int(extra_height * y_anchor)
    right = left + crop_width
    bottom = top + crop_height
    
    # 只裁剪，不缩放
    return img.crop((left, top, right, bottom))


def process_svg_images(svg_file: str, output_dir: str = None, dry_run: bool = False, 
                       verbose: bool = True) -> tuple:
    """
    处理 SVG 文件中的图片，根据 preserveAspectRatio 属性进行裁剪
    
    Args:
        svg_file: SVG 文件路径
        output_dir: 裁剪后图片的输出目录（默认为 images/cropped/）
        dry_run: 仅预览，不实际处理
        verbose: 详细输出
    
    Returns:
        (processed_count, error_count)
    """
    svg_path = Path(svg_file)
    svg_dir = svg_path.parent
    
    # 默认输出目录
    if output_dir is None:
        # 查找项目的 images 目录
        # svg_output 或 svg_final 的父目录下的 images
        project_dir = svg_dir.parent
        output_dir = project_dir / 'images' / 'cropped'
    else:
        output_dir = Path(output_dir)
    
    # 解析 SVG
    try:
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
    except Exception as e:
        if verbose:
            print(f"  [ERROR] 解析 SVG 失败: {e}")
        return (0, 1)
    
    ns = {'svg': 'http://www.w3.org/2000/svg', 'xlink': 'http://www.w3.org/1999/xlink'}
    
    processed_count = 0
    error_count = 0
    modified = False
    
    # 查找所有 image 元素
    for image in root.iter('{http://www.w3.org/2000/svg}image'):
        # 获取 href 属性
        href = image.get('{http://www.w3.org/1999/xlink}href') or image.get('href')
        if not href:
            continue
        
        # 跳过 base64 内嵌图片
        if href.startswith('data:'):
            continue
        
        # 获取 preserveAspectRatio 属性
        par = image.get('preserveAspectRatio', '')
        align, mode = parse_preserve_aspect_ratio(par)
        
        # 只处理 slice 模式
        if mode != 'slice':
            continue
        
        # 获取目标尺寸
        try:
            target_width = int(float(image.get('width', 0)))
            target_height = int(float(image.get('height', 0)))
        except (ValueError, TypeError):
            continue
        
        if target_width <= 0 or target_height <= 0:
            continue
        
        # 解析图片路径
        href_decoded = unquote(href)
        if href_decoded.startswith('../'):
            img_path = (svg_dir / href_decoded).resolve()
        else:
            img_path = (svg_dir / href_decoded).resolve()
        
        if not img_path.exists():
            if verbose:
                print(f"    [SKIP] 图片不存在: {href}")
            continue
        
        # 获取裁剪锚点
        x_anchor, y_anchor = get_crop_anchor(align)
        
        if dry_run:
            if verbose:
                print(f"    [DRY] {img_path.name} -> {target_width}x{target_height} "
                      f"(align: {align}, anchor: {x_anchor},{y_anchor})")
            processed_count += 1
            continue
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 打开并处理图片
            img = Image.open(img_path)
            
            # 转换模式
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 裁剪
            cropped = crop_image_to_size(img, target_width, target_height, x_anchor, y_anchor)
            
            # 生成输出文件名（保持原文件名，放到 cropped 目录）
            output_filename = img_path.name
            output_path = output_dir / output_filename
            
            # 保存
            if img_path.suffix.lower() == '.png':
                cropped.save(output_path, 'PNG', optimize=True)
            else:
                cropped.save(output_path, 'JPEG', quality=90, optimize=True)
            
            if verbose:
                print(f"    [OK] {img_path.name}: {img.size} -> {target_width}x{target_height} "
                      f"({align})")
            
            # 更新 SVG 中的图片路径
            new_href = f"../images/cropped/{output_filename}"
            if image.get('{http://www.w3.org/1999/xlink}href'):
                image.set('{http://www.w3.org/1999/xlink}href', new_href)
            else:
                image.set('href', new_href)
            
            # 移除 preserveAspectRatio（图片已是正确尺寸）
            if 'preserveAspectRatio' in image.attrib:
                del image.attrib['preserveAspectRatio']
            
            modified = True
            processed_count += 1
            
        except Exception as e:
            if verbose:
                print(f"    [ERROR] {img_path.name}: {e}")
            error_count += 1
    
    # 保存修改后的 SVG
    if modified and not dry_run:
        tree.write(str(svg_path), encoding='unicode', xml_declaration=False)
    
    return (processed_count, error_count)


def process_directory(directory: str, dry_run: bool = False, verbose: bool = True) -> tuple:
    """处理目录中的所有 SVG 文件"""
    directory = Path(directory)
    total_processed = 0
    total_errors = 0
    
    for svg_file in directory.glob('*.svg'):
        if verbose:
            print(f"  处理: {svg_file.name}")
        processed, errors = process_svg_images(str(svg_file), dry_run=dry_run, verbose=verbose)
        total_processed += processed
        total_errors += errors
    
    return (total_processed, total_errors)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='PPT Master - 智能图片裁剪工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  %(prog)s projects/my_project/svg_output
  %(prog)s page_01.svg --dry-run
  
preserveAspectRatio 用法：
  xMidYMid slice   居中裁剪（默认）
  xMidYMin slice   保留顶部
  xMidYMax slice   保留底部
  xMinYMid slice   保留左侧
  xMaxYMid slice   保留右侧
  xMidYMid meet    完整显示，不裁剪
        '''
    )
    
    parser.add_argument('path', type=Path, help='SVG 文件或目录')
    parser.add_argument('--dry-run', '-n', action='store_true', help='仅预览，不实际处理')
    parser.add_argument('--quiet', '-q', action='store_true', help='安静模式')
    
    args = parser.parse_args()
    
    if not args.path.exists():
        print(f"[ERROR] 路径不存在: {args.path}")
        exit(1)
    
    print("PPT Master - 智能图片裁剪")
    print("=" * 50)
    
    if args.path.is_file():
        processed, errors = process_svg_images(str(args.path), dry_run=args.dry_run, 
                                                verbose=not args.quiet)
    else:
        processed, errors = process_directory(str(args.path), dry_run=args.dry_run,
                                               verbose=not args.quiet)
    
    print()
    print(f"完成: {processed} 张图片已裁剪, {errors} 个错误")


if __name__ == '__main__':
    main()
