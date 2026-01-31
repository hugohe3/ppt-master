#!/usr/bin/env python3
"""
PPT Master - 讲稿拆分工具

将 total.md 讲稿文件拆分为多个独立的讲稿文件，每个文件对应一个 SVG 页面。

用法:
    python3 tools/total_md_split.py <项目路径>
    python3 tools/total_md_split.py <项目路径> -o output_dir

示例:
    python3 tools/total_md_split.py projects/<svg 标题>_ppt169_YYYYMMDD
    python3 tools/total_md_split.py projects/<svg 标题>_ppt169_YYYYMMDD -o notes

依赖:
    无（仅使用标准库）

注意:
    - 会检查 SVG 文件与讲稿的一一对应关系
    - 如果存在 SVG 没有对应的讲稿，会输出提示
    - 拆分后的文档不包含一级标题
    - 拆分后的文档命名与 SVG 文件同名，后缀改为 .md
"""

import sys
import os
import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

HEADING_RE = re.compile(r'^(#{1,6})\s*(.+?)\s*$')
HR_RE = re.compile(r'^\s*[-*]{3,}\s*$')


def normalize_title(title: str) -> str:
    """Normalize titles for fuzzy matching with SVG stems."""
    if not title:
        return ''
    text = title.strip()
    # Replace any non-alnum / non-CJK run with underscore
    text = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text.lower()





def extract_leading_number(text: str) -> Optional[int]:
    """Extract leading slide number if present."""
    if not text:
        return None
    
    # Try 1: Start with digits (standard)
    m = re.match(r'^(\d{1,3})', text.strip())
    if m:
        return int(m.group(1))
        
    # Try 2: Common prefixes (Slide X, Page X, 第X页)
    # Case insensitive for English
    text_lower = text.lower().strip()
    
    # Slide/Page X
    m = re.match(r'^(?:slide|page|p)\s*[-_:]?\s*(\d{1,3})', text_lower)
    if m:
        return int(m.group(1))
        
    # 第X页/张
    m = re.match(r'^第\s*(\d{1,3})\s*[页张]', text_lower)
    if m:
        return int(m.group(1))
        
    return None


def build_match_maps(svg_stems: List[str]) -> Tuple[set, Dict[str, List[str]], Dict[int, List[str]]]:
    exact = set(svg_stems)
    norm_map: Dict[str, List[str]] = {}
    num_map: Dict[int, List[str]] = {}
    for stem in svg_stems:
        norm = normalize_title(stem)
        if norm:
            norm_map.setdefault(norm, []).append(stem)
        num = extract_leading_number(stem)
        if num is not None:
            num_map.setdefault(num, []).append(stem)
    return exact, norm_map, num_map


def match_title(
    raw_title: str,
    exact: set,
    norm_map: Dict[str, List[str]],
    num_map: Dict[int, List[str]],
    svg_stems: Optional[List[str]] = None,
) -> Optional[str]:
    if raw_title in exact:
        return raw_title
    norm = normalize_title(raw_title)
    if norm in norm_map and len(norm_map[norm]) == 1:
        return norm_map[norm][0]
    num = extract_leading_number(raw_title)
    if num is not None and num in num_map and len(num_map[num]) == 1:
        return num_map[num][0]
    if norm and svg_stems:
        candidates = [s for s in svg_stems if norm in normalize_title(s)]
        if len(candidates) == 1:
            return candidates[0]
    return None


def find_svg_files(project_path: Path) -> List[Path]:
    """
    查找项目中的 SVG 文件

    Args:
        project_path: 项目目录路径

    Returns:
        SVG 文件列表（按文件名排序）
    """
    svg_dir = project_path / 'svg_output'

    if not svg_dir.exists():
        print(f"错误: {svg_dir} 目录不存在")
        return []

    return sorted(svg_dir.glob('*.svg'))


def parse_total_md(md_path: Path, svg_stems: Optional[List[str]] = None, verbose: bool = True) -> Dict[str, str]:
    """
    解析 total.md 文件，提取每个一级标题对应的讲稿内容

    Args:
        md_path: total.md 文件路径

    Returns:
        字典，key 为一级标题（不含 #），value 为讲稿内容
    """
    if not md_path.exists():
        print(f"错误: {md_path} 文件不存在")
        return {}

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"错误: 无法读取文件 {md_path}: {e}")
        return {}

    svg_stems = svg_stems or []
    exact, norm_map, num_map = build_match_maps(svg_stems)

    # 按标题解析（支持 # / ## / ###）
    notes: Dict[str, str] = {}
    current_key: Optional[str] = None
    current_lines: List[str] = []
    unmatched_headings: List[str] = []

    lines = content.splitlines()
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            raw_title = m.group(2).strip()
            matched = match_title(raw_title, exact, norm_map, num_map, svg_stems)
            if matched:
                if current_key is not None:
                    text = '\n'.join(current_lines).strip()
                    if current_key in notes and text:
                        notes[current_key] = (notes[current_key].rstrip() + "\n\n" + text).strip()
                    elif current_key not in notes:
                        notes[current_key] = text
                current_key = matched
                current_lines = []
                continue
            unmatched_headings.append(raw_title)

        if HR_RE.match(line):
            continue
        if current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        text = '\n'.join(current_lines).strip()
        if current_key in notes and text:
            notes[current_key] = (notes[current_key].rstrip() + "\n\n" + text).strip()
        elif current_key not in notes:
            notes[current_key] = text

    if verbose and unmatched_headings:
        print("\n[提示] 发现未匹配的标题（已忽略）：")
        for t in unmatched_headings[:10]:
            print(f"  - {t}")
        if len(unmatched_headings) > 10:
            print(f"  ... 以及另外 {len(unmatched_headings) - 10} 个")

    return notes


def check_svg_note_mapping(svg_files: List[Path], notes: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    检查 SVG 文件与讲稿的映射关系

    Args:
        svg_files: SVG 文件列表
        notes: 讲稿字典（key 为标题）

    Returns:
        (是否全部匹配, 缺失的讲稿标题列表)
    """
    missing_notes = []

    for svg_path in svg_files:
        # 提取 SVG 文件名（不含扩展名）
        svg_stem = svg_path.stem

        # 检查是否在讲稿中存在对应的标题
        if svg_stem not in notes:
            missing_notes.append(svg_stem)

    return len(missing_notes) == 0, missing_notes


def split_notes(notes: Dict[str, str], output_dir: Path, verbose: bool = True) -> bool:
    """
    根据讲稿字典拆分并保存为多个文件

    Args:
        notes: 讲稿字典（key 为标题，value 为内容）
        output_dir: 输出目录
        verbose: 是否输出详细信息

    Returns:
        是否成功
    """
    if not notes:
        print("错误: 没有找到讲稿内容")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for title, content in notes.items():
        # 生成输出文件名（与 SVG 文件同名，后缀改为 .md）
        output_path = output_dir / f"{title}.md"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            if verbose:
                print(f"  已生成: {output_path.name}")

            success_count += 1

        except Exception as e:
            if verbose:
                print(f"  错误: 无法写入文件 {output_path}: {e}")

    if verbose:
        print(f"\n[完成] 成功生成 {success_count}/{len(notes)} 个文件")

    return success_count == len(notes)


def main():
    parser = argparse.ArgumentParser(
        description='PPT Master - 讲稿拆分工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    %(prog)s projects/<svg 标题>_ppt169_YYYYMMDD
    %(prog)s projects/<svg 标题>_ppt169_YYYYMMDD -o notes
    %(prog)s projects/<svg 标题>_ppt169_YYYYMMDD -q

功能:
    - 读取 total.md 讲稿文件
    - 检查 SVG 文件与讲稿的对应关系
    - 拆分讲稿为多个独立文件
    - 输出文件命名与 SVG 文件同名
'''
    )

    parser.add_argument('project_path', type=str, help='项目目录路径')
    parser.add_argument('-o', '--output', type=str, default=None, help='输出目录路径（默认：项目下的 notes 目录）')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式')

    args = parser.parse_args()

    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"错误: 路径不存在: {project_path}")
        sys.exit(1)

    # 确定输出目录
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = project_path / 'notes'

    verbose = not args.quiet

    if verbose:
        print("PPT Master - 讲稿拆分工具")
        print("=" * 50)
        print(f"  项目路径: {project_path}")
        print(f"  输出目录: {output_dir}")
        print()

    # 查找 SVG 文件
    svg_files = find_svg_files(project_path)

    if not svg_files:
        print("错误: 未找到 SVG 文件")
        sys.exit(1)

    if verbose:
        print(f"  找到 {len(svg_files)} 个 SVG 文件")

    # 解析 total.md
    total_md_path = project_path / 'notes' / 'total.md'
    svg_stems = [p.stem for p in svg_files]
    notes = parse_total_md(total_md_path, svg_stems, verbose)

    if not notes:
        print("错误: 未找到讲稿内容")
        sys.exit(1)

    if verbose:
        print(f"  找到 {len(notes)} 个讲稿章节")
        print()

    # 检查映射关系
    all_match, missing_notes = check_svg_note_mapping(svg_files, notes)

    if not all_match:
        print("错误: SVG 文件与讲稿不匹配")
        print(f"  缺失的讲稿: {', '.join(missing_notes)}")
        print("\n请重新生成讲稿文件，确保每个 SVG 都有对应的讲稿。")
        sys.exit(1)

    if verbose:
        print("[OK] SVG 文件与讲稿一一对应")
        print()

    # 拆分讲稿
    success = split_notes(notes, output_dir, verbose)

    if success:
        if verbose:
            print(f"\n[完成] 讲稿拆分完成")
        sys.exit(0)
    else:
        print(f"\n[失败] 讲稿拆分失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
