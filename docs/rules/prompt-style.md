# Reference Document Style Guide

> Style rules for files under `skills/ppt-master/references/`. Follow these when writing or reviewing role definitions and shared specs.

The reference layer drives runtime LLM behavior. Style consistency across these files matters as much as correctness — divergent voice / structure forces the model to re-interpret each file from scratch and bloats the loaded context.

---

## 1. Document Header

| Element | Rule |
|---|---|
| Top line | `> See [`xxx`](xxx.md) for ...` — one-line cross-reference, optional |
| H1 title | `# Role: X` (for role files) or `# X Reference Manual` / `# X Specification` |
| Opening paragraph | One sentence stating mission + trigger. Max 2 lines |
| `## Core Mission` | Optional; if present, ≤ 3 sentences |

✅ Good (from `image-searcher.md`):
```
> See [`image-base.md`](./image-base.md) for the common framework.

# Image_Searcher Reference Manual

Role definition for the **web image acquisition path**: translate Strategist intent into keyword queries, search openly-licensed providers, download a license-cleared image into `project/images/`, and record provenance + license metadata into `image_sources.json`.

**Trigger**: resource list rows with `Acquire Via: web`. The role is loaded only when at least one such row exists.
```

❌ Avoid: long "Core Mission" paragraphs that explain *why* the role exists, list its philosophical goals, or narrate the pipeline context.

---

## 2. Sectioning

| Level | Format | Notes |
|---|---|---|
| Main | `## N. Title` | Numbered from 1 |
| Sub | `### N.1` / `### N.2` ... | Or `### a.` / `### b.` for confirmation flows |
| Divider | `---` between main sections | Always |

`## Core Mission`, `## Pipeline Context`, `## Trigger` may appear before `## 1.` without numbering.

---

## 3. Voice — Command, Not Explanation

| Use | Don't use |
|---|---|
| `Run X.` | `You should typically run X because ...` |
| `Output: Y` | `The role outputs Y, which is important because ...` |
| `MUST come from Z` | `It is recommended to source from Z` |
| `Forbidden — values outside the lock` | `Anti-pattern: using values outside the lock` |

**Hard rule**: if a sentence explains *why*, demote it to a single `> Note` blockquote line OR cut it. The agent does not need motivation, only behavior.

---

## 4. Bold Inline Labels

Begin substantive paragraphs with a bolded short label. Reuse this fixed vocabulary:

| Label | Use for |
|---|---|
| `**Hard rule**:` | Non-negotiable behavior |
| `**Forbidden — xxx**:` | Disallowed values / actions, followed by a list |
| `**Mandatory**:` | Required step within an optional phase |
| `**When to run**:` / `**Trigger**:` | Activation condition |
| `**Validation**:` | Post-step assertion |
| `**Per-page xxx**:` / `**Per-row xxx**:` | Loop body description |
| `**Generation pacing (mandatory)**:` | Concurrency / rate constraint |
| `**Missing X**` → ... | Fallback behavior |

✅ Good (from `executor-base.md`):
```
**Hard rule**: Before generating **each** SVG page, `read_file <project_path>/spec_lock.md`.

**Forbidden — values outside the lock**:
- Colors (fill / stroke / stop-color) MUST come from `colors`
- Icons MUST come from `icons.inventory`
```

---

## 5. Tables First

Most sections need at least one table. Reach for a table whenever you would write 3+ parallel bullet points.

| Use case | Format |
|---|---|
| Enums, modes, options | Table with `Key | Behavior` |
| Field definitions | Table with `Field | Notes` |
| Decision matrices | Table with `Condition | Action` |
| Cross-reference index | Table with `Term | Defined in` |

Bullets are fine for ≤ 3 short imperatives or a single ordered procedure.

---

## 6. Examples

| Form | Use |
|---|---|
| Fenced code block (` ``` `) | Commands, file content, ASCII diagrams |
| Inline code (` ` `) | File paths, identifiers, env vars |
| 2-column ✅/❌ table | Short keyword-vs-keyword contrast (one phrase per cell) |

❌ Avoid: 3-column ✅/❌/(why) tables. The "why" column is explanation — drop it or move to a `>` note.

❌ Avoid: long narrative example paragraphs. Use a code block or table.

---

## 7. Forbidden Section Types

These section names are not used anywhere in `references/`. Do not introduce them:

- `## Anti-patterns`
- `## Best Practices`
- `## Tips`
- `## FAQ` (FAQ lives in `docs/faq.md`)
- `## Why X`
- `## Background` / `## Motivation`

If you have rules to communicate that would naturally land in one of these sections, integrate them into the relevant numbered section as a `**Forbidden — xxx**` block or a `> Note` line.

---

## 8. Cross-References

| Reference type | Format |
|---|---|
| Sibling reference file | `[`xxx`](./xxx.md)` |
| Section in same file | `§N.M` (no link) |
| Section in another file | `[`xxx`](./xxx.md) §N.M` |
| Script doc | `[`xxx`](../scripts/docs/xxx.md)` |
| Workflow | `[`xxx`](../workflows/xxx.md)` |

Always backtick-wrap the filename in the link text.

---

## 9. Annotations

| Symbol | Meaning |
|---|---|
| `🚧 **GATE**:` | Mandatory checkpoint before proceeding |
| `⛔ **BLOCKING**:` | Must wait for explicit user confirmation |
| `📝 **Template mapping**:` | Page-to-template declaration (Executor-specific) |
| `> Note` blockquote | Edge case, fallback, or single-line context |

Use sparingly. If every paragraph has a symbol, none of them carry weight.

---

## 10. Checkpoint Output Format

Each phase ends with a fenced markdown block showing the agent's expected completion confirmation:

````markdown
## ✅ {Phase Name} Complete

- [x] {evidence-driven assertion 1}
- [x] {evidence-driven assertion 2}
- [ ] **Next**: {next-phase pointer}
````

Items are evidence-driven (`file exists at path X`, `status N is Generated`), not aspirational (`prompts are good`).

---

## 11. Forbidden Patterns Across the Whole Layer

- `> 重要：` / `> 注意：` Chinese exclamations (use `> Note` or omit)
- Emoji as decoration in headings (✅ in checkpoint headings is the only sanctioned use)
- Smiley face / sparkle / fire emoji
- Footnotes (`[^1]`)
- HTML in markdown body (`<details>`, `<br>`, etc.) — only the SVG embedding examples use real `<svg>`/`<image>` in code blocks, never as live markdown
- "**Best practice**: ..." labels — use `**Hard rule**:` if it's required, or omit if it's not

---

## 12. When This Guide Conflicts With Existing Files

Existing files take precedence as ground truth. If a current `references/*.md` violates a rule here, decide whether to (a) update this guide to match the de facto convention, or (b) refactor that file. Don't silently apply a divergent style to one new file.

The canonical exemplars to model new files after:

| If you're writing... | Model after |
|---|---|
| A role reference (Image_X / Strategist-style) | [`image-searcher.md`](../skills/ppt-master/references/image-searcher.md), [`strategist.md`](../skills/ppt-master/references/strategist.md) |
| A shared spec across roles | [`image-base.md`](../skills/ppt-master/references/image-base.md), [`shared-standards.md`](../skills/ppt-master/references/shared-standards.md) |
| A technical / format spec | [`canvas-formats.md`](../skills/ppt-master/references/canvas-formats.md), [`svg-image-embedding.md`](../skills/ppt-master/references/svg-image-embedding.md), [`image-layout-spec.md`](../skills/ppt-master/references/image-layout-spec.md) |
| Workflow runbook | [`workflows/verify-charts.md`](../skills/ppt-master/workflows/verify-charts.md) |
