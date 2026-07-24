# Confirm UI — Strategist Confirmation Stage Page

> The interactive, visual surface for [`generate-pptx`](../../workflows/generate-pptx.md) Step 4. Stage 1 is an open communication brief: common purpose paths are prompt text, never checkboxes or a forced single label. Stage 2 offers **≥3 coordinated design directions** and then exposes their component values for deliberate override; color, typography, icons, and generated-image rendering are one system rather than unrelated grids. When a template workspace is active, Stage 2 also shows one editable natural-language template-application plan—never internal mode controls. Generated images inherit the selected deck colors directly—there is no image-palette control. Stage 3 contains production mechanics only. The AI uses one `recommendations.stageN.json` file per stage; the active, unconfirmed stage may be overwritten when the user requests a new recommendation. Confirmed values accumulate into `result.json`. Final confirm saves the result and shuts the server down. The chat path mirrors the same staged semantics.

## Authority and Scope

| Concern | Owner |
|---|---|
| Step 4 gate and pipeline order | [`generate-pptx.md`](../../workflows/generate-pptx.md) |
| Confirm UI schema | This document |
| Stage 1 / Stage 2 / Stage 3 field membership | This document |
| Server launch / wait / shutdown behavior | This document |
| Port and lock behavior | This document |
| Chat fallback equivalence | This document |
| Confirmed-value precedence | [`generate-pptx.md`](../../workflows/generate-pptx.md) plus this document's `result.json` contract |

**Hard rule**: Keep detailed Confirm UI behavior here. The Generate route may summarize orchestration, but it should not duplicate the full JSON schema, catalog behavior, or launcher lifecycle.

**Fallback rule**: The page is default. Use chat only on explicit chat-only request or launch failure/timeout after one `result.json` re-check; a chat-question tool is not a launch failure. Preserve all three stages and keep Stage-1 prompts open-ended.

## `confirm_ui/server.py`

```bash
python3 scripts/confirm_ui/server.py <project_path> --daemon --wait   # launch + wait for Stage 1
python3 scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage2  # Stage 2: wait for the direction handoff
python3 scripts/confirm_ui/server.py <project_path> --wait-only       # Stage 3: wait for the final result
python3 scripts/confirm_ui/server.py <project_path> --daemon
python3 scripts/confirm_ui/server.py <project_path> --daemon --port 5051
python3 scripts/confirm_ui/server.py <project_path> --no-browser
python3 scripts/confirm_ui/server.py <project_path> --timeout 0   # disable idle auto-shutdown
python3 scripts/confirm_ui/server.py <project_path> --shutdown    # Step 4 cleanup (idempotent)
```

- Binds `127.0.0.1:5050` by default — or the next free port if another project already holds it (the launch log prints the actual URL) — and auto-opens the browser (suppress with `--no-browser`). `--port <other>` forces a specific port.
- In `--daemon` mode the launcher starts the child server with browser opening suppressed, waits for `GET /api/health` to prove the server is accepting requests, then opens the printed `http://127.0.0.1:<port>` URL. If health never becomes reachable, the command fails before presenting a dead page.
- **Shares port 5050 with the live preview server** (`svg_editor/server.py`). The two never run at once: confirm is Step 4, live preview is Step 6, and Step 4 always shuts this server down on exit (see `--shutdown`) so the port is free. One port = one forward rule for the whole pipeline. They still keep **separate processes and locks** (`.confirm_ui.lock` vs `.live_preview.lock`).
- `--daemon` starts the Flask process in the background; add `--wait` in the main pipeline so the parent command returns only after the page writes a fresh `result.json`. The `--wait` budget defaults to **590 s** (`--wait-timeout`), kept under the typical 600 s tool ceiling — run the launch with a long tool timeout (≈600000 ms). On timeout the parent returns non-zero but the detached server keeps running, so the caller must re-check `result.json` once before the chat fallback (a slow user may confirm just after the wait returns).
- `--wait-only` attaches to the page already running from the first `--daemon --wait` and blocks until the page writes the requested stage. If the recorded server died, it automatically restarts on the recorded/default port so polling reconnects. Use `--wait-stage stage2` for the complete-solution handoff, then the default `--wait-stage final` for Stage 3. It keys on stage alone (no mtime gate), because a user may submit before the wait command starts.
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. Generate Step 4 runs this on every path (page-confirm or chat-fallback) so the page never lingers on the shared port before live preview starts.
- Refuses to start unless the recommendation file expected from `result.json` exists (initially `<project_path>/confirm_ui/recommendations.stage1.json`; `--shutdown` needs no recommendations).
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.
- `/api/recommendations` and `/api/confirm` strip legacy `template_reuse_scope` and `template_adherence` fields. Those exporter values are never user-facing controls; an active template instead exposes the editable natural-language `template_application` field in Stage 2.

Dependency:

```bash
pip install flask
```

## Field shapes

- **Enumerable + custom** — canvas / icons retain blank manual inputs; mode / visual_style instead show a mandatory AI-authored proposal in full, initially unselected and editable after selection. Selected mode / style writes literal `custom` plus its behavior sibling.
- **Visual examples for hard-to-name choices** — the full-screen confirmation page loads real SVG page samples from `static/style_previews/` for `visual_style`, and renders real sample SVGs from `templates/icons` for `icons`. These thumbnails make style and icon-library choices visually comparable before the user locks them. Preview copy is fixed role text (big title / section title / body / points), not project content from recommendation files, so users compare visual treatment rather than copywriting. These previews are a confirmation aid only: they do not add fields to recommendation stage files or `result.json`, and they do not replace the later Step 6 live preview.
- **Image usage multi-select** — image sources are selected as one or more catalog ids: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. `none` is exclusive. A confirmed non-`none` set is the allowed acquisition-source boundary, not a requirement to use every selected source; only explicit `image_notes` wording can require a source, asset, or page role. Recommendation and result values may be a legacy single string, but new files should use an array. When several sources are recommended, write the source ids to `recommend.image_usage` and write the actual usage strategy to `image_notes`, not a custom prose value.
- **Closed enumerable** — PPT reading mode (`delivery_purpose` compatibility key), formula policy / generation mode / refine spec, plus AI source only when image usage includes `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option.
- **Open prose** — `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, `content_divergence`, and `page_count`. `communication_intent` may carry several purposes plus priority / sequence; common paths appear only as help text. `content_divergence` is the source-treatment axis. `page_count` may be a range here; Strategist resolves the exact §IX roster, leaving Executor no pagination latitude.
- **Coordinated generative directions** — `design_directions` carries ≥3 safe / shifted / bold candidates. Each candidate bundles visual style, color, typography, icon id, and conditional generated-image rendering. The page can still render legacy top-level `color`, `typography`, and `image_strategy` candidates, but new staged recommendations use the coordinated bundle.

AI-authored custom proposals apply only to mode, visual style, and conditional AI-image rendering; a selected proposal cannot be blank. Color / typography keep their existing manual Custom cards. Image usage uses source ids plus `image_notes`; closed sets have no Custom path.

**Stage-1 current-value contract.** Each editable prose box starts with the Strategist's recommendation, if one exists. The user may retain, revise, or clear it; no Stage-1 prose field has a non-empty validation gate. On confirmation, the browser submits the current strings and the server preserves them through every later stage and the final `result.json`, including `""`. Blank means no explicit user constraint and may cause downstream default judgment, but it never causes the initial recommendation to be restored. A profile-declared `locked: true` field is read-only and remains the sole exception.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` includes `ai`. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while trilingual labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `icons`, `image_usage`, `image_ai_path`, `formula_policy`, `generation_mode`, `delivery_purpose`. Each entry is `{ "id", "label", "label_zh", "label_en", "label_ja", ... }`; descriptions use `desc_zh` / `desc_en` / `desc_ja`, and `visual_styles` groups use `group_zh` / `group_en` / `group_ja`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must cover all three languages (zh / en / ja). English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `mixed`, etc.); Chinese and Japanese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_en", "group_ja", "items": [...] }]`. For `canvas` you only need to maintain the trilingual labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

Round-trip and session files live under `<project_path>/confirm_ui/`.

### Three-stage flow

The page runs as a **three-stage wizard in one browser session**. Each stage has its own Strategist-authored file and top-level `"stage"` selector. The active, unconfirmed stage may be overwritten any number of times when the user asks for a better recommendation; refresh the page to load the replacement. Once the user confirms it, normal progression writes the next stage file rather than repurposing the previous one. The server derives the active filename from `result.json`.

| Recommendation file | Declared stage | Page renders | Button | On submit |
|---|---|---|---|---|
| `recommendations.stage1.json` | `"stage1"` | communication contract — audience; open `communication_intent`; audience outcome; core message / delivery context / artifact afterlife / `content_divergence` (all prose fields may be blank); canvas | **Confirm contract & continue** | writes `result.json` `{ stage: "stage1", status: "stage1-confirmed", <communication contract> }`; the page stays open and polls |
| `recommendations.stage2.json` | `"stage2"` | complete deck solution — conditional natural-language template application, reading mode, mode, page count, visual direction, color, icons, typography, image usage, generated-image rendering | **Confirm solution & continue** | writes `result.json` `{ stage: "stage2", status: "stage2-confirmed", <contract + solution> }`; the page stays open and polls |
| `recommendations.stage3.json` | `"stage3"` | production only — confirmed image-source summary, conditional AI acquisition path, formula policy, generation mode, refine spec | **Confirm** | writes `result.json` `{ stage: "final", status: "confirmed", <all fields> }`, then shuts the page down |
| `recommendations.json` | stage or legacy no-stage payload | read-only compatibility when no stage-specific file exists | matching legacy behavior | preserves the former staged or single-pass behavior; new projects never create this file |

The AI launches Stage 1, authors the complete Stage-2 solution once from the user's actual contract, then authors Stage-3 production mechanics once from the confirmed solution. An edit inside the current stage never requests another recommendation. The page preserves earlier answers across transitions. `GET /api/session` is the waiting-state endpoint; `GET /api/recommendations` is `no-store`, and the server folds confirmed earlier-stage choices back into later payloads so refresh / reopen restores the user's actual values—including Stage-2 color, typography, icon, image-source, and rendering choices. Once any stage-specific file exists, the server ignores legacy `recommendations.json` to prevent mixed lifecycles.

**Stage progression guard.** Stages confirm strictly in order. `/api/confirm` accepts only the submit stage matching the active filename and its required predecessor; the declared `stage` must also match the filename. A later file that skips ahead (for example `recommendations.stage3.json` while only Stage 1 is confirmed and Stage 2 is absent) is never rendered: `/api/session` keeps reporting `waiting_agent` with `stage_skip: true`, and `--wait` / `--wait-only` exit `2` if a result skips the stage being awaited. An active template does not exempt Stage 2: its recommendations must include `template_application.value`, and an installed workspace or that field disables the no-stage legacy single-pass path. Legacy single-pass remains available only for non-template compatibility payloads.

### Input — `recommendations.stage1.json` (created by Strategist before launch)

```json
{
  "stage": "stage1",
  "lang": "zh",
  "recommend": {
    "canvas": "ppt169"
  },
  "audience": { "value": "公司管理层，包括财务与产品负责人" },
  "communication_intent": {
    "value": "先汇报进展并暴露交付风险，再推动管理层决定下一阶段投入"
  },
  "audience_outcome": {
    "value": "管理层能比较三个选项、接受风险判断，并选定一条获得预算的路径"
  },
  "core_message": {
    "value": "现在为方案 B 增加投入，能以可接受的成本守住发布时间"
  },
  "delivery_context": {
    "value": "管理层现场评审 20 分钟，有主讲；会后分享录屏和文件"
  },
  "artifact_afterlife": {
    "value": "作为审批记录、项目交接依据和季度审计材料"
  },
  "content_divergence": { "value": "" }
}
```

All seven Stage-1 prose values may be blank and none blocks confirmation. The values shown in the boxes are editable recommendations; the submitted current values are authoritative, so clearing a box writes and retains `""`. A preservation profile may lock an open field, for example `"content_divergence": { "value": "keep source wording and page structure verbatim", "locked": true }`; the browser renders it read-only. The server carries that lock through the intermediate results and restores the value on every staged submit; the internal carry-over marker is removed from the final `result.json`.

The common paths — inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off — appear only as help text for `communication_intent`. They are not catalog ids and must not be emitted as a `primary_job` field.

After Stage 1 is confirmed, create `recommendations.stage2.json` with the complete solution; leave Stage 1 unchanged (the server folds confirmed communication fields back in when serving the page):

```json
{
  "stage": "stage2",
  "lang": "zh",
  "recommend": {
    "delivery_purpose": "balanced",
    "mode": "pyramid",
    "visual_style": "swiss-minimal",
    "image_usage": ["ai", "provided"]
  },
  "page_count": { "value": "12-15" },
  "template_application": {
    "value": "选用封面、章节页和数据页原型；跳过示例内容页。品牌标识和页脚保留，正文可按当前材料重组。"
  },
  "image_notes": { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材。" },
  "custom_candidates": {
    "mode": {
      "name_zh": "冲突到决策",
      "behavior_zh": "先建立业务冲突，再用结论先行结构推动决策。"
    },
    "visual_style": {
      "name_zh": "编辑批注风",
      "behavior_zh": "严格栅格配合边注和证据强调。"
    },
    "image_strategy": {
      "name_zh": "证据拼贴",
      "rendering": "custom",
      "visual_zh": "纸面证据拼贴",
      "mood_zh": "审慎可信",
      "behavior_zh": "裁切纸面配少量批注，保持平面深度并继承演示色板。"
    }
  },
  "design_directions": {
    "selected": 0,
    "candidates": [
      {
        "name_zh": "稳妥专业",
        "note_zh": "像成熟咨询简报",
        "visual_style": "swiss-minimal",
        "icons": "tabler-outline",
        "color": { "name_zh": "冷静专业", "palette": {
          "background": "#FFFFFF", "secondary_bg": "#F4F6F8",
          "primary": "#1A3A6B", "accent": "#E8A317",
          "secondary_accent": "#4A7BB5", "body_text": "#1D2430"
        } },
        "typography": {
          "name_zh": "清晰无衬线",
          "heading": { "cjk": "Microsoft YaHei", "latin": "Arial", "css": "sans-serif" },
          "body": { "cjk": "Microsoft YaHei", "latin": "Arial", "css": "sans-serif" },
          "body_size": 24
        },
        "image_strategy": {
          "name_zh": "克制矢量",
          "rendering": "vector-illustration",
          "visual_zh": "扁平矢量、实色块、少阴影",
          "mood_zh": "稳定、可信、克制"
        }
      }
    ]
  }
}
```

The example abbreviates the required ≥3 directions. Custom mode/style candidates remain mandatory; AI usage also requires the custom image candidate. Stage 2 rejects fewer than three bundles, incomplete six-role palettes, and incomplete heading/body stacks. Legacy grids remain readable only with three complete palettes and complete typography.

After Stage 2 is confirmed, create `recommendations.stage3.json` with production recommendations only; leave both earlier files unchanged:

```json
{
  "stage": "stage3",
  "lang": "zh",
  "recommend": {
    "image_ai_path": "auto",
    "formula_policy": "mixed",
    "generation_mode": "continuous"
  },
  "refine_spec": { "value": false }
}
```

- `recommend.*` names each recommended id. New mode / style values use a catalog id or literal `custom`; arbitrary prose values are legacy-only. Use `recommend.image_strategy: "custom"` only when an explicit user-supplied image direction should start selected. Missing recommendations fall back to the normal preset. Legacy aliases remain accepted; new files write canonical ids.
- `custom_candidates` is recommendation-only. Mode / style carry localized `name` + `behavior`; conditional image strategy also carries `rendering: "custom"`, `visual`, and `mood`. When a proposal combines or borrows existing catalog entries, the visible behavior names every exact id and Strategist reads every corresponding file before authoring it; a genuinely novel proposal names none. The server rejects missing required candidates; the UI shows full copy, edits it only after selection, rejects a selected blank, and omits unselected candidates from `result.json`. Template-backed proposals obey inherited identity, prototype capacity, and `template_application`.
- `audience`, `communication_intent`, and `audience_outcome` are load-bearing Stage-1 reasoning inputs, so seed concrete recommendations when the evidence supports them; they are not required user inputs. Every Stage-1 prose field may be blank after confirmation. The complete six-field contract stays in `result.json` and `design_spec.md`; `spec_lock.md communication` receives only the compact `audience` / `objective` / `core_message` execution projection plus the applicable reading mode. `communication_intent` may preserve several purposes plus priority / sequence; never add a `primary_job` enum.
- Do not write `recommend.template_reuse_scope` or `recommend.template_adherence`. Strategist records those internal exporter values later in `spec_lock.md` after inspecting the actual template and current content.
- For an active template workspace, write one editable prose field as top-level `template_application.value`. It summarizes actual page/prototype use and preservation/reorganization decisions. Omit it for free design. The UI returns the current string through Stage 2, Stage 3, and final confirmation; Strategist then persists the final effective plan as `- **Template Application**: ...` in `design_spec.md §I`, which Executor reads from the retained Design Spec. Never replace it with internal reuse/adherence ids or a fixed option menu.
- `recommend.image_usage` should be an array of source ids when more than one source applies, e.g. `["ai", "provided"]`. A single string is still accepted for backward compatibility. Do not write bare `"custom"` and do not encode a mixed-source plan as prose here; write the prose to top-level `image_notes.value`.
- `image_notes` is the initial strategy note shown under the image source chips. Use it for page-role guidance and constraints: which source applies where, what to avoid, which user assets are authoritative, how realistic / abstract the imagery should be, and what can remain as placeholders. It is intent guidance, not a separate finite option.
- When confirmed Stage-2 `image_usage` includes `ai`, Stage 3 sets `recommend.image_ai_path` to one of `auto` / `api` / `host-native` / `manual`. Stage 2 never asks for the acquisition mechanism while the user is still deciding the image role.
- **Color candidates carry the user-facing core `palette`**: `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, and `body_text`. The page renders every role as a labelled swatch with its HEX value visible, and offers per-role override inputs for precise single-role edits, plus a **Custom color card with a free-text box** (parallel to the custom typography box) — the user can describe the palette in words or paste HEX values instead of filling each role; this writes `color: { "name": "custom", "custom": "<text>" }` to `result.json` for the AI to interpret. Legacy `text` is accepted as an alias for `body_text`, but new files should write `body_text`. Strategist derives secondary text, borders, state colors, and visual-style neutral tiers while writing `design_spec.md`, then projects the machine values to `spec_lock.md`; those are not user-facing confirmation choices.
- **Candidate display text may be multilingual**: color / typography candidates can provide `name_zh` / `name_en` / `name_ja` and `note_zh` / `note_en` / `note_ja`; the page falls back to legacy `name` / `note`. Labels resolve in the page language first, then fall back across the others (a `ja` page: ja → en → zh; zh/en pages keep their zh↔en fallback and try `_ja` last), so when `lang` is `ja` always include the `_ja` variants — otherwise the candidate labels render in English.
- **Typography candidates split CJK and Latin** for both `heading` and `body`; `css` is the fallback preview stack. Each candidate includes topic-matched sample text. Stage 2 is authored once with a reading-mode baseline of `text` 20 · `balanced` 24 · `presentation` 32 px on PPT. Font cards choose family / character and preserve the current sizing state; they do not introduce a competing size recommendation. The page writes px directly. `delivery_purpose` remains the compatibility key only.
- **Per-role size override** (parallel to color's per-role HEX override): besides `body_size`, the page exposes editable inputs for `title` / `subtitle` / `annotation`. The browser applies one documented deterministic dependency chain: `reading mode → body baseline → unpinned role sizes` (role ramp: `body ×` the §g ratios). Changing reading mode updates the body and all unpinned roles locally; changing body updates unpinned roles locally. Editing body or a role pins that value, so later reading-mode changes do not overwrite it. Font / direction-card selection preserves all current sizes. This is a browser-only state update: it performs no fetch, asks the backend to author no new recommendations, and a re-render preserves exactly what the user sees. Each role input is labelled as px and shows an approximate pt equivalent (`1px = 0.75pt`) for orientation. The final values are written to `result.json` as `typography.sizes: { "title", "subtitle", "annotation" }` in **px** — every canvas, no pt and no `sizes_pt` provenance. These confirmed values are Strategist input anchors: the completed page plan may add recurring roles, and downstream execution owns bounded per-occurrence treatment. Candidate `sizes` remain accepted for compatibility, but the fresh Stage-2 baseline is normalized through the same local ramp before first render.
- **`delivery_purpose` compatibility key / Reading mode** (enumerable, PPT only) decides where meaning is carried, not merely how large type is: `text` makes pages self-contained with complete sentences, short prose, captions, tables, and necessary detail; `balanced` shares explanation between page and presenter; `presentation` uses one idea, concise claims, and visual evidence while speech / notes carry the detail. It therefore governs page grammar, granularity, density / rhythm, and note burden. Reading-mode cards intentionally show **no px value**; the typography section owns the separately visible body / role sizes and applies any local default. It is surfaced in Stage 2 beside the visual system, separate from communication intent. `recommend.delivery_purpose` pre-selects one; `result.json` retains the key, while `spec_lock.md` uses canonical `consumption_mode`. Non-PPT canvases omit it.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated-image direction** appears only for `image_usage: ai`: up to three preset cards plus one full-width AI custom proposal. Custom has no preset dropdown; selection makes it editable and submits `rendering: "custom"` + `behavior`. If that behavior uses catalog renderings, it visibly names their exact ids; Strategist retains that confirmed basis as optional `image_rendering_references` in `spec_lock.md`. A genuinely novel behavior produces no reference row. The live preview follows the selection. No image palette is written; deck colors remain authoritative, and legacy `image_strategy.palette` is ignored.
- **`design_directions`** is the canonical Stage-2 spectrum: ≥3 safe / shifted / bold bundles with localized copy, style, icons, conditional image strategy, complete CJK/Latin typography, and HEX `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, `body_text`. Selection applies the bundle; component controls override it. `result.json` stores components, not a direction id.
- `recommend.generation_mode` and `refine_spec` mirror the two mandatory notes in [`generate-pptx`](../../workflows/generate-pptx.md) Step 4. Confirmed `generation_mode: "split"` / `refine_spec: true` are explicit user choices, equivalent to opting in through chat.
- `content_divergence` is a **free-text** Stage-1 source-treatment field. Blank means a balanced default; facts stay sourced at every level. Strategist consumes it while authoring §IX and records it in `design_spec.md §I`; it is not written to `spec_lock.md`. Beautify sends `{ "value": "keep source wording and page structure verbatim", "locked": true }`, so the UI displays it read-only and the server restores it on every staged submit. Template-fill does not use this confirmation flow and does not surface it.
- `lang` is a soft default (`zh` / `en` / `ja` — the page UI supports all three); an explicit user language choice in the page (persisted to `localStorage`) wins.

### Output — `result.json` (written on submit, read by the AI)

```json
{
  "canvas": "ppt169",
  "page_count": "12-15",
  "audience": "...",
  "communication_intent": "Report progress and expose risk first; then obtain an investment decision",
  "audience_outcome": "The committee compares the options and chooses one funded path",
  "core_message": "Fund option B now to protect the launch date at acceptable incremental cost",
  "delivery_context": "Presenter-led 20-minute leadership review; recording shared afterward",
  "artifact_afterlife": "Approval record, hand-off reference, and audit trail",
  "content_divergence": "freely restructure and expand within the source",
  "template_application": "选用封面、章节页和数据页原型；跳过示例内容页。品牌标识和页脚保留，正文可按当前材料重组。",
  "mode": "pyramid",
  "visual_style": "swiss-minimal",
  "color": { "name": "...", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
  "icons": "tabler-outline",
  "typography": { "name": "...", "heading": { "cjk": "...", "latin": "...", "css": "..." }, "body": { "cjk": "...", "latin": "...", "css": "..." }, "body_size": 24, "body_size_unit": "px", "sizes": { "title": 42, "subtitle": 32, "annotation": 18 } },
  "delivery_purpose": "balanced",
  "formula_policy": "mixed",
  "image_usage": ["ai", "provided"],
  "image_notes": "封面和章节页用 AI 主视觉；产品页优先用户素材，缺口页可用占位符。",
  "image_ai_path": "auto",
  "image_strategy": { "name": "方案 A", "rendering": "vector-illustration", "visual": "...", "mood": "..." },
  "generation_mode": "continuous",
  "refine_spec": false,
  "stage": "final",
  "status": "confirmed",
  "confirmed_at": "2026-06-15T11:44:44"
}
```

The shape above is final. Selected custom values use `mode: custom` + `mode_behavior`, `visual_style: custom` + `visual_style_behavior`, or `image_strategy.rendering: custom` + `behavior`. During Design Spec and lock authoring, Strategist projects optional `mode_references`, `visual_style_references`, or `image_rendering_references` only when that confirmed behavior actually uses named catalog sources; genuinely novel custom behavior has no reference list. Intermediate writes retain accumulated fields; legacy tier names remain read-compatible.

**Final-result consumption contract.** A final result is the user-confirmed input contract for the Strategist's Design Spec, not another recommendation input. After the final wait, Generate Step 4 reads the complete final object exactly once and retains it while Strategist writes and audits `design_spec.md` against every explicitly present field. Normal lock authoring and downstream execution do not reopen `result.json`; the completed Design Spec is the durable authority. Only after that audit passes does Strategist author `spec_lock.md` from the Design Spec plus current execution context, selecting stable anchors and routing rather than copying every field or enumerating every legal color/font. Every value must be consumed at the semantic type owned by [`strategist.md`](../../references/strategist.md) §1 and its field owner: do not omit or substitute it, and do not silently strengthen or weaken its type. If a confirmed requirement cannot be honored, the owning workflow reports or pauses under failure recovery; it never deletes the requirement to keep the pipeline moving.

- Bespoke mode / style prose lives only in the required behavior sibling; image custom prose lives in `image_strategy.behavior`. Canvas / icons retain free-text edge cases, color / typography retain `name: "custom"`, and image usage remains a source-id array plus `image_notes`.
- `image_ai_path` and `image_strategy` appear only with `image_usage: ai` and remain confirmed downstream. The page is default; explicit/failure chat fallback keeps identical fields. `image_ai_path` selects the Step 5 path, and [`strategist-image.md`](../../references/strategist-image.md) §2 retains the selected rendering or custom behavior as the deck-level image identity anchor; individual prompts still adapt subject, composition, and atmosphere within it.
- After the user clicks the **final Confirm** (Stage 3, or single-pass), the page saves `result.json` and shuts the server down (auto-close). Stage-1 **Confirm contract & continue** and Stage-2 **Confirm solution & continue** keep the page open while it polls for the downstream stage file. In the default flow, the first `--daemon --wait` returns on the stage-1 result, `--wait-only --wait-stage stage2` returns on the stage-2 result, and the final `--wait-only` returns on the final result; the AI reads each immediately — no extra chat confirmation is required. Chat fallback shows the same initially-unselected custom proposals. Either way, Step 4 ends with a `--shutdown` cleanup so a never-confirmed page cannot keep holding port 5050 ahead of the Step 6 live preview.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/stages/live-preview.md`, Step 6).
