# Shared Technical Standards

Compatibility router for the split SVG technical specifications. Runtime routes load the core plus only the modules triggered by the current lock and page features.

| Scope | Authority | Trigger |
|---|---|---|
| XML/SVG foundation, compatibility, page closure, grouping | [`shared-standards-core.md`](./shared-standards-core.md) | Always for SVG authoring |
| Advanced effects and geometry | [`svg-effects.md`](./svg-effects.md) | Corresponding effect or geometry is used |
| Preset patterns and native chart/table metadata | [`native-data-interface.md`](./native-data-interface.md) | Corresponding native-data interface is used |
| Master/Layout/placeholder structure | [`pptx-structure-interface.md`](./pptx-structure-interface.md) | `pptx_structure.mode: structured` |

**Hard rule**: This file is a routing pointer, not a combined runtime authority. Do not load every conditional module by default.
