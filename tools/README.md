# Tools

## flatten_tspan.py — 文本扁平化（去 `<tspan>`）

用途：将含有多行 `<tspan>` 的 `<text>` 结构扁平化为多条独立的 `<text>` 元素，便于部分渲染器兼容或文本抽取；生成端仍应使用 `<tspan>` 手动换行（禁止 `<foreignObject>`）。

用法：

```bash
# 扁平化整个输出目录（默认输出到同级 svg_output_flattext）
python3 tools/flatten_tspan.py examples/<project_name>_<format>_<YYYYMMDD>/svg_output

# 指定输出目录
python3 tools/flatten_tspan.py examples/<project>/svg_output examples/<project>/svg_output_flattext

# 处理单个 SVG（自定义输出路径）
python3 tools/flatten_tspan.py path/to/input.svg path/to/output.svg
```

行为说明：
- 逐个 `<tspan>` 计算绝对位置（综合 `x`/`y` 与 `dx`/`dy`），合并父/子样式，输出为独立 `<text>`；
- 复制父 `<text>` 的通用文本属性和 `style`，子级覆盖优先；
- 保留或合并 `transform`；
- 输出采用 UTF‑8 编码，无 XML 声明，保持与仓库示例风格一致。

建议校验：
- 目标目录为 `svg_output_flattext`，不应含 `<tspan>`；
- 抽检字号、字重、颜色、对齐和坐标是否与原文件一致；
- 若发现偏差，优先在生成端修正 `<tspan>` 的 `x`/`dy` 或父 `<text>` 的样式后重跑。

已知限制：
- 仅处理 `<text>`/`<tspan>` 结构；其他子元素不做转换；
- 复杂嵌套或特殊布局请先在生成端简化为规范的逐行 `<tspan>`。

