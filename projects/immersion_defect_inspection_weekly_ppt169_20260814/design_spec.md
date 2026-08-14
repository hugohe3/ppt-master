<!-- ppt-master-schema: design-spec/v1 -->
# 浸没式光刻缺陷检测周报 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 浸没式光刻缺陷检测周报 |
| Canvas Format | PPT 16:9（1280 × 720） |
| Page Count | 8 |
| Primary Language | zh-CN |
| Target Audience | 光刻、缺陷、良率和设备工程师，以及当值经理；关注本周检测是否可信、killer 类型是什么、该动哪台扫描机 |
| Communication Intent | 先报告本周 D0 上升是水印而非漏检，再给出空间签名、类型 Pareto 和工具拆分证据，最后冻结 recipe 并推动 S02 关闭残液路径 |
| Desired Audience Outcome | 与会者停止按颗数最高柱处理颗粒，改为按杀伤比处理 S02 水印，并同意本周不收检测阈值 |
| Core Message / Ask / Action | W33 L28 D0 升至 0.42/cm²；捕获率稳定，水印才是 killer；4 个 killer lot 全部来自 S02；先做浸没头/台面与后淋洗，禁止用 recipe 制造回收 |
| Delivery Context | 12 分钟主讲的缺陷工程周会；次要用于会后独立阅读和周跟踪 |
| Artifact Afterlife | 作为当周检测基线、SEM 分类口径和动作闭环记录 |
| Reading Mode | balanced |
| Content Strategy | 可在不改变演示用虚构数据口径的前提下重组和可视化；机制名称保持文献词汇 |
| Design Style | 深色工程蓝图：技术图纸式网格、单线结构、尺寸标记与少量状态色 |
| Formula Policy | text-only |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-08-14 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 40 px |
| Content Area | x=40–1240，y=40–680；页标题下方保留统一技术标尺带 |

## III. Visual Theme

### Theme Style

- **Mode**: pyramid
- **Visual style**: blueprint
- **Theme**: 以暗色工程图纸为底，细网格和技术标注组织全篇；完成/可用青绿，风险琥珀，阻塞红。
- **Tone**: 专业、克制、可审计；像缺陷工程图纸而非营销页。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #071827 | 主画布图纸底 |
| Secondary background | #0D2538 | 分区与标题栏 |
| Primary | #87D9F5 | 结构线与普通信息 |
| Accent | #32E0C4 | 完成、基线内、正向 |
| Secondary accent | #FFB454 | 风险、超限、待动作 |
| Body text | #EAF7FF | 主体文本与关键数字 |
| Grid | #16384C | 背景网格 |
| Muted text | #8BA9B8 | 注释与来源 |
| Blocking | #FF6B6B | 明确阻塞与 killer lot |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | clean engineering sans / bold | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Body | clean engineering sans / regular | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Data | technical monospace | Consolas | Consolas | Microsoft YaHei, monospace |

- **Title stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Body stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Data stack**: `Consolas, "Microsoft YaHei", "微软雅黑", monospace`
- **Role rationale**: Data is recurring across D0, lot IDs, tool codes and dates.

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 42 |
| Subtitle | 32 |
| Lead | 30 |
| Data | 20 |
| Annotation | 18 |
| Footnote | 16 |

## V. Layout Principles

### Page Structure

- **Header area**: 左上结论式标题；右上项目代号、数据日和页码坐标。
- **Content area**: 晶圆签名、漏斗、Pareto 或信号带做骨架；文字用引线挂上，不用卡片墙。
- **Footer area**: 含数字页标注“演示用虚构数据｜不代表真实工厂成绩”。

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | 40 px |
| Content block gap | 24–32 px |
| Icon-text gap | 12–16 px |

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/droplet | 水印 / 残液 |
| tabler-outline/zoom-scan | 光学检测与 SEM 复核 |
| tabler-outline/chart-column | Pareto 与对比 |
| tabler-outline/chart-funnel | 检测漏斗 |
| tabler-outline/alert-triangle | 超限与 killer |
| tabler-outline/checklist | 下周动作 |
| tabler-outline/chart-dots-3 | 捕获率 / nuisance / SNV |
| tabler-outline/layers-intersect | 当层 adder 与前层 |
| tabler-outline/wave-sine | 扫描路径签名 |
| tabler-outline/circle-dot | 空间热点 |

## VII. Visualization Reference List

| Page | Template | Usage |
| --- | --- | --- |
| P04 | pareto_chart | SEM 分类占比与累计贡献 |
| P05 | funnel_chart | 送检→超限→SEM→killer lot 收敛 |
| P06 | grouped_bar_chart | S01/S02/S03 的 D0 与 PWP |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline

### Part 1: 本周判断

#### Slide 01 - 封面

- **Audience move**: 从“还不知道本周检测结论”到“先记住 L28 D0 升至 0.42，问题在 S02 水印”。
- **Layout**: 左侧尺寸线框住 0.42/cm²；右侧扫描路径线框穿过晶圆示意图，起停点琥珀色。
- **Title**: 浸没式光刻缺陷检测周报
- **Core message**: 捕获率稳定，D0 上升是当层水印，不是漏检。
- **Content**: 副标题“2026-W33｜L28 ADI｜36 lot”；英雄数字 0.42 /cm²；对比“8 周基线 0.18”；状态“S02 4 个 killer lot”；数据日 2026-08-13。
- **Cover impact**: 绑定钩子为“0.42 对 0.18，问题在扫描起停点”。
- **Data class: scenario**: 周次、D0、lot 数和工具均为演示用虚构数据。

#### Slide 02 - 捕获率稳定，水印才是本周 killer

- **Audience move**: 形成对 D0、可信度、类型和工具的一页判断。
- **Layout**: 左主仪表 D0；右四信号带：进展/可信度/类型/工具。
- **Title**: 捕获率稳定，水印才是本周 killer
- **Core message**: 不要按颗数最高柱打颗粒；S02 水印按杀伤比排第一。
- **Content**: D0 0.42 vs 0.18；Capture 91% vs 93%；Nuisance 18%；SEM 颗数颗粒 31% 但水印 kill ratio 0.62 居首；4/4 killer lot 在 S02。
- **Data class: scenario**: 全部 KPI 为演示用虚构数据。
- **Fact IDs**: F005, F008

### Part 2: 证据

#### Slide 03 - 空间签名沿扫描起停点，符合残液而不是来料

- **Audience move**: 从“D0 高了”到“看懂是扫描路径水印”。
- **Layout**: 中央晶圆线框 + 扫描条带；边缘环带标注 41%；右侧鉴别口诀。
- **Title**: 空间签名沿扫描起停点，符合残液而不是来料
- **Core message**: 起停点密度为片心 3.4 倍；气泡会改 pitch，本周 79% 圆形缺陷 pitch 不变。
- **Content**: S02 边缘 5 mm 占 41%；S01/S03 近随机；鉴别：水印 pitch 不变 + T-top，气泡有条纹。
- **Native shape suggestion**: 圆形晶圆、同心环、直角扫描条带与引线。
- **Data class: scenario**: 倍率与占比为演示用虚构数据。
- **Fact IDs**: F001, F005, F008

#### Slide 04 - 按杀伤比加权后，水印优先于颗粒柱

- **Audience move**: 纠正“颗粒最多所以先打颗粒”。
- **Layout**: 左 Pareto 柱+累计线；右 kill ratio 对照轨。
- **Title**: 按杀伤比加权后，水印优先于颗粒柱
- **Core message**: 颗粒 31% 但 kill ratio 仅 0.18；水印 28% × 0.62 才是第一优先。
- **Content**: watermark 28%/0.62；particle 31%/0.18；microbridge 14%/0.41；bubble 7%/0.35；SNV 12% 不进杀伤排序。
- **Visualization**: 数据驱动 Pareto；参考 P04 `pareto_chart`。
- **Native-ready**: no
- **Data class: scenario**: 占比与杀伤比为演示用虚构数据。
- **Fact IDs**: F005, F008

#### Slide 05 - 检测漏斗收敛到 4 个 S02 killer lot

- **Audience move**: 看清从 36 lot 到 4 个必须动作的 lot。
- **Layout**: 横向工程漏斗，底部四枚 S02 lot 轨道。
- **Title**: 检测漏斗收敛到 4 个 S02 killer lot
- **Core message**: 36→11→7→4；killer 全部落在同一浸没头周期。
- **Content**: 送检 36、光学超限 11、SEM 7、killer 4；动作是关 S02 残液，不是全线停。
- **Visualization**: 参考 P05 `funnel_chart`。
- **Native-ready**: no
- **Data class: scenario**: 漏斗数量为演示用虚构数据。

#### Slide 06 - 只有 S02 的 D0 与 PWP 同时漂移

- **Audience move**: 把动作从“浸没整体”收到 S02。
- **Layout**: 三台扫描机分组柱：D0 与 PWP。
- **Title**: 只有 S02 的 D0 与 PWP 同时漂移
- **Core message**: S01/S03 在基线内；S02 D0 0.71、PWP 27，是当层 adder。
- **Content**: 表中三台数据；Adder vs 前层 +0.24。
- **Visualization**: 参考 P06 `grouped_bar_chart`。
- **Native-ready**: no
- **Data class: scenario**: 工具数据为演示用虚构数据。
- **Fact IDs**: F002

#### Slide 07 - 总数上升被 nuisance 放大，不要先收阈值

- **Audience move**: 分清工艺恶化和 recipe 偏热。
- **Layout**: 三轨对比 Capture / Nuisance / SNV，红线标“禁止收阈值”。
- **Title**: 总数上升被 nuisance 放大，不要先收阈值
- **Core message**: Capture 仍 91%；Nuisance 18%、SNV 22% 说明偏热和复核方法，不是先降灵敏度。
- **Content**: 三指标相对基线；False 0.8%；下周冻结 recipe。
- **Data class: scenario**: 比例为演示用虚构数据。
- **Fact IDs**: F019, F024, F027, F042

### Part 3: 动作

#### Slide 08 - 本周先关 S02 残液，recipe 冻结

- **Audience move**: 带着可执行清单离开。
- **Layout**: 五项动作签批板，编号 D01–D05。
- **Title**: 本周先关 S02 残液，recipe 冻结
- **Core message**: PM + 后淋洗延迟核查 + 颗粒降为观察项 + 阈值冻结 + 加密 SEM。
- **Content**: 五条动作及成功判据；不决策则 W34 无法区分工艺与检测。
- **Data class: scenario**: 动作窗口为演示用虚构设定。

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 每页先说结论，再补证据；所有数字口头标明“演示数据”
- **Total duration**: 12 minutes
- **Notes style**: formal
- **Presentation purpose**: report
