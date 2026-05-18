# 合并上游更新工作流

## 远程仓库布局

```
origin    → https://github.com/elvisw/ppt-master.git    (你的 fork)
upstream  → https://github.com/hugohe3/ppt-master.git   (原作者)
```

## 日常操作

### 方式一：GitHub Sync fork 按钮（推荐，省事）

1. 打开 https://github.com/elvisw/ppt-master
2. 点击 **Sync fork** → **Update branch**
3. 本地拉取：`git pull origin main`

> Sync fork 在 GitHub 服务器端完成 fetch + merge，不会产生本地冲突。如果 GitHub 上显示冲突（极少见），改用方式二手动处理。

### 方式二：CLI 手动合并（精细控制）

```bash
# 1. 确保工作区干净
git status

# 2. 拉取上游最新代码
git fetch upstream

# 3. 查看上游更新了什么
git log main..upstream/main --oneline

# 4. 合并
git merge upstream/main

# 5. 推送到你的 fork
git push origin main
```

## 冲突处理

### 机械替换类冲突（workflows/references/脚本文档）

这些文件的差异本质上是 `python3` ↔ `uv run` 的替换，涵盖 `.md` 和 `.py` 文件。

```bash
# 接受上游版本，然后自动做 uv 替换
git checkout --theirs <冲突文件>
# 对该文件执行机械替换（详见下方自动化脚本）
git add <冲突文件>
```

### 核心文件冲突速查

| 文件 | 解决策略 |
|---|---|
| `SKILL.md` | 保留上游内容，把 `python3` 换成 `uv run` |
| `CLAUDE.md` | 同上 |
| `update_repo.py` | 人工审查：保留 `ensure_uv_available`、`uv sync`、`--skip-deps`、双文件哈希校验；合入上游其他新功能 |
| `pyproject.toml` | 如果上游在 `requirements.txt` 新增/删除依赖，手动同步到 `[project] dependencies`，然后 `uv lock` |
| `.python-version` | 永不冲突（上游无此文件） |
| `generate_examples_index.py` | 该脚本会重新生成 `examples/README.md`，必须确保其内部字符串也已替换为 `uv run`，否则下次运行会覆盖迁移结果 |
| `docs/windows-installation.md` | 人工审查：保留 uv 安装流程，合入上游其他文档改进 |

### 自动化机械替换

以下 PowerShell 脚本一次性处理所有 markdown 和 Python 文件的机械替换：

```powershell
# === Markdown 文件 ===
Get-ChildItem -Recurse -Filter "*.md" | ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    $c = $c -replace 'python3 scripts/', 'uv run scripts/'
    $c = $c -replace 'python3 skills/ppt-master/scripts/', 'uv run skills/ppt-master/scripts/'
    $c = $c -replace 'python3 \$\{SKILL_DIR\}', 'uv run ${SKILL_DIR}'
    $c = $c -replace 'python3 -m http.server', 'uv run python -m http.server'
    $c = $c -replace 'python3 -m pip install', 'uv pip install'
    Set-Content $_.FullName -Value $c -NoNewline
}

# === Python 文件（docstring / help 文本 / print 语句） ===
Get-ChildItem -Recurse -Filter "*.py" | ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    $c = $c -replace 'python3 scripts/', 'uv run scripts/'
    $c = $c -replace 'python3 skills/ppt-master/scripts/', 'uv run skills/ppt-master/scripts/'
    $c = $c -replace 'python3 (image_gen|update_spec|pptx_to_svg|project_utils)\.py', 'uv run scripts/$1.py'
    $c = $c -replace 'python3 -m http\.server', 'uv run python -m http.server'
    $c = $c -replace 'python3 -m pip install', 'uv pip install'
    Set-Content $_.FullName -Value $c -NoNewline
}
```

## 上游新增依赖时

如果上游在 `requirements.txt` 新增了包：

1. 手动将新依赖添加到 `pyproject.toml` 的 `[project] dependencies`
2. 运行 `uv lock` 更新锁文件
3. 运行 `uv sync` 安装

## 注意事项

- Sync fork 和 CLI 合并**不要混着用在同一批更新上**，选一种方式即可
- 合并后先跑 `uv run python -c "import pptx; print('OK')"` 验证依赖正常
- `uv lock` 生成的 `uv.lock` 文件不需要提交（已在 `.gitignore` 中）
