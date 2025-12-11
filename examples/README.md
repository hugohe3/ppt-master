# PPT Master 示例项目

## 📂 目录说明

此目录用于存放示例项目。目前为空模板，欢迎贡献你的项目案例！

## 📁 项目结构

每个示例项目应采用以下结构：

```
<project_name>_<format>_<YYYYMMDD>/
├── README.md                          # 项目说明
├── 设计规范与内容大纲.md               # 或 design_specification.md
├── preview.html                       # 预览页面（可选）
└── svg_output/
    ├── slide_01_cover.svg
    ├── slide_02_xxx.svg
    └── ...
```

## 📖 使用说明

### 预览项目

**方法 1: 使用 HTTP 服务器（推荐）**

```bash
python -m http.server --directory examples/<project_name>/svg_output 8000
# 访问 http://localhost:8000
```

**方法 2: 直接打开 SVG**

```bash
# macOS
open examples/<project_name>/svg_output/slide_01_cover.svg

# Windows
start examples/<project_name>/svg_output/slide_01_cover.svg
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
