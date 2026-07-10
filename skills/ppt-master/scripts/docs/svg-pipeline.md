# SVG Pipeline Tools

> Architecture rationale (why each artifact / step exists, deletion impact, two-consumer relationship between `svg_finalize/` and native pptx conversion): see [docs/technical-design.md "Post-Processing Pipeline"](../../../../docs/technical-design.md#post-processing-pipeline).

These tools cover post-processing, SVG validation, speaker notes, recorded narration, and PPTX export.

## Recommended Pipeline

Run these steps in order:

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/svg_to_pptx.py <project_path>
```

## `finalize_svg.py`

Unified post-processing entry point. This is the preferred way to run SVG cleanup.

It aggregates:
- `embed_icons.py`
- `align_embed_images.py` (`crop-images` / `fix-aspect` / `embed-images` aliases route here)
- `flatten_tspan.py`
- `svg_rect_to_path.py`

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

```bash
python3 scripts/svg_to_pptx.py <project_path>
python3 scripts/svg_to_pptx.py <project_path> --native-objects
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure template  # explicit SVG template metadata
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure preserve  # imported source package contract
python3 scripts/svg_to_pptx.py <project_path> --pptx-structure flat  # structure diagnostic
# Template-import visual round-trip diagnostic only:
python3 scripts/svg_to_pptx.py <template_import_output> --only native -s svg-flat
python3 scripts/svg_to_pptx.py <project_path> --no-notes
python3 scripts/svg_to_pptx.py <project_path> -t none
python3 scripts/svg_to_pptx.py <project_path> --auto-advance 3
python3 scripts/svg_to_pptx.py <project_path> --animation mixed --animation-duration 0.8
python3 scripts/svg_to_pptx.py <project_path> --no-merge   # strict line-fidelity mode (see below)
python3 scripts/notes_to_audio.py <project_path> --voice zh-CN-XiaoxiaoNeural
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
```

Behavior:
- Default output (default-flow mode, no `-o`):
  - `exports/<project_name>_<timestamp>.pptx` — native editable pptx (canonical output)
  - `backup/<timestamp>/svg_output/` — copy of Executor SVG source, always written so the pptx can be rebuilt via `finalize_svg → svg_to_pptx` without re-running the LLM
- `--svg-snapshot` (opt-in) additionally emits:
  - `exports/<project_name>_<timestamp>_svg.pptx` — SVG snapshot pptx for visual reference, sibling of the native pptx
  - Live preview already serves as the SVG visual reference for day-to-day use; the snapshot pptx is for distribution or frozen-state archival
- Explicit `-o/--output` skips `backup/`; pair with `--svg-snapshot` to also emit the side-by-side `_svg.pptx` next to the chosen path
- Paragraph merging is enabled by default and trades some SVG line-layout fidelity for PowerPoint editability:
  - Default: mergeable paragraph blocks (same x, dy clustered around one base line-height, optional larger gap for paragraph breaks) collapse into one editable text frame with multiple `<a:p>` and precise `<a:lnSpc>` / `<a:spcBef>`. Resizing the box reflows text inside it.
  - With `--no-merge`: every dy-stacked `<tspan>` becomes its own text frame — exact SVG line layout is preserved but a 12-line paragraph is 12 separate textboxes
  - Side effect: PowerPoint may wrap merged paragraphs to a different line count than the SVG source. Long body text (abstracts, multi-paragraph sections, reference lists) usually benefits from the default; pages with tight typographic alignment (covers, charts, tables) usually want `--no-merge`
  - Mergeable detection is conservative: only fires when the children form a clean paragraph block; mixed-layout `<text>` falls through to the default per-line path
- Native export reads `svg_output/`; `--svg-snapshot` and legacy export read
  `svg_final/`. Use `-s` only as an explicit diagnostic override.
- For PPTX template-import workspaces, use `-s svg-flat` when you need a visual round-trip check. The layered `svg/` tree is the machine-readable template source and intentionally does not inline inherited master / layout decoration into each slide.
- Native mode is strict about unsupported visual SVG elements: if a visual element cannot be represented or safely preserved, export fails with the SVG file, element tag, and position instead of silently dropping content.
- Omitting `--pptx-structure` reads `spec_lock.md` `pptx_structure.mode`, then falls back to `baseline`; an explicit CLI value overrides the lock. After SVG conversion, baseline assigns filename-backed `Cover` / `Agenda` / `Section` / `Closing` / `Content` layout families (while retaining an existing chrome-safety `Cover` assignment), keeps real page content slide-local, and moves a family background to Layout only when every member has the exact same explicit `p:bg`; it never infers placeholders or visual similarity. Template mode builds reusable PowerPoint layouts only from explicit SVG metadata: root `data-pptx-layout`, direct-child `data-pptx-layer="master|layout"`, optional `data-pptx-layer="slide"` on a full-canvas solid background, and direct-child `data-pptx-placeholder`. It validates the per-page `pptx_layouts` lock plus cross-slide structure consistency and never infers layouts from visual similarity. Direct full-canvas solid rects compile to Master/Layout/Slide `p:bg` by scope; an unmarked one is a Slide override. Chart/table placeholders also require `--native-objects`. Full contracts: [`shared-standards.md`](../../references/shared-standards.md#baseline-layout-family-extraction) and [`shared-standards.md`](../../references/shared-standards.md#explicit-pptx-master--layout--placeholder-metadata-template-export).
- Template/preserve placeholder semantics distinguish title, subtitle, body, picture, chart, table, generic object, media, date, footer, and slide number. Reconstructed titles are normally type-matched without an index; explicit imported title indices and all other source indices are retained. Imported `subTitle`, `obj`, `media`, and `dt` identities remain distinct through `manifest.json`, `native_structure.json`, Layout XML, and Slide XML.
- Baseline/template native export reads `spec_lock.md` typography into the PowerPoint theme: `title_family` becomes the major font and `body_family` / `font_family` becomes the minor font. Matching SVG text emits `+mj-*` / `+mn-*` tokens, while unrelated emphasis/code/brand families stay concrete. Preserve mode keeps the imported source theme; flat mode keeps fixed-font diagnostic output.
- Baseline/template native export also maps canonical `spec_lock.md` color roles into the PowerPoint color scheme and emits context-safe `schemeClr` tokens for exact matches in SVG fills/text/strokes, gradients/patterns/bullets, native tables, and native-chart accent series. Local colors, inverse white/black, and effects stay concrete. Preserve mode keeps the imported source color scheme; flat mode keeps fixed-color diagnostic output.
- Preserve mode requires both a Strategist-confirmed `template_adherence: strict` and a `create-template` native pair (`native_structure.json` + `source_template.pptx`) declared in `spec_lock.md`. It verifies the source digest, binds each generated page to an imported layout part, retains the source master/layout/theme roster, removes preview-only inherited SVG layers, and restores source placeholder type/index identities. The SVG root still declares `data-pptx-layout`; repeated semantic placeholders may disambiguate with `data-pptx-placeholder-idx`. `template_adherence: adaptive` keeps export on baseline even when the pair is present.
- Native output uses content-hash media filenames, so identical images are reused and different images cannot overwrite each other by sharing a basename.
- `[Content_Types].xml` is generated from the actual media extensions written into the PPTX. Unknown media extensions fail unless Python's `mimetypes` can identify them.
- Native export writes to a temporary file first and publishes the requested PPTX only after conversion succeeds. A failed conversion does not replace the main output file.
- SVG clip paths are still restricted for authored SVGs, but nested crop wrappers generated by PPTX import are mapped back to native picture crop / geometry when possible.
- Speaker notes are embedded automatically unless `--no-notes` is used
- Recorded narration is opt-in:
  - `notes_to_audio.py` uses `edge-tts` by default, or a configured cloud TTS provider (`elevenlabs`, `minimax`, `qwen`, `cosyvoice`), and generates one audio file per slide into `audio/`
  - Narration text is read strictly from the matching `notes/*.md` file; the script only skips Markdown heading lines (`# ...`) and does not summarize, rewrite, or filter delivery notes
  - `--recorded-narration audio` prepares PowerPoint's "recorded timings and narrations": every slide must have matching `m4a` / `mp3` / `wav` audio, `ffprobe` must read every duration, and `--animation-trigger on-click` is rejected
  - `--recorded-narration audio` keeps speaker notes, embeds each matching audio file, and writes slide auto-advance timings from audio duration
  - `--narration-audio-dir audio` is the lower-level embedding path: it embeds whatever files match and allows partial audio coverage
  - Either narration flag names the default-flow export `<project_name>_<timestamp>_narrated.pptx`, telling it apart from silent exports in the same directory
  - This is intended for direct PowerPoint video export with "Use recorded timings and narrations"
  - Long-audio import and automatic long-audio splitting are not supported; keep narration assets page-level
  - Voice choices can be listed with `python3 scripts/notes_to_audio.py --list-common-voices`, `python3 scripts/notes_to_audio.py --list-voices --locale zh-CN`, or provider-specific `--provider <name> --list-voices`
- Page transitions are controlled by `-t/--transition`; per-element entrance animations are controlled by `-a/--animation`
- Per-element animation applies to top-level SVG `<g id="...">` groups in z-order; aim for 3–8 content groups per slide. Page chrome (background / header / footer / decorations / watermark / page number, by id token) is skipped automatically
- Start mode is set by `--animation-trigger`, mirroring PowerPoint's Start dropdown: `after-previous` (default, cascade with `--animation-stagger` spacing on slide entry), `on-click` (presenter-paced), `with-previous` (all together on slide entry)
- `on-click` is for live presentations only; recorded narration rejects it because the tool does not generate object-level click timings
- Flat SVG roots without top-level groups fall back to at most 8 visible primitives; beyond that, animation is skipped on the slide
- Per-element animation defaults to `none`. `auto` is opt-in (`-a auto`) and maps
  effects from the group's SVG id: information-dense elements get a stable
  effect (chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade); image-like
  ids (hero/figure-/image/img-/kpi) cycle through a richer pool
  (zoom/dissolve/circle/box/diamond/wheel), while unmatched ids cycle through
  fade/wipe/fly/zoom.
- `mixed` (legacy) is deterministic: the first animated group on each slide uses `fade`, then later groups cycle through a larger 16-effect pool across the whole deck; `random` samples from that same legacy pool
- `--animation-duration` controls per-element entrance length (default `0.4`); `--animation-stagger` adds gap between elements in `after-previous` mode (default `0.5`)
- Optional object-level overrides live in `<project>/animations.json` or a path passed via `--animation-config`; build and validate them with `animation_config.py scaffold|validate`

Performance (legacy `_svg.pptx` PNG fallback, only when `--svg-snapshot` or `--only legacy`):
- SVG→PNG is pre-rendered in a process pool before the main loop. Default workers = `min(cpu, pages, 8)`; override with `--workers N` (set `1` for sequential, `0` is treated as sequential).
- Results are cached at `<project>/.cache/svg_png/` keyed by SVG content hash + size + active renderer (`cairosvg` vs `svglib`). Switching renderers naturally invalidates the cache; nothing to clean by hand.
- `--cache-dir <path>` relocates the cache; `--no-cache` forces re-render without writing/reading the cache (handy when debugging rendering).
- Native mode (`--only native`) is unaffected — that path embeds DrawingML shapes and never touches PNG.

Dependency:

```bash
pip install python-pptx
```

## `total_md_split.py`

Split `total.md` into per-slide note files.

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/total_md_split.py <project_path> -o <output_directory>
python3 scripts/total_md_split.py <project_path> -q
```

Requirements:
- Each section begins with `# `
- Heading text matches the SVG filename
- Sections are separated by `---`

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
python3 scripts/svg_quality_checker.py examples/project/svg_output/01_cover.svg
python3 scripts/svg_quality_checker.py examples/project/svg_output
python3 scripts/svg_quality_checker.py examples/project
python3 scripts/svg_quality_checker.py examples/project --format ppt169
python3 scripts/svg_quality_checker.py --all examples
python3 scripts/svg_quality_checker.py examples/project --export
```

Checks include:
- `viewBox`
- banned elements
- line-break structure

## `svg_position_calculator.py`

Analyze and review supported chart coordinates after SVG generation.

Use this after `svg_quality_checker.py` passes, and only for chart types supported by this script: `bar`, `pie` / `donut`, `radar`, `line` / `area` / `scatter`, and `grid`. Area charts do not have a separate calculator mode: use `calc line` for the upper boundary points, then close the filled region to the plot area's bottom baseline (`y_max`) in the SVG.

### Calculate expected coordinates

```bash
python3 scripts/svg_position_calculator.py calc bar --data "A:185,B:142" --area "130,155,1200,480" --bar-width 120
python3 scripts/svg_position_calculator.py calc line --data "0:50,10:80,20:120" --area "120,120,1200,600" --y-range "0,150"
python3 scripts/svg_position_calculator.py calc pie --data "A:35,B:25,C:20" --center "420,400" --radius 200
python3 scripts/svg_position_calculator.py calc grid --rows 2 --cols 3 --area "50,150,1230,670"
```

For an area chart, use the line output as the top boundary:

```svg
M first_x,first_y ... L last_x,last_y L last_x,y_max L first_x,y_max Z
```

Manually compare the calculator output with the coordinates already present in the generated SVG. If coordinates differ, update the SVG from the `calc` output, rerun `svg_quality_checker.py`, then repeat the coordinate review. The tool intentionally does not rewrite SVG files automatically.

### Analyze (inspect existing SVG)

```bash
python3 scripts/svg_position_calculator.py analyze <svg_file>
```

Use this after SVG generation to inspect existing SVG geometry when manual comparison needs more context.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
python3 scripts/svg_finalize/flatten_tspan.py examples/<project>/svg_output
python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `svg_rect_to_path.py`

```bash
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path>
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path> -s final
python3 scripts/svg_finalize/svg_rect_to_path.py path/to/file.svg
```

Use when rounded corners must survive PowerPoint shape conversion.

### `align_embed_images.py`

```bash
python3 scripts/svg_finalize/align_embed_images.py path/to/slide.svg
python3 scripts/svg_finalize/align_embed_images.py --dry-run path/to/slide.svg
```

Use for rare single-file diagnostics when image `slice` / `meet` alignment and
Base64 embedding must be inspected outside `finalize_svg.py`. In normal project
runs, use `python3 scripts/finalize_svg.py <project_path>`; the old
`crop-images`, `fix-aspect`, and `embed-images` names remain accepted only as
`finalize_svg.py --only` aliases for the merged `align-images` step.

### `embed_icons.py`

```bash
python3 scripts/svg_finalize/embed_icons.py output.svg
python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Replaces `<use data-icon="chunk-filled/name" .../>`, `<use data-icon="tabler-filled/name" .../>` and `<use data-icon="tabler-outline/name" .../>` placeholders with actual SVG path elements. Use for manual icon embedding checks outside `finalize_svg.py`.

## PPT Compatibility Rules

Use PowerPoint-safe transparency syntax:

| Avoid | Use instead |
|------|-------------|
| `fill=\"rgba(...)\"` | `fill=\"#hex\"` + `fill-opacity` |
| `<g opacity=\"...\">` | Set opacity on each child |
| `<image opacity=\"...\">` | Overlay with a mask layer |

PowerPoint also has trouble with unsupported filters and direct SVG features
not mapped to DrawingML. Connector arrows may use qualified
`marker-start` / `marker-end`; chunky or exotic arrows should be standalone
`<path>` / `<polygon>` shapes.
