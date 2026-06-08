# 设计文档：uv run → uvx 工具化改造

**日期**: 2026-06-08  
**状态**: 待审核

## 1. 背景

### 1.1 现状

上游项目（hugohe3/ppt-master）不使用 pyproject.toml，仅用 `pip install -r requirements.txt` + `python3` 直接调用脚本。本 fork 已做了以下改造：

- 新增 `pyproject.toml` + `uv.lock`，引入 uv 包管理
- 新增 `.python-version`（3.12）
- 所有工作流 .md 文件中的 `python3` 调用改为 `uv run`
- 新增 `check_deps_sync.py` 等辅助脚本

### 1.2 痛点

`uv run` 要求当前目录（或上级目录）存在 `pyproject.toml`，意味着用户必须在项目根目录下操作。无法在任意目录调用工具。

### 1.3 目标

将脚本以 `uvx`（`uv tool run`）方式暴露，让工具在**任意目录**可直接调用，同时：

- **scripts 目录零改动** —— 不与上游脚本产生合并冲突
- **`.md` 工作流统一改为 `uvx`** —— 与上游的差异已存在，维持一致性
- **保留 `uv run` 兼容** —— 两套方式共存

## 2. 架构

### 2.1 入口点

```
uvx --from . ppt-master <子命令> [参数...]
```

安装后：
```
uv tool install --from . ppt-master
ppt-master project init myproj
```

### 2.2 分派机制

新增 `cli.py`（根目录），通过 `subprocess` + `sys.executable` 分派到子脚本：

```
cli.py (新增)
  └── 子命令映射表
        ├── project        → skills/ppt-master/scripts/project_manager.py
        ├── pdf-to-md      → skills/ppt-master/scripts/source_to_md/pdf_to_md.py
        ├── image-gen      → skills/ppt-master/scripts/image_gen.py
        └── ... (30+ 命令)
```

选择 `subprocess` 而非 `import` 的原因：
- 不用给 `scripts/` 目录加 `__init__.py`
- 不需要调整 `sys.path`
- 子脚本之间的内部 import 不受影响
- 上游更新脚本时不需要额外适配

### 2.3 命令命名

遵循 `kebab-case`，从脚本文件名派生：

| 脚本 | 命令名 | 使用示例 |
|------|--------|----------|
| `project_manager.py` | `project` | `ppt-master project init myproj` |
| `source_to_md/pdf_to_md.py` | `pdf-to-md` | `ppt-master pdf-to-md paper.pdf` |
| `source_to_md/doc_to_md.py` | `doc-to-md` | `ppt-master doc-to-md report.docx` |
| `source_to_md/excel_to_md.py` | `excel-to-md` | `ppt-master excel-to-md data.xlsx` |
| `source_to_md/ppt_to_md.py` | `ppt-to-md` | `ppt-master ppt-to-md deck.pptx` |
| `source_to_md/web_to_md.py` | `web-to-md` | `ppt-master web-to-md https://...` |
| `image_gen.py` | `image-gen` | `ppt-master image-gen "prompt"` |
| `image_search.py` | `image-search` | `ppt-master image-search "query"` |
| `svg_quality_checker.py` | `svg-quality-check` | `ppt-master svg-quality-check proj/` |
| `total_md_split.py` | `total-md-split` | `ppt-master total-md-split proj/` |
| `finalize_svg.py` | `finalize-svg` | `ppt-master finalize-svg proj/` |
| `svg_to_pptx.py` | `svg-to-pptx` | `ppt-master svg-to-pptx proj/` |
| `animation_config.py` | `animation-config` | `ppt-master animation-config scaffold proj/` |
| `notes_to_audio.py` | `notes-to-audio` | `ppt-master notes-to-audio proj/` |
| `analyze_images.py` | `analyze-images` | `ppt-master analyze-images proj/images` |
| `latex_render.py` | `latex-render` | `ppt-master latex-render proj/` |
| `check_annotations.py` | `check-annotations` | `ppt-master check-annotations proj/` |
| `pptx_template_import.py` | `pptx-template-import` | `ppt-master pptx-template-import template.pptx` |
| `template_fill_pptx.py` | `template-fill-pptx` | `ppt-master template-fill-pptx analyze ...` |
| `svg_editor/server.py` | `svg-editor` | `ppt-master svg-editor proj/ --live` |
| `update_spec.py` | `update-spec` | `ppt-master update-spec proj/ color=#FFF` |
| `visual_review.py` | `visual-review` | `ppt-master visual-review proj/` |
| `svg_position_calculator.py` | `svg-position-calc` | `ppt-master svg-position-calc calc ...` |
| `rotate_images.py` | `rotate-images` | `ppt-master rotate-images auto path/` |
| `update_repo.py` | `update-repo` | `ppt-master update-repo` |
| `generate_examples_index.py` | `generate-examples-index` | `ppt-master generate-examples-index` |
| `batch_validate.py` | `batch-validate` | `ppt-master batch-validate dir/` |
| `gemini_watermark_remover.py` | `gemini-watermark-remove` | `ppt-master gemini-watermark-remove img.png` |
| `pptx_animations.py` | `pptx-animations` | `ppt-master pptx-animations --demo` |
| `check_deps_sync.py` | `check-deps-sync` | `ppt-master check-deps-sync` |
| `pptx_to_svg.py` | `pptx-to-svg` | `ppt-master pptx-to-svg deck.pptx out/` |
| `error_helper.py` | `error-helper` | `ppt-master error-helper SVG_001` |
| `project_utils.py` | `project-utils` | `ppt-master project-utils proj/` |
| `config.py` | `config` | `ppt-master config --list-canvas` |
| `register_template.py` | `register-template` | `ppt-master register-template ...` |

## 3. 文件改动清单

### 3.1 新增文件

| 文件 | 说明 |
|------|------|
| `cli.py` | 统一 CLI 入口，约 80 行 |

### 3.2 修改文件

| 文件 | 改动 |
|------|------|
| `pyproject.toml` | ① `package = false` → `true`（或删除该行，默认 true）② 新增 `[project.scripts]` |
| `skills/ppt-master/pyproject.toml` | 同上，保持与根 pyproject.toml 镜像同步 |
| `skills/ppt-master/SKILL.md` | `uv run skills/ppt-master/scripts/xxx.py` → `uvx ppt-master xxx` |
| `AGENTS.md` | 同上替换 |
| `CLAUDE.md` | 同上替换 |
| `skills/ppt-master/workflows/*.md` | 所有 10+ 个工作流 .md 文件中的 `uv run` 替换 |
| `skills/ppt-master/references/*.md` | 部分引用文件中的 `uv run` 替换 |
| `skills/ppt-master/scripts/docs/*.md` | 脚本文档中的 `uv run` 替换 |

### 3.3 不改动的文件

| 文件 | 原因 |
|------|------|
| `skills/ppt-master/scripts/**/*.py` | 零改动，避免上游冲突 |
| `requirements.txt` / `skills/ppt-master/requirements.txt` | 无变化 |
| `uv.lock` / `skills/ppt-master/uv.lock` | uv 自动管理 |

## 4. pyproject.toml 改动细节

```toml
# 改：删除 package = false（默认 true）
[tool.uv]
# package = false   ← 删除这行
# 保留同步备注注释

# 新增：
[project.scripts]
ppt-master = "cli:main"
```

`skills/ppt-master/pyproject.toml` 做完全相同的修改。

## 5. cli.py 核心逻辑

```python
"""ppt-master CLI — unified entry point for all scripts."""

import os
import subprocess
import sys

SCRIPTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "skills", "ppt-master", "scripts"
)

COMMANDS = {
    "project":                "project_manager.py",
    "pdf-to-md":              "source_to_md/pdf_to_md.py",
    "doc-to-md":              "source_to_md/doc_to_md.py",
    "excel-to-md":            "source_to_md/excel_to_md.py",
    "ppt-to-md":              "source_to_md/ppt_to_md.py",
    "web-to-md":              "source_to_md/web_to_md.py",
    "analyze-images":         "analyze_images.py",
    "image-gen":              "image_gen.py",
    "image-search":           "image_search.py",
    "latex-render":           "latex_render.py",
    "svg-quality-check":      "svg_quality_checker.py",
    "total-md-split":         "total_md_split.py",
    "finalize-svg":           "finalize_svg.py",
    "svg-to-pptx":            "svg_to_pptx.py",
    "check-annotations":      "check_annotations.py",
    "animation-config":       "animation_config.py",
    "notes-to-audio":         "notes_to_audio.py",
    "pptx-template-import":   "pptx_template_import.py",
    "template-fill-pptx":     "template_fill_pptx.py",
    "svg-editor":             "svg_editor/server.py",
    "update-spec":            "update_spec.py",
    "visual-review":          "visual_review.py",
    "svg-position-calc":      "svg_position_calculator.py",
    "rotate-images":          "rotate_images.py",
    "update-repo":            "update_repo.py",
    "generate-examples-index": "generate_examples_index.py",
    "batch-validate":         "batch_validate.py",
    "gemini-watermark-remove": "gemini_watermark_remover.py",
    "pptx-animations":        "pptx_animations.py",
    "check-deps-sync":        "check_deps_sync.py",
    "pptx-to-svg":            "pptx_to_svg.py",
    "error-helper":           "error_helper.py",
    "project-utils":          "project_utils.py",
    "config":                 "config.py",
    "register-template":      "register_template.py",
}

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ppt-master <command> [args...]")
        print("\nCommands:")
        for name in sorted(COMMANDS):
            print(f"  {name}")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    script_rel = COMMANDS.get(cmd)
    if script_rel is None:
        print(f"Unknown command: {cmd}")
        print(f"Run 'ppt-master' without arguments to list commands.")
        sys.exit(1)

    script_path = os.path.join(SCRIPTS_DIR, script_rel)
    if not os.path.isfile(script_path):
        print(f"Script not found: {script_path}")
        sys.exit(1)

    result = subprocess.run([sys.executable, script_path, *args])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
```

## 6. 工作流 .md 文件替换模式

### 6.1 替换规则

| 原模式 | 新模式 |
|--------|--------|
| `uv run skills/ppt-master/scripts/project_manager.py` | `uvx ppt-master project` |
| `uv run skills/ppt-master/scripts/source_to_md/pdf_to_md.py` | `uvx ppt-master pdf-to-md` |
| `uv run skills/ppt-master/scripts/image_gen.py` | `uvx ppt-master image-gen` |
| `python3 skills/ppt-master/scripts/xxx.py` | `uvx ppt-master <command>` |
| `${SKILL_DIR}/scripts/xxx.py` | 删除变量，替换为 `uvx ppt-master <command>` |

### 6.2 涉及文件

- `AGENTS.md`（Command Quick Reference 部分）
- `skills/ppt-master/SKILL.md`（所有步骤中的 `uv run` 调用 + `${SKILL_DIR}` 变量）
- `CLAUDE.md`
- `skills/ppt-master/workflows/*.md`（10+ 个文件，包括其中残留的 `python3` 调用）
- `skills/ppt-master/references/*.md`（部分含命令示例的引用文件）
- `skills/ppt-master/scripts/docs/*.md`（脚本文档中的示例命令）

### 6.3 使用场景说明

- **项目开发时**（在 repo 目录下）：`uvx --from . ppt-master <command>`
- **安装到全局后**（任意目录）：直接 `ppt-master <command>`
- **AGENTS.md 中的命令**：统一写 `uvx ppt-master`，首次运行前需 `uv tool install --from . ppt-master`

AGENTS.md 中的 Command Quick Reference 示例：
```bash
# 改前
uv run skills/ppt-master/scripts/project_manager.py init myproj --format ppt169
# 改后
uvx ppt-master project init myproj --format ppt169
```

## 7. 上游兼容性分析

| 层面 | 冲突风险 | 说明 |
|------|----------|------|
| `cli.py` | 无 | 全新文件，上游不存在 |
| `pyproject.toml [project.scripts]` | 无 | 上游没有 pyproject.toml |
| `pyproject.toml package = true` | 无 | 上游没有 pyproject.toml |
| `skills/ppt-master/scripts/` | 零 | 完全不改动 |
| `AGENTS.md / SKILL.md / workflows/*.md` | 已有 | `python3` → `uv run` 时已产生差异，`uvx` 不会增加新的冲突面 |
| `requirements.txt` | 无 | 不依赖它 |

上游合入更新的关键点：`.md` 文件中的命令调用差异需要手动合并，但这是 fork 的固有代价。scripts 目录完全不动，上游的任何脚本更新（新增/修改）都能直接合入，只需在 `cli.py` 的 `COMMANDS` 字典中添加一行新命令映射（如果有新脚本的话）。

## 8. 验证计划

1. `uvx --from . ppt-master`（无参数）—— 应列出所有命令
2. `uvx --from . ppt-master project init testproj --format ppt169` —— 应创建项目
3. `uvx --from . ppt-master pdf-to-md somefile.pdf` —— 应转换 PDF
4. `uvx --from . ppt-master svg-editor testproj --live` —— 应启动编辑器
5. `uvx --from . ppt-master check-deps-sync` —— 应验证依赖同步
6. 在**非项目目录**下执行以上命令 —— 应全部正常
