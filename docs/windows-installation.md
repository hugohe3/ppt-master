# Windows Installation Guide

[English](./windows-installation.md) | [Chinese](./zh/windows-installation.md)

---

This guide walks you through installing PPT Master on Windows step by step. Follow along and you'll have a working setup in under 10 minutes.

---

## Step 1 — Install Python (Required)

Python is the only hard requirement.

1. Go to **[python.org/downloads](https://www.python.org/downloads/)** and download the latest **Python 3.10+** installer.

2. **⚠️ CRITICAL: Check "Add python.exe to PATH"** during installation — this is the single most common mistake on Windows. Skipping this will break every step that follows.

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

## Step 3 — Install Dependencies

```powershell
cd C:\Users\YourName\ppt-master   # ← adjust to your actual path
pip install -r requirements.txt
```

> If `pip` is not recognized, try `python -m pip install -r requirements.txt`.

Wait for it to finish. You should see `Successfully installed ...` at the end.

---

## Step 4 — Verify Your Setup

```powershell
python -c "import pptx; import fitz; print('All core dependencies OK')"
```

✅ Output: `All core dependencies OK` → you're good.

❌ Error → see [Troubleshooting](#troubleshooting) below.

---

## Step 5 — Run a Minimal Example

Open the `ppt-master` folder in an agent-capable AI tool (Claude Code, Codex, Cursor, a VS Code agent, etc.) and type in the chat:

```
Please create a simple 3-page test PPT with a cover, one content page, and a closing page. Topic: "Hello World".
```

After the standard flow finishes, you should see:

- A native DrawingML `.pptx` under `exports/`, generated from `svg_output/`, that opens in PowerPoint and remains editable element by element.
- A `svg_final/` directory containing self-contained visual-preview SVGs. They may be inserted manually as SVG pictures, but manual "Convert to Shape" is outside the supported contract.

If both are present, **you're done.**

---

## Step 6 — Optional Enhancements (most users can skip this)

With Python and `requirements.txt` installed, you already have everything needed to generate presentations. PPTX export writes native DrawingML shapes, so it does not require CairoSVG, GTK, or a separate SVG rasterization stack. The item below is an **edge-case fallback** — install it only if you hit the specific scenario.

| Enhancement | Install only if… | How to install | Verify |
|-------------|-----------------|----------------|--------|
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

### A `python3` command fails (exit 49 / opens Microsoft Store)

The python.org installer ships `python.exe` but not `python3.exe`. **Just replace `python3` with `python` in the command** (the AI agent usually switches to `python` and continues on its own too).

### `pip install` fails with permission errors

```powershell
pip install --user -r requirements.txt
```

Or run PowerShell as Administrator.

### `pip install` fails due to network issues

```powershell
pip install -r requirements.txt --proxy http://your-proxy:port
```

### `ModuleNotFoundError`

`pip` installed to a different Python. Use `python -m pip install -r requirements.txt` to match.

### `import fitz` fails

1. Upgrade pip: `python -m pip install --upgrade pip`
2. Pre-built wheel: `pip install PyMuPDF --only-binary :all:`
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
