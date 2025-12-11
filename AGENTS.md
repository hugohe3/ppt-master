# AGENTS.md

本文件为 AI 代理协作指引。详细文档请参阅 [README.md](./README.md)。

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统，通过四角色协作将来源文档转化为高质量输出。这是一个「文档与工作流框架」项目，此处的"代码"特指由 AI 代理生成的 SVG 标记。

## 角色与流程速查

| 角色 | 文件 | 职责 |
|------|------|------|
| **Strategist** | `roles/Strategist.md` | 初次沟通、内容分析、设计规范编制 |
| **Executor_General** | `roles/Executor_General.md` | 通用灵活风格 SVG 生成 |
| **Executor_Consultant** | `roles/Executor_Consultant.md` | 一般咨询风格 SVG 生成 |
| **Executor_Consultant_Top** | `roles/Executor_Consultant_Top.md` | 顶级咨询风格 SVG 生成（MBB 级） |
| **Optimizer_CRAP** | `roles/Optimizer_CRAP.md` | CRAP 原则视觉优化（可选） |

### 工作流程

```
Strategist → Executor (General/Consultant/Consultant_Top) → Optimizer_CRAP (可选)
```

## 关键规则（必须遵守）

### 1. 策略师初次沟通（强制）

在任何内容分析之前，**必须先完成七项确认**：

1. **画布格式** - 根据场景推荐（PPT/小红书/朋友圈等）
2. **页数范围** - 基于内容量给出建议
3. **目标受众与场景** - 给出初步判断
4. **设计风格** - A) 通用灵活 B) 一般咨询 C) 顶级咨询（MBB级），给出推荐理由
5. **配色方案** - 给出主导色、辅助色、强调色的 HEX 色值
6. **图标方式** - 四选一：A) Emoji B) AI生成 C) 内置图标库 D) 自定义路径
7. **图片使用** - 四选一：A) 不使用 B) 用户提供 C) AI生成 D) 占位符预留

**策略师必须主动给出专业建议，而非仅提问。**

### 2. SVG 技术约束（不可协商）

- **viewBox**: 必须与画布尺寸一致
- **禁止 `<foreignObject>`**: 使用 `<tspan>` 手动换行
- **背景**: 使用 `<rect>` 元素
- **字体**: 优先使用系统 UI 字体栈

### 3. 画布格式

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
# 初始化项目
python3 tools/project_manager.py init <名称> --format ppt169

# 验证项目
python3 tools/project_manager.py validate <路径>

# SVG 质量检查
python3 tools/svg_quality_checker.py <路径>

# ⭐ 最终化处理（一键完成：复制 + 嵌入图标）
python3 tools/finalize_svg.py <项目路径>

# 最终化处理 + 嵌入图片（转 Base64）
python3 tools/finalize_svg.py <项目路径> --embed-images

# 预览原始版本
python3 -m http.server --directory <路径>/svg_output 8000

# 预览最终版本
python3 -m http.server --directory <路径>/svg_final 8000
```

### 项目目录结构

```
project/
├── svg_output/    # 原始版本（带占位符，作为模板参考）
├── svg_final/     # 最终版本（嵌入图标/图片后）
└── images/        # 图片资源
```

## 质量检查清单

生成 SVG 时确保：

- [ ] viewBox 与画布尺寸一致
- [ ] 无 `<foreignObject>` 元素
- [ ] 使用 `<tspan>` 手动换行
- [ ] 颜色符合设计规范
- [ ] **对齐**: 元素沿网格线对齐
- [ ] **对比**: 建立清晰的视觉层级
- [ ] **重复**: 同类元素风格一致
- [ ] **亲密性**: 相关内容空间聚合

## 重要资源

| 资源 | 路径 |
|------|------|
| 图表模板 | `templates/charts/` |
| **图标库** | `templates/icons/` (640+ 图标) |
| 设计指南 | `docs/design_guidelines.md` |
| 画布格式 | `docs/canvas_formats.md` |
| 工作流教程 | `docs/workflow_tutorial.md` |
| 快速参考 | `docs/quick_reference.md` |
| 示例项目 | `examples/` |
| 工具说明 | `tools/README.md` |

## AI 代理重要提示

- 本项目定义 AI 角色协作机制，而非可执行代码
- 质量取决于对设计规范与画布格式的严格执行
- 策略师的「初次沟通」是**强制要求**
- 策略师必须对七项确认问题**均给出专业建议**
- 通用风格与咨询风格在规范格式上有本质区别
- 图标使用方式需在初次沟通中确认（Emoji / AI生成 / 内置库 / 自定义）
- 图片使用方式需在初次沟通中确认（不使用 / 用户提供 / AI生成 / 占位符）
- **SVG 生成不阻塞**：外部资源（AI 生成图片、用户提供图片）使用占位符或链接，生成完成后再处理
