---
description: Compatibility reference for existing-PPTX narration enhancement
---

# Native Narration PPTX Workflow

> Superseded routing: use [`native-enhance-pptx`](./native-enhance-pptx.md) for all existing-PPTX native enhancement work.

This file remains only as a compatibility reference for older agents and links. Do not maintain a separate narration workflow here.

## 1. Routing

| Need | Action |
|---|---|
| Existing `.pptx` + add speaker notes, narration audio, auto-advance, or page transitions while preserving visible slides | Run [`native-enhance-pptx`](./native-enhance-pptx.md) |
| PPT Master generated project with `svg_output/` / `svg_final/` | Use [`generate-audio`](./generate-audio.md) |
| Existing `.pptx` + beautify or re-layout visible slides | Use [`beautify-pptx`](./beautify-pptx.md) |
| Existing `.pptx` + fill new content into a native design | Use [`template-fill-pptx`](./template-fill-pptx.md) |

**Hard rule**: Do not follow the retired `native_narration_pptx.py` workflow steps directly. Use the stable `native_enhance_pptx.py` entry point documented in [`native-enhance-pptx`](./native-enhance-pptx.md).

## 2. Compatibility Boundary

`native_narration_pptx.py` may remain as a backward-compatible implementation entry point, but user-facing workflow execution must use:

```bash
python3 skills/ppt-master/scripts/native_enhance_pptx.py init "<source.pptx>" --name "<project_slug>"
python3 skills/ppt-master/scripts/native_enhance_pptx.py plan "<project>"
python3 skills/ppt-master/scripts/native_enhance_pptx.py validate "<project>"
python3 skills/ppt-master/scripts/native_enhance_pptx.py apply "<project>"
```

**Source import rule**: The active workflow archives the source PPTX into `<project>/sources/`; sources already under the repo's `projects/` tree are moved, and external sources are copied.

**Output rule**: Enhanced decks are written under `<project>/exports/` with the `_enhanced.pptx` suffix unless the caller passes an explicit `--output`.
