# PowerPoint 功能 ↔ 项目 SVG 映射指南

[English](../powerpoint-svg-mapping.md)

## 目的与权威边界

本指南从 PowerPoint 使用者的视角回答一个问题：**对于某项 PowerPoint 功能，项目中由什么表达承载，导出或回导时能保留什么？** 因此，PowerPoint 语义是唯一主索引，SVG 元素只作为某项 PowerPoint 能力的具体实现出现。

这是一份公开的能力映射表，不是第二份语法规范，也不承诺转换任意 SVG 或任意 OOXML。规范权威仍属于 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md)；如果本指南与该规范不一致，以规范为准。本指南未列出的功能不会因此被默认为受支持。

主路线编译的是**项目规范化 SVG**，而不是通用浏览器 SVG：

```text
PowerPoint 意图
    ↔ 项目规范化 SVG 或显式 sidecar
    ↔ DrawingML / PPTX 包语义
```

有些 PowerPoint 功能没有诚实的 SVG 等价表达。对于这些功能，本指南会明确标为 sidecar/打包层功能、直接 PPTX 保留功能或不支持，而不是强行塞进装饰性 SVG metadata。

## 如何阅读表格

每行只对应一项 PowerPoint 能力。映射的基数不一定是一个对象对一个对象：一个 SVG 文本节点可能生成多个 PowerPoint run，一个原生图表 marker 组可能收敛为一个 `p:graphicFrame`，一个导入的 PowerPoint 对象也可能重建为多个 SVG 元素。

| 术语 | 含义 |
|---|---|
| `Native-stable` | 在文档化边界内，导出使用对应的可编辑 DrawingML 属性或对象。 |
| `Native-normalized` | 导出结果仍可编辑，但源表达会被归一化为等价的 DrawingML 结构。 |
| `Approximate` | PowerPoint 没有完全对应的能力；效果具有实质意义时必须复核生成的 PPTX。 |
| `Bake-required` | 必须预渲染为图片，或使用受支持的显式几何重建。 |
| `Sidecar/package` | 该能力属于项目 sidecar 或 PPTX 打包器，而不是 SVG 页面设计。 |
| `Direct preservation` | 直接 PPTX 工作流可以保留源 OOXML；主 SVG 编译器不重建它。 |
| `Unsupported` | 主生成路线没有已登记映射，不得猜测。 |

下文中的“回导”是指 PPTX-to-SVG 路线对语义的重建，而不是恢复原始 SVG 语法。它不承诺恢复原始 `<defs>` 图、`<use>` 结构、path 命令或 `<tspan>` 排版。

## 1. 演示文稿、幻灯片与坐标模型

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 演示文稿页面尺寸 | 根 SVG `viewBox`，通过项目画布合同选择 | 演示文稿宽高；96 DPI 下 `1 SVG px = 9,525 EMU` | `Native-stable`；导入坐标投影到 SVG 画布 | 每页必须使用已选画布；禁止根 transform |
| 幻灯片 | 一个完整的 `svg_output/<slide>.svg` 页面 | 一个 `p:sld` 及其 relationships | 重建为一张完整 SVG 页面 | SVG 是可见页面权威；备注和包行为单独承载 |
| 对象位置与尺寸 | SVG 绝对坐标与元素边界 | `a:xfrm` 偏移和范围 | 经坐标换算后为 `Native-normalized` | 数值必须有限，并使用已登记坐标语法 |
| Z 顺序 | SVG 源码顺序，由后到前 | PowerPoint shape tree 顺序 | 按 shape tree 顺序重建 | 不得依赖浏览器专属堆叠行为 |
| 旋转、缩放、平移与镜像 | 受支持的 SVG transform 形式 | DrawingML transform 或归一化几何 | `Native-normalized`；matrix 可能被分解 | 已登记 transform 合同以外的倾斜与错切不可接受 |
| 主题颜色与字体 | `spec_lock.md` 锁定的角色；规范 SVG 使用解析后的值 | 当精确匹配锁定角色时保留 theme token，否则写直接 DrawingML 值 | 已登记角色为 `Native-stable` | 新页面不得自行发明未锁定颜色、字体或字号 |
| PowerPoint 包身份 | `spec_lock.md` 结构声明与打包器 | Presentation、Master、Layout、relationship 与 content type 注册 | 从包结构读回，不从页面外观推断 | 最终包读回必须与声明的 roster 一致 |

受支持的画布见 [`canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md)，精确单位语法以规范为准。

## 2. Master、Layout、背景与占位符功能

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 自由设计演示文稿结构 | `pptx_structure.mode: flat`；页面内容保持 Slide-local | 一个干净的项目 Master 和一个 Blank Layout，已表达对象留在 Slide | flat 路线包拓扑为 `Native-stable` | 禁止编写 Master/Layout/layer/placeholder metadata |
| 基于模板的演示文稿结构 | `pptx_structure.mode: structured` 加显式 Master/Layout/页面分配 | 声明的 `p:sldMaster`、`p:sldLayout`、注册与 Slide 父子关系 | 在显式结构合同内为 `Native-stable` | 导出器绝不猜测 Master、Layout 或占位符拓扑 |
| 幻灯片母版 | 根 Master 身份加原子级 `data-pptx-layer="master"` 对象 | 可复用 Master part 与 picker 身份 | 源结构由模板/导入工作流恢复 | Master atom 必须为直接、稳定对象，并在所属页面间一致 |
| 幻灯片版式 | 根 Layout 身份加原子级 `data-pptx-layer="layout"` 对象 | 某个 Master 下的可复用 Layout part | 可恢复源 Layout；adaptive 创作可分配新 Layout | 仅当固定 atom 和 slot 合同完全相同时才复用 Layout key |
| strict 模板 Layout | 选中的原型合同 | 保留现有已声明 Layout 拓扑 | 页面遵循原型时为 `Native-stable` | 不得改变固定 Layout atom 和 slot 结构 |
| adaptive 模板 Layout | 选定 Master 加显式的当前或新声明 Layout | 可在可复用结构变化时创建新 Layout 身份 | 更新 lock 与页面映射后为 `Native-stable` | 绝不默默改变已复用 Layout key |
| structured 模式以外的 Slide 背景填充 | 第一个合格的全幅 `<rect>`，可直接位于根下或位于简单单子组中，使用已登记纯色、线性/径向渐变或预设图案填充 | Slide 的原生 `p:bg` | 保真度遵循下文对应 paint 行 | transform、filter、clip、圆角、可见 stroke 或未映射 fill 会阻止提升 |
| structured 模式的 Master/Layout/Slide 背景填充 | 声明结构层中一个直接铺满画布的纯色 `<rect>` | Master、Layout 或 Slide 层级的原生 `p:bg` | `Native-stable` | 显式 scoped background 所有权有意只支持纯色 |
| structured 模式的渐变或图案背景形状 | 声明在 Master/Layout 层的普通渐变/图案 `<rect>`，或 Slide-local 内容 | 所属 part 上的可编辑 shape | 保真度遵循下文对应 paint 行 | structured 导出关闭通用背景提升；不得使用 `data-pptx-layer="slide"` |
| 图片背景 | 声明在 Master/Layout 层的普通项目 `<image>`，或 Slide-local 内容 | 所属 part 上的可编辑 `p:pic` | 保真度遵循下文 picture 对应行 | image 元素绝不提升为 `p:bg` |
| 标题占位符 | 含一个文本 carrier 的结构化 slot 组 | Layout 和 Slide 的 `title` 类型 `p:ph` | `Native-stable` | carrier 数量、边界、类型与有效 index 必须与 Layout 合同一致 |
| 副标题占位符 | 含一个文本 carrier 的结构化 slot 组 | `subTitle` 类型 `p:ph` | `Native-stable` | 与标题相同的 slot 规则 |
| 正文占位符 | 含一个文本 carrier 的结构化 slot 组 | `body` 类型 `p:ph` | `Native-stable` | 多行 carrier 仍必须是一个文本框 |
| 日期、页脚与页码占位符 | 结构化文本 slot | `dt`、`ftr` 与 `sldNum` 类型 `p:ph`，带匹配的 Layout 页眉/页脚标志 | `Native-stable` | 占位符 index 必须唯一且合法 |
| 图片占位符 | 含一个图片或受支持 crop carrier 的结构化 slot | `pic` 类型 `p:ph` | 在图片合同内为 `Native-stable` | slot 必须恰好含一个兼容的直接 carrier |
| 图表或表格占位符 | 含一个匹配原生对象 carrier 的结构化 slot | `chart` 或 `tbl` 类型 `p:ph` | 仅原生 Chart/Table 导出时为 `Native-stable` | 需要合法 JSON metadata 与 `--native-charts-and-tables` |
| 通用对象占位符 | 一个兼容 carrier，或显式复合 proxy binding | `obj` 类型 `p:ph` | 原生 binding；复合可见内容仍为普通 shape | 复合 slot 必须使用已登记 proxy 降级方案 |
| 媒体占位符 | 一个图片或受支持 crop carrier | `media` 类型 `p:ph` | 仅为原生占位符 binding | 不会从装饰性 SVG 内容生成视频或音频 |
| 空文本占位符 | 空或仅空白的已标记 text carrier | 使用合法 1 pt 下限的不可见 U+200B run，生成一个原生文本 shape | `Native-stable` | 不得添加假破折号、小于 1 pt 的文字或与背景同色的可见字符 |
| cover/content/ending 等页面角色 | flat 路线根 `data-pptx-page-role` 编译提示 | 路由/校验提示；不是 PowerPoint 原生页面类型 | 没有独立 OOXML 对象 | structured 页面改用显式 Master/Layout 身份 |
| 幻灯片节与自定义放映 | 无 SVG 映射 | 主生成路线不编写 | 当源保留工作流拥有该语义时为 `Direct preservation` | 不得编码为可见 metadata |

精确的结构 metadata 与 slot 语法见规范中的 [PPTX 结构章节](../../skills/ppt-master/references/shared-standards.md#pptx-structure-routing)。

内部标识符与 PowerPoint 显示名称是两件事：Master 和 Layout key 使用项目受限 ASCII 标识符语法，picker 名称可以含空格。每个 Layout 定义还必须指定父 Master 与一个显式原型来源。精确行语法由规范文档拥有。

## 3. PowerPoint 形状与绘图对象

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 矩形 | `<rect>` | 可编辑 `p:sp` 与 `a:prstGeom prst="rect"` | `Native-stable`；可能时回导为原语 | 仅使用已登记 paint、line 与 transform 属性 |
| 对称圆角矩形 | 圆角半径相等且受支持的 `<rect>` | `a:prstGeom prst="roundRect"` 加 adjustment | `Native-stable` | 不对称圆角按 freeform 行处理 |
| 圆或椭圆 | `<circle>` 或 `<ellipse>` | `a:prstGeom prst="ellipse"` | `Native-stable` | 需要时，bounds 和 radius 必须有限且为正 |
| 直线 | `<line>` | 可编辑 line/freeform shape | `Native-normalized` | 拒绝浏览器专属 line 效果 |
| 带箭头的线 | 带已登记起点/终点 marker 的 `<line>` 或受支持 path | 原生 DrawingML 线首/线尾 | `Native-normalized`；marker 大小为近似 | marker 定义必须遵循条件 marker 合同 |
| 原生连接符 | 带 connector metadata 的已创作 preset connector 片段 | `p:cxnSp` | 导入 connector 保留紧凑 metadata | 已登记 preset/connector schema 内为 `Native-stable` |
| 任意多边形 | `<path>` | 带 `a:custGeom` 的 `p:sp` | 导入自定义几何重建为 path | `Native-normalized`；SVG arc 转为三次曲线段 |
| 多边形 | `<polygon>` | 闭合自定义几何 | `Native-normalized` | points 必须有限且合法 |
| 折线 | `<polyline>` | 开放自定义几何 | `Native-normalized` | points 使用与其他生成几何相同的有限、已登记语法 |
| PowerPoint 预设形状 | 由 registry 生成的 authored preset 片段 | 一个可编辑 preset `p:sp` | preset 身份与 adjustment 可以经导入/导出保留 | 使用 [`preset_shape_svg.py`](../../skills/ppt-master/scripts/preset_shape_svg.py)；不得手工发明 metadata |
| 导入的预设形状 | 导入 metadata 加可见 SVG fallback | payload 合法且未改变时恢复 preset | 在导入合同内为 `Native-stable` | 不支持的 preset 保留为显式诊断 fallback，不猜测几何 |
| 动作按钮形状 | authored `actionButton*` preset 片段 | 仅生成可见 preset 几何 | 形状几何可往返 | 不创建单击动作、导航目标或超链接 |
| 组 | `<g>` | `p:grpSp`，或对特殊 carrier 执行文档化的 flatten/collapse | 分组内容可重建为 `<g>` | 结构 atom 与 placeholder 合同优先于普通分组 |
| 复用本地 symbol | 已登记的同文档 `<use>` 合同或项目 icon placeholder | 在生成 Slide 中展开为可编辑 shape | 回导不承诺恢复原 symbol 图 | 拒绝外部 use、不受支持的 symbol 能力和结构 metadata 复用 |
| 图标 | 由项目图标管线解析的 `<use data-icon="library/name">` | 展开后的可编辑矢量原语/组 | 重建几何，不恢复原图标库引用 | 图标标识区分大小写，必须存在于已同步图标库 |
| SmartArt / DiagramML | 无主 SVG 对象映射 | 主重设计路线可以用普通 shape 重建语义 | 原生/模板路线中为 `Direct preservation`，否则为 preview 或显式 fallback | 不得将装饰性组标记为原生 SmartArt |

preset 形状选择与精确原子片段合同见 [`native-shape-authoring.md`](../../skills/ppt-master/references/native-shape-authoring.md)。

## 4. PowerPoint 文本功能

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 文本框 | `<text>` | 带 `p:txBody` 的可编辑 `p:sp` | 重建为 `<text>`，需要时含 `<tspan>` | 文本必须是良构 XML，且仅使用已登记属性 |
| 行内混合格式 | 不带定位的 `<tspan>` run | 同一文本框内的 DrawingML run | `Native-normalized`；已登记 run 格式仍可编辑 | 改变文本框几何的定位可能会拆分结果 |
| 多段落 | 可合并的 text/tspan 结构 | 同一文本框内的多个 `a:p` 段落 | `Native-normalized` | 严格独立定位的行可保持为独立文本框 |
| 字体 | 根据项目 lock 解析的规范 `font-family` | 直接 typeface 或已登记 theme font | 在安装字体/替换边界内为 `Native-stable` | 校验会报告未锁定或不可用字体 |
| 字号 | 有限、无单位的 SVG px，例如 `font-size="24"` | DrawingML 百分之一磅；`1 px = 0.75 pt` | 单位转换后为 `Native-stable` | 生成创作只使用无单位 px；已登记历史单位是会产生 warning 的兼容输入，未知单位为 error；DrawingML 下限为 1 pt |
| 粗体、斜体、下划线与删除线 | `<text>`/`<tspan>` 上的已登记文本属性 | DrawingML run 属性 | `Native-stable` | 仅接受文档化取值 |
| 文本填充与透明度 | 规范 fill 加 run alpha | DrawingML run fill 与 alpha | `Native-normalized` | 使用语义 alpha 通道，不使用未登记 CSS 效果 |
| 文本轮廓 | 文本上已登记 stroke | DrawingML run outline | `Native-normalized` | 轮廓承载精细视觉意义时需复核 |
| 文本对齐 | `text-anchor` 与已登记段落语义 | 段落对齐加归一化文本框位置 | `Native-normalized` | 浏览器排版启发式不属于合同 |
| 文本框垂直对齐 | 无规范生成 SVG 控制；生成文本框使用顶部对齐 | 顶部对齐的 DrawingML text body | 导入的垂直文本可能被归一化，但主路线不公开通用创作控制 | 不得从 SVG baseline 或浏览器排版行为推断垂直对齐 |
| 字符间距 | 已登记 `letter-spacing` | DrawingML 字符间距 | `Native-normalized` | 拒绝不受支持的 CSS 排版 |
| 项目符号段落 | 已识别的前导项目符号形式 | 原生 DrawingML bullet | `Native-normalized` | 仅提升已登记 bullet 语法 |
| 旋转文本 | 文本对象上受支持的 transform | 旋转文本 shape | `Native-normalized` | 倾斜文本与浏览器专属 transform 不受支持 |
| 文本阴影或发光 | 受支持 filter/effect 合同 | 一个原生外阴影或发光 | `Approximate` | 仅支持一个已登记效果图；实质效果需复核 |
| WordArt、文本变形或沿路径文本 | 无已登记主路线映射 | 不生成原生 WordArt | `Bake-required` 或使用普通文本/几何重建 | 浏览器可渲染不代表 PowerPoint 受支持 |

## 5. PowerPoint 图片功能

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 图片 | 引用项目资产或 data URI 的 `<image>` | `p:pic`、media part 与 relationship | 重建为 `<image>` | 源必须可解析，尺寸必须合法 |
| 图片拉伸填满框 | `preserveAspectRatio="none"` | 原生拉伸 picture frame | `Native-stable` | `none` 必须单独出现；它会有意改变源宽高比 |
| 图片裁剪填充 | 一个已登记对齐值加显式 `slice` | 原生 `a:srcRect` 裁剪 | 源尺寸可读时为 `Native-stable` | 对齐值区分大小写；未知模式与额外 token 为 error |
| 图片适应框 | 省略时使用默认值，或一个已登记对齐值加显式 `meet` | 原生 fitted picture frame | `Native-normalized` | 仅写对齐值是兼容输入，Checker 会给出规范化建议 |
| 图片透明度 | 原子 image `opacity` | 原生 `a:alphaModFix` | `Native-stable` | 值必须有限，并在可接受 opacity 语法内 |
| 图片裁成形状 | 仅作用于 image 的已登记 `clip-path` | picture preset 或 custom geometry | `Native-normalized` | 不接受任意 mask |
| 导入的裁剪图片 | 导入器产生的嵌套 crop SVG 表达 | 重新导出为原生 `a:srcRect` | crop 合同内为 `Native-stable` | 不得手工将嵌套 SVG 泛化为不受限功能 |
| 图片重着色、艺术滤镜、模糊或复杂 mask | 无通用创作映射 | 使用受支持 overlay 重建或预渲染 | `Bake-required` | 任意 SVG filter 和 blend mode 违反主合同 |

## 6. PowerPoint 填充、线条与效果功能

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 无填充 | `fill="none"` | `a:noFill` | `Native-stable` | 生成 SVG 使用小写规范拼法 |
| 纯色填充 | 已锁定规范 `fill="#RRGGBB"` | `a:solidFill`；当锁定角色可精确复用时使用 theme token | `Native-stable` | 兼容颜色拼法可产生 warning；格式错误或生成未锁定值失败 |
| 填充透明度 | 不透明 fill 加 `fill-opacity` | 原生 alpha | `Native-stable` | 生成值为 0 到 1 的有限无单位数 |
| 线性渐变填充 | `<defs>` 中已登记 `<linearGradient>` | 原生 `a:gradFill` | `Native-normalized` | stop、坐标、transform 与引用必须遵循封闭合同 |
| 径向渐变填充 | 已登记 `<radialGradient>` | 居中圆形 DrawingML 渐变 | `Approximate` | 对焦点/半径敏感的设计需复核 |
| 图案填充 | 带注解的项目 pattern 定义 | 原生 `a:pattFill` | `Native-normalized` | 仅支持已登记 PowerPoint 预设 pattern |
| 无轮廓 | `stroke="none"` 或已登记线缺省 | `a:ln` 内的 `a:noFill` | `Native-stable` | 不得用零线宽模糊 CSS 模拟缺省 |
| 实线轮廓 | 已登记 `stroke` 与宽度 | 原生 `a:ln` | `Native-stable` | 宽度与 paint 必须使用规范单位/语法 |
| transform 下的轮廓缩放 | 精确的 `vector-effect="none"` 或 `vector-effect="non-scaling-stroke"` | 选择被解析为原生线宽 | `Native-normalized` | 拒绝其他取值；生成拼法必须精确且为小写 |
| 虚线或点线轮廓 | 已登记 dash array | 预设或自定义 DrawingML dash | `Native-normalized` | 拒绝不支持的 dash 语义 |
| 线端与连接样式 | 已登记 cap/join 值 | 原生 line cap/join 属性 | `Native-stable` | 仅接受文档化取值 |
| 线条箭头 | 已登记起点/终点 marker | 原生 head/tail end 属性 | marker 大小为 `Approximate` | 见条件 marker 合同 |
| 外阴影 | 一个受支持 shadow filter 图 | `a:effectLst` 中的原生外阴影 | `Approximate` | 不会默默简化不支持的图结构 |
| 发光 | 一个受支持 glow filter 图 | `a:effectLst` 中的原生发光 | `Approximate` | 发光承载语义强调时需复核 |
| 整个对象透明度 | 原子元素 `opacity` | alpha 分发至受支持原生通道 | `Native-normalized` | 除非整个原子对象需要淡出，否则优先通道专属 alpha |
| 组透明度 | 兼容 `<g opacity>` | 后代归一化近似 | `Approximate`，并产生 warning | 生成 SVG 应优先后代 alpha |
| 内阴影、柔化边缘、倒影、模糊、湍流、混合模式或任意 mask | 无已登记原生映射 | 显式几何替代或栅格资产 | `Bake-required` | 转换器和 Checker 不得发明视觉降级方案 |

## 7. PowerPoint 表格

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 视觉绘制表格 | 普通 SVG shape、line 与 text | 相互独立的可编辑 PowerPoint shape | 保真度遵循各组件对应行 | 它不是原生表格，也没有 PowerPoint 表格编辑模型 |
| PowerPoint 原生表格 | 一个带 `<metadata type="application/json">` 和可见 fallback 的 `<g data-pptx-replace-with="table">` | 启用原生 Chart/Table 替换时产生含 `a:tbl` 的 `p:graphicFrame` | 导入受支持表格重建 fallback 加替换 metadata | metadata 必须形成已登记矩形 schema；需要 `--native-charts-and-tables` |
| 合并表格单元格 | 规范原生表格 merge metadata | 原生水平/垂直合并语义 | 封闭 schema 内为 `Native-stable` | 拒绝重叠、歧义或非矩形合并 |
| 表格单元格格式 | 已登记原生表格单元格格式字段 | 原生单元格 fill、border、text 与 alignment | `Native-normalized` | 不猜测封闭 schema 以外的字段 |
| 不受支持的原生表格功能 | SVG fallback 或直接源保留 | 保留可见 fallback，或在直接路线保留源 OOXML | 显式 fallback / `Direct preservation` | 不得临时扩展 JSON |

PowerPoint 原生 Chart/Table 对象是可选功能。默认导出保留 SVG fallback，并转换为仍可独立编辑的 DrawingML shape，以保持视觉稳定；原生导出改为提供对象的数据源以及图表/表格专属编辑模型，并可能归一化外观。

导入的图表组使用 `data-pptx-fallback-kind="source-preview|normalized|placeholder"` 对可见 fallback 分类；其中 `placeholder` 自身即表示仅用于重建的 fallback。`data-pptx-replacement-status` 则记录 fallback-only 图表或表格导入无法提出有效替换声明的原因。该合同下的导入组均使用 `data-pptx-import-source="pptx"`，有效声明还可携带 `data-pptx-fallback-sha256` 防止陈旧 metadata 覆盖后续视觉编辑。旧 `data-pptx-native*`、`data-pptx-visual-status` 和 `data-pptx-route-status` 写法仍可读，但不再是规范创作格式。

## 8. PowerPoint 图表

| PowerPoint 功能 | 项目表达 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 视觉绘制图表 | 普通 SVG 几何与文本 | 相互独立的可编辑 PowerPoint shape | 保真度遵循各组件对应行 | 没有“编辑数据”工作簿 |
| PowerPoint 原生经典图表 | 一个带 `<metadata type="application/json">` 已登记 JSON 数据和可见 fallback 的 `<g data-pptx-replace-with="chart">` | `p:graphicFrame`、经典 chart part 与嵌入工作簿 | 受支持的导入重建 fallback 加替换 metadata | chart type 与数据必须匹配封闭 schema；需要 `--native-charts-and-tables` |
| 原生 ChartEx 图表 | 具有受支持 ChartEx family 的相同 marker 接口 | `cx:chart` part 与嵌入工作簿 | 受支持 family 可按语义重建 | 仅接受已登记 family/field 组合 |
| 图表标题、图例、坐标轴、标签与系列格式 | 已登记原生图表 metadata | 原生 chart 属性 | `Native-normalized` | 精确字段与受支持 family 仍以 `shared-standards.md` 为规范 |
| 图表说明、来源或脚注 | replacement marker 之外的普通伴随 SVG text | 图表旁边可编辑的 Slide 文本框 | 作为文本时为 `Native-stable` | 不得把 Slide 文案隐藏在 chart JSON 里 |
| 已编辑 SVG fallback 与过期替换 metadata | 更新后的可见 SVG 加过期 hash | 默认导出保留可见 SVG；原生替换失败 | 显式安全行为 | 编译器绝不默默丢弃更新的视觉编辑 |
| 不支持的 3D 或延后图表 family | SVG 绘制图表、烘焙资产或直接源保留 | 不猜测原生图表 | fallback / `Direct preservation` | 不支持的 alias 必须使原生校验失败 |

完整图表/表格 schema 和受支持 family 列表有意仅保留在[规范化替换合同](../../skills/ppt-master/references/shared-standards.md#powerpoint-native-chart--table-replacement-markers-opt-in)中。

## 9. PowerPoint 播放与打包功能

这些能力属于 PPTX 包语义。它们不出现在页面 SVG 中是有意设计。

| PowerPoint 功能 | 项目中的所有者 | PPTX 结果 | 回导与保真度 | 校验边界 |
|---|---|---|---|---|
| 演讲者备注 | `notes/<slide>.md` sidecar | Notes Slide part 与 relationship | `Sidecar/package` | 备注不是 SVG 文本，不影响页面几何 |
| 幻灯片切换 | CLI 选项或 `animations.json` | `p:transition` | `Sidecar/package` | 未知效果或非法时长失败；不默默 fallback 到 `fade` |
| 对象进入动画 | `animations.json`，目标为稳定的顶层 SVG group ID | 根 `p:timing` 动画树 | `Sidecar/package`；group ID 仅为目标锚点 | 静态结构层与占位符不可动画 |
| 旁白音频 | `audio/` 资产加 recorded-narration 导出选项 | media relationship、audio carrier 与 timing | `Sidecar/package` | 必须校验资产、Slide 关联与时序 |
| 幻灯片自动换页 | 显式 transition timing 或旁白派生时长 | `advTm`/换页行为 | `Sidecar/package` | 单击驱动动画与录制旁白不兼容 |
| 超链接或动作 | 无主 SVG 编译器映射 | 不由页面 SVG 创建 | 原生路线保留源 OOXML 时为 `Direct preservation` | action-button preset 只提供可见几何 |
| 批注或审阅线程 | 无 SVG 或生成侧映射 | 不编写 | 仅在其他路线明确拥有时为 `Direct preservation` | 不自动将审阅 metadata 转为可见 Slide 内容 |
| 不属于已映射功能的 relationship | 无通用 SVG 逃生口 | 不生成 | 适用时为 `Direct preservation` | 不支持任意 relationship 注入 |

sidecar 工作流见 [`animations.md`](../../skills/ppt-master/references/animations.md) 与 [`audio-narration.md`](./audio-narration.md)。

## 10. 其他 PowerPoint 原生功能

| PowerPoint 功能 | 主路线状态 | 受支持的替代方案 | 边界 |
|---|---|---|---|
| SmartArt / DiagramML | 无原生 SVG 编译器映射 | 使用 shape 重建语义，或通过原生/模板路线保留 | 截图或 fallback 必须是显式的 |
| OLE 或嵌入 Office 对象 | SVG 路线不支持 | 直接保留或渲染 preview | 不得通过 SVG metadata 制造包 relationship |
| 原生公式 / OMML | SVG 路线不支持 | 渲染公式资产或直接保留原生 OOXML | 渲染公式是图片，不是可编辑公式 |
| 视频 | 不支持作为 SVG 创作媒体对象 | 直接保留，或本合同之外的显式封面/链接工作流 | `media` 占位符不创建视频 |
| 3D 模型 | 不支持 | 直接保留或烘焙 preview | 不将浏览器 SVG 近似当作原生 3D |
| 宏 / VBA | 不支持 | 仅通过感知宏的直接工作流保留 | 普通生成 `.pptx` 路线不生成 VBA |
| 任意 Office 扩展 XML | 不支持 | 由拥有该语义的原生工作流直接保留 | SVG 编译器不提供通用 OOXML 透传 |

## 11. 反向映射：PPTX 到项目 SVG

导入器将受支持的 PowerPoint 语义重建为与导出相同的项目词汇：

| PowerPoint 源对象 | 项目 SVG 重建 |
|---|---|
| 预设形状 | SVG 原语/path，受支持时加紧凑 preset metadata |
| 自定义几何 | `<path>` |
| 文本体 | `<text>` 与 `<tspan>` run/段落 |
| 图片 | `<image>`，或已登记嵌套 crop 表达 |
| 连接符 | 线/path 加 connector metadata |
| 组 | `<g>` |
| 受支持原生表格/图表 | 可见 fallback 加原生对象 metadata |
| 不支持的 graphic frame 或 SmartArt | 显式 preview、placeholder 或 unsupported 状态 |

这是语义重建，不是语法往返。Master/Layout 恢复属于模板结构工作流；普通视觉导入不会从 Slide 外观推断可复用拓扑。

## 12. 校验职责

三层有意承担不同职责：

| 层 | 职责 |
|---|---|
| 提示词、模板与示例 | 对每项 PowerPoint 功能只生成规范表达 |
| `svg_quality_checker.py` | 拒绝非法/不支持映射；对已登记兼容拼法或保真风险给出 warning 但允许继续 |
| `svg_to_pptx.py` 与最终包读回 | 归一化兼容输入、编译 DrawingML，并拒绝任何会产生歧义、结构不一致或非法结果的输出 |

warning 不是猜测许可。它只适用于拥有唯一结果的受支持映射，但其拼法或保真度值得注意的情况。缺失映射、非法单位、格式错误 metadata、破损的结构合同，以及可能触发 PowerPoint 修复的 DrawingML 都是 error。

## 13. 新增或修改映射

应将映射变更视为编译器变更，而不是宽松 SVG parser 调整：

1. 命名 PowerPoint 能力与预期的可编辑 DrawingML 结果。
2. 在 [`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md) 中定义一种规范项目 SVG 或 sidecar 表达。
3. 将可接受兼容输入与生成创作分开声明。
4. 实现导出；仅当支持语义重建时实现导入。
5. 增加 Checker 分类：非法/歧义输入为 error，只有结果确定的兼容或近似输入可为 warning。
6. 对生成 SVG、PPTX 包、PowerPoint 渲染，以及适用时的反向导入执行聚焦回归验证。
7. 同步更新本指南中对应的英文与中文行。

实现入口：

- 导出：[`svg_to_pptx.py`](../../skills/ppt-master/scripts/svg_to_pptx.py) 与 `scripts/svg_to_pptx/`
- 导入：[`pptx_to_svg.py`](../../skills/ppt-master/scripts/pptx_to_svg.py) 与 `scripts/pptx_to_svg/`
- 校验：[`svg_quality_checker.py`](../../skills/ppt-master/scripts/svg_quality_checker.py)
- 规范合同：[`shared-standards.md`](../../skills/ppt-master/references/shared-standards.md)
