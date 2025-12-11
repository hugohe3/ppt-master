#!/usr/bin/env python3
"""
SVG 图片嵌入工具
将 SVG 中引用的外部图片转换为 Base64 内嵌格式

用法:
    python3 embed_images.py <svg_file> [svg_file2] ...
    python3 embed_images.py *.svg

示例:
    python3 embed_images.py examples/ppt169_demo/svg_output/01_封面.svg
    python3 embed_images.py examples/ppt169_demo/svg_output/*.svg
"""

import os
import base64
import re
import sys
import argparse

def get_mime_type(filename):
    """根据文件扩展名返回 MIME 类型"""
    ext = filename.lower().split('.')[-1]
    mime_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'svg': 'image/svg+xml',
    }
    return mime_map.get(ext, 'application/octet-stream')

def get_file_size_str(size_bytes):
    """将字节数转换为可读的文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def embed_images_in_svg(svg_path, dry_run=False):
    """
    将 SVG 文件中的外部图片转换为 Base64 内嵌
    
    Args:
        svg_path: SVG 文件路径
        dry_run: 如果为 True，只显示会处理的图片，不实际修改文件
    
    Returns:
        tuple: (处理的图片数量, 嵌入后的文件大小)
    """
    svg_dir = os.path.dirname(os.path.abspath(svg_path))
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content.encode('utf-8'))
    
    # 匹配 href="xxx.png" 或 href="xxx.jpg" 等（排除已经是 data: 的）
    pattern = r'href="(?!data:)([^"]+\.(png|jpg|jpeg|gif|webp))"'
    
    images_found = []
    images_embedded = 0
    
    def replace_with_base64(match):
        nonlocal images_embedded
        img_path = match.group(1)
        
        # 处理相对路径
        if not os.path.isabs(img_path):
            full_path = os.path.join(svg_dir, img_path)
        else:
            full_path = img_path
        
        if not os.path.exists(full_path):
            print(f"  ⚠️  Warning: Image not found: {img_path}")
            images_found.append((img_path, "NOT FOUND", 0))
            return match.group(0)
        
        img_size = os.path.getsize(full_path)
        
        if dry_run:
            images_found.append((img_path, "WILL EMBED", img_size))
            return match.group(0)
        
        with open(full_path, 'rb') as img_file:
            b64_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        mime_type = get_mime_type(img_path)
        images_embedded += 1
        images_found.append((img_path, "EMBEDDED", img_size))
        
        return f'href="data:{mime_type};base64,{b64_data}"'
    
    new_content = re.sub(pattern, replace_with_base64, content)
    
    new_size = len(new_content.encode('utf-8'))
    
    # 打印处理的图片
    if images_found:
        print(f"\n📄 {os.path.basename(svg_path)}")
        for img_path, status, size in images_found:
            size_str = get_file_size_str(size) if size > 0 else ""
            if status == "EMBEDDED":
                print(f"   ✅ {img_path} ({size_str})")
            elif status == "WILL EMBED":
                print(f"   📋 {img_path} ({size_str}) [dry-run]")
            else:
                print(f"   ❌ {img_path} ({status})")
        
        print(f"   📊 Size: {get_file_size_str(original_size)} → {get_file_size_str(new_size)}")
    
    if not dry_run and images_embedded > 0:
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return (images_embedded, new_size)

def main():
    parser = argparse.ArgumentParser(
        description='将 SVG 中引用的外部图片转换为 Base64 内嵌格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s 01_封面.svg              # 处理单个文件
  %(prog)s *.svg                     # 处理当前目录所有 SVG
  %(prog)s --dry-run *.svg           # 预览将处理的文件
        '''
    )
    parser.add_argument('files', nargs='+', help='要处理的 SVG 文件')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='只显示将要处理的图片，不实际修改文件')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 Dry-run mode: 只预览，不实际修改文件\n")
    
    total_images = 0
    total_files = 0
    
    for svg_file in args.files:
        if not os.path.exists(svg_file):
            print(f"❌ File not found: {svg_file}")
            continue
        
        if not svg_file.endswith('.svg'):
            print(f"⏭️  Skipping non-SVG file: {svg_file}")
            continue
        
        images, _ = embed_images_in_svg(svg_file, dry_run=args.dry_run)
        if images > 0:
            total_images += images
            total_files += 1
    
    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f"📋 预览完成: 将处理 {total_files} 个文件中的 {total_images} 张图片")
    else:
        print(f"✅ 处理完成: 已嵌入 {total_files} 个文件中的 {total_images} 张图片")

if __name__ == '__main__':
    main()
