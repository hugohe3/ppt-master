# AGENTS.md — 规则手册（必读）

> ⚠️ **AI 代理注意**：本文件是 PPT Master 系统的**规则总纲**，执行任何工作流之前必须先阅读本文件。
>
> 如果你是通过 `/generate-ppt` 或 `/create-template` 进入的，请确认已阅读本文件后再继续。

---

## 🚀 快速入口

| 任务 | 工作流 |
|------|--------|
| **生成 PPT** | [/generate-ppt](.agent/workflows/generate-ppt.md) |

> 📋 **执行顺序**：阅读本文件 → 阅读工作流 → 开始执行

---

## 三层架构导航

| 层级 | 文档 | 职责 |
|------|------|------|
| **流程** | [generate-ppt.md](.agent/workflows/generate-ppt.md) | "做什么"（步骤顺序） |
| **角色** | [roles/README.md](roles/README.md) | "谁来做"（专业能力） |
| **规则** | 本文件 | "怎么做"（约束边界） |

---

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统，通过多角色协作将来源文档转化为高质量输出。

---

## 角色切换协议（强制执行）

### 1. 强制阅读角色定义

**在执行任何阶段之前，必须先使用 `view_file` 工具阅读对应的角色定义文件：**

| 阶段         | 必须阅读的文件                     | 触发条件                                     |
| ------------ | ---------------------------------- | -------------------------------------------- |
| 策略规划     | `roles/Strategist.md`              | 用户提出新的 PPT/内容生成需求                |
| 模板设计     | `roles/Template_Designer.md`       | 使用 `/create-template` 工作流时触发（独立流程） |
| 图片生成     | `roles/Image_Generator.md`         | 图片方式包含「C) AI 生成」（如 C、B+C、C+D） |
| 通用风格执行 | `roles/Executor_General.md`        | 用户选择「A) 通用灵活」设计风格              |
| 咨询风格执行 | `roles/Executor_Consultant.md`     | 用户选择「B) 一般咨询」设计风格              |
| 顶级咨询执行 | `roles/Executor_Consultant_Top.md` | 用户选择「C) 顶级咨询」设计风格              |
| 视觉优化     | `roles/Optimizer_CRAP.md`          | 用户要求优化或主动建议优化                   |

> ⚠️ **禁止跳过**：不得在未阅读角色定义文件的情况下直接执行该角色的任务。

### 2. 显式角色切换标记

切换角色时，**必须输出以下格式的标记**：

```markdown
---
## 【角色切换：[角色名称]】

📖 **阅读角色定义**: `roles/[角色文件名].md`
📋 **当前任务**: [简述本阶段要完成的任务]
---
```

**示例**：

```markdown
---
## 【角色切换：Image_Generator】

📖 **阅读角色定义**: `roles/Image_Generator.md`
📋 **当前任务**: 为5张待生成图片创建优化提示词并生成图片
---
```

### 3. 阶段检查点

每个阶段完成后，**必须输出检查清单确认**：

#### Strategist 阶段检查点

```markdown
## ✅ Strategist 阶段完成

- [x] 已完成八项确认（画布/页数/受众/风格/配色/图标/图片/排版）
- [x] 已生成《设计规范与内容大纲》
- [x] 设计规范已保存到项目文件夹
- [x] 已确定图片资源清单（如需要）
- [ ] **下一步**: [Image_Generator / Executor_xxx]
```

#### Image_Generator 阶段检查点

```markdown
## ✅ Image_Generator 阶段完成

- [x] 已阅读 `roles/Image_Generator.md`
- [x] 已创建提示词文档 `images/image_prompts.md`
- [x] 每张图片都有：类型判断 + 优化提示词 + 负面提示词 + Alt Text
- [x] 所有图片已保存到 `images/` 目录（或已告知用户自行生成）
- [x] 已更新图片资源清单状态
- [ ] **下一步**: Executor_xxx
```

#### Executor 阶段检查点

```markdown
## ✅ Executor 阶段完成

### 视觉构建阶段
- [x] 已阅读对应的 Executor 角色定义
- [x] 所有 SVG 页面已生成到 `svg_output/`
- [x] 已通过质量检查

### 逻辑构建阶段（必须）
- [x] 已生成完整演讲备注文稿 `notes/total.md`

### 自动执行后处理（默认由 AI 执行，必要时可手动运行）

# 1. 拆分讲稿（将 total.md 拆分为各页独立文件）
python3 tools/total_md_split.py <项目路径>

# 2. 后处理（修正图片路径、嵌入图标）
python3 tools/finalize_svg.py <项目路径>

# 3. 导出为 PPTX（默认嵌入演讲备注）
python3 tools/svg_to_pptx.py <项目路径> -s final
```

> ⚠️ **强制要求**：演讲备注是 Executor 阶段的必须产出，SVG 页面生成完毕后必须进入「逻辑构建阶段」生成 `notes/total.md`，然后再进行后处理。
> ⚠️ **优化提示**：仅在完整初版产出后考虑 Optimizer；若优化过，请重新运行后处理与导出以保持产物一致。

---
## 源内容自动处理（强制触发）

> 📖 **详细工作流程**：参见 `.agent/workflows/generate-ppt.md`

### 强制规则

当用户提供 PDF 文件或网页链接时，**必须立即调用工具转换**：

| 源内容 | 工具 | 命令 |
|--------|------|------|
| PDF | `pdf_to_md.py` | `python3 tools/pdf_to_md.py <文件>` |
| 网页 | `web_to_md.py` | `python3 tools/web_to_md.py <URL>` |
| 微信/高防 | `web_to_md.cjs` | `node tools/web_to_md.cjs <URL>` |

**禁止行为**：
- ❌ 识别到 PDF/URL 后仅询问"是否需要转换"
- ❌ 等待用户明确说"请转换"才处理

**正确行为**：
- ✅ 识别到 PDF/URL 后立即调用工具
- ✅ 转换完成后创建项目 → 询问模板选项（A 使用 / B 不使用） → 进入策略师

---

## 关键规则（必须遵守）

### 1. 策略师初次沟通（强制）

在任何内容分析之前，**必须先完成八项确认**：

1. **画布格式** - 根据场景推荐（PPT/小红书/朋友圈等）
2. **页数范围** - 基于内容量给出建议
3. **目标受众与场景** - 给出初步判断
4. **设计风格** - A) 通用灵活 B) 一般咨询 C) 顶级咨询（MBB 级），给出推荐理由
5. **配色方案** - 给出主导色、辅助色、强调色的 HEX 色值
6. **图标方式** - 四选一：A) Emoji B) AI 生成 C) 内置图标库 D) 自定义路径
7. **图片使用** - 四选一：A) 不使用 B) 用户提供 C) AI 生成 D) 占位符预留
8. **排版方案** - 字体组合（P1-P5 预设或自定义）+ 正文字号基准（18-24px）

**策略师必须主动给出专业建议，而非仅提问。**

**若图片方案包含「B) 用户提供」**：八项确认完成后、进入内容分析与大纲编制之前，必须运行 `python3 tools/analyze_images.py <项目路径>/images`，并在输出《设计规范与内容大纲》前填充图片资源清单。

### 2. SVG 技术约束（不可协商）

> ⚠️ **详细规则**：各 Executor 角色文件中包含完整的代码示例和检查清单

**基础规则**：
- **viewBox**: 必须与画布尺寸一致
- **背景**: 使用 `<rect>` 元素
- **字体**: 使用系统字体（见规范中的字体方案）
- **换行**: 使用 `<tspan>` 手动换行

**禁用功能黑名单**（记忆口诀：PPT 只认基础形状 + 内联样式 + 系统字体）：

`clipPath` | `mask` | `<style>` | `class/id` | 外部 CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>`

**PPT 兼容性**（记忆口诀：不认 rgba、不认组透明、不认图片透明、不认 marker）：

| ❌ 禁止 | ✅ 替代方案 |
|--------|-------------|
| `rgba()` 颜色 | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` 组透明 | 每个子元素单独设置 |
| `<image opacity>` | 遮罩层叠加 |
| `marker-end` 箭头 | `<polygon>` 三角形 |

> 📖 **详细代码示例**：参见 `roles/Executor_*.md` 对应章节

### 4. 画布格式

| 格式       | 尺寸      | viewBox         |
| ---------- | --------- | --------------- |
| PPT 16:9   | 1280×720  | `0 0 1280 720`  |
| PPT 4:3    | 1024×768  | `0 0 1024 768`  |
| 小红书     | 1242×1660 | `0 0 1242 1660` |
| 朋友圈     | 1080×1080 | `0 0 1080 1080` |
| Story      | 1080×1920 | `0 0 1080 1920` |
| 公众号头图 | 900×383   | `0 0 900 383`   |

完整格式列表: [docs/canvas_formats.md](./docs/canvas_formats.md)

## 常用命令

```bash
# PDF 转 Markdown（优先使用，本地快速）
python3 tools/pdf_to_md.py <PDF文件>

# 网页转 Markdown（抓取网页内容并保存图片）
python3 tools/web_to_md.py <URL> 或 node tools/web_to_md.cjs <URL>

# 初始化项目
python3 tools/project_manager.py init <名称> --format ppt169

# 验证项目
python3 tools/project_manager.py validate <路径>

# SVG 质量检查
python3 tools/svg_quality_checker.py <路径>

# ⭐ 后处理（直接运行，无需参数）
python3 tools/finalize_svg.py <项目路径>

# 预览原始版本
python3 -m http.server -d <路径>/svg_output 8000

# 预览最终版本
python3 -m http.server -d <路径>/svg_final 8000

# ⭐ 导出为 PPTX（默认嵌入演讲备注）
python3 tools/svg_to_pptx.py <项目路径> -s final

# 导出 PPTX 但不嵌入备注
python3 tools/svg_to_pptx.py <项目路径> -s final --no-notes

# ⭐ 拆分讲稿文件（将 total.md 拆分为多个讲稿文件）
python3 tools/total_md_split.py <项目路径>
```

### 项目目录结构

```
project/
├── svg_output/    # 原始版本（带占位符，作为模板参考）
│   ├── 01_封面.svg
│   ├── 02_目录.svg
│   └── ...
├── svg_final/     # 最终版本（后处理完成）
├── images/        # 图片资源
├── notes/         # 演讲备注（Markdown 格式，与 SVG 同名）
│   ├── 01_封面.md
│   ├── 02_目录.md
│   └── ...
└── *.pptx         # 导出的 PPT 文件
```

## 质量检查清单

生成 SVG 时确保：

- [ ] viewBox 与画布尺寸一致
- [ ] 使用 `<tspan>` 手动换行
- [ ] 颜色符合设计规范
- [ ] **黑名单检查**: 无 `clipPath` / `mask` / `<style>` / `class` / `id` / 外部 CSS / `<foreignObject>` / `<symbol>+<use>` / `textPath` / `@font-face` / `animate*` / `set` / `script` / `on*` / `marker` / `marker-end` / `iframe`
- [ ] **PPT 兼容**: 无 `rgba()`、无 `<g opacity>`、图片用遮罩层、仅内联样式
- [ ] **对齐**: 元素沿网格线对齐
- [ ] **对比**: 建立清晰的视觉层级
- [ ] **重复**: 同类元素风格一致
- [ ] **亲密性**: 相关内容空间聚合

## 源文档转换工具选择

### PDF 转 Markdown

| 场景                            | 推荐工具       | 命令                                |
| ------------------------------- | -------------- | ----------------------------------- |
| **原生 PDF**（Word/LaTeX 导出） | `pdf_to_md.py` | `python3 tools/pdf_to_md.py <文件>` |
| **简单表格**                    | `pdf_to_md.py` | 同上                                |
| **隐私敏感文档**                | `pdf_to_md.py` | 同上（数据不出本机）                |
| **扫描版/图片 PDF**             | MinerU         | 需要 OCR                            |
| **复杂多栏排版**                | MinerU         | 版面分析更准                        |
| **数学公式**                    | MinerU         | AI 识别能力强                       |

> **策略**: PyMuPDF 优先，MinerU 兜底。先运行 `pdf_to_md.py`，如结果乱码/空白再换 MinerU。

### 网页转 Markdown

| 场景                         | 推荐工具        | 命令                                                   |
| ---------------------------- | --------------- | ------------------------------------------------------ |
| **微信公众号/高防站点**      | `web_to_md.cjs` | `node tools/web_to_md.cjs <URL>` (绕过 TLS 拦截，推荐) |
| **普通文章/新闻网页**        | `web_to_md.py`  | `python3 tools/web_to_md.py <URL>`                     |
| **图文内容**（游记、攻略等） | `web_to_md.py`  | 同上（自动下载图片到 `_files/`）                       |
| **政府/机构网站**            | `web_to_md.py`  | 同上（支持中文站点元数据提取）                         |
| **批量处理多个 URL**         | `web_to_md.py`  | `python3 tools/web_to_md.py -f urls.txt`               |
| **需要登录的页面**           | 手动处理        | 浏览器登录后复制内容                                   |
| **动态渲染页面（SPA）**      | 手动处理        | 需要 headless browser                                  |

> **策略**: 静态网页用 `web_to_md.py`，动态渲染或需登录的页面需手动处理。

## 重要资源

| 资源             | 路径                                    |
| ---------------- | --------------------------------------- |
| 图表模板         | `templates/charts/`                     |
| **图标库**       | `templates/icons/` (640+ 图标)          |
| 设计指南         | `docs/design_guidelines.md`             |
| **图片布局规范** | `docs/image_layout_spec.md` ⚠️ 强制执行 |
| 画布格式         | `docs/canvas_formats.md`                |
| 图片嵌入         | `docs/svg_image_embedding.md`           |
| 工作流教程       | `docs/workflow_tutorial.md`             |
| 快速参考         | `docs/quick_reference.md`               |
| 示例项目         | `examples/`                             |
| 工具说明         | `tools/README.md`                       |

## AI 代理重要提示

### 核心原则

- 本项目定义 AI 角色协作机制，而非可执行代码
- 质量取决于对设计规范与画布格式的严格执行
- **角色切换协议是强制要求，不可跳过**

### 角色切换强制规则

> ⚠️ **严重警告**：以下规则必须严格遵守，违反将导致流程混乱和质量问题。

1. **切换角色前必须阅读角色定义文件**
   - 使用 `view_file` 工具阅读 `roles/[角色名].md`
   - 不得在未阅读的情况下直接执行任务

2. **必须输出显式角色切换标记**
   - 格式：`## 【角色切换：[角色名称]】`
   - 包含阅读的文件和当前任务说明

3. **每个阶段结束必须输出检查点**
   - 确认已完成的任务项
   - 明确下一步操作

### 流程要点

- **项目文件夹必须在源材料转换完成后立即创建**
- **创建项目后立即询问模板选项**（A 使用已有 / B 不使用）— 这是流程步骤，非策略师职责
- **模板选项必须在策略师开始之前确认完成**，策略师需根据模板选项调整设计方案
- 如用户选择 A（使用已有模板），需**分别复制**：图片资源拷贝到项目 `images/` 目录，其他文件（SVG、design_spec 等）拷贝到项目 `templates/` 目录（来源：用户自备/其他项目/示例库等）
- 如需创建新模板，请使用 `/create-template` 工作流（独立流程）
- **策略师的「八项确认」是强制要求，无论模板选项如何都不可跳过**
- 策略师必须对八项确认问题**均给出专业建议**
- 如选择 A（使用已有模板），策略师需参考模板的配色、布局、风格进行设计
- 通用风格与咨询风格在规范格式上有本质区别
- 图标使用方式需在八项确认中确认（Emoji / AI 生成 / 内置库 / 自定义）
- 图片使用方式需在八项确认中确认（不使用 / 用户提供 / AI 生成 / 占位符）
- 若图片方案包含「B) 用户提供」，策略师在八项确认后、内容分析前必须运行 `python3 tools/analyze_images.py <项目路径>/images` 并填充图片资源清单
- **图片生成流程**：如果图片方式**包含**「C) AI 生成」（如 C、B+C、C+D），**必须**先切换到 Image_Generator 角色，阅读角色定义，完成图片生成后再进入 Executor 阶段
- **Executor 两阶段**：SVG 页面生成（视觉构建）完成后，**必须**进入逻辑构建阶段生成演讲备注 `notes/total.md`，**禁止**跳过此步骤直接进入后处理

### 后处理提示

**演讲备注和 SVG 都生成完成后**，运行以下命令：

```bash
# 1. 拆分讲稿（将 total.md 拆分为各页独立文件）
python3 tools/total_md_split.py <项目路径>

# 2. 后处理（修正图片路径、嵌入图标）
python3 tools/finalize_svg.py <项目路径>

# 3. 导出 PPTX
python3 tools/svg_to_pptx.py <项目路径> -s final
```

> ⚠️ **注意**：不要添加 `--only` 等参数，直接运行即可完成全部处理。
