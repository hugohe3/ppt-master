# Confirmation Surface and Payloads

What the Strategist needs to run the two-stage confirmation: the surface decision, the in-run switch, and the exact shape of the three files it authors or reads. Server lifecycle, port/lock behavior, the template-selection sidecar, catalogs, and the progression guard live in [`confirm_ui.md`](../scripts/docs/confirm_ui.md); the launch/wait/shutdown commands live in [`generate-pptx.md`](../workflows/generate-pptx.md) Step 4.

## 1. Surface decision

**Mandatory — before any UI command**: resolve the most recent explicit confirmation-surface instruction for this run. Unrelated later messages do not reset the branch; once confirmation starts in chat or UI switches to chat, keep chat for the rest of the run.

| Most recent explicit surface instruction | Branch |
|---|---|
| The user explicitly delegates confirmation | Make the combined Stage-1 communication/template decision, install it, then present one complete final summary. Do not launch the page or fabricate UI receipts. |
| The user asks for or agrees to personally confirm in chat, or declines the page | Use chat for both stages; Stage 1 includes the template/free-design choice. Do not launch the page, run `--wait-only`, or require UI-authored results. |
| No explicit instruction | Use the page. |

Interpret the instruction semantically — "confirm here", "use the chat window", "do not open the confirmation page" are sufficient; a chat-question tool by itself selects nothing. Both branches preserve the same Stage-1 decision, installation handoff, and template-aware Stage 2, and the chat branch records the same `design_spec_depth` in its summary.

**Chat/delegated Stage-1 listing**: author the communication recommendation before reading the four template indexes, then present it together with an explicit free-design/template-mode choice; only template mode expands registered candidates and supplied exact roots and requires at least one selection. Ordinary requests initialize free design; explicit template intent or any supplied exact root initializes template mode, and exactly one supplied root may seed that candidate.

**Always-on Stage-1 chat handoff (UI branch)**: after writing `template_options.json` and `recommendations.stage1.json`, launch the daemon, then immediately post its actual URL plus one compact localized summary of the recommendation and template-choice state (audience, communication intent, audience outcome, core message, delivery context, artifact afterlife, `content_divergence`, canvas, free-design vs template default and any sole preselected root; blank prose shown as "not specified"), ending with a localized line that the same items may be confirmed or revised in chat if the page did not open. Only then run `--wait-only --wait-stage stage1`. The handoff is context, not confirmation; silence confirms nothing.

**In-run UI → chat switch (any stage)**: when the user explicitly selects chat after launch — interrupt an active wait and confirm its process exited (that deliberate interruption is the only expected non-zero return), run `server.py <project_path> --shutdown` and require it to succeed, re-check the active receipt once (Stage 1: `result.json` plus `template_selection.json` from the same submission; Stage 2: `result.json`; an unsubmitted browser draft is not confirmed), then continue everything remaining in chat without relaunching or waiting again. After launch failure/timeout, re-check the receipts once the same way and present the same items as open chat questions.

## 2. `recommendations.stage1.json`

Author before reading any candidate index, spec, prototype, asset, or template canvas. All seven prose values may be blank; `primary_language` is canonical BCP-47 (`und` and Chinese without script/region are rejected); `lang` is the UI language only. The intent paths (inform / explain / persuade / decide / align / teach / report and account / mobilize / record and hand off) are help text, never a `primary_job` field.

```json
{
  "stage": "stage1",
  "lang": "zh",
  "primary_language": "zh-CN",
  "recommend": { "canvas": "ppt169" },
  "audience": { "value": "公司管理层，包括财务与产品负责人" },
  "communication_intent": { "value": "先汇报进展并暴露交付风险，再推动管理层决定下一阶段投入" },
  "audience_outcome": { "value": "管理层能比较三个选项、接受风险判断，并选定一条获得预算的路径" },
  "core_message": { "value": "现在为方案 B 增加投入，能以可接受的成本守住发布时间" },
  "delivery_context": { "value": "主要为有主讲的 20 分钟管理层现场评审；次要为会后独立阅读的审批材料" },
  "artifact_afterlife": { "value": "作为审批记录、项目交接依据和季度审计材料" },
  "content_divergence": { "value": "" }
}
```

## 3. `recommendations.stage2.json`

Create only after the Stage-1 receipts and the `--complete-template-selection` handoff exist, leaving Stage 1 unchanged. Required: `recommend.generation_mode`, boolean `refine_spec.value`, `design_spec_depth.value` as `brief` or `complete` (`brief` is rejected with `split` mode or `refine_spec: true`), and `recommend.image_ai_path` (`auto` / `api` / `host-native` / `manual`) whenever `image_usage` includes `ai`. `image_usage` is an array of source ids (`ai`, `web`, `provided`, `placeholder`; `none` is exclusive). `design_directions` carries exactly three complete candidates with unique stable ids; `selected` is the zero-based index chosen after all three are complete. Candidate display text is written once in the confirmed UI language using the plain keys (`name`, `note`, `mode_behavior`, `visual_style_behavior`, `visual`, `mood`, `behavior`; a single locale suffix such as `_zh` is accepted). Typography carries concrete heading/body `primary` plus `english` only for non-English decks and a positive `body_size`; color carries the six-role `palette`. For a confirmed templates-mode handoff, add top-level `template_application.value` — one editable prose paragraph on how to use the installed template. Never write `recommend.template_reuse_scope` or `template_adherence`.

```json
{
  "stage": "stage2",
  "lang": "zh",
  "recommend": {
    "delivery_purpose": "balanced",
    "mode": "custom",
    "visual_style": "custom",
    "image_strategy": "custom",
    "image_usage": ["ai", "provided"],
    "image_ai_path": "auto",
    "generation_mode": "continuous"
  },
  "page_count": { "value": "12-15" },
  "image_notes": { "value": "封面和章节页用 AI 主视觉；产品页优先用户素材。" },
  "proactive_speaker_notes": { "value": true },
  "proactive_custom_animations": { "value": false },
  "proactive_narration_audio": { "value": false },
  "refine_spec": { "value": false },
  "design_spec_depth": { "value": "brief" },
  "template_application": { "value": "选用封面、章节页和数据页原型；跳过示例内容页。品牌标识和页脚保留，正文可按当前材料重组。" },
  "design_directions": {
    "selected": 1,
    "candidates": [
      {
        "id": "executive-clarity",
        "name": "稳妥专业",
        "note": "以瑞士极简为主，融合柔和圆角与编辑出版风格。",
        "mode": "custom",
        "mode_behavior": "以 pyramid 作为唯一目录基底，为当前风险决策材料定制两次结论闸门；标题保持判断句，每章先给判断，再用证据展开并以可执行结论收束。",
        "visual_style": "custom",
        "visual_style_behavior": "由 swiss-minimal 负责精确栅格和大留白，soft-rounded 负责少量关键容器的轮廓与轻微抬升，editorial 负责细规则、边注与证据层级；标题锐利，正文中性。",
        "icons": "tabler-outline",
        "color": { "name": "冷静专业", "palette": {
          "background": "#FFFFFF", "secondary_bg": "#F4F6F8",
          "primary": "#1A3A6B", "accent": "#E8A317",
          "secondary_accent": "#4A7BB5", "body_text": "#1D2430"
        } },
        "typography": {
          "name": "微软雅黑 + Arial",
          "heading": { "primary": "Microsoft YaHei", "english": "Arial", "css": "sans-serif" },
          "body": { "primary": "Microsoft YaHei", "english": "Arial", "css": "sans-serif" },
          "body_size": 24
        },
        "image_strategy": {
          "name": "编辑式证据图",
          "rendering": "custom",
          "visual": "简化矢量主体配合编辑式注释与局部材质对比",
          "mood": "审慎、可信，像调查报道中的证据插图",
          "behavior": "由 vector-illustration 负责清晰轮廓，minimalist-swiss 负责留白构图，screen-print 负责克制的半调纹理；三者服从同一平面主体和当前演示文稿颜色角色。"
        }
      }
    ]
  }
}
```

The array repeats that candidate shape exactly three times. `template_application` appears only in templates mode.

## 4. `result.json`

Written by the user's submission; Generate Step 4 reads the final object (`stage: final`, `status: confirmed`) exactly once and retains it through Design Spec authoring. It carries the Stage-1 prose fields, `primary_language`, `canvas`, `page_count`, the confirmed `mode` / `visual_style` with their `_behavior` siblings, `color`, `icons`, `typography` (including `body_size`, optional per-role `sizes`), `delivery_purpose`, `image_usage`, `image_notes`, conditional `image_ai_path` and `image_strategy`, the three flat proactive booleans, `generation_mode`, `refine_spec`, and `design_spec_depth`. It contains no template-selection field — `template_selection.json` and the installed project-local state own that decision. Legacy results without `design_spec_depth` read as `complete`; results that omit the proactive booleans resolve to `true / false / false`.
