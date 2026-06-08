# uvx 改造 — 最终实现笔记

> 原始设计文档：`docs/superpowers/specs/2026-06-08-uvx-refactor-design.md`  
> 实现计划：`docs/superpowers/plans/2026-06-08-uvx-refactor.md`

## 与原始设计的差异

| 方面 | 原设计 | 最终实现 | 原因 |
|------|--------|----------|------|
| 安装方式 | `uv tool install --from .` | PyPI 发布后 `uvx` 自动下载 | 零安装步骤，用户体验最优 |
| Shell 调用 | Subprocess 分派到脚本文件 | 不变 | |
| 图标打包 | `package-data` `**/*` 通配 | `MANIFEST.in` + `recursive-include` | setuptools 不支持 `**` 递归 glob |
| 资源文件 | 仅 `**.py` + `**.json` | `**/*`（全部文件） | svg_editor/static、assets/ 等目录有非 Python 文件 |
| 模板目录 | 未纳入 | `templates/` 全部纳入（含 11K 图标） | icons、layouts、charts、brands、decks 均需运行时访问 |
| 构建速度 | 本地 `uv build` ~4min | `uvx` 从 PyPI 拉取预构建 wheel | 11K 图标本地打包太慢 |
| 版本号 | 硬编码 `0.1.0` | `uvx` 无版本概念 | 从 PyPI 发布自动解析 |
| Skill 独立构建 | 未考虑 | 新增 `skills/ppt-master/cli.py` + 独立 `pyproject.toml` | Skill 被复制到 `~/.claude/skills/` 独立使用 |
| CI | GitHub Releases 发布 wheel | PyPI Trusted Publishing | `uvx` 需要 PyPI 来源 |
| `project_manager.py` cwd | 始终指向 `REPO_ROOT` | `REPO_ROOT.is_dir()` 回退 | 打包后 `REPO_ROOT` 路径不存在 |

## 关键文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `cli.py` | 新增（根） | 统一入口，35 子命令 |
| `skills/ppt-master/cli.py` | 新增 | Skill 目录入口（`scripts/` 相对路径） |
| `MANIFEST.in` | 新增（根） | 递归包含 scripts + templates |
| `skills/ppt-master/MANIFEST.in` | 新增 | 同上（skill 目录版） |
| `skills/__init__.py` | 新增 | 包标记 |
| `skills/ppt-master/__init__.py` | 新增 | 包标记 |
| `skills/ppt-master/scripts/__init__.py` | 新增 | 包标记 |
| `skills/ppt-master/templates/__init__.py` | 新增 | 包标记 |
| `skills/ppt-master/templates/icons/__init__.py` | 新增 | 包标记 |
| `skills/ppt-master/scripts/check_cli_sync.py` | 新增 | 双 cli.py 同步检查 |
| `.github/workflows/check-cli-sync.yml` | 新增 | CI 自动检查 |
| `.github/workflows/publish-pypi.yml` | 新增 | Tag 推送到 PyPI |
| `pyproject.toml` | 修改 | `package=true` + `[project.scripts]` + `[project.urls]` |
| `skills/ppt-master/pyproject.toml` | 修改 | 同上 + setuptools 配置 |
| `CLAUDE.md` / `AGENTS.md` / `SKILL.md` | 修改 | 命令迁移到 `uvx` |
| `skills/ppt-master/workflows/*.md` | 修改 | 同上 |
| `skills/ppt-master/references/*.md` | 修改 | 同上 |
| `skills/ppt-master/scripts/docs/*.md` | 修改 | 同上 |

## 使用方式

```bash
# 无需安装，直接运行
uvx ppt-master project init myproj
uvx ppt-master pdf-to-md paper.pdf
uvx ppt-master svg-editor myproj --live
```

## 发布新版本

```bash
git tag v0.2.0 && git push origin v0.2.0
```

GitHub Actions 自动构建并发布到 PyPI。
