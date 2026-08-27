# 路线图

[English](../roadmap.md) | [Chinese](./roadmap.md)

---

> PPT Master 是一个由个人维护的开源项目，按**优先级而非固定时间表**推进。这份路线图用来对齐预期：项目往哪个方向走、当下在做什么、哪些事等真实需求出现再做、哪些明确不做。优先级会随用户反馈和真实使用信号调整——不承诺交付时间窗口。

---

## 方向

项目的主轴是**原生深度**：逐版本创作或保留更多 PowerPoint 自身的对象模型、行为与可复用结构——持续向 PowerPoint 本身靠拢。完整论述见[项目定位章程](./project-positioning.md)；[PowerPoint ↔ SVG 映射指南](./powerpoint-svg-mapping.md)逐特性诚实记录当前边界。

这条主轴今天体现为三条显式产物路线：**Generate PPTX** 通过受约束的 SVG → DrawingML 创作全新设计的页面；**Create Template** 产出可复用的 Brand / Style / Layout / Deck 模板工作区；**Edit Native PPTX** 把既有 deck 导入保留来源的 round-trip 工作区，只编辑计划中的页面或叠加内容。

---

## 能力覆盖地图

一份演示文稿由四层构成：页面上有什么、如何组织、如何行动、文档自身如何结构化。下面的表把每一层与 PPT Master 今天的实现对应起来。

**这是地图，不是待办清单。**「有意边界」与「有意的不对称」是**已定形态**而非未完成的格子——那里的空白是决定，不是欠账。「暂不考虑」的行会在该行内写明为什么现在不做。只有「信号驱动」的行偏开放，其理由留在下面的[未来方向](#未来方向信号驱动)一节，不在此重复。真正被论证过的立场放在[明确不做](#明确不做)；这张地图只描述，不做裁决。

| 状态 | 含义 |
|---|---|
| **系统化** | 有专属创作契约；适用且客观可判定的部分配有校验把关，持续打磨中 |
| **已覆盖** | 今天可用，但没有专门的规范体系 |
| **有意边界** | 有意停在这里，理由已记录在案 |
| **有意的不对称** | 只支持单侧——通常是读取或保留来源 deck，而不创作 |
| **信号驱动** | 真实需求出现时值得做，不构成承诺 |
| **暂不考虑** | 当前不在考虑范围，理由写在该行内 |

### 第一层 — 可见对象

| 对象 | 状态 | 说明 |
|---|---|---|
| 文字 | 系统化 | 全 deck 字号角色锚点、逐处受限微调、层级与段落规则、原生可编辑文本 |
| 原生 WordArt 与文字变形 | 暂不考虑 | 艺术字首选 AI 生成的装饰文字图片，普通可编辑文字负责兜底。原生 WordArt、文字变形与路径文字会额外引入一套创作和兼容性表面，却不能改善这条主路径，因此不生成 |
| 矢量形状 | 系统化 | primitive / Office preset 原子 → 独立组合 → 仅在单一轮廓需要时使用 Boolean → 必要 freeform 构造阶梯，附原生转换规范 |
| 线条 / 连接符 | 有意的不对称 | 原生 `p:cxnSp` 导出已实现，端点绑定在来源 deck 的 preserve/mirror 往返路径上会被还原。新创作的连接符保持不连接。要绑定就得先判断哪些线是真实的边、哪些是装饰——这是意图判断，任何几何阈值都定不下来；而无论把这个判断放在导出期还是创作期，做判断的都是 AI，往上游挪并不会更可靠。结果只会是同一张图里有的箭头跟着节点走、有的不走 |
| 图标 | 系统化 | 内置 SVG 图标库 + 逐项目同步；项目图标属于已准备材料。插图式语义提示仍是 `images/` 下用于普通图片构图的生成切片，不进入图标库 |
| Logo | 有意边界 | Logo 永远来自既有素材，不在这里设计：brand 工作区把官方提供的文件安装为已准备资产——内置品牌预设附带官方标识及记录在案的使用规则——真实公司 / 产品标识另有 simple-icons 图标库覆盖 |
| 图片 | 系统化 | 获取、生成、处理、裁切、布局、组合、嵌入与来源标注 |
| 图表 | 系统化 | 有专属创作 reference；默认 SVG，原生 Chart 替换为显式 opt-in |
| 表格 | 系统化 | 有专属创作 reference；六种可复用的单元格网格参考，仍可自定义网格；原生 Table 替换走同一 opt-in |
| 关系图 | 系统化 | 六个关系原子——`order`、`link`、`parent`、`membership`、`contrast`、`overlap` |
| 公式 | 系统化 | 独立块级公式与同段行内公式可把 Microsoft 365 LaTeX / mhchem 文档中所有明确点名的输入编译为可编辑 OMML，并遵循文档规定的原生归一化，档位外输入直接失败。PPTX 导入可把通过校验的 PPT Master 自有 OMML 恢复为带可见 SVG 预览的规范公式 marker；任意第三方 OMML 与原始 LaTeX 写法恢复仍不在合同内。不生成图片兜底。包目标仍为 PowerPoint 2010+；可执行档位锁定到所述 Microsoft 文档版本，仓库验证覆盖编译器、OMML 与包结构，不等同于完整的 Microsoft 365 UI 认证。非 PowerPoint 客户端仍不在合同内 |
| 旁白与动画音效 | 系统化 | 逐页旁白音频，以及取自内置 CC0 音效库的原生转场与对象音效 |
| 任意视频与背景音乐 | 暂不考虑 | 属于一次性、内容特定的插入动作，在 PowerPoint 里手动放进去更快，AI 也无法替你挑文件。背景音乐还会牵出旁白混音决策，那在范围之外。来源 deck 中已有的媒体在 Fill 与 Enhance 路线中原样保留 |
| SmartArt | 有意的不对称 | 读取来源 diagram part 的内容与结构；生成 deck 用普通形状管线把这些内容重画出来。从不编辑 DiagramML，也不承诺原生 SmartArt 再生 |
| 3D 模型、OLE 对象 | 暂不考虑 | 两者都要求打开文件的机器装有宿主程序或较新版 Office，否则退化成一张静态预览图——正是本项目有意规避的跨渲染器问题。手动插入只要几秒。来源 deck 中已有的对象原样保留 |
| 墨迹与摄像头对象（Cameo） | 暂不考虑 | 手绘批注与实时摄像头对象属于演示现场的表面，不是生成的设计内容，且都依赖较新版 Office。来源 deck 中已有的此类 part 经源保留路线作为未改动的包结构透传 |

**插图**有意不列进这张表。它是可组合结果——一张图片、透明切片、一段 SVG，或一组形状——而不是第七种载体；它可以与页面上其他合适载体共同构图，把它与「图片」并列反而会重新引入这套分层正要消除的维度混淆。

### 第二层 — 构图系统

| 关注点 | 状态 | 说明 |
|---|---|---|
| 背景 | 系统化 | 纯色与渐变页面背景导出为 PowerPoint 原生底色；图片背景属信号驱动 |
| 层级与分组 | 系统化 | 显式 z-order 与分组契约，含 registered base / subject 图层对 |
| 插图构成 | 系统化 | 按页面规划为统一的元素家族；生图能力可用时，可在色键图纸中批量生成兼容素材、严格透明切片，再作为固定标题 / 四角装饰复用，或重组为主体锚点、辅助形象与点缀，并与文字、形状、照片、艺术字共同构图 |
| 网格、对齐、留白 | 系统化 | 共享构图合同，加由每种视觉风格各自承载的构图几何词汇 |
| 配色 | 系统化 | 声明的 HEX 是具名语义角色的真值来源；可复用角色锚点跨页保持稳定，仍可使用情境派生色与稀疏页内点缀 |
| 字体 | 系统化 | 每个结构角色一个跨页字号锚点，单次出现可在 `±2px` 内受限调整；稀疏非结构 Hero/Display 另有例外 |
| 视觉效果 | 系统化 | 有专属 effects reference；一个已登记的外阴影或发光可在受支持的基础对象与 compact authored-preset 形状上编译为一个可编辑原生效果 |
| 阅读路径 | 系统化 | 每页计划声明一个 primary 重点，锚定入口、推进、层级与终点；visual review 按该声明复核最突出元素与锚点位置 |

### 第三层 — 行为系统

| 关注点 | 状态 | 说明 |
|---|---|---|
| 页面转场 | 系统化 | 含来自内置 CC0 音效库的按需转场音；PPTX 回导会把当前注册表内的精确转场重建到规范 sidecar |
| 对象动画 | 系统化 | 默认关闭、opt-in；逐对象配置为显式声明，PPTX 回导会把当前注册表内具有精确时长的有限子集重建到规范 sidecar |
| 自动翻页 | 已覆盖 | 由旁白起始留白、音频时长与页尾补白推导 |
| 音视频播放 | 已覆盖 | 旁白音频与动画音效原生播放；来源 deck 中已有的媒体保留其播放设置 |
| 超链接 | 系统化 | 整体对象与行内文字通过标准 SVG `<a href>` 创作，导出为原生外链或 deck 内跳转关系，并在受支持的 PPTX 回导中重建 |
| 动作与导航 | 系统化 | 导航通过把目标包进超链接锚点显式创作，含 deck 内跳到指定页。`actionButton*` 预设只贡献视觉几何——光有外观绝不隐含动作。鼠标悬停触发、自定义放映、宏或程序执行、以及裸 `ppaction://` 注入都在契约之外 |
| Zoom（摘要 / 节 / 幻灯片缩放） | 暂不考虑 | 依赖 Office 版本的导航对象，在其他渲染器退化为一张静态图片——正是本项目有意规避的跨渲染器退化。deck 内跳转已由原生超链接的页面目标覆盖 |

### 第四层 — 文档结构

| 关注点 | 状态 | 说明 |
|---|---|---|
| 画布尺寸 | 系统化 | 画布契约选定演示文稿格式；SVG `viewBox` 是页面几何的唯一真值，配 fail-closed 校验，且同一 deck 的所有页面必须使用同一格式 |
| Theme | 系统化 | 有锁的 Default 导出根据配色与字体合同逐 deck 派生 `clrScheme`、major/minor 字体与 Master 标题／正文默认字号。Flat Quick 保留转换器默认 Theme 脚手架；structured Quick 在工作区提供时保留逐 Master 源 Theme，并从语义 slot carrier 推导 Master 标题／正文字号默认值；SVG 派生的页面颜色与字体仍按直接值写入 |
| 字体嵌入 | 有意边界 | 从不在包内嵌入字体；品牌 / 网络字体只有确认目标系统可用后才领衔，否则导出安全字体族，并把原意向字体记录在 Design Spec 中 |
| 幻灯片节 | 有意的不对称 | Edit Native PPTX 在 identity roster 不改 presentation 结构时保留既有节元数据；使用 `page_plan.json` 重建页面清单时会丢弃节。生成或重建页面列表的路线不创作 PowerPoint 原生节，因为页面角色与可选的 Design Spec Part 并不构成所有路线都具备的必需章节合同。节只改变缩略图栏的组织方式，从不改变任何页面外观；长 deck 需要分组时，在 PowerPoint 里手动分节约一分钟，且只做一次 |
| Master / Layout | 系统化 | 结构化路线输出真实的 `p:sldMaster` / `p:sldLayout` part |
| Placeholder | 系统化 | 模板工作区契约，strict/adaptive 导出行为逐 deck 推导 |
| 日期、页脚与页码字段 | 有意边界 | 结构化模板路线按 placeholder 契约创作真实的日期 / 页脚 / 页码 placeholder。自由设计路线有意让画出的页码与页脚保持普通文本：页码数字经常本身就是设计元素而非标准字段，区分两者是意图判断；真需要标准页码域时在 PowerPoint 里手动插入只要几秒，且只做一次 |
| 备注 | 系统化 | 导出时带真实的 notes master |
| 旁白 | 系统化 | 逐页音频，带 provider 来源标注 |
| 字幕 | 系统化 | 受支持 provider 的逐词时间轴重组为统一的紧凑 SRT |
| 文档元数据 | 已覆盖 | 在导出时设定，而非交给打包库默认生成 |
| 无障碍信息（Alt Text、阅读顺序） | 暂不考虑 | AI 生成的图片带 `alt_text` 字段，网络抓取的图片会记录页面上常为空的 `alt` 属性，但形状、图表、关系图与用户自带图片完全没有描述——完整覆盖意味着为每个非文字对象新增创作描述，而不是接通既有数据。阅读顺序在 PowerPoint 里不是独立属性：它就是形状顺序，承载页面的视觉层叠，无法脱离它单独设置 |
| 宏与 Office 扩展 XML | 有意的不对称 | 从不创作——生成路线不合成 VBA；既有宏或扩展 part 只在支持宏的源保留工作流保持所属包 part 未改动时得以保留 |
| 评论、修订、协作状态 | 暂不考虑 | 属于 Office 协作面，在创作型产品之外 |

---

## 进行中 / 下一步

明确在做或下一步要做，不承诺时间窗口。

- **在真实 deck 上校准新落地的体系** — 多 deck 合并 intake、材料发散度、可组合插画体系、结构化模板创作均已上线；它们现在需要的是真实使用信号，而不是更多机制。不预先加机械阈值或配额。
- **Prompt 精简** — 在不降质量的前提下压缩各角色 prompt 的 token 占用、提升缓存命中率，带来间接的成本 / 速度改善。与「纯速度优化」的边界见下方「明确不做」。

---

## 未来方向（信号驱动）

已评估为「真实需求出现时值得做」的候选项，列出来是为了公开意图，均不构成承诺。

- **持续收窄[映射指南](./powerpoint-svg-mapping.md)记录的原生覆盖缺口** — 逐版本把更多「仅 SVG」的格子推向 PowerPoint 原生结构与行为。
- **图片页面背景提升为原生背景填充** — 纯色 / 渐变页面背景已导出为 PowerPoint 原生底色；图片背景按需求驱动。

---

## 已交付里程碑

一个月一行，细节见 [Release 发布说明](https://github.com/hugohe3/ppt-master/releases)与 commit log。

| 时间 | 主题 |
|---|---|
| 2026-03 | **原生 PPTX 路线成形** — SVG → DrawingML 链路可用；图表 / 版式模板索引上线 |
| 2026-04 | **管线规模化** — 仅凭主题生成、70 个图表模板 + 三套图标库、`spec_lock` 跨页一致性契约、逐元素动画与旁白 / 视频导出 |
| 2026-05 | **可视化编辑 + AI 图片体系化** — Live Preview 确定性原位编辑（基于 [@WodenJay](https://github.com/WodenJay) 的 [PR #85](https://github.com/hugohe3/ppt-master/pull/85)）、从 PPTX 创建模板工作区、rendering × palette × type 图片体系、旧版栅格 LaTeX 渲染器 |
| 2026-06 | **mode 与 visual-style 双 catalog + intake 扩展** — 5 种叙事 mode × 18 种视觉风格（+ `custom`）、内容忠实的美化 profile、多 deck 合并 intake、可组合插画切片管线、网络图片质量闸门、源转换保真提升（图注识别基于 [@suay1113](https://github.com/suay1113) 的 [PR #191](https://github.com/hugohe3/ppt-master/pull/191)，超链接保留提炼自 [@ZhaoZuohong](https://github.com/hugohe3/ppt-master/pull/155)） |
| 2026-07 | **定位章程 + 原生母版 / 版式 + token 效率**（[v4.0.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)）— 三段式分步确认 UI、真 `p:sldMaster` / `p:sldLayout` 导出、`--native-charts-and-tables` opt-in、动效导出加固、图表模板库压缩 |
| 2026-08 | **模板库 + 页面图重建 + 原生公式与链接 + AI 图像成为构图系统**（[v4.5.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.5.0)、[v4.6.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.6.0)、[v4.7.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.7.0)、[v4.8.0](https://github.com/hugohe3/ppt-master/releases/tag/v4.8.0)）— brand / style / layout 工作区库、可视化按信息模型拆分且结构改为组合语法、Codex 支持的 `image-to-pptx` profile、带原生动画音效的视频交付、三条可编辑整体设计方向、覆盖 Microsoft 365 文档化 profile 的可编辑 OMML 公式、原生超链接创作、可跨页复用的 AI 插画元素族与装饰艺术字、按任务决定来源并隔离审阅缩略图的配图路径、转场与对象动画的反向导入，以及四层能力覆盖地图 |

---

## 明确不做

下面这些方向被多次提过，已经评估并决定**不做**。列出来不是否定需求价值，而是说明它们与本项目产品方向不匹配；如果你刚好需要这些能力，建议看其他工具或 fork 本项目走自己的路。

### 对任意 PPTX placeholder 系统做无契约盲填

**对应 Issue**：[#53](https://github.com/hugohe3/ppt-master/issues/53)、[#118](https://github.com/hugohe3/ppt-master/issues/118)

Generate PPTX 路线围绕完全可控的新形状、文字与版式创作。结构完整的 PPTX 可以通过两种显式方式为经过确认的可复用模板包提供依据：`standard` / `fidelity` 读取完整来源证据，创作新的完整 Slide SVG 原型和 Master/Layout 系统；`mirror` 只物化来源 Slide 及其可达的 Layout/Master 链。两者都不修改来源 PPTX，也不补造缺失的设计意图。但「打开任意 PPTX 后不经规范化就盲填所有占位框」仍是另一种产品形态。

**基础诉求其实很简单**：如果只是「固定位置替换 Excel 数据到 PPT 模板」，直接让 AI 写一段 `python-pptx` 脚本即可，几行代码搞定，不需要本项目这套管线。

> **已支持边界**：Edit Native PPTX（`edit-native-pptx`）把既有 deck 导入 round-trip 工作区，逐字节引用未改页面，只编辑计划中的页面或叠加内容；Create Template（`create-template`）根据自然语言请求和来源证据，在内部推导重新创作或 mirror 物化实现；Strategist 再根据真实模板和当前内容推导 strict/adaptive 导出行为。仍不做未经审查、没有契约的任意第三方 placeholder 全自动替换。

### 把原生 PowerPoint 图表设为默认路线

**对应 Issue**：[#99](https://github.com/hugohe3/ppt-master/issues/99)、[#100](https://github.com/hugohe3/ppt-master/issues/100) 类

跨四渲染器（PowerPoint / Keynote / LibreOffice / WPS）的位置保真是项目主轴。把默认路线改成 PowerPoint 原生图表会让「像素级一致性」破功——同一个 PPTX 在不同渲染器里图表会显示不同布局。图表默认用 SVG 是 **by design**，不是能力缺失。

窄例外是 `data-pptx-replace-with` marker：Design Spec §IX `Native-ready` 映射中以 `<object-key>=yes` 点名的受支持独立数据图表与纯文本网格表格可以携带 PowerPoint 原生 Chart/Table 替换 payload；`no` 与零星微型图形保持普通 shape。§VII 只记录真正选中的可复用参考。导出加 `--native-charts-and-tables` 才激活已准备的 marker——供主动用跨渲染器保真换取带数据源对象及图表/表格专属编辑模型的用户使用；激活后的对象会保留 deck 的 chart-area / plot / 轴线 / 网格线 / 标签颜色与原生表格格式，不再塌回 PowerPoint 默认主题（见 [v4.0.0 发布说明](https://github.com/hugohe3/ppt-master/releases/tag/v4.0.0)）。默认导出路径与可编辑的 SVG 派生形状系统不变。

### uv 作为默认 / 必需依赖

**对应 Issue**：[#111](https://github.com/hugohe3/ppt-master/issues/111)

`pip + requirements.txt` 是唯一官方安装路径，因为它在所有 Python 环境下都可用、不需要额外学习成本。uv 是好工具，但「让 uv 成为默认」会抬高新用户的入门门槛。如果你个人偏好 uv，完全可以在 fork 里用，不影响主线。

### 纯速度优化

**对应 Issue**：[#97](https://github.com/hugohe3/ppt-master/issues/97)

成本 / 速度 / 质量三角下，本项目选择**质量优先**。20 分钟生成一个高质量 PPTX 是当前的合理点。

会做：通过 prompt 精简 / 缓存命中率提升带来的间接改善。

显式 `quick-generate` 是用户主动选择的工作流短路：它跳过 Strategist、确认和首屏 gate，随后创作 SVG、运行一次无锁最终质量门，再导出最终 PPTX。由于整个规划阶段不再发生——Strategist 系 reference 的加载、`design_spec.md` / `spec_lock.md` 的写入、分步确认往返——这部分 token 开销随之消失，而逐页 SVG 创作的开销不变。它保留同一套页面级视觉与资源创作能力，以及共享的 SVG / 资源阻塞标准；它不运行 Spec Lock 对齐检查，也不从 lock 派生当前项目 Theme。Flat Quick 保留转换器默认 Theme 脚手架；structured Quick 在工作区提供时保留逐 Master 源 Theme，并从语义 slot carrier 推导 Master 标题／正文字号默认值。由于没有已确认的设计契约、首屏校准或可恢复的决策历史，它不承诺与 Default 作出相同设计，也不承诺具体耗时。

默认 Generate 流程仍坚持质量优先。

### 独立 CLI / 托管 SaaS / 桌面 App 形态

产品形态明确为**运行在支持 Agent 的 AI 工具中的对话式工作流 / skill**（Claude Code、Codex、Cursor、VS Code agents 等）。

不会做：独立 CLI（`ppm` 之类）、SaaS Web 服务、Electron 桌面壳。所有「让它脱离 chat 独立运行」的提案都会被拒。chat 是交互核心，不是包装层。

---

## 反馈渠道

- **Issues**：[github.com/hugohe3/ppt-master/issues](https://github.com/hugohe3/ppt-master/issues) — 报告 Bug / 提建议
- **Discussions**：[github.com/hugohe3/ppt-master/discussions](https://github.com/hugohe3/ppt-master/discussions) — 用法讨论 / 经验分享
- **邮箱**：heyug3@gmail.com

提需求前先扫一眼上面的**明确不做**；如果你的需求落在那一节，多半不会被采纳，但欢迎讨论是否还有别的路径解决你的真实问题。
