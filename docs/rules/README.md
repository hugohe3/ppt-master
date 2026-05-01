# Project Rules

Conventions and style guides for contributors and AI agents working in this repository. These rules are derived from the de facto patterns in existing code and reference documents.

| Rule | Scope |
|---|---|
| [`prompt-style.md`](./prompt-style.md) | Style guide for files under `skills/ppt-master/references/` — voice, sectioning, table-first, forbidden patterns |
| [`code-style.md`](./code-style.md) | Style guide for Python under `skills/ppt-master/scripts/` — file headers, imports, CLI entry points, error handling, no-tests rule |

When adding a new rule file:

- One topic per file
- File name `<topic>.md` (lowercase, hyphenated)
- Add a row to the table above
- The body should be **prescriptive, not descriptive** — tell readers what to do, not what the project happens to look like
