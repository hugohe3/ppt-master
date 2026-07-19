# Project Tools

> **Import boundary**: copy out-of-repository sources by default to protect user
> files; move in-repository sources by default to avoid leaving accidental
> commit artifacts. Explicit `--copy` / `--move` flags override the default.

Project tools create, validate, and inspect the standard PPT Master workspace.

## `project_manager.py`

Main entry point for project setup and validation.

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source1_or_dir> [<source2_or_dir> ...]
python3 scripts/project_manager.py scaffold-spec <project_path>
python3 scripts/project_manager.py scaffold-lock <project_path>
python3 scripts/project_manager.py validate <project_path>
python3 scripts/project_manager.py info <project_path>
python3 scripts/project_manager.py page-context <project_path> P07 [--bundle] [--pretty] [--record-usage]
python3 scripts/project_manager.py page-context-report <project_path>
```

Notes:
- Files outside the repo are copied into `sources/` by default
- With `--move`, files outside the repo are moved into `sources/`
- Directory inputs are expanded non-recursively. After Step 1 conversion,
  pass the source file/directory once when generated Markdown lives beside the
  original source. If Step 1 used `-o` to write Markdown elsewhere, pass both
  the original source path/directory and the Markdown output path/directory.
- Files already inside the repo are moved into `sources/` by default (with a stderr
  note), to avoid leaving unintended artifacts that could be committed by mistake.
  Pass `--copy` to force a copy for in-repo sources instead.
- `--move` and `--copy` are mutually exclusive.
- `scaffold-spec` creates `design_spec.md` from
  `templates/scaffolds/design_spec.md`; `scaffold-lock` creates `spec_lock.md`
  from `templates/scaffolds/spec_lock.md`. Both substitute project/canvas
  metadata deterministically and refuse to overwrite an existing artifact.
- `validate` parses the existing Markdown artifacts against
  `templates/schemas/design_spec.schema.json` and
  `templates/schemas/spec_lock.schema.json`. It reports missing sections and
  fields, illegal enums, malformed page keys, and unmet conditional sections;
  it does not rewrite either artifact or compare their values for textual
  equality. It also does not prove final-confirmation → Design Spec fidelity or
  Design Spec → lock semantic projection; Generate Step 4 owns those two gates
  before this structural validation. One slice is enforced mechanically: when
  `confirm_ui/result.json` records a final confirmed stage, every confirmed
  non-`none` `image_usage` source must appear in at least one `## images` row
  of the lock (`provided` maps to `user`; `ai` is also satisfied by `slice`).
  The design schema is structural lint for
  the human-readable brief; the lock schema owns machine execution values. For structured template use,
  validation also compares the lock's Master/Layout identities with the actual
  template SVG roots. Versioned scaffolds carry the schema marker. Markerless
  legacy artifacts are left on their prior validation path with a warning;
  malformed or unsupported markers are errors.
- PPTX-family inputs are enriched automatically under `analysis/` with
  per-deck `<stem>.identity.json` / `<stem>.slide_library.json` plus the shared
  multi-deck index `source_profile.json` (`decks[]`).
  Multi-deck per project: several PPTX imports each get their own `<stem>.*`
  artifacts and a `decks[]` entry; re-importing the same stem replaces its entry.

### Per-page execution view

`page-context` projects `design_spec.md` and `spec_lock.md` into one current-page
view on stdout. The default command is read-only; `--pretty` changes JSON
formatting only. Before projection it revalidates only the machine lock and any
selected template-root identities; design-brief values are not treated as a
second lock. When present, the human-readable `Template Application` prose from
`design_spec.md §I` is projected as `global.template_application`. Slide
headings at H3–H6 remain readable by the projector.
`--bundle` appends only the route-selected authoring payloads:

| Project mode | Bundle contents |
|---|---|
| `flat` | page context |
| structured `layout` | page context + complete selected prototype SVG |
| structured `mirror` | page context + `text-slots.v2-min` + complete selected prototype SVG |

The projection keeps project-specific forbidden rules; universal SVG and icon
rules remain in the always-loaded execution core. Image rows are selected from
the current §IX brief, explicit §VIII page assignments, and mirror prototype
references. When those sources assign images elsewhere but not to the current
page, the view excludes those assigned images. Any still-unassigned legacy
image remains in a compatibility subset; `confirmed-none` is emitted only when
all locked images have a deterministic assignment elsewhere.

Mirror materialization publishes `ppt-master.template-text-slots.v2-min` with
only `selector`, `role`, `current_text`, `text_segments`, and `tspan_count` per
text node. Its top-level integrity hash covers selectors plus immutable text
and tspan topology/attributes. `page-context` recomputes that hash and every
model-visible field from the complete prototype before stripping the hash from
the bundle. A legacy v1 sidecar receives the same checks and is projected to the
same model-facing shape in memory; the workspace is not rewritten. The complete
SVG remains in the bundle. Checker and structured export validate output
attributes, text/tspan topology, and referenced-resource hashes internally, so
authoring supplies only semantic choices and edits only the existing visible
text values.

`--record-usage` requires `--bundle` and writes a derived snapshot to
`analysis/page-context/P<NN>.usage.json`. It hashes every input and measures the
exact controlled stdout plus each component; expected-but-absent optional inputs
are recorded so later artifact creation invalidates the snapshot. `tiktoken` is
loaded lazily with `o200k_base`; when unavailable, the command still succeeds
and records bytes, characters, hashes, and `tokens: null`.
`page-context-report` summarizes only fresh snapshots and identifies stale or
token-unavailable pages. The telemetry does not include source-material reads
or session-level prompt references.

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
python3 scripts/project_manager.py scaffold-spec projects/my_presentation_ppt169_20251116
python3 scripts/project_manager.py scaffold-lock projects/my_presentation_ppt169_20251116
python3 scripts/project_manager.py validate projects/my_presentation_ppt169_20251116
python3 scripts/project_manager.py info projects/my_presentation_ppt169_20251116
python3 scripts/project_manager.py page-context projects/my_presentation_ppt169_20251116 P07 --bundle --record-usage
python3 scripts/project_manager.py page-context-report projects/my_presentation_ppt169_20251116
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

Unified PPTX preparation entry point for `/create-template`.

```bash
python3 scripts/pptx_template_import.py <template.pptx>
python3 scripts/pptx_template_import.py <template.pptx> -o <output_dir>
python3 scripts/pptx_template_import.py <template.pptx> --manifest-only
python3 scripts/pptx_template_import.py <template.pptx> --skip-manifest
python3 scripts/pptx_template_import.py <template.pptx> --embed-images
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode both
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode flat
python3 scripts/pptx_template_import.py <template.pptx> --inheritance-mode layered
```

Notes:
- Extracts reusable media assets from `ppt/media/`
- Summarizes slide size, theme colors, font metadata, and per-master theme metadata
- Resolves slide / layout / master relationships from OOXML relationships; every master and layout is included even when no sample slide currently references it
- Generates `manifest.json` (single source of truth for slide size, theme, per-master themes, assets, layouts, masters, placeholders, slides, SVG file paths, and page-type candidates), `native_structure.json`, `source_template.pptx`, `assets/`, `conversion-report.json`, and shape-level SVGs under `svg/`
- **SVG output defaults to the layered authoring source** (`--inheritance-mode layered`):
  - `svg/` — layered template view for designers: every master and layout in the deck rendered once as `svg/master_*.svg` / `svg/layout_*.svg` (including ones no sample slide currently references); `svg/slide_NN.svg` contains only that slide's own shapes; `svg/inheritance.json` records parentage plus source-owned `showInheritedShapes` / `showMasterShapes` booleans.
  - `svg-flat/` — optional verification view emitted only by `--inheritance-mode both`: each `slide_NN.svg` is self-contained (the effective visible Master/Layout contributions plus Slide-local content painted into one file), so opening any slide in isolation shows the full page like PowerPoint would. Background inheritance remains independent of inherited-shape visibility. Useful for previews, screenshots, and "did this slide actually render correctly" sanity checks.
- `manifest.json` records `svgFile` for slides / layouts / masters, `flatSvgFile` for slides when `svg-flat/` exists, placeholder type / index / geometry / base style, an asset map used by SVG `href` values, and common assets reused through slide / layout / master inheritance. Placeholder semantics keep `subTitle`, `obj`, `media`, and `dt` distinct as `subtitle`, `object`, `media`, and `date`.
- `conversion-report.json` owns tolerant source-recovery diagnostics; it is not a cache or a duplicate of the structural manifests
- Layered slide SVGs keep only the slide's own background; inherited master / layout backgrounds stay in the corresponding master / layout SVGs
- Placeholder guides are intentionally lightweight in `svg/` master / layout files; `svg-flat/` hides those guides and is the visual preview source
- Charts, SmartArt, diagrams, and OLE objects become typed placeholders in `svg/`; `svg-flat/` shows a preview image with a corner badge when one exists, otherwise a visible placeholder. Tables are converted into real SVG content.
- Pass `--inheritance-mode both` to add `svg-flat/`, or `--inheritance-mode flat` for the legacy round-trip view (single self-contained `svg/` tree without master/layout/inheritance files).
- SVG export reads OOXML directly via `pptx_to_svg` — no PowerPoint or Keynote dependency, runs on any platform
- `<image>` elements in `svg/` reference files in `assets/` directly; pass `--embed-images` to inline as data URIs instead
- External linked images and missing media are strict failures. Office vector media such as EMF / WMF are converted to PNG previews when the local toolchain can do so; otherwise the import fails instead of silently dropping content.
- Required in `/create-template` whenever the reference source is `.pptx`
- Default output directory is `<pptx_stem>_template_import/`
- Use `--manifest-only` when you explicitly want only the lightweight import output without slide SVG export
- Intended for template reference preparation, not for final 1:1 template delivery

Implementation note:
- Internal helpers for this workflow live under `scripts/template_import/`

## `error_helper.py`

Show standardized fixes for common project errors.

```bash
python3 scripts/error_helper.py
python3 scripts/error_helper.py missing_readme
python3 scripts/error_helper.py missing_readme project_path=my_project
```
