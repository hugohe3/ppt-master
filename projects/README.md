# 用户项目工作区

此目录用于存放进行中的项目。

## 创建新项目

```bash
python tools/project_manager.py init my_project --format ppt169
```

## 目录结构

完成后的项目应包含：

```
project_name_format_YYYYMMDD/
├── README.md
├── 设计规范与内容大纲.md
├── svg_output/
│   ├── slide_01_cover.svg
│   └── ...
└── images/ (可选)
```

## 注意事项

- 此目录下的内容已被 `.gitignore` 排除
- 完成的项目可以移动到 `examples/` 目录分享
- 生成的svg格式可用`tools/check_svg.py`检验是否符合格式规范
- 生成用于浏览svg格式ppt的`index.html`中的静态文件，如字体、css、JS应存于本地，避免调用在线资源，可参考`tools/assets`文件夹，以便用户离线浏览
- 必要时可以通过`tools/svg_to_pptx_image.py`帮助用户将项目转换为pptx格式