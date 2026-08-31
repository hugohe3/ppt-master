# 常见问题

[English](../faq.md) | [中文](./faq.md)

---

## Q: PPT Master 支持哪些源文件格式？

几乎所有常见格式都支持：**PDF**、**DOCX**、**PPTX**、**EPUB**、**HTML**、**LaTeX**、**RST**、**网页链接**（包括微信公众号文章）、**Markdown**，或者直接在对话中粘贴文字内容。AI 代理会自动将源材料转换为 Markdown 后再生成幻灯片。

## Q: DOCX 里的内嵌图片会怎样处理？

DOCX 转换会把内嵌图片素材抽取到配套素材目录，并写入图片清单；来源能提供相应信息时，清单会记录显示尺寸、像素尺寸与宽高比。项目导入会让活动项目可以使用这些配套素材。规划会根据图片在来源中的位置、上下文、caption、alt text、文件名与几何信息，决定某个抽取素材是否使用；不要求查看或使用每一张抽取图片。选中的图片可以完整显示，也可以做保护焦点内容的安全裁剪。抽取和登记**不等于**重新生成图片。

配套素材的输出见[来源转换输出合同](../../skills/ppt-master/scripts/docs/conversion.md)，选用与几何依据见[图片规划合同](../../skills/ppt-master/references/strategist-image.md)。

## Q: 能把 DOCX 里的所有图片批量重画成统一比例和风格吗？

当前没有。现行 Generate 路线没有面向用户的入口，可以批量按参考图重画全部 DOCX 内嵌图片并自动替换原图。Manifest 模式可以根据提示词批量生成**新图**；内置 CLI 的 `--reference-image` 编辑则是独立的单图窄路径，不属于 manifest 模式，而且只适用于受支持的生图后端。图片还原为 PPTX 也不能补上这项能力：它只在栅格输入代表待还原的整页幻灯片画面时触发，普通 Word 照片或插图仍属于来源素材。

这些边界见[图片生成合同](../../skills/ppt-master/references/image-generator.md)、[Generate Step 5](../../skills/ppt-master/workflows/generate-pptx.md)与[图片还原为 PPTX profile](../../skills/ppt-master/workflows/profiles/image-to-pptx.md)。

## Q: 把原图裁成指定比例，与按指定比例生成新图有什么区别？

两者改变的对象不同。`crop=adaptive` 允许但不强制裁剪。Executor 可用 `meet` 完整显示原图，或用保护焦点内容的 `slice` 填满所选容器；两者都复用来源像素。AI 任务的 `aspect_ratio` 是新生成画布的要求。参考图编辑则通过独立的单图路径变换一张给定图片，不是 manifest 批处理。详见[图片资源清单规则](../../skills/ppt-master/references/strategist-image.md)、[Executor 裁剪政策](../../skills/ppt-master/references/executor-image.md)、[SVG 图片放置合同](../../skills/ppt-master/references/svg-image-embedding.md)与[图片 manifest schema](../../skills/ppt-master/references/image-generator.md)。

## Q: 只有一个主题或想法、没有任何资料，也能生成吗？

可以。直接告诉 AI 你想做的主题或场景（如"做一个关于宫崎骏的 PPT"、"介绍我们公司新产品"），Generate PPTX 路线会运行 **topic-research 阶段**，补齐规划所需的事实基础与来源记录。已有部分材料时，只补实现用户目标仍缺少的事实；如果用户要求只使用原材料，则不做外部补充。项目导入不会根据来源记录中的网页 URL 批量抓取材料；常规搜图失败后，才会按需获取一个相关网页及其图片资源包，审阅后只把选中的图片加入项目图池。

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

实际画布与已注册格式完全一致时，初始化可传对应键（如 `--format xhs`）。
其他画布应省略 `--format`；Default Generate 会把确认后的 viewBox 记录到
`spec_lock.md`，Quick Generate 则以第一张 SVG 为画布真值。输出仍然是包含原生形状的
`.pptx` 文件。

## Q: PPT Master 支持哪些 AI 工具？

PPT Master 可以在任何能读取文件和执行命令、支持 Agent 的 AI 工具中运行——**Claude Code**（CLI / VS Code / JetBrains / Web）、**VS Code Copilot**、**Codex** 等均可使用。所选 host 负责自身的安装与鉴权；安装后的工作目录模型见[快速入门](./getting-started.md)。

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
- **手动下载**：到 [Releases](https://github.com/hugohe3/ppt-master/releases) 页面下载 `ppt-master-skill-*.zip`——只含 skill 文件（约 56 MB），无需 clone 完整仓库。

两种 skill-only 方式装好后，找到同时包含 `SKILL.md` 与 `requirements.txt` 的 skill 安装目录，再运行 `python3 -m pip install -r "<installed-skill-dir>/requirements.txt"`，后处理脚本才能工作。

这两条路径都不带 `.git` 目录，`git describe` 查不到版本。已安装的版本记录在 skill 自身 `SKILL.md` frontmatter 的 `metadata.version` 字段里。

中国大陆地区访问 GitHub 下载不便时，可以从 [AtomGit](https://atomgit.com/hugohe3/ppt-master) 的完整仓库镜像 clone 或下载 ZIP。

## Q: 通过 Skill marketplace 安装后，还需要什么环境，应该在哪个目录运行？

所有安装方式都需要 Python 3.10+，以及一个已安装、已鉴权、能够读写文件并执行 shell 命令的 Agent host。使用 `npx skills add hugohe3/ppt-master` 还要求本机有可用的 `npx` 命令，通常由 Node.js/npm 提供；仓库没有声明 Node/npm 的最低版本。Host 自带的 `/plugin install` 不走这条 `npx` 路径。

Skill 安装目录与工作目录承担不同角色。Python 依赖从包含已安装 skill 的 `SKILL.md` 和 `requirements.txt` 的目录安装；Agent 则应从你自行选择的、可持久保存且可写的工作目录启动。Agent 会按需在这个工作目录下创建 `projects/`，不需要从 host 管理的 skill 缓存目录运行。详见[快速入门：配置安装目录与工作目录](./getting-started.md#配置安装目录与工作目录)和 skill 的[执行入口](../../skills/ppt-master/SKILL.md)。

## Q: macOS 或 Linux 怎样做与 Windows 相同的最小安装验证？

安装 Python 依赖后，运行 Windows 指南使用的同一条核心导入检查：

```bash
python3 -c "import pptx; import fitz; print('All core dependencies OK')"
```

然后让 Agent 用 Quick 模式生成一份无来源文件的 3 页 “Hello World” deck。导入命令只检查核心 Python 包；Quick 运行会连同项目初始化、SVG 创作、校验和导出一起检查。成功标志是活动项目的 `exports/` 目录出现 PPTX，并且该文件能在演示文稿应用中打开。依据见 [Windows 安装 smoke](./windows-installation.md)和[快速模式 profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

## Q: 需要手工创建 `projects/<name>` 吗？最终文件在哪个 `exports/`？

不需要。由 Agent 执行时，Default Generate Step 2 或 Quick 初始化会创建活动项目，通常位于 `<工作目录>/projects/<生成的项目名>/`，并报告它的精确路径。使用默认导出路径时，PPTX 属于这个活动项目：

```text
<活动项目>/exports/<项目名>_<时间戳>.pptx
```

它不是仓库根目录下一个没有项目上下文的 `exports/`；只有显式指定输出路径时例外。依据见 [Generate 的项目初始化与导出](../../skills/ppt-master/workflows/generate-pptx.md)、[快速模式 profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)和[工作目录说明](./getting-started.md#配置安装目录与工作目录)。

## Q: 能用 AI 生成配图吗？

可以。Agent host 提供原生生图工具时，PPT Master 可直接使用，不需要另配供应商生图 API Key；也可以通过内置 `image_gen.py` 使用已配置的供应商后端。图片方案选择"AI 生图"即可，也可明确要求 Agent 使用自身生图工具。你还可以把自己的图片放到项目的 `images/` 目录下。

## Q: 为什么没有图标？图标应该默认出现在每一页吗？

不要求逐页使用图标。Default 中的 `No base icons` 与 Emoji、内置 SVG 图标、自定义项目图标一样，都是合法的确认选项。Default 的 `icons.inventory` 只索引其精选的已备素材池，不会把图标分配到页面。两种 profile 都可以使用项目内已备图标；Quick 不创建通用资源 roster，也不创建逐页图标分配表。只有页面沟通任务需要时才会使用图标，因此整份 deck 或某一页可以不用。AI 生成的插画图标切片属于另一条图片素材路径，同样不是必选项。

依据见[策略师的图标选择](../../skills/ppt-master/references/strategist.md)、[执行器的图标用法](../../skills/ppt-master/references/executor-base.md)与[Quick 资源准备](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

## Q: 没有生图 API Key，还能配图吗？

可以。Agent host 提供原生生图能力时，选择"AI 生图"并要求它使用自身生图工具，不需要供应商生图 API Key。否则可在策略师的"图片方案"步骤选择"网络图片"；PPT Master 内置零配置的 `image_search.py`，在 Openverse 和 Wikimedia Commons 中搜索可商用的开放许可图片。零配置搜索适合作为兜底：能直接用，但图片质量不稳定，容易出现普通用户上传、构图随意、清晰度一般的素材。

如果想要更现代的商业风照片，建议在 `.env` 里设置 `PEXELS_API_KEY` 和/或 `PIXABAY_API_KEY`（都是免费申请）。搜索会自动纳入 Pexels / Pixabay，人物、办公、生活方式、产品和插画类图片质量通常会明显更稳定。两种路径可以在同一份 deck 里混用（比如 hero 图用 AI 生成、团队照片用网络搜索）；如果选中的图片需要署名，Executor 会在该幻灯片自动添加就地小字署名。

要清楚一点：**网络搜索只负责「找到一张相关、可下载、授权合规的图」，并不保证它在这一页里好看或贴切**——排序只看文字元数据，看不到画面。生成时多模态模型会读一份缩略图自查、不合适会重搜；但**要真正高质量，最可靠的还是你自己去搜**：在任何来源找到更合适的图，把链接给 AI，它会用 `image_search.py --from-url <链接>` 直接下载替换（记为手动来源、版权由你把关）。换图随时能做——生成途中或在实时预览里都行，不会打断流程。简而言之：把网络搜索当「兜底占位」，把人工挑图当「精修」。

## Q: 能把 AI 生成的 PPT 效果图或截图还原成可编辑 PowerPoint 吗？

可以。提供一张或多张图片，并要求把其中的页面还原为可编辑 PPTX，PPT Master 就会把请求路由到**图片还原为 PPTX**（[`image-to-pptx`](../../skills/ppt-master/workflows/profiles/image-to-pptx.md)）profile。该 profile 当前要求在 Codex 中使用；其他 Agent host 尚未适配，不对其行为作支持或承诺。图片还原为 PPTX 始终直接启用 Quick，不需要另行说明“快速模式”。它会先把所有输入规范化为一份有序页面画面清单，所以最终页数由实际页面画面决定，而不是由文件数决定。

普通可见文字会还原为原生可编辑文本。Logo、图标、徽标和装饰图形在原图足够清晰时直接使用；像素过低时可由 Codex 根据参考图重建，但必须锁定身份、轮廓、比例、颜色和字标，禁止换成仅仅相似的替代物。Chart、table 和 data graphic 禁止生成式重建：必须使用可核对数值的原生对象、精确源资产，或标记 `manual_required`。照片和插画场景至少拆成干净背景层与人物 / 前景层。多个带 padding 包围盒且互不重叠的对象可共用一次生成 plate，再通过 grid slice 或 SVG bbox crop 拆成 PowerPoint 中的独立图片对象。AI 可以补全拆层后露出的隐藏场景像素，但不能改掉可见构图。把整页截图铺底、只叠少量可编辑元素，不算还原成功。

## Q: 生成的 PPT 可以编辑吗？

可以。SVG 管线统一由项目转换器读取 `svg_output/` 并生成原生 DrawingML `.pptx`；文字、图形和颜色无需额外转换即可编辑，文件以时间戳命名保存至活动项目的 `exports/`。使用默认输出路径时，Default Generate 与 Quick Generate 都会把作者源 `svg_output/` 镜像到 `backup/<timestamp>/svg_output/`，便于归档或基于该版重新导出 PPTX，无需再走 LLM。对 Quick 而言，这只是包重建，不是可恢复的 AI 设计决策记录。

默认 Generate 流程的 Step 7 仍会强制生成 `svg_final/`。其中每页都是自包含的视觉预览 SVG，可直接在浏览器或 IDE 中打开，也可作为 SVG 图片手动插入 PowerPoint；显式快速生成会跳过这项预览产物，但在无锁最终质量检查通过后，仍保留普通 postflight 报告和默认输出路径下的备份。项目只保证 `svg_final/` 作为预览或图片显示，不保证 PowerPoint 手工“转换为形状”后的结果。需要可编辑形状时，请使用 `exports/` 中由项目转换器生成的原生 PPTX。

## Q: 多行文本会怎样导出？可以让 PowerPoint 自动重排吗？

默认会把可合并的多行文本块导出成一个可编辑的 PowerPoint 文本框，保留作者断行并禁用 PowerPoint 自动换行，因此拉伸文本框不会重写作者排好的行。普通生成文本框使用 PowerPoint 原生的“根据文字调整形状大小”：删除保留的换行后，文本框会随文字扩展，不会让文字留在框外。导入的精确文本框和结构化多行占位符 carrier 保持原有的固定尺寸行为。

如果需要让 PowerPoint 自动重排适合流动的正文，请使用 `--reflow-text`：

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --reflow-text
```

该模式会恢复段落自动重排，最终行数可能改变。旧参数 `--merge-paragraphs` 是 `--reflow-text` 的兼容别名。

只有每一视觉行都必须成为独立的 PowerPoint 文本框时，才使用 `--no-merge`：

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path> --no-merge
```

该模式保留逐行独立的对象位置，但 12 行正文会变成 12 个文本框。与 AI 对话时，可以直接说“允许文字自动重排”或“每一视觉行使用独立文本框”，由它选择对应的导出模式。

## Q: 字号为什么用 px 不是 pt？导出后字号会变吗？

PPT Master 内部**全程只用 px**（无单位像素）——确认页、`spec_lock.md`、SVG 都是 px，没有 pt 这一层。原因是 SVG 画布本身就是 1280×720 px，px 是真正的排版/执行单位；只用一个单位，能避免「确认时说 20pt、写进 SVG 又变成另一个数」这类单位混淆导致整套字号偏差。

PowerPoint 最终显示的是 pt，所以**导出时**自动把 px 换成 pt（`pt = px × 0.75`，保留 1 位小数）。例如正文 `24px` 导出后是 `18pt`、标题 `42px` 是 `31.5pt`。所以你在 PowerPoint 里看到 `13.5pt`、`31.5pt` 这种非整数是**正常的、有意的**，不是 bug——字号算出来是多少就是多少，不再强行凑成整数或半磅。

正文基准按**阅读模式**固定取值（不是区间）。它控制阅读距离与信息密度，与开放式沟通意图是两条独立轴：

| 阅读模式 | 正文 px | ≈ 导出 pt |
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

## Q: 结果看起来只有框和线，应该先核对哪些运行事实？

PPT Master 没有文档化的 `wireframe` 运行模式，也没有跨版本视觉等价保证，因此不能只凭观感判定版本回归。先记录本次使用 Default 还是 Quick，以及实际的 mode、visual style、图片方案、基础图标选择、Custom Animations 设置和资源备妥状态。Quick 不写 `design_spec.md` 或 `spec_lock.md`，这些决定只保留在 Agent 的当前上下文。

再比较活动项目 `svg_output/` 中的同一页与导出的 PPTX。SVG 本身已经稀疏时，应检查规划、资源与 SVG 创作层；SVG 中存在预期对象、PPTX 却丢失或改变时，才检查转换或渲染层。这个分界依据 [Materials → Plan → Realization](./technical-design.md)、[Default Generate 工作流](../../skills/ppt-master/workflows/generate-pptx.md)与[快速模式 profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

## Q: PPT Master 如何计费？复用模板会降低 token 用量吗？

按你的 AI 用量计费，不额外收订阅费。

仓库所说的模板复用，是复用身份、方法、结构或重复应用合同；当前没有文档化的测量或保证表明模板复用会改变 token 用量。依据见[产品定位](../../README_CN.md#产品定位)与[模板边界](./templates-guide.md)。

## Q: 生成的图表可以编辑数据吗？

默认情况下，图表以**自定义设计的 SVG 图形**形式渲染，转换为原生 PowerPoint 形状——形状级别完全可编辑（移动、改色、改文字、调样式）。默认不用 Excel 驱动的图表对象是有意为之：PowerPoint 默认图表样式陈旧、视觉受限于固定模板。SVG 图表则提供出版物级的视觉质量，可以在 PowerPoint 中直接精修，且在 PowerPoint / Keynote / LibreOffice / WPS 间像素一致。

如果你的工作流明确需要 Excel 驱动的数据编辑或 PowerPoint 的图表/表格专属控制，导出时加 `--native-charts-and-tables`：受支持的数据图表和纯文本表格会以**带数据源的 PowerPoint 原生 Chart / Table 对象**形式导出（保存为 `<活动项目>/exports/<name>_<timestamp>_native_charts_tables.pptx`，并保留这份 deck 自己的配色，而不是套用 PowerPoint 默认主题）。默认 SVG fallback 同样会转换成可编辑 DrawingML shape，但不具备图表数据工作簿或图表/表格对象模型。原生对象在 PowerPoint / Keynote / LibreOffice / WPS 间可能略有差异，因此形状路线仍是视觉稳定性的默认选择。

## Q: 公式可以编辑吗？

可以，但支持目标是 PowerPoint。PPT Master 会把独立块级公式和同段行内
公式都导出为可编辑 OMML，而不是截图或图片资源。块级公式使用 formula
group；行内公式使用夹在普通文本 run 中的叶子
`<tspan data-pptx-inline-formula="...">preview</tspan>`。矩阵、多行推导等
高结构表达仍使用块级形式。原始 LaTeX 不能直接在 SVG 中显示，因此每个
marker 都携带普通可见预览；原生导出会替换该预览，不增加图片兜底。

前向编译覆盖 Microsoft 文档中 Microsoft 365 2606 / Mac 16.110 LaTeX
档位与 2605 / 16.109 mhchem 档位明确点名的全部输入，包括符号、结构、环境、
宏、化学式、公式局部颜色及文档规定的原生归一化。未知或明确不支持的输入直接
失败，不会以原始 LaTeX 混进页面。PPTX 导入则复用同一封闭 OMML 校验器提供
窄反向路径：PPT Master 自有的块级与行内数学内容会恢复为带可见 SVG 预览的
规范公式 marker。这里恢复的是归一化语义，不是作者原始 LaTeX 写法，也不是任意
第三方 OMML 转换；未知 OMML 在 tolerant 模式下会被报告，并以可读 / 不透明
fallback 保留。

生成的 OMML 仍以 PowerPoint 2010+ 包为目标，可执行输入档位锁定到上述
Microsoft 文档版本。仓库验证覆盖编译器行为、OMML 结构与 PPTX 打包，不等同于
完整的 Microsoft 365 UI 显示 / 编辑认证。Keynote、WPS、LibreOffice 等非
PowerPoint 客户端中的公式显示与编辑能力不在支持范围内；PPT Master 不为这些
客户端附加公式图片兜底。

## Q: 生成的页面可以带可点击链接吗？

可以。PPT Master 支持整体对象或行内文字 run 上的 PowerPoint 原生链接。
外部目标使用 `https:`、`mailto:` 等绝对 URI；deck 内跳转使用精确的 1-based
`#slide-N`。两类链接都从标准 SVG `<a href>` anchor 编译为原生 click
relationship，受支持的 PPTX 回导也会重建同一种 SVG 表达。

这是超链接合同，不是通用 PowerPoint action API。鼠标悬停、custom show、
导航命令、程序 / macro / OLE / file 以及任意 action setting 不会被创作。
carrier 与保留边界见 [PowerPoint ↔ SVG 映射指南](./powerpoint-svg-mapping.md)。

## Q: 为什么没有页内元素动画？动画被移除了吗？

动画没有被移除。页间转场默认开（`fade` 0.4s），页内元素对象动画**默认关**——翻到
一页时整页一次性呈现，不会自动逐个级联。两者都通过 `svg_to_pptx.py` 的
参数控制：`-t/--transition` 控制页级，`-a/--animation` 控制元素级。对象
注册表已经包含进入、强调、动作路径和退出效果。
`pptx_to_svg.py` 也会把当前注册表内可精确读回的页面切换和具有精确时长的
有限对象动画记录重建到 `animations.json`；不支持的来源 timing 会保留明确诊断。

整份 deck 的自动入场可用 `-a auto`，统一效果可传规范效果名，逐页 / 逐对象时序则使用项目级 `animations.json`。Default 在已有 sidecar、显式逐页 / 逐对象请求，或有效的 Custom Animations 结果已启用时运行自定义阶段。Quick 在 sidecar 或当前上下文的动效决定需要对象级工作时运行；录制、自运行或视频导向的 Quick 交付必须进入该阶段，除非用户显式要求静态或只用页间转场。只涉及整份 deck 的要求可以保留为导出参数。所有触发都不成立时，保留 `fade` / `none` 默认值。触发边界见 [Generate 工作流](../../skills/ppt-master/workflows/generate-pptx.md)与[快速模式 profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push       # 换转场效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none       # 关闭转场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto       # 开启页内元素入场（按 group id 自动映射效果）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade # 开启并改用单一规范效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation emphasis_spin # 原生强调效果
python3 skills/ppt-master/scripts/pptx_animations.py --list             # 完整分类效果清单
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click   # 单击触发，演讲者控制节奏
```

`on-click` 适合现场演示。通过 `--recorded-narration` 做旁白/视频导出时会拒绝它，因为 PPT Master 只写页面级计时，不生成对象级点击计时；带旁白的 deck 请使用 `after-previous` 或 `with-previous`。

常用命令、Start 模式选择与对象级自定义见[转场与动画](./animations.md)；精确效果与校验行为由其中链接的执行规范维护。

## Q: 推荐用什么 AI 模型？

**Claude**（Opus / Sonnet）是推荐且测试最充分的模型。SVG 排版本质上是在绝对坐标系中做精确的数学计算（字号 x 字数 x 容器宽度），Claude 在这方面表现明显优于其他模型。

**GPT 系列**早期版本排版问题较多——文字超出容器、元素错位、坐标计算失误。较新的版本（如 GPT-5.5）在这方面已有明显进步，实际效果可以接受；如果遇到问题，可以告知 AI 修正具体页面。

其他模型（Gemini、GLM、MiniMax 等）效果参差不齐。总体来说，前端/视觉能力越强的模型，生成效果越好。

## Q: 有人说 PPT Master "只是个玩具"——这个评价准确吗？

不准确。PPT Master 是演示文稿工作流，不是模型，也不是完整 agent。它提供演示文稿专用的推理、合同、项目状态、确定性转换与质量门；最终质量上限仍由所选模型决定。用弱模型或小上下文窗口来评价这套工作流，就好比挂着一档开跑车然后说它跑不快。

**发挥完整实力的组合：**

- **Claude 大上下文窗口**（推荐 ~100 万 token 级别）：大上下文让 Executor 在同一个会话里看到全部已生成页面，在不拆分运行的前提下保持整份 deck 的视觉一致性。上下文不足时被迫走拆分模式，两段之间会出现明显的风格漂移。
- **AI 生图，推荐 `gpt-image-2`**（或同等质量）：配图水平是 deck 整体观感的最大变量。用占位级的网络图片和用真正贴合内容的 AI 生成图，视觉效果完全是两个量级。

如果你看到的效果差强人意，先对照以下几点检查你的配置，再下结论：用的什么模型？上下文开了多大？有没有接入图片生成 API？同样的工作流，Claude Opus 配 100 万 token 上下文配 `gpt-image-2` 的结果，和小参数开源模型配零配置的结果，是截然不同的体验。

> **没有 Claude 渠道？** 本项目赞助商 [PackyCode](https://www.packyapi.ai/register?aff=ppt-master) 提供 Claude 及其他主流模型的按量付费接入——无需订阅，无需境外信用卡，支持国内支付，开箱即用。充值时填写优惠码 **`ppt-master`** 享 9 折。

最后再说一句：这是一个免费、个人维护的开源项目。合用就用，能帮到你我很高兴；不合用，换个工具就好。真诚的反馈与建议始终欢迎——这也是项目一点点变好的方式。

## Q: 文字超出边框 / 元素错位怎么办？

原因取决于偏差出现在哪一层。如果源 SVG 本身已经溢出或错位，通常属于创作 / 排版问题：模型需要准确计算坐标、字体度量和容器尺寸。如果 SVG 预览正确、导出的 PPTX 却不同，则可能是转换器或渲染器问题，应连同两份产物一起反馈。

**解决办法**：
1. 对比 `svg_output/` 中的页面与导出 PPTX，先区分创作问题和转换问题
2. 告诉 AI 哪一页有问题、具体是什么问题——它可以单独重新生成某一页
3. 如果 SVG 本身持续出错，换更强的模型，或让 AI 直接修正坐标
4. 记住：生成的 PPTX 是**高质量、可编辑的草稿**，不是封闭的最终成品——在 PowerPoint 中做少量收尾是正常的

## Q: 生成一份 PPT 要多久？

一份典型的 10–15 页 PPT 大约需要 **10–20 分钟**（使用吞吐较快的模型）。生成流程是**故意串行的**（逐页生成），这样才能保持前后页面的视觉一致性——并行生成方案曾经测试过，结果是各画各的、缺乏整体观。

如果感觉生成很慢，检查一下模型的 token 吞吐速度。瓶颈通常在模型的输出速度，而不是脚本本身。

如果你想要的是少走流程、而不是换模型，可以显式要求快速生成：它省略策略师分析与确认停顿，但仍需逐页创作 SVG。仓库不承诺 Quick 会固定缩短多少时间。见下一问「不想先确认设计规格，能直接生成吗？」。

## Q: 不想先确认设计规格，能直接生成吗？

可以。请显式要求**快速生成**，Generate 路线会启用 [`quick-generate` profile](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

**它跳过的是策略师分析、`design_spec.md` / `spec_lock.md` 落盘和分步确认停顿：你明确提出的要求照做；你没提的，当前 Agent 直接决定并继续，不再回来征求同意。** 什么都不提，才是全部由 Agent 决定。它同时跳过 `finalize_svg.py`，因此不生成 `svg_final/` 预览。

它不跳过备料或设计能力：来源转换、已识别事实缺口的研究、共享美学参考，以及生成 deck 所需的资源仍按需准备——用户提供或源文件抽取的图片、AI / 网络 / 切片图片、项目图标、原生形状、图表 / 表格，以及对应的必要运行 manifest 或来源记录。公式由当前 Agent 直接写成受影响 SVG 中的 PowerPoint 原生 marker，不再作为图片资源准备。显式选择的 manual 路径或其他不可替代的文件依赖未就绪时，Quick 会阻塞并索取文件。自动 AI 生成或其必需切片路径耗尽时，Quick 则会移除失败任务与过期 manifest 条目，改用原生可编辑文字 / SVG 或已经备好的非 AI 素材承载原沟通任务，继续本次运行，并在最终交接中披露替代结果；它不会拿无关材料顶替。备料完成后，当前 Agent 按共享规范手写 `svg_output/`，运行无锁的 Quick 最终质量检查并修复所有阻塞错误，之后才导出最终 PPTX。

原生图表 / 表格替换、讲稿、动效、旁白和诊断等普通导出能力仍可按需使用；讲稿、自定义对象动画和旁白默认关闭，Agent 可在用户要求或 deck 确有需要时自动启用，不会打开确认流程。使用默认输出路径时会生成普通 postflight 报告，并把 `svg_output/` 备份到 `backup/`；显式指定输出路径时沿用普通流程不创建备份的行为。页数本身既不会自动触发，也不会阻止快速生成。

Quick 省略独立规划阶段，但仓库没有文档化的测量或保证表明它会降低多少 token；逐页 SVG 创作仍然存在。Quick 保留同一套页面级视觉与资源创作能力，以及共享的 SVG / 资源阻塞标准；它不运行 Spec Lock 对齐检查，也不从 lock 派生当前项目 Theme。Flat Quick 保留转换器默认 Theme 脚手架；structured Quick 在工作区提供时保留逐 Master 源 Theme，并从语义 slot carrier 推导 Master 标题／正文字号默认值。由于没有已确认的设计契约或可恢复的决策历史，它不承诺与 Default 作出相同设计，也不承诺具体耗时。

## Q: 长 PPT 一次生成会不会上下文爆掉？

默认推荐**一次性连续生成**——10–15 页的 deck 在 200K 上下文窗口下完全够用，跨页视觉一致性也最好（Executor 看到前几页 SVG 后会主动对齐风格、字号、节奏）。

当前 AI 编辑器若支持隔离研究子代理，`topic-research` 会把原始网页抓取留在该上下文，主会话只读取落盘的研究摘要和事实来源文件。

只有信号偏重的场景（页数 ≥ 18 / 源材料很厚 / 本地回退研究后主会话仍保留大量研究材料，或导入的研究摘要本身异常庞大），AI 才会在策略师阶段给出**拆分模式**的可选提示：规划会话（策略师确认阶段 + 图片获取）结束后停止当前对话；你新开聊天窗口，输入 `继续生成 projects/<项目名>` 进入执行会话（SVG 生成 + 导出）。新会话从磁盘重新加载 `design_spec` / `spec_lock` / `sources` / `images` 继续执行。

两段式是**折中方案**——新会话需付出重载 Generate 权威文档与必需执行引用的固定成本，但可丢弃规划会话噪声，并把节省下来的窗口空间用于主动重读 `sources/` 做内容增稠。**信号正常时不需要**，提示也不会出现；用户随时可以忽略提示，走默认连续模式。

## Q: 能在导出前预览或修正某一页吗？

可以。你可以**随时中断工作流**——前几页生成后就可以查看并反馈意见。AI 可以根据你的意见重新生成特定页面，不需要等到全部完成再修改。

生成后的修正也一样简单，直接告诉 AI："第 3 页布局有问题——标题和图表重叠了"，它会修正那个特定的 SVG。

## Q: 我手上有一份现成的 PPT，想基于它做东西，该走哪条路？

把「用一份已有 PPT」拆成两个问题：**留不留它的内容**、**留不留它的设计（版式 + 视觉）**。四种组合对应三种处理路径，以及直接保留原文件这一种无需生成的结果：

| 意图 | 路线 | 固定不变的东西 |
|---|---|---|
| 留内容 + 重做版式 | **Generate PPTX + beautify profile** | 页数、页序、每页文字、图表/表格数据 |
| 换内容 + 留设计 | **Edit Native PPTX** | 保留原生设计；未改页面逐字节保留，选中页面可编辑、重排、重复或省略 |
| 只留内容，设计与分页都重来 | **Generate PPTX** | 源事实；故事结构和页数都可重构 |
| 留内容 + 留设计 | 不必生成 | 直接用原文件 |

使用 **beautify profile** 的前提是：原 PPT 的分页本身就是输出要求的一部分。文字逐字不动、页数页序 1:1 保留，并重排版式、层级和留白。源配色与字体是推荐且预选的默认值；用户显式要求或最终确认可以覆盖视觉字段，但 Beautify 不会在未经确认时静默偏离源身份。典型说法是「把这份 PPT 美化一下 / 重新排版，内容别动」。见 [beautify profile](../../skills/ppt-master/workflows/profiles/beautify-pptx.md)。

用 **主管线** 的前提是：原 PPT 只是内容材料。流程会用 `ppt_to_md` 抽成 Markdown，并读取 `analysis/` 里的 PPTX intake 事实，再由 Strategist 自由重构大纲（合页 / 拆页 / 换序）。典型说法是「用这份 PPT 的内容重做一份更好的」或「提炼成 10 页高管汇报」。

只有在可见设计会被重新生成时，才用这句话区分 beautify 与普通 Generate：**原来的分页是要保留的信息，还是只是前一作者的结构、可以推翻？** 保留 → beautify；推翻 → 普通 Generate。beautify 严格 1:1。若原生设计必须保留，则改走 Edit Native PPTX；它的 `page_plan.json` 可以选择、重排、重复或省略既有页面，而不重设计这些页面。

如果用户说法含糊，比如「把这份 PPT 做得更专业一点」「优化一下这个 deck」，AI 应先问一句：**要保留原页数、页序和每页文字，只做美化；还是把 PPT 当素材，重新梳理成一份新故事？**

还有一条正交的路：如果你不是要现在产出一份 deck，而是想把这套设计**收成可复用模板**供以后反复用，走 **create-template**（见下面「如何制作自定义模板」）。

---

## Q: 我已经有一份做好的 `.pptx`，能不能复用它的设计、只填新内容？

可以——这就是 **Edit Native PPTX** 路线，独立于 Generate。把现成的 `.pptx` 连同素材（或一个主题）给 AI，说「套模板 / 把这些填回去」。它会把 deck 导入 `projects/` 下保留来源的 round-trip 工作区，把来源页面当作原生页面库，并在编辑选中内容前选择、重排、重复或省略页面。

未改的输出页面会被引用并逐字节恢复；在编辑过的页面上，未改对象恢复为原生形态，只有改过的对象会重建。`page_plan.json` 中有序的 `pages` 清单使用 `source_slide` 和可选的 SVG 副本文件名选择、重排、重复或省略来源页面。讲稿、旁白、计时和转场都作为保留页面上的叠加内容。一份 deck 的页面结构本身承载着逻辑（总分、对比、递进），所以应挑选结构本就契合内容的页面，而不是硬塞进去。若源页面库缺少所需的新结构，请走普通 Generate，或先 Create Template、再从产出的工作区 Generate。完整步骤：[Edit Native PPTX 工作流](../../skills/ppt-master/workflows/edit-native-pptx.md)。

---

## Q: 内容填到了意料之外的位置——怎么查看 PPT Master 到底识别到了什么？

Edit Native PPTX 与 Create Template 都会在开始创作前写出可读清单，用它确认识别到的页面和对象。

**Edit Native PPTX**：

```bash
python3 skills/ppt-master/scripts/pptx_to_svg.py <deck.pptx> \
  -o projects/<slug> --inheritance-mode both --roundtrip
```

`authoring-svg-flat/authoring_summary.json` 会列出来源页面清单，以及逐页文字、图片、矢量、placeholder 和 source-reference 数量；只打开确实要判断或编辑的紧凑 SVG 页面。

**Create Template**：

```bash
python3 skills/ppt-master/scripts/pptx_template_import.py <deck.pptx> --manifest-only -o <workspace>
```

`manifest.json` 逐页报告 layout / master 路径、占位符（`type`、`idx`、`semanticRole`、`shapeName`）、图片资源、文字数量与页面类型；`native_structure.json` 另外给出源结构评估。`--manifest-only` 跳过 SVG 导出，只是查看时开销很小。

注意 Create Template 产出的是可复用的模板工作区，而不是填好内容的 deck：后续页面由 Generate 重新创作，因此源文件的正文与备注不会被搬运过去。如果你预期可用的某个图形没有出现在上述报告里，这才是值得写进 issue 的具体事实。

---

## Q: 能把企业 `.pptx` 提炼成可复用工作区吗？应该选哪一种 kind？

可以，但必须显式请求 `/create-template`。一份完整的来源 deck 本身不自动等于 `Deck`；应按真正要复用的合同选择：

| Kind | 要复用的合同 |
|---|---|
| **Brand** | 只复用身份：颜色、字体、Logo、语调和图标语言；没有页面 roster |
| **Style** | 复用沟通方法和视觉默认值，不携带身份真值、页面原型或原生结构 |
| **Layout** | 复用品牌中立、应用中立的 Master / Layout / slot 结构 |
| **Deck** | 复用反复出现的演示应用，或把企业身份与结构整合在一起；同时拥有身份、结构和 SVG roster |

Create Template 会先确认简报，再写入已注册、可发现的 `library` 工作区，或一个不注册的已初始化 `project` 工作区。后续 Generate 应传产出的工作区根目录，而不是来源 `.pptx` 或其内层 `templates/` 目录。详见 [Create Template 路线](../../skills/ppt-master/workflows/create-template.md)与[模板指南](./templates-guide.md)。

---

## Q: 模板注册后，以后每次生成都会自动使用吗？

不会。注册只让工作区可被发现，不会自动选中。Default Generate 每次仍需在 Stage 1 确认；只提供一个精确工作区 root 时可在页面中预选，但不会跳过确认，提供多个 root 时则都只作为未选候选。Quick 没有模板选择页，因此精确 root 会被直接校验并使用；没有精确 root 就走自由设计。原始 `.pptx`、内层 `templates/` 目录、裸模板名或风格词都不算选中工作区。详见[模板选择机制](./templates-guide.md)与[Quick 模板边界](../../skills/ppt-master/workflows/profiles/quick-generate.md)。

---

## Q: 如何制作自定义模板？

想把自己喜欢的 PPT 模板制作成 PPT Master 可调用的模板？按以下步骤操作：

**第一步 — 准备参考材料**

**最推荐的方式是直接给原始 `.pptx` 文件**。PPT Master 会提取包内实际存在且受支持的主题色、字体、Master/Layout、placeholder type/idx、原生形状信息和可复用图片资源。`standard` 与 `fidelity` 把完整来源清单作为证据，重新设计 SVG roster 和新的 Master/Layout/slot 系统，不保留、也不蒸馏来源拓扑。`mirror` 则为每张来源 Slide 输出一个原型，并只把这组 Slide 可达的 Layout/Master 事实物化到新工作区，不做语义归纳或缺口补造；未引用的来源 Layout/Master 只保留为分析证据，不进入 mirror 输出。由于结构层禁止 `<g>`，来源 Master/Layout 的 group wrapper 只允许机械展开成直接原子。

完整导入 SVG 可以保留高级 PowerPoint 形状所需的 metadata、隐藏 carrier 和预览指纹，并作为载荷后备留在临时分析工作区且保持不可变。模板创建使用带文档内 source ref 和紧凑路径/hash manifest 的轻量可编辑 IR。`standard` / `fidelity` 创作项目规范化 SVG，只有精确匹配已登记 preset 时才使用 compact authored-preset 组。Mirror 从 IR 物化最终模板，只为未改且 hash 匹配的 Slide-local/slot ref 重新接入转换器已经支持的载荷；不支持或已修改的对象保留当前 SVG fallback。

没有源 PPTX 时，也可以提供关键页面类型的截图——封面、目录、章节、内容和结尾——但此时几何、字体和继承关系只能根据画面推断。这里提取的是可复用模板系统；如果目标是把每个页面画面还原成分层可编辑输出页，应改用图片还原为 PPTX（`image-to-pptx`）。

**第二步 — 让 AI 创建模板**

使用支持 Agent 的 AI 工具（Claude Code、Codex 等），要求它使用 **PPT Master 的 `/create-template` 工作流**，将这些参考材料转换成模板。提供的信息越详细，效果越好，例如：

- 模板名称和适用场景（如政府汇报、高端咨询、产品宣讲等）
- 期望的风格基调和配色（如"现代克制、深蓝主色调"）
- 类别偏好（`brand` 品牌 / `general` 通用 / `scenario` 场景 / `government` 政务 / `special` 特殊）
- 画布格式（默认 16:9，如需其他格式请注明）
- 输出范围：进入索引的 `library`（默认）或一个已经初始化的 `project`；两者共享同一 spec schema 和素材路由，library 使用裸 spec，project 使用限定名 spec

不需要一次提供所有细节——AI 代理会通过对话追问补齐缺失信息（输出范围、模板 ID、主题模式等）。

**第三步 — 等待完成**

AI 代理会自动完成后续工作——分析参考、写入 kind 专属规范，仅为 Layout/Deck 构建结构定义，并验证工作区。Brand/Style 不生成预览 PPTX；Layout/Deck 可按请求生成 `exports/<id>_template_preview.pptx`，多 Master 时必须生成。两种范围都要求 `templates/`；Brand/Layout/Deck 可使用包自有 `images/` 和 `icons/`，Style 只贡献自己的 Design Spec。`library` 在 `skills/ppt-master/templates/<kind>/<id>/` 写入裸 `templates/design_spec.md` 并完成全局注册；`project` 在 `projects/<name>/` 写入 `templates/design_spec.<kind>.<id>.md` 并跳过注册，四种 kind 均可各自共存一份；Layout 与 Deck 同时存在时，Layout 拥有有效 SVG roster。空的可选目录直接省略。把这个工作区 root 交给 Step 3 时，项目 root 会原子贡献其中全部 spec，安装不会复制 `exports/`。旧平铺或语义旧包只能作为参考输入，必须通过 `create-template` 重建为当前工作区后才能被 Generate 选择。

> **提示**：对风格和使用场景描述得越具体，生成的模板就越符合你的预期。

---

> 更多问题可先查看 [skills/ppt-master/SKILL.md](../../skills/ppt-master/SKILL.md) 与 [AGENTS.md](../../AGENTS.md)
