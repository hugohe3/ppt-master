# Artifact Ownership Specification

Global artifact ownership rules for PPT Master projects.

**Hard rule**: Read each fact from its owning artifact. Do not merge multiple channels into a second source of truth.

---

## 1. Ownership Matrix

| Artifact | Owner | Role | Read/write contract |
|---|---|---|---|
| `sources/` content-type files | Content contract | Main pipeline source for text, tables, chart data values, and SmartArt node wording | Strategist reads content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judges by content; do not replace values with PPTX geometry JSON in the main pipeline |
| `sources/*.facts.json` | Fact provenance contract | Stable external `fact_id` → claim/source mapping created by topic research | Strategist cites IDs in §IX; Executor resolves them for visible footnotes / natural notes attribution. Scenario data never enters this file. |
| `sources/` converted-source originals | Source archive | Imported source files that have a converted content contract (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) and source-adjacent extracted assets | Read via the converted `<stem>.md` in the main pipeline; direct-PPTX workflows read the `.pptx` by route |
| `sources/*.conversion_profile.json`, `sources/*_files/image_manifest.json` | Pipeline sidecar | Conversion audit record / asset index | NOT read as slide content; open only to audit a conversion or resolve assets |
| `analysis/source_profile.json` | Machine fact index | Compact Strategist-facing PPTX intake digest | Main pipeline reads as factual context and recommendation candidates |
| `analysis/<stem>.identity.json` | Native deck identity facts | Canvas, theme palette/fonts, observed usage | Read selectively when detailed identity facts are needed |
| `analysis/<stem>.slide_library.json` | Native PPTX structure facts | Text slots, geometry, native tables, native chart caches, SmartArt nodes/connections | Direct PPTX workflows use as native fill/structure contract |
| `analysis/image_analysis.csv` | Regenerated image fact view | Measured facts about the current `images/` folder | Re-run `analyze_images.py` before reading image facts after changes |
| `design_spec.md` | Strategist design authority | Human-readable design intent, outline, rationale, and resource plan authored from the final confirmation plus source analysis | Strategist writes and audits it against every confirmed field before lock projection; humans and later roles read it for intent |
| `spec_lock.md` | Execution projection | Machine-readable colors, typography, icons, images, page rhythm, charts, `template_reuse_scope`, and the route's PowerPoint structure mode; mirror/layout template routes additionally own input prototypes, the Master roster, and the complete page-to-Master/Layout mapping | Strategist projects the route-specific contract from the audited Design Spec without making another design decision; `page-context` deliberately repeats its compact global projection per page as an anti-drift guard and adds current-page routing values. Executor may add a new adaptive Layout identity only on a structured mirror/layout route while authoring the page that first needs it. |
| `project_manager.py page-context` stdout | Derived per-page context | Read-only model-facing lock projection + current-page delta + fingerprints for large references | Generate immediately before each page without `--bundle`; never edit or persist it as a replacement source of truth. `global` is the bounded repeated lock guard. `reference_set` carries path/SHA/load policy for project/template Design Specs and selected prototype/chart SVGs, but never appends their payloads. |
| `analysis/page-context/P<NN>.usage.json` | Derived context telemetry | Actual compact page-context size plus hashes of owning inputs/references | `page-context --record-usage` deterministically replaces that page's snapshot; `page-context-report` summarizes current snapshots and unique references. Use token data to evaluate context cost, never as content or an execution contract. |
| `images/` | Runtime image pool | User, extracted, AI, web, formula, slice, EMF/WMF assets | Step 5 writes here; `analysis/image_analysis.csv` derives from current contents |
| `icons/` | Project icon inventory | Icons copied by `icon_sync.py` for this project | Executor uses locked project icons; exporter may fall back to global library only as documented |
| `templates/` | Project template reference | Step 3 imported specs, template SVGs, and non-image assets | Strategist reads the template Design Spec and actual SVG roster during planning. Continuous Executor reuses that context; fresh Executor reads the Design Spec once and each selected complete SVG only before first use or after its SHA changes. |
| `templates/template_execution_manifest.json` (`v1`) + `templates/template_execution/*.text-slots.json` (`v2-min`) | Derived template index | Compact prototype/source-import summary plus per-prototype text-slot diagnostics; the sidecar integrity hash is tool-only | Materialization may publish these deterministic records, but page-context does not inject or require them and models do not read them during page authoring. The complete prototype SVG is the sole visual/template authority; never author from either JSON artifact. |
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
| `validation/svg_quality_report.json` | Quality provenance | Final SVG gate split into blocking / introduced / inherited / source-import categories, bound to the checked SVG bytes by SHA-256 | `svg_quality_checker.py --stage final --json` writes before export; the exporter reads it programmatically and links it only when the export-source fingerprint matches. Agents use successful command output and do not load the full JSON except for targeted failure/audit reads. |
| `validation/<output_stem>.report.json` | Published-package audit | PPTX package/resource postflight status, part counts, and quality-gate linkage | Step 7.3 writes after the PPTX passes package validation and emits a compact `[POSTFLIGHT]` receipt. Agents use the receipt on routine success and keep the full JSON cold unless targeted failure/audit evidence is required. |
| `exports/` | Delivery artifacts | Native DrawingML PPTX and explicit native-object/narration variants | Step 7.3 writes only final deliverables from `svg_output/`. |
| `backup/<timestamp>/svg_output/` | Frozen author-source archive | Re-export source without re-running LLM | `svg_to_pptx.py` writes a snapshot during export |
| `animations.json` | Optional animation config | Object-level animation sidecar | Created only by explicit animation workflow/request |

---

## 2. Ownership Invariants

| Invariant | Rule |
|---|---|
| Content values | Main pipeline text, tables, chart values, and SmartArt node wording come from content-type files in `sources/` (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`), not from `slide_library.json`. |
| Sources read policy | In `sources/`, read content-type files (`.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml`) and judge by content — a `.json` / `.csv` may be core content or just data. Exclude known sidecars: `*.conversion_profile.json` and `*_files/image_manifest.json`. `analysis/` facts (`source_profile.json`, `<stem>.slide_library.json`) are read per Step 4 / direct-PPTX workflow, not in the `sources/` content scan. |
| PPTX structure | `slide_library.json` owns native geometry, slot facts, and SmartArt layout/relationships for direct PPTX workflows. |
| Design contract | Final confirmation → audited `design_spec.md` → projected `spec_lock.md`. Executor may apply projected `Template Application` prose to visible template content, but never infer lock values from it. On divergence, repair the lock from the Design Spec unless the Design Spec itself fails confirmation fidelity. |
| Flat packaging authority | Free-design, brand-only, and `template_reuse_scope: style` declare `pptx_structure.mode: flat` and omit `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts`. `svg_output/` owns the complete Slide-local visual design without root Master/Layout identity, fixed-layer ownership, or placeholder metadata. Export materializes one clean project-owned Master plus one Blank Layout, applies the locked theme defaults, removes stock content placeholders/Layout inventory, and retains only the standard date/footer/slide-number capability hooks. |
| Template structure authority | `template_reuse_scope: mirror|layout` uses `page_layouts` for each page's authoring-input prototype. `pptx_masters` / `pptx_layouts` own the unique reusable output definitions, while `page_pptx_layouts` owns page assignment. Strict keeps the prototype contract; adaptive may create a new Layout definition during page authoring and updates its assignment immediately. Mirror additionally preserves literal visuals/text topology; layout allows project-controlled reflow/re-skinning. Unused definitions may register without a published Slide. Templates validate provenance but never add missing visible page objects during export. |
| Fact classes | External facts resolve through `sources/*.facts.json`; invented demo KPIs/targets/internal ratios are labeled `scenario` in `design_spec.md §IX` and visibly in the page. Never promote scenario data into the external fact registry. |
| Imported-template authoring | Editable SVGs under `authoring-svg/` own create-template edits, `authoring_summary.json` owns model-facing orientation, and `authoring_manifest.json` owns tool-only source-object identity. Lossless `svg/` owns immutable native payload and fallback evidence; optional `svg-flat/` owns only complete-page verification. Materialized `templates/*.svg` own the validated deliverable contract and contain no IR-only source refs. |
| Legacy template input | Old unmapped/distilled/preserve structured projects and incomplete template packages are not migrated in place. [`create-template`](../workflows/create-template.md) authors a new current workspace: original PPTX Type A may preserve existing native topology in mirror; legacy SVG-only Type B is visual reference for `standard` / `fidelity`. An intentional free-design or brand-only `flat` project is already current. The exporter does not migrate or visually cluster legacy structure. |
| Image facts | `images/` is live state; `analysis/image_analysis.csv` is a regenerated view, not a durable cache. |
| SVG source | `svg_output/` is the only author source for generated pages. |
| Page-design closure | On SVG-authoring routes, every visible exported-slide object exists in the corresponding page SVG or an explicitly referenced visual asset. |
| Package-behavior separation | Speaker notes, animations, transitions, narration, and direct native-PPTX workflows keep their owning artifacts; do not force them into SVG metadata. |
| Post-processed SVG | `svg_final/` is disposable, must be rebuilt in Step 7.2, and serves only as a self-contained visual preview / manually insertable SVG picture. |
| Export source | The only supported generated-PPTX route reads `svg_output/` through the project SVG-to-DrawingML converter. A diagnostic `-s final` override does not change ownership or create a supported release route. |
| Shape-conversion boundary | PowerPoint's manual Convert-to-Shape operation on `svg_final/` is outside the project compatibility contract. |
| Confirmation | Final `confirm_ui/result.json` or chat confirmation overrides recommendations and is the mandatory input contract for `design_spec.md`; `spec_lock.md` is derived only after that Design Spec passes confirmation-fidelity review. |

**Forbidden - mixed ownership**: Do not copy chart values from Markdown into `analysis/` by hand, do not edit `svg_final/` as the source of a fix, do not edit imported lossless SVGs instead of their authoring IR, and do not treat `design_spec.md` prose as a replacement for `spec_lock.md`.

---

## 3. Regeneration Rules

| Derived artifact | Regenerate from | Command / owner |
|---|---|---|
| `analysis/image_analysis.csv` | Current `images/` | `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` |
| `<import_workspace>/authoring-svg/authoring_summary.json` | Current authoring SVGs plus tool-only manifest roster | `python3 ${SKILL_DIR}/scripts/svg_authoring_view.py <import_workspace>/authoring-svg --refresh-summary`; in-place vector/picture extraction refreshes it automatically |
| `notes/slide_*.md` | `notes/total.md` | `python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>` |
| `svg_final/` | `svg_output/` plus project assets | `python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>` |
| `validation/svg_quality_report.json` | `svg_output/`, locks, template provenance | `python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --stage final --json` |
| Native PPTX + `validation/<output_stem>.report.json` | `svg_output/` plus notes/assets and final quality report | `python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>` |

**Default - regenerate derived views**: When a source artifact changes, regenerate the derived artifact at the owning step instead of patching the derived file directly.
