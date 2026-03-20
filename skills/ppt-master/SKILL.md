---
name: ppt-master
description: >
  AI-driven multi-format SVG content generation system. Converts source documents
  (PDF/URL/Markdown) into high-quality SVG pages and exports to PPTX through
  multi-role collaboration. Use when user asks to "create PPT", "make presentation",
  "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".
---

# PPT Master Skill

> AI 驱动的多格式 SVG 内容生成系统。通过多角色协作将源文档转化为高质量 SVG 页面并导出 PPTX。

**核心流程**：`源文档 → 创建项目 → 模板选项 → Strategist → [Image_Generator] → Executor → 后处理 → 导出`

## 脚本目录

| 脚本 | 用途 |
|------|------|
| `${SKILL_DIR}/scripts/pdf_to_md.py` | PDF 转 Markdown |
| `${SKILL_DIR}/scripts/web_to_md.py` | 网页转 Markdown |
| `${SKILL_DIR}/scripts/web_to_md.cjs` | 微信/高防站点转 Markdown |
| `${SKILL_DIR}/scripts/project_manager.py` | 项目初始化/验证/管理 |
| `${SKILL_DIR}/scripts/analyze_images.py` | 图片分析 |
| `${SKILL_DIR}/scripts/nano_banana_gen.py` | AI 图片生成（Gemini API） |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG 质量检查 |
| `${SKILL_DIR}/scripts/total_md_split.py` | 演讲备注拆分 |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG 后处理（统一入口） |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | 导出 PPTX |

## 模板与资源

| 资源 | 路径 |
|------|------|
| 页面布局模板 | `${SKILL_DIR}/templates/layouts/` |
| 图表 SVG 模板 | `${SKILL_DIR}/templates/charts/` |
| 矢量图标库 (640+) | `${SKILL_DIR}/templates/icons/` |
| 模板索引 | `${SKILL_DIR}/templates/layouts/layouts_index.json` |
| 设计规范参考 | `${SKILL_DIR}/templates/design_spec_reference.md` |

---

## 工作流

### Step 0: 偏好加载 ⛔ BLOCKING

检查用户偏好配置：
1. 项目级: `.ppt-master/EXTEND.md`
2. 用户级: `$HOME/.ppt-master/EXTEND.md`

如果存在，读取并应用偏好（默认风格、默认格式等）。

---

### Step 1: 源内容处理

当用户提供非 Markdown 内容时，必须立即转换：

| 用户提供 | 命令 |
|----------|------|
| PDF 文件 | `python3 ${SKILL_DIR}/scripts/pdf_to_md.py <文件>` |
| 网页链接 | `python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| 微信/高防站 | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | 直接读取 |

---

### Step 2: 项目初始化

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <项目名> --format <格式>
```

格式选项：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等。完整格式列表见 `references/canvas-formats.md`。

如需导入源文件：
```bash
python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <项目路径> <源文件...>
```

---

### Step 3: 模板选择

向用户确认（二选一）：

**A) 使用已有模板**
1. 查询 `${SKILL_DIR}/templates/layouts/layouts_index.json` 确认可用模板
2. 复制模板文件到项目目录：
   ```bash
   cp ${SKILL_DIR}/templates/layouts/<模板名>/*.svg <项目路径>/templates/
   cp ${SKILL_DIR}/templates/layouts/<模板名>/design_spec.md <项目路径>/templates/
   cp ${SKILL_DIR}/templates/layouts/<模板名>/*.png <项目路径>/images/ 2>/dev/null || true
   cp ${SKILL_DIR}/templates/layouts/<模板名>/*.jpg <项目路径>/images/ 2>/dev/null || true
   ```

**B) 不使用模板** → 自由设计

> 如需创建新模板，Read `references/template-designer.md`

---

### Step 4: Strategist 阶段（必须，不可跳过）

⛔ **BLOCKING**: 先读取角色定义：
```
Read references/strategist.md
Read references/shared-standards.md
```

**必须完成八项确认**：
1. 画布格式
2. 页数范围
3. 目标受众
4. 风格目标
5. 配色方案
6. 图标使用方式
7. 图片使用方式
8. 排版方案

如用户提供了图片：
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <项目路径>/images
```

**输出**：`<项目路径>/设计规范与内容大纲.md`

**检查点**：
```markdown
## ✅ Strategist 阶段完成
- [x] 已完成八项确认
- [x] 已生成《设计规范与内容大纲》
- [ ] **下一步**: [Image_Generator / Executor]
```

---

### Step 5: Image_Generator 阶段（条件触发）

> **触发条件**：图片方式包含「AI 生成」

⛔ **BLOCKING**: Read `references/image-generator.md`

1. 从设计规范中提取所有「状态=待生成」的图片
2. 生成提示词文档 → `<项目路径>/images/image_prompts.md`
3. 生成图片（推荐命令行工具）：
   ```bash
   python3 ${SKILL_DIR}/scripts/nano_banana_gen.py "提示词" --aspect_ratio 16:9 --image_size 1K -o <项目路径>/images
   ```

**检查点**：
```markdown
## ✅ Image_Generator 阶段完成
- [x] 提示词文档已创建
- [x] 所有图片已保存到 images/
```

---

### Step 6: Executor 阶段

⛔ **BLOCKING**: 根据风格选择读取角色定义：
```
Read references/executor-base.md          # 必读：公共准则
Read references/executor-general.md       # 通用灵活风格
Read references/executor-consultant.md    # 咨询风格
Read references/executor-consultant-top.md # 顶级咨询风格（MBB级）
```

> 只需读 executor-base + 一个风格文件即可。

**视觉构建阶段**：
- 批量生成 SVG 页面 → `<项目路径>/svg_output/`

**逻辑构建阶段**：
- 生成演讲备注 → `<项目路径>/notes/total.md`

**检查点**：
```markdown
## ✅ Executor 阶段完成
- [x] 所有 SVG 已生成到 svg_output/
- [x] 演讲备注已生成 notes/total.md
```

---

### Step 7: 后处理与导出

> ⚠️ 必须按顺序执行，不可省略或替换！

```bash
# 1. 拆分演讲备注
python3 ${SKILL_DIR}/scripts/total_md_split.py <项目路径>

# 2. SVG 后处理（图标嵌入/图片裁剪嵌入/文本扁平化/圆角转Path）
python3 ${SKILL_DIR}/scripts/finalize_svg.py <项目路径>

# 3. 导出 PPTX（默认嵌入演讲备注）
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <项目路径> -s final
```

> ❌ **禁止**用 `cp` 替代 `finalize_svg.py`，该工具执行多项关键处理
> ❌ **禁止**从 `svg_output/` 直接导出，必须用 `-s final` 从 `svg_final/` 导出

---

### Step 8: Optimizer 阶段（可选）

> **触发条件**：用户要求优化，或设计质量需要提升

Read `references/optimizer-crap.md`

优化后需重新执行 Step 7（后处理与导出）。

---

## 角色切换协议

切换角色前**必须先读取**对应的 reference 文件，禁止跳过。输出标记：

```markdown
## 【角色切换：[角色名称]】
📖 阅读角色定义: references/[文件名].md
📋 当前任务: [简述]
```

---

## 参考资源

| 资源 | 路径 |
|------|------|
| 公共技术约束 | `references/shared-standards.md` |
| 画布格式规范 | `references/canvas-formats.md` |
| 设计指南 | `references/design-guidelines.md` |
| 图片布局规范 | `references/image-layout-spec.md` |
| SVG 图片嵌入 | `references/svg-image-embedding.md` |

---

## 注意事项

- 后处理三步不要添加 `--only` 等额外参数，直接运行即可
- 如果执行了 Optimizer 优化，需重新运行后处理与导出
- 本地预览：`python3 -m http.server -d <项目路径>/svg_final 8000`
