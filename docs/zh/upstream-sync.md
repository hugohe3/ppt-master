# 合并上游更新工作流

## 远程仓库布局

```
origin    → https://github.com/elvisw/ppt-master.git    (你的 fork)
upstream  → https://github.com/hugohe3/ppt-master.git   (原作者)
```

---

## 触发方式总览

| 方式 | 触发 | 适用场景 | 自动发布 |
|------|------|----------|----------|
| **定时自动 (schedule)** | 每周一 UTC 8:00 | 定期维护，无需人工干预 | ✅ 全自动 |
| **Issue 评论 (`/oc`)** | 在 Issue 下评论 `/oc /sync-upstream` | 临时手动触发，需要立刻同步 | ✅ PR 合并后自动 |
| **本地 CLI** | `.opencode/command/sync-upstream.md` | 本地开发时手动执行 | ❌ 手动打 tag |

---

### 方式一：定时自动（GitHub Actions schedule）

`sync-upstream.yml` 每周一 UTC 8:00（北京时间 16:00）自动运行：

```
schedule cron → OpenCode Agent 拉取上游 → 合并 → 适配 uvx → 创建 PR
→ PR 合并到 main → auto-tag.yml 门禁校验 → 打 tag → publish-pypi.yml 发布
```

**不需要任何手动操作。** PR 合并后全自动发布到 PyPI。

> **注意**: `schedule` 事件在 GitHub Actions 中自动跳过权限检查（无需人工批准），不会卡住。`workflow_dispatch` 事件需要权限批准，会无限等待 —— 因此 sync-upstream.yml **仅使用 schedule** 触发。

### 方式二：Issue 评论触发

1. 在仓库中创建一个 Issue
2. 评论 `/oc /sync-upstream`
3. `opencode.yml` 触发 OpenCode Agent，读取 `.opencode/command/sync-upstream.md` 执行全流程
4. Agent 创建分支 → 提交 → 创建 PR
5. 合并 PR → `auto-tag.yml` → `publish-pypi.yml` → PyPI

### 方式三：本地 OpenCode CLI

```bash
# 在项目根目录下
opencode
# 然后输入: /sync-upstream
```

或直接通过 comment 触发上方的 Issue 评论方式。

---

## GitHub Actions 工作流一览

| 工作流文件 | 触发 | 功能 |
|-----------|------|------|
| `sync-upstream.yml` | schedule (每周一) | OpenCode Agent 拉取上游、合并、适配 uvx、创建 PR |
| `auto-tag.yml` | push to main (pyproject.toml 变更) | 5 道门禁校验 + 自动打 tag → 触发 PyPI 发布 |
| `publish-pypi.yml` | tag push `v*` | 构建 wheel + 发布到 PyPI |
| `opencode.yml` | issue_comment `/oc` | 通用 OpenCode Agent 入口 |
| `check-uvx-migration.yml` | push to main (merge commit) | 检测合并提交中 `python3` 命令残留 |

### auto-tag.yml 门禁

```
Gate 0: 两个 pyproject.toml 版本一致
Gate 1: cli.py 映射完整 (check_cli_sync.py)
Gate 2: .md 文件中无 python3 残留
Gate 3: .md 文件中无 uv run 残留
Gate 4: 依赖清单一致 (check_deps_sync.py)
→ 全部通过 → git tag vX.Y.Z → publish-pypi.yml
```

---

## 冲突处理

### 核心原则

**保留 fork 的 uvx 适配，合入上游的新功能。`skills/ppt-master/scripts/*.py` 零改动。**

| 冲突类型 | 解决策略 |
|----------|----------|
| `python3 scripts/xxx.py` vs `uvx ppt-master xxx` | 保留 uvx |
| 上游新增 .md 文件中的 `python3` 命令 | 同化为 `uvx ppt-master <cmd>` |
| `cli.py` | 无冲突（上游无此文件）；检查新脚本是否已映射 |
| `pyproject.toml` | 保留 fork 结构（version, tool.uv, tool.setuptools），只同步依赖 |
| `update_repo.py` | 保留 fork 的 uv 功能，合入上游改进 |
| `skills/ppt-master/scripts/*.py` | **零改动** —— docstring 中 `python3` 残留已知且可接受 |

### 命令转换规则

**规则一：cli.py 已有映射 → `uvx ppt-master <command>`**

对于 `cli.py` 的 `COMMANDS` 字典中已存在的映射：
- `python3 skills/ppt-master/scripts/xxx.py` → `uvx ppt-master <cmd>`
- `python3 scripts/xxx.py` → `uvx ppt-master <cmd>`
- `uv run skills/ppt-master/scripts/xxx.py` → `uvx ppt-master <cmd>`
- `uv run scripts/xxx.py` → `uvx ppt-master <cmd>`

**规则二：cli.py 无映射 → 添加到 cli.py**

运行 `python skills/ppt-master/scripts/check_cli_sync.py` 检测缺失脚本。

kebab-case 命名：下划线 `_` → 连字符 `-`，子目录取文件名。同时添加到根目录和 `skills/ppt-master/` 两个 `cli.py` 的 `COMMANDS` 和 `COMMAND_DESCRIPTIONS`。

### 内部脚本（不转换）

以下脚本没有 cli.py 映射，保留 `uv run` 调用：
- `svg_finalize/flatten_tspan.py`
- `svg_finalize/svg_rect_to_path.py`
- `svg_finalize/fix_image_aspect.py`
- `svg_finalize/embed_icons.py`

### 豁免目录

以下目录不进行 `python3` → `uvx` 转换：
- `docs/superpowers/` — 设计文档
- `docs/windows-installation.md` — 安装文档
- `docs/rules/code-style.md` — 代码规范
- `docs/zh/upstream-sync.md` — 本文档

---

## 上游新增依赖时

1. 同步到两个 `pyproject.toml` 和 `requirements.txt`
2. 在两个目录运行 `uv lock`：
   ```bash
   uv lock && cd skills/ppt-master && uv lock
   ```
3. 运行校验：
   ```bash
   python skills/ppt-master/scripts/check_deps_sync.py
   ```

---

## 版本发布

### AGENTS.md 约束

打 `v*` tag 前，**必须** 更新两个 `pyproject.toml` 的 `version` 字段为同一值。

### 手动发布

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```
`publish-pypi.yml` 自动构建发布。

### 自动发布

`auto-tag.yml` 在门禁通过后自动打 tag。tag 推送触发 `publish-pypi.yml`。

---

## 重要注意事项

- **`.gitignore` 必须包含 `!uv.lock` 例外规则**（`*.lock` 会匹配 `uv.lock`）
- **`sync-upstream.yml` 不使用 `workflow_dispatch`** — OpenCode action 在 `workflow_dispatch` 事件下会卡在权限 `ask` 状态
- **`issue_comment` 权限问题** — OpenCode Agent 在 issue_comment 事件下可能也需要权限批准（依赖 actor 角色）。如果 repo 所有者在 issue 下评论，权限通常自动放行
- **`skills/ppt-master/scripts/*.py` 的 `python3` 残留** — `check_uvx_migration.yml` 已豁免该目录
- 合并后运行 `uvx ppt-master check-deps-sync` 验证依赖一致性
- 两处 `uv.lock` 文件必须提交以实现可重复构建

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `.opencode/command/sync-upstream.md` | OpenCode sync-upstream 命令定义 |
| `cli.py` | CLI 命令映射（根目录） |
| `skills/ppt-master/cli.py` | CLI 命令映射（skill 目录） |
| `skills/ppt-master/scripts/check_cli_sync.py` | CLI 映射完整性检查 |
| `skills/ppt-master/scripts/check_deps_sync.py` | 依赖清单一致性检查 |
| `skills/ppt-master/scripts/check_uvx_migration.py` | 合并提交中 python3 残留检测 |
| `docs/superpowers/specs/2026-06-08-uvx-refactor-design.md` | uvx 改造设计文档 |
| `docs/superpowers/2026-06-08-uvx-refactor-final.md` | uvx 改造最终笔记 |
