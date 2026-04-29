# 常见问题

[English](../faq.md) | [中文](./faq.md)

---

## Q: PPT Master 支持哪些源文件格式？

几乎所有常见格式都支持：**PDF**、**DOCX**、**PPTX**、**EPUB**、**HTML**、**LaTeX**、**RST**、**网页链接**（包括微信公众号文章）、**Markdown**，或者直接在对话中粘贴文字内容。AI 代理会自动将源材料转换为 Markdown 后再生成幻灯片。

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

## Q: 能用 AI 生成配图吗？

可以。PPT Master 内置了图片生成脚本，支持多个供应商（Gemini、OpenAI、FLUX、通义千问、智谱等）。在策略师阶段选择"AI 生图"方案后，流程会根据内容自动生成配图。你也可以使用自己的图片——只需放到项目的 `images/` 目录下即可。

## Q: 生成的 PPT 可以编辑吗？

可以。主 `.pptx`（原生 PowerPoint 形状，文字、图形、颜色均可直接编辑，无需转换）以时间戳命名保存至 `exports/`。SVG 快照版 `_svg.pptx` 与 Executor 原始 SVG 源（`svg_output/` 副本）一同归档至 `backup/<timestamp>/`，便于回溯视觉参考或基于该版重跑 `finalize_svg → svg_to_pptx` 重建 pptx，无需再走 LLM。`backup/<timestamp>/` 目录可手动清理。需要 **Office 2016** 或更高版本。

## Q: 三种执行师有什么区别？

- **Executor_General**: 通用场景，灵活布局
- **Executor_Consultant**: 一般咨询，数据可视化
- **Executor_Consultant_Top**: 顶级咨询（MBB 级），5 大核心技巧

## Q: 用 PPT Master 做 PPT 贵吗？

PPT Master 本身免费开源，唯一的成本来自你自己的 AI 模型用量。

目前主流 AI 工具都已转向按量计费——用多少付多少。PPT Master 天然契合这一模型：不需要额外订阅 PPT 平台、没有专有积分、没有按人头收费的演示工具费用。

作为对比，Gamma 订阅 $8–20/月，Beautiful.ai $12–45/月——无论用多少都得付这个底价。PPT Master 在你现有 AI 支出之外不增加任何额外成本。

## Q: 生成的图表可以编辑数据吗？

图表以**自定义设计的 SVG 图形**形式渲染，转换为原生 PowerPoint 形状——形状级别完全可编辑（移动、改色、改文字、调样式）。这是一个有意为之的选择，而不是 Excel 驱动的图表对象：PowerPoint 默认图表样式陈旧、视觉受限于固定模板。SVG 图表则提供出版物级的视觉质量，并且可以在 PowerPoint 中直接精修。

如果你的工作流明确需要 Excel 驱动的数据编辑，可以在导出后自己手动在 PowerPoint 里制作一张类似的原生图表。

## Q: 页面切换和元素动画可以调吗？

可以。页间转场（默认 `fade` 0.4s）和页内元素入场动画（默认关闭）都通过 `svg_to_pptx.py` 的参数控制——`-t/--transition` 控制页级，`-a/--animation` 控制元素级。常用一行命令：

```bash
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push       # 换转场效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none       # 关闭转场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade   # 开启页内动画
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed  # 自动混搭效果
```

完整效果列表、`<g id="...">` 锚点机制、降级行为、限制：见 [转场与动画](./animations.md)。

## Q: 推荐用什么 AI 模型？

**Claude**（Opus / Sonnet）是推荐且测试最充分的模型。SVG 排版本质上是在绝对坐标系中做精确的数学计算（字号 x 字数 x 容器宽度），Claude 在这方面表现明显优于其他模型。

**GPT 系列**早期版本排版问题较多——文字超出容器、元素错位、坐标计算失误。较新的版本（如 GPT-5.5）在这方面已有明显进步，实际效果可以接受；如果遇到问题，可以告知 AI 修正具体页面。

其他模型（Gemini、GLM、MiniMax 等）效果参差不齐。总体来说，前端/视觉能力越强的模型，生成效果越好。

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

## Q: 能在导出前预览或修正某一页吗？

可以。你可以**随时中断工作流**——前几页生成后就可以查看并反馈意见。AI 可以根据你的意见重新生成特定页面，不需要等到全部完成再修改。

生成后的修正也一样简单，直接告诉 AI："第 3 页布局有问题——标题和图表重叠了"，它会修正那个特定的 SVG。

## Q: 如何制作自定义模板？

想把自己喜欢的 PPT 模板制作成 PPT Master 可调用的模板？按以下步骤操作：

**第一步 — 准备参考材料**

最简单的方式是将参考 PPT 的关键页面类型分别截图保存：欢迎页、目录页、章节页、内容页、结尾页。将截图放到同一个文件夹中，并使用规范的文件名（如 `cover.png`、`toc.png`、`chapter.png`、`content.png`、`closing.png`）。

如果你已经有原始 `.pptx` 模板文件，也可以把它作为参考源一并提供。PPT Master 会先从 PPTX 中提取可复用的背景图、logo、主题色和字体信息，再把这些素材用于模板重建。

**第二步 — 让 AI 创建模板**

使用 AI 编程代理（Claude Code、Codex 等），要求它使用 **PPT Master 的 `/create-template` 工作流**，将这些参考材料转换成模板。提供的信息越详细，效果越好，例如：

- 模板名称和适用场景（如政府汇报、高端咨询、产品宣讲等）
- 期望的风格基调和配色（如"现代克制、深蓝主色调"）
- 类别偏好（`brand` 品牌 / `general` 通用 / `scenario` 场景 / `government` 政务 / `special` 特殊）
- 画布格式（默认 16:9，如需其他格式请注明）

不需要一次提供所有细节——AI 代理会通过对话追问补齐缺失信息（模板 ID、主题模式等）。

**第三步 — 等待完成**

AI 代理会自动完成后续工作 — 分析截图、构建布局定义、注册模板，使其出现在 PPT Master 工作流的模板选项中。

> **提示**：对风格和使用场景描述得越具体，生成的模板就越符合你的预期。

---

> 更多问题可先查看 [skills/ppt-master/SKILL.md](../../skills/ppt-master/SKILL.md) 与 [AGENTS.md](../../AGENTS.md)
