# Artifact Ownership Specification

Global artifact ownership rules for PPT Master projects.

**Hard rule**: Read each fact from its owning artifact. Do not merge multiple channels into a second source of truth.

---

## 1. Ownership Matrix

| Artifact | Owner | Role | Read/write contract |
|---|---|---|---|
| `sources/` content-type files | Content contract | Main pipeline source for text, tables, chart data values, and SmartArt node wording | Strategist reads content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judges by content; do not replace values with PPTX geometry JSON in the main pipeline |
| `sources/` converted-source originals | Source archive | Imported source files that have a converted content contract (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) and source-adjacent extracted assets | Read via the converted `<stem>.md` in the main pipeline; direct-PPTX workflows read the `.pptx` by route |
| `sources/*.conversion_profile.json`, `sources/*_files/image_manifest.json` | Pipeline sidecar | Conversion audit record / asset index | NOT read as slide content; open only to audit a conversion or resolve assets |
| `analysis/source_profile.json` | Machine fact index | Compact Strategist-facing PPTX intake digest | Main pipeline reads as factual context and recommendation candidates |
| `analysis/<stem>.identity.json` | Native deck identity facts | Canvas, theme palette/fonts, observed usage | Read selectively when detailed identity facts are needed |
| `analysis/<stem>.slide_library.json` | Native PPTX structure facts | Text slots, geometry, native tables, native chart caches, SmartArt nodes/connections | Direct PPTX workflows use as native fill/structure contract |
| `analysis/image_analysis.csv` | Regenerated image fact view | Measured facts about the current `images/` folder | Re-run `analyze_images.py` before reading image facts after changes |
| `design_spec.md` | Human design narrative | Explains design intent, outline, rationale, and resource plan | Strategist writes; humans and later roles read for intent |
| `spec_lock.md` | Execution contract | Literal colors, typography, icons, images, page rhythm, charts, and the route's PowerPoint structure mode; deck/layout template routes additionally own input prototypes, the Master roster, and the complete page-to-Master/Layout mapping | Strategist writes the route-specific contract; Executor re-reads it before every page and may add a new adaptive Layout identity only on a structured template route while authoring the page that first needs it |
| `images/` | Runtime image pool | User, extracted, AI, web, formula, slice, EMF/WMF assets | Step 5 writes here; `analysis/image_analysis.csv` derives from current contents |
| `icons/` | Project icon inventory | Icons copied by `icon_sync.py` for this project | Executor uses locked project icons; exporter may fall back to global library only as documented |
| `templates/` | Project template reference | Step 3 imported specs, template SVGs, and non-image assets | Strategist/Executor read only when Step 3 is triggered |
| `<import_workspace>/svg/` | Imported native-payload backing | Complete PPTX-derived metadata, hidden carriers, fallback evidence, and source structure | Keep immutable; create-template materialization may resolve a validated source ref against these files, but models do not edit or bulk-read them |
| `<import_workspace>/svg-flat/` | Optional complete-page verification backing | Self-contained visual composition generated only by explicit `--inheritance-mode both` | Keep immutable when requested; never use as authoring or materialization input |
| `<import_workspace>/authoring-svg/` | Template-creation author source | Layered editable SVG IR for imported Master, Layout, and Slide objects | Template_Designer reads and edits this bundle; final template SVGs are materialized from it rather than copied from lossless backing |
| `<import_workspace>/authoring-svg/authoring_summary.json` | Model-readable authoring index | Current SVG roster plus compact per-file canvas, size, text, image, vector, placeholder, and source-ref counts | Models read this before authoring SVGs; regenerate after direct IR edits |
| `<import_workspace>/authoring-svg/authoring_manifest.json` | Tool-only authoring provenance contract | Per-document source/authoring hashes and document-local source-ref paths | Generated atomically with the IR; materialization validates it before reusing native payload; never load it into model context or duplicate raw payload here |
| `<import_workspace>/authoring-svg-flat/` | Optional complete-page verification IR | Self-contained page composition view with its own summary and provenance manifest | Generate only from an explicitly requested `svg-flat/`; use to verify composition, while layered `authoring-svg/` remains the canonical editable source |
| `<import_workspace>/icons/imported/` | Imported vector pool | One canonical copy of every factored vector subtree | Authoring SVGs reference `data-icon="imported/<name>"`; vector inventories retain source refs so expansion re-establishes IR identity |
| `confirm_ui/recommendations.json` | Confirmation proposal | Strategist-authored confirmation payload | Confirm UI reads; rewritten between Stage 1, Stage 2, and Stage 3 |
| `confirm_ui/result.json` | Confirmation result | User-confirmed values | Strategist treats final result as authoritative over recommendations |
| `svg_output/` | Page-design author source | Main-agent handwritten SVG pages containing the complete visible design | Quality checker and native PPTX export read this as the canonical visual/page-layout source; templates and locks do not add missing visible objects at export |
| `notes/total.md` | Speaker-note source | Complete notes before splitting | Step 6 writes; Step 7.1 splits |
| `notes/slide_*.md` | Split notes | Per-slide notes generated from `total.md` | Derived by `total_md_split.py` |
| `svg_final/` | Derived visual preview | Self-contained post-processed SVGs that may be opened directly or inserted as SVG pictures | Rebuild from `svg_output/` with `finalize_svg.py`; do not use as a supported PPTX source |
| `exports/` | Delivery artifacts | Native DrawingML PPTX and its explicit native-object/narration variants | Step 7.3 writes final outputs from `svg_output/` |
| `backup/<timestamp>/svg_output/` | Frozen author-source archive | Re-export source without re-running LLM | `svg_to_pptx.py` writes a snapshot during export |
| `animations.json` | Optional animation config | Object-level animation sidecar | Created only by explicit animation workflow/request |

---

## 2. Ownership Invariants

| Invariant | Rule |
|---|---|
| Content values | Main pipeline text, tables, chart values, and SmartArt node wording come from content-type files in `sources/` (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`), not from `slide_library.json`. |
| Sources read policy | In `sources/`, read content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judge by content — a `.json` / `.csv` may be core content or just data. Exclude known sidecars: `*.conversion_profile.json` and `*_files/image_manifest.json`. `analysis/` facts (`source_profile.json`, `<stem>.slide_library.json`) are read per Step 4 / direct-PPTX workflow, not in the `sources/` content scan. |
| PPTX structure | `slide_library.json` owns native geometry, slot facts, and SmartArt layout/relationships for direct PPTX workflows. |
| Design contract | `design_spec.md` explains; `spec_lock.md` executes. Executor must not infer execution values from prose. |
| Free-design / brand-only packaging authority | `spec_lock.md` declares `pptx_structure.mode: flat` and omits `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts`. `svg_output/` owns the complete Slide-local visual design without root Master/Layout identity, fixed-layer ownership, or placeholder metadata. Export materializes one clean project-owned Master plus one Blank Layout, applies the locked theme defaults, removes stock content placeholders/Layout inventory, and retains only the standard date/footer/slide-number capability hooks. |
| Template structure authority | `page_layouts` owns each page's authoring-input prototype. `pptx_masters` / `pptx_layouts` own the unique reusable output definitions, while `page_pptx_layouts` owns page assignment. Strict keeps the prototype contract; adaptive may create a new Layout definition during page authoring and updates its assignment immediately. Unused definitions may register without a published Slide. Templates validate provenance but never add missing visible page objects during export. |
| Imported-template authoring | Editable SVGs under `authoring-svg/` own create-template edits, `authoring_summary.json` owns model-facing orientation, and `authoring_manifest.json` owns tool-only source-object identity. Lossless `svg/` owns immutable native payload and fallback evidence; optional `svg-flat/` owns only complete-page verification. Materialized `templates/*.svg` own the validated deliverable contract and contain no IR-only source refs. |
| Legacy template input | Old unmapped/distilled/preserve structured projects and incomplete template packages are not migrated in place. [`create-template`](../workflows/create-template.md) authors a new current workspace: original PPTX Type A may preserve existing native topology in mirror; legacy SVG-only Type B is visual reference for `standard` / `fidelity`. An intentional free-design or brand-only `flat` project is already current. The exporter does not migrate or visually cluster legacy structure. |
| Image facts | `images/` is live state; `analysis/image_analysis.csv` is a regenerated view, not a durable cache. |
| SVG source | `svg_output/` is the only author source for generated pages. |
| Page-design closure | On SVG-authoring routes, every visible exported-slide object exists in the corresponding page SVG or an explicitly referenced visual asset. |
| Package-behavior separation | Speaker notes, animations, transitions, narration, and direct native-PPTX workflows keep their owning artifacts; do not force them into SVG metadata. |
| Post-processed SVG | `svg_final/` is disposable, must be rebuilt in Step 7.2, and serves only as a self-contained visual preview / manually insertable SVG picture. |
| Export source | The only supported generated-PPTX route reads `svg_output/` through the project SVG-to-DrawingML converter. A diagnostic `-s final` override does not change ownership or create a supported release route. |
| Shape-conversion boundary | PowerPoint's manual Convert-to-Shape operation on `svg_final/` is outside the project compatibility contract. |
| Confirmation | Final `confirm_ui/result.json` or chat confirmation overrides recommendations. |

**Forbidden - mixed ownership**: Do not copy chart values from Markdown into `analysis/` by hand, do not edit `svg_final/` as the source of a fix, do not edit imported lossless SVGs instead of their authoring IR, and do not treat `design_spec.md` prose as a replacement for `spec_lock.md`.

---

## 3. Regeneration Rules

| Derived artifact | Regenerate from | Command / owner |
|---|---|---|
| `analysis/image_analysis.csv` | Current `images/` | `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` |
| `<import_workspace>/authoring-svg/authoring_summary.json` | Current authoring SVGs plus tool-only manifest roster | `python3 ${SKILL_DIR}/scripts/svg_authoring_view.py <import_workspace>/authoring-svg --refresh-summary`; in-place vector/picture extraction refreshes it automatically |
| `notes/slide_*.md` | `notes/total.md` | `python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>` |
| `svg_final/` | `svg_output/` plus project assets | `python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>` |
| Native PPTX | `svg_output/` plus notes/assets | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>` |

**Default - regenerate derived views**: When a source artifact changes, regenerate the derived artifact at the owning step instead of patching the derived file directly.
