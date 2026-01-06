#!/usr/bin/env python3
"""
图片尺寸分析工具
================
分析指定文件夹中所有图片的宽度、高度、长宽比，输出PPT适配建议。

用法:
    python tools/analyze_images.py <images_folder_path>
    python tools/analyze_images.py projects/xxx/images

输出:
    - 控制台显示分析报告
    - 在图片目录的父目录生成 image_analysis.csv
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL/Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


def analyze_images(images_dir):
    """分析指定目录下所有图片的尺寸信息"""
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}
    
    results = []
    
    # 遍历目录中的所有文件
    for filename in sorted(os.listdir(images_dir)):
        filepath = os.path.join(images_dir, filename)
        
        # 检查是否为图片文件
        if os.path.isfile(filepath) and Path(filename).suffix.lower() in image_extensions:
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    aspect_ratio = width / height
                    
                    # 判断适合的PPT布局建议
                    if aspect_ratio > 1.5:
                        layout_hint = "宽幅横图"
                    elif aspect_ratio > 1.2:
                        layout_hint = "标准横图"
                    elif aspect_ratio > 0.8:
                        layout_hint = "接近正方形"
                    elif aspect_ratio > 0.6:
                        layout_hint = "标准竖图"
                    else:
                        layout_hint = "窄幅竖图"
                    
                    results.append({
                        'filename': filename,
                        'width': width,
                        'height': height,
                        'aspect_ratio': aspect_ratio,
                        'layout_hint': layout_hint,
                        'filesize_kb': os.path.getsize(filepath) / 1024
                    })
            except Exception as e:
                print(f"[WARN] Cannot read {filename}: {e}")
    
    return results


def print_results(results):
    """打印分析结果"""
    
    print("\n" + "="*100)
    print("Image Size Analysis Report")
    print("="*100)
    
    # 表头
    print(f"\n{'No.':<4} {'Width':<7} {'Height':<7} {'Ratio':<7} {'Size':<10} {'Layout':<15} {'Filename'}")
    print("-"*100)
    
    for i, img in enumerate(results, 1):
        print(f"{i:<4} {img['width']:<7} {img['height']:<7} {img['aspect_ratio']:<7.2f} {img['filesize_kb']:<10.1f}KB {img['layout_hint']:<15} {img['filename'][:40]}")
    
    print("-"*100)
    print(f"Total: {len(results)} images\n")
    
    # 按长宽比分组统计
    print("\nGroup by Aspect Ratio:")
    print("-"*50)
    
    categories = {
        "Wide (>1.5)": [],
        "Standard (1.2-1.5)": [],
        "Square (0.8-1.2)": [],
        "Portrait (0.6-0.8)": [],
        "Narrow (<0.6)": []
    }
    
    for img in results:
        ar = img['aspect_ratio']
        if ar > 1.5:
            categories["Wide (>1.5)"].append(img)
        elif ar > 1.2:
            categories["Standard (1.2-1.5)"].append(img)
        elif ar > 0.8:
            categories["Square (0.8-1.2)"].append(img)
        elif ar > 0.6:
            categories["Portrait (0.6-0.8)"].append(img)
        else:
            categories["Narrow (<0.6)"].append(img)
    
    for cat, imgs in categories.items():
        if imgs:
            print(f"\\n{cat}: {len(imgs)} images")
            for img in imgs[:5]:  # 只显示前5个
                print(f"  - {img['width']}x{img['height']} (ratio {img['aspect_ratio']:.2f}) - {img['filename'][:35]}...")
            if len(imgs) > 5:
                print(f"  ... and {len(imgs) - 5} more")

    # 输出PPT适配建议
    print("\\n" + "="*100)
    print("PPT Fit Suggestions (16:9 = 1280x720)")
    print("="*100)
    
    ppt_width, ppt_height = 1280, 720
    ppt_ratio = ppt_width / ppt_height
    
    print(f"\\nStandard PPT canvas: {ppt_width}x{ppt_height} (ratio {ppt_ratio:.2f})")
    
    fit_count = 0
    for img in results:
        if 1.5 <= img['aspect_ratio'] <= 2.0:
            fit_count += 1
    
    print(f"\\nImages suitable for full-screen display: {fit_count}")


def generate_markdown(results):
    """生成 Markdown 格式的图片资源清单"""
    print("\\n" + "="*100)
    print("Markdown Snippet for Strategist (Copy & Paste)")
    print("="*100)
    print("\\n## 图片资源清单（自动扫描结果）\\n")
    print("| 文件名 | 尺寸 | 比例 | 布局建议 | 用途 | 状态 | 生成描述 |")
    print("|--------|------|------|----------|------|------|----------|")
    
    for img in results:
        # 简化布局建议描述，使其更符合 Strategist 的习惯
        layout_desc = img['layout_hint']
        if img['aspect_ratio'] > 2.0:
            layout_desc += " (适合通栏/分割)"
        elif img['aspect_ratio'] > 1.2:
            layout_desc += " (适合全屏/插图)"
        elif img['aspect_ratio'] < 0.8:
            layout_desc += " (适合左右分栏)"
            
        # 用途和生成描述需策略师手动填写，这里用占位符
        print(f"| {img['filename']} | {img['width']}×{img['height']} | {img['aspect_ratio']:.2f} | {layout_desc} | （待填写） | 已有 | - |")
    print("\\n" + "="*100 + "\\n")


def save_csv(results, csv_path):
    """保存结果到CSV文件"""
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("No,Filename,Width,Height,AspectRatio,SizeKB,Layout\n")
        for i, img in enumerate(results, 1):
            f.write(f"{i},{img['filename']},{img['width']},{img['height']},{img['aspect_ratio']:.2f},{img['filesize_kb']:.1f},{img['layout_hint']}\n")
    print(f"\nCSV saved to: {csv_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_images.py <images_folder_path>")
        print("Example: python analyze_images.py projects/myproject/images")
        print("         python analyze_images.py C:/path/to/images")
        sys.exit(1)
    
    images_dir = sys.argv[1]
    
    # 转换为绝对路径
    images_dir = os.path.abspath(images_dir)
    
    if not os.path.exists(images_dir):
        print(f"Error: Directory not found: {images_dir}")
        sys.exit(1)
    
    if not os.path.isdir(images_dir):
        print(f"Error: Not a directory: {images_dir}")
        sys.exit(1)
    
    print(f"Analyzing: {images_dir}")
    
    results = analyze_images(images_dir)
    
    if results:
        print_results(results)
        generate_markdown(results)
        
        # 保存到CSV文件（保存在图片目录的父目录）
        parent_dir = os.path.dirname(images_dir)
        csv_path = os.path.join(parent_dir, "image_analysis.csv")
        save_csv(results, csv_path)
    else:
        print("No image files found in the directory.")


if __name__ == "__main__":
    main()

