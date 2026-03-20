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

> [!CAUTION]
> ## 🚨 全局执行纪律（MANDATORY）
>
> **本工作流为严格串行流程。以下规则具有最高优先级，违反任何一条即为执行失败：**
>
> 1. **SERIAL EXECUTION** — 步骤必须按顺序执行，前一步的产出是后一步的输入。非 BLOCKING 的相邻步骤在前置条件满足时可以连续执行，无需等待用户说"继续"
> 2. **BLOCKING = HARD STOP** — 标记为 ⛔ BLOCKING 的步骤，必须停下来等待用户明确回复后才能继续，AI 不得代替用户做出任何决定
> 3. **NO CROSS-PHASE BUNDLING** — 禁止跨阶段打包执行。（注：但当用户确认八项原则后，可连续自动生成设计规范、生成大纲、生成 SVG、生成备注以及进入后处理流程，只要前置条件就绪即可无缝衔接，无需等待用户确认即可推进）
> 4. **GATE BEFORE ENTRY** — 每个 Step 开头标注了前置条件（🚧 GATE），必须先验证前置条件满足后才能开始该 Step
> 5. **NO SPECULATIVE EXECUTION** — 禁止"预先准备"后续 Step 的内容（如在 Strategist 阶段就开始写 SVG 代码）

## 主流程脚本

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

完整工具说明见 `${SKILL_DIR}/scripts/README.md`。

## 模板索引

| 索引 | 路径 | 用途 |
|------|------|------|
| 布局模板索引 | `${SKILL_DIR}/templates/layouts/layouts_index.json` | 查询可用页面布局模板 |
| 图表模板索引 | `${SKILL_DIR}/templates/charts/charts_index.json` | 查询可用图表 SVG 模板 |
| 图标库索引 | `${SKILL_DIR}/templates/icons/icons_index.json` | 查询可用图标名称与分类 |

## 独立工作流

| 工作流 | 路径 | 用途 |
|--------|------|------|
| `create-template` | `workflows/create-template.md` | 独立模板创建流程 |

---

## 工作流

### Step 1: 源内容处理

🚧 **GATE**：用户已提供源材料（PDF / URL / Markdown 文件 / 文本描述 / 对话内容等任意形式均可）。

当用户提供非 Markdown 内容时，必须立即转换：

| 用户提供 | 命令 |
|----------|------|
| PDF 文件 | `python3 ${SKILL_DIR}/scripts/pdf_to_md.py <文件>` |
| 网页链接 | `python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| 微信/高防站 | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | 直接读取 |

**✅ 检查点 — 确认源内容已就绪，继续 Step 2。**

---

### Step 2: 项目初始化

🚧 **GATE**：Step 1 已完成，源内容已就绪（Markdown 文件、用户提供的文本、或对话中的需求描述均可）。

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <项目名> --format <格式>
```

格式选项：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等。完整格式列表见 `references/canvas-formats.md`。

导入源内容（根据实际情况选择）：

| 情况 | 操作 |
|------|------|
| 有源文件（PDF/MD等） | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <项目路径> <源文件...> --move` |
| 用户在对话中直接提供文本 | 无需导入，内容已在对话上下文中，后续步骤直接引用即可 |

> ⚠️ **必须使用 `--move`**：所有源文件（原始 PDF / MD / 图片等）必须**移动**（而非复制）到 `sources/` 中归档。
> - Step 1 转换生成的 Markdown 文件、原始 PDF、原始 MD，**全部**通过 `import-sources --move` 移入项目
> - 转换中间产物（如 `_files/` 目录）由 `import-sources` 自动处理
> - 执行后，源文件在原始位置不再存在

**✅ 检查点 — 确认项目结构已创建成功、`sources/` 中包含所有源文件、源转换物已就绪，继续 Step 3。**

---

### Step 3: 模板选择

🚧 **GATE**：Step 2 已完成，项目目录结构已就绪。

⛔ **BLOCKING**：如果用户尚未明确表达是否使用模板，则必须向用户展示选项并**等待用户明确回复**后才能继续。若用户在此前已经明确表示过“不使用模板”或指定了具体模板，则可跳过此询问直接执行结论。

查询 `${SKILL_DIR}/templates/layouts/layouts_index.json`，列出可用模板及其风格描述。
**向用户展示选项时，必须结合当前的 PPT 主题和内容，给出你的专业建议（建议使用某个具体模板，或建议不使用模板而是自由设计，并说明原因）**，然后再询问用户：

> 💡 **AI 建议**：根据您的内容主题（简述），我建议您选择 **[某一具体模板 / 自由设计]**，因为...
> 
> 请问您希望使用哪种方式？
> **A) 使用已有模板**（请告知模板名称或风格偏好）
> **B) 不使用模板**，自由设计

用户确认选 A 后，复制模板文件到项目目录：
```bash
cp ${SKILL_DIR}/templates/layouts/<模板名>/*.svg <项目路径>/templates/
cp ${SKILL_DIR}/templates/layouts/<模板名>/design_spec.md <项目路径>/templates/
cp ${SKILL_DIR}/templates/layouts/<模板名>/*.png <项目路径>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<模板名>/*.jpg <项目路径>/images/ 2>/dev/null || true
```

用户确认选 B 后，直接进入 Step 4。

> 如需创建新模板，Read `references/template-designer.md`

**✅ 检查点 — 用户已回复模板选择，模板文件已复制（若选 A），继续 Step 4。**

---

### Step 4: Strategist 阶段（必须，不可跳过）

🚧 **GATE**：Step 3 已完成，用户已确认模板选择。

先读取角色定义：
```
Read references/strategist.md
Read references/shared-standards.md
```

**必须完成八项确认**（参考 `templates/design_spec_reference.md` 模板内容）：

⛔ **BLOCKING**：八项确认必须以**打包问题的方式向用户呈现建议，等待用户回复确认或修改**后，才能输出《设计规范与内容大纲》。这是流程中仅有的两个核心确认点之一（另一个是模板选择）。一旦确认，后续所有脚本执行与幻灯片生成均应全自动连贯执行。

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

**✅ 检查点 — 本阶段产出完毕，自动进入下一步**：
```markdown
## ✅ Strategist 阶段完成
- [x] 已完成八项确认（用户已回复确认）
- [x] 已生成《设计规范与内容大纲》
- [ ] **下一步**: 自动进入 [Image_Generator / Executor] 环节
```

---

### Step 5: Image_Generator 阶段（条件触发）

🚧 **GATE**：Step 4 已完成，《设计规范与内容大纲》已生成且用户已确认。

> **触发条件**：图片方式包含「AI 生成」。若不触发，直接跳到 Step 6（但仍需满足 Step 6 的 GATE）。

Read `references/image-generator.md`

1. 从设计规范中提取所有「状态=待生成」的图片
2. 生成提示词文档 → `<项目路径>/images/image_prompts.md`
3. 生成图片（推荐命令行工具）：
   ```bash
   python3 ${SKILL_DIR}/scripts/nano_banana_gen.py "提示词" --aspect_ratio 16:9 --image_size 1K -o <项目路径>/images
   ```

**✅ 检查点 — 确认所有图片已就绪，继续 Step 6**：
```markdown
## ✅ Image_Generator 阶段完成
- [x] 提示词文档已创建
- [x] 所有图片已保存到 images/
```

---

### Step 6: Executor 阶段

🚧 **GATE**：Step 4（及 Step 5，如触发）已完成，所有前置产出已就绪。

根据风格选择读取角色定义：
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

**✅ 检查点 — 确认所有 SVG 和 notes 已完整生成。直接进入 Step 7 后处理命令**：
```markdown
## ✅ Executor 阶段完成
- [x] 所有 SVG 已生成到 svg_output/
- [x] 演讲备注已生成 notes/total.md
```

---

### Step 7: 后处理与导出

🚧 **GATE**：Step 6 已完成，所有 SVG 已生成到 `svg_output/`，演讲备注 `notes/total.md` 已生成。

> ⚠️ 以下三个子步骤必须**逐条单独执行**，每条命令执行完毕并确认成功后，才能执行下一条。
> ❌ **禁止**将三条命令写在同一个代码块或同一次 shell 调用中一次性执行。

**Step 7.1** — 拆分演讲备注：
```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <项目路径>
```

**Step 7.2** — SVG 后处理（图标嵌入/图片裁剪嵌入/文本扁平化/圆角转 Path）：
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <项目路径>
```

**Step 7.3** — 导出 PPTX（默认嵌入演讲备注）：
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <项目路径> -s final
```

> ❌ **禁止**用 `cp` 替代 `finalize_svg.py`，该工具执行多项关键处理
> ❌ **禁止**从 `svg_output/` 直接导出，必须用 `-s final` 从 `svg_final/` 导出
> ❌ **禁止**添加 `--only` 等额外参数

---

### Step 8: Optimizer 阶段（可选）

🚧 **GATE**：Step 7 已完成。

> **触发条件**：用户要求优化，或设计质量需要提升

Read `references/optimizer-crap.md`

优化后需**从 Step 7.1 开始重新执行**全部后处理子步骤（7.1 → 7.2 → 7.3），不可跳过。

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
