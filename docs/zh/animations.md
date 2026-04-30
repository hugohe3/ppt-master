# 页间转场与页内元素动画

PPT Master 导出的 PPTX 同时支持**页间转场**（page transition）与**页内元素入场动画**（per-element entrance animation）。两者都通过 `svg_to_pptx.py` 的 CLI 参数控制，输出为真正的 OOXML 动画——在 PowerPoint 和 Keynote 中原生播放，不是嵌入视频。

## 默认行为

| 层级 | 默认 | 原因 |
|---|---|---|
| 页间转场 | `fade`，0.4 秒 | 适合大多数 deck 的中性基线 |
| 页内元素动画 | `mixed` 效果 + `after-previous` 触发 | 进入页面后元素自动按顺序级联入场，零交互即可看到完整动画过程，最能体现 deck 的动画能力 |

修改设置只需对同一份 `svg_output/`（或 `svg_final/`）重跑 `svg_to_pptx.py`，无需重新跑 LLM。如要彻底关闭页内动画，加 `-a none`。

## 页间转场

```bash
# 换效果
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push --transition-duration 0.6

# 关闭转场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none

# 每 5 秒自动翻页（展厅 / 自动循环）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5
```

可选效果：`fade`、`push`、`wipe`、`split`、`strips`、`cover`、`random`。

参数：

- `-t/--transition` — 效果名，或 `none` 禁用。默认 `fade`。
- `--transition-duration` — 秒数，默认 `0.4`。
- `--auto-advance` — 秒数；不写则由演示者手动翻页。

## 页内元素动画

默认开启（`mixed` 效果 + `after-previous` 触发）。共有三种 Start 模式，**与 PowerPoint 动画窗格的 Start 下拉菜单一一对应**：

- **`on-click`**（单击时）—— 进入页面 → 第一次点击显示第一个语义组，后续每次点击按 z-order 显示下一个组。适合现场演讲，演讲者控制节奏。
- **`with-previous`**（与上一动画同时）—— 所有组在进入页面时一起入场，并行播放各自的入场动画。`--animation-stagger` 不生效。
- **`after-previous`**（默认，在上一动画之后）—— 第一组进入页面时入场，后续组在前一个结束后接着出现，并按 `--animation-stagger` 增加额外间隔。适合展厅循环、录屏走查，或者只是想看流动效果不想点击。

```bash
# 默认即开启：mixed 效果 + after-previous 触发，无需任何参数
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>

# 关闭页内动画
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a none

# 改用单一效果（仍走默认的 after-previous 自动级联）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# 改为单击触发（演讲者控制节奏）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation-trigger on-click

# 自定义节奏
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed \
        --animation-stagger 0.6 --animation-duration 0.5

# 所有组进入页面时同时入场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation-trigger with-previous
```

22 种单一效果：`appear`、`fade`、`fly`、`cut`、`zoom`、`wipe`、`split`、`blinds`、`checkerboard`、`dissolve`、`random_bars`、`peek`、`wheel`、`box`、`circle`、`diamond`、`plus`、`strips`、`wedge`、`stretch`、`expand`、`swivel`。再加两种自动轮换模式：

- `mixed` — 确定性轮换。每页第一个动画组使用 `fade`，后续组在整份 deck 范围内按精选效果池连续轮换。
- `random` — 在同一效果池中随机抽取。

效果池排除了 `appear`，因为它没有可见动画过程。

参数：

- `-a/--animation` — 效果名、`mixed`、`random` 或 `none`。默认 `mixed`。
- `--animation-trigger` — Start 模式（与 PowerPoint 一致）：`on-click`、`with-previous`、`after-previous`（默认）。
- `--animation-duration` — 单个元素入场秒数，默认 `0.3`。
- `--animation-stagger` — `after-previous` 模式下两组之间的额外间隔（秒，默认 `0.4`）。其他模式忽略。

## 锚点机制 — 顶层 `<g id="...">`

页内动画锚定在 SVG 的**顶层 `<g id="...">` 内容组**上（如 `<g id="cover-title">`、`<g id="card-1">`），一个组对应一次点击入场。

每页建议 **3–8 个内容组**。这同时也是 PowerPoint 框选 / 整体移动的颗粒度，与是否启用动画无关，都能改善编辑体验。

**装饰类分组自动跳过。** 顶层中看起来属于页面装饰的组（背景、页头页脚、装饰元素、水印、页码）会被排除在点击序列外，跟随页面立即显示。识别基于 `id`：按 `-` 和 `_` 切分后，若任一 token 命中 `background` / `bg` / `decoration` / `decorations` / `decor` / `header` / `footer` / `chrome` / `watermark` / `pagenumber` / `pagenum`，则视为装饰类。会自动跳过的例子：`<g id="background">`、`<g id="bg-texture">`、`<g id="cover-footer">`、`<g id="p03-header">`、`<g id="bottom-decor">`、`<g id="watermark">`。仍会动画的例子：`<g id="card-1">`、`<g id="cover-title">`、`<g id="step-discover">`。**不要为了规避动画去掉 `<g>` 包裹**——保留分组（PowerPoint 框选需要），只要给个合适的 id 即可。

**扁平 SVG 的回退逻辑**（顶层没有 `<g>`，只有裸 `<rect>` / `<text>` / `<path>`）：

- 顶层可见图元 ≤ 8 → 每个图元作为一个锚点（设上限以避免密集页面出现 70+ 次点击）。
- 顶层可见图元 > 8 → 该页跳过页内动画。页面照常显示，只是不带入场。

无论是否打算开启动画，Executor 都应该把逻辑分块包进 `<g id>`。`skills/ppt-master/references/shared-standards.md` 已将这一点列为强制要求。

## 限制

- **仅原生形状模式生效。** 页内动画需要可编辑形状作为锚点。`--only legacy` 模式每页一张大图，没有元素粒度，因此不响应 `-a/--animation`，只受 `-t/--transition` 影响。
- **不同 Office 版本对元素动画存在轻微差异。** 实现走 `<p:animEffect filter=...>` 路径（而非 `presetID` 查找表），在 PowerPoint 2016+ 上表现一致；更老的 Office 可能把部分效果降级为 Appear。
- **兼容模式的 PNG fallback 只用于显示。** 转场与动画都在 slide XML 里，不在 PNG 中；关掉兼容模式不影响两个动画层。

## 常用速查

| 目标 | 命令 |
|---|---|
| 关闭转场 | `-t none` |
| 切换转场效果 | `-t push`（或上文列表中任一） |
| 转场放慢 | `--transition-duration 0.8` |
| 自动播放 | `--auto-advance 5` |
| 关闭页内动画 | `-a none` |
| 改为单击触发 | `--animation-trigger on-click` |
| 切换为单一效果 | `--animation fade` |
| 所有组同时入场 | `--animation-trigger with-previous` |
| 元素入场放慢 | `--animation-duration 0.5` |
| after-previous 拉大间隔 | `--animation-stagger 0.8` |

完整 `svg_to_pptx.py` 参考：[`scripts/docs/svg-pipeline.md`](../../skills/ppt-master/scripts/docs/svg-pipeline.md)。
