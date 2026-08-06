# Shared Technical Standards

Compatibility router for the split SVG specifications. Runtime routes load the core plus their route-required and feature-triggered modules.

| Scope | Authority | Trigger |
|---|---|---|
| XML/SVG foundation, shared visual-quality defaults, page closure, grouping | [`shared-standards-core.md`](./shared-standards-core.md) | Always for SVG authoring |
| Advanced effects and geometry | [`svg-effects.md`](./svg-effects.md) | Always for Default / Quick Generate; otherwise when the corresponding effect or geometry is used |
| Preset patterns and native chart/table metadata | [`native-data-interface.md`](./native-data-interface.md) | Corresponding native-data interface is used |
| Master/Layout/placeholder structure | [`pptx-structure-interface.md`](./pptx-structure-interface.md) | `pptx_structure.mode: structured` |

**Hard rule**: This file is a routing pointer, not a combined runtime authority. Follow the selected route's required modules; do not load every remaining conditional module by default.
