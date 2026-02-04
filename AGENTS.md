# AGENTS.md — PPT Master 完整指南

> ⚠️ **AI 代理注意**：本文件是 PPT 生成流程的完整指南，包含工作流程和规则手册。
>
> 执行 `/generate-ppt` 前必须阅读本文件。

---

## 📚 目录导航

| 部分 | 内容 |
|------|------|
| [工作流程](#工作流程) | 从源文档到 PPT 的完整执行步骤 |
| [规则手册](#规则手册) | 约束边界、技术规范、角色切换协议 |
| [常用命令](#常用命令) | 工具命令快速参考 |
| [重要资源](#重要资源) | 模板、图标、文档链接 |

---

# 工作流程

> 📌 **这是 PPT Master 系统的主执行流程**。所有 PPT 生成任务都应从此工作流开始。

## 工作流概览

```
源文档 → 创建项目 → 模板选项 → Strategist → [Image_Generator] → Executor → 后处理 → 导出
```

---

## ⚠️ 阶段零：强制前置检查（不可跳过）

**在执行任何步骤之前，必须完成以下检查：**

### 检查项 1：确认已理解核心规则

- [ ] 角色切换协议（切换角色前必须阅读角色定义文件）
- [ ] SVG 技术约束（禁用功能黑名单、PPT 兼容性规则）
- [ ] 源内容自动处理（PDF/URL 必须立即转换）

**确认完成后，输出以下标记：**

```markdown
## ✅ 阶段零检查完成
- [x] 已阅读 AGENTS.md
- [x] 已理解核心规则
- [ ] 开始执行阶段一
```

---

## 阶段一：源内容处理（如需要）

当用户提供 PDF 或 URL 时，**必须立即调用对应工具**：

| 用户提供内容 | 必须调用的工具 | 命令 |
|--------------|----------------|------|
| **PDF 文件** | `pdf_to_md.py` | `python3 tools/pdf_to_md.py <文件路径>` |
| **网页链接** | `web_to_md.py` | `python3 tools/web_to_md.py <URL>` |
| **微信/高防站** | `web_to_md.cjs` | `node tools/web_to_md.cjs <URL>` |
| **Markdown** | - | 直接 `view_file` 读取 |

---

## 阶段二：创建项目文件夹

> ⚠️ **第一步！** 用户输入内容后必须立即创建

// turbo
```bash
python3 tools/project_manager.py init <项目名称> --format <格式>
```

格式选项：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等

---

## 阶段三：模板选项确认

> ⚠️ **必须在策略师开始之前确认**，策略师需根据模板选项调整设计方案

向用户询问模板选项（二选一）：

### A) 使用已有模板

**情况 1：模板在 repo 内**（如 `templates/layouts/` 下）

检查模板目录内容，按类型分别复制：
// turbo
```bash
# 复制模板文件（.svg, .md）到 templates/
cp templates/layouts/<模板名>/*.svg <项目路径>/templates/
cp templates/layouts/<模板名>/design_spec.md <项目路径>/templates/

# 复制图片资源（.png, .jpg 等）到 images/
# 注意：图片直接在模板目录下，不是在 images/ 子目录
cp templates/layouts/<模板名>/*.png <项目路径>/images/ 2>/dev/null || true
cp templates/layouts/<模板名>/*.jpg <项目路径>/images/ 2>/dev/null || true
cp templates/layouts/<模板名>/*.jpeg <项目路径>/images/ 2>/dev/null || true
```

**情况 2：模板在 repo 外**（用户自备/其他项目）

告知用户按以下规则手动复制：

| 文件类型 | 目标目录 | 示例 |
|----------|----------|------|
| 模板 SVG 文件 | `<项目路径>/templates/` | `01_cover.svg`, `02_toc.svg` |
| 设计规范文件 | `<项目路径>/templates/` | `design_spec.md` |
| 图片资源 | `<项目路径>/images/` | `cover_bg.png`, `logo.svg` |

等待用户确认文件已复制就绪后再继续。

**模板内容检查**：
```
<项目路径>/
├── templates/                # 模板文件
│   ├── design_spec.md        # 设计规范（必须）
│   ├── 01_cover.svg          # 封面模板
│   ├── 02_toc.svg            # 目录模板
│   ├── 03_chapter.svg        # 章节页模板
│   ├── 04_content.svg        # 内容页模板
│   └── 05_ending.svg         # 结尾页模板
└── images/                   # 图片资源（如有）
    ├── cover_bg.png
    └── ...
```

> 📌 策略师需参考模板的配色、布局、风格进行设计

### B) 不使用模板

→ 自由生成，策略师完全自主设计



---

## 阶段四：Strategist 角色（必须，不可跳过）

1. **阅读角色定义**：
   ```
   view_file: roles/Strategist.md
   ```

2. **完成八项确认**（强制要求）：
   - 画布格式、页数范围、目标受众、风格目标
   - 配色方案、图标使用、图片使用、排版方案

3. **如果用户提供了图片**，运行图片分析：
   // turbo
   ```bash
   python3 tools/analyze_images.py <项目路径>/images
   ```

4. **生成《设计规范与内容大纲》**：
   - 参考模板：`templates/design_spec_reference.md`
   - 保存到：`<项目路径>/设计规范与内容大纲.md`

5. **阶段检查点**：
   ```markdown
   ## ✅ Strategist 阶段完成
   - [x] 已完成八项确认
   - [x] 已生成《设计规范与内容大纲》
   - [x] 设计规范已保存到项目文件夹
   - [ ] **下一步**: [Image_Generator / Executor_xxx]
   ```

---

## 阶段五：Image_Generator 角色（条件触发）

> **触发条件**：图片方式包含「C) AI 生成」（如 C、B+C、C+D）

1. **阅读角色定义**：
   ```
   view_file: roles/Image_Generator.md
   ```

2. **分析图片资源清单**：
   - 从《设计规范与内容大纲》中提取所有「状态=待生成」的图片
   - 判断每张图片的类型（背景图/实景照片/插画/图表/装饰图案）

3. **生成提示词文档**（必须保存为文件）：
   - 保存到 `<项目路径>/images/image_prompts.md`
   - 格式：主体描述 + 风格指令 + 色彩指令 + 构图指令 + 负面提示词 + Alt Text

4. **生成图片**（四种方式）：

   **方式一：命令行工具** ⭐ 推荐
   - 使用 `nano_banana_gen.py` 调用 Gemini API 生成图片
   - 支持 4K 分辨率、自定义宽高比、负面提示词
   - 需先配置环境变量 `GEMINI_API_KEY`
     // turbo
     ```bash
     python3 tools/nano_banana_gen.py "现代科技感背景" --aspect_ratio 16:9 --image_size 4K -o <项目路径>/images
     ```
   - 详细用法参见 `tools/README.md` 和 `roles/Image_Generator.md`

   **方式二：直接生成**（如支持 generate_image 工具）
   - 使用 `generate_image` 工具生成图片

   **方式三：Gemini 网页版**
   - 在 [Gemini](https://gemini.google.com/) 中生成后选择 **Download full size** 下载
   - 去除水印：
     // turbo
     ```bash
     python3 tools/gemini_watermark_remover.py <图片路径>
     ```

   **方式四：手动生成**
   - 告知用户提示词文件位置 `images/image_prompts.md`
   - 推荐平台：Midjourney、DALL-E 3、Stable Diffusion

5. **验证图片就绪**：确认所有图片已保存到 `images/` 目录

6. **阶段检查点**：
   ```markdown
   ## ✅ Image_Generator 阶段完成
   - [x] 已创建提示词文档 `images/image_prompts.md`
   - [x] 所有图片已保存到 images/ 目录
   - [ ] **下一步**: Executor_xxx
   ```

---

## 阶段六：Executor 角色

1. **阅读角色定义**（根据风格选择）：
   ```
   view_file: roles/Executor_General.md        # 通用灵活风格
   view_file: roles/Executor_Consultant.md     # 一般咨询风格
   view_file: roles/Executor_Consultant_Top.md # 顶级咨询风格
   ```

2. **【视觉构建阶段】**：
   - 批量生成 SVG 页面
   - 保存到 `<项目路径>/svg_output/`

3. **【逻辑构建阶段】**（必须）：
   - 生成完整演讲备注文稿
   - 保存到 `<项目路径>/notes/total.md`

4. **阶段检查点**：
   ```markdown
   ## ✅ Executor 阶段完成
   ### 视觉构建阶段
   - [x] 所有 SVG 页面已生成到 svg_output/
   
   ### 逻辑构建阶段
   - [x] 已生成完整演讲备注 notes/total.md
   ```

---

## 阶段七：后处理与导出（自动执行）

> ⚠️ **必须按顺序执行以下三个命令，不可省略或替换！**

### 步骤 1：拆分演讲备注
// turbo
```bash
python3 tools/total_md_split.py <项目路径>
```

### 步骤 2：SVG 后处理
// turbo
```bash
python3 tools/finalize_svg.py <项目路径>
```

**此步骤执行以下处理**：
- 嵌入图标（将占位符替换为实际图标代码）
- 智能裁剪图片
- 修复图片宽高比
- 嵌入图片（Base64 编码，避免外部引用）
- 文本扁平化
- 圆角矩形转 Path（提高 PPT 兼容性）

> ❌ **禁止**：使用 `cp` 命令替代此步骤！

### 步骤 3：导出 PPTX
// turbo
```bash
python3 tools/svg_to_pptx.py <项目路径> -s final
```

- `-s final` 参数指定从 `svg_final/` 目录读取
- 默认会嵌入演讲备注

---

## 阶段八：Optimizer_CRAP（可选）

> **触发条件**：用户要求优化 或 质量不足时主动建议

1. **阅读角色定义**：
   ```
   view_file: roles/Optimizer_CRAP.md
   ```

2. **执行 CRAP 原则优化**

3. **重新执行后处理与导出**（如有修改）

---

## 完成检查清单

- [ ] 源内容已转换为 Markdown
- [ ] 项目文件夹已创建
- [ ] 模板选项已确认
- [ ] 八项确认已完成
- [ ] 设计规范已保存
- [ ] 图片已就绪（如需要）
- [ ] SVG 文件已生成到 `svg_output/`
- [ ] 演讲备注已生成 `notes/total.md`
- [ ] 后处理已执行（`finalize_svg.py`）
- [ ] SVG 文件已复制到 `svg_final/`
- [ ] PPTX 已导出

---

## 常见错误提醒

| 错误 | 正确做法 |
|------|----------|
| 用 `cp` 复制 SVG 到 svg_final | 使用 `finalize_svg.py` |
| 直接从 `svg_output` 导出 | 使用 `-s final` 从 `svg_final` 导出 |
| 忘记拆分备注 | 先运行 `total_md_split.py` |
| 忘记后处理 | 先运行 `finalize_svg.py` |
| 跳过 Strategist 八项确认 | 必须完成，无论模板选项如何 |
| 模板选项后才创建项目 | 先创建项目，再询问模板选项 |

---

# 规则手册

> 以下是 PPT Master 系统的约束边界和技术规范，执行工作流时必须遵守。

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

### 3. 画布格式

| 格式       | 尺寸      | viewBox         |
| ---------- | --------- | --------------- |
| PPT 16:9   | 1280×720  | `0 0 1280 720`  |
| PPT 4:3    | 1024×768  | `0 0 1024 768`  |
| 小红书     | 1242×1660 | `0 0 1242 1660` |
| 朋友圈     | 1080×1080 | `0 0 1080 1080` |
| Story      | 1080×1920 | `0 0 1080 1920` |
| 公众号头图 | 900×383   | `0 0 900 383`   |

完整格式列表: [docs/canvas_formats.md](./docs/canvas_formats.md)

---

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

---

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

---

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

---

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

---

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
