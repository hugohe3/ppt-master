# Windows 安装指南

本指南将手把手教你在 Windows 上安装 PPT Master。按顺序操作，10 分钟内即可跑通第一份 PPT。

---

## Step 1 — 安装 Python（必须）

Python 是唯一的硬性要求。

1. 前往 **[python.org/downloads](https://www.python.org/downloads/)**，下载最新的 **Python 3.10+** 安装包。

2. **⚠️ 关键步骤：安装时务必勾选 "Add python.exe to PATH"** — 这是 Windows 上最常见的安装失误，不勾的话后面每一步都会出问题。

   ![Python 安装器 — 勾选 Add to PATH](../assets/windows-python-path.png)

3. 安装完成后，打开 **PowerShell**（在开始菜单搜索「PowerShell」）并验证：

   ```powershell
   python --version
   ```

   应该看到 `Python 3.12.x` 之类的输出。如果提示「未找到」或弹出 Microsoft Store，见下方[常见问题](#python-未找到或弹出-microsoft-store)。

> **💡 提示**：Anaconda / Miniconda 安装的 Python 也可以用，只要 `python --version` 显示 3.10+ 即可。

---

## Step 2 — 下载项目

**方式 A — 下载 ZIP**（最简单）：

1. 打开 [GitHub](https://github.com/hugohe3/ppt-master)（或 [AtomGit 镜像](https://atomgit.com/hugohe3/ppt-master)，国内更快）
2. 点击绿色 **Code** 按钮 → **Download ZIP**
3. 解压到 `C:\Users\你的用户名\ppt-master`

**方式 B — Git Clone**（需要 [Git](https://git-scm.com/downloads)）：

```powershell
# GitHub
git clone https://github.com/hugohe3/ppt-master.git
# AtomGit（国内更快）
git clone https://atomgit.com/hugohe3/ppt-master.git
cd ppt-master
```

---

## Step 3 — 安装 uv 和依赖

**3.1 — 安装 uv（Python 包管理器）**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> 这会在系统层面安装 `uv`。安装完成后**重启 PowerShell**，验证：`uv --version`

**3.2 — 安装项目依赖**

```powershell
cd C:\Users\你的用户名\ppt-master   # ← 替换为你的实际路径
uv sync
```

> `uv sync` 会创建隔离的虚拟环境（`.venv/`）并将所有依赖安装到其中 — 不污染全局环境，无需 `pip`。

等待安装完成，最后看到 `Resolved 18 packages` 之类的输出就行。

---

## Step 4 — 验证安装

```powershell
uv run python -c "import pptx; import fitz; print('All core dependencies OK')"
```

✅ 输出 `All core dependencies OK` → 核心环境没问题。

❌ 报错 → 见下方[常见问题](#常见问题)。

---

## Step 5 — 跑一个最小示例

打开你的 AI 编辑器（Cursor、VS Code + Copilot 等），打开 `ppt-master` 目录，在聊天面板输入：

```
请创建一个 3 页测试 PPT，封面 + 内容页 + 封底，主题"Hello World"
```

`exports/` 下出现 `.pptx` 且能在 PowerPoint 中打开 → **搞定了。**

---

## Step 6 — 可选增强（大多数用户可以跳过）

装好 Python 和 `requirements.txt` 后，生成 PPT 的全部功能已经就绪。下面是**边缘场景的备用方案和增强项**——只有遇到对应的具体场景才需要装。

| 增强项 | 只在以下情况才装 | 安装方式 | 验证 |
|--------|-----------------|---------|------|
| **CairoSVG** — 更高质量 PNG 后备图 | 你希望在不原生支持 SVG 的 Office 版本下获得更清晰的 PNG 后备图。`svglib`（已默认安装）足够大多数场景。 | 安装 [GTK3 Runtime](https://github.com/nickvdp/gtk3/releases) 后 `uv add cairosvg` | `uv run python -c "import cairosvg"` |
| **Pandoc** — 旧格式文档 | 你需要转 `.doc`、`.odt`、`.rtf`、`.tex`、`.rst`、`.org`、`.typ`。`.docx`/`.html`/`.epub`/`.ipynb` 已由 Python 原生处理。 | [pandoc.org](https://pandoc.org/installing.html) 下载 `.msi` 安装 | `pandoc --version` |

---

## 常见问题

### `python` 未找到或弹出 Microsoft Store

**原因：** Python 没有加入系统 PATH。

**方法 1** — 重新运行 Python 安装程序，选择 **Modify**，确保勾选 **"Add Python to environment variables"**。

**方法 2** — 手动添加 PATH：
1. 先在 PowerShell 中运行 `where python`，记下输出的路径（如 `C:\Users\你的用户名\AppData\Local\Programs\Python\Python312\python.exe`）
2. 开始菜单搜索「环境变量」
3. 找到 `Path` → **编辑** → 新增上面路径的**目录部分**及其 `Scripts` 子目录：
   ```
   C:\Users\你的用户名\AppData\Local\Programs\Python\Python312
   C:\Users\你的用户名\AppData\Local\Programs\Python\Python312\Scripts
   ```
4. 确定，**重启 PowerShell**

**方法 3** — 试试 `python3` 或 `py` 命令。

### `uv sync` 报权限错误

```powershell
$env:UV_PYTHON = (Get-Command python).Source
uv sync
```

或以管理员身份运行 PowerShell。

### `uv sync` 网络问题

```powershell
# 清华镜像（国内推荐）
$env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
uv sync
# 代理
$env:HTTPS_PROXY = "http://your-proxy:port"
uv sync
```

### `ModuleNotFoundError`

直接用了 `python` 而非 `uv run python`。用 `uv run python` 确保在虚拟环境中运行。

### `import fitz` 失败

1. 升级 uv：`uv self update`
2. 预编译包：`uv pip install PyMuPDF --only-binary :all:`
3. 仍失败 → 安装 [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### PowerShell「脚本运行被禁用」

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 还是搞不定？

- 📖 [常见问题 (FAQ)](./faq.md)
- 🐛 [GitHub Issues](https://github.com/hugohe3/ppt-master/issues) — 附上 Python 版本、Windows 版本和完整报错
- 💬 [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
