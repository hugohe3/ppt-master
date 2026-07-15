# Analysis Prompt Packs

Use analysis packs to turn one or more project reference images into a repeatable set of generated diagrams before page-outline confirmation.

## 1. Library Contract

| File | Role |
|---|---|
| `templates/analysis-packs/analysis_packs_index.json` | Discovery list shown by the v2 wizard |
| `<pack-id>/pack.xlsx` | Human-edited source of truth |
| `<pack-id>/pack.json` | Validated runtime compilation |

**Hard rule**: Edit Excel, then compile. Do not hand-edit `pack.json` as the durable source.

---

## 2. Excel Columns

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

## 3. Reference-Image Manifest

Build every enabled row into the standard image manifest:

```bash
python3 ${SKILL_DIR}/scripts/analysis_pack.py build-manifest \
  <pack_dir>/pack.json <project_path> \
  --reference <project_path>/images/project_render.png \
  --profile gptimage2.0-1K-low
```

New per-item fields:

| Field | Role |
|---|---|
| `reference_images` | Paths resolved relative to `images/image_prompts.json` |
| `provider_profile` | Named backend/model/size/quality mapping |
| `analysis_pack_id` | Source pack provenance |
| `analysis_item_id` | Source Excel row provenance |

The initial `gptimage2.0-1K-low` profile maps to `asiai-edit`, `gpt-image-2`, 1K, low quality, and multipart `image[]` uploads to `/v1/images/edits`.

---

## 4. Execution and Recovery

```bash
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json --dry-run
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
```

`--dry-run` writes `image_prompts.request.redacted.json` and performs no credential lookup or network request. Real execution writes one `<filename>.generation.json` record per output without storing API keys or base64 response bodies.

**Capability gate**: A manifest row with `reference_images` fails before API execution when the selected backend has no `reference-image-edit` capability.
