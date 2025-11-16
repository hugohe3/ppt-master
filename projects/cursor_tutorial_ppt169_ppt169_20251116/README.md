# Cursor IDE 使用指南

## 项目概述

本项目是一套关于 Cursor IDE 使用的完整教程演示文稿，采用高端咨询风格设计。通过 10 页精心设计的幻灯片，系统介绍 Cursor 的核心功能、使用技巧和最佳实践。

## 项目信息

- **项目名称**：Cursor IDE 使用指南
- **画布格式**：PPT 16:9 (1280×720)
- **设计风格**：高端咨询风格
- **总页数**：10 页
- **创建日期**：2025-11-16

## 内容结构

### Slide 01 - 封面
科技蓝渐变背景，突出 AI-Powered 特性。

### Slide 02 - 什么是 Cursor
左右分栏布局，介绍 Cursor 定义、核心特点和三大优势（效率提升 3x、零门槛、$20/月）。

### Slide 03 - 核心功能概览
四象限布局展示 4 大核心功能：
- AI Chat (Cmd + L)
- AI Edit (Cmd + K)
- AI Composer (Cmd + I)
- Codebase Context (@Codebase)

### Slide 04 - AI Chat 功能详解
介绍 AI Chat 的使用场景、操作步骤和实战示例。

### Slide 05 - AI Edit 功能详解
展示 Inline Editing 的典型用例和 Before/After 代码对比示例。

### Slide 06 - Composer 功能详解
流程图展示多文件编辑的完整工作流程，包含文件清单和关键数据。

### Slide 07 - Context Controls 高级技巧
详细列出 7 种 @ 符号用法和 4 条最佳实践。

### Slide 08 - 效率对比数据
柱状图对比传统 IDE vs Cursor 在三个维度的表现，底部展示关键指标 KPI 卡片。

### Slide 09 - 快速上手指南
三栏布局展示：安装配置、快捷键必记、学习资源。

### Slide 10 - 总结与建议
三个黄金原则（明确表达、迭代优化、保持思考）+ 行动号召。

## 设计特点

### 色彩规范
- 主蓝色：`#0066FF`（Cursor 品牌色）
- 深蓝色：`#1A237E`（标题）
- 紫色：`#6366F1`（AI 功能强调）
- 绿色：`#10B981`（成功指标）

### 视觉风格
- **专业性**：高端咨询风格，强调数据驱动
- **简洁克制**：充足留白，突出核心信息
- **信息可视化**：大量使用卡片、图表、流程图
- **CRAP 原则**：对比、重复、对齐、亲密性

### 技术规范
- ✅ 所有文本使用 `<text>` + `<tspan>` 手动换行
- ✅ 背景使用 `<rect>` 元素
- ✅ viewBox 统一为 `0 0 1280 720`
- ❌ 禁止使用 `<foreignObject>`

## 适用场景

- 团队技术分享会
- 新员工 Onboarding 培训
- 开发者能力提升课程
- AI 工具推广演示

## 使用方法

### 预览幻灯片

```bash
# 在浏览器中打开预览页面
open preview.html

# 或使用 HTTP 服务器
python3 -m http.server --directory svg_output 8000
# 访问 http://localhost:8000
```

### 导出为其他格式

SVG 文件可以通过以下方式转换：
- 使用 Inkscape 批量导出为 PNG
- 使用在线工具转换为 PDF
- 直接在浏览器中打印为 PDF

## 文件清单

```
cursor_tutorial_ppt169_ppt169_20251116/
├── README.md                              # 本文件
├── 设计规范与内容大纲.md                   # 完整设计规范
├── preview.html                           # 预览页面
└── svg_output/                            # SVG 输出目录
    ├── slide_01_cover.svg
    ├── slide_02_what_is_cursor.svg
    ├── slide_03_core_features.svg
    ├── slide_04_ai_chat.svg
    ├── slide_05_ai_edit.svg
    ├── slide_06_composer.svg
    ├── slide_07_context_controls.svg
    ├── slide_08_productivity_comparison.svg
    ├── slide_09_getting_started.svg
    └── slide_10_conclusion.svg
```

## 质量检查

- [x] 所有页面 viewBox 为 `0 0 1280 720`
- [x] 色彩符合专业科技风格
- [x] 字体使用系统 UI 字体栈
- [x] 无 `<foreignObject>` 元素
- [x] CRAP 原则体现到位
- [x] 快捷键标注准确
- [x] 视觉层级清晰
- [x] 留白适度专业

## 关键数据

本教程通过数据展示 Cursor 的价值：
- **编码速度提升**：+3x
- **Bug 率降低**：-40%
- **开发者满意度**：95%
- **时间节省**：70%（使用 Composer）
- **成本投入**：$20/月

## 后续优化建议

1. 可选择关键页面进行 CRAP 优化
2. 如需发布，可使用 `flatten_tspan.py` 扁平化文本
3. 根据实际演讲场景调整内容详略
4. 添加实际项目案例截图

## 技术支持

本项目基于 PPT Master 框架生成：
- 框架文档：`/docs/workflow_tutorial.md`
- 设计规范：`/docs/design_guidelines.md`
- 角色定义：`/roles/`

---

_本项目由 PPT Master 系统生成，遵循高端咨询风格标准_
