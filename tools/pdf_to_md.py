#!/usr/bin/env python3
"""
PDF 转 Markdown 工具
使用 PyMuPDF 提取 PDF 文本内容并转换为 Markdown 格式
支持标题层级、粗体、斜体、列表识别
"""

import fitz  # PyMuPDF
import argparse
import os
import re
from pathlib import Path
from collections import Counter


def analyze_font_sizes(doc) -> dict:
    """分析文档中的字体大小分布，用于推断标题层级"""
    size_counter = Counter()
    
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        size = round(span["size"], 1)
                        text = span["text"].strip()
                        if text:
                            size_counter[size] += len(text)
    
    if not size_counter:
        return {"body": 12, "h1": 24, "h2": 18, "h3": 14}
    
    sorted_sizes = sorted(size_counter.items(), key=lambda x: x[1], reverse=True)
    body_size = sorted_sizes[0][0]
    
    all_sizes = sorted(size_counter.keys(), reverse=True)
    larger_sizes = [s for s in all_sizes if s > body_size + 1]
    
    size_map = {"body": body_size}
    if len(larger_sizes) >= 1:
        size_map["h1"] = larger_sizes[0]
    if len(larger_sizes) >= 2:
        size_map["h2"] = larger_sizes[1]
    if len(larger_sizes) >= 3:
        size_map["h3"] = larger_sizes[2]
    
    return size_map


def get_heading_level(size: float, size_map: dict) -> int:
    """根据字体大小返回标题级别，0 表示正文"""
    if "h1" in size_map and size >= size_map["h1"] - 0.5:
        return 1
    if "h2" in size_map and size >= size_map["h2"] - 0.5:
        return 2
    if "h3" in size_map and size >= size_map["h3"] - 0.5:
        return 3
    return 0


def format_span_text(text: str, flags: int) -> str:
    """根据字体标志格式化文本（粗体、斜体）"""
    text = text.strip()
    if not text:
        return ""
    
    is_bold = flags & 16
    is_italic = flags & 2
    
    if is_bold and is_italic:
        return f"***{text}***"
    elif is_bold:
        return f"**{text}**"
    elif is_italic:
        return f"*{text}*"
    return text


def detect_list_item(text: str) -> tuple:
    """检测是否为列表项，返回 (是否列表, 列表类型, 内容)"""
    text = text.strip()
    
    ul_patterns = [
        (r'^[•●○◦▪▸►]\s*', '-'),
        (r'^[-–—]\s+', '-'),
        (r'^\*\s+', '-'),
    ]
    for pattern, marker in ul_patterns:
        match = re.match(pattern, text)
        if match:
            return (True, 'ul', marker + ' ' + text[match.end():])
    
    ol_pattern = r'^(\d+)[.、)]\s*'
    match = re.match(ol_pattern, text)
    if match:
        num = match.group(1)
        return (True, 'ol', f"{num}. " + text[match.end():])
    
    return (False, None, text)


def clean_text(text: str) -> str:
    """清理提取的文本"""
    lines = text.split('\n')
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        line = line.rstrip()
        is_empty = len(line.strip()) == 0
        
        if is_empty:
            if not prev_empty:
                cleaned_lines.append('')
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
    
    return '\n'.join(cleaned_lines)


def merge_adjacent_formatting(text: str) -> str:
    """合并相邻的格式标记，如 **text1****text2** → **text1 text2**"""
    text = re.sub(r'\*\*\s*\*\*', ' ', text)
    text = re.sub(r'\*\s*\*', ' ', text)
    text = re.sub(r'\*\*\*\s*\*\*\*', ' ', text)
    return text


def is_sentence_end(text: str) -> bool:
    """判断文本是否以句末标点结尾"""
    text = text.rstrip()
    if not text:
        return True
    end_puncts = '.。!！?？:：;；'
    return text[-1] in end_puncts


def should_merge_lines(current: dict, next_line: dict) -> bool:
    """判断两行是否应该合并为同一段落"""
    if current.get("is_heading") or next_line.get("is_heading"):
        return False
    if current.get("is_list") or next_line.get("is_list"):
        return False
    if is_sentence_end(current.get("content", "")):
        return False
    return True


def extract_pdf_to_markdown(pdf_path: str, output_path: str = None) -> str:
    """
    从 PDF 提取文本、图片和表格并转换为 Markdown
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"❌ 无法打开 PDF 文件: {e}")
        return ""
    
    filename = Path(pdf_path).stem
    title = re.sub(r'^\d+-', '', filename).strip()
    
    print(f"📄 分析文档结构...")
    size_map = analyze_font_sizes(doc)
    print(f"   字体大小映射: 正文={size_map.get('body', 'N/A')}, " +
          f"H1={size_map.get('h1', 'N/A')}, H2={size_map.get('h2', 'N/A')}, H3={size_map.get('h3', 'N/A')}")
    
    markdown_content = f"# {title}\n\n"
    
    img_dir = None
    rel_img_dir = "images"
    if output_path:
        output_path = Path(output_path)
        img_dir = output_path.parent / rel_img_dir
        if not img_dir.exists():
            img_dir.mkdir(parents=True, exist_ok=True)
            
    img_count = 0
    
    for page_num, page in enumerate(doc, 1):
        try:
            tabs = page.find_tables()
        except Exception:
            tabs = []
            
        tab_rects = [fitz.Rect(t.bbox) for t in tabs]
        
        page_elements = []
        
        for tab in tabs:
            page_elements.append({
                "y0": tab.bbox[1],
                "type": 2,
                "content": tab.to_markdown()
            })
            print(f"  ✓ 发现表格: P{page_num}")

        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])
            
            is_in_table = False
            for tab_rect in tab_rects:
                intersect = block_rect & tab_rect
                if intersect.get_area() > 0.6 * block_rect.get_area():
                    is_in_table = True
                    break
            
            if is_in_table:
                continue
                
            if block["type"] == 0:
                for line in block["lines"]:
                    line_text = ""
                    line_size = 0
                    line_flags = 0
                    span_count = 0
                    
                    formatted_spans = []
                    for span in line["spans"]:
                        span_text = span["text"]
                        if not span_text.strip():
                            if span_text:
                                formatted_spans.append(span_text)
                            continue
                        
                        span_size = span["size"]
                        span_flags = span["flags"]
                        
                        line_size = max(line_size, span_size)
                        line_flags |= span_flags
                        span_count += 1
                        
                        heading_level = get_heading_level(span_size, size_map)
                        if heading_level > 0:
                            formatted_spans.append(span_text.strip())
                        else:
                            formatted_spans.append(format_span_text(span_text, span_flags))
                    
                    line_text = ''.join(formatted_spans).strip()
                    if not line_text:
                        continue
                    
                    line_text = merge_adjacent_formatting(line_text)
                    
                    heading_level = get_heading_level(line_size, size_map)
                    
                    is_list, list_type, list_content = detect_list_item(line_text)
                    
                    if heading_level > 0:
                        prefix = '#' * heading_level + ' '
                        clean_line = re.sub(r'\*+([^*]+)\*+', r'\1', line_text)
                        final_text = prefix + clean_line
                    elif is_list:
                        final_text = list_content
                    else:
                        final_text = line_text
                    
                    page_elements.append({
                        "y0": line["bbox"][1],
                        "type": 0,
                        "content": final_text,
                        "is_heading": heading_level > 0,
                        "is_list": is_list
                    })
                    
            elif block["type"] == 1:
                page_elements.append({
                    "y0": block["bbox"][1],
                    "type": 1,
                    "content": block
                })
        
        page_elements.sort(key=lambda x: x["y0"])
        
        merged_elements = []
        i = 0
        while i < len(page_elements):
            el = page_elements[i]
            if el["type"] == 0 and not el.get("is_heading") and not el.get("is_list"):
                merged_content = el["content"]
                j = i + 1
                while j < len(page_elements):
                    next_el = page_elements[j]
                    if next_el["type"] != 0:
                        break
                    if not should_merge_lines({"content": merged_content, "is_heading": False, "is_list": False}, next_el):
                        break
                    merged_content += " " + next_el["content"]
                    j += 1
                merged_elements.append({
                    "type": 0,
                    "content": merged_content,
                    "is_heading": False,
                    "is_list": False
                })
                i = j
            else:
                merged_elements.append(el)
                i += 1
        
        prev_was_list = False
        for el in merged_elements:
            if el["type"] == 0:
                is_list = el.get("is_list", False)
                is_heading = el.get("is_heading", False)
                
                if is_heading:
                    if prev_was_list:
                        markdown_content += "\n"
                    markdown_content += el["content"] + "\n\n"
                    prev_was_list = False
                elif is_list:
                    markdown_content += el["content"] + "\n"
                    prev_was_list = True
                else:
                    if prev_was_list:
                        markdown_content += "\n"
                    markdown_content += el["content"] + "\n\n"
                    prev_was_list = False
                    
            elif el["type"] == 2:
                if prev_was_list:
                    markdown_content += "\n"
                markdown_content += el["content"] + "\n\n"
                prev_was_list = False
                
            elif el["type"] == 1:
                if img_dir:
                    block = el["content"]
                    ext = block["ext"]
                    image_data = block["image"]
                    safe_filename = filename.replace(" ", "_")
                    image_name = f"{safe_filename}_p{page_num}_{img_count}.{ext}"
                    image_path = img_dir / image_name
                    
                    try:
                        with open(image_path, "wb") as f:
                            f.write(image_data)
                        
                        if prev_was_list:
                            markdown_content += "\n"
                        markdown_content += f"![{image_name}]({rel_img_dir}/{image_name})\n\n"
                        img_count += 1
                        prev_was_list = False
                        print(f"  ✓ 提取图片: {image_name}")
                    except Exception as e:
                        print(f"  ⚠️ 图片保存失败: {e}")
    
    doc.close()
    
    markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
    markdown_content = markdown_content.strip() + "\n"
    
    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✓ 保存 Markdown 到: {output_path}")
    
    return markdown_content


def process_directory(input_dir: str, output_dir: str = None):
    """处理目录下的所有 PDF 文件"""
    input_path = Path(input_dir)
    
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = input_path
    
    pdf_files = sorted(input_path.glob('*.pdf'))
    
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    
    for pdf_file in pdf_files:
        output_file = output_path / (pdf_file.stem + '.md')
        print(f"处理: {pdf_file.name}")
        extract_pdf_to_markdown(str(pdf_file), str(output_file))


def main():
    parser = argparse.ArgumentParser(
        description='PDF 转 Markdown 工具（支持结构识别）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python pdf_to_md.py book.pdf                    # 转换单个文件
  python pdf_to_md.py book.pdf -o output.md      # 指定输出文件
  python pdf_to_md.py ./pdfs                      # 转换目录下所有 PDF
  python pdf_to_md.py ./pdfs -o ./markdown       # 指定输出目录

结构识别功能:
  - 自动识别标题层级（基于字体大小）
  - 识别粗体和斜体文本
  - 识别有序和无序列表
  - 提取表格并转为 Markdown 格式
'''
    )
    
    parser.add_argument('input', help='PDF 文件或包含 PDF 的目录')
    parser.add_argument('-o', '--output', help='输出文件或目录')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        output = args.output or str(input_path.with_suffix('.md'))
        extract_pdf_to_markdown(str(input_path), output)
    elif input_path.is_dir():
        process_directory(str(input_path), args.output)
    else:
        print(f"错误: 找不到文件或目录: {args.input}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
