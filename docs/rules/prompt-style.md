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

### 4.1 Ownership Contract: Ingredients → Plan + Preparation → Realization

Constraint strength and decision ownership are independent. Preserve this chain whenever writing, compressing, or reviewing the default multi-role Generate prompts:

| Layer | Owns |
|---|---|
| User / initial materials | Supplied facts/assets, desired outcome, exclusions, and permission boundaries remain authoritative |
| Strategist / plan + preparation | Assess material sufficiency; trigger permitted topic research and retain its research/provenance pair without expanding adopted webpage URLs; decide the approved content, resources, keys, identity anchors, and exact page roster. During that roster composition, resolve each page's semantic carrier mix—background, text/lettering, native-geometry/relationship jobs, imagery/symbols, and data carriers—in one pass before deriving external-resource rows. Recommend high-level composition, visual focus, and continuity as Reference when useful, without selecting a local authoring capability or element geometry; materialize the planned project-local inventory or record an explicit `Needs-Manual` dependency before execution. For icons, prepare a curated project pool with broad semantic fit rather than assigning files to pages |
| Executor / realization | Use only prepared project-local assets; preserve approved content, resources, and identity anchors; realize each page by resolving the actual carrier combination, geometry, composition, hierarchy, and treatment together before coordinates. Discover and invoke local deterministic authoring capabilities without an upstream capability selection. Consider each field explicitly labeled `suggestion` or Reference, then adopt, adapt, or decline it while preserving its semantic job and every binding constraint. For icons, the complete `<project>/icons/` pool is prepared material; `icons.inventory` is a curated bundled-pool index, not a page-use plan or whitelist, and Executor chooses prepared icons per page without a coverage quota. Sparse local font/color garnish is allowed only while non-structural and non-recurring |

**Hard rule — capability knowledge precedes selection**: a role must know that
a capability exists before choosing among capabilities; otherwise a load trigger
circularly depends on a choice made without that capability. The always-read
core of the authoring role therefore carries the recall of every construction
capability — the everyday device menu and effects, the complete preset
vocabulary, the Structure decision, and one routing row per deeper module —
while the deeper module itself (effects beyond the everyday block, native-shape
authoring, relationship grammar and topology assembly, and the rarer formula,
hyperlink, chart/table, structured-template, video, animation, and web-image
files) is loaded on its own observable trigger, read completely on first use,
and kept for the run. The owning rule is
[`prompt-layers.md`](prompt-layers.md) §2.

**Hard rule — core volume ceiling**: the always-read core of an authoring role
stays small enough that its own content is not diluted by what follows. Measured
against the v2.13.0 baseline, an Executor-phase core of roughly 1,300 lines
across a role file plus a shared technical file produced richer pages than a
4,000-line, 12-file mandatory bundle; the larger bundle flattened expression
while passing every structural gate. Treat that as the working ceiling. When a
core grows past it, shrink it by removing what is not authoring guidance or by
moving a deeper module behind a trigger whose recall stays in the core. What may stay in a
prompt file at all — craft, minimal contract, or tool documentation — and the
procedure for moving content out are owned by
[`prompt-layers.md`](prompt-layers.md).

Default Strategist's planning bundle covers resource/preparation and high-level
expression options without local authoring parameters, because those choices are
persisted into artifacts other roles consume. Only post-selection mechanics whose
trigger is independently observable stay conditional: an actual `ai` / `slice`
resource row triggers Image_Generator backend, prompt-assembly, and per-image
type details after planning, and those mechanics are not a missing Strategist
capability.

**Hard rule — native shapes are authoring capabilities, not prepared
resources**: a prepared resource needs a stable project-local file/path before
realization because page authoring cannot acquire or generate it in place.
Office presets, SVG primitives, Connectors, Boolean helpers, and necessary
freeform geometry are locally callable construction capabilities. Strategist
never inventories them or promotes a concrete preset, primitive, Connector,
Boolean/freeform operation, or authoring parameter into a binding planning
selection. A macro Reference may mention a technique as optional inspiration
without prescribing or gating construction. The Design Spec / lock create no
native-shape field; Executor reads the complete current preset vocabulary and
chooses the page-fit construction during realization.

**Preparation timing**: In the default pipeline, topic research and import of
its two-artifact research pair may run before final confirmation. Facts JSON
URLs are not auto-expanded. AI / web / slice acquisition runs only from the
completed `design_spec.md §VIII` and `spec_lock.md`, after final confirmation
and before Executor. Only after normal image search fails may one relevant
adopted page become a Markdown + companion-image source package; review it and
promote accepted files individually, never the whole package. Image_Generator,
Image_Searcher, and icon-sync tooling execute Strategist-owned preparation;
they are not independent decision owners.

**Post-motion sound exception**: optional transition/object sound is not a
page-authoring ingredient and never enters Strategist planning,
`design_spec.md`, or `spec_lock.md`. After the SVG roster and visual motion
solution are complete, the active animation/export stage may discover bundled
sound ids and sync only a concretely selected cue into the project. With no
selected cue, it creates no `<project>/sounds/` directory. This exception does
not permit Executor to acquire visual resources.

**Hard rule — default pipeline**: downstream freedom exists only in dimensions left open upstream, including fields explicitly labeled `suggestion` or Reference. A named binding outcome retains identity; a broad semantic request or expression recommendation permits in-class choice. Executor may adopt, adapt, or decline a Reference without upstream repair unless an explicit user/template/resource constraint promotes the named property. Once the plan resolves a binding choice, execution cannot reopen or substitute it. For icons, library/stroke and the prepared-project boundary bind, while per-page choice within the prepared pool is realization. Executor never searches, generates, downloads, syncs, invents, or replaces a resource; missing material returns to Strategist-owned preparation or upstream repair.

**Explicit Quick Generate exception**: [`quick-generate`](../../skills/ppt-master/workflows/profiles/quick-generate.md) removes the separate Strategist/confirmation handoff. The current main agent therefore owns both its active-context decisions and the preparation of project-local sources, images, icons, and provenance before it begins SVG realization; native formulas are authored directly from exact mathematical content rather than acquired as resources. This exception does not move acquisition into a default-pipeline Executor and does not permit resource reselection while a page is being realized. Explicit user facts, choices, exclusions, and permissions remain upstream authority; unspecified routine choices are resolved automatically without a confirmation stop.

> Mnemonic — restaurant contract: the customer supplies initial ingredients and the desired dish; Strategist plans the dish and prepares the complete mise en place; Executor cooks from that prepared inventory. “Mapo tofu” cannot become tomato-and-eggs or tofu soup, while “a tofu dish” leaves deliberate in-class freedom.

**Review gate**: treat any prompt refactor that erases the selected profile's ownership chain, moves acquisition into the default-pipeline Executor, turns a permission into a quota, or turns flexible realization into silent resource/identity reselection as a semantic regression even when the compressed wording is shorter.

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
| Restriction census | Before each release, enumerate every `Hard rule` / `Mandatory` / `never` / quota in the Generate load sets (`route.generate.*`, `stage.generate.*` in `scripts/prompt_audit_manifest.json`) and classify each as EXPORT, SCRIPT-ENFORCED, PROCESS, or STYLE; Hard-rule counts are justified only by §4.2 mechanism citations; STYLE prohibitions are removed (capability entry, Reference, or example), and SCRIPT-ENFORCED prose keeps only the fix |

**Hard rule**: A shorter prompt that changes decision ownership, constraint strength, preparation timing, or capability discoverability is a semantic regression even when structural and token-budget audits pass.
