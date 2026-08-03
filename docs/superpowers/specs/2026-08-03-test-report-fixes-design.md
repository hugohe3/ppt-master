# 设计文档：测试报告问题修复（P0-1 + P1 系列）

**日期**: 2026-08-03
**状态**: 已确认，待实施
**来源**: `C:\Users\elvis\Documents\dev\test\ppt\PPT-Master测试报告.md`（2026-08-03 端到端测试）

## 1. 背景

2026-08-03 对 uvx 适配后的 ppt-master fork 进行了完整端到端测试（Generate PPTX 默认管线，3 页 AI 概述演示）。核心管线质量良好，问题集中在**环境适配层**：

| 编号 | 严重度 | 问题 |
|------|--------|------|
| P0-1 | 严重 | `--daemon` 后台启动模式在本机不可用（health 校验在 Windows/uvx 组合下失败） |
| P1-1 | 中等 | uvx CLI 命令名与文档不一致；`project init --help` 不透传子命令 |
| P1-2 | 中等 | 系统 Python 缺依赖，文档未标注须经 uvx 执行 |
| P1-3 | 中等 | `projects/` 路径约定不一致（init 落地 `<cwd>/projects`，`PROJECTS_ROOT` 解析到安装位置） |

P2（门禁内容问题）与 P3（PowerShell 编码注意事项）为质量基线参考，**本次不处理**。

## 2. 目标与范围

- 范围 B：修复 P0-1、P1-1、P1-2、P1-3
- P0-1 采用「启动 token 身份凭证 + 规范化路径兜底 + pid 仅诊断」方案
- P1-1 采用「别名 + 文档修复 + `--help` 透传」方案
- P1-3 采用「`PPT_MASTER_PROJECTS` 环境变量优先，默认 `<cwd>/projects/`」方案
- 修复完成后发布 0.1.72（两处 pyproject.toml 同步 bump）

## 3. P0-1：health 校验重构

**改动三个文件**：`scripts/confirm_ui/server.py`、`scripts/svg_editor/server.py`、`scripts/visual_review.py`。

> `visual_review.py:245-255` 的 `check_server` 存在同族问题（`expected_project = str(project_path)` 精确比较），一并纳入规范化修复。

### 3.1 启动 token 身份凭证

- confirm_ui：启动器 `_launch_background_server`；svg_editor：daemon 启动逻辑**内联在 `main()` 的 `args.daemon` 分支**（约 1281-1301 行 cmd 构建与 `_popen_detached` 调用之间），无独立启动函数——两处都生成随机 token（`uuid.uuid4().hex`）
- 通过环境变量 `PPT_MASTER_LAUNCH_TOKEN` 传给 detached 子进程（`_popen_detached` 的 `env` 参数）
- **env 必须基于 `os.environ.copy()` 合并**：`subprocess.Popen(env=...)` 是整体替换而非合并，只传 token 会丢失 PATH/系统环境导致子进程无法启动
- 子进程 `/api/health` 响应新增 `launch_token` 字段（`os.environ.get('PPT_MASTER_LAUNCH_TOKEN')`）
- 启动器等待就绪时：**token 相等作为身份凭证**，替换原 `pid == proc.pid` 判定

### 3.2 project 规范化比较

- `Path(...).resolve()` 规范化后比较；Windows 上（`os.name == 'nt'`）再 `casefold()`
- 替代原 `str(project_path)` 精确比较
- 三个文件（confirm_ui / svg_editor / visual_review）统一采用同一比较逻辑
- **visual_review.py 细节**：`check_server(server_url, project_path)` 中 `expected_project = str(project_path)`（245 行）——`project_path` 由调用方传入（lock 记录或命令行参数），可能未经 resolve。修复时在 `check_server` 内部先 `project_path = project_path.resolve()` 再比较（或直接 `expected_project = str(Path(project_path).resolve())`），与服务端返回的 resolve 后路径对齐

### 3.3 pid 降级为诊断

- health 返回的 `pid` 与 `proc.pid` 失配时仅 `logger.warning` 诊断日志，不阻断就绪判定

### 3.4 失败诊断

- 就绪失败时，日志打印实际收到的 health 字段（service/token/project/pid）与期望值，便于定位端口冲突 / 旧服务残留

### 3.5 兼容性

- health 响应仅新增字段，不影响前端轮询等其他消费者
- 前台模式（无 token 环境变量）health 的 `launch_token` 为 None；仅 daemon 启动路径生成并校验 token

## 4. P1-1：CLI 命令名与文档

### 4.1 `--help` 透传（两个 cli.py 同步改）

当前 `cli.py`：`any(a in ("-h", "--help") for a in argv[1:])` 会拦截任何层级的 `--help`，导致 `project init --help` 只回显顶层命令列表。

改为：仅当 `len(argv) < 2 or argv[1] in ("-h", "--help")` 时打印顶层帮助；否则 `--help` 透传给子脚本，由 argparse 显示子命令参数。

### 4.2 命令别名（独立 ALIASES 字典，不加入 COMMANDS）

```python
ALIASES = {
    "notes-split": "total-md-split",
    "svg-editor-server": "svg-editor",
}
# main 中：
cmd = ALIASES.get(argv[1], argv[1])
if cmd not in COMMANDS: ...
```

**关键约束**：别名不得加入 `COMMANDS` 字典。原因：`auto_fix_uvx.py` 从 COMMANDS 反查 `script_to_cmd`（dict 遍历后键覆盖前值），别名会污染 `total_md_split.py` 的规范化替换目标。

独立 ALIASES 的三个好处：
1. `check_cli_sync.py` 只解析 COMMANDS，不受影响
2. `auto_fix_uvx.py` 反向映射不受污染
3. 帮助列表不显示别名

两个 cli.py（根 + skills/ppt-master/）的 ALIASES 必须同步（Gate 1 检查命令名集合相等；ALIASES 虽不在检查范围，但保持一致）。

### 4.3 文档命令形式修复（根因修复）

**根因**：`auto_fix_uvx.py` 的正则只匹配字面量 `skills/ppt-master/scripts/` 和 `scripts/`，**不匹配** `python3 ${SKILL_DIR}/scripts/` 形式，导致残留 32 处未被 CI（Gate 2/3）发现：

| 文件 | 残留数 |
|------|--------|
| `workflows/generate-pptx.md` | 22 |
| `workflows/profiles/quick-generate.md` | 3 |
| `references/artifact-ownership.md` | 7 |

**修复**：扩展 `auto_fix_uvx.py`（fork 独有文件，无上游冲突）新增一条正则：

```
python3\s+\$\{SKILL_DIR\}/scripts/(\S*/)?<script> → uvx ppt-master <cmd>
```

然后运行一次自动修复全部残留。附带收益：
- CI Auto-fix 步骤（auto-tag Step 1）未来自动兜底 `${SKILL_DIR}` 形式
- 同步工作流 Step 4a 扫描命令同步加该模式（见第 6 节）

**注意事项**：
- `auto_fix_uvx.py` 从 cwd 读 `cli.py`，本地运行必须位于仓库根目录（CI 天然满足）
- 非 scripts 的 `${SKILL_DIR}/templates/`、`${SKILL_DIR}/references/` 引用保持原样（正则仅匹配 `scripts/` 前缀）

## 5. P1-2：uvx 环境依赖标注

4.3 修复后文档命令全部变为 `uvx ppt-master <cmd>`，天然不依赖系统 python。在 `generate-pptx.md` 开头补一句：「脚本须经 `uvx ppt-master` 执行；直接 `python` 调用需先安装 requirements.txt」。

## 6. P1-3：路径统一

### 6.1 统一解析函数（`project_management/paths.py`）

```python
def projects_root() -> Path:
    """Project workspace root: env PPT_MASTER_PROJECTS > <cwd>/projects."""
    env = os.environ.get("PPT_MASTER_PROJECTS")
    if env:
        return Path(env).expanduser().resolve()
    return (Path.cwd() / "projects").resolve()
```

两个分支都 `.resolve()`，保证返回绝对规范化路径（Windows 下统一为系统实际大小写）。`REPO_ROOT` 保留（`project_management/cli.py:45` 依赖它作子进程 cwd）。

### 6.2 使用点接入（清单已核实）

| 文件 | 现状 | 改法 |
|------|------|------|
| `paths.py:23` | `PROJECTS_ROOT` 常量 | 替换为 `projects_root()` 函数 |
| `project_manager.py:56,798,807,971` | 自身定义常量 + 3 处比较/提示 | 删常量，import `projects_root`；`ProjectManager.__init__` 默认 `base_dir = projects_root()` |
| `project_management/cli.py:44,829,838,1002` | import 常量 + 3 处 | import 改为 `from .paths import REPO_ROOT, projects_root, ...`（保持该文件既有的相对导入风格） |
| `config.py:44` | `PROJECTS_DIR = REPO_ROOT/"projects"` | 改为 `projects_root()`（无 .py 使用者，一致性同步） |

已验证：`project_management/__init__.py` 存在；无 import 循环；三个接入文件均有 scripts/ 在 sys.path 的既有机制。

### 6.3 文档语义锚定

`topic-research.md:88` 的 `projects/` 相对路径补一句：「`projects/` 指项目工作区根（`PPT_MASTER_PROJECTS` 或默认 `<cwd>/projects/`）」，消除研究产物落到 `.agents/projects` 的歧义。

### 6.4 已知遗留风险（不改动，仅记录）

`project_manager.py:354` 与 `project_management/cli.py:385` 用 `REPO_ROOT`（uvx 下指向安装目录）作为转换工具子进程 cwd。测试未暴露问题（工具输出均为绝对路径），超出本次范围，备查。

## 7. 同步工作流调整（sync-upstream）

**必要性**：本次修复修改 5 个上游文件，突破「scripts 零改动」隔离原则：

| 文件 | 修改原因 | 上游冲突风险 |
|------|---------|-------------|
| `confirm_ui/server.py` | P0-1 token 校验 | 中 |
| `svg_editor/server.py` | P0-1 token 校验 | 中 |
| `visual_review.py` | P0-1 project 规范化（同族代码） | 低 |
| `config.py` | P1-3 路径解析 | 低 |
| `project_management/paths.py` | P1-3 PROJECTS_ROOT | 低 |
| `project_manager.py` | P1-3 base_dir | 低 |

### 7.1 sync-upstream.md 调整

- Step 3 新增「**fork 修改文件清单**」小节：列出上述 6 文件，策略改为「保留 fork 的 Windows/uvx 适配（token 校验、`PPT_MASTER_PROJECTS`、规范化路径比较），合入上游功能改动」，注明每个文件的关键适配点
- Step 4a 扫描命令补全 `${SKILL_DIR}` 模式（当前 `rg -g '*.md' 'python3 (scripts/|skills/)' .` 不匹配该形式）：

  ```bash
  rg -g '*.md' -e 'python3 (scripts/|skills/)' -e 'python3 \$\{SKILL_DIR\}/scripts/' .
  ```

- Step 4e 门禁追加「fork 适配完整性检查」：grep 验证 `PPT_MASTER_LAUNCH_TOKEN`、`PPT_MASTER_PROJECTS` 等适配标记仍存在于对应文件

### 7.2 sync-upstream.yml 调整

- schedule 与 manual 两个 prompt 追加「fork 适配完整性门禁」：合并后 grep 验证适配标记仍在；缺失则回退修复再提交（与现有 guard 门禁并列）
- 两个 prompt 中的 python3 扫描命令同步追加 `${SKILL_DIR}` 模式（同 7.1）
- 确认 `ALIASES` 字典（cli.py，fork 独有文件）仍在

### 7.3 发布链核查结论

| 工作流 | 结论 |
|--------|------|
| auto-tag.yml Gate 0（版本一致） | bump 0.1.72 两处同步即可 |
| auto-tag.yml Gate 1（check_cli_sync） | 别名在独立 ALIASES，不影响；双 cli.py 同步 |
| auto-tag.yml Gate 2/3（python3/uv run 残留） | **Gate 2 追加 `${SKILL_DIR}` 模式**，与 4.3 修复及 7.1 Step 4a 对称（否则 auto-fix 漏网的 `${SKILL_DIR}` 形式无法被发布门禁捕获）。精确命令（bash 单引号下 `$`/`{` 为字面量，`-E` 下仍需 `\$`/`\{` 转义防歧义）：`grep -rn -E --include='*.md' 'python3 (skills/ppt-master/scripts/|\$\{SKILL_DIR\}/scripts/)' skills/ppt-master/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | grep -v 'superpowers' | ...`（既有 `grep -v` 排除项不变，`docs/superpowers/` 下含 `${SKILL_DIR}` 的设计文档仍被 `superpowers` 排除）；文档措辞避免 python3 模式 |
| auto-tag.yml Gate 4（依赖） | token 用标准库，无新依赖 |
| auto-tag.yml Gate 5/6（guard + MANIFEST.in） | 不碰 attribution 文件 |
| publish-pypi.yml | scripts/ 已在 MANIFEST.in include，自动进 wheel |
| check-uvx-migration.yml | push main 触发；脚本对非 merge commit 返回 exit 2 跳过，本次普通功能提交不阻断 |

## 8. 验证计划

### 8.1 本地（Windows）

> 注意：本机 uvx 安装为 0.1.71（PyPI 已发布），验证本地改动须用 `uvx --from . ppt-master <cmd>`（从仓库构建运行），发布后再用 `uvx ppt-master` 验收 wheel。

1. P0-1 核心验收：`uvx --from . ppt-master confirm-ui <proj> --daemon` → 5050 启动成功；`svg-editor --live --daemon` 同验；前台 + 显式端口回归
2. P1-3：`project init` 默认 → `<cwd>/projects/`；设置 `PPT_MASTER_PROJECTS` → 自定义目录；init 输出打印实际项目根
3. P1-1：`project init --help` 显示 init 参数；`notes-split` / `svg-editor-server` 别名可用
4. 文档修复：`auto_fix_uvx.py` 运行 → 32 处修复；`rg 'python3.*SKILL_DIR.*scripts' --glob '!docs/superpowers/**'` 零残留
5. 回归：`check_cli_sync.py` exit 0；`attribution_guard` exit 0

### 8.2 发布链

bump 0.1.72（两处 pyproject）→ push → check-uvx-migration → auto-tag Gate 0-6 → publish-pypi → `uvx ppt-master attribution-guard` 验证 wheel。

## 9. 涉及文件汇总

### 代码（fork 独有，无上游冲突）

- `cli.py`（根）+ `skills/ppt-master/cli.py`：`--help` 透传、ALIASES
- `scripts/auto_fix_uvx.py`：新增 `${SKILL_DIR}` 正则

### 代码（上游文件，进 fork 修改清单）

- `scripts/confirm_ui/server.py`：token 校验
- `scripts/svg_editor/server.py`：token 校验
- `scripts/visual_review.py`：project 规范化（同族代码）
- `scripts/config.py`：PROJECTS_DIR → projects_root()
- `scripts/project_management/paths.py`：projects_root() 函数
- `scripts/project_manager.py`：base_dir + 使用点

### 文档

- `workflows/generate-pptx.md`、`workflows/profiles/quick-generate.md`、`references/artifact-ownership.md`：命令形式自动修复（auto_fix_uvx.py）
- `workflows/generate-pptx.md`：uvx 环境依赖标注
- `workflows/stages/topic-research.md`：projects/ 语义锚定

### 工作流/命令

- `.opencode/command/sync-upstream.md`：fork 修改文件清单 + 扫描/门禁扩展
- `.github/workflows/sync-upstream.yml`：prompt 追加门禁
- `.github/workflows/auto-tag.yml`：Gate 2 grep 追加 `${SKILL_DIR}` 模式

### 版本

- `pyproject.toml` + `skills/ppt-master/pyproject.toml`：0.1.71 → 0.1.72
