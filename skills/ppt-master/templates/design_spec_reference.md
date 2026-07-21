# Design Spec Structure

Project-level `design_spec.md` is a human-readable English-heading Markdown artifact. This file owns its normal authoring structure. [`schemas/design_spec.schema.json`](./schemas/design_spec.schema.json) provides structural lint for readable sections and page projection; it is not an execution lock and does not require textual equality with `spec_lock.md`.

Strategist reads the complete final confirmation once, writes this artifact from that retained state plus source analysis, and audits every confirmed field here. Afterward, `spec_lock.md` is authored from the completed Design Spec plus current project/page/template context; normal lock authoring never reopens `result.json`.

## 1. Author the complete artifact

After final confirmation, compose the entire document in active context from the retained final state, source analysis, and project context. Then create `<project_path>/design_spec.md` once, from the first line through §X.

**Mandatory — new-project write**: The first non-empty line is exactly `<!-- ppt-master-schema: design-spec/v1 -->`, followed by `# <Project Name> - Design Spec`. Write every required section with final values and the complete page roster; include conditional §VII only when a real catalog reference is selected. Do not create a placeholder-bearing project file, copy example rows, or patch a scaffold field by field.

`project_manager.py scaffold-spec` remains an optional manual convenience and overwrite-safe troubleshooting tool. It is not part of normal Generate authoring. Resume and refine paths edit an existing completed Design Spec rather than replacing it with a scaffold.

---

## 2. Exact document contract

Angle-bracketed text below is authoring notation, not project content. Resolve every universal value before writing the file; omit only rows explicitly marked conditional. Keep every required `##` heading; omit §VII when no real catalog reference is selected, while §VIII remains present even with no data rows. Do not copy examples, notation tokens, or a second schema description into the project artifact.

### 2.1 Header and project contract

Start with this exact heading order:

```markdown
<!-- ppt-master-schema: design-spec/v1 -->
# <Project Name> - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | <resolved project name> |
| Canvas Format | <canonical format and dimensions> |
| Page Count | <exact final count matching §IX> |
| Target Audience | <confirmed audience> |
| Communication Intent | <confirmed intent, including priority or sequence> |
| Desired Audience Outcome | <confirmed observable outcome> |
| Core Message / Ask / Action | <confirmed core message or ask> |
| Delivery Context | <confirmed delivery context> |
| Artifact Afterlife | <confirmed afterlife> |
| Reading Mode | <text, balanced, presentation, or the active non-PPT equivalent> |
| Content Strategy | <confirmed material-divergence prose or balanced default> |
| Design Style | <resolved design direction> |
| Formula Policy | <mixed, render-all, or text-only> |
| AI Image Acquisition Path | <confirmed path or not applicable> |
| Generation Mode | <continuous or split> |
| Spec Refinement | <enabled or disabled> |
| Created Date | <YYYY-MM-DD> |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | <canonical format name> |
| Dimensions | <width × height> |
| viewBox | `<exact viewBox>` |
| Margins | <safe margins> |
| Content Area | <usable bounds> |
```

When a template workspace is active, append exactly one line after the §I table: `- **Template Application**: <confirmed or Strategist-resolved natural-language plan>`. Omit it for free design. Never replace this prose with internal reuse/adherence ids.

### 2.2 Visual, typography, layout, and icons

Use these exact subsections and field shapes:

```markdown
## III. Visual Theme

### Theme Style

- **Mode**: <confirmed preset or custom>
- **Visual style**: <confirmed preset or custom>
- **Theme**: <resolved identity direction>
- **Tone**: <resolved tone>

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | <HEX> | <semantic use> |
| Secondary background | <HEX> | <semantic use> |
| Primary | <HEX> | <semantic use> |
| Accent | <HEX> | <semantic use> |
| Secondary accent | <HEX> | <semantic use> |
| Body text | <HEX> | <semantic use> |

## IV. Typography System

### Font Plan

| Role | Chinese | English | Fallback tail |
| --- | --- | --- | --- |
| Title | <family> | <family> | <fallback> |
| Body | <family> | <family> | <fallback> |

- **Title stack**: <complete ordered stack>
- **Body stack**: <complete ordered stack>
- **Role rationale**: <why the confirmed Title/Body system fits the content; name justified recurring family overrides, or state that none is needed>

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | <confirmed value> |
| Title | <confirmed value> |
| Subtitle | <confirmed value> |
| Annotation | <confirmed value> |

## V. Layout Principles

### Page Structure

- **Header area**: <rule>
- **Content area**: <rule>
- **Footer area**: <rule>

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | <value> |
| Content block gap | <value> |
| Icon-text gap | <value> |

## VI. Icon Usage Specification

- **Library**: <confirmed library, custom, or none>

| Purpose | Icon Path | Page |
| --- | --- | --- |
```

Preserve the confirmed Title/Body system, then add every Strategist-established recurring family override justified by the completed page plan. Append the same semantic role to the Font Plan table and add `- **<Role> stack**: <complete ordered stack>`. Typical optional roles include `Annotation`, `Footer`, `Footnote`, `Data`, `Emphasis`, `Quote`, and `Code`; add only roles that recur and intentionally differ. `Role rationale` records the decision but does not itself become a lock field. Do not collapse distinct Title/Body stacks or discard a declared optional role. Treat every Font Size Hierarchy value as a role anchor: Executor may adjust one occurrence within anchor `±2px`, but a new semantic role or any planned feature outside that band needs its own row. Add every recurring palette role and typography-size anchor established by the plan; do not enumerate one-off paint or font-family garnish. For confirmed custom directions, add the applicable `Mode References`, `Mode Behavior`, `Visual Style References`, and `Visual Style Behavior` lines under Theme Style. Include `Stroke Width` under §VI only for a stroke library. Leave the §VI table empty when no icons are used.

When §VIII contains any `Acquire Via: ai` row, add this subsection under §III and preserve the complete confirmed AI direction:

```markdown
### AI Image Strategy

- **Image Rendering**: <confirmed preset or custom>
- **Visual**: <confirmed visual treatment>
- **Mood**: <confirmed mood and analogy>
```

For a selected custom rendering, also add `Image Rendering Behavior`; add `Image Rendering References` only when the confirmed custom direction actually uses catalog material. Never add a separate image palette.

### 2.3 Visualization and image resources

Use the §VII table only when at least one real catalog reference is selected. Always keep the §VIII table, including when it has no data rows:

```markdown
## VII. Visualization Reference List

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| --- | --- | --- | --- | --- |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

§VII is a positive reference inventory. Every row uses a returned catalog key, its real `templates/charts/<key>.svg` path, and its verbatim summary. Never emit an empty §VII, a `no-template-match` / `n/a` placeholder row, or prose explaining that no reference exists. When recall finds no fit, omit that page from §VII and describe the custom fallback in the page's §IX `Visualization` / `Layout`. List real runners-up only for pages with a selected §VII reference, as `- <returned_key> | rejected for P<NN>: <page-specific reason>`.

For every independent data chart or pure text-grid table, add `- **Native-ready**: yes|no` to its §IX Slide block. Choose `yes` only when the confirmed requirement or artifact afterlife benefits from an editable native data object; otherwise use `no`. Conceptual visualizations and incidental sparklines, KPI trends, or insets omit this field and remain ordinary SVG.

In §VIII, author every planned or explicitly required resource from the confirmed source boundary. Copy the selected `Layout pattern` id/name and modifiers verbatim; set `Crop Policy` to `adaptive` or `no-crop`; set `Acquire Via` to `ai`, `web`, `user`, `formula`, `placeholder`, or `slice`. Preserve unresolved required assets as `Pending` or `Needs-Manual` instead of dropping or reclassifying them.

### 2.4 Complete page roster and notes

Write one ordered Slide block per page. Slide count and order must equal §I `Page Count`; `Content` is a complete page brief, not a skeleton.

```markdown
## IX. Content Outline

### Part 1: <section name>

#### Slide 01 - <page name>

- **Audience move**: <audience state before → after>
- **Layout**: <composition; include the chosen prototype when template-active>
- **Title**: <preferred page title>
- **Core message**: <one governing assertion>
- **Content**: <complete intended on-slide content and hierarchy>

## X. Speaker Notes Requirements

- **Filename**: match each SVG filename under `notes/`
- **Content**: <notes content and source-handling policy>
- **Total duration**: <resolved duration>
- **Notes style**: <formal, conversational, interactive, or resolved equivalent>
- **Presentation purpose**: <inform, persuade, inspire, instruct, report, or resolved combination>
```

Add `Visualization` and `Images` to a Slide block when it consumes §VII/§VIII rows or uses a page-local visualization. State whether `Visualization` is data-driven when source values determine geometry; this page-level declaration remains authoritative even when no catalog reference fits. Add `Native-ready: yes|no` only for independent data charts or pure text-grid tables. Add `Fact IDs` for sourced claims and `Data class: scenario` for invented demo values. Add `Cover impact` to P01 except on preservation paths; add `Closing impact` only when the final page genuinely resolves the deck. Roster ids/count/order and final content are authoritative. Layout, cover/closing composition, and image/chart patterns are References whose selected semantics remain fixed while Executor realizes their geometry, hierarchy, treatment, and sparse local garnish.

---

## 3. Machine validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reads the Markdown directly. It reports missing or out-of-order I–X sections, unresolved `[fill...]` placeholders, missing per-slide `Audience move`, and a missing §III `AI Image Strategy` when an §VIII table selects `ai` acquisition.

The schema validates structure only. Strategist role modules own field meaning, recommendation logic, page planning, image policy, and template policy. `spec_lock.md` owns stable execution anchors and routing selected in context; it is not an exhaustive value projection. On divergence, repair the Design Spec from the retained final state when Gate 1 fails, then re-author affected lock anchors from the audited Design Spec and current context. Never reopen `result.json` merely to author or validate the lock, and never use the lock to overwrite a valid Design Spec decision.
