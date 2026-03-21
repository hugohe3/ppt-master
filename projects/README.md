# User Project Workspace

This directory is used for storing in-progress projects.

## Create a New Project

```bash
python3 skills/ppt-master/scripts/project_manager.py init my_project --format ppt169
```

## Directory Structure

A typical project usually contains the following:

```
project_name_format_YYYYMMDD/
├── README.md
├── design_spec.md
├── sources/
│   ├── Raw files / URL archives / Converted Markdown
│   └── *_files/                  # Markdown companion resource directory (e.g., images)
├── images/                       # Image assets used by the project
├── notes/
│   ├── 01_xxx.md
│   ├── 02_xxx.md
│   └── total.md
├── svg_output/
│   ├── 01_xxx.svg
│   └── ...
├── svg_final/
│   ├── 01_xxx.svg
│   └── ...
├── templates/                    # Project-level templates (if any)
├── *.pptx
└── image_analysis.csv            # Optional, image scan analysis results
```

Projects can remain at different stages and do not necessarily have all artifacts at once. For example:

- Only `sources/` archiving and the Design Specification & Content Outline (design_spec) are complete
- `svg_output/` has been generated, but post-processing has not yet been executed
- `svg_final/`, `notes/`, and `*.pptx` are all complete

## Notes

- Contents under this directory are excluded by `.gitignore`
- Completed projects can be moved to the `examples/` directory for sharing
- Files outside the workspace are copied by default; files within the workspace are moved directly to the project's `sources/`
