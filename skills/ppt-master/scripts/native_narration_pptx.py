#!/usr/bin/env python3
"""
PPT Master - Native Narration PPTX Compatibility Entrypoint

Backward-compatible CLI for callers that still use the retired narration
script name. New calls use native_enhance_pptx.py.

Usage:
    python3 scripts/native_narration_pptx.py init <source.pptx> [--name project_name]
    python3 scripts/native_narration_pptx.py plan <project_path>
    python3 scripts/native_narration_pptx.py validate <project_path>
    python3 scripts/native_narration_pptx.py apply <project_path>

Examples:
    python3 scripts/native_narration_pptx.py validate projects/native_enhance_project

Dependencies:
    Same as native_enhance_pptx_core.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from native_enhance_pptx_core import main  # noqa: E402

configure_utf8_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
