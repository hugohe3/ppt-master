---
description: 根据源材料完成大纲与素材准备的独立工作流（第一阶段）
---

# 大纲与素材准备工作流

> 📖 **调用角色**：[Strategist](../../roles/Strategist.md) / [Image_Generator](../../roles/Image_Generator.md)
>
> ⚠️ **执行前置要求**：先阅读 [AGENTS.md](../../AGENTS.md)。本文件只补充第一阶段的具体步骤与附加约束，不重复全局规则。

本工作流负责第一阶段：将源材料整理为可执行的《设计规范与内容大纲》，并在需要时完成图片生成，使项目进入可执行状态。

## 流程概览

```
源材料转换 → 创建项目 → 归档 sources → 模板选项确认 → Strategist → outline_quality_checker → 大纲审阅确认 → [Image_Generator] → 素材就绪
```

## 执行步骤

### 步骤 1：源材料转换

当用户提供 PDF 或 URL 时，必须先转换再进入项目流程：

```bash
python3 tools/pdf_to_md.py "<PDF文件路径>"
python3 tools/web_to_md.py "<URL>"
node tools/web_to_md.cjs "<URL>"
```

- PDF 优先使用 `pdf_to_md.py`
- 普通网页优先使用 `web_to_md.py`
- 微信或高防站点优先使用 `web_to_md.cjs`

### 步骤 2：创建项目

```bash
python3 tools/project_manager.py init "<项目名称>" --format ppt169
```

- 项目必须先创建，再继续模板与策略阶段
- 如有源材料，立即归档到项目目录

```bash
python3 tools/project_manager.py import-sources "<项目路径>" "<源文件或URL>"
```

### 步骤 3：模板选项确认

在进入 Strategist 前，必须先确认是否使用现有模板：

- A. 使用已有模板
- B. 不使用模板，自由生成

若选择 A：

- 模板 SVG 和 `design_spec.md` 放入 `<项目路径>/templates/`
- 模板图片资源放入 `<项目路径>/images/`
- Strategist 必须吸收模板的配色、布局和风格约束

### 步骤 4：Strategist

进入 Strategist 前，必须先阅读 [Strategist](../../roles/Strategist.md)。

Strategist 阶段必须完成：

1. 八项确认：画布、页数、受众、风格、配色、图标、图片、排版
2. 如图片方式包含用户提供图片，先运行：

```bash
python3 tools/analyze_images.py "<项目路径>/images"
```

3. 生成《设计规范与内容大纲》
4. 保存到 `<项目路径>/设计规范与内容大纲.md`

### 步骤 5：大纲检查与审阅

```bash
python3 tools/outline_quality_checker.py "<项目路径>"
```

- 未通过检查前，不得进入渲染阶段
- 大纲必须包含完整页面执行卡
- 允许在此阶段独立审阅、修改和确认大纲

### 步骤 6：Image_Generator（条件触发）

触发条件：图片方式包含「C) AI 生成」（如 C、B+C、C+D）。

进入 Image_Generator 前，必须先阅读 [Image_Generator](../../roles/Image_Generator.md)。

本阶段应完成：

1. 从大纲中提取待生成图片清单
2. 生成 `images/image_prompts.md`
3. 完成图片生成或明确交付给用户手动生成
4. 确认所有执行所需图片已经进入 `images/`

常用命令：

```bash
python3 tools/nano_banana_gen.py "现代科技感背景" --aspect_ratio 16:9 --image_size 1K -o "<项目路径>/images"
```

## 产出物

- `设计规范与内容大纲.md`
- `images/` 中已准备完成的图片资源（如需要）
- `sources/` 中归档后的源材料

## 关键原则

1. 本工作流结束时，不要求已经生成 SVG。
2. 大纲必须通过 `python3 tools/outline_quality_checker.py <项目路径>`。
3. 大纲可以先独立审阅、修改、确认。
4. 若图片方式包含 AI 生成，应在本阶段内完成 Image_Generator，再把项目交给渲染阶段。
5. 渲染阶段默认假设：大纲和图片素材都已经就绪。

## 本工作流附加约束

1. 本阶段允许回查 `sources/`，但输出必须沉淀为《设计规范与内容大纲》与图片资源清单，不能把隐性判断留到渲染阶段。
2. 若使用模板，模板风格约束必须在本阶段吸收到大纲中，而不是让 Executor 再自行推断。
3. 若图片方案是用户提供或 AI 生成，本阶段结束前必须让 `images/` 达到可执行状态。

## 完成检查点

```markdown
## ✅ 第一阶段完成

- [x] 已完成源材料转换与归档
- [x] 已创建项目并确认模板选项
- [x] 已完成 Strategist 八项确认
- [x] 已生成《设计规范与内容大纲》
- [x] 已通过 `outline_quality_checker.py`
- [x] 图片素材已就绪（如需要）
- [ ] **下一步**: 进入 `render-from-outline`
```

## 下一步

- 若仅需完成内容规划或素材准备，到此结束。
- 若需继续生成 PPT，请进入 [render-from-outline.md](./render-from-outline.md)。
- 若想一键串联完整流程，可使用 [generate-ppt.md](./generate-ppt.md)。
