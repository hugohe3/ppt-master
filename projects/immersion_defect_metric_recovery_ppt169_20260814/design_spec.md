<!-- ppt-master-schema: design-spec/v1 -->
# 浸没式光刻缺陷指标回收 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 浸没式光刻缺陷指标回收 |
| Canvas Format | PPT 16:9（1280 × 720） |
| Page Count | 8 |
| Primary Language | zh-CN |
| Target Audience | 良率与工艺专项决策会；约 15 分钟内需判断回收是否真实、剩余挂在哪条路径 |
| Communication Intent | 说明 D0 从 0.51 收到 0.29、剩余 0.09 挂在后淋洗与 hood，禁止把 recipe 收热算作回收，推动 W35 释放标准 |
| Desired Audience Outcome | 与会者把真实工艺/设备回收与检测阈值回退分开，并同意按 D0、PWP、捕获率三条标准签批 W35 释放 |
| Core Message / Ask / Action | 真实工艺/设备回收约 0.16；W32 recipe 回退使表观 D0 回升；剩余靠 hood 气帘与 EBR，不得把 recipe 收热计作回收 |
| Delivery Context | 15 分钟主讲的良率/工艺专项决策会；次要用于会后独立阅读和 W35 跟踪 |
| Artifact Afterlife | 作为回收口径、杠杆拆分和 W35 释放标准的会后记录 |
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
| Blocking | #FF6B6B | 明确阻塞与不可计入项 |

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
- **Content area**: 瀑布、趋势、拆分轨或签批板做骨架；文字用引线挂上，不用卡片墙。
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
| tabler-outline/target | 目标 D0 与释放门槛 |
| tabler-outline/adjustments | 工艺/设备杠杆调节 |
| tabler-outline/droplet | 水印与后淋洗 |
| tabler-outline/chart-column | 瀑布与杠杆对比 |
| tabler-outline/activity | D0 周趋势 |
| tabler-outline/filter | 检测阈值 / recipe |
| tabler-outline/checklist | 释放标准签批 |
| tabler-outline/alert-triangle | 残差与不可计入项 |
| tabler-outline/timeline | 回收窗口 W31–W35 |
| tabler-outline/chart-dots-3 | 捕获率 / nuisance / SNV |

## VII. Visualization Reference List

| Page | Template | Usage |
| --- | --- | --- |
| P03 | waterfall_chart | 各回收动作对 D0 的累计贡献与残差 |
| P06 | line_chart | W26–W33 D0 趋势对照目标与控制上限 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline

### Part 1: 回收判断

#### Slide 01 - 封面

- **Audience move**: 从“只记得 D0 在降”到“先记住 0.51→0.29，目标 0.20，剩余 0.09 仍开放”。
- **Layout**: 左侧尺寸线框住英雄跨度 0.51→0.29；右侧目标刻度 0.20 与残差 0.09 用琥珀引线标出，不用卡片墙。
- **Title**: 浸没式光刻缺陷指标回收
- **Core message**: 真实工艺/设备回收约 0.16；剩余 0.09 挂在后淋洗与 hood，不是 recipe 功劳。
- **Content**: 副标题“2026-W31 至 W33｜L28 浸没水印｜目标关闭 W35”；英雄数字 0.51→0.29 /cm²；目标 0.20；剩余 0.09；红线“禁止把 recipe 收热算作回收”。
- **Cover impact**: 绑定钩子为“0.51 收到 0.29，还差 0.09，且那 0.09 不是检测阈值”。
- **Data class: scenario**: 峰值、当前值、目标和残差均为演示用虚构数据。

#### Slide 02 - 主指标在回收，捕获率已从阈值假象中拉回

- **Audience move**: 形成对 D0、捕获、nuisance、SNV、PWP 的一页口径。
- **Layout**: 左主仪表 D0 0.51→0.29；右指标树沿竖向标尺展开 D0/capture/nuisance/SNV/PWP/kill/adder，完成项青绿、监控项浅线。
- **Title**: 主指标在回收，捕获率已从阈值假象中拉回
- **Core message**: D0 计入回收；捕获率从 W32 的 84% 回到 91%，阈值收热不得换主指标。
- **Content**: D0 0.51→0.29，目标 0.20；Capture 92%→91%，目标 ≥90%；Nuisance 21%→18%，目标 ≤12%；SNV 28%→22%，目标 ≤15%；S02 PWP 41→27，目标 ≤12；水印 kill ratio 0.66→0.62；Adder +0.38→+0.24。
- **Data class: scenario**: 全部 KPI 为演示用虚构数据。
- **Fact IDs**: F008, F019, F023, F024, F027, F042

### Part 2: 杠杆与证据

#### Slide 03 - 已关闭动作解释 0.16，剩余 0.09 仍是水印路径

- **Audience move**: 把 0.22 的表观下降拆成可审计动作，而不是一把记成回收。
- **Layout**: 横向工程瀑布，从峰值 0.51 起跳；已关闭段青绿，预测段琥珀虚线，残差 0.09 用阻塞红收尾。
- **Title**: 已关闭动作解释 0.16，剩余 0.09 仍是水印路径
- **Core message**: 台面清洁、后淋洗与 topcoat 换桶合计 −0.16；recipe 回退 +0.04 不能记入回收。
- **Content**: 回退 recipe +0.04；台面清洁 −0.07；后淋洗 −0.06；topcoat 换桶 −0.03；hood 预测 −0.05；EBR 预测 −0.02；未解释残差 0.09。净可见 0.51→0.29；真实工艺/设备回收约 0.16。
- **Visualization**: 数据驱动瀑布；参考 P03 `waterfall_chart`。
- **Native-ready**: no
- **Data class: scenario**: 各段 ΔD0 与残差为演示用虚构数据。
- **Fact IDs**: F008, F027, F033, F034, F038, F042

#### Slide 04 - 检测阈值回退，不算工艺回收

- **Audience move**: 把三类杠杆分开，堵住“检测变冷等于工艺变好”。
- **Layout**: 三列工程拆分轨——工艺 / 设备 / 检测；每轨上已关闭与未关闭用实线、虚线区分，检测轨底部画红线“禁止计入”。
- **Title**: 检测阈值回退，不算工艺回收
- **Core message**: 工艺已关换桶与部分后淋洗；设备已关台面清洁；检测只允许回退并冻结，不能制造 D0 下降。
- **Content**: 工艺：换桶已完成、后淋洗部分 lot、EBR 未关，红线是不改 PEB；设备：台面清洁已完成、气帘与 UPW 未关，红线是不降扫描速度；检测：W32 收阈值已回退，冻结至 W35。
- **Data class: scenario**: 关闭状态与窗口为演示用虚构设定。
- **Fact IDs**: F027, F033, F034, F038, F042

#### Slide 05 - 后淋洗有效但未完成，必须叠加 hood

- **Audience move**: 从“淋洗已经有效”转到“单靠淋洗收不完，必须叠加 hood”。
- **Layout**: 左右 split 对照：A/B 两条晶圆扫描条带并置；起停点倍率从 3.4× 收到 1.6×，用引线标出仍高于 S01 的 1.1×。
- **Title**: 后淋洗有效但未完成，必须叠加 hood
- **Core message**: 淋洗组 D0 0.24 对对照 0.33；起停点仍 1.6×，残差仍是水印空间签名。
- **Content**: W33 S02 的 6 对 split；A：后淋洗 + 现有 hood，平均 D0 0.24；B：无后淋洗 + 现有 hood，平均 D0 0.33；A 组起停点富集 3.4×→1.6×，S01 为 1.1×。
- **Native shape suggestion**: 两枚圆形晶圆、直角扫描条带与起停点引线。
- **Data class: scenario**: split lot 均值与倍率为演示用虚构数据。
- **Fact IDs**: F008, F033

#### Slide 06 - W33 的 0.29 仍在控制上限之上

- **Audience move**: 把“已经从 0.51 降下来”校正为“仍未进入控制带”。
- **Layout**: 单轴时间线，W26–W33 折线穿过目标 0.20 与上限 0.28；W31 尖峰与 W33 0.29 用尺寸线标出。
- **Title**: W33 的 0.29 仍在控制上限之上
- **Core message**: 趋势在降，但 0.29 仍高于 0.28 上限，W35 释放不能只看斜率。
- **Content**: W26 0.17，W27 0.18，W28 0.16，W29 0.19，W30 0.18，W31 0.51，W32 0.37，W33 0.29；目标线 0.20；控制上限 0.28。
- **Visualization**: 数据驱动折线；参考 P06 `line_chart`。
- **Native-ready**: no
- **Data class: scenario**: 周次 D0、目标线与上限均为演示用虚构数据。

### Part 3: 释放标准

#### Slide 07 - 若只做淋洗，W35 仍可能停在 0.24 以上

- **Audience move**: 接受残差风险：后淋洗不够，hood 与 EBR 不关就升不了级。
- **Layout**: 左残余路径示意（后淋洗延迟 + hood 气帘未复测）；右三条风险轨，W35 0.24 升级门槛用阻塞红标尺。
- **Title**: 若只做淋洗，W35 仍可能停在 0.24 以上
- **Core message**: 未关闭项是 hood −0.05 与 EBR −0.02；残差 0.09 仍是水印路径。
- **Content**: 后淋洗仅部分 lot；hood 待 W34 PM；EBR 待 DOE；若 W35 仍高于 0.24，升级为浸没头更换评估，而不是继续只做淋洗。
- **Data class: scenario**: 预测贡献、升级门槛为演示用虚构设定。
- **Fact IDs**: F008, F033, F038

#### Slide 08 - W35 释放必须同时满足 D0、PWP 和捕获率

- **Audience move**: 带着四条可签批标准离开，而不是只记住“继续回收”。
- **Layout**: 四条释放标准签批板，编号 S1–S4，横贯全宽；底部红线写“不满足则不释放”。
- **Title**: W35 释放必须同时满足 D0、PWP 和捕获率
- **Core message**: 连续两周 D0 ≤0.20 且 S02 PWP ≤12；捕获率达标不得靠收阈值。
- **Content**: 1. 连续 2 周 D0 ≤0.20，且 S02 PWP ≤12。2. 水印占 SEM 分类 ≤15%，且扫描起停点富集 ≤1.5×。3. Capture ≥90%，Nuisance ≤12%，不得靠收阈值达成。4. 若 W35 仍高于 0.24，升级浸没头更换评估。
- **Data class: scenario**: 释放门槛为演示用虚构设定。
- **Fact IDs**: F008, F019, F023, F027, F042

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 每页先说结论，再补证据；所有数字口头标明“演示数据”
- **Total duration**: 15 minutes
- **Notes style**: formal
- **Presentation purpose**: report
