---
description: 合并上游更新，解决冲突，适配uvx命令，补全cli.py映射，发布新版本
agent: general
---

# 上游同步命令

执行上游项目 (hugohe3/ppt-master) 的完整合并 → uvx 适配 → 版本发布流程。

## 前置条件

- 工作区干净 (`git status` 无变更)
- `rg` (ripgrep) 已安装（Windows: `winget install BurntSushi.ripgrep.MSVC`，macOS: `brew install ripgrep`）
- 已配置 `upstream` remote: `https://github.com/hugohe3/ppt-master.git`
- 已配置 `origin` remote: 本 fork

## 执行步骤

严格按照以下顺序执行，每步完成后确认无误再继续。

---

### Step 1: 拉取上游

```bash
git fetch upstream
git log main..upstream/main --oneline
```

记录上游新增的提交数量和主题。

---

### Step 2: 合并上游

```bash
git merge upstream/main
```

**如果合并失败且冲突无法解决**（如上游大规模重构导致 fork 的 cli.py/uvx 适配完全冲突），立即中止：

```bash
git merge --abort
```

中止后向用户报告失败原因和具体冲突范围，由用户决定下一步。

---

### Step 3: 解决冲突

**核心原则：保留 fork 的 uvx 适配，合入上游的新功能。`skills/ppt-master/scripts/*.py` 零改动。**

| 冲突类型 | 解决策略 |
|----------|----------|
| `python3 scripts/xxx.py` vs `uvx ppt-master xxx` | 保留 uvx 格式 |
| `python3 skills/ppt-master/scripts/xxx.py` vs `uvx ppt-master xxx` | 保留 uvx 格式 |
| 上游新增文件中的 `python3` 命令 | 保持原样，Step 4 统一替换 |
| `AGENTS.md` / `CLAUDE.md` 命令参考 | 接受上游内容后，将 `python3` 替换为 `uvx` |
| `pyproject.toml` 依赖变更 | 手动审查，同步到两个 `pyproject.toml` |
| `update_repo.py` | 保留 fork 的 uv 功能（`ensure_uv_available`、`uv sync`、`--skip-deps`），合入上游新功能 |
| `generate_examples_index.py` | 确保内部字符串已替换为 `uvx` |

**冲突文件速查：**

| 文件 | 策略 |
|------|------|
| `*.md` workflow/reference | 接受上游内容，将所有 `python3` → `uvx` |
| `cli.py` (根 & skills) | 无冲突（上游无此文件）；检查新脚本映射 |
| `pyproject.toml` | 手动同步依赖；保留 version/tool.uv/tool.setuptools 段 |
| `skills/ppt-master/scripts/*.py` | **零改动**（跳过 `upstream-sync.md` 中的 `.py` 替换脚本） |

---

### Step 4: 适配 uvx 命令

#### 4a. 扫描所有 `python3` / `uv run` 残留

PowerShell 等效命令：

```powershell
rg --include '*.md' 'python3 skills/ppt-master/scripts/' skills/ppt-master/ AGENTS.md CLAUDE.md docs/
rg --include '*.md' 'python3 scripts/' skills/ppt-master/scripts/docs/
rg --include '*.md' 'uv run skills/ppt-master/scripts/' skills/ppt-master/ AGENTS.md CLAUDE.md docs/
```

记录所有匹配的文件和行。

---

#### 4b. 补全 cli.py 映射

运行检测脚本：

```bash
python skills/ppt-master/scripts/check_cli_sync.py
```

对于输出的每个缺失脚本：
1. 按 **kebab-case 命名**（下划线 `_` → 连字符 `-`，子目录只取文件名）
2. 同时添加到 **两个** `cli.py`（根目录 + `skills/ppt-master/`）：
   - `COMMANDS` 字典中按字母序插入
   - `COMMAND_DESCRIPTIONS` 字典中添加一行中文描述
3. 重新运行检测脚本确认同步

**kebab-case 命名示例：**

| 脚本文件 | 命令名 |
|----------|--------|
| `native_enhance_pptx.py` | `native-enhance-pptx` |
| `confirm_ui/server.py` | `confirm-ui` |
| `extract_svg_assets.py` | `extract-svg-assets` |
| `icon_sync.py` | `icon-sync` |
| `beautify_inventory.py` | `beautify-inventory` |
| `source_to_md/pdf_to_md.py` | `pdf-to-md` |
| `svg_editor/server.py` | `svg-editor` |

---

#### 4c. 批量替换 — 使用 Python 脚本自动化

编写并执行以下 Python 脚本，自动解析 cli.py 的 `COMMANDS` 映射并将所有 `python3` / `uv run` 调用替换为 `uvx ppt-master <command>`：

```python
import re, ast, pathlib

# 解析 cli.py 的 COMMANDS 字典（AST 方式，不执行代码避免导入失败）
tree = ast.parse(pathlib.Path('cli.py').read_text(encoding='utf-8'))
commands = {}
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
        vals = [v.value for v in node.values if isinstance(v, ast.Constant)]
        if 'project' in keys and 'project_manager.py' in vals:
            commands = dict(zip(keys, vals))
            break

# 构建脚本名 → uvx 命令名 的映射
script_to_cmd = {}
for cmd_name, script_rel in commands.items():
    script_name = script_rel.rsplit('/', 1)[-1]
    script_to_cmd[script_name] = cmd_name

# 需要处理的文件目录
target_dirs = ['AGENTS.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'skills/ppt-master/', 'docs/', 'examples/', 'projects/']
exclude_keywords = ['superpowers', 'windows-installation', 'code-style']

# 收集所有目标 .md 文件
files = []
for d in target_dirs:
    p = pathlib.Path(d)
    if p.is_file():
        files.append(p)
    elif p.is_dir():
        files.extend(f for f in p.rglob('*.md') if not any(k in str(f) for k in exclude_keywords))

# 统计
total_replacements = 0
for filepath in sorted(set(files)):
    content = filepath.read_text(encoding='utf-8')
    original = content
    for script_name, cmd_name in sorted(script_to_cmd.items()):
        # python3 skills/ppt-master/scripts/xxx.py → uvx ppt-master xxx
        content = re.sub(
            rf'python3\s+skills/ppt-master/scripts/(\S*/)?{re.escape(script_name)}',
            f'uvx ppt-master {cmd_name}', content
        )
        # python3 scripts/xxx.py → uvx ppt-master xxx
        content = re.sub(
            rf'(?<!\w)python3\s+scripts/(\S*/)?{re.escape(script_name)}',
            f'uvx ppt-master {cmd_name}', content
        )
        # uv run skills/ppt-master/scripts/xxx.py → uvx ppt-master xxx
        content = re.sub(
            rf'uv\s+run\s+skills/ppt-master/scripts/(\S*/)?{re.escape(script_name)}',
            f'uvx ppt-master {cmd_name}', content
        )
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        total_replacements += 1
        print(f'Updated: {filepath}')

print(f'\nDone: {total_replacements} files updated.')
```

**重要：** 脚本使用 AST 解析 `cli.py` 而非 `exec()` 执行，避免顶层导入失败。所有替换使用正则精确匹配，排除 `docs/superpowers/` 和 `docs/windows-installation.md` 等设计/故障排除文档。

---

#### 4d. 验证

```bash
# 确认 skills/ppt-master/ 下无 python3 残留
python -c "import subprocess; subprocess.run('rg --include *.md python3 skills/ppt-master/', shell=True)"

# 确认 cli.py 映射完整 + 双文件同步（一次调用检查两者）
python skills/ppt-master/scripts/check_cli_sync.py
```

`check_cli_sync.py` 一次运行会同时检查映射完整性和双 cli.py 同步。

---

### Step 5: 依赖同步

无论上游 requirements.txt 是否有变更，都运行验证确保三份清单一致：

```bash
uv lock && cd skills/ppt-master && uv lock && cd ..
python skills/ppt-master/scripts/check_deps_sync.py
```

如果上游 `requirements.txt` 新增/删除了依赖，手动同步到两个 `pyproject.toml` 的 `[project] dependencies` 后重新运行以上命令。

---

### Step 6: 提交、打版本号、推送

```bash
# 提交合并和适配（仅已追踪文件的更新 + 新文件）
git add -u
git add cli.py skills/ppt-master/cli.py pyproject.toml skills/ppt-master/pyproject.toml
git commit -m "merge upstream/main: resolve conflicts, adapt to uvx, sync cli.py mappings"

# 查看当前版本
python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"

# 编辑两个 pyproject.toml，version 字段末尾 +1（如 0.1.15 → 0.1.16）

# 提交版本号变更
git add pyproject.toml skills/ppt-master/pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
```

**如果在 GitHub Actions 环境中运行：**

- **OpenCode Action 路径（schedule 触发）**：跳过 push — action 会自动创建分支和 PR，PR 合并后触发下游 CI 链（`check-uvx-migration` → `auto-tag` → `publish-pypi`）
- **CLI 路径（workflow_dispatch / `opencode run`）**：直接 push 到 main。git remote 已配置为 `secrets.PUSH_PAT`，PAT 推送会自然触发下游 CI 链

CLI 路径执行：
```bash
git push origin main
```
push 后下游自动触发，无需手动 `gh workflow run`。

> ⚠️ 无论是哪种路径，都不要手动 `git tag`。tag 由 `auto-tag.yml` 统一管理。

**如果本地运行：**
```bash
git push origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

---

### Step 7: 验证 PyPI 发布

输出验证信息即可，不要尝试执行 `gh` CLI 命令。

**schedule 触发路径：** 输出 "PR 已创建，合并后 auto-tag → publish-pypi 自动触发。查看 https://github.com/elvisw/ppt-master/actions"

**workflow_dispatch 路径：** 输出 "Push 成功，下游 CI 链自动触发。查看 https://github.com/elvisw/ppt-master/actions"

**本地流程：** 输出 Actions 页面 URL，提醒用户运行 `uvx ppt-master --version` 验证。

---

## 参考文档

- 上游同步指南：`docs/zh/upstream-sync.md`
- uvx 改造最终笔记：`docs/superpowers/2026-06-08-uvx-refactor-final.md`
- uvx 改造设计：`docs/superpowers/specs/2026-06-08-uvx-refactor-design.md`
- CLI 命令映射：`cli.py` + `skills/ppt-master/cli.py`
- 同步检查脚本：`skills/ppt-master/scripts/check_cli_sync.py`
- 依赖同步检查：`skills/ppt-master/scripts/check_deps_sync.py`
- AGENTS.md 版本规范：`AGENTS.md`
