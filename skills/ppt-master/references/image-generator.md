# Image_Generator 参考手册

> 本文件为 Image_Generator 角色的精简参考。通用标准（SVG 技术约束、画布格式、后处理流程等）见 [shared-standards.md](./shared-standards.md)。

## 核心使命

接收 Strategist 输出的《设计规范与内容大纲》中的「图片资源清单」，为每张待生成的图片创建优化提示词，并通过 AI 工具生成图片，保存到项目 `images/` 目录。

**触发条件**: 需要生成 AI 图片时（独立使用或流程中调用）

| 模式 | 触发方式 | 说明 |
|------|----------|------|
| **独立使用** | 直接说明图片需求 | 生成单张或多张 AI 图片 |
| **流程中使用** | `generate-ppt` 选择 AI 生成图片 | 为项目批量生成图片资源 |

> 流程中下一步：Executor 生成 SVG

---

## 1. 输入与输出

### 输入

- **设计规范与内容大纲**（来自 Strategist）：项目主题、目标受众、设计风格、配色方案、画布格式
- **图片资源清单**（关键输入）：

  | 文件名 | 尺寸 | 用途 | 类型 | 状态 | 生成描述 |
  |--------|------|------|------|------|----------|
  | cover_bg.png | 1920x1080 | 封面背景 | 背景图 | 待生成 | 现代科技感抽象背景，深蓝渐变 |

### 输出

| 产出物 | 路径/说明 | 要求 |
|--------|-----------|------|
| 提示词文档 | `项目/images/image_prompts.md` | **必须**用文件写入工具保存，不能仅在对话中输出 |
| 优化提示词 | 每张图片独立提示词 | 可直接用于 AI 图像生成工具，兼做 alt 文本 |
| 图片文件 | `项目/images/` 目录 | 按清单文件名命名 |
| 更新后的清单 | 状态变更 | 「待生成」→「已生成」 |

---

## 2. 统一提示词结构

### 2.1 标准输出格式

每张图片必须按以下格式输出：

```markdown
### 图片 N: {文件名}

| 属性     | 值                                   |
| -------- | ------------------------------------ |
| 用途     | {在哪页/承担什么功能}                |
| 类型     | {背景图/插画/实景照片/图表/装饰图案} |
| 尺寸     | {宽}x{高} ({宽高比})                 |
| 原始描述 | {用户在清单中提供的描述}             |

**提示词 (Prompt)**:
{主体描述}, {风格指令}, {色彩指令}, {构图指令}, {质量指令}

**负面提示词 (Negative Prompt)**:
{需要排除的元素}

**图片描述 (Alt Text)**:
> {中文描述，用于无障碍访问和图片说明}
```

### 2.2 提示词组成要素

| 要素 | 说明 | 示例 |
|------|------|------|
| 主体描述 | 核心内容 | `Abstract geometric shapes`, `Team collaboration scene` |
| 风格指令 | 视觉风格 | `flat design`, `3D isometric`, `watercolor style` |
| 色彩指令 | 配色方案 | `color palette: navy blue (#1E3A5F), gold (#D4AF37)` |
| 构图指令 | 布局比例 | `16:9 aspect ratio`, `centered composition` |
| 质量指令 | 分辨率质量 | `high quality`, `4K resolution`, `sharp details` |
| 负面提示词 | 排除元素 | `text, watermark, blurry, low quality` |

### 2.3 风格关键词速查

| 设计风格 | 推荐图片风格 | 核心关键词 |
|----------|-------------|------------|
| 通用灵活 | 现代插画、扁平设计 | `modern`, `flat design`, `gradient`, `vibrant colors` |
| 一般咨询 | 简洁专业、商务风 | `professional`, `clean`, `corporate`, `minimalist` |
| 顶级咨询 | 高端简约、抽象几何 | `premium`, `sophisticated`, `geometric`, `abstract`, `elegant` |

### 2.4 色彩整合方法

从设计规范提取配色，转换为提示词：

```
主导色: #1E3A5F (深海蓝)   →  "deep navy blue (#1E3A5F)"
辅助色: #F8F9FA (浅灰)     →  "light gray (#F8F9FA)"
强调色: #D4AF37 (金)       →  "gold accent (#D4AF37)"

完整指令: "color palette: deep navy blue (#1E3A5F), light gray (#F8F9FA), gold accent (#D4AF37)"
```

### 2.5 画布格式与宽高比

| 画布格式 | 背景图宽高比 | 建议分辨率 |
|----------|-------------|------------|
| PPT 16:9 | 16:9 | 1920x1080 或 2560x1440 |
| PPT 4:3 | 4:3 | 1600x1200 |
| 小红书 | 3:4 | 1242x1660 |
| 朋友圈 | 1:1 | 1080x1080 |
| Story | 9:16 | 1080x1920 |

> Nano Banana 支持的宽高比：`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

---

## 3. 图片类型分类与处理

### 类型判断流程

1. 全页/大面积铺底 → **背景图** (3.1)
2. 真实场景/人物/产品 → **实景照片** (3.2)
3. 扁平/插画/卡通风格 → **插画配图** (3.3)
4. 流程/架构/关系 → **图表/架构图** (3.4)
5. 局部装饰/纹理 → **装饰图案** (3.5)

### 3.1 背景图 (Background)

**识别特征**: 封面、章节页的全页背景，需承载文字叠加

| 要点 | 说明 |
|------|------|
| 强调背景属性 | 添加 `background`, `backdrop` |
| 预留文字区域 | `negative space in center for text overlay` |
| 避免强主体 | 使用抽象、渐变、几何元素 |
| 低对比细节 | `subtle`, `soft`, `muted` |

**模板**: `Abstract {主题元素} background, {风格} style, {主色} to {辅色} gradient, subtle {装饰元素}, clean negative space in center for text overlay, {宽高比} aspect ratio, high resolution, professional presentation background`

**负面提示词**: `text, letters, watermark, faces, busy patterns, high contrast details`

### 3.2 实景照片 (Photography)

**识别特征**: 真实场景、人物、产品、建筑等照片质感

| 要点 | 说明 |
|------|------|
| 强调真实感 | `photography`, `photorealistic`, `real photo` |
| 光影效果 | `natural lighting`, `soft shadows`, `studio lighting` |
| 背景处理 | `white background` / `blurred background` / `contextual setting` |
| 人物多样性 | `diverse`, `professional attire` |

**模板**: `{主体描述}, professional photography, {光影类型} lighting, {背景类型} background, color grading matching {配色方案}, high quality, sharp focus, 8K resolution`

**负面提示词**: `watermark, text overlay, artificial, CGI, illustration, cartoon, distorted faces`

### 3.3 插画配图 (Illustration)

**识别特征**: 扁平设计、矢量风格、卡通、概念图解

| 要点 | 说明 |
|------|------|
| 明确风格 | `flat design`, `isometric`, `vector style`, `hand-drawn` |
| 简化细节 | `simplified`, `clean lines`, `minimal details` |
| 统一色板 | 严格使用设计规范配色 |
| 背景选择 | `white background` 或 `transparent background` |

**模板**: `{主体描述}, {插画风格} illustration style, {细节程度} with clean lines, color palette: {配色列表}, {背景类型} background, professional {用途} illustration`

**负面提示词**: `realistic, photography, 3D render, complex textures, watermark`

### 3.4 图表/架构图 (Diagram)

**识别特征**: 流程图、架构图、概念关系图、数据可视化

| 要点 | 说明 |
|------|------|
| 清晰结构 | `clear structure`, `organized layout`, `logical flow` |
| 连接表示 | `arrows indicating flow`, `connecting lines` |
| 学术/专业感 | `suitable for academic publication`, `professional diagram` |
| 浅色背景 | `white background` 或 `light gray background` |

**模板**: `{图表类型} diagram showing {内容描述}, {组件描述} connected by {连接方式}, {风格} style with {配色方案}, white background, clear labels, professional technical diagram`

**负面提示词**: `cluttered, messy, overlapping elements, dark background, realistic, photography`

### 3.5 装饰图案 (Decorative Pattern)

**识别特征**: 局部装饰、纹理、边框、分隔元素

| 要点 | 说明 |
|------|------|
| 可重复性 | `seamless`, `tileable`, `repeatable`（如需要） |
| 低调辅助 | `subtle`, `understated`, `supporting element` |
| 透明友好 | `transparent background` 或 `isolated element` |
| 小尺寸适用 | 考虑在小尺寸下的可识别性 |

**模板**: `{图案类型} decorative pattern, {风格} style, {配色方案}, {背景类型} background, subtle and elegant, suitable for {用途}`

**负面提示词**: `busy, cluttered, high contrast, distracting, photorealistic`

---

## 4. 图片生成工作流

### 4.1 分析阶段

1. 阅读设计规范，理解项目整体风格
2. 提取配色方案、画布格式、目标受众
3. 逐一分析图片资源清单中的每张图片
4. 判断每张图片的类型（参考第 3 节）

### 4.2 提示词生成阶段

对每张「待生成」状态的图片：

1. **判断类型** → 背景图/实景照片/插画/图表/装饰
2. **理解用途** → 在哪页？承担什么功能？
3. **分析原始描述** → 用户「生成描述」中的信息
4. **应用类型要点** → 参考对应类型的表格
5. **生成优化提示词** → 使用 2.1 统一输出格式
6. **保存提示词文档** → **必须**写入 `项目/images/image_prompts.md`

### 4.3 图片生成阶段

> 前置条件：必须先完成 4.2，确保 `images/image_prompts.md` 已创建

#### 方式一：Nano Banana 命令行工具（推荐）

```bash
python3 scripts/nano_banana_gen.py "你的提示词" \
  --aspect_ratio 16:9 --image_size 1K \
  --output 项目/images --filename cover_bg
```

**参数列表**:

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `prompt` | - | 正向提示词（位置参数） | `Nano Banana` |
| `--negative_prompt` | `-n` | 负面提示词 | 无 |
| `--aspect_ratio` | - | 图片宽高比 | `1:1` |
| `--image_size` | - | 尺寸 (`1K`/`2K`/`4K`) | `1K` |
| `--output` | `-o` | 输出目录 | 当前目录 |
| `--filename` | `-f` | 输出文件名（不含扩展名） | 自动命名 |

**环境变量**: 必需 `GEMINI_API_KEY`，可选 `GEMINI_BASE_URL`

**生成节奏控制（强制）**:
- 每次只执行一个生成命令，等待确认文件落盘后再执行下一条
- 建议每张间隔 2-5 秒，避免并发导致失败
- 如出现失败/无输出，先停止队列，检查环境变量与输出目录，再继续

#### 方式二：自动生成

直接调用图像生成 API，下载并保存到 `项目/images/` 目录。

#### 方式三：Gemini 网页版

1. 在 [Gemini](https://gemini.google.com/) 中生成图片
2. 选择 **Download full size** 下载高分辨率版本
3. 去水印：`python3 scripts/gemini_watermark_remover.py <图片路径>`
4. 将处理后的图片放入 `项目/images/` 目录

#### 方式四：手动生成（其他 AI 平台）

提示词已保存在 `images/image_prompts.md`，告知用户文件位置。用户自行到 Midjourney、DALL-E、Stable Diffusion、文心一格、通义万相等平台生成，将图片放入 `项目/images/` 目录。

### 4.4 验证阶段

- 确认所有图片已保存到 `images/` 目录
- 检查文件名与清单一致
- 更新图片资源清单状态为「已生成」

---

## 5. 提示词文档模板

创建 `项目/images/image_prompts.md` 时使用以下结构：

```markdown
# 图片生成提示词

> 项目: {项目名称}
> 生成时间: {日期}
> 配色方案: 主导色 {#HEX} | 辅助色 {#HEX} | 强调色 {#HEX}

---

## 图片清单总览

| # | 文件名 | 类型 | 尺寸 | 状态 |
|---|--------|------|------|------|
| 1 | cover_bg.png | 背景图 | 1920x1080 | 待生成 |

---

## 详细提示词

### 图片 1: cover_bg.png

| 属性 | 值 |
|------|----|
| 用途 | 封面背景 |
| 类型 | 背景图 |
| 尺寸 | 1920x1080 (16:9) |
| 原始描述 | 现代科技感抽象背景，深蓝渐变 |

**提示词 (Prompt)**:
Abstract futuristic background with flowing digital waves...

**图片描述 (Alt Text)**:
> 现代科技感抽象背景，深蓝色渐变配合数字波浪和粒子效果

---

## 使用说明

1. 复制上方「提示词」到 AI 图像生成工具
2. 推荐平台: Midjourney / DALL-E 3 / Gemini / Stable Diffusion
3. 生成后将图片重命名为对应文件名
4. 放入 `images/` 目录
```

---

## 6. 负面提示词速查

### 按图片类型

| 类型 | 推荐负面提示词 |
|------|---------------|
| 背景图 | `text, letters, watermark, faces, busy patterns, high contrast details` |
| 实景照片 | `watermark, text overlay, artificial, CGI, illustration, cartoon, distorted faces` |
| 插画配图 | `realistic, photography, 3D render, complex textures, watermark` |
| 图表/架构图 | `cluttered, messy, overlapping elements, dark background, realistic` |
| 装饰图案 | `busy, cluttered, high contrast, distracting, photorealistic` |

### 通用负面提示词

- **标准版**: `text, watermark, signature, blurry, distorted, low quality`
- **扩展版**（人物场景）: `text, watermark, signature, blurry, low quality, distorted, extra fingers, mutated hands, poorly drawn face, bad anatomy, extra limbs, disfigured, deformed`

---

## 7. 常见问题

### 无「生成描述」时的默认推断

| 用途 | 默认推断 |
|------|----------|
| 封面背景 | 抽象渐变背景，预留中央文字区域 |
| 章节页背景 | 简洁几何图案，侧重单色调 |
| 团队介绍页 | 团队协作场景插图（扁平风格） |
| 数据展示页 | 简洁几何图案或纯色背景 |
| 产品展示 | 产品实拍风格，白底或渐变背景 |

### 图片不满意时

提供提示词变体供用户选择：变体 A（更抽象）、变体 B（更具象）、变体 C（不同色调）。

---

## 8. 角色协作

### 与 Strategist 的衔接

| 方向 | 内容 |
|------|------|
| 接收 | 设计规范与内容大纲（含图片资源清单） |
| 触发条件 | 用户在「图片使用」中选择包含「C) AI 生成」 |
| 关键信息 | 配色方案、设计风格、画布格式 |

### 与 Executor 的衔接

| 方向 | 内容 |
|------|------|
| 交付 | 所有图片已放入 `项目/images/` 目录 |
| Executor 引用 | `<image href="../images/xxx.png" .../>` |
| 路径说明 | SVG 在 `svg_output/`，图片在 `images/`，使用相对路径 `../images/` |

---

## 9. 任务完成检查点

### 必须完成项

- [ ] 已创建提示词文档 `项目/images/image_prompts.md`
- [ ] 每张图片都有：类型判断 + 优化提示词 + 负面提示词 + Alt Text
- [ ] 使用统一输出格式（2.1 标准格式）
- [ ] 已输出阶段完成确认

### 图片就绪项（至少满足一项）

- [ ] 所有图片已保存到 `项目/images/` 目录
- [ ] 或：已明确告知用户使用 `image_prompts.md` 自行生成

### 流程流转

- [ ] 已提示用户进入下一步（切换到 Executor 角色）

> **关键检查**: 如果 `images/image_prompts.md` 未创建，或输出格式不符合 2.1 标准，任务未完成。

### 完成确认输出格式

```markdown
## Image_Generator 阶段完成

- [x] 已创建提示词文档 `项目/images/image_prompts.md`
- [x] 已为 X 张图片生成优化提示词
- [x] 所有图片已保存到 `images/` 目录
- [x] 已更新图片资源清单状态

**图片状态汇总**:

| 文件名 | 类型 | 尺寸 | 状态 |
|--------|------|------|------|
| cover_bg.png | 背景图 | 1920x1080 | 已生成 |

**下一步**: 切换到 Executor 角色开始生成 SVG
```
