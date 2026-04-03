# Project Tools

Project tools create, validate, and inspect the standard PPT Master workspace.

## `project_manager.py`

Main entry point for project setup and validation.

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source1> [<source2> ...]
python3 scripts/project_manager.py validate <project_path>
python3 scripts/project_manager.py info <project_path>
```

Notes:
- Files outside the workspace are copied into `sources/` by default
- With `--move`, files outside the workspace are moved into `sources/`
- Files already inside the workspace are moved directly

Common formats:
- `ppt169`
- `ppt43`
- `xiaohongshu`
- `moments`
- `story`
- `banner`
- `a4`

Examples:

```bash
python3 scripts/project_manager.py init my_presentation --format ppt169
python3 scripts/project_manager.py validate projects/my_presentation_ppt169_20251116
python3 scripts/project_manager.py info projects/my_presentation_ppt169_20251116
```

## `project_utils.py`

Shared helper module used by other scripts.

Typical use:

```python
from project_utils import get_project_info, validate_project_structure
```

You can also run it directly for quick checks:

```bash
python3 scripts/project_utils.py <project_path>
```

## `batch_validate.py`

Batch-check project structure and compliance.

```bash
python3 scripts/batch_validate.py examples
python3 scripts/batch_validate.py examples projects
python3 scripts/batch_validate.py --all
python3 scripts/batch_validate.py examples --export
```

Use this for repository-wide health checks before release or cleanup.

## `generate_examples_index.py`

Rebuild `examples/README.md` automatically.

```bash
python3 scripts/generate_examples_index.py
python3 scripts/generate_examples_index.py examples
```

## `pptx_template_import.py`

Lightweight importer for `.pptx` template sources.

```bash
python3 scripts/pptx_template_import.py <template.pptx>
python3 scripts/pptx_template_import.py <template.pptx> -o <output_dir>
```

Notes:
- Extracts reusable media assets from `ppt/media/`
- Summarizes slide size, theme colors, and font metadata
- Infers background image inheritance across slide, layout, and master
- Produces `manifest.json`, `analysis.md`, and `assets/`
- Intended as an internal helper for template reconstruction, not a direct PPTX-to-SVG converter

## `error_helper.py`

Show standardized fixes for common project errors.

```bash
python3 scripts/error_helper.py
python3 scripts/error_helper.py missing_readme
python3 scripts/error_helper.py missing_readme project_path=my_project
```
