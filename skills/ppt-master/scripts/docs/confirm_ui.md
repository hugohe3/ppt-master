# Confirm UI — Strategist Confirmation Stage Page

> The interactive, visual surface for SKILL.md Step 4. Stage 1 is an open communication brief: common purpose paths are prompt text, never checkboxes or a forced single label. Stage 2 offers **≥3 coordinated design directions** and then exposes their component values for deliberate override; color, typography, icons, and generated-image rendering are one system rather than unrelated grids. Generated images inherit the selected deck colors directly—there is no image-palette control. Stage 3 contains production mechanics only. The AI writes `recommendations.json`; confirmed values accumulate into `result.json`. Final confirm saves the result and shuts the server down. The chat path mirrors the same staged semantics.

## Authority and Scope

| Concern | Owner |
|---|---|
| Step 4 gate and pipeline order | `SKILL.md` |
| Confirm UI schema | This document |
| Stage 1 / Stage 2 / Stage 3 field membership | This document |
| Server launch / wait / shutdown behavior | This document |
| Port and lock behavior | This document |
| Chat fallback equivalence | This document |
| Confirmed-value precedence | `SKILL.md` plus this document's `result.json` contract |

**Hard rule**: Keep detailed Confirm UI behavior here. `SKILL.md` may summarize the orchestration, but it should not duplicate the full JSON schema, catalog behavior, or launcher lifecycle.

**Fallback rule**: Browser failure never cancels Step 4. Re-check `result.json` once, then use the chat confirmation path with the same three-stage semantics. Stage-1 chat prompts remain open questions; do not turn the hint vocabulary into a numbered selection.

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
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. SKILL.md Step 4 runs this on every path (page-confirm or chat-fallback) so the page never lingers on the shared port before live preview starts.
- Refuses to start unless `<project_path>/confirm_ui/recommendations.json` exists (except `--shutdown`, which needs no recommendations).
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.
- `/api/recommendations` derives `_template_reuse_scope_enabled`, `_template_adherence_enabled`, and `_template_replication_mode` from `<project>/templates/design_spec.md` frontmatter. Stage 1 always suppresses both controls because template use is derived only after the communication contract; from Stage 2 onward, only `kind: deck` / `kind: layout` enables them. No template and `kind: brand` force both off even if stale recommendations contain them. The server defaults reuse scope to `layout`, exposes `mirror` only for `replication_mode: mirror`, defaults adherence to `adaptive` for `mirror` / `layout`, and removes adherence for `style`.

Dependency:

```bash
pip install flask
```

## Two kinds of field

- **Enumerable + custom** — canvas / mode / visual_style / icons. The page lists common options from `static/catalogs.json`, badges the AI's recommendation, and still offers a Custom box for edge cases.
- **Visual examples for hard-to-name choices** — the full-screen confirmation page loads real SVG page samples from `static/style_previews/` for `visual_style`, and renders real sample SVGs from `templates/icons` for `icons`. These thumbnails make style and icon-library choices visually comparable before the user locks them. Preview copy is fixed role text (big title / section title / body / points), not project content from `recommendations.json`, so users compare visual treatment rather than copywriting. These previews are a confirmation aid only: they do not add fields to `recommendations.json` or `result.json`, and they do not replace the later Step 6 live preview.
- **Image usage multi-select** — image sources are selected as one or more catalog ids: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. `none` is exclusive. Recommendation and result values may be a legacy single string, but new files should use an array. When several sources are recommended, write the source ids to `recommend.image_usage` and write the actual usage strategy to `image_notes`, not a custom prose value.
- **Closed enumerable** — PPT reading mode (`delivery_purpose` compatibility key), template reuse scope + adherence (conditional), formula policy / generation mode / refine spec, plus AI source only when image usage includes `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option.
- **Open prose** — `audience`, `communication_intent`, `audience_outcome`, `core_message`, `delivery_context`, `artifact_afterlife`, `content_divergence`, and `page_count`. `communication_intent` may carry several purposes plus priority / sequence; common paths appear only as help text. `content_divergence` remains a separate source-treatment axis.
- **Coordinated generative directions** — `design_directions` carries ≥3 safe / shifted / bold candidates. Each candidate bundles visual style, color, typography, icon id, and conditional generated-image rendering. The page can still render legacy top-level `color`, `typography`, and `image_strategy` candidates, but new staged recommendations use the coordinated bundle.

**Custom box** appears only on fields whose universe is genuinely open — `canvas`, `mode`, `visual_style`, and `icons`. Image usage uses a multi-select source list plus `image_notes` instead of a Custom box. Fully closed sets — `template_reuse_scope`, `template_adherence`, `image_ai_path`, `formula_policy`, `generation_mode`, `refine_spec` — have **no** Custom box; an out-of-catalog value there is snapped back to the recommended option.

**Stage-1 current-value contract.** Each editable prose box starts with the Strategist's recommendation, if one exists. The user may retain, revise, or clear it; no Stage-1 prose field has a non-empty validation gate. On confirmation, the browser submits the current strings and the server preserves them through every later stage and the final `result.json`, including `""`. Blank means no explicit user constraint and may cause downstream default judgment, but it never causes the initial recommendation to be restored. A profile-declared `locked: true` field is read-only and remains the sole exception.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` includes `ai`. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while trilingual labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `template_reuse_scope`, `template_adherence`, `icons`, `image_usage`, `image_ai_path`, `formula_policy`, `generation_mode`, `delivery_purpose`. Each entry is `{ "id", "label", "label_zh", "label_en", "label_ja", ... }`; descriptions use `desc_zh` / `desc_en` / `desc_ja`, and `visual_styles` groups use `group_zh` / `group_en` / `group_ja`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must cover all three languages (zh / en / ja). English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `mixed`, etc.); Chinese and Japanese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_en", "group_ja", "items": [...] }]`. For `canvas` you only need to maintain the trilingual labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

Round-trip and session files live under `<project_path>/confirm_ui/`.

### Three-stage flow

The page runs as a **three-stage wizard in one browser session**. `recommendations.json` carries a top-level `"stage"` selector. Legacy payloads that still carry `"tier"` are accepted as read-only compatibility input, but new files must use `stage`.

| `recommendations.json stage` | Page renders | Button | On submit |
|---|---|---|---|
| `"stage1"` | communication contract — audience; open `communication_intent`; audience outcome; core message / delivery context / artifact afterlife / `content_divergence` (all prose fields may be blank); canvas | **Confirm contract & continue** | writes `result.json` `{ stage: "stage1", status: "stage1-confirmed", <communication contract> }`; the page stays open and polls |
| `"stage2"` | complete deck solution — reading mode, mode, page count, visual / template direction, color, icons, typography, image usage, generated-image rendering | **Confirm solution & continue** | writes `result.json` `{ stage: "stage2", status: "stage2-confirmed", <contract + solution> }`; the page stays open and polls |
| `"stage3"` | production only — confirmed image-source summary, conditional AI acquisition path, formula policy, generation mode, refine spec | **Confirm** | writes `result.json` `{ stage: "final", status: "confirmed", <all fields> }`, then shuts the page down |
| *(absent)* | legacy single-pass — every section on one page | **Confirm** | single final write (`status: "confirmed"`) — backward-compatible |

The AI launches Stage 1, derives the complete Stage-2 solution from the user's actual contract, then derives Stage-3 production mechanics from the confirmed solution. The page preserves earlier answers across transitions. `GET /api/session` is the waiting-state endpoint; `GET /api/recommendations` is `no-store`, and the server folds confirmed earlier-stage choices back into later payloads so refresh / reopen restores the user's actual values—including Stage-2 color, typography, icon, image-source, and rendering choices.

**Stage progression guard.** Stages confirm strictly in order — a staged `recommendations.json` may only run **one** stage past the last confirmed result. A file that skips ahead (e.g. `"stage3"` while only Stage 1 is confirmed) is never rendered: `/api/session` keeps reporting `waiting_agent` with `stage_skip: true`, and `--wait` / `--wait-only` exit `2` with a directive log line naming the expected stage to rewrite. An active deck/layout template does not exempt Stage 2: template capability is an input to the scenario-fit decision, not a reason to skip it. Legacy single-pass files (no `stage`) are not staged and bypass the guard.

### Input — `recommendations.json` (written by Strategist before launch)

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

After Stage 1 is confirmed, overwrite the file with the complete Stage-2 solution (the server folds confirmed communication fields back in when serving the page):

```json
{
  "stage": "stage2",
  "lang": "zh",
  "recommend": {
    "delivery_purpose": "balanced",
    "mode": "pyramid",
    "visual_style": "swiss-minimal",
    "template_reuse_scope": "layout",
    "template_adherence": "adaptive",
    "image_usage": ["ai", "provided"]
  },
  "page_count": { "value": "12-15" },
  "image_notes": { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材。" },
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

The example shows one candidate for brevity; a real file carries ≥3 coordinated directions. Top-level `color`, `typography`, `image_strategy`, and `visual_style_spectrum` remain read-compatible for legacy payloads, but new staged files do not duplicate the bundle.

After Stage 2 is confirmed, overwrite it with Stage-3 production recommendations only:

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

- `recommend.*` names the recommended `id` for each enumerable field (must match a `catalogs.json` id, or be a free string for a recommended custom value). The page badges and pre-selects it. **Guarantee**: if a `recommend.*` is omitted, the page falls back to the first catalog option so every enumerable field always shows one badged recommendation — but the AI should still set them for a meaningful default. Legacy aliases are accepted for old files (`line` → `tabler-outline`, `filled` → `tabler-filled`, `monochrome` → `chunk-filled`, `search` → `web`, `default` → `auto`, `builtin` → `host-native`), but new files should write canonical ids.
- `audience`, `communication_intent`, and `audience_outcome` are load-bearing Stage-1 reasoning inputs, so seed concrete recommendations when the evidence supports them; they are not required user inputs. Every Stage-1 prose field may be blank after confirmation, while the six communication keys remain present as key lines in `spec_lock.md communication`. `communication_intent` may preserve several purposes plus priority / sequence; never add a `primary_job` enum.
- `recommend.template_reuse_scope` is conditional. Write `layout`, `style`, or `mirror` only when Step 3 loaded a `kind: deck` or `kind: layout` template. The default is `layout`; `mirror` is displayed only when the installed spec declares `replication_mode: mirror`. `style` means free-design `pptx_structure.mode: flat` and suppresses/removes `template_adherence`.
- `recommend.template_adherence` is conditional on reuse scope `mirror` or `layout`. Write `adaptive` or `strict`; the default is `adaptive`. Both values require a reference SVG for every page: `strict` keeps the selected Layout contract; `adaptive` may create a new Layout under the same Master. Free design, brand-only templates, and `style` cannot display or return this field.
- `recommend.image_usage` should be an array of source ids when more than one source applies, e.g. `["ai", "provided"]`. A single string is still accepted for backward compatibility. Do not write bare `"custom"` and do not encode a mixed-source plan as prose here; write the prose to top-level `image_notes.value`.
- `image_notes` is the initial strategy note shown under the image source chips. Use it for page-role guidance and constraints: which source applies where, what to avoid, which user assets are authoritative, how realistic / abstract the imagery should be, and what can remain as placeholders. It is intent guidance, not a separate finite option.
- When confirmed Stage-2 `image_usage` includes `ai`, Stage 3 sets `recommend.image_ai_path` to one of `auto` / `api` / `host-native` / `manual`. Stage 2 never asks for the acquisition mechanism while the user is still deciding the image role.
- **Color candidates carry the user-facing core `palette`**: `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, and `body_text`. The page renders labelled swatches and offers per-role override inputs for precise single-role edits, plus a **Custom color card with a free-text box** (parallel to the custom typography box) — the user can describe the palette in words or paste HEX values instead of filling each role; this writes `color: { "name": "custom", "custom": "<text>" }` to `result.json` for the AI to interpret. Legacy `text` is accepted as an alias for `body_text`, but new files should write `body_text`. Strategist derives secondary text, borders, state colors, and visual-style neutral tiers later when writing `design_spec.md` / `spec_lock.md`; those are not user-facing confirmation choices.
- **Candidate display text may be multilingual**: color / typography candidates can provide `name_zh` / `name_en` / `name_ja` and `note_zh` / `note_en` / `note_ja`; the page falls back to legacy `name` / `note`. Labels resolve in the page language first, then fall back across the others (a `ja` page: ja → en → zh; zh/en pages keep their zh↔en fallback and try `_ja` last), so when `lang` is `ja` always include the `_ja` variants — otherwise the candidate labels render in English.
- **Typography candidates split CJK and Latin** for both `heading` and `body`; `css` is the fallback preview stack. Each candidate includes topic-matched sample text and `body_size` in px. The initial value follows the Stage-2 reading mode: `text` 20 · `balanced` 24 · `presentation` 32. The page writes px directly and never silently rewrites a visible value. `delivery_purpose` remains the compatibility key only.
- **Per-role size override** (parallel to color's per-role HEX override): besides `body_size`, the page exposes **independent** editable inputs for `title` / `subtitle` / `annotation`. Each role is pre-filled **once** with a starting value — the candidate's `typography.sizes[role]` if provided, otherwise a one-time ramp suggestion (`body × ` mid-band ratio) — and then holds its own value. **There is no cross-field cascade**: changing `body_size`, `delivery_purpose`, or canvas updates only the recommended-value hint, never the role values; a re-render preserves exactly what the user sees. Each role input is labelled as px and shows an approximate pt equivalent (`1px = 0.75pt`) for orientation. The final values are written to `result.json` as `typography.sizes: { "title", "subtitle", "annotation" }` in **px** — every canvas, no pt and no `sizes_pt` provenance. Seeding `sizes` in a candidate is optional — omit it and each role gets its one-time ramp suggestion.
- **`delivery_purpose` compatibility key / Reading mode** (enumerable, PPT only) drives the body baseline: `text` (read-close), `balanced` (business, default), `presentation`. It is surfaced in Stage 2 beside the visual system, separate from communication intent. `recommend.delivery_purpose` pre-selects one; `result.json` retains the key, while `spec_lock.md` uses canonical `consumption_mode`. Non-PPT canvases omit it.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated-image direction** is a rendering decision inside each `design_directions` candidate and is shown only when `image_usage` includes `ai`. Each object records `rendering` plus short `visual` / `mood` prose. The UI derives up to three rendering cards and one Custom card, displays rendering reference PNGs only, and writes no `palette` or `color` field. Final image colors come directly from the selected deck `color.palette`. Legacy `image_strategy.palette` input is accepted but ignored for color and stripped from new submissions.
- **`design_directions`** is the canonical Stage-2 personality spectrum. Each candidate carries localized name / note, `visual_style`, `color`, `typography`, `icons`, and conditional `image_strategy`. Author ≥3 spanning safe / shifted / bold (honest-shortfall exception applies). Selecting one applies the whole bundle; the component controls below are advanced overrides. The bundle itself is presentation-only—`result.json` stores the actual selected components, not a direction id.
- `recommend.generation_mode` and `refine_spec` mirror the two mandatory notes in SKILL.md Step 4. Confirmed `generation_mode: "split"` / `refine_spec: true` are explicit user choices, equivalent to opting in through chat.
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
  "mode": "pyramid",
  "visual_style": "swiss-minimal",
  "template_reuse_scope": "layout",
  "template_adherence": "adaptive",
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

The shape above is the **final** result: Stage 1 owns the communication contract, Stage 2 owns the complete deck solution (including color / typography / icons / images), and Stage 3 adds production mechanics. Intermediate writes carry the accumulated earlier fields with `stage1-confirmed` or `stage2-confirmed`; legacy `tier1` / `tier2` remain read-compatible but are no longer written.

- Any option field may instead hold a **free-text custom string** (the user picked **Custom**); `color` / `typography` custom entries set `name: "custom"`. Image usage is not a custom string in new results: it is a source-id array, with free-text strategy captured in `image_notes`.
- `image_ai_path` and `image_strategy` are omitted from `result.json` unless `image_usage` includes `ai`. Both are honored downstream as confirmed choices — and the page is only a convenience surface over the **canonical chat channel**: the same choices made in chat are honored identically when no `result.json` exists. `image_ai_path` drives the Step 5 generation path (`image-generator.md` §7 — `host-native` forces the host tool even when `IMAGE_BACKEND` is set); the chosen `image_strategy` candidate is locked verbatim by Strategist h.5 (no re-pick).
- After the user clicks the **final Confirm** (Stage 3, or single-pass), the page saves `result.json` and shuts the server down (auto-close). Stage-1 **Confirm contract & continue** and Stage-2 **Confirm solution & continue** keep the page open while it polls for the re-derived downstream stage. In the default flow, the first `--daemon --wait` returns on the stage-1 result, `--wait-only --wait-stage stage2` returns on the stage-2 result, and the final `--wait-only` returns on the final result; the AI reads each immediately — no extra chat confirmation is required. Chat confirmation remains the fallback when the page cannot be used. Either way, Step 4 ends with a `--shutdown` cleanup so a never-confirmed page cannot keep holding port 5050 ahead of the Step 6 live preview.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/stages/live-preview.md`, Step 6).
