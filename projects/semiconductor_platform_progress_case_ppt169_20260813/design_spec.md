<!-- ppt-master-schema: design-spec/v1 -->
# 半导体设备实验平台能力建设项目阶段汇报 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 半导体设备实验平台能力建设项目阶段汇报 |
| Canvas Format | PPT 16:9（1280 × 720） |
| Page Count | 11 |
| Primary Language | zh-CN |
| Target Audience | 公司管理层，以及研发、工程、采购、EHS负责人；重点关注关键路径、能力形成和资源决策 |
| Communication Intent | 先用结论和证据说明平台建设阶段与已形成能力，再暴露影响阶段验收的关键阻塞，最后推动管理层确认未来90天行动与资源决策 |
| Desired Audience Outcome | 管理层能够判断项目是否仍可守住2026年12月15日阶段验收目标，并当场确认五项资源与合同决策 |
| Core Message / Ask / Action | 项目总体完成68.6%，已进入“设施收口、设备集中安装、首批能力验证”阶段；若五项决策按节点关闭，可追回7–10天并维持阶段验收目标 |
| Delivery Context | 主要用于有主讲人的15分钟管理层项目评审；次要用于会后独立阅读、决策留痕和周度行动跟踪 |
| Artifact Afterlife | 作为阶段评审材料、关键路径基线、管理决策记录和未来90天执行跟踪依据 |
| Reading Mode | balanced |
| Content Strategy | 可在不改变演示用虚构数据口径的前提下自由重组、提炼和可视化 |
| Design Style | 深色工程蓝图：技术图纸式网格、单线结构、尺寸标记与少量状态色 |
| Formula Policy | text-only |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — final Stage-2 proactive policy |
| Custom Animations | disabled — final Stage-2 proactive policy |
| Narration Audio | disabled — final Stage-2 proactive policy |
| Created Date | 2026-08-13 |

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
- **Theme**: 以暗色工程图纸为底，细网格和技术标注组织全篇；“当前关键路径”使用高亮青绿，“风险/待决策”使用琥珀色，红色仅用于明确阻塞。
- **Tone**: 专业、克制、精密、可审计；像项目评审图纸而非营销型科技发布会。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #071827 | 主画布与封面暗色图纸底 |
| Secondary background | #0D2538 | 内容分区、技术标题栏与深浅层级 |
| Primary | #87D9F5 | 结构线、坐标线、普通信息与系统连接 |
| Accent | #32E0C4 | 完成、可用、关键路径和正向状态 |
| Secondary accent | #FFB454 | 风险、偏差、待决策和临界状态 |
| Body text | #EAF7FF | 主体文本与关键数字 |
| Grid | #16384C | 背景网格、分隔线与弱化结构 |
| Muted text | #8BA9B8 | 注释、来源、次要说明 |
| Blocking | #FF6B6B | 明确阻塞、未通过和红线状态 |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | clean engineering sans / bold | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Body | clean engineering sans / regular | Microsoft YaHei | Arial | 微软雅黑, sans-serif |
| Data | technical monospace for codes and measurements | Consolas | Consolas | Microsoft YaHei, monospace |

- **Title stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Body stack**: `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- **Data stack**: `Consolas, "Microsoft YaHei", "微软雅黑", monospace`
- **Role rationale**: Data is recurring across equipment IDs, milestone codes, dates, measurements and component annotations; a monospace role reinforces the engineering-drawing language.

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

- **Header area**: 左上使用结论式标题；右上保留项目代号、数据日和页码式坐标标记。
- **Content area**: 让系统架构、时间轴、矩阵或状态轨道成为页面骨架；文字通过引线和标注依附于图形，不使用均匀卡片墙。
- **Footer area**: 所有含数字页面显示“演示用虚构数据｜不代表真实项目或行业标准”，并保留简短口径说明。

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
| tabler-outline/building-factory-2 | 场地、洁净环境、平台建设 |
| tabler-outline/circuit-resistor | 半导体设备、电气与工程系统 |
| tabler-outline/timeline | 里程碑、计划与时间窗口 |
| tabler-outline/tools | 安装、联调、工程整改 |
| tabler-outline/shield-check | EHS、放行条件与安全验收 |
| tabler-outline/alert-triangle | 风险、偏差与阻塞 |
| tabler-outline/route | 关键路径与未来90天路线 |
| tabler-outline/database | 数据链、追溯与平台接口 |
| tabler-outline/chart-dots-3 | 指标、覆盖率与验证结果 |
| tabler-outline/checklist | 决策清单、SOP和验收项 |

## VII. Visualization Reference List

| Page | Template | Usage |
| --- | --- | --- |
| P04 | progress_bar_chart | 对比八个工作包的完成率并突出总体68.6% |
| P06 | funnel_chart | 表达10个设备包从采购到验收的阶段收敛 |
| P07 | heatmap_chart | 表达八个能力域在可执行、联调中和未具备之间的覆盖差异 |
| P10 | roadmap_vertical | 组织未来13周七个执行阶段及出口条件 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## IX. Content Outline

### Part 1: 管理结论

#### Slide 01 - 封面

- **Audience move**: 从“尚不清楚项目真实阶段”到“先记住项目已进入能力形成期，但关键路径仍需管理动作”。
- **Layout**: 以68.6%作为绑定视觉钩子；用半透明工程网格、等轴测设备线框和一条从设施到验收的高亮路径构成主视觉，标题置于路径起点，数据日和项目代号置于图纸标题栏。
- **Title**: 半导体设备实验平台能力建设项目阶段汇报
- **Core message**: 平台已从基础建设转入设备联调与能力验证，关键阻塞的关闭速度将决定阶段验收能否按期完成。
- **Content**: 主标题；副标题“设施收口｜设备集中安装｜首批能力验证”；英雄数字“68.6% 总体完成度”；状态标记“较基线计划落后4.1个百分点”；数据日“2026-08-12”；底部显著标注“演示用虚构案例”。
- **Cover impact**: 绑定钩子为“68.6%完成，但关键路径仍落后4.1个百分点”；构图使用工程尺寸线框住68.6%，让一条琥珀色关键路径穿过设备线框并在验收节点转为青绿色。
- **Data class: scenario**: 项目名称、日期、68.6%、4.1个百分点及所有阶段判断均为演示用虚构数据。

#### Slide 02 - 项目仍可守住12月验收，但四项高关注风险必须立即升级

- **Audience move**: 从“知道项目正在建设”到“形成对进度、能力、风险和决策的一页式管理判断”。
- **Layout**: 左侧以68.6%主仪表和关键路径判断为焦点；右侧沿纵向信号带排列“进展、能力、风险、决策”四组结论，底部用五个决策编号形成待办轨道。
- **Title**: 项目仍可守住12月验收，但四项高关注风险必须立即升级
- **Core message**: 三个阻塞按计划关闭即可维持目标；管理决策迟于节点将把最大延期风险放大至15天。
- **Content**: ①总体进度68.6%，落后4.1个百分点；②已形成1套工艺设备＋1套量测设备的最小闭环；③10个设备包中6个到场、5个安装完成、3个进入联调、1个阶段验收通过；④当前高关注风险R01/R02/R04/R06共4项；⑤D01–D05五项决策须在8月16–21日完成；管理判断“按时决策可追回7–10天，维持2026-12-15阶段验收目标”。
- **Data class: scenario**: 本页全部数字、风险编号、决策编号、日期和管理判断均为演示用虚构数据。

### Part 2: 建设与能力形成

#### Slide 03 - 平台能力由“设施底座—工艺设备—量测数据—四级放行”共同闭环

- **Audience move**: 从“把平台理解为设备采购集合”到“理解能力形成依赖设施、设备、量测、数据和安全门的系统闭环”。
- **Layout**: 使用全页蓝图式分层架构：底层为洁净环境与五类公用工程，中层为六类工艺/设备能力，上层为量测、数据追溯和验收；右侧用G1–G4四个阶段门形成纵向放行标尺，组件以引线标注。
- **Title**: 平台能力由“设施底座—工艺设备—量测数据—四级放行”共同闭环
- **Core message**: 设备到场不等于平台可用，只有设施、单机、工艺和跨设备数据四个阶段门依次关闭，能力才可被管理层认可。
- **Content**: 设施底座：洁净环境、中央真空、特气、工艺冷却水、普通/UPS供电、排风监测；工艺设备：刻蚀、PVD、CVD、ALD、热处理、湿法清洗；量测与数据：膜厚、真空诊断、电学测试、样品流转、数据归档；阶段门：G1设施可用、G2单机可用、G3工艺可用、G4平台可用；建设目标覆盖薄膜沉积、刻蚀、热处理、清洗、真空诊断、膜厚与电学测试。
- **Native shape suggestion**: 使用基础矩形、等轴测平行四边形与直角Connector构成可编辑分层系统图，阶段门采用四级块箭头序列。
- **Data class: scenario**: 能力范围、系统组成和G1–G4门槛均为演示用虚构设定。

#### Slide 04 - 前端设计已闭环，当前落后集中在公用工程、设备安装与联调

- **Audience move**: 从“只看到一个总体百分比”到“定位造成计划偏差的具体工作包和后续里程碑”。
- **Layout**: 左侧用八条细线进度轨道显示工作包完成率，右侧用M0–M8里程碑时间轴标出实际/预测偏差；总体68.6%置于两区交汇点，琥珀色标注关键路径。
- **Title**: 前端设计已闭环，当前落后集中在公用工程、设备安装与联调
- **Core message**: 需求与设计均已完成，公用工程78%、设备安装48%、系统联调22%是决定后续验收节奏的三组关键工作。
- **Content**: 工作包完成率：需求与方案100%、详细设计与安全评审100%、场地与洁净环境92%、公用工程78%、设备采购与物流71%、设备安装48%、系统联调22%、能力验证12%；里程碑：M5全部设备到场预测延后10天，M6核心安装预测延后7天，M7多机联调预测延后5天，M8阶段验收目标仍维持2026-12-15。
- **Visualization**: 数据驱动的工作包进度条＋里程碑偏差时间轴；参考P04 `progress_bar_chart`，按蓝图线轨重新设计。
- **Native-ready**: no
- **Data class: scenario**: 所有完成率、日期和偏差均为演示用虚构数据。

#### Slide 05 - 主设施已支持三机并行，UPS与特气决定下一阶段放量上限

- **Audience move**: 从“设施基本完成”到“理解哪些系统已经可用、哪些约束直接限制多机联调和带片验证”。
- **Layout**: 以实验平台平面蓝图为中心，七个公用工程子系统围绕核心设备区分布；通过引线显示状态、当前值与关闭节点；右下角用“当前并行上限”技术框突出1台高负载＋2台低负载限制。
- **Title**: 主设施已支持三机并行，UPS与特气决定下一阶段放量上限
- **Core message**: 洁净环境、主真空、主冷却水和普通供电已可用，但UPS容量和特气联锁尚未完全放行。
- **Content**: 洁净环境合格率94.2%，2个回风口待整改；中央真空备用系统带载测试60%，1个远端支路压降偏差18%；特气14个末端点位中8个气密通过、2个联锁逻辑待复核；冷却水12个支路中9个具备供水条件；普通供电18个回路中16个送电；UPS当前可用420 kVA、目标600 kVA；设施数据点接入118/126、接入率93.7%。结论：当前最多支持3台设备并行调试，涉及G-D/G-E/G-F的工艺不得带片。
- **Visualization**: 自定义蓝图式系统就绪图；各子系统使用状态线和技术参数标注，不采用营销卡片。
- **Native-ready**: no
- **Data class: scenario**: 所有参数、点位、限制和关闭节点均为演示用虚构数据，不代表行业标准。

#### Slide 06 - 设备链路呈“10→9→6→5→3→1”收敛，瓶颈已从采购转向联调验收

- **Audience move**: 从“逐台查看设备清单”到“看清设备全流程的阶段收敛和三台关键设备的下一节点”。
- **Layout**: 横向工程漏斗贯穿页面，六段分别为采购启动、合同生效、到场、安装完成、进入联调、验收通过；下方用三条设备轨道标注E02、E03、E10的阻塞与下一节点。
- **Title**: 设备链路呈“10→9→6→5→3→1”收敛，瓶颈已从采购转向联调验收
- **Core message**: 到场和安装已进入集中阶段，但特气联锁、量测资源和数据平台合同决定设备能否快速转化为可验收能力。
- **Content**: 漏斗数据：采购启动10、合同生效9、到场6、安装完成5、进入联调3、阶段验收通过1；关键设备：E02沉积平台联调80%，需完成厚度均匀性复测；E03沉积平台安装完成但等待特气联锁；E10样品流转与数据平台合同谈判90%，需在8月18日前完成分段交付决策。
- **Visualization**: 数据驱动的阶段漏斗；参考P06 `funnel_chart`，采用线框和节点编号表达。
- **Native-ready**: no
- **Data class: scenario**: 设备包、数量、状态、日期和阻塞均为演示用虚构数据。

#### Slide 07 - 当前仅40%的测试方法可执行，量测与数据链是扩大覆盖的共同瓶颈

- **Audience move**: 从“设备安装进度”转向“用可执行测试方法衡量平台是否真正形成能力”。
- **Layout**: 左侧以20类方法的矩阵热图显示8类可执行、5类联调中、7类未具备；右侧用从工艺到量测再到数据归档的最小闭环示意，突出当前已打通的E01路径。
- **Title**: 当前仅40%的测试方法可执行，量测与数据链是扩大覆盖的共同瓶颈
- **Core message**: 刻蚀能力已形成，沉积与热处理正在爬坡；量测、诊断和电学测试的到位速度决定覆盖率能否从40%提升至85%。
- **Content**: 能力域：刻蚀3/3可执行；薄膜沉积2可执行＋2联调；热处理1可执行＋1联调；湿法清洗1联调＋1未具备；真空诊断0/2；膜厚量测1/3；电学测试0/2；数据追溯1可执行＋1联调；合计20类中8类可执行、5类联调、7类未具备。最小闭环：E01已验证3类配方、18批次、216个样品；自动归档字段覆盖率92%。
- **Visualization**: 数据驱动的能力覆盖热图；参考P07 `heatmap_chart`，使用三种状态线密度而非多彩填色。
- **Native-ready**: no
- **Data class: scenario**: 所有能力域、方法数、批次、样品数和覆盖率均为演示用虚构数据。

#### Slide 08 - 能力验证一次通过率仅40%，参数、设施与数据规则需并行收敛

- **Audience move**: 从“知道已有首批能力”到“理解当前能力距离阶段验收的具体差距及组织/EHS准备度”。
- **Layout**: 左侧用10条验收轨道显示4项通过、6项未通过及差距；右侧分上下两区显示SOP/人员和EHS放行准备度，底部用三类关闭路径连接到10月31日80%目标。
- **Title**: 能力验证一次通过率仅40%，参数、设施与数据规则需并行收敛
- **Core message**: 未通过项并非单一设备问题，需参数优化、设施整改和数据规则修订三条路径同步推进。
- **Content**: 通过：刻蚀重复性1.6%、沉积重复性2.2%、刻蚀72小时可用率96.2%、报警响应2.4分钟；未通过：沉积稳定性93.8%、刻蚀吞吐17.2个/小时、真空恢复13.5分钟、温度稳定性±0.7℃、数据链完整率98.8%、样品匹配99.6%；当前4/10通过，一次通过率40%，10月31日目标≥80%。准备度：设备操作SOP 19/28批准、31/46人认证、EHS开放问题7项且高风险0项。
- **Visualization**: 自定义验收状态轨道＋准备度刻度；每项显示门槛、实测与差距。
- **Native-ready**: no
- **Data class: scenario**: 所有门槛、实测值、样本、人数和目标均为演示用虚构数据，不代表行业标准。

### Part 3: 风险、执行与决策

#### Slide 09 - 四项高关注风险共同挤压关键路径，最坏可造成15天延期

- **Audience move**: 从“风险列表”到“识别必须管理升级的四个杠杆及其对阶段验收的共同影响”。
- **Layout**: 左侧用关键路径链展示UPS→多机联调、数据合同→追溯验收、E09物流→电学覆盖、量测资源→验证排队；右侧用概率×影响矩阵标出R01/R02/R04/R06，并以底部结果条对比“不干预15天”与“及时决策追回7–10天”。
- **Title**: 四项高关注风险共同挤压关键路径，最坏可造成15天延期
- **Core message**: 风险并非独立发生，设施并行能力、数据平台、量测资源和物流窗口共同决定联调与验证吞吐。
- **Content**: R01 UPS容量不足，概率70%，影响8–12天；R02数据平台合同未锁定，概率60%，影响10–15天；R04 E09物流延迟，概率65%，影响电学能力至9月下旬；R06量测资源不足，概率55%，日均等待增加6小时。管理动作：夜间切换扩容、核心接口先行、加急物流＋临时通道、8周量测租用。若按节点决策，预计追回7–10天。
- **Visualization**: 管理分区式风险路径与2×2概率影响矩阵；概率与影响以标签呈现，点位只表达高关注象限，不做精确坐标映射。
- **Native-ready**: no
- **Data class: scenario**: 风险、概率、影响、日期和追回天数均为演示用虚构数据。

#### Slide 10 - 未来13周按“设施放行—设备收口—多机验证—预验收”四段推进

- **Audience move**: 从“知道问题和目标”到“获得可执行、可追踪的未来90天节奏和每段出口条件”。
- **Layout**: 使用纵向蓝图路线图承载七个时间窗；每个节点包含任务、量化交付、出口条件与责任角色，右侧以四个90天结果指标形成终点标尺。
- **Title**: 未来13周按“设施放行—设备收口—多机验证—预验收”四段推进
- **Core message**: 前四周关闭设施与联锁，第六周完成九台安装，第十周完成十台收口，第十三周形成预验收报告。
- **Content**: 第1–2周关闭9个设施整改项并完成E04安装；第3–4周完成特气联锁、三台设备进入联调、UPS达到600 kVA；第5–6周完成E07/E08/E09安装并新增4类方法；第7–8周打通4台设备、2套量测和1套数据平台；第9–10周十台安装完成且至少8项指标通过；第11–12周完成4台核心设备72小时验证；第13周形成预验收报告。90天结果：安装率50%→100%，方法覆盖40%→85%，一次通过率40%→≥80%，认证操作员31→42。
- **Visualization**: 阶段驱动的七节点纵向路线图；参考P10 `roadmap_vertical`，节点按执行顺序等距排列并带出口条件和责任角色。
- **Native-ready**: no
- **Data class: scenario**: 时间窗、任务、交付、目标和责任角色均为演示用虚构数据。

#### Slide 11 - 五项决策需在8月21日前完成，才能用有限增量投入守住阶段验收

- **Audience move**: 从“理解项目状态”到“明确批准什么、何时批准以及不决策的直接后果”。
- **Layout**: 以D01–D05五条决策轨道作为页面主体；每条轨道依次显示建议选项、投入、最晚日期和不决策后果；右下角用工程签批框呈现总原则和明确的确认动作。
- **Title**: 五项决策需在8月21日前完成，才能用有限增量投入守住阶段验收
- **Core message**: 立即批准UPS扩容、数据平台分段交付、临时量测、E09加急和六名专职资源，是维持12月15日目标的最小管理动作集。
- **Content**: D01 UPS扩容：120万元，8月16日前；D02数据平台核心接口先行：首阶段260万元、总上限420万元，8月18日前；D03临时量测：35万元，8月19日前；D04 E09加急与替代通道：18万元，8月20日前；D05调配6名全职人员10周，8月21日前。管理原则：阶段验收优先、设施/单机/平台分层放行但EHS红线不豁免、每周45分钟关键路径例会、延期>5天或预算偏差>10%自动升级。
- **Visualization**: 纯文本决策轨道与签批框，使用琥珀色标出最晚决策日，红色仅标出不决策后果。
- **Native-ready**: no
- **Closing impact**: 绑定结论为“决策窗口只有5天”；构图让五条轨道汇聚至“2026-12-15阶段验收”终点，并以一个可编辑签批框明确“批准/调整/退回”。
- **Data class: scenario**: 所有金额、日期、资源、阈值和后果均为演示用虚构数据，不构成真实投资或采购建议。

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 每页先讲结论，再解释关键数据、风险因果和管理含义；所有数字必须口头声明为演示用虚构数据，不补充外部行业事实。
- **Total duration**: 15 minutes
- **Notes style**: formal, concise, decision-oriented
- **Presentation purpose**: report progress, explain capability formation, expose risk, and obtain management decisions
