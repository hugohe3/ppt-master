# ppt-master

> Originated by [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)

AI-driven PPT generation CLI — convert documents to editable PowerPoint via SVG pipeline.

## Install

```bash
# No install needed — run directly
uvx ppt-master <command>

# Or install globally
uv tool install ppt-master
pip install ppt-master
```

## Quick Start

```bash
# Create a project
uvx ppt-master project init my-presentation --format ppt169

# Convert source materials to Markdown
uvx ppt-master pdf-to-md paper.pdf -o my-presentation/sources/
uvx ppt-master web-to-md https://example.com -o my-presentation/sources/

# Post-process SVGs and export to PPTX
uvx ppt-master finalize-svg my-presentation
uvx ppt-master svg-to-pptx my-presentation
```

## Commands

| Command | Description |
|---------|-------------|
| `project` | Create / validate / manage PPT projects |
| `pdf-to-md` | Convert PDF to Markdown |
| `doc-to-md` | Convert DOCX / HTML / EPUB to Markdown |
| `excel-to-md` | Convert Excel to Markdown |
| `ppt-to-md` | Convert PPTX to Markdown |
| `web-to-md` | Convert URL to Markdown |
| `image-gen` | AI image generation (multi-backend) |
| `image-search` | Search and download web images |
| `latex-render` | Render LaTeX formulas to PNG |
| `analyze-images` | Analyze images and compute layout sizes |
| `svg-quality-check` | Validate SVG against PPT constraints |
| `total-md-split` | Split total.md into per-page files |
| `finalize-svg` | Post-process SVGs (icons, images, text) |
| `svg-to-pptx` | Export SVGs to PPTX |
| `svg-editor` | Launch web-based SVG editor (live preview) |
| `notes-to-audio` | Generate per-slide narration audio (TTS) |
| `animation-config` | Create / validate animation configuration |
| `pptx-template-import` | Extract SVG references from PPTX template |
| `template-fill-pptx` | Fill content into PPTX template |
| `pptx-to-svg` | Convert PPTX to SVG |
| `svg-position-calc` | Chart coordinate calculator |
| `update-spec` | Propagate color / font changes to all SVGs |
| `check-annotations` | Scan SVGs for edit annotations |
| `visual-review` | Visual review via Playwright |
| `update-repo` | Git pull + uv sync repository updater |
| `register-template` | Register layout template |
| `rotate-images` | Rotate images (EXIF + manual) |
| `config` | List canvas formats and color presets |
| `check-deps-sync` | Verify dependency manifest sync |

Run `uvx ppt-master` without arguments to see the full list.

## Configuration

AI backends use environment variables or a `.env` file:

```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
IMAGE_BACKEND=openai
```

See `.env.example` in the source repository for all options.

## Requirements

- Python 3.12+
- uv (recommended) or pip

## License

MIT — see [LICENSE](https://github.com/hugohe3/ppt-master/blob/main/LICENSE) in the original repository.
