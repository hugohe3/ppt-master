---
description: Generate a new PPT layout template based on existing project files or reference templates
---

# Create New Template Workflow

> **Role invoked**: [Template_Designer](../references/template-designer.md)

Generate a complete set of reusable PPT layout templates for the **global template library**.

> This workflow is for **library asset creation**, not project-level one-off customization. The output must be reusable by future PPT projects and discoverable from `templates/layouts/layouts_index.json`.

## Process Overview

```
Gather Brief -> Import PPTX References -> Create Directory -> Invoke Template_Designer -> Validate Assets -> Register Index -> Output
```

---

## Step 1: Gather Template Information

**MANDATORY interactive confirmation — this step BLOCKS all subsequent steps.**

Before any directory creation, file write, or `Template_Designer` invocation:

1. List every Required item below to the user in one message
2. Ask the user to confirm or fill them in
3. Wait for the user's reply
4. Echo back the finalized brief and emit the marker `[TEMPLATE_BRIEF_CONFIRMED]` on its own line

Skipping this gate — including silently inferring values from the reference source, opened IDE file, or prior conversation — is a workflow violation. Even if the user provides a `.pptx` reference and says "用这个做模板", you MUST still surface the Required items and obtain explicit confirmation; the reference source does not substitute for the brief.

Step 2 MUST NOT run until `[TEMPLATE_BRIEF_CONFIRMED]` has been emitted in the current conversation.

Items to confirm with the user:

| Item | Required | Description |
|------|----------|-------------|
| New template ID | Yes | Template directory / index key. Prefer ASCII slug such as `my_company`; if using a Chinese brand name, it must be filesystem-safe and match `layouts_index.json` exactly |
| Template display name | Yes | Human-readable name for documentation |
| Category | Yes | One of `brand` / `general` / `scenario` / `government` / `special` |
| Applicable scenarios | Yes | Typical use cases, such as annual report / defense / government briefing |
| Tone summary | Yes | Short tone description for recommendation, such as `Modern, restrained, data-driven` |
| Theme mode | Yes | Theme description for recommendation, such as `Light theme (white background + blue accent)` |
| Canvas format | Yes | Default `ppt169`; if another format is needed, specify it explicitly before generation |
| Replication mode | Yes | `standard` (default, 5-page roster) or `fidelity` (preserve every distinct layout from a `.pptx` source); `fidelity` requires a `.pptx` reference source |
| Visual fidelity for fixed pages | Yes (when reference source exists) | `literal` (exact reproduction — preserve original geometry, decoration, sprite crops as-is; for cover / chapter / ending especially) or `adapted` (use the reference for tone/structure but allow design evolution). Ask the user explicitly; do not assume. Different page types may take different settings |
| Reference source | Optional | Existing project, screenshot folder, or `.pptx` template file path |
| Theme color | Optional | Primary color HEX value (can be auto-extracted from reference) |
| Design style | Optional | Additional style notes, decorative language, brand cues |
| Assets list | Optional | Logos / background textures / reference images to include in the template package |
| Keywords | Yes | 3–5 short tags for `layouts_index.json` lookup (e.g., `McKinsey`, `Consulting`, `Structured`) |

> **Persist the brief into `design_spec.md`**. When the Template_Designer writes `design_spec.md` in Step 3, declare a YAML frontmatter block at the top with the confirmed brief (`template_id`, `label`, `category`, `summary`, `keywords`, `primary_color`, `canvas_format`, `replication_mode`, etc.). `register_template.py` reads this in Step 5, so the brief flows directly into the index without the AI re-deriving it from prose. See Step 5 for the recommended frontmatter shape.

**Required outcome of Step 1** (all must be true before emitting `[TEMPLATE_BRIEF_CONFIRMED]`):

- [ ] User has been asked the Required items above in the current conversation
- [ ] User has replied with values or explicit acceptance of suggested defaults
- [ ] The template is clearly positioned as a **global library template**
- [ ] The canvas format is fixed before SVG generation
- [ ] The template metadata is complete enough to register into `layouts_index.json`
- [ ] Marker `[TEMPLATE_BRIEF_CONFIRMED]` emitted on its own line after the echoed brief

**If a reference source is provided**, analyze its structure first:

```bash
ls -la "<reference_source_path>"
```

If the reference source is a `.pptx` template file, use the unified preparation helper:

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py "<reference_template.pptx>"
```

This helper reads OOXML directly via `pptx_to_svg` and produces, in one workspace:

- `manifest.json` — single source of truth: slide size, theme colors, fonts, asset inventory, per-slide / per-layout / per-master metadata, page-type candidates
- `summary.md` — short human-readable digest derived from manifest.json (for quick scanning only)
- `assets/` — extracted reusable image assets
- `svg/` — **primary view** (layered template view):
  - `svg/master_*.svg` — every slide master in the deck rendered once, including masters that no sample slide currently uses (template packages routinely ship more masters than the visible samples reference)
  - `svg/layout_*.svg` — every slide layout in the deck rendered once (its own contribution; master shapes do **not** repeat here)
  - `svg/slide_NN.svg` — each slide's own shapes; master / layout shapes are **not** inlined here
  - `svg/inheritance.json` — which layout & master each slide consumes
- `svg-flat/` — **companion view** (one self-contained SVG per slide):
  - `svg-flat/slide_NN.svg` — master + layout + slide painted into a single SVG so opening any slide on its own shows the full page like PowerPoint would. Use this for previews / screenshot pipelines / "what does the slide actually look like" sanity checks.
- The default `--inheritance-mode both` emits both views. Pass `layered` to skip `svg-flat/`, or `flat` for round-trip use cases (legacy: `svg/` becomes self-contained slides without the master/layout/inheritance files).

It is a reconstruction aid, not a final direct template conversion.

When the reference source is `.pptx`, use the following internal priority order during template creation:

1. `manifest.json` (factual metadata: slide size, theme, assets, layouts, masters, slide page-types)
2. `svg/master_*.svg` and `svg/layout_*.svg` — read these **before** any slide SVG; they show the deck's shared visual language (background, headers, footers, decorative bars). This is what the new template's fixed structure should adapt from.
3. `svg/inheritance.json` — confirms which slide uses which layout/master
4. exported `assets/`
5. cleaned slide SVG references `svg/slide_NN.svg` — content unique to each slide; consult after the master/layout language is understood
6. `summary.md` only as a quick orientation aid
7. user-provided screenshots or the original PPTX only for visual cross-checking

Interpretation rule:

- `manifest.json` is the source of truth for slide size, theme colors, fonts, background inheritance, reusable asset inventory, unique layout/master structure, and slide reuse relationships
- `summary.md` is a quick scan; never treat it as the canonical fact source — go back to `manifest.json` if anything is unclear
- exported `assets/` are the canonical reusable image pool — `<image>` references in `svg/` already point at these files directly
- `svg/master_*.svg` / `svg/layout_*.svg` are the **primary source for fixed structural design** — recurring backgrounds, page chrome, decorative motifs that the template should preserve. The new template's `01_cover` / `02_chapter` / `03_content` / `04_ending` typically inherit elements from these layers.
- `svg/slide_NN.svg` shows page-specific content — useful for judging composition rhythm and content density, not for fixed structure. Read every slide regardless of count.
- screenshots remain useful for judging composition and style, but should not override extracted factual metadata unless the import result is clearly incomplete

**Hard gate**:

- Before creating any template file, the agent MUST finish reading every `svg/master_*.svg`, `svg/layout_*.svg`, and `svg/slide_*.svg` file under `<import_workspace>/svg/`
- The agent MUST explicitly report the read master / layout / slide filenames before starting template generation

Do **not** treat the imported PPTX or exported slide SVGs as direct final template assets. The goal is to reconstruct a clean, maintainable PPT Master template package, not to perform 1:1 shape translation.

---

## Step 2: Create Template Directory

> **Precondition**: `[TEMPLATE_BRIEF_CONFIRMED]` was emitted in Step 1. If not, return to Step 1.

```bash
mkdir -p "skills/ppt-master/templates/layouts/<template_id>"
```

> **Output location**: Global templates go to `skills/ppt-master/templates/layouts/`; project templates go to `projects/<project>/templates/`
>
> The generated directory name must match the final template ID used in `layouts_index.json`.

---

## Step 3: Invoke Template_Designer Role

**Switch to the Template_Designer role** and generate per role definition. The role input is the finalized template brief from Step 1, not a project design spec.

If the reference source is `.pptx`, pass the following internal package to the role:

- finalized template brief from Step 1
- `manifest.json`
- `summary.md` (orientation only)
- exported `assets/`
- cleaned slide SVG references from `svg/`
- optional screenshots, if available

The role should use the import output to anchor objective facts such as theme colors, fonts, reusable backgrounds, and common branding assets, then rebuild the final SVG templates in a simplified, maintainable form.

**Apply the visual-fidelity decision from Step 1**: pages marked `literal` (typically cover / chapter / ending) must reproduce the reference's geometry, decoration, and sprite-sheet crops as-is — "simplified, maintainable form" applies only to genuinely redundant structure, not to load-bearing layout. Pages marked `adapted` may use the reference for tone and structural rhythm but evolve the design.

**Sprite-sheet preservation (do NOT simplify away)**: PPTX-exported assets are often sprite sheets — a single tall/large image referenced from multiple slides, each cropping a different region via nested `<svg ... viewBox="...">` wrappers around `<image width="1" height="1">`. This nesting is **load-bearing geometry**, not redundant structure. When rebuilding, preserve the exact `viewBox` crop and the outer `<svg>` placement for every image; do not flatten to a single `<image>` with direct `x/y/width/height`. Verify by sampling: if any asset's pixel dimensions don't match the on-page display aspect, it is a sprite and the wrapper must stay.

**Expected outputs from this step** (full spec → [template-designer.md](../references/template-designer.md)):

1. `design_spec.md` (with §VI page roster matching the actual SVG files; declare brief frontmatter for `register_template.py`)
2. Page roster — see [Page Roster](../references/template-designer.md#page-roster) for `standard` vs `fidelity` mode, variant naming, and TOC handling
3. Placeholder vocabulary — pages should adopt the conventional names (`{{TITLE}}`, `{{CONTENT_AREA}}`, ...) when they fit. Full reference: [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). When a template style legitimately needs different vocabulary (consulting → `{{KEY_MESSAGE}}`, branded cover → `{{BRAND_LOGO}}`), declare a `placeholders:` block in `design_spec.md` frontmatter so the registrar and quality checker treat it as the template's authoritative contract. **Avoid** one-off indexed families such as `{{CHAPTER_01_TITLE}}` — use the indexed TOC pattern instead.
4. Template assets (optional) — Logos / PNG / JPG / reference SVG bundled with the template package

---

## Step 4: Validate Template Assets

```bash
ls -la "skills/ppt-master/templates/layouts/<template_id>"
```

Run SVG validation on the template directory:

```bash
python3 skills/ppt-master/scripts/svg_quality_checker.py "skills/ppt-master/templates/layouts/<template_id>" --template-mode --format <canvas_format>
```

`--template-mode` makes the checker:

- glob `*.svg` in the template directory directly (templates do not live under `svg_output/`)
- skip `spec_lock.md` drift checks (templates do not ship a spec_lock)
- enforce roster ↔ `design_spec.md` consistency as **errors** (orphan files / missing files break `layouts_index.json`)
- emit advisory **warnings** when a page lacks a conventional placeholder — these are hints, not failures. Declare a `placeholders:` block in `design_spec.md` frontmatter to silence them when your template intentionally uses a different vocabulary

**Checklist**:

- [ ] `design_spec.md` contains complete design specification, with §VI listing every emitted page
- [ ] Every page declared in `design_spec.md §VI` exists as an SVG file in the template directory (and vice versa — no orphan files)
- [ ] Variant filenames follow the letter-suffix convention (e.g. `03a_content_two_col.svg`); variants typically reuse the parent type's placeholder set unless the spec frontmatter declares otherwise
- [ ] If TOC exists, placeholder pattern uses the canonical indexed form
- [ ] SVG viewBox matches the chosen canvas format (for `ppt169`: `0 0 1280 720`)
- [ ] Placeholder names follow the canonical convention where applicable; templates with intentionally different vocabularies (e.g. `{{KEY_MESSAGE}}` instead of `{{PAGE_TITLE}}`) should declare a `placeholders:` frontmatter block to silence advisory warnings
- [ ] Asset files referenced by SVGs actually exist in the template package
- [ ] For `fidelity` mode: every sprite-sheet asset retains its nested `<svg viewBox=...>` crop wrapper; no image whose file aspect differs from its on-page aspect was flattened to a bare `<image>`

This step is a **hard gate**. Do not register the template into the library index until validation passes.

---

## Step 5: Register Template in Library Index

Run the unified registrar; it derives the `layouts_index.json` entry and refreshes the `README.md` Quick Index from `design_spec.md` (frontmatter when present, §I / §III tables otherwise) plus the actual SVG file list:

```bash
python3 skills/ppt-master/scripts/register_template.py <template_id>
```

Outputs:

- updates `skills/ppt-master/templates/layouts/layouts_index.json` — the flat `template_id → { label, summary, keywords, pages }` map
- refreshes the auto-managed Quick Index inside `skills/ppt-master/templates/layouts/README.md` (the surrounding category sections stay hand-edited)
- prints a "Template Creation Complete" card you can use directly for Step 6

`pages` is collected by globbing `*.svg` in the template directory, so `fidelity`-mode templates that include variant pages such as `03a_content_two_col` are listed automatically.

`layouts_index.json` is the lightweight lookup used when a user explicitly opts into the template flow. The main workflow defaults to free design and does not read this file unless a template trigger fires (see `SKILL.md` Step 3). A template directory that has not been run through `register_template.py` will not be discoverable by that flow.

> **Recommended for new templates**: declare a YAML frontmatter block at the top of `design_spec.md`. The registrar prefers it over the §I table and lets you set `category`, `keywords`, `summary`, etc. without relying on prose extraction:
>
> ```yaml
> ---
> template_id: my_template
> label: My Template
> category: brand            # brand | general | scenario | government | special
> summary: For ...
> keywords: [tag1, tag2, tag3]
> primary_color: "#005587"
> canvas_format: ppt169
> replication_mode: standard
> # Optional: per-page placeholder overrides. Templates that legitimately
> # use a different vocabulary (e.g. consulting decks with {{KEY_MESSAGE}}
> # in place of {{PAGE_TITLE}}, or content variants with bespoke slots)
> # should declare them here so svg_quality_checker --template-mode does
> # not flag them as conventional-placeholder gaps.
> placeholders:
>   01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{BRAND_LOGO}}"]
>   03_content: ["{{KEY_MESSAGE}}", "{{CONTENT_AREA}}"]
>   03a_content_dual_col: []   # silences hints for this variant entirely
> ---
> ```

> To rebuild every entry at once (e.g. after editing many specs), run:
>
> ```bash
> python3 skills/ppt-master/scripts/register_template.py --rebuild-all
> ```

If you need to update the categorized sections lower in `README.md` (Brand Style Templates / General Style Templates / etc.), edit those by hand — the registrar deliberately leaves them alone so curated descriptions are preserved.

---

## Step 6: Output Confirmation

`register_template.py` already printed a "Template Creation Complete" card during Step 5 — copy it verbatim into the conversation. The card includes the template name, path, category, primary color, index status, and the full SVG file roster (auto-collected from disk, so `fidelity`-mode variant pages and TOC pages are listed correctly without manual editing).

For a standard-mode template the card looks like:

```markdown
## Template Creation Complete

**Template Name**: <template_id> (<display_name>)
**Template Path**: `templates/layouts/<template_id>/`
**Category**: <category>
**Primary Color**: <hex>
**Index Registration**: Done

### Files Included

| File | Status |
|------|--------|
| `01_cover.svg` | Done |
| `02_chapter.svg` | Done |
| `02_toc.svg` | Done |
| `03_content.svg` | Done |
| `04_ending.svg` | Done |
```

---

## Color Scheme Quick Reference

| Style | Primary Color | Use Cases |
|-------|---------------|-----------|
| Tech Blue | `#004098` | Certification, evaluation |
| McKinsey | `#005587` | Strategic consulting |
| Government Blue | `#003366` | Government projects |
| Business Gray | `#2C3E50` | General business |

---

## Notes

1. **SVG technical constraints**: See [template-designer.md → SVG Technical Constraints](../references/template-designer.md)
2. **Color consistency**: All SVG files must use the same color scheme as `design_spec.md §III`
3. **Placeholder convention**: `{{}}` format only; default names listed in [Placeholder Reference](../references/template-designer.md#4-placeholder-reference-canonical-convention-overridable-per-template). Override per template via `placeholders:` frontmatter when needed.
4. **Discovery requirement**: A template directory is only discoverable after `register_template.py` has been run against it (Step 5)

> **Full role specification**: [template-designer.md](../references/template-designer.md)
