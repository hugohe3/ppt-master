#!/usr/bin/env python3
"""
PPT Master - SVG 后处理工具（统一入口）

将 svg_output/ 中的 SVG 文件处理后输出到 svg_final/。
默认执行全部处理，也可通过参数指定部分处理。

用法：
    # 默认执行全部处理（推荐）
    python3 scripts/finalize_svg.py <项目目录>
    
    # 只执行部分处理
    python3 scripts/finalize_svg.py <项目目录> --only embed-icons fix-rounded

示例：
    python3 scripts/finalize_svg.py projects/my_project
    python3 scripts/finalize_svg.py examples/ppt169_demo --only embed-icons

处理选项：
    embed-icons   - 替换 <use data-icon="..."/> 为实际图标 SVG
    crop-images   - 根据 preserveAspectRatio="slice" 智能裁剪图片
    fix-aspect    - 修复图片宽高比（防止 PPT 转形状时拉伸）
    embed-images  - 将外部图片转换为 Base64 嵌入
    flatten-text  - 将 <tspan> 转为独立 <text>（用于特殊渲染器）
    fix-rounded   - 将 <rect rx="..."/> 转为 <path>（用于 PPT 转形状）
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
from fix_image_aspect import fix_image_aspect_in_svg
from crop_images import process_svg_images as crop_images_in_svg


def safe_print(text):
    """安全打印，处理 Windows 终端编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        text = text.replace('✅', '[OK]').replace('❌', '[ERROR]')
        text = text.replace('📁', '[DIR]').replace('📄', '[FILE]')
        print(text)


def process_flatten_text(svg_file: Path, verbose: bool = False) -> bool:
    """对单个 SVG 文件进行文本扁平化处理（原地修改）"""
    try:
        from flatten_tspan import flatten_text_with_tspans
        from xml.etree import ElementTree as ET
        
        tree = ET.parse(str(svg_file))
        changed = flatten_text_with_tspans(tree)
        
        if changed:
            tree.write(str(svg_file), encoding='unicode', xml_declaration=False)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: 文本已扁平化")
        return changed
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return False


def process_rounded_rect(svg_file: Path, verbose: bool = False) -> int:
    """对单个 SVG 文件进行圆角矩形转换（原地修改）"""
    try:
        from svg_rect_to_path import process_svg
        
        with open(svg_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        processed, count = process_svg(content, verbose=False)
        
        if count > 0:
            with open(svg_file, 'w', encoding='utf-8') as f:
                f.write(processed)
            if verbose:
                safe_print(f"   [OK] {svg_file.name}: {count} 个圆角矩形")
        return count
    except Exception as e:
        if verbose:
            safe_print(f"   [ERROR] {svg_file.name}: {e}")
        return 0


def finalize_project(project_dir: Path, options: dict, dry_run: bool = False, quiet: bool = False):
    """
    最终化处理项目中的 SVG 文件
    
    Args:
        project_dir: 项目目录路径
        options: 处理选项字典
        dry_run: 是否仅预览不执行
        quiet: 安静模式，减少输出
    """
    svg_output = project_dir / 'svg_output'
    svg_final = project_dir / 'svg_final'
    icons_dir = Path(__file__).parent.parent / 'templates' / 'icons'
    
    # 检查 svg_output 是否存在
    if not svg_output.exists():
        safe_print(f"[ERROR] 未找到 svg_output 目录: {svg_output}")
        return False
    
    # 获取 SVG 文件列表
    svg_files = list(svg_output.glob('*.svg'))
    if not svg_files:
        safe_print(f"[ERROR] svg_output 中没有 SVG 文件")
        return False
    
    if not quiet:
        print()
        safe_print(f"[DIR] 项目: {project_dir.name}")
        safe_print(f"[FILE] {len(svg_files)} 个 SVG 文件")
    
    if dry_run:
        safe_print("[PREVIEW] 预览模式，不执行操作")
        return True
    
    # 步骤 1: 复制目录
    if svg_final.exists():
        shutil.rmtree(svg_final)
    shutil.copytree(svg_output, svg_final)
    
    if not quiet:
        print()
    
    # 步骤 2: 嵌入图标
    if options.get('embed_icons'):
        if not quiet:
            safe_print("[1/6] 嵌入图标...")
        icons_count = 0
        for svg_file in svg_final.glob('*.svg'):
            count = embed_icons_in_file(svg_file, icons_dir, dry_run=False, verbose=False)
            icons_count += count
        if not quiet:
            if icons_count > 0:
                safe_print(f"      {icons_count} 个图标已嵌入")
            else:
                safe_print("      无图标")
    
    # 步骤 3: 智能裁剪图片（根据 preserveAspectRatio="slice"）
    if options.get('crop_images'):
        if not quiet:
            safe_print("[2/6] 智能裁剪图片...")
        crop_count = 0
        crop_errors = 0
        for svg_file in svg_final.glob('*.svg'):
            count, errors = crop_images_in_svg(str(svg_file), dry_run=False, verbose=False)
            crop_count += count
            crop_errors += errors
        if not quiet:
            if crop_count > 0:
                safe_print(f"      {crop_count} 张图片已裁剪")
            else:
                safe_print("      无需裁剪（无 slice 属性的图片）")
    
    # 步骤 4: 修复图片宽高比（防止 PPT 转形状时拉伸）
    if options.get('fix_aspect'):
        if not quiet:
            safe_print("[3/6] 修复图片宽高比...")
        aspect_count = 0
        for svg_file in svg_final.glob('*.svg'):
            count = fix_image_aspect_in_svg(str(svg_file), dry_run=False, verbose=False)
            aspect_count += count
        if not quiet:
            if aspect_count > 0:
                safe_print(f"      {aspect_count} 张图片已修复")
            else:
                safe_print("      无图片")
    
    # 步骤 5: 嵌入图片
    if options.get('embed_images'):
        if not quiet:
            safe_print("[4/6] 嵌入图片...")
        images_count = 0
        for svg_file in svg_final.glob('*.svg'):
            count, _ = embed_images_in_svg(str(svg_file), dry_run=False)
            images_count += count
        if not quiet:
            if images_count > 0:
                safe_print(f"      {images_count} 张图片已嵌入")
            else:
                safe_print("      无图片")
    
    # 步骤 6: 文本扁平化
    if options.get('flatten_text'):
        if not quiet:
            safe_print("[5/6] 文本扁平化...")
        flatten_count = 0
        for svg_file in svg_final.glob('*.svg'):
            if process_flatten_text(svg_file, verbose=False):
                flatten_count += 1
        if not quiet:
            if flatten_count > 0:
                safe_print(f"      {flatten_count} 个文件已处理")
            else:
                safe_print("      无需处理")
    
    # 步骤 7: 圆角转 Path
    if options.get('fix_rounded'):
        if not quiet:
            safe_print("[6/6] 圆角转 Path...")
        rounded_count = 0
        for svg_file in svg_final.glob('*.svg'):
            count = process_rounded_rect(svg_file, verbose=False)
            rounded_count += count
        if not quiet:
            if rounded_count > 0:
                safe_print(f"      {rounded_count} 个圆角矩形已转换")
            else:
                safe_print("      无圆角矩形")
    
    # 完成
    if not quiet:
        print()
        safe_print("[OK] 完成!")
        print()
        print("后续操作：")
        print(f"  python scripts/svg_to_pptx.py \"{project_dir}\" -s final")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master - SVG 后处理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例：
  %(prog)s projects/my_project           # 执行全部处理（默认）
  %(prog)s projects/my_project --only embed-icons fix-rounded
  %(prog)s projects/my_project -q        # 安静模式

处理选项（用于 --only）：
  embed-icons   嵌入图标
  crop-images   智能裁剪图片（根据 preserveAspectRatio）
  fix-aspect    修复图片宽高比（防止 PPT 转形状时拉伸）
  embed-images  嵌入图片
  flatten-text  文本扁平化
  fix-rounded   圆角转 Path
        '''
    )
    
    parser.add_argument('project_dir', type=Path, help='项目目录路径')
    parser.add_argument('--only', nargs='+', metavar='OPTION',
                        choices=['embed-icons', 'crop-images', 'fix-aspect', 'embed-images', 'flatten-text', 'fix-rounded'],
                        help='只执行指定的处理（默认执行全部）')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='仅预览操作，不实际执行')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='安静模式，减少输出')
    
    args = parser.parse_args()
    
    if not args.project_dir.exists():
        safe_print(f"[ERROR] 项目目录不存在: {args.project_dir}")
        sys.exit(1)
    
    # 确定处理选项
    if args.only:
        # 只执行指定的处理
        options = {
            'embed_icons': 'embed-icons' in args.only,
            'crop_images': 'crop-images' in args.only,
            'fix_aspect': 'fix-aspect' in args.only,
            'embed_images': 'embed-images' in args.only,
            'flatten_text': 'flatten-text' in args.only,
            'fix_rounded': 'fix-rounded' in args.only,
        }
    else:
        # 默认执行全部
        options = {
            'embed_icons': True,
            'crop_images': True,
            'fix_aspect': True,
            'embed_images': True,
            'flatten_text': True,
            'fix_rounded': True,
        }
    
    success = finalize_project(args.project_dir, options, args.dry_run, args.quiet)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
