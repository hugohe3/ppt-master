# ppt-master engine pack

Build a **self-contained** runtime for embedding in desktop apps (e.g. MindMux):

- `bin/ppt-master-engine/` — PyInstaller launcher (bundled Python + python-pptx stack)
- `skills/ppt-master/` — slim skill content (scripts, templates, references; no example decks / AI gallery PNGs)
- `manifest.json` — version / platform metadata

Apps invoke:

```bash
./bin/ppt-master-engine/ppt-master-engine project_manager init demo --format ppt169 --dir work
./bin/ppt-master-engine/ppt-master-engine svg_to_pptx /path/to/project
```

## Build (local)

```bash
# Prefer Python 3.11–3.12 for PyInstaller stability
PYTHON=python3.11 engine/build.sh
```

Output: `dist-engine/ppt-master-engine-<platform>-<arch>/`

## Zip for GitHub Releases

```bash
cd dist-engine
zip -ry "ppt-master-engine-$(uname -s | tr A-Z a-z)-$(uname -m | sed 's/x86_64/x64/;s/arm64/arm64/').zip" ppt-master-engine-*
```

CI (`.github/workflows/engine-pack.yml`) builds and uploads zip assets on tag `engine-v*`.

## MindMux

```bash
# In mindmux-app:
pnpm setup:ppt-master-engine /path/to/ppt-master-engine-darwin-arm64
# or configure downloadUrlTemplate to this fork's Releases.
```
