# 页间转场与元素动画

[English](../animations.md) | [中文](./animations.md)

---

PPT Master 会把**页间转场**和可选的**元素入场动画**写成真正的 PowerPoint OOXML，而不是嵌入视频。本文只说明用户需要做的选择和常用命令；精确效果映射、完整 sidecar schema、锚点规则与封包校验统一由[动画执行规范](../../skills/ppt-master/references/animations.md)维护。

## 默认行为

| 层级 | 默认 | 含义 |
|---|---|---|
| 页间转场 | `fade`，0.4 秒 | 页面之间使用克制的视觉过渡 |
| 元素入场动画 | **`none`（关闭）** | 每页一次性完整出现；只有当逐步揭示确实有助于表达时才开启 |

修改动画设置不需要重新生成页面，只需对同一份 `svg_output/` 重跑 `svg_to_pptx.py`。

## 常用操作

| 目标 | 命令 |
|---|---|
| 保持默认设置 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project>` |
| 更换页间转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push` |
| 关闭视觉转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none` |
| 每 5 秒自动翻页 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5` |
| 开启自动元素入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto` |
| 全部使用同一种入场效果 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade` |
| 单击逐个揭示元素 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| 所有元素同时入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| 放慢逐步揭示节奏 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

页间转场可选 `fade`、`push`、`wipe`、`split`、`strips`、`cover`、`random`。`-t none` 只关闭视觉效果，不会移除显式设置的自动翻页计时。

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
| `fade`、`wipe`、`fly`、`zoom` 等单一效果 | 整份 deck 需要统一的入场风格 |
| `mixed` | 需要兼容旧版的确定性效果轮换 |
| `random` | 需要从旧效果池中稳定地生成变化 |
| `none` | 关闭元素动画 |

完整效果清单及其精确 PowerPoint 映射属于[动画执行规范](../../skills/ppt-master/references/animations.md)，不在用户指南中重复维护。

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
| `effect` | 覆盖入场效果；设为 `none` 可让该对象保持静态 |
| `order` | 调整揭示顺序，不改变页面图层顺序 |
| `delay` | 在 `after-previous` 模式下增加开始前等待时间 |
| `duration` | 覆盖该对象的入场排程时长 |

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
