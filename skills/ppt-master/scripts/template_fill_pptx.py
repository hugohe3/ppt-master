#!/usr/bin/env python3
"""PPT Master - PPTX Template Fill (thin wrapper).

Delegates to the template_fill_pptx package. Kept as the CLI entry point so the
documented command paths keep working:

    uvx ppt-master template-fill-pptx analyze <deck.pptx> -o slide_library.json
    uvx ppt-master template-fill-pptx scaffold slide_library.json -o fill_plan.json
    uvx ppt-master template-fill-pptx check-plan slide_library.json fill_plan.json
    uvx ppt-master template-fill-pptx apply <deck.pptx> fill_plan.json -o output.pptx

Implementation lives in the template_fill_pptx/ package (ooxml, analyzer,
scaffolder, checker, text_fill, table_fill, chart_fill, transitions, notes,
package, applier, validator, cli).
"""

import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so the package can be found.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from attribution_guard import require_skill_integrity
from console_encoding import configure_utf8_stdio
from template_fill_pptx import main

configure_utf8_stdio()

if __name__ == "__main__":
    require_skill_integrity()
    raise SystemExit(main())
