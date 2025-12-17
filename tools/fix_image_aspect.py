#!/usr/bin/env python3
"""
SVG 图片宽高比修复工具

修复 SVG 中 <image> 元素的尺寸，使其与图片原始宽高比一致。
这样在 PowerPoint 将 SVG 转换为形状时，图片不会被拉伸变形。

原理：
    PowerPoint 在将 SVG 转换为可编辑形状时，会忽略 preserveAspectRatio 属性，
    直接将图片拉伸以填满 width/height 指定的区域。
    
    此工具会读取实际图片的宽高比，重新计算 <image> 元素的 x, y, width, height，
    使图片居中显示且保持原始宽高比。

用法:
    python3 tools/fix_image_aspect.py <svg_file> [svg_file2] ...
    python3 tools/fix_image_aspect.py projects/xxx/svg_output/*.svg
    
    # 预览模式
    python3 tools/fix_image_aspect.py --dry-run projects/xxx/svg_output/*.svg

示例:
    python3 tools/fix_image_aspect.py projects/应急避难场所专项规划/svg_output/slide_06_current_overview.svg
"""

import os
import re
import sys
import base64
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET

# 尝试导入 PIL，用于获取图片尺寸
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[WARN] PIL not installed. Install with: pip install Pillow")
    print("       Will try to use basic method for JPEG/PNG files.")


def get_image_dimensions_pil(image_path):
    """使用 PIL 获取图片尺寸"""
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"  [WARN] Cannot read image with PIL: {e}")
        return None, None


def get_image_dimensions_basic(image_path):
    """基本方法获取图片尺寸（不依赖 PIL）"""
    try:
        with open(image_path, 'rb') as f:
            data = f.read(64)  # 读取头部信息
        
        # PNG
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            w = int.from_bytes(data[16:20], 'big')
            h = int.from_bytes(data[20:24], 'big')
            return w, h
        
        # JPEG
        if data[:2] == b'\xff\xd8':
            # 需要完整读取文件来解析 JPEG
            with open(image_path, 'rb') as f:
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if not marker or len(marker) < 2:
                        break
                    if marker[0] != 0xff:
                        break
                    m = marker[1]
                    # SOF0, SOF2 markers contain dimensions
                    if m in (0xC0, 0xC2):
                        f.read(3)  # Skip length and precision
                        h = int.from_bytes(f.read(2), 'big')
                        w = int.from_bytes(f.read(2), 'big')
                        return w, h
                    elif m == 0xD9:  # EOI
                        break
                    elif m == 0xD8:  # SOI
                        continue
                    elif 0xD0 <= m <= 0xD7:  # RST
                        continue
                    else:
                        length = int.from_bytes(f.read(2), 'big')
                        f.seek(length - 2, 1)
        
        return None, None
    except Exception as e:
        print(f"  [WARN] Cannot read image dimensions: {e}")
        return None, None


def get_image_dimensions_from_base64(data_uri):
    """从 Base64 数据 URI 获取图片尺寸"""
    import io
    try:
        # 解析 data URI
        match = re.match(r'data:image/(\w+);base64,(.+)', data_uri)
        if not match:
            return None, None
        
        img_format = match.group(1)
        b64_data = match.group(2)
        img_bytes = base64.b64decode(b64_data)
        
        if HAS_PIL:
            with Image.open(io.BytesIO(img_bytes)) as img:
                return img.width, img.height
        else:
            # 使用基本方法
            if img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                w = int.from_bytes(img_bytes[16:20], 'big')
                h = int.from_bytes(img_bytes[20:24], 'big')
                return w, h
        
        return None, None
    except Exception as e:
        print(f"  [WARN] Cannot parse base64 image: {e}")
        return None, None


def get_image_dimensions(href, svg_dir):
    """获取图片尺寸"""
    # 处理 data URI
    if href.startswith('data:'):
        return get_image_dimensions_from_base64(href)
    
    # 处理外部文件
    if not os.path.isabs(href):
        full_path = os.path.join(svg_dir, href)
    else:
        full_path = href
    
    if not os.path.exists(full_path):
        print(f"  [WARN] Image not found: {href}")
        return None, None
    
    if HAS_PIL:
        return get_image_dimensions_pil(full_path)
    else:
        return get_image_dimensions_basic(full_path)


def calculate_fitted_dimensions(img_width, img_height, box_width, box_height, mode='meet'):
    """
    计算图片在框内的适合尺寸
    
    Args:
        img_width, img_height: 图片原始尺寸
        box_width, box_height: 容器框尺寸
        mode: 'meet' 保持宽高比，完全显示图片（可能有留白）
              'slice' 保持宽高比，完全填充容器（可能裁剪）
    
    Returns:
        (new_width, new_height, offset_x, offset_y)
    """
    img_ratio = img_width / img_height
    box_ratio = box_width / box_height
    
    if mode == 'meet':
        # 完全显示图片，可能有留白
        if img_ratio > box_ratio:
            # 图片更宽，以宽度为准
            new_width = box_width
            new_height = box_width / img_ratio
        else:
            # 图片更高，以高度为准
            new_height = box_height
            new_width = box_height * img_ratio
    else:  # slice
        # 完全填充容器，可能裁剪
        if img_ratio > box_ratio:
            # 图片更宽，以高度为准
            new_height = box_height
            new_width = box_height * img_ratio
        else:
            # 图片更高，以宽度为准
            new_width = box_width
            new_height = box_width / img_ratio
    
    # 居中偏移
    offset_x = (box_width - new_width) / 2
    offset_y = (box_height - new_height) / 2
    
    return new_width, new_height, offset_x, offset_y


def fix_image_aspect_in_svg(svg_path, dry_run=False, verbose=True):
    """
    修复 SVG 中图片的宽高比
    
    Args:
        svg_path: SVG 文件路径
        dry_run: 是否只预览不修改
        verbose: 是否输出详细信息
    
    Returns:
        修复的图片数量
    """
    svg_dir = os.path.dirname(os.path.abspath(svg_path))
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 注册 SVG 命名空间
    namespaces = {
        '': 'http://www.w3.org/2000/svg',
        'xlink': 'http://www.w3.org/1999/xlink',
        'svg': 'http://www.w3.org/2000/svg',
        'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    }
    
    for prefix, uri in namespaces.items():
        if prefix:
            ET.register_namespace(prefix, uri)
        else:
            ET.register_namespace('', uri)
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"  [ERROR] Cannot parse SVG: {e}")
        return 0
    
    # 查找所有 image 元素
    fixed_count = 0
    
    # 检查带命名空间和不带命名空间的 image 元素
    for ns_prefix in ['', '{http://www.w3.org/2000/svg}']:
        for image_elem in root.iter(f'{ns_prefix}image'):
            # 获取 href 属性（支持 xlink:href 和 href）
            href = image_elem.get('{http://www.w3.org/1999/xlink}href')
            if href is None:
                href = image_elem.get('href')
            if href is None:
                continue
            
            # 获取当前尺寸和位置
            try:
                x = float(image_elem.get('x', 0))
                y = float(image_elem.get('y', 0))
                width = float(image_elem.get('width', 0))
                height = float(image_elem.get('height', 0))
            except (ValueError, TypeError):
                continue
            
            if width <= 0 or height <= 0:
                continue
            
            # 获取 preserveAspectRatio
            par = image_elem.get('preserveAspectRatio', 'xMidYMid meet')
            
            # 解析 preserveAspectRatio
            # 格式: <align> [<meetOrSlice>]
            # 例如: xMidYMid meet, xMidYMid slice, none
            par_parts = par.split()
            align = par_parts[0] if par_parts else 'xMidYMid'
            meet_or_slice = par_parts[1] if len(par_parts) > 1 else 'meet'
            
            if align == 'none':
                # 如果是 none，不需要修复
                continue
            
            # 获取图片原始尺寸
            img_width, img_height = get_image_dimensions(href, svg_dir)
            if img_width is None or img_height is None:
                continue
            
            # 计算适合的尺寸
            mode = 'slice' if meet_or_slice == 'slice' else 'meet'
            new_width, new_height, offset_x, offset_y = calculate_fitted_dimensions(
                img_width, img_height, width, height, mode
            )
            
            # 检查是否需要修改
            tolerance = 0.5  # 允许的误差
            if (abs(new_width - width) < tolerance and 
                abs(new_height - height) < tolerance):
                # 尺寸已经正确，无需修改
                continue
            
            if verbose:
                img_name = os.path.basename(href.split('?')[0][:50] if not href.startswith('data:') else '[base64]')
                print(f"  [FIX] {img_name}")
                print(f"        原图尺寸: {img_width}x{img_height} (ratio: {img_width/img_height:.3f})")
                print(f"        原框尺寸: {width}x{height} @ ({x}, {y})")
                print(f"        新框尺寸: {new_width:.1f}x{new_height:.1f} @ ({x + offset_x:.1f}, {y + offset_y:.1f})")
            
            if not dry_run:
                # 更新属性
                image_elem.set('x', f'{x + offset_x:.1f}')
                image_elem.set('y', f'{y + offset_y:.1f}')
                image_elem.set('width', f'{new_width:.1f}')
                image_elem.set('height', f'{new_height:.1f}')
                # 移除 preserveAspectRatio，因为现在尺寸已经正确
                if 'preserveAspectRatio' in image_elem.attrib:
                    del image_elem.attrib['preserveAspectRatio']
            
            fixed_count += 1
    
    if not dry_run and fixed_count > 0:
        # 保存修改
        tree.write(svg_path, encoding='unicode', xml_declaration=True)
    
    return fixed_count


def main():
    parser = argparse.ArgumentParser(
        description='修复 SVG 中图片的宽高比，防止 PowerPoint 转换时拉伸变形',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s slide_01.svg                    # 处理单个文件
  %(prog)s *.svg                           # 处理当前目录所有 SVG
  %(prog)s --dry-run *.svg                 # 预览将处理的文件
  %(prog)s projects/xxx/svg_output/*.svg   # 处理项目目录
        '''
    )
    parser.add_argument('files', nargs='+', help='要处理的 SVG 文件')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='只显示将要修复的图片，不实际修改文件')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='安静模式，减少输出')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("[INFO] 预览模式：只显示将要修改的内容，不实际修改文件\n")
    
    total_fixed = 0
    total_files = 0
    
    for svg_file in args.files:
        if not os.path.exists(svg_file):
            if not args.quiet:
                print(f"[ERROR] 文件不存在: {svg_file}")
            continue
        
        if not svg_file.endswith('.svg'):
            if not args.quiet:
                print(f"[SKIP] 跳过非 SVG 文件: {svg_file}")
            continue
        
        if not args.quiet:
            print(f"\n[FILE] {os.path.basename(svg_file)}")
        
        fixed = fix_image_aspect_in_svg(svg_file, dry_run=args.dry_run, verbose=not args.quiet)
        
        if fixed > 0:
            total_fixed += fixed
            total_files += 1
        elif not args.quiet:
            print("       无需修复")
    
    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f"[预览] 将修复 {total_fixed} 张图片 (共 {total_files} 个文件)")
    else:
        print(f"[完成] 已修复 {total_fixed} 张图片 (共 {total_files} 个文件)")


if __name__ == '__main__':
    main()
