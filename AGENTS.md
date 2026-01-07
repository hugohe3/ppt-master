# AGENTS.md

本文件为 AI 代理协作指引。详细文档请参阅 [README.md](./README.md)。

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统，通过四角色协作将来源文档转化为高质量输出。这是一个「文档与工作流框架」项目，此处的"代码"特指由 AI 代理生成的 SVG 标记。

## 角色与流程速查

| 角色 | 文件 | 职责 |
|------|------|------|
| **Strategist** | `roles/Strategist.md` | 初次沟通、内容分析、设计规范编制 |
| **Image_Generator** | `roles/Image_Generator.md` | AI 图片生成（条件触发） |
| **Executor_General** | `roles/Executor_General.md` | 通用灵活风格 SVG 生成 |
| **Executor_Consultant** | `roles/Executor_Consultant.md` | 一般咨询风格 SVG 生成 |
| **Executor_Consultant_Top** | `roles/Executor_Consultant_Top.md` | 顶级咨询风格 SVG 生成（MBB 级） |
| **Optimizer_CRAP** | `roles/Optimizer_CRAP.md` | CRAP 原则视觉优化（可选） |

### 工作流程

```
Strategist
    │
    ├─ 图片方式包含「C) AI 生成」?
    │       │
    │       YES → Image_Generator → 图片归集到 images/
    │       │
    │       NO ──────────────────────────────────────┐
    │                                                │
    ▼                                                ▼
Executor (General/Consultant/Consultant_Top) ← ← ← ┘
    │
    ▼
Optimizer_CRAP (可选)
```

> **注意**: Image_Generator 是串行环节，图片归集完成后才进入 Executor 阶段。

---

## 角色切换协议（强制执行）

### 1. 强制阅读角色定义

**在执行任何阶段之前，必须先使用 `view_file` 工具阅读对应的角色定义文件：**

| 阶段 | 必须阅读的文件 | 触发条件 |
|------|---------------|----------|
| 策略规划 | `roles/Strategist.md` | 用户提出新的PPT/内容生成需求 |
| 图片生成 | `roles/Image_Generator.md` | 图片方式包含「C) AI 生成」（如 C、B+C、C+D） |
| 通用风格执行 | `roles/Executor_General.md` | 用户选择「A) 通用灵活」设计风格 |
| 咨询风格执行 | `roles/Executor_Consultant.md` | 用户选择「B) 一般咨询」设计风格 |
| 顶级咨询执行 | `roles/Executor_Consultant_Top.md` | 用户选择「C) 顶级咨询」设计风格 |
| 视觉优化 | `roles/Optimizer_CRAP.md` | 用户要求优化或主动建议优化 |

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

- [x] 已完成八项确认（画布/页数/受众/风格/配色/图标/图片/字体）
- [x] 已生成《设计规范与内容大纲》
- [x] 已确定图片资源清单（如需要）
- [ ] **下一步**: [Image_Generator / Executor_xxx]
```

#### Image_Generator 阶段检查点

```markdown
## ✅ Image_Generator 阶段完成

- [x] 已阅读 `roles/Image_Generator.md`
- [x] 已为每张图片生成优化提示词
- [x] 所有图片已保存到 `images/` 目录
- [x] 已更新图片资源清单状态
- [ ] **下一步**: Executor_xxx
```

#### Executor 阶段检查点

```markdown
## ✅ Executor 阶段完成

- [x] 已阅读对应的 Executor 角色定义
- [x] 所有 SVG 页面已生成到 `svg_output/`
- [x] 已通过质量检查
- [ ] **下一步**: 运行后处理命令
```

---

## 关键规则（必须遵守）

### 1. 策略师初次沟通（强制）

在任何内容分析之前，**必须先完成八项确认**：

1. **画布格式** - 根据场景推荐（PPT/小红书/朋友圈等）
2. **页数范围** - 基于内容量给出建议
3. **目标受众与场景** - 给出初步判断
4. **设计风格** - A) 通用灵活 B) 一般咨询 C) 顶级咨询（MBB级），给出推荐理由
5. **配色方案** - 给出主导色、辅助色、强调色的 HEX 色值
6. **图标方式** - 四选一：A) Emoji B) AI生成 C) 内置图标库 D) 自定义路径
7. **图片使用** - 四选一：A) 不使用 B) 用户提供 C) AI生成 D) 占位符预留
8. **字体方案** - 根据内容特征推荐字体组合（标题/正文/强调）

**策略师必须主动给出专业建议，而非仅提问。**

### 2. SVG 技术约束（不可协商）

- **viewBox**: 必须与画布尺寸一致
- **禁止 `<foreignObject>`**: 使用 `<tspan>` 手动换行
- **背景**: 使用 `<rect>` 元素
- **字体**: 使用《设计规范与内容大纲》中指定的字体方案（见 `docs/design_guidelines.md` 字体选择章节）

### 3. PPT 兼容性规则（必须遵守）

为确保 SVG 导出到 PowerPoint 后效果一致，**必须遵守以下透明度规则**：

#### 禁止使用的写法

| ❌ 禁止 | ✅ 正确替代 |
|--------|-----------|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `stroke="rgba(0,0,0,0.5)"` | `stroke="#000000" stroke-opacity="0.5"` |
| `<g opacity="0.2">...</g>` | 每个子元素单独设置 `opacity` / `fill-opacity` / `stroke-opacity` |
| `<image ... opacity="0.3"/>` | 图片后添加遮罩层 `<rect fill="背景色" opacity="0.7"/>` |

#### 透明度正确写法示例

```xml
<!-- ✅ 填充透明度 -->
<rect fill="#FFFFFF" fill-opacity="0.15"/>

<!-- ✅ 描边透明度 -->
<circle stroke="#FFFFFF" stroke-width="1" stroke-opacity="0.1"/>

<!-- ✅ 整体透明度（简单元素可用） -->
<rect fill="#2E5A8B" opacity="0.15"/>

<!-- ❌ 禁止：组透明度 -->
<g opacity="0.1">
  <circle .../>
  <line .../>
</g>

<!-- ✅ 正确：每个元素单独设置 -->
<circle stroke="#FFF" stroke-opacity="0.1"/>
<line stroke="#FFF" stroke-opacity="0.1"/>
```

#### 图片透明度遮罩方案

```xml
<!-- 图片原始透明度 0.35 → 遮罩层 opacity 0.65 -->
<image href="bg.png" x="0" y="0" width="1280" height="720"/>
<rect x="0" y="0" width="1280" height="720" fill="#背景色" opacity="0.65"/>
```

> 📌 **记忆口诀**：PPT 不认 rgba、不认组透明、不认图片透明

### 4. 画布格式

| 格式 | 尺寸 | viewBox |
|------|------|---------|
| PPT 16:9 | 1280×720 | `0 0 1280 720` |
| PPT 4:3 | 1024×768 | `0 0 1024 768` |
| 小红书 | 1242×1660 | `0 0 1242 1660` |
| 朋友圈 | 1080×1080 | `0 0 1080 1080` |
| Story | 1080×1920 | `0 0 1080 1920` |
| 公众号头图 | 900×383 | `0 0 900 383` |

完整格式列表: [docs/canvas_formats.md](./docs/canvas_formats.md)

## 常用命令

```bash
# PDF 转 Markdown（优先使用，本地快速）
python3 tools/pdf_to_md.py <PDF文件>

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

# ⭐ 导出为 PPTX
python3 tools/svg_to_pptx.py <项目路径> -s final
```

### 项目目录结构

```
project/
├── svg_output/    # 原始版本（带占位符，作为模板参考）
├── svg_final/     # 最终版本（后处理完成）
├── images/        # 图片资源
└── *.pptx         # 导出的 PPT 文件
```

## 质量检查清单

生成 SVG 时确保：

- [ ] viewBox 与画布尺寸一致
- [ ] 无 `<foreignObject>` 元素
- [ ] 使用 `<tspan>` 手动换行
- [ ] 颜色符合设计规范
- [ ] **PPT 兼容**: 无 `rgba()`、无 `<g opacity>`、图片用遮罩层
- [ ] **对齐**: 元素沿网格线对齐
- [ ] **对比**: 建立清晰的视觉层级
- [ ] **重复**: 同类元素风格一致
- [ ] **亲密性**: 相关内容空间聚合

## PDF 转 Markdown 工具选择

| 场景 | 推荐工具 | 命令 |
|------|----------|------|
| **原生 PDF**（Word/LaTeX 导出） | `pdf_to_md.py` | `python3 tools/pdf_to_md.py <文件>` |
| **简单表格** | `pdf_to_md.py` | 同上 |
| **隐私敏感文档** | `pdf_to_md.py` | 同上（数据不出本机） |
| **扫描版/图片 PDF** | MinerU | 需要 OCR |
| **复杂多栏排版** | MinerU | 版面分析更准 |
| **数学公式** | MinerU | AI 识别能力强 |

> **策略**: PyMuPDF 优先，MinerU 兜底。先运行 `pdf_to_md.py`，如结果乱码/空白再换 MinerU。

## 重要资源

| 资源 | 路径 |
|------|------|
| 图表模板 | `templates/charts/` |
| **图标库** | `templates/icons/` (640+ 图标) |
| 设计指南 | `docs/design_guidelines.md` |
| **图片布局规范** | `docs/image_layout_spec.md` ⚠️ 强制执行 |
| 画布格式 | `docs/canvas_formats.md` |
| 图片嵌入 | `docs/svg_image_embedding.md` |
| 工作流教程 | `docs/workflow_tutorial.md` |
| 快速参考 | `docs/quick_reference.md` |
| 示例项目 | `examples/` |
| 工具说明 | `tools/README.md` |

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

- 策略师的「初次沟通」是**强制要求**
- 策略师必须对八项确认问题**均给出专业建议**
- 通用风格与咨询风格在规范格式上有本质区别
- 图标使用方式需在初次沟通中确认（Emoji / AI生成 / 内置库 / 自定义）
- 图片使用方式需在初次沟通中确认（不使用 / 用户提供 / AI生成 / 占位符）
- **图片生成流程**：如果图片方式**包含**「C) AI 生成」（如 C、B+C、C+D），**必须**先切换到 Image_Generator 角色，阅读角色定义，完成图片生成后再进入 Executor 阶段

### 后处理提示

SVG 生成完成后，**直接运行以下两条命令**，无需任何参数：

```bash
# 1. 后处理（直接运行）
python3 tools/finalize_svg.py <项目路径>

# 2. 导出 PPTX
python3 tools/svg_to_pptx.py <项目路径> -s final
```

> ⚠️ **注意**：不要添加 `--only` 等参数，直接运行即可完成全部处理。
