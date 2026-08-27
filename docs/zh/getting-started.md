# 快速入门

[English](../getting-started.md) | [Chinese](./getting-started.md)

---

最快做出第一份 deck 的路径、围绕它的各项能力——模板、实时预览、动画、旁白、声音复刻——以及出问题时去哪里查。章节大致按你真实使用时遇到它们的顺序排列。每节都是精简版,需要细节就点 **完整说明 →** 链接。

- [配置安装目录与工作目录](#配置安装目录与工作目录)
- [用模板](#用模板)
- [做出第一份 deck](#做出第一份-deck)
- [实时预览与可视化修改](#实时预览与可视化修改)
- [转场与动画](#转场与动画)
- [旁白与视频](#旁白与视频)
- [使用复刻音色](#使用复刻音色)
- [遇到问题怎么办](#遇到问题怎么办)

---

## 配置安装目录与工作目录

启动 Agent 前，先分清三个目录：

| 目录 | 它是什么 | 怎样产生 |
|---|---|---|
| **Skill 安装目录** | 包含 `SKILL.md`、`requirements.txt`、工作流与脚本的 PPT Master 包 | 完整仓库 clone 或仓库 ZIP 中是 `skills/ppt-master/`；marketplace/plugin 安装或 skill-only release ZIP 则使用自己的安装或解压位置 |
| **工作目录** | 你在 Agent 中打开的、可持久保存且可写的目录 | 完整仓库 clone 或仓库 ZIP 通常使用仓库根目录；skill-only 安装则自行选择，不必是 skill 安装目录 |
| **活动项目** | 一次生成任务的来源、SVG、报告、备份与导出物所在目录 | Agent 会在 `<工作目录>/projects/<生成的项目名>/` 下初始化，并报告精确路径 |

所有安装方式都需要 Python 3.10+，以及一个已经安装和鉴权、能够读写工作目录并执行 shell 命令的 Agent host。完整仓库 clone 或仓库 ZIP 从仓库根目录安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

Skill-only 安装应先找到同时包含 skill 的 `SKILL.md` 与 `requirements.txt` 的安装或解压目录，再从该路径安装：

```bash
python3 -m pip install -r "<installed-skill-dir>/requirements.txt"
```

使用 `npx skills add hugohe3/ppt-master` 还要求本机有可用的 `npx` 命令，通常由 Node.js/npm 提供；仓库没有规定 Node/npm 的最低版本。Host 自带的 `/plugin install` 不走这条 `npx` 路径。安装完成后，从**工作目录**启动 Agent，不要从 host 管理的 skill 缓存目录启动；执行入口会单独解析已安装 skill。安装方式见[快速开始](../../README_CN.md#快速开始)，运行规范见 [`SKILL.md`](../../skills/ppt-master/SKILL.md)。

---

## 用模板

**可选。** 默认走**自由设计**——不需要模板,可以直接跳到下一节。只有当 deck 必须复用品牌身份、沟通与设计方法、固定版式或重复使用的 Deck 应用时,才需要模板。

**复用现成 `.pptx` 有两条路,取决于你想要什么结果:**

| 你想要… | 路径 | 会发生什么 |
|---|---|---|
| **用这份 deck 的原生页面壳承载新内容** | Edit Native PPTX | 导入 round-trip 工作区；未改页面逐字节恢复，`page_plan.json` 可选页、重排、重复或省略，且只编辑计划中的页面。 |
| **先建立可复用设计系统，再生成新 deck** | Create Template → Generate PPTX | 从参考材料创建经过验证的 Brand、Style、Layout 或 Deck 工作区，再创作一份新 deck。新故事、结构与页数都可以不同于来源。 |

前者：把 `.pptx` 连同素材（或一个主题）给 AI，说「套模板」——见 [Edit Native PPTX 工作流](../../skills/ppt-master/workflows/edit-native-pptx.md)。本节其余部分讲 create-template。

**想把某份现成 PowerPoint 做成可复用工作区，必须显式请求 Create Template 路线。** 原生 `.pptx` 加新材料默认属于 Edit Native PPTX，并不是 Generate 可以直接消费的模板工作区。先创建工作区：

```
你：用 /create-template 从 projects/brand/our_deck.pptx 创建一个可复用 Deck 模板
```

Create Template 会分析参考材料，确认结果属于 Brand、Style、Layout 还是 Deck，再创作或物化一个经过验证的新工作区。导入器只提供来源证据；library 工作区拥有 `templates/design_spec.md`，共享 project root 则拥有 `templates/design_spec.<kind>.<id>.md`，以及该 kind 真正需要的原型和素材。Brand 与 Style 不含 roster；Layout 与 Deck 拥有 structured SVG 原型。如果需要 Layout 或 Deck 的 PowerPoint 评审文件，再显式运行可选预览导出；它会按需创建 `exports/<id>_template_preview.pptx`。生成时引用的是工作区根目录。

在 create-template 简报中选择 `library`（沿用原默认）或 `project`。两种范围都要求 `templates/`，并使用可选的 `images/`、`icons/` 和按需生成的 `exports/`；空的可选目录直接省略。项目范围要求给出已初始化的目标项目；只有全局库范围会执行注册。

复刻出的模板可以放在两个位置之一:

| 位置 | 路径 | 说明 |
|---|---|---|
| **注册进 skill 库** | `skills/ppt-master/templates/<kind>/<id>/` | 可移植工作区并执行全局注册；问“有哪些模板”时会被列出来 |
| **放在 projects 下** | `projects/<name>/` | 不执行全局注册的共享限定名 spec root；四种 kind 均可共存，结构由 Layout 优先于 Deck |

Default Generate 把模板选择放在 Stage 1，与沟通契约同屏确认；沟通推荐在此之前不会读取任何模板。普通请求默认自由设计；用户明确要求模板或提供任意精确 root 时，默认进入模板模式，但界面始终允许切换。未注册 root 会进入指定地址下拉框；与注册 canonical root 完全相同的路径会归回对应 kind 下拉框。只提供一个 root 时可预选它；提供多个 root 时都只作为候选、不预选。完整选择中每个 kind 最多一份；Layout 与 Deck 可以共存，结构由 Layout 提供。多 kind project root 必须原子选择。一次确认同时闭合沟通与模板选择，随后才校验、安装所选 root；最终 Stage 2 才读取安装结果。裸模板名不会被解析为工作区。Project root 可直接被其他项目复用；把其中一项迁入 library 时，需要改变 spec 文件名落点并完成注册。

```
你：用 sources/report.pdf 做 deck,模板用 skills/ppt-master/templates/layouts/presentation_core/
```

完整说明 → [模板指南](./templates-guide.md)

---

## 做出第一份 deck

准备好上面的环境和工作目录后，整个流程就三步：

1. **把 Agent 可读取的源材料交给它**——PDF、DOCX、Markdown、网址，或直接粘贴的文字都可以。放在 `<工作目录>/inputs/` 之类的目录即可，不需要先手工创建最终的 `projects/<name>/`。
2. **在对话里告诉 AI** 要把什么做成 deck。[Default Generate Step 2](../../skills/ppt-master/workflows/generate-pptx.md)或[Quick 初始化](../../skills/ppt-master/workflows/profiles/quick-generate.md)会在工作目录的 `projects/` 下创建活动项目，并报告精确项目路径。存在文件型材料时才导入；直接粘贴的文字保留在对话上下文，不需要导入。Default 随后进入 Stage 1，同时确认沟通契约与自由设计/模板使用；Quick 会跳过这些确认阶段。Default 只附上一个精确工作区 root 时，页面可默认进入模板模式并预选该路径：
   ```
   你：用 <报告文件路径.pdf> 做一份 PPT
   你：把这份内容做成 PPT：<粘贴你的文字>
   ```
3. **拿回可编辑的 `.pptx`**。除非显式指定其他输出路径，文件位于 `<活动项目>/exports/<项目名>_<时间戳>.pptx`。完整仓库 clone 或仓库 ZIP 通常对应 `<仓库根目录>/projects/<生成的项目名>/exports/...`；skill-only 安装则对应 `<工作目录>/projects/<生成的项目名>/exports/...`。应以 Agent 报告的活动项目精确路径为准，不要到仓库根目录查找一个没有项目上下文的 `exports/`。

这些术语不是需要你另建的目录。**Stage 1** 会确认沟通契约，即用途、受众、阅读场景、画布/格式，以及自由设计/模板选择。**工作区根目录**是可选的 Brand、Style、Layout 或 Deck 可复用包的根目录，不是活动项目。AI 安装所选工作区后，**Stage 2** 再确认页数、视觉系统、模板应用方式与生产选项。之后内容分析、排版、配图、SVG 生成与导出都由 AI 完成。不想走交互确认，见下方[快速模式](#快速模式)。

---

## 快速模式

默认流程会先进行 Stage 1 的沟通/模板合并确认，再进入最终 Stage 2。不想经过这些交互，就显式要求**快速生成**：

```
你：用 sources/report.pdf 快速生成一份 PPT,不用跟我确认
你：这份内容直接做成 PPT,跳过确认,8 页左右,深色商务风
```

**你明确提的照做,你没提的 AI 直接定,不再回来问你。** 第二个例子里的页数和风格照样生效——快速模式省掉的是来回确认,不是你的话语权。Quick 不会真正生成 Default 的三套方向，而是直接执行 Default 会推荐的方向：自由设计时选整体适配度最高者，已安装模板时选最充分表达模板上下文的可行方向。什么都不提，才是全部交给 AI 决定。

快速模式不会打开 Confirm UI 的模板选择页。每个 kind 最多给出一个精确的
Brand / Style / Layout / Deck 工作区 root，它会直接校验、安装并使用；没有
给出精确 root，就直接自由设计。只写模板名或风格词仍然只是设计说明。
Quick 保持无锁流程，但不丢失模板能力：自由设计及仅 Brand / Style 的输出
保持 flat；一旦提供 Layout / Deck 工作区，创作 SVG 中的显式 Master /
Layout / slot 元数据会保留，并编译成可复用原生结构。P01 前，agent 会读取
全部已安装模板 SVG，并在当前上下文冻结一段自然语言应用方案；不创建确认页
或 spec 工件。

它不跳过能力：来源转换、事实缺口研究、共享美学规范、图片 / 图标准备，以及原生形状 / 图表 / 表格创作仍按需运行。结构性公式直接写成 PowerPoint 原生 marker，不再作为图片素材准备。显式选择的 manual 素材或其他不可替代的文件依赖缺失时，Quick 会阻塞并索取文件；自动 AI 生成或其必需切片路径耗尽时，Quick 会移除失败任务与过期 manifest 条目，改用原生可编辑文字 / SVG 或已经备好的非 AI 素材，继续本次运行，并在最终交接中披露替代结果。

快速模式是一次性生成,不是缩短后的可续接流程。它不产生 Strategist 记录、`design_spec.md`、`spec_lock.md` 或替代性的页面计划;内容、设计和资源决策只存在于 AI 的当前上下文。交付前一旦丢失该上下文,就重新运行 Quick。资源 manifest、质量报告、postflight 与冷 Python 审计日志可以保留,但无法还原 AI 为什么这样设计。该 profile 省掉的是交互和持久规划,不是 PPT 能力或预期质量标准。

完整说明 → [快速模式 profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)

---

## 实时预览与可视化修改

生成过程中会自动打开启动器报告的浏览器预览地址。它优先使用 `http://localhost:5050`，若 `5050` 已被占用则使用下一个空闲端口。

- **实时看着每页渲染**出来。
- **直接改,无需 AI** —— 选中元素后在右栏改文字、颜色、字体、字号;拖拽即可移动,或用方向键微调(`Shift` = 10px),`Ctrl+Z` 撤销。改动即时预览,点 **Apply changes** 写回 `svg_output/`。
- **或写注解交给 AI** —— 点选元素写一句要改成什么，点 **Add annotation** 暂存，再点 **Apply changes** 把注解标记写入 `svg_output/`；回到对话说“应用注解”（或 “apply my annotations”），AI 会改写那块区域并重新导出 PPTX。

PPT Master 最初是纯对话设计;可视化编辑是在很多用户提出后融入的(建立在 [@WodenJay](https://github.com/WodenJay) 的 [PR #85](https://github.com/hugohe3/ppt-master/pull/85) 之上)。

完整说明 → [实时预览阶段](../../skills/ppt-master/workflows/stages/live-preview.md)

---

## 转场与动画

导出的 deck 用真正的 OOXML 保存**页间转场**和可选的**页内元素对象动画**，
不是嵌入视频。默认保留 `fade` 页间转场，页内动画为 `none`；只有显式使用
`-a auto`、203 个原生 `entrance_*` / `emphasis_*` / `path_*` / `exit_*`
预设之一，或 `animations.json` 才会启用对象动画。29 个旧短名称只保留为兼容
输入；新的动画选择统一使用带前缀的规范名称。未知效果、Start
模式、非法时序值或缺失对象引用会直接阻断导出，候选 PPTX 还会在发布前回读
动画目标、效果和 timing 结构。Microsoft PowerPoint 是动效行为的主要验证
目标；Keynote、WPS、LibreOffice 可能重新映射个别效果。

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
| 没有生图 API key | Agent host 提供原生生图时直接使用,否则零配置网络图片搜索仍可用;见 [FAQ](./faq.md)。 |
| 动画或部分效果在别的软件里不对 | Microsoft PowerPoint 是动效行为的主要验证目标。Keynote / WPS / LibreOffice 可以打开 `.pptx`，但可能重新映射或省略个别效果或 Start 语义；动效关键交付应在 PowerPoint 中验证。 |
| 担心长 deck 撑爆上下文 | 生成可走分段模式;详见 [FAQ](./faq.md)。 |

模型选择、费用、图表可编辑性、自定义模板等,都在 [FAQ](./faq.md) 里。
