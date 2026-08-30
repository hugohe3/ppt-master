# Design Spec Structure

Project-level `design_spec.md` is a human-readable English-heading Markdown artifact. This file owns its authoring structure; [`schemas/design_spec.schema.json`](./schemas/design_spec.schema.json) lints readable sections and page projection — it is not an execution lock and requires no textual equality with `spec_lock.md`. Strategist reads the final confirmation once, writes this artifact from that retained state plus source analysis, and audits every confirmed field here; `spec_lock.md` is then authored from the completed Design Spec plus context without reopening `result.json`.

## 1. Author the complete artifact

Compose the entire document in active context, then create `<project_path>/design_spec.md` once, first line through §X. **Depth follows the confirmed `design_spec_depth`** — `brief` (default) or `complete`; both keep every required heading and machine-read field. `brief` serves a continuous run whose author also draws the pages: §I records production mechanics without restating Stage-1 prose, §VI may leave the scenario column empty, §IX `Content` is a short block list (one bullet per block in the phrasing that fits — a sentence for prose, `·`-joined parallel fragments, `/`-joined labels — never full copy), and `Layout` is one optional line; `Relationships` is written at both depths. `complete` writes full wording and layout prose; split mode, `refine_spec: true`, and preservation profiles force it.

**Mandatory — new-project write**: the first non-empty line is exactly `<!-- ppt-master-schema: design-spec/v1 -->`, then `# <Project Name> - Design Spec`; every required section carries final values and the complete roster; conditional §VII appears only with a real catalog reference. Never write a placeholder-bearing file, copy example rows, or patch a scaffold field by field (`project_manager.py scaffold-spec` is an optional manual troubleshooting tool, not part of Generate authoring; resume and refine edit the existing completed Design Spec).

---

## 2. Exact document contract

Angle-bracketed text is authoring notation. Resolve every universal value before writing; omit only rows marked conditional; keep every required `##` heading (§VII omitted without a catalog reference; §VIII present even with no data rows); copy no examples, notation, or schema prose into the artifact.

### 2.1 Header and project contract

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

With an active template workspace, append exactly one line after the §I table — `- **Template Application**: <confirmed or Strategist-resolved natural-language plan>` — never internal reuse/adherence ids; omit it for free design.

### 2.2 Visual, typography, layout, and icons

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
| Secondary text | <HEX> | <captions, annotations, footnotes> |
| Divider | <HEX> | <rules, borders, hairlines> |

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

### Deck-wide Direction

- **Hierarchy direction**: <how attention should move across a typical page>
- **Composition tendency**: <non-binding macro direction; no coordinates or authoring method>
- **Cross-page continuity**: <what may recur or vary across the roster>
- **Spacing posture**: <dense, open, or variable by page rhythm>
- **Spacing anchors**: <five deck-wide px values — page margin, block gap, column gutter, corner radius, body leading — kept stable like the color and type anchors>

## VI. Icon Usage Specification

- **Primary bundled library**: <one of chunk-filled / tabler-filled / tabler-outline / phosphor-duotone, or none>
- **Brand-logo library**: <simple-icons when actual content requires prepared real brand marks; omit otherwise>

| Icon Path | Suitable Scenarios |
| --- | --- |
```

Preserve Title/Body characters and resolved stacks; omit a blank Typography upgrade and never place it in a stack. Each justified recurring family override adds its role to Font Plan plus `- **<Role> stack**: <complete ordered stack>` (roles: `Annotation`, `Footer`, `Footnote`, `Data`, `Emphasis`, `Quote`, `Code` — only recurring, intentional differences; a non-locked `Role rationale` only for an extra family); never collapse distinct Title/Body stacks or drop a declared role. Each Font Size Hierarchy value is a role anchor Executor may vary by `±2px` per occurrence; a short non-structural Hero/Display size may stay unlisted only while planned at most twice — its third occurrence needs a named row. Record every recurring palette role and size anchor the plan establishes, never one-off garnish. For confirmed custom directions add `Mode References`, `Mode Behavior`, `Visual Style References`, and `Visual Style Behavior` under Theme Style as applicable. `Stroke Width` under §VI only for a stroke library. `simple-icons` accompanies the one primary library only when real brand marks are required and is never a separate confirmation choice. The §VI table records the synced SVG pool and, at `complete` depth, broad scenarios — never page placement; leave it empty when no bundled or brand icons are prepared. Other prepared SVGs under the project `icons/` remain usable without entering that selection. Illustrated icons are AI image resources: their sheet and placed slice rows belong in §VIII, and only placed slices project to `spec_lock.md images`.

When §VIII contains any `Acquire Via: ai` row, add under §III:

```markdown
### AI Image Strategy

- **Image Rendering**: <confirmed preset or custom>
- **Visual**: <confirmed visual treatment>
- **Mood**: <confirmed mood and analogy>
```

A custom rendering adds `Image Rendering Behavior`, and `Image Rendering References` only when catalog material is actually used; never a separate image palette.

### 2.3 Visualization and image resources

```markdown
## VII. Visualization Reference List

| Page | Family | Template | Usage |
| --- | --- | --- | --- |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

§VII lists at most one `chart|table` reference per page (canonical key plus semantic Usage; resolve `family/key`, never derive paths from bare keys; omit when empty; legacy rows stay readable, new specs use four columns). §IX owns child visuals and unmatched fallbacks in `Visualization`; qualitative relationships live only on the `Relationships` line; Layout/Deck alone owns reusable PowerPoint structure. In §IX `Visualization`, key every independent data chart or pure text-grid table in `kebab-case` and add one `Native-ready` map `<key>=yes|no; ...` — `yes` by default, `no` only when the native payload cannot express the object; qualitative relationships and incidental microvisuals stay unkeyed.

§VIII authors every planned or required resource from the confirmed source boundary: one concise non-empty `Layout pattern` suggestion in ordinary language (optionally citing hierarchical ids from the layout library; an image-led `adaptive` row names the page job the image resolves next to the composition serving it); `Crop Policy` `adaptive` or `no-crop`; `Acquire Via` `ai`, `web`, `user`, `placeholder`, or `slice`; unresolved required assets kept as `Pending` or `Needs-Manual`; native formulas never enter it. `Layout pattern` is per-resource — how several images relate on one page (repeated views, sequencing) is stated once in §IX `Images` as a Reference, never as duplicate rows; paint, overlay, and geometry are Executor's.

### 2.4 Complete page roster and notes

One ordered Slide block per page; count and order equal §I `Page Count`; `Content` is a complete brief at `complete` depth and a short block list at `brief` — never a skeleton.

```markdown
## IX. Content Outline

### Part 1: <section name>

#### Slide 01 - <page name>

- **Audience move**: <audience state before → after>
- **Relationships**: <the page's semantic units and the source-stated order / link / parent / membership / contrast / overlap among them, or none; no shape, carrier, or authoring words>
- **Layout**: <Reference — macro composition, hierarchy, and visual focus as a starting sketch; chosen prototype when template-active; optional at brief depth>
- **Title**: <preferred page title>
- **Core message**: <one governing assertion>
- **Content**: <complete content at complete depth; short block list at brief depth>
- **Mathematical content**: <exact expression as a delimiter-free LaTeX body; omit when none>

## X. Speaker Notes Requirements

- **Generation**: <enabled or disabled>
- **Filename**: match each SVG filename under `notes/`
- **Content**: <notes content and source-handling policy>
- **Total duration**: <resolved duration>
- **Notes style**: <formal, conversational, interactive, or resolved equivalent>
- **Presentation purpose**: <the confirmed communication intent from §I>
```

With Speaker Notes disabled, §X keeps only `- **Generation**: disabled`; an explicit notes-off/audio-on conflict blocks before authoring. When a final/literal narration script will become notes or audio, §X `Content` names the source and says `preserve verbatim`, with the segmented script kept in `notes/total.md`.

Optional Slide lines, added only when the capability earns a place (never an empty or `none` placeholder): `Mathematical content` (a valid delimiter-free LaTeX body — content authority for [`native-formula.md`](../references/native-formula.md), not a policy or marker; Executor chooses text, inline, or block); `Visualization` / `Images` when the Slide consumes §VII/§VIII or a page-local visual model, naming every value-driven geometry, cell grid, and child visual (only independent Chart/Table entries carry keys; qualitative relationships stay on the `Relationships` line, never a model name or grammar enum; §IX may choose a custom fallback; native construction is discovered by Executor, never a Design Spec field); `Motion suggestion` (purpose and semantic order/relationship, never registry keys, options, timing, ids, or coverage — it never activates execution, creates content, or binds implementation; required visible image states go in `Layout` / `Images` only for an explicit motion requirement or an enabled outcome); keyed `Native-ready`; `Fact IDs` for sourced claims; `Data class: scenario` for invented values. Except on preservation paths, `Cover impact` carries a binding hook and adaptable composition, and `Closing impact` the same split only when the deck genuinely resolves. Roster, order, content, and `Relationships` stay authoritative; §V/§IX layout, cover/closing composition, capability, motif, non-`ai` §VIII image-layout, and §VII directions are References — starting sketches Executor adjusts or replaces freely for the page's purpose, with no upstream repair or stated reason, carrying no binding semantics. When the user, a template, or a resource contract requires such a property, write `(binding)` after the field label (`- **Layout (binding)**:`) and Executor follows it literally. For free-design pages, `Layout` describes relationships, hierarchy, focus, and optional macro region/span suggestions — never element-level `x` / `y` / `width` / `height`, fixed gaps, or an authoring method; literal geometry is preserved only when the user requires it or a mirror/template contract owns it.

---

## 3. Machine validation

`python3 skills/ppt-master/scripts/project_manager.py validate <project_path>` reads the Markdown directly and reports missing or out-of-order I–X sections, unresolved `[fill...]` placeholders, missing per-slide `Audience move` or `Relationships` lines, and a missing §III `AI Image Strategy` when §VIII selects `ai`. The schema validates structure only; Strategist modules own meaning, and `spec_lock.md` owns stable anchors and routing, not an exhaustive projection. On divergence, repair the Design Spec from the retained final state when Gate 1 fails, then re-author affected lock anchors; never reopen `result.json` to author the lock or let the lock overwrite a valid Design Spec decision.
