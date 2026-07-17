# Upstream PR notes (hugohe3/ppt-master)

## Goal

Add optional **engine pack** build + CI so desktop hosts (e.g. MindMux) can ship a self-contained runtime without system Python.

## Non-goals

- Do not change the existing skill-only Release assets (`ppt-master-skill-v*.zip`).
- Do not require engine packs for IDE users of the skill.

## What this PR adds

| Path | Purpose |
|------|---------|
| `engine/launcher.py` | CLI dispatcher: `ppt-master-engine <script> [args…]` |
| `engine/build.sh` | Build onedir PyInstaller pack + slim skill tree |
| `engine/requirements-engine.txt` | Minimal freeze deps |
| `engine/README.md` | Build / layout docs |
| `.github/workflows/engine-pack.yml` | Matrix build + upload on `engine-v*` tags |

## Pack layout (contract)

```
ppt-master-engine-<platform>-<arch>/
  bin/ppt-master-engine/ppt-master-engine[.exe]
  skills/ppt-master/   # scripts, templates, references (no examples / no ai-image-comparison gallery)
  manifest.json
```

## How to verify

```bash
PYTHON=python3.11 engine/build.sh
./dist-engine/ppt-master-engine-*/bin/ppt-master-engine/ppt-master-engine --version
# optional: project_manager init + svg_to_pptx smoke
```

## Suggested release process

1. Merge this PR.
2. Tag `engine-v0.1.0` (or run workflow_dispatch).
3. Attach multi-arch zips from the workflow.

## Downstream consumer (MindMux)

`pnpm setup:ppt-master-engine` downloads:

`https://github.com/<org>/ppt-master/releases/download/engine-vX.Y.Z/ppt-master-engine-{platform}-{arch}.zip`
