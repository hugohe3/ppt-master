# 示例项目索引

本目录收录了多个示例项目，展示 PPT Master 在不同场景与画布格式下的实际产出。每个示例为一个独立文件夹，命名规则：`<project_name>_<format>_<YYYYMMDD>`。

## 如何预览

- 直接用浏览器打开该项目 `svg_output/` 下的任意 SVG 文件；或
- 启动本地服务器预览：

```
python3 -m http.server --directory examples/<project_name>_<format>_<YYYYMMDD>/svg_output 8000
# 然后访问 http://localhost:8000
```

某些示例项目提供 `preview.html`，可直接在浏览器打开该文件进行快速预览。

## 当前示例列表（节选）

- 重庆观音桥写字楼资产减值分析_PPT_20251011（PPT 16:9，11 页）
- 医疗器械注册调研报告_PPT_20251012（PPT 16:9，9 页）
- 重庆汇丰尽职调查_PPT_20251015（PPT 16:9，8 页）
- 科技型软件企业资质知识产权规划_PPT_20251015（PPT 16:9，11 页）
- 明朝那些事儿-1-朱元璋_PPT_20251010（PPT 16:9，12 页）
- 写给大家看的设计书_wechat_20251015（社媒图文，9 张）
- vscode_12_git_wechat_20251015（社媒图文，8 张）

说明：历史示例可能包含实验性尺寸；新项目请优先遵循 `docs/canvas_formats.md`。

