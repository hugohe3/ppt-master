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
VENV="$BUILD_DIR/venv"
"$PYTHON" -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -U pip wheel setuptools
python -m pip install -r "$ROOT/engine/requirements-engine.txt"

# ── PyInstaller onedir launcher ─────────────────────────────
echo "==> PyInstaller launcher"
pyinstaller \
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
echo "==> Copy slim skill content"
SKILL_SRC="$ROOT/skills/ppt-master"
SKILL_DST="$STAGE/skills/ppt-master"
mkdir -p "$SKILL_DST"

# Core files
cp "$SKILL_SRC/SKILL.md" "$SKILL_DST/"
cp "$SKILL_SRC/requirements.txt" "$SKILL_DST/" 2>/dev/null || true

# Scripts (full — needed for dispatch)
rsync -a --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  "$SKILL_SRC/scripts/" "$SKILL_DST/scripts/"

# Templates (icons + charts + layouts; skip huge nothing)
if [[ -d "$SKILL_SRC/templates" ]]; then
  rsync -a \
    --exclude '__pycache__' \
    --exclude '.DS_Store' \
    "$SKILL_SRC/templates/" "$SKILL_DST/templates/"
fi

# References without AI image comparison gallery (~43MB of PNGs)
if [[ -d "$SKILL_SRC/references" ]]; then
  rsync -a \
    --exclude 'ai-image-comparison' \
    --exclude '__pycache__' \
    --exclude '.DS_Store' \
    "$SKILL_SRC/references/" "$SKILL_DST/references/"
fi

if [[ -d "$SKILL_SRC/workflows" ]]; then
  rsync -a --exclude '.DS_Store' "$SKILL_SRC/workflows/" "$SKILL_DST/workflows/"
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
if [[ "$PLATFORM" == "win32" ]]; then
  BIN="${BIN}.exe"
fi
chmod +x "$BIN" 2>/dev/null || true
echo "==> Smoke: $BIN --version"
"$BIN" --version

echo "==> Pack ready: $STAGE"
du -sh "$STAGE" "$STAGE/bin" "$STAGE/skills" || true
