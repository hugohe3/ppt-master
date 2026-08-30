# Execution Lock Structure

`spec_lock.md` projects cross-page anchors and routes from the audited `design_spec.md` and context; it excludes local paint/type. This file owns structure; [`schemas/spec_lock.schema.json`](./schemas/spec_lock.schema.json) owns grammar.

## 1. Author the complete artifact

After Generate Step 4 Gate 1, read the completed Design Spec and current page/resource/template context, compose the entire lock in active context, and create `<project_path>/spec_lock.md` once. **Mandatory — new-project write**: the first non-empty line is exactly `<!-- ppt-master-schema: spec-lock/v1 -->`, then `# Execution Lock`; write only final sections and values — no blank lock, inactive optional sections, or scaffold placeholders (`project_manager.py scaffold-lock` is an optional troubleshooting tool); never reopen or reinterpret final confirmation. Repair a credible completed pair by re-projecting only the affected rows after auditing the Design Spec; discard an orphan lock as authority and re-author it completely from the recovered Design Spec.

**Hard rule**: a lock contains only `##` sections and `- key: value` lines, except `## forbidden`, whose items are literal rules; never copy guidance paragraphs into it.

---

## 2. Base sections

| Section | Required keys | Notes |
| --- | --- | --- |
| `canvas` | `viewBox`, `format` | `format` is the canonical display name (e.g. `PPT 16:9`); `viewBox` the exact geometry |
| `communication` | `primary_language`, `audience`, `objective`, `core_message` | Canonical BCP-47 (reject `und` and Chinese without script/region; old locks may omit it); `objective` merges intent/outcome; `consumption_mode` optional off PPT |
| `mode` | `mode` | Preset or `custom` |
| `visual_style` | `visual_style` | Preset or `custom` |
| `colors` | Stable semantic color roles | Core identity and recurring roles only, including `secondary_text` and `divider`; contextual paints need no row; `image_rendering` only for AI images |
| `typography` | `font_family`, `body`, `title` | Core family/size anchors; new locks also write `title_family` and `body_family`; sizes are unitless px |
| `icons` | `library`, `inventory` | `library` is the primary bundled style or `none`; `simple-icons/*` may be prepared alone or alongside it; `inventory` indexes the curated synced pool, not page usage or every usable project icon; `stroke_width` conditional |
| `page_rhythm` | One `P<NN>` row per page | `anchor`, `dense`, `breathing` |
| `pptx_structure` | `mode` | `flat`, `structured` |
| `forbidden` | Literal list items | The technical baseline rows stay untagged; every other row is a prohibition the user stated in their own words (request, chat, `image_notes`), quoted verbatim and ending with `(user)`; nothing else enters — general standards stay in their owning reference, a template's rules stay in its installed spec, and a confirmed `visual_style_behavior` binds as identity prose without becoming a lock row |

Optional data sections: `images`, `page_visualizations` (Chart/Table only). New locks never write legacy `page_charts` (existing locks may keep it read-only); never declare one page in both.

```markdown
## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
- 不要用任何阴影和发光 (user)
```

A `(user)` row is the user's sentence, not a paraphrase and never widened; a Strategist-drafted direction — even once confirmed — is identity prose in `visual_style_behavior`, not a prohibition, so nothing is projected from it into this section. `project_manager.py validate` rejects an untagged non-baseline row.

---

## 3. Conditional sections and fields

| Trigger | Required addition |
| --- | --- |
| `mode.mode: custom` | `mode_behavior`; optional `mode_references` only when catalog modes are used |
| `visual_style.visual_style: custom` | `visual_style_behavior`; optional `visual_style_references` |
| `colors.image_rendering: custom` | `image_rendering_behavior`; optional `image_rendering_references` |
| `icons.library: tabler-outline` | `stroke_width: 1.5`, `2`, or `3` |
| `pptx_structure.mode: structured` | `template_reuse_scope: layout\|mirror`, `template_adherence`, plus `pptx_masters`, `pptx_layouts`, `page_pptx_layouts`, `page_layouts` |
| `template_reuse_scope: mirror` | `mode: structured` and `template_adherence: strict` |
| `template_reuse_scope: style` | `mode: flat`; omit structured sections |
| `pptx_structure.mode: flat` | Omit all four structured sections |

```markdown
## pptx_masters
- master-default: Default Master

## pptx_layouts
- content-two-column: master-default | Two Column | template:03_content

## page_pptx_layouts
- P01: content-two-column

## page_layouts
- P01: 03_content

## page_visualizations
- P03: chart/line_chart
- P09: table/record_table
```

Project each §VII row into at most one `page_visualizations` `<chart|table>/<key>` row per page, resolved to one live SVG; Usage, children, no-match, and qualitative relationships stay in §IX; the reference locks neither type, geometry, nor native output. **Legacy compatibility**: existing `page_charts` bare keys resolve uniquely across the two live registries; retired Structure keys are semantic-only with no SVG; dual page declarations conflict even when they resolve alike.

Typography projection (excluding Character/upgrade References): Title font stack → `title_family`; Body font stack → `body_family` plus compatibility `font_family`; each additional recurring role `<role>` → `<role>_family`; each Font Size Hierarchy role → lowercase snake_case `<role>` with its numeric anchor. New locks always write `title_family` and `body_family` even when equal; omit only family roles that inherit without an override; old locks fall back to `font_family`. Executor may use the anchor or a value within `±2px`; a short non-structural Hero/Display size may stay absent only while the same undeclared value appears at most twice — its third occurrence needs a named role.

---

## 4. Field Grammar Index

- `font_family`, `title_family`, `body_family`, and every `<role>_family`: one non-empty PPT-safe exported family stack; `font_family` is the body/default compatibility stack, not permission to erase role differences.
- Every non-family `typography` value: a positive finite unitless px anchor; intermediate values within `±2px` need no row; a third occurrence of an undeclared Hero/Display size or any structural use requires Design Spec repair and a named anchor.
- `icons.library`: `chunk-filled`, `tabler-filled`, `tabler-outline`, `phosphor-duotone`, or `none`; `simple-icons/*` marks may appear alone or alongside in `inventory` without becoming a library or confirmation choice; every SVG under `<project_path>/icons/` remains valid material; illustrated-icon slices create no icon field — their paths belong under `images`, and the unplaced sheet stays out.
- `objective`: one concise sentence preserving goal and audience success condition.
- `image_rendering`: one catalog id, or `custom` with `image_rendering_behavior`.
- `images`: `- <key>: <path> | source=<via> | crop=<adaptive|no-crop>` (e.g. `- p04: images/a.png | source=user | crop=no-crop`); canonical `images/<filename>` path; `source` and `crop` project §VIII exactly; `Layout pattern` is not projected (Executor reads it from §VIII as a recommendation); a legacy `pattern=<layout>` segment is accepted; omit unplaced sheets.
- Custom reference fields: comma-separated exact catalog ids without duplicates, valid only for `custom`; omit for a genuinely novel direction.
- `stroke_width`: `1.5`, `2`, or `3`, only for `tabler-outline`.
- `page_rhythm`: `P` + at least two digits (`P01`, `P100`) followed by `anchor|dense|breathing`.
- `page_visualizations`: `P` + at least two digits followed by `chart|table`, `/`, and one canonical key resolving to one SVG through the matching live index. Legacy `page_charts`: `P` + at least two digits and one bare key; never added to a new lock.
- `pptx_masters`: `<master_key>: <PowerPoint picker name>`. `pptx_layouts`: `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`. `page_pptx_layouts`: `P` + at least two digits followed by a declared Layout key. `page_layouts`: `P` + at least two digits followed by a complete Slide template SVG basename; definition-only `layout_<layout_key>` files are obsolete and invalid as sources.

```markdown
## mode
- mode: custom
- mode_references: pyramid, narrative, instructional
- mode_behavior: Open conclusion-first with pyramid, develop the risk through a narrative tension-and-resolution act, then close with an instructional action sequence.
```

---

## 5. Machine Validation

`python3 skills/ppt-master/scripts/project_manager.py validate <project_path>` reports unresolved `[fill...]` placeholders, wrong casing, unknown sections or fields, illegal enums, malformed page keys, missing catalog assets, broken structured-layout references, and unmet conditions; it neither rewrites the lock nor checks semantic projection (Gate 2 does). Field meaning stays in the Strategist modules; Executor branches own consumption; the schema owns grammar and structural conditions only.

## 6. Anchor and extension semantics

Confirmed core palette roles and every declared typography family/size role are stable cross-page anchors. Page-local tints, gradient stops, shadow/glow paints, transparency composites, and one-off export-safe display families may be authored from context without a row. Executor may adjust one occurrence within its size role's `±2px` band. When a contextual value becomes a recurring semantic role, or an undeclared display size reaches its third occurrence, add the descriptive role, read back and validate affected planning fragments, then reuse it; structural typography outside its band returns upstream immediately. Never expand the lock merely to empty an informational checker comparison — a lock edit expresses reuse or identity, not incidental literals.
