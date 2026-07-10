# Artifact Ownership Specification

Global artifact ownership rules for PPT Master projects.

**Hard rule**: Read each fact from its owning artifact. Do not merge multiple channels into a second source of truth.

---

## 1. Ownership Matrix

| Artifact | Owner | Role | Read/write contract |
|---|---|---|---|
| `sources/` content-type files | Content contract | Main pipeline source for text, tables, and chart data values | Strategist reads content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judges by content; do not replace values with PPTX geometry JSON in the main pipeline |
| `sources/` converted-source originals | Source archive | Imported source files that have a converted content contract (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) and source-adjacent extracted assets | Read via the converted `<stem>.md` in the main pipeline; direct-PPTX workflows read the `.pptx` by route |
| `sources/*.conversion_profile.json`, `sources/*_files/image_manifest.json` | Pipeline sidecar | Conversion audit record / asset index | NOT read as slide content; open only to audit a conversion or resolve assets |
| `analysis/source_profile.json` | Machine fact index | Compact Strategist-facing PPTX intake digest | Main pipeline reads as factual context and recommendation candidates |
| `analysis/<stem>.identity.json` | Native deck identity facts | Canvas, theme palette/fonts, observed usage | Read selectively when detailed identity facts are needed |
| `analysis/<stem>.slide_library.json` | Native PPTX structure facts | Text slots, geometry, native tables, native chart caches | Direct PPTX workflows use as native fill/structure contract |
| `analysis/image_analysis.csv` | Regenerated image fact view | Measured facts about the current `images/` folder | Re-run `analyze_images.py` before reading image facts after changes |
| `design_spec.md` | Human design narrative | Explains design intent, outline, rationale, and resource plan | Strategist writes; humans and later roles read for intent |
| `spec_lock.md` | Execution contract | Literal colors, typography, icons, images, page rhythm, templates, and charts | Executor re-reads before every page; values must be used verbatim |
| `images/` | Runtime image pool | User, extracted, AI, web, formula, slice, EMF/WMF assets | Step 5 writes here; `analysis/image_analysis.csv` derives from current contents |
| `icons/` | Project icon inventory | Icons copied by `icon_sync.py` for this project | Executor uses locked project icons; exporter may fall back to global library only as documented |
| `templates/` | Project template reference | Step 3 imported specs, template SVGs, and non-image assets | Strategist/Executor read only when Step 3 is triggered |
| `confirm_ui/recommendations.json` | Confirmation proposal | Strategist-authored confirmation payload | Confirm UI reads; rewritten between Stage 1, Stage 2, and Stage 3 |
| `confirm_ui/result.json` | Confirmation result | User-confirmed values | Strategist treats final result as authoritative over recommendations |
| `svg_output/` | Page-design author source | Main-agent handwritten SVG pages containing the complete visible design | Quality checker and native PPTX export read this as the canonical visual/page-layout source; templates and locks do not add missing visible objects at export |
| `notes/total.md` | Speaker-note source | Complete notes before splitting | Step 6 writes; Step 7.1 splits |
| `notes/slide_*.md` | Split notes | Per-slide notes generated from `total.md` | Derived by `total_md_split.py` |
| `svg_final/` | Derived preview/export SVGs | Self-contained post-processed SVGs | Rebuild from `svg_output/` with `finalize_svg.py` |
| `exports/` | Delivery artifacts | Native PPTX and optional SVG snapshot PPTX | Step 7.3 writes final outputs |
| `backup/<timestamp>/svg_output/` | Frozen author-source archive | Re-export source without re-running LLM | `svg_to_pptx.py` writes a snapshot during export |
| `animations.json` | Optional animation config | Object-level animation sidecar | Created only by explicit animation workflow/request |

---

## 2. Ownership Invariants

| Invariant | Rule |
|---|---|
| Content values | Main pipeline text, tables, and chart values come from content-type files in `sources/` (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`), not from `slide_library.json`. |
| Sources read policy | In `sources/`, read content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judge by content — a `.json` / `.csv` may be core content or just data. Exclude known sidecars: `*.conversion_profile.json` and `*_files/image_manifest.json`. `analysis/` facts (`source_profile.json`, `<stem>.slide_library.json`) are read per Step 4 / direct-PPTX workflow, not in the `sources/` content scan. |
| PPTX structure | `slide_library.json` owns native geometry and slot facts for direct PPTX workflows. |
| Design contract | `design_spec.md` explains; `spec_lock.md` executes. Executor must not infer execution values from prose. |
| Image facts | `images/` is live state; `analysis/image_analysis.csv` is a regenerated view, not a durable cache. |
| SVG source | `svg_output/` is the only author source for generated pages. |
| Page-design closure | On SVG-authoring routes, every visible exported-slide object exists in the corresponding page SVG or an explicitly referenced visual asset. |
| Package-behavior separation | Speaker notes, animations, transitions, narration, and direct native-PPTX workflows keep their owning artifacts; do not force them into SVG metadata. |
| Post-processed SVG | `svg_final/` is disposable and must be rebuildable from `svg_output/`. |
| Export source | Native PPTX export reads `svg_output/` by default. SVG snapshot export reads `svg_final/` only when requested. |
| Confirmation | Final `confirm_ui/result.json` or chat confirmation overrides recommendations. |

**Forbidden - mixed ownership**: Do not copy chart values from Markdown into `analysis/` by hand, do not edit `svg_final/` as the source of a fix, and do not treat `design_spec.md` prose as a replacement for `spec_lock.md`.

---

## 3. Regeneration Rules

| Derived artifact | Regenerate from | Command / owner |
|---|---|---|
| `analysis/image_analysis.csv` | Current `images/` | `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` |
| `notes/slide_*.md` | `notes/total.md` | `python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>` |
| `svg_final/` | `svg_output/` plus project assets | `python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>` |
| Native PPTX | `svg_output/` plus notes/assets | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>` |
| SVG snapshot PPTX | `svg_final/` | `svg_to_pptx.py --svg-snapshot` |

**Default - regenerate derived views**: When a source artifact changes, regenerate the derived artifact at the owning step instead of patching the derived file directly.
