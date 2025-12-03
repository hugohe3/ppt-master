# GEMINI.md

本文件为本仓库中的 AI 协作与实施指引。

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统，通过四角色协作将来源文档转化为高质量输出。除演示文稿外，还支持社交媒体与营销物料等多种画布格式。本项目是一个「文档与工作流框架」项目，而非可编译的传统代码库。此处的“代码”特指基于角色规范由 AI 代理生成的 SVG 标记。

## 核心角色与流程

系统以顺序式工作流组织四个专业化 AI 角色：

1. **Strategist（策略师）**：初次接入、内容分析与设计规范编制
2. **Executor（执行者）**（通用/咨询）：依据规范产出 SVG 代码
3. **Optimizer_CRAP（优化者）**：按 CRAP 设计原则进行视觉优化（可选）

### 关键流程规则

在任何内容分析之前，**必须先进行策略师的「初次沟通」阶段**：

- 页数范围确认：**基于内容量/复杂度给出建议页数区间**
- 目标受众与使用场景：**给出初步判断与定位**
- 设计风格选择：A）通用灵活 或 B）高端咨询 —— **给出推荐并说明理由**
- 输出画布格式：**根据使用场景推荐（PPT 16:9/4:3、小红书、朋友圈、Story、Banner、A4 等）**

策略师不仅要提出问题，更要基于来源文档分析，对以上确认点逐项给出专业建议与理由。

## 开发常用命令

### 项目管理

使用项目管理工具创建和管理项目：

```bash
# 初始化新项目
python3 tools/project_manager.py init <project_name> --format ppt169

# 验证项目结构
python3 tools/project_manager.py validate <project_path>

# 查看项目信息
python3 tools/project_manager.py info <project_path>
```

支持的画布格式：`ppt169`, `ppt43`, `wechat`, `xiaohongshu`, `moments`, `story`, `banner`, `a4`

### 预览生成的 SVG 幻灯片

仓库中的示例均以「项目为单位」组织在 `examples/` 目录下，每个示例项目包含 `svg_output/` 文件夹。

预览任一示例项目（以占位项目名为例）：

```bash
# 方式一：使用内置 HTTP 服务器（推荐）
python3 -m http.server --directory examples/<project_name>_<format>_<YYYYMMDD>/svg_output 8000

# 方式二：直接用浏览器打开单个 SVG
open examples/<project_name>_<format>_<YYYYMMDD>/svg_output/slide_01_cover.svg
```

在浏览器访问 `http://localhost:8000` 以查看该项目的 SVG 文件。

### SVG 质量检查

```bash
# 检查单个项目
python3 tools/svg_quality_checker.py examples/<project>

# 检查所有项目
python3 tools/svg_quality_checker.py --all examples

# 批量验证项目结构
python3 tools/batch_validate.py examples
```

### 校验 SVG 画布规范（多格式）

依据 `docs/canvas_formats.md` 所列格式，校验每个 SVG 的 `viewBox` 是否与目标画布一致：

```bash
# 粗检：所有文件都应包含 viewBox 并以 0 0 起始
grep -R "viewBox=\"0 0 " examples

# 常见格式精检（可按需扩展或改为 -E 合并正则）
grep -R "viewBox=\"0 0 1280 720\"" examples   # PPT 16:9
grep -R "viewBox=\"0 0 1024 768\"" examples    # PPT 4:3
grep -R "viewBox=\"0 0 1242 1660\"" examples   # 小红书 3:4
grep -R "viewBox=\"0 0 1080 1080\"" examples   # 朋友圈/Instagram 1:1
grep -R "viewBox=\"0 0 1080 1920\"" examples   # Story/竖版 9:16
grep -R "viewBox=\"0 0 900 383\"" examples     # 公众号头图 2.35:1
grep -R "viewBox=\"0 0 1920 1080\"" examples   # 横版 Banner 16:9
grep -R "viewBox=\"0 0 1240 1754\"" examples   # A4 打印 150dpi
```

说明：仓库中的历史示例项目可能使用了非标准尺寸用于特定实验目的；新项目建议严格遵循 `docs/canvas_formats.md`。

### 文本扁平化（去 tspan）

在生成阶段，Executor 应使用 `<tspan>` 进行手动换行（禁止 `<foreignObject>`）。如发布链路或后续处理对 `<tspan>` 不友好（如部分渲染器或需要文本抽取），可使用 `tools/flatten_tspan.py` 将 `<tspan>` 扁平成多行 `<text>`：

```bash
# 扁平化整个输出目录（默认输出到同级 svg_output_flattext）
python3 tools/flatten_tspan.py examples/<project_name>_<format>_<YYYYMMDD>/svg_output

# 指定输出目录
python3 tools/flatten_tspan.py examples/<project>/svg_output examples/<project>/svg_output_flattext

# 处理单个 SVG（输出文件路径可自定义）
python3 tools/flatten_tspan.py examples/<project>/svg_output/slide_01_cover.svg examples/<project>/svg_output_flattext/slide_01_cover.svg
```

注意：

- 生成阶段仍以 `<tspan>` 手动换行为准；`flatten_tspan` 是可选后处理工具。
- 工具会将每个 `<tspan>` 转换为独立的 `<text>`，尽量保留样式与定位；原有 `<foreignObject>` 仍然禁止。

### 可选：Markdown 语法检查

```bash
npx markdownlint "**/*.md"
```

建议在提交前于仓库根目录运行，以保持一致的文档格式。

## 关键技术约束

### SVG 生成规则（不可协商）

- **画布与 viewBox**：必须与所选格式一致（参见 `docs/canvas_formats.md`）；`width/height` 与 `viewBox` 成对一致
- **禁止 `<foreignObject>`**：生成阶段使用 `<tspan>` 手动换行；如需发布去除 `<tspan>`，请使用 `tools/flatten_tspan.py` 后处理输出到 `svg_output_flattext`
- **背景**：根节点使用 `<rect>` 元素
- **字体**：优先使用系统 UI 字体栈

### 通用灵活风格：卡片与布局基线

- 16:9（1280×720）：单行 530–600px；双行 265–295px
- 4:3（1024×768）：单行 460–530px；双行 220–255px
- 3:4（1242×1660）：高度 400–600px，间距 40–60px
- 9:16（1080×1920）：高度 400–800px，间距 60–80px
- 1:1（1080×1080）：核心区约 800×800px，避免拥挤

边距建议：

- 横屏（16:9/4:3/2.35:1）：40–80px
- 竖屏（3:4/9:16）：60–120px（Story 顶/底安全区更大）

### 风格化实施要点

**通用灵活风格**：

- 设计规范需给出精确的像素级度量
- 完成卡片高度的详细规划与校验
- 采用灵活布局与丰富色彩方案

**高端咨询风格**：

- 规范更精炼，聚焦内容结构
- 优先信息可视化（图表、KPI、矩阵、时间轴）
- 专业配色（Deloitte Blue #0076A8、McKinsey Blue #005587、BCG 深蓝 #003F6C）
- 强化留白与视觉呼吸感

## 文件组织

### 新增角色

- 在 `roles/{RoleName}.md` 新建角色定义
- 更新 `roles/README.md` 索引
- 如有流程变化，同步更新 `docs/workflow_tutorial.md`

### 创建示例项目

示例项目采用「单项目目录」结构并带日期后缀：

```
examples/
└── <project_name>_<format>_<YYYYMMDD>/
    ├── README.md                       # 项目说明（可选）
    ├── 设计规范与内容大纲.md / design_specification.md
    └── svg_output/                     # SVG 输出
        ├── slide_01_cover.svg
        ├── slide_02_xxx.svg
        └── ...
```

### 进行中的项目（WIP）

将实验性项目放置于 `projects/{project_name}_{YYYYMMDD}/`，包含：

- **文件夹命名**：必须追加当前日期，格式为 `_YYYYMMDD`（如 `_20251012`）
- 来源文档
- 设计规范（由策略师产出）
- SVG 输出文件夹
- 迭代记录 `logs/`

示例：`projects/company_report_20251012/`

## 设计质量核对清单

用于审阅或生成 SVG 幻灯片时：

1. **对齐（Alignment）**：所有元素沿不可见网格线对齐
2. **对比（Contrast）**：通过尺寸、粗细或颜色建立清晰层级
3. **重复（Repetition）**：相同元素保持一致的样式
4. **亲密性（Proximity）**：相关内容空间聚合，不相关内容适度分离
5. （可选）文本扁平化：如采用 `svg_output_flattext`，抽检确认无 `<tspan>` 残留，样式与坐标正确

## 常见任务

### 生成新演示/海报/社媒素材

1. 使用策略师处理来源文档
2. 完成初次沟通（四项确认：页数、受众/场景、风格、画布格式）
3. 审阅并确认设计规范
4. 由合适的执行者按序生成各页 SVG
5. 关键页面可选用优化者进行 CRAP 优化

### 修改已有角色定义

- 更新 `roles/` 下对应的角色 Markdown 文件
- 如工作流变化，更新 `docs/workflow_tutorial.md`
- 如设计规则变化，更新 `docs/design_guidelines.md`
- 在 `CHANGELOG.md` 记录变更

### 添加示例项目

- 在 `examples/` 下新建 `{项目名}_{格式}_{YYYYMMDD}` 目录
- 放入来源文档与设计规范（Markdown）
- 在 `svg_output/` 下存放导出的 SVG 文件
- 建议文件命名：`slide_0X_topic.svg`（优化后以 `yh_` 前缀）

## 测试方式

鉴于本项目以文档与流程为核心：

- **视觉测试**：浏览器打开 SVG，核对布局与稳定性
- **规范一致性**：对照 `docs/design_guidelines.md` 与 `docs/canvas_formats.md`
- **流程校验**：构造最小示例验证 Strategist → Executor → Optimizer 协作
- **颜色/字体校验**：确保与设计规范一致

## AI 代理重要提示

- 本项目定义 AI 角色协作机制与输出规范，而非可执行代码
- 需优先维持角色定义与产出的一致性
- 质量取决于对设计规范与画布格式的严格执行
- 策略师的「初次沟通」阶段是强制要求，非可选项
- **策略师必须对四项确认问题均给出专业化建议**（页数范围、受众/场景、风格选择、画布格式），且需基于来源文档分析
- 通用风格与咨询风格在规范格式上有本质区别
- CRAP 优化虽为可选，但对关键页面价值显著

## 图表模板库

为提高 SVG 图表生成的质量和一致性，项目提供了标准化的图表模板库，位于 `templates/charts/` 目录。

### 可用模板

- **KPI 卡片** (`kpi_cards.svg`)：关键业绩指标展示
- **柱状图** (`bar_chart.svg`)：类别数据对比
- **折线图** (`line_chart.svg`)：趋势分析
- **环形图** (`donut_chart.svg`)：占比分析
- **漏斗图** (`funnel_chart.svg`)：转化流程分析
- **矩阵图** (`matrix_2x2.svg`)：四象限分析
- **时间轴** (`timeline.svg`)：时序事件展示
- **流程图** (`process_flow.svg`)：业务流程展示

详细使用说明请参阅 `templates/charts/README.md`。

## 参考文档

- **快速开始**：README.md
- **工作流详解**：docs/workflow_tutorial.md
- **设计规范**：docs/design_guidelines.md
- **画布格式**：docs/canvas_formats.md
- **图表模板库**：templates/charts/（标准化图表模板，见 templates/charts/README.md）
- **速查表**：docs/quick_reference.md
- **质检清单**：docs/doc_qa_checklist.md
- **工具使用指南**：tools/README.md
- **角色定义**：roles/\*.md
- **示例索引**：examples/（项目化目录，见 examples/README.md）
