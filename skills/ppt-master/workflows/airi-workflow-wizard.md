---
description: Run the AIRI v2 local wizard for multi-source intake, two-level analysis-image selection, and editable page-outline confirmation
---

# AIRI Workflow Wizard

Run the local wizard when the user wants a visual intake-to-outline workflow before formal PPT generation.

## 1. Launch

Initialize a normal PPT Master project, then launch the shared Confirm UI server in wizard mode:

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format ppt169
python3 ${SKILL_DIR}/scripts/confirm_ui/server.py <project_path> --wizard --daemon
```

**Hard rule**: Keep the chat fallback valid. If the page cannot open, create and confirm the same artifacts through chat and the CLI tools below.

---

## 2. Intake and Source Synthesis

| Artifact | Owner | Contract |
|---|---|---|
| `source_manifest.json` | `intake_manifest.py` | Deterministic file inventory, hashes, duplicates, roles, and available assets |
| `source_synthesis.json` | Strategist | Relationships, shared facts, conflicts, existing structure, and source-backed summary |
| `template_request.json` | Wizard intake | Uploaded PPT style-reference request; page count is not preserved |

After every upload, run:

```bash
python3 ${SKILL_DIR}/scripts/intake_manifest.py <project_path>
```

**Mandatory**: Replace `source_synthesis.json status: pending-ai` with `status: ready` after reading normalized source content and machine facts. Keep source ids in relationship/conflict records.

**Uploaded PPT style reference**: Follow [`create-template.md`](./create-template.md) using `template_request.json`, write the temporary package to `<project>/templates/custom-upload/`, and keep `preserve_page_count: false`.

---

## 3. Style and Analysis Images

Complete the existing three-stage direction/design/image confirmation at `/confirm`. Persist the wizard choices to `workflow_selection.json`.

**Two-level analysis selection**: Compile the one-style-per-sheet Excel source, then require one analysis style plus one or more analysis type ids. Keep the selected type ids when the user switches style.

```bash
python3 ${SKILL_DIR}/scripts/analysis_library.py compile <library_dir>/prompts_master.xlsx
python3 ${SKILL_DIR}/scripts/analysis_library.py build-manifest \
  <library_dir> <project_path> \
  --style <style-id> --item <analysis-type-id> --reference <image>
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
```

Use `--dry-run` on the final command to validate the selected provider request without credentials or network access.

Provider profiles:

- `gptimage2.0-1K-mid` — default; GPT Image 2 reference edit, 1K, medium quality.
- `nanobanana-pro-2K` — Gemini 3 Pro Image / Nano Banana Pro, Google GenAI `generateContent + inline_data`, 2K.
- `gptimage2.0-1K-low` — legacy compatibility only.

**Gate**: When `workflow_selection.json analysis_item_ids` is non-empty, every selected type must be `Generated` under the current `analysis_style_id` before final outline confirmation.

**Legacy compatibility**: Existing flat `analysis_pack_id` projects continue through `analysis_pack.py`; do not expose that path as the default v2 selector.

---

## 4. Editable Page Outline

Strategist writes `<project>/outline_draft.json` after generated analysis images are available. Use this minimum page shape:

```json
{
  "schema_version": 2,
  "pages": [
    {
      "page_id": "P01",
      "title": "Project title",
      "core_message": "One page, one message",
      "body": "Final page copy",
      "images": [
        {
          "source": "analysis-pack",
          "filename": "ARC-010__arch_massing_study__light_fresh_ppt_detailed.png",
          "analysis_library_id": "diagram-prompt-building-v1",
          "analysis_style_id": "light_fresh_ppt_detailed",
          "analysis_domain_id": "architecture",
          "analysis_item_id": "ARC-010",
          "prompt": "...",
          "reference_images": ["project_render.png"]
        }
      ]
    }
  ]
}
```

The page supports add/delete/reorder, copy edits, image replacement, prompt edits, and single-image regeneration.

Confirm only after the user finishes editing:

```bash
python3 ${SKILL_DIR}/scripts/outline_gate.py confirm <project_path>
python3 ${SKILL_DIR}/scripts/outline_gate.py check <project_path>
```

**Hard gate**: Any draft edit invalidates `outline_confirmed.json`. Do not write SVG, start Executor live preview, or export PPTX until `outline_gate.py check` passes.

---

## 5. Handoff to the Main Pipeline

After confirmation, copy the confirmed page content and image mapping into `design_spec.md Section IX`, then generate `spec_lock.md` from the same page order. Continue with the existing Executor, quality, post-processing, and export steps.

Do not add an AI-concept disclaimer to the generated analysis images or slide copy. Keep provider/profile/pack provenance only in project JSON artifacts.
