#!/usr/bin/env bash
# Build a MindMux-compatible ppt-master engine pack for the current platform.
#
# Output:
#   dist-engine/ppt-master-engine-<platform>-<arch>/
#     bin/ppt-master-engine/ppt-master-engine[.exe]
#     skills/ppt-master/   (slim skill content)
#     manifest.json
#
# Usage:
#   engine/build.sh
#   PYTHON=python3.11 engine/build.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3.11}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python3
fi

PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$PLATFORM" in
  darwin) PLATFORM=darwin ;;
  linux) PLATFORM=linux ;;
  mingw*|msys*|cygwin*) PLATFORM=win32 ;;
esac

ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64|amd64) ARCH=x64 ;;
  arm64|aarch64) ARCH=arm64 ;;
  *) ARCH="$ARCH_RAW" ;;
esac

FOLDER="ppt-master-engine-${PLATFORM}-${ARCH}"
STAGE="$ROOT/dist-engine/${FOLDER}"
BUILD_DIR="$ROOT/dist-engine/.build-${FOLDER}"

echo "==> Python: $($PYTHON --version 2>&1)"
echo "==> Target pack: $STAGE"

rm -rf "$STAGE" "$BUILD_DIR"
mkdir -p "$STAGE/bin" "$STAGE/skills" "$BUILD_DIR"

# ── venv + deps ─────────────────────────────────────────────
# Do NOT `source activate` — on Windows Git Bash the path is Scripts/, not bin/,
# and sourcing is fragile in CI. Call venv interpreters by absolute path instead.
VENV="$BUILD_DIR/venv"
"$PYTHON" -m venv "$VENV"
if [[ -x "$VENV/bin/python" ]]; then
  VENV_PY="$VENV/bin/python"
  VENV_BIN="$VENV/bin"
elif [[ -x "$VENV/Scripts/python.exe" ]]; then
  VENV_PY="$VENV/Scripts/python.exe"
  VENV_BIN="$VENV/Scripts"
elif [[ -x "$VENV/Scripts/python" ]]; then
  VENV_PY="$VENV/Scripts/python"
  VENV_BIN="$VENV/Scripts"
else
  echo "error: venv python not found under $VENV (bin/ or Scripts/)" >&2
  ls -la "$VENV" "$VENV/bin" "$VENV/Scripts" 2>/dev/null || true
  exit 1
fi
export PATH="$VENV_BIN:$PATH"
echo "==> venv python: $VENV_PY"
"$VENV_PY" -m pip install -U pip wheel setuptools
"$VENV_PY" -m pip install -r "$ROOT/engine/requirements-engine.txt"

# ── PyInstaller onedir launcher ─────────────────────────────
echo "==> PyInstaller launcher"
"$VENV_PY" -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --name ppt-master-engine \
  --distpath "$STAGE/bin" \
  --workpath "$BUILD_DIR/pyi-work" \
  --specpath "$BUILD_DIR" \
  --paths "$ROOT/skills/ppt-master/scripts" \
  --collect-submodules pptx \
  --collect-submodules lxml \
  --collect-submodules PIL \
  --hidden-import pptx \
  --hidden-import lxml \
  --hidden-import lxml.etree \
  --hidden-import PIL \
  --hidden-import PIL.Image \
  --hidden-import xlsxwriter \
  --hidden-import filecmp \
  --hidden-import xml.etree.ElementTree \
  "$ROOT/engine/launcher.py"

# ── slim skill content ──────────────────────────────────────
# copy_tree SRC/ DST/ [extra find -prune names ...]
# Prefer rsync; fall back to cp (Windows runners have no rsync by default).
copy_tree() {
  local src="$1"
  local dst="$2"
  shift 2
  mkdir -p "$dst"
  if command -v rsync >/dev/null 2>&1; then
    local args=(-a --delete --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store')
    local excl
    for excl in "$@"; do
      args+=(--exclude "$excl")
    done
    rsync "${args[@]}" "$src" "$dst"
    return
  fi
  # cp fallback: wipe dest contents then copy, skipping common junk + optional names
  find "$dst" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
  # Use tar pipeline when available (Git Bash / Unix) for exclude support
  if command -v tar >/dev/null 2>&1; then
    local tar_ex=(--exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store')
    local excl
    for excl in "$@"; do
      tar_ex+=(--exclude="$excl")
    done
    # src is expected to end with /
    (cd "${src%/}" && tar cf - "${tar_ex[@]}" .) | (cd "$dst" && tar xf -)
    return
  fi
  cp -R "${src%/}/." "$dst/"
}

echo "==> Copy slim skill content"
SKILL_SRC="$ROOT/skills/ppt-master"
SKILL_DST="$STAGE/skills/ppt-master"
mkdir -p "$SKILL_DST"

# Core files
cp "$SKILL_SRC/SKILL.md" "$SKILL_DST/"
cp "$SKILL_SRC/requirements.txt" "$SKILL_DST/" 2>/dev/null || true

# Scripts (full — needed for dispatch)
copy_tree "$SKILL_SRC/scripts/" "$SKILL_DST/scripts/"

# Templates (icons + charts + layouts)
if [[ -d "$SKILL_SRC/templates" ]]; then
  copy_tree "$SKILL_SRC/templates/" "$SKILL_DST/templates/"
fi

# References without AI image comparison gallery (~43MB of PNGs)
if [[ -d "$SKILL_SRC/references" ]]; then
  copy_tree "$SKILL_SRC/references/" "$SKILL_DST/references/" "ai-image-comparison"
fi

if [[ -d "$SKILL_SRC/workflows" ]]; then
  copy_tree "$SKILL_SRC/workflows/" "$SKILL_DST/workflows/"
fi

# ── manifest ────────────────────────────────────────────────
GIT_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILT_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
VERSION="${ENGINE_VERSION:-0.1.0}+${GIT_SHA}"

cat >"$STAGE/manifest.json" <<EOF
{
  "name": "ppt-master-engine",
  "version": "${VERSION}",
  "platform": "${PLATFORM}",
  "arch": "${ARCH}",
  "builtAt": "${BUILT_AT}",
  "gitSha": "${GIT_SHA}",
  "skillDir": "skills/ppt-master",
  "bin": "bin/ppt-master-engine/ppt-master-engine"
}
EOF

# ── smoke ───────────────────────────────────────────────────
BIN="$STAGE/bin/ppt-master-engine/ppt-master-engine"
if [[ -f "${BIN}.exe" ]]; then
  BIN="${BIN}.exe"
fi
chmod +x "$BIN" 2>/dev/null || true
echo "==> Smoke: $BIN --version"
"$BIN" --version

# ── zip (portable: ditto / zip / 7z / python) ───────────────
# Windows runners often lack `zip`; GitHub Actions has 7z. Prefer tools
# that handle macOS dylibs correctly when available.
ZIP_OUT="$ROOT/dist-engine/${FOLDER}.zip"
rm -f "$ZIP_OUT"
echo "==> Zip: $ZIP_OUT"
(
  cd "$ROOT/dist-engine"
  if command -v ditto >/dev/null 2>&1; then
    ditto -c -k --keepParent "$FOLDER" "${FOLDER}.zip"
  elif command -v zip >/dev/null 2>&1; then
    zip -ry "${FOLDER}.zip" "$FOLDER"
  elif command -v 7z >/dev/null 2>&1; then
    7z a -tzip "${FOLDER}.zip" "$FOLDER"
  elif command -v 7za >/dev/null 2>&1; then
    7za a -tzip "${FOLDER}.zip" "$FOLDER"
  else
    # Last resort: stdlib zipfile (no external tools)
    "$VENV_PY" - <<PY
import pathlib, zipfile
root = pathlib.Path("$FOLDER")
out = pathlib.Path("${FOLDER}.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in root.rglob("*"):
        if p.is_file():
            zf.write(p, p.as_posix())
print("wrote", out, "bytes", out.stat().st_size)
PY
  fi
)
ls -lh "$ZIP_OUT"

echo "==> Pack ready: $STAGE"
du -sh "$STAGE" "$STAGE/bin" "$STAGE/skills" || true
