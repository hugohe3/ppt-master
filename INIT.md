# PPT Master - 项目初始化向导

欢迎使用 PPT Master，一个由 AI 驱动的**多格式 SVG 内容生成系统**。

本文件为您提供一个快速的项目概览和启动指南。

## 核心理念

本项目通过模拟一个设计团队的工作流程，使用四个专门的 AI 角色，将您的源文档转化为专业级的 SVG 内容。**支持演示文稿、社交媒体、营销海报等多种格式**。

### 四大核心角色

1. **策略师 (Strategist)**：负责内容分析、与您沟通确认需求，并制定详细的设计规范。**会主动提供专业建议**。
2. **通用执行师 (Executor_General)**：负责生成"通用灵活风格"的 SVG 内容。
3. **咨询执行师 (Executor_Consultant)**：负责生成"高端咨询风格"的 SVG 内容。
4. **优化师 (Optimizer_CRAP)**：(可选) 负责根据 CRAP 设计原则对生成的内容进行视觉优化。

### 支持的画布格式

- **演示文稿**：PPT 16:9 (1280×720)、PPT 4:3 (1024×768)
- **社交媒体**：小红书 (1242×1660)、朋友圈 (1080×1080)、Story (1080×1920)
- **营销物料**：公众号头图 (900×383)、横版/竖版海报、A4 打印

## 快速开始

### 方式一：使用项目管理工具（推荐）

```bash
# 1. 初始化新项目
python3 tools/project_manager.py init my_project --format ppt169

# 2. 编辑生成的设计规范文件
# projects/my_project_ppt169_YYYYMMDD/设计规范与内容大纲.md

# 3. 使用 AI 角色生成 SVG 文件到 svg_output/ 目录

# 4. 验证项目结构
python3 tools/project_manager.py validate projects/my_project_ppt169_YYYYMMDD
```

### 方式二：手动创建项目

1. **准备源文档**：在 `projects/` 目录下创建一个新的项目文件夹（格式：`projects/my_project_format_YYYYMMDD/`）

2. **与"策略师"对话**：
   - 使用 `roles/Strategist.md` 的内容作为对 AI 的指示
   - 策略师会就**页数、受众、风格、画布格式**提出专业建议并与您确认
   - 沟通确认后，生成一份详细的《设计规范与内容大纲》

3. **逐页生成内容**：
   - 根据您选择的风格，使用相应的执行师角色
   - 根据设计规范，让执行师逐页生成 SVG 代码

4. **(可选) 优化设计**：
   - 对于关键页面，使用 `roles/Optimizer_CRAP.md` 进一步提升视觉效果

## 重要文件和目录

| 目录/文件 | 说明 |
|----------|------|
| `README.md` | 项目最详细的说明文档 |
| `roles/` | 存放四个 AI 角色的详细定义和指示 |
| `examples/` | 包含 24+ 个示例项目，展示完整工作流程 |
| `docs/` | 包含设计指南、工作流教程、画布格式规范 |
| `tools/` | 实用工具（项目管理、质量检查、批量验证等） |
| `templates/charts/` | 标准化图表模板库（8 种常用图表） |

## 常用工具命令

```bash
# 项目管理
python3 tools/project_manager.py init <name> --format ppt169
python3 tools/project_manager.py validate <path>
python3 tools/project_manager.py info <path>

# SVG 质量检查
python3 tools/svg_quality_checker.py <path>

# 批量验证
python3 tools/batch_validate.py examples
```

---

现在，您可以开始了！建议从 `examples/` 目录下的示例开始，以了解完整的工作流程。
