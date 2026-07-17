---
description: Run the mandatory new/restructured-deck intake, style, professional-analysis, content-inventory, and sourced page-outline confirmation workflow
---

# AIRI Content Planning Wizard

Use this workflow for every new or restructured deck. Fixed-page `template-fill`, strict 1:1 `beautify`, and `native-enhance` retain their own route boundaries.

## 1. Intake and Reusable Selection Assets

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format ppt169
```

Import files, URLs, text, existing outlines, and style-reference PPTX files. Persist audience, objective, canvas, delivery purpose, content-divergence notes, color/typography notes, and the **performance-image policy** (cover / decorative / photographic only) in `workflow_brief.json`.

Run `intake_manifest.py` after every source change. Source changes invalidate the content inventory and outline confirmation through the planning-input fingerprint.

Use the prebuilt chat assets by default:

- `assets/contact-sheets/ppt_visual_styles.png` (SVG fallback: `.svg`)
- `assets/contact-sheets/analysis_visual_styles.png` (SVG fallback: `.svg`)
- `assets/contact-sheets/analysis_domains.md`

When a source catalog or preview changes, rebuild once with `python3 ${SKILL_DIR}/scripts/build_contact_sheets.py`. Do not start a website for routine selection. The browser wizard is opt-in only when the user explicitly requests interactive browser editing.

## 2. Blocking Decision 1: Visual Style and Professional Analysis

### Visual style

- Show the reusable numbered PPT-style contact sheet. Its order is generated from `catalogs.json`, so the user may reply with either the visible number or the style id.
- Badge the Strategist recommendation but do not preselect it.
- A user click records `visual_style_source: user`.
- "随便" / equivalent or continuing without a click applies the recommendation and records `visual_style_source: auto`.
- Keep a Custom card and store its prose in `custom_style_description`.

### Explicit professional-analysis decision

Require `analysis_required: true | false`; a missing domain never means No.

- **False**: clear analysis style/domain/type/reference fields, skip professional-analysis generation, and continue to content inventory.
- **True**: show the reusable numbered analysis-style contact sheet and the four entries from `assets/contact-sheets/analysis_domains.md`. Require one style, exactly one user-facing domain, the analysis library id, optional reference images, and a provider profile. Do not show the detailed type catalog. Strategist resolves the source-specific internal type ids after the user confirms; if none are supplied, the runtime uses the domain's curated default set. Generate only through `analysis_library.py` + `image_gen.py`.

Write schema-v4 `workflow_selection.json` with `analysis_domain_id`, internal `analysis_item_ids`, `analysis_selection_confirmed`, and `analysis_selection_hash`. Changing style, domain, derived type set, reference image, provider profile, or the professional-analysis decision invalidates downstream artifacts.

## 3. Analysis Generation and Content Inventory

Every analysis style must have a preview declared by the compiled library. The seven current previews use the same residential massing example for fair comparison.

When analysis is required:

```bash
python3 ${SKILL_DIR}/scripts/analysis_library.py build-manifest \
  <library_dir> <project_path> --style <style-id> --item <type-id> --reference <image>
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json --dry-run
python3 ${SKILL_DIR}/scripts/image_gen.py --manifest <project_path>/images/image_prompts.json
```

Do not proceed until every selected item is `Generated`, the manifest carries the current `analysis_selection_hash`, and every output file exists.

Then synthesize all source facts, user images, generated analysis images, actual sizes/aspect ratios, full/half/combined placement recommendations, copy blocks, and density into `analysis/content_inventory.json`. Save through `POST /api/workflow/content-inventory` so the server adds the current `planning_input_hash`.

Required inventory fields:

```json
{
  "recommended_page_count": 12,
  "page_count_rationale": ["3 full-page analysis diagrams", "3 residential renders", "balanced presentation density"],
  "source_facts": [],
  "images": [],
  "content_blocks": []
}
```

Page count is first surfaced here. Never ask the user to lock it before this point.

## 4. Blocking Decision 2: Sourced Page Outline

Create schema-v3 `outline_draft.json` only from the current content inventory. `len(pages)` is the working page count.

Each page requires `page_id`, `title`, `core_message`, `body`, non-empty `source_refs`, and an `images` array. Every image entry requires `source`. The wizard supports add/delete/reorder, copy edits, image replacement, prompt edits, and single-image regeneration.

Any outline edit deletes the old confirmation. Any source/style/analysis/generated-file change makes the inventory and confirmation stale.

Confirm and check:

```bash
python3 ${SKILL_DIR}/scripts/outline_gate.py confirm <project_path>
python3 ${SKILL_DIR}/scripts/outline_gate.py check <project_path>
```

Only after `check` reports `generation unlocked` may Strategist copy the confirmed page order/content/image mapping into `design_spec.md` Section IX and `spec_lock.md`, then start Executor.

## 5. Browser Compatibility

Chat contact sheets are the default. If the user explicitly asks for an interactive browser surface, `confirm_ui/server.py --wizard` may present the same ordered decisions. Browser availability never changes the gate order, and early page-count confirmation remains forbidden.

Schema-v3 compatibility is read-only: existing analysis selections infer `analysis_required: true`; old projects with no analysis selection infer false and expose `analysis_requirement_legacy_inferred: true`. New projects must write schema v4. Legacy flat analysis packs remain executable but are not the default selector.
