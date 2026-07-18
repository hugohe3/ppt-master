# Execution Lock Structure

`spec_lock.md` is a compact Markdown data contract. Its machine contract is [`schemas/spec_lock.schema.json`](./schemas/spec_lock.schema.json); authoring starts from [`scaffolds/spec_lock.md`](./scaffolds/spec_lock.md).

## 1. Create the artifact

Run the scaffold command once, then fill or remove placeholder data lines:

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
| `communication` | `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife` | Values may be empty after explicit confirmation; `consumption_mode` is optional off PPT canvases |
| `mode` | `mode` | Preset or `custom` |
| `visual_style` | `visual_style` | Preset or `custom` |
| `colors` | Used color roles | `image_rendering` appears only for AI images |
| `typography` | `font_family`, `body`, `title` | Sizes are unitless numbers |
| `icons` | `library`, `inventory` | `stroke_width` is conditional |
| `page_rhythm` | One `P<NN>` row per page | Values: `anchor`, `dense`, `breathing` |
| `pptx_structure` | `mode` | Values: `flat`, `structured` |
| `forbidden` | Literal list items | General standards stay in their owning reference |

Optional data sections: `images`, `page_charts`.

---

## 3. Conditional sections and fields

| Trigger | Required addition |
| --- | --- |
| `mode.mode: custom` | `mode_behavior` in `mode` |
| `visual_style.visual_style: custom` | `visual_style_behavior` in `visual_style` |
| `colors.image_rendering: custom` | `image_rendering_behavior` in `colors` |
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

- `font_family` grammar: one PPT-safe family name; role-specific families may extend it in the same section.
- `image_rendering` grammar: one catalog id, or `custom` with `image_rendering_behavior`.
- `stroke_width` grammar: `1.5`, `2`, or `3`; present only for `tabler-outline`.
- `page_rhythm` grammar: `P` + at least two digits (`P01`, `P100`) followed by `anchor|dense|breathing`.
- `page_charts` grammar: `P` + at least two digits followed by a `charts_index` key; the key and `<key>.svg` must both exist.
- `pptx_masters` grammar: `<master_key>: <PowerPoint picker name>`.
- `pptx_layouts` grammar: `<layout_key>: <master_key> | <PowerPoint layout name> | <prototype source>`.
- `page_pptx_layouts` grammar: `P` + at least two digits followed by a declared Layout key.
- `page_layouts` grammar: `P` + at least two digits followed by a template SVG basename.

---

## 5. Machine Validation

```bash
python3 skills/ppt-master/scripts/project_manager.py validate <project_path>
```

Validation reads the existing Markdown form. It reports unresolved `[fill...]` scaffold placeholders, wrong section or field casing, unknown sections or fields, illegal declared enums, malformed page keys, catalog keys without their corresponding SVG asset, broken structured-layout references, and unmet required / forbidden conditional sections. It does not rewrite the lock and is not an automatic generation gate.

Field meaning and selection logic stay in the owning Strategist modules. Executor branch references own consumption behavior. The schema owns only artifact grammar and structural conditions.
