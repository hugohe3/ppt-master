#!/usr/bin/env python3
"""
SVG 最终化处理工具

将 svg_output/ 中的原始 SVG 复制到 svg_final/，并完成图标和图片的嵌入。
原始版本保留在 svg_output/ 作为模板参考。

用法：
    python3 tools/finalize_svg.py <项目目录>

示例：
    python3 tools/finalize_svg.py projects/my_project
    python3 tools/finalize_svg.py examples/ppt169_demo

流程：
    1. 复制 svg_output/ → svg_final/
    2. 嵌入图标（替换 <use data-icon="..."/>）
    3. 嵌入图片（转换为 Base64，可选）
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# 导入同目录的工具模块
sys.path.insert(0, str(Path(__file__).parent))
from embed_icons import process_svg_file as embed_icons_in_file
from embed_images import embed_images_in_svg


def finalize_project(project_dir: Path, embed_images: bool = False, dry_run: bool = False):
    """
    最终化处理项目中的 SVG 文件
    
    Args:
        project_dir: 项目目录路径
        embed_images: 是否嵌入图片（转为 Base64）
        dry_run: 是否仅预览不执行
    """
    svg_output = project_dir / 'svg_output'
    svg_final = project_dir / 'svg_final'
    icons_dir = Path(__file__).parent.parent / 'templates' / 'icons'
    
    # 检查 svg_output 是否存在
    if not svg_output.exists():
        print(f"❌ 未找到 svg_output 目录: {svg_output}")
        return False
    
    # 获取 SVG 文件列表
    svg_files = list(svg_output.glob('*.svg'))
    if not svg_files:
        print(f"❌ svg_output 中没有 SVG 文件")
        return False
    
    print(f"📁 项目目录: {project_dir}")
    print(f"📄 找到 {len(svg_files)} 个 SVG 文件")
    print()
    
    if dry_run:
        print("🔍 预览模式（不执行操作）")
        print()
        print("将执行以下操作：")
        print(f"  1. 复制 svg_output/ → svg_final/")
        print(f"  2. 在 svg_final/ 中嵌入图标")
        if embed_images:
            print(f"  3. 在 svg_final/ 中嵌入图片（Base64）")
        print()
        print("SVG 文件：")
        for f in svg_files:
            print(f"  - {f.name}")
        return True
    
    # 步骤 1: 复制目录
    print("📋 步骤 1/3: 复制 svg_output → svg_final")
    if svg_final.exists():
        shutil.rmtree(svg_final)
    shutil.copytree(svg_output, svg_final)
    print(f"   ✅ 已复制 {len(svg_files)} 个文件")
    print()
    
    # 步骤 2: 嵌入图标
    print("🎨 步骤 2/3: 嵌入图标")
    icons_count = 0
    for svg_file in svg_final.glob('*.svg'):
        count = embed_icons_in_file(svg_file, icons_dir, dry_run=False, verbose=False)
        if count > 0:
            print(f"   ✅ {svg_file.name}: {count} 个图标")
            icons_count += count
    if icons_count == 0:
        print("   ⏭️  无图标需要处理")
    print()
    
    # 步骤 3: 嵌入图片（可选）
    print("🖼️  步骤 3/3: 嵌入图片")
    if embed_images:
        images_count = 0
        for svg_file in svg_final.glob('*.svg'):
            count, _ = embed_images_in_svg(str(svg_file), dry_run=False)
            if count > 0:
                images_count += count
        if images_count == 0:
            print("   ⏭️  无图片需要处理")
    else:
        print("   ⏭️  跳过（使用 --embed-images 启用）")
    print()
    
    # 完成
    print("=" * 50)
    print("✅ 处理完成！")
    print()
    print(f"📂 原始版本: {svg_output}/")
    print(f"📂 最终版本: {svg_final}/")
    print()
    print("预览最终版本：")
    print(f"   cd {svg_final} && python3 -m http.server 8000")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='SVG 最终化处理：复制并嵌入图标/图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  %(prog)s projects/my_project           # 处理项目
  %(prog)s --dry-run projects/my_project # 预览操作
  %(prog)s --embed-images projects/xxx   # 同时嵌入图片（Base64）

目录结构：
  project/
  ├── svg_output/    # 原始版本（保留）
  ├── svg_final/     # 最终版本（生成）
  └── images/        # 图片资源
        '''
    )
    
    parser.add_argument('project_dir', type=Path, help='项目目录路径')
    parser.add_argument('--embed-images', action='store_true',
                        help='同时将图片转换为 Base64 嵌入（默认保持外部引用）')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='仅预览操作，不实际执行')
    
    args = parser.parse_args()
    
    if not args.project_dir.exists():
        print(f"❌ 项目目录不存在: {args.project_dir}")
        sys.exit(1)
    
    success = finalize_project(args.project_dir, args.embed_images, args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

