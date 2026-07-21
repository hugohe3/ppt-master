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
| `Forbidden — unresolved image references` | `Anti-pattern: broken image links` |

**Hard rule — retain failure predicates**: Cut narrative teaching and background motivation. Keep one compact protected invariant or failure predicate when it determines the rule's strength, scope, or safe generalization; attach it to the rule or one `> Note` line. Runtime prompts need the behavior and its objective failure boundary, not the full rationale.

---

## 4. Bold Inline Labels

Begin substantive paragraphs with a bolded short label. Reuse this fixed vocabulary:

| Label | Use for |
|---|---|
| `**Hard rule**:` | Non-negotiable behavior |
| `**Forbidden — xxx**:` | Disallowed values / actions, followed by a list |
| `**Mandatory**:` | Required step within an optional phase |
| `**Default — X (may override when …)**:` | A sensible default that saves re-deciding; deviating is allowed with a stated reason |
| `**Reference — not a constraint**:` | Vocabulary or options with no single right answer — a recall aid, not an instruction (replaces scattered "for recall, not constraint" / "illustrative only") |
| `**When to run**:` / `**Trigger**:` | Activation condition |
| `**Validation**:` | Post-step assertion |
| `**Per-page xxx**:` / `**Per-row xxx**:` | Loop body description |
| `**Generation pacing (mandatory)**:` | Concurrency / rate constraint |
| `**Missing X**` → ... | Fallback behavior |

✅ Good (from `executor-base.md`):
```
**Hard rule**: Before generating **each** SVG page, run:
`python3 skills/ppt-master/scripts/project_manager.py page-context <project_path> P<NN> --record-usage`.

**Forbidden — unresolved asset references**:
- Icons MUST come from `icons.inventory`
- Images MUST resolve to declared project assets
```

**Choosing the strength** — before labeling a constraint, ask: *if a page violates it, does it objectively fail (text overlaps, overflows, misaligns, becomes unreadable, loses information, breaks across renderers), or could it merely look worse?*

| Answer | Label |
|---|---|
| Objective failure, checkable by a concrete trigger | `**Hard rule**:` / `**Forbidden**:` |
| Has a sensible default, deviation can be justified | `**Default — … (may override)**:` |
| No right answer — taste, style, or scenario fit | `**Reference — not a constraint**:` |

Boundary cases go by this test, not by how strong the verb feels: "never split a full sentence into bullets" stays near-MUST because splitting *loses the information that the block was continuous reasoning*, not because "never" sounds strict.

**Hard rule**: A `Hard rule` or `Forbidden` label whose failure boundary is not self-evident retains one compact objective predicate. If no objective predicate exists, demote the instruction to `Default` or `Reference` instead of preserving only a strong verb.

> Note: only a MUST with a concrete objective trigger may become a `svg_quality_checker.py` rule. SHOULD is at most a `warning`; MAY is never checked — encoding taste as a check turns the checker into a de-facto spec.

### 4.1 Ownership Contract: Ingredients → Plan + Preparation → Realization

Constraint strength and decision ownership are independent. Preserve this chain whenever writing, compressing, or reviewing multi-role prompts:

| Layer | Owns |
|---|---|
| User / initial materials | Supplied facts/assets, desired outcome, exclusions, and permission boundaries remain authoritative |
| Strategist / plan + preparation | Assess material sufficiency; trigger permitted fact research; decide the approved content, resources, keys, identity anchors, and exact page roster; materialize the planned project-local inventory or record an explicit `Needs-Manual` dependency before execution |
| Executor / realization | Use only the prepared inventory and realize the approved selections through geometry, composition, hierarchy, and treatment; sparse local font/color garnish is allowed only while non-structural and non-recurring |

**Preparation timing**: Fact research required for planning may run before final confirmation. AI / web / slice acquisition runs only from the completed `design_spec.md §VIII` and `spec_lock.md`, after final confirmation and before Executor. Image_Generator, Image_Searcher, and icon-sync tooling execute Strategist-owned preparation; they are not independent decision owners.

**Hard rule**: downstream freedom exists only in dimensions left open upstream. A named outcome retains identity; a broad semantic request permits in-class choice. Once the plan resolves that choice, execution cannot reopen or substitute it. Executor never searches, generates, downloads, syncs, invents, or replaces a resource; missing material returns to Strategist-owned preparation or upstream repair.

> Mnemonic — restaurant contract: the customer supplies initial ingredients and the desired dish; Strategist plans the dish and prepares the complete mise en place; Executor cooks from that prepared inventory. “Mapo tofu” cannot become tomato-and-eggs or tofu soup, while “a tofu dish” leaves deliberate in-class freedom.

**Review gate**: treat any prompt refactor that erases this ownership chain, moves acquisition into Executor, turns a permission into a quota, or turns flexible realization into silent reselection as a semantic regression even when the compressed wording is shorter.

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

- Localized warning/exclamation blockquotes (use `> Note` or omit)
- Emoji as decoration in headings (✅ in checkpoint headings is the only sanctioned use)
- Smiley face / sparkle / fire emoji
- Footnotes (`[^1]`)
- HTML in markdown body (`<details>`, `<br>`, etc.) — only the SVG embedding examples use real `<svg>`/`<image>` in code blocks, never as live markdown
- "**Best practice**: ..." labels — pick the right strength label instead (§4): `**Hard rule**:` if violating it fails, `**Default — … (may override)**:` if it's a sensible default, `**Reference — not a constraint**:` if it's taste. Never leave a soft suggestion unlabeled — an unlabeled line reads as a hard rule to the model

---

## 12. When This Guide Conflicts With Existing Files

Existing files take precedence as ground truth. If a current `references/*.md` violates a rule here, decide whether to (a) update this guide to match the de facto convention, or (b) refactor that file. Don't silently apply a divergent style to one new file.

The canonical exemplars to model new files after:

| If you're writing... | Model after |
|---|---|
| A role reference (Image_X / Strategist-style) | [`image-searcher.md`](../../skills/ppt-master/references/image-searcher.md), [`strategist.md`](../../skills/ppt-master/references/strategist.md) |
| A shared spec across roles | [`image-base.md`](../../skills/ppt-master/references/image-base.md), [`shared-standards-core.md`](../../skills/ppt-master/references/shared-standards-core.md) |
| A technical / format spec | [`canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md), [`svg-image-embedding.md`](../../skills/ppt-master/references/svg-image-embedding.md), [`image-layout-spec.md`](../../skills/ppt-master/references/image-layout-spec.md) |
| Stage runbook | [`workflows/stages/verify-charts.md`](../../skills/ppt-master/workflows/stages/verify-charts.md) |

---

## 13. Prompt Refactor Review

Prompt compression is complete only after reviewing token reduction and semantic change separately.

| Check | Required evidence |
|---|---|
| Owner and consumer | Each moved field or capability still has one authority, and every runtime consumer loads or projects that authority |
| Strength delta | Record `before → after` for deleted, moved, or rewritten `Hard rule`, `Forbidden`, `Default`, and `Reference` instructions |
| Failure predicate | Preserve the compact objective invariant that justifies every non-self-evident hard boundary |
| Freedom boundary | A permission did not become a quota, a reference did not become a lock, and flexible realization did not become silent reselection |
| Preparation timing | Strategist-owned acquisition and materialization did not move into Executor or before final confirmation |
| Capability discovery | Conditional deep specifications retain a short visible menu or an externally observable trigger before their load gate |
| Token delta | Report route/file budget changes separately; a budget pass does not prove semantic equivalence |

**Hard rule**: A shorter prompt that changes decision ownership, constraint strength, preparation timing, or capability discoverability is a semantic regression even when structural and token-budget audits pass.
