# Confirm UI — Strategist Confirmation Stage Page

> The interactive, visual surface for SKILL.md Step 4 (the Strategist confirmation stage). Enumerable fields list **all** options from a catalog with the AI's recommendation badged; generative fields (color, typography, generated-image style) show **≥3** AI candidates (creative recommendations always offer real choice — same rule as the h.5 image strategy; fewer only on the honest-shortfall exception, with a stated reason). Fields whose universe is open (canvas, mode, visual style, icons) also get a **Custom** box; image usage is a multi-select source list plus a free-text `image_notes` box. Fully closed fields (template adherence when a deck/layout template is active, AI source when applicable, formula policy, generation mode, refine spec) do not. The AI writes its recommendation to `recommendations.json`; the user's final choices are written back to `result.json` for the AI to read. On confirm the page saves the result and shuts the server down (auto-close). The chat path is always a valid fallback — if the browser cannot open (remote / headless / web host), the AI presents the same staged confirmation in chat.

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

**Fallback rule**: Browser failure never cancels Step 4. Re-check `result.json` once, then use the chat confirmation path with the same three-stage semantics.

## `confirm_ui/server.py`

```bash
python3 scripts/confirm_ui/server.py <project_path> --daemon --wait   # launch + wait for Stage 1
python3 scripts/confirm_ui/server.py <project_path> --wait-only --wait-stage stage2  # Stage 2: wait for the design-system handoff
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
- `--wait-only` attaches to the page already running from the first `--daemon --wait` and blocks until the page writes the requested stage. If the recorded server died (common on Windows hosts that clean up background children), it automatically restarts the confirm server on the recorded/default port so the browser's polling reconnects without user action. Use `--wait-stage stage2` for the middle design-system handoff, then the default `--wait-stage final` for the final Stage-3 confirmation. It keys on the **stage alone** (no mtime gate), because a user may submit before this wait command is issued. Same `--wait-timeout` budget; on timeout / recovery failure it returns non-zero and the caller re-checks `result.json` once before the chat fallback.
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. SKILL.md Step 4 runs this on every path (page-confirm or chat-fallback) so the page never lingers on the shared port before live preview starts.
- Refuses to start unless `<project_path>/confirm_ui/recommendations.json` exists (except `--shutdown`, which needs no recommendations).
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.
- `/api/recommendations` derives `_template_adherence_enabled` from `<project>/templates/design_spec.md` frontmatter. Only `kind: deck` / `kind: layout` enables the Stage-1 field; no template and `kind: brand` force it off even if a stale recommendation contains the key. When enabled but no recommendation was authored, the server supplies `adaptive` as the default recommendation.

Dependency:

```bash
pip install flask
```

## Two kinds of field

- **Enumerable + custom** — canvas / mode / visual_style / icons. The page lists common options from `static/catalogs.json`, badges the AI's recommendation, and still offers a Custom box for edge cases (custom canvas size, bespoke narrative mode, self-provided icon system, etc.). `visual_style` additionally honors an optional `visual_style_spectrum` that badges a 3-pick personality spectrum (safe / shifted / bold, each with a temperament tag + analogy) in place of the single recommendation — see the schema below.
- **Visual examples for hard-to-name choices** — the full-screen confirmation page loads real SVG page samples from `static/style_previews/` for `visual_style`, and renders real sample SVGs from `templates/icons` for `icons`. These thumbnails make style and icon-library choices visually comparable before the user locks them. Preview copy is fixed role text (big title / section title / body / points), not project content from `recommendations.json`, so users compare visual treatment rather than copywriting. These previews are a confirmation aid only: they do not add fields to `recommendations.json` or `result.json`, and they do not replace the later Step 6 live preview.
- **Image usage multi-select** — image sources are selected as one or more catalog ids: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. `none` is exclusive. Recommendation and result values may be a legacy single string, but new files should use an array. When several sources are recommended, write the source ids to `recommend.image_usage` and write the actual usage strategy to `image_notes`, not a custom prose value.
- **Closed enumerable** — template adherence (conditional), formula policy / generation mode / refine spec, plus AI source only when image usage includes `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option. Use pipeline vocabulary: icon ids are actual library ids such as `tabler-outline`, or `emoji` for system emoji.
- **Generative (open)** — color, typography, generated-image style. No finite catalog; the AI authors **≥3 candidates** the page renders as cards (never a single option — creative fields must offer real choice; fewer than 3 only on the honest-shortfall exception). `page_count`, `audience`, and `content_divergence` are free inputs (`content_divergence` is a free-text intent shown under audience in §c, not a fixed-option field).

**Custom box** appears only on fields whose universe is genuinely open — `canvas`, `mode`, `visual_style`, and `icons`. Image usage uses a multi-select source list plus `image_notes` instead of a Custom box. Fully closed sets — `template_adherence`, `image_ai_path`, `formula_policy`, `generation_mode`, `refine_spec` — have **no** Custom box; an out-of-catalog value there is snapped back to the recommended option.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` includes `ai`. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while trilingual labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `template_adherence`, `icons`, `image_usage`, `image_ai_path`, `formula_policy`, `generation_mode`, `delivery_purpose`. Each entry is `{ "id", "label", "label_zh", "label_en", "label_ja", ... }`; descriptions use `desc_zh` / `desc_en` / `desc_ja`, and `visual_styles` groups use `group_zh` / `group_en` / `group_ja`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must cover all three languages (zh / en / ja). English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `mixed`, etc.); Chinese and Japanese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_en", "group_ja", "items": [...] }]`. For `canvas` you only need to maintain the trilingual labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

Round-trip and session files live under `<project_path>/confirm_ui/`.

### Three-stage flow

The page runs as a **three-stage wizard in one browser session**. `recommendations.json` carries a top-level `"stage"` selector. Legacy payloads that still carry `"tier"` are accepted as read-only compatibility input, but new files must use `stage`.

| `recommendations.json stage` | Page renders | Button | On submit |
|---|---|---|---|
| `"stage1"` | direction anchors — canvas, audience + `content_divergence` + `delivery_purpose` *(PPT only — omitted on non-PPT canvases, not written to the result)*, mode + visual_style, plus `template_adherence` only when a deck/layout template is active | **Next** | writes `result.json` `{ stage: "stage1", status: "stage1-confirmed", <anchors> }`; the page does **not** close — it shows a "deriving…" state and polls `GET /api/recommendations` |
| `"stage2"` | design system — page count, color, icons, typography, formula policy | **Next** | writes `result.json` `{ stage: "stage2", status: "stage2-confirmed", <anchors + design system> }`; the page stays open and polls for Stage 3 |
| `"stage3"` | images and execution — image usage + generated-image style, generation mode, refine spec | **Confirm** | writes `result.json` `{ stage: "final", status: "confirmed", <all fields> }`, then shuts the page down |
| *(absent)* | legacy single-pass — every section on one page | **Confirm** | single final write (`status: "confirmed"`) — backward-compatible |

The AI launches Stage 1 (`--daemon --wait`), reads the stage-1 result, **re-derives** the design-system candidates from the user's actual anchors, overwrites `recommendations.json` with `"stage": "stage2"`, and re-attaches with `--wait-only --wait-stage stage2`. After the Stage-2 result, it **re-derives** image and execution recommendations from the confirmed anchors + design system, overwrites `recommendations.json` with `"stage": "stage3"`, and re-attaches with `--wait-only` for the final result. The page preserves earlier selections across transitions (single JS session). `GET /api/session` is the browser's waiting-state endpoint: it is derived from `recommendations.json`, `result.json`, and the active server port, then persisted to `session.json` so a recovered server can resume the same stage state. Only after `/api/session` reports that the next recommendation stage is ready does the page fetch `GET /api/recommendations`. `GET /api/recommendations` is served `no-store` so polls see overwrites; on later stages the server folds already-confirmed choices from `result.json` back into the payload so a refresh / reopen re-initializes from the user's actual choices even though those sections are no longer rendered.

### Input — `recommendations.json` (written by Strategist before launch)

```json
{
  "stage": "stage1",
  "lang": "zh",
  "recommend": {
    "canvas": "ppt169",
    "mode": "pyramid",
    "visual_style": "swiss-minimal",
    "template_adherence": "adaptive",
    "icons": "tabler-outline",
    "image_usage": ["ai", "provided"],
    "image_ai_path": "auto",
    "formula_policy": "mixed",
    "generation_mode": "continuous",
    "delivery_purpose": "balanced"
  },
  "page_count":         { "value": "12-15" },
  "audience":           { "value": "..." },
  "content_divergence": { "value": "" },
  "image_notes":        { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材，缺口页可用占位符。" },
  "color": {
    "selected": 0,
    "candidates": [
      { "name": "...", "note": "...",
        "palette": {
          "background": "#FFFFFF",
          "secondary_bg": "#F4F6F8",
          "primary": "#1A3A6B",
          "accent": "#E8A317",
          "secondary_accent": "#4A7BB5",
          "body_text": "#1D2430"
        } }
    ]
  },
  "typography": {
    "selected": 0,
    "candidates": [
      { "name": "...", "note": "...",
        "sample_heading": "主题标题示例", "sample_heading_latin": "Topic Title",
        "sample_body": "关键信息摘要", "sample_body_latin": "Key message summary",
        "heading": { "cjk": "思源黑体", "latin": "Inter", "css": "'Source Han Sans SC','Inter',sans-serif" },
        "body":    { "cjk": "思源黑体", "latin": "Inter", "css": "..." },
        "body_size": 20 }
    ]
  },
  "image_strategy": {
    "selected": 0,
    "candidates": [
      {
        "name": "方案 A",
        "rendering": "vector-illustration",
        "palette": "cool-corporate",
        "visual": "扁平矢量、实色块、少阴影",
        "color": "背景 60-70% + 主色 25-30% + 强调色少量点题",
        "mood": "稳定、可信、克制"
      }
    ]
  },
  "visual_style_spectrum": [
    { "id": "soft-rounded", "tag_zh": "稳妥专业", "tag_en": "Safe & professional", "tag_ja": "手堅くプロフェッショナル", "note_zh": "像 Notion 官网", "note_en": "like the Notion site", "note_ja": "Notion公式サイト風" },
    { "id": "editorial",    "tag_zh": "编辑质感", "tag_en": "Editorial depth",     "tag_ja": "エディトリアルな質感", "note_zh": "像经济学人专题", "note_en": "like an Economist feature", "note_ja": "The Economistの特集記事風" },
    { "id": "brutalist",    "tag_zh": "硬核宣言", "tag_en": "Bold manifesto",      "tag_ja": "大胆なマニフェスト", "note_zh": "像研究机构年度宣言", "note_en": "like a research-house manifesto", "note_ja": "研究機関の年次宣言風" }
  ],
  "refine_spec": { "value": false }
}
```

> Each `candidates` array above shows **one** entry for brevity — `color` and `typography` must each carry **≥3** in a real file, while `image_strategy.candidates` should carry **exactly 3 non-custom recommendation** entries when AI image generation is offered. The UI adds the fourth **Custom** card itself; `selected` indexes the recommended default among the recommendation entries.

- `recommend.*` names the recommended `id` for each enumerable field (must match a `catalogs.json` id, or be a free string for a recommended custom value). The page badges and pre-selects it. **Guarantee**: if a `recommend.*` is omitted, the page falls back to the first catalog option so every enumerable field always shows one badged recommendation — but the AI should still set them for a meaningful default. Legacy aliases are accepted for old files (`line` → `tabler-outline`, `filled` → `tabler-filled`, `monochrome` → `chunk-filled`, `search` → `web`, `default` → `auto`, `builtin` → `host-native`), but new files should write canonical ids.
- `recommend.template_adherence` is conditional. Write `adaptive` or `strict` only when Step 3 loaded a `kind: deck` or `kind: layout` template. The server independently checks the copied template spec and enables the field only for those two kinds; free design and brand-only templates cannot display or return it. If the template is active but the recommendation key is missing, the server supplies `adaptive`. `adaptive` keeps native export on `baseline` and permits pages without `page_layouts`; `strict` requires every page to use the template roster and may activate a compatible preserved native pair.
- `recommend.image_usage` should be an array of source ids when more than one source applies, e.g. `["ai", "provided"]`. A single string is still accepted for backward compatibility. Do not write bare `"custom"` and do not encode a mixed-source plan as prose here; write the prose to top-level `image_notes.value`.
- `image_notes` is the initial strategy note shown under the image source chips. Use it for page-role guidance and constraints: which source applies where, what to avoid, which user assets are authoritative, how realistic / abstract the imagery should be, and what can remain as placeholders. It is intent guidance, not a separate finite option.
- When `recommend.image_usage` includes `ai`, also set `recommend.image_ai_path` to one of `auto` / `api` / `host-native` / `manual`; the page presents these as explicit choices.
- **Color candidates carry the user-facing core `palette`**: `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, and `body_text`. The page renders labelled swatches and offers per-role override inputs for precise single-role edits, plus a **Custom color card with a free-text box** (parallel to the custom typography box) — the user can describe the palette in words or paste HEX values instead of filling each role; this writes `color: { "name": "custom", "custom": "<text>" }` to `result.json` for the AI to interpret. Legacy `text` is accepted as an alias for `body_text`, but new files should write `body_text`. Strategist derives secondary text, borders, state colors, and visual-style neutral tiers later when writing `design_spec.md` / `spec_lock.md`; those are not user-facing confirmation choices.
- **Candidate display text may be multilingual**: color / typography candidates can provide `name_zh` / `name_en` / `name_ja` and `note_zh` / `note_en` / `note_ja`; the page falls back to legacy `name` / `note`. Labels resolve in the page language first, then fall back across the others (a `ja` page: ja → en → zh; zh/en pages keep their zh↔en fallback and try `_ja` last), so when `lang` is `ja` always include the `_ja` variants — otherwise the candidate labels render in English.
- **Typography candidates split CJK and Latin** for both `heading` and `body`; `css` is the fallback preview `font-family` stack. The page previews CJK sample text with `cjk + css` and Latin sample text with `latin + css`, so the two script choices are visible independently. Each candidate should include topic-matched `sample_heading`, `sample_heading_latin`, `sample_body`, and `sample_body_latin`; do not reuse unrelated fixed examples such as a digital-transformation headline for a travel, education, product, or brand deck. Each candidate should also include `body_size` — the body baseline in **px** (the system's only unit, every canvas). The initial value comes from the candidate's `body_size`, sized for the recommended delivery purpose: `text` ~20 · `balanced` ~24 · `presentation` ~32. On submit the page writes `typography.body_size` as px directly — no pt conversion, no `body_size_pt` provenance. The page exposes `body_size` as an editable numeric field whose hint shows the recommended size — **one fixed px per delivery purpose on PPT (`text` 20 · `balanced` 24 · `presentation` 32), not a range** (non-PPT ≈2.5–3.3% of height in px). The input area labels the value as px, shows the SVG px → PPT pt relation (`1px = 0.75pt`) above the input, and displays the current approximate pt value below it for user orientation only; the output contract remains px-only. The user may still edit it; an out-of-range flag only warns if the value strays far (e.g. a unit mistake). **Inputs are independent — the hint updates with canvas / delivery purpose but never rewrites a value the user can see.** It also offers a custom typography text box so the user is not limited to the proposed candidates.
- **Per-role size override** (parallel to color's per-role HEX override): besides `body_size`, the page exposes **independent** editable inputs for `title` / `subtitle` / `annotation`. Each role is pre-filled **once** with a starting value — the candidate's `typography.sizes[role]` if provided, otherwise a one-time ramp suggestion (`body × ` mid-band ratio) — and then holds its own value. **There is no cross-field cascade**: changing `body_size`, `delivery_purpose`, or canvas updates only the recommended-value hint, never the role values; a re-render preserves exactly what the user sees. Each role input is labelled as px and shows an approximate pt equivalent (`1px = 0.75pt`) for orientation. The final values are written to `result.json` as `typography.sizes: { "title", "subtitle", "annotation" }` in **px** — every canvas, no pt and no `sizes_pt` provenance. Seeding `sizes` in a candidate is optional — omit it and each role gets its one-time ramp suggestion.
- **`delivery_purpose`** (enumerable, PPT only) is the primary driver of the body baseline: `text` (read-close), `balanced` (business, the default), `presentation`. It is surfaced in the **§c key-information area** (beside audience, Stage 1) as a consumption-mode choice; the Stage-2 typography section then reads the confirmed value for the recommended body px — the pick itself does not rewrite the body field (inputs are independent). `recommend.delivery_purpose` pre-selects one (default `balanced`); the user's pick writes back to `result.json.delivery_purpose` as a plain id. Strategist uses it to set the px body baseline — **one fixed px per purpose (`text` 20 · `balanced` 24 · `presentation` 32), not a range** (see [strategist.md §g](../../references/strategist.md)). Non-PPT canvases omit it.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated image style candidates** live in `image_strategy.candidates` and are shown only when `image_usage` includes `ai`. Each candidate records `rendering`, `palette`, and short `visual` / `color` / `mood` lines from Strategist h.5. Author **exactly three non-custom recommendation candidates** here; the page displays those three, then appends one built-in **Custom** card. If extra candidates are present, the page shows only the first three non-custom entries. When `rendering` / `palette` match files under `references/ai-image-comparison/`, the left preview pane displays those reference PNGs for the selected candidate; when AI image generation is not selected, that left preview is hidden. The right-side option cards stay text-first and do not duplicate the gallery. The **Custom** card lists all reference-gallery `rendering` and `palette` ids from `ai-image-comparison/*/_manifest.json`, plus `custom` as a prose-only tail choice and a free-text prompt box; that prose is written to `result.json.image_strategy.custom`. If either selected dimension is `custom`, the preview intentionally falls back to prose and shows no reference image. `palette` means color behavior only — final AI image HEX values follow the confirmed `color` choice above. The chosen value is written to `result.json.image_strategy`; it is omitted when generated images are not part of the plan.
- **`visual_style_spectrum`** (optional) lets the AI surface the deck's aesthetic as a **personality spectrum** instead of one badged style. Each entry is `{ "id", "tag_zh"/"tag_en"/"tag_ja", "note_zh"/"note_en"/"note_ja" }` (include the `_ja` variants when `lang` is `ja`) where `id` is a real `visual_styles` catalog id; the page badges those chips with their temperament `tag` (replacing the single ★) and appends the `note` (a real-world analogy) inline. The full grouped style list and Custom box stay visible below, and `recommend.visual_style` is still the pre-selected default (it should equal the spectrum's safe pick). Author **≥3** spanning safe / shifted / bold (mirrors h.5; honest-shortfall exception applies — fewer only when the constraints genuinely cannot yield 3). The user's pick still writes back to `result.json.visual_style` as a plain id; the spectrum is presentation-only. Omit the field to fall back to the single-recommendation badge.
- `recommend.generation_mode` and `refine_spec` mirror the two mandatory notes in SKILL.md Step 4. Confirmed `generation_mode: "split"` / `refine_spec: true` are explicit user choices, equivalent to opting in through chat.
- `content_divergence` is a **free-text** field shown right under the audience box in §c — the user states in their own words how closely to follow the source vs how freely to reshape it (e.g. "stick closely to the document" / "freely restructure and expand within the source"). It is **not** a fixed-option field; blank means a balanced default. Whatever the level, facts stay sourced — reshaping develops what is in the source, never imports facts from outside it. The Strategist consumes the prose when authoring the §IX outline and records it in `design_spec.md §I`; it is **not** written to `spec_lock.md` (the Executor never reads it). It carries no page-count coupling and no source-signal recommendation — it is purely the user's stated intent. Beautify / template-fill keep content verbatim and do not surface this field.
- `lang` is a soft default (`zh` / `en` / `ja` — the page UI supports all three); an explicit user language choice in the page (persisted to `localStorage`) wins.

### Output — `result.json` (written on submit, read by the AI)

```json
{
  "canvas": "ppt169",
  "page_count": "12-15",
  "audience": "...",
  "content_divergence": "freely restructure and expand within the source",
  "mode": "pyramid",
  "visual_style": "swiss-minimal",
  "template_adherence": "adaptive",
  "color": { "name": "...", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
  "icons": "tabler-outline",
  "typography": { "name": "...", "heading": { "cjk": "...", "latin": "...", "css": "..." }, "body": { "cjk": "...", "latin": "...", "css": "..." }, "body_size": 24, "body_size_unit": "px", "sizes": { "title": 42, "subtitle": 32, "annotation": 18 } },
  "delivery_purpose": "balanced",
  "formula_policy": "mixed",
  "image_usage": ["ai", "provided"],
  "image_notes": "封面和章节页用 AI 主视觉；产品页优先用户素材，缺口页可用占位符。",
  "image_ai_path": "auto",
  "image_strategy": { "name": "方案 A", "rendering": "vector-illustration", "palette": "cool-corporate", "visual": "...", "color": "...", "mood": "..." },
  "generation_mode": "continuous",
  "refine_spec": false,
  "stage": "final",
  "status": "confirmed",
  "confirmed_at": "2026-06-15T11:44:44"
}
```

The shape above is the **final** (Stage 3) result, carrying Stage 1 anchors, Stage 2 design-system fields, and Stage 3 image / execution fields. The intermediate **Stage 1** write carries only the anchor fields plus `"stage": "stage1"`, `"status": "stage1-confirmed"`; the AI reads it to re-derive Stage 2 and never treats it as the final confirmation. The intermediate **Stage 2** write carries anchors + design-system fields plus `"stage": "stage2"`, `"status": "stage2-confirmed"`; the AI reads it to re-derive Stage 3 and never treats it as final. Legacy `tier1` / `tier2` results are accepted for old sessions but are no longer written. A legacy single-pass write has no `stage` (or `stage: "final"`) and `status: "confirmed"`.

- Any option field may instead hold a **free-text custom string** (the user picked **Custom**); `color` / `typography` custom entries set `name: "custom"`. Image usage is not a custom string in new results: it is a source-id array, with free-text strategy captured in `image_notes`.
- `image_ai_path` and `image_strategy` are omitted from `result.json` unless `image_usage` includes `ai`. Both are honored downstream as confirmed choices — and the page is only a convenience surface over the **canonical chat channel**: the same choices made in chat are honored identically when no `result.json` exists. `image_ai_path` drives the Step 5 generation path (`image-generator.md` §7 — `host-native` forces the host tool even when `IMAGE_BACKEND` is set); the chosen `image_strategy` candidate is locked verbatim by Strategist h.5 (no re-pick).
- After the user clicks the **final Confirm** (Stage 3, or single-pass), the page saves `result.json` and shuts the server down (auto-close). Stage-1 and Stage-2 **Next** keep the page open while it polls for the re-derived downstream stage. In the default flow, the first `--daemon --wait` returns on the stage-1 result, `--wait-only --wait-stage stage2` returns on the stage-2 result, and the final `--wait-only` returns on the final result; the AI reads each immediately — no extra chat confirmation is required. Chat confirmation remains the fallback when the page cannot be used. Either way, Step 4 ends with a `--shutdown` cleanup so a never-confirmed page cannot keep holding port 5050 ahead of the Step 6 live preview.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/live-preview.md`, Step 6).
