# Prompt Content Layers

> Which content belongs in a prompt file at all, and where each kind lives. Applies to every file the runtime loads: `skills/ppt-master/references/`, `skills/ppt-master/workflows/`, `skills/ppt-master/templates/*.md`, `SKILL.md`, and `AGENTS.md`. [`prompt-style.md`](prompt-style.md) governs how those files are written; this rule governs what goes into them.

The prompt files are read by a model before it plans a deck and hand-writes SVG slides. Everything in them competes for the model's attention with the design decisions it is about to make. A paragraph earns its place only by being one of the first two kinds below.

---

## 1. The three kinds

| Kind | Test | Lives in | Example |
|---|---|---|---|
| **Craft** — design judgment | Changing it changes what the page looks like or says | The prompt file of the phase that makes the decision, once | The Visual Job Router, the elevation table and one-light-source default, overlay recipes, the contour-before-encoding gate, the communication-contract table, the cover and closing rules |
| **Contract** — minimal form | The one canonical form the model must write, plus a boundary the tools cannot enforce | Beside the craft that uses it, as one example and one line | One XML example per effect; "a gradient stroke needs a path with both width and height"; "never put `filter` and `clip-path` on the same `<image>`" |
| **Tool documentation** — converter and importer behavior | The checker or exporter already enforces it, or it describes import/normalization/`--strict` behavior, or it restates a procedure another phase owns | `skills/ppt-master/scripts/docs/`, never a prompt file | Accepted-but-warned spellings, DrawingML numeric ranges, crop-transport quantization, closed transform/path grammars, server lifecycle, sidecar schemas |

**Hard rule — enforced grammar is not prose**: a rule that `svg_quality_checker.py` or `svg_to_pptx` preflight already rejects needs nothing in the prompt beyond its canonical form. The failing check teaches the boundary at the moment it matters, with the exact message; a paragraph read before authoring cannot compete with that.

**Hard rule — a selection cue stays with the craft**: when a contract paragraph also says *when to choose* one construction over another ("a thin circle with a preset dash stays a native ellipse line; the shorthand is for thick rings"), that sentence is craft. Keep it in the prompt file even when the rest of the paragraph moves. Moving a whole paragraph by its heading is how selection cues get lost.

---

## 2. Where each kind lives

| Location | Holds | Loaded by |
|---|---|---|
| `references/<role>*.md`, `workflows/**.md` | Craft and contract, one owner per rule, organized by the phase that decides it (Plan: Strategist and the Generate Steps 1–5 / Quick §2; Do·Check·Act: Executor and Steps 6–7 / Quick §3–4 — see [`SKILL.md`](../../skills/ppt-master/SKILL.md) Phase Frame) | The runtime load sets in `scripts/prompt_audit_manifest.json` |
| `scripts/docs/<topic>.md` | Tool documentation. A contract reference that mirrors a prompt file keeps that file's section numbers (`svg-contract.md` §1.1–§2.2 mirror `shared-standards-core.md`, Part II §6.2–§6.10 mirror `svg-effects.md`) so a pointer resolves in either direction | Nobody during generation; `coverage.exempt` in the manifest with a reason |
| `templates/*_reference.md`, `templates/schemas/*.json` | Artifact grammar the model authors against (`design_spec.md`, `spec_lock.md`) | Read at authoring time by the owning Step |

**Hard rule — contract before craft, both short**: inside a file, and inside
each section, state the contract first — the routing/menu rows and the one
canonical form — then the craft that uses it. A recall index (a routing table,
the Visual Job Router, the everyday device menu) counts as contract: it is the
list of what exists, and it stays at the top because a capability the model
has not seen is a capability it will not use. Anything that is plain SVG or
XML behavior — what `<use>` does, what a path command means, that a transform
composes — gets one line or nothing; the model knows SVG, and the prompt only
records where this pipeline departs from it. Craft is written as the decision
and its test, not as an essay: one labelled paragraph or one table per
decision, examples only where a form is easier shown than told. A long
passage is justified only when the decision genuinely has that many moving
parts; length that comes from restating context, hedging, or listing every
case is what makes a rule hard to recall at authoring time.

**Hard rule — one owner, pointers elsewhere**: a rule is stated in full in exactly one file. Every other file that needs it carries a pointer naming the file and section, not a paraphrase. A paraphrase is a second owner: it drifts, contradicts the original after the next edit, and doubles the tokens. The cross-file duplicate check in `prompt_audit.py` catches verbatim copies only; paraphrases are caught by reading.

**Hard rule — planning reads everything, execution loads on triggers, the core keeps the recall**: the planning role reads its complete bundle. The execution core (`executor-base.md`, `shared-standards-core.md`, `semantic-svg.md`, the preset vocabulary, plus the confirmed mode / visual-style catalog file when the confirmation points to one — a `custom` with `*_references` reads only those files, a `custom` without references reads none) stays resident and carries the everyday forms and a recall of every deeper module — device menu, everyday effects, preset families, the Structure decision — so a capability is known before its file is opened. The preset vocabulary stays resident with the core so contours are known before selection. Each deeper module (effects, native-shape authoring, relationship grammar and topology, images, charts/tables, formula, hyperlink, structured templates, video, animation, web-image attribution) loads on one observable trigger — named in the core's routing table for construction modules, or in the owning route step for video, animation, and post-processing stages — is read completely on first use, and stays for the run; the page's module line records the load. A module with no recall in the core is the failure where a capability not in context is never used.

---

## 3. Moving content out of a prompt file

Run this procedure paragraph by paragraph; do not classify by section heading.

1. **Verify enforcement.** `grep` `scripts/svg_quality/` and `scripts/svg_to_pptx/` for the rule's tokens. Enforced → the whole paragraph moves to `scripts/docs/`. Unenforced but export-affecting → one line stays. Unenforced and not export-affecting → it was never a contract; decide whether it is craft or noise.
2. **Extract the selection cue** before moving the rest (§1 above).
3. **Keep the canonical form**: one example, the generated spelling, nothing about accepted alternatives.
4. **Sweep references** after removing or renumbering a section: `grep -rn "<file>.*§<n>"` across `skills/` and `docs/`. A pointer to a section that no longer exists is a silent loss.
5. **Update the manifest**: move the file between load sets if its role changed, add a `coverage.exempt` entry with a reason for a new tool document, lower the file budget to the new size (budgets are fixed upper bounds; 1000-token increments for large files), and refresh or remove any `schema_grammars` projection whose paragraph you edited.
6. **Run `python3 skills/ppt-master/scripts/prompt_audit.py`** and record the per-file and per-load-set numbers in the commit message.
7. **Review for strength and reach** ([`prompt-style.md`](prompt-style.md) §13): a `Hard rule` that vanished from both the prompt and the tool document, a positive capability statement that no loaded file carries any more, and a Quick-only gap (Quick loads no Strategist module) are the three regressions this kind of edit produces.

---

## 4. What this rule does not permit

- Deleting craft to hit a token target. The ceiling in [`prompt-style.md`](prompt-style.md) §4.1 is met by moving the other two kinds, never by thinning design judgment.
- Turning a `Hard rule` into a pointer to a tool document when no tool enforces it.
- Restating a moved rule "briefly" in the file it left. Brief restatements are the mechanism that produced the bloat.
