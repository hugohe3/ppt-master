# Execution Lock Structure

`spec_lock.md` is the compact execution contract from audited `design_spec.md` plus current context. It keeps stable cross-page anchors and routes, not every page-local paint or typeface. This file owns authoring structure; [`schemas/spec_lock.schema.json`](./schemas/spec_lock.schema.json) owns grammar.

## 1. Author the complete artifact

After Generate Step 4 Gate 1, read the completed Design Spec and current page/resource/template context, compose the entire lock in active context, then create `<project_path>/spec_lock.md` once.

**Mandatory — new-project write**: The first non-empty line is exactly `<!-- ppt-master-schema: spec-lock/v1 -->`, followed by `# Execution Lock`. Write only final sections and values; do not create a blank lock, copy inactive optional sections, or patch scaffold placeholders. Do not reopen final confirmation or interpret it independently.

`project_manager.py scaffold-lock` remains an optional manual convenience and overwrite-safe troubleshooting tool. It is not part of normal Generate authoring. When a credible completed Design Spec/lock pair needs correction, repair only the affected projection after auditing the Design Spec. When the Design Spec was missing and an orphan lock survived, discard that lock as authority and re-author the complete lock from the recovered, audited Design Spec plus current context.

**Hard rule**: A project lock contains only `##` sections and `- key: value` data lines, except `## forbidden`, whose list items are literal rules. Do not copy guidance paragraphs into the lock.

---

## 2. Base sections

| Section | Required keys | Notes |
| --- | --- | --- |
| `canvas` | `viewBox`, `format` | `format` is the canonical display name (for example `PPT 16:9`); `viewBox` is the matching exact geometry |
| `communication` | `audience`, `objective`, `core_message` | Compact execution projection; `objective` combines intent and audience outcome; `consumption_mode` is optional off PPT canvases |
| `mode` | `mode` | Preset or `custom` |
| `visual_style` | `visual_style` | Preset or `custom` |
| `colors` | Stable semantic color roles | Core identity and recurring roles only; contextual SVG paints need no row; `image_rendering` appears only for AI images |
| `typography` | `font_family`, `body`, `title` | Core family/size anchors; new locks also write explicit `title_family` and `body_family`; size anchors are unitless px numbers |
| `icons` | `library`, `inventory` | `library` is the Strategist's primary bundled style choice or `none`; `simple-icons/*` may be selected alone or accompany it; `inventory` records the planned bundled selection rather than all usable project-local icons; `stroke_width` is conditional |
| `page_rhythm` | One `P<NN>` row per page | Values: `anchor`, `dense`, `breathing` |
| `pptx_structure` | `mode` | Values: `flat`, `structured` |
| `forbidden` | Literal list items | General standards stay in their owning reference |

Optional data sections: `images`, `page_charts`.

The required universal block is:

```markdown
## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
```

---

## 3. Conditional sections and fields

| Trigger | Required addition |
| --- | --- |
| `mode.mode: custom` | `mode_behavior` in `mode`; optional `mode_references` only when catalog modes are actually used |
| `visual_style.visual_style: custom` | `visual_style_behavior` in `visual_style`; optional `visual_style_references` only when catalog styles are actually used |
| `colors.image_rendering: custom` | `image_rendering_behavior` in `colors`; optional `image_rendering_references` only when catalog renderings are actually used |
| `icons.library: tabler-outline` | `stroke_width: 1.5`, `2`, or `3` |
| `pptx_structure.mode: structured` | `template_reuse_scope: layout\|mirror`, `template_adherence`, plus `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, and `page_layouts` |
| `pptx_structure.template_reuse_scope: mirror` | `mode: structured` and `template_adherence: strict` |
| `pptx_structure.template_reuse_scope: style` | `mode: flat`; omit structured mapping sections |
| `pptx_structure.mode: flat` | Omit all four structured mapping sections |

Structured section value shapes:

```markdown
## pptx_masters
- master-default: Default Master

## pptx_layouts
- content-two-column: master-default | Two Column | template:03_content

## page_pptx_layouts
- P01: content-two-column

## page_layouts
- P01: 03_content
```

Project each §VII `Page | Template | Usage` row's first two fields into `page_charts`; Usage stays in the Design Spec. This is a page-local reference, not a type/geometry lock. Keys must exist in `charts/charts_index.json`; no-match stays in §IX.

Typography projection is role-for-role, not a lossy summary:

| Design Spec §IV declaration | `spec_lock.md` field |
| --- | --- |
| Title font stack | `title_family` |
| Body font stack | `body_family` and compatibility/default `font_family` |
| Any additional recurring font role `<role>` | `<role>_family` |
| Every Font Size Hierarchy role `<role>` | lowercase `<role>` with its numeric anchor |

New locks always write `title_family` and `body_family`, even when their values happen to match. Every additional recurring family row and every size-anchor row in the Design Spec must appear under the same lowercase snake_case role; omit only family roles that inherit without an explicit override. Existing locks without family-role fields remain readable through `font_family` fallback. Executor may choose the anchor or a value within that role's `±2px` band; the lock does not enumerate intermediate values. A short non-structural Hero/Display size may remain absent only while the same undeclared value appears at most twice across the deck; its third occurrence requires a named role.

---

## 4. Field Grammar Index

- `font_family`, `title_family`, `body_family`, and every optional `<role>_family` use one non-empty PPT-safe exported family stack. `font_family` is the body/default compatibility stack, not permission to erase role differences.
- Every non-family `typography` value is a positive finite unitless px anchor. Intermediate values need no lock row when they stay within the mapped role's anchor `±2px`. At most two occurrences of one undeclared short non-structural Hero/Display size may remain sparse; a third occurrence or any structural use requires Design Spec repair and a named anchor.
- `icons.library` records the primary stylistic library selected from `chunk-filled`, `tabler-filled`, `tabler-outline`, or `phosphor-duotone`, or `none` when no generic bundled icons are selected. Selected `simple-icons/*` brand marks may appear alone or alongside it in `inventory` without becoming a stylistic library. The inventory records planned bundled choices, while every SVG already under `<project_path>/icons/` remains valid prepared execution material.
- `objective` grammar: one concise sentence preserving the deck goal and audience success condition.
- `image_rendering` grammar: one catalog id, or `custom` with `image_rendering_behavior`.
- `images`: `- <key>: <path> | source=<via> | pattern=<layout> | crop=<adaptive|no-crop>`; e.g. `- p04: images/a.png | source=user | pattern=#2 Left image | crop=no-crop`. Omit unplaced sheets.
- Custom reference grammar: comma-separated exact catalog ids with no duplicates. Reference fields are valid only for `custom`; omit them for a genuinely novel direction.
- `stroke_width` grammar: `1.5`, `2`, or `3`; present only for `tabler-outline`.
- `page_rhythm` grammar: `P` + at least two digits (`P01`, `P100`) followed by `anchor|dense|breathing`.
- `page_charts` grammar: `P` + at least two digits followed by a `charts_index` key; the key and `<key>.svg` must both exist.
- `pptx_masters` grammar: `<master_key>: <PowerPoint picker name>`.
- `pptx_layouts` grammar: `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`.
- `page_pptx_layouts` grammar: `P` + at least two digits followed by a declared Layout key.
- `page_layouts` grammar: `P` + at least two digits followed by a template SVG basename.

Catalog-based custom example:

```markdown
## mode
- mode: custom
- mode_references: pyramid, narrative
- mode_behavior: Lead each act with the decision-first clarity of pyramid, then develop it through a narrative tension-and-resolution arc.
```

---

## 5. Machine Validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reports unresolved `[fill...]` placeholders, wrong casing, unknown sections or fields, illegal enums, malformed page keys, missing catalog assets, broken structured-layout references, and unmet conditions. It neither rewrites the lock nor checks semantic projection; Generate Step 4 Gate 2 owns that check.

Field meaning and selection logic stay in the owning Strategist modules. Executor branch references own consumption behavior. The schema owns only artifact grammar and structural conditions.

## 6. Anchor and extension semantics

- Confirmed core palette roles and every declared typography family/size role remain stable cross-page anchors.
- Page-local tints, gradient stops, shadow/glow paints, transparency composites, and one-off export-safe display families may be authored from context without adding a lock row.
- Executor may adjust one occurrence within its declared size role's anchor `±2px` while preserving hierarchy and readability; intermediate values are realization choices, not new lock rows.
- When a contextual value becomes a recurring semantic role, or one undeclared display size reaches its third occurrence, add the descriptive role, read back and validate affected planning fragments, then reuse it. Structural typography outside its applicable anchor band returns upstream immediately.
- Do not expand the lock merely to make an informational checker comparison empty. A lock edit should express reuse or identity, not enumerate incidental literals.
