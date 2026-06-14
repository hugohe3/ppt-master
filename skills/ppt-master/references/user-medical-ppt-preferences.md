# User Medical PPT Preferences

These rules are mandatory for every PPT-making request from this user. Read this
file before Step 1 and before the Strategist phase.

## Conversation Style

Ask in Chinese by default unless the user asks otherwise. Use a clinical,
matter-of-fact tone: concise, respectful, specific, and evidence-oriented.
Do not sound like marketing copy or an AI demo.

Use token-efficient intake. Do not ask the long questionnaire every time. Ask
only the Core Intake Questions first, then add the relevant Conditional
Supplement for the deck type. Treat the fixed medical evidence, image, wording,
and cleanup rules in this file as defaults; do not re-ask them unless the user
asks to change them.

Avoid phrases that create an obvious AI tone, such as "具有重要意义",
"深入探讨", "全面分析", "赋能", "打造", "多维度", "系统性阐述", and
similar generic praise. Prefer clinical language: "诊断依据", "反对依据",
"下一步检查", "治疗选择", "证据等级", "局限性", "随访", "转归".

## Final Deck Wording Rules

Never expose the production process inside the final PPT, speaker notes, or
exported visible content. When updating an existing PPT or creating a new PPT
from an original deck, the final deck must read as a finished clinical or
academic presentation, not as an explanation of what was changed.

Do not write meta phrases such as "原PPT", "原始PPT", "旧版PPT", "新版PPT",
"我的新要求", "用户要求", "根据你的要求", "根据原PPT", "本次更新",
"修改后", "优化后", "AI生成", "由AI整理", "以下是", "本页将介绍", or similar
process-oriented wording in slide titles, body text, notes, captions, or
references.

When revising from an existing deck, silently incorporate the useful source
content and new instructions. Replace meta descriptions with final-form
clinical content. For example, use "诊疗时间轴" rather than "根据原PPT整理的诊疗时间轴",
and use "治疗方案调整依据" rather than "按照新要求补充治疗方案".

Do not add extra explanatory slides or text unless the user explicitly requests
them. Prefer direct final content over commentary about the task.

## Post-Production Cleanup Rules

After the final requested output is exported and the user does not need more
edits, remove production artifacts created during PPT generation. Preserve only
the final requested deliverables, such as PPTX/PDF/image exports, unless the user
asks to keep the full project.

Delete generated/intermediate artifacts such as AI-generated image drafts, web
image downloads, temporary image manifests, SVG output/final folders, preview
snapshots, backup folders, cache folders, temporary downloads, and working files
created only to build the deck.

Do not automatically delete user-provided original materials, final exported
deliverables, installed skill files, templates, icons, scripts, or reusable
reference assets. If source files were moved into a project folder, ask before
deleting them unless the user has explicitly requested full cleanup.

For medical or clinical decks, treat generated working files as potentially
sensitive. Prefer cleanup after delivery, and report only a brief cleanup
summary. Do not add cleanup explanations to the PPT itself.

## Token-Efficient Intake Rules

Ask the Core Intake Questions as one compact block before making a PPT. Use the
user's answers to prepare a single combined confirmation that covers both
medical choices and ppt-master's Eight Confirmations. Do not ask the same
question again in the Eight Confirmations unless the answer is unclear.

### Core Intake Questions

1. PPT 类型和用途：病例汇报、病历分析、文献总结、Journal Club、教学、MDT、课题汇报、会议发言，还是其他？
2. 听众是谁？希望听众看完后做出什么判断或行动？
3. 主题、科室、疾病、病例或核心临床问题是什么？
4. 你会提供哪些资料：病例、旧PPT、PDF、Word、Excel、图片、文献、网页，还是只有主题？
5. 是否允许检索外部资料？默认优先 PubMed、指南/共识、系统综述、RCT、Meta 分析，并提供来源；如有限制请说明。
6. 目标页数、演讲时长和输出格式是什么？
7. 是否需要讲稿/备注、动画、实时预览、旁白音频？
8. 是否先确认大纲和风格后再生成，还是回答这些问题后直接生成？

### Conditional Supplements

If the deck is a case report, clinical case analysis, or MDT discussion, ask only
these extra questions:

1. 病例是否已经脱敏？病例资料包括哪些关键内容？
2. 呈现结构用时间轴、入院-检查-诊断-治疗-转归、SOAP，还是问题驱动式？
3. 是否需要鉴别诊断、临床决策分析、治疗风险收益和随访转归？

If the deck is a literature review, Journal Club, guideline update, or research
summary, ask only these extra questions:

1. 文献范围：只用你提供的文献，还是允许检索？近 5 年、近 10 年，还是不限？
2. 引用格式：每页脚注、末页参考文献、Vancouver/AMA，还是观点-来源对应表？
3. 是否需要证据等级、研究类型、样本量、主要结论和局限性？

If the deck is teaching, training, patient education, or a lecture, ask only
these extra questions:

1. 听众基础水平是什么？需要讲到基础概念、临床思维，还是最新进展？
2. 是否需要课后总结、讨论题、流程图、病例练习或参考阅读？

If the user provides an existing PPT for revision, ask only these extra
questions:

1. 需要保留哪些内容、删除哪些内容、强化哪些内容？
2. 是否保留原视觉风格，还是重做为医学会议/科室汇报/学术风格？

### Fixed Defaults To Avoid Re-asking

- 医学事实不虚构；缺失信息标注"资料未提供"或"证据不足"。
- 外部医学结论必须给来源；高风险医学事实需要实时核验。
- 图片默认优先用户提供的脱敏医学图片，其次自绘图表；AI 只用于标明为示意图的机制/概念图。
- 最终 PPT 不出现"原PPT"、"根据你的要求"、"本次更新"、"AI生成"等过程痕迹。
- 默认视觉风格为克制、干净、学术/临床汇报风。
- 默认保留最终交付物，清理中间文件，不删除用户原始资料。

## Medical Evidence Rules

Do not fabricate medical facts. Do not invent case details, examination values,
imaging findings, pathology findings, medication doses, guideline
recommendations, follow-up outcomes, statistics, PMID/DOI values, citations, or
study conclusions.

When external medical information is used, cite sources. Prefer guidelines,
consensus statements, systematic reviews, randomized controlled trials,
meta-analyses, drug labels, and PubMed-indexed articles. For literature-heavy
slides, include article type, year, population/sample size when available, main
finding, and limitation.

If evidence is missing or uncertain, write "资料未提供", "证据不足", "未检索到可靠来源",
or "仅供讨论". Do not fill gaps with plausible-sounding content.

If the user asks for current guidelines, recent evidence, drug indications,
dosing, safety warnings, or any high-stakes medical fact, verify with current
sources before writing final slide content.

## Image Source Policy

Default image setting for this user:

1. Use user-provided, de-identified clinical images first.
2. Prefer self-made diagrams, timelines, tables, diagnostic pathways, mechanism
   diagrams, and evidence maps over decorative pictures.
3. Use public web images only when they add clinical value and the source,
   license/usage status, and access date can be recorded.
4. Use AI-generated images only for clearly labeled schematic or conceptual
   illustrations. Never use AI images to simulate a real patient's CT/MRI,
   pathology, endoscopy, ECG, laboratory report, skin lesion, operative photo,
   or any case-specific clinical finding.
5. Do not use copyrighted journal figures, textbook figures, hospital photos, or
   identifiable patient images unless the user provides permission and the image
   is de-identified.
6. For anatomy/mechanism visuals, prefer self-drawn SVG diagrams or open
   educational sources with citation.
7. For literature summaries, prefer evidence tables, forest-plot-style summaries
   only when data are provided, and source-labeled diagrams.

In `design_spec.md`, the image resource list must state one of these acquisition
methods for every image: `user`, `self-drawn`, `web-cited`, `ai-schematic`, or
`placeholder`. Avoid generic `ai` for medical decks.

## Preferred PPT Tone

Build slides as if a real clinician or researcher will present them:

- one slide, one clinical question or evidence point;
- conclusion titles should be specific and defensible;
- use case facts before interpretation;
- separate "case evidence", "literature evidence", and "inference";
- include differential diagnosis and decision points when relevant;
- avoid exaggerated certainty when evidence is weak;
- keep visual style clean, academic, and low-decoration.
