# AGENTS.md

本文件为通用 AI 代理提供项目入口。执行 PPT 生成任务前，**必须先阅读 `skills/ppt-master/SKILL.md`** 获取完整工作流与规则。

## 项目概述

PPT Master 是一个 AI 驱动的多格式 SVG 内容生成系统。通过多角色协作（Strategist → Image_Generator → Executor → Optimizer），将源文档（PDF/URL/Markdown）转化为高质量 SVG 页面，并导出为 PPTX。

**核心流程**：`源文档 → 创建项目 → 模板选项 → Strategist 八项确认 → [Image_Generator] → Executor → 后处理 → 导出 PPTX`

**执行要求**：

- 开始 PPT 任务前，优先阅读 `skills/ppt-master/SKILL.md`
- 如需独立创建模板，阅读 `skills/ppt-master/workflows/create-template.md`
- 具体角色规则与技术约束都在 `skills/ppt-master/references/`
- ⚠️ **严格串行执行**：流程中的每个 Step 必须逐步执行，禁止合并、打包、并行执行多个 Step

## 常用命令

```bash
# 源内容转换
python3 skills/ppt-master/scripts/pdf_to_md.py <PDF文件>
python3 skills/ppt-master/scripts/web_to_md.py <URL>
node skills/ppt-master/scripts/web_to_md.cjs <URL>

# 项目管理
python3 skills/ppt-master/scripts/project_manager.py init <项目名> --format ppt169
python3 skills/ppt-master/scripts/project_manager.py import-sources <项目路径> <源文件或URL...> --move
python3 skills/ppt-master/scripts/project_manager.py validate <项目路径>

# 图片工具
python3 skills/ppt-master/scripts/analyze_images.py <项目路径>/images
python3 skills/ppt-master/scripts/nano_banana_gen.py "提示词" --aspect_ratio 16:9 --image_size 1K -o <项目路径>/images

# SVG 质量检查
python3 skills/ppt-master/scripts/svg_quality_checker.py <项目路径>

# 后处理三步（必须按顺序逐条执行，禁止一次性执行）
python3 skills/ppt-master/scripts/total_md_split.py <项目路径>
# ✅ 确认无报错后执行下一条
python3 skills/ppt-master/scripts/finalize_svg.py <项目路径>
# ✅ 确认无报错后执行下一条
python3 skills/ppt-master/scripts/svg_to_pptx.py <项目路径> -s final
```

## 核心目录

- `skills/ppt-master/SKILL.md` — 主入口与完整流程
- `skills/ppt-master/workflows/create-template.md` — 独立模板工作流
- `skills/ppt-master/references/` — 角色定义与技术规范
- `skills/ppt-master/scripts/` — 工具脚本
- `skills/ppt-master/templates/` — 布局模板、图表模板、图标库
- `examples/` — 示例项目
- `projects/` — 用户项目工作区

## SVG 技术约束

**禁用功能**：`clipPath` | `mask` | `<style>` | `class` | 外部 CSS | `<foreignObject>` | `textPath` | `@font-face` | `<animate*>` | `<script>` | `marker-end` | `<iframe>` | `<symbol>+<use>`（`<defs>` 内 `id` 为合法引用，不在此列）

**PPT 兼容性替代**：

| 禁止 | 替代 |
|------|------|
| `rgba()` | `fill-opacity` / `stroke-opacity` |
| `<g opacity>` | 每个子元素单独设置 opacity |
| `<image opacity>` | 遮罩层叠加 |
| `marker-end` 箭头 | `<polygon>` 三角形 |

## 画布格式速查

| 格式 | viewBox |
|------|---------|
| PPT 16:9 | `0 0 1280 720` |
| PPT 4:3 | `0 0 1024 768` |
| 小红书 | `0 0 1242 1660` |
| 朋友圈 | `0 0 1080 1080` |
| Story | `0 0 1080 1920` |

## 后处理注意事项

- **禁止**用 `cp` 命令替代 `finalize_svg.py`
- **禁止**从 `svg_output/` 直接导出，必须从 `svg_final/`（`-s final`）导出
- 后处理三步命令不要添加 `--only` 等额外参数
- **禁止**将后处理三步写在同一个代码块或同一次 shell 调用中执行
