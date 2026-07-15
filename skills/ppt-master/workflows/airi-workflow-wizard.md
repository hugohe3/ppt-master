---
description: Run the AIRI v2 local wizard for multi-source intake, style selection, analysis-pack generation, and editable page-outline confirmation
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

**Manual pack selection**: Never auto-enable an analysis pack. When the user selects one, compile its Excel source and generate every enabled row before outline review:

```bash
python3 ${SKILL_DIR}/scripts/analysis_pack.py compile <pack_dir>/pack.xlsx
python3 ${SKILL_DIR}/scripts/analysis_pack.py build-manifest <pack_dir>/pack.json <project_path> --reference <image>
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
```

Use `--dry-run` on the final command to validate multipart request construction without credentials or network access.

**Gate**: When `workflow_selection.json analysis_pack_id` is non-empty, every manifest item must be `Generated` before final outline confirmation.

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
          "filename": "analysis_massing.png",
          "analysis_pack_id": "architecture-placeholder",
          "analysis_item_id": "massing-analysis",
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
