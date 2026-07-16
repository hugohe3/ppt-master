# Analysis Prompt Packs

Use analysis packs to turn one or more project reference images into a repeatable set of generated diagrams before page-outline confirmation.

## 1. Two-Level Analysis Library

The AIRI wizard uses one Excel worksheet per image style. Every worksheet must contain the same analysis type ids, grouped into Architecture, Interior, Landscape, and Planning.

| File | Role |
|---|---|
| `templates/analysis-library/diagram-prompt-building/prompts_master.xlsx` | Human-edited source of truth |
| `styles.json` | First-level image-style catalog |
| `analysis_types.json` | Second-level type catalog grouped by domain |
| `prompt_matrix.json` | Validated style-by-type prompt lookup |

Each worksheet uses these source columns: `id`, `category_l1`, `category_l2`, `graphic_mode`, `style_id`, `style_label`, `style_tags`, `title`, `prompt_final`, `template_id`, and `notes`. The compiler rejects missing columns, unsafe or duplicate ids, mixed styles in one worksheet, and inconsistent type sets across styles.

```bash
python3 ${SKILL_DIR}/scripts/analysis_library.py compile \
  ${SKILL_DIR}/templates/analysis-library/diagram-prompt-building/prompts_master.xlsx
```

Build only the selected intersections:

```bash
python3 ${SKILL_DIR}/scripts/analysis_library.py build-manifest \
  ${SKILL_DIR}/templates/analysis-library/diagram-prompt-building \
  <project_path> \
  --style light_fresh_ppt_detailed \
  --item ARC-010 --item ARC-014 \
  --reference <project_path>/images/project_render.png
```

**Hard rule**: Keep style selection independent from type selection. Switching style preserves selected type ids and resolves new prompts from the matrix.

---

## 2. Legacy Flat-Pack Contract

| File | Role |
|---|---|
| `templates/analysis-packs/analysis_packs_index.json` | Discovery list shown by the v2 wizard |
| `<pack-id>/pack.xlsx` | Human-edited source of truth |
| `<pack-id>/pack.json` | Validated runtime compilation |

**Hard rule**: Edit Excel, then compile. Do not hand-edit `pack.json` as the durable source.

---

## 3. Legacy Excel Columns

| Column | Contract |
|---|---|
| `item_id` | Unique stable id within the pack |
| `category` | User-facing grouping |
| `name` | User-facing task name |
| `prompt_template` | Full image-edit instruction |
| `output_filename` | Unique image basename with PNG/JPG/JPEG/WEBP suffix |
| `aspect_ratio` | `image_gen.py` ratio |
| `image_size` | `512px` / `1K` / `2K` / `4K`; the first GPT Image profile supports `1K` |
| `enabled` | Boolean execution switch |
| `reference_role` | Expected source role such as `project-render` |
| `notes` | Maintainer note, not sent to the provider |

Compile and validate:

```bash
python3 ${SKILL_DIR}/scripts/analysis_pack.py compile <pack_dir>/pack.xlsx
```

Duplicate ids, duplicate outputs, missing columns, invalid filenames, and empty prompts fail before any API call.

---

## 4. Reference-Image Manifest

Build every enabled row into the standard image manifest:

```bash
python3 ${SKILL_DIR}/scripts/analysis_pack.py build-manifest \
  <pack_dir>/pack.json <project_path> \
  --reference <project_path>/images/project_render.png \
  --profile gptimage2.0-1K-mid
```

New per-item fields:

| Field | Role |
|---|---|
| `reference_images` | Paths resolved relative to `images/image_prompts.json` |
| `provider_profile` | Named backend/model/size/quality mapping |
| `analysis_pack_id` | Source pack provenance |
| `analysis_library_id` | Two-level library provenance |
| `analysis_style_id` | First-level image-style selection |
| `analysis_domain_id` | Architecture / Interior / Landscape / Planning group |
| `analysis_item_id` | Source Excel row provenance |
| `analysis_template_id` | Stable semantic template id |

The default `gptimage2.0-1K-mid` profile maps to `asiai-edit`, `gpt-image-2`, 1K, medium quality, and multipart `image[]` uploads to `/v1/images/edits`. Select `nanobanana-pro-2K` for Gemini 3 Pro Image through Google GenAI `generateContent + inline_data` with 2K output. The legacy GPT low profile remains valid for existing manifests.

---

## 5. Execution and Recovery

```bash
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json --dry-run
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
```

`--dry-run` writes `image_prompts.request.redacted.json` and performs no credential lookup or network request. Real execution writes one `<filename>.generation.json` record per output without storing API keys or base64 response bodies.

**Capability gate**: A manifest row with `reference_images` fails before API execution when the selected backend has no `reference-image-edit` capability.
