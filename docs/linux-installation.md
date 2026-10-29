# Linux & WSL2 Installation Guide

[English](./linux-installation.md)

---

This guide walks you through installing PPT Master on Linux distributions (Ubuntu, Debian, Fedora, Arch Linux) and Windows Subsystem for Linux (WSL2). Follow along to set up your environment in under 10 minutes.

---

## Step 1 — Install Python 3.10–3.14

Python 3.10 to 3.14 is the only core requirement. Ensure both Python and `venv` are installed.

### Ubuntu / Debian / WSL2 (Ubuntu)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### Fedora / RHEL
```bash
sudo dnf install -y python3 python3-pip
```

### Arch Linux
```bash
sudo pacman -S python python-pip
```

Verify your installation:
```bash
python3 --version
```
You should see `Python 3.10.x` or higher (up to 3.14).

---

## Step 2 — Download the Project

### Option A — Git Clone (Recommended)
```bash
# GitHub
git clone https://github.com/hugohe3/ppt-master.git

# AtomGit mirror (Mainland China)
git clone https://atomgit.com/hugohe3/ppt-master.git
```

Enter the project folder:
```bash
cd ppt-master
```

---

## Step 3 — Set Up a Virtual Environment

Using a virtual environment is strongly recommended to isolate dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

To automatically activate the virtual environment in future shell sessions, you can add `source /path/to/ppt-master/.venv/bin/activate` to your `~/.bashrc` or `~/.zshrc`.

---

## Step 4 — Install Dependencies

Install all core dependencies via `pip`:

```bash
pip install -r requirements.txt
```

> **Note**: PPT Master uses only standard PyPI packages. No non-standard C compilation is required for the default pipeline.

---

## Step 5 — CRITICAL: Install Microsoft Core & CJK Fonts

PPT Master's text measurement engine (`text_measure.py`) calculates text bounding boxes and line wraps based on standard Microsoft PowerPoint font metrics (Calibri, Arial, Segoe UI, and CJK equivalents).

Without these fonts installed, Linux falls back to generic fonts (such as DejaVu Sans), which have different character widths and may cause text clipping or badge misalignment in exported slides.

### Ubuntu / Debian / WSL2
```bash
# Accept Microsoft TrueType core fonts (Arial, Times New Roman, etc.)
sudo apt install -y ttf-mscorefonts-installer

# Install Google Noto CJK fonts for Chinese, Japanese, and Korean rendering
sudo apt install -y fonts-noto-cjk fonts-noto-core

# Refresh font cache
fc-cache -fv
```

> **💡 Ubuntu EULA Tip**: When `ttf-mscorefonts-installer` displays the license agreement in the terminal, press `Tab` to highlight `<Ok>`, then press `Enter`. Highlight `<Yes>` on the next screen and press `Enter`.

### Fedora
```bash
sudo dnf install -y curl cabextract xorg-x11-font-utils fontconfig
sudo dnf install -y google-noto-sans-cjk-fonts google-noto-serif-cjk-fonts
fc-cache -fv
```

### Arch Linux
```bash
sudo pacman -S noto-fonts noto-fonts-cjk
# Microsoft fonts via AUR (optional but recommended):
# yay -S ttf-ms-win11-auto
fc-cache -fv
```

---

## Step 6 — Install LibreOffice (Optional)

If you plan to use headless export features (such as rendering `.pptx` slides to preview images or PDF on Linux), install LibreOffice:

```bash
# Ubuntu / Debian
sudo apt install -y libreoffice

# Fedora
sudo dnf install -y libreoffice

# Arch Linux
sudo pacman -S libreoffice-fresh
```

---

## Step 7 — Verify Installation

Run the built-in unit tests to confirm that your environment, font metrics, and SVG generators are working correctly:

```bash
cd skills/ppt-master/scripts
python -m unittest tests.test_text_measure
python -m unittest tests.test_svg_quality_checker
```

If all tests pass with `OK`, your installation is complete and ready to generate presentations!

---

## Troubleshooting

### `python3-venv` is missing on Debian/Ubuntu
If `python3 -m venv .venv` fails with `The virtual environment was not created successfully because ensurepip is not available`:
```bash
sudo apt install -y python3-venv
```

### Chinese / Japanese / Korean text renders as empty boxes (Tofu)
This means CJK fonts are not detected. Install the Noto CJK package:
```bash
sudo apt install -y fonts-noto-cjk
fc-cache -fv
```

### WSL2 Users: Sharing Windows Fonts
If you are running inside WSL2 on Windows 10/11, you can mount Windows host fonts directly into WSL:
1. Create or edit `/etc/fonts/local.conf`:
   ```xml
   <?xml version="1.0"?>
   <!DOCTYPE fontconfig SYSTEM "fonts.dtd">
   <fontconfig>
     <dir>/mnt/c/Windows/Fonts</dir>
   </fontconfig>
   ```
2. Rebuild the font cache:
   ```bash
   fc-cache -fv
   ```
This instantly gives WSL2 access to native Calibri, Aptos, Segoe UI, and Microsoft YaHei without downloading separate packages.
