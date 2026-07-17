# Upstream PR notes (hugohe3/ppt-master)

## Acknowledgments

Thanks to **[@hugohe3](https://github.com/hugohe3) (Hugo He)** for creating and maintaining [ppt-master](https://github.com/hugohe3/ppt-master). This engine pack only packages the existing skill runtime for desktop embeds; the product vision and core pipeline are his work.

## Goal

Add optional **engine pack** build + CI so desktop hosts (e.g. MindMux) can ship a self-contained runtime without system Python.

## Why

ppt-master’s skill + Python pipeline already produces strong native PPTX quality. Desktop hosts want that path, but differ from IDE skill users:

| Host need | Gap with skill-only releases |
|-----------|------------------------------|
| No system Python for end users | Skill zip assumes an existing Python + deps |
| One-command provision | Hosts need a downloadable, versioned artifact |
| Fixed layout + single launcher | Full git checkout / ad-hoc venv is fragile |
| Smaller payload | Examples / full repo are unnecessary in-app |

**Engine packs** freeze a minimal PyInstaller onedir runtime + slim skill tree, published on `engine-v*` tags so skill releases stay untouched. IDE users can ignore this; hosts pin a URL and unpack into app resources. We avoid vendoring the whole repo into each host app.

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
