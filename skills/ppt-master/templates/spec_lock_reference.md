# Execution Lock Structure

`spec_lock.md` is the compact execution contract authored from an audited `design_spec.md` and the current project context. It keeps stable cross-page anchors and routing values; it is not an exhaustive allowlist of every color, gradient stop, effect paint, or typeface that a page may use. After confirmation fidelity passes, start from [`scaffolds/spec_lock.md`](./scaffolds/spec_lock.md); [`schemas/spec_lock.schema.json`](./schemas/spec_lock.schema.json) owns its grammar.

## 1. Create the artifact

After Generate Step 4 Gate 1, run once and author the execution anchors from the Design Spec plus current page/resource/template context:

```bash
python3 skills/ppt-master/scripts/project_manager.py scaffold-lock <project_path>
```

The command refuses to overwrite an existing `spec_lock.md`. Re-running it with the same project metadata produces the same bytes.

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
| `typography` | `font_family`, `body`, `title` | Core family/size anchors; sizes are unitless numbers |
| `icons` | `library`, `inventory` | `stroke_width` is conditional |
| `page_rhythm` | One `P<NN>` row per page | Values: `anchor`, `dense`, `breathing` |
| `pptx_structure` | `mode` | Values: `flat`, `structured` |
| `forbidden` | Literal list items | General standards stay in their owning reference |

Optional data sections: `images`, `page_charts`.

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

`page_charts` values must exist as keys in `charts/charts_index.json`; pages using the explicit `no-template-match` result do not appear there.

---

## 4. Field Grammar Index

- `font_family` grammar: one non-empty PPT-safe exported family stack; role-specific families may extend it in the same section.
- `objective` grammar: one concise sentence preserving the deck goal and audience success condition.
- `image_rendering` grammar: one catalog id, or `custom` with `image_rendering_behavior`.
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

- Confirmed core palette roles and structural title/body typography remain stable cross-page anchors.
- Page-local tints, gradient stops, shadow/glow paints, transparency composites, and one-off export-safe display families may be authored from context without adding a lock row.
- When a contextual value becomes a recurring semantic role, add one descriptive `colors` or `*_family` row and regenerate page-context before later pages use that role.
- Do not expand the lock merely to make an informational checker comparison empty. A lock edit should express reuse or identity, not enumerate incidental literals.
