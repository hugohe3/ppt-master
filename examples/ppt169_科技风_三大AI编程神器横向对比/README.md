# ai_tools_comparison

## 项目信息

- **创建日期**: 2025-12-02
- **画布格式**: PPT 16:9 (1280×720)
- **设计风格**: 通用灵活
- **状态**: 进行中

## 项目说明

[在此添加项目描述]

## 内容概览

[在此添加内容概览]

## 使用说明

### 预览 SVG 文件

方式一：使用本地服务器
```bash
python3 -m http.server --directory svg_output 8000
# 访问 http://localhost:8000
```

方式二：直接打开单个 SVG
```bash
open svg_output/slide_01_cover.svg
```

## 文件说明

- `设计规范与内容大纲.md` - 设计规范和内容结构
- `来源文档.md` - 原始内容文档（可选）
- `svg_output/` - SVG 输出文件

## 技术规范

- viewBox: `0 0 1280 720`
- 禁止使用 `<foreignObject>`
- 文本换行使用 `<tspan>`
- 字体: 系统 UI 字体栈

---

*基于 PPT Master 框架生成*
