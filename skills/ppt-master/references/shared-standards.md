# Shared Technical Standards

Compatibility router for the split SVG specifications. The always-on authoring contract is [`shared-standards-core.md`](./shared-standards-core.md); Default and Quick Generate load every conditional module through [`executor-base.md`](./executor-base.md)'s routing table, and other SVG-authoring routes through the routing table at the top of the core. This file is a pointer, not a combined runtime authority: follow the selected route's required modules and do not load every conditional module by default.
