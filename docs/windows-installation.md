# Windows Installation Guide

This guide walks you through installing PPT Master on Windows step by step. Follow along and you'll have a working setup in under 10 minutes.

---

## Step 1 — Install Python (Required)

Python is the only hard requirement.

1. Go to **[python.org/downloads](https://www.python.org/downloads/)** and download the latest **Python 3.10+** installer.

2. **⚠️ CRITICAL: Check "Add python.exe to PATH"** during installation — this is the single most common mistake on Windows. Skipping this will break every step that follows.

   ![Python installer — check Add to PATH](assets/windows-python-path.png)

3. After installation, open **PowerShell** (search "PowerShell" in Start menu) and verify:

   ```powershell
   python --version
   ```

   You should see `Python 3.12.x` or similar. If you see "Python was not found" or it opens the Microsoft Store, see [Troubleshooting](#python-was-not-found-or-opens-microsoft-store) below.

> **💡 Tip**: Python installed via Anaconda or Miniconda works too — just make sure `python --version` shows 3.10+.

---

## Step 2 — Download the Project

**Option A — Download ZIP** (easiest):

1. Go to [github.com/hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)
2. Click the green **Code** button → **Download ZIP**
3. Unzip to `C:\Users\YourName\ppt-master`

**Option B — Git Clone** (requires [Git](https://git-scm.com/downloads)):

```powershell
git clone https://github.com/hugohe3/ppt-master.git
cd ppt-master
```

---

## Step 3 — Install uv and Dependencies

**3.1 — Install uv (Python package manager)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> This installs `uv` globally. After installation, **restart PowerShell** and verify: `uv --version`

**3.2 — Install project dependencies**

```powershell
cd C:\Users\YourName\ppt-master   # ← adjust to your actual path
uv sync
```

> `uv sync` creates an isolated virtual environment (`.venv/`) and installs all dependencies into it — no global pollution, no `pip` required.

Wait for it to finish. You should see `Resolved 18 packages` or similar at the end.

---

## Step 4 — Verify Your Setup

```powershell
uv run python -c "import pptx; import fitz; print('All core dependencies OK')"
```

✅ Output: `All core dependencies OK` → you're good.

❌ Error → see [Troubleshooting](#troubleshooting) below.

---

## Step 5 — Run a Minimal Example

Open your AI editor (Cursor, VS Code + Copilot, etc.), open the `ppt-master` folder, and type in the chat:

```
Please create a simple 3-page test PPT with a cover, one content page, and a closing page. Topic: "Hello World".
```

If a `.pptx` file appears in `exports/` that opens in PowerPoint — **you're done.**

---

## Step 6 — Optional Enhancements (most users can skip this)

With Python and `requirements.txt` installed, you already have everything needed to generate presentations. The items below are **edge-case fallbacks and enhancements** — install only if you hit the specific scenario.

| Enhancement | Install only if… | How to install | Verify |
|-------------|-----------------|----------------|--------|
| **CairoSVG** — higher quality PNG fallbacks | You want crisper PNG fallbacks for Office versions that don't render SVG natively. `svglib` (already installed) is fine for most cases. | Install [GTK3 Runtime](https://github.com/nickvdp/gtk3/releases), then `uv add cairosvg` | `uv run python -c "import cairosvg"` |
| **Pandoc** — legacy document formats | You need to convert `.doc`, `.odt`, `.rtf`, `.tex`, `.rst`, `.org`, or `.typ`. `.docx`/`.html`/`.epub`/`.ipynb` work natively in Python. | Download `.msi` from [pandoc.org](https://pandoc.org/installing.html) | `pandoc --version` |

---

## Troubleshooting

### `python` was not found or opens Microsoft Store

**Cause**: Python isn't in your system PATH.

**Fix 1** — Re-run the Python installer → **Modify** → check **"Add Python to environment variables"**.

**Fix 2** — Manually add to PATH:
1. Run `where python` in PowerShell first to find the actual path (e.g. `C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe`)
2. Search "Environment Variables" in Start menu
3. Find `Path` → **Edit** → add the **directory** from step 1 and its `Scripts` subfolder:
   ```
   C:\Users\YourName\AppData\Local\Programs\Python\Python312
   C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts
   ```
4. Click OK, then **restart PowerShell**

**Fix 3** — Try `python3` or `py` instead.

### `uv sync` fails with permission errors

```powershell
$env:UV_PYTHON = (Get-Command python).Source
uv sync
```

Or run PowerShell as Administrator.

### `uv sync` fails due to network issues

```powershell
$env:UV_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
uv sync
# Or via proxy:
$env:HTTPS_PROXY = "http://your-proxy:port"
uv sync
```

### `ModuleNotFoundError`

You ran `python` directly instead of `uv run python`. Use `uv run python` to ensure the virtual environment is active.

### `import fitz` fails

1. Upgrade uv: `uv self update`
2. Pre-built wheel: `uv pip install PyMuPDF --only-binary :all:`
3. Still failing → install [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### PowerShell says "running scripts is disabled"

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Still stuck?

- 📖 [FAQ](./faq.md)
- 🐛 [GitHub Issues](https://github.com/hugohe3/ppt-master/issues) — include your Python version, Windows version, and full error message
- 💬 [GitHub Discussions](https://github.com/hugohe3/ppt-master/discussions)
