# Reference Document Style Guide

> Style rules for every file the runtime loads: `skills/ppt-master/SKILL.md`, `references/**/*.md`, `workflows/**/*.md`, and `templates/*.md`. Follow these when writing or reviewing role definitions, route authorities, stages, and shared specs. [`prompt-layers.md`](prompt-layers.md) says what may go into such a file; [`ownership.md`](ownership.md) says which role decides it; this file says how it is written.

These files drive runtime LLM behavior. Style consistency across them matters as much as correctness — divergent voice / structure forces the model to re-interpret each file from scratch and bloats the loaded context. The house pattern that has proved readable is the catalog format of `references/visual-styles/*.md`: one file per subject, a fixed section skeleton shared by every sibling, short labelled paragraphs written as positive vocabulary, and one example where a form is easier shown than told.

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

### 3.1 One Rule per Sentence

A sentence states one rule. An exception is its own sentence, or a row in a table; it is never a clause nested inside the rule it qualifies. A labelled paragraph states one decision in roughly sixty words or fewer; a second decision starts another labelled paragraph or a table row. When a rule needs three or more cases (`never X unless Y, and only when Z`), write the cases as a two-column table. Concision is measured in decisions per paragraph, not words per sentence: a compression pass that folds several rules into one long sentence has made the file harder to follow, not shorter.

❌ Avoid: a 100-word sentence that names the rule, two exceptions, the owning file, and the fallback.
✅ Prefer: the rule in one sentence; the exceptions as a table; the owning file as one pointer.

### 3.2 Pointers Name the File to Open

A pointer exists so the model knows which file to read next — `[`svg-effects.md`](./svg-effects.md) §6.4` — and appears where that reading is needed. Ownership bookkeeping written for the maintainer ("owned by", "belongs to", "lives in", "is not restated here") does not belong in a prompt file; the owner of every cross-file rule is recorded once in [`rule-owners.md`](rule-owners.md).

### 3.3 One Meaning per Term

Every term used in a rule has exactly one meaning across the loaded corpus, defined once in the vocabulary section of [`SKILL.md`](../../skills/ppt-master/SKILL.md) or in the section that owns it. Do not give an existing term a second meaning; when two concepts share a word, rename one (record the rename in [`rule-owners.md`](rule-owners.md) with every file it touches). A term used in a `Hard rule` or `Mandatory` that no loaded file defines is a defect: the obligation cannot be followed.

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
**Hard rule**: Reuse the complete Design Spec and lock while the active context remains valid. After compaction or fresh/resumed execution, read both once before continuing.

**Forbidden — unresolved asset references**:
- Icons MUST resolve to prepared project-local assets
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

### 4.1 Ownership Contract

Decision ownership across plan, execution, and the Reference grey zone — the ingredients → plan + preparation → realization chain, the three ownership tiers, the capability-before-selection rule, the core volume ceiling, preparation timing, and the review gate — is owned by [`ownership.md`](ownership.md). Classify a decision there before labeling its strength here.

### 4.2 Admission Criterion for Prohibitions

Before adding a `Hard rule`, `Forbidden`, `Mandatory`, `never`, `do not`, or any quota/threshold to a process prompt, name the mechanism that makes it hard: a checker rule id, an exporter behaviour, a DrawingML limit, a structured Master/Layout contract, artifact ownership or gate order, or reading-cost control. A rule with no such mechanism does not affect whether the SVG renders as authored or exports to editable PPTX; it may enter only as a capability entry (what exists and its syntax), a `Reference — not a constraint`, or an example — never as a prohibition, quota, usage default, or "omit when …" clause. Whether and how the model uses a capability is its own judgment. A prohibition that a script already enforces is not restated in prose; write only the fix.

**Owner exceptions — kept as `Mandatory`**: primary-per-page, composition geometry vocabulary (including its slide-versus-web-grid motivation), the ±2px font-size band, the Layout-pattern diversity self-check, and "do not start from a universal palette" are deliberate anti-sameness devices retained by the maintainer. If sameness returns after other restrictions are relaxed, add examples first; do not re-escalate demoted rules.

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

### 5.1 Closed vs Illustrative Lists

Strength (§4) and extent are separate axes: a `Hard rule` may carry an illustrative list, and a `Reference` may carry a closed one.

| List kind | Test | Marking |
|---|---|---|
| Closed | A schema, validator, exporter, or script rejects an unlisted value | State the complete set; adding a value means changing that consumer too |
| Illustrative | The list names instances of a broader idea the reader must still judge | Say so inline — `common triggers rather than an exhaustive list` |

❌ An unmarked enumeration reads as closed, the same way an unlabeled soft rule reads as hard (§11).

❌ Never phrase a rule so it turns an illustrative list into a lookup obligation. "Consult `<table>` for `<X>`" makes that table's rows the only reachable answers and invites restating `<X>` until it matches one — even when the table's own boundary grants free-form authorship. Point at the procedure that generates answers; offer the table as a shortcut when an entry already matches.

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

## 12. Exemplars

This guide is prescriptive. A file that violates a rule here is refactored toward the rule; the rule changes only through an explicit decision recorded in the commit, never by treating the divergent file as the new convention.

The canonical exemplars to model new or rewritten files after:

| If you're writing... | Model after |
|---|---|
| A catalog entry (one style, mode, rendering, type) | [`visual-styles/swiss-minimal.md`](../../skills/ppt-master/references/visual-styles/swiss-minimal.md), [`modes/pyramid.md`](../../skills/ppt-master/references/modes/pyramid.md) |
| A construction module loaded on a trigger | [`executor-structure.md`](../../skills/ppt-master/references/executor-structure.md), [`native-formula.md`](../../skills/ppt-master/references/native-formula.md) |
| A technical / format spec | [`canvas-formats.md`](../../skills/ppt-master/references/canvas-formats.md), [`semantic-svg.md`](../../skills/ppt-master/references/semantic-svg.md) |
| A route authority | [`workflows/edit-native-pptx.md`](../../skills/ppt-master/workflows/edit-native-pptx.md) |
| Stage runbook | [`workflows/stages/verify-charts.md`](../../skills/ppt-master/workflows/stages/verify-charts.md), [`workflows/stages/web-image-review.md`](../../skills/ppt-master/workflows/stages/web-image-review.md) |

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
| Owner registry | Every cross-file rule the edit touches has one owner entry in [`rule-owners.md`](rule-owners.md); the other files carry a pointer, not a paraphrase. A new paragraph that restates an owned rule is the regression this table exists to catch |
| Restriction admission | Every `Hard rule` / `Mandatory` / `never` / quota the edit adds or keeps cites its §4.2 mechanism; a STYLE prohibition is removed (capability entry, Reference, or example), and SCRIPT-ENFORCED prose keeps only the fix |

**Hard rule**: A shorter prompt that changes decision ownership, constraint strength, preparation timing, or capability discoverability is a semantic regression even when structural and token-budget audits pass.
