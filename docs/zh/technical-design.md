# 技术路线

[English](../technical-design.md) | [中文](./technical-design.md)

---

## 设计哲学 —— AI 是你的设计师，不是完工师

生成的 PPTX 是一份**设计稿**，而非成品。把它理解成建筑师的效果图：AI 负责视觉设计、排版布局和内容结构，交付给你一个高质量的起点。要想获得真正精良的成品，**需要你自己在 PowerPoint 里做精装修**：换掉形状、细化图表、调整配色、把占位图形替换成原生对象。这个工具的目标是消除 90% 的从零开始的工作量，而不是替代人在最后一公里的判断。不要指望 AI 一遍搞定所有——好的演示文稿从来不是这样做出来的。

**工具的上限是你的上限。** PPT Master 放大的是你已有的能力——你有设计感和内容判断力，它帮你快速落地；你不知道一个好的演示文稿应该长什么样，它也没法替你知道。输出的质量，归根结底是你自身品味与判断力的映射。

---

## 系统架构

```
用户输入 (PDF/DOCX/XLSX/URL/Markdown)
    ↓
[源内容转换] → source_to_md/pdf_to_md.py / doc_to_md.py / excel_to_md.py / ppt_to_md.py / web_to_md.py
    ↓
[创建项目] → project_manager.py init <项目名> --format <格式>
    ↓
[模板处理（可选）] — 默认跳过，直接自由设计
    用户主动点名模板时：复制模板文件到项目目录
    需要新建全局模板：使用 /create-template 工作流单独完成
    ↓
[Strategist] 策略师 - 八项确认与设计规范 → design_spec.md + spec_lock.md
    ↓
[Image_Generator] 图片生成师（当选择 AI 生图时）
    ↓
[Executor] 执行师
    ├── 视觉构建：连续生成所有 SVG 页面 → svg_output/
    ├── [Quality Check] svg_quality_checker.py（强制通过，0 错误）
    └── 讲稿生成：完整讲稿 → notes/total.md
    ↓
[图表校准（可选）] → verify-charts 工作流（含数据图表的幻灯片在此步骤校准坐标）
    ↓
[后处理] → total_md_split.py（拆分讲稿）→ finalize_svg.py → svg_to_pptx.py
    ↓
输出：
    exports/
    └── presentation_<timestamp>.pptx          ← 原生形状版（DrawingML）— 推荐用于编辑与交付
    backup/<timestamp>/
    ├── presentation_svg.pptx                  ← SVG 快照版 — 像素级视觉参考备份
    └── svg_output/                            ← Executor 原始 SVG 备份（重跑 finalize_svg → svg_to_pptx 即可重建 pptx）
```

---

## 技术流程

**核心流程：AI 生成 SVG → 后处理转换为 DrawingML（PPTX）。**

整个流程分为三个阶段：

**第一阶段：内容理解与设计规划**
源文档（PDF/DOCX/URL/Markdown）经过转换变为结构化文本，由 Strategist 角色完成内容分析、页面规划和设计风格确认，输出完整的设计规格。

**第二阶段：AI 视觉生成**
Executor 角色逐页生成演示文稿的视觉内容，输出为 SVG 文件。这个阶段的产物是**设计稿**，而非成品。

**第三阶段：工程化转换**
后处理脚本将 SVG 转换为 DrawingML，每一个形状都变成真正的 PowerPoint 原生对象——可点击、可编辑、可改色，而不是嵌入的图片。

---

## 为什么是 SVG？

SVG 是这套流程的核心枢纽。这个选择是通过逐一排除其他方案得出的。

**直接生成 DrawingML** 看起来最直接——跳过中间格式，AI 直接输出 PowerPoint 的底层 XML。但 DrawingML 极其繁琐，一个简单的圆角矩形就需要数十行嵌套 XML，AI 的训练数据中远少于 SVG，生成质量不稳定，调试几乎无法肉眼完成。

**HTML/CSS** 是 AI 最熟悉的格式之一，但 HTML 和 PowerPoint 有根本不同的世界观。HTML 描述的是**文档**——标题、段落、列表，元素的位置由内容流动决定。PowerPoint 描述的是**画布**——每个元素都是独立的、绝对定位的对象，没有流，没有上下文关系。这不只是排版计算的问题，而是两种完全不同的内容组织方式之间的鸿沟。就算解决了浏览器排版引擎的问题（Chromium 用数百万行代码做这件事），HTML 里的一个 `<table>` 也没法自然地变成 PPT 里的几个独立形状。

**WMF/EMF**（Windows 图元文件）是微软自家的原生矢量图形格式，与 DrawingML 有直接的血缘关系——理论上转换损耗最小。但 AI 对它几乎没有训练数据，这条路死在起点。值得注意的是：连微软自家的格式在这里都输给了 SVG。

**SVG 作为嵌入图片** 是最简单的路线——把整张幻灯片渲染成图片塞进 PPT。但这样完全丧失可编辑性，形状变成像素，文字无法选中，颜色无法修改，和截图没有本质区别。

SVG 胜出，因为它与 DrawingML 拥有相同的世界观：两者都是绝对坐标的二维矢量图形格式，共享同一套概念体系：

| SVG | DrawingML |
|---|---|
| `<path d="...">` | `<a:custGeom>` |
| `<rect rx="...">` | `<a:prstGeom prst="roundRect">` |
| `<circle>` / `<ellipse>` | `<a:prstGeom prst="ellipse">` |
| `transform="translate/scale/rotate"` | `<a:xfrm>` |
| `linearGradient` / `radialGradient` | `<a:gradFill>` |
| `fill-opacity` / `stroke-opacity` | `<a:alpha>` |

转换不是格式错配，而是两种方言之间的精确翻译。

SVG 也是唯一同时满足流程中所有角色需要的格式：**AI 能可靠地生成它，人能在任意浏览器里直接预览和调试，脚本能精确地转换它**——在生成任何 DrawingML 之前，设计稿就已经完全透明可见。
