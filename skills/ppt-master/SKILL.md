---
name: ppt-master
description: >
  AI-driven presentation workflow for generating editable PPTX decks, creating
  reusable Brand/Layout/Deck workspaces, filling native PPTX templates, and
  enhancing finished PPTX files. Use when the user asks to create, regenerate,
  template, fill, or enhance a presentation, or mentions ppt-master.
---

# PPT Master Skill

PPT Master is a routed presentation workflow. This entry owns global execution discipline and route selection only; each selected route owns its procedure.

## Mandatory Load Order

1. Read this file.
2. Read [`workflows/routing.md`](workflows/routing.md).
3. Select exactly one top-level route from the routing authority.
4. Read only that route's authority and its explicitly triggered supporting documents.

| Selected route | Runtime authority |
|---|---|
| Generate PPTX | [`workflows/generate-pptx.md`](workflows/generate-pptx.md) |
| Create Template | [`workflows/create-template.md`](workflows/create-template.md) |
| Fill Native PPTX | [`workflows/template-fill-pptx.md`](workflows/template-fill-pptx.md) |
| Enhance Native PPTX | [`workflows/native-enhance-pptx.md`](workflows/native-enhance-pptx.md) |

**Hard rule — selected authority only**: Do not load another top-level route's procedure after routing. Profiles, stages, governance files, and child workflows refine the selected route; they never compete with it.

---

## Global Execution Discipline

1. **Serial execution** — Follow the selected authority's steps in order. A completed non-blocking step may continue directly to the next eligible step.
2. **Blocking means stop** — At every `⛔ BLOCKING` gate, wait for explicit user confirmation. Do not decide on the user's behalf.
3. **No cross-phase bundling** — Do not combine work across an unclosed gate. Once the route's final user gate closes, later non-blocking steps may continue automatically.
4. **Gate before entry** — Verify every listed prerequisite before entering a step.
5. **No speculative execution** — Do not prepare later-phase artifacts before their owning step.
6. **Deterministic routing** — Do not add a route-choice question when [`routing.md`](workflows/routing.md) resolves the request. If a route prerequisite is missing, state it and stop that route.
7. **Owning-source recovery** — On failure, repair or regenerate the owning source artifact and resume from the route's declared pointer. Do not silently downgrade a required artifact.

## Global Communication Rules

- Match the user's language and source language unless the user explicitly overrides it.
- Localize user-facing option labels and explanations. Keep exact enum IDs or field names when needed for precision.
- Keep `design_spec.md` section headings and field names in the template's original English; content values may use the user's language.
- Before switching roles, read the corresponding role reference and output:

```markdown
## [Role Switch: <Role Name>]
📖 Reading role definition: references/<filename>.md
📋 Current task: <brief description>
```

---

## Repository Compatibility

- This package is a workflow/skill, not a generic application scaffold. Do not create `.worktrees/`, `tests/`, branch workflows, or generic engineering structure by default.
- Keep required workflow, reference, script, and template documentation inside this Skill directory.
- Repository-level documents may point into the package; package runtime files must not depend on repository-level instructions.
- On Windows, if a documented `python3 ...` command is unavailable, rerun the same command with `python`.
