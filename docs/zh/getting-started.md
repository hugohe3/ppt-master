# 快速入门

[English](../getting-started.md) | [Chinese](./getting-started.md)

---

最快做出第一份 deck 的路径、围绕它的各项能力——模板、实时预览、动画、旁白、声音复刻——以及出问题时去哪里查。章节大致按你真实使用时遇到它们的顺序排列。每节都是精简版,需要细节就点 **完整说明 →** 链接。

- [用模板](#用模板)
- [做出第一份 deck](#做出第一份-deck)
- [实时预览与可视化修改](#实时预览与可视化修改)
- [转场与动画](#转场与动画)
- [旁白与视频](#旁白与视频)
- [使用复刻音色](#使用复刻音色)
- [遇到问题怎么办](#遇到问题怎么办)

---

## 用模板

**可选。** 默认走**自由设计**——不需要模板,可以直接跳到下一节。只有当 deck 必须复用一套固定版式或品牌时,才需要模板。

**复用现成 `.pptx` 有两条路,取决于你想要什么结果:**

| 你想要… | 路径 | 会发生什么 |
|---|---|---|
| **用这份 deck 的原生页面壳承载新内容** | Fill Native PPTX | 克隆选中的源页面，并在 OOXML 中直接改写文字 / 表格 / 图表数据。来源设计保持原生；输出是受现有页面壳约束的新回填 deck。 |
| **先建立可复用设计系统，再生成新 deck** | Create Template → Generate PPTX | 从参考材料创建经过验证的 Brand、Layout 或 Deck 工作区，再创作一份新 deck。新故事、结构与页数都可以不同于来源。 |

前者:把 `.pptx` 连同素材(或一个主题)给 AI,说「套模板」——见 [套模板工作流](../../skills/ppt-master/workflows/template-fill-pptx.md)。本节其余部分讲 create-template。

**想把某份现成 PowerPoint 做成可复用工作区，必须显式请求 Create Template 路线。** 原生 `.pptx` 加新材料默认属于 Fill Native PPTX，并不是 Generate PPTX Step 3 可以直接消费的模板。先创建工作区：

```
你：用 /create-template 从 projects/brand/our_deck.pptx 创建一个可复用 Deck 模板
```

Create Template 会分析参考材料，确认结果属于 Brand、Layout 还是 Deck，再创作或物化一个经过验证的新工作区。导入器只提供来源证据；最终工作区拥有 `templates/design_spec.md`、所需 SVG 原型与配套素材。如果需要 PowerPoint 评审文件，再显式运行可选预览导出；它会按需创建 `exports/<id>_template_preview.pptx`。生成时引用的是工作区根目录。

在 create-template 简报中选择 `library`（沿用原默认）或 `project`。两种范围都要求 `templates/`，并使用可选的 `images/`、`icons/` 和按需生成的 `exports/`；空的可选目录直接省略。项目范围要求给出已初始化的目标项目；只有全局库范围会执行注册。

复刻出的模板可以放在两个位置之一:

| 位置 | 路径 | 说明 |
|---|---|---|
| **注册进 skill 库** | `skills/ppt-master/templates/<kind>/<id>/` | 可移植工作区并执行全局注册；问“有哪些模板”时会被列出来 |
| **放在 projects 下** | `projects/<name>/` | 相同的可移植工作区，不执行全局注册 |

两种结果都通过对话里给出**工作区根目录路径**来引用。Step 3 会解析 `templates/design_spec.md`；为兼容目录形态，也接受 `design_spec.md` 直接位于所给根目录、且 SVG 已满足当前合同的平铺工作区。create-template 可在同一对话里把已验证的精确工作区根目录直接交给 Step 3。两种情况都以路径为准，绝不认裸模板名。完整工作区可以在全局库与 `projects/` 之间复制或迁移，无需调整目录结构；只有全局库注册不同。

```
你：用 sources/report.pdf 做 deck,模板用 skills/ppt-master/templates/layouts/presentation_core/
```

完整说明 → [模板指南](./templates-guide.md)

---

## 做出第一份 deck

整个流程就三步。先装好环境——只需要 Python,见 [快速开始](../../README_CN.md#快速开始)。

1. **把源材料放进** `projects/` —— PDF、DOCX、Markdown、一个网址,或直接要粘贴的文字。
2. **在对话里告诉 AI** 要把什么做成 deck(如果上面准备了模板,把它的路径一起给;否则就是自由设计):
   ```
   你：用 projects/q3-report/sources/report.pdf 做一份 PPT
   你：把这份内容做成 PPT：<粘贴你的文字>
   ```
3. **拿回可编辑的 `.pptx`**,位于 `exports/<名称>_<时间戳>.pptx` —— 真正的 DrawingML 形状、文本框、图表,在 PowerPoint / Keynote / WPS / LibreOffice 里点开就能改。

开始前 AI 会先确认一份简短的设计规格(模板、格式、页数……);之后内容分析、排版、配图、SVG 生成、导出都由它完成——这就是其它能力围绕的核心环节。

---

## 实时预览与可视化修改

生成过程中会自动打开浏览器预览 `http://localhost:5050`。

- **实时看着每页渲染**出来。
- **直接改,无需 AI** —— 选中元素后在右栏改文字、颜色、字体、字号;拖拽即可移动,或用方向键微调(`Shift` = 10px),`Ctrl+Z` 撤销。改动即时预览,点 **Apply changes** 写回 `svg_output/`。
- **或写注解交给 AI** —— 点选元素写一句要改成什么,点 **Submit annotations**,再回对话说"应用注解"(或 "apply my annotations"),AI 会改写那块区域并重新导出 PPTX。

PPT Master 最初是纯对话设计;可视化编辑是在很多用户提出后融入的(建立在 [@WodenJay](https://github.com/WodenJay) 的 [PR #85](https://github.com/hugohe3/ppt-master/pull/85) 之上)。

完整说明 → [实时预览阶段](../../skills/ppt-master/workflows/stages/live-preview.md)

---

## 转场与动画

导出的 deck 用真正的 OOXML 保存**页间转场**和可选的**页内元素入场动画**，不是嵌入视频。默认保留 `fade` 页间转场，页内动画为 `none`；只有显式使用 `-a auto`、其它效果或 `animations.json` 才会启用对象入场。未知效果、Start 模式、非法时序值或缺失对象引用会直接阻断导出，候选 PPTX 还会在发布前回读动画目标、效果和 timing 结构。Microsoft PowerPoint 是动效行为的主要验证目标；Keynote、WPS、LibreOffice 可能重新映射个别效果。

完整说明 → [转场与动画](./animations.md)

---

## 旁白与视频

把演讲者备注按页生成语音旁白,把音频嵌回 PPTX,再用 PowerPoint 导出带旁白和转场的 MP4——无需第三方工具。

```
你：给这个 PPT 生成音频,并把音频嵌回重新导出
你：给这个 PPT 生成音频
```

旁白默认用 `edge-tts`(约 90 种语区);需要更高质量音色可配置云端 provider。AI 会按 deck 语言推荐音色,生成前只问你一次。

完整说明 → [音频旁白与视频导出](./audio-narration.md)

---

## 使用复刻音色

用 ElevenLabs / MiniMax / Qwen / CosyVoice 复刻你自己的声音(或在授权前提下复刻演讲者的声音),让整份 deck 用 *你的声音* 念出来。在 provider 控制台复刻一次,把得到的 `voice_id` 传进来,PPT Master 就会用这个音色逐页朗读备注并嵌回 PPTX。

完整说明 → [使用复刻音色](./audio-narration.md#使用复刻音色)

---

## 遇到问题怎么办

[常见问题(FAQ)](./faq.md) 是持续更新的排查真值——来自真实用户反馈。最常见情况的快速指引:

| 情况 | 先试这个 |
|---|---|
| AI 跑偏或漏了步骤 | 让它重新读 `skills/ppt-master/SKILL.md`、`skills/ppt-master/workflows/routing.md` 和已选路线的权威文档。 |
| 视觉质量不理想 | 换成大上下文 Claude 模型 + `gpt-image-2`——harness 决定下限,模型决定上限。 |
| 文字溢出或元素重叠 | 重跑那一页,或用实时预览修;详见 [FAQ](./faq.md)。 |
| 没有生图 API key | 零配置的网络图片搜索仍可作为兜底;见 [FAQ](./faq.md)。 |
| 动画或部分效果在别的软件里不对 | Microsoft PowerPoint 是动效行为的主要验证目标。Keynote / WPS / LibreOffice 可以打开 `.pptx`，但可能重新映射或省略个别效果或 Start 语义；动效关键交付应在 PowerPoint 中验证。 |
| 担心长 deck 撑爆上下文 | 生成可走分段模式;详见 [FAQ](./faq.md)。 |

模型选择、费用、图表可编辑性、自定义模板等,都在 [FAQ](./faq.md) 里。
