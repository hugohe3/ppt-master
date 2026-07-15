# 常见问题

[English](../faq.md) | [中文](./faq.md)

---

## Q: PPT Master 支持哪些源文件格式？

几乎所有常见格式都支持：**PDF**、**DOCX**、**PPTX**、**EPUB**、**HTML**、**LaTeX**、**RST**、**网页链接**（包括微信公众号文章）、**Markdown**，或者直接在对话中粘贴文字内容。AI 代理会自动将源材料转换为 Markdown 后再生成幻灯片。

## Q: 只有一个主题或想法、没有任何资料，也能生成吗？

可以。直接告诉 AI 你想做的主题或场景（如"做一个关于宫崎骏的 PPT"、"介绍我们公司新产品"），AI 会自动启动 **topic-research 工作流**——通过网页搜索抓取权威来源（Wikipedia / 官网 / 机构发布），整理成 Markdown 资料文档 + 配图集后再走主流程生成幻灯片。

效果取决于公开网页的覆盖度。如果你已有专业资料（论文、内部文档），直接把文件给 AI 比联网检索更准。

## Q: 除了 PPT 还能生成其他格式吗？

可以。除了标准的 **16:9** 和 **4:3** 演示文稿格式，PPT Master 还内置了社交媒体和营销类格式：

| 格式 | 适用场景 |
|------|----------|
| 小红书 3:4 | 图文分享、知识帖 |
| 微信朋友圈 / IG 1:1 | 方形海报、品牌展示 |
| Story / 抖音 9:16 | 竖版故事、短视频封面 |
| 微信文章头图 | 公众号文章封面 |
| A4 印刷 | 印刷海报、传单 |

创建项目时指定格式即可（如 `--format xhs`）。输出仍然是包含原生形状的 `.pptx` 文件。

## Q: PPT Master 支持哪些 AI 工具？

PPT Master 可以在任何能读取文件和执行命令的 AI 编程代理中运行——**Claude Code**（CLI / VS Code / JetBrains / Web）、**VS Code Copilot**、**Codex** 等均可使用。不同工具的使用成本可参考下方的费用对比。

## Q: 我下载过旧版本，怎么更新到最新版？

看你当时怎么安装：

| 安装方式 | 更新方式 |
|---|---|
| Git clone | 在 `ppt-master` 目录运行 `python3 skills/ppt-master/scripts/update_repo.py` |
| Download ZIP | 重新下载最新版 ZIP，解压到新目录；把旧目录里的 `.env` 和 `projects/` 复制过去；再运行 `pip install -r requirements.txt` |
| Skill marketplace | 用对应的 marketplace / skills 工具重新安装或更新 |

长期使用建议用 Git clone。ZIP 适合快速体验，但没有 Git 历史，不能自动 `git pull`。

如果不确定自己是哪种安装方式，可以让 AI 在项目目录里运行：

```bash
python3 skills/ppt-master/scripts/update_repo.py
```

如果当前目录不是 Git clone 版本，脚本会提示你按 ZIP 方式迁移。

## Q: 仓库超过 1 GB，skills 工具下载直接失败——能只拿 skill 吗？

可以。完整仓库确实很大（Git 历史，加上内置的示例 deck 及其素材），而且这个体积是写进历史里的——在不破坏已有大量 fork 的前提下没法瘦身。如果你只想要 skill、不需要完整仓库，用下面的轻量方式：

- **Marketplace CLI**：`npx skills add hugohe3/ppt-master`，或 Claude Code 里的 `/plugin install`，都只拉取 skill 文件（见 README 的「开始设置」一节）。
- **手动下载**：到 [Releases](https://github.com/hugohe3/ppt-master/releases) 页面下载 `ppt-master-skill-*.zip`——只含 skill 文件（约 50 MB），无需 clone 完整仓库。

两种方式装好后，都要在安装目录跑 `pip install -r requirements.txt`，后处理脚本才能工作。

中国大陆地区访问 GitHub 下载不便的话，完整仓库在 [AtomGit](https://atomgit.com/hugohe3/ppt-master) 也有镜像（clone 或下载 ZIP）；1 GB 出头的体积在中国大陆地区网络下载一般没问题。

## Q: 能用 AI 生成配图吗？

可以。PPT Master 内置了图片生成脚本，支持多个供应商（Gemini、OpenAI、FLUX、通义千问、智谱等）。在策略师阶段选择"AI 生图"方案后，流程会根据内容自动生成配图。你也可以使用自己的图片——只需放到项目的 `images/` 目录下即可。

## Q: 没有生图 API Key，还能配图吗？

可以——在策略师的"图片方案"步骤选择"网络图片"。PPT Master 内置了零配置的 `image_search.py`，在 Openverse 和 Wikimedia Commons 中搜索可商用的开放许可图片（无需 API Key）。零配置搜索适合作为兜底：能直接用，但图片质量不稳定，容易出现普通用户上传、构图随意、清晰度一般的素材。

如果想要更现代的商业风照片，建议在 `.env` 里设置 `PEXELS_API_KEY` 和/或 `PIXABAY_API_KEY`（都是免费申请）。搜索会自动纳入 Pexels / Pixabay，人物、办公、生活方式、产品和插画类图片质量通常会明显更稳定。两种路径可以在同一份 deck 里混用（比如 hero 图用 AI 生成、团队照片用网络搜索）；如果选中的图片需要署名，Executor 会在该幻灯片自动添加就地小字署名。

要清楚一点：**网络搜索只负责「找到一张相关、可下载、授权合规的图」，并不保证它在这一页里好看或贴切**——排序只看文字元数据，看不到画面。生成时多模态模型会读一份缩略图自查、不合适会重搜；但**要真正高质量，最可靠的还是你自己去搜**：在任何来源找到更合适的图，把链接给 AI，它会用 `image_search.py --from-url <链接>` 直接下载替换（记为手动来源、版权由你把关）。换图随时能做——生成途中或在实时预览里都行，不会打断流程。简而言之：把网络搜索当「兜底占位」，把人工挑图当「精修」。

## Q: 生成的 PPT 可以编辑吗？

可以。唯一受支持的 PPTX 产物路线，是由项目转换器读取 `svg_output/` 并生成原生 DrawingML `.pptx`；文字、图形和颜色无需额外转换即可编辑，文件以时间戳命名保存至 `exports/`。Executor 的原始 SVG 源（`svg_output/` 副本）始终镜像到 `backup/<timestamp>/svg_output/`，便于归档或基于该版重跑 `finalize_svg → svg_to_pptx` 重建 PPTX，无需再走 LLM。

Step 7 仍会强制生成 `svg_final/`。其中每页都是自包含的视觉预览 SVG，可直接在浏览器或 IDE 中打开，也可作为 SVG 图片手动插入 PowerPoint；项目只保证其作为预览或图片显示，不保证 PowerPoint 手工“转换为形状”后的结果。需要可编辑形状时，请使用 `exports/` 中由项目转换器生成的原生 PPTX。

## Q: 为什么一段正文被拆成了好几个文本框？能不能一段一个文本框？

默认会把可合并的正文段落导出成一个可编辑的 PowerPoint 文本框，内部保留多个段落。**拉伸框时文字会在框内自动重排**。

如果你需要严格保持逐行版式，重新导出时加上 `--no-merge`：

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --no-merge
```

使用 `--no-merge` 时，SVG 里的每一视觉行都会变成一个独立的 PowerPoint 文本框。这样能**逐像素保留 SVG 的版式**，适合封面、图表、表格、以及任何对版式精度敏感的页面。

**代价**：默认合并会保留一个可编辑文本框和原始视觉行边界；只有需要让每一视觉行都能单独移动时才使用 `--no-merge`。判定足够保守——非段落型 `<text>` 会自动落回按行拆框路径。

跟 AI 对话时也可以直接说："这个页面要严格保持逐行版式" —— AI 重新导出时会加上 `--no-merge`。

## Q: 字号为什么用 px 不是 pt？导出后字号会变吗？

PPT Master 内部**全程只用 px**（无单位像素）——确认页、`spec_lock.md`、SVG 都是 px，没有 pt 这一层。原因是 SVG 画布本身就是 1280×720 px，px 是真正的排版/执行单位；只用一个单位，能避免「确认时说 20pt、写进 SVG 又变成另一个数」这类单位混淆导致整套字号偏差。

PowerPoint 最终显示的是 pt，所以**导出时**自动把 px 换成 pt（`pt = px × 0.75`，保留 1 位小数）。例如正文 `24px` 导出后是 `18pt`、标题 `42px` 是 `31.5pt`。所以你在 PowerPoint 里看到 `13.5pt`、`31.5pt` 这种非整数是**正常的、有意的**，不是 bug——字号算出来是多少就是多少，不再强行凑成整数或半磅。

正文基准按**交付目的**固定取值（不是区间）：

| 交付目的 | 正文 px | ≈ 导出 pt |
|---|---|---|
| `text` 文字型（近读：报告 / 资料） | 20px | 15pt |
| `balanced` 均衡（默认：路演 / 评审） | 24px | 18pt |
| `presentation` 展示型（投影 / 发布） | 32px | 24pt |

标题、副标题、脚注等其它角色按比例从正文派生，并取整洁偶数 px。你在确认页可以手动覆盖任何角色的 px 值。

## Q: PPT Master 怎么确定演示的风格？

在第 d 项确认时锁定两个独立维度：

- **Mode（怎么讲）**：`pyramid` / `narrative` / `instructional` / `showcase` / `briefing` —— 见 `references/modes/`
- **Visual style（长什么样）**：`swiss-minimal` / `editorial` / `soft-rounded` / `dark-tech` … + `custom` —— 见 `references/visual-styles/`

任意 mode 可与任意 visual style 自由组合。

## Q: 用 PPT Master 做 PPT 贵吗？

PPT Master 本身免费开源，唯一的成本来自你自己的 AI 模型用量。

目前主流 AI 工具都已转向按量计费——用多少付多少。PPT Master 天然契合这一模型：不需要额外订阅 PPT 平台、没有专有积分、没有按人头收费的演示工具费用。

作为对比，Gamma 订阅 $8–20/月，Beautiful.ai $12–45/月——无论用多少都得付这个底价。PPT Master 在你现有 AI 支出之外不增加任何额外成本。

## Q: 生成的图表可以编辑数据吗？

默认情况下，图表以**自定义设计的 SVG 图形**形式渲染，转换为原生 PowerPoint 形状——形状级别完全可编辑（移动、改色、改文字、调样式）。默认不用 Excel 驱动的图表对象是有意为之：PowerPoint 默认图表样式陈旧、视觉受限于固定模板。SVG 图表则提供出版物级的视觉质量，可以在 PowerPoint 中直接精修，且在 PowerPoint / Keynote / LibreOffice / WPS 间像素一致。

如果你的工作流明确需要 Excel 驱动的数据编辑或 PowerPoint 的图表/表格专属控制，导出时加 `--native-charts-and-tables`：受支持的数据图表和纯文本表格会以**带数据源的 PowerPoint 原生 Chart / Table 对象**形式导出（保存为 `exports/<name>_<timestamp>_native_charts_tables.pptx`，并保留这份 deck 自己的配色，而不是套用 PowerPoint 默认主题）。默认 SVG fallback 同样会转换成可编辑 DrawingML shape，但不具备图表数据工作簿或图表/表格对象模型。原生对象在 PowerPoint / Keynote / LibreOffice / WPS 间可能略有差异，因此形状路线仍是视觉稳定性的默认选择。

## Q: 页面切换和元素动画可以调吗？

可以。页间转场默认开（`fade` 0.4s），页内元素入场动画**默认关**——翻到一页时整页一次性呈现，不会有元素一个个自动级联出来（那种没人要的自动连播正是「AI 味」最重的地方）。两者都通过 `svg_to_pptx.py` 的参数控制——`-t/--transition` 控制页级，`-a/--animation` 控制元素级。想要页内动画时显式开启即可：

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push       # 换转场效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none       # 关闭转场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto       # 开启页内元素入场（按 group id 自动映射效果）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade        # 开启并改用单一效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click   # 单击触发，演讲者控制节奏
```

`on-click` 适合现场演示。通过 `--recorded-narration` 做旁白/视频导出时会拒绝它，因为 PPT Master 只写页面级计时，不生成对象级点击计时；带旁白的 deck 请使用 `after-previous` 或 `with-previous`。

完整效果列表、`<g id="...">` 锚点机制、降级行为、限制：见 [转场与动画](./animations.md)。

## Q: 推荐用什么 AI 模型？

**Claude**（Opus / Sonnet）是推荐且测试最充分的模型。SVG 排版本质上是在绝对坐标系中做精确的数学计算（字号 x 字数 x 容器宽度），Claude 在这方面表现明显优于其他模型。

**GPT 系列**早期版本排版问题较多——文字超出容器、元素错位、坐标计算失误。较新的版本（如 GPT-5.5）在这方面已有明显进步，实际效果可以接受；如果遇到问题，可以告知 AI 修正具体页面。

其他模型（Gemini、GLM、MiniMax 等）效果参差不齐。总体来说，前端/视觉能力越强的模型，生成效果越好。

## Q: 有人说 PPT Master "只是个玩具"——这个评价准确吗？

不准确。PPT Master 是一个 **harness**，不是完整的 agent——`harness + model = agent`，输出上限完全由模型决定，而不是由 harness 本身决定。用弱模型或小上下文窗口来评价 PPT Master，就好比挂着一档开跑车然后说它跑不快。

**发挥完整实力的组合：**

- **Claude 大上下文窗口**（推荐 ~100 万 token 级别）：大上下文让 Executor 在同一个会话里看到全部已生成页面，在不拆分运行的前提下保持整份 deck 的视觉一致性。上下文不足时被迫走拆分模式，两段之间会出现明显的风格漂移。
- **AI 生图，推荐 `gpt-image-2`**（或同等质量）：配图水平是 deck 整体观感的最大变量。用占位级的网络图片和用真正贴合内容的 AI 生成图，视觉效果完全是两个量级。

如果你看到的效果差强人意，先对照以下几点检查你的配置，再下结论：用的什么模型？上下文开了多大？有没有接入图片生成 API？同样的工作流，Claude Opus 配 100 万 token 上下文配 `gpt-image-2` 的结果，和小参数开源模型配零配置的结果，是截然不同的体验。

**harness 决定工作流上限，model 决定质量上限。** 如果 agent 能力不达预期，请先升级模型，再来评价 harness。

> **没有 Claude 渠道？** 本项目赞助商 [PackyCode](https://www.packyapi.com/register?aff=ppt-master) 提供 Claude 及其他主流模型的按量付费接入——无需订阅，无需境外信用卡，支持国内支付，开箱即用。充值时填写优惠码 **`ppt-master`** 享 9 折。

最后再说一句：这是一个免费、个人维护的开源项目。合用就用，能帮到你我很高兴；不合用，换个工具就好。真诚的反馈与建议始终欢迎——这也是项目一点点变好的方式。

## Q: 文字超出边框 / 元素错位怎么办？

这几乎都是模型能力问题，不是 PPT Master 的 bug。SVG 排版是纯手动绝对定位——模型必须准确计算坐标、字体度量和容器尺寸。

**解决办法**：
1. 切换到 **Claude**（Opus 或 Sonnet），如果你用的是其他模型
2. 告诉 AI 哪一页有问题、具体是什么问题——它可以单独重新生成某一页
3. 直接打开 SVG 源文件，让 AI 修正坐标
4. 记住：生成的 PPTX 是**高质量起点**，不是最终成品——在 PowerPoint 中做少量调整是正常的

## Q: 生成一份 PPT 要多久？

一份典型的 10–15 页 PPT 大约需要 **10–20 分钟**（使用吞吐较快的模型）。生成流程是**故意串行的**（逐页生成），这样才能保持前后页面的视觉一致性——并行生成方案曾经测试过，结果是各画各的、缺乏整体观。

如果感觉生成很慢，检查一下模型的 token 吞吐速度。瓶颈通常在模型的输出速度，而不是脚本本身。

## Q: 长 PPT 一次生成会不会上下文爆掉？

默认推荐**一次性连续生成**——10–15 页的 deck 在 200K 上下文窗口下完全够用，跨页视觉一致性也最好（Executor 看到前几页 SVG 后会主动对齐风格、字号、节奏）。

只有信号偏重的场景（页数 ≥ 18 / 源材料很厚 / 走过 topic-research 累积大量 web 抓取），AI 才会在策略师阶段给出**拆分模式**的可选提示：规划会话（策略师确认阶段 + 图片获取）结束后停止当前对话；你新开聊天窗口，输入 `继续生成 projects/<项目名>` 进入执行会话（SVG 生成 + 导出）。新会话从磁盘重新加载 `design_spec` / `spec_lock` / `sources` / `images` 继续执行。

两段式是**折中方案**——付出约 6K tokens 的 SKILL.md 重读成本，换得 60–200K 的规划会话噪声丢弃，并把节省下来的窗口空间用于执行会话主动重读 `sources/` 做内容增稠。**信号正常时不需要**，提示也不会出现；用户随时可以忽略提示，走默认连续模式。

## Q: 能在导出前预览或修正某一页吗？

可以。你可以**随时中断工作流**——前几页生成后就可以查看并反馈意见。AI 可以根据你的意见重新生成特定页面，不需要等到全部完成再修改。

生成后的修正也一样简单，直接告诉 AI："第 3 页布局有问题——标题和图表重叠了"，它会修正那个特定的 SVG。

## Q: 我手上有一份现成的 PPT，想基于它做东西，该走哪条路？

把「用一份已有 PPT」拆成两个问题：**留不留它的内容**、**留不留它的设计（版式 + 视觉）**。四种组合对应四条路：

| 意图 | 路线 | 固定不变的东西 |
|---|---|---|
| 留内容 + 重做版式 | **beautify（美化 / 重排）** | 页数、页序、每页文字、图表/表格数据 |
| 换内容 + 留设计 | **template-fill（套模板）** | 原生页面设计；可选择、乱序、复用源页 |
| 只留内容，设计与分页都重来 | **主管线** | 源事实；故事结构和页数都可重构 |
| 留内容 + 留设计 | 不必生成 | 直接用原文件 |

用 **beautify** 的前提是：原 PPT 的分页本身就是输出要求的一部分。文字逐字不动、页数页序 1:1 保留，只重排版式、层级和留白，并继承原配色字体。典型说法是「把这份 PPT 美化一下 / 重新排版，内容别动」。见 [beautify 工作流](../../skills/ppt-master/workflows/beautify-pptx.md)。

用 **主管线** 的前提是：原 PPT 只是内容材料。流程会用 `ppt_to_md` 抽成 Markdown，并读取 `analysis/` 里的 PPTX intake 事实，再由 Strategist 自由重构大纲（合页 / 拆页 / 换序）。典型说法是「用这份 PPT 的内容重做一份更好的」或「提炼成 10 页高管汇报」。

beautify 和主管线的一句话判别：**原来的分页是要保留的信息，还是只是前一作者的结构、可以推翻？** 保留 → beautify；推翻 → 主管线。落到硬判据就是**页数 / 页序**：只要它有任何变化——拆页、合页、删页、换序，乃至「一字不改、只把某张太挤的页拆开排得更好看」——都属于重分页，走主管线。beautify 严格 1:1。

如果用户说法含糊，比如「把这份 PPT 做得更专业一点」「优化一下这个 deck」，AI 应先问一句：**要保留原页数、页序和每页文字，只做美化；还是把 PPT 当素材，重新梳理成一份新故事？**

还有一条正交的路：如果你不是要现在产出一份 deck，而是想把这套设计**收成可复用模板**供以后反复用，走 **create-template**（见下面「如何制作自定义模板」）。

---

## Q: 我已经有一份做好的 `.pptx`，能不能复用它的设计、只填新内容？

可以——这就是 **套模板（template fill）** 路径，独立于 SVG 生成管线。把你现成的 `.pptx` 连同素材（或一个主题）给 AI，说「套模板 / 把这些填回去」。它会把你的 deck 当作原生页面库，只挑适合新内容的页面（可乱序、可重复），把新文字——以及原生表格单元格、图表数据——直接写回原始 OOXML。

输出仍是 100% 原生可编辑的 PowerPoint：原设计、母版、图片、动画都保留，且只导出选中的页面。它刻意**不**改版式、不加页、不换图——一份 deck 的页面结构本身承载着逻辑（总分、对比、递进），所以应挑选结构本就契合内容的页面，而不是硬塞进去。若需要全新结构或不同页数，请改用 create-template（见下一问）。完整步骤：[套模板工作流](../../skills/ppt-master/workflows/template-fill-pptx.md)。

---

## Q: 如何制作自定义模板？

想把自己喜欢的 PPT 模板制作成 PPT Master 可调用的模板？按以下步骤操作：

**第一步 — 准备参考材料**

**最推荐的方式是直接给原始 `.pptx` 文件**。PPT Master 会提取主题色、字体、Master/Layout、placeholder type/idx、原生形状信息和可复用图片资源。`standard` 与 `fidelity` 把来源当作视觉参考，重新设计 SVG roster 和新的 Master/Layout/slot 系统，不保留、也不蒸馏来源拓扑。`mirror` 则按来源页序恢复 Master/Layout 身份与父子关系、placeholder 事实和受支持的视觉对象，不做语义归纳。由于结构层禁止 `<g>`，来源 Master/Layout 的 group wrapper 只允许机械展开成直接原子。

完整导入 SVG 可以保留高级 PowerPoint 形状所需的 metadata、隐藏 carrier 和预览指纹，并作为载荷后备留在临时分析工作区且保持不可变。模板创建使用带文档内 source ref 和紧凑路径/hash manifest 的轻量可编辑 IR。`standard` / `fidelity` 创作项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从 IR 物化最终模板，只为未改且 hash 匹配的 Slide-local/slot ref 恢复转换器已经支持的载荷；不支持或已修改的对象保留当前 SVG fallback。

没有源 PPTX 时，截图集也能跑（`cover.png` / `toc.png` / `chapter.png` / `content.png` / `closing.png`），但保真度会明显下降。建议优先找原始 PPTX。

**第二步 — 让 AI 创建模板**

使用 AI 编程代理（Claude Code、Codex 等），要求它使用 **PPT Master 的 `/create-template` 工作流**，将这些参考材料转换成模板。提供的信息越详细，效果越好，例如：

- 模板名称和适用场景（如政府汇报、高端咨询、产品宣讲等）
- 期望的风格基调和配色（如"现代克制、深蓝主色调"）
- 类别偏好（`brand` 品牌 / `general` 通用 / `scenario` 场景 / `government` 政务 / `special` 特殊）
- 画布格式（默认 16:9，如需其他格式请注明）
- 输出范围：进入索引的 `library`（默认）或一个已经初始化的 `project`；两者使用相同路由并省略空的可选目录

不需要一次提供所有细节——AI 代理会通过对话追问补齐缺失信息（输出范围、模板 ID、主题模式等）。

**第三步 — 等待完成**

AI 代理会自动完成后续工作——分析参考、构建布局定义并验证模板。如果你明确需要 PowerPoint 审阅文件，它还会按需生成 `exports/<id>_template_preview.pptx`。两种范围都要求 `templates/`，并使用可选的 `images/`、`icons/` 与 `exports/`：`library` 写入 `skills/ppt-master/templates/<kind>/<id>/` 并完成全局注册；`project` 写入 `projects/<name>/` 并跳过注册；空的可选目录直接省略。把这个工作区根目录交给 Step 3 即可，Step 3 不会复制 `exports/`，全局库的预览导出也由 Git 忽略。旧式平铺包仍可把 `design_spec.md` 放在根目录，目录平铺本身不要求恢复结构。

> **提示**：对风格和使用场景描述得越具体，生成的模板就越符合你的预期。

---

> 更多问题可先查看 [skills/ppt-master/SKILL.md](../../skills/ppt-master/SKILL.md) 与 [AGENTS.md](../../AGENTS.md)
