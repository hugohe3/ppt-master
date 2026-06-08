# uvx 工具化改造 实现计划

> **状态**: 已完成 — 最终笔记见 [`2026-06-08-uvx-refactor-final.md`](../2026-06-08-uvx-refactor-final.md)
>
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 ppt-master 所有脚本从 `uv run` 方式改为 `uvx` 统一入口调用，tools 在任意目录可用。

**Architecture:** 新增 `cli.py` 作为统一子命令分派入口（subprocess 方式），pyproject.toml 注册 `[project.scripts]` 入口点，所有 `.md` 工作流文件中的脚本调用统一替换为 `uvx ppt-master <command>`。

**Tech Stack:** Python 3.12, uv, GitHub Actions

---

## Task 1: 创建统一 CLI 入口 cli.py

**Files:**
- Create: `cli.py`

- [ ] **Step 1: 编写 cli.py**

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

COMMAND_DESCRIPTIONS = {
    "project":                "Create/validate/manage PPT projects",
    "pdf-to-md":              "Convert PDF to Markdown",
    "doc-to-md":              "Convert DOCX/HTML/EPUB to Markdown",
    "excel-to-md":            "Convert Excel to Markdown",
    "ppt-to-md":              "Convert PPTX to Markdown",
    "web-to-md":              "Convert URL/webpage to Markdown",
    "analyze-images":         "Analyze images and compute layout sizes",
    "image-gen":              "AI image generation (multi-backend)",
    "image-search":           "Search and download web images",
    "latex-render":           "Render LaTeX formulas to PNG",
    "svg-quality-check":      "Validate SVG against PPT constraints",
    "total-md-split":         "Split total.md into per-page files",
    "finalize-svg":           "Post-process SVGs (icons, images, text)",
    "svg-to-pptx":            "Export SVGs to PPTX",
    "check-annotations":      "Scan SVGs for edit annotations",
    "animation-config":       "Create/validate animation configuration",
    "notes-to-audio":         "Generate per-slide narration audio (TTS)",
    "pptx-template-import":   "Extract SVG references from PPTX template",
    "template-fill-pptx":     "Fill content into PPTX template",
    "svg-editor":             "Launch web-based SVG editor (live preview)",
    "update-spec":            "Propagate color/font changes to all SVGs",
    "visual-review":          "Visual review via Playwright (PNG renderer)",
    "svg-position-calc":      "Chart coordinate calculator",
    "rotate-images":          "Rotate images (EXIF + manual)",
    "update-repo":            "Git pull + uv sync repository updater",
    "generate-examples-index": "Generate examples README index",
    "batch-validate":         "Batch project validator",
    "gemini-watermark-remove": "Remove watermarks from Gemini images",
    "pptx-animations":        "Animation demo and list utilities",
    "check-deps-sync":        "Verify dependency manifest sync",
    "pptx-to-svg":            "Convert PPTX to SVG",
    "error-helper":           "Error explanation lookup",
    "project-utils":          "Project utility helpers",
    "config":                 "List canvas formats and color presets",
    "register-template":      "Register layout template",
}

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ppt-master <command> [args...]")
        print("\nCommands:")
        width = max(len(k) for k in COMMANDS) + 2
        for name in sorted(COMMANDS):
            desc = COMMAND_DESCRIPTIONS.get(name, "")
            print(f"  {name:<{width}}{desc}")
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

- [ ] **Step 2: 验证 cli.py 能直接运行**

```bash
python cli.py
```
Expected: 列出所有命令及描述。

- [ ] **Step 3: 提交**

```bash
git add cli.py
git commit -m "feat: add unified CLI entry point (cli.py)"
```

---

## Task 2: 修改 pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 删除 package = false，添加 [project.scripts]**

编辑 `pyproject.toml`，将：

```toml
[tool.uv]
package = false
```

替换为：

```toml
[project.scripts]
ppt-master = "cli:main"

[tool.uv]
```

变更完成后运行 `uv lock` 更新锁文件：

```bash
uv lock
```

## Task 2a: 验证 uvx 构建（早期关卡）

> **在修改 .md 文件之前必须先完成此任务。**

**Files:**
- None (verification only)

- [ ] **Step 1: 验证 uvx --from . 可用**

```bash
uvx --from . ppt-master
```
Expected: 列出所有命令及描述。

- [ ] **Step 2: 验证 uv tool install 可用**

```bash
uv tool install --from . ppt-master
ppt-master check-deps-sync
```
Expected: 依赖同步检查通过。

- [ ] **Step 3: 卸载并提交**

```bash
uv tool uninstall ppt-master
git add pyproject.toml
git commit -m "feat: add [project.scripts] entry point for uvx"
```

---

## Task 3: 更新 AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 在 Command Quick Reference 之前添加安装步骤**

在 AGENTS.md 的 "Command Quick Reference" 标题之前插入：

```markdown
## Setup

```bash
# First-time setup: install the CLI tool globally (run once, then available anywhere)
uv tool install --from . ppt-master
```

```

- [ ] **Step 2: 替换所有脚本调用**

将 Command Quick Reference 部分的所有 `uv run skills/ppt-master/scripts/` 替换为 `uvx ppt-master `：

```bash
# 改前
uv run skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
# 改后
uvx ppt-master project init <project_name> --format ppt169
```

完整替换以下 10 行：
```bash
# Dependency management
uv sync

# Source content conversion
uvx ppt-master pdf-to-md <PDF_file>
uvx ppt-master doc-to-md <DOCX_or_other_file>
uvx ppt-master excel-to-md <XLSX_or_XLSM_file>
uvx ppt-master ppt-to-md <PPTX_file>
uvx ppt-master web-to-md <URL>

# Project management
uvx ppt-master project init <project_name> --format ppt169
uvx ppt-master project import-sources <project_path> <source_files_or_URLs...> --move
uvx ppt-master project validate <project_path>

# Image tools and SVG quality check
uvx ppt-master analyze-images <project_path>/images
# In-pipeline AI image generation — manifest mode (required, even for 1 image):
uvx ppt-master image-gen --manifest <project_path>/images/image_prompts.json
uvx ppt-master image-gen --render-md <project_path>/images/image_prompts.json
# Out-of-pipeline one-off / debug / single-image fixup only (no manifest, no sidecar):
uvx ppt-master image-gen "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
uvx ppt-master svg-editor <project_path> --live
uvx ppt-master svg-quality-check <project_path>
uvx ppt-master animation-config scaffold <project_path>  # optional, only for custom object-level animation
uvx ppt-master animation-config validate <project_path>  # optional, before re-export

# Post-processing pipeline: run sequentially, one command at a time
uvx ppt-master total-md-split <project_path>
uvx ppt-master finalize-svg <project_path>
uvx ppt-master svg-to-pptx <project_path>
```

- [ ] **Step 3: 提交**

```bash
git add AGENTS.md
git commit -m "docs: migrate AGENTS.md commands from uv run to uvx"
```

---

## Task 4: 更新 skills/ppt-master/SKILL.md

**Files:**
- Modify: `skills/ppt-master/SKILL.md`

- [ ] **Step 1: 定位并替换所有 uv run 脚本调用**

SKILL.md 中所有形如 `uv run ${SKILL_DIR}/scripts/xxx.py` 的调用替换为 `uvx ppt-master xxx`。搜索并逐个替换以下模式：

| 搜索 | 替换为 |
|------|--------|
| `uv run ${SKILL_DIR}/scripts/source_to_md/pdf_to_md.py` | `uvx ppt-master pdf-to-md` |
| `uv run ${SKILL_DIR}/scripts/source_to_md/doc_to_md.py` | `uvx ppt-master doc-to-md` |
| `uv run ${SKILL_DIR}/scripts/source_to_md/excel_to_md.py` | `uvx ppt-master excel-to-md` |
| `uv run ${SKILL_DIR}/scripts/source_to_md/ppt_to_md.py` | `uvx ppt-master ppt-to-md` |
| `uv run ${SKILL_DIR}/scripts/source_to_md/web_to_md.py` | `uvx ppt-master web-to-md` |
| `uv run ${SKILL_DIR}/scripts/project_manager.py` | `uvx ppt-master project` |
| `uv run ${SKILL_DIR}/scripts/analyze_images.py` | `uvx ppt-master analyze-images` |
| `uv run ${SKILL_DIR}/scripts/image_gen.py` | `uvx ppt-master image-gen` |
| `uv run ${SKILL_DIR}/scripts/image_search.py` | `uvx ppt-master image-search` |
| `uv run ${SKILL_DIR}/scripts/latex_render.py` | `uvx ppt-master latex-render` |
| `uv run ${SKILL_DIR}/scripts/svg_quality_checker.py` | `uvx ppt-master svg-quality-check` |
| `uv run ${SKILL_DIR}/scripts/total_md_split.py` | `uvx ppt-master total-md-split` |
| `uv run ${SKILL_DIR}/scripts/finalize_svg.py` | `uvx ppt-master finalize-svg` |
| `uv run ${SKILL_DIR}/scripts/svg_to_pptx.py` | `uvx ppt-master svg-to-pptx` |
| `uv run ${SKILL_DIR}/scripts/svg_editor/server.py` | `uvx ppt-master svg-editor` |
| `uv run ${SKILL_DIR}/scripts/check_annotations.py` | `uvx ppt-master check-annotations` |
| `uv run ${SKILL_DIR}/scripts/animation_config.py` | `uvx ppt-master animation-config` |
| `uv run ${SKILL_DIR}/scripts/notes_to_audio.py` | `uvx ppt-master notes-to-audio` |

> **注意**：`${SKILL_DIR}/templates/`、`${SKILL_DIR}/references/` 等非脚本路径**不替换**。

- [ ] **Step 2: 添加安装前置步骤**

在 SKILL.md 顶部区域（Step 0 或 "Execution Requirements" 之后）添加：

```markdown
> **Setup:** Run this once before using any command below:
> ```bash
> uv tool install --from . ppt-master
> ```
```

- [ ] **Step 3: 提交**

```bash
git add skills/ppt-master/SKILL.md
git commit -m "docs: migrate SKILL.md commands from uv run to uvx"
```

---

## Task 5: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 同步 SKILL.md 的安装前置步骤到 CLAUDE.md**

在 CLAUDE.md 的 Command Quick Reference 附近添加同样的 setup block。

- [ ] **Step 2: 执行相同替换**

CLAUDE.md 是 AGENTS.md 的镜像，执行与 Task 3 完全相同的替换：`uv run skills/ppt-master/scripts/` → `uvx ppt-master `。

- [ ] **Step 3: 提交**

```bash
git add CLAUDE.md
git commit -m "docs: migrate CLAUDE.md commands from uv run to uvx"
```

---

## Task 6: 更新工作流文件 workflows/*.md

**Files:**
- Modify: `skills/ppt-master/workflows/topic-research.md`
- Modify: `skills/ppt-master/workflows/template-fill-pptx.md`
- Modify: `skills/ppt-master/workflows/resume-execute.md`
- Modify: `skills/ppt-master/workflows/verify-charts.md`
- Modify: `skills/ppt-master/workflows/generate-audio.md`
- Modify: `skills/ppt-master/workflows/customize-animations.md`
- Modify: `skills/ppt-master/workflows/live-preview.md`
- Modify: `skills/ppt-master/workflows/create-template.md`
- Modify: `skills/ppt-master/workflows/create-brand.md`
- Modify: `skills/ppt-master/workflows/visual-review.md`

- [ ] **Step 1: 逐个文件替换**

对每个文件执行以下搜索替换：

1. `uv run skills/ppt-master/scripts/xxx.py` → `uvx ppt-master <command>`
2. `python3 skills/ppt-master/scripts/xxx.py` → `uvx ppt-master <command>`（template-fill-pptx.md、visual-review.md、create-brand.md 中有残留）

每个文件替换完毕后确认 `${SKILL_DIR}/templates/` 等路径未被误改。

- [ ] **Step 2: 审查并提交**

```bash
git add skills/ppt-master/workflows/
git commit -m "docs: migrate workflow files from uv run/python3 to uvx"
```

---

## Task 7: 更新引用和脚本文档

**Files:**
- Modify: `skills/ppt-master/references/shared-standards.md`
- Modify: `skills/ppt-master/references/strategist.md`
- Modify: `skills/ppt-master/references/executor-base.md`
- Modify: `skills/ppt-master/references/image-generator.md`
- Modify: `skills/ppt-master/references/image-searcher.md`
- Modify: `skills/ppt-master/references/image-layout-spec.md`
- Modify: `skills/ppt-master/references/svg-image-embedding.md`
- Modify: `skills/ppt-master/references/animations.md`
- Modify: `skills/ppt-master/references/ai-image-comparison/README.md`
- Modify: `skills/ppt-master/scripts/docs/conversion.md`
- Modify: `skills/ppt-master/scripts/docs/image.md`
- Modify: `skills/ppt-master/scripts/docs/project.md`
- Modify: `skills/ppt-master/scripts/docs/svg-pipeline.md`
- Modify: `skills/ppt-master/scripts/docs/troubleshooting.md`
- Modify: `skills/ppt-master/scripts/docs/update_spec.md`

- [ ] **Step 1: 编译前扫描未覆盖文件**

```bash
rg "uv run.*scripts/" skills/ppt-master/ --files-with-matches
```
确认输出列表与下方文件列表一致，如有遗漏补充进去。

- [ ] **Step 2: 批量替换**

对上述文件中所有 `uv run skills/ppt-master/scripts/` 替换为 `uvx ppt-master `。

- [ ] **Step 3: 确认无误并提交**

```bash
git add skills/ppt-master/references/ skills/ppt-master/scripts/docs/
git commit -m "docs: migrate reference and script docs from uv run to uvx"
```

---

## Task 8: 创建 check_cli_sync.py lint 脚本

**Files:**
- Create: `skills/ppt-master/scripts/check_cli_sync.py`

- [ ] **Step 1: 编写检测脚本**

```python
"""Verify all scripts in the scripts directory have a mapping in cli.py."""

import ast
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
CLI_FILE = os.path.join(ROOT_DIR, "cli.py")


def find_scripts_with_main(scripts_dir: str) -> set[str]:
    """Find all .py files under scripts_dir that define a main() function."""
    scripts: set[str] = set()
    for root, dirs, files in os.walk(scripts_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") and d != "__pycache__"]
        for f in files:
            if not f.endswith(".py") or f.startswith("__"):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    rel = os.path.relpath(path, scripts_dir)
                    scripts.add(rel.replace("\\", "/"))
                    break
    return scripts


def parse_commands_from_cli(cli_path: str) -> set[str]:
    """Parse the COMMANDS dict from cli.py to extract script paths."""
    with open(cli_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    scripts: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "COMMANDS":
                if isinstance(node.value, ast.Dict):
                    for v in node.value.values:
                        if isinstance(v, ast.Constant):
                            scripts.add(v.value)
    return scripts


def derive_command_name(script_path: str) -> str:
    """Derive kebab-case command name from script file path."""
    basename = os.path.splitext(os.path.basename(script_path))[0]
    basename = basename.replace("_", "-")
    # Handle subdirectories like source_to_md/pdf_to_md.py
    dirname = os.path.dirname(script_path)
    if dirname and dirname != ".":
        dirname = dirname.replace("_", "-").replace("\\", "/")
        if dirname == "source-to-md":
            suffix = basename.replace("base64-to-", "").replace("to-", "-to-")
            if suffix != "html-to":
                return suffix
    return basename


def main() -> int:
    scripts = find_scripts_with_main(SCRIPTS_DIR)
    # Exclude this script itself and Flask helper modules (not CLI tools)
    scripts.discard("check_cli_sync.py")
    scripts.discard(os.path.join("svg_editor", "app.py"))

    if not os.path.exists(CLI_FILE):
        print(f"ERROR: cli.py not found at {CLI_FILE}")
        return 1

    mapped = parse_commands_from_cli(CLI_FILE)

    missing = scripts - mapped
    if not missing:
        print("OK: All scripts have CLI mappings.")
        return 0

    print("ERROR: The following scripts are missing from cli.py COMMANDS dict:\n")
    for script in sorted(missing):
        cmd = derive_command_name(script)
        desc_file = cmd.replace("-", " ")
        print(f'    "{cmd}": "{script}",  # {desc_file}')
    print(f"\nAdd the above entries to the COMMANDS dict in cli.py, and a")
    print(f"description to COMMAND_DESCRIPTIONS.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 验证检测逻辑**

```bash
python skills/ppt-master/scripts/check_cli_sync.py
```
Expected: `OK: All scripts have CLI mappings.`（当前应全部已映射）

- [ ] **Step 3: 测试未映射场景**

创建一个临时测试脚本：
```bash
echo "def main(): pass" > skills/ppt-master/scripts/_test_new_tool.py
python skills/ppt-master/scripts/check_cli_sync.py
```
Expected: 输出 `_test_new_tool.py` 未映射，并建议 `test-new-tool` 命令名。

清理：
```bash
rm skills/ppt-master/scripts/_test_new_tool.py
```

- [ ] **Step 4: 提交**

```bash
git add skills/ppt-master/scripts/check_cli_sync.py
git commit -m "feat: add check_cli_sync.py to detect unmapped scripts"
```

---

## Task 9: 创建 GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/check-cli-sync.yml`

- [ ] **Step 1: 编写 CI 配置**

```yaml
name: Check CLI Sync

on:
  pull_request:
    paths:
      - "skills/ppt-master/scripts/**"
      - "cli.py"

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      - name: Run cli sync check
        run: python skills/ppt-master/scripts/check_cli_sync.py
```

- [ ] **Step 2: 提交**

```bash
git add .github/workflows/check-cli-sync.yml
git commit -m "ci: add check-cli-sync workflow for CLI mapping coverage"
```

---

## Task 10: 最终验证

- [ ] **Step 1: 安装后完整流程验证**

```bash
uv tool install --from . ppt-master
ppt-master project init testproj --format ppt169
ppt-master svg-quality-check projects/testproj --format ppt169
```
Expected: 创建项目 + 质量检查均正常。

- [ ] **Step 2: 非项目目录验证**

在 `C:\Users\elvis` 目录下执行：
```bash
ppt-master check-deps-sync
```
Expected: 正常执行（证明不受目录限制）。

- [ ] **Step 3: CLI lint 自检**

```bash
python skills/ppt-master/scripts/check_cli_sync.py
```
Expected: `OK: All scripts have CLI mappings.`

- [ ] **Step 4: 清理并提交**

```bash
uv tool uninstall ppt-master
rm -r projects/testproj
git add -A
git commit -m "chore: cleanup test artifacts, final verification complete"
```

---

## 实现顺序

```
Task 1 (cli.py) → Task 2 (pyproject.toml)
    ↓
Task 2a (build verify + uv tool install) ← 【关键关卡：确认构建无误】
    ↓
Task 3-7 (.md files, 可并行)
    ↓
Task 8 (check_cli_sync.py) → Task 9 (CI workflow)
    ↓
Task 10 (final verification + cleanup)
```

Task 1 和 Task 2 是关键路径，完成后**必须先执行 Task 2a** 验证 `uv tool install --from . ppt-master` 可用性，确认构建无误后再继续 .md 文件替换。避免大面积改完 .md 后发现入口点有问题需要返工。
