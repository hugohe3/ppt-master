# 测试报告修复实施计划（P0-1 + P1 系列）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 PPT-Master 测试报告的 P0-1（daemon health 校验）、P1-1（CLI 命令名/帮助）、P1-2（uvx 依赖标注）、P1-3（projects/ 路径统一），并发布 0.1.72。

**Architecture:** P0-1 用「启动 token 身份凭证 + 规范化路径兜底 + pid 仅诊断」重构三个 server 的就绪校验；P1-1 用独立 ALIASES 字典 + `--help` 透传 + auto_fix_uvx.py 正则扩展；P1-3 用 `projects_root()` 函数统一解析（`PPT_MASTER_PROJECTS` 环境变量优先，默认 `<cwd>/projects/`）。涉及 6 个上游文件，同步工作流登记 fork 修改文件清单。

**Tech Stack:** Python 3.12（标准库：subprocess/uuid/os/pathlib/re/ast）、Flask、GitHub Actions（auto-tag/sync-upstream/publish-pypi）、uvx。

## Global Constraints

- 版本号：`pyproject.toml` 与 `skills/ppt-master/pyproject.toml` 两处同步，0.1.71 → 0.1.72
- 本机 uvx 安装是 0.1.71 旧版：本地验证必须用 `uvx --from . ppt-master <cmd>`，发布后才用 `uvx ppt-master`
- 别名 `notes-split`/`svg-editor-server` 只进独立 `ALIASES` 字典，**禁止加入 COMMANDS**（auto_fix_uvx.py 反查污染）
- 两个 cli.py（根 + skills/ppt-master/）的命令名集合与 ALIASES 必须同步
- `auto_fix_uvx.py` 从 cwd 读 `cli.py`：运行必须在仓库根目录
- `attribution_guard.py` 的 `_SKILL_GATE_MARKER` 保持 `uvx ppt-master attribution-guard`（本 fork 不可回退）
- 每个 task 完成后运行：`python skills/ppt-master/scripts/check_cli_sync.py`（exit 0）+ `python skills/ppt-master/scripts/attribution_guard.py`（exit 0）
- Windows 下所有 Python 命令用 `python` 而非 `python3`

---

### Task 1: server_common.py 规范化 helper + confirm_ui token 校验

**Files:**
- Modify: `skills/ppt-master/scripts/server_common.py`（新增 `normalized_project_key`，被三个 server 共享）
- Modify: `skills/ppt-master/scripts/confirm_ui/server.py`
- Test: 无 pytest 基础设施；验证 = py_compile + daemon 功能验证（Task 8）

**Interfaces:**
- Consumes: `server_common.popen_detached(args, *, logger=None, **kwargs)`（已支持 env 透传）
- Produces: `server_common.normalized_project_key(project_path: object) -> str`（resolve + Windows casefold）
  `confirm_ui` 的 `_wait_for_server_ready(port, proc, project_path, timeout, launch_token: Optional[str] = None) -> bool`
  `_launch_background_server(...)` 内部生成 token 并经 env `PPT_MASTER_LAUNCH_TOKEN` 传给子进程

- [ ] **Step 1: server_common.py 新增 normalized_project_key**

在 `skills/ppt-master/scripts/server_common.py` 的 import 区确认 `from pathlib import Path` 已存在（无则添加），并在 `popen_detached` 之后新增：

```python
def normalized_project_key(project_path: object) -> str:
    """Return a canonical comparable key for a project path.

    Resolves symlinks and relative segments; on Windows the key is
    case-folded so drive-letter case differences (``c:\\`` vs ``C:\\``)
    do not defeat identity comparison.
    """
    resolved = Path(project_path).resolve()
    return str(resolved).casefold() if os.name == 'nt' else str(resolved)
```

- [ ] **Step 2: confirm_ui/server.py 的 import 增加 helper**

在 `skills/ppt-master/scripts/confirm_ui/server.py` 的 `from server_common import (...)` 块（63-73 行）中增加一行：

```python
    normalized_project_key as _normalized_project_key,
```

- [ ] **Step 3: 改造 `_wait_for_server_ready`（172-208 行）**

替换整个函数为（token 身份凭证 + 规范化路径 + pid 诊断 + 失败诊断）：

```python
def _wait_for_server_ready(
    port: int,
    proc: subprocess.Popen,
    project_path: Path,
    timeout: int = STARTUP_TIMEOUT,
    launch_token: Optional[str] = None,
) -> bool:
    """Wait until this project's detached confirm server is accepting requests."""
    deadline = time.time() + timeout
    last_error = ''
    health_url = _server_url(port, '/api/health')
    expected_project = _normalized_project_key(project_path)
    while time.time() < deadline:
        returncode = proc.poll()
        if returncode is not None:
            logger.error('confirm UI exited during startup (code=%s)', returncode)
            return False
        try:
            with urllib.request.urlopen(health_url, timeout=1) as resp:
                data = json.load(resp)
                if (
                    resp.status == 200
                    and isinstance(data, dict)
                    and data.get('service') == 'confirm_ui'
                    and _normalized_project_key(Path(data.get('project') or '')) == expected_project
                    and (launch_token is None or data.get('launch_token') == launch_token)
                ):
                    if data.get('pid') != proc.pid:
                        logger.warning(
                            'confirm UI health pid=%s differs from launcher pid=%s; '
                            'accepting (identity confirmed by launch token)',
                            data.get('pid'), proc.pid,
                        )
                    return True
                last_error = (
                    'health response belongs to another service or project: '
                    f'service={data.get("service")!r} project={data.get("project")!r} '
                    f'token={data.get("launch_token")!r} expected_project={expected_project!r}'
                )
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = str(exc)
        time.sleep(0.2)
    logger.error(
        'confirm UI did not become ready at %s within %ss%s',
        health_url,
        timeout,
        f' (last error: {last_error})' if last_error else '',
    )
    return False
```

- [ ] **Step 4: 改造 `_launch_background_server`（211-252 行）**

在 `cmd = [...]` 构建（224 行）之前插入 token 生成，并给 `_popen_detached` 传 env、给 `_wait_for_server_ready` 传 token：

```python
    launch_token = uuid.uuid4().hex
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        str(project_path),
        '--port',
        str(port),
        '--timeout',
        str(idle_timeout),
        '--no-browser',
    ]
    child_env = os.environ.copy()
    child_env['PPT_MASTER_LAUNCH_TOKEN'] = launch_token
    with log_path.open('a', encoding='utf-8') as log:
        proc = _popen_detached(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=child_env,
            logger=logger,
        )
    logger.info('log: %s', log_path)
    if not _wait_for_server_ready(port, proc, project_path, launch_token=launch_token):
```

注意：`uuid` 已在文件顶部 import（45 行）；`os` 已在 36 行。不需要新增 import。

- [ ] **Step 5: health 端点新增 launch_token 字段（1595-1624 行）**

在 `jsonify({...})` 字典中 `'project': str(project_path),` 之后新增一行：

```python
            'launch_token': os.environ.get('PPT_MASTER_LAUNCH_TOKEN'),
```

- [ ] **Step 6: 语法验证**

Run:
```powershell
python -m py_compile skills/ppt-master/scripts/server_common.py skills/ppt-master/scripts/confirm_ui/server.py
```
Expected: 无输出，exit 0

- [ ] **Step 7: Commit**

```bash
git add skills/ppt-master/scripts/server_common.py skills/ppt-master/scripts/confirm_ui/server.py
git commit -m "fix: daemon health check via launch token + normalized project path (confirm_ui)"
```

---

### Task 2: svg_editor token 校验

**Files:**
- Modify: `skills/ppt-master/scripts/svg_editor/server.py`

**Interfaces:**
- Consumes: `server_common.normalized_project_key`（Task 1）、`_popen_detached`（已有）
- Produces: `_wait_for_ready(port, proc, project_path, timeout, launch_token: Optional[str] = None) -> bool`（与 confirm_ui 对称）

- [ ] **Step 1: import 增加 uuid 与 helper**

在 `skills/ppt-master/scripts/svg_editor/server.py` 顶部 import 区新增 `import uuid`（`import os` 已在 25 行），并在 `from server_common import (...)` 块（65-75 行）中增加：

```python
    normalized_project_key as _normalized_project_key,
```

- [ ] **Step 2: 改造 `_wait_for_ready`（1075-1110 行）**

替换整个函数为（与 confirm_ui 对称）：

```python
def _wait_for_ready(
    port: int,
    proc: subprocess.Popen,
    project_path: Path,
    timeout: int = STARTUP_TIMEOUT,
    launch_token: Optional[str] = None,
) -> bool:
    """Wait until this project's detached live-preview server responds."""
    deadline = time.time() + timeout
    health_url = _server_url(port, '/api/health')
    last_error = ''
    expected_project = _normalized_project_key(project_path)
    while time.time() < deadline:
        if proc.poll() is not None:
            logger.error('live preview exited during startup (code=%s)', proc.returncode)
            return False
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                data = json.load(response)
                if (
                    response.status == 200
                    and isinstance(data, dict)
                    and data.get('service') == 'live_preview'
                    and _normalized_project_key(Path(data.get('project') or '')) == expected_project
                    and (launch_token is None or data.get('launch_token') == launch_token)
                ):
                    if data.get('pid') != proc.pid:
                        logger.warning(
                            'live preview health pid=%s differs from launcher pid=%s; '
                            'accepting (identity confirmed by launch token)',
                            data.get('pid'), proc.pid,
                        )
                    return True
                last_error = (
                    'health response belongs to another service or project: '
                    f'service={data.get("service")!r} project={data.get("project")!r} '
                    f'token={data.get("launch_token")!r} expected_project={expected_project!r}'
                )
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(0.25)
    logger.error(
        'live preview did not become ready at %s within %ss%s',
        health_url,
        timeout,
        f' (last error: {last_error})' if last_error else '',
    )
    return False
```

- [ ] **Step 3: main() daemon 分支生成 token 并传 env（1258-1315 行）**

在 `cmd = [` 构建（1281 行）之前插入 token 生成与 env 构建，替换 1293-1301 行的 `_popen_detached` 调用：

```python
        launch_token = uuid.uuid4().hex
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            str(project_path),
            '--port',
            str(port),
            '--timeout',
            str(idle_timeout),
            '--no-browser',
        ]
        if args.live:
            cmd.append('--live')
        child_env = os.environ.copy()
        child_env['PPT_MASTER_LAUNCH_TOKEN'] = launch_token
        try:
            with log_path.open('a', encoding='utf-8') as log:
                proc = _popen_detached(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=child_env,
                    logger=logger,
                )
        except OSError as exc:
            logger.error('cannot write live preview log: %s (%s)', log_path, exc)
            return 1
        url = _server_url(port)
        if not _wait_for_ready(port, proc, project_path, launch_token=launch_token):
```

- [ ] **Step 4: health 端点新增 launch_token 字段（501-518 行）**

在 `jsonify({...})` 字典中 `'project': str(project_path),` 之后新增一行：

```python
            'launch_token': os.environ.get('PPT_MASTER_LAUNCH_TOKEN'),
```

- [ ] **Step 5: 语法验证**

Run:
```powershell
python -m py_compile skills/ppt-master/scripts/svg_editor/server.py
```
Expected: 无输出，exit 0

- [ ] **Step 6: Commit**

```bash
git add skills/ppt-master/scripts/svg_editor/server.py
git commit -m "fix: live preview daemon health check via launch token + normalized path"
```

---

### Task 3: visual_review.py project 规范化

**Files:**
- Modify: `skills/ppt-master/scripts/visual_review.py`

**Interfaces:**
- Consumes: `server_common.normalized_project_key`（Task 1）
- Produces: `check_server(server_url, project_path)` 接受 casefold 规范化比较；legacy 分支行为不变

- [ ] **Step 1: import 增加 helper**

在 `skills/ppt-master/scripts/visual_review.py` 的 43 行 `from server_common import lock_pid, process_alive, read_lock` 中增加：

```python
from server_common import lock_pid, normalized_project_key, process_alive, read_lock
```

- [ ] **Step 2: 改造 `check_server`（235-260 行）**

替换 245 行与 253-256 行的比较逻辑（不动 legacy 分支）：

```python
    expected_project = normalized_project_key(project_path)
    expected_svg_output = str((project_path / 'svg_output').resolve())
    service = data.get('service') if isinstance(data, dict) else None
    legacy_live_preview = (
        service is None
        and isinstance(data, dict)
        and data.get('svg_output') == expected_svg_output
    )
    if (
        not isinstance(data, dict)
        or normalized_project_key(Path(data.get('project') or '')) != expected_project
        or (service != 'live_preview' and not legacy_live_preview)
    ):
        raise RuntimeError(
            f'URL does not belong to this project live preview: {server_url}'
        )
```

- [ ] **Step 3: 语法验证**

Run:
```powershell
python -m py_compile skills/ppt-master/scripts/visual_review.py
```
Expected: 无输出，exit 0

- [ ] **Step 4: Commit**

```bash
git add skills/ppt-master/scripts/visual_review.py
git commit -m "fix: normalize project path comparison in visual review server check"
```

---

### Task 4: cli.py ×2 — ALIASES + --help 透传

**Files:**
- Modify: `cli.py`（根）
- Modify: `skills/ppt-master/cli.py`

**Interfaces:**
- Produces: `ALIASES` 字典（独立于 COMMANDS）+ main() 的 `--help` 判定只检查 argv[1]

- [ ] **Step 1: 根 cli.py 增加 ALIASES**

在根 `cli.py` 的 `COMMAND_DESCRIPTIONS` 字典结束之后、`def main` 之前插入：

```python
# Alias names tolerated for documentation/backward compatibility. Must stay
# separate from COMMANDS: auto_fix_uvx.py derives its normalization mapping
# from COMMANDS, and an alias key would overwrite the canonical command name.
ALIASES = {
    "notes-split": "total-md-split",
    "svg-editor-server": "svg-editor",
}
```

- [ ] **Step 2: 根 cli.py 修改 main() 的 help 判定与命令解析（152-172 行）**

将 156 行改为只检查 argv[1]，并在 165 行 `cmd = argv[1]` 处加别名解析：

```python
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print("Usage: ppt-master <command> [args...]")
        print("\nCommands:")
        width = max(len(k) for k in COMMANDS) + 2
        for name in sorted(COMMANDS):
            desc = COMMAND_DESCRIPTIONS.get(name, "")
            print(f"  {name:<{width}}{desc}")
        return 0

    cmd = ALIASES.get(argv[1], argv[1])
    args = argv[2:]

    script_rel = COMMANDS.get(cmd)
```

- [ ] **Step 3: skills/ppt-master/cli.py 同样修改**

对 `skills/ppt-master/cli.py` 重复 Step 1 与 Step 2 的完全相同修改（两个文件必须逐字一致）。

- [ ] **Step 4: 验证双文件同步 + 帮助透传**

Run:
```powershell
python skills/ppt-master/scripts/check_cli_sync.py
python cli.py project init --help
python cli.py notes-split --help
python cli.py svg-editor-server --help
python cli.py --help
```
Expected: check_cli_sync exit 0；`project init --help` 显示 init 的参数说明（含 project_name/--format/--dir）；`notes-split --help` / `svg-editor-server --help` 显示对应子脚本帮助；`cli.py --help` 显示顶层命令列表。

- [ ] **Step 5: Commit**

```bash
git add cli.py skills/ppt-master/cli.py
git commit -m "feat: cli aliases (notes-split, svg-editor-server) and pass-through --help"
```

---

### Task 5: projects_root() 路径统一

**Files:**
- Modify: `skills/ppt-master/scripts/project_management/paths.py`
- Modify: `skills/ppt-master/scripts/project_manager.py`
- Modify: `skills/ppt-master/scripts/project_management/cli.py`
- Modify: `skills/ppt-master/scripts/config.py`

**Interfaces:**
- Produces: `project_management.paths.projects_root() -> Path`（env `PPT_MASTER_PROJECTS` 优先，否则 `(Path.cwd()/"projects").resolve()`）；`PROJECTS_ROOT` 常量删除；`REPO_ROOT` 保留

- [ ] **Step 1: paths.py 新增 projects_root()**

在 `skills/ppt-master/scripts/project_management/paths.py` 顶部增加 `import os`（17 行 `from pathlib import Path` 之后），并替换第 23 行 `PROJECTS_ROOT = REPO_ROOT / "projects"` 为：

```python
def projects_root() -> Path:
    """Project workspace root: env PPT_MASTER_PROJECTS > <cwd>/projects."""
    env = os.environ.get("PPT_MASTER_PROJECTS")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / "projects").resolve()
```

`REPO_ROOT`（22 行）保留（`project_management/cli.py` 依赖它作子进程 cwd）。

- [ ] **Step 2: project_manager.py 接入**

在 `skills/ppt-master/scripts/project_manager.py`：
1. 删除 56 行 `PROJECTS_ROOT = REPO_ROOT / "projects"`（`REPO_ROOT` 54 行保留，354 行 cwd 用）
2. 在 56 行原位置（或 import 区）新增 `from project_management.paths import projects_root  # noqa: E402`
3. 209 行：`self.base_dir = Path(base_dir) if base_dir is not None else projects_root()`
4. 798 行：`inside_projects = is_within_path(source_path, projects_root())`
5. 807 行：f-string 内 `{PROJECTS_ROOT}` → `{projects_root()}`
6. 971 行：`if copy or not is_within_path(directory, projects_root()):`

- [ ] **Step 3: project_management/cli.py 接入**

在 `skills/ppt-master/scripts/project_management/cli.py`：
1. 43-48 行 import 块：`PROJECTS_ROOT` 条目替换为 `projects_root,`（保持相对导入风格：`from .paths import (REPO_ROOT, SCRIPTS_DIR, SOURCE_TO_MD_DIR, projects_root,)`）
2. 829 行：`is_within_path(source_path, PROJECTS_ROOT)` → `is_within_path(source_path, projects_root())`
3. 838 行：f-string 内 `{PROJECTS_ROOT}` → `{projects_root()}`
4. 1002 行：`is_within_path(directory, PROJECTS_ROOT)` → `is_within_path(directory, projects_root())`

- [ ] **Step 4: config.py 接入**

在 `skills/ppt-master/scripts/config.py` 顶部 import 区（23 行 `from console_encoding import configure_utf8_stdio` 附近）新增：

```python
from project_management.paths import projects_root
```

并替换 44 行 `PROJECTS_DIR = REPO_ROOT / 'projects'` 为：

```python
PROJECTS_DIR = projects_root()
```

- [ ] **Step 5: 语法 + 功能验证**

Run:
```powershell
python -m py_compile skills/ppt-master/scripts/project_management/paths.py skills/ppt-master/scripts/project_manager.py skills/ppt-master/scripts/project_management/cli.py skills/ppt-master/scripts/config.py
python -c "import sys; sys.path.insert(0, 'skills/ppt-master/scripts'); from project_management.paths import projects_root; print(projects_root())"
```
Expected: py_compile 无输出 exit 0；第二个命令打印 `<cwd>\projects` 的绝对规范化路径。

- [ ] **Step 6: Commit**

```bash
git add skills/ppt-master/scripts/project_management/paths.py skills/ppt-master/scripts/project_manager.py skills/ppt-master/scripts/project_management/cli.py skills/ppt-master/scripts/config.py
git commit -m "fix: unify projects root resolution (PPT_MASTER_PROJECTS env, default cwd/projects)"
```

---

### Task 6: auto_fix_uvx.py ${SKILL_DIR} 正则 + 文档修复

**Files:**
- Modify: `skills/ppt-master/scripts/auto_fix_uvx.py`
- Modify（自动）: `skills/ppt-master/workflows/generate-pptx.md`（22 处）、`skills/ppt-master/workflows/profiles/quick-generate.md`（3 处）、`skills/ppt-master/references/artifact-ownership.md`（7 处）
- Modify（手工）: `skills/ppt-master/workflows/generate-pptx.md`（P1-2 依赖标注）、`skills/ppt-master/workflows/stages/topic-research.md`（projects/ 锚定）

**Interfaces:**
- Consumes: 根 `cli.py` 的 COMMANDS 映射（AST 解析）
- Produces: `auto_fix_uvx.py` 支持 `python3 ${SKILL_DIR}/scripts/xxx.py` → `uvx ppt-master xxx` 替换

- [ ] **Step 1: auto_fix_uvx.py 新增 ${SKILL_DIR} 正则**

在 `skills/ppt-master/scripts/auto_fix_uvx.py` 的 44-49 行循环内、现有四条 `re.sub` 之后新增：

```python
            content = re.sub(
                rf"python3\s+\$\{{SKILL_DIR\}}/scripts/(\S*/)?{p}",
                f"uvx ppt-master {cmd_name}",
                content,
            )
```

注意 f-string 转义：`\$\{{SKILL_DIR\}}` 产生正则 `\$\{SKILL_DIR\}`（字面 `$`、`{`、`}`），与 46-49 行同风格。仅匹配 `scripts/` 前缀，`templates/`、`references/` 引用不受影响。

- [ ] **Step 2: 运行 auto_fix_uvx.py 修复残留（必须 cwd = 仓库根）**

Run:
```powershell
python skills/ppt-master/scripts/auto_fix_uvx.py
```
Expected: 输出 `Fixed: skills/ppt-master/workflows/generate-pptx.md`、`Fixed: skills/ppt-master/workflows/profiles/quick-generate.md`、`Fixed: skills/ppt-master/references/artifact-ownership.md`，共 3 个文件；`Total files auto-fixed: 3`

- [ ] **Step 3: 验证零残留**

Run:
```powershell
rg -g '*.md' -e 'python3 (scripts/|skills/)' -e 'python3 \$\{SKILL_DIR\}/scripts/' . --glob '!.opencode/**' --glob '!docs/superpowers/**' --glob '!docs/zh/upstream-sync.md'
```
Expected: 无输出（空）

- [ ] **Step 4: generate-pptx.md 补 uvx 依赖标注（P1-2）**

在 `skills/ppt-master/workflows/generate-pptx.md` 第 7 行 blockquote 之后新增：

```markdown
**执行环境**：本路由所有脚本命令须经 `uvx ppt-master <command>` 执行（uvx 环境自带依赖）。直接 `python` 调用脚本需先安装 `skills/ppt-master/requirements.txt`。
```

- [ ] **Step 5: topic-research.md 补 projects/ 语义锚定（P1-3 文档部分）**

在 `skills/ppt-master/workflows/stages/topic-research.md` 第 88 行 `Write two artifacts under \`projects/\`:` 之后新增：

```markdown
> `projects/` 指项目工作区根（`PPT_MASTER_PROJECTS` 环境变量指定的目录，或默认 `<cwd>/projects/`）。
```

- [ ] **Step 6: 回归验证**

Run:
```powershell
python skills/ppt-master/scripts/check_cli_sync.py
python skills/ppt-master/scripts/attribution_guard.py
```
Expected: 两命令 exit 0

- [ ] **Step 7: Commit**

```bash
git add skills/ppt-master/scripts/auto_fix_uvx.py skills/ppt-master/workflows/generate-pptx.md skills/ppt-master/workflows/profiles/quick-generate.md skills/ppt-master/references/artifact-ownership.md skills/ppt-master/workflows/stages/topic-research.md
git commit -m "fix: auto_fix_uvx covers \${SKILL_DIR} form; annotate uvx env + projects root docs"
```

---

### Task 7: 同步工作流与发布门禁扩展

**Files:**
- Modify: `.opencode/command/sync-upstream.md`
- Modify: `.github/workflows/sync-upstream.yml`
- Modify: `.github/workflows/auto-tag.yml`

- [ ] **Step 1: sync-upstream.md 核心原则更新（52 行）**

将 52 行改为：

```markdown
**核心原则：保留 fork 的 uvx 适配，合入上游的新功能。`skills/ppt-master/scripts/*.py` 除 `attribution_guard.py` 与下方「fork 修改文件清单」列出的文件外零改动。**

**fork 修改文件清单**（这些文件含 fork 独有的 Windows/uvx 适配，上游更新时**保留 fork 适配标记、合入上游功能改动**，不得整文件回退）：

| 文件 | 关键适配标记 |
|------|-------------|
| `confirm_ui/server.py` | `PPT_MASTER_LAUNCH_TOKEN`（launch token 校验）、`normalized_project_key`（Windows casefold 路径比较） |
| `svg_editor/server.py` | `PPT_MASTER_LAUNCH_TOKEN`、`normalized_project_key` |
| `visual_review.py` | `normalized_project_key` |
| `server_common.py` | `normalized_project_key` 函数本身 |
| `config.py` | `projects_root()`（`PPT_MASTER_PROJECTS`） |
| `project_management/paths.py` | `projects_root()` 函数 |
| `project_manager.py` | `projects_root()` 接入 |

合并后必须逐文件 grep 验证适配标记仍在（见 Step 4e 门禁 4）。
```

- [ ] **Step 2: sync-upstream.md 4a 扫描命令（84-92 行）**

将 84-87 行的 python3 扫描命令改为：

```bash
# 扫描 python3 命令残留（全仓库 .md 文件）
rg -g '*.md' -e 'python3 (scripts/|skills/)' -e 'python3 \$\{SKILL_DIR\}/scripts/' . \
  --glob '!.opencode/**' \
  --glob '!docs/superpowers/**' \
  --glob '!docs/zh/upstream-sync.md'
```

- [ ] **Step 3: sync-upstream.md 4c 批量替换脚本（168-177 行）**

在脚本的两条 `python3` `re.sub` 之后（178 行 `uv run` 之前）新增：

```python
        # python3 ${SKILL_DIR}/scripts/xxx.py → uvx ppt-master xxx
        content = re.sub(
            rf'python3\s+\$\{{SKILL_DIR\}}/scripts/(\S*/)?{re.escape(script_name)}',
            f'uvx ppt-master {cmd_name}', content
        )
```

- [ ] **Step 4: sync-upstream.md 4d 验证命令（198-203 行）**

将 199-202 行改为与 Step 2 相同的双模式 rg 命令。

- [ ] **Step 5: sync-upstream.md 4e 门禁新增第 4 项（216-228 行）**

在 4e 三项列表后新增：

```markdown
4. **fork 适配完整性**：对「fork 修改文件清单」的每个文件 grep 验证其关键适配标记仍在（`PPT_MASTER_LAUNCH_TOKEN`、`normalized_project_key`、`projects_root`），任一缺失必须修复后再提交
```

- [ ] **Step 6: sync-upstream.yml 两个 prompt 追加门禁**

1. schedule prompt（59-82 行）在现有 guard 段落后追加：

```
CRITICAL: After the python3 and skill guard gates, verify fork adaptation markers
still exist: grep for PPT_MASTER_LAUNCH_TOKEN in scripts/confirm_ui/server.py and
scripts/svg_editor/server.py, grep for normalized_project_key in server_common.py,
and grep for projects_root in project_management/paths.py and config.py. If any
marker is missing, restore the fork adaptation before committing.
```

2. manual prompt（99 行）在行尾追加同样的门禁要求（紧接 "Do NOT commit or push until both gates pass." 之后）：

```
 Also verify fork adaptation markers (PPT_MASTER_LAUNCH_TOKEN in confirm_ui/server.py + svg_editor/server.py, normalized_project_key in server_common.py, projects_root in paths.py/config.py) still exist; restore them if missing before committing.
```

- [ ] **Step 7: auto-tag.yml Gate 2 追加 ${SKILL_DIR} 模式（99 行）**

将 99 行替换为：

```yaml
          MATCHES=$(grep -rn --include='*.md' -E 'python3 (skills/ppt-master/scripts/|\$\{SKILL_DIR\}/scripts/)' skills/ppt-master/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | grep -v 'superpowers' | grep -v 'windows-installation' | grep -v 'code-style' | grep -v 'upstream-sync' || true)
```

注意：`grep -E` 下 `\$`、`\{`、`\}` 需转义（bash 单引号内字面传递）；既有 `grep -v` 排除项不变。

- [ ] **Step 8: 验证**

Run:
```powershell
python -c "import yaml; yaml.safe_load(open('.github/workflows/sync-upstream.yml', encoding='utf-8')); yaml.safe_load(open('.github/workflows/auto-tag.yml', encoding='utf-8')); print('yaml OK')"
```
Expected: 输出 `yaml OK`（若环境无 PyYAML，改为目视检查缩进与引号配对）

- [ ] **Step 9: Commit**

```bash
git add .opencode/command/sync-upstream.md .github/workflows/sync-upstream.yml .github/workflows/auto-tag.yml
git commit -m "chore: register fork-modified files in sync workflow; extend scans to \${SKILL_DIR}"
```

---

### Task 8: bump 0.1.72 + 本地验证 + 发布

**Files:**
- Modify: `pyproject.toml`、`skills/ppt-master/pyproject.toml`

**Interfaces:**
- Produces: 发布链产物 0.1.72（check-uvx-migration → auto-tag Gate 0-6 → publish-pypi）

- [ ] **Step 1: 两处版本 bump**

将根 `pyproject.toml` 与 `skills/ppt-master/pyproject.toml` 的 `version = "0.1.71"` 改为 `version = "0.1.72"`。

- [ ] **Step 2: 完整回归**

Run:
```powershell
python skills/ppt-master/scripts/check_cli_sync.py
python skills/ppt-master/scripts/attribution_guard.py
python skills/ppt-master/scripts/check_deps_sync.py
python -m py_compile skills/ppt-master/scripts/confirm_ui/server.py skills/ppt-master/scripts/svg_editor/server.py skills/ppt-master/scripts/visual_review.py skills/ppt-master/scripts/server_common.py skills/ppt-master/scripts/project_management/paths.py skills/ppt-master/scripts/project_manager.py skills/ppt-master/scripts/project_management/cli.py skills/ppt-master/scripts/config.py skills/ppt-master/scripts/auto_fix_uvx.py cli.py skills/ppt-master/cli.py
```
Expected: 全部 exit 0

- [ ] **Step 3: P0-1 核心验收（uvx --from .）**

Run（用任意已有项目目录替换 `<proj>`，如 `projects/demo`）:
```powershell
uvx --from . ppt-master confirm-ui <proj> --daemon
uvx --from . ppt-master svg-editor <proj> --live --daemon
```
Expected: 两命令显示启动日志（`started ... in background`）并返回 0，浏览器打开；控制台无「failed to become reachable」

- [ ] **Step 4: P1-1/P1-3 功能验收**

Run:
```powershell
uvx --from . ppt-master project init --help
uvx --from . ppt-master project init demo_check --format ppt169
$env:PPT_MASTER_PROJECTS = "$pwd\alt-projects"
uvx --from . ppt-master project init demo_alt --format ppt169
Remove-Item Env:PPT_MASTER_PROJECTS
```
Expected: `project init --help` 显示 init 参数；`demo_check` 落在 `<cwd>/projects/demo_check`；`demo_alt` 落在 `<cwd>/alt-projects/demo_alt`；随后清理两个测试项目目录

- [ ] **Step 5: Commit 版本**

```bash
git add pyproject.toml skills/ppt-master/pyproject.toml
git commit -m "chore: bump version to 0.1.72"
```

- [ ] **Step 6: Push 触发发布链**

Run:
```bash
git push origin main
```
Expected: GitHub Actions 依次触发 check-uvx-migration（exit 2 跳过，因非 merge commit）→ auto-tag（Gate 0-6 全过，建 tag v0.1.72）→ publish-pypi（uv build + wheel guard + uv publish）。查看 https://github.com/elvisw/ppt-master/actions

- [ ] **Step 7: wheel 级验收**

Run（等待 publish-pypi 完成后）:
```powershell
uvx ppt-master attribution-guard
uvx ppt-master confirm-ui --help
```
Expected: attribution-guard exit 0；confirm-ui --help 显示选项。发布后首次运行 `uvx` 会拉取 0.1.72 新版本。
