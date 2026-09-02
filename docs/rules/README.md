# Project Rules

Conventions and style guides for contributors and AI agents working in this repository. These rules are derived from the de facto patterns in existing code and reference documents.

| Rule | Scope |
|---|---|
| [`prompt-style.md`](./prompt-style.md) | Style guide for every runtime-loaded file (`SKILL.md`, `references/`, `workflows/`, `templates/*.md`) — voice, one rule per sentence, labels, tables, exemplars |
| [`prompt-layers.md`](./prompt-layers.md) | What belongs in a prompt file — craft, minimal contract, procedure, or tool documentation — where each lives, and how to move content out without losing a rule |
| [`ownership.md`](./ownership.md) | Which role decides what — the plan / execution / Reference tiers, capability before selection, the core volume ceiling, preparation timing |
| [`rule-owners.md`](./rule-owners.md) | Registry of every cross-file rule: its one owner section and the files that may only point to it |
| [`code-style.md`](./code-style.md) | Style guide for Python under `skills/ppt-master/scripts/` — file headers, imports, CLI entry points, error handling, no-tests rule |
| [`language.md`](./language.md) | Language rule for agent-facing Markdown and `docs/` — one language per file, non-English as content but never as a rule, no hard-coded output language |

When adding a new rule file:

- One topic per file
- File name `<topic>.md` (lowercase, hyphenated)
- Add a row to the table above
- The body should be **prescriptive, not descriptive** — tell readers what to do, not what the project happens to look like
