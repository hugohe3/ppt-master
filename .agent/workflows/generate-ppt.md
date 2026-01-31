---
description: 从 Markdown 源文档生成 PPT 的完整流程（主入口）
---

# PPT 生成工作流

> 📌 **这是 PPT Master 系统的主执行流程**。所有 PPT 生成任务都应从此工作流开始。

本工作流用于从 Markdown 源文档生成 PowerPoint 演示文稿。

**相关文档**：
- [AGENTS.md](../../AGENTS.md) — 规则手册（角色切换协议、技术约束、AI 提示）
- [roles/](../../roles/) — 各角色详细定义和知识库

---

## 工作流概览

```
源文档 → 创建项目 → 模板选项 → Strategist → [Image_Generator] → Executor → 后处理 → 导出
```

---

## 前置条件

- 用户已提供源文档（Markdown、PDF 或 URL）
- 如果是 PDF/URL，需先转换为 Markdown

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

> 💡 **需要创建新模板？** 请使用 `/create-template` 工作流单独创建模板，完成后再回到此流程选择 A。

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

## 阶段六：Image_Generator 角色（条件触发）

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

4. **生成图片**（三种方式）：

   **方式一：直接生成**（如支持 generate_image 工具）
   - 使用 `generate_image` 工具生成图片

   **方式二：用户自行生成**
   - 告知用户提示词文件位置
   - 推荐平台：Gemini、Midjourney、DALL-E 3、Stable Diffusion

   **方式三：Gemini 生成**（推荐高分辨率）
   - 下载 Full Size 版本
   - 去除水印：
     // turbo
     ```bash
     python3 tools/gemini_watermark_remover.py <图片路径>
     ```

5. **验证图片就绪**：确认所有图片已保存到 `images/` 目录

6. **阶段检查点**：
   ```markdown
   ## ✅ Image_Generator 阶段完成
   - [x] 已创建提示词文档 `images/image_prompts.md`
   - [x] 所有图片已保存到 images/ 目录
   - [ ] **下一步**: Executor_xxx
   ```

---

## 阶段七：Executor 角色

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

## 阶段八：后处理与导出（自动执行）

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

## 阶段九：Optimizer_CRAP（可选）

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
