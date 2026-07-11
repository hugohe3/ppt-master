#!/usr/bin/env python3
"""ppt-master CLI — unified entry point for all scripts (skill directory edition)."""

import os
import subprocess
import sys

SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "scripts"
)

COMMANDS = {
    "project":                "project_manager.py",
    "pdf-to-md":              "source_to_md/pdf_to_md.py",
    "doc-to-md":              "source_to_md/doc_to_md.py",
    "excel-to-md":            "source_to_md/excel_to_md.py",
    "ppt-to-md":              "source_to_md/ppt_to_md.py",
    "web-to-md":              "source_to_md/web_to_md.py",
    "analyze-images":         "analyze_images.py",
    "image-gen":              "image_gen.py",
    "image-search":           "image_search.py",
    "latex-render":           "latex_render.py",
    "svg-quality-check":      "svg_quality_checker.py",
    "total-md-split":         "total_md_split.py",
    "finalize-svg":           "finalize_svg.py",
    "svg-to-pptx":            "svg_to_pptx.py",
    "check-annotations":      "check_annotations.py",
    "animation-config":       "animation_config.py",
    "auto-fix-uvx":           "auto_fix_uvx.py",
    "notes-to-audio":         "notes_to_audio.py",
    "pptx-template-import":   "pptx_template_import.py",
    "template-fill-pptx":     "template_fill_pptx.py",
    "svg-editor":             "svg_editor/server.py",
    "update-spec":            "update_spec.py",
    "visual-review":          "visual_review.py",
    "svg-position-calc":      "svg_position_calculator.py",
    "rotate-images":          "rotate_images.py",
    "slice-images":           "slice_images.py",
    "source-to-md":           "source_to_md.py",
    "update-repo":            "update_repo.py",
    "generate-examples-index": "generate_examples_index.py",
    "batch-validate":         "batch_validate.py",
    "gemini-watermark-remove": "gemini_watermark_remover.py",
    "pptx-animations":        "pptx_animations.py",
    "check-deps-sync":        "check_deps_sync.py",
    "check-uvx-migration":    "check_uvx_migration.py",
    "pptx-to-svg":            "pptx_to_svg.py",
    "confirm-ui":             "confirm_ui/server.py",
    "error-helper":           "error_helper.py",
    "project-utils":          "project_utils.py",
    "config":                 "config.py",
    "register-template":      "register_template.py",
    "icon-sync":              "icon_sync.py",
    "extract-svg-assets":     "extract_svg_assets.py",
    "native-enhance-pptx":    "native_enhance_pptx.py",
    "native-narration-pptx":  "native_narration_pptx.py",
    "pptx-intake":            "pptx_intake.py",
    "beautify-identity":      "beautify_identity.py",
    "beautify-inventory":     "beautify_inventory.py",
    "align-embed-images":     "svg_finalize/align_embed_images.py",
}

COMMAND_DESCRIPTIONS = {
    "project":                "Create/validate/manage PPT projects",
    "pdf-to-md":              "Convert PDF to Markdown",
    "doc-to-md":              "Convert DOCX/HTML/EPUB to Markdown",
    "excel-to-md":            "Convert Excel to Markdown",
    "ppt-to-md":              "Convert PPTX to Markdown",
    "web-to-md":              "Convert URL/webpage to Markdown",
    "analyze-images":         "Analyze images and compute layout sizes",
    "image-gen":              "AI image generation (multi-backend)",
    "image-search":           "Search and download web images",
    "latex-render":           "Render LaTeX formulas to PNG",
    "svg-quality-check":      "Validate SVG against PPT constraints",
    "total-md-split":         "Split total.md into per-page files",
    "finalize-svg":           "Post-process SVGs (icons, images, text)",
    "svg-to-pptx":            "Export SVGs to PPTX",
    "check-annotations":      "Scan SVGs for edit annotations",
    "animation-config":       "Create/validate animation configuration",
    "auto-fix-uvx":           "Auto fix uvx command references in .md files",
    "notes-to-audio":         "Generate per-slide narration audio (TTS)",
    "pptx-template-import":   "Extract SVG references from PPTX template",
    "template-fill-pptx":     "Fill content into PPTX template",
    "svg-editor":             "Launch web-based SVG editor (live preview)",
    "update-spec":            "Propagate color/font changes to all SVGs",
    "visual-review":          "Visual review via Playwright (PNG renderer)",
    "svg-position-calc":      "Chart coordinate calculator",
    "rotate-images":          "Rotate images (EXIF + manual)",
    "slice-images":           "Slice AI illustration sheet into individual elements",
    "source-to-md":           "Unified source document to Markdown converter",
    "update-repo":            "Git pull + uv sync repository updater",
    "generate-examples-index": "Generate examples README index",
    "batch-validate":         "Batch project validator",
    "gemini-watermark-remove": "Remove watermarks from Gemini images",
    "pptx-animations":        "Animation demo and list utilities",
    "check-deps-sync":        "Verify dependency manifest sync",
    "check-uvx-migration":    "Check for old-style command patterns",
    "pptx-to-svg":            "Convert PPTX to SVG",
    "confirm-ui":             "Launch Eight Confirmations interactive UI",
    "error-helper":           "Error explanation lookup",
    "project-utils":          "Project utility helpers",
    "config":                 "List canvas formats and color presets",
    "register-template":      "Register layout template",
    "icon-sync":              "Copy library icons into project icons/",
    "extract-svg-assets":     "Extract and deduplicate SVG assets",
    "native-enhance-pptx":    "Native PPTX enhancement (notes/audio/timings/transitions)",
    "native-narration-pptx":  "Native narration PPTX (legacy compat)",
    "pptx-intake":            "Standard PPTX intake enrichment",
    "beautify-identity":      "Extract visual identity from PPTX",
    "beautify-inventory":     "Extract slide inventory from PPTX",
    "align-embed-images":     "Single-pass image alignment + Base64 embedding",
}


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv

    if len(argv) < 2 or any(a in ("-h", "--help") for a in argv[1:]):
        print("Usage: ppt-master <command> [args...]")
        print("\nCommands:")
        width = max(len(k) for k in COMMANDS) + 2
        for name in sorted(COMMANDS):
            desc = COMMAND_DESCRIPTIONS.get(name, "")
            print(f"  {name:<{width}}{desc}")
        return 0

    cmd = argv[1]
    args = argv[2:]

    script_rel = COMMANDS.get(cmd)
    if script_rel is None:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(f"Run 'ppt-master' without arguments to list commands.", file=sys.stderr)
        return 1

    script_path = os.path.join(SCRIPTS_DIR, script_rel)
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}", file=sys.stderr)
        return 1

    try:
        result = subprocess.run([sys.executable, script_path, *args])
        return result.returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
