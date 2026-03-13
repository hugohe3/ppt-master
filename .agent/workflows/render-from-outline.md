---
description: 基于已完成的大纲与素材生成 SVG、讲稿与 PPT 的独立工作流（第二阶段）
---

# 基于大纲渲染工作流

> 📖 **调用角色**：Executor / Optimizer_CRAP
>
> ⚠️ **执行前置要求**：先阅读 [AGENTS.md](../../AGENTS.md)。本文件只补充第二阶段的具体步骤与附加约束，不重复全局规则。

本工作流只负责第二阶段：以现成的《设计规范与内容大纲》和已准备完成的素材为输入，生成 SVG、讲稿并导出 PPT。

## 流程概览

```
读取项目与大纲 → outline_quality_checker → Executor → total_md_split → finalize_svg → svg_to_pptx
```

## 执行步骤

### 步骤 1：执行前校验

进入渲染前，必须确认：

```bash
python3 tools/project_manager.py validate "<项目路径>" --stage outline
python3 tools/outline_quality_checker.py "<项目路径>"
```

- 大纲已经确认
- 所需素材已经在 `images/` 中准备完成
- 本阶段不再负责图片生成

### 步骤 2：Executor

进入 Executor 前，必须阅读所选角色文件：

```text
roles/Executor_General.md
roles/Executor_Consultant.md
roles/Executor_Consultant_Top.md
```

Executor 必须完成两部分产物：

1. 视觉构建阶段
   - 按页面执行卡逐页生成 SVG
   - 输出到 `<项目路径>/svg_output/`
   - 全部 SVG 页面生成完成后，统一执行正式质量检查
2. 逻辑构建阶段
   - 生成完整讲稿
   - 输出到 `<项目路径>/notes/total.md`

### 步骤 3：后处理

后处理顺序固定，不可跳过或替换：

```bash
python3 tools/total_md_split.py "<项目路径>"
python3 tools/finalize_svg.py "<项目路径>"
python3 tools/svg_to_pptx.py "<项目路径>" -s final
```

- `total_md_split.py`：将 `notes/total.md` 拆分为单页备注
- `finalize_svg.py`：嵌入图标、修正图片、生成 `svg_final/`
- `svg_to_pptx.py -s final`：从 `svg_final/` 导出 PPTX

### 步骤 4：Optimizer_CRAP（可选）

若用户要求优化，或发现页面质量不足，可进入 `Optimizer_CRAP`。

- 优化后必须重新执行后处理与导出
- 不要在未完成初版前过早进入优化阶段

## 前置条件

- 项目目录已存在
- `设计规范与内容大纲.md` 已完成
- `python3 tools/project_manager.py validate <项目路径> --stage outline` 通过
- 若大纲要求 AI 图片或用户图片，`images/` 中对应素材已就绪

## 产出物

- `svg_output/`
- `notes/total.md`
- `svg_final/`
- `*.pptx`

## 关键原则

1. Executor 只能以大纲为主执行，不得回退为直接从源材料自由生成。
2. 本工作流不负责图片生成；所需图片必须在第一阶段准备完成。
3. 讲稿属于渲染阶段产物，不属于大纲阶段。
4. 后处理与导出默认属于本工作流的一部分。

## 本工作流附加约束

1. 如需查证内容，只能按页面执行卡回查已标记来源，不能重新发散扫描全部 `sources/`。
2. 若发现大纲缺字段或素材缺失，应退回第一阶段修正，而不是在渲染阶段临时补设计决策。
3. `notes/total.md` 与 `svg_output/` 都是本阶段必需产物，缺一不能直接进入后处理。

## 完成检查点

```markdown
## ✅ 第二阶段完成

- [x] 已按大纲生成 `svg_output/`
- [x] 已生成 `notes/total.md`
- [x] 已完成 `total_md_split.py`
- [x] 已完成 `finalize_svg.py`
- [x] 已导出 PPTX
- [ ] **下一步**: 如需优化，进入 `Optimizer_CRAP`
```

## 下一步

- 如需优化关键页面，可调用 `Optimizer_CRAP` 后重新执行后处理与导出。
- 若要回到内容规划，请修改大纲后重新运行本工作流。
