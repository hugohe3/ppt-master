# 如何用公司 AI 复刻本 PPT 的展示效果

本文件面向公司内网 Agent。当前参考模型是 **DeepSeek V4 Flash 0731**，无生图能力。不要把材料上传到公网。

**结论先行**：Flash 不能从一段文案自己“发明”出当前效果。要复刻，必须把本项目的视觉合同和 11 页几何骨架一起交给它，只允许换内容和数字，不允许重做风格。无生图不是障碍——这份案例本来就禁止配图。

---

## 1. 先认清上限

| 真实原因 | 说明 |
| --- | --- |
| 模型视觉/坐标能力弱 | Flash 类模型写 SVG 时容易字号乱、对齐漂、标题溢出、卡片墙回潮。差效果通常不是缺图。 |
| 跳过了视觉合同 | 只喂文案、走 Quick、不写 `design_spec.md` / `spec_lock.md`、不跑质量门，就会回到“普通公文 PPT”。 |
| 字体回退 | 公司 Windows 必须能用微软雅黑和 Consolas。不要换成 Linux 专用字体。 |
| 无生图 | 与本案例一致。`image_usage: none`。禁止调用任何外部图片或 AI 生图服务。 |

**不要做**：让 Flash 从零设计一版“科技感 / 商务风 / 咨询风”。它会退化成圆角卡片、彩虹色块和居中大标题。

**要做**：把本目录当作版式母版。Agent 只替换文案、编号和数字，保留网格、配色、字号、页骨架和图表几何。

---

## 2. 拷到公司电脑的最小包

整目录拷贝最稳。若必须精简，至少带这些文件：

```text
design_spec.md
spec_lock.md
REPLICATE.md
svg_output/*.svg
icons/tabler-outline/*.svg
sources/semiconductor_platform_case_research.md
```

同时保证本机已安装 PPT Master，并能运行：

```bash
python3 skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 skills/ppt-master/scripts/icon_sync.py <project_path> tabler-outline/building-factory-2 tabler-outline/circuit-resistor tabler-outline/timeline tabler-outline/tools tabler-outline/shield-check tabler-outline/alert-triangle tabler-outline/route tabler-outline/database tabler-outline/chart-dots-3 tabler-outline/checklist
python3 skills/ppt-master/scripts/svg_quality_checker.py <project_path>
python3 skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project_path>
```

---

## 3. 推荐执行路径（Flash 专用）

按可靠性从高到低：

### 路径 A — 几何复用，只换内容（首选）

1. 用 `project_manager.py init` 建新项目，画布必须是 `ppt169`（1280×720）。
2. 原样复制本项目的 `design_spec.md` 视觉章节、`spec_lock.md`、`svg_output/`、`icons/`。
3. 把内部真实材料放进新项目 `sources/`。所有数字若仍是演示口径，必须保留“演示用虚构数据”；换成真实内部数据后删除虚构标记。
4. **禁止重画页面结构。** 只改 `svg_output/` 里已有文字、数值、状态色和必要标注。
5. 标题必须仍是结论句，不能改成“工作进展 / 下一页 / 谢谢”。
6. 跑 `svg_quality_checker.py`，blocking error 必须为 0，再 `finalize_svg.py` 和 `svg_to_pptx.py`。

11 页骨架必须保持：

| 页 | 文件 | 作用 | 节奏 |
| --- | --- | --- | --- |
| P01 | `01_cover.svg` | 封面：一个绑定数字 + 设施→安装→验证→验收路径 | anchor |
| P02 | `02_executive_summary.svg` | 管理摘要：进展/能力/风险/决策四信号 + 决策轨道 | anchor |
| P03 | `03_capability_architecture.svg` | 分层能力架构 + 阶段门 | breathing |
| P04 | `04_progress_milestones.svg` | 工作包进度条 + 里程碑偏差 | dense |
| P05 | `05_facilities_readiness.svg` | 设施/公用工程就绪图 | dense |
| P06 | `06_equipment_funnel.svg` | 设备漏斗 + 关键阻塞轨道 | anchor |
| P07 | `07_capability_heatmap.svg` | 能力覆盖热图 | dense |
| P08 | `08_validation_readiness.svg` | 验收计分板 | dense |
| P09 | `09_risk_critical_path.svg` | 高关注风险分区 | dense |
| P10 | `10_ninety_day_roadmap.svg` | 13 周 / 90 天路线图 | dense |
| P11 | `11_management_decisions.svg` | 管理决策签批 | breathing |

若真实材料撑不满 11 页：允许合并相邻 dense 页，但不得改配色、字体、网格语言，也不得改成卡片墙。

### 路径 B — 锁定合同后走 Default Generate

仅当新材料的信息架构与这 11 页明显不同、必须重排页面时使用。仍然禁止 Flash 自由设计。

1. 读取 `skills/ppt-master/SKILL.md` → `workflows/routing.md`。
2. 路由必须是 **Generate PPTX / Default**，不是 Quick，不是 Beautify，不是 Fill Native，不是 Enhance Native。
3. 把本项目 `spec_lock.md` 的 canvas / visual_style / colors / typography / icons / forbidden 整段视为不可修改合同。
4. Stage 1 确认时选择 **free_design 但视觉合同锁定**，或先把本案例做成 Create Style/Create Deck 模板后再选 templates。未完成 Create Template 前，不要假装已经选中了模板库。
5. `AI Image Acquisition Path: not applicable`。`image_usage: none`。不写 `image_prompts.json`，不调用 `image_gen.py`。
6. 图标只允许 `icon_sync.py` 同步 `tabler-outline` 线框，`stroke_width: 2`。
7. 公式政策：`text-only`。
8. 结构：`pptx_structure.mode: flat`。
9. 终检 0 error 后才导出。

### 路径 C — 先做成可复用模板（中长期）

若公司要反复生成“同一套工程蓝图风管理层汇报”，应在可联网或本机完整仓库上走 Create Template，产出 `style` 或 `deck` workspace，再作为 Generate 的 Stage-1 候选。Flash 不适合承担 Create Template 的几何抽取。不要把原始 PPTX 直接当 Generate 模板。

---

## 4. 视觉合同（必须原样遵守）

- 画布：PPT 16:9，`viewBox="0 0 1280 720"`，边距 40px
- 模式：`pyramid`（结论先行）
- 视觉风格：`blueprint`
- 阅读模式：`balanced`
- 背景 `#071827`；分区底 `#0D2538`；结构线 `#87D9F5`；完成/可用 `#32E0C4`；风险/待决策 `#FFB454`；正文 `#EAF7FF`；网格 `#16384C`；注释 `#8BA9B8`；明确阻塞 `#FF6B6B`
- 标题/正文：`"Microsoft YaHei", "微软雅黑", Arial, sans-serif`
- 编号/参数/日期：`Consolas, "Microsoft YaHei", "微软雅黑", monospace`
- 字号：body 24 / title 42 / subtitle 32 / lead 30 / data 20 / annotation 18 / footnote 16
- 图标：`tabler-outline`，描边 2
- 禁止：`mask`、`<style>`、`class`、外部 CSS、`<foreignObject>`、`textPath`、`@font-face`、动画元素、`<script>`、HTML 命名实体
- 禁止：卡片墙、大圆角营销块、彩虹配色、渐变炫光、照片/插画、强行配图、居中海报标题、把结论句改成栏目名

---

## 5. 直接粘贴给公司 Agent 的指令

把下面整段连同本项目目录一起交给 Agent。把 `<新项目路径>` 和材料来源换成公司内部路径。

```text
你必须使用本机已安装的 PPT Master。先读 skills/ppt-master/SKILL.md 和 workflows/routing.md。

本次任务：用我提供的内部材料，复刻参考项目的展示效果，而不是重新设计。
参考项目路径：<本案例目录>
新项目路径：<新项目路径>
模型约束：DeepSeek V4 Flash 0731；无生图；材料不得上传外网。

硬性路由：Generate PPTX / Default。禁止 Quick。禁止 Beautify。禁止 Fill Native。禁止 Enhance Native。禁止调用 image_gen.py 或任何外部图片服务。

视觉合同不可修改，必须逐项抄自参考项目 spec_lock.md：
- 画布 1280×720，viewBox 0 0 1280 720
- pyramid + blueprint
- 配色、字体栈、字号、tabler-outline stroke 2、flat 结构、forbidden 列表

执行方式（Flash 专用，优先级最高）：
1. init 新项目，format=ppt169。
2. 复制参考项目的 design_spec.md 视觉章节、spec_lock.md、svg_output/ 全部 SVG、icons/。
3. 将我的内部材料写入 sources/。只替换各页已有文字、数字、状态色和必要标注。
4. 禁止重排版、禁止改网格语言、禁止改成卡片墙、禁止增加照片或插画。
5. 每页标题必须是结论句。
6. 图标只许使用已同步到项目 icons/ 的 tabler-outline 文件。
7. 跑 svg_quality_checker.py；blocking error 必须为 0。若溢出，缩短标题/标注并扩大 data-pptx-bounds，不要缩小到不可读。
8. 再串行执行 finalize_svg.py 和 svg_to_pptx.py（需要备注则不要加 --no-notes）。

11 页骨架保持：封面绑定数字、管理四信号、分层架构、进度条+里程碑、设施就绪图、设备漏斗、能力热图、验收计分板、风险分区、90天路线图、决策签批。真实材料不足时允许合并 dense 页，但不得破坏视觉合同。

成功标准：导出 PPTX 后，第一眼仍是深色工程蓝图，而不是浅底公文页或彩色卡片墙。
```

---

## 6. 验收清单

打开导出 PPTX 后，下列任一项失败即未复刻成功，必须回到 `svg_output/` 修源文件，不要在 PowerPoint 里手工“美化”充数：

- [ ] 深色图纸底，可见细网格，不是白底或浅灰公文底
- [ ] 完成态青绿、风险琥珀、阻塞红，没有额外彩虹色
- [ ] 标题是结论句，左上对齐，不是居中海报标题
- [ ] 正文微软雅黑，编号/参数 Consolas；没有变成宋体或默认 Calibri 全文
- [ ] 没有均匀圆角卡片墙，没有照片插画
- [ ] 漏斗、进度条、热图、路线图仍是线框工程图，不是 SmartArt 默认样式
- [ ] 质量报告 0 blocking error；导出报告 `passed` 或 `passed-with-warnings`

Flash 仍可能把长标题写爆。处理原则：缩短句子，不要缩小字号到 16px 以下充正文。
