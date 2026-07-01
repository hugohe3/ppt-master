#!/usr/bin/env python3
"""
PPT Master - Source to Markdown Dispatcher

Shared routing and backend command construction for source-to-Markdown tools.

Usage:
    Imported by scripts/source_to_md.py and scripts/project_manager.py

Examples:
    build_conversion_command("report.pdf", "report.md")

Dependencies:
    None
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


SOURCE_TO_MD_DIR = Path(__file__).resolve().parent
WECHAT_HOST_KEYWORDS = ("mp.weixin.qq.com", "weixin.qq.com")

DOC_SUFFIXES = {
    ".docx", ".doc", ".odt", ".rtf",          # Office documents
    ".epub",                                    # eBooks
    ".html", ".htm",                            # Web pages
    ".tex", ".latex", ".rst", ".org",           # Academic / technical
    ".ipynb", ".typ",                           # Notebooks / Typst
}
EXCEL_SUFFIXES = {".xlsx", ".xlsm"}
LEGACY_EXCEL_SUFFIXES = {".xls"}
MARKDOWN_SUFFIXES = {".md", ".markdown"}
PDF_SUFFIXES = {".pdf"}
PRESENTATION_SUFFIXES = {".pptx", ".pptm", ".ppsx", ".ppsm", ".potx", ".potm"}
TEXT_SUFFIXES = {".txt", ".text"}


@dataclass
class ConversionCommand:
    """Backend command plus metadata for one conversion route."""

    command: list[str]
    script_name: str
    conversion_type: str
    output_path: Path | None


def is_url(value: str) -> bool:
    """Return whether a string looks like an HTTP(S) URL."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def detect_source_type(input_arg: str) -> str:
    """Detect a conversion type from a URL, file, or directory."""
    if is_url(input_arg):
        return "web"

    path = Path(input_arg)
    if not path.exists():
        return "unknown"
    if path.is_dir():
        return "directory"

    suffix = path.suffix.lower()
    if suffix in PDF_SUFFIXES:
        return "pdf"
    if suffix in DOC_SUFFIXES:
        return "doc"
    if suffix in EXCEL_SUFFIXES or suffix in LEGACY_EXCEL_SUFFIXES:
        return "excel"
    if suffix in PRESENTATION_SUFFIXES:
        return "pptx"
    if suffix in MARKDOWN_SUFFIXES:
        return "markdown"
    if suffix in TEXT_SUFFIXES:
        return "text"
    return "unknown"


def default_markdown_path(input_arg: str) -> Path:
    """Return the conventional Markdown output path for a local input."""
    path = Path(input_arg)
    return path.parent / f"{path.stem}.md"


def _curl_cffi_available() -> bool:
    """Return whether curl_cffi is importable."""
    try:
        import curl_cffi  # noqa: F401
        return True
    except ImportError:
        return False


def _web_script_command(
    url: str,
    output_path: Path | None,
    python_executable: str,
    allow_node_fallback: bool,
) -> tuple[str, list[str]]:
    """Return the web backend script name and base command."""
    host = urlparse(url).netloc.lower()
    is_tls_sensitive = any(keyword in host for keyword in WECHAT_HOST_KEYWORDS)
    node_backend = SOURCE_TO_MD_DIR / "web_to_md.cjs"

    if (
        allow_node_fallback
        and is_tls_sensitive
        and not _curl_cffi_available()
        and node_backend.is_file()
        and shutil.which("node")
    ):
        command = ["node", str(node_backend), url]
        script_name = "web_to_md.cjs"
    else:
        command = [python_executable, str(SOURCE_TO_MD_DIR / "web_to_md.py"), url]
        script_name = "web_to_md.py"

    if output_path is not None:
        command.extend(["-o", str(output_path)])
    return script_name, command


def build_conversion_command(
    input_arg: str,
    output_path: str | Path | None,
    *,
    forced_type: str | None = None,
    extra_args: list[str] | None = None,
    pdf_image_mode: str | None = None,
    render_vector_figures: bool = False,
    python_executable: str | None = None,
    allow_node_web_fallback: bool = True,
) -> ConversionCommand:
    """Build the backend CLI command for one source-to-Markdown conversion."""
    conversion_type = forced_type or detect_source_type(input_arg)
    output = Path(output_path) if output_path is not None else None
    extra = extra_args or []
    python = python_executable or sys.executable

    if conversion_type == "web":
        if not is_url(input_arg):
            raise ValueError("web conversion requires an http:// or https:// URL")
        script_name, command = _web_script_command(
            input_arg,
            output,
            python,
            allow_node_web_fallback,
        )
        command.extend(extra)
        return ConversionCommand(command, script_name, conversion_type, output)

    if conversion_type in {"markdown", "text", "directory", "unknown"}:
        raise ValueError(f"conversion type {conversion_type!r} has no backend command")

    script_by_type = {
        "pdf": "pdf_to_md.py",
        "doc": "doc_to_md.py",
        "excel": "excel_to_md.py",
        "pptx": "ppt_to_md.py",
    }
    script_name = script_by_type.get(conversion_type)
    if script_name is None:
        raise ValueError(f"unsupported conversion type: {conversion_type}")
    if output is None:
        output = default_markdown_path(input_arg)

    command = [
        python,
        str(SOURCE_TO_MD_DIR / script_name),
        input_arg,
        "-o",
        str(output),
    ]
    if conversion_type == "pdf" and pdf_image_mode:
        command.extend(["--images", pdf_image_mode])
    if conversion_type == "pdf" and render_vector_figures:
        command.append("--render-vector-figures")
    command.extend(extra)
    return ConversionCommand(command, script_name, conversion_type, output)
