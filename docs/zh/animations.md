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

修改动画设置不需要重新生成页面，可以继续使用同一份 `svg_output/`。默认发布导出仍要求
当前匹配且通过的最终 SVG 质量报告；不存在这样的报告时，先运行最终检查并解决其中的
阻塞问题，再重跑 `svg_to_pptx.py`。

## 常用操作

| 目标 | 命令 |
|---|---|
| 保持默认设置 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project>` |
| 更换页间转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t push` |
| 关闭视觉转场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -t none` |
| 每 5 秒自动翻页 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --auto-advance 5` |
| 开启自动元素入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto` |
| 全部使用同一种入场效果 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation entrance_fade` |
| 单击逐个揭示元素 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click` |
| 所有元素同时入场 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous` |
| 放慢逐步揭示节奏 | `python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-duration 0.5 --animation-stagger 0.8` |

## 选择页间切换

| 相邻页面关系 | 优先考虑 |
|---|---|
| 同一章节内的普通连续叙述 | `fade` |
| 无需保留连续性的直接切换 | `none` 或 `cut` |
| 有明确方向的步骤、时间线或可见层级推进 | 按语义方向使用 `push`、`wipe`、`cover` 或 `uncover` |
| 同一对象或场景的位置、尺寸、裁切或外观发生变化 | `morph` |
| 章节开场、关键揭示或明显状态边界 | 少量使用 `split`、`reveal`、`shape`、`flash` 或 `random_bars` |
| 重复内容在同一空间框架中连续推进 | `pan`、`conveyor` 或 `ferris_wheel`；单个对象需要保持身份时使用 Morph |
| 视点围绕或穿越一个连续空间 | `rotate`、`window`、`orbit` 或 `fly_through` |
| 主题适合舞台、纸张或实体翻页隐喻 | 少量使用 `fall_over`、`drape`、`curtains`、`wind`、`prestige`、`peel_off`、`page_curl`、`airplane`、`origami` 或 `doors` |
| 破坏性节点表达断裂、坍塌或消散 | 少量使用 `fracture`、`crush`、`dissolve`、`vortex` 或 `shred` |
| 关键揭示适合几何、计时或纹理图案 | 少量使用 `checkerboard`、`blinds`、`clock`、`ripple`、`honeycomb`、`glitter` 或 `comb` |
| 卡片、面板、图库或视角发生可见翻面 | 少量使用 `switch`、`flip`、`gallery`、`cube`、`box` 或 `zoom` |

没有其他切换能增加表达意义时，保留 `fade` 或 `none`。不要只为制造变化而
更换效果；只有“不确定性”本身就是意图时才使用 `random`。

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

## 选择对象动画

从 `none` 开始。只有对象运动承担明确沟通任务时，才先选择生命周期，再选择
视觉效果：

| 沟通任务 | 选择 | 使用边界 |
|---|---|---|
| 按阅读或旁白顺序揭示信息 | `auto` 或原生 `entrance_*` | 这是最常见的对象动画场景 |
| 让已经可见的对象重新获得关注 | 显式 `emphasis_*` | 不用于对象第一次出现 |
| 表达有意义的空间或因果移动 | 显式 `path_*`，或在相邻页间使用 Morph | 路径本身应承载意义；刻意设计的背景氛围运动属于高级例外 |
| 在同一页移除、替换内容或腾出空间 | 显式 `exit_*` | 普通翻页已经会移走旧页面 |
| 为通用进入效果增加确定性或固定种子变化 | `mixed` 或 `random` | 两种模式仍只选择进入效果 |
| 没有明确的运动任务 | `none` | 保持静态 |

规范注册表包含 203 个 PowerPoint 原生标识：53 个进入、33 个强调、64 条
动作路径、53 个退出。现在新选择、sidecar、自动决策、转换轨迹和示例都只使用
带类别前缀的规范名称。`auto`、`mixed` 与 `random` 只会选择进入效果；强调、
动作路径与退出必须使用显式规范标识。29 个旧短名称只保留为兼容输入，写入前会
归一化，不再维护第二套动画行为。旧 Fly 方向名统一映射到 `entrance_fly`，旧
Wipe 方向名统一映射到 `entrance_wipe`；方向会保留为参数，而不会形成新的规范
预设。旧 `wheel` 保留四辐语义。运行
`python3 skills/ppt-master/scripts/pptx_animations.py --list` 可查看完整分类清单。
4 个媒体播放命令需要媒体或书签目标，仍由音视频工作流负责。

## 在确定动效后添加声音

音效默认关闭。PPT Master 内置了全局 CC0 音效库，但不会在策略阶段或普通
项目初始化时把它复制进项目。先完成 SVG 页面并确定视觉转场 / 对象动画；只有
其中一个已确定的节拍确实需要听觉提示时，才完整读取客观的
[声音词汇表](../../skills/ppt-master/templates/sounds/sound-vocabulary.md)，选定一个
准确 id 并同步声音：

```bash
python3 skills/ppt-master/scripts/sound_sync.py \
  <project> bigsoundbank/1797 kenney-interface/click_001
```

该命令只会把选中的文件复制到 `<project>/sounds/<namespace>/`。没有选中声音时，
PPT Master 不创建项目 `sounds/` 目录，也不复制任何文件。完整阅读词汇表后，可以
用 CLI 缩小已经考虑过的名称、标签或语境范围，但它不负责判断适配性：

```bash
python3 skills/ppt-master/scripts/sound_sync.py list --query whoosh
```

配置始终引用复制后的项目相对路径，不直接引用全局 `templates/sounds/` 路径，
也不把声音库 id 写进 sidecar：

```json
{
  "version": 1,
  "slides": {
    "02_process": {
      "transition": {
        "effect": "push",
        "sound": "sounds/bigsoundbank/1797.wav"
      },
      "groups": {
        "next-step": {
          "effect": "entrance_fade",
          "sound": "sounds/kenney-interface/click_001.wav"
        }
      }
    }
  }
}
```

`transition.sound` 使用 WAV。对象动画 `sound` 仍兼容已有的项目相对或绝对
`.m4a`、`.mp3`、`.wav` 输入；内置库统一为 WAV，应使用同步后的项目相对路径。
只有转场声音时可以使用稀疏 `animations.json`；页面级
`transition.sound: null` 可清除继承的默认转场声音。导出前仍须校验。
不要为了展示项目具备音效能力而强行添加声音。

上述校验只能证明可编辑 PPTX 含有原生 cue，不能证明 PowerPoint 导出的 MP4
音轨含有它。直接交付带旁白且含音效 cue 的视频时，应按
[音频旁白与视频导出](./audio-narration.md)选择验收后的原生导出混音，或显式采用
捕获系统音频的 PowerPoint 实时放映录制；两条路径不能叠加。

## 自定义具体对象

只有当整份 deck 的统一设置不够用时才需要 `animations.json`，例如让同一对象
进入、移动、获得强调后再退出。先列出真实分组，只为受影响页面和对象写稀疏覆盖，
然后校验并导出。`scaffold` 是可选的中性编辑起点：其默认对象效果为 `none`，
未修改的 `{}` 分组条目不会开启动画。

```bash
python3 skills/ppt-master/scripts/animation_config.py list-groups <project>
python3 skills/ppt-master/scripts/animation_config.py validate <project>
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

sidecar 以稳定的顶层 `<g id="...">` 内容组为目标。group ID 是 PowerPoint
shape target 锚点，不等同于 Animation Pane 中的一行。兼容的单效果对象仍生成
一行；`effects[]` 可以生成多条有序记录，并让它们共同指向同一 shape：

```json
{
  "version": 1,
  "slides": {
    "03_threshold": {
      "animation": { "trigger": "after-previous" },
      "groups": {
        "risk-marker": {
          "effects": [
            { "effect": "entrance_fade", "order": 1, "duration": 0.25 },
            { "effect": "path_right", "order": 2, "delay": 0.1, "duration": 0.7 },
            { "effect": "emphasis_teeter", "order": 3, "trigger": "with-previous", "duration": 0.45 },
            { "effect": "exit_fade", "order": 4, "trigger_shape": "details-button", "duration": 0.3 }
          ]
        }
      }
    }
  }
}
```

一个已填写的分组只能使用旧单效果字段或 `{ "effects": [...] }`，不能混用。
`effects` 必须非空，且每一行都要显式声明 `effect`。现有单效果 sidecar 完全兼容。

常用动画行字段如下：

| 字段 | 用途 |
|---|---|
| `effect` | 选择一个显式效果；旧单效果形式可用 `none` 让对象保持静态 |
| `trigger` | 覆盖本行的 Start 模式；省略时继承页面动画 trigger |
| `order` | 设置普通动画行的整页顺序且不改变图层；trigger-shape 行保留在独立交互序列中 |
| `delay` | 给本行解析后的 Start 行为增加等待时间 |
| `duration` | 覆盖本行的动画排程时长 |
| `effect_options` | 设置效果适用的 `direction`、`amount`、`color`、`font_name`、`relative` 或 `size` |
| `trigger_shape` | 单击另一个顶层内容组时触发本行（PowerPoint“单击下列对象时”） |
| 计时修饰 | `repeat_count`/`repeat_duration`、`auto_reverse`、`rewind`、`accelerate`、`decelerate`、`bounce_end` 与 `restart` |
| 播放完成 | `after_effect`（`none`、变暗、隐藏或下次单击时隐藏） |
| 声音提示 | 可选的项目级 `sound` 路径；内置库声音按上面的流程按需同步 |

`order`、`delay`、`duration`、`trigger` 与 `trigger_shape` 都按动画行独立解析。
页面级动画 trigger 只负责提供继承值。`trigger_shape` 隐含 `on-click`；若同一行
也显式写了 `trigger`，其值必须是 `on-click`。

运行 `python3 skills/ppt-master/scripts/pptx_animations.py --describe
<canonical_effect>` 可查看该效果实际接受的完整参数。速度由 `duration` 控制，
平滑开始/结束由 `accelerate`/`decelerate` 控制。Change Font 的 `font_name`
必须是目标环境已安装的一个具体 PowerPoint 字体名，不能写 CSS 字体列表。

`trigger_shape` 指向同一页另一个分组 id，并且只影响所在动画行。录制旁白不接受
任何最终解析为 `on-click` 的动画行，其中包括 `trigger_shape` 行。

当用户要求 AI 调整具体对象时，使用 [`customize-animations`](../../skills/ppt-master/workflows/stages/customize-animations.md) 阶段。完整 sidecar schema 与目标校验规则仍由[动画执行规范](../../skills/ppt-master/references/animations.md)维护。

## 校验与兼容性

PPT Master 会严格校验动画设置：未知效果或 Start 模式、非法计时、缺失页面/分组引用，以及尝试给结构对象加动画都会直接失败，不会静默改成另一种行为。导出还会在替换现有产物前回读候选 PPTX。

| 边界 | 对用户的影响 |
|---|---|
| 动画目标 | 元素动画作用于逻辑顶层内容组锚点；一个锚点可以拥有多条 Animation Pane 记录 |
| 静态结构 | 背景、Master/Layout 内容、placeholder 与页面框架保持静态 |
| 不支持的对象 build | 不会从分组 SVG 推导段落/文字范围 build、自定义自由动作路径、原生 Chart/SmartArt 分步 build 或媒体播放命令 |
| 输出路线 | 动画存在于从 `svg_output/` 生成的原生 PPTX；`svg_final/` 只是静态预览 |
| 现有 PPTX 路线 | Template Fill 与 Native Enhance 保留源对象动画，不把它翻译成生成路线的动画模型 |
| PPTX-to-SVG 回导 | 只重建当前注册表内具有精确原生时长且可唯一映射到顶层 group 的记录；高级/build/media timing 保留诊断 |
| 播放兼容性 | Microsoft PowerPoint 桌面版是主要验证目标；Keynote、WPS、LibreOffice 与较旧 Office 可能重新映射或忽略个别效果 |

完整 CLI 说明见 [`svg-pipeline.md`](../../skills/ppt-master/scripts/docs/svg-pipeline.md)。精确效果定义、sidecar 要求、锚点回退逻辑与 OOXML 回读规则见[动画执行规范](../../skills/ppt-master/references/animations.md)。
