# 用户项目工作区

此目录用于存放进行中的项目。

## 创建新项目

```bash
python tools/project_manager.py init my_project --format ppt169
```

## 目录结构

项目可以停留在“大纲已完成、尚未生成 SVG”的中间态。标准目录建议如下：

```
project_name_format_YYYYMMDD/
├── README.md
├── 设计规范与内容大纲.md
├── sources/
│   └── ...
├── templates/
│   └── ...
├── notes/
│   └── total.md
├── svg_output/
│   ├── 01_cover.svg
│   └── ...
├── svg_final/
│   └── ...
└── images/ (可选)
```

## 注意事项

- 此目录下的内容已被 `.gitignore` 排除
- 合法项目状态包括：仅完成大纲、已完成图片归集、已生成 SVG、已导出 PPTX
- 完成的项目可以移动到 `examples/` 目录分享
