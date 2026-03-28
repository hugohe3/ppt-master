#!/usr/bin/env python3
"""
Document to Markdown Converter (Pandoc-based)

Uses Pandoc to convert various document formats to Markdown.
Primary use case: DOCX lecture notes / manuscripts → Markdown for PPT generation.

Dependency: pandoc must be installed
   macOS:   brew install pandoc
   Ubuntu:  sudo apt install pandoc
   Windows: https://pandoc.org/installing.html
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


# Supported input formats
SUPPORTED_FORMATS = {
    # Office documents
    ".docx": ("docx", "Microsoft Word"),
    ".doc": ("doc", "Microsoft Word 97-2003"),
    ".odt": ("odt", "OpenDocument Text"),
    ".rtf": ("rtf", "Rich Text Format"),
    # eBooks
    ".epub": ("epub", "EPUB"),
    # Web
    ".html": ("html", "HTML"),
    ".htm": ("html", "HTML"),
    # Academic / technical
    ".tex": ("latex", "LaTeX"),
    ".latex": ("latex", "LaTeX"),
    ".rst": ("rst", "reStructuredText"),
    ".org": ("org", "Emacs Org-mode"),
    ".ipynb": ("ipynb", "Jupyter Notebook"),
    ".typ": ("typst", "Typst"),
}

# Formats that may contain embedded media
MEDIA_FORMATS = {".docx", ".odt", ".epub", ".html", ".htm"}


def check_pandoc() -> bool:
    """Check if pandoc is installed."""
    return shutil.which("pandoc") is not None


def convert_to_markdown(input_path: str, output_path: str | None = None) -> str:
    """
    Convert a document to Markdown using Pandoc.

    Args:
        input_path: Path to the input document.
        output_path: Path to write the output Markdown (default: same dir, .md extension).

    Returns:
        The generated Markdown content.
    """
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"[ERROR] File not found: {input_path}")
        return ""

    suffix = input_file.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS.keys()))
        print(f"[ERROR] Unsupported format: {suffix}")
        print(f"   Supported: {supported}")
        return ""

    input_format, format_desc = SUPPORTED_FORMATS[suffix]
    print(f"[INFO] Converting {format_desc} file: {input_file.name}")

    # Determine output path
    if output_path:
        out_file = Path(output_path)
    else:
        out_file = input_file.with_suffix(".md")

    # Media extraction directory (use name only — pandoc writes relative paths)
    rel_media_dir = f"{out_file.stem}_files"
    media_dir = out_file.parent / rel_media_dir

    # Build pandoc command — use resolved absolute paths for input/output,
    # but a relative directory name for --extract-media so pandoc writes
    # relative image references in the markdown.
    cmd = [
        "pandoc",
        "-f", input_format,
        "-t", "gfm",
        str(input_file.resolve()),
        "-o", str(out_file.resolve()),
        "--wrap", "none",
        "--strip-comments",
    ]

    # Extract embedded media for formats that support it
    if suffix in MEDIA_FORMATS:
        cmd.extend(["--extract-media", rel_media_dir])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=str(out_file.parent))
    except FileNotFoundError:
        print("[ERROR] pandoc not found! Please install it first:")
        print("   macOS:   brew install pandoc")
        print("   Ubuntu:  sudo apt install pandoc")
        print("   Windows: https://pandoc.org/installing.html")
        return ""

    if result.returncode != 0:
        print(f"[ERROR] Pandoc conversion failed:\n{result.stderr}")
        return ""

    # Read generated markdown
    if not out_file.exists():
        print("[ERROR] Conversion completed but no output file was generated")
        return ""

    markdown_content = out_file.read_text(encoding="utf-8")

    # --- Post-processing: fix media paths ---

    # 1. Flatten nested media/ subdirectory that pandoc creates
    nested_media = media_dir / "media"
    if nested_media.exists():
        for f in nested_media.iterdir():
            if f.is_file():
                target = media_dir / f.name
                shutil.move(str(f), str(target))
        try:
            nested_media.rmdir()
        except OSError:
            pass
        # Fix references: {dir}/media/img.png → {dir}/img.png
        markdown_content = markdown_content.replace(
            f"{rel_media_dir}/media/", f"{rel_media_dir}/"
        )

    # 2. Convert any absolute paths to relative (safety net)
    abs_media_str = str(media_dir.resolve()).replace("\\", "/")
    if abs_media_str in markdown_content:
        markdown_content = markdown_content.replace(abs_media_str, rel_media_dir)
    # Also handle backslash variant on Windows
    abs_media_str_bs = str(media_dir.resolve())
    if abs_media_str_bs in markdown_content:
        markdown_content = markdown_content.replace(abs_media_str_bs, rel_media_dir)

    # 3. Convert <img> HTML tags to Markdown ![alt](src) syntax
    #    Pandoc generates <img> when the source has styling (width/height)
    def _img_to_md(match: re.Match[str]) -> str:
        src = match.group("src")
        alt = match.group("alt") or Path(src).stem
        return f"![{alt}]({src})"

    markdown_content = re.sub(
        r'<img\s[^>]*?src="(?P<src>[^"]+)"[^>]*?(?:alt="(?P<alt>[^"]*)")?[^>]*/?\s*>',
        _img_to_md,
        markdown_content,
    )
    # Handle alt before src order as well
    markdown_content = re.sub(
        r'<img\s[^>]*?alt="(?P<alt>[^"]*)"[^>]*?src="(?P<src>[^"]+)"[^>]*/?\s*>',
        _img_to_md,
        markdown_content,
    )

    out_file.write_text(markdown_content, encoding="utf-8")

    # Report results
    size = out_file.stat().st_size
    print(f"[OK] Saved Markdown to: {out_file} ({_format_size(size)})")

    if media_dir.exists():
        media_files = [f for f in media_dir.rglob("*") if f.is_file()]
        if media_files:
            print(f"   Extracted {len(media_files)} media file(s) → {media_dir}")

    return markdown_content


def _format_size(size: int) -> str:
    """Format file size for display."""
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def main() -> None:
    """Run the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert documents to Markdown using Pandoc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python doc_to_md.py lecture.docx                # Convert Word document
  python doc_to_md.py lecture.docx -o output.md   # Specify output path
  python doc_to_md.py notes.odt                   # Convert OpenDocument

Supported formats:
  Office:    .docx  .doc  .odt  .rtf
  eBooks:    .epub
  Web:       .html  .htm
  Academic:  .tex  .rst  .org  .ipynb  .typ
        """,
    )

    parser.add_argument("input", help="Input document file")
    parser.add_argument("-o", "--output", help="Output Markdown file path")

    args = parser.parse_args()

    if not check_pandoc():
        print("[ERROR] pandoc not found! Please install it first:")
        print("   macOS:   brew install pandoc")
        print("   Ubuntu:  sudo apt install pandoc")
        print("   Windows: https://pandoc.org/installing.html")
        sys.exit(1)

    result = convert_to_markdown(args.input, args.output)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
