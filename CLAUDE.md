# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统。通过多角色协作（Strategist → Image_Generator → Executor → Optimizer），将源文档（PDF/URL/Markdown）转化为高质量 SVG 页面，并导出为 PPTX。

**核心流程**：`源文档 → 创建项目 → 模板选项 → Strategist八项确认 → [Image_Generator] → Executor → 后处理 → 导出PPTX`

**完整工作流和规则手册**：执行 PPT 生成任务前，必须阅读 [AGENTS.md](./AGENTS.md)。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 源内容转换
python3 tools/pdf_to_md.py <PDF文件>
python3 tools/web_to_md.py <URL>
node tools/web_to_md.cjs <URL>          # 微信/高防站点

# 项目管理
python3 tools/project_manager.py init <项目名> --format ppt169
python3 tools/project_manager.py validate <项目路径>

# 图片工具
python3 tools/analyze_images.py <项目路径>/images
python3 tools/nano_banana_gen.py "提示词" --aspect_ratio 16:9 --image_size 4K -o <项目路径>/images

# SVG 质量检查
python3 tools/svg_quality_checker.py <项目路径>

# 后处理三步（必须按顺序执行）
python3 tools/total_md_split.py <项目路径>       # 1. 拆分讲稿
python3 tools/finalize_svg.py <项目路径>          # 2. SVG后处理（嵌入图标/图片/文本扁平化等）
python3 tools/svg_to_pptx.py <项目路径> -s final  # 3. 导出PPTX（默认嵌入演讲备注）

# 本地预览
python3 -m http.server -d <项目路径>/svg_final 8000
```

## 架构与关键目录

- `roles/` — 7个 AI 角色定义文件（Strategist、Image_Generator、Executor_General/Consultant/Consultant_Top、Optimizer_CRAP、Template_Designer）
- `tools/` — 28个 Python 工具脚本，每个独立可调用。核心入口：`finalize_svg.py`（后处理统一入口）、`svg_to_pptx.py`（PPTX导出）、`project_manager.py`（项目管理）
- `templates/layouts/` — 页面布局模板（General、Consultant、Consultant_Top 等多种风格）
- `templates/charts/` — 13种标准化图表 SVG 模板
- `templates/icons/` — 640+ 矢量图标库
- `docs/` — 设计指南、画布格式规范、图片布局规范等技术文档
- `examples/` — 15个完整示例项目（229页 SVG）
- `projects/` — 用户项目工作区（gitignored）

**项目目录结构**（每个生成的项目）：
```
project/
├── svg_output/    # 原始SVG（带占位符）
├── svg_final/     # 后处理完成的最终SVG
├── images/        # 图片资源
├── notes/         # 演讲备注（与SVG同名的.md文件）
├── templates/     # 项目使用的模板（如有）
└── *.pptx         # 导出的PPT文件
```

## SVG 技术约束（不可协商）

生成 SVG 时必须遵守以下规则，否则 PPT 兼容性会出问题：

**禁用功能黑名单**：`clipPath` | `mask` | `<style>` | `class/id` | 外部 CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>` | `<symbol>+<use>`

**PPT 兼容性替代方案**：

| 禁止 | 替代 |
|------|------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | 每个子元素单独设置 opacity |
| `<image opacity>` | 遮罩层叠加 |
| `marker-end` 箭头 | `<polygon>` 三角形 |

**基础规则**：viewBox 必须与画布尺寸一致、用 `<rect>` 做背景、用 `<tspan>` 手动换行、仅使用系统字体和内联样式。

## 画布格式速查

| 格式 | viewBox |
|------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| 小红书 | `0 0 1242 1660` |
| 朋友圈 | `0 0 1080 1080` |
| Story | `0 0 1080 1920` |

完整列表：`docs/canvas_formats.md`

## 角色切换协议

切换角色前**必须先阅读**对应的角色定义文件（`roles/*.md`），禁止跳过。切换时输出标记：

```markdown
## 【角色切换：[角色名称]】
📖 阅读角色定义: roles/[角色文件名].md
📋 当前任务: [简述]
```

每个阶段完成后必须输出检查点确认清单。详见 AGENTS.md 中的完整协议。

## 后处理注意事项

- **禁止**用 `cp` 命令替代 `finalize_svg.py`，该工具执行图标嵌入、图片裁剪/嵌入、文本扁平化、圆角矩形转Path等处理
- **禁止**从 `svg_output/` 直接导出，必须从 `svg_final/`（`-s final`）导出
- 后处理三步命令不要添加 `--only` 等额外参数，直接运行即可
- 如果执行了 Optimizer 优化，需重新运行后处理与导出
