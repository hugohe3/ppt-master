#!/usr/bin/env python3
"""
PPT Master - Native Enhance PPTX Entrypoint

Public CLI wrapper for native enhancement of existing PPTX decks. It delegates
to the shared native core for delivery checks, notes, narration, timings, and
global or per-slide transitions while keeping the stable workflow command.

Usage:
    python3 scripts/native_enhance_pptx.py init <source.pptx> [--name project_name]
    python3 scripts/native_enhance_pptx.py plan <project_path>
    python3 scripts/native_enhance_pptx.py validate <project_path> [--materials {all,notes}]
    python3 scripts/native_enhance_pptx.py apply <project_path>

Examples:
    python3 scripts/native_enhance_pptx.py init projects/source.pptx --name fire_station
    python3 scripts/native_enhance_pptx.py plan projects/fire_station_native_enhance_20260626
    python3 scripts/native_enhance_pptx.py apply projects/fire_station_native_enhance_20260626

Dependencies:
    Same as native_enhance_pptx_core.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from attribution_guard import require_skill_integrity  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402
from native_enhance_pptx_core import main  # noqa: E402

configure_utf8_stdio()


if __name__ == "__main__":
    require_skill_integrity()
    raise SystemExit(main())
