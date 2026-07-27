# 页间转场与元素动画

[English](../animations.md) | [中文](./animations.md)

---

PPT Master 会把**页间转场**和可选的**元素对象动画**写成真正的 PowerPoint
OOXML，而不是嵌入视频。对象动画包括进入、强调、动作路径和退出。本文只说明
用户需要做的选择和常用命令；精确效果映射、完整 sidecar schema、锚点规则与
封包校验统一由[动画执行规范](../../skills/ppt-master/references/animations.md)维护。

## 默认行为

| 层级 | 默认 | 含义 |
|---|---|---|
| 页间转场 | `fade`，0.4 秒 | 页面之间使用克制的视觉过渡 |
| 元素对象动画 | **`none`（关闭）** | 每页一次性完整出现；只有当动效确实有助于表达时才开启 |

修改动画设置不需要重新生成页面，只需对同一份 `svg_output/` 重跑 `svg_to_pptx.py`。

## 常用操作

| 目标 | 命令 |
|---|---|
| 保持默认设置 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project>` |
| 更换页间转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push` |
| 关闭视觉转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none` |
| 每 5 秒自动翻页 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5` |
| 开启自动元素入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto` |
| 全部使用同一种入场效果 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade` |
| 全部使用同一种原生强调效果 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation emphasis_spin` |
| 全部使用同一种原生动作路径 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation path_circle` |
| 全部使用同一种原生退出效果 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation exit_fade` |
| 单击逐个揭示元素 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| 所有元素同时入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| 放慢逐步揭示节奏 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

48 个规范页间切换标识已经覆盖当前 PowerPoint 效果库的三个完整分组：

- 细微：平滑 `morph`、淡入/淡出 `fade`、推入 `push`、擦除 `wipe`、
  分割 `split`、显示 `reveal`、切入 `cut`、随机线条 `random_bars`、
  形状 `shape`、揭开 `uncover`、覆盖 `cover`、闪光 `flash`。
- 华丽：跌落 `fall_over`、悬挂 `drape`、帘式 `curtains`、风 `wind`、
  上拉帷幕 `prestige`、折断 `fracture`、压碎 `crush`、剥离 `peel_off`、
  页面卷曲 `page_curl`、飞机 `airplane`、日式折纸 `origami`、溶解
  `dissolve`、棋盘 `checkerboard`、百叶窗 `blinds`、时钟 `clock`、
  涟漪 `ripple`、蜂巢 `honeycomb`、闪耀 `glitter`、涡流 `vortex`、
  碎片 `shred`、切换 `switch`、翻转 `flip`、库 `gallery`、立方体
  `cube`、门 `doors`、框 `box`、梳理 `comb`、缩放 `zoom`、随机
  `random`。
- 动态内容：平移 `pan`、摩天轮 `ferris_wheel`、传送带 `conveyor`、
  旋转 `rotate`、窗口 `window`、轨道 `orbit`、飞过 `fly_through`。

旧标识 `strips`、`circle`、`diamond`、`newsflash`、`plus`、`pull`、
`wedge`、`wheel` 只保留为兼容输入；新 sidecar、计划、轨迹和输出只使用规范
标识。兼容输入会反糖化为一个原生效果及其效果选项，例如 `diamond` 会变成
`shape` 加 `shape: diamond`，`wedge` 会变成 `clock` 加 `style: wedge`。

原生 PowerPoint 效果选项写在 `transition.effect_options` 中。方向、形状、
图案、Morph 范围、黑场、卷页数量和弹跳等参数都会按所选效果严格校验。运行
`python3 skills/ppt-master/scripts/pptx_animations.py --describe-transition <effect>`
可查看精确取值。`-t none` 只关闭视觉效果，不会移除显式设置的自动翻页计时。

## 选择 Start 模式

| Start 模式 | 行为 | 适用场景 |
|---|---|---|
| `on-click` | 每次单击显示一个内容组 | 由演讲者控制节奏的现场演示 |
| `with-previous` | 页面出现时所有内容组同时入场 | 一次协调完成的整体入场 |
| `after-previous`（默认） | 各内容组无需点击，按顺序自动出现 | 展厅循环、录屏走查和旁白 deck |

`--recorded-narration` 不支持 `on-click`；带旁白或用于视频导出的 deck 应使用 `after-previous` 或 `with-previous`。

## 选择动画效果

| 选择 | 适用场景 |
|---|---|
| `auto` | 让 PPT Master 根据内容组角色选择合适效果；这是开启元素动画时的推荐选项 |
| 原生 `entrance_*` | 使用 PowerPoint 的 53 个原生进入预设之一 |
| 原生 `emphasis_*` | 让已显示对象获得关注或改变外观 |
| 原生 `path_*` | 让对象沿 PowerPoint 的 64 条动作路径之一移动 |
| 原生 `exit_*` | 让对象在动画序列中退出页面 |
| `mixed` | 使用兼容模式名，在规范 PowerPoint 预设中确定性轮换 |
| `random` | 从同一规范预设池中稳定地生成变化 |
| `none` | 关闭元素动画 |

规范注册表包含 203 个 PowerPoint 原生标识：53 个进入、33 个强调、64 条
动作路径、53 个退出。现在新选择、sidecar、自动决策、转换轨迹和示例都只使用
带类别前缀的规范名称。29 个旧短名称只保留为兼容输入，写入前会归一化，不再
维护第二套动画行为。旧 Fly 方向名统一映射到 `entrance_fly`，旧 Wipe 方向名
统一映射到 `entrance_wipe`；方向会保留为参数，而不会形成新的规范预设。旧
`wheel` 保留四辐语义。运行
`python3 skills/ppt-master/scripts/pptx_animations.py --list` 可查看完整分类清单。
4 个媒体播放命令需要媒体或书签目标，仍由音视频工作流负责。

## 自定义具体对象

只有当整份 deck 的统一设置不够用时才需要 `animations.json`，例如标题先出现、图表第二个出现、结论最后出现。最简单的方式是从真实页面分组生成完整 scaffold，修改后校验并导出：

```bash
python3 skills/ppt-master/scripts/animation_config.py scaffold <project>
python3 skills/ppt-master/scripts/animation_config.py validate <project>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

生成的 sidecar 以稳定的顶层 `<g id="...">` 内容组为目标。常用对象级字段如下：

| 字段 | 用途 |
|---|---|
| `effect` | 覆盖对象动画效果；设为 `none` 可让该对象保持静态 |
| `order` | 调整揭示顺序，不改变页面图层顺序 |
| `delay` | 在 `after-previous` 中或单击 `trigger_shape` 后增加等待时间 |
| `duration` | 覆盖该对象的动画排程时长 |
| `effect_options` | 设置效果适用的 `direction`、`amount`、`color`、`font_name`、`relative` 或 `size` |
| `trigger_shape` | 单击另一个顶层内容组时触发本行（PowerPoint“单击下列对象时”） |
| 计时修饰 | `repeat_count`/`repeat_duration`、`auto_reverse`、`rewind`、`accelerate`、`decelerate`、`bounce_end` 与 `restart` |
| 播放完成 | `after_effect`（变暗/隐藏）和 `.m4a`/`.mp3`/`.wav` `sound` 路径 |

运行 `python3 skills/ppt-master/scripts/pptx_animations.py --describe
<canonical_effect>` 可查看该效果实际接受的完整参数。速度由 `duration` 控制，
平滑开始/结束由 `accelerate`/`decelerate` 控制。

`trigger_shape` 只能写在对象组上，并指向同一页另一个分组 id。它只让当前动画行
变为交互触发，其他行仍遵循页面 Start 模式；录制旁白不接受这种交互动画。

当用户要求 AI 调整具体对象时，使用 [`customize-animations`](../../skills/ppt-master/workflows/stages/customize-animations.md) 阶段。完整 sidecar schema 与目标校验规则仍由[动画执行规范](../../skills/ppt-master/references/animations.md)维护。

## 校验与兼容性

PPT Master 会严格校验动画设置：未知效果或 Start 模式、非法计时、缺失页面/分组引用，以及尝试给结构对象加动画都会直接失败，不会静默改成另一种行为。导出还会在替换现有产物前回读候选 PPTX。

| 边界 | 对用户的影响 |
|---|---|
| 动画目标 | 元素动画作用于逻辑内容组，而不是每一个 SVG 原子 |
| 静态结构 | 背景、Master/Layout 内容、placeholder 与页面框架保持静态 |
| 输出路线 | 动画存在于从 `svg_output/` 生成的原生 PPTX；`svg_final/` 只是静态预览 |
| 现有 PPTX 路线 | Template Fill 与 Native Enhance 保留源对象动画，不把它翻译成生成路线的动画模型 |
| 播放兼容性 | Microsoft PowerPoint 桌面版是主要验证目标；Keynote、WPS、LibreOffice 与较旧 Office 可能重新映射或忽略个别效果 |

完整 CLI 说明见 [`svg-pipeline.md`](../../skills/ppt-master/scripts/docs/svg-pipeline.md)。精确效果定义、sidecar 要求、锚点回退逻辑与 OOXML 回读规则见[动画执行规范](../../skills/ppt-master/references/animations.md)。
