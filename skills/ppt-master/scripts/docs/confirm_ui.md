# Confirm UI — Eight Confirmations Page

> The interactive, visual surface for SKILL.md Step 4 (the Eight Confirmations). Enumerable fields list **all** options from a catalog with the AI's recommendation badged; generative fields (color, typography, generated-image style) show **≥3** AI candidates (creative recommendations always offer real choice — same rule as the h.5 image strategy; fewer only on the honest-shortfall exception, with a stated reason). Fields whose universe is open (canvas, mode, visual style, icons, image usage) also get a **Custom** box; fully closed fields (AI source when applicable, formula policy, generation mode, refine spec) do not. The AI writes its recommendation to `recommendations.json`; the user's final choices are written back to `result.json` for the AI to read. On confirm the page saves the result and shuts the server down (auto-close). The chat path is always a valid fallback — if the browser cannot open (remote / headless / web host), the AI presents the same confirmations in chat.

## `confirm_ui/server.py`

```bash
python3 scripts/confirm_ui/server.py <project_path> --daemon --wait
python3 scripts/confirm_ui/server.py <project_path> --daemon
python3 scripts/confirm_ui/server.py <project_path> --daemon --port 5051
python3 scripts/confirm_ui/server.py <project_path> --no-browser
python3 scripts/confirm_ui/server.py <project_path> --timeout 0   # disable idle auto-shutdown
python3 scripts/confirm_ui/server.py <project_path> --shutdown    # Step 4 cleanup (idempotent)
```

- Binds `127.0.0.1:5050` by default — or the next free port if another project already holds it (the launch log prints the actual URL) — and auto-opens the browser (suppress with `--no-browser`). `--port <other>` forces a specific port.
- **Shares port 5050 with the live preview server** (`svg_editor/server.py`). The two never run at once: confirm is Step 4, live preview is Step 6, and Step 4 always shuts this server down on exit (see `--shutdown`) so the port is free. One port = one forward rule for the whole pipeline. They still keep **separate processes and locks** (`.confirm_ui.lock` vs `.live_preview.lock`).
- `--daemon` starts the Flask process in the background; add `--wait` in the main pipeline so the parent command returns only after the page writes a fresh `result.json`. The `--wait` budget defaults to **590 s** (`--wait-timeout`), kept under the typical 600 s tool ceiling — run the launch with a long tool timeout (≈600000 ms). On timeout the parent returns non-zero but the detached server keeps running, so the caller must re-check `result.json` once before the chat fallback (a slow user may confirm just after the wait returns).
- `--shutdown` stops a confirm server left running for this project and exits — **idempotent** (a no-op when nothing is running). Tries a graceful `/api/shutdown`, falls back to killing the recorded pid, then clears the lock. SKILL.md Step 4 runs this on every path (page-confirm or chat-fallback) so the page never lingers on the shared port before live preview starts.
- Refuses to start unless `<project_path>/confirm_ui/recommendations.json` exists (except `--shutdown`, which needs no recommendations).
- Per-project lock at `<project_path>/.confirm_ui.lock` — duplicate launches are refused; stale locks (dead pid) are overwritten.
- Idle auto-shutdown after 900 s by default; `/api/shutdown` exits gracefully and releases the lock.

Dependency:

```bash
pip install flask
```

## Two kinds of field

- **Enumerable + custom** — canvas / mode / visual_style / icons / image usage. The page lists common options from `static/catalogs.json`, badges the AI's recommendation, and still offers a Custom box for edge cases (custom canvas size, bespoke narrative mode, mixed image plan, self-provided icon system, etc.). `visual_style` additionally honors an optional `visual_style_spectrum` that badges a 3-pick personality spectrum (safe / shifted / bold, each with a temperament tag + analogy) in place of the single recommendation — see the schema below.
- **Closed enumerable** — formula policy / generation mode / refine spec, plus AI source only when image usage may include `ai`. These have no Custom box; out-of-catalog values snap back to the recommended option. Use pipeline vocabulary: icon ids are actual library ids such as `tabler-outline`, or `emoji` for system emoji; image usage labels mirror Strategist terminology: `ai` = AI-generated, `web` = Web-sourced, `provided` = User-provided, `placeholder` = Placeholder, `none` = No images. Use custom prose only when several sources are mixed.
- **Generative (open)** — color, typography, generated-image style. No finite catalog; the AI authors **≥3 candidates** the page renders as cards (never a single option — creative fields must offer real choice; fewer than 3 only on the honest-shortfall exception). `page_count`, `audience`, and `content_divergence` are free inputs (`content_divergence` is a free-text intent shown under audience in §c, not a fixed-option field).

**Custom box** appears only on fields whose universe is genuinely open — `canvas`, `mode`, `visual_style`, `icons`, and `image_usage`. Fully closed sets — `image_ai_path`, `formula_policy`, `generation_mode`, `refine_spec` — have **no** Custom box; an out-of-catalog value there is snapped back to the recommended option.

`image_ai_path` is conditional: the page shows it and writes it to `result.json` only when `image_usage` is `ai` or a custom image plan that may include AI. Web-sourced / User-provided / Placeholder / No images paths do not carry an AI backend choice.

## Catalogs — `static/catalogs.json` (the finite option universe)

The front-end loads `/api/catalogs` (served by the confirm server) and falls back to the static `/static/catalogs.json` if that route is unavailable. `/api/catalogs` returns the static file **with the `canvas` list synced live from `config.py CANVAS_FORMATS`** — the set of formats and their `dim` come from config (single source of truth, zero drift), while bilingual labels / use text stay in catalogs.json (a plain fallback label is synthesized for any new id config adds). Keys: `canvas`, `modes`, `visual_styles` (grouped), `icons`, `image_usage`, `image_ai_path`, `formula_policy`, `generation_mode`. Each entry is `{ "id", "label", "label_zh", "label_en", ... }`; descriptions use `desc_zh` / `desc_en`, and `visual_styles` groups use `group_zh` / `group_en`. The front-end falls back to legacy `label` / `desc` / `group`, so old catalogs still load, but new user-facing catalog text must be bilingual. English labels should mirror canonical reference names (`pyramid`, `swiss-minimal`, `Path A`, `mixed`, etc.); Chinese labels should be translated for users. Descriptions render inline after the option title, not as a separate selected-option line. `visual_styles` is `[{ "group", "group_zh", "group_en", "items": [...] }]`. For `canvas` you only need to maintain the bilingual labels in catalogs.json; the format set and dimensions are authoritative in `config.py CANVAS_FORMATS`.

## Round-trip data contract

Both files live under `<project_path>/confirm_ui/`.

### Input — `recommendations.json` (written by Strategist before launch)

```json
{
  "lang": "zh",
  "recommend": {
    "canvas": "ppt169",
    "mode": "pyramid",
    "visual_style": "swiss-minimal",
    "icons": "tabler-outline",
    "image_usage": "web",
    "formula_policy": "mixed",
    "generation_mode": "continuous"
  },
  "page_count":         { "value": "12-15" },
  "audience":           { "value": "..." },
  "content_divergence": { "value": "" },
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
        "heading": { "cjk": "思源黑体", "latin": "Inter", "css": "'Source Han Sans SC','Inter',sans-serif", "sample_cjk": "标题示例", "sample_latin": "Heading Sample" },
        "body":    { "cjk": "思源黑体", "latin": "Inter", "css": "...", "sample_cjk": "正文示例", "sample_latin": "Body sample" },
        "body_size": 18 }
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
    { "id": "soft-rounded", "tag_zh": "稳妥专业", "tag_en": "Safe & professional", "note_zh": "像 Notion 官网", "note_en": "like the Notion site" },
    { "id": "editorial",    "tag_zh": "编辑质感", "tag_en": "Editorial depth",     "note_zh": "像经济学人专题", "note_en": "like an Economist feature" },
    { "id": "brutalist",    "tag_zh": "硬核宣言", "tag_en": "Bold manifesto",      "note_zh": "像研究机构年度宣言", "note_en": "like a research-house manifesto" }
  ],
  "refine_spec": { "value": false }
}
```

> Each `candidates` array above shows **one** entry for brevity — the creative fields (`color`, `typography`, `image_strategy`) must each carry **≥3** in a real file (see the rule above); `selected` indexes the recommended default.

- `recommend.*` names the recommended `id` for each enumerable field (must match a `catalogs.json` id, or be a free string for a recommended custom value). The page badges and pre-selects it. **Guarantee**: if a `recommend.*` is omitted, the page falls back to the first catalog option so every enumerable field always shows one badged recommendation — but the AI should still set them for a meaningful default. Legacy aliases are accepted for old files (`line` → `tabler-outline`, `filled` → `tabler-filled`, `monochrome` → `chunk-filled`, `search` → `web`, `default` → `auto`, `builtin` → `host-native`), but new files should write canonical ids. For `recommend.image_usage`, do not write bare `"custom"`; if several image sources are mixed, write the concrete prose plan directly, such as `"封面用 AI 生成，产品页用用户素材，行业页用网络来源"` / `"AI cover + user product assets + web industry images"`.
- When `recommend.image_usage` is `ai` or a custom plan that includes AI, also set `recommend.image_ai_path` to one of `auto` / `api` / `host-native` / `manual`; the page presents these as explicit choices.
- For a custom image plan, the page treats "may include AI" as true only when the recommendation includes `recommend.image_ai_path` or `image_strategy.candidates`; a custom plan without those signals is handled as non-AI and omits AI controls / fields.
- **Color candidates carry the user-facing core `palette`**: `background`, `secondary_bg`, `primary`, `accent`, `secondary_accent`, and `body_text`. The page renders labelled swatches and offers per-role override inputs for precise single-role edits, plus a **Custom color card with a free-text box** (parallel to the custom typography box) — the user can describe the palette in words or paste HEX values instead of filling each role; this writes `color: { "name": "custom", "custom": "<text>" }` to `result.json` for the AI to interpret. Legacy `text` is accepted as an alias for `body_text`, but new files should write `body_text`. Strategist derives secondary text, borders, state colors, and visual-style neutral tiers later when writing `design_spec.md` / `spec_lock.md`; those are not user-facing confirmation choices.
- **Candidate display text may be bilingual**: color / typography candidates can provide `name_zh` / `name_en` and `note_zh` / `note_en`; the page falls back to legacy `name` / `note`.
- **Typography candidates split CJK and Latin** for both `heading` and `body`; `css` is the fallback preview `font-family` stack. The page previews CJK sample text with `cjk + css` and Latin sample text with `latin + css`, so the two script choices are visible independently. Each candidate should also include `body_size` (the body baseline in px; common values are 18 and 24, but any reasonable integer is valid). The page exposes `body_size` as an editable numeric field whose hint shows a canvas-appropriate range (≈2.5–3.3% of the confirmed canvas height, parsed from the canvas `dim`), updated when the canvas changes — a hint only, never an override, so a 16:9 default is not silently kept on a tall canvas (Xiaohongshu / Story / A4). It also offers a custom typography text box so the user is not limited to the proposed candidates.
- **Combined style preview** — a compact live "overall impression" strip sits just above the color section and is **sticky**: it pins under the topbar so it stays visible while the user scrolls through the color / icon / typography sections, keeping the picking controls and their combined effect on screen together. It applies the currently selected color palette **and** typography (heading sample in `primary` over `background`, body sample in `body_text`, an `accent` bar, a `secondary_bg` chip) and repaints on every color / HEX-override / font / `body_size` change. It does not replace the per-candidate swatches or font samples (those stay for picking); it is deliberately an abstract style chip, **not** a slide-layout preview — page layout preview remains the live-preview server's job (Step 6). No schema field; it derives entirely from the existing color + typography selections.
- **Generated image style candidates** live in `image_strategy.candidates` and are shown only when `image_usage` is `ai` or a custom image plan may include generated images. Each candidate records `rendering`, `palette`, and short `visual` / `color` / `mood` lines from Strategist h.5. The chosen value is written to `result.json.image_strategy`; it is omitted when generated images are not part of the plan.
- **`visual_style_spectrum`** (optional) lets the AI surface the deck's aesthetic as a **personality spectrum** instead of one badged style. Each entry is `{ "id", "tag_zh"/"tag_en", "note_zh"/"note_en" }` where `id` is a real `visual_styles` catalog id; the page badges those chips with their temperament `tag` (replacing the single ★) and appends the `note` (a real-world analogy) inline. The full grouped style list and Custom box stay visible below, and `recommend.visual_style` is still the pre-selected default (it should equal the spectrum's safe pick). Author **≥3** spanning safe / shifted / bold (mirrors h.5; honest-shortfall exception applies — fewer only when the constraints genuinely cannot yield 3). The user's pick still writes back to `result.json.visual_style` as a plain id; the spectrum is presentation-only. Omit the field to fall back to the single-recommendation badge.
- `recommend.generation_mode` and `refine_spec` mirror the two mandatory notes in SKILL.md Step 4. Confirmed `generation_mode: "split"` / `refine_spec: true` are explicit user choices, equivalent to opting in through chat.
- `content_divergence` is a **free-text** field shown right under the audience box in §c — the user states in their own words how closely to follow the source vs how freely to reshape it (e.g. "stick closely to the document" / "freely restructure and expand within the source"). It is **not** a fixed-option field; blank means a balanced default. Whatever the level, facts stay sourced — reshaping develops what is in the source, never imports facts from outside it. The Strategist consumes the prose when authoring the §IX outline and records it in `design_spec.md §I`; it is **not** written to `spec_lock.md` (the Executor never reads it). It carries no page-count coupling and no source-signal recommendation — it is purely the user's stated intent. Beautify / template-fill keep content verbatim and do not surface this field.
- `lang` is a soft default; an explicit user language choice in the page (persisted to `localStorage`) wins.

### Output — `result.json` (written on submit, read by the AI)

```json
{
  "canvas": "ppt169",
  "page_count": "12-15",
  "audience": "...",
  "content_divergence": "freely restructure and expand within the source",
  "mode": "pyramid",
  "visual_style": "swiss-minimal",
  "color": { "name": "...", "palette": { "background": "#...", "secondary_bg": "#...", "primary": "#...", "accent": "#...", "secondary_accent": "#...", "body_text": "#..." } },
  "icons": "tabler-outline",
  "typography": { "name": "...", "heading": { "cjk": "...", "latin": "...", "css": "..." }, "body": { "cjk": "...", "latin": "...", "css": "..." }, "body_size": 18 },
  "formula_policy": "mixed",
  "image_usage": "web",
  "image_strategy": { "name": "方案 A", "rendering": "vector-illustration", "palette": "cool-corporate", "visual": "...", "color": "...", "mood": "..." },
  "generation_mode": "continuous",
  "refine_spec": false,
  "status": "confirmed",
  "confirmed_at": "2026-06-15T11:44:44"
}
```

- Any option field may instead hold a **free-text custom string** (the user picked **Custom**); `color` / `typography` custom entries set `name: "custom"`. Image usage custom values must be concrete prose plans, not the literal string `"custom"`. The AI interprets custom text against the canonical references.
- `image_ai_path` and `image_strategy` are omitted from `result.json` unless `image_usage` is `ai` or a custom image plan that may include generated images. Both are honored downstream as confirmed choices — and the page is only a convenience surface over the **canonical chat channel**: the same choices made in chat are honored identically when no `result.json` exists. `image_ai_path` drives the Step 5 generation path (`image-generator.md` §7 — `host-native` forces the host tool even when `IMAGE_BACKEND` is set); the chosen `image_strategy` candidate is locked verbatim by Strategist h.5 (no re-pick).
- After the user clicks **Confirm**, the page saves `result.json` and shuts the server down (auto-close). In the default `--daemon --wait` flow, the waiting command returns and the AI reads `result.json` immediately; no second chat confirmation is required. Chat confirmation remains the fallback when the page cannot be used. Either way, Step 4 ends with a `--shutdown` cleanup so a never-confirmed page cannot keep holding port 5050 ahead of the Step 6 live preview.

## Scope

- Confirmation surface only — Strategist authors every recommendation; the page never generates deck content.
- No SVG / layout preview here — that is the live preview server's job (`workflows/live-preview.md`, Step 6).
