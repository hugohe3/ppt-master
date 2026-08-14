# 如何用公司 AI 复刻本 PPT 的展示效果

本文件面向公司内网 Agent。当前参考模型是 **DeepSeek V4 Flash 0731**，无生图能力。不要把材料上传到公网。

**结论先行**：复刻的是工程蓝图这套**视觉语言**，不是把新内容填进现成骨架。页数、信息架构和每页构图必须按你提供的材料重新规划；配色、字体、网格、线框语法和质量门不可改。无生图不是障碍——这些样板本来就禁止配图。

浸没式光刻缺陷周报请优先对照这三份专项样板，而不是半导体设备平台那 11 页：

| 周会类型 | 项目目录 | 导出 PPTX |
| --- | --- | --- |
| 缺陷检测结果 | `projects/immersion_defect_inspection_weekly_ppt169_20260814/` | `exports/immersion_defect_inspection_weekly_20260814_024226.pptx` |
| 指标回收 | `projects/immersion_defect_metric_recovery_ppt169_20260814/` | `exports/immersion_defect_metric_recovery_20260814_024240.pptx` |
| 项目进展 | `projects/immersion_defect_project_progress_ppt169_20260814/` | `exports/immersion_defect_project_progress_20260814_024250.pptx` |

---

## 1. 锁什么，放什么

| 必须锁定 | 必须按新内容决定 |
| --- | --- |
| `blueprint` 视觉语言：暗底、细网格、单线结构、尺寸标注、引线 | 页数、页序、每页要回答的管理问题 |
| 配色、字体栈、字号、`tabler-outline` 描边 2 | 这一页用漏斗、热图、进度轨、架构图还是决策板 |
| `pyramid`：标题是结论句，不是栏目名 | 主视觉放左还是铺满；哪里留白、哪里加密 |
| `image_usage: none`；不生图、不配照片 | 哪些数字做英雄钩子，哪些降为标注 |
| SVG 禁令与质量门 0 blocking error | 材料不够就不硬凑 11 页；材料密就拆页，不把一页写成墙 |

参考项目的 `svg_output/` 是**语法样本**，不是填空母版。允许打开 1–2 页看网格、标题栏、引线和状态色怎么用，然后为新内容手写新 SVG。禁止整页复制后只换字。

---

## 2. 先认清失败模式

| 失败原因 | 表现 |
| --- | --- |
| 跳过视觉合同 | 走 Quick、不写 `spec_lock.md`、不跑质量门 → 浅底公文页 |
| 把“合理排版”理解成默认商务风 | 圆角卡片墙、彩虹色块、居中海报标题 |
| 把参考页当填空 | 你的材料被硬塞进半导体平台那 11 个槽位，信息架构错位 |
| 字体回退 | 公司 Windows 没有微软雅黑 / Consolas |
| 溢出后乱缩字 | 正文小于 16px，看起来像备注而不是汇报 |

无生图与本案例一致。禁止 `image_gen.py` 和任何外部图片服务。

---

## 3. 拷到公司电脑的最小包

整目录拷贝最稳。若必须精简，至少带：

```text
design_spec.md
spec_lock.md
REPLICATE.md
svg_output/01_cover.svg
svg_output/02_executive_summary.svg
svg_output/03_capability_architecture.svg
icons/tabler-outline/*.svg
```

`01`/`02`/`03` 足够示范封面钩子、四信号摘要、分层架构三种构图语法。其余页按需打开，不要整包当母版复制。

同时保证本机已安装 PPT Master，并能运行：

```bash
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/icon_sync.py <project_path> <tabler-outline/name...>
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

图标按新内容从 `tabler-outline` 重选并 `icon_sync.py` 同步，不必沿用本案例那 10 个文件名。

---

## 4. 推荐执行路径

走 **Generate PPTX / Default**。Stage 1 选 **free_design**，但把本项目 `spec_lock.md` 的 canvas / visual_style / colors / typography / forbidden 整段写入新项目，视为不可修改合同。

1. 读 `skills/ppt-master/SKILL.md` → `workflows/routing.md` → `workflows/generate-pptx.md`。
2. 禁止 Quick、Beautify、Fill Native、Enhance Native。
3. `project_manager.py init`，画布 `ppt169`（1280×720）。
4. 把内部材料写入 `sources/`。数字若仍是演示口径，保留“演示用虚构数据”；换成真实内部数据后删除虚构标记。
5. 先根据材料写沟通合同：受众、要他们带走的判断、核心请求、页大纲。页大纲来自材料结构，不来自本案例 11 页目录。
6. 把参考 `spec_lock.md` 的视觉段抄进新 lock；`page_rhythm`、`page_charts`、`icons.inventory` 按新大纲重写。
7. 图标：`icon_sync.py` 同步本盘会用到的 `tabler-outline`。`AI Image Acquisition Path: not applicable`。不写 `image_prompts.json`。
8. 为每一页**新写** SVG。构图规则见 §5。打开参考 SVG 只为模仿线宽、网格和标注语法。
9. `svg_quality_checker.py` blocking error 必须为 0，再串行 `finalize_svg.py` 和 `svg_to_pptx.py`。

中长期若要反复生成同一套蓝图风，再走 Create Template 做成 style/deck。Flash 可以执行 Default Generate；不要让它做模板抽取，也不要把原始 PPTX 直接当 Generate 模板。

---

## 5. 按内容选构图（合理排版的规则）

先判断这一页要完成的**管理动作**，再选骨架。不要先画四个等大卡片再往里塞字。

| 材料形态 | 优先骨架 | 不要用 |
| --- | --- | --- |
| 一个必须先记住的判断或数字 | 尺寸线框住英雄数字；一条关键路径穿过主图 | 居中海报标题 + 装饰圆环 |
| 3–5 个并列管理信号 | 纵向/横向信号带，结论在前、证据用引线挂上 | 2×2 圆角卡片墙 |
| 系统、分层、闭环、阶段门 | 全页示意图：层、连接、放行标尺 | 左列表右插画 |
| 同类完成率 / 进度对比 | 细线进度轨 + 一个汇合数字 | 饼图墙、3D 柱 |
| 阶段收敛、漏斗、转化 | 横向工程漏斗，阻塞另开轨道 | 默认 SmartArt 漏斗 |
| 覆盖、具备/不具备矩阵 | 热图或状态格，三色语义固定 | 每格一篇短文 |
| 时间与出口条件 | 路线图或里程碑轴，节点写出口而不是活动名 | 日历贴片 |
| 需要当场拍板的事项 | 决策签批板：编号、窗口、不决策的后果 | “谢谢 / Q&A” |

**排版纪律**：

- 标题左上，结论句；右上放项目代号、数据日、页码坐标。
- 让示意图成为页面骨架，文字挂在引线和标注上，而不是先铺满文本框。
- 完成/可用只用 `#32E0C4`，风险/待决策只用 `#FFB454`，明确阻塞只用 `#FF6B6B`。不要为“好看”加第四种强调色。
- 页节奏按信息密度定：`anchor` / `breathing` / `dense`。一页只服务一个受众动作。
- 溢出时先缩短标题、拆页或扩大 `data-pptx-bounds`，不要把正文字号压到 16px 以下。

参考页对照（只学语法，不复制槽位）：

- `01_cover.svg`：一个绑定数字 + 路径
- `02_executive_summary.svg`：四信号 + 底部决策轨道
- `03_capability_architecture.svg`：分层架构 + 阶段门

---

## 6. 视觉合同（必须原样遵守）

- 画布：PPT 16:9，`viewBox="0 0 1280 720"`，边距 40px
- 模式：`pyramid`（结论先行）
- 视觉风格：`blueprint`
- 阅读模式：按材料选 `balanced` 或更密/更疏，但不要改成营销演示
- 背景 `#071827`；分区底 `#0D2538`；结构线 `#87D9F5`；完成/可用 `#32E0C4`；风险/待决策 `#FFB454`；正文 `#EAF7FF`；网格 `#16384C`；注释 `#8BA9B8`；明确阻塞 `#FF6B6B`
- 标题/正文：`"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- 编号/参数/日期：`Consolas, "Microsoft YaHei", "微软雅黑", monospace`
- 字号：body 24 / title 42 / subtitle 32 / lead 30 / data 20 / annotation 18 / footnote 16
- 图标：`tabler-outline`，描边 2
- 结构：`pptx_structure.mode: flat`
- 公式：`text-only`
- 禁止：`mask`、`<style>`、`class`、外部 CSS、`<foreignObject>`、`textPath`、`@font-face`、动画元素、`<script>`、HTML 命名实体
- 禁止：卡片墙、大圆角营销块、彩虹配色、渐变炫光、照片/插画、强行配图、居中海报标题、把结论句改成栏目名

---

## 7. 直接粘贴给公司 Agent 的指令

把下面整段连同参考目录一起交给 Agent。把路径换成公司内部路径。

```text
你必须使用本机已安装的 PPT Master。先读 skills/ppt-master/SKILL.md、workflows/routing.md、workflows/generate-pptx.md。

本次任务：用我提供的内部材料生成新的管理层汇报 PPT。复刻参考项目的视觉语言，但必须按我的内容重新规划页数、信息架构和每页构图。不要把我的材料填进参考项目的 11 页槽位。

参考项目路径：<本案例目录>
新项目路径：<新项目路径>
模型：DeepSeek V4 Flash 0731；无生图；材料不得上传外网。

硬性路由：Generate PPTX / Default。禁止 Quick / Beautify / Fill Native / Enhance Native。禁止 image_gen.py 和任何外部图片服务。Stage 1 选 free_design。

视觉合同不可修改，从参考项目 spec_lock.md 抄入 canvas / visual_style / colors / typography / forbidden：
- 1280×720，viewBox 0 0 1280 720
- pyramid + blueprint
- 配色、微软雅黑+Consolas 字号层级、tabler-outline stroke 2、flat 结构

内容权：
- 以 sources/ 里我的材料为唯一事实来源。
- 先写沟通合同：受众、要带走的判断、核心请求，再写页大纲。
- 页大纲按材料结构决定，不复制参考项目的 11 页目录。
- 参考 svg_output/ 只作为语法样本。最多精读 01_cover / 02_executive_summary / 03_capability_architecture，学习网格、标题栏、引线、状态色。然后为每一页新写 SVG。

排版规则：
- 每页先判断管理动作，再选骨架：英雄数字用尺寸线；3–5 个信号用信号带；系统用分层示意图；对比用进度轨；收敛用漏斗；覆盖用热图；时间用路线图；拍板用决策板。
- 禁止 2×2 卡片墙、居中海报标题、彩虹强调色、照片插画。
- 标题必须是结论句，左上对齐。
- 示意图做骨架，文字用引线挂上。
- 完成/可用 #32E0C4，风险/待决策 #FFB454，阻塞 #FF6B6B。

执行：
1. init 新项目，format=ppt169。
2. 导入我的材料到 sources/。
3. 写 design_spec.md 与 spec_lock.md：视觉段锁定，page_rhythm / page_charts / icons 按新大纲重写。
4. icon_sync.py 只同步本盘将使用的 tabler-outline 图标。
5. 手写全部 svg_output/ 新页面。
6. svg_quality_checker.py 的 blocking error 必须为 0。溢出则缩短标题、拆页或扩大 bounds，不要把正文缩到 16px 以下。
7. 串行 finalize_svg.py 与 svg_to_pptx.py。

成功标准：第一眼仍是深色工程蓝图；页结构和图表种类明显服务我的材料，而不是半导体平台那 11 页的换皮。
```

---

## 8. 验收清单

- [ ] 深色图纸底 + 细网格，不是白底公文或浅灰咨询页
- [ ] 状态色只有青绿 / 琥珀 / 阻塞红，没有额外彩虹色
- [ ] 标题是结论句，左上对齐
- [ ] 微软雅黑 + Consolas，不是宋体或全文 Calibri
- [ ] 没有均匀圆角卡片墙，没有照片
- [ ] 页数和骨架能从你的材料解释，而不是参考项目换皮
- [ ] 质量报告 0 blocking error；导出 `passed` 或 `passed-with-warnings`
