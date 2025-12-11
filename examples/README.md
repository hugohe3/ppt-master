# PPT Master 示例项目

## 📂 目录说明

此目录包含使用 PPT Master 生成的示例项目。

## 🎴 精选示例

### demo_project_intro_ppt169_20251211

> **PPT Master 项目介绍** - 完整的 10 页演示文稿

| 属性 | 内容 |
|------|------|
| **画布格式** | PPT 16:9 (1280×720) |
| **设计风格** | 清新科技风格 (Modern Tech) |
| **页数** | 10 页 |
| **配色方案** | 靛蓝紫渐变 (#6366F1 → #06B6D4) |

**包含页面**:
1. 封面
2. 痛点与挑战
3. 解决方案
4. 系统架构
5. 四大角色
6. 核心特性
7. 支持格式
8. 工具生态
9. 快速开始
10. 行动号召

📁 [查看项目](./demo_project_intro_ppt169_20251211/) · 📄 [设计规范](./demo_project_intro_ppt169_20251211/设计规范与内容大纲.md)

---

## 📁 项目结构

每个示例项目应采用以下结构：

```
<project_name>_<format>_<YYYYMMDD>/
├── 设计规范与内容大纲.md               # 设计规范文档
├── images/                            # 图片资源
├── svg_output/                        # 原始 SVG（带占位符）
│   ├── slide_01_cover.svg
│   └── ...
└── svg_final/                         # 最终 SVG（嵌入图标/图片）
    ├── slide_01_cover.svg
    └── ...
```

## 📖 使用说明

### 预览项目

**方法 1: 使用 HTTP 服务器（推荐）**

```bash
python -m http.server --directory examples/<project_name>/svg_final 8000
# 访问 http://localhost:8000
```

**方法 2: 直接打开 SVG**

```bash
# macOS
open examples/<project_name>/svg_final/slide_01_cover.svg

# Windows
start examples/<project_name>/svg_final/slide_01_cover.svg
```

## 🤝 贡献示例

欢迎分享你的项目！请确保：

1. 遵循标准项目结构
2. 包含完整的设计规范文档
3. SVG 文件符合技术规范（使用 `python tools/svg_quality_checker.py` 检查）
4. 不包含敏感信息

### 贡献步骤

1. Fork 本仓库
2. 在 `examples/` 目录下创建项目文件夹
3. 提交 Pull Request

## 📚 相关资源

- [快速开始](../README.md)
- [工作流教程](../docs/workflow_tutorial.md)
- [设计规范](../docs/design_guidelines.md)
- [图表模板](../templates/charts/)
