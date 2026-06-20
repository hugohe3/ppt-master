#!/usr/bin/env python3
"""PPT Master - PPTX Template Fill (thin wrapper).

Delegates to the template_fill_pptx package. Kept as the CLI entry point so the
documented command paths keep working:

    python3 scripts/template_fill_pptx.py analyze <deck.pptx> -o <stem>.slide_library.json
    python3 scripts/template_fill_pptx.py scaffold <stem>.slide_library.json -o fill_plan.json
    python3 scripts/template_fill_pptx.py check-plan <stem>.slide_library.json fill_plan.json
    python3 scripts/template_fill_pptx.py apply <deck.pptx> fill_plan.json -o output.pptx

Implementation lives in the template_fill_pptx/ package (ooxml, analyzer,
scaffolder, checker, text_fill, table_fill, chart_fill, transitions, notes,
package, applier, cli).
"""

import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so the package can be found.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from template_fill_pptx import main

if __name__ == "__main__":
    raise SystemExit(main())
