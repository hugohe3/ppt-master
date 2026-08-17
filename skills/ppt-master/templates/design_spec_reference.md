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
| Primary Language | <confirmed canonical BCP-47 content tag> |
| Target Audience | <confirmed audience> |
| Communication Intent | <confirmed intent, including priority or sequence> |
| Desired Audience Outcome | <confirmed observable outcome> |
| Core Message / Ask / Action | <confirmed core message or ask> |
| Delivery Context | <confirmed delivery context> |
| Artifact Afterlife | <confirmed afterlife> |
| Reading Mode | <text, balanced, presentation, or the active non-PPT equivalent> |
| Content Strategy | <confirmed material-divergence prose or balanced default> |
| Design Style | <resolved design direction> |
| AI Image Acquisition Path | <confirmed path or not applicable> |
| Generation Mode | <continuous or split> |
| Spec Refinement | <enabled or disabled> |
| Speaker Notes | <enabled or disabled> — <explicit user instruction, final Stage-2 proactive policy, workflow default, or enabled Narration Audio dependency> |
| Custom Animations | <enabled or disabled> — <explicit instruction and object/all-motion scope, final Stage-2 proactive policy, or workflow default> |
| Narration Audio | <enabled or disabled> — <explicit user instruction, final Stage-2 proactive policy, or workflow default> |
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

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | <category/modifier> | <family> | <family> | <fallback> |
| Body | <category/modifier> | <family> | <family> | <fallback> |

- **Typography upgrade (Reference)**: <post-export role substitution after target installation; omit if none>
- **Title stack**: <complete ordered stack>
- **Body stack**: <complete ordered stack>

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

- **Primary bundled library**: <one of chunk-filled / tabler-filled / tabler-outline / phosphor-duotone, or none>
- **Brand-logo library**: <simple-icons when actual content requires prepared real brand marks; omit otherwise>

| Icon Path | Suitable Scenarios |
| --- | --- |
```

Preserve Title/Body characters and resolved stacks; omit blank Typography upgrade and never place it in a stack. For each justified recurring family override, add the role to Font Plan plus `- **<Role> stack**: <complete ordered stack>`. Possible roles are `Annotation`, `Footer`, `Footnote`, `Data`, `Emphasis`, `Quote`, and `Code`; add only recurring, intentional differences. Add non-locked `Role rationale` only for an extra family. Do not collapse distinct Title/Body stacks or discard a declared optional role. Each Font Size Hierarchy value is a role anchor: Executor may vary one occurrence `±2px`; a short non-structural Hero/Display size may stay unlisted only while the same value is planned at most twice, and its third occurrence needs a named row. Add every recurring palette role and typography-size anchor established by the plan; do not enumerate one-off paint or font-family garnish. For confirmed custom directions, add the applicable `Mode References`, `Mode Behavior`, `Visual Style References`, and `Visual Style Behavior` lines under Theme Style. Include `Stroke Width` under §VI only for a stroke library. `simple-icons` may accompany the one primary bundled library and is recorded only when actual content requires real brand marks; it is never a separate confirmation choice. The icon table records the curated synced SVG pool and broad semantic scenarios, not exact page placement or mandatory use. User-provided, template-carried, imported, custom, and other prepared SVGs under the project `icons/` directory remain usable without being forced into that bundled selection. Leave the §VI table empty when no bundled or brand SVG icons are prepared. Illustrated icons are AI image resources: their production sheet and placed slice rows belong in §VIII, and only placed slices project to `spec_lock.md images`.

When §VIII contains any `Acquire Via: ai` row, add this subsection under §III and preserve the complete confirmed AI direction:

```markdown
### AI Image Strategy

- **Image Rendering**: <confirmed preset or custom>
- **Visual**: <confirmed visual treatment>
- **Mood**: <confirmed mood and analogy>
```

For a selected custom rendering, also add `Image Rendering Behavior`; add `Image Rendering References` only when the confirmed custom direction actually uses catalog material. Never add a separate image palette.

### 2.3 Visualization and image resources

Use the §VII table only when at least one real Chart/Table catalog reference is selected. Always keep the §VIII table, including when it has no data rows:

```markdown
## VII. Visualization Reference List

| Page | Family | Template | Usage |
| --- | --- | --- | --- |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

§VII lists at most one `chart|table` reference per page: canonical Template key
plus semantic Usage. Resolve `family/key`; never derive paths from bare keys.
§IX owns child visuals, unmatched fallbacks, and qualitative relationships as
free `Layout` / `Visualization` prose. Layout/Deck alone owns reusable
PowerPoint structure. Omit empty §VII and recall diagnostics; legacy rows stay
readable, while new specs use four columns.

In §IX `Visualization`, key every independent data chart/pure text-grid table
in `kebab-case` and add one `Native-ready` map: `<key>=yes|no; ...`. Use `yes`
only when editable native output helps. Qualitative relationships/read order
remain unkeyed prose, as do incidental microvisuals.

In §VIII, author every planned or explicitly required resource from the confirmed source boundary. Write one concise, non-empty `Layout pattern` suggestion in ordinary language; optionally cite hierarchical ids from the layout library when they help recall a technique. Set `Crop Policy` to `adaptive` or `no-crop`; set `Acquire Via` to `ai`, `web`, `user`, `placeholder`, or `slice`. Preserve unresolved required assets as `Pending` or `Needs-Manual` instead of dropping or reclassifying them. Native formulas never enter this table or `spec_lock.md images`.

§VIII `Layout pattern` is a per-resource preference. When a page uses several images, repeats one image in multiple views, or combines an image with native overlays, describe the page-level relationship and participating resources in §IX `Layout` / `Images`; do not duplicate an unchanged resource row merely to encode animation sequencing.

Put native paint/overlay intent in §IX `Layout` plus `Images` for imagery—not a new field; state semantic job/layering, while Executor chooses type, stops, opacity, and geometry.

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
- **Mathematical content**: <exact expression as a delimiter-free LaTeX body; omit when none>

## X. Speaker Notes Requirements

- **Generation**: <enabled or disabled>
- **Filename**: match each SVG filename under `notes/`
- **Content**: <notes content and source-handling policy>
- **Total duration**: <resolved duration>
- **Notes style**: <formal, conversational, interactive, or resolved equivalent>
- **Presentation purpose**: <inform, persuade, inspire, instruct, report, or resolved combination>
```

When Speaker Notes is disabled, keep §X with only
`- **Generation**: disabled`; do not write filename, duration, style, or purpose
placeholders. An explicit notes-off/audio-on conflict blocks before authoring.

When an explicit final/literal narration script will become notes or generated
audio, make §X `Content` name that source and say `preserve verbatim`; keep the
full segmented script in `notes/total.md`, not in §IX or this Design Spec.

Append either or both optional lines only when the capability earns a place;
never write an empty or `none` placeholder:

```markdown
- **Native shape suggestion**: <semantic page/object geometry jobs plus independent atom roles, candidate preset/Connector family, or Boolean operation/operand roles as applicable>
- **Motion suggestion**: <communication job plus desired page-entry or reveal relationship/order>
```

Add `Mathematical content` whenever a Slide needs a mathematical expression preserved exactly. Store the expression body as valid LaTeX without `$...$`, `$$...$$`, `\(...\)`, or `\[...\]` source delimiters; the field does not classify inline versus structural use. This is content authority for [`native-formula.md`](../references/native-formula.md), not a formula policy, marker, or implementation request; Executor chooses ordinary text, inline native math, or block native math. Add `Visualization` / `Images` when a Slide consumes §VII/§VIII or uses a page-local visual model. Name every value-driven geometry, qualitative relationship, cell grid, and child visual here; only independent Chart/Table entries use object keys. Describe qualitative order, linkage, hierarchy, grouping, contrast, overlap, and reading path freely—not as a model name or grammar enum. §IX may choose a custom Chart/Table fallback. Add `Native shape suggestion` only when a page-level shape system, preset, stock Connector, or compound silhouette/cutout/intersection/fragment may help; name semantic geometry jobs and relationships plus independent atom roles, a candidate family, or Boolean operands as applicable, never implementation geometry or keys. Executor chooses the primitive, preset, independent compound construction, Boolean result, or necessary freeform. Add `Motion suggestion` whenever transition/reveal advice strengthens communication, regardless of the Custom Animations outcome; state purpose and semantic order/relationship, not registry keys, options, timing, ids, or coverage. The suggestion never activates animation execution by itself, creates content, or binds implementation. Describe required visible image states in `Layout` / `Images` only for an explicit motion requirement or an enabled Custom Animations outcome. Add keyed `Native-ready` only for independent data charts or pure text-grid tables, `Fact IDs` for sourced claims, and `Data class: scenario` for invented demo values. Except on preservation paths, `Cover impact` carries a binding hook and adaptable composition; apply the same split to `Closing impact` only when the deck genuinely resolves. Roster/order/content stay authoritative. §VIII image layout is non-empty free prose with optional library ids; §VII Chart/Table rows are references. Executor owns geometry, hierarchy, treatment, and sparse local garnish.

For free-design pages, describe `Layout` through relationships, hierarchy, regions, and column spans; do not prescribe element-level `x`, `y`, `width`, or `height` or duplicate the global geometry in §II/§V. Exact coordinates belong to Executor SVG authoring. Preserve literal geometry only when the user explicitly requires it or a mirror/template preservation contract owns it.

---

## 3. Machine validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reads the Markdown directly. It reports missing or out-of-order I–X sections, unresolved `[fill...]` placeholders, missing per-slide `Audience move`, and a missing §III `AI Image Strategy` when an §VIII table selects `ai` acquisition.

The schema validates structure only. Strategist role modules own field meaning, recommendation logic, page planning, image policy, and template policy. `spec_lock.md` owns stable execution anchors and routing selected in context; it is not an exhaustive value projection. On divergence, repair the Design Spec from the retained final state when Gate 1 fails, then re-author affected lock anchors from the audited Design Spec and current context. Never reopen `result.json` merely to author or validate the lock, and never use the lock to overwrite a valid Design Spec decision.
