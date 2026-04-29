# 页间转场与页内元素动画

PPT Master 导出的 PPTX 同时支持**页间转场**（page transition）与**页内元素入场动画**（per-element entrance animation）。两者都通过 `svg_to_pptx.py` 的 CLI 参数控制，输出为真正的 OOXML 动画——在 PowerPoint 和 Keynote 中原生播放，不是嵌入视频。

## 默认行为

| 层级 | 默认 | 原因 |
|---|---|---|
| 页间转场 | `fade`，0.4 秒 | 适合大多数 deck 的中性基线 |
| 页内元素动画 | 关闭 | 老用户更新后行为不变 |

修改设置只需对同一份 `svg_output/`（或 `svg_final/`）重跑 `svg_to_pptx.py`，无需重新跑 LLM。

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

默认关闭。开启后：进入页面 → 第一次点击显示第一个语义组，后续每次点击按 z-order 显示下一个组。

```bash
# 全部用 fade 入场（推荐起点）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# 同页自动轮换效果（首组 fade，后续组在精选效果池中轮换）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed

# 让每次入场放慢到 0.5 秒
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade --animation-duration 0.5
```

22 种单一效果：`appear`、`fade`、`fly`、`cut`、`zoom`、`wipe`、`split`、`blinds`、`checkerboard`、`dissolve`、`random_bars`、`peek`、`wheel`、`box`、`circle`、`diamond`、`plus`、`strips`、`wedge`、`stretch`、`expand`、`swivel`。再加两种自动轮换模式：

- `mixed` — 确定性轮换。每页第一个动画组使用 `fade`，后续组在整份 deck 范围内按精选效果池连续轮换。
- `random` — 在同一效果池中随机抽取。

效果池排除了 `appear`，因为它没有可见动画过程。

参数：

- `-a/--animation` — 效果名、`mixed`、`random` 或 `none`。默认 `none`。
- `--animation-duration` — 单个元素入场秒数，默认 `0.3`。
- `--animation-stagger` — 仅保留兼容旧命令；当前逐次点击入场逻辑会忽略它。

## 锚点机制 — 顶层 `<g id="...">`

页内动画锚定在 SVG 的**顶层 `<g id="...">` 组**上（如 `<g id="cover-title">`、`<g id="card-1">`），一个组对应一次点击入场。

每页建议 **3–8 个语义组**。这同时也是 PowerPoint 框选 / 整体移动的颗粒度，与是否启用动画无关，都能改善编辑体验。

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
| 启用元素动画 | `--animation fade` |
| 元素动画自动轮换 | `--animation mixed` |
| 元素入场放慢 | `--animation-duration 0.5` |

完整 `svg_to_pptx.py` 参考：[`scripts/docs/svg-pipeline.md`](../../skills/ppt-master/scripts/docs/svg-pipeline.md)。
