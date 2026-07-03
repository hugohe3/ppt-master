---
name: ppt-master
description: >
  AI-driven multi-format SVG content generation system. Converts source documents
  (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through
  multi-role collaboration. Use when user asks to "create PPT", "make presentation",
  "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".
---

# PPT Master Skill

> AI-driven multi-format SVG content generation system. Converts source documents into high-quality SVG pages through multi-role collaboration and exports to PPTX.

**Core Pipeline**: `Source Document → Create Project → [Template] → Strategist → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export`

> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> **This workflow is a strict serial pipeline. The following rules have the highest priority — violating any one of them constitutes execution failure:**
>
> 1. **SERIAL EXECUTION** — Steps MUST be executed in order; the output of each step is the input for the next. Non-BLOCKING adjacent steps may proceed continuously once prerequisites are met, without waiting for the user to say "continue"
> 2. **BLOCKING = HARD STOP** — Steps marked ⛔ BLOCKING require a full stop; the AI MUST wait for an explicit user response before proceeding and MUST NOT make any decisions on behalf of the user
> 3. **NO CROSS-PHASE BUNDLING** — Cross-phase bundling is FORBIDDEN. (Note: the Eight Confirmations in Step 4 are ⛔ BLOCKING — the AI MUST present recommendations and wait for explicit user confirmation before proceeding. Once the user confirms, all subsequent non-BLOCKING steps — design spec output, SVG generation, speaker notes, and post-processing — may proceed automatically without further user confirmation)
> 4. **GATE BEFORE ENTRY** — Each Step has prerequisites (🚧 GATE) listed at the top; these MUST be verified before starting that Step
> 5. **NO SPECULATIVE EXECUTION** — "Pre-preparing" content for subsequent Steps is FORBIDDEN (e.g., writing SVG code during the Strategist phase)
> 6. **NO SUB-AGENT SVG GENERATION** — Executor Step 6 SVG generation is context-dependent and MUST be completed by the current main agent end-to-end. Delegating page SVG generation to sub-agents is FORBIDDEN
> 7. **SEQUENTIAL PAGE GENERATION ONLY** — In Executor Step 6, after the global design context is confirmed, SVG pages MUST be generated sequentially page by page in one continuous pass. Grouped page batches (for example, 5 pages at a time) are FORBIDDEN
> 8. **SPEC_LOCK RE-READ PER PAGE** — Before generating each SVG page, Executor MUST `read_file <project_path>/spec_lock.md`. All colors / fonts / icons / images MUST come from this file — no values from memory or invented on the fly. Executor MUST also look up the current page's `page_rhythm` (`anchor` / `dense` / `breathing`), `page_layouts` (which template SVG to inherit, if any), and `page_charts` (which chart template to adapt, if any). Empty / absent entries are intentional Strategist signals — see executor-base.md §2.1. This rule exists to resist context-compression drift on long decks and to break the uniform "every page is a card grid" default
> 9. **SVG MUST BE HAND-WRITTEN, NOT SCRIPT-GENERATED** — Every SVG page is written by the main agent directly, one page at a time (see rules 6 and 7). Writing or running a Python / Node / shell script that produces the SVG files in batch — looping over pages, templating from data, or emitting them via a generator — is FORBIDDEN, including under "save tokens", "quick draft", or "user is in a hurry" pretexts. The script-generation path was tried on a feature branch and abandoned: cross-page visual consistency depends on per-page authoring with full upstream context, which a generator script cannot reproduce
> 10. **FOLLOW DETERMINISTIC ROUTING RULES** — Do not add blocking routing questions when this skill defines a route. If the user request violates a route precondition, state the required prerequisite and stop that route instead of asking the user to choose around the rule. Ordinary finite options, stylistic preferences, and recoverable details are surfaced with a recommended value plus alternatives at the next existing confirmation gate.

> [!IMPORTANT]
> ## 🌐 Language & Communication Rule
>
> - **Response language**: match the user's input and source materials. Explicit user override (e.g., "请用英文回答") takes precedence.
> - **User-facing option labels**: when presenting confirmations, brief proposals, choices, or finite option sets, use the user's language for labels and explanations. English enum IDs / file fields may appear in parentheses for precision, but never rely on English-only labels such as `deck`, `layout`, `mirror`, or `fidelity` without a localized explanation.
> - **Template format**: `design_spec.md` MUST follow its original English template structure (section headings, field names) regardless of conversation language. Content values may be in the user's language.

> [!IMPORTANT]
> ## 🔌 Compatibility With Generic Coding Skills
>
> - `ppt-master` is a repository-specific workflow, not a general application scaffold
> - Do NOT create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default
> - On conflict with a generic coding skill, follow this skill unless the user explicitly says otherwise

## Rule Strength Labels

| Label | Meaning |
|---|---|
| `MUST` | Required behavior; violation is workflow failure |
| `MUST NOT` | Forbidden behavior |
| `DEFAULT` | Used when the user has not specified otherwise |
| `OPTIONAL` | Run only when explicitly triggered or when the route says so |
| `FALLBACK` | Recovery path after the primary path fails |
| `GATE` | Required checkpoint before entering the next step |

## Cross-Cutting Authorities

| Concern | Authority | Contract |
|---|---|---|
| Main pipeline sequencing | This `SKILL.md` | Owns Step 1-7 order, gates, role switching, and mandatory commands |
| Route selection | [`workflows/routing.md`](workflows/routing.md) | Owns deterministic route choice before the main pipeline or a standalone workflow |
| Workflow registry | [`workflows/index.md`](workflows/index.md) | Owns standalone workflow trigger/precondition/output inventory |
| Artifact ownership | [`references/artifact-ownership.md`](references/artifact-ownership.md) | Owns fact channels, source/derived artifact boundaries, and regeneration rules |
| Failure recovery | [`workflows/failure-recovery.md`](workflows/failure-recovery.md) | Owns stop/continue decisions for common failures |
| Confirm UI details | [`scripts/docs/confirm_ui.md`](scripts/docs/confirm_ui.md) | Owns schema, launcher behavior, port strategy, and chat fallback details |

## Main Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `${SKILL_DIR}/scripts/source_to_md.py` | Unified source-to-Markdown dispatcher — default Step 1 entry for explicit file(s) or URL(s) |
| `${SKILL_DIR}/scripts/pptx_intake.py` | Standard PPTX intake enrichment — canvas / identity / slide geometry / tables / native chart data |
| `${SKILL_DIR}/scripts/project_manager.py` | Project init / validate / manage |
| `${SKILL_DIR}/scripts/icon_sync.py` | Copy chosen library icons into `<project>/icons/` at selection time; missing names reported + non-zero (re-pick gate) |
| `${SKILL_DIR}/scripts/analyze_images.py` | Image analysis |
| `${SKILL_DIR}/scripts/latex_render.py` | LaTeX formula rendering (manifest-driven PNG assets) |
| `${SKILL_DIR}/scripts/image_gen.py` | AI image generation (multi-provider) |
| `${SKILL_DIR}/scripts/slice_images.py` | Slice one AI illustration sheet into individual spot-illustration elements |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG quality check |
| `${SKILL_DIR}/scripts/total_md_split.py` | Speaker notes splitting |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG post-processing (unified entry) |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | Export to PPTX |
| `${SKILL_DIR}/scripts/native_enhance_pptx.py` | Existing PPTX enhancement project init / validation / direct OOXML patch export |
| `${SKILL_DIR}/scripts/native_narration_pptx.py` | Backward-compatible entrypoint for existing PPTX notes / narration enhancement |
| `${SKILL_DIR}/scripts/update_spec.py` | Propagate a `spec_lock.md` color / font_family change across all generated SVGs |

For complete tool documentation, see `${SKILL_DIR}/scripts/README.md`.

> **Windows note**: if a `python3 ...` command fails (common on python.org installs, which provide `python.exe` but not `python3.exe`), rerun the same command with `python` instead.

## Template Index

| Index | Path | Purpose |
|-------|------|---------|
| Layout templates | `${SKILL_DIR}/templates/layouts/layouts_index.json` | Query available page layout templates |
| Brand presets | `${SKILL_DIR}/templates/brands/brands_index.json` | Query available brand identity presets (color / typography / logo / voice) |
| Visualization templates | `${SKILL_DIR}/templates/charts/charts_index.json` | Query available visualization SVG templates (charts, infographics, diagrams, frameworks) |
| Icon library | `${SKILL_DIR}/templates/icons/` | See `${SKILL_DIR}/templates/icons/README.md`; search icons on demand with `ls templates/icons/<library>/ \| grep <keyword>` |

## Standalone Workflows

**Route authority**: Use [`workflows/routing.md`](workflows/routing.md) before entering the main pipeline or any standalone workflow.

**Registry**: Use [`workflows/index.md`](workflows/index.md) for the complete workflow list, triggers, preconditions, exclusions, outputs, and blocking points.

### PPTX Route Boundary

| User intent | Route |
|---|---|
| Raw PPTX template plus new material/topic, generate a PPTX | [`template-fill-pptx`](workflows/template-fill-pptx.md) |
| Existing PPTX, preserve page count/order and slide wording 1:1, improve layout | [`beautify-pptx`](workflows/beautify-pptx.md) |
| Existing PPTX as source material, rethink outline or change page count/order | Main pipeline via `source_to_md.py` plus PPTX intake |
| Build a reusable template package from a PPTX/design reference | [`create-template`](workflows/create-template.md), then return with the generated template directory path |
| Finished PPTX, keep content/layout stable and add notes/audio/timing/transitions | [`native-enhance-pptx`](workflows/native-enhance-pptx.md) |

**MUST**: Raw `.pptx` template plus "generate PPTX" routes to `template-fill-pptx` by default. The SVG generation route consumes only an explicit template directory path that already contains a valid template `design_spec.md`.

**MUST**: Beautify is strictly 1:1. Any split, merge, drop, reorder, or page-count change routes to the main pipeline.

**FALLBACK**: Ambiguous requests such as "make this PPT more professional" require exactly one discriminator question: preserve original page count/order and slide wording, or treat the deck as source material and restructure it?

---

## Workflow

### Step 1: Source Content Processing

🚧 **GATE**: User has provided source material (PDF / DOCX / EPUB / URL / Markdown file / text description / conversation content — any form is acceptable).

> **No source content?** When the user supplies only a topic name or requirements without any file or substantive description, run the [`topic-research`](workflows/topic-research.md) workflow first, then return here with its products as input.

When the user provides non-Markdown content, convert immediately through the
unified dispatcher. It preserves the backend converters' existing behavior,
routes by source type, and writes the standard Markdown plus conversion profile.

| User Provides | Action |
|---------------|--------|
| PDF / DOCX / Office document / XLSX / XLSM / PPTX / EPUB / HTML / LaTeX / RST / web URL | `python3 ${SKILL_DIR}/scripts/source_to_md.py <file_or_URL_or_dir> [<file_or_URL_or_dir> ...]` |
| CSV / TSV | Read directly as plain-text table source |
| Markdown | Read directly |

For PPTX sources, Step 1 converts the deck to Markdown content; after Step 2
`import-sources`, standard PPTX intake is also written to `<project>/analysis/`.
Use `source_to_md.py -t <type>` only when extension detection is ambiguous.
Default local conversion writes Markdown/profile outputs beside each source file.
Use `-o` only when a specific output file/directory is required; with multiple
inputs or directory inputs, `-o` is an output directory. Backend converter details are documented in
[`scripts/docs/conversion.md`](scripts/docs/conversion.md).

> **Office vector assets (EMF/WMF) from DOCX/PPTX sources**:
> Source conversion extracts embedded Office vector images (.emf/.wmf)
> alongside bitmap images when the source format exposes them. After `import-sources`, these land in `images/`
> together with `image_manifest.json` and are first-class assets in §VIII Image Resource List.
>
> **Do NOT convert EMF/WMF to PNG.** The PPT Master pipeline preserves them as external
> references (`finalize_svg.py` skips them) and `svg_to_pptx.py` embeds them as
> PPTX-native media via `image/x-emf` / `image/x-wmf` MIME — PowerPoint renders them at full vector fidelity.
> Converting via LibreOffice/Inkscape introduces CJK font substitution drift and
> rasterization loss; the original EMF/WMF is always higher fidelity than the converted PNG.
>
> Browser-based live preview cannot render EMF (will show blank) — this is expected;
> the PPTX output is the source of truth.

**✅ Checkpoint — Confirm source content is ready, proceed to Step 2.**

---

### Step 2: Project Initialization

🚧 **GATE**: Step 1 complete; source content is ready (Markdown file, user-provided text, or requirements described in conversation are all valid).

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

Format options must be named with concrete dimensions. Default: `ppt169` = `1280x720`, `viewBox="0 0 1280 720"`. Other examples: `ppt43` = `1024x768`, `story` = `1080x1920`, `banner` = `1920x1080`. For the full format list, see `references/canvas-formats.md`.

Import source content (choose based on the situation):

| Situation | Action |
|-----------|--------|
| Has source files (PDF/MD/etc.) | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files_or_dirs...> --move` |
| User provided text directly in conversation | No import needed — content is already in conversation context; subsequent steps can reference it directly |

For PPTX sources, `import-sources` automatically runs the standard intake enrichment:

```bash
python3 ${SKILL_DIR}/scripts/pptx_intake.py <project_path>/sources/<source.pptx> -o <project_path>/analysis
```

For each PPTX it writes `<stem>.identity.json` (canvas, theme palette/fonts, observed usage) and `<stem>.slide_library.json` (text slots, geometry, native tables, native chart caches), and merges that deck's Strategist-facing digest into the single multi-deck index `analysis/source_profile.json` (`decks[]`, one self-contained entry per source deck, with prefixed artifact pointers). In the main generation path these are source facts and recommendation candidates, not replica constraints; beautify and template-fill workflows decide separately which fields become locked constraints.

Multi-deck: several PPTX files may be imported into one main-pipeline project — each gets its own `<stem>.*` artifacts and a deck entry in `source_profile.json`. `source_profile.json` stays the single must-read index (one entry for a one-deck project, several for a combined-source project). Stems must be distinct; re-importing the same stem replaces that deck's entry. The beautify / template-fill workflows remain single-deck (1:1 to one chosen source deck) and read that deck's `<stem>.*` artifacts.

> ⚠️ **MUST use `--move`** (not copy): all source files — Step 1's generated Markdown, original PDFs / MDs / images — go into `sources/` via `import-sources --move`. If Step 1 wrote Markdown beside the original sources, pass that source path/directory once. If Step 1 used `-o` to write Markdown elsewhere, pass both the original source path(s)/directory and the Markdown output path(s)/directory. After execution they no longer exist at the original location. Intermediate artifacts (e.g., `_files/`) are handled automatically.

**✅ Checkpoint — Confirm project structure created successfully, `sources/` contains all source files, converted materials are ready. Proceed to Step 3.**

---

### Step 3: Template Option

🚧 **GATE**: Step 2 complete; project directory structure is ready.

**Default — free design.** Proceed directly to Step 4. Do NOT query any `*_index.json` unless triggered. Do NOT ask the user. Do NOT proactively suggest, hint at, or fuzzy-match any template based on content, slug-like words, or vague style descriptions.

**Hard boundary — raw PPTX template references are not Step 3 templates.** PPTX-as-source remains valid in Step 1 / Step 2, and raw PPTX template + generated PPTX routes to `template-fill`. But if the user wants the SVG/template-based generation route from that PPTX, stop before Step 3. The user must first run [`workflows/create-template.md`](workflows/create-template.md), then return with the generated template directory path. Step 3 only consumes an explicit template directory that already contains `design_spec.md` with `kind: brand` / `kind: layout` / `kind: deck`.

Do **not** reinterpret this boundary as 1:1 redesign or free SVG generation. Use `template-fill` for raw PPTX template + generated PPTX requests; use `beautify` only when the source deck's page count, order, and wording are preserved.

**Template flow triggers ONLY on explicit directory paths** supplied by the user in their initial message. The trigger rule is mechanical, not interpretive:

| User input contains | Step 3 action |
|---|---|
| One or more explicit template directory paths (each resolves to a directory containing `design_spec.md` with `kind: brand` / `kind: layout` / `kind: deck` in its YAML frontmatter) | Read each spec's `kind`, dispatch per the kind matrix below, fuse if multiple |
| Anything else — bare template names ("用 academic_defense"), style descriptions ("麦肯锡风格"), brand mentions ("招商银行风格"), vague intent ("想用个模板"), or silence | Skip Step 3, free design |

There is no slug matching, no name lookup, no fuzzy resolution. A name without a path does not trigger — the user must give a path the AI can `cd` into.

> Style descriptions ("麦肯锡风格" / "Keynote 风" / "极简风" / etc.) never trigger Step 3. They flow into Strategist's Eight Confirmations as a style brief (color / typography / tone in confirmations e–g).

> Bare names ("academic_defense", "招商银行", "anthropic") do NOT trigger Step 3 even if a matching directory exists in the library. The user must give a path. AI must not "helpfully" resolve a name to a path.

> "What templates exist?" is out-of-band Q&A — answer by listing entries from `brands_index.json` / `layouts_index.json` / `decks_index.json` together with their paths. Listing alone does not advance the pipeline; the user must send a path back to trigger Step 3.

> To create a new layout or deck, read [`workflows/create-template.md`](workflows/create-template.md). To create a new brand, read [`workflows/create-brand.md`](workflows/create-brand.md).

#### Three template kinds

The architecture has three independent reference bundles. Full schema in [`docs/zh/templates-architecture.md`](../../docs/zh/templates-architecture.md). Summary:

| Kind | Physical dir | Contains | Frontmatter |
|---|---|---|---|
| **brand** | `templates/brands/<id>/` | identity-only segment: color / typography / logo / voice / icon style | `kind: brand` |
| **layout** | `templates/layouts/<id>/` | structure-only segment: canvas / page structure / page types / SVG roster | `kind: layout` |
| **deck** | `templates/decks/<id>/` | full replica: identity + structure + middle (template overview) segments | `kind: deck` |

**Segment ownership** (governs fusion override priority):

| Segment | Sections | Owner kind on fusion |
|---|---|---|
| Identity | Color Scheme / Typography / Logo / Voice & Tone / Icon Style | brand |
| Structure | Canvas / Page Structure / Page Types / SVG Roster | layout |
| Middle | Template Overview (use cases / design intent) | deck (no other kind writes this) |

#### Single-path dispatch

| User path's `kind` | Step 3 action |
|---|---|
| `kind: brand` | `design_spec.md` + non-image assets → `<project>/templates/`; logo / illustration / icon **bitmaps** → `<project>/images/`. Strategist locks identity segment as truth; structure stays free. |
| `kind: layout` | `design_spec.md` + SVG roster → `<project>/templates/`; any **bitmap** assets → `<project>/images/`. Strategist locks structure; identity decided in Eight Confirmations e–g. |
| `kind: deck` | `design_spec.md` + template SVGs → `<project>/templates/`; logos / backgrounds / other **bitmaps** → `<project>/images/`. Strategist locks all segments; Eight Confirmations narrows to deck-content fields (audience / page count / outline / tone tweaks). |

```bash
TEMPLATE_DIR=<user-supplied path>
# Bitmaps join the project's single runtime image pool (images/, referenced as
# ../images/); the spec + template SVGs + other non-image assets stay in
# templates/ as design reference the Strategist/Executor read but never render.
cp -r ${TEMPLATE_DIR}/* <project_path>/templates/
find <project_path>/templates -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.gif' -o -iname '*.webp' -o -iname '*.bmp' \) -exec mv {} <project_path>/images/ \;
```

The same split applies to all three kinds — bitmaps always land in `images/`, the rest in `templates/`. The spec's `kind` field tells Strategist how to read the `templates/` side; downstream code doesn't distinguish. (Template SVGs in `templates/` are reference material only — the rendered pages live in `svg_output/` and reference images via `../images/`.)

#### Multi-path fusion

When the user gives two or more paths of **different kinds**, Step 3 fuses them into a single `<project>/templates/design_spec.md`. **Default granularity is segment-level integer replacement** — entire identity / structure / middle segments are taken from the highest-priority source for that segment, no implicit field-level mixing.

Override priority by segment:

| Combination | Identity from | Structure from | Middle from |
|---|---|---|---|
| brand only | brand | (free design) | (none) |
| layout only | (free design) | layout | (none) |
| deck only | deck | deck | deck |
| brand + layout | brand | layout | (none) |
| brand + deck | brand (overrides deck) | deck | deck |
| layout + deck | deck | layout (overrides deck) | deck |
| brand + layout + deck | brand | layout | deck |

Field-level micro-adjustment (e.g. "use anthropic brand but primary changed to #FF0000") is **not** part of Step 3 fusion — it flows into Strategist Eight Confirmations e–g as a normal user request.

#### Same-kind multiple paths — conflict resolution

When the user gives two paths of the **same kind** (e.g. `brands/anthropic` + `brands/google`), Step 3 surfaces a conflict prompt before fusing — like resolving a git merge conflict:

```
AI: 你给了两个 brand，检测到段级冲突：
    - Color Scheme（Anthropic 橙红 vs Google 多色）
    - Typography（Styrene/AnthropicSans vs GoogleSans/Roboto）
    - Logo（Anthropic 标 vs Google 标）
    - Voice & Tone（restrained vs friendly）
    - Icon Style（stroke vs filled）

    要 (a) 全部按 Anthropic / (b) 全部按 Google / (c) 逐段挑？
```

Rules:
- Default: no implicit ordering — every cross-source segment difference is reported as a conflict
- Only when the user picks `(c)` does AI walk through each segment one by one
- Field-level conflicts are out of scope — segment-level only
- Three or more same-kind paths are not supported — ask the user to converge to at most two

#### Fused spec provenance

When fusion happens (any multi-path case), the resulting `<project>/templates/design_spec.md` carries a provenance block immediately under its H1:

```markdown
> **Fused from:**
> - deck: `templates/decks/招商银行/` （base）
> - brand: `templates/brands/anthropic/` （identity override）
> - layout: `templates/layouts/academic_defense/` （structure override）
> - conflicts resolved: Color Scheme from anthropic（user picked a）
```

Single-path Step 3 does **not** add provenance (the source is self-evident from the copied files).

**✅ Checkpoint — Default path proceeds to Step 4 without user interaction. If the user supplied one or more explicit template paths, those have been dispatched (or fused) into `<project_path>/templates/` before advancing.**

---

### Step 4: Strategist Phase (MANDATORY — cannot be skipped)

🚧 **GATE**: Step 3 complete; default free-design path taken, or (if triggered) template files copied into the project.

First, read the role definition:
```
Read references/strategist.md
```

> ⚠️ **Mandatory gate**: before writing `design_spec.md`, Strategist MUST `read_file templates/design_spec_reference.md` and follow its full I–XI section structure. See `strategist.md` Section 1.

**Artifact ownership**: fact-channel and source/derived artifact boundaries are defined in [`references/artifact-ownership.md`](references/artifact-ownership.md). This Step uses those ownership rules; it does not redefine them.

**`<project_path>/analysis/` is the project's intermediate-analysis folder: the canonical home for machine-extracted source/asset facts — the PPTX intake bundle (`source_profile.json` index + per-deck `<stem>.identity.json` / `<stem>.slide_library.json`) and `image_analysis.csv`. It holds facts, not design contracts — `design_spec.md` / `spec_lock.md` stay at the project root.** The MUST-read contract covers only the **compact structured data files (`.json` / `.csv`)**; other artifacts that may live under `analysis/` (e.g. a beautify `source_svg_import/` vector reference package) are NOT bulk-read — they are read selectively only when a specific workflow step calls for them. Before the Eight Confirmations, Strategist MUST read the auto-extracted fact files already in `analysis/` — currently `source_profile.json` (PPTX intake), when present. This file is the multi-deck index: read it once for the `decks[]` digests (canvas / chart / table entries per source deck), then open a specific deck's `<stem>.identity.json` / `<stem>.slide_library.json` only if you need its full raw facts. Use these entries as **factual source context** (format default + content facts); when several decks are present, synthesize across all of them. The source's **palette / typography / visual identity are a reference, not a constraint**: the main pipeline may inherit them where they fit the content and the confirmed style, or design fresh where they don't — the Strategist's judgment, never an obligation to either keep or discard. (Template-fill preserves the native source design by editing cloned slides directly; beautify defaults to the source identity but still follows the confirmed values; the main pipeline treats source identity as reference only and defaults to fresh design.) (`image_analysis.csv` lands later, at the image-analysis step below, and is the authoritative regenerated image-fact view there — re-derived from the live `images/` folder, not a durable store.)

**Channel ownership — read each fact once from its owning channel.** In the main pipeline the **content contract is the content-type files in `sources/`** — primarily `<stem>.md`, but also any user-supplied content the import archived there: `.md` / `.markdown` / `.txt` / `.csv` / `.tsv` / `.json` / `.jsonl` / `.yaml` / `.yml` (a `metrics.json` or `data.csv` may carry core content — judge by what the file holds). Text, tables, and chart data values come from these (`ppt_to_md` now transcribes native chart data into Markdown tables). **Do NOT read pipeline sidecars in `sources/` as content**: `*.conversion_profile.json` (conversion audit) and `*_files/image_manifest.json` (asset index) are process metadata — open them only to audit a conversion or resolve assets, never as slide content. Converted-source originals archived in `sources/` (`.pdf` / `.pptx` / `.docx` / `.xlsx` / `.html` / `.epub` / `.tex` / `.rst` / `.ipynb` / `.typ`, etc.) are read via their converted `<stem>.md`, not scanned directly in the main pipeline. The `analysis/` chart / table entries are a **structural digest** for outline decisions (which slides carried charts, type, series names) — not a second copy of the values; do NOT also pull chart values from `<stem>.slide_library.json` in the main pipeline. The `<stem>.slide_library.json` full structured data is owned by the direct-PPTX workflows: template-fill uses it as the native fill contract; beautify uses it for native chart / table data while keeping slide text from the Markdown.

**Eight Confirmations** (full template: `templates/design_spec_reference.md`):

⛔ **BLOCKING**: present the Eight Confirmations and **wait for explicit user confirmation or modification** before outputting Design Specification & Content Outline. This is the single core confirmation gate — once the final confirmation lands, all subsequent steps proceed automatically. The default Confirm UI delivers the gate in **two tiers** (anchors → re-derive → realization; see below); the chat fallback mirrors the same two steps.

1. Canvas format
2. Page count range
3. Target audience
4. Style objective
5. Color scheme
6. Icon usage approach
7. Typography plan, including formula rendering policy
8. Image usage approach

**Confirm UI Auto-Launch (Mandatory — default visual confirmation surface)**: by default the Eight Confirmations are presented through an interactive local page in **two tiers within one browser session** — Tier 1 confirms the *anchors*; the AI then re-derives the realization layer from the **user's actual** anchors; Tier 2 confirms that layer. Color swatches, live font previews, candidate picks; the chat path is the always-valid fallback. [`scripts/docs/confirm_ui.md`](scripts/docs/confirm_ui.md) owns the schema, server lifecycle, port strategy, and fallback details; this section keeps the orchestration contract. The split:

| Tier | Confirms | Driven by |
|---|---|---|
| **1 — anchors** | canvas · audience + core message + `content_divergence` + `delivery_purpose` *(PPT only — omitted on non-PPT canvases)* (all §c key info) · `mode` + `visual_style` | the source + user intent |
| **2 — realization** (re-derived from Tier 1) | page count · color · typography (font + size) · icons · formula policy · image usage + generated-image style · generation mode · refine-spec toggle | the confirmed Tier 1 |

> **Why two tiers.** Every realization field is anchored by the same few choices (`visual_style` anchors color / icon / typography / image; `delivery_purpose` sets the body size, page density, **and** the page-count recommendation). Confirming anchors first, then re-deriving, means Tier 2's candidates fit the user's *real* anchors instead of your originals — the coherence reconciliation below is done by construction on this path. Page count is a **derived** field (content volume × `delivery_purpose`), which is why it lives in Tier 2, not up front.

Steps:

> ⛔ **Steps 2 → 3 → 4 are ONE uninterrupted run — do NOT yield to the user mid-flow.** When the tier-1 `--wait` (step 2) returns, the AI **immediately and autonomously** continues to step 3 (re-derive + write Tier 2) and step 4 (`--wait-only`) in the **same turn**: do **not** summarize, ask a question, report progress, or end the turn in between. The browser is sitting on a "deriving…" spinner polling for the Tier 2 you must write next — stopping here strands the page and the user must prod you in chat to finish (a bug, not the intended flow). **The tier-1 confirmation is an intermediate machine handoff, not a stopping point.** The single ⛔ BLOCKING wait is the **final** confirmation at the end of step 4. (Chat-fallback path — only when the page never opened — is the exception: there you do present each tier in chat and wait for a reply.)

1. **Write Tier 1** to `<project_path>/confirm_ui/recommendations.json` with `"tier": 1` and only the anchor fields. Enumerable anchors (`canvas` / `mode` / `visual_style` / `delivery_purpose`) name a recommended canonical `id` in a `recommend` block (the page lists common options from `confirm_ui/static/catalogs.json`); `visual_style` also carries the ≥3-style `visual_style_spectrum` (safe / shifted / bold — same hard rule as h.5). `audience` and `content_divergence` are plain `{ "value": "<free text>" }`. `content_divergence` is the **free-text** field shown under audience in §c — how closely to follow the source vs how freely to reshape it (blank = balanced; facts stay sourced at every level); it is consumed by Strategist when authoring `§IX`, recorded in `design_spec.md §I`, carries no page-count coupling, and is **not** written to `spec_lock.md`. Set `lang` to the page language (`zh` / `en` / `ja`); visible text matches `lang`, or provide multilingual `name_zh` / `name_en` / `name_ja` + `note_zh` / `note_en` / `note_ja` — when the user's language is Japanese, set `lang: "ja"` and always include the `_ja` variants (labels resolve in the page language first — a `ja` page falls back ja → en → zh, so missing `_ja` labels silently render in English; zh/en pages keep their zh↔en fallback and only try `_ja` last).
2. **Launch + wait for Tier 1.** Background launch; the parent returns when the page writes the tier-1 `result.json`. **Long tool timeout — 600000 ms** (the `--wait` ≈590 s budget):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --daemon --wait
   ```
   Page opens at `http://localhost:5050` — the **same port as the Step 6 live preview** (they never run at once: this page shuts down at the end of Step 4). If 5050 is held, the launcher **auto-advances** (5051, …) — read the actual URL from the launch log and report it. The page does **not** close after Tier 1: it shows a "deriving…" state and polls for Tier 2. **Launch or wait failure is non-fatal**: if it fails or times out (flask missing, port blocked, no GUI / remote / web host), do **NOT** troubleshoot — **on any non-zero exit, re-check `result.json` once** (a fresh `status: tier1-confirmed`) before dropping to the chat fallback. **On success (exit 0 with a tier-1 result), do not pause or report — go straight to step 3 in the same turn.**
3. **Re-derive Tier 2 from the confirmed anchors, then write it — immediately, same turn (the page is polling for it).** Read the tier-1 `result.json` (`status: tier1-confirmed`). Using the user's **actual** confirmed anchors (not your originals), author the realization candidates and **overwrite** `recommendations.json` with `"tier": 2`: page count (content volume × `delivery_purpose`); color, typography, and generated-image style as **generative ≥3-candidate** fields (creative recommendations always offer real choice — same rule as h.5; fewer than 3 only on the honest-shortfall exception, with a stated reason; color: core `palette` with background/secondary_bg/primary/accent/secondary_accent/body_text; typography: CJK + Latin for `heading` and `body` with `css` preview stacks + `body_size` as the body baseline in **px** (every canvas) — **one fixed value per confirmed `delivery_purpose`** (`text` 20 / `balanced` 24 / `presentation` 32), not a range; each typography candidate must include topic-matched `sample_heading` / `sample_heading_latin` / `sample_body` / `sample_body_latin` preview text, never a fixed unrelated industry sample; images: `image_strategy.candidates` rendering × palette from h.5); enumerable `icons` / `formula_policy` / `generation_mode` (recommended `id`); `image_usage` as one or more source ids (`["ai"]`, `["ai","provided"]`, `["web","placeholder"]`, or `["none"]`; `none` is exclusive). If the recommendation involves several sources, keep the source list structured in `recommend.image_usage` and write the usage rationale / page-role guidance into `image_notes` (for example, "封面和章节页用 AI 主视觉，产品页优先用户素材，行业背景页可用网络参考"). Write `image_ai_path` only when `image_usage` includes `ai`. Spot-illustration lean is **not** a candidate field here: it derives from the locked `visual_style`'s illustration propensity and is expressed only in the recommendation rationale / `image_notes`, never as a new confirmation field. The still-open page polls, renders Tier 2, and preserves the user's Tier 1 picks. Closed fields (`image_ai_path`, `formula_policy`, `generation_mode`, `refine_spec`) stay finite; open fields (`icons`, typography custom text, image notes) expose free-text controls.
4. **Wait for the final confirmation** — attach to the already-running page, do **not** relaunch (same 600000 ms budget):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wait-only
   ```
   This is the ⛔ BLOCKING completion: returns when the page writes the final `result.json` (`status: confirmed`, `stage: final`, carrying all Tier 1 + Tier 2 fields). On a non-zero exit, re-check `result.json` once. Confirmed sizes are **already px** (the system is px-only — no pt anywhere, no conversion): write `result.json` `typography.body_size` / `sizes` into `design_spec.md` / `spec_lock.md` / SVG verbatim. `generation_mode: "split"` / `refine_spec: true` are explicit user choices.
5. **Close the confirm page (Mandatory cleanup — every path).** Shut the server down before leaving Step 4 so it cannot keep holding port 5050 (which Step 6 live preview reuses):
   ```bash
   python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --shutdown
   ```
   **Idempotent and required regardless of whether Confirm was clicked**: clicking the final Confirm already shuts the page down (then a no-op); the chat-fallback path leaves it running. Run it after reading the confirmation, before Step 5.

**Always also print each tier's recommendations + URL in chat** as the always-valid fallback. **The chat fallback is two-step too**: if the page never opens or a wait times out with no fresh result, present Tier 1 in chat → get confirmation → re-derive → present Tier 2 → get confirmation → take those values. Either path converges.

**Honoring the confirmation (result.json is authoritative — Mandatory)**: the confirmed values **override your own recommendations** when you write `design_spec.md` / `spec_lock.md`. A user who changed any field changed it on purpose. In particular, map `image_usage` to §VIII `Acquire Via` (its value names differ from §h options — translate). `image_usage` may be either a legacy single string or a Confirm UI multi-select array; for arrays, apply every selected source. `image_notes`, when present, is a user-authored image intent note that Strategist must honor while assigning per-page §VIII rows:

| `result.json.image_usage` | §VIII `Acquire Via` | h.5 + Step 5 generation |
|---|---|---|
| `ai` | `ai` rows | Run h.5 (lock rendering + palette); Step 5 generates |
| `web` | `web` rows | None |
| `provided` | **`user`** rows | None — never generate |
| `placeholder` | `placeholder` rows | None |
| `none` | no image rows (§h option A) | None |
| Legacy custom prose | Infer the intended rows from the prose | Run h.5 only if the prose includes AI |

When the confirmed `image_usage` does not include `ai` (and no legacy custom prose includes AI), do **NOT** run h.5, do **NOT** write `ai` rows, and do **NOT** generate images in Step 5 — regardless of what you recommended. `none` is exclusive: if confirmed, write no §VIII image rows. The same "confirmed value wins" rule applies to every field (color → §III, typography → §IV, etc.).

**Small spot illustrations are a Strategist judgment, not a confirmation field.** The user chooses image *source* through `image_usage`; whether the deck leans into decorative illustrations is anchored by the locked `visual_style`'s **illustration propensity** (`core` / `supportive` / `sparse`), expressed only in the `image_notes` rationale — never a new confirmation control. An explicit user request to use or skip illustrations overrides that default either way; `image_usage: none` still wins (write no illustration rows); and source still comes from `image_usage` — a `core` style does not silently generate AI spots when the user did not pick AI. They are ordinary §VIII image rows (`Type: Illustration` / `Illustration Sheet`) using normal `Acquire Via` values. If the plan needs ≥3 same-family AI spot illustrations, use the `ai` Illustration Sheet + `slice` workflow by default; do not generate one AI image per spot. Full rule + precedence: [`references/strategist.md`](references/strategist.md) §h. Use them on suitable pages and omit them where they would weaken clarity.

**Upstream override → re-derive untouched downstream (Mandatory — chat-fallback / single-pass path).** On the **two-tier page path this is already handled** (Step 3 re-derives Tier 2 from the user's actual anchors). It still applies whenever anchors and realization are confirmed **together** — the two-step chat fallback collapsed into one bundle, or a legacy single-pass `result.json`. "Confirmed value wins" governs each field's *own* value — never recompute a value the user set (a size, canvas, or palette they edited stays verbatim). But a single-pass `result.json` can carry a changed **anchor** beside downstream fields still holding your original — now incoherent — recommendation (e.g. switched to `dark-tech` while the light palette you proposed is untouched). Before writing the spec, reconcile: when the user changed an anchor, re-derive the downstream fields the user did **not** themselves edit so they realize the new anchor; fields the user pinned stay as confirmed.

| Anchor the user changed | Re-derive (only the downstream fields the user left at your recommendation) |
|---|---|
| `visual_style` (§d Layer 2 — anchors e–h) | color neutral tiers (§e), icon library / stroke (§f), typography character (§g), image rendering (§h.5) |
| `mode` (§d Layer 1) | outline structure + register (§IX) |
| `delivery_purpose` (§g) | body baseline + per-page density / rhythm (§6.1) |
| `audience` / core message (§c) | tone across e–h, outline emphasis (§IX) |
| `color` HEX (§e) | h.5 palette (re-filter for the new HEX) |

Reconcile **without a new blocking wait** — fold the coherent values into `design_spec.md` / `spec_lock.md` and state the adjustment in the §8 next-step handoff (e.g. "you switched to `dark-tech`; the light palette you had left no longer fit, so background / accent were re-derived — tell me if you wanted the original"). Canvas is the explicit exception: font sizes are deliberately **not** rescaled on a canvas change (see strategist §g).

**Opt-out**: if the user has said they don't want the page (e.g. "不要网页" / "just confirm in chat" / "纯聊天确认"), skip the launch entirely (step 2) and present the Eight Confirmations in chat as before — steps 1, 3, 4 still apply (recommendations summary in chat; wait; take chat values).

The page is a **confirmation surface only** — Strategist still authors every recommendation; the page never generates content.

**Mandatory — split-mode note** (not a ninth confirmation): after listing the eight confirmation details, you MUST append exactly one short line (rendered in the user's language, prefixed with 💡) about generation mode. Pick the variant by qualitative read of Phase A signals — recommended page count, source-material bulk, whether `topic-research` ran with substantial web-fetch accumulation:

| Signal read | Line content |
|---|---|
| Heavy (long page count / bulky sources / heavy web-fetch accumulation) | State estimated page count and large source size; recommend switching to [split mode](workflows/resume-execute.md) after Step 5 — stop this chat, open a fresh window and input `继续生成 projects/<project_name>` to enter Phase B (SVG generation + export); no response or "continue" = default continuous mode. |
| Normal (default) | State scale is moderate, default continuous mode generates in one go; if mid-way window switch is desired, input `继续生成 projects/<project_name>` after Step 5 to switch to [split mode](workflows/resume-execute.md). |

This line is required output every run — the user must always see the mode choice exists. Whether to act on it is the user's call. When the Confirm UI is used, this choice also appears as the in-page generation-mode toggle and is captured in `result.json` (`generation_mode`); the chat-summary fallback still prints this line.

**Mandatory — spec-refinement note** (not a ninth confirmation): after the split-mode line, you MUST append one short opt-in line (rendered in the user's language, prefixed with 💡) telling the user they may **refine the spec first** — Strategist will produce the full design spec, then stop for review/revision of any part of it before any generation, via the [refine-spec](workflows/refine-spec.md) workflow. Default is OFF: no request → the spec is written in one go and the pipeline auto-proceeds as usual. Only when the user explicitly asks in chat (e.g. "refine the spec first") or confirms `refine_spec: true` through Confirm UI does the [refine-spec](workflows/refine-spec.md) workflow take over after the Eight Confirmations. This line, like the split-mode line, is required output every run — the user must see the choice exists; whether to act on it is theirs. When the Confirm UI is used, this choice also appears as the in-page refine-spec toggle and is captured in `result.json` (`refine_spec`); the chat-summary fallback still prints this line.

**Formula rendering policy lives inside item 7 (Typography plan)**:

| Policy | Behavior |
|---|---|
| `mixed` (default) | Strategist renders complex formula-worthy expressions as PNG assets; simple inline expressions remain editable text / Unicode |
| `render-all` | Strategist renders every formula-worthy expression as PNG assets |
| `text-only` | No formula rendering; formulas remain editable text / Unicode |

After the Eight Confirmations are approved and **before outputting `design_spec.md` / `spec_lock.md`**, if the confirmed formula policy is `mixed` or `render-all` and the content contains formula-worthy expressions, Strategist MUST:

1. Identify explicit LaTeX and any source expressions that should be faithfully structured as formulas.
2. Write `<project_path>/images/formula_manifest.json` with only the formulas selected for rendering.
3. Run:
   ```bash
   python3 ${SKILL_DIR}/scripts/latex_render.py <project_path>
   ```
4. Include the rendered formula PNGs as `Acquire Via: formula`, `Status: Rendered`, `Type: Latex Formula` rows in `design_spec.md §VIII Image Resource List`; also list them in `spec_lock.md images` with `| no-crop`.

The formula renderer uses a provider fallback chain by default: `codecogs,quicklatex,mathpad,wikimedia`. The first three are color-aware; Wikimedia is an availability fallback. Formula PNGs are transparent by default: manifest `background` is the temporary render matte and transparency-removal reference, not a retained final background unless `transparent: false` is set for that item. Do not scan `spec_lock.md` for `$...$` or `$$...$$`. Dollar-delimited math in source material is only a signal for Strategist; the renderer consumes the explicit manifest.

If the user provided images or formula PNGs were rendered, run analysis **before outputting the design spec**. It writes `analysis/image_analysis.csv` — the authoritative regenerated image-fact view in the `analysis/` folder, which MUST be read before authoring §VIII:
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> 🔁 **Image facts are regenerated on demand, never a durable store.** `images/` is a live working folder — pictures are extracted from the source at import, the user may drop or replace files at any time, and Step 5 writes web/AI images into it. The single source of truth is therefore the **current contents of `images/`**, and `analysis/image_analysis.csv` is a *regenerated view* of it, not a fact to keep in sync. Re-run `analyze_images.py <project_path>/images` immediately **before any step that reads image facts** so the view reflects the live folder: before the §h image-usage recommendation (see [strategist.md](references/strategist.md) §h), here before authoring §VIII, after Step 5 acquisition (so web/AI files join the view), and again any time the user says they added or replaced images. This is the staleness strategy — re-derive on use, no cache to invalidate.

> ⚠️ **Image handling**: NEVER directly read / open / view image files (`.jpg`, `.png`, etc.). All image info comes from `analyze_images.py` output (`analysis/image_analysis.csv`) or the Design Spec's Image Resource List.

**Output**:
- `<project_path>/design_spec.md` — human-readable design narrative
- `<project_path>/spec_lock.md` — machine-readable execution contract (skeleton: `templates/spec_lock_reference.md`); Executor re-reads before every page

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
```markdown
## ✅ Strategist Phase Complete
- [x] Read the auto-extracted facts already in `analysis/` (e.g. `source_profile.json`) before the Eight Confirmations
- [x] Eight Confirmations completed (user confirmed via Confirm UI `result.json` or chat fallback)
- [x] Split-mode note appended below the eight items (heavy or normal variant)
- [x] Spec-refinement opt-in line appended (default OFF; only the user's explicit request enters the refine-spec workflow)
- [x] Design Specification & Content Outline generated
- [x] Execution lock (spec_lock.md) generated
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

---

### Step 5: Image Acquisition Phase (Conditional)

🚧 **GATE**: Step 4 complete; Design Specification & Content Outline generated and user confirmed. Any formula rows already have `Acquire Via: formula` and `Status: Rendered`.

> **Trigger**: At least one row in the resource list has `Acquire Via: ai`, `web`, and/or `slice`. If every row is `user`, `formula`, or `placeholder`, skip to Step 6.

**Failure recovery**: stop/continue behavior for AI/web/slice/image-readiness failures is defined in [`workflows/failure-recovery.md`](workflows/failure-recovery.md). This Step keeps the acquisition procedure.

**Always load the common framework**:

```
Read references/image-base.md
```

Then **lazy-load the path-specific reference** for each row that actually needs it:

| Acquire Via | Load reference (only if any such row exists) | Run |
|---|---|---|
| `ai` | `references/image-generator.md` | write `<project_path>/images/image_prompts.json`, then follow `image-generator.md §7 Path Selection` (`image_gen.py --manifest` is **Path A only**) |
| `web` | `references/image-searcher.md` | `python3 ${SKILL_DIR}/scripts/image_search.py ...` (≥2 web rows → `--batch images/image_queries.json`) |
| `slice` | `references/image-generator.md` §4.3 | derived — **after** the parent `ai` sheet row is `Generated`, run `python3 ${SKILL_DIR}/scripts/slice_images.py <project_path>/images/<sheet>.png --grid RxC --names ... --trim --alpha` (see workflow step 2.5) |
| `user` / `formula` / `placeholder` | (skip) | (skip) |

A deck with only `ai` rows never loads `image-searcher.md`; a deck with only `web` rows never loads `image-generator.md`. A mixed deck loads both, processes each row through its own path, and writes both `image_prompts.json` and `image_sources.json`.

> ⚠️ **In-pipeline ai rows MUST use the manifest contract** — even when only 1 ai row exists. Always write `images/image_prompts.json` first and render `image_prompts.md` with `image_gen.py --render-md`. Then execute the confirmed path from `image-generator.md §7`: `image_gen.py --manifest` is **Path A only**; `host-native` is **Path B** and MUST skip `--manifest`; `manual` writes the prompts and stops for external generation. The positional form (`image_gen.py "prompt" ...`) is reserved for **out-of-pipeline one-off testing / single-image fixups** — it skips manifest + sidecar, leaving no audit trail.

> ⚠️ **web path — batch multiple rows**: when ≥2 rows are `Acquire Via: web`, write all queries into `images/image_queries.json` and run `image_search.py --batch` once (concurrent acquisition, status written back), instead of one CLI call per row. A single web row may use the positional single-query form. See [image-searcher.md](references/image-searcher.md) §5.

> 💡 **ai path — spot illustrations as one sheet**: when the §VIII image resource plan needs ≥3 same-family spot illustrations as decorative accessories, generate **one grid sheet** (a single `ai` sheet row) instead of one row per element, then slice it (workflow step 2.5 below). Choose sheet geometry from intended placement: `1xN` / `Nx1` are useful for extreme portrait / landscape cells, and a designed `MxN` grid is valid when its cell ratio fits the planned elements. The sheet row is generated but not placed; each cut **element row** (`Acquire Via: slice`) is placed and must appear in `spec_lock.md images`. One generation = one coherent style across all pieces. Resource contract + the geometry rules: [image-generator.md](references/image-generator.md) §4.3.

> ⚠️ **Honor the confirmed image source before running any generation command**: the `ai` generation path (Path A = `image_gen.py` API / Path B = host-native tool / Offline Manual) is **not** auto-only — a confirmed choice other than `auto` wins, whether it came from chat (canonical) or, when the page was used, `result.json.image_ai_path`. `host-native` forces Path B even when `IMAGE_BACKEND` is configured; `api` forces Path A; `manual` forces offline. Never run `image_gen.py --manifest` when the confirmed value is `host-native` or `manual`. Full selection rule: [image-generator.md](references/image-generator.md) §7 Path Selection.

Workflow:

1. Extract all resource rows from the design spec and group them by `Acquire Via`; rows with `Status: Pending` or `Status: Failed` and `Acquire Via ∈ {ai, web, slice}` must all reach a terminal state before Executor starts
2. Generate prompts (ai rows) and/or run search (web rows) per [image-base.md](references/image-base.md) §3 dispatch table
2.5. **Slice any spot-illustration sheets (only if `slice` rows exist).** For each generated `ai` **sheet** row, run `slice_images.py` (grid + the element `--names` matching the `slice` rows, `--trim --alpha`) so every element file lands in `images/`; mark each `slice` row `Generated`. A sheet still in `Needs-Manual` cannot be sliced — leave its `slice` rows `Needs-Manual` and surface them at the Step 7 readiness gate. Contract: [image-generator.md](references/image-generator.md) §4.3.
3. Verify every row reaches a terminal status: `Generated` (ai success / sliced element), `Sourced` (web success), or `Needs-Manual`. `Failed` is not a terminal status: it means the current run did not generate that item, but the item remains retryable. The agent must resolve every residual `Failed` item by rerunning the confirmed path or marking it `Needs-Manual` before Executor starts
4. Re-derive image facts now that web / AI / sliced files are in the folder — `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` — so `analysis/image_analysis.csv` reflects every acquired image **including the sliced elements** (real measured sizes) before the Executor lays them out. Image facts are regenerated on use, never a stale store (see Step 4's image-facts note).

**✅ Checkpoint — Confirm acquisition attempted for every row**:
```markdown
## ✅ Image Acquisition Phase Complete
- [x] image_prompts.json created (when any ai rows processed)
- [x] image_prompts.md sidecar rendered (when any ai rows processed)
- [x] image_sources.json created (when any web rows processed)
- [x] Spot-illustration sheets sliced (when any `slice` rows exist); every element file present in `images/` and listed in `spec_lock.md images`
- [x] Each row: status is `Generated` / `Sourced` / `Needs-Manual` (no `Pending` or `Failed` remaining)
- [x] analyze_images.py re-run so image_analysis.csv covers the acquired web / AI / sliced images
```

**Default — auto-proceed to Step 6.** Only when the user's Step 4 response explicitly opted into split mode (in chat or via Confirm UI `result.json` with `generation_mode: "split"`), output the Phase A hand-off below and stop this conversation:

  ```markdown
  ## ✅ Phase A Complete
  - [x] Spec: `design_spec.md`, `spec_lock.md`
  - [x] Resources: `sources/`, `images/`, `templates/`
  - [ ] **Next**: open a fresh chat window and input `继续生成 projects/<project_name>` to enter Phase B via the [`resume-execute`](workflows/resume-execute.md) workflow.
  ```

> On acquisition failure, do NOT halt — follow the Failure Handling rule in [image-base.md](references/image-base.md) §5: retry once, then mark the row `Needs-Manual`, report to user, and continue to the checkpoint above.

---

### Step 6: Executor Phase

🚧 **GATE**: Step 4 (and Step 5 if triggered) complete; all prerequisite deliverables are ready.

**Artifact ownership**: `svg_output/` is the author source, `svg_final/` is derived, and image facts come from the regenerated `analysis/image_analysis.csv`; see [`references/artifact-ownership.md`](references/artifact-ownership.md).

Read the execution references for this deck's locked `mode` + `visual_style` (from `spec_lock.md`):
```
Read references/executor-base.md                  # REQUIRED: common guidelines
Read references/shared-standards.md               # REQUIRED: SVG/PPT technical constraints
Read references/modes/<locked-mode>.md            # narrative skeleton (spec_lock.md `mode`)
Read references/visual-styles/<locked-style>.md   # aesthetic (spec_lock.md `visual_style`)
```

> Read executor-base + shared-standards + the one locked mode file + the one locked visual-style file. For `mode: custom` or `visual_style: custom`, skip that preset file and follow `mode_behavior` / `visual_style_behavior` from `spec_lock.md` instead. Never glob `modes/` or `visual-styles/`.

**Design Parameter Confirmation (Mandatory)**: before the first SVG, output key design parameters from the spec (canvas dimensions, color scheme, font plan, body font size). See executor-base.md §2.

**Live Preview Auto-Startup (Mandatory)**: before the first SVG, automatically start the browser editor in live mode and keep it running continuously through Executor + Step 7 export:
```bash
python3 ${SKILL_DIR}/scripts/svg_editor/server.py <project_path> --live --daemon
```
- Start it immediately when Executor begins; `svg_output/` may be empty. Editor opens at `http://localhost:5050`; if another project already holds it, the launcher **auto-advances to the next free port** — read the actual URL from the launch log and report that.
- Run it as a long-running side process/session; do not wait for it to exit before generating SVG pages. Do not wait for user confirmation after startup.
- **Service must keep running** until one of: (a) the user clicks **Exit preview** in the browser, or (b) the user explicitly asks in chat to stop it. Generation continues even if the user closes the editor.
- **Do NOT read or apply submitted annotations during generation.** Users may annotate at any time, but Executor proceeds without touching them. The window to apply annotations opens only after Step 7 completes — see [`workflows/live-preview.md`](workflows/live-preview.md).
- The editor also supports **staged direct edits** (text content + SVG element attributes previewed immediately, then written to `svg_output/` only when the user clicks **Apply changes**; `Ctrl+Z` / Undo drops staged edits) alongside annotation; re-export stays chat-driven. Full scope and editor details: see [`workflows/live-preview.md`](workflows/live-preview.md) Notes.

**Pre-generation Batch Read (Mandatory)**: before the first SVG, batch-read every distinct layout SVG referenced in `spec_lock.page_layouts` and every distinct chart SVG referenced in `spec_lock.page_charts` (plus any §VII backup charts). One read per file, up front — do not re-read these during page generation. See executor-base.md §1.0.

> Image facts: trust the `analysis/image_analysis.csv` regenerated at the end of Step 5. If `images/` changed since (the user swapped or added files), re-run `python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images` before laying images out — facts are re-derived on use, never a stale store (Step 4 image-facts note).

**Per-page spec_lock re-read (Mandatory)**: before **each** SVG page, `read_file <project_path>/spec_lock.md` and use only its colors / fonts / icons / images, plus the per-page `page_rhythm` / `page_layouts` / `page_charts` lookups (resolves to template SVGs already loaded in the batch read above). Resists context-compression drift on long decks. See executor-base.md §2.1.

> ⚠️ **Main-agent only**: SVG generation MUST stay in the current main agent — page design depends on full upstream context. Do NOT delegate to sub-agents.
> ⚠️ **Generation rhythm**: generate pages sequentially, one at a time, in the same continuous context. Do NOT batch (e.g., 5 per group).

**Visual Construction Phase**: generate SVG pages sequentially, one at a time, in one continuous pass → `<project_path>/svg_output/`

**Quality Check Gate (Mandatory)** — after all SVGs, BEFORE annotation handling and speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path>
```
- Any `error` (banned SVG features, viewBox mismatch, spec_lock drift, etc.) MUST be fixed before proceeding — return to Visual Construction, regenerate that page, re-run check.
- `warning` entries (low-res image, non-PPT-safe font tail, etc.): fix when straightforward, otherwise acknowledge and release.
- Run against `svg_output/` (not after `finalize_svg.py` — finalize rewrites SVG and masks violations).

**Logic Construction Phase**: generate speaker notes → `<project_path>/notes/total.md`

**✅ Checkpoint — Confirm all SVGs and notes are fully generated and quality-checked. Proceed directly to Step 7 post-processing**:
```markdown
## ✅ Executor Phase Complete
- [x] Live preview started and kept available at the reported URL
- [x] All SVGs generated to svg_output/
- [x] svg_quality_checker.py passed (0 errors)
- [x] Speaker notes generated at notes/total.md
```

> **Chart pages?** If this deck contains data charts (bar / line / pie / radar / etc.), run the standalone [`verify-charts`](workflows/verify-charts.md) workflow before Step 7 to calibrate coordinates. AI models routinely introduce 10–50 px errors when mapping data to pixel positions; verify-charts eliminates that class of error. Skip if no chart pages.

> **Visual self-check (opt-in)?** If the user explicitly asked for a per-page visual re-pass on the SVGs ("跑一下视觉自检 / 视觉回看", "visual review", "check pages visually", etc.), run the standalone [`visual-review`](workflows/visual-review.md) workflow before Step 7. Do NOT run it by default and do NOT recommend it based on inferred model capability or deck size — trigger is user request only.

---

### Step 7: Post-processing & Export

🚧 **GATE**: Step 6 complete; all SVGs generated to `svg_output/`; speaker notes `notes/total.md` generated.

🚧 **Image readiness GATE** (when Step 5 left ai rows in `Needs-Manual`): every expected file must exist at `project/images/<filename>` before running 7.1.

**Failure recovery**: if a Step 7 command fails, fix the owning source artifact and resume from the failed sub-step per [`workflows/failure-recovery.md`](workflows/failure-recovery.md). Do not restart Phase A unless the owning source changed.

> If files are missing: PAUSE, list the missing filenames, point the user to `images/image_prompts.md` (each `### Image N:` block is paste-ready for ChatGPT / Gemini / Midjourney; auto-generated from `image_prompts.json`) and the required placement `project/images/<filename>`. Resume Step 7.1 only after all expected files are in place. `finalize_svg.py` and `svg_to_pptx.py` do not detect missing files at this layer — proceeding with gaps produces a deck with broken image references.

> **Spot-illustration sheets at this gate**: `slice` element files are **derived**, not placed by the user. If a sheet was `Needs-Manual` (offline), the element files do not exist yet — list the **sheet** filename (`images/<sheet>.png`) plus its element target names, and instruct: place the sheet, then run the Step 5 `slice_images.py` command for it, then re-run `analyze_images.py`, before resuming 7.1. Never tell the user to hand-place the individual element files — they only come from slicing the sheet.

> ⚠️ Run the three sub-steps **one at a time** — each must complete successfully before the next.
> ❌ **NEVER** combine them into a single code block or shell invocation.

Canonical three-command pipeline (mirrors `references/shared-standards.md` §5):

**Step 7.1** — Split speaker notes:
```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** — SVG post-processing (icon embedding / image crop & embed / raster image optimization / text flattening / rounded rect to path):
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```
Default raster handling for `svg_final/`: images are embedded at the rendered SVG size budget (`--image-scale 2`, `--max-dimension 2560`), opaque PNG photos may be written as JPEG, and transparent assets remain PNG. Use `--no-compress` or a higher `--max-dimension` only for diagnostic / high-fidelity SVG snapshots.

**Step 7.3** — Export PPTX (embeds speaker notes by default):
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path>
# Output (default-flow mode):
#   exports/<project_name>_<timestamp>.pptx           ← native pptx (canonical output, reads svg_output/)
#   backup/<timestamp>/svg_output/                    ← Executor SVG source backup (always written)
#
# Add --svg-snapshot to additionally emit the SVG-image preview pptx alongside the native pptx:
#   exports/<project_name>_<timestamp>_svg.pptx      ← SVG preview pptx (reads svg_final/)
```

> The native pptx consumes `svg_output/` directly so the converter can preserve
> high-fidelity primitives (icon `<use>` placeholders, image `preserveAspectRatio`
> → native picture crop metadata, rounded rect `rx/ry` → `prstGeom roundRect`).
> Native raster images are optimized by default before writing `ppt/media`
> (`--image-sizing cap`, `--image-max-dimension 2560`, `--image-quality 85`).
> This optimization downscales only oversized full source images; it does not
> crop pixels out of embedded PPTX media, and it does not reduce a small
> placement image merely because it is currently displayed small. Display
> cropping remains editable PPT picture-crop metadata. Add `--no-image-optimize`
> only when the deck must retain original image bytes. Use
> `--image-sizing display --image-scale 2` only for aggressive size reduction.
> The `svg_output/`
> snapshot in `backup/<timestamp>/` is always written so the project can be
> re-exported from frozen SVG sources without re-running the LLM. The SVG-rendered
> preview pptx is opt-in via `--svg-snapshot` — live preview already provides the
> SVG visual reference, so it's only needed when you want a self-contained file
> to share. Pass `-s output` or `-s final` to force a single source if you need it.

> **Paragraph editability vs line fidelity** — by default, mergeable dy-stacked
> paragraph blocks collapse into one editable PowerPoint text frame with multiple
> `<a:p>`, improving body-text editing and resize/reflow behavior. Add `--no-merge`
> only when the user explicitly asks for strict line-layout fidelity or when a
> layout-tight page must keep every dy-stacked line as its own text frame. The
> merge detector is conservative; mixed-layout text falls back to per-line frames.

**Optional animation flags** (page transitions are on by default; per-element entrance is off by default — turn it on only when the user asks for it):
- `-t <effect>` — page transition. Default `fade`. Options: `fade` / `push` / `wipe` / `split` / `strips` / `cover` / `random` / `none`.
- `-a <effect>` — per-element entrance animation. **Default `none`** — pages appear as a whole, no auto-firing element builds (the unsolicited cascade reads as the "AI deck" tell). Opt in with `auto` (map effect from group id: chart→wipe, card-/step-/pillar-→fly, title/takeaway→fade; image-like ids `hero` / `figure-` / `image` / `img-` / `kpi` cycle a richer pool — zoom / dissolve / circle / box / diamond / wheel — so multiple images vary across the deck), a specific effect like `fade`, or `mixed` for the legacy 16-effect cycle. Requires top-level `<g id="...">` groups (already required by Executor).
- `--animation-trigger {on-click,with-previous,after-previous}` — Start mode (matches PowerPoint's animation-pane Start dropdown). Default `after-previous` (click-free cascade; pace via `--animation-stagger`). Use `on-click` for presenter-paced reveals, or `with-previous` for all-at-once.
- `--animation-config <path>` — optional object-level sidecar. Default: `<project_path>/animations.json` when present.
- `--auto-advance <seconds>` — kiosk-style auto-play.

**Optional custom animations** (only when the user asks to tune animation order/effects/timing for specific objects):

Run the standalone [`customize-animations`](workflows/customize-animations.md) workflow. Default export applies page transitions but no per-element entrance animation; create `animations.json` (or pass `-a auto`) only when the user asks for element animation or object-level customization.

**Optional recorded narration** (only when the user asks for narrated/video export):

Run the standalone [`generate-audio`](workflows/generate-audio.md) workflow. The AI picks a narration backend (`edge` by default, or a configured cloud provider such as ElevenLabs / MiniMax / Qwen / CosyVoice for high-quality or cloned voices), asks the user once (backend + voice + rate/settings + embed-or-not, all with recommended values), then executes `notes_to_audio.py` and (if chosen) re-exports the PPTX with `--recorded-narration audio`.

Do NOT call `notes_to_audio.py` directly without going through the workflow — `--voice` / `--voice-id` is required and the workflow produces the locale/provider-aware recommendation that makes the choice meaningful.

Full effect list, anchor logic, and limits: [`references/animations.md`](references/animations.md).

> ❌ **NEVER** substitute `cp` for `finalize_svg.py` — finalize performs multiple critical processing steps
> ❌ **NEVER** force `-s output` for the legacy/preview pptx (PowerPoint's internal SVG parser drops icons and rounded corners). The default auto-split already gives native the high-fidelity source it needs without touching legacy.
> ❌ **NEVER** use `--only` (it suppresses one of the two output files)

> **Post-export annotation window**: the preview service from Step 6 typically remains running after export. If the user submitted annotations in the browser (during Executor or after export) and now asks to apply them — they may quote the browser prompt (`Changes saved to svg_output...` / `修改已保存到 svg_output...`), say "apply my annotations" / "应用注解" / equivalent — run [`live-preview`](workflows/live-preview.md) Step 2 to apply and re-export. Annotations submitted during generation are also handled here, not earlier.

> **Direct edits in the browser**: the user may also stage text / SVG attribute edits in the preview. These land in `svg_output/` only after the user clicks **Apply changes**. If they ask to "re-export" / "重新导出" after applying such edits, just re-run Step 7.2–7.3 (finalize + export); no annotation-application step is needed unless they also saved AI-needed annotations.

> **Preview not running?** Any time the user mentions "live preview", "preview", "看效果", or wants to select/click a slide element and the service is not running, run [`live-preview`](workflows/live-preview.md) Step 1 to start it. If the service is already running, just point them at the URL — do not restart.

---

## Role Switching Protocol

Before switching roles, **MUST first read** the corresponding reference file. Output marker:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Reference Resources

| Resource | Path |
|----------|------|
| Shared technical constraints | `references/shared-standards.md` |
| Canvas format specification | `references/canvas-formats.md` |
| Image-text layout patterns (Primary structures + Modifier layers — combine freely) | `references/image-layout-patterns.md` |
| Image layout sizing (math for side-by-side container dimensions) | `references/image-layout-spec.md` |
| SVG image embedding | `references/svg-image-embedding.md` |
| Icon library | `templates/icons/README.md` |

---

## Notes

- Local preview: `python3 -m http.server -d <project_path>/svg_final 8000`
- **Troubleshooting**: on generation issues (layout overflow, export errors, blank images, etc.), check `docs/faq.md` for known solutions
