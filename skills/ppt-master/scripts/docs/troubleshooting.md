# Troubleshooting

## Validation Failed

1. Run:

```bash
python3 scripts/project_manager.py validate <project_path>
```

2. Fix missing files or invalid directories reported by the validator.
3. Re-run validation before post-processing or export.

## SVG Preview Looks Wrong

1. Check the file path and filename.
2. Confirm naming conventions are consistent.
3. Run the mandatory post-processing step when you need a self-contained preview:

```bash
python3 scripts/finalize_svg.py <project_path>
python3 -m http.server --directory <project_path>/svg_final 8000
```

`svg_final/` is the visual-preview artifact and may be inserted into PowerPoint as an SVG picture. Fix authored content in `svg_output/`, then regenerate `svg_final/`; do not edit the derived preview as the source.

## Speaker Notes Do Not Split

Check `total.md`:
- headings must start with `# `
- heading text must match SVG filenames
- sections must be separated by `---`

Then rerun:

```bash
python3 scripts/total_md_split.py <project_path>
```

## PPT Export Quality Issues

Preferred sequence:

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

Keep all three steps even though they have different consumers: Step 7.2 creates the mandatory `svg_final/` visual preview, while the supported native PPTX exporter reads `svg_output/` directly. Do not pass `-s final` for a release export; that override is diagnostic-only.

## Inserted SVG Does Not Convert Cleanly to Shapes

PowerPoint's manual Convert-to-Shape behavior is unsupported. `svg_final/` is supported only as a visual preview / SVG picture. Use the native PPTX generated from `svg_output/` when editable DrawingML shapes are required.

## Recorded Narration Missing

1. Generate audio after `total_md_split.py`, so filenames in `audio/` can match split `notes/*.md` files.
2. Export with the project-relative audio directory:

```bash
python3 scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
```

`--recorded-narration` prepares PowerPoint recorded timings and narrations. If it fails, check:
- every slide has a matching `m4a`, `mp3`, or `wav` file in `audio/`
- `ffprobe` is installed and can read each audio duration
- the deck is not using `--animation-trigger on-click`

Use `--narration-audio-dir audio` only when you intentionally want lower-level, partial audio embedding instead of PowerPoint recorded timings.

## Dependency Checklist

Most tools use the standard library. Install extra dependencies only when needed:

```bash
pip install -r requirements.txt
```

Important optional packages:
- `python-pptx` for PPTX export
- `edge-tts` for `notes_to_audio.py` recorded narration audio
- `Pillow` for image utilities
- `numpy` for watermark removal
- `PyMuPDF` for PDF conversion
- `google-genai` for Gemini image generation
