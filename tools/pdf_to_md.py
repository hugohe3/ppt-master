#!/usr/bin/env python3
"""
PDF 转 Markdown 工具
使用 PyMuPDF 提取 PDF 文本内容并转换为 Markdown 格式
"""

import fitz  # PyMuPDF
import argparse
import os
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """清理提取的文本"""
    # 移除多余的空白行
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
    
    markdown_content = f"# {title}\n\n"
    
    # 准备图片保存目录
    img_dir = None
    rel_img_dir = "images"
    if output_path:
        output_path = Path(output_path)
        img_dir = output_path.parent / rel_img_dir
        if not img_dir.exists():
            img_dir.mkdir(parents=True, exist_ok=True)
            
    img_count = 0
    
    for page_num, page in enumerate(doc, 1):
        # 1. 查找表格
        try:
            tabs = page.find_tables()
        except Exception:
            tabs = []
            
        tab_rects = [fitz.Rect(t.bbox) for t in tabs]
        
        # 收集页面素有元素: (y0, type, content)
        # type: 0=text, 1=image, 2=table
        page_elements = []
        
        # 添加表格到列表
        for tab in tabs:
            page_elements.append({
                "y0": tab.bbox[1],
                "type": 2,
                "content": tab.to_markdown()
            })
            print(f"  ✓ 发现表格: P{page_num}")

        # 获取所有文本和图片块
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])
            
            # 检查块是否在某个表格区域内
            is_in_table = False
            for tab_rect in tab_rects:
                # 如果重叠面积超过 60%，认为该块属于表格，跳过（避免内容重复）
                # 使用 intersect 计算交集
                intersect = block_rect & tab_rect
                if intersect.get_area() > 0.6 * block_rect.get_area():
                    is_in_table = True
                    break
            
            if is_in_table:
                continue
                
            if block["type"] == 0:  # 文本块
                text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        text += span["text"]
                    text += "\n"
                
                cleaned = clean_text(text)
                if cleaned:
                    page_elements.append({
                        "y0": block["bbox"][1],
                        "type": 0,
                        "content": cleaned
                    })
                    
            elif block["type"] == 1:  # 图片块
                page_elements.append({
                    "y0": block["bbox"][1],
                    "type": 1,
                    "content": block  # 暂存 block 数据后续处理
                })
        
        # 按垂直位置(y0)排序，还原页面阅读顺序
        page_elements.sort(key=lambda x: x["y0"])
        
        # 生成 Markdown 内容
        for el in page_elements:
            if el["type"] == 0: # Text
                markdown_content += el["content"] + "\n\n"
                
            elif el["type"] == 2: # Table
                markdown_content += el["content"] + "\n\n"
                
            elif el["type"] == 1: # Image
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
                        
                        markdown_content += f"![{image_name}]({rel_img_dir}/{image_name})\n\n"
                        img_count += 1
                        print(f"  ✓ 提取图片: {image_name}")
                    except Exception as e:
                        print(f"  ⚠️ 图片保存失败: {e}")
    
    doc.close()
    
    # 移除末尾多余的换行
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
        description='PDF 转 Markdown 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python pdf_to_md.py book.pdf                    # 转换单个文件
  python pdf_to_md.py book.pdf -o output.md      # 指定输出文件
  python pdf_to_md.py ./pdfs                      # 转换目录下所有 PDF
  python pdf_to_md.py ./pdfs -o ./markdown       # 指定输出目录
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
