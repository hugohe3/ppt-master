#!/usr/bin/env python3
"""PPT Master - SVG to PPTX Tool (thin wrapper).

Delegates to the svg_to_pptx package. ``-s final`` remains a native-export
diagnostic override; the standard pipeline reads ``svg_output/``:
    python3 scripts/svg_to_pptx.py <project_path> -s final

An imported flat authoring bundle rehydrates unchanged source objects before
the source-preserving export:
    python3 scripts/svg_to_pptx.py <project_path> --roundtrip

An explicit compatibility export may normalize the default ``svg_output/`` or
another project-relative source selected with ``-s`` before strict flat
conversion. It does not provide source-object restoration.
"""

import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so the package can be found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from attribution_guard import require_skill_integrity
from console_encoding import configure_utf8_stdio
from svg_to_pptx import main

configure_utf8_stdio()

if __name__ == '__main__':
    require_skill_integrity()
    raise SystemExit(main())
