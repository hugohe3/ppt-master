#!/usr/bin/env python3
"""
PPT Master - Project Management Tool

Stable CLI entry point for project creation, source import, validation, and
page-context diagnostics. Implementation lives in ``project_management/``.

Usage:
    python3 scripts/project_manager.py init <project_name> [--format ppt169]
    python3 scripts/project_manager.py import-sources <project_path> <sources...>
    python3 scripts/project_manager.py validate <project_path>

Examples:
    python3 scripts/project_manager.py init demo --format ppt169
    python3 scripts/project_manager.py validate projects/demo

Dependencies:
    Same as project_management.cli.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from attribution_guard import require_skill_integrity  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402

configure_utf8_stdio()

from project_management.cli import (  # noqa: E402
    BITMAP_IMAGE_SUFFIXES,
    IMAGE_ASSET_SUFFIXES,
    SOURCE_DIRNAME,
    SOURCE_TO_MD_TOOLS_DIR,
    TABLE_TEXT_SUFFIXES,
    TEXT_SOURCE_SUFFIXES,
    TOOLS_DIR,
    ProjectManager,
    build_parser,
    derive_url_basename,
    is_url,
    is_within_path,
    main,
    sanitize_name,
)
from project_management.paths import (  # noqa: E402
    PROJECTS_ROOT,
    REPO_ROOT,
    SKILL_DIR,
)

__all__ = [
    "BITMAP_IMAGE_SUFFIXES",
    "IMAGE_ASSET_SUFFIXES",
    "PROJECTS_ROOT",
    "REPO_ROOT",
    "SKILL_DIR",
    "SOURCE_DIRNAME",
    "SOURCE_TO_MD_TOOLS_DIR",
    "TABLE_TEXT_SUFFIXES",
    "TEXT_SOURCE_SUFFIXES",
    "TOOLS_DIR",
    "ProjectManager",
    "build_parser",
    "derive_url_basename",
    "is_url",
    "is_within_path",
    "main",
    "sanitize_name",
]


if __name__ == "__main__":
    require_skill_integrity()
    raise SystemExit(main())
