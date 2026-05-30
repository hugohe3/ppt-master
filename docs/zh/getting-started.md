# 快速入门

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

**想让 deck 复用某份现成 PPT,必须显式走 create-template 流程——别直接丢个 `.pptx` 指望 AI 自动处理。** AI 默认走自由设计,不会主动切进创建模板的流程;不显式启动它,生成过程就容易错乱。先用 create-template 把那份 `.pptx` 复刻成 PPT Master 模板:

```
你：用 /create-template 把这个复刻成模板：projects/brand/our_deck.pptx
```

这会跑 `pptx_template_import.py`,把文件重建成可复用的资产包——版式 SVG + `design_spec.md` + 抽取出的主题色、字体、图片。生成时引用的就是这个资产包。

复刻出的模板可以放在两个位置之一:

| 位置 | 路径 | 说明 |
|---|---|---|
| **注册进 skill 库** | `skills/ppt-master/templates/layouts/<id>/` | 全局,所有项目可复用;跑 `register_template.py` 后,问"有哪些模板"时会被列出来 |
| **放进项目里** | `projects/<project>/templates/` | 项目本地;给路径即用,无需注册 |

无论放哪,生成时都靠在对话里给出它的**目录路径**来引用——工作流只认显式路径,绝不认裸模板名:

```
你：用 sources/report.pdf 做 deck,模板用 skills/ppt-master/templates/layouts/academic_defense/
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
- **点选任意元素**,写一句要改成什么,点 **Submit annotations**。
- **回到对话说一句"应用注解"(或 "apply my annotations")** —— AI 会改写那页 SVG 并重新导出 PPTX。

PPT Master 最初是纯对话设计;可视化编辑是在很多用户提出后融入的(建立在 [@WodenJay](https://github.com/WodenJay) 的 [PR #85](https://github.com/hugohe3/ppt-master/pull/85) 之上)。

完整说明 → [实时预览工作流](../../skills/ppt-master/workflows/live-preview.md)

---

## 转场与动画

导出的 deck 自带**页间转场**和**页内元素入场动画**,输出为真正的 OOXML——不是嵌入视频。默认元素进入页面时自动级联入场,无需设置,在 PowerPoint 和 Keynote 中原生播放,无需额外工具。只有当你想要特定顺序、效果或时序时,才需要定制。

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
| AI 跑偏或漏了步骤 | 让它重新读 `skills/ppt-master/SKILL.md`。 |
| 视觉质量不理想 | 换成大上下文 Claude 模型 + `gpt-image-2`——harness 决定下限,模型决定上限。 |
| 文字溢出或元素重叠 | 重跑那一页,或用实时预览修;详见 [FAQ](./faq.md)。 |
| 没有生图 API key | 零配置的网络图片搜索仍可作为兜底;见 [FAQ](./faq.md)。 |
| 动画或部分效果在别的软件里不对 | 文件是标准 `.pptx`,PowerPoint / Keynote / WPS / LibreOffice 都能打开;元素动画在 PowerPoint 2016+ 和 Keynote 还原最完整,更老的 Office 会把部分效果降级为 Appear。 |
| 担心长 deck 撑爆上下文 | 生成可走分段模式;详见 [FAQ](./faq.md)。 |

模型选择、费用、图表可编辑性、自定义模板等,都在 [FAQ](./faq.md) 里。
