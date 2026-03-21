# 用户项目工作区

此目录用于存放进行中的项目。

## 创建新项目

```bash
python3 skills/ppt-master/scripts/project_manager.py init my_project --format ppt169
```

## 目录结构

一个典型项目通常包含以下内容：

```
project_name_format_YYYYMMDD/
├── README.md
├── 设计规范与内容大纲.md
├── sources/
│   ├── 原始文件 / URL 归档 / 转换后的 Markdown
│   └── *_files/                  # Markdown 配套资源目录（如图片）
├── images/                       # 项目使用的图片资源
├── notes/
│   ├── 01_xxx.md
│   ├── 02_xxx.md
│   └── total.md
├── svg_output/
│   ├── 01_xxx.svg
│   └── ...
├── svg_final/
│   ├── 01_xxx.svg
│   └── ...
├── templates/                    # 项目级模板（如有）
├── *.pptx
└── image_analysis.csv            # 可选，图片扫描分析结果
```

项目可以停留在不同阶段，不一定一次性具备全部产物。例如：

- 仅完成 `sources/` 归档和《设计规范与内容大纲》
- 已生成 `svg_output/`，但尚未执行后处理
- 已完成 `svg_final/`、`notes/` 和 `*.pptx`

## 注意事项

- 此目录下的内容已被 `.gitignore` 排除
- 完成的项目可以移动到 `examples/` 目录分享
- 工作空间外文件默认复制；工作空间内文件会直接移动到项目 `sources/`
