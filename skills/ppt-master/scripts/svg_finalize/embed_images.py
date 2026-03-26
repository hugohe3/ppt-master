#!/usr/bin/env python3
"""
SVG Image Embedding Tool
Converts externally referenced images in SVG files to Base64 inline format.

Usage:
    python3 scripts/svg_finalize/embed_images.py <svg_file> [svg_file2] ...
    python3 scripts/svg_finalize/embed_images.py *.svg

Examples:
    python3 scripts/svg_finalize/embed_images.py examples/ppt169_demo/svg_output/01_cover.svg
    python3 scripts/svg_finalize/embed_images.py examples/ppt169_demo/svg_output/*.svg
"""

import os
import base64
import re
import sys
import argparse


def get_mime_type(filename, file_bytes=None):
    """Return the MIME type based on file bytes first, then extension as fallback."""
    if file_bytes:
        if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return 'image/png'
        if file_bytes.startswith(b"\xff\xd8\xff"):
            return 'image/jpeg'
        if file_bytes.startswith((b"GIF87a", b"GIF89a")):
            return 'image/gif'
        if file_bytes.startswith(b"RIFF") and file_bytes[8:12] == b"WEBP":
            return 'image/webp'
        if file_bytes.lstrip().startswith(b"<svg"):
            return 'image/svg+xml'

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
    """Convert byte count to a human-readable file size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def embed_images_in_svg(svg_path, dry_run=False):
    """
    Convert externally referenced images in an SVG file to Base64 inline format.

    Args:
        svg_path: SVG file path
        dry_run: If True, only show which images would be processed without modifying the file

    Returns:
        tuple: (number of images processed, file size after embedding)
    """
    svg_dir = os.path.dirname(os.path.abspath(svg_path))
    
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content.encode('utf-8'))
    
    # Match href="xxx.png" or href="xxx.jpg" etc. (exclude those already using data:)
    pattern = r'href="(?!data:)([^"]+\.(png|jpg|jpeg|gif|webp))"'
    
    images_found = []
    images_embedded = 0
    
    def replace_with_base64(match):
        nonlocal images_embedded
        img_path = match.group(1)
        
        # Decode XML/HTML entities (e.g., &amp; -> &)
        import html
        img_path_decoded = html.unescape(img_path)
        
        # Handle relative paths
        if not os.path.isabs(img_path_decoded):
            full_path = os.path.join(svg_dir, img_path_decoded)
        else:
            full_path = img_path_decoded
        
        if not os.path.exists(full_path):
            print(f"  [WARN] Image not found: {img_path}")
            images_found.append((img_path, "NOT FOUND", 0))
            return match.group(0)
        
        img_size = os.path.getsize(full_path)
        
        if dry_run:
            images_found.append((img_path, "WILL EMBED", img_size))
            return match.group(0)
        
        with open(full_path, 'rb') as img_file:
            img_bytes = img_file.read()
            b64_data = base64.b64encode(img_bytes).decode('utf-8')

        mime_type = get_mime_type(img_path, img_bytes)
        images_embedded += 1
        images_found.append((img_path, "EMBEDDED", img_size))
        
        return f'href="data:{mime_type};base64,{b64_data}"'
    
    new_content = re.sub(pattern, replace_with_base64, content)
    
    new_size = len(new_content.encode('utf-8'))
    
    # Print processed images
    if images_found:
        print(f"\n[FILE] {os.path.basename(svg_path)}")
        for img_path, status, size in images_found:
            size_str = get_file_size_str(size) if size > 0 else ""
            if status == "EMBEDDED":
                print(f"   [OK] {img_path} ({size_str})")
            elif status == "WILL EMBED":
                print(f"   [PREVIEW] {img_path} ({size_str}) [dry-run]")
            else:
                print(f"   [FAIL] {img_path} ({status})")
        
        print(f"   [SIZE] {get_file_size_str(original_size)} -> {get_file_size_str(new_size)}")
    
    if not dry_run and images_embedded > 0:
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    return (images_embedded, new_size)

def main():
    parser = argparse.ArgumentParser(
        description='Convert externally referenced images in SVG files to Base64 inline format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s 01_cover.svg                # Process a single file
  %(prog)s *.svg                       # Process all SVGs in current directory
  %(prog)s --dry-run *.svg             # Preview files to be processed
        '''
    )
    parser.add_argument('files', nargs='+', help='SVG files to process')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Only show which images would be processed, without modifying files')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("[INFO] Dry-run mode: only preview, no modification\n")
    
    total_images = 0
    total_files = 0
    
    for svg_file in args.files:
        if not os.path.exists(svg_file):
            print(f"[ERROR] File not found: {svg_file}")
            continue
        
        if not svg_file.endswith('.svg'):
            print(f"[SKIP] Skipping non-SVG file: {svg_file}")
            continue
        
        images, _ = embed_images_in_svg(svg_file, dry_run=args.dry_run)
        if images > 0:
            total_images += images
            total_files += 1
    
    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f"[PREVIEW] Will process {total_images} images in {total_files} files")
    else:
        print(f"[DONE] Embedded {total_images} images in {total_files} files")

if __name__ == '__main__':
    main()
