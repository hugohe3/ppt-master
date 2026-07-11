# 页间转场与页内元素动画

PPT Master 导出的 PPTX 同时支持**页间转场**（page transition）与**页内元素入场动画**（per-element entrance animation）。两者都通过 `svg_to_pptx.py` 的 CLI 参数控制，输出为真正的 OOXML 动画，不是嵌入视频。Microsoft PowerPoint 桌面版是动效行为的主要验证目标；Keynote、WPS、LibreOffice 可以打开 PPTX，但可能以不同方式映射个别效果或 Start 语义。

## 默认行为

| 层级 | 默认 | 原因 |
|---|---|---|
| 页间转场 | `fade`，0.4 秒 | 适合大多数 deck 的中性基线 |
| 页内元素动画 | **`none`（关闭）** | 翻到一页时整页一次性呈现。元素一个个自动级联出来是「AI 味」最重的信号，且没人主动要，所以页内动画改为按需开启。用 `-a auto`（或其它效果）开启：根据每个 group 的 SVG id 映射效果（chart→wipe、card-/step-/pillar-→fly、title/takeaway→fade），图片类 id（`hero` / `figure-` / `image` / `img-` / `kpi`）在更丰富的视觉池（zoom / dissolve / circle / box / diamond / wheel）中循环以产生 deck 内变化，未命中的 id 在 fade/wipe/fly/zoom 间循环 |

修改设置只需对同一份 `svg_output/` 重跑 `svg_to_pptx.py`，无需重新跑 LLM。`-s final` 只保留给诊断对比，不能作为受支持的发布源。如要为整份 deck 开启页内动画，加 `-a auto`。

## 对象级自定义动画

页内元素动画默认关闭。为整份 deck 开启只需导出时加 `-a auto`（无需配置文件）。若需要更具体的演示节奏，例如标题先淡入、图表第二个出现、关键注释最后飞入，可以使用可选的 `animations.json` sidecar。SVG 仍然只保存静态视觉结构；sidecar 只控制 PPTX 导出动画。

当用户要求调整动画顺序、效果、时长或具体对象出现方式时，运行独立 [`customize-animations`](../../skills/ppt-master/workflows/customize-animations.md) 工作流。

```bash
# 从真实顶层 <g id> 锚点生成可编辑模板
python3 skills/ppt-master/scripts/animation_config.py scaffold <project>

# 导出前校验引用是否存在
python3 skills/ppt-master/scripts/animation_config.py validate <project>

# 导出时会自动读取 <project>/animations.json
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>
```

完整 sidecar 示例（假设项目只有下面两页）：

```json
{
  "version": 1,
  "defaults": {
    "transition": { "effect": "fade", "duration": 0.4 },
    "animation": {
      "effect": "auto",
      "duration": 0.4,
      "stagger": 0.5,
      "trigger": "after-previous"
    }
  },
  "slides": {
    "01_cover": {
      "transition": { "effect": "fade", "duration": 0.5 },
      "animation": {
        "effect": "fade",
        "duration": 0.5,
        "stagger": 0.3,
        "trigger": "after-previous"
      },
      "groups": {
        "cover-hero": { "effect": "zoom", "order": 2, "duration": 0.6 }
      }
    },
    "03_market": {
      "transition": { "effect": "wipe", "duration": 0.35 },
      "animation": {
        "effect": "fade",
        "duration": 0.4,
        "stagger": 0.25,
        "trigger": "after-previous"
      },
      "groups": {
        "chart": { "effect": "wipe", "order": 2, "duration": 0.6 },
        "insight": { "effect": "fly", "order": 3, "delay": 0.2 }
      }
    }
  }
}
```

规则：

- `defaults` 是未列页面的回退值；正式自定义配置仍应把 `svg_output/` 中的每一页都写进 `slides`。
- `slides` key 匹配 SVG 文件 stem（`03_market.svg` → `03_market`）。
- 每个页面都显式写完整的 `transition`、`animation` 和 `groups`；`groups` 只列真正偏离页面默认值的对象。
- `groups` key 只能匹配可动画的顶层 `<g id="...">` 内容锚点；带 `data-pptx-layer` 或显式静态 role/placeholder 标记的 Master / Layout / 静态框架对象不属于可覆盖目标。
- `effect: none` 会把该组移出入场动画序列。
- `order` 必须是大于零的整数，只改变动画顺序，不改变页面图层顺序。
- `delay` 是 `after-previous` 模式下该组开始前的秒数。
- `duration` 覆盖该组的排程时长；`appear` 的可见性切换固定为 1ms，该值只用于计算下一条 `after-previous` 的间隔。
- `--animation none` 覆盖 sidecar，强制关闭所有页内动画。

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

默认关闭——用 `-a auto`（或其它效果）为整份 deck 开启。开启后共有三种 Start 模式，**与 PowerPoint 动画窗格的 Start 下拉菜单一一对应**：

- **`on-click`**（单击时）—— 进入页面 → 第一次点击显示第一个语义组，后续每次点击按 z-order 显示下一个组。适合现场演讲，演讲者控制节奏。与 `--recorded-narration` 互斥，因为带旁白的视频导出需要无点击播放。
- **`with-previous`**（与上一动画同时）—— 所有组在进入页面时一起入场，并行播放各自的入场动画。`--animation-stagger` 不生效。
- **`after-previous`**（默认，在上一动画之后）—— 第一组进入页面时入场，后续组在前一个结束后接着出现，并按 `--animation-stagger` 增加额外间隔。适合展厅循环、录屏走查，或者只是想看流动效果不想点击。

```bash
# 默认行为（无参数）：只有页间转场，没有页内元素动画
python3 skills/ppt-master/scripts/svg_to_pptx.py <project>

# 为整份 deck 开启页内动画（auto 效果 + after-previous 自动级联）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto

# 开启并改用单一效果（走 after-previous 自动级联）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation fade

# 开启并改为单击触发（演讲者控制节奏）
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger on-click

# 自定义节奏
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> --animation mixed \
        --animation-stagger 0.6 --animation-duration 0.5

# 所有组进入页面时同时入场
python3 skills/ppt-master/scripts/svg_to_pptx.py <project> -a auto --animation-trigger with-previous
```

22 种单一效果：`appear`、`fade`、`fly`、`cut`、`zoom`、`wipe`、`split`、`blinds`、`checkerboard`、`dissolve`、`random_bars`、`peek`、`wheel`、`box`、`circle`、`diamond`、`plus`、`strips`、`wedge`、`stretch`、`expand`、`swivel`。再加三种自动模式：

这些 key 保留既有的 `filter + presetID + presetSubtype` tuple。`cut` 是兼容旧配置的公开 key；项目承诺保持其既有 tuple，不根据外部 preset 表推测或重命名视觉语义。

- `auto`（开启时推荐）—— 按 group 的 SVG id 映射效果。信息密集元素稳定映射：`chart` / `table` / `legend` / `timeline` / `track` → `wipe`；`card-*` / `pillar-*` / `item-*` / `step-*` / `stage-*` / `tier-*` / `principle-*` → `fly`；`title` / `chapter-*` / `section-*` / `cover-*` / `tagline` / `subtitle` → `fade`；`takeaway` / `callout` / `quote` / `source` / `conclusion` / `note` → `fade`。图片类 id `hero` / `figure-*` / `image` / `img-*` / `kpi` 则在更丰富的视觉池（`zoom` / `dissolve` / `circle` / `box` / `diamond` / `wheel`）中循环，使多张图片在 deck 内呈现不同入场。未命中的 id 在 `fade` / `wipe` / `fly` / `zoom` 之间循环。
- `mixed`（旧逻辑）—— 确定性轮换。每页第一个动画组使用 `fade`，后续组在整份 deck 范围内按 16 效果池（`blinds` / `checkerboard` / `dissolve` / `fly` / `cut` / `random_bars` / `box` / `split` / `strips` / `wedge` / `wheel` / `wipe` / `expand` / `fade` / `swivel` / `zoom`）连续轮换。保留以兼容旧配置。
- `random` —— 从旧的 16 效果池中按有效 deck 输入使用稳定 seed 抽取；相同输入得到相同结果，启用 `--conversion-trace` 时记录每个已解析效果。

所有轮换池都排除了 `appear`，因为它没有可见动画过程。

参数：

- `-a/--animation` — 效果名、`auto`、`mixed`、`random` 或 `none`。默认 `none`（页内动画关闭；用 `auto` 开启）。
- `--animation-trigger` — Start 模式（与 PowerPoint 一致）：`on-click`、`with-previous`、`after-previous`（默认）。
- `--animation-duration` — 单个元素入场秒数，默认 `0.4`。
- `--animation-stagger` — `after-previous` 模式下两组之间的额外间隔（秒，默认 `0.5`）。其他模式忽略。
- `--animation-config` — sidecar 路径。默认自动读取 `<project>/animations.json`（如果存在）。

> Note: `--recorded-narration` 会拒绝 `on-click`；带旁白的视频导出请使用 `after-previous` 或 `with-previous`。

## 严格校验与导出回读

动画配置不会静默换成另一个效果或触发方式。运行 `animation_config.py validate` 后，以下问题都会返回非零：

| 问题 | 结果 |
|---|---|
| 未知效果、自动模式或 Start 模式 | 报错；不会回退为 `fade` 或 `on-click` |
| `duration` 非有限或不大于零 | 报错；页间 `effect: none` 是兼容例外，可使用 `duration: 0` |
| `stagger` / `delay` 非有限或小于零 | 报错 |
| `order` 不是大于零的整数（含布尔、浮点或字符串） | 报错 |
| `slides` / `groups` 引用不存在 | 报错并阻止导出 |
| 顶层 `<g>` 没有 `id` | 给出警告；该组不能被 `groups` 精确引用，建议补稳定 id |

导出先写候选 PPTX，再回读整个包：每页只能有一个合法的根级 `p:timing`，时间节点 ID 必须唯一，`spTgt` / `bldP` 必须指向现存 shape，效果、时长和 Start 模式必须与已解析配置一致。旁白加入音频 timing 后也走同一包级校验；任何失败都不会替换已有公开产物。

## 锚点机制 — 顶层 `<g id="...">`

页内动画锚定在 SVG 的**顶层 `<g id="...">` 内容组**上（如 `<g id="cover-title">`、`<g id="card-1">`），一个组对应动画窗格中的一条入场记录；是否需要点击由 Start 模式决定。

每页建议 **3–8 个内容组**。这同时也是 PowerPoint 框选 / 整体移动的颗粒度，与是否启用动画无关，都能改善编辑体验。

**静态结构优先于动画覆盖。** `data-pptx-layer` 明确标记 Master / Layout / 静态页面框架，永远不会成为页内动画锚点，`groups` 中的手工覆盖也不能强制开启。没有该标记时，结构角色 / placeholder 语义继续优先；只对缺少显式语义的旧 SVG 使用 id token 回退。若 id 按 `-` 和 `_` 切分后命中 `background` / `bg` / `decoration` / `decorations` / `decor` / `header` / `footer` / `chrome` / `watermark` / `pagenumber` / `pagenum` / `nav` / `logo` / `rule`，该组会跟随页面立即显示。会跳过的例子：`<g id="background">`、`<g id="cover-footer">`、`<g id="p03-header">`、`<g id="bottom-decor">`、`<g id="watermark">`、`<g id="logo-area">`。仍会动画的例子：`<g id="card-1">`、`<g id="cover-title">`、`<g id="step-discover">`、`<g id="timeline-track">`。**不要为了规避动画去掉 `<g>` 包裹**——保留分组（PowerPoint 框选需要），为静态结构使用正确的 layer / role 标记。

**扁平 SVG 的回退逻辑**（顶层没有 `<g>`，只有裸 `<rect>` / `<text>` / `<path>`）：

- 顶层可见图元 ≤ 8 → 每个图元作为一个锚点（设上限以避免密集页面出现 70+ 次点击）。
- 顶层可见图元 > 8 → 该页跳过页内动画。页面照常显示，只是不带入场。

无论是否打算开启动画，Executor 都应该把逻辑分块包进 `<g id>`。`skills/ppt-master/references/shared-standards.md` 已将这一点列为强制要求。

## 限制

- **动画只写入原生 DrawingML PPTX。** 页间转场和页内元素动画都属于项目转换器从 `svg_output/` 生成的 PPTX；`svg_final/` 仍是静态视觉预览，不是带动画的替代 PPTX 路线。
- **直接 PPTX 路线只保留对象动画。** Template Fill 与 Native Enhance 不把源 `p:timing` 翻译或重建为生成路线的效果模型；它们保留源对象动画，Native Enhance 仅在需要时合并旁白音频 timing，并在封包前校验结果。旁白合并只接受根级 `p:sld/p:timing`；若源 timing 位于 `mc:AlternateContent` 或其他非根容器中，会安全报错，不会重写或重复 timing 树。
- **PowerPoint 是主要动效验证目标。** Keynote、WPS、LibreOffice 与较旧 Office 可能重新映射、简化或忽略部分效果；动效是交付要求时，请在 Microsoft PowerPoint 桌面版中完成最终播放检查。
- **手工 SVG 形状转换不受支持。** 把 `svg_final/` 页面作为 SVG 图片插入 PowerPoint，不会获得元素级动画锚点；需要可编辑且可动画的形状时，请使用原生 PPTX。

## 常用速查

| 目标 | 命令 |
|---|---|
| 关闭转场 | `-t none` |
| 切换转场效果 | `-t push`（或上文列表中任一） |
| 转场放慢 | `--transition-duration 0.8` |
| 自动播放 | `--auto-advance 5` |
| 关闭页内动画 | `-a none` |
| 改为单击触发 | `-a auto --animation-trigger on-click` |
| 切换为单一效果 | `--animation fade` |
| 所有组同时入场 | `-a auto --animation-trigger with-previous` |
| 元素入场放慢 | `-a auto --animation-duration 0.5` |
| after-previous 拉大间隔 | `-a auto --animation-stagger 0.8` |

完整 `svg_to_pptx.py` 参考：[`scripts/docs/svg-pipeline.md`](../../skills/ppt-master/scripts/docs/svg-pipeline.md)。
